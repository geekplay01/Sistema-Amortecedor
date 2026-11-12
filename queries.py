"""Consultas das telas (somente leitura, exceto status/amostras/backup)."""
import os, re, json, shutil, sqlite3, datetime
import database as db

def q(sql, a=()):
    c = db.conn()
    try: return [dict(r) for r in c.execute(sql, a)]
    finally: c.close()
def q1(sql, a=()):
    r = q(sql, a); return r[0] if r else None
def run(sql, a=()):
    c = db.conn()
    try: cur = c.execute(sql, a); c.commit(); return cur.lastrowid
    finally: c.close()

APP_TXT = "coalesce(a.make,'')||' '||coalesce(a.model,'')||' '||coalesce(a.version,'')||' '||coalesce(a.application_text,'')||' '||coalesce(a.axle,'')||' '||coalesce(a.side,'')"
def _app_conds(f, p):
    w = []
    if f.get("make"): w.append("upper(trim(a.make))=upper(trim(:make))"); p["make"] = f["make"]
    if f.get("model"): w.append("upper(trim(a.model))=upper(trim(:model))"); p["model"] = f["model"]
    if re.fullmatch(r"\d{4}", f.get("year") or ""): w.append("a.year_from<=:year AND coalesce(a.year_to,9999)>=:year"); p["year"] = int(f["year"])
    if f.get("axle"): w.append("a.axle=:axle"); p["axle"] = f["axle"]
    if f.get("side"): w.append("(a.side=:side OR a.side='ambos')"); p["side"] = f["side"]
    return w

KEY = "replace(replace(replace(replace(replace(replace(upper({c}),'-',''),'.',''),'/',''),' ',''),'_',''),'\\','')"      # código sem pontuação: «16.470», «16-470» e «16470» são o mesmo código
def code_key(t): return re.sub(r"[^A-Z0-9]", "", str(t or "").upper())

def _where(f):
    w, p = [], {}
    for i, t in enumerate((f.get("q") or "").split()):
        k = f"t{i}"; p[k] = f"%{t}%"; p[k + "k"] = f"%{code_key(t)}%"
        c = (f"p.perfect_code LIKE :{k} OR p.description LIKE :{k} OR p.ean LIKE :{k} OR p.catalog_group LIKE :{k} "
             f"OR EXISTS(SELECT 1 FROM codes k WHERE k.product_id=p.id AND (k.code LIKE :{k} OR k.normalized_code LIKE :{k}" + (f" OR {KEY.format(c='k.code')} LIKE :{k}k" if len(code_key(t)) >= 3 else "") + ")) "
             f"OR EXISTS(SELECT 1 FROM applications a WHERE a.product_id=p.id AND ({APP_TXT}) LIKE :{k})")
        if re.fullmatch(r"(19|20)\d\d", t):
            p[k + "y"] = int(t); c += f" OR EXISTS(SELECT 1 FROM applications a WHERE a.product_id=p.id AND a.year_from<=:{k}y AND coalesce(a.year_to,9999)>=:{k}y)"
        w.append("(" + c + ")")
    if f.get("code") or f.get("code_type"):
        c = "SELECT 1 FROM codes k WHERE k.product_id=p.id"
        if f.get("code"): c += f" AND (k.code LIKE :code OR k.normalized_code LIKE :code OR {KEY.format(c='k.code')} LIKE :codek)"; p["code"] = f"%{f['code']}%"; p["codek"] = f"%{code_key(f['code'])}%"
        if f.get("code_type"): c += " AND k.code_type=:ctype"; p["ctype"] = f["code_type"]
        w.append(f"EXISTS({c})")
    ac = _app_conds(f, p)
    if ac: w.append("EXISTS(SELECT 1 FROM applications a WHERE a.product_id=p.id AND " + " AND ".join(ac) + ")")
    if f.get("system"): w.append("p.system_type=:system"); p["system"] = f["system"]
    if f.get("family"): w.append("upper(p.family)=upper(:family)"); p["family"] = f["family"]
    if f.get("launch") in ("S", "N"): w.append("coalesce(p.is_launch,'N')=:launch"); p["launch"] = f["launch"]
    try: rod = float(str(f.get("rod") or "").replace(",", "."))
    except ValueError: rod = None
    if rod is not None: w.append("EXISTS(SELECT 1 FROM dimensions d2 WHERE d2.product_id=p.id AND abs(d2.rod_diameter_mm-:rod)<0.001)"); p["rod"] = rod
    return w, p

def product_facets():
    """Opções (com contagem) dos filtros da tela Produtos: família, Ø da haste, sistema e lançamentos."""
    return {"family": q("SELECT family v, COUNT(*) n FROM products WHERE family IS NOT NULL GROUP BY 1 ORDER BY 2 DESC, 1"),
            "rod": q("SELECT rod_diameter_mm v, COUNT(*) n FROM dimensions WHERE rod_diameter_mm IS NOT NULL GROUP BY 1 ORDER BY 1"),
            "system": {r["s"]: r["n"] for r in q("SELECT coalesce(system_type,'nd') s, COUNT(*) n FROM products GROUP BY 1")},
            "launch": q1("SELECT COUNT(*) n FROM products WHERE is_launch='S'")["n"], "total": q1("SELECT COUNT(*) n FROM products")["n"],
            "catalogo": q1("SELECT COUNT(*) n FROM products WHERE catalog_position IS NOT NULL")["n"]}

def perfect_codes(term, limit=200):
    """BUSCA REVERSA: código de CONCORRENTE/OEM/marca (CrossCatalogo, aba Equivalências, planilhas Brands) → códigos PERFECT correspondentes.
    Comparação sem pontuação e exata (16.470 = 16-470 = 16470); termos com menos de 3 caracteres não convertem. Devolve lista ordenada e sem repetição."""
    k = code_key(term)
    if len(k) < 3: return []
    out = {r["c"] for r in q(f"SELECT DISTINCT p.perfect_code c FROM codes k JOIN products p ON p.id=k.product_id WHERE {KEY.format(c='k.code')}=? LIMIT ?", (k, limit))}
    out |= {r["c"] for r in q(f"SELECT DISTINCT perfect_code c FROM brand_items WHERE perfect_code IS NOT NULL AND {KEY.format(c='code')}=? LIMIT ?", (k, limit))}
    return sorted(c for c in out if c and code_key(c) != k)

def fob_quotes(d):
    """Cotações FOB do item (E-WIN / ZS / XGM), da mais barata para a mais cara; a(s) de menor preço leva(m) melhor=True (destaque «Melhor Preço» na ficha)."""
    if not d: return []
    qs = sorted(({"fornecedor": n, "preco": d.get(k)} for n, k in (("E-WIN", "fob_ewin"), ("ZS", "fob_zs"), ("XGM", "fob_xgm")) if d.get(k) is not None), key=lambda x: x["preco"])
    for x in qs: x["melhor"] = bool(qs) and x["preco"] == qs[0]["preco"]
    return qs

def products(f):
    w, p = _where(f); sw = " AND ".join(w) or "1=1"
    size = 10**9 if f.get("all") else min(int(f.get("size") or 50), 200); off = 0 if f.get("all") else (max(int(f.get("page") or 1), 1) - 1) * size
    total = q1(f"SELECT COUNT(*) n FROM products p WHERE {sw}", p)["n"]
    rows = q(f"""SELECT p.id,p.perfect_code,p.description,p.ean,p.weight_kg,p.fob,p.fob_supplier,p.catalog_position,p.catalog_group,p.system_type,p.family,p.is_launch,d.lmin_mm,d.lmax_mm,d.rod_diameter_mm,
      (SELECT COUNT(*) FROM applications a WHERE a.product_id=p.id) apps,(SELECT COUNT(*) FROM codes k WHERE k.product_id=p.id) ncodes,
      (SELECT COUNT(*) FROM pendencies x WHERE x.product_id=p.id AND x.status='aberta') pend
      FROM products p LEFT JOIN dimensions d ON d.product_id=p.id WHERE {sw}
      ORDER BY p.catalog_position IS NULL, p.catalog_position, p.perfect_code LIMIT {size} OFFSET {off}""", p)
    _via(rows, f)
    return {"total": total, "rows": rows, "size": size}

def _via(rows, f):
    """Busca por código de CONCORRENTE (ou OEM/fornecedor): em cada linha, `via` mostra qual referência casou — «MONROE 16470 (concorrente)» — para ninguém achar que é o código PERFECT."""
    toks = [code_key(t) for t in ((f.get("q") or "").split() + ([f["code"]] if f.get("code") else [])) if len(code_key(t)) >= 3]
    for r in rows: r["via"] = []
    if not toks or not rows: return
    ids = {r["id"]: r for r in rows}; ph = ",".join("?" * len(ids)); cond = " OR ".join(f"{KEY.format(c='code')} LIKE ?" for _ in toks)
    for k in q(f"SELECT product_id, code, brand, code_type FROM codes WHERE product_id IN ({ph}) AND ({cond}) ORDER BY code_type='concorrente' DESC, brand", [*ids, *[f"%{t}%" for t in toks]]):
        v = ids[k["product_id"]]["via"]
        if len(v) < 4: v.append({"code": k["code"], "brand": k["brand"], "type": k["code_type"]})

def ficha(pid):
    p = q1("SELECT * FROM products WHERE id=?", (pid,))
    if not p: return None
    P = lambda s, n=1: q(s, (pid,) * n)
    p["dimensions"] = q1("SELECT d.*,s.name source FROM dimensions d LEFT JOIN sources s ON s.id=d.source_id WHERE d.product_id=?", (pid,))
    p["codes"] = P("SELECT k.code,k.code_type,k.brand,s.name source,(s.name LIKE 'CrossCatalogo%') is_cross FROM codes k LEFT JOIN sources s ON s.id=k.source_id WHERE k.product_id=? ORDER BY k.code_type,k.code")
    p["cross"] = cross_for(pid)
    p["applications"] = P("SELECT a.*,s.name source FROM applications a LEFT JOIN sources s ON s.id=a.source_id WHERE a.product_id=? ORDER BY a.make,a.model,a.year_from")
    p["pair"] = P("""SELECT p2.id,p2.perfect_code,'esquerdo' lado FROM side_pairs sp JOIN products p2 ON p2.id=sp.left_product_id WHERE sp.right_product_id=?
                     UNION ALL SELECT p2.id,p2.perfect_code,'direito' FROM side_pairs sp JOIN products p2 ON p2.id=sp.right_product_id WHERE sp.left_product_id=?""", 2)
    try: p["fob_detail"] = q1("SELECT fob, fob_ewin, fob_zs, fob_xgm, fob_fornecedor, fob_origem, fob_data, fob_cod_fornecedor FROM fob_prices WHERE upper(trim(codigo))=upper(trim(?))", (p["perfect_code"],))
    except Exception: p["fob_detail"] = None
    p["fob_quotes"] = fob_quotes(p["fob_detail"])
    p["box"] = q1("SELECT * FROM packaging_boxes WHERE code=?", (p["package_code"],)) if p.get("package_code") else None
    p["components"] = P("SELECT component_code,component_desc,seq,qty,date_from,date_to FROM product_components WHERE product_id=? ORDER BY seq")
    p["certificates"] = P("SELECT c.inmetro_number,c.family,c.cert_description,s.name source FROM certificates c LEFT JOIN sources s ON s.id=c.source_id WHERE c.product_id=?")
    p["supplier_items"] = P("SELECT supplier_name,erp_code,item_type,supplier_code,supplier_code2 FROM supplier_items WHERE product_id=?")
    p["rd"] = P("SELECT code,suggestion,status,drawing_substatus,validation_substatus,supplier,make,vehicle,application_text,year_from,year_to FROM rd_projects WHERE product_id=?")
    p["pendencies"] = P("SELECT id,kind,field,description,status FROM pendencies WHERE product_id=? ORDER BY status,kind")
    p["equivalences"] = P("""SELECT e.id,e.score,e.confidence,e.status,pa.perfect_code a_code,pb.perfect_code b_code FROM equivalence_suggestions e
        JOIN products pa ON pa.id=e.product_a JOIN products pb ON pb.id=e.product_b WHERE e.product_a=? OR e.product_b=? ORDER BY e.score DESC""", 2)
    p["samples"] = q("SELECT id,sc_number,sample_code,supplier,stage FROM sample_orders WHERE product_id=? OR perfect_code=?", (pid, p["perfect_code"]))
    return p

def compare(ids): return [x for x in (ficha(i) for i in ids[:4]) if x]

def applications(f):
    p = {}; w = _app_conds(f, p)
    for i, t in enumerate((f.get("q") or "").split()): p[f"t{i}"] = f"%{t}%"; w.append(f"(({APP_TXT}) LIKE :t{i} OR p.perfect_code LIKE :t{i})")
    sw = " AND ".join(w) or "1=1"; size = 10**9 if f.get("all") else 100; off = 0 if f.get("all") else (max(int(f.get("page") or 1), 1) - 1) * size
    base = f"FROM applications a JOIN products p ON p.id=a.product_id WHERE {sw}"
    return {"total": q1("SELECT COUNT(*) n " + base, p)["n"], "size": size,
            "rows": q(f"SELECT a.id,a.make,a.model,a.version,a.application_text,a.year_from,a.year_to,a.axle,a.side,p.id product_id,p.perfect_code,p.catalog_position {base} ORDER BY a.make,a.model,a.year_from LIMIT {size} OFFSET {off}", p)}

def pendencies(f):
    w, p = [], {}
    for k in ("kind", "status"):
        if f.get(k): w.append(f"x.{k}=:{k}"); p[k] = f[k]
    for i, t in enumerate((f.get("q") or "").split()): w.append(f"(p.perfect_code LIKE :t{i} OR x.description LIKE :t{i} OR x.field LIKE :t{i})"); p[f"t{i}"] = f"%{t}%"
    sw = " AND ".join(w) or "1=1"; size = 10**9 if f.get("all") else 100; off = 0 if f.get("all") else (max(int(f.get("page") or 1), 1) - 1) * size
    base = f"FROM pendencies x LEFT JOIN products p ON p.id=x.product_id WHERE {sw}"
    return {"total": q1("SELECT COUNT(*) n " + base, p)["n"], "size": size, "kinds": [r["kind"] for r in q("SELECT DISTINCT kind FROM pendencies")],
            "rows": q(f"SELECT x.id,x.kind,x.field,x.description,x.status,p.id product_id,p.perfect_code {base} ORDER BY x.status,x.kind,p.perfect_code LIMIT {size} OFFSET {off}", p)}

def duplicates():
    return q("""SELECT k.code_type,k.normalized_code code,group_concat(DISTINCT p.perfect_code) products,COUNT(DISTINCT k.product_id) n
        FROM codes k JOIN products p ON p.id=k.product_id WHERE k.normalized_code IS NOT NULL AND coalesce(k.source_id,0) NOT IN (SELECT id FROM sources WHERE name LIKE 'CrossCatalogo%') GROUP BY k.code_type,k.normalized_code HAVING COUNT(DISTINCT k.product_id)>1 ORDER BY n DESC,code""")

def history():
    return {"batches": q("SELECT b.id,b.imported_at,b.filename,b.sheet,b.category,b.rows_read,b.rows_new,b.rows_updated,b.rows_conflict,b.rows_error,b.status FROM import_batches b ORDER BY b.id DESC LIMIT 200"),
            "sources": q("SELECT s.id,s.name,s.category,s.priority,(SELECT COUNT(*) FROM import_batches b WHERE b.source_id=s.id) imports,(SELECT COUNT(*) FROM generic_rows g WHERE g.source_id=s.id) generic_rows FROM sources s ORDER BY s.name")}

# ---- backup / restauração ----
BK = os.path.join(db.BASE, "backups")
def backups():
    os.makedirs(BK, exist_ok=True)
    return sorted([{"name": f, "size": os.path.getsize(os.path.join(BK, f)), "date": datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(BK, f))).strftime("%d/%m/%Y %H:%M")}
                   for f in os.listdir(BK) if f.endswith(".db")], key=lambda x: x["name"], reverse=True)
def backup_create(prefix="backup"):
    os.makedirs(BK, exist_ok=True); name = f"{prefix}_{datetime.datetime.now():%Y%m%d_%H%M%S}.db"
    s, d = sqlite3.connect(db.DB_PATH), sqlite3.connect(os.path.join(BK, name))
    try: s.backup(d)
    finally: s.close(); d.close()
    return name
def backup_restore(name):
    if not re.fullmatch(r"[\w\-]+\.db", name or "") or not os.path.exists(os.path.join(BK, name)): raise ValueError("Backup inválido.")
    safety = backup_create("antes_de_restaurar")
    s, d = sqlite3.connect(os.path.join(BK, name)), sqlite3.connect(db.DB_PATH)
    try: s.backup(d)
    finally: s.close(); d.close()
    db.migrate(); return safety

# ---- compra de amostras ----
STAGES = [("cotacao", "Cotação"), ("sc_aberta", "SC aberta"), ("chegou", "Chegou"), ("finalizado", "Projeto finalizado"), ("aprovado", "Aprovado")]
def samples(f):
    w, p = [], {}
    for k in ("stage", "supplier", "month", "side"):
        if f.get(k): w.append(f"o.{k}=:{k}"); p[k] = f[k]
    fl = {"enviar": "o.to_send=1", "pendente_fornecedor": "o.pending_supplier=1"}.get(f.get("flag") or "")      # atalhos da tela (batem com totals.to_send / pending_supplier)
    if fl: w.append(fl)
    for i, t in enumerate((f.get("q") or "").split()):
        w.append(f"(o.perfect_code LIKE :t{i} OR o.sample_code LIKE :t{i} OR o.application LIKE :t{i} OR o.sc_number LIKE :t{i} OR o.supplier LIKE :t{i} OR o.ship_code LIKE :t{i})"); p[f"t{i}"] = f"%{t}%"
    rows = q(f"SELECT o.*,(SELECT p.description FROM products p WHERE p.id=o.product_id) description FROM sample_orders o WHERE {' AND '.join(w) or '1=1'} ORDER BY o.id DESC", p)
    quotes = {}
    for r in q("SELECT * FROM sample_quotes ORDER BY id"): quotes.setdefault(r["order_id"], []).append(r)
    ship = {s["order_id"]: s for s in q("SELECT order_id,status,ex_code,shipped_at FROM sample_shipments WHERE order_id IS NOT NULL")}   # vínculo com Envio de amostra
    chosen = best = 0.0
    for r in rows:
        sh = ship.get(r["id"]); r["ship_status"] = sh["status"] if sh else None; r["ship_ex"] = sh["ex_code"] if sh else None; r["ship_date"] = sh["shipped_at"] if sh else None
        r["quotes"] = quotes.get(r["id"], []); pr = [x["price"] for x in r["quotes"] if x["price"] is not None]
        ch = [x["price"] for x in r["quotes"] if x["chosen"] and x["price"] is not None]
        chosen += ch[0] if ch else 0; best += min(pr) if pr else 0
    opts = lambda c: [r[c] for r in q(f"SELECT DISTINCT {c} FROM sample_orders WHERE {c} IS NOT NULL AND {c}<>'' ORDER BY {c}")]
    return {"rows": rows, "stages": STAGES, "suppliers": opts("supplier"), "months": opts("month"),
            "totals": {"n": len(rows), "chosen": round(chosen, 2), "best": round(best, 2), "best_sheet": round(sum(r.get("best_price") or 0 for r in rows), 2), "usd": round(sum(r.get("price_usd") or 0 for r in rows), 2), "pending_supplier": sum(r["pending_supplier"] for r in rows), "to_send": sum(r["to_send"] for r in rows)}}

def sample_save(d):
    if d.get("stage") not in [s for s, _ in STAGES]: d["stage"] = "cotacao"
    num = lambda v: None if v in (None, "") else float(str(v).replace(",", "."))
    pc = (d.get("perfect_code") or "").strip() or None; pr = q1("SELECT id FROM products WHERE perfect_code=?", (pc,)) if pc else None
    side = d.get("side") if d.get("side") in ("direito", "esquerdo", "ambos") else None
    ship = (d.get("ship_code") or "").strip() or (("D-" + pc) if pc else None)   # D- + código, quando não informado
    vals = (pr["id"] if pr else None, pc, ship, d.get("sc_number"), d.get("application"), d.get("sample_code"), d.get("supplier"), d.get("month"), d.get("tracking"),
            num(d.get("net_weight")), num(d.get("gross_weight")), d.get("credit_note"), d["stage"], int(bool(d.get("to_send"))), int(bool(d.get("pending_supplier"))), d.get("notes"), side)
    c = db.conn()
    try:
        if d.get("id"):
            c.execute("UPDATE sample_orders SET product_id=?,perfect_code=?,ship_code=?,sc_number=?,application=?,sample_code=?,supplier=?,month=?,tracking=?,net_weight=?,gross_weight=?,credit_note=?,stage=?,to_send=?,pending_supplier=?,notes=?,side=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", vals + (d["id"],)); oid = d["id"]
            c.execute("DELETE FROM sample_quotes WHERE order_id=?", (oid,))
        else:
            oid = c.execute("INSERT INTO sample_orders(product_id,perfect_code,ship_code,sc_number,application,sample_code,supplier,month,tracking,net_weight,gross_weight,credit_note,stage,to_send,pending_supplier,notes,side) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", vals).lastrowid
        for qt in d.get("quotes") or []:
            if num(qt.get("price")) is not None or (qt.get("link") or "").strip():
                c.execute("INSERT INTO sample_quotes(order_id,price,link,chosen) VALUES(?,?,?,?)", (oid, num(qt.get("price")), (qt.get("link") or "").strip() or None, int(bool(qt.get("chosen")))))
        c.commit(); return oid
    finally: c.close()


# ---- preenchimento automático da amostra a partir do código PERFECT ----
_AX = {"dianteiro": "DIANT.", "traseiro": "TRAS."}
_SD = {"ambos": "LD/LE", "direito": "LD", "esquerdo": "LE"}
def _axle_from_text(t):
    d = (t or "").upper(); return "dianteiro" if re.search(r"DIANT|FRONT", d) else "traseiro" if re.search(r"TRAS|REAR", d) else None
def _clean(v):
    v = (v or "").strip().lstrip("'").strip(); return None if v in ("", "-", "NA", "N/A") else v
def _app_text(make, model, extra, axle, side, yf, yt):
    """Mesmo padrão das planilhas: MONTADORA - MODELO - DIANT. LD/LE - 2021/2025."""
    veh = " ".join(x for x in (_clean(model), _clean(extra)) if x)
    ax = " ".join(x for x in (_AX.get(axle), _SD.get(side)) if x)
    yr = (f"{yf}/{yt}" if yt and yt != yf else str(yf)) if yf else None
    return " - ".join(x for x in (_clean(make), veh or None, ax or None, yr) if x)

def sample_prefill(code):
    code = re.sub(r"[/\s]", "", (code or "").strip().upper())
    if code.startswith("MP-") or code.startswith("D-"): code = code[3:] if code.startswith("MP-") else code[2:]
    if not code: return {"code": "", "ship_code": None, "application": None, "side": None, "source": None, "options": []}
    opts, side = [], None
    for r in q("SELECT make,vehicle,application_text,year_from,year_to,description,suggestion FROM rd_projects WHERE upper(code)=? ORDER BY CASE suggestion WHEN 'DESENVOLVIMENTO' THEN 0 ELSE 1 END,id", (code,)):
        sd = db.side_from_text(r["description"]); ax = _axle_from_text(r["description"])
        t = _app_text(r["make"], r["vehicle"], r["application_text"], ax, sd, r["year_from"], r["year_to"])
        if t and t not in [o["text"] for o in opts]: opts.append({"text": t, "source": "Desenvolvimento" if r["suggestion"] == "DESENVOLVIMENTO" else "Redesenvolvimento", "side": sd})
        side = side or sd
    if not opts:   # sem item em desenvolvimento: usa a aplicação do catálogo
        for r in q("SELECT a.make,a.model,a.application_text,a.year_from,a.year_to,a.axle,a.side FROM applications a JOIN products p ON p.id=a.product_id WHERE p.perfect_code=? ORDER BY a.id", (code,)):
            t = _app_text(r["make"], r["model"], r["application_text"], r["axle"], r["side"], r["year_from"], r["year_to"])
            if t and t not in [o["text"] for o in opts]: opts.append({"text": t, "source": "Catálogo", "side": r["side"]})
            side = side or r["side"]
    if not side:   # pares direito/esquerdo (planilha Lados)
        if q1("SELECT 1 FROM side_pairs sp JOIN products p ON p.id=sp.right_product_id WHERE p.perfect_code=?", (code,)): side = "direito"
        elif q1("SELECT 1 FROM side_pairs sp JOIN products p ON p.id=sp.left_product_id WHERE p.perfect_code=?", (code,)): side = "esquerdo"
    if not side and q1("SELECT 1 FROM products WHERE perfect_code=?", (code,)):
        side = db.side_from_text((q1("SELECT description FROM products WHERE perfect_code=?", (code,)) or {}).get("description"))
    pr = q1("SELECT description FROM products WHERE perfect_code=?", (code,))
    return {"code": code, "ship_code": "D-" + code, "application": opts[0]["text"] if opts else None, "side": side,
            "source": opts[0]["source"] if opts else None, "options": opts, "in_catalog": bool(pr), "description": pr["description"] if pr else None}


def cross_for(pid):
    """Referência cruzada do produto (concorrentes e OEM da planilha CrossCatalogo): [{brand, code}], marcas de reposição primeiro, OEM por último."""
    rows = q("SELECT k.brand,k.code FROM codes k JOIN sources s ON s.id=k.source_id WHERE k.product_id=? AND s.name LIKE 'CrossCatalogo%' ORDER BY k.brand,k.code", (pid,))
    return sorted(rows, key=lambda r: (r["brand"] == "OEM", r["brand"] or "", r["code"]))
