"""Metas/validações, pedidos em aberto, curva A, garantia e FOB (funções Pandas puras + rotas)."""
import os, sys, io, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import metas, orders, curva_abc as curva, warranty, fob_merge

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

class Garantia(unittest.TestCase):
    def test_parse_so_tres_colunas(self):
        buf = io.BytesIO(); pd.DataFrame({"Código": ["amd1 ", "AMD2", None, "AMD3", "Total"], "Qtd": [2, 1, 4, 0, 7], "Valor C_ST": [1, 2, 3, 4, 10], "Defeito": ["haste travada", None, "X", "Y", None], "Cliente": list("abcde"), "Fabricante": ["ZS"] * 5}).to_excel(buf, index=False); buf.seek(0)
        r = warranty.parse(buf, "g.xlsx"); self.assertEqual(r["rows"], [{"codigo": "AMD1", "defeito": "HASTE TRAVADA", "quantidade": 2}, {"codigo": "AMD2", "defeito": "NÃO INFORMADO", "quantidade": 1}])
        self.assertEqual(r["descartadas"], {"sem_codigo": 1, "sem_quantidade": 1, "linha_de_total": 1}); self.assertEqual(sorted(r["colunas_removidas"]), ["Cliente", "Fabricante", "Valor C_ST"])
    def test_csv(self):
        r = warranty.parse(io.BytesIO("Código;Defeito;Qtd\nAMD1;VAZAMENTO;3\n".encode("cp1252")), "g.csv"); self.assertEqual(r["rows"][0], {"codigo": "AMD1", "defeito": "VAZAMENTO", "quantidade": 3})
    def test_sem_coluna(self):
        with self.assertRaises(ValueError): warranty.parse(io.BytesIO(b"a;b\n1;2\n"), "x.csv")

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
    def test_ds_garantia_alimenta_resumo(self):
        import data_pipeline as dp
        raw = pd.DataFrame({"Código": [" amd1 ", "AMD1", "AMD2", None], "Defeito Relatado": ["Vazando", "vazando", None, "x"], "Qtde": ["2", 3, 1, 5], "Cliente": list("abcd")})
        df, warn, mp = dp.normalize_dataset("garantia", raw)
        self.assertEqual(mp["code"], "Código"); self.assertEqual(mp["defect"], "Defeito Relatado"); self.assertEqual(mp["qty"], "Qtde")
        self.sql("INSERT INTO ds_garantia(code,defect,qty) VALUES(?,?,?)", list(df[["code", "defect", "qty"]].itertuples(index=False, name=None)))
        s = warranty.summary()
        self.assertEqual(s["meta"]["origem"], "servidor"); self.assertEqual(s["total"], 6); self.assertEqual(s["top_defeitos"][0]["defeito"], "VAZANDO")

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
        self.assertEqual(df.loc[df["code"] == "B1", "kind"].unique().tolist(), ["REDESENVOLVIMENTO"]); self.assertEqual(res.warnings.get("codigos_em_des_e_rd"), 1)      # B1 em DES e R-D → só R-D
        self.db.init_db(); c = self.db.conn(); c.executemany("INSERT INTO rd_projects(code,suggestion,description,line) VALUES(?,?,?,?)", list(df[["code", "kind", "description", "line"]].itertuples(index=False, name=None))); c.commit()
        ok = sorted(r[0] for r in c.execute("SELECT DISTINCT code FROM rd_projects WHERE " + rules.desc_sql())); c.close()
        self.assertEqual(ok, ["A1", "A2", "A3", "B1"])          # COX e KAD fora; «AMORTECEDOR LINHA PESADA» dentro
        c = self.db.conn(); c.execute("UPDATE rd_projects SET line=NULL"); c.commit()      # banco antigo, sem LINHA: vale a descrição, ainda sem COX/KAD
        ok2 = sorted(r[0] for r in c.execute("SELECT DISTINCT code FROM rd_projects WHERE " + rules.desc_sql())); c.close(); self.assertEqual(ok2, ["A1", "A2", "A3", "B1", "K1"])      # fallback pela descrição: K1 («KIT AMORTECEDOR») só sai quando a coluna LINHA (KAD) chega do servidor


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


class MetasEstritas(unittest.TestCase):
    def test_linha_estrita_sem_cox_kad_e_des_rd_exclusivos(self):
        import metas
        df = pd.DataFrame([("A1", "DES", "AMORTECEDOR", "italoc "), ("A2", "des", "Amortecedor Linha Pesada", "ITALOC"), ("C1", "DES", "COXIM DO AMORTECEDOR", "ITALOC"),
                           ("K1", "R-D", "AMORTECEDOR KAD", "ITALOC"), ("A3", "R-D", "AMORTECEDOR", "ITALOC"), ("A1", "R-D", "AMORTECEDOR", "ITALOC"),
                           ("A4", "DES", "AMORTECEDOR", "OUTRO")], columns=["CODIGO", "SUGESTAO", "LINHA", "USER_VALID"])
        r = metas.validation_counts(df)
        self.assertEqual((r["DES"], r["R-D"]), (1, 2))      # A2 em DES; A3 e A1 em R-D (A1 está nos dois → só R-D); COX/KAD e outro usuário ficam fora


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
                       ("AMD5", "REDESENVOLVIMENTO", "PENDENTE COMPRAS", "AMORTECEDOR Y"),    # entra
                       ("COX6", "DESENVOLVIMENTO", "PENDENTE COMPRAS", "COXIM DO AMORTECEDOR")])   # COX → fora
        r = purchases.pending({}); self.assertEqual(sorted(x["code"] for x in r["rows"]), ["AMD1", "AMD5"]); self.assertEqual(r["summary"]["total"], 2)

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
