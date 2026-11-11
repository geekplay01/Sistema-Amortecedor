/* Telas novas: Dashboard (gráficos), Metas e validações, painel do servidor e busca de preços.
   Carregado antes do core.js; recebe os utilitários dele (window.PSD_NEW(ctx)). */
window.PSD_NEW = ctx => {
  const { J, post, $, $$, esc, num, tag, T, clip, empty, fail, dlg, qs, dmy, root, FLG, FGROUPS } = ctx;
  const put = (u, b) => J(u, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) });
  const brl = v => v == null ? "–" : Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  const when = s => s ? `${dmy(s)} ${String(s).slice(11, 16)}`.trim() : "–";
  const MON = ["", "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
  const DES = "DESENVOLVIMENTO", RD = "REDESENVOLVIMENTO";
  const panel = (title, body, cls = "", extra = "") => `<section class="dpanel ${cls}"><header><h3>${title}</h3>${extra}</header>${body}</section>`;
  const note = (t, cls = "") => `<div class="notice ${cls}">${t}</div>`;

  // ───────────────────────── Dashboard ─────────────────────────
  async function dashboard() {
    root.innerHTML = `<div id="dbanner"></div><div class="dash-grid" id="dgrid"><p class="muted">Carregando indicadores…</p></div>`;
    let d; try { d = await J("/api/dashboard"); } catch (e) { return fail(e); }
    const g = d.goals.goals, ps = d.pipeline, tr = d.tracking, none = a => `<div class="ch-empty">${a}</div>`;
    const bn = [];
    if (!ps.configured) bn.push(note("<b>Servidor SQL não configurado.</b> Abra o arquivo <code>.env</code> (copie o <code>.env.example</code>), preencha <code>DEV_DB_PASSWORD</code> e reinicie. Enquanto isso o sistema usa os dados já gravados.", "warn"));
    else if (!ps.last_ok_at) bn.push(note("<b>Nenhuma sincronização com o servidor ainda.</b> Clique em <b>Sincronizar</b> no topo da tela para trazer Desenvolvimento, Redesenvolvimento, compras, vendas e estoque.", "warn"));
    if (ps.last_status === "erro" && ps.last_error) bn.push(note(`<b>A última sincronização falhou:</b> ${esc(ps.last_error)}`, "err"));
    $("#dbanner").innerHTML = bn.join("");
    $("#dgrid").innerHTML = [
      panel("Metas " + d.goals.year, `<div class="gauges"><div id="g-des"></div><div id="g-rd"></div></div><div class="pfoot"><a class="btn ghost sm" href="/metas">Detalhes e validações</a><small class="muted">${tr.since ? "Rastreio de transições desde " + dmy(tr.since) : "Rastreio começa na 1ª sincronização"}</small></div>`, "span2"),
      panel("Evolução mensal das metas", '<div id="c-evo" class="chart"></div>', "span2"),
      panel("Funil — " + DES, '<div id="c-fun-des" class="chart"></div>'), panel("Funil — " + RD, '<div id="c-fun-rd" class="chart"></div>'),
      panel("Pendências por status", `<div class="seg sm" id="pk"><button type="button" data-k="${DES}" class="on">${DES}</button><button type="button" data-k="${RD}">${RD}</button></div><div id="c-flags" class="chart"></div>`, "span2"),
      panel("Vendas — últimos 12 meses", '<div id="c-sales" class="chart"></div>'), panel("Mais vendidos (12 meses)", '<div id="c-top" class="chart"></div>'),
      panel("Estoque disponível", '<div id="c-stock"></div>'), panel("Sistema: Gás × Óleo", '<div id="c-sys" class="chart"></div>')].join("");
    // metas
    const gg = (id, k, sub) => PSDCharts.gauge($(id), { value: g[k].done, target: g[k].target, title: k, subtitle: sub });
    const vb = d.goals.basis === "validacao"; gg("#g-des", DES, vb ? `meta ${g[DES].target} · validações ${d.goals.validacoes.filtro.USER_VALID} em ${d.goals.year}` : `meta ${g[DES].target} · item recebido em ${d.goals.year}`); gg("#g-rd", RD, vb ? `meta ${g[RD].target} · validações ${d.goals.validacoes.filtro.USER_VALID} em ${d.goals.year}` : `meta ${g[RD].target} · recebido e validado (${d.goals.validacoes.filtro.USER_VALID})`);
    const x = g[DES].series.main.map(m => m.month), bs = d.goals.basis === "validacao" ? "validações ITALOC" : "item recebido";
    PSDCharts.line($("#c-evo"), { x, series: [{ name: DES + " · " + bs, y: g[DES].series.main.map(m => m.n), color: "#2f6bff" }, { name: RD + " · " + bs, y: g[RD].series.main.map(m => m.n), color: "#10b981" }], height: 260 });
    // funis
    const fun = (id, k) => { const f = d.funnel[k]; f.length ? PSDCharts.funnel($(id), { labels: f.map(r => r.status), values: f.map(r => r.n) }) : ($(id).innerHTML = none("Sem itens ainda. Sincronize com o servidor.")); };
    fun("#c-fun-des", DES); fun("#c-fun-rd", RD);
    // pendências por status
    const flags = k => { const f = d.flags[k], rows = d.groups.defs.filter(s => f[s.key]).map(s => [s.label, f[s.key]]).sort((a, b) => b[1] - a[1]); rows.length ? PSDCharts.hbars($("#c-flags"), { labels: rows.map(r => r[0]), values: rows.map(r => r[1]), color: "#64748b" }) : ($("#c-flags").innerHTML = none("Nenhuma pendência de status.")); };
    flags(DES); $("#pk").onclick = e => { const b = e.target.closest("[data-k]"); if (!b) return; $$("#pk button").forEach(x => x.classList.toggle("on", x === b)); flags(b.dataset.k); };
    // vendas e estoque
    const s = d.sales;
    if (s.available) {
      PSDCharts.bars($("#c-sales"), { x: s.months.map(m => m.month), series: [{ name: "Quantidade vendida", y: s.months.map(m => m.qty), color: "#2f6bff" }], height: 250 });
      s.top.length ? PSDCharts.hbars($("#c-top"), { labels: s.top.map(t => `${t.code}${t.description ? " · " + t.description : ""}`), values: s.top.map(t => t.value || t.qty), color: "#10b981" }) : ($("#c-top").innerHTML = none("Sem vendas no período."));
    } else { $("#c-sales").innerHTML = $("#c-top").innerHTML = none("Vendas ainda não chegaram do servidor (PEDIDOS_VENDA_DETALHADO). Sincronize ou rode <code>python data_pipeline.py probe</code> para conferir as colunas."); }
    const st = d.stock; $("#c-stock").innerHTML = st.available ? `<div class="kpis"><div><span class="num">${num(st.qty)}</span><small>peças disponíveis</small></div><div><span class="num">${num(st.items)}</span><small>códigos em estoque</small></div><div><span class="num">${num(st.zero)}</span><small>zerados</small></div></div>` : none("Estoque ainda não chegou do servidor (EST DISP).");
    const sys = d.system, lab = { gas: "Gás", oleo: "Óleo", nd: "Sem dado" }; PSDCharts.donut($("#c-sys"), { labels: sys.map(r => lab[r.s] || r.s), values: sys.map(r => r.n), colors: ["#2f6bff", "#10b981", "#94a3b8"] });
  }

  // ───────────────────────── Metas e validações ─────────────────────────
  async function metas() {
    const year0 = new URLSearchParams(location.search).get("year") || "";
    root.innerHTML = `<div class="toolbar"><label class="inl">Ano <select id="my"></select></label><span class="muted" id="mtr"></span></div><div id="mx"></div><div id="mg" class="goal-grid"></div><div id="mevo"></div><div class="two"><div id="mev"></div><div id="mval"></div></div>`;
    const load = async yr => {
      let d, ev, pv; try { [d, ev, pv] = await Promise.all([J("/api/goals?year=" + (yr || "")), J("/api/goals/events?year=" + (yr || "")), J("/api/validations/pending")]); } catch (e) { return fail(e); }
      $("#mx").innerHTML = PSDTW.validationBlock(d); { const pm = d.validacoes.por_mes, ks = Object.keys(pm).sort(); PSDCharts.bars($("#mxc"), { x: ks.length ? ks : [d.year + "-01"], series: [{ name: DES, y: ks.map(k => pm[k][DES] || 0), color: "#2f6bff" }, { name: RD, y: ks.map(k => pm[k][RD] || 0), color: "#10b981" }], height: 240, labels: true }); }
      $("#my").innerHTML = d.years.map(y => `<option ${y === d.year ? "selected" : ""}>${y}</option>`).join("");
      $("#mtr").textContent = d.tracking.since ? `Transições rastreadas desde ${dmy(d.tracking.since)} (${d.tracking.runs} sincronização(ões)). O que aconteceu antes entra em «já realizado antes do rastreio».` : "O rastreio começa na 1ª sincronização com o servidor.";
      $("#mg").innerHTML = [DES, RD].map(k => { const g = d.goals[k], p = g.parts; return `<section class="dpanel goalcard ${g.reached ? "ok" : ""}"><header><h3>${k}</h3><button class="btn ghost sm" data-edit="${k}">Editar meta</button></header><div id="gg-${k}" class="chart"></div>
        <div class="gstats"><div><b>${g.target}</b><small>meta ${d.year}</small></div><div><b>${g.done}</b><small>realizado</small></div><div><b>${g.missing}</b><small>faltam</small></div><div><b>${g.pct == null ? "–" : g.pct + "%"}</b><small>da meta</small></div></div>
        <p class="muted gline">Rastreado pelo sistema: <b>${g.tracked}</b> + já realizado antes do rastreio: <b>${g.prior_done}</b>${g.note ? ` · <i>${esc(g.note)}</i>` : ""}</p>
        <p class="muted gline">${esc(d.rules[k])}</p>
        <p class="muted gline">${d.basis === "validacao" ? `Validações ${esc(d.validacoes.filtro.USER_VALID)} no ano: <b>${p.validacoes}</b>${p.validacoes_sem_data ? ` · ${p.validacoes_sem_data} sem data de aprovação` : ""}.` : k === RD ? `Recebidos e validados no ano: <b>${p.recebidos_validados}</b>${p.recebidos_sem_validacao ? ` · <b>${p.recebidos_sem_validacao}</b> recebido(s) sem validação de usuário não contam.` : ""}` : `Recebidos no ano: <b>${p.recebidos_no_ano}</b>${p.por_coluna_de_data ? ` (<b>${p.por_coluna_de_data}</b> datados pela coluna de status do servidor)` : ""}.`}</p></section>`; }).join("");
      [DES, RD].forEach(k => PSDCharts.gauge($("#gg-" + k), { value: d.goals[k].done, target: d.goals[k].target, title: "", subtitle: `realizado × meta ${d.goals[k].target}` }));
      $("#mevo").innerHTML = d.basis === "validacao" ? "" : panel("Evolução mensal — itens recebidos", '<div id="mevoc" class="chart"></div>');
      if (d.basis !== "validacao") PSDCharts.bars($("#mevoc"), { x: d.goals[DES].series.main.map(m => m.month), series: [{ name: DES + " · item recebido", y: d.goals[DES].series.main.map(m => m.n), color: "#2f6bff" }, { name: RD + " · recebido e validado", y: d.goals[RD].series.main.map(m => m.n), color: "#10b981" }], height: 250, labels: true });
      $("#mev").innerHTML = panel("Itens recebidos no ano e se contam", ev.rows.length ? T(["Código", "Tipo", "Mudança", "Data", "Conta?"], ev.rows.slice(0, 25).map(r => `<tr><td><a href="#" data-rd="${r.kind === RD ? "rd" : "des"}" data-code="${esc(r.code)}">${esc(r.code)}</a></td><td>${tag(r.kind)}</td><td>${esc(r.from_value || "—")} → <b>${esc(r.to_value)}</b></td><td>${dmy(r.at)}</td><td>${r.counts ? '<span class="badge ok">conta</span>' : `<span class="badge warn" title="${esc(r.why_not || "")}">não conta</span> <small class="muted">${esc(r.why_not || "")}</small>`}</td></tr>`)) : empty("Nenhum item chegou a ITEM RECEBIDO neste ano ainda (a data vem da sincronização diária ou da coluna de data de status do servidor)."));
      $("#mval").innerHTML = panel(`Validações — ${RD}`, `<p class="muted">Itens em <b>PENDENTE CONFIRMAÇÃO</b> (Amortecedor): ${pv.total}, com validação enviada: <b>${pv.sent}</b>. Quando o servidor mostrar <b>ITEM RECEBIDO</b> e o item tiver a validação do usuário ITALOC, ele entra na meta automaticamente.</p>` + (pv.rows.length ? T(["Código", "Descrição", "Validação", ""], pv.rows.slice(0, 40).map(r => `<tr><td><a href="#" data-rd="rd" data-code="${esc(r.code)}">${esc(r.code)}</a></td><td>${clip(r.description)}</td><td>${r.sent_at ? `<span class="badge ok">enviada em ${dmy(r.sent_at)}</span> <small class="muted">aguardando ITEM RECEBIDO</small>` : '<span class="badge warn">não enviada</span>'}</td><td>${r.sent_at ? "" : `<button class="btn sm" data-vs="${esc(r.code)}">Marcar enviada</button>`}</td></tr>`)) : empty("Nenhum item de Redesenvolvimento aguardando confirmação.")));
    };
    $("#my").onchange = e => load(e.target.value);
    root.addEventListener("click", async e => {
      const ed = e.target.closest("[data-edit]"), vs = e.target.closest("[data-vs]");
      if (vs) { try { await post("/api/validations", { code: vs.dataset.vs, kind: RD }); load($("#my").value); } catch (er) { alert(er.message); } }
      if (ed) { const k = ed.dataset.edit, yr = $("#my").value, d = await J("/api/goals?year=" + yr), g = d.goals[k];
        dlg.innerHTML = `<div class="dh"><div><h2>Meta ${yr} — ${k}</h2></div><div><button class="btn ghost" data-close>Fechar</button></div></div><div class="fgrid"><label>Meta do ano<input id="gt" type="number" min="0" value="${g.target}"></label><label>Já realizado antes do rastreio<input id="gp" type="number" min="0" value="${g.prior_done}"></label><label>Observação<input id="gn" value="${esc(g.note || "")}" placeholder="opcional"></label></div>
          <p class="muted">«Já realizado antes do rastreio» soma ao que o sistema contar a partir da 1ª sincronização (o servidor não guarda histórico).</p><p id="gm" class="imp-msg"></p><div class="acts"><button class="btn" id="gs">Salvar</button><button class="btn ghost" data-close>Cancelar</button></div>`;
        $("#gs").onclick = async () => { try { await put("/api/goals", { year: yr, kind: k, target: $("#gt").value, prior_done: $("#gp").value, note: $("#gn").value }); dlg.close(); load(yr); } catch (er) { $("#gm").textContent = er.message; $("#gm").className = "imp-msg err"; } }; dlg.showModal(); }
    });
    load(year0);
  }

  // ───────────────────────── Painel do servidor (Configurações) ─────────────────────────
  async function serverPanel(host) {
    host.innerHTML = '<p class="muted">Consultando o servidor…</p>';
    const draw = async () => {
      let st, rn; try { [st, rn] = await Promise.all([J("/api/pipeline/status"), J("/api/pipeline/runs")]); } catch (e) { host.innerHTML = note(esc(e.message), "err"); return; }
      const ok = st.last_status === "ok", drv = st.drivers.length ? st.drivers.map(d => `<span class="chip ok">${d}</span>`).join(" ") : '<span class="chip warn">nenhum (rode o iniciar.bat novamente)</span>';
      host.innerHTML = `<section class="dpanel srv"><header><h3>Servidor SQL — ${esc(st.host)}</h3><button class="btn" id="srvgo" ${st.running || !st.configured ? "disabled" : ""}>${st.running ? "Sincronizando…" : "Sincronizar agora"}</button></header>
        <div class="srv-grid"><div><small>Credenciais (.env)</small><b>${st.configured ? "✔ preenchidas" : "✖ faltam usuário/senha"}</b></div><div><small>Drivers</small><b>${drv}</b></div><div><small>Última sincronização</small><b>${st.last_ok_at ? when(st.last_ok_at) : "nunca"}</b></div><div><small>Itens no servidor</small><b>${num(st.items)}</b></div><div><small>Sincronizações feitas</small><b>${st.runs}</b></div><div><small>Agendamento</small><b>diário (DEV_SYNC_HOURS)</b></div></div>
        ${st.last_status === "erro" ? note(`<b>Última tentativa falhou:</b> ${esc(st.last_error || "")}`, "err") : ""}
        ${rn.tracking.since ? `<p class="muted">O servidor só guarda o status atual: o sistema grava um <b>snapshot a cada sincronização</b> (marco zero em ${dmy(rn.tracking.since)}) e detecta as mudanças de status a partir dele.</p>` : ""}
        <h4>Últimas sincronizações</h4>${rn.runs.length ? T(["#", "Início", "Fim", "Resultado", "Linhas", "Itens", "Eventos", "Novos", "Ausentes", "Avisos"], rn.runs.map(r => `<tr><td>${r.id}</td><td>${when(r.started_at)}</td><td>${when(r.finished_at)}</td><td>${r.status === "ok" ? `<span class="badge ok">${r.baseline ? "marco zero" : "ok"}</span>` : `<span class="badge bad" title="${esc(r.error || "")}">erro</span>`}</td><td>${num(r.source_rows)}</td><td>${num(r.items)}</td><td>${num(r.events)}</td><td>${num(r.new_items)}</td><td>${num(r.removed_items)}</td><td>${warnTxt(r)}</td></tr>`)) : '<p class="muted">Nenhuma ainda.</p>'}
        ${rn.datasets.length ? `<h4>Compras, vendas e estoque</h4>` + T(["Conjunto", "Objeto no servidor", "Linhas", "Resultado", "Quando", "Observação"], rn.datasets.map(r => `<tr><td>${esc(r.dataset)}</td><td>${esc(r.object || "")}</td><td>${num(r.rows)}</td><td><span class="badge ${r.status === "ok" ? "ok" : "warn"}">${esc(r.status)}</span></td><td>${when(r.at)}</td><td>${esc(r.note || "")}</td></tr>`)) : ""}</section>`;
      const b = $("#srvgo"); if (b) b.onclick = async () => { b.disabled = true; b.textContent = "Sincronizando…"; try { await post("/api/pipeline/sync"); window.psdSyncPoll && window.psdSyncPoll(draw); } catch (e) { alert(e.message); draw(); } };
    };
    const warnTxt = r => { try { const w = JSON.parse(r.warnings || "{}"); const k = Object.keys(w); return k.length ? `<span class="muted" title="${esc(JSON.stringify(w))}">${k.length} aviso(s)</span>` : "–"; } catch (e) { return "–"; } };
    draw();
  }

  // ───────────────────────── Busca de preços (Compra de amostras) ─────────────────────────
  function priceSearch(host, o = {}) {
    let refs = [...(o.refs || [])]; const sig = () => refs.map(r => `${r.brand || ""}|${r.code}`).join(",");
    const render = () => {
      host.innerHTML = `<div class="psearch"><div class="ps-h"><b><svg viewBox="0 0 24 24" width="16" height="16"><circle cx="11" cy="11" r="6"/><path d="M20 20l-4-4"/></svg> Buscar preço na web</b><small class="muted">sempre o menor preço · produto novo · unitário ou par/kit</small></div>
        <div class="ps-refs">${refs.length ? refs.map((r, i) => `<label class="ps-chip"><input type="checkbox" data-i="${i}" ${r.on ? "checked" : ""}><span><b>${esc(r.brand || "")}</b> ${esc(r.code)}</span></label>`).join("") : '<span class="muted">Sem referência cruzada para este código — digite um código abaixo.</span>'}
          <span class="ps-add"><input id="ps-code" placeholder="outro código (ex.: 16470)" size="18"><input id="ps-brand" placeholder="marca" size="10"><button type="button" class="btn ghost sm" id="ps-plus">+</button></span></div>
        <div class="ps-act"><label class="inl"><input type="checkbox" id="ps-strict" checked> priorizar anúncios que citam o código</label><button type="button" class="btn sm" id="ps-go">Buscar preços</button></div><div class="ps-res" id="ps-res"></div></div>`;
      host.onchange = e => { const c = e.target.closest("[data-i]"); if (c) refs[+c.dataset.i].on = c.checked; };
      $("#ps-plus", host).onclick = () => { const c = $("#ps-code", host).value.trim(); if (!c) return; refs.push({ brand: $("#ps-brand", host).value.trim().toUpperCase(), code: c, on: true }); render(); };
      $("#ps-go", host).onclick = go;
    };
    const go = async () => {
      const sel = refs.filter(r => r.on); const out = $("#ps-res", host);
      if (!sel.length) { out.innerHTML = note("Marque ao menos uma referência para buscar.", "warn"); return; }
      out.innerHTML = '<p class="muted">Buscando… (pode levar alguns segundos)</p>'; $("#ps-go", host).disabled = true;
      try {
        const d = await post("/api/prices/search", { refs: sel.map(r => ({ brand: r.brand, code: r.code })), limit: 5, strict: $("#ps-strict", host).checked });
        const tried = d.refs.map(r => r.tried.map(t => `${t.source}: ${t.accepted}/${t.found}${t.error ? " — " + esc(t.error) : ""}`).join(" · ")).join("<br>");
        const links = d.refs[0] ? Object.entries(d.refs[0].links).map(([k, u]) => `<a href="${esc(u)}" target="_blank" rel="noopener">${{ google_shopping: "Google Shopping", google: "Google", mercado_livre: "Mercado Livre", mercadocar: "Mercadocar" }[k]}</a>`).join(" · ") : "";
        out.innerHTML = (d.refs[0] ? `<p class="ps-qlink"><a href="${esc(d.refs[0].links.mercado_livre)}" target="_blank" rel="noopener">Abrir a consulta no Mercado Livre (menor preço) ↗</a>${d.refs[0].approx ? ' · <span class="badge warn">resultados aproximados (não citam o código)</span>' : ""}</p>` : "") + (d.results.length ? d.results.map((r, i) => `<article class="ps-card ${i === 0 ? "best" : ""}">${r.thumbnail ? `<img src="${esc(r.thumbnail)}" alt="" loading="lazy">` : '<span class="ps-noimg"></span>'}
            <div class="ps-b"><a href="${esc(r.url)}" target="_blank" rel="noopener" class="ps-t">${esc(r.title)}</a><div class="ps-m"><span class="tag">${esc(r.source)}</span> ${r.pair ? '<span class="badge warn" title="Anúncio de par, kit ou jogo">par/kit</span> ' : ""}${r.ref ? `<span class="xchip">${esc(r.ref)}</span>` : ""} ${r.seller ? `vendedor <b>${esc(r.seller)}</b>` : ""} ${r.reputation ? `· ${esc(r.reputation)}` : ""} ${r.free_shipping ? '· <span class="badge ok">frete grátis</span>' : ""} ${r.sold ? `· ${num(r.sold)} vendidos` : ""}</div></div>
            <div class="ps-p"><b>${brl(r.price)}</b>${i === 0 ? '<small class="best-t">menor preço</small>' : ""}<button type="button" class="btn sm" data-use="${i}">Usar este preço</button></div></article>`).join("") : note(`<b>Não consegui trazer o preço automaticamente — a consulta está pronta para abrir:</b> <a class="btn sm" target="_blank" rel="noopener" href="${esc(d.refs[0] ? d.refs[0].links.mercado_livre : "#")}">Abrir no Mercado Livre (menor preço) ↗</a> ${d.token_configured ? "" : "<br><small>Dica: com <code>ML_CLIENT_ID</code> e <code>ML_CLIENT_SECRET</code> no <code>.env</code> a busca automática fica mais estável.</small>"}<br>Outras buscas: ${links}`, "warn"))
          + `<details class="ps-dbg"><summary>Fontes consultadas</summary><div class="muted">${tried}</div><div>${links}</div></details>`;
        out.onclick = e => { const b = e.target.closest("[data-use]"); if (!b) return; const r = d.results[+b.dataset.use]; o.onUse && o.onUse(r); b.textContent = "✔ Adicionado"; b.disabled = true; };
      } catch (e) { out.innerHTML = note(esc(e.message), "err"); } finally { const b = $("#ps-go", host); if (b) b.disabled = false; }
    };
    render();
    return { setRefs(r) { const keep = refs.filter(x => x.manual); refs = [...r.map((x, i) => ({ ...x, on: i < 2 })), ...keep]; render(); }, search: go, refs: () => refs };
  }

  return { pages: { dashboard, metas }, serverPanel, priceSearch };
};
