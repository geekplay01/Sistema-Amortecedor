"""FOB — merge da base de produtos com a tabela de preços FOB (Pandas, left join pelo código do produto).

Uso (linha de comando, sem tocar no banco):
    python fob_merge.py PRODUTOS.xlsx fob.xlsx -o produtos_com_fob.xlsx
Uso no sistema: POST /api/fob/import (grava products.fob + tabela fob_prices) ou fob_merge.apply_to_db(caminho).

A planilha FOB (TABELA-PRECO) traz: Linha · Codigo (código do FORNECEDOR) · Mínimo (menor FOB, USD) · Melhor Preço («ZS = DES. 2026-11-03») · PartNumber (= código PERFECT, a CHAVE)
· FOB EWIN / FOB ZS / FOB XGM («$ 7,25»). Regras: chave = PartNumber (maiúsculo, sem espaços); linhas sem PartNumber não entram (contadas); PartNumber repetido (vários códigos de
fornecedor para o mesmo item) fica com o MENOR FOB. O left join mantém TODOS os produtos: quem não tem FOB fica com FOB vazio (nunca some).
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

def read_fob(src):
    """Lê a planilha FOB e devolve (DataFrame com uma linha por PartNumber, relatório)."""
    raw = pd.read_csv(src, sep=None, engine="python", dtype=object) if str(src).lower().endswith((".csv", ".txt")) else pd.read_excel(src, dtype=object)
    by = {_canon(c): c for c in raw.columns}; need = lambda *n: next((by[_canon(x)] for x in n if _canon(x) in by), None)
    c = {"pn": need("PartNumber", "Part Number", "codigo_perfect"), "min": need("Mínimo", "Minimo", "FOB"), "best": need("Melhor Preço", "Melhor Preco"), "forn": need("Codigo", "Código"),
         "ewin": need("FOB EWIN", "FOB E-WIN"), "zs": need("FOB ZS"), "xgm": need("FOB XGM")}
    if not c["pn"]: raise ValueError("Coluna «PartNumber» (código do produto) não encontrada na planilha FOB. Colunas: " + ", ".join(map(str, raw.columns)))
    s = lambda k: raw[c[k]] if c[k] else pd.Series([None] * len(raw))
    d = pd.DataFrame({"codigo": s("pn").astype("object").where(s("pn").notna(), "").astype(str).str.replace(" ", " ", regex=False).str.strip().str.upper(),
                      "fob_ewin": s("ewin").map(money), "fob_zs": s("zs").map(money), "fob_xgm": s("xgm").map(money), "fob_cod_fornecedor": s("forn").astype("object").where(s("forn").notna(), None)})
    d["fob_cod_fornecedor"] = d["fob_cod_fornecedor"].map(lambda v: None if v is None else str(v).replace(" ", " ").strip())
    d["fob"] = s("min").map(money); alt = d[["fob_ewin", "fob_zs", "fob_xgm"]].min(axis=1, skipna=True); d["fob"] = d["fob"].where(d["fob"].notna(), alt)
    best = s("best").astype("object").where(s("best").notna(), "").astype(str).str.replace(" ", " ", regex=False)
    m = best.str.extract(r"^\s*([A-Za-z\-]+)\s*=\s*([A-Za-z]+)\.?\s*(\d{4}-\d{2}-\d{2})?")
    d["fob_fornecedor"] = m[0].str.upper(); d["fob_origem"] = m[1].str.upper(); d["fob_data"] = m[2]
    n0 = len(d); no_pn = d["codigo"].isin(["", "NAN", "NONE"]); d = d[~no_pn]
    dup = int(d["codigo"].duplicated().sum()); d = d.sort_values(["codigo", "fob"], na_position="last").drop_duplicates("codigo", keep="first").reset_index(drop=True)
    return d, {"linhas_fob": n0, "sem_partnumber": int(no_pn.sum()), "partnumber_repetido": dup, "itens_fob": len(d)}

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
    fob, rep = read_fob(path); db.migrate(); c = db.conn()
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
    """Tela FOB: produtos do CATÁLOGO com o FOB importado (US$). filtro: '' todos · 'com' só com FOB · 'sem' só sem FOB."""
    from queries import q as Q, q1
    try: meta = q1("SELECT COUNT(*) n, MAX(loaded_at) at FROM fob_prices")
    except Exception: return {"available": False}
    if not meta or not meta["n"]: return {"available": False}
    w, p = ["p.catalog_position IS NOT NULL"], {}
    if filtro == "com": w.append("f.fob IS NOT NULL")
    elif filtro == "sem": w.append("f.fob IS NULL")
    for i, t in enumerate((q or "").split()): w.append(f"(p.perfect_code LIKE :t{i} OR p.description LIKE :t{i} OR f.fob_cod_fornecedor LIKE :t{i})"); p[f"t{i}"] = f"%{t}%"
    size = max(10, min(int(size or 100), 500)); page = max(1, int(page or 1)); W = " AND ".join(w)
    base = "FROM products p LEFT JOIN fob_prices f ON upper(trim(f.codigo))=upper(trim(p.perfect_code)) WHERE " + W
    tot = q1("SELECT COUNT(*) n " + base, p)["n"]
    rows = Q("SELECT p.id, p.perfect_code, p.description, f.fob, f.fob_ewin, f.fob_zs, f.fob_xgm, f.fob_fornecedor, f.fob_origem, f.fob_data, f.fob_cod_fornecedor " + base + f" ORDER BY (f.fob IS NULL), p.catalog_position LIMIT {size} OFFSET {(page - 1) * size}", p)
    k = q1("SELECT COUNT(*) n, SUM(f.fob IS NOT NULL) c, AVG(f.fob) m FROM products p LEFT JOIN fob_prices f ON upper(trim(f.codigo))=upper(trim(p.perfect_code)) WHERE p.catalog_position IS NOT NULL")
    return {"available": True, "total": tot, "page": page, "size": size, "rows": rows, "summary": {"catalogo": k["n"], "com_fob": int(k["c"] or 0), "sem_fob": k["n"] - int(k["c"] or 0), "fob_medio": round(k["m"], 2) if k["m"] else None,
            "itens_fob": meta["n"], "carregado_em": meta["at"], "fob_sem_produto": q1("SELECT COUNT(*) n FROM fob_prices f WHERE NOT EXISTS(SELECT 1 FROM products p WHERE upper(trim(p.perfect_code))=upper(trim(f.codigo)))")["n"]}}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Left join: produtos x FOB"); ap.add_argument("produtos"); ap.add_argument("fob"); ap.add_argument("-o", "--saida", default="produtos_com_fob.xlsx"); ap.add_argument("--chave", default="codigo")
    a = ap.parse_args(); prod = pd.read_csv(a.produtos, dtype=object) if a.produtos.lower().endswith(".csv") else pd.read_excel(a.produtos, dtype=object)
    fobdf, r1 = read_fob(a.fob); res, r2 = merge_fob(prod, fobdf, a.chave); res.to_excel(a.saida, index=False); print({**r1, **r2}, "->", a.saida)
