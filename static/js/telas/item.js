/* Tela · Página do item (/item/<código>, etapa 17 · Q9): tudo o que o app tem de um código, de forma visual. Substitui a ficha antiga (janela).
   Topo com desenho, código, descrição e selos (origem, sistema, família, linha, híbrido, lançamento, curva ABC, situação) + 4 KPIs; índice fixo das seções;
   seção sem dado fica recolhida com «sem registro». Fonte: /api/item/<código> (item.py). */
(function () {
  const { $, esc, J, root, SYS, dmy } = PSD;
  const TW = window.PSDTW, { nf, brl0, badge, kpi, ico, grafico } = TW;
  const mm = v => v == null ? "–" : nf(v, v % 1 ? 1 : 0);
  const cap = s => s ? String(s).charAt(0) + String(s).slice(1).toLowerCase() : "";
  const linha = l => cap(String(l || "").replace(/^LINHA\s+/, ""));
  const SIT = { ruptura: ["Ruptura", "red"], risco: ["Risco", "amber"], ok: ["OK", "green"], excesso: ["Excesso", "violet"], sem_giro: ["Sem giro", "slate"] };
  const mes = m => { const [y, mo] = String(m).split("-"); return ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"][+mo - 1] + "/" + String(y).slice(2); };
  const anos = r => r.year_from || r.year_to ? `${r.year_from || "…"}–${r.year_to || "…"}` : "–";
  const vazio = (t = "Sem registro.") => `<p class="m-0 text-sm text-mute">${t}</p>`;

  /* seção: card com ícone e contador; sem dado = <details> fechado («sem registro») */
  const secao = (id, icone, titulo, n, corpo, extra = "") => n
    ? `<section id="s-${id}" class="scroll-mt-24 rounded-2xl border border-line bg-card p-5 shadow-sm"><div class="mb-4 flex flex-wrap items-center justify-between gap-3"><h3 class="m-0 flex items-center gap-2 font-display text-lg font-semibold text-ink"><span class="text-blue-600">${ico(icone)}</span>${titulo}${typeof n === "number" ? ` <span class="text-sm font-normal text-mute">· ${nf(n)}</span>` : ""}</h3>${extra}</div>${corpo}</section>`
    : `<details id="s-${id}" class="scroll-mt-24 rounded-2xl border border-dashed border-line bg-card px-5 py-3"><summary class="flex cursor-pointer items-center gap-2 text-sm text-mute"><span>${ico(icone, "sm")}</span><b class="text-ink">${titulo}</b> · sem registro</summary></details>`;
  const kv = (k, v) => `<div class="rounded-xl border border-line px-3 py-2"><div class="text-xs text-mute">${k}</div><div class="mt-0.5 break-words text-sm font-semibold text-ink">${v == null || v === "" ? '<span class="font-normal text-mute">—</span>' : v}</div></div>`;

  function topo(d) {
    const t = d.topo, e = (d.estoque.row || {}), des = d.desenhos.desenho || d.desenhos.projeto, foto = des && des.current && des.current[0];
    const origem = [t.no_catalogo ? badge("Catálogo", "blue") : "", ...t.tipos.map(k => badge(k === "REDESENVOLVIMENTO" ? "Redesenvolvimento" : "Desenvolvimento", k === "REDESENVOLVIMENTO" ? "green" : "amber"))].join(" ");
    const selos = [t.sistema ? badge(SYS[t.sistema] || t.sistema, t.sistema === "gas" ? "blue" : "amber") : "", t.familia ? badge(cap(t.familia), "slate") : "", t.linha ? badge(linha(t.linha), "slate") : "",
      t.hibrido === "S" ? badge("Híbrido/elétrico", "violet") : "", t.lancamento === "S" ? badge("Lançamento", "green") : "", t.classe ? badge("Curva " + t.classe, t.classe === "A" ? "green" : t.classe === "B" ? "blue" : "slate") : "",
      t.situacao ? badge("Estoque: " + SIT[t.situacao][0], SIT[t.situacao][1]) : ""].filter(Boolean).join(" ");
    const img = foto ? `<a href="/desenhos?q=${encodeURIComponent(t.code)}" title="Abrir em Desenhos" class="block h-full"><img src="/api/drawings/thumb/${foto.id}" alt="Desenho ${esc(t.code)}" class="h-full w-full rounded-xl object-cover"></a>`
      : `<div class="flex h-full w-full items-center justify-center rounded-xl bg-thead text-mute">${ico("amortecedor", "xl")}</div>`;
    return `<section class="rounded-2xl border border-line bg-card p-5 shadow-sm"><div class="flex flex-col gap-5 md:flex-row">
      <div class="h-[10rem] w-full shrink-0 md:w-[10rem]">${img}</div>
      <div class="min-w-0 flex-1"><div class="flex flex-wrap items-center gap-2">${origem}</div>
        <div class="mt-2 font-display text-3xl font-bold text-ink">${esc(t.code)}</div><div class="mt-1 text-base text-mute">${esc(t.description || "Sem descrição")}</div>
        <div class="mt-3 flex flex-wrap gap-2">${selos || '<span class="text-sm text-mute">Sem dados de catálogo (item em desenvolvimento).</span>'}</div></div></div>
      <div class="mt-5 grid grid-cols-2 gap-4 lg:grid-cols-4">${kpi("Vendas 12 meses", nf(d.vendas.total_qty || 0), d.vendas.total_value ? brl0(d.vendas.total_value) : "sem venda", "blue", "chart-column")}
        ${kpi("Estoque disponível", nf(e.estoque || 0), e.reservado ? `${nf(e.reservado)} reservado(s) · armazém 04` : "armazém 04", e.situacao === "ruptura" ? "red" : "slate", "warehouse")}
        ${kpi("Cobertura", e.cobertura == null ? "–" : nf(e.cobertura, 1) + " meses", e.media_mensal ? `venda média ${nf(e.media_mensal, 0)}/mês` : "sem venda média", (SIT[e.situacao] || [, "slate"])[1], "gauge")}
        ${kpi("A caminho", nf(e.a_caminho || 0), d.pedidos.rows.length ? `${nf(d.pedidos.rows.length)} linha(s) de pedido` : "sem pedido em aberto", "sky", "ship")}</div></section>`;
  }

  const INDICE = [["dados", "Dados"], ["aplicacoes", "Aplicações"], ["concorrentes", "Concorrentes"], ["vendas", "Vendas"], ["estoque", "Estoque"], ["pedidos", "Pedidos"], ["desenvolvimento", "Desenvolvimento"],
    ["garantia", "Garantia"], ["desenhos", "Desenhos"], ["inmetro", "Inmetro e FOB"], ["brands", "Brands"], ["pendencias", "Pendências"]];

  function item() {
    const code = decodeURIComponent(location.pathname.split("/item/")[1] || "");
    root.innerHTML = TW.esqueleto(8, 4);
    J("/api/item/" + encodeURIComponent(code)).then(d => desenhar(d)).catch(e => { root.innerHTML = TW.notice(`Código <b>${esc(code)}</b> não encontrado no catálogo nem em DES/R-D. ${esc(e.message)}`, "amber"); });
  }

  function desenhar(d) {
    const t = d.topo, m = t.medidas || {}, e = d.estoque.row, ap = d.aplicacoes, cc = d.concorrentes;
    const nAp = ap.catalogo.length + ap.desenvolvimento.length;
    root.innerHTML = `<div class="flex flex-col gap-5">${topo(d)}
      <nav class="sticky top-0 z-20 flex flex-wrap gap-1 rounded-xl border border-line bg-card px-2 py-2 shadow-sm" aria-label="Seções do item">${INDICE.map(([id, l]) => `<a href="#s-${id}" class="rounded-lg px-2.5 py-1 text-xs font-semibold text-ink no-underline hover:bg-slate-500/10">${l}</a>`).join("")}</nav>
      ${secao("dados", "package", "Dados do produto", true, `<div class="grid grid-cols-2 gap-2 md:grid-cols-4 xl:grid-cols-6">${kv("Grupo", esc(t.grupo || ""))}${kv("EAN", esc(t.ean || ""))}${kv("Peso líquido (kg)", t.peso == null ? "" : nf(t.peso, 2))}${kv("NCM", esc(t.ncm || ""))}${kv("IPI", t.ipi == null ? "" : nf(t.ipi, 2) + "%")}
        ${kv("Caixa", esc([t.caixa, t.caixa_dim].filter(Boolean).join(" · ")))}${kv("Lmin (mm)", m.lmin_mm == null ? "" : mm(m.lmin_mm))}${kv("Lmax (mm)", m.lmax_mm == null ? "" : mm(m.lmax_mm))}${kv("Curso (mm)", m.stroke_mm == null ? "" : mm(m.stroke_mm))}
        ${kv("Ø haste (mm)", m.rod_diameter_mm == null ? "" : mm(m.rod_diameter_mm))}${kv("Fixação sup.", esc(m.upper_mount || ""))}${kv("Fixação inf.", esc(m.lower_mount || ""))}</div>
        <p class="mb-0 mt-3 text-xs text-mute">Peso e código de barras do BI03 (Protheus) quando ele tem o item; IPI do servidor. «—» = não consta nas bases.</p>`)}
      ${secao("aplicacoes", "car", "Aplicações e lados", nAp + d.lados.length, `${d.lados.length ? `<div class="mb-3 flex flex-wrap items-center gap-2 text-sm"><b class="text-ink">Par:</b>${d.lados.map(x => `<a href="/item/${encodeURIComponent(x.perfect_code)}" class="font-semibold">${esc(x.perfect_code)}</a> <span class="text-mute">(${esc(x.lado)})</span>`).join(" · ")}</div>` : ""}
        ${TW.table([{ h: "Origem" }, { h: "Montadora" }, { h: "Veículo" }, { h: "Aplicação", nw: false }, { h: "Anos" }, { h: "Eixo / lado" }],
          [...ap.catalogo.map(a => [badge("Catálogo", "blue"), esc(a.make || "–"), esc(a.model || "–"), esc(a.application_text || ""), anos(a), esc([a.axle, a.side].filter(Boolean).join(" · ") || "–")]),
           ...ap.desenvolvimento.map(a => [badge(a.tipo === "REDESENVOLVIMENTO" ? "R-D" : "DES", a.tipo === "REDESENVOLVIMENTO" ? "green" : "amber"), esc(a.make || "–"), esc(a.vehicle || "–"), esc(a.application_text || ""), anos(a), `<span class="text-xs text-mute">${esc(a.status || "")}</span>`])], { h: "max-h-[50vh]" })}`)}
      ${secao("concorrentes", "swords", "Concorrentes e código original", cc.concorrentes.length + cc.oem.length, `<p class="mb-3 mt-0 text-xs text-mute">Fonte: <b>${cc.fonte === "CrossCatalogo" ? "CrossCatalogo.xlsx (catálogo)" : "servidor — DESENVOLVIMENTO_CONCORRENTES"}</b>.</p>
        <div class="grid grid-cols-1 gap-4 lg:grid-cols-2"><div><div class="mb-2 text-xs font-semibold uppercase tracking-wide text-mute">Concorrentes · ${nf(cc.concorrentes.length)}</div><div class="flex flex-wrap gap-2">${cc.concorrentes.map(x => `<span class="rounded-lg border border-line px-2.5 py-1 text-sm"><b class="text-xs text-mute">${esc(x.marca)}</b> <span class="font-semibold text-ink">${esc(x.codigo)}</span></span>`).join("") || vazio("Nenhum.")}</div></div>
        <div><div class="mb-2 text-xs font-semibold uppercase tracking-wide text-mute">Código original (montadora) · ${nf(cc.oem.length)}</div><div class="flex flex-wrap gap-2">${cc.oem.map(x => `<span class="rounded-lg border border-line px-2.5 py-1 text-sm font-semibold text-ink">${esc(x.codigo)}</span>`).join("") || vazio("Nenhum.")}</div></div></div>
        ${d.codigos.length ? `<div class="mt-4 text-sm text-mute"><b class="text-ink">Códigos de fornecedor:</b> ${d.codigos.map(c => `${esc(c.brand || "")} ${esc(c.code)}`).join(" · ")}</div>` : ""}`)}
      ${secao("vendas", "chart-column", "Vendas — últimos 12 meses", !!(d.vendas.available && d.vendas.total_qty), `<div class="flex flex-wrap gap-6 text-sm"><span><b class="font-display text-xl text-ink">${nf(d.vendas.total_qty)}</b> peças</span><span><b class="font-display text-xl text-ink">${brl0(d.vendas.total_value)}</b> faturado</span>${d.vendas.classe ? `<span>${badge("Curva " + d.vendas.classe, "green")} <span class="text-mute">(12 meses fechados, universo do BI)</span></span>` : ""}</div><div id="g-vendas" class="mt-3"></div>`)}
      ${secao("estoque", "warehouse", "Estoque, cobertura e projeção", !!e, e ? `<div class="grid grid-cols-2 gap-2 md:grid-cols-5">${kv("Disponível (arm. 04)", nf(e.estoque))}${kv("Reservado", nf(e.reservado))}${kv("A caminho", nf(e.a_caminho))}${kv("Venda média/mês", nf(e.media_mensal, 1))}${kv("Situação", badge(SIT[e.situacao][0], SIT[e.situacao][1]) + (e.falta_em ? ` <span class="text-xs text-red-600">falta em ${mes(e.falta_em)}${e.antes_de_chegar ? " (antes de chegar)" : ""}</span>` : ""))}</div><div id="g-proj" class="mt-4"></div>` : "")}
      ${secao("pedidos", "ship", "Pedidos em aberto e chegadas previstas", d.pedidos.rows.length, TW.table([{ h: "Pedido" }, { h: "Fornecedor" }, { h: "Etapa" }, { h: "Qtd.", r: true }, { h: "Chegada prevista" }, { h: "Faixa" }, { h: "" }],
        d.pedidos.rows.map(r => [esc(r.pedido), esc(r.fornecedor || "–"), esc(r.etapa || "–"), nf(r.quantidade), r.chegada_prevista ? `<b>${dmy(r.chegada_prevista)}</b>` : "–", r.faixa_de ? `${dmy(r.faixa_de)} – ${dmy(r.faixa_ate)}` : "–",
          (r.alertas || []).map(a => badge(a === "vencida" ? "previsão vencida" : "vai atrasar", a === "vencida" ? "red" : "amber")).join(" ")]), { h: "max-h-[45vh]" }), `<a class="text-sm" href="/pedidos-aberto?pvq=${encodeURIComponent(t.code)}">Abrir em Pedidos em Aberto</a>`)}
      ${secao("desenvolvimento", "amortecedor", "Desenvolvimento e amostras", d.desenvolvimento.rows.length + d.amostras.length, `${d.desenvolvimento.eventos.length ? `<ol class="mb-4 mt-0 flex flex-col gap-2 border-l-2 border-line pl-4">${d.desenvolvimento.eventos.map(v => `<li class="text-sm"><b class="text-ink">${esc(v.para || "–")}</b> <span class="text-mute">← ${esc(v.de || "início")} · ${dmy(v.em)}</span></li>`).join("")}</ol>` : ""}
        ${d.desenvolvimento.rows.length ? TW.table([{ h: "Tipo" }, { h: "Status" }, { h: "Fornecedor" }, { h: "Veículo" }, { h: "Início" }, { h: "Pedido confirmado" }, { h: "Amostra comprada" }, { h: "Amostra enviada" }],
          d.desenvolvimento.rows.map(r => [badge(r.tipo === "REDESENVOLVIMENTO" ? "R-D" : "DES", r.tipo === "REDESENVOLVIMENTO" ? "green" : "amber"), esc(r.status || "–"), esc(r.supplier || "–"), esc([r.make, r.vehicle].filter(Boolean).join(" ") || "–"), dmy(r.data_inicio), dmy(r.pedido_confirmado), dmy(r.amostra_comprada), dmy(r.amostra_enviada)]), { h: "max-h-[40vh]" }) : ""}
        ${d.amostras.length ? `<div class="mt-3 flex flex-wrap gap-2">${d.amostras.map(s => `<span class="rounded-lg border border-line px-2.5 py-1 text-sm">${ico("shopping-cart", "sm")} SC ${esc(s.sc_number || "–")} · ${esc(s.supplier || "")} · <b>${esc(s.stage || "")}</b></span>`).join("")}</div>` : ""}`)}
      ${secao("garantia", "shield-check", "Garantia", !!(d.garantia.available && d.garantia.kpis.pecas), d.garantia.available ? `<div class="flex flex-wrap gap-6 text-sm"><span><b class="font-display text-xl text-ink">${nf(d.garantia.kpis.pecas)}</b> peças</span><span><b class="font-display text-xl text-ink">${nf(d.garantia.kpis.ocorrencias)}</b> ocorrências</span>${d.garantia.kpis.pct_procedente != null ? `<span><b class="font-display text-xl text-ink">${nf(d.garantia.kpis.pct_procedente, 1)}%</b> procedentes</span>` : ""}</div>
        <div class="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2"><div id="g-gar"></div><div class="flex flex-col gap-2">${d.garantia.defeitos.map(x => `<div><div class="flex justify-between gap-2 text-sm"><span class="truncate text-ink">${esc(x.defeito)}</span><b class="tabular-nums">${nf(x.pecas)}</b></div><div class="mt-1 h-1.5 rounded-full bg-thead"><div class="h-1.5 rounded-full bg-amber-500" style="width:${Math.max(2, x.pct)}%"></div></div></div>`).join("")}</div></div>
        <a class="mt-3 inline-block text-sm" href="/garantia?q=${encodeURIComponent(t.code)}&ano=todos">Abrir em Garantia</a>` : "")}
      ${secao("desenhos", "drafting-compass", "Desenhos e projeto", (d.desenhos.desenho ? 1 : 0) + (d.desenhos.projeto ? 1 : 0), `<div class="flex flex-wrap gap-4">${["desenho", "projeto"].filter(k => d.desenhos[k]).map(k => { const x = d.desenhos[k];
          return x.current.map(f => `<a href="/api/drawings/file/${f.id}" target="_blank" rel="noopener" class="block w-[11rem] rounded-xl border border-line p-2 no-underline"><img src="/api/drawings/thumb/${f.id}" alt="" class="h-[7rem] w-full rounded-lg object-cover"><div class="mt-1 truncate text-xs text-ink">${esc(f.filename)}</div><div class="text-xs text-mute">${esc(x.kind_label)} · ${esc(x.label)}</div></a>`).join(""); }).join("")}</div>`)}
      ${secao("inmetro", "selo-inmetro", "Inmetro e FOB", d.inmetro.length + d.fob.length, `<div class="grid grid-cols-1 gap-4 lg:grid-cols-2"><div>${d.inmetro.length ? TW.table([{ h: "Nº Inmetro" }, { h: "Família" }, { h: "Descrição", nw: false }], d.inmetro.map(c => [esc(c.inmetro_number || "–"), esc(c.family || "–"), esc(c.cert_description || "")]), { h: "max-h-[30vh]" }) : vazio("Sem certificado.")}</div>
        <div class="flex flex-col gap-2">${d.fob.map(x => `<div class="flex items-center justify-between rounded-xl border ${x.melhor ? "border-emerald-500 bg-emerald-500/10" : "border-line"} px-4 py-2"><span class="font-semibold text-ink">${esc(x.fornecedor)}</span><span class="font-display text-lg font-bold text-ink">US$ ${nf(x.preco, 2)}</span>${x.melhor ? badge("Melhor preço", "green") : ""}</div>`).join("") || vazio("Sem cotação FOB.")}</div></div>`)}
      ${secao("brands", "tags", "Brands", d.brands.length, `<div class="flex flex-wrap gap-2">${d.brands.map(b => `<span class="rounded-lg border border-line px-2.5 py-1 text-sm"><b class="text-xs text-mute">${esc(b.brand)}</b> <span class="font-semibold text-ink">${esc(b.code)}</span></span>`).join("")}</div>`)}
      ${secao("pendencias", "circle-alert", "Pendências e anomalias", d.pendencias.length + d.anomalias.length, `<div class="flex flex-col gap-2">${d.anomalias.map(a => `<a href="/anomalias?tab=${a.tab}&q=${encodeURIComponent(t.code)}" class="flex items-center gap-2 rounded-xl border border-amber-500 bg-amber-500/10 px-3 py-2 text-sm text-ink no-underline">${ico("triangle-alert", "sm")}${esc(a.texto)}</a>`).join("")}
        ${d.pendencias.map(x => `<div class="rounded-xl border border-line px-3 py-2 text-sm"><b class="text-ink">${esc(x.field || x.kind)}</b> <span class="text-mute">${esc(x.description || "")}</span></div>`).join("")}</div>`)}
    </div>`;
    if (d.vendas.available && d.vendas.total_qty) grafico($("#g-vendas"), { type: "bar", altura: 240, titulo: "Vendas por mês", data: { labels: d.vendas.months.map(x => mes(x.month)), datasets: [{ label: "Peças", data: d.vendas.months.map(x => x.qty) }] },
      options: { plugins: { legend: { display: false }, tooltip: { callbacks: { afterLabel: c => "Faturado: " + brl0(d.vendas.months[c.dataIndex].value) } } } } });
    if (e) grafico($("#g-proj"), { type: "bar", altura: 240, titulo: "Projeção de estoque", data: { labels: d.estoque.meses.map(mes), datasets: [
        { type: "line", label: "Saldo projetado", data: e.projecao, cor: "#2F4A8C", fill: false, order: 0 }, { label: "Chegadas previstas", data: e.chegadas, cor: "#64C4E9", order: 1 }] },
      options: { plugins: { tooltip: { mode: "index", intersect: false } } } });
    if (d.garantia.available && d.garantia.kpis.pecas) grafico($("#g-gar"), { type: "bar", altura: 200, titulo: "Garantia por ano", data: { labels: d.garantia.por_ano.map(x => x.ano), datasets: [{ label: "Peças em garantia", data: d.garantia.por_ano.map(x => x.pecas), cor: "#F6A019" }] }, options: { plugins: { legend: { display: false } } } });
  }
  PSD.tela("item", item);
})();
