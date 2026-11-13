/* Painel do servidor (Configurações) e busca de preços (Compra de amostras). (Dashboard: telas/dashboard.js · Metas & Validação: telas/metas.js.)
   Carregado antes do core.js; recebe os utilitários dele (window.PSD_NEW(ctx)). */
window.PSD_NEW = ctx => {
  const { post, $, esc, num, T, dmy } = ctx, J = ctx.J;
  const brl = v => v == null ? "–" : Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  const when = s => s ? `${dmy(s)} ${String(s).slice(11, 16)}`.trim() : "–";
  const note = (t, cls = "") => `<div class="notice ${cls}">${t}</div>`;

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

  return { serverPanel, priceSearch };
};
