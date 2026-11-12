"""Módulo Lados — interpreta AUTOMATICAMENTE, para cada amortecedor do catálogo, o lado, o par do outro lado e o amortecedor do OUTRO EIXO
(nos dianteiros, o traseiro; nos traseiros, o dianteiro) da mesma aplicação — e o PAR desse traseiro, montando o conjunto completo do veículo.

Fontes, em ordem de confiança:
  1. Planilha «Lados - Amortecedores.xlsx» (side_pairs)          → par LD × LE oficial.
  2. Catálogo «Produtos Relacionados» (CatalogoAMD.xlsx)        → par do outro lado (mesmo eixo, lado oposto) e o amortecedor do outro eixo.
  3. Aplicação do catálogo (Veículos: montadora, modelo e anos)  → mesmo modelo e anos que se cruzam = «exata»; mesmo modelo-base = «provável».
  4. Servidor (DESENVOLVIMENTO_PRODUTOS: montadora, veículo, aplicação e anos de cada código DES/R-D) → mesma aplicação no servidor;
     se o código encontrado ainda não está no catálogo, aparece como «em desenvolvimento» (com o status do servidor).
Regra de lado: um LD casa com LD (ou com um código LD/LE único); nunca LD com LE no outro eixo. Item inativo só casa com inativo."""
import re, unicodedata
import database as db
from queries import q

SIDE = {"direito": "Direito (LD)", "esquerdo": "Esquerdo (LE)", "ambos": "Ambos (LD/LE)"}
LEVELS = {"relacionado": "Produtos Relacionados (catálogo)", "exata": "Mesma aplicação (catálogo)", "servidor": "Mesma aplicação (servidor DES/R-D)",
          "desenvolvimento": "Em desenvolvimento (servidor)", "provavel": "Mesmo modelo-base — confira a versão"}
_RANK = {"relacionado": 0, "exata": 1, "servidor": 2, "desenvolvimento": 3, "provavel": 4}

def _up(t): return unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().upper()
def _axle(desc):
    d = _up(desc)
    if "DIANTEIRO/TRASEIRO" in d or ("DIANT" in d and "TRAS" in d): return "ambos_eixos"
    if "DIANT" in d: return "dianteiro"
    if "TRAS" in d: return "traseiro"
    if "CABINE" in d: return "cabine"
    return None
def _status(desc):
    d = _up(desc); return "inativo" if "INATIVO" in d else "em_breve" if "EM BREVE" in d else "ativo"
def _mkey(model): return re.sub(r"[^A-Z0-9()/ .+-]", "", re.sub(r"\s+", " ", _up(model))).strip()
def _first(model):
    t = re.findall(r"[A-Z0-9]+", _up(model)); return t[0] if t else ""
def _norm(t): return re.sub(r"[^A-Z0-9]", "", _up(t))
def _overlap(a1, a2, b1, b2):
    a2 = a2 if a2 is not None else a1 and 9999; b2 = b2 if b2 is not None else b1 and 9999
    if None in (a1, a2, b1, b2): return True
    return a1 <= b2 and b1 <= a2
def _side_ok(a, b):
    """LD casa com LD ou com LD/LE; LE com LE ou LD/LE; nunca LD × LE."""
    return not (a in ("direito", "esquerdo") and b in ("direito", "esquerdo") and a != b)

def _server_rows():
    """Linhas de amortecedor do servidor (DES/R-D): código, eixo, lado e aplicação normalizada."""
    import rules
    try: rows = q(f"SELECT code, suggestion, status, make, vehicle, application_text, year_from, year_to, description FROM rd_projects WHERE {rules.desc_sql('description')}")
    except Exception: return []
    out = []
    for r in rows:
        ax = _axle(r["description"])
        if ax not in ("dianteiro", "traseiro") or not r["make"] or not r["vehicle"]: continue
        out.append({"code": (r["code"] or "").upper(), "kind": r["suggestion"], "status": r["status"], "axle": ax, "side": db.side_from_text(r["description"]),
                    "key": (_norm(r["make"]), _norm(r["vehicle"]), _norm(r["application_text"])), "y1": r["year_from"], "y2": r["year_to"], "app": " ".join(str(x) for x in (r["make"], r["vehicle"], r["application_text"], r["year_from"] or "", "–" if r["year_from"] else "", r["year_to"] or "") if x).strip()})
    return out

def build():
    prods = {p["id"]: p for p in q("SELECT id,perfect_code,description,catalog_position FROM products WHERE catalog_position IS NOT NULL")}
    by_code = {(p["perfect_code"] or "").upper(): pid for pid, p in prods.items()}
    veh = {}
    for v in q("SELECT product_id,make,model,year_from,year_to,raw FROM catalog_vehicles"): veh.setdefault(v["product_id"], []).append(v)
    pairs = {}
    for r in q("SELECT right_product_id r,left_product_id l FROM side_pairs"): pairs[r["r"]] = r["l"]; pairs[r["l"]] = r["r"]
    try: rel = q("SELECT product_id, related_code, related_product_id FROM product_relations ORDER BY product_id, seq")
    except Exception: rel = []
    rels = {}
    for r in rel: rels.setdefault(r["product_id"], []).append(r)
    items = {}
    for pid, p in prods.items():        # ESCOPO: só itens do CATÁLOGO (planilha CatalogoAMD)
        d = p["description"]; sd = db.side_from_text(d)
        if sd is None: sd = db.side_from_text(" ; ".join(str(v["raw"] or "") for v in veh.get(pid, [])))      # sem lado na descrição: procura na Aplicação do catálogo
        items[pid] = {"id": pid, "code": p["perfect_code"], "description": d, "axle": _axle(d), "side": sd, "status": _status(d), "vehicles": veh.get(pid, []), "pair": None, "pair_how": None,
                      "rear": [], "front": [], "in_lados": pid in pairs, "server_apps": []}
    # ── servidor: aplicações de cada código (inclusive itens já no catálogo) ──
    srv = _server_rows(); srv_by_code, srv_idx, srv_veh = {}, {}, {}
    for s in srv:
        srv_by_code.setdefault(s["code"], []).append(s); srv_idx.setdefault((s["axle"], s["key"]), []).append(s); srv_veh.setdefault((s["axle"], s["key"][:2]), []).append(s)
    for it in items.values(): it["server_apps"] = sorted({s["app"] for s in srv_by_code.get((it["code"] or "").upper(), [])})[:6]
    # ── 1) par do outro lado ──
    for pid, it in items.items():
        if pid in pairs and pairs[pid] in items:
            o = items[pairs[pid]]; it["pair"] = {"id": o["id"], "code": o["code"], "side": o["side"]}; it["pair_how"] = "planilha Lados"
    for pid, it in items.items():       # 2) Produtos Relacionados: mesmo eixo, lado oposto
        if it["pair"] or it["side"] not in ("direito", "esquerdo"): continue
        for r in rels.get(pid, []):
            o = items.get(r["related_product_id"])
            if o and o["axle"] == it["axle"] and o["side"] in ("direito", "esquerdo") and o["side"] != it["side"]:
                it["pair"] = {"id": o["id"], "code": o["code"], "side": o["side"]}; it["pair_how"] = "Produtos Relacionados (catálogo)"; break
    idx_exact, idx_first = {}, {}
    for pid, it in items.items():
        for v in it["vehicles"]:
            idx_exact.setdefault((it["axle"], v["make"], _mkey(v["model"])), []).append((pid, v["year_from"], v["year_to"]))
            idx_first.setdefault((it["axle"], v["make"], _first(v["model"])), []).append((pid, v["year_from"], v["year_to"]))
    for pid, it in items.items():       # 3) mesma aplicação (catálogo), lado oposto
        if it["pair"] or it["side"] not in ("direito", "esquerdo") or not it["axle"]: continue
        opp = "esquerdo" if it["side"] == "direito" else "direito"; found = {}
        for v in it["vehicles"]:
            for o, y1, y2 in idx_exact.get((it["axle"], v["make"], _mkey(v["model"])), []):
                if o != pid and items[o]["side"] == opp and items[o]["status"] == it["status"] and _overlap(v["year_from"], v["year_to"], y1, y2): found[o] = found.get(o, 0) + 1
        if found:
            o = items[max(found, key=found.get)]; it["pair"] = {"id": o["id"], "code": o["code"], "side": o["side"]}; it["pair_how"] = "mesma aplicação (catálogo)"
    for pid, it in items.items():       # 4) mesma aplicação no servidor, lado oposto
        if it["pair"] or it["side"] not in ("direito", "esquerdo"): continue
        opp = "esquerdo" if it["side"] == "direito" else "direito"
        for s in srv_by_code.get((it["code"] or "").upper(), []):
            o = next((by_code[x["code"]] for x in srv_idx.get((s["axle"], s["key"]), []) if x["side"] == opp and x["code"] in by_code and _overlap(s["y1"], s["y2"], x["y1"], x["y2"])), None)
            if o and o in items: oi = items[o]; it["pair"] = {"id": oi["id"], "code": oi["code"], "side": oi["side"]}; it["pair_how"] = "mesma aplicação (servidor)"; break

    def pair_of(pid):
        p = items[pid]["pair"]; return p and {"code": p["code"], "side": p["side"], "id": p["id"]}

    def match(it, want_axle):
        """Códigos do outro eixo para a mesma aplicação, do mais confiável ao menos (ver LEVELS)."""
        res = {}
        def add(key, lvl, **kw):
            if key not in res or _RANK[lvl] < _RANK[res[key]["level"]]: res[key] = {"level": lvl, **kw}
        for r in rels.get(it["id"], []):
            o = items.get(r["related_product_id"])
            if o and o["axle"] == want_axle: add(("p", o["id"]), "relacionado")
        for v in it["vehicles"]:
            ex = [(o, y1, y2) for o, y1, y2 in idx_exact.get((want_axle, v["make"], _mkey(v["model"])), []) if _overlap(v["year_from"], v["year_to"], y1, y2)]
            for o, *_ in ex: add(("p", o), "exata")
            if not ex:
                for o, y1, y2 in idx_first.get((want_axle, v["make"], _first(v["model"])), []):
                    if _overlap(v["year_from"], v["year_to"], y1, y2): add(("p", o), "provavel")
        for s in srv_by_code.get((it["code"] or "").upper(), []):
            for x in srv_idx.get((want_axle, s["key"]), []):
                if not _overlap(s["y1"], s["y2"], x["y1"], x["y2"]): continue
                if x["code"] in by_code: add(("p", by_code[x["code"]]), "servidor", app=s["app"])
                else: add(("d", x["code"]), "desenvolvimento", code=x["code"], side=x["side"], status=x["status"], kind=x["kind"], app=s["app"])
            for x in srv_veh.get((want_axle, s["key"][:2]), []):      # mesma montadora e veículo, versão/aplicação escrita diferente: provável
                if x["code"] in by_code and _overlap(s["y1"], s["y2"], x["y1"], x["y2"]): add(("p", by_code[x["code"]]), "provavel", app=s["app"])
        out = []
        for (t, k), m in res.items():
            if t == "p":
                o = items[k]
                if not _side_ok(it["side"], o["side"]) or (o["status"] == "inativo" and it["status"] != "inativo"): continue
                out.append({"id": o["id"], "code": o["code"], "side": o["side"], "level": m["level"], "description": o["description"], "pair": pair_of(o["id"]), "app": m.get("app"), "in_catalog": True})
            else:
                if not _side_ok(it["side"], m["side"]): continue
                out.append({"id": None, "code": m["code"], "side": m["side"], "level": "desenvolvimento", "status": m["status"], "kind": m["kind"], "app": m["app"], "in_catalog": False, "pair": None})
        strong = [x for x in out if x["level"] != "provavel"]
        return sorted(strong or out, key=lambda x: (_RANK[x["level"]], x["code"]))

    for pid, it in items.items():
        if it["axle"] == "dianteiro": it["rear"] = match(it, "traseiro")
        elif it["axle"] == "traseiro": it["front"] = match(it, "dianteiro")
        other = it["rear"] if it["axle"] == "dianteiro" else it["front"] if it["axle"] == "traseiro" else []
        it["has_vehicles"] = bool(it["vehicles"] or it["server_apps"])
        lv = {x["level"] for x in other}
        it["other_axle"] = ("nao_se_aplica" if it["axle"] not in ("dianteiro", "traseiro") else "exata" if lv & {"relacionado", "exata", "servidor"} else "desenvolvimento" if "desenvolvimento" in lv
                            else "provavel" if lv else "sem_aplicacao" if not it["has_vehicles"] else "nao")
        it["kit"] = kit(it)
    return items

def kit(it):
    """Conjunto completo do veículo a partir do item: dianteiros (item + par) e traseiros (melhor candidato + par dele). Lista de {code, axle, side, qty}."""
    fr = it if it["axle"] == "dianteiro" else None
    out, seen = [], set()
    def put(code, axle, side, src=None):
        if code and code not in seen: seen.add(code); out.append({"code": code, "axle": axle, "side": side, "qty": 2 if side == "ambos" else 1, "src": src})
    if it["axle"] not in ("dianteiro", "traseiro"): return []
    other = it["rear"] if fr else it["front"]; best = [x for x in other if x["level"] == other[0]["level"]] if other else []
    put(it["code"], it["axle"], it["side"]); it["pair"] and put(it["pair"]["code"], it["axle"], it["pair"]["side"])
    oa = "traseiro" if fr else "dianteiro"
    for x in best[:2]:
        put(x["code"], oa, x["side"], x["level"]); x.get("pair") and put(x["pair"]["code"], oa, x["pair"]["side"], x["level"])
    return out

def has_sides(i): return i["side"] in ("direito", "esquerdo")      # «possui lados»: o catálogo separa LD e LE (descrição «LD» ou «LE»); LD/LE juntos = um item só, sem lados

def listing(f):
    every = list(build().values())
    scope = f.get("escopo") or "lados"
    # escopo «lados» (padrão): itens com LD/LE separados ou que estão na planilha Lados · «todos»: todos os dianteiros/traseiros do catálogo (inclui os LD/LE de código único)
    items = [i for i in every if has_sides(i) or i["in_lados"]] if scope == "lados" else [i for i in every if i["axle"] in ("dianteiro", "traseiro")]
    term = (f.get("q") or "").upper().split()
    def ok(i):
        if term:
            txt = f"{i['code']} {i['description'] or ''} " + " ".join(v["raw"] or "" for v in i["vehicles"]).upper() + " " + " ".join(i["server_apps"]).upper() + " " + " ".join(r["code"] for r in i["rear"] + i["front"]) + " " + ((i["pair"] or {}).get("code") or "")
            if any(t not in txt.upper() for t in term): return False
        if f.get("axle") and i["axle"] != f["axle"]: return False
        if f.get("side") and i["side"] != f["side"]: return False
        if f.get("pair") == "sem" and (i["pair"] or i["side"] not in ("direito", "esquerdo")): return False
        if f.get("pair") == "com" and not i["pair"]: return False
        if f.get("rear") == "sem" and not (i["axle"] == "dianteiro" and not i["rear"]): return False
        if f.get("rear") == "com" and not i["rear"]: return False
        if f.get("other") and i["other_axle"] != f["other"]: return False
        if f.get("status") and i["status"] != f["status"]: return False
        return True
    rows = sorted((i for i in items if ok(i)), key=lambda i: (i["code"] or ""))
    fr = [i for i in items if i["axle"] == "dianteiro"]
    stats = {"total": len(items), "dianteiro": len(fr), "traseiro": sum(i["axle"] == "traseiro" for i in items), "com_traseiro": sum(1 for i in items if i["rear"]),
             "dianteiro_sem_traseiro": sum(1 for i in fr if not i["rear"] and i["status"] == "ativo"), "sem_par": sum(1 for i in items if not i["pair"] and has_sides(i)),
             "traseiro_exato": sum(1 for i in fr if i["other_axle"] == "exata"), "traseiro_provavel": sum(1 for i in fr if i["other_axle"] == "provavel"),
             "traseiro_desenvolvimento": sum(1 for i in fr if i["other_axle"] == "desenvolvimento"),
             "traseiro_nao": sum(1 for i in fr if i["other_axle"] == "nao"), "sem_aplicacao": sum(1 for i in items if i["other_axle"] == "sem_aplicacao"),
             "por_relacionados": sum(1 for i in fr if any(x["level"] == "relacionado" for x in i["rear"])), "por_servidor": sum(1 for i in fr if any(x["level"] in ("servidor", "desenvolvimento") for x in i["rear"])),
             "pares_planilha": sum(1 for i in items if i["pair_how"] == "planilha Lados"), "pares_automaticos": sum(1 for i in items if i["pair"] and i["pair_how"] != "planilha Lados"),
             "com_par": sum(1 for i in items if i["pair"]), "direito": sum(i["side"] == "direito" for i in items), "esquerdo": sum(i["side"] == "esquerdo" for i in items),
             **{k: sum(i["status"] == k for i in items) for k in ("ativo", "em_breve", "inativo")}}          # cada contagem = total da lista com o filtro do atalho (tela Lados)
    size = 50 if not f.get("all") else 10**9; page = max(1, int(f.get("page") or 1))
    out = []
    for i in rows[(page - 1) * size: page * size]:
        j = dict(i); j["vehicles"] = [v["raw"] for v in i["vehicles"]]; out.append(j)
    return {"total": len(rows), "page": page, "size": size, "rows": out, "stats": stats, "levels": LEVELS, "escopo": scope}
