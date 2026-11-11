"""
data_pipeline.py — servidor SQL Server (SOMENTE LEITURA)  →  cache local SQLite  →  módulos do app.

Roda 100% portátil (venv na pasta do projeto, sem administrador e sem instalar driver no Windows):
  • preferência: pymssql  (vem com o FreeTDS embutido, instala só com pip);
  • alternativa: pyodbc com  DRIVER={SQL Server}  (driver legado que já vem no Windows).

O que faz
  1. conecta só com SELECT (guarda de somente-leitura);
  2. localiza as tabelas/views pelo nome, em qualquer banco/esquema que o login enxergue;
  3. extrai e NORMALIZA DESENVOLVIMENTO_PRODUTOS: tipo → DESENVOLVIMENTO | REDESENVOLVIMENTO, status, datas, curtiu...;
  4. grava o snapshot local a cada sincronização (1ª carga = marco zero) e registra as TRANSIÇÕES de status (o servidor só guarda o status atual);
  5. publica o resultado em rd_projects (as telas de Desenvolvimento/Redesenvolvimento passam a ler o servidor, não mais a planilha);
  6. traz também compras, vendas e estoque (PEDIDOS_COMPRA_DETALHADO, PEDIDOS_VENDA_DETALHADO, EST DISP);
  7. trava de segurança: recusa carga com menos de 50% dos itens da sincronização anterior.

Linha de comando:  python data_pipeline.py probe | sync | status
Configuração: .env (copie .env.example). A senha nunca fica no código.
"""
import os, shutil, re, sys, json, time, shutil, sqlite3, hashlib, datetime, threading, unicodedata, logging

import pandas as pd
import kinds

log = logging.getLogger("data_pipeline")
BASE = os.path.dirname(os.path.abspath(__file__))

# ───────────────────────── rótulos oficiais ─────────────────────────
KIND_DES = kinds.DES            # "DESENVOLVIMENTO"
KIND_RD = kinds.RD              # "REDESENVOLVIMENTO"
normalize_kind = kinds.normalize_kind

# Ciclo de vida: usado para escolher o status do ITEM quando o código tem várias linhas (aplicações) com status diferentes.
STATUS_RANK = {
    "PENDENTE COD. PERFECT": 0, "PENDENTE PARTNUMBER FORNECEDOR": 0, "PENDENTE CONFIRMAÇÃO": 1, "EM COTAÇÃO": 2,
    "PEDIDO CONFIRMADO": 3, "FINALIZANDO CIT": 4, "ITEM RECEBIDO": 5,
}

# ───────────────────────── configuração ─────────────────────────
PERSIST_DIR = os.path.join(os.path.expanduser("~"), ".perfect_shock_data")          # pasta fixa do usuário: sobrevive a trocar de versão/pasta do sistema

def env_candidates():
    """Onde procurar o .env, em ordem: variável PSD_ENV · pasta do sistema · pasta fixa do usuário (~/.perfect_shock_data) · pasta ACIMA · pastas irmãs (versões anteriores, a mais recente primeiro)."""
    out = [os.environ.get("PSD_ENV") or "", os.path.join(BASE, ".env"), os.path.join(PERSIST_DIR, ".env"), os.path.join(os.path.dirname(BASE), ".env")]
    try:
        sib = [os.path.join(os.path.dirname(BASE), d, ".env") for d in os.listdir(os.path.dirname(BASE)) if os.path.abspath(os.path.join(os.path.dirname(BASE), d)) != os.path.abspath(BASE)]
        out += sorted((x for x in sib if os.path.isfile(x)), key=os.path.getmtime, reverse=True)
    except OSError: pass
    seen, res = set(), []
    for x in out:
        if x and os.path.isfile(x) and os.path.abspath(x) not in seen: seen.add(os.path.abspath(x)); res.append(x)
    return res

def _read_env(path):
    try:
        from dotenv import load_dotenv
        load_dotenv(path, override=False); return
    except ImportError:
        pass
    for line in open(path, encoding="utf-8-sig"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k, v = line.split("=", 1); v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'": v = v[1:-1]
        os.environ.setdefault(k.strip(), v)

def load_env(path=None):
    """Lê o .env (sem sobrescrever variáveis já definidas). Sem `path`, usa o PRIMEIRO .env encontrado em env_candidates() — assim trocar de versão do sistema NÃO exige preencher tudo de novo —
    e guarda uma cópia em ~/.perfect_shock_data/.env (só se ainda não houver), que passa a valer para qualquer versão. O .env nunca vai dentro do .zip."""
    if path: return _read_env(path) if os.path.isfile(path) else None
    found = env_candidates()
    if not found: return
    _read_env(found[0]); keep = os.path.join(PERSIST_DIR, ".env")
    if not os.path.isfile(keep):
        try: os.makedirs(PERSIST_DIR, exist_ok=True); shutil.copyfile(found[0], keep)
        except OSError: pass


class Config:
    def __init__(self, **kw):
        e = os.environ.get
        self.host = kw.get("host") or e("DEV_DB_HOST", "192.168.0.54")
        self.port = int(kw.get("port") or e("DEV_DB_PORT", "1433"))
        self.user = kw.get("user") or e("DEV_DB_USER", "")
        self.password = kw.get("password") or e("DEV_DB_PASSWORD", "")
        self.database = kw.get("database") or e("DEV_DB_NAME", "")           # vazio = banco padrão do login (e, se não achar, procura nos demais)
        self.schema = kw.get("schema") or e("DEV_DB_SCHEMA", "")             # vazio = qualquer esquema
        self.driver = kw.get("driver") or e("DEV_DB_DRIVER", "")             # vazio = pymssql e, se faltar, pyodbc "SQL Server" (legado). Valores: pymssql | pyodbc
        self.timeout = int(kw.get("timeout") or e("DEV_DB_TIMEOUT", "15"))
        self.query_timeout = int(e("DEV_DB_QUERY_TIMEOUT", "180"))
        self.tds = kw.get("tds") or e("DEV_DB_TDS", "")                      # só se precisar: 7.0 | 7.1 | 7.2 | 7.3 | 7.4
        self.encrypt = (kw.get("encrypt") or e("DEV_DB_ENCRYPT", "no")).lower()
        self.dev_object = kw.get("dev_object") or e("DEV_DB_OBJECT_DEV", "DESENVOLVIMENTO_PRODUTOS")
        self.min_ratio = float(e("DEV_SYNC_MIN_RATIO", "0.5"))               # trava: não aceita carga com menos de 50% dos itens da anterior
        self.backfill = e("DEV_SYNC_BACKFILL_DATES", "0") == "1"             # opcional: eventos retroativos a partir de colunas de data (padrão: desligado)
        try: self.column_overrides = json.loads(kw.get("column_overrides") or e("DEV_DB_COLUMNS", "") or "{}")   # {"status": "STATUS_ITEM", ...}
        except ValueError: self.column_overrides = {}

    def masked(self, text):
        t = str(text)
        for secret in (self.password,):
            if secret: t = t.replace(secret, "****")
        return re.sub(r"(PWD=)[^;]*", r"\1****", t, flags=re.I)


# ───────────────────────── conexão (somente leitura) ─────────────────────────
_FORBIDDEN = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|MERGE|CREATE|EXEC|EXECUTE|GRANT|REVOKE|DENY|BULK|INTO)\b", re.I)

def assert_select(sql):
    """Defesa em profundidade: só passa SELECT/WITH, uma instrução, sem comandos de escrita."""
    s = re.sub(r"'(?:[^']|'')*'", "''", sql)                 # ignora texto entre aspas
    s = re.sub(r"--[^\n]*|/\*.*?\*/", " ", s, flags=re.S).strip().rstrip(";").strip()
    if ";" in s or not re.match(r"(SELECT|WITH)\b", s, re.I) or _FORBIDDEN.search(s):
        raise PermissionError("Pipeline é somente leitura: só SELECT é permitido.")
    return sql

def qi(name):
    """Identificador entre colchetes (SQL Server): aceita espaço, acento e ']' no nome — ex.: [EST DISP]."""
    return "[" + str(name).replace("]", "]]") + "]"

def _is_login_error(e):
    t = str(e).lower(); return "login failed" in t or "18456" in t or "authentication" in t

def _connect_pymssql(cfg):
    import pymssql
    kw = dict(server=cfg.host, port=str(cfg.port), user=cfg.user, password=cfg.password, login_timeout=cfg.timeout, timeout=cfg.query_timeout, autocommit=True, charset="UTF-8")
    if cfg.database: kw["database"] = cfg.database
    if cfg.tds: kw["tds_version"] = cfg.tds
    return pymssql.connect(**kw)

def _connect_pyodbc_legacy(cfg):
    """pyodbc + DRIVER={SQL Server}: driver legado que já vem com o Windows (nenhuma instalação). Senha com @ ; } é tratada."""
    import pyodbc
    pwd = "{" + cfg.password.replace("}", "}}") + "}"
    cs = f"DRIVER={{{cfg.driver if cfg.driver.lower() not in ('', 'pyodbc') else 'SQL Server'}}};SERVER={cfg.host},{cfg.port};UID={cfg.user};PWD={pwd};"
    if cfg.database: cs += f"DATABASE={cfg.database};"
    return pyodbc.connect(cs, timeout=cfg.timeout, autocommit=True)

def connect(cfg):
    """Abre a conexão (somente leitura na prática: o pipeline só emite SELECT). Tenta pymssql e, se não houver/falhar por rede, pyodbc legado."""
    if not cfg.user or not cfg.password: raise RuntimeError("Defina DEV_DB_USER e DEV_DB_PASSWORD no arquivo .env.")
    order = ["pyodbc"] if cfg.driver.lower() in ("pyodbc", "sql server") else ["pymssql"] if cfg.driver.lower() == "pymssql" else ["pymssql", "pyodbc"]; errs = []
    for mode in order:
        try: return _connect_pymssql(cfg) if mode == "pymssql" else _connect_pyodbc_legacy(cfg)
        except ImportError: errs.append(f"{mode}: não instalado")
        except Exception as e:
            errs.append(f"{mode}: {e}")
            if _is_login_error(e): break          # senha/usuário errados: tentar outro driver não adianta
    raise RuntimeError("Não foi possível conectar ao SQL Server " + cfg.host + ". " + " | ".join(errs) + ". Dicas: confira a VPN/rede, o usuário/senha no .env e, se o erro citar SSL/TLS, defina DEV_DB_TDS=7.4.")


class Dialect:
    """O que muda entre o SQL Server (produção) e o SQLite (usado nos testes como 'servidor de mentira')."""
    name = "mssql"
    ph = "?"                          # marcador de parâmetro: pyodbc/sqlite '?' · pymssql '%s'
    def quote(self, n): return qi(n)
    def _all(self, conn, sql, params=()):
        cur = conn.cursor()
        try: cur.execute(assert_select(sql), params) if params else cur.execute(assert_select(sql)); return [tuple(r) for r in cur.fetchall()]
        finally: cur.close()
    def databases(self, conn):
        cur_db = self._all(conn, "SELECT DB_NAME()")[0][0]
        others = [r[0] for r in self._all(conn, "SELECT name FROM sys.databases WHERE state=0 AND HAS_DBACCESS(name)=1 AND database_id>4 ORDER BY name")]
        return [cur_db] + [d for d in others if d != cur_db]
    def objects(self, conn, db): return self._all(conn, f"SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE FROM {qi(db)}.INFORMATION_SCHEMA.TABLES")
    def columns(self, conn, db, schema, name):
        return self._all(conn, f"SELECT COLUMN_NAME, DATA_TYPE FROM {qi(db)}.INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA={self.ph} AND TABLE_NAME={self.ph} ORDER BY ORDINAL_POSITION", (schema, name))
    def qualified(self, db, schema, name): return f"{qi(db)}.{qi(schema)}.{qi(name)}"

class PymssqlDialect(Dialect):
    ph = "%s"

class SqliteDialect(Dialect):
    name = "sqlite"
    def quote(self, n): return '"' + str(n).replace('"', '""') + '"'
    def databases(self, conn): return ["main"]
    def objects(self, conn, db): return self._all(conn, "SELECT 'main', name, CASE type WHEN 'view' THEN 'VIEW' ELSE 'BASE TABLE' END FROM sqlite_master WHERE type IN ('table','view')")
    def columns(self, conn, db, schema, name):
        cur = conn.cursor(); cur.execute(f"PRAGMA table_info({self.quote(name)})"); r = [(x[1], x[2]) for x in cur.fetchall()]; cur.close(); return r
    def qualified(self, db, schema, name): return self.quote(name)

def dialect_for(conn):
    mod = conn.__class__.__module__
    return SqliteDialect() if mod.startswith("sqlite3") else PymssqlDialect() if mod.startswith("pymssql") else Dialect()

def _key(s): return re.sub(r"[^A-Z0-9]", "", unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().upper())

def locate(conn, names, cfg=None, dialect=None):
    """Acha cada objeto (tabela ou view) pelo nome, ignorando maiúsculas, espaço e underline ('EST DISP' = EST_DISP).
    Procura no banco informado (DEV_DB_NAME) ou no padrão do login e, se não achar, nos demais bancos acessíveis.
    Retorna {nome_pedido: {db, schema, name, type, sql}} (só os encontrados)."""
    cfg = cfg or Config(); dl = dialect or dialect_for(conn); want = {_key(n): n for n in names}; found = {}
    dbs = [cfg.database] if cfg.database else dl.databases(conn)
    for db in dbs:
        for schema, name, typ in dl.objects(conn, db):
            if cfg.schema and schema.upper() != cfg.schema.upper(): continue
            k = _key(name)
            if k in want and want[k] not in found:
                found[want[k]] = {"db": db, "schema": schema, "name": name, "type": typ, "sql": dl.qualified(db, schema, name)}
        if len(found) == len(want): break
    return found


# ───────────────────────── extração ─────────────────────────
def extract_raw(conn, obj, chunk=20000, limit=None, where="", sql=None):
    """SELECT * do objeto (ou a consulta `sql` pronta), em blocos (não estoura memória), como DataFrame de objetos. `obj` vem de locate().
    `where`: filtro aplicado NO SERVIDOR (só vem o que o app usa — muito mais rápido que trazer a view inteira)."""
    cur = conn.cursor()
    try:
        top = f"TOP ({int(limit)}) " if limit and dialect_for(conn).name == "mssql" else ""
        sql = sql or (f"SELECT {top}* FROM {obj['sql']}" + (f" WHERE {where}" if where else "") + (f" LIMIT {int(limit)}" if limit and not top else ""))
        cur.execute(assert_select(sql)); cols = [d[0] for d in cur.description]; rows = []
        while True:
            part = cur.fetchmany(chunk)
            if not part: break
            rows.extend(tuple(r) for r in part)
    finally: cur.close()
    return pd.DataFrame.from_records(rows, columns=cols) if rows else pd.DataFrame(columns=cols)


# ───────────────────────── normalização ─────────────────────────
def unaccent(s): return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
def canon_col(c): return re.sub(r"[^A-Z0-9]+", "_", unaccent(c).upper()).strip("_")

# campo canônico -> nomes possíveis da coluna (já em forma canônica: sem acento, maiúscula, '_')
COLUMN_ALIASES = {
    "code": ["CODIGO", "COD", "COD_PRODUTO", "CODIGO_PRODUTO", "PRODUTO", "ITEM", "CODIGO_PERFECT"],
    "kind": ["SUGESTAO", "TIPO", "TIPO_PROJETO", "CLASSIFICACAO", "DES_RD", "TIPO_DESENVOLVIMENTO", "DESENVOLVIMENTO_REDESENVOLVIMENTO"],
    "status": ["STATUS", "STATUS_ITEM", "SITUACAO"],
    "sub_desenho": ["SUB_STATUS_DESENHO"], "sub_validacao": ["SUB_STATUS_VALIDACAO"], "sub_projeto": ["SUB_STATUS_PROJETO_INVOICE", "SUB_STATUS_PROJETO"],
    "sub_negociacao": ["SUB_STATUS_NEGOCIACAO"], "sub_vendas": ["SUB_STATUS_VENDAS"], "sub_cit": ["SUB_STATUS_CIT"], "sub_inmetro": ["SUB_STATUS_INMETRO"],
    "curtiu": ["CURTIU"], "nao_curtiu": ["NAO_CURTIU"],
    "supplier": ["FORNECEDOR"], "brand": ["MARCA"], "make": ["MONTADORA"], "vehicle": ["VEICULO", "MODELO"], "application": ["APLICACAO"],
    "description": ["DESCRICAO", "DESCRICAO_PRODUTO"], "line": ["LINHA"], "year_from": ["ANO_INICIAL", "ANO_INI"], "year_to": ["ANO_FINAL", "ANO_FIM"],
    "sample_bought": ["AMOSTRA_COMPRADA"], "sample_sent": ["AMOSTRA_ENVIADA"], "date_start": ["DATA_INICIO"], "pedido_confirmado": ["PEDIDO_CONFIRMADO", "DATA_PEDIDO_CONFIRMADO"],
    # validação/aprovação pelo usuário (regra de metas do REDESENVOLVIMENTO) e data em que o status mudou (regra do ano em DESENVOLVIMENTO)
    "user_valid": ["USER_VALID", "USER_APROV", "USUARIO_APROV", "USUARIO_APROVACAO", "APROVADO_POR", "VALIDADO_POR"], "date_valid": ["DATA_APROV", "DATA_APROVACAO", "DATA_VALIDACAO"],
    "status_date": ["DATA_STATUS", "DATA_MUDANCA_STATUS", "DATA_ALTERACAO_STATUS", "DATA_ULTIMA_ALTERACAO_STATUS", "DATA_ITEM_RECEBIDO", "DATA_RECEBIDO", "DATA_RECEBIMENTO", "DT_STATUS"],
}
TEXT_UPPER = ["line", "user_valid", "status", "sub_desenho", "sub_validacao", "sub_projeto", "sub_negociacao", "sub_vendas", "sub_cit", "sub_inmetro", "supplier", "brand", "make", "vehicle"]
DATE_FIELDS = ["sample_bought", "sample_sent", "date_start", "pedido_confirmado", "date_valid", "status_date"]
SUB_FIELDS = ["sub_desenho", "sub_validacao", "sub_projeto", "sub_negociacao", "sub_vendas", "sub_cit", "sub_inmetro"]

_NULLS = {"", "NULL", "NONE", "NAN", "NAT", "<NA>"}
def clean_text(v):
    """Texto limpo: sem espaços sobrando/NBSP, vazio e 'NULL' viram None."""
    if v is None: return None
    try:
        if pd.isna(v): return None
    except (TypeError, ValueError): pass
    t = re.sub(r"\s+", " ", str(v).replace("\xa0", " ")).strip()
    return None if t.upper() in _NULLS else t

def normalize_kind(v):
    """Qualquer variação ('DES', 'des ', 'Desenv.', 'R-D', 'rd', 'R/D'...) vira DESENVOLVIMENTO ou REDESENVOLVIMENTO. Desconhecido → None."""
    t = clean_text(v)
    if t is None: return None
    k = re.sub(r"[^A-Z]", "", unaccent(t).upper())
    if k.startswith("REDES") or k in ("RD", "R"): return KIND_RD
    if k.startswith("DES") or k == "D": return KIND_DES
    return None

_STATUS_CANON = {_key(s): s for s in STATUS_RANK}
_STATUS_CANON.update({_key(s): s for s in ("PENDENTE COD PERFECT",)}); _STATUS_CANON[_key("PENDENTE COD PERFECT")] = "PENDENTE COD. PERFECT"
def normalize_status(v):
    """Status em MAIÚSCULAS e com a grafia oficial (corrige acento/pontuação). Desconhecido: mantém limpo e o pipeline avisa."""
    t = clean_text(v)
    if t is None: return None
    return _STATUS_CANON.get(_key(t), t.upper())

def to_date(v):
    t = clean_text(v)
    if t is None: return None
    try:
        d = pd.to_datetime(v if not isinstance(v, str) else t, errors="coerce", dayfirst=isinstance(v, str) and bool(re.match(r"\d{1,2}/\d{1,2}/\d{4}", t)))
        return None if pd.isna(d) else d.strftime("%Y-%m-%d")
    except Exception: return None

def to_int(v):
    t = clean_text(v)
    if t is None: return None
    u = unaccent(t).upper()
    if u in ("SIM", "S", "TRUE", "VERDADEIRO", "X"): return 1
    if u in ("NAO", "N", "FALSE", "FALSO"): return 0
    try: return int(float(t.replace(",", ".")))
    except ValueError: return None

def _json_safe(v):
    t = clean_text(v)
    if t is None: return None
    if hasattr(v, "strftime"): return v.strftime("%Y-%m-%d")
    return float(v) if v.__class__.__name__ == "Decimal" else t

class NormResult:
    def __init__(self, rows, items, warnings, mapped, unmapped):
        self.rows, self.items, self.warnings, self.mapped, self.unmapped = rows, items, warnings, mapped, unmapped

def map_columns(columns, overrides=None):
    """{campo_canônico: nome_real_da_coluna}. `overrides` ({'status': 'STATUS_ITEM'}) vence o reconhecimento automático."""
    by_canon = {canon_col(c): c for c in columns}; out = {}
    for field, aliases in COLUMN_ALIASES.items():
        ov = (overrides or {}).get(field)
        if ov and ov in columns: out[field] = ov; continue
        for a in aliases:
            if a in by_canon: out[field] = by_canon[a]; break
    return out

def normalize_dev(raw, overrides=None):
    """DESENVOLVIMENTO_PRODUTOS bruto → (linhas normalizadas, itens distintos). Todas as colunas não reconhecidas vão em `extra` (nada se perde)."""
    mp = map_columns(list(raw.columns), overrides); warn = {}
    def w(k, n=1): warn[k] = warn.get(k, 0) + n
    if "code" not in mp: raise ValueError("Coluna de CÓDIGO não encontrada em DESENVOLVIMENTO_PRODUTOS. Colunas: " + ", ".join(map(str, raw.columns)))
    if "kind" not in mp: w("coluna_tipo_ausente")
    if "status" not in mp: w("coluna_status_ausente")
    mapped_cols = set(mp.values()); rows = []
    for rec in raw.to_dict("records"):
        code = clean_text(rec.get(mp["code"]))
        if not code: w("linha_sem_codigo"); continue
        r = {"code": code.upper()}
        kind = normalize_kind(rec.get(mp["kind"])) if "kind" in mp else None
        if kind is None and "kind" in mp and clean_text(rec.get(mp["kind"])): w("tipo_desconhecido")
        r["kind"] = kind
        for f in ("status", "user_valid", *SUB_FIELDS, "supplier", "brand", "make", "vehicle", "application", "description", "line"):
            v = clean_text(rec.get(mp[f])) if f in mp else None
            r[f] = (normalize_status(v) if f == "status" else v.upper() if v and f in TEXT_UPPER else v)
        for f in ("curtiu", "nao_curtiu", "year_from", "year_to"): r[f] = to_int(rec.get(mp[f])) if f in mp else None
        for f in DATE_FIELDS: r[f] = to_date(rec.get(mp[f])) if f in mp else None
        if r["status"] and r["status"] not in STATUS_RANK: w("status_novo:" + r["status"])
        r["extra"] = json.dumps({str(c): _json_safe(v) for c, v in rec.items() if c not in mapped_cols and _json_safe(v) is not None}, ensure_ascii=False)
        rows.append(r)
    cols = ["code", "kind", "status", *SUB_FIELDS, "curtiu", "nao_curtiu", "supplier", "brand", "make", "vehicle", "application", "description", "year_from", "year_to", "user_valid", *DATE_FIELDS, "extra", "line"]
    df = pd.DataFrame(rows, columns=cols)
    # DESENVOLVIMENTO e REDESENVOLVIMENTO são EXCLUSIVOS: o código que tem linha R-D (item já recebido que está sendo redesenvolvido) vale só como REDESENVOLVIMENTO — nunca aparece nos dois.
    both = df.groupby("code")["kind"].agg(lambda k: {x for x in k if x}); both = {c for c, ks in both.items() if len(ks) > 1}
    if both:
        df.loc[df["code"].isin(both) & df["kind"].notna(), "kind"] = "REDESENVOLVIMENTO"; warn["codigos_em_des_e_rd"] = len(both)
    return NormResult(df, _items(df), warn, mp, [c for c in raw.columns if c not in mapped_cols])

def _items(df):
    """Uma linha por (código, tipo): status = o mais avançado do ciclo; sub status = união dos textos; curtiu = maior valor."""
    out = []
    if df.empty: return pd.DataFrame(columns=["code", "kind", "status", "substatus", "curtiu", "nao_curtiu", "n_rows"])
    for (code, kind), g in df.groupby(["code", df["kind"].fillna("")], sort=False):
        txt = lambda x: isinstance(x, str) and x != ""       # o pandas troca None por NaN (que é "verdadeiro"): só texto de verdade conta
        sts = [s for s in g["status"] if txt(s)]; status = max(sts, key=lambda s: STATUS_RANK.get(s, -1)) if sts else None
        subs = sorted({s for f in SUB_FIELDS for s in g[f] if txt(s)})
        num = lambda c: (None if g[c].dropna().empty else int(g[c].dropna().max()))
        out.append({"code": code, "kind": kind or None, "status": status, "substatus": " / ".join(subs) or None, "curtiu": num("curtiu"), "nao_curtiu": num("nao_curtiu"), "n_rows": len(g)})
    return pd.DataFrame(out)



# ───────────────────────── compras, vendas e estoque ─────────────────────────
EX_SUPPLIERS = {"EX0002116": "ZS", "EX0002110": "E-WIN", "EX0008042": "XGM", "EX008042": "XGM"}     # código EX de cada fornecedor
DATASETS = {
    "compras": {"object": "PEDIDOS_COMPRA_DETALHADO", "table": "ds_compras", "aliases": {
        "pedido": ["PEDIDO", "NUM_PEDIDO", "NUMERO_PEDIDO", "N_PEDIDO", "ORDEM_COMPRA", "OC", "PEDIDO_COMPRA"],
        "supplier": ["FORNECEDOR", "NOME_FORNECEDOR", "RAZAO_SOCIAL", "COD_FORNECEDOR", "CODIGO_FORNECEDOR", "EX"],
        "code": ["CODIGO", "COD_PRODUTO", "CODIGO_PRODUTO", "PRODUTO", "ITEM", "CODIGO_ITEM", "COD_ITEM"],
        "description": ["DESCRICAO", "DESCRICAO_PRODUTO", "DESCRICAO_ITEM"],
        "qty_ordered": ["QTDE", "QUANTIDADE", "QTDE_PEDIDA", "QTD_PEDIDA", "QUANTIDADE_PEDIDA", "QTD", "QTDE_PEDIDO"],
        "qty_received": ["QTDE_RECEBIDA", "QTD_RECEBIDA", "QUANTIDADE_RECEBIDA", "QTDE_ENTREGUE", "QTD_ENTREGUE", "RECEBIDO", "QTDE_ATENDIDA"],
        "qty_pending": ["SALDO", "QTDE_PENDENTE", "QUANTIDADE_PENDENTE", "QTD_PENDENTE", "QTD_SALDO", "SALDO_PEDIDO", "PENDENTE"],
        "unit_price": ["PRECO", "PRECO_UNITARIO", "VALOR_UNITARIO", "VLR_UNIT", "PRECO_UNIT"],
        "total": ["VALOR_TOTAL", "TOTAL", "VLR_TOTAL", "VALOR"],
        "order_date": ["DATA_EMISSAO_PC", "DATA_PEDIDO", "DT_PEDIDO", "EMISSAO", "DATA_EMISSAO", "DATA", "DT_EMISSAO"],
        "due_date": ["DATA_PREV_ENT", "PREVISAO", "DATA_PREVISTA", "DATA_ENTREGA", "PREVISAO_ENTREGA", "DT_ENTREGA", "DT_PREVISAO", "ENTREGA_PREVISTA"],
        "received_date": ["DATA_RECEBIMENTO", "DT_RECEBIMENTO", "DATA_RECEBIDA", "DATA_ENTRADA"],
        "status": ["STATUS_PC", "STATUS", "SITUACAO", "STATUS_PEDIDO"],
        "status_imp": ["STATUS_IMP"], "line": ["LINHA"], "qty_transit": ["QTD_EM_TRANSITO"], "qty_prev_ship": ["QTD_PREV_EMBARQUE"], "supplier_name": ["FORNECEDOR_ORIGEM", "NOME_FORNECEDOR"]},
        "num": ["qty_ordered", "qty_received", "qty_pending", "unit_price", "total", "qty_transit", "qty_prev_ship"], "dates": ["order_date", "due_date", "received_date"],
        # só amortecedor (o resto do histórico de compras não é usado pelo app): filtro aplicado NO SERVIDOR
        "where": [({"LINHA", "DESCRICAO_PRODUTO"}, "(LINHA LIKE '%AMORTECEDOR%' OR DESCRICAO_PRODUTO LIKE '%AMORTECEDOR%')")]},
    "vendas": {"object": os.environ.get("DEV_DB_OBJECT_VENDAS", "VENDAS_FATURAMENTO_DETALHADO"), "alt": ["PEDIDOS_VENDA_DETALHADO"], "table": "ds_vendas", "aliases": {
        "pedido": ["PEDIDO", "NUM_PEDIDO", "NUMERO_PEDIDO", "N_PEDIDO", "PEDIDO_VENDA"],
        "customer": ["CLIENTE", "NOME_CLIENTE", "RAZAO_SOCIAL", "COD_CLIENTE", "GRUPO_CLIENTE"],
        "code": ["CODIGO", "COD_PRODUTO", "CODIGO_PRODUTO", "PRODUTO", "ITEM", "CODIGO_ITEM", "COD_ITEM"],
        "description": ["DESCRICAO", "DESCRICAO_PRODUTO", "DESCRICAO_ITEM"],
        "line": ["LINHA"],
        "qty": ["QTDE", "QUANTIDADE", "QTD", "QTDE_VENDIDA", "QTD_VENDIDA", "QUANTIDADE_VENDIDA", "QTDE_PEDIDA"],
        "unit_price": ["PRECO", "PRECO_UNITARIO", "VALOR_UNITARIO", "VLR_UNIT", "PRECO_UNIT"],
        "total": ["VALOR_TOTAL", "TOTAL", "VALOR", "VLR_TOTAL", "VALOR_LIQUIDO", "VLR_LIQUIDO", "VALOR_FATURADO", "FATURADO"],
        "sale_date": ["DATA_FATUR", "DATA_FATURAMENTO", "DT_FATURAMENTO", "DATA", "DATA_PEDIDO", "DT_PEDIDO", "EMISSAO", "DATA_EMISSAO", "DT_EMISSAO"],
        "total_net": ["VALOR_TOTAL_NET", "VL_T_NET_MENOS_DEV"], "n_customers": ["N_CLIENTES"], "grain": ["GRAO"]},
        "num": ["qty", "unit_price", "total", "total_net", "n_customers"], "dates": ["sale_date"]},
    "garantia": {"object": os.environ.get("DEV_DB_OBJECT_GARANTIA", "ANALITICO_GARANTIA_DEVOLUCAO"), "table": "ds_garantia", "aliases": {
        "code": ["CODIGO", "COD_PRODUTO", "CODIGO_PRODUTO", "COD_PROD", "PRODUTO", "ITEM", "CODIGO_ITEM", "COD_ITEM", "COD"],
        "description": ["DESCRICAO", "DESCRICAO_PRODUTO", "DESCRICAO_ITEM"],
        "defect": ["DEFEITO", "DEFEITO_RELATADO", "DEFEITO_APRESENTADO", "MOTIVO", "MOTIVO_DEVOLUCAO", "MOTIVO_GARANTIA", "PROBLEMA"],
        "qty": ["QTDE", "QUANTIDADE", "QTD", "QTDE_DEVOLVIDA", "QTD_DEVOLVIDA", "QUANTIDADE_DEVOLVIDA"],
        "event_date": ["DATA_CADASTRO", "DATA", "DATA_DEVOLUCAO", "DT_DEVOLUCAO", "DATA_ENTRADA", "DATA_GARANTIA", "DATA_EMISSAO", "DT_EMISSAO"],
        "family": ["FAMILIA"], "kind": ["TIPO_OCO"], "verdict": ["PROC_IMPROC"]},
        "num": ["qty"], "dates": ["event_date"],
        "where": [({"FAMILIA"}, "FAMILIA LIKE '%AMORTECEDOR%'")]},
    "embarques": {"object": os.environ.get("DEV_DB_OBJECT_EMBARQUES", "EMBARQUES_DETALHADO"), "table": "ds_embarques", "aliases": {
        "pedido": ["PEDIDO", "NUM_PEDIDO", "NUMERO_PEDIDO", "N_PEDIDO", "PEDIDO_COMPRA", "ORDEM_COMPRA", "OC", "NUMERO_PC", "PC"],
        "supplier": ["FORNECEDOR", "NOME_FORNECEDOR", "COD_FORNECEDOR", "CODIGO_FORNECEDOR", "EX"],
        "code": ["CODIGO", "COD_PRODUTO", "CODIGO_PRODUTO", "PRODUTO", "ITEM", "CODIGO_ITEM", "COD_ITEM"],
        "description": ["DESCRICAO", "DESCRICAO_PRODUTO", "DESCRICAO_ITEM"],
        "qty": ["QTDE", "QUANTIDADE", "QTD", "QTDE_EMBARCADA", "QTD_EMBARCADA"],
        "ship_date": ["DATA_EMBARQUE", "DT_EMBARQUE", "DATA_SAIDA", "ETD", "DATA_ETD", "EMBARQUE", "DATA_SHIPMENT", "DATA_BL"],
        "eta_date": ["ETA_ATUAL", "DATA_PREV_CHEGADA", "PREVISAO_CHEGADA", "DATA_PREVISAO_CHEGADA", "DATA_PREVISTA_CHEGADA", "PREV_CHEGADA", "ETA", "DATA_ETA", "DATA_PREV_ENT", "PREVISAO"],
        "arrival_date": ["DATA_CHEGADA_FILIAL", "DATA_CHEGADA", "DT_CHEGADA", "DATA_ENTRADA", "DATA_RECEBIMENTO", "DT_RECEBIMENTO", "DATA_NACIONALIZACAO"],
        "status": ["STATUS_MICRO", "STATUS", "SITUACAO", "STATUS_EMBARQUE"],
        "status_macro": ["STATUS_MACRO"], "etd_date": ["ETD_ATUAL"], "port_date": ["DATA_CHEGADA_PORTO"], "created_date": ["DATA_INCLUSAO"], "process": ["IP"],
        "terms": ["PRAZO"], "origin_port": ["PORTO_ORIGEM"], "transit_days": ["QTDE_DIAS"]},
        "num": ["qty", "transit_days"], "dates": ["ship_date", "eta_date", "arrival_date", "etd_date", "port_date", "created_date"],
        # só os embarques de produtos que aparecem em pedidos de compra de amortecedor (subconsulta no próprio servidor)
        # (COLLATE DATABASE_DEFAULT: as duas views usam collations diferentes no servidor — sem ele o SQL Server recusa a comparação)
        "where": [({"CODIGO_PRODUTO"}, "CODIGO_PRODUTO COLLATE DATABASE_DEFAULT IN (SELECT PRODUTO COLLATE DATABASE_DEFAULT FROM {compras} WHERE LINHA LIKE '%AMORTECEDOR%' OR DESCRICAO_PRODUTO LIKE '%AMORTECEDOR%')")]},
    "estoque": {"object": "EST DISP", "table": "ds_estoque", "aliases": {
        "code": ["CODIGO", "COD_PRODUTO", "CODIGO_PRODUTO", "PRODUTO", "ITEM", "CODIGO_ITEM", "COD_ITEM"],
        "description": ["DESCRICAO", "DESCRICAO_PRODUTO", "DESCRICAO_ITEM"],
        "warehouse": ["ARMAZEM", "DEPOSITO", "LOCAL", "ALMOXARIFADO", "FILIAL"],
        "qty": ["QTD_DISP", "DISPONIVEL", "QTDE_DISPONIVEL", "QTD_DISPONIVEL", "ESTOQUE", "SALDO", "SALDO_ESTOQUE", "QTDE", "QTD", "QUANTIDADE", "ESTOQUE_DISPONIVEL"],
        "reserved": ["RESERVA", "RESERVADO", "QTDE_RESERVADA", "EMPENHADO"], "line": ["LINHA"]},
        "num": ["qty", "reserved"], "dates": [],
        "where": [({"LINHA"}, "LINHA LIKE '%AMORTECEDOR%'")]},
}
# DESENVOLVIMENTO_PRODUTOS: só as linhas de amortecedor (as demais linhas do servidor não são usadas por nenhuma tela nem meta)
DEV_WHERE = [({"LINHA"}, "LINHA LIKE '%AMORTECEDOR%'")]

def scope_on():
    """DEV_SYNC_ESCOPO=amortecedor (padrão) aplica os filtros no servidor; «tudo» traz as views inteiras (comportamento antigo)."""
    return os.environ.get("DEV_SYNC_ESCOPO", "amortecedor").strip().lower() not in ("tudo", "all", "0", "off")

def vendas_agg_sql(obj, cols, since_month):
    """VENDAS_FATURAMENTO_DETALHADO tem milhões de linhas (≈9 mi desde 2016): o app só precisa de quantidade e valor por SKU e mês.
    O servidor soma e devolve ~1 linha por (mês, SKU, LINHA) — só amortecedor e só a partir de `since_month` (AAAA-MM). None se a view não tiver as colunas."""
    by = {canon_col(c): c for c in cols}
    val = next((by[v] for v in [canon_col(os.environ.get("DEV_VENDAS_VALOR", "VALOR_TOTAL_CIPI")), "VALOR_TOTAL_CIPI", "VL_T_CIPI_MENOS_DEV", "VALOR_TOTAL"] if v in by), None)
    need = [by.get(n) for n in ("ANO_MES", "PRODUTO", "LINHA", "QUANTIDADE")]
    if None in need or not val: return None
    am, pr, ln, qt = (qi(x) for x in need); net = f"SUM({qi(by['VALOR_TOTAL_NET'])})" if "VALOR_TOTAL_NET" in by else "NULL"
    cli = f"COUNT(DISTINCT {qi(by['CODIGO_CLIENTE'])})" if "CODIGO_CLIENTE" in by else "NULL"
    return (f"SELECT {am} AS ANO_MES, LTRIM(RTRIM({pr})) AS PRODUTO, LTRIM(RTRIM({ln})) AS LINHA, SUM({qt}) AS QTDE, SUM({qi(val)}) AS VALOR_TOTAL, {net} AS VALOR_TOTAL_NET, {cli} AS N_CLIENTES "
            f"FROM {obj['sql']} WHERE {ln} LIKE '%AMORTECEDOR%' AND {am} >= '{since_month}' GROUP BY {am}, LTRIM(RTRIM({pr})), LTRIM(RTRIM({ln}))")

def where_for(spec_where, cols, refs=None):
    """Monta o WHERE do servidor só com os filtros cujas colunas existem no objeto (o servidor de testes não tem LINHA, por exemplo). '' = sem filtro."""
    if not scope_on() or not spec_where: return ""
    have = {canon_col(c) for c in cols}; parts = []
    for need, sql in spec_where:
        if not {canon_col(n) for n in need} <= have: continue
        try: parts.append(sql.format(**(refs or {})))
        except KeyError: continue                       # subconsulta que depende de outro objeto não encontrado
    return " AND ".join(parts)
DS_COLUMNS = {k: list(v["aliases"]) for k, v in DATASETS.items()}

def to_num(v):
    t = clean_text(v)
    if t is None: return None
    try: return float(t)
    except ValueError:
        try: return float(t.replace(".", "").replace(",", "."))      # 1.234,56
        except ValueError: return None

def normalize_dataset(key, raw, overrides=None):
    """Compras/vendas/estoque brutos → tabela normalizada (código em maiúsculas, números e datas limpos). Colunas não reconhecidas vão em `extra`."""
    spec = DATASETS[key]; by_canon = {canon_col(c): c for c in raw.columns}; mp = {}
    for field, aliases in spec["aliases"].items():
        ov = (overrides or {}).get(field)
        if ov and ov in raw.columns: mp[field] = ov; continue
        for a in aliases:
            if a in by_canon: mp[field] = by_canon[a]; break
    warn = {}
    if "code" not in mp: warn["coluna_codigo_ausente"] = 1
    keep_extra = len(raw) <= int(os.environ.get("DEV_DS_EXTRA_MAX_ROWS", "50000")); other = [c for c in raw.columns if c not in mp.values()]; rows = []
    for rec in raw.to_dict("records"):
        r = {f: None for f in spec["aliases"]}
        for f, col in mp.items():
            v = rec.get(col)
            r[f] = to_num(v) if f in spec["num"] else to_date(v) if f in spec["dates"] else clean_text(v)
        if r.get("code"): r["code"] = r["code"].upper()
        if key in ("compras", "embarques"):
            blob = " ".join(str(rec.get(c) or "") for c in raw.columns if canon_col(c) in ("FORNECEDOR", "COD_FORNECEDOR", "CODIGO_FORNECEDOR", "EX", "NOME_FORNECEDOR")).upper(); m = re.search(r"EX\d{6,8}", blob)
            r["ex_code"] = m.group(0) if m else None
            if r["ex_code"] in EX_SUPPLIERS: r["supplier"] = EX_SUPPLIERS[r["ex_code"]]
            if key == "compras" and r["qty_pending"] is None and r["qty_ordered"] is not None: r["qty_pending"] = max((r["qty_ordered"] or 0) - (r["qty_received"] or 0), 0)
        r["extra"] = json.dumps({str(c): _json_safe(rec.get(c)) for c in other if _json_safe(rec.get(c)) is not None}, ensure_ascii=False) if keep_extra else None
        rows.append(r)
    cols = list(spec["aliases"]) + (["ex_code"] if key in ("compras", "embarques") else []) + ["extra"]
    return pd.DataFrame(rows, columns=cols), warn, mp

# ───────────────────────── cache local: snapshots e transições ─────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS dev_sync_runs(id INTEGER PRIMARY KEY, started_at TEXT, finished_at TEXT, status TEXT, baseline INTEGER DEFAULT 0, source_rows INTEGER, items INTEGER, events INTEGER, new_items INTEGER, removed_items INTEGER, host TEXT, error TEXT, warnings TEXT);
CREATE TABLE IF NOT EXISTS dev_rows(code TEXT, kind TEXT, status TEXT, sub_desenho TEXT, sub_validacao TEXT, sub_projeto TEXT, sub_negociacao TEXT, sub_vendas TEXT, sub_cit TEXT, sub_inmetro TEXT, curtiu INTEGER, nao_curtiu INTEGER,
  supplier TEXT, brand TEXT, make TEXT, vehicle TEXT, application TEXT, description TEXT, year_from INTEGER, year_to INTEGER, sample_bought TEXT, sample_sent TEXT, date_start TEXT, pedido_confirmado TEXT, extra TEXT);
CREATE INDEX IF NOT EXISTS ix_devrows_code ON dev_rows(code, kind);
CREATE TABLE IF NOT EXISTS dev_item_state(code TEXT NOT NULL, kind TEXT NOT NULL DEFAULT '', status TEXT, substatus TEXT, curtiu INTEGER, nao_curtiu INTEGER, present INTEGER DEFAULT 1, first_run INTEGER, last_run INTEGER, updated_at TEXT, PRIMARY KEY(code, kind));
CREATE TABLE IF NOT EXISTS dev_status_events(id INTEGER PRIMARY KEY, code TEXT NOT NULL, kind TEXT, field TEXT NOT NULL, from_value TEXT, to_value TEXT, at TEXT NOT NULL, run_id INTEGER, origin TEXT DEFAULT 'sync');
CREATE INDEX IF NOT EXISTS ix_devev_code ON dev_status_events(code, kind);
CREATE INDEX IF NOT EXISTS ix_devev_to ON dev_status_events(field, to_value, at);
CREATE TABLE IF NOT EXISTS dev_snapshot(run_id INTEGER NOT NULL, code TEXT NOT NULL, kind TEXT, status TEXT, substatus TEXT, curtiu INTEGER, nao_curtiu INTEGER);
CREATE INDEX IF NOT EXISTS ix_devsnap_run ON dev_snapshot(run_id);
CREATE TABLE IF NOT EXISTS ds_compras(pedido TEXT, supplier TEXT, code TEXT, description TEXT, qty_ordered REAL, qty_received REAL, qty_pending REAL, unit_price REAL, total REAL, order_date TEXT, due_date TEXT, received_date TEXT, status TEXT, ex_code TEXT, extra TEXT);
CREATE INDEX IF NOT EXISTS ix_dsc_code ON ds_compras(code);
CREATE TABLE IF NOT EXISTS ds_vendas(pedido TEXT, customer TEXT, code TEXT, description TEXT, line TEXT, qty REAL, unit_price REAL, total REAL, sale_date TEXT, extra TEXT);
CREATE INDEX IF NOT EXISTS ix_dsv_code ON ds_vendas(code); CREATE INDEX IF NOT EXISTS ix_dsv_date ON ds_vendas(sale_date);
CREATE TABLE IF NOT EXISTS ds_estoque(code TEXT, description TEXT, warehouse TEXT, qty REAL, reserved REAL, extra TEXT);
CREATE INDEX IF NOT EXISTS ix_dse_code ON ds_estoque(code);
CREATE TABLE IF NOT EXISTS ds_embarques(pedido TEXT, supplier TEXT, code TEXT, description TEXT, qty REAL, ship_date TEXT, eta_date TEXT, arrival_date TEXT, status TEXT, ex_code TEXT, extra TEXT);
CREATE INDEX IF NOT EXISTS ix_dse2_ped ON ds_embarques(pedido);
CREATE TABLE IF NOT EXISTS ds_garantia(code TEXT, description TEXT, defect TEXT, qty REAL, event_date TEXT, extra TEXT);
CREATE INDEX IF NOT EXISTS ix_dsg_code ON ds_garantia(code);
CREATE TABLE IF NOT EXISTS ds_runs(id INTEGER PRIMARY KEY, run_id INTEGER, dataset TEXT, object TEXT, rows INTEGER, status TEXT, note TEXT, at TEXT);
"""
TRACKED = ("status", "substatus", "curtiu", "nao_curtiu")
ROW_COLS = ["code", "kind", "status", "sub_desenho", "sub_validacao", "sub_projeto", "sub_negociacao", "sub_vendas", "sub_cit", "sub_inmetro", "curtiu", "nao_curtiu", "supplier", "brand", "make", "vehicle",
            "application", "description", "year_from", "year_to", "sample_bought", "sample_sent", "date_start", "pedido_confirmado", "extra"]

def now(): return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def _nn(v):
    try:
        if pd.isna(v): return None
    except (TypeError, ValueError): pass
    return v.item() if hasattr(v, "item") else v

class Store:
    def __init__(self, path=None):
        if path is None:
            try:
                import database; path = database.DB_PATH
            except Exception: path = os.path.join(BASE, "data", "pipeline_cache.db")
        self.path = path; os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        c = self.conn(); c.executescript(SCHEMA)
        for key, spec in DATASETS.items():          # colunas novas (bancos criados antes): LINHA, status de importação, datas do embarque, valor líquido...
            have = {r[1] for r in c.execute(f"PRAGMA table_info({spec['table']})")}
            for f in spec["aliases"]:
                if f not in have: c.execute(f"ALTER TABLE {spec['table']} ADD COLUMN {f} {'REAL' if f in spec['num'] else 'TEXT'}")
        for tbl in ("ds_runs", "dev_sync_runs"):
            if "scope" not in {r[1] for r in c.execute(f"PRAGMA table_info({tbl})")}: c.execute(f"ALTER TABLE {tbl} ADD COLUMN scope TEXT")
        c.commit(); c.close()
    def conn(self):
        c = sqlite3.connect(self.path, timeout=30); c.row_factory = sqlite3.Row; return c

    def backup(self, label="pre_servidor"):
        """Cópia de segurança do banco inteiro (API de backup do SQLite) antes de trocar a fonte oficial."""
        here = os.path.abspath(self.path); d = os.path.join(BASE, "backups") if here.startswith(BASE) else os.path.join(os.path.dirname(here), "backups"); os.makedirs(d, exist_ok=True)
        dst = os.path.join(d, f"{label}_{datetime.datetime.now():%Y%m%d_%H%M%S}.db"); src = self.conn(); out = sqlite3.connect(dst)
        try: src.backup(out)
        finally: out.close(); src.close()
        return dst

    SRC_NAME = "Servidor SQL — DESENVOLVIMENTO_PRODUTOS"

    def has_published(self):
        c = self.conn()
        try: return c.execute("SELECT 1 FROM sources WHERE name=?", (self.SRC_NAME,)).fetchone() is not None
        except sqlite3.Error: return False
        finally: c.close()

    def _publish(self, c, res, run_id, cfg):
        """Troca o conteúdo de rd_projects (usado por Desenvolvimento/Redesenvolvimento) pelo que veio do servidor. Roda na MESMA transação da sincronização."""
        cols = {r[1] for r in c.execute("PRAGMA table_info(rd_projects)")}
        if "project_substatus" not in cols: return {"publicado": False, "motivo": "banco do app ainda sem as colunas novas (abra o app uma vez)"}
        rows = res.rows[res.rows["kind"].map(lambda v: isinstance(v, str))]
        skipped = len(res.rows) - len(rows); new_items = rows.drop_duplicates(["code", "kind"]).shape[0]
        first = c.execute("SELECT 1 FROM sources WHERE name=?", (self.SRC_NAME,)).fetchone() is None
        old_items = c.execute("SELECT COUNT(*) FROM (SELECT DISTINCT code, suggestion FROM rd_projects)").fetchone()[0]
        if first and old_items and new_items < old_items * cfg.min_ratio and os.environ.get("DEV_SYNC_FORCE_PUBLISH") != "1":
            return {"publicado": False, "motivo": f"1ª publicação bloqueada: o servidor trouxe {new_items} itens contra {old_items} já cadastrados (limite {int(cfg.min_ratio*100)}%). Confira o servidor ou defina DEV_SYNC_FORCE_PUBLISH=1."}
        src = c.execute("SELECT id FROM sources WHERE name=?", (self.SRC_NAME,)).fetchone()
        src_id = src[0] if src else c.execute("INSERT INTO sources(name,category,priority) VALUES(?,?,?)", (self.SRC_NAME, "Servidor SQL", 1)).lastrowid
        legacy = [r[0] for r in c.execute("SELECT id FROM sources WHERE name LIKE 'DadosR-D%' OR name LIKE 'DadosDES%' OR id=?", (src_id,))]
        bid = c.execute("INSERT INTO import_batches(source_id,filename,sheet,category,rows_read,rows_new,rows_updated,rows_conflict,rows_error,status) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (src_id, cfg.dev_object, None, "Servidor SQL", len(res.rows), len(rows), 0, 0, skipped, "ok")).lastrowid
        pmap = {str(code).upper(): pid for pid, code in c.execute("SELECT id,perfect_code FROM products")}
        c.execute("DELETE FROM rd_projects"); c.execute(f"DELETE FROM applications WHERE source_id IN ({','.join('?' * len(legacy))})", legacy)
        try: import loaders; axle_side = loaders._axle_side
        except Exception: axle_side = lambda d: (None, None)
        seen, n_app = set(), 0; names = {"sub_negociacao": "SUB STATUS NEGOCIAÇÃO", "sub_vendas": "SUB STATUS VENDAS", "sub_cit": "SUB STATUS CIT", "date_start": "DATA INICIO", "pedido_confirmado": "PEDIDO CONFIRMADO", "user_valid": "USER APROV", "date_valid": "DATA APROV", "line": "LINHA", "status_date": "DATA STATUS"}
        out = []
        for r in rows.to_dict("records"):
            ex = json.loads(r["extra"]) if isinstance(r.get("extra"), str) and r["extra"] else {}
            for f, label in names.items():
                if isinstance(r.get(f), str) and r[f]: ex.setdefault(label, r[f])
            ex = {k: v for k, v in ex.items()}
            t = lambda f: r[f] if isinstance(r.get(f), str) and r[f] else None
            iv = lambda f: None if r.get(f) is None or r.get(f) != r.get(f) else int(r[f])
            pid = pmap.get(r["code"]); out.append((r["code"], pid, r["kind"], t("status"), t("sub_desenho"), t("sub_validacao"), t("supplier"), t("sample_bought"), t("sample_sent"), src_id, bid, t("make"), t("vehicle"), t("application"), iv("year_from"), iv("year_to"),
                                                  t("description"), t("brand"), t("sub_projeto"), t("sub_inmetro"), iv("curtiu"), iv("nao_curtiu"), json.dumps(ex, ensure_ascii=False) if ex else None, t("line")))
            if pid:
                ax, sd = axle_side(t("description")); k = (pid, t("make"), t("vehicle"), t("application"), iv("year_from"), iv("year_to"), ax, sd)
                if k not in seen:
                    seen.add(k); n_app += 1
                    c.execute("INSERT INTO applications(product_id,make,model,application_text,year_from,year_to,axle,side,source_id) VALUES(?,?,?,?,?,?,?,?,?)", (pid, k[1], k[2], k[3], k[4], k[5], ax, sd, src_id))
        c.executemany("INSERT INTO rd_projects(code,product_id,suggestion,status,drawing_substatus,validation_substatus,supplier,sample_bought,sample_sent,source_id,batch_id,make,vehicle,application_text,year_from,year_to,description,brand,project_substatus,inmetro_substatus,curtiu,nao_curtiu,extra,line) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", out)
        return {"publicado": True, "linhas": len(out), "itens": int(new_items), "sem_tipo": int(skipped), "aplicacoes": n_app}

    def _last_scope(self, c, key):
        r = c.execute("SELECT scope FROM ds_runs WHERE dataset=? AND status='ok' ORDER BY id DESC LIMIT 1", (key,)).fetchone()
        return r[0] if r else None

    def replace_dataset(self, key, df, run_id, object_name, cfg, scope=None, since=None):
        """Compras/vendas/estoque: troca a tabela local pelo que veio agora (trava: não aceita menos de 50% do que havia).
        A trava não vale quando o FILTRO mudou (ex.: passou a trazer só amortecedor: a queda de linhas é esperada).
        `since` (vendas): carga INCREMENTAL — só os meses a partir de `since` (AAAA-MM-DD) são trocados; o histórico anterior fica como está."""
        tbl = DATASETS[key]["table"]; c = self.conn()
        try:
            same_scope = self._last_scope(c, key) == scope
            cond, par = ("WHERE sale_date >= ? OR sale_date IS NULL", (since,)) if since else ("", ())
            prev = c.execute(f"SELECT COUNT(*) FROM {tbl} {cond}", par).fetchone()[0]
            if same_scope and prev and len(df) < prev * cfg.min_ratio:
                note = f"bloqueado: {len(df)} linhas contra {prev} antes"; c.execute("INSERT INTO ds_runs(run_id,dataset,object,rows,status,note,at,scope) VALUES(?,?,?,?,?,?,?,?)", (run_id, key, object_name, len(df), "bloqueado", note, now(), scope)); c.commit(); return {"status": "bloqueado", "note": note, "rows": prev}
            have = [r[1] for r in c.execute(f"PRAGMA table_info({tbl})")]; use = [x for x in df.columns if x in have]
            if not same_scope and since: cond, par = "", ()           # mudou o formato (ex.: de linhas para totais por mês): recarrega a janela inteira
            c.execute(f"DELETE FROM {tbl} {cond}", par)
            c.executemany(f"INSERT INTO {tbl}({','.join(use)}) VALUES({','.join('?' * len(use))})", [tuple(_nn(v) for v in r) for r in df[use].itertuples(index=False, name=None)])
            note = (f"incremental desde {since[:7]}" if since and same_scope else None) or (None if same_scope else "filtro/escopo novo: tabela recarregada")
            c.execute("INSERT INTO ds_runs(run_id,dataset,object,rows,status,note,at,scope) VALUES(?,?,?,?,?,?,?,?)", (run_id, key, object_name, len(df), "ok", note, now(), scope)); c.commit()
            return {"status": "ok", "rows": len(df), **({"note": note} if note else {})}
        except Exception:
            c.rollback(); raise
        finally: c.close()

    def vendas_since(self, scope, years=3):
        """Início da janela de vendas a buscar: com a mesma consulta já carregada, só o mês anterior em diante (o que ainda pode mudar); senão `years` anos completos."""
        c = self.conn()
        try:
            full = f"{datetime.date.today().year - years + 1}-01-01"
            if self._last_scope(c, "vendas") != scope: return full, True
            m = c.execute("SELECT MAX(sale_date) FROM ds_vendas").fetchone()[0]
            if not m: return full, True
            d = datetime.date(int(m[:4]), int(m[5:7]), 1) - datetime.timedelta(days=1)
            return max(f"{d.year}-{d.month:02d}-01", full), False
        finally: c.close()

    def last_sync(self):
        """Para o topo da tela: data da última sincronização e se deu certo."""
        c = self.conn()
        try:
            ok = c.execute("SELECT * FROM dev_sync_runs WHERE status='ok' ORDER BY id DESC LIMIT 1").fetchone(); last = c.execute("SELECT * FROM dev_sync_runs ORDER BY id DESC LIMIT 1").fetchone()
            return {"last_ok_at": ok["finished_at"] if ok else None, "last_status": last["status"] if last else None, "last_error": last["error"] if last and last["status"] != "ok" else None,
                    "items": ok["items"] if ok else 0, "runs": c.execute("SELECT COUNT(*) FROM dev_sync_runs WHERE status='ok'").fetchone()[0]}
        finally: c.close()

    def log_error(self, cfg, started, err):
        c = self.conn(); c.execute("INSERT INTO dev_sync_runs(started_at,finished_at,status,host,error) VALUES(?,?,?,?,?)", (started, now(), "erro", cfg.host, cfg.masked(err)[:1000])); c.commit(); c.close()

    def apply(self, cfg, res, started, publish=True, scope="tudo"):
        """Grava o resultado numa única transação: espelho das linhas, estado dos itens, eventos de transição e snapshot. Retorna o resumo.
        `scope` = filtro usado no servidor (ex.: só LINHA amortecedor). Quando ele muda, a trava de 50% não se aplica e os itens que ficaram FORA do filtro
        saem do estado em silêncio (não foram removidos do servidor, só deixaram de ser buscados — não geram evento «ausente»)."""
        c = self.conn(); items = res.items
        try:
            prev = {(r["code"], r["kind"] or ""): dict(r) for r in c.execute("SELECT * FROM dev_item_state")}
            last = c.execute("SELECT scope FROM dev_sync_runs WHERE status='ok' ORDER BY id DESC LIMIT 1").fetchone()
            had_ok = last is not None; changed = had_ok and (last[0] or "tudo") != scope
            n_prev = sum(1 for p in prev.values() if p["present"])
            if had_ok and not changed and n_prev and len(items) < n_prev * cfg.min_ratio:
                raise RuntimeError(f"Carga suspeita: {len(items)} itens contra {n_prev} na sincronização anterior (limite {int(cfg.min_ratio*100)}%). Nada foi alterado.")
            if changed:
                keep = {(r["code"], r["kind"] if isinstance(r["kind"], str) and r["kind"] else "") for r in items.to_dict("records")}
                gone = [k for k in prev if k not in keep]
                c.executemany("DELETE FROM dev_item_state WHERE code=? AND kind=?", gone); prev = {k: v for k, v in prev.items() if k in keep}
                res.warnings["escopo_alterado"] = f"filtro do servidor mudou: {len(gone)} itens fora do novo filtro deixaram de ser acompanhados"
            baseline = 0 if had_ok else 1; at = now()
            run_id = c.execute("INSERT INTO dev_sync_runs(started_at,status,baseline,host,scope) VALUES(?,?,?,?,?)", (started, "rodando", baseline, cfg.host, scope)).lastrowid
            events, new_items, removed = [], 0, 0; seen = set()
            for it in items.to_dict("records"):
                it["kind"] = it["kind"] if isinstance(it["kind"], str) and it["kind"] else None      # NaN do pandas -> None
                key = (it["code"], it["kind"] or ""); seen.add(key); new = {k: _nn(it.get(k)) for k in TRACKED}; old = prev.get(key)
                if old is None:
                    new_items += 1
                    if not baseline: events.append((it["code"], it["kind"], "status", None, new["status"], at, run_id, "novo_item"))
                    c.execute("INSERT INTO dev_item_state(code,kind,status,substatus,curtiu,nao_curtiu,present,first_run,last_run,updated_at) VALUES(?,?,?,?,?,?,1,?,?,?)", (it["code"], it["kind"] or "", new["status"], new["substatus"], new["curtiu"], new["nao_curtiu"], run_id, run_id, at))
                    continue
                if not old["present"]: events.append((it["code"], it["kind"], "presenca", "AUSENTE", "PRESENTE", at, run_id, "sync"))
                for f in TRACKED:
                    if old[f] != new[f]: events.append((it["code"], it["kind"], f, old[f], new[f], at, run_id, "sync"))
                c.execute("UPDATE dev_item_state SET status=?,substatus=?,curtiu=?,nao_curtiu=?,present=1,last_run=?,updated_at=? WHERE code=? AND kind=?", (new["status"], new["substatus"], new["curtiu"], new["nao_curtiu"], run_id, at if any(old[f] != new[f] for f in TRACKED) else old["updated_at"], it["code"], it["kind"] or ""))
            for key, old in prev.items():       # sumiu da view: marca ausente (não apaga o histórico)
                if key not in seen and old["present"]:
                    removed += 1; events.append((key[0], key[1] or None, "presenca", "PRESENTE", "AUSENTE", at, run_id, "sync")); c.execute("UPDATE dev_item_state SET present=0,updated_at=? WHERE code=? AND kind=?", (at, key[0], key[1]))
            if baseline and cfg.backfill:       # opcional e DESLIGADO por padrão: usa a coluna de data de PEDIDO CONFIRMADO como evento retroativo
                for r in res.rows.dropna(subset=["pedido_confirmado"]).drop_duplicates(["code", "kind"]).to_dict("records"):
                    events.append((r["code"], _nn(r["kind"]) if isinstance(r["kind"], str) else None, "status", None, "PEDIDO CONFIRMADO", r["pedido_confirmado"] + " 00:00:00", run_id, "backfill_coluna"))
            c.executemany("INSERT INTO dev_status_events(code,kind,field,from_value,to_value,at,run_id,origin) VALUES(?,?,?,?,?,?,?,?)", events)
            c.execute("DELETE FROM dev_rows")
            c.executemany(f"INSERT INTO dev_rows({','.join(ROW_COLS)}) VALUES({','.join('?' * len(ROW_COLS))})", [tuple(_nn(v) for v in r) for r in res.rows[ROW_COLS].itertuples(index=False, name=None)])
            c.executemany("INSERT INTO dev_snapshot(run_id,code,kind,status,substatus,curtiu,nao_curtiu) VALUES(?,?,?,?,?,?,?)", [(run_id, r["code"], r["kind"] if isinstance(r["kind"], str) else None, _nn(r["status"]), _nn(r["substatus"]), _nn(r["curtiu"]), _nn(r["nao_curtiu"])) for r in items.to_dict("records")])
            c.execute("UPDATE dev_sync_runs SET finished_at=?,status='ok',source_rows=?,items=?,events=?,new_items=?,removed_items=?,warnings=? WHERE id=?", (now(), len(res.rows), len(items), len(events), new_items, removed, json.dumps(res.warnings, ensure_ascii=False), run_id))
            pub = self._publish(c, res, run_id, cfg) if publish else {"publicado": False, "motivo": "desligado"}
            if not pub.get("publicado") and pub.get("motivo"): res.warnings["publicacao"] = pub["motivo"]
            c.execute("UPDATE dev_sync_runs SET warnings=? WHERE id=?", (json.dumps(res.warnings, ensure_ascii=False), run_id))
            self._prune(c)
            c.commit()
            return {"run_id": run_id, "baseline": bool(baseline), "events": len(events), "new_items": new_items, "removed_items": removed, "publicacao": pub}
        except Exception:
            c.rollback(); raise
        finally: c.close()

    def _prune(self, c, keep_days=400):
        """Snapshots: guarda o último de cada dia e descarta os mais antigos que `keep_days` (eventos nunca são apagados)."""
        old = (datetime.date.today() - datetime.timedelta(days=keep_days)).isoformat()
        runs = c.execute("SELECT id, substr(finished_at,1,10) d FROM dev_sync_runs WHERE status='ok' ORDER BY id").fetchall(); lastday = {}
        for r in runs: lastday[r["d"]] = r["id"]
        drop = [r["id"] for r in runs if lastday[r["d"]] != r["id"] or r["d"] < old]
        if drop: c.execute(f"DELETE FROM dev_snapshot WHERE run_id IN ({','.join('?' * len(drop))})", drop)


# ───────────────────────── orquestração ─────────────────────────
_LOCK = threading.Lock()
_STATE = {"running": False, "started": None, "last": None, "next_at": None}

LOCK_STALE_S = 45 * 60          # trava mais velha que isso = processo que morreu no meio (a 1ª carga completa leva ~8 min)

def lock_path(store):
    return os.path.join(os.path.dirname(os.path.abspath(store.path)), "sincronizacao.lock")

def _take_file_lock(path):
    """Trava ENTRE PROCESSOS (tarefa agendada do Windows × app aberto): cria o arquivo de forma atômica; False se outro processo já tem a trava."""
    try:
        if time.time() - os.path.getmtime(path) > LOCK_STALE_S: os.remove(path)
    except OSError: pass
    try: fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError: return False
    with os.fdopen(fd, "w") as fh: fh.write(f"pid={os.getpid()} desde={now()}\n")
    return True

def sync(cfg=None, store=None, conn_factory=None):
    """Sincroniza: servidor → normalização → snapshot/transições → publica em rd_projects → compras/vendas/estoque.
    Nunca levanta exceção para quem chama: devolve {'ok': False, 'error': ...} e mantém os dados anteriores. Só roda uma por vez (no processo e entre processos)."""
    if not _LOCK.acquire(blocking=False): return {"ok": False, "error": "Já existe uma sincronização em andamento."}
    try:
        store = store or Store(); lp = lock_path(store)
        if not _take_file_lock(lp): return {"ok": False, "error": "Já existe uma sincronização em andamento (em outro processo: tarefa agendada ou outra janela do app)."}
        _STATE.update(running=True, started=now())
        try:
            out = _sync(cfg, store, conn_factory); _STATE["last"] = {k: out.get(k) for k in ("ok", "error", "finished_at", "items", "events")}; return out
        finally:
            _STATE["running"] = False
            try: os.remove(lp)
            except OSError: pass
    finally: _LOCK.release()

def _sync(cfg, store, conn_factory):
    load_env(); cfg = cfg or Config(); store = store or Store(); t0 = time.time(); started = now(); conn = None
    try:
        conn = (conn_factory or connect)(cfg)
        wanted = [cfg.dev_object] + [n for d in DATASETS.values() for n in [d["object"], *d.get("alt", [])]]
        found = locate(conn, wanted, cfg)
        if cfg.dev_object not in found: raise RuntimeError(f"Tabela/view {cfg.dev_object} não encontrada no servidor {cfg.host} (login {cfg.user}). Rode 'python data_pipeline.py probe' e confira o banco/esquema (DEV_DB_NAME / DEV_DB_SCHEMA).")
        dl = dialect_for(conn); cols_of = lambda o: [c for c, _ in dl.columns(conn, o["db"], o["schema"], o["name"])]
        dev_where = where_for(DEV_WHERE, cols_of(found[cfg.dev_object]))
        raw = extract_raw(conn, found[cfg.dev_object], where=dev_where); res = normalize_dev(raw, cfg.column_overrides)
        backup = None
        if not store.has_published():       # 1ª vez que o servidor vira a fonte oficial: guarda uma cópia do banco antes de trocar
            try: backup = store.backup("pre_servidor")
            except Exception as e: log.warning("backup falhou: %s", e)
        out = store.apply(cfg, res, started, scope=dev_where or "tudo")
        dss = {}; only = {x.strip().lower() for x in os.environ.get("DEV_SYNC_DATASETS", "").split(",") if x.strip()}
        objs = {k: found.get(s["object"]) or next((found[a] for a in s.get("alt", []) if a in found), None) for k, s in DATASETS.items()}
        refs = {k: o["sql"] for k, o in objs.items() if o}
        for key, spec in DATASETS.items():     # compras, vendas, embarques, estoque e garantia: falha de um não derruba os outros
            obj = objs[key]
            if only and key not in only: dss[key] = {"status": "pulado", "note": "fora de DEV_SYNC_DATASETS"}; continue
            if not obj: dss[key] = {"status": "ausente", "note": f"{spec['object']} não encontrado"}; continue
            try:
                cols = cols_of(obj); ov = json.loads(os.environ.get(f"DEV_DB_COLUMNS_{key.upper()}", "") or "{}")
                probe_sql = vendas_agg_sql(obj, cols, "2000-01") if key == "vendas" and scope_on() else None
                if probe_sql:        # vendas: totais por mês × SKU calculados NO SERVIDOR, só os meses que ainda podem mudar (incremental)
                    since, full = store.vendas_since(probe_sql, int(os.environ.get("DEV_VENDAS_ANOS", "3")))
                    raw_v = extract_raw(conn, obj, sql=vendas_agg_sql(obj, cols, since[:7]))
                    raw_v["DATA"] = raw_v["ANO_MES"].astype(str).str.strip() + "-01"; raw_v["GRAO"] = "mes"
                    df, warn, mp = normalize_dataset(key, raw_v, ov)
                    dss[key] = {**store.replace_dataset(key, df, out["run_id"], obj["sql"], cfg, scope=probe_sql, since=since), "mapped": sorted(mp), "avisos": warn, "desde": since[:7], "completa": full}
                    continue
                where = where_for(spec.get("where"), cols, refs)
                df, warn, mp = normalize_dataset(key, extract_raw(conn, obj, where=where, limit=None if where else int(os.environ.get("DEV_DS_MAX_ROWS", "300000"))), ov)
                dss[key] = {**store.replace_dataset(key, df, out["run_id"], obj["sql"], cfg, scope=where or "tudo"), "mapped": sorted(mp), "avisos": warn, "filtro": where or None}
            except Exception as e: dss[key] = {"status": "erro", "note": cfg.masked(f"{e.__class__.__name__}: {e}")}
        if (dss.get("compras") or {}).get("status") == "ok":      # guarda a data prevista de cada pedido: mostra quantas vezes o fornecedor empurrou a previsão
            try: import leadtime; dss["compras"]["previsoes_gravadas"] = leadtime.snapshot_due()
            except Exception as e: log.warning("histórico de previsões falhou: %s", e)
        return {"ok": True, **out, "source_rows": len(res.rows), "items": len(res.items), "warnings": res.warnings, "unmapped_columns": len(res.unmapped), "datasets": dss, "backup": backup,
                "object": found[cfg.dev_object]["sql"], "seconds": round(time.time() - t0, 1), "finished_at": now()}
    except Exception as e:
        msg = cfg.masked(f"{e.__class__.__name__}: {e}")
        try: store.log_error(cfg, started, msg)
        except Exception: pass
        log.error("Sincronização falhou: %s", msg); return {"ok": False, "error": msg}
    finally:
        try: conn and conn.close()
        except Exception: pass

def sync_async(on_done=None, **kw):
    """Dispara a sincronização em segundo plano (a tela consulta o andamento em status()). False se já houver uma rodando."""
    if _STATE["running"] or _LOCK.locked(): return False
    def run():
        r = sync(**kw)
        if on_done:
            try: on_done(r)
            except Exception: log.exception("on_done falhou")
    threading.Thread(target=run, name="pipeline-sync", daemon=True).start(); return True

def status(store=None):
    """Tudo que a tela precisa: rodando?, última sincronização (topo direito), próxima agendada e se o .env está preenchido."""
    load_env(); cfg = Config(); st = store or Store()
    return {"running": _STATE["running"], "started": _STATE["started"], "next_at": _STATE["next_at"], "configured": bool(cfg.user and cfg.password), "host": cfg.host, **st.last_sync(), "drivers": available_drivers()}

def available_drivers():
    out = []
    for mod in ("pymssql", "pyodbc"):
        try: __import__(mod); out.append(mod)
        except Exception: pass
    return out

def sync_at():
    """Horário fixo da sincronização DIÁRIA (DEV_SYNC_AT=HH:MM, padrão 06:30). Vazio = volta ao modo «a cada DEV_SYNC_HOURS horas»."""
    t = os.environ.get("DEV_SYNC_AT", "06:30").strip()
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", t)
    return datetime.time(int(m.group(1)), int(m.group(2))) if m and int(m.group(1)) < 24 and int(m.group(2)) < 60 else None

def is_due(last_ok, now_=None, hours=24.0, at=None):
    """Precisa sincronizar agora? Modo diário (at): 1× por dia, a partir do horário marcado (se o app abrir depois dele, roda logo ao abrir).
    Modo intervalo (at=None): quando a última foi há mais de `hours` horas."""
    now_ = now_ or datetime.datetime.now()
    if not last_ok: return True
    last = datetime.datetime.strptime(last_ok, "%Y-%m-%d %H:%M:%S")
    if at: return last.date() < now_.date() and now_.time() >= at
    return (now_ - last).total_seconds() >= hours * 3600 - 60

def next_run(last_ok, now_=None, hours=24.0, at=None):
    now_ = now_ or datetime.datetime.now()
    if is_due(last_ok, now_, hours, at): return now_
    if at:
        d = now_.date() if now_.time() < at and (not last_ok or last_ok[:10] < now_.date().isoformat()) else now_.date() + datetime.timedelta(days=1)
        return datetime.datetime.combine(d, at)
    return datetime.datetime.strptime(last_ok, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=hours)

def daily(cfg=None, store=None, conn_factory=None, now_=None):
    """Usada pela tarefa agendada do Windows (sincronizar.bat): sincroniza só se ainda não houve sincronização OK hoje
    (o app aberto pode ter feito antes). 2 min de folga para a tarefa que dispara segundos antes do horário."""
    load_env(); store = store or Store(); now_ = now_ or datetime.datetime.now(); at = sync_at()
    last = store.last_sync().get("last_ok_at")
    if not is_due(last, now_ + datetime.timedelta(minutes=2), float(os.environ.get("DEV_SYNC_HOURS", "24") or 24), at):
        return {"ok": True, "pulada": True, "motivo": f"já sincronizado hoje ({last})", "last_ok_at": last}
    return sync(cfg, store, conn_factory)

def start_scheduler(interval_hours=None, conn_factory=None, on_done=None, first_delay=20):
    """Sincronização DIÁRIA automática: uma vez por dia no horário DEV_SYNC_AT (padrão 06:30; se o app abrir depois, roda ~20 s após abrir).
    Só busca no servidor o que o app usa (DES/R-D e, de compras/vendas/embarques/estoque/garantia, só amortecedor; vendas de forma incremental). DEV_SYNC_HOURS=0 desliga."""
    load_env(); hours = float(interval_hours or os.environ.get("DEV_SYNC_HOURS", "24"))
    if hours <= 0: return None
    def loop():
        time.sleep(first_delay)
        while True:
            try:
                cfg = Config(); at = sync_at()
                if cfg.user and cfg.password:
                    last = Store().last_sync().get("last_ok_at")
                    if is_due(last, hours=hours, at=at): r = sync(conn_factory=conn_factory); on_done and on_done(r); last = Store().last_sync().get("last_ok_at")
                    _STATE["next_at"] = next_run(last, hours=hours, at=at).strftime("%Y-%m-%d %H:%M:%S")
            except Exception: log.exception("agendador")
            time.sleep(600)          # confere a cada 10 min se já chegou a hora
    t = threading.Thread(target=loop, name="pipeline-scheduler", daemon=True); t.start(); return t

def probe(cfg=None, conn_factory=None, names=None):
    """Diagnóstico para rodar na rede da empresa: lista os objetos esperados, colunas, contagem e como as colunas de DESENVOLVIMENTO_PRODUTOS foram reconhecidas."""
    load_env(); cfg = cfg or Config(); names = names or ["ANALITICO_GARANTIA_DEVOLUCAO", "APONTAMENTOS_OP", "DESENVOLVIMENTO_PRODUTOS", "EMBARQUES_DETALHADO", "EST DISP", "ESTOQUE_ANALISE_REPOSICAO", "FECHAMENTO_CUSTOS",
                                                      "PEDIDOS_COMPRA_DETALHADO", "PEDIDOS_VENDA_DETALHADO", "TABELA_DE_PRECOS", "TABELA_DE_PRECOS_FORNECEDOR_RED", "VENDAS_FATURAMENTO_DETALHADO"]
    conn = (conn_factory or connect)(cfg)
    try:
        dl = dialect_for(conn); found = locate(conn, names, cfg, dl); rep = {"host": cfg.host, "drivers": available_drivers(), "found": {}, "missing": [n for n in names if n not in found]}
        for n, o in found.items():
            cols = dl.columns(conn, o["db"], o["schema"], o["name"]); cur = conn.cursor()
            try: cur.execute(assert_select(f"SELECT COUNT(*) FROM {o['sql']}")); n_rows = cur.fetchone()[0]
            finally: cur.close()
            rep["found"][n] = {"onde": o["sql"], "tipo": o["type"], "linhas": n_rows, "colunas": [f"{c} ({t})" for c, t in cols]}
            if n == cfg.dev_object: rep["found"][n]["reconhecimento"] = {"mapeadas": map_columns([c for c, _ in cols], cfg.column_overrides), "vao_para_extra": [c for c, _ in cols if c not in map_columns([c for c, _ in cols], cfg.column_overrides).values()]}
            for k, spec in DATASETS.items():
                if _key(n) in {_key(spec["object"]), *map(_key, spec.get("alt", []))}:
                    by = {canon_col(c): c for c, _ in cols}; rep["found"][n]["reconhecimento"] = {f: next((by[a] for a in al if a in by), None) for f, al in spec["aliases"].items()}
        return rep
    finally: conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s"); cmd = (sys.argv[1] if len(sys.argv) > 1 else "status").lower()
    if cmd == "probe": print(json.dumps(probe(), ensure_ascii=False, indent=2, default=str))
    elif cmd == "sync": print(json.dumps(sync(), ensure_ascii=False, indent=2, default=str))
    elif cmd == "diaria":        # tarefa agendada: só sincroniza se ainda não houve hoje; saída 1 = falhou (o Agendador mostra o código)
        r = daily(); print(json.dumps({k: v for k, v in r.items() if k != "datasets"}, ensure_ascii=False, indent=2, default=str)); sys.exit(0 if r.get("ok") else 1)
    else: load_env(); print(json.dumps(Store().last_sync(), ensure_ascii=False, indent=2))
