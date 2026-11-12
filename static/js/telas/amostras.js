/* Tela · Compra de amostras — visual Tailwind (etapa 16). Duas abas (na URL: tab=pendentes|pedidos):
   · Sugestões de compra: DES/R-D com «Pendente compras», sem amostra comprada e fora do catálogo (purchases.pending); menor preço na web e «Criar pedido».
   · Pedidos de amostra: kanban por etapa (queries.samples); atalhos «Para enviar» / «Pendente fornecedor» (flag), fornecedor, mês e lado.
   Filtros na URL e lembrados (PSDTW.filtros); Excel com os filtros da aba. O formulário do pedido (diálogo) segue o estilo antigo. */
(function () {
  const { $, $$, esc, J, post, qs, root, fail, dlg, dwBlocks, dwFill, NEW } = PSD;
  const TW = window.PSDTW, { nf, brl, badge, kpi, notice, empty } = TW;
  const ABA = { pendentes: ["q", "kind"], pedidos: ["q", "supplier", "month", "side", "flag"] };
  const SDL = { direito: "LD", esquerdo: "LE", ambos: "LD/LE" };
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500";
  const botao = "rounded-lg border border-line bg-card px-3 py-1.5 text-sm font-semibold text-ink hover:bg-slate-500/10";
  const chip = (attrs, label, on, n, forte = false) => `<button type="button" ${attrs} aria-pressed="${on}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${on ? "border-blue-500 bg-blue-500 text-white" : forte ? "border-amber-500 bg-amber-500/10 text-ink hover:bg-amber-500/20" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${label}${n != null ? ` · ${nf(n)}` : ""}</button>`;
  const selectF = (name, rotulo, opts, cur) => `<select name="${name}" class="${campo} max-w-[13rem]" title="${esc(rotulo)}"><option value="">${esc(rotulo)}</option>${opts.map(([v, l]) => `<option value="${esc(v)}" ${String(v) === String(cur ?? "") ? "selected" : ""}>${esc(l)}</option>`).join("")}</select>`;
  const usd = v => "US$ " + Number(v || 0).toLocaleString("pt-BR", { maximumFractionDigits: 2 });
  const pager = (pg, pages) => pages > 1 ? `<button type="button" data-p="${pg - 1}" class="${botao}" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button type="button" data-p="${pg + 1}" class="${botao}" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
  const mlUrl = (brand, code) => "https://lista.mercadolivre.com.br/" + encodeURIComponent(`${brand && brand !== "OEM" ? brand + " " : ""}${code} amortecedor`.trim().toLowerCase().replace(/\s+/g, "-")) + "_OrderId_PRICE*ASC_ITEM*CONDITION_2230284";
  const topRefs = cross => { const com = (cross || []).filter(c => c.brand && !["OEM", "PERFECT"].includes(c.brand)); return (com.length ? com : cross || []).slice(0, 2); };
  const link = (href, t) => `<a class="text-xs font-semibold text-blue-600" href="${esc(href)}" target="_blank" rel="noopener">${t}</a>`;

  async function amostras() {
    const F = TW.filtros("amostras", ["tab", ...new Set([...ABA.pendentes, ...ABA.pedidos])]);
    let data = null, pend = null, rows = [], pg = 1, timer, nPend = null;
    const aba = () => F.get().tab === "pedidos" ? "pedidos" : "pendentes", filtrosDa = () => { const s = F.get(); return Object.fromEntries(ABA[aba()].filter(k => s[k]).map(k => [k, s[k]])); };
    root.innerHTML = `<div class="flex flex-col gap-5">
      <div id="atab" class="flex flex-wrap items-center gap-2"></div>
      <p id="aintro" class="m-0 text-sm text-mute"></p>
      <div id="ak" class="grid grid-cols-2 gap-4 lg:grid-cols-4"></div>
      <div id="aq" class="flex flex-wrap items-center gap-2"></div>
      <form id="af" class="flex flex-wrap items-center gap-2" autocomplete="off"></form>
      <div id="ameta" class="flex flex-wrap items-center justify-between gap-3 text-sm text-mute"></div>
      <div id="abody"></div><div id="ap" class="flex items-center justify-center gap-3 text-sm text-mute"></div>
    </div>`;
    const meta = async () => data || (data = await J("/api/samples?" + qs(filtrosDa())));     // etapas e fornecedores (formulário) mesmo vindo da aba de sugestões

    const desenharAbas = () => { const a = aba(), b = (k, l, n) => `<button type="button" data-tab="${k}" aria-pressed="${a === k}" class="rounded-lg border px-4 py-2 text-sm font-semibold ${a === k ? "border-blue-500 bg-blue-500 text-white" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${l}${n != null ? ` · ${nf(n)}` : ""}</button>`;
      $("#atab").innerHTML = b("pendentes", "Sugestões de compra", nPend) + b("pedidos", "Pedidos de amostra", data && aba() === "pedidos" ? data.totals.n : null); };
    const desenharFiltros = () => {
      const s = F.get();
      if (aba() === "pendentes") {
        $("#aintro").innerHTML = 'Itens em <b class="text-ink">DESENVOLVIMENTO / REDESENVOLVIMENTO</b> marcados <b class="text-ink">PENDENTE COMPRAS</b>, sem amostra comprada, fora do catálogo e com status diferente de ITEM RECEBIDO (só Amortecedor). Cada referência abre a consulta do menor preço; <b class="text-ink">Buscar menor preço</b> traz o anúncio mais barato (unitário ou par/kit).';
        $("#af").innerHTML = `<input name="q" type="search" value="${esc(s.q || "")}" placeholder="Buscar código, descrição, veículo…" class="${campo} min-w-[16rem] flex-1">` +
          selectF("kind", "DES e R-D", [["des", "Somente DESENVOLVIMENTO"], ["rd", "Somente REDESENVOLVIMENTO"]], s.kind) + `<button type="button" id="aclr" class="${botao} py-2">Limpar filtros</button>`;
      } else {
        $("#aintro").innerHTML = 'Pedidos de amostra por etapa. Use ◀ ▶ para mudar a etapa; ao chegar em <b class="text-ink">Chegou</b>, o item entra no <a class="font-semibold text-blue-600" href="/envio">Envio de amostra</a> como «Pendente projeto».';
        const d = data || { suppliers: [], months: [] };
        $("#af").innerHTML = `<input name="q" type="search" value="${esc(s.q || "")}" placeholder="Buscar código, SC, aplicação, fornecedor…" class="${campo} min-w-[16rem] flex-1">` +
          selectF("supplier", "Fornecedor", d.suppliers.map(x => [x, x]), s.supplier) + selectF("month", "Mês", d.months.map(x => [x, x]), s.month) +
          selectF("side", "Lado", [["direito", "Direito (LD)"], ["esquerdo", "Esquerdo (LE)"], ["ambos", "Ambos (LD/LE)"]], s.side) +
          `<button type="button" id="aclr" class="${botao} py-2">Limpar filtros</button><button type="button" id="anew" class="rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-blue-700">+ Nova amostra</button>`;
      }
    };
    const metaLinha = (total, rotulo, xlsx) => { const n = Object.keys(filtrosDa()).length;
      $("#ameta").innerHTML = `<span><b class="text-ink">${nf(total)}</b> ${rotulo}${n ? ` · ${n} filtro(s) ativo(s)` : ""}${F.restaurado && pg === 1 ? ' · <span class="text-amber-700">filtros da última visita</span>' : ""}</span>
        <a class="rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-blue-700" href="/api/export/${xlsx}.xlsx?${new URLSearchParams(filtrosDa())}">⬇ Baixar Excel</a>`; };

    // ---------- Sugestões de compra ----------
    const carregarPendentes = async () => {
      const s = filtrosDa(), d = await J("/api/purchases/pending?" + qs({ ...s, page: pg })), sm = d.summary, pages = Math.max(1, Math.ceil(d.total / d.size)); pend = d; rows = d.rows;
      if (!s.q && !s.kind) nPend = sm.total; desenharAbas();
      $("#ak").innerHTML = kpi("Sugestões de compra", nf(sm.total), "sem amostra comprada", "amber") + kpi("Com referência cruzada", nf(sm.com_referencia), "dá para cotar já", "green") +
        kpi("Sem referência", nf(sm.total - sm.com_referencia), "buscar a referência antes de cotar", "slate") + kpi("Marcadas «Pendente compras»", nf(sm.pend_compras), "sub status do servidor ou marcação manual", "blue");
      $("#aq").innerHTML = `<span class="mr-1 text-xs font-semibold uppercase tracking-wide text-mute">Atalhos</span>` + chip('data-tg="kind" data-v="des"', "DESENVOLVIMENTO", s.kind === "des") + chip('data-tg="kind" data-v="rd"', "REDESENVOLVIMENTO", s.kind === "rd");
      metaLinha(d.total, "sugestão(ões)", "pendente_compras");
      $("#abody").innerHTML = TW.table([{ h: "Código" }, { h: "Descrição / veículos", nw: false }, { h: "Status", nw: false }, { h: "Referência cruzada (abre a consulta)", nw: false }, { h: "Menor preço", nw: false }, { h: "" }], d.rows.map((r, i) => {
        const k = r.suggestion === "DESENVOLVIMENTO" ? "des" : "rd", refs = topRefs(r.cross);
        const cr = r.cross.slice(0, 6).map(c => `<a class="mb-1 mr-1 inline-flex items-center gap-1 rounded-full bg-slate-500/15 px-2 py-0.5 text-xs text-ink hover:bg-slate-500/20" target="_blank" rel="noopener" href="${mlUrl(c.brand, c.code)}" title="Abrir a consulta no Mercado Livre, do menor preço"><b>${esc(c.brand || "")}</b> ${esc(c.code)} ↗</a>`).join("") +
          (r.cross.length > 6 ? `<span class="text-xs text-mute" title="${esc(r.cross.slice(6).map(c => (c.brand || "") + " " + c.code).join(" · "))}">+${r.cross.length - 6}</span>` : "");
        return [`<a href="#" class="font-semibold text-blue-600" data-rd="${k}" data-code="${esc(r.code)}">${esc(r.code)}</a><div class="mt-1">${badge(k === "des" ? "DES" : "R-D", k === "des" ? "blue" : "green")}</div>`,
          `<span class="block max-w-[22rem] truncate" title="${esc(r.description || "")}">${esc(r.description || "")}</span><span class="block max-w-[22rem] truncate text-xs text-mute" title="${esc(r.vehicles || "")}">${esc(r.vehicles || "")}</span>`,
          `<span class="text-xs">${esc(r.statuses || "–")}</span>${r.pend_compras ? `<div class="mt-1">${badge("pendente compras", "amber")}</div>` : ""}${r.state === "cotacao" ? `<div class="mt-1">${badge("em cotação", "blue")}</div>` : ""}`,
          `<div class="max-w-[24rem]">${cr || '<span class="text-mute">sem referência cruzada</span>'}</div>`, `<div id="pc-${i}" class="min-w-[9rem]">${refs.length ? '<span class="text-mute">–</span>' : '<span class="text-mute">sem referência</span>'}</div>`,
          `${refs.length ? `<button type="button" class="${botao}" data-bp="${i}">Buscar menor preço</button> ` : ""}<button type="button" class="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-blue-700" data-np="${i}">Criar pedido</button>`]; }), { h: "max-h-[65vh]" });
      $("#ap").innerHTML = pager(pg, pages);
    };
    const menorPreco = async (i, btn) => {     // nunca quebra: se a busca falhar, mostra o link da consulta
      const r = rows[i], refs = topRefs(r.cross), cell = $("#pc-" + i), lk = refs[0] ? mlUrl(refs[0].brand, refs[0].code) : null; btn.disabled = true; cell.innerHTML = '<span class="text-mute">buscando…</span>';
      try {
        const d = await post("/api/prices/search", { refs: refs.map(x => ({ brand: x.brand, code: x.code })), limit: 3, strict: true }); r._best = d.best;
        cell.innerHTML = d.best ? `<a class="font-semibold text-blue-600" href="${esc(d.best.url || lk)}" target="_blank" rel="noopener" title="${esc(d.best.title)}">${brl(d.best.price)} ↗</a>${d.best.pair ? " " + badge("par/kit", "amber") : ""}<span class="block text-xs text-mute">${esc(d.best.ref || "")} · ${esc(d.best.source)}${d.best.seller ? " · " + esc(d.best.seller) : ""}</span>${link(d.refs[0].links.mercado_livre, "ver consulta ↗")}`
          : `<span class="block text-mute">sem resposta automática</span>${link(d.refs[0].links.mercado_livre, "abrir consulta no Mercado Livre ↗")}`;
      } catch (e) { cell.innerHTML = `<span class="block text-mute">busca indisponível</span>${lk ? link(lk, "abrir consulta ↗") : ""}`; }
      btn.disabled = false; btn.textContent = "Buscar de novo";
    };

    // ---------- Pedidos de amostra (kanban) ----------
    const cartao = (r, i, n) => {
      const ch = r.quotes.find(q => q.chosen && q.price != null), mut = t => `<div class="text-xs text-mute">${t}</div>`;
      const det = [r.ship_code ? esc(r.ship_code) : "", r.credit_note && r.credit_note !== "-" ? "Credit note " + esc(r.credit_note) : "", r.net_weight != null ? "Líq. " + nf(r.net_weight, 2) + " kg" : "", r.gross_weight != null ? "Bruto " + nf(r.gross_weight, 2) + " kg" : ""].filter(Boolean).join(" · ");
      const envio = r.ship_status ? `<a href="/envio?q=${encodeURIComponent(r.perfect_code || "")}&status=todos" title="Envio de amostra">${badge({ pendente_projeto: "Pendente projeto", enviada: "Enviada" + (r.ship_ex ? " · " + r.ship_ex : ""), finalizada: "Envio finalizado" }[r.ship_status] || r.ship_status, r.ship_status === "enviada" ? "green" : r.ship_status === "pendente_projeto" ? "amber" : "slate")}</a>` : "";
      return `<div class="flex flex-col gap-1 rounded-xl border border-line bg-card p-3 text-sm shadow-sm">
        <div class="flex items-start justify-between gap-2"><b>${r.product_id ? `<a href="#" class="text-blue-600" data-ficha="${r.product_id}">${esc(r.perfect_code)}</a>` : esc(r.perfect_code || "(sem código)")}</b><span class="text-xs text-mute">${esc(r.sc_number ? "SC " + r.sc_number : "")}</span></div>
        ${r.application ? `<div>${esc(r.application)}</div>` : ""}${mut([r.sample_code, r.supplier, r.month].filter(Boolean).map(esc).join(" · "))}
        ${ch || r.quotes.length > 1 ? `<div>${ch ? `<b>${brl(ch.price)}</b>` : ""}${r.quotes.length > 1 ? ` <span class="text-xs text-mute">(${r.quotes.length} cotações)</span>` : ""}</div>` : ""}
        ${r.best_price != null || r.price_usd != null ? mut(`${r.best_price != null ? `Melhor preço <b class="text-ink">${brl(r.best_price)}</b>` : ""}${r.price_usd != null ? ` · <b class="text-ink">${usd(r.price_usd)}</b>` : ""}`) : ""}${det ? mut(det) : ""}
        ${r.quotes.some(x => x.link) ? `<div class="flex flex-wrap gap-2">${r.quotes.filter(x => x.link).map((x, k) => /^https?:/i.test(x.link) ? link(x.link, `link ${k + 1} ↗`) : `<span class="text-xs text-mute">${esc(x.link)}</span>`).join("")}</div>` : ""}
        <div class="flex flex-wrap items-center gap-1">${r.side ? badge(SDL[r.side], "slate") : ""}${r.to_send ? badge("Enviar", "amber") : ""}${r.pending_supplier ? badge("Pendente fornecedor", "red") : ""}${r.tracking && r.tracking !== "-" ? badge(r.tracking, "slate") : ""}${envio}${r.perfect_code ? `<span data-dw="${esc(r.perfect_code)}" data-dwk="projeto" data-chip="1"></span>` : ""}</div>
        <div class="mt-1 flex items-center justify-between gap-1"><button type="button" class="${botao} px-2" data-mv="${r.id}" data-d="-1" ${i === 0 ? "disabled" : ""} title="Etapa anterior">◀</button><button type="button" class="${botao}" data-ed="${r.id}">Editar</button><button type="button" class="${botao} px-2" data-mv="${r.id}" data-d="1" ${i === n - 1 ? "disabled" : ""} title="Próxima etapa">▶</button></div></div>`;
    };
    const carregarPedidos = async () => {
      const s = filtrosDa(), novo = !data; data = await J("/api/samples?" + qs(s)); const t = data.totals; desenharAbas(); if (novo) desenharFiltros();
      $("#ak").innerHTML = kpi("Amostras", nf(t.n), `${nf(t.to_send)} para enviar`, "blue") + kpi("Total (preço escolhido)", brl(t.chosen), `menor cotação ${brl(t.best)}`, "green") +
        kpi("Melhor preço (planilha)", brl(t.best_sheet), usd(t.usd), "slate") + kpi("Pendente fornecedor", nf(t.pending_supplier), "aguardando resposta", "red");
      $("#aq").innerHTML = `<span class="mr-1 text-xs font-semibold uppercase tracking-wide text-mute">Atalhos</span>` + chip('data-tg="flag" data-v="enviar"', "Para enviar", s.flag === "enviar", s.flag && s.flag !== "enviar" ? null : t.to_send, true) +
        chip('data-tg="flag" data-v="pendente_fornecedor"', "Pendente fornecedor", s.flag === "pendente_fornecedor", s.flag && s.flag !== "pendente_fornecedor" ? null : t.pending_supplier, true);
      metaLinha(t.n, "pedido(s) de amostra", "amostras"); $("#ap").innerHTML = "";
      const n = data.stages.length;
      $("#abody").innerHTML = t.n ? `<div class="overflow-x-auto pb-2"><div class="grid gap-3" style="grid-template-columns:repeat(${n},minmax(15rem,1fr))">${data.stages.map(([k, l], i) => { const rs = data.rows.filter(r => r.stage === k);
        return `<section class="flex flex-col gap-2 rounded-2xl border border-line p-3"><h4 class="m-0 flex items-center justify-between text-sm font-semibold text-ink">${esc(l)} ${badge(nf(rs.length), rs.length ? "blue" : "slate")}</h4>${rs.map(r => cartao(r, i, n)).join("") || '<div class="py-4 text-center text-xs text-mute">–</div>'}</section>`; }).join("")}</div></div>`
        : empty("Nenhum pedido de amostra com esses filtros.");
      dwFill($("#abody"));
    };

    const carregar = async () => {
      $("#abody").innerHTML = `<div class="rounded-2xl border border-line bg-card px-5 py-8 text-sm text-mute">Carregando…</div>`; $("#ap").innerHTML = "";
      try { await (aba() === "pendentes" ? carregarPendentes() : carregarPedidos()); } catch (e) { $("#abody").innerHTML = notice(esc(e.message), "red"); }
    };
    const aplicar = (logo = false) => { pg = 1; clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 300); };
    const trocarAba = t => { F.set({ tab: t === "pedidos" ? "pedidos" : "" }); pg = 1; $("#ak").innerHTML = $("#aq").innerHTML = ""; desenharAbas(); desenharFiltros(); carregar(); };

    $("#atab").addEventListener("click", e => { const b = e.target.closest("[data-tab]"); if (b && b.dataset.tab !== aba()) trocarAba(b.dataset.tab); });
    $("#af").addEventListener("input", e => { const n = e.target.name; if (!n) return; F.set({ [n]: e.target.value }); aplicar(e.target.tagName === "SELECT"); });
    $("#af").addEventListener("submit", e => e.preventDefault());
    $("#af").addEventListener("click", e => {
      if (e.target.id === "aclr") { F.set(Object.fromEntries(ABA[aba()].map(k => [k, ""]))); desenharFiltros(); aplicar(true); }
      if (e.target.id === "anew") form({ stage: "cotacao", quotes: [{ price: "", link: "", chosen: 1 }] });
    });
    $("#aq").addEventListener("click", e => { const b = e.target.closest("[data-tg]"); if (!b) return; F.toggle(b.dataset.tg, b.dataset.v); desenharFiltros(); aplicar(true); });
    $("#ap").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; carregar(); scrollTo(0, 0); } });
    $("#abody").addEventListener("click", async e => {
      const bp = e.target.closest("[data-bp]"), np = e.target.closest("[data-np]"), mv = e.target.closest("[data-mv]"), ed = e.target.closest("[data-ed]");
      if (bp) menorPreco(+bp.dataset.bp, bp);
      if (np) { const r = rows[+np.dataset.np], q = r._best ? [{ price: r._best.price, link: r._best.url, chosen: 1 }] : [{ price: "", link: "", chosen: 1 }];
        form({ autoSearch: false, stage: "cotacao", perfect_code: r.code, quotes: q, notes: r.cross.length ? "Referência cruzada: " + r.cross.slice(0, 8).map(c => (c.brand || "") + " " + c.code).join(" · ") : "" }); }
      if (mv) { const r = data.rows.find(x => x.id == mv.dataset.mv), ks = data.stages.map(s => s[0]); try { await post("/api/samples", { ...r, stage: ks[ks.indexOf(r.stage) + +mv.dataset.d] }); carregar(); } catch (er) { alert(er.message); } }
      if (ed) form(data.rows.find(x => x.id == ed.dataset.ed));
    });

    // ---------- formulário do pedido (diálogo; estilo antigo) ----------
    async function form(o) {
      const md = await meta();
      const q = (o.quotes && o.quotes.length) ? o.quotes : [{ price: "", link: "", chosen: 1 }];
      const fld = (n, l, ex = "") => `<label>${l}<input name="${n}" value="${esc(o[n] ?? "")}" ${ex}></label>`;
      dlg.innerHTML = `<form id="sform"><div class="dh"><h2>${o.id ? "Editar amostra" : "Nova amostra"}</h2><button type="button" class="btn ghost" data-close>Fechar</button></div>
        <div class="fgrid">${fld("perfect_code", "Código PERFECT", 'list="pl" autocomplete="off"')}<datalist id="pl"></datalist>${fld("sample_code", "Código da amostra")}${fld("sc_number", "Nº SC")}${fld("ship_code", "Código de envio")}
        <label>Aplicação<input name="application" value="${esc(o.application ?? "")}" list="al" autocomplete="off"></label><datalist id="al"></datalist>
        <label>Lado<select name="side">${[["", "—"], ["direito", "Direito (LD)"], ["esquerdo", "Esquerdo (LE)"], ["ambos", "Ambos (LD/LE)"]].map(([k, l]) => `<option value="${k}" ${(o.side || "") === k ? "selected" : ""}>${l}</option>`).join("")}</select></label>${fld("supplier", "Fornecedor", 'list="sl"')}<datalist id="sl">${md.suppliers.map(s => `<option value="${esc(s)}">`).join("")}</datalist>${fld("month", "Mês")}${fld("tracking", "Cód. rastreio")}
        ${fld("net_weight", "Peso líq. (kg)")}${fld("gross_weight", "Peso bruto (kg)")}${fld("credit_note", "Credit note")}
        <label>Etapa<select name="stage">${md.stages.map(([k, l]) => `<option value="${k}" ${o.stage === k ? "selected" : ""}>${l}</option>`).join("")}</select></label></div>
        <div class="checks"><label><input type="checkbox" name="to_send" ${o.to_send ? "checked" : ""}> Enviar</label><label><input type="checkbox" name="pending_supplier" ${o.pending_supplier ? "checked" : ""}> Pendente fornecedor</label></div>
        <h4>Cotações <button type="button" class="btn ghost" id="aq2">+ cotação</button></h4><div id="qs"></div>
        <label>Observações<textarea name="notes" rows="2">${esc(o.notes || "")}</textarea></label>
        <div class="acts"><button class="btn" type="submit">Salvar</button>${o.id ? '<button type="button" class="btn ghost" id="del">Excluir</button>' : ""}</div></form>`;
      $(".fgrid", dlg).insertAdjacentHTML("afterend", '<div id="xref"></div><div id="xproj" data-dwblock="" data-dwkind="projeto"></div><div id="psearch"></div>');
      const qrow = x => `<div class="qrow"><input class="qp" placeholder="Preço" value="${x.price ?? ""}"><input class="ql" placeholder="Link / contato" value="${esc(x.link || "")}"><label><input type="radio" name="ch" ${x.chosen ? "checked" : ""}> escolhida</label><button type="button" class="btn ghost" data-rq>×</button></div>`;
      $("#qs").innerHTML = q.map(qrow).join("");
      $("#aq2").onclick = () => $("#qs").insertAdjacentHTML("beforeend", qrow({ price: "", link: "", chosen: 0 }));
      $("#qs").onclick = e => { if (e.target.closest("[data-rq]")) e.target.closest(".qrow").remove(); };
      // Ao preencher o código PERFECT: "D-" + código no código de envio, e aplicação/lado importados de Desenvolvimento (ou do catálogo).
      const addQuote = r => { $$(".qrow", dlg).forEach(x => { if (!$(".qp", x).value && !$(".ql", x).value) x.remove(); }); $$(".qrow input[type=radio]", dlg).forEach(x => x.checked = false); $("#qs").insertAdjacentHTML("beforeend", qrow({ price: r.price, link: r.url, chosen: 1 })); };
      const ps = NEW.priceSearch($("#psearch"), { refs: [], onUse: addQuote }); let autoDone = false;
      const pc = $("[name=perfect_code]", dlg), ship = $("[name=ship_code]", dlg), ap = $("[name=application]", dlg), sd = $("[name=side]", dlg);
      const hint = document.createElement("small"); hint.className = "muted"; ap.parentElement.appendChild(hint);
      let auto = { ship: o.ship_code || "", app: o.application || "", side: o.side || "" }, seq = 0;   // só sobrescreve o que ainda é automático (ou vazio)
      const setIf = (el, key, val) => { if (val != null && (!el.value || el.value === auto[key])) { el.value = val; auto[key] = val; } };
      const fill = async () => {
        const code = pc.value.trim().toUpperCase().replace(/^D-/, ""), my = ++seq;
        if (!code) return;
        setIf(ship, "ship", "D-" + code);                     // imediato, sem esperar o servidor
        if (code.length < 4) return;
        try {
          const d = await J("/api/samples/prefill?code=" + encodeURIComponent(code)); if (my !== seq) return;
          $("#al").innerHTML = d.options.map(x => `<option value="${esc(x.text)}">${esc(x.source)}</option>`).join("");
          setIf(ap, "app", d.application); setIf(sd, "side", d.side);
          const com = (d.cross || []).filter(c => c.brand && !["OEM", "PERFECT"].includes(c.brand)), oth = (d.cross || []).filter(c => !com.includes(c)); ps.setRefs([...com, ...oth].map(c => ({ brand: c.brand, code: c.code })));
          if (o.autoSearch && !autoDone) { autoDone = true; ps.search(); }
          const xp = $("#xproj"); xp.dataset.dwblock = d.code || code; xp.innerHTML = ""; dwBlocks(dlg);   // Projeto PERFECT do item
          $("#xref").innerHTML = (d.pending && d.pending.length ? `<div class="notice">Este código está <b>pendente de compra</b> em ${d.pending.map(x => x === "DESENVOLVIMENTO" ? "Desenvolvimento" : "Redesenvolvimento").join(" e ")}${d.state === "sem" ? " e ainda <b>não tem pedido de amostra</b>" : d.state === "andamento" ? " (já há pedido em andamento)" : " (já foi comprado)"}.</div>` : "")
            + (d.cross && d.cross.length ? `<div class="xref"><b>Referência cruzada — o que cotar:</b> ${d.cross.map(c => `<span class="xchip"><b>${esc(c.brand || "")}</b> ${esc(c.code)}</span>`).join("")}</div>` : "");
          hint.textContent = d.application ? `Aplicação importada de ${d.source === "Catálogo" ? "Catálogo" : "Desenvolvimento"}${d.options.length > 1 ? ` (${d.options.length} opções na lista)` : ""}.` : (d.in_catalog ? "Sem aplicação cadastrada para este código." : "Código não encontrado em Desenvolvimento nem no catálogo.");
        } catch (e) { hint.textContent = ""; }
      };
      let tt; pc.addEventListener("input", async () => {
        clearTimeout(tt); tt = setTimeout(fill, 200);
        if (pc.value.length < 3) return; const d = await J("/api/products?size=8&q=" + encodeURIComponent(pc.value)); $("#pl").innerHTML = d.rows.map(r => `<option value="${esc(r.perfect_code)}">${esc(r.description || "")}</option>`).join(""); });
      pc.addEventListener("change", fill); if (o.perfect_code) fill();
      $("#sform").onsubmit = async e => { e.preventDefault(); const v = Object.fromEntries(new FormData(e.target));
        const body = { ...v, id: o.id, to_send: !!v.to_send, pending_supplier: !!v.pending_supplier, quotes: $$(".qrow", dlg).map(r => ({ price: $(".qp", r).value, link: $(".ql", r).value, chosen: $("input[type=radio]", r).checked })) };
        try { await post("/api/samples", body); dlg.close(); data = null; nPend = null; if (aba() === "pedidos") desenharFiltros(); carregar(); } catch (er) { alert(er.message); } };
      const del = $("#del"); if (del) del.onclick = async () => { if (confirm("Excluir esta amostra?")) { await J("/api/samples/" + o.id, { method: "DELETE" }); dlg.close(); data = null; carregar(); } };
      dlg.showModal();
    }

    desenharAbas(); desenharFiltros(); await carregar();
  }
  PSD.tela("amostras", () => amostras().catch(fail));
})();
