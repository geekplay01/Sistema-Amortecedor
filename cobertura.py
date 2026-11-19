"""Cobertura de concorrentes (etapa 17 · Q12/Q13/Q21–Q23/Q27/Q28) — tela «Cobertura de concorrentes».
  • Catálogo (aba padrão): só itens do catálogo. Uma linha por concorrente × referência × nosso código, com descrição, aplicação, linha, curva ABC de vendas
    do nosso item (12 meses fechados, universo do BI — curva_abc.classes) e situação do estoque (estoque.mapa). Referências pela regra Q18
    (CrossCatalogo quando a planilha tem o item; senão o servidor). OEM não é concorrente e fica fora.
    Cartões por concorrente (códigos nossos cobertos e quantos em A/B/C); atalhos concorrente, curva e linha — cada contagem = lista ao clicar.
  • Desenvolvimento: DES em andamento (universo amortecedor, não bloqueado, sem ITEM RECEBIDO e sem cancelado; R-D fora; só PERFECT AMD… — itens de montadora
    BPROAUTO/MOTRIO/MOTORCRAFT fora desde a etapa 18 · Q10) com curva PRÓPRIA pela frota:
      frota do item = soma da frota do ano atual dos veículos da Fraga (LANÇAMENTOS) que batem com a aplicação — mesma marca, nome do veículo e ano de venda dentro
      dos anos da aplicação (várias aplicações somam; o mesmo veículo × ano não conta duas vezes);
      sem casamento → frota do arquivo COFAP × Fraga pela referência COFAP do servidor; por último a FROTA do servidor (DESENVOLVIMENTO_PRODUTOS).
      Curva A até 80% da frota acumulada, B até 95%, C o resto; sem frota = «sem dado». Selo «Lançamento» = algum veículo com início de produção a partir de 2024."""
import re, json, datetime, unicodedata
from collections import Counter
from queries import q, q1

LANC_DESDE = 2024
def _un(s): return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().upper()
def _tok(s): return re.sub(r"[^A-Z0-9 ]", " ", _un(s)).split()
def _k(c): return re.sub(r"[^A-Z0-9]", "", re.sub(r"^\s*MP-", "", str(c or "").upper()))
def _ano(v):
    m = re.match(r"\s*(\d{4})", str(v or "")); return int(m.group(1)) if m else None

# ---------------- catálogo ----------------
def _catalogo_rows():
    import concorrentes as cc, curva_abc, estoque
    prods = {r["id"]: r for r in q("SELECT id, perfect_code, description, catalog_line FROM products WHERE catalog_position IS NOT NULL")}
    cross = {}
    for r in q("""SELECT k.product_id, k.brand, k.code FROM codes k JOIN sources s ON s.id=k.source_id WHERE s.name=? AND k.code_type='concorrente'""", (cc.CROSS_SRC,)):
        if r["product_id"] in prods: cross.setdefault(r["product_id"], []).append((cc.nome(r["brand"]) or "—", r["code"]))
    srv = {}
    if cc.available():
        for r in q("SELECT code, competitor, MIN(reference) reference FROM concorrentes WHERE is_oem=0 GROUP BY code, competitor, ref_key"):
            srv.setdefault(r["code"], []).append((r["competitor"], r["reference"]))
    apps = {}
    for r in q("SELECT product_id, make, model, year_from, year_to FROM applications ORDER BY make, model, year_from"):
        if r["product_id"] in prods:
            t = " ".join(x for x in (r["make"], r["model"]) if x)
            if r["year_from"] or r["year_to"]: t += f" {r['year_from'] or '…'}–{r['year_to'] or '…'}"
            lst = apps.setdefault(r["product_id"], [])
            if t and t not in lst: lst.append(t)
    cls = curva_abc.classes(); est, _, _ = estoque.mapa()
    def linha(pid, comp, ref, fonte):
        p = prods[pid]; k = _k(p["perfect_code"]); a = apps.get(pid, [])
        return {"concorrente": comp, "referencia": ref, "codigo": p["perfect_code"], "product_id": pid, "descricao": p["description"], "linha": p["catalog_line"],
                "aplicacao": " · ".join(a[:3]) + (f" (+{len(a) - 3})" if len(a) > 3 else ""), "curva": cls.get(k) or "sem", "situacao": (est.get(k) or {}).get("situacao") or "sem", "fonte": fonte}
    out = []
    for pid, p in prods.items():
        refs = cross.get(pid) or srv.get(p["perfect_code"].upper()) or []
        fonte = "CrossCatalogo" if pid in cross else "servidor"
        for comp, ref in refs: out.append(linha(pid, comp, ref, fonte))
    corr = correcoes_map()          # etapa 19 · Q7: «Nosso código» corrigido na tela vale sobre o CrossCatalogo e o servidor
    if corr:
        por_codigo = {p["perfect_code"].upper(): pid for pid, p in prods.items()}
        out = [r for r in out if (r["concorrente"], _k(r["referencia"])) not in corr]
        for (comp, _rk), c in corr.items():
            for cod in c["codigos"]:
                if cod in por_codigo: out.append(linha(por_codigo[cod], comp, c["referencia"], "corrigido no app"))
    out.sort(key=lambda r: (r["concorrente"], r["codigo"], r["referencia"]))
    return out

# ---------------- correções do «Nosso código» feitas na tela (etapa 19 · Q7) ----------------
CORR_TABLE = """CREATE TABLE IF NOT EXISTS cross_correcoes(concorrente TEXT NOT NULL, ref_key TEXT NOT NULL, referencia TEXT, codigos TEXT, antes TEXT, por TEXT,
  em TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(concorrente, ref_key))"""
def _corr_ensure():
    import database as db
    c = db.conn()
    try: c.execute(CORR_TABLE); c.commit()
    finally: c.close()
def correcoes_map():
    """{(concorrente, ref_key): {referencia, codigos: [...], antes: [...], por, em}} — o conjunto de códigos PERFECT daquela referência (vazio = sem ligação)."""
    try: rows = q("SELECT * FROM cross_correcoes")
    except Exception: return {}
    sp = lambda t: [x for x in (t or "").split(",") if x]
    return {(r["concorrente"], r["ref_key"]): {**r, "codigos": sp(r["codigos"]), "antes": sp(r["antes"])} for r in rows}

def _valido(code):
    """Código PERFECT (AMD…) do catálogo ou de DES/R-D. → None se ok, senão o motivo."""
    c = _k(code)
    if not c.startswith("AMD"): return f"{c} não é código PERFECT (AMD…)."
    if not (q1("SELECT 1 FROM products WHERE upper(perfect_code)=?", (c,)) or q1("SELECT 1 FROM rd_projects WHERE upper(code)=? LIMIT 1", (c,))): return f"{c} não está no catálogo nem em DES/R-D."
    return None

def codigos_da_referencia(concorrente, referencia):
    """Conjunto atual (efetivo) de códigos PERFECT ligados à referência: catálogo (com as correções) e, na COFAP, os DES/R-D AMD da regra da aba."""
    rk = _k(referencia); cods = {r["codigo"].upper() for r in _catalogo_rows() if r["concorrente"] == concorrente and _k(r["referencia"]) == rk}
    corr = correcoes_map().get((concorrente, rk))
    if corr: return sorted(set(corr["codigos"]))
    if _has("concorrentes"):
        cods |= {r["c"] for r in q("SELECT DISTINCT upper(code) c FROM concorrentes WHERE competitor=? AND ref_key=? AND is_oem=0 AND upper(code) LIKE 'AMD%'", (concorrente, rk))}
    return sorted(cods)

def corrigir(concorrente, referencia, de=None, para=None, codigos=None, por=None):
    """Grava a correção. `codigos` = conjunto completo; ou `de` → `para` troca um código do conjunto atual (de vazio = acrescenta; para vazio = tira).
    → {"anterior": correção que existia (ou None), "codigos": novo conjunto}"""
    if not concorrente or not _k(referencia): raise ValueError("Informe o concorrente e a referência.")
    atual = codigos_da_referencia(concorrente, referencia)
    if codigos is None:
        novo = [c for c in atual if c != _k(de or "")]
        if _k(para or ""): novo.append(_k(para))
    else: novo = [_k(c) for c in codigos if _k(c)]
    novo = sorted(set(novo))
    for c in novo:
        err = _valido(c)
        if err: raise ValueError(err)
    _corr_ensure(); ant = correcoes_map().get((concorrente, _k(referencia)))
    import database as db
    c = db.conn()
    try:
        c.execute("""INSERT INTO cross_correcoes(concorrente, ref_key, referencia, codigos, antes, por) VALUES(?,?,?,?,?,?)
                     ON CONFLICT(concorrente, ref_key) DO UPDATE SET codigos=excluded.codigos, referencia=excluded.referencia, por=excluded.por, em=CURRENT_TIMESTAMP""",
                  (concorrente, _k(referencia), referencia.strip(), ",".join(novo), ",".join(ant["antes"] if ant else atual), por)); c.commit()
    finally: c.close()
    _CCACHE.clear()
    return {"anterior": ({k: ant[k] for k in ("referencia", "codigos", "antes", "por")} if ant else None), "codigos": novo}

def desfazer(concorrente, referencia, anterior=None):
    """Volta ao que era antes da última correção: sem correção anterior apaga a linha (vale de novo o CrossCatalogo/servidor)."""
    _corr_ensure(); import database as db
    c = db.conn()
    try:
        if anterior: c.execute("UPDATE cross_correcoes SET codigos=?, antes=?, em=CURRENT_TIMESTAMP WHERE concorrente=? AND ref_key=?", (",".join(anterior.get("codigos") or []), ",".join(anterior.get("antes") or []), concorrente, _k(referencia)))
        else: c.execute("DELETE FROM cross_correcoes WHERE concorrente=? AND ref_key=?", (concorrente, _k(referencia)))
        c.commit()
    finally: c.close()
    _CCACHE.clear()

def correcoes(qtxt=""):
    """Aba «Cross corrigido no app» de Anomalias: para levar ao CrossCatalogo.xlsx."""
    t = (qtxt or "").upper().split()
    rows = [{"concorrente": k[0], "referencia": c["referencia"], "antes": ", ".join(c["antes"]) or "—", "depois": ", ".join(c["codigos"]) or "(sem ligação)", "em": c["em"], "por": c["por"]}
            for k, c in sorted(correcoes_map().items(), key=lambda x: x[1]["em"] or "", reverse=True)]
    return [r for r in rows if all(x in f"{r['concorrente']} {r['referencia']} {r['antes']} {r['depois']}".upper() for x in t)]

CAT_F = ("concorrente", "curva", "linha")
def catalogo(f=None, page=1, size=200):
    f = f or {}; rows = _catalogo_rows(); term = (f.get("q") or "").upper().split()
    def ok(r, skip=""):
        for k in CAT_F:
            if k != skip and f.get(k) and str(r.get(k) or "sem") != f[k]: return False
        return all(t in f"{r['concorrente']} {r['referencia']} {r['codigo']} {r['descricao'] or ''} {r['aplicacao']}".upper() for t in term)
    sel = [r for r in rows if ok(r)]
    counts = {k: dict(Counter(str(r.get(k) or "sem") for r in rows if ok(r, k)).most_common()) for k in CAT_F}
    # cartões: por concorrente, códigos nossos cobertos e quantos em A/B/C (com os outros filtros, sem o de concorrente)
    cards = {}
    for r in (r for r in rows if ok(r, "concorrente")):
        c = cards.setdefault(r["concorrente"], {"concorrente": r["concorrente"], "codigos": set(), "A": set(), "B": set(), "C": set()})
        c["codigos"].add(r["codigo"])
        if r["curva"] in "ABC" and r["curva"] != "sem": c[r["curva"]].add(r["codigo"])
    cards = sorted(({"concorrente": c["concorrente"], "codigos": len(c["codigos"]), "A": len(c["A"]), "B": len(c["B"]), "C": len(c["C"])} for c in cards.values()), key=lambda c: -c["codigos"])
    catalogo_total = q1("SELECT COUNT(*) n FROM products WHERE catalog_position IS NOT NULL")["n"]
    nossos = len({r["codigo"] for r in sel})
    page = max(int(page or 1), 1); n = 10**9 if f.get("all") else size
    return {"total": len(sel), "rows": sel[(page - 1) * n: page * n], "page": page, "size": n, "counts": counts, "cards": cards,
            "kpis": {"referencias": len(sel), "concorrentes": len({r["concorrente"] for r in sel}), "nossos_codigos": nossos, "catalogo": catalogo_total}}

# ---------------- desenvolvimento ----------------
_CACHE = {}
def _fraga_index():
    """{marca: [(id, tokens do veículo, ano de venda, frota, início de produção, nome)]} — LANÇAMENTOS da Fraga."""
    try: rows = q("SELECT rowid id, marca, veiculo, modelo, ano_venda, frota, inicio FROM fraga_veiculos WHERE frota > 0")
    except Exception: rows = []
    idx = {}
    for r in rows:
        idx.setdefault(" ".join(_tok(r["marca"])), []).append((r["id"], set(_tok(r["veiculo"])), _tok(r["veiculo"]), r["ano_venda"], r["frota"] or 0, _ano(r["inicio"]), f"{r['marca']} {r['veiculo']} {r['ano_venda']}"))
    return idx

def _match(idx, make, vehicle, y0, y1):
    """Veículos da Fraga da mesma marca cujo nome contém as duas primeiras palavras do veículo da aplicação (a 1ª no começo), com ano de venda dentro da aplicação."""
    cand = idx.get(" ".join(_tok(make)))
    vt = _tok(vehicle)
    if not cand or not vt: return []
    want = vt[:2]
    return [c for c in cand if c[2] and c[2][0] == want[0] and all(w in c[1] for w in want) and (y0 is None or (c[3] or 0) >= y0) and (y1 is None or (c[3] or 9999) <= y1)]

def _des_rows():
    import rules, kinds, concorrentes as cc
    key = (datetime.date.today().isoformat(), (q1("SELECT MAX(id) i FROM ds_runs") or {}).get("i"), (q1("SELECT COUNT(*) n FROM fraga_veiculos") or {}).get("n") if _has("fraga_veiculos") else 0,
           (q1("SELECT COUNT(*) n FROM fraga_pecas") or {}).get("n") if _has("fraga_pecas") else 0)
    if _CACHE.get("k") == key: return _CACHE["v"]
    apps = q(f"""SELECT r.code, r.description, r.make, r.vehicle, r.application_text, r.year_from, r.year_to, r.status, r.supplier, r.extra FROM rd_projects r
                 WHERE r.suggestion=? AND {rules.desc_sql('r.description')}
                   AND upper(r.code) LIKE 'AMD%'
                   AND upper(r.code) NOT IN (SELECT upper(code) FROM rd_projects GROUP BY upper(code) HAVING MAX(upper(coalesce(status,''))='ITEM RECEBIDO')=1 OR MAX(upper(coalesce(status,'')) LIKE 'CANCEL%')=1)
                 ORDER BY r.code""", (kinds.DES,))
    idx = _fraga_index()
    cofap = {}
    if _has("fraga_pecas"):
        for r in q("SELECT cofap, frota FROM fraga_pecas WHERE cofap IS NOT NULL AND frota > 0"):
            for c in re.split(r"[;,/ ]+", r["cofap"]):
                if _k(c): cofap[_k(c)] = cofap.get(_k(c), 0) + (r["frota"] or 0)
    refs = {}
    if cc.available():
        for r in q("SELECT code, competitor, reference, is_oem FROM concorrentes"): refs.setdefault(r["code"], []).append(r)
    by = {}
    for a in apps:
        code = a["code"].upper()
        g = by.setdefault(code, {"codigo": code, "descricao": a["description"], "status": a["status"], "fornecedor": a["supplier"], "aplicacoes": [], "_hits": {}, "_frota_srv": 0})
        g["aplicacoes"].append(" ".join(str(x) for x in (a["make"], a["vehicle"], (f"{a['year_from'] or '…'}–{a['year_to'] or '…'}" if a["year_from"] or a["year_to"] else "")) if x))
        for h in _match(idx, a["make"], a["vehicle"], _ano(a["year_from"]), _ano(a["year_to"])): g["_hits"][h[0]] = h
        try: g["_frota_srv"] = max(g["_frota_srv"], float(json.loads(a["extra"] or "{}").get("FROTA") or 0))
        except (ValueError, TypeError): pass
    out = []
    for g in by.values():
        hits = list(g.pop("_hits").values()); fs = g.pop("_frota_srv")
        rr = refs.get(g["codigo"], [])
        g["concorrentes"] = [f"{r['competitor']} {r['reference']}" for r in rr if not r["is_oem"]][:12]
        if hits:
            g["frota"], g["origem"] = sum(h[4] for h in hits), "Fraga · veículos"
            top = sorted(hits, key=lambda h: -h[4])[:6]; g["veiculos"] = [{"nome": h[6], "frota": h[4]} for h in top]
            g["lancamento"] = any((h[5] or 0) >= LANC_DESDE for h in hits)
        else:
            cof = sum(cofap.get(_k(r["reference"]), 0) for r in rr if r["competitor"] == "COFAP")
            g["frota"], g["origem"] = (cof, "Fraga · COFAP") if cof else ((fs, "Servidor (FROTA)") if fs else (0, "sem dado"))
            g["veiculos"] = []; g["lancamento"] = False
        g["aplicacoes"] = list(dict.fromkeys(x for x in g["aplicacoes"] if x))
        out.append(g)
    vals = sorted((g for g in out if g["frota"] > 0), key=lambda g: -g["frota"]); tot = sum(g["frota"] for g in vals) or 1; acc = 0
    for g in vals: g["curva"] = "A" if acc / tot < .80 else "B" if acc / tot < .95 else "C"; acc += g["frota"]
    for g in out: g.setdefault("curva", "sem")
    out.sort(key=lambda g: (-g["frota"], g["codigo"]))
    _CACHE.update(k=key, v=out)
    return out

def _has(t):
    try: q(f"SELECT 1 FROM {t} LIMIT 1"); return True
    except Exception: return False

# ---------------- COFAP (etapa 18 · Q5–Q9) ----------------
_CCACHE = {}
SIT_COFAP = {"catalogo": "Temos · catálogo", "des": "Em desenvolvimento", "nao": "Não temos"}
def _montadora(code): return not str(code or "").upper().startswith("AMD")       # BPROAUTO (1BP…), MOTRIO (só números), MOTORCRAFT (PN Ford): nunca conta como «temos»

def _cofap_rows():
    """Um registro por código COFAP da planilha «COFAP × frota» (sem Motos): situação pelo NOSSO cross (Q7), frota da planilha (veículo × ano uma vez),
    principais veículos e — para «Não temos» — curva A/B/C pela frota (80/95%)."""
    if not _has("fraga_pecas"): return [], False
    key = (datetime.date.today().isoformat(), (q1("SELECT COUNT(*) n, MAX(rowid) m FROM fraga_pecas") or {}).get("m"), (q1("SELECT MAX(id) i FROM ds_runs") or {}).get("i"),
           (q1("SELECT COUNT(*) n FROM products WHERE catalog_position IS NOT NULL") or {}).get("n"), (q1("SELECT MAX(id) i FROM import_batches") or {}).get("i"),
           tuple(sorted((k, tuple(v["codigos"])) for k, v in correcoes_map().items() if k[0] == "COFAP")))
    if _CCACHE.get("k") == key: return _CCACHE["v"]
    cols = {r["name"] for r in q("PRAGMA table_info(fraga_pecas)")}
    tem_classe = "classificacao" in cols and bool(q("SELECT 1 FROM fraga_pecas WHERE classificacao IS NOT NULL LIMIT 1"))
    sel = "classificacao, modelo" if "classificacao" in cols else "NULL classificacao, NULL modelo"
    por, partes = {}, {}
    for r in q(f"SELECT codigo_fraga, ano_venda, marca, veiculo, frota, cofap, {sel} FROM fraga_pecas WHERE cofap IS NOT NULL AND coalesce(classificacao,'') <> 'Motos'" if "classificacao" in cols
               else f"SELECT codigo_fraga, ano_venda, marca, veiculo, frota, cofap, {sel} FROM fraga_pecas WHERE cofap IS NOT NULL"):
        ps = partes.get(r["cofap"])
        if ps is None: ps = partes[r["cofap"]] = [(_k(x), x.strip().upper()) for x in re.split(r"[;,/]+", r["cofap"]) if _k(x)]     # poucas combinações distintas: separa uma vez
        for k, raw in ps:
            g = por.setdefault(k, {"cofap": raw, "_vy": set(), "frota": 0.0, "_veic": {}, "classes": set()})
            vy = (r["codigo_fraga"], r["ano_venda"])
            if vy in g["_vy"]: continue
            g["_vy"].add(vy); g["frota"] += r["frota"] or 0
            if r["classificacao"]: g["classes"].add(r["classificacao"])
            nome = " ".join(x for x in (r["marca"], r["veiculo"]) if x) or "—"
            v = g["_veic"].setdefault(nome, {"nome": nome, "frota": 0.0, "de": None, "ate": None})
            v["frota"] += r["frota"] or 0; a = r["ano_venda"]
            if a: v["de"] = min(v["de"] or a, a); v["ate"] = max(v["ate"] or a, a)
    # nosso cross: catálogo (CrossCatalogo; servidor quando a planilha não tem o item) e DES/R-D AMD fora do catálogo e não cancelados (servidor)
    cat = {}
    for r in _catalogo_rows():
        if r["concorrente"] == "COFAP" and not _montadora(r["codigo"]): cat.setdefault(_k(r["referencia"]), set()).add(r["codigo"])
    des = {}
    if _has("concorrentes"):
        no_catalogo = {x["c"] for x in q("SELECT upper(perfect_code) c FROM products WHERE catalog_position IS NOT NULL")}
        cancel = {x["c"] for x in q("SELECT upper(code) c FROM rd_projects GROUP BY upper(code) HAVING MAX(upper(coalesce(status,'')) LIKE 'CANCEL%')=1")}
        for r in q("SELECT upper(code) code, reference FROM concorrentes WHERE competitor='COFAP' AND is_oem=0"):
            c = r["code"]
            if not _montadora(c) and c not in no_catalogo and c not in cancel: des.setdefault(_k(r["reference"]), set()).add(c)
        for (comp, rk), cr in correcoes_map().items():          # correção feita na tela: o conjunto corrigido substitui o do servidor (catálogo já veio corrigido)
            if comp != "COFAP": continue
            des[rk] = {c for c in cr["codigos"] if not _montadora(c) and c not in no_catalogo and c not in cancel}
            if not des[rk]: des.pop(rk)
    out = []
    for k, g in por.items():
        vs = sorted(g.pop("_veic").values(), key=lambda v: -v["frota"]); g.pop("_vy")
        sit = "catalogo" if k in cat else "des" if k in des else "nao"
        out.append({**g, "situacao": sit, "nossos": sorted(cat.get(k) or des.get(k) or []), "classes": sorted(g["classes"]), "n_veiculos": len(vs),
                    "veiculos": [{"nome": v["nome"], "anos": (f"{v['de']}–{v['ate']}" if v["de"] != v["ate"] else str(v["de"])) if v["de"] else "", "frota": v["frota"]} for v in vs[:5]]})
    nao = sorted((r for r in out if r["situacao"] == "nao" and r["frota"] > 0), key=lambda r: -r["frota"]); tot = sum(r["frota"] for r in nao) or 1; acc = 0
    for r in nao: r["curva"] = "A" if acc / tot < .80 else "B" if acc / tot < .95 else "C"; acc += r["frota"]
    for r in out: r.setdefault("curva", "sem" if r["situacao"] == "nao" else "")
    out.sort(key=lambda r: (-r["frota"], r["cofap"]))
    _CCACHE.update(k=key, v=(out, tem_classe))
    return out, tem_classe

COF_F = ("situacao", "classif", "curva")
def cofap(f=None, page=1, size=200):
    """Aba COFAP: códigos da planilha COFAP × frota (sem Motos) — temos (catálogo), em desenvolvimento ou não temos. Atalhos de situação, classificação e curva
    (só «Não temos»): cada contagem = lista ao clicar."""
    f = f or {}; rows, tem_classe = _cofap_rows(); term = (f.get("q") or "").upper().split()
    def ok(r, skip=""):
        if skip != "situacao" and f.get("situacao") and r["situacao"] != f["situacao"]: return False
        if skip != "classif" and f.get("classif") and f["classif"] not in r["classes"]: return False
        if skip != "curva" and f.get("curva") and r["curva"] != f["curva"]: return False
        return all(t in f"{r['cofap']} {' '.join(r['nossos'])} {' '.join(v['nome'] for v in r['veiculos'])}".upper() for t in term)
    sel = [r for r in rows if ok(r)]
    cnt = lambda key, fn: dict(Counter(x for r in rows if ok(r, key) for x in fn(r)).most_common())
    counts = {"situacao": cnt("situacao", lambda r: [r["situacao"]]), "classif": cnt("classif", lambda r: r["classes"]), "curva": cnt("curva", lambda r: [r["curva"]] if r["situacao"] == "nao" else [])}
    by = lambda s, rr: [r for r in rr if r["situacao"] == s]
    page = max(int(page or 1), 1); n = 10**9 if f.get("all") else size
    return {"total": len(sel), "rows": sel[(page - 1) * n: page * n], "page": page, "size": n, "counts": counts, "disponivel": bool(rows), "sem_classificacao": bool(rows) and not tem_classe,
            "kpis": {"codigos": len(sel), "catalogo": len(by("catalogo", sel)), "des": len(by("des", sel)), "nao": len(by("nao", sel)),
                     "frota": sum(r["frota"] for r in sel), "frota_nao": sum(r["frota"] for r in by("nao", sel)), "frota_temos": sum(r["frota"] for r in sel if r["situacao"] != "nao")}}

DES_F = ("curva", "origem", "lancamento")
def desenvolvimento(f=None, page=1, size=200):
    f = f or {}; rows = _des_rows(); term = (f.get("q") or "").upper().split()
    def ok(r, skip=""):
        if skip != "curva" and f.get("curva") and r["curva"] != f["curva"]: return False
        if skip != "origem" and f.get("origem") and r["origem"] != f["origem"]: return False
        if skip != "lancamento" and f.get("lancamento") and not r["lancamento"]: return False
        return all(t in f"{r['codigo']} {r['descricao'] or ''} {' '.join(r['aplicacoes'])} {' '.join(r['concorrentes'])} {r['fornecedor'] or ''}".upper() for t in term)
    sel = [r for r in rows if ok(r)]
    counts = {"curva": dict(Counter(r["curva"] for r in rows if ok(r, "curva")).most_common()), "origem": dict(Counter(r["origem"] for r in rows if ok(r, "origem")).most_common()),
              "lancamento": sum(1 for r in rows if r["lancamento"] and ok(r, "lancamento"))}
    page = max(int(page or 1), 1); n = 10**9 if f.get("all") else size
    return {"total": len(sel), "rows": sel[(page - 1) * n: page * n], "page": page, "size": n, "counts": counts,
            "kpis": {"itens": len(sel), "com_frota": sum(1 for r in sel if r["frota"] > 0), "frota": sum(r["frota"] for r in sel), "ano": datetime.date.today().year,
                     "fraga": _has("fraga_veiculos") and bool(q("SELECT 1 FROM fraga_veiculos LIMIT 1"))}}
