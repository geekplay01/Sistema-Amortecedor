"""Módulos «Desenvolvimento» e «Redesenvolvimento». Fonte oficial: SQL Server (DESENVOLVIMENTO_PRODUTOS) via data_pipeline.
Item = código distinto dentro do tipo. Um código pode ter várias linhas (aplicações). Cada linha vale pelo tipo do servidor (SUGESTAO): o código que tem
linhas DES e R-D aparece nas duas listas, cada uma com as próprias linhas (etapa 19 · Q2; antes o R-D prevalecia e escondia o DES ativo).
Etapa 20 · Q2/Q4: a tela abre «em andamento» (status=andamento: aplicações que ainda não são ITEM RECEBIDO); o recebido aparece no estágio ITEM RECEBIDO.
Filtro `sub=<chave>:<valor>` = aplicações com aquele sub status do servidor (statuses.SUBS; valor composto vale como cada parte)."""
import re
from queries import q, q1

import kinds, statuses, rules
KINDS = dict(kinds.SLUG)          # {"des": "DESENVOLVIMENTO", "rd": "REDESENVOLVIMENTO"}
ANDAMENTO, RECEBIDO = "andamento", "ITEM RECEBIDO"
NAO_RECEBIDA = f"upper(trim(coalesce(r.status,'')))<>'{RECEBIDO}'"

def _stage(st, p):
    """Condição do estágio: «andamento» (não recebidas), um STATUS exato ou nada (todas)."""
    if st == ANDAMENTO: return NAO_RECEBIDA
    if st: p["status"] = st; return "r.status=:status"
    return None

def _where(kind, f):
    w, p = ["r.suggestion=:kind", rules.desc_sql("r.description")], {"kind": kind}
    st = _stage(f.get("status") or "", p)
    if st: w.append(st)
    sk, _, sv = (f.get("sub") or "").partition(":")
    if sk in statuses.SUB_COL and sv.strip():
        w.append(f"{statuses.sub_has('r.' + statuses.SUB_COL[sk])} LIKE :subv"); p["subv"] = f"%/{sv.strip().upper()}/%"
    for i, t in enumerate((f.get("q") or "").split()):
        k = re.sub(r"[^A-Z0-9]", "", t.upper())        # referência de concorrente/OEM do servidor (DESENVOLVIMENTO_CONCORRENTES), com ou sem pontuação
        ref = f" OR upper(r.code) IN (SELECT code FROM concorrentes WHERE ref_key LIKE :t{i}k)" if len(k) >= 3 else ""
        w.append(f"(r.code LIKE :t{i} OR r.description LIKE :t{i} OR r.make LIKE :t{i} OR r.vehicle LIKE :t{i} OR r.application_text LIKE :t{i} OR r.supplier LIKE :t{i}{ref})"); p[f"t{i}"] = f"%{t}%"
        if ref: p[f"t{i}k"] = f"%{k}%"
    if f.get("make"): w.append("upper(trim(r.make))=upper(trim(:make))"); p["make"] = f["make"]
    if f.get("model"): w.append("upper(trim(r.vehicle))=upper(trim(:model))"); p["model"] = f["model"]
    if (f.get("year") or "").isdigit(): w.append("r.year_from<=:year AND coalesce(r.year_to,9999)>=:year"); p["year"] = int(f["year"])
    if f.get("supplier"): w.append("r.supplier=:supplier"); p["supplier"] = f["supplier"]
    fl = f.get("flag")
    if fl in FLAGS: w.append(f"r.code IN (SELECT code FROM v_rd_flags WHERE suggestion=:kind AND {fl}=1)")
    elif fl == "nenhum": w.append(f"r.code IN (SELECT code FROM v_rd_flags WHERE suggestion=:kind AND NOT ({statuses.ANY_SQL}))")
    elif (fl or "").startswith("grupo_"):
        ks = [k for k in statuses.KEYS if statuses.GROUP[k] == fl[6:]]
        if ks: w.append("r.code IN (SELECT code FROM v_rd_flags WHERE suggestion=:kind AND (" + " OR ".join(ks) + "))")
    if f.get("catalog") == "sim": w.append("r.product_id IS NOT NULL")
    if f.get("catalog") == "nao": w.append("r.product_id IS NULL")
    s = f.get("sample")
    if s == "comprada": w.append("r.sample_bought IS NOT NULL")
    elif s == "enviada": w.append("r.sample_sent IS NOT NULL")
    elif s == "nenhuma": w.append("r.sample_bought IS NULL AND r.sample_sent IS NULL")
    cu = CURTIU.get(f.get("curtiu") or "")           # curtidas valem por ITEM (maior valor entre as aplicações do código)
    if cu: w.append(f"r.code IN (SELECT code FROM rd_projects WHERE suggestion=:kind GROUP BY code HAVING {cu})")
    return " AND ".join(w), p

CURTIU = {"sim": "MAX(coalesce(curtiu,0))>0", "sem": "MAX(coalesce(curtiu,0))=0", "nao": "MAX(coalesce(nao_curtiu,0))>0"}

def _rank_sql():
    """Posição do status no ciclo (PENDENTE … ITEM RECEBIDO); o item vale pelo status mais avançado entre as aplicações."""
    from data_pipeline import STATUS_RANK
    return "MAX(CASE r.status " + " ".join(f"WHEN '{k}' THEN {v}" for k, v in STATUS_RANK.items()) + " ELSE -1 END)"

def _order(f):
    """Ordem da lista. Padrão (etapa 16): mais curtidos primeiro; empate → status mais avançado; depois o código."""
    o = f.get("ordem") or "curtidas"
    if o == "codigo": return "r.code"
    if o == "status": return f"{_rank_sql()} DESC, r.code"
    return f"MAX(coalesce(r.curtiu,0)) DESC, {_rank_sql()} DESC, r.code"

FLAGS = dict(statuses.LABEL)

def _j(v): return (v or "").replace(",", " · ")

def items(kind, f):
    w, p = _where(kind, f)
    size = 10**9 if f.get("all") else 50; off = 0 if f.get("all") else (max(int(f.get("page") or 1), 1) - 1) * size
    total = q1(f"SELECT COUNT(DISTINCT r.code) n FROM rd_projects r WHERE {w}", p)["n"]
    subs = ",".join(f"group_concat(DISTINCT r.{c}) s_{k}" for k, c, _ in statuses.SUBS)          # «,» entre aplicações vira «/» abaixo
    rows = q(f"""SELECT r.code,MAX(r.description) description,MAX(r.product_id) product_id,COUNT(*) n_rows,group_concat(DISTINCT r.make) makes,group_concat(DISTINCT r.vehicle) vehicles,
        group_concat(DISTINCT r.status) statuses,group_concat(DISTINCT r.supplier) suppliers,{subs},
        MAX(substr(r.sample_bought,1,10)) bought,MAX(substr(r.sample_sent,1,10)) sent,MAX(r.curtiu) curtiu,MAX(r.nao_curtiu) nao_curtiu
        FROM rd_projects r WHERE {w} GROUP BY r.code ORDER BY {_order(f)} LIMIT {size} OFFSET {off}""", p)
    for r in rows:
        for k in ("makes", "vehicles", "statuses", "suppliers"): r[k] = _j(r[k])
        r["subs"] = [{"k": k, "l": lab, "v": v} for k, _, lab in statuses.SUBS for v in dict.fromkeys(statuses.split_sub((r.pop("s_" + k) or "").replace(",", "/")))]
    return {"total": total, "rows": rows, "size": size, "kind": KINDS.get(kind, kind)}

def _sub_counts(kind, st):
    """Sub status do servidor no estágio `st`, por coluna: [{key, label, values: [{v, n (itens), l (aplicações)}]}] — um valor composto conta em cada parte."""
    p = {"kind": kind}; c = _stage(st, p)
    cols = ",".join(f"r.{col}" for _, col, _ in statuses.SUBS)
    rows = q(f"SELECT r.code,{cols} FROM rd_projects r WHERE r.suggestion=:kind AND {rules.desc_sql('r.description')}{' AND ' + c if c else ''}", p)
    out = []
    for k, col, lab in statuses.SUBS:
        acc = {}
        for r in rows:
            for v in dict.fromkeys(statuses.split_sub(r[col])):
                a = acc.setdefault(v, [set(), 0]); a[0].add(r["code"]); a[1] += 1
        out.append({"key": k, "label": lab, "values": sorted(({"v": v, "n": len(a[0]), "l": a[1]} for v, a in acc.items()), key=lambda x: (-x["n"], x["v"]))})
    return out

def facets(kind, status=None):
    """Contadores da tela. `status` = estágio escolhido (padrão «andamento»): o quadro de sub status e o `etapa` contam só nele.
    `status`, `total`, `curtidos` e `flags` valem para todas as aplicações (o Dashboard usa estes)."""
    st = ANDAMENTO if status is None else status
    g = lambda col: q(f"SELECT {col} v,COUNT(DISTINCT code) n FROM rd_projects WHERE {rules.desc_sql()} AND suggestion=? AND {col} IS NOT NULL AND trim({col})<>'' GROUP BY {col} ORDER BY n DESC", (kind,))
    base = "suggestion=? AND " + rules.desc_sql()
    tot = q1("SELECT COUNT(DISTINCT code) n,COUNT(*) l FROM rd_projects WHERE " + base, (kind,))
    cur = q1(f"SELECT SUM(cu>0) curtidos,SUM(nc>0) nao_curtidos FROM (SELECT MAX(coalesce(curtiu,0)) cu,MAX(coalesce(nao_curtiu,0)) nc FROM rd_projects WHERE {base} GROUP BY code)", (kind,))
    est = q(f"SELECT r.status v,COUNT(DISTINCT r.code) n,COUNT(*) l FROM rd_projects r WHERE r.suggestion=? AND {rules.desc_sql('r.description')} AND trim(coalesce(r.status,''))<>'' GROUP BY r.status", (kind,))
    def resumo(s):
        p = {"kind": kind}; c = _stage(s, p)
        x = q1(f"""SELECT COUNT(*) n,SUM(l) l,SUM(cu>0) curtidos,SUM(nc>0) nao_curtidos FROM (SELECT COUNT(*) l,MAX(coalesce(r.curtiu,0)) cu,MAX(coalesce(r.nao_curtiu,0)) nc
                   FROM rd_projects r WHERE r.suggestion=:kind AND {rules.desc_sql('r.description')}{' AND ' + c if c else ''} GROUP BY r.code)""", p)
        return {k: x[k] or 0 for k in ("n", "l", "curtidos", "nao_curtidos")}
    return {"status": g("status"), "supplier": g("supplier"), "total": tot["n"], "lines": tot["l"], "flags": flag_counts(kind),
            "curtidos": cur["curtidos"] or 0, "nao_curtidos": cur["nao_curtidos"] or 0,
            "esteira": est, "andamento": resumo(ANDAMENTO), "estagio": st, "etapa": resumo(st), "subs": _sub_counts(kind, st)}

def _cross(pid, code):
    import purchases, queries
    cs = [{"brand": c["brand"], "code": c["code"]} for c in queries.cross_for(pid)] if pid else []
    return purchases._sort_cross(cs or purchases.rd_cross_index().get(code, []))

def _info(kind, code):
    """Todas as informações da planilha de Desenvolvimento para o item (marca, sub status do projeto, usuários, datas, IPI, Inmetro...)."""
    import json
    rows = q("SELECT brand,project_substatus,extra FROM rd_projects WHERE code=? AND suggestion=?", (code, kind)); out = {}
    for r in rows:
        if r["brand"] and "MARCA" not in out: out["MARCA"] = r["brand"]
        if r["project_substatus"] and "SUB STATUS PROJETO / INVOICE" not in out: out["SUB STATUS PROJETO / INVOICE"] = r["project_substatus"]
        try: d = json.loads(r["extra"]) if r["extra"] else {}
        except ValueError: d = {}
        for k, v in d.items(): out.setdefault(k, v)
    return out

def flag_counts(kind):
    sums = ",".join(f"SUM({k}) {k}" for k in statuses.KEYS)
    t = q1(f"SELECT COUNT(*) n,{sums},SUM(NOT ({statuses.ANY_SQL})) ok FROM v_rd_flags WHERE suggestion=?", (kind,))
    out = {k: t[k] or 0 for k in statuses.KEYS}; out["nenhum"] = t["ok"] or 0; return out

def detail(kind, code):
    cols = ",".join(f"{c} s_{k}" for k, c, _ in statuses.SUBS)
    rows = q(f"SELECT make,vehicle,application_text,year_from,year_to,status,{cols},supplier,substr(sample_bought,1,10) bought,substr(sample_sent,1,10) sent,description,product_id,curtiu,nao_curtiu FROM rd_projects WHERE code=? AND suggestion=? ORDER BY make,vehicle,year_from", (code, kind))
    if not rows: return None
    for r in rows: r["subs"] = [{"k": k, "l": lab, "v": v} for k, _, lab in statuses.SUBS for v in statuses.split_sub(r.pop("s_" + k))]
    pid = max([r["product_id"] for r in rows if r["product_id"]] or [0])
    return {"code": code, "kind": kind, "description": next((r["description"] for r in rows if r["description"]), None), "rows": rows,
            "other": q("SELECT suggestion,COUNT(*) n FROM rd_projects WHERE code=? AND suggestion<>? GROUP BY suggestion", (code, kind)),
            "product": q1("SELECT id,perfect_code,description FROM products WHERE id=?", (pid,)) if pid else None,
            "samples": q("SELECT id,sc_number,sample_code,supplier,stage FROM sample_orders WHERE perfect_code=? OR sample_code=?", (code, code)),
            "damping": q("SELECT id,test_date FROM damping_tests WHERE perfect_code=?", (code,)),
            "cross": _cross(pid, code), "info": _info(kind, code), "validations": __import__("goals").validations_of(code, kind),
            "curtiu": max([r["curtiu"] or 0 for r in rows] or [0]), "nao_curtiu": max([r["nao_curtiu"] or 0 for r in rows] or [0])}

def filter_lists(make=None):
    mk = [r["m"] for r in q("SELECT DISTINCT upper(trim(make)) m FROM (SELECT make FROM applications UNION ALL SELECT make FROM rd_projects) WHERE make IS NOT NULL AND trim(make)<>'' ORDER BY m")]
    a = {"mk": make} if make else {}
    mw = "AND upper(trim(make))=upper(:mk)" if make else ""
    models = [r["m"] for r in q(f"SELECT DISTINCT upper(trim(m)) m FROM (SELECT make,model m FROM applications UNION ALL SELECT make,vehicle FROM rd_projects) WHERE m IS NOT NULL AND trim(m)<>'' {mw} ORDER BY m", a)]
    y = q1("SELECT MIN(y1) a,MAX(y2) b FROM (SELECT year_from y1,coalesce(year_to,year_from) y2 FROM applications UNION ALL SELECT year_from,coalesce(year_to,year_from) FROM rd_projects) WHERE y1>=1950 AND y2<=2040")
    return {"makes": mk, "models": models, "years": list(range(y["b"], y["a"] - 1, -1)) if y and y["a"] else []}

def quick(term, limit=5):
    like = f"%{term.strip()}%"
    prods = q("""SELECT DISTINCT p.perfect_code code,p.description FROM products p LEFT JOIN codes k ON k.product_id=p.id LEFT JOIN applications a ON a.product_id=p.id
        WHERE p.perfect_code LIKE ?1 OR p.description LIKE ?1 OR k.code LIKE ?1 OR (?3<>'' AND replace(replace(replace(replace(upper(k.code),'-',''),'.',''),'/',''),' ','') LIKE ?3) OR a.make LIKE ?1 OR a.model LIKE ?1 ORDER BY p.catalog_position LIMIT ?2""", (like, limit, "%" + re.sub(r'[^A-Z0-9]', '', term.upper()) + "%" if len(re.sub(r'[^A-Za-z0-9]', '', term)) >= 3 else ""))
    out = [{"kind": "Catálogo", "code": r["code"], "text": r["description"], "url": "/pesquisa?q=" + r["code"]} for r in prods]
    for k, label, slug in ((kinds.DES, kinds.DES, "desenvolvimento"), (kinds.RD, kinds.RD, "redesenvolvimento")):
        rs = q(f"""SELECT code,MAX(description) d,MAX(vehicle) v,MAX(status) s FROM rd_projects WHERE suggestion=?1 AND {rules.desc_sql()} AND (code LIKE ?2 OR description LIKE ?2 OR vehicle LIKE ?2 OR make LIKE ?2 OR application_text LIKE ?2)
            GROUP BY code ORDER BY code LIMIT ?3""", (k, like, limit))
        out += [{"kind": label, "code": r["code"], "text": " · ".join(x for x in (r["d"], r["v"], r["s"]) if x), "url": f"/{slug}?q=" + r["code"]} for r in rs]
    return out
