"""Módulo Brands: BPROAUTO, MOTRIO, PERFECT e MOTORCRAFT.
Regra pelo código do item:  1BP… → BPROAUTO · AMD… → PERFECT · está na base ItensMotorcraft (PN Ford, e mesma família de prefixo) → MOTORCRAFT · só números → MOTRIO."""
import re
import database as db
import rules
from queries import q, q1

BRANDS = ["PERFECT", "BPROAUTO", "MOTRIO", "MOTORCRAFT"]
RULE = {"PERFECT": "Códigos AMD…", "BPROAUTO": "Códigos 1BP…", "MOTRIO": "Códigos somente numéricos", "MOTORCRAFT": "Base ItensMotorcraft (PN Ford)"}
def _k(c): return re.sub(r"[^A-Z0-9]", "", (c or "").upper())
_FORD = re.compile(r"^[A-Z0-9]{2,5}/18[A-Z0-9]{3,4}/[A-Z]{1,3}\d?(/\d*)?$")       # PN Ford de amortecedor: prefixo / base 18xxx / sufixo (ex.: BJ3A/18045/AA/, ENS1/18097/AC, MB5A/18K001/AA/)
def is_ford(code): return bool(_FORD.match(re.sub(r"\s", "", (code or "").upper())))

def _motor():
    norms = {r["norm_code"] for r in q("SELECT norm_code FROM brand_items WHERE brand='MOTORCRAFT'")}
    return norms, {n[:3] for n in norms}

def classify(code, motor=None):
    n = _k(code); norms, pref = motor or _motor()
    if n.startswith("1BP"): return "BPROAUTO"
    if n.startswith("AMD"): return "PERFECT"
    if n in norms: return "MOTORCRAFT"
    if n.isdigit(): return "MOTRIO"
    if n[:3] in pref: return "MOTORCRAFT"   # mesma família de código Ford da base (ex.: BJ3…, MB5…)
    return None

def _perfect_index():
    """código normalizado (de qualquer marca) → {códigos PERFECT relacionados}, a partir da base: referência cruzada (codes), base de marcas,
    itens de Desenvolvimento ligados ao catálogo e pedidos de amostra."""
    idx = {}
    def add(code, perfect):
        k = _k(code); p = (perfect or "").strip().upper()
        if k and p and k != _k(p): idx.setdefault(k, set()).add(p)
    for r in q("SELECT k.code, k.normalized_code n, p.perfect_code pc FROM codes k JOIN products p ON p.id=k.product_id"):
        add(r["code"], r["pc"]); add(r["n"], r["pc"])
    for r in q("SELECT code, perfect_code FROM brand_items WHERE perfect_code IS NOT NULL"): add(r["code"], r["perfect_code"])
    for r in q("SELECT s.sample_code c, s.perfect_code pc FROM sample_orders s WHERE s.sample_code IS NOT NULL AND s.perfect_code IS NOT NULL"): add(r["c"], r["pc"])
    return idx

# ---------------- vínculo manual com o item PERFECT relativo (etapa 22, como o «Nosso código» da Cobertura) ----------------
LINK_TABLE = """CREATE TABLE IF NOT EXISTS brand_links(key TEXT PRIMARY KEY, code TEXT, codigos TEXT, antes TEXT, por TEXT, em TEXT DEFAULT CURRENT_TIMESTAMP)"""
def _link_ensure():
    c = db.conn()
    try: c.execute(LINK_TABLE); c.commit()
    finally: c.close()
def vinculos_map():
    """{código normalizado: {code, codigos: [...], antes: [...], por, em}} — o conjunto de códigos PERFECT do item (vazio = sem relação)."""
    try: rows = q("SELECT * FROM brand_links")
    except Exception: return {}
    sp = lambda t: [x for x in (t or "").split(",") if x]
    return {r["key"]: {**r, "codigos": sp(r["codigos"]), "antes": sp(r["antes"])} for r in rows}

def vincular(code, codigos, por=None):
    """Grava o conjunto completo de códigos PERFECT relativos de um item de outra marca. Vale sobre a base (cross, base de marcas, amostras).
    → {"anterior": vínculo que existia (ou None), "codigos": novo conjunto} — «anterior» serve para o «Desfazer»."""
    import cobertura
    k = _k(code)
    if not k: raise ValueError("Informe o código.")
    if k.startswith("AMD"): raise ValueError(f"{k} já é um código PERFECT.")
    it = next((i for i in universe() if i["key"] == k), None)
    if it is None: raise ValueError(f"{k} não está em Brands.")
    novo = sorted({cobertura._k(c) for c in (codigos or []) if cobertura._k(c)})
    for c in novo:
        err = cobertura._valido(c)
        if err: raise ValueError(err)
    _link_ensure(); ant = vinculos_map().get(k)
    c = db.conn()
    try:
        c.execute("""INSERT INTO brand_links(key, code, codigos, antes, por) VALUES(?,?,?,?,?)
                     ON CONFLICT(key) DO UPDATE SET codigos=excluded.codigos, code=excluded.code, por=excluded.por, em=CURRENT_TIMESTAMP""",
                  (k, it["code"], ",".join(novo), ",".join(ant["antes"] if ant else it["perfect_codes"]), por)); c.commit()
    finally: c.close()
    return {"anterior": ({x: ant[x] for x in ("codigos", "antes", "por")} if ant else None), "codigos": novo}

def desvincular(code, anterior=None):
    """Volta ao que era antes do último vínculo: sem vínculo anterior apaga a linha (vale de novo a base)."""
    _link_ensure(); k = _k(code); c = db.conn()
    try:
        if anterior: c.execute("UPDATE brand_links SET codigos=?, antes=?, em=CURRENT_TIMESTAMP WHERE key=?", (",".join(anterior.get("codigos") or []), ",".join(anterior.get("antes") or []), k))
        else: c.execute("DELETE FROM brand_links WHERE key=?", (k,))
        c.commit()
    finally: c.close()

def universe():
    """Todos os itens conhecidos (catálogo, DES, R-D, base Motorcraft, pedidos de amostra), 1 por código."""
    motor = _motor(); items = {}
    def get(code):
        k = _k(code)
        if not k: return None
        it = items.get(k)
        if it is None: it = items[k] = {"perfect_codes": [], "key": k, "code": code, "brand": classify(code, motor), "description": None, "catalog": False, "des": False, "rd": False, "base": False, "samples": 0, "vehicle": None, "product_id": None, "flags": []}
        return it
    for p in q("SELECT id,perfect_code,description FROM products"):
        it = get(p["perfect_code"]); it["catalog"] = True; it["product_id"] = p["id"]; it["description"] = it["description"] or p["description"]
    for r in q("SELECT code,suggestion,MAX(description) d,MAX(product_id) pid,group_concat(DISTINCT make) mk,group_concat(DISTINCT vehicle) vh FROM rd_projects WHERE " + rules.desc_sql() + " GROUP BY code,suggestion"):
        it = get(r["code"]); it["des" if r["suggestion"] == "DESENVOLVIMENTO" else "rd"] = True
        it["description"] = it["description"] or r["d"]; it["product_id"] = it["product_id"] or r["pid"]
        it["vehicle"] = it["vehicle"] or " · ".join(x for x in ((r["mk"] or "").replace(",", "/"), (r["vh"] or "").replace(",", " · ")) if x) or None
    for b in q("SELECT brand,code,perfect_code,description,vehicle,application,years FROM brand_items WHERE brand IN ('MOTORCRAFT','BPROAUTO','MOTRIO')"):
        it = get(b["code"]); it["base"] = True; it["brand"] = it["brand"] or b["brand"]; it["description"] = it["description"] or b["description"]
        it["vehicle"] = it["vehicle"] or " · ".join(x for x in (b["vehicle"], b["application"], b["years"]) if x) or None; it["perfect_code"] = b["perfect_code"]
    for s in q("SELECT perfect_code,COUNT(*) n FROM sample_orders WHERE perfect_code IS NOT NULL GROUP BY perfect_code"):
        it = get(s["perfect_code"]); it["samples"] += s["n"]
    pidx = _perfect_index(); pc_of_pid = {r["id"]: r["perfect_code"] for r in q("SELECT id,perfect_code FROM products")}; man = vinculos_map()
    for k, it in items.items():
        found = set(pidx.get(k, ()))
        if it["product_id"] and pc_of_pid.get(it["product_id"]) and _k(pc_of_pid[it["product_id"]]) != k: found.add(pc_of_pid[it["product_id"]].upper())
        if it.get("perfect_code"): found.add(str(it["perfect_code"]).upper())
        if it["brand"] == "PERFECT": found.discard(it["code"].upper())
        it["perfect_codes"] = sorted(found); it["vinculo_manual"] = k in man
        if k in man: it["perfect_codes_base"] = it["perfect_codes"]; it["perfect_codes"] = man[k]["codigos"]      # etapa 22: o vínculo feito na tela vale sobre a base
    fl = {}
    for v in q("SELECT code,suggestion,pend_validacao,val_reprovada,pend_desenho_forn,pend_compras FROM v_rd_flags"):
        fl.setdefault(_k(v["code"]), set()).update(k for k in ("pend_validacao", "val_reprovada", "pend_desenho_forn", "pend_compras") if v[k])
    for k, it in items.items():
        it["flags"] = sorted(fl.get(k, ()))
        it["fora_base"] = not it["brand"] and is_ford(it["code"])          # PN Ford fora da base ItensMotorcraft (etapa 16 · D7): entra na lista MOTORCRAFT, sem contar no indicador
        if it["fora_base"]: it["brand"] = "MOTORCRAFT"
    return list(items.values())

def summary():
    """Indicador por marca: `total` não conta os PN Ford fora da base (`fora_base`, só na lista); `total` geral = todos os itens conhecidos."""
    its = universe(); out = []
    for b in BRANDS:
        xs = [i for i in its if i["brand"] == b and not i["fora_base"]]
        out.append({"brand": b, "rule": RULE[b], "total": len(xs), "catalog": sum(i["catalog"] for i in xs), "des": sum(i["des"] for i in xs), "rd": sum(i["rd"] for i in xs), "base": sum(i["base"] for i in xs),
                    "pend_compras": sum("pend_compras" in i["flags"] for i in xs), "val_reprovada": sum("val_reprovada" in i["flags"] for i in xs), "fora_base": sum(1 for i in its if i["brand"] == b and i["fora_base"])})
    return {"brands": out, "unclassified": sum(1 for i in its if not i["brand"]), "total": len(its), "fora_base": sum(1 for i in its if i["fora_base"])}

SCOPES = ("catalog", "des", "rd", "base")
FLAGS = ("pend_validacao", "val_reprovada", "pend_desenho_forn", "pend_compras")      # os controles que universe() junta por código
def _marca(i): return i["brand"] or "OUTROS"

def items(brand, f):
    """Itens da marca (OUTROS = sem marca) com busca, «onde está» (scope) e controle (flag).
    counts: atalhos da tela — marca, scope e flag; cada grupo ignora o próprio filtro e respeita os outros, então o número = total da lista ao clicar (test_24)."""
    uni = universe(); mine = [i for i in uni if _marca(i) == brand]
    term = (f.get("q") or "").upper().split(); sc = f.get("scope"); fl = f.get("flag")
    def ok(i, skip=""):
        txt = f"{i['code']} {i['description'] or ''} {i['vehicle'] or ''} {' '.join(i.get('perfect_codes') or [])}".upper()
        if any(t not in txt for t in term): return False
        if skip != "scope" and sc in SCOPES and not i[sc]: return False
        if skip != "flag" and fl and fl not in i["flags"]: return False
        return True
    counts = {"brand": {b: sum(1 for i in uni if _marca(i) == b and not i["fora_base"] and ok(i)) for b in BRANDS + ["OUTROS"]},      # cartão: sem os PN Ford fora da base
              "scope": {"all": sum(1 for i in mine if ok(i, "scope")), **{s: sum(1 for i in mine if i[s] and ok(i, "scope")) for s in SCOPES}},
              "flag": {k: sum(1 for i in mine if k in i["flags"] and ok(i, "flag")) for k in FLAGS}}
    its = sorted((i for i in mine if ok(i)), key=lambda i: i["code"])
    size = 50 if not f.get("all") else 10**9; page = max(1, int(f.get("page") or 1))
    return {"total": len(its), "page": page, "size": size, "rows": its[(page - 1) * size: page * size], "counts": counts, "fora_base": sum(1 for i in its if i["fora_base"])}
