"""Garantia pela planilha «Analítico de Garantias» (etapa 16 · D8). Uma linha = um item de ocorrência (autorização × código).
  • Fonte: a planilha prevalece — entra por Atualização de dados (nome «Analítico de Garantias») e SUBSTITUI a carga anterior; sem planilha, a tela usa
    a view do servidor (warranty.py, ANALITICO_GARANTIA_DEVOLUCAO). Guarda só as colunas usadas (sem CNPJ); clientes ficam só no banco local.
  • Padrão da tela: tipos de garantia (GARANTIA, GARANTIA AUTOMATICA, CRÉDITO GARANTIA, GARANTIA EM DEVOLUÇÃO), sem ocorrências canceladas, no ano atual.
  • Defeito agrupado pelo texto: o prefixo «AM-014 » / «O-209 » é ignorado ao agrupar (o código fica em `defeito_cod`).
  • Atalhos (ano, tipo, status, fornecedor, procedência, unidade): cada contagem = linhas da lista ao clicar (ignora o próprio filtro, respeita os outros)."""
import re, datetime, hashlib, unicodedata
import pandas as pd
import database as db
from queries import q, q1

TABLE = """CREATE TABLE IF NOT EXISTS garantias(id INTEGER PRIMARY KEY, autorizacao TEXT, unidade TEXT, data_cadastro TEXT, tipo TEXT, status TEXT, grupo_cliente TEXT, cliente TEXT,
  nf TEXT, data_entrada TEXT, linha TEXT, codigo TEXT, qtd REAL, valor REAL, data_analise TEXT, defeito TEXT, defeito_cod TEXT, defeito_raw TEXT, lote TEXT, data_fabricacao TEXT,
  fornecedor TEXT, procedencia TEXT, responsavel TEXT, erro_lote TEXT, hash TEXT, source_file TEXT, loaded_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS ix_gar_cod ON garantias(codigo); CREATE INDEX IF NOT EXISTS ix_gar_data ON garantias(data_cadastro);"""
GARANTIA = ("GARANTIA", "GARANTIA AUTOMATICA", "CRÉDITO GARANTIA", "GARANTIA EM DEVOLUÇÃO")       # «Só garantias» (padrão)
CANCEL = "OCORRÊNCIA CANCELADA"
LABEL = "Garantias (Analítico de Garantias)"
# nomes de coluna aceitos (comparados sem acento/pontuação: «Nº Autorização» vira «noautorizacao»)
COLS = {"autorizacao": ["Nº Autorização", "N Autorizacao", "Numero Autorizacao", "Autorizacao"], "unidade": ["Unidade"], "data_cadastro": ["Data Cadastro"], "tipo": ["Tipo Ocorrencia"],
        "status": ["Status Ocorrencia"], "grupo_cliente": ["Grupo Cliente"], "cliente": ["Razao Social"], "nf": ["NF"], "data_entrada": ["Data Entrada"], "linha": ["Linha"],
        "codigo": ["Codigo"], "qtd": ["Qtd"], "valor": ["Valor C.IPI", "Valor CIPI"], "data_analise": ["D.Analise", "Data Analise"], "defeito": ["Defeito"], "lote": ["Lote"],
        "data_fabricacao": ["Data Fabricacao"], "fornecedor": ["Fornecedor Short"], "procedencia": ["Tipo I/P"], "responsavel": ["Responsavel"], "erro_lote": ["Erro Lote"]}
DATES = ("data_cadastro", "data_entrada", "data_analise", "data_fabricacao")

def ensure():
    with db.session() as c: c.executescript(TABLE)

def _canon(s): return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower())
def _txt(v):
    if v is None or (isinstance(v, float) and v != v): return None
    s = re.sub(r"\s+", " ", str(v).replace("_x000D_", " ")).strip(); return s or None
_DEF = re.compile(r"^([A-Z]{1,3}-\d{2,4})\s+")
def defeito(raw):
    """(texto agrupado, código) — «AM-006 AMORTECEDOR SEM AÇÃO» e «AMORTECEDOR SEM AÇÃO» viram o mesmo defeito."""
    t = (_txt(raw) or "").upper()
    if not t: return "NÃO INFORMADO", None
    m = _DEF.match(t); return (t[m.end():].strip() or t, m.group(1)) if m else (t, None)

def is_file(name): return _canon(re.sub(r"\.\w+$", "", str(name or ""))).startswith("analiticodegarantia")

def read(path):
    """DataFrame com as colunas do sistema. O cabeçalho é a 1ª linha (das 5 primeiras) que tem «Codigo» e «Qtd» (a planilha traz uma linha de totais antes)."""
    raw = pd.read_excel(path, header=None, nrows=6)
    hdr = next((i for i in range(len(raw)) if {"codigo", "qtd"} <= {_canon(x) for x in raw.iloc[i].tolist()}), None)
    if hdr is None: raise ValueError("Cabeçalho não encontrado (precisa das colunas «Codigo» e «Qtd»).")
    df = pd.read_excel(path, header=hdr); by = {_canon(c): c for c in df.columns}
    out = pd.DataFrame(index=df.index)
    for k, names in COLS.items():
        col = next((by[_canon(n)] for n in names if _canon(n) in by), None)
        out[k] = df[col] if col is not None else None
    out = out[out["codigo"].map(_txt).notna()].copy()
    for k in out.columns:
        if k in DATES: out[k] = pd.to_datetime(out[k], errors="coerce").dt.strftime("%Y-%m-%d").where(lambda s: s.notna(), None)
        elif k in ("qtd", "valor"): out[k] = pd.to_numeric(out[k], errors="coerce")
        else: out[k] = out[k].map(_txt)
    for k in ("codigo", "tipo", "status", "fornecedor", "procedencia", "responsavel", "unidade", "linha", "lote"): out[k] = out[k].map(lambda v: v.upper() if isinstance(v, str) else None)
    d = out["defeito"].map(defeito); out["defeito_raw"] = out["defeito"]; out["defeito"] = d.map(lambda x: x[0]); out["defeito_cod"] = d.map(lambda x: x[1])
    out["hash"] = [hashlib.md5("|".join(str(v) for v in r).encode()).hexdigest() for r in out[list(COLS)].itertuples(index=False, name=None)]
    return out.astype(object).where(out.notna(), None)

def load(path, name, confirm, conn):
    """Substitui a carga anterior (planilha prevalece). Na verificação a transação é desfeita por quem chamou (updater.run). → resultado no formato do updater."""
    for s in TABLE.split(";"):          # execute (não executescript): executescript faria commit no meio da transação da atualização
        if s.strip(): conn.execute(s)
    df = read(path); old = {r[0] for r in conn.execute("SELECT hash FROM garantias")}; new = set(df["hash"])
    n_new, n_pres, n_gone = len(new - old), len(new & old), len(old - new)
    conn.execute("DELETE FROM garantias")
    cols = list(COLS) + ["defeito_cod", "defeito_raw", "hash"]
    conn.executemany(f"INSERT INTO garantias({','.join(cols)},source_file) VALUES({','.join('?' * len(cols))},?)", [(*r, name) for r in df[cols].itertuples(index=False, name=None)])
    msgs = [f"{n_gone} linha(s) da carga anterior não estão nesta planilha e saem (a planilha substitui a anterior)."] if n_gone else []
    return {"label": LABEL, "rows": len(df), "counts": {"new": n_new, "updated": 0, "present": n_pres}, "messages": msgs}

def available():
    try: return (q1("SELECT COUNT(*) n FROM garantias") or {}).get("n", 0) > 0
    except Exception: return False

# ---------------- consulta da tela ----------------
FILTROS = ("ano", "tipo", "status", "fornecedor", "procedencia", "unidade", "defeito", "q")
def _where(f, skip=""):
    """`ano`: vazio = ano atual, «todos» = sem filtro · `tipo`: vazio = só garantias, «todos» = todos · `status`: vazio = sem as canceladas, «todos» = inclui."""
    w, p = [], []
    ano = f.get("ano") or str(datetime.date.today().year)
    if skip != "ano" and ano != "todos": w.append("substr(data_cadastro,1,4)=?"); p.append(ano)
    t = f.get("tipo") or ""
    if skip != "tipo":
        if not t: w.append(f"tipo IN ({','.join('?' * len(GARANTIA))})"); p += list(GARANTIA)
        elif t != "todos": w.append("tipo=?"); p.append(t)
    s = f.get("status") or ""
    if skip != "status":
        if not s: w.append("coalesce(status,'')<>?"); p.append(CANCEL)
        elif s != "todos": w.append("status=?"); p.append(s)
    for k in ("fornecedor", "procedencia", "unidade"):
        v = f.get(k)
        if skip == k or not v: continue
        if v == "sem": w.append(f"coalesce({k},'')=''")
        else: w.append(f"{k}=?"); p.append(v)
    if skip != "defeito" and f.get("defeito"): w.append("defeito=?"); p.append(f["defeito"])
    for t_ in (f.get("q") or "").upper().split():
        w.append("(upper(codigo) LIKE ? OR upper(coalesce(cliente,'')) LIKE ? OR upper(coalesce(grupo_cliente,'')) LIKE ? OR upper(coalesce(lote,'')) LIKE ? OR coalesce(autorizacao,'') LIKE ? OR coalesce(nf,'') LIKE ?)"); p += [f"%{t_}%"] * 6
    return (" WHERE " + " AND ".join(w)) if w else "", p

def _grp(col, f, skip):
    w, p = _where(f, skip); return {r["v"] or "sem": r["n"] for r in q(f"SELECT {col} v, COUNT(*) n FROM garantias{w} GROUP BY 1 ORDER BY 2 DESC", p)}

def summary(f, page=1, size=100):
    ensure()
    if not available(): return {"available": False}
    w, p = _where(f); T = lambda sql, extra=(): q(sql.format(w=w), p + list(extra))
    k = q1(f"""SELECT COUNT(*) linhas, COUNT(DISTINCT autorizacao) ocorrencias, COALESCE(SUM(qtd),0) pecas, COALESCE(SUM(valor),0) valor, COUNT(DISTINCT codigo) codigos,
               COALESCE(SUM(CASE WHEN procedencia='PROCEDENTE' THEN qtd END),0) proc, COALESCE(SUM(CASE WHEN procedencia='IMPROCEDENTE' THEN qtd END),0) improc FROM garantias{w}""", p)
    k["pct_procedente"] = round(100 * k["proc"] / (k["proc"] + k["improc"]), 1) if (k["proc"] + k["improc"]) else None
    lw = (w + " AND " if w else " WHERE ") + "coalesce(lote,'')<>''"
    desc = {r["perfect_code"]: r["description"] for r in q("SELECT perfect_code,description FROM products")}
    codigos = T("SELECT codigo, COUNT(*) linhas, COALESCE(SUM(qtd),0) pecas, COALESCE(SUM(valor),0) valor, COUNT(DISTINCT defeito) defeitos FROM garantias{w} GROUP BY codigo ORDER BY pecas DESC LIMIT 15")
    for r in codigos: r["descricao"] = desc.get(r["codigo"])
    tot = k["pecas"] or 1
    defeitos = T("SELECT defeito, MAX(defeito_cod) cod, COUNT(*) linhas, COALESCE(SUM(qtd),0) pecas FROM garantias{w} GROUP BY defeito ORDER BY pecas DESC LIMIT 15")
    for r in defeitos: r["pct"] = round(100 * r["pecas"] / tot, 1)
    off = (max(int(page or 1), 1) - 1) * size
    return {"available": True, "meta": q1("SELECT COUNT(*) n, MAX(loaded_at) at, MAX(source_file) file, MIN(data_cadastro) de, MAX(data_cadastro) ate FROM garantias"),
            "kpis": k, "total": k["linhas"], "page": max(int(page or 1), 1), "size": size,
            "counts": {"ano": _grp("substr(data_cadastro,1,4)", f, "ano"), "tipo": _grp("tipo", f, "tipo"), "status": _grp("status", f, "status"), "fornecedor": _grp("fornecedor", f, "fornecedor"),
                       "procedencia": _grp("procedencia", f, "procedencia"), "unidade": _grp("unidade", f, "unidade")},
            "por_mes": T("SELECT substr(data_cadastro,1,7) mes, COUNT(*) linhas, COALESCE(SUM(qtd),0) pecas, COALESCE(SUM(valor),0) valor FROM garantias{w} GROUP BY 1 ORDER BY 1"),
            "defeitos": defeitos, "codigos": codigos,
            "clientes": T("SELECT cliente, MAX(grupo_cliente) grupo, COUNT(DISTINCT autorizacao) ocorrencias, COALESCE(SUM(qtd),0) pecas, COALESCE(SUM(valor),0) valor FROM garantias{w} GROUP BY cliente ORDER BY pecas DESC LIMIT 15"),
            "lotes": q(f"SELECT lote, MAX(codigo) codigo, COUNT(DISTINCT codigo) codigos, MIN(data_fabricacao) fabricacao, COALESCE(SUM(qtd),0) pecas, SUM(CASE WHEN coalesce(erro_lote,'')<>'' THEN 1 ELSE 0 END) erro_lote FROM garantias{lw} GROUP BY lote ORDER BY pecas DESC LIMIT 15", p),
            "responsavel": T("SELECT coalesce(responsavel,'NÃO INFORMADO') responsavel, COALESCE(SUM(qtd),0) pecas FROM garantias{w} GROUP BY 1 ORDER BY 2 DESC"),
            "rows": T(f"SELECT data_cadastro,autorizacao,tipo,status,unidade,cliente,codigo,qtd,valor,defeito,defeito_cod,lote,data_fabricacao,fornecedor,procedencia,responsavel,erro_lote FROM garantias{{w}} ORDER BY data_cadastro DESC, autorizacao DESC LIMIT {size} OFFSET {off}")}

def rows_all(f):
    w, p = _where(f)
    return q(f"SELECT data_cadastro,autorizacao,tipo,status,unidade,grupo_cliente,cliente,nf,codigo,qtd,valor,defeito,defeito_cod,lote,data_fabricacao,fornecedor,procedencia,responsavel,erro_lote FROM garantias{w} ORDER BY data_cadastro DESC, autorizacao DESC", p)
