"""LEAD TIME dos pedidos de compra de amortecedor: pedido → embarque → previsão de chegada → recebimento, por fornecedor.

Objetivo do negócio: a estratégia é 6 MESES (180 dias) para amortecedores; este módulo mede o que o fornecedor REALMENTE entrega para identificar quem está «enrolando».
Fonte: PEDIDOS_COMPRA_DETALHADO (ds_compras) + EMBARQUES_DETALHADO (ds_embarques, quando o servidor a tiver) + histórico das datas previstas (po_due_history, gravado a cada sincronização).
Só pedidos EMITIDOS no ano vigente (filtro no SQL). Mesmo universo da tela Pedidos em Aberto: descrição «amortecedor» e código «MP-»; fornecedor traduzido do código EX (ZS / E-WIN / XGM / VERIFICAR).
Métricas (dias corridos, por linha de pedido):
  prazo_prometido  = DATA_PREV_ENT − DATA_EMISSAO_PC          (o que o fornecedor prometeu)
  ate_embarque     = embarque − emissão                          (pedido → embarque)
  transito         = previsão de chegada − embarque              (embarque → previsão para chegar)
  prazo_real       = recebimento/chegada − emissão               (só pedidos já entregues)
  atraso           = recebimento/chegada − DATA_PREV_ENT         (>0 = chegou depois do prometido)
Sinais de alerta: prometido acima da meta · previsão já vencida (aberto) · previsão empurrada (adiada) em sincronizações anteriores · atraso histórico."""
import datetime
import pandas as pd
import orders, rules

DEFAULT_META = 180

def meta_dias():
    try: v = int(float(rules._setting("leadtime_meta_dias") or DEFAULT_META))
    except (TypeError, ValueError): v = DEFAULT_META
    return v if 30 <= v <= 720 else DEFAULT_META

def _ensure(c):
    c.execute("CREATE TABLE IF NOT EXISTS po_due_history(id INTEGER PRIMARY KEY, pedido TEXT NOT NULL, code TEXT NOT NULL, due_date TEXT, seen_at TEXT NOT NULL, baseline INTEGER DEFAULT 0)")
    c.execute("CREATE INDEX IF NOT EXISTS ix_pdh ON po_due_history(pedido, code, id)")

def snapshot_due(today=None):
    """Chamada a cada sincronização: grava a DATA_PREV_ENT de cada linha de pedido quando ela muda (a 1ª gravação é o marco zero). Devolve quantas mudanças registrou."""
    import database as db
    c = db.conn(); at = (today or datetime.date.today()).isoformat()
    try:
        _ensure(c); first = c.execute("SELECT COUNT(*) FROM po_due_history").fetchone()[0] == 0
        last = {(r[0], r[1]): r[2] for r in c.execute("SELECT pedido, code, due_date FROM po_due_history WHERE id IN (SELECT MAX(id) FROM po_due_history GROUP BY pedido, code)")}
        new = [(p, k, d, at, 1 if first else 0) for p, k, d in c.execute("SELECT pedido, upper(code), due_date FROM ds_compras WHERE pedido IS NOT NULL AND code IS NOT NULL")
               if (str(p), k) not in last or last[(str(p), k)] != d]
        c.executemany("INSERT INTO po_due_history(pedido, code, due_date, seen_at, baseline) VALUES(?,?,?,?,?)", [(str(p), k, d, a, b) for p, k, d, a, b in new]); c.commit()
        return len(new)
    finally: c.close()

def _d(s): return pd.to_datetime(s, errors="coerce")
def _days(a, b): return (b - a).dt.days                    # b − a em dias (NaN se faltar alguma data)

def _stats(s):
    s = pd.to_numeric(s, errors="coerce").dropna()
    return {"n": int(len(s)), "media": None, "mediana": None, "p90": None, "max": None} if s.empty else {"n": int(len(s)), "media": round(float(s.mean()), 1), "mediana": round(float(s.median()), 1), "p90": round(float(s.quantile(.9)), 1), "max": int(s.max())}

def frame(today=None):
    """DataFrame com uma linha por (pedido, código) já com as métricas. Vazio se não houver compras sincronizadas.
    Usa só as linhas do universo (MP- + amortecedor), pré-filtradas no SQL — nunca o histórico inteiro de compras."""
    from queries import q
    from analytics import _has
    if not _has("ds_compras"): return None
    ano = (today or datetime.date.today()).year                      # ANO VIGENTE: só pedidos emitidos neste ano, filtrados já no SQL (poupa memória)
    df = orders.pedidos_em_aberto(orders.load(only_open=False, year=ano), only_open=False)
    rec = pd.DataFrame(q("SELECT upper(code) codigo, COALESCE(pedido,'') numero_pedido, MAX(received_date) received_date FROM ds_compras WHERE upper(code) LIKE 'MP-%' AND substr(order_date, 1, 4) = ? GROUP BY 1, 2", (f"{ano:04d}",)))
    df = df.merge(rec, on=["codigo", "numero_pedido"], how="left") if len(rec) else df.assign(received_date=None)
    df["emissao"], df["prevista"], df["recebido"] = _d(df["DATA_EMISSAO_PC"]), _d(df["DATA_PREV_ENT"]), _d(df["received_date"])
    df["embarque"] = pd.NaT; df["chegada_prev"] = pd.NaT; df["chegada"] = pd.NaT
    try:
        e = pd.DataFrame(q("SELECT COALESCE(pedido,'') pedido, upper(code) code, MIN(ship_date) ship, MAX(eta_date) eta, MAX(arrival_date) arr FROM ds_embarques GROUP BY 1, 2"))
    except Exception: e = pd.DataFrame()
    df.attrs["has_embarques"] = not e.empty
    if not e.empty:
        m = df.merge(e, left_on=["numero_pedido", "codigo"], right_on=["pedido", "code"], how="left")      # (pedido, código); senão só pelo pedido
        e2 = e.groupby("pedido").agg(ship=("ship", "min"), eta=("eta", "max"), arr=("arr", "max")).reset_index()
        m = m.merge(e2, left_on="numero_pedido", right_on="pedido", how="left", suffixes=("", "_p"))
        for a, b in (("ship", "ship_p"), ("eta", "eta_p"), ("arr", "arr_p")): m[a] = m[a].where(m[a].notna(), m[b])
        df["embarque"], df["chegada_prev"], df["chegada"] = _d(m["ship"]).values, _d(m["eta"]).values, _d(m["arr"]).values
    fim = df["recebido"].where(df["recebido"].notna(), df["chegada"])
    df["prazo_prometido"] = _days(df["emissao"], df["prevista"]); df["ate_embarque"] = _days(df["emissao"], df["embarque"])
    df["transito"] = _days(df["embarque"], df["chegada_prev"].where(df["chegada_prev"].notna(), df["prevista"]))
    df["prazo_real"] = _days(df["emissao"], fim); df["atraso"] = _days(df["prevista"], fim)
    hoje = pd.Timestamp(today or datetime.date.today()); df["idade"] = (hoje - df["emissao"]).dt.days
    df["vencida"] = df["em_aberto"] & df["prevista"].notna() & (df["prevista"] < hoje); df["dias_vencida"] = (hoje - df["prevista"]).dt.days.where(df["vencida"])
    df["entregue"] = fim.notna() | ~df["em_aberto"]
    return df

def _pushes():
    """{(pedido, código): {'vezes': n, 'dias': total empurrado}} a partir do histórico de previsões (ignora o marco zero)."""
    from queries import q
    try: h = pd.DataFrame(q("SELECT pedido, code, due_date, baseline FROM po_due_history ORDER BY id"))
    except Exception: return None
    if h.empty: return {}
    h["d"] = _d(h["due_date"]); h = h.dropna(subset=["d"])              # vetorizado: o histórico tem centenas de milhares de linhas (o laço por grupo levava minutos)
    if h.empty: return {}
    h["delta"] = h.groupby(["pedido", "code"])["d"].diff().dt.days
    up = h[h["delta"] > 0]
    if up.empty: return {}
    g = up.groupby(["pedido", "code"])["delta"].agg(["count", "sum"])
    return {k: {"vezes": int(r["count"]), "dias": int(r["sum"])} for k, r in g.iterrows()}

_C = {}
def payload(today=None):
    """Resultado em cache até a próxima sincronização (ou virada do dia): abrir a tela repetidamente não recalcula nada."""
    from queries import q1
    def n(t):
        try: return (q1(f"SELECT COUNT(*) n FROM {t}") or {}).get("n")
        except Exception: return None
    k = (orders._stamp(), n("po_due_history"), n("ds_embarques"), str(today or datetime.date.today()), meta_dias())
    if k is not None and _C.get("k") == k: return _C["v"]
    v = _payload(today)
    if k is not None: _C["k"], _C["v"] = k, v
    return v

def _payload(today=None):
    df = frame(today)
    if df is None or df.empty: return {"available": False}
    meta = meta_dias(); push = _pushes(); df["adiada_vezes"] = 0; df["adiada_dias"] = 0
    if push:
        df["adiada_vezes"] = [push.get((r.numero_pedido, r.codigo), {}).get("vezes", 0) for r in df.itertuples()]; df["adiada_dias"] = [push.get((r.numero_pedido, r.codigo), {}).get("dias", 0) for r in df.itertuples()]
    df["acima_meta"] = df["prazo_prometido"] > meta
    def alerts(r):
        a = []
        if r.acima_meta: a.append(f"prometido em {int(r.prazo_prometido)} dias (meta {meta})")
        if r.vencida: a.append(f"previsão vencida há {int(r.dias_vencida)} dias")
        if r.adiada_vezes: a.append(f"previsão adiada {int(r.adiada_vezes)}× (+{int(r.adiada_dias)} dias)")
        if r.em_aberto and pd.isna(r.embarque) and df.attrs.get("has_embarques") and pd.notna(r.idade) and r.idade > meta * 0.6: a.append(f"sem embarque há {int(r.idade)} dias")
        if pd.notna(r.atraso) and r.atraso > 0 and not r.em_aberto: a.append(f"chegou {int(r.atraso)} dias após o prometido")
        return a
    df["alertas"] = [alerts(r) for r in df.itertuples()]
    def block(g):
        ab = g[g["em_aberto"]]
        return {"linhas": int(len(g)), "em_aberto": int(len(ab)), "pedidos": int(g["numero_pedido"].nunique()),
                "prazo_prometido": _stats(g["prazo_prometido"]), "ate_embarque": _stats(g["ate_embarque"]), "transito": _stats(g["transito"]), "prazo_real": _stats(g["prazo_real"]), "atraso": _stats(g["atraso"]),
                "acima_meta": int(g["acima_meta"].sum()), "pct_acima_meta": round(100 * float(g["acima_meta"].mean()), 1) if len(g) else None,
                "vencidas": int(ab["vencida"].sum()), "adiadas": int((g["adiada_vezes"] > 0).sum()), "adiamento_medio_dias": round(float(g.loc[g["adiada_vezes"] > 0, "adiada_dias"].mean()), 1) if (g["adiada_vezes"] > 0).any() else None,
                "sem_embarque": int(ab["embarque"].isna().sum()) if df.attrs.get("has_embarques") else None,
                "no_prazo_pct": round(100 * float((g["atraso"].dropna() <= 0).mean()), 1) if g["atraso"].notna().any() else None}
    por = [{"fornecedor": f, **block(g)} for f, g in df.groupby("fornecedor")]
    bins = [(-10**6, 90, "até 90 dias"), (90, 180, "91 a 180"), (180, 270, "181 a 270"), (270, 10**6, "mais de 270")]
    dist = [{"faixa": l, "n": int(((df["prazo_prometido"] > a) & (df["prazo_prometido"] <= b)).sum())} for a, b, l in bins]
    cols = ["codigo", "numero_pedido", "fornecedor", "STATUS_PC", "DATA_EMISSAO_PC", "DATA_PREV_ENT", "quantidade", "prazo_prometido", "ate_embarque", "transito", "idade", "adiada_vezes", "alertas"]
    ab = df[df["em_aberto"]].copy()
    ab["_n"] = ab["alertas"].map(len); ab = ab.sort_values(["_n", "idade"], ascending=False)
    lin = ab[cols].astype(object).where(ab[cols].notna(), None).to_dict("records")
    for r in lin:
        for k in ("prazo_prometido", "ate_embarque", "transito", "idade", "adiada_vezes"): r[k] = None if r[k] is None else int(r[k])
        r["quantidade"] = None if r["quantidade"] is None else float(r["quantidade"])
    return {"available": True, "meta_dias": meta, "tem_embarques": bool(df.attrs.get("has_embarques")), "tem_historico": push is not None and bool(push or _has_hist()),
            "geral": block(df), "por_fornecedor": por, "distribuicao": dist, "linhas": lin[:300], "linhas_total": int(len(ab))}

def _has_hist():
    from queries import q1
    try: return (q1("SELECT COUNT(*) n FROM po_due_history") or {"n": 0})["n"] > 0
    except Exception: return False


# ═══════════════════════ PREVISÃO DE EMBARQUES E CHEGADAS ═══════════════════════
# O lead time é decomposto em ETAPAS medidas no histórico real de cada fornecedor (embarques já entregues):
#   produção     = embarque (DATA_EMBARQUE / ETD) − emissão do pedido   → quanto o fornecedor leva para embarcar
#   mar          = chegada ao porto − embarque                          → trânsito marítimo (depende do porto/rota)
#   desembaraço  = chegada à filial − chegada ao porto                  → porto, nacionalização e transporte interno
# Cada linha em aberto recebe a previsão a partir de ONDE ela está hoje: já no porto → só falta o desembaraço; no mar → ETA do servidor
# (ou embarque + mar típico) + desembaraço; aguardando embarque → emissão + produção típica (nunca antes de hoje) + mar + desembaraço.
# Faixa = p25…p75 de cada etapa somados (metade dos casos históricos cai dentro dela). Fornecedor com menos de MIN_N casos usa a base geral.
HIST_MESES = 24; MIN_N = 5; PARADO = "Parado — verificar saldo"
STAGES = (("producao", "Produção (pedido → embarque)"), ("mar", "Mar (embarque → porto)"), ("desembaraco", "Desembaraço (porto → filial)"), ("total", "Total (pedido → filial)"))

def _q(s, p):
    s = pd.to_numeric(s, errors="coerce").dropna(); s = s[s >= 0]
    return None if s.empty else float(s.quantile(p))

def _stage_stats(s):
    s = pd.to_numeric(s, errors="coerce").dropna(); s = s[s >= 0]
    if s.empty: return {"n": 0, "p25": None, "mediana": None, "p75": None, "p90": None, "media": None}
    return {"n": int(len(s)), "p25": round(float(s.quantile(.25))), "mediana": round(float(s.median())), "p75": round(float(s.quantile(.75))), "p90": round(float(s.quantile(.9))), "media": round(float(s.mean()), 1)}

def _embarques():
    """Embarques de amortecedor (MP-) com fornecedor traduzido do código EX e a emissão do pedido (de ds_compras)."""
    from queries import q
    try:
        e = pd.DataFrame(q("""SELECT COALESCE(pedido,'') pedido, upper(code) codigo, COALESCE(ex_code, supplier) forn, qty, ship_date, etd_date, eta_date, port_date, arrival_date, status, status_macro, process, origin_port, created_date
                              FROM ds_embarques WHERE upper(code) LIKE 'MP-%'"""))
        c = pd.DataFrame(q("SELECT COALESCE(pedido,'') pedido, upper(code) codigo, MIN(order_date) order_date, MAX(due_date) due_date FROM ds_compras WHERE upper(code) LIKE 'MP-%' GROUP BY 1, 2"))
    except Exception: return pd.DataFrame()
    if e.empty: return e
    e = e.merge(c, on=["pedido", "codigo"], how="left") if len(c) else e.assign(order_date=None, due_date=None)      # join em memória (pedido × código): rápido, sem subconsulta por linha
    e["fornecedor"] = e["forn"].map(orders.translate_supplier)
    for c in ("ship_date", "etd_date", "eta_date", "port_date", "arrival_date", "order_date", "due_date", "created_date"): e[c] = _d(e[c])
    e["embarque"] = e["ship_date"].where(e["ship_date"].notna(), e["etd_date"])
    e["producao"] = _days(e["order_date"], e["embarque"]); e["mar"] = _days(e["embarque"], e["port_date"])
    e["desembaraco"] = _days(e["port_date"], e["arrival_date"]); e["total"] = _days(e["order_date"], e["arrival_date"])
    e["atraso_promessa"] = _days(e["due_date"], e["arrival_date"])
    return e

def model(e, today=None):
    """Estatísticas de cada etapa por fornecedor (e «Geral»), só com embarques ENTREGUES nos últimos HIST_MESES meses."""
    hoje = pd.Timestamp(today or datetime.date.today()); lo = hoje - pd.DateOffset(months=HIST_MESES)
    h = e[e["arrival_date"].notna() & (e["arrival_date"] >= lo)] if not e.empty else e
    out = {"Geral": {k: _stage_stats(h[k]) if not h.empty else _stage_stats([]) for k, _ in STAGES}}
    if not h.empty:
        for f, g in h.groupby("fornecedor"): out[f] = {k: _stage_stats(g[k]) for k, _ in STAGES}
        rel = {}
        for f, g in [("Geral", h), *h.groupby("fornecedor")]:
            a = g.dropna(subset=["atraso_promessa"]).drop_duplicates(["pedido", "codigo"])
            rel[f] = {"linhas": int(len(a)), "no_prazo_pct": round(100 * float((a["atraso_promessa"] <= 0).mean()), 1) if len(a) else None,
                      "atraso_mediano": round(float(a["atraso_promessa"].median())) if len(a) else None, "atraso_p90": round(float(a["atraso_promessa"].quantile(.9))) if len(a) else None}
        for f in out: out[f]["confiabilidade"] = rel.get(f, {})
    return out, h

def _params(M, forn, stage):
    """(p25, mediana, p75) da etapa para o fornecedor; com poucos casos, usa a base Geral."""
    s = (M.get(forn) or {}).get(stage) or {}
    if (s.get("n") or 0) < MIN_N: s = M["Geral"][stage]
    return (s.get("p25"), s.get("mediana"), s.get("p75"), s.get("n") or 0)

def forecast(today=None):
    """Previsão linha a linha (pedido × código × embarque) dos pedidos em aberto + calendário mensal de chegadas e de embarques."""
    hoje = pd.Timestamp(today or datetime.date.today()).normalize()
    e = _embarques(); M, hist = model(e, today)
    ab = orders.pedidos_em_aberto(orders.load(True), only_open=True)
    if ab.empty: return {"available": False}
    ab["emissao"], ab["prometido"] = _d(ab["DATA_EMISSAO_PC"]), _d(ab["DATA_PREV_ENT"])
    open_e = e[e["arrival_date"].isna()] if not e.empty else e
    by_line = {k: g for k, g in open_e.groupby(["pedido", "codigo"])} if not open_e.empty else {}
    rows = []
    def days(x): return pd.Timedelta(days=float(x or 0))
    def add(r, etapa, qtd, base, falta, emb=None, eta=None, porto=None, proc=None, embarque_prev=None):
        p = [(_params(M, r.fornecedor, s)) for s in falta]
        lo = base + sum((days(a) for a, _, _, _ in p), pd.Timedelta(0)); mid = base + sum((days(b) for _, b, _, _ in p), pd.Timedelta(0)); hi = base + sum((days(c) for _, _, c, _ in p), pd.Timedelta(0))
        n = min([x[3] for x in p]) if p else 0
        atraso = (mid - r.prometido).days if pd.notna(r.prometido) else None
        rows.append({"codigo": r.codigo, "pedido": r.numero_pedido, "fornecedor": r.fornecedor, "quantidade": qtd, "etapa": etapa, "emissao": r.DATA_EMISSAO_PC, "prometido": r.DATA_PREV_ENT,
                     "embarque": None if emb is None or pd.isna(emb) else emb.strftime("%Y-%m-%d"), "embarque_previsto": None if embarque_prev is None else embarque_prev.strftime("%Y-%m-%d"),
                     "eta_servidor": None if eta is None or pd.isna(eta) else eta.strftime("%Y-%m-%d"), "porto": None if porto is None or pd.isna(porto) else porto.strftime("%Y-%m-%d"), "processo": proc,
                     "chegada_prevista": mid.strftime("%Y-%m-%d"), "faixa_de": lo.strftime("%Y-%m-%d"), "faixa_ate": hi.strftime("%Y-%m-%d"), "dias_para_chegar": int((mid - hoje).days),
                     "atraso_previsto": None if atraso is None else int(atraso), "base_n": int(n), "confianca": "alta" if n >= 20 else "média" if n >= MIN_N else "baixa"})
    for r in ab.itertuples():
        saldo = float(r.quantidade or 0); emb = by_line.get((r.numero_pedido, r.codigo))
        if emb is not None:
            for x in emb.itertuples():
                q_ = float(x.qty or 0) or saldo; saldo -= q_
                if pd.notna(x.port_date):
                    add(r, "No porto / desembaraço", q_, x.port_date, ["desembaraco"], x.embarque, x.eta_date, x.port_date, x.process)
                elif pd.notna(x.embarque) and x.embarque <= hoje:
                    base = x.eta_date if pd.notna(x.eta_date) else None
                    if base is not None: add(r, "No mar", q_, base, ["desembaraco"], x.embarque, x.eta_date, None, x.process)
                    else: add(r, "No mar", q_, x.embarque, ["mar", "desembaraco"], x.embarque, None, None, x.process)
                else:
                    base = x.embarque if pd.notna(x.embarque) else hoje
                    add(r, "Embarque programado", q_, base, ["mar", "desembaraco"], None, x.eta_date, None, x.process, embarque_prev=base)
        if saldo > 0.5:                                         # parte (ou tudo) ainda não embarcou: produção típica a partir da emissão (nunca antes de hoje)
            _, med, _, _ = _params(M, r.fornecedor, "producao"); p90 = ((M.get(r.fornecedor) or M["Geral"]).get("producao") or {}).get("p90") or M["Geral"]["producao"].get("p90") or 180
            ship = r.emissao + days(med) if pd.notna(r.emissao) and med is not None else hoje
            parado = pd.notna(r.emissao) and (hoje - r.emissao).days > 2 * p90      # sem embarque há mais que o dobro do p90 da produção: saldo provavelmente «fantasma»
            ship = max(ship, hoje)
            add(r, PARADO if parado else "Aguardando embarque", saldo, ship, ["mar", "desembaraco"], embarque_prev=None if parado else ship)
    df = pd.DataFrame(rows)
    if df.empty: return {"available": False}
    stale = df[df["etapa"] == PARADO]; df_all = df; df = df[df["etapa"] != PARADO].copy()     # parados: fora do calendário e dos KPIs de chegada (aparecem à parte)
    df["mes"] = df["chegada_prevista"].str[:7]; atual = hoje.strftime("%Y-%m")
    df.loc[df["mes"] < atual, "mes"] = atual                # previsão já vencida e ainda não chegou: conta no mês atual (atrasado)
    meses = pd.period_range(hoje.to_period("M"), periods=9, freq="M").strftime("%Y-%m").tolist()
    forn = sorted(df["fornecedor"].unique(), key=lambda f: (f == orders.UNKNOWN, f))
    cal = {"meses": meses + ["depois"], "series": [{"fornecedor": f, "qtd": [float(df[(df["fornecedor"] == f) & (df["mes"] == m)]["quantidade"].sum()) for m in meses] + [float(df[(df["fornecedor"] == f) & (df["mes"] > meses[-1])]["quantidade"].sum())]} for f in forn]}
    emb = df[df["embarque_previsto"].notna()].copy(); emb["mes"] = emb["embarque_previsto"].str[:7]
    cal_emb = {"meses": meses, "series": [{"fornecedor": f, "qtd": [float(emb[(emb["fornecedor"] == f) & (emb["mes"] == m)]["quantidade"].sum()) for m in meses]} for f in forn]}
    etapas = df_all.groupby("etapa").agg(linhas=("codigo", "size"), quantidade=("quantidade", "sum")).reset_index().to_dict("records")
    risco = df[(df["atraso_previsto"].fillna(-1) > 15)]
    df = pd.concat([df.sort_values(["chegada_prevista", "fornecedor", "codigo"]), stale.assign(mes=None).sort_values("emissao")], ignore_index=True)
    return {"available": True, "modelo": M, "etapas_def": dict(STAGES), "historico_meses": HIST_MESES, "historico_embarques": int(len(hist)), "min_n": MIN_N,
            "por_etapa": [{"etapa": r["etapa"], "linhas": int(r["linhas"]), "quantidade": float(r["quantidade"])} for r in etapas],
            "calendario": cal, "calendario_embarques": cal_emb, "linhas": df.drop(columns=["mes"]).astype(object).where(df.drop(columns=["mes"]).notna(), None).to_dict("records"), "linhas_total": int(len(df)),
            "risco": {"linhas": int(len(risco)), "quantidade": float(risco["quantidade"].sum()), "atraso_mediano": int(risco["atraso_previsto"].median()) if len(risco) else None},
            "parados": {"linhas": int(len(stale)), "quantidade": float(stale["quantidade"].sum()), "pedidos": int(stale["pedido"].nunique())},
            "proximos_30": float(df[(df["etapa"] != PARADO) & (df["dias_para_chegar"] <= 30)]["quantidade"].sum()), "proximos_90": float(df[(df["etapa"] != PARADO) & (df["dias_para_chegar"] <= 90)]["quantidade"].sum())}

_CF = {}
def forecast_cached(today=None):
    from queries import q1
    def n(t):
        try: return (q1(f"SELECT COUNT(*) n, COALESCE(MAX(rowid),0) m FROM {t}") or {}).get("m")
        except Exception: return None
    k = (orders._stamp(), n("ds_embarques"), str(today or datetime.date.today()))
    if _CF.get("k") == k: return _CF["v"]
    v = forecast(today); _CF["k"], _CF["v"] = k, v; return v
