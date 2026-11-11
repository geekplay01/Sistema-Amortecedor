"""Vendas FATURADAS — CURVA A (ABC) de amortecedores (Pandas).

Regras (definidas pelo usuário):
  1. agrupa pelo código do PRODUTO (SKU)
  2. soma a quantidade (QTD) e o valor faturado (VALOR)
  3. ordena do MAIOR para o MENOR valor faturado
  4. base = vendas faturadas do BI, com todos os valores de AMORTECEDORES (LINHA contém «AMORTECEDOR»: inclui linha pesada e kits).
Além do pedido: participação %, % acumulado e classe A (até 80% do faturamento) / B (até 95%) / C — a «Curva A» é a classe A.
"""
import re, unicodedata
import pandas as pd

CUT_A, CUT_B = 80.0, 95.0
def _unaccent(s): return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
def _canon(c): return re.sub(r"[^a-z0-9]", "", _unaccent(c).lower())
def _col(df, *names):
    by = {_canon(c): c for c in df.columns}
    for n in names:
        if _canon(n) in by: return by[_canon(n)]
    return None

def curva_a(df, linha="AMORTECEDOR"):
    """df do BI (PRODUTO, QTD, VALOR [, LINHA]) → DataFrame [PRODUTO, QTD, VALOR, pct, acum_pct, classe], ordenado por VALOR desc.
    Se houver coluna LINHA, só entram linhas que a contêm (caixa/acento/espaços ignorados)."""
    p, q, v, l = (_col(df, *n) for n in (("PRODUTO", "codigo", "code", "sku"), ("QTD", "qtde", "quantidade", "qty"), ("VALOR", "valor_total", "faturado", "total"), ("LINHA", "line")))
    miss = [n for n, c in (("PRODUTO", p), ("QTD", q), ("VALOR", v)) if not c]
    if miss: raise ValueError("Colunas ausentes na base de vendas: " + ", ".join(miss))
    d = pd.DataFrame({"PRODUTO": df[p].astype("object").where(df[p].notna(), "").astype(str).str.replace(" ", " ", regex=False).str.strip().str.upper(),
                      "QTD": pd.to_numeric(df[q], errors="coerce").fillna(0), "VALOR": pd.to_numeric(df[v], errors="coerce").fillna(0)})
    if l is not None and linha:
        ln = df[l].astype("object").where(df[l].notna(), "").astype(str).map(_unaccent).str.upper()
        d = d[ln.str.contains(_unaccent(linha).upper(), regex=False)]
    d = d[d["PRODUTO"] != ""]
    g = d.groupby("PRODUTO", as_index=False).agg(QTD=("QTD", "sum"), VALOR=("VALOR", "sum")).sort_values(["VALOR", "QTD", "PRODUTO"], ascending=[False, False, True]).reset_index(drop=True)
    tot = g["VALOR"].sum(); g["pct"] = (g["VALOR"] / tot * 100).round(2) if tot else 0.0
    cum = g["VALOR"].cumsum(); g["acum_pct"] = (cum / tot * 100).round(2) if tot else 0.0
    before = ((cum - g["VALOR"]) / tot * 100) if tot else pd.Series([100.0] * len(g))
    g["classe"] = before.map(lambda b: "A" if b < CUT_A else "B" if b < CUT_B else "C")
    return g

def load(year=None, month=None):
    """Vendas faturadas do cache local (ds_vendas) — filtra ano/mês (como os filtros Ano/Mês do BI). Sem coluna LINHA na base, usa a descrição do produto."""
    from queries import q
    where, par = ["code IS NOT NULL"], []
    if year: where.append("substr(sale_date,1,4)=?"); par.append(str(int(year)))
    if month: where.append("substr(sale_date,6,2)=?"); par.append(f"{int(month):02d}")
    rows = q("SELECT code AS PRODUTO, qty AS QTD, total AS VALOR, COALESCE(NULLIF(line,''), description) AS LINHA FROM ds_vendas WHERE " + " AND ".join(where), par)
    return pd.DataFrame(rows, columns=["PRODUTO", "QTD", "VALOR", "LINHA"])

def overview(months=24):
    """Resumo de vendas (ds_vendas = totais por mês × SKU vindos do servidor): evolução mensal (qtd, valor, nº de SKUs), comparação com o mesmo período do ano anterior,
    participação por LINHA e cobertura do catálogo (quanto do faturamento é de SKUs do catálogo CatalogoAMD)."""
    from queries import q, q1
    from analytics import _has
    if not _has("ds_vendas"): return {"available": False}
    info = q1("SELECT MIN(sale_date) a, MAX(sale_date) b, COUNT(*) n, SUM(CASE WHEN sale_date IS NULL THEN 1 ELSE 0 END) sem_data, SUM(CASE WHEN total IS NULL THEN 1 ELSE 0 END) sem_valor FROM ds_vendas")
    if not info["b"]: return {"available": True, "sem_data": True, "info": info}
    run = q1("SELECT at, note, rows FROM ds_runs WHERE dataset='vendas' AND status='ok' ORDER BY id DESC LIMIT 1") or {}
    mes = q("SELECT substr(sale_date,1,7) m, SUM(qty) q, SUM(total) v, SUM(total_net) net, COUNT(DISTINCT code) skus FROM ds_vendas WHERE upper(COALESCE(line,'')) LIKE '%AMORTECEDOR%' OR line IS NULL GROUP BY 1 ORDER BY 1")
    mes = mes[-int(months):]
    last = info["b"][:7]; y, m = int(last[:4]), int(last[5:7])
    ytd = lambda yy: q1("SELECT COALESCE(SUM(qty),0) q, COALESCE(SUM(total),0) v FROM ds_vendas WHERE substr(sale_date,1,4)=? AND substr(sale_date,6,2)<=? AND (upper(COALESCE(line,'')) LIKE '%AMORTECEDOR%' OR line IS NULL)", (str(yy), f"{m:02d}"))
    a, b = ytd(y), ytd(y - 1)
    lines = q("SELECT COALESCE(NULLIF(trim(line),''),'(sem linha)') linha, SUM(qty) q, SUM(total) v FROM ds_vendas WHERE substr(sale_date,1,4)=? GROUP BY 1 ORDER BY 3 DESC", (str(y),))
    cat = q1("""SELECT COALESCE(SUM(CASE WHEN p.id IS NOT NULL THEN v.total END),0) dentro, COALESCE(SUM(v.total),0) tot, COUNT(DISTINCT CASE WHEN p.id IS NULL THEN v.code END) skus_fora
                FROM ds_vendas v LEFT JOIN products p ON upper(p.perfect_code)=upper(v.code) AND p.catalog_position IS NOT NULL WHERE substr(v.sale_date,1,4)=?""", (str(y),))
    return {"available": True, "ultimo_mes": last, "primeiro_mes": info["a"][:7], "linhas_cache": info["n"], "atualizado_em": run.get("at"), "carga": run.get("note"),
            "meses": [{"mes": r["m"], "qtd": r["q"] or 0, "valor": r["v"] or 0, "valor_liquido": r["net"], "skus": r["skus"]} for r in mes],
            "ytd": {"ano": y, "ate_mes": m, "qtd": a["q"], "valor": a["v"], "qtd_ant": b["q"], "valor_ant": b["v"], "var_valor_pct": round(100 * (a["v"] / b["v"] - 1), 1) if b["v"] else None, "var_qtd_pct": round(100 * (a["q"] / b["q"] - 1), 1) if b["q"] else None},
            "por_linha": lines, "catalogo": {"ano": y, "pct_valor_catalogo": round(100 * cat["dentro"] / cat["tot"], 1) if cat["tot"] else None, "skus_fora": cat["skus_fora"]}}

def payload(year=None, month=None, limit=None):
    from analytics import _has
    from queries import q
    if not _has("ds_vendas"): return {"available": False, "rows": []}
    try: q("SELECT line FROM ds_vendas LIMIT 1")
    except Exception: pass
    df = curva_a(load(year, month)); tot = float(df["VALOR"].sum()); n = {c: int((df["classe"] == c).sum()) for c in "ABC"}
    share = {c: round(float(df.loc[df["classe"] == c, "VALOR"].sum() / tot * 100), 1) if tot else 0 for c in "ABC"}
    years = [r["y"] for r in q("SELECT DISTINCT substr(sale_date,1,4) y FROM ds_vendas WHERE sale_date IS NOT NULL ORDER BY y DESC")]
    rows = df if not limit else df.head(int(limit))
    return {"available": True, "year": year, "month": month, "years": years, "total_valor": tot, "total_qtd": float(df["QTD"].sum()), "skus": len(df), "classes": {"n": n, "valor_pct": share},
            "rows": rows.to_dict("records")}
