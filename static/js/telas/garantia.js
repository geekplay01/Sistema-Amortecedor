/* Tela · Garantia — servidor (view ANALITICO_GARANTIA_DEVOLUCAO; etapa 18 · Q1/Q2/Q4). Tudo vem de /api/garantias (garantias.summary).
   Padrão: tipos de garantia, sem ocorrências canceladas, ano atual. Atalhos (ano, tipo, status, fornecedor, procedência, unidade, lote válido/vencido): cada número =
   linhas da lista ao clicar. Ordem da tela (Q4): KPIs × mesmo período do ano anterior · mapa do Brasil (índice = peças em garantia ÷ vendidas na UF, e o código com
   mais garantia em cada estado; clicar filtra) · mensal com a linha do ano anterior · Pareto de defeitos · top códigos (link para a página do item) · lotes e
   fornecedores lado a lado · itens de ocorrência. Filtros só na URL; o Excel segue os filtros. Clientes ficam só no PC (o banco não vai para o repositório). */
(function () {
  const { $, esc, J, qs, root, fail } = PSD;
  const TW = window.PSDTW, { nf, brl0, badge, kpi, card, notice, empty, ico } = TW;
  const botao = "psd-chip";            // botões pequenos dentro dos cards (etapa 19: padrão novo, sem o quadrado cinza)
  const seg = (grupo, opts, cur) => `<div class="psd-seg sm" role="group">${opts.map(([v, l]) => `<button type="button" data-seg="${grupo}" data-v="${v}" aria-pressed="${v === cur}">${l}</button>`).join("")}</div>`;
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
  const dica = (r, u) => `<div class="mb-1 font-display text-sm font-semibold">${UFN[u] || u}</div>` + (r ? `<div>Índice de garantia: <b>${pct(r.indice)}</b></div><div>${nf(r.pecas)} peças em garantia, ${r.vendidas ? nf(r.vendidas) + " vendidas" : "sem venda no período"}</div>
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
        ${top ? `<div class="mt-1 text-xs text-mute">maior índice: <button type="button" data-uf="${top.uf}" class="font-semibold text-blue-600">${top.uf}</button> ${pct(top.indice)}${top.top[0] ? `, mais garantia ${esc(top.top[0].codigo)}` : ""}</div>` : ""}</div>`; }).join("")}</div>`;
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
      <div id="gbar"></div>
      <div id="gm" class="text-sm text-mute"></div>
      <div class="grid grid-cols-1 gap-5 xl:grid-cols-5"><div id="gmap" class="xl:col-span-3"></div><div id="greg" class="xl:col-span-2"></div></div>
      <div class="grid grid-cols-1 gap-5 xl:grid-cols-2"><div id="gmes"></div><div id="gpar"></div></div>
      <div id="gcod"></div>
      <div class="grid grid-cols-1 gap-5 xl:grid-cols-2"><div id="glot"></div><div id="gfor"></div></div>
      <div id="gl"></div><div id="gp" class="flex items-center justify-center gap-3 text-sm text-mute"></div></div>`;
    let maisAberto = false;

    /* barra de filtros (etapa 19 · Q5): Ano (3 anos + Todos), Tipo e Status à vista; o resto em «Mais filtros»; etiquetas dos ativos */
    const desenharBarra = () => {
      const s = F.get(), c = d.counts, hoje = String(new Date().getFullYear());
      const anos = Object.keys(c.ano).filter(x => x !== "sem").sort().reverse().slice(0, 3);
      if (s.ano && s.ano !== "todos" && !anos.includes(s.ano)) anos.push(s.ano);
      const lista = (obj, rot) => Object.entries(obj).sort((a, b) => b[1] - a[1]).map(([v, n]) => ({ v, l: rot ? rot(v) : v.toLowerCase(), n, t: UFN[v] }));
      const op = (k, rot) => lista(c[k], rot);
      const R = { fornecedor: v => v === "sem" ? "Não informado" : v, procedencia: v => (PROC[v] || [v])[0], validade: v => VAL[v] || v, unidade: v => nomeUni(v) || v, uf: v => v === "sem" ? "Não informada" : v };
      const nomes = { ano: "Ano", tipo: "Tipo", status: "Status", fornecedor: "Fornecedor", procedencia: "Procedência", validade: "Lote", unidade: "Unidade", uf: "Estado", defeito: "Defeito", q: "Busca" };
      const val = (k, v) => k === "ano" ? (v === "todos" ? "todos os anos" : v) : k === "tipo" || k === "status" ? (v === "todos" ? "todos" : v.toLowerCase()) : k === "uf" ? (UFN[v] || R.uf(v)) : R[k] ? R[k](v) : v;
      TW.pintarBarra($("#gbar"), {
        busca: { valor: s.q, ph: "Código, cliente, lote, NF…" },
        principais: [
          { k: "ano", rotulo: "Ano", tipo: "seg", atual: !s.ano || s.ano === hoje ? "" : s.ano, opcoes: [...anos.map(y => ({ v: y === hoje ? "" : y, l: y, n: c.ano[y] })), { v: "todos", l: "Todos" }] },
          { k: "tipo", rotulo: "Tipo", tipo: "lista", atual: s.tipo || "", opcoes: [{ v: "", l: "Só garantias" }, { v: "todos", l: "Todos os tipos" }, ...op("tipo")] },
          { k: "status", rotulo: "Status", tipo: "lista", atual: s.status || "", opcoes: [{ v: "", l: "Sem canceladas" }, { v: "todos", l: "Todos os status" }, ...op("status")] }],
        mais: ["fornecedor", "procedencia", "validade", "unidade", "uf"].map(k => ({ k, rotulo: nomes[k], atual: s[k] || "", opcoes: op(k, R[k]) })),
        aberto: maisAberto,
        etiquetas: Object.keys(nomes).filter(k => s[k] && !(k === "ano" && s[k] === hoje)).map(k => ({ k, l: `${nomes[k]}: ${val(k, s[k])}` })),
        acoes: TW.botao("Baixar Excel", { href: "/api/export/garantia.xlsx?" + qs(s), icone: "download" })
      });
    };

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
          <div class="psd-rot">Amortecedores com mais garantia</div>${TW.table([{ h: "Código" }, { h: "Peças", r: true }], sel.top.map(t => [itemLink(t.codigo), nf(t.pecas)]), { h: "" })}</div>`
        : regioes(d) || empty("Sem dados."), s.uf ? `<button type="button" data-uf="${s.uf}" class="${botao} py-1 text-xs">Todos os estados</button>` : `<span class="text-xs text-mute">índice = peças em garantia ÷ vendidas</span>`);
    };

    const desenharMes = () => {
      const pm = d.por_mes, temAnt = d.anterior && pm.length && pm[0].pecas_ant != null, k = serie;
      $("#gmes").innerHTML = card("Mês a mês", pm.length ? '<div id="gcm"></div>' : empty("Sem dados no período."), seg("serie", [["pecas", "Peças"], ["valor", "Valor"]], serie));
      if (!pm.length) return;
      const lab = pm.map(m => `${MES[+m.mes.slice(5, 7)]}/${m.mes.slice(2, 4)}`);
      // etapa 24 · Q9: ano atual em azul (vermelho é «crítico»); o anterior em barra fina cinza ao lado, no mesmo eixo, em vez de uma linha cruzando as barras
      const fino = temAnt ? { maxBarThickness: 12 } : {}, fmt = v => k === "valor" ? "R$ " + TW.curto(v) : TW.curto(v);
      const ds = [{ label: temAnt ? ano() : (k === "valor" ? "Valor c/ IPI" : "Peças"), data: pm.map(m => m.futuro ? null : m[k]), cor: "--chart-1", ...fino }];
      if (temAnt) ds.unshift({ label: d.anterior.ano, data: pm.map(m => m[k + "_ant"]), cor: "--chart-7", ...fino });
      TW.grafico($("#gcm"), { type: "bar", altura: 280, titulo: "Garantia mês a mês", data: { labels: lab, datasets: ds },
        options: { datasets: { bar: temAnt ? { categoryPercentage: 0.62, barPercentage: 0.92 } : {} }, interaction: { mode: "index", intersect: false },
          plugins: { psdRotulos: { fmt }, tooltip: { callbacks: { label: c => ` ${c.dataset.label}: ${k === "valor" ? brl0(c.parsed.y) : nf(c.parsed.y) + " peças"}` } } },
          scales: { y: { ticks: { callback: fmt } } } } });
    };

    const desenharPareto = () => {
      const s = F.get(), df = d.defeitos;
      $("#gpar").innerHTML = card("Pareto de defeitos", df.length ? '<div id="gcp"></div>' : empty("Nada."), s.defeito ? `<button type="button" data-def="" class="${botao} py-1 text-xs">Todos os defeitos</button>` : '<span class="text-xs text-mute">clique numa barra para filtrar</span>');
      if (!df.length) return;
      // etapa 24 · Q9: um eixo só (dois eixos Y inventam uma relação entre as escalas); o acumulado vira a divisória «80% em N defeitos» e fica na dica.
      // Sem filtro, todas as barras em azul; com um defeito filtrado, ele em laranja e o resto em cinza.
      const i80 = df.findIndex(r => r.acum >= 80);
      const g = TW.grafico($("#gcp"), { type: "bar", altura: 280, titulo: "Pareto de defeitos", data: { labels: df.map(r => r.defeito.length > 22 ? r.defeito.slice(0, 21) + "…" : r.defeito),
          datasets: [{ label: "Peças", data: df.map(r => r.pecas), backgroundColor: df.map(r => !s.defeito ? "--chart-1" : r.defeito === s.defeito ? "--chart-2" : "--chart-7") }] },
        options: { onClick: (e, els) => { const i = (els[0] || {}).index; if (i == null) return; F.set({ defeito: df[i].defeito === F.get().defeito ? "" : df[i].defeito }); aplicar(null, true); },
          onHover: (e, els) => { e.native.target.style.cursor = els.length ? "pointer" : "default"; },
          plugins: { psdRotulos: false, psdDivisa: i80 >= 0 && i80 < df.length - 1 ? { i: i80, texto: `80% em ${i80 + 1} defeito${i80 ? "s" : ""}` } : { i: null },
            tooltip: { callbacks: { title: c => df[c[0].dataIndex].defeito, label: c => ` ${nf(c.parsed.y)} peças (${pct(df[c.dataIndex].pct, 1)}), acumulado ${pct(df[c.dataIndex].acum, 1)}` } } },
          layout: { padding: { top: 4 } }, scales: { x: { ticks: { maxRotation: 50, minRotation: 30, font: { size: 11 } } } } } });
      return g;
    };

    const desenhar = () => {
      const s = F.get(), k = d.kpis, a = d.anterior, c = d.counts;
      const ref = a ? `vs ${a.ano}${a.ate ? " até " + a.ate.split("-").reverse().join("/") : ""}` : "";
      const sub = (cur, ant, pp, extra) => [a ? `${delta(cur, ant, pp)} <span class="text-mute">${ref}</span>` : "", extra].filter(Boolean).join(", ");
      $("#gk").innerHTML = kpi("Peças em garantia", nf(k.pecas), sub(k.pecas, a && a.pecas, false, a ? "" : `${nf(k.codigos)} códigos`), "red", "shield-check")
        + kpi("Valor c/ IPI", brl0(k.valor), sub(k.valor, a && a.valor, false), "amber")
        + kpi("Ocorrências", nf(k.ocorrencias), sub(k.ocorrencias, a && a.ocorrencias, false, a ? "" : "autorizações distintas"), "blue")
        + kpi("Procedentes", k.pct_procedente == null ? "–" : nf(k.pct_procedente, 1) + "%", a ? sub(k.pct_procedente, a.pct_procedente, true) : `${nf(k.proc)} procedentes · ${nf(k.improc)} improcedentes`, "slate");
      desenharBarra();
      $("#gm").innerHTML = `<b class="text-ink">${nf(d.total)}</b> item(ns) de ocorrência, servidor, cadastros de ${TW.dmy(d.meta.de)} a ${TW.dmy(d.meta.ate)}`;
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
          `<span class="block max-w-[14rem] truncate" title="${esc(r.cliente || "")}">${esc(r.cliente || "–")}</span>`, itemLink(r.codigo), nf(r.qtd), brl0(r.valor), `<span class="block min-w-[14rem] text-xs">${esc((r.defeito_cod ? r.defeito_cod + ": " : "") + (r.defeito || ""))}</span>`,
          esc(r.lote || "–") + (r.lote_validade === "VENCIDO" ? " " + badge("vencido", "amber") : "") + (r.erro_lote ? " " + badge("erro lote", "amber") : ""), TW.dmy(r.data_fabricacao), esc(r.fornecedor || "–"),
          r.procedencia ? badge((PROC[r.procedencia] || [r.procedencia])[0], (PROC[r.procedencia] || [0, "slate"])[1]) : meio]), { h: "max-h-[60vh]" }));
      $("#gp").innerHTML = pager(pg, Math.max(1, Math.ceil(d.total / d.size)));
    };
    const carregar = async () => { try { d = await J("/api/garantias?" + qs({ ...F.get(), page: pg })); } catch (e) { $("#gl").innerHTML = notice(esc(e.message), "red"); return; } desenhar(); };
    const aplicar = (patch, logo) => { if (patch) F.set(patch); pg = 1; clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 300); };

    TW.ligarBarra($("#gbar"), { set: (k, v) => aplicar({ [k]: v }, true), busca: t => aplicar({ q: t }, true), limpar: () => { F.clear(); aplicar(null, true); }, mais: ab => { maisAberto = ab; } });
    root.onclick = e => {
      const b = e.target.closest("[data-k]"), uf = e.target.closest("[data-uf]"), sg = e.target.closest("[data-seg]"), df = e.target.closest("[data-def]"), qq = e.target.closest("[data-q]"), p = e.target.closest("[data-p]");
      if (sg) { if (sg.dataset.seg === "metrica") { metrica = sg.dataset.v; desenharMapa(); } else { serie = sg.dataset.v; desenharMes(); } return; }
      if (uf) { F.toggle("uf", uf.dataset.uf); return aplicar(null, true); }
      if (b) { const k = b.dataset.k, v = b.dataset.v; if (b.hasAttribute("data-tg")) F.toggle(k, v); else F.set({ [k]: k === "ano" && v === String(new Date().getFullYear()) ? "" : v }); return aplicar(null, true); }
      if (df) { F.set({ defeito: df.dataset.def === F.get().defeito ? "" : df.dataset.def }); return aplicar(null, true); }
      if (qq) return aplicar({ q: qq.dataset.q }, true);
      if (p && !p.disabled) { pg = +p.dataset.p; carregar(); $("#gl").scrollIntoView({ block: "start" }); }
    };
    desenhar();
  }
  PSD.tela("garantia", garantia);
})();
