/* Tela · Lados: par LD × LE e traseiro da mesma aplicação.
   Usa o núcleo window.PSD (core.js); registra a tela com PSD.tela(slug, desenhar). Separado do antigo pages.js na etapa 16. */
(function () {
  const { $, esc, J, qs, num, T, lnk, empty, root, page, fail, clip } = PSD;
  // ---------- Lados: item, lado, par e traseiro da mesma aplicação ----------
  async function ladosPage() {
    const AXL = { dianteiro: "Dianteiro", traseiro: "Traseiro", cabine: "Cabine", ambos_eixos: "Diant./Tras." }, SDL = { direito: "LD", esquerdo: "LE", ambos: "LD/LE" };
    const sd = s => s ? `<span class="sd ${s}">${SDL[s]}</span>` : '<span class="muted">–</span>';
    let LV = {};
    const rch = x => { const tip = (LV[x.level] || x.level) + (x.app ? ` · ${x.app}` : "") + (x.status ? ` · status ${x.status}` : "") + (x.pair ? ` · par: ${x.pair.code}` : "");
      const body = `${esc(x.code)} <i>${SDL[x.side] || ""}</i>${x.level === "provavel" ? "?" : ""}${x.pair ? `<span class="rp">+ ${esc(x.pair.code)} ${SDL[x.pair.side] || ""}</span>` : ""}`;
      return x.id ? `<a href="#" data-ficha="${x.id}" class="rchip ${x.level}" title="${esc(tip)}">${body}</a>` : `<a href="/desenvolvimento?q=${encodeURIComponent(x.code)}" class="rchip ${x.level}" title="${esc(tip)}">${body} <i>DES</i></a>`; };
    const kit = i => (i.kit || []).length > 1 ? `<span class="kit">${i.kit.map((k, n) => `${n ? '<span class="plus">+</span>' : ""}<span class="k ${k.axle === "dianteiro" ? "f" : "t"}" title="${k.axle}${k.src ? " · " + esc(LV[k.src] || k.src) : ""}">${esc(k.code)} <i>${SDL[k.side] || ""}${k.qty === 2 ? " ×2" : ""}</i></span>`).join("")}</span>` : '<span class="muted">–</span>';
    root.innerHTML = `<div class="notice">Amortecedores <b>do catálogo (CatalogoAMD.xlsx)</b>. O <b>par LD × LE</b> vem da planilha <b>Lados - Amortecedores.xlsx</b> (ou, se ela não cobrir, dos Produtos Relacionados / aplicação). O <b>traseiro</b> (e, nos traseiros, o dianteiro) é interpretado automaticamente, nesta ordem:
      <span class="rchip relacionado">Produtos Relacionados</span> do catálogo · <span class="rchip exata">mesma aplicação</span> do catálogo · <span class="rchip servidor">mesma aplicação no servidor</span> (DES/R-D) · <span class="rchip desenvolvimento">em desenvolvimento</span> (ainda fora do catálogo) · <span class="rchip provavel">provável ?</span> (mesmo modelo-base, confira a versão). Cada traseiro mostra também o <b>par</b> dele, e a coluna <b>Conjunto</b> monta o jogo completo do veículo.</div>
      <div class="cards mini-cards" id="ls"></div>
      <form class="toolbar" id="lf"><input name="q" placeholder="Buscar código, descrição, veículo…" style="flex:1;min-width:240px">
        <select name="escopo"><option value="lados">Itens com lados (LD/LE) e da planilha Lados</option><option value="todos">Todos os dianteiros/traseiros do catálogo</option></select>
        <select name="axle"><option value="">Eixo: todos</option><option value="dianteiro">Dianteiro</option><option value="traseiro">Traseiro</option><option value="cabine">Cabine</option></select>
        <select name="side"><option value="">Lado: todos</option><option value="direito">Direito (LD)</option><option value="esquerdo">Esquerdo (LE)</option></select>
        <select name="other"><option value="">Traseiro/dianteiro pela aplicação: todos</option><option value="exata">Possuímos (relacionado / mesma aplicação)</option><option value="desenvolvimento">Em desenvolvimento (servidor)</option><option value="provavel">Provável (confira a versão)</option><option value="nao">NÃO possuímos</option><option value="sem_aplicacao">Sem aplicação cadastrada</option></select>
        <select name="rear"><option value="">Traseiro: todos</option><option value="com">Com traseiro encontrado</option><option value="sem">Dianteiro sem traseiro</option></select>
        <select name="pair"><option value="">Par: todos</option><option value="com">Com par do outro lado</option><option value="sem">LD/LE sem par</option></select>
        <select name="status"><option value="">Situação: todas</option><option value="ativo">Ativo</option><option value="em_breve">Em breve</option><option value="inativo">Inativo</option></select><a class="btn" id="lxl" href="#">⬇ Baixar Excel</a></form>
      <div class="summary" id="lsum"></div><div id="lt"></div><div class="pager" id="lpg"></div>`;
    const f = $("#lf"); let pg = 1, tm;
    const load = async () => { try {
      const fv = Object.fromEntries(new FormData(f)); $("#lxl").href = "/api/export/lados.xlsx?" + qs(fv);
      const d = await J("/api/sides?" + qs({ ...fv, page: pg })), s = d.stats, pages = Math.max(1, Math.ceil(d.total / d.size)); LV = d.levels || {};
      $("#ls").innerHTML = [[d.escopo === "todos" ? "Dianteiros + traseiros" : "Com lados (LD/LE)", s.total, ""], ["Dianteiros", s.dianteiro, "axle=dianteiro"], ["Traseiros", s.traseiro, "axle=traseiro"], ["Traseiro confirmado", s.traseiro_exato, "other=exata&axle=dianteiro"], ["Traseiro em desenvolvimento", s.traseiro_desenvolvimento, "other=desenvolvimento&axle=dianteiro"], ["Traseiro provável", s.traseiro_provavel, "other=provavel&axle=dianteiro"], ["SEM traseiro", s.traseiro_nao, "other=nao&axle=dianteiro"], ["Sem aplicação", s.sem_aplicacao, "other=sem_aplicacao"], ["Sem par do outro lado", s.sem_par, "pair=sem"]]
        .map(([l, v, a]) => `<button type="button" class="card stat" ${a ? `data-fs="${a}"` : ""}><span class="num sm">${num(v)}</span><small>${l}</small></button>`).join("");
      $("#lsum").textContent = num(d.total) + " item(ns)";
      $("#lt").innerHTML = d.rows.length ? T(["Código", "Descrição", "Eixo", "Lado", "Par (outro lado)", "Traseiro (mesma aplicação)", "Dianteiro (mesma aplicação)", "Possuímos?", "Conjunto do veículo", "Veículos"], d.rows.map(i => `<tr><td>${lnk(i.id, i.code)} ${window.psdCode ? psdCode(i.code, "↗") : ""}</td><td>${clip(i.description)}</td><td>${AXL[i.axle] || "–"}</td><td>${sd(i.side)}</td>
          <td>${i.pair ? `<a href="#" data-ficha="${i.pair.id}" class="rchip exata" title="${esc(i.pair_how || "")}">${esc(i.pair.code)} <i>${SDL[i.pair.side] || ""}</i></a>` : (i.side === "ambos" ? '<span class="muted" title="Um código atende os dois lados">mesmo código</span>' : '<span class="muted">–</span>')}</td>
          <td>${i.axle === "dianteiro" ? (i.rear.length ? i.rear.slice(0, 3).map(rch).join("") + (i.rear.length > 3 ? `<span class="xchip more" title="${esc(i.rear.slice(3).map(x => x.code).join(" · "))}">+${i.rear.length - 3}</span>` : "") : '<span class="muted">não encontrado</span>') : '<span class="muted">–</span>'}</td>
          <td>${i.axle === "traseiro" ? (i.front.length ? i.front.slice(0, 3).map(rch).join("") + (i.front.length > 3 ? `<span class="xchip more" title="${esc(i.front.slice(3).map(x => x.code).join(" · "))}">+${i.front.length - 3}</span>` : "") : '<span class="muted">não encontrado</span>') : '<span class="muted">–</span>'}</td>
          <td>${{ exata: '<span class="sd direito">Sim</span>', desenvolvimento: '<span class="sd ambos">Em DES</span>', provavel: '<span class="sd ambos">Provável</span>', nao: '<span class="sd esquerdo">NÃO</span>', sem_aplicacao: '<span class="muted">sem aplicação</span>' }[i.other_axle] || '<span class="muted">–</span>'}</td>
          <td>${kit(i)}</td>
          <td><span class="clip" title="${esc([...i.vehicles, ...(i.server_apps || []).map(a => "servidor: " + a)].join("\n"))}">${esc((i.vehicles.length ? i.vehicles : (i.server_apps || [])).slice(0, 2).join(" | "))}${i.vehicles.length > 2 ? ` <small class="muted">+${i.vehicles.length - 2}</small>` : ""}</span></td></tr>`)) : empty("Nenhum item com esses filtros.");
      $("#lpg").innerHTML = pages > 1 ? `<button class="btn ghost" data-p="${pg - 1}" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button class="btn ghost" data-p="${pg + 1}" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
    } catch (e) { fail(e); } };
    f.addEventListener("input", () => { clearTimeout(tm); tm = setTimeout(() => { pg = 1; load(); }, 300); }); f.addEventListener("submit", e => e.preventDefault());
    $("#lpg").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; load(); scrollTo(0, 0); } });
    $("#ls").addEventListener("click", e => { const b = e.target.closest("[data-fs]"); if (!b) return; [...f.elements].forEach(x => { if (x.name && x.name !== "q" && x.name !== "escopo") x.value = ""; }); new URLSearchParams(b.dataset.fs).forEach((v, k) => f.elements[k].value = v); pg = 1; load(); });
    const q0 = new URLSearchParams(location.search).get("q"); if (q0) f.elements.q.value = q0;
    load();
  }
  PSD.tela("lados", () => ladosPage());
})();
