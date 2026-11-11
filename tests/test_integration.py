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
        r = C.post(f"/api/rd/des/item/{code}/flags", json={"flag": "pend_inmetro", "value": True}).json; self.assertTrue(r["flags"]["pend_inmetro"]["value"] and r["flags"]["pend_inmetro"]["manual"])
        self.assertEqual(r["flags"]["pend_inmetro"]["group"], "inmetro"); C.post(f"/api/rd/des/item/{code}/flags", json={"flag": "pend_inmetro", "value": None})

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
        set_status(des_a, "ITEM RECEBIDO", DES); set_status(des_b, "ITEM RECEBIDO", DES); run_sync()
        g = C.get("/api/goals?year=2026").json["goals"]
        self.assertEqual(g[RD]["tracked"], 4); self.assertEqual(g[RD]["parts"]["recebidos_validados"], 4); self.assertEqual(g[RD]["parts"]["recebidos_sem_validacao"], 2)   # só ITALOC conta
        self.assertEqual(g[DES]["tracked"], 0); self.assertEqual(g[DES]["parts"]["recebidos_sem_validacao"], 5)             # des_a(4)+des_b[0]; des_b[1] não é amortecedor; já-recebidos no marco zero (sem data) não contam
        set_status(des_a, "ITEM RECEBIDO", DES); run_sync(); g = C.get("/api/goals?year=2026").json["goals"][DES]; self.assertEqual(g["tracked"], 0)     # repetir não conta duas vezes (e sem validação não conta)
        m = {x["month"]: x["n"] for x in g["series"]["ITEM RECEBIDO"]}; self.assertEqual(sum(m.values()), 0)
        self.assertEqual(C.get("/api/goals?year=2025").json["goals"][DES]["tracked"], 0)                                 # outro ano: nada (a data da mudança está em 2026)
        ev = C.get("/api/goals/events?year=2026").json["rows"]; self.assertTrue(any(e["counts"] for e in ev)); self.assertTrue(any(not e["counts"] and "ITALOC" in (e["why_not"] or "") for e in ev))
        self.assertFalse(any(e["code"] == des_b[1] for e in ev))                                                          # fora do filtro «Amortecedor»
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
        run_sync(); C.put("/api/settings", json={"goal_basis": "validacao"})
        v = C.get("/api/metas/validacoes?year=2026").json
        self.assertEqual((v[DES], v[RD], v["total"]), (3, 2, 5)); self.assertEqual(v["por_mes"]["2026-05"], {DES: 3, RD: 2}); self.assertEqual(v["filtro"]["USER_VALID"], "ITALOC")
        self.assertEqual(C.get("/api/metas/validacoes?year=2025").json[RD], 2)
        g = C.get("/api/goals?year=2026").json; self.assertEqual(g["basis"], "validacao"); self.assertEqual((g["goals"][DES]["tracked"], g["goals"][RD]["tracked"]), (0, 2)); self.assertEqual(g["validacoes"]["total"], 5)      # DES: só ITEM RECEBIDO no ano E validado — nenhum recebido ainda
        set_status(des[:4], "ITEM RECEBIDO", DES); run_sync(); g = C.get("/api/goals?year=2026").json; n = g["goals"][DES]["tracked"]; self.assertIn(n, (2, 3))      # validados por ITALOC e recebidos neste ano (o ITALOC2 não conta; item já recebido no marco zero não tem data)
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
        oid = C.post("/api/samples", json={"perfect_code": "AMD0100", "stage": "cotacao", "quotes": []}).json["id"]
        qid = C.post("/api/prices/save", json={"order_id": oid, "price": 99.9, "link": "https://produto.mercadolivre.com.br/MLB5"}).json["id"]
        row = next(x for x in C.get("/api/samples?q=AMD0100").json["rows"] if x["id"] == oid); self.assertEqual((row["quotes"][0]["price"], row["quotes"][0]["chosen"]), (99.9, 1))
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
            aid = next(u["id"] for u in c2.get("/api/admin/users").json["users"] if u["username"] == "ana"); self.assertTrue(c2.delete(f"/api/admin/users/{aid}").json["ok"])
            self.assertEqual(c2.get("/logout").status_code, 302); self.assertEqual(c2.get("/api/dashboard").status_code, 401)
            self.assertEqual(c2.get("/favicon.ico").status_code, 200)
            self.assertNotIn("senha-forte", sqlite3.connect(DB).execute("SELECT pw_hash FROM users").fetchone()[0])                                                      # só o hash
        finally: os.environ["PSD_AUTH"] = "off"

    def test_11_paginas_carregam(self):
        for slug in ("dashboard", "metas", "pedidos-aberto", "vendas", "garantia", "desenvolvimento", "redesenvolvimento", "amostras", "configuracoes", "brands", "lados", "envio", "desenhos"):
            r = C.get("/" + slug); self.assertEqual(r.status_code, 200, slug); html = r.get_data(as_text=True)
            self.assertIn("syncchip", html); self.assertIn("PSD_STATUS", html); self.assertIn("bg-slate-800", html); self.assertIn("psd-nav", html)         # sidebar fixa slate-800 em Tailwind
        self.assertIn("Desenvolvimento", C.get("/desenvolvimento").get_data(as_text=True)); self.assertNotIn("Em desenvolvimento", C.get("/desenvolvimento").get_data(as_text=True))

    def test_12_favicon_e_menu_sem_pedidos(self):
        r = C.get("/favicon.ico"); self.assertEqual((r.status_code, r.mimetype), (200, "image/x-icon")); self.assertGreater(len(r.data), 1000)
        html = C.get("/dashboard").get_data(as_text=True); self.assertIn('href="/favicon.ico"', html); self.assertNotIn("Pedidos de compra", html)

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
        r = C.get("/api/vendas/curva-a?year=2026&month=10").json
        self.assertEqual([(x["PRODUTO"], x["QTD"], x["VALOR"]) for x in r["rows"]], [("AMD2", 1, 900), ("AMD1", 5, 510)]); self.assertEqual(r["rows"][0]["classe"], "A")
        self.assertEqual([x["PRODUTO"] for x in C.get("/api/vendas/curva-a?year=2026").json["rows"]], ["AMD2", "AMD1", "AMD3"]); self.assertIn("2026", r["years"])

    def test_18_garantia_e_fob(self):
        import io, pandas as pd
        b = io.BytesIO(); pd.DataFrame({"Código": ["AMD1", "AMD1", "AMD2"], "Qtd": [2, 1, 4], "Valor C_ST": [1, 1, 1], "Defeito": ["HASTE TRAVADA", "HASTE TRAVADA", "SEM AÇÃO"], "Cliente": list("abc"), "Fabricante": ["ZS"] * 3}).to_excel(b, index=False); b.seek(0)
        r = C.post("/api/warranty/parse", data={"file": (b, "g.xlsx")}, content_type="multipart/form-data").json; self.assertEqual(len(r["rows"]), 3); self.assertEqual(set(r["rows"][0]), {"codigo", "defeito", "quantidade"})
        w = C.get("/api/warranty").json; self.assertEqual(w["total"], 7); self.assertEqual(w["top_defeitos"][0]["defeito"], "SEM AÇÃO"); self.assertEqual(w["top_codigos"][0]["codigo"], "AMD2")
        self.assertEqual(C.post("/api/warranty/parse", data={}, content_type="multipart/form-data").status_code, 400)
        code = sqlite3.connect(DB).execute("SELECT perfect_code FROM products ORDER BY id LIMIT 1").fetchone()[0]
        b = io.BytesIO(); pd.DataFrame({"Linha": ["AMORTECEDOR"] * 2, "Codigo": ["S1", "S2"], "Mínimo": [7.25, 9], "Melhor Preço": ["E-WIN = DES. 2026-11-03", "ZS = DES. 2026-11-03"], "PartNumber": [code, "NAOEXISTE"], "FOB EWIN": ["$ 7,25", None], "FOB ZS": [None, "$ 9"], "FOB XGM": [None, None]}).to_excel(b, index=False); b.seek(0)
        r = C.post("/api/fob/import", data={"file": (b, "fob.xlsx")}, content_type="multipart/form-data").json; self.assertEqual((r["com_fob"], r["fob_sem_produto"]), (1, 1))
        self.assertEqual(sqlite3.connect(DB).execute("SELECT fob, fob_supplier FROM products WHERE perfect_code=?", (code,)).fetchone(), (7.25, "E-WIN"))
        for slug in ("pedidos-aberto", "vendas", "garantia", "metas"): self.assertEqual(C.get("/" + slug).status_code, 200, slug)


if __name__ == "__main__":
    unittest.main(verbosity=2)
