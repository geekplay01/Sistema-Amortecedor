/* Telas executivas em TailwindCSS: Pedidos em Aberto · Vendas (Curva A) · Garantia.
   (Metas & Validação usa o bloco PSDTW.validationBlock dentro de pages_new.js.) Recebe os utilitários do pages.js (window.PSD_EXEC(ctx)). */
window.PSD_EXEC = ctx => {
  const { J, $, root, fail } = ctx, TW = window.PSDTW, { esc, nf, brl, brl0, dmy } = TW;
  const MONTHS = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
  const FORN = { "ZS": "blue", "E-WIN": "green", "XGM": "violet", "VERIFICAR": "amber" };
  const debounce = (f, ms = 200) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => f(...a), ms); }; };
  const waiting = t => `<div class="flex items-center gap-3 rounded-2xl border border-line bg-card px-5 py-8 text-sm text-mute"><span class="h-4 w-4 animate-spin rounded-full border-2 border-slate-400 border-t-blue-500"></span>${t}</div>`;
  const pc = (c, l) => window.psdCode ? window.psdCode(c, l) : `<b>${esc(l || c)}</b>`;      // código com conector (menu: pesquisa · lados · pedidos · vendas)
  const nodata = (obj, extra = "") => TW.empty(`Os dados ainda não chegaram do servidor${obj ? ` (<code>${obj}</code>)` : ""}. Clique em <b>Sincronizar</b> no topo da tela${extra}.`);

  // ───────────────────────── Lead time (pedido → embarque → previsão) ─────────────────────────
  const dd = v => v == null ? "–" : nf(v, 0) + " d";
  function leadtimeBlock(L) {
    if (!L || !L.available) return "";
    const G = L.geral, M = L.meta_dias, over = x => x != null && x > M;
    const avail = [];
    if (!L.tem_embarques) avail.push("A view de <b>embarques</b> (EMBARQUES_DETALHADO) ainda não trouxe dados: sem ela não há como medir <b>pedido → embarque</b> nem <b>embarque → previsão de chegada</b>. Sincronize com o servidor.");
    if (!L.tem_historico || !G.adiadas) avail.push("O sistema passou a <b>gravar a data prevista a cada sincronização</b>; as previsões empurradas aparecerão a partir da 2ª sincronização com datas diferentes.");
    const cell = (o, tone) => `<span class="${tone ? "font-semibold text-red-600" : ""}">${o && o.media != null ? `${nf(o.media, 0)} d` : "–"}</span>${o && o.p90 != null ? `<span class="text-xs text-mute">&nbsp;· p90 ${nf(o.p90, 0)}</span>` : ""}`;
    const rows = [...L.por_fornecedor, { fornecedor: "Geral", ...G }].map(f => [`<b>${esc(f.fornecedor)}</b>`, nf(f.linhas), cell(f.prazo_prometido, over(f.prazo_prometido.media)), cell(f.ate_embarque), cell(f.transito), cell(f.prazo_real, over(f.prazo_real.media)),
      f.atraso.media == null ? "–" : `<span class="${f.atraso.media > 0 ? "font-semibold text-red-600" : ""}">${f.atraso.media > 0 ? "+" : ""}${nf(f.atraso.media, 0)} d</span>`,
      f.pct_acima_meta ? TW.badge(`${nf(f.acima_meta)} (${nf(f.pct_acima_meta, 0)}%)`, "red") : TW.badge("0", "green"), f.vencidas ? TW.badge(nf(f.vencidas), "red") : "0", f.adiadas ? TW.badge(`${nf(f.adiadas)} · +${nf(f.adiamento_medio_dias, 0)} d`, "amber") : "0"]);
    const al = L.linhas.filter(r => r.alertas.length).slice(0, 60);
    return TW.card(`Lead time por fornecedor <span class="ml-2 text-sm font-normal text-mute">meta ${nf(M)} dias (${nf(M / 30, 0)} meses)</span>`,
      `<div class="flex flex-col gap-4">
        <p class="text-sm text-mute"><b>Prometido</b> = previsão − emissão · <b>Pedido→embarque</b> = embarque − emissão · <b>Embarque→chegada</b> = previsão de chegada − embarque · <b>Real</b> = recebimento − emissão (só entregues) · <b>Atraso</b> = recebimento − previsão. Média e p90 (9 de cada 10 pedidos levam até esse prazo).</p>
        ${avail.map(t => TW.notice(t, "amber")).join("")}
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">${TW.kpi("Prazo prometido (médio)", dd(G.prazo_prometido.media), `mediana ${dd(G.prazo_prometido.mediana)} · meta ${M} d`, over(G.prazo_prometido.media) ? "red" : "green")}
          ${TW.kpi("Pedido → embarque", dd(G.ate_embarque.media), G.ate_embarque.n ? `${nf(G.ate_embarque.n)} linhas com embarque` : "sem dados de embarque", "blue")}
          ${TW.kpi("Embarque → chegada prevista", dd(G.transito.media), G.transito.n ? `${nf(G.transito.n)} linhas` : "sem dados de embarque", "slate")}
          ${TW.kpi("Prometido acima da meta", nf(G.acima_meta), `${nf(G.pct_acima_meta, 0)}% das linhas · ${nf(G.vencidas)} com previsão vencida`, G.acima_meta || G.vencidas ? "red" : "green")}</div>
        ${TW.table([{ h: "Fornecedor" }, { h: "Linhas", r: 1 }, { h: "Prometido", r: 1 }, { h: "Pedido→embarque", r: 1 }, { h: "Embarque→chegada", r: 1 }, { h: "Real (entregues)", r: 1 }, { h: "Atraso médio", r: 1 }, { h: "Acima da meta", r: 1 }, { h: "Vencidas", r: 1 }, { h: "Previsão empurrada", r: 1 }], rows, { h: "max-h-[40vh]" })}
        ${al.length ? `<details class="rounded-xl border border-line bg-card"><summary class="cursor-pointer px-4 py-3 text-sm font-semibold text-ink">Linhas com alerta (${nf(L.linhas.filter(r => r.alertas.length).length)}) — onde o fornecedor pode estar enrolando</summary><div class="p-3">${TW.table([{ h: "Código" }, { h: "Pedido" }, { h: "Fornecedor" }, { h: "Emissão" }, { h: "Previsão" }, { h: "Prometido", r: 1 }, { h: "Alertas", nw: false }],
          al.map(r => [`<b>${esc(r.codigo)}</b>`, esc(r.numero_pedido), TW.badge(r.fornecedor, FORN[r.fornecedor]), dmy(r.DATA_EMISSAO_PC), dmy(r.DATA_PREV_ENT), dd(r.prazo_prometido), r.alertas.map(a => TW.badge(a, "red")).join(" ")]), { h: "max-h-[50vh]" })}</div></details>` : ""}
      </div>`);
  }

  // ───────────────────────── Previsão de embarques e chegadas (etapas medidas no histórico) ─────────────────────────
  const ETAPAS = ["Aguardando embarque", "No mar", "No porto / desembaraço"], PARADO = "Parado — verificar saldo";
  const FCLR = { "ZS": "#2f6bff", "E-WIN": "#10b981", "XGM": "#8b5cf6", "VERIFICAR": "#f59e0b" };
  async function previsaoBlock(el) {
    let F; try { F = await J("/api/pedidos/previsao"); } catch (e) { el.innerHTML = ""; return; }
    if (!F.available) { el.innerHTML = ""; return; }
    const M = F.modelo, G = M.Geral, st = { etapa: "", forn: "", q: "" };
    const by = Object.fromEntries(F.por_etapa.map(x => [x.etapa, x]));
    const stg = (k, l, sub, cls = "") => `<div class="st ${cls}" data-et="${esc(k)}"><small>${l}</small><b>${nf((by[k] || {}).quantidade || 0)}</b><span>${nf((by[k] || {}).linhas || 0)} linha(s) · ${sub}</span></div>`;
    const cn = t => `<i class="cn"><em>${t}</em></i>`;
    const md = s => s && s.mediana != null ? `${nf(s.mediana)} d` : "–";
    const fornList = Object.keys(M).filter(k => k !== "Geral");
    el.innerHTML = TW.card(`Previsão de embarques e chegadas <span class="ml-2 text-sm font-normal text-mute">base: ${nf(F.historico_embarques)} embarques entregues nos últimos ${F.historico_meses} meses</span>`, `<div class="flex flex-col gap-5">
      <p class="text-sm text-mute">Cada linha em aberto é prevista a partir de <b>onde ela está hoje</b>, somando as etapas que faltam com o prazo <b>típico (mediana)</b> daquele fornecedor; a faixa é p25–p75 (metade dos casos históricos cai nela). No mar, usa o <b>ETA do servidor</b>. Fornecedor com menos de ${F.min_n} casos usa a base geral.</p>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">${TW.kpi("Chegam em 30 dias", nf(F.proximos_30), "peças previstas na filial", "blue")}${TW.kpi("Chegam em 90 dias", nf(F.proximos_90), "peças", "green")}
        ${TW.kpi("Vão atrasar (> 15 d da promessa)", nf(F.risco.quantidade), `${nf(F.risco.linhas)} linhas · atraso previsto mediano ${F.risco.atraso_mediano == null ? "–" : nf(F.risco.atraso_mediano) + " d"}`, F.risco.linhas ? "red" : "green")}
        ${TW.kpi("Parados — verificar saldo", nf(F.parados.quantidade), `${nf(F.parados.linhas)} linhas em ${nf(F.parados.pedidos)} pedidos sem embarque há mais de 2× o p90 da produção`, F.parados.linhas ? "amber" : "green")}</div>
      <div class="flowx">${stg("Aguardando embarque", "1 · Em produção", `típico ${md(G.producao)} até embarcar`)}${cn("produção")}${stg("No mar", "2 · No mar", `típico ${md(G.mar)} até o porto`)}${cn("mar")}${stg("No porto / desembaraço", "3 · No porto", `típico ${md(G.desembaraco)} até a filial`)}${cn("desembaraço")}<div class="st" data-et=""><small>4 · Filial</small><b>${md(G.total)}</b><span>total típico pedido → filial</span></div>${stg(PARADO, "Parado", "verificar saldo no ERP", "warn")}</div>
      <div class="grid grid-cols-1 gap-6 xl:grid-cols-2">${TW.card("Chegadas previstas por mês (peças)", '<div id="pvc" class="chart"></div>')}${TW.card("Embarques previstos por mês (peças ainda não embarcadas)", '<div id="pve" class="chart"></div>')}</div>
      ${TW.card("Etapas por fornecedor (dias · mediana e faixa p25–p75)", TW.table([{ h: "Fornecedor" }, { h: "Produção", r: 1 }, { h: "Mar", r: 1 }, { h: "Desembaraço", r: 1 }, { h: "Total", r: 1 }, { h: "p90 total", r: 1 }, { h: "Chegou até a promessa", r: 1 }, { h: "Atraso mediano", r: 1 }, { h: "Embarques", r: 1 }],
        [...fornList, "Geral"].map(f => { const m = M[f], c = m.confiabilidade || {}, rg = s => s && s.mediana != null ? `<b>${nf(s.mediana)}</b> <span class="rng">${nf(s.p25)}–${nf(s.p75)}</span>` : "–";
          return [f === "Geral" ? "<b>Geral</b>" : TW.badge(f, FORN[f]), rg(m.producao), rg(m.mar), rg(m.desembaraco), rg(m.total), m.total.p90 == null ? "–" : nf(m.total.p90), c.no_prazo_pct == null ? "–" : TW.badge(nf(c.no_prazo_pct, 0) + "%", c.no_prazo_pct >= 70 ? "green" : c.no_prazo_pct >= 40 ? "amber" : "red"), c.atraso_mediano == null ? "–" : (c.atraso_mediano > 0 ? "+" : "") + nf(c.atraso_mediano) + " d", nf(m.total.n)]; }), { h: "max-h-[40vh]" }))}
      ${TW.card("Linhas previstas", `<div class="mb-3 flex flex-wrap items-center gap-3"><div class="min-w-[200px] flex-1">${TW.input("pvq", "Buscar código ou pedido…")}</div>${TW.select("pvf", [["", "Fornecedor: todos"], ...fornList.map(f => [f, f])], "")}${TW.select("pvs", [["", "Etapa: todas"], ...[...ETAPAS, PARADO].map(e => [e, e])], "")}${TW.btn("pvcsv", "Exportar (CSV)")}</div><div id="pvt"></div>`, `<span id="pvn" class="text-sm text-mute"></span>`)}</div>`);
    const cal = (id, C) => PSDCharts.bars($("#" + id), { x: C.meses.map(m => m === "depois" ? "depois" : m), stacked: true, series: C.series.map(s => ({ name: s.fornecedor, y: s.qtd, color: FCLR[s.fornecedor] })) });
    cal("pvc", F.calendario); cal("pve", F.calendario_embarques);
    const rows = () => F.linhas.filter(r => (!st.etapa || r.etapa === st.etapa) && (!st.forn || r.fornecedor === st.forn) && (!st.q || r.codigo.includes(st.q) || String(r.pedido).includes(st.q)));
    const draw = () => { const v = rows(); $("#pvn").textContent = `${nf(v.length)} de ${nf(F.linhas_total)} linha(s)`;
      el.querySelectorAll(".flowx .st").forEach(x => x.classList.toggle("on", !!st.etapa && x.dataset.et === st.etapa));
      $("#pvt").innerHTML = TW.table([{ h: "Código" }, { h: "Pedido" }, { h: "Fornecedor" }, { h: "Qtd", r: 1 }, { h: "Etapa" }, { h: "Emissão" }, { h: "Promessa" }, { h: "Embarque" }, { h: "ETA servidor" }, { h: "Chegada prevista" }, { h: "Faixa" }, { h: "vs. promessa", r: 1 }, { h: "Confiança" }],
        v.slice(0, 400).map(r => [pc(r.codigo), esc(r.pedido), TW.badge(r.fornecedor, FORN[r.fornecedor]), nf(r.quantidade), TW.badge(r.etapa, r.etapa === PARADO ? "amber" : r.etapa === "No mar" ? "blue" : r.etapa.startsWith("No porto") ? "violet" : "slate"),
          dmy(r.emissao), dmy(r.prometido), r.embarque ? dmy(r.embarque) : r.embarque_previsto ? `<span class="text-mute">~${dmy(r.embarque_previsto)}</span>` : "–", dmy(r.eta_servidor),
          r.etapa === PARADO ? '<span class="text-mute">–</span>' : `<b>${dmy(r.chegada_prevista)}</b>${r.dias_para_chegar < 0 ? ` ${TW.badge("vencida", "red")}` : ""}`, r.etapa === PARADO ? "–" : `<span class="rng">${dmy(r.faixa_de)} – ${dmy(r.faixa_ate)}</span>`,
          r.atraso_previsto == null || r.etapa === PARADO ? "–" : r.atraso_previsto > 15 ? TW.badge(`+${nf(r.atraso_previsto)} d`, "red") : r.atraso_previsto > 0 ? TW.badge(`+${nf(r.atraso_previsto)} d`, "amber") : TW.badge("no prazo", "green"), TW.badge(r.confianca, r.confianca === "alta" ? "green" : r.confianca === "média" ? "amber" : "slate")]), { h: "max-h-[60vh]" }); };
    el.querySelector(".flowx").onclick = e => { const s = e.target.closest(".st[data-et]"); if (!s) return; st.etapa = st.etapa === s.dataset.et ? "" : s.dataset.et; $("#pvs").value = st.etapa; draw(); };
    $("#pvq").oninput = debounce(e => { st.q = e.target.value.trim().toUpperCase(); draw(); }); $("#pvf").onchange = e => { st.forn = e.target.value; draw(); }; $("#pvs").onchange = e => { st.etapa = e.target.value; draw(); };
    $("#pvcsv").onclick = () => { const cols = ["codigo", "pedido", "fornecedor", "quantidade", "etapa", "emissao", "prometido", "embarque", "embarque_previsto", "eta_servidor", "chegada_prevista", "faixa_de", "faixa_ate", "atraso_previsto", "confianca"]; TW.csv("previsao_chegadas.csv", cols, rows().map(r => cols.map(c => r[c]))); };
    draw();
  }

  // ───────────────────────── Pedidos em Aberto ─────────────────────────
  async function pedidos() {
    root.innerHTML = waiting("Carregando pedidos em aberto…");
    const st0 = { q: (new URLSearchParams(location.search).get("q") || "").trim(), forn: "", st: "", rec: "0", tipo: "compra", page: 1 };
    const get = () => J("/api/pedidos-em-aberto?" + new URLSearchParams({ q: st0.q, fornecedor: st0.forn, status: st0.st, recebidos: st0.rec, tipo: st0.tipo, page: st0.page, size: 200 }).toString());
    let d, lt; try { [d, lt] = await Promise.all([get(), J("/api/pedidos/leadtime").catch(() => ({ available: false }))]); } catch (e) { root.innerHTML = ""; return fail(e); }
    if (!d.available) { root.innerHTML = nodata("PEDIDOS_COMPRA_DETALHADO"); return; }
    const today = new Date().toISOString().slice(0, 10), months = s => { if (!s) return null; const a = new Date(s), b = new Date(); return Math.max(0, (b.getFullYear() - a.getFullYear()) * 12 + b.getMonth() - a.getMonth()); };
    const S = d.summary;
    root.innerHTML = `<div class="flex flex-col gap-6">
      <div id="pprev">${waiting("Calculando a previsão de embarques e chegadas…")}</div>
      ${leadtimeBlock(lt)}
      <p class="text-sm text-mute">Pedidos de compra de <b>amortecedor</b> com código iniciado em <b>MP-</b> e saldo em aberto. O fornecedor vem do código EX do ERP (EX0002116 = ZS · EX0002110 = E-WIN · EX008042 = XGM; outro código aparece como <b>VERIFICAR</b>).</p>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">${TW.kpi("Pedidos em aberto", nf(S.pedidos), `${nf(S.linhas)} linhas`, "blue")}${TW.kpi("Itens (códigos)", nf(S.itens), "", "green")}
        ${TW.kpi("Quantidade em aberto", nf(S.quantidade), "peças aguardando entrega", "slate")}${TW.kpi("Com previsão vencida", nf(S.vencidas), S.verificar ? `${nf(S.verificar)} linha(s) com fornecedor a VERIFICAR` : "entrega após a previsão", S.vencidas ? "red" : "green")}</div>
      ${TW.card("Pedidos", `<div class="mb-4 flex flex-wrap items-center gap-3"><div class="min-w-[220px] flex-1">${TW.input("pq", "Buscar código ou nº do pedido…")}</div>
        ${TW.select("pst", [["", "STATUS_PC: todos"], ...(d.status_pc || []).map(x => [x.status, `${x.status} (${nf(x.linhas)})`])], "")}
        ${TW.select("pab", [["0", "Somente em aberto"], ["1", "Incluir já recebidos"]], "0")}
        ${TW.select("ptp", [["compra", "Tipo: Compra (servidor)"], ["amostra", `Tipo: Amostra (${nf(d.n_amostras || 0)})`], ["todos", "Tipo: Compra + Amostra"]], "compra")}
        <div id="pf" class="flex flex-wrap gap-2"></div>${TW.btn("pcsv", "Exportar página (CSV)")}</div><div id="ptab"></div><div id="ppg" class="mt-3 flex items-center justify-between text-sm text-mute"></div>`, `<span id="pcount" class="text-sm text-mute"></span>`)}</div>`;
    const chips = () => { $("#pf").innerHTML = [["", "Todos", S.linhas], ...S.por_fornecedor.map(f => [f.fornecedor, f.fornecedor, null])]
      .map(([v, l, n]) => `<button type="button" data-f="${esc(v)}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${st0.forn === v ? "border-blue-500 bg-blue-500 text-white" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${esc(l)}${n != null ? ` · ${nf(n)}` : ""}</button>`).join(""); };
    const draw = () => { const pages = Math.max(1, Math.ceil(d.total / d.size)); chips(); $("#pcount").textContent = `${nf(d.total)} linha(s)` + ((d.busca && d.busca.perfect.length) ? ` · «${d.busca.termo}» é código de concorrente → PERFECT: ${d.busca.perfect.slice(0, 5).join(", ")}` : "");
      $("#ptab").innerHTML = TW.table([{ h: "Código" }, { h: "Pedido" }, { h: "Abertura" }, { h: "Meses em aberto", r: 1 }, { h: "Quantidade", r: 1 }, { h: "Previsão" }, { h: "Fornecedor" }, { h: "Tipo" }, { h: "STATUS_PC" }, { h: "Prazo" }],
        d.rows.map(r => { const m = months(r.DATA_EMISSAO_PC), late = !!r.DATA_PREV_ENT && r.DATA_PREV_ENT < today;
          return [pc(r.codigo), esc(r.numero_pedido), dmy(r.DATA_EMISSAO_PC), m == null ? "–" : nf(m), nf(r.quantidade), dmy(r.DATA_PREV_ENT), TW.badge(r.fornecedor, FORN[r.fornecedor]), TW.badge(r.TIPO_PEDIDO || "Compra", r.TIPO_PEDIDO === "Amostra" ? "amber" : "slate"), TW.badge(r.STATUS_PC, r.em_aberto ? "blue" : "slate"),
            !r.em_aberto ? TW.badge("Recebido", "slate") : late ? TW.badge("Atrasado", "red") : r.DATA_PREV_ENT ? TW.badge("No prazo", "green") : TW.badge("Sem previsão", "slate")]; }));
      $("#ppg").innerHTML = pages > 1 ? `<span>Página ${d.page} de ${pages}</span><span class="flex gap-2">${TW.btn("ppv", "‹ Anterior")}${TW.btn("pnx", "Próxima ›")}</span>` : "";
      if (pages > 1) { $("#ppv").disabled = d.page <= 1; $("#pnx").disabled = d.page >= pages; $("#ppv").onclick = () => reload(d.page - 1); $("#pnx").onclick = () => reload(d.page + 1); } };
    const reload = async (pg = 1) => { st0.page = pg; $("#ptab").style.opacity = .5; try { d = await get(); } catch (e) { return fail(e); } $("#ptab").style.opacity = 1; draw(); };
    previsaoBlock($("#pprev")); $("#pq").value = st0.q;
    $("#pq").oninput = debounce(e => { st0.q = e.target.value.trim(); reload(); }, 300); $("#pst").onchange = e => { st0.st = e.target.value; reload(); }; $("#pab").onchange = e => { st0.rec = e.target.value; reload(); }; $("#ptp").onchange = e => { st0.tipo = e.target.value; reload(); };
    $("#pf").onclick = e => { const b = e.target.closest("[data-f]"); if (b) { st0.forn = b.dataset.f; reload(); } };
    $("#pcsv").onclick = () => TW.csv("pedidos_em_aberto.csv", [...d.columns, "TIPO_PEDIDO"], d.rows.map(r => [...d.columns, "TIPO_PEDIDO"].map(c => r[c]))); draw();
  }

  // ───────────────────────── Vendas · Curva A ─────────────────────────
  // «Conferir com o BI»: envia o export VENDA_POR_SKU do Power BI e compara com o servidor e com o catálogo (POST /api/vendas/conciliar). Nada é gravado.
  function conciliar(el) {
    el.innerHTML = `<details class="rounded-2xl border border-line bg-card shadow-sm"><summary class="cursor-pointer px-5 py-4 text-base font-semibold text-ink">Conferir com o BI (export VENDA_POR_SKU)</summary><div class="flex flex-col gap-4 px-5 pb-5">
      <label for="cfile" class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-line px-6 py-6 text-center hover:bg-slate-500/10"><span class="text-sm font-semibold text-ink">Clique para enviar o export do BI (.xlsx ou .csv com PRODUTO, QTD e VALOR)</span><span class="text-xs text-mute">Os filtros do BI (ano, mês e LINHA) são lidos da linha «Filtros aplicados» e aplicados também aos dados do servidor.</span></label>
      <input id="cfile" type="file" accept=".xlsx,.xls,.csv,.txt" class="hidden"><div id="cres"></div></div></details>`;
    el.querySelector("#cfile").onchange = async e => { const f = e.target.files[0]; if (!f) return; const out = el.querySelector("#cres"), fd = new FormData(); fd.append("file", f); out.innerHTML = waiting(`Comparando ${esc(f.name)}…`);
      let r; try { r = await J("/api/vendas/conciliar", { method: "POST", body: fd }); } catch (er) { out.innerHTML = TW.notice(esc(er.message), "red"); return; }
      const S = r.servidor || {}, C = r.catalogo, F = r.filtros || {};
      const lst = (t, rows) => rows && rows.length ? TW.card(t, TW.table([{ h: "Produto" }, { h: "Qtd BI", r: 1 }, { h: "Valor BI", r: 1 }, { h: "Qtd servidor", r: 1 }, { h: "Valor servidor", r: 1 }, { h: "Dif. valor", r: 1 }],
        rows.map(x => [pc(x.produto), nf(x.qtd_bi), brl(x.valor_bi), nf(x.qtd_srv), brl(x.valor_srv), x.dv ? `<span class="${Math.abs(x.dv) > 1 ? "font-semibold text-red-600" : ""}">${brl(x.dv)}</span>` : "–"]), { h: "max-h-[40vh]" })) : "";
      out.innerHTML = `<div class="flex flex-col gap-4">${TW.notice(`Filtros do BI: ano <b>${F.ano || "todos"}</b> · mês <b>${F.mes ? MONTHS[F.mes] : "todos"}</b> · linha <b>${esc((F.incluidos || []).join(", ") || "AMORTECEDOR")}</b>${(F.excluidos || []).length ? ` · exceto ${esc(F.excluidos.join(", "))}` : ""}`, "blue")}
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">${TW.kpi("BI", brl0(r.bi.valor), `${nf(r.bi.skus)} SKUs · ${nf(r.bi.qtd)} peças`, "blue")}${S.disponivel ? TW.kpi("Servidor", brl0(S.valor), `${nf(S.skus)} SKUs · ${nf(S.qtd)} peças`, "green") + TW.kpi("SKUs iguais", nf(S.iguais), `${nf(S.diferentes)} com diferença · ${nf(S.n_so_bi)} só no BI · ${nf(S.n_so_srv)} só no servidor`, S.diferentes ? "amber" : "green") : TW.kpi("Servidor", "–", esc(S.motivo || ""), "amber")}
          ${C ? TW.kpi("Fora do catálogo", `${nf(C.skus_fora)} SKUs`, `${nf(C.pct_valor_fora, 1)}% do valor · ${nf(C.resolvidos_por_equivalencia)} resolvidos por equivalência`, C.skus_fora ? "amber" : "green") : ""}</div>
        ${lst("Diferenças BI × servidor", S.diferencas)}${lst("Só no BI", S.so_no_bi)}${lst("Só no servidor", S.so_no_servidor)}
        ${C && C.rows.length ? TW.card("Vendidos fora do catálogo (CatalogoAMD)", TW.table([{ h: "Produto" }, { h: "Qtd", r: 1 }, { h: "Valor", r: 1 }, { h: "Equivalente no catálogo" }], C.rows.slice(0, 200).map(x => [pc(x.produto), nf(x.qtd), brl(x.valor), x.equivalente ? esc(x.equivalente) : '<span class="text-mute">–</span>']), { h: "max-h-[40vh]" })) : ""}</div>`; };
  }

  async function vendasResumo(el) {
    let o; try { o = await J("/api/vendas/resumo?months=24"); } catch (e) { el.innerHTML = ""; return; }
    if (!o.available) { el.innerHTML = ""; return; }
    if (o.sem_data) { el.innerHTML = TW.notice("As vendas do servidor chegaram <b>sem data de faturamento</b>. Clique em <b>Sincronizar</b> no topo: a nova carga lê <code>DATA_FATUR</code> e os valores (<code>VALOR_TOTAL_CIPI</code>) já somados por mês no servidor.", "amber"); return; }
    const Y = o.ytd, pct = v => v == null ? "" : `<span class="${v >= 0 ? "text-emerald-600" : "text-red-600"} font-semibold">${v >= 0 ? "▲" : "▼"} ${nf(Math.abs(v), 1)}%</span>`;
    el.innerHTML = `<div class="flex flex-col gap-6">
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">${TW.kpi(`Faturado ${Y.ano} (até ${MONTHS[Y.ate_mes]})`, brl0(Y.valor), `${pct(Y.var_valor_pct)} vs. ${brl0(Y.valor_ant)} no mesmo período de ${Y.ano - 1}`, "blue")}
        ${TW.kpi("Peças faturadas", nf(Y.qtd), `${pct(Y.var_qtd_pct)} vs. ${nf(Y.qtd_ant)} em ${Y.ano - 1}`, "green")}
        ${TW.kpi("Faturamento de SKUs do catálogo", o.catalogo.pct_valor_catalogo == null ? "–" : nf(o.catalogo.pct_valor_catalogo, 1) + "%", `${nf(o.catalogo.skus_fora)} SKU(s) vendidos fora do CatalogoAMD em ${o.catalogo.ano}`, o.catalogo.pct_valor_catalogo >= 90 ? "green" : "amber")}
        ${TW.kpi("Dados do servidor", `<span class="text-lg">${esc(MONTHS[+o.primeiro_mes.slice(5)].slice(0, 3))}/${o.primeiro_mes.slice(0, 4)} → ${esc(MONTHS[+o.ultimo_mes.slice(5)].slice(0, 3))}/${o.ultimo_mes.slice(0, 4)}</span>`, `atualizado ${dmy(o.atualizado_em)} · ${esc(o.carga || "carga completa")}`, "slate")}</div>
      ${TW.card("Faturamento mensal de amortecedores (últimos 24 meses)", '<div id="vmes" class="chart"></div>', `<span class="text-sm text-mute">${o.por_linha.map(l => `${esc(l.linha)}: ${brl0(l.v)}`).join(" · ")}</span>`)}</div>`;
    PSDCharts.bars($("#vmes"), { x: o.meses.map(m => m.mes), series: [{ name: "Faturado (R$)", y: o.meses.map(m => Math.round(m.valor)) }], colors: ["#2f6bff"] });
  }
  async function vendas() {
    const P = new URLSearchParams(location.search);
    let year = P.get("year") || "", month = "", cls = "", q = (P.get("q") || "").trim().toUpperCase(), d;
    root.innerHTML = `<div class="flex flex-col gap-6"><div id="vres"></div><div id="vtop" class="flex flex-wrap items-center gap-3"></div><div id="vbody">${waiting("Calculando a Curva A…")}</div><div id="vcon"></div></div>`;
    vendasResumo($("#vres")); conciliar($("#vcon"));
    const load = async () => {
      $("#vbody").innerHTML = waiting("Calculando a Curva A…");
      try { d = await J("/api/vendas/curva-a?" + new URLSearchParams({ year, month }).toString()); } catch (e) { $("#vbody").innerHTML = ""; return fail(e); }
      if (!d.available) { $("#vtop").innerHTML = ""; $("#vbody").innerHTML = nodata("VENDAS_FATURAMENTO_DETALHADO"); return; }
      $("#vtop").innerHTML = `<label class="flex items-center gap-2 text-sm text-mute">Ano ${TW.select("vy", [["", "Todos"], ...d.years.map(y => [y, y])], year)}</label>
        <label class="flex items-center gap-2 text-sm text-mute">Mês ${TW.select("vm", [["", "Todos"], ...MONTHS.slice(1).map((m, i) => [i + 1, m])], month)}</label>
        <div class="min-w-[200px] flex-1">${TW.input("vq", "Buscar produto (SKU)…")}</div>
        <div id="vc" class="flex gap-2"></div>${TW.btn("vcsv", "Exportar CSV")}`;
      $("#vy").onchange = e => { year = e.target.value; load(); }; $("#vm").onchange = e => { month = e.target.value; load(); };
      $("#vq").oninput = debounce(e => { q = e.target.value.trim().toUpperCase(); table(); }); $("#vq").value = q;
      $("#vc").onclick = e => { const b = e.target.closest("[data-c]"); if (b) { cls = b.dataset.c; table(); } };
      $("#vcsv").onclick = () => TW.csv("vendas_curva_a.csv", ["PRODUTO", "QTD", "VALOR", "pct", "acum_pct", "classe"], d.rows.map(r => [r.PRODUTO, r.QTD, r.VALOR, r.pct, r.acum_pct, r.classe]));
      const C = d.classes; const sk = ["A", "B", "C"].map(c => [c, C.n[c], C.valor_pct[c]]);
      $("#vbody").innerHTML = `<div class="flex flex-col gap-6"><div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">${TW.kpi("Faturado", brl0(d.total_valor), month || year ? `${month ? MONTHS[+month] + " de " : ""}${year || "todos os anos"}` : "todo o período", "blue")}
        ${TW.kpi("Quantidade", nf(d.total_qtd), "peças faturadas", "green")}${TW.kpi("SKUs", nf(d.skus), "códigos com faturamento", "slate")}${TW.kpi("Curva A", `${nf(C.n.A)} SKUs`, `${nf(C.valor_pct.A, 1)}% do faturamento`, "amber")}</div>
        <div class="grid grid-cols-1 gap-6 xl:grid-cols-3"><div class="xl:col-span-2">${TW.card("Top 15 SKUs por valor faturado", '<div id="vh" class="chart"></div>')}</div>${TW.card("Participação por classe", '<div id="vd" class="chart"></div>')}</div>
        ${TW.card("Curva ABC por produto", '<div id="vt"></div>', `<span id="vcount" class="text-sm text-mute"></span>`)}</div>`;
      const top = d.rows.slice(0, 15);
      top.length ? PSDCharts.hbars($("#vh"), { labels: top.map(r => r.PRODUTO), values: top.map(r => r.VALOR), color: "#2f6bff" }) : $("#vh").innerHTML = '<div class="ch-empty">Sem vendas no período.</div>';
      PSDCharts.donut($("#vd"), { labels: sk.map(([c, n]) => `Classe ${c} · ${n} SKUs`), values: sk.map(s => s[2] || 0), colors: ["#2f6bff", "#10b981", "#94a3b8"] });
      table();
    };
    const table = () => {
      const v = d.rows.map((r, i) => ({ ...r, n: i + 1 })).filter(r => (!cls || r.classe === cls) && (!q || r.PRODUTO.includes(q))), TONE = { A: "blue", B: "green", C: "slate" };
      $("#vc").innerHTML = [["", "Todas"], ["A", "A"], ["B", "B"], ["C", "C"]].map(([k, l]) => `<button type="button" data-c="${k}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${cls === k ? "border-blue-500 bg-blue-500 text-white" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${l}</button>`).join("");
      $("#vcount").textContent = `${nf(v.length)} de ${nf(d.rows.length)} SKUs`;
      $("#vt").innerHTML = TW.table([{ h: "#", r: 1 }, { h: "Produto" }, { h: "Qtd", r: 1 }, { h: "Valor faturado", r: 1 }, { h: "%", r: 1 }, { h: "% acumulado" }, { h: "Classe" }],
        v.map(r => [nf(r.n), pc(r.PRODUTO), nf(r.QTD), brl(r.VALOR), nf(r.pct, 2) + "%", `<div class="flex items-center gap-2"><div class="h-1.5 w-24 overflow-hidden rounded-full bg-slate-500/20"><div class="h-full rounded-full bg-blue-500" style="width:${Math.min(100, r.acum_pct)}%"></div></div><span class="tabular-nums text-mute">${nf(r.acum_pct, 1)}%</span></div>`, TW.badge(r.classe, TONE[r.classe])]));
    };
    load();
  }

  // ───────────────────────── Garantia ─────────────────────────
  async function garantia() {
    root.innerHTML = `<div class="flex flex-col gap-6"><div id="gup"></div><div id="gbody"></div></div>`;
    let rep = null;
    let fromServer = false;
    const upload = () => { if (fromServer) { $("#gup").innerHTML = ""; return; } $("#gup").innerHTML = TW.card("Planilha de garantia", `<label for="gfile" class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-line px-6 py-8 text-center hover:bg-slate-500/10">
        <svg class="h-8 w-8 text-mute" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16V4M7 9l5-5 5 5M4 20h16"/></svg>
        <span class="text-sm font-semibold text-ink">Clique para enviar o Excel/CSV de garantia</span><span class="text-xs text-mute">Só <b>código</b>, <b>defeito</b> e <b>quantidade</b> são mantidos; as demais colunas (cliente, valor, fabricante…) são descartadas.</span></label>
        <input id="gfile" type="file" accept=".xlsx,.xls,.csv,.txt" class="hidden"><div id="gmsg" class="mt-4">${rep || ""}</div>`);
      $("#gfile").onchange = async e => { const f = e.target.files[0]; if (!f) return; const fd = new FormData(); fd.append("file", f); $("#gmsg").innerHTML = waiting(`Lendo ${esc(f.name)}…`);
        try { const r = await J("/api/warranty/parse?rows=0", { method: "POST", body: fd }), ds = r.descartadas;
          rep = TW.notice(`<b>${nf(r.validas)}</b> de ${nf(r.lidas)} linhas válidas. Descartadas: ${nf(ds.sem_codigo)} sem código, ${nf(ds.sem_quantidade)} sem quantidade${ds.linha_de_total ? `, ${nf(ds.linha_de_total)} linha de total` : ""}. Colunas removidas: ${r.colunas_removidas.length ? r.colunas_removidas.map(esc).join(", ") : "nenhuma"}.`, "blue"); upload(); body(); }
        catch (er) { rep = TW.notice(esc(er.message), "red"); upload(); } };
    };
    const body = async (code = "") => {
      let d; try { d = await J("/api/warranty?top=15" + (code ? "&code=" + encodeURIComponent(code) : "")); } catch (e) { return fail(e); }
      if (!d.available) { $("#gbody").innerHTML = TW.empty("Nenhum dado de garantia ainda. Aguarde a sincronização com o servidor (ANALITICO_GARANTIA_DEVOLUCAO) ou envie a planilha acima."); return; }
      if ((d.meta.origem === "servidor") !== fromServer) { fromServer = d.meta.origem === "servidor"; upload(); }
      $("#gbody").innerHTML = `<div class="flex flex-col gap-6"><div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">${TW.kpi("Peças em garantia", nf(d.total), code ? `filtro «${esc(code)}»` : "soma das quantidades", "red")}${TW.kpi("Códigos", nf(d.codigos), "com ocorrência", "blue")}
        ${TW.kpi("Tipos de defeito", nf(d.defeitos), "relatados", "amber")}${TW.kpi(d.meta.origem === "servidor" ? "Origem" : "Arquivo", `<span class="text-lg">${d.meta.origem === "servidor" ? "Servidor · " : ""}${esc(d.meta.filename || "–")}</span>`, `${nf(d.meta.rows)} linhas · ${dmy(d.meta.loaded_at)}`, "slate")}</div>
        <div class="grid grid-cols-1 gap-6 xl:grid-cols-2">${TW.card("Defeitos mais frequentes", '<div id="gd" class="chart"></div>')}${TW.card("Códigos com mais peças em garantia", '<div id="gc" class="chart"></div>')}</div>
        ${TW.card("Código × defeito", '<div id="gt"></div>', `<div class="w-64">${TW.input("gq", "Filtrar por código…")}</div>`)}</div>`;
      PSDCharts.hbars($("#gd"), { labels: d.top_defeitos.map(r => r.defeito), values: d.top_defeitos.map(r => r.quantidade), color: "#f43f5e" });
      PSDCharts.hbars($("#gc"), { labels: d.top_codigos.map(r => r.codigo), values: d.top_codigos.map(r => r.quantidade), color: "#2f6bff" });
      $("#gt").innerHTML = TW.table([{ h: "Código" }, { h: "Defeito relatado", nw: false }, { h: "Quantidade", r: 1 }], d.lista.map(r => [`<b>${esc(r.codigo)}</b>`, esc(r.defeito), nf(r.quantidade)]));
      const gq = $("#gq"); gq.value = code; gq.oninput = debounce(e => body(e.target.value.trim()), 350); if (code) { gq.focus(); gq.setSelectionRange(code.length, code.length); }
    };
    upload(); body();
  }
  // ───────────────────────── FOB (preços de compra em US$) ─────────────────────────
  async function fob() {
    const st = { q: "", filtro: "", page: 1 }; let msg = "", d;
    root.innerHTML = `<div class="flex flex-col gap-6"><div id="fup"></div><div id="fbody">${waiting("Carregando FOB…")}</div></div>`;
    const money = v => v == null ? "–" : Number(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const upload = () => { $("#fup").innerHTML = TW.card("Planilha FOB", `<label for="ffile" class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-line px-6 py-6 text-center hover:bg-slate-500/10">
        <span class="text-sm font-semibold text-ink">Clique para enviar a tabela FOB (TABELA-PRECO .xlsx)</span><span class="text-xs text-mute">Une pelo código do produto (coluna <b>PartNumber</b>); quem tem vários códigos de fornecedor fica com o <b>menor FOB</b>. Reenviar substitui a versão anterior. Só administrador.</span></label>
        <input id="ffile" type="file" accept=".xlsx,.xls,.csv" class="hidden"><div class="mt-4">${msg}</div>`);
      $("#ffile").onchange = async e => { const f = e.target.files[0]; if (!f) return; const fd = new FormData(); fd.append("file", f); msg = waiting(`Importando ${esc(f.name)}…`); upload();
        try { const r = await J("/api/fob/import", { method: "POST", body: fd });
          msg = TW.notice(`FOB importado: <b>${nf(r.itens_fob)}</b> itens (de ${nf(r.linhas_fob)} linhas; ${nf(r.sem_partnumber)} sem PartNumber, ${nf(r.partnumber_repetido)} repetidos → menor FOB). <b>${nf(r.com_fob)}</b> produtos receberam FOB; ${nf(r.sem_fob)} ficaram sem; ${nf(r.fob_sem_produto)} itens do FOB não existem no catálogo.`, "blue"); upload(); load(); }
        catch (er) { msg = TW.notice(esc(er.message), "red"); upload(); } };
    };
    const load = async () => {
      try { d = await J("/api/fob?" + new URLSearchParams({ q: st.q, filtro: st.filtro, page: st.page, size: 100 }).toString()); } catch (e) { return fail(e); }
      if (!d.available) { $("#fbody").innerHTML = TW.empty("Nenhuma tabela FOB importada ainda. Envie a planilha acima."); return; }
      const S = d.summary, pages = Math.max(1, Math.ceil(d.total / d.size));
      $("#fbody").innerHTML = `<div class="flex flex-col gap-6"><div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">${TW.kpi("Produtos do catálogo", nf(S.catalogo), `${nf(S.itens_fob)} itens na tabela FOB`, "blue")}${TW.kpi("Com FOB", nf(S.com_fob), `${nf(S.catalogo ? 100 * S.com_fob / S.catalogo : 0, 0)}% do catálogo`, "green")}
        ${TW.kpi("Sem FOB", nf(S.sem_fob), "produtos sem preço na tabela", S.sem_fob ? "amber" : "green")}${TW.kpi("FOB médio", S.fob_medio == null ? "–" : "US$ " + money(S.fob_medio), `importado em ${dmy(S.carregado_em)} · ${nf(S.fob_sem_produto)} do FOB fora do catálogo`, "slate")}</div>
        ${TW.card("FOB por produto", `<div class="mb-4 flex flex-wrap items-center gap-3"><div class="min-w-[220px] flex-1">${TW.input("fq", "Buscar código, descrição ou código do fornecedor…")}</div>${TW.select("ff", [["", "Todos"], ["com", "Só com FOB"], ["sem", "Só sem FOB"]], st.filtro)}${TW.btn("fcsv", "Exportar página (CSV)")}</div>
          ${TW.table([{ h: "Código" }, { h: "Descrição", nw: false }, { h: "FOB mín. (US$)", r: 1 }, { h: "Melhor preço" }, { h: "E-WIN", r: 1 }, { h: "ZS", r: 1 }, { h: "XGM", r: 1 }, { h: "Cód. fornecedor" }],
            d.rows.map(r => [`<b>${esc(r.perfect_code)}</b>`, esc(r.description || ""), r.fob == null ? TW.badge("sem FOB", "amber") : `<b>${money(r.fob)}</b>`, r.fob_fornecedor ? `${TW.badge(r.fob_fornecedor, FORN[r.fob_fornecedor] || "slate")} ${esc(r.fob_origem || "")} ${dmy(r.fob_data)}` : "–", money(r.fob_ewin), money(r.fob_zs), money(r.fob_xgm), esc(r.fob_cod_fornecedor || "–")]))}
          <div class="mt-3 flex items-center justify-between text-sm text-mute"><span>${nf(d.total)} produto(s) · página ${d.page} de ${pages}</span>${pages > 1 ? `<span class="flex gap-2">${TW.btn("fpv", "‹ Anterior")}${TW.btn("fnx", "Próxima ›")}</span>` : ""}</div>`)}</div>`;
      const fq = $("#fq"); fq.value = st.q; fq.oninput = debounce(e => { st.q = e.target.value.trim(); st.page = 1; load().then(() => { const x = $("#fq"); x.focus(); x.setSelectionRange(x.value.length, x.value.length); }); }, 350);
      $("#ff").onchange = e => { st.filtro = e.target.value; st.page = 1; load(); };
      if (pages > 1) { $("#fpv").disabled = d.page <= 1; $("#fnx").disabled = d.page >= pages; $("#fpv").onclick = () => { st.page--; load(); }; $("#fnx").onclick = () => { st.page++; load(); }; }
      $("#fcsv").onclick = () => TW.csv("fob.csv", ["codigo", "descricao", "fob", "fob_ewin", "fob_zs", "fob_xgm", "melhor_fornecedor", "origem", "data", "cod_fornecedor"], d.rows.map(r => [r.perfect_code, r.description, r.fob, r.fob_ewin, r.fob_zs, r.fob_xgm, r.fob_fornecedor, r.fob_origem, r.fob_data, r.fob_cod_fornecedor]));
    };
    upload(); load();
  }

  return { pages: { "pedidos-aberto": pedidos, vendas, garantia, fob } };
};
