"""Módulo Validação (etapa 24): validação de desenho de REDESENVOLVIMENTO (e, depois, DESENVOLVIMENTO) que gera o F-008.

Fluxo da bancada: 1 · desenhos (PERFECT, com a máscara limpa à mão, e o do fornecedor) → 2 · família (modelo F-008 de bases_exemplo/VALIDATION)
→ 3 · medidas (o Claude lê os dois desenhos e LISTA; quem confere e aprova é o usuário) → 4 · revisão e aprovação (Aprovar ou Reprovar gera o
F-008 em xlsx e pdf; só Aprovar sobe o desenho do fornecedor para Desenhos).

Regras do F-008 (modelo intocado: fórmulas, logo e formatação ficam como estão):
- T. Validação: linhas 10–34; B = medida (inglês), F = desenho PERFECT («OEM or Reference»), I = fornecedor, L/M = tolerância +/−, N = Ap (fórmula), O = Improve.
  Imagem PERFECT em S10:AJ34; do fornecedor (com os números das medidas) em A37:R57. Conclusão: X em S50 (aprovado) ou S52 (reprovado).
- DampingForce: Pf na linha 11 e Py na 12; C–G = PERFECT, H–L = fornecedor; imagens em R11:AI25 e A28:Q48; X em R41 / R43.
- Dados: B9 código … B26 tipo («DRAWING»). Nome: «F-008 - Validation Test - Rev.00 - <CÓD> - <FORNECEDOR> - <CÓD FORNECEDOR> - REV.00»."""
import os, re, io, json, glob, shutil, datetime, subprocess
import database as db
from queries import q, q1

DIR = os.path.join(db.BASE, "data", "validacoes")
MODELOS = os.path.join(db.BASE, "bases_exemplo", "VALIDATION")
KINDS = {"rd": "REDESENVOLVIMENTO", "des": "DESENVOLVIMENTO"}
STATUS = {"andamento": "Em andamento", "aprovada": "Aprovada", "reprovada": "Reprovada"}
LINHA0, NLINHAS = 10, 25                  # T. Validação: linhas 10 a 34
MODELO_IA = "claude-opus-5-5"
VELOCIDADES = [0.079, 0.157, 0.314, 0.52, 0.75]
_TOL_DAMP = [0.3, 0.25, 0.15, 0.15, 0.15]      # fórmula da aba DampingForce

def _agora(): return datetime.datetime.now().isoformat(timespec="seconds")
def _pasta(vid): p = os.path.join(DIR, str(int(vid))); os.makedirs(p, exist_ok=True); return p
def _seguro(t): return re.sub(r'[\\/:*?"<>|]+', " ", str(t or "")).strip()

# ---------------- famílias (modelos F-008) ----------------
_cache_fam = {}
def _arquivos_modelo():
    out = {}
    for f in sorted(glob.glob(os.path.join(MODELOS, "F-008*.xlsx"))):
        m = re.search(r"Rev\.00 - AMORTECEDOR (.+?) - FORNECEDOR", os.path.basename(f), re.I)
        if m: out[m.group(1).strip().upper()] = f
    return out

def familias():
    """[{v: 'ESTRUTURAL', l: 'Estrutural', medidas: [...], n}] lidos dos modelos (coluna B, linhas 10–34, sem «-»)."""
    import openpyxl
    out = []
    for fam, f in _arquivos_modelo().items():
        st = os.stat(f); k = (f, st.st_mtime_ns)
        if k not in _cache_fam:
            wb = openpyxl.load_workbook(f, read_only=True)
            try:
                ws = wb.worksheets[0]
                med = [str(ws.cell(r, 2).value).strip() for r in range(LINHA0, LINHA0 + NLINHAS) if ws.cell(r, 2).value not in (None, "") and str(ws.cell(r, 2).value).strip() != "-"]
                regra = "relativa" if "ABS(" in str(wb.worksheets[1].cell(11, 13).value or "").upper() else "faixa"      # fórmula Ap da aba DampingForce do modelo
                _cache_fam[k] = (med, regra)
            finally: wb.close()
        out.append({"v": fam, "l": fam, "medidas": _cache_fam[k][0], "n": len(_cache_fam[k][0]), "damping": _cache_fam[k][1]})
    ordem = ["CARTUCHO", "CONVENCIONAL", "ESTRUTURAL", "SEMI-ESTRUTURAL", "SEMI-ESTRUTURAL INTERFERENCIA"]
    out.sort(key=lambda x: (ordem.index(x["v"]) if x["v"] in ordem else 99, x["v"]))
    for x in out: x["l"] = x["v"].capitalize().replace("interferencia", "interferência")
    return out

def _medidas(fam): return next((x["medidas"] for x in familias() if x["v"] == (fam or "").upper()), [])

def _linhas_da_familia(fam, antigas=None):
    """Linhas do modelo da família; valores de uma família anterior ficam quando o nome da medida é o mesmo; medidas extras ficam no fim."""
    antigas = antigas or []; por_nome = {(l.get("nome") or "").strip().upper(): l for l in antigas if l.get("nome")}
    nomes = _medidas(fam); out = []
    for n in nomes:
        l = dict(por_nome.pop(n.strip().upper(), None) or _linha_vazia()); l["nome"] = n; l["extra"] = False; out.append(l)
    for l in antigas:
        if l.get("extra") and (l.get("nome") or "").strip().upper() in por_nome and len(out) < NLINHAS: out.append(dict(l))
    for i, l in enumerate(out, 1): l["n"] = i
    return out

def _aplicar_mola(linhas, mola, antiga=None):
    """Item com mola (etapa 24): a linha LMAX2 entra logo abaixo do LMAX (sem LMAX, no começo); desligado, ela sai. `antiga` = a LMAX2 de antes (guarda os valores)."""
    sem = [l for l in linhas if not l.get("mola")]
    if mola:
        if len(sem) >= NLINHAS: raise ValueError("A tabela já tem 25 medidas: tire uma antes de ligar «Item com mola».")
        nova = dict(antiga or {**_linha_vazia(), "nome": "LMAX2"}); nova["mola"] = True; nova["extra"] = False
        pos = next((i + 1 for i, l in enumerate(sem) if (l.get("nome") or "").upper() == "LMAX"), 0)
        sem = sem[:pos] + [nova] + sem[pos:]
    for i, l in enumerate(sem, 1): l["n"] = i
    return sem

def _linha_vazia(): return {"n": 0, "nome": "", "p": "", "f": "", "tm": "", "tn": "", "melhoria": "", "conferida": False, "lida": False, "pp": None, "pf": None, "obs": "", "extra": False}

# ---------------- regras do modelo (A / R) ----------------
def num(v):
    s = str(v if v is not None else "").strip().replace("Ø", "").replace("ø", "").replace("Φ", "").replace(",", ".").replace(" ", "")
    if not s: return None
    try: return float(s)
    except ValueError: return None

def ap(l):
    """Coluna Ap do F-008 (fórmula N10), na tela: A, R ou vazio (sem os dois valores)."""
    F, I, L, M = (str(l.get(k) or "").strip() for k in ("p", "f", "tm", "tn"))
    if L.lower() == "ok": return "A"
    if L.upper() == "N": return "R"
    if not F or not I or num(F) == 0: return ""
    Fs, Is = F.upper(), I.upper()
    if Fs.startswith("M") and Is.startswith("M"): return "A" if Fs == Is else "R"
    for suf in ("T", "°", "'"):
        if Fs.endswith(suf) and Is.endswith(suf): return "A" if Fs == Is else "R"
    fn, inn = num(F), num(I)
    if fn is None or inn is None: return "A" if Fs == Is else "R"
    lt, mt = num(L) or 0.0, num(M) or 0.0
    if fn == inn and fn > 0: return "A"
    if inn - lt <= fn and inn > fn: return "A"
    if fn + mt <= inn and inn < fn: return "A"
    return "R"

_TOL_REL = [0.3, 0.25, 0.15, 0.2, 0.15]
def ap_damping(p, f, regra="relativa"):
    """Coluna Ap da aba DampingForce. Os modelos têm duas fórmulas:
    - «faixa» (Cartucho): cada velocidade dentro de ±30/25/15/15/15 % do PERFECT, com ±30 N a menos na faixa abaixo de 1000 N;
    - «relativa» (os outros): |forn − PERFECT| ≤ 30 % (+0,03) na 1ª velocidade e ≤ 25/15/20/15 % nas outras; PERFECT vazio da 2ª à 5ª dá erro de divisão e o
      modelo mostra vazio. Sem nenhum valor do PERFECT: vazio. Vazio conta 0, como no Excel."""
    pv, fv = [num(x) or 0.0 for x in (p or [])[:5]], [num(x) or 0.0 for x in (f or [])[:5]]
    if not any(pv): return ""
    pv += [0.0] * (5 - len(pv)); fv += [0.0] * (5 - len(fv))
    if regra == "faixa":
        for c, h, t in zip(pv, fv, _TOL_DAMP):
            lo, hi = (c * (1 - t) + 30, c * (1 + t) - 30) if c < 1000 else (c * (1 - t), c * (1 + t))
            if not (lo <= h <= hi): return "R"
        return "A"
    if not all(pv[1:]): return ""
    ok = abs(fv[0] - pv[0]) <= abs(pv[0] * _TOL_REL[0]) + 0.03 and all(abs(fv[i] - pv[i]) / pv[i] <= _TOL_REL[i] for i in range(1, 5))
    return "A" if ok else "R"

def _regra_damping(fam): return next((x["damping"] for x in familias() if x["v"] == (fam or "").upper()), "relativa")

def _melhoria_padrao(l):
    return f"CHANGE TO {l.get('p')}".upper() if ap(l) == "R" and str(l.get("p") or "").strip() else ""

# ---------------- registro ----------------
def _rd_info(kind, code):
    sug = KINDS.get(kind, kind)
    rows = q("SELECT description,make,vehicle,application_text,year_from,year_to,supplier,product_id FROM rd_projects WHERE upper(code)=upper(?) AND suggestion=? ORDER BY id", (code, sug))
    prod = q1("SELECT id,description,family FROM products WHERE upper(perfect_code)=upper(?)", (code,))
    anos = sorted({y for r in rows for y in (r["year_from"], r["year_to"]) if y})
    junta = lambda k: ", ".join(dict.fromkeys(str(r[k]).strip() for r in rows if r[k]))
    return {"description": (prod or {}).get("description") or next((r["description"] for r in rows if r["description"]), None),
            "make": junta("make"), "vehicle": junta("vehicle"), "application": junta("application_text"), "years": f"{anos[0]}-{anos[-1]}" if len(anos) > 1 else (str(anos[0]) if anos else ""),
            "suppliers": [s for s in dict.fromkeys(r["supplier"] for r in rows if r["supplier"])], "family": (prod or {}).get("family"), "in_rd": bool(rows)}

# ---------------- nome do arquivo, PERFECT já preenchido, posições e par LD/LE (ajuste 3 da etapa 24) ----------------
def _chave(t): return re.sub(r"[^A-Z0-9]", "", str(t or "").upper())

def _fornecedores_conhecidos():
    out = {"EWIN": "E-WIN"}
    try:
        for r in q("SELECT DISTINCT upper(supplier) s FROM rd_projects WHERE supplier IS NOT NULL UNION SELECT upper(supplier) FROM supplier_ex"):
            if r["s"]: out.setdefault(_chave(r["s"]), r["s"].strip())
    except Exception: pass
    return out

def ler_nome(nome, code=None):
    """Fornecedor, código do fornecedor e revisão pelo nome do arquivo do desenho, no padrão «RED - AMD0128 - ZS - DQ32713 - REV.06».
    O código do fornecedor é o pedaço logo depois do fornecedor (se não for o código AMD nem a revisão). Sem fornecedor conhecido no nome: nada."""
    base = os.path.splitext(os.path.basename(nome or ""))[0]
    base = re.sub(r"\s*\(\d+\)\s*$", "", base); base = re.sub(r"^\d+_(?=\D)", "", base)          # «(1)» de download repetido; «7_» do nome guardado em Desenhos
    partes = [p.strip() for p in re.split(r"\s+-\s*|\s*-\s+", base) if p.strip()]
    conhecidos, out = _fornecedores_conhecidos(), {}
    rev = lambda p: re.fullmatch(r"REV\.?\s*(\w+)", p.upper())
    for i, p in enumerate(partes):
        if rev(p): out["rev"] = rev(p).group(1); continue
        if "supplier" not in out and _chave(p) in conhecidos:
            out["supplier"] = conhecidos[_chave(p)]
            prox = partes[i + 1] if i + 1 < len(partes) else ""
            if prox and not rev(prox) and not re.fullmatch(r"AMD\d+", _chave(prox)) and _chave(prox) != _chave(code) and _chave(prox) not in conhecidos:
                out["supplier_code"] = prox.upper()
    return out

def _num_txt(x): return f"{x:g}" if isinstance(x, (int, float)) else ""

def _preencher_perfect(code, linhas, sem_id=None):
    """Coluna PERFECT já preenchida (só nas linhas vazias): os valores do desenho PERFECT não mudam de fornecedor para fornecedor. Fonte, em ordem:
    a última validação do mesmo código, a do par LD/LE e as dimensões do catálogo (Lmax, Lmin, curso, Ø haste, Ø tubo, corpo). `fonte_p` diz de onde veio."""
    if not linhas: return linhas
    pr = par(code); cods = [c for c in (code, pr["code"] if pr else None) if c]
    for c in cods:
        rows = q("SELECT id, code, dados, updated_at FROM validacoes WHERE upper(code)=upper(?) AND id<>? ORDER BY updated_at DESC, id DESC LIMIT 5", (c, sem_id or 0))
        for r in rows:
            ant = {(l.get("nome") or "").upper(): l for l in (json.loads(r["dados"] or "{}").get("linhas") or []) if str(l.get("p") or "").strip()}
            if not ant: continue
            for l in linhas:
                a = ant.get((l.get("nome") or "").upper())
                if a and not str(l.get("p") or "").strip():
                    l.update(p=a.get("p") or "", tm=a.get("tm") or "", tn=a.get("tn") or "", fonte_p=f"validação de {r['code']} ({(r['updated_at'] or '')[:10]})")
            break
    dm = q1("SELECT d.* FROM dimensions d JOIN products p ON p.id=d.product_id WHERE upper(p.perfect_code)=upper(?)", (code,))
    if dm:
        curso = dm.get("stroke_mm") or (dm["lmax_mm"] - dm["lmin_mm"] if dm.get("lmax_mm") and dm.get("lmin_mm") else None)
        cat = {"LMAX": dm.get("lmax_mm"), "LMIN": dm.get("lmin_mm"), "S": curso, "ROD DIAMETER": dm.get("rod_diameter_mm"), "BODY DIAMETER": dm.get("tube_diameter_mm"), "BODY LENGTH": dm.get("body_length_mm")}
        for l in linhas:
            x = cat.get((l.get("nome") or "").upper())
            if x and not str(l.get("p") or "").strip(): l.update(p=_num_txt(x), fonte_p="catálogo")
    return linhas

def par(code):
    """Par do outro lado (LD × LE) pela planilha Lados (side_pairs). Só itens com lados (LD ou LE na descrição); LD/LE num item só não tem par."""
    p = q1("SELECT id, description FROM products WHERE upper(perfect_code)=upper(?)", (code or "",))
    if not p: return None
    r = q1("SELECT CASE WHEN right_product_id=? THEN left_product_id ELSE right_product_id END o FROM side_pairs WHERE right_product_id=? OR left_product_id=?", (p["id"],) * 3)
    o = q1("SELECT perfect_code, description FROM products WHERE id=?", (r["o"],)) if r and r["o"] else None
    meu, dele = db.side_from_text(p["description"]), db.side_from_text(o["description"]) if o else None
    if not o or meu not in ("direito", "esquerdo") or dele not in ("direito", "esquerdo") or meu == dele: return None
    return {"code": o["perfect_code"].upper(), "side": dele, "meu_lado": meu}

LADO_CURTO = {"direito": "LD", "esquerdo": "LE"}

def _fonte_posicoes(v):
    """De onde reaproveitar as posições dos números: PERFECT = última validação do mesmo código (o desenho PERFECT é o mesmo);
    fornecedor = última validação do mesmo fornecedor e família (o fornecedor costuma usar o mesmo formato de desenho)."""
    out = {}
    def tem(dados, k): return any(l.get(k) for l in (json.loads(dados or "{}").get("linhas") or []))
    for r in q("SELECT id, code, dados FROM validacoes WHERE upper(code)=upper(?) AND id<>? ORDER BY updated_at DESC LIMIT 5", (v["code"], v["id"])):
        if tem(r["dados"], "pp"): out["pp"] = {"id": r["id"], "code": r["code"]}; break
    if v.get("supplier") and v.get("family"):          # mesmo código e fornecedor antes; depois o mesmo fornecedor e família
        for r in q("""SELECT id, code, dados FROM validacoes WHERE upper(coalesce(supplier,''))=upper(?) AND family=? AND id<>?
                      ORDER BY upper(code)=upper(?) DESC, updated_at DESC LIMIT 8""", (v["supplier"], v["family"], v["id"], v["code"])):
            if tem(r["dados"], "pf"): out["pf"] = {"id": r["id"], "code": r["code"], "supplier": v["supplier"]}; break
    return out

def criar(kind, code, by=None):
    """Abre a bancada do item: devolve a validação em andamento do código (se houver) ou cria uma nova, com fornecedor e família sugeridos."""
    kind = kind if kind in KINDS else "rd"; code = (code or "").strip().upper()
    if not code: raise ValueError("Informe o código.")
    v = q1("SELECT id FROM validacoes WHERE kind=? AND upper(code)=? AND status='andamento' ORDER BY id DESC", (kind, code))
    if v: return v["id"]
    info = _rd_info(kind, code)
    if not info["in_rd"]: raise ValueError(f"{code} não está em {KINDS[kind]}.")
    fams = {x["v"] for x in familias()}; fam = (info["family"] or "").upper()
    fam = fam if fam in fams else None
    dados = {"linhas": _preencher_perfect(code, _linhas_da_familia(fam)) if fam else [], "damping": _damping_vazio()}
    with db.session() as c:
        vid = c.execute("INSERT INTO validacoes(kind,code,supplier,family,received_at,dados,by_user) VALUES(?,?,?,?,?,?,?)",
                        (kind, code, (info["suppliers"] or [None])[0], fam, datetime.date.today().isoformat(), json.dumps(dados, ensure_ascii=False), by)).lastrowid
    return _pasta_limpa(vid)

def _pasta_limpa(vid):
    """Validação nova começa com a pasta vazia: o SQLite reaproveita o número de uma validação apagada, e arquivos que sobraram nela apareceriam aqui."""
    shutil.rmtree(os.path.join(DIR, str(int(vid))), ignore_errors=True); return vid

def _damping_vazio(): return {"p": {"pf": [""] * 5, "py": [""] * 5}, "f": {"pf": [""] * 5, "py": [""] * 5}}

def _row(vid):
    v = q1("SELECT * FROM validacoes WHERE id=?", (vid,))
    if not v: raise LookupError("Validação não encontrada.")
    v["dados"] = json.loads(v["dados"] or "{}"); v["dados"].setdefault("linhas", []); v["dados"].setdefault("damping", _damping_vazio()); v["dados"].setdefault("mascara", []); v["dados"].setdefault("mola", False)
    return v

def _arquivo(vid, nome):
    p = os.path.join(DIR, str(int(vid)), nome)
    return p if os.path.isfile(p) else None

def obter(vid):
    """Tudo o que a bancada desenha: cabeçalho, imagens disponíveis, linhas com Ap e a conta, damping com Ap, famílias e arquivos gerados."""
    v = _row(vid); d = v["dados"]
    for l in d["linhas"]: l["ap"] = ap(l)
    dm = d["damping"]
    v["damping_regra"] = rg = _regra_damping(v["family"])
    v["damping_ap"] = {"pf": ap_damping(dm["p"]["pf"], dm["f"]["pf"], rg), "py": ap_damping(dm["p"]["py"], dm["f"]["py"], rg)}
    usadas = [l for l in d["linhas"] if str(l.get("p") or "").strip() or str(l.get("f") or "").strip()]
    v["conta"] = {"linhas": len(usadas), "conferidas": sum(1 for l in usadas if l.get("conferida")), "A": sum(1 for l in usadas if l["ap"] == "A"), "R": sum(1 for l in usadas if l["ap"] == "R")}
    v["img_ver"] = _versoes(vid); v["imagens"] = {k: bool(n) for k, n in v["img_ver"].items()}
    v["info"] = _rd_info(v["kind"], v["code"]); v["familias"] = familias(); v["status_label"] = STATUS.get(v["status"], v["status"])
    v["kind_label"] = KINDS.get(v["kind"], v["kind"]); v["nome_f008"] = nome_f008(v)
    v["ia"] = ia_disponivel()
    pr = par(v["code"])
    if pr:
        w = q1("SELECT id, status FROM validacoes WHERE kind=? AND upper(code)=? ORDER BY id DESC", (v["kind"], pr["code"]))
        v["par"] = {**pr, "lado": LADO_CURTO[pr["side"]], "meu": LADO_CURTO[pr["meu_lado"]], "validacao": dict(w) if w else None}
    else: v["par"] = None
    v["reaproveitar"] = {}
    if v["status"] == "andamento":          # só oferece quando a outra validação tem número para alguma linha que aqui ainda não tem
        for lado, f in _fonte_posicoes(v).items():
            ant = {(l.get("nome") or "").upper() for l in _row(f["id"])["dados"]["linhas"] if l.get(lado)}
            n = sum(1 for l in d["linhas"] if not l.get(lado) and (l.get("nome") or "").upper() in ant)
            if n: v["reaproveitar"][lado] = {**f, "n": n}
    return v

def nome_f008(v):
    return f"F-008 - Validation Test - Rev.00 - {_seguro(v['code'])} - {_seguro(v.get('supplier') or 'FORNECEDOR')} - {_seguro(v.get('supplier_code') or 'CÓDIGO DO FORNECEDOR')} - REV.00"

def _gravar(vid, **campos):
    if "dados" in campos: campos["dados"] = json.dumps(campos["dados"], ensure_ascii=False)
    campos["updated_at"] = _agora()
    with db.session() as c:
        c.execute(f"UPDATE validacoes SET {', '.join(k + '=?' for k in campos)} WHERE id=?", [*campos.values(), vid])

def _so_andamento(v):
    if v["status"] != "andamento": raise ValueError("Esta validação já foi concluída. Para validar de novo, abra uma nova validação.")

def salvar(vid, patch):
    """Rascunho: fornecedor, código do fornecedor, data de recebimento, família (refaz as linhas, guardando valores de mesmo nome), linhas e damping."""
    v = _row(vid); _so_andamento(v); d = v["dados"]; campos = {}
    for k in ("supplier", "supplier_code", "received_at"):
        if k in patch: campos[k] = (str(patch[k] or "").strip() or None) if k != "supplier" else (str(patch[k] or "").strip().upper() or None)
    if "family" in patch and (patch["family"] or "").upper() != (v["family"] or ""):
        fam = (patch["family"] or "").upper()
        if fam and fam not in {x["v"] for x in familias()}: raise ValueError("Família sem modelo F-008.")
        antiga = next((l for l in d["linhas"] if l.get("mola")), None)
        campos["family"] = fam or None; d["linhas"] = _linhas_da_familia(fam, [l for l in d["linhas"] if not l.get("mola")]) if fam else []
        if fam and d.get("mola"): d["linhas"] = _aplicar_mola(d["linhas"], True, antiga)
        d["linhas"] = _preencher_perfect(v["code"], d["linhas"], vid)
    if "linhas" in patch:
        novas = []
        for i, l in enumerate(patch["linhas"][:NLINHAS], 1):
            x = {**_linha_vazia(), **{k: l.get(k) for k in _linha_vazia() if k in l}}; x["n"] = i
            for k in ("nome", "p", "f", "tm", "tn", "melhoria", "obs"): x[k] = str(x[k] or "").strip()
            x["nome"] = x["nome"].upper(); x["conferida"] = bool(x["conferida"]); x["mola"] = bool(l.get("mola"))
            if l.get("fonte_p") and str(l.get("p") or "").strip(): x["fonte_p"] = str(l["fonte_p"])[:80]
            t = num(x["tn"])
            if t is not None and t > 0: x["tn"] = f"-{x['tn']}"          # tolerância «−» sempre negativa (a fórmula soma F + M)
            for k in ("pp", "pf"):
                pt = x.get(k); x[k] = [min(max(float(pt[0]), 0.0), 1.0), min(max(float(pt[1]), 0.0), 1.0)] if isinstance(pt, (list, tuple)) and len(pt) == 2 else None
            if x["nome"]: novas.append(x)
        d["linhas"] = novas
    if "mola" in patch:
        d["mola"] = bool(patch["mola"])
        if d["linhas"]: d["linhas"] = _aplicar_mola(d["linhas"], d["mola"], next((l for l in d["linhas"] if l.get("mola")), None))
    if patch.get("reaproveitar"):          # posições dos números de outra validação (só nas linhas sem número)
        fonte = _fonte_posicoes(v)
        for lado in [x for x in patch["reaproveitar"] if x in ("pp", "pf")]:
            if lado not in fonte: continue
            ant = {(l.get("nome") or "").upper(): l.get(lado) for l in (_row(fonte[lado]["id"])["dados"]["linhas"])}
            for l in d["linhas"]:
                if not l.get(lado) and ant.get((l.get("nome") or "").upper()): l[lado] = ant[(l["nome"] or "").upper()]
    if patch.get("espelhar") in ("pp", "pf", "ambos"):          # desenho do outro lado espelhado: as posições também (x → 1 − x)
        for l in d["linhas"]:
            for lado in (("pp", "pf") if patch["espelhar"] == "ambos" else (patch["espelhar"],)):
                if l.get(lado): l[lado] = [round(1 - l[lado][0], 6), l[lado][1]]
    if "mascara" in patch:
        if not _arquivo(vid, "perfect.png"): raise ValueError("Envie primeiro o desenho PERFECT.")
        d["mascara"] = _ops_mascara(patch["mascara"]); _aplicar_mascara(vid, d["mascara"])
    if "damping" in patch:
        dm = patch["damping"] or {}
        nominal = lambda x: str(x or "").split("±")[0].strip()          # «1155±365» → 1155 (o modelo usa só o nominal)
        d["damping"] = {lado: {g: ([nominal(x) for x in ((dm.get(lado) or {}).get(g) or [])][:5] + [""] * 5)[:5] for g in ("pf", "py")} for lado in ("p", "f")}
    campos["dados"] = d; _gravar(vid, **campos)
    return obter(vid)

# ---------------- desenhos ----------------
LARGURA = 2400
def _png_de(path, ext):
    from PIL import Image
    if ext == ".pdf":
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(path)
        try:
            pg = pdf[0]; w, _ = pg.get_size(); img = pg.render(scale=LARGURA / max(w, 1)).to_pil()
        finally: pdf.close()
    else:
        with Image.open(path) as im: img = im.convert("RGB"); img.load()
        if img.width > LARGURA: img = img.resize((LARGURA, round(img.height * LARGURA / img.width)))
    return img.convert("RGB")

def desenho(vid, lado, storage):
    """Envio de um desenho (PDF, PNG ou JPG). lado = perfect | fornecedor. O PERFECT novo apaga a versão limpa anterior."""
    v = _row(vid); _so_andamento(v)
    if lado not in ("perfect", "fornecedor"): raise ValueError("Lado inválido.")
    nome = os.path.basename((storage.filename or "").replace("\\", "/")); ext = os.path.splitext(nome)[1].lower()
    if ext not in (".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".webp"): raise ValueError("Envie o desenho em PDF, PNG ou JPG.")
    p = _pasta(vid)
    for x in glob.glob(os.path.join(p, f"{lado}_original.*")): os.remove(x)
    orig = os.path.join(p, f"{lado}_original{ext}"); storage.save(orig)
    try: img = _png_de(orig, ext)
    except Exception as e: os.remove(orig); raise ValueError(f"Não foi possível abrir o desenho ({e}).")
    img.save(os.path.join(p, f"{lado}.png"), optimize=True)
    campos = {("perfect_name" if lado == "perfect" else "supplier_name"): nome}
    lido = ler_nome(nome, v["code"]) if lado == "fornecedor" else {}
    if lido.get("supplier"): campos["supplier"] = lido["supplier"]          # Q4: fornecedor e código do fornecedor pelo nome do arquivo
    if lido.get("supplier_code"): campos["supplier_code"] = lido["supplier_code"]
    if lado == "perfect":           # desenho novo: a máscara anterior não vale mais
        try: os.remove(os.path.join(p, "perfect_limpo.png"))
        except OSError: pass
        v["dados"]["mascara"] = []; campos["dados"] = v["dados"]
    _gravar(vid, **campos)
    out = obter(vid); out["lido_do_nome"] = lido
    return out

def _aplicar_mascara(vid, ops):
    """Desenho PERFECT com a máscara limpa = perfect.png + as operações da ferramenta de seleção, na ordem: «apagar» pinta o retângulo de branco;
    «manter» deixa só o retângulo. Coordenadas em fração da imagem. Sem operações, não há versão limpa (vale o desenho como veio)."""
    from PIL import Image, ImageDraw
    base = _arquivo(vid, "perfect.png"); destino = os.path.join(_pasta(vid), "perfect_limpo.png")
    if not ops or not base:
        try: os.remove(destino)
        except OSError: pass
        return
    with Image.open(base) as im: img = im.convert("RGB"); img.load()
    W, H = img.size
    for o in ops:
        x, y, w, h = o["r"]; box = (round(x * W), round(y * H), round((x + w) * W), round((y + h) * H))
        if o["t"] == "apagar": ImageDraw.Draw(img).rectangle(box, fill=(255, 255, 255))
        else:
            novo = Image.new("RGB", img.size, (255, 255, 255)); novo.paste(img.crop(box), box[:2]); img = novo
    img.save(destino, optimize=True)

def _ops_mascara(lst):
    out = []
    for o in (lst or [])[:200]:
        try:
            t = o.get("t"); r = [min(max(float(v), 0.0), 1.0) for v in o.get("r")][:4]
            if t in ("apagar", "manter") and len(r) == 4 and r[2] > 0.001 and r[3] > 0.001: out.append({"t": t, "r": r})
        except (TypeError, ValueError, AttributeError): continue
    return out

TELA = 1600
def imagem(vid, nome, tela=False):
    """PNG cheio (F-008) ou, com `tela`, a versão leve da bancada (JPEG de 1600 px, refeita quando o PNG muda)."""
    if nome not in ("perfect", "perfect_limpo", "fornecedor"): return None
    p = _arquivo(vid, nome + ".png")
    if not p or not tela: return p
    t = os.path.join(os.path.dirname(p), nome + "_tela.jpg")
    if not os.path.isfile(t) or os.path.getmtime(t) < os.path.getmtime(p):
        from PIL import Image
        with Image.open(p) as im:
            img = im.convert("RGB"); img.load()
        if img.width > TELA: img = img.resize((TELA, round(img.height * TELA / img.width)), Image.LANCZOS)
        img.save(t, "JPEG", quality=88, optimize=True)
    return t

def _versoes(vid):
    """Chave de cada imagem para o navegador: muda só quando a imagem muda (antes mudava a cada gravação e o desenho era baixado de novo)."""
    out = {}
    for k in ("perfect", "perfect_limpo", "fornecedor"):
        p = _arquivo(vid, k + ".png"); out[k] = int(os.path.getmtime(p) * 1000) if p else 0
    return out

def _img_perfect(vid): return _arquivo(vid, "perfect_limpo.png") or _arquivo(vid, "perfect.png")

# ---------------- leitura pelo Claude ----------------
def ia_disponivel():
    """{ok, ligada, motivo}. Desligada em Configurações (padrão): ok=False, sem motivo — a bancada não mostra o botão nem aviso e nada vai para a API.
    Ligada: exige o SDK `anthropic` e uma credencial (ANTHROPIC_API_KEY no ~/.perfect_shock_data/.env ou no ambiente)."""
    import rules
    if not rules.validacao_ia(): return {"ok": False, "ligada": False, "motivo": ""}
    r = _ia_pronta(); r["ligada"] = True; return r

def _ia_pronta():
    try: import anthropic  # noqa: F401
    except ImportError: return {"ok": False, "motivo": "Falta instalar o SDK do Claude: .venv\\Scripts\\python.exe -m pip install anthropic"}
    try:
        import data_pipeline; data_pipeline.load_env()
    except Exception: pass
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        return {"ok": False, "motivo": "Falta a chave da API: coloque ANTHROPIC_API_KEY=... no arquivo ~/.perfect_shock_data/.env e reabra o app."}
    return {"ok": True, "motivo": ""}

_VAL = {"type": "object", "additionalProperties": False, "required": ["valor", "tol_mais", "tol_menos", "x", "y"],
        "properties": {"valor": {"type": "string"}, "tol_mais": {"type": "string"}, "tol_menos": {"type": "string"}, "x": {"type": "number"}, "y": {"type": "number"}}}
_LISTA5 = {"type": "array", "items": {"type": "string"}}
_DAMP = {"type": "object", "additionalProperties": False, "required": ["pf", "py"], "properties": {"pf": _LISTA5, "py": _LISTA5}}
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["medidas", "damping"],
          "properties": {"medidas": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["nome", "perfect", "fornecedor", "observacao"],
                                                                "properties": {"nome": {"type": "string"}, "perfect": _VAL, "fornecedor": _VAL, "observacao": {"type": "string"}}}},
                         "damping": {"type": "object", "additionalProperties": False, "required": ["perfect", "fornecedor"], "properties": {"perfect": _DAMP, "fornecedor": _DAMP}}}}

SISTEMA = """Você lê desenhos técnicos de amortecedores automotivos para a engenharia da PERFECT, que compara o desenho de referência (PERFECT) com o desenho de um fornecedor.
Você só lê e lista: não aprova nem reprova nada. Quem confere cada valor é o engenheiro.

Para cada medida da lista, procure a cota nos DOIS desenhos e devolva:
- valor: como está no desenho, em mm, com ponto decimal e sem o símbolo Ø («Ø51±2.5» → «51»). Roscas ficam como texto («M12X1.25-6h»). Materiais e sistema em inglês, em maiúsculas
  («PA6», «PLASTIC» para 塑料, «RUBBER», «GAS», «OIL»). Sem a cota no desenho: valor "".
- tol_mais e tol_menos: a tolerância da cota («553±3» → "3" e "-3»; «12.1 +0.15/0» → "0.15" e "0"; sem tolerância: "" e "").
- x e y: onde está o TEXTO da cota na imagem, de 0 a 1 (0,0 = canto superior esquerdo). Sem a cota: -1 e -1.
Significados: LMAX = comprimento estendido (Lmax), LMIN = comprimento comprimido (Lmin), S = curso (Stroke, «S=»), SYSTEM = GAS ou OIL (tabela de damping, carimbo ou nota).
Ignore carimbo, logo e números de desenho. Não invente: na dúvida, valor "" e explique em observacao (em português, curto).
Use o nome da medida exatamente como está na lista. Damping force: os valores de Pf e Py nas 5 velocidades (0.079, 0.157, 0.314, 0.520, 0.750 m/s), só o número nominal
(«1155±365» → "1155"); velocidade sem valor: ""."""

def _chamar_claude(imagens_png, texto):
    """Uma chamada à Messages API (Claude Opus 5.5, esforço alto, saída em JSON pelo esquema). Devolve o dict lido. Os testes substituem esta função."""
    import base64, anthropic
    try:
        import data_pipeline; data_pipeline.load_env()
    except Exception: pass
    client = anthropic.Anthropic()
    conteudo = []
    for rotulo, png in imagens_png:
        conteudo += [{"type": "text", "text": rotulo}, {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": base64.standard_b64encode(png).decode("ascii")}}]
    conteudo.append({"type": "text", "text": texto})
    try:
        with client.beta.messages.stream(model=MODELO_IA, max_tokens=32000, system=SISTEMA, messages=[{"role": "user", "content": conteudo}],
                                         output_config={"effort": "high", "format": {"type": "json_schema", "schema": SCHEMA}},
                                         betas=["server-side-fallback-2026-07-01"], fallbacks="default") as st:
            msg = st.get_final_message()
    except anthropic.AuthenticationError: raise ValueError("A chave da API do Claude foi recusada. Confira ANTHROPIC_API_KEY no ~/.perfect_shock_data/.env.")
    except anthropic.RateLimitError: raise ValueError("Limite de uso da API do Claude atingido agora. Tente de novo em alguns minutos.")
    except anthropic.APIConnectionError: raise ValueError("Sem conexão com a API do Claude. Confira a internet e tente de novo.")
    except anthropic.APIStatusError as e: raise ValueError(f"A API do Claude respondeu com erro {e.status_code}. Tente de novo; se continuar, digite as medidas.")
    if msg.stop_reason == "refusal": raise ValueError("O Claude não leu estes desenhos. Digite as medidas na tabela.")
    if msg.stop_reason == "max_tokens": raise ValueError("A resposta do Claude veio cortada. Tente ler de novo.")
    texto_resp = next((b.text for b in msg.content if b.type == "text"), "")
    try: return json.loads(texto_resp)
    except json.JSONDecodeError: raise ValueError("A resposta do Claude veio em formato inesperado. Tente ler de novo.")

def _png_para_ia(path, lado_max=2000):
    from PIL import Image
    with Image.open(path) as im:
        img = im.convert("RGB"); img.load()
    if max(img.size) > lado_max:
        r = lado_max / max(img.size); img = img.resize((round(img.width * r), round(img.height * r)))
    b = io.BytesIO(); img.save(b, "PNG", optimize=True); return b.getvalue()

def ler(vid):
    """Lê os dois desenhos com o Claude e preenche a tabela: valores, tolerâncias, posições e damping. Linhas já conferidas pelo usuário ficam como estão;
    as outras voltam a «não conferida». Nada é aprovado aqui."""
    v = _row(vid); _so_andamento(v); d = v["dados"]
    if not v["family"]: raise ValueError("Escolha a família antes de ler as medidas.")
    pp, pf = _img_perfect(vid), _arquivo(vid, "fornecedor.png")
    if not pp or not pf: raise ValueError("Envie os dois desenhos antes de ler as medidas.")
    disp = ia_disponivel()
    if not disp["ok"]: raise ValueError(disp["motivo"] or "A leitura pelo Claude está desligada (Configurações › Regras de negócio). Digite as medidas no desenho.")
    nomes = [l["nome"] for l in d["linhas"]] or _medidas(v["family"])
    texto = ("Medidas do modelo F-008 da família " + v["family"] + " (nome exato, uma por linha):\n" + "\n".join(nomes) +
             "\n\nImagem 1 = desenho PERFECT (referência). Imagem 2 = desenho do fornecedor " + (v["supplier"] or "") + ". Devolva uma entrada para cada medida da lista.")
    r = _chamar_claude([("Imagem 1: desenho PERFECT (referência)", _png_para_ia(pp)), ("Imagem 2: desenho do fornecedor", _png_para_ia(pf))], texto)
    por_nome = {(m.get("nome") or "").strip().upper(): m for m in (r.get("medidas") or [])}
    pos = lambda x: [float(x["x"]), float(x["y"])] if isinstance(x, dict) and 0 <= float(x.get("x", -1)) <= 1 and 0 <= float(x.get("y", -1)) <= 1 else None
    n_lidas = 0
    for l in d["linhas"]:
        if l.get("conferida"): continue
        m = por_nome.get(l["nome"].upper())
        if not m: continue
        p, f = m.get("perfect") or {}, m.get("fornecedor") or {}
        l.update(p=str(p.get("valor") or "").strip(), f=str(f.get("valor") or "").strip(), tm=str(p.get("tol_mais") or "").strip(), tn=str(p.get("tol_menos") or "").strip(),
                 pp=pos(p), pf=pos(f), obs=str(m.get("observacao") or "").strip(), lida=True, conferida=False)
        t = num(l["tn"])
        if t is not None and t > 0: l["tn"] = "-" + l["tn"]
        l["melhoria"] = _melhoria_padrao(l)
        if l["p"] or l["f"]: n_lidas += 1
    dm = r.get("damping") or {}
    for lado, k in (("p", "perfect"), ("f", "fornecedor")):
        for g in ("pf", "py"):
            vals = [str(x or "").strip() for x in ((dm.get(k) or {}).get(g) or [])][:5]
            if any(vals): d["damping"][lado][g] = vals + [""] * (5 - len(vals))
    _gravar(vid, dados=d, leitura_em=_agora())
    out = obter(vid); out["lidas"] = n_lidas
    return out

# ---------------- F-008 ----------------
def _px_coluna(ws, letra):
    w = ws.column_dimensions[letra].width if letra in ws.column_dimensions and ws.column_dimensions[letra].width else 8.43
    return w * 7 + 5
def _px_linha(ws, r):
    h = ws.row_dimensions[r].height if r in ws.row_dimensions and ws.row_dimensions[r].height else 15
    return h * 96 / 72

def _por_imagem(ws, pil, faixa):
    """Põe a imagem dentro da área mesclada `faixa` (ex.: S10:AJ34), mantendo a proporção, com 6 px de folga."""
    from openpyxl.drawing.image import Image as XLImage
    from openpyxl.utils import range_boundaries, get_column_letter
    c1, r1, c2, r2 = range_boundaries(faixa)
    W = sum(_px_coluna(ws, get_column_letter(c)) for c in range(c1, c2 + 1)) - 12; H = sum(_px_linha(ws, r) for r in range(r1, r2 + 1)) - 12
    esc = min(W / pil.width, H / pil.height)
    b = io.BytesIO(); pil.save(b, "PNG"); b.seek(0)
    xi = XLImage(b); xi.width, xi.height = int(pil.width * esc), int(pil.height * esc)
    from openpyxl.drawing.spreadsheet_drawing import OneCellAnchor, AnchorMarker
    from openpyxl.drawing.xdr import XDRPositiveSize2D
    from openpyxl.utils.units import pixels_to_EMU
    xi.anchor = OneCellAnchor(_from=AnchorMarker(col=c1 - 1, colOff=pixels_to_EMU(6), row=r1 - 1, rowOff=pixels_to_EMU(6)), ext=XDRPositiveSize2D(pixels_to_EMU(xi.width), pixels_to_EMU(xi.height)))
    ws.add_image(xi)

def _fonte(tam):
    from PIL import ImageFont
    for f in ("arialbd.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf"):
        try: return ImageFont.truetype(f, tam)
        except OSError: continue
    return ImageFont.load_default()

def marcar(path, linhas, campo):
    """Imagem com os números das medidas (quadrado vermelho de borda, número vermelho, como no F-008) na posição `campo` (pp | pf)."""
    from PIL import Image, ImageDraw
    with Image.open(path) as im: img = im.convert("RGB"); img.load()
    dr = ImageDraw.Draw(img); lado = max(22, round(img.width * 0.016)); ft = _fonte(round(lado * 0.68)); vermelho = (231, 43, 59)
    for l in linhas:
        pt = l.get(campo)
        if not pt or not (str(l.get("p") or "").strip() or str(l.get("f") or "").strip()): continue
        x, y = pt[0] * img.width, pt[1] * img.height; t = str(l["n"]); w = max(lado, dr.textlength(t, font=ft) + lado * 0.4)
        box = [x - w / 2, y - lado - 4, x + w / 2, y - 4]
        if box[1] < 0: box = [box[0], y + 4, box[2], y + 4 + lado]
        dr.rectangle(box, fill=(255, 255, 255), outline=vermelho, width=max(2, lado // 10))
        dr.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), t, fill=vermelho, font=ft, anchor="mm")
    return img

def _valor_excel(s):
    s = str(s or "").strip()
    if not s: return None
    n = num(s)
    if n is not None and not s.upper().startswith("M"): return int(n) if n == int(n) else n
    return s

def _dados_aba(wb, v):
    ws = wb["Dados"]; info = _rd_info(v["kind"], v["code"])
    try: rec = datetime.datetime.fromisoformat(v["received_at"]) if v.get("received_at") else datetime.datetime.now()
    except ValueError: rec = datetime.datetime.now()
    for cel, val in (("B9", v["code"]), ("B14", info["make"]), ("B15", info["vehicle"]), ("B16", info["application"]), ("B17", info["description"]), ("B18", info["years"]),
                     ("B19", v.get("supplier")), ("B21", rec), ("B22", v.get("supplier_code")), ("B23", "R-D" if v["kind"] == "rd" else "des"), ("B24", 0), ("B25", 0), ("B26", "DRAWING")):
        ws[cel] = val
    ws["B21"].number_format = "mmmm d, yyyy"

def gerar(vid, decisao, by=None, pdf=True):
    """Aprovar ou Reprovar: preenche o modelo F-008 da família e grava o xlsx (e o pdf, pelo Excel do PC). Aprovar sobe o desenho do fornecedor para Desenhos."""
    import openpyxl
    from PIL import Image
    v = _row(vid); _so_andamento(v); d = v["dados"]
    if decisao not in ("aprovada", "reprovada"): raise ValueError("Decisão inválida.")
    if not v["family"]: raise ValueError("Escolha a família.")
    if not v.get("supplier") or not v.get("supplier_code"): raise ValueError("Informe o fornecedor e o código do fornecedor (vão no nome do F-008).")
    pp, pf = _img_perfect(vid), _arquivo(vid, "fornecedor.png")
    if not pp or not pf: raise ValueError("Envie os dois desenhos.")
    usadas = [l for l in d["linhas"] if str(l.get("p") or "").strip() or str(l.get("f") or "").strip()]
    if not usadas: raise ValueError("Nenhuma medida preenchida.")
    falta = [l["n"] for l in usadas if not l.get("conferida")]
    if falta: raise ValueError(f"Confira todas as medidas antes de concluir (faltam as linhas {', '.join(map(str, falta[:8]))}{'…' if len(falta) > 8 else ''}).")
    modelo = _arquivos_modelo().get(v["family"])
    if not modelo: raise ValueError("Modelo F-008 da família não encontrado em bases_exemplo\\VALIDATION.")
    wb = openpyxl.load_workbook(modelo); ws, dmp = wb.worksheets[0], wb.worksheets[1]
    _dados_aba(wb, v)
    for i in range(NLINHAS):
        r = LINHA0 + i; l = d["linhas"][i] if i < len(d["linhas"]) else None
        if not l: continue
        ws.cell(r, 2).value = l["nome"]
        ws.cell(r, 6).value = _valor_excel(l["p"]); ws.cell(r, 9).value = _valor_excel(l["f"])
        tm, tn = str(l.get("tm") or "").strip(), str(l.get("tn") or "").strip()
        if not tm and ap(l) == "R" and (num(l["p"]) is None or num(l["f"]) is None) and not (str(l["p"]).upper().startswith("M") and str(l["f"]).upper().startswith("M")):
            tm = "N"          # texto diferente sem tolerância: a fórmula do modelo daria #VALOR!; «N» na Tol.(+) é a convenção do modelo para reprovar
        ws.cell(r, 12).value = tm.upper() if tm.lower() in ("ok", "n") else _valor_excel(tm)
        ws.cell(r, 13).value = tn.upper() if tn.lower() in ("ok", "n") else _valor_excel(tn)
        ws.cell(r, 15).value = (l.get("melhoria") or "").strip() or None
    dm = d["damping"]
    for g, r in (("pf", 11), ("py", 12)):
        for j in range(5):
            dmp.cell(r, 3 + j).value = _valor_excel(dm["p"][g][j]); dmp.cell(r, 8 + j).value = _valor_excel(dm["f"][g][j])
    with Image.open(pp) as im: ip = im.convert("RGB"); ip.load()
    ifn = marcar(pf, d["linhas"], "pf")
    _por_imagem(ws, ip, "S10:AJ34"); _por_imagem(ws, ifn, "A37:R57"); _por_imagem(dmp, ip, "R11:AI25"); _por_imagem(dmp, ifn, "A28:Q48")
    ws["S50" if decisao == "aprovada" else "S52"] = "X"; dmp["R41" if decisao == "aprovada" else "R43"] = "X"
    try:
        from openpyxl.workbook.properties import CalcProperties
        wb.calculation = CalcProperties(fullCalcOnLoad=True)
    except Exception: pass
    pasta = _pasta(vid); base = nome_f008(v); xlsx = os.path.join(pasta, base + ".xlsx")
    wb.save(xlsx); aviso = None; pdf_nome = None
    if pdf:
        try: _pdf(xlsx, os.path.join(pasta, base + ".pdf")); pdf_nome = base + ".pdf"
        except Exception as e: aviso = f"O PDF não foi gerado ({e}). O xlsx está pronto; gere o PDF pelo Excel se precisar."
    fid = None
    if decisao == "aprovada":
        try: fid = subir_desenho(v)
        except Exception as e: aviso = ((aviso + " ") if aviso else "") + f"O desenho não subiu para Desenhos ({e})."
    _gravar(vid, status=decisao, concluida_em=_agora(), xlsx=base + ".xlsx", pdf=pdf_nome, aviso=aviso, drawing_file_id=fid, by_user=by or v.get("by_user"))
    try: pp_ = preparar_par(vid, by)          # item com lados: o outro lado fica pronto para concluir (ajuste 3)
    except Exception: pp_ = None
    out = obter(vid); out["par_preparado"] = pp_
    return out

PS_PDF = r"""param([string]$x, [string]$p)
$e = New-Object -ComObject Excel.Application
$e.Visible = $false; $e.DisplayAlerts = $false
try {
  $wb = $e.Workbooks.Open($x)
  $e.CalculateFull()
  for ($i = $wb.Worksheets.Count; $i -ge 3; $i--) { $wb.Worksheets.Item($i).Visible = 0 }
  $wb.ExportAsFixedFormat(0, $p)
  $wb.Close($false)
} finally { $e.Quit(); [System.Runtime.InteropServices.Marshal]::ReleaseComObject($e) | Out-Null }
"""
def _pdf(xlsx, pdf):
    """PDF das duas abas de teste pelo Excel instalado no PC (as fórmulas são calculadas pelo próprio Excel)."""
    ps1 = os.path.join(DIR, "_excel_pdf.ps1"); os.makedirs(DIR, exist_ok=True)
    with open(ps1, "w", encoding="utf-8-sig") as fh: fh.write(PS_PDF)
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1, os.path.abspath(xlsx), os.path.abspath(pdf)],
                       capture_output=True, text=True, timeout=240, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if r.returncode != 0 or not os.path.isfile(pdf): raise RuntimeError((r.stderr or r.stdout or "Excel não respondeu").strip().splitlines()[-1][:200])

def subir_desenho(v):
    """Desenho do fornecedor aprovado → Desenhos: arquivo original, nome «RED - <cód> - <forn> - <cód forn> - REV.00», ligado ao código, origem do módulo e
    fonte «Validação». Entra como a revisão vigente (uma acima da maior já cadastrada)."""
    import drawings, uuid
    orig = next(iter(glob.glob(os.path.join(DIR, str(v["id"]), "fornecedor_original.*"))), None)
    if not orig: raise ValueError("arquivo original do fornecedor não encontrado")
    ext = os.path.splitext(orig)[1].lower(); pre = "RED" if v["kind"] == "rd" else "DES"
    nome = f"{pre} - {_seguro(v['code'])} - {_seguro(v['supplier'])} - {_seguro(v['supplier_code'])} - REV.00{ext}"
    tmp = os.path.join(drawings.TMP, "val_" + uuid.uuid4().hex); os.makedirs(tmp, exist_ok=True)
    try:
        cp = os.path.join(tmp, drawings._safe(nome)); shutil.copy2(orig, cp)
        k = drawings._key(v["code"]); top = max([f["rev_num"] for f in drawings._rows_for(k)], default=None)
        rev = 0 if top is None else top + 1
        man = {"kind": "desenho", "files": [{"name": nome, "path": cp, "source": "Validação", "folder": ""}]}
        res = drawings.apply(man, {"0": {"codes": k, "origin": KINDS[v["kind"]], "rev": str(rev)}})
        it = res["items"][0]
        if it["action"] == "duplicado": return None
        row = q1("SELECT id FROM drawing_files WHERE sha256=? AND source='Validação' ORDER BY id DESC", (it["sha"],))
        return row["id"] if row else None
    finally: shutil.rmtree(tmp, ignore_errors=True)

def arquivo_gerado(vid, tipo):
    v = _row(vid); nome = v.get(tipo) if tipo in ("xlsx", "pdf") else None
    p = _arquivo(vid, nome) if nome else None
    return (p, nome) if p else (None, None)

def nova(vid, by=None):
    """Nova validação do mesmo item (depois de uma concluída): copia fornecedor e família; desenhos e medidas começam vazios."""
    v = _row(vid)
    if v["status"] == "andamento": return vid
    ja = q1("SELECT id FROM validacoes WHERE kind=? AND upper(code)=upper(?) AND status='andamento'", (v["kind"], v["code"]))
    if ja: return ja["id"]
    with db.session() as c:
        nid = c.execute("INSERT INTO validacoes(kind,code,supplier,family,received_at,dados,by_user) VALUES(?,?,?,?,?,?,?)",
                        (v["kind"], v["code"], v["supplier"], v["family"], datetime.date.today().isoformat(),
                         json.dumps({"linhas": _preencher_perfect(v["code"], _linhas_da_familia(v["family"])) if v["family"] else [], "damping": _damping_vazio()}, ensure_ascii=False), by)).lastrowid
    return _pasta_limpa(nid)

def preparar_par(vid, by=None):
    """Ao concluir um lado de um item com lados (LD × LE da planilha Lados), deixa a validação do outro lado pronta: família, mola, medidas (valores,
    tolerâncias, melhorias, conferência e posições dos números), damping e fornecedor; o desenho PERFECT vem do vigente do par em Desenhos (se houver).
    Faltam o desenho do fornecedor do par (o código do fornecedor sai do nome do arquivo) e concluir — com a mesma decisão, que fica guardada em
    `origem_par`. Validação do par já com medidas digitadas não é sobrescrita."""
    import copy, drawings
    v = _row(vid); pr = par(v["code"])
    if not pr: return None
    try: pid = criar(v["kind"], pr["code"], by)
    except ValueError: return None
    w = _row(pid)
    if w["status"] != "andamento": return None
    usadas = [l for l in w["dados"]["linhas"] if str(l.get("f") or "").strip()]
    if not usadas:
        d = w["dados"]
        d.update(linhas=copy.deepcopy(v["dados"]["linhas"]), damping=copy.deepcopy(v["dados"]["damping"]), mola=v["dados"].get("mola", False))
        for l in d["linhas"]: l.pop("fonte_p", None); l["obs"] = ""
        d["origem_par"] = {"id": vid, "code": v["code"], "lado": LADO_CURTO.get(pr["meu_lado"]), "decisao": v["status"], "em": _agora()}
        campos = {"dados": d, "family": v["family"], "supplier": v["supplier"], "received_at": v["received_at"]}
        if not _arquivo(pid, "perfect.png"):          # PERFECT do par: o desenho vigente dele em Desenhos (PDF ou imagem)
            try:
                det = drawings.detail(pr["code"]) or {}
                f = next((x for x in det.get("current", []) if (x.get("ext") or "").lower() in (".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".webp")), None)
                fp = drawings.file_path(f["id"])[1] if f else None
                if fp:
                    pasta = _pasta(pid); ext = os.path.splitext(fp)[1].lower(); orig = os.path.join(pasta, "perfect_original" + ext); shutil.copy2(fp, orig)
                    _png_de(orig, ext).save(os.path.join(pasta, "perfect.png"), optimize=True); campos["perfect_name"] = f["filename"]
            except Exception: pass
        _gravar(pid, **campos)
    return {"id": pid, "code": pr["code"], "lado": LADO_CURTO[pr["side"]], "perfect": bool(_arquivo(pid, "perfect.png"))}

def excluir(vid):
    v = _row(vid)
    if v["status"] != "andamento": raise ValueError("Só um rascunho pode ser excluído.")
    with db.session() as c: c.execute("DELETE FROM validacoes WHERE id=?", (vid,))
    shutil.rmtree(os.path.join(DIR, str(int(vid))), ignore_errors=True)

# ---------------- listas ----------------
PEND_FLAGS = ("pend_validacao", "val_reprovada", "pend_desenho_forn")

_cache_pend = {}
def pendentes_rd(kind):
    """Itens do servidor que pedem validação de desenho (em andamento): pendente validação, validação reprovada, pendente desenho do fornecedor.
    Guardado até o banco mudar ou o dia virar (≈ 0,5–0,9 s na cópia; antes rodava a cada abertura do Redesenvolvimento e da tela Validação)."""
    import rd as R
    k = (db.versao(), datetime.date.today(), db.DB_PATH)
    if kind in _cache_pend and _cache_pend[kind][0] == k: return _cache_pend[kind][1]
    sug = KINDS[kind]; out = {}
    for fl in PEND_FLAGS:
        for r in R.items(sug, {"flag": fl, "status": "andamento", "all": 1})["rows"]:
            out.setdefault(r["code"].upper(), {**r, "flags": []})["flags"].append(fl)
    _cache_pend[kind] = (k, out)
    return out

def _local_por_codigo(kind):
    out = {}
    for v in q("SELECT id,code,status,supplier,supplier_code,family,dados,updated_at FROM validacoes WHERE kind=? ORDER BY id", (kind,)):
        out[v["code"].upper()] = v          # a mais recente fica
    return out

def _conta(dados):
    try: ls = json.loads(dados or "{}").get("linhas") or []
    except ValueError: ls = []
    us = [l for l in ls if str(l.get("p") or "").strip() or str(l.get("f") or "").strip()]
    return {"linhas": len(us), "conferidas": sum(1 for l in us if l.get("conferida")), "A": sum(1 for l in us if ap(l) == "A"), "R": sum(1 for l in us if ap(l) == "R")}

def aba(kind, f):
    """Aba «Validar itens» do R-D: sem busca, os pendentes no servidor (validação primeiro); com busca, qualquer item em andamento que case.
    Cada linha leva a situação da validação no app."""
    import rd as R
    kind = kind if kind in KINDS else "rd"; loc = _local_por_codigo(kind); pend = pendentes_rd(kind)
    if (f.get("q") or "").strip():
        rows = {r["code"].upper(): {**r, "flags": pend.get(r["code"].upper(), {}).get("flags", [])} for r in R.items(KINDS[kind], {"q": f["q"], "status": "andamento", "all": 1})["rows"]}
    else: rows = dict(pend)
    ordem = {fl: i for i, fl in enumerate(PEND_FLAGS)}
    out = []
    for k, r in rows.items():
        v = loc.get(k)
        out.append({"code": r["code"], "description": r.get("description"), "vehicles": r.get("vehicles"), "suppliers": r.get("suppliers"), "flags": r.get("flags") or [],
                    "subs": [s for s in (r.get("subs") or []) if s["k"] in ("validacao", "desenho")],
                    "validacao": {"id": v["id"], "status": v["status"], "status_label": STATUS[v["status"]], **_conta(v["dados"])} if v else None})
    out.sort(key=lambda x: (min([ordem[fl] for fl in x["flags"]] or [9]), x["validacao"] is not None and x["validacao"]["status"] != "andamento", x["code"]))
    return {"total": len(out), "pendentes": len(pend), "rows": out}

def listagem(f):
    """Tela «Validação» do menu: todas as validações, com estágios (Pendentes no R-D, Em andamento, Aprovadas, Reprovadas) e filtros."""
    w, p = ["1=1"], []
    if f.get("kind") in KINDS: w.append("v.kind=?"); p.append(f["kind"])
    if f.get("supplier"): w.append("upper(coalesce(v.supplier,''))=upper(?)"); p.append(f["supplier"])
    if f.get("family"): w.append("v.family=?"); p.append(f["family"].upper())
    for i, t in enumerate((f.get("q") or "").split()):
        w.append("(upper(v.code) LIKE ? OR upper(coalesce(v.supplier,'')) LIKE ? OR upper(coalesce(v.supplier_code,'')) LIKE ?)"); p += [f"%{t.upper()}%"] * 3
    base = q(f"SELECT v.* FROM validacoes v WHERE {' AND '.join(w)} ORDER BY v.updated_at DESC, v.id DESC", p)
    cont = {k: sum(1 for v in base if v["status"] == k) for k in STATUS}
    st = f.get("status") if f.get("status") in STATUS else ""
    rows = [v for v in base if not st or v["status"] == st]
    desc = {}
    for r in q("SELECT upper(perfect_code) c, description d FROM products"): desc[r["c"]] = r["d"]
    for r in q("SELECT upper(code) c, MAX(description) d FROM rd_projects GROUP BY upper(code)"): desc.setdefault(r["c"], r["d"])
    out = [{"id": v["id"], "kind": v["kind"], "kind_label": KINDS[v["kind"]], "code": v["code"], "description": desc.get(v["code"].upper()), "supplier": v["supplier"], "supplier_code": v["supplier_code"],
            "family": v["family"], "status": v["status"], "status_label": STATUS[v["status"]], "updated_at": v["updated_at"], "concluida_em": v["concluida_em"], "xlsx": bool(v["xlsx"]), "pdf": bool(v["pdf"]),
            **{"conta": _conta(v["dados"])}} for v in rows]
    pend = 0
    try:
        loc = _local_por_codigo("rd"); pend = sum(1 for k in pendentes_rd("rd") if k not in loc)
    except Exception: pass
    return {"total": len(out), "rows": out, "counts": {**cont, "pendentes": pend},
            "suppliers": sorted({v["supplier"] for v in q("SELECT DISTINCT supplier FROM validacoes WHERE supplier IS NOT NULL")}), "familias": [{"v": x["v"], "l": x["l"]} for x in familias()]}
