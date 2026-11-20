/* Núcleo das telas antigas (separado do pages.js na etapa 16): utilitários, ficha do produto, lista paginada, controle de status de DES/R-D e miniaturas de desenho.
   Expõe tudo em window.PSD. Cada tela vive em static/js/telas/<tela>.js e se registra com PSD.tela(slug, desenhar); page.html chama PSD.iniciar() depois de carregar tudo.
   Carregado depois de pages_new.js e pages_exec.js (fábricas window.PSD_NEW / window.PSD_EXEC). */
(function () {
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const J = async (u, o) => { const r = await fetch(u, o), d = await r.json().catch(() => ({})); if (!r.ok) throw new Error(d.error || ("Erro " + r.status)); return d; };
  const post = (u, b) => J(u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) });
  const qs = o => new URLSearchParams(Object.entries(o).filter(([, v]) => v !== "" && v != null)).toString();
  const num = (v, d = 0) => v == null ? "–" : Number(v).toLocaleString("pt-BR", { maximumFractionDigits: d });
  const brl = v => "R$ " + Number(v || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const SYS = { gas: "FORCE GAS", oleo: "FORCE OIL" }, yr = a => a.year_from ? a.year_from + (a.year_to && a.year_to !== a.year_from ? "–" + a.year_to : "") : "–";
  const T = (h, rows) => `<div class="tbl"><table><tr>${h.map(x => `<th>${x}</th>`).join("")}</tr>${rows.join("")}</table></div>`;
  const lnk = (id, t) => `<a href="#" data-ficha="${id}">${esc(t)}</a>`;
  const empty = m => `<div class="notice soon"><img src="/static/img/amortecedor-desenho.png" alt="" width="72"><div>${m}</div></div>`;
  const root = $("#panel"), page = root.dataset.page, url = new URLSearchParams(location.search);
  const fail = e => { root.insertAdjacentHTML("afterbegin", `<div class="notice err">${esc(e.message)}</div>`); };

  // ---------- ficha técnica (janela) ----------
  const dlg = document.createElement("dialog"); dlg.className = "dlg"; document.body.appendChild(dlg);
  dlg.addEventListener("click", e => { if (e.target === dlg || e.target.closest("[data-close]")) dlg.close(); });
  document.addEventListener("click", e => { const a = e.target.closest("[data-ficha]"); if (a) { e.preventDefault(); openFicha(a.dataset.ficha, e.ctrlKey || e.metaKey || e.button === 1); } });
  const kv = (k, v) => `<div><small>${k}</small><b>${v == null || v === "" ? "—" : esc(v)}</b></div>`;
  const usd = v => "US$ " + Number(v).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  // ficha = página do item (etapa 17 · Q9): /item-id/<id> redireciona para /item/<código>; Ctrl/botão do meio abre em outra aba
  function openFicha(id, novaAba) { const u = "/item-id/" + encodeURIComponent(id); if (novaAba) window.open(u, "_blank"); else location.href = u; }

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
  const prodRow = p => `<tr><td>${lnk(p.id, p.perfect_code)}</td><td>${esc(p.description || "")}${(p.via || []).length ? `<div class="via">${p.via.map(v => `<span class="xchip ${v.type === "concorrente" ? "" : "more"}" title="Código ${esc(v.type)} que casou com a busca">${esc(v.brand || v.type)} ${esc(v.code)}</span>`).join(" ")}</div>` : ""}</td><td>${SYS[p.system_type] || "–"}</td><td>${num(p.lmin_mm)}</td><td>${num(p.lmax_mm)}</td><td>${p.fob != null ? `${p.fob}${p.fob_supplier ? ` <small class="muted">${esc(p.fob_supplier)}</small>` : ""}` : "–"}</td><td>${p.apps}</td><td>${p.ncodes}</td><td>${p.pend ? `<span class="badge warn">${p.pend}</span>` : ""}</td>${dwCol(p.perfect_code)}</tr>`;
  const prodHead = ["Código PERFECT", "Descrição", "Sistema", "Lmin", "Lmax", "FOB (US$)", "Aplic.", "Códigos", "Pend.", "Desenho"];
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
  /* sub status do servidor no detalhe do item (etapa 20 · Q3: só leitura) — por coluna, com quantas aplicações têm cada valor */
  const subPanel = rows => { const g = new Map();
    rows.forEach(r => (r.subs || []).forEach(x => { const m = g.get(x.l) || new Map(); m.set(x.v, (m.get(x.v) || 0) + 1); g.set(x.l, m); }));
    return `<div class="fpanel"><h4>Sub status do servidor</h4>${g.size ? `<div class="fgrid2">${[...g].map(([l, m]) => `<div class="fgroup"><h5>${esc(l)}</h5>${[...m].map(([v, n]) => `<div>${esc(v)} <small class="muted">· ${n} de ${rows.length} aplicaç${rows.length === 1 ? "ão" : "ões"}</small></div>`).join("")}</div>`).join("")}</div>` : '<p class="muted">Nenhum sub status no servidor.</p>'}</div>`; };
  const subsTxt = r => [...new Set((r.subs || []).map(x => x.v))].join(" · ");
  const rdOpen = async (k, code) => { try { const d = await J(`/api/rd/${k}/item/` + encodeURIComponent(code)); const lab = k === "des" ? "DESENVOLVIMENTO" : "REDESENVOLVIMENTO", other = d.other.map(o => o.suggestion);
    dlg.innerHTML = `<div class="dh"><div><h2>${esc(d.code)} ${tag(lab)} ${other.map(tag).join(" ")}</h2><p>${esc(d.description || "")}</p></div><div><a class="btn ghost" href="/item/${encodeURIComponent(d.code)}">Página do item</a> <button class="btn ghost" data-close>Fechar</button></div></div>
      ${other.length ? `<div class="notice">Este código também consta em <b>${other.join(", ")}</b>.</div>` : ""}
      <div class="curline"><span class="cur up">▲ Curtiu ${d.curtiu || 0}</span><span class="cur down">▼ Não curtiu ${d.nao_curtiu || 0}</span></div>
      ${k === "rd" ? `<div class="vpanel" data-vc="${esc(d.code)}"><b>Validação</b> ${(d.validations || []).length ? d.validations.map(v => `<span class="vchip">enviada em ${dmy(v.sent_at)}${v.by_user ? " · " + esc(v.by_user) : ""} <a href="#" data-vundo="${v.id}">desfazer</a></span>`).join("") : '<span class="muted">nenhuma validação enviada registrada.</span>'}<button class="btn sm" data-vsend="${esc(d.code)}">Marcar validação enviada</button><small class="muted">A meta de Redesenvolvimento conta quando o status passar de PENDENTE CONFIRMAÇÃO para ITEM RECEBIDO.</small></div>` : ""}
      ${d.product ? "" : '<p class="muted">Ainda não está no catálogo.</p>'}
      ${subPanel(d.rows)}
      ${d.cross && d.cross.length ? `<div class="xref"><b>Referência cruzada:</b> ${xchips(d.cross)}</div>` : ""}
      <div data-dwblock="${esc(d.code)}" data-dwkind="projeto"></div>
      ${d.product ? "" : `<div data-dwblock="${esc(d.code)}"></div>`}
      ${d.info && Object.keys(d.info).length ? `<details class="sec"><summary><b>Todas as informações do servidor</b> <span class="badge">${Object.keys(d.info).length}</span></summary><div class="infogrid">${Object.entries(d.info).map(([k, v]) => `<div><small>${esc(k)}</small><b>${esc(v)}</b></div>`).join("")}</div></details>` : ""}
      <h4>Aplicações (${d.rows.length})</h4>` + T(["Montadora", "Veículo", "Aplicação", "Anos", "Status", "Sub status", "Fornecedor", "Amostra comprada", "Amostra enviada"], d.rows.map(r => `<tr><td>${esc(r.make || "")}</td><td>${esc(r.vehicle || "")}</td><td>${esc(r.application_text || "")}</td><td>${yr(r)}</td><td>${esc(r.status || "")}</td><td>${esc(subsTxt(r))}</td><td>${esc(r.supplier || "")}</td><td>${r.bought || ""}</td><td>${r.sent || ""}</td></tr>`)) +
      `<h4>Compras de amostra ligadas (${d.samples.length})</h4>` + (d.samples.length ? d.samples.map(x => `SC ${esc(x.sc_number || "–")} · ${esc(x.sample_code || "")} · ${esc(x.supplier || "")} · ${esc(x.stage)}`).join("<br>") + ` <a href="/amostras?q=${encodeURIComponent(d.code)}">abrir em Compra de amostras</a>` : '<p class="muted">Nenhuma.</p>') +
      `<h4>Ensaios de damping force (${d.damping.length})</h4>` + (d.damping.length ? `<a href="/damping">ver em Damping force</a>` : '<p class="muted">Nenhum.</p>'); dlg.showModal(); dwBlocks(dlg); } catch (e) { PSDTW.erro(e); } };
  dlg.addEventListener("click", async e => {   // validação enviada (REDESENVOLVIMENTO)
    const s = e.target.closest("[data-vsend]"), u = e.target.closest("[data-vundo]"); if (!s && !u) return; e.preventDefault();
    try { if (s) await post("/api/validations", { code: s.dataset.vsend, kind: "REDESENVOLVIMENTO" }); else await J("/api/validations/" + u.dataset.vundo, { method: "DELETE" }); const c = (s || u).closest(".vpanel").dataset.vc; dlg.close(); rdOpen("rd", c); } catch (er) { PSDTW.erro(er); } });
  document.addEventListener("click", e => { const a = e.target.closest("[data-rd]"); if (a) { e.preventDefault(); rdOpen(a.dataset.rd, a.dataset.code); } });
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

  const NEW = window.PSD_NEW({ J, post, $, $$, esc, num, tag, T, clip, empty, fail, dlg, qs, dmy, root, FLG, FGROUPS });
  const pages = {};
  const tela = (slug, desenhar) => { pages[slug] = desenhar; };
  const iniciar = () => {
    Object.entries(window.PSD_EXEC({ J, post, $, $$, esc, num, root, fail, empty }).pages).forEach(([s, f]) => pages[s] = pages[s] || f);   // Pedidos em Aberto · Vendas (Curva A) · Garantia (Tailwind)
    (pages[page] || (() => root.innerHTML = empty("Página sem conteúdo.")))();
  };
  window.PSD = { $, $$, esc, J, post, qs, num, brl, SYS, yr, T, lnk, empty, root, page, url, fail, dlg, kv, usd, openFicha, listView, inp, sel, prodRow, prodHead, fillSel, initLists, tag, clip, AX, SD, FLG, FGROUPS, flagSel, flagChips, xchips, rdOpen, FMT, fext, dwTile, kb, dmy, KL, dwBlocks, dwFill, dwCol, dwCollect, dwPrevOk, dwNav, NEW, pages, tela, iniciar };
})();
