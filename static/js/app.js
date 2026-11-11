// Dashboard, busca rápida e filtro do menu.
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const fetchJSON = (u) => fetch(u).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); });
  const esc = s => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

  if ($(".cards") && $("#empty")) {
    fetchJSON("/api/stats").then(s => {
      document.querySelectorAll("[data-stat]").forEach(el => el.textContent = s[el.dataset.stat] ?? 0);
      $("#empty").hidden = s.products > 0;
    }).catch(() => { const e = $("#empty"); e.hidden = false; e.textContent = "Não foi possível consultar o banco local. Verifique se o app.py está em execução."; });
  }
  // ---- menu lateral (Tailwind): grupos recolhíveis (lembra o estado), filtro, contadores e abertura no celular ----
  const navEl = $("#psd-nav"), side = $("#psd-side");
  if (navEl) {
    let st = {}; try { st = JSON.parse(localStorage.getItem("psd-menu") || "{}"); } catch (e) { }
    navEl.querySelectorAll(".gx").forEach(g => {
      const h = g.querySelector(".gx-h"); if (!h) return;                      // o grupo «Painel executivo» é fixo
      const on = g.querySelector("a[aria-current],a.bg-slate-700"), open = on ? true : st[g.dataset.g] !== false;
      g.classList.toggle("closed", !open); h.setAttribute("aria-expanded", open);
    });
    navEl.addEventListener("click", e => {
      const h = e.target.closest(".gx-h"); if (!h) return; const g = h.parentElement, closed = g.classList.toggle("closed");
      h.setAttribute("aria-expanded", !closed); st[g.dataset.g] = !closed; try { localStorage.setItem("psd-menu", JSON.stringify(st)); } catch (er) { }
    });
    fetch("/api/menu/counts").then(r => r.json()).then(c => Object.entries(c).forEach(([k, v]) => { const b = navEl.querySelector(`[data-badge="${k}"]`); if (b && v) { b.textContent = v > 999 ? Math.round(v / 100) / 10 + "k" : v; b.hidden = false; } })).catch(() => { });
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
  if (q) { let timer;
    q.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(async () => {
      if (q.value.trim().length < 2) { list.innerHTML = ""; return; }
      const r = await fetchJSON("/api/quick-search?q=" + encodeURIComponent(q.value));
      list.innerHTML = r.length ? r.map(p => `<li><a href="${esc(p.url)}"><span class="tag ${p.kind === "Catálogo" ? "cat" : p.kind.replace("-", "")}">${esc(p.kind)}</span> <b>${esc(p.code)}</b> ${esc(p.text || "")}</a></li>`).join("")
                                : "<li>Nenhum resultado no catálogo nem em DES / R-D.</li>";
    }, 250); });
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
  const DEST = [["Ficha / pesquisa", "/pesquisa?q="], ["Lados (par e traseiro)", "/lados?q="], ["Pedidos em aberto / lead time", "/pedidos-aberto?q="], ["Vendas (Curva A)", "/vendas?q="], ["Compra de amostras", "/amostras?q="]];
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
window.psdTheme = {
  get: () => document.documentElement.getAttribute("data-theme") || "light",
  set(t) { document.documentElement.setAttribute("data-theme", t); try { localStorage.setItem("psd-theme", t); } catch (e) { } document.dispatchEvent(new CustomEvent("psd-theme", { detail: t })); },
  toggle() { this.set(this.get() === "dark" ? "light" : "dark"); }
};
document.addEventListener("click", e => { if (e.target.closest("#themebtn")) psdTheme.toggle(); });


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
    pop.innerHTML = `<b>Servidor SQL ${esc(st.host)}</b><p>${st.last_ok_at ? "Última sincronização: <b>" + fmt(st.last_ok_at) + "</b> · " + (st.items || 0).toLocaleString("pt-BR") + " itens" : "Ainda não houve sincronização."}</p>`
      + (!st.configured ? "<p class='syncerr'>Preencha <code>DEV_DB_USER</code> e <code>DEV_DB_PASSWORD</code> no arquivo <code>.env</code> e reinicie.</p>" : "")
      + (st.last_status === "erro" && st.last_error ? `<p class="syncerr">${esc(st.last_error)}</p>` : "")
      + `<button class="btn sm" id="syncnow" ${st.running || !st.configured ? "disabled" : ""}>${st.running ? "Sincronizando…" : "Sincronizar agora"}</button> <a class="btn ghost sm" href="/configuracoes">Detalhes</a>`;
    const b = document.getElementById("syncnow"); if (b) b.onclick = async () => { b.disabled = true; b.textContent = "Iniciando…"; try { const r = await fetch("/api/pipeline/sync", { method: "POST" }); const d = await r.json(); if (!r.ok) throw new Error(d.error); poll(); } catch (e) { alert(e.message); refresh(); } };
  }
  async function refresh() { try { const st = await (await fetch("/api/pipeline/status")).json(); render(st); return st; } catch (e) { return null; } }
  function poll(cb) { clearInterval(timer); timer = setInterval(async () => { const st = await refresh(); if (st && !st.running) { clearInterval(timer); cb && cb(); window.dispatchEvent(new Event("psd-synced")); } }, 2000); refresh(); }
  window.psdSyncPoll = poll;
  chip.addEventListener("click", e => { e.stopPropagation(); pop.hidden = !pop.hidden; });
  document.addEventListener("click", e => { if (!pop.contains(e.target)) pop.hidden = true; });
  refresh().then(st => { if (st && st.running) poll(); });
})();
