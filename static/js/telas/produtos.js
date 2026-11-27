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

  function lista(slug, pesquisa, host = root) {
    const F = TW.filtros(slug, pesquisa ? PESQ : BASE); let pg = 1, fc = null, L = { makes: [], models: [], years: [] }, timer;
    host.innerHTML = `<div class="flex flex-col gap-5">
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
          $("#pmeta").innerHTML = `<b class="text-ink">${nf(d.total)}</b> produto(s)${ativos ? `, ${ativos} filtro(s) ativo(s)` : ""}`;
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
  /* update 8: abas de Produtos e códigos — «Catálogo» (a lista de sempre) e «Inmetro». A aba fica na URL (?aba=inmetro); trocar não recarrega a página */
  function produtos() {
    const aba = new URLSearchParams(location.search).get("aba") === "inmetro" ? "inmetro" : "catalogo";
    root.innerHTML = `<div class="flex flex-col gap-5"><div><div class="psd-seg" role="tablist" aria-label="Abas de Produtos e códigos">${[["catalogo", "Catálogo"], ["inmetro", "Inmetro"]].map(([v, l]) =>
      `<button type="button" role="tab" data-paba="${v}" aria-selected="${v === aba}" aria-pressed="${v === aba}">${l}</button>`).join("")}</div></div><div id="pcorpo"></div></div>`;
    root.querySelector("[data-paba]").parentElement.onclick = e => { const b = e.target.closest("[data-paba]"); if (!b || b.dataset.paba === aba) return;
      const u = new URLSearchParams(location.search); b.dataset.paba === "inmetro" ? u.set("aba", "inmetro") : u.delete("aba");
      history.replaceState(null, "", location.pathname + (u.toString() ? "?" + u : "")); produtos(); };
    if (aba === "inmetro") inmetroAba($("#pcorpo")); else lista("produtos", false, $("#pcorpo"));
  }

  /* update 8 · aba Inmetro: catálogo × certificados (ZS e E-WIN), códigos só no certificado, DES/R-D em andamento e divergências (inmetro.py) */
  function inmetroAba(host) {
    const F = TW.filtros("inmetro", ["aba", "sit", "familia", "forn", "iq"]); F.set({ aba: "inmetro" }); let pg = 1, d = null, timer;          /* «aba» fica na URL junto com os filtros */
    host.innerHTML = `<div class="flex flex-col gap-5"><div id="ik" class="grid grid-cols-2 gap-4 lg:grid-cols-5"></div><div id="ifam" class="psd-ifams"></div>
      <div id="ibar"></div><section aria-label="Situação"><div id="igr" class="psd-subfs"></div></section><div id="imeta" class="text-sm text-mute"></div><div id="it"></div>
      <div id="ip" class="flex items-center justify-center gap-3 text-sm text-mute"></div></div>`;
    const api = () => { const s = F.get(); return { sit: s.sit || "", familia: s.familia || "", forn: s.forn || "", q: s.iq || "" }; };
    const SIT = { dois: "Nos dois fornecedores", zs: "Só ZS", ewin: "Só E-WIN", sem: "Sem certificado", so_cert: "Só no certificado", rd_aprovacao: "Em aprovação", rd_com_num: "Com nº Inmetro",
      rd_fora: "Fora do certificado", div_familia: "Família", div_haste: "Ø da haste", div_ean: "Código de barras" };
    const GRUPOS = [["Catálogo", ["dois", "zs", "ewin", "sem"]], ["Fora do catálogo", ["so_cert"]], ["DES/R-D em andamento", ["rd_aprovacao", "rd_com_num", "rd_fora"]], ["Divergências", ["div_familia", "div_haste", "div_ean"]]];
    const COR = { dois: "ok", zs: "mu", ewin: "mu", sem: "", so_cert: "mu", rd_aprovacao: "", rd_com_num: "ok", rd_fora: "mu", div_familia: "", div_haste: "", div_ean: "" };
    const FORN = { dois: "Os dois", zs: "Só ZS", ewin: "Só E-WIN", nenhum: "Nenhum" }, NOMES = { sit: "Situação", familia: "Família", forn: "Fornecedor do certificado", iq: "Busca" };
    const SELO = { dois: ["Nos dois", " ok"], zs: ["Só ZS", ""], ewin: ["Só E-WIN", ""], sem: ["Sem certificado", " am"], so_cert: ["Só no certificado", ""], aprovacao: ["Em aprovação", " am"], com_num: ["Com nº Inmetro", " ok"], fora: ["Fora do certificado", ""] };
    const DIV = { familia: "família", haste: "Ø da haste", ean: "código de barras" };
    const mu = '<span class="text-mute">–</span>';
    const desenhar = () => {
      const { aba: _a, ...s } = F.get(), K = d.kpi;
      $("#ik").innerHTML = kpi("Catálogo com certificado", nf(K.com_cert), `${nf(K.dois)} nos dois fornecedores`, "blue") + kpi("Catálogo sem certificado", nf(K.sem), "em nenhum fornecedor", K.sem ? "amber" : "slate")
        + kpi("Só no certificado", nf(K.so_cert), "códigos fora do catálogo", "slate") + kpi("DES/R-D em aprovação", nf(K.rd_aprovacao), `${nf(K.rd_fora)} códigos fora do certificado`, K.rd_aprovacao ? "amber" : "slate")
        + kpi("Divergências", nf(K.div), "catálogo × certificado", K.div ? "amber" : "slate");
      $("#ifam").innerHTML = d.familias.map(f => { const com = f.dois + f.um, t = f.total || 1;
        return `<button type="button" class="psd-ifam" data-fam="${esc(f.fam)}" aria-pressed="${s.familia === f.fam}"><span class="n">${esc(familia(f.fam))}</span><span class="q">${nf(com)}<small>de ${nf(f.total)} com certificado</small></span>
          <span class="bar" aria-hidden="true"><i style="width:${100 * f.dois / t}%;background:var(--chart-1)"></i><i style="width:${100 * f.um / t}%;background:var(--chart-3)"></i><i style="width:${100 * f.sem / t}%;background:var(--pf-orange)"></i></span>
          <span class="ce">ZS <b>${esc(f.certs.ZS || "sem certificado")}</b><br>E-WIN <b>${esc(f.certs["E-WIN"] || "sem certificado")}</b>${f.sem ? `<br><span class="am">${nf(f.sem)} sem certificado</span>` : ""}</span></button>`; }).join("");
      const val = (k, v) => k === "sit" ? (v.startsWith("div_") ? "divergência de " + SIT[v].toLowerCase() : v.startsWith("rd_") ? "DES/R-D " + SIT[v].toLowerCase() : SIT[v] || v) : k === "familia" ? familia(v) : k === "forn" ? FORN[v] || v : v;
      TW.pintarBarra($("#ibar"), {
        busca: { valor: s.iq, ph: "Código, descrição ou nº Inmetro" },
        principais: [{ k: "familia", rotulo: "Família", tipo: "lista", atual: s.familia || "", opcoes: [{ v: "", l: "Todas" }, ...d.familia_opc.map(x => ({ v: x.v, l: familia(x.v), n: x.n }))] },
                     { k: "forn", rotulo: "Fornecedor do certificado", tipo: "lista", atual: s.forn || "", opcoes: [{ v: "", l: "Todos" }, ...d.forn_opc.map(x => ({ v: x.v, l: FORN[x.v], n: x.n }))] }],
        etiquetas: TW.etiquetas(s, NOMES, val),
        acoes: TW.botao("Baixar Excel", { href: `/api/export/inmetro.xlsx?${qs(api())}`, icone: "download" }) });
      $("#igr").innerHTML = GRUPOS.map(([g, ks]) => `<div class="psd-subf"><span class="g">${g}</span><div class="cs">${ks.map(k => { const on = s.sit === k, n = d.chips[k] || 0;
        return `<button type="button" data-sit="${k}" aria-pressed="${on}" class="psd-subc${!n && !on ? " zero" : ""}"><i class="psd-sd ${COR[k]}"></i><span class="v">${SIT[k]}</span><span class="n">${nf(n)}</span></button>`; }).join("")}</div></div>`).join("");
      const ativos = Object.keys(s).length, pages = Math.max(1, Math.ceil(d.total / d.size));
      $("#imeta").innerHTML = `<b class="text-ink">${nf(d.total)}</b> código(s)${ativos ? `, ${ativos} filtro(s) ativo(s)` : ""}`;
      $("#it").innerHTML = d.rows.length ? TW.table([{ h: "Código" }, { h: "Situação" }, { h: "Família" }, { h: "Nº ZS" }, { h: "Nº E-WIN" }, { h: "Código de barras" }, { h: "Descrição padronizada", nw: false }], d.rows.map(l => {
        const sel = SELO[l.sit] || [l.sit, ""], rdl = l.grupo === "rd";
        const cod = rdl ? `<a href="#" class="font-semibold text-blue-600" data-rd="${l.tipo === "DES" ? "des" : "rd"}" data-code="${esc(l.code)}">${esc(l.code)}</a> ${badge(l.tipo, l.tipo === "DES" ? "blue" : "green")}` : `<a class="font-semibold text-blue-600" href="/item/${encodeURIComponent(l.code)}">${esc(l.code)}</a>`;
        const eans = [...new Set([l.ean_zs, l.ean_ew].filter(Boolean))];
        return [`${cod}${l.descr ? `<span class="block max-w-[16rem] truncate text-xs text-mute" title="${esc(l.descr)}">${esc(l.descr)}</span>` : ""}`,
          `<span class="psd-inm${sel[1]}">${sel[0]}</span>${rdl && l.status ? `<span class="block text-xs text-mute">${esc(l.status)}</span>` : ""}${l.num_srv ? `<span class="block text-xs text-mute">nº ${esc(l.num_srv)}, do servidor</span>` : ""}${l.div.length ? `<span class="psd-dv">diverge: ${l.div.map(x => DIV[x]).join(", ")}</span>` : ""}`,
          `${esc(familia(l.fam)) || mu}${l.fam_cert.length ? `<span class="psd-dv">certificado: ${esc(l.fam_cert.map(familia).join(", "))}</span>` : ""}`,
          `<span class="tabular-nums">${esc(l.num_zs || "–")}</span>`, `<span class="tabular-nums" ${l.outros && l.outros.length ? `title="Também em: ${esc(l.outros.join(", "))}"` : ""}>${esc(l.num_ew || "–")}</span>`,
          `<span class="tabular-nums">${eans.length ? eans.map(esc).join("<br>") : mu}</span>${l.div.includes("ean") ? `<span class="psd-dv">catálogo: ${esc(l.ean)}</span>` : ""}`,
          `<span title="${esc(l.orig || "")}">${esc(l.pad_txt || "–")}</span>${l.div.includes("haste") ? `<span class="psd-dv">catálogo: Ø ${nf(l.haste_cat, l.haste_cat % 1 ? 1 : 0)} mm</span>` : ""}`]; }), { h: "max-h-[65vh]" }) : empty("Nenhum código com estes filtros.");
      $("#ip").innerHTML = pages > 1 ? `<button type="button" data-p="${pg - 1}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button type="button" data-p="${pg + 1}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
    };
    let seq = 0;
    const carregar = async () => { const meu = ++seq;
      try { const r = await J("/api/inmetro?" + qs({ ...api(), page: pg })); if (meu !== seq) return; d = r; desenhar(); } catch (e) { $("#it").innerHTML = notice(esc(e.message), "red"); } };
    const aplicar = (patch, logo = true) => { if (patch) F.set(patch); pg = 1; clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 250); };
    TW.ligarBarra($("#ibar"), { set: (k, v) => aplicar({ [k]: v }), busca: t => aplicar({ iq: t }, false), limpar: () => { F.clear(); F.set({ aba: "inmetro" }); aplicar(); } });
    $("#ifam").addEventListener("click", e => { const b = e.target.closest("[data-fam]"); if (b) aplicar({ familia: F.get().familia === b.dataset.fam ? "" : b.dataset.fam }); });
    $("#igr").addEventListener("click", e => { const b = e.target.closest("[data-sit]"); if (b) aplicar({ sit: F.get().sit === b.dataset.sit ? "" : b.dataset.sit }); });
    $("#ip").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; carregar(); scrollTo(0, 0); } });
    $("#it").innerHTML = TW.carregando("Lendo os certificados…");
    carregar();
  }
  PSD.tela("produtos", produtos);
  PSD.tela("pesquisa", () => lista("pesquisa", true));
})();
