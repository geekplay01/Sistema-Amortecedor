"""Página do item (etapa 17 · Q9): tudo o que o app tem de UM código — catálogo, desenvolvimento ou os dois — num só lugar (/item/<código>, API /api/item/<código>).
Seções: topo (selos e dados), aplicações e lados, concorrentes e OEM, vendas 12 meses + curva ABC, estoque/cobertura/projeção, pedidos e chegadas previstas,
linha do tempo de DES/R-D e amostras, garantia, desenhos/projeto, Inmetro, FOB, Brands e pendências/anomalias. Cada seção vem pronta para a tela (vazia = sem registro).
Não inventa nada: o que não está nas bases fica vazio. Posição no catálogo e IDs não vão para a tela (decisão Q16)."""
import re, datetime, json
from queries import q, q1

def _k(c): return re.sub(r"[^A-Z0-9]", "", re.sub(r"^\s*MP-", "", str(c or "").upper()))

def _estoque(code, today=None):
    """Linha da tela Estoque do código (mesma regra: PRIVATE + FECT, média de 12 meses fechados, cobertura e projeção de 6 meses). Em memória até a próxima sincronização."""
    import estoque
    by, lim, jan = estoque.mapa(today)
    r = by.get(_k(code))
    return {"available": bool(by), "row": r, "limites": lim, "meses": jan.get("meses", [])}

def _timeline(code):
    """Desenvolvimento: aplicações por tipo (status, fornecedor, datas) + mudanças de status registradas pela sincronização, da mais nova para a mais antiga."""
    rows = q("""SELECT suggestion tipo, status, supplier, make, vehicle, application_text, year_from, year_to, substr(sample_bought,1,10) amostra_comprada, substr(sample_sent,1,10) amostra_enviada,
                       drawing_substatus, validation_substatus FROM rd_projects WHERE upper(code)=? ORDER BY suggestion, make, vehicle""", (code,))
    try:          # datas do servidor (DESENVOLVIMENTO_PRODUTOS) por aplicação: início do desenvolvimento e pedido confirmado
        dt = {(r["kind"], (r["make"] or "").upper(), (r["vehicle"] or "").upper()): r for r in q("SELECT kind, make, vehicle, MIN(substr(date_start,1,10)) ini, MAX(substr(pedido_confirmado,1,10)) ped FROM dev_rows WHERE upper(code)=? GROUP BY 1,2,3", (code,))}
    except Exception: dt = {}
    for r in rows:
        x = dt.get((r["tipo"], (r["make"] or "").upper(), (r["vehicle"] or "").upper())) or {}
        r["data_inicio"], r["pedido_confirmado"] = x.get("ini"), x.get("ped")
    try: ev = q("SELECT kind tipo, field campo, from_value de, to_value para, substr(at,1,10) em FROM dev_status_events WHERE upper(code)=? AND field='status' ORDER BY at DESC, id DESC LIMIT 40", (code,))
    except Exception: ev = []
    return rows, ev

def _garantia(code):
    """Garantia do código, mesmo padrão da tela Garantia (só garantias, sem canceladas), todos os anos — consulta pelo código exato (índice), não o resumo inteiro."""
    import garantias
    w, p = garantias._where({"ano": "todos"}); w = (w + " AND " if w else " WHERE ") + "codigo=?"; p = p + [code]
    k = q1(f"""SELECT COUNT(DISTINCT autorizacao) ocorrencias, COALESCE(SUM(qtd),0) pecas, COALESCE(SUM(valor),0) valor,
               COALESCE(SUM(CASE WHEN procedencia='PROCEDENTE' THEN qtd END),0) proc, COALESCE(SUM(CASE WHEN procedencia='IMPROCEDENTE' THEN qtd END),0) improc FROM garantias{w}""", p)
    k["pct_procedente"] = round(100 * k["proc"] / (k["proc"] + k["improc"]), 1) if (k["proc"] + k["improc"]) else None
    tot = k["pecas"] or 1
    defeitos = q(f"SELECT defeito, COALESCE(SUM(qtd),0) pecas FROM garantias{w} GROUP BY defeito ORDER BY pecas DESC LIMIT 8", p)
    for r in defeitos: r["pct"] = round(100 * r["pecas"] / tot, 1)
    return {"available": True, "kpis": k, "defeitos": defeitos,
            "por_ano": q(f"SELECT substr(data_cadastro,1,4) ano, COALESCE(SUM(qtd),0) pecas FROM garantias{w} GROUP BY 1 ORDER BY 1", p),
            "rows": q(f"SELECT data_cadastro, autorizacao, cliente, qtd, defeito, lote, procedencia FROM garantias{w} ORDER BY data_cadastro DESC LIMIT 10", p)}

def _anomalias(code, pid):
    """Em quais listas de Anomalias o código aparece (para corrigir na origem)."""
    import anomalias, concorrentes
    out = []
    try:
        if any(r["perfect_code"] == code for r in anomalias.pesoean(code)): out.append(("pesoean", "Peso ou EAN diferente entre CatalogoAMD e BI03"))
        if any(r["code"] == code for r in anomalias.protheus(code)): out.append(("protheus", "Pendente cadastro Protheus"))
        if any(r["perfect_code"] == code for r in concorrentes.cross_x_servidor(code)): out.append(("cross", "Concorrente com referência diferente no CrossCatalogo e no servidor"))
        if any(code in r["codigos"] for r in concorrentes.repetidos(code)): out.append(("repetidos", "Referência de concorrente repetida"))
        if pid and any(r["product_id"] == pid for r in anomalias.familia(code)): out.append(("familia", "Família do catálogo diferente do Inmetro"))
    except Exception: pass
    return [{"tab": t, "texto": x} for t, x in out]

def ficha(code):
    import queries, concorrentes, analytics, curva_abc, leadtime, garantias, drawings, bi03
    code = re.sub(r"\s+", "", str(code or "")).upper()
    if not code: return None
    p = q1("SELECT id FROM products WHERE upper(perfect_code)=?", (code,))
    rd_rows, eventos = _timeline(code)
    if not p and not rd_rows: return None
    pid = p["id"] if p else None
    f = queries.ficha(pid) if pid else {}
    d = f.get("dimensions") or {}
    tipos = sorted({r["tipo"] for r in rd_rows})
    desc = f.get("description") or (q1("SELECT description FROM rd_projects WHERE upper(code)=? AND description IS NOT NULL LIMIT 1", (code,)) or {}).get("description")
    no_catalogo = bool(pid and f.get("catalog_position") is not None)
    cls = curva_abc.classes().get(_k(code))
    vendas = analytics.sales_of(code, 12)
    est = _estoque(code)
    prev = leadtime.previsao_linhas({"q": code, "all": 1})
    pedidos = [r for r in prev.get("rows", []) if _k(r.get("codigo")) == _k(code)]
    gar = _garantia(code) if garantias.available() else {"available": False}
    des = {k: drawings.detail(code, k) for k in ("desenho", "projeto")}
    brands = q("SELECT brand, code, description FROM brand_items WHERE upper(perfect_code)=? ORDER BY brand, code", (code,))
    amostras = q("SELECT sc_number, sample_code, supplier, stage FROM sample_orders WHERE upper(perfect_code)=? OR upper(sample_code)=?" + (" OR product_id=?" if pid else ""), (code, code, pid) if pid else (code, code))
    topo = {"code": code, "description": desc, "product_id": pid, "no_catalogo": no_catalogo, "tipos": tipos,
            "sistema": f.get("system_type"), "familia": f.get("family"), "linha": f.get("catalog_line"), "hibrido": f.get("hybrid"), "lancamento": f.get("is_launch"),
            "grupo": f.get("catalog_group"), "ean": f.get("ean"), "peso": f.get("weight_kg"), "ncm": f.get("ncm"), "ipi": bi03.ipi(code),
            "caixa": f.get("package_code"), "caixa_dim": (f.get("box") or {}).get("raw_dims"), "embalagem": f.get("package_note"),
            "medidas": {k: d.get(k) for k in ("lmin_mm", "lmax_mm", "stroke_mm", "rod_diameter_mm", "body_length_mm", "tube_diameter_mm", "upper_mount", "lower_mount")},
            "classe": cls, "situacao": (est["row"] or {}).get("situacao")}
    return {"topo": topo,
            "aplicacoes": {"catalogo": f.get("applications", []), "desenvolvimento": [{k: r[k] for k in ("tipo", "make", "vehicle", "application_text", "year_from", "year_to", "status")} for r in rd_rows]},
            "lados": f.get("pair", []),
            "concorrentes": concorrentes.para_item(code),
            "codigos": [c for c in f.get("codes", []) if c["code_type"] == "fornecedor"],
            "vendas": {**vendas, "classe": cls},
            "estoque": est,
            "pedidos": {"available": prev.get("available", False), "rows": pedidos, "compras": analytics.purchases_of(code)},
            "desenvolvimento": {"rows": rd_rows, "eventos": eventos},
            "amostras": amostras,
            "garantia": gar,
            "desenhos": des,
            "inmetro": f.get("certificates", []),
            "fob": f.get("fob_quotes") if pid else queries.fob_quotes(queries.fob_row(code)),          # etapa 22: item só de DES/R-D também mostra o FOB
            "brands": brands,
            "componentes": f.get("components", []),
            "pendencias": [x for x in f.get("pendencies", []) if x["status"] == "aberta"],
            "anomalias": _anomalias(code, pid)}
