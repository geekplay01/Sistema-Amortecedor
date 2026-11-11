/* Telas · Produtos e Pesquisa — visual Tailwind (etapa 16).
   Filtros do catálogo (planilha CatalogoAMD prevalece): Família, Ø da haste, Sistema (FORCE GAS / FORCE OIL) e Lançamento, com atalhos que ligam/desligam.
   Busca por código PERFECT, OEM ou de concorrente (com ou sem pontuação); a linha mostra qual referência casou. Filtros na URL e lembrados por tela (PSDTW.filtros).
   Pesquisa = Produtos + aplicação (montadora/modelo/ano/eixo/lado), código por tipo e itens em DES / R-D. Ficha: clique no código (data-ficha → PSD.openFicha). */
(function () {
  const { $, esc, J, qs, root, fail, SYS, dwFill } = PSD;
  const TW = window.PSDTW, { nf, badge, kpi, notice, empty } = TW;
  const BASE = ["q", "family", "rod", "system", "launch"], PESQ = [...BASE, "origem", "code", "code_type", "make", "model", "year", "axle", "side"];
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500";
  const chip = (attrs, label, on, n, forte = false) => `<button type="button" ${attrs} aria-pressed="${on}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${on ? "border-blue-500 bg-blue-500 text-white" : forte ? "border-amber-500 bg-amber-500/10 text-ink hover:bg-amber-500/20" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${label}${n != null ? ` · ${nf(n)}` : ""}</button>`;
  const selectF = (name, rotulo, opts, cur) => `<select name="${name}" class="${campo} max-w-[13rem]" title="${esc(rotulo)}"><option value="">${esc(rotulo)}</option>${opts.map(([v, l]) => `<option value="${esc(v)}" ${String(v) === String(cur ?? "") ? "selected" : ""}>${esc(l)}</option>`).join("")}</select>`;
  const textoF = (name, ph, cur, cls = "") => `<input name="${name}" type="search" value="${esc(cur || "")}" placeholder="${esc(ph)}" class="${campo} ${cls}">`;
  const mm = v => v == null ? '<span class="text-mute">–</span>' : nf(v, v % 1 ? 1 : 0);
  const sistema = s => s ? badge(SYS[s], s === "gas" ? "blue" : "amber") : '<span class="text-mute">–</span>';
  const familia = f => f ? f.charAt(0) + f.slice(1).toLowerCase() : "";
  const RD_LAB = { des: "DESENVOLVIMENTO", rd: "REDESENVOLVIMENTO" };

  function lista(slug, pesquisa) {
    const F = TW.filtros(slug, pesquisa ? PESQ : BASE); let pg = 1, fc = null, L = { makes: [], models: [], years: [] }, timer;
    root.innerHTML = `<div class="flex flex-col gap-5">
      <p class="m-0 text-sm text-mute">${pesquisa ? "<b>Digite o código PERFECT, OEM ou de um CONCORRENTE</b> (com ou sem ponto/hífen: 16.470 = 16470) ou uma aplicação (ex.: strada 2012 dianteiro). Procura no catálogo e nos itens em DESENVOLVIMENTO e REDESENVOLVIMENTO." : "Ordenado pela posição no catálogo (ordem da planilha CatalogoAMD, que prevalece). A busca aceita código PERFECT, OEM ou de concorrente — a linha mostra qual referência casou."}</p>
      ${pesquisa ? "" : '<div id="pk" class="grid grid-cols-2 gap-4 lg:grid-cols-4"></div>'}
      <div id="pq" class="flex flex-wrap items-center gap-2"></div>
      <form id="pf" class="flex flex-wrap items-center gap-2" autocomplete="off"></form>
      <div id="pmeta" class="flex flex-wrap items-center justify-between gap-3 text-sm text-mute"></div>
      <div id="pt"></div><div id="pp" class="flex items-center justify-center gap-3 text-sm text-mute"></div>
      <div id="px" class="flex flex-col gap-4"></div>
    </div>`;

    const desenharKpis = () => {
      if (pesquisa) return;
      $("#pk").innerHTML = kpi("Itens no catálogo", nf(fc.catalogo), `${nf(fc.total)} produtos cadastrados`, "blue") + kpi("FORCE GAS", nf(fc.system.gas || 0), "sistema a gás", "blue") +
        kpi("FORCE OIL", nf(fc.system.oleo || 0), fc.system.nd ? `${nf(fc.system.nd)} sem sistema informado` : "sistema a óleo", "amber") + kpi("Lançamentos", nf(fc.launch), "coluna Lançamento da planilha", "green");
    };
    const desenharAtalhos = () => {
      const s = F.get();
      $("#pq").innerHTML = `<span class="mr-1 text-xs font-semibold uppercase tracking-wide text-mute">Atalhos</span>` +
        chip('data-tg="launch" data-v="S"', "Lançamentos", s.launch === "S", fc.launch, true) + chip('data-tg="system" data-v="gas"', "FORCE GAS", s.system === "gas", fc.system.gas || 0) +
        chip('data-tg="system" data-v="oleo"', "FORCE OIL", s.system === "oleo", fc.system.oleo || 0) + fc.family.map(x => chip(`data-tg="family" data-v="${esc(x.v)}"`, esc(familia(x.v)), s.family === x.v, x.n)).join("");
    };
    const desenharFiltros = () => {
      const s = F.get();
      $("#pf").innerHTML = textoF("q", pesquisa ? "Busca livre: código, OEM, concorrente, veículo, ano…" : "Buscar: código PERFECT, OEM, concorrente, descrição, veículo, ano…", s.q, "min-w-[16rem] flex-1") +
        selectF("family", "Família", fc.family.map(x => [x.v, `${familia(x.v)} (${nf(x.n)})`]), s.family) +
        selectF("rod", "Ø haste", fc.rod.map(x => [x.v, `${mm(x.v)} mm (${nf(x.n)})`]), s.rod) +
        selectF("system", "Sistema", [["gas", `FORCE GAS (${nf(fc.system.gas || 0)})`], ["oleo", `FORCE OIL (${nf(fc.system.oleo || 0)})`]], s.system) +
        selectF("launch", "Lançamento", [["S", `Só lançamentos (${nf(fc.launch)})`], ["N", "Fora de lançamento"]], s.launch) +
        (pesquisa ? selectF("origem", "Origem: todas", [["catalogo", "Somente catálogo"], ["des", "Somente DESENVOLVIMENTO"], ["rd", "Somente REDESENVOLVIMENTO"]], s.origem) +
          textoF("code", "Código", s.code, "w-36") + selectF("code_type", "Tipo de código", [["oem", "OEM"], ["fornecedor", "Fornecedor"], ["concorrente", "Concorrente"]], s.code_type) +
          selectF("make", "Montadora", L.makes.map(x => [x, x]), s.make) + selectF("model", "Modelo", L.models.map(x => [x, x]), s.model) + selectF("year", "Ano", L.years.map(y => [y, y]), s.year) +
          selectF("axle", "Eixo", [["dianteiro", "Dianteiro"], ["traseiro", "Traseiro"]], s.axle) + selectF("side", "Lado", [["direito", "Direito"], ["esquerdo", "Esquerdo"]], s.side) : "") +
        `<button type="button" id="pclr" class="rounded-lg border border-line bg-card px-3.5 py-2 text-sm font-semibold text-ink hover:bg-slate-500/10">Limpar filtros</button>`;
    };

    const via = r => (r.via || []).length ? `<div class="mt-1 flex flex-wrap gap-1">${r.via.map(v => `<span class="rounded-lg border border-line px-1.5 py-0.5 text-xs text-mute" title="Código ${esc(v.type)} que casou com a busca"><b class="text-ink">${esc(v.brand || v.type)}</b> ${esc(v.code)}</span>`).join("")}</div>` : "";
    const carregar = async () => {
      const s = F.get(), soRd = pesquisa && (s.origem === "des" || s.origem === "rd");
      $("#pt").innerHTML = soRd ? "" : `<div class="rounded-2xl border border-line bg-card px-5 py-8 text-sm text-mute">Carregando…</div>`; $("#pp").innerHTML = ""; $("#pmeta").innerHTML = "";
      try {
        if (!soRd) {
          const d = await J("/api/products?" + qs({ ...s, page: pg })), pages = Math.max(1, Math.ceil(d.total / d.size)), ativos = Object.keys(s).length;
          $("#pmeta").innerHTML = `<span><b class="text-ink">${nf(d.total)}</b> produto(s)${ativos ? ` · ${ativos} filtro(s) ativo(s)` : ""}${F.restaurado && pg === 1 ? ' · <span class="text-amber-700">filtros da última visita</span>' : ""}</span>
            <a class="rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-blue-700" href="/api/export/${slug}.xlsx?${new URLSearchParams(s)}">⬇ Baixar Excel</a>`;
          $("#pt").innerHTML = TW.table([{ h: "Pos.", r: true }, { h: "Código PERFECT" }, { h: "Descrição", nw: false }, { h: "Família" }, { h: "Sistema" }, { h: "Ø haste", r: true }, { h: "Lmin", r: true }, { h: "Lmax", r: true },
            { h: "FOB (US$)", r: true }, { h: "Aplic.", r: true }, { h: "Códigos", r: true }, { h: "Pend.", r: true }, { h: "Desenho" }], d.rows.map(r => [r.catalog_position ?? '<span class="text-mute">–</span>',
            `<a href="#" class="font-semibold text-blue-600" data-ficha="${r.id}">${esc(r.perfect_code)}</a>${r.is_launch === "S" ? " " + badge("lançamento", "green") : ""}`,
            `<div class="min-w-[16rem] max-w-[26rem]">${esc(r.description || "")}${via(r)}</div>`, esc(familia(r.family)) || '<span class="text-mute">–</span>', sistema(r.system_type), mm(r.rod_diameter_mm), mm(r.lmin_mm), mm(r.lmax_mm),
            r.fob != null ? `${nf(r.fob, 2)}${r.fob_supplier ? ` <span class="text-xs text-mute">${esc(r.fob_supplier)}</span>` : ""}` : '<span class="text-mute">–</span>', nf(r.apps), nf(r.ncodes), r.pend ? badge(r.pend, "amber") : "",
            `<span data-dw="${esc(r.perfect_code)}"></span>`]), { h: "max-h-[65vh]" });
          dwFill($("#pt"));
          $("#pp").innerHTML = pages > 1 ? `<button type="button" data-p="${pg - 1}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button type="button" data-p="${pg + 1}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
        }
        if (pesquisa) await emDesenvolvimento(s);
      } catch (e) { $("#pt").innerHTML = notice(esc(e.message), "red"); }
    };

    // Pesquisa: itens em DESENVOLVIMENTO / REDESENVOLVIMENTO que casam com a busca ou a aplicação
    const emDesenvolvimento = async s => {
      const o = s.origem || "", want = o === "" ? ["des", "rd"] : o === "catalogo" ? [] : [o], f = { q: s.q, make: s.make, model: s.model, year: s.year };
      if (!want.length || (o === "" && !s.q && !s.make && !s.model && !s.year)) { $("#px").innerHTML = ""; return; }
      const parts = await Promise.all(want.map(k => J(`/api/rd/${k}?` + qs(f)).then(d => [k, d])));
      $("#px").innerHTML = parts.map(([k, d]) => TW.card(`${badge(RD_LAB[k], k === "des" ? "blue" : "green")} <span class="ml-1">${nf(d.total)} item(ns)</span>`,
        d.rows.length ? TW.table([{ h: "Código" }, { h: "Descrição", nw: false }, { h: "Veículo(s)", nw: false }, { h: "Status" }, { h: "Catálogo" }], d.rows.slice(0, 12).map(r => [
          `<a href="#" class="font-semibold text-blue-600" data-rd="${k}" data-code="${esc(r.code)}">${esc(r.code)}</a>`, `<span class="block max-w-[22rem] truncate" title="${esc(r.description || "")}">${esc(r.description || "")}</span>`,
          `<span class="block max-w-[18rem] truncate" title="${esc(r.vehicles || "")}">${esc(r.vehicles || "")}</span>`, esc(r.statuses || "–"), r.product_id ? `<a href="#" class="text-blue-600" data-ficha="${r.product_id}">abrir ficha</a>` : '<span class="text-mute">–</span>']), { h: "max-h-[40vh]" })
          : empty("Nenhum item."),
        `<a class="rounded-lg border border-line bg-card px-3 py-1.5 text-sm font-semibold text-ink hover:bg-slate-500/10" href="/${k === "des" ? "desenvolvimento" : "redesenvolvimento"}?${qs(f)}">Ver todos</a>`)).join("");
    };

    const aplicar = (patch, logo = false) => { if (patch) F.set(patch); pg = 1; desenharAtalhos(); clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 300); };
    const modelos = async () => { const m = F.get().make; L.models = (await J("/api/filters" + (m ? "?make=" + encodeURIComponent(m) : ""))).models; if (F.get().model && !L.models.includes(F.get().model)) F.set({ model: "" }); };
    $("#pf").addEventListener("input", async e => {
      const n = e.target.name; if (!n) return;
      if (n === "make") { F.set({ make: e.target.value }); await modelos(); desenharFiltros(); }
      aplicar({ [n]: e.target.value }, e.target.tagName === "SELECT");
    });
    $("#pf").addEventListener("submit", e => e.preventDefault());
    $("#pf").addEventListener("click", async e => { if (e.target.id !== "pclr") return; const tinha = F.get().make; F.clear(); if (pesquisa && tinha) await modelos(); desenharFiltros(); aplicar(null, true); });
    root.addEventListener("click", e => { const b = e.target.closest("[data-tg]"); if (!b) return; F.toggle(b.dataset.tg, b.dataset.v); desenharFiltros(); aplicar(null, true); });
    $("#pp").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; carregar(); scrollTo(0, 0); } });

    (async () => {
      fc = await J("/api/products/facets");
      if (pesquisa) { const f = await J("/api/filters"); L = { makes: f.makes, models: f.models, years: f.years.map(String) }; if (F.get().make) await modelos(); }
      desenharKpis(); desenharAtalhos(); desenharFiltros(); await carregar();
    })().catch(fail);
  }
  PSD.tela("produtos", () => lista("produtos", false));
  PSD.tela("pesquisa", () => lista("pesquisa", true));
})();
