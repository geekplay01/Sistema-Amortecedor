/* Tela · Desenvolvimento e Redesenvolvimento (etapa 20 · Q2/Q3/Q4; etapa 21: chave de linha, marca, itens = linhas do servidor).
   Chave de linha no topo (família do servidor: amortecedor · moto · linha pesada). Abre «em andamento» (aplicações que ainda não são ITEM RECEBIDO);
   a esteira de estágios troca o estágio; o quadro de sub status mostra o que o servidor manda, por coluna, no estágio escolhido — negociação e vendas
   ficam em «Mais filtros». Itens = linhas do servidor (como o sistema PERFECT conta); a lista agrupa por código. Nada é marcado à mão.
   Curtidos primeiro (desempate: status mais avançado). Filtros na URL. Detalhe do item: clique no código (data-rd → PSD.rdOpen, no núcleo).
   As regras da tela ficam em Configurações › Regras das telas. */
(function () {
  const { $, esc, J, lnk, root, fail, dwFill } = PSD;
  const TW = window.PSDTW, { nf, badge, kpi, notice } = TW;
  const CHAVES = ["linha", "q", "status", "sub", "flag", "curtiu", "supplier", "marca", "negociacao", "vendas", "controladoria", "catalog", "sample", "ordem"];
  const MAIS_SUBS = ["negociacao", "vendas"];         // sub status que saem do quadro e vão para «Mais filtros»
  const STATUS_ORDEM = ["PENDENTE COD. PERFECT", "PENDENTE PARTNUMBER FORNECEDOR", "PENDENTE CONFIRMAÇÃO", "EM COTAÇÃO", "PEDIDO CONFIRMADO", "FINALIZANDO CIT", "ITEM RECEBIDO"];
  const TOM = { "ITEM RECEBIDO": "green", "FINALIZANDO CIT": "blue", "PEDIDO CONFIRMADO": "violet", "EM COTAÇÃO": "amber" };
  const ANDAMENTO = "andamento", TODOS = "todos", RECEBIDO = "ITEM RECEBIDO";
  const curtidas = r => `<span class="whitespace-nowrap tabular-nums"><span class="${r.curtiu ? "font-bold text-emerald-600" : "text-mute"}" title="Curtiu">▲ ${r.curtiu || 0}</span> <span class="${r.nao_curtiu ? "font-bold text-red-600" : "text-mute"}" title="Não curtiu">▼ ${r.nao_curtiu || 0}</span></span>`;
  const statusCell = s => (s || "").split(" · ").filter(Boolean).map(x => badge(x, TOM[x] || "slate")).join(" ") || "–";
  const clip = (t, w = "max-w-[16rem]") => t ? `<span class="block truncate ${w}" title="${esc(t)}">${esc(t)}</span>` : '<span class="text-mute">–</span>';
  /* bolinha do sub status: finalizado = verde · reprovado = vermelho · o resto (pendente…) = laranja */
  const tom = v => /REPROVAD/.test(v) ? "no" : /FINALIZAD|CONCLU|APROVAD/.test(v) ? "ok" : "";
  const subCell = subs => { const vs = [...new Map((subs || []).map(x => [x.v, x])).values()];
    return vs.length ? `<div class="psd-sublist">${vs.map(x => `<span title="Sub status ${esc(x.l.toLowerCase())}"><i class="psd-sd ${tom(x.v)}"></i>${esc(x.v)}</span>`).join("")}</div>` : '<span class="text-mute">–</span>'; };

  function rdPage(k) {
    const slug = k === "des" ? "desenvolvimento" : "redesenvolvimento";
    const F = TW.filtros(slug, CHAVES); let pg = 1, fc = null, timer;
    root.innerHTML = `<div class="flex flex-col gap-5">
      <section aria-label="Linha"><div id="rlin" class="psd-est psd-linha" role="group" aria-label="Linha do produto"></div></section>
      <div id="rk" class="grid grid-cols-2 gap-4 lg:grid-cols-4"></div>
      <section aria-label="Estágios"><div class="mb-2 text-xs font-semibold uppercase tracking-wide text-mute">Estágio</div><div id="rest" class="psd-est"></div></section>
      <div id="rbar"></div>
      <section aria-label="Sub status do servidor"><div class="mb-2 flex flex-wrap items-baseline justify-between gap-2"><span class="text-xs font-semibold uppercase tracking-wide text-mute">Sub status do servidor</span><span id="rsubt" class="text-xs text-mute"></span></div><div id="rsub" class="psd-subs"></div></section>
      <div id="rmeta" class="text-sm text-mute"></div>
      <div id="rt"></div><div id="rp" class="flex items-center justify-center gap-3 text-sm text-mute"></div>
    </div>`;

    /* estágio efetivo: vazio na URL = em andamento; «todos» = sem filtro de estágio */
    const estagio = s => s.status || ANDAMENTO;
    const api = s => { const o = { ...s, status: estagio(s) === TODOS ? "" : estagio(s) }; return new URLSearchParams(o).toString(); };
    const nomeEstagio = v => v === ANDAMENTO ? "Em andamento" : v === TODOS ? "Todos os estágios" : v;
    /* o que muda os contadores (facetas): estágio, linha e marca */
    const chaveFc = s => [estagio(s), s.linha || "", s.marca || ""].join("|");

    const CURT = { sim: "Curtidos ▲", sem: "Sem curtida", nao: "Com «não curtiu» ▼" }, CAT = { sim: "Já no catálogo", nao: "Fora do catálogo" }, AMO = { comprada: "Comprada", enviada: "Enviada", nenhuma: "Sem amostra" }, ORD = { status: "Status mais avançado", codigo: "Código" };
    const NOMES = { status: "Estágio", sub: "Sub status", flag: "Pendência", supplier: "Fornecedor", curtiu: "Curtidas", marca: "Marca", negociacao: "Negociação", vendas: "Vendas", controladoria: "Controladoria", catalog: "Catálogo", sample: "Amostra", ordem: "Ordem", q: "Busca" };
    const subVal = (kk, f) => { const g = fc.subs.find(x => x.key === kk) || { values: [] }, x = g.values.find(y => (y.f || y.v) === f); return x ? x.v : f.replace(/^@/, ""); };
    const subNome = v => { const [kk, ...r] = v.split(":"), g = (fc.subs.find(x => x.key === kk) || {}).label || kk; return `${g} · ${subVal(kk, r.join(":"))}`; };
    const linNome = v => (fc.familias.find(x => x.v === v) || { t: v }).t;
    const marcaNome = v => v === "todas" ? "Todas as marcas" : v;
    let maisAberto = false;
    const desenharFiltros = () => {
      const s = F.get(), e = fc.etapa;
      const val = (kk, v) => kk === "status" ? nomeEstagio(v) : kk === "sub" ? subNome(v) : kk === "linha" ? linNome(v) : kk === "marca" ? marcaNome(v) : MAIS_SUBS.includes(kk) ? subVal(kk, v) : kk === "controladoria" ? "Pendente controladoria"
        : kk === "flag" ? (PSD.FLG[v] ? PSD.FLG[v][0] : v) : ({ curtiu: CURT, catalog: CAT, sample: AMO, ordem: ORD }[kk] || {})[v] || v;
      const subOps = kk => ((fc.subs.find(g => g.key === kk) || {}).values || []).map(x => ({ v: x.f || x.v, l: x.v, n: x.l }));
      const padrao = fc.marca_padrao, marcas = fc.marcas.filter(x => x.v !== "(SEM MARCA)");
      const marcaOps = padrao === "TODAS" ? marcas.map(x => ({ v: x.v, l: x.v, n: x.l }))
        : [{ v: "todas", l: "Todas as marcas", n: fc.marcas.reduce((a, x) => a + x.l, 0) }, ...marcas.filter(x => x.v !== padrao).map(x => ({ v: x.v, l: x.v, n: x.l }))];
      TW.pintarBarra($("#rbar"), {
        busca: { valor: s.q, ph: "Código, descrição, veículo, fornecedor…" },
        principais: [{ k: "supplier", rotulo: "Fornecedor", tipo: "lista", atual: s.supplier || "", opcoes: [{ v: "", l: "Todos" }, ...TW.ops(fc.supplier)] }],
        mais: [{ k: "curtiu", rotulo: "Curtidas", atual: s.curtiu || "", opcoes: [{ v: "sim", l: CURT.sim, n: e.curtidos_l }, { v: "sem", l: CURT.sem }, { v: "nao", l: CURT.nao, n: e.nao_curtidos_l }] },
               { k: "negociacao", rotulo: "Negociação", atual: s.negociacao || "", opcoes: subOps("negociacao") },
               { k: "vendas", rotulo: "Vendas", atual: s.vendas || "", opcoes: subOps("vendas") },
               ...(k === "des" ? [{ k: "controladoria", rotulo: "Controladoria", atual: s.controladoria || "", opcoes: [{ v: "1", l: "Pendente controladoria", n: fc.controladoria }] }] : []),
               { k: "marca", rotulo: padrao === "TODAS" ? "Marca" : `Marca (padrão: ${padrao}, como no sistema PERFECT)`, atual: s.marca || "", opcoes: marcaOps },
               { k: "catalog", rotulo: "Catálogo", atual: s.catalog || "", opcoes: Object.entries(CAT).map(([v, l]) => ({ v, l })) },
               { k: "sample", rotulo: "Amostra", atual: s.sample || "", opcoes: Object.entries(AMO).map(([v, l]) => ({ v, l })) },
               { k: "ordem", rotulo: "Ordenar por (padrão: mais curtidos)", atual: s.ordem || "", opcoes: Object.entries(ORD).map(([v, l]) => ({ v, l })) }],
        aberto: maisAberto,
        atalhos: [{ k: "flag", v: "pend_compras", l: "Pendente compras", n: fc.flags.pend_compras, on: s.flag === "pend_compras", forte: true }, { k: "curtiu", v: "sim", l: "▲ Curtidos", n: e.curtidos_l, on: s.curtiu === "sim" }],
        etiquetas: TW.etiquetas(s, NOMES, val),
        acoes: TW.botao("Baixar Excel", { href: `/api/export/${slug}.xlsx?${api(s)}`, icone: "download" })
      });
    };
    /* contagem principal = itens (linhas do servidor, como o sistema PERFECT); embaixo, os códigos distintos */
    const cod = n => `${nf(n)} código${n === 1 ? "" : "s"}`;
    const botaoEstagio = (v, t, n, l, cls = "") => `<button type="button" data-est="${esc(v)}" class="${cls}" aria-pressed="${estagio(F.get()) === v}"><span class="t">${esc(t)}</span><span class="n">${nf(l)}</span><span class="l">${cod(n)}</span></button>`;
    const desenharLinhas = () => {
      const atual = fc.linha;
      $("#rlin").innerHTML = fc.familias.map(x => `<button type="button" data-lin="${esc(x.v)}" aria-pressed="${x.v === atual}" title="${nf(x.l)} itens em andamento · ${cod(x.n)}"><span class="t">${esc(x.t)}</span><span class="n">${nf(x.l)}</span></button>`).join("");
    };
    const desenharEstagios = () => {
      const est = [...fc.esteira].sort((a, b) => STATUS_ORDEM.indexOf(a.v) - STATUS_ORDEM.indexOf(b.v)), rec = est.find(x => x.v === RECEBIDO);
      $("#rest").innerHTML = botaoEstagio(ANDAMENTO, "Em andamento", fc.andamento.n, fc.andamento.l, "soma") +
        est.filter(x => x.v !== RECEBIDO).map(x => botaoEstagio(x.v, x.v, x.n, x.l)).join("") +
        (rec ? botaoEstagio(RECEBIDO, "Item recebido", rec.n, rec.l, "fim") : "") + botaoEstagio(TODOS, "Todos", fc.total, fc.lines);
    };
    const desenharSubs = () => {
      const s = F.get(), grupos = fc.subs.filter(g => g.values.length && !MAIS_SUBS.includes(g.key));
      $("#rsubt").textContent = `contagem em «${nomeEstagio(estagio(s))}» · itens (códigos) · clique para filtrar · negociação e vendas em «Mais filtros»`;
      $("#rsub").innerHTML = grupos.length ? grupos.map(g => `<div class="psd-sub"><h4>${esc(g.label)}</h4>${g.values.map(x => { const v = `${g.key}:${x.f || x.v}`, on = s.sub === v;
        return `<button type="button" data-sub="${esc(v)}" aria-pressed="${on}" ${!x.l && !on ? 'class="zero"' : ""} title="${nf(x.l)} item(ns) · ${cod(x.n)}"><i class="psd-sd ${tom(x.v)}"></i><span class="v">${esc(x.v)}</span><span class="n">${nf(x.l)}</span><span class="l">${nf(x.n)} cód.</span></button>`; }).join("")}</div>`).join("")
        : `<div class="text-sm text-mute">Nenhum sub status neste estágio.</div>`;
    };
    const desenharKpis = () => {
      const rec = fc.esteira.find(x => x.v === RECEBIDO) || { n: 0, l: 0 }, a = fc.andamento;
      $("#rk").innerHTML = kpi(k === "des" ? "Em desenvolvimento" : "Em redesenvolvimento", nf(a.l), `itens em andamento · ${cod(a.n)}`, "blue") +
        kpi("Curtidos ▲", nf(a.curtidos_l), a.l ? `${nf(100 * a.curtidos_l / a.l, 0)}% dos itens em andamento` : "", "green") +
        kpi("Pendente compras", nf(fc.flags.pend_compras || 0), "códigos · atalho na barra de filtros", "amber") +
        kpi("Item recebido", nf(rec.l), `${cod(rec.n)} · fim do ciclo`, "slate");
    };

    const carregar = async () => {
      const s = F.get(), qs = api(s) + "&page=" + pg;
      $("#rt").innerHTML = `<div class="rounded-2xl border border-line bg-card px-5 py-8 text-sm text-mute">Carregando…</div>`;
      try {
        const d = await J(`/api/rd/${k}?` + qs), pages = Math.max(1, Math.ceil(d.total / d.size)), ativos = Object.keys(s).filter(x => x !== "ordem" && x !== "linha").length;
        $("#rmeta").innerHTML = `<b class="text-ink">${nf(d.linhas)}</b> item(ns) · ${cod(d.total)} em «${esc(nomeEstagio(estagio(s)))}» · ${esc(linNome(fc.linha))}${fc.marca !== "TODAS" ? ` · marca ${esc(fc.marca)}` : ""}${ativos ? ` · ${ativos} filtro(s) ativo(s)` : ""}`;
        const cols = [{ h: "Código" }, { h: "Curtidas" }, { h: "Status" }, { h: "Sub status", nw: false }, { h: "Aplic.", r: true }, { h: "Descrição" },
          { h: "Montadora(s)" }, { h: "Veículo(s)" }, { h: "Fornecedor" }, { h: "Amostra" }, { h: "Catálogo" }, { h: "Desenho" }];
        $("#rt").innerHTML = TW.table(cols, d.rows.map(r => [`<a href="#" class="font-semibold text-blue-600" data-rd="${k}" data-code="${esc(r.code)}">${esc(r.code)}</a>`,
          curtidas(r), statusCell(r.statuses), subCell(r.subs), nf(r.n_rows), clip(r.description, "max-w-[18rem]"), clip(r.makes, "max-w-[10rem]"), clip(r.vehicles), clip(r.suppliers, "max-w-[8rem]"),
          r.sent ? `enviada ${TW.dmy(r.sent)}` : r.bought ? `comprada ${TW.dmy(r.bought)}` : '<span class="text-mute">–</span>', r.product_id ? lnk(r.product_id, "ficha") : '<span class="text-mute">–</span>', `<span data-dw="${esc(r.code)}"></span>`]),
          { h: "max-h-[65vh]" });
        dwFill($("#rt"));
        $("#rp").innerHTML = pages > 1 ? `<button type="button" data-p="${pg - 1}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button type="button" data-p="${pg + 1}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
      } catch (e) { $("#rt").innerHTML = notice(esc(e.message), "red"); }
    };
    /* estágio, linha e marca mudam os contadores (quadro de sub status, esteira, chave de linha) → busca as facetas de novo */
    const aplicar = async (patch, logo = false) => {
      const antes = chaveFc(F.get()); if (patch) F.set(patch); pg = 1;
      if (chaveFc(F.get()) !== antes) { try { await facetas(); } catch (e) { return fail(e); } }
      desenharLinhas(); desenharFiltros(); desenharEstagios(); desenharSubs(); clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 250);
    };

    TW.ligarBarra($("#rbar"), { set: (kk, v) => aplicar({ [kk]: v }, true), busca: t => aplicar({ q: t }, true), limpar: () => { const a = chaveFc(F.get()); F.clear(); if (a !== chaveFc(F.get())) facetas().then(() => aplicar(null, true), fail); else aplicar(null, true); }, mais: ab => { maisAberto = ab; } });
    $("#rlin").addEventListener("click", e => { const b = e.target.closest("[data-lin]"); if (!b) return; const v = b.dataset.lin;
      aplicar({ linha: v === "amortecedor" ? "" : v, sub: "", negociacao: "", vendas: "" }, true); });     // os valores de sub status mudam de uma linha para outra
    $("#rest").addEventListener("click", e => { const b = e.target.closest("[data-est]"); if (!b) return; const v = b.dataset.est;
      aplicar({ status: v === ANDAMENTO ? "" : v, sub: "" }, true); });         // trocar de estágio limpa o sub status (o valor pode não existir no outro estágio)
    $("#rsub").addEventListener("click", e => { const b = e.target.closest("[data-sub]"); if (!b) return; const v = b.dataset.sub; aplicar({ sub: F.get().sub === v ? "" : v }, true); });
    $("#rp").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; carregar(); scrollTo(0, 0); } });

    const facetas = async () => { const s = F.get(), st = estagio(s); fc = await J(`/api/rd/${k}/facets?` + new URLSearchParams({ status: st === TODOS ? "" : st, linha: s.linha || "", marca: s.marca || "" })); desenharKpis(); };
    facetas().then(() => aplicar(null, true)).catch(fail);
  }
  PSD.tela("desenvolvimento", () => rdPage("des"));
  PSD.tela("redesenvolvimento", () => rdPage("rd"));
})();
