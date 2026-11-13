/* Tela · Brands: PERFECT · BPROAUTO · MOTRIO · MOTORCRAFT (+ «Sem marca») — visual Tailwind (etapa 16 · B).
   Cartões de marca, «onde está» (catálogo, DES, R-D, base Motorcraft) e controles de status são atalhos: cada número = total da lista ao clicar
   (brands.items · counts; cada grupo ignora o próprio filtro e respeita os outros; test_24). Filtros na URL e lembrados (PSDTW.filtros); o Excel segue os filtros. */
(function () {
  const { $, esc, J, qs, root, fail, FLG, flagChips, dwFill } = PSD;
  const TW = window.PSDTW, { nf, badge, notice } = TW;
  const BC = { PERFECT: "#d4372c", BPROAUTO: "#2f7de1", MOTRIO: "#f2c12e", MOTORCRAFT: "#7c8cff", OUTROS: "#7b8794" }, NOME = { OUTROS: "Sem marca" };
  const ONDE = [["catalog", "No catálogo"], ["des", "Em DES"], ["rd", "Em R-D"], ["base", "Na base Motorcraft"]];
  const CTRL = ["pend_compras", "pend_validacao", "val_reprovada", "pend_desenho_forn"];
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500";
  const botao = "rounded-lg border border-line bg-card px-3.5 py-2 text-sm font-semibold text-ink hover:bg-slate-500/10";
  const primario = "rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-blue-700";
  const chip = (attrs, label, on, n, forte = false) => `<button type="button" ${attrs} aria-pressed="${on}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${on ? "border-blue-500 bg-blue-500 text-white" : forte ? "border-amber-500 bg-amber-500/10 text-ink hover:bg-amber-500/20" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${label}${n != null ? ` · ${nf(n)}` : ""}</button>`;
  const rotulo = t => `<span class="mr-1 text-xs font-semibold uppercase tracking-wide text-mute">${t}</span>`;
  const meio = '<span class="text-mute">–</span>';
  const pager = (pg, pages) => { const b = (p, dis, l) => `<button type="button" data-p="${p}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${dis ? "disabled" : ""}>${l}</button>`;
    return pages > 1 ? `${b(pg - 1, pg < 2, "‹")} Página ${pg} de ${pages} ${b(pg + 1, pg >= pages, "›")}` : ""; };

  function brands() {
    const F = TW.filtros("brands", ["b", "q", "scope", "flag"]); let pg = 1, S = null, d = null, timer;
    const marca = () => F.get().b || "PERFECT", nome = b => NOME[b] || b, filtrado = () => ["q", "scope", "flag"].some(k => F.get()[k]);
    root.innerHTML = `<div class="flex flex-col gap-5">
      <p class="m-0 text-sm text-mute">Itens agrupados pelo código: <b class="text-ink">AMD…</b> = PERFECT · <b class="text-ink">1BP…</b> = BPROAUTO · <b class="text-ink">somente números</b> = MOTRIO · itens da base <b class="text-ink">ItensMotorcraft</b> (PN Ford e a mesma família de código) = MOTORCRAFT. Reúne catálogo, desenvolvimento, redesenvolvimento, base de marcas e pedidos de amostra.</p>
      <div id="bg" class="grid grid-cols-2 gap-4 lg:grid-cols-5"></div>
      <div id="bq" class="flex flex-col gap-2"></div>
      <form id="bf" class="flex flex-wrap items-center gap-2" autocomplete="off"><input name="q" type="search" placeholder="Buscar código, código PERFECT, descrição ou veículo…" class="${campo} min-w-[16rem] flex-1"><button type="button" id="bclr" class="${botao}">Limpar filtros</button></form>
      <div id="bm" class="flex flex-wrap items-center justify-between gap-3 text-sm text-mute"></div>
      <div id="bt"></div><div id="bp" class="flex items-center justify-center gap-3 text-sm text-mute"></div>
    </div>`;
    $("#bf").q.value = F.get().q || "";

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
    const atalhos = () => {
      const s = F.get(), c = d.counts, onde = ONDE.filter(([k]) => c.scope[k] || s.scope === k), ctrl = CTRL.filter(k => c.flag[k] || s.flag === k);
      $("#bq").innerHTML = `<div class="flex flex-wrap items-center gap-2">${rotulo("Onde está")}${chip('data-tg="scope" data-v=""', "Todos", !s.scope, c.scope.all)}${onde.map(([k, l]) => chip(`data-tg="scope" data-v="${k}"`, l, s.scope === k, c.scope[k])).join("")}</div>`
        + (ctrl.length ? `<div class="flex flex-wrap items-center gap-2">${rotulo("Controle")}${ctrl.map(k => chip(`data-tg="flag" data-v="${k}"`, esc(FLG[k] ? FLG[k][0] : k), s.flag === k, c.flag[k], k === "pend_compras")).join("")}</div>` : "");
    };
    const tabela = () => {
      const s = F.get(), cur = marca(), n = ["q", "scope", "flag"].filter(k => s[k]).length, x = { ...s }; delete x.b;
      $("#bm").innerHTML = `<span><b class="text-ink">${nf(d.total)}</b> item(ns) ${esc(nome(cur))}${n ? ` · ${n} filtro(s) ativo(s)` : ""}${F.restaurado && pg === 1 ? ' · <span class="text-amber-700">filtros da última visita</span>' : ""}</span>
        <a class="${primario}" href="/api/export/brands.xlsx?${qs({ ...x, brand: cur })}">⬇ Baixar Excel</a>`;
      $("#bt").innerHTML = TW.table([{ h: "Código" }, { h: "Código PERFECT" }, { h: "Descrição" }, { h: "Veículo / aplicação" }, { h: "Onde está" }, { h: "Controle de status", nw: false }, { h: "Desenho" }, { h: "Amostras", r: true }],
        d.rows.map(i => [
          i.catalog && i.product_id ? `<a href="#" class="font-semibold text-blue-600" data-ficha="${i.product_id}">${esc(i.code)}</a>` : i.des || i.rd ? `<a href="#" class="font-semibold text-blue-600" data-rd="${i.des ? "des" : "rd"}" data-code="${esc(i.code)}">${esc(i.code)}</a>` : `<b class="text-ink">${esc(i.code)}</b>`,
          (i.perfect_codes || []).length ? i.perfect_codes.map(c => `<a class="font-semibold text-blue-600" href="/pesquisa?q=${encodeURIComponent(c)}">${esc(c)}</a>`).join(" ") : `<span class="text-mute">${i.brand === "PERFECT" ? "é o próprio" : "sem relação"}</span>`,
          i.description ? `<span class="block max-w-[18rem] truncate" title="${esc(i.description)}">${esc(i.description)}</span>` : meio,
          i.vehicle ? `<span class="block max-w-[18rem] truncate" title="${esc(i.vehicle)}">${esc(i.vehicle)}</span>` : meio,
          [i.catalog && badge("Catálogo", "blue"), i.des && badge("DES", "violet"), i.rd && badge("R-D", "green"), i.base && badge("Base Motorcraft", "slate")].filter(Boolean).join(" ") || meio,
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

    $("#bf").addEventListener("input", e => { if (e.target.name === "q") aplicar({ q: e.target.value }); });
    $("#bf").addEventListener("submit", e => e.preventDefault());
    $("#bclr").addEventListener("click", () => { $("#bf").q.value = ""; aplicar({ q: "", scope: "", flag: "" }, true); });
    $("#bg").addEventListener("click", e => { const b = e.target.closest("[data-b]"); if (b) aplicar({ b: b.dataset.b === "PERFECT" ? "" : b.dataset.b }, true); });
    $("#bq").addEventListener("click", e => { const b = e.target.closest("[data-tg]"); if (!b) return; if (b.dataset.v) F.toggle(b.dataset.tg, b.dataset.v); else F.set({ [b.dataset.tg]: "" }); aplicar(null, true); });
    $("#bp").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; carregar(); scrollTo(0, 0); } });
    (async () => { S = await J("/api/brands"); await carregar(); })().catch(fail);
  }
  PSD.tela("brands", brands);
})();
