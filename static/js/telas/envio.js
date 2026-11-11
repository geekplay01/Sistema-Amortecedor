/* Tela · Envio de amostra.
   Usa o núcleo window.PSD (core.js); registra a tela com PSD.tela(slug, desenhar). Separado do antigo pages.js na etapa 16. */
(function () {
  const { $, $$, esc, J, post, qs, num, T, lnk, empty, root, page, fail, dlg, sel, clip, dmy, dwFill, dwCol } = PSD;
  // ---------- Envio de amostra: Compra (SC) → Recebida (Pendente projeto) → Enviada (EX do fornecedor) → Finalizada ----------
  async function envioPage() {
    const ST = { pendente_projeto: ["Pendente projeto", "warn"], enviada: ["Amostra enviada", "ok"], finalizada: ["Finalizada", "mut"] }, SDL = { direito: "LD", esquerdo: "LE", ambos: "LD/LE" };
    const put = (u, b) => J(u, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) });
    const p0 = new URLSearchParams(location.search); let status = p0.get("status") === null ? "abertos" : p0.get("status") || "abertos", supplier = p0.get("supplier") || "", pg = 1, rows = [], sums = null, tm;
    root.innerHTML = `<div class="flow"><span><b>1</b> Compra de amostra<small>com o nº da SC</small></span><i>›</i><span><b>2</b> Amostra recebida<small>etapa «Chegou»</small></span><i>›</i><span class="w"><b>3</b> Pendente projeto<small>aguarda o projeto</small></span><i>›</i><span class="o"><b>4</b> Amostra enviada<small>com o EX do fornecedor</small></span><i>›</i><span><b>5</b> Finalizada</span></div>
      <div class="sup-grid" id="sg"></div><div class="seg" id="sst"></div>
      <form class="toolbar" id="ef"><input name="q" placeholder="Buscar código, aplicação, SC, EX, rastreio…" style="flex:1;min-width:240px"><select name="supplier"><option value="">Todos os fornecedores</option></select>
        <button type="button" class="btn ghost" id="enew">+ Novo envio</button><a class="btn" id="exl" href="#">⬇ Baixar Excel</a></form>
      <div class="bulkbar" id="ebar" hidden><b id="en">0</b> selecionado(s) <button type="button" class="btn sm" data-ea="send">Marcar como enviada…</button><button type="button" class="btn ghost sm" data-ea="finalizada">Finalizar</button><button type="button" class="btn ghost sm" data-ea="pendente_projeto">Voltar p/ pendente projeto</button><button type="button" class="btn ghost sm" data-ea="x">Limpar seleção</button></div>
      <div class="summary" id="esum"></div><div id="et"></div><div class="pager" id="epg"></div>`;
    const f = $("#ef"); f.elements.q.value = p0.get("q") || "";
    const sel = () => $$(".esel:checked", root).map(c => +c.value), upd = () => { const n = sel().length; $("#ebar").hidden = !n; $("#en").textContent = n; };
    const supOpts = () => (sums ? sums.suppliers : []).map(s => `<option value="${esc(s.supplier)}">${esc(s.supplier)} — ${esc(s.ex)}</option>`).join("");
    const load = async () => { try {
      const fv = Object.fromEntries(new FormData(f)); fv.supplier = supplier; $("#exl").href = "/api/export/envio.xlsx?" + qs({ ...fv, status });
      const d = await J("/api/shipments?" + qs({ ...fv, status, page: pg })), pages = Math.max(1, Math.ceil(d.total / d.size)); sums = d.summary; rows = d.rows;
      if (f.elements.supplier.options.length < 2) { f.elements.supplier.insertAdjacentHTML("beforeend", sums.suppliers.map(s => `<option value="${esc(s.supplier)}">${esc(s.supplier)}</option>`).join("") + '<option value="sem">Sem fornecedor</option>'); }
      f.elements.supplier.value = supplier;
      $("#sg").innerHTML = [...sums.suppliers, sums.other].filter(s => s.supplier || s.pendente_projeto || s.enviada).map(s => `<div class="sup ${supplier === (s.supplier || "sem") ? "on" : ""}" data-sup="${esc(s.supplier || "sem")}"><div class="sup-h"><b>${esc(s.supplier || "Sem fornecedor")}</b>${s.ex ? `<code>${esc(s.ex)}</code><button type="button" class="ex-ed" data-ex="${esc(s.supplier)}" title="Editar o EX">✎</button>` : ""}</div>
        <div class="sup-n"><span class="w"><b>${s.pendente_projeto}</b> pendente projeto</span><span class="o"><b>${s.enviada}</b> enviada${s.enviada === 1 ? "" : "s"}</span><span class="m"><b>${s.finalizada}</b> finalizada${s.finalizada === 1 ? "" : "s"}</span></div></div>`).join("");
      $("#sst").innerHTML = [["abertos", "Em aberto", sums.pendente_projeto + sums.enviada], ["pendente_projeto", "Pendente projeto", sums.pendente_projeto], ["enviada", "Amostra enviada", sums.enviada], ["finalizada", "Finalizadas", sums.finalizada]].map(([k, l, n]) => `<button type="button" data-st="${k}" class="${status === k ? "on" : ""}">${l} <span class="badge">${n}</span></button>`).join("");
      $("#esum").textContent = num(d.total) + " envio(s)";
      $("#et").innerHTML = d.rows.length ? T(['<input type="checkbox" class="eall" title="Selecionar a página">', "Código", "Aplicação", "Lado", "Fornecedor", "EX", "SC", "Recebida", "Status", "Enviada em", "Rastreio", "Projeto PERFECT", ""], d.rows.map(r => {
        const code = r.product_id ? lnk(r.product_id, r.perfect_code) : r.rd ? `<a href="#" data-rd="${r.rd}" data-code="${esc(r.perfect_code)}">${esc(r.perfect_code)}</a>` : esc(r.perfect_code);
        return `<tr><td><input type="checkbox" class="esel" value="${r.id}"></td><td>${code}</td><td>${clip(r.application || r.description)}</td><td>${r.side ? `<span class="sd ${r.side}">${SDL[r.side]}</span>` : "–"}</td><td>${esc(r.supplier || "–")}</td><td>${r.ex_code ? `<code>${esc(r.ex_code)}</code>` : "–"}</td>
          <td>${esc(r.sc_number || "–")}${r.order_id ? ` <a href="/amostras?q=${encodeURIComponent(r.perfect_code)}" title="Ver na Compra de amostras">↗</a>` : ""}</td><td>${esc(dmy(r.received_at) || "–")}</td><td><span class="badge ${ST[r.status][1]}">${ST[r.status][0]}</span></td><td>${esc(dmy(r.shipped_at) || "–")}</td><td>${esc(r.tracking || "–")}</td>${dwCol(r.perfect_code, "projeto")}
          <td><button class="btn ghost sm" data-ee="${r.id}">Editar</button></td></tr>`; })) : empty("Nenhum envio nesta visão.");
      $("#epg").innerHTML = pages > 1 ? `<button class="btn ghost" data-p="${pg - 1}" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button class="btn ghost" data-p="${pg + 1}" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
      upd(); dwFill($("#et"));
    } catch (e) { fail(e); } };
    const dialog = (title, body, onok, okLabel = "Salvar") => { dlg.innerHTML = `<div class="dh"><div><h2>${title}</h2></div><div><button class="btn ghost" data-close>Fechar</button></div></div><div class="fgrid">${body}</div><p id="dmsg" class="imp-msg"></p><div class="acts"><button class="btn" id="dok">${okLabel}</button><button class="btn ghost" data-close>Cancelar</button></div>`;
      $("#dok").onclick = async () => { try { await onok(); dlg.close(); load(); } catch (e) { $("#dmsg").textContent = e.message; $("#dmsg").className = "imp-msg err"; } }; dlg.showModal(); };
    const supSel = (name, cur) => `<select name="${name}" id="${name}"><option value="">—</option>${(sums.suppliers).map(s => `<option value="${esc(s.supplier)}" ${s.supplier === cur ? "selected" : ""}>${esc(s.supplier)} (${esc(s.ex)})</option>`).join("")}</select>`;
    const val = n => ($("#" + n) || {}).value;
    f.addEventListener("input", () => { clearTimeout(tm); tm = setTimeout(() => { pg = 1; load(); }, 300); }); f.addEventListener("submit", e => e.preventDefault());
    f.elements.supplier.addEventListener("change", () => { supplier = f.elements.supplier.value; });
    $("#sst").onclick = e => { const b = e.target.closest("[data-st]"); if (b) { status = b.dataset.st; pg = 1; load(); } };
    $("#sg").onclick = e => { const x = e.target.closest("[data-ex]"); if (x) { const s = sums.suppliers.find(y => y.supplier === x.dataset.ex);
        return dialog("EX do fornecedor " + esc(s.supplier), `<label>Fornecedor<input value="${esc(s.supplier)}" disabled></label><label>Código EX<input id="exv" value="${esc(s.ex)}" placeholder="EX0002116"></label>`, () => put("/api/supplier-ex", { supplier: s.supplier, ex_code: val("exv") })); }
      const c = e.target.closest("[data-sup]"); if (c) { supplier = supplier === c.dataset.sup ? "" : c.dataset.sup; pg = 1; load(); } };
    $("#epg").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; load(); scrollTo(0, 0); } });
    root.addEventListener("change", e => { if (e.target.classList.contains("eall")) $$(".esel", root).forEach(c => c.checked = e.target.checked); if (e.target.matches(".eall,.esel")) upd(); });
    $("#ebar").addEventListener("click", async e => { const b = e.target.closest("[data-ea]"); if (!b) return; const ids = sel(), a = b.dataset.ea;
      if (a === "x") { $$(".esel,.eall", root).forEach(c => c.checked = false); return upd(); }
      if (a === "send") { const first = rows.find(r => r.id === ids[0]);
        return dialog(`Marcar ${ids.length} amostra(s) como enviada(s)`, `<label>Fornecedor (define o EX)${supSel("sf", first && first.supplier)}</label><label>Data do envio<input type="date" id="sd" value="${new Date().toISOString().slice(0, 10)}"></label><label>Rastreio / documento<input id="st" placeholder="opcional"></label><label>Observações<input id="sn" placeholder="opcional"></label>`,
          () => post("/api/shipments/send", { ids, supplier: val("sf"), date: val("sd"), tracking: val("st"), notes: val("sn") }), "Marcar como enviada"); }
      if (!confirm(`${a === "finalizada" ? "Finalizar" : "Voltar para pendente projeto"}: ${ids.length} envio(s)?`)) return; try { await post("/api/shipments/status", { ids, status: a }); load(); } catch (er) { alert(er.message); } });
    $("#enew").onclick = () => dialog("Novo envio de amostra", `<label>Código PERFECT<input id="nc" placeholder="ex.: AMD0170 ou 1BP31901AB"></label><label>Fornecedor${supSel("nf")}</label><label>Nº da SC<input id="nsc"></label><label>Aplicação<input id="nap"></label><label>Observações<input id="nno"></label>`,
      () => post("/api/shipments", { perfect_code: val("nc"), supplier: val("nf"), sc_number: val("nsc"), application: val("nap"), notes: val("nno") }));
    $("#et").addEventListener("click", e => { const b = e.target.closest("[data-ee]"); if (!b) return; const r = rows.find(x => x.id === +b.dataset.ee);
      dlg.innerHTML = `<div class="dh"><div><h2>${esc(r.perfect_code)} <span class="badge ${ST[r.status][1]}">${ST[r.status][0]}</span></h2><p>${esc(r.description || "")}</p></div><div><button class="btn ghost" data-close>Fechar</button></div></div>
        <div class="fgrid"><label>Status<select id="es">${Object.entries(ST).map(([k, v]) => `<option value="${k}" ${k === r.status ? "selected" : ""}>${v[0]}</option>`).join("")}</select></label><label>Fornecedor (define o EX)${supSel("ef2", r.supplier)}</label><label>Nº da SC<input id="esc" value="${esc(r.sc_number || "")}"></label>
        <label>Aplicação<input id="eap" value="${esc(r.application || "")}"></label><label>Lado<select id="esd"><option value="">—</option><option value="direito" ${r.side === "direito" ? "selected" : ""}>Direito (LD)</option><option value="esquerdo" ${r.side === "esquerdo" ? "selected" : ""}>Esquerdo (LE)</option><option value="ambos" ${r.side === "ambos" ? "selected" : ""}>Ambos (LD/LE)</option></select></label>
        <label>Comprada em<input type="date" id="ebo" value="${esc(r.bought_at || "")}"></label><label>Recebida em<input type="date" id="ere" value="${esc(r.received_at || "")}"></label><label>Enviada em<input type="date" id="esh" value="${esc(r.shipped_at || "")}"></label>
        <label>Rastreio<input id="etr" value="${esc(r.tracking || "")}"></label><label>Observações<input id="eno" value="${esc(r.notes || "")}"></label></div>${r.ex_code ? `<p class="muted">EX atual: <code>${esc(r.ex_code)}</code></p>` : ""}<p id="dmsg" class="imp-msg"></p>
        <div class="acts"><button class="btn" id="dok">Salvar</button><button class="btn ghost" id="ddel">Excluir</button><button class="btn ghost" data-close>Cancelar</button></div>`;
      $("#dok").onclick = async () => { try { await put("/api/shipments/" + r.id, { status: val("es"), supplier: val("ef2"), sc_number: val("esc"), application: val("eap"), side: val("esd"), bought_at: val("ebo"), received_at: val("ere"), shipped_at: val("esh"), tracking: val("etr"), notes: val("eno") }); dlg.close(); load(); } catch (er) { $("#dmsg").textContent = er.message; } };
      $("#ddel").onclick = async () => { if (!confirm("Excluir este envio?")) return; await J("/api/shipments/" + r.id, { method: "DELETE" }); dlg.close(); load(); }; dlg.showModal(); });
    load();
  }
  PSD.tela("envio", () => envioPage());
})();
