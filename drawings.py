"""Módulo Desenhos: guarda arquivos de desenho (qualquer formato), reconhece o CÓDIGO e a REVISÃO pelo nome do arquivo e vincula
automaticamente a todos os cadastros (catálogo, desenvolvimento, redesenvolvimento). Revisões antigas ficam guardadas no banco;
os cadastros mostram só a vigente (maior revisão do código)."""
import os, re, json, uuid, shutil, hashlib, datetime, zipfile
import database as db
from queries import q, q1

DIR = os.path.join(db.BASE, "data", "drawings")
TMP = os.path.join(db.BASE, "data", "uploads")
IMG = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
INLINE = IMG | {".pdf", ".svg"}          # abrem no navegador; o resto (dwg, dxf, step, zip...) baixa
_REV_WORD = re.compile(r"(?:^|[\s._\-(])(?:REV|REVISAO|REVISÃO|VERSAO|VERSÃO|VER)[\s._\-]*([0-9]{1,3}|[A-Z])(?=$|[\s._\-)])")
_REV_SHORT = re.compile(r"(?:^|[\s._\-(])[RV][\s._\-]*([0-9]{1,3})(?=$|[\s._\-)])")

# ---- regra de origem pelo NOME do arquivo: RED… = REDESENVOLVIMENTO · DES… = DESENVOLVIMENTO ----
ORIGIN_LABEL = {"RED": "REDESENVOLVIMENTO", "DES": "DESENVOLVIMENTO"}
_ORIGIN = re.compile(r"^(REDESENVOLVIMENTO|DESENVOLVIMENTO|RED|DES)(?:[\s._\-]+|(?=AMD|\d))", re.I)   # «DESENHO_…» NÃO é DES: precisa de separador, dígito ou AMD logo após o prefixo
def split_origin(name):
    """'RED_AMD0170_REV02.pdf' -> ('REDESENVOLVIMENTO', 'AMD0170_REV02.pdf'); sem prefixo -> (None, nome)."""
    base = os.path.basename(name or ""); m = _ORIGIN.match(base)
    if not m or "." not in base[m.end():] or not os.path.splitext(base[m.end():])[0].strip(" ._-"): return None, base
    w = m.group(1).upper()
    return ("REDESENVOLVIMENTO" if w.startswith("RED") else "DESENVOLVIMENTO"), base[m.end():]

MAX_ZIP_ENTRIES, MAX_ZIP_TOTAL, MAX_ZIP_FILE = 5000, 4 << 30, 1 << 30
def expand_zip(zpath, dest, start=0):
    """Extrai com segurança (sem zip-slip: só o nome do arquivo é usado, pastas são ignoradas). Devolve [{name, path, folder}] e avisos."""
    out, warn, total, i = [], [], 0, start
    try: z = zipfile.ZipFile(zpath)
    except zipfile.BadZipFile: return [], ["O arquivo ZIP está corrompido ou não é um ZIP válido."]
    with z:
        infos = [x for x in z.infolist() if not x.is_dir()]
        if len(infos) > MAX_ZIP_ENTRIES: warn.append(f"O ZIP tem {len(infos)} arquivos; foram lidos só os primeiros {MAX_ZIP_ENTRIES}."); infos = infos[:MAX_ZIP_ENTRIES]
        for x in infos:
            parts = [p for p in x.filename.replace("\\", "/").split("/") if p]
            name = parts[-1] if parts else ""
            if not name or name.startswith((".", "~$")) or "__MACOSX" in parts or name.lower() in ("thumbs.db", "desktop.ini"): continue
            if x.flag_bits & 0x1: warn.append(f"«{name}» está protegido por senha e foi ignorado."); continue
            if x.file_size > MAX_ZIP_FILE: warn.append(f"«{name}» é grande demais (>1 GB) e foi ignorado."); continue
            total += x.file_size
            if total > MAX_ZIP_TOTAL: warn.append("O conteúdo do ZIP passa de 4 GB; o restante foi ignorado."); break
            if name.lower().endswith(".zip"): warn.append(f"«{name}» é um ZIP dentro do ZIP e foi ignorado (envie-o separado)."); continue
            p = os.path.join(dest, f"{i:04d}__{_safe(name)}"); i += 1
            with z.open(x) as src, open(p, "wb") as dst: shutil.copyfileobj(src, dst, 1 << 20)
            out.append({"name": name, "path": p, "folder": parts[-2] if len(parts) > 1 else ""})
    return out, warn

def _key(code): return re.sub(r"[^A-Z0-9]", "", (code or "").upper())
def _safe(name): return re.sub(r"[^\w.\- ()]", "_", os.path.basename(name or "arquivo"), flags=re.U)[:120] or "arquivo"

def known_codes():
    """{chave normalizada: código como cadastrado} — catálogo + desenvolvimento/redesenvolvimento."""
    out = {}
    for t, col in (("products", "perfect_code"), ("rd_projects", "code")):
        for (c,) in db.conn().execute(f"SELECT DISTINCT {col} FROM {t} WHERE {col} IS NOT NULL"):
            k = _key(c)
            if len(k) >= 4: out.setdefault(k, c.strip().upper())
    return out

def parse_name(name, known):
    """-> {codes, known_codes, rev_num, rev_label}. Aceita 'AMD0170_REV02.pdf', 'D-AMD0170 R3.dwg', 'AMD0108_AMD0109 rev B.pdf'."""
    stem = re.sub(r"\s*\(\d+\)\s*$", "", os.path.splitext(os.path.basename(name))[0].strip()).upper()
    toks = re.findall(r"[A-Z0-9]+", stem); codes, used, i = [], set(), 0
    while i < len(toks):
        hit = None
        for j in (3, 2, 1):
            k = "".join(toks[i:i + j])
            if len(k) >= 5 and k in known and not re.fullmatch(r"R(EV)?\d+", k): hit = (k, j); break
        if hit: codes.append(known[hit[0]]); used.update(range(i, i + hit[1])); i += hit[1]
        else: i += 1
    unknown = False
    if not codes:   # ainda não cadastrado, mas com cara de código PERFECT
        for t in toks:
            if re.fullmatch(r"AMD\d{3,6}", t) and t not in codes: codes.append(t); unknown = True
    rest = re.sub(r"[A-Z0-9]+", lambda m: " " if m.group(0) in codes or _key(m.group(0)) in {_key(c) for c in codes} else m.group(0), stem)
    m = _REV_WORD.search(rest) or _REV_SHORT.search(rest); rn = rl = None
    if m:
        v = m.group(1)
        rn = int(v) if v.isdigit() else ord(v) - 64
        rl = v.zfill(2) if v.isdigit() else v
    return {"codes": list(dict.fromkeys(codes)), "unregistered": unknown, "rev_num": rn, "rev_label": rl}

def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

# ---------------- consultas ----------------
KINDS = {"desenho": "Desenho técnico", "projeto": "Projeto PERFECT"}
def _kind(k): return k if k in KINDS else "desenho"
def _rows_for(code, kind="desenho"):
    return q("""SELECT f.id,f.filename,f.ext,f.size,f.rev_num,f.rev_label,f.rev_auto,f.uploaded_at,f.note FROM drawing_files f JOIN drawing_links l ON l.file_id=f.id
                WHERE l.code=? AND coalesce(f.kind,'desenho')=? ORDER BY f.rev_num DESC,f.id DESC""", (_key_up(code), _kind(kind)))
def _key_up(code): return _key(code)
def _prod_index():   # {chave: (id, descrição, código)}
    return {_key(r["perfect_code"]): (r["id"], r["description"], r["perfect_code"]) for r in q("SELECT id,perfect_code,description FROM products")}
def _rd_index():     # {chave: {sugestões}}
    out = {}
    for r in q("SELECT code,suggestion FROM rd_projects"): out.setdefault(_key(r["code"]), set()).add(r["suggestion"])
    return out

def _current(files):
    """vigentes = arquivos da maior revisão, último enviado de cada formato."""
    if not files: return []
    top = max(f["rev_num"] for f in files); seen, out = set(), []
    for f in sorted((f for f in files if f["rev_num"] == top), key=lambda f: -f["id"]):
        if f["ext"] not in seen: seen.add(f["ext"]); out.append(f)
    return sorted(out, key=lambda f: (f["ext"] != ".pdf", f["ext"]))

def _label(f): return "Rev. " + (f["rev_label"] or str(f["rev_num"]).zfill(2))

def detail(code, kind="desenho"):
    kind = _kind(kind); files = _rows_for(code, kind)
    if not files: return None
    cur = _current(files); ids = {f["id"] for f in cur}; revs = {}
    for f in files: revs.setdefault(f["rev_num"], []).append(f)
    hist = [{"rev_num": n, "label": _label(fs[0]), "current": n == max(revs), "files": [dict(x, current=x["id"] in ids) for x in fs]} for n, fs in sorted(revs.items(), reverse=True)]
    k = _key_up(code); pi = _prod_index().get(k); rd = _rd_index().get(k, set())
    desc = pi[1] if pi else (q1("SELECT description FROM rd_projects WHERE description IS NOT NULL AND upper(replace(replace(replace(code,'-',''),' ',''),'/',''))=? LIMIT 1", (k,)) or {}).get("description")
    return {"kind": kind, "kind_label": KINDS[kind], "in_catalog": bool(pi), "code": (pi[2] if pi else k), "key": k, "label": _label(cur[0]), "current": cur, "history": hist, "n_revisions": len(revs),
            "product_id": pi[0] if pi else None, "description": desc, "registries": _registries(pi, rd)}

def _registries(p, rd): return (["Catálogo"] if p else []) + (["DESENVOLVIMENTO"] if "DESENVOLVIMENTO" in rd else []) + (["REDESENVOLVIMENTO"] if "REDESENVOLVIMENTO" in rd else [])

def lookup(codes, kind="desenho"):
    back = {_key(c): c for c in codes if c}
    """Resumo por código (para colunas das listas). {CÓDIGO: {label, n, file_id}}"""
    codes = list(back)[:300]
    if not codes: return {}
    out = {}
    rows = q(f"""SELECT l.code,f.id,f.ext,f.rev_num,f.rev_label FROM drawing_links l JOIN drawing_files f ON f.id=l.file_id WHERE coalesce(f.kind,'desenho')=? AND l.code IN ({",".join("?" * len(codes))})""", [_kind(kind), *codes])
    by = {}
    for r in rows: by.setdefault(r["code"], []).append(r)
    for c, fs in by.items():
        cur = _current(fs); out[back[c]] = {"label": _label(cur[0]), "n": len(cur), "file_id": cur[0]["id"], "ext": cur[0]["ext"], "revs": len({f["rev_num"] for f in fs})}
    return out

def gallery(p):
    """Cards do módulo Desenhos, agrupados por código (+ arquivos ainda sem vínculo)."""
    term, where, ext = (p.get("q") or "").strip().upper(), p.get("where") or "", (p.get("ext") or "").lower()
    kind = _kind(p.get("kind")); rows = q("SELECT l.code,f.id,f.filename,f.ext,f.size,f.rev_num,f.rev_label,f.uploaded_at,f.origin FROM drawing_links l JOIN drawing_files f ON f.id=l.file_id WHERE coalesce(f.kind,'desenho')=?", (kind,))
    by = {}
    for r in rows: by.setdefault(r["code"], []).append(r)
    prod = _prod_index(); rdc = _rd_index(); rdd = {}
    for r in q("SELECT code,description FROM rd_projects WHERE description IS NOT NULL"): rdd.setdefault(_key(r["code"]), r["description"])
    page, size = max(1, int(p.get("page") or 1)), (10**9 if p.get("all") else 48)
    if where == "falta":    # o que ainda não tem arquivo: mesmo conjunto do número «sem desenho / sem projeto» de stats()
        cards = []
        for k in sorted(_missing(kind, set(by), prod)):
            desc = prod[k][1] if k in prod else rdd.get(k)
            if term and term not in k and term not in (desc or "").upper(): continue
            cards.append({"code": prod[k][2] if k in prod else k, "key": k, "missing": True, "description": desc, "product_id": prod[k][0] if k in prod else None, "registries": _registries(prod.get(k), rdc.get(k, set()))})
        return {"total": len(cards), "page": page, "size": size, "rows": cards[(page - 1) * size: page * size]}
    cards = []
    for code, fs in by.items():
        cur = _current(fs); reg = _registries(prod.get(code), rdc.get(code, set()))
        if where == "cat" and "Catálogo" not in reg: continue
        if where == "des" and "DESENVOLVIMENTO" not in reg: continue
        if where == "rd" and "REDESENVOLVIMENTO" not in reg: continue
        if where == "sem": continue
        if ext and ext not in {f["ext"] for f in fs}: continue
        if p.get("origin") in ORIGIN_LABEL.values() and p["origin"] not in {f["origin"] for f in fs}: continue
        desc = prod[code][1] if code in prod else rdd.get(code)
        if term and term not in code and term not in (desc or "").upper() and not any(term in f["filename"].upper() for f in fs): continue
        th = next((f for f in cur if f["ext"] in IMG | {".pdf"}), cur[0])
        cards.append({"code": prod[code][2] if code in prod else code, "key": code, "label": _label(cur[0]), "rev_num": cur[0]["rev_num"], "description": desc, "registries": reg, "n_revisions": len({f["rev_num"] for f in fs}), "n_files": len(fs),
                      "origin": next((f["origin"] for f in cur if f["origin"]), None) or next((f["origin"] for f in fs if f["origin"]), None), "exts": [f["ext"].lstrip(".").upper() for f in cur], "thumb_id": th["id"], "thumb_ext": th["ext"], "updated": max(f["uploaded_at"] for f in fs), "registered": code in prod or code in rdc})
    if where in ("", "sem"):
        for f in q("SELECT id,filename,ext,size,uploaded_at,origin FROM drawing_files WHERE coalesce(kind,'desenho')=? AND id NOT IN (SELECT file_id FROM drawing_links) ORDER BY id DESC", (kind,)):
            if term and term not in f["filename"].upper(): continue
            if ext and ext != f["ext"]: continue
            if p.get("origin") in ORIGIN_LABEL.values() and f["origin"] != p["origin"]: continue
            cards.append({"origin": f["origin"], "code": None, "file_id": f["id"], "filename": f["filename"], "label": None, "description": None, "registries": [], "n_revisions": 0, "n_files": 1, "exts": [(f["ext"] or "").lstrip(".").upper()],
                          "thumb_id": f["id"], "thumb_ext": f["ext"], "updated": f["uploaded_at"], "registered": False})
    srt = p.get("sort") or "recent"
    if srt == "code": cards.sort(key=lambda c: (c["code"] is None, c["code"] or c.get("filename") or ""))
    elif srt == "rev": cards.sort(key=lambda c: (c["code"] is None, -c["n_revisions"], c["code"] or ""))
    else: cards.sort(key=lambda c: (c["code"] is None, c["updated"] or ""), reverse=False); cards.sort(key=lambda c: (c["code"] is None, c["updated"] or ""), reverse=True)
    return {"total": len(cards), "page": page, "size": size, "rows": cards[(page - 1) * size: page * size]}

def _missing(kind, have, prod=None):
    """Chaves sem arquivo: desenho = produtos do catálogo sem desenho · projeto = itens DES/R-D fora do catálogo sem projeto."""
    if kind == "desenho": return set(prod if prod is not None else _prod_index()) - have
    return {_key(r["code"]) for r in q("SELECT DISTINCT code FROM rd_projects WHERE product_id IS NULL")} - have

def stats(kind="desenho"):
    kind = _kind(kind); K = "coalesce(f.kind,'desenho')=?"
    base = {"codes": q1(f"SELECT COUNT(DISTINCT l.code) n FROM drawing_links l JOIN drawing_files f ON f.id=l.file_id WHERE {K}", (kind,))["n"], "files": q1("SELECT COUNT(*) n FROM drawing_files f WHERE " + K, (kind,))["n"],
            "orphans": q1(f"SELECT COUNT(*) n FROM drawing_files f WHERE {K} AND f.id NOT IN (SELECT file_id FROM drawing_links)", (kind,))["n"],
            "old": q1(f"""SELECT COUNT(*) n FROM drawing_files f JOIN drawing_links l ON l.file_id=f.id WHERE {K} AND f.rev_num < (SELECT MAX(f2.rev_num) FROM drawing_files f2 JOIN drawing_links l2 ON l2.file_id=f2.id WHERE l2.code=l.code AND coalesce(f2.kind,'desenho')=?)""", (kind, kind))["n"]}
    have = {r["code"] for r in q(f"SELECT DISTINCT l.code FROM drawing_links l JOIN drawing_files f ON f.id=l.file_id WHERE {K}", (kind,))}
    prod, rdc = _prod_index(), _rd_index(); base["missing"] = len(_missing(kind, have, prod))   # projeto PERFECT: o que importa são os itens DES/R-D fora do catálogo
    reg = [_registries(prod.get(c), rdc.get(c, set())) for c in have]      # atalhos por cadastro (mesma regra do filtro where de gallery)
    base.update(cat=sum("Catálogo" in r for r in reg), des=sum("DESENVOLVIMENTO" in r for r in reg), rd=sum("REDESENVOLVIMENTO" in r for r in reg))
    return base

# ---------------- envio: verificação e aplicação ----------------
def stash(uploads, kind="desenho"):
    """Recebe arquivos soltos e/ou .zip (o ZIP é aberto e cada desenho dentro dele entra como se tivesse sido enviado separado)."""
    tok = uuid.uuid4().hex; d = os.path.join(TMP, "drw_" + tok); os.makedirs(d, exist_ok=True); man, warns, zips = [], [], []
    for i, f in enumerate(uploads):
        name = os.path.basename((f.filename or "").replace("\\", "/")).strip()
        if not name: continue
        p = os.path.join(d, f"{i:04d}__{_safe(name)}"); f.save(p)
        if name.lower().endswith(".zip"):
            ents, w = expand_zip(p, d, start=10000 * (i + 1)); os.remove(p); zips.append({"zip": name, "files": len(ents)}); warns += [f"{name}: {x}" for x in w]
            for e in ents: e["source"] = name; man.append(e)
        else: man.append({"name": name, "path": p, "source": None, "folder": ""})
    info = {"kind": _kind(kind), "files": man, "zips": zips, "warnings": warns}
    json.dump(info, open(os.path.join(d, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return tok, info
def stashed(tok):
    if not re.fullmatch(r"[0-9a-f]{32}", tok or ""): return None
    mf = os.path.join(TMP, "drw_" + tok, "manifest.json")
    return json.load(open(mf, encoding="utf-8")) if os.path.exists(mf) else None
def discard(tok):
    if re.fullmatch(r"[0-9a-f]{32}", tok or ""): shutil.rmtree(os.path.join(TMP, "drw_" + tok), ignore_errors=True)

def _plan_one(name, path, known, ov=None, kind="desenho", folder="", source=None):
    ov = ov or {}; origin, rest = split_origin(name)
    if not origin and folder: origin, _ = split_origin(folder + "_x")      # pasta «RED_…» / «DES_…» dentro do ZIP também vale
    if ov.get("origin") in ORIGIN_LABEL.values(): origin = ov["origin"]
    info = parse_name(rest, known); ext = os.path.splitext(name)[1].lower(); sha = _sha(path)
    if ov.get("codes"): info["codes"] = [c for c in re.split(r"[,;\s]+", ov["codes"]) if c]; info["unregistered"] = False
    if ov.get("rev"):
        v = str(ov["rev"]).strip().upper(); 
        if v: info["rev_num"] = int(v) if v.isdigit() else ord(v[0]) - 64; info["rev_label"] = v.zfill(2) if v.isdigit() else v[0]
    info["codes"] = list(dict.fromkeys(_key(c) for c in info["codes"] if _key(c))); codes = info["codes"]; existing = []
    for c in codes: existing += _rows_for(c, kind)
    dup = q1("SELECT f.id FROM drawing_files f JOIN drawing_links l ON l.file_id=f.id WHERE f.sha256=? AND coalesce(f.kind,'desenho')=? AND l.code IN (%s)" % ",".join("?" * len(codes)), [sha, kind, *codes]) if codes else q1("SELECT id FROM drawing_files WHERE sha256=? AND coalesce(kind,'desenho')=? AND id NOT IN (SELECT file_id FROM drawing_links)", (sha, kind))
    top = max([f["rev_num"] for f in existing], default=None); auto = info["rev_num"] is None
    rn = info["rev_num"] if not auto else ((top + 1) if top is not None else 0)
    rl = info["rev_label"] if not auto else str(rn).zfill(2)
    if not origin and codes:     # sem prefixo: se o código só existe em um dos módulos, assume esse
        kinds_of = _rd_index().get(codes[0], set()) & set(ORIGIN_LABEL.values())
        if len(kinds_of) == 1: origin = next(iter(kinds_of)); origin_guess = True
    if dup: action, note = "duplicado", "Arquivo idêntico já cadastrado: será ignorado."
    elif not codes: action, note = "sem_vinculo", "Código não reconhecido pelo nome. Informe o código ou envie assim e vincule depois."
    elif top is None: action, note = "nova", "Primeiro desenho deste código."
    elif rn > top: action, note = "nova_revisao", f"Nova revisão: a anterior (Rev. {str(top).zfill(2)}) continua guardada no histórico."
    elif rn == top and any(f["rev_num"] == rn and f["ext"] == ext for f in existing): action, note = "atualiza_revisao", "Mesma revisão e formato: este arquivo passa a ser o vigente; o anterior fica guardado."
    elif rn == top: action, note = "nova", "Outro formato da revisão vigente."
    else: action, note = "revisao_antiga", f"Revisão anterior à vigente (Rev. {str(top).zfill(2)}): guardada no histórico, sem substituir."
    if auto and not dup and codes: note += " Revisão não informada no nome: atribuída automaticamente."
    if not origin and not dup: note += " Sem prefixo RED/DES no nome: origem não identificada."
    return {"origin": origin, "origin_auto": bool(origin) and split_origin(name)[0] is None and not ov.get("origin"), "source": source, "name": name, "ext": ext, "size": os.path.getsize(path), "sha": sha, "codes": codes, "unregistered": info["unregistered"], "rev_num": rn, "rev_label": rl, "rev_auto": auto,
            "action": action, "note": note, "path": path}

def plan(man, overrides=None):
    kind = _kind(man.get("kind")); known = known_codes(); overrides = overrides or {}; out = []
    for n, m in enumerate(man["files"]):
        r = _plan_one(m["name"], m["path"], known, overrides.get(str(n)) or overrides.get(m["name"]), kind, m.get("folder", ""), m.get("source")); out.append(r)
    # arquivos idênticos no mesmo envio: só o primeiro entra
    seen = set()
    for r in out:
        k = (r["sha"], tuple(r["codes"]))
        if k in seen and r["action"] != "duplicado": r["action"], r["note"] = "duplicado", "Repetido neste mesmo envio: será ignorado."
        seen.add(k)
    return out

def apply(man, overrides=None):
    items = plan(man, overrides); kind = _kind(man.get("kind")); os.makedirs(DIR, exist_ok=True); c = db.conn(); n = dict(novos=0, revisoes=0, ignorados=0, sem_vinculo=0, redesenvolvimento=0, desenvolvimento=0, sem_origem=0)
    try:
        src = c.execute("SELECT id FROM sources WHERE name='Desenhos (upload)'").fetchone()
        sid = src[0] if src else c.execute("INSERT INTO sources(name,category,priority) VALUES('Desenhos (upload)','Desenhos',5)").lastrowid
        bid = c.execute("INSERT INTO import_batches(source_id,filename,sheet,category,rows_read,rows_new,rows_updated,rows_conflict,rows_error,status) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (sid, f"{len(items)} arquivo(s) — {KINDS[kind]}", None, "Desenhos", len(items), 0, 0, 0, 0, "ok")).lastrowid
        for r in sorted(items, key=lambda r: (r["rev_num"], r["name"])):   # revisões antigas entram antes das novas
            if r["action"] == "duplicado": n["ignorados"] += 1; continue
            fid = c.execute("INSERT INTO drawing_files(filename,stored_name,ext,size,sha256,rev_num,rev_label,rev_auto,batch_id,kind,origin,source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                            (r["name"], "", r["ext"], r["size"], r["sha"], r["rev_num"], r["rev_label"], int(r["rev_auto"]), bid, kind, r.get("origin"), r.get("source"))).lastrowid
            stored = f"{fid}_{_safe(r['name'])}"; shutil.copy2(r["path"], os.path.join(DIR, stored))
            c.execute("UPDATE drawing_files SET stored_name=? WHERE id=?", (stored, fid))
            for code in r["codes"]: c.execute("INSERT OR IGNORE INTO drawing_links(file_id,code) VALUES(?,?)", (fid, code))
            n["redesenvolvimento" if r.get("origin") == "REDESENVOLVIMENTO" else "desenvolvimento" if r.get("origin") == "DESENVOLVIMENTO" else "sem_origem"] += 1
            if not r["codes"]: n["sem_vinculo"] += 1
            elif r["action"] in ("nova_revisao", "atualiza_revisao", "revisao_antiga"): n["revisoes"] += 1
            else: n["novos"] += 1
        c.execute("UPDATE import_batches SET rows_new=?,rows_updated=?,rows_error=? WHERE id=?", (n["novos"], n["revisoes"], n["sem_vinculo"], bid))
        c.commit()
    except Exception:
        c.rollback(); raise
    finally: c.close()
    return {"summary": n, "items": [{k: v for k, v in r.items() if k != "path"} for r in items]}

def relink():
    """Tenta vincular arquivos sem código (ex.: o código foi cadastrado depois do envio)."""
    orph = q("SELECT id,filename FROM drawing_files WHERE id NOT IN (SELECT file_id FROM drawing_links)")
    if not orph: return 0
    known = known_codes(); c = db.conn(); n = 0
    for f in orph:
        info = parse_name(f["filename"], known)
        if info["codes"] and not info["unregistered"]:
            for code in info["codes"]: c.execute("INSERT OR IGNORE INTO drawing_links(file_id,code) VALUES(?,?)", (f["id"], code))
            n += 1
    c.commit(); c.close(); return n

def assign(file_id, codes, rev=None):
    codes = [_key(x) for x in re.split(r"[,;\s]+", codes or "") if _key(x)]
    if not codes: raise ValueError("Informe ao menos um código.")
    c = db.conn(); c.execute("DELETE FROM drawing_links WHERE file_id=?", (file_id,))
    for code in codes: c.execute("INSERT OR IGNORE INTO drawing_links(file_id,code) VALUES(?,?)", (file_id, code))
    if rev not in (None, ""):
        v = str(rev).strip().upper(); c.execute("UPDATE drawing_files SET rev_num=?,rev_label=?,rev_auto=0 WHERE id=?", (int(v) if v.isdigit() else ord(v[0]) - 64, v.zfill(2) if v.isdigit() else v[0], file_id))
    c.commit(); c.close()

def delete_file(file_id):
    f = q1("SELECT stored_name FROM drawing_files WHERE id=?", (file_id,))
    if not f: return False
    c = db.conn(); c.execute("DELETE FROM drawing_links WHERE file_id=?", (file_id,)); c.execute("DELETE FROM drawing_files WHERE id=?", (file_id,)); c.commit(); c.close()
    import glob
    for p in [os.path.join(DIR, f["stored_name"])] + glob.glob(os.path.join(DIR, "_thumbs", f"{file_id}_*.jpg")):
        try: os.remove(p)
        except OSError: pass
    return True

def file_path(file_id):
    f = q1("SELECT filename,stored_name,ext FROM drawing_files WHERE id=?", (file_id,))
    p = os.path.join(DIR, f["stored_name"]) if f else None
    return (f, p) if p and os.path.isfile(p) else (None, None)

def thumb(file_id, size=560):
    """Imagem de pré-visualização em cache (JPEG). Imagens: Pillow. PDF: PyMuPDF ou pypdfium2 (o que estiver instalado). None = sem prévia (o front mostra o ícone do formato)."""
    f, p = file_path(file_id)
    if not f: return None
    t = os.path.join(DIR, "_thumbs", f"{file_id}_{size}.jpg")
    if os.path.isfile(t): return t
    try:
        from PIL import Image
        os.makedirs(os.path.dirname(t), exist_ok=True)
        if f["ext"] in IMG: im = Image.open(p)
        elif f["ext"] == ".pdf":
            im = None
            try:
                import fitz
                pg = fitz.open(p)[0]; z = size / max(pg.rect.width, pg.rect.height); pix = pg.get_pixmap(matrix=fitz.Matrix(z, z)); im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            except ImportError:
                import pypdfium2 as pdfium
                pg = pdfium.PdfDocument(p)[0]; w, h = pg.get_size(); im = pg.render(scale=size / max(w, h)).to_pil()
        else: return None
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA"); bg = Image.new("RGB", im.size, "white"); bg.paste(im, mask=im.split()[-1]); im = bg
        im = im.convert("RGB"); im.thumbnail((size, size)); im.save(t, "JPEG", quality=84); return t
    except Exception: return None
