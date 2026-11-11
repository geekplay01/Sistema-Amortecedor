"""Módulo PEDIDOS EM ABERTO (Pandas).

Regras (definidas pelo usuário):
  1. descricao contém «amortecedor» (sem acento nem caixa) E codigo começa OBRIGATORIAMENTE com «MP-».
  2. nova coluna `fornecedor`, traduzida de cod_fornecedor:  EX0002116 → ZS · EX0002110 → E-WIN · EX008042 → XGM · qualquer outro → «VERIFICAR».
  3. o payload devolve APENAS: codigo, numero_pedido, DATA_EMISSAO_PC (abertura), quantidade, DATA_PREV_ENT (previsão), fornecedor e STATUS_PC (situação do pedido no ERP; a tela filtra por ele).
   O payload traz também a marca `em_aberto` (saldo > 0) para o filtro «Em aberto / Todos».
«Em aberto»: linhas cujo saldo pendente é zero (pedido já totalmente recebido) ficam de fora; sem informação de saldo, a linha é mantida.
`quantidade` = saldo em aberto (se a base traz) ou a quantidade do pedido.
"""
import re, unicodedata
import pandas as pd

SUPPLIER_MAP = {"EX0002116": "ZS", "EX0002110": "E-WIN", "EX008042": "XGM",
                "EX0008042": "XGM"}          # grafia que o ERP também usa (EX + 7 dígitos) — mesmo fornecedor XGM
PREFIX = "MP-"; WORD = "AMORTECEDOR"; UNKNOWN = "VERIFICAR"
COLS = ["codigo", "numero_pedido", "DATA_EMISSAO_PC", "quantidade", "DATA_PREV_ENT", "fornecedor", "STATUS_PC"]

def _unaccent(s): return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
def _canon(c): return re.sub(r"[^a-z0-9]", "", _unaccent(c).lower())
def _txt(s): return s.astype("object").where(s.notna(), "").astype(str).str.replace(" ", " ", regex=False).str.strip()

def translate_supplier(v):
    """cod_fornecedor → nome. Aceita «EX0002116», «ex0002116 - ZS ZHEJIANG» etc.; o que não estiver no mapa vira «VERIFICAR»."""
    t = re.sub(r"\s+", "", str(v or "")).upper()
    if t in SUPPLIER_MAP: return SUPPLIER_MAP[t]
    m = re.search(r"EX\d{6,8}", str(v or "").upper())
    return SUPPLIER_MAP.get(m.group(0), UNKNOWN) if m else UNKNOWN

def _col(df, *names):
    by = {_canon(c): c for c in df.columns}
    for n in names:
        if _canon(n) in by: return by[_canon(n)]
    return None

def pedidos_em_aberto(df, only_open=True):
    """df com colunas (nomes tolerantes): codigo, descricao, cod_fornecedor, numero_pedido, DATA_EMISSAO_PC, quantidade, DATA_PREV_ENT [, saldo]. → DataFrame só com COLS."""
    c = {k: _col(df, *n) for k, n in {"codigo": ("codigo", "cod_produto"), "descricao": ("descricao",), "forn": ("cod_fornecedor", "codigo_fornecedor", "ex_code"),
                                       "pedido": ("numero_pedido", "pedido", "num_pedido"), "emissao": ("DATA_EMISSAO_PC", "data_emissao", "order_date"),
                                       "qtd": ("quantidade", "qtde", "qtd"), "prev": ("DATA_PREV_ENT", "previsao", "due_date"), "saldo": ("saldo", "qty_pending", "qtde_pendente"), "status": ("STATUS_PC", "status_pedido", "status")}.items()}
    miss = [k for k in ("codigo", "descricao") if not c[k]]
    if miss: raise ValueError("Colunas obrigatórias ausentes no pedido: " + ", ".join(miss))
    z = pd.Series([None] * len(df), index=df.index, dtype="object"); g = lambda k: df[c[k]] if c[k] else z
    codigo = _txt(df[c["codigo"]]).str.upper(); desc = _txt(df[c["descricao"]]).map(_unaccent).str.upper()
    keep = codigo.str.startswith(PREFIX) & desc.str.contains(WORD, regex=False)
    saldo = pd.to_numeric(g("saldo"), errors="coerce"); aberto = ~(saldo.fillna(1) <= 0)                       # saldo 0 = pedido já recebido
    if only_open: keep &= aberto
    qtd = saldo.where(saldo.notna(), pd.to_numeric(g("qtd"), errors="coerce"))
    out = pd.DataFrame({"codigo": codigo, "numero_pedido": _txt(g("pedido")), "DATA_EMISSAO_PC": pd.to_datetime(g("emissao"), errors="coerce"), "quantidade": qtd,
                        "DATA_PREV_ENT": pd.to_datetime(g("prev"), errors="coerce"), "fornecedor": g("forn").map(translate_supplier), "STATUS_PC": _txt(g("status")).str.upper().replace("", "NÃO INFORMADO"), "em_aberto": aberto})[keep]
    out = out.sort_values(["DATA_EMISSAO_PC", "numero_pedido", "codigo"], na_position="last").reset_index(drop=True)
    for k in ("DATA_EMISSAO_PC", "DATA_PREV_ENT"): out[k] = out[k].dt.strftime("%Y-%m-%d").where(out[k].notna(), None)
    out["quantidade"] = out["quantidade"].map(lambda v: None if pd.isna(v) else int(v) if float(v).is_integer() else float(v))
    return out[COLS + ["em_aberto"]]

def load(only_open=True, year=None):
    """Lê do cache local (ds_compras) JÁ FILTRADO NO SQL (código «MP-» + descrição «amortecedor» + saldo > 0): com centenas de milhares de linhas de histórico, trazer tudo para o Pandas era o que travava a tela.
    `year` (opcional) mantém só pedidos EMITIDOS naquele ano, já no SQL (usado pelo Lead time). Os filtros do SQL são só um pré-corte; as regras exatas continuam em pedidos_em_aberto()."""
    from queries import q
    w = "upper(code) LIKE 'MP-%' AND upper(description) LIKE '%AMORTECEDOR%'" + (" AND COALESCE(qty_pending, 1) > 0" if only_open else "") + (f" AND substr(order_date, 1, 4) = '{int(year):04d}'" if year else "")
    rows = q("SELECT code AS codigo, description AS descricao, COALESCE(ex_code, supplier) AS cod_fornecedor, pedido AS numero_pedido, order_date AS DATA_EMISSAO_PC, "
             f"qty_ordered AS quantidade, qty_pending AS saldo, due_date AS DATA_PREV_ENT, status AS STATUS_PC, received_date FROM ds_compras WHERE {w}")
    return pd.DataFrame(rows, columns=["codigo", "descricao", "cod_fornecedor", "numero_pedido", "DATA_EMISSAO_PC", "quantidade", "saldo", "DATA_PREV_ENT", "STATUS_PC", "received_date"])

_CACHE = {}
def _stamp():
    """Muda quando uma sincronização troca ds_compras (o resultado só precisa ser recalculado aí)."""
    from queries import q1
    try: r = q1("SELECT COALESCE(MAX(id),0) i, COUNT(*) n FROM ds_runs WHERE dataset='compras'"); return (r["i"], r["n"])
    except Exception: return None

def _open():
    k = _stamp()
    if _CACHE.get("k") != k or k is None:
        _CACHE.clear(); _CACHE["k"] = k; _CACHE["df"] = pedidos_em_aberto(load(True), only_open=True)
    return _CACHE["df"]

AMOSTRA_ABERTA = ("cotacao", "sc_aberta", "chegou")      # etapas de amostra ainda em andamento

def amostras_df():
    """Pedidos de AMOSTRA (aba «Compra de amostras», vindos da planilha Compra_de_amostra) no mesmo formato da lista de pedidos, com TIPO_PEDIDO='Amostra'.
    Servem só para consulta: NUNCA entram em resumo, KPIs, lead time ou alertas (que são dos pedidos de compra do servidor)."""
    from queries import q, STAGES
    lab = dict(STAGES)
    rows = q("SELECT perfect_code, sample_code, sc_number, supplier, stage FROM sample_orders WHERE coalesce(perfect_code, sample_code) IS NOT NULL ORDER BY id")
    df = pd.DataFrame({"codigo": [(r["perfect_code"] or r["sample_code"] or "").upper() for r in rows], "numero_pedido": [r["sc_number"] or "" for r in rows], "DATA_EMISSAO_PC": None, "quantidade": None,
                       "DATA_PREV_ENT": None, "fornecedor": [{"EWIN": "E-WIN"}.get((r["supplier"] or "").strip().upper(), (r["supplier"] or "").strip().upper()) or UNKNOWN for r in rows], "STATUS_PC": [lab.get(r["stage"], r["stage"] or "").upper() for r in rows],
                       "em_aberto": [r["stage"] in AMOSTRA_ABERTA for r in rows], "TIPO_PEDIDO": "Amostra"}, columns=COLS + ["em_aberto", "TIPO_PEDIDO"])
    return df

def payload(q=None, fornecedor=None, status=None, incluir_recebidos=False, page=1, size=200, tipo="compra"):
    """{'available','columns','rows' (UMA PÁGINA, só as colunas do contrato + em_aberto),'total','page','size','status_pc','summary'}.
    O resumo e os chips contam sempre os pedidos EM ABERTO; `incluir_recebidos` acrescenta os já recebidos à lista. `tipo`: «compra» (padrão: pedidos do servidor), «amostra» (pedidos de amostra) ou «todos» — o resumo e os chips contam SEMPRE só as compras. Filtros e paginação são feitos aqui — a tela nunca recebe milhares de linhas."""
    from analytics import _has
    if not _has("ds_compras"): return {"available": False, "rows": [], "columns": COLS}
    ab = _open()
    df = ab if not incluir_recebidos else pedidos_em_aberto(load(False), only_open=False)
    by = ab.groupby("fornecedor").agg(pedidos=("numero_pedido", "nunique"), itens=("codigo", "nunique"), quantidade=("quantidade", "sum")).reset_index()
    st = ab.groupby("STATUS_PC").size().reset_index(name="linhas")
    tipo = tipo if tipo in ("compra", "amostra", "todos") else "compra"; am = amostras_df()
    df = df.assign(TIPO_PEDIDO="Compra"); df = {"compra": df, "amostra": am, "todos": pd.concat([df, am], ignore_index=True)}[tipo]
    sa = am.groupby("STATUS_PC").size().reset_index(name="linhas")
    f = df; conv = []
    if fornecedor: f = f[f["fornecedor"] == fornecedor]
    if status: f = f[f["STATUS_PC"] == status]
    if q and q.strip():
        t = q.strip().upper(); m = f["codigo"].str.contains(t, regex=False) | f["numero_pedido"].str.upper().str.contains(t, regex=False)
        from queries import perfect_codes, code_key
        conv = perfect_codes(t)                                                  # código de concorrente (CrossCatalogo) → código(s) PERFECT; pedidos do item PERFECT entram na lista
        if conv:
            ks = {code_key(c) for c in conv}; ck = f["codigo"].str.upper().str.replace(r"[^A-Z0-9]", "", regex=True)
            m = m | ck.isin(ks) | ck.str.replace(r"^MP", "", regex=True).isin(ks)
        f = f[m]
    size = max(10, min(int(size or 200), 1000)); page = max(1, int(page or 1)); total = len(f)
    rows = f.iloc[(page - 1) * size: page * size].astype(object).where(lambda x: x.notna(), None).to_dict("records")
    return {"available": True, "busca": {"termo": (q or "").strip(), "perfect": conv}, "columns": COLS, "rows": rows, "total": total, "page": page, "size": size, "tipo": tipo, "n_amostras": len(am), "status_pc": [{"status": r["STATUS_PC"], "linhas": int(r["linhas"])} for r in [*st.to_dict("records"), *sa.to_dict("records")]],
            "summary": {"linhas": len(ab), "pedidos": int(ab["numero_pedido"].nunique()), "itens": int(ab["codigo"].nunique()), "quantidade": float(ab["quantidade"].sum() or 0), "verificar": int((ab["fornecedor"] == UNKNOWN).sum()),
                        "vencidas": int((ab["DATA_PREV_ENT"].notna() & (ab["DATA_PREV_ENT"] < __import__("datetime").date.today().isoformat())).sum()),
                        "por_fornecedor": [{"fornecedor": r["fornecedor"], "pedidos": int(r["pedidos"]), "itens": int(r["itens"]), "quantidade": float(r["quantidade"] or 0)} for r in by.to_dict("records")]}}
