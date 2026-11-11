"""Pesquisa de preços na web para a Compra de amostras.

Ordem de busca (para no primeiro que devolver anúncios):
  1. API oficial do Mercado Livre  (precisa de ML_ACCESS_TOKEN ou ML_CLIENT_ID + ML_CLIENT_SECRET no .env);
  2. página pública de resultados do Mercado Livre (alternativa quando a API recusa ou não há token);
  3. mercadocar.com.br;
  4. Google: o Google bloqueia leitura automática, então só entram LINKS de busca prontos (Google Shopping, Mercado Livre, Mercadocar).

Regras do usuário: SEMPRE produto novo e SEMPRE o link de MENOR preço — unitário ou não (par/kit/jogo entram, marcados com a etiqueta «par/kit»).
Cada consulta devolve SEMPRE o hiperlink da busca (Mercado Livre ordenado do menor preço, Google Shopping...), mesmo quando a API, a página ou a rede falham:
a busca nunca levanta erro para a tela — no pior caso a resposta traz só os links.
Só biblioteca padrão do Python (urllib): nada a instalar, e respeita o proxy da empresa (HTTP_PROXY/HTTPS_PROXY).
"""
import os, re, json, time, html, gzip, datetime, unicodedata, urllib.request, urllib.parse, urllib.error
import database as db

TTL_HOURS = 6
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# ───────────────────────── regras de filtro ─────────────────────────
_PAIR = re.compile(r"\b(par|pares|kit|kits|jogo|jogos|conjunto|conjuntos|dupla|duplas|2\s*(?:x\s*)?(?:pecas?|pcs?|pç?s?|unid\w*|un)|02\s*(?:pecas?|pcs?|un\w*)|x\s*2|2\s*x|dois|duas|4\s*(?:pecas?|pcs?|un\w*))\b", re.I)
_USED = re.compile(r"\b(usado|usados|seminovo|semi\s*novo|recondicionado|remanufaturado|retirado|sucata|defeito|avariado|vitrine)\b", re.I)

def _plain(t): return unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()
def _key(t): return re.sub(r"[^A-Z0-9]", "", _plain(t).upper())

def is_pair(title):
    """«Par de amortecedor», «Kit 2 amortecedores», «Jogo dianteiro», «2x», «02 unidades»... → True."""
    return bool(_PAIR.search(_plain(title)))

def is_used(title): return bool(_USED.search(_plain(title)))

def accept(item, code_key=None, strict=True, allow_pair=True):
    """Anúncio válido: novo, preço > 0 e (se strict) o título contém o código procurado. Par/kit só é recusado se allow_pair=False."""
    t = item.get("title") or ""
    if item.get("condition") not in (None, "new") or is_used(t) or (is_pair(t) and not allow_pair): return False
    if not item.get("price") or item["price"] <= 0: return False
    if strict and code_key and len(code_key) >= 3 and code_key not in _key(t): return False
    return True

# ───────────────────────── HTTP ─────────────────────────
def http_get(url, headers=None, timeout=None, data=None):
    """(status, texto). Nunca levanta exceção de rede: devolve (0, mensagem)."""
    timeout = timeout or float(os.environ.get("PRICE_HTTP_TIMEOUT", "12")); h = {"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9", "Accept-Encoding": "gzip, identity", **(headers or {})}
    req = urllib.request.Request(url, headers=h, data=data)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(); 
            if r.headers.get("Content-Encoding") == "gzip": raw = gzip.decompress(raw)
            return r.status, raw.decode(r.headers.get_content_charset() or "utf-8", "replace")
    except urllib.error.HTTPError as e:
        try: body = e.read().decode("utf-8", "replace")
        except Exception: body = ""
        return e.code, body
    except Exception as e: return 0, f"{e.__class__.__name__}: {e}"

# ───────────────────────── Mercado Livre (API oficial) ─────────────────────────
_TOKEN = {"v": None, "exp": 0}
def ml_token(fetch=None):
    """Token da API: ML_ACCESS_TOKEN direto ou obtido com ML_CLIENT_ID/ML_CLIENT_SECRET (client_credentials), guardado até expirar."""
    if os.environ.get("ML_ACCESS_TOKEN"): return os.environ["ML_ACCESS_TOKEN"]
    cid, sec = os.environ.get("ML_CLIENT_ID"), os.environ.get("ML_CLIENT_SECRET")
    if not (cid and sec): return None
    if _TOKEN["v"] and time.time() < _TOKEN["exp"] - 60: return _TOKEN["v"]
    body = urllib.parse.urlencode({"grant_type": "client_credentials", "client_id": cid, "client_secret": sec}).encode()
    st, txt = (fetch or http_get)("https://api.mercadolibre.com/oauth/token", {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}, None, body)
    try: d = json.loads(txt)
    except ValueError: d = {}
    if st == 200 and d.get("access_token"): _TOKEN.update(v=d["access_token"], exp=time.time() + int(d.get("expires_in", 21600))); return _TOKEN["v"]
    return None

_LEVEL = {"5_green": "Verde (excelente)", "4_light_green": "Verde claro", "3_yellow": "Amarela", "2_orange": "Laranja", "1_red": "Vermelha"}
def reputation_text(sel):
    rep = (sel or {}).get("seller_reputation") or {}; parts = []
    ps = rep.get("power_seller_status")
    if ps: parts.append("MercadoLíder " + str(ps).capitalize())
    if rep.get("level_id"): parts.append(_LEVEL.get(rep["level_id"], rep["level_id"]))
    pos = ((rep.get("transactions") or {}).get("ratings") or {}).get("positive")
    if pos is not None: parts.append(f"{round(pos * 100)}% positivas")
    return " · ".join(parts) or None

def parse_ml_api(payload):
    out = []
    for r in (payload.get("results") or []):
        sel = r.get("seller") or {}; sh = r.get("shipping") or {}
        out.append({"source": "Mercado Livre", "title": r.get("title"), "price": r.get("price"), "currency": r.get("currency_id") or "BRL", "url": r.get("permalink"), "thumbnail": (r.get("thumbnail") or "").replace("http://", "https://") or None,
                    "condition": r.get("condition"), "seller": sel.get("nickname") or (f"vendedor {sel.get('id')}" if sel.get("id") else None), "seller_id": sel.get("id"), "reputation": reputation_text(sel),
                    "free_shipping": bool(sh.get("free_shipping")), "shipping": "Frete grátis" if sh.get("free_shipping") else None, "sold": r.get("sold_quantity"), "official": bool(r.get("official_store_id"))})
    return out

def ml_api_search(query, limit=50, fetch=None):
    """API do Mercado Livre. Se o token falhar/expirar (ou a rota autenticada recusar), NÃO quebra: refaz a busca silenciosamente pela rota pública (sem Authorization)."""
    try: tok = ml_token(fetch)
    except Exception: tok = None
    site = os.environ.get("ML_SITE", "MLB")
    url = f"https://api.mercadolibre.com/sites/{site}/search?" + urllib.parse.urlencode({"q": query, "condition": "new", "limit": limit, "sort": "price_asc"})
    hdr = {"Accept": "application/json"}
    st, txt = (fetch or http_get)(url, {**hdr, **({"Authorization": f"Bearer {tok}"} if tok else {})})
    if st in (401, 403) and tok:                                 # token expirado/inválido → rota pública
        _TOKEN.update(v=None, exp=0)
        st, txt = (fetch or http_get)(url, hdr)
    if st != 200: return [], f"API do Mercado Livre respondeu {st}" + (" (sem token: configure ML_CLIENT_ID/ML_CLIENT_SECRET)" if st in (401, 403) and not tok else "")
    try: return parse_ml_api(json.loads(txt)), None
    except ValueError: return [], "resposta inválida da API"

def enrich_reputation(items, fetch=None, max_n=5):
    """Completa a reputação dos primeiros vendedores (GET /users/{id}) quando a busca não trouxe."""
    tok = ml_token(fetch); done = {}
    for it in items[:max_n]:
        sid = it.get("seller_id")
        if it.get("reputation") or not sid: continue
        if sid not in done:
            st, txt = (fetch or http_get)(f"https://api.mercadolibre.com/users/{sid}", {"Accept": "application/json", **({"Authorization": f"Bearer {tok}"} if tok else {})})
            try: done[sid] = reputation_text(json.loads(txt)) if st == 200 else None
            except ValueError: done[sid] = None
        it["reputation"] = done[sid]

# ───────────────────────── páginas públicas (alternativas) ─────────────────────────
def _money(txt):
    t = re.sub(r"[^\d,\.]", "", txt or "")
    if not t: return None
    if "," in t: t = t.replace(".", "").replace(",", ".")
    elif t.count(".") > 1 or (t.count(".") == 1 and len(t.split(".")[1]) == 3): t = t.replace(".", "")
    try: return float(t)
    except ValueError: return None

def parse_jsonld_products(page, source):
    """Produtos de blocos <script type="application/ld+json"> (Product/Offer/ItemList) — funciona em muitas lojas."""
    out = []
    def walk(o):
        if isinstance(o, list): [walk(x) for x in o]
        elif isinstance(o, dict):
            t = o.get("@type"); t = t if isinstance(t, list) else [t]
            if "Product" in t:
                off = o.get("offers"); off = off[0] if isinstance(off, list) and off else off or {}
                price = _money(str(off.get("price") or off.get("lowPrice") or "")) if isinstance(off, dict) else None
                img = o.get("image"); img = img[0] if isinstance(img, list) and img else img
                out.append({"source": source, "title": o.get("name"), "price": price, "currency": (off.get("priceCurrency") if isinstance(off, dict) else None) or "BRL", "url": o.get("url") or (off.get("url") if isinstance(off, dict) else None),
                            "thumbnail": img if isinstance(img, str) else None, "condition": "new" if "NewCondition" in str((off or {}).get("itemCondition", "NewCondition")) else "used", "seller": ((off.get("seller") or {}).get("name") if isinstance(off, dict) and isinstance(off.get("seller"), dict) else None), "reputation": None, "free_shipping": False, "shipping": None})
            for v in o.values():
                if isinstance(v, (dict, list)): walk(v)
    for m in re.finditer(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', page, re.S | re.I):
        try: walk(json.loads(html.unescape(m.group(1)).strip()))
        except ValueError: continue
    return out

def parse_ml_html(page):
    """Cartões da lista pública do Mercado Livre (layouts 'ui-search' e 'poly-card'). Melhor esforço: o site muda de HTML com frequência."""
    out = []
    blocks = re.split(r'(?=<li[^>]+class="[^"]*(?:ui-search-layout__item|ui-search-result)[^"]*")|(?=<div[^>]+class="[^"]*poly-card[^"]*")', page)
    for b in blocks:
        t = re.search(r'(?:ui-search-item__title|poly-component__title|ui-search-link__title-card)[^>]*>\s*(?:<[^>]+>)*\s*([^<]{6,200})<', b)
        u = re.search(r'href="(https?://(?:produto|www|click\d*)\.mercadolivre\.com\.br/[^"]+)"', b) or re.search(r'href="(https?://[^"]*mercadolivre\.com\.br/MLB[^"]+)"', b)
        p = re.search(r'andes-money-amount__fraction[^>]*>\s*([\d\.]+)\s*<(?:.*?andes-money-amount__cents[^>]*>\s*(\d{1,2})\s*<)?', b, re.S)
        if not (t and u and p): continue
        price = _money(p.group(1) + ("," + p.group(2) if p.group(2) else ""))
        im = re.search(r'<img[^>]+(?:data-src|src)="(https://http2\.mlstatic\.com/[^"]+)"', b); sh = "gr[aá]tis" in b.lower() and "frete" in b.lower()
        sl = re.search(r'(?:Vendido por|Por)\s*<?[^>]*>?\s*([^<]{3,60})<', b)
        out.append({"source": "Mercado Livre (página)", "title": html.unescape(t.group(1)).strip(), "price": price, "currency": "BRL", "url": html.unescape(u.group(1)), "thumbnail": im.group(1) if im else None, "condition": None,
                    "seller": html.unescape(sl.group(1)).strip() if sl else None, "reputation": None, "free_shipping": sh, "shipping": "Frete grátis" if sh else None})
    return out

def ml_page_search(query, fetch=None):
    slug = re.sub(r"\s+", "-", _plain(query).strip()); url = f"https://lista.mercadolivre.com.br/{urllib.parse.quote(slug)}_ITEM*CONDITION_2230284_NoIndex_True"
    st, txt = (fetch or http_get)(url)
    if st != 200: return [], f"página do Mercado Livre respondeu {st or txt}"
    items = parse_ml_html(txt) or [dict(x, source="Mercado Livre (página)") for x in parse_jsonld_products(txt, "Mercado Livre")]
    return items, None if items else "nenhum anúncio reconhecido na página"

def mercadocar_search(query, fetch=None):
    tpl = os.environ.get("MERCADOCAR_SEARCH_URL", "https://mercadocar.com.br/?s={q}&post_type=product")
    st, txt = (fetch or http_get)(tpl.replace("{q}", urllib.parse.quote_plus(query)))
    if st != 200: return [], f"mercadocar respondeu {st or txt}"
    items = parse_jsonld_products(txt, "Mercadocar")
    for it in items: it["condition"] = it.get("condition") if it.get("condition") == "used" else "new"
    return items, None if items else "nenhum produto reconhecido na página"

def manual_links(query):
    q = urllib.parse.quote_plus(query)
    slug = urllib.parse.quote(re.sub(r"\s+", "-", _plain(query).strip()))
    return {"google_shopping": f"https://www.google.com/search?tbm=shop&q={q}", "google": f"https://www.google.com/search?q={q}", "mercado_livre": f"https://lista.mercadolivre.com.br/{slug}_OrderId_PRICE*ASC_ITEM*CONDITION_2230284",
            "mercadocar": f"https://mercadocar.com.br/?s={q}&post_type=product"}

# ───────────────────────── orquestração ─────────────────────────
def build_query(brand=None, code=None, noun="amortecedor"):
    return " ".join(x for x in (brand if brand and brand.upper() not in ("OEM",) else None, code, noun) if x).strip()

def _cache_conn():
    c = db.conn(); c.execute("CREATE TABLE IF NOT EXISTS price_cache(key TEXT PRIMARY KEY, fetched_at TEXT, payload TEXT)"); return c

def _cache_get(key):
    c = _cache_conn()
    try:
        r = c.execute("SELECT fetched_at,payload FROM price_cache WHERE key=?", (key,)).fetchone()
        if r and (datetime.datetime.now() - datetime.datetime.strptime(r[0], "%Y-%m-%d %H:%M:%S")).total_seconds() < TTL_HOURS * 3600: return json.loads(r[1])
    finally: c.close()

def _cache_put(key, payload):
    c = _cache_conn()
    try: c.execute("INSERT OR REPLACE INTO price_cache(key,fetched_at,payload) VALUES(?,?,?)", (key, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), json.dumps(payload, ensure_ascii=False))); c.commit()
    finally: c.close()

def search_one(brand, code, limit=5, fetch=None, refresh=False, strict=True, noun="amortecedor"):
    """Uma referência (ex.: MONROE + 16470) → {query, results[], best, tried[], links, url}. Nunca levanta exceção: se tudo falhar, volta só com os links."""
    query = build_query(brand, code, noun); links = manual_links(query); key = f"{_key(query)}|{int(bool(strict))}|{limit}|any"
    base = {"query": query, "brand": brand, "code": code, "results": [], "tried": [], "links": links, "url": links["mercado_livre"], "best": None, "cached": False, "approx": False}
    try:
        if not refresh and fetch is None:
            hit = _cache_get(key)
            if hit: hit["cached"] = True; return hit
        ck = _key(code); tried = []; results = []; approx = False
        sources = (("Mercado Livre (API)", lambda: ml_api_search(query, fetch=fetch)), ("Mercado Livre (página)", lambda: ml_page_search(query, fetch=fetch)), ("Mercadocar", lambda: mercadocar_search(query, fetch=fetch)))
        raw = {}                                                 # cada fonte é consultada no máximo uma vez
        def got(name, fn):
            if name not in raw:
                try: raw[name] = fn()
                except Exception as e: raw[name] = ([], f"{e.__class__.__name__}: {e}")
            return raw[name]
        for relaxed in ((False, True) if strict else (True,)):   # 1º só anúncios que citam o código; se não houver nenhum, aceita os da busca (marcado como aproximado)
            for name, fn in sources:
                items, err = got(name, fn); good = [i for i in items if accept(i, ck, strict=not relaxed, allow_pair=True)]
                if not relaxed: tried.append({"source": name, "found": len(items), "accepted": len(good), "error": err})
                elif good: tried.append({"source": name + " (aproximado)", "found": len(items), "accepted": len(good), "error": None})
                if good: results = good; approx = relaxed; break
            if results: break
        for i in results: i["pair"] = is_pair(i.get("title"))
        results.sort(key=lambda i: (i["price"], 0 if i.get("free_shipping") else 1)); results = results[:max(1, min(int(limit), 10))]
        if results and results[0]["source"].startswith("Mercado Livre"):
            try: enrich_reputation(results, fetch)
            except Exception: pass
        out = dict(base, results=results, tried=tried, best=results[0]["price"] if results else None, approx=approx, url=(results[0]["url"] if results and results[0].get("url") else links["mercado_livre"]))
        if fetch is None and results: _cache_put(key, out)
        return out
    except Exception as e:
        return dict(base, tried=[{"source": "busca", "found": 0, "accepted": 0, "error": f"{e.__class__.__name__}: {e}"}])

def search(refs, limit=5, fetch=None, refresh=False, strict=True):
    """Referências escolhidas pelo usuário (máx. 4 por vez). Junta os anúncios, do MENOR preço para cima (unitário ou par/kit), e sempre devolve os links da consulta."""
    refs = [r for r in (refs or []) if (r.get("code") or "").strip()][:4]
    if not refs: raise ValueError("Marque ao menos uma referência para buscar.")
    parts = [search_one(r.get("brand"), r["code"].strip(), limit, fetch, refresh, strict) for r in refs]
    allr = []
    for p, r in zip(parts, refs):
        for it in p["results"]: allr.append(dict(it, ref=f"{(r.get('brand') or '').strip()} {r['code'].strip()}".strip()))
    allr.sort(key=lambda i: (i["price"], 0 if i.get("free_shipping") else 1))
    best = allr[0] if allr else None
    return {"refs": [{"query": p["query"], "found": len(p["results"]), "best": p["best"], "tried": p["tried"], "links": p["links"], "url": p["url"], "cached": p["cached"], "approx": p["approx"]} for p in parts], "results": allr[:max(1, min(int(limit), 10)) * (1 if len(parts) == 1 else 2)],
            "best": best, "status": "ok" if best else "links_only", "links": parts[0]["links"] if len(parts) == 1 else None,
            "token_configured": bool(os.environ.get("ML_ACCESS_TOKEN") or (os.environ.get("ML_CLIENT_ID") and os.environ.get("ML_CLIENT_SECRET")))}

# ───────────────────────── salvar a escolha ─────────────────────────
def save_quote(order_id, price, link, chosen=True):
    """Grava o anúncio escolhido em sample_quotes (e marca como a cotação escolhida do pedido)."""
    try: price = float(price)
    except (TypeError, ValueError): raise ValueError("Preço inválido.")
    if not link: raise ValueError("Informe o link do anúncio.")
    c = db.conn()
    try:
        if not c.execute("SELECT 1 FROM sample_orders WHERE id=?", (int(order_id),)).fetchone(): raise ValueError("Pedido de amostra não encontrado.")
        if chosen: c.execute("UPDATE sample_quotes SET chosen=0 WHERE order_id=?", (int(order_id),))
        cur = c.execute("INSERT INTO sample_quotes(order_id,price,link,chosen) VALUES(?,?,?,?)", (int(order_id), price, str(link)[:1000], int(bool(chosen)))); c.commit(); return cur.lastrowid
    finally: c.close()
