/* Tela · Desenvolvimento e Redesenvolvimento (etapa 20 · Q2/Q3/Q4).
   Abre «em andamento» (aplicações que ainda não são ITEM RECEBIDO); a esteira de estágios (sem setas) troca o estágio; o quadro de sub status mostra
   tudo o que o servidor manda, por coluna, contado no estágio escolhido. Nada é marcado à mão: só o servidor decide.
   Curtidos primeiro (desempate: status mais avançado). Filtros na URL. Detalhe do item: clique no código (data-rd → PSD.rdOpen, no núcleo). */
(function () {
  const { $, esc, J, lnk, root, fail, dwFill } = PSD;
  const TW = window.PSDTW, { nf, badge, kpi, notice } = TW;
  const CHAVES = ["q", "status", "sub", "flag", "curtiu", "supplier", "catalog", "sample", "ordem"];
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
      <p class="m-0 text-sm text-mute">${k === "des" ? "DESENVOLVIMENTO = item novo em desenvolvimento." : "REDESENVOLVIMENTO = item do catálogo com outro fornecedor."} Um código = um item (pode ter várias aplicações). Tudo vem do servidor SQL, atualizado todo dia. <b>Curtidos aparecem primeiro.</b></p>
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

    const CURT = { sim: "Curtidos ▲", sem: "Sem curtida", nao: "Com «não curtiu» ▼" }, CAT = { sim: "Já no catálogo", nao: "Fora do catálogo" }, AMO = { comprada: "Comprada", enviada: "Enviada", nenhuma: "Sem amostra" }, ORD = { status: "Status mais avançado", codigo: "Código" };
    const NOMES = { status: "Estágio", sub: "Sub status", flag: "Pendência", supplier: "Fornecedor", curtiu: "Curtidas", catalog: "Catálogo", sample: "Amostra", ordem: "Ordem", q: "Busca" };
    const subNome = v => { const [kk, ...r] = v.split(":"), g = (fc.subs.find(x => x.key === kk) || {}).label || kk; return `${g} · ${r.join(":")}`; };
    let maisAberto = false;
    const desenharFiltros = () => {
      const s = F.get(), e = fc.etapa;
      const val = (kk, v) => kk === "status" ? nomeEstagio(v) : kk === "sub" ? subNome(v) : kk === "flag" ? (PSD.FLG[v] ? PSD.FLG[v][0] : v) : ({ curtiu: CURT, catalog: CAT, sample: AMO, ordem: ORD }[kk] || {})[v] || v;
      TW.pintarBarra($("#rbar"), {
        busca: { valor: s.q, ph: "Código, descrição, veículo, fornecedor…" },
        principais: [{ k: "supplier", rotulo: "Fornecedor", tipo: "lista", atual: s.supplier || "", opcoes: [{ v: "", l: "Todos" }, ...TW.ops(fc.supplier)] }],
        mais: [{ k: "curtiu", rotulo: "Curtidas", atual: s.curtiu || "", opcoes: [{ v: "sim", l: CURT.sim, n: e.curtidos }, { v: "sem", l: CURT.sem }, { v: "nao", l: CURT.nao, n: e.nao_curtidos }] },
               { k: "catalog", rotulo: "Catálogo", atual: s.catalog || "", opcoes: Object.entries(CAT).map(([v, l]) => ({ v, l })) },
               { k: "sample", rotulo: "Amostra", atual: s.sample || "", opcoes: Object.entries(AMO).map(([v, l]) => ({ v, l })) },
               { k: "ordem", rotulo: "Ordenar por (padrão: mais curtidos)", atual: s.ordem || "", opcoes: Object.entries(ORD).map(([v, l]) => ({ v, l })) }],
        aberto: maisAberto,
        atalhos: [{ k: "flag", v: "pend_compras", l: "Pendente compras", n: fc.flags.pend_compras, on: s.flag === "pend_compras", forte: true }, { k: "curtiu", v: "sim", l: "▲ Curtidos", n: e.curtidos, on: s.curtiu === "sim" }],
        etiquetas: TW.etiquetas(s, NOMES, val),
        acoes: TW.botao("Baixar Excel", { href: `/api/export/${slug}.xlsx?${api(s)}`, icone: "download" })
      });
    };
    const botaoEstagio = (v, t, n, l, cls = "") => `<button type="button" data-est="${esc(v)}" class="${cls}" aria-pressed="${estagio(F.get()) === v}"><span class="t">${esc(t)}</span><span class="n">${nf(n)}</span><span class="l">${nf(l)} aplicaç${l === 1 ? "ão" : "ões"}</span></button>`;
    const desenharEstagios = () => {
      const est = [...fc.esteira].sort((a, b) => STATUS_ORDEM.indexOf(a.v) - STATUS_ORDEM.indexOf(b.v)), rec = est.find(x => x.v === RECEBIDO);
      $("#rest").innerHTML = botaoEstagio(ANDAMENTO, "Em andamento", fc.andamento.n, fc.andamento.l, "soma") +
        est.filter(x => x.v !== RECEBIDO).map(x => botaoEstagio(x.v, x.v, x.n, x.l)).join("") +
        (rec ? botaoEstagio(RECEBIDO, "Item recebido", rec.n, rec.l, "fim") : "") + botaoEstagio(TODOS, "Todos", fc.total, fc.lines);
    };
    const desenharSubs = () => {
      const s = F.get(), grupos = fc.subs.filter(g => g.values.length);
      $("#rsubt").textContent = `contagem em «${nomeEstagio(estagio(s))}» · itens e aplicações · clique para filtrar`;
      $("#rsub").innerHTML = grupos.length ? grupos.map(g => `<div class="psd-sub"><h4>${esc(g.label)}</h4>${g.values.map(x => { const v = `${g.key}:${x.v}`;
        return `<button type="button" data-sub="${esc(v)}" aria-pressed="${s.sub === v}" title="${nf(x.n)} item(ns) · ${nf(x.l)} aplicação(ões)"><i class="psd-sd ${tom(x.v)}"></i><span class="v">${esc(x.v)}</span><span class="n">${nf(x.n)}</span><span class="l">${nf(x.l)} apl.</span></button>`; }).join("")}</div>`).join("")
        : `<div class="text-sm text-mute">Nenhum sub status neste estágio.</div>`;
    };
    const desenharKpis = () => {
      const rec = fc.esteira.find(x => x.v === RECEBIDO) || { n: 0, l: 0 }, a = fc.andamento;
      $("#rk").innerHTML = kpi(k === "des" ? "Em desenvolvimento" : "Em redesenvolvimento", nf(a.n), `${nf(a.l)} aplicações em andamento`, "blue") +
        kpi("Curtidos ▲", nf(a.curtidos), a.n ? `${nf(100 * a.curtidos / a.n, 0)}% dos itens em andamento` : "", "green") +
        kpi("Pendente compras", nf(fc.flags.pend_compras || 0), "atalho na barra de filtros", "amber") +
        kpi("Item recebido", nf(rec.n), `${nf(rec.l)} aplicações · fim do ciclo`, "slate");
    };

    const carregar = async () => {
      const s = F.get(), qs = api(s) + "&page=" + pg;
      $("#rt").innerHTML = `<div class="rounded-2xl border border-line bg-card px-5 py-8 text-sm text-mute">Carregando…</div>`;
      try {
        const d = await J(`/api/rd/${k}?` + qs), pages = Math.max(1, Math.ceil(d.total / d.size)), ativos = Object.keys(s).filter(x => x !== "ordem").length;
        $("#rmeta").innerHTML = `<b class="text-ink">${nf(d.total)}</b> item(ns) em «${esc(nomeEstagio(estagio(s)))}»${ativos ? ` · ${ativos} filtro(s) ativo(s)` : ""}`;
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
    /* `estagioMudou`: os contadores do quadro de sub status dependem do estágio → busca de novo */
    const aplicar = async (patch, logo = false) => {
      const antes = estagio(F.get()); if (patch) F.set(patch); pg = 1;
      if (estagio(F.get()) !== antes) { try { await facetas(); } catch (e) { return fail(e); } }
      desenharFiltros(); desenharEstagios(); desenharSubs(); clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 250);
    };

    TW.ligarBarra($("#rbar"), { set: (kk, v) => aplicar({ [kk]: v }, true), busca: t => aplicar({ q: t }, true), limpar: () => { const a = estagio(F.get()); F.clear(); if (a !== ANDAMENTO) facetas().then(() => aplicar(null, true), fail); else aplicar(null, true); }, mais: ab => { maisAberto = ab; } });
    $("#rest").addEventListener("click", e => { const b = e.target.closest("[data-est]"); if (!b) return; const v = b.dataset.est;
      aplicar({ status: v === ANDAMENTO ? "" : v, sub: "" }, true); });         // trocar de estágio limpa o sub status (o valor pode não existir no outro estágio)
    $("#rsub").addEventListener("click", e => { const b = e.target.closest("[data-sub]"); if (!b) return; const v = b.dataset.sub; aplicar({ sub: F.get().sub === v ? "" : v }, true); });
    $("#rp").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; carregar(); scrollTo(0, 0); } });

    const facetas = async () => { const st = estagio(F.get()); fc = await J(`/api/rd/${k}/facets?status=${encodeURIComponent(st === TODOS ? "" : st)}`); desenharKpis(); };
    facetas().then(() => aplicar(null, true)).catch(fail);
  }
  PSD.tela("desenvolvimento", () => rdPage("des"));
  PSD.tela("redesenvolvimento", () => rdPage("rd"));
})();
