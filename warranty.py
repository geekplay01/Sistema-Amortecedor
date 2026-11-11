"""Módulo GARANTIA — lê a planilha (Excel/CSV) e devolve uma lista LIMPA com apenas: codigo, defeito (relatado) e quantidade.
Colunas desnecessárias (Valor C_ST, Cliente, Fabricante…) são descartadas já na leitura (usecols). Código e defeito saem sem espaços (inclusive NBSP) e em MAIÚSCULAS;
linhas sem código, sem quantidade válida (> 0) e a linha «Total» do fim da planilha são descartadas e CONTADAS (nada some em silêncio). Defeito vazio vira «NÃO INFORMADO»."""
import io, os, re, unicodedata
import pandas as pd

KEEP = {"codigo": ("codigo", "cod", "cod_produto", "produto", "sku"), "defeito": ("defeito", "defeito_relatado", "motivo", "problema"), "quantidade": ("qtd", "qtde", "quantidade", "qty")}
NO_DEFECT = "NÃO INFORMADO"
def _canon(c): return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", str(c)).encode("ascii", "ignore").decode().lower())

def _read(src, name=""):
    """Aceita caminho ou arquivo em memória/stream. .csv/.txt → separador e codificação detectados; demais → Excel (1ª planilha)."""
    ext = os.path.splitext(name or (src if isinstance(src, str) else ""))[1].lower()
    raw = src.read() if hasattr(src, "read") else None
    if ext in (".csv", ".txt"):
        data = raw if raw is not None else open(src, "rb").read()
        for enc in ("utf-8-sig", "cp1252", "latin-1"):
            try: return pd.read_csv(io.BytesIO(data), sep=None, engine="python", encoding=enc, dtype=object)
            except UnicodeDecodeError: continue
        raise ValueError("Não foi possível ler o CSV (codificação desconhecida).")
    return pd.read_excel(io.BytesIO(raw) if raw is not None else src, dtype=object)

def parse(src, name=""):
    """→ {'rows': [{codigo, defeito, quantidade}], 'lidas', 'validas', 'descartadas': {...}, 'colunas_removidas': [...]}"""
    try: raw = _read(src, name)
    except ValueError: raise
    except Exception as e: raise ValueError(f"Arquivo ilegível ({e.__class__.__name__}). Envie .xlsx, .xls ou .csv.")
    by = {_canon(c): c for c in raw.columns}; pick = {}
    for std, names in KEEP.items():
        col = next((by[_canon(n)] for n in names if _canon(n) in by), None)
        if col is None and std != "defeito": raise ValueError(f"Coluna «{std}» não encontrada. Colunas lidas: {', '.join(map(str, raw.columns))}")
        pick[std] = col
    removed = [str(c) for c in raw.columns if c not in pick.values()]
    clean = lambda s: s.astype("object").where(s.notna(), "").astype(str).str.replace(" ", " ", regex=False).str.replace(r"\s+", " ", regex=True).str.strip().str.upper()
    d = pd.DataFrame({"codigo": clean(raw[pick["codigo"]]), "defeito": clean(raw[pick["defeito"]]) if pick["defeito"] else "",
                      "quantidade": pd.to_numeric(raw[pick["quantidade"]].astype(str).str.replace(",", ".", regex=False), errors="coerce")})
    n0 = len(d); no_code = d["codigo"].isin(["", "NAN", "NONE"]); no_qty = d["quantidade"].isna() | (d["quantidade"] <= 0)
    is_total = d["codigo"].str.fullmatch(r"(SUB)?TOTAL(IS)?( GERAL)?|SOMA|=.*", na=False)      # a linha «Total» (=SOMA) do fim da planilha NÃO é um código: contar duas vezes dobraria a garantia
    no_code = no_code & ~is_total; no_qty = no_qty & ~is_total
    d = d[~no_code & ~no_qty & ~is_total].copy(); d["defeito"] = d["defeito"].replace({"": NO_DEFECT, "NAN": NO_DEFECT, "NONE": NO_DEFECT})
    d["quantidade"] = d["quantidade"].map(lambda v: int(v) if float(v).is_integer() else float(v))
    return {"rows": d.to_dict("records"), "lidas": n0, "validas": len(d), "descartadas": {"sem_codigo": int(no_code.sum()), "sem_quantidade": int((~no_code & no_qty).sum()), "linha_de_total": int(is_total.sum())}, "colunas_removidas": removed}

# ───────── persistência + resumo (alimenta a tela Garantia) ─────────
def save(rows, filename=None):
    import database as db
    c = db.conn()
    try:
        c.execute("CREATE TABLE IF NOT EXISTS warranty(codigo TEXT NOT NULL, defeito TEXT, quantidade REAL NOT NULL)"); c.execute("CREATE INDEX IF NOT EXISTS ix_war_code ON warranty(codigo)")
        c.execute("CREATE TABLE IF NOT EXISTS warranty_meta(id INTEGER PRIMARY KEY CHECK(id=1), filename TEXT, rows INTEGER, loaded_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        c.execute("DELETE FROM warranty"); c.executemany("INSERT INTO warranty VALUES(?,?,?)", [(r["codigo"], r["defeito"], r["quantidade"]) for r in rows])
        c.execute("INSERT INTO warranty_meta(id,filename,rows) VALUES(1,?,?) ON CONFLICT(id) DO UPDATE SET filename=excluded.filename, rows=excluded.rows, loaded_at=CURRENT_TIMESTAMP", (filename, len(rows))); c.commit()
    finally: c.close()

def _source():
    """Origem dos dados: o SERVIDOR (view ANALITICO_GARANTIA_DEVOLUCAO, cache ds_garantia) quando já sincronizou; senão a planilha enviada. → (subconsulta, meta) ou (None, None)."""
    from queries import q1
    try:
        n = q1("SELECT COUNT(*) n FROM ds_garantia")["n"]
        if n:
            run = q1("SELECT object, at FROM ds_runs WHERE dataset='garantia' AND status='ok' ORDER BY id DESC LIMIT 1") or {}
            return ("(SELECT upper(trim(code)) codigo, upper(COALESCE(NULLIF(trim(defect),''), '" + NO_DEFECT + "')) defeito, qty quantidade FROM ds_garantia WHERE code IS NOT NULL AND trim(code)<>'' AND qty>0)",
                    {"origem": "servidor", "filename": run.get("object") or "ANALITICO_GARANTIA_DEVOLUCAO", "rows": n, "loaded_at": run.get("at")})
    except Exception: pass
    try: meta = q1("SELECT filename, rows, loaded_at FROM warranty_meta WHERE id=1")
    except Exception: meta = None
    return ("warranty", {**meta, "origem": "planilha"}) if meta else (None, None)

def summary(top=15, code=None):
    from queries import q, q1
    src, meta = _source()
    if not src: return {"available": False}
    w, par = ("WHERE codigo LIKE ?", ["%" + code.strip().upper() + "%"]) if code and code.strip() else ("", [])
    src = f"{src} g"
    tot = q1(f"SELECT COALESCE(SUM(quantidade),0) q, COUNT(DISTINCT codigo) c, COUNT(DISTINCT defeito) d FROM {src} {w}", par)
    return {"available": True, "meta": meta, "total": tot["q"], "codigos": tot["c"], "defeitos": tot["d"],
            "top_defeitos": q(f"SELECT defeito, SUM(quantidade) quantidade, COUNT(DISTINCT codigo) codigos FROM {src} {w} GROUP BY defeito ORDER BY 2 DESC LIMIT ?", par + [int(top)]),
            "top_codigos": q(f"SELECT codigo, SUM(quantidade) quantidade, COUNT(DISTINCT defeito) defeitos FROM {src} {w} GROUP BY codigo ORDER BY 2 DESC LIMIT ?", par + [int(top)]),
            "lista": q(f"SELECT codigo, defeito, SUM(quantidade) quantidade FROM {src} {w} GROUP BY codigo, defeito ORDER BY 3 DESC, codigo LIMIT 500", par)}
