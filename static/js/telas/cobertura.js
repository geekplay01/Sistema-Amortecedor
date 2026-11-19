/* Tela · Cobertura de concorrentes (etapa 17 · Q12/Q13/Q21–Q23/Q27). Abas (`tab` na URL):
   · catalogo (padrão) — concorrente × referência × nosso código do catálogo, com curva ABC de vendas e situação do estoque. Cartões por concorrente (clique filtra),
     atalhos de curva e linha (contagem = lista), busca, Excel. Referências pela regra Q18 (CrossCatalogo; servidor quando a planilha não tem o item).
   · desenvolvimento — DES em andamento com a curva PRÓPRIA pela frota da Fraga (LANÇAMENTOS; reserva COFAP × Fraga e FROTA do servidor). Atalhos de curva, origem e lançamento.
   Fonte: /api/cobertura (cobertura.py). Filtros só na URL (PSDTW.filtros). */
(function () {
  const { $, esc, J, qs, root } = PSD;
  const TW = window.PSDTW, { nf, badge, kpi, notice, ico, grafico } = TW;
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-ink outline-none";
  const prim = "inline-flex items-center gap-2 rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white no-underline hover:bg-blue-700";
  const chip = (k, v, label, n, on, forte) => `<button type="button" data-tg="${k}" data-v="${esc(v)}" aria-pressed="${on}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${on ? "border-blue-500 bg-blue-500 text-white" : forte ? "border-amber-500 bg-amber-500/10 text-ink hover:bg-amber-500/20" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${label} · ${nf(n)}</button>`;
  const cap = s => s ? String(s).charAt(0) + String(s).slice(1).toLowerCase() : "";
  const linha = l => l ? cap(String(l).replace(/^LINHA\s+/, "")) : "Sem linha";
  const CUR = { A: "blue", B: "slate", C: "slate", sem: "slate" }, curva = c => c && c !== "sem" ? badge("Curva " + c, CUR[c]) : '<span class="text-xs text-mute">sem venda</span>';
  const SIT = { ruptura: ["Ruptura", "red"], risco: ["Risco", "amber"], ok: ["OK", "green"], excesso: ["Excesso", "violet"], sem_giro: ["Sem giro", "slate"] };
  const codigo = c => `<a href="/item/${encodeURIComponent(c)}" class="font-semibold">${esc(c)}</a>`;
  const ABAS = [["catalogo", "Catálogo · concorrentes × nossos itens", "package"], ["desenvolvimento", "Em desenvolvimento · curva pela frota", "amortecedor"]];

  function cobertura() {
    const pedida = new URLSearchParams(location.search).get("tab"), tab = pedida === "desenvolvimento" ? "desenvolvimento" : "catalogo";
    const F = TW.filtros("cobertura", ["tab", "q", "concorrente", "curva", "linha", "origem", "lancamento"]); F.set({ tab }); let pg = 1, timer;
    root.innerHTML = `<div class="flex flex-col gap-5">
      <nav id="cba" class="flex flex-wrap gap-1 border-b border-line">${ABAS.map(([t, l, i]) => `<a href="/cobertura?tab=${t}" data-aba="${t}" class="-mb-px inline-flex items-center gap-2 border-b-2 px-3 py-2 text-sm font-semibold no-underline ${t === tab ? "border-blue-500 text-blue-600" : "border-transparent text-mute hover:text-ink"}">${ico(i, "sm")}${l}</a>`).join("")}</nav>
      <div id="cbk" class="grid grid-cols-2 gap-4 lg:grid-cols-4">${'<div class="skel h-24"></div>'.repeat(4)}</div>
      <div id="cbx"></div>
      <div id="cbq" class="flex flex-wrap items-center gap-2"></div>
      <form id="cbf" class="flex flex-wrap items-center gap-2" autocomplete="off"><input name="q" type="search" class="${campo} min-w-[16rem] flex-1" placeholder="${tab === "catalogo" ? "Buscar concorrente, referência, nosso código, aplicação…" : "Buscar código, veículo, concorrente, fornecedor…"}">
        <button type="button" id="cbl" class="rounded-lg border border-line bg-card px-3.5 py-2 text-sm font-semibold text-ink hover:bg-slate-500/10">Limpar filtros</button><a id="cbe" class="${prim}" href="#">${ico("download", "sm")}Baixar Excel</a></form>
      <div id="cbm" class="text-sm text-mute"></div><div id="cbt">${TW.esqueleto(8)}</div><div id="cbp" class="flex items-center justify-center gap-3 text-sm text-mute"></div></div>`;
    $("#cbf").q.value = F.get().q || "";
    $("#cba").addEventListener("click", e => { const a = e.target.closest("[data-aba]"); if (!a) return; e.preventDefault(); history.replaceState(null, "", "/cobertura?" + qs({ tab: a.dataset.aba })); cobertura(); });

    const pager = (d) => { const pages = Math.max(1, Math.ceil(d.total / d.size));
      $("#cbp").innerHTML = pages > 1 ? `<button type="button" data-p="${pg - 1}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button type="button" data-p="${pg + 1}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${pg >= pages ? "disabled" : ""}>›</button>` : ""; };

    const catalogo = d => {
      const s = F.get(), k = d.kpis;
      $("#cbk").innerHTML = kpi("Referências de concorrentes", nf(k.referencias), "com os filtros", "blue", "swords") + kpi("Concorrentes", nf(k.concorrentes), "marcas com item equivalente", "sky", "tags")
        + kpi("Nossos códigos cobertos", nf(k.nossos_codigos), `de ${nf(k.catalogo)} itens do catálogo`, "green", "package") + kpi("Cobertura do catálogo", nf(k.catalogo ? 100 * k.nossos_codigos / k.catalogo : 0, 1) + "%", "itens com algum concorrente", "slate", "gauge");
      $("#cbx").innerHTML = `<div class="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-6">${d.cards.slice(0, 12).map(c => { const on = s.concorrente === c.concorrente, t = c.A + c.B + c.C || 1;
        return `<button type="button" data-tg="concorrente" data-v="${esc(c.concorrente)}" aria-pressed="${on}" class="rounded-2xl border ${on ? "border-blue-500 bg-blue-500/10" : "border-line bg-card hover:bg-slate-500/10"} p-4 text-left shadow-sm">
          <div class="font-display text-sm font-semibold uppercase tracking-wide text-mute">${esc(c.concorrente)}</div><div class="mt-1 font-display text-2xl font-bold text-ink">${nf(c.codigos)}</div><div class="text-xs text-mute">códigos nossos</div>
          <div class="mt-3 flex h-2 overflow-hidden rounded-full bg-thead" title="A ${c.A} · B ${c.B} · C ${c.C}"><span class="bg-blue-600" style="width:${100 * c.A / t}%"></span><span class="bg-accent" style="width:${100 * c.B / t}%"></span><span class="bg-slate-400" style="width:${100 * c.C / t}%"></span></div>
          <div class="mt-1 flex justify-between text-xs text-mute"><span>A ${nf(c.A)}</span><span>B ${nf(c.B)}</span><span>C ${nf(c.C)}</span></div></button>`; }).join("")}</div>`;
      $("#cbq").innerHTML = `<span class="mr-1 text-xs font-semibold uppercase tracking-wide text-mute">Atalhos</span>` + ["A", "B", "C", "sem"].filter(c => d.counts.curva[c]).map(c => chip("curva", c, c === "sem" ? "Sem venda" : "Curva " + c, d.counts.curva[c], s.curva === c, c === "A")).join("")
        + Object.entries(d.counts.linha).map(([l, n]) => chip("linha", l, linha(l === "sem" ? "" : l), n, s.linha === l)).join("")
        + (s.concorrente ? chip("concorrente", s.concorrente, s.concorrente, d.counts.concorrente[s.concorrente] || 0, true) : "");
      $("#cbm").innerHTML = `<b class="text-ink">${nf(d.total)}</b> referência(s) · <b class="text-ink">${nf(k.nossos_codigos)}</b> código(s) nosso(s)${Object.keys(s).filter(x => x !== "tab").length ? " · com filtros" : ""}`;
      $("#cbt").innerHTML = TW.table([{ h: "Concorrente" }, { h: "Referência" }, { h: "Nosso código" }, { h: "Descrição", nw: false }, { h: "Aplicação", nw: false }, { h: "Linha" }, { h: "Curva" }, { h: "Estoque" }],
        d.rows.map(r => [`<b class="text-ink">${esc(r.concorrente)}</b>`, `<span class="tabular-nums">${esc(r.referencia)}</span>`, codigo(r.codigo), `<span class="block max-w-[16rem] truncate" title="${esc(r.descricao || "")}">${esc(r.descricao || "")}</span>`,
          `<span class="block min-w-[12rem] max-w-[22rem] text-xs">${esc(r.aplicacao || "–")}</span>`, esc(linha(r.linha)), curva(r.curva), SIT[r.situacao] ? badge(SIT[r.situacao][0], SIT[r.situacao][1]) : '<span class="text-xs text-mute">–</span>']), { h: "max-h-[65vh]" });
    };

    const desenvolvimento = d => {
      const s = F.get(), k = d.kpis, A = d.counts.curva.A || 0;
      $("#cbk").innerHTML = kpi("DES em andamento", nf(k.itens), "com os filtros", "blue", "amortecedor") + kpi("Com frota", nf(k.com_frota), "Fraga ou servidor", "green", "car")
        + kpi(`Frota ${k.ano}`, nf(k.frota / 1e6, 1) + " mi", "veículos das aplicações somados", "sky", "gauge") + kpi("Curva A", nf(A), "até 80% da frota acumulada", "amber", "target");
      $("#cbx").innerHTML = (k.fraga ? "" : notice("A planilha <b>LANÇAMENTOS</b> da Fraga ainda não foi carregada: a curva usa só a FROTA do servidor. Carregue «LANÇAMENTOS aaaa.xlsx» (e «COFAP_AMORTECEDORES_x_FROTA.xlsx») em Atualização de dados.", "amber"))
        + (d.rows.length ? TW.card("Maiores frotas", '<div id="cbg"></div>') : "");
      $("#cbq").innerHTML = `<span class="mr-1 text-xs font-semibold uppercase tracking-wide text-mute">Atalhos</span>` + ["A", "B", "C", "sem"].filter(c => d.counts.curva[c]).map(c => chip("curva", c, c === "sem" ? "Sem frota" : "Curva " + c, d.counts.curva[c], s.curva === c, c === "A")).join("")
        + chip("lancamento", "1", "Lançamento (2024+)", d.counts.lancamento, s.lancamento === "1") + Object.entries(d.counts.origem).map(([o, n]) => chip("origem", o, o, n, s.origem === o)).join("");
      $("#cbm").innerHTML = `<b class="text-ink">${nf(d.total)}</b> item(ns) em desenvolvimento`;
      $("#cbt").innerHTML = TW.table([{ h: "Código" }, { h: "Descrição", nw: false }, { h: "Aplicações", nw: false }, { h: `Frota ${k.ano}`, r: true }, { h: "Origem" }, { h: "Curva" }, { h: "Concorrentes", nw: false }, { h: "Status" }],
        d.rows.map(r => [codigo(r.codigo) + (r.lancamento ? " " + badge("lançamento", "green") : ""), `<span class="block max-w-[14rem] truncate" title="${esc(r.descricao || "")}">${esc(r.descricao || "")}</span>`,
          `<span class="block min-w-[12rem] max-w-[20rem] text-xs">${esc(r.aplicacoes.join(" · "))}</span>`,
          `<span title="${esc(r.veiculos.map(v => v.nome + ": " + nf(v.frota)).join("\n") || "")}" class="tabular-nums font-semibold">${r.frota ? nf(r.frota) : "–"}</span>`, `<span class="text-xs text-mute">${esc(r.origem)}</span>`,
          r.curva !== "sem" ? badge("Curva " + r.curva, CUR[r.curva]) : '<span class="text-xs text-mute">sem dado</span>', `<span class="block max-w-[16rem] truncate text-xs" title="${esc(r.concorrentes.join(", "))}">${esc(r.concorrentes.join(", ") || "–")}</span>`, `<span class="text-xs">${esc(r.status || "")}</span>`]), { h: "max-h-[65vh]" });
      const top = d.rows.filter(r => r.frota > 0).slice(0, 15);
      if (top.length) grafico($("#cbg"), { type: "bar", altura: 260, titulo: "Maiores frotas", data: { labels: top.map(r => r.codigo), datasets: [{ label: `Frota ${k.ano}`, data: top.map(r => r.frota), backgroundColor: top.map(r => ({ A: "#2F4A8C", B: "#64C4E9", C: "#94A3B8" })[r.curva] || "#94A3B8") }] },
        options: { indexAxis: "y", plugins: { legend: { display: false }, tooltip: { callbacks: { afterLabel: c => top[c.dataIndex].aplicacoes.slice(0, 2).join(" · ") } } }, scales: { x: { ticks: { callback: v => nf(v / 1e3) + " mil" } } } } });
    };

    const carregar = async () => {
      const s = F.get(); $("#cbe").href = "/api/export/cobertura.xlsx?" + qs({ ...s, tab });
      try { const d = await J("/api/cobertura?" + qs({ ...s, tab, page: pg })); (tab === "catalogo" ? catalogo : desenvolvimento)(d); pager(d); }
      catch (e) { $("#cbt").innerHTML = notice(esc(e.message), "red"); }
    };
    const aplicar = patch => { if (patch) F.set(patch); pg = 1; carregar(); };
    root.onclick = e => { const b = e.target.closest("[data-tg]"); if (b) { F.toggle(b.dataset.tg, b.dataset.v); pg = 1; carregar(); }          // onclick (não addEventListener): trocar de aba não acumula ouvintes
      const p = e.target.closest("[data-p]"); if (p && !p.disabled) { pg = +p.dataset.p; carregar(); } };
    $("#cbf").addEventListener("input", e => { if (e.target.name === "q") { clearTimeout(timer); timer = setTimeout(() => aplicar({ q: e.target.value.trim() }), 300); } });
    $("#cbf").addEventListener("submit", e => e.preventDefault());
    $("#cbl").onclick = () => { F.clear(); F.set({ tab }); $("#cbf").q.value = ""; aplicar(); };
    carregar();
  }
  PSD.tela("cobertura", cobertura);
})();
