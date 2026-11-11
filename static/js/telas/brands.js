/* Tela · Brands: PERFECT · BPROAUTO · MOTRIO · MOTORCRAFT.
   Usa o núcleo window.PSD (core.js); registra a tela com PSD.tela(slug, desenhar). Separado do antigo pages.js na etapa 16. */
(function () {
  const { $, $$, esc, J, qs, num, T, lnk, empty, root, page, fail, tag, clip, FLG, flagChips, dwFill, dwCol } = PSD;
  // ---------- Brands: PERFECT · BPROAUTO · MOTRIO · MOTORCRAFT ----------
  async function brandsPage() {
    const BC = { PERFECT: "#d4372c", BPROAUTO: "#2f7de1", MOTRIO: "#f2c12e", MOTORCRAFT: "#7c8cff", OUTROS: "#7b8794" }, NAME = { PERFECT: "PERFECT", BPROAUTO: "BPROAUTO", MOTRIO: "MOTRIO", MOTORCRAFT: "MOTORCRAFT", OUTROS: "Sem marca" };
    try {
      const s = await J("/api/brands"); let cur = new URLSearchParams(location.search).get("b") || "PERFECT";
      const cards = [...s.brands]; if (s.unclassified) cards.push({ brand: "OUTROS", rule: "Não se encaixa em nenhuma regra", total: s.unclassified, catalog: 0, des: 0, rd: 0, base: 0, pend_compras: 0 });
      root.innerHTML = `<div class="notice">Itens agrupados pelo código: <b>AMD…</b> = PERFECT · <b>1BP…</b> = BPROAUTO · <b>somente números</b> = MOTRIO · itens da base <b>ItensMotorcraft</b> (PN Ford, e mesma família de código) = MOTORCRAFT. Reúne catálogo, desenvolvimento, redesenvolvimento e pedidos de amostra.</div>
        <div class="brand-grid" id="bg">${cards.map(b => `<button type="button" class="bcard ${b.brand === cur ? "on" : ""}" data-b="${b.brand}" style="--bc:${BC[b.brand]}"><h3>${NAME[b.brand]}</h3><div class="bn">${num(b.total)}</div><small>${esc(b.rule)}</small>
          <div class="bch">${b.catalog ? `<span>Catálogo ${num(b.catalog)}</span>` : ""}${b.des ? `<span>DES ${num(b.des)}</span>` : ""}${b.rd ? `<span>R-D ${num(b.rd)}</span>` : ""}${b.base ? `<span>Base ${num(b.base)}</span>` : ""}${b.pend_compras ? `<span>Pend. compras ${num(b.pend_compras)}</span>` : ""}</div></button>`).join("")}</div>
        <form class="toolbar" id="bf"><input name="q" placeholder="Buscar código, descrição ou veículo…" style="flex:1;min-width:240px">
        <select name="scope"><option value="">Onde está: todos</option><option value="catalog">No catálogo</option><option value="des">Em desenvolvimento (DES)</option><option value="rd">Em redesenvolvimento (R-D)</option><option value="base">Na base Motorcraft</option></select>
        <select name="flag"><option value="">Controle de status</option>${Object.entries(FLG).map(([k, v]) => `<option value="${k}">${v[0]}</option>`).join("")}</select><a class="btn" id="bdl" href="#">⬇ Baixar Excel</a></form>
        <div class="summary" id="bsum"></div><div id="bt"></div><div class="pager" id="bpg"></div>`;
      const f = $("#bf"); let pg = 1, tm;
      const load = async () => { try {
        const fv = Object.fromEntries(new FormData(f)); $("#bdl").href = "/api/export/brands.xlsx?" + qs({ ...fv, brand: cur === "OUTROS" ? "" : cur });
        const d = await J(`/api/brands/${cur}/items?` + qs({ ...fv, page: pg })), pages = Math.max(1, Math.ceil(d.total / d.size));
        $("#bsum").textContent = `${NAME[cur]} · ${num(d.total)} item(ns)`;
        $("#bt").innerHTML = d.rows.length ? T(["Código", "Código PERFECT", "Descrição", "Veículo / aplicação", "Onde está", "Controle de status", "Desenho", "Amostras"], d.rows.map(i => {
          const code = i.catalog && i.product_id ? lnk(i.product_id, i.code) : i.des ? `<a href="#" data-rd="des" data-code="${esc(i.code)}">${esc(i.code)}</a>` : i.rd ? `<a href="#" data-rd="rd" data-code="${esc(i.code)}">${esc(i.code)}</a>` : esc(i.code);
          return `<tr><td>${code}</td><td>${(i.perfect_codes || []).length ? i.perfect_codes.map(c => `<a class="pcode" href="/pesquisa?q=${encodeURIComponent(c)}">${esc(c)}</a>`).join(" ") : (i.brand === "PERFECT" ? '<span class="muted">é o próprio</span>' : '<span class="muted">sem relação</span>')}</td><td>${clip(i.description)}</td><td>${clip(i.vehicle)}</td><td>${[i.catalog && tag("Catálogo"), i.des && tag("DESENVOLVIMENTO"), i.rd && tag("REDESENVOLVIMENTO"), i.base && '<span class="tag">Base Motorcraft</span>'].filter(Boolean).join(" ")}</td><td class="fcell">${flagChips(i.flags)}</td>${dwCol(i.code)}<td>${i.samples ? `<a href="/amostras?q=${encodeURIComponent(i.code)}">${i.samples}</a>` : "–"}</td></tr>`; })) : empty("Nenhum item com esses filtros.");
        $("#bpg").innerHTML = pages > 1 ? `<button class="btn ghost" data-p="${pg - 1}" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button class="btn ghost" data-p="${pg + 1}" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
        dwFill($("#bt"));
      } catch (e) { fail(e); } };
      f.addEventListener("input", () => { clearTimeout(tm); tm = setTimeout(() => { pg = 1; load(); }, 300); }); f.addEventListener("submit", e => e.preventDefault());
      $("#bpg").addEventListener("click", e => { const b = e.target.closest("[data-p]"); if (b && !b.disabled) { pg = +b.dataset.p; load(); scrollTo(0, 0); } });
      $("#bg").addEventListener("click", e => { const b = e.target.closest("[data-b]"); if (!b) return; cur = b.dataset.b; pg = 1; $$(".bcard", root).forEach(x => x.classList.toggle("on", x === b)); load(); });
      load();
    } catch (e) { fail(e); }
  }
  PSD.tela("brands", () => brandsPage());
})();
