"""Update 8 · Inmetro: aba «Inmetro» de Produtos e códigos e a situação Inmetro dos itens de Desenvolvimento / Redesenvolvimento.

Fontes:
  • certificados (tabela `certificates`, planilhas «Inmetro… Certificado» de cada fornecedor): código, nº Inmetro, família, código de barras, marca e a
    descrição do certificado. O fornecedor vem do nome da planilha (ZS ou E-WIN).
  • catálogo (`products`, CatalogoAMD prevalece): família, código de barras do catálogo (`cat_ean`, senão `ean`) e Ø da haste (`dimensions`).
  • DES/R-D (`rd_projects`, servidor): sub status Inmetro, INMETRO_PRIVATE (nº) e DESCRICAO_INMETRO no `extra`.
Situação no catálogo: nos dois fornecedores · só ZS · só E-WIN · sem certificado. Fora do catálogo: código que só aparece nos certificados.
Divergência (catálogo × certificado): família, Ø da haste (> 0,05 mm) ou código de barras.
Situação no DES/R-D (por aplicação; o código vale pela mais forte): em aprovação (sub status PENDENTE INMETRO ou descrição «PENDENTE INCLUSÃO»)
· com nº Inmetro (código nas planilhas ou nº vindo do servidor) · fora do certificado.
"""
import re, json
from queries import q

SIT = {"aprovacao": "Em aprovação", "com_num": "Com nº Inmetro", "fora": "Fora do certificado"}
CAT = {"dois": "Nos dois fornecedores", "zs": "Só ZS", "ewin": "Só E-WIN", "sem": "Sem certificado", "so_cert": "Só no certificado"}
DIV = {"familia": "Família", "haste": "Ø da haste", "ean": "Código de barras"}
FAMILIAS = ["ESTRUTURAL", "SEMI-ESTRUTURAL", "CONVENCIONAL", "CARTUCHO", "CABINE"]
_CODIGO = re.compile(r"^[A-Z]{2,5}\d{2,}[A-Z0-9-]*$")          # descarta lixo das planilhas (ex.: «BJ3T/18045/CA/»)


# ---------------- SQL da situação no DES/R-D (usado por rd.py) ----------------
def _ex(a, chave): return f"(CASE WHEN json_valid({a}extra) THEN json_extract({a}extra,'$.{chave}') END)"

def num_sql(a="r."):
    """Nº Inmetro da aplicação: o do servidor (INMETRO_PRIVATE, sem «N/A») ou, sem ele, o do certificado do código."""
    srv = _ex(a, "INMETRO_PRIVATE")
    return (f"(CASE WHEN upper(trim(coalesce({srv},''))) NOT IN ('','N/A','NA','-','N/D') THEN trim({srv}) "
            f"ELSE (SELECT MIN(c.inmetro_number) FROM certificates c WHERE upper(trim(c.perfect_code_raw))=upper(trim({a}code))) END)")

def aprov_sql(a="r."):
    return f"(upper(coalesce({a}inmetro_substatus,'')) LIKE '%PENDENTE INMETRO%' OR upper(coalesce({_ex(a, 'DESCRICAO_INMETRO')},'')) LIKE '%PENDENTE INCLUS%')"

def sit_sql(a="r."):
    return f"(CASE WHEN {aprov_sql(a)} THEN 'aprovacao' WHEN {num_sql(a)} IS NOT NULL THEN 'com_num' ELSE 'fora' END)"

RANK = {"aprovacao": 3, "com_num": 2, "fora": 1}


# ---------------- descrição padronizada ----------------
_ACENTO = {"ACO": "AÇO", "TEMPERA": "TÊMPERA", "CROMACAO": "CROMAÇÃO"}          # certificados escritos sem acento
def _cap(s):
    s = re.sub(r"\s+", " ", (s or "").strip(" ;'-.")).strip()
    s = re.sub(r"\b(ACO|TEMPERA|CROMACAO)\b", lambda m: _ACENTO[m.group(1)], s.upper()) if s else s
    return s[:1].upper() + s[1:].lower() if s else None

def padroniza(texto):
    """Descrição do certificado (formatos ZS, E-WIN e do servidor) → {material, categoria, tratamento, haste (mm)}; None sem texto."""
    if not texto or str(texto).strip().upper() in ("N/A", "-"): return None
    t = re.sub(r"\s*\n\s*", "; ", str(texto))
    pega = lambda *ps: next((m.group(1) for p in ps for m in [re.search(p, t, re.I)] if m), None)
    mat = pega(r"\bmat(?:erial)?\s*\.?\s*:?\s*([^;]+?)(?=;|\bcat|$)")
    cat = pega(r"\bcat(?:egoria)?\.?(?:\s*(?:do\s+)?ve[ií]culo)?\s*:?\s*(M[\dM,\s]*)")
    tr = pega(r"trat(?:amento)?\.?\s*t[ée]rmico\s*:?\s*([^;]+?)(?=;|\b[ØO] da haste|\bdimens|$)")
    h = pega(r"(?:[ØO]|di[âa]metro)\s*da\s*haste\s*:?\s*(\d+(?:[.,]\d+)?)")
    haste = float(h.replace(",", ".")) if h else None
    cat = ", ".join(x for x in re.split(r"[,\s]+", (cat or "").upper()) if x) or None
    out = {"material": _cap(mat), "categoria": cat, "tratamento": _cap(tr), "haste": haste}
    return out if any(v for v in out.values()) else None

def texto_pad(p):
    if not p: return None
    h = p.get("haste"); hs = (f"Ø {h:g}".replace(".", ",") + " mm") if h else None
    return ", ".join(x for x in (p.get("material"), p.get("categoria"), p.get("tratamento"), hs) if x) or None


def fornecedor(nome):
    u = re.sub(r"[^A-Z]", "", (nome or "").upper())
    return "E-WIN" if "EWIN" in u else "ZS" if "ZS" in u else (nome or "?")


# ---------------- dados ----------------
def _certs():
    """{código: {forn: [{num, ean, marca, fam, desc}, …]}} — o mesmo código pode estar em mais de um certificado do fornecedor (famílias diferentes)."""
    out = {}
    for r in q("""SELECT upper(trim(c.perfect_code_raw)) code, c.inmetro_number num, c.ean, c.brand marca, upper(trim(coalesce(c.family,''))) fam, c.cert_description descr, s.name src
                  FROM certificates c LEFT JOIN sources s ON s.id=c.source_id ORDER BY c.id"""):
        if not r["code"] or not _CODIGO.match(r["code"]): continue
        out.setdefault(r["code"], {}).setdefault(fornecedor(r["src"]), []).append({"num": r["num"], "ean": (r["ean"] or "").strip() or None, "marca": r["marca"], "fam": r["fam"] or None, "desc": r["descr"]})
    return out

def _ref(lista, fam=None):
    """Certificado de referência do fornecedor: o da família do catálogo; sem ele, o primeiro."""
    if not lista: return None
    return next((c for c in lista if fam and c["fam"] == fam), lista[0])

def _numeros():
    """Certificados existentes: [{forn, num, fam, n}] e {nº: forn}."""
    rows = q("""SELECT s.name src, c.inmetro_number num, upper(trim(coalesce(c.family,''))) fam, COUNT(*) n FROM certificates c LEFT JOIN sources s ON s.id=c.source_id
                WHERE trim(coalesce(c.inmetro_number,''))<>'' GROUP BY 1,2,3 ORDER BY 2""")
    lista = [{"forn": fornecedor(r["src"]), "num": r["num"], "fam": r["fam"], "n": r["n"]} for r in rows]
    return lista, {x["num"]: x["forn"] for x in lista}

def _catalogo():
    return q("""SELECT p.id, upper(p.perfect_code) code, p.description descr, upper(trim(coalesce(p.family,''))) fam, coalesce(nullif(trim(p.cat_ean),''), nullif(trim(p.ean),'')) ean,
                (SELECT MIN(d.rod_diameter_mm) FROM dimensions d WHERE d.product_id=p.id) haste FROM products p""")

def _outros(cs, fam):
    """Números dos outros certificados do código (família diferente da de referência), para a dica."""
    return sorted({f"{c['num']} ({c['fam'].capitalize() if c['fam'] else '?'})" for l in cs.values() for c in l if fam and c["fam"] != fam and c["num"]})

def _linha_catalogo(p, cs):
    zs, ew = _ref(cs.get("ZS"), p["fam"]), _ref(cs.get("E-WIN"), p["fam"]); ref = zs or ew
    sit = "dois" if zs and ew else "zs" if zs else "ewin" if ew else "sem"
    pad = padroniza(ref["desc"]) if ref else None; div = []
    fams = sorted({c["fam"] for l in cs.values() for c in l if c["fam"]})
    if p["fam"] and any(f != p["fam"] for f in fams): div.append("familia")          # como em Anomalias › Família: algum certificado de outra família
    if pad and pad.get("haste") and p["haste"] and abs(pad["haste"] - p["haste"]) > 0.05: div.append("haste")
    eans = {x["ean"] for x in (zs, ew) if x and x["ean"]}
    if p["ean"] and eans and p["ean"] not in eans: div.append("ean")
    return {"code": p["code"], "descr": p["descr"], "grupo": "catalogo", "sit": sit, "fam": p["fam"] or None, "fam_cert": [f for f in fams if f != p["fam"]] if "familia" in div else [],
            "num_zs": zs and zs["num"], "num_ew": ew and ew["num"], "outros": _outros(cs, p["fam"]), "ean": p["ean"], "ean_zs": zs and zs["ean"], "ean_ew": ew and ew["ean"],
            "marca": ref and ref["marca"], "haste_cat": p["haste"], "pad": pad, "pad_txt": texto_pad(pad), "orig": ref and ref["desc"], "div": div}

def _linha_so_cert(code, cs):
    zs, ew = _ref(cs.get("ZS")), _ref(cs.get("E-WIN")); ref = zs or ew; pad = padroniza(ref["desc"])
    return {"code": code, "descr": None, "grupo": "fora", "sit": "so_cert", "fam": ref["fam"], "fam_cert": [], "num_zs": zs and zs["num"], "num_ew": ew and ew["num"], "outros": _outros(cs, ref["fam"]),
            "ean": None, "ean_zs": zs and zs["ean"], "ean_ew": ew and ew["ean"], "marca": ref["marca"], "haste_cat": None, "pad": pad, "pad_txt": texto_pad(pad), "orig": ref["desc"], "div": []}

def _rd_linhas(certs, por_num):
    """Itens de DES/R-D em andamento (universo padrão das telas), um por código e tipo, com a situação Inmetro mais forte entre as aplicações."""
    import rd
    out = []
    for kind, sigla in (("DESENVOLVIMENTO", "DES"), ("REDESENVOLVIMENTO", "R-D")):
        w = " AND ".join(rd._univ(kind, {}) + [rd.NAO_RECEBIDA])
        rows = q(f"""SELECT upper(trim(r.code)) code, MAX(r.description) descr, group_concat(DISTINCT r.status) statuses, {sit_sql()} sit, {num_sql()} num,
                     MAX({_ex('r.', 'DESCRICAO_INMETRO')}) dsc, COUNT(*) l FROM rd_projects r WHERE {w} GROUP BY 1, 4, 5""", {"kind": kind})
        by = {}
        for r in rows:
            a = by.get(r["code"])
            if not a or RANK[r["sit"]] > RANK[a["sit"]] or (r["sit"] == a["sit"] and not a["num"] and r["num"]): by[r["code"]] = {**r, "l": (a["l"] if a else 0) + r["l"]}
            else: a["l"] += r["l"]
        for code, r in by.items():
            cs = certs.get(code, {}); zs, ew = _ref(cs.get("ZS")), _ref(cs.get("E-WIN")); ref = zs or ew
            pad = padroniza(r["dsc"]) or (padroniza(ref["desc"]) if ref else None)
            n_zs = zs and zs["num"]; n_ew = ew and ew["num"]
            if r["num"] and r["num"] not in (n_zs, n_ew):
                f = por_num.get(r["num"])
                if f == "ZS" and not n_zs: n_zs = r["num"]
                elif f == "E-WIN" and not n_ew: n_ew = r["num"]
            out.append({"code": code, "descr": r["descr"], "grupo": "rd", "tipo": sigla, "sit": r["sit"], "status": (r["statuses"] or "").replace(",", ", "), "itens": r["l"],
                        "num": r["num"], "num_srv": r["num"] if r["num"] and r["num"] not in (n_zs, n_ew) else None, "num_zs": n_zs, "num_ew": n_ew,
                        "fam": ref["fam"] if ref else None, "fam_cert": [], "outros": [], "ean": None, "ean_zs": zs and zs["ean"], "ean_ew": ew and ew["ean"], "marca": ref and ref["marca"],
                        "haste_cat": None, "pad": pad, "pad_txt": texto_pad(pad), "orig": r["dsc"] or (ref and ref["desc"]), "div": [], "na_planilha": bool(ref)})
    return out

def base():
    certs = _certs(); lista, por_num = _numeros(); cat = _catalogo(); no_cat = {p["code"] for p in cat}
    linhas = [_linha_catalogo(p, certs.get(p["code"], {})) for p in cat]
    linhas += [_linha_so_cert(c, cs) for c, cs in sorted(certs.items()) if c not in no_cat]
    linhas += _rd_linhas(certs, por_num)
    return linhas, lista


# ---------------- tela ----------------
CHAVES = ["dois", "zs", "ewin", "sem", "so_cert", "rd_aprovacao", "rd_com_num", "rd_fora", "div_familia", "div_haste", "div_ean"]

def _bate(l, chave):
    if chave in ("dois", "zs", "ewin", "sem"): return l["grupo"] == "catalogo" and l["sit"] == chave
    if chave == "so_cert": return l["grupo"] == "fora"
    if chave.startswith("rd_"): return l["grupo"] == "rd" and l["sit"] == chave[3:]
    if chave.startswith("div_"): return chave[4:] in l["div"]
    return True

def _forn_de(l):
    return "dois" if l["num_zs"] and l["num_ew"] else "zs" if l["num_zs"] else "ewin" if l["num_ew"] else "nenhum"

def _filtra(linhas, f, ignora=None):
    s, fam, fo, termo = f.get("sit") or "", (f.get("familia") or "").upper(), f.get("forn") or "", (f.get("q") or "").strip().upper()
    out = []
    for l in linhas:
        if ignora != "sit" and s and not _bate(l, s): continue
        if ignora != "familia" and fam and (l["fam"] or "") != fam: continue
        if ignora != "forn" and fo and _forn_de(l) != fo: continue
        if termo and not any(termo in str(v or "").upper() for v in (l["code"], l["descr"], l["num_zs"], l["num_ew"], l.get("num_srv"))): continue
        out.append(l)
    return out

def tela(f=None, page=1, size=100):
    f = f or {}; linhas, certs = base(); cat = [l for l in linhas if l["grupo"] == "catalogo"]; rdl = [l for l in linhas if l["grupo"] == "rd"]
    conta = lambda chave, ls: sum(1 for l in ls if _bate(l, chave))
    kpi = {"catalogo": len(cat), "com_cert": sum(1 for l in cat if l["sit"] != "sem"), "dois": conta("dois", cat), "sem": conta("sem", cat),
           "so_cert": conta("so_cert", linhas), "div": sum(1 for l in cat if l["div"]), "rd_aprovacao": conta("rd_aprovacao", rdl), "rd_fora": conta("rd_fora", rdl), "rd_total": len(rdl)}
    familias = []
    for fam in FAMILIAS + sorted({l["fam"] for l in cat if l["fam"] and l["fam"] not in FAMILIAS}):
        ls = [l for l in cat if l["fam"] == fam]
        if not ls and fam not in FAMILIAS: continue
        familias.append({"fam": fam, "total": len(ls), "dois": conta("dois", ls), "um": conta("zs", ls) + conta("ewin", ls), "sem": conta("sem", ls),
                         "certs": {fo: next((c["num"] for c in certs if c["fam"] == fam and c["forn"] == fo), None) for fo in ("ZS", "E-WIN")}})
    base_sit = _filtra(linhas, f, ignora="sit")
    chips = {k: conta(k, base_sit) for k in CHAVES}
    base_fam = _filtra(linhas, f, ignora="familia"); base_forn = _filtra(linhas, f, ignora="forn")
    opc_fam = [{"v": fam, "n": sum(1 for l in base_fam if l["fam"] == fam)} for fam in FAMILIAS]
    opc_forn = [{"v": k, "n": sum(1 for l in base_forn if _forn_de(l) == k)} for k in ("dois", "zs", "ewin", "nenhum")]
    rows = _filtra(linhas, f); total = len(rows); page = max(int(page or 1), 1)
    srv = sorted({l["num_srv"] for l in rdl if l.get("num_srv")})
    return {"kpi": kpi, "familias": familias, "certificados": certs, "nums_servidor": srv, "chips": chips, "familia_opc": opc_fam, "forn_opc": opc_forn,
            "total": total, "page": page, "size": size, "rows": rows[(page - 1) * size: page * size] if size else rows, "rotulos": {"cat": CAT, "rd": SIT, "div": DIV}}

def linhas_excel(f=None):
    rows = _filtra(base()[0], f or {})
    return rows


# ---------------- DES/R-D: situação do item (rd.py) ----------------
def item(code):
    """Ficha do item no DES/R-D: situação, nº, descrição padronizada e de onde veio."""
    certs = _certs(); _, por_num = _numeros(); c = str(code or "").strip().upper()
    for l in _rd_linhas(certs, por_num):
        if l["code"] == c:
            de = [x for x, ok in (("planilha de certificado", l["na_planilha"]), ("servidor", l["num_srv"] or (l["orig"] and not l["na_planilha"]))) if ok]
            return {"sit": l["sit"], "rotulo": SIT[l["sit"]], "num": l["num"], "pad": l["pad_txt"], "orig": l["orig"], "origem": " e ".join(de) or None}
    cs = certs.get(c)
    if cs:
        ref = _ref(cs.get("ZS")) or _ref(cs.get("E-WIN")); return {"sit": "com_num", "rotulo": SIT["com_num"], "num": ref["num"], "pad": texto_pad(padroniza(ref["desc"])), "orig": ref["desc"], "origem": "planilha de certificado"}
    return None
