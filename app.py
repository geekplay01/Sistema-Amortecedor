"""Perfect Shock Data - rotas Flask."""
from flask import Flask, send_file, Response, render_template, jsonify, request, abort, send_from_directory, g
import os, re, glob, uuid, shutil, datetime, threading
import database as db, importer, loaders, queries, equivalence, damping, exporter, rd, updater, drawings, purchases, brands, shipments, sides
import kinds, statuses, data_pipeline, goals, analytics, price_search, auth, rules, metas, orders, curva_abc, fob_merge, regras_telas

data_pipeline.load_env()          # lê o .env (usuário/senha do servidor, chaves do Mercado Livre...)
app = Flask(__name__)
auth.init_app(app)                # login de administrador (desligar só em desenvolvimento: PSD_AUTH=off)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024   # desenhos CAD podem ser grandes
ASSET_V = datetime.datetime.now().strftime("%Y%m%d%H%M%S")   # muda a cada vez que o app abre: o navegador baixa JS/CSS novos (sem Ctrl+F5)

@app.url_defaults
def _asset_version(endpoint, values):
    if endpoint == "static" and "v" not in values and str(values.get("filename", "")).endswith((".js", ".css", ".svg")): values["v"] = ASSET_V      # .svg: arquivo único de ícones
UPLOADS = os.path.join(db.BASE, 'data', 'uploads')
CATEGORIES = ['Produtos / códigos', 'Aplicações', 'Dimensões técnicas', 'Fornecedores / concorrentes', 'Dados comerciais / logísticos', 'Personalizada']
db.init_db()
shipments.sync()   # envios coerentes com Compra de amostra e os itens em desenvolvimento
goals.ensure()
import ipi; ipi.ensure()          # update 9: envios e respostas da aprovação de IPI

# slug, rótulo, ícone (nome em static/img/icones.svg — tools/icones.py), etapa em que foi implementada
PAGES = [
 ("dashboard", "Dashboard", "layout-dashboard", 1),
 ("pesquisa", "Pesquisa de amortecedores", "search", 3),
 ("produtos", "Produtos e códigos", "package", 3),
 ("aplicacoes", "Aplicações veiculares", "car", 3),
 ("comparacao", "Comparação técnica", "git-compare-arrows", 4),
 ("anomalias", "Anomalias", "triangle-alert", 4),          # antiga «Equivalências» (agora uma das abas); /equivalencias redireciona
 ("cobertura", "Cobertura de concorrentes", "swords", 17),          # etapa 17: concorrentes × nossos itens (catálogo) e curva dos DES pela frota
 ("atualizacao", "Atualização de dados", "refresh-cw", 2),
 ("lados", "Lados", "arrow-left-right", 3),
 ("envio", "Envio de amostra", "send", 3),
 ("metas", "Metas & Validação", "target", 1),
 ("pedidos-aberto", "Pedidos em Aberto", "clipboard-list", 1),
 ("vendas", "Vendas (Curva A)", "chart-column", 1),
 ("estoque", "Estoque", "warehouse", 1),          # vendas × estoque (etapa 16 · C)
 ("fob", "FOB (preços de compra)", "circle-dollar-sign", 2),
 ("garantia", "Garantia", "shield-check", 1),
 ("brands", "Brands", "tags", 1),
 ("desenhos", "Desenhos", "drafting-compass", 1),
 ("importacao", "Importação de Excel", "upload", 2),
 ("desenvolvimento", "Desenvolvimento", "amortecedor", 3),
 ("redesenvolvimento", "Redesenvolvimento", "rotate-ccw", 3),
 ("validacao", "Validação", "clipboard-check", 24),          # etapa 24: validação de desenho (PERFECT × fornecedor) que gera o F-008
 ("amostras", "Compra de amostras", "shopping-cart", 3),
 ("damping", "Damping force", "activity", 3),
 ("monitoramento-ipi", "Monitoramento de IPI", "file-spreadsheet", 24),          # update 9: aprovação do IPI dos itens em desenvolvimento
 ("pendencias", "Pendências de dados", "circle-alert", 4),
 ("fontes", "Fontes e histórico", "history", 2),
 ("configuracoes", "Configurações e backup", "settings", 5),
]
HIDDEN = [("guia-visual", "Guia visual", "sparkles", 17)]          # telas fora do menu (abertas pelo endereço): guia do design da etapa 17
CARDS = [  # chave, rótulo, destino, dica — produtos, DES e R-D ficam só na fileira de destaque do Dashboard (etapa 21: antes apareciam duas vezes)
 # etapa 23 · Q5: lista em duas colunas — primeiro o que pede ação, depois os cadastros; os zerados vão para o fim (app.js)
 ("pend_compras", "Pendente compras", "amostras?tab=pendentes", "Itens aguardando compra de amostra"),
 ("equivalences_pending", "Equivalências a validar", "anomalias?tab=sugestoes", "Sugestões aguardando decisão"),
 ("ship_pendente", "Amostras a enviar", "envio?status=pendente_projeto", "Recebidas, aguardando o projeto"),
 ("duplicates", "Possíveis duplicidades", "pendencias?tab=dup", "Mesmo código em produtos diferentes"),
 ("pendencies", "Pendências técnicas", "pendencias", "Dados ausentes ou inconsistentes"),
 ("val_reprovada", "Validação reprovada", "desenvolvimento?flag=val_reprovada", "Itens com validação reprovada"),
 ("oem_codes", "Códigos OEM relacionados", "pesquisa?code_type=oem", "Códigos OEM distintos"),
 ("applications", "Aplicações cadastradas", "aplicacoes", "Veículo, modelo, ano e eixo"),
 ("drawings", "Códigos com desenho", "desenhos", "Desenho vigente cadastrado"),
 ("imports", "Bases importadas", "fontes", "Planilhas já importadas"),
]

PRIMARY = ["metas", "pedidos-aberto", "vendas", "estoque", "garantia"]     # menu fixo da sidebar (Metas & Validação · Pedidos em Aberto · Vendas (Curva A) · Estoque · Garantia)
# Menu na ordem do FLUXO do produto: desenvolve → compra amostra → entra no catálogo → compra/importa → vende (a numeração dos grupos mostra a ordem)
MENU = [("Visão geral", ["dashboard", "brands"]),
        ("1 · Desenvolvimento", ["desenvolvimento", "redesenvolvimento", "validacao", "desenhos", "damping", "monitoramento-ipi"]),
        ("2 · Amostras", ["amostras", "envio"]),
        ("3 · Catálogo", ["pesquisa", "produtos", "aplicacoes", "lados", "comparacao", "cobertura", "anomalias"]),
        ("4 · Compras", ["fob"]),
        ("Dados", ["atualizacao", "importacao", "fontes", "pendencias"])]
_NAMES = {"pesquisa": "Pesquisa de amortecedores", "aplicacoes": "Aplicações veiculares", "comparacao": "Comparação técnica", "desenvolvimento": "Desenvolvimento", "redesenvolvimento": "Redesenvolvimento"}

@app.context_processor
def inject():
    byslug = {p[0]: p for p in PAGES}
    return {"pages": PAGES, "primary": [byslug[s] for s in PRIMARY], "tw_local": os.path.exists(os.path.join(app.root_path, "static", "vendor", "tailwind.js")), "menu": [(t, [byslug[s] for s in ss if s in byslug]) for t, ss in MENU],
            "cfg_page": byslug.get("configuracoes"), "status_defs": statuses.public(), "regras_slugs": regras_telas.slugs()}

@app.get("/api/regras-telas")
def api_regras_telas(): return jsonify(regras_telas.lista())          # etapa 21: os textos de regra das telas ficam em Configurações › Regras das telas

_memo = {}
def _ate_o_banco_mudar(nome, f, *chave):
    """Etapa 22: guarda o resultado até o banco mudar (qualquer gravação: sincronização, importação ou edição no app) ou o dia virar.
    Antes o menu recalculava a cada 20 s e o Dashboard a cada abertura (≈ 0,6 s e 1,6 s no banco real)."""
    import datetime
    k = (db.versao(), datetime.date.today(), *chave); m = _memo.get((nome, *chave))
    if m and m[0] == k: return m[1]
    v = f(); _memo[(nome, *chave)] = (k, v); return v

def _menu_counts():
    return _ate_o_banco_mudar("menu", lambda: {"envio": queries.q1("SELECT COUNT(*) n FROM sample_shipments WHERE status='pendente_projeto'")["n"], "amostras": purchases.pending({})["summary"]["total"],
                                               "pendencias": queries.q1("SELECT COUNT(*) n FROM pendencies WHERE status='aberta'")["n"]})
@app.get("/api/menu/counts")
def api_menu_counts(): return jsonify(_menu_counts())

def _aquecer():
    """Calcula menu e Dashboard antes de alguém abrir (ao iniciar o app e ao fim de cada sincronização): a 1ª abertura já sai do cache."""
    try: _menu_counts(); _dashboard()
    except Exception: pass
    try: validacao.familias(); validacao.pendentes_rd("rd")          # etapa 24: modelos F-008 e pendentes de validação prontos antes da 1ª abertura
    except Exception: pass

@app.get("/favicon.ico")
def favicon():
    # um ícone só na aba, em todas as páginas e no login (pedido do usuário em 26/11/2026): o logo ShockAbsorberData.ico; o favicon.svg não é mais ligado
    r = send_file(os.path.join(app.root_path, "static", "img", "ShockAbsorberData.ico"), mimetype="image/x-icon"); r.headers["Cache-Control"] = "public, max-age=3600"; return r

@app.route("/")
def home():
    return render_template("home.html", s=db.stats(), user=auth.current_user())

@app.route("/<slug>")
def page(slug):
    if slug == "equivalencias":         # tela antiga: agora é a aba «Sugestões de equivalência» de Anomalias (links e favoritos antigos continuam valendo)
        from flask import redirect
        from urllib.parse import urlencode
        return redirect("/anomalias?" + urlencode({**request.args.to_dict(), "tab": "sugestoes"}))
    p = next((x for x in PAGES + HIDDEN if x[0] == slug), None)
    if not p: abort(404)
    return render_template("page.html", cur=p, cards=CARDS, user=auth.current_user(), tw_page=True)

@app.get("/api/stats")
def api_stats(): return jsonify(db.stats())

@app.get("/api/quick-search")
def api_quick():
    q = request.args.get("q", "").strip()
    return jsonify(db.quick_search(q) if len(q) >= 2 else [])


# ---- Importação: upload, abas e prévia (nada é gravado no banco nesta etapa) ----
def _upload_path(fid):
    if not re.fullmatch(r"[0-9a-f]{32}", fid or ""): abort(400)
    m = glob.glob(os.path.join(UPLOADS, fid + "__*"))
    if not m: abort(404)
    return m[0]

@app.post("/api/import/upload")
def api_upload():
    f = request.files.get("file")
    if not f or not f.filename.lower().endswith((".xlsx", ".xls", ".csv")):
        return jsonify(error="Selecione um arquivo .xlsx, .xls ou .csv."), 400
    os.makedirs(UPLOADS, exist_ok=True)
    fid = uuid.uuid4().hex; name = re.sub(r"[^\w.\- ]", "_", os.path.basename(f.filename))
    path = os.path.join(UPLOADS, f"{fid}__{name}"); f.save(path)
    try: sheets = importer.list_sheets(path)
    except Exception as e:
        os.remove(path); return jsonify(error=f"Não foi possível abrir o arquivo: {e}"), 400
    return jsonify(file_id=fid, name=name, sheets=sheets, categories=CATEGORIES)

@app.get("/api/import/preview")
def api_preview():
    path = _upload_path(request.args.get("file_id")); sheet = request.args.get("sheet") or None
    try: p = importer.preview(path, sheet)
    except Exception as e: return jsonify(error=f"Erro ao ler a planilha: {e}"), 400
    p["fields"] = list(importer.ALIASES); return jsonify(p)

@app.post("/api/import/run")
def api_run():
    d = request.get_json(force=True); path = _upload_path(d.get("file_id")); fname = os.path.basename(path).split("__", 1)[1]
    confirm = bool(d.get("confirm")); backup = None
    if confirm and os.path.exists(db.DB_PATH):  # backup ANTES de gravar
        os.makedirs(os.path.join(db.BASE, "backups"), exist_ok=True)
        backup = os.path.join("backups", "pre_import_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".db")
        shutil.copy2(db.DB_PATH, os.path.join(db.BASE, backup))
    try: res = loaders.run(path, d.get("sheet"), d.get("mapping"), d.get("category"), fname, confirm, "overwrite" if d.get("policy") == "overwrite" else "keep")
    except ValueError as e: return jsonify(error=str(e)), 400
    except Exception as e: return jsonify(error=f"Erro na importação; o banco foi preservado. Detalhe: {e}"), 500
    res["backup"] = backup; return jsonify(res)

# ---- Atualização de dados: lê as planilhas, compara com o banco e insere só o que falta ----
@app.post("/api/update/check")
def api_upd_check():
    try:
        if request.form.get("folder"): files, tok = updater.folder_files(), "folder"
        else:
            tok, files = updater.stash(request.files.getlist("files"))
            if not files: return jsonify(error="Selecione planilhas .xlsx, .xls ou .csv."), 400
        if not files: return jsonify(error="A pasta bases_exemplo está vazia ou não existe."), 400
        res = updater.run(files, confirm=False); res["token"] = tok; return jsonify(res)
    except Exception as e: return jsonify(error=f"Erro ao verificar: {e}"), 500
@app.post("/api/update/apply")
def api_upd_apply():
    tok = (request.get_json(force=True) or {}).get("token")
    files = updater.folder_files() if tok == "folder" else updater.stashed(tok)
    if not files: return jsonify(error="Verificação expirada. Envie as planilhas novamente."), 400
    try: res = updater.run(files, confirm=True)
    except Exception as e: return jsonify(error=f"Erro na atualização; o banco foi preservado. Detalhe: {e}"), 500
    if tok != "folder": updater.discard(tok)
    return jsonify(res)

@app.get("/api/sources/<int:sid>/rows")
def api_src_rows(sid):
    import json
    s = queries.q1("SELECT id,name,notes FROM sources WHERE id=?", (sid,))
    if not s: abort(404)
    cols = (json.loads(s["notes"]) if s["notes"] and s["notes"].startswith("{") else {}).get("columns", [])
    page = max(1, int(request.args.get("page") or 1)); tot = queries.q1("SELECT COUNT(*) n FROM generic_rows WHERE source_id=?", (sid,))["n"]
    rows = [json.loads(r["payload"]) for r in queries.q("SELECT payload FROM generic_rows WHERE source_id=? ORDER BY row_no,id LIMIT 100 OFFSET ?", (sid, (page - 1) * 100))]
    return jsonify(name=s["name"], columns=cols, rows=rows, total=tot, page=page, size=100)
@app.get("/api/sources/<int:sid>/export.xlsx")
def api_src_xlsx(sid):
    import json
    from openpyxl import Workbook
    s = queries.q1("SELECT name,notes FROM sources WHERE id=?", (sid,))
    if not s: abort(404)
    cols = (json.loads(s["notes"]) if s["notes"] and s["notes"].startswith("{") else {}).get("columns", [])
    wb = exporter.Workbook(); wb.remove(wb.active)
    exporter._sheet(wb, "Dados", cols, [[json.loads(r["payload"]).get(c, "") for c in cols] for r in queries.q("SELECT payload FROM generic_rows WHERE source_id=? ORDER BY row_no,id", (sid,))])
    base = re.sub(r"\.(xlsx?|csv)", "", s["name"], flags=re.I)
    return send_file(exporter._finish(wb, {"Fonte": s["name"]}), as_attachment=True, download_name=exporter.friendly_name("fontes").replace("Fontes e histórico", "Dados avulsos"), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ---- Lados e Envio de amostra ----
@app.get("/api/sides")
def api_sides(): return jsonify(sides.listing(request.args.to_dict()))
@app.get("/api/shipments")
def api_ship_list(): return jsonify(shipments.listing(request.args.to_dict()))
@app.post("/api/shipments")
def api_ship_new():
    try: return jsonify(id=shipments.create(request.get_json(force=True) or {}))
    except ValueError as e: return jsonify(error=str(e)), 400
@app.put("/api/shipments/<int:sid>")
def api_ship_upd(sid): shipments.update_one(sid, request.get_json(force=True) or {}); return jsonify(ok=True)
@app.delete("/api/shipments/<int:sid>")
def api_ship_del(sid): shipments.delete(sid); return jsonify(ok=True)
@app.post("/api/shipments/send")
def api_ship_send():
    b = request.get_json(force=True) or {}
    try: return jsonify(updated=shipments.mark_sent([int(i) for i in b.get("ids", [])], b.get("supplier"), b.get("date"), b.get("tracking"), b.get("notes")))
    except ValueError as e: return jsonify(error=str(e)), 400
@app.post("/api/shipments/status")
def api_ship_status():
    b = request.get_json(force=True) or {}
    try: return jsonify(updated=shipments.set_status([int(i) for i in b.get("ids", [])], b.get("status")))
    except ValueError as e: return jsonify(error=str(e)), 400
@app.put("/api/supplier-ex")
def api_sup_ex():
    b = request.get_json(force=True) or {}
    try: shipments.set_ex(b.get("supplier"), b.get("ex_code"), b.get("full_name")); return jsonify(ok=True)
    except ValueError as e: return jsonify(error=str(e)), 400

# ---- Compras pendentes e Brands (as pendências de DES / R-D vêm só do servidor: etapa 20 · Q3) ----
@app.get("/api/purchases/pending")
def api_pend_buy(): return jsonify(purchases.pending(request.args.to_dict()))
@app.get("/api/brands")
def api_brands(): return jsonify(brands.summary())
@app.get("/api/brands/<brand>/items")
def api_brand_items(brand): return jsonify(brands.items(brand.upper(), request.args.to_dict()))
@app.post("/api/brands/vinculo")
def api_brand_link():
    """Etapa 22: liga um item de outra marca aos códigos PERFECT relativos (conjunto completo; vazio = sem relação). Body: code, codigos. → {anterior, codigos}"""
    d = request.get_json(force=True) or {}
    try: return jsonify(brands.vincular(d.get("code"), d.get("codigos") or [], (auth.current_user() or {}).get("username")))
    except ValueError as e: return jsonify(error=str(e)), 400
@app.post("/api/brands/vinculo/desfazer")
def api_brand_link_undo():
    d = request.get_json(force=True) or {}; brands.desvincular(d.get("code"), d.get("anterior")); return jsonify(ok=True)

# ---- Desenhos: qualquer formato; nome do arquivo => código + revisão; cadastros mostram só a revisão vigente ----
@app.get("/api/drawings")
def api_drw_list():
    drawings.relink(); return jsonify(drawings.gallery(request.args.to_dict()))
@app.get("/api/drawings/stats")
def api_drw_stats(): return jsonify(drawings.stats(request.args.get("kind", "desenho")))
@app.get("/api/drawings/lookup")
def api_drw_lookup(): return jsonify(drawings.lookup([c for c in request.args.get("codes", "").split(",") if c], request.args.get("kind", "desenho")))
@app.get("/api/drawings/code/<path:code>")
def api_drw_detail(code):
    d = drawings.detail(code, request.args.get("kind", "desenho"))
    return (jsonify(d), 200) if d else (jsonify(error="Sem desenho cadastrado."), 404)
@app.get("/api/drawings/file/<int:fid>")
def api_drw_file(fid):
    f, p = drawings.file_path(fid)
    if not f: abort(404)
    inline = f["ext"] in drawings.INLINE and not request.args.get("download")
    r = send_file(p, as_attachment=not inline, download_name=f["filename"], mimetype="image/svg+xml" if f["ext"] == ".svg" else None)
    r.headers["X-Content-Type-Options"] = "nosniff"
    if f["ext"] != ".pdf": r.headers["Content-Security-Policy"] = "sandbox; default-src 'none'; style-src 'unsafe-inline'; img-src data:"   # PDF precisa do leitor do navegador (sem sandbox)
    return r
@app.get("/api/drawings/thumb/<int:fid>")
def api_drw_thumb(fid):
    t = drawings.thumb(fid, 1400 if request.args.get("big") else 560)
    if not t: abort(404)
    r = send_file(t, mimetype="image/jpeg"); r.headers["Cache-Control"] = "public, max-age=86400"; return r
@app.post("/api/drawings/check")
def api_drw_check():
    ups = [f for f in request.files.getlist("files") if f.filename]
    if not ups: return jsonify(error="Selecione os arquivos de desenho."), 400
    tok, man = drawings.stash(ups, request.form.get("kind", "desenho"))
    items = drawings.plan(man); return jsonify(token=tok, kind=man["kind"], zips=man.get("zips", []), warnings=man.get("warnings", []), items=[{k: v for k, v in i.items() if k not in ("path", "sha")} for i in items])
@app.post("/api/drawings/apply")
def api_drw_apply():
    b = request.get_json(force=True) or {}; man = drawings.stashed(b.get("token"))
    if not man: return jsonify(error="Verificação expirada. Envie os arquivos novamente."), 400
    try: res = drawings.apply(man, b.get("overrides") or {})
    except Exception as e: return jsonify(error=f"Não foi possível gravar os desenhos: {e}"), 500
    drawings.discard(b.get("token")); return jsonify(res)
@app.post("/api/drawings/file/<int:fid>/assign")
def api_drw_assign(fid):
    b = request.get_json(force=True) or {}
    try: drawings.assign(fid, b.get("codes"), b.get("rev"))
    except ValueError as e: return jsonify(error=str(e)), 400
    return jsonify(ok=True)
@app.delete("/api/drawings/file/<int:fid>")
def api_drw_del(fid): return jsonify(ok=drawings.delete_file(fid))

# ---- Consulta, fichas, comparação, equivalências, pendências, fontes, backup, amostras ----
def admin_only():
    if not auth.is_admin(): abort(403, description="Somente administradores.")
@app.errorhandler(403)
def _forbidden(e): return (jsonify(error=getattr(e, "description", "Acesso negado.")), 403) if request.path.startswith("/api/") else (e.description, 403)
@app.errorhandler(Exception)
def _unexpected(e):
    """Erro inesperado numa rota /api/: devolve JSON legível (e registra no log) em vez de uma página HTML de erro 500."""
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException): return e
    app.logger.exception("Erro em %s", request.path)
    if request.path.startswith("/api/"): return jsonify(error=f"Erro interno: {e.__class__.__name__}: {e}"), 500
    raise e
A = lambda: request.args.to_dict()
@app.get("/api/products")
def api_products(): return jsonify(queries.products(A()))
@app.get("/api/products/facets")
def api_products_facets(): return jsonify(queries.product_facets())
@app.get("/api/products/<int:pid>")
def api_ficha(pid):
    d = queries.ficha(pid) or abort(404); code = (d.get("product") or d).get("perfect_code") if isinstance(d, dict) else None
    if code: d["sales"] = analytics.sales_of(code); d["stock"] = analytics.stock_of(code); d["purchases"] = analytics.purchases_of(code)
    return jsonify(d)
@app.get("/api/item/<path:code>")
def api_item(code):
    import item
    return jsonify(item.ficha(code) or abort(404))
@app.get("/api/cobertura")
def api_cobertura():
    """Cobertura de concorrentes (etapa 17/18): tab=catalogo (padrão), desenvolvimento ou cofap; filtros e atalhos com contagem = lista."""
    import cobertura
    a = request.args.to_dict(); fn = {"desenvolvimento": cobertura.desenvolvimento, "cofap": cobertura.cofap}.get(a.get("tab"), cobertura.catalogo)
    return jsonify(fn(a, a.get("page")))
@app.post("/api/cobertura/cross")
def api_cobertura_cross():
    """Etapa 19 · Q7: corrige o «Nosso código» de uma referência de concorrente (vale sobre o CrossCatalogo e o servidor). Body: concorrente, referencia e
    de/para (troca um código) ou codigos (conjunto completo). → {anterior, codigos} — «anterior» serve para o «Desfazer»."""
    import cobertura
    d = request.get_json(force=True) or {}
    try: return jsonify(cobertura.corrigir(d.get("concorrente"), d.get("referencia") or "", d.get("de"), d.get("para"), d.get("codigos"), (auth.current_user() or {}).get("username")))
    except ValueError as e: return jsonify(error=str(e)), 400
@app.post("/api/cobertura/cross/desfazer")
def api_cobertura_cross_undo():
    import cobertura
    d = request.get_json(force=True) or {}; cobertura.desfazer(d.get("concorrente"), d.get("referencia") or "", d.get("anterior")); return jsonify(ok=True)
@app.get("/item-id/<int:pid>")
def item_by_id(pid):
    """Links antigos de ficha (data-ficha = id do produto) → página do item pelo código."""
    from flask import redirect
    from urllib.parse import quote
    p = queries.q1("SELECT perfect_code FROM products WHERE id=?", (pid,)) or abort(404)
    return redirect("/item/" + quote(p["perfect_code"]))
@app.get("/item/<path:code>")
def item_page(code):
    """Página do item (etapa 17 · Q9): aberta pela Pesquisa e por qualquer código clicável."""
    code = re.sub(r"\s+", "", code).upper()
    return render_template("page.html", cur=("item", f"Item {code}", "amortecedor", 17), cards=CARDS, user=auth.current_user(), tw_page=True)
@app.get("/api/compare")
def api_compare(): return jsonify(queries.compare([int(i) for i in re.findall(r"\d+", request.args.get("ids", ""))]))
@app.get("/api/applications")
def api_apps(): return jsonify(queries.applications(A()))
@app.get("/api/pendencies")
def api_pend(): return jsonify(queries.pendencies(A()))
@app.post("/api/pendencies/<int:i>")
def api_pend_set(i):
    s = (request.get_json(force=True) or {}).get("status")
    if s not in ("aberta", "resolvida", "ignorada"): abort(400)
    queries.run("UPDATE pendencies SET status=? WHERE id=?", (s, i)); return jsonify(ok=True)
@app.post("/api/pendencies/<int:i>/apply")
def api_pend_apply(i):          # conflito: grava no produto o valor que veio da planilha (clique do usuário) e resolve
    try: return jsonify(queries.pendency_apply(i))
    except ValueError as e: return jsonify(error=str(e)), 400
@app.get("/api/duplicates")
def api_dups(): return jsonify(queries.duplicates())
@app.get("/api/history")
def api_hist(): return jsonify(queries.history())
@app.post("/api/sources/<int:i>")
def api_src(i):
    pr = int((request.get_json(force=True) or {}).get("priority", 5)); queries.run("UPDATE sources SET priority=? WHERE id=?", (max(1, min(pr, 9)), i)); return jsonify(ok=True)
def _eqf():
    g = request.args; lst = lambda k: [x for v in g.getlist(k) for x in v.split("|") if x]          # crit/dif/miss: repetidos (crit=a&crit=b) ou juntos por «|» (URL da tela)
    return dict(status=g.get("status") or None, conf=g.get("confidence") or None, qtxt=g.get("q") or None, crit=lst("crit"), dif=lst("dif"), miss=lst("miss"), diff=g.get("diff") or None, minscore=g.get("minscore") or None)
@app.get("/api/anomalies")
def api_anomalies():
    import anomalias
    q = request.args.get("q", ""); tab = request.args.get("tab") or "familia"
    if tab == "protheus":
        f = {k: request.args.get(k) for k in anomalias.PROT_FILTROS if request.args.get(k)}
        return jsonify(rows=anomalias.com_itens(tab, anomalias.protheus(q, f)), counts=anomalias.counts(q), atalhos=anomalias.protheus_counts(q, f), tab=tab)
    tab = tab if tab in anomalias.TABS else "familia"
    return jsonify(rows=anomalias.com_itens(tab, anomalias.TABS[tab](q)), counts=anomalias.counts(q), tab=tab)
@app.get("/api/anomalies/export.xlsx")
def api_anomalies_xlsx():
    import anomalias
    from flask import send_file
    bio, _ = anomalias.export_xlsx(request.args.get("q", ""))
    return send_file(bio, as_attachment=True, download_name=exporter.friendly_name("anomalias", {"q": request.args.get("q")}), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
@app.get("/api/equivalences")
def api_eq(): return jsonify(equivalence.listing(page=int(request.args.get("page") or 1), **_eqf()))
@app.get("/api/equivalences/export.xlsx")
def api_eq_xlsx():
    from flask import send_file
    bio, n = equivalence.export_xlsx(**_eqf())
    return send_file(bio, as_attachment=True, download_name=exporter.friendly_name("equivalencias", {"status": request.args.get("status"), "q": request.args.get("q")}), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
@app.post("/api/equivalences/generate")
def api_eq_gen(): return jsonify(equivalence.generate())
@app.post("/api/equivalences/<int:i>")
def api_eq_set(i):
    s = (request.get_json(force=True) or {}).get("status")
    if s not in ("pendente", "aprovada", "rejeitada"): abort(400)
    queries.run("UPDATE equivalence_suggestions SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (s, i)); return jsonify(ok=True)
@app.get("/api/samples")
def api_samples(): return jsonify(queries.samples(A()))
@app.get("/api/samples/prefill")
def api_sample_prefill():
    code = request.args.get("code", ""); d = queries.sample_prefill(code); d.update(purchases.for_code(d.get("code") or code)); return jsonify(d)
@app.get("/api/samples/codes")
def api_sample_codes():
    """Sugestões do campo «Código PERFECT» do pedido de amostra: códigos AMD de Desenvolvimento/Redesenvolvimento e do catálogo (etapa 19 · Q3: pedido manual de item já desenvolvido)."""
    t = "%" + (request.args.get("q") or "").strip().upper() + "%"
    return jsonify(rows=queries.q("""SELECT c perfect_code, MAX(d) description FROM (SELECT upper(code) c, description d FROM rd_projects UNION ALL SELECT upper(perfect_code), description FROM products)
                                     WHERE c LIKE 'AMD%' AND (c LIKE ? OR upper(coalesce(d,'')) LIKE ?) GROUP BY c ORDER BY 1 LIMIT 8""", (t, t)))
@app.post("/api/samples")
def api_sample_save():
    d = request.get_json(force=True) or {}
    old = queries.q1("SELECT perfect_code FROM sample_orders WHERE id=?", (d["id"],)) if d.get("id") else None
    if not old or purchases._base(old.get("perfect_code")) != purchases._base(d.get("perfect_code")):     # pedido novo ou código trocado: só PERFECT em desenvolvimento
        err = purchases.code_problem(d.get("perfect_code"))
        if err: return jsonify(error=err), 400
    oid = queries.sample_save(d); shipments.sync(); return jsonify(id=oid)   # etapa «Chegou» gera o envio «Pendente projeto»
@app.delete("/api/samples/<int:i>")
def api_sample_del(i): queries.run("DELETE FROM sample_orders WHERE id=?", (i,)); return jsonify(ok=True)
@app.get("/api/backups")
def api_bk(): return jsonify(backups=queries.backups(), db=db.DB_PATH, size=os.path.getsize(db.DB_PATH) if os.path.exists(db.DB_PATH) else 0)
@app.post("/api/backups")
def api_bk_new(): admin_only(); return jsonify(name=queries.backup_create())
@app.post("/api/backups/restore")
def api_bk_restore():
    admin_only()
    try: return jsonify(safety=queries.backup_restore((request.get_json(force=True) or {}).get("name")))
    except ValueError as e: return jsonify(error=str(e)), 400
@app.get("/api/backups/<name>")
def api_bk_dl(name):
    if not re.fullmatch(r"[\w\-]+\.db", name): abort(400)
    return send_from_directory(queries.BK, name, as_attachment=True)

# ---- Damping force ----
@app.get("/api/damping/rules")
def api_dr(): return jsonify(damping.rules())
@app.post("/api/damping/rules")
def api_dr_up():
    f = request.files.get("file")
    if not f or not f.filename.lower().endswith(".xlsx"): return jsonify(error="Envie a planilha da regra (.xlsx)."), 400
    os.makedirs(UPLOADS, exist_ok=True); p = os.path.join(UPLOADS, uuid.uuid4().hex + "__regra.xlsx"); f.save(p)
    try: n, par = damping.load_rules(p, os.path.basename(f.filename))
    except Exception as e: return jsonify(error=str(e)), 400
    finally: os.remove(p)
    return jsonify(points=n, **par)
@app.get("/api/damping/tests")
def api_dt(): return jsonify(damping.listing(request.args.get("q"), request.args.get("res")))
@app.get("/api/damping/tests/<int:i>")
def api_dt1(i): return jsonify(damping.get_test(i) or abort(404))
@app.post("/api/damping/tests")
def api_dt_save():
    try: return jsonify(id=damping.save_test(request.get_json(force=True)))
    except (ValueError, KeyError) as e: return jsonify(error=str(e)), 400
@app.delete("/api/damping/tests/<int:i>")
def api_dt_del(i): queries.run("DELETE FROM damping_tests WHERE id=?", (i,)); return jsonify(ok=True)
@app.get("/api/damping/prefill")
def api_dpre(): return jsonify(damping.prefill(request.args.get("code", "")))
@app.get("/api/damping/tests/<int:i>/export.xlsx")
def api_dt_xlsx(i):
    from flask import send_file
    if not damping.get_test(i): abort(404)
    t = damping.get_test(i); tt = t.get("test", t) if isinstance(t, dict) else {}
    nm = exporter.friendly_name("damping").replace(".xlsx", f" - {tt.get('perfect_code') or tt.get('label') or f'ensaio {i}'}.xlsx")
    return send_file(damping.test_workbook(i), as_attachment=True, download_name=nm, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
@app.get("/api/export/<name>.xlsx")
def api_export(name):
    from flask import send_file
    try: bio, fn = exporter.build(name, request.args.to_dict())
    except ValueError as e: return jsonify(error=str(e)), 400
    return send_file(bio, as_attachment=True, download_name=fn, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ---- Em desenvolvimento (DES) / Em redesenvolvimento (R-D) ----
def _rdk(k): return rd.KINDS.get(k) or abort(404)
@app.get("/api/rd/<kind>")
def api_rd(kind): return jsonify(rd.items(_rdk(kind), A()))
@app.get("/api/rd/<kind>/facets")
def api_rd_f(kind): return jsonify(rd.facets(_rdk(kind), request.args.get("status"), {k: request.args.get(k) for k in ("linha", "marca")}))
@app.get("/api/rd/<kind>/item/<path:code>")
def api_rd_d(kind, code): return jsonify(rd.detail(_rdk(kind), code) or abort(404))
@app.get("/api/filters")
def api_filters(): return jsonify(rd.filter_lists(request.args.get("make") or None))

# ---- Validação de desenho (etapa 24): bancada do R-D e tela do menu; gera o F-008 ----
import validacao
def _val(f):
    """Erros da validação: regra (ValueError) = 400 com a frase para o usuário; validação inexistente = 404."""
    from functools import wraps
    @wraps(f)
    def g(*a, **k):
        try: return f(*a, **k)
        except LookupError as e: return jsonify(error=str(e)), 404
        except ValueError as e: return jsonify(error=str(e)), 400
    return g
def _quem(): return (auth.current_user() or {}).get("username")
@app.get("/api/validacao")
@_val
def api_val_lista(): return jsonify(validacao.listagem(A()))
@app.get("/api/validacao/aba/<kind>")
@_val
def api_val_aba(kind): return jsonify(validacao.aba(kind, A()))
@app.post("/api/validacao")
@_val
def api_val_criar():
    b = request.get_json(force=True) or {}; return jsonify(id=validacao.criar(b.get("kind") or "rd", b.get("code"), _quem()))
@app.get("/api/validacao/<int:vid>")
@_val
def api_val_obter(vid): return jsonify(validacao.obter(vid))
@app.patch("/api/validacao/<int:vid>")
@_val
def api_val_salvar(vid): return jsonify(validacao.salvar(vid, request.get_json(force=True) or {}))
@app.delete("/api/validacao/<int:vid>")
@_val
def api_val_excluir(vid): return jsonify(ok=True, **validacao.excluir(vid))
@app.post("/api/validacao/<int:vid>/desenho/<lado>")
@_val
def api_val_desenho(vid, lado):
    f = request.files.get("file")
    if not f or not f.filename: raise ValueError("Escolha o arquivo do desenho.")
    return jsonify(validacao.desenho(vid, lado, f))
@app.get("/api/validacao/<int:vid>/img/<nome>.png")
def api_val_img(vid, nome):
    tela = request.args.get("tela") == "1"; p = validacao.imagem(vid, nome, tela)
    if not p: abort(404)
    r = send_file(p, mimetype="image/jpeg" if tela else "image/png")
    r.headers["Cache-Control"] = "private, max-age=604800" if request.args.get("u") else "no-store"     # o endereço leva a versão da imagem (img_ver)
    return r
@app.post("/api/validacao/<int:vid>/ler")
@_val
def api_val_ler(vid): return jsonify(validacao.ler(vid))
@app.post("/api/validacao/<int:vid>/concluir")
@_val
def api_val_concluir(vid): return jsonify(validacao.gerar(vid, (request.get_json(force=True) or {}).get("decisao"), _quem()))
@app.post("/api/validacao/<int:vid>/nova")
@_val
def api_val_nova(vid): return jsonify(id=validacao.nova(vid, _quem()))
@app.post("/api/validacao/<int:vid>/preparar-par")          # próximo update: validação concluída antes da correção do par pela aplicação
@_val
def api_val_preparar_par(vid): return jsonify(validacao.preparar_par(vid, _quem()) or {})
@app.get("/api/validacao/<int:vid>/arquivo/<tipo>")
@_val
def api_val_arquivo(vid, tipo):
    p, nome = validacao.arquivo_gerado(vid, tipo)
    if not p: abort(404)
    return send_file(p, as_attachment=True, download_name=nome)

# ---- Plotly servido localmente (pip install plotly) — sem CDN, funciona atrás do firewall da empresa ----
@app.get("/vendor/plotly.min.js")
def vendor_plotly():
    try:
        import plotly, os as _os
        p = _os.path.join(_os.path.dirname(plotly.__file__), "package_data", "plotly.min.js")
        if _os.path.isfile(p): r = send_file(p, mimetype="application/javascript"); r.headers["Cache-Control"] = "public, max-age=86400"; return r
    except ImportError: pass
    abort(404)

# ---- Servidor SQL: sincronização, status e histórico ----
def _after_sync(result):
    try: shipments.sync(); goals.ensure(); _aquecer()
    except Exception: pass
@app.get("/api/pipeline/status")
def api_pipe_status(): return jsonify(data_pipeline.status())
@app.post("/api/pipeline/sync")
def api_pipe_sync():
    st = data_pipeline.status()
    if not st["configured"]: return jsonify(error="Preencha DEV_DB_USER e DEV_DB_PASSWORD no arquivo .env e reinicie o sistema."), 400
    started = data_pipeline.sync_async(on_done=_after_sync, conn_factory=app.config.get("PIPELINE_CONN_FACTORY"))
    return jsonify(started=started, running=True, message=None if started else "Já existe uma sincronização em andamento.")
@app.get("/api/pipeline/runs")
def api_pipe_runs():
    runs = queries.q("SELECT id,started_at,finished_at,status,baseline,source_rows,items,events,new_items,removed_items,error,warnings FROM dev_sync_runs ORDER BY id DESC LIMIT 15")
    ds = queries.q("SELECT dataset,object,rows,status,note,at FROM ds_runs WHERE id IN (SELECT MAX(id) FROM ds_runs GROUP BY dataset) ORDER BY dataset")
    return jsonify(runs=runs, datasets=ds, tracking=goals.tracking_info())

# ---- Configurações de regras (aba Administração) ----
@app.get("/api/settings")
def api_settings():
    admin_only(); return jsonify(only_description=rules.only_desc(), goal_valid_user=rules.valid_user(), goal_basis=rules.goal_basis(), leadtime_meta_dias=__import__("leadtime").meta_dias(), validacao_ia=rules.validacao_ia(),
                                 defaults={"only_description": "AMORTECEDOR", "goal_valid_user": "ITALOC", "goal_basis": "validacao", "leadtime_meta_dias": 180, "validacao_ia": False})
@app.put("/api/settings")
def api_settings_set():
    admin_only(); b = request.get_json(force=True) or {}; u = (auth.current_user() or {}).get("username")
    if "only_description" in b: rules.set_setting("only_description", str(b["only_description"] or "").strip().upper()[:60], u)
    if "goal_valid_user" in b:
        v = str(b["goal_valid_user"] or "").strip().upper()[:40]
        if not v: return jsonify(error="Informe o usuário validador (ex.: ITALOC)."), 400
        rules.set_setting("goal_valid_user", v, u)
    if "goal_basis" in b:
        v = str(b["goal_basis"] or "").strip().lower()
        if v not in ("validacao", "recebido"): return jsonify(error="Base de contagem inválida (use «validacao» ou «recebido»)."), 400
        rules.set_setting("goal_basis", v, u)
    if "leadtime_meta_dias" in b:
        try: v = int(float(b["leadtime_meta_dias"]))
        except (TypeError, ValueError): v = 0
        if not 30 <= v <= 720: return jsonify(error="Meta de lead time inválida (use de 30 a 720 dias; padrão 180 = 6 meses)."), 400
        rules.set_setting("leadtime_meta_dias", str(v), u)
    if "validacao_ia" in b: rules.set_setting("validacao_ia", "1" if str(b["validacao_ia"]).strip().lower() in ("1", "true", "sim", "on") else "0", u)      # etapa 24: leitura pelo Claude (padrão desligada)
    db.rebuild_flags_view(); _memo.clear()
    return jsonify(only_description=rules.only_desc(), goal_valid_user=rules.valid_user(), goal_basis=rules.goal_basis(), leadtime_meta_dias=__import__("leadtime").meta_dias(), validacao_ia=rules.validacao_ia())

# ---- Metas e validações ----
@app.get("/api/goals")
def api_goals():
    y = request.args.get("year"); out = goals.progress(y); out["tracking"] = goals.tracking_info(); out["years"] = sorted({datetime.date.today().year, out["year"], *[r["year"] for r in queries.q("SELECT DISTINCT year FROM goals")]}, reverse=True)
    return jsonify(out)
@app.put("/api/goals")
def api_goal_set():
    admin_only(); b = request.get_json(force=True) or {}
    try: goals.set_goal(b.get("year"), b.get("kind"), b.get("target"), b.get("prior_done"), b.get("note"))
    except ValueError as e: return jsonify(error=str(e)), 400
    return jsonify(goals.progress(b.get("year")))
@app.get("/api/goals/rd-validations")
def api_goal_rd_val(): return jsonify(goals.rd_validations(request.args.get("year")))
@app.get("/api/goals/validacoes")          # próximo update: DES e R-D numa lista, com os meses de cada validação (clique no gráfico de Metas filtra o mês)
def api_goal_validacoes(): return jsonify(goals.validacoes_ano(request.args.get("year")))
@app.get("/api/goals/events")
def api_goal_events(): return jsonify(goals.events_list(request.args.get("year"), request.args.get("kind"), max(request.args.get("limit", 80, type=int), 1)))
@app.get("/api/validations/pending")
def api_val_pending(): return jsonify(goals.pending_validations())
@app.post("/api/validations")
def api_val_send():
    b = request.get_json(force=True) or {}; u = auth.current_user()
    try: return jsonify(id=goals.send_validation(b.get("code"), b.get("kind"), (u or {}).get("username"), b.get("note"), b.get("sent_at")))
    except ValueError as e: return jsonify(error=str(e)), 400
@app.delete("/api/validations/<int:vid>")
def api_val_undo(vid): goals.undo_validation(vid); return jsonify(ok=True)

# ---- Dashboard, vendas e estoque ----
def _dashboard(y=""):
    def calc():
        funnel, fl, tot = {}, {}, {}
        for k in (kinds.DES, kinds.RD):       # cada barra do funil = itens distintos no status = total da lista DES/R-D com ?status= (test_24)
            fc = rd.facets(k); rank = data_pipeline.STATUS_RANK
            funnel[k] = sorted([{"status": r["v"], "n": r["n"]} for r in fc["status"]], key=lambda r: rank.get(r["status"], -1)); fl[k] = fc["flags"]; tot[k] = fc["total"]
        return dict(stats=db.stats(), goals=goals.progress(y or None), funnel=funnel, flags=fl, totals=tot, sales=analytics.sales_summary(), stock=analytics.stock_summary(),
                    system=queries.q("SELECT coalesce(system_type,'nd') s, COUNT(*) n FROM products GROUP BY 1"))
    return _ate_o_banco_mudar("dashboard", calc, y or "")
@app.get("/api/dashboard")
def api_dashboard():
    # pipeline (sincronização em curso) e rastreio são lidos na hora: mudam sem gravar no banco
    return jsonify(**_dashboard(request.args.get("year") or ""), tracking=goals.tracking_info(), pipeline=data_pipeline.status(), groups=statuses.public())
@app.get("/api/analytics/sales")
def api_sales(): return jsonify(analytics.sales_summary(int(request.args.get("months") or 12), int(request.args.get("top") or 10)))

# ---- Novos módulos: validações (metas), pedidos em aberto, vendas (Curva A), garantia, FOB ----
@app.get("/api/metas/validacoes")
def api_metas_valid(): return jsonify(metas.dashboard(request.args.get("year")))

@app.get("/api/pedidos-em-aberto")
def api_open_orders():
    a = request.args
    try: return jsonify(orders.payload(a.get("q"), a.get("fornecedor"), a.get("status"), a.get("recebidos") == "1", a.get("page") or 1, a.get("size") or 200, a.get("tipo") or "compra"))
    except ValueError as e: return jsonify(error=str(e)), 400

@app.post("/api/vendas/conciliar")
def api_vendas_conciliar():
    import conciliacao
    f = request.files.get("file")
    if not f or not f.filename: return jsonify(error="Envie o export do BI (VENDA_POR_SKU .xlsx ou .csv) no campo «file»."), 400
    try: return jsonify(conciliacao.vendas(f.stream, f.filename))
    except ValueError as e: return jsonify(error=str(e)), 400
    except Exception as e: return jsonify(error=f"Arquivo ilegível ({e.__class__.__name__}). Envie .xlsx ou .csv."), 400

@app.get("/api/pedidos/leadtime")
def api_leadtime():
    import leadtime
    try: return jsonify(leadtime.payload())
    except ValueError as e: return jsonify(error=str(e)), 400

@app.get("/api/pedidos/previsao/acerto")
def api_previsao_acerto():      # previsão × realizado (etapa 16 · A2)
    import leadtime
    return jsonify(leadtime.acerto())
@app.get("/api/pedidos/previsao/linhas")
def api_previsao_linhas():      # lista da previsão com filtros e atalhos (etapa 16 · A3/A4)
    import leadtime
    return jsonify(leadtime.previsao_linhas({k: request.args.get(k, "") for k in ("etapa", "fornecedor", "alerta", "q", "page")}))
@app.get("/api/pedidos/previsao")
def api_previsao():
    """Previsão de embarques e chegadas (etapas produção → mar → desembaraço medidas no histórico de cada fornecedor)."""
    import leadtime
    return jsonify(leadtime.forecast_cached())

@app.get("/api/vendas/resumo")
def api_vendas_resumo():
    return jsonify(curva_abc.overview(request.args.get("months") or 24, request.args.get("linhas")))

@app.get("/api/inmetro")          # update 8: aba Inmetro de Produtos e códigos
def api_inmetro():
    import inmetro
    f = {k: request.args.get(k, "") for k in ("sit", "familia", "forn", "q")}
    return jsonify(inmetro.tela(f, request.args.get("page", 1, type=int)))

# ---- update 9 · Monitoramento de IPI (ipi.py) ----
@app.get("/api/ipi")
def api_ipi(): return jsonify(ipi.publico({k: request.args.get(k, "") for k in ("sit", "ipi", "q")}))

@app.get("/api/ipi/aprovador")          # tela do perfil «Aprovador IPI»: só leitura
def api_ipi_aprovador():
    d = ipi.publico({})          # os mesmos dados da tela Monitoramento de IPI (pedido do usuário, 27/11/2026)
    return jsonify(kpi=d["kpi"], aprovadores=d["aprovadores"], itens=d["itens"], proximos=d["proximos"], resposta=d["resposta"], envio=d["envio_info"], usuario=(auth.current_user() or {}).get("username"))

@app.get("/api/ipi/aprovador/planilha.xlsx")          # «Baixar planilha» da tela dos aprovadores: os itens de agora no modelo IPI.xlsx
def api_ipi_aprovador_planilha():
    bio, nome = ipi.planilha_atual()
    return send_file(bio, as_attachment=True, download_name=nome, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.post("/api/ipi/envio")
def api_ipi_envio():
    admin_only()
    try: return jsonify(ipi.preparar_envio(_quem()))
    except ValueError as e: return jsonify(error=str(e)), 400

@app.get("/api/ipi/envio/<int:eid>.xlsx")
def api_ipi_envio_xlsx(eid):
    try: bio, nome = ipi.planilha(eid)
    except ValueError as e: return jsonify(error=str(e)), 404
    return send_file(bio, as_attachment=True, download_name=nome, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.post("/api/ipi/envio/<int:eid>/<acao>")
def api_ipi_envio_acao(eid, acao):
    admin_only()
    try:
        if acao == "confirmar": ipi.confirmar_envio(eid)
        elif acao == "cancelar": ipi.cancelar_envio(eid)
        else: abort(404)
    except ValueError as e: return jsonify(error=str(e)), 400
    return jsonify(ok=True)

@app.post("/api/ipi/resposta")          # resposta da aprovadora (lida no Gmail a pedido do usuário, ou colada na tela)
def api_ipi_resposta():
    admin_only(); b = request.get_json(force=True) or {}
    try: return jsonify(ipi.registrar_resposta(b.get("envio_id"), b.get("autor"), b.get("recebido_em"), b.get("texto") or "", _quem()))
    except (ValueError, TypeError) as e: return jsonify(error=str(e)), 400

@app.get("/aprovacao-ipi")
def aprovacao_ipi(): return render_template("aprovacao_ipi.html", user=auth.current_user())

@app.get("/api/vendas/uf")          # update 8: mapa da tela Vendas (peças e R$ por UF + os 10 códigos mais vendidos de cada UF)
def api_vendas_uf():
    try: return jsonify(curva_abc.por_uf(request.args.get("year"), request.args.get("month"), request.args.get("linhas")))
    except ValueError as e: return jsonify(error=str(e)), 400

@app.get("/api/vendas/curva-a")
def api_curva_a():
    try: return jsonify(curva_abc.payload(request.args.get("year"), request.args.get("month"), request.args.get("limit"), request.args.get("linhas")))
    except ValueError as e: return jsonify(error=str(e)), 400

@app.get("/api/estoque")
def api_estoque():              # vendas × estoque (etapa 16 · C2–C4)
    import estoque
    return jsonify(estoque.listing({k: request.args.get(k, "") for k in ("situacao", "classe", "q", "falta", "conta", "page")}))
@app.get("/api/garantias")
def api_garantias():            # tela Garantia: só o servidor (etapa 18 · Q1; garantias.build a cada sincronização); sem dados → available=False
    import garantias
    f = {k: request.args.get(k, "") for k in garantias.FILTROS}
    return jsonify(garantias.summary(f, request.args.get("page", 1, type=int)))

@app.get("/api/fob")
def api_fob_list():
    a = request.args; return jsonify(fob_merge.listing(a.get("q"), a.get("filtro") or "", a.get("page") or 1, a.get("size") or 100))

@app.post("/api/fob/import")
def api_fob_import():
    admin_only(); f = request.files.get("file")
    if not f or not f.filename: return jsonify(error="Envie a planilha FOB (.xlsx ou .csv) no campo «file»."), 400
    p = os.path.join(UPLOADS, "fob_" + uuid.uuid4().hex[:8] + os.path.splitext(f.filename)[1].lower()); os.makedirs(UPLOADS, exist_ok=True); f.save(p)
    try: return jsonify(fob_merge.apply_to_db(p))
    except ValueError as e: return jsonify(error=str(e)), 400
    finally: os.path.exists(p) and os.remove(p)

# ---- Pesquisa de preços na web (Compra de amostras) ----
@app.post("/api/prices/search")
def api_price_search():
    b = request.get_json(force=True) or {}
    try: return jsonify(price_search.search(b.get("refs"), int(b.get("limit") or 5), refresh=bool(b.get("refresh")), strict=b.get("strict", True), fetch=app.config.get("PRICE_FETCH")))
    except ValueError as e: return jsonify(error=str(e)), 400
@app.post("/api/prices/save")
def api_price_save():
    b = request.get_json(force=True) or {}
    try: return jsonify(id=price_search.save_quote(b.get("order_id"), b.get("price"), b.get("link"), b.get("chosen", True)))
    except ValueError as e: return jsonify(error=str(e)), 400

# ---- etapa 24 · próximo update Q1: o sistema roda sem a janela do cmd (pythonw); «Fechar o sistema» no topo encerra o servidor ----
@app.get("/api/sistema")          # update 5: seção «Sistema» de Configurações (o botão «Fechar o sistema» saiu da barra do topo)
def api_sistema():
    log = os.path.join(db.BASE, "data", "app_log.txt")
    return jsonify(aberto_em=datetime.datetime.strptime(ASSET_V, "%Y%m%d%H%M%S").isoformat(timespec="seconds"), endereco=request.host,
                   log="data\\app_log.txt" if os.path.isfile(log) else None, autofechar=bool(app.config.get("AUTOFECHAR")), celular=_celular())

# ---- update 8: fechar o sistema quando a última aba fecha (abas.py) e acesso pelo celular ----
_em_curso = [0]; _em_curso_lock = threading.Lock()
@app.before_request
def _conta_inicio():
    if request.path.startswith("/api/") and not request.path.startswith("/api/aba"):
        with _em_curso_lock: _em_curso[0] += 1
        g._psd_conta = True
@app.teardown_request
def _conta_fim(_exc=None):
    if g.pop("_psd_conta", None):
        with _em_curso_lock: _em_curso[0] -= 1

def _ocupado():
    """Sincronização, importação, backup ou qualquer outra requisição da API em andamento: o fechamento automático espera."""
    return bool(data_pipeline._STATE.get("running")) or _em_curso[0] > 0

@app.post("/api/aba")
def api_aba():
    """Sinal de cada página aberta: {id, ev: "ping" | "saiu"} (saiu vem por sendBeacon). Aba do PC = endereço local."""
    import abas
    b = request.get_json(force=True, silent=True) or {}
    if b.get("ev") == "saiu": abas.saiu(b.get("id"))
    else: abas.ping(b.get("id"), request.remote_addr in ("127.0.0.1", "::1"))
    return ("", 204)

def _enderecos():
    import socket
    try: ips = socket.gethostbyname_ex(socket.gethostname())[2]
    except OSError: ips = []
    return sorted({i for i in ips if not i.startswith("127.")})

def _celular():
    host = app.config.get("HOST_ATIVO") or "127.0.0.1"; porta = app.config.get("PORTA_ATIVA") or 5000
    return {"ligado": rules.acesso_celular(), "ativo": host not in ("127.0.0.1", "localhost", "::1"),
            "enderecos": [f"http://{i}:{porta}" for i in _enderecos()]}

@app.put("/api/sistema/celular")
def api_sistema_celular():
    admin_only(); b = request.get_json(force=True) or {}
    rules.set_setting("acesso_celular", "1" if str(b.get("ligado")).strip().lower() in ("1", "true", "sim", "on") else "0", (auth.current_user() or {}).get("username"))
    return jsonify(_celular())

@app.post("/api/sistema/fechar")
def api_sistema_fechar():
    if app.config.get("TESTING"): return jsonify(ok=True, teste=True)          # nos testes não derruba o processo
    import threading, time
    def _sair():          # 27/11/2026: fechar no meio de uma sincronização deixava a trava e cortava a carga — espera ela terminar (até 15 min)
        t0 = time.time()
        while data_pipeline._STATE.get("running") and time.time() - t0 < 900: time.sleep(1)
        time.sleep(0.6); os._exit(0)
    threading.Thread(target=_sair, daemon=True).start()
    return jsonify(ok=True, espera_sincronizacao=bool(data_pipeline._STATE.get("running")))

def _ja_aberto(porta):
    """Já há um sistema respondendo nesta porta? (abrir de novo só abre o navegador)"""
    import socket
    with socket.socket() as s:
        s.settimeout(0.6)
        return s.connect_ex(("127.0.0.1", porta)) == 0

if __name__ == "__main__":
    import sys, threading, webbrowser
    porta = int(os.environ.get("PORT", 5000)); url = f"http://127.0.0.1:{porta}"
    _sem_janela = sys.stdout is None or sys.stderr is None
    if _sem_janela:          # aberto pelo pythonw (sem janela): as mensagens vão para data\app_log.txt
        os.makedirs(os.path.join(db.BASE, "data"), exist_ok=True)
        _log = open(os.path.join(db.BASE, "data", "app_log.txt"), "a", encoding="utf-8", buffering=1); sys.stdout = sys.stderr = _log
        print(f"\n=== {datetime.datetime.now():%d/%m/%Y %H:%M:%S} · sistema aberto ===")
    if _ja_aberto(porta):
        if os.environ.get("PSD_ABRIR") == "1": webbrowser.open(url)
        print("O sistema já está aberto nesta porta: só abri o navegador."); sys.exit(0)
    if os.environ.get("PSD_SCHEDULER", "on") != "off": data_pipeline.start_scheduler(on_done=_after_sync)      # sincronização diária automática (DEV_SYNC_HOURS, padrão 24)
    threading.Thread(target=_aquecer, daemon=True).start()
    if os.environ.get("PSD_ABRIR") == "1": threading.Timer(1.5, webbrowser.open, (url,)).start()
    host = os.environ.get("HOST") or ("0.0.0.0" if rules.acesso_celular() else "127.0.0.1")      # update 8: «Acesso pelo celular» atende a rede
    # update 8: pelo atalho (pythonw, sem janela) o sistema fecha sozinho quando a última aba fecha; PSD_AUTOFECHAR=0 desliga.
    # update 9: com o acesso pela rede ligado (aprovadores de IPI), não fecha sozinho — os outros aparelhos dependem do app aberto
    if _sem_janela and os.environ.get("PSD_AUTOFECHAR", "1") != "0" and host in ("127.0.0.1", "localhost"):
        import abas
        def _fechar_sozinho(): print(f"{datetime.datetime.now():%d/%m/%Y %H:%M:%S} · última aba fechada: sistema encerrado"); os._exit(0)
        app.config["AUTOFECHAR"] = True; abas.iniciar(_ocupado, _fechar_sozinho)
    app.config.update(HOST_ATIVO=host, PORTA_ATIVA=porta)
    app.run(host=host, port=porta, debug=False)
