"""Referências de concorrentes (etapa 17 · Q10/Q11/Q18/Q19/Q20).
  • Servidor: DESENVOLVIMENTO_CONCORRENTES (ID, concorrente, referência) → ds_concorrentes. O ID é o de DESENVOLVIMENTO_PRODUTOS: `build()` liga cada
    referência ao código do item (rd_projects.extra.ID) no universo amortecedor (LINHA AMORTECEDOR / LINHA PESADA, não bloqueado no ERP), qualquer status.
  • Nomes: grafias diferentes do mesmo concorrente viram um («HIPPERFREIOS» = «HIPPER FREIOS»; «N° INDISA» = INDISA). **OEM** = código original da montadora,
    separado dos concorrentes.
  • Regra de uso (`para_item`): item em DESENVOLVIMENTO usa o servidor; item do CATÁLOGO usa o CrossCatalogo.xlsx quando ele tem o item — senão o servidor
    (ex.: acabou de virar ITEM RECEBIDO e ainda não está na planilha). A busca procura nas duas fontes.
  • Anomalias: «Cross × servidor» (mesmo concorrente, referências diferentes num item do catálogo) e «Concorrentes repetidos»
    (mesma referência em 2+ códigos PERFECT; mesmo código e concorrente com 2+ referências). Mesma referência em vários IDs do mesmo código = várias aplicações, não é anomalia."""
import re, unicodedata
import database as db
from queries import q, q1

TABLE = """CREATE TABLE IF NOT EXISTS concorrentes(code TEXT, kind TEXT, status TEXT, dev_id TEXT, competitor TEXT, reference TEXT, ref_key TEXT, is_oem INTEGER);
CREATE INDEX IF NOT EXISTS ix_conc_code ON concorrentes(code); CREATE INDEX IF NOT EXISTS ix_conc_key ON concorrentes(ref_key)"""
CROSS_SRC = "CrossCatalogo.xlsx"
OEM = "OEM"
_ALIAS = {"HIPPERFREIOS": "HIPPER FREIOS", "TRWAMD": "TRW", "KYB": "KAYABA"}         # chave sem espaço/pontuação → nome único

def _un(s): return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
def ref_key(t): return re.sub(r"[^A-Z0-9]", "", str(t or "").upper())
def nome(raw):
    """Nome único do concorrente: maiúsculas, sem «N°»/«Nº» na frente, grafias sem espaço unificadas."""
    n = re.sub(r"\s+", " ", str(raw or "")).strip().upper()
    n = re.sub(r"^N\s*[°ºO]\s*\.?\s+", "", n)
    k = re.sub(r"[^A-Z0-9]", "", _un(n))
    return _ALIAS.get(k, n) if n else None

def ensure(c=None):
    stmts = [s for s in TABLE.split(";") if s.strip()]
    if c is not None:
        for s in stmts: c.execute(s)
        return
    with db.session() as cc:
        for s in stmts: cc.execute(s)

def build():
    """Refaz a tabela `concorrentes` a partir do que veio do servidor. → nº de referências ligadas a um código."""
    import rules
    with db.session() as c:
        ensure(c)
        try: raw = c.execute(f"""SELECT upper(r.code) code, r.suggestion kind, r.status, k.dev_id, k.competitor, k.reference FROM ds_concorrentes k
                                 JOIN rd_projects r ON json_extract(r.extra,'$.ID')=k.dev_id
                                 WHERE upper(trim(coalesce(r.line,''))) IN ('AMORTECEDOR','AMORTECEDOR LINHA PESADA') AND {rules.desc_sql('r.description')}""").fetchall()
        except Exception: raw = []
        rows = []
        for r in raw:
            n, ref = nome(r[4]), str(r[5] or "").strip().upper()
            if n and ref: rows.append((r[0], r[1], r[2], r[3], n, ref, ref_key(ref), int(n == OEM)))
        c.execute("DELETE FROM concorrentes")
        c.executemany("INSERT INTO concorrentes(code,kind,status,dev_id,competitor,reference,ref_key,is_oem) VALUES(?,?,?,?,?,?,?,?)", rows)
    return len(rows)

def available():
    try: return bool(q("SELECT 1 FROM concorrentes LIMIT 1"))
    except Exception: return False

def _cross(code):
    return q("""SELECT k.brand, k.code, k.code_type FROM codes k JOIN products p ON p.id=k.product_id JOIN sources s ON s.id=k.source_id
                WHERE p.perfect_code=? AND s.name=? AND k.code_type IN ('concorrente','oem') ORDER BY k.code_type DESC, k.brand, k.code""", (code, CROSS_SRC))

def _server(code):
    """Referências do servidor do código (uma linha por concorrente × referência; `aplicacoes` = em quantos IDs ela aparece)."""
    if not available(): return []
    return q("""SELECT competitor, reference, is_oem, COUNT(DISTINCT dev_id) aplicacoes FROM concorrentes WHERE code=upper(?)
                GROUP BY competitor, ref_key ORDER BY is_oem, competitor, reference""", (code,))

def para_item(code):
    """{fonte, concorrentes:[{marca, codigo, aplicacoes}], oem:[…]} pela regra Q18: catálogo com o item no CrossCatalogo → CrossCatalogo; senão o servidor."""
    cat = q1("SELECT catalog_position FROM products WHERE perfect_code=?", (code,))
    cr = _cross(code) if cat and cat["catalog_position"] is not None else []
    if cr:
        return {"fonte": "CrossCatalogo", "concorrentes": [{"marca": nome(x["brand"]) or "—", "codigo": x["code"]} for x in cr if x["code_type"] == "concorrente"],
                "oem": [{"marca": x["brand"], "codigo": x["code"]} for x in cr if x["code_type"] == "oem"]}
    sv = _server(code)
    return {"fonte": "servidor" if sv else None, "concorrentes": [{"marca": x["competitor"], "codigo": x["reference"], "aplicacoes": x["aplicacoes"]} for x in sv if not x["is_oem"]],
            "oem": [{"marca": "OEM", "codigo": x["reference"], "aplicacoes": x["aplicacoes"]} for x in sv if x["is_oem"]]}

def busca(term, limit=200):
    """Códigos (PERFECT ou de desenvolvimento) cuja referência no servidor é `term` (sem pontuação, exata). Termos com menos de 3 caracteres não buscam."""
    k = ref_key(term)
    if len(k) < 3 or not available(): return []
    return [r["code"] for r in q("SELECT DISTINCT code FROM concorrentes WHERE ref_key=? ORDER BY code LIMIT ?", (k, limit))]

# ---------------- anomalias ----------------
def _match(qtxt, *txt):
    t = " ".join(str(x or "") for x in txt).upper(); return all(w in t for w in (qtxt or "").upper().split())

def cross_x_servidor(qtxt=""):
    """Itens do catálogo que estão no CrossCatalogo e no servidor com o MESMO concorrente e referências diferentes (nenhuma referência em comum)."""
    if not available(): return []
    cross = {}
    for r in q("""SELECT p.id product_id, p.perfect_code code, p.description, k.brand, k.code ref FROM codes k JOIN products p ON p.id=k.product_id JOIN sources s ON s.id=k.source_id
                  WHERE s.name=? AND k.code_type='concorrente' AND p.catalog_position IS NOT NULL""", (CROSS_SRC,)):
        g = cross.setdefault((r["code"], nome(r["brand"])), {"product_id": r["product_id"], "description": r["description"], "refs": set()}); g["refs"].add(r["ref"].upper())
    serv = {}
    for r in q("SELECT code, competitor, reference FROM concorrentes WHERE is_oem=0"):
        serv.setdefault((r["code"], r["competitor"]), set()).add(r["reference"])
    out = []
    for (code, comp), g in sorted(cross.items()):
        s = serv.get((code, comp))
        if s and not ({ref_key(x) for x in g["refs"]} & {ref_key(x) for x in s}) and _match(qtxt, code, g["description"], comp, *g["refs"], *s):
            out.append({"product_id": g["product_id"], "perfect_code": code, "description": g["description"], "concorrente": comp, "cross": sorted(g["refs"]), "servidor": sorted(s)})
    return out

def repetidos(qtxt=""):
    """Dois grupos: «ref_em_varios» (mesma referência de concorrente em 2+ códigos PERFECT) e «varias_refs» (mesmo código e concorrente com 2+ referências)."""
    if not available(): return []
    out = []
    for r in q("""SELECT competitor, MIN(reference) reference, group_concat(DISTINCT code) codes, COUNT(DISTINCT code) n FROM concorrentes WHERE is_oem=0
                  GROUP BY competitor, ref_key HAVING COUNT(DISTINCT code) > 1 ORDER BY n DESC, competitor"""):
        cs = sorted(r["codes"].split(","))
        if _match(qtxt, r["competitor"], r["reference"], *cs): out.append({"grupo": "ref_em_varios", "concorrente": r["competitor"], "referencias": [r["reference"]], "codigos": cs})
    for r in q("""SELECT code, competitor, group_concat(DISTINCT reference) refs, COUNT(DISTINCT ref_key) n FROM concorrentes WHERE is_oem=0
                  GROUP BY code, competitor HAVING COUNT(DISTINCT ref_key) > 1 ORDER BY code, competitor"""):
        rs = sorted(r["refs"].split(","))
        if _match(qtxt, r["code"], r["competitor"], *rs): out.append({"grupo": "varias_refs", "concorrente": r["competitor"], "referencias": rs, "codigos": [r["code"]]})
    return out
