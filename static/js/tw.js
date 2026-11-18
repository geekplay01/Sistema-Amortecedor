/* Componentes de tela em TailwindCSS (cards, KPIs, tabelas com rolagem interna, selos).
   As cores vêm das variáveis do tema (claro/escuro): bg-card, border-line, text-ink, text-mute — o mesmo HTML serve aos dois temas. */
window.PSDTW = (() => {
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const nf = (v, d = 0) => v == null || isNaN(v) ? "–" : Number(v).toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });
  const brl = v => v == null || isNaN(v) ? "–" : Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  const brl0 = v => v == null || isNaN(v) ? "–" : Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
  const dmy = s => s ? String(s).slice(0, 10).split("-").reverse().join("/") : "–";
  const TONE = { blue: "bg-blue-500/15 text-blue-600", green: "bg-emerald-500/15 text-emerald-600", amber: "bg-amber-500/20 text-amber-700", red: "bg-red-500/15 text-red-600", violet: "bg-violet-500/15 text-violet-600", slate: "bg-slate-500/15 text-slate-600" };
  const badge = (t, tone = "slate") => `<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${TONE[tone] || TONE.slate}">${esc(t)}</span>`;
  /* ícone do arquivo único (static/img/icones.svg; lista em tools/icones.py): ico("amortecedor"), ico("ship", "lg") */
  const ico = (n, cls = "") => `<svg class="psd-ico ${cls}" aria-hidden="true"><use href="${window.PSD_ICONES || "/static/img/icones.svg"}#i-${n}"/></svg>`;
  const stripes = () => '<span class="psd-stripes" aria-hidden="true"><i></i><i></i><i></i><i></i></span>';
  /* KPI: rótulo, número grande em Barlow e a linha de baixo na cor do significado (blue · green = OK · amber = risco · red = ruptura/erro · slate = neutro · sky) */
  const kpi = (label, value, sub = "", accent = "blue", icone = "") => `<div class="psd-kpi acc-${accent}"><div class="kpi-top"><span class="kpi-label">${label}</span>${icone ? `<span class="text-mute">${ico(icone)}</span>` : ""}</div>
    <div class="kpi-val">${value}</div>${sub ? `<div class="kpi-sub">${sub}</div>` : ""}</div>`;
  const card = (title, body, right = "", cls = "") => `<section class="rounded-2xl border border-line bg-card p-5 shadow-sm ${cls}"><div class="mb-4 flex flex-wrap items-center justify-between gap-3"><h3 class="m-0 text-base font-semibold text-ink">${title}</h3>${right}</div>${body}</section>`;
  const notice = (t, tone = "blue") => `<div class="rounded-xl border px-4 py-3 text-sm ${{ blue: "border-blue-500/30 bg-blue-500/10 text-ink", amber: "border-amber-500/40 bg-amber-500/10 text-ink", red: "border-red-500/40 bg-red-500/10 text-ink" }[tone]}">${t}</div>`;
  const empty = t => `<div class="rounded-2xl border border-dashed border-line bg-card px-6 py-12 text-center text-sm text-mute">${t}</div>`;
  /* tabela minimalista: fundo do card, bordas sutis, hover nas linhas e rolagem vertical INTERNA (cabeçalho fixo) */
  const table = (cols, rows, o = {}) => `<div class="${o.h || "max-h-[60vh]"} overflow-y-auto overflow-x-auto rounded-xl border border-line bg-card"><table class="psd-tbl w-full border-collapse text-sm">
    <thead class="sticky top-0 z-10 bg-thead"><tr class="border-b border-line">${cols.map(c => `<th class="whitespace-nowrap px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-mute ${c.r ? "text-right" : "text-left"}">${c.h}</th>`).join("")}</tr></thead>
    <tbody class="divide-y divide-line">${rows.length ? rows.map(r => `<tr>${r.map((v, i) => `<td class="px-4 py-2 text-ink ${cols[i].r ? "text-right tabular-nums" : ""} ${cols[i].nw === false ? "" : "whitespace-nowrap"}">${v}</td>`).join("")}</tr>`).join("") : `<tr><td class="px-4 py-10 text-center text-mute" colspan="${cols.length}">Nada encontrado com estes filtros.</td></tr>`}</tbody></table></div>`;
  const input = (id, ph, cls = "") => `<input id="${id}" type="search" placeholder="${ph}" class="w-full rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500 ${cls}">`;
  const select = (id, opts, cur = "", cls = "") => `<select id="${id}" class="rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500 ${cls}">${opts.map(([v, l]) => `<option value="${esc(v)}" ${String(v) === String(cur) ? "selected" : ""}>${esc(l)}</option>`).join("")}</select>`;
  const btn = (id, label, ghost = true) => `<button type="button" id="${id}" class="rounded-lg px-3.5 py-2 text-sm font-semibold ${ghost ? "border border-line bg-card text-ink hover:bg-slate-500/10" : "bg-blue-600 text-white hover:bg-blue-700"}">${label}</button>`;
  /* nome do arquivo baixado: «PerfectAmortecedores - <tela como no menu> - dd-mm.ext» (igual a exporter.friendly_name) */
  const nome = (tela, ext = "csv") => { const d = new Date(); return `PerfectAmortecedores - ${tela} - ${String(d.getDate()).padStart(2, "0")}-${String(d.getMonth() + 1).padStart(2, "0")}.${ext}`; };
  const csv = (name, head, rows) => { const q = v => '"' + String(v ?? "").replace(/"/g, '""') + '"'; const b = new Blob(["﻿" + [head, ...rows].map(r => r.map(q).join(";")).join("\r\n")], { type: "text/csv;charset=utf-8" }); const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(b), download: name }); document.body.appendChild(a); a.click(); a.remove(); };

  /* Estado dos filtros de uma tela (etapa 17 · Q8): a URL manda e é a única memória.
     · links e conectores abrem a tela já filtrada; o Voltar do navegador volta aos filtros da URL;
     · tela aberta pelo menu (URL sem filtros) vem LIMPA (nada é lembrado da visita anterior);
     · set() grava na URL (sem recarregar); chip ativo clicado de novo = toggle() limpa o filtro.
     Uso: const F = PSDTW.filtros("desenvolvimento", ["q", "status", ...]);  F.get() → {chave: valor}; F.set({status: "X"}); F.toggle("flag", "pend_compras"); F.clear() */
  const filtros = (tela, chaves) => {
    const pick = o => Object.fromEntries(chaves.filter(k => o[k] != null && o[k] !== "").map(k => [k, String(o[k])]));
    try { localStorage.removeItem("psd-filtros-" + tela); } catch (e) { }          // limpa o que a versão anterior guardou
    let st = pick(Object.fromEntries(new URLSearchParams(location.search)));
    const write = () => { const u = new URLSearchParams(st).toString(); history.replaceState(null, "", location.pathname + (u ? "?" + u : "") + location.hash); };
    write();
    return { get: () => ({ ...st }), set: patch => { st = pick({ ...st, ...patch }); write(); }, toggle: (k, v) => { st = pick({ ...st, [k]: st[k] === String(v) ? "" : v }); write(); }, clear: () => { st = {}; write(); } };
  };
  /* ---------- avisos no canto (etapa 17 · Q7): somem sozinhos em 4 s; erro só some ao fechar ----------
     toast("3 desenhos enviados", { tom: "ok", titulo: "Envio concluído" })  · tom: ok | erro | aviso | info */
  const TICO = { ok: "circle-check", erro: "circle-alert", aviso: "triangle-alert", info: "info" };
  const toast = (msg, o = {}) => {
    const tom = o.tom || "ok"; let box = document.querySelector(".psd-toasts");
    if (!box) { box = Object.assign(document.createElement("div"), { className: "psd-toasts" }); box.setAttribute("aria-live", "polite"); document.body.appendChild(box); }
    const t = Object.assign(document.createElement("div"), { className: "psd-toast " + tom }); t.setAttribute("role", tom === "erro" ? "alert" : "status");
    t.innerHTML = `<span class="t-ico">${ico(TICO[tom] || "info")}</span><div>${o.titulo ? `<b>${esc(o.titulo)}</b>` : ""}${o.html ? msg : esc(msg)}</div><button type="button" aria-label="Fechar aviso">${ico("x", "sm")}</button>`;
    const sai = () => { t.classList.add("saindo"); setTimeout(() => t.remove(), 170); };
    t.querySelector("button").onclick = sai; box.appendChild(t);
    if (tom !== "erro" && o.fixo !== true) setTimeout(sai, o.ms || 4000);
    return t;
  };
  /* ---------- confirmação no próprio app (nunca a caixa do navegador) ----------
     if (await confirmar({ titulo: "Excluir o ensaio?", texto: "AMD0100 · 12/11/2026", botao: "Excluir", perigo: true, nota: "Não dá para desfazer." })) … */
  const confirmar = (o = {}) => new Promise(res => {
    const d = Object.assign(document.createElement("dialog"), { className: "psd-confirm" + (o.perigo ? " perigo" : "") });
    d.innerHTML = `<div class="c-body"><span class="c-ico">${ico(o.icone || (o.perigo ? "trash-2" : "info"), "lg")}</span><div><h3>${esc(o.titulo || "Confirmar?")}</h3>${o.texto ? `<p>${o.html ? o.texto : esc(o.texto)}</p>` : ""}${o.nota ? `<p class="c-note">${esc(o.nota)}</p>` : ""}</div></div>
      <div class="c-acts"><button type="button" class="psd-btn" data-r="0">${esc(o.cancelar || "Cancelar")}</button><button type="button" class="psd-btn ${o.perigo ? "perigo" : "prim"}" data-r="1">${esc(o.botao || "Confirmar")}</button></div>`;
    const fim = v => { d.close(); d.remove(); res(v); };
    d.addEventListener("click", e => { const b = e.target.closest("[data-r]"); if (b) fim(b.dataset.r === "1"); else if (e.target === d) fim(false); });
    d.addEventListener("cancel", e => { e.preventDefault(); fim(false); });
    document.body.appendChild(d); d.showModal(); d.querySelector(o.perigo ? '[data-r="0"]' : '[data-r="1"]').focus();
  });
  /* ---------- carregamento: faixas da marca + texto, ou esqueleto no lugar de KPIs/tabela ---------- */
  const carregando = (t = "Carregando…") => `<div class="psd-load rounded-2xl border border-line bg-card px-5 py-8">${stripes()}<span>${esc(t)}</span></div>`;
  const esqueleto = (linhas = 6, kpis = 0) => (kpis ? `<div class="grid grid-cols-2 gap-4 lg:grid-cols-4">${'<div class="skel h-24"></div>'.repeat(kpis)}</div>` : "")
    + `<div class="flex flex-col gap-2 ${kpis ? "mt-5" : ""}"><div class="skel h-10"></div>${'<div class="skel h-8"></div>'.repeat(linhas)}</div>`;
  /* ---------- gráfico (Chart.js 4, salvo em static/vendor): cores da marca, fonte e grade do tema; redesenha ao trocar o tema ----------
     grafico(el, { type: "bar", data: { labels, datasets: [{ label, data }] }, options }) → instância (el = <canvas> ou contêiner) */
  const CORES = ["#2F4A8C", "#64C4E9", "#F6A019", "#E72B3B", "#0E9F6E", "#8B5CF6", "#94A3B8"];
  const cssv = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const tema = () => { const C = window.Chart; if (!C) return;
    C.defaults.font.family = '"Segoe UI Variable Text","Segoe UI",system-ui,sans-serif'; C.defaults.font.size = 12.5; C.defaults.color = cssv("--mut"); C.defaults.borderColor = cssv("--chart-grid");
    Object.assign(C.defaults.plugins.tooltip, { backgroundColor: cssv("--card"), titleColor: cssv("--tx"), bodyColor: cssv("--tx"), borderColor: cssv("--line"), borderWidth: 1, padding: 10, cornerRadius: 10, boxPadding: 4,
      titleFont: { family: cssv("--fontd"), weight: "600", size: 13 }, usePointStyle: true });
    C.defaults.plugins.legend.labels.usePointStyle = true; C.defaults.plugins.legend.labels.boxWidth = 8; C.defaults.maintainAspectRatio = false;
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) C.defaults.animation = false; };
  const vivos = new Set();
  const corDe = i => i % CORES.length === 0 ? (cssv("--chart-1") || CORES[0]) : CORES[i % CORES.length];      // a 1ª série clareia no tema escuro
  const pinta = (type, datasets) => (datasets || []).forEach((ds, i) => {          // só pinta o que o chamador não definiu (marcado em _auto)
    ds._auto ??= { bg: ds.backgroundColor == null, bd: ds.borderColor == null }; const c = ds.cor || corDe(i), roda = type === "doughnut" || type === "pie";
    if (ds._auto.bg) ds.backgroundColor = type === "line" ? c + "22" : roda ? CORES : c;
    if (ds._auto.bd) ds.borderColor = roda ? cssv("--card") : c; });
  const grafico = (el, cfg) => {
    if (!window.Chart) { (el.tagName === "CANVAS" ? el.parentElement : el).innerHTML = notice("Gráfico indisponível: static/vendor/chart.umd.js não foi carregado.", "amber"); return null; }
    tema(); let cv = el;
    if (el.tagName !== "CANVAS") { el.innerHTML = '<canvas role="img"></canvas>'; cv = el.firstChild; if (!el.style.height) el.style.height = (cfg.altura || 280) + "px"; el.style.position = "relative"; }
    if (cfg.titulo) cv.setAttribute("aria-label", cfg.titulo);
    pinta(cfg.type, cfg.data.datasets);
    (cfg.data.datasets || []).forEach(ds => {
      if (cfg.type === "bar") { ds.borderRadius ??= 6; ds.maxBarThickness ??= 34; ds.borderWidth ??= 0; }
      if (cfg.type === "line") { ds.tension ??= 0.35; ds.pointRadius ??= 3; ds.borderWidth ??= 2.5; ds.fill ??= true; } });
    const old = window.Chart.getChart(cv); if (old) old.destroy();
    const g = new window.Chart(cv, { type: cfg.type, data: cfg.data, options: cfg.options || {} }); vivos.add(g); return g;
  };
  document.addEventListener("psd-theme", () => { tema(); vivos.forEach(g => { if (!g.canvas.isConnected) { vivos.delete(g); return; } pinta(g.config.type, g.data.datasets); g.update(); }); });
  return { esc, nf, brl, brl0, dmy, badge, kpi, card, notice, empty, table, input, select, btn, csv, nome, filtros, ico, stripes, toast, confirmar, carregando, esqueleto, grafico, CORES };
})();
