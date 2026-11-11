"""Metas anuais (editáveis) e validações.

Regras de negócio (definidas pelo usuário):
  • REDESENVOLVIMENTO (meta 150 em 2026): conta quando o item vai de «PENDENTE CONFIRMAÇÃO» a «ITEM RECEBIDO» no ano E tem a validação do usuário ITALOC (USER APROV / USER_VALID).
  • DESENVOLVIMENTO   (meta 125 em 2026): conta o item cujo status chegou a «ITEM RECEBIDO» dentro do ano (ano da data da mudança de status).
  • Só itens com descrição «Amortecedor» (rules.py). Contagem por CÓDIGO DISTINTO por ano.
O servidor só guarda o status atual: a data vem das transições gravadas pelo data_pipeline (marco zero = 1ª sincronização) ou da coluna de data de status, se a view tiver.
Para o que já aconteceu antes do rastreio, a meta tem um «já realizado antes do rastreio» editável na tela.
"""
import datetime
import database as db
import kinds, rules
from queries import q, q1

DEFAULT_TARGETS = {kinds.DES: 125, kinds.RD: 150}
PEDIDO = "PEDIDO CONFIRMADO"; RECEBIDO = "ITEM RECEBIDO"; PEND_CONF = "PENDENTE CONFIRMAÇÃO"

SCHEMA = """
CREATE TABLE IF NOT EXISTS goals(year INTEGER NOT NULL, kind TEXT NOT NULL, target INTEGER NOT NULL, prior_done INTEGER NOT NULL DEFAULT 0, note TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(year, kind));
CREATE TABLE IF NOT EXISTS validations(id INTEGER PRIMARY KEY, code TEXT NOT NULL, kind TEXT NOT NULL, sent_at TEXT NOT NULL, by_user TEXT, note TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS ix_val_code ON validations(code, kind);
"""

def ensure():
    import data_pipeline; data_pipeline.Store()      # garante as tabelas dev_* (eventos/estado) no mesmo banco
    c = db.conn()
    try: c.executescript(SCHEMA); c.commit()
    finally: c.close()

def _year(y): return int(y) if str(y or "").isdigit() else datetime.date.today().year

def get_goals(year=None):
    """Metas do ano (cria com os valores padrão se ainda não existirem)."""
    ensure(); year = _year(year); c = db.conn()
    try:
        for k, t in DEFAULT_TARGETS.items(): c.execute("INSERT OR IGNORE INTO goals(year,kind,target) VALUES(?,?,?)", (year, k, t))
        c.commit()
    finally: c.close()
    return {r["kind"]: dict(r) for r in q("SELECT * FROM goals WHERE year=?", (year,))}

def set_goal(year, kind, target, prior_done=None, note=None):
    kind = kinds.normalize_kind(kind)
    if not kind: raise ValueError("Tipo inválido.")
    try: target = int(target)
    except (TypeError, ValueError): raise ValueError("Meta deve ser um número inteiro.")
    if target < 0: raise ValueError("Meta não pode ser negativa.")
    year = _year(year); get_goals(year); c = db.conn()
    try:
        c.execute("UPDATE goals SET target=?, prior_done=coalesce(?,prior_done), note=coalesce(?,note), updated_at=CURRENT_TIMESTAMP WHERE year=? AND kind=?", (target, None if prior_done in (None, "") else max(int(prior_done), 0), note, year, kind)); c.commit()
    finally: c.close()

def _meta(kind):
    """Por código: é «Amortecedor»? validado pelo usuário (ITALOC)? data de status vinda do servidor (se a view tiver essa coluna)?"""
    import json
    out = {}; vu = rules.valid_user()
    for r in q(f"SELECT code, extra, description FROM rd_projects WHERE suggestion=? AND {rules.desc_sql('description')}", (kind,)):
        m = out.setdefault(r["code"], {"validated": False, "status_date": None, "valid_by": None, "valid_at": None})
        try: ex = json.loads(r["extra"]) if r["extra"] else {}
        except ValueError: ex = {}
        u = ex.get("USER APROV")
        if rules.is_valid_user(u, vu): m["validated"] = True; m["valid_by"] = u.strip().upper(); m["valid_at"] = m["valid_at"] or ex.get("DATA APROV")
        d = ex.get("DATA STATUS")
        if isinstance(d, str) and len(d) >= 10 and (not m["status_date"] or d[:10] > m["status_date"]): m["status_date"] = d[:10]
    return out

def _events(year):
    """Itens que chegaram a ITEM RECEBIDO em `year`, por tipo. A data vem da transição observada na sincronização diária; se o item já estava
    recebido no marco zero, usa a coluna de data de status do servidor (DATA STATUS), quando existir.
    {(código, tipo): {'code','kind','recebido': 'AAAA-MM-DD'|None,'origem': 'transicao'|'coluna','pend_to_rec': data|None}}"""
    y0, y1 = f"{year}-01-01", f"{year + 1}-01-01"; out = {}
    for r in q("SELECT code, kind, from_value, substr(at,1,10) d FROM dev_status_events WHERE field='status' AND to_value=? AND at>=? AND at<? ORDER BY at", (RECEBIDO, y0, y1)):
        e = out.setdefault((r["code"], r["kind"]), {"code": r["code"], "kind": r["kind"], "recebido": r["d"], "origem": "transicao", "pend_to_rec": None})
        if r["from_value"] == PEND_CONF and not e["pend_to_rec"]: e["pend_to_rec"] = r["d"]
    cur = {(r["code"], r["kind"] or None) for r in q("SELECT code,kind FROM dev_item_state WHERE status=? AND present=1", (RECEBIDO,))}
    for kind in (kinds.DES, kinds.RD):
        for code, m in _meta(kind).items():
            d = m["status_date"]
            if d and d.startswith(str(year)) and (code, kind) in cur and (code, kind) not in out:
                out[(code, kind)] = {"code": code, "kind": kind, "recebido": d, "origem": "coluna", "pend_to_rec": None}
    return out

def progress(year=None):
    """Andamento das duas metas + evolução mensal (alimenta os velocímetros do dashboard). Duas bases de contagem (rules.goal_basis, editável na tela):
    «validacao» (padrão) → validações do usuário ITALOC (USER_VALID) em itens de LINHA «Amortecedor», por SUGESTAO DES / R-D, no ano da DATA_APROVACAO (metas.py).
    «recebido»          → REDESENVOLVIMENTO: PENDENTE CONFIRMAÇÃO → ITEM RECEBIDO no ano e validado.
    DESENVOLVIMENTO é sempre: ITEM RECEBIDO no ano E validado por USER_VALID (nas duas bases). Contagem por código distinto."""
    import metas
    year = _year(year); g = get_goals(year); ev = _events(year); basis = rules.goal_basis(); vc = metas.dashboard(year)
    out = {"year": year, "basis": basis, "goals": {}, "months": {}, "rules": rules_text(), "validacoes": vc}
    months = lambda: {f"{year}-{m:02d}": 0 for m in range(1, 13)}
    for kind in (kinds.DES, kinds.RD):
        meta = _meta(kind); items = [e for e in ev.values() if e["kind"] == kind and e["code"] in meta]; counted = {}; evo = months(); k2 = kind
        if kind == kinds.RD:
            for e in items:
                if e["pend_to_rec"] and meta[e["code"]]["validated"]: counted[e["code"]] = e["pend_to_rec"]
            parts = {"recebidos_validados": len(counted), "recebidos_sem_validacao": sum(1 for e in items if e["pend_to_rec"] and not meta[e["code"]]["validated"])}
        else:
            for e in items:        # DESENVOLVIMENTO: só item que chegou a ITEM RECEBIDO neste ano E foi validado pelo usuário (USER_VALID)
                if meta[e["code"]]["validated"]: counted[e["code"]] = e["recebido"]
            parts = {"recebidos_validados": len(counted), "recebidos_sem_validacao": sum(1 for e in items if not meta[e["code"]]["validated"]), "por_coluna_de_data": sum(1 for e in items if e["origem"] == "coluna")}
        for d in counted.values(): evo[d[:7]] += 1
        rec_series = [{"month": m, "n": n} for m, n in evo.items()]
        if basis == "validacao" and kind != kinds.DES:
            n_track = vc[k2]; val_evo = {m: (vc["por_mes"].get(m) or {}).get(k2, 0) for m in months()}; series = [{"month": m, "n": n} for m, n in val_evo.items()]
            parts = {"validacoes": n_track, "validacoes_sem_data": vc["sem_data"], **parts}
        else: n_track = len(counted); series = rec_series
        goal = g[kind]; done = n_track + goal["prior_done"]; pct = round(100 * done / goal["target"], 1) if goal["target"] else None
        out["goals"][kind] = {"kind": kind, "label": kinds.LABEL[kind], "target": goal["target"], "prior_done": goal["prior_done"], "tracked": n_track, "done": done, "pct": pct, "missing": max(goal["target"] - done, 0), "reached": bool(goal["target"]) and done >= goal["target"],
                              "parts": parts, "series": {"main": series, "ITEM RECEBIDO": rec_series}, "note": goal["note"]}
    return out

def rules_text():
    a = f"Somente LINHA/descrição «{rules.only_desc().title()}»."; u = rules.valid_user()
    des = f"Conta só o item DESENVOLVIMENTO que chegou a ITEM RECEBIDO dentro do ano (data da mudança de status) E foi validado pelo usuário {u} (USER_VALID). {a}"
    if rules.goal_basis() == "validacao":
        return {kinds.DES: des, kinds.RD: f"Conta os itens de SUGESTÃO «R-D» validados pelo usuário {u} (USER_VALID) no ano da data de aprovação. {a}"}
    return {kinds.DES: des, kinds.RD: f"Conta o item que passou de PENDENTE CONFIRMAÇÃO para ITEM RECEBIDO no ano e que tem a validação do usuário {u}. {a}"}

def tracking_info():
    """Desde quando a base rastreia transições (marco zero) — a tela avisa que o histórico anterior não existe."""
    r = q1("SELECT MIN(finished_at) a, COUNT(*) n FROM dev_sync_runs WHERE status='ok'")
    return {"since": (r["a"] or "")[:10] or None, "runs": r["n"]}

# ---- validações (R-D: «enviei a validação, aguardando o item ser recebido») ----
def pending_validations(limit=200):
    """Itens de REDESENVOLVIMENTO em PENDENTE CONFIRMAÇÃO: são os que viram meta quando passarem a ITEM RECEBIDO."""
    ensure()
    rows = q("""SELECT s.code, s.kind, s.status, s.updated_at,
                (SELECT MAX(v.sent_at) FROM validations v WHERE v.code=s.code AND v.kind=s.kind) sent_at,
                (SELECT description FROM rd_projects r WHERE r.code=s.code AND r.suggestion=s.kind LIMIT 1) description
                FROM dev_item_state s WHERE s.kind=? AND s.status=? AND s.present=1 AND s.code IN (SELECT code FROM rd_projects WHERE suggestion=s.kind AND """ + rules.desc_sql("description") + """) ORDER BY s.code LIMIT ?""", (kinds.RD, PEND_CONF, int(limit)))
    meta = _meta(kinds.RD)
    for r in rows: r["validated"] = bool(meta.get(r["code"], {}).get("validated"))
    return {"rows": rows, "total": len(rows), "sent": sum(1 for r in rows if r["sent_at"])}

def send_validation(code, kind, by_user=None, note=None, sent_at=None):
    ensure(); kind = kinds.normalize_kind(kind)
    if not kind or not code: raise ValueError("Informe código e tipo.")
    if not q1("SELECT 1 FROM rd_projects WHERE code=? AND suggestion=?", (code, kind)): raise ValueError("Item não encontrado.")
    c = db.conn()
    try:
        cur = c.execute("INSERT INTO validations(code,kind,sent_at,by_user,note) VALUES(?,?,?,?,?)", (code, kind, sent_at or datetime.date.today().isoformat(), by_user, note)); c.commit(); return cur.lastrowid
    finally: c.close()

def undo_validation(vid):
    ensure(); c = db.conn()
    try: c.execute("DELETE FROM validations WHERE id=?", (int(vid),)); c.commit()
    finally: c.close()

def validations_of(code, kind):
    ensure(); return q("SELECT id,sent_at,by_user,note FROM validations WHERE code=? AND kind=? ORDER BY id DESC", (code, kinds.normalize_kind(kind) or kind))

def events_list(year=None, kind=None, limit=80):
    """Itens que chegaram a ITEM RECEBIDO no ano (mais recentes primeiro), já indicando se CONTAM pela regra de negócio e por quê."""
    ensure(); year = _year(year); k = kinds.normalize_kind(kind) if kind else None; ev = _events(year); rows = []
    for kd in ((k,) if k else (kinds.DES, kinds.RD)):
        meta = _meta(kd)
        for e in ev.values():
            if e["kind"] != kd or e["code"] not in meta: continue
            m = meta[e["code"]]
            if kd == kinds.RD: counts = bool(e["pend_to_rec"]) and m["validated"]; why = None if counts else ("sem validação do usuário " + rules.valid_user() if not m["validated"] else "não veio de PENDENTE CONFIRMAÇÃO")
            else: counts = m["validated"]; why = None if counts else "sem validação do usuário " + rules.valid_user()      # mesma regra de progress(): DES só conta se validado
            rows.append({"code": e["code"], "kind": kd, "from_value": PEND_CONF if e["pend_to_rec"] else None, "to_value": RECEBIDO, "at": e["recebido"], "origin": e["origem"], "counts": counts, "why_not": why, "validated": m["validated"]})
    rows.sort(key=lambda r: r["at"] or "", reverse=True)
    return {"year": year, "rows": rows[:int(limit)]}
