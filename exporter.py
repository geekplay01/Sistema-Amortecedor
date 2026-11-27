"""Exportação XLSX de todos os módulos (sempre TODAS as linhas do filtro atual, não só a página)."""
import io, datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
import queries as Q, equivalence, damping, database as db

def _sheet(wb, title, head, rows, widths=None):
    ws = wb.create_sheet(title[:31]); ws.append(head)
    for r in rows: ws.append(["" if v is None else v for v in r])
    for c in ws[1]: c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="243242"); c.alignment = Alignment(vertical="center", wrap_text=True)
    for i in range(1, len(head) + 1): ws.column_dimensions[get_column_letter(i)].width = (widths or [])[i - 1] if widths and i <= len(widths) else 18
    ws.freeze_panes = "A2"
    if rows: ws.auto_filter.ref = ws.dimensions
    return ws

def _finish(wb, filtros):
    ws = wb.create_sheet("Filtros aplicados")
    for k, v in [("Gerado em", datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))] + [(k, v or "—") for k, v in filtros.items()]: ws.append([k, v])
    ws.column_dimensions["A"].width = 22; ws.column_dimensions["B"].width = 80
    for c in ws["A"]: c.font = Font(bold=True)
    bio = io.BytesIO(); wb.save(bio); bio.seek(0); return bio

def _codes():
    out = {}
    for r in Q.q("SELECT product_id,code_type,group_concat(DISTINCT code) c FROM codes GROUP BY product_id,code_type"): out[(r["product_id"], r["code_type"])] = r["c"].replace(",", "; ")
    return out
from loaders import SYSTEM_LABEL as SYS          # FORCE GAS / FORCE OIL

def _extras():
    """Por produto: famílias dos certificados Inmetro, FOB (menor preço, US$, e fornecedor) e estoque do servidor (disponível e reservado, somando os armazéns). Etapa 16 · D9."""
    import re
    inm, fob, est = {}, {}, {}
    for r in Q.q("SELECT product_id,group_concat(DISTINCT upper(family)) f FROM certificates WHERE family IS NOT NULL AND product_id IS NOT NULL GROUP BY product_id"): inm[r["product_id"]] = "; ".join(sorted(r["f"].split(",")))
    for r in Q.q("SELECT id,fob,fob_supplier FROM products WHERE fob IS NOT NULL"): fob[r["id"]] = (r["fob"], r["fob_supplier"])
    try:
        for r in Q.q("SELECT code,SUM(qty) qty,SUM(reserved) res FROM ds_estoque GROUP BY code"):
            k = re.sub(r"[^A-Z0-9]", "", (r["code"] or "").upper()); a = est.setdefault(k, [0, 0]); a[0] += r["qty"] or 0; a[1] += r["res"] or 0
    except Exception: pass          # sem sincronização ainda: sem estoque
    return inm, fob, est

def _products(a):
    import re
    rows = Q.products({**a, "all": 1})["rows"]; cd = _codes(); inm, fob, est = _extras()
    def e(r): return est.get(re.sub(r"[^A-Z0-9]", "", (r["perfect_code"] or "").upper()), [None, None])
    return [("Produtos", ["Pos. catálogo", "Código PERFECT", "Descrição", "Grupo", "Linha", "Híbrido ou elétrico", "Família", "Família Inmetro", "Sistema", "Ø haste (mm)", "Lançamento", "EAN", "Peso (kg)", "Lmin (mm)", "Lmax (mm)", "Aplicações",
                          "Códigos OEM", "Códigos fornecedor", "Códigos concorrente", "FOB menor (US$)", "Fornecedor do FOB", "Estoque disponível", "Estoque reservado", "Pendências abertas"],
             [[r["catalog_position"], r["perfect_code"], r["description"], r["catalog_group"], r["catalog_line"], HYB.get(r["hybrid"], "Não informado"), r["family"], inm.get(r["id"]), SYS.get(r["system_type"]), r["rod_diameter_mm"], "Sim" if r["is_launch"] == "S" else "", r["ean"], r["weight_kg"], r["lmin_mm"], r["lmax_mm"], r["apps"],
               cd.get((r["id"], "oem")), cd.get((r["id"], "fornecedor")), cd.get((r["id"], "concorrente")), *fob.get(r["id"], (None, None)), *e(r), r["pend"]] for r in rows],
             [11, 16, 38, 18, 24, 12, 16, 22, 12, 11, 11, 16, 10, 10, 10, 11, 30, 30, 30, 12, 14, 12, 12, 11])], len(rows)
HYB = {"S": "Sim", "N": "Não"}

def _pesquisa(a):
    """Pesquisa de amortecedores (etapa 24 · Q1): todos os dados do produto, inclusive caixa e medidas da caixa (C x L x A, mm, da CaixasAMD),
    mais as abas «Aplicações» (uma linha por veículo dos produtos filtrados) e «DES e R-D» (os itens que a busca achou, como na tela)."""
    import re, rd as R
    from loaders import box_base
    o = a.get("origem") or ""; so_rd = o in ("des", "rd")
    rows = [] if so_rd else Q.products({**a, "all": 1})["rows"]; ids = [r["id"] for r in rows]
    cd = _codes(); inm, fob, est = _extras()
    det = {}
    for i in range(0, len(ids), 500):
        ch = ids[i:i + 500]
        for r in Q.q(f"""SELECT p.id,p.package_code,p.ncm,p.description_en,p.description_es,p.inmetro_number,d.stroke_mm,d.body_length_mm,d.tube_diameter_mm,
                          d.upper_mount,d.upper_mount_dims,d.lower_mount,d.lower_mount_dims FROM products p LEFT JOIN dimensions d ON d.product_id=p.id WHERE p.id IN ({','.join('?' * len(ch))})""", ch):
            det[r["id"]] = r
    caixas = {b["code"]: b for b in Q.q("SELECT code,length_mm,width_mm,height_mm,raw_dims FROM packaging_boxes")}
    def medida(cx):
        if not cx: return None
        b = caixas.get(str(cx).strip().upper()) or caixas.get(box_base(cx))
        if not b: return None
        n = lambda v: f"{v:g}" if isinstance(v, (int, float)) else str(v)
        return " x ".join(n(v) for v in (b["length_mm"], b["width_mm"], b["height_mm"])) if b["length_mm"] is not None else b["raw_dims"]
    def e(r): return est.get(re.sub(r"[^A-Z0-9]", "", (r["perfect_code"] or "").upper()), [None, None])
    def fix(t, dims): return " ".join(x for x in (t, f"({dims})" if dims else "") if x) or None
    head = ["Pos. catálogo", "Código PERFECT", "Descrição", "Descrição (inglês)", "Descrição (espanhol)", "Grupo", "Linha", "Híbrido ou elétrico", "Família", "Família Inmetro", "Nº Inmetro", "Sistema",
            "Lmin (mm)", "Lmax (mm)", "Curso (mm)", "Comprimento do corpo (mm)", "Ø haste (mm)", "Ø tubo (mm)", "Fixação superior", "Fixação inferior", "Caixa", "Medidas da caixa (C x L x A, mm)",
            "EAN", "NCM", "Peso (kg)", "Lançamento", "Aplicações", "Códigos OEM", "Códigos fornecedor", "Códigos concorrente", "FOB menor (US$)", "Fornecedor do FOB", "Estoque disponível", "Estoque reservado", "Pendências abertas"]
    data = []
    for r in rows:
        x = det.get(r["id"], {})
        data.append([r["catalog_position"], r["perfect_code"], r["description"], x.get("description_en"), x.get("description_es"), r["catalog_group"], r["catalog_line"], HYB.get(r["hybrid"], "Não informado"), r["family"], inm.get(r["id"]), x.get("inmetro_number"),
                     SYS.get(r["system_type"]), r["lmin_mm"], r["lmax_mm"], x.get("stroke_mm"), x.get("body_length_mm"), r["rod_diameter_mm"], x.get("tube_diameter_mm"), fix(x.get("upper_mount"), x.get("upper_mount_dims")), fix(x.get("lower_mount"), x.get("lower_mount_dims")),
                     x.get("package_code"), medida(x.get("package_code")), r["ean"], x.get("ncm"), r["weight_kg"], "Sim" if r["is_launch"] == "S" else "", r["apps"],
                     cd.get((r["id"], "oem")), cd.get((r["id"], "fornecedor")), cd.get((r["id"], "concorrente")), *fob.get(r["id"], (None, None)), *e(r), r["pend"]])
    sheets = [("Produtos", head, data, [11, 16, 38, 30, 30, 18, 24, 12, 16, 22, 16, 12, 10, 10, 10, 14, 11, 11, 24, 24, 10, 18, 16, 12, 10, 11, 11, 30, 30, 30, 12, 14, 12, 12, 11])]
    apps = []
    for i in range(0, len(ids), 500):
        ch = ids[i:i + 500]
        apps += Q.q(f"""SELECT p.perfect_code,a.make,a.model,a.version,a.application_text,a.year_from,a.year_to,a.axle,a.side FROM applications a JOIN products p ON p.id=a.product_id
                        WHERE a.product_id IN ({','.join('?' * len(ch))})""", ch)
    pos = {r["perfect_code"]: n for n, r in enumerate(rows)}
    apps.sort(key=lambda x: (pos.get(x["perfect_code"], 0), x["make"] or "", x["model"] or "", x["year_from"] or 0))
    sheets.append(("Aplicações", ["Código PERFECT", "Montadora", "Modelo", "Versão", "Aplicação", "Ano inicial", "Ano final", "Eixo", "Lado"],
                   [[x["perfect_code"], x["make"], x["model"], x["version"], x["application_text"], x["year_from"], x["year_to"], x["axle"], x["side"]] for x in apps], [16, 16, 22, 14, 40, 11, 11, 11, 11]))
    want = ["des", "rd"] if o == "" else [] if o == "catalogo" else [o]; f = {k: a[k] for k in ("q", "make", "model", "year") if a.get(k)}
    rdl = []
    if want and (o or f):          # como na tela: sem busca nem veículo, a lista de DES / R-D não aparece
        for k in want:
            for r in R.items("DESENVOLVIMENTO" if k == "des" else "REDESENVOLVIMENTO", {**f, "all": 1})["rows"]:
                rdl.append(["DESENVOLVIMENTO" if k == "des" else "REDESENVOLVIMENTO", r["code"], r["description"], r["makes"], r["vehicles"], r["statuses"], r["suppliers"], "Sim" if r["product_id"] else ""])
    sheets.append(("DES e R-D", ["Tipo", "Código", "Descrição", "Montadoras", "Veículos", "Status", "Fornecedores", "No catálogo"], rdl, [20, 16, 36, 20, 34, 28, 18, 11]))
    return sheets, len(rows) + len(rdl)

def _selecao(a):
    """Etapa 24 · Q2: o que está selecionado na Pesquisa (código buscado; montadora, modelo e ano) para o nome do arquivo."""
    import re
    s = " ".join(str(a[k]).strip() for k in ("q", "code", "make", "model", "year") if a.get(k) and str(a[k]).strip())
    s = re.sub(r'[\\/:*?"<>|]+', " ", s.upper()); s = re.sub(r"\s+", " ", s).strip()
    return s[:60].strip()

def _apps(a):
    rows = Q.applications({**a, "all": 1})["rows"]
    return [("Aplicações", ["Montadora", "Modelo", "Versão", "Aplicação", "Ano inicial", "Ano final", "Eixo", "Lado", "Código PERFECT", "Pos. catálogo"],
             [[r["make"], r["model"], r["version"], r["application_text"], r["year_from"], r["year_to"], r["axle"], r["side"], r["perfect_code"], r["catalog_position"]] for r in rows], [16, 22, 14, 38, 11, 11, 11, 11, 16, 11])], len(rows)

def _compare(a):
    import re
    ps = Q.compare([int(i) for i in re.findall(r"\d+", a.get("ids", ""))])
    F = [("Posição no catálogo", lambda p: p["catalog_position"]), ("Descrição", lambda p: p["description"]), ("Grupo", lambda p: p["catalog_group"]), ("Família", lambda p: p["family"]), ("Sistema", lambda p: SYS.get(p["system_type"])),
         ("Lmin (mm)", lambda p: (p["dimensions"] or {}).get("lmin_mm")), ("Lmax (mm)", lambda p: (p["dimensions"] or {}).get("lmax_mm")), ("Ø haste (mm)", lambda p: (p["dimensions"] or {}).get("rod_diameter_mm")),
         ("Ø tubo (mm)", lambda p: (p["dimensions"] or {}).get("tube_diameter_mm")), ("Peso (kg)", lambda p: p["weight_kg"]), ("EAN", lambda p: p["ean"]), ("Caixa", lambda p: p["package_code"]),
         ("Códigos OEM", lambda p: "; ".join(c["code"] for c in p["codes"] if c["code_type"] == "oem")), ("Códigos fornecedor", lambda p: "; ".join(sorted({c["code"] for c in p["codes"] if c["code_type"] == "fornecedor"}))),
         ("Aplicações", lambda p: "; ".join(f"{x['make'] or ''} {x['model'] or ''} {x['year_from'] or ''}-{x['year_to'] or ''}".strip() for x in p["applications"])),
         ("Nº Inmetro", lambda p: "; ".join(sorted({c["inmetro_number"] for c in p["certificates"] if c["inmetro_number"]}))),
         ("Fontes", lambda p: "; ".join(sorted({x["source"] for x in p["codes"] + p["applications"] if x["source"]})))]
    rows = []
    for l, fn in F:
        v = [fn(p) for p in ps]; rows.append([l] + v + ["SIM" if len({str(x or "") for x in v}) > 1 and len(ps) > 1 else ""])
    return [("Comparação", ["Campo"] + [p["perfect_code"] for p in ps] + ["Difere?"], rows, [24] + [36] * len(ps) + [10])], len(ps)

def _pend(a):
    d = Q.pendencies({**a, "all": 1})["rows"]; du = Q.duplicates()
    return [("Pendências", ["Código PERFECT", "Tipo", "Campo", "Descrição", "Status"], [[r["perfect_code"], r["kind"], r["field"], r["description"], r["status"]] for r in d], [16, 20, 14, 90, 12]),
            ("Duplicidades", ["Tipo de código", "Código", "Produtos", "Qtd. produtos"], [[r["code_type"], r["code"], r["products"], r["n"]] for r in du], [14, 20, 60, 12])], len(d)

def _fontes(a):
    h = Q.history(a.get("status"))
    return [("Histórico", ["#", "Data", "Arquivo", "Planilha", "Categoria", "Linhas lidas", "Novos", "Atualizados", "Conflitos", "Erros", "Status"],
             [[b["id"], b["imported_at"], b["filename"], b["sheet"], b["category"], b["rows_read"], b["rows_new"], b["rows_updated"], b["rows_conflict"], b["rows_error"], b["status"]] for b in h["batches"]], [6, 20, 40, 14, 28, 12, 9, 12, 10, 8, 10]),
            ("Fontes", ["Fonte", "Categoria", "Importações", "Prioridade"], [[s["name"], s["category"], s["imports"], s["priority"]] for s in h["sources"]], [44, 30, 12, 10])], len(h["batches"])

def _samples(a):
    d = Q.samples(a); rows = []
    for r in d["rows"]:
        qs = (r["quotes"] + [{}, {}, {}])[:3]; ch = next((x["price"] for x in r["quotes"] if x.get("chosen")), None)
        rows.append([r["perfect_code"], r["sample_code"], r["sc_number"], r["ship_code"], r["application"], {"direito": "Direito (LD)", "esquerdo": "Esquerdo (LE)", "ambos": "Ambos (LD/LE)"}.get(r.get("side")), r["supplier"], r["month"], dict(d["stages"]).get(r["stage"]), "SIM" if r["to_send"] else "", "SIM" if r["pending_supplier"] else "",
                     r["tracking"], r["net_weight"], r["gross_weight"], r["credit_note"], ch] + [v for x in qs for v in (x.get("price"), x.get("link"))] + [r["notes"]])
    return [("Amostras", ["Código PERFECT", "Código amostra", "Nº SC", "Cód. envio", "Aplicação", "Lado", "Fornecedor", "Mês", "Etapa", "Enviar", "Pendente fornecedor", "Rastreio", "Peso líq.", "Peso bruto", "Credit note", "Preço escolhido",
             "Preço 1", "Link 1", "Preço 2", "Link 2", "Preço 3", "Link 3", "Observações"], rows, [16, 18, 10, 12, 40, 14, 16, 12, 18, 8, 12, 18, 9, 9, 12, 12, 10, 30, 10, 30, 10, 30, 30])], len(rows)

def _damping(a):
    ts = damping.tests(a.get("q"), a.get("res")); pts = []
    for t in ts:
        full = damping.get_test(t["id"])
        for p in full["points"]: pts.append([t["id"], t["perfect_code"], t["label"], t["test_date"], p["table_name"], p["velocity"], p["tolerance"], p["drawing"], p["min"], p["max"], p["found"], p["result"]])
    return [("Ensaios", ["#", "Código PERFECT", "Identificação", "Data", "Resultado geral"], [[t["id"], t["perfect_code"], t["label"], t["test_date"], t["overall"]] for t in ts], [6, 16, 30, 12, 16]),
            ("Pontos", ["Ensaio", "Código PERFECT", "Identificação", "Data", "Tabela", "VM/S", "Tolerância", "DRAWING", "Mín (N)", "Máx (N)", "FOUND", "Resultado"], pts, [8, 16, 26, 12, 8, 8, 10, 10, 10, 10, 10, 16])], len(ts)

def _backups(a):
    return [("Backups", ["Arquivo", "Data", "Tamanho (bytes)"], [[b["name"], b["date"], b["size"]] for b in Q.backups()], [50, 20, 16])], 0

def _rd(kind):
    def f(a):
        import rd as R
        its = R.items(kind, {**a, "all": 1})["rows"]
        import statuses as S
        lines = Q.q(f"SELECT code,suggestion,description,make,vehicle,application_text,year_from,year_to,status,{','.join(c for _, c, _ in S.SUBS)},supplier,substr(sample_bought,1,10) b,substr(sample_sent,1,10) s,product_id FROM rd_projects WHERE suggestion=? ORDER BY code,make,vehicle", (kind,))
        sub = lambda r: " · ".join(f"{x['l']}: {x['v']}" for x in r["subs"])
        # etapa 22 · Q16c: FOB do fornecedor do item (FOB_FINAL do servidor; sem ele, a planilha FOB) e o de comparação (vigente ou outros, da planilha)
        fi = lambda r: (r.get("fob") or {}).get("item") or {}
        cmp_ = lambda r: " · ".join(f"{'vigente ' if c['rotulo'] == 'vigente' else ''}{c['fornecedor']} {c['preco'] if c['preco'] is not None else 'sem FOB'}" for c in (r.get("fob") or {}).get("comparar") or [])
        return [("Itens", ["Código", "Descrição", "Montadoras", "Veículos", "Aplicações", "Status", "Sub status", "Fornecedores", "Amostra comprada", "Amostra enviada", "No catálogo",
                           "FOB fornecedor do item (US$)", "Fornecedor do item", "Fonte do FOB", "FOB vigente / outros (planilha)"],
                 [[r["code"], r["description"], r["makes"], r["vehicles"], r["n_rows"], r["statuses"], sub(r), r["suppliers"], r["bought"], r["sent"], "SIM" if r["product_id"] else "",
                   fi(r).get("preco"), fi(r).get("fornecedor"), {"servidor": "FOB_FINAL do servidor", "planilha": "planilha FOB"}.get(fi(r).get("fonte"), ""), cmp_(r)] for r in its],
                 [16, 36, 20, 30, 10, 28, 60, 18, 14, 14, 10, 14, 14, 20, 30]),
                ("Linhas (todas)", ["Código", "Tipo", "Descrição", "Montadora", "Veículo", "Aplicação", "Ano inicial", "Ano final", "Status", *[f"Sub status {l.lower()}" for _, _, l in S.SUBS], "Fornecedor", "Amostra comprada", "Amostra enviada"],
                 [[l["code"], l["suggestion"], l["description"], l["make"], l["vehicle"], l["application_text"], l["year_from"], l["year_to"], l["status"], *[l[c] for _, c, _ in S.SUBS], l["supplier"], l["b"], l["s"]] for l in lines],
                 [16, 8, 34, 16, 18, 40, 10, 10, 24, *[24] * len(S.SUBS), 12, 14, 14])], len(its)
    return f

BUILD = {"desenvolvimento": _rd("DESENVOLVIMENTO"), "redesenvolvimento": _rd("REDESENVOLVIMENTO"), "produtos": _products, "pesquisa": _pesquisa, "aplicacoes": _apps, "comparacao": _compare, "pendencias": _pend, "fontes": _fontes, "amostras": _samples, "damping": _damping, "configuracoes": _backups}

LABELS = {"desenvolvimento": "Desenvolvimento", "redesenvolvimento": "Redesenvolvimento", "produtos": "Produtos e códigos", "pesquisa": "Pesquisa de amortecedores", "aplicacoes": "Aplicações veiculares",
          "comparacao": "Comparação técnica", "pendencias": "Pendências de dados", "fontes": "Fontes e histórico", "amostras": "Compra de amostras", "damping": "Damping force",
          "configuracoes": "Backups", "desenhos": "Desenhos", "equivalencias": "Equivalências", "anomalias": "Anomalias", "parados": "Saldos parados", "garantia": "Garantia", "vendas_uf": "Vendas por estado", "inmetro": "Inmetro", "estoque": "Estoque", "previsao": "Previsão de chegadas","brands": "Brands", "pendente_compras": "Pendente de compra", "lados": "Lados", "envio": "Envio de amostra", "cobertura": "Cobertura de concorrentes", "validacao": "Validação"}      # nome da tela como no menu (nome do arquivo baixado)
FLABEL = {"sit": "Situação", "familia": "Família", "forn": "Fornecedor do certificado", "q": "Busca", "make": "Montadora", "model": "Modelo", "year": "Ano", "axle": "Eixo", "side": "Lado", "system": "Sistema", "status": "Status", "supplier": "Fornecedor", "month": "Mês", "stage": "Etapa",
          "code": "Código", "code_type": "Tipo de código", "origem": "Origem", "ids": "Produtos", "kind": "Tipo", "where": "Cadastro", "ext": "Formato", "confidence": "Confiança", "family": "Família", "brand": "Marca",
          "curtiu": "Curtiu", "flag": "Controle", "rod": "Ø haste", "launch": "Lançamento", "linha": "Linha", "hibrido": "Híbrido ou elétrico","origin": "Origem", "res": "Resultado", "scope": "Onde está", "field": "Campo", "ano": "Ano", "tipo": "Tipo", "fornecedor": "Fornecedor", "procedencia": "Procedência", "unidade": "Unidade", "defeito": "Defeito", "concorrente": "Concorrente", "curva": "Curva ABC", "lancamento": "Lançamento", "tab": "Aba", "uf": "UF", "linhas": "Linhas", "validade": "Lote válido/vencido", "situacao": "Situação", "classif": "Classificação"}
FVALUE = {"sit": {"dois": "Nos dois fornecedores", "zs": "Só ZS", "ewin": "Só E-WIN", "sem": "Sem certificado", "so_cert": "Só no certificado", "rd_aprovacao": "DES/R-D em aprovação", "rd_com_num": "DES/R-D com nº Inmetro", "rd_fora": "DES/R-D fora do certificado", "div_familia": "Divergência de família", "div_haste": "Divergência de Ø da haste", "div_ean": "Divergência de código de barras"}, "forn": {"dois": "Os dois", "zs": "Só ZS", "ewin": "Só E-WIN", "nenhum": "Nenhum"}, "system": SYS, "launch": {"S": "Sim", "N": "Não"}, "hibrido": {"S": "Sim", "N": "Não", "nd": "Não informado"}, "linha": {"sem": "Sem linha"},"kind": {"desenho": "Desenho técnico", "projeto": "Projeto PERFECT", "rd": "Redesenvolvimento", "des": "Desenvolvimento", "conflito": "Conflito entre fontes", "campo_ausente": "Campo ausente", "campo_invalido": "Campo inválido"},
          "status": {"aberta": "Abertas", "resolvida": "Resolvidas", "ignorada": "Ignoradas", "todas": "Todas", "simulado": "Só verificação", "andamento": "Em andamento", "aprovada": "Aprovadas", "reprovada": "Reprovadas"},
          "field": {"family": "Família", "package_code": "Código da caixa", "ean": "EAN", "peso": "Peso", "sistema": "Sistema"},
          "where": {"cat": "No catálogo", "des": "Em DES", "rd": "Em R-D", "sem": "Sem vínculo", "falta": "Sem desenho"},
          "res": {"APPROVED": "Aprovados", "DISAPPROVED": "Reprovados", "INCOMPLETO": "Incompletos"}, "axle": {"sem": "não informado"}, "side": {"sem": "não informado"},
          "scope": {"catalog": "No catálogo", "des": "Em DES", "rd": "Em R-D", "base": "Na base Motorcraft"}, "brand": {"OUTROS": "Sem marca"},
          "flag": {"pend_validacao": "Pend. validação", "val_reprovada": "Validação reprovada", "pend_desenho_forn": "Pend. desenho forn.", "pend_compras": "Pend. compras"}}          # valor legível no nome do arquivo e na aba «Filtros aplicados»
def _fv(k, v): return FVALUE.get(k, {}).get(v, v)

def friendly_name(module, filtros=None, ext="xlsx"):
    """'PerfectAmortecedores - Produtos e códigos - 18-11.xlsx' (decisão Q16/Q26 da etapa 17): nome da tela como no menu e o dia.
    Os filtros não entram no nome — ficam na aba «Filtros aplicados». Dois downloads no mesmo dia: o navegador acrescenta «(1)».
    Exceção (etapa 24 · Q2): na Pesquisa, o item selecionado (código buscado; montadora, modelo e ano) entra no nome."""
    sel = _selecao(filtros or {}) if module == "pesquisa" else ""
    return f"PerfectAmortecedores - {LABELS.get(module, module.title())}{' - ' + sel if sel else ''} - {datetime.datetime.now():%d-%m}.{ext}"

def _desenhos(a):
    """Sem filtro: todos os arquivos dos dois tipos. Com filtro (tela Desenhos): os mesmos códigos da galeria; where=falta lista os itens sem arquivo."""
    import drawings
    flt = {k: a[k] for k in ("kind", "q", "where", "origin", "ext") if a.get(k)}; keys = None
    if flt:
        g = drawings.gallery({**flt, "all": 1})["rows"]
        if flt.get("where") == "falta":
            return [("Sem desenho" if drawings._kind(flt.get("kind")) == "desenho" else "Sem projeto", ["Código", "Descrição", "Cadastros"],
                     [[c["code"], c["description"], ", ".join(c["registries"])] for c in g], [16, 50, 40])], len(g)
        keys = {c["key"] for c in g if c.get("code")}
    rows = []
    for r in Q.q("""SELECT l.code,f.filename,f.ext,f.size,f.rev_num,f.rev_label,f.rev_auto,f.uploaded_at,coalesce(f.kind,'desenho') kind FROM drawing_links l JOIN drawing_files f ON f.id=l.file_id ORDER BY l.code,f.kind,f.rev_num DESC,f.id DESC"""):
        if keys is not None and (r["code"] not in keys or r["kind"] != drawings._kind(flt.get("kind"))): continue
        cur = {x["filename"] for x in drawings._current([x for x in Q.q("SELECT f.id,f.filename,f.ext,f.rev_num FROM drawing_files f JOIN drawing_links l ON l.file_id=f.id WHERE l.code=? AND coalesce(f.kind,'desenho')=?", (r["code"], r["kind"]))])}
        rows.append([r["code"], "Projeto PERFECT" if r["kind"] == "projeto" else "Desenho técnico", "Rev. " + (r["rev_label"] or str(r["rev_num"]).zfill(2)), "Vigente" if r["filename"] in cur else "Histórico", r["filename"], (r["ext"] or "").lstrip(".").upper(), round((r["size"] or 0) / 1024, 1), "Automática" if r["rev_auto"] else "Pelo nome", r["uploaded_at"]])
    return [("Desenhos", ["Código", "Tipo", "Revisão", "Situação", "Arquivo", "Formato", "Tamanho (KB)", "Revisão definida", "Enviado em"], rows, [16, 16, 12, 12, 46, 10, 14, 16, 20])], len(rows)

FL = {"pend_validacao": "Pend. validação", "val_reprovada": "Validação reprovada", "pend_desenho_forn": "Pend. desenho forn.", "pend_compras": "Pend. compras"}
def _brands(a):
    import brands
    sel = [a["brand"].upper()] if a.get("brand") else brands.BRANDS; sheets, n = [], 0
    for b in sel:
        its = brands.items(b, {**a, "all": 1})["rows"]; n += len(its)
        sheets.append(("Sem marca" if b == "OUTROS" else b.title(), ["Código", "Código PERFECT relacionado", "Descrição", "Veículo / aplicação", "Catálogo", "Em DES", "Em R-D", "Base Motorcraft", "Pedidos de amostra", "Controle de status"],
                       [[i["code"], " / ".join(i.get("perfect_codes") or []), i["description"], i["vehicle"], "Sim" if i["catalog"] else "", "Sim" if i["des"] else "", "Sim" if i["rd"] else "", "Sim" if i["base"] else "Não (PN Ford fora da base)" if i.get("fora_base") else "", i["samples"] or "", ", ".join(FL[f] for f in i["flags"])] for i in its], [20, 24, 38, 40, 10, 8, 8, 14, 12, 40]))
    return sheets, n
def _pendente(a):
    import purchases
    tot = purchases.pending({**a, "page": 1})["total"]; rows = []
    for pg in range(1, tot // 40 + 2):
        for r in purchases.pending({**a, "page": pg})["rows"]:
            rows.append([r["code"], r["suggestion"], r["description"], r["vehicles"], {"sem": "Sem pedido", "cotacao": "Em cotação"}.get(r["state"], r["state"]),
                         " | ".join(f"{c['brand']} {c['code']}" for c in r["cross"]) or "sem referência cruzada", "; ".join(f"SC {o['sc'] or '–'} ({o['stage']})" for o in r["orders"])])
    return [("Pendente de compra", ["Código", "Tipo", "Descrição", "Veículo(s)", "Situação da compra", "Referência cruzada (o que cotar)", "Pedidos de amostra"], rows, [18, 8, 36, 30, 20, 70, 36])], len(rows)
def _lados(a):
    import sides
    its = sides.listing({**a, "all": 1})["rows"]; AX = {"dianteiro": "Dianteiro", "traseiro": "Traseiro", "cabine": "Cabine", "ambos_eixos": "Diant./Tras."}
    SH = {"direito": "LD", "esquerdo": "LE", "ambos": "LD/LE"}
    fmt = lambda xs: " | ".join(f"{x['code']} ({SH.get(x['side'], '—')}; {sides.LEVELS.get(x['level'], x['level'])}{'; par ' + x['pair']['code'] if x.get('pair') else ''})" for x in xs)
    kit = lambda i: " + ".join(f"{k['code']} {SH.get(k['side'], '')}{' ×2' if k['qty'] == 2 else ''}" for k in i.get("kit") or [])
    return [("Lados", ["Código", "Descrição", "Eixo", "Lado", "Par (outro lado)", "Como achou o par", "Traseiro (mesma aplicação)", "Dianteiro (mesma aplicação)", "Possuímos o outro eixo?", "Conjunto do veículo", "Veículos (aplicação)", "Aplicações no servidor (DES/R-D)"],
             [[i["code"], i["description"], AX.get(i["axle"], ""), sides.SIDE.get(i["side"], ""), (i["pair"] or {}).get("code", ""), i["pair_how"] or "", fmt(i["rear"]), fmt(i["front"]),
               {"exata": "Sim", "desenvolvimento": "Em desenvolvimento", "provavel": "Provável", "nao": "NÃO", "sem_aplicacao": "Sem aplicação"}.get(i["other_axle"], ""), kit(i), " | ".join(i["vehicles"]), " | ".join(i.get("server_apps") or [])] for i in its],
             [14, 34, 12, 14, 14, 22, 50, 50, 16, 50, 90, 60])], len(its)
def _envio(a):
    import shipments
    d = shipments.listing({**a, "all": 1}); SD = {"direito": "Direito (LD)", "esquerdo": "Esquerdo (LE)", "ambos": "Ambos (LD/LE)"}
    return [("Envio de amostra", ["Código", "Descrição", "Aplicação", "Lado", "Fornecedor", "EX", "SC", "Comprada em", "Recebida em", "Status", "Enviada em", "Rastreio", "Observações"],
             [[r["perfect_code"], r["description"], r["application"], SD.get(r["side"], ""), r["supplier"], r["ex_code"], r["sc_number"], r["bought_at"], r["received_at"], r["status_label"], r["shipped_at"], r["tracking"], r["notes"]] for r in d["rows"]],
             [14, 34, 34, 14, 12, 12, 12, 12, 12, 16, 12, 18, 30])], len(d["rows"])
BUILD["lados"] = _lados; BUILD["envio"] = _envio
BUILD["brands"] = _brands; BUILD["pendente_compras"] = _pendente
BUILD["desenhos"] = _desenhos
def _parados(a):
    """Saldos parados (Q19): pedido × código sem embarque há mais de 2× o p90 da produção do fornecedor. `today` só para teste."""
    import leadtime, datetime
    t = datetime.date.fromisoformat(a["today"]) if a.get("today") else None; rows = leadtime.parados(t)
    return [("Saldos parados", ["Pedido", "Fornecedor", "Código", "Descrição", "Saldo", "Emissão", "Dias sem embarque", "Limite (2× p90, dias)", "Última previsão", "Nº de adiamentos", "Dias adiados"],
             [[r["pedido"], r["fornecedor"], r["codigo"], r["descricao"], r["saldo"], r["emissao"], r["dias_sem_embarque"], r["limite_dias"], r["ultima_previsao"], r["adiamentos"], r["dias_adiados"]] for r in rows],
             [12, 14, 16, 38, 10, 12, 14, 16, 14, 12, 12])], len(rows)
BUILD["parados"] = _parados
def _vendas_uf(a):
    """Update 8: todos os códigos vendidos num estado (mapa da tela Vendas), no período e nas linhas da tela."""
    import curva_abc
    if not a.get("uf"): raise ValueError("Escolha um estado no mapa.")
    rows = curva_abc.uf_codigos(a["uf"], a.get("year"), a.get("month"), a.get("linhas"))
    return [(f"Vendas em {a['uf'].upper()}"[:31], ["Código", "Descrição", "Peças", "Valor c/ IPI", "% das peças do estado"],
             [[r["code"], r["desc"], r["pecas"], r["valor"], r["pct"]] for r in rows], [16, 44, 12, 16, 14])], len(rows)
BUILD["vendas_uf"] = _vendas_uf
def _inmetro(a):
    """Update 8: aba Inmetro de Produtos e códigos com os filtros da tela (situação, família, fornecedor, busca)."""
    import inmetro
    rows = inmetro.linhas_excel({k: a.get(k, "") for k in ("sit", "familia", "forn", "q")})
    sit = lambda l: inmetro.SIT[l["sit"]] if l["grupo"] == "rd" else inmetro.CAT[l["sit"]]
    p = lambda l, k: (l["pad"] or {}).get(k)
    return [("Inmetro", ["Código", "Descrição", "Origem", "Situação", "Família (catálogo)", "Família em outro certificado", "Nº ZS", "Nº E-WIN", "Nº do servidor", "Outros certificados",
                         "Cód. barras catálogo", "Cód. barras ZS", "Cód. barras E-WIN", "Marca", "Material", "Categoria", "Tratamento térmico", "Ø haste certificado (mm)", "Ø haste catálogo (mm)",
                         "Descrição padronizada", "Descrição do certificado", "Divergências", "Status DES/R-D"],
             [[l["code"], l["descr"], {"catalogo": "Catálogo", "fora": "Só no certificado", "rd": l.get("tipo")}[l["grupo"]], sit(l), l["fam"], ", ".join(l["fam_cert"]), l["num_zs"], l["num_ew"], l.get("num_srv"),
               ", ".join(l.get("outros") or []), l["ean"], l["ean_zs"], l["ean_ew"], l["marca"], p(l, "material"), p(l, "categoria"), p(l, "tratamento"), p(l, "haste"), l["haste_cat"],
               l["pad_txt"], l["orig"], ", ".join(inmetro.DIV[d] for d in l["div"]), l.get("status")] for l in rows],
             [14, 34, 12, 18, 16, 18, 13, 13, 13, 22, 16, 16, 16, 12, 10, 12, 20, 12, 12, 40, 50, 22, 24])], len(rows)
BUILD["inmetro"] = _inmetro
def _garantia(a):
    """Garantia (servidor, etapa 18) com os filtros da tela: ocorrências + defeitos (Pareto), códigos, UF (índice), fornecedores e lotes."""
    import garantias
    f = {k: a.get(k, "") for k in garantias.FILTROS}; rows = garantias.rows_all(f); s = garantias.summary(f, size=1)
    if not s.get("available"): raise ValueError("Sem dados de garantia: sincronize com o servidor (a garantia vem da view ANALITICO_GARANTIA_DEVOLUCAO).")
    return [("Ocorrências", ["Data", "Autorização", "Tipo", "Status", "Status do item", "Unidade", "UF", "Grupo cliente", "Cliente", "NF", "Código", "Qtd", "Valor c/ IPI", "Defeito", "Cód. defeito", "Lote", "Lote válido/vencido", "Fabricação", "Fornecedor", "Procedência", "Responsável", "Erro lote"],
             [[r["data_cadastro"], r["autorizacao"], r["tipo"], r["status"], r["status_item"], r["unidade"], r["uf"], r["grupo_cliente"], r["cliente"], r["nf"], r["codigo"], r["qtd"], r["valor"], r["defeito"], r["defeito_cod"], r["lote"], r["lote_validade"], r["data_fabricacao"],
               r["fornecedor"], r["procedencia"], r["responsavel"], r["erro_lote"]] for r in rows], [11, 12, 20, 24, 24, 14, 6, 18, 30, 12, 14, 8, 12, 40, 10, 12, 12, 11, 10, 13, 14, 10]),
            ("Defeitos", ["Defeito", "Cód.", "Linhas", "Peças", "% das peças", "% acumulado"], [[r["defeito"], r["cod"], r["linhas"], r["pecas"], r["pct"], r["acum"]] for r in s["defeitos"]], [50, 10, 10, 10, 12, 12]),
            ("Códigos", ["Código", "Descrição", "Linhas", "Peças", "Valor c/ IPI", "Defeitos"], [[r["codigo"], r["descricao"], r["linhas"], r["pecas"], r["valor"], r["defeitos"]] for r in s["codigos"]], [16, 38, 10, 10, 14, 10]),
            ("Por UF", ["UF", "Ocorrências", "Peças em garantia", "Valor c/ IPI", "Peças vendidas", "Índice de garantia (%)", "Código com mais peças", "Peças do código"],
             [[r["uf"] or "não informada", r["ocorrencias"], r["pecas"], r["valor"], r["vendidas"], r["indice"], (r["top"] or [{}])[0].get("codigo"), (r["top"] or [{}])[0].get("pecas")] for r in s["por_uf"]], [8, 12, 14, 14, 14, 14, 18, 12]),
            ("Fornecedores", ["Fornecedor", "Códigos", "Peças", "Valor c/ IPI", "% procedente"], [[r["fornecedor"] or "não informado", r["codigos"], r["pecas"], r["valor"], r["pct_procedente"]] for r in s["fornecedores"]], [18, 10, 10, 14, 12]),
            ("Lotes", ["Lote", "Código", "Códigos", "Fabricação", "Válido/vencido", "Peças", "Linhas com erro de lote"], [[r["lote"], r["codigo"], r["codigos"], r["fabricacao"], r["validade"], r["pecas"], r["erro_lote"]] for r in s["lotes"]], [16, 16, 10, 12, 12, 10, 18])], len(rows)
BUILD["garantia"] = _garantia
def _estoque(a):
    """Vendas × estoque com os filtros da tela (situação, classe, busca). `today` só para teste."""
    import estoque, datetime
    t = datetime.date.fromisoformat(a["today"]) if a.get("today") else None; d = estoque.listing({**a, "all": 1}, today=t); S = {"ruptura": "Ruptura", "risco": "Risco", "ok": "OK", "excesso": "Excesso", "sem_giro": "Sem giro"}
    M = d["meses"]
    P = ("pa", "mp", "private", "fect")
    return [("Vendas × estoque", ["Código", "Descrição", "Situação", "Classe", "Venda 12 meses (peças)", "Valor 12 meses", "Venda média/mês", f"Estoque contado ({d['contas'][d['conta']]})",
                                  "Estoque PA", "Estoque MP", "PRIVATE", "FECT", "A caminho", "Cobertura (meses)",
                                  "Falta em", "Falta antes de chegar o pedido", *[f"Chegada {m}" for m in M], *[f"Saldo fim {m}" for m in M]],
             [[r["codigo"], r["descricao"], S[r["situacao"]], r["classe"], r["venda_12m"], r["valor_12m"], r["media_mensal"], r["estoque"], *[r["partes"][p] for p in P], r["a_caminho"], r["cobertura"],
               r["falta_em"], "Sim" if r["antes_de_chegar"] else "", *r["chegadas"], *r["projecao"]] for r in d["rows"]],
             [16, 38, 11, 8, 14, 14, 12, 16, 11, 11, 11, 11, 11, 12, 10, 14] + [11] * (2 * len(M)))], d["total"]
BUILD["estoque"] = _estoque
def _previsao(a):
    """Previsão de chegadas (linhas) com os filtros da tela: etapa, fornecedor, alerta (atrasar / vencida), busca. Com «vencida» serve para cobrar o fornecedor."""
    import leadtime
    d = leadtime.previsao_linhas({**a, "all": 1}); desc = {(str(r["pedido"]), (r["code"] or "").upper()): r["d"] for r in Q.q("SELECT pedido, code, MAX(description) d FROM ds_compras GROUP BY pedido, code")} if d["total"] else {}
    A = {"atrasar": "vai atrasar", "vencida": "previsão vencida"}
    return [("Previsão de chegadas", ["Pedido", "Fornecedor", "Código", "Descrição", "Quantidade", "Etapa", "Processo", "Emissão", "Promessa", "Embarque", "ETA servidor", "Chegada prevista", "Faixa de", "Faixa até",
                                      "Atraso previsto (dias)", "Dias vencida", "Alertas", "Confiança"],
             [[r.get("pedido"), r.get("fornecedor"), r.get("codigo"), desc.get((str(r.get("pedido")), (r.get("codigo") or "").upper())), r.get("quantidade"), r.get("etapa"), r.get("processo"), str(r.get("emissao") or "")[:10] or None,
               str(r.get("prometido") or "")[:10] or None, r.get("embarque") or r.get("embarque_previsto"), r.get("eta_servidor"), r.get("chegada_prevista"), r.get("faixa_de"), r.get("faixa_ate"), r.get("atraso_previsto"),
               r.get("dias_vencida"), ", ".join(A[x] for x in r["alertas"]), r.get("confianca")] for r in d["rows"]],
             [10, 10, 16, 34, 10, 20, 14, 11, 11, 11, 11, 13, 11, 11, 12, 10, 22, 10])], d["total"]
BUILD["previsao"] = _previsao

def _cobertura(a):
    """Cobertura de concorrentes (etapa 17): aba Catálogo (concorrente × referência × nosso código, curva e estoque) e aba Desenvolvimento (DES em andamento com frota e curva),
    cada uma com os filtros da sua aba na tela (`tab` diz qual aba estava aberta; a outra sai sem filtro)."""
    import cobertura
    if a.get("tab") == "cofap":       # etapa 18 · Q5: a aba COFAP tem Excel próprio (só ela, com os filtros da aba)
        d = cobertura.cofap({**a, "all": 1})
        return [("COFAP", ["Código COFAP", "Situação", "Nosso código", "Frota 2024 (planilha)", "Curva (não temos)", "Classificação", "Veículos", "Principais veículos"],
                 [[r["cofap"], cobertura.SIT_COFAP[r["situacao"]], ", ".join(r["nossos"]), r["frota"], r["curva"] if r["curva"] not in ("", "sem") else "", ", ".join(r["classes"]), r["n_veiculos"],
                   "; ".join(f"{v['nome']} {v['anos']} ({v['frota']:,.0f})".replace(",", ".") for v in r["veiculos"])] for r in d["rows"]],
                 [16, 20, 24, 16, 12, 28, 10, 70])], d["total"]
    des = a.get("tab") == "desenvolvimento"
    c = cobertura.catalogo({**({} if des else a), "all": 1}); d = cobertura.desenvolvimento({**(a if des else {}), "all": 1})
    SITL = {"ruptura": "Ruptura", "risco": "Risco", "ok": "OK", "excesso": "Excesso", "sem_giro": "Sem giro", "sem": ""}
    return [("Catálogo", ["Concorrente", "Referência", "Código PERFECT", "Descrição", "Linha", "Aplicação", "Curva ABC", "Situação do estoque", "Fonte da referência"],
             [[r["concorrente"], r["referencia"], r["codigo"], r["descricao"], r["linha"], r["aplicacao"], "" if r["curva"] == "sem" else r["curva"], SITL.get(r["situacao"], r["situacao"]), r["fonte"]] for r in c["rows"]],
             [16, 16, 14, 34, 24, 40, 10, 14, 16]),
            ("Desenvolvimento", ["Código", "Descrição", "Status", "Fornecedor", "Aplicações", f"Frota {d['kpis']['ano']}", "Origem da frota", "Curva", "Lançamento", "Concorrentes", "Veículos que mais somaram"],
             [[r["codigo"], r["descricao"], r["status"], r["fornecedor"], " · ".join(r["aplicacoes"]), r["frota"], r["origem"], "" if r["curva"] == "sem" else r["curva"], "Sim" if r["lancamento"] else "",
               ", ".join(r["concorrentes"]), "; ".join(f"{v['nome']} ({v['frota']:,.0f})".replace(",", ".") for v in r["veiculos"])] for r in d["rows"]],
             [14, 30, 20, 12, 40, 12, 16, 8, 10, 36, 50])], c["total"] + d["total"]
BUILD["cobertura"] = _cobertura

def _validacao(a):
    """Tela Validação (etapa 24): as validações com os filtros da tela e, em outra aba, todas as medidas de cada uma (com o Ap do modelo F-008)."""
    import validacao, json
    d = validacao.listagem({**a}); ids = [r["id"] for r in d["rows"]]
    med = []
    for vid in ids:
        v = q1("SELECT code,supplier,supplier_code,dados FROM validacoes WHERE id=?", (vid,))
        for l in (json.loads(v["dados"] or "{}").get("linhas") or []):
            if str(l.get("p") or "").strip() or str(l.get("f") or "").strip():
                med.append([vid, v["code"], v["supplier"], l.get("n"), l.get("nome"), l.get("p"), l.get("f"), l.get("tm"), l.get("tn"), validacao.ap(l), l.get("melhoria"), "Sim" if l.get("conferida") else ""])
    return [("Validações", ["#", "Código", "Descrição", "Tipo", "Fornecedor", "Cód. fornecedor", "Família", "Medidas", "Conferidas", "A", "R", "Situação", "Atualizada", "Concluída", "F-008"],
             [[r["id"], r["code"], r["description"], r["kind_label"], r["supplier"], r["supplier_code"], (r["family"] or "").capitalize(), r["conta"]["linhas"], r["conta"]["conferidas"], r["conta"]["A"], r["conta"]["R"],
               r["status_label"], (r["updated_at"] or "")[:16].replace("T", " "), (r["concluida_em"] or "")[:16].replace("T", " "), "Sim" if r["xlsx"] else ""] for r in d["rows"]],
             [6, 14, 34, 18, 12, 16, 24, 9, 10, 6, 6, 14, 16, 16, 8]),
            ("Medidas", ["Validação", "Código", "Fornecedor", "Nº", "Medida", "PERFECT", "Fornecedor (valor)", "Tol. +", "Tol. −", "Ap", "Melhoria", "Conferida"], med, [10, 14, 12, 5, 30, 14, 16, 8, 8, 5, 30, 10])], d["total"]
BUILD["validacao"] = _validacao
from queries import q1

def build(name, args):
    if name not in BUILD: raise ValueError("Módulo sem exportação.")
    a = {k: v for k, v in args.items() if v}; sheets, n = BUILD[name](a); wb = Workbook(); wb.remove(wb.active)
    for s in sheets: _sheet(wb, *s)
    bio = _finish(wb, {"Módulo": LABELS.get(name, name), **{FLABEL.get(k, k): _fv(k, v) for k, v in a.items() if k != "all"}})
    flt = dict(a)
    if name == "comparacao" and a.get("ids"):   # nomes mais claros: códigos em vez de ids
        flt["ids"] = " x ".join(r["perfect_code"] for r in Q.q("SELECT perfect_code FROM products WHERE id IN (%s)" % ",".join("?" * len(a["ids"].split(","))), [int(i) for i in a["ids"].split(",") if i.isdigit()]))[:40]
    return bio, friendly_name(name, flt)
