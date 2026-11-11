"""Importador: normalização de código (sempre roda) e reconhecimento das planilhas reais de bases_exemplo (pula se a pasta não existir — ex.: clone do GitHub).
Confere a ESTRUTURA (colunas reconhecidas, linhas > 0), não contagens exatas: a planilha muda a cada versão do catálogo."""
import os, sys, glob, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import importer as im

B = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bases_exemplo")
def f(p):
    m = [x for x in glob.glob(os.path.join(B, p)) if not os.path.basename(x).startswith("~$")]
    if not m: raise unittest.SkipTest(f"planilha {p} não está em bases_exemplo")
    return m[0]


class Codigo(unittest.TestCase):
    def test_normalize_code(self):
        self.assertEqual(im.normalize_code("MP-AMD0243"), ("AMD0243", True))           # MP- = granel
        self.assertEqual(im.normalize_code("BJ3A/18045/DA/"), ("BJ3A18045DA", False))
        self.assertEqual(im.normalize_code("0012"), ("0012", False))                    # zeros à esquerda preservados


@unittest.skipUnless(os.path.isdir(B), "sem a pasta bases_exemplo (dados da empresa ficam fora do repositório)")
class PlanilhasReais(unittest.TestCase):
    def test_catalogo_formato_atual(self):
        p = im.preview(f("CatalogoAMD.xlsx")); m = p["mapping"]
        self.assertEqual(p["header_row"], 0); self.assertGreater(p["rows_total"], 800)
        for col, field in (("Código Produto", "perfect_code"), ("Descrição Produto", "description"), ("Números Referência", "cross_refs"),
                           ("Veículos", "vehicles"), ("Produtos Relacionados", "related_codes"), ("Cód. NCM", "ncm"), ("Cód. Barras", "ean")):
            self.assertEqual(m.get(col), field, col)

    def test_outras_bases(self):
        self.assertEqual(im.preview(f("ZS.csv"))["mapping"]["Cod.Prod.For"], "supplier_code")
        zp = im.preview(f("C*ZSxPERFECT.xlsx")); self.assertEqual(zp["mapping"]["PERFECT CODE"], "perfect_code"); self.assertGreater(zp["rows_total"], 0)
        self.assertEqual(im.preview(f("Itens*"), "MOTORCRAFT")["mapping"]["PN PERFECT (CORRESP.)"], "perfect_code")

    def test_caixas(self):
        df, _ = im.read_table(f("CaixasAMD.xlsx")); rows, _ = im.parse_boxes(df); d = {r["code"]: r for r in rows}
        self.assertGreater(len(rows), 0); self.assertEqual((d["PP013B"]["length_mm"], d["PP013B"]["width_mm"]), (425, 85))


if __name__ == "__main__": unittest.main()
