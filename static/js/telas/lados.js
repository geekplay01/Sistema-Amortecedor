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
  const chip = (attrs, label, on, n, forte = false) => `<button type="button" ${attrs} aria-pressed="${on}" class="psd-chip${forte ? " forte" : ""}">${label}${n != null ? `<span class="n">${nf(n)}</span>` : ""}</button>`;
  const OUTRO = { exata: "Possuímos (relacionado / mesma aplicação)", desenvolvimento: "Em DES/R-D (servidor)", provavel: "Provável (confira a versão)", nao: "NÃO possuímos", sem_aplicacao: "Sem aplicação cadastrada" };
  const REAR = { com: "Com traseiro encontrado", sem: "Dianteiro sem traseiro" }, PAR = { com: "Com par do outro lado", sem: "LD/LE sem par" }, SIT = { ativo: "Ativo", em_breve: "Em breve", inativo: "Inativo" };
  const lado = s => s ? badge(SDL[s], s === "direito" ? "blue" : s === "esquerdo" ? "violet" : "slate") : nada();

  async function ladosPage() {
    const F = TW.filtros("lados", CHAVES); let pg = 1, timer, LV = {}, st = null;
    root.innerHTML = `<div class="flex flex-col gap-5">
      <p class="m-0 text-xs font-semibold uppercase tracking-wide text-mute">Outro eixo · ordem de busca, do mais confiável ao menos</p>
      <div id="lleg" class="flex flex-wrap gap-1.5"></div>
      <div id="lk" class="grid grid-cols-2 gap-4 lg:grid-cols-4"></div>
      <div id="lf"></div>
      <div id="lq" class="psd-atalhos"></div>
      <div id="lmeta" class="text-sm text-mute"></div>
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
      $("#lq").innerHTML = `<span class="t">Atalhos</span>` + ATALHOS.map(([l, k, a, forte]) => chip(`data-at="${a}"`, l, ligado(a), s[k], forte)).join("");
    };
    /* barra (etapa 19 · Q6): Escopo, Eixo e Lado à vista; Outro eixo, Traseiro, Par e Situação em «Mais filtros»; os atalhos combinados ficam logo abaixo */
    let maisAberto = false;
    const desenharFiltros = () => {
      const f = F.get(), s = st || {}, c = k => s[k] != null ? s[k] : null, todos = [{ v: "", l: "Todos" }];
      TW.pintarBarra($("#lf"), {
        busca: { valor: f.q, ph: "Código, descrição, veículo, par ou traseiro…" },
        principais: [{ k: "escopo", rotulo: "Escopo", tipo: "seg", atual: f.escopo || "", opcoes: [{ v: "", l: "Com lados (LD/LE)" }, { v: "todos", l: "Todos diant./tras." }] },
                     { k: "axle", rotulo: "Eixo", tipo: "lista", atual: f.axle || "", opcoes: [...todos, { v: "dianteiro", l: "Dianteiro", n: c("dianteiro") }, { v: "traseiro", l: "Traseiro", n: c("traseiro") }, { v: "cabine", l: "Cabine" }] },
                     { k: "side", rotulo: "Lado", tipo: "lista", atual: f.side || "", opcoes: [...todos, { v: "direito", l: "Direito (LD)", n: c("direito") }, { v: "esquerdo", l: "Esquerdo (LE)", n: c("esquerdo") }] }],
        mais: [{ k: "other", rotulo: "Outro eixo pela aplicação", atual: f.other || "", opcoes: Object.entries(OUTRO).map(([v, l]) => ({ v, l, n: v === "sem_aplicacao" ? c("sem_aplicacao") : null })) },
               { k: "rear", rotulo: "Traseiro", atual: f.rear || "", opcoes: Object.entries(REAR).map(([v, l]) => ({ v, l })) },
               { k: "pair", rotulo: "Par", atual: f.pair || "", opcoes: [{ v: "com", l: PAR.com, n: c("com_par") }, { v: "sem", l: PAR.sem, n: c("sem_par") }] },
               { k: "status", rotulo: "Situação", atual: f.status || "", opcoes: Object.entries(SIT).map(([v, l]) => ({ v, l, n: c(v) })) }],
        aberto: maisAberto,
        etiquetas: TW.etiquetas(f, { axle: "Eixo", side: "Lado", other: "Outro eixo", rear: "Traseiro", pair: "Par", status: "Situação", q: "Busca" },
          (k, v) => ({ axle: AXL, side: { direito: "Direito (LD)", esquerdo: "Esquerdo (LE)" }, other: OUTRO, rear: REAR, pair: PAR, status: SIT }[k] || {})[v] || v),
        acoes: TW.botao("Baixar Excel", { href: `/api/export/lados.xlsx?${new URLSearchParams(f)}`, icone: "download" })
      });
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
        desenharTopo(); desenharFiltros();
        $("#lmeta").innerHTML = `<b class="text-ink">${nf(d.total)}</b> item(ns)${ativos ? ` · ${ativos} filtro(s) ativo(s)` : ""}`;
        $("#lt").innerHTML = TW.table([{ h: "Código" }, { h: "Descrição", nw: false }, { h: "Eixo" }, { h: "Lado" }, { h: "Par (outro lado)" }, { h: "Traseiro (mesma aplicação)", nw: false }, { h: "Dianteiro (mesma aplicação)", nw: false },
          { h: "Possuímos?" }, { h: "Conjunto do veículo", nw: false }, { h: "Veículos", nw: false }], d.rows.map(i => [
          `<a href="#" class="font-semibold text-blue-600" data-ficha="${i.id}">${esc(i.code)}</a>${window.psdCode ? " " + psdCode(i.code, "↗") : ""}${i.status !== "ativo" ? " " + badge(i.status === "inativo" ? "inativo" : "em breve", i.status === "inativo" ? "red" : "amber") : ""}`,
          `<span class="block min-w-[14rem] max-w-[22rem] truncate" title="${esc(i.description || "")}">${esc(i.description || "")}</span>`, AXL[i.axle] || nada(), lado(i.side), par(i),
          outroEixo(i.rear, i.axle === "dianteiro"), outroEixo(i.front, i.axle === "traseiro"),
          POSSUI[i.other_axle] ? badge(...POSSUI[i.other_axle]) : i.other_axle === "sem_aplicacao" ? nada("sem aplicação") : nada(), conjunto(i), veiculos(i)]), { h: "max-h-[65vh]" });
        $("#lp").innerHTML = pages > 1 ? `<button type="button" data-p="${pg - 1}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button type="button" data-p="${pg + 1}" class="rounded-lg border border-line bg-card px-3 py-1.5 text-ink" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
      } catch (e) { $("#lt").innerHTML = notice(esc(e.message), "red"); }
    };

    const aplicar = (logo = false) => { pg = 1; if (st) desenharTopo(); desenharFiltros(); clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 300); };
    TW.ligarBarra($("#lf"), { set: (k, v) => { F.set({ [k]: v }); aplicar(true); }, busca: t => { F.set({ q: t }); aplicar(true); },
      limpar: () => { const esc0 = F.get().escopo; F.clear(); if (esc0) F.set({ escopo: esc0 }); aplicar(true); }, mais: ab => { maisAberto = ab; } });
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
