"""Catálogo único de status dos itens em Desenvolvimento (DES) e Redesenvolvimento (R-D).
Cada status é detectado pelo texto do STATUS e dos sub status da planilha (desenho, validação, projeto/invoice, Inmetro) e pode ser marcado/desmarcado à mão
(a marcação manual prevalece e pode voltar ao automático). Textos diferentes ficam em status diferentes — ex.: «validação reprovada» ≠ «validação reprovada pela qualidade»."""

import rules
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
    return {"groups": [{"key": k, "label": l} for k, l in GROUPS], "defs": [{"key": d[0], "label": d[1], "group": d[2], "cls": d[3]} for d in DEFS]}

def _cond(inc, exc):
    c = [f"t LIKE '%{p}%'" for p in inc] + [f"t NOT LIKE '%{p}%'" for p in exc]
    return "(" + " AND ".join(c) + ")"

def view_sql(has_cols):
    """CREATE VIEW v_rd_flags: valor efetivo (marcação manual ou o que a planilha indica) e a_<chave> (só o que a planilha indica)."""
    parts = ["coalesce(status,'')", "coalesce(drawing_substatus,'')", "coalesce(validation_substatus,'')"]
    for col in ("project_substatus", "inmetro_substatus"):
        if col in has_cols: parts.append(f"coalesce({col},'')")
    agg = ", ".join(f"MAX({_cond(inc, exc)}) {k}_a" for k, _, _, _, inc, exc in DEFS)
    eff = ",\n ".join(f"COALESCE((SELECT value FROM rd_flags f WHERE f.code=g.code AND f.suggestion=g.suggestion AND f.flag='{k}'), g.{k}_a) {k}" for k in KEYS)
    auto = ", ".join(f"g.{k}_a a_{k}" for k in KEYS)
    return (f"CREATE VIEW v_rd_flags AS\nWITH a AS (SELECT code, suggestion, upper({"||' '||".join(parts)}) t FROM rd_projects WHERE {rules.desc_sql()}),\n"
            f"g AS (SELECT code, suggestion, {agg} FROM a GROUP BY code, suggestion)\nSELECT g.code, g.suggestion,\n {eff},\n {auto} FROM g")

ANY_SQL = " OR ".join(KEYS)
