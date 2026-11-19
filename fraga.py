"""Planilhas da Fraga (etapa 17 · Q22/Q27/Q28/Q29) — base da curva dos itens em desenvolvimento na Cobertura de concorrentes.
  • «LANÇAMENTOS aaaa.xlsx» (~75 mil veículos × ano de venda, 180 colunas): guarda só código Fraga, marca, veículo, modelo, ano de venda, início/fim de produção,
    status, classificação e a frota do ANO ATUAL (coluna «Frota<ano>»; na virada do ano passa a usar a do novo ano). Tabela `fraga_veiculos`.
  • «COFAP_AMORTECEDORES_x_FROTA.xlsx» (veículo × amortecedor COFAP/PERFECT, Frota2024): tabela `fraga_pecas` — caminho de reserva da curva
    (referência COFAP do servidor → frota dos veículos em que ela aparece).
  • As duas entram pela Atualização de dados (Verificar → Aplicar) e cada carga SUBSTITUI a anterior."""
import os, re, datetime, unicodedata
from queries import q

TABLES = ["""CREATE TABLE IF NOT EXISTS fraga_veiculos(codigo_fraga TEXT, marca TEXT, veiculo TEXT, modelo TEXT, ano_venda INTEGER, inicio TEXT, fim TEXT, status TEXT, classificacao TEXT,
             frota REAL, frota_ano INTEGER, source_file TEXT)""", "CREATE INDEX IF NOT EXISTS ix_fv_marca ON fraga_veiculos(marca, veiculo)",
          "CREATE TABLE IF NOT EXISTS fraga_pecas(codigo_fraga TEXT, ano_venda INTEGER, marca TEXT, veiculo TEXT, frota REAL, perfect TEXT, cofap TEXT, source_file TEXT, classificacao TEXT, modelo TEXT)",
          "CREATE INDEX IF NOT EXISTS ix_fp_cofap ON fraga_pecas(cofap)"]
NOVAS = {"fraga_pecas": (("classificacao", "TEXT"), ("modelo", "TEXT"))}      # etapa 18 (página COFAP: tirar Motos, mostrar o modelo) — bancos criados antes
LABEL = {"lancamentos": "Fraga · veículos e frota (LANÇAMENTOS)", "pecas": "Fraga · amortecedores COFAP × frota"}

def _canon(s): return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower())
def kind(name):
    n = _canon(re.sub(r"\.\w+$", "", os.path.basename(str(name or ""))))
    return "lancamentos" if re.match(r"lancamentos\d{4}", n) else "pecas" if n.endswith("xfrota") or "xfrota" in n else None
def is_file(name): return kind(name) is not None

def ensure(conn):
    for s in TABLES: conn.execute(s)
    for t, cols in NOVAS.items():
        have = {r[1] for r in conn.execute(f"PRAGMA table_info({t})")}
        for c, tp in cols:
            if c not in have: conn.execute(f"ALTER TABLE {t} ADD COLUMN {c} {tp}")

def _txt(v):
    if v is None: return None
    s = re.sub(r"\s+", " ", str(v)).strip(); return None if s in ("", "-", "None", "nan") else s
def _int(v):
    try: return int(float(str(v).strip()))
    except (TypeError, ValueError): return None
def _num(v):
    try: return float(str(v).replace(",", "."))
    except (TypeError, ValueError): return None
def _date(v):
    if isinstance(v, (datetime.date, datetime.datetime)): return v.strftime("%Y-%m-%d")
    s = _txt(v)
    if not s: return None
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}" if m else s[:10]

def _rows(path, want):
    """Lê só as colunas pedidas ({canon: campo}) sem montar a planilha inteira na memória (openpyxl em modo leitura)."""
    from openpyxl import load_workbook
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        it = wb.worksheets[0].iter_rows(values_only=True); head = [_canon(h) for h in next(it)]
        idx = {f: head.index(c) for c, f in want.items() if c in head}
        for r in it:
            if r and any(v is not None for v in r): yield {f: (r[i] if i < len(r) else None) for f, i in idx.items()}
    finally: wb.close()

def read_lancamentos(path, ano=None):
    ano = ano or datetime.date.today().year
    want = {"codigofraga": "codigo_fraga", "marcaveiculo": "marca", "nomeveiculo": "veiculo", "modeloveiculo": "modelo", "anovenda": "ano_venda", "inicioproducao": "inicio",
            "finalproducao": "fim", "statusproducao": "status", "classificacao": "classificacao", f"frota{ano}": "frota"}
    out = []
    for r in _rows(path, want):
        if "frota" not in r: raise ValueError(f"A planilha não tem a coluna «Frota{ano}» (frota do ano atual).")
        out.append((_txt(r.get("codigo_fraga")), (_txt(r.get("marca")) or "").upper() or None, (_txt(r.get("veiculo")) or "").upper() or None, _txt(r.get("modelo")), _int(r.get("ano_venda")),
                    _date(r.get("inicio")), _date(r.get("fim")), _txt(r.get("status")), _txt(r.get("classificacao")), _num(r.get("frota")) or 0, ano))
    return out

def read_pecas(path):
    want = {"codigofraga": "codigo_fraga", "anovenda": "ano_venda", "marca": "marca", "nomeveiculo": "veiculo", "frota2024": "frota", "amortecedorperfect": "perfect", "amortecedorcofap": "cofap",
            "classificacao": "classificacao", "modeloveiculo": "modelo"}
    out = []
    for r in _rows(path, want):
        if "cofap" not in r: raise ValueError("A planilha não tem a coluna «Amortecedor COFAP».")
        out.append((_txt(r.get("codigo_fraga")), _int(r.get("ano_venda")), (_txt(r.get("marca")) or "").upper() or None, (_txt(r.get("veiculo")) or "").upper() or None,
                    _num(r.get("frota")) or 0, (_txt(r.get("perfect")) or "").upper() or None, (_txt(r.get("cofap")) or "").upper() or None, _txt(r.get("classificacao")), _txt(r.get("modelo"))))
    return out

_CACHE = {}
def _read(path, k):
    st = os.stat(path); key = (os.path.abspath(path), st.st_size, st.st_mtime, k)
    if key not in _CACHE: _CACHE.clear(); _CACHE[key] = read_lancamentos(path) if k == "lancamentos" else read_pecas(path)
    return _CACHE[key]

def load(path, name, confirm, conn):
    """Substitui a carga anterior da mesma planilha. Na verificação a transação é desfeita por quem chamou (updater.run)."""
    k = kind(name); ensure(conn); rows = _read(path, k)
    tbl = "fraga_veiculos" if k == "lancamentos" else "fraga_pecas"
    old = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    conn.execute(f"DELETE FROM {tbl}")
    if k == "lancamentos":
        conn.executemany("INSERT INTO fraga_veiculos(codigo_fraga,marca,veiculo,modelo,ano_venda,inicio,fim,status,classificacao,frota,frota_ano,source_file) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", [(*r, name) for r in rows])
        msgs = [f"{len(rows)} linha(s) de veículo × ano de venda; frota de {rows[0][-1] if rows else '—'} ({sum(r[9] for r in rows):,.0f} veículos)".replace(",", ".")]
    else:
        conn.executemany("INSERT INTO fraga_pecas(codigo_fraga,ano_venda,marca,veiculo,frota,perfect,cofap,classificacao,modelo,source_file) VALUES(?,?,?,?,?,?,?,?,?,?)", [(*r, name) for r in rows])
        msgs = [f"{len(rows)} linha(s); {sum(1 for r in rows if r[6])} com amortecedor COFAP e {sum(1 for r in rows if r[5])} com PERFECT; {sum(1 for r in rows if r[7] == 'Motos')} de motos (fora da página COFAP)."]
    if old: msgs.append(f"Substitui a carga anterior ({old} linha(s)).")
    return {"label": LABEL[k], "rows": len(rows), "counts": {"new": len(rows) if not old else 0, "updated": len(rows) if old else 0, "present": 0}, "messages": msgs}

def available(k="lancamentos"):
    try: return bool(q(f"SELECT 1 FROM {'fraga_veiculos' if k == 'lancamentos' else 'fraga_pecas'} LIMIT 1"))
    except Exception: return False
