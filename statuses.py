"""Catálogo único de status dos itens em Desenvolvimento (DES) e Redesenvolvimento (R-D).
  • SUBS: os sub status como o servidor manda, um por coluna (desenho, validação, projeto/invoice, negociação, vendas, CIT, Inmetro). Um valor composto
    («PENDENTE DESENHO FORNECEDOR / PENDENTE COMPRAS») vale como cada parte. É o que as telas mostram (etapa 20 · Q4).
  • DEFS: pendências deduzidas do texto do STATUS e dos sub status (Pendente compras, Pendente Inmetro…), usadas por Compras, metas, Brands e Dashboard.
    Só o servidor decide (etapa 20 · Q3): a marcação manual (tabela rd_flags) deixou de valer."""

import re, rules, kinds

# chave da URL, coluna de rd_projects, rótulo — na ordem do ciclo
SUBS = [("desenho", "drawing_substatus", "Desenho"), ("validacao", "validation_substatus", "Validação"), ("projeto", "project_substatus", "Projeto / invoice"),
        ("negociacao", "negotiation_substatus", "Negociação"), ("vendas", "sales_substatus", "Vendas"), ("cit", "cit_substatus", "CIT"), ("inmetro", "inmetro_substatus", "Inmetro")]
SUB_COL = {k: c for k, c, _ in SUBS}
# Etapa 21: valores de validação que ficam sempre no quadro, mesmo zerados (o servidor ainda não manda nenhum). Filtro «sub=validacao:@CHAVE»;
# cada um junta as grafias do servidor pelo trecho (precisa ter / não pode ter). Negociação e vendas vão para «Mais filtros» (só na tela).
FIXOS = {"validacao": [("APROVADA", "VALIDAÇÃO APROVADA", ["APROVAD"], ["REPROVAD"]), ("REPROVADA", "VALIDAÇÃO REPROVADA", ["REPROVAD"], []),
                       ("QUALIDADE", "PENDENTE QUALIDADE", ["QUALIDADE"], ["APROVAD", "REPROVAD"])]}      # «reprovada pela qualidade» é reprovada
CONTROLADORIA = "CONTROLADORIA"       # «Pendente controladoria» (Mais filtros do DES): o texto em qualquer status ou sub status

def fixo_of(key, v):
    """Chave do valor fixo que `v` (uma parte do sub status) representa, ou None."""
    u = (v or "").upper()
    for k, _, inc, exc in FIXOS.get(key, []):
        if all(p in u for p in inc) and not any(p in u for p in exc): return k
    return None

def fixo_sql(key, fk, col):
    """Condição SQL do valor fixo `fk` na coluna `col` (trechos sem acento comparados em maiúsculas)."""
    for k, _, inc, exc in FIXOS.get(key, []):
        if k == fk: return "(" + " AND ".join([f"upper(coalesce({col},'')) LIKE '%{p}%'" for p in inc] + [f"upper(coalesce({col},'')) NOT LIKE '%{p}%'" for p in exc]) + ")"
    return "0"

def split_sub(v):
    """«A / B /» → ["A", "B"] (maiúsculas, sem vazios)."""
    return [p.strip().upper() for p in str(v or "").split("/") if p.strip()]

def sub_has(col):
    """Expressão SQL «/A/B/» da coluna, para testar uma parte com LIKE '%/' || valor || '/%'."""
    return f"('/'||replace(replace(replace(upper(trim(coalesce({col},''))),' / ','/'),' /','/'),'/ ','/')||'/')"
GROUPS = [("compras", "Compras"), ("validacao", "Validação"), ("desenho", "Desenho e projeto"), ("fornecedor", "Fornecedor e cadastro"), ("inmetro", "Inmetro")]

# key, rótulo, grupo, classe de cor, trechos que precisam aparecer (LIKE, maiúsculas, sem acento), trechos que não podem aparecer
DEFS = [
    ("pend_compras",        "Pendente compras",                  "compras",    "pc", ["PENDENTE COMPRAS"], []),
    ("pend_validacao",      "Pendente validação",                "validacao",  "pv", ["PENDENTE VALIDA"], ["QUALIDADE"]),
    ("pend_validacao_qual", "Pendente validação pela qualidade", "validacao",  "pq", ["PENDENTE VALIDA", "QUALIDADE"], []),
    ("val_reprovada",       "Validação reprovada",               "validacao",  "vr", ["REPROVAD"], ["QUALIDADE"]),
    ("val_reprovada_qual",  "Validação reprovada pela qualidade", "validacao", "vq", ["REPROVAD", "QUALIDADE"], []),
    ("pend_desenho_forn",   "Pendente desenho do fornecedor",    "desenho",    "pd", ["DESENHO FORNECEDOR"], []),
    ("pend_projeto",        "Pendente projeto",                  "desenho",    "pj", ["PENDENTE PROJETO"], []),
    ("pend_partnumber",     "Pendente partnumber do fornecedor", "fornecedor", "pn", ["PARTNUMBER"], []),
    ("pend_cod_perfect",    "Pendente código PERFECT",           "fornecedor", "pp", ["COD%PERFECT"], []),
    ("pend_confirmacao",    "Pendente confirmação",              "fornecedor", "pf", ["PENDENTE CONFIRMA"], []),
    ("pend_inmetro",        "Pendente Inmetro",                  "inmetro",    "pi", ["PENDENTE INMETRO"], []),
]
KEYS = [d[0] for d in DEFS]
LABEL = {d[0]: d[1] for d in DEFS}
GROUP = {d[0]: d[2] for d in DEFS}
SHORT = {"pend_compras": "Pend. compras", "pend_validacao": "Pend. validação", "pend_validacao_qual": "Pend. validação qualidade", "val_reprovada": "Validação reprovada", "val_reprovada_qual": "Validação reprovada qualidade",
         "pend_desenho_forn": "Pend. desenho forn.", "pend_projeto": "Pend. projeto", "pend_partnumber": "Pend. partnumber", "pend_cod_perfect": "Pend. cód. PERFECT", "pend_confirmacao": "Pend. confirmação", "pend_inmetro": "Pend. Inmetro"}
def auto_col(k): return "a_" + k

def public():
    """Estrutura entregue ao navegador (rótulos, grupos e cores)."""
    return {"groups": [{"key": k, "label": l} for k, l in GROUPS], "defs": [{"key": d[0], "label": d[1], "group": d[2], "cls": d[3]} for d in DEFS],
            "subs": [{"key": k, "label": l} for k, _, l in SUBS]}

def _cond(inc, exc):
    c = [f"t LIKE '%{p}%'" for p in inc] + [f"t NOT LIKE '%{p}%'" for p in exc]
    return "(" + " AND ".join(c) + ")"

def view_sql(has_cols):
    """CREATE VIEW v_rd_flags: cada pendência como o servidor indica (a_<chave> repete o valor, para quem ainda lê a coluna antiga)."""
    parts = ["coalesce(status,'')", "coalesce(drawing_substatus,'')", "coalesce(validation_substatus,'')"]
    for col in ("project_substatus", "inmetro_substatus"):
        if col in has_cols: parts.append(f"coalesce({col},'')")
    # «Pendente compras»:
    #  · DESENVOLVIMENTO — de um item já recebido é resíduo do servidor: não vale (etapa 16 · D5). O item está recebido quando alguma aplicação dele está em
    #    ITEM RECEBIDO, mesmo que outra aplicação ainda traga o sub status antigo.
    #  · REDESENVOLVIMENTO — vale POR APLICAÇÃO (etapa 19 · Q1): a aplicação R-D marcada «Pendente compras» conta enquanto ELA não estiver em ITEM RECEBIDO,
    #    mesmo que outra aplicação do código já tenha sido recebida (cada aplicação R-D é um redesenvolvimento com outro fornecedor).
    def agg1(k, inc, exc):
        c = _cond(inc, exc)
        if k != "pend_compras": return f"MAX({c})"
        return f"CASE WHEN suggestion='{kinds.RD}' THEN MAX({c} AND st<>'ITEM RECEBIDO') ELSE MAX({c}) * (1 - MAX(st='ITEM RECEBIDO')) END"
    agg = ", ".join(f"{agg1(k, inc, exc)} {k}_a" for k, _, _, _, inc, exc in DEFS)
    eff = ",\n ".join(f"g.{k}_a {k}" for k in KEYS)
    auto = ", ".join(f"g.{k}_a a_{k}" for k in KEYS)
    # as três famílias (amortecedor, moto, linha pesada): quem lê a view escolhe a família pelo próprio filtro de universo (etapa 21)
    return (f"CREATE VIEW v_rd_flags AS\nWITH a AS (SELECT code, suggestion, upper({"||' '||".join(parts)}) t, upper(trim(coalesce(status,''))) st FROM rd_projects WHERE {rules.desc_sql(familia='todas')}),\n"
            f"g AS (SELECT code, suggestion, {agg} FROM a GROUP BY code, suggestion)\nSELECT g.code, g.suggestion,\n {eff},\n {auto} FROM g")

ANY_SQL = " OR ".join(KEYS)
