/* Gráficos do PERFECT Shock Data — a MESMA interface de antes (PSDCharts.gauge | funnel | bars | hbars | donut | line (elemento, opções)), desenhada por
   PSDTW.grafico (Chart.js 4, static/vendor). Etapa 24 · Q9 (DESIGN.md §6.6): a paleta, a espessura das barras, as linhas de 2 px, os rótulos seletivos e a grade
   vêm de PSDTW.grafico; aqui ficam só as formas: donut → barra segmentada alta (PSDTW.segmentos), gauge → medidor reto (PSDTW.medidor), pilha com vão de 2 px.
   Cor: token ("--chart-2"); um hex antigo ainda passado por alguma tela cai no slot equivalente da paleta. */
window.PSDCharts = (() => {
  const T = () => window.PSDTW;
  const nf = n => (n == null || isNaN(n)) ? "–" : Number(n).toLocaleString("pt-BR", { maximumFractionDigits: 1 });
  const MES = ["", "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
  const mlabel = m => { const p = String(m).split("-"); return p.length > 1 && /^\d{4}$/.test(p[0]) ? MES[+p[1]] + "/" + p[0].slice(2) : String(m); };
  const SLOT = ["--chart-1", "--chart-2", "--chart-3", "--chart-4", "--chart-5", "--chart-6"];
  const pal = o => o.colors || SLOT;
  const G = (el, cfg) => { if (!el) return Promise.resolve(null); el.classList.add("ch"); el.style.height = ""; return Promise.resolve(T().grafico(el, cfg)); };
  const fmtOp = o => o.fmt ? { psdRotulos: { fmt: o.fmt } } : {};
  const tickOp = o => o.fmt ? { ticks: { callback: v => o.fmt(v) } } : {};
  /* pilha: só o bloco de cima de cada coluna tem a ponta arredondada (os do meio ficam retos; o vão de 2 px vem da borda na cor do cartão) */
  const topo = ctx => { const { dataIndex: i, datasetIndex: d, chart } = ctx, D = chart.data.datasets;
    for (let k = D.length - 1; k > d; k--) if (chart.isDatasetVisible(k) && D[k].data[i]) return 0; return { topLeft: 4, topRight: 4 }; };

  const bars = (el, o) => G(el, { type: "bar", altura: o.height || 280, data: { labels: o.x.map(mlabel), datasets: o.series.map((s, j) => ({ label: s.name, data: s.y, cor: s.color || pal(o)[j % pal(o).length],
      ...(o.stacked ? { stack: "s", borderRadius: topo } : {}) })) },
    options: { plugins: { tooltip: { mode: "index", intersect: false }, ...fmtOp(o) }, scales: { x: { stacked: !!o.stacked }, y: { stacked: !!o.stacked, ...tickOp(o) } } } });
  const line = (el, o) => G(el, { type: "line", altura: o.height || 260, data: { labels: o.x.map(mlabel), datasets: o.series.map((s, j) => ({ label: s.name, data: s.y, cor: s.color || pal(o)[j % pal(o).length],
      fill: o.fill === true && o.series.length === 1 })) },                    // área só com uma série (duas áreas sobrepostas escondem uma à outra)
    options: { plugins: { ...fmtOp(o) }, scales: { y: { ...tickOp(o) } } } });
  const hbars = (el, o) => { const tot = o.values.reduce((a, b) => a + (b || 0), 0) || 1;
    return G(el, { type: "bar", altura: Math.max(120, o.labels.length * 30 + 30), data: { labels: o.labels, datasets: [{ label: o.name || "Quantidade", data: o.values, cor: o.color || SLOT[0] }] },
      options: { indexAxis: "y", plugins: { tooltip: { callbacks: { afterLabel: c => "Participação: " + nf(100 * c.parsed.x / tot) + "%" } } }, scales: { x: { ...tickOp(o) } } } }); };
  const funnel = (el, o) => hbars(el, { labels: o.labels, values: o.values, color: (o.colors || [])[0], name: "Itens" });
  /* parte de um todo: barra segmentada de 28 px com a fatia escrita dentro (quando cabe) e a legenda embaixo, em vez da rosca */
  const donut = (el, o) => { if (!el) return Promise.resolve(null); el.classList.remove("ch"); el.style.height = "";
    T().segmentos(el, o.labels.map((l, i) => ({ l, v: o.values[i] || 0, cor: pal(o)[i % pal(o).length], txt: o.txt ? o.txt[i] : undefined })), { fmt: o.fmtParte });
    return Promise.resolve(null); };
  /* medidor de meta: número, «de N (x%)» e o trilho; verde só quando bate a meta */
  const gauge = (el, o) => { if (!el) return Promise.resolve(null); el.classList.remove("ch"); el.style.height = ""; el.innerHTML = T().medidor(o); return Promise.resolve(null); };

  return { ready: () => Promise.resolve(null), nf, palette: SLOT, gauge, funnel, bars, hbars, donut, line };
})();
