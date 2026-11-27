"""Update 9 · Monitoramento de IPI — aprovação do IPI dos itens em DESENVOLVIMENTO pela controladoria.

Universo: DESENVOLVIMENTO em andamento (sem ITEM RECEBIDO), famílias Amortecedor e Linha pesada, todas as marcas; um item = uma linha do servidor (ID).
Caminho do item: «Finalizando CIT» (saiu de compras) = pendente controladoria → pendente precificação (sugestão ainda não enviada) → enviado para
aprovação (e-mail confirmado) → IPI aprovado (a resposta da Mariana diz no corpo que aprovou) ou com ressalva (código citado na resposta).
O IPI do servidor é a sugestão cadastrada (pelo Douglas); a aprovação vem só do e-mail (decisão de 27/11/2026).
Sugestão pela aplicação (10,4 = leve e passeio; 2,6 = utilitário e pesado), nesta ordem: família Linha pesada · linha do catálogo · Fraga (caminhões e
ônibus) · palavras da aplicação · histórico do veículo no servidor (sem o próprio código) · 10,4 «conferir».
"""
import re, json, datetime, collections, urllib.parse
from queries import q, q1

LEVE, PESADO = 10.4, 2.6
CTRL = "FINALIZANDO CIT"
FUTUROS = ("EM COTAÇÃO", "PEDIDO CONFIRMADO")
APROVADORES = [{"chave": "mariana", "nome": "Mariana Agostinho", "email": "marianaagostinho@perfectbrasil.com.br", "papel": "para", "aprova": True},
               {"chave": "gabriel", "nome": "Gabriel Santos", "email": "gabrielsantos@perfectbrasil.com.br", "papel": "cc", "aprova": False}]
TEXTO = ("{saudacao} Mari!\nComo você está?\n\nPoderia nos auxiliar com a aprovação da sugestão de IPI dos itens da planilha em anexo?\n\n"
         "Fico à disposição caso haja qualquer dúvida.")
COLUNAS = ["ID", "CÓDIGO", "IPI", "FAMILIA", "MONTADORA", "VEICULO", "APLICAÇÃO", "MARCA", "DESCRIÇÃO", "ANO INICIAL", "ANO FINAL", "OEM", "COFAP", "MONROE", "NAKATA", "KAYABA"]
REFS = ("OEM", "COFAP", "MONROE", "NAKATA", "KAYABA")
SEM_RESPOSTA_DIAS = 7
_KW = re.compile(r"PICK.?UP|PICAPE|FURG[AÃ]O|CARGO|\bVAN\b|CAMINH[AÃ]O|CABINE|[ÔO]NIBUS|\bTRUCK\b", re.I)

SCHEMA = """
CREATE TABLE IF NOT EXISTS ipi_envios(id INTEGER PRIMARY KEY, criado_em TEXT NOT NULL, criado_por TEXT, assunto TEXT, itens INTEGER, confirmado_em TEXT, cancelado_em TEXT);
CREATE TABLE IF NOT EXISTS ipi_envio_itens(envio_id INTEGER NOT NULL REFERENCES ipi_envios(id) ON DELETE CASCADE, rd_id TEXT NOT NULL, code TEXT, ipi REAL,
  situacao TEXT NOT NULL DEFAULT 'enviado', PRIMARY KEY(envio_id, rd_id));
CREATE TABLE IF NOT EXISTS ipi_respostas(id INTEGER PRIMARY KEY, envio_id INTEGER NOT NULL REFERENCES ipi_envios(id) ON DELETE CASCADE, autor TEXT, recebido_em TEXT,
  texto TEXT, aprovou INTEGER NOT NULL DEFAULT 0, trecho TEXT, ressalvas TEXT, registrado_em TEXT, registrado_por TEXT);
"""

def ensure():
    import database as db
    with db.session() as c: c.executescript(SCHEMA)

def _agora(): return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _num(v):
    try: return round(float(str(v).replace(",", ".")), 2)
    except (TypeError, ValueError): return None


# ---------------- itens do servidor ----------------
def _linhas():
    """Linhas DES em andamento (Amortecedor e Linha pesada, todas as marcas) com ID, IPI do servidor e a linha do catálogo."""
    import rd
    out, vistos = [], set()
    for fam in ("amortecedor", "pesada"):
        w = " AND ".join(rd._univ("DESENVOLVIMENTO", {"linha": fam, "marca": "todas"}) + [rd.NAO_RECEBIDA])
        for r in q(f"""SELECT r.id rid, r.code, r.status, r.family, r.make, r.vehicle, r.application_text, r.brand, r.description, r.year_from, r.year_to, r.extra,
                       p.catalog_line FROM rd_projects r LEFT JOIN products p ON p.id=r.product_id WHERE {w}""", {"kind": "DESENVOLVIMENTO"}):
            if r["rid"] in vistos: continue
            vistos.add(r["rid"]); e = {}
            try: e = json.loads(r["extra"] or "{}")
            except ValueError: pass
            r["id"] = str(e.get("ID") or f"L{r['rid']}"); r["ipi"] = _num(e.get("IPI")); r.pop("extra"); r["code"] = (r["code"] or "").strip().upper()
            out.append(r)
    return out

def _contexto():
    """Histórico de IPI por veículo e por código (todo o DES do servidor), classificação Fraga e IPI do Protheus (BI03)."""
    hist = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))          # (montadora, veículo) → código → {ipi: n}
    for r in q("SELECT upper(trim(make)) mk, upper(trim(vehicle)) vh, upper(trim(code)) code, extra FROM rd_projects WHERE suggestion='DESENVOLVIMENTO' AND extra LIKE '%\"IPI\"%'"):
        try: v = _num(json.loads(r["extra"]).get("IPI"))
        except ValueError: v = None
        if v: hist[(r["mk"], r["vh"])][r["code"]][v] += 1
    fraga = {}
    try:
        for r in q("SELECT upper(trim(marca)) mk, upper(trim(veiculo)) vh, classificacao cl, COUNT(*) n FROM fraga_veiculos GROUP BY 1,2,3 ORDER BY n"): fraga[(r["mk"], r["vh"])] = r["cl"]
    except Exception: pass
    bi = {}
    try: bi = {r["c"]: _num(r["ipi"]) for r in q("SELECT upper(code) c, ipi FROM bi03")}
    except Exception: pass
    return {"hist": hist, "fraga": fraga, "bi03": bi}

def sugere(r, ctx):
    """(ipi sugerido, regra) pela aplicação."""
    if "PESADA" in (r.get("family") or "").upper(): return PESADO, "família Linha pesada"
    cl = (r.get("catalog_line") or "").upper()
    if "LEVE" in cl: return LEVE, "catálogo: linha leve"
    if "PICK" in cl or "UTILIT" in cl or "PESADA" in cl: return PESADO, "catálogo: " + r["catalog_line"].lower()
    vk = ((r.get("make") or "").upper().strip(), (r.get("vehicle") or "").upper().strip())
    fr = ctx["fraga"].get(vk)
    if fr in ("Caminhões", "Ônibus"): return PESADO, "Fraga: " + fr.lower()
    t = " ".join(str(r.get(k) or "") for k in ("vehicle", "application_text", "description"))
    m = _KW.search(t)
    if m and not re.search(r"EXCETO[^)]*" + re.escape(m.group(0)), t, re.I): return PESADO, f"aplicação: «{m.group(0).lower()}»"
    h = collections.Counter()
    for code, c in ctx["hist"].get(vk, {}).items():
        if code != r.get("code"): h.update(c)
    if len(h) == 1: v = next(iter(h)); n = sum(h.values()); return v, f"histórico do veículo ({n} {'item' if n == 1 else 'itens'})"
    if h: v = h.most_common(1)[0][0]; return v, "histórico do veículo, misto: " + ", ".join(f"{k:g}".replace(".", ",") + f" em {n}" for k, n in h.most_common())
    return LEVE, "padrão, conferir"


# ---------------- envios e respostas ----------------
def _situacoes():
    """{ID: {situacao, envio_id, enviado_em}} pelo envio CONFIRMADO mais recente de cada item."""
    out = {}
    for r in q("""SELECT i.rd_id, i.situacao, e.id envio_id, e.confirmado_em FROM ipi_envio_itens i JOIN ipi_envios e ON e.id=i.envio_id
                  WHERE e.confirmado_em IS NOT NULL AND e.cancelado_em IS NULL ORDER BY e.confirmado_em, e.id"""):
        out[r["rd_id"]] = {"situacao": r["situacao"], "envio_id": r["envio_id"], "enviado_em": r["confirmado_em"]}
    return out

def envio_aberto():
    """Envio preparado (planilha baixada, Gmail aberto) e ainda não confirmado nem cancelado."""
    return q1("SELECT * FROM ipi_envios WHERE confirmado_em IS NULL AND cancelado_em IS NULL ORDER BY id DESC LIMIT 1")

_APROVA = re.compile(r"\b(aprov(?:ei|ado|ada|ados|adas|amos|o)|de acordo|pode(?:m)? seguir|pode(?:m)? cadastrar|liberad[oa]s?)\b", re.I)
_NEGA = re.compile(r"\b(n[ãa]o|nao|sem|ainda n[ãa]o|reprov\w*)\W+(?:\w+\W+){0,2}$", re.I)

def detecta(texto, codigos=()):
    """Resposta da aprovadora → {aprovou, trecho, ressalvas}. Só aprova se o CORPO disser que aprovou («aprovei», «aprovado», «de acordo»…) sem negação
    logo antes; códigos do envio citados no texto ficam com ressalva. O texto citado de e-mails anteriores (linhas com «>» e o que vem depois de «Em … escreveu:») é ignorado."""
    corpo = re.split(r"\n\s*(?:Em .{5,120} escreveu:|On .{5,120} wrote:|De: |From: )", texto or "", maxsplit=1)[0]
    corpo = "\n".join(l for l in corpo.splitlines() if not l.lstrip().startswith(">"))
    trecho, aprovou = None, False
    for m in _APROVA.finditer(corpo):
        if _NEGA.search(corpo[max(0, m.start() - 40):m.start()]): continue
        a, b = max(0, corpo.rfind("\n", 0, m.start()) + 1), corpo.find("\n", m.end())
        trecho, aprovou = corpo[a:b if b > 0 else len(corpo)].strip(), True; break
    cods = {str(c).upper() for c in codigos}
    ress = sorted({c for c in re.findall(r"\b[A-Z0-9]{2,5}\d{2,}[A-Z0-9]*\b", corpo.upper()) if c in cods})
    return {"aprovou": aprovou, "trecho": trecho, "ressalvas": ress}

def registrar_resposta(envio_id, autor, recebido_em, texto, por=None):
    """Guarda a resposta e, se o corpo aprova, passa os itens do envio para «aprovado» (os citados ficam «ressalva»)."""
    import database as db
    e = q1("SELECT * FROM ipi_envios WHERE id=? AND confirmado_em IS NOT NULL", (int(envio_id),))
    if not e: raise ValueError("Envio não encontrado ou ainda não confirmado.")
    codigos = [r["code"] for r in q("SELECT code FROM ipi_envio_itens WHERE envio_id=?", (e["id"],))]
    d = detecta(texto, codigos)
    with db.session() as c:
        c.execute("INSERT INTO ipi_respostas(envio_id,autor,recebido_em,texto,aprovou,trecho,ressalvas,registrado_em,registrado_por) VALUES(?,?,?,?,?,?,?,?,?)",
                  (e["id"], autor, recebido_em, texto, int(d["aprovou"]), d["trecho"], json.dumps(d["ressalvas"]), _agora(), por))
        if d["aprovou"]:
            c.execute("UPDATE ipi_envio_itens SET situacao='aprovado' WHERE envio_id=? AND situacao<>'aprovado'", (e["id"],))
            if d["ressalvas"]:
                c.execute(f"UPDATE ipi_envio_itens SET situacao='ressalva' WHERE envio_id=? AND upper(code) IN ({','.join('?' * len(d['ressalvas']))})", (e["id"], *d["ressalvas"]))
    return d

def preparar_envio(por=None):
    """Cria (ou refaz) o envio aberto com todos os itens pendentes de precificação. Devolve {id, itens, assunto, gmail, xlsx}."""
    import database as db
    linhas = [l for l in tela({})["_todas"] if l["sit"] == "prec"]
    if not linhas: raise ValueError("Nenhum item pendente de precificação.")
    hoje = datetime.date.today(); assunto = f"Sugestão de IPI - Amortecedores - {hoje:%d/%m/%Y}"
    with db.session() as c:
        c.execute("UPDATE ipi_envios SET cancelado_em=? WHERE confirmado_em IS NULL AND cancelado_em IS NULL", (_agora(),))
        eid = c.execute("INSERT INTO ipi_envios(criado_em,criado_por,assunto,itens) VALUES(?,?,?,?)", (_agora(), por, assunto, len(linhas))).lastrowid
        c.executemany("INSERT INTO ipi_envio_itens(envio_id,rd_id,code,ipi,situacao) VALUES(?,?,?,?, 'enviado')",
                      [(eid, l["id"], l["code"], l["ipi"] if l["ipi"] is not None else l["sug"]) for l in linhas])
    return {"id": eid, "itens": len(linhas), "assunto": assunto, "gmail": gmail_url(assunto), "xlsx": f"/api/ipi/envio/{eid}.xlsx"}

def confirmar_envio(eid):
    import database as db
    with db.session() as c:
        n = c.execute("UPDATE ipi_envios SET confirmado_em=? WHERE id=? AND confirmado_em IS NULL AND cancelado_em IS NULL", (_agora(), int(eid))).rowcount
    if not n: raise ValueError("Envio não encontrado (já confirmado ou cancelado).")

def cancelar_envio(eid):
    import database as db
    with db.session() as c: c.execute("UPDATE ipi_envios SET cancelado_em=? WHERE id=? AND confirmado_em IS NULL", (_agora(), int(eid)))

def gmail_url(assunto, agora=None):
    """Nova mensagem do Gmail já preenchida (Para, Cópia, Assunto, texto); o anexo o usuário arrasta (link não anexa arquivo)."""
    h = (agora or datetime.datetime.now()).hour
    p = {"view": "cm", "fs": "1", "to": ",".join(a["email"] for a in APROVADORES if a["papel"] == "para"), "cc": ",".join(a["email"] for a in APROVADORES if a["papel"] == "cc"),
         "su": assunto, "body": TEXTO.format(saudacao="Bom dia" if h < 12 else "Boa tarde")}
    return "https://mail.google.com/mail/?" + urllib.parse.urlencode(p, quote_via=urllib.parse.quote)

def planilha(eid):
    """Anexo do e-mail no modelo IPI.xlsx: aba «AprovacaoIPI - dd-mm-aa», as 16 colunas, um item (ID) por linha. → (BytesIO, nome do arquivo)."""
    import io
    from openpyxl import Workbook
    from openpyxl.styles import Font
    e = q1("SELECT * FROM ipi_envios WHERE id=?", (int(eid),))
    if not e: raise ValueError("Envio não encontrado.")
    ids = {r["rd_id"]: r for r in q("SELECT rd_id, code, ipi FROM ipi_envio_itens WHERE envio_id=?", (e["id"],))}
    por_id = {l["id"]: l for l in _linhas()}; refs = _refs({x["code"] for x in ids.values()})
    d = datetime.datetime.strptime(e["criado_em"][:10], "%Y-%m-%d")
    wb = Workbook(); ws = wb.active; ws.title = f"AprovacaoIPI - {d:%d-%m-%y}"; ws.append(COLUNAS)
    for c in ws[1]: c.font = Font(bold=True)
    for rid, it in ids.items():
        l = por_id.get(rid, {}); rf = refs.get(it["code"], {})
        ws.append([int(rid) if str(rid).isdigit() else rid, it["code"], it["ipi"], l.get("family"), l.get("make"), l.get("vehicle"), l.get("application_text"), l.get("brand"),
                   l.get("description"), l.get("year_from"), l.get("year_to"), *[", ".join(rf.get(k, [])) or None for k in REFS]])
    for col, w in zip("ABCDEFGHIJKLMNOP", [8, 12, 6, 24, 16, 20, 28, 12, 40, 11, 11, 30, 18, 18, 18, 18]): ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"; bio = io.BytesIO(); wb.save(bio); bio.seek(0)
    return bio, f"{d:%Y%m%d} - APROVACAOIPI.xlsx"

def _refs(codes):
    out = collections.defaultdict(lambda: collections.defaultdict(list)); codes = [c for c in codes if c]
    for i in range(0, len(codes), 800):
        part = codes[i:i + 800]
        try:
            rows = q(f"SELECT upper(code) c, upper(competitor) k, reference ref FROM concorrentes WHERE upper(code) IN ({','.join('?' * len(part))}) AND upper(competitor) IN ('OEM','COFAP','MONROE','NAKATA','KAYABA')", part)
        except Exception: rows = []
        for r in rows:
            if r["ref"] and r["ref"] not in out[r["c"]][r["k"]]: out[r["c"]][r["k"]].append(r["ref"])
    return out


# ---------------- tela ----------------
def _anomalias(itens, todas):
    a = {"srv": [], "protheus": [], "misto": [], "sem_ipi": [], "fora": [], "sem_resposta": []}
    for l in todas:
        if l["status"] in (CTRL, "PEDIDO CONFIRMADO") and l["ipi"] is None: a["sem_ipi"].append(l)
        if l["ipi"] is not None and l["ipi"] not in (LEVE, PESADO): a["fora"].append(l)
    for l in itens:
        if l["ipi"] is not None and l["ipi"] != l["sug"]: a["srv"].append(l)
        if l["bi03"] is not None and l["ipi"] is not None and l["bi03"] != l["ipi"]: a["protheus"].append(l)
        if "misto" in l["regra"]: a["misto"].append(l)
    lim = (datetime.datetime.now() - datetime.timedelta(days=SEM_RESPOSTA_DIAS)).strftime("%Y-%m-%d %H:%M:%S")
    a["sem_resposta"] = q("""SELECT e.id, e.assunto, e.confirmado_em, e.itens FROM ipi_envios e WHERE e.confirmado_em IS NOT NULL AND e.cancelado_em IS NULL AND e.confirmado_em < ?
                             AND NOT EXISTS(SELECT 1 FROM ipi_respostas r WHERE r.envio_id=e.id AND r.aprovou=1)""", (lim,))
    return a

def _aprovadores():
    ult = q1("SELECT * FROM ipi_envios WHERE confirmado_em IS NOT NULL AND cancelado_em IS NULL ORDER BY confirmado_em DESC, id DESC LIMIT 1")
    resp = q("SELECT * FROM ipi_respostas WHERE envio_id=? ORDER BY id", (ult["id"],)) if ult else []
    out = []
    for a in APROVADORES:
        if not ult: out.append({**a, "estado": "nada", "texto": "nada enviado"}); continue
        aprov = next((r for r in resp if r["aprovou"] and a["nome"].split()[0].lower() in (r["autor"] or "").lower()), None)
        if aprov: out.append({**a, "estado": "aprovou", "texto": f"aprovou em {aprov['recebido_em'] or aprov['registrado_em'][:10]}"})
        else: out.append({**a, "estado": "aguardando", "texto": "aguardando" if a["papel"] == "para" else "em cópia"})
    return out

def tela(f=None):
    f = f or {}; ctx = _contexto(); sits = _situacoes(); todas = _linhas()
    for l in todas:
        l["sug"], l["regra"] = sugere(l, ctx); l["bi03"] = ctx["bi03"].get(l["code"])
        s = sits.get(l["id"]); l["sit"] = s["situacao"] if s else "prec"; l["enviado_em"] = s["enviado_em"] if s else None
    itens = [l for l in todas if l["status"] == CTRL]
    prox = [l for l in todas if l["status"] in FUTUROS]
    an = _anomalias(itens, todas)
    k = collections.Counter(l["sit"] for l in itens)
    kpi = {"controladoria": len(itens), "prec": k["prec"], "enviado": k["enviado"] + k["ressalva"], "aprovado": k["aprovado"], "ressalva": k["ressalva"],
           "leve": sum(1 for l in itens if l["sug"] == LEVE), "pesado": sum(1 for l in itens if l["sug"] == PESADO)}
    termo = (f.get("q") or "").strip().upper()
    vis = [l for l in itens if (not f.get("sit") or l["sit"] == f["sit"] or (f["sit"] == "enviado" and l["sit"] == "ressalva"))
           and (not f.get("ipi") or str(l["sug"]) == str(f["ipi"]))
           and (not termo or any(termo in str(l.get(x) or "").upper() for x in ("id", "code", "make", "vehicle", "application_text", "brand", "description")))]
    refs = _refs({l["code"] for l in vis + prox})
    for l in vis + prox: l["refs"] = {k2: (refs.get(l["code"], {}).get(k2) or [])[:3] for k2 in REFS}
    ult = q1("SELECT r.*, e.assunto FROM ipi_respostas r JOIN ipi_envios e ON e.id=r.envio_id ORDER BY r.id DESC LIMIT 1")
    if ult: ult["ressalvas"] = json.loads(ult["ressalvas"] or "[]")
    ue = q1("SELECT id, assunto, confirmado_em FROM ipi_envios WHERE confirmado_em IS NOT NULL AND cancelado_em IS NULL ORDER BY confirmado_em DESC, id DESC LIMIT 1")
    return {"kpi": kpi, "aprovadores": _aprovadores(), "ultimo_envio": ue["id"] if ue else None, "envio_info": ue, "itens": vis, "proximos": prox, "anomalias": {k2: v for k2, v in an.items()},
            "n_anomalias": sum(len(v) for v in an.values()), "envio_aberto": envio_aberto(), "resposta": ult, "_todas": itens}

def publico(f=None):
    """Para a API: sem a chave interna."""
    d = tela(f); d.pop("_todas", None); return d
