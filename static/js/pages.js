// Telas: produtos, pesquisa, aplicações, comparação, equivalências, amostras, pendências, fontes, configurações.
(function () {
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const J = async (u, o) => { const r = await fetch(u, o), d = await r.json().catch(() => ({})); if (!r.ok) throw new Error(d.error || ("Erro " + r.status)); return d; };
  const post = (u, b) => J(u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) });
  const qs = o => new URLSearchParams(Object.entries(o).filter(([, v]) => v !== "" && v != null)).toString();
  const num = (v, d = 0) => v == null ? "–" : Number(v).toLocaleString("pt-BR", { maximumFractionDigits: d });
  const brl = v => "R$ " + Number(v || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const SYS = { gas: "Gás", oleo: "Óleo" }, yr = a => a.year_from ? a.year_from + (a.year_to && a.year_to !== a.year_from ? "–" + a.year_to : "") : "–";
  const T = (h, rows) => `<div class="tbl"><table><tr>${h.map(x => `<th>${x}</th>`).join("")}</tr>${rows.join("")}</table></div>`;
  const lnk = (id, t) => `<a href="#" data-ficha="${id}">${esc(t)}</a>`;
  const empty = m => `<div class="notice soon"><img src="/static/img/amortecedor-desenho.png" alt="" width="72"><div>${m}</div></div>`;
  const root = $("#panel"), page = root.dataset.page, url = new URLSearchParams(location.search);
  const fail = e => { root.insertAdjacentHTML("afterbegin", `<div class="notice err">${esc(e.message)}</div>`); };

  // ---------- ficha técnica (janela) ----------
  const dlg = document.createElement("dialog"); dlg.className = "dlg"; document.body.appendChild(dlg);
  dlg.addEventListener("click", e => { if (e.target === dlg || e.target.closest("[data-close]")) dlg.close(); });
  document.addEventListener("click", e => { const a = e.target.closest("[data-ficha]"); if (a) { e.preventDefault(); openFicha(a.dataset.ficha); } });
  const kv = (k, v) => `<div><small>${k}</small><b>${v == null || v === "" ? "—" : esc(v)}</b></div>`;
  const usd = v => "US$ " + Number(v).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const fobBlock = p => {   // cotações FOB do item; a mais barata em destaque executivo (verde)
    const q = p.fob_quotes || []; if (!q.length) return "";
    const rows = q.map(x => x.melhor
      ? `<div class="flex items-center justify-between rounded-lg border-2 border-emerald-500 bg-emerald-50 px-3 py-2 font-bold text-emerald-700"><span>${esc(x.fornecedor)} <span class="rounded-full bg-emerald-600 px-2 text-xs font-semibold text-white">Melhor Preço</span></span><span class="tabular-nums">${usd(x.preco)}</span></div>`
      : `<div class="flex items-center justify-between rounded-lg border px-3 py-2"><span>${esc(x.fornecedor)}</span><span class="tabular-nums">${usd(x.preco)}</span></div>`).join("");
    return `<details class="sec" open><summary>Cotações FOB <span class="badge">${q.length}</span></summary><div class="flex flex-col gap-2 py-2">${rows}</div></details>`;
  };
  const sec = (t, n, h) => `<details class="sec" ${n ? "open" : ""}><summary>${t} <span class="badge">${n}</span></summary>${n ? h : '<p class="muted">Nenhum dado nas bases importadas.</p>'}</details>`;
  async function openFicha(id) {
    try {
      const p = await J("/api/products/" + id), d = p.dimensions || {}, b = p.box;
      dlg.innerHTML = `<div class="dh"><div><h2>${esc(p.perfect_code)}</h2><p>${esc(p.description || "")}</p></div><div><a class="btn ghost" href="/comparacao?ids=${p.id}">Comparar</a> <button class="btn ghost" data-close>Fechar</button></div></div>
      <div class="kvs">${kv("Posição no catálogo", p.catalog_position)}${kv("Grupo", p.catalog_group)}${kv("Família", p.family)}${kv("Sistema", SYS[p.system_type])}${kv("EAN", p.ean)}${kv("NCM", p.ncm)}${kv("Peso (kg)", p.weight_kg)}${kv("Descrição (ES)", p.description_es)}
      ${kv("Lmin (mm)", d.lmin_mm)}${kv("Lmax (mm)", d.lmax_mm)}${kv("Curso (mm)", d.stroke_mm)}${kv("Ø haste (mm)", d.rod_diameter_mm)}${kv("Corpo (mm)", d.body_length_mm)}${kv("Ø tubo (mm)", d.tube_diameter_mm)}${kv("Fixação sup.", d.upper_mount)}${kv("Fixação inf.", d.lower_mount)}
      ${kv("FOB mín. (US$)", p.fob_detail && p.fob_detail.fob != null ? `${p.fob_detail.fob} · ${p.fob_detail.fob_fornecedor || ""} ${p.fob_detail.fob_data || ""}` : null)}${kv("FOB E-WIN / ZS / XGM (US$)", p.fob_detail ? [p.fob_detail.fob_ewin, p.fob_detail.fob_zs, p.fob_detail.fob_xgm].map(x => x ?? "–").join(" / ") : null)}${kv("Caixa", p.package_code)}${kv("Dim. caixa (mm)", b && b.raw_dims)}${kv("Embalagem (catálogo)", p.package_note)}${kv("Características", p.features)}</div><p class="muted">“—” = não consta nas bases importadas (nada foi inventado).</p>
      ${fobBlock(p)}
      <div data-dwblock="${esc(p.perfect_code)}"></div>
      <div id="fch-srv"></div>
      ${sec("Par direito/esquerdo", p.pair.length, p.pair.map(x => `${lnk(x.id, x.perfect_code)} (${x.lado})`).join(" · "))}
      ${sec("Referência cruzada (concorrentes e OEM)", (p.cross || []).length, `<div class="xref">${xchips(p.cross || [])}</div>`)}
      ${sec("Códigos (OEM, fornecedor, concorrente)", p.codes.filter(c => !c.is_cross).length, T(["Tipo", "Código", "Marca/fornecedor", "Fonte"], p.codes.filter(c => !c.is_cross).map(c => `<tr><td>${esc(c.code_type)}</td><td>${esc(c.code)}</td><td>${esc(c.brand || "")}</td><td>${esc(c.source || "")}</td></tr>`)))}
      ${sec("Aplicações veiculares", p.applications.length, T(["Montadora", "Modelo", "Aplicação", "Anos", "Eixo", "Lado", "Fonte"], p.applications.map(a => `<tr><td>${esc(a.make || "")}</td><td>${esc(a.model || "")}</td><td>${esc(a.application_text || "")}</td><td>${yr(a)}</td><td>${esc(a.axle || "")}</td><td>${esc(a.side || "")}</td><td>${esc(a.source || "")}</td></tr>`)))}
      ${sec("Estrutura (componentes)", p.components.length, T(["Seq.", "Componente", "Descrição", "Qtd"], p.components.map(c => `<tr><td>${c.seq ?? ""}</td><td>${esc(c.component_code)}</td><td>${esc(c.component_desc || "")}</td><td>${c.qty ?? ""}</td></tr>`)))}
      ${sec("Certificados Inmetro", p.certificates.length, T(["Nº Inmetro", "Família", "Descrição", "Fonte"], p.certificates.map(c => `<tr><td>${esc(c.inmetro_number || "")}</td><td>${esc(c.family || "")}</td><td>${esc(c.cert_description || "")}</td><td>${esc(c.source || "")}</td></tr>`)))}
      ${sec("Fornecedores (ERP)", p.supplier_items.length, T(["Fornecedor", "Item ERP", "Tipo", "Cód. fornecedor 2"], p.supplier_items.map(c => `<tr><td>${esc(c.supplier_name || "")}</td><td>${esc(c.erp_code || "")}</td><td>${esc(c.item_type || "")}</td><td>${esc(c.supplier_code2 || "")}</td></tr>`)))}
      ${sec("Desenvolvimento (R&D)", p.rd.length, T(["Tipo", "Status", "Fornecedor", "Veículo", "Aplicação", "Anos"], p.rd.map(r => `<tr><td>${esc(r.suggestion || "")}</td><td>${esc(r.status || "")}</td><td>${esc(r.supplier || "")}</td><td>${esc(r.vehicle || "")}</td><td>${esc(r.application_text || "")}</td><td>${yr({ year_from: r.year_from, year_to: r.year_to })}</td></tr>`)))}
      ${sec("Compra de amostras", p.samples.length, p.samples.map(s => `SC ${esc(s.sc_number || "–")} · ${esc(s.sample_code || "")} · ${esc(s.supplier || "")} · ${esc(s.stage)}`).join("<br>"))}
      ${sec("Pendências", p.pendencies.length, T(["Tipo", "Campo", "Descrição", "Status"], p.pendencies.map(x => `<tr><td>${esc(x.kind)}</td><td>${esc(x.field || "")}</td><td>${esc(x.description || "")}</td><td>${esc(x.status)}</td></tr>`)))}
      ${sec("Sugestões de equivalência", p.equivalences.length, p.equivalences.map(e => `${esc(e.a_code)} × ${esc(e.b_code)} — ${e.score}% (${e.confidence}) · ${e.status}`).join("<br>"))}`;
      dlg.showModal(); dwBlocks(dlg); fichaServer(p);
    } catch (e) { alert(e.message); }
  }
  function fichaServer(p) {   // vendas, estoque e pedidos de compra que vêm do servidor (se já sincronizados)
    const box = $("#fch-srv"); if (!box) return; const s = p.sales || {}, st = p.stock || {}, pu = p.purchases || {};
    if (!s.available && !st.available && !pu.available) return;
    box.innerHTML = `<div class="dwb srvx"><div class="dwb-h"><b>Vendas, estoque e compras</b><small class="muted">dados do servidor</small></div><div class="srvx-grid">
      ${s.available ? `<div><div id="fch-sales" class="chart mini"></div><small class="muted">${num(s.total_qty)} un. · ${brl(s.total_value)} em 12 meses</small></div>` : ""}
      ${st.available ? `<div class="kpis"><div><span class="num">${num(st.total)}</span><small>em estoque</small></div><div><span class="num">${num(st.reserved)}</span><small>reservado</small></div></div>` : ""}
      ${pu.available ? `<div class="kpis"><div><span class="num">${num(pu.pending)}</span><small>em pedidos de compra pendentes</small></div></div>` : ""}</div></div>`;
    if (s.available) PSDCharts.bars($("#fch-sales"), { x: s.months.map(m => m.month), series: [{ name: "Vendas", y: s.months.map(m => m.qty), color: "#5aa9ff" }], height: 150 });
  }

  // ---------- lista genérica com filtros e paginação ----------
  function listView({ form, endpoint, head, row, note = "", xlsx = "", init = null, after = null }) {
    root.innerHTML = `${note}<form class="toolbar">${form}<button type="reset" class="btn ghost sm">Limpar filtros</button></form><div class="toolbar"><span class="summary" id="sum"></span><span style="flex:1"></span>${xlsx ? '<a class="btn" id="dl" href="#">⬇ Baixar Excel</a>' : ""}</div><div id="out"></div><div class="pager" id="pg"></div><div id="xtra"></div>`;
    const f = $("form", root); let pg = 1, t;
    const load = async () => {
      try {
        if (xlsx) $("#dl").href = "/api/export/" + xlsx + ".xlsx?" + qs(Object.fromEntries(new FormData(f)));
        const d = await J(endpoint + "?" + qs({ ...Object.fromEntries(new FormData(f)), page: pg }));
        const pages = Math.max(1, Math.ceil(d.total / d.size));
        $("#sum").textContent = d.total.toLocaleString("pt-BR") + " resultado(s)";
        $("#out").innerHTML = d.rows.length ? T(head, d.rows.map(row)) : empty("Nenhum resultado para esses filtros."); dwFill($("#out"));
        $("#pg").innerHTML = pages > 1 ? `<button class="btn ghost" data-p="${pg - 1}" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button class="btn ghost" data-p="${pg + 1}" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
        if (after) await after(Object.fromEntries(new FormData(f)), d);
        return d;
      } catch (e) { fail(e); }
    };
    f.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => { pg = 1; load(); }, 300); });
    f.addEventListener("submit", e => { e.preventDefault(); pg = 1; load(); });
    $("#pg").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; load(); scrollTo(0, 0); } });
    return (async () => { if (init) await init(f); url.forEach((v, k) => { const i = f.elements[k]; if (i) i.value = v; }); f.addEventListener("reset", () => setTimeout(() => { pg = 1; load(); }, 0)); return load(); })();
  }
  const inp = (n, ph, w = "") => `<input name="${n}" placeholder="${ph}" ${w}>`;
  const sel = (n, lab, opts) => `<select name="${n}"><option value="">${lab}</option>${opts.map(o => `<option value="${o[0]}">${o[1]}</option>`).join("")}</select>`;
  const prodRow = p => `<tr><td>${p.catalog_position ?? "–"}</td><td>${lnk(p.id, p.perfect_code)}</td><td>${esc(p.description || "")}${(p.via || []).length ? `<div class="via">${p.via.map(v => `<span class="xchip ${v.type === "concorrente" ? "" : "more"}" title="Código ${esc(v.type)} que casou com a busca">${esc(v.brand || v.type)} ${esc(v.code)}</span>`).join(" ")}</div>` : ""}</td><td>${SYS[p.system_type] || "–"}</td><td>${num(p.lmin_mm)}</td><td>${num(p.lmax_mm)}</td><td>${p.fob != null ? `${p.fob}${p.fob_supplier ? ` <small class="muted">${esc(p.fob_supplier)}</small>` : ""}` : "–"}</td><td>${p.apps}</td><td>${p.ncodes}</td><td>${p.pend ? `<span class="badge warn">${p.pend}</span>` : ""}</td>${dwCol(p.perfect_code)}</tr>`;
  const prodHead = ["Pos. catálogo", "Código PERFECT", "Descrição", "Sistema", "Lmin", "Lmax", "FOB (US$)", "Aplic.", "Códigos", "Pend.", "Desenho"];
  const fillSel = (el, items) => { if (!el) return; const keep = el.options[0]; el.innerHTML = ""; el.appendChild(keep); items.forEach(([v, l]) => el.add(new Option(l ?? v, v))); };
  const initLists = async f => { const L = await J("/api/filters"); fillSel(f.elements.make, L.makes.map(x => [x])); fillSel(f.elements.model, L.models.map(x => [x])); fillSel(f.elements.year, L.years.map(y => [String(y)]));
    f.elements.make.addEventListener("change", async () => { const m = f.elements.make.value, cur = f.elements.model.value; const L2 = await J("/api/filters" + (m ? "?make=" + encodeURIComponent(m) : "")); fillSel(f.elements.model, L2.models.map(x => [x])); if (L2.models.includes(cur)) f.elements.model.value = cur; }); };
  const tag = k => `<span class="tag ${k === "Catálogo" ? "cat" : k.replace("-", "")}">${k}</span>`, clip = t => `<span class="clip" title="${esc(t || "")}">${esc(t || "")}</span>`;
  const AX = [["dianteiro", "Dianteiro"], ["traseiro", "Traseiro"]], SD = [["direito", "Direito"], ["esquerdo", "Esquerdo"]];

  // ---------- Em desenvolvimento (DES) e Em redesenvolvimento (R-D) ----------
  const FLG = Object.fromEntries(PSD_STATUS.defs.map(d => [d.key, [d.label, d.cls, d.group]])), FGROUPS = PSD_STATUS.groups;   // status oficiais (statuses.py)
  const flagSel = () => `<select name="flag"><option value="">Controle de status</option>${FGROUPS.map(g => `<optgroup label="${esc(g.label)}"><option value="grupo_${g.key}">Todos de ${esc(g.label)}</option>${Object.keys(FLG).filter(x => FLG[x][2] === g.key).map(x => `<option value="${x}">${esc(FLG[x][0])}</option>`).join("")}</optgroup>`).join("")}<option value="nenhum">Sem pendência</option></select>`;
  const flagChips = fs => (fs || []).length ? fs.map(k => `<span class="fchip ${FLG[k][1]}">${FLG[k][0]}</span>`).join("") : '<span class="muted">–</span>';
  const xchips = (cs, max = 99) => cs.slice(0, max).map(c => `<span class="xchip"><b>${esc(c.brand || "")}</b> ${esc(c.code)}</span>`).join("") + (cs.length > max ? `<span class="xchip more">+${cs.length - max}</span>` : "");
  const flagPanel = (k, code, fl) => `<div class="fpanel" data-fk="${k}" data-fc="${esc(code)}"><h4>Controle de status</h4>${FGROUPS.map(g => { const ks = Object.keys(FLG).filter(x => FLG[x][2] === g.key);
    return `<div class="fgroup"><h5>${esc(g.label)}</h5><div class="fgrid2">${ks.map(key => { const s = fl[key], cls = FLG[key][1];
      return `<label class="swl ${cls}"><span class="sw"><input type="checkbox" data-fl="${key}" ${s.value ? "checked" : ""}><i></i></span><span><b>${FLG[key][0]}</b><small>${s.manual ? "marcação manual" + (s.by ? " · " + esc(s.by) : "") + ` · <a href="#" data-flauto="${key}">voltar ao automático</a>` : s.auto ? "indicado pelo servidor" : "automático (sem indicação no servidor)"}</small></span></label>`; }).join("")}</div></div>`; }).join("")}</div>`;
  const rdOpen = async (k, code) => { try { const d = await J(`/api/rd/${k}/item/` + encodeURIComponent(code)); const lab = k === "des" ? "DESENVOLVIMENTO" : "REDESENVOLVIMENTO", other = d.other.map(o => o.suggestion);
    dlg.innerHTML = `<div class="dh"><div><h2>${esc(d.code)} ${tag(lab)} ${other.map(tag).join(" ")}</h2><p>${esc(d.description || "")}</p></div><div>${d.product ? `<a class="btn ghost" href="#" data-ficha="${d.product.id}">Ficha do catálogo (${esc(d.product.perfect_code)})</a> ` : ""}<button class="btn ghost" data-close>Fechar</button></div></div>
      ${other.length ? `<div class="notice">Este código também consta em <b>${other.join(", ")}</b>.</div>` : ""}
      <div class="curline"><span class="cur up">▲ Curtiu ${d.curtiu || 0}</span><span class="cur down">▼ Não curtiu ${d.nao_curtiu || 0}</span></div>
      ${k === "rd" ? `<div class="vpanel" data-vc="${esc(d.code)}"><b>Validação</b> ${(d.validations || []).length ? d.validations.map(v => `<span class="vchip">enviada em ${dmy(v.sent_at)}${v.by_user ? " · " + esc(v.by_user) : ""} <a href="#" data-vundo="${v.id}">desfazer</a></span>`).join("") : '<span class="muted">nenhuma validação enviada registrada.</span>'}<button class="btn sm" data-vsend="${esc(d.code)}">Marcar validação enviada</button><small class="muted">A meta de Redesenvolvimento conta quando o status passar de PENDENTE CONFIRMAÇÃO para ITEM RECEBIDO.</small></div>` : ""}
      ${d.product ? "" : '<p class="muted">Ainda não está no catálogo.</p>'}
      ${flagPanel(k, d.code, d.flags)}
      ${d.cross && d.cross.length ? `<div class="xref"><b>Referência cruzada:</b> ${xchips(d.cross)}</div>` : ""}
      <div data-dwblock="${esc(d.code)}" data-dwkind="projeto"></div>
      ${d.product ? "" : `<div data-dwblock="${esc(d.code)}"></div>`}
      ${d.info && Object.keys(d.info).length ? `<details class="sec"><summary><b>Todas as informações do servidor</b> <span class="badge">${Object.keys(d.info).length}</span></summary><div class="infogrid">${Object.entries(d.info).map(([k, v]) => `<div><small>${esc(k)}</small><b>${esc(v)}</b></div>`).join("")}</div></details>` : ""}
      <h4>Aplicações (${d.rows.length})</h4>` + T(["Montadora", "Veículo", "Aplicação", "Anos", "Status", "Pend. desenho", "Pend. validação", "Fornecedor", "Amostra comprada", "Amostra enviada"], d.rows.map(r => `<tr><td>${esc(r.make || "")}</td><td>${esc(r.vehicle || "")}</td><td>${esc(r.application_text || "")}</td><td>${yr(r)}</td><td>${esc(r.status || "")}</td><td>${esc(r.drawing_substatus || "")}</td><td>${esc(r.validation_substatus || "")}</td><td>${esc(r.supplier || "")}</td><td>${r.bought || ""}</td><td>${r.sent || ""}</td></tr>`)) +
      `<h4>Compras de amostra ligadas (${d.samples.length})</h4>` + (d.samples.length ? d.samples.map(x => `SC ${esc(x.sc_number || "–")} · ${esc(x.sample_code || "")} · ${esc(x.supplier || "")} · ${esc(x.stage)}`).join("<br>") + ` <a href="/amostras?q=${encodeURIComponent(d.code)}">abrir em Compra de amostras</a>` : '<p class="muted">Nenhuma.</p>') +
      `<h4>Ensaios de damping force (${d.damping.length})</h4>` + (d.damping.length ? `<a href="/damping">ver em Damping force</a>` : '<p class="muted">Nenhum.</p>'); dlg.showModal(); dwBlocks(dlg); } catch (e) { alert(e.message); } };
  dlg.addEventListener("click", async e => {   // validação enviada (REDESENVOLVIMENTO)
    const s = e.target.closest("[data-vsend]"), u = e.target.closest("[data-vundo]"); if (!s && !u) return; e.preventDefault();
    try { if (s) await post("/api/validations", { code: s.dataset.vsend, kind: "REDESENVOLVIMENTO" }); else await J("/api/validations/" + u.dataset.vundo, { method: "DELETE" }); const c = (s || u).closest(".vpanel").dataset.vc; dlg.close(); rdOpen("rd", c); } catch (er) { alert(er.message); } });
  const flagRefresh = () => { const f = $("form.toolbar", root); if (f) f.dispatchEvent(new Event("input", { bubbles: true })); };
  dlg.addEventListener("change", async e => { const t = e.target.closest("[data-fl]"), pn = e.target.closest(".fpanel"); if (!t || !pn) return;
    try { const r = await post(`/api/rd/${pn.dataset.fk}/item/${encodeURIComponent(pn.dataset.fc)}/flags`, { flag: t.dataset.fl, value: t.checked }); pn.outerHTML = flagPanel(pn.dataset.fk, pn.dataset.fc, r.flags); flagRefresh(); } catch (er) { alert(er.message); t.checked = !t.checked; } });
  dlg.addEventListener("click", async e => { const a = e.target.closest("[data-flauto]"), pn = e.target.closest(".fpanel"); if (!a || !pn) return; e.preventDefault();
    try { const r = await post(`/api/rd/${pn.dataset.fk}/item/${encodeURIComponent(pn.dataset.fc)}/flags`, { flag: a.dataset.flauto, value: null }); pn.outerHTML = flagPanel(pn.dataset.fk, pn.dataset.fc, r.flags); flagRefresh(); } catch (er) { alert(er.message); } });
  document.addEventListener("click", e => { const a = e.target.closest("[data-rd]"); if (a) { e.preventDefault(); rdOpen(a.dataset.rd, a.dataset.code); } });
  function rdPage(k) {
    const lab = k === "des" ? "DESENVOLVIMENTO" : "REDESENVOLVIMENTO", name = k === "des" ? "desenvolvimento" : "redesenvolvimento";
    return listView({ endpoint: `/api/rd/${k}`, xlsx: name, init: async f => { const fc = await J(`/api/rd/${k}/facets`), o = x => [x.v, `${x.v} (${x.n})`];
        fillSel(f.elements.status, fc.status.map(o)); fillSel(f.elements.drawing, fc.drawing.map(o)); fillSel(f.elements.validation, fc.validation.map(o)); fillSel(f.elements.supplier, fc.supplier.map(o)); fillSel(f.elements.make, fc.make.map(x => [x.v, `${x.v} (${x.n})`]));
        $("#rdc").innerHTML = `<div class="card"><span class="num sm">${fc.total}</span><small>${k === "des" ? "itens em desenvolvimento" : "itens em redesenvolvimento"} (${fc.lines} linhas)</small></div>` + fc.status.map(x => `<button type="button" class="card stat" data-st="${esc(x.v)}"><span class="num sm">${x.n}</span><small>${esc(x.v)}</small></button>`).join("");
        $("#rdc").insertAdjacentHTML("afterend", `<h4 class="fh">Controle de status <small class="muted">— clique para filtrar</small></h4><div id="rdf">` + FGROUPS.map(g => `<div class="fg"><h5>${esc(g.label)}</h5><div class="cards mini-cards flrow">` + Object.keys(FLG).filter(x => FLG[x][2] === g.key).map(key => `<button type="button" class="card stat fl ${FLG[key][1]} ${(fc.flags[key] || 0) ? "" : "zero"}" data-flt="${key}"><span class="num sm">${fc.flags[key] || 0}</span><small>${FLG[key][0]}</small></button>`).join("") + `</div></div>`).join("") + `</div>`);
        $("#rdf").addEventListener("click", e => { const g = e.target.closest("[data-flt]"); if (g) { f.elements.flag.value = f.elements.flag.value === g.dataset.flt ? "" : g.dataset.flt; f.dispatchEvent(new Event("input", { bubbles: true })); $$("#rdf .fl").forEach(x => x.classList.toggle("on", x.dataset.flt === f.elements.flag.value)); } });
        $("#rdc").addEventListener("click", e => { const b = e.target.closest("[data-st]"), g = e.target.closest("[data-flt]"); if (b) { f.elements.status.value = b.dataset.st; f.dispatchEvent(new Event("input", { bubbles: true })); } if (g) { f.elements.flag.value = f.elements.flag.value === g.dataset.flt ? "" : g.dataset.flt; f.dispatchEvent(new Event("input", { bubbles: true })); } });
        const pf = new URLSearchParams(location.search).get("flag"); if (pf) f.elements.flag.value = pf;
        // marcação em lote: seleciona linhas e aplica um controle de status
        const bar = document.createElement("div"); bar.className = "bulkbar"; bar.hidden = true;
        bar.innerHTML = `<b id="bn">0</b> selecionado(s) <select id="bf">${Object.entries(FLG).map(([key, v]) => `<option value="${key}">${v[0]}</option>`).join("")}</select><button type="button" class="btn sm" data-bv="1">Marcar</button><button type="button" class="btn ghost sm" data-bv="0">Desmarcar</button><button type="button" class="btn ghost sm" data-bv="auto">Voltar ao automático</button><button type="button" class="btn ghost sm" data-bv="x">Limpar seleção</button>`;
        $("#out").before(bar);
        const sel = () => $$(".rdsel:checked", root).map(c => c.value), upd = () => { const n = sel().length; bar.hidden = !n; $("#bn", bar).textContent = n; };
        root.addEventListener("change", e => { if (e.target.classList.contains("rdall")) $$(".rdsel", root).forEach(c => c.checked = e.target.checked); if (e.target.matches(".rdall,.rdsel")) upd(); });
        bar.addEventListener("click", async e => { const b = e.target.closest("[data-bv]"); if (!b) return; if (b.dataset.bv === "x") { $$(".rdsel,.rdall", root).forEach(c => c.checked = false); return upd(); }
          const codes = sel(); if (!codes.length) return; const val = b.dataset.bv === "auto" ? null : b.dataset.bv === "1";
          if (!confirm(`${val === null ? "Voltar ao automático" : val ? "Marcar" : "Desmarcar"} “${FLG[$("#bf", bar).value][0]}” em ${codes.length} item(ns)?`)) return;
          try { await post(`/api/rd/${k}/flags/bulk`, { codes, flag: $("#bf", bar).value, value: val }); bar.hidden = true; f.dispatchEvent(new Event("input", { bubbles: true })); } catch (er) { alert(er.message); } }); },
      note: `<p class="muted">${k === "des" ? "DESENVOLVIMENTO = item novo em desenvolvimento." : "REDESENVOLVIMENTO = item do catálogo com outro fornecedor."} Cada linha é um código distinto; um código pode ter várias aplicações. Fonte oficial: servidor SQL (DESENVOLVIMENTO_PRODUTOS), atualizado diariamente. Clique no código para ver o detalhe.</p><div class="cards mini-cards" id="rdc"></div>`,
      form: inp("q", "Buscar código, descrição, veículo, aplicação, fornecedor…", 'style="flex:1;min-width:240px"') + sel("status", "Status", []) + sel("drawing", "Pendência de desenho", []) + sel("validation", "Pendência de validação", []) + sel("supplier", "Fornecedor", []) + sel("make", "Montadora", []) +
        flagSel() + sel("catalog", "No catálogo?", [["sim", "Sim, já no catálogo"], ["nao", "Não está no catálogo"]]) + sel("sample", "Amostra", [["comprada", "Comprada"], ["enviada", "Enviada"], ["nenhuma", "Sem amostra"]]),
      head: ["<input type=\"checkbox\" class=\"rdall\" title=\"Selecionar a página\">", "Código", "Controle de status", "Descrição", "Montadora(s)", "Veículo(s)", "Linhas", "Status", "Pend. desenho", "Pend. validação", "Fornecedor", "Curtiu", "Amostra comprada", "Amostra enviada", "Catálogo", "Desenho"],
      row: r => `<tr><td><input type="checkbox" class="rdsel" value="${esc(r.code)}"></td><td><a href="#" data-rd="${k}" data-code="${esc(r.code)}">${esc(r.code)}</a>${r.also_other ? ` ${tag(k === "des" ? "REDESENVOLVIMENTO" : "DESENVOLVIMENTO")}` : ""}</td><td class="fcell">${flagChips(r.flags)}</td><td>${clip(r.description)}</td><td>${clip(r.makes)}</td><td>${clip(r.vehicles)}</td><td>${r.n_rows}</td><td>${clip(r.statuses)}</td><td>${clip(r.drawing)}</td><td>${clip(r.validation)}</td><td>${clip(r.suppliers)}</td><td class="curcell"><span class="cur up" title="Curtiu">▲ ${r.curtiu || 0}</span><span class="cur down" title="Não curtiu">▼ ${r.nao_curtiu || 0}</span></td><td>${r.bought || "–"}</td><td>${r.sent || "–"}</td><td>${r.product_id ? lnk(r.product_id, "ficha") : "–"}</td>${dwCol(r.code)}</tr>` });
  }
  // ---------- desenhos: miniaturas, bloco nos cadastros e a página do módulo ----------
  const FMT = { pdf: "PDF", dwg: "DWG", dxf: "DXF", step: "STEP", stp: "STEP", igs: "IGES", iges: "IGES", png: "PNG", jpg: "JPG", jpeg: "JPG", gif: "GIF", webp: "WEBP", svg: "SVG", zip: "ZIP" };
  const fext = e => String(e || "").replace(/^\./, "").toLowerCase();
  const dwTile = (id, ext, big = false) => ["pdf", "png", "jpg", "jpeg", "gif", "webp", "bmp"].includes(fext(ext))
    ? `<img class="dwimg" loading="lazy" alt="" src="/api/drawings/thumb/${id}" data-ext="${esc(fext(ext))}">` : `<span class="ftile ${big ? "big" : ""}"><b>${esc(FMT[fext(ext)] || fext(ext).toUpperCase() || "ARQ")}</b></span>`;
  document.addEventListener("error", e => { const i = e.target; if (i.classList && i.classList.contains("dwimg")) i.replaceWith(Object.assign(document.createElement("span"), { className: "ftile", innerHTML: `<b>${esc(FMT[i.dataset.ext] || i.dataset.ext.toUpperCase())}</b>` })); }, true);
  const kb = n => n > 1048576 ? (n / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(n / 1024)) + " KB";
  const dmy = s => s ? String(s).slice(0, 10).split("-").reverse().join("/") : "";
  const KL = { desenho: "Desenho", projeto: "Projeto PERFECT" };
  async function dwBlocks(scope) {   // "Desenho / Projeto PERFECT vigente" dentro da ficha, do detalhe de DES/R-D e do pedido de amostra
    for (const el of $$("[data-dwblock]", scope)) {
      const code = el.dataset.dwblock, kind = el.dataset.dwkind || "desenho", lab = KL[kind]; if (!code) continue;
      try {
        const d = await J(`/api/drawings/code/${encodeURIComponent(code)}?kind=${kind}`);
        el.innerHTML = `<div class="dwb ${kind}"><div class="dwb-h"><b>${lab}</b> <span class="rev">${esc(d.label)}</span> <span class="muted">vigente${d.n_revisions > 1 ? ` · ${d.n_revisions - 1} revisão(ões) anterior(es) guardada(s)` : ""}</span> <a href="/desenhos?kind=${kind}&open=${encodeURIComponent(code)}" class="dwb-l">Ver histórico e arquivos</a></div>
          <div class="dwb-r">${d.current.map(f => `<a class="dwt" href="/api/drawings/file/${f.id}" target="_blank" rel="noopener" title="${esc(f.filename)}"><span class="dwt-i">${dwTile(f.id, f.ext)}</span><small>${esc(f.filename)}</small></a>`).join("")}</div></div>`;
      } catch (e) { el.innerHTML = `<div class="dwb none ${kind}"><b>${lab}</b> <span class="muted">${kind === "projeto" ? "Nenhum projeto PERFECT anexado para este código." : "Nenhum desenho cadastrado para este código."}</span> <a href="/desenhos?kind=${kind}" class="dwb-l">Anexar em Desenhos</a></div>`; }
    }
  }
  async function dwFill(scope) {      // colunas/etiquetas "Desenho" e "Projeto": Rev. vigente (data-dw = código; data-dwk = tipo)
    const els = $$("[data-dw]", scope); if (!els.length) return;
    for (const kind of ["desenho", "projeto"]) {
      const g = els.filter(e => (e.dataset.dwk || "desenho") === kind); if (!g.length) continue;
      try {
        const m = await J(`/api/drawings/lookup?kind=${kind}&codes=` + encodeURIComponent([...new Set(g.map(e => e.dataset.dw))].join(",")));
        g.forEach(e => { const x = m[e.dataset.dw], chip = e.dataset.chip; e.innerHTML = x ? `<a href="/desenhos?kind=${kind}&open=${encodeURIComponent(e.dataset.dw)}" class="rev ${kind === "projeto" ? "prj" : ""}" title="${KL[kind]} · ${x.revs} revisão(ões) guardada(s)">${chip ? KL[kind] + " " : ""}${esc(x.label)}</a>` : (chip ? "" : '<span class="muted">–</span>'); });
      } catch (e) { /* informativo */ }
    }
  }
  const dwCol = (c, kind) => `<td><span data-dw="${esc(c)}" ${kind ? `data-dwk="${kind}"` : ""}></span></td>`;

  async function dwCollect(dt) {   // arquivos e pastas soltos na área de envio
    const out = [], walk = async en => {
      if (en.isFile) out.push(await new Promise(r => en.file(r)));
      else if (en.isDirectory) { const rd = en.createReader(); let b; do { b = await new Promise(r => rd.readEntries(r)); for (const x of b) await walk(x); } while (b.length); }
    };
    for (const it of dt.items || []) { const en = it.webkitGetAsEntry && it.webkitGetAsEntry(); if (en) await walk(en); }
    return out.length ? out : [...dt.files];
  }

  const dwPrevOk = e => ["pdf", "png", "jpg", "jpeg", "gif", "webp", "bmp"].includes(fext(e));
  const dwNav = { list: [], onDone: null };   // códigos da galeria atual (setas ← → no visualizador)

  function desenhos() {
    let kind = new URLSearchParams(location.search).get("kind") === "projeto" ? "projeto" : "desenho";
    const TXT = { desenho: "Solte os arquivos de desenho em <b>qualquer formato</b>. Aceita também um <b>arquivo ZIP</b> com vários desenhos. O sistema lê a <b>origem</b> (nome começando com <b>RED</b> = redesenvolvimento, <b>DES</b> = desenvolvimento), o <b>código</b> e a <b>revisão</b> pelo nome (ex.: <code>RED_AMD0170_REV02.pdf</code>), vincula a todos os cadastros — catálogo, desenvolvimento e redesenvolvimento — e guarda as revisões anteriores. Nos cadastros aparece sempre a <b>vigente</b>.",
      projeto: "Anexe aqui o <b>Projeto PERFECT</b> (ex.: <code>1BP31901AB_REV01.pdf</code>). Ele fica visível no cadastro dos itens <b>em desenvolvimento que ainda não estão no catálogo</b>, na <b>Compra de amostras</b> e no <b>Envio de amostra</b>. Mesma lógica: código e revisão pelo nome, revisões anteriores guardadas." };
    root.innerHTML = `<div class="seg" id="dw-kind"><button type="button" data-k="desenho">Desenhos técnicos</button><button type="button" data-k="projeto">Projeto PERFECT</button></div>
      <section class="dw-hero" id="hero"><div class="dw-hero-t"><h2 id="dw-h2"></h2><p id="dw-p"></p></div>
      <label class="dw-drop" id="dz"><svg width="34" height="34" viewBox="0 0 24 24"><path d="M12 16V4M7 9l5-5 5 5M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3"/></svg>
        <span class="dw-dt"><b>Arraste arquivos ou uma pasta para cá</b><span class="muted">PDF · DWG · DXF · STEP · imagens · ZIP · qualquer formato</span></span>
        <span class="dw-btns"><span class="btn">Escolher arquivos ou ZIP</span><button type="button" class="btn ghost" id="dw-folder">Escolher pasta</button></span>
        <input type="file" id="dw-f" multiple hidden><input type="file" id="dw-d" webkitdirectory hidden></label></section>
      <p id="dw-msg" class="imp-msg" role="status"></p><div class="dw-stats" id="dw-stats"></div>
      <form class="toolbar dw-tb" id="dw-form"><input name="q" placeholder="Buscar código, descrição ou nome do arquivo…" style="flex:1;min-width:240px">
        <select name="where"><option value="">Todos os cadastros</option><option value="cat">No catálogo</option><option value="des">Em desenvolvimento</option><option value="rd">Em redesenvolvimento</option><option value="sem">Sem vínculo</option></select>
        <select name="origin"><option value="">Origem: todas</option><option value="DESENVOLVIMENTO">Origem DES</option><option value="REDESENVOLVIMENTO">Origem RED</option></select>
        <select name="ext"><option value="">Todos os formatos</option>${[".pdf", ".dwg", ".dxf", ".step", ".png", ".jpg"].map(x => `<option value="${x}">${x.slice(1).toUpperCase()}</option>`).join("")}</select>
        <select name="sort"><option value="recent">Mais recentes</option><option value="code">Código (A–Z)</option><option value="rev">Mais revisões</option></select>
        <span class="seg sm" id="dw-size" title="Tamanho dos cartões"><button type="button" data-s="170">P</button><button type="button" data-s="215" class="on">M</button><button type="button" data-s="290">G</button></span>
        <a class="btn" id="dw-xl" href="/api/export/desenhos.xlsx">⬇ Excel</a></form>
      <div class="summary" id="dw-sum"></div><div class="dw-grid" id="dw-grid"></div><div class="pager" id="dw-pg"></div>`;
    const msg = (t, err) => { const m = $("#dw-msg"); m.textContent = t; m.className = "imp-msg" + (err ? " err" : ""); };
    const f = $("#dw-form"); let pg = 1, t;
    const setKind = k => { kind = k; $$("#dw-kind button").forEach(b => b.classList.toggle("on", b.dataset.k === k)); $("#dw-h2").textContent = k === "projeto" ? "Projeto PERFECT" : "Desenhos técnicos"; $("#dw-p").innerHTML = TXT[k]; $("#hero").classList.toggle("projeto", k === "projeto");
      $("#dw-xl").href = "/api/export/desenhos.xlsx"; history.replaceState(null, "", k === "projeto" ? "?kind=projeto" : location.pathname); };
    const ICO = { codes: "M4 5a2 2 0 012-2h12a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2zM8 8h8M8 12h8M8 16h5", files: "M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8zM14 3v5h5", old: "M12 8v5l3 2M3 12a9 9 0 109-9 9 9 0 00-6.4 2.6L3 8M3 3v5h5", orph: "M10 13a5 5 0 007 0l3-3a5 5 0 00-7-7l-1 1M14 11a5 5 0 00-7 0l-3 3a5 5 0 007 7l1-1", miss: "M12 3l10 18H2zM12 10v5M12 18v.5" };
    const stats = async () => { try { const s = await J("/api/drawings/stats?kind=" + kind);
      $("#hero").classList.toggle("compact", s.files > 0);
      $("#dw-stats").innerHTML = [["codes", "Códigos com desenho", s.codes, ""], ["files", "Arquivos guardados", s.files, ""], ["old", "Revisões anteriores", s.old, "guardadas no histórico"], ["orph", "Sem vínculo", s.orphans, s.orphans ? "clique para ver" : "", "sem"], ["miss", kind === "projeto" ? "DES/R-D fora do catálogo sem projeto" : "Catálogo sem desenho", s.missing, ""]]
        .map(([k, l, v, h, w]) => `<div class="dws ${w ? "link" : ""}" ${w ? `data-w="${w}"` : ""}><svg viewBox="0 0 24 24"><path d="${ICO[k]}"/></svg><div><span class="num sm">${num(v)}</span><small>${l}${h ? ` · ${h}` : ""}</small></div></div>`).join(""); } catch (e) { } };
    const load = async () => { try {
      const d = await J("/api/drawings?" + qs({ ...Object.fromEntries(new FormData(f)), kind, page: pg })), pages = Math.max(1, Math.ceil(d.total / d.size));
      $("#dw-sum").textContent = num(d.total) + " desenho(s)"; dwNav.list = d.rows.filter(c => c.code).map(c => c.code);
      $("#dw-grid").innerHTML = d.rows.length ? d.rows.map(c => c.code
        ? `<article class="dw-card" data-open="${esc(c.code)}" tabindex="0"><div class="dw-th"><div class="sk"></div>${dwTile(c.thumb_id, c.thumb_ext, true)}<span class="rev">${esc(c.label)}</span><span class="dw-ex">${c.exts.map(x => `<i>${esc(x)}</i>`).join("")}</span>
            <div class="dw-ov"><span class="btn sm">Visualizar</span><a class="btn ghost sm" href="/api/drawings/file/${c.thumb_id}?download=1" title="Baixar o arquivo vigente">⬇</a></div></div>
            <div class="dw-bd"><b>${esc(c.code)}</b><span class="clip" title="${esc(c.description || "")}">${esc(c.description || (c.registered ? "" : "Código ainda não cadastrado"))}</span>
            <div class="dw-tags">${c.origin ? `<span class="tag org ${c.origin === "REDESENVOLVIMENTO" ? "red" : "des"}" title="Origem pelo prefixo do nome do arquivo">${c.origin === "REDESENVOLVIMENTO" ? "RED" : "DES"}</span> ` : ""}${c.registries.map(tag).join(" ")}</div><small class="muted">${dmy(c.updated)} · ${c.n_revisions} revisão(ões)</small></div></article>`
        : `<article class="dw-card orph" data-orph="${c.file_id}" data-name="${esc(c.filename)}" tabindex="0"><div class="dw-th"><div class="sk"></div>${dwTile(c.thumb_id, c.thumb_ext, true)}<span class="rev warn">Sem código</span></div><div class="dw-bd"><b class="clip" title="${esc(c.filename)}">${esc(c.filename)}</b><small class="muted">Clique para informar o código</small></div></article>`).join("")
        : empty("Nenhum desenho com esses filtros. Arraste os arquivos para a área acima.");
      $("#dw-pg").innerHTML = pages > 1 ? `<button class="btn ghost" data-p="${pg - 1}" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button class="btn ghost" data-p="${pg + 1}" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
    } catch (e) { fail(e); } };
    const refresh = () => { stats(); load(); }; dwNav.onDone = refresh;
    f.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => { pg = 1; load(); }, 300); }); f.addEventListener("submit", e => e.preventDefault());
    $("#dw-pg").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; load(); scrollTo(0, 0); } });
    $("#dw-size").onclick = e => { const b = e.target.closest("[data-s]"); if (!b) return; $$("#dw-size button").forEach(x => x.classList.toggle("on", x === b)); $("#dw-grid").style.setProperty("--cw", b.dataset.s + "px"); };
    $("#dw-stats").onclick = e => { const s = e.target.closest("[data-w]"); if (s) { f.elements.where.value = s.dataset.w; pg = 1; load(); } };
    const openCard = e => { if (e.target.closest("a")) return; const c = e.target.closest("[data-open],[data-orph]"); if (!c || (e.type === "keydown" && e.key !== "Enter")) return; c.dataset.open ? dwOpen(c.dataset.open, refresh, kind) : dwOrphan(+c.dataset.orph, c.dataset.name, refresh); };
    $("#dw-grid").addEventListener("click", openCard); $("#dw-grid").addEventListener("keydown", openCard);
    const send = async files => {
      if (!files.length) return; const fd = new FormData(); fd.append("kind", kind); files.forEach(x => fd.append("files", x, x.name));
      msg(`Enviando ${files.length} arquivo(s) para análise…`);
      try { const r = await J("/api/drawings/check", { method: "POST", body: fd }); msg(""); dwReview(r, refresh); } catch (e) { msg(e.message, true); }
    };
    $("#dw-f").onchange = e => { send([...e.target.files]); e.target.value = ""; };
    $("#dw-d").onchange = e => { send([...e.target.files]); e.target.value = ""; };
    $("#dw-folder").onclick = e => { e.preventDefault(); e.stopPropagation(); $("#dw-d").click(); };
    const dz = $("#dz"); ["dragenter", "dragover"].forEach(n => dz.addEventListener(n, e => { e.preventDefault(); dz.classList.add("over"); }));
    ["dragleave", "drop"].forEach(n => dz.addEventListener(n, e => { e.preventDefault(); dz.classList.remove("over"); }));
    dz.addEventListener("drop", async e => { msg("Lendo os arquivos soltos…"); send(await dwCollect(e.dataTransfer)); });
    const p0 = new URLSearchParams(location.search); if (p0.get("q")) f.elements.q.value = p0.get("q");
    $("#dw-kind").onclick = e => { const b = e.target.closest("[data-k]"); if (!b || b.dataset.k === kind) return; setKind(b.dataset.k); pg = 1; refresh(); };
    setKind(kind); stats(); load().then(() => { if (p0.get("open")) dwOpen(p0.get("open"), refresh, kind); });
  }

  function dwReview(res, done) {
    const items = res.items, c = a => items.filter(i => i.action === a).length;
    const ACT = { nova: ["Novo desenho", "ok"], nova_revisao: ["Nova revisão", "new"], atualiza_revisao: ["Atualiza a revisão", "new"], revisao_antiga: ["Revisão antiga → histórico", "warn"], duplicado: ["Já existe: ignorado", "mut"], sem_vinculo: ["Sem código", "bad"] };
    const todo = items.filter(i => i.action !== "duplicado").length;
    dlg.classList.add("wide");
    dlg.innerHTML = `<div class="dh"><div><h2>Revisar envio de desenhos</h2><p>${items.length} arquivo(s) analisado(s). Confira o código e a revisão reconhecidos; nada foi gravado ainda.</p></div><div><button class="btn ghost" data-close>Cancelar</button></div></div>
      ${(res.zips || []).length ? `<div class="notice">ZIP lido: ${res.zips.map(z => `<b>${esc(z.zip)}</b> (${z.files} arquivo(s))`).join(", ")}. Regra: nome que começa com <b>RED</b> = REDESENVOLVIMENTO · <b>DES</b> = DESENVOLVIMENTO.</div>` : ""}${(res.warnings || []).length ? `<div class="notice warn">${res.warnings.map(esc).join("<br>")}</div>` : ""}<div class="dw-sumline">${[["Novos", c("nova")], ["Novas revisões", c("nova_revisao") + c("atualiza_revisao")], ["Histórico", c("revisao_antiga")], ["Ignorados", c("duplicado")], ["Sem código", c("sem_vinculo")]].map(([l, v]) => `<span><b>${v}</b> ${l}</span>`).join("")}</div>
      <div class="tbl dw-rev"><table><tr><th>Arquivo</th><th>Origem (prefixo)</th><th>Código(s) reconhecido(s)</th><th>Revisão</th><th>O que vai acontecer</th></tr>${items.map((i, n) => `<tr data-n="${n}" data-name="${esc(i.name)}"><td><span class="clip" title="${esc(i.name)}">${esc(i.name)}</span><small class="muted">${esc(i.ext.slice(1).toUpperCase())} · ${kb(i.size)}${i.source ? ` · do ZIP ${esc(i.source)}` : ""}</small></td>
        <td><select class="dw-org" ${i.action === "duplicado" ? "disabled" : ""}><option value="">— sem origem —</option><option value="DESENVOLVIMENTO" ${i.origin === "DESENVOLVIMENTO" ? "selected" : ""}>DESENVOLVIMENTO (DES)</option><option value="REDESENVOLVIMENTO" ${i.origin === "REDESENVOLVIMENTO" ? "selected" : ""}>REDESENVOLVIMENTO (RED)</option></select>${i.origin_auto ? '<small class="muted">deduzida pelo cadastro</small>' : ""}</td>
        <td><input class="dw-code" value="${esc(i.codes.join(", "))}" placeholder="informe o código" ${i.action === "duplicado" ? "disabled" : ""}>${i.unregistered ? '<small class="muted">ainda não cadastrado</small>' : ""}</td>
        <td><input class="dw-rev-i" size="4" value="${esc(i.rev_auto ? "" : i.rev_label)}" placeholder="${esc(i.rev_label)}" title="Vazio = automática" ${i.action === "duplicado" ? "disabled" : ""}></td>
        <td><span class="badge ${ACT[i.action][1]}">${ACT[i.action][0]}</span><small class="muted">${esc(i.note)}</small></td></tr>`).join("")}</table></div>
      <p id="dw-rmsg" class="imp-msg" role="status"></p>
      <div class="acts"><button class="btn" id="dw-go" ${todo ? "" : "disabled"}>Gravar ${todo} arquivo(s)</button><button class="btn ghost" data-close>Cancelar</button></div>`;
    dlg.addEventListener("close", () => dlg.classList.remove("wide"), { once: true });
    $("#dw-go").onclick = async () => {
      const ov = {}; $$("tr[data-n]", dlg).forEach(tr => { const code = $(".dw-code", tr).value.trim(), rev = $(".dw-rev-i", tr).value.trim(), origin = $(".dw-org", tr)?.value || ""; if (code || rev || origin) ov[tr.dataset.n] = { codes: code, rev, origin }; });
      const b = $("#dw-go"); b.disabled = true; $("#dw-rmsg").textContent = "Gravando…";
      try { const r = await post("/api/drawings/apply", { token: res.token, overrides: ov }), s = r.summary; dlg.close();
        root.insertAdjacentHTML("afterbegin", `<div class="notice">✔ ${s.novos} novo(s), ${s.revisoes} revisão(ões), ${s.ignorados} ignorado(s) · ${s.redesenvolvimento} REDESENVOLVIMENTO, ${s.desenvolvimento} DESENVOLVIMENTO${s.sem_origem ? `, ${s.sem_origem} sem prefixo RED/DES` : ""}${s.sem_vinculo ? `, ${s.sem_vinculo} sem código (vincule clicando no card)` : ""}. Os cadastros já mostram a revisão vigente.</div>`); done && done(); }
      catch (e) { b.disabled = false; $("#dw-rmsg").textContent = e.message; $("#dw-rmsg").className = "imp-msg err"; }
    };
    dlg.showModal();
  }

  async function dwOpen(code, done, kind = "desenho") {
    try {
      const d = await J(`/api/drawings/code/${encodeURIComponent(code)}?kind=${kind}`); let cur = d.current.find(x => dwPrevOk(x.ext)) || d.current[0], zoom = 1;
      const idx = dwNav.list.indexOf(d.code), prevC = idx > 0 ? dwNav.list[idx - 1] : null, nextC = idx >= 0 && idx < dwNav.list.length - 1 ? dwNav.list[idx + 1] : null;
      const src = f => fext(f.ext) === "pdf" ? `/api/drawings/thumb/${f.id}?big=1` : `/api/drawings/file/${f.id}`;
      const prev = f => { const e = fext(f.ext), url = "/api/drawings/file/" + f.id;
        if (dwPrevOk(e)) return `<div class="dw-stage" id="dws"><img id="dwimg" src="${src(f)}" alt="${esc(f.filename)}" ${e === "pdf" ? `data-pdf="${url}"` : ""}></div>`;
        if (e === "svg") return `<div class="dw-stage" id="dws"><img id="dwimg" src="${url}" alt="${esc(f.filename)}"></div>`;
        return `<div class="dw-nop">${dwTile(f.id, f.ext, true)}<p>Este formato não tem pré-visualização no navegador.</p><a class="btn" href="${url}?download=1">⬇ Baixar ${esc(f.filename)}</a></div>`; };
      const revFiles = d.history.map(h => ({ h, f: h.files.find(x => dwPrevOk(x.ext)) })).filter(x => x.f);
      dlg.classList.add("wide");
      dlg.innerHTML = `<div class="dh"><div><h2>${esc(d.code)} <span class="rev ${kind === "projeto" ? "prj" : ""}">${esc(d.label)}</span> ${kind === "projeto" ? '<span class="tag">Projeto PERFECT</span>' : ""} ${d.registries.map(tag).join(" ")}</h2><p>${esc(d.description || "")}</p></div>
        <div class="dw-hact"><button class="btn ghost" id="dw-prv" ${prevC ? "" : "disabled"} title="Desenho anterior (←)">‹</button><button class="btn ghost" id="dw-nxt" ${nextC ? "" : "disabled"} title="Próximo desenho (→)">›</button>
        ${d.product_id ? `<a class="btn ghost" href="#" data-ficha="${d.product_id}">Ficha</a>` : ""}${d.registries.includes("DESENVOLVIMENTO") ? `<a class="btn ghost" href="#" data-rd="des" data-code="${esc(d.code)}">Desenvolvimento</a>` : ""}${d.registries.includes("REDESENVOLVIMENTO") ? `<a class="btn ghost" href="#" data-rd="rd" data-code="${esc(d.code)}">Redesenvolvimento</a>` : ""}<button class="btn ghost" data-close>Fechar</button></div></div>
        <div class="dw-view"><div class="dw-main"><div class="dw-tools"><button type="button" data-z="-">−</button><span id="dwz">100%</span><button type="button" data-z="+">+</button><button type="button" data-z="0">Ajustar</button><button type="button" data-z="full">Tela cheia</button>
          ${revFiles.length > 1 ? '<button type="button" data-z="cmp" class="cmp">Comparar revisões</button>' : ""}<a class="dw-tl2" id="dwopen" href="/api/drawings/file/${cur.id}" target="_blank" rel="noopener">Abrir original ↗</a></div>
          <div class="dw-prev" id="dwp">${prev(cur)}</div></div>
        <aside><h4>Arquivos vigentes (${esc(d.label)})</h4><div class="dw-files">${d.current.map(f => `<button class="dw-f ${f.id === cur.id ? "on" : ""}" data-pv="${f.id}"><span class="dwt-i">${dwTile(f.id, f.ext)}</span><span><b class="clip" title="${esc(f.filename)}">${esc(f.filename)}</b><small>${kb(f.size)} · ${dmy(f.uploaded_at)}</small></span><a class="dw-dlb" href="/api/drawings/file/${f.id}?download=1" title="Baixar">⬇</a></button>`).join("")}</div>
        <h4>Histórico de revisões</h4><ol class="dw-tl">${d.history.map(h => `<li class="${h.current ? "cur" : ""}"><div><b>${esc(h.label)}</b> ${h.current ? '<span class="badge ok">vigente</span>' : '<span class="badge mut">anterior</span>'}</div>
          ${h.files.map(f => `<div class="dw-hf">${dwPrevOk(f.ext) ? `<span class="dw-mini"><img loading="lazy" src="/api/drawings/thumb/${f.id}" alt=""></span>` : `<span class="dw-mini"><i>${esc((f.ext || "").slice(1).toUpperCase())}</i></span>`}<div><span class="clip" title="${esc(f.filename)}">${esc(f.filename)}</span><small class="muted">${dmy(f.uploaded_at)} · ${kb(f.size)}${f.rev_auto ? " · rev. automática" : ""}</small>
            <span class="dw-la"><a href="/api/drawings/file/${f.id}" target="_blank" rel="noopener">abrir</a> · <a href="/api/drawings/file/${f.id}?download=1">baixar</a> · <a href="#" data-del="${f.id}" data-n="${esc(f.filename)}">excluir</a></span></div></div>`).join("")}</li>`).join("")}</ol></aside></div>`;
      const applyZoom = () => { const im = $("#dwimg"); if (im) { im.style.width = zoom === 1 ? "" : zoom * 100 + "%"; im.style.maxWidth = zoom === 1 ? "100%" : "none"; im.style.maxHeight = zoom === 1 ? "100%" : "none"; } const z = $("#dwz"); if (z) z.textContent = Math.round(zoom * 100) + "%"; };
      const bindImg = () => { const im = $("#dwimg"); if (im && im.dataset.pdf) im.onerror = () => { $("#dws").innerHTML = `<iframe src="${im.dataset.pdf}#view=FitH" title="PDF"></iframe>`; }; };
      const showCmp = () => {
        const opt = x => `<option value="${x.f.id}">${esc(x.h.label)}${x.h.current ? " (vigente)" : ""}</option>`;
        $("#dwp").innerHTML = `<div class="dw-cmp"><div class="dw-cbar"><label>Base <select id="ca">${revFiles.map(opt).join("")}</select></label><label>Sobre <select id="cb">${revFiles.map(opt).join("")}</select></label><label>Mistura <input type="range" id="cs" min="0" max="100" value="50"></label><label class="chk"><input type="checkbox" id="cd"> Só diferenças</label></div>
          <div class="dw-cstage" id="cst"><img id="ci1"><img id="ci2"></div></div>`;
        $("#ca").selectedIndex = Math.min(1, revFiles.length - 1); $("#cb").selectedIndex = 0;
        const up = () => { const a = revFiles.find(x => x.f.id == $("#ca").value).f, b = revFiles.find(x => x.f.id == $("#cb").value).f; $("#ci1").src = src(a); $("#ci2").src = src(b); $("#ci2").style.opacity = $("#cd").checked ? 1 : $("#cs").value / 100; $("#ci2").style.mixBlendMode = $("#cd").checked ? "difference" : "normal"; $("#cst").classList.toggle("diff", $("#cd").checked); };
        ["ca", "cb", "cs", "cd"].forEach(i => $("#" + i).oninput = up); up();
      };
      applyZoom(); bindImg();
      const go = c => { dlg.close(); dwOpen(c, done, kind); };
      $("#dw-prv").onclick = () => prevC && go(prevC); $("#dw-nxt").onclick = () => nextC && go(nextC);
      dlg.onkeydown = e => { if (e.key === "ArrowLeft" && prevC && !/INPUT|SELECT/.test(e.target.tagName)) go(prevC); if (e.key === "ArrowRight" && nextC && !/INPUT|SELECT/.test(e.target.tagName)) go(nextC); };
      dlg.addEventListener("close", () => { dlg.classList.remove("wide"); dlg.onkeydown = null; }, { once: true });
      dlg.onclick = async e => {
        if (e.target === dlg || e.target.closest("[data-close]")) return dlg.close();
        const z = e.target.closest("[data-z]");
        if (z) { const k = z.dataset.z; if (k === "+") zoom = Math.min(5, zoom + .25); else if (k === "-") zoom = Math.max(.25, zoom - .25); else if (k === "0") zoom = 1; else if (k === "full") { (document.fullscreenElement ? document.exitFullscreen() : $("#dwp").requestFullscreen()); return; } else if (k === "cmp") { return showCmp(); } applyZoom(); return; }
        const pv = e.target.closest("[data-pv]"); if (pv && !e.target.closest(".dw-dlb")) { cur = d.current.find(x => x.id == pv.dataset.pv); zoom = 1; $("#dwp").innerHTML = prev(cur); $("#dwopen").href = "/api/drawings/file/" + cur.id; $$(".dw-f", dlg).forEach(b => b.classList.toggle("on", b === pv)); applyZoom(); bindImg(); }
        const del = e.target.closest("[data-del]"); if (del) { e.preventDefault(); if (!confirm("Excluir definitivamente " + del.dataset.n + "?\nSe for a revisão vigente, a anterior volta a ser a vigente.")) return; await J("/api/drawings/file/" + del.dataset.del, { method: "DELETE" }); dlg.close(); done && done(); }
      };
      dlg.showModal();
    } catch (e) { alert(e.message); }
  }

  function dwOrphan(id, name, done) {
    dlg.innerHTML = `<div class="dh"><div><h2>Vincular desenho</h2><p>${esc(name)}</p></div><div><button class="btn ghost" data-close>Fechar</button></div></div>
      <p class="muted">O código não foi reconhecido pelo nome. Informe o(s) código(s) (separe por vírgula, se o desenho servir a mais de um) e a revisão.</p>
      <div class="fgrid"><label>Código(s)<input id="o-code" placeholder="ex.: AMD0170"></label><label>Revisão (opcional)<input id="o-rev" placeholder="ex.: 02 ou B"></label></div>
      <p id="o-msg" class="imp-msg"></p><div class="acts"><button class="btn" id="o-go">Vincular</button> <a class="btn ghost" href="/api/drawings/file/${id}" target="_blank" rel="noopener">Abrir arquivo</a> <button class="btn ghost" id="o-del">Excluir</button></div>`;
    $("#o-go").onclick = async () => { try { await post(`/api/drawings/file/${id}/assign`, { codes: $("#o-code").value, rev: $("#o-rev").value }); dlg.close(); done && done(); } catch (e) { $("#o-msg").textContent = e.message; $("#o-msg").className = "imp-msg err"; } };
    $("#o-del").onclick = async () => { if (!confirm("Excluir este arquivo?")) return; await J("/api/drawings/file/" + id, { method: "DELETE" }); dlg.close(); done && done(); };
    dlg.showModal();
  }

  async function genericView(id, pg) {   // dados de planilhas novas guardados como estão
    try {
      const d = await J(`/api/sources/${id}/rows?page=${pg}`), pages = Math.max(1, Math.ceil(d.total / d.size)); dlg.classList.add("wide");
      dlg.innerHTML = `<div class="dh"><div><h2>${esc(d.name)}</h2><p>${num(d.total)} linha(s) guardada(s) como vieram da planilha.</p></div><div><a class="btn ghost" href="/api/sources/${id}/export.xlsx">⬇ Excel</a> <button class="btn ghost" data-close>Fechar</button></div></div>`
        + T(d.columns.map(esc), d.rows.map(r => `<tr>${d.columns.map(c => `<td>${esc(r[c] ?? "")}</td>`).join("")}</tr>`))
        + (pages > 1 ? `<div class="pager"><button class="btn ghost" id="gv-p" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button class="btn ghost" id="gv-n" ${pg >= pages ? "disabled" : ""}>›</button></div>` : "");
      dlg.addEventListener("close", () => dlg.classList.remove("wide"), { once: true });
      const a = $("#gv-p"), b = $("#gv-n"); if (a) a.onclick = () => genericView(id, pg - 1); if (b) b.onclick = () => genericView(id, pg + 1);
      if (!dlg.open) dlg.showModal();
    } catch (e) { alert(e.message); }
  }

  // ---------- Brands: PERFECT · BPROAUTO · MOTRIO · MOTORCRAFT ----------
  async function brandsPage() {
    const BC = { PERFECT: "#d4372c", BPROAUTO: "#2f7de1", MOTRIO: "#f2c12e", MOTORCRAFT: "#7c8cff", OUTROS: "#7b8794" }, NAME = { PERFECT: "PERFECT", BPROAUTO: "BPROAUTO", MOTRIO: "MOTRIO", MOTORCRAFT: "MOTORCRAFT", OUTROS: "Sem marca" };
    try {
      const s = await J("/api/brands"); let cur = new URLSearchParams(location.search).get("b") || "PERFECT";
      const cards = [...s.brands]; if (s.unclassified) cards.push({ brand: "OUTROS", rule: "Não se encaixa em nenhuma regra", total: s.unclassified, catalog: 0, des: 0, rd: 0, base: 0, pend_compras: 0 });
      root.innerHTML = `<div class="notice">Itens agrupados pelo código: <b>AMD…</b> = PERFECT · <b>1BP…</b> = BPROAUTO · <b>somente números</b> = MOTRIO · itens da base <b>ItensMotorcraft</b> (PN Ford, e mesma família de código) = MOTORCRAFT. Reúne catálogo, desenvolvimento, redesenvolvimento e pedidos de amostra.</div>
        <div class="brand-grid" id="bg">${cards.map(b => `<button type="button" class="bcard ${b.brand === cur ? "on" : ""}" data-b="${b.brand}" style="--bc:${BC[b.brand]}"><h3>${NAME[b.brand]}</h3><div class="bn">${num(b.total)}</div><small>${esc(b.rule)}</small>
          <div class="bch">${b.catalog ? `<span>Catálogo ${num(b.catalog)}</span>` : ""}${b.des ? `<span>DES ${num(b.des)}</span>` : ""}${b.rd ? `<span>R-D ${num(b.rd)}</span>` : ""}${b.base ? `<span>Base ${num(b.base)}</span>` : ""}${b.pend_compras ? `<span>Pend. compras ${num(b.pend_compras)}</span>` : ""}</div></button>`).join("")}</div>
        <form class="toolbar" id="bf"><input name="q" placeholder="Buscar código, descrição ou veículo…" style="flex:1;min-width:240px">
        <select name="scope"><option value="">Onde está: todos</option><option value="catalog">No catálogo</option><option value="des">Em desenvolvimento (DES)</option><option value="rd">Em redesenvolvimento (R-D)</option><option value="base">Na base Motorcraft</option></select>
        <select name="flag"><option value="">Controle de status</option>${Object.entries(FLG).map(([k, v]) => `<option value="${k}">${v[0]}</option>`).join("")}</select><a class="btn" id="bdl" href="#">⬇ Baixar Excel</a></form>
        <div class="summary" id="bsum"></div><div id="bt"></div><div class="pager" id="bpg"></div>`;
      const f = $("#bf"); let pg = 1, tm;
      const load = async () => { try {
        const fv = Object.fromEntries(new FormData(f)); $("#bdl").href = "/api/export/brands.xlsx?" + qs({ ...fv, brand: cur === "OUTROS" ? "" : cur });
        const d = await J(`/api/brands/${cur}/items?` + qs({ ...fv, page: pg })), pages = Math.max(1, Math.ceil(d.total / d.size));
        $("#bsum").textContent = `${NAME[cur]} · ${num(d.total)} item(ns)`;
        $("#bt").innerHTML = d.rows.length ? T(["Código", "Código PERFECT", "Descrição", "Veículo / aplicação", "Onde está", "Controle de status", "Desenho", "Amostras"], d.rows.map(i => {
          const code = i.catalog && i.product_id ? lnk(i.product_id, i.code) : i.des ? `<a href="#" data-rd="des" data-code="${esc(i.code)}">${esc(i.code)}</a>` : i.rd ? `<a href="#" data-rd="rd" data-code="${esc(i.code)}">${esc(i.code)}</a>` : esc(i.code);
          return `<tr><td>${code}</td><td>${(i.perfect_codes || []).length ? i.perfect_codes.map(c => `<a class="pcode" href="/pesquisa?q=${encodeURIComponent(c)}">${esc(c)}</a>`).join(" ") : (i.brand === "PERFECT" ? '<span class="muted">é o próprio</span>' : '<span class="muted">sem relação</span>')}</td><td>${clip(i.description)}</td><td>${clip(i.vehicle)}</td><td>${[i.catalog && tag("Catálogo"), i.des && tag("DESENVOLVIMENTO"), i.rd && tag("REDESENVOLVIMENTO"), i.base && '<span class="tag">Base Motorcraft</span>'].filter(Boolean).join(" ")}</td><td class="fcell">${flagChips(i.flags)}</td>${dwCol(i.code)}<td>${i.samples ? `<a href="/amostras?q=${encodeURIComponent(i.code)}">${i.samples}</a>` : "–"}</td></tr>`; })) : empty("Nenhum item com esses filtros.");
        $("#bpg").innerHTML = pages > 1 ? `<button class="btn ghost" data-p="${pg - 1}" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button class="btn ghost" data-p="${pg + 1}" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
        dwFill($("#bt"));
      } catch (e) { fail(e); } };
      f.addEventListener("input", () => { clearTimeout(tm); tm = setTimeout(() => { pg = 1; load(); }, 300); }); f.addEventListener("submit", e => e.preventDefault());
      $("#bpg").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; load(); scrollTo(0, 0); } });
      $("#bg").addEventListener("click", e => { const b = e.target.closest("[data-b]"); if (!b) return; cur = b.dataset.b; pg = 1; $$(".bcard", root).forEach(x => x.classList.toggle("on", x === b)); load(); });
      load();
    } catch (e) { fail(e); }
  }

  // ---------- Lados: item, lado, par e traseiro da mesma aplicação ----------
  async function ladosPage() {
    const AXL = { dianteiro: "Dianteiro", traseiro: "Traseiro", cabine: "Cabine", ambos_eixos: "Diant./Tras." }, SDL = { direito: "LD", esquerdo: "LE", ambos: "LD/LE" };
    const sd = s => s ? `<span class="sd ${s}">${SDL[s]}</span>` : '<span class="muted">–</span>';
    let LV = {};
    const rch = x => { const tip = (LV[x.level] || x.level) + (x.app ? ` · ${x.app}` : "") + (x.status ? ` · status ${x.status}` : "") + (x.pair ? ` · par: ${x.pair.code}` : "");
      const body = `${esc(x.code)} <i>${SDL[x.side] || ""}</i>${x.level === "provavel" ? "?" : ""}${x.pair ? `<span class="rp">+ ${esc(x.pair.code)} ${SDL[x.pair.side] || ""}</span>` : ""}`;
      return x.id ? `<a href="#" data-ficha="${x.id}" class="rchip ${x.level}" title="${esc(tip)}">${body}</a>` : `<a href="/desenvolvimento?q=${encodeURIComponent(x.code)}" class="rchip ${x.level}" title="${esc(tip)}">${body} <i>DES</i></a>`; };
    const kit = i => (i.kit || []).length > 1 ? `<span class="kit">${i.kit.map((k, n) => `${n ? '<span class="plus">+</span>' : ""}<span class="k ${k.axle === "dianteiro" ? "f" : "t"}" title="${k.axle}${k.src ? " · " + esc(LV[k.src] || k.src) : ""}">${esc(k.code)} <i>${SDL[k.side] || ""}${k.qty === 2 ? " ×2" : ""}</i></span>`).join("")}</span>` : '<span class="muted">–</span>';
    root.innerHTML = `<div class="notice">Amortecedores <b>do catálogo (CatalogoAMD.xlsx)</b>. O <b>par LD × LE</b> vem da planilha <b>Lados - Amortecedores.xlsx</b> (ou, se ela não cobrir, dos Produtos Relacionados / aplicação). O <b>traseiro</b> (e, nos traseiros, o dianteiro) é interpretado automaticamente, nesta ordem:
      <span class="rchip relacionado">Produtos Relacionados</span> do catálogo · <span class="rchip exata">mesma aplicação</span> do catálogo · <span class="rchip servidor">mesma aplicação no servidor</span> (DES/R-D) · <span class="rchip desenvolvimento">em desenvolvimento</span> (ainda fora do catálogo) · <span class="rchip provavel">provável ?</span> (mesmo modelo-base, confira a versão). Cada traseiro mostra também o <b>par</b> dele, e a coluna <b>Conjunto</b> monta o jogo completo do veículo.</div>
      <div class="cards mini-cards" id="ls"></div>
      <form class="toolbar" id="lf"><input name="q" placeholder="Buscar código, descrição, veículo…" style="flex:1;min-width:240px">
        <select name="escopo"><option value="lados">Itens com lados (LD/LE) e da planilha Lados</option><option value="todos">Todos os dianteiros/traseiros do catálogo</option></select>
        <select name="axle"><option value="">Eixo: todos</option><option value="dianteiro">Dianteiro</option><option value="traseiro">Traseiro</option><option value="cabine">Cabine</option></select>
        <select name="side"><option value="">Lado: todos</option><option value="direito">Direito (LD)</option><option value="esquerdo">Esquerdo (LE)</option></select>
        <select name="other"><option value="">Traseiro/dianteiro pela aplicação: todos</option><option value="exata">Possuímos (relacionado / mesma aplicação)</option><option value="desenvolvimento">Em desenvolvimento (servidor)</option><option value="provavel">Provável (confira a versão)</option><option value="nao">NÃO possuímos</option><option value="sem_aplicacao">Sem aplicação cadastrada</option></select>
        <select name="rear"><option value="">Traseiro: todos</option><option value="com">Com traseiro encontrado</option><option value="sem">Dianteiro sem traseiro</option></select>
        <select name="pair"><option value="">Par: todos</option><option value="com">Com par do outro lado</option><option value="sem">LD/LE sem par</option></select>
        <select name="status"><option value="">Situação: todas</option><option value="ativo">Ativo</option><option value="em_breve">Em breve</option><option value="inativo">Inativo</option></select><a class="btn" id="lxl" href="#">⬇ Baixar Excel</a></form>
      <div class="summary" id="lsum"></div><div id="lt"></div><div class="pager" id="lpg"></div>`;
    const f = $("#lf"); let pg = 1, tm;
    const load = async () => { try {
      const fv = Object.fromEntries(new FormData(f)); $("#lxl").href = "/api/export/lados.xlsx?" + qs(fv);
      const d = await J("/api/sides?" + qs({ ...fv, page: pg })), s = d.stats, pages = Math.max(1, Math.ceil(d.total / d.size)); LV = d.levels || {};
      $("#ls").innerHTML = [[d.escopo === "todos" ? "Dianteiros + traseiros" : "Com lados (LD/LE)", s.total, ""], ["Dianteiros", s.dianteiro, "axle=dianteiro"], ["Traseiros", s.traseiro, "axle=traseiro"], ["Traseiro confirmado", s.traseiro_exato, "other=exata&axle=dianteiro"], ["Traseiro em desenvolvimento", s.traseiro_desenvolvimento, "other=desenvolvimento&axle=dianteiro"], ["Traseiro provável", s.traseiro_provavel, "other=provavel&axle=dianteiro"], ["SEM traseiro", s.traseiro_nao, "other=nao&axle=dianteiro"], ["Sem aplicação", s.sem_aplicacao, "other=sem_aplicacao"], ["Sem par do outro lado", s.sem_par, "pair=sem"]]
        .map(([l, v, a]) => `<button type="button" class="card stat" ${a ? `data-fs="${a}"` : ""}><span class="num sm">${num(v)}</span><small>${l}</small></button>`).join("");
      $("#lsum").textContent = num(d.total) + " item(ns)";
      $("#lt").innerHTML = d.rows.length ? T(["Código", "Descrição", "Eixo", "Lado", "Par (outro lado)", "Traseiro (mesma aplicação)", "Dianteiro (mesma aplicação)", "Possuímos?", "Conjunto do veículo", "Veículos"], d.rows.map(i => `<tr><td>${lnk(i.id, i.code)} ${window.psdCode ? psdCode(i.code, "↗") : ""}</td><td>${clip(i.description)}</td><td>${AXL[i.axle] || "–"}</td><td>${sd(i.side)}</td>
          <td>${i.pair ? `<a href="#" data-ficha="${i.pair.id}" class="rchip exata" title="${esc(i.pair_how || "")}">${esc(i.pair.code)} <i>${SDL[i.pair.side] || ""}</i></a>` : (i.side === "ambos" ? '<span class="muted" title="Um código atende os dois lados">mesmo código</span>' : '<span class="muted">–</span>')}</td>
          <td>${i.axle === "dianteiro" ? (i.rear.length ? i.rear.slice(0, 3).map(rch).join("") + (i.rear.length > 3 ? `<span class="xchip more" title="${esc(i.rear.slice(3).map(x => x.code).join(" · "))}">+${i.rear.length - 3}</span>` : "") : '<span class="muted">não encontrado</span>') : '<span class="muted">–</span>'}</td>
          <td>${i.axle === "traseiro" ? (i.front.length ? i.front.slice(0, 3).map(rch).join("") + (i.front.length > 3 ? `<span class="xchip more" title="${esc(i.front.slice(3).map(x => x.code).join(" · "))}">+${i.front.length - 3}</span>` : "") : '<span class="muted">não encontrado</span>') : '<span class="muted">–</span>'}</td>
          <td>${{ exata: '<span class="sd direito">Sim</span>', desenvolvimento: '<span class="sd ambos">Em DES</span>', provavel: '<span class="sd ambos">Provável</span>', nao: '<span class="sd esquerdo">NÃO</span>', sem_aplicacao: '<span class="muted">sem aplicação</span>' }[i.other_axle] || '<span class="muted">–</span>'}</td>
          <td>${kit(i)}</td>
          <td><span class="clip" title="${esc([...i.vehicles, ...(i.server_apps || []).map(a => "servidor: " + a)].join("\n"))}">${esc((i.vehicles.length ? i.vehicles : (i.server_apps || [])).slice(0, 2).join(" | "))}${i.vehicles.length > 2 ? ` <small class="muted">+${i.vehicles.length - 2}</small>` : ""}</span></td></tr>`)) : empty("Nenhum item com esses filtros.");
      $("#lpg").innerHTML = pages > 1 ? `<button class="btn ghost" data-p="${pg - 1}" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button class="btn ghost" data-p="${pg + 1}" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
    } catch (e) { fail(e); } };
    f.addEventListener("input", () => { clearTimeout(tm); tm = setTimeout(() => { pg = 1; load(); }, 300); }); f.addEventListener("submit", e => e.preventDefault());
    $("#lpg").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; load(); scrollTo(0, 0); } });
    $("#ls").addEventListener("click", e => { const b = e.target.closest("[data-fs]"); if (!b) return; [...f.elements].forEach(x => { if (x.name && x.name !== "q" && x.name !== "escopo") x.value = ""; }); new URLSearchParams(b.dataset.fs).forEach((v, k) => f.elements[k].value = v); pg = 1; load(); });
    const q0 = new URLSearchParams(location.search).get("q"); if (q0) f.elements.q.value = q0;
    load();
  }

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

  const NEW = window.PSD_NEW({ J, post, $, $$, esc, num, tag, T, clip, empty, fail, dlg, qs, dmy, root, FLG, FGROUPS });
  const PAGES = {
    produtos: () => listView({ endpoint: "/api/products", xlsx: "produtos", head: prodHead, row: prodRow,
      note: '<p class="muted">Ordenado pela posição do item no catálogo (ordem das linhas da planilha do catálogo importada). Clique no código para abrir a ficha completa.</p>',
      form: inp("q", "Buscar: código, OEM, fornecedor, descrição, veículo, ano…", 'autofocus style="flex:1;min-width:260px"') }),
    pesquisa: () => listView({ endpoint: "/api/products", xlsx: "pesquisa", head: prodHead, row: prodRow, init: initLists,
      note: '<p class="muted"><b>Digite o código PERFECT, OEM ou de um CONCORRENTE</b> (com ou sem ponto/hífen: 16.470 = 16470) — a linha mostra qual referência casou. Pesquisa no catálogo e nos itens em desenvolvimento (DES) e redesenvolvimento (R-D). Use “Origem” para escolher onde procurar.</p>',
      form: inp("q", "Busca livre (ex.: strada 2012 dianteiro)", 'style="flex:1;min-width:220px"') + sel("origem", "Origem: todas", [["catalogo", "Somente catálogo"], ["des", "Somente em desenvolvimento (DES)"], ["rd", "Somente redesenvolvimento (R-D)"]]) + inp("code", "Código") + sel("code_type", "Tipo de código", [["oem", "OEM"], ["fornecedor", "Fornecedor"], ["concorrente", "Concorrente (referência cruzada)"]]) +
        sel("make", "Montadora", []) + sel("model", "Modelo", []) + sel("year", "Ano", []) + sel("axle", "Eixo", AX) + sel("side", "Lado", SD) + sel("system", "Sistema", [["gas", "Gás"], ["oleo", "Óleo"]]),
      after: async p => { const o = p.origem || "", box = $("#xtra"); $("#out").hidden = $("#pg").hidden = (o === "des" || o === "rd");
        const want = o === "" ? ["des", "rd"] : o === "catalogo" ? [] : [o]; if (!want.length || (o === "" && !p.q && !p.make && !p.model && !p.year)) { box.innerHTML = ""; return; }
        const parts = await Promise.all(want.map(k => J(`/api/rd/${k}?` + qs({ q: p.q, make: p.make, model: p.model, year: p.year })).then(d => [k, d])));
        box.innerHTML = parts.map(([k, d]) => { const slug = k === "des" ? "desenvolvimento" : "redesenvolvimento", lab = k === "des" ? "DESENVOLVIMENTO" : "REDESENVOLVIMENTO";
          return `<h3>${tag(lab)} ${k === "des" ? "Em desenvolvimento" : "Em redesenvolvimento"} — ${d.total} item(ns) <a class="btn ghost sm" href="/${slug}?${qs({ q: p.q, make: p.make, model: p.model, year: p.year })}">Ver todos</a></h3>` +
            (d.rows.length ? T(["Código", "Descrição", "Veículo(s)", "Status", "Catálogo"], d.rows.slice(0, 12).map(r => `<tr><td><a href="#" data-rd="${k}" data-code="${esc(r.code)}">${esc(r.code)}</a></td><td>${clip(r.description)}</td><td>${clip(r.vehicles)}</td><td>${clip(r.statuses)}</td><td>${r.product_id ? lnk(r.product_id, "abrir ficha") : "–"}</td></tr>`)) : '<p class="muted">Nenhum item.</p>'); }).join(""); } }),
    aplicacoes: () => listView({ endpoint: "/api/applications", xlsx: "aplicacoes", init: initLists, head: ["Montadora", "Modelo", "Aplicação", "Anos", "Eixo", "Lado", "Produto", "Pos."],
      row: a => `<tr><td>${esc(a.make || "")}</td><td>${esc(a.model || "")}</td><td>${esc(a.application_text || "")}</td><td>${yr(a)}</td><td>${esc(a.axle || "")}</td><td>${esc(a.side || "")}</td><td>${lnk(a.product_id, a.perfect_code)}</td><td>${a.catalog_position ?? "–"}</td></tr>`,
      form: inp("q", "Buscar veículo, aplicação ou código", 'style="flex:1;min-width:220px"') + sel("make", "Montadora", []) + sel("model", "Modelo", []) + sel("year", "Ano", []) + sel("axle", "Eixo", AX) + sel("side", "Lado", SD) }),

    desenvolvimento: () => rdPage("des"),
    redesenvolvimento: () => rdPage("rd"),
    comparacao: async () => {
      let ids = (url.get("ids") || "").match(/\d+/g) || [];
      root.innerHTML = `<div class="toolbar"><input id="add" list="addl" placeholder="Adicionar produto: digite o código e escolha" style="flex:1;min-width:260px"><datalist id="addl"></datalist><a class="btn" id="dl" href="#">⬇ Baixar Excel</a></div><div id="out"></div>`;
      const add = $("#add"), dl = $("#addl"); let found = {};
      add.addEventListener("input", async () => { if (add.value.length < 2) return; const d = await J("/api/products?size=8&q=" + encodeURIComponent(add.value)); found = {}; d.rows.forEach(r => found[r.perfect_code] = r.id); dl.innerHTML = d.rows.map(r => `<option value="${esc(r.perfect_code)}">${esc(r.description || "")}</option>`).join(""); if (found[add.value.trim()]) { ids = [...new Set([...ids, String(found[add.value.trim()])])].slice(0, 4); add.value = ""; draw(); } });
      root.addEventListener("click", e => { const r = e.target.closest("[data-rm]"); if (r) { ids = ids.filter(i => i !== r.dataset.rm); draw(); } });
      const ROWS = [["Posição no catálogo", p => p.catalog_position], ["Descrição", p => p.description], ["Grupo", p => p.catalog_group], ["Família", p => p.family], ["Sistema", p => SYS[p.system_type]],
        ["Lmin (mm)", p => p.dimensions?.lmin_mm], ["Lmax (mm)", p => p.dimensions?.lmax_mm], ["Curso (mm)", p => p.dimensions?.stroke_mm], ["Ø haste (mm)", p => p.dimensions?.rod_diameter_mm], ["Corpo (mm)", p => p.dimensions?.body_length_mm], ["Ø tubo (mm)", p => p.dimensions?.tube_diameter_mm],
        ["Fixação superior", p => p.dimensions?.upper_mount], ["Fixação inferior", p => p.dimensions?.lower_mount], ["Peso (kg)", p => p.weight_kg], ["EAN", p => p.ean], ["Caixa", p => [p.package_code, p.box?.raw_dims].filter(Boolean).join(" · ")],
        ["Códigos OEM", p => p.codes.filter(c => c.code_type === "oem").map(c => c.code).join(", ")], ["Códigos de fornecedor", p => [...new Set(p.codes.filter(c => c.code_type === "fornecedor").map(c => c.code))].join(", ")],
        ["Aplicações", p => p.applications.length ? p.applications.length + ": " + p.applications.slice(0, 4).map(a => [a.make, a.model, yr(a)].filter(Boolean).join(" ")).join("; ") : ""],
        ["Nº Inmetro", p => [...new Set(p.certificates.map(c => c.inmetro_number).filter(Boolean))].join(", ")],
        ["Fontes", p => [...new Set([...p.codes, ...p.applications].map(x => x.source).filter(Boolean))].join("; ")]];
      async function draw() {
        history.replaceState(null, "", "?ids=" + ids.join(",")); $("#dl").href = "/api/export/comparacao.xlsx?ids=" + ids.join(",");
        if (!ids.length) return $("#out").innerHTML = empty("Escolha de 2 a 4 produtos para comparar lado a lado.");
        const ps = await J("/api/compare?ids=" + ids.join(","));
        const diffs = [], trs = ROWS.map(([l, fn]) => { const v = ps.map(p => String(fn(p) ?? "")); const dif = ps.length > 1 && new Set(v).size > 1; if (dif) diffs.push(l); return `<tr class="${dif ? "diff" : ""}"><th>${l}</th>${v.map(x => `<td>${esc(x) || "—"}</td>`).join("")}</tr>`; });
        $("#out").innerHTML = (ps.length > 1 ? `<div class="notice">${diffs.length ? "<b>Diferenças identificadas:</b> " + diffs.join(", ") : "Nenhuma diferença nos campos comparados."} Linhas destacadas diferem; “—” = sem dado. Dimensões parecidas não bastam para afirmar intercambialidade.</div>` : "") +
          `<div class="tbl"><table><tr><th></th>${ps.map(p => `<th>${lnk(p.id, p.perfect_code)} <button class="btn ghost" data-rm="${p.id}">×</button></th>`).join("")}</tr>${trs.join("")}</table></div>`;
      }
      draw();
    },

    equivalencias: () => {
      const DF = ["Nenhuma aplicação em comum", "Eixo diferente", "Lados diferentes", "São lados opostos", "Lmax difere", "Lmin difere", "Sistema diferente", "Família diferente"];
      const MS = ["Eixo", "Lado", "Lmax", "Lmin", "Sistema óleo/gás", "Aplicações", "Diâmetro da haste"];
      const grp = (n, t, h, L) => `<div class="ms" data-ms><button type="button" class="btn ghost msb">${t} <b class="msn"></b> ▾</button><div class="msp" hidden><small class="muted">${h}</small>${L.map(c => `<label><input type="checkbox" name="${n}" value="${c}"> ${c} <small data-fc="${n}:${c}"></small></label>`).join("")}</div></div>`;
      const CR = ["Código em comum", "Aplicação em comum", "Mesmo eixo", "Mesmo lado", "Lmax igual", "Lmin igual", "Mesmo sistema", "Mesma família"];
      root.innerHTML = `<div class="notice">A pontuação (0–100%) mede a <b>similaridade dos dados</b> (códigos, aplicação, medidas, sistema). <b>Não comprova intercambialidade</b> e nenhuma sugestão é aprovada automaticamente.</div>
      <form class="eqform"><div class="toolbar">${inp("q", "Código PERFECT")}${sel("status", "Todos os status", [["pendente", "Pendente"], ["aprovada", "Aprovada"], ["rejeitada", "Rejeitada"]])}${sel("confidence", "Confiança", [["Alta", "Alta"], ["Média", "Média"], ["Baixa", "Baixa"]])}${sel("diff", "Diferenças", [["sem", "Sem diferenças"], ["com", "Com diferenças"]])}
        <input name="minscore" type="number" min="0" max="100" placeholder="Pontuação mín. (%)" style="width:150px"><button type="button" class="btn ghost" id="clr">Limpar filtros</button></div>
        <div class="toolbar">${grp("crit", "Critérios atendidos", "todos os marcados precisam ser atendidos", CR)}${grp("dif", "Diferenças", "exigir que apareça", DF)}${grp("miss", "Dados ausentes", "exigir que apareça", MS)}</div></form>
      <div class="toolbar"><span class="summary" id="sum"></span><span style="flex:1"></span><button type="button" class="btn ghost" id="gen">Gerar / atualizar sugestões</button><a class="btn" id="dl" href="#">⬇ Baixar planilha (XLSX)</a></div><div id="out"></div><div class="pager" id="pg"></div>`;
      const f = $("form", root); let pg = 1, t;
      url.forEach((v, k) => { const i = f.elements[k]; if (i && i.type !== "checkbox") i.value = v; });
      const updMs = () => $$("[data-ms]", root).forEach(m => { const n = $$("input:checked", m).length; $(".msn", m).textContent = n ? "(" + n + ")" : ""; });
      root.addEventListener("click", e => { const b = e.target.closest(".msb"); $$(".msp", root).forEach(p => { if (!b || p !== b.nextElementSibling) p.hidden = true; }); if (b) b.nextElementSibling.hidden = !b.nextElementSibling.hidden; });
      document.addEventListener("click", e => { if (!e.target.closest("[data-ms]")) $$(".msp", root).forEach(p => p.hidden = true); });
      f.addEventListener("change", updMs);
      const params = () => new URLSearchParams([...new FormData(f)].filter(([, v]) => v !== "")).toString();
      const chips = (a, c) => a.map(x => `<span class="chip ${c}">${esc(x)}</span>`).join("");
      const load = async () => { try {
        $("#dl").href = "/api/equivalences/export.xlsx?" + params();
        const d = await J("/api/equivalences?" + params() + "&page=" + pg);
        const sc = d.status_counts || {}; $("#sum").textContent = `${d.total} sugestão(ões) · Pendente ${sc.pendente || 0} · Aprovada ${sc.aprovada || 0} · Rejeitada ${sc.rejeitada || 0}`;
        $$("[data-fc]").forEach(s => s.textContent = "(" + (d.facets?.[s.dataset.fc] ?? 0) + ")");
        $("#out").innerHTML = d.rows.length ? d.rows.map(e => `<div class="eq"><div class="eqh"><b>${lnk(e.product_a, e.a_code)} × ${lnk(e.product_b, e.b_code)}</b><span class="badge ${e.confidence === "Alta" ? "ok" : e.confidence === "Média" ? "warn" : "bad"}">${e.confidence}</span><span class="status ${e.status}">${e.status}</span><a href="/comparacao?ids=${e.product_a},${e.product_b}">Comparar</a></div>
          <div class="bar"><i style="width:${e.score}%"></i><span>${e.score}% de similaridade</span></div><p class="muted">${esc(e.a_desc || "")} · ${esc(e.b_desc || "")}</p>
          <div>${chips(e.criteria, "ok")}${chips(e.differences, "bad")}${chips(e.missing, "warn")}</div><p class="muted">Fontes: ${esc(e.sources || "")}</p>
          <div class="acts">${["pendente", "aprovada", "rejeitada"].map(s => `<button class="btn ghost ${e.status === s ? "on" : ""}" data-eq="${e.id}" data-s="${s}">${{ pendente: "Pendente", aprovada: "Aprovar", rejeitada: "Rejeitar" }[s]}</button>`).join("")}</div></div>`).join("") : empty("Nenhuma sugestão com esses filtros. Ajuste os filtros ou clique em “Gerar / atualizar sugestões”.");
        const pages = Math.ceil(d.total / d.size); $("#pg").innerHTML = pages > 1 ? `<button class="btn ghost" data-p="${pg - 1}" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button class="btn ghost" data-p="${pg + 1}" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
      } catch (e) { fail(e); } };
      f.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => { pg = 1; load(); }, 250); });
      $("#clr").onclick = () => { f.reset(); updMs(); pg = 1; load(); };
      $("#gen").onclick = async () => { $("#gen").textContent = "Calculando…"; try { const r = await post("/api/equivalences/generate"); alert(`${r.candidates} pares analisados; ${r.saved} sugestões (≥50%). Os status já definidos foram preservados.`); } catch (e) { fail(e); } $("#gen").textContent = "Gerar / atualizar sugestões"; pg = 1; load(); };
      root.addEventListener("click", async e => { const b = e.target.closest("[data-eq]"), p = e.target.closest("[data-p]"); if (b) { await post("/api/equivalences/" + b.dataset.eq, { status: b.dataset.s }); load(); } else if (p && !p.disabled) { pg = +p.dataset.p; load(); scrollTo(0, 0); } });
      load();
    },

    pendencias: () => {
      const tab = url.get("tab") === "dup" ? "dup" : "pend";
      root.innerHTML = `<div class="toolbar"><span style="flex:1"></span><a class="btn" id="dl" href="/api/export/pendencias.xlsx">⬇ Baixar Excel</a></div><div class="tabs"><a href="/pendencias" class="${tab === "pend" ? "on" : ""}">Pendências e conflitos</a><a href="/pendencias?tab=dup" class="${tab === "dup" ? "on" : ""}">Possíveis duplicidades</a></div><div id="tb"></div>`;
      const host = $("#tb");
      if (tab === "dup") return J("/api/duplicates").then(r => host.innerHTML = '<p class="muted">Mesmo código associado a mais de um produto. Nada é unido ou excluído automaticamente.</p>' + (r.length ? T(["Tipo", "Código", "Produtos", "Qtd"], r.map(x => `<tr><td>${esc(x.code_type)}</td><td><a href="/pesquisa?code=${encodeURIComponent(x.code)}">${esc(x.code)}</a></td><td>${esc(x.products)}</td><td>${x.n}</td></tr>`)) : empty("Nenhuma duplicidade."))).catch(fail);
      listInto(host);
      function listInto(h) {
        h.innerHTML = `<form class="toolbar">${inp("q", "Código ou texto")}<select name="status"><option value="aberta" selected>Abertas</option><option value="resolvida">Resolvidas</option><option value="ignorada">Ignoradas</option><option value="">Todas</option></select><select name="kind"><option value="">Todos os tipos</option></select></form><div class="summary" id="sum"></div><div id="out"></div><div class="pager" id="pg"></div>`;
        const f = $("form", h); let pg = 1, t, kinds = false;
        const load = async () => { try {
          $("#dl").href = "/api/export/pendencias.xlsx?" + qs(Object.fromEntries(new FormData(f)));
          const d = await J("/api/pendencies?" + qs({ ...Object.fromEntries(new FormData(f)), page: pg }));
          if (!kinds) { kinds = true; $("[name=kind]", f).innerHTML += d.kinds.map(k => `<option>${esc(k)}</option>`).join(""); }
          const L = { campo_ausente: "Campo ausente", conflito: "Conflito entre fontes" };
          $("#sum").textContent = d.total + " registro(s)";
          $("#out").innerHTML = d.rows.length ? T(["Produto", "Tipo", "Campo", "Descrição", "Status", ""], d.rows.map(x => `<tr><td>${x.product_id ? lnk(x.product_id, x.perfect_code) : "–"}</td><td>${esc(L[x.kind] || x.kind)}</td><td>${esc(x.field || "")}</td><td>${esc(x.description || "")}</td><td>${x.status}</td><td>${x.status === "aberta" ? `<button class="btn ghost" data-pd="${x.id}" data-s="resolvida">Resolver</button> <button class="btn ghost" data-pd="${x.id}" data-s="ignorada">Ignorar</button>` : `<button class="btn ghost" data-pd="${x.id}" data-s="aberta">Reabrir</button>`}</td></tr>`)) : empty("Nenhuma pendência com esses filtros.");
          const pages = Math.ceil(d.total / d.size); $("#pg").innerHTML = pages > 1 ? `<button class="btn ghost" data-p="${pg - 1}" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button class="btn ghost" data-p="${pg + 1}" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
        } catch (e) { fail(e); } };
        f.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => { pg = 1; load(); }, 300); });
        h.addEventListener("click", async e => { const b = e.target.closest("[data-pd]"), p = e.target.closest("[data-p]"); if (b) { await post("/api/pendencies/" + b.dataset.pd, { status: b.dataset.s }); load(); } else if (p && !p.disabled) { pg = +p.dataset.p; load(); } });
        load();
      }
    },

    fontes: async () => {
      try {
        const d = await J("/api/history");
        root.innerHTML = `<div class="toolbar"><span style="flex:1"></span><a class="btn" href="/api/export/fontes.xlsx">⬇ Baixar Excel</a></div><h3>Histórico de importações</h3>` + (d.batches.length ? T(["#", "Data", "Arquivo", "Planilha", "Categoria", "Linhas lidas", "Novos", "Prod. complementados", "Conflitos", "Erros", "Status"], d.batches.map(b => `<tr><td>${b.id}</td><td>${esc(b.imported_at)}</td><td>${esc(b.filename || "")}</td><td>${esc(b.sheet || "")}</td><td>${esc(b.category || "")}</td><td>${b.rows_read ?? "–"}</td><td>${b.rows_new}</td><td>${b.rows_updated}</td><td>${b.rows_conflict}</td><td>${b.rows_error}</td><td>${esc(b.status)}</td></tr>`)) : empty("Nenhuma importação ainda. Use “Importação de Excel”."))
          + `<h3>Fontes e prioridade</h3><p class="muted">Prioridade de 1 (maior) a 9. Usada para sinalizar qual fonte prevalece na análise manual de conflitos.</p>` + T(["Fonte", "Categoria", "Importações", "Dados", "Prioridade"], d.sources.map(s => `<tr><td>${esc(s.name)}</td><td>${esc(s.category || "")}</td><td>${s.imports}</td><td>${s.generic_rows ? `<button class="btn ghost sm" data-gv="${s.id}">Ver ${num(s.generic_rows)} linhas</button> <a class="btn ghost sm" href="/api/sources/${s.id}/export.xlsx">⬇ Excel</a>` : "–"}</td><td><select data-src="${s.id}">${[1, 2, 3, 4, 5, 6, 7, 8, 9].map(n => `<option ${n === s.priority ? "selected" : ""}>${n}</option>`).join("")}</select></td></tr>`));
        root.addEventListener("click", async e => { const g = e.target.closest("[data-gv]"); if (g) genericView(+g.dataset.gv, 1); });
        root.addEventListener("change", e => { const s = e.target.closest("[data-src]"); if (s) post("/api/sources/" + s.dataset.src, { priority: +s.value }).catch(fail); });
      } catch (e) { fail(e); }
    },

    configuracoes: async () => {
      let me; try { me = await J("/api/auth/me"); } catch (e) { return fail(e); }
      const user = me.user, admin = !!me.admin, ICO = {
        perfil: "M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z", seg: "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6zM9 12l2 2 4-4", tema: "M12 3a9 9 0 109 9 7 7 0 01-9-9z",
        users: "M17 21v-2a4 4 0 00-4-4H7a4 4 0 00-4 4v2M10 11a4 4 0 100-8 4 4 0 000 8zM21 21v-2a4 4 0 00-3-3.9M16 3.1a4 4 0 010 7.8", regras: "M4 6h16M4 12h10M4 18h6M18 14l2 2 3-4", srv: "M4 5h16v5H4zM4 14h16v5H4zM8 7.5h.01M8 16.5h.01", bk: "M4 7c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3zM4 7v10c0 1.7 3.6 3 8 3s8-1.3 8-3V7M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" };
      const SECT = [["perfil", "Meu perfil", ICO.perfil], ["seguranca", "Senha e acesso", ICO.seg], ["aparencia", "Aparência", ICO.tema]];
      const ADM = [["usuarios", "Usuários", ICO.users], ["regras", "Regras de negócio", ICO.regras], ["servidor", "Servidor e sincronização", ICO.srv], ["backups", "Backups", ICO.bk]];
      let cur = (location.hash || "#perfil").slice(1); if (![...SECT, ...ADM].some(x => x[0] === cur) || (!admin && ADM.some(x => x[0] === cur))) cur = "perfil";
      const put = (u, b) => J(u, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) });
      const nav = b => `<button type="button" data-s="${b[0]}" class="${b[0] === cur ? "on" : ""}"><svg viewBox="0 0 24 24"><path d="${b[2]}"/></svg>${b[1]}</button>`;
      root.innerHTML = `<div class="set-wrap"><nav class="set-nav" id="snav">${SECT.map(nav).join("")}${admin ? `<hr><small>Administração</small>${ADM.map(nav).join("")}` : ""}</nav><div class="set-pane" id="spane"></div></div>`;
      const msg = (id, t, err) => { const m = $("#" + id); if (m) { m.textContent = t; m.className = "fmsg" + (err ? " err" : ""); } };
      const initial = u => esc((u.username || "?").slice(0, 1).toUpperCase());
      const avatar = (u, big) => u.avatar ? `<img src="/avatar/${u.id}?t=${Date.now()}" alt="Foto de ${esc(u.username)}">` : initial(u);
      const noAuth = '<div class="lockbox"><b>Login desligado neste computador</b><p>O sistema está com <code>PSD_AUTH=off</code> (modo de desenvolvimento), por isso não há usuário para editar. Remova essa linha do arquivo <code>.env</code> e reinicie para usar contas.</p></div>';
      const PANES = {
        perfil: () => !user ? noAuth : `<section class="fcard"><div class="profile-head"><div class="avatar-lg" id="av">${avatar(user)}</div><div><h3>${esc(user.username)} <span class="rolechip ${user.role}">${user.role === "admin" ? "Administrador" : "Usuário"}</span></h3><div class="meta">Conta criada em ${dmy(user.created_at)} · último acesso ${user.last_login ? dmy(user.last_login) + " " + String(user.last_login).slice(11, 16) : "—"}</div>
            <div class="frow-act"><label class="btn ghost sm" style="cursor:pointer">Escolher foto<input type="file" id="avf" accept="image/png,image/jpeg,image/webp,image/gif" hidden></label>${user.avatar ? '<button type="button" class="btn ghost sm" id="avd">Remover foto</button>' : ""}<span id="avm" class="fmsg"></span></div></div></div></section>
          <section class="fcard"><h3>Nome de usuário</h3><p class="sub2">É o nome usado para entrar. Por segurança, confirme com a senha atual.</p><form class="fform" id="fu"><label>Novo usuário<input name="username" value="${esc(user.username)}" minlength="3" required autocomplete="username"></label><label>Senha atual<input name="password" type="password" required autocomplete="current-password"></label>
            <div class="frow-act full"><button class="btn" type="submit">Salvar usuário</button><span id="fum" class="fmsg"></span></div></form></section>`,
        seguranca: () => !user ? noAuth : `<section class="fcard"><h3>Alterar senha</h3><p class="sub2">Use ao menos 8 caracteres. A senha é guardada com hash — nem o administrador consegue lê-la.</p><form class="fform" id="fp"><label class="full">Senha atual<input name="old" type="password" required autocomplete="current-password"></label><label>Nova senha<input name="new" type="password" minlength="8" required autocomplete="new-password"></label><label>Repita a nova senha<input name="new2" type="password" minlength="8" required autocomplete="new-password"></label>
            <div class="frow-act full"><button class="btn" type="submit">Alterar senha</button><span id="fpm" class="fmsg"></span></div></form></section>
          <section class="fcard"><h3>Sessão</h3><p class="sub2">A sessão expira sozinha após 12 horas.</p><a class="btn ghost" href="/logout">Sair deste computador</a></section>`,
        aparencia: () => `<section class="fcard"><h3>Aparência</h3><p class="sub2">Escolha o modo de cor. Fica gravado neste navegador.</p><div class="seg" id="thm"><button type="button" data-t="light">Claro</button><button type="button" data-t="dark">Escuro</button></div></section>`,
        usuarios: async () => { const d = await J("/api/admin/users");
          return `<section class="fcard"><h3>Usuários</h3><p class="sub2">Administradores podem alterar metas, regras, backups e usuários. Sempre existe ao menos um administrador.</p>${T(["Usuário", "Perfil", "Último acesso", ""], d.users.map(u => `<tr><td><b>${esc(u.username)}</b>${u.id === d.me ? ' <span class="badge">você</span>' : ""}</td><td><select data-role="${u.id}"><option value="admin" ${u.role === "admin" ? "selected" : ""}>Administrador</option><option value="user" ${u.role === "user" ? "selected" : ""}>Usuário</option></select></td><td>${u.last_login ? dmy(u.last_login) : "—"}</td><td style="white-space:nowrap"><button class="btn ghost sm" data-rp="${u.id}" data-n="${esc(u.username)}">Redefinir senha</button> ${u.id === d.me ? "" : `<button class="btn ghost sm" data-du="${u.id}" data-n="${esc(u.username)}">Remover</button>`}</td></tr>`))}<span id="um" class="fmsg"></span></section>
            <section class="fcard"><h3>Novo usuário</h3><form class="fform" id="fn"><label>Usuário<input name="username" required minlength="3"></label><label>Senha inicial<input name="password" type="password" required minlength="8" autocomplete="new-password"></label><label>Perfil<select name="role"><option value="user">Usuário</option><option value="admin">Administrador</option></select></label><div class="frow-act full"><button class="btn" type="submit">Criar usuário</button><span id="fnm" class="fmsg"></span></div></form></section>`; },
        regras: async () => { const d = await J("/api/settings");
          return `<section class="fcard"><h3>Regras de negócio</h3><p class="sub2">Valem para listas, contadores, metas e sugestões de compra.</p><form class="fform" id="fr"><label>Somente itens cuja descrição contém<input name="only_description" value="${esc(d.only_description)}" placeholder="vazio = todos os itens"><small class="hint">Padrão: ${esc(d.defaults.only_description)}. Sem acento nem diferença de maiúsculas.</small></label>
            <label>Usuário validador (USER_VALID)<input name="goal_valid_user" value="${esc(d.goal_valid_user)}" required><small class="hint">Padrão: ${esc(d.defaults.goal_valid_user)} — conta só item com USER_VALID estritamente igual a este (sem diferença de maiúsculas ou espaços).</small></label>
            <label>Como as metas contam<select name="goal_basis"><option value="validacao" ${d.goal_basis === "validacao" ? "selected" : ""}>Validações do usuário (SUGESTÃO DES / R-D no ano da aprovação)</option><option value="recebido" ${d.goal_basis === "recebido" ? "selected" : ""}>Itens que chegaram a ITEM RECEBIDO no ano</option></select><small class="hint">Padrão: validações.</small></label>
            <label>Meta de lead time — amortecedores (dias)<input type="number" name="leadtime_meta_dias" min="30" max="720" value="${esc(d.leadtime_meta_dias ?? 180)}" required><small class="hint">Padrão: 180 dias (6 meses). Usada na análise de prazos em Pedidos em Aberto.</small></label>
            <div class="frow-act full"><button class="btn" type="submit">Salvar regras</button><a class="btn ghost" href="/metas">Editar metas do ano</a><span id="frm" class="fmsg"></span></div></form></section>
            <section class="fcard"><h3>Como as metas contam</h3><ul style="margin:0;padding-left:18px;line-height:1.7"><li><b>Validações</b> (padrão): itens com USER_VALID = usuário validador e LINHA «Amortecedor», separados pela SUGESTÃO (<b>DES</b> = DESENVOLVIMENTO, <b>R-D</b> = REDESENVOLVIMENTO), no ano da DATA_APROVACAO.</li><li><b>DESENVOLVIMENTO</b> (sempre): status chegou a <b>ITEM RECEBIDO</b> no ano <u>e</u> tem a validação do usuário. <b>Itens recebidos</b> (opção): REDESENVOLVIMENTO = foi de <b>PENDENTE CONFIRMAÇÃO</b> a <b>ITEM RECEBIDO</b> no ano <u>e</u> tem a validação do usuário.</li><li>Cada código conta uma vez por ano.</li></ul></section>`; },
        servidor: () => '<div id="srvpanel"></div>',
        backups: async () => { const d = await J("/api/backups");
          return `<section class="fcard"><h3>Backups</h3><p class="sub2">Banco local: <code>${esc(d.db)}</code> · ${(d.size / 1048576).toFixed(2)} MB. Antes de cada importação confirmada e de cada restauração o sistema cria um backup automático.</p>
            <div class="frow-act"><button class="btn" id="bk">Criar backup agora</button><a class="btn ghost" href="/api/export/configuracoes.xlsx">⬇ Excel (lista)</a></div></section>
            <section class="fcard">${d.backups.length ? T(["Arquivo", "Data", "Tamanho", ""], d.backups.map(b => `<tr><td>${esc(b.name)}</td><td>${b.date}</td><td>${(b.size / 1048576).toFixed(2)} MB</td><td><a class="btn ghost sm" href="/api/backups/${encodeURIComponent(b.name)}">Baixar</a> <button class="btn ghost sm" data-rs="${esc(b.name)}">Restaurar</button></td></tr>`)) : empty("Nenhum backup ainda.")}</section>`; }
      };
      const wire = {
        perfil() {
          const f = $("#avf"); if (f) f.onchange = async () => { if (!f.files[0]) return; const fd = new FormData(); fd.append("file", f.files[0]); msg("avm", "Enviando…"); try { await J("/api/auth/avatar", { method: "POST", body: fd }); location.reload(); } catch (e) { msg("avm", e.message, true); } };
          const d = $("#avd"); if (d) d.onclick = async () => { try { await J("/api/auth/avatar", { method: "DELETE" }); location.reload(); } catch (e) { msg("avm", e.message, true); } };
          const fu = $("#fu"); if (fu) fu.onsubmit = async e => { e.preventDefault(); const v = Object.fromEntries(new FormData(fu)); try { await post("/api/auth/username", v); msg("fum", "Usuário alterado."); setTimeout(() => location.reload(), 600); } catch (er) { msg("fum", er.message, true); } };
        },
        seguranca() {
          const fp = $("#fp"); if (fp) fp.onsubmit = async e => { e.preventDefault(); const v = Object.fromEntries(new FormData(fp)); if (v.new !== v.new2) return msg("fpm", "As senhas novas não conferem.", true);
            try { await post("/api/auth/password", { old: v.old, new: v.new }); fp.reset(); msg("fpm", "Senha alterada."); } catch (er) { msg("fpm", er.message, true); } };
        },
        aparencia() { const mark = () => $$("#thm button").forEach(b => b.classList.toggle("on", b.dataset.t === psdTheme.get())); mark(); $("#thm").onclick = e => { const b = e.target.closest("[data-t]"); if (b) { psdTheme.set(b.dataset.t); mark(); } }; },
        usuarios() {
          const pane = $("#spane");
          pane.onchange = async e => { const r = e.target.closest("[data-role]"); if (r) try { await put("/api/admin/users/" + r.dataset.role, { role: r.value }); msg("um", "Perfil atualizado."); } catch (er) { msg("um", er.message, true); show(); } };
          pane.onclick = async e => { const rp = e.target.closest("[data-rp]"), du = e.target.closest("[data-du]");
            if (rp) { const pw = prompt(`Nova senha para ${rp.dataset.n} (mínimo 8 caracteres):`); if (pw) try { await put("/api/admin/users/" + rp.dataset.rp, { password: pw }); msg("um", "Senha redefinida."); } catch (er) { msg("um", er.message, true); } }
            if (du && confirm(`Remover o usuário ${du.dataset.n}?`)) try { await J("/api/admin/users/" + du.dataset.du, { method: "DELETE" }); show(); } catch (er) { msg("um", er.message, true); } };
          const fn = $("#fn"); fn.onsubmit = async e => { e.preventDefault(); try { await post("/api/admin/users", Object.fromEntries(new FormData(fn))); show(); } catch (er) { msg("fnm", er.message, true); } };
        },
        regras() { const fr = $("#fr"); fr.onsubmit = async e => { e.preventDefault(); try { await put("/api/settings", Object.fromEntries(new FormData(fr))); msg("frm", "Regras salvas. Listas, contadores e metas já usam o novo critério."); } catch (er) { msg("frm", er.message, true); } }; },
        servidor() { NEW.serverPanel($("#srvpanel")); },
        backups() {
          $("#bk").onclick = async () => { await post("/api/backups"); show(); };
          $$("[data-rs]").forEach(b => b.onclick = async () => { if (!confirm("Restaurar " + b.dataset.rs + "?\nO banco atual será substituído (um backup do estado atual é criado antes).")) return; try { const r = await post("/api/backups/restore", { name: b.dataset.rs }); alert("Restaurado. Backup do estado anterior: " + r.safety); show(); } catch (e) { alert(e.message); } });
        }
      };
      const show = async () => { const pane = $("#spane"); pane.onclick = pane.onchange = null; try { pane.innerHTML = await PANES[cur](); wire[cur](); } catch (e) { pane.innerHTML = `<div class="notice err">${esc(e.message)}</div>`; } };
      $("#snav").onclick = e => { const b = e.target.closest("[data-s]"); if (!b) return; cur = b.dataset.s; history.replaceState(null, "", "#" + cur); $$("#snav button").forEach(x => x.classList.toggle("on", x === b)); show(); };
      show();
    },

    damping: async () => {
      let R; try { R = await J("/api/damping/rules"); } catch (e) { return fail(e); }
      const names = Object.keys(R.tables); let cur = null;
      const num = v => { v = String(v ?? "").trim().replace(",", "."); return v === "" || isNaN(v) ? null : +v; };
      const calc = (d, tol, f) => { if (d == null) return [null, null, ""]; let lo = d * (1 - tol), hi = d * (1 + tol); if (d < R.threshold) { lo += R.offset; hi -= R.offset; } if (lo > hi) return [lo, hi, "FAIXA INVÁLIDA"]; if (f == null) return [lo, hi, "INCOMPLETO"]; return [lo, hi, lo <= f && f <= hi ? "APPROVED" : "DISAPPROVED"]; };
      const cls = r => r === "APPROVED" ? "ok" : r === "DISAPPROVED" ? "bad" : "warn", fx = v => v == null ? "–" : v.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
      root.innerHTML = R.tables && names.length ? `<div class="notice"><b>Regra:</b> ${esc(R.source || "")} — se DRAWING &lt; ${R.threshold} N: mín = D×(1−tol)+${R.offset} e máx = D×(1+tol)−${R.offset}; senão sem ajuste. Aprovado se mín ≤ FOUND ≤ máx.<br><small>${esc(R.note)}</small></div>
        <div class="toolbar"><label class="muted">Atualizar regra a partir de planilha: <input type="file" id="rf" accept=".xlsx"></label></div>
        <h3>Ensaio <span id="ov"></span></h3>
        <form id="df" class="fgrid"><label>Código PERFECT<input name="perfect_code" list="dpl" autocomplete="off"></label><datalist id="dpl"></datalist><label>Identificação / lote<input name="label"></label><label>Data<input type="date" name="test_date"></label><label>Observações<input name="notes"></label></form>
        ${names.map(n => `<h4>Tabela ${n}</h4>` + T(["PERFECT STANDARD", "VM/S", "DRAWING (N)", n + " (N) mín", n + " (N) máx", "FOUND (N)", "RESULT"], R.tables[n].map(r => `<tr data-t="${n}" data-v="${r.velocity}" data-tol="${r.tolerance}"><td>${Math.round(r.tolerance * 100)}%</td><td>${r.velocity}</td><td><input class="dd" inputmode="decimal" size="8"></td><td class="mn">–</td><td class="mx">–</td><td><input class="df" inputmode="decimal" size="8"></td><td class="rs"></td></tr>`))).join("")}
        <div class="acts"><button class="btn" id="sv">Salvar ensaio</button><button class="btn ghost" id="nw">Novo ensaio</button><a class="btn ghost" id="dx" href="#" hidden>⬇ Baixar este ensaio (Excel)</a></div>
        <h3>Ensaios salvos</h3><div class="toolbar"><input id="dq" placeholder="Buscar código ou identificação"><span style="flex:1"></span><a class="btn" id="dall" href="/api/export/damping.xlsx">⬇ Baixar todos (Excel)</a></div><div id="dl2"></div>` : empty("Regra não carregada. Selecione a planilha DAMPING FORCE - REGRA.xlsx em “Atualizar regra”.") + `<input type="file" id="rf" accept=".xlsx">`;
      $("#rf").onchange = async e => { const fd = new FormData(); fd.append("file", e.target.files[0]); const r = await fetch("/api/damping/rules", { method: "POST", body: fd }), d = await r.json(); if (!r.ok) return alert(d.error); alert("Regra atualizada: " + d.points + " pontos."); PAGES.damping(); };
      if (!names.length) return;
      const rows = () => $$("tr[data-t]", root), F = $("#df");
      const recalc = () => { const res = []; rows().forEach(tr => { const d = num($(".dd", tr).value), f = num($(".df", tr).value), [lo, hi, r] = calc(d, +tr.dataset.tol, f); $(".mn", tr).textContent = fx(lo); $(".mx", tr).textContent = fx(hi); $(".rs", tr).innerHTML = r ? `<span class="badge ${cls(r)}">${r}</span>` : ""; if (d != null) res.push(r); });
        const o = !res.length ? "" : res.includes("DISAPPROVED") ? "DISAPPROVED" : res.some(r => r !== "APPROVED") || res.length < rows().length ? "INCOMPLETO" : "APPROVED"; $("#ov").innerHTML = o ? `<span class="badge ${cls(o)}">${o}</span>` : ""; };
      root.addEventListener("input", e => { if (e.target.closest("tr[data-t]")) recalc(); });
      const fill = t => { F.perfect_code.value = t.perfect_code || ""; F.label.value = t.label || ""; F.test_date.value = t.test_date || ""; F.notes.value = t.notes || "";
        rows().forEach(tr => { const p = (t.points || []).find(x => x.table_name === tr.dataset.t && Math.abs(x.velocity - tr.dataset.v) < 1e-6); $(".dd", tr).value = p?.drawing ?? ""; $(".df", tr).value = p?.found ?? ""; });
        cur = t.id || null; $("#dx").hidden = !cur; if (cur) $("#dx").href = `/api/damping/tests/${cur}/export.xlsx`; recalc(); };
      const list = async () => { const ts = await J("/api/damping/tests?q=" + encodeURIComponent($("#dq").value));
        $("#dl2").innerHTML = ts.length ? T(["#", "Código", "Identificação", "Data", "Resultado", ""], ts.map(t => `<tr><td>${t.id}</td><td>${t.product_id ? lnk(t.product_id, t.perfect_code) : esc(t.perfect_code || "–")}</td><td>${esc(t.label || "")}</td><td>${esc(t.test_date || "")}</td><td><span class="badge ${cls(t.overall)}">${t.overall}</span></td><td><button class="btn ghost" data-op="${t.id}">Abrir</button> <a class="btn ghost" href="/api/damping/tests/${t.id}/export.xlsx">Excel</a> <button class="btn ghost" data-rm2="${t.id}">Excluir</button></td></tr>`)) : empty("Nenhum ensaio salvo ainda."); };
      $("#dq").oninput = list;
      $("#sv").onclick = async e => { e.preventDefault(); const points = rows().map(tr => ({ table: tr.dataset.t, velocity: +tr.dataset.v, drawing: $(".dd", tr).value, found: $(".df", tr).value }));
        try { const r = await post("/api/damping/tests", { id: cur, ...Object.fromEntries(new FormData(F)), points }); cur = r.id; $("#dx").hidden = false; $("#dx").href = `/api/damping/tests/${cur}/export.xlsx`; list(); alert("Ensaio salvo."); } catch (er) { alert(er.message); } };
      $("#nw").onclick = e => { e.preventDefault(); fill({}); };
      root.addEventListener("click", async e => { const o = e.target.closest("[data-op]"), d = e.target.closest("[data-rm2]");
        if (o) { fill(await J("/api/damping/tests/" + o.dataset.op)); scrollTo(0, 0); } if (d && confirm("Excluir este ensaio?")) { await J("/api/damping/tests/" + d.dataset.rm2, { method: "DELETE" }); list(); } });
      const pc = F.perfect_code; pc.addEventListener("input", async () => { if (pc.value.length < 3) return; const d = await J("/api/products?size=8&q=" + encodeURIComponent(pc.value)); $("#dpl").innerHTML = d.rows.map(r => `<option value="${esc(r.perfect_code)}">${esc(r.description || "")}</option>`).join("");
        if (d.rows.some(r => r.perfect_code === pc.value.trim()) && rows().every(tr => !$(".dd", tr).value)) { const pts = await J("/api/damping/prefill?code=" + encodeURIComponent(pc.value.trim()));
          rows().forEach(tr => { const p = pts.find(x => x.table_name === tr.dataset.t && Math.abs(x.velocity - tr.dataset.v) < 1e-6); if (p?.drawing != null) $(".dd", tr).value = p.drawing; }); recalc(); } });
      F.test_date.value = new Date().toISOString().slice(0, 10); recalc(); list();
    },

    amostras: () => amostras(),
    desenhos: () => desenhos(),
    dashboard: () => NEW.pages.dashboard(),
    metas: () => NEW.pages.metas(),
    brands: () => brandsPage(),
    lados: () => ladosPage(),
    envio: () => envioPage(),
    atualizacao: () => atualizacao(),
  };

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


  // ---------- atualização de dados (insere só o que falta) ----------
  function atualizacao() {
    root.innerHTML = `<div class="notice">Envie as planilhas <b>com o mesmo nome de sempre</b> (ex.: <code>DadosR-D e DES.xlsx</code>, <code>Compra_de_amostra.xlsx</code>). O sistema lê todas as linhas, confere com o banco e <b>insere apenas o que ainda não está</b>. <b>Planilhas novas</b> (nome desconhecido) também entram: se as colunas forem de um cadastro conhecido, são carregadas como tal; senão, os dados ficam guardados como estão. Em ambos os casos aparecem em <a href="/fontes">Fontes e histórico</a>.
      Nada é apagado. Primeiro mostra o que seria alterado (<b>verificação</b>); só grava quando você clicar em <b>Aplicar</b> — e faz backup antes.</div>
      <div class="toolbar"><label class="btn ghost" style="cursor:pointer">Escolher planilhas…<input id="uf" type="file" multiple accept=".xlsx,.xls,.csv" hidden></label>
      <button class="btn ghost" id="uf-folder">Verificar a pasta bases_exemplo</button><span class="muted" id="uf-names"></span></div>
      <p id="uf-msg" class="imp-msg" role="status"></p><div id="uf-out"></div>`;
    const msg = (t, err) => { const m = $("#uf-msg"); m.textContent = t; m.className = "imp-msg" + (err ? " err" : ""); };
    const fmt = c => k => c[k] ? num(c[k]) : "–";
    const show = (res, applied) => {
      const rows = res.results.map(r => { const c = r.counts || {}, f = fmt(c), bad = r.status !== "ok";
        return `<tr><td>${esc(r.file)}</td><td>${esc(r.label || "")}</td><td>${bad ? `<span class="badge ${r.status === "erro" ? "bad" : "warn"}">${r.status}</span>` : num(r.rows)}</td><td><b>${f("new")}</b></td><td>${f("updated")}</td><td>${f("present")}</td><td>${f("unmatched")}</td><td class="muted" style="white-space:normal;min-width:260px">${(r.messages || []).slice(0, 3).map(esc).join("<br>")}</td></tr>`; });
      const t = res.totals, todo = t.new + t.updated;
      $("#uf-out").innerHTML = `<div class="cards mini-cards">${[["Novos", t.new], ["Atualizados", t.updated], ["Já existiam", t.present], ["Sem vínculo (guardados)", t.unmatched]].map(([l, v]) => `<div class="card"><span class="num sm">${num(v)}</span><small>${l}</small></div>`).join("")}</div>
        ${T(["Planilha", "Tipo de dado", "Linhas lidas", "Novos", "Atualizados", "Já existiam", "Sem vínculo", "Avisos"], rows)}
        ${applied ? `<div class="notice">✔ Atualização aplicada. Backup criado: <code>${esc(res.backup || "—")}</code>${res.equivalences ? " · equivalências recalculadas" : ""}. <a href="/dashboard">Ver dashboard</a></div>`
          : todo ? `<div class="acts"><button class="btn" id="uf-apply">Aplicar atualização (${num(t.new)} novos, ${num(t.updated)} atualizados)</button></div>`
                 : '<div class="notice">Banco já está em dia com estas planilhas: nada a inserir.</div>'}`;
      const ap = $("#uf-apply"); if (ap) ap.onclick = async () => { ap.disabled = true; msg("Aplicando… (backup + gravação)");
        try { const r = await post("/api/update/apply", { token: res.token }); msg(""); show(r, true); } catch (e) { ap.disabled = false; msg(e.message, true); } };
    };
    const check = async fd => { msg("Lendo as planilhas e comparando com o banco… pode levar alguns segundos."); $("#uf-out").innerHTML = "";
      try { const r = await J("/api/update/check", { method: "POST", body: fd }); msg(""); show(r, false); } catch (e) { msg(e.message, true); } };
    $("#uf").onchange = e => { const fs = [...e.target.files]; if (!fs.length) return; $("#uf-names").textContent = fs.length + " arquivo(s)"; const fd = new FormData(); fs.forEach(f => fd.append("files", f)); check(fd); };
    $("#uf-folder").onclick = () => { const fd = new FormData(); fd.append("folder", "1"); check(fd); };
  }

  Object.assign(PAGES, window.PSD_EXEC({ J, post, $, $$, esc, num, root, fail, empty }).pages);      // Pedidos em Aberto · Vendas (Curva A) · Garantia (Tailwind)
  (PAGES[page] || (() => root.innerHTML = empty("Página sem conteúdo.")))();
})();
