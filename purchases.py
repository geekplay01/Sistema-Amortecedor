"""Compra de amostras x Desenvolvimento: tudo que está 'Pendente compras' (planilha ou marcação manual) aparece aqui, com a referência cruzada do item
(o que cotar/comprar) e a situação dos pedidos de amostra já abertos para o mesmo código."""
import re
import database as db
from queries import q, q1, cross_for
import rd, rules

DONE = {"chegou", "finalizado", "aprovado"}
BRAND_ORDER = ["MONROE", "KAYABA", "COFAP", "NAKATA", "SACHS", "CORVEN", "TRW", "TRW AMD", "ISAPA", "ALBARUS", "DEVIGILI", "RECORD", "CILBRAKE", "GLOBO", "FRIC ROT", "JINBO AUTOPART", "PERFECT", "OEM"]
STAGE = {"cotacao": "Cotação", "sc_aberta": "SC aberta", "chegou": "Chegou", "finalizado": "Finalizado", "aprovado": "Aprovado"}
def _k(c): return re.sub(r"[^A-Z0-9]", "", (c or "").upper())

def _orders():
    out = {}
    for o in q("SELECT id,perfect_code,sample_code,sc_number,supplier,stage FROM sample_orders"):
        for c in (o["perfect_code"], o["sample_code"]):
            if c: out.setdefault(_k(c), []).append(o)
    return out

def state_of(orders):
    if not orders: return "sem"
    if any(o["stage"] in DONE for o in orders): return "comprada"
    return "andamento" if any(o["stage"] not in ("cotacao", None, "") for o in orders) else "cotacao"

RD_BRANDS = ("COFAP", "MONROE", "NAKATA", "CORVEN", "KAYABA", "OEM")
def rd_cross_index():
    """Referência cruzada dos itens de Desenvolvimento (colunas COFAP, MONROE, NAKATA, CORVEN, KAYABA e OEM da planilha). {código: [{brand, code}]}"""
    import json
    out = {}
    for r in q("SELECT code,extra FROM rd_projects WHERE extra IS NOT NULL"):
        try: d = json.loads(r["extra"])
        except ValueError: continue
        lst = out.setdefault(r["code"], [])
        for b in RD_BRANDS:
            for c in re.split(r"[/;,\n]+", str(d.get(b) or "")):
                c = c.strip()
                if c and c != r["code"] and not any(x["brand"] == b and x["code"] == c for x in lst): lst.append({"brand": b, "code": c})
    return {k: v for k, v in out.items() if v}

def _sort_cross(cs):
    rank = {b: i for i, b in enumerate(BRAND_ORDER)}
    return sorted(cs, key=lambda c: (rank.get(c["brand"], 50), c["brand"] or "", c["code"]))

def pending(f):
    """Sugestões de compra de amostra: itens (Amortecedor) em DESENVOLVIMENTO/REDESENVOLVIMENTO marcados «PENDENTE COMPRAS», que NÃO estão no catálogo, cujo status é DIFERENTE
    de ITEM RECEBIDO e para os quais AINDA NÃO compramos amostra (sem data de amostra comprada/enviada e sem pedido de amostra além da cotação)."""
    kind = {"des": "DESENVOLVIMENTO", "rd": "REDESENVOLVIMENTO"}.get(f.get("kind") or "")
    # SÓ o que está em desenvolvimento/redesenvolvimento com «PENDENTE COMPRAS»; ITEM RECEBIDO e itens que já estão no catálogo não são listados
    w, p = [rules.desc_sql("r.description"), "coalesce(v.pend_compras,0)=1",
            "NOT EXISTS (SELECT 1 FROM products pp WHERE pp.catalog_position IS NOT NULL AND (pp.id=r.product_id OR upper(pp.perfect_code)=upper(r.code)))"], {}
    if kind: w.append("r.suggestion=:k"); p["k"] = kind
    for i, t in enumerate((f.get("q") or "").split()):
        w.append(f"(r.code LIKE :t{i} OR r.description LIKE :t{i} OR r.make LIKE :t{i} OR r.vehicle LIKE :t{i})"); p[f"t{i}"] = f"%{t}%"
    rows = q(f"""SELECT r.code,r.suggestion,MAX(r.description) description,MAX(r.product_id) product_id,group_concat(DISTINCT r.make) makes,group_concat(DISTINCT r.vehicle) vehicles,
        group_concat(DISTINCT r.status) statuses,group_concat(DISTINCT r.supplier) suppliers,MAX(coalesce(v.pend_compras,0)) pend_compras
        FROM rd_projects r LEFT JOIN v_rd_flags v ON v.code=r.code AND v.suggestion=r.suggestion WHERE {" AND ".join(w)} GROUP BY r.code,r.suggestion
        HAVING SUM(coalesce(r.status,'')='ITEM RECEBIDO')=0 AND MAX(r.sample_bought) IS NULL AND MAX(r.sample_sent) IS NULL ORDER BY r.code""", p)
    od = _orders(); out = []
    has_cross = {r["product_id"] for r in q("SELECT DISTINCT k.product_id FROM codes k JOIN sources s ON s.id=k.source_id WHERE s.name LIKE 'CrossCatalogo%'")}; rdx = rd_cross_index()
    for r in rows:
        ors = od.get(_k(r["code"]), []); st = state_of(ors)
        if st in ("andamento", "comprada"): continue                 # já tem compra em andamento ou concluída: não sugere
        r.update(state=st, orders=[{"id": o["id"], "sc": o["sc_number"], "sample_code": o["sample_code"], "supplier": o["supplier"], "stage": STAGE.get(o["stage"], o["stage"])} for o in ors],
                 makes=(r["makes"] or "").replace(",", " · "), vehicles=(r["vehicles"] or "").replace(",", " · "), statuses=(r["statuses"] or "").replace(",", " · "), suppliers=(r["suppliers"] or "").replace(",", " · "))
        out.append(r)
    out.sort(key=lambda r: (0 if (r["product_id"] in has_cross or r["code"] in rdx) else 1, -(r["pend_compras"] or 0), r["code"]))   # o que dá para cotar já (tem referência cruzada) vem primeiro
    summ = {"total": len(out), "sem": len(out), "com_referencia": sum(1 for r in out if r["product_id"] in has_cross or r["code"] in rdx), "pend_compras": sum(1 for r in out if r["pend_compras"])}
    size = 40; page = max(1, int(f.get("page") or 1)); chunk = out[(page - 1) * size: page * size]
    for r in chunk:   # referência cruzada só do que vai aparecer na página
        cs = [{"brand": c["brand"], "code": c["code"]} for c in cross_for(r["product_id"])] if r["product_id"] else []
        r["cross"] = _sort_cross(cs or rdx.get(r["code"], []))
    return {"total": len(out), "page": page, "size": size, "rows": chunk, "summary": summ}

def for_code(code):
    """Usado no formulário do pedido: o código está pendente de compra? quais referências cotar?"""
    k = _k(code); fl = []
    for r in q("SELECT suggestion,pend_compras FROM v_rd_flags WHERE pend_compras=1 AND replace(replace(upper(code),'/',''),' ','')=?", (k,)): fl.append(r["suggestion"])
    p = q1("SELECT id FROM products WHERE upper(perfect_code)=?", (k,)) or (q1("SELECT product_id id FROM rd_projects WHERE replace(replace(upper(code),'/',''),' ','')=? AND product_id IS NOT NULL LIMIT 1", (k,)))
    cross = [{"brand": c["brand"], "code": c["code"]} for c in cross_for(p["id"])] if p and p.get("id") else []
    if not cross:
        for code_, lst in rd_cross_index().items():
            if _k(code_) == k: cross = lst; break
    cross = _sort_cross(cross)
    ors = _orders().get(k, [])
    return {"pending": fl, "cross": cross, "state": state_of(ors), "orders": len(ors)}
