/* Tela · Configurações — visual Tailwind (etapa 16 · B). Seções: perfil, senha, aparência, regras das telas (etapa 21: os textos que explicavam cada
   tela, abertos pelo link «Regras da tela» ao lado do título — #telas-<tela>); e, só para administradores: usuários, regras de negócio,
   servidor e sincronização (somente leitura no POWERBI), backups. A seção aberta fica no endereço (#perfil, #servidor…).
   Com PSD_AUTH=off (desenvolvimento) não há usuário: perfil e senha mostram o aviso; as seções de administração continuam abertas. */
(function () {
  const { $, $$, esc, J, post, root, fail } = PSD;
  const TW = window.PSDTW, { nf, badge, card, notice, empty } = TW;
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500";
  const botao = "cursor-pointer rounded-lg border border-line bg-card px-3.5 py-2 text-sm font-semibold text-ink no-underline hover:bg-slate-500/10";
  const primario = "rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50";
  const mini = "rounded-lg border border-line bg-card px-2.5 py-1 text-xs font-semibold text-ink no-underline hover:bg-slate-500/10";
  const rot = (label, ctrl, hint = "", cls = "") => `<label class="flex flex-col gap-1 text-sm font-semibold text-ink ${cls}">${label}${ctrl}${hint ? `<small class="text-xs font-normal text-mute">${hint}</small>` : ""}</label>`;
  const inp = (name, attrs = "") => `<input name="${name}" class="${campo} font-normal" ${attrs}>`;
  const aviso = id => `<span id="${id}" class="text-sm" role="status"></span>`;
  const sub = t => `<p class="mb-4 mt-0 text-sm text-mute">${t}</p>`;
  const quando = s => s ? `${TW.dmy(s)} ${String(s).slice(11, 16)}`.trim() : "–";
  const ICO = {
    perfil: "M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z", seg: "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6zM9 12l2 2 4-4", tema: "M12 3a9 9 0 109 9 7 7 0 01-9-9z",
    users: "M17 21v-2a4 4 0 00-4-4H7a4 4 0 00-4 4v2M10 11a4 4 0 100-8 4 4 0 000 8zM21 21v-2a4 4 0 00-3-3.9M16 3.1a4 4 0 010 7.8", regras: "M4 6h16M4 12h10M4 18h6M18 14l2 2 3-4", srv: "M4 5h16v5H4zM4 14h16v5H4zM8 7.5h.01M8 16.5h.01", bk: "M4 7c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3zM4 7v10c0 1.7 3.6 3 8 3s8-1.3 8-3V7M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" };
  const SECT = [["perfil", "Meu perfil", ICO.perfil], ["seguranca", "Senha e acesso", ICO.seg], ["aparencia", "Aparência", ICO.tema], ["telas", "Regras das telas", ICO.regras]];
  const ADM = [["usuarios", "Usuários", ICO.users], ["regras", "Regras de negócio", ICO.regras], ["servidor", "Servidor e sincronização", ICO.srv], ["backups", "Backups", ICO.bk]];

  // ---------- servidor SQL (só leitura) e sincronização ----------
  async function servidor(host) {
    host.innerHTML = '<p class="text-sm text-mute">Consultando o servidor…</p>';
    const avisos = r => { try { const k = Object.keys(JSON.parse(r.warnings || "{}")); return k.length ? `<span class="text-mute" title="${esc(r.warnings)}">${k.length} aviso(s)</span>` : "–"; } catch (e) { return "–"; } };
    const draw = async () => {
      let st, rn; try { [st, rn] = await Promise.all([J("/api/pipeline/status"), J("/api/pipeline/runs")]); } catch (e) { host.innerHTML = notice(esc(e.message), "red"); return; }
      const item = (l, v) => `<div class="rounded-xl border border-line px-4 py-3"><div class="psd-rot">${l}</div><div class="mt-1 text-sm font-semibold text-ink">${v}</div></div>`;
      const drv = st.drivers.length ? st.drivers.map(d => badge(d, "green")).join(" ") : badge("nenhum (rode o iniciar.bat novamente)", "amber");
      host.innerHTML = card(`Servidor SQL: ${esc(st.host)}`,
        `<div class="grid grid-cols-2 gap-3 lg:grid-cols-3">${item("Credenciais (.env)", st.configured ? "✔ preenchidas" : "✖ faltam usuário/senha")}${item("Drivers", drv)}${item("Última sincronização", st.last_ok_at ? quando(st.last_ok_at) : "nunca")}
          ${item("Itens no servidor", nf(st.items))}${item("Sincronizações feitas", nf(st.runs))}${item("Agendamento", "diário (DEV_SYNC_HOURS)")}</div>
        ${st.last_status === "erro" ? `<div class="mt-3">${notice(`<b>Última tentativa falhou:</b> ${esc(st.last_error || "")}`, "red")}</div>` : ""}
        ${rn.tracking.since ? `<p class="mb-0 mt-3 text-sm text-mute">O servidor só guarda o status atual: o sistema grava um <b class="text-ink">retrato a cada sincronização</b> (marco zero em ${TW.dmy(rn.tracking.since)}) e detecta as mudanças de status a partir dele. O servidor só é lido (SELECT), nunca alterado.</p>` : ""}`,
        `<button type="button" id="srvgo" class="${primario}" ${st.running || !st.configured ? "disabled" : ""}>${st.running ? "Sincronizando…" : "Sincronizar agora"}</button>`)
        + `<div class="mt-5">${card("Últimas sincronizações", rn.runs.length ? TW.table([{ h: "#", r: true }, { h: "Início" }, { h: "Fim" }, { h: "Resultado" }, { h: "Linhas", r: true }, { h: "Itens", r: true }, { h: "Eventos", r: true }, { h: "Novos", r: true }, { h: "Ausentes", r: true }, { h: "Avisos" }],
            rn.runs.map(r => [r.id, quando(r.started_at), quando(r.finished_at), r.status === "ok" ? badge(r.baseline ? "marco zero" : "ok", "green") : `<span title="${esc(r.error || "")}">${badge("erro", "red")}</span>`,
              nf(r.source_rows), nf(r.items), nf(r.events), nf(r.new_items), nf(r.removed_items), avisos(r)]), { h: "max-h-[45vh]" }) : empty("Nenhuma sincronização ainda."))}</div>`
        + (rn.datasets.length ? `<div class="mt-5">${card("Compras, vendas e estoque", TW.table([{ h: "Conjunto" }, { h: "Objeto no servidor" }, { h: "Linhas", r: true }, { h: "Resultado" }, { h: "Quando" }, { h: "Observação", nw: false }],
            rn.datasets.map(r => [esc(r.dataset), esc(r.object || ""), nf(r.rows), badge(r.status, r.status === "ok" ? "green" : "amber"), quando(r.at), esc(r.note || "")])))}</div>` : "");
      const b = $("#srvgo"); if (b) b.onclick = async () => { b.disabled = true; b.textContent = "Sincronizando…"; try { await post("/api/pipeline/sync"); window.psdSyncPoll && window.psdSyncPoll(draw); } catch (e) { PSDTW.erro(e); draw(); } };
    };
    draw();
  }

  async function configuracoes() {
    let me; try { me = await J("/api/auth/me"); } catch (e) { return fail(e); }
    const user = me.user, admin = !!me.admin;
    let cur = (location.hash || "#perfil").slice(1), alvo = "";
    if (cur.startsWith("telas-")) { alvo = cur; cur = "telas"; }            // «Regras da tela» (link ao lado do título de cada tela) abre direto na tela certa
    if (![...SECT, ...ADM].some(x => x[0] === cur) || (!admin && ADM.some(x => x[0] === cur))) cur = "perfil";
    const put = (u, b) => J(u, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) });
    const nav = b => `<button type="button" data-s="${b[0]}" aria-current="${b[0] === cur}" class="flex items-center gap-2 rounded-lg px-3 py-2 text-left text-sm font-semibold ${b[0] === cur ? "bg-blue-500/10 text-blue-600" : "text-ink hover:bg-slate-500/10"}"><svg viewBox="0 0 24 24" class="h-4 w-4 shrink-0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="${b[2]}"/></svg>${b[1]}</button>`;
    root.innerHTML = `<div class="flex flex-col gap-5 lg:flex-row lg:items-start">
      <nav id="snav" class="flex flex-wrap gap-1 rounded-2xl border border-line bg-card p-2 shadow-sm lg:w-60 lg:shrink-0 lg:flex-col">${SECT.map(nav).join("")}${admin ? `<div class="w-full px-3 pb-1 pt-3 psd-rot">Administração</div>${ADM.map(nav).join("")}` : ""}</nav>
      <div id="spane" class="flex min-w-0 flex-1 flex-col gap-5"></div></div>`;
    const msg = (id, t, err) => { const m = $("#" + id); if (m) { m.textContent = t; m.className = "text-sm font-semibold " + (err ? "text-red-600" : "text-emerald-600"); } };
    const avatar = u => u.avatar ? `<img src="/avatar/${u.id}?t=${Date.now()}" alt="Foto de ${esc(u.username)}" class="h-full w-full object-cover">` : esc((u.username || "?").slice(0, 1).toUpperCase());
    const semLogin = notice("<b>Login desligado neste computador.</b> O sistema está com <code>PSD_AUTH=off</code> (modo de desenvolvimento), por isso não há usuário para editar. Remova essa linha do arquivo <code>.env</code> e reinicie para usar contas.", "amber");
    const acoes = (btn, id) => `<div class="flex flex-wrap items-center gap-3 sm:col-span-2">${btn}${aviso(id)}</div>`;
    const PANES = {
      perfil: () => !user ? semLogin : card("Meu perfil", `<div class="flex flex-wrap items-center gap-4"><div id="av" class="grid h-16 w-16 shrink-0 place-items-center overflow-hidden rounded-full bg-blue-600 text-2xl font-bold text-white">${avatar(user)}</div>
          <div class="flex flex-col gap-1"><div class="flex flex-wrap items-center gap-2 text-lg font-semibold text-ink">${esc(user.username)} ${badge(user.role === "admin" ? "Administrador" : "Usuário", user.role === "admin" ? "violet" : "slate")}</div>
            <div class="text-sm text-mute">Conta criada em ${TW.dmy(user.created_at)}, último acesso ${user.last_login ? quando(user.last_login) : "—"}</div>
            <div class="mt-1 flex flex-wrap items-center gap-2"><label class="${botao} py-1.5 text-xs">Escolher foto<input type="file" id="avf" accept="image/png,image/jpeg,image/webp,image/gif" hidden></label>${user.avatar ? `<button type="button" class="${botao} py-1.5 text-xs" id="avd">Remover foto</button>` : ""}${aviso("avm")}</div></div></div>`)
        + card("Nome de usuário", sub("É o nome usado para entrar. Por segurança, confirme com a senha atual.") + `<form id="fu" class="grid gap-4 sm:grid-cols-2">${rot("Novo usuário", inp("username", `value="${esc(user.username)}" minlength="3" required autocomplete="username"`))}${rot("Senha atual", inp("password", 'type="password" required autocomplete="current-password"'))}${acoes(`<button class="${primario}" type="submit">Salvar usuário</button>`, "fum")}</form>`),
      seguranca: () => !user ? semLogin : card("Alterar senha", sub("Use ao menos 8 caracteres. A senha é guardada com hash: nem o administrador consegue lê-la.") + `<form id="fp" class="grid gap-4 sm:grid-cols-2">${rot("Senha atual", inp("old", 'type="password" required autocomplete="current-password"'), "", "sm:col-span-2")}
          ${rot("Nova senha", inp("new", 'type="password" minlength="8" required autocomplete="new-password"'))}${rot("Repita a nova senha", inp("new2", 'type="password" minlength="8" required autocomplete="new-password"'))}${acoes(`<button class="${primario}" type="submit">Alterar senha</button>`, "fpm")}</form>`)
        + card("Sessão", sub("A sessão expira sozinha após 12 horas.") + `<a class="${botao}" href="/logout">Sair deste computador</a>`),
      /* etapa 21: os textos de regra saíram das telas e ficam aqui (regras_telas.py), um cartão por tela, com o link de volta */
      telas: async () => { const d = await J("/api/regras-telas");
        return `<div class="flex flex-wrap gap-2 rounded-2xl border border-line bg-card p-3 shadow-sm">${d.map(t => `<a class="${mini}" href="#telas-${t.slug}" data-ir="${t.slug}">${esc(t.titulo)}</a>`).join("")}</div>`
          + d.map(t => `<section id="telas-${t.slug}" class="psd-regra scroll-mt-4">${card(esc(t.titulo), `<ul class="m-0 flex list-disc flex-col gap-2 pl-5 text-sm leading-relaxed text-ink">${t.itens.map(i => `<li>${i}</li>`).join("")}</ul>`,
              `<a class="${mini}" href="/${t.slug}">Abrir a tela</a>`)}</section>`).join(""); },
      aparencia: () => card("Aparência", sub("Escolha o modo de cor. Fica gravado neste navegador.") + `<div id="thm" class="inline-flex rounded-lg border border-line p-1">${[["light", "Claro"], ["dark", "Escuro"]].map(([t, l]) => `<button type="button" data-t="${t}" class="rounded-md px-4 py-1.5 text-sm font-semibold">${l}</button>`).join("")}</div>`),
      usuarios: async () => { const d = await J("/api/admin/users");
        return card("Usuários", sub("Administradores podem alterar metas, regras, backups e usuários. Sempre existe ao menos um administrador.") + TW.table([{ h: "Usuário" }, { h: "Perfil" }, { h: "Último acesso" }, { h: "" }],
            d.users.map(u => [`<b>${esc(u.username)}</b>${u.id === d.me ? " " + badge("você", "blue") : ""}`,
              `<select data-role="${u.id}" class="rounded-lg border border-line bg-card px-2 py-1 text-sm text-ink"><option value="admin" ${u.role === "admin" ? "selected" : ""}>Administrador</option><option value="user" ${u.role === "user" ? "selected" : ""}>Usuário</option></select>`,
              u.last_login ? TW.dmy(u.last_login) : "—", `<span class="flex gap-1"><button type="button" class="${mini}" data-rp="${u.id}" data-n="${esc(u.username)}">Redefinir senha</button>${u.id === d.me ? "" : `<button type="button" class="${mini}" data-du="${u.id}" data-n="${esc(u.username)}">Remover</button>`}</span>`]), { h: "max-h-[50vh]" })
            + `<div class="mt-2">${aviso("um")}</div>`)
          + card("Novo usuário", `<form id="fn" class="grid gap-4 sm:grid-cols-3">${rot("Usuário", inp("username", 'required minlength="3"'))}${rot("Senha inicial", inp("password", 'type="password" required minlength="8" autocomplete="new-password"'))}
            ${rot("Perfil", `<select name="role" class="${campo} font-normal"><option value="user">Usuário</option><option value="admin">Administrador</option></select>`)}<div class="flex flex-wrap items-center gap-3 sm:col-span-3"><button class="${primario}" type="submit">Criar usuário</button>${aviso("fnm")}</div></form>`); },
      regras: async () => { const d = await J("/api/settings");
        return card("Regras de negócio", sub("Valem para listas, contadores, metas e sugestões de compra.") + `<form id="fr" class="grid gap-4 sm:grid-cols-2">
            ${rot("Somente itens cuja descrição contém", inp("only_description", `value="${esc(d.only_description)}" placeholder="vazio = todos os itens"`), `Padrão: ${esc(d.defaults.only_description)}. Sem acento nem diferença de maiúsculas.`)}
            ${rot("Usuário validador (USER_VALID)", inp("goal_valid_user", `value="${esc(d.goal_valid_user)}" required`), `Padrão: ${esc(d.defaults.goal_valid_user)}. Conta só item com USER_VALID igual a este (sem diferença de maiúsculas ou espaços).`)}
            ${rot("Como as metas contam", `<select name="goal_basis" class="${campo} font-normal"><option value="validacao" ${d.goal_basis === "validacao" ? "selected" : ""}>Validações do usuário (SUGESTÃO DES / R-D no ano da aprovação)</option><option value="recebido" ${d.goal_basis === "recebido" ? "selected" : ""}>Itens que chegaram a ITEM RECEBIDO no ano</option></select>`, "Padrão: validações.")}
            ${rot("Meta de lead time: amortecedores (dias)", inp("leadtime_meta_dias", `type="number" min="30" max="720" value="${esc(d.leadtime_meta_dias ?? 180)}" required`), "Padrão: 180 dias (6 meses). Usada na análise de prazos em Pedidos em Aberto.")}
            ${rot("Ler medidas com o Claude (API) na Validação", `<select name="validacao_ia" class="${campo} font-normal"><option value="0" ${d.validacao_ia ? "" : "selected"}>Desligada: as medidas são digitadas no desenho</option><option value="1" ${d.validacao_ia ? "selected" : ""}>Ligada: o Claude lê os desenhos (as imagens vão para a API da Anthropic)</option></select>`, "Padrão: desligada. Ligada, precisa da chave ANTHROPIC_API_KEY no ~/.perfect_shock_data/.env e do SDK anthropic.")}
            ${acoes(`<button class="${primario}" type="submit">Salvar regras</button><a class="${botao}" href="/metas">Editar metas do ano</a>`, "frm")}</form>`)
          + card("Como as metas contam", `<ul class="m-0 flex list-disc flex-col gap-2 pl-5 text-sm text-ink"><li><b>Validações</b> (padrão): itens com USER_VALID = usuário validador e LINHA «Amortecedor», separados pela SUGESTÃO (<b>DES</b> = DESENVOLVIMENTO, <b>R-D</b> = REDESENVOLVIMENTO), no ano da DATA_APROVACAO.</li>
            <li><b>DESENVOLVIMENTO</b> (sempre): status chegou a <b>ITEM RECEBIDO</b> no ano <u>e</u> tem a validação do usuário. <b>Itens recebidos</b> (opção): REDESENVOLVIMENTO = foi de <b>PENDENTE CONFIRMAÇÃO</b> a <b>ITEM RECEBIDO</b> no ano <u>e</u> tem a validação do usuário.</li><li>Cada código conta uma vez por ano.</li></ul>`); },
      servidor: () => '<div id="srvpanel" class="flex flex-col"></div>',
      backups: async () => { const d = await J("/api/backups");
        return card("Backups", sub(`Banco local: <code>${esc(d.db)}</code>, ${nf(d.size / 1048576, 2)} MB. Antes de cada atualização aplicada e de cada restauração o sistema cria um backup automático.`)
            + `<div class="flex flex-wrap items-center gap-2"><button type="button" class="${primario}" id="bk">Criar backup agora</button><a class="${botao}" href="/api/export/configuracoes.xlsx">⬇ Excel (lista)</a>${aviso("bkm")}</div>`)
          + card(`Backups guardados (${nf(d.backups.length)})`, d.backups.length ? TW.table([{ h: "Arquivo" }, { h: "Data" }, { h: "Tamanho", r: true }, { h: "" }],
              d.backups.map(b => [esc(b.name), esc(b.date), nf(b.size / 1048576, 2) + " MB", `<span class="flex gap-1"><a class="${mini}" href="/api/backups/${encodeURIComponent(b.name)}">Baixar</a><button type="button" class="${mini}" data-rs="${esc(b.name)}">Restaurar</button></span>`]), { h: "max-h-[55vh]" }) : empty("Nenhum backup ainda.")); }
    };
    const wire = {
      perfil() {
        const f = $("#avf"); if (f) f.onchange = async () => { if (!f.files[0]) return; const fd = new FormData(); fd.append("file", f.files[0]); msg("avm", "Enviando…"); try { await J("/api/auth/avatar", { method: "POST", body: fd }); location.reload(); } catch (e) { msg("avm", e.message, true); } };
        const d = $("#avd"); if (d) d.onclick = async () => { try { await J("/api/auth/avatar", { method: "DELETE" }); location.reload(); } catch (e) { msg("avm", e.message, true); } };
        const fu = $("#fu"); if (fu) fu.onsubmit = async e => { e.preventDefault(); try { await post("/api/auth/username", Object.fromEntries(new FormData(fu))); msg("fum", "Usuário alterado."); setTimeout(() => location.reload(), 600); } catch (er) { msg("fum", er.message, true); } };
      },
      seguranca() {
        const fp = $("#fp"); if (fp) fp.onsubmit = async e => { e.preventDefault(); const v = Object.fromEntries(new FormData(fp)); if (v.new !== v.new2) return msg("fpm", "As senhas novas não conferem.", true);
          try { await post("/api/auth/password", { old: v.old, new: v.new }); fp.reset(); msg("fpm", "Senha alterada."); } catch (er) { msg("fpm", er.message, true); } };
      },
      telas() {
        const ir = s => { const el = document.getElementById("telas-" + s); if (!el) return; $$(".psd-regra.on").forEach(x => x.classList.remove("on")); el.classList.add("on"); el.scrollIntoView({ block: "start" }); };
        $("#spane").onclick = e => { const a = e.target.closest("[data-ir]"); if (!a) return; e.preventDefault(); history.replaceState(null, "", location.pathname + "#telas-" + a.dataset.ir); ir(a.dataset.ir); };
        if (alvo) { ir(alvo.slice(6)); alvo = ""; }
      },
      aparencia() { const mark = () => $$("#thm button").forEach(b => { const on = b.dataset.t === psdTheme.get(); b.setAttribute("aria-pressed", on); b.className = "rounded-md px-4 py-1.5 text-sm font-semibold " + (on ? "bg-blue-600 text-white" : "text-ink hover:bg-slate-500/10"); });
        mark(); $("#thm").onclick = e => { const b = e.target.closest("[data-t]"); if (b) { psdTheme.set(b.dataset.t); mark(); } }; },
      usuarios() {
        const pane = $("#spane");
        pane.onchange = async e => { const r = e.target.closest("[data-role]"); if (r) try { await put("/api/admin/users/" + r.dataset.role, { role: r.value }); msg("um", "Perfil atualizado."); } catch (er) { msg("um", er.message, true); show(); } };
        pane.onclick = async e => { const rp = e.target.closest("[data-rp]"), du = e.target.closest("[data-du]");
          if (rp) { const pw = await PSDTW.confirmar({ titulo: `Redefinir a senha de ${rp.dataset.n}`, campo: { tipo: "password", rotulo: "Nova senha (mínimo 8 caracteres)", min: 8 }, botao: "Redefinir senha", icone: "settings" });
            if (pw) try { await put("/api/admin/users/" + rp.dataset.rp, { password: pw }); PSDTW.toast(`Senha de ${rp.dataset.n} redefinida.`); } catch (er) { PSDTW.erro(er); } }
          if (du && await PSDTW.confirmar({ titulo: `Remover o usuário ${du.dataset.n}?`, texto: "Ele deixa de entrar no sistema.", nota: "Não dá para desfazer: para voltar, cadastre o usuário de novo.", botao: "Remover", perigo: true }))
            try { await J("/api/admin/users/" + du.dataset.du, { method: "DELETE" }); PSDTW.toast(`Usuário ${du.dataset.n} removido.`); show(); } catch (er) { PSDTW.erro(er); } };
        const fn = $("#fn"); fn.onsubmit = async e => { e.preventDefault(); try { await post("/api/admin/users", Object.fromEntries(new FormData(fn))); show(); } catch (er) { msg("fnm", er.message, true); } };
      },
      regras() { const fr = $("#fr"); fr.onsubmit = async e => { e.preventDefault(); try { await put("/api/settings", Object.fromEntries(new FormData(fr))); msg("frm", "Regras salvas. Listas, contadores e metas já usam o novo critério."); } catch (er) { msg("frm", er.message, true); } }; },
      servidor() { servidor($("#srvpanel")); },
      backups() {
        $("#bk").onclick = async () => { $("#bk").disabled = true; try { await post("/api/backups"); show(); } catch (e) { $("#bk").disabled = false; msg("bkm", e.message, true); } };
        $$("[data-rs]").forEach(b => b.onclick = async () => {
          if (!await PSDTW.confirmar({ titulo: "Restaurar este backup?", texto: b.dataset.rs, nota: "O banco atual é substituído. Antes, um backup do estado atual é criado (dá para voltar por ele).", botao: "Restaurar", perigo: true, icone: "history" })) return;
          try { const r = await post("/api/backups/restore", { name: b.dataset.rs }); PSDTW.toast("Backup do estado anterior: " + r.safety, { titulo: "Banco restaurado", fixo: true }); show(); } catch (e) { PSDTW.erro(e); } });
      }
    };
    const show = async () => { const pane = $("#spane"); pane.onclick = pane.onchange = null; try { pane.innerHTML = await PANES[cur](); wire[cur](); } catch (e) { pane.innerHTML = notice(esc(e.message), "red"); } };
    $("#snav").onclick = e => { const b = e.target.closest("[data-s]"); if (!b) return; cur = b.dataset.s; history.replaceState(null, "", location.pathname + location.search + "#" + cur);
      $$("#snav [data-s]").forEach(x => { const on = x === b; x.setAttribute("aria-current", on); x.className = x.className.replace(/bg-blue-500\/10 text-blue-600|text-ink hover:bg-slate-500\/10/, on ? "bg-blue-500/10 text-blue-600" : "text-ink hover:bg-slate-500/10"); }); show(); };
    show();
  }
  PSD.tela("configuracoes", configuracoes);
})();
