// Importação: upload, escolha de aba/categoria, prévia e mapeamento editável (sem gravar no banco).
(function () {
  const $ = s => document.querySelector(s);
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  let fid = null;
  const msg = (t, err) => { const m = $("#imp-msg"); m.textContent = t || ""; m.classList.toggle("err", !!err); };

  $("#imp-file").addEventListener("change", async e => {
    const file = e.target.files[0]; if (!file) return;
    msg("Lendo arquivo…"); $("#imp-map").hidden = true;
    const fd = new FormData(); fd.append("file", file);
    const r = await fetch("/api/import/upload", { method: "POST", body: fd }), d = await r.json();
    if (!r.ok) return msg(d.error, true);
    fid = window.__fid = d.file_id; msg(`${d.name}: ${d.sheets.length} planilha(s).`);
    $("#imp-cat").innerHTML = d.categories.map(c => `<option>${esc(c)}</option>`).join(""); $("#imp-cat").disabled = false;
    $("#imp-sheet").innerHTML = d.sheets.map(s => `<option>${esc(s)}</option>`).join(""); $("#imp-sheet").disabled = false;
    loadPreview();
  });
  $("#imp-sheet").addEventListener("change", loadPreview);

  async function loadPreview() {
    msg("Gerando prévia…");
    const sh = $("#imp-sheet").value, q = new URLSearchParams({ file_id: fid }); if (sh && sh !== "(csv)") q.set("sheet", sh);
    const r = await fetch("/api/import/preview?" + q), d = await r.json();
    if (!r.ok) return msg(d.error, true);
    if (!d.rows_total) { $("#imp-map").hidden = true; return msg("Esta planilha está vazia.", true); }
    const cols = Object.keys(d.mapping), mapped = cols.filter(c => d.mapping[c]).length;
    msg(`${d.rows_total} linhas · cabeçalho na linha ${d.header_row + 1} · ${mapped} de ${cols.length} colunas mapeadas automaticamente.`);
    const opts = sel => `<option value="">(ignorar)</option>` + d.fields.map(f => `<option ${f === sel ? "selected" : ""}>${f}</option>`).join("");
    $("#imp-map-tbl").innerHTML = "<tr><th>Coluna da planilha</th><th>Campo</th><th>Exemplo</th></tr>" + cols.map(c =>
      `<tr class="${d.mapping[c] ? "" : "unmapped"}"><td>${esc(c)}</td><td><select data-col="${esc(c)}">${opts(d.mapping[c])}</select></td><td>${esc((d.sample[0] || {})[c])}</td></tr>`).join("");
    $("#imp-sample").innerHTML = "<tr>" + cols.map(c => `<th>${esc(c)}</th>`).join("") + "</tr>" +
      d.sample.map(row => "<tr>" + cols.map(c => `<td>${esc(row[c])}</td>`).join("") + "</tr>").join("");
    $("#imp-map").hidden = false;
  }
})();

// Simulação e confirmação da importação
(function () {
  const $ = s => document.querySelector(s);
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const L = { new: "novos", updated: "produtos complementados/atualizados", replaced: "linhas anteriores desta fonte substituídas", conflicts: "conflitos (valor atual preservado)", duplicates: "duplicidades ignoradas", unmatched: "sem produto no catálogo (guardadas sem vínculo, ligam sozinhas quando o produto entrar)", errors: "erros", pendencies: "pendências geradas", relinked: "ligadas a produtos agora" };
  async function send(confirm) {
    const mapping = {}; document.querySelectorAll("#imp-map-tbl select").forEach(s => { if (s.value) mapping[s.dataset.col] = s.value; });
    const box = $("#imp-result"); box.hidden = false; box.textContent = confirm ? "Importando…" : "Simulando…";
    const sheet = $("#imp-sheet").value;
    const r = await fetch("/api/import/run", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_id: window.__fid, sheet, category: $("#imp-cat").value, mapping, confirm, policy: $("#imp-policy").value }) });
    const d = await r.json();
    if (!r.ok) { box.innerHTML = `<b>Não foi possível ${confirm ? "importar" : "validar"}.</b> ${esc(d.error)}`; return; }
    const items = Object.entries(d.counts).filter(([, v]) => v).map(([k, v]) => `<li><b>${v}</b> ${L[k]}</li>`).join("");
    box.innerHTML = `<b>${confirm ? "Importação concluída" : "Simulação"} — ${esc(d.label)}</b> (${d.rows} linhas lidas — nenhuma descartada)<ul>${items || "<li>Nenhuma alteração.</li>"}</ul>` +
      (d.messages.length ? `<details><summary>Avisos e erros (${d.messages.length})</summary><ul>${d.messages.map(m => `<li>${esc(m)}</li>`).join("")}</ul></details>` : "") +
      (confirm ? `<p>Lote ${d.batch_id} registrado.${d.backup ? " Backup anterior: <code>" + esc(d.backup) + "</code>." : ""} <a href="/dashboard">Ver dashboard</a></p>`
               : `<p>Nada foi gravado. <button class="btn" id="imp-confirm">Confirmar importação</button></p>`);
    const b = $("#imp-confirm"); if (b) b.onclick = () => send(true);
  }
  $("#imp-run").addEventListener("click", () => send(false));
})();
