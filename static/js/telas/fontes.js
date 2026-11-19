/* Tela · Fontes e histórico — visual Tailwind (etapa 16 · B).
   Histórico das últimas 200 importações com atalhos «Gravadas» (status ok) × «Só verificação» (status simulado: a planilha foi lida e comparada, nada gravado);
   cada número = linhas da lista ao clicar (queries.history · counts; test_25). Filtro na URL e lembrado; o Excel do histórico segue o filtro.
   Fontes: prioridade 1–9 (qual fonte prevalece na análise manual de conflitos) e os dados de planilhas novas guardados como vieram. */
(function () {
  const { $, esc, J, post, root, fail, dlg } = PSD;
  const TW = window.PSDTW, { nf, badge, kpi, card, empty } = TW;
  const STL = { ok: ["Gravada", "green"], simulado: ["Só verificação", "slate"] }, CH = [["todas", "Todas"], ["ok", "Gravadas"], ["simulado", "Só verificação"]];
  const primario = "rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-blue-700 no-underline";
  const mini = "rounded-lg border border-line bg-card px-2.5 py-1 text-xs font-semibold text-ink hover:bg-slate-500/10 no-underline";
  const chip = (attrs, label, on, n) => `<button type="button" ${attrs} aria-pressed="${on}" class="psd-chip">${label}<span class="n">${nf(n)}</span></button>`;      // etapa 19: mesmo visual da barra de filtros
  const quando = s => s ? `${TW.dmy(s)} ${String(s).slice(11, 16)}` : "–";
  const alerta = (n, tone) => n ? `<b class="${tone}">${nf(n)}</b>` : '<span class="text-mute">0</span>';

  async function dadosAvulsos(id, pg) {          // dados de planilhas novas guardados como estão
    try {
      const d = await J(`/api/sources/${id}/rows?page=${pg}`), pages = Math.max(1, Math.ceil(d.total / d.size)); dlg.classList.add("wide");
      dlg.innerHTML = `<div class="dh"><div><h2>${esc(d.name)}</h2><p>${nf(d.total)} linha(s) guardada(s) como vieram da planilha.</p></div><div><a class="btn ghost" href="/api/sources/${id}/export.xlsx">⬇ Excel</a> <button class="btn ghost" data-close>Fechar</button></div></div>`
        + TW.table(d.columns.map(c => ({ h: esc(c) })), d.rows.map(r => d.columns.map(c => esc(r[c] ?? ""))), { h: "max-h-[60vh]" })
        + (pages > 1 ? `<div class="mt-3 flex items-center justify-center gap-3 text-sm text-mute"><button type="button" class="${mini}" id="gv-p" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button type="button" class="${mini}" id="gv-n" ${pg >= pages ? "disabled" : ""}>›</button></div>` : "");
      dlg.addEventListener("close", () => dlg.classList.remove("wide"), { once: true });
      const a = $("#gv-p", dlg), b = $("#gv-n", dlg); if (a) a.onclick = () => dadosAvulsos(id, pg - 1); if (b) b.onclick = () => dadosAvulsos(id, pg + 1);
      if (!dlg.open) dlg.showModal();
    } catch (e) { fail(e); }
  }

  async function fontes() {
    const F = TW.filtros("fontes", ["status"]); let h;
    try { h = await J("/api/history"); } catch (e) { return fail(e); }
    const linhas = h.sources.reduce((a, s) => a + (s.generic_rows || 0), 0);
    root.innerHTML = `<div class="flex flex-col gap-5">
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">${kpi("Importações gravadas", nf(h.counts.ok || 0), "entraram no banco", "green")}${kpi("Só verificação", nf(h.counts.simulado || 0), "lidas e comparadas, nada gravado", "slate")}
        ${kpi("Fontes cadastradas", nf(h.sources.length), "planilhas, ERP e servidor")}${kpi("Dados avulsos", nf(linhas), "linhas de planilhas novas guardadas", "amber")}</div>
      <div id="fh"></div><div id="fs"></div></div>`;

    const historico = () => {
      const st = F.get().status || "todas", b = h.batches.filter(x => st === "todas" || x.status === st);
      $("#fh").innerHTML = card("Histórico de importações", `<div class="mb-3 flex flex-wrap items-center gap-2">${CH.map(([v, l]) => chip(`data-st="${v}"`, l, st === v, h.counts[v] || 0)).join("")}<span class="text-xs text-mute">últimas ${nf(h.counts.todas)} · mais recentes primeiro</span></div>`
        + (h.counts.todas ? TW.table([{ h: "#", r: true }, { h: "Quando" }, { h: "Arquivo" }, { h: "Aba" }, { h: "Tipo de dado" }, { h: "Linhas lidas", r: true }, { h: "Novos", r: true }, { h: "Atualizados", r: true }, { h: "Conflitos", r: true }, { h: "Erros", r: true }, { h: "Status" }],
            b.map(x => [x.id, quando(x.imported_at), `<span class="block max-w-[20rem] truncate" title="${esc(x.filename || "")}">${esc(x.filename || "–")}</span>`, esc(x.sheet || "–"), esc(x.category || "–"),
              nf(x.rows_read), nf(x.rows_new), nf(x.rows_updated), alerta(x.rows_conflict, "text-amber-700"), alerta(x.rows_error, "text-red-600"), badge(...(STL[x.status] || [x.status, "amber"]))]), { h: "max-h-[55vh]" })
          : empty("Nenhuma importação ainda. Use «Atualização de dados».")),
        `<a class="${primario}" href="/api/export/fontes.xlsx${st === "todas" ? "" : "?status=" + st}">${PSDTW.ico("download", "sm")} Baixar Excel</a>`);
    };
    $("#fs").innerHTML = card("Fontes e prioridade", `<p class="mb-3 mt-0 text-sm text-mute">Prioridade de 1 (maior) a 9: indica qual fonte prevalece quando você analisa um conflito em <a class="text-blue-600" href="/pendencias">Pendências</a>. O sistema nunca sobrescreve um valor sozinho. <span id="fsm" class="font-semibold" role="status"></span></p>`
      + TW.table([{ h: "Fonte" }, { h: "Tipo de dado" }, { h: "Importações", r: true }, { h: "Dados avulsos" }, { h: "Prioridade" }],
        h.sources.map(s => [`<span class="block max-w-[22rem] truncate" title="${esc(s.name)}">${esc(s.name)}</span>`, esc(s.category || "–"), nf(s.imports),
          s.generic_rows ? `<span class="flex gap-1"><button type="button" class="${mini}" data-gv="${s.id}">Ver ${nf(s.generic_rows)} linha(s)</button><a class="${mini}" href="/api/sources/${s.id}/export.xlsx">⬇ Excel</a></span>` : '<span class="text-mute">–</span>',
          `<select data-src="${s.id}" aria-label="Prioridade de ${esc(s.name)}" class="rounded-lg border border-line bg-card px-2 py-1 text-sm text-ink">${[1, 2, 3, 4, 5, 6, 7, 8, 9].map(n => `<option ${n === s.priority ? "selected" : ""}>${n}</option>`).join("")}</select>`]), { h: "max-h-[55vh]" }));
    historico();

    $("#fh").addEventListener("click", e => { const c = e.target.closest("[data-st]"); if (c) { F.set({ status: c.dataset.st === "todas" ? "" : c.dataset.st }); historico(); } });
    $("#fs").addEventListener("click", e => { const g = e.target.closest("[data-gv]"); if (g) dadosAvulsos(+g.dataset.gv, 1); });
    $("#fs").addEventListener("change", async e => { const s = e.target.closest("[data-src]"); if (!s) return; const m = $("#fsm");
      try { await post("/api/sources/" + s.dataset.src, { priority: +s.value }); m.className = "font-semibold text-emerald-600"; m.textContent = "✔ Prioridade salva."; }
      catch (er) { m.className = "font-semibold text-red-600"; m.textContent = er.message; } });
  }
  PSD.tela("fontes", fontes);
})();
