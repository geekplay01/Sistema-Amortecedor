/* Update 9 · tela do perfil «Aprovador IPI» (Mariana e Gabriel Santos): os itens do envio aberto em duas colunas (10,4 leve e passeio · 2,6 utilitário
   e pesado) e os próximos cadastros recolhidos. Só leitura: a aprovação é pela resposta do e-mail. Usa só /api/ipi/aprovador. */
(function () {
  const el = document.getElementById("ap");
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const nf = (v, d = 0) => v == null ? "–" : Number(v).toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });
  const selo = v => `<span class="psd-ipi ${v === 2.6 ? "p" : "l"}">${nf(v, 1)}</span>`;
  const li = r => `<li><span><span class="cod">${esc(r.code)}</span><span class="id">ID ${esc(r.id)}</span></span><span class="v">${esc([r.make, r.vehicle].filter(Boolean).join(" "))}
    <span class="a">${esc(r.application_text || "")}</span></span><span class="a">${r.year_from || ""}${r.year_to ? "–" + r.year_to : ""}</span></li>`;
  const col = (t, v, rows) => `<div class="psd-apcol"><div class="h"><b>${t}</b>${selo(v)}</div><ul>${rows.length ? rows.map(li).join("") : '<li><span class="a">nenhum</span></li>'}</ul></div>`;
  const val = r => r.ipi != null ? r.ipi : r.sug;
  fetch("/api/ipi/aprovador").then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }).then(d => {
    const env = d.envio, leve = env.filter(r => val(r) === 10.4), pes = env.filter(r => val(r) === 2.6);
    const big = (r, v, s) => `<div><div class="r">${r}</div><div class="v">${nf(v)}</div><div class="s">${s}</div></div>`;
    el.innerHTML = `<div class="psd-big">${big("Para aprovar", env.length, env.length ? "itens do último e-mail" : "nada enviado agora")}${big("Leve e passeio", leve.length, "IPI 10,4")}${big("Utilitário e pesado", pes.length, "IPI 2,6")}</div>
      ${env.length ? `<div class="psd-apcols">${col("Leve e passeio", 10.4, leve)}${col("Utilitário e pesado", 2.6, pes)}</div>` : '<p class="psd-approx">Nenhum envio aberto. Quando chegar o e-mail «Sugestão de IPI», os itens aparecem aqui, separados por IPI.</p>'}
      <details class="psd-approx"><summary>Próximos cadastros: ${nf(d.proximos.length)} itens</summary><div class="psd-apcols" style="margin-top:10px">
        ${col("Leve e passeio", 10.4, d.proximos.filter(r => val(r) === 10.4))}${col("Utilitário e pesado", 2.6, d.proximos.filter(r => val(r) === 2.6))}</div></details>
      <p style="margin:0;font-size:12.5px;color:var(--mut)">Só leitura. A aprovação é pela resposta do e-mail.</p>`;
  }).catch(() => { el.innerHTML = "<p>Não foi possível carregar. Atualize a página; se continuar, avise o Italo.</p>"; });
})();
