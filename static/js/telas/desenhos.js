/* Tela · Desenhos: envio, revisões, visualizador.
   Usa o núcleo window.PSD (core.js); registra a tela com PSD.tela(slug, desenhar). Separado do antigo pages.js na etapa 16. */
(function () {
  const { $, $$, esc, J, post, qs, num, empty, root, page, url, fail, dlg, tag, clip, fext, dwTile, kb, dmy, dwCollect, dwPrevOk, dwNav } = PSD;
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
  PSD.tela("desenhos", () => desenhos());
})();
