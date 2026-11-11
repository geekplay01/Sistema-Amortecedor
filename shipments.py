"""Envio de amostra — vinculado à Compra de amostra.
Fluxo:  Compra (nº da SC)  →  amostra recebida  ⇒ status «Pendente projeto»  →  amostra enviada ao fornecedor ⇒ «Amostra enviada» (com o EX do fornecedor)  →  finalizada.
Fontes: pedidos de Compra de amostra (etapa «Chegou») e a planilha de Desenvolvimento (datas de amostra comprada/enviada e sub status «Pendente projeto»)."""
import re, datetime
import database as db
from queries import q, q1

STATUS = {"pendente_projeto": "Pendente projeto", "enviada": "Amostra enviada", "finalizada": "Finalizada"}
DONE_RD = ("ITEM RECEBIDO",)   # item de desenvolvimento já recebido do fornecedor = envio finalizado
def _k(c): return re.sub(r"[^A-Z0-9]", "", (c or "").upper())
def canon_supplier(s):
    t = re.sub(r"[^A-Z0-9]", "", (s or "").upper())
    return {"EWIN": "E-WIN", "ZS": "ZS", "XGM": "XGM"}.get(t, (s or "").strip().upper() or None)
def ex_map(): return {r["supplier"]: r["ex_code"] for r in q("SELECT supplier,ex_code FROM supplier_ex")}
def ex_for(sup): return ex_map().get(canon_supplier(sup))
def today(): return datetime.date.today().isoformat()

def sync():
    """Mantém os envios coerentes com Compra de amostra e com a planilha de Desenvolvimento (idempotente; não apaga nada)."""
    c = db.conn(); exm = {r[0]: r[1] for r in c.execute("SELECT supplier,ex_code FROM supplier_ex")}; new = upd = 0
    try:
        ship = {}   # código normalizado -> envios
        for r in c.execute("SELECT * FROM sample_shipments"): ship.setdefault(_k(r["perfect_code"]), []).append(dict(zip(r.keys(), tuple(r))))
        def insert(**v):
            nonlocal new
            v.setdefault("origin", "planilha"); sup = canon_supplier(v.get("supplier")); v["supplier"] = sup; v["ex_code"] = v.get("ex_code") or exm.get(sup)
            cols = ",".join(v); cur = c.execute(f"INSERT INTO sample_shipments({cols}) VALUES({','.join('?' * len(v))})", list(v.values())); new += 1
            ship.setdefault(_k(v["perfect_code"]), []).append({"id": cur.lastrowid, **v}); return cur.lastrowid
        def update(sid, **v):
            nonlocal upd
            c.execute("UPDATE sample_shipments SET " + ",".join(f"{k}=?" for k in v) + ",updated_at=CURRENT_TIMESTAMP WHERE id=?", [*v.values(), sid]); upd += 1
        # 1) planilha de Desenvolvimento / Redesenvolvimento
        for r in c.execute("""SELECT code,MAX(description) d,MAX(supplier) sup,MAX(sample_bought) bought,MAX(sample_sent) sent,MAX(CASE WHEN project_substatus LIKE '%PENDENTE PROJETO%' THEN 1 ELSE 0 END) pp,
                              MAX(CASE WHEN status IN ('ITEM RECEBIDO') THEN 1 ELSE 0 END) done,MAX(vehicle) veh,MAX(make) mk FROM rd_projects GROUP BY code"""):
            code, sent, pp = r["code"], r["sent"], r["pp"]
            if not sent and not pp: continue
            sup = canon_supplier(r["sup"]); lst = ship.get(_k(code), []); app = " ".join(x for x in (r["mk"], r["veh"]) if x) or None
            if sent:
                hit = next((s for s in lst if s["shipped_at"] == sent), None) or next((s for s in lst if s["status"] == "pendente_projeto"), None)
                if hit:
                    ch = {}
                    if hit["status"] == "pendente_projeto": ch.update(status="enviada", shipped_at=sent)
                    if not hit["supplier"] and sup: ch.update(supplier=sup, ex_code=exm.get(sup))
                    if not hit["bought_at"] and r["bought"]: ch["bought_at"] = r["bought"]
                    if r["done"] and hit["status"] == "enviada" and hit["origin"] == "planilha" and not hit.get("notes"): ch["status"] = "finalizada"
                    if ch: update(hit["id"], **ch); hit.update(ch)
                else:
                    insert(perfect_code=code, description=r["d"], application=app, side=db.side_from_text(r["d"]), supplier=sup, bought_at=r["bought"], shipped_at=sent, status="finalizada" if r["done"] else "enviada")
            elif pp and not lst:
                insert(perfect_code=code, description=r["d"], application=app, side=db.side_from_text(r["d"]), supplier=sup, bought_at=r["bought"], status="pendente_projeto")
        # 2) pedidos de Compra de amostra: «Chegou» ⇒ pendente projeto; vincula o nº da SC
        for o in c.execute("SELECT id,perfect_code,application,side,supplier,sc_number,stage,date(updated_at) up FROM sample_orders WHERE perfect_code IS NOT NULL").fetchall():
            o = dict(zip(("id", "perfect_code", "application", "side", "supplier", "sc_number", "stage", "up"), tuple(o))); lst = ship.get(_k(o["perfect_code"]), [])
            mine = next((s for s in lst if s.get("order_id") == o["id"]), None)
            if mine:
                ch = {k: o[k] for k in ("sc_number",) if o[k] and not mine.get(k)}
                if ch: update(mine["id"], **ch)
                continue
            free = next((s for s in lst if not s.get("order_id") and s["status"] in ("pendente_projeto", "enviada")), None)
            if free: update(free["id"], order_id=o["id"], sc_number=o["sc_number"] or free.get("sc_number")); free["order_id"] = o["id"]; continue
            if o["stage"] == "chegou":
                desc = (c.execute("SELECT description FROM products WHERE perfect_code=?", (o["perfect_code"],)).fetchone() or [None])[0]
                insert(order_id=o["id"], perfect_code=o["perfect_code"], description=desc, application=o["application"], side=o["side"], supplier=o["supplier"], sc_number=o["sc_number"], received_at=o["up"], status="pendente_projeto", origin="compra")
        c.commit()
    finally: c.close()
    return {"new": new, "updated": upd}

def _rows(f):
    w, p = [], {}
    st = f.get("status") or "abertos"
    if st == "abertos": w.append("s.status IN ('pendente_projeto','enviada')")
    elif st in STATUS: w.append("s.status=:st"); p["st"] = st
    if f.get("supplier") == "sem": w.append("(s.supplier IS NULL OR s.supplier='')")
    elif f.get("supplier"): w.append("s.supplier=:sup"); p["sup"] = f["supplier"]
    for i, t in enumerate((f.get("q") or "").split()):
        w.append(f"(s.perfect_code LIKE :t{i} OR s.description LIKE :t{i} OR s.application LIKE :t{i} OR s.sc_number LIKE :t{i} OR s.ex_code LIKE :t{i} OR s.tracking LIKE :t{i})"); p[f"t{i}"] = f"%{t}%"
    return q(f"""SELECT s.*,o.stage order_stage,(SELECT p.id FROM products p WHERE p.perfect_code=s.perfect_code) product_id,
                 (SELECT MAX(r.suggestion) FROM rd_projects r WHERE r.code=s.perfect_code) rd_kind FROM sample_shipments s LEFT JOIN sample_orders o ON o.id=s.order_id
                 WHERE {' AND '.join(w) or '1=1'} ORDER BY CASE s.status WHEN 'pendente_projeto' THEN 0 WHEN 'enviada' THEN 1 ELSE 2 END, s.supplier, coalesce(s.shipped_at,s.received_at,s.bought_at) DESC, s.id DESC""", p)

def listing(f):
    sync()
    rows = _rows(f); size = 50 if not f.get("all") else 10**9; page = max(1, int(f.get("page") or 1))
    for r in rows: r["status_label"] = STATUS.get(r["status"], r["status"]); r["rd"] = {"DESENVOLVIMENTO": "des", "REDESENVOLVIMENTO": "rd"}.get(r["rd_kind"])
    return {"total": len(rows), "page": page, "size": size, "rows": rows[(page - 1) * size: page * size], "summary": summary(), "statuses": STATUS}

def summary():
    sup = [{"supplier": r["supplier"], "ex": r["ex_code"], "full": r["full_name"]} for r in q("SELECT * FROM supplier_ex ORDER BY supplier")]
    cnt = {(r["supplier"] or "", r["status"]): r["n"] for r in q("SELECT supplier,status,COUNT(*) n FROM sample_shipments GROUP BY 1,2")}
    out = [{**s, "pendente_projeto": cnt.get((s["supplier"], "pendente_projeto"), 0), "enviada": cnt.get((s["supplier"], "enviada"), 0), "finalizada": cnt.get((s["supplier"], "finalizada"), 0)} for s in sup]
    known = {s["supplier"] for s in sup}
    other = {"supplier": None, "ex": None, "full": "Sem fornecedor", "pendente_projeto": sum(n for (s, st), n in cnt.items() if s not in known and st == "pendente_projeto"), "enviada": sum(n for (s, st), n in cnt.items() if s not in known and st == "enviada"),
             "finalizada": sum(n for (s, st), n in cnt.items() if s not in known and st == "finalizada")}
    return {"suppliers": out, "other": other, "pendente_projeto": sum(n for (s, st), n in cnt.items() if st == "pendente_projeto"), "enviada": sum(n for (s, st), n in cnt.items() if st == "enviada"), "finalizada": sum(n for (s, st), n in cnt.items() if st == "finalizada")}

def create(d):
    code = (d.get("perfect_code") or "").strip().upper()
    if not code: raise ValueError("Informe o código.")
    sup = canon_supplier(d.get("supplier")); pr = q1("SELECT description FROM products WHERE perfect_code=?", (code,))
    c = db.conn()
    try:
        cur = c.execute("INSERT INTO sample_shipments(perfect_code,description,application,side,supplier,ex_code,sc_number,bought_at,received_at,status,tracking,notes,origin) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (code, (pr or {}).get("description") or d.get("description"), d.get("application"), d.get("side") or db.side_from_text(d.get("application")), sup, ex_for(sup), d.get("sc_number"), d.get("bought_at"), d.get("received_at") or today(), "pendente_projeto", d.get("tracking"), d.get("notes"), "manual"))
        c.commit(); return cur.lastrowid
    finally: c.close()

def update_one(sid, d):
    f = {k: (d.get(k) or None) for k in ("application", "sc_number", "bought_at", "received_at", "shipped_at", "tracking", "notes", "description") if k in d}
    if "side" in d: f["side"] = d["side"] if d["side"] in ("direito", "esquerdo", "ambos") else None
    if "supplier" in d: f["supplier"] = canon_supplier(d["supplier"]); f["ex_code"] = ex_for(d["supplier"]) if d["supplier"] else None
    if d.get("status") in STATUS: f["status"] = d["status"]
    if not f: return
    c = db.conn()
    try: c.execute("UPDATE sample_shipments SET " + ",".join(f"{k}=?" for k in f) + ",updated_at=CURRENT_TIMESTAMP WHERE id=?", [*f.values(), sid]); c.commit()
    finally: c.close()

def mark_sent(ids, supplier=None, date=None, tracking=None, notes=None):
    """Passa os envios para «Amostra enviada» (data, fornecedor e o EX dele). Sem fornecedor informado, mantém o do envio."""
    sup = canon_supplier(supplier) if supplier else None; c = db.conn(); n = 0
    try:
        for sid in ids:
            cur = c.execute("SELECT supplier FROM sample_shipments WHERE id=?", (sid,)).fetchone()
            if not cur: continue
            s = sup or cur[0]
            if not s: raise ValueError("Informe o fornecedor para gerar o EX.")
            c.execute("UPDATE sample_shipments SET status='enviada',supplier=?,ex_code=?,shipped_at=?,tracking=coalesce(?,tracking),notes=coalesce(?,notes),updated_at=CURRENT_TIMESTAMP WHERE id=?",
                      (s, ex_map().get(s), date or today(), tracking or None, notes or None, sid)); n += 1
        c.commit()
    except Exception:
        c.rollback(); raise
    finally: c.close()
    return n

def set_status(ids, status):
    if status not in STATUS: raise ValueError("Status desconhecido.")
    c = db.conn()
    try:
        for sid in ids:
            extra = ",shipped_at=NULL" if status == "pendente_projeto" else ""
            c.execute(f"UPDATE sample_shipments SET status=?{extra},updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, sid))
        c.commit()
    finally: c.close()
    return len(ids)

def delete(sid):
    c = db.conn()
    try: c.execute("DELETE FROM sample_shipments WHERE id=?", (sid,)); c.commit()
    finally: c.close()

def set_ex(supplier, ex_code, full=None):
    sup = canon_supplier(supplier)
    if not sup or not re.fullmatch(r"EX\d{4,10}", (ex_code or "").strip().upper()): raise ValueError("Informe o fornecedor e um EX no formato EX0002116.")
    c = db.conn()
    try:
        c.execute("INSERT INTO supplier_ex(supplier,ex_code,full_name) VALUES(?,?,?) ON CONFLICT(supplier) DO UPDATE SET ex_code=excluded.ex_code,full_name=coalesce(excluded.full_name,full_name)", (sup, ex_code.strip().upper(), full))
        c.execute("UPDATE sample_shipments SET ex_code=? WHERE supplier=? AND status='enviada'", (ex_code.strip().upper(), sup)); c.commit()
    finally: c.close()
