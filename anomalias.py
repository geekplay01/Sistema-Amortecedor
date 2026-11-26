"""Anomalias do cadastro (etapa 16 · D1/D2) — tela «Anomalias» (antiga Equivalências, que virou uma das abas).
  • Família: catálogo × certificados Inmetro. O CatalogoAMD prevalece (a importação do Inmetro só preenche família vazia); aqui aparecem os produtos
    com algum certificado de família diferente. Calculado dos dados (products × certificates), não das pendências.
  • EAN: conflitos abertos de EAN (o certificado não guarda o EAN; o conflito guarda os dois valores). Continuam em Pendências («Usar o da planilha»).
  • Peso e EAN × BI03 (etapa 17): o Protheus prevalece; lista onde a planilha do catálogo diverge.
  • Pendente cadastro Protheus (etapa 17): DES/R-D em andamento que não estão no BI03 como PA.
  • Cross × servidor e Concorrentes repetidos (etapa 17): ver concorrentes.py."""
import io
import queries as Q

def _match(q, *txt):
    t = " ".join(str(x or "") for x in txt).upper(); return all(w in t for w in (q or "").upper().split())

def familia(q=""):
    rows = Q.q("""SELECT p.id product_id,p.perfect_code,p.description,p.family,k.family inmetro,k.inmetro_number,k.supplier
                  FROM products p JOIN certificates k ON k.product_id=p.id
                  WHERE k.family IS NOT NULL AND p.family IS NOT NULL ORDER BY p.perfect_code,k.inmetro_number""")
    by = {}
    for r in rows:
        g = by.setdefault(r["product_id"], {"product_id": r["product_id"], "perfect_code": r["perfect_code"], "description": r["description"], "family": r["family"], "certificates": []})
        g["certificates"].append({"family": r["inmetro"].upper(), "number": r["inmetro_number"], "supplier": r["supplier"]})
    out = []
    for g in by.values():
        fams = sorted({c["family"] for c in g["certificates"]})
        if any(f != (g["family"] or "").upper() for f in fams) and _match(q, g["perfect_code"], g["description"], g["family"], *fams):
            out.append({**g, "inmetro_families": fams, "mixed": len(fams) > 1})
    return out

def ean(q=""):
    out = []
    for r in Q.q("""SELECT x.id,x.description d,x.created_at,p.id product_id,p.perfect_code,p.description FROM pendencies x JOIN products p ON p.id=x.product_id
                    WHERE x.kind='conflito' AND x.field='ean' AND x.status='aberta' ORDER BY p.perfect_code"""):
        v = Q.conflict_values(r["d"]) or (None, None)
        src = r["d"].split("(fonte ", 1)[1].split(")", 1)[0] if "(fonte " in (r["d"] or "") else None
        if _match(q, r["perfect_code"], r["description"], *v):
            out.append({"id": r["id"], "product_id": r["product_id"], "perfect_code": r["perfect_code"], "description": r["description"], "current": v[0], "imported": v[1], "source": src, "created_at": r["created_at"]})
    return out

def pesoean(q=""):
    """Etapa 17 · Q15: o BI03 (Protheus) prevalece no peso líquido e no código de barras; aqui ficam os itens do catálogo em que a planilha CatalogoAMD
    diz outra coisa (os dois preenchidos e diferentes) — para corrigir a planilha. Uma linha por campo divergente."""
    import bi03
    if not bi03.available(): return []
    out = []
    for r in Q.q("""SELECT p.id product_id,p.perfect_code,p.description,p.cat_weight_kg,p.cat_ean,b.peso,b.ean FROM products p JOIN bi03 b ON b.code=p.perfect_code
                    WHERE p.catalog_position IS NOT NULL ORDER BY p.catalog_position"""):
        base = {"product_id": r["product_id"], "perfect_code": r["perfect_code"], "description": r["description"]}
        if r["cat_weight_kg"] is not None and r["peso"] is not None and abs(r["cat_weight_kg"] - r["peso"]) > 0.0005: out.append({**base, "campo": "Peso líquido (kg)", "catalogo": r["cat_weight_kg"], "bi03": r["peso"]})
        if r["cat_ean"] and r["ean"] and str(r["cat_ean"]).strip() != r["ean"]: out.append({**base, "campo": "Código de barras", "catalogo": r["cat_ean"], "bi03": r["ean"]})
    return [x for x in out if _match(q, x["perfect_code"], x["description"], x["catalogo"], x["bi03"])]

PROT_FILTROS = ("tipo", "status")
def protheus(q="", f=None, skip=""):
    """Etapa 17 · Q30: «Pendente cadastro Protheus» — códigos de DES/R-D em andamento (universo amortecedor, não bloqueado; nenhuma aplicação em ITEM RECEBIDO,
    sem cancelado) que não estão no BI03 como amortecedor acabado (PA). Sem BI03 carregado a lista fica vazia (senão tudo pareceria pendente).
    `f`: tipo (DESENVOLVIMENTO/REDESENVOLVIMENTO) e status; `skip` ignora um filtro (contagem dos atalhos)."""
    import bi03, rules, data_pipeline as dp
    if not bi03.available(): return []
    f = f or {}; rank = dp.STATUS_RANK; by = {}
    for r in Q.q(f"""SELECT r.code,r.suggestion,r.status,r.supplier,r.make,r.vehicle,r.application_text,r.year_from,r.year_to FROM rd_projects r
                     WHERE {rules.desc_sql('r.description')} AND upper(r.code) NOT IN (SELECT code FROM bi03)
                       AND upper(r.code) NOT IN (SELECT upper(code) FROM rd_projects GROUP BY upper(code) HAVING MAX(upper(coalesce(status,''))='ITEM RECEBIDO')=1 OR MAX(upper(coalesce(status,'')) LIKE 'CANCEL%')=1)
                     ORDER BY r.code"""):
        g = by.setdefault((r["code"].upper(), r["suggestion"]), {"code": r["code"].upper(), "tipo": r["suggestion"], "status": r["status"], "supplier": r["supplier"], "apps": []})
        if rank.get(r["status"] or "", -1) > rank.get(g["status"] or "", -1): g["status"] = r["status"]
        if not g["supplier"]: g["supplier"] = r["supplier"]
        g["apps"].append(" ".join(str(x) for x in (r["make"], r["vehicle"], r["application_text"]) if x))
    out = []
    for g in by.values():
        g["application"] = " · ".join(dict.fromkeys(a for a in g.pop("apps") if a))[:300]
        if "tipo" != skip and f.get("tipo") and g["tipo"] != f["tipo"]: continue
        if "status" != skip and f.get("status") and g["status"] != f["status"]: continue
        if _match(q, g["code"], g["supplier"], g["application"], g["status"]): out.append(g)
    return out

def protheus_counts(q="", f=None):
    """Atalhos da aba: cada contagem = total da lista ao clicar (ignora o próprio filtro, respeita os outros)."""
    from collections import Counter
    return {k: dict(Counter(r[k] for r in protheus(q, f, skip=k))) for k in PROT_FILTROS}

def cross(q=""):
    import concorrentes; return concorrentes.cross_x_servidor(q)
def repetidos(q=""):
    import concorrentes; return concorrentes.repetidos(q)

def corrigido(q=""):
    """Etapa 19 · Q7: «Nosso código» corrigido na tela Cobertura — levar ao CrossCatalogo.xlsx."""
    import cobertura; return cobertura.correcoes(q)

TABS = {"familia": familia, "ean": ean, "pesoean": pesoean, "cross": cross, "repetidos": repetidos, "corrigido": corrigido}

# ---- dados do item em todas as abas (etapa 24 · update 4 · Q7): descrição e aplicação de cada código PERFECT ----
_MAX_APP = 240
def itens(codes):
    """{CÓDIGO: {description, application}}: do catálogo (products + applications); o código que não está no catálogo vem do DES/R-D (rd_projects).
    Aplicação no padrão das planilhas (MONTADORA - MODELO - DIANT. LD/LE - 2021/2025), sem repetir, cortada em ~240 caracteres."""
    codes = sorted({str(c).strip().upper() for c in codes if c and str(c).strip()})
    out = {}
    for i in range(0, len(codes), 900):
        parte = codes[i:i + 900]; ph = ",".join("?" * len(parte))
        for r in Q.q(f"""SELECT upper(p.perfect_code) code, p.description, a.make, a.model, a.application_text, a.axle, a.side, a.year_from, a.year_to
                         FROM products p LEFT JOIN applications a ON a.product_id=p.id WHERE upper(p.perfect_code) IN ({ph}) ORDER BY p.perfect_code, a.make, a.model, a.year_from""", parte):
            g = out.setdefault(r["code"], {"description": r["description"], "apps": []})
            if r["make"] or r["model"] or r["application_text"]:
                g["apps"].append(Q._app_text(r["make"], r["model"], r["application_text"], r["axle"], r["side"], r["year_from"], r["year_to"]))
        falta = [c for c in parte if c not in out or not out[c]["apps"] or not out[c]["description"]]
        if falta:
            ph = ",".join("?" * len(falta))
            for r in Q.q(f"""SELECT upper(code) code, description, make, vehicle, application_text, year_from, year_to FROM rd_projects
                             WHERE upper(code) IN ({ph}) ORDER BY CASE suggestion WHEN 'DESENVOLVIMENTO' THEN 0 ELSE 1 END, id""", falta):
                g = out.setdefault(r["code"], {"description": None, "apps": [], "rd": True})
                if not g["description"]: g["description"] = r["description"]
                if g.get("rd") or not g["apps"]:
                    g["rd"] = True; g["apps"].append(Q._app_text(r["make"], r["vehicle"], r["application_text"], None, None, r["year_from"], r["year_to"]))
    res = {}
    for c, g in out.items():
        t = " · ".join(dict.fromkeys(a for a in g["apps"] if a))
        res[c] = {"description": g["description"], "application": (t[:_MAX_APP - 1] + "…") if len(t) > _MAX_APP else t}
    return res

def _codigos(txt): return [c.strip() for c in str(txt or "").split(",") if c.strip() and not c.strip().startswith("(") and c.strip() != "—"]

def com_itens(tab, rows):
    """Acrescenta descrição e aplicação às linhas da aba (na tela e no Excel). Abas de um código: `description`/`application`;
    Concorrentes repetidos e Cross corrigido (vários códigos): `itens` = [{code, description, application}]."""
    if tab == "repetidos": chaves = [c for r in rows for c in r["codigos"]]
    elif tab == "corrigido": chaves = [c for r in rows for c in _codigos(r["depois"])]
    else: chaves = [r.get("perfect_code") or r.get("code") for r in rows]
    I = itens(chaves); vazio = {"description": None, "application": ""}
    for r in rows:
        if tab in ("repetidos", "corrigido"):
            cs = r["codigos"] if tab == "repetidos" else _codigos(r["depois"])
            r["itens"] = [{"code": c, **I.get(c.upper(), vazio)} for c in cs]
        else:
            i = I.get(str(r.get("perfect_code") or r.get("code") or "").upper(), vazio)
            if not r.get("description"): r["description"] = i["description"]
            if not r.get("application"): r["application"] = i["application"]
    return rows

def _itens_txt(r, k): return "\n".join(f"{i['code']}: {i[k] or '-'}" for i in r.get("itens") or [])

def counts(q=""):
    return {"familia": len(familia(q)), "ean": len(ean(q)), "pesoean": len(pesoean(q)), "protheus": len(protheus(q)), "cross": len(cross(q)), "repetidos": len(repetidos(q)), "corrigido": len(corrigido(q)),
            "sugestoes": Q.q1("SELECT COUNT(*) n FROM equivalence_suggestions WHERE status='pendente'")["n"]}

def export_xlsx(q=""):
    """Excel com as abas Família, EAN, Peso e EAN × BI03 e Pendente cadastro Protheus, filtradas pela busca."""
    import exporter
    wb = exporter.Workbook(); wb.remove(wb.active)
    f, e, pe, pr = com_itens("familia", familia(q)), com_itens("ean", ean(q)), com_itens("pesoean", pesoean(q)), com_itens("protheus", protheus(q))
    exporter._sheet(wb, "Família", ["Código PERFECT", "Descrição", "Aplicação", "Família no catálogo", "Famílias no Inmetro", "Certificados (nº · fornecedor · família)"],
                    [[r["perfect_code"], r["description"], r["application"], r["family"], " / ".join(r["inmetro_families"]), "; ".join(f"{c['number']} · {c['supplier'] or '-'} · {c['family']}" for c in r["certificates"])] for r in f])
    exporter._sheet(wb, "EAN", ["Código PERFECT", "Descrição", "Aplicação", "EAN no catálogo", "EAN importado", "Fonte"], [[r["perfect_code"], r["description"], r["application"], r["current"], r["imported"], r["source"]] for r in e])
    exporter._sheet(wb, "Peso e EAN × BI03", ["Código PERFECT", "Descrição", "Aplicação", "Campo", "No CatalogoAMD", "No BI03 (Protheus, vale este)"], [[r["perfect_code"], r["description"], r["application"], r["campo"], r["catalogo"], r["bi03"]] for r in pe])
    exporter._sheet(wb, "Pendente cadastro Protheus", ["Código", "Descrição", "Tipo", "Status", "Fornecedor", "Aplicação", "Situação"], [[r["code"], r["description"], r["tipo"], r["status"], r["supplier"], r["application"], "Pendente cadastro Protheus"] for r in pr])
    cx, rp = com_itens("cross", cross(q)), com_itens("repetidos", repetidos(q))
    exporter._sheet(wb, "Cross × servidor", ["Código PERFECT", "Descrição", "Aplicação", "Concorrente", "No CrossCatalogo", "No servidor"], [[r["perfect_code"], r["description"], r["application"], r["concorrente"], " / ".join(r["cross"]), " / ".join(r["servidor"])] for r in cx])
    exporter._sheet(wb, "Concorrentes repetidos", ["Caso", "Concorrente", "Referência(s)", "Código(s) PERFECT", "Descrição", "Aplicação"],
                    [["Mesma referência em vários códigos" if r["grupo"] == "ref_em_varios" else "Várias referências no mesmo código", r["concorrente"], " / ".join(r["referencias"]), " / ".join(r["codigos"]),
                      _itens_txt(r, "description"), _itens_txt(r, "application")] for r in rp])
    co = com_itens("corrigido", corrigido(q))
    exporter._sheet(wb, "Cross corrigido no app", ["Concorrente", "Referência", "Antes", "Depois (vale no app)", "Descrição (depois)", "Aplicação (depois)", "Quando"],
                    [[r["concorrente"], r["referencia"], r["antes"], r["depois"], _itens_txt(r, "description"), _itens_txt(r, "application"), r["em"]] for r in co])
    bio = io.BytesIO(); wb.save(bio); bio.seek(0); return bio, len(f) + len(e) + len(pe) + len(pr) + len(cx) + len(rp) + len(co)
