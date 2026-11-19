"""Tela Garantia (etapa 16 · D8; etapa 18 · Q1/Q2/Q4). Uma linha = um item de ocorrência (autorização × código).
  • Fonte: SÓ o servidor (view ANALITICO_GARANTIA_DEVOLUCAO → ds_garantia, FAMILIA AMORTECEDOR e AMORTECEDOR LINHA PESADA, todos os anos). A cada sincronização
    `build()` refaz a tabela `garantias` a partir de ds_garantia. A planilha «Analítico de Garantias» não é mais lida (a Atualização de dados avisa).
    Mesmos campos da planilha (NF = NF_ORI-série; lote e fabricação = campos _GRV; responsável = DEPARTAMENTO; fornecedor = FORNECEDOR_SHORT_GRV; valor = VALOR c/ IPI)
    + UF, lote válido/vencido e status do item. Clientes ficam só no banco local; o CNPJ não é guardado.
  • Padrão da tela: tipos de garantia (GARANTIA, GARANTIA AUTOMATICA, CRÉDITO GARANTIA, GARANTIA EM DEVOLUÇÃO), sem ocorrências canceladas, no ano atual.
  • Defeito agrupado pelo texto: o prefixo «AM-014 » / «O-209 » é ignorado ao agrupar (o código fica em `defeito_cod`).
  • Atalhos (ano, tipo, status, fornecedor, procedência, unidade, UF, validade do lote): cada contagem = linhas da lista ao clicar (ignora o próprio filtro, respeita os outros).
  • Mapa por UF: índice de garantia = peças em garantia ÷ peças de amortecedor vendidas no estado no mesmo período (ds_vendas_uf), e o código com mais peças em cada UF."""
import re, datetime, sqlite3, unicodedata
import database as db
from queries import q, q1

TABLE = """CREATE TABLE IF NOT EXISTS garantias(id INTEGER PRIMARY KEY, autorizacao TEXT, unidade TEXT, data_cadastro TEXT, tipo TEXT, status TEXT, grupo_cliente TEXT, cliente TEXT,
  nf TEXT, data_entrada TEXT, linha TEXT, codigo TEXT, qtd REAL, valor REAL, data_analise TEXT, defeito TEXT, defeito_cod TEXT, defeito_raw TEXT, lote TEXT, data_fabricacao TEXT,
  fornecedor TEXT, procedencia TEXT, responsavel TEXT, erro_lote TEXT, hash TEXT, source_file TEXT, loaded_at TEXT DEFAULT CURRENT_TIMESTAMP, uf TEXT, lote_validade TEXT, status_item TEXT);
CREATE INDEX IF NOT EXISTS ix_gar_cod ON garantias(codigo); CREATE INDEX IF NOT EXISTS ix_gar_data ON garantias(data_cadastro);"""
NOVAS = (("uf", "TEXT"), ("lote_validade", "TEXT"), ("status_item", "TEXT"))      # etapa 18: bancos criados antes
GARANTIA = ("GARANTIA", "GARANTIA AUTOMATICA", "CRÉDITO GARANTIA", "GARANTIA EM DEVOLUÇÃO")       # «Só garantias» (padrão)
CANCEL = "OCORRÊNCIA CANCELADA"
FONTE = "servidor · ANALITICO_GARANTIA_DEVOLUCAO"

def ensure(conn=None):
    c = conn or db.conn()
    try:
        for s in TABLE.split(";"):
            if s.strip(): c.execute(s)
        have = {r[1] for r in c.execute("PRAGMA table_info(garantias)")}
        for col, t in NOVAS:
            if col not in have: c.execute(f"ALTER TABLE garantias ADD COLUMN {col} {t}")
        if conn is None: c.commit()
    finally:
        if conn is None: c.close()

def _canon(s): return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower())
def _txt(v):
    if v is None or (isinstance(v, float) and v != v): return None
    s = re.sub(r"\s+", " ", str(v).replace("_x000D_", " ")).strip(); return s or None
def _up(v):
    t = _txt(v); return t.upper() if t else None
_DEF = re.compile(r"^([A-Z]{1,3}-\d{2,4})\s+")
def defeito(raw):
    """(texto agrupado, código) — «AM-006 AMORTECEDOR SEM AÇÃO» e «AMORTECEDOR SEM AÇÃO» viram o mesmo defeito."""
    t = (_txt(raw) or "").upper()
    if not t: return "NÃO INFORMADO", None
    m = _DEF.match(t); return (t[m.end():].strip() or t, m.group(1)) if m else (t, None)

def is_file(name):
    """Planilha «Analítico de Garantias» (qualquer cópia): a Atualização de dados a reconhece só para avisar que ela não é mais lida."""
    return _canon(re.sub(r"\.\w+$", "", str(name or ""))).startswith("analiticodegarantia")
AVISO_PLANILHA = "A garantia agora vem direto do servidor (view ANALITICO_GARANTIA_DEVOLUCAO), atualizada a cada sincronização. Esta planilha foi ignorada."

def _nf(nf, serie):
    n = (_txt(nf) or "").lstrip("0"); s = _txt(serie)
    return (f"{n}-{s}" if s else n) or None

def build():
    """ds_garantia (servidor) → tabela `garantias` da tela, substituindo a anterior. → nº de linhas gravadas."""
    c = db.conn()
    try:
        ensure(c)
        cols = {r[1] for r in c.execute("PRAGMA table_info(ds_garantia)")}
        g = lambda r, k: r[k] if k in cols else None
        c.row_factory = sqlite3.Row
        out = []
        for r in c.execute("SELECT * FROM ds_garantia WHERE code IS NOT NULL AND trim(code)<>''"):
            d, cod = defeito(g(r, "defect"))
            out.append((_txt(g(r, "auth")), _up(g(r, "unit")), g(r, "event_date"), _up(g(r, "kind")), _up(g(r, "status")), _txt(g(r, "client_group")), _txt(g(r, "customer")),
                        _nf(g(r, "nf"), g(r, "nf_serie")), g(r, "entry_date"), _up(g(r, "family")), _up(g(r, "code")), g(r, "qty"), g(r, "value"), g(r, "analysis_date"),
                        d, cod, _txt(g(r, "defect")), _up(g(r, "lot")), g(r, "fab_date"), _up(g(r, "supplier")), _up(g(r, "verdict")), _up(g(r, "dept")), _txt(g(r, "lot_error")),
                        FONTE, _up(g(r, "uf")), _up(g(r, "lot_valid")), _up(g(r, "status_item"))))
        c.execute("DELETE FROM garantias")
        c.executemany("""INSERT INTO garantias(autorizacao,unidade,data_cadastro,tipo,status,grupo_cliente,cliente,nf,data_entrada,linha,codigo,qtd,valor,data_analise,defeito,defeito_cod,
                         defeito_raw,lote,data_fabricacao,fornecedor,procedencia,responsavel,erro_lote,source_file,uf,lote_validade,status_item) VALUES({})""".format(",".join("?" * 27)), out)
        c.commit(); return len(out)
    finally: c.close()

def available():
    try: return (q1("SELECT COUNT(*) n FROM garantias") or {}).get("n", 0) > 0
    except Exception: return False

# ---------------- consulta da tela ----------------
FILTROS = ("ano", "tipo", "status", "fornecedor", "procedencia", "unidade", "uf", "validade", "defeito", "q")
_COL = {"validade": "lote_validade"}
def _ano(f): return f.get("ano") or str(datetime.date.today().year)
def _where(f, skip="", ano=None, ate=None):
    """`ano`: vazio = ano atual, «todos» = sem filtro · `tipo`: vazio = só garantias, «todos» = todos · `status`: vazio = sem as canceladas, «todos» = inclui.
    `ano`/`ate` (parâmetros): troca o ano do filtro e corta no dia-mês `ate` (MM-DD) — usado no «mesmo período do ano anterior»."""
    w, p = [], []
    a = ano or _ano(f)
    if skip != "ano" and a != "todos": w.append("substr(data_cadastro,1,4)=?"); p.append(a)
    if ate: w.append("substr(data_cadastro,6,5)<=?"); p.append(ate)
    t = f.get("tipo") or ""
    if skip != "tipo":
        if not t: w.append(f"tipo IN ({','.join('?' * len(GARANTIA))})"); p += list(GARANTIA)
        elif t != "todos": w.append("tipo=?"); p.append(t)
    s = f.get("status") or ""
    if skip != "status":
        if not s: w.append("coalesce(status,'')<>?"); p.append(CANCEL)
        elif s != "todos": w.append("status=?"); p.append(s)
    for k in ("fornecedor", "procedencia", "unidade", "uf", "validade"):
        v = f.get(k); col = _COL.get(k, k)
        if skip == k or not v: continue
        if v == "sem": w.append(f"coalesce({col},'')=''")
        else: w.append(f"{col}=?"); p.append(v)
    if skip != "defeito" and f.get("defeito"): w.append("defeito=?"); p.append(f["defeito"])
    for t_ in (f.get("q") or "").upper().split():
        w.append("(upper(codigo) LIKE ? OR upper(coalesce(cliente,'')) LIKE ? OR upper(coalesce(grupo_cliente,'')) LIKE ? OR upper(coalesce(lote,'')) LIKE ? OR coalesce(autorizacao,'') LIKE ? OR coalesce(nf,'') LIKE ?)"); p += [f"%{t_}%"] * 6
    return (" WHERE " + " AND ".join(w)) if w else "", p

def _grp(col, f, skip):
    w, p = _where(f, skip); return {r["v"] or "sem": r["n"] for r in q(f"SELECT {col} v, COUNT(*) n FROM garantias{w} GROUP BY 1 ORDER BY 2 DESC", p)}

_K = """SELECT COUNT(*) linhas, COUNT(DISTINCT autorizacao) ocorrencias, COALESCE(SUM(qtd),0) pecas, COALESCE(SUM(valor),0) valor, COUNT(DISTINCT codigo) codigos,
        COALESCE(SUM(CASE WHEN procedencia='PROCEDENTE' THEN qtd END),0) proc, COALESCE(SUM(CASE WHEN procedencia='IMPROCEDENTE' THEN qtd END),0) improc FROM garantias{w}"""
def _kpis(w, p):
    k = q1(_K.format(w=w), p)
    k["pct_procedente"] = round(100 * k["proc"] / (k["proc"] + k["improc"]), 1) if (k["proc"] + k["improc"]) else None
    return k

def _periodo(f):
    """Mesmo período do ano anterior: ano atual → 1/jan até o mesmo dia-mês do último cadastro; ano fechado → o ano anterior inteiro. «todos» → None."""
    a = _ano(f)
    if a == "todos" or not a.isdigit(): return None
    ate = None
    if a == str(datetime.date.today().year):
        w, p = _where(f); m = (q1(f"SELECT MAX(data_cadastro) m FROM garantias{w}", p) or {}).get("m")
        ate = (m or datetime.date.today().isoformat())[5:10]
    return str(int(a) - 1), ate

def _vendas_uf(f):
    """{UF: peças vendidas} no mesmo período do filtro de ano (ds_vendas_uf, sincronizada do servidor). {} se a tabela não existe ou está vazia."""
    a = _ano(f); w, p = [], []
    if a != "todos": w.append("substr(sale_date,1,4)=?"); p.append(a)
    try: return {r["uf"]: r["qtd"] for r in q(f"SELECT upper(uf) uf, SUM(qty) qtd FROM ds_vendas_uf{(' WHERE ' + ' AND '.join(w)) if w else ''} GROUP BY 1", p) if r["uf"]}
    except Exception: return {}

def summary(f, page=1, size=100):
    ensure()
    if not available(): return {"available": False}
    w, p = _where(f); T = lambda sql, extra=(): q(sql.format(w=w), p + list(extra))
    k = _kpis(w, p)
    ant = None; per = _periodo(f)
    if per:
        wa, pa = _where(f, ano=per[0], ate=per[1]); ant = {**_kpis(wa, pa), "ano": per[0], "ate": per[1]}
    lw = (w + " AND " if w else " WHERE ") + "coalesce(lote,'')<>''"
    desc = {r["perfect_code"]: r["description"] for r in q("SELECT perfect_code,description FROM products")}
    codigos = T("SELECT codigo, COUNT(*) linhas, COALESCE(SUM(qtd),0) pecas, COALESCE(SUM(valor),0) valor, COUNT(DISTINCT defeito) defeitos FROM garantias{w} GROUP BY codigo ORDER BY pecas DESC LIMIT 15")
    for r in codigos: r["descricao"] = desc.get(r["codigo"])
    tot = k["pecas"] or 1
    defeitos = T("SELECT defeito, MAX(defeito_cod) cod, COUNT(*) linhas, COALESCE(SUM(qtd),0) pecas FROM garantias{w} GROUP BY defeito ORDER BY pecas DESC LIMIT 15")
    acc = 0
    for r in defeitos: r["pct"] = round(100 * r["pecas"] / tot, 1); acc += r["pecas"]; r["acum"] = round(100 * acc / tot, 1)      # Pareto: % acumulado sobre o total filtrado
    por_mes = T("SELECT substr(data_cadastro,1,7) mes, COUNT(*) linhas, COALESCE(SUM(qtd),0) pecas, COALESCE(SUM(valor),0) valor FROM garantias{w} GROUP BY 1 ORDER BY 1")
    if per:      # linha do ano anterior no gráfico mensal (mesmos filtros, ano inteiro anterior)
        wa, pa = _where(f, ano=per[0]); prev = {r["m"]: r for r in q(f"SELECT substr(data_cadastro,6,2) m, COALESCE(SUM(qtd),0) pecas, COALESCE(SUM(valor),0) valor FROM garantias{wa} GROUP BY 1", pa)}
        meses = [f"{_ano(f)}-{m:02d}" for m in range(1, 13)]; have = {r["mes"]: r for r in por_mes}
        ult = max([int(x["mes"][5:7]) for x in por_mes] or [0])
        por_mes = [{**(have.get(m) or {"mes": m, "linhas": 0, "pecas": 0, "valor": 0}), "pecas_ant": (prev.get(m[5:7]) or {}).get("pecas", 0), "valor_ant": (prev.get(m[5:7]) or {}).get("valor", 0),
                    "futuro": int(m[5:7]) > ult} for m in meses]
    # mapa: por UF (peças, valor, ocorrências, índice = peças ÷ vendidas no estado) e o código com mais peças em cada UF
    vend = _vendas_uf(f)
    ufs = T("SELECT coalesce(uf,'') uf, COUNT(DISTINCT autorizacao) ocorrencias, COALESCE(SUM(qtd),0) pecas, COALESCE(SUM(valor),0) valor FROM garantias{w} GROUP BY 1 ORDER BY pecas DESC")
    topc = {}
    for r in T("SELECT coalesce(uf,'') uf, codigo, COALESCE(SUM(qtd),0) pecas FROM garantias{w} GROUP BY 1, 2 ORDER BY 1, 3 DESC, 2"):
        lst = topc.setdefault(r["uf"], [])
        if len(lst) < 3: lst.append({"codigo": r["codigo"], "pecas": r["pecas"]})
    for r in ufs:
        v = vend.get(r["uf"]); r["vendidas"] = v; r["indice"] = round(100 * r["pecas"] / v, 2) if v else None
        r["top"] = topc.get(r["uf"], []); r["descricao"] = desc.get(r["top"][0]["codigo"]) if r["top"] else None
    fornecedores = T("""SELECT coalesce(fornecedor,'') fornecedor, COUNT(DISTINCT codigo) codigos, COALESCE(SUM(qtd),0) pecas, COALESCE(SUM(valor),0) valor,
                        COALESCE(SUM(CASE WHEN procedencia='PROCEDENTE' THEN qtd END),0) proc, COALESCE(SUM(CASE WHEN procedencia='IMPROCEDENTE' THEN qtd END),0) improc
                        FROM garantias{w} GROUP BY 1 ORDER BY pecas DESC""")
    for r in fornecedores: r["pct_procedente"] = round(100 * r["proc"] / (r["proc"] + r["improc"]), 1) if (r["proc"] + r["improc"]) else None
    off = (max(int(page or 1), 1) - 1) * size
    return {"available": True, "meta": q1("SELECT COUNT(*) n, MAX(loaded_at) at, MAX(source_file) fonte, MIN(data_cadastro) de, MAX(data_cadastro) ate FROM garantias"),
            "kpis": k, "anterior": ant, "total": k["linhas"], "page": max(int(page or 1), 1), "size": size, "vendas_uf": bool(vend),
            "counts": {"ano": _grp("substr(data_cadastro,1,4)", f, "ano"), "tipo": _grp("tipo", f, "tipo"), "status": _grp("status", f, "status"), "fornecedor": _grp("fornecedor", f, "fornecedor"),
                       "procedencia": _grp("procedencia", f, "procedencia"), "unidade": _grp("unidade", f, "unidade"), "uf": _grp("uf", f, "uf"), "validade": _grp("lote_validade", f, "validade")},
            "por_mes": por_mes, "defeitos": defeitos, "codigos": codigos, "por_uf": ufs, "fornecedores": fornecedores,
            "lotes": q(f"SELECT lote, MAX(codigo) codigo, COUNT(DISTINCT codigo) codigos, MIN(data_fabricacao) fabricacao, MAX(lote_validade) validade, COALESCE(SUM(qtd),0) pecas, SUM(CASE WHEN coalesce(erro_lote,'')<>'' THEN 1 ELSE 0 END) erro_lote FROM garantias{lw} GROUP BY lote ORDER BY pecas DESC LIMIT 15", p),
            "rows": T(f"SELECT data_cadastro,autorizacao,tipo,status,status_item,unidade,uf,cliente,codigo,qtd,valor,defeito,defeito_cod,lote,lote_validade,data_fabricacao,fornecedor,procedencia,responsavel,erro_lote FROM garantias{{w}} ORDER BY data_cadastro DESC, autorizacao DESC LIMIT {size} OFFSET {off}")}

def rows_all(f):
    w, p = _where(f)
    return q(f"SELECT data_cadastro,autorizacao,tipo,status,status_item,unidade,uf,grupo_cliente,cliente,nf,codigo,qtd,valor,defeito,defeito_cod,lote,lote_validade,data_fabricacao,fornecedor,procedencia,responsavel,erro_lote FROM garantias{w} ORDER BY data_cadastro DESC, autorizacao DESC", p)
