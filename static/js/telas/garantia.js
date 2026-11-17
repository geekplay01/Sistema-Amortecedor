/* Tela · Garantia — planilha «Analítico de Garantias» (etapa 16 · D8), visual Tailwind. (Antes: pages_exec.js, só código × defeito × quantidade.)
   Padrão: tipos de garantia, sem ocorrências canceladas, ano atual. Atalhos de ano, tipo, status, fornecedor, procedência e unidade: cada número = linhas da lista ao clicar
   (garantias.summary · counts). Defeito agrupado sem o prefixo AM-xxx; clicar num defeito, código, cliente ou lote filtra a tela. Filtros na URL e lembrados; o Excel segue os filtros.
   Sem a planilha, mostra o resumo do servidor (view ANALITICO_GARANTIA_DEVOLUCAO) e explica como carregar a planilha. Clientes ficam só no PC (o banco não vai para o repositório). */
(function () {
  const { $, esc, J, qs, root, fail } = PSD;
  const TW = window.PSDTW, { nf, brl0, badge, kpi, card, notice, empty } = TW;
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500";
  const botao = "rounded-lg border border-line bg-card px-3.5 py-2 text-sm font-semibold text-ink hover:bg-slate-500/10";
  const primario = "rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white no-underline hover:bg-blue-700";
  const chip = (attrs, label, on, n) => `<button type="button" ${attrs} aria-pressed="${on}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${on ? "border-blue-500 bg-blue-500 text-white" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${label}${n != null ? ` · ${nf(n)}` : ""}</button>`;
  const rotulo = t => `<span class="mr-1 w-24 shrink-0 text-xs font-semibold uppercase tracking-wide text-mute">${t}</span>`;
  const meio = '<span class="text-mute">–</span>';
  const MES = ["", "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
  const PROC = { PROCEDENTE: ["Procedente", "red"], IMPROCEDENTE: ["Improcedente", "green"], sem: ["Sem análise", "slate"] };
  const nomeUni = u => (u || "").replace(/^PRIVATE-/, "").replace("MOGI", "Mogi").replace("ARUJA", "Arujá");
  const pager = (pg, pages) => { const b = (p, dis, l) => `<button type="button" data-p="${p}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${dis ? "disabled" : ""}>${l}</button>`;
    return pages > 1 ? `${b(pg - 1, pg < 2, "‹")} Página ${pg} de ${pages} ${b(pg + 1, pg >= pages, "›")}` : ""; };
  // barras horizontais clicáveis (cada barra filtra a tela)
  const barras = (rows, lab, val, attr, cor = "bg-rose-500") => { const mx = Math.max(1, ...rows.map(val));
    return `<div class="flex flex-col gap-1.5">${rows.map(r => `<button type="button" ${attr(r)} class="group flex items-center gap-3 rounded-lg px-1 py-0.5 text-left hover:bg-slate-500/10">
      <span class="w-48 shrink-0 truncate text-xs text-ink sm:w-72" title="${esc(lab(r))}">${esc(lab(r))}</span><span class="h-2.5 flex-1 rounded-full bg-slate-500/10"><span class="block h-2.5 rounded-full ${cor}" style="width:${Math.max(2, 100 * val(r) / mx)}%"></span></span>
      <span class="w-14 shrink-0 text-right text-xs font-semibold tabular-nums text-ink">${nf(val(r))}</span></button>`).join("")}</div>`; };

  async function servidor() {          // sem planilha: o resumo antigo (servidor), compacto
    let d; try { d = await J("/api/warranty?top=10"); } catch (e) { d = { available: false }; }
    const como = notice('Carregue a planilha <b>Analítico de Garantias.xlsx</b> em <a class="text-blue-600" href="/atualizacao">Atualização de dados</a> (com esse nome). Ela traz tipo, status, cliente, valor, lote, fabricação, procedência e unidade; a cada carga, substitui a anterior.', "amber");
    if (!d.available) { root.innerHTML = `<div class="flex flex-col gap-5">${como}${empty("Ainda não há dados de garantia.")}</div>`; return; }
    root.innerHTML = `<div class="flex flex-col gap-5">${como}<div class="grid grid-cols-2 gap-4 lg:grid-cols-3">${kpi("Peças (servidor)", nf(d.total), "view ANALITICO_GARANTIA_DEVOLUCAO", "red")}${kpi("Códigos", nf(d.codigos))}${kpi("Defeitos", nf(d.defeitos), "", "amber")}</div>
      ${card("Defeitos mais frequentes", barras(d.top_defeitos, r => r.defeito, r => r.quantidade, () => ""))}</div>`;
  }

  async function garantia() {
    const F = TW.filtros("garantia", ["ano", "tipo", "status", "fornecedor", "procedencia", "unidade", "defeito", "q"]); let pg = 1, d = null, timer;
    try { d = await J("/api/garantias?" + qs({ ...F.get(), page: 1 })); } catch (e) { return fail(e); }
    if (!d.available) return servidor();
    const ano = () => F.get().ano || String(new Date().getFullYear());
    root.innerHTML = `<div class="flex flex-col gap-5">
      <div id="gk" class="grid grid-cols-2 gap-4 lg:grid-cols-4"></div>
      <div id="gq" class="flex flex-col gap-2"></div>
      <form id="gf" class="flex flex-wrap items-center gap-2" autocomplete="off"><input name="q" type="search" placeholder="Buscar código, cliente, grupo, lote, autorização ou NF…" class="${campo} min-w-[16rem] flex-1"><button type="button" id="gclr" class="${botao}">Limpar filtros</button></form>
      <div id="gm" class="flex flex-wrap items-center justify-between gap-3 text-sm text-mute"></div>
      <div id="gc"></div>
      <div id="gg" class="grid grid-cols-1 gap-5 xl:grid-cols-2"></div>
      <div id="gl"></div><div id="gp" class="flex items-center justify-center gap-3 text-sm text-mute"></div></div>`;
    $("#gf").q.value = F.get().q || "";

    const desenhar = () => {
      const s = F.get(), k = d.kpis, c = d.counts;
      $("#gk").innerHTML = kpi("Peças em garantia", nf(k.pecas), `${nf(k.linhas)} itens · ${nf(k.codigos)} códigos`, "red") + kpi("Ocorrências", nf(k.ocorrencias), "autorizações distintas", "blue")
        + kpi("Valor c/ IPI", brl0(k.valor), "soma dos itens", "amber") + kpi("Procedentes", k.pct_procedente == null ? "–" : nf(k.pct_procedente, 1) + "%", `${nf(k.proc)} peças procedentes · ${nf(k.improc)} improcedentes`, "slate");
      const anos = Object.keys(c.ano).filter(x => x !== "sem").sort().reverse();
      const linha = (titulo, html) => `<div class="flex flex-wrap items-center gap-2">${rotulo(titulo)}${html}</div>`;
      $("#gq").innerHTML = linha("Ano", anos.map(y => chip(`data-k="ano" data-v="${y}"`, y, ano() === y, c.ano[y])).join("") + chip('data-k="ano" data-v="todos"', "Todos", s.ano === "todos"))
        + linha("Tipo", chip('data-k="tipo" data-v=""', "Só garantias", !s.tipo) + chip('data-k="tipo" data-v="todos"', "Todos", s.tipo === "todos") + Object.entries(c.tipo).sort((a, b) => b[1] - a[1]).map(([t, n]) => chip(`data-k="tipo" data-v="${esc(t)}"`, esc(t.toLowerCase()), s.tipo === t, n)).join(""))
        + linha("Status", chip('data-k="status" data-v=""', "Sem canceladas", !s.status) + chip('data-k="status" data-v="todos"', "Todos", s.status === "todos") + Object.entries(c.status).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([t, n]) => chip(`data-k="status" data-v="${esc(t)}"`, esc(t.toLowerCase()), s.status === t, n)).join(""))
        + linha("Fornecedor", Object.entries(c.fornecedor).sort((a, b) => b[1] - a[1]).map(([t, n]) => chip(`data-k="fornecedor" data-v="${esc(t)}" data-tg`, t === "sem" ? "não informado" : esc(t), s.fornecedor === t, n)).join(""))
        + linha("Procedência", Object.entries(c.procedencia).map(([t, n]) => chip(`data-k="procedencia" data-v="${esc(t)}" data-tg`, (PROC[t] || [t])[0], s.procedencia === t, n)).join(""))
        + linha("Unidade", Object.entries(c.unidade).map(([t, n]) => chip(`data-k="unidade" data-v="${esc(t)}" data-tg`, esc(nomeUni(t)), s.unidade === t, n)).join(""));
      const n = Object.keys(s).filter(x => s[x]).length;
      $("#gm").innerHTML = `<span><b class="text-ink">${nf(d.total)}</b> item(ns) de ocorrência${s.defeito ? ` · defeito <b class="text-ink">${esc(s.defeito)}</b>` : ""}${n ? ` · ${n} filtro(s)` : ""}${F.restaurado && pg === 1 ? ' · <span class="text-amber-700">filtros da última visita</span>' : ""}
        · planilha de ${TW.dmy(d.meta.de)} a ${TW.dmy(d.meta.ate)}</span><a class="${primario}" href="/api/export/garantia.xlsx?${qs(s)}">⬇ Baixar Excel</a>`;
      const pm = d.por_mes;
      $("#gc").innerHTML = card("Peças por mês", pm.length ? '<div id="gcm" class="chart"></div>' : empty("Sem dados no período."));
      if (pm.length) PSDCharts.bars($("#gcm"), { x: pm.map(m => `${MES[+m.mes.slice(5, 7)]}/${m.mes.slice(2, 4)}`), series: [{ name: "Peças", y: pm.map(m => m.pecas), color: "#f43f5e" }], height: 230, labels: pm.length <= 24 });
      $("#gg").innerHTML = card("Defeitos (sem o prefixo AM-xxx)", d.defeitos.length ? barras(d.defeitos, r => (r.cod ? r.cod + " · " : "") + r.defeito, r => r.pecas, r => `data-def="${esc(r.defeito)}"`) : empty("Nada."), s.defeito ? `<button type="button" data-def="" class="${botao} py-1 text-xs">Todos os defeitos</button>` : "")
        + card("Códigos com mais peças", TW.table([{ h: "Código" }, { h: "Descrição" }, { h: "Peças", r: true }, { h: "Valor", r: true }, { h: "Defeitos", r: true }],
            d.codigos.map(r => [`<button type="button" data-q="${esc(r.codigo)}" class="font-semibold text-blue-600">${esc(r.codigo)}</button>`, r.descricao ? `<span class="block max-w-[16rem] truncate" title="${esc(r.descricao)}">${esc(r.descricao)}</span>` : meio, nf(r.pecas), brl0(r.valor), nf(r.defeitos)]), { h: "max-h-[24rem]" }))
        + card("Clientes", TW.table([{ h: "Cliente" }, { h: "Grupo" }, { h: "Ocorrências", r: true }, { h: "Peças", r: true }, { h: "Valor", r: true }],
            d.clientes.map(r => [`<button type="button" data-q="${esc(r.cliente || "")}" class="block max-w-[16rem] truncate text-left font-semibold text-blue-600" title="${esc(r.cliente || "")}">${esc(r.cliente || "–")}</button>`, esc(r.grupo || "–"), nf(r.ocorrencias), nf(r.pecas), brl0(r.valor)]), { h: "max-h-[24rem]" }))
        + card("Lotes com mais peças", d.lotes.length ? TW.table([{ h: "Lote" }, { h: "Código" }, { h: "Fabricação" }, { h: "Peças", r: true }, { h: "Erro de lote", r: true }],
            d.lotes.map(r => [`<button type="button" data-q="${esc(r.lote)}" class="font-semibold text-blue-600">${esc(r.lote)}</button>`, esc(r.codigo || "–") + (r.codigos > 1 ? ` <span class="text-xs text-mute">+${r.codigos - 1}</span>` : ""), TW.dmy(r.fabricacao), nf(r.pecas), r.erro_lote ? badge(nf(r.erro_lote), "amber") : meio]), { h: "max-h-[24rem]" }) : empty("Nenhum lote informado nestas ocorrências."),
            `<span class="text-xs text-mute">responsável: ${d.responsavel.map(r => `${esc(r.responsavel.toLowerCase())} ${nf(r.pecas)}`).join(" · ")}</span>`);
      $("#gl").innerHTML = card("Itens de ocorrência", TW.table([{ h: "Data" }, { h: "Autorização" }, { h: "Tipo" }, { h: "Status" }, { h: "Unidade" }, { h: "Cliente" }, { h: "Código" }, { h: "Qtd", r: true }, { h: "Valor", r: true }, { h: "Defeito", nw: false }, { h: "Lote" }, { h: "Fabricação" }, { h: "Fornecedor" }, { h: "Procedência" }],
        d.rows.map(r => [TW.dmy(r.data_cadastro), esc(r.autorizacao || "–"), esc((r.tipo || "–").toLowerCase()), esc((r.status || "–").toLowerCase()), esc(nomeUni(r.unidade)), `<span class="block max-w-[14rem] truncate" title="${esc(r.cliente || "")}">${esc(r.cliente || "–")}</span>`,
          `<b>${esc(r.codigo)}</b>`, nf(r.qtd), brl0(r.valor), `<span class="block min-w-[14rem] text-xs">${esc((r.defeito_cod ? r.defeito_cod + " · " : "") + (r.defeito || ""))}</span>`, esc(r.lote || "–") + (r.erro_lote ? " " + badge("erro lote", "amber") : ""), TW.dmy(r.data_fabricacao), esc(r.fornecedor || "–"),
          r.procedencia ? badge((PROC[r.procedencia] || [r.procedencia])[0], (PROC[r.procedencia] || [0, "slate"])[1]) : meio]), { h: "max-h-[60vh]" }));
      $("#gp").innerHTML = pager(pg, Math.max(1, Math.ceil(d.total / d.size)));
    };
    const carregar = async () => { try { d = await J("/api/garantias?" + qs({ ...F.get(), page: pg })); } catch (e) { $("#gl").innerHTML = notice(esc(e.message), "red"); return; } desenhar(); };
    const aplicar = (patch, logo) => { if (patch) F.set(patch); pg = 1; clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 300); };

    $("#gf").addEventListener("input", e => { if (e.target.name === "q") aplicar({ q: e.target.value }); });
    $("#gf").addEventListener("submit", e => e.preventDefault());
    $("#gclr").addEventListener("click", () => { $("#gf").q.value = ""; F.clear(); aplicar(null, true); });
    root.addEventListener("click", e => {
      const b = e.target.closest("[data-k]"), df = e.target.closest("[data-def]"), qq = e.target.closest("[data-q]"), p = e.target.closest("[data-p]");
      if (b) { const k = b.dataset.k, v = b.dataset.v; if (b.hasAttribute("data-tg")) F.toggle(k, v); else F.set({ [k]: k === "ano" && v === String(new Date().getFullYear()) ? "" : v }); return aplicar(null, true); }
      if (df) { F.set({ defeito: df.dataset.def === F.get().defeito ? "" : df.dataset.def }); return aplicar(null, true); }
      if (qq) { $("#gf").q.value = qq.dataset.q; return aplicar({ q: qq.dataset.q }, true); }
      if (p && !p.disabled) { pg = +p.dataset.p; carregar(); $("#gl").scrollIntoView({ block: "start" }); }
    });
    desenhar();
  }
  PSD.tela("garantia", garantia);
})();
