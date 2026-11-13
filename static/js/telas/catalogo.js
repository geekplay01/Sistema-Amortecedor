/* Telas · Aplicações, Comparação e Equivalências — visual Tailwind (etapa 16). (Produtos e Pesquisa: telas/produtos.js.)
   Aplicações: eixo e lado (inclusive «não informado») são atalhos que batem com a lista (queries.applications · stats; tests: test_23).
   Comparação: 2 a 4 produtos lado a lado, linhas que diferem destacadas, opção «só diferenças»; a última comparação fica lembrada.
   Equivalências: atalhos por status, confiança e «sem diferenças» (equivalence.listing · *_counts); critérios/diferenças/dados ausentes
   são listas guardadas na URL juntas por «|». Filtros na URL e lembrados (PSDTW.filtros); o Excel segue os mesmos filtros. */
(function () {
  const { $, $$, esc, J, post, qs, root, fail, SYS, yr } = PSD;
  const TW = window.PSDTW, { nf, badge, kpi, notice } = TW;
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500";
  const botao = "rounded-lg border border-line bg-card px-3.5 py-2 text-sm font-semibold text-ink hover:bg-slate-500/10";
  const primario = "rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-blue-700";
  const chip = (attrs, label, on, n, forte = false) => `<button type="button" ${attrs} aria-pressed="${on}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${on ? "border-blue-500 bg-blue-500 text-white" : forte ? "border-amber-500 bg-amber-500/10 text-ink hover:bg-amber-500/20" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${label}${n != null ? ` · ${nf(n)}` : ""}</button>`;
  const selectF = (name, rotulo, opts, cur, cls = "max-w-[13rem]") => `<select name="${name}" class="${campo} ${cls}" title="${esc(rotulo)}"><option value="">${esc(rotulo)}</option>${opts.map(([v, l]) => `<option value="${esc(v)}" ${String(v) === String(cur ?? "") ? "selected" : ""}>${esc(l)}</option>`).join("")}</select>`;
  const textoF = (name, ph, cur, cls = "") => `<input name="${name}" type="search" value="${esc(cur || "")}" placeholder="${esc(ph)}" class="${campo} ${cls}">`;
  const rotulo = t => `<span class="mr-1 text-xs font-semibold uppercase tracking-wide text-mute">${t}</span>`;
  const ficha = (id, code) => `<a href="#" class="font-semibold text-blue-600" data-ficha="${id}">${esc(code)}</a>`;
  const meio = '<span class="text-mute">–</span>';
  const pager = (pg, pages) => { const b = (p, dis, l) => `<button type="button" data-p="${p}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${dis ? "disabled" : ""}>${l}</button>`;
    return pages > 1 ? `${b(pg - 1, pg < 2, "‹")} Página ${pg} de ${pages} ${b(pg + 1, pg >= pages, "›")}` : ""; };
  const metaLinha = (total, nome, F, pg, xlsx) => { const n = Object.keys(F.get()).length;
    return `<span><b class="text-ink">${nf(total)}</b> ${nome}${n ? ` · ${n} filtro(s) ativo(s)` : ""}${F.restaurado && pg === 1 ? ' · <span class="text-amber-700">filtros da última visita</span>' : ""}</span>${xlsx ? `<a class="${primario}" href="${xlsx}">⬇ Baixar Excel</a>` : ""}`; };

  // ================= Aplicações =================
  const EIXO = { dianteiro: "Dianteiro", traseiro: "Traseiro" }, LADO = { direito: "Direito", esquerdo: "Esquerdo", ambos: "Ambos" };
  function aplicacoes() {
    const F = TW.filtros("aplicacoes", ["q", "make", "model", "year", "axle", "side"]); let pg = 1, d = null, L = { makes: [], models: [], years: [] }, timer;
    root.innerHTML = `<div class="flex flex-col gap-5">
      <p class="m-0 text-sm text-mute">Veículos em que cada amortecedor do catálogo é aplicado (um produto pode ter várias aplicações). Clique no código para abrir a ficha.</p>
      <div id="ak" class="grid grid-cols-2 gap-4 lg:grid-cols-4"></div>
      <div id="aq" class="flex flex-col gap-2"></div>
      <form id="af" class="flex flex-wrap items-center gap-2" autocomplete="off"></form>
      <div id="am" class="flex flex-wrap items-center justify-between gap-3 text-sm text-mute"></div>
      <div id="at"></div><div id="ap" class="flex items-center justify-center gap-3 text-sm text-mute"></div>
    </div>`;
    const topo = () => {
      const s = d.stats, f = F.get(), k = d.kpis;
      $("#ak").innerHTML = kpi("Aplicações", nf(d.total), Object.keys(f).length ? "com os filtros atuais" : "todas as cadastradas", "blue") + kpi("Produtos", nf(k.products), "com ao menos uma aplicação aqui", "green")
        + kpi("Montadoras", nf(k.makes), "distintas", "slate") + kpi("Modelos", nf(k.models), "montadora + modelo distintos", "slate");
      const c = (g, v, l, forte) => chip(`data-tg="${g}" data-v="${v}"`, l, f[g] === v, s[g + ":" + v], forte);
      $("#aq").innerHTML = `<div class="flex flex-wrap items-center gap-2">${rotulo("Eixo")}${c("axle", "dianteiro", "Dianteiro")}${c("axle", "traseiro", "Traseiro")}${c("axle", "sem", "Eixo não informado", true)}</div>
        <div class="flex flex-wrap items-center gap-2">${rotulo("Lado")}${c("side", "direito", "Direito")}${c("side", "esquerdo", "Esquerdo")}${c("side", "sem", "Lado não informado", true)}<span class="text-xs text-mute">Direito e Esquerdo incluem as aplicações de ambos os lados.</span></div>`;
    };
    const filtrosF = () => { const s = F.get();
      $("#af").innerHTML = textoF("q", "Buscar veículo, aplicação ou código PERFECT…", s.q, "min-w-[16rem] flex-1") + selectF("make", "Montadora", L.makes.map(x => [x, x]), s.make) + selectF("model", "Modelo", L.models.map(x => [x, x]), s.model)
        + selectF("year", "Ano", L.years.map(y => [y, y]), s.year, "max-w-[8rem]") + selectF("axle", "Eixo", [["dianteiro", "Dianteiro"], ["traseiro", "Traseiro"], ["sem", "Não informado"]], s.axle)
        + selectF("side", "Lado", [["direito", "Direito"], ["esquerdo", "Esquerdo"], ["sem", "Não informado"]], s.side) + `<button type="button" id="aclr" class="${botao}">Limpar filtros</button>`; };
    const carregar = async () => { try {
      const s = F.get(); d = await J("/api/applications?" + qs({ ...s, page: pg })); topo();
      $("#am").innerHTML = metaLinha(d.total, "aplicação(ões)", F, pg, "/api/export/aplicacoes.xlsx?" + new URLSearchParams(s));
      $("#at").innerHTML = TW.table([{ h: "Montadora" }, { h: "Modelo" }, { h: "Aplicação", nw: false }, { h: "Anos" }, { h: "Eixo" }, { h: "Lado" }, { h: "Código PERFECT" }, { h: "Pos.", r: true }],
        d.rows.map(a => [esc(a.make || "") || meio, `${esc(a.model || "") || meio}${a.version ? ` <span class="text-xs text-mute">${esc(a.version)}</span>` : ""}`, `<span class="block min-w-[14rem] max-w-[30rem]">${esc(a.application_text || "")}</span>`,
          yr(a), a.axle ? esc(EIXO[a.axle] || a.axle) : badge("não informado", "amber"), a.side ? esc(LADO[a.side] || a.side) : badge("não informado", "amber"),
          `${ficha(a.product_id, a.perfect_code)}<span class="block max-w-[16rem] truncate text-xs text-mute" title="${esc(a.description || "")}">${esc(a.description || "")}</span>`, a.catalog_position ?? meio]), { h: "max-h-[65vh]" });
      $("#ap").innerHTML = pager(pg, Math.max(1, Math.ceil(d.total / d.size)));
    } catch (e) { $("#at").innerHTML = notice(esc(e.message), "red"); } };
    const aplicar = (patch, logo) => { if (patch) F.set(patch); pg = 1; clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 300); };
    const modelos = async () => { const m = F.get().make; L.models = (await J("/api/filters" + (m ? "?make=" + encodeURIComponent(m) : ""))).models; if (F.get().model && !L.models.includes(F.get().model)) F.set({ model: "" }); };
    $("#af").addEventListener("input", async e => { const n = e.target.name; if (!n) return;
      if (n === "make") { F.set({ make: e.target.value }); await modelos(); filtrosF(); }
      aplicar({ [n]: e.target.value }, e.target.tagName === "SELECT"); });
    $("#af").addEventListener("submit", e => e.preventDefault());
    $("#af").addEventListener("click", async e => { if (e.target.id !== "aclr") return; const tinha = F.get().make; F.clear(); if (tinha) await modelos(); filtrosF(); aplicar(null, true); });
    $("#aq").addEventListener("click", e => { const b = e.target.closest("[data-tg]"); if (!b) return; F.toggle(b.dataset.tg, b.dataset.v); filtrosF(); aplicar(null, true); });
    $("#ap").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; carregar(); scrollTo(0, 0); } });
    (async () => { const f = await J("/api/filters"); L = { makes: f.makes, models: f.models, years: f.years.map(String) }; if (F.get().make) await modelos(); filtrosF(); await carregar(); })().catch(fail);
  }

  // ================= Comparação =================
  const LINHAS = [["Posição no catálogo", p => p.catalog_position], ["Descrição", p => p.description], ["Grupo", p => p.catalog_group], ["Família", p => p.family], ["Sistema", p => SYS[p.system_type]],
    ["Lmin (mm)", p => p.dimensions?.lmin_mm], ["Lmax (mm)", p => p.dimensions?.lmax_mm], ["Curso (mm)", p => p.dimensions?.stroke_mm], ["Ø haste (mm)", p => p.dimensions?.rod_diameter_mm], ["Corpo (mm)", p => p.dimensions?.body_length_mm], ["Ø tubo (mm)", p => p.dimensions?.tube_diameter_mm],
    ["Fixação superior", p => p.dimensions?.upper_mount], ["Fixação inferior", p => p.dimensions?.lower_mount], ["Peso (kg)", p => p.weight_kg], ["EAN", p => p.ean], ["Caixa", p => [p.package_code, p.box?.raw_dims].filter(Boolean).join(" · ")],
    ["Códigos OEM", p => p.codes.filter(c => c.code_type === "oem").map(c => c.code).join(", ")], ["Códigos de fornecedor", p => [...new Set(p.codes.filter(c => c.code_type === "fornecedor").map(c => c.code))].join(", ")],
    ["Aplicações", p => p.applications.length ? p.applications.length + ": " + p.applications.slice(0, 4).map(a => [a.make, a.model, yr(a)].filter(Boolean).join(" ")).join("; ") : ""],
    ["Nº Inmetro", p => [...new Set(p.certificates.map(c => c.inmetro_number).filter(Boolean))].join(", ")],
    ["Fontes", p => [...new Set([...p.codes, ...p.applications].map(x => x.source).filter(Boolean))].join("; ")]];
  function comparacao() {
    const F = TW.filtros("comparacao", ["ids", "dif"]);
    const ids = () => ((F.get().ids || "").match(/\d+/g) || []).slice(0, 4);
    root.innerHTML = `<div class="flex flex-col gap-5">
      <p class="m-0 text-sm text-mute">Escolha de 2 a 4 produtos para comparar os dados lado a lado. As linhas que diferem ficam destacadas; dimensões parecidas não bastam para afirmar intercambialidade.</p>
      <section class="flex flex-col gap-3 rounded-2xl border border-line bg-card p-5 shadow-sm">
        <div class="flex flex-wrap items-center gap-2"><input id="cadd" list="cdl" placeholder="Adicionar produto: digite o código PERFECT e escolha" class="${campo} min-w-[16rem] flex-1" autocomplete="off"><datalist id="cdl"></datalist>
          <button type="button" id="cdif" class="${botao}"></button><a id="cxl" class="${primario}" href="#">⬇ Baixar Excel</a></div>
        <div id="csel" class="flex flex-wrap items-center gap-2"></div><span id="cmsg" class="hidden text-sm text-amber-700"></span>
      </section>
      <div id="cout"></div>
    </div>`;
    const add = $("#cadd"); let achados = {}, tb, ps = [];
    const desenhar = () => {
      const so = F.get().dif === "1", lista = ids();
      $("#cdif").textContent = so ? "Mostrar todos os campos" : "Só as diferenças"; $("#cdif").setAttribute("aria-pressed", so);
      $("#cxl").href = "/api/export/comparacao.xlsx?ids=" + lista.join(",");
      $("#csel").innerHTML = lista.length ? rotulo("Comparando") + ps.map(p => `<span class="inline-flex items-center gap-1 rounded-full border border-line px-3 py-1 text-xs font-semibold text-ink">${esc(p.perfect_code)}<button type="button" data-rm="${p.id}" class="text-mute hover:text-red-600" title="Tirar da comparação" aria-label="Tirar ${esc(p.perfect_code)} da comparação">×</button></span>`).join("")
        + `<button type="button" id="cclr" class="text-xs font-semibold text-blue-600">Limpar</button>` : "";
      if (!ps.length) { $("#cout").innerHTML = TW.empty("Nenhum produto escolhido. Digite um código acima, ou use «Comparar» numa sugestão de Equivalências."); return; }
      const difs = [], linhas = LINHAS.map(([l, fn]) => { const v = ps.map(p => String(fn(p) ?? "")); const dif = ps.length > 1 && new Set(v).size > 1; if (dif) difs.push(l); return { l, v, dif }; });
      const vis = linhas.filter(r => !so || r.dif);
      $("#cout").innerHTML = (ps.length > 1 ? notice(difs.length ? `<b>${nf(difs.length)} campo(s) diferem:</b> ${difs.map(esc).join(", ")}. «—» = sem dado.` : "Nenhuma diferença nos campos comparados.", difs.length ? "amber" : "blue") : notice("Adicione mais um produto para ver as diferenças.", "blue"))
        + `<div class="mt-3 overflow-x-auto rounded-xl border border-line bg-card"><table class="w-full border-collapse text-sm"><thead><tr class="border-b border-line"><th class="sticky left-0 z-10 bg-card px-4 py-3"></th>${ps.map(p => `<th class="min-w-[12rem] px-4 py-3 text-left align-top">${ficha(p.id, p.perfect_code)}<span class="mt-1 block text-xs font-normal text-mute">${esc(p.description || "")}</span></th>`).join("")}</tr></thead>
          <tbody class="divide-y divide-line">${vis.length ? vis.map(r => `<tr class="${r.dif ? "bg-amber-500/10" : ""}"><th class="sticky left-0 z-10 whitespace-nowrap bg-card px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-mute">${r.dif ? "● " : ""}${r.l}</th>${r.v.map(x => `<td class="px-4 py-2.5 align-top text-ink">${esc(x) || meio}</td>`).join("")}</tr>`).join("")
            : `<tr><td class="px-4 py-10 text-center text-mute" colspan="${ps.length + 1}">Nenhuma diferença para mostrar.</td></tr>`}</tbody></table></div>`;
    };
    const carregar = async () => { try { const l = ids(); ps = l.length ? await J("/api/compare?ids=" + l.join(",")) : []; desenhar(); } catch (e) { $("#cout").innerHTML = notice(esc(e.message), "red"); } };
    const msg = t => { const m = $("#cmsg"); m.textContent = t; m.classList.toggle("hidden", !t); };
    add.addEventListener("input", () => { clearTimeout(tb); tb = setTimeout(async () => { const v = add.value.trim(); msg(""); if (v.length < 2) return;
      const d = await J("/api/products?size=8&q=" + encodeURIComponent(v)); achados = {}; d.rows.forEach(r => achados[r.perfect_code] = r.id);
      $("#cdl").innerHTML = d.rows.map(r => `<option value="${esc(r.perfect_code)}">${esc(r.description || "")}</option>`).join("");
      if (achados[v]) { const l = ids(); if (l.includes(String(achados[v]))) msg(`${v} já está na comparação.`); else if (l.length >= 4) msg("Já há 4 produtos: tire um antes de adicionar outro."); else { F.set({ ids: [...l, achados[v]].join(",") }); add.value = ""; carregar(); } } }, 200); });
    root.addEventListener("click", e => { const r = e.target.closest("[data-rm]");
      if (r) { F.set({ ids: ids().filter(i => i !== r.dataset.rm).join(",") }); msg(""); carregar(); }
      if (e.target.id === "cclr") { F.set({ ids: "" }); msg(""); carregar(); }
      if (e.target.id === "cdif") { F.toggle("dif", "1"); desenhar(); } });
    carregar();
  }

  // ================= Equivalências =================
  const CRIT = ["Código em comum", "Aplicação em comum", "Mesmo eixo", "Mesmo lado", "Lmax igual", "Lmin igual", "Mesmo sistema", "Mesma família"];
  const DIF = ["Nenhuma aplicação em comum", "Eixo diferente", "Lados diferentes", "São lados opostos", "Lmax difere", "Lmin difere", "Sistema diferente", "Família diferente"];
  const MISS = ["Eixo", "Lado", "Lmax", "Lmin", "Sistema óleo/gás", "Aplicações", "Diâmetro da haste"];
  const ST = { pendente: ["Pendente", "slate"], aprovada: ["Aprovada", "green"], rejeitada: ["Rejeitada", "red"] }, CF = { Alta: "green", "Média": "amber", Baixa: "red" };
  function equivalencias() {
    const F = TW.filtros("equivalencias", ["q", "status", "confidence", "diff", "minscore", "crit", "dif", "miss"]); let pg = 1, d = null, timer;
    root.innerHTML = `<div class="flex flex-col gap-5">
      ${notice("A pontuação (0–100%) mede a <b>similaridade dos dados</b> (códigos, aplicação, medidas, sistema). <b>Não comprova intercambialidade</b> e nenhuma sugestão é aprovada automaticamente.", "blue")}
      <div id="ek" class="grid grid-cols-2 gap-4 lg:grid-cols-4"></div>
      <div id="eq" class="flex flex-col gap-2"></div>
      <form id="ef" class="flex flex-wrap items-center gap-2" autocomplete="off"></form>
      <div id="em" class="flex flex-wrap items-center justify-between gap-3 text-sm text-mute"></div><span id="emsg" class="hidden text-sm" role="status"></span>
      <div id="el" class="flex flex-col gap-3"></div><div id="ep" class="flex items-center justify-center gap-3 text-sm text-mute"></div>
    </div>`;
    const lista = k => (F.get()[k] || "").split("|").filter(Boolean);
    const topo = () => {
      const f = F.get(), sc = d.status_counts || {}, cc = d.conf_counts || {}, dc = d.diff_counts || {}, tot = Object.values(sc).reduce((a, b) => a + b, 0);
      $("#ek").innerHTML = kpi("Sugestões", nf(tot), "com os demais filtros", "blue") + kpi("Pendentes", nf(sc.pendente || 0), "aguardando análise", sc.pendente ? "amber" : "slate")
        + kpi("Aprovadas", nf(sc.aprovada || 0), "equivalência confirmada", "green") + kpi("Rejeitadas", nf(sc.rejeitada || 0), "não são equivalentes", "red");
      $("#eq").innerHTML = `<div class="flex flex-wrap items-center gap-2">${rotulo("Status")}${Object.entries(ST).map(([v, [l]]) => chip(`data-tg="status" data-v="${v}"`, l + "s", f.status === v, sc[v] || 0)).join("")}</div>
        <div class="flex flex-wrap items-center gap-2">${rotulo("Confiança")}${Object.keys(CF).map(v => chip(`data-tg="confidence" data-v="${v}"`, v, f.confidence === v, cc[v] || 0)).join("")}${chip('data-tg="diff" data-v="sem"', "Sem diferenças", f.diff === "sem", dc.sem || 0, true)}</div>`;
    };
    const multi = (k, t, h, L) => { const on = lista(k);
      return `<details class="relative" data-ms><summary class="${botao} cursor-pointer list-none">${t} <b class="text-blue-600" data-mn="${k}">${on.length ? `(${on.length})` : ""}</b> ▾</summary>
        <div class="absolute left-0 z-20 mt-1 flex w-72 flex-col gap-1 rounded-xl border border-line bg-card p-3 shadow-lg"><span class="text-xs text-mute">${h}</span>
        ${L.map(c => `<label class="flex items-center gap-2 text-sm text-ink"><input type="checkbox" data-mk="${k}" value="${esc(c)}" ${on.includes(c) ? "checked" : ""}> ${esc(c)} <span class="ml-auto text-xs text-mute" data-fc="${esc(k + ":" + c)}"></span></label>`).join("")}</div></details>`; };
    // o formulário é desenhado só ao abrir, ao limpar e ao clicar num atalho (redesenhar a cada busca tiraria o foco do campo); as contagens são atualizadas no lugar
    const filtrosF = () => { const s = F.get();
      $("#ef").innerHTML = textoF("q", "Código PERFECT ou de concorrente…", s.q, "min-w-[14rem] flex-1") + selectF("status", "Todos os status", Object.entries(ST).map(([v, [l]]) => [v, l]), s.status)
        + selectF("confidence", "Confiança", Object.keys(CF).map(v => [v, v]), s.confidence) + selectF("diff", "Diferenças", [["sem", "Sem diferenças"], ["com", "Com diferenças"]], s.diff)
        + `<input name="minscore" type="number" min="0" max="100" value="${esc(s.minscore || "")}" placeholder="Pontuação mín. (%)" class="${campo} w-44">`
        + multi("crit", "Critérios atendidos", "todos os marcados precisam ser atendidos", CRIT) + multi("dif", "Diferenças", "exigir que apareçam", DIF) + multi("miss", "Dados ausentes", "exigir que apareçam", MISS)
        + `<button type="button" id="eclr" class="${botao}">Limpar filtros</button>`; contagens(); };
    const contagens = () => { const fc = d?.facets || {}; $$("#ef [data-fc]").forEach(x => x.textContent = d ? nf(fc[x.dataset.fc] ?? 0) : "");
      ["crit", "dif", "miss"].forEach(k => { const n = lista(k).length, m = $(`#ef [data-mn="${k}"]`); if (m) m.textContent = n ? `(${n})` : ""; }); };
    const cartao = e => `<article class="rounded-2xl border border-line bg-card p-4 shadow-sm">
      <div class="flex flex-wrap items-center gap-2"><b class="text-base">${ficha(e.product_a, e.a_code)} <span class="text-mute">×</span> ${ficha(e.product_b, e.b_code)}</b>${badge("Confiança " + e.confidence, CF[e.confidence])}${badge(ST[e.status]?.[0] || e.status, ST[e.status]?.[1])}
        <a class="ml-auto text-sm font-semibold text-blue-600" href="/comparacao?ids=${e.product_a},${e.product_b}">Comparar lado a lado →</a></div>
      <div class="mt-3 flex items-center gap-3"><div class="h-2 flex-1 rounded-full bg-slate-500/15"><div class="h-2 rounded-full ${{ Alta: "bg-emerald-500", "Média": "bg-amber-500" }[e.confidence] || "bg-red-500"}" title="Cor = confiança (diferença crítica, como lados opostos, rebaixa a confiança mesmo com pontuação alta)" style="width:${Math.max(0, Math.min(100, e.score))}%"></div></div><span class="text-sm font-semibold tabular-nums text-ink">${nf(e.score)}%</span></div>
      <p class="mb-0 mt-2 text-xs text-mute">${esc(e.a_desc || "")} · ${esc(e.b_desc || "")}</p>
      <div class="mt-2 flex flex-wrap gap-1">${e.criteria.map(x => badge(x, "green")).join(" ")}${e.differences.map(x => badge(x, "red")).join(" ")}${e.missing.map(x => badge(x, "amber")).join(" ")}</div>
      <div class="mt-3 flex flex-wrap items-center gap-2"><span class="text-xs text-mute">Fontes: ${esc(e.sources || "–")}</span><span class="ml-auto inline-flex overflow-hidden rounded-lg border border-line">${[["pendente", "Pendente"], ["aprovada", "Aprovar"], ["rejeitada", "Rejeitar"]].map(([s, l]) =>
        `<button type="button" data-eq="${e.id}" data-s="${s}" aria-pressed="${e.status === s}" class="px-3 py-1.5 text-sm font-semibold ${e.status === s ? "bg-blue-600 text-white" : "bg-card text-ink hover:bg-slate-500/10"}">${l}</button>`).join("")}</span></div></article>`;
    const carregar = async () => { try {
      const s = F.get(); d = await J("/api/equivalences?" + qs({ ...s, page: pg })); topo(); contagens();
      $("#em").innerHTML = metaLinha(d.total, "sugestão(ões)", F, pg, "") + `<span class="flex flex-wrap gap-2"><button type="button" id="egen" class="${botao}">Gerar / atualizar sugestões</button>
        <a class="${primario}" href="/api/equivalences/export.xlsx?${new URLSearchParams(s)}">⬇ Baixar Excel</a></span>`;
      $("#el").innerHTML = d.rows.length ? d.rows.map(cartao).join("") : TW.empty(Object.keys(s).length ? "Nenhuma sugestão com esses filtros." : "Nenhuma sugestão ainda. Clique em <b>Gerar / atualizar sugestões</b>.");
      $("#ep").innerHTML = pager(pg, Math.max(1, Math.ceil(d.total / d.size)));
    } catch (e) { $("#el").innerHTML = notice(esc(e.message), "red"); } };
    const aplicar = (patch, logo) => { if (patch) F.set(patch); pg = 1; clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 300); };
    const aviso = (t, err) => { const m = $("#emsg"); m.innerHTML = t; m.classList.toggle("hidden", !t); m.classList.toggle("text-red-600", !!err); m.classList.toggle("text-emerald-600", !err); };
    $("#ef").addEventListener("input", e => { const t = e.target;
      if (t.dataset.mk) return aplicar({ [t.dataset.mk]: $$(`#ef [data-mk="${t.dataset.mk}"]:checked`).map(x => x.value).join("|") }, true);
      if (t.name) aplicar({ [t.name]: t.value }, t.tagName === "SELECT"); });
    $("#ef").addEventListener("submit", e => e.preventDefault());
    $("#ef").addEventListener("toggle", e => { if (e.target.open) $$("#ef details[open]").forEach(x => { if (x !== e.target) x.open = false; }); }, true);
    document.addEventListener("click", e => { if (!e.target.closest("[data-ms]")) $$("#ef details[open]").forEach(x => x.open = false); });
    root.addEventListener("click", async e => {
      const tg = e.target.closest("[data-tg]"), b = e.target.closest("[data-eq]"), p = e.target.closest("[data-p]");
      if (e.target.id === "eclr") { F.clear(); aviso(""); filtrosF(); return aplicar(null, true); }
      if (tg) { F.toggle(tg.dataset.tg, tg.dataset.v); filtrosF(); return aplicar(null, true); }
      if (b) { try { await post("/api/equivalences/" + b.dataset.eq, { status: b.dataset.s }); carregar(); } catch (er) { aviso(esc(er.message), true); } return; }
      if (p && !p.disabled) { pg = +p.dataset.p; carregar(); scrollTo(0, 0); return; }
      if (e.target.id === "egen") { const g = e.target; g.disabled = true; g.textContent = "Calculando…"; aviso("");
        try { const r = await post("/api/equivalences/generate"); aviso(`✔ ${nf(r.candidates)} pares analisados; ${nf(r.saved)} sugestões (≥ 50%)${r.removed_stale ? `; ${nf(r.removed_stale)} pendente(s) obsoleta(s) removida(s)` : ""}. Os status já definidos foram preservados.`); }
        catch (er) { aviso(esc(er.message), true); } pg = 1; carregar(); }
    });
    filtrosF(); carregar();
  }

  PSD.tela("aplicacoes", aplicacoes);
  PSD.tela("comparacao", comparacao);
  PSD.tela("equivalencias", equivalencias);
})();
