/* Tela · Envio de amostra — visual Tailwind (etapa 16). Fluxo: Compra (SC) → Chegou ⇒ Pendente projeto → Enviada (com o EX do fornecedor) → Finalizada (shipments.py).
   Cartões por fornecedor (clique filtra; ✎ edita o EX), atalhos de status (padrão «Em aberto»; «Todos» inclui finalizados), seleção em lote.
   Filtros na URL e lembrados (PSDTW.filtros); Excel com os mesmos filtros. Diálogos (novo, editar, enviar) seguem o estilo antigo. */
(function () {
  const { $, $$, esc, J, post, qs, root, fail, dlg, dmy, dwFill } = PSD;
  const TW = window.PSDTW, { nf, badge, notice } = TW;
  const ST = { pendente_projeto: ["Pendente projeto", "amber"], enviada: ["Amostra enviada", "green"], finalizada: ["Finalizada", "slate"] }, SDL = { direito: "LD", esquerdo: "LE", ambos: "LD/LE" };
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500";
  const botao = "rounded-lg border border-line bg-card px-3 py-1.5 text-sm font-semibold text-ink hover:bg-slate-500/10";
  const chip = (attrs, label, on, n, forte = false) => `<button type="button" ${attrs} aria-pressed="${on}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${on ? "border-blue-500 bg-blue-500 text-white" : forte ? "border-amber-500 bg-amber-500/10 text-ink hover:bg-amber-500/20" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${label}${n != null ? ` · ${nf(n)}` : ""}</button>`;
  const nada = '<span class="text-mute">–</span>';
  const put = (u, b) => J(u, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) });

  async function envioPage() {
    const F = TW.filtros("envio", ["q", "status", "supplier"]); let pg = 1, rows = [], sums = null, timer;
    const status = () => F.get().status || "abertos";
    root.innerHTML = `<div class="flex flex-col gap-5">
      <ol class="m-0 flex list-none flex-wrap items-center gap-2 p-0 text-xs text-mute">${[["Compra de amostra", "com o nº da SC"], ["Amostra recebida", "etapa «Chegou»"], ["Pendente projeto", "aguarda o projeto", "amber"], ["Amostra enviada", "com o EX do fornecedor", "green"], ["Finalizada", ""]]
        .map(([t, s, c], i) => `${i ? '<li class="text-mute">›</li>' : ""}<li class="rounded-xl border px-3 py-1.5 ${c === "amber" ? "border-amber-500 bg-amber-500/10" : c === "green" ? "border-emerald-500/40 bg-emerald-500/10" : "border-line bg-card"}"><b class="text-ink">${i + 1}. ${t}</b>${s ? ` <span>${s}</span>` : ""}</li>`).join("")}</ol>
      <div id="eg" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"></div>
      <div id="eq" class="flex flex-wrap items-center gap-2"></div>
      <form id="ef" class="flex flex-wrap items-center gap-2" autocomplete="off"></form>
      <div id="ebar" class="hidden flex-wrap items-center gap-2 rounded-xl border border-blue-500/30 bg-blue-500/10 px-4 py-2 text-sm text-ink"></div>
      <div id="emeta" class="flex flex-wrap items-center justify-between gap-3 text-sm text-mute"></div>
      <div id="et"></div><div id="ep" class="flex items-center justify-center gap-3 text-sm text-mute"></div>
    </div>`;

    const desenharFiltros = () => { const f = F.get(), sup = sums ? sums.suppliers : [];
      $("#ef").innerHTML = `<input name="q" type="search" value="${esc(f.q || "")}" placeholder="Buscar código, aplicação, SC, EX, rastreio…" class="${campo} min-w-[16rem] flex-1">` +
        `<select name="supplier" class="${campo} max-w-[14rem]" title="Fornecedor"><option value="">Todos os fornecedores</option>${sup.map(s => `<option value="${esc(s.supplier)}" ${f.supplier === s.supplier ? "selected" : ""}>${esc(s.supplier)}</option>`).join("")}<option value="sem" ${f.supplier === "sem" ? "selected" : ""}>Sem fornecedor</option></select>` +
        `<button type="button" id="eclr" class="${botao} py-2">Limpar filtros</button><button type="button" id="enew" class="rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-blue-700">+ Novo envio</button>`; };
    const desenharTopo = () => { const s = sums, f = F.get(), st = status();
      $("#eg").innerHTML = [...s.suppliers, s.other].filter(x => x.supplier || x.pendente_projeto || x.enviada).map(x => { const k = x.supplier || "sem", on = f.supplier === k;
        return `<div role="button" tabindex="0" data-sup="${esc(k)}" aria-pressed="${on}" class="cursor-pointer rounded-2xl border bg-card p-4 shadow-sm ${on ? "border-blue-500" : "border-line hover:bg-slate-500/10"}">
          <div class="flex items-center justify-between gap-2"><b class="text-ink">${esc(x.supplier || "Sem fornecedor")}</b>${x.ex ? `<span class="flex items-center gap-1"><code class="text-xs text-mute">${esc(x.ex)}</code><button type="button" data-ex="${esc(x.supplier)}" class="rounded px-1 text-mute hover:text-ink" title="Editar o EX">✎</button></span>` : ""}</div>
          <div class="mt-3 flex flex-wrap gap-1.5">${badge(nf(x.pendente_projeto) + " pendente projeto", x.pendente_projeto ? "amber" : "slate")}${badge(nf(x.enviada) + " enviada" + (x.enviada === 1 ? "" : "s"), x.enviada ? "green" : "slate")}${badge(nf(x.finalizada) + " finalizada" + (x.finalizada === 1 ? "" : "s"), "slate")}</div></div>`; }).join("");
      $("#eq").innerHTML = `<span class="mr-1 text-xs font-semibold uppercase tracking-wide text-mute">Status</span>` + [["abertos", "Em aberto", s.pendente_projeto + s.enviada], ["pendente_projeto", "Pendente projeto", s.pendente_projeto, true], ["enviada", "Amostra enviada", s.enviada], ["finalizada", "Finalizadas", s.finalizada], ["todos", "Todos", s.pendente_projeto + s.enviada + s.finalizada]]
        .map(([k, l, n, forte]) => chip(`data-st="${k}"`, l, st === k, n, forte)).join(""); };
    const selecionados = () => $$(".esel:checked", root).map(c => +c.value);
    const barra = () => { const n = selecionados().length, b = $("#ebar"); b.classList.toggle("hidden", !n); b.classList.toggle("flex", !!n);
      b.innerHTML = n ? `<b>${nf(n)}</b> selecionado(s) <button type="button" class="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-blue-700" data-ea="send">Marcar como enviada…</button><button type="button" class="${botao}" data-ea="finalizada">Finalizar</button><button type="button" class="${botao}" data-ea="pendente_projeto">Voltar p/ pendente projeto</button><button type="button" class="${botao}" data-ea="x">Limpar seleção</button>` : ""; };

    const carregar = async () => {
      const f = F.get();
      $("#et").innerHTML = `<div class="rounded-2xl border border-line bg-card px-5 py-8 text-sm text-mute">Carregando…</div>`; $("#ep").innerHTML = "";
      try {
        const d = await J("/api/shipments?" + qs({ ...f, status: status(), page: pg })), pages = Math.max(1, Math.ceil(d.total / d.size)), novo = !sums; sums = d.summary; rows = d.rows;
        desenharTopo(); if (novo) desenharFiltros();
        const n = Object.keys(f).filter(k => !(k === "status" && f[k] === "abertos")).length;
        $("#emeta").innerHTML = `<span><b class="text-ink">${nf(d.total)}</b> envio(s)${n ? ` · ${n} filtro(s) ativo(s)` : ""}${F.restaurado && pg === 1 ? ' · <span class="text-amber-700">filtros da última visita</span>' : ""}</span>
          <a class="rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-blue-700" href="/api/export/envio.xlsx?${new URLSearchParams({ ...f, status: status() })}">⬇ Baixar Excel</a>`;
        $("#et").innerHTML = TW.table([{ h: '<input type="checkbox" class="eall" title="Selecionar a página">' }, { h: "Código" }, { h: "Aplicação", nw: false }, { h: "Lado" }, { h: "Fornecedor" }, { h: "EX" }, { h: "SC" }, { h: "Recebida" }, { h: "Status" }, { h: "Enviada em" }, { h: "Rastreio" }, { h: "Projeto PERFECT" }, { h: "" }], d.rows.map(r => {
          const code = r.product_id ? `<a href="#" class="font-semibold text-blue-600" data-ficha="${r.product_id}">${esc(r.perfect_code)}</a>` : r.rd ? `<a href="#" class="font-semibold text-blue-600" data-rd="${r.rd}" data-code="${esc(r.perfect_code)}">${esc(r.perfect_code)}</a>` : `<b>${esc(r.perfect_code)}</b>`;
          const s = ST[r.status] || [r.status, "slate"];
          return [`<input type="checkbox" class="esel" value="${r.id}">`, code, `<span class="block max-w-[20rem] truncate" title="${esc(r.application || r.description || "")}">${esc(r.application || r.description || "")}</span>`, r.side ? badge(SDL[r.side], "slate") : nada,
            esc(r.supplier || "–"), r.ex_code ? `<code class="text-xs">${esc(r.ex_code)}</code>` : nada,
            `${esc(r.sc_number || "–")}${r.order_id ? ` <a class="text-blue-600" href="/amostras?tab=pedidos&q=${encodeURIComponent(r.perfect_code)}" title="Ver o pedido na Compra de amostras">↗</a>` : ""}`,
            esc(r.received_at ? dmy(r.received_at) : "–"), badge(s[0], s[1]), esc(r.shipped_at ? dmy(r.shipped_at) : "–"), esc(r.tracking || "–"), `<span data-dw="${esc(r.perfect_code)}" data-dwk="projeto"></span>`,
            `<button type="button" class="${botao}" data-ee="${r.id}">Editar</button>`]; }), { h: "max-h-[65vh]" });
        $("#ep").innerHTML = pages > 1 ? `<button type="button" data-p="${pg - 1}" class="${botao}" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button type="button" data-p="${pg + 1}" class="${botao}" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
        barra(); dwFill($("#et"));
      } catch (e) { $("#et").innerHTML = notice(esc(e.message), "red"); }
    };
    const aplicar = (logo = false) => { pg = 1; if (sums) desenharTopo(); clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 300); };

    // ---------- diálogos (estilo antigo) ----------
    const dialog = (title, body, onok, okLabel = "Salvar") => { dlg.innerHTML = `<div class="dh"><div><h2>${title}</h2></div><div><button class="btn ghost" data-close>Fechar</button></div></div><div class="fgrid">${body}</div><p id="dmsg" class="imp-msg"></p><div class="acts"><button class="btn" id="dok">${okLabel}</button><button class="btn ghost" data-close>Cancelar</button></div>`;
      $("#dok").onclick = async () => { try { await onok(); dlg.close(); carregar(); } catch (e) { $("#dmsg").textContent = e.message; $("#dmsg").className = "imp-msg err"; } }; dlg.showModal(); };
    const supSel = (name, cur) => `<select name="${name}" id="${name}"><option value="">—</option>${sums.suppliers.map(s => `<option value="${esc(s.supplier)}" ${s.supplier === cur ? "selected" : ""}>${esc(s.supplier)} (${esc(s.ex)})</option>`).join("")}</select>`;
    const val = n => ($("#" + n) || {}).value;
    const editar = r => { const s = ST[r.status] || [r.status];
      dlg.innerHTML = `<div class="dh"><div><h2>${esc(r.perfect_code)} <span class="badge">${esc(s[0])}</span></h2><p>${esc(r.description || "")}</p></div><div><button class="btn ghost" data-close>Fechar</button></div></div>
        <div class="fgrid"><label>Status<select id="es">${Object.entries(ST).map(([k, v]) => `<option value="${k}" ${k === r.status ? "selected" : ""}>${v[0]}</option>`).join("")}</select></label><label>Fornecedor (define o EX)${supSel("ef2", r.supplier)}</label><label>Nº da SC<input id="esc" value="${esc(r.sc_number || "")}"></label>
        <label>Aplicação<input id="eap" value="${esc(r.application || "")}"></label><label>Lado<select id="esd"><option value="">—</option>${Object.entries({ direito: "Direito (LD)", esquerdo: "Esquerdo (LE)", ambos: "Ambos (LD/LE)" }).map(([k, l]) => `<option value="${k}" ${r.side === k ? "selected" : ""}>${l}</option>`).join("")}</select></label>
        <label>Comprada em<input type="date" id="ebo" value="${esc(r.bought_at || "")}"></label><label>Recebida em<input type="date" id="ere" value="${esc(r.received_at || "")}"></label><label>Enviada em<input type="date" id="esh" value="${esc(r.shipped_at || "")}"></label>
        <label>Rastreio<input id="etr" value="${esc(r.tracking || "")}"></label><label>Observações<input id="eno" value="${esc(r.notes || "")}"></label></div>${r.ex_code ? `<p class="muted">EX atual: <code>${esc(r.ex_code)}</code></p>` : ""}<p id="dmsg" class="imp-msg"></p>
        <div class="acts"><button class="btn" id="dok">Salvar</button><button class="btn ghost" id="ddel">Excluir</button><button class="btn ghost" data-close>Cancelar</button></div>`;
      $("#dok").onclick = async () => { try { await put("/api/shipments/" + r.id, { status: val("es"), supplier: val("ef2"), sc_number: val("esc"), application: val("eap"), side: val("esd"), bought_at: val("ebo"), received_at: val("ere"), shipped_at: val("esh"), tracking: val("etr"), notes: val("eno") }); dlg.close(); carregar(); } catch (er) { $("#dmsg").textContent = er.message; } };
      $("#ddel").onclick = async () => { if (!confirm("Excluir este envio?")) return; await J("/api/shipments/" + r.id, { method: "DELETE" }); dlg.close(); carregar(); }; dlg.showModal(); };

    // ---------- eventos ----------
    $("#ef").addEventListener("input", e => { const n = e.target.name; if (!n) return; F.set({ [n]: e.target.value }); aplicar(e.target.tagName === "SELECT"); });
    $("#ef").addEventListener("submit", e => e.preventDefault());
    $("#ef").addEventListener("click", e => {
      if (e.target.id === "eclr") { F.clear(); desenharFiltros(); aplicar(true); }
      if (e.target.id === "enew") dialog("Novo envio de amostra", `<label>Código PERFECT<input id="nc" placeholder="ex.: AMD0170 ou 1BP31901AB"></label><label>Fornecedor${supSel("nf")}</label><label>Nº da SC<input id="nsc"></label><label>Aplicação<input id="nap"></label><label>Observações<input id="nno"></label>`,
        () => post("/api/shipments", { perfect_code: val("nc"), supplier: val("nf"), sc_number: val("nsc"), application: val("nap"), notes: val("nno") }));
    });
    $("#eq").addEventListener("click", e => { const b = e.target.closest("[data-st]"); if (!b) return; F.set({ status: b.dataset.st === "abertos" || b.dataset.st === status() ? "" : b.dataset.st }); aplicar(true); });
    $("#eg").addEventListener("click", e => {
      const x = e.target.closest("[data-ex]");
      if (x) { const s = sums.suppliers.find(y => y.supplier === x.dataset.ex);
        return dialog("EX do fornecedor " + esc(s.supplier), `<label>Fornecedor<input value="${esc(s.supplier)}" disabled></label><label>Código EX<input id="exv" value="${esc(s.ex)}" placeholder="EX0002116"></label>`, () => put("/api/supplier-ex", { supplier: s.supplier, ex_code: val("exv") })); }
      const c = e.target.closest("[data-sup]"); if (c) { F.toggle("supplier", c.dataset.sup); desenharFiltros(); aplicar(true); }
    });
    $("#eg").addEventListener("keydown", e => { const c = e.target.closest("[data-sup]"); if (c && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); c.click(); } });
    $("#ep").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; carregar(); scrollTo(0, 0); } });
    $("#et").addEventListener("change", e => { if (e.target.classList.contains("eall")) $$(".esel", root).forEach(c => c.checked = e.target.checked); if (e.target.matches(".eall,.esel")) barra(); });
    $("#et").addEventListener("click", e => { const b = e.target.closest("[data-ee]"); if (b) editar(rows.find(x => x.id === +b.dataset.ee)); });
    $("#ebar").addEventListener("click", async e => { const b = e.target.closest("[data-ea]"); if (!b) return; const ids = selecionados(), a = b.dataset.ea;
      if (a === "x") { $$(".esel,.eall", root).forEach(c => c.checked = false); return barra(); }
      if (a === "send") { const first = rows.find(r => r.id === ids[0]);
        return dialog(`Marcar ${ids.length} amostra(s) como enviada(s)`, `<label>Fornecedor (define o EX)${supSel("sf", first && first.supplier)}</label><label>Data do envio<input type="date" id="sd" value="${new Date().toISOString().slice(0, 10)}"></label><label>Rastreio / documento<input id="st" placeholder="opcional"></label><label>Observações<input id="sn" placeholder="opcional"></label>`,
          () => post("/api/shipments/send", { ids, supplier: val("sf"), date: val("sd"), tracking: val("st"), notes: val("sn") }), "Marcar como enviada"); }
      if (!confirm(`${a === "finalizada" ? "Finalizar" : "Voltar para pendente projeto"}: ${ids.length} envio(s)?`)) return; try { await post("/api/shipments/status", { ids, status: a }); carregar(); } catch (er) { alert(er.message); } });

    desenharFiltros(); await carregar();
  }
  PSD.tela("envio", () => envioPage().catch(fail));
})();
