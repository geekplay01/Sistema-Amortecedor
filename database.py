"""Banco SQLite local: esquema completo e consultas do dashboard."""
import os, sqlite3
BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("PSD_DB", os.path.join(BASE, "data", "perfect_shock.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources(id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT, priority INTEGER DEFAULT 5, notes TEXT);
CREATE TABLE IF NOT EXISTS import_batches(id INTEGER PRIMARY KEY, source_id INTEGER REFERENCES sources(id), filename TEXT, sheet TEXT, category TEXT,
  imported_at TEXT DEFAULT CURRENT_TIMESTAMP, rows_new INTEGER DEFAULT 0, rows_updated INTEGER DEFAULT 0, rows_conflict INTEGER DEFAULT 0, rows_error INTEGER DEFAULT 0, status TEXT DEFAULT 'ok');
CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY, perfect_code TEXT NOT NULL UNIQUE, description TEXT, system_type TEXT CHECK(system_type IN ('oleo','gas') OR system_type IS NULL),
  features TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT);
CREATE TABLE IF NOT EXISTS codes(id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  code TEXT NOT NULL, code_type TEXT NOT NULL CHECK(code_type IN ('oem','fornecedor','concorrente')), brand TEXT, source_id INTEGER REFERENCES sources(id), batch_id INTEGER REFERENCES import_batches(id));
CREATE INDEX IF NOT EXISTS ix_codes_code ON codes(code);
CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  make TEXT, model TEXT, version TEXT, year_from INTEGER, year_to INTEGER, axle TEXT CHECK(axle IN ('dianteiro','traseiro') OR axle IS NULL),
  side TEXT CHECK(side IN ('esquerdo','direito','ambos') OR side IS NULL), source_id INTEGER REFERENCES sources(id), batch_id INTEGER REFERENCES import_batches(id));
CREATE TABLE IF NOT EXISTS dimensions(product_id INTEGER PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE, lmax_mm REAL, lmin_mm REAL, stroke_mm REAL, rod_diameter_mm REAL,
  body_length_mm REAL, tube_diameter_mm REAL, upper_mount TEXT, upper_mount_dims TEXT, lower_mount TEXT, lower_mount_dims TEXT, source_id INTEGER REFERENCES sources(id));
CREATE TABLE IF NOT EXISTS commercial(product_id INTEGER PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE, cost REAL, price REAL, weight_kg REAL, package TEXT, source_id INTEGER REFERENCES sources(id));
CREATE TABLE IF NOT EXISTS pendencies(id INTEGER PRIMARY KEY, product_id INTEGER REFERENCES products(id) ON DELETE CASCADE, kind TEXT NOT NULL, field TEXT, description TEXT,
  status TEXT DEFAULT 'aberta' CHECK(status IN ('aberta','resolvida','ignorada')), created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS equivalence_suggestions(id INTEGER PRIMARY KEY, product_a INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE, product_b INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  score REAL, confidence TEXT, criteria TEXT, differences TEXT, missing TEXT, sources TEXT, status TEXT DEFAULT 'pendente' CHECK(status IN ('pendente','aprovada','rejeitada')), updated_at TEXT);
"""

def conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH); c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON"); return c

from contextlib import contextmanager
@contextmanager
def session():
    """Conexão que faz commit (ou rollback) e FECHA no fim. `with sqlite3.connect()` sozinho não fecha: o arquivo fica preso no Windows."""
    c = conn()
    try:
        with c: yield c
    finally: c.close()

def init_db():
    with session() as c: c.executescript(SCHEMA)
    migrate()

def stats():
    import rules
    q = {
     "products": "SELECT COUNT(*) FROM products",
     "oem_codes": "SELECT COUNT(DISTINCT code) FROM codes WHERE code_type='oem'",
     "applications": "SELECT COUNT(*) FROM applications",
     "drawings": "SELECT COUNT(DISTINCT code) FROM drawing_links",
     "ship_pendente": "SELECT COUNT(*) FROM sample_shipments WHERE status='pendente_projeto'",
     # mesmo universo das telas DES/R-D (família amortecedor e, no DES, a marca padrão): o cartão bate com o atalho «Pendente compras» das telas
     **{k: f"SELECT COUNT(DISTINCT code||suggestion) FROM v_rd_flags WHERE {k}=1 AND code||'|'||suggestion IN (SELECT r.code||'|'||r.suggestion FROM rd_projects r WHERE {rules.desc_sql('r.description')}"
           f" AND (r.suggestion<>'DESENVOLVIMENTO' OR {rules.marca_sql('DESENVOLVIMENTO') or '1=1'}))" for k in ("pend_compras", "val_reprovada")},
     "imports": "SELECT COUNT(*) FROM import_batches",
     "pendencies": "SELECT COUNT(*) FROM pendencies WHERE status='aberta'",
     "duplicates": "SELECT COUNT(*) FROM (SELECT 1 FROM codes WHERE coalesce(source_id,0) NOT IN (SELECT id FROM sources WHERE name LIKE 'CrossCatalogo%') GROUP BY coalesce(normalized_code,code), code_type HAVING COUNT(DISTINCT product_id)>1)",
     # etapa 20 · Q2 / etapa 21: «em desenvolvimento» = itens (linhas do servidor, como o sistema PERFECT conta) em andamento — ainda não ITEM RECEBIDO —,
     # família AMORTECEDOR e a marca padrão do tipo: o mesmo número que abre a tela
     **{k: f"SELECT COUNT(*) FROM rd_projects r WHERE r.suggestion='{s}' AND upper(trim(coalesce(r.status,'')))<>'ITEM RECEBIDO' AND {rules.desc_sql('r.description')}"
           + (f" AND {rules.marca_sql(s)}" if rules.marca_sql(s) else "") for k, s in (("des_items", "DESENVOLVIMENTO"), ("rd_items", "REDESENVOLVIMENTO"))},
     "equivalences_pending": "SELECT COUNT(*) FROM equivalence_suggestions WHERE status='pendente'",
    }
    with session() as c: return {k: c.execute(v).fetchone()[0] for k, v in q.items()}

def quick_search(term, limit=5):
    import rd
    return rd.quick(term, limit)

# ---- Migrações aditivas (v2, v3, v4): campos e tabelas vindos da análise das bases reais ----
SCHEMA_V2 = """
CREATE TABLE IF NOT EXISTS side_pairs(right_product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE, left_product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE, source_id INTEGER REFERENCES sources(id), PRIMARY KEY(right_product_id,left_product_id));
CREATE TABLE IF NOT EXISTS product_relations(product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE, related_code TEXT NOT NULL, related_product_id INTEGER REFERENCES products(id) ON DELETE SET NULL, seq INTEGER, source_id INTEGER REFERENCES sources(id), PRIMARY KEY(product_id, related_code));
CREATE INDEX IF NOT EXISTS ix_prel_rel ON product_relations(related_product_id);
CREATE TABLE IF NOT EXISTS packaging_boxes(code TEXT PRIMARY KEY, length_mm REAL, width_mm REAL, height_mm REAL, raw_dims TEXT, source_id INTEGER REFERENCES sources(id));
CREATE TABLE IF NOT EXISTS product_components(id INTEGER PRIMARY KEY, parent_code TEXT NOT NULL, product_id INTEGER REFERENCES products(id) ON DELETE SET NULL, component_code TEXT NOT NULL, component_desc TEXT, seq INTEGER, qty REAL, loss_index REAL, date_from TEXT, date_to TEXT, source_id INTEGER REFERENCES sources(id), batch_id INTEGER REFERENCES import_batches(id));
CREATE INDEX IF NOT EXISTS ix_comp_parent ON product_components(parent_code);
CREATE TABLE IF NOT EXISTS supplier_items(id INTEGER PRIMARY KEY, supplier_name TEXT, erp_code TEXT, item_type TEXT, supplier_code TEXT, supplier_code2 TEXT, description TEXT, product_id INTEGER REFERENCES products(id) ON DELETE SET NULL, source_id INTEGER REFERENCES sources(id), batch_id INTEGER REFERENCES import_batches(id));
CREATE TABLE IF NOT EXISTS certificates(id INTEGER PRIMARY KEY, product_id INTEGER REFERENCES products(id) ON DELETE CASCADE, perfect_code_raw TEXT, inmetro_number TEXT, family TEXT, supplier TEXT, cert_description TEXT, brand TEXT, source_id INTEGER REFERENCES sources(id), batch_id INTEGER REFERENCES import_batches(id));
CREATE TABLE IF NOT EXISTS rd_projects(id INTEGER PRIMARY KEY, code TEXT NOT NULL, product_id INTEGER REFERENCES products(id) ON DELETE SET NULL, suggestion TEXT, status TEXT, drawing_substatus TEXT, validation_substatus TEXT, supplier TEXT, sample_bought TEXT, sample_sent TEXT, source_id INTEGER REFERENCES sources(id), batch_id INTEGER REFERENCES import_batches(id));
"""
NEW_COLUMNS = {
 "products": [("description_es","TEXT"),("description_en","TEXT"),("ean","TEXT"),("ncm","TEXT"),("family","TEXT"),("inmetro_number","TEXT"),("weight_kg","REAL"),("package_code","TEXT"),("package_note","TEXT"),("is_launch","TEXT")],
 "codes": [("normalized_code","TEXT")],
 "applications": [("application_text","TEXT"),("year_note","TEXT")],
}
SCHEMA_V3 = """
CREATE TABLE IF NOT EXISTS sample_orders(id INTEGER PRIMARY KEY, product_id INTEGER REFERENCES products(id) ON DELETE SET NULL, perfect_code TEXT, ship_code TEXT, sc_number TEXT, application TEXT, sample_code TEXT, supplier TEXT, month TEXT, tracking TEXT, net_weight REAL, gross_weight REAL, credit_note TEXT, stage TEXT NOT NULL DEFAULT 'cotacao', to_send INTEGER DEFAULT 0, pending_supplier INTEGER DEFAULT 0, notes TEXT, source_id INTEGER REFERENCES sources(id), created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT);
CREATE TABLE IF NOT EXISTS sample_quotes(id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES sample_orders(id) ON DELETE CASCADE, price REAL, link TEXT, chosen INTEGER DEFAULT 0);
CREATE UNIQUE INDEX IF NOT EXISTS ux_eq ON equivalence_suggestions(product_a, product_b);
"""
SCHEMA_V4 = """
CREATE TABLE IF NOT EXISTS damping_rules(id INTEGER PRIMARY KEY, table_name TEXT NOT NULL, seq INTEGER, velocity REAL NOT NULL, tolerance REAL NOT NULL, source_id INTEGER REFERENCES sources(id));
CREATE TABLE IF NOT EXISTS damping_params(key TEXT PRIMARY KEY, value REAL, note TEXT);
CREATE TABLE IF NOT EXISTS damping_tests(id INTEGER PRIMARY KEY, product_id INTEGER REFERENCES products(id) ON DELETE SET NULL, perfect_code TEXT, label TEXT, test_date TEXT, notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS damping_points(id INTEGER PRIMARY KEY, test_id INTEGER NOT NULL REFERENCES damping_tests(id) ON DELETE CASCADE, table_name TEXT, velocity REAL, tolerance REAL, drawing REAL, found REAL);
CREATE TABLE IF NOT EXISTS unlinked_rows(id INTEGER PRIMARY KEY, kind TEXT, source_id INTEGER REFERENCES sources(id), code TEXT, payload TEXT, reason TEXT);
"""
SCHEMA_V5 = """
CREATE TABLE IF NOT EXISTS drawing_files(id INTEGER PRIMARY KEY, filename TEXT NOT NULL, stored_name TEXT NOT NULL, ext TEXT, size INTEGER, sha256 TEXT, rev_num INTEGER NOT NULL DEFAULT 0, rev_label TEXT,
  rev_auto INTEGER DEFAULT 0, note TEXT, uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP, batch_id INTEGER REFERENCES import_batches(id));
CREATE TABLE IF NOT EXISTS drawing_links(file_id INTEGER NOT NULL REFERENCES drawing_files(id) ON DELETE CASCADE, code TEXT NOT NULL, PRIMARY KEY(file_id, code));
CREATE INDEX IF NOT EXISTS ix_dl_code ON drawing_links(code);
CREATE INDEX IF NOT EXISTS ix_df_sha ON drawing_files(sha256);
CREATE TABLE IF NOT EXISTS generic_rows(id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE, batch_id INTEGER REFERENCES import_batches(id), sheet TEXT, row_no INTEGER, row_hash TEXT NOT NULL, payload TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_gr_src ON generic_rows(source_id, row_hash);
"""
SCHEMA_V6 = """
CREATE TABLE IF NOT EXISTS rd_flags(code TEXT NOT NULL, suggestion TEXT NOT NULL, flag TEXT NOT NULL, value INTEGER NOT NULL, by_user TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(code, suggestion, flag));
CREATE TABLE IF NOT EXISTS brand_items(id INTEGER PRIMARY KEY, brand TEXT NOT NULL, code TEXT NOT NULL, norm_code TEXT NOT NULL, product_id INTEGER REFERENCES products(id) ON DELETE SET NULL, perfect_code TEXT, description TEXT,
  item_type TEXT, vehicle TEXT, application TEXT, years TEXT, box_code TEXT, suppliers TEXT, source_id INTEGER REFERENCES sources(id));
CREATE INDEX IF NOT EXISTS ix_bi_norm ON brand_items(brand, norm_code);
"""
# Pendências dos itens em DES / R-D: só o que o servidor indica (etapa 20 · Q3). rd_flags guarda as marcações manuais antigas, que não valem mais.
# (a view v_rd_flags é montada por statuses.view_sql() — veja migrate())
SCHEMA_V7 = """
CREATE TABLE IF NOT EXISTS supplier_ex(supplier TEXT PRIMARY KEY, ex_code TEXT NOT NULL, full_name TEXT);
INSERT OR IGNORE INTO supplier_ex(supplier,ex_code,full_name) VALUES('ZS','EX0002116','ZS'),('E-WIN','EX0002110','E-WIN'),('XGM','EX0008042','XGM');
CREATE TABLE IF NOT EXISTS sample_shipments(id INTEGER PRIMARY KEY, order_id INTEGER REFERENCES sample_orders(id) ON DELETE SET NULL, perfect_code TEXT, description TEXT, application TEXT, side TEXT,
  supplier TEXT, ex_code TEXT, sc_number TEXT, bought_at TEXT, received_at TEXT, shipped_at TEXT, status TEXT NOT NULL DEFAULT 'pendente_projeto', tracking TEXT, notes TEXT, origin TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS ix_ship_code ON sample_shipments(perfect_code);
CREATE INDEX IF NOT EXISTS ix_ship_status ON sample_shipments(status, supplier);
CREATE TABLE IF NOT EXISTS catalog_vehicles(id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE, make TEXT, model TEXT, year_from INTEGER, year_to INTEGER, raw TEXT, source_id INTEGER REFERENCES sources(id));
CREATE INDEX IF NOT EXISTS ix_cv_prod ON catalog_vehicles(product_id);
-- situação do código no ERP (ESTOQUE_ANALISE_REPOSICAO, via sincronização): bloqueado/inativo sai de DES/R-D (rules.desc_sql)
CREATE TABLE IF NOT EXISTS ds_situacao(code TEXT, active TEXT, blocked TEXT, line TEXT, extra TEXT);
CREATE INDEX IF NOT EXISTS ix_dssit_code ON ds_situacao(code);
"""
NEW_COLUMNS["import_batches"] = [("rows_read","INTEGER")]
NEW_COLUMNS["products"] += [("catalog_position","INTEGER"),("catalog_group","TEXT"),("fob","REAL"),("fob_supplier","TEXT"),("catalog_subgroup","TEXT"),("catalog_highlight","TEXT"),("catalog_photo","TEXT")]   # FOB em USD (menor preço) e fornecedor do melhor preço
# etapa 17: Linha e Híbrido/elétrico (CatalogoAMD; híbrido 'S'/'N', NULL = não informado) e o peso/EAN como estão na planilha (cat_*) — o efetivo (weight_kg/ean) vem do BI03 quando ele tem o item
NEW_COLUMNS["products"] += [("catalog_line","TEXT"),("hybrid","TEXT"),("cat_ean","TEXT"),("cat_weight_kg","REAL")]
NEW_COLUMNS["sample_orders"] = [("side","TEXT"), ("best_price","REAL"), ("price_usd","REAL")]
NEW_COLUMNS["rd_projects"] = [("make","TEXT"),("vehicle","TEXT"),("application_text","TEXT"),("year_from","INTEGER"),("year_to","INTEGER"),("description","TEXT")]

NEW_COLUMNS.setdefault("rd_projects", []).extend([("brand", "TEXT"), ("project_substatus", "TEXT"), ("inmetro_substatus", "TEXT"), ("curtiu", "INTEGER"), ("nao_curtiu", "INTEGER"), ("extra", "TEXT"), ("line", "TEXT")])
# etapa 20: os três sub status que só iam para o `extra` ganham coluna (as telas filtram por eles)
NEW_COLUMNS["rd_projects"] += [("negotiation_substatus", "TEXT"), ("sales_substatus", "TEXT"), ("cit_substatus", "TEXT")]
NEW_COLUMNS["rd_projects"] += [("family", "TEXT")]      # etapa 21: FAMILIA do servidor (amortecedor / de moto / linha pesada), o universo das telas
NEW_COLUMNS["ds_situacao"] = [("stock_total", "REAL"), ("priv_pa", "REAL"), ("priv_mp", "REAL"), ("fect_pa", "REAL"), ("fect_mp", "REAL")]      # estoque da tela Estoque (etapa 20 · Q5)
SUB_EXTRA = {"negotiation_substatus": "SUB STATUS NEGOCIAÇÃO", "sales_substatus": "SUB STATUS VENDAS", "cit_substatus": "SUB STATUS CIT", "family": "FAMILIA"}
NEW_COLUMNS["drawing_files"] = [("kind", "TEXT DEFAULT 'desenho'"), ("origin", "TEXT"), ("source", "TEXT")]

def rebuild_flags_view():
    """Recria v_rd_flags (usa o filtro de descrição vigente). Chamado ao mudar a regra na tela de Configurações."""
    import statuses
    with session() as c:
        c.execute("DROP VIEW IF EXISTS v_rd_flags"); c.execute(statuses.view_sql({r[1] for r in c.execute("PRAGMA table_info(rd_projects)")}))

def migrate():
    with session() as c:
        c.executescript(SCHEMA_V2 + SCHEMA_V3 + SCHEMA_V4 + SCHEMA_V5 + SCHEMA_V6 + SCHEMA_V7)
        for t, cols in NEW_COLUMNS.items():
            have = {r["name"] for r in c.execute(f"PRAGMA table_info({t})")}
            for n, ty in cols:
                if n not in have: c.execute(f"ALTER TABLE {t} ADD COLUMN {n} {ty}")
        import statuses   # rótulos oficiais + view dos status (11 status; valor efetivo = marcação manual ou o que o servidor indica)
        c.execute("UPDATE rd_projects SET suggestion='DESENVOLVIMENTO' WHERE suggestion='DES'"); c.execute("UPDATE rd_projects SET suggestion='REDESENVOLVIMENTO' WHERE suggestion IN ('R-D','RD')")
        c.execute("UPDATE rd_flags SET suggestion='DESENVOLVIMENTO' WHERE suggestion='DES'"); c.execute("UPDATE rd_flags SET suggestion='REDESENVOLVIMENTO' WHERE suggestion='R-D'")
        c.execute("DROP VIEW IF EXISTS v_rd_flags"); c.execute(statuses.view_sql({r[1] for r in c.execute("PRAGMA table_info(rd_projects)")}))
        for col, lab in SUB_EXTRA.items():          # banco sincronizado antes da etapa 20: copia do `extra` (uma vez; a próxima sincronização grava direto)
            c.execute(f"""UPDATE rd_projects SET {col}=json_extract(extra,'$."{lab}"') WHERE {col} IS NULL AND extra IS NOT NULL AND json_valid(extra) AND json_extract(extra,'$."{lab}"') IS NOT NULL""")
        for col in ("sample_bought", "sample_sent"):   # datas sem a hora: 2026-04-22 00:00:00 -> 2026-04-22
            c.execute(f"UPDATE rd_projects SET {col}=substr({col},1,10) WHERE length({col})>10 AND {col} GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] *'")
        import re as _re   # aplicação limpa (uma vez): sem apóstrofo inicial, espaços repetidos ou traço
        for rid, t in c.execute("SELECT id,application_text FROM rd_projects WHERE application_text IS NOT NULL AND (application_text LIKE \"'%\" OR application_text LIKE '%  %' OR application_text LIKE ' %' OR application_text LIKE '% ' OR application_text='-')").fetchall():
            n = _re.sub(r"\s+", " ", t.lstrip("'")).strip(); c.execute("UPDATE rd_projects SET application_text=? WHERE id=?", (None if n in ("-", "") else n, rid))
        c.execute("CREATE INDEX IF NOT EXISTS ix_codes_norm ON codes(normalized_code)")
        c.execute("CREATE INDEX IF NOT EXISTS ix_rd_code ON rd_projects(code)")
        import bi03, concorrentes, fraga; bi03.ensure(c); concorrentes.ensure(c); fraga.ensure(c)          # etapa 17: cadastro Protheus, concorrentes do servidor e Fraga
        # caixa «PP025M» × «PP025»: só o sufixo da marca (M Motorcraft, B BPROAUTO) difere → não é conflito (etapa 16 · D); fecha os abertos antes da regra
        for pid_, d in c.execute("SELECT id,description FROM pendencies WHERE kind='conflito' AND field='package_code' AND status='aberta'").fetchall():
            m = _re.match(r"Valor atual «(.*?)» × importado «(.*?)»", d or "")
            if m and _re.sub(r"(?<=\d)[MB]$", "", m.group(1).strip().upper()) == _re.sub(r"(?<=\d)[MB]$", "", m.group(2).strip().upper()):
                c.execute("UPDATE pendencies SET status='resolvida' WHERE id=?", (pid_,))
        # família do catálogo × Inmetro: o catálogo prevalece e a divergência vai para Anomalias (etapa 16 · D1) → fecha o conflito cujo valor importado é a família de um certificado do produto
        for pid_, prod, d in c.execute("SELECT id,product_id,description FROM pendencies WHERE kind='conflito' AND field='family' AND status='aberta'").fetchall():
            m = _re.match(r"Valor atual «(.*?)» × importado «(.*?)»", d or "")
            if m and c.execute("SELECT 1 FROM certificates WHERE product_id=? AND upper(family)=upper(?)", (prod, m.group(2).strip())).fetchone():
                c.execute("UPDATE pendencies SET status='resolvida' WHERE id=?", (pid_,))
        # amostras antigas: deduz o lado a partir do texto da aplicação (LD / LE / LD/LE)
        import re
        for oid, app in c.execute("SELECT id,application FROM sample_orders WHERE side IS NULL AND application IS NOT NULL").fetchall():
            sd = side_from_text(app)
            if sd: c.execute("UPDATE sample_orders SET side=? WHERE id=?", (sd, oid))

def side_from_text(t):
    """Lado a partir de texto livre (Descrição e/ou Aplicação), sem diferenciar maiúsculas/acentos:
    'LD/LE', 'AMBOS' ou 'Direito' + 'Esquerdo' juntos → 'ambos' · ' LD ', 'Lado Direito', 'Direito' → 'direito' · ' LE ', 'Lado Esquerdo', 'Esquerdo' → 'esquerdo' · senão None."""
    import re, unicodedata
    d = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().upper()
    if re.search(r"\bL\s*D\s*/\s*L\s*E\b|\bL\s*E\s*/\s*L\s*D\b|\bAMBOS\b", d): return "ambos"
    dr = re.search(r"\bLD\b|\bLADO\s+DIREITO\b|\bDIREIT[OA]S?\b", d); es = re.search(r"\bLE\b|\bLADO\s+ESQUERDO\b|\bESQUERD[OA]S?\b", d)
    if dr and es: return "ambos"
    return "direito" if dr else "esquerdo" if es else None
