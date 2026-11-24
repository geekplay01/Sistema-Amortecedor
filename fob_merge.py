"""FOB — merge da base de produtos com a tabela de preços FOB (Pandas, left join pelo código do produto).

Uso (linha de comando, sem tocar no banco):
    python fob_merge.py PRODUTOS.xlsx fob.xlsx -o produtos_com_fob.xlsx
Uso no sistema: POST /api/fob/import (grava products.fob + tabela fob_prices) ou fob_merge.apply_to_db(caminho).

A planilha FOB (TABELA-PRECO) traz: Linha · Codigo (código do item na planilha: AMD…, 1BP…) · Mínimo (menor FOB, USD) · Melhor Preço («ZS = DES. 2026-11-03»)
· PartNumber (= código PERFECT relativo) · FOB EWIN / FOB ZS / FOB XGM («$ 7,25»). Regras (etapa 22):
  • chave = PartNumber (maiúsculo, sem espaços); PartNumber vazio e Codigo PERFECT (AMD…) → a chave é o próprio Codigo (é o item PERFECT na planilha).
    Sem nenhum dos dois (ex.: 1BP… sem PartNumber): o código PERFECT relativo único que o app conhece (Brands), se esse AMD não tiver linha própria;
    sem relativo a linha não entra (contada em «sem_partnumber»).
  • mesma chave em várias linhas (o item PERFECT e os códigos de outras marcas que apontam para ele) → JUNTA as linhas: cada fornecedor fica com o seu menor preço
    (AMD0637: XGM e ZS estavam na linha «Codigo AMD0637» sem PartNumber).
  • FOB = o MENOR VALOR entre E-WIN, ZS e XGM, e o fornecedor é o dono dele (empate: «ZS / XGM») — mesmo quando o «Mínimo»/«Melhor Preço» da planilha indica outro
    (AMD0907: planilha «ZS 8,24», XGM 7,57 → FOB 7,57 XGM). Origem e data da planilha só quando ela indica esse mesmo fornecedor.
    Sem preço por fornecedor vale o «Mínimo» com o fornecedor da planilha.
O left join mantém TODOS os produtos: quem não tem FOB fica com FOB vazio (nunca some).
"""
import re, sys, argparse
import pandas as pd

OUT_COLS = ["fob", "fob_ewin", "fob_zs", "fob_xgm", "fob_fornecedor", "fob_origem", "fob_data", "fob_cod_fornecedor"]
def _canon(c): return re.sub(r"[^a-z0-9]", "", re.sub(r"[ \s]", "", str(c)).lower().translate(str.maketrans("íáãâéêóôúç", "iaaaeeoouc")))

def money(v):
    """'$ 7,25' → 7.25 · '$ 1.234,50' → 1234.5 · '$ -', '-', vazio → None."""
    if v is None or (isinstance(v, float) and v != v): return None
    if isinstance(v, (int, float)): return float(v)
    t = re.sub(r"[^\d,.\-]", "", str(v).replace(" ", " "))
    if t in ("", "-", ".", ","): return None
    if "," in t and "." in t: t = t.replace(".", "").replace(",", ".")
    elif "," in t: t = t.replace(",", ".")
    try: return float(t)
    except ValueError: return None

FORN = (("E-WIN", "fob_ewin"), ("ZS", "fob_zs"), ("XGM", "fob_xgm"))          # fornecedores com coluna própria na planilha

def read_fob(src, relativo=None):
    """Lê a planilha FOB e devolve (DataFrame com uma linha por código PERFECT, relatório).
    relativo(código) → o código PERFECT relativo ÚNICO no app (Brands: base de marcas, cross e vínculo manual) ou None — usado nas linhas sem PartNumber
    cujo Codigo não é AMD (1BP…), e só se o AMD não tiver linha própria na planilha (etapa 22 · Q3)."""
    raw = pd.read_csv(src, sep=None, engine="python", dtype=object) if str(src).lower().endswith((".csv", ".txt")) else pd.read_excel(src, dtype=object)
    by = {_canon(c): c for c in raw.columns}; need = lambda *n: next((by[_canon(x)] for x in n if _canon(x) in by), None)
    c = {"pn": need("PartNumber", "Part Number", "codigo_perfect"), "min": need("Mínimo", "Minimo", "FOB"), "best": need("Melhor Preço", "Melhor Preco"), "forn": need("Codigo", "Código"),
         "ewin": need("FOB EWIN", "FOB E-WIN"), "zs": need("FOB ZS"), "xgm": need("FOB XGM")}
    if not c["pn"]: raise ValueError("Coluna «PartNumber» (código do produto) não encontrada na planilha FOB. Colunas: " + ", ".join(map(str, raw.columns)))
    s = lambda k: raw[c[k]] if c[k] else pd.Series([None] * len(raw), index=raw.index)
    nb = lambda x: x.str.replace(" ", " ", regex=False)
    txt = lambda k: nb(s(k).astype("object").where(s(k).notna(), "").astype(str)).str.strip().str.upper().replace({"NAN": "", "NONE": ""})
    pn, cod = txt("pn").str.replace(" ", "", regex=False), txt("forn")
    cod_k = cod.str.replace(" ", "", regex=False)
    pelo_codigo = pn.eq("") & cod_k.str.startswith("AMD")      # o próprio item PERFECT na planilha, sem PartNumber
    chave = pn.where(~pelo_codigo, cod_k).copy()
    proprios = set(chave[chave.ne("")])                        # códigos PERFECT com linha própria (PartNumber ou Codigo AMD)
    via_rel = pd.Series(False, index=raw.index)
    if relativo:
        for i in chave.index[chave.eq("") & cod_k.ne("")]:
            r = relativo(cod_k[i])
            r = str(r or '').strip().upper()
            if r and r not in proprios: chave[i] = r; via_rel[i] = True
    d = pd.DataFrame({"codigo": chave, "fob_ewin": s("ewin").map(money), "fob_zs": s("zs").map(money), "fob_xgm": s("xgm").map(money),
                      "fob_cod_fornecedor": cod.where(cod.ne(""), None), "minimo": s("min").map(money)})
    best = nb(s("best").astype("object").where(s("best").notna(), "").astype(str))
    m = best.str.extract(r"^\s*([A-Za-z\-]+)\s*=\s*([A-Za-z]+)\.?\s*(\d{4}-\d{2}-\d{2})?")
    d["pl_forn"] = m[0].str.upper(); d["pl_origem"] = m[1].str.upper(); d["pl_data"] = m[2]
    n0 = len(d); sem = d["codigo"].eq(""); d = d[~sem]
    dup = int(d["codigo"].duplicated().sum())
    juntar = lambda xs: ", ".join(dict.fromkeys(x for x in xs if isinstance(x, str) and x)) or None      # códigos da planilha que levam ao item, o mais barato primeiro
    d = (d.sort_values(["codigo", "minimo"], na_position="last")
          .groupby("codigo", sort=True).agg(fob_ewin=("fob_ewin", "min"), fob_zs=("fob_zs", "min"), fob_xgm=("fob_xgm", "min"), fob_cod_fornecedor=("fob_cod_fornecedor", juntar),
                                            minimo=("minimo", "min"), pl_forn=("pl_forn", "first"), pl_origem=("pl_origem", "first"), pl_data=("pl_data", "first")).reset_index())
    def melhor(r):
        """etapa 22 · Q1/Q7/Q8/Q9: FOB = o menor valor entre os fornecedores e o fornecedor é o dono dele (empate: «ZS / XGM»). Origem e data da planilha só quando
        ela indica esse mesmo fornecedor (senão seriam de outra cotação). Sem preço por fornecedor vale o «Mínimo» com o fornecedor que a planilha indica."""
        vals = {n: r[col] for n, col in FORN if pd.notna(r[col])}
        pf = r["pl_forn"] if isinstance(r["pl_forn"], str) else None
        if not vals: return r["minimo"], pf, r["pl_origem"], r["pl_data"]
        v = min(vals.values()); fs = [n for n, x in vals.items() if abs(x - v) < 1e-9]
        igual = pf in fs
        return v, " / ".join(fs), (r["pl_origem"] if igual else None), (r["pl_data"] if igual else None)
    if len(d):
        d[["fob", "fob_fornecedor", "fob_origem", "fob_data"]] = d.apply(lambda r: pd.Series(melhor(r)), axis=1)
    else:
        for k in ("fob", "fob_fornecedor", "fob_origem", "fob_data"): d[k] = None
    d = d.drop(columns=["minimo", "pl_forn", "pl_origem", "pl_data"])
    d["fob"] = pd.to_numeric(d["fob"], errors="coerce")
    for k in ("fob_fornecedor", "fob_origem", "fob_data"): d[k] = d[k].astype(object).where(d[k].notna(), None)
    return d, {"linhas_fob": n0, "sem_partnumber": int(sem.sum()), "codigo_como_chave": int(pelo_codigo.sum()), "via_relativo": int(via_rel.sum()),
               "partnumber_repetido": dup, "itens_fob": len(d)}

def relativos_do_app():
    """código (normalizado) → código PERFECT relativo, só quando o app conhece exatamente um (Brands: cross, base de marcas, amostras e vínculo manual)."""
    import brands
    mapa = {i["key"]: i["perfect_codes"] for i in brands.universe() if i.get("perfect_codes")}
    def rel(code):
        cs = mapa.get(brands._k(code)) or []
        return cs[0].upper() if len(cs) == 1 else None
    return rel

def merge_fob(products, fob, key="codigo"):
    """LEFT JOIN: todos os produtos + colunas FOB (casadas pelo código do produto, sem espaços/caixa). Devolve (DataFrame, relatório)."""
    p = products.copy(); k = next((c for c in p.columns if _canon(c) in (_canon(key), "perfectcode", "codigoperfect", "codigo")), None)
    if k is None: raise ValueError(f"Coluna de código não encontrada na base de produtos (esperado «{key}»).")
    p["_k"] = p[k].astype("object").where(p[k].notna(), "").astype(str).str.replace(" ", " ", regex=False).str.strip().str.upper()
    p = p.drop(columns=[c for c in OUT_COLS if c in p.columns])
    out = p.merge(fob.rename(columns={"codigo": "_k"}), on="_k", how="left").drop(columns="_k")
    return out, {"produtos": len(p), "com_fob": int(out["fob"].notna().sum()), "sem_fob": int(out["fob"].isna().sum()), "fob_sem_produto": int((~fob["codigo"].isin(set(p["_k"]))).sum())}

def apply_to_db(path):
    """Importa a FOB para o banco: products.fob (menor FOB, USD) e a tabela fob_prices (por fornecedor). Reimportar substitui a versão anterior."""
    import database as db
    db.migrate(); fob, rep = read_fob(path, relativos_do_app()); c = db.conn()
    try:
        prods = pd.read_sql_query("SELECT id, perfect_code FROM products", c)
        merged, rep2 = merge_fob(prods.rename(columns={"perfect_code": "codigo"}), fob)
        c.execute("CREATE TABLE IF NOT EXISTS fob_prices(codigo TEXT PRIMARY KEY, fob REAL, fob_ewin REAL, fob_zs REAL, fob_xgm REAL, fob_fornecedor TEXT, fob_origem TEXT, fob_data TEXT, fob_cod_fornecedor TEXT, loaded_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        c.execute("DELETE FROM fob_prices"); cols = ["codigo"] + OUT_COLS
        c.executemany(f"INSERT INTO fob_prices({','.join(cols)}) VALUES({','.join('?' * len(cols))})", [tuple(None if (isinstance(v, float) and v != v) else v for v in r) for r in fob[cols].itertuples(index=False, name=None)])
        c.execute("UPDATE products SET fob=NULL, fob_supplier=NULL")
        c.executemany("UPDATE products SET fob=?, fob_supplier=? WHERE id=?", [(r.fob, r.fob_fornecedor if isinstance(r.fob_fornecedor, str) else None, int(r.id)) for r in merged[merged["fob"].notna()].itertuples()])
        c.commit()
    finally: c.close()
    return {**rep, **rep2}

def listing(q=None, filtro="", page=1, size=100):
    """Tela FOB: produtos do CATÁLOGO com o FOB importado (US$). filtro: '' todos · 'com' só com FOB · 'sem' só sem FOB.
    Com busca, entram também os itens da tabela FOB que só existem em DES/R-D (fora do catálogo), com des/rd marcados (etapa 22 · 3ª rodada Q3).
    fob_prices.codigo é gravado em maiúsculo e sem espaços (read_fob), então o join usa a chave primária (antes: upper(trim()) dos dois lados, ≈ 1,8 s)."""
    import kinds
    from queries import q as Q, q1
    try: meta = q1("SELECT COUNT(*) n, MAX(loaded_at) at FROM fob_prices")
    except Exception: return {"available": False}
    if not meta or not meta["n"]: return {"available": False}
    J = "LEFT JOIN fob_prices f ON f.codigo=upper(trim(p.perfect_code))"
    F = "f.fob, f.fob_ewin, f.fob_zs, f.fob_xgm, f.fob_fornecedor, f.fob_origem, f.fob_data, f.fob_cod_fornecedor"
    termos = (q or "").split(); p = {f"t{i}": f"%{x}%" for i, x in enumerate(termos)}
    filtro_sql = {"com": ["f.fob IS NOT NULL"], "sem": ["f.fob IS NULL"]}.get(filtro, [])
    w = ["p.catalog_position IS NOT NULL", *filtro_sql, *(f"(p.perfect_code LIKE :t{i} OR p.description LIKE :t{i} OR f.fob_cod_fornecedor LIKE :t{i})" for i in range(len(termos)))]
    sql = f"SELECT p.id, p.perfect_code, p.description, {F}, p.catalog_position pos, 0 des, 0 rd FROM products p {J} WHERE " + " AND ".join(w)
    if termos:
        p.update(kd=kinds.SLUG["des"], kr=kinds.SLUG["rd"])
        we = ["f.codigo NOT IN (SELECT upper(trim(perfect_code)) FROM products WHERE catalog_position IS NOT NULL)", *filtro_sql,
              *(f"(f.codigo LIKE :t{i} OR r.descr LIKE :t{i} OR f.fob_cod_fornecedor LIKE :t{i})" for i in range(len(termos)))]
        sql += (f" UNION ALL SELECT NULL, f.codigo, r.descr, {F}, NULL, r.des, r.rd FROM fob_prices f JOIN (SELECT upper(trim(code)) c, MAX(description) descr,"
                " MAX(suggestion=:kd) des, MAX(suggestion=:kr) rd FROM rd_projects GROUP BY 1) r ON r.c=f.codigo WHERE " + " AND ".join(we))
    size = max(10, min(int(size or 100), 500)); page = max(1, int(page or 1))
    tot = q1(f"SELECT COUNT(*) n FROM ({sql})", p)["n"]
    rows = Q(f"SELECT * FROM ({sql}) ORDER BY (fob IS NULL), (pos IS NULL), pos, perfect_code LIMIT {size} OFFSET {(page - 1) * size}", p)
    for r in rows: r["des"], r["rd"] = bool(r["des"]), bool(r["rd"]); r.pop("pos", None)
    k = q1(f"SELECT COUNT(*) n, SUM(f.fob IS NOT NULL) c, AVG(f.fob) m FROM products p {J} WHERE p.catalog_position IS NOT NULL")
    return {"available": True, "total": tot, "page": page, "size": size, "rows": rows, "summary": {"catalogo": k["n"], "com_fob": int(k["c"] or 0), "sem_fob": k["n"] - int(k["c"] or 0), "fob_medio": round(k["m"], 2) if k["m"] else None,
            "itens_fob": meta["n"], "carregado_em": meta["at"], "fob_sem_produto": q1("SELECT COUNT(*) n FROM fob_prices WHERE codigo NOT IN (SELECT upper(trim(perfect_code)) FROM products)")["n"]}}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Left join: produtos x FOB"); ap.add_argument("produtos"); ap.add_argument("fob"); ap.add_argument("-o", "--saida", default="produtos_com_fob.xlsx"); ap.add_argument("--chave", default="codigo")
    a = ap.parse_args(); prod = pd.read_csv(a.produtos, dtype=object) if a.produtos.lower().endswith(".csv") else pd.read_excel(a.produtos, dtype=object)
    fobdf, r1 = read_fob(a.fob); res, r2 = merge_fob(prod, fobdf, a.chave); res.to_excel(a.saida, index=False); print({**r1, **r2}, "->", a.saida)
