/* Tela · Garantia — servidor (view ANALITICO_GARANTIA_DEVOLUCAO; etapa 18 · Q1/Q2/Q4). Tudo vem de /api/garantias (garantias.summary).
   Padrão: tipos de garantia, sem ocorrências canceladas, ano atual. Atalhos (ano, tipo, status, fornecedor, procedência, unidade, lote válido/vencido): cada número =
   linhas da lista ao clicar. Ordem da tela (Q4): KPIs × mesmo período do ano anterior · mapa do Brasil (índice = peças em garantia ÷ vendidas na UF, e o código com
   mais garantia em cada estado; clicar filtra) · mensal com a linha do ano anterior · Pareto de defeitos · top códigos (link para a página do item) · lotes e
   fornecedores lado a lado · itens de ocorrência. Filtros só na URL; o Excel segue os filtros. Clientes ficam só no PC (o banco não vai para o repositório). */
(function () {
  const { $, esc, J, qs, root, fail } = PSD;
  const TW = window.PSDTW, { nf, brl0, badge, kpi, card, notice, empty, ico } = TW;
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500";
  const botao = "rounded-lg border border-line bg-card px-3.5 py-2 text-sm font-semibold text-ink hover:bg-slate-500/10";
  const primario = "inline-flex items-center gap-2 rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white no-underline hover:bg-blue-700";
  const chip = (attrs, label, on, n) => `<button type="button" ${attrs} aria-pressed="${on}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${on ? "border-blue-500 bg-blue-500 text-white" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${label}${n != null ? ` · ${nf(n)}` : ""}</button>`;
  const seg = (grupo, opts, cur) => `<div class="inline-flex rounded-lg border border-line bg-card p-0.5" role="group">${opts.map(([v, l]) => `<button type="button" data-seg="${grupo}" data-v="${v}" aria-pressed="${v === cur}" class="rounded-md px-2.5 py-1 text-xs font-semibold ${v === cur ? "bg-blue-600 text-white" : "text-mute hover:text-ink"}">${l}</button>`).join("")}</div>`;
  const rotulo = t => `<span class="mr-1 w-24 shrink-0 text-xs font-semibold uppercase tracking-wide text-mute">${t}</span>`;
  const meio = '<span class="text-mute">–</span>';
  const MES = ["", "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
  const PROC = { PROCEDENTE: ["Procedente", "red"], IMPROCEDENTE: ["Improcedente", "green"], sem: ["Sem análise", "slate"] };
  const VAL = { VALIDO: "Lote válido", VENCIDO: "Lote vencido", sem: "Lote não informado" };
  const UFN = { AC: "Acre", AL: "Alagoas", AP: "Amapá", AM: "Amazonas", BA: "Bahia", CE: "Ceará", DF: "Distrito Federal", ES: "Espírito Santo", GO: "Goiás", MA: "Maranhão", MT: "Mato Grosso",
    MS: "Mato Grosso do Sul", MG: "Minas Gerais", PA: "Pará", PB: "Paraíba", PR: "Paraná", PE: "Pernambuco", PI: "Piauí", RJ: "Rio de Janeiro", RN: "Rio Grande do Norte", RS: "Rio Grande do Sul",
    RO: "Rondônia", RR: "Roraima", SC: "Santa Catarina", SP: "São Paulo", SE: "Sergipe", TO: "Tocantins" };
  const nomeUni = u => (u || "").replace(/^PRIVATE-/, "").replace("MOGI", "Mogi").replace("ARUJA", "Arujá");
  const pct = (v, d = 2) => v == null ? "–" : nf(v, d) + "%";
  const pager = (pg, pages) => { const b = (p, dis, l) => `<button type="button" data-p="${p}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${dis ? "disabled" : ""}>${l}</button>`;
    return pages > 1 ? `${b(pg - 1, pg < 2, "‹")} Página ${pg} de ${pages} ${b(pg + 1, pg >= pages, "›")}` : ""; };
  const itemLink = c => `<a href="/item/${encodeURIComponent(c)}" class="font-semibold text-blue-600 no-underline hover:underline" title="Abrir a página do item">${esc(c)}</a>`;

  /* variação × mesmo período do ano anterior: garantia que SOBE é ruim (vermelho), que cai é bom (verde) */
  const delta = (cur, ant, pp) => {
    if (ant == null || cur == null) return "";
    const v = pp ? cur - ant : ant ? 100 * (cur - ant) / ant : null; if (v == null) return "";
    const up = v > 0.05, dn = v < -0.05, cor = pp ? (up ? "text-red-600" : dn ? "text-emerald-600" : "text-mute") : (up ? "text-red-600" : dn ? "text-emerald-600" : "text-mute");
    return `<b class="${cor}">${up ? "▲" : dn ? "▼" : "="} ${nf(Math.abs(v), 1)}${pp ? " p.p." : "%"}</b>`;
  };

  /* ---------- mapa do Brasil (contornos do IBGE em static/js/brasil_uf.js) ---------- */
  const RAMPA = [16, 34, 52, 72, 92];          // % de vermelho da marca misturado ao fundo do card: funciona no tema claro e no escuro
  const cor = i => i == null ? "var(--thead)" : `color-mix(in srgb, var(--pf-red) ${RAMPA[i]}%, var(--card))`;
  const quebras = vals => { const v = vals.filter(x => x != null).sort((a, b) => a - b); if (!v.length) return [];
    return [0.2, 0.4, 0.6, 0.8].map(p => v[Math.min(v.length - 1, Math.floor(p * v.length))]); };
  const classe = (x, qb) => x == null ? null : qb.filter(t => x > t).length;
  function mapa(d, metrica, sel) {
    const B = window.PSD_BRASIL; if (!B) return notice("Mapa indisponível: static/js/brasil_uf.js não foi carregado.", "amber");
    const por = Object.fromEntries(d.por_uf.filter(r => r.uf).map(r => [r.uf, r]));
    const val = r => r ? (metrica === "indice" ? r.indice : r.pecas) : null;
    const qb = quebras(Object.keys(B.uf).map(u => val(por[u])));
    const paths = Object.entries(B.uf).map(([u, g]) => { const r = por[u], k = classe(val(r), qb), on = sel === u;
      return `<path d="${g.d}" data-uf="${u}" tabindex="0" role="button" aria-label="${UFN[u]}: ${metrica === "indice" ? pct(r && r.indice) : nf(r && r.pecas) + " peças"}" fill="${cor(k)}" stroke="${on ? "var(--navy)" : "var(--card)"}" stroke-width="${on ? 4 : 1.2}"></path>`; }).join("");
    const rot = Object.entries(B.uf).map(([u, g]) => { const k = classe(val(por[u]), qb);
      return `<text x="${g.x}" y="${g.y}" text-anchor="middle" dominant-baseline="central" font-size="${["DF", "SE", "AL", "RN", "PB", "ES", "RJ"].includes(u) ? 20 : 28}" font-weight="700" fill="${k >= 3 ? "#fff" : "var(--tx)"}">${u}</text>`; }).join("");
    const leg = qb.length ? [null, ...qb].map((t, i) => `<span class="inline-flex items-center gap-1.5"><i class="psd-sw" style="background:${cor(i)}"></i>${i === 0 ? "até " + (metrica === "indice" ? pct(qb[0]) : nf(qb[0])) : i === qb.length ? "acima de " + (metrica === "indice" ? pct(qb[i - 1]) : nf(qb[i - 1])) : (metrica === "indice" ? pct(qb[i]) : nf(qb[i]))}</span>`).join("")
      + `<span class="inline-flex items-center gap-1.5"><i class="psd-sw" style="background:var(--thead);border:1px solid var(--line)"></i>sem dado</span>` : "";
    return `<div class="relative"><svg viewBox="0 0 ${B.w} ${B.h}" class="psd-mapa mx-auto block h-auto max-h-[30rem] w-full" role="img" aria-label="Mapa do Brasil: ${metrica === "indice" ? "índice de garantia" : "peças em garantia"} por estado">${paths}${rot}</svg>
      <div id="gtip" class="pointer-events-none absolute z-20 hidden max-w-[17rem] rounded-xl border border-line bg-card px-3 py-2 text-xs text-ink shadow-lg"></div></div>
      <div class="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-mute">${leg}</div>`;
  }
  const dica = (r, u) => `<div class="mb-1 font-display text-sm font-semibold">${UFN[u] || u}</div>` + (r ? `<div>Índice de garantia: <b>${pct(r.indice)}</b></div><div>${nf(r.pecas)} peças em garantia · ${r.vendidas ? nf(r.vendidas) + " vendidas" : "sem venda no período"}</div>
    ${r.top.length ? `<div class="mt-1.5 border-t border-line pt-1.5">Mais garantia: <b>${esc(r.top[0].codigo)}</b> (${nf(r.top[0].pecas)} pç)${r.descricao ? `<div class="truncate text-mute">${esc(r.descricao)}</div>` : ""}</div>` : ""}` : '<div class="text-mute">Sem garantia no período.</div>');

  function regioes(d) {
    const B = window.PSD_BRASIL; if (!B) return "";
    const ac = {};
    d.por_uf.filter(r => r.uf && B.uf[r.uf]).forEach(r => { const g = B.uf[r.uf].regiao, a = ac[g] ||= { pecas: 0, vendidas: 0, ufs: [] }; a.pecas += r.pecas; a.vendidas += r.vendidas || 0; a.ufs.push(r); });
    const rows = Object.entries(ac).map(([g, a]) => ({ g, ...a, indice: a.vendidas ? 100 * a.pecas / a.vendidas : null })).sort((x, y) => (y.indice ?? -1) - (x.indice ?? -1));
    const mx = Math.max(0.0001, ...rows.map(r => r.indice || 0));
    return `<div class="flex flex-col gap-3">${rows.map(r => { const top = r.ufs.slice().sort((a, b) => (b.indice ?? -1) - (a.indice ?? -1))[0];
      return `<div><div class="flex items-baseline justify-between gap-2 text-sm"><span class="font-semibold text-ink">${B.regioes[r.g]}</span><span class="tabular-nums text-ink"><b>${pct(r.indice)}</b> <span class="text-xs text-mute">${nf(r.pecas)} pç</span></span></div>
        <div class="mt-1 h-2 rounded-full bg-slate-500/10"><div class="h-2 rounded-full" style="width:${Math.max(3, 100 * (r.indice || 0) / mx)}%;background:var(--pf-red)"></div></div>
        ${top ? `<div class="mt-1 text-xs text-mute">maior índice: <button type="button" data-uf="${top.uf}" class="font-semibold text-blue-600">${top.uf}</button> ${pct(top.indice)}${top.top[0] ? ` · mais garantia ${esc(top.top[0].codigo)}` : ""}</div>` : ""}</div>`; }).join("")}</div>`;
  }

  async function garantia() {
    const F = TW.filtros("garantia", ["ano", "tipo", "status", "fornecedor", "procedencia", "unidade", "uf", "validade", "defeito", "q"]); let pg = 1, d = null, timer, metrica = "indice", serie = "pecas";
    root.innerHTML = TW.esqueleto(6, 4);
    try { d = await J("/api/garantias?" + qs({ ...F.get(), page: 1 })); } catch (e) { return fail(e); }
    if (!d.available) { root.innerHTML = `<div class="flex flex-col gap-5">${notice('A garantia vem direto do servidor (view ANALITICO_GARANTIA_DEVOLUCAO) e é atualizada a cada sincronização. Use <b>Sincronizar agora</b> no topo ou aguarde a sincronização diária.', "amber")}${empty("Ainda não há dados de garantia.")}</div>`; return; }
    if (!d.vendas_uf) metrica = "pecas";
    const ano = () => F.get().ano || String(new Date().getFullYear());
    root.innerHTML = `<div class="flex flex-col gap-5">
      <div id="gk" class="grid grid-cols-2 gap-4 lg:grid-cols-4"></div>
      <div id="gq" class="flex flex-col gap-2"></div>
      <form id="gf" class="flex flex-wrap items-center gap-2" autocomplete="off"><input name="q" type="search" placeholder="Buscar código, cliente, grupo, lote, autorização ou NF…" class="${campo} min-w-[16rem] flex-1"><button type="button" id="gclr" class="${botao}">Limpar filtros</button></form>
      <div id="gm" class="flex flex-wrap items-center justify-between gap-3 text-sm text-mute"></div>
      <div class="grid grid-cols-1 gap-5 xl:grid-cols-5"><div id="gmap" class="xl:col-span-3"></div><div id="greg" class="xl:col-span-2"></div></div>
      <div class="grid grid-cols-1 gap-5 xl:grid-cols-2"><div id="gmes"></div><div id="gpar"></div></div>
      <div id="gcod"></div>
      <div class="grid grid-cols-1 gap-5 xl:grid-cols-2"><div id="glot"></div><div id="gfor"></div></div>
      <div id="gl"></div><div id="gp" class="flex items-center justify-center gap-3 text-sm text-mute"></div></div>`;
    $("#gf").q.value = F.get().q || "";

    const desenharMapa = () => {
      const s = F.get();
      $("#gmap").innerHTML = card("Garantia por estado", mapa(d, metrica, s.uf), (d.vendas_uf ? seg("metrica", [["indice", "Índice"], ["pecas", "Peças"]], metrica) : '<span class="text-xs text-mute">sem vendas por UF: mostra peças</span>'));
      const svg = $("#gmap svg"), tip = $("#gtip"); if (!svg) return;
      const por = Object.fromEntries(d.por_uf.filter(r => r.uf).map(r => [r.uf, r]));
      svg.addEventListener("mousemove", e => { const p = e.target.closest("[data-uf]"); if (!p) { tip.classList.add("hidden"); return; }
        const box = svg.parentElement.getBoundingClientRect(); tip.innerHTML = dica(por[p.dataset.uf], p.dataset.uf); tip.classList.remove("hidden");
        const x = e.clientX - box.left + 14, y = e.clientY - box.top + 14; tip.style.left = Math.min(x, box.width - tip.offsetWidth - 4) + "px"; tip.style.top = Math.min(y, box.height - tip.offsetHeight - 4) + "px"; });
      svg.addEventListener("mouseleave", () => tip.classList.add("hidden"));
      svg.addEventListener("keydown", e => { const p = e.target.closest("[data-uf]"); if (p && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); p.dispatchEvent(new MouseEvent("click", { bubbles: true })); } });
      const sel = s.uf ? por[s.uf] : null;
      $("#greg").innerHTML = card(sel ? UFN[s.uf] || s.uf : "Regiões", sel ? `<div class="flex flex-col gap-3 text-sm"><div class="grid grid-cols-2 gap-3">${kpi("Índice", pct(sel.indice), sel.vendidas ? nf(sel.vendidas) + " vendidas" : "sem venda", "red")}${kpi("Peças", nf(sel.pecas), nf(sel.ocorrencias) + " ocorrências", "slate")}</div>
          <div class="text-xs font-semibold uppercase tracking-wide text-mute">Amortecedores com mais garantia</div>${TW.table([{ h: "Código" }, { h: "Peças", r: true }], sel.top.map(t => [itemLink(t.codigo), nf(t.pecas)]), { h: "" })}</div>`
        : regioes(d) || empty("Sem dados."), s.uf ? `<button type="button" data-uf="${s.uf}" class="${botao} py-1 text-xs">Todos os estados</button>` : `<span class="text-xs text-mute">índice = peças em garantia ÷ vendidas</span>`);
    };

    const desenharMes = () => {
      const pm = d.por_mes, temAnt = d.anterior && pm.length && pm[0].pecas_ant != null, k = serie;
      $("#gmes").innerHTML = card("Mês a mês", pm.length ? '<div id="gcm"></div>' : empty("Sem dados no período."), seg("serie", [["pecas", "Peças"], ["valor", "Valor"]], serie));
      if (!pm.length) return;
      const lab = pm.map(m => `${MES[+m.mes.slice(5, 7)]}/${m.mes.slice(2, 4)}`);
      // a linha do ano anterior vai primeiro e sem cor fixa: usa a 1ª cor do tema (azul-marinho no claro, mais clara no escuro)
      const ds = [{ type: "bar", label: temAnt ? ano() : (k === "valor" ? "Valor c/ IPI" : "Peças"), data: pm.map(m => m.futuro ? null : m[k]), cor: "#E72B3B", order: 2 }];
      if (temAnt) ds.unshift({ type: "line", label: d.anterior.ano, data: pm.map(m => m[k + "_ant"]), fill: false, pointRadius: 2, tension: 0.2, order: 1 });
      TW.grafico($("#gcm"), { type: "bar", altura: 280, titulo: "Garantia mês a mês", data: { labels: lab, datasets: ds },
        options: { plugins: { legend: { display: temAnt }, tooltip: { mode: "index", intersect: false, callbacks: { label: c => ` ${c.dataset.label}: ${k === "valor" ? brl0(c.parsed.y) : nf(c.parsed.y) + " peças"}` } } },
          scales: { x: { grid: { display: false } }, y: { beginAtZero: true, ticks: { callback: v => k === "valor" ? "R$ " + nf(v / 1000) + " mil" : nf(v) } } } } });
    };

    const desenharPareto = () => {
      const s = F.get(), df = d.defeitos;
      $("#gpar").innerHTML = card("Pareto de defeitos", df.length ? '<div id="gcp"></div>' : empty("Nada."), s.defeito ? `<button type="button" data-def="" class="${botao} py-1 text-xs">Todos os defeitos</button>` : '<span class="text-xs text-mute">clique numa barra para filtrar</span>');
      if (!df.length) return;
      const g = TW.grafico($("#gcp"), { type: "bar", altura: 280, titulo: "Pareto de defeitos", data: { labels: df.map(r => r.defeito.length > 22 ? r.defeito.slice(0, 21) + "…" : r.defeito),
          datasets: [{ type: "line", label: "% acumulado", data: df.map(r => r.acum), fill: false, pointRadius: 2, tension: 0.2, yAxisID: "y1", order: 1 },
                     { type: "bar", label: "Peças", data: df.map(r => r.pecas), backgroundColor: df.map(r => r.defeito === s.defeito ? "#F6A019" : "#E72B3B"), yAxisID: "y", order: 2 }] },
        options: { onClick: (e, els) => { const i = (els.find(x => x.datasetIndex === 1) || els[0] || {}).index; if (i == null) return; F.set({ defeito: df[i].defeito === F.get().defeito ? "" : df[i].defeito }); aplicar(null, true); },
          onHover: (e, els) => { e.native.target.style.cursor = els.length ? "pointer" : "default"; },
          plugins: { legend: { display: true }, tooltip: { mode: "index", intersect: false, callbacks: { title: c => df[c[0].dataIndex].defeito, label: c => c.datasetIndex === 1 ? ` ${nf(c.parsed.y)} peças (${pct(df[c.dataIndex].pct, 1)})` : ` acumulado ${pct(c.parsed.y, 1)}` } } },
          scales: { x: { grid: { display: false }, ticks: { maxRotation: 50, minRotation: 30, font: { size: 11 } } }, y: { beginAtZero: true, ticks: { callback: v => nf(v) } },
            y1: { position: "right", min: 0, max: 100, grid: { display: false }, ticks: { callback: v => v + "%" } } } } });
      return g;
    };

    const desenhar = () => {
      const s = F.get(), k = d.kpis, a = d.anterior, c = d.counts;
      const ref = a ? `vs ${a.ano}${a.ate ? " até " + a.ate.split("-").reverse().join("/") : ""}` : "";
      const sub = (cur, ant, pp, extra) => [a ? `${delta(cur, ant, pp)} <span class="text-mute">${ref}</span>` : "", extra].filter(Boolean).join(" · ");
      $("#gk").innerHTML = kpi("Peças em garantia", nf(k.pecas), sub(k.pecas, a && a.pecas, false, a ? "" : `${nf(k.codigos)} códigos`), "red", "shield-check")
        + kpi("Valor c/ IPI", brl0(k.valor), sub(k.valor, a && a.valor, false), "amber")
        + kpi("Ocorrências", nf(k.ocorrencias), sub(k.ocorrencias, a && a.ocorrencias, false, a ? "" : "autorizações distintas"), "blue")
        + kpi("Procedentes", k.pct_procedente == null ? "–" : nf(k.pct_procedente, 1) + "%", a ? sub(k.pct_procedente, a.pct_procedente, true) : `${nf(k.proc)} procedentes · ${nf(k.improc)} improcedentes`, "slate");
      const anos = Object.keys(c.ano).filter(x => x !== "sem").sort().reverse();
      const linha = (titulo, html) => html ? `<div class="flex flex-wrap items-center gap-2">${rotulo(titulo)}${html}</div>` : "";
      $("#gq").innerHTML = linha("Ano", anos.map(y => chip(`data-k="ano" data-v="${y}"`, y, ano() === y, c.ano[y])).join("") + chip('data-k="ano" data-v="todos"', "Todos", s.ano === "todos"))
        + linha("Tipo", chip('data-k="tipo" data-v=""', "Só garantias", !s.tipo) + chip('data-k="tipo" data-v="todos"', "Todos", s.tipo === "todos") + Object.entries(c.tipo).sort((x, y) => y[1] - x[1]).map(([t, n]) => chip(`data-k="tipo" data-v="${esc(t)}"`, esc(t.toLowerCase()), s.tipo === t, n)).join(""))
        + linha("Status", chip('data-k="status" data-v=""', "Sem canceladas", !s.status) + chip('data-k="status" data-v="todos"', "Todos", s.status === "todos") + Object.entries(c.status).sort((x, y) => y[1] - x[1]).slice(0, 8).map(([t, n]) => chip(`data-k="status" data-v="${esc(t)}"`, esc(t.toLowerCase()), s.status === t, n)).join(""))
        + linha("Fornecedor", Object.entries(c.fornecedor).sort((x, y) => y[1] - x[1]).map(([t, n]) => chip(`data-k="fornecedor" data-v="${esc(t)}" data-tg`, t === "sem" ? "não informado" : esc(t), s.fornecedor === t, n)).join(""))
        + linha("Procedência", Object.entries(c.procedencia).map(([t, n]) => chip(`data-k="procedencia" data-v="${esc(t)}" data-tg`, (PROC[t] || [t])[0], s.procedencia === t, n)).join(""))
        + linha("Lote", Object.entries(c.validade).map(([t, n]) => chip(`data-k="validade" data-v="${esc(t)}" data-tg`, VAL[t] || esc(t), s.validade === t, n)).join(""))
        + linha("Unidade", Object.entries(c.unidade).map(([t, n]) => chip(`data-k="unidade" data-v="${esc(t)}" data-tg`, esc(nomeUni(t)), s.unidade === t, n)).join(""))
        + (s.uf ? linha("Estado", chip(`data-k="uf" data-v="${esc(s.uf)}" data-tg`, esc(UFN[s.uf] || s.uf), true, c.uf[s.uf] || 0)) : "");
      const n = Object.keys(s).filter(x => s[x]).length;
      $("#gm").innerHTML = `<span><b class="text-ink">${nf(d.total)}</b> item(ns) de ocorrência${s.defeito ? ` · defeito <b class="text-ink">${esc(s.defeito)}</b>` : ""}${n ? ` · ${n} filtro(s)` : ""}
        · servidor, cadastros de ${TW.dmy(d.meta.de)} a ${TW.dmy(d.meta.ate)}</span><a class="${primario}" href="/api/export/garantia.xlsx?${qs(s)}">${ico("download")} Baixar Excel</a>`;
      desenharMapa(); desenharMes(); desenharPareto();
      $("#gcod").innerHTML = card("Amortecedores com mais garantia", TW.table([{ h: "Código" }, { h: "Descrição" }, { h: "Peças", r: true }, { h: "% das peças", r: true }, { h: "Valor", r: true }, { h: "Defeitos", r: true }, { h: "" }],
        d.codigos.map(r => [itemLink(r.codigo), r.descricao ? `<span class="block max-w-[22rem] truncate" title="${esc(r.descricao)}">${esc(r.descricao)}</span>` : meio, nf(r.pecas), pct(100 * r.pecas / (k.pecas || 1), 1), brl0(r.valor), nf(r.defeitos),
          `<button type="button" data-q="${esc(r.codigo)}" class="text-xs font-semibold text-blue-600" title="Filtrar a tela por este código">filtrar</button>`]), { h: "max-h-[26rem]" }), '<span class="text-xs text-mute">clique no código para abrir a página do item</span>');
      $("#glot").innerHTML = card("Lotes com mais peças", d.lotes.length ? TW.table([{ h: "Lote" }, { h: "Código" }, { h: "Fabricação" }, { h: "Peças", r: true }, { h: "Erro", r: true }],
          d.lotes.map(r => [`<button type="button" data-q="${esc(r.lote)}" class="font-semibold text-blue-600">${esc(r.lote)}</button>${r.validade === "VENCIDO" ? " " + badge("vencido", "amber") : ""}`, esc(r.codigo || "–") + (r.codigos > 1 ? ` <span class="text-xs text-mute">+${r.codigos - 1}</span>` : ""), TW.dmy(r.fabricacao),
            nf(r.pecas), r.erro_lote ? badge(nf(r.erro_lote), "amber") : meio]), { h: "max-h-[24rem]" }) : empty("Nenhum lote informado nestas ocorrências."));
      $("#gfor").innerHTML = card("Fornecedores", TW.table([{ h: "Fornecedor" }, { h: "Códigos", r: true }, { h: "Peças", r: true }, { h: "Valor", r: true }, { h: "% procedente", r: true }],
          d.fornecedores.map(r => [r.fornecedor ? `<button type="button" data-k="fornecedor" data-v="${esc(r.fornecedor)}" data-tg class="font-semibold text-blue-600">${esc(r.fornecedor)}</button>` : '<span class="text-mute">não informado</span>', nf(r.codigos), nf(r.pecas), brl0(r.valor), pct(r.pct_procedente, 1)]), { h: "max-h-[24rem]" }));
      $("#gl").innerHTML = card("Itens de ocorrência", TW.table([{ h: "Data" }, { h: "Autorização" }, { h: "Tipo" }, { h: "Status" }, { h: "UF" }, { h: "Cliente" }, { h: "Código" }, { h: "Qtd", r: true }, { h: "Valor", r: true }, { h: "Defeito", nw: false }, { h: "Lote" }, { h: "Fabricação" }, { h: "Fornecedor" }, { h: "Procedência" }],
        d.rows.map(r => [TW.dmy(r.data_cadastro), esc(r.autorizacao || "–"), esc((r.tipo || "–").toLowerCase()), `<span title="${esc("Item: " + (r.status_item || "–").toLowerCase())}">${esc((r.status || "–").toLowerCase())}</span>`, esc(r.uf || "–"),
          `<span class="block max-w-[14rem] truncate" title="${esc(r.cliente || "")}">${esc(r.cliente || "–")}</span>`, itemLink(r.codigo), nf(r.qtd), brl0(r.valor), `<span class="block min-w-[14rem] text-xs">${esc((r.defeito_cod ? r.defeito_cod + " · " : "") + (r.defeito || ""))}</span>`,
          esc(r.lote || "–") + (r.lote_validade === "VENCIDO" ? " " + badge("vencido", "amber") : "") + (r.erro_lote ? " " + badge("erro lote", "amber") : ""), TW.dmy(r.data_fabricacao), esc(r.fornecedor || "–"),
          r.procedencia ? badge((PROC[r.procedencia] || [r.procedencia])[0], (PROC[r.procedencia] || [0, "slate"])[1]) : meio]), { h: "max-h-[60vh]" }));
      $("#gp").innerHTML = pager(pg, Math.max(1, Math.ceil(d.total / d.size)));
    };
    const carregar = async () => { try { d = await J("/api/garantias?" + qs({ ...F.get(), page: pg })); } catch (e) { $("#gl").innerHTML = notice(esc(e.message), "red"); return; } desenhar(); };
    const aplicar = (patch, logo) => { if (patch) F.set(patch); pg = 1; clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 300); };

    $("#gf").addEventListener("input", e => { if (e.target.name === "q") aplicar({ q: e.target.value }); });
    $("#gf").addEventListener("submit", e => e.preventDefault());
    $("#gclr").addEventListener("click", () => { $("#gf").q.value = ""; F.clear(); aplicar(null, true); });
    root.onclick = e => {
      const b = e.target.closest("[data-k]"), uf = e.target.closest("[data-uf]"), sg = e.target.closest("[data-seg]"), df = e.target.closest("[data-def]"), qq = e.target.closest("[data-q]"), p = e.target.closest("[data-p]");
      if (sg) { if (sg.dataset.seg === "metrica") { metrica = sg.dataset.v; desenharMapa(); } else { serie = sg.dataset.v; desenharMes(); } return; }
      if (uf) { F.toggle("uf", uf.dataset.uf); return aplicar(null, true); }
      if (b) { const k = b.dataset.k, v = b.dataset.v; if (b.hasAttribute("data-tg")) F.toggle(k, v); else F.set({ [k]: k === "ano" && v === String(new Date().getFullYear()) ? "" : v }); return aplicar(null, true); }
      if (df) { F.set({ defeito: df.dataset.def === F.get().defeito ? "" : df.dataset.def }); return aplicar(null, true); }
      if (qq) { $("#gf").q.value = qq.dataset.q; return aplicar({ q: qq.dataset.q }, true); }
      if (p && !p.disabled) { pg = +p.dataset.p; carregar(); $("#gl").scrollIntoView({ block: "start" }); }
    };
    desenhar();
  }
  PSD.tela("garantia", garantia);
})();
