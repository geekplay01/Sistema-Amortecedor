/* Tela · Metas & Validação — visual Tailwind (etapa 16 · B).
   Filtros na URL e lembrados (PSDTW.filtros): ano · tipo (DESENVOLVIMENTO / REDESENVOLVIMENTO; clicar de novo limpa) · «conta?» na lista de recebidos.
   Fontes: /api/goals (metas + validações), /api/goals/events?kind= (recebidos no ano), /api/validations/pending (R-D aguardando confirmação). */
(function () {
  const { $, esc, J, post, root, fail, dlg } = PSD;
  const TW = window.PSDTW, { nf, dmy, badge, kpi, card, notice, empty } = TW;
  const DES = "DESENVOLVIMENTO", RD = "REDESENVOLVIMENTO", TIPO = { des: DES, rd: RD }, SLUG = { [DES]: "des", [RD]: "rd" }, COR = { [DES]: "#2f6bff", [RD]: "#10b981" };
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500";
  const chip = (attrs, label, on) => `<button type="button" ${attrs} aria-pressed="${on}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${on ? "border-blue-500 bg-blue-500 text-white" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${label}</button>`;
  const LIMITE = 5000;                                       // recebidos no ano: lista inteira (contadores «conta?» exatos)
  const pct = p => p == null ? "–" : nf(p, 1) + "%";
  const put = (u, b) => J(u, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) });

  function metas() {
    const F = TW.filtros("metas", ["year", "tipo", "conta"]); let d = null, ev = null, pv = null, mexeu = false;
    root.innerHTML = `<div class="flex flex-col gap-5">
      <div id="mbar" class="flex flex-wrap items-center gap-2"></div>
      <p id="mtr" class="m-0 text-sm text-mute"></p>
      <div id="mx"></div>
      <div id="mg" class="grid grid-cols-1 gap-4 lg:grid-cols-2"></div>
      <div id="mevo"></div><div id="mev"></div><div id="mval"></div>
    </div>`;
    const tipos = () => { const t = TIPO[F.get().tipo]; return t ? [t] : [DES, RD]; };

    const desenharBarra = () => {
      const s = F.get();
      $("#mbar").innerHTML = `<label class="flex items-center gap-2 text-sm text-mute">Ano <select name="year" class="${campo}">${d.years.map(y => `<option ${y === d.year ? "selected" : ""}>${y}</option>`).join("")}</select></label>
        <span class="ml-2 mr-1 text-xs font-semibold uppercase tracking-wide text-mute">Tipo</span>
        ${chip("data-tipo-todos", "Todos", !s.tipo)}${chip('data-tg="tipo" data-v="des"', DES, s.tipo === "des")}${chip('data-tg="tipo" data-v="rd"', RD, s.tipo === "rd")}
        ${F.restaurado && !mexeu ? '<span class="ml-2 text-sm text-amber-700">filtros da última visita</span>' : ""}
        ${Object.keys(s).length ? `<button type="button" id="mclr" class="ml-auto rounded-lg border border-line bg-card px-3.5 py-2 text-sm font-semibold text-ink hover:bg-slate-500/10">Limpar filtros</button>` : ""}`;
      $("#mtr").textContent = d.tracking.since ? `Transições rastreadas desde ${dmy(d.tracking.since)} (${d.tracking.runs} sincronização(ões)). O que aconteceu antes entra em «já realizado antes do rastreio».` : "O rastreio começa na 1ª sincronização com o servidor.";
    };

    // validações do usuário (USER_VALID) no ano: KPIs e evolução mensal só dos tipos escolhidos
    const desenharValidacoes = () => {
      const v = d.validacoes || {}, g = d.goals, ks = tipos(), warn = [...(v.avisos || [])], u = esc(v.filtro?.USER_VALID || "ITALOC");
      if (v.sem_data) warn.push(`${v.sem_data} validação(ões) sem data de aprovação (não entram na evolução mensal)`);
      const kp = ks.map(k => kpi(k, nf(v[k]), g[k] ? `meta ${nf(g[k].target)} · ${pct(g[k].pct)} atingido` : "", k === DES ? "green" : "slate"));
      if (ks.length > 1) kp.unshift(kpi("Total de validações", nf(v.total), `${nf(v.linhas?.do_usuario_e_linha)} linhas de ${nf(v.linhas?.lidas)} lidas`, "blue"));
      $("#mx").innerHTML = `<section class="flex flex-col gap-4">
        <div><h3 class="m-0 text-lg font-semibold text-ink">Validações ${u} · ${d.year}</h3>
          <p class="m-0 mt-1 text-sm text-mute">USER_VALID = <b>${u}</b> · LINHA contém <b>${esc(v.filtro?.LINHA_contem || "AMORTECEDOR")}</b> · contagem por código distinto · tipo pela SUGESTÃO</p></div>
        <div class="grid grid-cols-1 gap-4 ${kp.length > 2 ? "md:grid-cols-3" : "md:grid-cols-2"}">${kp.join("")}</div>
        ${warn.length ? notice(warn.map(esc).join("<br>"), "amber") : ""}
        ${card("Validações por mês", '<div id="mxc" class="chart"></div>')}</section>`;
      const pm = v.por_mes || {}, ms = Object.keys(pm).sort();
      PSDCharts.bars($("#mxc"), { x: ms.length ? ms : [d.year + "-01"], series: ks.map(k => ({ name: k, y: ms.map(m => pm[m][k] || 0), color: COR[k] })), height: 240, labels: true });
    };

    const desenharMetas = () => {
      const ks = tipos(), u = esc(d.validacoes?.filtro?.USER_VALID || "ITALOC"), st = (n, l) => `<div class="rounded-xl bg-slate-500/10 px-3 py-2 text-center"><div class="text-xl font-bold tabular-nums text-ink">${n}</div><div class="text-xs text-mute">${l}</div></div>`;
      $("#mg").innerHTML = ks.map(k => {
        const g = d.goals[k], p = g.parts;
        const base = d.basis === "validacao" && k === RD ? `Validações ${u} no ano: <b class="text-ink">${nf(p.validacoes)}</b>${p.validacoes_sem_data ? ` · ${nf(p.validacoes_sem_data)} sem data de aprovação` : ""}.`
          : k === RD ? `Recebidos e validados no ano: <b class="text-ink">${nf(p.recebidos_validados)}</b>${p.recebidos_sem_validacao ? ` · <b class="text-ink">${nf(p.recebidos_sem_validacao)}</b> recebido(s) sem validação de usuário não contam.` : ""}`
          : `Recebidos e validados no ano: <b class="text-ink">${nf(p.recebidos_validados)}</b>${p.recebidos_sem_validacao ? ` · <b class="text-ink">${nf(p.recebidos_sem_validacao)}</b> recebido(s) sem validação não contam` : ""}${p.por_coluna_de_data ? ` · ${nf(p.por_coluna_de_data)} datado(s) pela coluna de status do servidor` : ""}.`;
        return card(`${k} ${g.reached ? badge("meta atingida", "green") : ""}`, `<div id="gg-${SLUG[k]}" class="chart"></div>
          <div class="mt-3 grid grid-cols-4 gap-2">${st(nf(g.target), "meta " + d.year)}${st(nf(g.done), "realizado")}${st(nf(g.missing), "faltam")}${st(pct(g.pct), "da meta")}</div>
          <div class="mt-3 flex flex-col gap-1.5 text-sm text-mute"><p class="m-0">Rastreado pelo sistema: <b class="text-ink">${nf(g.tracked)}</b> + já realizado antes do rastreio: <b class="text-ink">${nf(g.prior_done)}</b>${g.note ? ` · <i>${esc(g.note)}</i>` : ""}</p>
          <p class="m-0">${esc(d.rules[k])}</p><p class="m-0">${base}</p></div>`,
          `<button type="button" data-edit="${k}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-sm font-semibold text-ink hover:bg-slate-500/10">Editar meta</button>`, g.reached ? "ring-1 ring-emerald-500/50" : "");
      }).join("");
      ks.forEach(k => PSDCharts.gauge($("#gg-" + SLUG[k]), { value: d.goals[k].done, target: d.goals[k].target, title: "", subtitle: `realizado × meta ${d.goals[k].target}` }));
      $("#mevo").innerHTML = d.basis === "validacao" ? "" : card("Evolução mensal — itens recebidos", '<div id="mevoc" class="chart"></div>');
      if (d.basis !== "validacao") PSDCharts.bars($("#mevoc"), { x: d.goals[DES].series.main.map(m => m.month), series: ks.map(k => ({ name: k + (k === DES ? " · item recebido" : " · recebido e validado"), y: d.goals[k].series.main.map(m => m.n), color: COR[k] })), height: 250, labels: true });
    };

    // itens que chegaram a ITEM RECEBIDO no ano (já filtrados por tipo na API) + filtro «conta?» local
    const desenharEventos = () => {
      const s = F.get(), rows = ev.rows.filter(r => s.conta === "sim" ? r.counts : s.conta === "nao" ? !r.counts : true), n = ev.rows.filter(r => r.counts).length;
      const right = `<select name="conta" class="${campo}"><option value="">Conta? todos (${nf(ev.rows.length)})</option><option value="sim" ${s.conta === "sim" ? "selected" : ""}>Contam (${nf(n)})</option><option value="nao" ${s.conta === "nao" ? "selected" : ""}>Não contam (${nf(ev.rows.length - n)})</option></select>`;
      const aviso = d.basis === "validacao" && tipos().includes(RD) ? `<p class="m-0 mb-3 text-sm text-mute">Na base atual (validações), a meta de ${RD} soma as validações do ano, não estes recebimentos; para ${RD}, «Conta?» mostra a regra da base «item recebido».</p>` : "";
      $("#mev").innerHTML = card("Itens recebidos no ano e se contam", ev.rows.length ? aviso + TW.table([{ h: "Código" }, { h: "Tipo" }, { h: "Mudança" }, { h: "Data" }, { h: "Conta?", nw: false }],
        rows.map(r => [`<a href="#" class="font-semibold text-blue-600" data-rd="${SLUG[r.kind]}" data-code="${esc(r.code)}">${esc(r.code)}</a>`, badge(r.kind, r.kind === DES ? "blue" : "green"),
          `${esc(r.from_value || "—")} → <b>${esc(r.to_value)}</b>`, dmy(r.at), r.counts ? badge("conta", "green") : `${badge("não conta", "amber")} <span class="text-xs text-mute">${esc(r.why_not || "")}</span>`]), { h: "max-h-[50vh]" })
        + (ev.rows.length >= LIMITE ? `<p class="m-0 mt-2 text-xs text-mute">Mostrando os ${nf(LIMITE)} mais recentes.</p>` : "")
        : empty("Nenhum item chegou a ITEM RECEBIDO neste ano ainda (a data vem da sincronização diária ou da coluna de data de status do servidor)."), ev.rows.length ? right : "");
    };

    const desenharPendentes = () => {
      if (!tipos().includes(RD)) { $("#mval").innerHTML = ""; return; }
      $("#mval").innerHTML = card(`Validações — ${RD}`, `<p class="m-0 mb-3 text-sm text-mute">Itens em <b class="text-ink">PENDENTE CONFIRMAÇÃO</b> (Amortecedor): ${nf(pv.total)}, com validação enviada: <b class="text-ink">${nf(pv.sent)}</b>. Quando o servidor mostrar <b class="text-ink">ITEM RECEBIDO</b> e o item tiver a validação do usuário, ele entra na meta automaticamente.</p>` +
        (pv.rows.length ? TW.table([{ h: "Código" }, { h: "Descrição" }, { h: "Validação" }, { h: "" }], pv.rows.map(r => [`<a href="#" class="font-semibold text-blue-600" data-rd="rd" data-code="${esc(r.code)}">${esc(r.code)}</a>`,
          r.description ? `<span class="block max-w-[22rem] truncate" title="${esc(r.description)}">${esc(r.description)}</span>` : '<span class="text-mute">–</span>',
          r.sent_at ? `${badge("enviada em " + dmy(r.sent_at), "green")} <span class="text-xs text-mute">aguardando ITEM RECEBIDO</span>` : badge("não enviada", "amber"),
          r.sent_at ? "" : `<button type="button" data-vs="${esc(r.code)}" class="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700">Marcar enviada</button>`]), { h: "max-h-[50vh]" })
          : empty("Nenhum item de Redesenvolvimento aguardando confirmação.")));
    };

    const carregar = async () => {
      const s = F.get(), y = encodeURIComponent(s.year || ""), kind = s.tipo ? "&kind=" + s.tipo : "";
      try { [d, ev, pv] = await Promise.all([J("/api/goals?year=" + y), J(`/api/goals/events?year=${y}${kind}&limit=${LIMITE}`), J("/api/validations/pending")]); }
      catch (e) { return fail(e); }
      desenharBarra(); desenharValidacoes(); desenharMetas(); desenharEventos(); desenharPendentes();
    };
    const aplicar = patch => { mexeu = true; if (patch) F.set(patch); return carregar(); };

    root.addEventListener("change", e => {
      if (e.target.name === "year") aplicar({ year: e.target.value });
      if (e.target.name === "conta") { mexeu = true; F.set({ conta: e.target.value }); desenharBarra(); desenharEventos(); }
    });
    root.addEventListener("click", async e => {
      const tg = e.target.closest("[data-tg]"), todos = e.target.closest("[data-tipo-todos]"), ed = e.target.closest("[data-edit]"), vs = e.target.closest("[data-vs]");
      if (tg) { mexeu = true; F.toggle(tg.dataset.tg, tg.dataset.v); return carregar(); }
      if (todos) return aplicar({ tipo: "" });
      if (e.target.id === "mclr") { F.clear(); return aplicar(null); }
      if (vs) { vs.disabled = true; try { await post("/api/validations", { code: vs.dataset.vs, kind: RD }); await carregar(); } catch (er) { alert(er.message); vs.disabled = false; } }
      if (ed) editar(ed.dataset.edit);
    });

    const editar = k => {
      const g = d.goals[k], yr = d.year;
      dlg.innerHTML = `<div class="dh"><div><h2>Meta ${yr} — ${esc(k)}</h2></div><div><button class="btn ghost" data-close>Fechar</button></div></div>
        <div class="fgrid"><label>Meta do ano<input id="gt" type="number" min="0" value="${g.target}"></label><label>Já realizado antes do rastreio<input id="gp" type="number" min="0" value="${g.prior_done}"></label><label>Observação<input id="gn" value="${esc(g.note || "")}" placeholder="opcional"></label></div>
        <p class="muted">«Já realizado antes do rastreio» soma ao que o sistema contar a partir da 1ª sincronização (o servidor não guarda histórico).</p><p id="gm" class="imp-msg"></p><div class="acts"><button class="btn" id="gs">Salvar</button><button class="btn ghost" data-close>Cancelar</button></div>`;
      $("#gs", dlg).onclick = async () => {
        try { await put("/api/goals", { year: yr, kind: k, target: $("#gt", dlg).value, prior_done: $("#gp", dlg).value, note: $("#gn", dlg).value }); dlg.close(); carregar(); }
        catch (er) { $("#gm", dlg).textContent = er.message; $("#gm", dlg).className = "imp-msg err"; }
      };
      dlg.showModal();
    };
    carregar();
  }
  PSD.tela("metas", metas);
})();
