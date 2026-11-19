/* Tela · Brands: PERFECT · BPROAUTO · MOTRIO · MOTORCRAFT (+ «Sem marca») — visual Tailwind (etapa 16 · B).
   Cartões de marca, «onde está» (catálogo, DES, R-D, base Motorcraft) e controles de status são atalhos: cada número = total da lista ao clicar
   (brands.items · counts; cada grupo ignora o próprio filtro e respeita os outros; test_24). Filtros na URL e lembrados (PSDTW.filtros); o Excel segue os filtros. */
(function () {
  const { $, esc, J, qs, root, fail, FLG, flagChips, dwFill } = PSD;
  const TW = window.PSDTW, { nf, badge, notice } = TW;
  const BC = { PERFECT: "#d4372c", BPROAUTO: "#2f7de1", MOTRIO: "#f2c12e", MOTORCRAFT: "#7c8cff", OUTROS: "#7b8794" }, NOME = { OUTROS: "Sem marca" };
  const ONDE = [["catalog", "No catálogo"], ["des", "Em DES"], ["rd", "Em R-D"], ["base", "Na base Motorcraft"]];
  const CTRL = ["pend_compras", "pend_validacao", "val_reprovada", "pend_desenho_forn"];
  const meio = '<span class="text-mute">–</span>';
  const pager = (pg, pages) => { const b = (p, dis, l) => `<button type="button" data-p="${p}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${dis ? "disabled" : ""}>${l}</button>`;
    return pages > 1 ? `${b(pg - 1, pg < 2, "‹")} Página ${pg} de ${pages} ${b(pg + 1, pg >= pages, "›")}` : ""; };

  function brands() {
    const F = TW.filtros("brands", ["b", "q", "scope", "flag"]); let pg = 1, S = null, d = null, timer;
    const marca = () => F.get().b || "PERFECT", nome = b => NOME[b] || b, filtrado = () => ["q", "scope", "flag"].some(k => F.get()[k]);
    root.innerHTML = `<div class="flex flex-col gap-5">
      <p class="m-0 text-sm text-mute">Itens agrupados pelo código: <b class="text-ink">AMD…</b> = PERFECT · <b class="text-ink">1BP…</b> = BPROAUTO · <b class="text-ink">somente números</b> = MOTRIO · itens da base <b class="text-ink">ItensMotorcraft</b> (PN Ford e a mesma família de código) = MOTORCRAFT. Reúne catálogo, desenvolvimento, redesenvolvimento, base de marcas e pedidos de amostra.</p>
      <div id="bg" class="grid grid-cols-2 gap-4 lg:grid-cols-5"></div>
      <div id="bq"></div>
      <div id="bm" class="text-sm text-mute"></div>
      <div id="bt"></div><div id="bp" class="flex items-center justify-center gap-3 text-sm text-mute"></div>
    </div>`;

    const cartoes = () => {
      const cur = marca(), c = d.counts.brand, lista = [...S.brands, ...(S.unclassified ? [{ brand: "OUTROS", rule: "Não se encaixa em nenhuma regra", total: S.unclassified }] : [])];
      $("#bg").innerHTML = lista.map(b => { const on = b.brand === cur, det = [["Catálogo", b.catalog], ["DES", b.des], ["R-D", b.rd], ["Base", b.base], ["Pend. compras", b.pend_compras]].filter(x => x[1]);
        return `<button type="button" data-b="${b.brand}" aria-pressed="${on}" class="relative overflow-hidden rounded-2xl border bg-card p-4 text-left shadow-sm ${on ? "border-blue-500 ring-2 ring-blue-500/40" : "border-line hover:bg-slate-500/10"}">
          <span class="absolute inset-x-0 top-0 h-1" style="background:${BC[b.brand]}"></span>
          <div class="text-xs font-semibold uppercase tracking-wide text-mute">${esc(nome(b.brand))}</div>
          <div class="mt-2 text-2xl font-bold leading-none tabular-nums text-ink">${nf(c[b.brand])}</div>
          <div class="mt-1 text-xs text-mute">${filtrado() ? `com os filtros · de ${nf(b.total)}` : esc(b.rule)}</div>
          ${det.length ? `<div class="mt-2 flex flex-wrap gap-1">${det.map(([l, n]) => `<span class="rounded-full bg-slate-500/10 px-2 py-0.5 text-xs text-mute">${l} ${nf(n)}</span>`).join("")}</div>` : ""}</button>`; }).join("");
    };
    /* barra (etapa 19 · Q6): a marca é escolhida nos cartões; Onde está e Controle à vista (listas com contagem) */
    const atalhos = () => {
      const s = F.get(), c = d.counts, x = { ...s }; delete x.b;
      const onde = ONDE.filter(([k]) => c.scope[k] || s.scope === k), ctrl = CTRL.filter(k => c.flag[k] || s.flag === k), nomeOnde = Object.fromEntries(ONDE);
      TW.pintarBarra($("#bq"), {
        busca: { valor: s.q, ph: "Código, código PERFECT, descrição ou veículo…" },
        principais: [{ k: "scope", rotulo: "Onde está", tipo: "lista", atual: s.scope || "", opcoes: [{ v: "", l: "Todos", n: c.scope.all }, ...onde.map(([k, l]) => ({ v: k, l, n: c.scope[k] }))] },
                     { k: "flag", rotulo: "Controle", tipo: "lista", atual: s.flag || "", opcoes: [{ v: "", l: "Todos" }, ...ctrl.map(k => ({ v: k, l: FLG[k] ? FLG[k][0] : k, n: c.flag[k] }))] }],
        atalhos: c.flag.pend_compras ? [{ k: "flag", v: "pend_compras", l: "Pendente compras", n: c.flag.pend_compras, on: s.flag === "pend_compras", forte: true }] : [],
        etiquetas: TW.etiquetas(s, { scope: "Onde está", flag: "Controle", q: "Busca" }, (k, v) => k === "scope" ? nomeOnde[v] || v : FLG[v] ? FLG[v][0] : v),
        acoes: TW.botao("Baixar Excel", { href: `/api/export/brands.xlsx?${qs({ ...x, brand: marca() })}`, icone: "download" })
      });
    };
    const tabela = () => {
      const s = F.get(), cur = marca(), n = ["q", "scope", "flag"].filter(k => s[k]).length;
      $("#bm").innerHTML = `<b class="text-ink">${nf(d.total)}</b> item(ns) ${esc(nome(cur))}${d.fora_base ? ` · inclui <b class="text-amber-700">${nf(d.fora_base)}</b> PN Ford fora da base (não contam no cartão)` : ""}${n ? ` · ${n} filtro(s) ativo(s)` : ""}`;
      $("#bt").innerHTML = TW.table([{ h: "Código" }, { h: "Código PERFECT" }, { h: "Descrição" }, { h: "Veículo / aplicação" }, { h: "Onde está" }, { h: "Controle de status", nw: false }, { h: "Desenho" }, { h: "Amostras", r: true }],
        d.rows.map(i => [
          i.catalog && i.product_id ? `<a href="#" class="font-semibold text-blue-600" data-ficha="${i.product_id}">${esc(i.code)}</a>` : i.des || i.rd ? `<a href="#" class="font-semibold text-blue-600" data-rd="${i.des ? "des" : "rd"}" data-code="${esc(i.code)}">${esc(i.code)}</a>` : `<b class="text-ink">${esc(i.code)}</b>`,
          (i.perfect_codes || []).length ? i.perfect_codes.map(c => `<a class="font-semibold text-blue-600" href="/pesquisa?q=${encodeURIComponent(c)}">${esc(c)}</a>`).join(" ") : `<span class="text-mute">${i.brand === "PERFECT" ? "é o próprio" : "sem relação"}</span>`,
          i.description ? `<span class="block max-w-[18rem] truncate" title="${esc(i.description)}">${esc(i.description)}</span>` : meio,
          i.vehicle ? `<span class="block max-w-[18rem] truncate" title="${esc(i.vehicle)}">${esc(i.vehicle)}</span>` : meio,
          [i.catalog && badge("Catálogo", "blue"), i.des && badge("DES", "violet"), i.rd && badge("R-D", "green"), i.base && badge("Base Motorcraft", "slate"), i.fora_base && badge("PN Ford fora da base", "amber")].filter(Boolean).join(" ") || meio,
          `<div class="flex min-w-[10rem] flex-wrap gap-1">${flagChips(i.flags)}</div>`, `<span data-dw="${esc(i.code)}"></span>`,
          i.samples ? `<a class="font-semibold text-blue-600" href="/amostras?q=${encodeURIComponent(i.code)}">${nf(i.samples)}</a>` : meio]), { h: "max-h-[65vh]" });
      dwFill($("#bt"));
      $("#bp").innerHTML = pager(pg, Math.max(1, Math.ceil(d.total / d.size)));
    };
    const carregar = async () => {
      try { const s = F.get(), x = { ...s }; delete x.b; d = await J(`/api/brands/${marca()}/items?` + qs({ ...x, page: pg })); }
      catch (e) { $("#bt").innerHTML = notice(esc(e.message), "red"); return; }
      cartoes(); atalhos(); tabela();
    };
    const aplicar = (patch, logo) => { if (patch) F.set(patch); pg = 1; clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 300); };

    TW.ligarBarra($("#bq"), { set: (k, v) => aplicar({ [k]: v }, true), busca: t => aplicar({ q: t }, true), limpar: () => aplicar({ q: "", scope: "", flag: "" }, true) });
    $("#bg").addEventListener("click", e => { const b = e.target.closest("[data-b]"); if (b) aplicar({ b: b.dataset.b === "PERFECT" ? "" : b.dataset.b }, true); });
    $("#bp").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; carregar(); scrollTo(0, 0); } });
    (async () => { S = await J("/api/brands"); await carregar(); })().catch(fail);
  }
  PSD.tela("brands", brands);
})();
