"""Compra de amostras x Desenvolvimento: tudo que está 'Pendente compras' (planilha ou marcação manual) aparece aqui, com a referência cruzada do item
(o que cotar/comprar) e a situação dos pedidos de amostra já abertos para o mesmo código."""
import re
import database as db
from queries import q, q1, cross_for
import rd, rules, kinds

DONE = {"chegou", "finalizado", "aprovado"}
BRAND_ORDER = ["MONROE", "KAYABA", "COFAP", "NAKATA", "SACHS", "CORVEN", "TRW", "TRW AMD", "ISAPA", "ALBARUS", "DEVIGILI", "RECORD", "CILBRAKE", "GLOBO", "FRIC ROT", "JINBO AUTOPART", "PERFECT", "OEM"]
STAGE = {"cotacao": "Cotação", "sc_aberta": "SC aberta", "chegou": "Chegou", "finalizado": "Finalizado", "aprovado": "Aprovado"}
def _k(c): return re.sub(r"[^A-Z0-9]", "", (c or "").upper())
def _base(c): return re.sub(r"^(MP-|D-)", "", re.sub(r"[/\s]", "", (c or "").strip().upper()))

# Etapa 18 · Q11: compra de amostra só para código PERFECT (AMD…). Itens de montadora — BPROAUTO (1BP…), MOTRIO (só números) e
# MOTORCRAFT (PN Ford) — não são sugeridos nem aceitos no pedido. Etapa 19 · Q3: o pedido MANUAL aceita também item já desenvolvido (no catálogo).
def is_perfect(code): return _base(code).startswith("AMD")
def code_problem(code):
    """None se o código pode ter pedido de amostra; senão o motivo (mostrado no formulário e devolvido pela API)."""
    c = _base(code)
    if not c: return "Informe o código PERFECT do item."
    if not c.startswith("AMD"): return f"{c} não é código PERFECT (AMD…). Itens de montadora (BPROAUTO, MOTRIO, MOTORCRAFT) não têm pedido de amostra."
    if not (q1("SELECT 1 FROM rd_projects WHERE upper(code)=? LIMIT 1", (c,)) or q1("SELECT 1 FROM products WHERE upper(perfect_code)=? LIMIT 1", (c,))):
        return f"{c} não está em Desenvolvimento, Redesenvolvimento nem no catálogo."
    return None

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
    """Referência cruzada dos itens de Desenvolvimento. {código: [{brand, code}]}
    Etapa 17 · Q10: vem do servidor (DESENVOLVIMENTO_CONCORRENTES, ligado pelo ID — concorrentes.py), com OEM como marca «OEM». Sem essa tabela
    sincronizada, vale o jeito antigo: colunas COFAP, MONROE, NAKATA, CORVEN, KAYABA e OEM da planilha antiga (rd_projects.extra)."""
    import json, concorrentes
    out = {}
    if concorrentes.available():
        for r in q("SELECT code, competitor, MIN(reference) reference FROM concorrentes GROUP BY code, competitor, ref_key ORDER BY code, is_oem, competitor"):
            out.setdefault(r["code"], []).append({"brand": r["competitor"], "code": r["reference"]})
        return out
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
    # SÓ DESENVOLVIMENTO com «PENDENTE COMPRAS» (etapa 19 · Q3: Redesenvolvimento não tem sugestão de amostra; o pedido de item já desenvolvido é manual);
    # ITEM RECEBIDO e itens que já estão no catálogo não são listados
    w, p = [rules.desc_sql("r.description"), "coalesce(v.pend_compras,0)=1", "upper(r.code) LIKE 'AMD%'",     # só PERFECT (sem itens de montadora)
            "NOT EXISTS (SELECT 1 FROM products pp WHERE pp.catalog_position IS NOT NULL AND (pp.id=r.product_id OR upper(pp.perfect_code)=upper(r.code)))", "r.suggestion=:k"], {"k": kinds.DES}
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
    return {"pending": fl, "cross": cross, "state": state_of(ors), "orders": len(ors), "problem": code_problem(code)}
