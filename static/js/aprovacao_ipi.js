/* Update 9 · tela do perfil «Aprovador IPI» (Mariana e Gabriel Santos), repaginada com /frontend-design: a frase do momento, o caminho em 3 passos e as
   duas alíquotas como as duas colunas da tela (10,4% leve e passeio · 2,6% utilitário e pesado), com os mesmos dados do Monitoramento de IPI.
   Só leitura: a aprovação é pela resposta do e-mail. Usa só /api/ipi/aprovador. */
(function () {
  const el = document.getElementById("ap");
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const nf = (v, d = 0) => v == null ? "–" : Number(v).toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });
  const dmy = s => s ? String(s).slice(0, 10).split("-").reverse().join("/") : "";
  const cap = s => s ? s.charAt(0) + s.slice(1).toLowerCase() : "";
  const val = r => r.ipi != null ? r.ipi : r.sug;
  const SIT = { prec: ["Ainda não enviado", ""], enviado: ["Aguardando sua aprovação", "esp"], ressalva: ["Com ressalva", "res"], aprovado: ["Aprovado", "ok"] };
  const ORD = { enviado: 0, ressalva: 1, prec: 2, aprovado: 3 };
  let d = null, busca = "", sitf = "";

  const pista = (v, cor, t, dsc, rows, comSit) => `<section class="ap-pista" style="--cor:${cor}" aria-label="IPI ${nf(v, 1)}%"><div class="cab"><span class="tx">${nf(v, 1)}<small>%</small></span>
      <div class="d"><b>${t}</b><span>${dsc}</span></div><div class="tot"><b>${nf(rows.length)}</b><span>itens</span></div></div>
    <ul>${rows.length ? rows.map(r => `<li><span><span class="cod">${esc(r.code)}</span><span class="id">ID ${esc(r.id)}</span></span>
      <span class="vei"><b>${esc([r.make, r.vehicle].filter(Boolean).join(" "))}</b><span>${esc([r.application_text, r.year_from ? `${r.year_from}${r.year_to ? "–" + r.year_to : ""}` : ""].filter(Boolean).join(", "))}</span></span>
      ${comSit ? `<span class="ap-sit ${SIT[r.sit][1]}"><i></i>${SIT[r.sit][0]}</span>` : `<span class="ap-sit">${esc(cap(r.status))}</span>`}</li>`).join("") : '<li class="vazio">Nenhum item.</li>'}</ul></section>`;

  function desenhar() {
    const K = d.kpi, L = [...d.itens].sort((a, b) => ORD[a.sit] - ORD[b.sit] || a.code.localeCompare(b.code)), E = d.envio, R = d.resposta;
    const conta = k => L.filter(r => r.sit === k).length, env = conta("enviado"), res = conta("ressalva"), ap = K.aprovado, enviados = env + res + ap;
    const frase = env ? [`${nf(env)} ${env === 1 ? "item aguarda" : "itens aguardam"} sua aprovação`, `Enviados no e-mail «${esc(E ? E.assunto : "Sugestão de IPI")}». Para aprovar, responda o e-mail dizendo que aprovou; se algum item precisa de outro IPI, cite o código.`]
      : ap ? [`${nf(ap)} ${ap === 1 ? "item aprovado" : "itens aprovados"}`, `${R ? `Resposta registrada em ${esc(R.recebido_em || dmy(R.registrado_em))}.` : ""}${res ? ` ${nf(res)} ${res === 1 ? "item ficou" : "itens ficaram"} com ressalva e volta${res === 1 ? "" : "m"} para o Italo decidir.` : ""}${K.prec ? ` ${nf(K.prec)} ${K.prec === 1 ? "item ainda não foi enviado" : "itens ainda não foram enviados"}.` : ""}`]
      : [`${nf(K.controladoria)} itens estão finalizando o CIT`, "A sugestão de IPI deles ainda não foi enviada. Quando o e-mail «Sugestão de IPI» chegar, eles aparecem aqui como aguardando sua aprovação."];
    const passo = (k, t, q, s, cls) => `<li class="${cls}"><span class="num" aria-hidden="true">${k}</span><div><b>${t}</b><div class="q">${nf(q)}</div><div class="s">${s}</div></div></li>`;
    const p1 = enviados ? "feito" : "agora", p2 = env ? "agora" : enviados ? "feito" : "", p3 = ap && !env ? "feito" : "";
    const vis = L.filter(r => (!sitf || r.sit === sitf || (sitf === "enviado" && r.sit === "ressalva")) && (!busca || [r.id, r.code, r.make, r.vehicle, r.application_text].join(" ").toUpperCase().includes(busca)));
    const tl = L.filter(r => val(r) === 10.4).length, tp = L.filter(r => val(r) === 2.6).length;
    const chip = (k, t, c) => `<button type="button" data-sit="${k}" aria-pressed="${sitf === k}">${t}<span>${nf(c)}</span></button>`;
    const pes = d.aprovadores.map(a => `<span><i class="${a.estado === "aprovou" ? "ok" : a.estado === "aguardando" ? "esp" : ""}"></i><b>${esc(a.nome)}</b> ${esc(a.texto)}</span>`).join("");
    el.innerHTML = `<div class="ap-frase"><h2>${frase[0]}</h2><p>${frase[1]}</p></div>
      <ol class="ap-cam">${passo(1, "Sugestão preparada", K.controladoria, "itens finalizando o CIT", p1)}${passo(2, "E-mail enviado", enviados, E ? `em ${dmy(E.confirmado_em)}` : "nada enviado ainda", p2)}${passo(3, "IPI aprovado", ap, "pela resposta do e-mail", p3)}</ol>
      ${R && R.aprovou ? `<div class="ap-resp"><q>${esc(R.trecho || "")}</q><div class="m">Resposta de ${esc(R.autor || "–")}${R.recebido_em ? ", " + esc(R.recebido_em) : ""}</div></div>` : ""}
      <div class="ap-pess">${pes}</div>
      <div class="ap-filtro"><label><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg>
        <input id="busca" type="search" autocomplete="off" placeholder="Procurar código, ID ou veículo" value="${esc(busca)}" aria-label="Procurar"></label>
        ${chip("", "Todos", L.length)}${chip("enviado", "Aguardando", env + res)}${chip("aprovado", "Aprovados", ap)}</div>
      <div class="ap-aliq"><div class="faixa" role="img" aria-label="${tl} itens a 10,4% e ${tp} a 2,6%"><i style="width:${100 * tl / (L.length || 1)}%;background:var(--ap-leve)"></i><i style="width:${100 * tp / (L.length || 1)}%;background:var(--ap-pesado)"></i></div>
        ${pista(10.4, "var(--ap-leve)", "Leve e passeio", "carros e utilitários leves", vis.filter(r => val(r) === 10.4), true)}${pista(2.6, "var(--ap-pesado)", "Utilitário e pesado", "pick-ups, vans, caminhões e linha pesada", vis.filter(r => val(r) === 2.6), true)}</div>
      <details class="ap-prox"><summary>Próximos cadastros: <b>${nf(d.proximos.length)} itens</b> em cotação ou com pedido confirmado</summary><div class="ap-aliq">
        ${pista(10.4, "var(--ap-leve)", "Leve e passeio", "sugestão pela aplicação", d.proximos.filter(r => val(r) === 10.4), false)}${pista(2.6, "var(--ap-pesado)", "Utilitário e pesado", "sugestão pela aplicação", d.proximos.filter(r => val(r) === 2.6), false)}</div></details>
      <p class="ap-rodape">Esta tela só mostra. A aprovação vale pela resposta do e-mail «Sugestão de IPI».</p>`;
  }
  el.addEventListener("click", e => { const s = e.target.closest("[data-sit]"); if (s) { sitf = s.dataset.sit; desenhar(); } });
  el.addEventListener("input", e => { if (e.target.id !== "busca") return; busca = e.target.value.trim().toUpperCase(); const p = e.target.selectionStart; desenhar();
    const b = document.getElementById("busca"); b.focus(); b.setSelectionRange(p, p); });
  fetch("/api/ipi/aprovador").then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }).then(x => { d = x; desenhar(); })
    .catch(() => { el.innerHTML = '<p class="ap-rodape">Não foi possível carregar. Atualize a página; se continuar, avise o Italo.</p>'; });
})();
