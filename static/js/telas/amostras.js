/* Tela · Compra de amostras (kanban).
   Usa o núcleo window.PSD (core.js); registra a tela com PSD.tela(slug, desenhar). Separado do antigo pages.js na etapa 16. */
(function () {
  const { $, $$, esc, J, post, qs, num, brl, T, lnk, empty, root, page, fail, dlg, inp, tag, clip, kb, dwBlocks, dwFill, NEW } = PSD;

  // ---------- compra de amostras (kanban dinâmico) ----------
  async function amostras() {
    root.innerHTML = `<div class="seg" id="stabs"><button type="button" class="on" data-t="pend">Sugestões de compra <span class="badge" id="pc-n"></span></button><button type="button" data-t="kb">Pedidos de amostra</button></div><div id="pendview"></div>
      <form class="toolbar" id="sf">${inp("q", "Buscar código, SC, aplicação, fornecedor", 'style="flex:1;min-width:220px"')}<select name="supplier"><option value="">Fornecedor</option></select><select name="month"><option value="">Mês</option></select><select name="side"><option value="">Lado</option><option value="direito">Direito (LD)</option><option value="esquerdo">Esquerdo (LE)</option><option value="ambos">Ambos (LD/LE)</option></select><button type="button" class="btn" id="new">+ Nova amostra</button><a class="btn" id="dl" href="#">⬇ Baixar Excel</a></form>
      <div class="cards mini-cards" id="tot"></div><div class="kanban" id="kb"></div>`;
    ["#sf", "#tot", "#kb"].forEach(x => $(x).hidden = true);
    const f = $("#sf"); let t, data, first = true;
    const ST = {}; 
    const load = async () => { try {
      $("#dl").href = "/api/export/amostras.xlsx?" + qs(Object.fromEntries(new FormData(f)));
      data = await J("/api/samples?" + qs(Object.fromEntries(new FormData(f)))); data.stages.forEach(([k, l]) => ST[k] = l);
      if (first) { first = false; $("[name=supplier]", f).innerHTML += data.suppliers.map(s => `<option>${esc(s)}</option>`).join(""); $("[name=month]", f).innerHTML += data.months.map(s => `<option>${esc(s)}</option>`).join(""); }
      const tt = data.totals; $("#tot").innerHTML = [["Amostras", tt.n], ["Total (preço escolhido)", brl(tt.chosen)], ["Total (menor cotação)", brl(tt.best)], ["Melhor preço (planilha)", brl(tt.best_sheet)], ["Total em US$", "US$ " + Number(tt.usd || 0).toLocaleString("pt-BR", { maximumFractionDigits: 2 })], ["Pendente fornecedor", tt.pending_supplier], ["Para enviar", tt.to_send]].map(([l, v]) => `<div class="card"><span class="num sm">${v}</span><small>${l}</small></div>`).join("");
      $("#kb").innerHTML = data.stages.map(([k, l], i) => { const rs = data.rows.filter(r => r.stage === k); return `<div class="kcol"><h4>${l} <span class="badge">${rs.length}</span></h4>${rs.map(r => { const ch = r.quotes.find(q => q.chosen && q.price != null); return `<div class="kcard"><div class="kt"><b>${r.product_id ? lnk(r.product_id, r.perfect_code) : esc(r.perfect_code || "(sem código)")}</b><span>${esc(r.sc_number ? "SC " + r.sc_number : "")}</span></div>
        <div>${esc(r.application || "")}</div><div class="muted">${esc(r.sample_code || "")}${r.supplier ? " · " + esc(r.supplier) : ""}${r.month ? " · " + esc(r.month) : ""}</div>
        <div>${ch ? brl(ch.price) : ""}${r.quotes.length > 1 ? ` <small class="muted">(${r.quotes.length} cotações)</small>` : ""}</div>
        <div class="muted">${r.best_price != null ? `Melhor preço <b>${brl(r.best_price)}</b>` : ""}${r.price_usd != null ? ` · <b>US$ ${Number(r.price_usd).toLocaleString("pt-BR", { maximumFractionDigits: 2 })}</b>` : ""}</div>
        <div class="muted">${[r.sc_number ? "SC " + esc(r.sc_number) : "", r.ship_code ? esc(r.ship_code) : "", r.credit_note && r.credit_note !== "-" ? "Credit note " + esc(r.credit_note) : "", r.net_weight != null ? "Líq. " + r.net_weight + " kg" : "", r.gross_weight != null ? "Bruto " + r.gross_weight + " kg" : ""].filter(Boolean).join(" · ")}</div>
        ${r.quotes.some(x => x.link) ? `<div>${r.quotes.filter(x => x.link).map((x, n) => /^https?:/i.test(x.link) ? `<a class="small-link" href="${esc(x.link)}" target="_blank" rel="noopener">link ${n + 1} ↗</a>` : `<small class="muted">${esc(x.link)}</small>`).join(" · ")}</div>` : ""}
        <div>${r.side ? `<span class="chip">${{ direito: "LD", esquerdo: "LE", ambos: "LD/LE" }[r.side]}</span>` : ""}${r.to_send ? '<span class="chip warn">Enviar</span>' : ""}${r.pending_supplier ? '<span class="chip bad">Pendente fornecedor</span>' : ""}${r.tracking && r.tracking !== "-" ? `<span class="chip">${esc(r.tracking)}</span>` : ""}${r.ship_status ? `<a class="chip ${r.ship_status === "enviada" ? "ok" : r.ship_status === "pendente_projeto" ? "warn" : ""}" href="/envio?q=${encodeURIComponent(r.perfect_code || "")}&status=" title="Envio de amostra">${{ pendente_projeto: "Pendente projeto", enviada: "Enviada" + (r.ship_ex ? " · " + esc(r.ship_ex) : ""), finalizada: "Envio finalizado" }[r.ship_status]}</a>` : ""}${r.perfect_code ? `<span data-dw="${esc(r.perfect_code)}" data-dwk="projeto" data-chip="1"></span>` : ""}</div>
        <div class="acts"><button class="btn ghost" data-mv="${r.id}" data-d="-1" ${i === 0 ? "disabled" : ""}>◀</button><button class="btn ghost" data-ed="${r.id}">Editar</button><button class="btn ghost" data-mv="${r.id}" data-d="1" ${i === data.stages.length - 1 ? "disabled" : ""}>▶</button></div></div>`; }).join("")}</div>`; }).join("");
      dwFill($("#kb"));
    } catch (e) { fail(e); } };
    f.addEventListener("input", () => { clearTimeout(t); t = setTimeout(load, 300); });
    root.addEventListener("click", async e => {
      const mv = e.target.closest("[data-mv]"), ed = e.target.closest("[data-ed]");
      if (mv) { const r = data.rows.find(x => x.id == mv.dataset.mv), ks = data.stages.map(s => s[0]); r.stage = ks[ks.indexOf(r.stage) + +mv.dataset.d]; await post("/api/samples", r); load(); }
      if (ed) form(data.rows.find(x => x.id == ed.dataset.ed));
    });
    $("#new").onclick = () => form({ stage: "cotacao", quotes: [{ price: "", link: "", chosen: 1 }] });

    // ---- Sugestões de compra: só o que AINDA NÃO compramos amostra e cujo status é diferente de ITEM RECEBIDO (Amortecedor) ----
    let pendLoaded = false;
    const mlUrl = (brand, code) => "https://lista.mercadolivre.com.br/" + encodeURIComponent(`${brand && brand !== "OEM" ? brand + " " : ""}${code} amortecedor`.trim().toLowerCase().replace(/\s+/g, "-")) + "_OrderId_PRICE*ASC_ITEM*CONDITION_2230284";
    const topRefs = cross => { const com = (cross || []).filter(c => c.brand && !["OEM", "PERFECT"].includes(c.brand)); return (com.length ? com : cross || []).slice(0, 2); };
    async function pend() {
      const host = $("#pendview");
      host.innerHTML = `<div class="notice slim">Somente itens em <b>desenvolvimento / redesenvolvimento</b> marcados <b>PENDENTE COMPRAS</b>, <b>sem amostra comprada</b>, fora do catálogo e com status diferente de ITEM RECEBIDO (somente Amortecedor). Em cada linha o link da consulta já está pronto — e <b>Buscar menor preço</b> traz o anúncio mais barato (unitário ou par/kit).</div>
        <form class="toolbar" id="pf"><input name="q" placeholder="Buscar código, descrição, veículo…" style="flex:1;min-width:220px"><select name="kind"><option value="">DES e R-D</option><option value="des">Somente DES</option><option value="rd">Somente R-D</option></select>
        <a class="btn ghost" id="pdl" href="#">⬇ Excel</a></form>
        <div class="summary" id="ps"></div><div id="pt"></div><div class="pager" id="pp"></div>`;
      const pf = $("#pf"); let pg = 1, tm, rows = [];
      const ld = async () => { try {
        const fv = Object.fromEntries(new FormData(pf)); $("#pdl").href = "/api/export/pendente_compras.xlsx?" + qs(fv);
        const d = await J("/api/purchases/pending?" + qs({ ...fv, page: pg })), pages = Math.max(1, Math.ceil(d.total / d.size)); rows = d.rows;
        $("#pc-n").textContent = d.summary.total; $("#ps").innerHTML = `<b>${num(d.summary.total)}</b> sugestão(ões) · ${num(d.summary.com_referencia)} com referência cruzada · ${num(d.summary.pend_compras)} marcadas «Pendente compras»`;
        $("#pt").innerHTML = d.rows.length ? T(["Código", "Descrição", "Status", "Referência cruzada (marque o que buscar)", "Menor preço", ""], d.rows.map((r, i) => {
          const k = r.suggestion === "DESENVOLVIMENTO" ? "des" : "rd", refs = topRefs(r.cross);
          const cr = r.cross.slice(0, 6).map(c => `<a class="xchip" target="_blank" rel="noopener" href="${mlUrl(c.brand, c.code)}" title="Abrir a consulta no Mercado Livre, do menor preço"><b>${esc(c.brand || "")}</b> ${esc(c.code)} ↗</a>`).join("") + (r.cross.length > 6 ? `<span class="xchip more" title="${esc(r.cross.slice(6).map(c => (c.brand || "") + " " + c.code).join(" · "))}">+${r.cross.length - 6}</span>` : "");
          return `<tr data-i="${i}"><td><a href="#" data-rd="${k}" data-code="${esc(r.code)}">${esc(r.code)}</a><div>${tag(r.suggestion)}</div></td><td>${clip(r.description)}<small class="muted" style="display:block">${clip(r.vehicles)}</small></td><td><small>${esc(r.statuses || "–")}</small>${r.pend_compras ? '<div><span class="badge warn">pendente compras</span></div>' : ""}${r.state === "cotacao" ? '<div><span class="badge">em cotação</span></div>' : ""}</td>
            <td>${cr || '<span class="muted">sem referência cruzada</span>'}</td><td class="pcell" id="pc-${i}">${refs.length ? '<span class="muted">—</span>' : '<span class="muted">sem referência</span>'}</td>
            <td style="white-space:nowrap">${refs.length ? `<button class="btn ghost sm" data-bp="${i}">Buscar menor preço</button> ` : ""}<button class="btn sm" data-np="${i}">Criar pedido</button></td></tr>`; })) : empty("Nenhum item pendente de compra com esses filtros.");
        $("#pp").innerHTML = pages > 1 ? `<button class="btn ghost" data-p="${pg - 1}" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button class="btn ghost" data-p="${pg + 1}" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
        dwFill($("#pt"));
      } catch (e) { fail(e); } };
      pf.addEventListener("input", () => { clearTimeout(tm); tm = setTimeout(() => { pg = 1; ld(); }, 300); }); pf.addEventListener("submit", e => e.preventDefault());
      $("#pp").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; ld(); scrollTo(0, 0); } });
      const quick = async (i, btn) => {   // menor preço da linha — nunca quebra: se a busca falhar, mostra o link da consulta
        const r = rows[i], refs = topRefs(r.cross), cell = $("#pc-" + i), link = refs[0] ? mlUrl(refs[0].brand, refs[0].code) : null; btn.disabled = true; cell.innerHTML = '<span class="muted">buscando…</span>';
        try { const d = await post("/api/prices/search", { refs: refs.map(x => ({ brand: x.brand, code: x.code })), limit: 3, strict: true });
          r._best = d.best; cell.innerHTML = d.best ? `<a class="pbest" href="${esc(d.best.url || link)}" target="_blank" rel="noopener" title="${esc(d.best.title)}"><b>${brl(d.best.price)}</b> ↗</a>${d.best.pair ? ' <span class="badge warn" title="Anúncio de par/kit/jogo">par/kit</span>' : ""}<small class="muted" style="display:block">${esc(d.best.ref || "")} · ${esc(d.best.source)}${d.best.seller ? " · " + esc(d.best.seller) : ""}</small><a class="small-link" href="${esc(d.refs[0].links.mercado_livre)}" target="_blank" rel="noopener">ver consulta ↗</a>`
            : `<span class="muted">sem resposta automática</span><a class="small-link" style="display:block" href="${esc(d.refs[0].links.mercado_livre)}" target="_blank" rel="noopener">abrir consulta no Mercado Livre ↗</a>`; }
        catch (e) { cell.innerHTML = `<span class="muted">busca indisponível</span>${link ? `<a class="small-link" style="display:block" href="${link}" target="_blank" rel="noopener">abrir consulta ↗</a>` : ""}`; }
        btn.disabled = false; btn.textContent = "Buscar de novo"; };
      $("#pt").addEventListener("click", e => { const b = e.target.closest("[data-bp]"), n = e.target.closest("[data-np]");
        if (b) quick(+b.dataset.bp, b);
        if (n) { const r = rows[+n.dataset.np], q = r._best ? [{ price: r._best.price, link: r._best.url, chosen: 1 }] : [{ price: "", link: "", chosen: 1 }];
          form({ autoSearch: false, stage: "cotacao", perfect_code: r.code, quotes: q, notes: r.cross.length ? "Referência cruzada: " + r.cross.slice(0, 8).map(c => (c.brand || "") + " " + c.code).join(" · ") : "" }); } });
      ld();
    }
    const showTab = t => { $$("#stabs button").forEach(b => b.classList.toggle("on", b.dataset.t === t)); const k = t === "kb";
      ["#sf", "#tot", "#kb"].forEach(s => $(s).hidden = !k); $("#pendview").hidden = k; if (!k && !pendLoaded) { pendLoaded = true; pend(); } if (k && !kbLoaded) { kbLoaded = true; load(); } };
    $("#stabs").onclick = e => { const b = e.target.closest("[data-t]"); if (b) showTab(b.dataset.t); };
    let kbLoaded = false; showTab(new URLSearchParams(location.search).get("tab") === "pedidos" ? "kb" : "pend");

    function form(o) {
      const q = (o.quotes && o.quotes.length) ? o.quotes : [{ price: "", link: "", chosen: 1 }];
      const fld = (n, l, ex = "") => `<label>${l}<input name="${n}" value="${esc(o[n] ?? "")}" ${ex}></label>`;
      dlg.innerHTML = `<form id="sform"><div class="dh"><h2>${o.id ? "Editar amostra" : "Nova amostra"}</h2><button type="button" class="btn ghost" data-close>Fechar</button></div>
        <div class="fgrid">${fld("perfect_code", "Código PERFECT", 'list="pl" autocomplete="off"')}<datalist id="pl"></datalist>${fld("sample_code", "Código da amostra")}${fld("sc_number", "Nº SC")}${fld("ship_code", "Código de envio")}
        <label>Aplicação<input name="application" value="${esc(o.application ?? "")}" list="al" autocomplete="off"></label><datalist id="al"></datalist>
        <label>Lado<select name="side">${[["", "—"], ["direito", "Direito (LD)"], ["esquerdo", "Esquerdo (LE)"], ["ambos", "Ambos (LD/LE)"]].map(([k, l]) => `<option value="${k}" ${(o.side || "") === k ? "selected" : ""}>${l}</option>`).join("")}</select></label>${fld("supplier", "Fornecedor", 'list="sl"')}<datalist id="sl">${data.suppliers.map(s => `<option value="${esc(s)}">`).join("")}</datalist>${fld("month", "Mês")}${fld("tracking", "Cód. rastreio")}
        ${fld("net_weight", "Peso líq. (kg)")}${fld("gross_weight", "Peso bruto (kg)")}${fld("credit_note", "Credit note")}
        <label>Etapa<select name="stage">${data.stages.map(([k, l]) => `<option value="${k}" ${o.stage === k ? "selected" : ""}>${l}</option>`).join("")}</select></label></div>
        <div class="checks"><label><input type="checkbox" name="to_send" ${o.to_send ? "checked" : ""}> Enviar</label><label><input type="checkbox" name="pending_supplier" ${o.pending_supplier ? "checked" : ""}> Pendente fornecedor</label></div>
        <h4>Cotações <button type="button" class="btn ghost" id="aq">+ cotação</button></h4><div id="qs"></div>
        <label>Observações<textarea name="notes" rows="2">${esc(o.notes || "")}</textarea></label>
        <div class="acts"><button class="btn" type="submit">Salvar</button>${o.id ? '<button type="button" class="btn ghost" id="del">Excluir</button>' : ""}</div></form>`;
      $(".fgrid", dlg).insertAdjacentHTML("afterend", '<div id="xref"></div><div id="xproj" data-dwblock="" data-dwkind="projeto"></div><div id="psearch"></div>');
      const qrow = x => `<div class="qrow"><input class="qp" placeholder="Preço" value="${x.price ?? ""}"><input class="ql" placeholder="Link / contato" value="${esc(x.link || "")}"><label><input type="radio" name="ch" ${x.chosen ? "checked" : ""}> escolhida</label><button type="button" class="btn ghost" data-rq>×</button></div>`;
      $("#qs").innerHTML = q.map(qrow).join("");
      $("#aq").onclick = () => $("#qs").insertAdjacentHTML("beforeend", qrow({ price: "", link: "", chosen: 0 }));
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
        try { await post("/api/samples", body); dlg.close(); load(); } catch (er) { alert(er.message); } };
      const del = $("#del"); if (del) del.onclick = async () => { if (confirm("Excluir esta amostra?")) { await J("/api/samples/" + o.id, { method: "DELETE" }); dlg.close(); load(); } };
      dlg.showModal();
    }
  }
  PSD.tela("amostras", () => amostras());
})();
