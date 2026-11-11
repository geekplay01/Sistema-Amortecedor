"""Banco de teste SINTÉTICO e determinístico (nenhum dado real da empresa): substitui a cópia de data/perfect_shock.db nos testes de integração.
Começa limpo: sem usuários, sem sincronizações anteriores e sem dados de servidor (ds_*). Quem precisa de dados de servidor usa o fake_server.
Uso:  seed_db.build(caminho)   ·   python tests/seed_db.py saida.db"""
import os, sys, json, random, sqlite3
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MAKES = {"FIAT": ["UNO", "PALIO", "STRADA", "ARGO", "TORO"], "VW": ["GOL", "FOX", "POLO", "SAVEIRO"], "GM": ["ONIX", "PRISMA", "S10", "CELTA"],
         "FORD": ["KA", "FIESTA", "RANGER", "ECOSPORT"], "RENAULT": ["SANDERO", "LOGAN", "DUSTER"], "TOYOTA": ["COROLLA", "HILUX", "ETIOS"]}
AXLES = [("DIANT.", "dianteiro"), ("TRAS.", "traseiro")]
SIDES = [("LD/LE", "ambos"), ("LD", "direito"), ("LE", "esquerdo")]
FAMILIES = ["Estrutural", "Semi-estrutural", "Convencional", "Cartucho"]
DES_STATUS = [("ITEM RECEBIDO", 250), ("EM COTAÇÃO", 200), ("PEDIDO CONFIRMADO", 120), ("FINALIZANDO CIT", 80)]
RD_STATUS = [("ITEM RECEBIDO", 400), ("FINALIZANDO CIT", 150), ("PENDENTE PARTNUMBER FORNECEDOR", 50), ("PEDIDO CONFIRMADO", 50)]
SUBS_VALID = [None] * 6 + ["PENDENTE COMPRAS", "PENDENTE VALIDAÇÃO", "VALIDAÇÃO REPROVADA QUALIDADE", "PENDENTE DESENHO FORNECEDOR / PENDENTE COMPRAS"]
USERS = ["ITALOC", "ITALOC", "BRUNOA", "DOUGLASJ", None]


REAL_DB = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "perfect_shock.db"))

def guard(db):
    """Trava de segurança dos testes: aborta se o app estiver apontando para o banco REAL da empresa."""
    if os.path.abspath(db.DB_PATH).lower() == REAL_DB.lower():
        raise SystemExit("ABORTADO: o teste está apontando para data/perfect_shock.db (banco real). Defina PSD_DB antes de importar o app.")

def build(path, n_products=400, seed=11):
    """Cria o banco em `path` (substitui se existir). Retorna o caminho."""
    if os.path.abspath(path).lower() == REAL_DB.lower(): raise SystemExit("ABORTADO: seed_db.build nunca escreve no banco real.")
    import database as db, data_pipeline as dp
    if os.path.exists(path): os.remove(path)
    rnd = random.Random(seed)
    with mock.patch.object(db, "DB_PATH", path):
        db.init_db()
        dp.Store(path)                                                     # tabelas do pipeline (dev_*, ds_*)
        c = db.conn()
        try:
            c.execute("INSERT INTO sources(id,name,category) VALUES(1,'CatalogoAMD.xlsx','catalogo'),(2,'CrossCatalogo.xlsx','cross'),(3,'ItensMotorcraft.xlsx [MOTORCRAFT]','marca')")
            prods = []
            for i in range(n_products):
                code = f"AMD{100 + i:04d}"; ax, axn = AXLES[i % 2]; sd, sdn = SIDES[(i // 2) % 3]; mk = list(MAKES)[i % len(MAKES)]; md = MAKES[mk][i % len(MAKES[mk])]
                y0 = 1995 + i % 25; prods.append((code, f"AMORTECEDOR {ax} {sd}", "oleo" if i % 6 == 0 else "gas", f"78991525{i:05d}", "87088000", FAMILIES[i % 4], round(1 + i % 5 * .4, 2),
                                                  i + 1, "SUSPENSÃO", "AMORTECEDOR LINHA PESADA" if i % 40 == 0 else "AMORTECEDOR", "S" if i % 15 == 0 else None, mk, md, y0, axn, sdn))
            c.executemany("INSERT INTO products(perfect_code,description,system_type,ean,ncm,family,weight_kg,catalog_position,catalog_group,catalog_subgroup,is_launch) VALUES(?,?,?,?,?,?,?,?,?,?,?)", [p[:11] for p in prods])
            pid = {r[0]: r[1] for r in c.execute("SELECT perfect_code,id FROM products")}
            c.executemany("INSERT INTO applications(product_id,make,model,year_from,year_to,axle,side,source_id) VALUES(?,?,?,?,?,?,?,1)", [(pid[p[0]], p[11], p[12], p[13], p[13] + 8, p[14], p[15]) for p in prods])
            c.executemany("INSERT INTO dimensions(product_id,lmin_mm,lmax_mm,rod_diameter_mm,source_id) VALUES(?,?,?,?,1)", [(pid[p[0]], 300 + i % 90, 450 + i % 160, [12.5, 15, 20, 22][i % 4]) for i, p in enumerate(prods)])
            brands = ["MONROE", "COFAP", "NAKATA", "KAYABA"]
            c.executemany("INSERT INTO codes(product_id,code,normalized_code,code_type,brand,source_id) VALUES(?,?,?,?,?,2)",
                          [(pid[p[0]], f"{10000 + i * 7}{'G' if i % 3 else ''}", f"{10000 + i * 7}{'G' if i % 3 else ''}", "concorrente", brands[i % 4]) for i, p in enumerate(prods)] +
                          [(pid[p[0]], f"5202{i:04d}", f"5202{i:04d}", "oem", "OEM") for i, p in enumerate(prods) if i % 4 == 0])
            pairs = [(pid[prods[i][0]], pid[prods[i + 2][0]]) for i in range(0, n_products - 4, 6) if prods[i][15] == "direito" and prods[i + 2][15] == "esquerdo"]
            c.executemany("INSERT OR IGNORE INTO side_pairs(right_product_id,left_product_id,source_id) VALUES(?,?,1)", pairs)
            motor = [(f"BJ3A-18045-{chr(65 + i % 26)}{chr(65 + i // 26)}", prods[i * 3][0]) for i in range(20)]
            c.executemany("INSERT INTO brand_items(brand,code,norm_code,product_id,perfect_code,description,vehicle,source_id) VALUES('MOTORCRAFT',?,?,?,?,?,?,3)",
                          [(m, m.replace("-", ""), pid[p], p, "AMORTECEDOR", "FORD - KA") for m, p in motor])
            c.executemany("INSERT INTO brand_items(brand,code,norm_code,product_id,perfect_code,description,source_id) VALUES('BPROAUTO',?,?,?,?,'AMORTECEDOR',1)",
                          [(f"1BP{30000 + i}AB", f"1BP{30000 + i}AB", pid[prods[i][0]], prods[i][0]) for i in range(0, 60, 3)])
            # DES / R-D: códigos fora do catálogo (AMD5xxx/AMD6xxx) + alguns R-D de itens do catálogo; cada (código, tipo) com 1–2 aplicações
            rows, n = [], 0
            def add(code, kind, status, k, linked):
                mk = list(MAKES)[k % len(MAKES)]; md = MAKES[mk][k % len(MAKES[mk])]; ax, _ = AXLES[k % 2]; sd, _ = SIDES[k % 3]; y0 = 2000 + k % 24
                done = status in ("ITEM RECEBIDO", "FINALIZANDO CIT")       # validação só em item que já chegou (DES em cotação/pedido nunca vem validado)
                ex = {"USER APROV": USERS[k % len(USERS)] if done else None, "DATA APROV": f"{2024 + k % 3}-{1 + k % 12:02d}-10" if done else None, "LINHA": "AMORTECEDOR"}
                for a in range(1 + (k % 5 == 0)):
                    rows.append((code, pid.get(code) if linked else None, kind, status, "PENDENTE DESENHO FORNECEDOR" if k % 9 == 0 else None, SUBS_VALID[k % len(SUBS_VALID)] if status != "ITEM RECEBIDO" else None,
                                 ["ZS", "E-WIN", "XGM", "JYF"][k % 4], mk, md, f"{1.0 + a:.1f}", f"AMORTECEDOR {ax} {sd}", y0, y0 + 6, "PERFECT", k % 3, k % 7 == 0, json.dumps(ex), "AMORTECEDOR"))
            for kind, plan, base in (("DESENVOLVIMENTO", DES_STATUS, 5000), ("REDESENVOLVIMENTO", RD_STATUS, 6000)):
                seq = [s for _, _, s in sorted((j / qty, i, s) for i, (s, qty) in enumerate(plan) for j in range(qty))]   # status intercalados na ordem dos códigos
                for k, status in enumerate(seq):
                    if kind == "REDESENVOLVIMENTO" and k % 10 == 0 and k // 10 < n_products: add(prods[k // 10][0], kind, status, k, True)      # R-D de item que já está no catálogo
                    else: add(f"AMD{base + k:04d}", kind, status, k, False)
            rows.append(("COX0001", None, "DESENVOLVIMENTO", "EM COTAÇÃO", None, "PENDENTE COMPRAS", "ZS", "FIAT", "UNO", None, "COXIM DO AMORTECEDOR", 2010, 2015, "PERFECT", 0, 0, "{}", "COX"))   # fora do universo
            c.executemany("INSERT INTO rd_projects(code,product_id,suggestion,status,drawing_substatus,validation_substatus,supplier,make,vehicle,application_text,description,year_from,year_to,brand,curtiu,nao_curtiu,extra,line) "
                          "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
            c.executemany("INSERT INTO sample_orders(perfect_code,sc_number,supplier,stage,application) VALUES(?,?,?,?,?)",
                          [(f"AMD{5000 + i:04d}", f"{7600 + i}", ["EWIN", "ZS"][i % 2], ["sc_aberta", "chegou", "aprovado"][i % 3], "FIAT - UNO - DIANT. LD") for i in range(0, 30, 3)])
            c.commit()
        finally: c.close()
    return path


if __name__ == "__main__":
    print(build(sys.argv[1] if len(sys.argv) > 1 else "seed_teste.db"))
