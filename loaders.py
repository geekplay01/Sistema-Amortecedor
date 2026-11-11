"""Etapa 2 (parte 2): gravação da importação. Um único transação: simulação = rollback; confirmação = commit.
Política padrão: campos vazios são preenchidos; valores divergentes NÃO sobrescrevem (viram pendência 'conflito').
Tabelas sem chave natural: ao reimportar a mesma fonte, as linhas anteriores DESSA fonte são substituídas."""
import os, json, hashlib, re
import database as db
from importer import read_table, normalize_code

KINDS = [("catalogo", {"perfect_code", "description", "related_codes"}),   # CatalogoAMD.xlsx (formato completo: Números Referência, Veículos, Produtos Relacionados)
         ("marca", {"brand_code", "perfect_code"}), ("amostras", {"sample_code", "sc_number"}), ("caixas", {"box_code", "box_dims_mm"}), ("estrutura", {"parent_code", "component_code"}),
         ("lados", {"rh_code", "lh_code"}), ("fornecedor_erp", {"erp_code", "supplier_code"}),
         ("desenvolvimento", {"rd_kind"}), ("certificados", {"perfect_code", "inmetro_number"}),
         ("de_para", {"perfect_code", "zs_code"}), ("oem", {"perfect_code", "oem_code"}), ("referencia_cruzada", {"perfect_code", "cross_refs"}),
         ("catalogo", {"perfect_code", "description"})]
LABEL = {"marca": "Brands (código da marca × PERFECT)", "amostras": "Compra de amostras", "caixas": "Tipos de caixa", "estrutura": "Estrutura de produto", "lados": "Pares direito/esquerdo",
         "fornecedor_erp": "Cadastro de fornecedor (ERP)", "desenvolvimento": "Desenvolvimento / aplicações",
         "certificados": "Certificados Inmetro", "de_para": "De-para fornecedor × PERFECT", "oem": "Códigos OEM e aplicações", "referencia_cruzada": "Referência cruzada (concorrentes)", "catalogo": "Catálogo de produtos"}

def _s(v):
    v = None if v is None else str(v).strip()
    return v or None
def _fmt(v):
    """Valor de célula para texto legível: datas sem hora, números inteiros sem .0."""
    if v is None or v != v: return ""
    if hasattr(v, "strftime"): return v.strftime("%Y-%m-%d")
    if isinstance(v, float) and v.is_integer(): return str(int(v))
    t = str(v).strip()
    return t[:10] if re.fullmatch(r"\d{4}-\d{2}-\d{2} 00:00:00", t) else t
def _dt(v):
    t = _fmt(v); return t[:10] if re.match(r"\d{4}-\d{2}-\d{2}", t) else (t or None)
def _ap(v):
    """Texto da aplicação limpo: sem apóstrofo inicial, espaços repetidos ou o traço de 'sem aplicação'."""
    t = _s(v)
    if t is None: return None
    t = re.sub(r"\s+", " ", t.lstrip("'")).strip()
    return None if t in ("-", "") else t
def _kind_rd(v):
    t = (str(v or "")).strip().upper()
    import kinds; return kinds.normalize_kind(t) or (t or None)
def _f(v):
    try: return float(str(v).strip().replace(",", "."))
    except (TypeError, ValueError): return None
def _i(v):
    f = _f(v); return int(f) if f is not None else None

class Ctx:
    def __init__(s, c, src, name, policy="keep", sync=False):
        s.c, s.src, s.name, s.msgs, s.policy, s.sync = c, src, name, [], policy, sync
        s.n = dict(new=0, updated=0, replaced=0, conflicts=0, duplicates=0, unmatched=0, errors=0, pendencies=0, relinked=0, present=0)
        s.pid = {r[0]: r[1] for r in c.execute("SELECT perfect_code,id FROM products")}
        # modo sync: o que já está no banco é conhecido e nunca apagado; só entra o que falta
        s.known = {(r[0], r[1], r[2]) for r in c.execute("SELECT product_id,normalized_code,code_type FROM codes")} if sync else set()
    def of(s, raw):
        n, _ = normalize_code(raw); return s.pid.get(n) if n else None
    def err(s, m):
        s.n["errors"] += 1
        if len(s.msgs) < 12: s.msgs.append(m)
    def unlink(s, kind, code, row, reason):
        s.n["unmatched"] += 1
        s.c.execute("INSERT INTO unlinked_rows(kind,source_id,code,payload,reason) VALUES(?,?,?,?,?)", (kind, s.src, code, json.dumps(row, ensure_ascii=False), reason))
    def reset_unlinked(s, kind):   # linhas sem vínculo são recalculadas a cada leitura (nunca perdem dados do banco)
        s.c.execute("DELETE FROM unlinked_rows WHERE source_id=? AND kind=?", (s.src, kind))
    def replace(s, table):
        if s.sync: return
        s.n["replaced"] += s.c.execute(f"DELETE FROM {table} WHERE source_id=?", (s.src,)).rowcount
    def add_code(s, pid, raw, ctype, brand=None, seen=None):
        norm, _ = normalize_code(raw)
        if not norm: return False
        if s.sync and (pid, norm, ctype) in s.known: s.n["present"] += 1; return False
        if seen is not None and (pid, norm, ctype) in seen: return False
        if seen is not None: seen.add((pid, norm, ctype))
        s.known.add((pid, norm, ctype))
        s.c.execute("INSERT INTO codes(product_id,code,normalized_code,code_type,brand,source_id) VALUES(?,?,?,?,?,?)", (pid, raw, norm, ctype, brand, s.src)); return True

def _merge(x, pid, vals):
    cur = x.c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone(); sets = {}
    for k, v in vals.items():
        if v is None: continue
        old = cur[k]
        if old is None: sets[k] = v
        elif str(old) != str(v) and x.policy == "overwrite": sets[k] = v   # regra escolhida: a planilha prevalece
        elif str(old) != str(v):
            x.n["conflicts"] += 1
            x.c.execute("DELETE FROM pendencies WHERE product_id=? AND kind='conflito' AND field=? AND status='aberta'", (pid, k))
            x.c.execute("INSERT INTO pendencies(product_id,kind,field,description) VALUES(?,?,?,?)",
                        (pid, "conflito", k, f"Valor atual «{old}» × importado «{v}» (fonte {x.name}). Nada foi sobrescrito."))
    if sets:
        x.c.execute(f"UPDATE products SET {','.join(k + '=?' for k in sets)},updated_at=CURRENT_TIMESTAMP WHERE id=?", [*sets.values(), pid]); x.n["updated"] += 1

SYSTEM_LABEL = {"gas": "FORCE GAS", "oleo": "FORCE OIL"}       # como a PERFECT chama o sistema (telas, filtros e exports)
def _system(u):
    """Texto já em maiúsculas → 'gas' | 'oleo' | None («FORCE GAS», «GÁS», «FORCE OIL», «ÓLEO»; «Código Produto» e vazio → None)."""
    return "gas" if re.search(r"\bG[ÁA]S\b", u) else "oleo" if re.search(r"\bOIL\b|[ÓO]LEO", u) else None

def _axle_side(desc):
    d = (desc or "").upper(); ax = "dianteiro" if "DIANT" in d else "traseiro" if "TRAS" in d else None
    sd = "ambos" if re.search(r"LD\s*/\s*LE|LE\s*/\s*LD", d) else "direito" if re.search(r"\bLD\b", d) else "esquerdo" if re.search(r"\bLE\b", d) else None
    return ax, sd

def _relink(x):
    """Linhas guardadas sem vínculo (de-para, lados) são ligadas automaticamente quando o produto passa a existir no catálogo."""
    for u in x.c.execute("SELECT * FROM unlinked_rows WHERE kind IN ('de_para','lados')").fetchall():
        r = json.loads(u["payload"]); ok = False
        if u["kind"] == "de_para" and "suspeito" not in (u["reason"] or ""):
            pid, z = x.of(r.get("perfect_code")), _s(r.get("zs_code"))
            if pid and z:
                nz, _ = normalize_code(z)
                x.c.execute("INSERT INTO codes(product_id,code,normalized_code,code_type,brand,source_id) VALUES(?,?,?,?,?,?)", (pid, z, nz, "fornecedor", "ZS", u["source_id"])); ok = True
        elif u["kind"] == "lados":
            a, b = x.of(r.get("rh_code")), x.of(r.get("lh_code"))
            if a and b: x.c.execute("INSERT OR IGNORE INTO side_pairs(right_product_id,left_product_id,source_id) VALUES(?,?,?)", (a, b, u["source_id"])); ok = True
        if ok: x.c.execute("DELETE FROM unlinked_rows WHERE id=?", (u["id"],)); x.n["relinked"] += 1

def L_catalogo(x, rows):
    """A planilha «CatalogoAMD» é a FONTE DE VERDADE do catálogo: o que está nela PREVALECE sobre o banco (política «overwrite»), a posição segue a ordem das linhas e
    produto que NÃO está mais na planilha sai do catálogo (catalog_position = NULL) — nada é apagado. O servidor SQL nunca grava nos dados de catálogo."""
    x.policy = "overwrite"; seen = set(); invalid = []
    has_launch = bool(rows) and "launch_flag" in rows[0]                 # coluna presente e vazia = não é lançamento
    for pos, r in enumerate(rows, 1):  # posição no catálogo = ordem das linhas da planilha
        code, _ = normalize_code(r.get("perfect_code"))
        if not code: x.err("linha sem código PERFECT"); continue
        v = {"description": _s(r.get("description")), "description_es": _s(r.get("description_es")), "description_en": _s(r.get("description_en")),
             "ean": _s(r.get("ean")), "ncm": _s(r.get("ncm")), "weight_kg": _f(r.get("weight_kg")), "catalog_group": _s(r.get("group_name")),
             "catalog_subgroup": _s(r.get("subgroup_name")), "is_launch": (_s(r.get("launch_flag")) or "").upper()[:1] or ("N" if has_launch else None), "catalog_highlight": (_s(r.get("highlight_flag")) or "").upper()[:1] or None,
             "catalog_photo": _s(r.get("photo_file")), "family": (_s(r.get("family")) or "").upper() or None}      # família em maiúsculas, como nos certificados Inmetro
        obs = _s(r.get("observation")) or ""
        m = re.search(r"Sistema\.?:\s*(.+)", obs, re.I)
        if m:
            u = m.group(1).upper(); v["features"] = "Sistema: " + m.group(1).strip()
            v["system_type"] = _system(u)
        if "system_col" in r:                                             # coluna «Sistema» (FORCE GAS / FORCE OIL) prevalece; inválida → fica a da Observação + pendência
            raw = _s(r.get("system_col")); st = _system((raw or "").upper())
            if st: v["system_type"] = st
            else: invalid.append((code, raw, v.get("system_type")))
        m = re.search(r"Medida emb\.?:\s*(.+)", obs, re.I)
        if m: v["package_note"] = m.group(1).strip()
        pid = x.pid.get(code)
        if pid is None:
            cols = [k for k, val in v.items() if val is not None]
            pid = x.c.execute(f"INSERT INTO products(perfect_code{''.join(',' + k for k in cols)}) VALUES(?{',?' * len(cols)})", [code] + [v[k] for k in cols]).lastrowid
            x.pid[code] = pid; x.n["new"] += 1
        else: _merge(x, pid, v); x.n["present"] += 1
        x.c.execute("UPDATE products SET catalog_position=? WHERE id=?", (pos, pid)); seen.add(pid)
        mm = re.search(r"MIN:\s*(\d+).*?M[ÁA]X:\s*(\d+)", _s(r.get("measure_min_max")) or "", re.I)
        if mm: x.c.execute("INSERT INTO dimensions(product_id,lmin_mm,lmax_mm,source_id) VALUES(?,?,?,?) ON CONFLICT(product_id) DO UPDATE SET lmin_mm=excluded.lmin_mm,lmax_mm=excluded.lmax_mm,source_id=excluded.source_id",
                           (pid, float(mm.group(1)), float(mm.group(2)), x.src))
        rod = _f(r.get("rod_diameter"))
        if rod is not None: x.c.execute("INSERT INTO dimensions(product_id,rod_diameter_mm,source_id) VALUES(?,?,?) ON CONFLICT(product_id) DO UPDATE SET rod_diameter_mm=excluded.rod_diameter_mm", (pid, rod, x.src))
    if rows and "system_col" in rows[0]:
        x.c.execute("DELETE FROM pendencies WHERE kind='campo_invalido' AND field='sistema' AND status='aberta'")
        for code, raw, st in invalid:
            x.c.execute("INSERT INTO pendencies(product_id,kind,field,description) VALUES(?,?,?,?)", (x.pid[code], "campo_invalido", "sistema",
                        f"Sistema inválido na planilha («{raw or 'vazio'}»). " + (f"Usado o da Observação: {SYSTEM_LABEL[st]}." if st else "A Observação também não informa: fica o sistema que já estava no cadastro (se houver).")))
        x.n["sistema_invalido"] = len(invalid)
        if invalid: x.msgs.append(f"{len(invalid)} produto(s) com Sistema inválido na planilha (ex.: {', '.join(c for c, _, _ in invalid[:8])}): ver Pendências.")
    gone =[r[0] for r in x.c.execute("SELECT perfect_code FROM products WHERE catalog_position IS NOT NULL AND id NOT IN (%s)" % (",".join(map(str, seen)) or "0"))]
    if gone and seen:
        x.c.execute("UPDATE products SET catalog_position=NULL WHERE catalog_position IS NOT NULL AND id NOT IN (%s)" % ",".join(map(str, seen))); x.n["fora_do_catalogo"] = len(gone)
        x.msgs.append(f"{len(gone)} produto(s) saíram do catálogo (não estão mais na planilha): " + ", ".join(gone[:15]) + ("…" if len(gone) > 15 else ""))
    if rows and any(k in rows[0] for k in ("vehicles", "cross_refs", "related_codes")):     # formato completo (CatalogoAMD.xlsx): veículos, referências e produtos relacionados
        x.c.execute("DELETE FROM catalog_vehicles WHERE source_id=?", (x.src,))              # o catálogo é a fonte de verdade das próprias aplicações
        _refs_vehicles(x, rows); _related(x, rows)
    _relink(x)
    x.c.execute("DELETE FROM pendencies WHERE kind='campo_ausente' AND status='aberta'")
    for fld, cond, fr in [("Lmin/Lmax", "d.lmin_mm IS NULL OR d.lmax_mm IS NULL", "LEFT JOIN dimensions d ON d.product_id=p.id"),
                          ("peso", "p.weight_kg IS NULL", ""), ("EAN", "p.ean IS NULL", "")]:
        x.n["pendencies"] += x.c.execute(f"INSERT INTO pendencies(product_id,kind,field,description) SELECT p.id,'campo_ausente','{fld}','Campo ausente: {fld}' FROM products p {fr} WHERE {cond}").rowcount

def _related(x, rows):
    """«Produtos Relacionados» do CatalogoAMD (ex.: AMD0108 → AMD0109, AMD0129): par do outro lado e amortecedor do outro eixo para a mesma aplicação.
    Substitui por completo a lista de cada produto da planilha (fonte de verdade); código relacionado fora do catálogo fica guardado sem vínculo."""
    x.c.execute("CREATE TABLE IF NOT EXISTS product_relations(product_id INTEGER NOT NULL, related_code TEXT NOT NULL, related_product_id INTEGER, seq INTEGER, source_id INTEGER, PRIMARY KEY(product_id, related_code))")
    n = 0
    for r in rows:
        pid = x.of(r.get("perfect_code"))
        if not pid: continue
        x.c.execute("DELETE FROM product_relations WHERE product_id=?", (pid,))
        for i, rc in enumerate(c for c in re.split(r"[,;\n/]+", str(r.get("related_codes") or "")) if c.strip()):
            code, _ = normalize_code(rc.strip())
            if code and x.pid.get(code) != pid:
                x.c.execute("INSERT OR IGNORE INTO product_relations(product_id,related_code,related_product_id,seq,source_id) VALUES(?,?,?,?,?)", (pid, code, x.pid.get(code), i, x.src)); n += 1
    x.n["relacionados"] = n

RD_KEY = ("code", "suggestion", "make", "vehicle", "application_text", "year_from", "year_to")
RD_UPD = ("status", "drawing_substatus", "validation_substatus", "supplier", "sample_bought", "sample_sent", "description", "product_id", "project_substatus", "brand", "extra")

def L_desenvolvimento(x, rows):
    x.replace("rd_projects"); x.replace("applications"); seen = set()
    have_apps = {tuple(r) for r in x.c.execute("SELECT product_id,make,model,application_text,year_from,year_to,axle,side FROM applications")} if x.sync else set()
    existing = {}
    if x.sync:   # linhas já cadastradas, agrupadas pela chave natural (cada ocorrência da chave casa com uma linha do banco)
        for r in x.c.execute("SELECT id,%s,%s FROM rd_projects" % (",".join(RD_KEY), ",".join(RD_UPD))).fetchall():
            existing.setdefault(tuple(r[k] for k in RD_KEY), []).append(r)
    used = {}
    for r in rows:
        code = _s(r.get("perfect_code") or r.get("parent_code"))
        if not code: x.err("linha sem código"); continue
        pid = x.of(code); yf, yt = _i(r.get("year_from")), _i(r.get("year_to"))
        xt = r.get("_raw") or {}; vals = dict(code=code, suggestion=_kind_rd(r.get("rd_kind")), make=_s(r.get("make")), vehicle=_s(r.get("vehicle")), application_text=_ap(r.get("application")), year_from=yf, year_to=yt,
                    status=_s(r.get("status")), drawing_substatus=_s(r.get("sub_status_drawing")), validation_substatus=_s(r.get("sub_status_validation")), supplier=_s(r.get("supplier")),
                    sample_bought=_dt(r.get("sample_bought")), sample_sent=_dt(r.get("sample_sent")), description=_s(r.get("description")), product_id=pid,
                    project_substatus=_s(r.get("project_substatus")), brand=_s(r.get("brand")), extra=json.dumps(xt, ensure_ascii=False) if xt else None)
        key = tuple(vals[k] for k in RD_KEY); hit = None
        if x.sync:
            n = used.get(key, 0); used[key] = n + 1; lst = existing.get(key, [])
            hit = lst[n] if n < len(lst) else None
        if hit is not None:   # já existe: só atualiza o que mudou na planilha (status, fornecedor, amostras...)
            ch = {k: vals[k] for k in RD_UPD if vals[k] is not None and str(hit[k]) != str(vals[k])}
            if ch:
                x.c.execute("UPDATE rd_projects SET " + ",".join(k + "=?" for k in ch) + " WHERE id=?", [*ch.values(), hit["id"]]); x.n["updated"] += 1
            else: x.n["present"] += 1
        else:
            x.c.execute("INSERT INTO rd_projects(code,product_id,suggestion,status,drawing_substatus,validation_substatus,supplier,sample_bought,sample_sent,make,vehicle,application_text,year_from,year_to,description,source_id,project_substatus,brand,extra) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (code, pid, vals["suggestion"], vals["status"], vals["drawing_substatus"], vals["validation_substatus"], vals["supplier"], vals["sample_bought"], vals["sample_sent"], vals["make"], vals["vehicle"],
                         vals["application_text"], yf, yt, vals["description"], x.src, vals["project_substatus"], vals["brand"], vals["extra"]))
            x.n["new"] += 1
        if not pid: x.n["unmatched"] += 1; continue
        ax, sd = _axle_side(_s(r.get("description")))
        key = (pid, _s(r.get("make")), _s(r.get("vehicle")), _ap(r.get("application")), yf, yt, ax, sd)
        if key in seen or tuple(key) in have_apps: x.n["duplicates"] += (key in seen); continue
        seen.add(key)
        x.c.execute("INSERT INTO applications(product_id,make,model,application_text,year_from,year_to,axle,side,source_id) VALUES(?,?,?,?,?,?,?,?,?)", (pid, key[1], key[2], key[3], yf, yt, ax, sd, x.src))

def L_oem(x, rows):
    x.replace("codes"); x.replace("applications"); x.replace("unlinked_rows")
    if x.sync: x.reset_unlinked("oem")
    seen = set(); motor = "motorcraft" in (x.name or "").lower()
    if motor and not x.sync: x.c.execute("DELETE FROM brand_items WHERE source_id=?", (x.src,))
    have_b = {(b[0], b[1]) for b in x.c.execute("SELECT brand,norm_code FROM brand_items")} if motor else set()
    have = {(r[0], r[1], r[2], r[3], r[4]) for r in x.c.execute("SELECT product_id,model,application_text,year_from,year_to FROM applications")} if x.sync else set()
    for r in rows:
        if motor and _s(r.get("oem_code")):   # base MOTORCRAFT: guarda o item (PN Ford) com seus dados, vinculado ao código PERFECT correspondente
            nb, _ = normalize_code(r.get("oem_code"))
            if ("MOTORCRAFT", nb) not in have_b:
                have_b.add(("MOTORCRAFT", nb))
                x.c.execute("INSERT INTO brand_items(brand,code,norm_code,product_id,perfect_code,description,item_type,vehicle,application,years,box_code,suppliers,source_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            ("MOTORCRAFT", _s(r.get("oem_code")), nb, x.of(r.get("perfect_code")), _s(r.get("perfect_code")), _s(r.get("description")), _s(r.get("family")), _s(r.get("vehicle")), _s(r.get("application")), _s(r.get("year_range")), _s(r.get("box_code")), _s(r.get("supplier")), x.src))
        pid = x.of(r.get("perfect_code"))
        if not pid: x.unlink("oem", _s(r.get("perfect_code")), r, "código PERFECT não está no catálogo"); continue
        for f in ("oem_code", "oem_code_alt", "oem_code_proj"):
            raw = _s(r.get(f))
            if raw and raw != "-":
                if x.add_code(pid, raw, "oem", seen=seen) and x.sync: x.n["new"] += 1
        yr = (_s(r.get("year_range")) or "").split("/"); yf, yt = (_i(yr[0]), _i(yr[-1])) if yr[0] else (None, None)
        ak = (pid, _s(r.get("vehicle")), _s(r.get("application")), yf, yt)
        if ak in have: x.n["present"] += 1
        else:
            have.add(ak)
            x.c.execute("INSERT INTO applications(product_id,model,application_text,year_from,year_to,source_id) VALUES(?,?,?,?,?,?)", (pid, ak[1], ak[2], yf, yt, x.src)); x.n["new"] += 1
        _merge(x, pid, {"family": (_s(r.get("family")) or "").upper() or None, "package_code": _s(r.get("box_code"))})

def L_referencia_cruzada(x, rows):
    """'Números Referência': uma referência por linha, no formato 'CÓDIGO (MARCA)' — ex.: 16470 (MONROE). Vira código do produto: marca OEM -> tipo 'oem'; demais marcas -> 'concorrente'."""
    x.replace("codes"); x.replace("unlinked_rows")
    if not x.sync: x.c.execute("DELETE FROM catalog_vehicles WHERE source_id=?", (x.src,))
    if x.sync: x.reset_unlinked("referencia")
    _refs_vehicles(x, rows)

def _refs_vehicles(x, rows):
    """Veículos ('MONTADORA: MODELO 2001/2020', um por linha) → catalog_vehicles; Números Referência ('CÓDIGO (MARCA)') → codes."""
    seen = set(); rx = re.compile(r"^(.+?)\s*\(([^()]+)\)\s*$"); vrx = re.compile(r"^\s*([^:]+?)\s*:\s*(.+?)\s*$"); yrx = re.compile(r"^(.*?)\s*(\d{4})(?:\s*[/\-]\s*(\d{4}))?\s*$")
    have_v = {(a, b) for a, b in x.c.execute("SELECT product_id,raw FROM catalog_vehicles")} if x.sync else set()
    for r in rows:
        raw = _s(r.get("perfect_code")); pid = x.of(raw)
        for vl in str(r.get("vehicles") or "").replace("\r", "").split("\n"):   # 'FIAT: DOBLO SOMENTE CARGO 2001/2020' -> aplicação do catálogo (usada no módulo Lados)
            vl = vl.strip(); m = vrx.match(vl) if pid else None
            if not m or (pid, vl) in have_v: continue
            ym = yrx.match(m.group(2)); model, y1, y2 = (ym.group(1), int(ym.group(2)), int(ym.group(3) or ym.group(2))) if ym else (m.group(2), None, None)
            x.c.execute("INSERT INTO catalog_vehicles(product_id,make,model,year_from,year_to,raw,source_id) VALUES(?,?,?,?,?,?,?)", (pid, m.group(1).strip().upper(), model.strip().upper(), y1, y2, vl, x.src)); have_v.add((pid, vl))
        for line in str(r.get("cross_refs") or "").replace("\r", "").split("\n"):
            line = line.strip()
            if not line: continue
            m = rx.match(line); code, brand = (m.group(1).strip(), m.group(2).strip().upper()) if m else (line, None)
            if not pid: x.unlink("referencia", raw, {"perfect_code": raw, "referencia": line}, "código PERFECT não está no catálogo"); continue
            if x.add_code(pid, code, "oem" if brand == "OEM" else "concorrente", brand, seen): x.n["new"] += 1


def L_de_para(x, rows):
    x.replace("codes"); x.replace("unlinked_rows")
    if x.sync: x.reset_unlinked("de_para")
    seen = set()
    for r in rows:
        z = _s(r.get("zs_code"))
        if not z: x.err("linha sem código de fornecedor"); continue
        pid = x.of(r.get("perfect_code"))
        if len(z) > 30 or " " in z: x.unlink("de_para", _s(r.get("perfect_code")), r, "código de fornecedor suspeito (guardado sem vínculo)"); continue
        if not pid: x.unlink("de_para", _s(r.get("perfect_code")), r, "código PERFECT não está no catálogo"); continue
        if (pid, z) in seen: x.n["duplicates"] += 1; continue
        seen.add((pid, z))
        if x.add_code(pid, z, "fornecedor", "ZS", seen): x.n["new"] += 1

def L_fornecedor_erp(x, rows):
    x.replace("supplier_items"); x.replace("codes"); seen = set()
    have = {(r[0], r[1], r[2], r[3]) for r in x.c.execute("SELECT supplier_name,erp_code,supplier_code,supplier_code2 FROM supplier_items")} if x.sync else set()
    for r in rows:
        pid = x.of(r.get("supplier_code")); sup = _s(r.get("supplier_name"))
        k = (sup, _s(r.get("erp_code")), _s(r.get("supplier_code")), _s(r.get("supplier_code2")))
        if k in have: x.n["present"] += 1
        else:
            have.add(k)
            x.c.execute("INSERT INTO supplier_items(supplier_name,erp_code,item_type,supplier_code,supplier_code2,description,product_id,source_id) VALUES(?,?,?,?,?,?,?,?)",
                        (sup, _s(r.get("erp_code")), _s(r.get("item_type")), _s(r.get("supplier_code")), _s(r.get("supplier_code2")), _s(r.get("description")), pid, x.src)); x.n["new"] += 1
            if not pid: x.n["unmatched"] += 1
        if pid and _s(r.get("supplier_code2")): x.add_code(pid, _s(r.get("supplier_code2")), "fornecedor", sup, seen)

def L_certificados(x, rows):
    x.replace("certificates")
    have = {(r[0], r[1], r[2]) for r in x.c.execute("SELECT perfect_code_raw,inmetro_number,cert_description FROM certificates")} if x.sync else set()
    for r in rows:
        pid = x.of(r.get("perfect_code")); fam = (_s(r.get("family")) or "").upper() or None
        k = (_s(r.get("perfect_code")), _s(r.get("inmetro_number")), _s(r.get("description")))
        if k in have: x.n["present"] += 1; continue
        have.add(k)
        x.c.execute("INSERT INTO certificates(product_id,perfect_code_raw,inmetro_number,family,cert_description,source_id) VALUES(?,?,?,?,?,?)",
                    (pid, k[0], k[1], fam, k[2], x.src)); x.n["new"] += 1
        if not pid: x.n["unmatched"] += 1; continue
        _merge(x, pid, {"ean": _s(r.get("ean")), "family": fam})  # nº Inmetro fica só em certificates (um por fornecedor)

def L_estrutura(x, rows):
    x.replace("product_components")
    have = {(r[0], r[1], r[2], r[3]) for r in x.c.execute("SELECT parent_code,component_code,seq,date_from FROM product_components")} if x.sync else set()
    for r in rows:
        par, comp = _s(r.get("parent_code")), _s(r.get("component_code"))
        if not par or not comp: x.err("linha sem pai ou componente"); continue
        pid = x.of(par); k = (par, comp, _i(r.get("seq")), _s(r.get("date_from")))
        if k in have: x.n["present"] += 1; continue
        have.add(k)
        x.c.execute("INSERT INTO product_components(parent_code,product_id,component_code,component_desc,seq,qty,date_from,date_to,source_id) VALUES(?,?,?,?,?,?,?,?,?)",
                    (par, pid, comp, _s(r.get("component_desc")), k[2], _f(r.get("qty")), k[3], _s(r.get("date_to")), x.src)); x.n["new"] += 1
        if not pid: x.n["unmatched"] += 1
        elif comp.upper().startswith("PP"): _merge(x, pid, {"package_code": comp})

def L_lados(x, rows):
    x.replace("side_pairs"); x.replace("unlinked_rows")
    if x.sync: x.reset_unlinked("lados")
    for r in rows:
        a, b = x.of(r.get("rh_code")), x.of(r.get("lh_code"))
        if a and b:
            if x.c.execute("INSERT OR IGNORE INTO side_pairs(right_product_id,left_product_id,source_id) VALUES(?,?,?)", (a, b, x.src)).rowcount: x.n["new"] += 1
            else: x.n["present"] += 1
        else: x.unlink("lados", _s(r.get("rh_code")), r, "um dos códigos não está no catálogo")

def L_caixas(x, rows):
    for r in rows:
        code, dims = _s(r.get("box_code")), _s(r.get("box_dims_mm"))
        m = re.fullmatch(r"(\d+)x(\d+)x(\d+)", dims or "")
        if not code or not m: x.err(f"caixa {code}: dimensão em mm ilegível ({dims})"); continue
        L, W, H = map(float, m.groups())
        ex = x.c.execute("SELECT 1 FROM packaging_boxes WHERE code=?", (code,)).fetchone()
        if ex and x.sync: x.n["present"] += 1; continue
        x.c.execute("INSERT INTO packaging_boxes(code,length_mm,width_mm,height_mm,raw_dims,source_id) VALUES(?,?,?,?,?,?) ON CONFLICT(code) DO UPDATE SET length_mm=excluded.length_mm,width_mm=excluded.width_mm,height_mm=excluded.height_mm,raw_dims=excluded.raw_dims,source_id=excluded.source_id", (code, L, W, H, dims, x.src))
        x.n["updated" if ex else "new"] += 1
        cm = _s(r.get("box_dims_cm"))
        if cm:
            try: ok = [float(t.replace(",", ".")) for t in cm.split("x")] == [round(L / 10, 1), round(W / 10, 1), round(H / 10, 1)]
            except ValueError: ok = False
            if not ok and len(x.msgs) < 12: x.msgs.append(f"Aviso {code}: {dims} mm × coluna cm «{cm}». Usado o valor em mm.")

def _yes(v): return str(v or "").strip().upper() in ("SIM", "S", "1", "TRUE")

SAMPLE_FILL = (("ship_code", "ship_code"), ("sc_number", "sc_number"), ("application", "application"), ("supplier", "supplier"), ("month", "month"), ("tracking", "tracking"), ("credit_note", "credit_note"))

def L_amostras(x, rows):
    x.replace("sample_orders"); existing, used = {}, {}
    if x.sync:   # identidade da amostra = código PERFECT + código da amostra (o resto pode mudar ao longo do projeto)
        for r in x.c.execute("SELECT * FROM sample_orders").fetchall():
            existing.setdefault((r["perfect_code"] or "", r["sample_code"] or ""), []).append(r)
    for r in rows:
        pc, sc = _s(r.get("perfect_code")), _s(r.get("sample_code"))
        if not (pc or sc): continue
        k = (pc or "", sc or ""); n = used.get(k, 0); used[k] = n + 1; lst = existing.get(k, [])
        if x.sync and n < len(lst):   # já existe: preenche só campos vazios; etapa e edições feitas no sistema são preservadas
            cur = lst[n]; ch = {c: _s(r.get(f)) for f, c in SAMPLE_FILL if cur[c] in (None, "") and _s(r.get(f))}
            for f, c in (("net_weight", "net_weight"), ("gross_weight", "gross_weight")):
                if cur[c] is None and _f(r.get(f)) is not None: ch[c] = _f(r.get(f))
            for f in ("best_price", "price_usd"):
                if cur[f] is None and _f(r.get(f)) is not None: ch[f] = _f(r.get(f))
            if cur["side"] is None and db.side_from_text(_s(r.get("application"))): ch["side"] = db.side_from_text(_s(r.get("application")))
            if ch:
                x.c.execute("UPDATE sample_orders SET " + ",".join(c + "=?" for c in ch) + ",updated_at=CURRENT_TIMESTAMP WHERE id=?", [*ch.values(), cur["id"]]); x.n["updated"] += 1
            else: x.n["present"] += 1
            continue
        stage = "aprovado" if _yes(r.get("approved")) else "finalizado" if _yes(r.get("finished")) else "chegou" if _yes(r.get("arrived")) else "sc_aberta" if _yes(r.get("sc_open")) else "cotacao"
        ship = _s(r.get("ship_code")) or (("D-" + pc) if pc else None)
        oid = x.c.execute("INSERT INTO sample_orders(product_id,perfect_code,ship_code,sc_number,application,sample_code,supplier,month,tracking,net_weight,gross_weight,credit_note,stage,to_send,pending_supplier,side,source_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (x.of(pc), pc, ship, _s(r.get("sc_number")), _s(r.get("application")), sc, _s(r.get("supplier")), _s(r.get("month")), _s(r.get("tracking")),
             _f(r.get("net_weight")), _f(r.get("gross_weight")), _s(r.get("credit_note")), stage, int(_yes(r.get("to_send"))), int(_yes(r.get("pending_des"))), db.side_from_text(_s(r.get("application"))), x.src)).lastrowid
        x.n["new"] += 1
        x.c.execute("UPDATE sample_orders SET best_price=?, price_usd=? WHERE id=?", (_f(r.get("best_price")), _f(r.get("price_usd")), oid))      # MELHOR PREÇO (R$) e PREÇO DOLAR da planilha
        for i in (1, 2, 3):
            pr, lk = _f(r.get(f"price{i}")), _s(r.get(f"link{i}"))
            if pr is not None or (lk and lk != "-"): x.c.execute("INSERT INTO sample_quotes(order_id,price,link,chosen) VALUES(?,?,?,?)", (oid, pr, None if lk == "-" else lk, int(i == 1)))
        if not x.of(pc): x.n["unmatched"] += 1

def _brand_of(x):
    """Marca da planilha: pelo nome do arquivo («…Brands (MOTORCRAFT)…», «…BPROAUTO…»); MOTRIO também é reconhecida."""
    t = re.sub(r"[^A-Z]", "", (x.name or "").upper())
    for b in ("MOTORCRAFT", "BPROAUTO", "MOTRIO"):
        if b in t: return b
    return None

def L_marca(x, rows):
    """Planilhas «Shock Data - Brands (MOTORCRAFT)» / «Perfect Shock Data - Brands (BPROAUTO)»: LEFT JOIN pelo código PERFECT.
    Toda linha da planilha entra (lado esquerdo); o vínculo com o catálogo (product_id) é preenchido quando o código PERFECT existe em products.
    Reimportar substitui o que veio de planilhas de Brands dessa marca; itens da base ItensMotorcraft (outra fonte) são preservados."""
    brand = _brand_of(x)
    if not brand: raise ValueError("Não identifiquei a marca: o nome do arquivo precisa conter MOTORCRAFT, BPROAUTO ou MOTRIO (ex.: «Shock Data - Brands (MOTORCRAFT) - 03-11-2026.xlsx»).")
    if not x.sync:
        x.n["replaced"] += x.c.execute("DELETE FROM brand_items WHERE brand=? AND source_id IN (SELECT id FROM sources WHERE upper(name) LIKE '%BRANDS%')", (brand,)).rowcount
    have = {r[0]: r[1] for r in x.c.execute("SELECT norm_code,id FROM brand_items WHERE brand=?", (brand,))}
    for r in rows:
        code = _s(r.get("brand_code")); nb, _ = normalize_code(code)
        if not nb: x.err("linha sem código da marca"); continue
        pc = _s(r.get("perfect_code")); pid = x.of(pc)
        if nb in have:                                   # já existe (ex.: base ItensMotorcraft): só completa o que faltar
            if have[nb] and pid: x.c.execute("UPDATE brand_items SET product_id=coalesce(product_id,?), perfect_code=coalesce(perfect_code,?), vehicle=coalesce(vehicle,?) WHERE id=?", (pid, pc, _s(r.get("vehicle")), have[nb]))
            x.n["present"] += 1; continue
        have[nb] = 0
        x.c.execute("INSERT INTO brand_items(brand,code,norm_code,product_id,perfect_code,description,vehicle,source_id) VALUES(?,?,?,?,?,?,?,?)", (brand, code, nb, pid, pc, _s(r.get("description")), _s(r.get("vehicle")), x.src))
        x.n["new"] += 1
        if pc and not pid: x.n["unmatched"] += 1
    if x.n["unmatched"]: x.msgs.append(f"{x.n['unmatched']} código(s) PERFECT da planilha não estão no catálogo (ficam no Brands sem vínculo).")

LOADERS = {"marca": L_marca, "amostras": L_amostras, "caixas": L_caixas, "estrutura": L_estrutura, "lados": L_lados, "fornecedor_erp": L_fornecedor_erp, "desenvolvimento": L_desenvolvimento,
           "certificados": L_certificados, "de_para": L_de_para, "oem": L_oem, "referencia_cruzada": L_referencia_cruzada, "catalogo": L_catalogo}

def run(path, sheet, mapping, category, filename, confirm, policy="keep", sync=False, conn=None):
    """Simula (confirm=False -> rollback) ou grava (confirm=True). Retorna o resumo."""
    mapping = {c: f for c, f in (mapping or {}).items() if f}
    fields = list(mapping.values()); dup = sorted({f for f in fields if fields.count(f) > 1})
    if dup: raise ValueError("Campo mapeado em mais de uma coluna: " + ", ".join(dup))
    kind = next((k for k, req in KINDS if req <= set(fields)), None)
    if kind == "desenvolvimento" and os.environ.get("PSD_ALLOW_EXCEL_DES") != "1":
        raise ValueError("Desenvolvimento/Redesenvolvimento agora vêm do servidor SQL (DESENVOLVIMENTO_PRODUTOS). Use «Sincronizar» no topo da tela; importar planilha não é mais permitido para esses itens.")
    if not kind: raise ValueError("Mapeamento insuficiente para reconhecer o tipo de dado. Mapeie ao menos o código e um campo característico (ex.: descrição, RH/LH, inmetro, componente).")
    df, _ = read_table(path, None if sheet in (None, "", "(csv)") else sheet)
    miss = [c for c in mapping if c not in df.columns]
    if miss: raise ValueError("Colunas não encontradas na planilha: " + ", ".join(miss))
    rows = df[list(mapping)].rename(columns=mapping).fillna("").to_dict("records")
    if kind == "desenvolvimento":   # demais colunas da planilha (OEM, concorrentes, IPI, Inmetro, usuários...) ficam em "extra", visíveis no detalhe
        raw = df.fillna("").to_dict("records"); other = [c for c in df.columns if c not in mapping]
        for rec, rw in zip(rows, raw): rec["_raw"] = {str(c).strip(): _fmt(rw[c]) for c in other if _fmt(rw[c]) != ""}
    name = filename + (f" [{sheet}]" if sheet and sheet != "(csv)" else "")
    own = conn is None; conn = conn or db.conn()
    try:
        norm = lambda s: re.sub(r"[\s_]+", " ", s.lower()).strip()   # 'DadosR-D_e_DES.xlsx' == 'DadosR-D e DES.xlsx' (mesma fonte, nova versão)
        r = next(((i,) for i, n_ in conn.execute("SELECT id,name FROM sources") if norm(n_) == norm(name)), None)
        src = r[0] if r else conn.execute("INSERT INTO sources(name,category) VALUES(?,?)", (name, category or LABEL[kind])).lastrowid
        x = Ctx(conn, src, name, policy, sync); LOADERS[kind](x, rows)
        n = x.n; bid = conn.execute("INSERT INTO import_batches(source_id,filename,sheet,category,rows_new,rows_updated,rows_conflict,rows_error,rows_read,status) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (src, filename, sheet, category or LABEL[kind], n["new"], n["updated"], n["conflicts"], n["errors"], len(rows), "ok" if confirm else "simulado")).lastrowid
        if own: conn.commit() if confirm else conn.rollback()
        return {"kind": kind, "label": LABEL[kind], "rows": len(rows), "counts": n, "messages": x.msgs, "confirmed": confirm, "batch_id": bid if confirm else None}
    except Exception:
        if own: conn.rollback()
        raise
    finally:
        if own: conn.close()


def run_generic(path, sheet, filename, confirm, conn=None, category="Dados avulsos (planilha nova)"):
    """Planilha cujo conteúdo não é um tipo conhecido: guarda todas as linhas como estão (fonte + histórico) e, nas próximas leituras, insere só as que faltam."""
    df, _ = read_table(path, None if sheet in (None, "", "(csv)") else sheet)
    if df.empty: raise ValueError("Planilha vazia.")
    df = df.fillna(""); cols = [str(c) for c in df.columns]; name = filename + (f" [{sheet}]" if sheet and sheet != "(csv)" else "")
    own = conn is None; conn = conn or db.conn()
    try:
        norm = lambda s: re.sub(r"[\s_]+", " ", s.lower()).strip()
        r = next(((i,) for i, n_ in conn.execute("SELECT id,name FROM sources") if norm(n_) == norm(name)), None)
        meta = json.dumps({"generic": True, "columns": cols}, ensure_ascii=False)
        if r: src = r[0]; conn.execute("UPDATE sources SET notes=? WHERE id=?", (meta, src))
        else: src = conn.execute("INSERT INTO sources(name,category,notes) VALUES(?,?,?)", (name, category, meta)).lastrowid
        have = {h[0] for h in conn.execute("SELECT row_hash FROM generic_rows WHERE source_id=?", (src,))}
        bid = conn.execute("INSERT INTO import_batches(source_id,filename,sheet,category,rows_new,rows_updated,rows_conflict,rows_error,rows_read,status) VALUES(?,?,?,?,?,?,?,?,?,?)",
                           (src, filename, sheet, category, 0, 0, 0, 0, len(df), "ok" if confirm else "simulado")).lastrowid
        new = present = 0; occ = {}
        for i, rec in enumerate(df.to_dict("records")):
            vals = {c: str(rec[o]).strip() for c, o in zip(cols, df.columns)}
            if not any(vals.values()): continue
            body = json.dumps(vals, ensure_ascii=False); n_ = occ.get(body, 0); occ[body] = n_ + 1   # linhas idênticas contam como linhas diferentes
            h = hashlib.sha1(f"{body}#{n_}".encode("utf-8")).hexdigest()
            if h in have: present += 1; continue
            conn.execute("INSERT INTO generic_rows(source_id,batch_id,sheet,row_no,row_hash,payload) VALUES(?,?,?,?,?,?)", (src, bid, sheet, i + 1, h, body)); new += 1
        conn.execute("UPDATE import_batches SET rows_new=? WHERE id=?", (new, bid))
        if own: conn.commit() if confirm else conn.rollback()
        return {"kind": "generic", "label": category, "rows": len(df), "counts": {"new": new, "present": present, "updated": 0, "unmatched": 0, "conflicts": 0, "errors": 0},
                "messages": [f"Estrutura não corresponde a um cadastro conhecido: {len(cols)} colunas guardadas como estão (consulte em Fontes e histórico → Ver dados)."], "confirmed": confirm, "batch_id": bid if confirm else None}
    except Exception:
        if own: conn.rollback()
        raise
    finally:
        if own: conn.close()
