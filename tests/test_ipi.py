"""Update 9 · Monitoramento de IPI: a aprovação só vale quando o CORPO do e-mail diz que aprovou; sugestão de IPI pela aplicação."""
import unittest
import tests  # noqa: F401  (aponta PSD_DB para o banco temporário antes de importar o app)
import ipi


class TestDetecta(unittest.TestCase):
    def test_aprovacao_no_corpo(self):
        d = ipi.detecta("Boa tarde Italo,\n\nAprovei na sexta, esqueci de retornar o email.\nA análise está de acordo com a nossa.")
        self.assertTrue(d["aprovou"]); self.assertIn("Aprovei na sexta", d["trecho"])

    def test_negacao_nao_aprova(self):
        for t in ("Ainda não aprovei, vejo amanhã.", "Não aprovado, falta conferir.", "Reprovado o lote."):
            self.assertFalse(ipi.detecta(t)["aprovou"], t)

    def test_texto_citado_nao_conta(self):
        t = "Recebido, vou olhar.\n\nEm ter., 10 de nov. de 2026 às 08:47, Italo escreveu:\n> Aprovei na sexta"
        self.assertFalse(ipi.detecta(t)["aprovou"])
        self.assertFalse(ipi.detecta("Recebido.\n> aprovado")["aprovou"])

    def test_ressalva_so_de_codigos_do_envio(self):
        d = ipi.detecta("Aprovei, exceto o AMD1403 e o AMD9999.", ["AMD1403", "AMD0001"])
        self.assertEqual(d["ressalvas"], ["AMD1403"])


class TestSugestao(unittest.TestCase):
    ctx = {"hist": {("FIAT", "UNO"): {"AMD1": {10.4: 3}, "AMD2": {2.6: 1}}, ("FORD", "KA"): {"AMD3": {10.4: 2}}}, "fraga": {("VW", "DELIVERY"): "Caminhões"}, "bi03": {}}

    def test_ordem_das_regras(self):
        s = lambda **r: ipi.sugere({"code": "X", **r}, self.ctx)
        self.assertEqual(s(family="AMORTECEDOR LINHA PESADA")[0], 2.6)
        self.assertEqual(s(family="AMORTECEDOR", catalog_line="LINHA LEVE")[0], 10.4)
        self.assertEqual(s(family="AMORTECEDOR", catalog_line="LINHA PICK-UP E UTILITÁRIOS")[0], 2.6)
        self.assertEqual(s(family="AMORTECEDOR", make="VW", vehicle="DELIVERY")[0], 2.6)
        self.assertEqual(s(family="AMORTECEDOR", make="FIAT", vehicle="STRADA", application_text="CABINE DUPLA")[0], 2.6)
        self.assertEqual(s(family="AMORTECEDOR", make="AUDI", vehicle="A4", application_text="(EXCETO CABINE ESPECIAL)")[1], "padrão, conferir")
        self.assertEqual(s(family="AMORTECEDOR", make="FORD", vehicle="KA"), (10.4, "histórico do veículo (2 itens)"))
        self.assertIn("misto", s(family="AMORTECEDOR", make="FIAT", vehicle="UNO")[1])

    def test_historico_sem_o_proprio_codigo(self):
        r = ipi.sugere({"code": "AMD3", "family": "AMORTECEDOR", "make": "FORD", "vehicle": "KA"}, self.ctx)
        self.assertEqual(r, (10.4, "padrão, conferir"))          # o único histórico do KA é o próprio AMD3


if __name__ == "__main__":
    unittest.main()
