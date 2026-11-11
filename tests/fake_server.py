"""Servidor SQL de mentira (SQLite) para testar o pipeline sem rede: imita DESENVOLVIMENTO_PRODUTOS, PEDIDOS_COMPRA_DETALHADO, PEDIDOS_VENDA_DETALHADO e EST DISP.
Os dados de desenvolvimento vêm do próprio banco do app (rd_projects), com rótulos propositalmente SUJOS (des, R-D, rd, espaços) para provar a normalização."""
import os, sys, json, random, sqlite3, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEV_COLS = ["CÓDIGO", "SUGESTÃO", "STATUS", "SUB STATUS DESENHO", "SUB STATUS VALIDAÇÃO", "SUB STATUS PROJETO / INVOICE", "SUB STATUS INMETRO", "CURTIU", "NÃO CURTIU", "FORNECEDOR", "MARCA", "MONTADORA", "VEICULO", "APLICAÇÃO", "DESCRIÇÃO",
            "ANO INICIAL", "ANO FINAL", "AMOSTRA COMPRADA", "AMOSTRA ENVIADA", "OEM", "COFAP", "MONROE", "NAKATA", "KAYABA", "IPI", "USER APROV", "PEDIDO CONFIRMADO"]

def _dirty(kind, rnd):
    if kind == "DESENVOLVIMENTO": return rnd.choice(["DES", "des", "DES ", "Desenvolvimento", "DESENVOLVIMENTO", " des"])
    return rnd.choice(["R-D", "r-d", "RD", "R-D ", "Redesenvolvimento", "REDESENVOLVIMENTO", " rd"])

def build(path, app_db, seed=7):
    rnd = random.Random(seed)
    if os.path.exists(path): os.remove(path)
    a = sqlite3.connect(app_db); a.row_factory = sqlite3.Row; c = sqlite3.connect(path)
    c.execute('CREATE TABLE "DESENVOLVIMENTO_PRODUTOS" (' + ",".join(f'"{x}"' for x in DEV_COLS) + ")")
    rows = []
    for r in a.execute("SELECT * FROM rd_projects ORDER BY id"):
        ex = json.loads(r["extra"]) if r["extra"] else {}
        rows.append((r["code"], _dirty(r["suggestion"], rnd), (r["status"] or "").lower() if rnd.random() < .1 else r["status"], r["drawing_substatus"], r["validation_substatus"], r["project_substatus"], r["inmetro_substatus"], r["curtiu"] if r["curtiu"] is not None else rnd.choice([0, 0, 1, 2]), r["nao_curtiu"] if r["nao_curtiu"] is not None else rnd.choice([0, 0, 0, 1]),
                     r["supplier"], r["brand"], r["make"], r["vehicle"], r["application_text"], r["description"], r["year_from"], r["year_to"], r["sample_bought"], r["sample_sent"], ex.get("OEM"), ex.get("COFAP"), ex.get("MONROE"), ex.get("NAKATA"), ex.get("KAYABA"), ex.get("IPI"), ex.get("USER APROV"), ex.get("PEDIDO CONFIRMADO")))
    c.executemany(f'INSERT INTO "DESENVOLVIMENTO_PRODUTOS" VALUES ({",".join("?" * len(DEV_COLS))})', rows)
    codes = [x[0] for x in a.execute("SELECT perfect_code FROM products ORDER BY catalog_position LIMIT 400")]; desc = {x[0]: x[1] for x in a.execute("SELECT perfect_code,description FROM products")}
    # compras (ZS / E-WIN / XGM) -------------------------------------------------
    c.execute('CREATE TABLE "PEDIDOS_COMPRA_DETALHADO" ("PEDIDO","FORNECEDOR","CODIGO","DESCRICAO","QTDE","QTDE_RECEBIDA","SALDO","PRECO_UNITARIO","VALOR_TOTAL","DATA_PEDIDO","PREVISAO_ENTREGA")')
    sup = ["EX0002116 - ZS ZHEJIANG", "EX0002110 - E-WIN", "EX0008042 - XGM"]; today = datetime.date.today(); pr = []
    for i in range(90):
        code = rnd.choice(codes); q = rnd.choice([100, 200, 300, 500, 1000]); got = rnd.choice([0, 0, q // 2, q, q]); d0 = today - datetime.timedelta(days=rnd.randint(5, 330)); due = d0 + datetime.timedelta(days=rnd.randint(30, 120)); u = round(rnd.uniform(8, 60), 2)
        pr.append((f"PC{26000 + i // 3}", rnd.choice(sup), code, desc.get(code), q, got, q - got, u, round(u * q, 2), d0.isoformat(), due.isoformat()))
    c.executemany('INSERT INTO "PEDIDOS_COMPRA_DETALHADO" VALUES (?,?,?,?,?,?,?,?,?,?,?)', pr)
    # vendas ---------------------------------------------------------------------
    c.execute('CREATE TABLE "PEDIDOS_VENDA_DETALHADO" ("PEDIDO","CLIENTE","CODIGO","DESCRICAO","QTDE","PRECO_UNITARIO","VALOR_TOTAL","DATA_PEDIDO")')
    vs = []
    for i in range(1800):
        code = rnd.choice(codes[:120]); q = rnd.choice([1, 2, 4, 6, 10, 20]); u = round(rnd.uniform(60, 420), 2); d = today - datetime.timedelta(days=rnd.randint(0, 400))
        vs.append((f"PV{50000 + i}", rnd.choice(["AUTOPEÇAS ALFA", "REDE BETA", "DISTRIBUIDORA GAMA"]), code, desc.get(code), q, u, round(q * u, 2), d.isoformat()))
    c.executemany('INSERT INTO "PEDIDOS_VENDA_DETALHADO" VALUES (?,?,?,?,?,?,?,?)', vs)
    # estoque (nome COM ESPAÇO) ----------------------------------------------------
    c.execute('CREATE TABLE "EST DISP" ("CODIGO","DESCRICAO","ARMAZEM","DISPONIVEL","RESERVADO")')
    c.executemany('INSERT INTO "EST DISP" VALUES (?,?,?,?,?)', [(code, desc.get(code), rnd.choice(["01", "02"]), rnd.choice([0, 0, 12, 40, 150, 600]), rnd.choice([0, 0, 5, 20])) for code in codes[:300]])
    c.commit(); c.close(); a.close()

def mutate(path, n_rd=7, n_des=5):
    """Simula o que muda no servidor entre duas sincronizações: R-D pendente→recebido, DES cotação→pedido confirmado, DES já recebido sem pedido, item novo."""
    c = sqlite3.connect(path); c.row_factory = sqlite3.Row
    rd = [r["rowid"] for r in c.execute("SELECT rowid FROM DESENVOLVIMENTO_PRODUTOS WHERE upper(trim(SUGESTÃO)) IN ('R-D','RD','REDESENVOLVIMENTO') AND upper(STATUS)='ITEM RECEBIDO' LIMIT ?", (n_rd,))]
    ids = [r["rowid"] for r in c.execute("SELECT rowid FROM DESENVOLVIMENTO_PRODUTOS WHERE upper(trim(SUGESTÃO)) IN ('R-D','RD','REDESENVOLVIMENTO') LIMIT ?", (n_rd,))]
    c.execute("UPDATE DESENVOLVIMENTO_PRODUTOS SET STATUS='PENDENTE CONFIRMAÇÃO' WHERE rowid IN (%s)" % ",".join(map(str, ids)))   # (preparação: devem estar pendentes antes)
    c.commit(); c.close(); return ids

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2]); print("ok")
