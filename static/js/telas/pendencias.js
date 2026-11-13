/* Tela · Pendências de dados — visual Tailwind (etapa 16 · B). Abas: pendências e conflitos × possíveis duplicidades.
   Atalhos de status, tipo e campo: cada número = total da lista ao clicar (queries.pendencies · counts: cada grupo ignora o próprio filtro e respeita os outros; test_25).
   Status padrão «Abertas»; «Todas» = sem filtro. Filtros na URL e lembrados (PSDTW.filtros); o Excel segue os filtros. Nada é unido, sobrescrito ou apagado automaticamente. */
(function () {
  const { $, esc, J, post, qs, root, fail } = PSD;
  const TW = window.PSDTW, { nf, badge, notice } = TW;
  const ST = [["aberta", "Abertas"], ["resolvida", "Resolvidas"], ["ignorada", "Ignoradas"], ["todas", "Todas"]], STB = { aberta: "amber", resolvida: "green", ignorada: "slate" };
  const KIND = { conflito: ["Conflito entre fontes", "amber"], campo_ausente: ["Campo ausente", "blue"], campo_invalido: ["Campo inválido", "red"] };
  const CAMPO = { family: "Família", package_code: "Código da caixa", ean: "EAN", peso: "Peso", sistema: "Sistema" };
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500";
  const botao = "rounded-lg border border-line bg-card px-3.5 py-2 text-sm font-semibold text-ink hover:bg-slate-500/10";
  const primario = "rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-blue-700";
  const mini = "rounded-lg border border-line bg-card px-2.5 py-1 text-xs font-semibold text-ink hover:bg-slate-500/10";
  const chip = (attrs, label, on, n) => `<button type="button" ${attrs} aria-pressed="${on}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${on ? "border-blue-500 bg-blue-500 text-white" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${label}${n != null ? ` · ${nf(n)}` : ""}</button>`;
  const rotulo = t => `<span class="mr-1 text-xs font-semibold uppercase tracking-wide text-mute">${t}</span>`;
  const aba = (href, label, on) => `<a href="${href}" data-aba class="-mb-px border-b-2 px-3 py-2 text-sm font-semibold no-underline ${on ? "border-blue-500 text-blue-600" : "border-transparent text-mute hover:text-ink"}">${label}</a>`;
  const pager = (pg, pages) => { const b = (p, dis, l) => `<button type="button" data-p="${p}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${dis ? "disabled" : ""}>${l}</button>`;
    return pages > 1 ? `${b(pg - 1, pg < 2, "‹")} Página ${pg} de ${pages} ${b(pg + 1, pg >= pages, "›")}` : ""; };
  const nomeCampo = f => CAMPO[f] || f;
  // «Valor atual «X» × importado «Y» (fonte F). Nada foi sobrescrito.» → valores em destaque (o texto gravado não muda)
  const descricao = t => { const m = /^Valor atual «(.*?)» × importado «(.*?)» \(fonte (.*?)\)/.exec(t || "");
    return m ? `No banco <b class="text-ink">${esc(m[1])}</b> × na planilha <b class="text-ink">${esc(m[2])}</b> <span class="text-mute">· ${esc(m[3])} · nada foi sobrescrito</span>` : esc(t || ""); };

  function pendencias() {
    const F = TW.filtros("pendencias", ["tab", "q", "status", "kind", "field"]); let pg = 1, d = null, timer;
    const s0 = F.get(), dup = s0.tab === "dup", st = () => F.get().status || "aberta";
    const api = () => { const s = F.get(); return { q: s.q || "", status: st(), kind: s.kind || "", field: s.field || "" }; };
    root.innerHTML = `<div class="flex flex-col gap-5">
      <div class="flex flex-wrap items-end justify-between gap-3 border-b border-line"><nav class="flex gap-1">${aba("/pendencias?tab=", "Pendências e conflitos", !dup)}${aba("/pendencias?tab=dup", 'Possíveis duplicidades <span id="pdn"></span>', dup)}</nav>
        <a id="pdl" class="${primario} mb-2" href="/api/export/pendencias.xlsx">⬇ Baixar Excel</a></div>
      <div id="pbody" class="flex flex-col gap-5"></div></div>`;
    // as abas trocam só a chave «tab» (os filtros da lista ficam guardados)
    root.querySelector("nav").addEventListener("click", e => { const a = e.target.closest("[data-aba]"); if (!a) return; e.preventDefault(); F.set({ tab: a.href.includes("tab=dup") ? "dup" : "" }); pendencias(); });
    J("/api/duplicates").then(r => { $("#pdn").textContent = "· " + nf(r.length); if (dup) duplicidades(r); }).catch(fail);
    if (dup) return;

    $("#pbody").innerHTML = `<p class="m-0 text-sm text-mute">Diferenças encontradas ao importar planilhas (<b class="text-ink">conflito</b>: o banco e a planilha trazem valores diferentes; o valor do banco foi mantido) e campos que faltam no cadastro. Resolva no ERP ou na planilha de origem e marque aqui como <b class="text-ink">resolvida</b>, ou <b class="text-ink">ignore</b> o que não precisa de ação.</p>
      <div id="pq" class="flex flex-col gap-2"></div>
      <form id="pf" class="flex flex-wrap items-center gap-2" autocomplete="off"><input name="q" type="search" placeholder="Buscar código PERFECT, campo ou texto da pendência…" class="${campo} min-w-[16rem] flex-1"><button type="button" id="pclr" class="${botao}">Limpar filtros</button></form>
      <div id="pm" class="text-sm text-mute"></div><div id="pt"></div><div id="pp" class="flex items-center justify-center gap-3 text-sm text-mute"></div>`;
    $("#pf").q.value = s0.q || "";

    const atalhos = () => {
      const s = F.get(), c = d.counts, maior = o => Object.keys(o).sort((a, b) => o[b] - o[a]), k = maior(c.kind), f = maior(c.field);
      if (s.kind && !k.includes(s.kind)) k.push(s.kind); if (s.field && !f.includes(s.field)) f.push(s.field);
      $("#pq").innerHTML = `<div class="flex flex-wrap items-center gap-2">${rotulo("Status")}${ST.map(([v, l]) => chip(`data-st="${v}"`, l, st() === v, c.status[v])).join("")}</div>`
        + (k.length ? `<div class="flex flex-wrap items-center gap-2">${rotulo("Tipo")}${k.map(v => chip(`data-tg="kind" data-v="${esc(v)}"`, esc(KIND[v] ? KIND[v][0] : v), s.kind === v, c.kind[v] || 0)).join("")}</div>` : "")
        + (f.length ? `<div class="flex flex-wrap items-center gap-2">${rotulo("Campo")}${f.map(v => chip(`data-tg="field" data-v="${esc(v)}"`, esc(nomeCampo(v)), s.field === v, c.field[v] || 0)).join("")}</div>` : "");
    };
    const tabela = () => {
      const s = F.get(), n = ["q", "kind", "field"].filter(k => s[k]).length + (st() !== "aberta" ? 1 : 0);
      $("#pdl").href = "/api/export/pendencias.xlsx?" + qs(api());
      $("#pm").innerHTML = `<b class="text-ink">${nf(d.total)}</b> pendência(s)${n ? ` · ${n} filtro(s) ativo(s)` : ""}${F.restaurado && pg === 1 ? ' · <span class="text-amber-700">filtros da última visita</span>' : ""}`;
      $("#pt").innerHTML = TW.table([{ h: "Produto" }, { h: "Tipo" }, { h: "Campo" }, { h: "Descrição", nw: false }, { h: "Desde" }, { h: "Status" }, { h: "" }],
        d.rows.map(x => [
          x.product_id ? `<a href="#" class="font-semibold text-blue-600" data-ficha="${x.product_id}">${esc(x.perfect_code)}</a>` : '<span class="text-mute">–</span>',
          badge(KIND[x.kind] ? KIND[x.kind][0] : x.kind, KIND[x.kind] ? KIND[x.kind][1] : "slate"), esc(nomeCampo(x.field || "")) || '<span class="text-mute">–</span>',
          `<span class="block min-w-[18rem]">${descricao(x.description)}</span>`, TW.dmy(x.created_at), badge(x.status, STB[x.status]),
          x.status === "aberta" ? `<span class="flex gap-1"><button type="button" class="${mini}" data-pd="${x.id}" data-s="resolvida">Resolver</button><button type="button" class="${mini}" data-pd="${x.id}" data-s="ignorada">Ignorar</button></span>`
            : `<button type="button" class="${mini}" data-pd="${x.id}" data-s="aberta">Reabrir</button>`]), { h: "max-h-[65vh]" });
      $("#pp").innerHTML = pager(pg, Math.max(1, Math.ceil(d.total / d.size)));
    };
    const carregar = async () => {
      try { d = await J("/api/pendencies?" + qs({ ...api(), page: pg })); } catch (e) { $("#pt").innerHTML = notice(esc(e.message), "red"); return; }
      atalhos(); tabela();
    };
    const aplicar = (patch, logo) => { if (patch) F.set(patch); pg = 1; clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 300); };

    $("#pf").addEventListener("input", e => { if (e.target.name === "q") aplicar({ q: e.target.value }); });
    $("#pf").addEventListener("submit", e => e.preventDefault());
    $("#pclr").addEventListener("click", () => { $("#pf").q.value = ""; aplicar({ q: "", status: "", kind: "", field: "" }, true); });
    $("#pq").addEventListener("click", e => { const a = e.target.closest("[data-st]"), b = e.target.closest("[data-tg]");
      if (a) aplicar({ status: a.dataset.st === "aberta" ? "" : a.dataset.st }, true);
      else if (b) { F.toggle(b.dataset.tg, b.dataset.v); aplicar(null, true); } });
    $("#pbody").addEventListener("click", async e => { const b = e.target.closest("[data-pd]"), p = e.target.closest("[data-p]");
      if (b) { b.disabled = true; try { await post("/api/pendencies/" + b.dataset.pd, { status: b.dataset.s }); } catch (er) { fail(er); } carregar(); }
      else if (p && !p.disabled) { pg = +p.dataset.p; carregar(); scrollTo(0, 0); } });
    carregar();
  }

  function duplicidades(r) {
    $("#pdl").href = "/api/export/pendencias.xlsx";
    $("#pbody").innerHTML = `<p class="m-0 text-sm text-mute">Mesmo código (OEM, concorrente, EAN…) ligado a mais de um produto PERFECT. Pode ser correto (aplicações em comum) ou erro de cadastro: confira na Pesquisa. Nada é unido ou excluído automaticamente. O Excel traz as duas abas.</p>
      <div class="text-sm text-mute"><b class="text-ink">${nf(r.length)}</b> código(s) em mais de um produto</div>`
      + TW.table([{ h: "Tipo de código" }, { h: "Código" }, { h: "Produtos", nw: false }, { h: "Qtd.", r: true }],
        r.map(x => [esc(x.code_type), `<a class="font-semibold text-blue-600" href="/pesquisa?code=${encodeURIComponent(x.code)}">${esc(x.code)}</a>`,
          String(x.products || "").split(",").map(c => `<a class="text-blue-600" href="/pesquisa?q=${encodeURIComponent(c)}">${esc(c)}</a>`).join(" · "), nf(x.n)]), { h: "max-h-[65vh]" });
  }
  PSD.tela("pendencias", pendencias);
})();
