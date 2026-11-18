/* Tela · Anomalias (etapa 16 · D1/D2; antiga «Equivalências»). Abas (`tab` na URL):
   · familia  — catálogo × certificados Inmetro: o CatalogoAMD prevalece; lista os produtos com algum certificado de família diferente (anomalias.familia).
   · ean      — conflitos abertos de EAN (catálogo × planilha): «Usar o da planilha» grava o importado; «Manter o do catálogo» resolve sem mudar.
   · pesoean  — peso líquido e código de barras: CatalogoAMD × BI03 (o BI03 prevalece; corrigir a planilha) · etapa 17.
   · protheus — DES/R-D em andamento fora do BI03: «Pendente cadastro Protheus», com atalhos de tipo e status (`tipo`, `status` na URL) · etapa 17.
   · sugestoes — sugestões de equivalência (PSD.equivalencias, em telas/catalogo.js).
   Busca na URL (PSDTW.filtros); trocar de aba abre a aba nova sem filtros. O Excel traz Família e EAN. */
(function () {
  const { $, esc, J, post, qs, root, fail } = PSD;
  const TW = window.PSDTW, { nf, badge, notice, empty } = TW;
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500";
  const primario = "rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white no-underline hover:bg-blue-700";
  const mini = "rounded-lg border border-line bg-card px-2.5 py-1 text-xs font-semibold text-ink hover:bg-slate-500/10";
  const ABAS = [["familia", "Família: catálogo × Inmetro"], ["ean", "EAN divergente"], ["pesoean", "Peso e EAN × BI03"], ["protheus", "Pendente cadastro Protheus"], ["sugestoes", "Sugestões de equivalência"]];
  const aba = (t, label, on, n) => `<a href="/anomalias?tab=${t}" data-aba="${t}" class="-mb-px border-b-2 px-3 py-2 text-sm font-semibold no-underline ${on ? "border-blue-500 text-blue-600" : "border-transparent text-mute hover:text-ink"}">${label}${n != null ? ` · ${nf(n)}` : ""}</a>`;
  const ficha = (id, code) => `<a href="#" class="font-semibold text-blue-600" data-ficha="${id}">${esc(code)}</a>`;
  function anomalias() {
    const pedida = new URLSearchParams(location.search).get("tab"), tab = ABAS.some(([t]) => t === pedida) ? pedida : "familia";
    try { localStorage.removeItem("psd-anomalias-aba"); } catch (e) { }          // a versão anterior lembrava a aba
    root.innerHTML = `<div class="flex flex-col gap-5">
      <nav id="an" class="flex flex-wrap gap-1 border-b border-line">${ABAS.map(([t, l]) => aba(t, l, t === tab)).join("")}</nav><div id="ab" class="flex flex-col gap-5"></div></div>`;
    const abas = c => { $("#an").innerHTML = ABAS.map(([t, l]) => aba(t, l, t === tab, c[t])).join(""); };
    // trocar de aba: a aba nova abre sem filtros (etapa 17 · Q8)
    $("#an").addEventListener("click", e => { const a = e.target.closest("[data-aba]"); if (!a) return; e.preventDefault();
      history.replaceState(null, "", "/anomalias?" + qs({ tab: a.dataset.aba })); anomalias(); });
    J("/api/anomalies").then(r => abas(r.counts)).catch(fail);
    if (tab === "sugestoes") return PSD.equivalencias($("#ab"));

    const F = TW.filtros("anomalias", ["tab", "q", "tipo", "status"]); F.set({ tab }); let timer;
    const AVISO = {
      familia: notice("O <b>CatalogoAMD prevalece</b> na família. Aqui aparecem os produtos com algum certificado Inmetro de família diferente. A importação do Inmetro não abre mais conflito de família: confira o certificado (ou o catálogo) e corrija na origem."),
      ean: notice("EAN do catálogo diferente do que veio na planilha. Nada foi sobrescrito: escolha <b>Usar o da planilha</b> (grava o EAN importado no produto) ou <b>Manter o do catálogo</b>. Os mesmos casos aparecem em <a class=\"text-blue-600\" href=\"/pendencias?field=ean\">Pendências</a>.", "amber"),
      pesoean: notice("O <b>BI03 (cadastro do Protheus) prevalece</b> no peso líquido e no código de barras. Aqui aparecem os itens em que a planilha CatalogoAMD diz outra coisa: corrija a planilha."),
      protheus: notice("Itens de DESENVOLVIMENTO e REDESENVOLVIMENTO em andamento (sem ITEM RECEBIDO, sem cancelado) que <b>ainda não estão no BI03</b> como amortecedor acabado (PA): pendentes de cadastro no Protheus.", "amber") };
    const META = { familia: "produto(s) com família divergente", ean: "EAN divergente(s)", pesoean: "diferença(s) entre o CatalogoAMD e o BI03", protheus: "item(ns) pendente(s) de cadastro no Protheus" };
    const chip = (k, v, label, n) => { const on = F.get()[k] === v; return `<button type="button" data-tg="${k}" data-v="${esc(v)}" aria-pressed="${on}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${on ? "border-blue-500 bg-blue-500 text-white" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${esc(label)} · ${nf(n)}</button>`; };
    $("#ab").innerHTML = AVISO[tab] + (tab === "protheus" ? '<div id="aq" class="flex flex-wrap items-center gap-2"></div>' : "")
      + `<form id="af" class="flex flex-wrap items-center gap-2" autocomplete="off"><input name="q" type="search" placeholder="Buscar código, descrição ou valor…" class="${campo} min-w-[16rem] flex-1">
        <a id="ax" class="${primario}" href="/api/anomalies/export.xlsx">⬇ Baixar Excel</a></form><div id="am" class="text-sm text-mute"></div><div id="at"></div>`;
    $("#af").q.value = F.get().q || "";
    const valor = v => typeof v === "number" ? v.toLocaleString("pt-BR", { maximumFractionDigits: 3 }) : esc(v ?? "–");          // peso 2,1 · EAN como texto
    const desc = r => `<span class="block max-w-[18rem] truncate" title="${esc(r.description || "")}">${esc(r.description || "–")}</span>`;

    const carregar = async () => {
      let d; const s = F.get(), q = s.q || "";
      try { d = await J("/api/anomalies?" + qs({ ...s, tab })); } catch (e) { $("#at").innerHTML = notice(esc(e.message), "red"); return; }
      abas(d.counts); $("#ax").href = "/api/anomalies/export.xlsx" + (q ? "?" + qs({ q }) : "");
      if (d.atalhos) $("#aq").innerHTML = `<span class="mr-1 text-xs font-semibold uppercase tracking-wide text-mute">Atalhos</span>`
        + Object.entries(d.atalhos.tipo).map(([v, n]) => chip("tipo", v, v, n)).join("") + Object.entries(d.atalhos.status).sort((a, b) => b[1] - a[1]).map(([v, n]) => chip("status", v, v, n)).join("");
      const ok = $("#am").dataset.ok; delete $("#am").dataset.ok;
      $("#am").innerHTML = `<b class="text-ink">${nf(d.rows.length)}</b> ${META[tab]}${q ? " · com a busca" : ""}${ok ? ` · <span class="font-semibold text-emerald-600">${esc(ok)}</span>` : ""}`;
      if (!d.rows.length) { $("#at").innerHTML = empty(q ? "Nada encontrado com esta busca." : tab === "protheus" || tab === "pesoean" ? "Nada aqui. Se o BI03 ainda não foi carregado, carregue a planilha «003(dd-mm).xls» em Atualização de dados." : "Nenhuma anomalia: tudo confere."); return; }
      if (tab === "pesoean") { $("#at").innerHTML = TW.table([{ h: "Código PERFECT" }, { h: "Descrição" }, { h: "Campo" }, { h: "No CatalogoAMD", r: true }, { h: "No BI03 (vale este)", r: true }],
        d.rows.map(r => [ficha(r.product_id, r.perfect_code), desc(r), esc(r.campo), `<span class="tabular-nums">${valor(r.catalogo)}</span>`, `<b class="tabular-nums text-blue-600">${valor(r.bi03)}</b>`]), { h: "max-h-[65vh]" }); return; }
      if (tab === "protheus") { $("#at").innerHTML = TW.table([{ h: "Código" }, { h: "Tipo" }, { h: "Status" }, { h: "Fornecedor" }, { h: "Aplicação", nw: false }, { h: "Situação" }],
        d.rows.map(r => [`<b>${esc(r.code)}</b>${window.psdCode ? " " + psdCode(r.code, "↗") : ""}`, badge(r.tipo === "REDESENVOLVIMENTO" ? "R-D" : "DES", r.tipo === "REDESENVOLVIMENTO" ? "green" : "blue"), esc(r.status || "–"), esc(r.supplier || "–"),
          `<span class="block min-w-[14rem] max-w-[28rem] text-xs">${esc(r.application || "–")}</span>`, badge("Pendente cadastro Protheus", "amber")]), { h: "max-h-[65vh]" }); return; }
      $("#at").innerHTML = tab === "familia"
        ? TW.table([{ h: "Código PERFECT" }, { h: "Descrição" }, { h: "Família no catálogo" }, { h: "Família no Inmetro" }, { h: "Certificados (nº · fornecedor)", nw: false }],
            d.rows.map(r => [ficha(r.product_id, r.perfect_code), `<span class="block max-w-[18rem] truncate" title="${esc(r.description || "")}">${esc(r.description || "–")}</span>`, badge(r.family, "blue"),
              r.inmetro_families.map(f => badge(f, f === (r.family || "").toUpperCase() ? "slate" : "amber")).join(" ") + (r.mixed ? ` <span class="text-xs text-mute">(fornecedores com famílias diferentes)</span>` : ""),
              `<span class="block min-w-[16rem] text-xs text-mute">${r.certificates.map(c => `${esc(c.number || "–")} · ${esc(c.supplier || "–")} · <b class="${c.family === (r.family || "").toUpperCase() ? "text-mute" : "text-amber-700"}">${esc(c.family)}</b>`).join("<br>")}</span>`]), { h: "max-h-[65vh]" })
        : TW.table([{ h: "Código PERFECT" }, { h: "Descrição" }, { h: "EAN no catálogo" }, { h: "EAN na planilha" }, { h: "Fonte" }, { h: "" }],
            d.rows.map(r => [ficha(r.product_id, r.perfect_code), `<span class="block max-w-[18rem] truncate" title="${esc(r.description || "")}">${esc(r.description || "–")}</span>`, `<b class="tabular-nums">${esc(r.current || "–")}</b>`, `<b class="tabular-nums text-amber-700">${esc(r.imported || "–")}</b>`, esc(r.source || "–"),
              `<span class="flex gap-1"><button type="button" class="${mini}" data-ap="${r.id}">Usar o da planilha</button><button type="button" class="${mini}" data-keep="${r.id}">Manter o do catálogo</button></span>`]), { h: "max-h-[65vh]" });
    };
    $("#af").addEventListener("input", e => { if (e.target.name === "q") { F.set({ q: e.target.value }); clearTimeout(timer); timer = setTimeout(carregar, 300); } });
    $("#af").addEventListener("submit", e => e.preventDefault());
    if (tab === "protheus") $("#aq").addEventListener("click", e => { const b = e.target.closest("[data-tg]"); if (b) { F.toggle(b.dataset.tg, b.dataset.v); carregar(); } });
    $("#at").addEventListener("click", async e => { const a = e.target.closest("[data-ap]"), k = e.target.closest("[data-keep]"); if (!a && !k) return; (a || k).disabled = true;
      try { if (a) { const r = await post(`/api/pendencies/${a.dataset.ap}/apply`, {}); $("#am").dataset.ok = `✔ EAN gravado: ${r.value} (antes ${r.old}).`; }
            else { await post("/api/pendencies/" + k.dataset.keep, { status: "resolvida" }); $("#am").dataset.ok = "✔ Mantido o EAN do catálogo."; } } catch (er) { fail(er); }
      carregar(); });
    carregar();
  }
  PSD.tela("anomalias", anomalias);
})();
