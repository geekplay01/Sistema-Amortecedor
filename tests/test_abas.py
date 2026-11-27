"""Update 8 · fechamento automático quando a última aba fecha (abas.py) — regras puras, sem servidor."""
import unittest
import tests  # noqa: F401  (aponta PSD_DB para o banco temporário antes de importar o app)
import abas


class TestAbas(unittest.TestCase):
    def setUp(self): abas.zerar()

    def test_sem_aviso_de_saida_nunca_fecha(self):
        abas.ping("a", True, agora=0)
        self.assertFalse(abas.deve_fechar(agora=10_000))          # PC suspenso ou tela travada: a aba do PC não vence por tempo

    def test_fecha_depois_da_folga_sem_aba_viva(self):
        abas.ping("a", True, agora=0); abas.saiu("a", agora=100)
        self.assertFalse(abas.deve_fechar(agora=100 + abas.GRACA - 1))
        self.assertTrue(abas.deve_fechar(agora=100 + abas.GRACA))

    def test_trocar_de_tela_nao_fecha(self):
        abas.ping("a", True, agora=0); abas.saiu("a", agora=100); abas.ping("b", True, agora=101)
        self.assertFalse(abas.deve_fechar(agora=500))

    def test_espera_trabalho_em_andamento(self):
        abas.ping("a", True, agora=0); abas.saiu("a", agora=100)
        self.assertFalse(abas.deve_fechar(ocupado=True, agora=200)); self.assertTrue(abas.deve_fechar(ocupado=False, agora=200))

    def test_celular_conta_enquanto_manda_sinal(self):
        abas.ping("pc", True, agora=0); abas.ping("cel", False, agora=0); abas.saiu("pc", agora=50)
        self.assertFalse(abas.deve_fechar(agora=50 + abas.GRACA))          # o celular ainda está vivo
        self.assertTrue(abas.deve_fechar(agora=abas.CELULAR + 1))           # o celular parou de mandar sinal

    def test_duas_abas_do_pc(self):
        abas.ping("a", True, agora=0); abas.ping("b", True, agora=0); abas.saiu("a", agora=10)
        self.assertFalse(abas.deve_fechar(agora=1000)); abas.saiu("b", agora=1000); self.assertTrue(abas.deve_fechar(agora=1000 + abas.GRACA))


if __name__ == "__main__":
    unittest.main()
