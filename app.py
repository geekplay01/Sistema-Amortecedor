"""Perfect Shock Data - rotas Flask."""
from flask import Flask, send_file, Response, render_template, jsonify, request, abort, send_from_directory
import os, re, glob, uuid, shutil, datetime
import database as db, importer, loaders, queries, equivalence, damping, exporter, rd, updater, drawings, purchases, brands, shipments, sides
import kinds, statuses, data_pipeline, goals, analytics, price_search, auth, rules, metas, orders, curva_abc, warranty, fob_merge

data_pipeline.load_env()          # lê o .env (usuário/senha do servidor, chaves do Mercado Livre...)
app = Flask(__name__)
auth.init_app(app)                # login de administrador (desligar só em desenvolvimento: PSD_AUTH=off)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024   # desenhos CAD podem ser grandes
ASSET_V = datetime.datetime.now().strftime("%Y%m%d%H%M%S")   # muda a cada vez que o app abre: o navegador baixa JS/CSS novos (sem Ctrl+F5)

@app.url_defaults
def _asset_version(endpoint, values):
    if endpoint == "static" and "v" not in values and str(values.get("filename", "")).endswith((".js", ".css")): values["v"] = ASSET_V
UPLOADS = os.path.join(db.BASE, 'data', 'uploads')
CATEGORIES = ['Produtos / códigos', 'Aplicações', 'Dimensões técnicas', 'Fornecedores / concorrentes', 'Dados comerciais / logísticos', 'Personalizada']
db.init_db()
shipments.sync()   # envios coerentes com Compra de amostra e os itens em desenvolvimento
goals.ensure()

# slug, rótulo, ícone (path SVG 24x24), etapa em que será implementada
PAGES = [
 ("dashboard", "Dashboard", "M3 13h8V3H3zM13 21h8V11h-8zM3 21h8v-6H3zM13 3v6h8V3z", 1),
 ("pesquisa", "Pesquisa de amortecedores", "M11 4a7 7 0 105 12l4 4 1.5-1.5-4-4A7 7 0 0011 4z", 3),
 ("produtos", "Produtos e códigos", "M4 7l8-4 8 4v10l-8 4-8-4zM4 7l8 4 8-4M12 11v10", 3),
 ("aplicacoes", "Aplicações veiculares", "M5 16l1.5-5h11L19 16M4 16h16v3H4zM7 19v1.5M17 19v1.5", 3),
 ("comparacao", "Comparação técnica", "M8 4v16M16 4v16M3 8h5M16 14h5", 4),
 ("equivalencias", "Equivalências", "M7 7h11l-3-3M17 17H6l3 3", 4),
 ("atualizacao", "Atualização de dados", "M4 12a8 8 0 0114-5l2 2M20 4v5h-5M20 12a8 8 0 01-14 5l-2-2M4 20v-5h5", 2),
 ("lados", "Lados", "M12 3v18M7 7l-4 5 4 5M17 7l4 5-4 5", 3),
 ("envio", "Envio de amostra", "M3 7l9-4 9 4v10l-9 4-9-4zM3 7l9 4 9-4M12 11v10M16 9.5l-8-3.5", 3),
 ("metas", "Metas & Validação", "M12 3a9 9 0 109 9M12 7v5l3 2M16 3h5v5", 1),
 ("pedidos-aberto", "Pedidos em Aberto", "M9 4h6v3H9zM7 5H5v16h14V5h-2M9 12h6M9 16h4", 1),
 ("vendas", "Vendas (Curva A)", "M4 20V10M10 20V4M16 20v-8M22 20H2", 1),
 ("fob", "FOB (preços de compra)", "M12 3v18M16 7.5C16 6 14.5 5 12 5S8 6 8 8s1.5 2.5 4 3 4 1 4 3-1.5 3-4 3-4-1-4-2.5", 2),
 ("garantia", "Garantia", "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6zM9 12l2 2 4-4", 1),
 ("brands", "Brands", "M4 7l8-4 8 4v10l-8 4-8-4zM4 7l8 4 8-4M12 11v10", 1),
 ("desenhos", "Desenhos", "M4 5a2 2 0 012-2h12a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2zM8 8h8M8 12h8M8 16h5", 1),
 ("importacao", "Importação de Excel", "M12 3v12M7 10l5 5 5-5M4 20h16", 2),
 ("desenvolvimento", "Desenvolvimento", "M4 20l4-1 11-11-3-3L5 16zM14 6l3 3", 3),
 ("redesenvolvimento", "Redesenvolvimento", "M4 4v6h6M20 20v-6h-6M20 10a8 8 0 00-14-3M4 14a8 8 0 0014 3", 3),
 ("amostras", "Compra de amostras", "M4 5h2l2 10h9l2-7H7M10 20a1 1 0 100-2 1 1 0 000 2zM17 20a1 1 0 100-2 1 1 0 000 2z", 3),
 ("damping", "Damping force", "M3 12h3l2-6 4 12 3-9 2 3h4", 3),
 ("pendencias", "Pendências de dados", "M12 3l10 18H2zM12 10v5M12 18v.5", 4),
 ("fontes", "Fontes e histórico", "M12 7v5l3 2M3 12a9 9 0 109-9", 2),
 ("configuracoes", "Configurações e backup", "M12 9a3 3 0 100 6 3 3 0 000-6zM19 12l2-1-2-4-2 1-2-1-1-2h-4l-1 2-2 1-2-1-2 4 2 1v2l-2 1 2 4 2-1 2 1 1 2h4l1-2 2-1 2 1 2-4-2-1z", 5),
]
CARDS = [  # chave, rótulo, destino, dica
 ("products", "Total de amortecedores", "produtos", "Produtos PERFECT cadastrados"),
 ("oem_codes", "Códigos OEM relacionados", "pesquisa?code_type=oem", "Códigos OEM distintos"),
 ("applications", "Aplicações cadastradas", "aplicacoes", "Veículo, modelo, ano e eixo"),
 ("des_items", "DESENVOLVIMENTO", "desenvolvimento", "Itens distintos em desenvolvimento (servidor)"),
 ("rd_items", "REDESENVOLVIMENTO", "redesenvolvimento", "Itens distintos em redesenvolvimento (servidor)"),
 ("ship_pendente", "Amostras a enviar", "envio?status=pendente_projeto", "Recebidas, aguardando o projeto para envio ao fornecedor"),
 ("pend_compras", "Pendente compras", "amostras?tab=pendentes", "Itens em desenvolvimento/redesenvolvimento aguardando compra de amostra"),
 ("val_reprovada", "Validação reprovada", "desenvolvimento?flag=val_reprovada", "Itens com validação reprovada (marcação de status)"),
 ("drawings", "Códigos com desenho", "desenhos", "Desenho vigente cadastrado (todas as revisões ficam guardadas)"),
 ("imports", "Bases importadas", "fontes", "Planilhas já importadas"),
 ("pendencies", "Pendências técnicas", "pendencias", "Dados ausentes ou inconsistentes"),
 ("duplicates", "Possíveis duplicidades", "pendencias?tab=dup", "Mesmo código em produtos diferentes"),
 ("equivalences_pending", "Equivalências a validar", "equivalencias", "Sugestões aguardando decisão"),
]

PRIMARY = ["metas", "pedidos-aberto", "vendas", "garantia"]     # menu fixo da sidebar (Metas & Validação · Pedidos em Aberto · Vendas (Curva A) · Garantia)
# Menu na ordem do FLUXO do produto: desenvolve → compra amostra → entra no catálogo → compra/importa → vende (o menu lateral desenha o conector entre as etapas)
MENU = [("Visão geral", ["dashboard", "brands"]),
        ("1 · Desenvolvimento", ["desenvolvimento", "redesenvolvimento", "desenhos", "damping"]),
        ("2 · Amostras", ["amostras", "envio"]),
        ("3 · Catálogo", ["pesquisa", "produtos", "aplicacoes", "lados", "comparacao", "equivalencias"]),
        ("4 · Compras", ["fob"]),
        ("Dados", ["atualizacao", "importacao", "fontes", "pendencias"])]
FLOW_GROUPS = {"1 · Desenvolvimento", "2 · Amostras", "3 · Catálogo", "4 · Compras"}
# Conectores entre telas: de onde a informação vem → esta tela → para onde ela vai (faixa abaixo do título de cada página)
RELATED = {
 "desenvolvimento": (["metas"], ["amostras", "desenhos", "lados"]), "redesenvolvimento": (["metas"], ["amostras", "desenhos", "lados"]),
 "amostras": (["desenvolvimento", "redesenvolvimento"], ["envio", "pedidos-aberto"]), "envio": (["amostras"], ["desenvolvimento"]),
 "produtos": (["atualizacao"], ["lados", "aplicacoes", "vendas"]), "pesquisa": (["produtos"], ["lados", "pedidos-aberto", "vendas"]),
 "lados": (["produtos", "desenvolvimento"], ["pedidos-aberto", "vendas"]), "aplicacoes": (["produtos"], ["lados"]),
 "pedidos-aberto": (["fob", "amostras"], ["vendas", "lados"]), "vendas": (["pedidos-aberto", "produtos"], ["garantia", "lados"]),
 "garantia": (["vendas"], ["redesenvolvimento"]), "metas": (["desenvolvimento", "redesenvolvimento"], []), "fob": (["produtos"], ["pedidos-aberto"]),
 "atualizacao": ([], ["produtos", "lados"]), "equivalencias": (["produtos"], ["pesquisa"]), "desenhos": (["desenvolvimento"], ["envio"]),
}
_NAMES = {"pesquisa": "Pesquisa de amortecedores", "aplicacoes": "Aplicações veiculares", "comparacao": "Comparação técnica", "desenvolvimento": "Desenvolvimento", "redesenvolvimento": "Redesenvolvimento"}

@app.context_processor
def inject():
    byslug = {p[0]: p for p in PAGES}
    rel = lambda slug: tuple([byslug[s] for s in side if s in byslug] for side in RELATED.get(slug, ([], [])))
    return {"pages": PAGES, "primary": [byslug[s] for s in PRIMARY], "tw_local": os.path.exists(os.path.join(app.root_path, "static", "vendor", "tailwind.js")), "menu": [(t, [byslug[s] for s in ss if s in byslug]) for t, ss in MENU],
            "flow_groups": FLOW_GROUPS, "related": rel, "cfg_page": byslug.get("configuracoes"), "status_defs": statuses.public()}

_cnt = {"t": 0, "v": {}}
@app.get("/api/menu/counts")
def api_menu_counts():
    import time
    if time.time() - _cnt["t"] > 20:   # contadores do menu (cache curto)
        _cnt["v"] = {"envio": queries.q1("SELECT COUNT(*) n FROM sample_shipments WHERE status='pendente_projeto'")["n"], "amostras": purchases.pending({})["summary"]["total"],
                     "pendencias": queries.q1("SELECT COUNT(*) n FROM pendencies WHERE status='aberta'")["n"]}; _cnt["t"] = time.time()
    return jsonify(_cnt["v"])

@app.get("/favicon.ico")
def favicon():
    r = send_file(os.path.join(app.root_path, "static", "img", "ShockAbsorberData.ico"), mimetype="image/x-icon"); r.headers["Cache-Control"] = "public, max-age=3600"; return r

@app.route("/")
def home():
    return render_template("home.html", s=db.stats(), user=auth.current_user())

@app.route("/<slug>")
def page(slug):
    p = next((x for x in PAGES if x[0] == slug), None)
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
    return send_file(exporter._finish(wb, {"Fonte": s["name"]}), as_attachment=True, download_name=exporter.friendly_name("fontes", {"q": base}).replace("Fontes e histórico", "Dados avulsos"), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

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

# ---- Controle de status (DES / R-D), compras pendentes e Brands ----
@app.post("/api/rd/<kind>/item/<path:code>/flags")
def api_rd_flag(kind, code):
    b = request.get_json(force=True) or {}
    try: rd.set_flag(_rdk(kind), code, b.get("flag"), b.get("value"), b.get("user"))
    except ValueError as e: return jsonify(error=str(e)), 400
    return jsonify(flags=rd.item_flags(_rdk(kind), code))
@app.post("/api/rd/<kind>/flags/bulk")
def api_rd_flag_bulk(kind):
    b = request.get_json(force=True) or {}; codes = [c for c in (b.get("codes") or []) if c][:2000]
    try: n = rd.set_flags_bulk(_rdk(kind), codes, b.get("flag"), b.get("value"), b.get("user"))
    except ValueError as e: return jsonify(error=str(e)), 400
    return jsonify(updated=n, counts=rd.flag_counts(_rdk(kind)))
@app.get("/api/purchases/pending")
def api_pend_buy(): return jsonify(purchases.pending(request.args.to_dict()))
@app.get("/api/brands")
def api_brands(): return jsonify(brands.summary())
@app.get("/api/brands/<brand>/items")
def api_brand_items(brand): return jsonify(brands.items(brand.upper(), request.args.to_dict()))

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
@app.get("/api/duplicates")
def api_dups(): return jsonify(queries.duplicates())
@app.get("/api/history")
def api_hist(): return jsonify(queries.history())
@app.post("/api/sources/<int:i>")
def api_src(i):
    pr = int((request.get_json(force=True) or {}).get("priority", 5)); queries.run("UPDATE sources SET priority=? WHERE id=?", (max(1, min(pr, 9)), i)); return jsonify(ok=True)
def _eqf():
    g = request.args; return dict(status=g.get("status") or None, conf=g.get("confidence") or None, qtxt=g.get("q") or None, crit=g.getlist("crit"), dif=g.getlist("dif"), miss=g.getlist("miss"), diff=g.get("diff") or None, minscore=g.get("minscore") or None)
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
@app.post("/api/samples")
def api_sample_save():
    oid = queries.sample_save(request.get_json(force=True)); shipments.sync(); return jsonify(id=oid)   # etapa «Chegou» gera o envio «Pendente projeto»
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
def api_dt(): return jsonify(damping.tests(request.args.get("q")))
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
    nm = exporter.friendly_name("damping", {"code": tt.get("perfect_code") or tt.get("label")}).replace(".xlsx", f" - ensaio {i}.xlsx")
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
def api_rd_f(kind): return jsonify(rd.facets(_rdk(kind)))
@app.get("/api/rd/<kind>/item/<path:code>")
def api_rd_d(kind, code): return jsonify(rd.detail(_rdk(kind), code) or abort(404))
@app.get("/api/filters")
def api_filters(): return jsonify(rd.filter_lists(request.args.get("make") or None))

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
    try: shipments.sync(); goals.ensure(); _cnt["t"] = 0
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
    admin_only(); return jsonify(only_description=rules.only_desc(), goal_valid_user=rules.valid_user(), goal_basis=rules.goal_basis(), leadtime_meta_dias=__import__("leadtime").meta_dias(), defaults={"only_description": "AMORTECEDOR", "goal_valid_user": "ITALOC", "goal_basis": "validacao", "leadtime_meta_dias": 180})
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
    db.rebuild_flags_view(); _cnt["t"] = 0
    return jsonify(only_description=rules.only_desc(), goal_valid_user=rules.valid_user(), goal_basis=rules.goal_basis(), leadtime_meta_dias=__import__("leadtime").meta_dias())

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
@app.get("/api/dashboard")
def api_dashboard():
    y = request.args.get("year"); funnel, fl = {}, {}
    for k in (kinds.DES, kinds.RD):
        rows = rd.facets(k)["status"]; rank = data_pipeline.STATUS_RANK
        funnel[k] = sorted([{"status": r["v"], "n": r["n"]} for r in rows], key=lambda r: rank.get(r["status"], -1)); fl[k] = rd.flag_counts(k)
    return jsonify(stats=db.stats(), goals=goals.progress(y), tracking=goals.tracking_info(), funnel=funnel, flags=fl, sales=analytics.sales_summary(), stock=analytics.stock_summary(), pipeline=data_pipeline.status(),
                   groups=statuses.public(), system=queries.q("SELECT coalesce(system_type,'nd') s, COUNT(*) n FROM products GROUP BY 1"))
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

@app.get("/api/pedidos/previsao")
def api_previsao():
    """Previsão de embarques e chegadas (etapas produção → mar → desembaraço medidas no histórico de cada fornecedor)."""
    import leadtime
    return jsonify(leadtime.forecast_cached())

@app.get("/api/vendas/resumo")
def api_vendas_resumo():
    return jsonify(curva_abc.overview(request.args.get("months") or 24))

@app.get("/api/vendas/curva-a")
def api_curva_a():
    try: return jsonify(curva_abc.payload(request.args.get("year"), request.args.get("month"), request.args.get("limit")))
    except ValueError as e: return jsonify(error=str(e)), 400

@app.post("/api/warranty/parse")
def api_warranty_parse():
    f = request.files.get("file")
    if not f or not f.filename: return jsonify(error="Envie a planilha de garantia (.xlsx, .xls ou .csv) no campo «file»."), 400
    try: r = warranty.parse(f.stream, f.filename)
    except ValueError as e: return jsonify(error=str(e)), 400
    if request.values.get("save", "1") != "0": warranty.save(r["rows"], f.filename)
    if request.values.get("rows", "1") == "0": r = {k: v for k, v in r.items() if k != "rows"}
    return jsonify(r)
@app.get("/api/warranty")
def api_warranty(): return jsonify(warranty.summary(int(request.args.get("top") or 15), request.args.get("code")))

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

if __name__ == "__main__":
    if os.environ.get("PSD_SCHEDULER", "on") != "off": data_pipeline.start_scheduler(on_done=_after_sync)      # sincronização diária automática (DEV_SYNC_HOURS, padrão 24)
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", 5000)), debug=False)
