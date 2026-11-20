"""Metas/validações, pedidos em aberto, curva A, garantia e FOB (funções Pandas puras + rotas)."""
import os, sys, io, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import metas, orders, curva_abc as curva, fob_merge

class Metas(unittest.TestCase):
    def test_sujeira_oculta_nao_zera(self):
        df = pd.DataFrame({"CODIGO": ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9"],
            "USER_VALID": ["ITALOC", " italoc ", "ITALOC ", "Italoc", "ITALOC2", "XITALOC", "ITALOC", "ITALOC", None],
            "SUGESTAO": ["DES", "des ", "R-D", " r-d", "DES", "DES", "Redesenvolvimento", "DES", "DES"],
            "LINHA": ["AMORTECEDOR", "Amortecedor", " amortecedor ", "AMORTECEDOR LINHA PESADA", "AMORTECEDOR", "AMORTECEDOR", "BANDEJA", "AMORTECEDOR", "AMORTECEDOR"]})
        r = metas.validation_counts(df)
        self.assertEqual((r["DES"], r["R-D"], r["total"]), (3, 2, 5))      # A1,A2,A8 = DES · A3,A4 = R-D; ITALOC2/XITALOC/BANDEJA/None fora
    def test_ano_e_mes(self):
        df = pd.DataFrame({"CODIGO": ["A", "B", "C"], "USER_VALID": ["ITALOC"] * 3, "SUGESTAO": ["DES", "R-D", "DES"], "LINHA": ["AMORTECEDOR"] * 3, "DATA_APROVACAO": ["2026-03-10", "2026-03-20", "2025-12-01"]})
        r = metas.validation_counts(df, year=2026)
        self.assertEqual((r["DES"], r["R-D"]), (1, 1)); self.assertEqual(r["por_mes"], {"2026-03": {"DES": 1, "R-D": 1}})
    def test_nomes_de_coluna_tolerantes_e_vazio(self):
        r = metas.validation_counts(pd.DataFrame({"user valid": ["italoc"], "Sugestão": ["des"], "linha": ["amortecedor"]})); self.assertEqual(r["DES"], 1)
        r = metas.validation_counts(pd.DataFrame(columns=["USER_VALID", "SUGESTAO", "LINHA"])); self.assertEqual((r["total"], r["DES"], r["R-D"]), (0, 0, 0))

class Pedidos(unittest.TestCase):
    def test_regras(self):
        df = pd.DataFrame({"codigo": ["MP-001", "mp-002", "AMD1", "MP-003", "MP-004", "MP-005"], "descricao": ["AMORTECEDOR DIANT", "Amortecedor tras", "AMORTECEDOR", "BANDEJA", "AMORTECEDOR", "AMORTECEDOR"],
            "cod_fornecedor": ["EX0002116", "EX0002110", "EX0002116", "EX0002116", "EX008042", "EX999"], "numero_pedido": ["P1", "P2", "P3", "P4", "P5", "P6"],
            "DATA_EMISSAO_PC": ["2026-01-05", "2026-02-01", "2026-01-01", "2026-01-01", "2026-03-01", "2026-04-01"], "quantidade": [100, 50, 9, 9, 7, 3], "DATA_PREV_ENT": ["2026-06-01"] * 6, "outra": [1] * 6})
        r = orders.pedidos_em_aberto(df)
        self.assertEqual(list(r.columns), ["codigo", "numero_pedido", "DATA_EMISSAO_PC", "quantidade", "DATA_PREV_ENT", "fornecedor", "STATUS_PC", "em_aberto"])
        self.assertEqual(r["codigo"].tolist(), ["MP-001", "MP-002", "MP-004", "MP-005"]); self.assertEqual(r["fornecedor"].tolist(), ["ZS", "E-WIN", "XGM", "VERIFICAR"])
    def test_saldo_zero_sai(self):
        df = pd.DataFrame({"codigo": ["MP-1", "MP-2"], "descricao": ["AMORTECEDOR"] * 2, "cod_fornecedor": ["EX0002116"] * 2, "numero_pedido": ["1", "2"], "DATA_EMISSAO_PC": ["2026-01-01"] * 2, "quantidade": [10, 10], "saldo": [0, 4], "DATA_PREV_ENT": [None, None]})
        r = orders.pedidos_em_aberto(df); self.assertEqual(r["numero_pedido"].tolist(), ["2"]); self.assertEqual(r["quantidade"].tolist(), [4])
    def test_traducao(self):
        self.assertEqual([orders.translate_supplier(x) for x in ("EX0002116", "ex0002110 ", "EX008042", "EX0008042", "EX0002116 - ZS ZHEJIANG", None, "")], ["ZS", "E-WIN", "XGM", "XGM", "ZS", "VERIFICAR", "VERIFICAR"])

class CurvaA(unittest.TestCase):
    def test_agrupa_soma_e_ordena(self):
        df = pd.DataFrame({"PRODUTO": ["AMD1", " amd1", "AMD2", "AMD3", "TX1"], "QTD": [1, 2, 5, 1, 9], "VALOR": [100, 50, 1000, 10, 9999], "LINHA": ["AMORTECEDOR", "AMORTECEDOR", "AMORTECEDOR LINHA PESADA", "AMORTECEDOR", "TERMINAL"]})
        r = curva.curva_a(df); self.assertEqual(r["PRODUTO"].tolist(), ["AMD2", "AMD1", "AMD3"]); self.assertEqual(r.loc[1, "QTD"], 3); self.assertEqual(r.loc[1, "VALOR"], 150)
        self.assertTrue(r["VALOR"].is_monotonic_decreasing); self.assertEqual(r["classe"].tolist()[0], "A"); self.assertAlmostEqual(r["acum_pct"].iloc[-1], 100, places=1)

class Fob(unittest.TestCase):
    def test_money(self): self.assertEqual([fob_merge.money(x) for x in ("$ 7,25", "$ 1.234,50", "$ -", None, 6, "$ 6")], [7.25, 1234.5, None, None, 6.0, 6.0])
    def test_left_join(self):
        f = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False); f.close()
        pd.DataFrame({"\xa0 Linha\xa0": ["A"] * 4, "\xa0 Codigo\xa0": ["S1", "S2", "S3", "S4"], "\xa0 Mínimo\xa0": [7.25, 5.0, 9.0, 3.0], "\xa0 Melhor Preço\xa0": ["E-WIN = DES. 2026-11-03", "ZS = NEG. 2026-11-03", "ZS = DES. 2026-11-03", "ZS = DES. 2026-11-03"],
                      "\xa0 PartNumber": ["AMD1", "AMD1", "AMD2", None], "FOB EWIN": ["$ 7,25", None, None, None], "FOB ZS": [None, "$ 5", "$ 9", "$ 3"], "FOB XGM": [None] * 4}).to_excel(f.name, index=False)
        fob, rep = fob_merge.read_fob(f.name); os.remove(f.name)
        self.assertEqual((rep["sem_partnumber"], rep["partnumber_repetido"], rep["itens_fob"]), (1, 1, 2)); self.assertEqual(fob.set_index("codigo").loc["AMD1", "fob"], 5.0)      # repetido → menor FOB
        prod = pd.DataFrame({"codigo": ["amd1", "AMD2", "AMD9"], "descricao": ["a", "b", "c"]}); out, r2 = fob_merge.merge_fob(prod, fob)
        self.assertEqual(len(out), 3); self.assertEqual(out["fob"].tolist()[:2], [5.0, 9.0]); self.assertTrue(pd.isna(out["fob"].iloc[2])); self.assertEqual((r2["com_fob"], r2["sem_fob"]), (2, 1))
        self.assertEqual(out.loc[0, "fob_fornecedor"], "ZS"); self.assertEqual(out.loc[0, "fob_origem"], "NEG"); self.assertEqual(out.loc[0, "fob_data"], "2026-11-03")

if __name__ == "__main__": unittest.main()


class _TmpDB(unittest.TestCase):
    """Banco temporário: nenhum teste toca no banco real do projeto."""
    def setUp(self):
        import database as db, data_pipeline as dp
        from unittest import mock
        self.f = tempfile.NamedTemporaryFile(suffix=".db", delete=False); self.f.close()
        self.p = mock.patch.object(db, "DB_PATH", self.f.name); self.p.start(); self.db = db
        c = db.conn(); c.executescript(dp.SCHEMA); c.commit(); c.close()
    def tearDown(self): self.p.stop(); os.remove(self.f.name)
    def sql(self, q, rows=()):
        c = self.db.conn(); (c.executemany(q, rows) if rows else c.execute(q)); c.commit(); c.close()

class GarantiaServidor(_TmpDB):
    def test_view_vira_tabela_da_tela_sem_cnpj(self):
        """Etapa 18 · Q1/Q2: colunas da view ANALITICO_GARANTIA_DEVOLUCAO → ds_garantia (sem CNPJ, sem extra) → garantias.build() → tela."""
        import data_pipeline as dp, garantias, datetime
        y = datetime.date.today().year
        raw = pd.DataFrame({"UNIDADE": ["PRIVATE-MOGI"], "CNPJ": [123], "NOME_CLI": ["CLIENTE A  "], "UF": ["sp"], "COD_AUTORIZA": [1706], "DATA_CADASTRO": [f"{y}-02-03"], "TIPO_OCO": ["GARANTIA"],
                            "STATUS_AUTO": ["GARANTIA FINALIZADA"], "STATUS_AUTO_ITEM": ["GARANTIA FINALIZADA"], "NF_ORI": ["000280108"], "SERIE_ORI": ["1"], "FAMILIA": ["AMORTECEDOR   "], "COD_PROD": ["amd1   "],
                            "QTD": [2.0], "VALOR": [100.0], "DEFEITO": ["AM-006 AMORTECEDOR SEM AÇÃO"], "LOTE": ["X"], "LOTE_GRV": ["L1"], "DATA_FABRICACAO_GRV": ["2025-01-01"], "FORNECEDOR_SHORT_GRV": ["ZS"],
                            "PROC_IMPROC": ["PROCEDENTE"], "DEPARTAMENTO": ["CLIENTE\r\n"], "ERRO_LOTE": [None], "VALIDO_VENCIDO": ["VALIDO"], "GRUPO_CLIENTE": ["G1"]})
        df, warn, mp = dp.normalize_dataset("garantia", raw)
        self.assertNotIn("CNPJ", mp.values()); self.assertTrue(df["extra"].isna().all())                       # CNPJ não é guardado
        cols = [c for c in df.columns if c != "extra"]
        c = self.db.conn(); have = {r[1] for r in c.execute("PRAGMA table_info(ds_garantia)")}
        for k in cols:
            if k not in have: c.execute(f"ALTER TABLE ds_garantia ADD COLUMN {k}")
        c.executemany(f"INSERT INTO ds_garantia({','.join(cols)}) VALUES({','.join('?' * len(cols))})", list(df[cols].itertuples(index=False, name=None))); c.commit(); c.close()
        self.assertEqual(garantias.build(), 1)
        r = garantias.rows_all({})[0]
        self.assertEqual((r["codigo"], r["autorizacao"], r["nf"], r["lote"], r["uf"], r["lote_validade"], r["responsavel"], r["fornecedor"], r["procedencia"], r["cliente"]),
                         ("AMD1", "1706", "280108-1", "L1", "SP", "VALIDO", "CLIENTE", "ZS", "PROCEDENTE", "CLIENTE A"))
        self.assertEqual((r["defeito"], r["defeito_cod"]), ("AMORTECEDOR SEM AÇÃO", "AM-006"))

class LeadTime(_TmpDB):
    def test_prazos_embarque_e_adiamento(self):
        import leadtime, datetime
        ins = "INSERT INTO ds_compras(pedido,code,description,qty_ordered,qty_pending,order_date,due_date,received_date,status,ex_code) VALUES(?,?,?,?,?,?,?,?,?,?)"
        self.sql(ins, [("P1", "MP-1", "AMORTECEDOR", 100, 100, "2026-01-01", "2026-07-30", None, "ABERTO", "EX0002116"),      # prometido 210 dias (> meta 180), previsão já vencida
                       ("P2", "MP-2", "AMORTECEDOR", 50, 0, "2026-01-01", "2026-05-01", "2026-05-11", "ENCERRADO", "EX0002110"),   # entregue com 10 dias de atraso, prazo real 130
                       ("P3", "MP-3", "PASTILHA", 50, 50, "2026-01-01", "2026-05-01", None, "ABERTO", "EX0002110"),             # fora do universo
                       ("P4", "MP-4", "AMORTECEDOR", 50, 50, "2025-11-20", "2026-03-01", None, "ABERTO", "EX0002116")])             # emitido em 2025: fora do ano vigente
        self.sql("INSERT INTO ds_embarques(pedido,code,ship_date,eta_date) VALUES(?,?,?,?)", [("P1", "MP-1", "2026-04-01", "2026-06-01")])
        t0 = datetime.date(2026, 8, 1); self.assertEqual(leadtime.snapshot_due(t0), 4)       # marco zero (todas as linhas de compra)
        self.sql("UPDATE ds_compras SET due_date='2026-09-30' WHERE pedido='P1'"); self.assertEqual(leadtime.snapshot_due(datetime.date(2026, 8, 5)), 1)      # fornecedor empurrou 62 dias
        r = leadtime.payload(datetime.date(2026, 10, 15)); g = r["geral"]; z = {x["fornecedor"]: x for x in r["por_fornecedor"]}
        self.assertEqual(r["meta_dias"], 180); self.assertTrue(r["tem_embarques"]); self.assertEqual(g["linhas"], 2)
        self.assertEqual(z["ZS"]["ate_embarque"]["media"], 90); self.assertEqual(z["ZS"]["transito"]["media"], 61)          # emissão→embarque 90 · embarque→chegada prevista (ETA 01/06) 61
        self.assertEqual(z["ZS"]["adiadas"], 1); self.assertEqual(z["ZS"]["adiamento_medio_dias"], 62)
        self.assertEqual(z["E-WIN"]["prazo_real"]["media"], 130); self.assertEqual(z["E-WIN"]["atraso"]["media"], 10)
        lin = r["linhas"][0]; self.assertEqual(lin["codigo"], "MP-1"); self.assertTrue(any("adiada" in a for a in lin["alertas"])); self.assertTrue(any("meta 180" in a for a in lin["alertas"]))

class AtualizacaoVerificacao(_TmpDB):
    def test_verificacao_nao_grava(self):
        """Corrigido (etapa 16 · D8): cada planilha roda num SAVEPOINT; sem BEGIN antes, o RELEASE fazia commit e a «verificação» gravava no banco."""
        import updater
        from unittest import mock
        self.db.init_db()
        f = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False); f.close()
        pd.DataFrame({"Coluna X": ["a", "b"], "Coluna Y": [1, 2]}).to_excel(f.name, index=False)       # planilha nova: dados avulsos
        def conta():
            c = self.db.conn()
            try: return c.execute("SELECT (SELECT COUNT(*) FROM generic_rows)+(SELECT COUNT(*) FROM import_batches)").fetchone()[0]
            finally: c.close()
        try:
            updater.run([("planilha qualquer.xlsx", f.name)], confirm=False); self.assertEqual(conta(), 0)
            with mock.patch("queries.backup_create", return_value="x.db"): updater.run([("planilha qualquer.xlsx", f.name)], confirm=True)
            self.assertGreater(conta(), 0)
        finally: os.remove(f.name)

class Bi03Protheus(_TmpDB):
    def test_bi03_prevalece_anomalias_e_pendente_protheus(self):
        """Etapa 17 · Q15/Q25/Q30: planilha «003(dd-mm)» (cadastro do Protheus) entra pela Atualização de dados; só PA de amortecedor; peso e EAN do BI03
        prevalecem sobre o CatalogoAMD (e continuam depois de reimportar o catálogo); diferenças em Anomalias; DES/R-D em andamento fora do BI03 = pendente de cadastro."""
        import bi03, updater, anomalias, loaders, importer
        from unittest import mock
        self.db.init_db(); bi03._CACHE.clear()
        self.sql("INSERT INTO products(perfect_code,description,ean,weight_kg,cat_ean,cat_weight_kg,catalog_position) VALUES(?,?,?,?,?,?,?)",
                 [("AMD1", "AMORTECEDOR", "111", 1.5, "111", 1.5, 1), ("AMD3", "AMORTECEDOR", "333", None, "333", None, 2)])
        self.sql("INSERT INTO pendencies(product_id,kind,field,description) SELECT id,'campo_ausente','peso','Campo ausente: peso' FROM products WHERE perfect_code='AMD3'")
        self.sql("INSERT INTO rd_projects(code,suggestion,status,supplier,description,line,make,vehicle) VALUES(?,?,?,?,?,?,?,?)",
                 [("X1", "DESENVOLVIMENTO", "EM COTAÇÃO", "ZS", "AMORTECEDOR", "AMORTECEDOR", "FIAT", "UNO"), ("X1", "DESENVOLVIMENTO", "PEDIDO CONFIRMADO", None, "AMORTECEDOR", "AMORTECEDOR", "FIAT", "PALIO"),
                  ("X2", "REDESENVOLVIMENTO", "EM COTAÇÃO", "E-WIN", "AMORTECEDOR", "AMORTECEDOR", "VW", "GOL"), ("X3", "DESENVOLVIMENTO", "ITEM RECEBIDO", "ZS", "AMORTECEDOR", "AMORTECEDOR", "VW", "UP"),
                  ("X4", "DESENVOLVIMENTO", "EM COTAÇÃO", "ZS", "BANDEJA", "BANDEJA", "VW", "UP")])
        f = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False); f.close()
        pd.DataFrame({"Filial\t": ["0101"] * 6, "Codigo\t": ["AMD1", "MP-AMD1", "AMD3", "X2", "BAN1", "X1"], "Tipo\t": ["PA", "MP", "PA", "PA", "PA", "MP"],
                      "Desc. Linha": ["AMORTECEDOR", "AMORTECEDOR", "AMORTECEDOR", "AMORTECEDOR LINHA PESADA", "BANDEJA", "AMORTECEDOR"], "Aliq. IPI\t": ["10.4", "2.6", "10.4", "2.6", "3.25", "10.4"],
                      "Peso Liquido\t": ["2", "2.45", "1.85", "0", "6", "1"], "Cod Barras\t": ["999", None, "333", None, "777", None], "Seg. Cod Barras": ["x"] * 6}).to_excel(f.name, index=False)
        self.assertTrue(bi03.is_file("003(18-11).xls")); self.assertTrue(bi03.is_file("003 (5-1) (1).xlsx")); self.assertFalse(bi03.is_file("CatalogoAMD.xlsx"))
        try:
            r = updater.run([("003(18-11).xlsx", f.name)], confirm=False)                     # verificação: lê, mas não grava
            self.assertEqual(r["results"][0]["label"], bi03.LABEL, r["results"]); self.assertEqual(r["results"][0]["rows"], 3)          # AMD1, AMD3, X2 (MP- e BANDEJA fora)
            c = self.db.conn(); self.assertEqual(c.execute("SELECT weight_kg FROM products WHERE perfect_code='AMD1'").fetchone()[0], 1.5); c.close()
            self.assertFalse(bi03.available())
            with mock.patch("queries.backup_create", return_value="x.db"): updater.run([("003(18-11).xlsx", f.name)], confirm=True)
        finally: os.remove(f.name)
        c = self.db.conn(); P = {r[0]: (r[1], r[2]) for r in c.execute("SELECT perfect_code, weight_kg, ean FROM products")}
        pend = c.execute("SELECT status FROM pendencies WHERE field='peso'").fetchone()[0]; c.close()
        self.assertEqual(P["AMD1"], (2.0, "999")); self.assertEqual(P["AMD3"], (1.85, "333")); self.assertEqual(pend, "resolvida")
        pe = anomalias.pesoean(); self.assertEqual(sorted((x["perfect_code"], x["campo"], x["catalogo"], x["bi03"]) for x in pe), [("AMD1", "Código de barras", "111", "999"), ("AMD1", "Peso líquido (kg)", 1.5, 2.0)])
        pr = anomalias.protheus(); self.assertEqual([(x["code"], x["status"], x["supplier"]) for x in pr], [("X1", "PEDIDO CONFIRMADO", "ZS")])      # X2 está no BI03; X3 recebido; X4 não é amortecedor
        self.assertEqual(anomalias.protheus_counts()["tipo"], {"DESENVOLVIMENTO": 1}); self.assertEqual(anomalias.protheus("", {"tipo": "REDESENVOLVIMENTO"}), [])
        self.assertEqual(bi03.ipi("X2"), 2.6)
        # reimportar o CatalogoAMD não desfaz o BI03 (e atualiza o valor da planilha em cat_*)
        g = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False); g.close()
        pd.DataFrame({"Código Produto": ["AMD1", "AMD3"], "Descrição Produto": ["AMORTECEDOR"] * 2, "Cód. Barras": ["111", "333"], "Peso (Kg)": ["1,5", "1,85"]}).to_excel(g.name, index=False)
        df, _ = importer.read_table(g.name, None); loaders.run(g.name, None, importer.suggest_mapping(df.columns), None, "CatalogoAMD.xlsx", True); os.remove(g.name)
        c = self.db.conn(); P = {r[0]: (r[1], r[2], r[3]) for r in c.execute("SELECT perfect_code, weight_kg, ean, cat_weight_kg FROM products")}; c.close()
        self.assertEqual(P["AMD1"], (2.0, "999", 1.5)); self.assertEqual(len(anomalias.pesoean()), 2); self.assertEqual(anomalias.pesoean("AMD3"), [])

class ConcorrentesServidor(_TmpDB):
    def test_ligacao_por_id_regra_cross_busca_e_anomalias(self):
        """Etapa 17 · Q10/Q11/Q18/Q19/Q20: DESENVOLVIMENTO_CONCORRENTES liga ao código pelo ID (universo amortecedor, não bloqueado); nomes unificados; OEM separado;
        catálogo com o item no CrossCatalogo usa o CrossCatalogo, senão o servidor; busca nas duas fontes; anomalias Cross × servidor e repetidos."""
        import concorrentes as cc, queries, rd, purchases, json
        self.db.init_db()
        ext = lambda i: json.dumps({"ID": str(i)})
        self.sql("INSERT INTO rd_projects(code,suggestion,status,description,line,extra) VALUES(?,?,?,?,?,?)",
                 [("AMD1", "REDESENVOLVIMENTO", "ITEM RECEBIDO", "AMORTECEDOR", "AMORTECEDOR", ext(1)), ("AMD2", "DESENVOLVIMENTO", "ITEM RECEBIDO", "AMORTECEDOR", "AMORTECEDOR", ext(2)),
                  ("X9", "DESENVOLVIMENTO", "EM COTAÇÃO", "AMORTECEDOR", "AMORTECEDOR", ext(9)), ("X9", "DESENVOLVIMENTO", "EM COTAÇÃO", "AMORTECEDOR", "AMORTECEDOR", ext(10)),
                  ("BAN1", "DESENVOLVIMENTO", "EM COTAÇÃO", "BANDEJA", "BANDEJA", ext(20)), ("BLQ1", "DESENVOLVIMENTO", "EM COTAÇÃO", "AMORTECEDOR", "AMORTECEDOR", ext(30))])
        self.sql("INSERT INTO ds_situacao(code,active,blocked) VALUES('BLQ1','ATIVO','SIM')")
        self.sql("INSERT INTO ds_concorrentes(dev_id,competitor,reference) VALUES(?,?,?)",
                 [("1", "NAKATA", "HG33066"), ("1", "COFAP", "GP32530"), ("1", "OEM", "52025115"), ("2", "MONROE", "27016"), ("9", "N° INDISA", "IN-100"), ("9", "HIPPERFREIOS", "HF1"),
                  ("10", "N° INDISA", "IN-100"), ("9", "MONROE", "27016"), ("9", "COFAP", "GP1"), ("10", "COFAP", "GP2"), ("20", "COFAP", "BAN-1"), ("30", "COFAP", "BLQ-1")])
        self.sql("INSERT INTO products(perfect_code,description,catalog_position) VALUES(?,?,?)", [("AMD1", "AMORTECEDOR DIANT", 1), ("AMD2", "AMORTECEDOR TRAS", 2)])
        self.sql("INSERT INTO sources(name,category) VALUES('CrossCatalogo.xlsx','Referência cruzada')")
        self.sql("INSERT INTO codes(product_id,code,normalized_code,code_type,brand,source_id) SELECT p.id,?,?,?,?,(SELECT id FROM sources WHERE name='CrossCatalogo.xlsx') FROM products p WHERE p.perfect_code='AMD1'",
                 [("HG33064", "HG33064", "concorrente", "NAKATA"), ("GP32530", "GP32530", "concorrente", "COFAP")])
        self.assertEqual((cc.nome("N° INDISA"), cc.nome("Nº URBA"), cc.nome("HIPPERFREIOS"), cc.nome("NAKATA")), ("INDISA", "URBA", "HIPPER FREIOS", "NAKATA"))
        self.assertEqual(cc.build(), 10)                                                   # BANDEJA e o bloqueado no ERP ficam fora
        a1 = cc.para_item("AMD1"); self.assertEqual((a1["fonte"], sorted(x["codigo"] for x in a1["concorrentes"])), ("CrossCatalogo", ["GP32530", "HG33064"]))   # catálogo com CrossCatalogo
        a2 = cc.para_item("AMD2"); self.assertEqual((a2["fonte"], a2["concorrentes"]), ("servidor", [{"marca": "MONROE", "codigo": "27016", "aplicacoes": 1}]))    # catálogo sem CrossCatalogo
        x9 = cc.para_item("X9"); self.assertEqual(x9["fonte"], "servidor"); self.assertIn({"marca": "INDISA", "codigo": "IN-100", "aplicacoes": 2}, x9["concorrentes"])     # 2 IDs = 2 aplicações, 1 referência
        self.assertEqual(cc._server("AMD1")[-1]["is_oem"], 1); self.assertNotIn("OEM", [x["marca"] for x in cc.para_item("AMD2")["concorrentes"]])
        self.assertEqual(queries.perfect_codes("IN100"), ["X9"]); self.assertEqual(queries.perfect_codes("27.016"), ["AMD2", "X9"])
        self.assertEqual([r["code"] for r in rd.items("DESENVOLVIMENTO", {"q": "in-100"})["rows"]], ["X9"])
        self.assertEqual([r["perfect_code"] for r in queries.products({"q": "27016"})["rows"]], ["AMD2"])
        self.assertEqual(queries.products({"q": "27016"})["rows"][0]["via"], [{"code": "27016", "brand": "MONROE", "type": "concorrente"}])
        cx = cc.cross_x_servidor(); self.assertEqual([(r["perfect_code"], r["concorrente"], r["cross"], r["servidor"]) for r in cx], [("AMD1", "NAKATA", ["HG33064"], ["HG33066"])])
        rp = cc.repetidos(); self.assertIn({"grupo": "ref_em_varios", "concorrente": "MONROE", "referencias": ["27016"], "codigos": ["AMD2", "X9"]}, rp)
        self.assertIn({"grupo": "varias_refs", "concorrente": "COFAP", "referencias": ["GP1", "GP2"], "codigos": ["X9"]}, rp); self.assertEqual(len(rp), 2)        # IN-100 em 2 IDs do X9 não é repetido
        self.assertIn({"brand": "INDISA", "code": "IN-100"}, purchases.rd_cross_index()["X9"])

class FragaPlanilhas(_TmpDB):
    def test_lancamentos_e_cofap_x_frota(self):
        """Etapa 17 · Q22/Q28/Q29: «LANÇAMENTOS aaaa» guarda só as colunas usadas e a frota do ano atual; «…x_FROTA» guarda veículo × amortecedor COFAP;
        as duas entram pela Atualização de dados, a verificação não grava e cada carga substitui a anterior."""
        import fraga, updater, datetime
        from unittest import mock
        self.db.init_db(); fraga._CACHE.clear(); y = datetime.date.today().year
        self.assertEqual((fraga.kind("LANÇAMENTOS 2026.xlsx"), fraga.kind("Lancamentos 2027 (1).xlsx"), fraga.kind("COFAP_AMORTECEDORES_x_FROTA.xlsx"), fraga.kind("CatalogoAMD.xlsx")),
                         ("lancamentos", "lancamentos", "pecas", None))
        la = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False); la.close(); pc = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False); pc.close()
        pd.DataFrame({"codigo_fraga": ["A.VW.1", "A.VW.1", "A.FIA.2"], "sigla_marca": ["VW", "VW", "FIA"], "status_producao": ["Inativo", "Inativo", "Ativo"], "classificacao": ["Automóveis"] * 3,
                      "marca_veiculo": ["VOLKSWAGEN", "VOLKSWAGEN", "FIAT"], "nome_veiculo": ["GOL", "GOL", "PALIO"], "modelo_veiculo": ["1.0", "1.0", "-"], "ano_venda": [2010, 2011, 2024],
                      "inicio_producao": ["2008-01-01", "2008-01-01", "2024-03-01"], "final_producao": [None, None, None], f"Frota{y - 1}": [9, 9, 9], f"Frota{y}": [1000, 500, 70], "FrotaSP": [1, 1, 1]}).to_excel(la.name, index=False)
        pd.DataFrame({"CodigoFraga": ["A.VW.1", "A.FIA.2"], "Ano Venda": [2010, 2024], "Marca": ["VOLKSWAGEN", "FIAT"], "Nome Veículo": ["GOL", "PALIO"], "Frota2024": [800, 60],
                      "Amortecedor PERFECT": ["-", "AMD9"], "Amortecedor COFAP": ["GP1", "GP2"]}).to_excel(pc.name, index=False)
        conta = lambda t: (lambda c: (c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0], c.close())[0])(self.db.conn())
        try:
            files = [("LANÇAMENTOS 2026.xlsx", la.name), ("COFAP_AMORTECEDORES_x_FROTA.xlsx", pc.name)]
            r = updater.run(files, confirm=False); self.assertEqual([x["status"] for x in r["results"]], ["ok", "ok"], r["results"]); self.assertEqual((conta("fraga_veiculos"), conta("fraga_pecas")), (0, 0))
            with mock.patch("queries.backup_create", return_value="x.db"): updater.run(files, confirm=True); updater.run(files, confirm=True)       # 2ª carga substitui (não duplica)
        finally: os.remove(la.name); os.remove(pc.name)
        self.assertEqual((conta("fraga_veiculos"), conta("fraga_pecas")), (3, 2))
        c = self.db.conn(); v = c.execute("SELECT marca, veiculo, ano_venda, frota, frota_ano, inicio FROM fraga_veiculos ORDER BY ano_venda").fetchall(); p = c.execute("SELECT perfect, cofap, frota FROM fraga_pecas ORDER BY cofap").fetchall(); c.close()
        self.assertEqual(tuple(v[0]), ("VOLKSWAGEN", "GOL", 2010, 1000.0, y, "2008-01-01")); self.assertEqual(tuple(v[2])[3], 70.0)
        self.assertEqual([tuple(x) for x in p], [(None, "GP1", 800.0), ("AMD9", "GP2", 60.0)])

class GarantiaAnalitico(_TmpDB):
    def test_servidor_filtros_atalhos_mapa_e_planilha_ignorada(self):
        """Etapa 18: a tela vem do servidor (ds_garantia → garantias.build); a planilha «Analítico de Garantias» é ignorada com aviso.
        Padrão: só garantias, sem canceladas, ano atual; defeito agrupado sem o prefixo AM-xxx; cada atalho = linhas da lista ao clicar;
        mapa: índice = peças em garantia ÷ vendidas na UF; comparação com o mesmo período do ano anterior."""
        import garantias, updater, datetime
        self.db.init_db(); y = datetime.date.today().year
        c = self.db.conn(); have = {r[1] for r in c.execute("PRAGMA table_info(ds_garantia)")}
        import data_pipeline as dp
        for k in dp.DATASETS["garantia"]["aliases"]:
            if k not in have: c.execute(f"ALTER TABLE ds_garantia ADD COLUMN {k}")
        c.commit(); c.close()
        ins = "INSERT INTO ds_garantia(unit,auth,event_date,kind,status,client_group,customer,nf,family,code,qty,value,defect,lot,fab_date,supplier,verdict,dept,lot_error,uf,lot_valid) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        L = [("PRIVATE-MOGI", 1, f"{y}-01-03", "GARANTIA", "GARANTIA FINALIZADA", "G1", "CLIENTE A", "N1", "AMORTECEDOR", "AMD1", 2, 100.0, "AM-006 AMORTECEDOR SEM AÇÃO", "L1", "2025-01-01", "ZS", "PROCEDENTE", "INSPEÇÃO", None, "SP", "VALIDO"),
             ("PRIVATE-ARUJA", 2, f"{y}-01-04", "GARANTIA AUTOMATICA", "PAGAMENTO FINALIZADO", "G2", "CLIENTE B", "N2", "AMORTECEDOR", "AMD1", 1, 50.0, "AMORTECEDOR SEM AÇÃO", "L1", "2025-01-01", "ZS", "IMPROCEDENTE", "CLIENTE_x000D_", "SIM", "RS", "VENCIDO"),
             ("PRIVATE-MOGI", 3, f"{y}-01-05", "ACORDO COMERCIAL", "PAGAMENTO FINALIZADO", "G1", "CLIENTE A", "N3", "AMORTECEDOR", "AMD2", 5, 10.0, "BATENDO FIM DE CURSO", None, None, "E-WIN", None, None, None, "SP", None),
             ("PRIVATE-MOGI", 4, f"{y}-01-06", "GARANTIA", "OCORRÊNCIA CANCELADA", "G1", "CLIENTE A", "N4", "AMORTECEDOR", "AMD2", 7, 70.0, "VAZAMENTO", None, None, "E-WIN", None, None, None, "SP", None),
             ("PRIVATE-MOGI", 5, f"{y - 1}-01-02", "GARANTIA", "GARANTIA FINALIZADA", "G1", "CLIENTE A", "N5", "AMORTECEDOR", "AMD3", 3, 30.0, "AM-014 SEM PRESSÃO", None, None, "E-WIN", "PROCEDENTE", None, None, "SP", None),
             ("PRIVATE-MOGI", 6, f"{y - 1}-12-31", "GARANTIA", "GARANTIA FINALIZADA", "G1", "CLIENTE A", "N6", "AMORTECEDOR", "AMD3", 9, 90.0, "VAZAMENTO", None, None, "E-WIN", "PROCEDENTE", None, None, "SP", None)]
        self.sql(ins, L)
        self.sql("INSERT INTO ds_vendas_uf(sale_date,uf,qty,total) VALUES(?,?,?,?)", [(f"{y}-01-01", "SP", 400, 1), (f"{y}-01-01", "RS", 50, 1), (f"{y - 1}-01-01", "SP", 999, 1)])
        self.assertEqual(garantias.build(), 6)
        s = garantias.summary({})
        self.assertEqual((s["kpis"]["linhas"], s["kpis"]["pecas"], s["kpis"]["valor"]), (2, 3, 150.0))          # só garantias, sem canceladas, ano atual
        self.assertEqual(s["kpis"]["pct_procedente"], 66.7); self.assertEqual(s["defeitos"][0]["defeito"], "AMORTECEDOR SEM AÇÃO"); self.assertEqual(s["defeitos"][0]["pecas"], 3)
        self.assertEqual(s["defeitos"][0]["cod"], "AM-006"); self.assertEqual(s["defeitos"][0]["acum"], 100.0); self.assertEqual(s["lotes"][0]["lote"], "L1"); self.assertEqual(s["lotes"][0]["erro_lote"], 1)
        # mesmo período do ano anterior: até o dia-mês do último cadastro filtrado (04/jan) → só a ocorrência 5 (3 peças); a 6 (31/dez) fica fora
        self.assertEqual((s["anterior"]["ano"], s["anterior"]["ate"], s["anterior"]["pecas"]), (str(y - 1), "01-04", 3))
        jan = s["por_mes"][0]; self.assertEqual((len(s["por_mes"]), jan["pecas"], jan["pecas_ant"]), (12, 3, 3)); self.assertTrue(s["por_mes"][5]["futuro"])
        # mapa: índice = peças em garantia ÷ vendidas na UF (mesmo ano) e o código com mais peças
        uf = {r["uf"]: r for r in s["por_uf"]}
        self.assertEqual((uf["SP"]["pecas"], uf["SP"]["vendidas"], uf["SP"]["indice"], uf["SP"]["top"][0]["codigo"]), (2, 400, 0.5, "AMD1")); self.assertEqual(uf["RS"]["indice"], 2.0)
        for grp, base in (("ano", {}), ("tipo", {}), ("status", {}), ("fornecedor", {}), ("procedencia", {}), ("unidade", {}), ("uf", {}), ("validade", {}), ("tipo", {"ano": "todos"})):
            cc = garantias.summary(base)["counts"][grp]
            for val, n in cc.items(): self.assertEqual(garantias.summary({**base, grp: val})["total"], n, f"{grp}={val} {base}")
        self.assertEqual(garantias.summary({"tipo": "todos", "status": "todos"})["total"], 4); self.assertEqual(garantias.summary({"ano": "todos"})["total"], 4)
        self.assertEqual(garantias.summary({"q": "cliente b"})["total"], 1); self.assertEqual(garantias.summary({"defeito": "AMORTECEDOR SEM AÇÃO"})["kpis"]["pecas"], 3)
        self.assertIsNone(garantias.summary({"ano": "todos"})["anterior"])
        # a planilha antiga é reconhecida e ignorada (não grava nada)
        r = updater.run([("Analitico de Garantias (2).xlsx", "nao_existe.xlsx")], confirm=False)
        self.assertEqual(r["results"][0]["status"], "ignorado"); self.assertIn("servidor", r["results"][0]["messages"][0])
        self.assertEqual(garantias.summary({"ano": "todos", "tipo": "todos", "status": "todos"})["total"], 6)
        c = self.db.conn()
        try: self.assertNotIn("cnpj", [x[1] for x in c.execute("PRAGMA table_info(garantias)")])
        finally: c.close()

class SaldosParados(_TmpDB):
    def test_lista_por_pedido_e_codigo(self):
        """Etapa 16 · D4 (Q19): saldo sem embarque há mais de 2× o p90 da produção do fornecedor → lista por pedido × código com descrição, saldo, emissão,
        dias sem embarque, última previsão e nº de adiamentos; pedido recente não entra. O Excel traz as mesmas linhas."""
        import leadtime, datetime, exporter, io
        from openpyxl import load_workbook
        ins = "INSERT INTO ds_compras(pedido,code,description,qty_ordered,qty_pending,order_date,due_date,received_date,status,ex_code) VALUES(?,?,?,?,?,?,?,?,?,?)"
        self.sql(ins, [("P1", "MP-1", "AMORTECEDOR DIANT", 100, 100, "2024-06-01", "2024-12-01", None, "ABERTO", "EX0002116"),
                       ("P2", "MP-2", "AMORTECEDOR TRAS", 50, 50, "2026-09-01", "2027-02-01", None, "ABERTO", "EX0002116")])
        self.assertEqual(leadtime.snapshot_due(datetime.date(2026, 8, 1)), 2)
        self.sql("UPDATE ds_compras SET due_date='2025-03-01' WHERE pedido='P1'"); leadtime.snapshot_due(datetime.date(2026, 8, 2))     # 1 adiamento
        rows = leadtime.parados(datetime.date(2026, 10, 15))
        self.assertEqual([(r["pedido"], r["codigo"]) for r in rows], [("P1", "MP-1")])
        r = rows[0]
        self.assertEqual((r["descricao"], r["saldo"], r["emissao"], r["ultima_previsao"], r["adiamentos"], r["dias_sem_embarque"]), ("AMORTECEDOR DIANT", 100.0, "2024-06-01", "2025-03-01", 1, 866))
        self.assertGreater(r["dias_sem_embarque"], r["limite_dias"])
        bio, fn = exporter.build("parados", {"today": "2026-10-15"}); ws = load_workbook(io.BytesIO(bio.read())).worksheets[0]
        self.assertEqual(ws.max_row - 1, 1); self.assertEqual(ws.cell(2, 1).value, "P1"); self.assertIn("parados", fn.lower().replace(" ", "_"))

class VendasUniverso(_TmpDB):
    def test_linha_exata_seletor_e_resumo(self):
        """Etapa 16 · C1 (Q10): padrão = BI (LINHA = 'AMORTECEDOR' exata); linha pesada e kit só pelo seletor; resumo: último mês fechado · mês atual parcial · acumulado do ano."""
        import curva_abc, analytics, datetime, data_pipeline as dp
        self.db.init_db(); dp.Store(self.f.name)                                     # catálogo + colunas novas das tabelas ds_* (total_net, line…), como no app
        ins = "INSERT INTO ds_vendas(pedido,code,qty,total,sale_date,line) VALUES(?,?,?,?,?,?)"
        self.sql(ins, [("1", "AMD1", 10, 1000, "2026-10-01", "AMORTECEDOR"), ("2", "AMD2", 1, 500, "2026-10-01", "AMORTECEDOR LINHA PESADA"), ("3", "KIT1", 2, 80, "2026-10-01", "KIT DE AMORTECEDOR"),
                       ("4", "TRM", 9, 9999, "2026-10-01", "TERMINAL"), ("5", "AMD1", 3, 300, "2026-11-01", "AMORTECEDOR"), ("6", "AMD1", 4, 400, "2025-10-01", "AMORTECEDOR"), ("7", "AMD3", 1, 50, "2026-01-01", " amortecedor ")])
        self.assertEqual([r["PRODUTO"] for r in curva_abc.payload(2026, 10)["rows"]], ["AMD1"])
        self.assertEqual([r["PRODUTO"] for r in curva_abc.payload(2026, 10, linhas="amortecedor,pesada,kit")["rows"]], ["AMD1", "AMD2", "KIT1"])
        self.assertEqual(curva_abc.payload(2026, 10, linhas="pesada")["total_valor"], 500)
        o = curva_abc.overview(today=datetime.date(2026, 11, 17)); r = o["resumo"]
        self.assertEqual((r["fechado"]["mes"], r["fechado"]["valor"], r["fechado"]["qtd"]), ("2026-10", 1000, 10))
        self.assertEqual((r["parcial"]["mes"], r["parcial"]["valor"]), ("2026-11", 300))
        self.assertEqual((r["ytd"]["valor"], r["ytd"]["valor_ant"]), (1350, 400)); self.assertEqual(o["linhas_sel"], ["amortecedor"])
        self.assertEqual(curva_abc.overview(today=datetime.date(2026, 11, 17), linhas="amortecedor,pesada")["resumo"]["fechado"]["valor"], 1500)
        self.assertEqual(analytics.sales_summary(months=24, today=datetime.date(2026, 11, 17))["total_value"], 1750)          # Dashboard: mesmo universo do BI (só AMORTECEDOR)
        self.sql("INSERT INTO ds_vendas(code,qty,total,sale_date,line,description) VALUES(?,?,?,?,?,?)", [("V1", 1, 7, "2026-10-01", None, "AMORTECEDOR DIANT"), ("V2", 1, 3, "2026-10-01", "", "KIT AMORTECEDOR")])
        self.assertEqual(curva_abc.payload(2026, 10)["total_valor"], 1007); self.assertEqual(curva_abc.payload(2026, 10, linhas="kit")["total_valor"], 83)      # sem LINHA: a descrição decide

class EstoqueCobertura(_TmpDB):
    def test_faixas_e_atalhos(self):
        """Etapa 16 · C2–C4 (fonte do estoque: etapa 20 · Q5/Q6): só itens do catálogo; venda média = 12 meses fechados; estoque = PRIVATE + FECT de
        ESTOQUE_ANALISE_REPOSICAO (ds_situacao); a caminho = pedidos em aberto sem os parados; cobertura = (estoque + a caminho) ÷ média.
        Ruptura (vende, sem estoque) · Risco < 6 meses · OK 6–18 · Excesso > 18 · Sem giro (estoque sem venda). «Contar» só PA / só MP troca o estoque usado."""
        import estoque, datetime, data_pipeline as dp, exporter, io
        from unittest import mock
        from openpyxl import load_workbook
        self.db.init_db(); dp.Store(self.f.name)
        self.sql("INSERT INTO products(perfect_code,description,catalog_position) VALUES(?,?,?)", [(x, "AMORTECEDOR " + x, i) for i, x in enumerate("ABCDEF", 1)])
        mes = lambda i: f"{2025 + (10 + i) // 12}-{(10 + i) % 12 + 1:02d}-01"           # 12 meses fechados: 2025-11 … 2026-10
        v = []
        for code, qtd in (("A", 10), ("B", 1), ("C", 2), ("E", 5), ("F", 1), ("Z", 50)): v += [(code, qtd, qtd * 10.0, mes(i), "AMORTECEDOR") for i in range(12)]    # Z: fora do catálogo
        v += [("A", 999, 9.0, "2026-11-01", "AMORTECEDOR"), ("A", 500, 5.0, "2025-10-01", "AMORTECEDOR")]          # mês atual (parcial) e mês fora da janela: não entram
        self.sql("INSERT INTO ds_vendas(code,qty,total,sale_date,line) VALUES(?,?,?,?,?)", v)
        self.sql("INSERT INTO ds_situacao(code,active,blocked,stock_total,priv_pa,priv_mp,fect_pa,fect_mp) VALUES(?,'ATIVO','NAO',?,?,?,?,?)",
                 [("A", 25, 20, 5, 0, 0), ("B", 30, 30, 0, 0, 0), ("D", 10, 0, 10, 0, 0), ("F", 5, 3, 0, 2, 0), ("Z", 99, 99, 0, 0, 0)])
        prev = {"available": True, "linhas": [{"codigo": "MP-C", "quantidade": 20, "etapa": "No mar"}, {"codigo": "MP-F", "quantidade": 5, "etapa": "Aguardando embarque"}, {"codigo": "MP-B", "quantidade": 1000, "etapa": "Parado — verificar saldo"}]}
        with mock.patch("leadtime.forecast_cached", return_value=prev):
            d = estoque.listing({}, today=datetime.date(2026, 11, 17)); r = {x["codigo"]: x for x in estoque.listing({"all": 1}, today=datetime.date(2026, 11, 17))["rows"]}
            self.assertEqual({k: x["situacao"] for k, x in r.items()}, {"A": "risco", "B": "excesso", "C": "ruptura", "D": "sem_giro", "E": "ruptura", "F": "ok"})
            self.assertEqual((r["A"]["media_mensal"], r["A"]["estoque"], r["A"]["a_caminho"], r["A"]["cobertura"]), (10.0, 25.0, 0, 2.5))
            self.assertEqual(r["F"]["partes"], {"total": 5, "pa": 5, "mp": 0, "private": 3, "fect": 2}); self.assertEqual((d["kpis"]["pa"], d["kpis"]["mp"]), (55, 15))
            pa = {x["codigo"]: x for x in estoque.listing({"all": 1, "conta": "pa"}, today=datetime.date(2026, 11, 17))["rows"]}
            self.assertEqual((pa["A"]["estoque"], pa["A"]["cobertura"]), (20, 2.0)); self.assertNotIn("D", pa)                # D só tem MP e não vende: fora quando conta só PA
            mp = {x["codigo"]: x for x in estoque.listing({"all": 1, "conta": "mp"}, today=datetime.date(2026, 11, 17))["rows"]}
            self.assertEqual((mp["A"]["estoque"], mp["B"]["situacao"], mp["D"]["estoque"]), (5, "ruptura", 10))
            self.assertEqual((r["F"]["a_caminho"], r["F"]["cobertura"]), (5, 10.0)); self.assertEqual(r["B"]["a_caminho"], 0)
            self.assertEqual(d["counts"]["situacao"], {"ruptura": 2, "risco": 1, "ok": 1, "excesso": 1, "sem_giro": 1}); self.assertEqual(d["limites"], {"risco": 6.0, "excesso": 18})
            for k, n in d["counts"]["situacao"].items(): self.assertEqual(estoque.listing({"situacao": k}, today=datetime.date(2026, 11, 17))["total"], n, k)
            for k, n in estoque.listing({"situacao": "ruptura"}, today=datetime.date(2026, 11, 17))["counts"]["classe"].items():
                self.assertEqual(estoque.listing({"situacao": "ruptura", "classe": k}, today=datetime.date(2026, 11, 17))["total"], n, k)
            self.assertEqual(estoque.listing({"q": "f"}, today=datetime.date(2026, 11, 17))["total"], 1)
            bio, _ = exporter.build("estoque", {"situacao": "ruptura", "today": "2026-11-17"}); self.assertEqual(load_workbook(io.BytesIO(bio.read())).worksheets[0].max_row - 1, 2)

class EstoqueProjecao(_TmpDB):
    def test_vai_faltar_antes_de_chegar(self):
        """Etapa 16 · A1: projeção mês a mês (6 meses, a partir do atual): saldo = estoque + chegadas previstas do mês − venda média (mês atual: só os dias que faltam).
        «Falta em» = 1º mês com saldo negativo; previsão vencida conta no mês atual; parado não chega."""
        import estoque, datetime, data_pipeline as dp
        from unittest import mock
        self.db.init_db(); dp.Store(self.f.name)
        mes = lambda i: f"{2025 + (10 + i) // 12}-{(10 + i) % 12 + 1:02d}-01"
        v = []
        for code, qtd in (("A", 10), ("C", 2), ("F", 1), ("G", 3)): v += [(code, qtd, qtd * 10.0, mes(i), "AMORTECEDOR") for i in range(12)]
        self.sql("INSERT INTO ds_vendas(code,qty,total,sale_date,line) VALUES(?,?,?,?,?)", v)
        self.sql("INSERT INTO products(perfect_code,catalog_position) VALUES(?,?)", [(x, i) for i, x in enumerate("ACFG", 1)])
        self.sql("INSERT INTO ds_situacao(code,stock_total,priv_pa) VALUES(?,?,?)", [("A", 25, 25), ("F", 5, 5)])
        prev = {"available": True, "linhas": [{"codigo": "MP-C", "quantidade": 20, "etapa": "No mar", "chegada_prevista": "2027-02-10"},
                                              {"codigo": "MP-F", "quantidade": 5, "etapa": "No mar", "chegada_prevista": "2026-12-05"},
                                              {"codigo": "MP-G", "quantidade": 10, "etapa": "No porto / desembaraço", "chegada_prevista": "2026-10-01"},      # vencida: conta em nov/2026
                                              {"codigo": "MP-A", "quantidade": 999, "etapa": "Parado — verificar saldo", "chegada_prevista": "2026-12-01"}]}
        hoje = datetime.date(2026, 11, 17)
        with mock.patch("leadtime.forecast_cached", return_value=prev):
            d = estoque.listing({"all": 1}, today=hoje); r = {x["codigo"]: x for x in d["rows"]}
            self.assertEqual(d["meses"], ["2026-11", "2026-12", "2027-01", "2027-02", "2027-03", "2027-04"])
            self.assertEqual({k: x["falta_em"] for k, x in r.items()}, {"A": "2027-02", "C": "2026-11", "F": None, "G": "2027-02"})
            self.assertEqual(r["A"]["projecao"][:4], [20.3, 10.3, 0.3, -9.7]);          # novembro: só 14 dos 30 dias (hoje é 17/11) self.assertEqual(r["F"]["chegadas"], [0, 5, 0, 0, 0, 0]); self.assertEqual(r["G"]["chegadas"][0], 10)
            self.assertTrue(r["C"]["antes_de_chegar"]); self.assertFalse(r["A"]["antes_de_chegar"])      # C tem pedido, mas chega depois da falta; A não tem pedido nenhum
            self.assertEqual(d["counts"]["falta"], 3); self.assertEqual(estoque.listing({"falta": "1"}, today=hoje)["total"], 3)
            com_falta = estoque.listing({"falta": "1"}, today=hoje)["counts"]["situacao"]          # atalho de situação respeita o filtro «vai faltar»
            for k, n in com_falta.items(): self.assertEqual(estoque.listing({"falta": "1", "situacao": k}, today=hoje)["total"], n, k)

class PrevisaoLinhas(_TmpDB):
    def test_atalhos_vencidas_e_excel(self):
        """Etapa 16 · A3/A4: lista da previsão filtrada no servidor; atalhos de etapa, fornecedor e alerta (vai atrasar > 15 d, vencida) com contagem = lista; Excel com os filtros."""
        import leadtime, exporter, io
        from unittest import mock
        from openpyxl import load_workbook
        L = [{"codigo": "MP-A", "pedido": "1", "fornecedor": "ZS", "quantidade": 10, "etapa": "No mar", "chegada_prevista": "2026-10-01", "dias_para_chegar": -47, "atraso_previsto": 30, "prometido": "2026-09-01", "emissao": "2026-04-01"},
             {"codigo": "MP-B", "pedido": "2", "fornecedor": "E-WIN", "quantidade": 5, "etapa": "Aguardando embarque", "chegada_prevista": "2027-01-10", "dias_para_chegar": 54, "atraso_previsto": 20, "prometido": "2026-12-20", "emissao": "2026-09-01"},
             {"codigo": "MP-C", "pedido": "3", "fornecedor": "ZS", "quantidade": 7, "etapa": "No porto / desembaraço", "chegada_prevista": "2026-11-20", "dias_para_chegar": 3, "atraso_previsto": 0, "prometido": "2026-11-25", "emissao": "2026-05-01"},
             {"codigo": "MP-D", "pedido": "4", "fornecedor": "ZS", "quantidade": 9, "etapa": "Parado — verificar saldo", "chegada_prevista": "2026-11-17", "dias_para_chegar": 0, "atraso_previsto": None, "prometido": "2024-01-01", "emissao": "2023-01-01"}]
        with mock.patch("leadtime.forecast_cached", return_value={"available": True, "linhas": L}):
            d = leadtime.previsao_linhas({})
            self.assertEqual(d["total"], 4); self.assertEqual(d["counts"]["alerta"], {"atrasar": 2, "vencida": 1}); self.assertEqual(d["counts"]["fornecedor"], {"ZS": 3, "E-WIN": 1})
            for grp in ("etapa", "fornecedor", "alerta"):
                for v, n in leadtime.previsao_linhas({"fornecedor": "ZS"})["counts"][grp].items():
                    self.assertEqual(leadtime.previsao_linhas({"fornecedor": "ZS", grp: v})["total"], n, f"{grp}={v}")
            v = leadtime.previsao_linhas({"alerta": "vencida"}); self.assertEqual([r["codigo"] for r in v["rows"]], ["MP-A"]); self.assertEqual(v["rows"][0]["dias_vencida"], 47)
            self.assertEqual(leadtime.previsao_linhas({"q": "mp-c"})["total"], 1); self.assertEqual(leadtime.previsao_linhas({"q": "2"})["rows"][0]["codigo"], "MP-B")
            bio, fn = exporter.build("previsao", {"alerta": "atrasar"}); ws = load_workbook(io.BytesIO(bio.read())).worksheets[0]; self.assertEqual(ws.max_row - 1, 2)

class PrevisaoRealizado(_TmpDB):
    def test_foto_diaria_e_erro_na_chegada(self):
        """Etapa 16 · A2: uma foto da previsão por dia (sem parados); quando o embarque chega, compara com a 1ª previsão de cada etapa
        (erro em dias: + = chegou depois do previsto; «na faixa» = dentro do p25–p75)."""
        import leadtime, datetime, data_pipeline as dp
        from unittest import mock
        self.db.init_db(); dp.Store(self.f.name)
        def linhas(prev_p1):
            return {"available": True, "linhas": [
                {"pedido": "P1", "codigo": "MP-1", "processo": "IP1", "etapa": "No mar", "fornecedor": "ZS", "quantidade": 10, "chegada_prevista": prev_p1, "faixa_de": "2026-10-15", "faixa_ate": "2026-10-25"},
                {"pedido": "P2", "codigo": "MP-2", "processo": None, "etapa": "Aguardando embarque", "fornecedor": "E-WIN", "quantidade": 5, "chegada_prevista": "2026-12-01", "faixa_de": "2026-11-20", "faixa_ate": "2026-12-10"},
                {"pedido": "P3", "codigo": "MP-3", "processo": None, "etapa": "Aguardando embarque", "fornecedor": "ZS", "quantidade": 5, "chegada_prevista": "2027-01-01", "faixa_de": "2026-12-20", "faixa_ate": "2027-01-10"},
                {"pedido": "P4", "codigo": "MP-4", "processo": None, "etapa": "Parado — verificar saldo", "fornecedor": "ZS", "quantidade": 5, "chegada_prevista": "2026-10-01", "faixa_de": None, "faixa_ate": None}]}
        with mock.patch("leadtime.forecast_cached", return_value=linhas("2026-10-20")):
            self.assertEqual(leadtime.snapshot_forecast(datetime.date(2026, 10, 1)), 3); self.assertEqual(leadtime.snapshot_forecast(datetime.date(2026, 10, 1)), 0)      # 1 por dia, sem parado
        with mock.patch("leadtime.forecast_cached", return_value=linhas("2026-10-22")): leadtime.snapshot_forecast(datetime.date(2026, 10, 5))     # 2ª foto: vale a 1ª de cada etapa
        self.assertEqual(leadtime.acerto()["geral"]["n"], 0)
        self.sql("INSERT INTO ds_embarques(pedido,code,process,arrival_date) VALUES(?,?,?,?)", [("P1", "MP-1", "IP1", "2026-10-23"), ("P2", "MP-2", "IP9", "2026-11-25")])
        a = leadtime.acerto(); g = a["geral"]
        self.assertEqual((g["n"], g["erro_mediano"], g["pct_faixa"]), (2, -1.5, 100.0)); self.assertEqual(a["aguardando"], 1); self.assertEqual(a["desde"], "2026-10-01")
        e = {x["etapa"]: x for x in a["por_etapa"]}; self.assertEqual((e["No mar"]["erro_mediano"], e["Aguardando embarque"]["erro_mediano"]), (3, -6))
        f = {x["fornecedor"]: x for x in a["por_fornecedor"]}; self.assertEqual((f["ZS"]["n"], f["E-WIN"]["n"]), (1, 1))

class Conciliacao(_TmpDB):
    def test_bi_x_servidor_e_catalogo(self):
        import conciliacao as cc
        self.db.init_db(); import data_pipeline as dp; c = self.db.conn(); c.executescript(dp.SCHEMA); c.commit(); c.close()
        self.sql("INSERT INTO products(perfect_code,description,catalog_position) VALUES(?,?,?)", [("AMD1", "AMORTECEDOR", 1), ("AMD2", "AMORTECEDOR", 2)])
        self.sql("INSERT INTO codes(product_id,code,code_type) VALUES(1,'BJ3A/18045/PA/','oem')")
        self.sql("INSERT INTO ds_vendas(code,qty,total,sale_date,line) VALUES(?,?,?,?,?)", [("AMD1", 10, 1000, "2026-10-03", "AMORTECEDOR"), ("AMD1", 5, 500, "2026-10-20", "AMORTECEDOR"), ("AMD2", 1, 99, "2026-10-04", "AMORTECEDOR"),
            ("AMD9", 4, 400, "2026-10-05", "AMORTECEDOR"), ("AMD1", 7, 700, "2026-09-05", "AMORTECEDOR"), ("AMD2", 3, 30, "2026-10-05", "MARKETING")])      # set/2026 e MARKETING ficam de fora
        f = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False); f.close()
        pd.DataFrame({"PRODUTO": ["AMD1", "AMD2", "BJ3A/18045/PA/", "ZZ9", None], "QTD": [15, 2, 8, 1, None], "VALOR": [1500, 99, 800, 10, None]}).assign(
            PRODUTO=lambda d: d["PRODUTO"].where(d["PRODUTO"].notna(), "Filtros aplicados:\nAno é 2026\nMês é outubro\nIncluídos (1) AMORTECEDOR (LINHA)\nLINHA não é (Em branco), MARKETING ou SAPATA")).to_excel(f.name, index=False)
        r = cc.vendas(f.name, "bi.xlsx"); os.remove(f.name)
        self.assertEqual((r["filtros"]["ano"], r["filtros"]["mes"], r["filtros"]["excluidos"]), (2026, 10, ["MARKETING", "SAPATA"]))
        s = r["servidor"]; self.assertTrue(s["disponivel"]); self.assertEqual(s["iguais"], 1); self.assertEqual([d["produto"] for d in s["diferencas"]], ["AMD2"]); self.assertEqual(s["diferencas"][0]["dq"], -1)
        self.assertEqual([x["produto"] for x in s["so_no_servidor"]], ["AMD9"]); self.assertEqual(sorted(x["produto"] for x in s["so_no_bi"]), ["BJ3A/18045/PA/", "ZZ9"])
        k = r["catalogo"]; self.assertEqual((k["skus_fora"], k["resolvidos_por_equivalencia"]), (2, 1)); self.assertEqual(k["rows"][0]["equivalente"], "AMD1 (oem)")

class CatalogoPlanilha(_TmpDB):
    def test_planilha_prevalece_e_tira_do_catalogo(self):
        import loaders, importer
        self.db.init_db(); self.sql("INSERT INTO products(perfect_code,description,ean,catalog_position) VALUES(?,?,?,?)", [("AMD1", "ANTIGA", "111", 1), ("AMD7", "SAIU", "777", 2)])
        f = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False); f.close()
        pd.DataFrame({"Código do Produto": ["AMD1", "AMD2"], "Descrição do Produto": ["AMORTECEDOR DIANTEIRO LD", "AMORTECEDOR TRASEIRO LD/LE"], "Cód. Barras": ["999", "222"], "Descrição do SubGrupo do Produto": ["AMORTECEDOR", "AMORTECEDOR LINHA PESADA"],
                      "Produto é Lançamento?": ["S", "N"]}).to_excel(f.name, index=False)
        df, _ = importer.read_table(f.name, None); s = loaders.run(f.name, None, importer.suggest_mapping(df.columns), None, "CatalogoAMD - atualizar.xlsx", True); os.remove(f.name)
        c = self.db.conn(); P = {r["perfect_code"]: dict(r) for r in c.execute("SELECT * FROM products")}; c.close()
        self.assertEqual((P["AMD1"]["description"], P["AMD1"]["ean"], P["AMD1"]["is_launch"], P["AMD1"]["catalog_position"]), ("AMORTECEDOR DIANTEIRO LD", "999", "S", 1))      # a planilha prevalece
        self.assertEqual(P["AMD2"]["catalog_subgroup"], "AMORTECEDOR LINHA PESADA"); self.assertIsNone(P["AMD7"]["catalog_position"]); self.assertEqual(P["AMD7"]["description"], "SAIU")  # saiu do catálogo, mas não foi apagado
        self.assertEqual(s["counts"]["conflicts"], 0)

    def test_campos_novos_sistema_familia_haste_lancamento(self):
        """Etapa 16 (Q12/Q13): colunas Sistema, Familia, Diametro Haste e Lançamento do CatalogoAMD. Sistema inválido → usa a Observação e abre pendência."""
        import loaders, importer, queries
        self.db.init_db()
        def carregar(sistemas):
            f = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False); f.close()
            pd.DataFrame({"Código Produto": ["AMD1", "AMD2", "AMD3", "AMD4"], "Descrição Produto": ["AMORTECEDOR"] * 4, "Lançamento": ["Sim", None, None, None],
                          "Observação": [None, None, "Sistema.: Óleo", None], "Sistema": sistemas, "Familia": ["Estrutural", "Cabine", "Convencional", None],
                          "Diametro Haste": ["20", "12.5", None, "22"]}).to_excel(f.name, index=False)
            df, _ = importer.read_table(f.name, None); loaders.run(f.name, None, importer.suggest_mapping(df.columns), None, "CatalogoAMD.xlsx", True); os.remove(f.name)
            c = self.db.conn(); P = {r["perfect_code"]: dict(r) for r in c.execute("SELECT p.*, d.rod_diameter_mm FROM products p LEFT JOIN dimensions d ON d.product_id=p.id")}
            pend = {r[0] for r in c.execute("SELECT p.perfect_code FROM pendencies x JOIN products p ON p.id=x.product_id WHERE x.kind='campo_invalido' AND x.field='sistema' AND x.status='aberta'")}; c.close()
            return P, pend
        P, pend = carregar(["FORCE GAS", "FORCE OIL", "Código Produto", "Código Produto"])
        self.assertEqual([P[k]["system_type"] for k in ("AMD1", "AMD2", "AMD3", "AMD4")], ["gas", "oleo", "oleo", None])        # AMD3: inválido → Observação
        self.assertEqual(pend, {"AMD3", "AMD4"})
        self.assertEqual((P["AMD1"]["family"], P["AMD2"]["family"]), ("ESTRUTURAL", "CABINE"))                                      # mesmo formato das famílias do Inmetro
        self.assertEqual((P["AMD1"]["rod_diameter_mm"], P["AMD2"]["rod_diameter_mm"], P["AMD4"]["rod_diameter_mm"]), (20.0, 12.5, 22.0))
        self.assertEqual((P["AMD1"]["is_launch"], P["AMD2"]["is_launch"]), ("S", "N"))                                              # coluna presente e vazia = não é lançamento
        _, pend = carregar(["FORCE GAS", "FORCE OIL", "FORCE GAS", "FORCE OIL"]); self.assertEqual(pend, set())                   # planilha corrigida: pendência some
        # filtros e contagens da tela Produtos
        cod = lambda f: sorted(r["perfect_code"] for r in queries.products(f)["rows"])
        self.assertEqual(cod({"family": "ESTRUTURAL"}), ["AMD1"]); self.assertEqual(cod({"rod": "12.5"}), ["AMD2"]); self.assertEqual(cod({"launch": "S"}), ["AMD1"])
        self.assertEqual(cod({"system": "oleo"}), ["AMD2", "AMD4"]); self.assertEqual(cod({"launch": "N", "system": "gas"}), ["AMD3"])
        fc = queries.product_facets()
        self.assertEqual(fc["family"][0], {"v": "CABINE", "n": 1}); self.assertIn({"v": 12.5, "n": 1}, fc["rod"]); self.assertEqual((fc["launch"], fc["system"]["gas"], fc["system"]["oleo"]), (1, 2, 2))
        r = queries.products({"q": "AMD1"})["rows"][0]; self.assertEqual((r["is_launch"], r["rod_diameter_mm"]), ("S", 20.0))

    def test_linha_e_hibrido(self):
        """Etapa 17 · Q14: colunas Linha e «Hibrido ou elétrico» do CatalogoAMD. Vazio = não informado (nunca «não»); a planilha manda, inclusive quando esvazia."""
        import loaders, importer, queries
        self.db.init_db()
        def carregar(linhas, hib):
            f = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False); f.close()
            pd.DataFrame({"Código Produto": ["AMD1", "AMD2", "AMD3"], "Descrição Produto": ["AMORTECEDOR"] * 3, "Linha": linhas, "Hibrido ou elétrico": hib,
                          "Cód. Barras": ["789", None, "790"], "Peso (Kg)": ["1,5", None, "2"]}).to_excel(f.name, index=False)
            df, _ = importer.read_table(f.name, None); loaders.run(f.name, None, importer.suggest_mapping(df.columns), None, "CatalogoAMD.xlsx", True); os.remove(f.name)
            c = self.db.conn(); P = {r["perfect_code"]: dict(r) for r in c.execute("SELECT * FROM products")}; c.close(); return P
        P = carregar(["LINHA LEVE", "Linha pick-up e utilitários", None], ["SIM", "NÃO", None])
        self.assertEqual([P[k]["catalog_line"] for k in ("AMD1", "AMD2", "AMD3")], ["LINHA LEVE", "LINHA PICK-UP E UTILITÁRIOS", None])
        self.assertEqual([P[k]["hybrid"] for k in ("AMD1", "AMD2", "AMD3")], ["S", "N", None])
        self.assertEqual((P["AMD1"]["cat_ean"], P["AMD1"]["cat_weight_kg"], P["AMD2"]["cat_ean"]), ("789", 1.5, None))       # peso/EAN como estão na planilha (comparação com o BI03)
        cod = lambda f: sorted(r["perfect_code"] for r in queries.products(f)["rows"])
        self.assertEqual(cod({"linha": "LINHA LEVE"}), ["AMD1"]); self.assertEqual(cod({"linha": "sem"}), ["AMD3"])
        self.assertEqual(cod({"hibrido": "S"}), ["AMD1"]); self.assertEqual(cod({"hibrido": "N"}), ["AMD2"]); self.assertEqual(cod({"hibrido": "nd"}), ["AMD3"])
        fc = queries.product_facets(); self.assertEqual(fc["hibrido"], {"S": 1, "N": 1, "nd": 1}); self.assertEqual(sum(x["n"] for x in fc["linha"]), 2)
        P = carregar([None, None, None], [None, "SIM", None])                     # a planilha esvaziou: o banco acompanha
        self.assertEqual((P["AMD1"]["catalog_line"], P["AMD1"]["hybrid"], P["AMD2"]["hybrid"]), (None, None, "S"))

class CaixaComSufixo(_TmpDB):
    def test_sufixo_m_b_nao_e_conflito_e_usar_valor_da_planilha(self):
        """Etapa 16 · D: caixa «PP025M» (Motorcraft) / «PP025B» (BPROAUTO) × «PP025» da EstruturaAMD não é conflito e o banco fica como está.
        Caixa base diferente continua conflito; «usar o valor da planilha» grava o valor importado e resolve. Conflito falso antigo é fechado na migração."""
        import loaders, importer, queries
        self.db.init_db()
        self.sql("INSERT INTO products(perfect_code,description,package_code) VALUES(?,?,?)", [("AMD1", "A", "PP025M"), ("AMD2", "B", "PP014M"), ("AMD3", "C", "PP026B"), ("AMD4", "D", "PP030")])
        f = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False); f.close()
        pd.DataFrame({"Codigo": ["AMD1", "AMD2", "AMD3", "AMD4"], "Componente": ["PP025", "PP030", "PP026", "PP030"], "Descricao Comp.": ["CAIXA"] * 4}).to_excel(f.name, index=False)
        df, _ = importer.read_table(f.name, None); s = loaders.run(f.name, None, importer.suggest_mapping(df.columns), None, "EstruturaAMD.xls", True); os.remove(f.name)
        self.assertEqual(s["counts"]["conflicts"], 1)
        c = self.db.conn()
        try:
            box = dict(c.execute("SELECT perfect_code,package_code FROM products").fetchall())
            pend = c.execute("SELECT x.id,p.perfect_code,x.field FROM pendencies x JOIN products p ON p.id=x.product_id WHERE x.kind='conflito' AND x.status='aberta'").fetchall()
        finally: c.close()
        self.assertEqual(box, {"AMD1": "PP025M", "AMD2": "PP014M", "AMD3": "PP026B", "AMD4": "PP030"})
        self.assertEqual([(r[1], r[2]) for r in pend], [("AMD2", "package_code")])
        self.assertEqual(queries.pendency_apply(pend[0][0]), {"field": "package_code", "value": "PP030", "old": "PP014M"})
        c = self.db.conn()
        try:
            self.assertEqual(c.execute("SELECT package_code FROM products WHERE perfect_code='AMD2'").fetchone()[0], "PP030")
            self.assertEqual(c.execute("SELECT status FROM pendencies WHERE id=?", (pend[0][0],)).fetchone()[0], "resolvida")
            pid = c.execute("SELECT id FROM products WHERE perfect_code='AMD1'").fetchone()[0]          # conflito falso gravado antes da regra
            c.execute("INSERT INTO pendencies(product_id,kind,field,description) VALUES(?,?,?,?)", (pid, "conflito", "package_code", "Valor atual «PP025M» × importado «PP025» (fonte EstruturaAMD.xls). Nada foi sobrescrito."))
            c.execute("INSERT INTO pendencies(product_id,kind,field,description) VALUES(?,?,?,?)", (pid, "campo_ausente", "peso", "Campo ausente: peso")); c.commit()
        finally: c.close()
        with self.assertRaises(ValueError): queries.pendency_apply(pend[0][0])                    # já resolvida
        self.db.migrate()
        c = self.db.conn()
        try: st = dict(c.execute("SELECT kind,status FROM pendencies WHERE product_id=?", (pid,)).fetchall())
        finally: c.close()
        self.assertEqual(st, {"conflito": "resolvida", "campo_ausente": "aberta"})

class FamiliaInmetro(_TmpDB):
    def test_catalogo_prevalece_e_vira_anomalia(self):
        """Etapa 16 · D1/D2: família do certificado Inmetro diferente da do catálogo não abre conflito (o CatalogoAMD prevalece) e aparece em Anomalias;
        família vazia é preenchida; EAN diferente continua conflito e também aparece em Anomalias. Conflito de família antigo vindo do Inmetro é fechado na migração."""
        import loaders, importer, anomalias
        self.db.init_db()
        self.sql("INSERT INTO products(perfect_code,description,family,ean) VALUES(?,?,?,?)", [("AMD1", "A", "CONVENCIONAL", "111"), ("AMD2", "B", None, None), ("AMD3", "C", "CABINE", "555")])
        f = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False); f.close()
        pd.DataFrame({"Perfect": ["AMD1", "AMD1", "AMD2", "AMD3"], "Inmetro": ["001/2018", "009/2017", "002/2018", "003/2018"], "Familia": ["Semi-estrutural", "Convencional", "Estrutural", "Cabine"],
                      "Cod. Barras": ["222", "222", "333", "555"]}).to_excel(f.name, index=False)
        df, _ = importer.read_table(f.name, None); loaders.run(f.name, None, importer.suggest_mapping(df.columns), None, "InmetroE-win - Todos - Certificado.xlsx", True); os.remove(f.name)
        c = self.db.conn()
        try:
            P = {r[0]: (r[1], r[2]) for r in c.execute("SELECT perfect_code,family,ean FROM products")}
            pend = sorted((r[0], r[1]) for r in c.execute("SELECT p.perfect_code,x.field FROM pendencies x JOIN products p ON p.id=x.product_id WHERE x.kind='conflito' AND x.status='aberta'"))
        finally: c.close()
        self.assertEqual(P, {"AMD1": ("CONVENCIONAL", "111"), "AMD2": ("ESTRUTURAL", "333"), "AMD3": ("CABINE", "555")})
        self.assertEqual(pend, [("AMD1", "ean")])
        fam = anomalias.familia(); self.assertEqual([r["perfect_code"] for r in fam], ["AMD1"])
        self.assertEqual(fam[0]["family"], "CONVENCIONAL"); self.assertEqual(fam[0]["inmetro_families"], ["CONVENCIONAL", "SEMI-ESTRUTURAL"]); self.assertTrue(fam[0]["mixed"])
        e = anomalias.ean(); self.assertEqual([(r["perfect_code"], r["current"], r["imported"]) for r in e], [("AMD1", "111", "222")])
        self.assertEqual(anomalias.counts()["familia"], 1); self.assertEqual(anomalias.familia("amd3"), [])
        c = self.db.conn()
        try:
            for code, imp in (("AMD1", "SEMI-ESTRUTURAL"), ("AMD3", "ESTRUTURAL")):          # o 1º veio do Inmetro (está nos certificados); o 2º não
                pid = c.execute("SELECT id FROM products WHERE perfect_code=?", (code,)).fetchone()[0]
                c.execute("INSERT INTO pendencies(product_id,kind,field,description) VALUES(?,?,?,?)", (pid, "conflito", "family", f"Valor atual «X» × importado «{imp}» (fonte antiga.xlsx). Nada foi sobrescrito."))
            c.commit()
        finally: c.close()
        self.db.migrate()
        c = self.db.conn()
        try: st = dict(c.execute("SELECT p.perfect_code,x.status FROM pendencies x JOIN products p ON p.id=x.product_id WHERE x.field='family'").fetchall())
        finally: c.close()
        self.assertEqual(st, {"AMD1": "resolvida", "AMD3": "aberta"})

class MetaRdPorValidacao(_TmpDB):
    """Etapa 16 · D5/D5b: «Pendente compras» some quando o item já é ITEM RECEBIDO (etapa 20: a marcação manual não vale mais);
    meta R-D = itens validados pelo usuário no ano (DATA APROV) que chegaram a ITEM RECEBIDO, mesmo depois do fim do ano. A lista traz todas as validações do ano."""
    R = "REDESENVOLVIMENTO"
    def setUp(self):
        super().setUp(); self.db.init_db(); import goals, json; goals.ensure()
        v = lambda u, d: json.dumps({"USER APROV": u, "DATA APROV": d})
        ins = "INSERT INTO rd_projects(code,suggestion,status,validation_substatus,description,line,extra) VALUES(?,?,?,?,?,'AMORTECEDOR',?)"
        self.sql(ins, [("V1", self.R, "ITEM RECEBIDO", "PENDENTE COMPRAS", "AMORTECEDOR", v("ITALOC", "2026-03-10")),
                       ("V2", self.R, "FINALIZANDO CIT", "VALIDAÇÃO REPROVADA", "AMORTECEDOR", v("italoc ", "2026-05-02")),
                       ("V3", self.R, "EM COTAÇÃO", "PENDENTE VALIDAÇÃO QUALIDADE / PENDENTE COMPRAS", "AMORTECEDOR", v("ITALOC", "2026-06-20")),
                       ("V4", self.R, "ITEM RECEBIDO", None, "AMORTECEDOR", v("ITALOC", "2025-12-01")),
                       ("V5", self.R, "ITEM RECEBIDO", None, "AMORTECEDOR", v("OUTRO", "2026-02-01"))])
        self.sql("INSERT INTO dev_item_state(code,kind,status,present) VALUES(?,?,?,1)", [("V1", self.R, "ITEM RECEBIDO"), ("V2", self.R, "FINALIZANDO CIT")])     # V3: sem estado → vale rd_projects

    def flags(self):
        c = self.db.conn()
        try: return {r[0]: r[1] for r in c.execute("SELECT code,pend_compras FROM v_rd_flags")}
        finally: c.close()

    def test_pendente_compras_some_quando_recebido(self):
        self.assertEqual(self.flags()["V1"], 0); self.assertEqual(self.flags()["V3"], 1)
        self.sql("INSERT INTO rd_projects(code,suggestion,status,validation_substatus,description,line) VALUES('V4',?,'FINALIZANDO CIT','PENDENTE COMPRAS','AMORTECEDOR','AMORTECEDOR')", [(self.R,)])
        self.assertEqual(self.flags()["V4"], 1)                                   # etapa 19 · Q1: no R-D vale por aplicação — esta aplicação ainda não foi recebida
        self.sql("UPDATE rd_projects SET status='ITEM RECEBIDO' WHERE code='V4'")
        self.assertEqual(self.flags()["V4"], 0)                                   # todas as aplicações recebidas: o sub status antigo não vale
        self.sql("INSERT INTO rd_flags(code,suggestion,flag,value) VALUES('V1',?,'pend_compras',1)", [(self.R,)])
        self.assertEqual(self.flags()["V1"], 0)                                   # etapa 20 · Q3: marcação manual antiga não vale mais — só o servidor

    def test_sub_status_do_servidor_por_parte(self):
        """Etapa 20 · Q4: «A / B» conta em A e em B; em andamento deixa de fora as aplicações recebidas; filtro sub=<chave>:<valor>."""
        import rd
        fc = rd.facets(self.R); val = {x["v"]: (x["n"], x["l"]) for g in fc["subs"] if g["key"] == "validacao" for x in g["values"]}
        # V1 (recebido) fora; etapa 21: aprovada, reprovada e pendente qualidade ficam sempre no quadro e juntam as grafias do servidor
        self.assertEqual(val, {"VALIDAÇÃO REPROVADA": (1, 1), "PENDENTE QUALIDADE": (1, 1), "VALIDAÇÃO APROVADA": (0, 0), "PENDENTE COMPRAS": (1, 1)})
        self.assertEqual([r["code"] for r in rd.items(self.R, {"status": "andamento", "sub": "validacao:@QUALIDADE"})["rows"]], ["V3"])
        self.assertEqual([r["code"] for r in rd.items(self.R, {"status": "andamento", "sub": "validacao:PENDENTE COMPRAS"})["rows"]], ["V3"])
        self.assertEqual(sorted(r["code"] for r in rd.items(self.R, {"status": "", "sub": "validacao:PENDENTE COMPRAS"})["rows"]), ["V1", "V3"])
        self.assertEqual((fc["andamento"]["n"], fc["total"]), (2, 5))
        r3 = rd.items(self.R, {"status": "andamento", "q": "V3"})["rows"][0]["subs"]
        self.assertEqual([x["v"] for x in r3], ["PENDENTE VALIDAÇÃO QUALIDADE", "PENDENTE COMPRAS"])

    def test_meta_rd_conta_validados_do_ano_quando_recebidos(self):
        import goals
        L = goals.rd_validations(2026); r = {x["code"]: x for x in L["rows"]}
        self.assertEqual(sorted(r), ["V1", "V2", "V3"])
        self.assertEqual({k: x["counts"] for k, x in r.items()}, {"V1": True, "V2": False, "V3": False})
        self.assertEqual((r["V1"]["status"], r["V2"]["status"], r["V3"]["status"]), ("ITEM RECEBIDO", "FINALIZANDO CIT", "EM COTAÇÃO"))
        self.assertIn("val_reprovada", r["V2"]["flags"]); self.assertIn("pend_validacao_qual", r["V3"]["flags"]); self.assertEqual(r["V1"]["valid_at"], "2026-03-10")
        self.assertEqual(L["counts"], {"todas": 3, "contam": 1, "aguardando": 2, "pend_validacao_qual": 1, "val_reprovada": 1})
        g = goals.progress(2026)["goals"][self.R]; self.assertEqual(g["tracked"], 1); self.assertEqual((g["parts"]["validacoes"], g["parts"]["recebidas"], g["parts"]["aguardando"]), (3, 1, 2))
        self.assertEqual(goals.progress(2025)["goals"][self.R]["tracked"], 1)     # V4: validado em 2025
        self.sql("UPDATE dev_item_state SET status='ITEM RECEBIDO' WHERE code='V2'")
        self.assertEqual(goals.progress(2026)["goals"][self.R]["tracked"], 2)     # chegou depois: entra na meta do ano da validação

class FordForaDaBase(_TmpDB):
    def test_pn_ford_entra_na_lista_motorcraft_sem_contar(self):
        """Etapa 16 · D7: código no formato Ford (XXXX/18xxx/XX) fora da base ItensMotorcraft vai para a lista MOTORCRAFT marcado «fora da base»,
        mas NÃO conta no indicador (cartão) da marca; código que não é Ford continua «Sem marca»."""
        import brands
        self.db.init_db()
        self.sql("INSERT INTO brand_items(brand,code,norm_code) VALUES('MOTORCRAFT','BJ3A/18045/AA/','BJ3A18045AA')")
        self.sql("INSERT INTO rd_projects(code,suggestion,status,description,line) VALUES(?,?,?,?,'AMORTECEDOR')",
                 [("ENS1/18097/AC", "DESENVOLVIMENTO", "EM COTAÇÃO", "AMORTECEDOR"), ("NZ6Z/18124/N", "DESENVOLVIMENTO", "EM COTAÇÃO", "AMORTECEDOR"), ("48510-79425-2P", "DESENVOLVIMENTO", "EM COTAÇÃO", "AMORTECEDOR")])
        self.assertTrue(brands.is_ford("MB5A/18K001/AA/")); self.assertFalse(brands.is_ford("48510-79425-2P")); self.assertFalse(brands.is_ford("AMD0103"))
        s = {b["brand"]: b for b in brands.summary()["brands"]}
        self.assertEqual((s["MOTORCRAFT"]["total"], s["MOTORCRAFT"]["fora_base"]), (1, 2)); self.assertEqual(brands.summary()["unclassified"], 1)
        d = brands.items("MOTORCRAFT", {})
        self.assertEqual(d["total"], 3); self.assertEqual(d["fora_base"], 2); self.assertEqual(d["counts"]["brand"]["MOTORCRAFT"], 1)
        self.assertEqual(sorted(i["code"] for i in d["rows"] if i["fora_base"]), ["ENS1/18097/AC", "NZ6Z/18124/N"])
        self.assertEqual([i["code"] for i in brands.items("OUTROS", {})["rows"]], ["48510-79425-2P"])

class SemProjeto(_TmpDB):
    def test_so_desenvolvimento_em_andamento(self):
        """Etapa 16 · D6: «Sem projeto» (Desenhos) conta só DESENVOLVIMENTO em andamento fora do catálogo: sem ITEM RECEBIDO (em nenhuma aplicação), sem cancelado, sem R-D."""
        import drawings
        self.db.init_db(); self.sql("INSERT INTO products(perfect_code,description) VALUES('AMD9','AMORTECEDOR')")
        D, R = "DESENVOLVIMENTO", "REDESENVOLVIMENTO"
        self.sql("INSERT INTO rd_projects(code,suggestion,status,description,line,product_id) VALUES(?,?,?,?,'AMORTECEDOR',?)",
                 [("A1", D, "EM COTAÇÃO", "AMORTECEDOR", None), ("A2", D, "ITEM RECEBIDO", "AMORTECEDOR", None), ("A3", D, "EM COTAÇÃO", "AMORTECEDOR", None), ("A3", D, "ITEM RECEBIDO", "AMORTECEDOR", None),
                  ("A4", D, "CANCELADO", "AMORTECEDOR", None), ("R1", R, "EM COTAÇÃO", "AMORTECEDOR", None), ("AMD9", D, "EM COTAÇÃO", "AMORTECEDOR", 1)])
        self.assertEqual(drawings._missing("projeto", set()), {"A1"})
        self.assertEqual(drawings.stats("projeto")["missing"], 1)

class BuscaConcorrente(_TmpDB):
    def test_codigo_com_ou_sem_pontuacao(self):
        import queries
        self.db.init_db(); self.sql("INSERT INTO products(perfect_code,description,catalog_position) VALUES('AMD1','AMORTECEDOR',1)")
        self.sql("INSERT INTO codes(product_id,code,normalized_code,code_type,brand) VALUES(1,'2-JB.5909/F','2-JB.5909F','concorrente','JINBO')")
        for t in ("2-JB.5909/F", "2jb5909f", "JB5909", "2 JB 5909 F"):
            r = queries.products({"q": t}); self.assertEqual([x["perfect_code"] for x in r["rows"]], ["AMD1"], t); self.assertEqual(r["rows"][0]["via"][0]["brand"], "JINBO")
        self.assertEqual(queries.products({"code": "jb-5909", "code_type": "concorrente"})["total"], 1); self.assertEqual(queries.products({"q": "XX999"})["total"], 0)

class EnvPersistente(unittest.TestCase):
    def test_nova_versao_acha_o_env_da_anterior_e_guarda_copia(self):
        import data_pipeline as dp
        from unittest import mock
        with tempfile.TemporaryDirectory() as root:
            old, new, home = (os.path.join(root, d) for d in ("v10", "v11", "home")); [os.makedirs(d) for d in (old, new)]
            open(os.path.join(old, ".env"), "w").write("PSD_TESTE_X=abc\n")
            with mock.patch.object(dp, "BASE", new), mock.patch.object(dp, "PERSIST_DIR", home), mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("PSD_TESTE_X", None); self.assertEqual(dp.env_candidates(), [os.path.join(old, ".env")])
                dp.load_env(); self.assertEqual(os.environ.get("PSD_TESTE_X"), "abc"); self.assertTrue(os.path.isfile(os.path.join(home, ".env")))      # cópia fixa criada
                os.environ.pop("PSD_TESTE_X"); os.remove(os.path.join(old, ".env")); self.assertEqual(dp.env_candidates(), [os.path.join(home, ".env")])    # versão antiga apagada: a cópia fixa continua valendo
                dp.load_env(); self.assertEqual(os.environ.get("PSD_TESTE_X"), "abc"); os.environ.pop("PSD_TESTE_X", None)

class UniversoDesRd(_TmpDB):
    def test_linhas_aceitas_e_tipos_exclusivos(self):
        import data_pipeline as dp, rules
        raw = pd.DataFrame({"CÓDIGO": ["A1", "A2", "A3", "C1", "K1", "B1", "B1"], "SUGESTÃO": ["DES", "R-D", "DES", "DES", "DES", "DES", "R-D"],
                            "STATUS": ["EM COTAÇÃO"] * 7, "DESCRIÇÃO": ["AMORTECEDOR DIANT", "AMORTECEDOR TRAS", "AMORTECEDOR PESADO", "COXIM DO AMORTECEDOR", "KIT AMORTECEDOR", "AMORTECEDOR X", "AMORTECEDOR X"],
                            "LINHA": ["AMORTECEDOR", " amortecedor ", "AMORTECEDOR LINHA PESADA", "COX", "KAD", "AMORTECEDOR", "AMORTECEDOR"]})
        res = dp.normalize_dev(raw); df = res.rows
        self.assertEqual(sorted(df.loc[df["code"] == "B1", "kind"].unique().tolist()), ["DESENVOLVIMENTO", "REDESENVOLVIMENTO"]); self.assertEqual(res.warnings.get("codigos_em_des_e_rd"), 1)      # etapa 19: cada linha pelo tipo do servidor
        self.db.init_db(); c = self.db.conn(); c.executemany("INSERT INTO rd_projects(code,suggestion,description,line) VALUES(?,?,?,?)", list(df[["code", "kind", "description", "line"]].itertuples(index=False, name=None))); c.commit()
        ok = sorted(r[0] for r in c.execute("SELECT DISTINCT code FROM rd_projects WHERE " + rules.desc_sql()))
        pes = sorted(r[0] for r in c.execute("SELECT DISTINCT code FROM rd_projects WHERE " + rules.desc_sql(pesada=True))); c.close()
        self.assertEqual(ok, ["A1", "A2", "B1"])                # etapa 20: módulos e Dashboard só com a LINHA exata «AMORTECEDOR»; COX e KAD fora
        self.assertEqual(pes, ["A1", "A2", "A3", "B1"])         # metas: «AMORTECEDOR LINHA PESADA» dentro
        c = self.db.conn(); c.execute("UPDATE rd_projects SET line=NULL"); c.commit()      # banco antigo, sem LINHA: vale a descrição, ainda sem COX/KAD
        ok2 = sorted(r[0] for r in c.execute("SELECT DISTINCT code FROM rd_projects WHERE " + rules.desc_sql())); c.close(); self.assertEqual(ok2, ["A1", "A2", "A3", "B1", "K1"])      # fallback pela descrição: K1 («KIT AMORTECEDOR») só sai quando a coluna LINHA (KAD) chega do servidor

    def test_item_bloqueado_ou_inativo_no_erp_sai_do_universo(self):
        import rules, rd
        self.db.init_db()
        self.sql("INSERT INTO rd_projects(code,suggestion,description,line) VALUES(?,?,?,?)", [(x, "DESENVOLVIMENTO", "AMORTECEDOR", "AMORTECEDOR") for x in ("A1", "A2", "A3", "A4")])
        self.sql("INSERT INTO ds_situacao(code,active,blocked) VALUES(?,?,?)", [("A1", "ATIVO", "SIM"), ("A2", "ATIVO", "NAO"), ("A3", "INATIVO", "NAO")])
        c = self.db.conn()
        try: ok = sorted(r[0] for r in c.execute("SELECT DISTINCT code FROM rd_projects r WHERE " + rules.desc_sql("r.description")))
        finally: c.close()
        self.assertEqual(ok, ["A2", "A4"])          # A1 bloqueado e A3 inativo saem; A4 (fora da view do ERP) fica
        self.assertEqual(sorted(x["code"] for x in rd.items("DESENVOLVIMENTO", {"all": 1})["rows"]), ["A2", "A4"])
        self.assertEqual(self.db.stats()["des_items"], 2)
        import goals; self.assertEqual(sorted(goals._meta("DESENVOLVIMENTO")), ["A1", "A2", "A3", "A4"])      # metas: o que foi recebido e validado continua contando

    def test_familia_do_servidor_marca_e_itens_por_linha(self):
        """Etapa 21: a FAMILIA decide a linha (amortecedor · moto · pesada), mesmo com LINHA «AMORTECEDOR»; DES padrão = marca PERFECT (ou vazia);
        itens = linhas do servidor, códigos = distintos."""
        import rd, rules
        self.db.init_db(); D, R = "DESENVOLVIMENTO", "REDESENVOLVIMENTO"
        rows = [("F1", D, "AMORTECEDOR", "AMORTECEDOR", "PERFECT"), ("F2", D, "AMORTECEDOR", "AMORTECEDOR DE MOTO", "PERFECT"), ("F3", D, "AMORTECEDOR", "AMORTECEDOR LINHA PESADA", "PERFECT"),
                ("F4", D, "AMORTECEDOR", "AMORTECEDOR", "BPROAUTO"), ("F5", D, "AMORTECEDOR", "AMORTECEDOR", None), ("F6", D, "AMORTECEDOR", None, "PERFECT"),
                ("G1", R, "AMORTECEDOR", "AMORTECEDOR", None), ("G1", R, "AMORTECEDOR", "AMORTECEDOR", "MOTORCRAFT"), ("G2", R, "AMORTECEDOR LINHA PESADA", "AMORTECEDOR LINHA PESADA", None)]
        self.sql("INSERT INTO rd_projects(code,suggestion,description,line,family,brand,status) VALUES(?,?,'AMORTECEDOR',?,?,?,'EM COTAÇÃO')", rows)
        cod = lambda k, f: sorted({x["code"] for x in rd.items(k, {"all": 1, **f})["rows"]})
        self.assertEqual(cod(D, {}), ["F1", "F5", "F6"])                       # F2 moto e F3 pesada fora; F4 outra marca fora; F6 sem FAMILIA vale pela LINHA
        self.assertEqual(cod(D, {"linha": "moto"}), ["F2"]); self.assertEqual(cod(D, {"linha": "pesada"}), ["F3"])
        self.assertEqual(cod(D, {"marca": "todas"}), ["F1", "F4", "F5", "F6"]); self.assertEqual(cod(D, {"marca": "BPROAUTO"}), ["F4"])
        r = rd.items(R, {"all": 1}); self.assertEqual((r["total"], r["linhas"]), (1, 2))      # R-D sem filtro de marca: 2 itens (linhas) do mesmo código
        fc = rd.facets(R); self.assertEqual({x["v"]: x["l"] for x in fc["familias"]}, {"amortecedor": 2, "moto": 0, "pesada": 1})
        self.assertEqual((fc["andamento"]["l"], fc["andamento"]["n"]), (2, 1))
        self.assertEqual(self.db.stats()["des_items"], 3); self.assertEqual(self.db.stats()["rd_items"], 2)      # tela inicial: itens em andamento, como a tela


class MercadoLivreFallback(unittest.TestCase):
    def test_token_expirado_cai_para_rota_publica(self):
        import os, json, price_search as ps
        calls = []
        def fetch(url, headers=None, timeout=None, data=None):
            calls.append((url, dict(headers or {})))
            if (headers or {}).get("Authorization"): return 401, "expired"
            return 200, json.dumps({"results": []})
        old = os.environ.get("ML_ACCESS_TOKEN"); os.environ["ML_ACCESS_TOKEN"] = "TOKEN-EXPIRADO"
        try: items, err = ps.ml_api_search("amortecedor 16470", fetch=fetch)
        finally:
            if old is None: os.environ.pop("ML_ACCESS_TOKEN", None)
            else: os.environ["ML_ACCESS_TOKEN"] = old
        self.assertEqual(err, None); self.assertEqual(items, [])
        self.assertEqual(len(calls), 2); self.assertNotIn("Authorization", calls[1][1])

    def test_erro_inesperado_na_api_vira_json(self):
        import os, app as A, queries
        old = os.environ.get("PSD_AUTH"); os.environ["PSD_AUTH"] = "off"
        real = queries.products
        def boom(f): raise RuntimeError("falha de teste")
        queries.products = boom
        try: r = A.app.test_client().get("/api/products")
        finally:
            queries.products = real
            if old is None: os.environ.pop("PSD_AUTH", None)
            else: os.environ["PSD_AUTH"] = old
        self.assertEqual(r.status_code, 500); self.assertIn("falha de teste", r.get_json()["error"])


class EventoNovoItem(_TmpDB):
    def test_item_que_aparece_ja_recebido_nao_conta_como_recebido_hoje(self):
        """Etapa 19: linha DES que antes era regravada como R-D volta ao DES e aparece como item novo já recebido (origin «novo_item»): não data o recebimento."""
        import goals
        self.db.init_db(); goals.ensure()
        self.sql("INSERT INTO dev_status_events(code,kind,field,from_value,to_value,at,origin) VALUES(?,?,?,?,?,?,?)",
                 [("N1", "DESENVOLVIMENTO", "status", None, "ITEM RECEBIDO", "2026-11-19 10:00", "novo_item"), ("N2", "DESENVOLVIMENTO", "status", "FINALIZANDO CIT", "ITEM RECEBIDO", "2026-11-19 10:00", "sync")])
        self.assertEqual(sorted(c for c, _ in goals._events(2026)), ["N2"])


class MetasEstritas(unittest.TestCase):
    def test_linha_estrita_sem_cox_kad_e_tipo_por_linha(self):
        import metas
        df = pd.DataFrame([("A1", "DES", "AMORTECEDOR", "italoc "), ("A2", "des", "Amortecedor Linha Pesada", "ITALOC"), ("C1", "DES", "COXIM DO AMORTECEDOR", "ITALOC"),
                           ("K1", "R-D", "AMORTECEDOR KAD", "ITALOC"), ("A3", "R-D", "AMORTECEDOR", "ITALOC"), ("A1", "R-D", "AMORTECEDOR", "ITALOC"),
                           ("A4", "DES", "AMORTECEDOR", "OUTRO")], columns=["CODIGO", "SUGESTAO", "LINHA", "USER_VALID"])
        r = metas.validation_counts(df)
        self.assertEqual((r["DES"], r["R-D"]), (2, 2))      # etapa 19: A1 e A2 em DES; A3 e A1 em R-D (cada linha pelo tipo do servidor); COX/KAD e outro usuário ficam fora


class BrandsPlanilha(_TmpDB):
    def test_left_join_pelo_codigo_perfect(self):
        import loaders, importer
        self.db.init_db()
        self.sql("INSERT INTO products(perfect_code,description,catalog_position) VALUES(?,?,?)", [("AMD0122", "AMORTECEDOR DIANT. LD/LE", 1)])
        f = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False); f.close()
        pd.DataFrame({"Código da marca": ["1BP31974AB", "1BP99999ZZ", None], "Código PERFECT": ["AMD0122", "AMD9999", None], "Descrição": ["AMORT", "AMORT", None],
                      "Veículo / aplicação": ["FIAT - STRADA", "FIAT - UNO", None], "Em DES": ["Sim", "Sim", None]}).to_excel(f.name, index=False)
        mp = importer.preview(f.name, None)["mapping"]; self.assertEqual(mp["Código da marca"], "brand_code")
        r = loaders.run(f.name, None, mp, None, "Perfect Shock Data - Brands (BPROAUTO) - 03-11-2026.xlsx", True); os.remove(f.name)
        self.assertEqual((r["kind"], r["counts"]["new"], r["counts"]["unmatched"]), ("marca", 2, 1))
        from queries import q
        rows = {x["code"]: x for x in q("SELECT code,brand,product_id,perfect_code FROM brand_items")}
        self.assertEqual(rows["1BP31974AB"]["brand"], "BPROAUTO"); self.assertIsNotNone(rows["1BP31974AB"]["product_id"]); self.assertIsNone(rows["1BP99999ZZ"]["product_id"])   # left join: a linha sem PERFECT no catálogo permanece
        X = lambda n: type("X", (), {"name": n})()
        self.assertEqual(loaders._brand_of(X("Shock Data - Brands (MOTORCRAFT) - 03-11-2026.xlsx")), "MOTORCRAFT"); self.assertIsNone(loaders._brand_of(X("qualquer.xlsx")))

class LadoPorTexto(unittest.TestCase):
    def test_termos_de_lado(self):
        import database as db
        casos = {"AMORTECEDOR DIANT. LD/LE": "ambos", "amortecedor tras. ld": "direito", "Lado Esquerdo": "esquerdo", "LADO DIREITO": "direito", "Traseiro Direito": "direito",
                 "Direito / Esquerdo": "ambos", "FOCUS LEVE": None, "CLD 3": None}
        for t, esp in casos.items(): self.assertEqual(db.side_from_text(t), esp, t)


class BuscaReversa(_TmpDB):
    def test_codigo_do_concorrente_vira_codigo_perfect(self):
        import queries, orders
        self.db.init_db()
        self.sql("INSERT INTO products(perfect_code,description,catalog_position) VALUES(?,?,?)", [("AMD0122", "AMORTECEDOR", 1), ("AMD0150", "AMORTECEDOR", 2)])
        self.sql("INSERT INTO codes(product_id,code,normalized_code,code_type,brand) VALUES(1,'16.470','16.470','concorrente','MONROE')")
        self.assertEqual(queries.perfect_codes("16-470"), ["AMD0122"]); self.assertEqual(queries.perfect_codes("16470"), ["AMD0122"]); self.assertEqual(queries.perfect_codes("99"), [])
        import data_pipeline as dp
        self.sql("INSERT INTO ds_compras(pedido,code,description,qty_ordered,qty_pending,order_date,due_date,status,ex_code) VALUES(?,?,?,?,?,?,?,?,?)",
                 [("P1", "MP-AMD0122", "AMORTECEDOR", 10, 10, "2026-01-01", "2026-07-01", "ABERTO", "EX0002116"), ("P2", "MP-AMD0150", "AMORTECEDOR", 10, 10, "2026-01-01", "2026-07-01", "ABERTO", "EX0002116")])
        orders._CACHE.clear()
        r = orders.payload(q="16.470"); self.assertEqual([x["codigo"] for x in r["rows"]], ["MP-AMD0122"]); self.assertEqual(r["busca"]["perfect"], ["AMD0122"])
        self.assertEqual(orders.payload(q="AMD0150")["total"], 1)               # busca direta continua funcionando
        import equivalence; w, p = equivalence._where(qtxt="16.470"); self.assertIn("IN (:cv0)", w); self.assertEqual(p["cv0"], "AMD0122")


class CompraAmostra(_TmpDB):
    def test_sugestoes_so_pendente_compras_fora_do_catalogo_e_nao_recebido(self):
        import purchases
        self.db.init_db()
        self.sql("INSERT INTO products(perfect_code,description,catalog_position) VALUES(?,?,?)", [("AMD2", "AMORTECEDOR", 5)])
        ins = "INSERT INTO rd_projects(code,suggestion,status,description) VALUES(?,?,?,?)"
        self.sql(ins, [("AMD1", "DESENVOLVIMENTO", "PENDENTE COMPRAS", "AMORTECEDOR X"),      # entra
                       ("AMD2", "DESENVOLVIMENTO", "PENDENTE COMPRAS", "AMORTECEDOR X"),      # já está no catálogo → fora
                       ("AMD3", "DESENVOLVIMENTO", "ITEM RECEBIDO", "AMORTECEDOR X"),         # recebido → fora
                       ("AMD4", "REDESENVOLVIMENTO", "EM ANDAMENTO", "AMORTECEDOR X"),        # sem «Pendente compras» → fora
                       ("AMD5", "REDESENVOLVIMENTO", "PENDENTE COMPRAS", "AMORTECEDOR Y"),    # R-D não tem sugestão de amostra (etapa 19 · Q3) → fora
                       ("COX6", "DESENVOLVIMENTO", "PENDENTE COMPRAS", "COXIM DO AMORTECEDOR"),   # COX → fora
                       ("1BP31901AB", "DESENVOLVIMENTO", "PENDENTE COMPRAS", "AMORTECEDOR X"),     # montadora (BPROAUTO) → fora (etapa 18)
                       ("8550514114", "DESENVOLVIMENTO", "PENDENTE COMPRAS", "AMORTECEDOR X"),     # MOTRIO → fora
                       ("JS1/18097/AA", "DESENVOLVIMENTO", "PENDENTE COMPRAS", "AMORTECEDOR X")])  # MOTORCRAFT → fora
        r = purchases.pending({}); self.assertEqual(sorted(x["code"] for x in r["rows"]), ["AMD1"]); self.assertEqual(r["summary"]["total"], 1)

    def test_planilha_traz_melhor_preco_e_dolar(self):
        import loaders, importer
        self.db.init_db()
        f = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False); f.close()
        pd.DataFrame({"CÓDIGO ENVIO": ["D-AMD1"], "PERFECT": ["AMD1"], "N° SC": ["7626"], "APLICAÇÃO": ["FIAT - TITANO - DIANT. LD"], "CÓDIGO AMOSTRA": ["9873474480"], "PREÇO 1": [1875.06],
                      "LINK 1 / CONTATO": ["+55 11 91846-3397"], "SC ABERTA": ["SIM"], "CHEGOU": ["SIM"], "PROJETO FINALIZADO": ["NÃO"], "PROJETO APROVADO": ["NÃO"], "ENVIAR": ["NÃO"],
                      "FORNECEDOR": ["EWIN"], "MELHOR PREÇO": [1875.06], "PREÇO DOLAR": [365.51]}).to_excel(f.name, index=False)
        mp = importer.preview(f.name, None)["mapping"]; self.assertEqual((mp["MELHOR PREÇO"], mp["PREÇO DOLAR"]), ("best_price", "price_usd"))
        r = loaders.run(f.name, None, mp, None, "Compra_de_amostra.xlsx", True); os.remove(f.name)
        from queries import samples
        s = samples({})["rows"][0]; self.assertEqual((s["stage"], s["best_price"], s["price_usd"], s["supplier"]), ("chegou", 1875.06, 365.51, "EWIN"))
        self.assertEqual(samples({})["totals"]["usd"], 365.51)


class CurtidasDesRd(_TmpDB):
    """Etapa 16 · B: lista de DES/R-D com os curtidos primeiro (desempate: status mais avançado) e filtro Curtiu."""
    def setUp(self):
        super().setUp(); self.db.init_db()
        ins = "INSERT INTO rd_projects(code,suggestion,status,description,curtiu,nao_curtiu,line) VALUES(?,?,?,?,?,?,'AMORTECEDOR')"
        D = "DESENVOLVIMENTO"
        self.sql(ins, [("AMD1", D, "EM COTAÇÃO", "AMORTECEDOR", 0, 0), ("AMD2", D, "ITEM RECEBIDO", "AMORTECEDOR", 1, 0), ("AMD3", D, "EM COTAÇÃO", "AMORTECEDOR", 1, 0),
                       ("AMD4", D, "PEDIDO CONFIRMADO", "AMORTECEDOR", 2, 0), ("AMD5", D, "ITEM RECEBIDO", "AMORTECEDOR", None, 1),
                       ("AMD3", D, "FINALIZANDO CIT", "AMORTECEDOR", 0, 0)])          # 2ª aplicação do AMD3: o item fica com curtiu 1 e status FINALIZANDO CIT
    def codes(self, **f):
        import rd; return [r["code"] for r in rd.items("DESENVOLVIMENTO", f)["rows"]]
    def test_curtidos_primeiro_e_desempate_pelo_status(self):
        self.assertEqual(self.codes(), ["AMD4", "AMD2", "AMD3", "AMD5", "AMD1"])      # 2 curtidas; 1 curtida (recebido > finalizando CIT); sem curtida (recebido > cotação)
        self.assertEqual(self.codes(ordem="codigo"), ["AMD1", "AMD2", "AMD3", "AMD4", "AMD5"])
        self.assertEqual(self.codes(ordem="status")[:2], ["AMD2", "AMD5"])
    def test_filtro_curtiu(self):
        self.assertEqual(self.codes(curtiu="sim"), ["AMD4", "AMD2", "AMD3"])
        self.assertEqual(self.codes(curtiu="sem"), ["AMD5", "AMD1"])
        self.assertEqual(self.codes(curtiu="nao"), ["AMD5"])
    def test_contadores(self):
        import rd; fc = rd.facets("DESENVOLVIMENTO")
        self.assertEqual((fc["curtidos"], fc["nao_curtidos"], fc["total"]), (3, 1, 5))


class TipoPedido(_TmpDB):
    def test_amostras_na_lista_sem_afetar_resumo(self):
        import orders
        self.db.init_db()
        self.sql("INSERT INTO ds_compras(pedido,code,description,qty_ordered,qty_pending,order_date,due_date,status,ex_code) VALUES(?,?,?,?,?,?,?,?,?)",
                 [("P1", "MP-AMD1", "AMORTECEDOR", 10, 10, "2026-01-01", "2026-07-01", "ABERTO", "EX0002116")])
        self.sql("INSERT INTO sample_orders(perfect_code,sc_number,supplier,stage) VALUES(?,?,?,?)", [("AMD0170", "7626", "EWIN", "sc_aberta"), ("AMD0171", "7626", "EWIN", "aprovado")])
        orders._CACHE.clear()
        c = orders.payload(); a = orders.payload(tipo="amostra"); t = orders.payload(tipo="todos")
        self.assertEqual((c["total"], a["total"], t["total"]), (1, 2, 3)); self.assertEqual({r["TIPO_PEDIDO"] for r in t["rows"]}, {"Compra", "Amostra"})
        self.assertEqual(c["summary"], a["summary"]); self.assertEqual(c["summary"], t["summary"])           # resumo/KPIs são só das compras do servidor
        self.assertEqual(c["columns"], orders.COLS); self.assertEqual(orders.payload(tipo="amostra", q="AMD0170")["total"], 1)
        self.assertEqual(orders.payload(tipo="xyz")["tipo"], "compra")
