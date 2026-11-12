/* Tela · Lados — visual Tailwind (etapa 16): par LD × LE, amortecedor do outro eixo da mesma aplicação e o conjunto do veículo.
   Regras e ordem das fontes em sides.py. Cada número do topo é um atalho (liga/desliga) e bate com o total da lista filtrada (tests: test_19).
   Filtros na URL e lembrados por tela (PSDTW.filtros); o Excel segue os mesmos filtros. Ficha: clique no código (data-ficha → PSD.openFicha). */
(function () {
  const { $, esc, J, qs, root, fail } = PSD;
  const TW = window.PSDTW, { nf, badge, kpi, notice } = TW;
  const CHAVES = ["q", "escopo", "axle", "side", "other", "rear", "pair", "status"], ATALHO = ["axle", "side", "other", "rear", "pair", "status"];
  const AXL = { dianteiro: "Dianteiro", traseiro: "Traseiro", cabine: "Cabine", ambos_eixos: "Diant./Tras." }, SDL = { direito: "LD", esquerdo: "LE", ambos: "LD/LE" };
  const NIVEL = { relacionado: "violet", exata: "green", servidor: "blue", desenvolvimento: "amber", provavel: "slate" };
  const POSSUI = { exata: ["Sim", "green"], desenvolvimento: ["Em DES/R-D", "amber"], provavel: ["Provável", "slate"], nao: ["NÃO", "red"] };
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500";
  const nada = t => `<span class="text-mute">${t || "–"}</span>`;
  const chip = (attrs, label, on, n, forte = false) => `<button type="button" ${attrs} aria-pressed="${on}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${on ? "border-blue-500 bg-blue-500 text-white" : forte ? "border-amber-500 bg-amber-500/10 text-ink hover:bg-amber-500/20" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${label}${n != null ? ` · ${nf(n)}` : ""}</button>`;
  const selectF = (name, rotulo, opts, cur) => `<select name="${name}" class="${campo} max-w-[15rem]" title="${esc(rotulo)}"><option value="">${esc(rotulo)}</option>${opts.map(([v, l]) => `<option value="${esc(v)}" ${String(v) === String(cur ?? "") ? "selected" : ""}>${esc(l)}</option>`).join("")}</select>`;
  const lado = s => s ? badge(SDL[s], s === "direito" ? "blue" : s === "esquerdo" ? "violet" : "slate") : nada();

  async function ladosPage() {
    const F = TW.filtros("lados", CHAVES); let pg = 1, timer, LV = {}, st = null;
    root.innerHTML = `<div class="flex flex-col gap-5">
      <p class="m-0 text-sm text-mute">Amortecedores <b class="text-ink">do catálogo (CatalogoAMD.xlsx)</b>. O <b class="text-ink">par LD × LE</b> vem da planilha <b class="text-ink">Lados - Amortecedores.xlsx</b>; se ela não cobrir, dos Produtos Relacionados ou da aplicação.
        O amortecedor do <b class="text-ink">outro eixo</b> (traseiro de um dianteiro e vice-versa) é procurado nesta ordem, do mais confiável ao menos:</p>
      <div id="lleg" class="flex flex-wrap gap-1.5"></div>
      <div id="lk" class="grid grid-cols-2 gap-4 lg:grid-cols-4"></div>
      <div id="lq" class="flex flex-wrap items-center gap-2"></div>
      <form id="lf" class="flex flex-wrap items-center gap-2" autocomplete="off"></form>
      <div id="lmeta" class="flex flex-wrap items-center justify-between gap-3 text-sm text-mute"></div>
      <div id="lt"></div><div id="lp" class="flex items-center justify-center gap-3 text-sm text-mute"></div>
    </div>`;

    // atalhos: cada um é um conjunto de filtros; ligado = todos batem. Ligar troca os outros atalhos; clicar de novo desliga.
    const ATALHOS = [["Dianteiros", "dianteiro", "axle=dianteiro"], ["Traseiros", "traseiro", "axle=traseiro"], ["Traseiro confirmado", "traseiro_exato", "axle=dianteiro&other=exata"],
      ["Traseiro em DES/R-D", "traseiro_desenvolvimento", "axle=dianteiro&other=desenvolvimento"], ["Traseiro provável", "traseiro_provavel", "axle=dianteiro&other=provavel"],
      ["SEM traseiro", "traseiro_nao", "axle=dianteiro&other=nao", true], ["Sem par do outro lado", "sem_par", "pair=sem", true], ["Sem aplicação", "sem_aplicacao", "other=sem_aplicacao"],
      ["LD", "direito", "side=direito"], ["LE", "esquerdo", "side=esquerdo"], ["Inativos", "inativo", "status=inativo"]];
    const ligado = a => { const s = F.get(); return [...new URLSearchParams(a)].every(([k, v]) => s[k] === v); };

    const desenharTopo = () => {
      const s = st, todos = F.get().escopo === "todos";
      $("#lleg").innerHTML = ["relacionado", "exata", "servidor", "desenvolvimento", "provavel"].map((k, i) => `<span title="${esc(LV[k] || k)}">${badge(`${i + 1}. ${LV[k] || k}`, NIVEL[k])}</span>`).join("");
      $("#lk").innerHTML = kpi(todos ? "Dianteiros + traseiros" : "Itens com lados (LD/LE)", nf(s.total), `${nf(s.dianteiro)} dianteiros · ${nf(s.traseiro)} traseiros`, "blue") +
        kpi("Traseiro confirmado", nf(s.traseiro_exato), `de ${nf(s.dianteiro)} dianteiros · ${nf(s.traseiro_provavel)} provável(is)`, "green") +
        kpi("Dianteiro SEM traseiro", nf(s.traseiro_nao), `${nf(s.traseiro_desenvolvimento)} com traseiro em DES/R-D`, "red") +
        kpi("Sem par do outro lado", nf(s.sem_par), `${nf(s.pares_planilha)} pares da planilha · ${nf(s.pares_automaticos)} automáticos`, "amber");
      $("#lq").innerHTML = `<span class="mr-1 text-xs font-semibold uppercase tracking-wide text-mute">Atalhos</span>` + ATALHOS.map(([l, k, a, forte]) => chip(`data-at="${a}"`, l, ligado(a), s[k], forte)).join("");
    };
    const desenharFiltros = () => {
      const f = F.get(), s = st || {}, c = k => s[k] != null ? ` (${nf(s[k])})` : "";
      $("#lf").innerHTML = `<input name="q" type="search" value="${esc(f.q || "")}" placeholder="Buscar código, descrição, veículo, par ou traseiro…" class="${campo} min-w-[16rem] flex-1">` +
        `<select name="escopo" class="${campo} max-w-[17rem]" title="Escopo"><option value="">Itens com lados (LD/LE) e da planilha Lados</option><option value="todos" ${f.escopo === "todos" ? "selected" : ""}>Todos os dianteiros e traseiros do catálogo</option></select>` +
        selectF("axle", "Eixo", [["dianteiro", "Dianteiro" + c("dianteiro")], ["traseiro", "Traseiro" + c("traseiro")], ["cabine", "Cabine"]], f.axle) +
        selectF("side", "Lado", [["direito", "Direito (LD)" + c("direito")], ["esquerdo", "Esquerdo (LE)" + c("esquerdo")]], f.side) +
        selectF("other", "Outro eixo pela aplicação", [["exata", "Possuímos (relacionado / mesma aplicação)"], ["desenvolvimento", "Em DES/R-D (servidor)"], ["provavel", "Provável (confira a versão)"], ["nao", "NÃO possuímos"], ["sem_aplicacao", "Sem aplicação cadastrada" + c("sem_aplicacao")]], f.other) +
        selectF("rear", "Traseiro", [["com", "Com traseiro encontrado"], ["sem", "Dianteiro sem traseiro"]], f.rear) +
        selectF("pair", "Par", [["com", "Com par do outro lado" + c("com_par")], ["sem", "LD/LE sem par" + c("sem_par")]], f.pair) +
        selectF("status", "Situação", [["ativo", "Ativo" + c("ativo")], ["em_breve", "Em breve" + c("em_breve")], ["inativo", "Inativo" + c("inativo")]], f.status) +
        `<button type="button" id="lclr" class="rounded-lg border border-line bg-card px-3.5 py-2 text-sm font-semibold text-ink hover:bg-slate-500/10">Limpar filtros</button>`;
    };

    // célula de candidato do outro eixo: nível pela cor, lado, par dele; código fora do catálogo leva à lista DES/R-D
    const cand = x => {
      const tip = (LV[x.level] || x.level) + (x.app ? ` · ${x.app}` : "") + (x.status ? ` · status ${x.status}` : "") + (x.pair ? ` · par: ${x.pair.code}` : "");
      const corpo = `${esc(x.code)} <span class="font-normal">${SDL[x.side] || ""}</span>${x.level === "provavel" ? "?" : ""}${x.pair ? ` <span class="font-normal">+${esc(x.pair.code)} ${SDL[x.pair.side] || ""}</span>` : ""}`;
      const cls = `mb-1 mr-1 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${{ violet: "bg-violet-500/15 text-violet-600", green: "bg-emerald-500/15 text-emerald-600", blue: "bg-blue-500/15 text-blue-600", amber: "bg-amber-500/20 text-amber-700", slate: "bg-slate-500/15 text-slate-600" }[NIVEL[x.level]]}`;
      return x.id ? `<a href="#" data-ficha="${x.id}" class="${cls}" title="${esc(tip)}">${corpo}</a>`
        : `<a href="/${x.kind === "REDESENVOLVIMENTO" ? "redesenvolvimento" : "desenvolvimento"}?q=${encodeURIComponent(x.code)}" class="${cls}" title="${esc(tip)}">${corpo} <span class="font-normal">${x.kind === "REDESENVOLVIMENTO" ? "R-D" : "DES"}</span></a>`;
    };
    const outroEixo = (lst, aplica) => !aplica ? nada() : lst.length ? lst.slice(0, 3).map(cand).join("") + (lst.length > 3 ? `<span class="text-xs text-mute" title="${esc(lst.slice(3).map(x => x.code).join(" · "))}">+${lst.length - 3}</span>` : "") : nada("não encontrado");
    const conjunto = i => (i.kit || []).length > 1 ? `<span class="inline-flex flex-wrap items-center gap-1">${i.kit.map((k, n) => `${n ? '<span class="text-mute">+</span>' : ""}<span class="rounded-lg px-1.5 py-0.5 text-xs font-semibold ${k.axle === "dianteiro" ? "bg-blue-500/15 text-blue-600" : "bg-slate-500/15 text-slate-600"}" title="${esc(k.axle + (k.src ? " · " + (LV[k.src] || k.src) : ""))}">${esc(k.code)} <span class="font-normal">${SDL[k.side] || ""}${k.qty === 2 ? " ×2" : ""}</span></span>`).join("")}</span>` : nada();
    const veiculos = i => { const v = i.vehicles.length ? i.vehicles : (i.server_apps || []); if (!v.length) return nada();
      return `<span class="block max-w-[18rem] truncate" title="${esc([...i.vehicles, ...(i.server_apps || []).map(a => "servidor: " + a)].join("\n"))}">${esc(v.slice(0, 2).join(" | "))}${v.length > 2 ? ` <span class="text-xs text-mute">+${v.length - 2}</span>` : ""}</span>`; };
    const par = i => i.pair ? `<a href="#" data-ficha="${i.pair.id}" class="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs font-semibold text-emerald-600" title="${esc(i.pair_how || "")}">${esc(i.pair.code)} <span class="font-normal">${SDL[i.pair.side] || ""}</span></a>`
      : i.side === "ambos" ? '<span class="text-mute" title="Um código atende os dois lados">mesmo código</span>' : nada();

    const carregar = async () => {
      const f = F.get();
      $("#lt").innerHTML = `<div class="rounded-2xl border border-line bg-card px-5 py-8 text-sm text-mute">Carregando…</div>`; $("#lp").innerHTML = ""; $("#lmeta").innerHTML = "";
      try {
        const d = await J("/api/sides?" + qs({ ...f, page: pg })), pages = Math.max(1, Math.ceil(d.total / d.size)), ativos = Object.keys(f).filter(k => k !== "escopo").length;
        const novo = !st || JSON.stringify(st) !== JSON.stringify(d.stats); LV = d.levels || {}; st = d.stats;
        desenharTopo(); if (novo) desenharFiltros();
        $("#lmeta").innerHTML = `<span><b class="text-ink">${nf(d.total)}</b> item(ns)${ativos ? ` · ${ativos} filtro(s) ativo(s)` : ""}${F.restaurado && pg === 1 ? ' · <span class="text-amber-700">filtros da última visita</span>' : ""}</span>
          <a class="rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-blue-700" href="/api/export/lados.xlsx?${new URLSearchParams(f)}">⬇ Baixar Excel</a>`;
        $("#lt").innerHTML = TW.table([{ h: "Código" }, { h: "Descrição", nw: false }, { h: "Eixo" }, { h: "Lado" }, { h: "Par (outro lado)" }, { h: "Traseiro (mesma aplicação)", nw: false }, { h: "Dianteiro (mesma aplicação)", nw: false },
          { h: "Possuímos?" }, { h: "Conjunto do veículo", nw: false }, { h: "Veículos", nw: false }], d.rows.map(i => [
          `<a href="#" class="font-semibold text-blue-600" data-ficha="${i.id}">${esc(i.code)}</a>${window.psdCode ? " " + psdCode(i.code, "↗") : ""}${i.status !== "ativo" ? " " + badge(i.status === "inativo" ? "inativo" : "em breve", i.status === "inativo" ? "red" : "amber") : ""}`,
          `<span class="block min-w-[14rem] max-w-[22rem] truncate" title="${esc(i.description || "")}">${esc(i.description || "")}</span>`, AXL[i.axle] || nada(), lado(i.side), par(i),
          outroEixo(i.rear, i.axle === "dianteiro"), outroEixo(i.front, i.axle === "traseiro"),
          POSSUI[i.other_axle] ? badge(...POSSUI[i.other_axle]) : i.other_axle === "sem_aplicacao" ? nada("sem aplicação") : nada(), conjunto(i), veiculos(i)]), { h: "max-h-[65vh]" });
        $("#lp").innerHTML = pages > 1 ? `<button type="button" data-p="${pg - 1}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button type="button" data-p="${pg + 1}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
      } catch (e) { $("#lt").innerHTML = notice(esc(e.message), "red"); }
    };

    const aplicar = (logo = false) => { pg = 1; if (st) desenharTopo(); clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 300); };
    $("#lf").addEventListener("input", e => { const n = e.target.name; if (!n) return; F.set({ [n]: e.target.value }); aplicar(e.target.tagName === "SELECT"); });
    $("#lf").addEventListener("submit", e => e.preventDefault());
    $("#lf").addEventListener("click", e => { if (e.target.id !== "lclr") return; const esc0 = F.get().escopo; F.clear(); if (esc0) F.set({ escopo: esc0 }); desenharFiltros(); aplicar(true); });
    $("#lq").addEventListener("click", e => {
      const b = e.target.closest("[data-at]"); if (!b) return; const a = b.dataset.at, on = ligado(a);
      F.set(Object.fromEntries(ATALHO.map(k => [k, ""]))); if (!on) F.set(Object.fromEntries(new URLSearchParams(a)));
      desenharFiltros(); aplicar(true);
    });
    $("#lp").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; carregar(); scrollTo(0, 0); } });
    desenharFiltros(); await carregar();
  }
  PSD.tela("lados", () => ladosPage().catch(fail));
})();
