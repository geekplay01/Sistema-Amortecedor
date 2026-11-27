"""Update 8 · Inmetro: descrição padronizada dos certificados (formatos ZS, E-WIN e do servidor) e o fornecedor pelo nome da planilha."""
import unittest
import tests  # noqa: F401  (aponta PSD_DB para o banco temporário antes de importar o app)
import inmetro


class TestInmetro(unittest.TestCase):
    def test_formatos_viram_a_mesma_descricao(self):
        zs = "Mat.: AÇO; Cat. Veículo: M1, M2, M3; Trat. Térmico: Têmpera e cromação; Ø da haste: 20mm; 'Cor/potência/tensão: N/A"
        ew = "- Material: AÇO\n- Categoria do veículo: M1, M2, M3\n- Tratamento térmico: TÊMPERA e CROMAÇÃO\n- Dimensões - Diâmetro da haste: 20 mm\n- Cor, potência e tensão - N/A"
        srv = "MAT.: AÇO; CAT.: M1, M2, M3; TRAT. TÉRMICO: TÊMPERA E CROMAÇÃO; Ø DA HASTE: 20MM; COR/W/V: N/A;"
        alvo = "Aço, M1, M2, M3, Têmpera e cromação, Ø 20 mm"
        for t in (zs, ew, srv): self.assertEqual(inmetro.texto_pad(inmetro.padroniza(t)), alvo, t)

    def test_haste_decimal_e_sem_acento(self):
        p = inmetro.padroniza(" Material ACO\n Categoria do veiculo M\n Tratamento termico Tempera e cromacao\n Diametro da haste 12,4 mm")
        self.assertEqual((p["material"], p["categoria"], p["tratamento"], p["haste"]), ("Aço", "M", "Têmpera e cromação", 12.4))
        self.assertEqual(inmetro.texto_pad(p), "Aço, M, Têmpera e cromação, Ø 12,4 mm")

    def test_vazio_e_fornecedor(self):
        self.assertIsNone(inmetro.padroniza("N/A")); self.assertIsNone(inmetro.padroniza(None))
        self.assertEqual([inmetro.fornecedor(n) for n in ("InmetroZS - Todos - Certificado.xlsx", "InmetroE-win - Todos - Certificado.xlsx")], ["ZS", "E-WIN"])


if __name__ == "__main__":
    unittest.main()
