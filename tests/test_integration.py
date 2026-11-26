"""Teste de integração ponta a ponta (sem rede e sem senha): servidor SQL de mentira → pipeline → app Flask.
Rodar (na pasta do projeto):   python -m unittest tests.test_integration -v
Roda SOZINHO (usa um banco temporário). Não misture com outros módulos de teste no mesmo processo."""
import os, sys, json, time, shutil, sqlite3, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
TMP = tempfile.mkdtemp(prefix="psd_int_"); DB = os.path.join(TMP, "app.db"); SERVER = os.path.join(TMP, "server.db")
# o ambiente vem ANTES de qualquer import do app: database.DB_PATH é lido na importação (importar antes = gravar no banco REAL)
os.environ.update(PSD_DB=DB, PSD_AUTH="off", PSD_SCHEDULER="off", DEV_DB_USER="pwbi.desenvolvimento", DEV_DB_PASSWORD="senha-de-teste", ML_CLIENT_ID="id", ML_CLIENT_SECRET="segredo")
import seed_db; seed_db.build(DB)          # banco sintético: o teste não depende (nem expõe) dos dados reais da empresa
import app as A, database as db, fake_server, data_pipeline as dp, goals, price_search, auth, kinds, statuses
seed_db.guard(db)
DES, RD = kinds.DES, kinds.RD
import drawings
drawings.DIR = os.path.join(TMP, "drawings"); drawings.TMP = os.path.join(TMP, "uploads"); auth.AVATAR_DIR = os.path.join(TMP, "avatars")      # os testes não tocam nos arquivos reais do projeto
import validacao; validacao.DIR = os.path.join(TMP, "validacoes")
fake_server.build(SERVER, DB)
A.app.config["PIPELINE_CONN_FACTORY"] = lambda cfg: sqlite3.connect(SERVER)
C = A.app.test_client()

def wait_sync(timeout=40):
    t0 = time.time(); time.sleep(.2)
    while time.time() - t0 < timeout:
        s = C.get("/api/pipeline/status").json
        if not s["running"]: return s
        time.sleep(.2)
    raise AssertionError("sincronização não terminou")

def run_sync():
    r = C.post("/api/pipeline/sync"); assert r.status_code == 200 and r.json["started"], r.json; return wait_sync()

def server(sql, params=()):
    c = sqlite3.connect(SERVER); n = c.execute(sql, params).rowcount; c.commit(); c.close(); return n

def codes_where(kind, status, n):
    """Códigos do tipo/status pedidos que existem SÓ nesse tipo no servidor (DES e R-D são exclusivos: código nos dois vale como R-D)."""
    sv = sqlite3.connect(SERVER); other = KIND_SQL[RD if kind == DES else DES]
    both = {x[0].upper() for x in sv.execute(f"SELECT DISTINCT CÓDIGO FROM DESENVOLVIMENTO_PRODUTOS WHERE lower(trim(SUGESTÃO)) IN {other}")}; sv.close()
    c = sqlite3.connect(DB); r = [x[0] for x in c.execute("SELECT DISTINCT code FROM rd_projects WHERE suggestion=? AND status=? ORDER BY code", (kind, status)) if x[0] not in both][:n]; c.close(); return r

KIND_SQL = {DES: "('des','desenvolvimento')", RD: "('r-d','rd','redesenvolvimento')"}
def set_status(codes, status, kind=None):
    """Muda o status no servidor de mentira. `kind` limita ao tipo (o mesmo código pode existir em DESENVOLVIMENTO e em REDESENVOLVIMENTO)."""
    w = f" AND lower(trim(SUGESTÃO)) IN {KIND_SQL[kind]}" if kind else ""
    server("UPDATE DESENVOLVIMENTO_PRODUTOS SET STATUS=? WHERE CÓDIGO IN (%s)%s" % (",".join("?" * len(codes)), w), (status, *codes))


class Fluxo(unittest.TestCase):
    """Os testes dependem da ordem (cada um usa o estado deixado pelo anterior)."""
    ctx = {}

    def test_01_sync_publica_e_normaliza(self):
        st = run_sync(); self.assertEqual(st["last_status"], "ok"); self.assertTrue(st["configured"]); self.assertGreater(st["items"], 1000)
        c = sqlite3.connect(DB); labels = {r[0] for r in c.execute("SELECT DISTINCT suggestion FROM rd_projects")}; c.close()
        self.assertEqual(labels, {DES, RD})                                                      # nenhuma variação suja sobrou
        d = C.get("/api/rd/des").json; self.assertEqual(d["kind"], DES); self.assertGreater(d["total"], 100); self.assertEqual(C.get("/api/rd/rd").json["kind"], RD)
        runs = C.get("/api/pipeline/runs").json; self.assertTrue(runs["runs"][0]["baseline"]); self.assertEqual(runs["runs"][0]["events"], 0)   # marco zero
        self.assertEqual({r["dataset"] for r in runs["datasets"]}, {"compras", "vendas", "estoque"})
        self.assertTrue(os.path.isdir(os.path.join(TMP, "backups")))                                # backup antes de trocar a fonte oficial

    def test_02_nenhuma_sigla_antiga_nas_apis(self):
        for u in ("/api/rd/des", "/api/rd/rd", "/api/rd/des/facets", "/api/brands/PERFECT/items", "/api/purchases/pending", "/api/dashboard", "/api/quick-search?q=amd"):
            txt = C.get(u).get_data(as_text=True); self.assertNotIn('"DES"', txt, u); self.assertNotIn('"R-D"', txt, u)
        self.assertEqual(kinds.normalize_kind("des "), DES); self.assertEqual(kinds.normalize_kind("r-d"), RD); self.assertEqual(kinds.of_slug("rd"), RD)

    def test_03_status_em_11_categorias(self):
        fc = C.get("/api/rd/des/facets").json["flags"]
        for k in statuses.KEYS: self.assertIn(k, fc)
        self.assertEqual(len(statuses.KEYS), 11); self.assertEqual(len(statuses.GROUPS), 5)
        n_q = C.get("/api/rd/des?flag=val_reprovada_qual").json["total"]; n_v = C.get("/api/rd/des?flag=val_reprovada").json["total"]
        grp = C.get("/api/rd/des?flag=grupo_validacao").json["total"]; self.assertGreaterEqual(grp, max(n_q, n_v))
        code = C.get("/api/rd/des?size=1").json["rows"][0]["code"]
        self.assertEqual(C.post(f"/api/rd/des/item/{code}/flags", json={"flag": "pend_inmetro", "value": True}).status_code, 405)      # etapa 20 · Q3: nada é marcado à mão

    def test_03b_estagios_e_sub_status_do_servidor(self):
        """Etapa 20 · Q2/Q4: a lista abre em andamento; cada estágio da esteira e cada sub status do quadro abrem a lista com o mesmo número."""
        from urllib.parse import quote
        for slug in ("des", "rd"):
            fc = C.get(f"/api/rd/{slug}/facets").json; a = fc["andamento"]
            self.assertEqual(fc["estagio"], "andamento"); self.assertEqual(C.get(f"/api/rd/{slug}?status=andamento").json["total"], a["n"], slug)
            self.assertLessEqual(a["n"], fc["total"]); self.assertGreater(a["n"], 0, slug)
            for x in fc["esteira"]: self.assertEqual(C.get(f"/api/rd/{slug}?status={quote(x['v'])}").json["total"], x["n"], f"{slug} {x['v']}")
            for g in fc["subs"]:
                for v in g["values"]:
                    d = C.get(f"/api/rd/{slug}?status=andamento&sub={quote(g['key'] + ':' + (v.get('f') or v['v']))}").json
                    self.assertEqual((d["total"], d["linhas"]), (v["n"], v["l"]), f"{slug} {g['key']} {v['v']}")
            # etapa 21: chave de linha (família) — o «Amortecedor» é o padrão e bate com o em andamento; itens = linhas do servidor
            fam = {x["v"]: x for x in fc["familias"]}; self.assertEqual(fam["amortecedor"]["l"], a["l"]); self.assertEqual(fc["linha"], "amortecedor")
            self.assertEqual(C.get(f"/api/rd/{slug}?status=andamento").json["linhas"], a["l"])
            for k, x in fam.items(): self.assertEqual(C.get(f"/api/rd/{slug}?status=andamento&linha={k}").json["linhas"], x["l"], f"{slug} {k}")
            rows = C.get(f"/api/rd/{slug}?status=andamento&all=1").json["rows"]
            self.assertTrue(all("also_other" not in r and isinstance(r["subs"], list) for r in rows))

    def test_04_metas_regras_de_negocio(self):
        C.put("/api/settings", json={"goal_basis": "recebido"})                         # este teste cobre a base «item recebido»; a base «validação» é o test_04b
        g = C.get("/api/goals?year=2026").json["goals"]; self.assertEqual((g[DES]["target"], g[RD]["target"]), (125, 150)); self.assertEqual((g[DES]["tracked"], g[RD]["tracked"]), (0, 0))
        r = C.put("/api/goals", json={"year": 2026, "kind": RD, "target": 150, "prior_done": 150}).json["goals"][RD]; self.assertTrue(r["reached"]); self.assertEqual(r["pct"], 100.0)
        C.put("/api/goals", json={"year": 2026, "kind": RD, "target": 150, "prior_done": 0}); self.assertEqual(C.put("/api/goals", json={"year": 2026, "kind": "xyz", "target": 1}).status_code, 400)
        # --- prepara o cenário no "servidor" e sincroniza (cada passo = uma sincronização = uma transição) ---
        rd_codes = codes_where(RD, "ITEM RECEBIDO", 6); des_a = codes_where(DES, "EM COTAÇÃO", 4); des_b = codes_where(DES, "EM COTAÇÃO", 8)[4:6]; des_done = codes_where(DES, "ITEM RECEBIDO", 2)
        self.assertEqual((len(rd_codes), len(des_a), len(des_b), len(des_done)), (6, 4, 2, 2)); Fluxo.ctx.update(rd=rd_codes, des_a=des_a, des_b=des_b, des_done=des_done)
        set_status(rd_codes, "PENDENTE CONFIRMAÇÃO", RD); run_sync()                  # R-D: voltam a pendente (transição para trás: não conta)
        self.assertEqual(C.get("/api/goals?year=2026").json["goals"][RD]["tracked"], 0)
        pv = C.get("/api/validations/pending").json; self.assertGreaterEqual(pv["total"], 6)
        # regras novas: R-D só conta com validação do usuário ITALOC; DES conta quem chegou a ITEM RECEBIDO no ano; só descrição «Amortecedor»
        set_status(rd_codes, "ITEM RECEBIDO", RD)
        for cds, usr in ((rd_codes[:4], "ITALOC"), (rd_codes[4:5], "DOUGLASJ"), (rd_codes[5:], None)):
            server("UPDATE DESENVOLVIMENTO_PRODUTOS SET \"USER APROV\"=? WHERE CÓDIGO IN (%s) AND lower(trim(SUGESTÃO)) IN %s" % (",".join("?" * len(cds)), KIND_SQL[RD]), (usr, *cds))
        server("UPDATE DESENVOLVIMENTO_PRODUTOS SET \"DESCRIÇÃO\"='PASTILHA DE FREIO' WHERE CÓDIGO=? AND lower(trim(SUGESTÃO)) IN %s" % KIND_SQL[DES], (des_b[1],))
        # etapa 19: DES = PEDIDO CONFIRMADO → ITEM RECEBIDO no ano, sem exigir validação. des_a passa por PEDIDO CONFIRMADO; des_b pula direto de EM COTAÇÃO
        server("UPDATE DESENVOLVIMENTO_PRODUTOS SET \"PEDIDO CONFIRMADO\"=NULL WHERE CÓDIGO IN (%s) AND lower(trim(SUGESTÃO)) IN %s" % (",".join("?" * 6), KIND_SQL[DES]), (*des_a, *des_b))
        set_status(des_a, "PEDIDO CONFIRMADO", DES); run_sync()
        set_status(des_a, "ITEM RECEBIDO", DES); set_status(des_b, "ITEM RECEBIDO", DES); run_sync()
        g = C.get("/api/goals?year=2026").json["goals"]
        self.assertEqual(g[RD]["tracked"], 4); self.assertEqual(g[RD]["parts"]["recebidos_validados"], 4); self.assertEqual(g[RD]["parts"]["recebidos_sem_validacao"], 2)   # só ITALOC conta
        self.assertEqual(g[DES]["tracked"], 4); self.assertEqual(g[DES]["parts"]["sem_pedido_confirmado"], 1)               # des_a(4); des_b[0] não passou por PEDIDO CONFIRMADO; des_b[1] não é amortecedor
        set_status(des_a, "ITEM RECEBIDO", DES); run_sync(); g = C.get("/api/goals?year=2026").json["goals"][DES]; self.assertEqual(g["tracked"], 4)     # repetir não conta duas vezes
        m = {x["month"]: x["n"] for x in g["series"]["ITEM RECEBIDO"]}; self.assertEqual(sum(m.values()), 4)
        self.assertEqual(C.get("/api/goals?year=2025").json["goals"][DES]["tracked"], 0)                                 # outro ano: nada (a data da mudança está em 2026)
        ev = C.get("/api/goals/events?year=2026").json["rows"]; self.assertTrue(any(e["counts"] for e in ev)); self.assertTrue(any(not e["counts"] and "ITALOC" in (e["why_not"] or "") for e in ev))
        self.assertTrue(any(not e["counts"] and "PEDIDO CONFIRMADO" in (e["why_not"] or "") for e in ev))
        self.assertFalse(any(e["code"] == des_b[1] for e in ev))                                                          # fora do filtro «Amortecedor»
        # filtro Tipo da tela Metas (etapa 16): aceita sigla ou rótulo; cada tipo traz só os seus e, juntos, dão a lista completa
        ev_des = C.get("/api/goals/events?year=2026&kind=des").json["rows"]; ev_rd = C.get("/api/goals/events?year=2026&kind=REDESENVOLVIMENTO").json["rows"]
        self.assertTrue(ev_des and ev_rd); self.assertEqual({e["kind"] for e in ev_des}, {DES}); self.assertEqual({e["kind"] for e in ev_rd}, {RD})
        self.assertEqual(sorted((e["code"], e["kind"]) for e in ev_des + ev_rd), sorted((e["code"], e["kind"]) for e in ev))
        self.assertEqual(len(C.get("/api/goals/events?year=2026&limit=1").json["rows"]), 1)                              # a tela pede a lista inteira (contadores «conta?» exatos)
        self.assertEqual(C.get("/api/goals/events?year=2026&limit=abc").status_code, 200)
        self.assertNotIn(des_b[1], {r["code"] for r in C.get("/api/rd/des?all=1").json["rows"]})                         # e some das listas

    def test_04b_metas_por_validacao_nao_zera(self):
        """Bug dos dados zerados: espaços/caixa/NBSP em USER_VALID, SUGESTAO e LINHA. Conta só ITALOC + LINHA Amortecedor, DES e R-D separados."""
        server("ALTER TABLE DESENVOLVIMENTO_PRODUTOS ADD COLUMN LINHA"); server('ALTER TABLE DESENVOLVIMENTO_PRODUTOS ADD COLUMN "DATA APROV"')
        server('UPDATE DESENVOLVIMENTO_PRODUTOS SET "USER APROV"=NULL, LINHA=\'AMORTECEDOR\'')
        used = {x for v in Fluxo.ctx.values() for x in v}          # códigos que o test_04 já mexeu (recebidos em 2026) não servem: o cenário aqui parte de «nenhum recebido no ano»
        c = sqlite3.connect(DB); pick = lambda k, n: [x[0] for x in c.execute("SELECT DISTINCT code FROM rd_projects WHERE suggestion=? AND upper(description) LIKE '%AMORTECEDOR%' ORDER BY code", (k,)) if x[0] not in used][:n]; des, rd_ = pick(DES, 5), pick(RD, 4); c.close()
        def mark(codes, kind, user, linha="AMORTECEDOR", dt="2026-05-10"):
            server("UPDATE DESENVOLVIMENTO_PRODUTOS SET \"USER APROV\"=?, LINHA=?, \"DATA APROV\"=? WHERE CÓDIGO IN (%s) AND lower(trim(SUGESTÃO)) IN %s" % (",".join("?" * len(codes)), KIND_SQL[kind]), (user, linha, dt, *codes))
        mark(des[:3], DES, " italoc\u00a0"); mark(des[3:4], DES, "ITALOC2"); mark(des[4:5], DES, "ITALOC", linha="BANDEJA"); mark(rd_[:2], RD, "Italoc ", dt="2025-12-30"); mark(rd_[2:4], RD, "ITALOC")
        set_status(rd_[2:3], "ITEM RECEBIDO", RD); set_status(rd_[3:4], "EM COTA\u00c7\u00c3O", RD)          # meta R-D (etapa D5b): validado no ano conta quando chegar a ITEM RECEBIDO
        run_sync(); C.put("/api/settings", json={"goal_basis": "validacao"})
        v = C.get("/api/metas/validacoes?year=2026").json
        self.assertEqual((v[DES], v[RD], v["total"]), (3, 2, 5)); self.assertEqual(v["por_mes"]["2026-05"], {DES: 3, RD: 2}); self.assertEqual(v["filtro"]["USER_VALID"], "ITALOC")
        self.assertEqual(C.get("/api/metas/validacoes?year=2025").json[RD], 2)
        g = C.get("/api/goals?year=2026").json; self.assertEqual(g["basis"], "validacao"); self.assertEqual((g["goals"][DES]["tracked"], g["goals"][RD]["tracked"]), (4, 1)); self.assertEqual(g["validacoes"]["total"], 5)      # DES (etapa 19): os 4 do test_04 (pedido confirmado → recebido, validação não importa); R-D: 2 validados, 1 recebido
        lv = C.get("/api/goals/rd-validations?year=2026").json; self.assertEqual(sorted(r["code"] for r in lv["rows"]), sorted(rd_[2:4])); self.assertEqual((lv["counts"]["contam"], lv["counts"]["aguardando"]), (1, 1))
        self.assertEqual(g["goals"][RD]["parts"]["validacoes"], v[RD])
        set_status(des[:4], "ITEM RECEBIDO", DES); set_status(rd_[3:4], "ITEM RECEBIDO", RD); run_sync(); g = C.get("/api/goals?year=2026").json; n = g["goals"][DES]["tracked"]; self.assertGreaterEqual(n, 4)      # etapa 19: soma quem passou por PEDIDO CONFIRMADO (coluna ou transição); a validação não importa
        self.assertEqual(g["goals"][RD]["tracked"], 2)
        self.assertEqual(sum(m["n"] for m in g["goals"][DES]["series"]["main"]), n); self.assertEqual(C.put("/api/settings", json={"goal_basis": "x"}).status_code, 400)

    def test_05_validacoes(self):
        code = Fluxo.ctx["rd"][0]; set_status([code], "PENDENTE CONFIRMAÇÃO", RD); run_sync()
        pv = C.get("/api/validations/pending").json; row = next(r for r in pv["rows"] if r["code"] == code); self.assertIsNone(row["sent_at"])
        vid = C.post("/api/validations", json={"code": code, "kind": RD}).json["id"]; row = next(r for r in C.get("/api/validations/pending").json["rows"] if r["code"] == code); self.assertTrue(row["sent_at"])
        d = C.get(f"/api/rd/rd/item/{code}").json; self.assertEqual(len(d["validations"]), 1); C.delete(f"/api/validations/{vid}")
        self.assertIsNone(next(r for r in C.get("/api/validations/pending").json["rows"] if r["code"] == code)["sent_at"]); self.assertEqual(C.post("/api/validations", json={"code": "NAOEXISTE", "kind": RD}).status_code, 400)

    def test_06_compras_vendas_estoque(self):
        self.assertEqual(C.get("/api/purchase-orders").status_code, 404); self.assertEqual(C.get("/pedidos").status_code, 404)    # módulo removido
        dash = C.get("/api/dashboard").json; self.assertTrue(dash["sales"]["available"]); self.assertEqual(len(dash["sales"]["months"]), 12); self.assertTrue(dash["sales"]["top"]); self.assertTrue(dash["stock"]["available"])
        self.assertTrue(set(dash["funnel"]) == {DES, RD}); self.assertEqual(dash["groups"]["groups"][0]["key"], "compras")
        pid = C.get("/api/products?size=1").json["rows"][0]["id"]; f = C.get(f"/api/products/{pid}").json; self.assertIn("sales", f); self.assertIn("stock", f)
        fc = C.get("/api/products/facets").json; self.assertTrue(fc["family"] and fc["rod"]); self.assertGreater(fc["system"]["gas"], 0)       # filtros da tela Produtos (etapa 16)
        rod = fc["rod"][0]; self.assertEqual(C.get(f"/api/products?rod={rod['v']}").json["total"], rod["n"])
        import openpyxl, io
        r = C.get("/api/export/produtos.xlsx?system=gas&launch=S"); wb = openpyxl.load_workbook(io.BytesIO(r.data)); ws = wb["Produtos"]
        head = [c.value for c in ws[1]]; self.assertIn("Ø haste (mm)", head); self.assertEqual({row[head.index("Sistema")] for row in ws.iter_rows(min_row=2, values_only=True)}, {"FORCE GAS"})
        self.assertIn("FORCE GAS", r.headers.get("Content-Disposition", "") + str([c.value for c in wb["Filtros aplicados"]["B"]]))
        for x in ("lados", "envio", "desenvolvimento", "redesenvolvimento", "brands", "desenhos"): self.assertEqual(C.get(f"/api/export/{x}.xlsx").status_code, 200, x)

    def test_07_busca_de_precos(self):
        def item(i, title, price, cond="new", free=False, sold=10): return {"id": f"MLB{i}", "title": title, "price": price, "currency_id": "BRL", "permalink": f"https://produto.mercadolivre.com.br/MLB{i}", "thumbnail": "http://x/y.jpg", "condition": cond,
                                                                      "shipping": {"free_shipping": free}, "seller": {"id": 100 + i, "nickname": f"LOJA{i}", "seller_reputation": {"level_id": "5_green", "power_seller_status": "gold", "transactions": {"ratings": {"positive": .97}}}}, "sold_quantity": sold}
        api = {"results": [item(1, "Par De Amortecedor Traseiro Monroe 16470", 180), item(2, "Kit 2 Amortecedores Monroe 16470", 170), item(3, "Amortecedor Traseiro Monroe 16470 Novo", 129.9, free=True), item(4, "Amortecedor Monroe 16470 Usado", 40, cond="used"),
                           item(5, "Amortecedor Monroe 16470 Original", 99.9), item(6, "Amortecedor Cofap GP32530", 50), item(7, "Jogo Amortecedor Monroe 16470 2 Peças", 110), item(8, "Amortecedor Monroe 16470", 150, free=True)]}
        calls = []
        def fetch(url, headers=None, timeout=None, data=None):
            calls.append(url)
            if "oauth/token" in url: return 200, json.dumps({"access_token": "TOK", "expires_in": 3600})
            if "/sites/MLB/search" in url: return 200, json.dumps(api)
            return 404, ""
        A.app.config["PRICE_FETCH"] = fetch; price_search._TOKEN.update(v=None, exp=0)
        r = C.post("/api/prices/search", json={"refs": [{"brand": "MONROE", "code": "16470"}], "limit": 5}).json
        titles = [x["title"] for x in r["results"]]; prices = [x["price"] for x in r["results"]]
        self.assertEqual(prices, [99.9, 110, 129.9, 150, 170]); self.assertFalse(any("Usado" in t or "Cofap" in t for t in titles))      # menor preço primeiro, unitário ou par/kit; sem usados nem outro código
        self.assertEqual({x["price"]: x["pair"] for x in r["results"]}, {99.9: False, 110: True, 129.9: False, 150: False, 170: True}); self.assertEqual(r["best"]["price"], 99.9); self.assertEqual(r["status"], "ok")
        self.assertIn("OrderId_PRICE", r["refs"][0]["links"]["mercado_livre"])
        self.assertEqual(r["results"][0]["seller"], "LOJA5"); self.assertIn("Verde", r["results"][0]["reputation"]); self.assertTrue(r["results"][2]["free_shipping"]); self.assertTrue(r["token_configured"])
        self.assertTrue(any("condition=new" in u for u in calls)); self.assertEqual(r["refs"][0]["tried"][0]["source"], "Mercado Livre (API)")
        # sem código no título (strict desligado) o anúncio de outra marca volta; com strict some
        r2 = C.post("/api/prices/search", json={"refs": [{"brand": "MONROE", "code": "16470"}], "strict": False}).json; self.assertIn(50, [x["price"] for x in r2["results"]])
        # API recusa → cai para a página pública
        html = '<ol><li class="ui-search-layout__item"><a class="ui-search-link" href="https://produto.mercadolivre.com.br/MLB-123-amortecedor-monroe-16470-_JM"><h2 class="ui-search-item__title">Amortecedor Monroe 16470 Dianteiro</h2></a><span class="andes-money-amount__fraction">134</span><span class="andes-money-amount__cents">90</span></li><li class="ui-search-layout__item"><a href="https://produto.mercadolivre.com.br/MLB-999-par-_JM"><h2 class="ui-search-item__title">Par Amortecedor Monroe 16470</h2></a><span class="andes-money-amount__fraction">90</span></li></ol>'
        def fetch2(url, headers=None, timeout=None, data=None):
            if "oauth/token" in url: return 200, json.dumps({"access_token": "TOK", "expires_in": 3600})
            if "api.mercadolibre.com" in url: return 403, "forbidden"
            if "lista.mercadolivre.com.br" in url: return 200, html
            return 404, ""
        A.app.config["PRICE_FETCH"] = fetch2; r3 = C.post("/api/prices/search", json={"refs": [{"brand": "MONROE", "code": "16470"}]}).json
        self.assertEqual([x["price"] for x in r3["results"]], [90.0, 134.9]); self.assertTrue(r3["results"][0]["pair"]); self.assertEqual([t["source"] for t in r3["refs"][0]["tried"]][:2], ["Mercado Livre (API)", "Mercado Livre (página)"]); self.assertIn("403", r3["refs"][0]["tried"][0]["error"])
        # tudo falha → devolve links manuais (Google, ML, mercadocar)
        A.app.config["PRICE_FETCH"] = lambda *a, **k: (500, ""); r4 = C.post("/api/prices/search", json={"refs": [{"brand": "MONROE", "code": "16470"}]}).json
        self.assertEqual(r4["results"], []); self.assertIn("google_shopping", r4["refs"][0]["links"]); self.assertEqual(C.post("/api/prices/search", json={"refs": []}).status_code, 400)
        # salvar a escolha em sample_quotes
        # etapa 18 · Q11: pedido de amostra só para código PERFECT (AMD…) em desenvolvimento
        for bad in ("1BP31901AB", "8550514114", "JS1/18097/AA", "AMD9999", ""):
            r = C.post("/api/samples", json={"perfect_code": bad, "stage": "cotacao", "quotes": []}); self.assertEqual(r.status_code, 400, bad); self.assertTrue(r.json["error"])
        self.assertTrue(all(x["perfect_code"].startswith("AMD") for x in C.get("/api/samples/codes?q=50").json["rows"]))
        self.assertIsNone(C.get("/api/samples/prefill?code=AMD5001").json["problem"]); self.assertIn("montadora", C.get("/api/samples/prefill?code=1BP31901AB").json["problem"])
        oid = C.post("/api/samples", json={"perfect_code": "AMD5001", "stage": "cotacao", "quotes": []}).json["id"]
        self.assertEqual(C.post("/api/samples", json={"id": oid, "perfect_code": "AMD5001", "stage": "sc_aberta", "quotes": []}).status_code, 200)    # editar sem trocar o código
        qid = C.post("/api/prices/save", json={"order_id": oid, "price": 99.9, "link": "https://produto.mercadolivre.com.br/MLB5"}).json["id"]
        row = next(x for x in C.get("/api/samples?q=AMD5001").json["rows"] if x["id"] == oid); self.assertEqual((row["quotes"][0]["price"], row["quotes"][0]["chosen"]), (99.9, 1))
        self.assertEqual(C.post("/api/prices/save", json={"order_id": 99999, "price": 1, "link": "x"}).status_code, 400); A.app.config.pop("PRICE_FETCH")

    def test_07b_busca_a_prova_de_falhas(self):
        def boom(url, headers=None, timeout=None, data=None): raise RuntimeError("rede caiu")
        A.app.config["PRICE_FETCH"] = boom; price_search._TOKEN.update(v=None, exp=0)
        r = C.post("/api/prices/search", json={"refs": [{"brand": "MONROE", "code": "99999"}], "refresh": True}); self.assertEqual(r.status_code, 200); d = r.json
        self.assertEqual(d["status"], "links_only"); self.assertIsNone(d["best"]); self.assertTrue(d["refs"][0]["url"].startswith("https://lista.mercadolivre.com.br/")); self.assertTrue(d["links"]["google_shopping"])
        self.assertEqual(C.post("/api/prices/search", json={"refs": []}).status_code, 400)

    def test_08_planilhas_antigas_de_desenvolvimento_sao_ignoradas(self):
        import updater
        p = os.path.join(ROOT, "bases_exemplo", "Compra_de_amostra.xlsx"); r = updater.run([("DadosR-D e DES.xlsx", p), ("DadosDES.xlsx", p)], confirm=False)
        self.assertTrue(all(x["status"] == "ignorado" for x in r["results"]), r["results"]); self.assertIn("servidor", r["results"][0]["messages"][0])

    def test_09_falha_do_servidor_preserva_os_dados(self):
        n0 = C.get("/api/rd/des").json["total"]
        A.app.config["PIPELINE_CONN_FACTORY"] = lambda cfg: (_ for _ in ()).throw(RuntimeError("Login failed for user pwbi.desenvolvimento PWD=senha-de-teste"))
        st = run_sync(); self.assertEqual(st["last_status"], "erro"); self.assertNotIn("senha-de-teste", json.dumps(st)); self.assertIsNotNone(st["last_ok_at"])
        self.assertEqual(C.get("/api/rd/des").json["total"], n0)
        A.app.config["PIPELINE_CONN_FACTORY"] = lambda cfg: sqlite3.connect(SERVER)
        # servidor devolvendo muito pouco (view quebrada) → recusado, nada muda
        c = sqlite3.connect(SERVER); c.execute("CREATE TABLE bkp AS SELECT * FROM DESENVOLVIMENTO_PRODUTOS"); c.execute("DELETE FROM DESENVOLVIMENTO_PRODUTOS WHERE rowid>30"); c.commit(); c.close()
        st = run_sync(); self.assertEqual(st["last_status"], "erro"); self.assertIn("suspeita", st["last_error"]); self.assertEqual(C.get("/api/rd/des").json["total"], n0)
        c = sqlite3.connect(SERVER); c.execute("DELETE FROM DESENVOLVIMENTO_PRODUTOS"); c.execute("INSERT INTO DESENVOLVIMENTO_PRODUTOS SELECT * FROM bkp"); c.execute("DROP TABLE bkp"); c.commit(); c.close(); run_sync()

    def test_10_login_de_administrador(self):
        os.environ["PSD_AUTH"] = "on"
        try:
            c = A.app.test_client(); self.assertEqual(c.get("/dashboard").headers["Location"], "/setup"); self.assertEqual(c.get("/api/dashboard").status_code, 401)
            r = c.post("/setup", data={"username": "adm", "password": "curta", "password2": "curta"}); self.assertIn("ao menos 8", r.get_data(as_text=True))
            r = c.post("/setup", data={"username": "adm", "password": "senha-forte-9", "password2": "senha-forte-9"}); self.assertEqual(r.headers["Location"], "/"); self.assertEqual(c.get("/api/dashboard").status_code, 200)
            self.assertEqual(c.post("/setup", data={"username": "x", "password": "senha-forte-9", "password2": "senha-forte-9"}).headers["Location"], "/login")   # só cria o 1º
            c2 = A.app.test_client(); self.assertEqual(c2.get("/metas").headers["Location"].split("?")[0], "/login")
            self.assertIn("incorretos", c2.post("/login", data={"username": "adm", "password": "errada"}).get_data(as_text=True))
            r = c2.post("/login", data={"username": "adm", "password": "senha-forte-9", "next": "//evil.com"}); self.assertEqual(r.headers["Location"], "/")        # sem redirecionamento aberto
            self.assertEqual(c2.get("/api/auth/me").json["user"]["username"], "adm"); self.assertEqual(c2.post("/api/auth/password", json={"old": "senha-forte-9", "new": "outra-senha-10"}).json, {"ok": True})
            # perfil: trocar usuário (exige a senha), foto de perfil, administração de usuários
            self.assertIn("incorreta", c2.post("/api/auth/username", json={"password": "x", "username": "novo.adm"}).json["error"]); self.assertEqual(c2.post("/api/auth/username", json={"password": "outra-senha-10", "username": "ab"}).status_code, 400)
            self.assertTrue(c2.post("/api/auth/username", json={"password": "outra-senha-10", "username": "novo.adm"}).json["ok"]); self.assertEqual(c2.get("/api/auth/me").json["user"]["username"], "novo.adm")
            from PIL import Image; import io; buf = io.BytesIO(); Image.new("RGB", (300, 120), "#2f6bff").save(buf, "PNG"); buf.seek(0)
            self.assertTrue(c2.post("/api/auth/avatar", data={"file": (buf, "foto.png")}, content_type="multipart/form-data").json["ok"]); uid = c2.get("/api/auth/me").json["user"]["id"]
            av = c2.get(f"/avatar/{uid}"); self.assertEqual((av.status_code, av.mimetype), (200, "image/png")); self.assertEqual(Image.open(io.BytesIO(av.data)).size, (256, 256))
            self.assertEqual(c2.post("/api/auth/avatar", data={"file": (io.BytesIO(b"nao e imagem"), "x.png")}, content_type="multipart/form-data").status_code, 400)
            self.assertEqual(len(c2.get("/api/admin/users").json["users"]), 1); self.assertTrue(c2.post("/api/admin/users", json={"username": "ana", "password": "senha-ana-123", "role": "user"}).json["ok"])
            self.assertEqual(c2.put(f"/api/admin/users/{uid}", json={"role": "user"}).status_code, 400); self.assertEqual(c2.delete(f"/api/admin/users/{uid}").status_code, 400)   # nunca fica sem administrador
            ana = A.app.test_client(); self.assertEqual(ana.post("/login", data={"username": "ana", "password": "senha-ana-123"}).status_code, 302)
            for m, u in (("get", "/api/admin/users"), ("get", "/api/settings"), ("put", "/api/goals"), ("post", "/api/backups")): self.assertEqual(getattr(ana, m)(u, json={}).status_code, 403, u)   # usuário comum não administra
            self.assertEqual(c2.put("/api/settings", json={"goal_valid_user": "italoc"}).json["goal_valid_user"], "ITALOC")
            # com login ligado, «por» grava o NOME do usuário (antes ia o dicionário do usuário → erro 500 e nada salvo: vínculo do Brands e «Nosso código» da Cobertura)
            con = sqlite3.connect(DB)
            try: pc = con.execute("SELECT perfect_code FROM products WHERE catalog_position IS NOT NULL AND upper(perfect_code) LIKE 'AMD%' ORDER BY id LIMIT 1").fetchone()[0]
            finally: con.close()
            it = c2.get("/api/brands/MOTORCRAFT/items?all=1").json["rows"][0]
            r = c2.post("/api/brands/vinculo", json={"code": it["code"], "codigos": [pc]}); self.assertEqual(r.status_code, 200, r.get_data(as_text=True)[:200])
            r2 = c2.post("/api/cobertura/cross", json={"concorrente": "MONROE", "referencia": "T10-LOGIN", "codigos": [pc]}); self.assertEqual(r2.status_code, 200, r2.get_data(as_text=True)[:200])
            con = sqlite3.connect(DB)
            try: self.assertEqual([x[0] for x in con.execute("SELECT por FROM brand_links UNION ALL SELECT por FROM cross_correcoes WHERE ref_key='T10LOGIN'")], ["novo.adm", "novo.adm"])
            finally: con.close()
            c2.post("/api/brands/vinculo/desfazer", json={"code": it["code"], "anterior": None}); c2.post("/api/cobertura/cross/desfazer", json={"concorrente": "MONROE", "referencia": "T10-LOGIN", "anterior": None})
            aid = next(u["id"] for u in c2.get("/api/admin/users").json["users"] if u["username"] == "ana"); self.assertTrue(c2.delete(f"/api/admin/users/{aid}").json["ok"])
            self.assertEqual(c2.get("/logout").status_code, 302); self.assertEqual(c2.get("/api/dashboard").status_code, 401)
            self.assertEqual(c2.get("/favicon.ico").status_code, 200)
            self.assertNotIn("senha-forte", sqlite3.connect(DB).execute("SELECT pw_hash FROM users").fetchone()[0])                                                      # só o hash
        finally: os.environ["PSD_AUTH"] = "off"

    def test_11_paginas_carregam(self):
        import re
        for slug in ("dashboard", "metas", "pedidos-aberto", "vendas", "garantia", "desenvolvimento", "redesenvolvimento", "amostras", "configuracoes", "brands", "lados", "envio", "desenhos", "pendencias", "fontes", "atualizacao", "anomalias", "garantia", "estoque"):
            r = C.get("/" + slug); self.assertEqual(r.status_code, 200, slug); html = r.get_data(as_text=True)
            self.assertIn("syncchip", html); self.assertIn("PSD_STATUS", html); self.assertIn("nav-side", html); self.assertIn("psd-nav", html)         # menu azul-marinho (marca.css, etapa 17)
            self.assertIn("marca.css", html); self.assertIn("vendor/chart.umd.js", html); self.assertIn("icones.svg", html)
        telas = re.findall(r'/static/js/telas/([\w-]+)\.js', html); self.assertIn("pendencias", telas); self.assertNotIn("dados", telas)
        for t in telas:
            with C.get(f"/static/js/telas/{t}.js") as r: self.assertEqual(r.status_code, 200, t)                                                       # todo script de tela citado existe
        for f in ("vendor/chart.umd.js", "img/icones.svg", "fonts/barlow-latin-700-normal.woff2", "img/favicon.svg"):
            with C.get("/static/" + f) as r: self.assertEqual(r.status_code, 200, f)
        with C.get("/static/img/icones.svg") as r: icones = r.get_data(as_text=True)
        import app as AP
        for p in AP.PAGES + AP.HIDDEN: self.assertIn(f'id="i-{p[2]}"', icones, p[0])                                                                   # todo ícone do menu existe no arquivo único
        self.assertEqual(C.get("/guia-visual").status_code, 200)
        self.assertIn("Desenvolvimento", C.get("/desenvolvimento").get_data(as_text=True)); self.assertNotIn("Em desenvolvimento", C.get("/desenvolvimento").get_data(as_text=True))

    def test_12_favicon_e_menu_sem_pedidos(self):
        r = C.get("/favicon.ico"); self.assertEqual((r.status_code, r.mimetype), (200, "image/x-icon")); self.assertGreater(len(r.data), 1000)
        html = C.get("/dashboard").get_data(as_text=True); self.assertIn('href="/favicon.ico?v=2"', html)
        self.assertNotIn('id="psd-fechar"', html)                                  # update 5: «Fechar o sistema» saiu da barra do topo (fica em Configurações › Sistema)
        s = C.get("/api/sistema").json; self.assertRegex(s["aberto_em"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d$"); self.assertTrue(s["endereco"]); self.assertNotIn("Pedidos de compra", html)

    def test_13_brands_mostra_codigo_perfect(self):
        d = C.get("/api/brands/MOTORCRAFT/items?all=1").json; self.assertTrue(d["rows"]); self.assertTrue(all("perfect_codes" in r for r in d["rows"]))
        com = [r for r in d["rows"] if r["perfect_codes"]]; self.assertTrue(com, "ao menos um item Motorcraft deveria ter código PERFECT relacionado")
        pc = com[0]["perfect_codes"][0]; self.assertEqual(C.get("/api/brands/MOTORCRAFT/items?all=1&q=" + pc).json["rows"][0]["perfect_codes"].count(pc), 1)    # a busca também acha pelo código PERFECT
        self.assertIn("Código PERFECT relacionado", sqlite3.connect(":memory:").execute("select 'Código PERFECT relacionado'").fetchone()[0])
        x = C.get("/api/export/brands.xlsx?brand=MOTORCRAFT"); self.assertEqual(x.status_code, 200)

    def test_14_sugestoes_de_compra_de_amostra(self):
        d = C.get("/api/purchases/pending").json; self.assertTrue(d["total"] > 0)
        c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
        for r in d["rows"][:40]:
            st = {x["status"] for x in c.execute("SELECT status FROM rd_projects WHERE code=? AND suggestion=?", (r["code"], r["suggestion"]))}; self.assertNotIn("ITEM RECEBIDO", st)           # nunca sugere o que já foi recebido
            self.assertEqual(c.execute("SELECT COUNT(*) FROM rd_projects WHERE code=? AND suggestion=? AND (sample_bought IS NOT NULL OR sample_sent IS NOT NULL)", (r["code"], r["suggestion"])).fetchone()[0], 0)   # nem o que já tem amostra
        code = d["rows"][0]["code"]; kind = d["rows"][0]["suggestion"]
        c.execute("UPDATE rd_projects SET sample_bought='2026-10-01' WHERE code=? AND suggestion=?", (code, kind)); c.commit(); c.close()
        self.assertNotIn((code, kind), {(r["code"], r["suggestion"]) for r in C.get("/api/purchases/pending?page=1").json["rows"] + C.get("/api/purchases/pending?page=2").json["rows"]})
        self.assertTrue(C.get("/api/export/pendente_compras.xlsx").status_code == 200)

    def test_15_desenhos_zip_prefixo_red_des(self):
        import zipfile, io
        from PIL import Image
        def png(color):
            b = io.BytesIO(); Image.new("RGB", (40, 30), color).save(b, "PNG"); return b.getvalue()
        z = io.BytesIO()
        with zipfile.ZipFile(z, "w") as f:
            f.writestr("lote/RED_AMD9001_REV02.png", png("red")); f.writestr("DES-AMD9002 R1.png", png("blue")); f.writestr("lote/DESENHO_AMD9003.png", png("green"))
            f.writestr("../../evil.png", png("black")); f.writestr("__MACOSX/._x.png", b"x"); f.writestr("lote/sub.zip", b"PK"); f.writestr("lote/leiame.txt", b"oi")
        z.seek(0); r = C.post("/api/drawings/check", data={"files": (z, "lote.zip"), "kind": "desenho"}, content_type="multipart/form-data").json
        by = {i["name"]: i for i in r["items"]}; self.assertEqual(r["zips"][0]["zip"], "lote.zip")
        self.assertEqual(by["RED_AMD9001_REV02.png"]["origin"], "REDESENVOLVIMENTO"); self.assertEqual(by["RED_AMD9001_REV02.png"]["codes"], ["AMD9001"]); self.assertEqual(by["RED_AMD9001_REV02.png"]["rev_num"], 2)
        self.assertEqual(by["DES-AMD9002 R1.png"]["origin"], "DESENVOLVIMENTO"); self.assertIsNone(by["DESENHO_AMD9003.png"]["origin"])        # «DESENHO_» não é o prefixo DES
        self.assertNotIn("sub.zip", by); self.assertNotIn("._x.png", by); self.assertIn("evil.png", by); self.assertTrue(any("ZIP dentro do ZIP" in w for w in r["warnings"]))   # sem zip-slip: só o nome do arquivo
        ap = C.post("/api/drawings/apply", json={"token": r["token"], "overrides": {}}).json["summary"]; self.assertEqual((ap["redesenvolvimento"], ap["desenvolvimento"]), (1, 1))
        g = C.get("/api/drawings?origin=REDESENVOLVIMENTO").json; self.assertEqual([c["code"] for c in g["rows"] if c["code"]], ["AMD9001"]); self.assertEqual(g["rows"][0]["origin"], "REDESENVOLVIMENTO")
        self.assertFalse(os.path.exists(os.path.join(ROOT, "evil.png"))); self.assertEqual(C.post("/api/drawings/check", data={"files": (io.BytesIO(b"nao zip"), "x.zip")}, content_type="multipart/form-data").json["warnings"][0].endswith("não é um ZIP válido."), True)

    def test_16_pedidos_em_aberto(self):
        c = sqlite3.connect(DB); c.execute("DELETE FROM ds_compras")
        c.executemany("INSERT INTO ds_compras(pedido,supplier,code,description,qty_ordered,qty_pending,order_date,due_date,ex_code) VALUES(?,?,?,?,?,?,?,?,?)",
                      [("P1", "x", "MP-100", "AMORTECEDOR DIANT", 100, 100, "2026-01-05", "2026-07-01", "EX0002116"), ("P2", "x", "MP-101", "AMORTECEDOR TRAS", 50, 20, "2026-02-01", "2026-08-01", "EX0002110"), ("P3", "x", "AMD200", "AMORTECEDOR", 9, 9, "2026-02-01", None, "EX0002116"),
                       ("P4", "x", "MP-102", "BANDEJA", 9, 9, "2026-02-01", None, "EX0002116"), ("P5", "x", "MP-103", "AMORTECEDOR", 7, 7, "2026-03-01", None, "EX008042"), ("P6", "x", "MP-104", "AMORTECEDOR", 7, 7, "2026-03-02", None, "EX777"), ("P7", "x", "MP-105", "AMORTECEDOR", 7, 0, "2026-03-02", None, "EX0002116")])
        c.commit(); c.close(); r = C.get("/api/pedidos-em-aberto").json
        self.assertEqual(r["columns"], ["codigo", "numero_pedido", "DATA_EMISSAO_PC", "quantidade", "DATA_PREV_ENT", "fornecedor", "STATUS_PC"]); self.assertTrue(all(set(x) == set(r["columns"]) | {"em_aberto", "TIPO_PEDIDO"} for x in r["rows"])); r["rows"] = [x for x in r["rows"] if x["em_aberto"]]
        self.assertEqual([(x["codigo"], x["fornecedor"], x["quantidade"]) for x in r["rows"]], [("MP-100", "ZS", 100), ("MP-101", "E-WIN", 20), ("MP-103", "XGM", 7), ("MP-104", "VERIFICAR")[:2] + (7,)])
        self.assertEqual(r["summary"]["verificar"], 1)

    def test_17_vendas_curva_a(self):
        c = sqlite3.connect(DB); c.execute("DELETE FROM ds_vendas")
        c.executemany("INSERT INTO ds_vendas(pedido,code,qty,total,sale_date,line) VALUES(?,?,?,?,?,?)", [("1", "AMD1", 2, 200, "2026-10-02", "AMORTECEDOR"), ("2", "AMD1", 3, 310, "2026-10-09", "AMORTECEDOR"), ("3", "AMD2", 1, 900, "2026-10-10", "AMORTECEDOR LINHA PESADA"),
                       ("4", "AMD3", 5, 40, "2026-09-10", "AMORTECEDOR"), ("5", "TRM1", 9, 9999, "2026-10-10", "TERMINAL")]); c.commit(); c.close()
        r = C.get("/api/vendas/curva-a?year=2026&month=10").json                      # padrão = BI: LINHA = AMORTECEDOR exata (etapa C1)
        self.assertEqual([(x["PRODUTO"], x["QTD"], x["VALOR"]) for x in r["rows"]], [("AMD1", 5, 510)]); self.assertEqual(r["rows"][0]["classe"], "A")
        r2 = C.get("/api/vendas/curva-a?year=2026&month=10&linhas=amortecedor,pesada").json
        self.assertEqual([(x["PRODUTO"], x["QTD"], x["VALOR"]) for x in r2["rows"]], [("AMD2", 1, 900), ("AMD1", 5, 510)])
        self.assertEqual([x["PRODUTO"] for x in C.get("/api/vendas/curva-a?year=2026").json["rows"]], ["AMD1", "AMD3"]); self.assertIn("2026", r["years"])

    def test_18_garantia_e_fob(self):
        import io, pandas as pd
        self.assertEqual(C.get("/api/warranty").status_code, 404)          # etapa 18: a garantia só vem do servidor (rotas antigas da planilha saíram)
        code = sqlite3.connect(DB).execute("SELECT perfect_code FROM products ORDER BY id LIMIT 1").fetchone()[0]
        b = io.BytesIO(); pd.DataFrame({"Linha": ["AMORTECEDOR"] * 2, "Codigo": ["S1", "S2"], "Mínimo": [7.25, 9], "Melhor Preço": ["E-WIN = DES. 2026-11-03", "ZS = DES. 2026-11-03"], "PartNumber": [code, "NAOEXISTE"], "FOB EWIN": ["$ 7,25", None], "FOB ZS": [None, "$ 9"], "FOB XGM": [None, None]}).to_excel(b, index=False); b.seek(0)
        r = C.post("/api/fob/import", data={"file": (b, "fob.xlsx")}, content_type="multipart/form-data").json; self.assertEqual((r["com_fob"], r["fob_sem_produto"]), (1, 1))
        self.assertEqual(sqlite3.connect(DB).execute("SELECT fob, fob_supplier FROM products WHERE perfect_code=?", (code,)).fetchone(), (7.25, "E-WIN"))
        for slug in ("pedidos-aberto", "vendas", "garantia", "metas"): self.assertEqual(C.get("/" + slug).status_code, 200, slug)

    def test_19_lados_atalhos_batem_com_a_lista(self):
        """Cada número da tela Lados é um atalho: clicar nele filtra a lista e o total tem de ser o mesmo número."""
        for esc in ("lados", "todos"):
            d = C.get(f"/api/sides?escopo={esc}").json; s = d["stats"]; self.assertEqual(d["total"], s["total"])
            self.assertGreater(s["total"], 0, esc)
            atalhos = {"dianteiro": "axle=dianteiro", "traseiro": "axle=traseiro", "traseiro_exato": "other=exata&axle=dianteiro", "traseiro_desenvolvimento": "other=desenvolvimento&axle=dianteiro",
                       "traseiro_provavel": "other=provavel&axle=dianteiro", "traseiro_nao": "other=nao&axle=dianteiro", "sem_aplicacao": "other=sem_aplicacao", "sem_par": "pair=sem", "com_par": "pair=com",
                       "direito": "side=direito", "esquerdo": "side=esquerdo", "ativo": "status=ativo", "em_breve": "status=em_breve", "inativo": "status=inativo"}
            for k, f in atalhos.items(): self.assertEqual(C.get(f"/api/sides?escopo={esc}&{f}").json["total"], s[k], f"{esc}: {k}")
        self.assertEqual(C.get("/api/export/lados.xlsx?escopo=todos&axle=traseiro").status_code, 200)

    def test_20_amostras_e_envio_atalhos(self):
        """Compra de amostras: «Pendente fornecedor» e «Para enviar» filtram a lista (e batem com o total). Envio: status=todos traz também os finalizados."""
        con = sqlite3.connect(DB)
        try:
            con.executemany("INSERT INTO sample_orders(perfect_code,stage,to_send,pending_supplier,supplier) VALUES(?,?,?,?,?)", [("T20A", "cotacao", 1, 0, "ZS"), ("T20B", "chegou", 0, 1, "ZS"), ("T20C", "cotacao", 1, 1, "E-WIN")])
            con.executemany("INSERT INTO sample_shipments(perfect_code,status,supplier) VALUES(?,?,?)", [("T20S1", "pendente_projeto", "ZS"), ("T20S2", "finalizada", "ZS")]); con.commit()
        finally: con.close()
        d = C.get("/api/samples?q=T20").json; self.assertEqual(d["totals"]["n"], 3)
        self.assertEqual(sorted(r["perfect_code"] for r in C.get("/api/samples?q=T20&flag=enviar").json["rows"]), ["T20A", "T20C"])
        self.assertEqual(sorted(r["perfect_code"] for r in C.get("/api/samples?q=T20&flag=pendente_fornecedor").json["rows"]), ["T20B", "T20C"])
        tudo = C.get("/api/samples").json["totals"]
        self.assertEqual(C.get("/api/samples?flag=enviar").json["totals"]["n"], tudo["to_send"]); self.assertEqual(C.get("/api/samples?flag=pendente_fornecedor").json["totals"]["n"], tudo["pending_supplier"])
        self.assertEqual([r["perfect_code"] for r in C.get("/api/shipments?q=T20S").json["rows"]], ["T20S1"])                  # padrão: só em aberto
        self.assertEqual(sorted(r["perfect_code"] for r in C.get("/api/shipments?q=T20S&status=todos").json["rows"]), ["T20S1", "T20S2"])
        s = C.get("/api/shipments?status=todos").json; self.assertEqual(s["total"], s["summary"]["pendente_projeto"] + s["summary"]["enviada"] + s["summary"]["finalizada"])
        for x in ("amostras.xlsx?flag=enviar", "envio.xlsx?status=todos", "pendente_compras.xlsx?kind=des"): self.assertEqual(C.get("/api/export/" + x).status_code, 200, x)

    def test_21_desenhos_atalhos_e_excel(self):
        """Desenhos: cada número do topo é um atalho (where=…) e bate com o total da galeria; «sem desenho» lista os itens; o Excel segue os filtros."""
        import io
        from openpyxl import load_workbook
        if not C.get("/api/drawings?kind=desenho").json["total"]: self.test_15_desenhos_zip_prefixo_red_des()      # módulo rodado sozinho com filtro
        for kind in ("desenho", "projeto"):
            s = C.get(f"/api/drawings/stats?kind={kind}").json; tot = lambda w: C.get(f"/api/drawings?kind={kind}&where={w}").json["total"]
            self.assertEqual(tot(""), s["codes"] + s["orphans"], kind); self.assertEqual(tot("sem"), s["orphans"], kind); self.assertEqual(tot("falta"), s["missing"], kind)
            for w in ("cat", "des", "rd"): self.assertEqual(tot(w), s[w], f"{kind}: {w}")
        s = C.get("/api/drawings/stats?kind=desenho").json; self.assertGreater(s["codes"], 0); self.assertGreater(s["orphans"], 0); self.assertGreater(s["missing"], 0)
        f = C.get("/api/drawings?kind=desenho&where=falta&all=1").json["rows"]; com = {c["key"] for c in C.get("/api/drawings?kind=desenho&all=1").json["rows"] if c["code"]}
        self.assertEqual(len(f), s["missing"]); self.assertTrue(all(r["missing"] and r["code"] and r["key"] not in com for r in f))
        alvo = f[0]["code"]; self.assertIn(alvo, [r["code"] for r in C.get(f"/api/drawings?kind=desenho&where=falta&q={alvo}").json["rows"]])
        def linhas(qs):
            r = C.get("/api/export/desenhos.xlsx?" + qs); self.assertEqual(r.status_code, 200, qs); return load_workbook(io.BytesIO(r.data)).worksheets[0].max_row - 1
        self.assertEqual(linhas("kind=desenho&where=falta"), s["missing"])
        red = [c for c in C.get("/api/drawings?kind=desenho&origin=REDESENVOLVIMENTO&all=1").json["rows"] if c["code"]]; self.assertTrue(red)
        self.assertEqual(linhas("kind=desenho&origin=REDESENVOLVIMENTO"), sum(c["n_files"] for c in red))       # todas as revisões dos códigos filtrados
        self.assertEqual(linhas("kind=projeto"), 0)

    def test_22_damping_atalhos_e_excel(self):
        """Damping: cada resultado (aprovado/reprovado/incompleto) é um atalho que bate com a lista; o Excel segue os filtros; excluir apaga os pontos."""
        import io
        from openpyxl import load_workbook
        con = sqlite3.connect(DB)
        try:
            con.execute("DELETE FROM damping_rules"); con.execute("DELETE FROM damping_params")
            con.executemany("INSERT INTO damping_rules(table_name,seq,velocity,tolerance) VALUES(?,?,?,?)", [("Pf", 0, .05, .2), ("Pf", 1, .3, .15), ("Py", 0, .05, .2), ("Py", 1, .3, .15)])
            con.executemany("INSERT INTO damping_params(key,value) VALUES(?,?)", [("threshold", 1000), ("offset", 30)]); con.commit()
        finally: con.close()
        def ensaio(code, found):              # 4 pontos com DRAWING 500 N: faixa 430–570 N na 1ª velocidade (abaixo do limite → ajuste de 30 N)
            pts = [{"table": t, "velocity": v, "drawing": "500", "found": f} for (t, v), f in zip([("Pf", .05), ("Pf", .3), ("Py", .05), ("Py", .3)], found)]
            r = C.post("/api/damping/tests", json={"perfect_code": code, "label": "lote T22", "points": pts}); self.assertEqual(r.status_code, 200, r.json); return r.json["id"]
        ids = {"APPROVED": ensaio("T22A", ["500"] * 4), "DISAPPROVED": ensaio("T22B", ["500", "500", "1000", "500"]), "INCOMPLETO": ensaio("T22C", ["500", "", "", ""])}
        t = C.get(f"/api/damping/tests/{ids['APPROVED']}").json; p = t["points"][0]
        self.assertEqual((round(p["min"]), round(p["max"]), p["result"]), (430, 570, "APPROVED"))
        d = C.get("/api/damping/tests?q=T22").json; self.assertEqual(d["total"], 3); self.assertEqual(d["counts"], {"APPROVED": 1, "DISAPPROVED": 1, "INCOMPLETO": 1, "all": 3})
        for res, i in ids.items():
            r = C.get(f"/api/damping/tests?q=T22&res={res}").json; self.assertEqual([x["id"] for x in r["rows"]], [i], res); self.assertEqual(r["counts"], d["counts"])
        self.assertEqual(r["rows"][0]["points_filled"], 1); self.assertEqual(r["rows"][0]["points_total"], 4)
        tudo = C.get("/api/damping/tests").json; self.assertEqual(sum(tudo["counts"][k] for k in ids), tudo["counts"]["all"])
        def linhas(qs):
            r = C.get("/api/export/damping.xlsx?" + qs); self.assertEqual(r.status_code, 200, qs); wb = load_workbook(io.BytesIO(r.data)); return [ws.max_row - 1 for ws in wb.worksheets[:2]]
        self.assertEqual(linhas("q=T22"), [3, 12]); self.assertEqual(linhas("q=T22&res=DISAPPROVED"), [1, 4])
        self.assertEqual([p["drawing"] for p in C.get("/api/damping/prefill?code=T22C").json], [500.0] * 4)
        C.delete(f"/api/damping/tests/{ids['INCOMPLETO']}")
        con = sqlite3.connect(DB)
        try: self.assertEqual(con.execute("SELECT COUNT(*) FROM damping_points WHERE test_id=?", (ids["INCOMPLETO"],)).fetchone()[0], 0)
        finally: con.close()
        self.assertEqual(C.get("/api/damping/tests?q=T22").json["counts"]["INCOMPLETO"], 0)

    def test_23_aplicacoes_equivalencias_atalhos(self):
        """Aplicações: eixo e lado (inclusive «não informado») são atalhos que batem com a lista. Equivalências: status, confiança e «sem diferenças» idem;
        crit/dif/miss aceitam «|» (URL da tela) como os parâmetros repetidos; o Excel traz o mesmo número de linhas."""
        import io
        from openpyxl import load_workbook
        con = sqlite3.connect(DB)
        try:
            pid = con.execute("SELECT id FROM products ORDER BY id LIMIT 1").fetchone()[0]
            con.execute("INSERT INTO applications(product_id,make,model,year_from,year_to,axle,side) VALUES(?,?,?,?,?,?,?)", (pid, "T23", "SEM EIXO", 2020, 2021, None, None)); con.commit()
        finally: con.close()
        for flt in ("", "make=T23", "q=strada"):
            d = C.get(f"/api/applications?{flt}").json; s = d["stats"]
            for k, n in s.items():
                g, v = k.split(":"); self.assertEqual(C.get(f"/api/applications?{flt}&{g}={v}").json["total"], n, f"{flt} {k}")
        d = C.get("/api/applications").json; self.assertGreater(d["stats"]["axle:dianteiro"], 0); self.assertGreaterEqual(d["stats"]["axle:sem"], 1)
        self.assertEqual(d["stats"]["axle:dianteiro"] + d["stats"]["axle:traseiro"] + d["stats"]["axle:sem"], d["total"])
        self.assertEqual(d["kpis"]["makes"] >= 1 and d["kpis"]["products"] <= d["total"], True)
        r = C.get("/api/export/aplicacoes.xlsx?axle=sem"); self.assertEqual(load_workbook(io.BytesIO(r.data)).worksheets[0].max_row - 1, d["stats"]["axle:sem"])
        if not C.get("/api/equivalences").json["total"]: C.post("/api/equivalences/generate")
        e = C.get("/api/equivalences").json; self.assertGreater(e["total"], 0)
        for grp, par in (("status_counts", "status"), ("conf_counts", "confidence"), ("diff_counts", "diff")):
            self.assertEqual(sum(e[grp].values()), e["total"], grp)
            for v, n in e[grp].items(): self.assertEqual(C.get(f"/api/equivalences?{par}={v}").json["total"], n, f"{par}={v}")
        crit = [k.split(":", 1)[1] for k, n in e["facets"].items() if k.startswith("crit:") and n][:2]; self.assertTrue(crit)
        junto = C.get("/api/equivalences?crit=" + "|".join(crit)).json["total"]
        self.assertEqual(junto, C.get("/api/equivalences?" + "&".join("crit=" + c for c in crit)).json["total"])
        r = C.get("/api/equivalences/export.xlsx?crit=" + "|".join(crit)); self.assertEqual(load_workbook(io.BytesIO(r.data)).worksheets[0].max_row - 1, junto)
        ids = [str(x) for x in range(1, 7)]; self.assertLessEqual(len(C.get("/api/compare?ids=" + ",".join(ids)).json), 4)

    def test_24_dashboard_brands_atalhos(self):
        """Dashboard: totais, barras do funil (status) e pendências por controle abrem a lista de DES/R-D com o mesmo número; produtos = lista de Produtos.
        Brands: cartões de marca, «onde está» e controles contam como a lista filtrada (cada grupo ignora o próprio filtro); Excel de «Sem marca» só com os sem marca."""
        import io
        from urllib.parse import quote
        from openpyxl import load_workbook
        d = C.get("/api/dashboard").json
        self.assertEqual(d["stats"]["products"], C.get("/api/products").json["total"])
        for r in d["system"]:
            if r["s"] != "nd": self.assertEqual(C.get(f"/api/products?system={r['s']}").json["total"], r["n"], r["s"])     # botões FORCE GAS / FORCE OIL
        for k, slug in (("DESENVOLVIMENTO", "des"), ("REDESENVOLVIMENTO", "rd")):
            self.assertEqual(d["totals"][k], C.get(f"/api/rd/{slug}").json["total"], k)
            self.assertTrue(d["funnel"][k], k)
            for r in d["funnel"][k]: self.assertEqual(C.get(f"/api/rd/{slug}?status={quote(r['status'])}").json["total"], r["n"], f"{k} {r['status']}")
            for fl, n in d["flags"][k].items():
                if n and fl != "nenhum": self.assertEqual(C.get(f"/api/rd/{slug}?flag={fl}").json["total"], n, f"{k} {fl}")
        s = C.get("/api/brands").json
        for flt in ("", "scope=catalog&q=a", "flag=pend_compras"):
            c = C.get(f"/api/brands/PERFECT/items?{flt}").json["counts"]
            for m, n in c["brand"].items():
                x = C.get(f"/api/brands/{m}/items?{flt}").json; self.assertEqual(x["total"] - x["fora_base"], n, f"{flt} marca {m}")      # PN Ford fora da base: na lista, fora do cartão (D7)
            for b in ("PERFECT", "MOTORCRAFT"):
                c = C.get(f"/api/brands/{b}/items?{flt}").json["counts"]
                base = "&".join(x for x in flt.split("&") if x and not x.startswith("scope="))
                for sc, n in c["scope"].items(): self.assertEqual(C.get(f"/api/brands/{b}/items?{base}" + ("" if sc == "all" else f"&scope={sc}")).json["total"], n, f"{b} {flt} scope {sc}")
                base = "&".join(x for x in flt.split("&") if x and not x.startswith("flag="))
                for fl, n in c["flag"].items(): self.assertEqual(C.get(f"/api/brands/{b}/items?{base}&flag={fl}").json["total"], n, f"{b} {flt} flag {fl}")
        tot = C.get("/api/brands/PERFECT/items").json
        self.assertEqual(sum(tot["counts"]["brand"].values()) + s["fora_base"], s["total"]); self.assertEqual(tot["counts"]["brand"]["PERFECT"], tot["total"]); self.assertGreater(tot["total"], 0)
        r = C.get("/api/export/brands.xlsx?brand=OUTROS"); self.assertEqual(r.status_code, 200)
        wb = load_workbook(io.BytesIO(r.data)); ws = wb.worksheets[0]; self.assertEqual(ws.max_row - 1, s["unclassified"])
        r = C.get("/api/export/brands.xlsx?brand=PERFECT&scope=catalog"); n = C.get("/api/brands/PERFECT/items?scope=catalog").json["total"]
        self.assertEqual(load_workbook(io.BytesIO(r.data)).worksheets[0].max_row - 1, n)

    def test_25_dados_pendencias_fontes(self):
        """Pendências: status, tipo e campo são atalhos (cada grupo ignora o próprio filtro e respeita os outros); status=todas = sem filtro de status;
        resolver tira da contagem de abertas; o Excel traz as mesmas linhas. Fontes: o histórico conta gravadas × só verificação e o Excel segue o status."""
        import io
        from openpyxl import load_workbook
        con = sqlite3.connect(DB)
        try:
            p = [r[0] for r in con.execute("SELECT id FROM products ORDER BY id LIMIT 3")]
            con.executemany("INSERT INTO pendencies(product_id,kind,field,description,status) VALUES(?,?,?,?,?)", [
                (p[0], "conflito", "family", "Valor atual «A» × importado «B» (fonte T25.xlsx). Nada foi sobrescrito.", "aberta"),
                (p[1], "conflito", "ean", "Valor atual «1» × importado «2» (fonte T25.xlsx). Nada foi sobrescrito.", "aberta"),
                (p[2], "campo_ausente", "peso", "Campo ausente: peso T25", "aberta"), (p[0], "campo_ausente", "peso", "Campo ausente: peso T25", "resolvida"),
                (p[1], "conflito", "family", "T25 ignorada", "ignorada")])
            src = con.execute("INSERT INTO sources(name,category,priority) VALUES('T25.xlsx','Dados avulsos (planilha nova)',5)").lastrowid
            con.executemany("INSERT INTO import_batches(source_id,filename,category,rows_new,status) VALUES(?,?,?,?,?)", [(src, "T25.xlsx", "Dados avulsos (planilha nova)", 1, "ok"), (src, "T25.xlsx", "Dados avulsos (planilha nova)", 0, "simulado")])
            con.commit()
        finally: con.close()
        for flt in ("", "q=T25", "kind=conflito", "status=aberta&field=peso", "status=todas&q=T25"):
            c = C.get(f"/api/pendencies?{flt}").json["counts"]
            for grp in ("status", "kind", "field"):
                base = "&".join(x for x in flt.split("&") if x and not x.startswith(grp + "="))
                for v, n in c[grp].items(): self.assertEqual(C.get(f"/api/pendencies?{base}&{grp}={v}").json["total"], n, f"{flt} {grp}={v}")
            self.assertEqual(sum(n for v, n in c["status"].items() if v != "todas"), c["status"]["todas"], flt)
        d = C.get("/api/pendencies?q=T25").json
        self.assertEqual(d["counts"]["status"], {"todas": 5, "aberta": 3, "resolvida": 1, "ignorada": 1}); self.assertEqual(d["counts"]["kind"], {"conflito": 3, "campo_ausente": 2})
        self.assertEqual(C.get("/api/pendencies?q=T25&status=todas").json["total"], 5)
        r = C.get("/api/export/pendencias.xlsx?q=T25&status=aberta&kind=conflito"); self.assertEqual(r.status_code, 200)
        self.assertEqual(load_workbook(io.BytesIO(r.data)).worksheets[0].max_row - 1, 2)
        i = next(x["id"] for x in C.get("/api/pendencies?q=T25&status=aberta&field=ean").json["rows"])
        self.assertEqual(C.post(f"/api/pendencies/{i}", json={"status": "resolvida"}).status_code, 200)
        self.assertEqual(C.get("/api/pendencies?q=T25").json["counts"]["status"]["aberta"], 2)
        h = C.get("/api/history").json; n = {s: sum(1 for b in h["batches"] if b["status"] == s) for s in {b["status"] for b in h["batches"]}}
        self.assertEqual(h["counts"], {"todas": len(h["batches"]), **n}); self.assertGreaterEqual(n["simulado"], 1); self.assertGreaterEqual(n["ok"], 1)
        for s in n:
            r = C.get(f"/api/export/fontes.xlsx?status={s}"); self.assertEqual(load_workbook(io.BytesIO(r.data)).worksheets[0].max_row - 1, n[s], s)
        j = next(x["id"] for x in C.get("/api/pendencies?q=T25&status=aberta&field=family").json["rows"])          # «Usar o da planilha» (etapa D)
        self.assertEqual(C.post(f"/api/pendencies/{j}/apply").json, {"field": "family", "value": "B", "old": "A"})
        self.assertEqual(C.post(f"/api/pendencies/{j}/apply").status_code, 400)
        con = sqlite3.connect(DB)
        try: self.assertEqual(con.execute("SELECT family FROM products WHERE id=?", (p[0],)).fetchone()[0], "B")
        finally: con.close()

    def test_26_anomalias(self):
        """Anomalias (antiga Equivalências): família catálogo × Inmetro e EAN em conflito; /equivalencias redireciona para a aba de sugestões; Excel com as duas abas."""
        import io
        from openpyxl import load_workbook
        r = C.get("/equivalencias?status=pendente"); self.assertEqual(r.status_code, 302); self.assertIn("/anomalias?", r.headers["Location"]); self.assertIn("tab=sugestoes", r.headers["Location"]); self.assertIn("status=pendente", r.headers["Location"])
        con = sqlite3.connect(DB)
        try:
            p = con.execute("INSERT INTO products(perfect_code,description,family,ean) VALUES('AMDT26','T26 AMORTECEDOR','CONVENCIONAL','789')").lastrowid
            con.executemany("INSERT INTO certificates(product_id,perfect_code_raw,inmetro_number,family,supplier) VALUES(?,?,?,?,?)", [(p, "AMDT26", "001/2026", "ESTRUTURAL", "ZS"), (p, "AMDT26", "002/2026", "CONVENCIONAL", "E-WIN")])
            con.execute("INSERT INTO pendencies(product_id,kind,field,description) VALUES(?,?,?,?)", (p, "conflito", "ean", "Valor atual «789» × importado «790» (fonte T26.xlsx). Nada foi sobrescrito."))
            con.execute("INSERT INTO applications(product_id,make,model,year_from,year_to,axle,side) VALUES(?,?,?,?,?,?,?)", (p, "FIAT", "UNO T26", 2010, 2014, "dianteiro", "ambos")); con.commit()
        finally: con.close()
        f = C.get("/api/anomalies?q=T26").json; self.assertEqual([x["perfect_code"] for x in f["rows"]], ["AMDT26"]); self.assertEqual(f["rows"][0]["inmetro_families"], ["CONVENCIONAL", "ESTRUTURAL"])
        # update 4 · Q7: descrição e aplicação do item em todas as abas (e no Excel)
        self.assertEqual((f["rows"][0]["description"], f["rows"][0]["application"]), ("T26 AMORTECEDOR", "FIAT - UNO T26 - DIANT. LD/LE - 2010/2014"))
        import anomalias
        self.assertEqual(anomalias.com_itens("repetidos", [{"codigos": ["AMDT26", "AMDNADA"]}])[0]["itens"],
                         [{"code": "AMDT26", "description": "T26 AMORTECEDOR", "application": "FIAT - UNO T26 - DIANT. LD/LE - 2010/2014"}, {"code": "AMDNADA", "description": None, "application": ""}])
        e = C.get("/api/anomalies?tab=ean&q=T26").json; self.assertEqual([(x["current"], x["imported"], x["source"]) for x in e["rows"]], [("789", "790", "T26.xlsx")])
        self.assertEqual((f["counts"]["familia"], f["counts"]["ean"]), (1, 1))
        wb = load_workbook(io.BytesIO(C.get("/api/anomalies/export.xlsx?q=T26").data)); self.assertEqual([ws.max_row - 1 for ws in wb.worksheets[:2]], [1, 1])
        self.assertEqual([c.value for c in wb.worksheets[0][2]][:3], ["AMDT26", "T26 AMORTECEDOR", "FIAT - UNO T26 - DIANT. LD/LE - 2010/2014"])
        self.assertIn("Anomalias", C.get("/anomalias").get_data(as_text=True))

    def test_27_excel_pesquisa_inmetro_fob_estoque(self):
        """D9: o Excel da Pesquisa (e de Produtos) traz a família do Inmetro, o FOB (menor preço e fornecedor) e o estoque (disponível e reservado)."""
        import io
        from openpyxl import load_workbook
        con = sqlite3.connect(DB)
        try:
            p = con.execute("SELECT id FROM products WHERE perfect_code='AMDT26'").fetchone()[0]
            con.execute("UPDATE products SET fob=12.5, fob_supplier='ZS' WHERE id=?", (p,))
            con.executemany("INSERT INTO ds_estoque(code,warehouse,qty,reserved) VALUES(?,?,?,?)", [("AMDT26", "01", 30, 5), ("amd-t26", "02", 12, 0)]); con.commit()
        finally: con.close()
        for slug in ("pesquisa", "produtos"):
            ws = load_workbook(io.BytesIO(C.get(f"/api/export/{slug}.xlsx?q=AMDT26").data)).worksheets[0]
            head = [c.value for c in ws[1]]; row = dict(zip(head, [c.value for c in ws[2]]))
            self.assertEqual(ws.max_row, 2, slug); self.assertEqual(row["Código PERFECT"], "AMDT26")
            self.assertEqual(row["Família Inmetro"], "CONVENCIONAL; ESTRUTURAL"); self.assertEqual((row["FOB menor (US$)"], row["Fornecedor do FOB"]), (12.5, "ZS"))
            self.assertEqual((row["Estoque disponível"], row["Estoque reservado"]), (42, 5))

    def test_27b_excel_pesquisa_caixa_abas_e_nome(self):
        """Etapa 24 · Q1–Q2: o Excel da Pesquisa traz a caixa e as medidas da caixa (C x L x A) em outra coluna, as abas Aplicações e DES e R-D,
        e o item selecionado (código buscado; montadora, modelo e ano) no nome do arquivo. Produtos continua sem filtro no nome."""
        import io, re, datetime
        from urllib.parse import unquote
        from openpyxl import load_workbook
        if not C.get("/api/products?q=AMDT26").json["total"]: self.test_26_anomalias()
        con = sqlite3.connect(DB)
        try:
            con.execute("INSERT OR REPLACE INTO packaging_boxes(code,length_mm,width_mm,height_mm,raw_dims) VALUES('PP913',425,85,60,'425x85x60')")
            con.execute("UPDATE products SET package_code='PP913M' WHERE perfect_code='AMDT26'"); con.commit()
        finally: con.close()
        nome = lambda r: unquote((re.search(r"filename\*=UTF-8''([^;]+)", r.headers["Content-Disposition"]) or re.search(r"filename=\"?([^\";]+)", r.headers["Content-Disposition"])).group(1))
        dia = datetime.date.today().strftime("%d-%m")
        r = C.get("/api/export/pesquisa.xlsx?q=AMDT26"); wb = load_workbook(io.BytesIO(r.data)); ws = wb["Produtos"]
        row = dict(zip([c.value for c in ws[1]], [c.value for c in ws[2]]))
        self.assertEqual((row["Caixa"], row["Medidas da caixa (C x L x A, mm)"]), ("PP913M", "425 x 85 x 60"))
        for k in ("Curso (mm)", "Ø tubo (mm)", "Fixação superior", "NCM", "Descrição (inglês)", "Nº Inmetro"): self.assertIn(k, row)
        self.assertEqual(wb.sheetnames[:3], ["Produtos", "Aplicações", "DES e R-D"])
        self.assertEqual(nome(r), f"PerfectAmortecedores - Pesquisa de amortecedores - AMDT26 - {dia}.xlsx")
        self.assertEqual(nome(C.get("/api/export/pesquisa.xlsx?make=Fiat&model=Toro&year=2020")), f"PerfectAmortecedores - Pesquisa de amortecedores - FIAT TORO 2020 - {dia}.xlsx")
        self.assertEqual(nome(C.get("/api/export/pesquisa.xlsx")), f"PerfectAmortecedores - Pesquisa de amortecedores - {dia}.xlsx")
        self.assertEqual(nome(C.get("/api/export/produtos.xlsx?q=AMDT26")), f"PerfectAmortecedores - Produtos e códigos - {dia}.xlsx")

    def test_28_garantia_planilha(self):
        """D8/etapa 18: sem dados do servidor, /api/garantias avisa e o Excel recusa; com a tabela da tela preenchida, rota e Excel seguem os filtros."""
        import io, datetime, garantias
        from openpyxl import load_workbook
        self.assertFalse(C.get("/api/garantias").json["available"]); self.assertEqual(C.get("/api/export/garantia.xlsx").status_code, 400)
        y = datetime.date.today().year; con = sqlite3.connect(DB)
        try:
            for s in garantias.TABLE.split(";"):
                if s.strip(): con.execute(s)
            con.executemany("INSERT INTO garantias(autorizacao,data_cadastro,tipo,status,codigo,qtd,valor,defeito,fornecedor,procedencia,unidade,cliente) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                            [("1", f"{y}-01-05", "GARANTIA", "GARANTIA FINALIZADA", "AMD1", 2, 20.0, "SEM AÇÃO", "ZS", "PROCEDENTE", "PRIVATE-MOGI", "C1"),
                             ("2", f"{y}-02-05", "ACORDO COMERCIAL", "PAGAMENTO FINALIZADO", "AMD2", 4, 40.0, "VAZAMENTO", "E-WIN", None, "PRIVATE-ARUJA", "C2")]); con.commit()
        finally: con.close()
        d = C.get("/api/garantias").json; self.assertTrue(d["available"]); self.assertEqual((d["total"], d["kpis"]["pecas"]), (1, 2))
        self.assertEqual(C.get("/api/garantias?tipo=todos").json["total"], 2); self.assertEqual(C.get("/api/garantias?tipo=todos&fornecedor=E-WIN").json["kpis"]["pecas"], 4)
        wb = load_workbook(io.BytesIO(C.get("/api/export/garantia.xlsx?tipo=todos").data)); self.assertEqual(wb.worksheets[0].max_row - 1, 2); self.assertEqual(wb.worksheets[0].title, "Ocorrências")

    def test_29_estoque_atalhos(self):
        """C2–C4: cada atalho de situação/classe = total da lista; resumo do Q10 na rota de vendas; Excel do Estoque com os filtros."""
        import io
        from openpyxl import load_workbook
        con = sqlite3.connect(DB)
        try:          # etapa 20: estoque = PRIVATE + FECT (ds_situacao), só itens do catálogo
            con.execute("INSERT INTO products(perfect_code,description,catalog_position) VALUES('ZZT29','AMORTECEDOR TESTE 29',99999)")
            con.executemany("INSERT INTO ds_situacao(code,active,blocked,stock_total,priv_pa,priv_mp) VALUES(?,'ATIVO','NAO',?,?,?)", [("AMD1", 500, 400, 100), ("ZZT29", 7, 7, 0)]); con.commit()
        finally: con.close()
        d = C.get("/api/estoque").json; self.assertEqual(sum(d["counts"]["situacao"].values()), d["total"]); self.assertGreater(d["total"], 0)
        for k, n in d["counts"]["situacao"].items(): self.assertEqual(C.get(f"/api/estoque?situacao={k}").json["total"], n, k)
        for k, n in d["counts"]["classe"].items(): self.assertEqual(C.get(f"/api/estoque?classe={k}").json["total"], n, k)
        self.assertEqual(C.get("/api/estoque?q=ZZT29").json["rows"][0]["situacao"], "sem_giro")
        self.assertEqual(load_workbook(io.BytesIO(C.get("/api/export/estoque.xlsx?q=ZZT29").data)).worksheets[0].max_row - 1, 1)
        o = C.get("/api/vendas/resumo").json
        if o.get("available") and not o.get("sem_data"): self.assertIn("fechado", o["resumo"]); self.assertIn("parcial", o["resumo"])
        self.assertEqual(len(d["meses"]), 6); self.assertEqual(C.get("/api/estoque?falta=1").json["total"], d["counts"]["falta"])      # projeção (A1)

    def test_31_pagina_do_item(self):
        """Etapa 17 · Q9: /item/<código> reúne tudo do código (catálogo ou DES/R-D); a ficha antiga (data-ficha = id) redireciona para ela; código inexistente = 404."""
        p = C.get("/api/products?size=1").json["rows"][0]
        d = C.get("/api/item/" + p["perfect_code"].lower()).json
        for k in ("topo", "aplicacoes", "lados", "concorrentes", "vendas", "estoque", "pedidos", "desenvolvimento", "amostras", "garantia", "desenhos", "inmetro", "fob", "brands", "pendencias", "anomalias"): self.assertIn(k, d, k)
        self.assertEqual((d["topo"]["code"], d["topo"]["no_catalogo"]), (p["perfect_code"], True)); self.assertNotIn("catalog_position", d["topo"])
        r = C.get(f"/item-id/{p['id']}"); self.assertEqual(r.status_code, 302); self.assertTrue(r.headers["Location"].endswith("/item/" + p["perfect_code"]))
        html = C.get("/item/" + p["perfect_code"]).get_data(as_text=True); self.assertIn("telas/item.js", html); self.assertIn(f"Item {p['perfect_code']}", html)
        con = sqlite3.connect(DB)
        try: rd = con.execute("SELECT code FROM rd_projects WHERE product_id IS NULL LIMIT 1").fetchone()
        finally: con.close()
        if rd:                                                                                      # item só em desenvolvimento: página abre sem dados de catálogo
            x = C.get("/api/item/" + rd[0]); self.assertEqual(x.status_code, 200); self.assertTrue(x.json["desenvolvimento"]["rows"]); self.assertFalse(x.json["topo"]["no_catalogo"])
        self.assertEqual(C.get("/api/item/NAOEXISTE999").status_code, 404)

    def test_32_cobertura_de_concorrentes(self):
        """Etapa 17 · Q12/Q13/Q27: catálogo = concorrente × referência × nosso código (atalhos de curva/linha/concorrente = lista); desenvolvimento = DES em andamento
        com frota da Fraga pelo veículo e anos da aplicação, curva A/B/C pela frota acumulada e selo de lançamento; Excel com as duas abas."""
        import io, datetime
        from openpyxl import load_workbook
        y = datetime.date.today().year; con = sqlite3.connect(DB)
        try:
            pid, pc = con.execute("SELECT id, perfect_code FROM products WHERE catalog_position IS NOT NULL ORDER BY id LIMIT 1").fetchone()
            con.execute("INSERT INTO sources(name,category) SELECT 'CrossCatalogo.xlsx','Referência cruzada' WHERE NOT EXISTS(SELECT 1 FROM sources WHERE name='CrossCatalogo.xlsx')")
            src = con.execute("SELECT id FROM sources WHERE name='CrossCatalogo.xlsx'").fetchone()[0]
            con.executemany("INSERT INTO codes(product_id,code,normalized_code,code_type,brand,source_id) VALUES(?,?,?,?,?,?)", [(pid, "T32-A1", "T32A1", "concorrente", "MONROE", src), (pid, "T32-B1", "T32B1", "concorrente", "NAKATA", src)])
            con.executemany("INSERT INTO rd_projects(code,suggestion,status,description,line,make,vehicle,year_from,year_to,extra) VALUES(?,?,?,?,?,?,?,?,?,?)",
                            [("AMDT32DES1", "DESENVOLVIMENTO", "EM COTAÇÃO", "AMORTECEDOR", "AMORTECEDOR", "FIAT", "UNO MILLE", 2010, 2012, "{}"), ("AMDT32DES2", "DESENVOLVIMENTO", "EM COTAÇÃO", "AMORTECEDOR", "AMORTECEDOR", "VOLKSWAGEN", "GOL", 2024, 2026, "{}"),
                             ("AMDT32DES3", "DESENVOLVIMENTO", "ITEM RECEBIDO", "AMORTECEDOR", "AMORTECEDOR", "FIAT", "UNO", 2010, 2012, "{}"),
                             ("1BPT32DES4", "DESENVOLVIMENTO", "EM COTAÇÃO", "AMORTECEDOR", "AMORTECEDOR", "FIAT", "UNO MILLE", 2010, 2012, "{}")])          # montadora: fora (etapa 18 · Q10)
            con.executemany("INSERT INTO fraga_veiculos(codigo_fraga,marca,veiculo,ano_venda,frota,frota_ano,inicio) VALUES(?,?,?,?,?,?,?)",
                            [("F1", "FIAT", "UNO MILLE FIRE", 2010, 9000, y, "2004-01-01"), ("F1", "FIAT", "UNO MILLE FIRE", 2011, 8000, y, "2004-01-01"), ("F1", "FIAT", "UNO MILLE FIRE", 2015, 7000, y, "2004-01-01"),
                             ("F2", "VOLKSWAGEN", "GOL", 2025, 100, y, "2024-02-01")])
            con.commit()
        finally: con.close()
        d = C.get("/api/cobertura?q=T32").json; self.assertEqual(sorted((r["concorrente"], r["referencia"], r["codigo"]) for r in d["rows"]), [("MONROE", "T32-A1", pc), ("NAKATA", "T32-B1", pc)])
        base = C.get("/api/cobertura").json
        for k in ("curva", "linha", "concorrente"):
            for v, n in list(base["counts"][k].items())[:3]: self.assertEqual(C.get(f"/api/cobertura?{k}={v}").json["total"], n, (k, v))
        self.assertEqual(C.get("/api/cobertura?concorrente=MONROE&q=T32").json["total"], 1)
        des = {r["codigo"]: r for r in C.get("/api/cobertura?tab=desenvolvimento&q=T32").json["rows"]}
        self.assertEqual(set(des), {"AMDT32DES1", "AMDT32DES2"})                                   # recebido e montadora ficam fora
        self.assertEqual((des["AMDT32DES1"]["frota"], des["AMDT32DES1"]["origem"], des["AMDT32DES1"]["lancamento"]), (17000, "Fraga · veículos", False))      # 2015 fora dos anos da aplicação
        self.assertEqual((des["AMDT32DES2"]["frota"], des["AMDT32DES2"]["lancamento"]), (100, True))
        t = C.get("/api/cobertura?tab=desenvolvimento").json
        for k in ("curva", "origem"):
            for v, n in t["counts"][k].items(): self.assertEqual(C.get(f"/api/cobertura?tab=desenvolvimento&{k}={v}").json["total"], n, (k, v))
        self.assertEqual(C.get("/api/cobertura?tab=desenvolvimento&lancamento=1").json["total"], t["counts"]["lancamento"])
        wb = load_workbook(io.BytesIO(C.get("/api/export/cobertura.xlsx?q=T32").data)); self.assertEqual(wb.sheetnames[:2], ["Catálogo", "Desenvolvimento"]); self.assertEqual(wb["Catálogo"].max_row - 1, 2)
        self.assertIn("/cobertura", C.get("/dashboard").get_data(as_text=True))                     # está no menu

    def test_34_cobertura_cofap(self):
        """Etapa 18 · Q5–Q9: aba COFAP — códigos da planilha COFAP × frota sem Motos; «temos» pelo nosso cross (catálogo; DES/R-D AMD fora do catálogo e não
        cancelado); montadora nunca conta; frota com veículo × ano uma vez; curva só em «Não temos»; atalhos = lista; Excel próprio."""
        import io, fraga
        from openpyxl import load_workbook
        con = sqlite3.connect(DB)
        try:
            fraga.ensure(con)
            pid, pc = con.execute("SELECT id, perfect_code FROM products WHERE catalog_position IS NOT NULL ORDER BY id LIMIT 1").fetchone()
            con.execute("INSERT INTO sources(name,category) SELECT 'CrossCatalogo.xlsx','Referência cruzada' WHERE NOT EXISTS(SELECT 1 FROM sources WHERE name='CrossCatalogo.xlsx')")
            src = con.execute("SELECT id FROM sources WHERE name='CrossCatalogo.xlsx'").fetchone()[0]
            con.execute("INSERT INTO codes(product_id,code,normalized_code,code_type,brand,source_id) VALUES(?,?,?,?,?,?)", (pid, "T34-CAT", "T34CAT", "concorrente", "COFAP", src))
            con.executemany("INSERT INTO rd_projects(code,suggestion,status,description,line) VALUES(?,?,?,?,?)", [("AMDT34D", "DESENVOLVIMENTO", "EM COTAÇÃO", "AMORTECEDOR", "AMORTECEDOR"),
                            ("AMDT34X", "DESENVOLVIMENTO", "CANCELADO", "AMORTECEDOR", "AMORTECEDOR"), ("1BPT34", "DESENVOLVIMENTO", "EM COTAÇÃO", "AMORTECEDOR", "AMORTECEDOR")])
            con.executemany("INSERT INTO concorrentes(code,competitor,reference,ref_key,is_oem) VALUES(?,?,?,?,?)", [("AMDT34D", "COFAP", "T34DES", "T34DES", 0), ("AMDT34X", "COFAP", "T34CAN", "T34CAN", 0),
                            ("1BPT34", "COFAP", "T34MON", "T34MON", 0)])
            ins = "INSERT INTO fraga_pecas(codigo_fraga,ano_venda,marca,veiculo,frota,perfect,cofap,classificacao) VALUES(?,?,?,?,?,?,?,?)"
            con.executemany(ins, [("V1", 2010, "FIAT", "UNO", 1000, None, "T34-CAT;T34NAO1", "Automóveis e Utilitários Leves"), ("V1", 2010, "FIAT", "UNO", 1000, None, "T34NAO1", "Automóveis e Utilitários Leves"),   # mesmo veículo × ano: conta uma vez
                                  ("V2", 2012, "VW", "GOL", 500, None, "T34NAO1", "Automóveis e Utilitários Leves"), ("V3", 2015, "MB", "ACCELO", 50, None, "T34NAO2", "Caminhões"),
                                  ("V4", 2018, "HONDA", "CG", 99999, None, "T34MOTO", "Motos"), ("V5", 2019, "FIAT", "TORO", 10, None, "T34DES", "Automóveis e Utilitários Leves"),
                                  ("V6", 2019, "FIAT", "TORO", 10, None, "T34CAN", "Automóveis e Utilitários Leves"), ("V7", 2019, "FIAT", "TORO", 10, None, "T34MON", "Automóveis e Utilitários Leves")])
            con.commit()
        finally: con.close()
        d = C.get("/api/cobertura?tab=cofap&q=T34").json
        r = {x["cofap"]: x for x in d["rows"]}
        self.assertNotIn("T34MOTO", r)                                                                       # motos fora
        self.assertEqual((r["T34-CAT"]["situacao"], r["T34-CAT"]["nossos"]), ("catalogo", [pc]))
        self.assertEqual((r["T34DES"]["situacao"], r["T34DES"]["nossos"]), ("des", ["AMDT34D"]))
        self.assertEqual((r["T34CAN"]["situacao"], r["T34MON"]["situacao"]), ("nao", "nao"))               # cancelado e montadora não contam
        self.assertEqual((r["T34NAO1"]["frota"], r["T34NAO1"]["n_veiculos"], r["T34NAO1"]["curva"]), (1500, 2, "A"))
        self.assertEqual(r["T34NAO2"]["classes"], ["Caminhões"]); self.assertEqual(r["T34-CAT"]["curva"], "")
        for k in ("situacao", "classif", "curva"):
            for v, n in d["counts"][k].items(): self.assertEqual(C.get(f"/api/cobertura?tab=cofap&q=T34&{k}={v}").json["total"], n, (k, v))
        wb = load_workbook(io.BytesIO(C.get("/api/export/cobertura.xlsx?tab=cofap&q=T34&situacao=nao").data)); self.assertEqual(wb.sheetnames[0], "COFAP"); self.assertEqual(wb["COFAP"].max_row - 1, 4)

    def test_35_corrigir_nosso_codigo_na_cobertura(self):
        """Etapa 19 · Q7: corrigir o «Nosso código» na célula vale sobre o CrossCatalogo/servidor, aparece em Anomalias e o «Desfazer» volta ao que era."""
        if not C.get("/api/cobertura?tab=cofap&q=T34").json["rows"]: self.test_34_cobertura_cofap()      # mesmo cenário (T34…) quando este teste roda sozinho
        con = sqlite3.connect(DB)
        try: pc, outro = [r[0] for r in con.execute("SELECT perfect_code FROM products WHERE catalog_position IS NOT NULL ORDER BY id LIMIT 2")]
        finally: con.close()
        self.assertEqual(C.post("/api/cobertura/cross", json={"concorrente": "COFAP", "referencia": "T34-CAT", "de": pc, "para": "1BP0001"}).status_code, 400)     # montadora não
        self.assertEqual(C.post("/api/cobertura/cross", json={"concorrente": "COFAP", "referencia": "T34-CAT", "de": pc, "para": "AMD99999"}).status_code, 400)    # não existe
        r = C.post("/api/cobertura/cross", json={"concorrente": "COFAP", "referencia": "T34-CAT", "de": pc, "para": outro}).json
        self.assertEqual((r["codigos"], r["anterior"]), ([outro], None))
        cat = [x for x in C.get("/api/cobertura?q=T34-CAT").json["rows"] if x["referencia"] == "T34-CAT"]
        self.assertEqual([(x["codigo"], x["fonte"]) for x in cat], [(outro, "corrigido no app")])
        an = C.get("/api/anomalies?tab=corrigido").json; self.assertEqual(an["counts"]["corrigido"], 1); self.assertEqual((an["rows"][0]["antes"], an["rows"][0]["depois"]), (pc, outro))
        # COFAP: dar um código a um «Não temos» faz ele virar «Temos»
        C.post("/api/cobertura/cross", json={"concorrente": "COFAP", "referencia": "T34NAO2", "codigos": [pc]})
        r2 = {x["cofap"]: x for x in C.get("/api/cobertura?tab=cofap&q=T34").json["rows"]}
        self.assertEqual((r2["T34NAO2"]["situacao"], r2["T34NAO2"]["nossos"]), ("catalogo", [pc]))
        C.post("/api/cobertura/cross/desfazer", json={"concorrente": "COFAP", "referencia": "T34NAO2", "anterior": None})
        C.post("/api/cobertura/cross/desfazer", json={"concorrente": "COFAP", "referencia": "T34-CAT", "anterior": None})
        self.assertEqual(C.get("/api/anomalies?tab=corrigido").json["counts"]["corrigido"], 0)
        cat = [x for x in C.get("/api/cobertura?q=T34-CAT").json["rows"] if x["referencia"] == "T34-CAT"]; self.assertEqual([x["codigo"] for x in cat], [pc])
        self.assertEqual({x["cofap"]: x for x in C.get("/api/cobertura?tab=cofap&q=T34").json["rows"]}["T34NAO2"]["situacao"], "nao")

    def test_36_vincular_item_perfect_em_brands(self):
        """Etapa 22: o lápis do «Código PERFECT» em Brands grava o conjunto (vale sobre a base), marca «vinculado no app», a busca acha pelo novo código
        e o «Desfazer» volta ao que era. Código PERFECT ou inexistente não entra."""
        rows = C.get("/api/brands/MOTORCRAFT/items?all=1").json["rows"]; it = rows[0]
        con = sqlite3.connect(DB)
        try: outro = next(r[0] for r in con.execute("SELECT perfect_code FROM products WHERE catalog_position IS NOT NULL AND upper(perfect_code) LIKE 'AMD%' ORDER BY id DESC") if r[0].upper() not in it["perfect_codes"])
        finally: con.close()
        self.assertEqual(C.post("/api/brands/vinculo", json={"code": it["code"], "codigos": ["AMD99999"]}).status_code, 400)
        self.assertEqual(C.post("/api/brands/vinculo", json={"code": outro, "codigos": [outro]}).status_code, 400)
        r = C.post("/api/brands/vinculo", json={"code": it["code"], "codigos": [outro]}).json
        self.assertEqual((r["codigos"], r["anterior"]), ([outro.upper()], None))
        x = next(i for i in C.get("/api/brands/MOTORCRAFT/items?all=1&q=" + outro).json["rows"] if i["code"] == it["code"])
        self.assertEqual((x["perfect_codes"], x["vinculo_manual"], x["perfect_codes_base"]), ([outro.upper()], True, it["perfect_codes"]))
        C.post("/api/brands/vinculo/desfazer", json={"code": it["code"], "anterior": r["anterior"]})
        x = next(i for i in C.get("/api/brands/MOTORCRAFT/items?all=1").json["rows"] if i["code"] == it["code"])
        self.assertEqual((x["perfect_codes"], x["vinculo_manual"]), (it["perfect_codes"], False))

    def test_37_menu_e_dashboard_guardados_ate_o_banco_mudar(self):
        """Etapa 22: menu e Dashboard reaproveitam o cálculo enquanto o banco não muda; qualquer gravação refaz (sem esperar tempo nenhum)."""
        m0, d0 = C.get("/api/menu/counts").json["pendencias"], C.get("/api/dashboard").json["stats"]["pendencies"]
        self.assertEqual(C.get("/api/menu/counts").json["pendencias"], m0)
        con = sqlite3.connect(DB)
        try: con.execute("INSERT INTO pendencies(kind, description) VALUES('teste', 'T37')"); con.commit()
        finally: con.close()
        try: self.assertEqual((C.get("/api/menu/counts").json["pendencias"], C.get("/api/dashboard").json["stats"]["pendencies"]), (m0 + 1, d0 + 1))
        finally:
            con = sqlite3.connect(DB)
            try: con.execute("DELETE FROM pendencies WHERE description='T37'"); con.commit()
            finally: con.close()
        self.assertEqual(C.get("/api/menu/counts").json["pendencias"], m0)

    def test_38_validacao_rotas_menu_e_aba(self):
        """Etapa 24: tela Validação no menu (1 · Desenvolvimento), aba «Validar itens» do R-D, bancada pelas rotas (criar, salvar, imagem, Excel da lista) e erros com frase."""
        import io
        from openpyxl import load_workbook
        from PIL import Image
        pg = C.get("/validacao").get_data(as_text=True); self.assertIn("telas/validacao.js", pg); self.assertIn('href="/validacao"', pg)
        self.assertEqual(C.post("/api/validacao", json={"kind": "rd", "code": "NAOEXISTE"}).status_code, 400)
        self.assertEqual(C.get("/api/validacao/999999").status_code, 404)
        code = next(iter(C.get("/api/rd/rd?status=andamento").json["rows"]), {}).get("code")
        if not code: self.skipTest("seed sem item de R-D em andamento")
        vid = C.post("/api/validacao", json={"kind": "rd", "code": code}).json["id"]
        v = C.patch(f"/api/validacao/{vid}", json={"family": "CARTUCHO", "supplier_code": "DQ1"}).json; self.assertEqual((v["family"], len(v["dados"]["linhas"])), ("CARTUCHO", 10))
        b = io.BytesIO(); Image.new("RGB", (300, 200), "white").save(b, "PNG")
        r = C.post(f"/api/validacao/{vid}/desenho/perfect", data={"file": (io.BytesIO(b.getvalue()), "P.png")}, content_type="multipart/form-data"); self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual(C.get(f"/api/validacao/{vid}/img/perfect.png").status_code, 200); self.assertEqual(C.get(f"/api/validacao/{vid}/img/fornecedor.png").status_code, 404)
        self.assertEqual(C.post(f"/api/validacao/{vid}/concluir", json={"decisao": "aprovada"}).status_code, 400)        # sem o desenho do fornecedor
        a = C.get("/api/validacao/aba/rd?q=" + code).json; self.assertIn(code, [x["code"] for x in a["rows"]])
        lst = C.get("/api/validacao?status=andamento").json; self.assertIn(vid, [x["id"] for x in lst["rows"]])
        wb = load_workbook(io.BytesIO(C.get("/api/export/validacao.xlsx?status=andamento").data)); self.assertEqual(wb.sheetnames[:2], ["Validações", "Medidas"])
        self.assertEqual((v["ia"]["ligada"], C.get("/api/settings").json["validacao_ia"]), (False, False))           # padrão: sem API
        self.assertEqual(C.post(f"/api/validacao/{vid}/ler").status_code, 400)
        self.assertTrue(C.put("/api/settings", json={"validacao_ia": "1"}).json["validacao_ia"]); self.assertTrue(C.get(f"/api/validacao/{vid}").json["ia"]["ligada"])
        self.assertFalse(C.put("/api/settings", json={"validacao_ia": "0"}).json["validacao_ia"])
        self.assertEqual(C.delete(f"/api/validacao/{vid}").status_code, 200)

    def test_30_nome_do_arquivo_e_filtros_limpos(self):
        """Etapa 17 · Q8/Q16/Q26: arquivo «PerfectAmortecedores - <tela do menu> - dd-mm.xlsx», sem filtros no nome (eles ficam na aba «Filtros aplicados»);
        nenhuma tela guarda filtros da última visita; posição no catálogo fora da interface."""
        import io, re, glob, datetime
        from openpyxl import load_workbook
        dia = datetime.date.today().strftime("%d-%m")
        for rota, tela in (("/api/export/produtos.xlsx?system=gas", "Produtos e códigos"), ("/api/export/desenvolvimento.xlsx?q=AMD", "Desenvolvimento"), ("/api/export/estoque.xlsx", "Estoque")):
            r = C.get(rota); self.assertEqual(r.status_code, 200, rota)
            cd = r.headers["Content-Disposition"]; m = re.search(r"filename\*=UTF-8''([^;]+)", cd) or re.search(r"filename=\"?([^\";]+)", cd); nome = m.group(1)
            from urllib.parse import unquote
            self.assertEqual(unquote(nome), f"PerfectAmortecedores - {tela} - {dia}.xlsx", rota)
        wb = load_workbook(io.BytesIO(C.get("/api/export/produtos.xlsx?system=gas").data)); self.assertIn("FORCE GAS", str([c.value for c in wb["Filtros aplicados"]["B"]]))
        js = {p: open(p, encoding="utf-8").read() for p in glob.glob(os.path.join(ROOT, "static", "js", "**", "*.js"), recursive=True)}
        for p, s in js.items():
            for x in ("filtros da última visita", "catalog_position", "?limpo=1"): self.assertTrue(x not in s, f"{x} em {p}")
            self.assertIsNone(re.search(r"\b(confirm|prompt)\(", s), f"caixa do navegador em {p} (use PSDTW.confirmar)")                  # Q7: confirmação própria do app
            if not p.endswith("app.js"): self.assertIsNone(re.search(r"\balert\(", s), f"alert em {p} (use PSDTW.toast / PSDTW.erro)")
        self.assertNotIn("localStorage.setItem", js[os.path.join(ROOT, "static", "js", "tw.js")])


if __name__ == "__main__":
    unittest.main(verbosity=2)
