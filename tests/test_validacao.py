"""Etapa 24: módulo Validação (validacao.py) — regras do F-008 (Ap e damping), famílias pelos modelos, bancada completa com a leitura do Claude
substituída por um dublê (nada sai do PC no teste), máscara, F-008 gerado do modelo e desenho aprovado em Desenhos. Banco e pastas temporários."""
import os, sys, io, json, shutil, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unittest import mock

class Regras(unittest.TestCase):
    def test_pastas_de_arquivos_ficam_ao_lado_do_banco(self):
        """Com PSD_DB numa cópia, validações, desenhos e fotos usam as pastas ao lado da cópia — nunca as do banco real (25/11/2026)."""
        import database as db, validacao as V, drawings, auth
        real = os.path.join(db.BASE, "data")
        self.assertEqual(db.DATA_DIR, os.path.dirname(os.path.abspath(db.DB_PATH)))
        self.assertNotEqual(os.path.normcase(db.DATA_DIR), os.path.normcase(real))          # tests/__init__.py aponta o banco para o temporário
        for d in (V.DIR, drawings.DIR, auth.AVATAR_DIR): self.assertEqual(os.path.normcase(os.path.dirname(d)), os.path.normcase(db.DATA_DIR))

    def test_ap_igual_a_formula_do_modelo(self):
        import validacao as V
        L = lambda p, f, tm="", tn="": {"p": p, "f": f, "tm": tm, "tn": tn}
        casos = [(L("553", "552", "3", "-3"), "A"), (L("553", "557", "3", "-3"), "R"), (L("553", "550", "3", "-3"), "A"), (L("553", "549", "3", "-3"), "R"),
                 (L("157", "155"), "R"), (L("22", "22"), "A"), (L("12.1", "12", "0.15", "0"), "R"), (L("57,5", "57.5", "0.4", "-0.4"), "A"),
                 (L("M12X1.25-6h", "m12x1.25-6H"), "A"), (L("M12X1.25-6h", "M12X1.25-6g"), "R"), (L("GAS", "GAS"), "A"), (L("PA6", "PLASTIC"), "R"),
                 (L("PA6", "PLASTIC", "OK", "OK"), "A"), (L("75", "75", "N"), "R"), (L("", "10"), ""), (L("10", ""), ""), (L("Ø51", "51", "2.5", "-2.5"), "A")]
        for l, esperado in casos: self.assertEqual(V.ap(l), esperado, l)

    def test_damping_e_familias(self):
        import validacao as V
        P, F = ["1155", "1360", "1575", "1745", "2000"], ["1100", "1300", "1500", "1700", "2050"]
        for regra in ("faixa", "relativa"):
            self.assertEqual(V.ap_damping(P, F, regra), "A", regra)
            self.assertEqual(V.ap_damping(P, ["455", "810", "1130", "1475", "1840"], regra), "R", regra)
            self.assertEqual(V.ap_damping(["", "", "", "", ""], ["1", "2", "3", "4", "5"], regra), "", regra)
        self.assertEqual(V.ap_damping(P[:4] + [""], F, "faixa"), "R")          # Cartucho: velocidade sem PERFECT conta 0 → fora da faixa
        self.assertEqual(V.ap_damping(P[:4] + [""], F, "relativa"), "")        # os outros: divisão por zero → o modelo mostra vazio
        self.assertEqual(V.ap_damping(["100", "200", "300", "400", "500"], ["129", "249", "344", "479", "574"], "relativa"), "A")
        self.assertEqual(V.ap_damping(["100", "200", "300", "400", "500"], ["129", "249", "344", "481", "574"], "relativa"), "R")
        f = {x["v"]: x for x in V.familias()}
        self.assertEqual({k: x["damping"] for k, x in f.items()}, {"CARTUCHO": "faixa", "CONVENCIONAL": "relativa", "ESTRUTURAL": "relativa", "SEMI-ESTRUTURAL": "relativa", "SEMI-ESTRUTURAL INTERFERENCIA": "relativa"})
        self.assertEqual(sorted(f), ["CARTUCHO", "CONVENCIONAL", "ESTRUTURAL", "SEMI-ESTRUTURAL", "SEMI-ESTRUTURAL INTERFERENCIA"])
        self.assertEqual(f["ESTRUTURAL"]["n"], 21); self.assertEqual(f["ESTRUTURAL"]["medidas"][:3], ["LMAX", "LMIN", "S"]); self.assertEqual(f["CARTUCHO"]["n"], 10)

class _Arq:
    """Arquivo enviado (como o FileStorage do Flask)."""
    def __init__(self, nome, dados): self.filename, self.dados = nome, dados
    def save(self, p):
        with open(p, "wb") as fh: fh.write(self.dados)

def _png(cor=(0, 0, 0), tam=(800, 560)):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", tam, (255, 255, 255)); ImageDraw.Draw(im).rectangle([600, 450, 780, 540], fill=cor)      # «carimbo» no canto
    b = io.BytesIO(); im.save(b, "PNG"); return b.getvalue()

class Bancada(unittest.TestCase):
    def setUp(self):
        import database as db, data_pipeline as dp, validacao as V, drawings
        self.tmp = tempfile.mkdtemp(prefix="psd_val_"); self.db = db
        self.ps = [mock.patch.object(db, "DB_PATH", os.path.join(self.tmp, "app.db")), mock.patch.object(V, "DIR", os.path.join(self.tmp, "validacoes")),
                   mock.patch.object(drawings, "DIR", os.path.join(self.tmp, "drawings")), mock.patch.object(drawings, "TMP", os.path.join(self.tmp, "uploads"))]
        for p in self.ps: p.start()
        db.init_db(); c = db.conn(); c.executescript(dp.SCHEMA); c.commit(); c.close()
        with db.session() as c:
            c.execute("INSERT INTO products(perfect_code,description,family,catalog_position) VALUES('AMD0100','AMORTECEDOR DIANT. LD','ESTRUTURAL',1)")
            c.executemany("INSERT INTO rd_projects(code,suggestion,description,family,brand,status,validation_substatus,supplier,make,vehicle,year_from,year_to) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                          [("AMD0100", "REDESENVOLVIMENTO", "AMORTECEDOR DIANT. LD", "AMORTECEDOR", "PERFECT", "PEDIDO CONFIRMADO", "PENDENTE VALIDAÇÃO", "ZS", "NISSAN", "KICKS", 2017, 2024),
                           ("AMD0200", "REDESENVOLVIMENTO", "AMORTECEDOR TRAS.", "AMORTECEDOR", "PERFECT", "EM COTAÇÃO", None, "E-WIN", "VW", "T-CROSS", 2019, 2025)])
    def tearDown(self):
        for p in self.ps: p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_fluxo_completo(self):
        import validacao as V, openpyxl
        vid = V.criar("rd", "amd0100", "teste")
        self.assertEqual(V.criar("rd", "AMD0100"), vid)                         # rascunho aberto: a mesma bancada
        v = V.obter(vid); self.assertEqual((v["family"], v["supplier"], len(v["dados"]["linhas"])), ("ESTRUTURAL", "ZS", 21))
        with self.assertRaises(ValueError): V.criar("rd", "AMD9999")             # fora do R-D
        # aba do R-D: o pendente de validação vem com o rascunho
        a = V.aba("rd", {}); self.assertEqual([r["code"] for r in a["rows"]], ["AMD0100"]); self.assertEqual(a["rows"][0]["validacao"]["status"], "andamento")
        self.assertEqual([r["code"] for r in V.aba("rd", {"q": "T-CROSS"})["rows"]], ["AMD0200"])
        # desenhos e máscara
        V.desenho(vid, "perfect", _Arq("PERFECT.png", _png())); V.desenho(vid, "fornecedor", _Arq("ZS DQ41746.png", _png((40, 40, 40))))
        with self.assertRaises(ValueError): V.desenho(vid, "fornecedor", _Arq("x.dwg", b"0"))
        v = V.salvar(vid, {"mascara": [{"t": "apagar", "r": [0.74, 0.79, 0.25, 0.19]}], "supplier_code": "DQ41746"})
        self.assertTrue(v["imagens"]["perfect_limpo"])
        from PIL import Image
        with Image.open(V.imagem(vid, "perfect_limpo")) as im: self.assertEqual(im.getpixel((round(im.width * 0.85), round(im.height * 0.88))), (255, 255, 255))
        V.salvar(vid, {"mascara": []}); self.assertFalse(V.obter(vid)["imagens"]["perfect_limpo"])          # desfazer tudo = desenho como veio
        V.salvar(vid, {"mascara": [{"t": "manter", "r": [0, 0, 0.5, 0.5]}]})
        # leitura (dublê do Claude): preenche, não confere, não aprova; linha já conferida fica
        V.salvar(vid, {"linhas": [{**l, "p": "1", "f": "1", "conferida": True} if l["nome"] == "BODY DIAMETER" else l for l in V.obter(vid)["dados"]["linhas"]]})
        resp = {"medidas": [{"nome": "LMAX", "perfect": {"valor": "553", "tol_mais": "3", "tol_menos": "3", "x": 0.5, "y": 0.1}, "fornecedor": {"valor": "552", "tol_mais": "3", "tol_menos": "-3", "x": 0.52, "y": 0.06}, "observacao": ""},
                            {"nome": "S", "perfect": {"valor": "157", "tol_mais": "", "tol_menos": "", "x": 0.53, "y": 0.13}, "fornecedor": {"valor": "155", "tol_mais": "", "tol_menos": "", "x": -1, "y": -1}, "observacao": ""},
                            {"nome": "BODY DIAMETER", "perfect": {"valor": "51", "tol_mais": "2.5", "tol_menos": "-2.5", "x": 0.4, "y": 0.4}, "fornecedor": {"valor": "51", "tol_mais": "", "tol_menos": "", "x": 0.7, "y": 0.35}, "observacao": ""}],
                "damping": {"perfect": {"pf": ["1155", "1360", "1575", "1745", ""], "py": ["110", "305", "460", "795", ""]}, "fornecedor": {"pf": ["455", "810", "1130", "1475", "1840"], "py": ["175", "240", "370", "590", "870"]}}}
        with mock.patch.object(V, "ia_disponivel", return_value={"ok": True, "motivo": ""}), mock.patch.object(V, "_chamar_claude", return_value=resp) as chamada:
            v = V.ler(vid)
        self.assertEqual(len(chamada.call_args[0][0]), 2)                        # as duas imagens
        L = {l["nome"]: l for l in v["dados"]["linhas"]}
        self.assertEqual((L["LMAX"]["p"], L["LMAX"]["f"], L["LMAX"]["tm"], L["LMAX"]["tn"], L["LMAX"]["ap"], L["LMAX"]["conferida"]), ("553", "552", "3", "-3", "A", False))
        self.assertEqual((L["S"]["ap"], L["S"]["melhoria"], L["S"]["pf"]), ("R", "CHANGE TO 157", None))
        self.assertEqual((L["BODY DIAMETER"]["p"], L["BODY DIAMETER"]["conferida"]), ("1", True))                # conferida pelo usuário: a leitura não mexe
        self.assertEqual((v["damping_regra"], v["damping_ap"]["pf"], v["leitura_em"] is not None), ("relativa", "", True))      # Estrutural: 0,750 sem PERFECT → vazio, como o modelo
        with mock.patch.object(V, "ia_disponivel", return_value={"ok": False, "motivo": "sem chave"}):
            with self.assertRaises(ValueError): V.ler(vid)
        # padrão: leitura pelo Claude desligada (nada vai para a API, nem com SDK e chave); ligada só em Configurações
        import rules
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "teste"}), mock.patch.object(V, "_chamar_claude") as nunca:
            self.assertEqual(V.ia_disponivel(), {"ok": False, "ligada": False, "motivo": ""})
            with self.assertRaises(ValueError): V.ler(vid)
            nunca.assert_not_called()
            rules.set_setting("validacao_ia", "1"); self.assertTrue(V.ia_disponivel()["ligada"]); rules.set_setting("validacao_ia", "0")
        # concluir só com tudo conferido
        with self.assertRaises(ValueError): V.gerar(vid, "aprovada", pdf=False)
        ls = V.obter(vid)["dados"]["linhas"]
        for l in ls: l["conferida"] = True
        ls[3].update(p="GAS", f="GAS"); ls[4].update(p="PA6", f="PLASTIC")         # SYSTEM, DUST COVER MATERIAL
        V.salvar(vid, {"linhas": ls})
        v = V.gerar(vid, "aprovada", by="teste", pdf=False)
        self.assertEqual((v["status"], v["xlsx"]), ("aprovada", "F-008 - Validation Test - Rev.00 - AMD0100 - ZS - DQ41746 - REV.00.xlsx"))
        wb = openpyxl.load_workbook(V.arquivo_gerado(vid, "xlsx")[0]); ws, dm, da = wb.worksheets[0], wb.worksheets[1], wb["Dados"]
        self.assertEqual((ws["B10"].value, ws["F10"].value, ws["I10"].value, ws["L10"].value, ws["M10"].value), ("LMAX", 553, 552, 3, -3))
        self.assertEqual((ws["O12"].value, ws["S50"].value, ws["S52"].value, dm["R41"].value, dm["C11"].value, dm["L12"].value), ("CHANGE TO 157", "X", None, "X", 1155, 870))
        self.assertEqual((ws["F13"].value, ws["L13"].value, ws["L14"].value), ("GAS", None, "N"))    # texto igual = A; texto diferente sem tolerância leva «N» (convenção do modelo)
        self.assertTrue(str(ws["N10"].value).startswith("=IF("))                   # a fórmula do modelo continua
        self.assertEqual((da["B9"].value, da["B19"].value, da["B22"].value, da["B23"].value, da["B26"].value), ("AMD0100", "ZS", "DQ41746", "R-D", "DRAWING"))
        self.assertEqual(len(ws._images), 3); self.assertEqual(len(dm._images), 3)  # logo + PERFECT + fornecedor
        # desenho aprovado em Desenhos, como revisão vigente
        c = self.db.conn()
        try: f = c.execute("SELECT f.filename,f.source,f.origin,l.code FROM drawing_files f JOIN drawing_links l ON l.file_id=f.id").fetchone()
        finally: c.close()
        self.assertEqual(tuple(f), ("RED - AMD0100 - ZS - DQ41746 - REV.00.png", "Validação", "REDESENVOLVIMENTO", "AMD0100"))
        self.assertEqual(v["drawing_file_id"] is not None, True)
        # concluída: só leitura; nova validação abre outra
        with self.assertRaises(ValueError): V.salvar(vid, {"supplier": "X"})
        with self.assertRaises(ValueError): V.gerar(vid, "reprovada", pdf=False)
        # «Nova revisão» (no lugar de duplicar): Rev.01 com tudo da Rev.00; a lista mostra uma linha por validação (a revisão mais nova)
        nv = V.nova(vid); n = V.obter(nv); self.assertNotEqual(nv, vid); self.assertEqual(V.nova(vid), nv)          # uma revisão aberta por vez
        self.assertEqual((n["family"], n["revisao"], n["supplier_code"], n["conta"]["linhas"], n["imagens"]["fornecedor"]), ("ESTRUTURAL", 1, "DQ41746", 5, True))
        self.assertTrue(n["nome_f008"].endswith("DQ41746 - REV.01")); self.assertEqual([r["revisao"] for r in n["revisoes"]], [1, 0])
        lst = V.listagem({}); self.assertEqual((lst["counts"]["aprovada"], lst["counts"]["andamento"], lst["total"], lst["rows"][0]["n_revisoes"]), (0, 1, 1, 2))
        self.assertEqual(V.listagem({"status": "andamento"})["rows"][0]["conta"], {"linhas": 5, "conferidas": 5, "A": 3, "R": 2})      # só as linhas preenchidas contam
        V.excluir(nv); self.assertEqual((V.listagem({})["total"], V.listagem({})["counts"]["aprovada"]), (1, 1))
        self.assertIsNotNone(V.excluir(vid)["drawing_file_id"]); self.assertEqual(V.listagem({})["total"], 0)          # concluída também se exclui (o desenho fica em Desenhos)
        c = self.db.conn()
        try: self.assertEqual(c.execute("SELECT COUNT(*) FROM drawing_files").fetchone()[0], 1)
        finally: c.close()

    def test_mola_nome_imagem_leve_damping_e_pendentes_guardados(self):
        """Ajustes da etapa 24: «Item com mola» põe LMAX2 logo abaixo do LMAX (e tira), guardando o valor ao trocar de família; o nome da cota muda só nesta
        validação; a bancada usa a imagem leve (JPEG 1600 px) com chave que só muda quando a imagem muda; «1155±365» vira 1155; pendentes guardados até o banco mudar."""
        import validacao as V
        from PIL import Image
        vid = V.criar("rd", "AMD0100")
        v = V.salvar(vid, {"mola": True}); ls = v["dados"]["linhas"]
        self.assertEqual(([l["nome"] for l in ls[:3]], [l["n"] for l in ls[:3]], len(ls)), (["LMAX", "LMAX2", "LMIN"], [1, 2, 3], 22))
        ls[1]["p"] = "560"; ls[2]["nome"] = "lmin comprimido"; V.salvar(vid, {"linhas": ls})
        ls = V.obter(vid)["dados"]["linhas"]; self.assertEqual((ls[1]["mola"], ls[2]["nome"]), (True, "LMIN COMPRIMIDO"))
        v = V.salvar(vid, {"family": "CARTUCHO"}); self.assertEqual([(l["nome"], l["p"]) for l in v["dados"]["linhas"][:2]], [("LMAX", ""), ("LMAX2", "560")])
        v = V.salvar(vid, {"mola": False}); self.assertEqual((len(v["dados"]["linhas"]), "LMAX2" in [l["nome"] for l in v["dados"]["linhas"]]), (10, False))
        v = V.salvar(vid, {"damping": {"p": {"pf": ["1155±365", "1360", "", "", ""], "py": []}, "f": {}}}); self.assertEqual(v["dados"]["damping"]["p"]["pf"][:2], ["1155", "1360"])
        self.assertEqual(v["dados"]["damping"]["f"]["py"], [""] * 5)
        V.desenho(vid, "fornecedor", _Arq("F.png", _png(tam=(2400, 1700))))
        k1 = V.obter(vid)["img_ver"]["fornecedor"]; V.salvar(vid, {"supplier_code": "X"}); self.assertEqual(V.obter(vid)["img_ver"]["fornecedor"], k1)        # gravar não muda a chave
        with Image.open(V.imagem(vid, "fornecedor", tela=True)) as im: self.assertEqual((im.format, im.width), ("JPEG", 1600))
        with Image.open(V.imagem(vid, "fornecedor")) as im: self.assertEqual((im.format, im.width), ("PNG", 2400))
        p1 = V.pendentes_rd("rd"); self.assertIs(V.pendentes_rd("rd"), p1)          # mesmo banco: não recalcula
        with self.db.session() as c: c.execute("UPDATE rd_projects SET validation_substatus='PENDENTE VALIDAÇÃO' WHERE code='AMD0200'")
        self.assertEqual(sorted(V.pendentes_rd("rd")), ["AMD0100", "AMD0200"])

    def test_nome_do_arquivo_perfect_preenchido_e_par_ld_le(self):
        """Ajuste 3: fornecedor e código pelo nome do arquivo; PERFECT já preenchido (catálogo e validação anterior); validar um lado deixa o par pronto
        (medidas, posições, PERFECT vigente do par em Desenhos) com a decisão guardada; posições reaproveitadas e espelhadas."""
        import validacao as V, drawings
        self.assertEqual(V.ler_nome("RED - AMD0128 - ZS - DQ32713 - REV.06.pdf", "AMD0128"), {"supplier": "ZS", "supplier_code": "DQ32713", "rev": "06"})
        self.assertEqual(V.ler_nome("3_RED - AMD0100 - EWIN - DQF60333-02 - REV.03 (1).pdf"), {"supplier": "E-WIN", "supplier_code": "DQF60333-02", "rev": "03"})
        self.assertEqual(V.ler_nome("RED -AMD0122 - ZS - DQ43922 - REV.04.pdf")["supplier_code"], "DQ43922")
        self.assertNotIn("supplier_code", V.ler_nome("DES - 1BP31974AB - E-WIN - AMD0122 - REV.00.pdf"))       # depois do fornecedor vem o AMD: sem código
        self.assertEqual(V.ler_nome("desenho_final.pdf"), {})
        with self.db.session() as c:
            ids = {}
            for code, desc in (("AMD0138", "AMORTECEDOR DIANT. LD"), ("AMD0139", "AMORTECEDOR DIANT. LE")):
                ids[code] = c.execute("INSERT INTO products(perfect_code,description,family,catalog_position) VALUES(?,?,'ESTRUTURAL',2)", (code, desc)).lastrowid
                c.execute("INSERT INTO rd_projects(code,suggestion,description,family,brand,status,validation_substatus,supplier) VALUES(?,'REDESENVOLVIMENTO',?,'AMORTECEDOR','PERFECT','PEDIDO CONFIRMADO','PENDENTE VALIDAÇÃO','ZS')", (code, desc))
            c.execute("INSERT INTO side_pairs(right_product_id,left_product_id) VALUES(?,?)", (ids["AMD0138"], ids["AMD0139"]))
            c.execute("INSERT INTO dimensions(product_id,lmax_mm,lmin_mm,rod_diameter_mm) VALUES(?,553,396,22)", (ids["AMD0138"],))
        self.assertEqual(V.par("AMD0138"), {"code": "AMD0139", "side": "esquerdo", "meu_lado": "direito"}); self.assertIsNone(V.par("AMD0100"))      # AMD0100 sem par
        # PERFECT vigente do par em Desenhos
        tmp = os.path.join(self.tmp, "up"); os.makedirs(tmp); pth = os.path.join(tmp, "RED - AMD0139 - ZS - DQ2 - REV.00.png"); open(pth, "wb").write(_png())
        drawings.apply({"kind": "desenho", "files": [{"name": os.path.basename(pth), "path": pth, "source": None, "folder": ""}]}, {"0": {"codes": "AMD0139"}})
        vid = V.criar("rd", "AMD0138"); L = {l["nome"]: l for l in V.obter(vid)["dados"]["linhas"]}
        self.assertEqual((L["LMAX"]["p"], L["LMAX"]["fonte_p"], L["S"]["p"], L["ROD DIAMETER"]["p"]), ("553", "catálogo", "157", "22"))
        V.desenho(vid, "perfect", _Arq("P.png", _png())); v = V.desenho(vid, "fornecedor", _Arq("RED - AMD0138 - ZS - DQ41746 - REV.00.png", _png()))
        self.assertEqual((v["supplier"], v["supplier_code"], v["lido_do_nome"]["supplier_code"]), ("ZS", "DQ41746", "DQ41746"))
        self.assertEqual((v["par"]["code"], v["par"]["lado"], v["par"]["meu"]), ("AMD0139", "LE", "LD"))
        ls = v["dados"]["linhas"]
        for l in ls:
            if l["p"]: l.update(f=l["p"], conferida=True)          # linha já preenchida pelo catálogo também precisa ser conferida
        for l in ls[:3]: l.update(pp=[0.2, 0.1], pf=[0.3, 0.1])
        V.salvar(vid, {"linhas": ls})
        r = V.gerar(vid, "aprovada", pdf=False)
        self.assertEqual((r["par_preparado"]["code"], r["par_preparado"]["lado"], r["par_preparado"]["perfect"]), ("AMD0139", "LE", True))
        w = V.obter(r["par_preparado"]["id"]); W = {l["nome"]: l for l in w["dados"]["linhas"]}
        self.assertEqual((w["family"], w["supplier"], w["supplier_code"], w["dados"]["origem_par"]["code"], w["dados"]["origem_par"]["decisao"]), ("ESTRUTURAL", "ZS", None, "AMD0138", "aprovada"))
        self.assertEqual((W["LMAX"]["f"], W["LMAX"]["conferida"], W["LMAX"]["pf"]), ("553", True, [0.3, 0.1])); self.assertTrue(w["imagens"]["perfect"])
        w = V.salvar(w["id"], {"espelhar": "ambos"}); self.assertEqual(w["dados"]["linhas"][0]["pf"], [0.7, 0.1])          # desenho do outro lado espelhado
        # outra validação do lado já validado (sem ser revisão): PERFECT da validação anterior; posições reaproveitáveis do mesmo código e do mesmo fornecedor/família
        nv = V.criar("rd", "AMD0138"); self.assertNotEqual(nv, vid); n = V.obter(nv)
        self.assertEqual((n["dados"]["linhas"][0]["p"], n["dados"]["linhas"][0]["fonte_p"][:22]), ("553", "validação de AMD0138 ("))
        self.assertEqual((n["reaproveitar"]["pp"]["code"], n["reaproveitar"]["pf"]["supplier"], n["reaproveitar"]["pf"]["n"]), ("AMD0138", "ZS", 3))
        n = V.salvar(nv, {"reaproveitar": ["pp", "pf"]}); self.assertEqual((n["dados"]["linhas"][0]["pp"], n["dados"]["linhas"][0]["pf"]), ([0.2, 0.1], [0.3, 0.1]))

    def test_reprovar_nao_sobe_desenho_e_familia_troca_guardando_valores(self):
        import validacao as V
        vid = V.criar("rd", "AMD0200"); self.assertIsNone(V.obter(vid)["family"])        # sem família no catálogo: escolher
        with self.assertRaises(ValueError): V.salvar(vid, {"family": "CABINE"})
        V.salvar(vid, {"family": "CARTUCHO"}); ls = V.obter(vid)["dados"]["linhas"]; ls[0].update(p="400", f="401", tm="2", tn="2", conferida=True)
        V.salvar(vid, {"linhas": ls})
        self.assertEqual(V.obter(vid)["dados"]["linhas"][0]["tn"], "-2")                  # tolerância − sempre negativa
        v = V.salvar(vid, {"family": "CONVENCIONAL"}); self.assertEqual((len(v["dados"]["linhas"]), v["dados"]["linhas"][0]["p"]), (16, "400"))
        V.desenho(vid, "perfect", _Arq("P.png", _png())); V.desenho(vid, "fornecedor", _Arq("F.png", _png()))
        V.salvar(vid, {"supplier_code": "DQF1"})
        v = V.gerar(vid, "reprovada", pdf=False); self.assertEqual(v["status"], "reprovada")
        c = self.db.conn()
        try: self.assertEqual(c.execute("SELECT COUNT(*) FROM drawing_files").fetchone()[0], 0)
        finally: c.close()
        import openpyxl
        ws = openpyxl.load_workbook(V.arquivo_gerado(vid, "xlsx")[0]).worksheets[0]; self.assertEqual((ws["S50"].value, ws["S52"].value), (None, "X"))

if __name__ == "__main__": unittest.main()
