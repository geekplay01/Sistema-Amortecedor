"""Anomalias do cadastro (etapa 16 · D1/D2) — tela «Anomalias» (antiga Equivalências, que virou uma das abas).
  • Família: catálogo × certificados Inmetro. O CatalogoAMD prevalece (a importação do Inmetro só preenche família vazia); aqui aparecem os produtos
    com algum certificado de família diferente. Calculado dos dados (products × certificates), não das pendências.
  • EAN: conflitos abertos de EAN (o certificado não guarda o EAN; o conflito guarda os dois valores). Continuam em Pendências («Usar o da planilha»)."""
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

def counts(q=""):
    return {"familia": len(familia(q)), "ean": len(ean(q)), "sugestoes": Q.q1("SELECT COUNT(*) n FROM equivalence_suggestions WHERE status='pendente'")["n"]}

def export_xlsx(q=""):
    """Excel com as duas abas (Família e EAN), filtradas pela busca."""
    import exporter
    wb = exporter.Workbook(); wb.remove(wb.active); f = familia(q); e = ean(q)
    exporter._sheet(wb, "Família", ["Código PERFECT", "Descrição", "Família no catálogo", "Famílias no Inmetro", "Certificados (nº · fornecedor · família)"],
                    [[r["perfect_code"], r["description"], r["family"], " / ".join(r["inmetro_families"]), "; ".join(f"{c['number']} · {c['supplier'] or '-'} · {c['family']}" for c in r["certificates"])] for r in f])
    exporter._sheet(wb, "EAN", ["Código PERFECT", "Descrição", "EAN no catálogo", "EAN importado", "Fonte"], [[r["perfect_code"], r["description"], r["current"], r["imported"], r["source"]] for r in e])
    bio = io.BytesIO(); wb.save(bio); bio.seek(0); return bio, len(f) + len(e)
