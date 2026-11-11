"""Consultas sobre os dados que vêm do servidor: vendas, estoque e compras por código (ficha do produto) (tabelas ds_*, preenchidas pelo data_pipeline).
Tudo é opcional: se o servidor ainda não trouxe o dataset, a função devolve {'available': False} e a tela mostra um aviso."""
import re, datetime
import database as db
from queries import q, q1

def _k(c): return re.sub(r"[^A-Z0-9]", "", (c or "").upper())
def _has(table):
    try: return q1(f"SELECT COUNT(*) n FROM {table}")["n"] > 0
    except Exception: return False

def _names():
    """{chave do código: descrição} para enriquecer as listas (catálogo + desenvolvimento)."""
    out = {_k(r["perfect_code"]): r["description"] for r in q("SELECT perfect_code,description FROM products")}
    for r in q("SELECT code,MAX(description) d FROM rd_projects GROUP BY code"): out.setdefault(_k(r["code"]), r["d"])
    return out

def _month_axis(n=12, end=None):
    end = end or datetime.date.today().replace(day=1); out = []
    y, m = end.year, end.month
    for _ in range(n): out.append(f"{y}-{m:02d}"); m -= 1; y, m = (y - 1, 12) if m == 0 else (y, m)
    return out[::-1]

# ───────────── vendas ─────────────
def sales_summary(months=12, top=10):
    if not _has("ds_vendas"): return {"available": False}
    axis = _month_axis(months); lo = axis[0] + "-01"; names = _names()
    tot = q1("SELECT COUNT(*) n, COALESCE(SUM(qty),0) q, COALESCE(SUM(total),0) v, MAX(sale_date) last FROM ds_vendas WHERE sale_date>=?", (lo,))
    by_m = {r["m"]: r for r in q("SELECT substr(sale_date,1,7) m, SUM(qty) q, SUM(total) v FROM ds_vendas WHERE sale_date>=? GROUP BY m", (lo,))}
    rows = q("SELECT code, SUM(qty) q, SUM(total) v, MAX(description) d FROM ds_vendas WHERE sale_date>=? AND code IS NOT NULL GROUP BY code ORDER BY COALESCE(SUM(total),0) DESC, SUM(qty) DESC LIMIT ?", (lo, int(top)))
    return {"available": True, "months": [{"month": m, "qty": (by_m.get(m) or {}).get("q") or 0, "value": (by_m.get(m) or {}).get("v") or 0} for m in axis],
            "total_qty": tot["q"], "total_value": tot["v"], "lines": tot["n"], "last_date": tot["last"],
            "top": [{"code": r["code"], "description": names.get(_k(r["code"])) or r["d"], "qty": r["q"], "value": r["v"]} for r in rows]}

def sales_of(code, months=12):
    if not _has("ds_vendas"): return {"available": False}
    axis = _month_axis(months); rows = q("SELECT substr(sale_date,1,7) m, SUM(qty) q, SUM(total) v FROM ds_vendas WHERE upper(replace(replace(code,'-',''),' ',''))=? AND sale_date>=? GROUP BY m", (_k(code), axis[0] + "-01")); by = {r["m"]: r for r in rows}
    return {"available": True, "months": [{"month": m, "qty": (by.get(m) or {}).get("q") or 0, "value": (by.get(m) or {}).get("v") or 0} for m in axis], "total_qty": sum(r["q"] or 0 for r in rows), "total_value": sum(r["v"] or 0 for r in rows)}

# ───────────── estoque ─────────────
def stock_of(code):
    if not _has("ds_estoque"): return {"available": False}
    rows = q("SELECT warehouse, SUM(qty) qty, SUM(reserved) reserved FROM ds_estoque WHERE upper(replace(replace(code,'-',''),' ',''))=? GROUP BY warehouse", (_k(code),))
    return {"available": True, "total": sum(r["qty"] or 0 for r in rows), "reserved": sum(r["reserved"] or 0 for r in rows), "warehouses": rows}

def stock_summary():
    if not _has("ds_estoque"): return {"available": False}
    t = q1("SELECT COUNT(DISTINCT code) n, COALESCE(SUM(qty),0) q FROM ds_estoque"); zero = q1("SELECT COUNT(*) n FROM (SELECT code FROM ds_estoque GROUP BY code HAVING COALESCE(SUM(qty),0)<=0)")["n"]
    return {"available": True, "items": t["n"], "qty": t["q"], "zero": zero}

def purchases_of(code):
    if not _has("ds_compras"): return {"available": False}
    rows = q("SELECT pedido,supplier,qty_ordered,qty_received,qty_pending,order_date,due_date FROM ds_compras WHERE upper(replace(replace(code,'-',''),' ',''))=? ORDER BY order_date DESC LIMIT 20", (_k(code),))
    return {"available": True, "rows": rows, "pending": sum(r["qty_pending"] or 0 for r in rows)}
