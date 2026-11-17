"""Vendas × estoque — tela «Estoque» (etapa 16 · C2–C5). Um item por código (sem pontuação; o prefixo MP- dos pedidos de importação sai).
  • Venda média mensal = peças dos últimos 12 meses FECHADOS ÷ 12 (o mês atual, parcial, fica de fora). Linhas: amortecedor, linha pesada e kit — aqui vale
    a venda do próprio SKU, não o total do BI.
  • Estoque disponível = armazém 04 − reservado (os outros armazéns não contam).
  • A caminho = pedidos em aberto da previsão de chegadas (leadtime), SEM os «Parado — verificar saldo».
  • Cobertura (meses) = (estoque + a caminho) ÷ venda média.
  • Situação: ruptura (vende e o estoque disponível é 0) · risco (< meta de lead time em meses, 180 d = 6) · ok (até 18) · excesso (> 18) · sem giro (estoque sem venda em 12 meses).
  • Atalhos (situação, classe ABC): cada número = linhas da lista ao clicar (ignora o próprio filtro, respeita os outros)."""
import re, datetime
from queries import q

ARMAZEM = "04"; EXCESSO = 18
SIT = ("ruptura", "risco", "ok", "excesso", "sem_giro")
LINHAS = "amortecedor,pesada,kit"
def _k(c): return re.sub(r"[^A-Z0-9]", "", re.sub(r"^\s*MP-", "", str(c or "").upper()))

def _janela(today):
    """(primeiro dia do 12º mês fechado, primeiro dia do mês atual) — ex.: 17/11/2026 → ('2025-11-01', '2026-11-01')."""
    a = today.replace(day=1); y, m = a.year - 1, a.month
    return f"{y}-{m:02d}-01", a.isoformat()

def base(today=None):
    import curva_abc, leadtime, analytics
    today = today or datetime.date.today(); de, ate = _janela(today); ls, lp = curva_abc.linha_sql(LINHAS)
    it = {}
    def get(code):
        k = _k(code)
        return it.setdefault(k, {"codigo": k, "venda_12m": 0.0, "valor_12m": 0.0, "estoque": 0.0, "reservado": 0.0, "a_caminho": 0.0}) if k else None
    for r in q(f"SELECT code, SUM(qty) qq, SUM(total) vv FROM ds_vendas WHERE sale_date>=? AND sale_date<? AND {ls} GROUP BY code", [de, ate, *lp]):
        x = get(r["code"])
        if x: x["venda_12m"] += r["qq"] or 0; x["valor_12m"] += r["vv"] or 0
    try: est = q("SELECT code, SUM(qty) qq, SUM(reserved) rr FROM ds_estoque WHERE trim(warehouse)=? GROUP BY code", (ARMAZEM,))
    except Exception: est = []
    for r in est:
        x = get(r["code"])
        if x: x["estoque"] += r["qq"] or 0; x["reservado"] += r["rr"] or 0
    F = leadtime.forecast_cached(today) or {}
    for r in (F.get("linhas") or []) if F.get("available") else []:
        if r.get("etapa") == leadtime.PARADO: continue
        x = it.get(_k(r["codigo"]))
        if x is not None: x["a_caminho"] += float(r.get("quantidade") or 0)      # só códigos que vendem ou têm estoque (pedido de item sem venda nem estoque não entra)
    names = analytics._names()
    risco = round(leadtime.meta_dias() / 30, 1)
    vals = sorted((x for x in it.values() if x["valor_12m"] > 0), key=lambda x: -x["valor_12m"]); tot = sum(x["valor_12m"] for x in vals) or 1; acc = 0
    for x in vals:
        x["classe"] = "A" if acc / tot * 100 < 80 else "B" if acc / tot * 100 < 95 else "C"; acc += x["valor_12m"]
    out = []
    for x in it.values():
        disp = max(x["estoque"] - x["reservado"], 0); media = round(x["venda_12m"] / 12, 2)
        if media <= 0 and disp <= 0: continue
        cob = round((disp + x["a_caminho"]) / media, 1) if media > 0 else None
        sit = "sem_giro" if media <= 0 else "ruptura" if disp <= 0 else "risco" if cob < risco else "ok" if cob <= EXCESSO else "excesso"
        out.append({"codigo": x["codigo"], "descricao": names.get(x["codigo"]), "venda_12m": x["venda_12m"], "valor_12m": round(x["valor_12m"], 2), "media_mensal": media, "estoque": disp,
                    "reservado": x["reservado"], "a_caminho": x["a_caminho"], "cobertura": cob, "situacao": sit, "classe": x.get("classe") or "—"})
    return out, {"risco": risco, "excesso": EXCESSO}, {"de": de, "ate": ate}

ORDEM = {"ruptura": 0, "risco": 1, "ok": 2, "excesso": 3, "sem_giro": 4}
def listing(f, today=None, size=100):
    rows, lim, jan = base(today)
    term = (f.get("q") or "").upper().split(); sit = f.get("situacao") or ""; cl = f.get("classe") or ""
    def ok(r, skip=""):
        if any(t not in f"{r['codigo']} {r['descricao'] or ''}".upper() for t in term): return False
        if skip != "situacao" and sit and r["situacao"] != sit: return False
        if skip != "classe" and cl and r["classe"] != cl: return False
        return True
    counts = {"situacao": {s: sum(1 for r in rows if r["situacao"] == s and ok(r, "situacao")) for s in SIT}, "classe": {}}
    for r in rows:
        if ok(r, "classe"): counts["classe"][r["classe"]] = counts["classe"].get(r["classe"], 0) + 1
    sel = sorted((r for r in rows if ok(r)), key=lambda r: (ORDEM[r["situacao"]], -(r["valor_12m"] or 0), r["codigo"]))
    kp = {"itens": len(sel), "estoque": sum(r["estoque"] for r in sel), "a_caminho": sum(r["a_caminho"] for r in sel), "venda_mes": round(sum(r["media_mensal"] for r in sel), 1)}
    kp["cobertura"] = round((kp["estoque"] + kp["a_caminho"]) / kp["venda_mes"], 1) if kp["venda_mes"] else None
    page = max(int(f.get("page") or 1), 1); n = 10**9 if f.get("all") else size
    return {"total": len(sel), "page": page, "size": n, "rows": sel[(page - 1) * n: page * n], "counts": counts, "limites": lim, "janela": jan, "kpis": kp, "armazem": ARMAZEM}
