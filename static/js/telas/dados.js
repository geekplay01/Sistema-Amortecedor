/* Tela · Dados: Pendências, Fontes, Configurações e Atualização de dados (Damping foi para telas/damping.js).
   Usa o núcleo window.PSD (core.js); registra a tela com PSD.tela(slug, desenhar). Separado do antigo pages.js na etapa 16. */
(function () {
  const { $, $$, esc, J, post, qs, num, T, lnk, empty, root, page, url, fail, dlg, inp, dmy, NEW } = PSD;
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
  PSD.tela("pendencias", () => {
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
    });
  PSD.tela("fontes", async () => {
      try {
        const d = await J("/api/history");
        root.innerHTML = `<div class="toolbar"><span style="flex:1"></span><a class="btn" href="/api/export/fontes.xlsx">⬇ Baixar Excel</a></div><h3>Histórico de importações</h3>` + (d.batches.length ? T(["#", "Data", "Arquivo", "Planilha", "Categoria", "Linhas lidas", "Novos", "Prod. complementados", "Conflitos", "Erros", "Status"], d.batches.map(b => `<tr><td>${b.id}</td><td>${esc(b.imported_at)}</td><td>${esc(b.filename || "")}</td><td>${esc(b.sheet || "")}</td><td>${esc(b.category || "")}</td><td>${b.rows_read ?? "–"}</td><td>${b.rows_new}</td><td>${b.rows_updated}</td><td>${b.rows_conflict}</td><td>${b.rows_error}</td><td>${esc(b.status)}</td></tr>`)) : empty("Nenhuma importação ainda. Use “Importação de Excel”."))
          + `<h3>Fontes e prioridade</h3><p class="muted">Prioridade de 1 (maior) a 9. Usada para sinalizar qual fonte prevalece na análise manual de conflitos.</p>` + T(["Fonte", "Categoria", "Importações", "Dados", "Prioridade"], d.sources.map(s => `<tr><td>${esc(s.name)}</td><td>${esc(s.category || "")}</td><td>${s.imports}</td><td>${s.generic_rows ? `<button class="btn ghost sm" data-gv="${s.id}">Ver ${num(s.generic_rows)} linhas</button> <a class="btn ghost sm" href="/api/sources/${s.id}/export.xlsx">⬇ Excel</a>` : "–"}</td><td><select data-src="${s.id}">${[1, 2, 3, 4, 5, 6, 7, 8, 9].map(n => `<option ${n === s.priority ? "selected" : ""}>${n}</option>`).join("")}</select></td></tr>`));
        root.addEventListener("click", async e => { const g = e.target.closest("[data-gv]"); if (g) genericView(+g.dataset.gv, 1); });
        root.addEventListener("change", e => { const s = e.target.closest("[data-src]"); if (s) post("/api/sources/" + s.dataset.src, { priority: +s.value }).catch(fail); });
      } catch (e) { fail(e); }
    });
  PSD.tela("configuracoes", async () => {
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
    });
  PSD.tela("atualizacao", () => atualizacao());
})();
