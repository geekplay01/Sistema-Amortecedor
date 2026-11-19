/* Tela · Desenvolvimento e Redesenvolvimento — visual Tailwind (etapa 16 · B).
   Curtidos primeiro (desempate: status mais avançado) · atalho «Pendente compras» (clicar de novo limpa) · filtros na URL e lembrados por tela ·
   controle de status com marcação em lote. Detalhe do item: clique no código (data-rd → PSD.rdOpen, no núcleo). */
(function () {
  const { $, $$, esc, J, post, lnk, root, fail, FLG, FGROUPS, flagChips, dwFill } = PSD;
  const TW = window.PSDTW, { nf, badge, kpi, card, notice } = TW;
  const CHAVES = ["q", "status", "flag", "curtiu", "supplier", "make", "drawing", "validation", "catalog", "sample", "ordem"];
  const STATUS_ORDEM = ["PENDENTE COD. PERFECT", "PENDENTE PARTNUMBER FORNECEDOR", "PENDENTE CONFIRMAÇÃO", "EM COTAÇÃO", "PEDIDO CONFIRMADO", "FINALIZANDO CIT", "ITEM RECEBIDO"];
  const TOM = { "ITEM RECEBIDO": "green", "FINALIZANDO CIT": "blue", "PEDIDO CONFIRMADO": "violet", "EM COTAÇÃO": "amber" };
  const chip = (attrs, label, on, n, forte = false) => `<button type="button" ${attrs} aria-pressed="${on}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${on ? "border-blue-500 bg-blue-500 text-white" : forte ? "border-amber-500 bg-amber-500/10 text-ink hover:bg-amber-500/20" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${label}${n != null ? ` · ${nf(n)}` : ""}</button>`;
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500";
  const curtidas = r => `<span class="whitespace-nowrap tabular-nums"><span class="${r.curtiu ? "font-bold text-emerald-600" : "text-mute"}" title="Curtiu">▲ ${r.curtiu || 0}</span> <span class="${r.nao_curtiu ? "font-bold text-red-600" : "text-mute"}" title="Não curtiu">▼ ${r.nao_curtiu || 0}</span></span>`;
  const statusCell = s => (s || "").split(" · ").filter(Boolean).map(x => badge(x, TOM[x] || "slate")).join(" ") || "–";
  const clip = (t, w = "max-w-[16rem]") => t ? `<span class="block truncate ${w}" title="${esc(t)}">${esc(t)}</span>` : '<span class="text-mute">–</span>';

  function rdPage(k) {
    const lab = k === "des" ? "DESENVOLVIMENTO" : "REDESENVOLVIMENTO", slug = k === "des" ? "desenvolvimento" : "redesenvolvimento", outro = k === "des" ? "REDESENVOLVIMENTO" : "DESENVOLVIMENTO";
    const F = TW.filtros(slug, CHAVES); let pg = 1, fc = null, timer;
    root.innerHTML = `<div class="flex flex-col gap-5">
      <p class="m-0 text-sm text-mute">${k === "des" ? "DESENVOLVIMENTO = item novo em desenvolvimento." : "REDESENVOLVIMENTO = item do catálogo com outro fornecedor."} Um código = um item (pode ter várias aplicações). Fonte: servidor SQL, atualizado todo dia. <b>Curtidos aparecem primeiro.</b></p>
      <div id="rk" class="grid grid-cols-2 gap-4 lg:grid-cols-4"></div>
      <div id="rbar"></div>
      <div id="rbulk" class="hidden"></div>
      <div id="rmeta" class="text-sm text-mute"></div>
      <div id="rt"></div><div id="rp" class="flex items-center justify-center gap-3 text-sm text-mute"></div>
      <details id="rctl" class="rounded-2xl border border-line bg-card p-5 shadow-sm"><summary class="cursor-pointer text-base font-semibold text-ink">Controle de status <span class="text-sm font-normal text-mute">— contagem por pendência; clique para filtrar</span></summary><div id="rgr" class="mt-4 flex flex-col gap-4"></div></details>
    </div>`;

    /* barra de filtros (etapa 19 · Q6): Status, Controle e Fornecedor à vista; o resto em «Mais filtros»; atalhos Pendente compras e Curtidos */
    const CURT = { sim: "Curtidos ▲", sem: "Sem curtida", nao: "Com «não curtiu» ▼" }, CAT = { sim: "Já no catálogo", nao: "Fora do catálogo" }, AMO = { comprada: "Comprada", enviada: "Enviada", nenhuma: "Sem amostra" }, ORD = { status: "Status mais avançado", codigo: "Código" };
    const NOMES = { status: "Status", flag: "Controle", supplier: "Fornecedor", curtiu: "Curtidas", make: "Montadora", drawing: "Sub status desenho", validation: "Sub status validação", catalog: "Catálogo", sample: "Amostra", ordem: "Ordem", q: "Busca" };
    let maisAberto = false;
    const desenharFiltros = () => {
      const s = F.get(), sts = [...fc.status].sort((a, b) => STATUS_ORDEM.indexOf(a.v) - STATUS_ORDEM.indexOf(b.v));
      const flagOps = [{ v: "", l: "Todos" }, ...FGROUPS.flatMap(g => [{ g: g.label }, ...Object.keys(FLG).filter(x => FLG[x][2] === g.key).map(x => ({ v: x, l: FLG[x][0], n: fc.flags[x] || 0 }))]), { g: "Outros" }, { v: "nenhum", l: "Sem pendência", n: fc.flags.nenhum }];
      const val = (kk, v) => kk === "flag" ? (FLG[v] ? FLG[v][0] : "Sem pendência") : ({ curtiu: CURT, catalog: CAT, sample: AMO, ordem: ORD }[kk] || {})[v] || v;
      TW.pintarBarra($("#rbar"), {
        busca: { valor: s.q, ph: "Código, descrição, veículo, fornecedor…" },
        principais: [{ k: "status", rotulo: "Status", tipo: "lista", atual: s.status || "", opcoes: [{ v: "", l: "Todos" }, ...TW.ops(sts)] },
                     { k: "flag", rotulo: "Controle", tipo: "lista", atual: s.flag || "", opcoes: flagOps },
                     { k: "supplier", rotulo: "Fornecedor", tipo: "lista", atual: s.supplier || "", opcoes: [{ v: "", l: "Todos" }, ...TW.ops(fc.supplier)] }],
        mais: [{ k: "curtiu", rotulo: "Curtidas", atual: s.curtiu || "", opcoes: [{ v: "sim", l: CURT.sim, n: fc.curtidos }, { v: "sem", l: CURT.sem }, { v: "nao", l: CURT.nao, n: fc.nao_curtidos }] },
               { k: "catalog", rotulo: "Catálogo", atual: s.catalog || "", opcoes: Object.entries(CAT).map(([v, l]) => ({ v, l })) },
               { k: "sample", rotulo: "Amostra", atual: s.sample || "", opcoes: Object.entries(AMO).map(([v, l]) => ({ v, l })) },
               { k: "ordem", rotulo: "Ordenar por (padrão: mais curtidos)", atual: s.ordem || "", opcoes: Object.entries(ORD).map(([v, l]) => ({ v, l })) },
               { k: "make", rotulo: "Montadora", atual: s.make || "", opcoes: TW.ops(fc.make) },
               { k: "drawing", rotulo: "Sub status desenho", atual: s.drawing || "", opcoes: TW.ops(fc.drawing) },
               { k: "validation", rotulo: "Sub status validação", atual: s.validation || "", opcoes: TW.ops(fc.validation) }],
        aberto: maisAberto,
        atalhos: [{ k: "flag", v: "pend_compras", l: "Pendente compras", n: fc.flags.pend_compras, on: s.flag === "pend_compras", forte: true }, { k: "curtiu", v: "sim", l: "▲ Curtidos", n: fc.curtidos, on: s.curtiu === "sim" }],
        etiquetas: TW.etiquetas(s, NOMES, val),
        acoes: TW.botao("Baixar Excel", { href: `/api/export/${slug}.xlsx?${new URLSearchParams(s)}`, icone: "download" })
      });
    };
    const desenharAtalhos = () => {
      const s = F.get();
      $("#rgr").innerHTML = FGROUPS.map(g => `<div><div class="mb-2 text-xs font-semibold uppercase tracking-wide text-mute">${esc(g.label)}</div><div class="flex flex-wrap gap-2">` +
        Object.keys(FLG).filter(x => FLG[x][2] === g.key).map(x => chip(`data-tg="flag" data-v="${x}"`, esc(FLG[x][0]), s.flag === x, fc.flags[x] || 0)).join("") + `</div></div>`).join("");
    };
    const desenharKpis = () => {
      $("#rk").innerHTML = kpi(k === "des" ? "Itens em desenvolvimento" : "Itens em redesenvolvimento", nf(fc.total), `${nf(fc.lines)} aplicações (linhas)`, "blue") +
        kpi("Curtidos ▲", nf(fc.curtidos), fc.total ? `${nf(100 * fc.curtidos / fc.total, 0)}% dos itens` : "", "green") +
        kpi("Pendente compras", nf(fc.flags.pend_compras || 0), "atalho logo abaixo", "amber") +
        kpi("Item recebido", nf((fc.status.find(x => x.v === "ITEM RECEBIDO") || {}).n || 0), "status mais avançado do ciclo", "slate");
    };

    const carregar = async () => {
      const s = F.get(), qs = new URLSearchParams({ ...s, page: pg }).toString();
      $("#rt").innerHTML = `<div class="rounded-2xl border border-line bg-card px-5 py-8 text-sm text-mute">Carregando…</div>`;
      try {
        const d = await J(`/api/rd/${k}?` + qs), pages = Math.max(1, Math.ceil(d.total / d.size)), ativos = Object.keys(s).filter(x => x !== "ordem").length;
        $("#rmeta").innerHTML = `<b class="text-ink">${nf(d.total)}</b> item(ns)${ativos ? ` · ${ativos} filtro(s) ativo(s)` : ""}`;
        const cols = [{ h: '<input type="checkbox" class="rdall" title="Selecionar a página">' }, { h: "Código" }, { h: "Curtidas" }, { h: "Status" }, { h: "Controle de status", nw: false }, { h: "Descrição" },
          { h: "Montadora(s)" }, { h: "Veículo(s)" }, { h: "Fornecedor" }, { h: "Amostra" }, { h: "Catálogo" }, { h: "Desenho" }];
        $("#rt").innerHTML = TW.table(cols, d.rows.map(r => [`<input type="checkbox" class="rdsel" value="${esc(r.code)}">`,
          `<a href="#" class="font-semibold text-blue-600" data-rd="${k}" data-code="${esc(r.code)}">${esc(r.code)}</a>${r.also_other ? " " + badge(outro === "REDESENVOLVIMENTO" ? "também R-D" : "também DES", "violet") : ""}`,
          curtidas(r), statusCell(r.statuses), `<div class="flex min-w-[12rem] flex-wrap gap-1">${flagChips(r.flags)}</div>`, clip(r.description, "max-w-[18rem]"), clip(r.makes, "max-w-[10rem]"), clip(r.vehicles), clip(r.suppliers, "max-w-[8rem]"),
          r.sent ? `enviada ${TW.dmy(r.sent)}` : r.bought ? `comprada ${TW.dmy(r.bought)}` : '<span class="text-mute">–</span>', r.product_id ? lnk(r.product_id, "ficha") : '<span class="text-mute">–</span>', `<span data-dw="${esc(r.code)}"></span>`]),
          { h: "max-h-[65vh]" });
        dwFill($("#rt"));
        $("#rp").innerHTML = pages > 1 ? `<button type="button" data-p="${pg - 1}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button type="button" data-p="${pg + 1}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
        marcar();
      } catch (e) { $("#rt").innerHTML = notice(esc(e.message), "red"); }
    };
    const aplicar = (patch, logo = false) => { if (patch) F.set(patch); pg = 1; desenharFiltros(); desenharAtalhos(); clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 250); };

    // filtros: barra (etapa 19) → URL + recarrega; grupos do controle de status: clicar no ativo limpa
    TW.ligarBarra($("#rbar"), { set: (kk, v) => aplicar({ [kk]: v }, true), busca: t => aplicar({ q: t }, true), limpar: () => { F.clear(); aplicar(null, true); }, mais: ab => { maisAberto = ab; } });
    root.addEventListener("click", e => { const b = e.target.closest("[data-tg]"); if (!b) return; F.toggle(b.dataset.tg, b.dataset.v); aplicar(null, true); });
    $("#rp").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; carregar(); scrollTo(0, 0); } });

    // marcação em lote do controle de status
    const bar = $("#rbulk");
    bar.innerHTML = `<div class="flex flex-wrap items-center gap-2 rounded-xl border border-blue-500/30 bg-blue-500/10 px-4 py-2.5 text-sm text-ink"><b id="bn">0</b> selecionado(s)
      <select id="bf" class="${campo}">${Object.entries(FLG).map(([x, v]) => `<option value="${x}">${esc(v[0])}</option>`).join("")}</select>
      <button type="button" data-bv="1" class="rounded-lg bg-blue-600 px-3 py-1.5 font-semibold text-white">Marcar</button><button type="button" data-bv="0" class="rounded-lg border border-line bg-card px-3 py-1.5">Desmarcar</button>
      <button type="button" data-bv="auto" class="rounded-lg border border-line bg-card px-3 py-1.5">Voltar ao automático</button><button type="button" data-bv="x" class="rounded-lg border border-line bg-card px-3 py-1.5">Limpar seleção</button></div>`;
    const selecionados = () => $$(".rdsel:checked", root).map(c => c.value);
    const marcar = () => { const n = selecionados().length; bar.classList.toggle("hidden", !n); $("#bn", bar).textContent = n; };
    root.addEventListener("change", e => { if (e.target.classList.contains("rdall")) $$(".rdsel", root).forEach(c => c.checked = e.target.checked); if (e.target.matches(".rdall,.rdsel")) marcar(); });
    bar.addEventListener("click", async e => { const b = e.target.closest("[data-bv]"); if (!b) return;
      if (b.dataset.bv === "x") { $$(".rdsel,.rdall", root).forEach(c => c.checked = false); return marcar(); }
      const codes = selecionados(); if (!codes.length) return; const val = b.dataset.bv === "auto" ? null : b.dataset.bv === "1", fl = $("#bf", bar).value;
      const acao = val === null ? "Voltar ao automático" : val ? "Marcar" : "Desmarcar";
      if (!await PSDTW.confirmar({ titulo: `${acao} «${FLG[fl][0]}»?`, texto: `${codes.length} item(ns) selecionado(s).`, nota: "Dá para desfazer: marque de novo ou volte ao automático.", botao: acao, icone: "list-filter" })) return;
      try { await post(`/api/rd/${k}/flags/bulk`, { codes, flag: fl, value: val }); PSDTW.toast(`«${FLG[fl][0]}»: ${acao.toLowerCase()} em ${codes.length} item(ns).`); await recarregarTudo(); } catch (er) { PSDTW.erro(er); } });

    const recarregarTudo = async () => { fc = await J(`/api/rd/${k}/facets`); desenharKpis(); desenharFiltros(); desenharAtalhos(); await carregar(); };
    PSD.aoMudarControle = () => recarregarTudo().catch(fail);       // controle de status alterado no detalhe do item
    recarregarTudo().catch(fail);
  }
  PSD.tela("desenvolvimento", () => rdPage("des"));
  PSD.tela("redesenvolvimento", () => rdPage("rd"));
})();
