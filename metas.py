"""Processamento de METAS / VALIDAÇÕES (Pandas) — a conta que alimenta o dashboard.

Por que a versão anterior dava ZERO: o texto vindo do servidor traz espaços ocultos (inclusive NBSP), caixa mista ("Italoc", "des ") e rótulos variados
("R-D", "RD", "Redesenvolvimento"), e a comparação era exata. Aqui TUDO é normalizado antes de comparar:  .str.strip().str.upper()  nas colunas
USER_VALID, SUGESTAO e LINHA (mais NBSP / caracteres de largura zero e acento nos nomes de coluna).

Regras (definidas pelo usuário):
  1. USER_VALID estritamente igual a "ITALOC"            (rules.valid_user(); não é "contém": «ITALOC2» ou «XITALOC» NÃO entram)
  2. LINHA = "AMORTECEDOR" ou "AMORTECEDOR LINHA PESADA" (estrito); qualquer linha com COX ou KAD fica de fora
  3. duas contagens separadas por SUGESTAO: "DES" e "R-D" (mutuamente exclusivas: código em R-D não conta em DES)
  4. retorno = dicionário com o total de validações e a quebra DES / R-D.
`total` conta CÓDIGOS DISTINTOS por tipo (o mesmo item em várias aplicações não infla a meta); `linhas` traz a contagem de linhas brutas.
"""
import re, json, datetime
import pandas as pd
import kinds, rules

DES, RD = "DES", "R-D"                                   # chaves do dicionário de retorno (as do usuário); o rótulo oficial na tela é DESENVOLVIMENTO / REDESENVOLVIMENTO
_INVIS = re.compile(r"[​‌‍⁠﻿]")

def canon(c):
    """Nome de coluna canônico: sem acento, maiúsculo, só A-Z0-9 (USER_VALID = 'user valid' = 'USER-VALID')."""
    import unicodedata
    return re.sub(r"[^A-Z0-9]", "", unicodedata.normalize("NFKD", str(c)).encode("ascii", "ignore").decode().upper())

def clean_series(s):
    """`.str.strip().str.upper()` à prova de NBSP, caracteres invisíveis e valores nulos."""
    s = s.astype("object").where(s.notna(), "").astype(str)
    s = s.str.replace(" ", " ", regex=False).str.replace(_INVIS, "", regex=True)
    return s.str.strip().str.upper().replace({"NAN": "", "NONE": "", "NULL": "", "NAT": ""})

def _find(df, *names):
    by = {canon(c): c for c in df.columns}
    for n in names:
        if canon(n) in by: return by[canon(n)]
    return None

def tipo(v):
    """'DES', 'des ', 'Desenvolvimento' → 'DES' · 'R-D', 'rd', 'Redesenvolvimento' → 'R-D' · outro → None."""
    k = kinds.normalize_kind(v)
    return DES if k == kinds.DES else RD if k == kinds.RD else None

def prepare(df):
    """Normaliza as colunas USER_VALID, SUGESTAO e LINHA (e CODIGO / DATA_APROVACAO, se houver). Devolve uma CÓPIA com colunas padronizadas."""
    out = pd.DataFrame(index=df.index)
    for std, names in (("USER_VALID", ("USER_VALID", "USER APROV", "USER_APROV")), ("SUGESTAO", ("SUGESTAO", "SUGESTÃO", "TIPO")), ("LINHA", ("LINHA",)),
                       ("CODIGO", ("CODIGO", "CÓDIGO", "COD")), ("DATA_APROVACAO", ("DATA_APROVACAO", "DATA APROV", "DATA_APROV", "DATA_VALIDACAO"))):
        col = _find(df, *names)
        if std == "DATA_APROVACAO": out[std] = pd.to_datetime(df[col], errors="coerce") if col else pd.NaT; continue
        out[std] = clean_series(df[col]) if col else ""
    if "DESCRICAO" in {canon(c) for c in df.columns}: out["DESCRICAO"] = clean_series(df[_find(df, "DESCRICAO")])
    return out

def validation_counts(df, user=None, line=None, year=None):
    """Dicionário para o dashboard:
    {"total": n, "DES": n, "R-D": n, "outros": n, "linhas": {...}, "por_mes": {"2026-07": {"DES": a, "R-D": b}, ...}, "filtro": {...}, "avisos": [...]}
    df: DataFrame com (ao menos) USER_VALID, SUGESTAO e LINHA — nomes em qualquer caixa/acentuação."""
    user = (user or rules.valid_user()).strip().upper(); line = (line or rules.only_desc() or "AMORTECEDOR").strip().upper(); avisos = []
    p = prepare(df); n0 = len(p)
    if not (p["USER_VALID"] != "").any(): avisos.append("coluna USER_VALID ausente ou vazia — nada pôde ser validado")
    if not (p["LINHA"] != "").any():
        if "DESCRICAO" in p.columns: avisos.append("coluna LINHA ausente: usada a DESCRIÇÃO do item (sem COX/KAD)")
        else: avisos.append("coluna LINHA ausente")
    m_user = p["USER_VALID"] == user
    lines = {line, line + " LINHA PESADA"}                              # LINHA estrita: «AMORTECEDOR» ou «AMORTECEDOR LINHA PESADA»
    excl = p["LINHA"].str.contains("|".join(rules.LINE_EXCLUDE), regex=True, na=False)      # qualquer linha com COX ou KAD fica fora
    m_line = p["LINHA"].isin(lines) & ~excl
    if "DESCRICAO" in p.columns:                                         # linha vazia (servidor antigo): vale a descrição, também sem COX/KAD
        sem = p["LINHA"] == ""
        m_line = m_line | (sem & p["DESCRICAO"].str.contains(re.escape(line), regex=True, na=False) & ~p["DESCRICAO"].str.contains("|".join(rules.LINE_EXCLUDE), regex=True, na=False))
    sel = p[m_user & m_line].copy(); sel["T"] = sel["SUGESTAO"].map(tipo)
    cod_rd = set(sel.loc[sel["T"] == RD, "CODIGO"]) - {""}              # DES e R-D mutuamente exclusivos: código em R-D não conta em DES (R-D prevalece)
    sel = sel[~((sel["T"] == DES) & sel["CODIGO"].isin(cod_rd))]
    if year:
        has = sel["DATA_APROVACAO"].notna().any()
        if has: sel = sel[sel["DATA_APROVACAO"].dt.year == int(year)]
        else: avisos.append("sem DATA_APROVACAO: o ano não pôde ser aplicado (contagem de todos os anos)")
    def cnt(t):
        x = sel[sel["T"] == t]
        return int(x["CODIGO"].replace("", pd.NA).dropna().nunique() + (x["CODIGO"] == "").sum()) if len(x) else 0
    out = {DES: cnt(DES), RD: cnt(RD)}
    out["total"] = out[DES] + out[RD]; out["outros"] = int(sel["T"].isna().sum())
    out["linhas"] = {"lidas": n0, "do_usuario": int(m_user.sum()), "do_usuario_e_linha": int((m_user & m_line).sum()), "DES": int((sel["T"] == DES).sum()), RD: int((sel["T"] == RD).sum())}
    por = {}
    d = sel.dropna(subset=["DATA_APROVACAO"])
    for (ym, t), g in d.groupby([d["DATA_APROVACAO"].dt.strftime("%Y-%m"), "T"]):
        if t: por.setdefault(ym, {DES: 0, RD: 0})[t] = int(g["CODIGO"].nunique() if (g["CODIGO"] != "").any() else len(g))
    out["por_mes"] = dict(sorted(por.items())); out["sem_data"] = int(sel["DATA_APROVACAO"].isna().sum())
    out["filtro"] = {"USER_VALID": user, "LINHA_contem": line, "ano": int(year) if year else None}; out["avisos"] = avisos
    return out

# ───────────── carga a partir do banco local (cache do servidor) ─────────────
def load_frame():
    """rd_projects (+ extra JSON com USER APROV, DATA APROV e LINHA do servidor) → DataFrame com as colunas do BI."""
    from queries import q
    rows = []
    for r in q("SELECT code, suggestion, description, extra, line FROM rd_projects"):
        try: ex = json.loads(r["extra"]) if r["extra"] else {}
        except ValueError: ex = {}
        by = {canon(k): v for k, v in ex.items()}
        rows.append({"CODIGO": r["code"], "SUGESTAO": r["suggestion"], "DESCRICAO": r["description"], "USER_VALID": by.get("USERAPROV") or by.get("USERVALID"),
                     "LINHA": r["line"] or by.get("LINHA"), "DATA_APROVACAO": by.get("DATAAPROV") or by.get("DATAAPROVACAO")})
    return pd.DataFrame(rows, columns=["CODIGO", "SUGESTAO", "DESCRICAO", "USER_VALID", "LINHA", "DATA_APROVACAO"])

def dashboard(year=None):
    """Dicionário final para o dashboard/API (ano opcional): total, quebra por tipo e evolução mensal.
    Na tela e na API os tipos levam o rótulo OFICIAL (DESENVOLVIMENTO / REDESENVOLVIMENTO); «DES» e «R-D» são só os valores de SUGESTAO na origem."""
    y = int(year) if str(year or "").isdigit() else datetime.date.today().year
    r = validation_counts(load_frame(), year=y); official = {DES: kinds.DES, RD: kinds.RD}; fix = lambda d: {official.get(k, k): v for k, v in d.items()}
    r = {**r, **fix({DES: r[DES], RD: r[RD]})}; r.pop(DES); r.pop(RD)
    r["linhas"] = fix(r["linhas"]); r["por_mes"] = {m: fix(v) for m, v in r["por_mes"].items()}
    return r | {"year": y}
