/* Tela · Catálogo: Aplicações, Comparação e Equivalências. (Produtos e Pesquisa: telas/produtos.js.)
   Usa o núcleo window.PSD (core.js); registra a tela com PSD.tela(slug, desenhar). Separado do antigo pages.js na etapa 16. */
(function () {
  const { $, $$, esc, J, post, qs, SYS, yr, T, lnk, empty, root, page, url, fail, listView, inp, sel, prodRow, prodHead, initLists, tag, clip, AX, SD } = PSD;
  PSD.tela("aplicacoes", () => listView({ endpoint: "/api/applications", xlsx: "aplicacoes", init: initLists, head: ["Montadora", "Modelo", "Aplicação", "Anos", "Eixo", "Lado", "Produto", "Pos."],
      row: a => `<tr><td>${esc(a.make || "")}</td><td>${esc(a.model || "")}</td><td>${esc(a.application_text || "")}</td><td>${yr(a)}</td><td>${esc(a.axle || "")}</td><td>${esc(a.side || "")}</td><td>${lnk(a.product_id, a.perfect_code)}</td><td>${a.catalog_position ?? "–"}</td></tr>`,
      form: inp("q", "Buscar veículo, aplicação ou código", 'style="flex:1;min-width:220px"') + sel("make", "Montadora", []) + sel("model", "Modelo", []) + sel("year", "Ano", []) + sel("axle", "Eixo", AX) + sel("side", "Lado", SD) }));
  PSD.tela("comparacao", async () => {
      let ids = (url.get("ids") || "").match(/\d+/g) || [];
      root.innerHTML = `<div class="toolbar"><input id="add" list="addl" placeholder="Adicionar produto: digite o código e escolha" style="flex:1;min-width:260px"><datalist id="addl"></datalist><a class="btn" id="dl" href="#">⬇ Baixar Excel</a></div><div id="out"></div>`;
      const add = $("#add"), dl = $("#addl"); let found = {};
      add.addEventListener("input", async () => { if (add.value.length < 2) return; const d = await J("/api/products?size=8&q=" + encodeURIComponent(add.value)); found = {}; d.rows.forEach(r => found[r.perfect_code] = r.id); dl.innerHTML = d.rows.map(r => `<option value="${esc(r.perfect_code)}">${esc(r.description || "")}</option>`).join(""); if (found[add.value.trim()]) { ids = [...new Set([...ids, String(found[add.value.trim()])])].slice(0, 4); add.value = ""; draw(); } });
      root.addEventListener("click", e => { const r = e.target.closest("[data-rm]"); if (r) { ids = ids.filter(i => i !== r.dataset.rm); draw(); } });
      const ROWS = [["Posição no catálogo", p => p.catalog_position], ["Descrição", p => p.description], ["Grupo", p => p.catalog_group], ["Família", p => p.family], ["Sistema", p => SYS[p.system_type]],
        ["Lmin (mm)", p => p.dimensions?.lmin_mm], ["Lmax (mm)", p => p.dimensions?.lmax_mm], ["Curso (mm)", p => p.dimensions?.stroke_mm], ["Ø haste (mm)", p => p.dimensions?.rod_diameter_mm], ["Corpo (mm)", p => p.dimensions?.body_length_mm], ["Ø tubo (mm)", p => p.dimensions?.tube_diameter_mm],
        ["Fixação superior", p => p.dimensions?.upper_mount], ["Fixação inferior", p => p.dimensions?.lower_mount], ["Peso (kg)", p => p.weight_kg], ["EAN", p => p.ean], ["Caixa", p => [p.package_code, p.box?.raw_dims].filter(Boolean).join(" · ")],
        ["Códigos OEM", p => p.codes.filter(c => c.code_type === "oem").map(c => c.code).join(", ")], ["Códigos de fornecedor", p => [...new Set(p.codes.filter(c => c.code_type === "fornecedor").map(c => c.code))].join(", ")],
        ["Aplicações", p => p.applications.length ? p.applications.length + ": " + p.applications.slice(0, 4).map(a => [a.make, a.model, yr(a)].filter(Boolean).join(" ")).join("; ") : ""],
        ["Nº Inmetro", p => [...new Set(p.certificates.map(c => c.inmetro_number).filter(Boolean))].join(", ")],
        ["Fontes", p => [...new Set([...p.codes, ...p.applications].map(x => x.source).filter(Boolean))].join("; ")]];
      async function draw() {
        history.replaceState(null, "", "?ids=" + ids.join(",")); $("#dl").href = "/api/export/comparacao.xlsx?ids=" + ids.join(",");
        if (!ids.length) return $("#out").innerHTML = empty("Escolha de 2 a 4 produtos para comparar lado a lado.");
        const ps = await J("/api/compare?ids=" + ids.join(","));
        const diffs = [], trs = ROWS.map(([l, fn]) => { const v = ps.map(p => String(fn(p) ?? "")); const dif = ps.length > 1 && new Set(v).size > 1; if (dif) diffs.push(l); return `<tr class="${dif ? "diff" : ""}"><th>${l}</th>${v.map(x => `<td>${esc(x) || "—"}</td>`).join("")}</tr>`; });
        $("#out").innerHTML = (ps.length > 1 ? `<div class="notice">${diffs.length ? "<b>Diferenças identificadas:</b> " + diffs.join(", ") : "Nenhuma diferença nos campos comparados."} Linhas destacadas diferem; “—” = sem dado. Dimensões parecidas não bastam para afirmar intercambialidade.</div>` : "") +
          `<div class="tbl"><table><tr><th></th>${ps.map(p => `<th>${lnk(p.id, p.perfect_code)} <button class="btn ghost" data-rm="${p.id}">×</button></th>`).join("")}</tr>${trs.join("")}</table></div>`;
      }
      draw();
    });
  PSD.tela("equivalencias", () => {
      const DF = ["Nenhuma aplicação em comum", "Eixo diferente", "Lados diferentes", "São lados opostos", "Lmax difere", "Lmin difere", "Sistema diferente", "Família diferente"];
      const MS = ["Eixo", "Lado", "Lmax", "Lmin", "Sistema óleo/gás", "Aplicações", "Diâmetro da haste"];
      const grp = (n, t, h, L) => `<div class="ms" data-ms><button type="button" class="btn ghost msb">${t} <b class="msn"></b> ▾</button><div class="msp" hidden><small class="muted">${h}</small>${L.map(c => `<label><input type="checkbox" name="${n}" value="${c}"> ${c} <small data-fc="${n}:${c}"></small></label>`).join("")}</div></div>`;
      const CR = ["Código em comum", "Aplicação em comum", "Mesmo eixo", "Mesmo lado", "Lmax igual", "Lmin igual", "Mesmo sistema", "Mesma família"];
      root.innerHTML = `<div class="notice">A pontuação (0–100%) mede a <b>similaridade dos dados</b> (códigos, aplicação, medidas, sistema). <b>Não comprova intercambialidade</b> e nenhuma sugestão é aprovada automaticamente.</div>
      <form class="eqform"><div class="toolbar">${inp("q", "Código PERFECT")}${sel("status", "Todos os status", [["pendente", "Pendente"], ["aprovada", "Aprovada"], ["rejeitada", "Rejeitada"]])}${sel("confidence", "Confiança", [["Alta", "Alta"], ["Média", "Média"], ["Baixa", "Baixa"]])}${sel("diff", "Diferenças", [["sem", "Sem diferenças"], ["com", "Com diferenças"]])}
        <input name="minscore" type="number" min="0" max="100" placeholder="Pontuação mín. (%)" style="width:150px"><button type="button" class="btn ghost" id="clr">Limpar filtros</button></div>
        <div class="toolbar">${grp("crit", "Critérios atendidos", "todos os marcados precisam ser atendidos", CR)}${grp("dif", "Diferenças", "exigir que apareça", DF)}${grp("miss", "Dados ausentes", "exigir que apareça", MS)}</div></form>
      <div class="toolbar"><span class="summary" id="sum"></span><span style="flex:1"></span><button type="button" class="btn ghost" id="gen">Gerar / atualizar sugestões</button><a class="btn" id="dl" href="#">⬇ Baixar planilha (XLSX)</a></div><div id="out"></div><div class="pager" id="pg"></div>`;
      const f = $("form", root); let pg = 1, t;
      url.forEach((v, k) => { const i = f.elements[k]; if (i && i.type !== "checkbox") i.value = v; });
      const updMs = () => $$("[data-ms]", root).forEach(m => { const n = $$("input:checked", m).length; $(".msn", m).textContent = n ? "(" + n + ")" : ""; });
      root.addEventListener("click", e => { const b = e.target.closest(".msb"); $$(".msp", root).forEach(p => { if (!b || p !== b.nextElementSibling) p.hidden = true; }); if (b) b.nextElementSibling.hidden = !b.nextElementSibling.hidden; });
      document.addEventListener("click", e => { if (!e.target.closest("[data-ms]")) $$(".msp", root).forEach(p => p.hidden = true); });
      f.addEventListener("change", updMs);
      const params = () => new URLSearchParams([...new FormData(f)].filter(([, v]) => v !== "")).toString();
      const chips = (a, c) => a.map(x => `<span class="chip ${c}">${esc(x)}</span>`).join("");
      const load = async () => { try {
        $("#dl").href = "/api/equivalences/export.xlsx?" + params();
        const d = await J("/api/equivalences?" + params() + "&page=" + pg);
        const sc = d.status_counts || {}; $("#sum").textContent = `${d.total} sugestão(ões) · Pendente ${sc.pendente || 0} · Aprovada ${sc.aprovada || 0} · Rejeitada ${sc.rejeitada || 0}`;
        $$("[data-fc]").forEach(s => s.textContent = "(" + (d.facets?.[s.dataset.fc] ?? 0) + ")");
        $("#out").innerHTML = d.rows.length ? d.rows.map(e => `<div class="eq"><div class="eqh"><b>${lnk(e.product_a, e.a_code)} × ${lnk(e.product_b, e.b_code)}</b><span class="badge ${e.confidence === "Alta" ? "ok" : e.confidence === "Média" ? "warn" : "bad"}">${e.confidence}</span><span class="status ${e.status}">${e.status}</span><a href="/comparacao?ids=${e.product_a},${e.product_b}">Comparar</a></div>
          <div class="bar"><i style="width:${e.score}%"></i><span>${e.score}% de similaridade</span></div><p class="muted">${esc(e.a_desc || "")} · ${esc(e.b_desc || "")}</p>
          <div>${chips(e.criteria, "ok")}${chips(e.differences, "bad")}${chips(e.missing, "warn")}</div><p class="muted">Fontes: ${esc(e.sources || "")}</p>
          <div class="acts">${["pendente", "aprovada", "rejeitada"].map(s => `<button class="btn ghost ${e.status === s ? "on" : ""}" data-eq="${e.id}" data-s="${s}">${{ pendente: "Pendente", aprovada: "Aprovar", rejeitada: "Rejeitar" }[s]}</button>`).join("")}</div></div>`).join("") : empty("Nenhuma sugestão com esses filtros. Ajuste os filtros ou clique em “Gerar / atualizar sugestões”.");
        const pages = Math.ceil(d.total / d.size); $("#pg").innerHTML = pages > 1 ? `<button class="btn ghost" data-p="${pg - 1}" ${pg < 2 ? "disabled" : ""}>‹</button> Página ${pg} de ${pages} <button class="btn ghost" data-p="${pg + 1}" ${pg >= pages ? "disabled" : ""}>›</button>` : "";
      } catch (e) { fail(e); } };
      f.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => { pg = 1; load(); }, 250); });
      $("#clr").onclick = () => { f.reset(); updMs(); pg = 1; load(); };
      $("#gen").onclick = async () => { $("#gen").textContent = "Calculando…"; try { const r = await post("/api/equivalences/generate"); alert(`${r.candidates} pares analisados; ${r.saved} sugestões (≥50%). Os status já definidos foram preservados.`); } catch (e) { fail(e); } $("#gen").textContent = "Gerar / atualizar sugestões"; pg = 1; load(); };
      root.addEventListener("click", async e => { const b = e.target.closest("[data-eq]"), p = e.target.closest("[data-p]"); if (b) { await post("/api/equivalences/" + b.dataset.eq, { status: b.dataset.s }); load(); } else if (p && !p.disabled) { pg = +p.dataset.p; load(); scrollTo(0, 0); } });
      load();
    });
})();
