/* Gráficos do PERFECT Shock Data — etapa 17: a MESMA interface de antes (PSDCharts.gauge | funnel | bars | hbars | donut | line (elemento, opções)),
   agora desenhada pelo Chart.js 4 (static/vendor/chart.umd.js, salvo no app) através de PSDTW.grafico: cores da marca, fonte e grade do tema, dicas ao passar
   o mouse e redesenho ao trocar o tema. As telas que já chamavam PSDCharts não mudam. Cores antigas passadas pelas telas são trocadas pela paleta do logo. */
window.PSDCharts = (() => {
  const nf = n => (n == null || isNaN(n)) ? "–" : Number(n).toLocaleString("pt-BR", { maximumFractionDigits: 1 });
  const esc = s => String(s ?? "").replace(/[&<>"]/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m]));
  const MES = ["", "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
  const mlabel = m => { const p = String(m).split("-"); return p.length > 1 && /^\d{4}$/.test(p[0]) ? MES[+p[1]] + "/" + p[0].slice(2) : String(m); };
  const BRAND = ["#2F4A8C", "#64C4E9", "#F6A019", "#E72B3B", "#0E9F6E", "#8B5CF6", "#94A3B8"];
  const TROCA = { "#2f6bff": "#2F4A8C", "#5aa9ff": "#64C4E9", "#10b981": "#64C4E9",          /* verde antigo das séries → azul-claro (verde fica só para «OK») */ "#64748b": "#94A3B8", "#f59e0b": "#F6A019", "#8b5cf6": "#8B5CF6", "#06b6d4": "#64C4E9", "#f43f5e": "#E72B3B", "#94a3b8": "#94A3B8", "#ef4444": "#E72B3B", "#3b82f6": "#2F4A8C" };
  const cor = c => c ? (TROCA[String(c).toLowerCase()] || c) : null;
  const pal = o => (o.colors || BRAND).map(cor);
  const G = (el, cfg) => { if (!el) return Promise.resolve(null); el.classList.add("ch"); el.style.height = ""; return Promise.resolve(window.PSDTW.grafico(el, cfg)); };
  const tick = { callback: v => nf(v) };

  const bars = (el, o) => G(el, { type: "bar", altura: o.height || 280, data: { labels: o.x.map(mlabel), datasets: o.series.map((s, j) => ({ label: s.name, data: s.y, cor: cor(s.color) || pal(o)[j % pal(o).length], stack: o.stacked ? "s" : undefined })) },
    options: { plugins: { legend: { display: o.series.length > 1 }, tooltip: { mode: "index", intersect: false } }, scales: { x: { stacked: !!o.stacked, grid: { display: false } }, y: { stacked: !!o.stacked, ticks: tick } } } });
  const line = (el, o) => G(el, { type: "line", altura: o.height || 260, data: { labels: o.x.map(mlabel), datasets: o.series.map((s, j) => ({ label: s.name, data: s.y, cor: cor(s.color) || pal(o)[j % pal(o).length], fill: o.fill !== false })) },
    options: { plugins: { legend: { display: o.series.length > 1 }, tooltip: { mode: "index", intersect: false } }, scales: { x: { grid: { display: false } }, y: { ticks: tick, beginAtZero: true } } } });
  const hbars = (el, o) => { const tot = o.values.reduce((a, b) => a + (b || 0), 0) || 1;
    return G(el, { type: "bar", altura: Math.max(120, o.labels.length * 34 + 30), data: { labels: o.labels, datasets: [{ label: o.name || "Quantidade", data: o.values, cor: cor(o.color) || BRAND[0] }] },
      options: { indexAxis: "y", plugins: { legend: { display: false }, tooltip: { callbacks: { afterLabel: c => "Participação: " + nf(100 * c.parsed.x / tot) + "%" } } }, scales: { x: { ticks: tick }, y: { grid: { display: false } } } } }); };
  const funnel = (el, o) => hbars(el, { labels: o.labels, values: o.values, color: (o.colors || [])[0], name: "Itens" });
  const donut = (el, o) => { const tot = o.values.reduce((a, b) => a + (b || 0), 0) || 1;
    return G(el, { type: "doughnut", altura: o.height || 230, data: { labels: o.labels, datasets: [{ data: o.values, backgroundColor: pal(o) }] },
      options: { cutout: "64%", plugins: { legend: { position: "right" }, tooltip: { callbacks: { label: c => ` ${c.label}: ${nf(c.parsed)} (${nf(100 * c.parsed / tot)}%)` } } } } }); };
  /* medidor de meta: meia rosca (realizado × falta) com o número no centro; verde quando bate a meta */
  const gauge = (el, o) => { if (!el) return Promise.resolve(null);
    const v = o.value || 0, tgt = o.target || 0, ok = tgt && v >= tgt, pct = tgt ? Math.round(1000 * v / tgt) / 10 : 0;
    el.classList.add("ch"); el.style.position = "relative";
    el.innerHTML = `${o.title ? `<div class="text-center font-display text-sm font-semibold text-ink">${esc(o.title)}</div>` : ""}${o.subtitle ? `<div class="truncate text-center text-xs text-mute">${esc(o.subtitle)}</div>` : ""}
      <div class="relative" style="height:170px"><div data-g></div><div class="pointer-events-none absolute inset-x-0 text-center" style="bottom:14px"><div class="font-display text-3xl font-bold text-ink">${nf(v)}</div><div class="text-xs text-mute">${tgt ? `de ${nf(tgt)} · ${nf(pct)}%` : "sem meta"}</div></div></div>`;
    return Promise.resolve(window.PSDTW.grafico(el.querySelector("[data-g]"), { type: "doughnut", altura: 170, titulo: o.title || "Meta",
      data: { labels: ["Realizado", "Falta"], datasets: [{ data: [Math.min(v, tgt || v), Math.max((tgt || 0) - v, 0)], backgroundColor: [ok ? "#0E9F6E" : "#2F4A8C", getComputedStyle(document.documentElement).getPropertyValue("--line").trim() || "#DCE2EC"], borderWidth: 0 }] },
      options: { rotation: -90, circumference: 180, cutout: "74%", plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => ` ${c.label}: ${nf(c.parsed)}` } } } } })); };

  return { ready: () => Promise.resolve(null), nf, palette: BRAND, gauge, funnel, bars, hbars, donut, line };
})();
