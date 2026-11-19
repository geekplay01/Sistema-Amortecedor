/* Telas · Produtos e Pesquisa — visual Tailwind (etapa 16).
   Filtros do catálogo (planilha CatalogoAMD prevalece): Família, Ø da haste, Sistema (FORCE GAS / FORCE OIL), Lançamento, Linha e Híbrido/elétrico (etapa 17), com atalhos que ligam/desligam.
   Busca por código PERFECT, OEM ou de concorrente (com ou sem pontuação); a linha mostra qual referência casou. Filtros na URL (PSDTW.filtros).
   Pesquisa = Produtos + aplicação (montadora/modelo/ano/eixo/lado), código por tipo e itens em DES / R-D. Ficha: clique no código (data-ficha → PSD.openFicha). */
(function () {
  const { $, esc, J, qs, root, fail, SYS, dwFill } = PSD;
  const TW = window.PSDTW, { nf, badge, kpi, notice, empty } = TW;
  const BASE = ["q", "family", "rod", "system", "launch", "linha", "hibrido"], PESQ = [...BASE, "origem", "code", "code_type", "make", "model", "year", "axle", "side"];
  const mm = v => v == null ? '<span class="text-mute">–</span>' : nf(v, v % 1 ? 1 : 0);
  const sistema = s => s ? badge(SYS[s], s === "gas" ? "blue" : "amber") : '<span class="text-mute">–</span>';
  const familia = f => f ? f.charAt(0) + f.slice(1).toLowerCase() : "";
  const linha = l => familia(String(l || "").replace(/^LINHA\s+/, ""));          // «LINHA PICK-UP E UTILITÁRIOS» → «Pick-up e utilitários»
  const RD_LAB = { des: "DESENVOLVIMENTO", rd: "REDESENVOLVIMENTO" };

  function lista(slug, pesquisa) {
    const F = TW.filtros(slug, pesquisa ? PESQ : BASE); let pg = 1, fc = null, L = { makes: [], models: [], years: [] }, timer;
    root.innerHTML = `<div class="flex flex-col gap-5">
      <p class="m-0 text-sm text-mute">${pesquisa ? "<b>Digite o código PERFECT, OEM ou de um CONCORRENTE</b> (com ou sem ponto/hífen: 16.470 = 16470) ou uma aplicação (ex.: strada 2012 dianteiro). Procura no catálogo e nos itens em DESENVOLVIMENTO e REDESENVOLVIMENTO." : "Na ordem do catálogo (planilha CatalogoAMD, que prevalece). A busca aceita código PERFECT, OEM ou de concorrente — a linha mostra qual referência casou."}</p>
      ${pesquisa ? "" : '<div id="pk" class="grid grid-cols-2 gap-4 lg:grid-cols-4"></div>'}
      <div id="pbar"></div>
      <div id="pmeta" class="text-sm text-mute"></div>
      <div id="pt"></div><div id="pp" class="flex items-center justify-center gap-3 text-sm text-mute"></div>
      <div id="px" class="flex flex-col gap-4"></div>
    </div>`;

    const desenharKpis = () => {
      if (pesquisa) return;
      $("#pk").innerHTML = kpi("Itens no catálogo", nf(fc.catalogo), `${nf(fc.total)} produtos cadastrados`, "blue") + kpi("FORCE GAS", nf(fc.system.gas || 0), "sistema a gás", "blue") +
        kpi("FORCE OIL", nf(fc.system.oleo || 0), fc.system.nd ? `${nf(fc.system.nd)} sem sistema informado` : "sistema a óleo", "amber") + kpi("Lançamentos", nf(fc.launch), "coluna Lançamento da planilha", "green");
    };
    /* barra de filtros (etapa 19 · Q6). Produtos: Linha, Família e Sistema à vista. Pesquisa: Montadora, Modelo e Ano à vista. O resto em «Mais filtros». */
    const SISL = { gas: "FORCE GAS", oleo: "FORCE OIL" }, LANL = { S: "Só lançamentos", N: "Fora de lançamento" }, HIBL = { S: "Sim", N: "Não", nd: "Não informado" };
    const ORIL = { catalogo: "Somente catálogo", des: "Somente DESENVOLVIMENTO", rd: "Somente REDESENVOLVIMENTO" }, TIPL = { oem: "OEM", fornecedor: "Fornecedor", concorrente: "Concorrente" };
    const AXL = { dianteiro: "Dianteiro", traseiro: "Traseiro" }, SDL = { direito: "Direito", esquerdo: "Esquerdo" };
    const NOMES = { make: "Montadora", model: "Modelo", year: "Ano", linha: "Linha", family: "Família", system: "Sistema", rod: "Ø haste", launch: "Lançamento", hibrido: "Híbrido ou elétrico",
      origem: "Origem", code_type: "Tipo de código", code: "Código", axle: "Eixo", side: "Lado", q: "Busca" };
    let maisAberto = false;
    const desenharAtalhos = () => {};          // os atalhos agora ficam na própria barra
    const desenharFiltros = () => {
      const s = F.get(), todos = [{ v: "", l: "Todos" }];
      const fLinha = { k: "linha", rotulo: "Linha", atual: s.linha || "", opcoes: [...TW.ops(fc.linha, linha), { v: "sem", l: "Sem linha informada" }] };
      const fFam = { k: "family", rotulo: "Família", atual: s.family || "", opcoes: TW.ops(fc.family, familia) };
      const fSis = { k: "system", rotulo: "Sistema", atual: s.system || "", opcoes: [{ v: "gas", l: SISL.gas, n: fc.system.gas || 0 }, { v: "oleo", l: SISL.oleo, n: fc.system.oleo || 0 }] };
      const resto = [{ k: "rod", rotulo: "Ø haste (mm)", atual: s.rod || "", opcoes: fc.rod.map(x => ({ v: x.v, l: `${mm(x.v)} mm`, n: x.n })) },
                     { k: "launch", rotulo: "Lançamento", atual: s.launch || "", opcoes: [{ v: "S", l: LANL.S, n: fc.launch }, { v: "N", l: LANL.N }] },
                     { k: "hibrido", rotulo: "Híbrido ou elétrico", atual: s.hibrido || "", opcoes: Object.entries(HIBL).map(([v, l]) => ({ v, l, n: fc.hibrido[v] || 0 })) }];
      const lista_ = f => ({ ...f, tipo: "lista", opcoes: [...todos, ...f.opcoes] });
      const principais = pesquisa ? [lista_({ k: "make", rotulo: "Montadora", atual: s.make || "", opcoes: L.makes.map(x => ({ v: x, l: x })) }),
                                     lista_({ k: "model", rotulo: "Modelo", atual: s.model || "", opcoes: L.models.map(x => ({ v: x, l: x })) }),
                                     lista_({ k: "year", rotulo: "Ano", atual: s.year || "", opcoes: L.years.map(y => ({ v: y, l: y })) })]
                                  : [lista_(fLinha), lista_(fFam), lista_(fSis)];
      const mais = pesquisa ? [{ k: "axle", rotulo: "Eixo", atual: s.axle || "", opcoes: Object.entries(AXL).map(([v, l]) => ({ v, l })) }, { k: "side", rotulo: "Lado", atual: s.side || "", opcoes: Object.entries(SDL).map(([v, l]) => ({ v, l })) },
                              { k: "origem", rotulo: "Origem", atual: s.origem || "", opcoes: Object.entries(ORIL).map(([v, l]) => ({ v, l })) }, { k: "code_type", rotulo: "Tipo de código", atual: s.code_type || "", opcoes: Object.entries(TIPL).map(([v, l]) => ({ v, l })) },
                              fLinha, fFam, fSis, ...resto] : resto;
      const val = (k, v) => ({ linha: linha(v), family: familia(v), system: SISL[v], launch: LANL[v], hibrido: HIBL[v], origem: ORIL[v], code_type: TIPL[v], axle: AXL[v], side: SDL[v], rod: v + " mm" })[k] || v;
      TW.pintarBarra($("#pbar"), {
        busca: { valor: s.q, ph: pesquisa ? "Código PERFECT, OEM, concorrente, veículo, ano…" : "Código PERFECT, OEM, concorrente, descrição…" },
        principais, mais, aberto: maisAberto,
        atalhos: [{ k: "launch", v: "S", l: "Lançamentos", n: fc.launch, on: s.launch === "S", forte: true }, { k: "system", v: "gas", l: "FORCE GAS", n: fc.system.gas || 0, on: s.system === "gas" },
                  { k: "system", v: "oleo", l: "FORCE OIL", n: fc.system.oleo || 0, on: s.system === "oleo" }, { k: "hibrido", v: "S", l: "Híbrido ou elétrico", n: fc.hibrido.S || 0, on: s.hibrido === "S", forte: true }],
        etiquetas: TW.etiquetas(s, NOMES, val),
        acoes: TW.botao("Baixar Excel", { href: `/api/export/${slug}.xlsx?${new URLSearchParams(s)}`, icone: "download" })
      });
    };

    const via = r => (r.via || []).length ? `<div class="mt-1 flex flex-wrap gap-1">${r.via.map(v => `<span class="rounded-lg border border-line px-1.5 py-0.5 text-xs text-mute" title="Código ${esc(v.type)} que casou com a busca"><b class="text-ink">${esc(v.brand || v.type)}</b> ${esc(v.code)}</span>`).join("")}</div>` : "";
    const carregar = async () => {
      const s = F.get(), soRd = pesquisa && (s.origem === "des" || s.origem === "rd");
      $("#pt").innerHTML = soRd ? "" : `<div class="rounded-2xl border border-line bg-card px-5 py-8 text-sm text-mute">Carregando…</div>`; $("#pp").innerHTML = ""; $("#pmeta").innerHTML = "";
      try {
        if (!soRd) {
          const d = await J("/api/products?" + qs({ ...s, page: pg })), pages = Math.max(1, Math.ceil(d.total / d.size)), ativos = Object.keys(s).length;
          $("#pmeta").innerHTML = `<b class="text-ink">${nf(d.total)}</b> produto(s)${ativos ? ` · ${ativos} filtro(s) ativo(s)` : ""}`;
          $("#pt").innerHTML = TW.table([{ h: "Código PERFECT" }, { h: "Descrição", nw: false }, { h: "Linha" }, { h: "Família" }, { h: "Sistema" }, { h: "Ø haste", r: true }, { h: "Lmin", r: true }, { h: "Lmax", r: true },
            { h: "FOB (US$)", r: true }, { h: "Aplic.", r: true }, { h: "Códigos", r: true }, { h: "Pend.", r: true }, { h: "Desenho" }], d.rows.map(r => [`<a href="#" class="font-semibold text-blue-600" data-ficha="${r.id}">${esc(r.perfect_code)}</a>${r.is_launch === "S" ? " " + badge("lançamento", "green") : ""}${r.hybrid === "S" ? " " + badge("híbrido/elétrico", "violet") : ""}`,
            `<div class="min-w-[16rem] max-w-[26rem]">${esc(r.description || "")}${via(r)}</div>`, esc(linha(r.catalog_line)) || '<span class="text-mute">–</span>', esc(familia(r.family)) || '<span class="text-mute">–</span>', sistema(r.system_type), mm(r.rod_diameter_mm), mm(r.lmin_mm), mm(r.lmax_mm),
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

    const aplicar = (patch, logo = false) => { if (patch) F.set(patch); pg = 1; desenharFiltros(); clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 300); };
    const modelos = async () => { const m = F.get().make; L.models = (await J("/api/filters" + (m ? "?make=" + encodeURIComponent(m) : ""))).models; if (F.get().model && !L.models.includes(F.get().model)) F.set({ model: "" }); };
    TW.ligarBarra($("#pbar"), {
      set: async (k, v) => { if (k === "make" && pesquisa) { F.set({ make: v }); await modelos(); } aplicar({ [k]: v }, true); },
      busca: t => aplicar({ q: t }, true),
      limpar: async () => { const tinha = F.get().make; F.clear(); if (pesquisa && tinha) await modelos(); aplicar(null, true); },
      mais: ab => { maisAberto = ab; } });
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
