/* Tela · Desenhos — visual Tailwind (etapa 16): envio (arrastar arquivos/ZIP/pasta), galeria por código, revisões e visualizador.
   Abas Desenhos técnicos × Projeto PERFECT (kind). Cada número do topo é um atalho (where=…) e bate com o total da galeria (tests: test_21);
   «Sem desenho» lista os itens que ainda não têm arquivo. Filtros na URL e lembrados (PSDTW.filtros); o Excel segue os mesmos filtros.
   Links de outras telas: /desenhos?kind=…&open=CÓDIGO abre o visualizador. Diálogos (revisar envio, visualizador, vincular) seguem no estilo antigo. */
(function () {
  const { $, $$, esc, J, post, qs, root, fail, dlg, tag, fext, dwTile, kb, dmy, dwCollect, dwPrevOk, dwNav } = PSD;
  const TW = window.PSDTW, { nf, badge, kpi, notice } = TW;
  const CHAVES = ["kind", "q", "where", "origin", "ext", "sort"];
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500";
  const botao = "rounded-lg border border-line bg-card px-3.5 py-2 text-sm font-semibold text-ink hover:bg-slate-500/10";
  const chip = (attrs, label, on, n, forte = false) => `<button type="button" ${attrs} aria-pressed="${on}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${on ? "border-blue-500 bg-blue-500 text-white" : forte ? "border-amber-500 bg-amber-500/10 text-ink hover:bg-amber-500/20" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${label}${n != null ? ` · ${nf(n)}` : ""}</button>`;
  const selectF = (name, rotulo, opts, cur, extra = "") => `<select name="${name}" class="${campo} max-w-[15rem]" title="${esc(rotulo)}" ${extra}>${rotulo ? `<option value="">${esc(rotulo)}</option>` : ""}${opts.map(([v, l]) => `<option value="${esc(v)}" ${String(v) === String(cur ?? "") ? "selected" : ""}>${esc(l)}</option>`).join("")}</select>`;
  const TAM = { P: 170, M: 215, G: 290 };
  const tam = { get: () => { try { return localStorage.getItem("psd-dw-tam") || "M"; } catch (e) { return "M"; } }, set: v => { try { localStorage.setItem("psd-dw-tam", v); } catch (e) { } } };

  function desenhos() {
    const abrir = new URLSearchParams(location.search).get("open");          // lido antes de filtros() reescrever a URL
    const F = TW.filtros("desenhos", CHAVES); let pg = 1, t, st = null;
    const kind = () => F.get().kind === "projeto" ? "projeto" : "desenho";
    const TXT = { desenho: "Solte os arquivos de desenho em <b>qualquer formato</b>, um <b>ZIP</b> ou uma pasta. O nome diz a <b>origem</b> (começa com <b>RED</b> = redesenvolvimento, <b>DES</b> = desenvolvimento), o <b>código</b> e a <b>revisão</b> (ex.: <code>RED_AMD0170_REV02.pdf</code>). O desenho vale para todos os cadastros (catálogo, DES e R-D), as revisões anteriores ficam guardadas e os cadastros mostram sempre a <b>vigente</b>.",
      projeto: "Anexe aqui o <b>Projeto PERFECT</b> (ex.: <code>1BP31901AB_REV01.pdf</code>). Ele aparece no cadastro dos itens <b>em desenvolvimento que ainda não estão no catálogo</b>, na <b>Compra de amostras</b> e no <b>Envio de amostra</b>. Mesma lógica: código e revisão pelo nome, revisões anteriores guardadas." };
    root.innerHTML = `<div class="flex flex-col gap-5">
      <div id="dw-kind" class="flex flex-wrap gap-2" role="tablist"></div>
      <section id="hero" class="grid gap-4 rounded-2xl border border-line bg-card p-5 shadow-sm lg:grid-cols-5">
        <div class="lg:col-span-3"><h3 id="dw-h2" class="m-0 text-base font-semibold text-ink"></h3><p id="dw-p" class="mb-0 mt-2 text-sm text-mute"></p></div>
        <label id="dz" class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-line px-4 py-5 text-center transition hover:border-blue-500 lg:col-span-2">
          <svg class="h-8 w-8 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16V4M7 9l5-5 5 5M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3"/></svg>
          <b class="text-sm text-ink">Arraste arquivos ou uma pasta para cá</b><span class="text-xs text-mute">PDF · DWG · DXF · STEP · imagens · ZIP · qualquer formato</span>
          <span class="mt-1 flex flex-wrap justify-center gap-2"><span class="rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-blue-700">Escolher arquivos ou ZIP</span><button type="button" id="dw-folder" class="${botao}">Escolher pasta</button></span>
          <input type="file" id="dw-f" multiple hidden><input type="file" id="dw-d" webkitdirectory hidden></label>
      </section>
      <p id="dw-msg" class="m-0 hidden text-sm" role="status"></p><div id="dw-done"></div>
      <div id="dw-k" class="grid grid-cols-2 gap-4 lg:grid-cols-4"></div>
      <div id="dw-q" class="flex flex-wrap items-center gap-2"></div>
      <form id="dw-form" class="flex flex-wrap items-center gap-2" autocomplete="off"></form>
      <div id="dw-meta" class="flex flex-wrap items-center justify-between gap-3 text-sm text-mute"></div>
      <div id="dw-grid"></div><div id="dw-pg" class="flex items-center justify-center gap-3 text-sm text-mute"></div>
    </div>`;
    const msg = (t, err) => { const m = $("#dw-msg"); m.textContent = t; m.classList.toggle("hidden", !t); m.classList.toggle("text-red-600", !!err); m.classList.toggle("text-mute", !err); };
    const semNome = () => kind() === "projeto" ? "Sem projeto" : "Sem desenho";
    const ATALHOS = [["No catálogo", "cat"], ["Em DES", "des"], ["Em R-D", "rd"], ["Sem vínculo", "sem", true], [null, "falta", true]];

    const desenharTopo = () => {
      const k = kind(), s = st || {}, w = F.get().where || "";
      $("#dw-kind").innerHTML = [["desenho", "Desenhos técnicos"], ["projeto", "Projeto PERFECT"]].map(([v, l]) => `<button type="button" role="tab" data-k="${v}" aria-selected="${v === k}" class="rounded-lg px-4 py-2 text-sm font-semibold ${v === k ? "bg-blue-600 text-white" : "border border-line bg-card text-ink hover:bg-slate-500/10"}">${l}</button>`).join("");
      $("#dw-h2").textContent = k === "projeto" ? "Projeto PERFECT" : "Desenhos técnicos"; $("#dw-p").innerHTML = TXT[k];
      if (!st) return;
      $("#dw-k").innerHTML = kpi(k === "projeto" ? "Códigos com projeto" : "Códigos com desenho", nf(s.codes), `${nf(s.files)} arquivo(s) guardado(s)`, "blue") +
        kpi("Revisões anteriores", nf(s.old), "guardadas no histórico", "slate") +
        kpi("Sem vínculo", nf(s.orphans), s.orphans ? "arquivos sem código: abra o cartão e informe" : "todo arquivo tem código", s.orphans ? "amber" : "green") +
        kpi(k === "projeto" ? "DES/R-D fora do catálogo sem projeto" : "Catálogo sem desenho", nf(s.missing), "use o atalho para ver a lista", s.missing ? "red" : "green");
      $("#dw-q").innerHTML = `<span class="mr-1 text-xs font-semibold uppercase tracking-wide text-mute">Atalhos</span>` +
        ATALHOS.map(([l, v, forte]) => chip(`data-w="${v}"`, l || semNome(), w === v, v === "sem" ? s.orphans : v === "falta" ? s.missing : s[v], forte)).join("");
    };
    const desenharFiltros = () => {
      const f = F.get(), s = st || {}, c = k => s[k] != null ? ` (${nf(s[k])})` : "", falta = f.where === "falta", off = falta ? 'disabled title="Não se aplica à lista de itens sem arquivo"' : "";
      $("#dw-form").innerHTML = `<input name="q" type="search" value="${esc(f.q || "")}" placeholder="Buscar código, descrição ou nome do arquivo…" class="${campo} min-w-[16rem] flex-1">` +
        selectF("where", "Todos os cadastros", [["cat", "No catálogo" + c("cat")], ["des", "Em desenvolvimento" + c("des")], ["rd", "Em redesenvolvimento" + c("rd")], ["sem", "Sem vínculo" + c("orphans")], ["falta", semNome() + c("missing")]], f.where) +
        selectF("origin", "Origem: todas", [["DESENVOLVIMENTO", "Origem DES"], ["REDESENVOLVIMENTO", "Origem RED"]], f.origin, off) +
        selectF("ext", "Todos os formatos", [".pdf", ".dwg", ".dxf", ".step", ".png", ".jpg"].map(x => [x, x.slice(1).toUpperCase()]), f.ext, off) +
        selectF("sort", "", [["recent", "Mais recentes"], ["code", "Código (A–Z)"], ["rev", "Mais revisões"]], f.sort || "recent", off) +
        `<span class="inline-flex overflow-hidden rounded-lg border border-line" title="Tamanho dos cartões">${Object.keys(TAM).map(v => `<button type="button" data-s="${v}" class="px-3 py-2 text-sm font-semibold ${tam.get() === v ? "bg-blue-600 text-white" : "bg-card text-ink hover:bg-slate-500/10"}">${v}</button>`).join("")}</span>` +
        `<button type="button" id="dw-clr" class="${botao}">Limpar filtros</button>`;
    };

    const cartao = c => c.code
      ? `<article class="dw-card" data-open="${esc(c.code)}" tabindex="0"><div class="dw-th"><div class="sk"></div>${dwTile(c.thumb_id, c.thumb_ext, true)}<span class="rev">${esc(c.label)}</span><span class="dw-ex">${c.exts.map(x => `<i>${esc(x)}</i>`).join("")}</span>
          <div class="dw-ov"><span class="btn sm">Visualizar</span><a class="btn ghost sm" href="/api/drawings/file/${c.thumb_id}?download=1" title="Baixar o arquivo vigente">⬇</a></div></div>
          <div class="dw-bd"><b>${esc(c.code)}</b><span class="clip" title="${esc(c.description || "")}">${esc(c.description || (c.registered ? "" : "Código ainda não cadastrado"))}</span>
          <div class="dw-tags">${c.origin ? `<span class="tag org ${c.origin === "REDESENVOLVIMENTO" ? "red" : "des"}" title="Origem pelo prefixo do nome do arquivo">${c.origin === "REDESENVOLVIMENTO" ? "RED" : "DES"}</span> ` : ""}${c.registries.map(tag).join(" ")}</div><small class="muted">${dmy(c.updated)} · ${c.n_revisions} revisão(ões)</small></div></article>`
      : `<article class="dw-card orph" data-orph="${c.file_id}" data-name="${esc(c.filename)}" tabindex="0"><div class="dw-th"><div class="sk"></div>${dwTile(c.thumb_id, c.thumb_ext, true)}<span class="rev warn">Sem código</span></div><div class="dw-bd"><b class="clip" title="${esc(c.filename)}">${esc(c.filename)}</b><small class="muted">Clique para informar o código</small></div></article>`;
    // item ainda sem arquivo: código leva à ficha (catálogo) ou à lista DES/R-D
    const REGC = { "Catálogo": "blue", DESENVOLVIMENTO: "amber", REDESENVOLVIMENTO: "violet" };
    const faltando = c => [c.product_id ? `<a href="#" class="font-semibold text-blue-600" data-ficha="${c.product_id}">${esc(c.code)}</a>`
        : `<a href="/${c.registries.includes("DESENVOLVIMENTO") ? "desenvolvimento" : "redesenvolvimento"}?q=${encodeURIComponent(c.code)}" class="font-semibold text-blue-600">${esc(c.code)}</a>`,
      `<span class="block min-w-[16rem] max-w-[34rem] truncate" title="${esc(c.description || "")}">${esc(c.description || "")}</span>`,
      c.registries.map(r => badge(r === "DESENVOLVIMENTO" ? "DES" : r === "REDESENVOLVIMENTO" ? "R-D" : r, REGC[r])).join(" ")];

    const stats = async () => { try { st = await J("/api/drawings/stats?kind=" + kind()); desenharTopo(); desenharFiltros(); } catch (e) { } };
    const load = async () => { try {
      const f = F.get(), falta = f.where === "falta";
      const d = await J("/api/drawings?" + qs({ ...f, kind: kind(), page: pg })), pages = Math.max(1, Math.ceil(d.total / d.size)), ativos = Object.keys(f).filter(k => k !== "kind" && k !== "sort").length;
      dwNav.list = falta ? [] : d.rows.filter(c => c.code).map(c => c.code);
      $("#dw-meta").innerHTML = `<span><b class="text-ink">${nf(d.total)}</b> ${falta ? "item(ns) sem arquivo" : "desenho(s)"}${ativos ? ` · ${ativos} filtro(s) ativo(s)` : ""}${F.restaurado && pg === 1 ? ' · <span class="text-amber-700">filtros da última visita</span>' : ""}</span>
        <a class="rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-blue-700" href="/api/export/desenhos.xlsx?${new URLSearchParams({ ...f, kind: kind() })}">⬇ Baixar Excel</a>`;
      $("#dw-grid").innerHTML = falta
        ? notice(`Para anexar, arraste o arquivo com o código no nome para a área acima (ex.: <code>DES_${esc(d.rows[0]?.code || "AMD0000")}_REV00.pdf</code>).`, "blue") + `<div class="mt-3">${TW.table([{ h: "Código" }, { h: "Descrição", nw: false }, { h: "Cadastros" }], d.rows.map(faltando), { h: "max-h-[65vh]" })}</div>`
        : d.rows.length ? `<div class="dw-grid" style="--cw:${TAM[tam.get()]}px">${d.rows.map(cartao).join("")}</div>` : TW.empty("Nenhum desenho com esses filtros. Arraste os arquivos para a área acima.");
      const b = (p, dis, l) => `<button type="button" data-p="${p}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${dis ? "disabled" : ""}>${l}</button>`;
      $("#dw-pg").innerHTML = pages > 1 ? `${b(pg - 1, pg < 2, "‹")} Página ${pg} de ${pages} ${b(pg + 1, pg >= pages, "›")}` : "";
    } catch (e) { $("#dw-grid").innerHTML = notice(esc(e.message), "red"); } };
    const refresh = () => { stats(); load(); }; dwNav.onDone = refresh;
    const aplicar = (logo = false) => { pg = 1; desenharTopo(); clearTimeout(t); t = setTimeout(load, logo ? 0 : 300); };
    const f = $("#dw-form");
    f.addEventListener("input", e => { const n = e.target.name; if (!n) return; F.set({ [n]: e.target.value }); if (n === "where") desenharFiltros(); aplicar(e.target.tagName === "SELECT"); });
    f.addEventListener("submit", e => e.preventDefault());
    f.addEventListener("click", e => {
      const s = e.target.closest("[data-s]"); if (s) { tam.set(s.dataset.s); desenharFiltros(); const g = $("#dw-grid .dw-grid"); if (g) g.style.setProperty("--cw", TAM[s.dataset.s] + "px"); return; }
      if (e.target.id === "dw-clr") { const k = F.get().kind; F.clear(); if (k) F.set({ kind: k }); desenharFiltros(); aplicar(true); }
    });
    $("#dw-q").addEventListener("click", e => { const b = e.target.closest("[data-w]"); if (!b) return; F.toggle("where", b.dataset.w); desenharFiltros(); aplicar(true); });
    $("#dw-kind").addEventListener("click", e => { const b = e.target.closest("[data-k]"); if (!b || b.dataset.k === kind()) return; F.set({ kind: b.dataset.k === "projeto" ? "projeto" : "" }); st = null; pg = 1; desenharTopo(); refresh(); });
    $("#dw-pg").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; load(); scrollTo(0, 0); } });
    $("#dw-grid").addEventListener("click", e => { if (e.target.closest("a")) return; openCard(e); }); $("#dw-grid").addEventListener("keydown", openCard);
    function openCard(e) { const c = e.target.closest("[data-open],[data-orph]"); if (!c || (e.type === "keydown" && e.key !== "Enter")) return; c.dataset.open ? dwOpen(c.dataset.open, refresh, kind()) : dwOrphan(+c.dataset.orph, c.dataset.name, refresh); }
    const send = async files => {
      if (!files.length) return msg(""); const fd = new FormData(); fd.append("kind", kind()); files.forEach(x => fd.append("files", x, x.name));
      msg(`Enviando ${files.length} arquivo(s) para análise…`);
      try { const r = await J("/api/drawings/check", { method: "POST", body: fd }); msg(""); dwReview(r, refresh); } catch (e) { msg(e.message, true); }
    };
    $("#dw-f").onchange = e => { send([...e.target.files]); e.target.value = ""; };
    $("#dw-d").onchange = e => { send([...e.target.files]); e.target.value = ""; };
    $("#dw-folder").onclick = e => { e.preventDefault(); e.stopPropagation(); $("#dw-d").click(); };
    const dz = $("#dz"), sobre = on => ["border-blue-500", "bg-blue-500/10"].forEach(c => dz.classList.toggle(c, on));
    ["dragenter", "dragover"].forEach(n => dz.addEventListener(n, e => { e.preventDefault(); sobre(true); }));
    ["dragleave", "drop"].forEach(n => dz.addEventListener(n, e => { e.preventDefault(); sobre(false); }));
    dz.addEventListener("drop", async e => { msg("Lendo os arquivos soltos…"); send(await dwCollect(e.dataTransfer)); });
    desenharTopo(); desenharFiltros(); stats(); load().then(() => { if (abrir) dwOpen(abrir, refresh, kind()); });
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
        const aviso = `✔ ${s.novos} novo(s), ${s.revisoes} revisão(ões), ${s.ignorados} ignorado(s) · ${s.redesenvolvimento} REDESENVOLVIMENTO, ${s.desenvolvimento} DESENVOLVIMENTO${s.sem_origem ? `, ${s.sem_origem} sem prefixo RED/DES` : ""}${s.sem_vinculo ? `, ${s.sem_vinculo} sem código (vincule clicando no cartão)` : ""}. Os cadastros já mostram a revisão vigente.`;
        const slot = $("#dw-done"); if (slot) slot.innerHTML = PSDTW.notice(aviso, "blue"); else root.insertAdjacentHTML("afterbegin", `<div class="notice">${aviso}</div>`); done && done(); }
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
  PSD.tela("desenhos", () => desenhos());
})();
