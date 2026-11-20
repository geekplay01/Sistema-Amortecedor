"""Vendas × estoque — tela «Estoque» (etapa 16 · C2–C5; fonte do estoque na etapa 20 · Q5/Q6). Um item por código (sem pontuação; o prefixo MP- dos pedidos sai).
  • Itens = só os do controle (catálogo: products com catalog_position).
  • Estoque = ESTOQUE_ANALISE_REPOSICAO (ds_situacao): total PRIVATE + FECT, que é PA + MP. `conta` escolhe o que entra na cobertura: total (padrão), só PA ou só MP.
    Cada linha leva as partes (PA, MP, PRIVATE, FECT) para a dica da tela.
  • Venda média mensal = peças dos últimos 12 meses FECHADOS ÷ 12 (o mês atual, parcial, fica de fora), do próprio app (ds_vendas). Linhas: amortecedor,
    linha pesada e kit — vale a venda do próprio SKU, não o total do BI.
  • A caminho = pedidos em aberto da previsão de chegadas (leadtime), SEM os «Parado — verificar saldo».
  • Cobertura (meses) = (estoque + a caminho) ÷ venda média.
  • Situação: ruptura (vende e o estoque disponível é 0) · risco (< meta de lead time em meses, 180 d = 6) · ok (até 18) · excesso (> 18) · sem giro (estoque sem venda em 12 meses).
  • Projeção (etapa 16 · A1): mês a mês por 6 meses a partir do atual, saldo = estoque + chegadas previstas do mês − venda média (no mês atual, só a fração
    dos dias que faltam: o estoque de hoje já desconta o que vendeu até agora; previsão vencida conta no mês atual; parado não chega). «Falta em» = 1º mês com saldo negativo; «antes de chegar» = tem pedido a caminho, mas falta antes de ele cobrir.
  • Atalhos (situação, classe ABC, vai faltar): cada número = linhas da lista ao clicar (ignora o próprio filtro, respeita os outros)."""
import re, datetime
from queries import q

FONTE = "ESTOQUE_ANALISE_REPOSICAO"; EXCESSO = 18; HORIZONTE = 6
CONTA = {"total": "PA + MP", "pa": "só PA", "mp": "só MP"}
def _meses(today):
    y, m = today.year, today.month; out = []
    for _ in range(HORIZONTE): out.append(f"{y}-{m:02d}"); y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out
SIT = ("ruptura", "risco", "ok", "excesso", "sem_giro")
LINHAS = "amortecedor,pesada,kit"
def _k(c): return re.sub(r"[^A-Z0-9]", "", re.sub(r"^\s*MP-", "", str(c or "").upper()))

def _janela(today):
    """(primeiro dia do 12º mês fechado, primeiro dia do mês atual) — ex.: 17/11/2026 → ('2025-11-01', '2026-11-01')."""
    a = today.replace(day=1); y, m = a.year - 1, a.month
    return f"{y}-{m:02d}-01", a.isoformat()

def _partes(r):
    """Partes do estoque de uma linha de ds_situacao; o total é QTD_EST_T_PRIVATE_E_FECT (ou a soma das partes, se faltar)."""
    pp, pm, fp, fm = (float(r[k] or 0) for k in ("pp", "pm", "fp", "fm"))
    tot = float(r["t"]) if r["t"] is not None else pp + pm + fp + fm
    return {"total": tot, "pa": pp + fp, "mp": pm + fm, "private": pp + pm, "fect": fp + fm}

def base(today=None, conta="total"):
    import curva_abc, leadtime
    today = today or datetime.date.today(); de, ate = _janela(today); ls, lp = curva_abc.linha_sql(LINHAS)
    conta = conta if conta in CONTA else "total"
    zero = {"total": 0.0, "pa": 0.0, "mp": 0.0, "private": 0.0, "fect": 0.0}
    it = {_k(r["perfect_code"]): {"codigo": _k(r["perfect_code"]), "descricao": r["description"], "venda_12m": 0.0, "valor_12m": 0.0, "partes": dict(zero), "a_caminho": 0.0}
          for r in q("SELECT perfect_code, description FROM products WHERE catalog_position IS NOT NULL AND trim(coalesce(perfect_code,''))<>''")}
    it.pop("", None)
    for r in q(f"SELECT code, SUM(qty) qq, SUM(total) vv FROM ds_vendas WHERE sale_date>=? AND sale_date<? AND {ls} GROUP BY code", [de, ate, *lp]):
        x = it.get(_k(r["code"]))
        if x: x["venda_12m"] += r["qq"] or 0; x["valor_12m"] += r["vv"] or 0
    try: est = q("SELECT code, MAX(stock_total) t, MAX(priv_pa) pp, MAX(priv_mp) pm, MAX(fect_pa) fp, MAX(fect_mp) fm FROM ds_situacao GROUP BY code")
    except Exception: est = []                    # banco sem as colunas de estoque (antes da 1ª sincronização da etapa 20)
    for r in est:
        x = it.get(_k(r["code"]))
        if x: x["partes"] = _partes(r)
    F = leadtime.forecast_cached(today) or {}; meses = _meses(today); idx = {m: i for i, m in enumerate(meses)}
    for r in (F.get("linhas") or []) if F.get("available") else []:
        if r.get("etapa") == leadtime.PARADO: continue
        x = it.get(_k(r["codigo"]))
        if x is None: continue                    # só itens do catálogo
        qq = float(r.get("quantidade") or 0); x["a_caminho"] += qq
        mm = max(str(r.get("chegada_prevista") or meses[0])[:7], meses[0])          # vencida (ou sem data) → mês atual
        if mm in idx: x.setdefault("chegadas", [0.0] * HORIZONTE)[idx[mm]] += qq
    risco = round(leadtime.meta_dias() / 30, 1)
    vals = sorted((x for x in it.values() if x["valor_12m"] > 0), key=lambda x: -x["valor_12m"]); tot = sum(x["valor_12m"] for x in vals) or 1; acc = 0
    for x in vals:
        x["classe"] = "A" if acc / tot * 100 < 80 else "B" if acc / tot * 100 < 95 else "C"; acc += x["valor_12m"]
    import calendar
    dias = calendar.monthrange(today.year, today.month)[1]; resto = (dias - today.day + 1) / dias      # mês atual: o estoque de hoje já desconta a venda até agora → só o resto do mês
    out = []
    for x in it.values():
        disp = max(x["partes"][conta], 0); media = round(x["venda_12m"] / 12, 2)
        if media <= 0 and disp <= 0: continue          # item do catálogo sem venda e sem estoque (no que se está contando) não entra
        cob = round((disp + x["a_caminho"]) / media, 1) if media > 0 else None
        sit = "sem_giro" if media <= 0 else "ruptura" if disp <= 0 else "risco" if cob < risco else "ok" if cob <= EXCESSO else "excesso"
        ch = x.get("chegadas") or [0.0] * HORIZONTE; saldo, proj, falta = disp, [], None
        for i in range(HORIZONTE):
            saldo = saldo + ch[i] - media * (resto if i == 0 else 1); proj.append(round(saldo, 1))
            if falta is None and saldo < 0: falta = meses[i]
        out.append({"codigo": x["codigo"], "descricao": x["descricao"], "venda_12m": x["venda_12m"], "valor_12m": round(x["valor_12m"], 2), "media_mensal": media, "estoque": disp,
                    "partes": {k: round(v, 1) for k, v in x["partes"].items()}, "a_caminho": x["a_caminho"], "cobertura": cob, "situacao": sit, "classe": x.get("classe") or "—",
                    "chegadas": ch, "projecao": proj, "falta_em": falta, "antes_de_chegar": bool(falta) and x["a_caminho"] > 0})
    return out, {"risco": risco, "excesso": EXCESSO}, {"de": de, "ate": ate, "meses": meses}

_MAPA = {}
def mapa(today=None):
    """(linhas por código sem pontuação, limites, janela) — o mesmo cálculo da tela, em memória até a próxima sincronização ou a virada do dia
    (página do item e Cobertura de concorrentes, etapa 17)."""
    from queries import q1
    hoje = today or datetime.date.today(); run = (q1("SELECT MAX(id) i FROM ds_runs") or {}).get("i"); key = (hoje.isoformat(), run)
    if _MAPA.get("k") != key:
        try: rows, lim, jan = base(hoje)
        except Exception: rows, lim, jan = [], {}, {"meses": []}
        _MAPA.update(k=key, v=({r["codigo"]: r for r in rows}, lim, jan))
    return _MAPA["v"]

ORDEM = {"ruptura": 0, "risco": 1, "ok": 2, "excesso": 3, "sem_giro": 4}
def listing(f, today=None, size=100):
    conta = f.get("conta") if f.get("conta") in CONTA else "total"
    rows, lim, jan = base(today, conta)
    term = (f.get("q") or "").upper().split(); sit = f.get("situacao") or ""; cl = f.get("classe") or ""; fa = bool(f.get("falta"))
    def ok(r, skip=""):
        if any(t not in f"{r['codigo']} {r['descricao'] or ''}".upper() for t in term): return False
        if skip != "situacao" and sit and r["situacao"] != sit: return False
        if skip != "classe" and cl and r["classe"] != cl: return False
        if skip != "falta" and fa and not r["falta_em"]: return False
        return True
    counts = {"situacao": {s: sum(1 for r in rows if r["situacao"] == s and ok(r, "situacao")) for s in SIT}, "classe": {}, "falta": sum(1 for r in rows if r["falta_em"] and ok(r, "falta")),
              "antes_de_chegar": sum(1 for r in rows if r["antes_de_chegar"] and ok(r, "falta"))}
    for r in rows:
        if ok(r, "classe"): counts["classe"][r["classe"]] = counts["classe"].get(r["classe"], 0) + 1
    chave = (lambda r: (r["falta_em"] or "9999", -(r["valor_12m"] or 0), r["codigo"])) if fa else (lambda r: (ORDEM[r["situacao"]], -(r["valor_12m"] or 0), r["codigo"]))     # «vai faltar»: o que falta primeiro
    sel = sorted((r for r in rows if ok(r)), key=chave)
    kp = {"itens": len(sel), "estoque": sum(r["estoque"] for r in sel), "a_caminho": sum(r["a_caminho"] for r in sel), "venda_mes": round(sum(r["media_mensal"] for r in sel), 1),
          **{p: round(sum(r["partes"][p] for r in sel)) for p in ("pa", "mp", "private", "fect")}}
    kp["cobertura"] = round((kp["estoque"] + kp["a_caminho"]) / kp["venda_mes"], 1) if kp["venda_mes"] else None
    page = max(int(f.get("page") or 1), 1); n = 10**9 if f.get("all") else size
    return {"total": len(sel), "page": page, "size": n, "rows": sel[(page - 1) * n: page * n], "counts": counts, "limites": lim, "janela": jan, "meses": jan["meses"], "kpis": kp,
            "fonte": FONTE, "conta": conta, "contas": CONTA}
