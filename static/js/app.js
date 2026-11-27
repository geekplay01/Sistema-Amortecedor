// Dashboard, busca rápida e filtro do menu.
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const fetchJSON = (u) => fetch(u).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); });
  const esc = s => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

  if ($(".cards") && $("#empty")) {
    fetchJSON("/api/stats").then(s => {
      document.querySelectorAll("[data-stat]").forEach(el => { const v = s[el.dataset.stat] ?? 0; el.textContent = Number(v).toLocaleString("pt-BR");
        const c = el.closest(".card"); if (c) c.classList.toggle("zero", !Number(v)); });          // cartão zerado fica discreto: o olho vai para o que tem número
      document.querySelectorAll(".cards.psd-atl .card.zero").forEach(c => c.parentNode.append(c));          // etapa 23 · Q5: zerados no fim da lista
      $("#empty").hidden = s.products > 0;
    }).catch(() => { const e = $("#empty"); e.hidden = false; e.textContent = "Não foi possível consultar o banco local. Verifique se o app.py está em execução."; });
  }
  // ---- menu lateral (Tailwind): grupos recolhíveis (lembra o estado), filtro, contadores e abertura no celular ----
  const navEl = $("#psd-nav"), side = $("#psd-side");
  if (navEl) {
    let st = {}; try { st = JSON.parse(localStorage.getItem("psd-menu") || "{}"); } catch (e) { }
    navEl.querySelectorAll(".gx").forEach(g => {
      const h = g.querySelector(".gx-h"); if (!h) return;                      // o grupo «Painel executivo» é fixo
      const on = g.querySelector("a[aria-current],a.is-cur"), open = on ? true : st[g.dataset.g] !== false;
      g.classList.toggle("closed", !open); h.setAttribute("aria-expanded", open);
    });
    navEl.addEventListener("click", e => {
      const h = e.target.closest(".gx-h"); if (!h) return; const g = h.parentElement, closed = g.classList.toggle("closed");
      h.setAttribute("aria-expanded", !closed); st[g.dataset.g] = !closed; try { localStorage.setItem("psd-menu", JSON.stringify(st)); } catch (er) { }
    });
    fetch("/api/menu/counts").then(r => r.json()).then(c => Object.entries(c).forEach(([k, v]) => { const b = navEl.querySelector(`[data-badge="${k}"]`); if (b && v) { b.textContent = v > 999 ? Math.round(v / 100) / 10 + "k" : v; b.hidden = false; } })).catch(() => { });
  }
  /* update 8: cada página avisa que está aberta (agora e a cada 30 s) e, ao sair, que saiu — pelo atalho, o sistema fecha quando a última aba fecha (abas.py) */
  { const id = Math.random().toString(36).slice(2) + Date.now().toString(36);
    const sinal = ev => { const b = JSON.stringify({ id, ev });
      if (ev === "saiu" && navigator.sendBeacon) { navigator.sendBeacon("/api/aba", new Blob([b], { type: "application/json" })); return; }
      fetch("/api/aba", { method: "POST", headers: { "Content-Type": "application/json" }, body: b, keepalive: true }).catch(() => { }); };
    sinal("ping"); setInterval(() => sinal("ping"), 30000);
    document.addEventListener("visibilitychange", () => { if (document.visibilityState === "visible") sinal("ping"); });
    addEventListener("pageshow", e => { if (e.persisted) sinal("ping"); });
    addEventListener("pagehide", () => sinal("saiu")); }
  /* update 8: alfinete — fixado (padrão) ou desfixado (faixa de ícones que abre ao passar o mouse); a escolha fica no navegador (base.html aplica antes de desenhar) */
  const pin = $("#psd-pin");
  if (pin && side) {
    const H = document.documentElement, marca = () => { const m = H.classList.contains("psd-mini"); pin.setAttribute("aria-pressed", String(!m));
      pin.title = m ? "Fixar o menu" : "Desfixar o menu"; pin.setAttribute("aria-label", pin.title); };
    marca();
    pin.addEventListener("click", () => { const m = !H.classList.contains("psd-mini"); H.classList.toggle("psd-mini", m); side.classList.remove("abre");
      try { localStorage.setItem("psd-menu-fixo", m ? "0" : "1"); } catch (e) { }
      marca(); pin.classList.remove("crava", "solta"); void pin.offsetWidth; pin.classList.add(m ? "solta" : "crava"); });
    side.addEventListener("focusin", e => { if (H.classList.contains("psd-mini") && e.target.matches(":focus-visible")) side.classList.add("abre"); });
    side.addEventListener("focusout", e => { if (!side.contains(e.relatedTarget)) side.classList.remove("abre"); });
    side.addEventListener("keydown", e => { if (e.key === "Escape" && side.classList.contains("abre")) { side.classList.remove("abre"); document.activeElement && document.activeElement.blur(); } });
  }
  const nav = $("#navsearch");
  if (nav) nav.addEventListener("input", () => {
    const t = nav.value.toLowerCase().trim(); side.classList.toggle("filtering", !!t);
    document.querySelectorAll("#psd-nav a[data-nav]").forEach(a => a.style.display = a.textContent.toLowerCase().includes(t) ? "" : "none");
    document.querySelectorAll("#psd-nav .gx").forEach(g => { const any = [...g.querySelectorAll("a[data-nav]")].some(a => a.style.display !== "none"); g.style.display = any ? "" : "none"; });
  });
  { const burger = $("#psd-burger"), scrim = $("#psd-scrim"), set = o => { if (!side) return; side.classList.toggle("open", o); if (scrim) scrim.hidden = !o; if (burger) burger.setAttribute("aria-expanded", o); };
    if (burger) burger.addEventListener("click", () => set(!side.classList.contains("open"))); if (scrim) scrim.addEventListener("click", () => set(false));
    document.addEventListener("keydown", e => { if (e.key === "Escape") set(false); }); if (side) side.addEventListener("click", e => { if (e.target.closest("a[data-nav]")) set(false); }); }
  const q = $("#quick"), list = $("#quick-results");
  if (q) { let timer, seq = 0, sel = -1;
    /* etapa 23: só a resposta da última busca é desenhada; ↑/↓ marcam, Enter abre a marcada, Esc fecha (como as sugestões .psd-sug) */
    const itens = () => [...list.querySelectorAll("a")];
    const marcar = i => { const a = itens(); sel = a.length ? (i + a.length) % a.length : -1; a.forEach((x, k) => x.classList.toggle("on", k === sel)); if (a[sel]) a[sel].scrollIntoView({ block: "nearest" }); };
    q.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(async () => {
      const meu = ++seq;
      if (q.value.trim().length < 2) { list.innerHTML = ""; sel = -1; return; }
      const r = await fetchJSON("/api/quick-search?q=" + encodeURIComponent(q.value));
      if (meu !== seq) return;
      sel = -1;
      list.innerHTML = r.length ? r.map(p => `<li><a href="${esc(p.url)}"><span class="tag ${p.kind === "Catálogo" ? "cat" : p.kind.replace("-", "")}">${esc(p.kind)}</span><b>${esc(p.code)}</b><span class="d">${esc(p.text || "")}</span></a></li>`).join("")
                                : '<li class="vazio">Nenhum resultado no catálogo nem em DES / R-D.</li>';
    }, 250); });
    q.addEventListener("keydown", e => {
      const a = itens();
      if (e.key === "ArrowDown" && a.length) { e.preventDefault(); marcar(sel + 1); }
      else if (e.key === "ArrowUp" && a.length) { e.preventDefault(); marcar(sel - 1); }
      else if (e.key === "Enter" && a[sel]) { e.preventDefault(); location.href = a[sel].href; }
      else if (e.key === "Escape" && list.innerHTML) { e.preventDefault(); seq++; list.innerHTML = ""; sel = -1; }
    });
  }
})();

// Vídeo do amortecedor: respeita redução de movimento e cai para a imagem estática se não carregar.
(function () {
  const v = document.getElementById("hero-video"); if (!v) return;
  const still = () => { const i = new Image(); i.src = v.dataset.fallback; i.alt = "Amortecedor PERFECT"; v.replaceWith(i); };
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return still();
  v.addEventListener("error", still, true); v.querySelector("source").addEventListener("error", still);
  v.play().catch(() => {});
})();


// ---- conector de código: clicar num código (<span class="pcx" data-code="AMD0108">) abre as telas onde ele aparece ----
(function () {
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const DEST = [["Página do item (tudo sobre o código)", "/item/"], ["Pesquisa", "/pesquisa?q="], ["Lados (par e traseiro)", "/lados?q="], ["Pedidos em aberto / lead time", "/pedidos-aberto?q="], ["Vendas (Curva A)", "/vendas?q="], ["Compra de amostras", "/amostras?q="]];
  let menu = null;
  const close = () => { if (menu) { menu.remove(); menu = null; } };
  window.psdCode = (code, label) => `<span class="pcx" data-code="${esc(code)}" title="Ver ${esc(code)} nas outras telas">${esc(label || code)}</span>`;
  document.addEventListener("click", e => {
    const t = e.target.closest(".pcx[data-code]");
    if (!t) { if (menu && !menu.contains(e.target)) close(); return; }
    e.preventDefault(); e.stopPropagation(); close();
    const code = t.dataset.code.replace(/^MP-/i, ""), here = location.pathname;
    menu = Object.assign(document.createElement("div"), { className: "pcxmenu" });
    menu.innerHTML = `<b>${esc(t.dataset.code)}</b>` + DEST.filter(([, u]) => !u.startsWith(here + "?")).map(([l, u]) => `<a href="${u}${encodeURIComponent(u.startsWith("/pedidos") ? t.dataset.code : code)}"><i></i>${l}</a>`).join("");
    document.body.appendChild(menu);
    const r = t.getBoundingClientRect(), w = menu.offsetWidth, h = menu.offsetHeight;
    menu.style.left = Math.max(8, Math.min(r.left, innerWidth - w - 8)) + "px"; menu.style.top = (r.bottom + h + 8 > innerHeight ? r.top - h - 6 : r.bottom + 6) + "px";
  });
  document.addEventListener("keydown", e => { if (e.key === "Escape") close(); });
  window.addEventListener("scroll", close, true);
})();

// ---- tema claro/escuro (gravado neste navegador) ----
/* update 6: com `origem` (o botão clicado), a troca vem numa onda — View Transitions: o navegador fotografa a tela antes e depois e só o recorte em círculo
   cresce do centro do botão até cobrir a tela (~0,6 s), sem recalcular a página a cada quadro. Sem o recurso, ou com «reduzir movimento», troca na hora.
   Enquanto dura, menu e barra do topo perdem o nome de transição próprio (html.psd-onda), senão escapariam da onda. */
const _aplicaTema = t => { document.documentElement.setAttribute("data-theme", t); try { localStorage.setItem("psd-theme", t); } catch (e) { } document.dispatchEvent(new CustomEvent("psd-theme", { detail: t })); };
window.psdTheme = {
  get: () => document.documentElement.getAttribute("data-theme") || "light",
  set(t, origem) {
    const html = document.documentElement;
    if (!origem || !document.startViewTransition || matchMedia("(prefers-reduced-motion: reduce)").matches || html.classList.contains("psd-onda")) return _aplicaTema(t);
    const r = origem.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2, raio = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
    html.classList.add("psd-onda");
    let tr; try { tr = document.startViewTransition(() => _aplicaTema(t)); } catch (e) { html.classList.remove("psd-onda"); return _aplicaTema(t); }
    tr.ready.then(() => html.animate({ clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${raio}px at ${x}px ${y}px)`] },
      { duration: 600, easing: "cubic-bezier(.2,.8,.2,1)", pseudoElement: "::view-transition-new(root)" })).catch(() => { });
    tr.finished.finally(() => html.classList.remove("psd-onda"));
  },
  toggle(origem) { this.set(this.get() === "dark" ? "light" : "dark", origem); }
};
document.addEventListener("click", e => { const b = e.target.closest("#themebtn"); if (!b) return; psdTheme.toggle(b);
  b.classList.remove("gira"); void b.offsetWidth; b.classList.add("gira"); b.addEventListener("animationend", () => b.classList.remove("gira"), { once: true }); });   // etapa 23: o ícone que entra gira (marca.css)
/* etapa 24: o sistema abre sem a janela do cmd; «Fechar o sistema» (botão no topo) encerra o servidor */
document.addEventListener("click", async e => { if (!e.target.closest("#psd-fechar") || !window.PSDTW) return;
  if (!(await PSDTW.confirmar({ titulo: "Fechar o sistema?", texto: "O servidor para e esta página deixa de funcionar. Para abrir de novo, use o atalho «PERFECT Shock Data» (ou o iniciar.bat).", botao: "Fechar o sistema", perigo: true, icone: "power" }))) return;
  let espera = false; try { espera = !!(await (await fetch("/api/sistema/fechar", { method: "POST" })).json()).espera_sincronizacao; } catch (er) { }
  document.body.innerHTML = '<div style="display:grid;place-items:center;min-height:100vh;font:16px Segoe UI,sans-serif;color:#5A6378;text-align:center;padding:24px"><div><b style="font-size:20px;color:#202D56">'
    + (espera ? "O sistema fecha quando a sincronização terminar." : "O sistema foi fechado.") + '</b><br>Pode fechar esta aba. Para abrir de novo, use o atalho «PERFECT Shock Data».</div></div>'; });


// ---- chip de sincronização (topo direito): data da última sincronização com o servidor SQL ----
(() => {
  const chip = document.getElementById("syncchip"); if (!chip) return;
  const pop = document.getElementById("syncpop"), txt = document.getElementById("synctxt"); let timer = null, last = null;
  const fmt = s => s ? `${s.slice(8, 10)}/${s.slice(5, 7)} ${s.slice(11, 16)}` : null;
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  function render(st) {
    last = st; const cls = st.running ? "run" : !st.configured ? "off" : st.last_status === "erro" ? "err" : st.last_ok_at ? "ok" : "off";
    chip.className = "syncchip " + cls;
    txt.textContent = st.running ? "Sincronizando…" : !st.configured ? "Servidor não configurado" : st.last_ok_at ? "Atualizado " + fmt(st.last_ok_at) : "Nunca sincronizado";
    pop.innerHTML = `<b>Servidor SQL ${esc(st.host)}</b><p>${st.last_ok_at ? "Última sincronização: <b>" + fmt(st.last_ok_at) + "</b>, " + (st.items || 0).toLocaleString("pt-BR") + " itens" : "Ainda não houve sincronização."}</p>`
      + (!st.configured ? "<p class='syncerr'>Preencha <code>DEV_DB_USER</code> e <code>DEV_DB_PASSWORD</code> no arquivo <code>.env</code> e reinicie.</p>" : "")
      + (st.last_status === "erro" && st.last_error ? `<p class="syncerr">${esc(st.last_error)}</p>` : "")
      + `<button class="btn sm" id="syncnow" ${st.running || !st.configured ? "disabled" : ""}>${st.running ? "Sincronizando…" : "Sincronizar agora"}</button> <a class="btn ghost sm" href="/configuracoes">Detalhes</a>`;
    const b = document.getElementById("syncnow"); if (b) b.onclick = async () => { b.disabled = true; b.textContent = "Iniciando…"; try { const r = await fetch("/api/pipeline/sync", { method: "POST" }); const d = await r.json(); if (!r.ok) throw new Error(d.error); poll(); } catch (e) { (window.PSDTW ? PSDTW.erro(e) : alert(e.message)); refresh(); } };
  }
  async function refresh() { try { const st = await (await fetch("/api/pipeline/status")).json(); render(st); return st; } catch (e) { return null; } }
  function poll(cb) { clearInterval(timer); timer = setInterval(async () => { const st = await refresh(); if (st && !st.running) { clearInterval(timer); cb && cb(); window.dispatchEvent(new Event("psd-synced")); } }, 2000); refresh(); }
  window.psdSyncPoll = poll;
  chip.addEventListener("click", e => { e.stopPropagation(); pop.hidden = !pop.hidden; });
  document.addEventListener("click", e => { if (!pop.contains(e.target)) pop.hidden = true; });
  refresh().then(st => { if (st && st.running) poll(); });
})();
