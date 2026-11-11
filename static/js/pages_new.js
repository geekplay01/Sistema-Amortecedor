/* Telas novas: Dashboard (gráficos), painel do servidor e busca de preços. (Metas & Validação: static/js/telas/metas.js.)
   Carregado antes do core.js; recebe os utilitários dele (window.PSD_NEW(ctx)). */
window.PSD_NEW = ctx => {
  const { J, post, $, $$, esc, num, tag, T, clip, empty, fail, dlg, qs, dmy, root, FLG, FGROUPS } = ctx;
  const brl = v => v == null ? "–" : Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  const when = s => s ? `${dmy(s)} ${String(s).slice(11, 16)}`.trim() : "–";
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

  return { pages: { dashboard }, serverPanel, priceSearch };
};
