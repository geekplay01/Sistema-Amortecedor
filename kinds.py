"""Rótulos OFICIAIS dos itens em desenvolvimento: DESENVOLVIMENTO e REDESENVOLVIMENTO (nunca as siglas DES / R-D).
`normalize_kind` limpa qualquer variação que venha do servidor, de planilhas antigas ou da tela."""
import re, unicodedata

DES = "DESENVOLVIMENTO"
RD = "REDESENVOLVIMENTO"
SLUG = {"des": DES, "rd": RD}                       # apelidos usados nas URLs e no JavaScript
LABEL = {DES: "Desenvolvimento", RD: "Redesenvolvimento"}
SLUG_OF = {DES: "desenvolvimento", RD: "redesenvolvimento"}   # páginas do menu

def normalize_kind(v):
    """'DES', 'des ', 'Desenv.', 'D' -> DESENVOLVIMENTO · 'R-D', 'rd', 'R/D', 'Redes.' -> REDESENVOLVIMENTO · desconhecido -> None."""
    if v is None: return None
    try:
        if v != v: return None          # NaN
    except Exception: pass
    t = re.sub(r"\s+", " ", str(v).replace("\xa0", " ")).strip()
    if not t or t.upper() in ("NULL", "NONE", "NAN"): return None
    k = re.sub(r"[^A-Z]", "", unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().upper())
    if k.startswith("REDES") or k in ("RD", "R"): return RD
    if k.startswith("DES") or k == "D": return DES
    return None

def of_slug(s):
    """'des' / 'rd' / 'desenvolvimento' / 'DES' ... -> rótulo oficial (ou None)."""
    s = (s or "").strip().lower()
    return SLUG.get(s) or normalize_kind(s)
