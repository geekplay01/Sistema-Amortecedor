"""27/11/2026 · trava da sincronização: o app fechado no meio da carga deixava o arquivo de trava e nenhuma sincronização nova começava por 45 min."""
import os, tempfile, unittest
import tests  # noqa: F401  (aponta PSD_DB para o banco temporário antes de importar o app)
import data_pipeline as dp


class TestTrava(unittest.TestCase):
    def setUp(self):
        self.p = os.path.join(tempfile.mkdtemp(), "sincronizacao.lock")

    def test_trava_de_processo_morto_e_descartada(self):
        morto = 2 ** 22 + 12345          # pid que não existe
        self.assertFalse(dp._pid_vivo(morto))
        with open(self.p, "w") as f: f.write(f"pid={morto} desde=2026-11-27 15:56:08\n")
        self.assertTrue(dp._take_file_lock(self.p))
        self.assertIn(f"pid={os.getpid()}", open(self.p).read())

    def test_trava_de_processo_vivo_e_respeitada(self):
        with open(self.p, "w") as f: f.write(f"pid={os.getpid()} desde=agora\n")
        self.assertFalse(dp._take_file_lock(self.p))


if __name__ == "__main__":
    unittest.main()
