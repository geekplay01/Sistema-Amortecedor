/* Tela · Metas & Validação — visual Tailwind (etapa 16 · B).
   Filtros na URL e lembrados (PSDTW.filtros): ano · tipo (DESENVOLVIMENTO / REDESENVOLVIMENTO; clicar de novo limpa) · «conta?» na lista de recebidos · rdv (atalho da lista de validações R-D).
   Fontes: /api/goals (metas + validações), /api/goals/rd-validations (validações R-D do ano: contam ao chegar a ITEM RECEBIDO, etapa 16 · D5b),
   /api/goals/events?kind= (recebidos no ano; na base «validação» só DESENVOLVIMENTO), /api/validations/pending (R-D aguardando confirmação). */
(function () {
  const { $, esc, J, post, root, fail, dlg } = PSD;
  const TW = window.PSDTW, { nf, dmy, badge, kpi, card, notice, empty } = TW;
  const DES = "DESENVOLVIMENTO", RD = "REDESENVOLVIMENTO", TIPO = { des: DES, rd: RD }, SLUG = { [DES]: "des", [RD]: "rd" }, COR = { [DES]: "var(--chart-1)", [RD]: "var(--chart-2)" };   // DES azul, R-D laranja (DESIGN.md §6.6)
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500";
  const chip = (attrs, label, on) => `<button type="button" ${attrs} aria-pressed="${on}" class="psd-chip">${label}</button>`;      // etapa 19: mesmo visual da barra de filtros
  const LIMITE = 5000;                                       // recebidos no ano: lista inteira (contadores «conta?» exatos)
  const pct = p => p == null ? "–" : nf(p, 1) + "%";
  const put = (u, b) => J(u, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) });

  function metas() {
    const F = TW.filtros("metas", ["year", "tipo", "conta", "rdv", "mes", "vt"]); let d = null, ev = null, pv = null, rv = null;
    const MESN = ["", "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"], mesl = m => m ? `${MESN[+m.slice(5, 7)]}/${m.slice(2, 4)}` : "";
    root.innerHTML = `<div class="flex flex-col gap-5">
      <div id="mbar" class="flex flex-wrap items-center gap-2"></div>
      <p id="mtr" class="m-0 text-sm text-mute"></p>
      <div id="mx"></div>
      <div id="mg" class="grid grid-cols-1 gap-4 lg:grid-cols-2"></div>
      <div id="mevo"></div><div id="mrd"></div><div id="mev"></div><div id="mval"></div>
    </div>`;
    const tipos = () => { const t = TIPO[F.get().tipo]; return t ? [t] : [DES, RD]; };

    const desenharBarra = () => {
      const s = F.get();
      $("#mbar").innerHTML = `<label class="flex items-center gap-2 text-sm text-mute">Ano <select name="year" class="${campo}">${d.years.map(y => `<option ${y === d.year ? "selected" : ""}>${y}</option>`).join("")}</select></label>
        <span class="ml-2 mr-1 psd-rot">Tipo</span>
        ${chip("data-tipo-todos", "Todos", !s.tipo)}${chip('data-tg="tipo" data-v="des"', DES, s.tipo === "des")}${chip('data-tg="tipo" data-v="rd"', RD, s.tipo === "rd")}
        
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
        <div><h3 class="m-0 text-lg font-semibold text-ink">Validações ${u} em ${d.year}</h3></div>
        <div class="grid grid-cols-1 gap-4 ${kp.length > 2 ? "md:grid-cols-3" : "md:grid-cols-2"}">${kp.join("")}</div>
        ${warn.length ? notice(warn.map(esc).join("<br>"), "amber") : ""}
        ${card("Validações por mês", '<div id="mxc" class="chart"></div>', '<span class="text-xs text-mute">clique numa barra para ver as validações do mês</span>')}</section>`;
      const pm = v.por_mes || {}, ms = Object.keys(pm).sort();
      /* próximo update (26/11/2026): clicar numa barra filtra a lista de validações pelo mês e pelo tipo dela e rola até a lista */
      PSDCharts.bars($("#mxc"), { x: ms.length ? ms : [d.year + "-01"], series: ks.map(k => ({ name: k, y: ms.map(m => pm[m][k] || 0), color: COR[k] })), height: 240, labels: true }).then(g => { if (!g || !ms.length) return;
        g.options.onHover = (e, els) => { e.native.target.style.cursor = els.length ? "pointer" : "default"; };
        g.options.onClick = (e, els) => { const el = els[0]; if (!el) return; const k = ks[el.datasetIndex], m = ms[el.index], s = F.get();
          const mesmo = s.mes === m && s.vt === SLUG[k]; F.set({ mes: mesmo ? "" : m, vt: mesmo ? "" : SLUG[k], rdv: "" }); desenharBarra(); desenharRd();
          if (!mesmo) { const alvo = $("#mrd"); if (alvo) alvo.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" }); } }; });
    };

    const desenharMetas = () => {
      const ks = tipos(), u = esc(d.validacoes?.filtro?.USER_VALID || "ITALOC"), st = (n, l) => `<div class="rounded-xl bg-slate-500/10 px-3 py-2 text-center"><div class="text-xl font-bold tabular-nums text-ink">${n}</div><div class="text-xs text-mute">${l}</div></div>`;
      $("#mg").innerHTML = ks.map(k => {
        const g = d.goals[k], p = g.parts;
        const base = d.basis === "validacao" && k === RD ? `Validações ${u} no ano: <b class="text-ink">${nf(p.validacoes)}</b>, já em ITEM RECEBIDO (contam): <b class="text-ink">${nf(p.recebidas)}</b>, aguardando: <b class="text-ink">${nf(p.aguardando)}</b>${p.validacoes_sem_data ? `, ${nf(p.validacoes_sem_data)} sem data de aprovação` : ""}. A lista está abaixo.`
          : k === RD ? `Recebidos e validados no ano: <b class="text-ink">${nf(p.recebidos_validados)}</b>${p.recebidos_sem_validacao ? `, <b class="text-ink">${nf(p.recebidos_sem_validacao)}</b> recebido(s) sem validação de usuário não contam.` : ""}`
          : `Pedido confirmado → item recebido no ano: <b class="text-ink">${nf(p.recebidos)}</b>${p.sem_pedido_confirmado ? `, <b class="text-ink">${nf(p.sem_pedido_confirmado)}</b> recebido(s) sem passar por PEDIDO CONFIRMADO não contam` : ""} (data de recebimento do servidor).`;
        return card(`${k} ${g.reached ? badge("meta atingida", "green") : ""}`, `<div id="gg-${SLUG[k]}" class="chart"></div>
          <div class="mt-3 grid grid-cols-4 gap-2">${st(nf(g.target), "meta " + d.year)}${st(nf(g.done), "realizado")}${st(nf(g.missing), "faltam")}${st(pct(g.pct), "da meta")}</div>
          <div class="mt-3 flex flex-col gap-1.5 text-sm text-mute"><p class="m-0">${g.prior_aplica === false ? `Contado pelo servidor: <b class="text-ink">${nf(g.tracked)}</b> (sem itens de montadora)` : `Rastreado pelo sistema: <b class="text-ink">${nf(g.tracked)}</b> + já realizado antes do rastreio: <b class="text-ink">${nf(g.prior_done)}</b>`}${g.note ? `, <i>${esc(g.note)}</i>` : ""}</p>
          <p class="m-0">${base}</p></div>`,
          `<button type="button" data-edit="${k}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-sm font-semibold text-ink hover:bg-slate-500/10">Editar meta</button>`, g.reached ? "ring-1 ring-emerald-500/50" : "");
      }).join("");
      ks.forEach(k => PSDCharts.gauge($("#gg-" + SLUG[k]), { value: d.goals[k].done, target: d.goals[k].target, title: "", year: d.year }));          // anel com o ritmo do ano (update 5)
      $("#mevo").innerHTML = d.basis === "validacao" ? "" : card("Evolução mensal — itens recebidos", '<div id="mevoc" class="chart"></div>');
      if (d.basis !== "validacao") PSDCharts.bars($("#mevoc"), { x: d.goals[DES].series.main.map(m => m.month), series: ks.map(k => ({ name: k + (k === DES ? ": item recebido" : ": recebido e validado"), y: d.goals[k].series.main.map(m => m.n), color: COR[k] })), height: 250, labels: true });
    };

    // itens que chegaram a ITEM RECEBIDO no ano (já filtrados por tipo na API) + filtro «conta?» local
    // validações R-D do ano (base «validação»): todas, com status atual e controles; conta quando chegar a ITEM RECEBIDO (goals.rd_validations)
    // próximo update: DES e R-D numa lista só (goals.validacoes_ano); mês e tipo vêm do clique no gráfico; os atalhos de «conta?» valem para o R-D (base «validação»)
    const RDF = { todas: "Todas", contam: "Contam (ITEM RECEBIDO)", aguardando: "Aguardando ITEM RECEBIDO", pend_validacao_qual: "Pend. validação qualidade", val_reprovada: "Validação reprovada" };
    const desenharRd = () => {
      if (!rv) { $("#mrd").innerHTML = ""; return; }
      const f = F.get(), s = f.rdv || "todas", vb = d.basis === "validacao";
      const ks = tipos().filter(k => !f.vt || SLUG[k] === f.vt);
      const base = rv.rows.filter(r => ks.includes(r.kind) && (!f.mes || (r.meses || []).includes(f.mes)));
      const ok = r => s === "todas" ? true : r.kind !== RD ? false : s === "contam" ? r.counts : s === "aguardando" ? !r.counts : r.flags.includes(s), rows = base.filter(ok);
      const rd = base.filter(r => r.kind === RD), c = { todas: base.length, contam: rd.filter(r => r.counts).length, aguardando: rd.filter(r => !r.counts).length,
        pend_validacao_qual: rd.filter(r => r.flags.includes("pend_validacao_qual")).length, val_reprovada: rd.filter(r => r.flags.includes("val_reprovada")).length };
      const misto = rd.length < base.length;          // lista com DES e R-D: os atalhos de «conta?» dizem que são do R-D
      const chips = vb && rd.length ? Object.entries(RDF).filter(([k]) => k === "todas" || c[k] || s === k).map(([k, l]) => chip(`data-rdv="${k}"`, `${misto && k !== "todas" ? "R-D: " : ""}${l} ${nf(c[k])}`, s === k)).join("") : "";
      const etq = [f.mes ? `<span class="psd-tag">Mês: ${mesl(f.mes)}<button type="button" data-tira-mes aria-label="Tirar o filtro de mês">${TW.ico("x", "sm")}</button></span>` : "",
                   f.vt ? `<span class="psd-tag">Tipo: ${TIPO[f.vt]}<button type="button" data-tira-vt aria-label="Tirar o filtro de tipo">${TW.ico("x", "sm")}</button></span>` : ""].join("");
      const outros = r => (r.meses || []).length > 1 ? ` <span class="text-xs text-mute">também em ${esc(r.meses.filter(m => m !== (r.valid_at || "").slice(0, 7)).map(mesl).join(", "))}</span>` : "";
      $("#mrd").innerHTML = card(`Validações item a item`, `${etq || chips ? `<div class="mb-3 flex flex-wrap items-center gap-2">${etq}${chips}</div>` : ""}`
        + (rows.length ? TW.table([{ h: "Código" }, { h: "Tipo" }, { h: "Descrição" }, { h: "Validado em" }, { h: "Status atual" }, { h: "Controle de status", nw: false }, { h: "Recebido em" }, { h: "Conta?" }],
            rows.map(r => [`<a href="#" class="font-semibold text-blue-600" data-rd="${SLUG[r.kind]}" data-code="${esc(r.code)}">${esc(r.code)}</a>`, badge(r.kind === DES ? "DES" : "R-D", r.kind === DES ? "blue" : "amber"),
              r.description ? `<span class="block max-w-[18rem] truncate" title="${esc(r.description)}">${esc(r.description)}</span>` : "–",
              dmy(r.valid_at) + outros(r),
              r.status ? badge(r.status, r.counts ? "green" : "slate") : "–", r.flags.length ? `<div class="flex min-w-[10rem] flex-wrap gap-1">${PSD.flagChips(r.flags)}</div>` : "–",
              r.received_at ? dmy(r.received_at) : "–", r.kind !== RD || !vb ? '<span class="text-mute">–</span>' : r.counts ? badge("conta", "green") : badge("aguardando", "amber")]), { h: "max-h-[55vh]" })
          : empty("Nenhuma validação com este filtro.")), `<span class="text-sm text-mute">${nf(rows.length)} validação(ões)</span>`);
    };

    const desenharEventos = () => {
      const s = F.get(), soDes = d.basis === "validacao", base = soDes ? ev.rows.filter(r => r.kind === DES) : ev.rows;       // base «validação»: R-D tem a lista própria (validações do ano)
      if (soDes && !tipos().includes(DES)) { $("#mev").innerHTML = ""; return; }
      const rows = base.filter(r => s.conta === "sim" ? r.counts : s.conta === "nao" ? !r.counts : true), n = base.filter(r => r.counts).length;
      const right = `<select name="conta" class="${campo}"><option value="">Conta? todos (${nf(base.length)})</option><option value="sim" ${s.conta === "sim" ? "selected" : ""}>Contam (${nf(n)})</option><option value="nao" ${s.conta === "nao" ? "selected" : ""}>Não contam (${nf(base.length - n)})</option></select>`;
      ev = { ...ev, rows: base };
      $("#mev").innerHTML = card(soDes ? `Itens ${DES} recebidos no ano e se contam` : "Itens recebidos no ano e se contam", ev.rows.length ? TW.table([{ h: "Código" }, { h: "Tipo" }, { h: "Mudança" }, { h: "Data" }, { h: "Conta?", nw: false }],
        rows.map(r => [`<a href="#" class="font-semibold text-blue-600" data-rd="${SLUG[r.kind]}" data-code="${esc(r.code)}">${esc(r.code)}</a>`, badge(r.kind, r.kind === DES ? "blue" : "green"),
          `${esc(r.from_value || "—")} → <b>${esc(r.to_value)}</b>`, dmy(r.at), r.counts ? badge("conta", "green") : `${badge("não conta", "amber")} <span class="text-xs text-mute">${esc(r.why_not || "")}</span>`]), { h: "max-h-[50vh]" })
        + (ev.rows.length >= LIMITE ? `<p class="m-0 mt-2 text-xs text-mute">Mostrando os ${nf(LIMITE)} mais recentes.</p>` : "")
        : empty("Nenhum item chegou a ITEM RECEBIDO neste ano ainda (a data vem da sincronização diária ou da coluna de data de status do servidor)."), ev.rows.length ? right : "");
    };

    const desenharPendentes = () => {
      if (!tipos().includes(RD)) { $("#mval").innerHTML = ""; return; }
      $("#mval").innerHTML = card(`Validações — ${RD}`, `<p class="m-0 mb-3 text-sm text-mute">Itens em <b class="text-ink">PENDENTE CONFIRMAÇÃO</b> (Amortecedor): ${nf(pv.total)}, com validação enviada: <b class="text-ink">${nf(pv.sent)}</b>.</p>` +
        (pv.rows.length ? TW.table([{ h: "Código" }, { h: "Descrição" }, { h: "Validação" }, { h: "" }], pv.rows.map(r => [`<a href="#" class="font-semibold text-blue-600" data-rd="rd" data-code="${esc(r.code)}">${esc(r.code)}</a>`,
          r.description ? `<span class="block max-w-[22rem] truncate" title="${esc(r.description)}">${esc(r.description)}</span>` : '<span class="text-mute">–</span>',
          r.sent_at ? `${badge("enviada em " + dmy(r.sent_at), "green")} <span class="text-xs text-mute">aguardando ITEM RECEBIDO</span>` : badge("não enviada", "amber"),
          r.sent_at ? "" : `<button type="button" data-vs="${esc(r.code)}" class="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-700">Marcar enviada</button>`]), { h: "max-h-[50vh]" })
          : empty("Nenhum item de Redesenvolvimento aguardando confirmação.")));
    };

    const carregar = async () => {
      const s = F.get(), y = encodeURIComponent(s.year || ""), kind = s.tipo ? "&kind=" + s.tipo : "";
      try { [d, ev, pv, rv] = await Promise.all([J("/api/goals?year=" + y), J(`/api/goals/events?year=${y}${kind}&limit=${LIMITE}`), J("/api/validations/pending"), J("/api/goals/validacoes?year=" + y)]); }
      catch (e) { return fail(e); }
      desenharBarra(); desenharValidacoes(); desenharMetas(); desenharRd(); desenharEventos(); desenharPendentes();
    };
    const aplicar = patch => { if (patch) F.set(patch); return carregar(); };

    root.addEventListener("change", e => {
      if (e.target.name === "year") aplicar({ year: e.target.value });
      if (e.target.name === "conta") { F.set({ conta: e.target.value }); desenharBarra(); desenharEventos(); }
    });
    root.addEventListener("click", async e => {
      const tg = e.target.closest("[data-tg]"), todos = e.target.closest("[data-tipo-todos]"), ed = e.target.closest("[data-edit]"), vs = e.target.closest("[data-vs]"), rdv = e.target.closest("[data-rdv]");
      if (rdv) { F.set({ rdv: rdv.dataset.rdv === "todas" ? "" : rdv.dataset.rdv }); desenharBarra(); return desenharRd(); }
      if (e.target.closest("[data-tira-mes]")) { F.set({ mes: "" }); desenharBarra(); return desenharRd(); }
      if (e.target.closest("[data-tira-vt]")) { F.set({ vt: "" }); desenharBarra(); return desenharRd(); }
      if (tg) { F.toggle(tg.dataset.tg, tg.dataset.v); return carregar(); }
      if (todos) return aplicar({ tipo: "" });
      if (e.target.id === "mclr") { F.clear(); return aplicar(null); }
      if (vs) { vs.disabled = true; try { await post("/api/validations", { code: vs.dataset.vs, kind: RD }); await carregar(); } catch (er) { PSDTW.erro(er); vs.disabled = false; } }
      if (ed) editar(ed.dataset.edit);
    });

    const editar = k => {
      const g = d.goals[k], yr = d.year;
      dlg.innerHTML = `<div class="dh"><div><h2>Meta ${yr} — ${esc(k)}</h2></div><div><button class="btn ghost" data-close>Fechar</button></div></div>
        <div class="fgrid"><label>Meta do ano<input id="gt" type="number" min="0" value="${g.target}"></label>${g.prior_aplica === false ? "" : `<label>Já realizado antes do rastreio<input id="gp" type="number" min="0" value="${g.prior_done}"></label>`}<label>Observação<input id="gn" value="${esc(g.note || "")}" placeholder="opcional"></label></div>
        <p class="muted">${g.prior_aplica === false ? "Desenvolvimento vem inteiro do servidor (pedido confirmado → item recebido no ano, pela data de recebimento): não há «já realizado antes do rastreio»." : "«Já realizado antes do rastreio» soma ao que o sistema contar a partir da 1ª sincronização (o servidor não guarda histórico)."}</p><p id="gm" class="imp-msg"></p><div class="acts"><button class="btn" id="gs">Salvar</button><button class="btn ghost" data-close>Cancelar</button></div>`;
      $("#gs", dlg).onclick = async () => {
        try { await put("/api/goals", { year: yr, kind: k, target: $("#gt", dlg).value, prior_done: $("#gp", dlg) ? $("#gp", dlg).value : "", note: $("#gn", dlg).value }); dlg.close(); carregar(); }
        catch (er) { $("#gm", dlg).textContent = er.message; $("#gm", dlg).className = "imp-msg err"; }
      };
      dlg.showModal();
    };
    carregar();
  }
  PSD.tela("metas", metas);
})();
