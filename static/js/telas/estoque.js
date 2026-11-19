/* Tela · Estoque — vendas × estoque (etapa 16 · C2–C5), visual Tailwind.
   Venda média = 12 meses fechados ÷ 12 · estoque = armazém 04 − reservado · a caminho = pedidos em aberto sem os parados · cobertura = (estoque + a caminho) ÷ média.
   Atalhos de situação (ruptura, risco, OK, excesso, sem giro) e classe ABC: cada número = linhas da lista ao clicar (estoque.listing · counts). Filtros na URL e lembrados; Excel com os filtros. */
(function () {
  const { $, esc, J, qs, root, fail } = PSD;
  const TW = window.PSDTW, { nf, brl0, badge, kpi, notice, empty } = TW;
  const SIT = { ruptura: ["Ruptura", "red", "vende e está sem estoque"], risco: ["Risco", "amber", "cobertura abaixo do lead time"], ok: ["OK", "green", "cobertura adequada"], excesso: ["Excesso", "violet", "cobertura acima de 18 meses"], sem_giro: ["Sem giro", "slate", "estoque sem venda em 12 meses"] };
  const pager = (pg, pages) => { const b = (p, dis, l) => `<button type="button" data-p="${p}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${dis ? "disabled" : ""}>${l}</button>`;
    return pages > 1 ? `${b(pg - 1, pg < 2, "‹")} Página ${pg} de ${pages} ${b(pg + 1, pg >= pages, "›")}` : ""; };
  const mesAno = s => s ? `${s.slice(5, 7)}/${s.slice(0, 4)}` : "–";
  // barra da cobertura: escala até 24 meses, com as marcas de risco e excesso
  const barra = (c, L) => { if (c == null) return '<span class="text-mute">–</span>'; const w = Math.min(100, c / 24 * 100), cor = c < L.risco ? "bg-amber-500" : c <= L.excesso ? "bg-emerald-500" : "bg-violet-500";
    return `<div class="flex items-center gap-2"><div class="relative h-2 w-28 rounded-full bg-slate-500/15"><span class="absolute inset-y-0 left-0 rounded-full ${cor}" style="width:${w}%"></span></div><span class="tabular-nums text-ink">${nf(c, 1)}</span></div>`; };

  // «Falta em»: mês da 1ª projeção negativa; a dica mostra o saldo e as chegadas de cada mês
  const falta = (r, M) => { const tip = M.map((m, i) => `${mesAno(m + "-01")}: ${r.chegadas[i] ? "+" + nf(r.chegadas[i]) + " chega · " : ""}saldo ${nf(r.projecao[i])}`).join("\n");
    return r.falta_em ? `<span title="${esc(tip)}">${badge(mesAno(r.falta_em + "-01"), "red")}${r.antes_de_chegar ? ' <span class="text-xs text-mute">antes de chegar</span>' : ""}</span>` : `<span class="text-mute" title="${esc(tip)}">não falta</span>`; };

  function estoque() {
    const F = TW.filtros("estoque", ["situacao", "classe", "falta", "q"]); let pg = 1, d = null, timer;
    root.innerHTML = `<div class="flex flex-col gap-5">
      <div id="ek" class="grid grid-cols-2 gap-4 lg:grid-cols-4"></div><p id="en" class="m-0 text-sm text-mute"></p>
      <div id="eq"></div>
      <div id="em" class="text-sm text-mute"></div><div id="et"></div><div id="ep" class="flex items-center justify-center gap-3 text-sm text-mute"></div></div>`;
    const desenhar = () => {
      const s = F.get(), c = d.counts, k = d.kpis, L = d.limites;
      $("#ek").innerHTML = kpi("Itens", nf(k.itens), "com venda ou estoque", "blue") + kpi(`Estoque disponível (arm. ${d.armazem})`, nf(k.estoque), "peças, sem o reservado", "green")
        + kpi("A caminho", nf(k.a_caminho), "pedidos em aberto, sem os parados", "slate") + kpi("Cobertura", k.cobertura == null ? "–" : nf(k.cobertura, 1) + " meses", `venda média ${nf(k.venda_mes, 0)} peças/mês`, "amber");
      const [ay, am] = d.janela.ate.split("-").map(Number), ult = am === 1 ? `12/${ay - 1}` : `${String(am - 1).padStart(2, "0")}/${ay}`;
      $("#en").innerHTML = `Venda média: ${mesAno(d.janela.de)} a ${ult} (12 meses fechados; o mês atual fica de fora) · risco abaixo de <b class="text-ink">${nf(L.risco, 1)} meses</b> (meta de lead time) · excesso acima de <b class="text-ink">${L.excesso} meses</b>.`;
      /* barra (etapa 19 · Q6): Situação, Classe ABC e «Falta em» à vista; atalhos Ruptura e Vai faltar */
      const cls = Object.keys(c.classe).sort(), clsL = x => x === "—" ? "Sem venda" : "Classe " + x, FALTA = `Vai faltar em ${d.meses.length} meses`;
      TW.pintarBarra($("#eq"), {
        busca: { valor: s.q, ph: "Código ou descrição…" },
        principais: [{ k: "situacao", rotulo: "Situação", tipo: "lista", atual: s.situacao || "", opcoes: [{ v: "", l: "Todas" }, ...Object.entries(SIT).map(([key, [l]]) => ({ v: key, l, n: c.situacao[key] }))] },
                     { k: "classe", rotulo: "Classe", tipo: "lista", atual: s.classe || "", opcoes: [{ v: "", l: "Todas" }, ...cls.map(x => ({ v: x, l: clsL(x), n: c.classe[x] }))] },
                     { k: "falta", rotulo: "Falta em", tipo: "lista", atual: s.falta || "", opcoes: [{ v: "", l: "Todos" }, { v: "1", l: FALTA, n: c.falta }] }],
        atalhos: [{ k: "situacao", v: "ruptura", l: "Ruptura", n: c.situacao.ruptura, on: s.situacao === "ruptura", forte: true }, { k: "falta", v: "1", l: FALTA, n: c.falta, on: s.falta === "1", forte: true }],
        etiquetas: TW.etiquetas(s, { situacao: "Situação", classe: "Classe", falta: "Projeção", q: "Busca" }, (kk, v) => kk === "situacao" ? SIT[v][0] : kk === "classe" ? clsL(v) : kk === "falta" ? FALTA : v),
        acoes: TW.botao("Baixar Excel", { href: `/api/export/estoque.xlsx?${qs(s)}`, icone: "download" })
      });
      const n = ["situacao", "classe", "falta", "q"].filter(x => s[x]).length;
      $("#em").innerHTML = `<b class="text-ink">${nf(d.total)}</b> item(ns)${n ? ` · ${n} filtro(s) ativo(s)` : ""} · ${nf(c.antes_de_chegar)} com pedido a caminho que chega tarde · saldo mês a mês = estoque + chegadas previstas − venda média (${mesAno(d.meses[0] + "-01")} a ${mesAno(d.meses[d.meses.length - 1] + "-01")})`;
      $("#et").innerHTML = d.rows.length ? TW.table([{ h: "Código" }, { h: "Descrição" }, { h: "Situação" }, { h: "Classe" }, { h: "Venda 12 m", r: true }, { h: "Média/mês", r: true }, { h: "Estoque", r: true }, { h: "A caminho", r: true }, { h: "Cobertura (meses)" }, { h: "Falta em" }, { h: "Valor 12 m", r: true }],
          d.rows.map(r => [window.psdCode ? psdCode(r.codigo) : `<b>${esc(r.codigo)}</b>`, r.descricao ? `<span class="block max-w-[18rem] truncate" title="${esc(r.descricao)}">${esc(r.descricao)}</span>` : '<span class="text-mute">–</span>',
            badge(SIT[r.situacao][0], SIT[r.situacao][1]), esc(r.classe), nf(r.venda_12m), nf(r.media_mensal, 1), nf(r.estoque), r.a_caminho ? nf(r.a_caminho) : '<span class="text-mute">–</span>', barra(r.cobertura, L), falta(r, d.meses), brl0(r.valor_12m)]), { h: "max-h-[65vh]" })
        : empty("Nenhum item com estes filtros.");
      $("#ep").innerHTML = pager(pg, Math.max(1, Math.ceil(d.total / d.size)));
    };
    const carregar = async () => { try { d = await J("/api/estoque?" + qs({ ...F.get(), page: pg })); } catch (e) { $("#et").innerHTML = notice(esc(e.message), "red"); return; } desenhar(); };
    const aplicar = (patch, logo) => { if (patch) F.set(patch); pg = 1; clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 300); };
    TW.ligarBarra($("#eq"), { set: (k, v) => aplicar({ [k]: v }, true), busca: t => aplicar({ q: t }, true), limpar: () => { F.clear(); aplicar(null, true); } });
    root.addEventListener("click", e => { const p = e.target.closest("[data-p]"); if (p && !p.disabled) { pg = +p.dataset.p; carregar(); scrollTo(0, 0); } });
    $("#et").innerHTML = '<p class="text-sm text-mute">Calculando vendas × estoque…</p>';
    carregar().catch(fail);
  }
  PSD.tela("estoque", estoque);
})();
