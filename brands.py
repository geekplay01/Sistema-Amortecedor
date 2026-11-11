"""Módulo Brands: BPROAUTO, MOTRIO, PERFECT e MOTORCRAFT.
Regra pelo código do item:  1BP… → BPROAUTO · AMD… → PERFECT · está na base ItensMotorcraft (PN Ford, e mesma família de prefixo) → MOTORCRAFT · só números → MOTRIO."""
import re
import database as db
import rules
from queries import q, q1

BRANDS = ["PERFECT", "BPROAUTO", "MOTRIO", "MOTORCRAFT"]
RULE = {"PERFECT": "Códigos AMD…", "BPROAUTO": "Códigos 1BP…", "MOTRIO": "Códigos somente numéricos", "MOTORCRAFT": "Base ItensMotorcraft (PN Ford)"}
def _k(c): return re.sub(r"[^A-Z0-9]", "", (c or "").upper())

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
    pidx = _perfect_index(); pc_of_pid = {r["id"]: r["perfect_code"] for r in q("SELECT id,perfect_code FROM products")}
    for k, it in items.items():
        found = set(pidx.get(k, ()))
        if it["product_id"] and pc_of_pid.get(it["product_id"]) and _k(pc_of_pid[it["product_id"]]) != k: found.add(pc_of_pid[it["product_id"]].upper())
        if it.get("perfect_code"): found.add(str(it["perfect_code"]).upper())
        if it["brand"] == "PERFECT": found.discard(it["code"].upper())
        it["perfect_codes"] = sorted(found)
    fl = {}
    for v in q("SELECT code,suggestion,pend_validacao,val_reprovada,pend_desenho_forn,pend_compras FROM v_rd_flags"):
        fl.setdefault(_k(v["code"]), set()).update(k for k in ("pend_validacao", "val_reprovada", "pend_desenho_forn", "pend_compras") if v[k])
    for k, it in items.items(): it["flags"] = sorted(fl.get(k, ()))
    return list(items.values())

def summary():
    its = universe(); out = []
    for b in BRANDS:
        xs = [i for i in its if i["brand"] == b]
        out.append({"brand": b, "rule": RULE[b], "total": len(xs), "catalog": sum(i["catalog"] for i in xs), "des": sum(i["des"] for i in xs), "rd": sum(i["rd"] for i in xs), "base": sum(i["base"] for i in xs),
                    "pend_compras": sum("pend_compras" in i["flags"] for i in xs), "val_reprovada": sum("val_reprovada" in i["flags"] for i in xs)})
    return {"brands": out, "unclassified": sum(1 for i in its if not i["brand"]), "total": len(its)}

def items(brand, f):
    its = [i for i in universe() if (i["brand"] == brand if brand != "OUTROS" else not i["brand"])]
    term = (f.get("q") or "").upper().split(); sc = f.get("scope")
    def ok(i):
        txt = f"{i['code']} {i['description'] or ''} {i['vehicle'] or ''} {' '.join(i.get('perfect_codes') or [])}".upper()
        if any(t not in txt for t in term): return False
        if sc in ("catalog", "des", "rd", "base") and not i[sc]: return False
        if f.get("flag") and f["flag"] not in i["flags"]: return False
        return True
    its = sorted((i for i in its if ok(i)), key=lambda i: i["code"])
    size = 50 if not f.get("all") else 10**9; page = max(1, int(f.get("page") or 1))
    return {"total": len(its), "page": page, "size": size, "rows": its[(page - 1) * size: page * size]}
