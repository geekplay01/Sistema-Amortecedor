/* Tela · Guia visual (/guia-visual, fora do menu) — etapa 17 · Q32: mostra a base do design em um lugar só, para aprovação e para quem for criar tela nova.
   Paleta do logo, tipografia, ícones, KPIs, atalhos, filtros, formulário, tabela, gráficos (Chart.js), avisos, confirmação e carregamento. Os números são de EXEMPLO. */
(function () {
  const { $, esc } = PSD;
  const TW = window.PSDTW, { nf, badge, kpi, card, ico, toast, confirmar, grafico } = TW;
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-ink outline-none";
  const prim = "inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700";
  const sec = "inline-flex items-center gap-2 rounded-lg border border-line bg-card px-4 py-2 text-sm font-semibold text-ink hover:bg-slate-500/10";
  const chip = (l, n, on, tom = "") => `<button type="button" aria-pressed="${on}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${on ? "border-blue-500 bg-blue-500 text-white" : tom === "forte" ? "border-amber-500 bg-amber-500/10 text-ink" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${l} ${nf(n)}</button>`;
  const cor = (nome, hex, uso) => `<div class="flex items-center gap-3"><span class="h-12 w-12 shrink-0 rounded-xl border border-line" style="background:${hex}"></span><div><b class="text-ink">${nome}</b><div class="text-xs text-mute">${hex}, ${uso}</div></div></div>`;
  const ICONES = ["amortecedor", "amortecedor-dianteiro", "mola", "coxim", "caixa-amortecedor", "selo-inmetro", "ship", "container", "drafting-compass", "warehouse", "chart-column", "target",
    "clipboard-list", "shield-check", "search", "package", "car", "triangle-alert", "lancamento", "vai-faltar", "download", "filter", "trash-2", "circle-check"];

  function guia() {
    PSD.root.innerHTML = `<div class="flex flex-col gap-6">
      <p class="m-0 text-sm text-mute">Base visual da etapa 17 nas cores do logo PERFECT. Os números desta página são <b>exemplos</b>. Troque o tema no botão do topo para ver o escuro.</p>
      ${card("Paleta do logo", `<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">${cor("Azul-marinho", "#202D56", "menu, títulos, botão principal")}${cor("Azul-claro", "#64C4E9", "destaque, gráficos, foco")}
        ${cor("Laranja", "#F6A019", "risco e aviso")}${cor("Vermelho", "#E72B3B", "ruptura e erro")}</div>
        <div class="mt-4 flex flex-wrap items-center gap-2">${badge("OK (verde só aqui)", "green")}${badge("Risco", "amber")}${badge("Ruptura", "red")}${badge("Em desenvolvimento", "blue")}${badge("Híbrido/elétrico", "violet")}${badge("Neutro", "slate")}</div>`)}
      ${card("Tipografia", `<div class="flex flex-col gap-3"><div class="font-display text-3xl font-bold text-ink">Barlow 700: títulos e números grandes, 1.059 itens</div>
        <div class="font-display text-xl font-semibold text-ink">Barlow 600 — subtítulos e cabeçalhos de seção</div>
        <div class="text-base text-ink">Segoe UI 16 px — texto corrido, campos de formulário e mensagens.</div><div class="text-sm text-mute">Segoe UI 14 px — tabelas, dicas e textos secundários.</div></div>`)}
      ${card("Ícones (Lucide + próprios do amortecedor)", `<div class="grid grid-cols-3 gap-3 sm:grid-cols-6 lg:grid-cols-8">${ICONES.map(n => `<div class="flex flex-col items-center gap-2 rounded-xl border border-line px-2 py-3 text-center"><span class="text-blue-600">${ico(n, "lg")}</span><span class="text-xs text-mute">${n}</span></div>`).join("")}</div>`)}
      <section class="grid grid-cols-2 gap-4 lg:grid-cols-4">${kpi("Itens no estoque", nf(1059), "armazém 04 · disponível", "blue", "warehouse")}${kpi("OK", nf(390), "cobertura de 6 a 18 meses", "green", "circle-check")}
        ${kpi("Risco", nf(236), "menos de 6 meses", "amber", "triangle-alert")}${kpi("Ruptura", nf(197), "sem estoque disponível", "red", "vai-faltar")}</section>
      ${card("Atalhos, filtros e formulário", `<div class="flex flex-col gap-4">
        <div class="flex flex-wrap items-center gap-2"><span class="mr-1 psd-rot">Atalhos</span>${chip("Vai faltar", 448, false, "forte")}${chip("Ruptura", 197, true)}${chip("Risco", 236, false)}${chip("Leve", 678, false)}${chip("Pick-up e utilitários", 157, false)}</div>
        <form class="flex flex-wrap items-center gap-2" onsubmit="return false"><input type="search" class="${campo} min-w-[16rem] flex-1" placeholder="Buscar código, concorrente, veículo…">
          <select class="${campo}"><option>Linha</option><option>Leve</option></select><select class="${campo}"><option>Sistema</option><option>FORCE GAS</option></select>
          <button type="button" class="${sec}">${ico("x", "sm")}Limpar filtros</button><a class="${prim} no-underline" href="#">${ico("download", "sm")}Baixar Excel</a></form>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-3"><label class="flex flex-col gap-1"><span class="font-semibold text-ink">Código PERFECT</span><input class="${campo}" value="AMD0100"><span class="text-xs text-mute">Com ou sem pontuação.</span></label>
          <label class="flex flex-col gap-1"><span class="font-semibold text-ink">Fornecedor</span><select class="${campo}"><option>ZS</option><option>E-WIN</option></select></label>
          <label class="flex flex-col gap-1"><span class="font-semibold text-ink">Quantidade</span><input class="${campo}" type="number" value="120"></label></div></div>`)}
      ${card("Tabela (14 px, linhas de 36 px, cabeçalho fixo e zebra)", TW.table([{ h: "Código" }, { h: "Descrição", nw: false }, { h: "Linha" }, { h: "Situação" }, { h: "Estoque", r: true }, { h: "Cobertura", r: true }],
        [["AMD0637", "AMORTECEDOR DIANTEIRO LD/LE", "Leve", "Ruptura", 85, "0,0"], ["AMD0100", "AMORTECEDOR DIANTEIRO LD/LE", "Pick-up e utilitários", "OK", 1240, "9,4"], ["AMD01111", "AMORTECEDOR DIANTEIRO LD", "Leve", "Risco", 310, "4,2"],
         ["AMD0245", "AMORTECEDOR TRASEIRO LD/LE", "Pesada", "Excesso", 2600, "22,1"], ["AMD4701", "AMORTECEDOR TRASEIRO LD/LE", "Leve", "OK", 880, "11,0"]].map(r =>
          [`<b class="text-blue-600">${r[0]}</b>`, r[1], r[2], badge(r[3], { Ruptura: "red", Risco: "amber", OK: "green", Excesso: "violet" }[r[3]]), nf(r[4]), r[5]]), { h: "max-h-[40vh]" }))}
      <section class="grid grid-cols-1 gap-4 xl:grid-cols-3">
        ${card("Vendas por mês (barras; ano anterior em cinza)", '<div id="g1"></div>', "", "xl:col-span-2")}${card("Situação do estoque (barra segmentada)", '<div id="g2"></div>')}
        ${card("Previsão × realizado (linhas)", '<div id="g3"></div>', "", "xl:col-span-2")}${card("Meta do ano (medidor)", TW.medidor({ value: 41, target: 60, title: "DESENVOLVIMENTO" }) + TW.medidor({ value: 62, target: 60, title: "REDESENVOLVIMENTO" }))}</section>
      ${card("Avisos, confirmação e carregamento", `<div class="flex flex-wrap gap-2">
        <button type="button" class="${sec}" data-t="ok">${ico("circle-check", "sm")}Aviso de inclusão</button><button type="button" class="${sec}" data-t="erro">${ico("circle-alert", "sm")}Aviso de erro</button>
        <button type="button" class="${sec}" data-t="aviso">${ico("triangle-alert", "sm")}Aviso de atenção</button><button type="button" class="${sec}" data-c="1">${ico("trash-2", "sm")}Excluir (confirmação)</button></div>
        <div class="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2"><div>${TW.carregando("Carregando a lista…")}</div><div>${TW.esqueleto(3)}</div></div>`)}
    </div>`;
    const meses = ["jun", "jul", "ago", "set", "out", "nov"];
    grafico($("#g1"), { type: "bar", titulo: "Vendas por mês", data: { labels: meses, datasets: [{ label: "2025", data: [16.2, 17.0, 17.9, 18.4, 18.8, 17.1], cor: "--chart-7", maxBarThickness: 12 }, { label: "2026", data: [21.4, 22.8, 24.1, 23.6, 25.5, 12.9], cor: "--chart-1", maxBarThickness: 12 }] },
      options: { datasets: { bar: { categoryPercentage: 0.62, barPercentage: 0.92 } }, interaction: { mode: "index", intersect: false }, plugins: { tooltip: { callbacks: { label: c => ` ${c.dataset.label}: R$ ${nf(c.parsed.y, 1)} mi` } } }, scales: { y: { ticks: { callback: v => "R$ " + v + " mi" } } } } });
    // situação do estoque é estado (bom/ruim): cores de status, não da paleta das séries
    TW.segmentos($("#g2"), [["OK", 390, "--ok"], ["Risco", 236, "--t-amber-500"], ["Ruptura", 197, "--t-red-500"], ["Excesso", 166, "--t-violet-500"], ["Sem giro", 70, "--chart-7"]].map(([l, v, cor]) => ({ l, v, cor })));
    grafico($("#g3"), { type: "line", altura: 240, titulo: "Previsão × realizado", data: { labels: ["sem 1", "sem 2", "sem 3", "sem 4", "sem 5", "sem 6"], datasets: [{ label: "Previsto", data: [120, 180, 150, 210, 190, 240] }, { label: "Chegou", data: [110, 170, 160, 190, 200, null] }] } });
    PSD.root.addEventListener("click", async e => {
      const t = e.target.closest("[data-t]"), c = e.target.closest("[data-c]");
      if (t) toast({ ok: "3 desenhos enviados, AMD0170 rev 02", erro: "Não foi possível gravar: o arquivo está aberto em outro programa.", aviso: "12 itens sem peso no catálogo." }[t.dataset.t],
        { tom: t.dataset.t, titulo: { ok: "Envio concluído", erro: "Erro ao gravar", aviso: "Atenção" }[t.dataset.t] });
      if (c && await confirmar({ titulo: "Excluir o ensaio?", texto: "AMD0100, ensaio de 12/11/2026, 10 pontos medidos.", nota: "Não dá para desfazer: o ensaio e os pontos saem do banco.", botao: "Excluir", perigo: true }))
        toast("Ensaio excluído.", { tom: "ok" });
    });
  }
  PSD.tela("guia-visual", guia);
})();
