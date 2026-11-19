"""Cobertura de concorrentes (etapa 17 · Q12/Q13/Q21–Q23/Q27/Q28) — tela «Cobertura de concorrentes».
  • Catálogo (aba padrão): só itens do catálogo. Uma linha por concorrente × referência × nosso código, com descrição, aplicação, linha, curva ABC de vendas
    do nosso item (12 meses fechados, universo do BI — curva_abc.classes) e situação do estoque (estoque.mapa). Referências pela regra Q18
    (CrossCatalogo quando a planilha tem o item; senão o servidor). OEM não é concorrente e fica fora.
    Cartões por concorrente (códigos nossos cobertos e quantos em A/B/C); atalhos concorrente, curva e linha — cada contagem = lista ao clicar.
  • Desenvolvimento: DES em andamento (universo amortecedor, não bloqueado, sem ITEM RECEBIDO e sem cancelado; R-D fora) com curva PRÓPRIA pela frota:
      frota do item = soma da frota do ano atual dos veículos da Fraga (LANÇAMENTOS) que batem com a aplicação — mesma marca, nome do veículo e ano de venda dentro
      dos anos da aplicação (várias aplicações somam; o mesmo veículo × ano não conta duas vezes);
      sem casamento → frota do arquivo COFAP × Fraga pela referência COFAP do servidor; por último a FROTA do servidor (DESENVOLVIMENTO_PRODUTOS).
      Curva A até 80% da frota acumulada, B até 95%, C o resto; sem frota = «sem dado». Selo «Lançamento» = algum veículo com início de produção a partir de 2024."""
import re, json, datetime, unicodedata
from collections import Counter
from queries import q, q1

LANC_DESDE = 2024
def _un(s): return unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().upper()
def _tok(s): return re.sub(r"[^A-Z0-9 ]", " ", _un(s)).split()
def _k(c): return re.sub(r"[^A-Z0-9]", "", re.sub(r"^\s*MP-", "", str(c or "").upper()))
def _ano(v):
    m = re.match(r"\s*(\d{4})", str(v or "")); return int(m.group(1)) if m else None

# ---------------- catálogo ----------------
def _catalogo_rows():
    import concorrentes as cc, curva_abc, estoque
    prods = {r["id"]: r for r in q("SELECT id, perfect_code, description, catalog_line FROM products WHERE catalog_position IS NOT NULL")}
    cross = {}
    for r in q("""SELECT k.product_id, k.brand, k.code FROM codes k JOIN sources s ON s.id=k.source_id WHERE s.name=? AND k.code_type='concorrente'""", (cc.CROSS_SRC,)):
        if r["product_id"] in prods: cross.setdefault(r["product_id"], []).append((cc.nome(r["brand"]) or "—", r["code"]))
    srv = {}
    if cc.available():
        for r in q("SELECT code, competitor, MIN(reference) reference FROM concorrentes WHERE is_oem=0 GROUP BY code, competitor, ref_key"):
            srv.setdefault(r["code"], []).append((r["competitor"], r["reference"]))
    apps = {}
    for r in q("SELECT product_id, make, model, year_from, year_to FROM applications ORDER BY make, model, year_from"):
        if r["product_id"] in prods:
            t = " ".join(x for x in (r["make"], r["model"]) if x)
            if r["year_from"] or r["year_to"]: t += f" {r['year_from'] or '…'}–{r['year_to'] or '…'}"
            lst = apps.setdefault(r["product_id"], [])
            if t and t not in lst: lst.append(t)
    cls = curva_abc.classes(); est, _, _ = estoque.mapa()
    out = []
    for pid, p in prods.items():
        refs = cross.get(pid) or srv.get(p["perfect_code"].upper()) or []
        fonte = "CrossCatalogo" if pid in cross else "servidor"
        k = _k(p["perfect_code"]); a = apps.get(pid, [])
        for comp, ref in refs:
            out.append({"concorrente": comp, "referencia": ref, "codigo": p["perfect_code"], "product_id": pid, "descricao": p["description"], "linha": p["catalog_line"],
                        "aplicacao": " · ".join(a[:3]) + (f" (+{len(a) - 3})" if len(a) > 3 else ""), "curva": cls.get(k) or "sem", "situacao": (est.get(k) or {}).get("situacao") or "sem", "fonte": fonte})
    out.sort(key=lambda r: (r["concorrente"], r["codigo"], r["referencia"]))
    return out

CAT_F = ("concorrente", "curva", "linha")
def catalogo(f=None, page=1, size=200):
    f = f or {}; rows = _catalogo_rows(); term = (f.get("q") or "").upper().split()
    def ok(r, skip=""):
        for k in CAT_F:
            if k != skip and f.get(k) and str(r.get(k) or "sem") != f[k]: return False
        return all(t in f"{r['concorrente']} {r['referencia']} {r['codigo']} {r['descricao'] or ''} {r['aplicacao']}".upper() for t in term)
    sel = [r for r in rows if ok(r)]
    counts = {k: dict(Counter(str(r.get(k) or "sem") for r in rows if ok(r, k)).most_common()) for k in CAT_F}
    # cartões: por concorrente, códigos nossos cobertos e quantos em A/B/C (com os outros filtros, sem o de concorrente)
    cards = {}
    for r in (r for r in rows if ok(r, "concorrente")):
        c = cards.setdefault(r["concorrente"], {"concorrente": r["concorrente"], "codigos": set(), "A": set(), "B": set(), "C": set()})
        c["codigos"].add(r["codigo"])
        if r["curva"] in "ABC" and r["curva"] != "sem": c[r["curva"]].add(r["codigo"])
    cards = sorted(({"concorrente": c["concorrente"], "codigos": len(c["codigos"]), "A": len(c["A"]), "B": len(c["B"]), "C": len(c["C"])} for c in cards.values()), key=lambda c: -c["codigos"])
    catalogo_total = q1("SELECT COUNT(*) n FROM products WHERE catalog_position IS NOT NULL")["n"]
    nossos = len({r["codigo"] for r in sel})
    page = max(int(page or 1), 1); n = 10**9 if f.get("all") else size
    return {"total": len(sel), "rows": sel[(page - 1) * n: page * n], "page": page, "size": n, "counts": counts, "cards": cards,
            "kpis": {"referencias": len(sel), "concorrentes": len({r["concorrente"] for r in sel}), "nossos_codigos": nossos, "catalogo": catalogo_total}}

# ---------------- desenvolvimento ----------------
_CACHE = {}
def _fraga_index():
    """{marca: [(id, tokens do veículo, ano de venda, frota, início de produção, nome)]} — LANÇAMENTOS da Fraga."""
    try: rows = q("SELECT rowid id, marca, veiculo, modelo, ano_venda, frota, inicio FROM fraga_veiculos WHERE frota > 0")
    except Exception: rows = []
    idx = {}
    for r in rows:
        idx.setdefault(" ".join(_tok(r["marca"])), []).append((r["id"], set(_tok(r["veiculo"])), _tok(r["veiculo"]), r["ano_venda"], r["frota"] or 0, _ano(r["inicio"]), f"{r['marca']} {r['veiculo']} {r['ano_venda']}"))
    return idx

def _match(idx, make, vehicle, y0, y1):
    """Veículos da Fraga da mesma marca cujo nome contém as duas primeiras palavras do veículo da aplicação (a 1ª no começo), com ano de venda dentro da aplicação."""
    cand = idx.get(" ".join(_tok(make)))
    vt = _tok(vehicle)
    if not cand or not vt: return []
    want = vt[:2]
    return [c for c in cand if c[2] and c[2][0] == want[0] and all(w in c[1] for w in want) and (y0 is None or (c[3] or 0) >= y0) and (y1 is None or (c[3] or 9999) <= y1)]

def _des_rows():
    import rules, kinds, concorrentes as cc
    key = (datetime.date.today().isoformat(), (q1("SELECT MAX(id) i FROM ds_runs") or {}).get("i"), (q1("SELECT COUNT(*) n FROM fraga_veiculos") or {}).get("n") if _has("fraga_veiculos") else 0,
           (q1("SELECT COUNT(*) n FROM fraga_pecas") or {}).get("n") if _has("fraga_pecas") else 0)
    if _CACHE.get("k") == key: return _CACHE["v"]
    apps = q(f"""SELECT r.code, r.description, r.make, r.vehicle, r.application_text, r.year_from, r.year_to, r.status, r.supplier, r.extra FROM rd_projects r
                 WHERE r.suggestion=? AND {rules.desc_sql('r.description')}
                   AND upper(r.code) NOT IN (SELECT upper(code) FROM rd_projects GROUP BY upper(code) HAVING MAX(upper(coalesce(status,''))='ITEM RECEBIDO')=1 OR MAX(upper(coalesce(status,'')) LIKE 'CANCEL%')=1)
                   AND r.code NOT IN (SELECT code FROM rd_projects WHERE suggestion=?)
                 ORDER BY r.code""", (kinds.DES, kinds.RD))
    idx = _fraga_index()
    cofap = {}
    if _has("fraga_pecas"):
        for r in q("SELECT cofap, frota FROM fraga_pecas WHERE cofap IS NOT NULL AND frota > 0"):
            for c in re.split(r"[;,/ ]+", r["cofap"]):
                if _k(c): cofap[_k(c)] = cofap.get(_k(c), 0) + (r["frota"] or 0)
    refs = {}
    if cc.available():
        for r in q("SELECT code, competitor, reference, is_oem FROM concorrentes"): refs.setdefault(r["code"], []).append(r)
    by = {}
    for a in apps:
        code = a["code"].upper()
        g = by.setdefault(code, {"codigo": code, "descricao": a["description"], "status": a["status"], "fornecedor": a["supplier"], "aplicacoes": [], "_hits": {}, "_frota_srv": 0})
        g["aplicacoes"].append(" ".join(str(x) for x in (a["make"], a["vehicle"], (f"{a['year_from'] or '…'}–{a['year_to'] or '…'}" if a["year_from"] or a["year_to"] else "")) if x))
        for h in _match(idx, a["make"], a["vehicle"], _ano(a["year_from"]), _ano(a["year_to"])): g["_hits"][h[0]] = h
        try: g["_frota_srv"] = max(g["_frota_srv"], float(json.loads(a["extra"] or "{}").get("FROTA") or 0))
        except (ValueError, TypeError): pass
    out = []
    for g in by.values():
        hits = list(g.pop("_hits").values()); fs = g.pop("_frota_srv")
        rr = refs.get(g["codigo"], [])
        g["concorrentes"] = [f"{r['competitor']} {r['reference']}" for r in rr if not r["is_oem"]][:12]
        if hits:
            g["frota"], g["origem"] = sum(h[4] for h in hits), "Fraga · veículos"
            top = sorted(hits, key=lambda h: -h[4])[:6]; g["veiculos"] = [{"nome": h[6], "frota": h[4]} for h in top]
            g["lancamento"] = any((h[5] or 0) >= LANC_DESDE for h in hits)
        else:
            cof = sum(cofap.get(_k(r["reference"]), 0) for r in rr if r["competitor"] == "COFAP")
            g["frota"], g["origem"] = (cof, "Fraga · COFAP") if cof else ((fs, "Servidor (FROTA)") if fs else (0, "sem dado"))
            g["veiculos"] = []; g["lancamento"] = False
        g["aplicacoes"] = list(dict.fromkeys(x for x in g["aplicacoes"] if x))
        out.append(g)
    vals = sorted((g for g in out if g["frota"] > 0), key=lambda g: -g["frota"]); tot = sum(g["frota"] for g in vals) or 1; acc = 0
    for g in vals: g["curva"] = "A" if acc / tot < .80 else "B" if acc / tot < .95 else "C"; acc += g["frota"]
    for g in out: g.setdefault("curva", "sem")
    out.sort(key=lambda g: (-g["frota"], g["codigo"]))
    _CACHE.update(k=key, v=out)
    return out

def _has(t):
    try: q(f"SELECT 1 FROM {t} LIMIT 1"); return True
    except Exception: return False

DES_F = ("curva", "origem", "lancamento")
def desenvolvimento(f=None, page=1, size=200):
    f = f or {}; rows = _des_rows(); term = (f.get("q") or "").upper().split()
    def ok(r, skip=""):
        if skip != "curva" and f.get("curva") and r["curva"] != f["curva"]: return False
        if skip != "origem" and f.get("origem") and r["origem"] != f["origem"]: return False
        if skip != "lancamento" and f.get("lancamento") and not r["lancamento"]: return False
        return all(t in f"{r['codigo']} {r['descricao'] or ''} {' '.join(r['aplicacoes'])} {' '.join(r['concorrentes'])} {r['fornecedor'] or ''}".upper() for t in term)
    sel = [r for r in rows if ok(r)]
    counts = {"curva": dict(Counter(r["curva"] for r in rows if ok(r, "curva")).most_common()), "origem": dict(Counter(r["origem"] for r in rows if ok(r, "origem")).most_common()),
              "lancamento": sum(1 for r in rows if r["lancamento"] and ok(r, "lancamento"))}
    page = max(int(page or 1), 1); n = 10**9 if f.get("all") else size
    return {"total": len(sel), "rows": sel[(page - 1) * n: page * n], "page": page, "size": n, "counts": counts,
            "kpis": {"itens": len(sel), "com_frota": sum(1 for r in sel if r["frota"] > 0), "frota": sum(r["frota"] for r in sel), "ano": datetime.date.today().year,
                     "fraga": _has("fraga_veiculos") and bool(q("SELECT 1 FROM fraga_veiculos LIMIT 1"))}}
