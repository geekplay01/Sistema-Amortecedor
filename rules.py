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
        try:      # só leitura: um CREATE aqui esperava 5 s pelo lock quando chamado dentro da migração (outra conexão escrevendo)
            if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='app_settings'").fetchone(): return None
            r = c.execute("SELECT value FROM app_settings WHERE key=?", (key,)).fetchone()
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

# Chave de linha das telas DES/R-D (etapa 21): a FAMILIA do servidor, como o sistema PERFECT conta. «{t}» = texto da regra (AMORTECEDOR).
FAMILIAS = {"amortecedor": ("{t}", "Amortecedor"), "moto": ("{t} DE MOTO", "Amortecedor de moto"), "pesada": ("{t} LINHA PESADA", "Linha pesada")}
FAMILIA_PADRAO = "amortecedor"
# Marca padrão por tipo (etapa 21): o sistema PERFECT mostra em Desenvolvimento só a marca PERFECT (as marcas próprias de clientes — BPROAUTO,
# MOTORCRAFT, MOTRIO — ficam fora); em Redesenvolvimento a MARCA quase sempre vem vazia, então não há filtro. «todas» desliga.
MARCA_PADRAO = {"DESENVOLVIMENTO": "PERFECT"}

def familia_key(v):
    v = (v or "").strip().lower()
    return v if v in FAMILIAS else FAMILIA_PADRAO

def desc_sql(col="description", erp=True, pesada=False, familia=None):
    """Condição SQL que define o UNIVERSO de Desenvolvimento/Redesenvolvimento. Vale a FAMILIA do servidor (etapa 21: é o que o sistema PERFECT usa);
    `familia` = chave de FAMILIAS, lista de chaves ou «todas» (as três). Padrão: só «AMORTECEDOR» (módulos e Dashboard, etapa 20 · Q1); `pesada=True` (metas)
    = amortecedor + linha pesada. Linha sem FAMILIA (banco sincronizado antes da etapa 21) usa a LINHA — e, sem LINHA, a descrição contendo o texto da regra,
    sempre sem COX/KAD. `col` carrega o alias da tabela («r.description» → r.family, r.line, r.code). `erp=False` mantém os bloqueados/inativos no ERP
    (metas: o que já foi recebido e validado continua contando)."""
    t = re.sub(r"[^A-Z0-9 ]", "", only_desc())
    pre = col[:-len("description")] if col.endswith("description") else ""
    fm, ln, cd, ds = f"upper(trim(coalesce({pre}family,'')))", f"upper(trim(coalesce({pre}line,'')))", f"upper(coalesce({pre}code,''))", f"upper(coalesce({col},''))"
    off = f"{cd} NOT IN ({ERP_OFF_SQL})" if erp else "1=1"
    if not t: return f"({off})"
    ks = list(FAMILIAS) if familia == "todas" else ["amortecedor", "pesada"] if pesada and familia is None else [familia_key(x) for x in (familia if isinstance(familia, (list, tuple)) else [familia])]
    fams = [FAMILIAS[k][0].format(t=t) for k in dict.fromkeys(ks)]
    ex = " AND ".join(f"{cd} NOT LIKE '{x}%' AND {ds} NOT LIKE '{x}%'" for x in LINE_EXCLUDE)
    sem_fam = [f for f in fams if not f.endswith(" DE MOTO")]          # sem FAMILIA não dá para separar a moto: ela só aparece depois da sincronização
    pela_linha = f"({ln} IN ({', '.join(repr(f) for f in sem_fam)}) OR ({ln}='' AND {ds} LIKE '%{t}%' AND {ex}))" if t in sem_fam else f"({ln} IN ({', '.join(repr(f) for f in sem_fam)}))" if sem_fam else "0"
    return f"((({fm} IN ({', '.join(repr(f) for f in fams)})) OR ({fm}='' AND {pela_linha})) AND {off})"

def marca_sql(kind, marca=None, pre="r."):
    """Condição da marca no universo DES/R-D: vazio = padrão do tipo (MARCA_PADRAO: a marca padrão ou MARCA vazia — só as outras marcas saem),
    «todas» = sem filtro, outro valor = a MARCA exata. None se não filtra."""
    m = re.sub(r"[^A-Z0-9 .&-]", "", (marca or "").strip().upper()); col = f"upper(trim(coalesce({pre}brand,'')))"
    if m == "TODAS": return None
    if m: return f"{col}='{m}'"
    d = MARCA_PADRAO.get(kind, "")
    return f"{col} IN ('{d}','')" if d else None

# Bloqueado (BLOQ=SIM) ou inativo no ERP: sai de DES/R-D (listas, contadores e metas). Vem de ESTOQUE_ANALISE_REPOSICAO pela sincronização (tabela ds_situacao).
ERP_OFF_SQL = "SELECT upper(code) FROM ds_situacao WHERE upper(trim(coalesce(blocked,'')))='SIM' OR upper(trim(coalesce(active,'ATIVO')))<>'ATIVO'"

def valid_user():
    v = _setting("goal_valid_user")
    return (v if v else os.environ.get("GOAL_VALID_USER", "ITALOC")).strip().upper()

def is_valid_user(v, user=None):
    return isinstance(v, str) and v.strip().upper() == (user or valid_user())

def validacao_ia():
    """Etapa 24: a bancada de Validação lê as medidas com o Claude (API da Anthropic)? Padrão: não — as medidas são digitadas no desenho e nenhuma imagem sai do PC."""
    return (_setting("validacao_ia") or "0").strip() == "1"

def goal_basis():
    """Base de contagem das metas: 'validacao' (padrão: validações ITALOC por SUGESTAO) ou 'recebido' (transições de status até ITEM RECEBIDO)."""
    v = (_setting("goal_basis") or os.environ.get("GOAL_BASIS", "validacao")).strip().lower()
    return v if v in ("validacao", "recebido") else "validacao"
