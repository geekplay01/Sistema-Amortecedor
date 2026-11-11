"""Regras de negócio configuráveis (valores padrão = o que foi definido pela diretoria).
  • Só entram nas listas, contadores e metas os itens cuja DESCRIÇÃO contém «AMORTECEDOR»  (ONLY_DESCRIPTION no .env; vazio = desliga).
  • REDESENVOLVIMENTO só conta se o item tiver a marca de validação/aprovação do usuário ITALOC (GOAL_VALID_USER no .env).
"""
import os, re

_CACHE = {"t": 0.0, "db": None, "v": {}}
def _setting(key):
    """Valor gravado na tela de Configurações (aba Administração); None se não houver. Nunca levanta erro.
    Cache curto (3 s, zerado ao salvar): antes cada linha de item abria uma conexão SQLite só para ler a regra (milhares por tela = ~8 s de espera)."""
    import time
    try:
        import database as _d
        if _CACHE["db"] != _d.DB_PATH or time.time() - _CACHE["t"] > 3: _CACHE.update(t=time.time(), db=_d.DB_PATH, v={})
    except Exception: pass
    if key in _CACHE["v"]: return _CACHE["v"][key]
    v = _setting_db(key); _CACHE["v"][key] = v; return v

def _setting_db(key):
    try:
        import database as db
        c = db.conn()
        try: c.execute("CREATE TABLE IF NOT EXISTS app_settings(key TEXT PRIMARY KEY, value TEXT, updated_by TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)"); r = c.execute("SELECT value FROM app_settings WHERE key=?", (key,)).fetchone()
        finally: c.close()
        return r[0] if r else None
    except Exception: return None

def set_setting(key, value, by=None):
    import database as db
    c = db.conn()
    try:
        c.execute("CREATE TABLE IF NOT EXISTS app_settings(key TEXT PRIMARY KEY, value TEXT, updated_by TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        c.execute("INSERT INTO app_settings(key,value,updated_by) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_by=excluded.updated_by,updated_at=CURRENT_TIMESTAMP", (key, value, by)); c.commit()
    finally: c.close()
    _CACHE.update(t=0.0, v={})

def only_desc():
    v = _setting("only_description")
    return (v if v is not None else os.environ.get("ONLY_DESCRIPTION", "AMORTECEDOR")).strip().upper()

LINE_EXCLUDE = ("COX", "KAD")          # linhas COX (coxim) e KAD: não entram nas listas nem nas metas

def desc_sql(col="description"):
    """Condição SQL que define o UNIVERSO de Desenvolvimento/Redesenvolvimento: só a linha «AMORTECEDOR» e «AMORTECEDOR LINHA PESADA» (coluna LINHA do servidor);
    COX e KAD ficam de fora. `col` carrega o alias da tabela («r.description» → usa r.line e r.code). Enquanto a coluna LINHA não veio do servidor (banco antigo), vale a descrição
    contendo o texto da regra — sempre sem itens COX/KAD."""
    t = re.sub(r"[^A-Z0-9 ]", "", only_desc())
    if not t: return "1=1"
    pre = col[:-len("description")] if col.endswith("description") else ""
    ln, cd, ds = f"upper(trim(coalesce({pre}line,'')))", f"upper(coalesce({pre}code,''))", f"upper(coalesce({col},''))"
    ex = " AND ".join(f"{cd} NOT LIKE '{x}%' AND {ds} NOT LIKE '{x}%'" for x in LINE_EXCLUDE)
    return f"(({ln} IN ('{t}', '{t} LINHA PESADA')) OR ({ln}='' AND {ds} LIKE '%{t}%' AND {ex}))"

def valid_user():
    v = _setting("goal_valid_user")
    return (v if v else os.environ.get("GOAL_VALID_USER", "ITALOC")).strip().upper()

def is_valid_user(v, user=None):
    return isinstance(v, str) and v.strip().upper() == (user or valid_user())

def goal_basis():
    """Base de contagem das metas: 'validacao' (padrão: validações ITALOC por SUGESTAO) ou 'recebido' (transições de status até ITEM RECEBIDO)."""
    v = (_setting("goal_basis") or os.environ.get("GOAL_BASIS", "validacao")).strip().lower()
    return v if v in ("validacao", "recebido") else "validacao"
