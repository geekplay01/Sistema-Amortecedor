"""Etapa 24: módulo Validação (validacao.py) — regras do F-008 (Ap e damping), famílias pelos modelos, bancada completa com a leitura do Claude
substituída por um dublê (nada sai do PC no teste), máscara, F-008 gerado do modelo e desenho aprovado em Desenhos. Banco e pastas temporários."""
import os, sys, io, json, shutil, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unittest import mock

class Regras(unittest.TestCase):
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
        nv = V.nova(vid); self.assertNotEqual(nv, vid); self.assertEqual(V.obter(nv)["family"], "ESTRUTURAL")
        lst = V.listagem({}); self.assertEqual((lst["counts"]["aprovada"], lst["counts"]["andamento"], lst["total"]), (1, 1, 2))
        self.assertEqual(V.listagem({"status": "aprovada"})["rows"][0]["conta"], {"linhas": 5, "conferidas": 5, "A": 3, "R": 2})      # só as linhas preenchidas contam
        V.excluir(nv); self.assertEqual(V.listagem({})["total"], 1)
        with self.assertRaises(ValueError): V.excluir(vid)

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
