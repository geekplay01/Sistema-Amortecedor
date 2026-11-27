"""Vendas FATURADAS — CURVA A (ABC) de amortecedores (Pandas).

Regras (definidas pelo usuário):
  1. agrupa pelo código do PRODUTO (SKU)
  2. soma a quantidade (QTD) e o valor faturado (VALOR)
  3. ordena do MAIOR para o MENOR valor faturado
  4. base = vendas faturadas (VALOR_TOTAL_CIPI). Universo padrão = o do BI: LINHA = «AMORTECEDOR» exata (etapa 16 · C1/Q10); linha pesada e kit só pelo seletor `linhas`.
Além do pedido: participação %, % acumulado e classe A (até 80% do faturamento) / B (até 95%) / C — a «Curva A» é a classe A.
"""
import re, unicodedata, datetime
import pandas as pd

CUT_A, CUT_B = 80.0, 95.0
LINHAS = {"amortecedor": "AMORTECEDOR", "pesada": "AMORTECEDOR LINHA PESADA", "kit": "KIT DE AMORTECEDOR"}       # seletor de linha (chave na URL → LINHA do servidor)
def linhas_sel(s=None):
    """«amortecedor,pesada» → ['amortecedor', 'pesada'] (só chaves válidas; vazio = padrão do BI: só amortecedor)."""
    sel = [x for x in re.split(r"[,|\s]+", (s if isinstance(s, str) else ",".join(s or [])).lower()) if x in LINHAS]
    return sel or ["amortecedor"]
def linha_sql(s=None, col="line", desc="description"):
    """Condição SQL do universo de vendas (LINHA exata, sem diferenciar caixa/espaços) → (sql, params).
    LINHA vazia (servidor antigo): a descrição decide — KIT… → kit · «LINHA PESADA» → linha pesada · «AMORTECEDOR» → amortecedor."""
    sel = linhas_sel(s)
    expr = (f"CASE WHEN trim(coalesce({col},''))<>'' THEN upper(trim({col})) WHEN upper(coalesce({desc},'')) LIKE '%KIT%' THEN 'KIT DE AMORTECEDOR' "
            f"WHEN upper(coalesce({desc},'')) LIKE '%LINHA PESADA%' THEN 'AMORTECEDOR LINHA PESADA' WHEN upper(coalesce({desc},'')) LIKE '%AMORTECEDOR%' THEN 'AMORTECEDOR' END")
    return f"{expr} IN ({','.join('?' * len(sel))})", [LINHAS[k] for k in sel]
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

def load(year=None, month=None, linhas=None):
    """Vendas faturadas do cache local (ds_vendas) — filtra ano/mês (como os filtros Ano/Mês do BI) e o universo de linhas (`linha_sql`)."""
    from queries import q
    ls, lp = linha_sql(linhas); where, par = ["code IS NOT NULL", ls], list(lp)
    if year: where.append("substr(sale_date,1,4)=?"); par.append(str(int(year)))
    if month: where.append("substr(sale_date,6,2)=?"); par.append(f"{int(month):02d}")
    rows = q("SELECT code AS PRODUTO, qty AS QTD, total AS VALOR, COALESCE(NULLIF(line,''), description) AS LINHA FROM ds_vendas WHERE " + " AND ".join(where), par)
    return pd.DataFrame(rows, columns=["PRODUTO", "QTD", "VALOR", "LINHA"])

def overview(months=24, linhas=None, today=None):
    """Resumo de vendas (ds_vendas = totais por mês × SKU vindos do servidor) no universo escolhido (`linhas`; padrão = BI): evolução mensal (qtd, valor, nº de SKUs),
    resumo do Q10 — último mês FECHADO · mês atual PARCIAL · acumulado do ano (com o mesmo período do ano anterior) —, participação por LINHA (todas, para referência)
    e cobertura do catálogo (quanto do faturamento é de SKUs do catálogo CatalogoAMD)."""
    from queries import q, q1
    from analytics import _has
    if not _has("ds_vendas"): return {"available": False}
    info = q1("SELECT MIN(sale_date) a, MAX(sale_date) b, COUNT(*) n, SUM(CASE WHEN sale_date IS NULL THEN 1 ELSE 0 END) sem_data, SUM(CASE WHEN total IS NULL THEN 1 ELSE 0 END) sem_valor FROM ds_vendas")
    if not info["b"]: return {"available": True, "sem_data": True, "info": info}
    run = q1("SELECT at, note, rows FROM ds_runs WHERE dataset='vendas' AND status='ok' ORDER BY id DESC LIMIT 1") or {}
    ls, lp = linha_sql(linhas)
    mes = q(f"SELECT substr(sale_date,1,7) m, SUM(qty) q, SUM(total) v, SUM(total_net) net, COUNT(DISTINCT code) skus FROM ds_vendas WHERE {ls} GROUP BY 1 ORDER BY 1", lp)
    mes = mes[-int(months):]
    last = info["b"][:7]; hoje = today or datetime.date.today(); atual = f"{hoje.year}-{hoje.month:02d}"
    fech = f"{hoje.year - (hoje.month == 1)}-{(hoje.month - 2) % 12 + 1:02d}"          # mês anterior ao atual
    y, m = hoje.year, hoje.month
    one = lambda mm: q1(f"SELECT COALESCE(SUM(qty),0) q, COALESCE(SUM(total),0) v, COUNT(DISTINCT code) skus FROM ds_vendas WHERE substr(sale_date,1,7)=? AND {ls}", [mm, *lp])
    ytd = lambda yy: q1(f"SELECT COALESCE(SUM(qty),0) q, COALESCE(SUM(total),0) v FROM ds_vendas WHERE substr(sale_date,1,4)=? AND substr(sale_date,6,2)<=? AND {ls}", [str(yy), f"{m:02d}", *lp])
    a, b = ytd(y), ytd(y - 1); f1, p1 = one(fech), one(atual)
    resumo = {"fechado": {"mes": fech, "qtd": f1["q"], "valor": f1["v"], "skus": f1["skus"]},
              "parcial": {"mes": atual, "qtd": p1["q"], "valor": p1["v"], "skus": p1["skus"], "tem_dados": last >= atual},
              "ytd": {"ano": y, "ate_mes": m, "qtd": a["q"], "valor": a["v"], "qtd_ant": b["q"], "valor_ant": b["v"], "var_valor_pct": round(100 * (a["v"] / b["v"] - 1), 1) if b["v"] else None}}
    lines = q("SELECT COALESCE(NULLIF(trim(line),''),'(sem linha)') linha, SUM(qty) q, SUM(total) v FROM ds_vendas WHERE substr(sale_date,1,4)=? GROUP BY 1 ORDER BY 3 DESC", (str(y),))
    no_cat = {r["c"] for r in q("SELECT upper(perfect_code) c FROM products WHERE catalog_position IS NOT NULL")}      # em Python: o JOIN com upper() não usava índice (4 s)
    vv = q("SELECT upper(code) c, COALESCE(SUM(total),0) v FROM ds_vendas WHERE substr(sale_date,1,4)=? GROUP BY 1", (str(y),))
    cat = {"dentro": sum(r["v"] for r in vv if r["c"] in no_cat), "tot": sum(r["v"] for r in vv), "skus_fora": sum(1 for r in vv if r["c"] and r["c"] not in no_cat)}
    return {"available": True, "ultimo_mes": last, "primeiro_mes": info["a"][:7], "linhas_cache": info["n"], "atualizado_em": run.get("at"), "carga": run.get("note"), "resumo": resumo, "linhas_sel": linhas_sel(linhas),
            "meses": [{"mes": r["m"], "qtd": r["q"] or 0, "valor": r["v"] or 0, "valor_liquido": r["net"], "skus": r["skus"]} for r in mes],
            "ytd": {"ano": y, "ate_mes": m, "qtd": a["q"], "valor": a["v"], "qtd_ant": b["q"], "valor_ant": b["v"], "var_valor_pct": round(100 * (a["v"] / b["v"] - 1), 1) if b["v"] else None, "var_qtd_pct": round(100 * (a["q"] / b["q"] - 1), 1) if b["q"] else None},
            "por_linha": lines, "catalogo": {"ano": y, "pct_valor_catalogo": round(100 * cat["dentro"] / cat["tot"], 1) if cat["tot"] else None, "skus_fora": cat["skus_fora"]}}

_CLS = {}
def classes(today=None):
    """{código sem pontuação: 'A'|'B'|'C'} — curva ABC de vendas dos últimos 12 meses FECHADOS no universo do BI (padrão da tela Vendas). Usada na página do item
    e na Cobertura de concorrentes (etapa 17). Fica em memória até a próxima sincronização de vendas ou a virada do dia."""
    from analytics import _has
    from queries import q, q1
    if not _has("ds_vendas"): return {}
    hoje = today or datetime.date.today(); run = (q1("SELECT MAX(id) i FROM ds_runs WHERE dataset='vendas'") or {}).get("i"); key = (hoje.isoformat(), run)
    if _CLS.get("k") != key:
        a = hoje.replace(day=1); de = f"{a.year - 1}-{a.month:02d}-01"; ls, lp = linha_sql(None)
        rows = q(f"SELECT code, SUM(total) v FROM ds_vendas WHERE sale_date>=? AND sale_date<? AND {ls} GROUP BY code", [de, a.isoformat(), *lp])
        by = {}
        for r in rows:
            k = re.sub(r"[^A-Z0-9]", "", str(r["code"] or "").upper())
            if k: by[k] = by.get(k, 0) + (r["v"] or 0)
        tot = sum(v for v in by.values() if v > 0) or 1; acc = 0; out = {}
        for k, v in sorted(((k, v) for k, v in by.items() if v > 0), key=lambda x: -x[1]):
            out[k] = "A" if acc / tot < CUT_A / 100 else "B" if acc / tot < CUT_B / 100 else "C"; acc += v
        _CLS.update(k=key, v=out)
    return _CLS["v"]

def _uf_rows(year=None, month=None, linhas=None, uf=None):
    """ds_vendas_uf_cod (mês × UF × código × linha, servidor) no período e no universo de linhas da tela Vendas → [{uf, code, q, v}]."""
    from queries import q
    ls, lp = linha_sql(linhas, desc="''"); where, par = ["code IS NOT NULL", "trim(coalesce(uf,''))<>''", ls], list(lp)
    if year: where.append("substr(sale_date,1,4)=?"); par.append(str(int(year)))
    if month: where.append("substr(sale_date,6,2)=?"); par.append(f"{int(month):02d}")
    if uf: where.append("upper(trim(uf))=?"); par.append(str(uf).strip().upper())
    return q("SELECT upper(trim(uf)) uf, upper(code) code, SUM(qty) q, SUM(total) v FROM ds_vendas_uf_cod WHERE " + " AND ".join(where) + " GROUP BY 1, 2", par)

def _descricoes(codes):
    from queries import q
    codes = list(codes)
    if not codes: return {}
    out = {}
    for i in range(0, len(codes), 800):
        part = codes[i:i + 800]
        out.update({r["c"]: r["d"] for r in q(f"SELECT upper(perfect_code) c, description d FROM products WHERE upper(perfect_code) IN ({','.join('?' * len(part))})", part)})
    return out

def por_uf(year=None, month=None, linhas=None, top=10):
    """Update 8 · mapa da tela Vendas: peças e R$ por UF no período e nas linhas da tela, com os `top` códigos mais vendidos (em peças) de cada UF."""
    from analytics import _has
    from queries import q1
    if not _has("ds_vendas_uf_cod"): return {"available": False}
    rows = _uf_rows(year, month, linhas)
    if not rows:
        vazio = not (q1("SELECT 1 x FROM ds_vendas_uf_cod LIMIT 1") or {}).get("x")
        return {"available": True, "sem_dados": vazio, "por_uf": [], "linhas_sel": linhas_sel(linhas)}
    by = {}
    for r in rows:
        a = by.setdefault(r["uf"], {"uf": r["uf"], "pecas": 0.0, "valor": 0.0, "cods": []}); a["pecas"] += r["q"] or 0; a["valor"] += r["v"] or 0; a["cods"].append(r)
    tops = {u: sorted(a["cods"], key=lambda x: (-(x["q"] or 0), x["code"]))[:top] for u, a in by.items()}
    desc = _descricoes({x["code"] for t in tops.values() for x in t})
    out = []
    for u, a in sorted(by.items(), key=lambda kv: -kv[1]["pecas"]):
        out.append({"uf": u, "pecas": a["pecas"], "valor": a["valor"], "n_codigos": len(a["cods"]),
                    "top": [{"code": x["code"], "desc": desc.get(x["code"]), "pecas": x["q"] or 0, "valor": x["v"] or 0, "pct": round(100 * (x["q"] or 0) / a["pecas"], 1) if a["pecas"] else 0} for x in tops[u]]})
    per = q1("SELECT MIN(sale_date) a, MAX(sale_date) b FROM ds_vendas_uf_cod") or {}
    return {"available": True, "por_uf": out, "linhas_sel": linhas_sel(linhas), "primeiro_mes": (per.get("a") or "")[:7], "ultimo_mes": (per.get("b") or "")[:7]}

def uf_codigos(uf, year=None, month=None, linhas=None):
    """Todos os códigos vendidos numa UF (Excel do estado), do maior para o menor em peças."""
    rows = sorted(_uf_rows(year, month, linhas, uf), key=lambda x: (-(x["q"] or 0), x["code"])); tot = sum(r["q"] or 0 for r in rows); desc = _descricoes({r["code"] for r in rows})
    return [{"code": r["code"], "desc": desc.get(r["code"]), "pecas": r["q"] or 0, "valor": r["v"] or 0, "pct": round(100 * (r["q"] or 0) / tot, 2) if tot else 0} for r in rows]

def payload(year=None, month=None, limit=None, linhas=None):
    from analytics import _has
    from queries import q
    if not _has("ds_vendas"): return {"available": False, "rows": []}
    df = curva_a(load(year, month, linhas), linha=None); tot = float(df["VALOR"].sum()); n = {c: int((df["classe"] == c).sum()) for c in "ABC"}
    share = {c: round(float(df.loc[df["classe"] == c, "VALOR"].sum() / tot * 100), 1) if tot else 0 for c in "ABC"}
    years = [r["y"] for r in q("SELECT DISTINCT substr(sale_date,1,4) y FROM ds_vendas WHERE sale_date IS NOT NULL ORDER BY y DESC")]
    rows = df if not limit else df.head(int(limit))
    return {"available": True, "year": year, "month": month, "years": years, "linhas_sel": linhas_sel(linhas), "total_valor": tot, "total_qtd": float(df["QTD"].sum()), "skus": len(df), "classes": {"n": n, "valor_pct": share},
            "rows": rows.to_dict("records")}
