"""CONCILIAÇÃO: export do BI (VENDA_POR_SKU) × servidor × catálogo.
1) BI × servidor: mesmos filtros do BI (ano, mês, LINHA) aplicados em ds_vendas (VENDAS_FATURAMENTO_DETALHADO); mostra SKUs só no BI, só no servidor e diferenças de QTD/VALOR.
2) Vendas × CATÁLOGO (planilha CatalogoAMD = fonte de verdade): SKU vendido que NÃO está no catálogo — com o AMD equivalente quando o código é OEM/concorrente/fornecedor de um produto do catálogo.
Nada é gravado: é só um relatório."""
import io, re, unicodedata
import pandas as pd

MESES = {"janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12}
def _un(s): return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
def key(s): return re.sub(r"[^A-Z0-9]", "", _un(s).upper())

def parse_bi(src, name=""):
    """Export do Power BI: colunas PRODUTO/QTD/VALOR + linha final «Filtros aplicados: …». → (DataFrame limpo, filtros {ano, mes, incluidos, excluidos})."""
    raw = pd.read_csv(src, sep=None, engine="python", dtype=object) if str(name).lower().endswith((".csv", ".txt")) else pd.read_excel(src, dtype=object)
    by = {key(c): c for c in raw.columns}; miss = [n for n in ("PRODUTO", "QTD", "VALOR") if n not in by]
    if miss: raise ValueError("Colunas ausentes no export do BI: " + ", ".join(miss) + ". Colunas lidas: " + ", ".join(map(str, raw.columns)))
    p, q_, v = by["PRODUTO"], by["QTD"], by["VALOR"]; note = ""
    for x in raw[p].dropna().astype(str):
        if x.strip().lower().startswith("filtros"): note = x
    d = pd.DataFrame({"PRODUTO": raw[p].astype("object").where(raw[p].notna(), "").astype(str).str.strip().str.upper(), "QTD": pd.to_numeric(raw[q_], errors="coerce"), "VALOR": pd.to_numeric(raw[v], errors="coerce")})
    d = d[(d["PRODUTO"] != "") & ~d["PRODUTO"].str.lower().str.startswith(("filtros", "total")) & d["QTD"].notna()]
    d = d.groupby("PRODUTO", as_index=False).agg(QTD=("QTD", "sum"), VALOR=("VALOR", "sum"))
    t = _un(note).lower(); f = {"ano": None, "mes": None, "incluidos": [], "excluidos": [], "texto": note.strip()}
    m = re.search(r"ano e\w*\s*(\d{4})", t); f["ano"] = int(m.group(1)) if m else None
    m = re.search(r"mes e\w*\s*([a-z]+)", t); f["mes"] = MESES.get(m.group(1)) if m else None
    m = re.search(r"incluidos[^\n]*?([A-Z][A-Z ]+)\s*\(linha\)", _un(note), re.I); f["incluidos"] = [m.group(1).strip().upper()] if m else []
    m = re.search(r"linha nao e\s*(.+)", t)
    if m: f["excluidos"] = [x.strip().upper() for x in re.split(r",|\sou\s", m.group(1)) if x.strip() and "branco" not in x]
    return d, f

def _server(f):
    from queries import q
    from analytics import _has
    if not _has("ds_vendas"): return None
    where, par = ["code IS NOT NULL"], []
    if f["ano"]: where.append("substr(sale_date,1,4)=?"); par.append(str(f["ano"]))
    if f["mes"]: where.append("substr(sale_date,6,2)=?"); par.append(f"{f['mes']:02d}")
    df = pd.DataFrame(q("SELECT upper(trim(code)) PRODUTO, qty QTD, total VALOR, COALESCE(NULLIF(line,''), description) LINHA FROM ds_vendas WHERE " + " AND ".join(where), par), columns=["PRODUTO", "QTD", "VALOR", "LINHA"])
    if df.empty: return df
    ln = df["LINHA"].fillna("").astype(str).map(_un).str.upper()
    for w in f["incluidos"] or ["AMORTECEDOR"]: df = df[ln.loc[df.index].str.contains(_un(w).upper(), regex=False)]; ln = ln.loc[df.index]
    for w in f["excluidos"]: df = df[~ln.loc[df.index].eq(_un(w).upper())]
    return df.groupby("PRODUTO", as_index=False).agg(QTD=("QTD", "sum"), VALOR=("VALOR", "sum"))

def vs_catalogo(bi):
    """SKUs vendidos que não estão no catálogo (catalog_position não nulo); sugere o produto do catálogo cujo código OEM/concorrente/fornecedor é igual ao SKU."""
    from queries import q
    cat = {r["perfect_code"] for r in q("SELECT perfect_code FROM products WHERE catalog_position IS NOT NULL")}
    if not cat: return None
    alias = {}
    for r in q("SELECT p.perfect_code pc, k.code, k.code_type t FROM codes k JOIN products p ON p.id=k.product_id WHERE p.catalog_position IS NOT NULL"): alias.setdefault(key(r["code"]), []).append((r["pc"], r["t"]))
    fora = bi[~bi["PRODUTO"].isin(cat)].sort_values("VALOR", ascending=False); rows = []
    for r in fora.itertuples():
        eq = alias.get(key(r.PRODUTO), []); rows.append({"produto": r.PRODUTO, "qtd": float(r.QTD), "valor": float(r.VALOR), "equivalente": ", ".join(f"{a} ({t})" for a, t in eq[:3]), "resolvido": bool(eq)})
    tot = float(bi["VALOR"].sum()) or 1.0
    return {"catalogo_produtos": len(cat), "skus_no_catalogo": int(bi["PRODUTO"].isin(cat).sum()), "skus_fora": len(rows), "valor_fora": float(fora["VALOR"].sum()), "pct_valor_fora": round(100 * float(fora["VALOR"].sum()) / tot, 1),
            "resolvidos_por_equivalencia": sum(r["resolvido"] for r in rows), "valor_resolvido": round(sum(r["valor"] for r in rows if r["resolvido"]), 2),
            "catalogo_sem_venda": len(cat - set(bi["PRODUTO"])), "rows": rows}

def vendas(src, name=""):
    bi, f = parse_bi(src, name); sv = _server(f); out = {"filtros": f, "bi": {"skus": len(bi), "qtd": float(bi["QTD"].sum()), "valor": round(float(bi["VALOR"].sum()), 2)}, "catalogo": vs_catalogo(bi)}
    if sv is None or sv.empty:
        out["servidor"] = {"disponivel": False, "motivo": "O servidor ainda não trouxe vendas para este período (sincronize VENDAS_FATURAMENTO_DETALHADO)." if sv is None else "Nenhuma venda no servidor com estes filtros (ano/mês/linha)."}; return out
    m = bi.merge(sv, on="PRODUTO", how="outer", suffixes=("_bi", "_srv"), indicator=True); z = lambda c: m[c].fillna(0)
    m["dq"], m["dv"] = z("QTD_srv") - z("QTD_bi"), (z("VALOR_srv") - z("VALOR_bi")).round(2)
    both = m[m["_merge"] == "both"]; dif = both[(both["dq"].abs() > 0) | (both["dv"].abs() > 0.05)].sort_values("dv", key=abs, ascending=False)
    row = lambda r: {"produto": r.PRODUTO, "qtd_bi": None if pd.isna(r.QTD_bi) else float(r.QTD_bi), "valor_bi": None if pd.isna(r.VALOR_bi) else float(r.VALOR_bi), "qtd_srv": None if pd.isna(r.QTD_srv) else float(r.QTD_srv), "valor_srv": None if pd.isna(r.VALOR_srv) else float(r.VALOR_srv), "dq": float(r.dq), "dv": float(r.dv)}
    out["servidor"] = {"disponivel": True, "skus": len(sv), "qtd": float(sv["QTD"].sum()), "valor": round(float(sv["VALOR"].sum()), 2), "iguais": int(len(both) - len(dif)), "diferentes": int(len(dif)),
        "so_no_bi": [row(r) for r in m[m["_merge"] == "left_only"].sort_values("VALOR_bi", ascending=False).head(200).itertuples()], "so_no_servidor": [row(r) for r in m[m["_merge"] == "right_only"].sort_values("VALOR_srv", ascending=False).head(200).itertuples()],
        "diferencas": [row(r) for r in dif.head(200).itertuples()], "n_so_bi": int((m["_merge"] == "left_only").sum()), "n_so_srv": int((m["_merge"] == "right_only").sum())}
    return out
