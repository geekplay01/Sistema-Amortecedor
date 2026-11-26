/* Tela · Atualização de dados — visual Tailwind (etapa 16 · B).
   Duas fases: «verificação» (lê as planilhas e compara com o banco, nada gravado: /api/update/check) e «Aplicar» (backup + grava só o que falta: /api/update/apply).
   Nada é apagado. Planilhas de nome desconhecido também entram (cadastro reconhecido pelas colunas ou dados guardados como vieram) e aparecem em Fontes e histórico. */
(function () {
  const { $, esc, J, post, root } = PSD;
  const TW = window.PSDTW, { nf, badge, kpi, notice } = TW;
  const botao = "cursor-pointer rounded-lg border border-line bg-card px-3.5 py-2 text-sm font-semibold text-ink hover:bg-slate-500/10";
  const primario = "cursor-pointer rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-blue-700";
  const cel = n => n ? nf(n) : '<span class="text-mute">–</span>';

  function atualizacao() {
    root.innerHTML = `<div class="flex flex-col gap-5">
      ${notice(`Envie as planilhas <b>com o mesmo nome de sempre</b> (ex.: <code>DadosR-D e DES.xlsx</code>, <code>Compra_de_amostra.xlsx</code>). O sistema lê todas as linhas, confere com o banco e <b>insere só o que ainda não está</b>.
        Planilhas novas (nome desconhecido) também entram: se as colunas forem de um cadastro conhecido, são carregadas como tal; senão, os dados ficam guardados como vieram. Tudo aparece em <a class="text-blue-600" href="/fontes">Fontes e histórico</a>.<br>
        <b>Nada é apagado.</b> Primeiro vem a <b>verificação</b> (o que seria alterado); só grava quando você clicar em <b>Aplicar</b>, e faz backup antes.`)}
      ${TW.zonaPlanilha({ id: "uf", titulo: "Enviar planilhas", multiplo: true })}
      <div class="flex flex-wrap items-center gap-2"><button type="button" id="uf-folder" class="${botao}">Verificar a pasta bases_exemplo</button><span id="uf-names" class="text-sm text-mute"></span></div>
      <p id="uf-msg" class="m-0 text-sm text-mute" role="status"></p><div id="uf-out" class="flex flex-col gap-5"></div></div>`;
    const msg = (t, err) => { const m = $("#uf-msg"); m.textContent = t; m.className = "m-0 text-sm " + (err ? "font-semibold text-red-600" : "text-mute"); };
    const show = (res, applied) => {
      const t = res.totals, todo = t.new + t.updated;
      $("#uf-out").innerHTML = `<div class="grid grid-cols-2 gap-4 lg:grid-cols-4">${kpi("Novos", nf(t.new), applied ? "inseridos" : "seriam inseridos", "green")}${kpi("Atualizados", nf(t.updated), applied ? "complementados" : "seriam complementados")}
          ${kpi("Já existiam", nf(t.present), "nada a fazer", "slate")}${kpi("Sem vínculo", nf(t.unmatched), "guardados como vieram", "amber")}</div>`
        + TW.table([{ h: "Planilha" }, { h: "Tipo de dado" }, { h: "Linhas lidas", r: true }, { h: "Novos", r: true }, { h: "Atualizados", r: true }, { h: "Já existiam", r: true }, { h: "Sem vínculo", r: true }, { h: "Avisos", nw: false }],
          res.results.map(r => { const c = r.counts || {};
            return [`<b>${esc(r.file)}</b>`, esc(r.label || "–"), r.status === "ok" ? nf(r.rows) : badge(r.status, r.status === "erro" ? "red" : "amber"),
              cel(c.new), cel(c.updated), cel(c.present), cel(c.unmatched), `<span class="block min-w-[16rem] text-xs text-mute">${(r.messages || []).slice(0, 3).map(esc).join("<br>")}</span>`]; }), { h: "max-h-[55vh]" })
        + (applied ? notice(`✔ Atualização aplicada. Backup criado: <code>${esc(res.backup || "—")}</code>${res.equivalences ? ", equivalências recalculadas" : ""}. <a class="text-blue-600" href="/fontes">Ver histórico</a>, <a class="text-blue-600" href="/dashboard">Ver dashboard</a>`)
          : todo ? `<div><button type="button" id="uf-apply" class="${primario}">Aplicar atualização (${nf(t.new)} novos, ${nf(t.updated)} atualizados)</button></div>`
          : notice("O banco já está em dia com estas planilhas: nada a inserir."));
      const ap = $("#uf-apply"); if (ap) ap.onclick = async () => { ap.disabled = true; msg("Aplicando… (backup + gravação)");
        try { const r = await post("/api/update/apply", { token: res.token }); msg(""); show(r, true);
          PSDTW.toast(`${nf(r.totals.new)} novo(s) e ${nf(r.totals.updated)} atualizado(s) gravados. Backup antes: ${r.backup || "—"}.`, { titulo: "Atualização aplicada" }); } catch (e) { ap.disabled = false; msg(e.message, true); PSDTW.erro(e); } };
    };
    const check = async (fd, arquivos = []) => { msg("Lendo as planilhas e comparando com o banco… pode levar alguns segundos (o cadastro do Protheus e a Fraga levam mais)."); $("#uf-out").innerHTML = TW.carregando("Lendo as planilhas…");
      try { const r = await PSDTW.enviar("/api/update/check", fd, arquivos); msg(""); show(r, false); } catch (e) { $("#uf-out").innerHTML = ""; msg(e.message, true); PSDTW.erro(e); } };
    TW.ligarPlanilha("#uf", { multiplo: true, receber: fs => { $("#uf-names").textContent = fs.length + " arquivo(s): " + fs.map(f => f.name).join(", "); const fd = new FormData(); fs.forEach(f => fd.append("files", f)); check(fd, fs); } });
    $("#uf-folder").onclick = () => { $("#uf-names").textContent = ""; const fd = new FormData(); fd.append("folder", "1"); check(fd); };
  }
  PSD.tela("atualizacao", atualizacao);
})();
