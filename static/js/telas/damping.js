/* Tela · Damping force — visual Tailwind (etapa 16): regra (da planilha DAMPING FORCE - REGRA), formulário do ensaio com cálculo ao vivo e ensaios salvos.
   Cada resultado (aprovado/reprovado/incompleto) é um atalho que filtra a lista e bate com o número (tests: test_22). Filtros na URL e lembrados
   (PSDTW.filtros); o Excel segue os mesmos filtros. O cálculo daqui repete damping.calc/overall (o servidor recalcula ao salvar e no Excel). */
(function () {
  const { $, $$, esc, J, post, qs, root, fail } = PSD;
  const TW = window.PSDTW, { nf, badge, kpi, notice, dmy } = TW;
  const campo = "rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500";
  const botao = "rounded-lg border border-line bg-card px-3.5 py-2 text-sm font-semibold text-ink hover:bg-slate-500/10";
  const primario = "rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white hover:bg-blue-700";
  const chip = (attrs, label, on, n) => `<button type="button" ${attrs} aria-pressed="${on}" class="rounded-full border px-3 py-1.5 text-xs font-semibold ${on ? "border-blue-500 bg-blue-500 text-white" : "border-line bg-card text-ink hover:bg-slate-500/10"}">${label}${n != null ? ` · ${nf(n)}` : ""}</button>`;
  const RES = { APPROVED: ["Aprovado", "green"], DISAPPROVED: ["Reprovado", "red"], INCOMPLETO: ["Incompleto", "amber"], "FAIXA INVÁLIDA": ["Faixa inválida", "amber"] };
  const selo = r => r ? `<span title="${esc(r)}">${badge(RES[r]?.[0] || r, RES[r]?.[1])}</span>` : "";
  const fx = v => v == null ? "–" : v.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
  const numero = v => { v = String(v ?? "").trim().replace(",", "."); return v === "" || isNaN(v) ? null : +v; };

  async function damping() {
    let R; try { R = await J("/api/damping/rules"); } catch (e) { return fail(e); }
    const names = Object.keys(R.tables || {}), pontos = names.reduce((s, n) => s + R.tables[n].length, 0);
    const regra = names.length
      ? `<p class="mb-0 mt-2 text-sm text-mute">Se DRAWING &lt; <b class="text-ink">${nf(R.threshold)} N</b>: mín = D×(1−tol)+${nf(R.offset)} e máx = D×(1+tol)−${nf(R.offset)}; senão, sem o ajuste. <b class="text-ink">Aprovado</b> se mín ≤ FOUND ≤ máx.</p>
         <p class="mb-0 mt-2 text-xs text-mute">${esc(R.note)}</p>`
      : `<p class="mb-0 mt-2 text-sm text-mute">Nenhuma regra carregada. Envie a planilha <b>DAMPING FORCE - REGRA.xlsx</b> para começar a registrar ensaios.</p>`;
    root.innerHTML = `<div class="flex flex-col gap-5">
      <section class="grid gap-4 rounded-2xl border border-line bg-card p-5 shadow-sm lg:grid-cols-5">
        <div class="lg:col-span-3"><h3 class="m-0 text-base font-semibold text-ink">Regra de damping force</h3>${regra}</div>
        <div class="flex flex-col items-start justify-center gap-2 lg:col-span-2">
          ${names.length ? `<span class="text-sm text-mute">Fonte: <b class="text-ink">${esc(R.source || "—")}</b> · ${nf(pontos)} ponto(s) em ${names.map(n => "<b class=\"text-ink\">" + esc(n) + "</b>").join(", ")}</span>` : ""}
          <label class="${names.length ? botao : primario} cursor-pointer">${names.length ? "Atualizar regra (planilha)" : "Carregar a planilha da regra"}<input type="file" id="dm-rf" accept=".xlsx" hidden></label>
          <span id="dm-rmsg" class="hidden text-sm" role="status"></span>
        </div>
      </section>
      ${names.length ? `<div id="dm-k" class="grid grid-cols-2 gap-4 lg:grid-cols-4"></div>
      <section id="dm-ed" class="rounded-2xl border border-line bg-card p-5 shadow-sm">
        <div class="mb-4 flex flex-wrap items-center justify-between gap-3"><h3 class="m-0 text-base font-semibold text-ink">Ensaio <span id="dm-id" class="text-mute"></span></h3><span id="dm-ov"></span></div>
        <form id="dm-f" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" autocomplete="off">
          <label class="flex flex-col gap-1 text-xs font-semibold text-mute">Código PERFECT<input name="perfect_code" list="dm-dl" class="${campo}" placeholder="Digite 3 letras para buscar"></label><datalist id="dm-dl"></datalist>
          <label class="flex flex-col gap-1 text-xs font-semibold text-mute">Identificação / lote<input name="label" class="${campo}"></label>
          <label class="flex flex-col gap-1 text-xs font-semibold text-mute">Data<input type="date" name="test_date" class="${campo}"></label>
          <label class="flex flex-col gap-1 text-xs font-semibold text-mute">Observações<input name="notes" class="${campo}"></label>
        </form>
        <div class="mt-4 grid gap-4 xl:grid-cols-2">${names.map(tabela).join("")}</div>
        <div class="mt-4 flex flex-wrap items-center gap-2"><button type="button" id="dm-sv" class="${primario}">Salvar ensaio</button><button type="button" id="dm-nw" class="${botao}">Novo ensaio</button>
          <a id="dm-x" class="${botao} hidden" href="#">⬇ Baixar este ensaio (Excel)</a><span id="dm-msg" class="hidden text-sm" role="status"></span></div>
      </section>
      <section class="rounded-2xl border border-line bg-card p-5 shadow-sm">
        <div class="mb-4 flex flex-wrap items-center justify-between gap-3"><h3 class="m-0 text-base font-semibold text-ink">Ensaios salvos</h3><a id="dm-xl" class="${primario}" href="/api/export/damping.xlsx">⬇ Baixar Excel</a></div>
        <div class="flex flex-col gap-3"><div id="dm-q" class="flex flex-wrap items-center gap-2"></div>
          <div class="flex flex-wrap items-center gap-2"><input id="dm-busca" type="search" placeholder="Buscar código ou identificação…" class="${campo} min-w-[16rem] flex-1"><button type="button" id="dm-clr" class="${botao}">Limpar filtros</button></div>
          <div id="dm-meta" class="text-sm text-mute"></div><div id="dm-l"></div></div>
      </section>` : ""}
    </div>`;

    const aviso = (id, t, err) => { const m = $("#" + id); m.innerHTML = t; m.classList.toggle("hidden", !t); m.classList.toggle("text-red-600", !!err); m.classList.toggle("text-emerald-600", !err); };
    $("#dm-rf").onchange = async e => { const f = e.target.files[0]; if (!f) return; const fd = new FormData(); fd.append("file", f); aviso("dm-rmsg", "Lendo a planilha…");
      try { const d = await J("/api/damping/rules", { method: "POST", body: fd }); aviso("dm-rmsg", `Regra atualizada: ${nf(d.points)} pontos.`); setTimeout(damping, 900); } catch (er) { aviso("dm-rmsg", esc(er.message), true); } };
    if (!names.length) return;

    // ---------- formulário do ensaio (cálculo ao vivo) ----------
    const F = $("#dm-f"), linhas = () => $$("tr[data-t]", root); let cur = null, sujo = false;
    const calc = (d, tol, f) => { if (d == null) return [null, null, ""]; let lo = d * (1 - tol), hi = d * (1 + tol); if (d < R.threshold) { lo += R.offset; hi -= R.offset; }
      if (lo > hi) return [lo, hi, "FAIXA INVÁLIDA"]; if (f == null) return [lo, hi, "INCOMPLETO"]; return [lo, hi, lo <= f && f <= hi ? "APPROVED" : "DISAPPROVED"]; };
    const recalc = () => { const res = []; linhas().forEach(tr => { const d = numero($(".dd", tr).value), f = numero($(".df", tr).value), [lo, hi, r] = calc(d, +tr.dataset.tol, f);
        $(".mn", tr).textContent = fx(lo); $(".mx", tr).textContent = fx(hi); $(".rs", tr).innerHTML = selo(r); if (d != null) res.push(r); });
      const o = !res.length ? "" : res.includes("DISAPPROVED") ? "DISAPPROVED" : res.some(r => r !== "APPROVED") || res.length < linhas().length ? "INCOMPLETO" : "APPROVED";
      $("#dm-ov").innerHTML = o ? `<span class="text-sm text-mute">Resultado geral</span> ${selo(o)}` : ""; };
    const marcar = id => { cur = id || null; sujo = false; $("#dm-id").textContent = cur ? "#" + cur : "(novo)"; $("#dm-x").classList.toggle("hidden", !cur); if (cur) $("#dm-x").href = `/api/damping/tests/${cur}/export.xlsx`; };
    const preencher = t => { F.perfect_code.value = t.perfect_code || ""; F.label.value = t.label || ""; F.test_date.value = t.test_date || new Date().toISOString().slice(0, 10); F.notes.value = t.notes || "";
      linhas().forEach(tr => { const p = (t.points || []).find(x => x.table_name === tr.dataset.t && Math.abs(x.velocity - tr.dataset.v) < 1e-6); $(".dd", tr).value = p?.drawing ?? ""; $(".df", tr).value = p?.found ?? ""; });
      marcar(t.id); aviso("dm-msg", ""); recalc(); };
    const descartar = () => !sujo || confirm("Descartar as alterações do ensaio em edição?");
    $("#dm-ed").addEventListener("input", e => { sujo = true; if (e.target.closest("tr[data-t]")) recalc(); });
    $("#dm-nw").onclick = () => { if (descartar()) preencher({}); };
    $("#dm-sv").onclick = async () => { const points = linhas().map(tr => ({ table: tr.dataset.t, velocity: +tr.dataset.v, drawing: $(".dd", tr).value, found: $(".df", tr).value }));
      try { const r = await post("/api/damping/tests", { id: cur, ...Object.fromEntries(new FormData(F)), points }); marcar(r.id); aviso("dm-msg", `✔ Ensaio #${r.id} salvo.`); lista(); } catch (er) { aviso("dm-msg", esc(er.message), true); } };
    const pc = F.perfect_code; let tb;
    pc.addEventListener("input", () => { clearTimeout(tb); tb = setTimeout(async () => { const v = pc.value.trim(); if (v.length < 3) return;
      try { const d = await J("/api/products?size=8&q=" + encodeURIComponent(v)); $("#dm-dl").innerHTML = d.rows.map(r => `<option value="${esc(r.perfect_code)}">${esc(r.description || "")}</option>`).join("");
        if (!d.rows.some(r => r.perfect_code === v) || linhas().some(tr => $(".dd", tr).value)) return;
        const pts = await J("/api/damping/prefill?code=" + encodeURIComponent(v)); if (!pts.length) return;           // DRAWING do último ensaio deste código
        linhas().forEach(tr => { const p = pts.find(x => x.table_name === tr.dataset.t && Math.abs(x.velocity - tr.dataset.v) < 1e-6); if (p?.drawing != null) $(".dd", tr).value = p.drawing; });
        recalc(); aviso("dm-msg", `DRAWING preenchido com o último ensaio de ${esc(v)}.`); } catch (e) { } }, 250); });

    // ---------- ensaios salvos (atalhos por resultado + busca) ----------
    const FL = TW.filtros("damping", ["q", "res"]); let tq, cnt = null;
    const topo = () => { const c = cnt || {}, r = FL.get().res || "";
      $("#dm-k").innerHTML = kpi("Ensaios salvos", nf(c.all), FL.get().q ? "com a busca atual" : "todos os registrados", "blue") + kpi("Aprovados", nf(c.APPROVED), "todos os pontos na faixa", "green")
        + kpi("Reprovados", nf(c.DISAPPROVED), "ao menos um ponto fora da faixa", c.DISAPPROVED ? "red" : "slate") + kpi("Incompletos", nf(c.INCOMPLETO), "falta FOUND ou DRAWING em algum ponto", c.INCOMPLETO ? "amber" : "slate");
      $("#dm-q").innerHTML = `<span class="mr-1 text-xs font-semibold uppercase tracking-wide text-mute">Atalhos</span>` + [["Aprovados", "APPROVED"], ["Reprovados", "DISAPPROVED"], ["Incompletos", "INCOMPLETO"]].map(([l, v]) => chip(`data-r="${v}"`, l, r === v, c[v])).join(""); };
    const codigo = t => t.product_id ? `<a href="#" class="font-semibold text-blue-600" data-ficha="${t.product_id}">${esc(t.perfect_code)}</a>` : esc(t.perfect_code || "–");
    const acoes = t => `<span class="inline-flex gap-1"><button type="button" class="${botao} py-1" data-op="${t.id}">Abrir</button><a class="${botao} py-1" href="/api/damping/tests/${t.id}/export.xlsx">Excel</a><button type="button" class="${botao} py-1" data-rm="${t.id}">Excluir</button></span>`;
    const lista = async () => { try {
      const f = FL.get(), d = await J("/api/damping/tests?" + qs(f)); cnt = d.counts; topo();
      $("#dm-xl").href = "/api/export/damping.xlsx?" + new URLSearchParams(f);
      $("#dm-meta").innerHTML = `<b class="text-ink">${nf(d.total)}</b> ensaio(s)${Object.keys(f).length ? ` · ${Object.keys(f).length} filtro(s) ativo(s)` : ""}${FL.restaurado ? ' · <span class="text-amber-700">filtros da última visita</span>' : ""}`;
      $("#dm-l").innerHTML = d.rows.length || Object.keys(f).length
        ? TW.table([{ h: "#", r: true }, { h: "Código" }, { h: "Identificação", nw: false }, { h: "Data" }, { h: "Pontos medidos", r: true }, { h: "Resultado" }, { h: "" }],
            d.rows.map(t => [t.id, codigo(t), esc(t.label || ""), dmy(t.test_date), `${nf(t.points_filled)} / ${nf(t.points_total)}`, selo(t.overall), acoes(t)]), { h: "max-h-[55vh]" })
        : TW.empty("Nenhum ensaio salvo ainda. Preencha o formulário acima e clique em <b>Salvar ensaio</b>.");
    } catch (e) { $("#dm-l").innerHTML = notice(esc(e.message), "red"); } };
    $("#dm-busca").value = FL.get().q || "";
    $("#dm-busca").oninput = e => { clearTimeout(tq); tq = setTimeout(() => { FL.set({ q: e.target.value.trim() }); lista(); }, 300); };
    $("#dm-clr").onclick = () => { FL.clear(); $("#dm-busca").value = ""; lista(); };
    $("#dm-q").onclick = e => { const b = e.target.closest("[data-r]"); if (b) { FL.toggle("res", b.dataset.r); lista(); } };
    $("#dm-l").onclick = async e => { const o = e.target.closest("[data-op]"), d = e.target.closest("[data-rm]");
      if (o && descartar()) { try { preencher(await J("/api/damping/tests/" + o.dataset.op)); $("#dm-ed").scrollIntoView({ behavior: "smooth", block: "start" }); } catch (er) { fail(er); } }
      if (d && confirm(`Excluir o ensaio #${d.dataset.rm}?`)) { try { await J("/api/damping/tests/" + d.dataset.rm, { method: "DELETE" }); if (String(cur) === d.dataset.rm) preencher({}); lista(); } catch (er) { fail(er); } } };
    preencher({}); lista();

    function tabela(n) {
      const th = (h, r) => `<th class="whitespace-nowrap px-2 py-2.5 text-xs font-semibold uppercase tracking-wide text-mute ${r ? "text-right" : "text-left"}">${h}</th>`;
      const ent = cls => `<input class="${cls} w-20 rounded-lg border border-line bg-card px-2 py-1 text-right text-sm text-ink outline-none focus:border-blue-500" inputmode="decimal">`;
      return `<div><h4 class="mb-2 mt-0 text-sm font-semibold text-ink">Tabela ${esc(n)} <span class="font-normal text-mute">· forças em N</span></h4><div class="overflow-x-auto rounded-xl border border-line"><table class="w-full border-collapse text-sm">
        <thead><tr class="border-b border-line">${th("Tol.", 1)}${th("VM/S", 1)}${th("Drawing", 1)}${th("Mín", 1)}${th("Máx", 1)}${th("Found", 1)}${th("Resultado")}</tr></thead>
        <tbody class="divide-y divide-line">${R.tables[n].map(r => `<tr data-t="${esc(n)}" data-v="${r.velocity}" data-tol="${r.tolerance}" class="hover:bg-slate-500/10">
          <td class="px-2 py-2 text-right tabular-nums text-mute">${Math.round(r.tolerance * 100)}%</td><td class="px-2 py-2 text-right tabular-nums text-ink">${r.velocity.toLocaleString("pt-BR", { maximumFractionDigits: 4 })}</td>
          <td class="px-2 py-2 text-right">${ent("dd")}</td><td class="mn px-2 py-2 text-right tabular-nums text-mute">–</td><td class="mx px-2 py-2 text-right tabular-nums text-mute">–</td>
          <td class="px-2 py-2 text-right">${ent("df")}</td><td class="rs whitespace-nowrap px-2 py-2"></td></tr>`).join("")}</tbody></table></div></div>`;
    }
  }
  PSD.tela("damping", damping);
})();
