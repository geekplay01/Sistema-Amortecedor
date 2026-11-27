/* Tela · Dashboard — visual Tailwind (etapa 16 · B).
   Números do topo, barras do funil (status) e pendências por controle são links: abrem Produtos / DES / R-D já filtrados, com o mesmo número
   (app.api_dashboard · totals, funnel, flags; test_24).
   Fonte: /api/dashboard (metas, funil, controles, vendas e estoque do servidor, sistema FORCE GAS × FORCE OIL). */
(function () {
  const { $, esc, J, root, fail } = PSD;
  const TW = window.PSDTW, { nf, brl0, dmy, kpi, card, notice } = TW;
  const DES = "DESENVOLVIMENTO", RD = "REDESENVOLVIMENTO", SLUG = { [DES]: "desenvolvimento", [RD]: "redesenvolvimento" }, COR = { [DES]: "var(--chart-1)", [RD]: "var(--chart-2)" };   // DES azul, R-D laranja (ordem fixa da paleta, DESIGN.md §6.6)
  const chip = (attrs, label, on) => `<button type="button" ${attrs} aria-pressed="${on}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${on ? "border-blue-500 bg-blue-500 text-white" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${label}</button>`;
  const botao = "rounded-lg border border-line bg-card px-3 py-1.5 text-sm font-semibold text-ink no-underline hover:bg-slate-500/10";
  const vazio = t => `<p class="m-0 py-6 text-center text-sm text-mute">${t}</p>`;
  const link = (href, html, title) => `<a href="${href}" title="${esc(title)}" class="block no-underline">${html}</a>`;
  /* barras horizontais clicáveis: rótulo · barra proporcional · número (cada linha é um link para a lista filtrada) */
  const barras = (rows, cor) => {
    const max = Math.max(1, ...rows.map(r => r.n)), tot = rows.reduce((a, r) => a + r.n, 0) || 1;
    return `<div class="flex flex-col gap-0.5">${rows.map(r => `<a href="${r.href}" title="${esc(r.l)}: ${nf(r.n)} (${nf(100 * r.n / tot, 1)}%), clique para abrir a lista" class="flex items-center gap-3 rounded-lg px-2 py-1.5 text-sm no-underline hover:bg-slate-500/10">
      <span class="w-32 shrink-0 truncate text-ink sm:w-48">${esc(r.l)}</span>
      <span class="h-2.5 flex-1 rounded-full bg-slate-500/15"><span class="block h-2.5 rounded-full" style="width:${Math.max(2, 100 * r.n / max).toFixed(1)}%;background:${cor}"></span></span>
      <span class="w-14 shrink-0 text-right font-semibold tabular-nums text-ink">${nf(r.n)}</span></a>`).join("")}</div>`;
  };

  function dashboard() {
    const F = TW.filtros("dashboard", ["pk"]); let d = null;
    root.innerHTML = `<div class="flex flex-col gap-5">
      <div id="dban" class="flex flex-col gap-3"></div>
      <div id="dk" class="grid grid-cols-2 gap-4 lg:grid-cols-4"><p class="m-0 text-sm text-mute">Carregando indicadores…</p></div>
      <div id="dg" class="grid grid-cols-1 gap-4 xl:grid-cols-2"></div>
    </div>`;

    const banner = () => {
      const ps = d.pipeline, bn = [];
      if (!ps.configured) bn.push(notice("<b>Servidor SQL não configurado.</b> Preencha <code>DEV_DB_PASSWORD</code> no arquivo <code>.env</code> e reinicie. Enquanto isso, o sistema usa os dados já gravados.", "amber"));
      else if (!ps.last_ok_at) bn.push(notice("<b>Nenhuma sincronização com o servidor ainda.</b> Clique em <b>Sincronizar</b> no topo da tela para trazer Desenvolvimento, Redesenvolvimento, compras, vendas e estoque.", "amber"));
      if (ps.last_status === "erro" && ps.last_error) bn.push(notice(`<b>A última sincronização falhou:</b> ${esc(ps.last_error)}`, "red"));
      $("#dban").innerHTML = bn.join("");
    };

    /* fileira de destaque primeiro; os cartões de atalho (page.html · section.cards) vêm logo abaixo dela. DES e R-D com o mesmo número que abre a tela
       (itens em andamento, etapa 21) — antes mostravam o total de códigos de todos os estágios, diferente do cartão logo acima */
    const topo = () => {
      const s = d.sales, st = d.stats;
      $("#dk").innerHTML = link("/produtos", kpi("Produtos no catálogo", nf(st.products), "amortecedores PERFECT cadastrados", "blue"), "Abrir a lista de Produtos sem filtros")
        + link("/desenvolvimento", kpi("Em desenvolvimento", nf(st.des_items), `itens em andamento · ${nf(d.totals[DES])} códigos no total`, "blue"), "Abrir Desenvolvimento")
        + link("/redesenvolvimento", kpi("Em redesenvolvimento", nf(st.rd_items), `itens em andamento · ${nf(d.totals[RD])} códigos no total`, "green"), "Abrir Redesenvolvimento")
        + kpi("Vendas em 12 meses", s.available ? brl0(s.total_value) : "–", s.available ? `${nf(s.total_qty)} peças${s.last_date ? " · até " + dmy(s.last_date) : ""}` : "aguardando o servidor", "slate");
      const cs = document.querySelector("section.cards"); if (cs) $("#dk").after(cs);
    };

    const flagsCard = () => {
      const k = F.get().pk === "rd" ? RD : DES, f = d.flags[k];
      const rows = d.groups.defs.filter(s => f[s.key]).map(s => ({ l: s.label, n: f[s.key], href: `/${SLUG[k]}?flag=${s.key}` })).sort((a, b) => b.n - a.n);
      $("#dfl").innerHTML = card(`Pendências por controle de status`, (rows.length ? barras(rows, "#64748b") : vazio("Nenhuma pendência de status.")),
        `<div class="flex gap-2">${chip('data-pk=""', DES, k === DES)}${chip('data-pk="rd"', RD, k === RD)}</div>`);
    };

    const corpo = () => {
      const g = d.goals.goals, tr = d.tracking, vb = d.goals.basis === "validacao", u = esc(d.goals.validacoes?.filtro?.USER_VALID || "ITALOC"), y = d.goals.year;
      const funil = k => card(`Funil de ${k}`, d.funnel[k].length
        ? barras(d.funnel[k].map(r => ({ l: r.status, n: r.n, href: `/${SLUG[k]}?status=${encodeURIComponent(r.status)}` })), COR[k])
        : vazio("Sem itens ainda. Sincronize com o servidor."), `<a class="${botao}" href="/${SLUG[k]}">Abrir lista</a>`);
      const est = d.stock, st = (n, l) => `<div class="rounded-xl bg-slate-500/10 px-3 py-3 text-center"><div class="text-2xl font-bold tabular-nums text-ink">${n}</div><div class="text-xs text-mute">${l}</div></div>`;
      const ORD = ["gas", "oleo", "nd"], sys = [...d.system].sort((a, b) => ORD.indexOf(a.s) - ORD.indexOf(b.s)), LAB ={ gas: "FORCE GAS", oleo: "FORCE OIL", nd: "Sem dado" };
      $("#dg").innerHTML = [
        card(`Metas ${y}`, `<div class="grid grid-cols-1 gap-3"><div id="dg-des"></div><div id="dg-rd"></div></div>
          <p class="m-0 mt-2 text-xs text-mute">${tr.since ? "Transições rastreadas desde " + dmy(tr.since) : "O rastreio começa na 1ª sincronização com o servidor"}.</p>`, `<a class="${botao}" href="/metas">Detalhes e validações</a>`),
        card(`Evolução mensal das metas <span class="text-sm font-normal text-mute">${vb ? `validações ${u}` : "item recebido"}</span>`, '<div id="dg-evo" class="chart"></div>'),
        funil(DES), funil(RD),
        `<div id="dfl" class="xl:col-span-2"></div>`,
        card("Vendas nos últimos 12 meses", d.sales.available ? '<div id="dg-sales" class="chart"></div>' : vazio("Vendas ainda não chegaram do servidor. Sincronize em Configurações.")),
        card("Mais vendidos em 12 meses", !d.sales.available ? vazio("Vendas ainda não chegaram do servidor.") : d.sales.top.length
          ? TW.table([{ h: "Código" }, { h: "Descrição" }, { h: "Peças", r: true }, { h: "Valor", r: true }], d.sales.top.map(t => [`<a href="/pesquisa?q=${encodeURIComponent(t.code)}" class="font-semibold text-blue-600" title="Abrir na Pesquisa">${esc(t.code)}</a>`,
            `<span class="block max-w-[11rem] truncate" title="${esc(t.description || "")}">${esc(t.description || "–")}</span>`, nf(t.qty), brl0(t.value)]), { h: "max-h-[22rem]" })
          : vazio("Sem vendas no período.")),
        card("Estoque disponível", est.available ? `<div class="grid grid-cols-3 gap-2">${st(nf(est.qty), "peças disponíveis")}${st(nf(est.items), "códigos em estoque")}${st(nf(est.zero), "zerados")}</div>` : vazio("Estoque ainda não chegou do servidor.")),
        // update 5: volta a rosca (fina, total no centro, nome, quantidade e % ao lado); «Sem dado» em cinza
        // update 7: rosca dinâmica — a linha (e a fatia) abre Produtos filtrado pelo sistema; os botões «Ver …» saíram (a linha é o link)
        card("Sistema: FORCE GAS × FORCE OIL", TW.rosca(sys.map(r => ({ l: LAB[r.s] || r.s, v: r.n, cor: ({ gas: "--chart-1", oleo: "--chart-2" })[r.s] || "--chart-7", href: r.s !== "nd" ? `/produtos?system=${r.s}` : "" })),
          { rotulo: "itens no catálogo" })),
      ].join("");
      flagsCard();
      // anel com o ritmo do ano (update 5) + meses, rebobinar e projeção (update 7)
      const gg = (id, k, sub) => PSDCharts.gauge($(id), { value: g[k].done, target: g[k].target, title: k, subtitle: sub, year: y, serie: (g[k].series || {}).main, inicio: g[k].prior_aplica === false ? 0 : g[k].prior_done });
      gg("#dg-des", DES, vb ? `validações ${u} em ${y}` : `item recebido em ${y}`);          // a meta já aparece no medidor («de N»)
      gg("#dg-rd", RD, vb ? `validações ${u} em ${y}` : `recebido e validado (${u})`);
      const bs = vb ? `validações ${u}` : "item recebido";
      // update 6: nomes curtos (o visor mostra «DES 23  R-D 64»); a base da contagem vai no título do cartão
      PSDCharts.line($("#dg-evo"), { x: g[DES].series.main.map(m => m.month), series: [DES, RD].map(k => ({ name: k === DES ? "DES" : "R-D", y: g[k].series.main.map(m => m.n), color: COR[k] })), height: 260 });
      if (d.sales.available) PSDCharts.bars($("#dg-sales"), { x: d.sales.months.map(m => m.month), series: [{ name: "Peças vendidas", y: d.sales.months.map(m => m.qty) }], height: 250 });
    };

    root.addEventListener("click", e => { const b = e.target.closest("[data-pk]"); if (!b) return; F.set({ pk: b.dataset.pk }); flagsCard(); });
    (async () => {
      try { d = await J("/api/dashboard"); } catch (e) { return fail(e); }
      banner(); topo(); corpo();
    })();
  }
  PSD.tela("dashboard", dashboard);
})();
