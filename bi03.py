"""BI03 = cadastro de produtos do Protheus (planilha «003(dd-mm).xls», ~95 MB; etapa 17 · Q15/Q25/Q30).
  • Entra por Atualização de dados e SUBSTITUI a carga anterior. Guarda só os amortecedores acabados: Tipo PA com «Desc. Linha» AMORTECEDOR ou
    AMORTECEDOR LINHA PESADA (os MP- são matéria-prima) e só as colunas usadas: código, linha, alíquota de IPI, peso líquido e código de barras.
  • Peso líquido e código de barras do BI03 PREVALECEM sobre os do CatalogoAMD (products.weight_kg / products.ean); o valor da planilha do catálogo
    fica em products.cat_weight_kg / cat_ean e as diferenças aparecem em Anomalias («Peso e EAN: catálogo × BI03»).
  • IPI: vale o do servidor (DESENVOLVIMENTO_PRODUTOS); o do BI03 só para quem não tem linha no servidor (`ipi`).
  • «Pendente cadastro Protheus» (Anomalias): DES/R-D em andamento que não estão no BI03 como PA."""
import os, re, unicodedata, warnings
import pandas as pd
from queries import q

TABLE = """CREATE TABLE IF NOT EXISTS bi03(code TEXT PRIMARY KEY, linha TEXT, ipi REAL, peso REAL, ean TEXT, source_file TEXT, loaded_at TEXT DEFAULT CURRENT_TIMESTAMP)"""
LABEL = "Cadastro Protheus (BI03)"
LINHAS = ("AMORTECEDOR", "AMORTECEDOR LINHA PESADA")
COLS = {"codigo": "code", "tipo": "tipo", "desclinha": "linha", "aliqipi": "ipi", "pesoliquido": "peso", "codbarras": "ean"}      # cabeçalho sem acento/pontuação → campo

def _canon(s): return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower())
def is_file(name):
    """«003(16-11).xls», «003 (16-11).xls», «BI03…», «BI003…» (cópia do navegador «(1)» também)."""
    n = os.path.splitext(os.path.basename(str(name or "")))[0].strip().upper()
    return bool(re.match(r"^0*03\s*\(\d{1,2}[-_.]\d{1,2}\)", n) or re.match(r"^BI0*3\b", n.replace("_", " ").replace("-", " ")))

def ensure(conn=None):
    if conn is not None: conn.execute(TABLE); return
    import database as db
    with db.session() as c: c.execute(TABLE)

_CACHE = {}
def read(path):
    """DataFrame (code, linha, ipi, peso, ean) só com amortecedor acabado. Leitura ~20 s: fica em memória enquanto o arquivo não muda (Verificar → Aplicar lê uma vez)."""
    st = os.stat(path); key = (os.path.abspath(path), st.st_size, st.st_mtime)
    if key in _CACHE: return _CACHE[key].copy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = pd.read_excel(path, dtype=str, engine="xlrd" if path.lower().endswith(".xls") else None, usecols=lambda c: _canon(c) in COLS)
    df.columns = [COLS[_canon(c)] for c in df.columns]
    falta = set(COLS.values()) - set(df.columns)
    if falta: raise ValueError("Planilha sem as colunas do cadastro de produtos do Protheus: " + ", ".join(k for k, v in COLS.items() if v in falta) + ".")
    for c in df.columns: df[c] = df[c].map(lambda v: re.sub(r"\s+", " ", str(v)).strip().upper() if isinstance(v, str) and v.strip() not in ("", "nan") else None)
    df = df[(df["tipo"] == "PA") & df["linha"].isin(LINHAS) & df["code"].notna()].drop_duplicates("code").copy()
    for c in ("ipi", "peso"): df[c] = pd.to_numeric(df[c].str.replace(",", "."), errors="coerce")
    df["peso"] = df["peso"].where(df["peso"] > 0)                                  # 0 no Protheus = não informado
    df["ean"] = df["ean"].map(lambda v: re.sub(r"\.0$", "", v) if isinstance(v, str) and v != "0" else None)       # pandas 3: vazio vira NaN (float), não None
    out = df[["code", "linha", "ipi", "peso", "ean"]].astype(object).where(df[["code", "linha", "ipi", "peso", "ean"]].notna(), None)
    _CACHE.clear(); _CACHE[key] = out
    return out.copy()

def apply(conn):
    """Peso e EAN do BI03 nos produtos (prevalecem) e fecha as pendências «Campo ausente» que o BI03 resolveu. → (pesos, eans) alterados."""
    n_peso = conn.execute("""UPDATE products SET weight_kg=(SELECT b.peso FROM bi03 b WHERE b.code=products.perfect_code), updated_at=CURRENT_TIMESTAMP
        WHERE EXISTS(SELECT 1 FROM bi03 b WHERE b.code=products.perfect_code AND b.peso IS NOT NULL AND (products.weight_kg IS NULL OR abs(products.weight_kg-b.peso)>0.0005))""").rowcount
    n_ean = conn.execute("""UPDATE products SET ean=(SELECT b.ean FROM bi03 b WHERE b.code=products.perfect_code), updated_at=CURRENT_TIMESTAMP
        WHERE EXISTS(SELECT 1 FROM bi03 b WHERE b.code=products.perfect_code AND b.ean IS NOT NULL AND coalesce(products.ean,'')<>b.ean)""").rowcount
    conn.execute("""UPDATE pendencies SET status='resolvida' WHERE kind='campo_ausente' AND status='aberta' AND (
        (field='peso' AND product_id IN (SELECT id FROM products WHERE weight_kg IS NOT NULL)) OR (field='EAN' AND product_id IN (SELECT id FROM products WHERE ean IS NOT NULL)))""")
    return n_peso, n_ean

def values(conn):
    """{código: (peso, ean)} do BI03 já carregado — o CatalogoAMD usa para não sobrescrever o que o BI03 informa."""
    try: return {r[0]: (r[1], r[2]) for r in conn.execute("SELECT code, peso, ean FROM bi03")}
    except Exception: return {}

def load(path, name, confirm, conn):
    """Substitui a carga anterior e aplica peso/EAN. Na verificação a transação é desfeita por quem chamou (updater.run). → resultado no formato do updater."""
    ensure(conn); df = read(path)
    old = {r[0]: (r[1], r[2], r[3]) for r in conn.execute("SELECT code, ipi, peso, ean FROM bi03")}
    new = {r[0]: (r[2], r[3], r[4]) for r in df.itertuples(index=False, name=None)}
    n_new = len(new.keys() - old.keys()); n_upd = sum(1 for k in new.keys() & old.keys() if new[k] != old[k]); n_gone = len(old.keys() - new.keys())
    conn.execute("DELETE FROM bi03")
    conn.executemany("INSERT INTO bi03(code,linha,ipi,peso,ean,source_file) VALUES(?,?,?,?,?,?)", [(*r, name) for r in df.itertuples(index=False, name=None)])
    n_peso, n_ean = apply(conn)
    cat = conn.execute("SELECT COUNT(*) FROM products p JOIN bi03 b ON b.code=p.perfect_code WHERE p.catalog_position IS NOT NULL").fetchone()[0]
    msgs = [f"{len(df)} amortecedor(es) acabado(s) (PA) no cadastro do Protheus; {cat} do catálogo.",
            f"Peso líquido do BI03 gravado em {n_peso} produto(s) e código de barras em {n_ean} (o BI03 prevalece sobre o CatalogoAMD; diferenças em Anomalias)."]
    if n_gone: msgs.append(f"{n_gone} código(s) da carga anterior não estão nesta planilha e saem.")
    return {"label": LABEL, "rows": len(df), "counts": {"new": n_new, "updated": n_upd, "present": len(new) - n_new - n_upd}, "messages": msgs}

def available():
    try: return bool(q("SELECT 1 FROM bi03 LIMIT 1"))
    except Exception: return False

def ipi(code):
    """IPI do item: servidor (DESENVOLVIMENTO_PRODUTOS, campo IPI) primeiro; BI03 só para quem não tem linha no servidor (decisão Q25)."""
    try:
        r = q("SELECT json_extract(extra,'$.IPI') v FROM rd_projects WHERE upper(code)=upper(?) AND json_extract(extra,'$.IPI') IS NOT NULL LIMIT 1", (code,))
        if r: return float(r[0]["v"])
        r = q("SELECT ipi v FROM bi03 WHERE code=upper(?)", (code,)); return r[0]["v"] if r else None
    except Exception: return None
