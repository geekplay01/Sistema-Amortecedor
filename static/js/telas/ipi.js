/* Tela · Monitoramento de IPI (update 9, ipi.py). Faixa do fluxo (pendente controladoria → precificação → enviados → aprovado; cada número filtra),
   «Enviar para aprovação» (baixa a planilha no modelo IPI.xlsx e abre o Gmail já preenchido numa nova aba; depois «Confirmar envio»),
   a resposta da Mariana como chegou (aprovado só quando o corpo do e-mail diz) e as abas Itens · Anomalias · Próximos cadastros. */
(function () {
  const { $, esc, J, qs, root, fail } = PSD;
  const TW = window.PSDTW, { nf, empty } = TW;
  const ipi = v => v == null ? "–" : nf(v, 1);
  const selo = (v, dv) => v == null ? '<span class="psd-ipi">–</span>' : `<span class="psd-ipi ${v === 2.6 ? "p" : "l"}${dv ? " dv" : ""}">${ipi(v)}</span>`;
  const cap = s => s ? s.charAt(0) + s.slice(1).toLowerCase() : "";
  const dmy = s => s ? TW.dmy(String(s).slice(0, 10)) : "";
  const SIT = { prec: ["Pendente precificação", "amber"], enviado: ["Enviado", "blue"], ressalva: ["Com ressalva", "amber"], aprovado: ["IPI aprovado", "green"] };
  const NOMES = { sit: "Situação", ipi: "IPI sugerido", q: "Busca" }, SITN = { prec: "pendente precificação", enviado: "enviados", aprovado: "IPI aprovado" };
  const cod = l => `<a href="#" class="font-medium text-blue-600" data-rd="des" data-code="${esc(l.code)}">${esc(l.code)}</a>`;
  const veic = l => `${esc([l.make, l.vehicle].filter(Boolean).join(" "))}<span class="block text-xs text-mute">${esc(l.application_text || "")}${l.year_from ? `, ${l.year_from}${l.year_to ? "–" + l.year_to : ""}` : ""}</span>`;
  const refs = l => { const r = ["OEM", "COFAP", "MONROE", "NAKATA", "KAYABA"].filter(k => (l.refs[k] || []).length);
    return r.length ? `<div class="psd-refs">${r.map(k => `<span title="${esc(l.refs[k].join(", "))}"><b>${k}</b> ${esc(String(l.refs[k][0]).split(/[,/]/)[0].trim())}</span>`).join("")}</div>` : '<span class="text-mute">–</span>'; };

  function tela() {
    const F = TW.filtros("monitoramento-ipi", ["sit", "ipi", "q", "aba"]); let d = null, seq = 0, colar = false;
    root.innerHTML = `<div class="psd-ipit"><div id="iacao" class="acao"></div>
      <div id="ifluxo"></div><div id="ienvio"></div><div id="iresp"></div><div id="iabas"></div><div id="ibar"></div><div id="icorpo">${TW.carregando("Lendo o servidor…")}</div></div>`;
    const api = () => { const s = F.get(); return { sit: s.sit || "", ipi: s.ipi || "", q: s.q || "" }; };
    const desenhar = () => {
      const s = F.get(), K = d.kpi, aba = s.aba || "itens", ab = d.envio_aberto;
      $("#iacao").innerHTML = TW.botao("Baixar Excel", { href: `/api/export/ipi.xlsx?${qs(api())}`, icone: "download", secundario: true })
        + `<button type="button" class="psd-btn prim" data-acao="enviar" ${K.prec ? "" : "disabled"}>${TW.ico("send", "sm")}Enviar para aprovação<span class="psd-vn">${nf(K.prec)}</span></button>`;
      const pes = d.aprovadores.map(a => `<span><i class="psd-dot ${a.estado === "aprovou" ? "ok" : a.estado === "aguardando" ? "am" : ""}"></i>${esc(a.nome)} <small>${esc(a.texto)}</small></span>`).join("");
      const st = (k, r, v, sub, t, extra = "") => `<button type="button" data-sit="${k}" aria-pressed="${(s.sit || "") === k}"><span class="r">${r}</span><span class="v ${t}">${nf(v)}</span><span class="s">${sub}</span>${extra}</button>`;
      $("#ifluxo").innerHTML = `<div class="psd-fluxo" role="group" aria-label="Situação">${st("", "Pendente controladoria", K.controladoria, "Finalizando CIT, saiu de compras", "")
        + st("prec", "Pendente precificação", K.prec, "sugestão ainda não enviada", K.prec ? "am" : "ze")
        + st("enviado", "Enviados para aprovação", K.enviado, K.ressalva ? `${nf(K.ressalva)} com ressalva` : "aguardando a resposta", K.enviado ? "" : "ze", `<div class="psd-pes">${pes}</div>`)
        + st("aprovado", "IPI aprovado", K.aprovado, "pela resposta da Mariana", K.aprovado ? "ok" : "ze")}</div>`;
      $("#ienvio").innerHTML = ab ? `<div class="psd-envio">${TW.ico("send", "sm")}<span><span class="font-medium">${esc(ab.assunto)}</span>: ${nf(ab.itens)} itens preparados. Arraste a planilha baixada no Gmail e envie; depois confirme aqui.</span>
        <span class="ac"><a class="psd-btn" href="/api/ipi/envio/${ab.id}.xlsx">${TW.ico("download", "sm")}Planilha</a><button type="button" class="psd-btn" data-acao="cancelar" data-id="${ab.id}">Cancelar</button>
        <button type="button" class="psd-btn prim" data-acao="confirmar" data-id="${ab.id}">${TW.ico("check", "sm")}Confirmar envio</button></span></div>` : "";
      const R = d.resposta;
      $("#iresp").innerHTML = (R ? `<div class="psd-resp${R.aprovou ? "" : " sem"}"><i class="psd-dot ${R.aprovou ? "ok" : ""}" style="margin-top:5px"></i><div><div class="mu">Resposta de ${esc(R.autor || "–")}${R.recebido_em ? ", " + esc(R.recebido_em) : ""}, ao e-mail «${esc(R.assunto)}»</div>
          <div>${R.trecho ? "<mark>" + esc(R.trecho) + "</mark>" : esc((R.texto || "").slice(0, 400))}</div>
          <div class="mu">${R.aprovou ? `Aprovação no corpo do e-mail${R.ressalvas.length ? `; com ressalva: ${esc(R.ressalvas.join(", "))}` : ""}.` : "Sem aprovação no corpo do e-mail: nada mudou."}</div></div>
          ${d.ultimo_envio ? '<span class="ac"><button type="button" class="psd-btn" data-acao="colar">Registrar outra resposta</button></span>' : ""}</div>`
        : d.ultimo_envio ? `<div class="psd-resp sem"><i class="psd-dot am" style="margin-top:5px"></i><div>Aguardando a resposta da Mariana. Peça ao Claude «verifique a resposta do IPI», ou cole a resposta aqui.</div><span class="ac"><button type="button" class="psd-btn" data-acao="colar">Colar resposta</button></span></div>` : "")
        + (colar ? `<form class="psd-colar" id="icolar"><input name="autor" placeholder="Quem respondeu" value="Mariana Agostinho" required aria-label="Quem respondeu"><input name="recebido_em" placeholder="Quando (dd/mm/aaaa hh:mm)" aria-label="Quando">
          <textarea name="texto" placeholder="Cole aqui o corpo do e-mail de resposta" required aria-label="Corpo do e-mail"></textarea><div class="ac"><button class="psd-btn prim" type="submit">Registrar resposta</button><button class="psd-btn" type="button" data-acao="fechar">Cancelar</button>
          <span class="text-xs text-mute">Só vira «IPI aprovado» se o corpo disser que aprovou.</span></div></form>` : "");
      const tab = (k, l, c, am) => `<button type="button" role="tab" data-aba="${k}" aria-pressed="${aba === k}" aria-selected="${aba === k}">${l}<span class="psd-vn${am && c ? " am" : ""}">${nf(c)}</span></button>`;
      $("#iabas").innerHTML = `<div class="psd-seg" role="tablist" aria-label="Abas do Monitoramento de IPI">${tab("itens", "Itens", K.controladoria)}${tab("anom", "Anomalias", d.n_anomalias, true)}${tab("prox", "Próximos cadastros", d.proximos.length)}</div>`;
      $("#ibar").hidden = aba !== "itens";
      if (aba === "anom") return anomalias();
      if (aba === "prox") return proximos();
      TW.pintarBarra($("#ibar"), { busca: { valor: s.q, ph: "ID, código, veículo, aplicação ou marca" },
        atalhos: [{ k: "ipi", v: "10.4", l: "10,4 leve e passeio", n: K.leve, on: s.ipi === "10.4" }, { k: "ipi", v: "2.6", l: "2,6 utilitário e pesado", n: K.pesado, on: s.ipi === "2.6" }],
        etiquetas: TW.etiquetas(s, NOMES, (k, v) => k === "sit" ? SITN[v] || v : k === "ipi" ? nf(+v, 1) : v) });
      $("#icorpo").innerHTML = `<p class="mb-2 text-sm text-mute"><span class="font-medium text-ink">${nf(d.itens.length)}</span> item(ns)</p>`
        + (d.itens.length ? TW.table([{ h: "ID" }, { h: "Código" }, { h: "Situação" }, { h: "IPI servidor" }, { h: "Sugestão" }, { h: "Veículo e aplicação", nw: false }, { h: "Marca" }, { h: "Referências", nw: false }],
          d.itens.map(l => [`<span class="tabular-nums text-mute">${esc(l.id)}</span>`, `${cod(l)}<span class="block text-xs text-mute">${esc(cap(l.family))}</span>`,
            `${TW.badge(SIT[l.sit][0], SIT[l.sit][1])}${l.enviado_em ? `<span class="block text-xs text-mute">enviado ${dmy(l.enviado_em)}</span>` : ""}`,
            `${selo(l.ipi, l.ipi != null && l.ipi !== l.sug)}${l.bi03 != null && l.bi03 !== l.ipi ? `<span class="psd-dv">Protheus ${ipi(l.bi03)}</span>` : ""}`,
            `<span class="inline-block min-w-[10rem]">${selo(l.sug)}<span class="block text-xs text-mute">${esc(l.regra)}</span></span>`, `<span class="inline-block min-w-[13rem]">${veic(l)}</span>`, esc(l.brand || "–"), refs(l)]), { h: "max-h-[65vh]" })
          : empty("Nenhum item com estes filtros."));
    };
    const anomalias = () => {
      const A = d.anomalias, lst = (xs, f) => xs.length ? `<ul>${xs.map(f).join("")}</ul>` : "";
      const it = (l, t) => `<li>${cod(l)} <span class="text-xs text-mute">ID ${esc(l.id)}</span> ${t}</li>`;
      const c = (t, dsc, xs, f) => `<div class="psd-anc"><h4>${t}</h4><div class="n ${xs.length ? "" : "ze"}">${nf(xs.length)}</div><div class="d">${dsc}</div>${lst(xs, f)}</div>`;
      $("#icorpo").innerHTML = `<div class="psd-ancs">${c("Servidor × sugestão", "IPI cadastrado diferente do que a aplicação indica", A.srv, l => it(l, `servidor ${ipi(l.ipi)}, sugerido ${ipi(l.sug)} (${esc(l.regra)})`))}
        ${c("Protheus × servidor", "IPI do cadastro Protheus (BI03) diferente do servidor", A.protheus, l => it(l, `Protheus ${ipi(l.bi03)}, servidor ${ipi(l.ipi)}`))}
        ${c("Veículo com os dois IPIs", "o histórico do veículo tem 10,4 e 2,6", A.misto, l => it(l, esc([l.make, l.vehicle].join(" "))))}
        ${c("Sem IPI no servidor", "Pedido confirmado ou Finalizando CIT sem IPI", A.sem_ipi, l => it(l, esc(l.status)))}
        ${c("IPI fora de 10,4 e 2,6", "valor diferente dos dois usados", A.fora, l => it(l, `IPI ${ipi(l.ipi)}`))}
        ${c("Enviado sem resposta", "e-mail confirmado há mais de 7 dias sem aprovação", A.sem_resposta, e => `<li>${esc(e.assunto)}, ${nf(e.itens)} itens, enviado ${dmy(e.confirmado_em)}</li>`)}</div>`;
    };
    const proximos = () => {
      $("#icorpo").innerHTML = `<p class="mb-2 text-sm text-mute">${nf(d.proximos.length)} itens em Em cotação e Pedido confirmado; a sugestão já indica o IPI que virá.</p>`
        + TW.table([{ h: "ID" }, { h: "Código" }, { h: "Status" }, { h: "IPI servidor" }, { h: "Sugestão" }, { h: "Veículo e aplicação", nw: false }, { h: "Marca" }],
          d.proximos.map(l => [`<span class="tabular-nums text-mute">${esc(l.id)}</span>`, cod(l), `<span class="text-xs text-mute">${esc(l.status)}</span>`,
            selo(l.ipi), `${selo(l.sug)}<span class="block text-xs text-mute">${esc(l.regra)}</span>`, veic(l), esc(l.brand || "–")]), { h: "max-h-[65vh]" });
    };
    const carregar = async () => { const meu = ++seq;
      try { const r = await J("/api/ipi?" + qs(api())); if (meu !== seq) return; d = r; desenhar(); } catch (e) { fail(e); } };
    const aplicar = patch => { if (patch) F.set(patch); carregar(); };
    TW.ligarBarra($("#ibar"), { set: (k, v) => aplicar({ [k]: v }), busca: t => aplicar({ q: t }), limpar: () => { const a = F.get().aba; F.clear(); aplicar(a ? { aba: a } : null); } });
    root.addEventListener("submit", async e => { if (e.target.id !== "icolar") return; e.preventDefault();
      try { const r = await J("/api/ipi/resposta", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...Object.fromEntries(new FormData(e.target)), envio_id: d.ultimo_envio }) });
        TW.toast(r.aprovou ? "Aprovação registrada" : "Resposta registrada, sem aprovação no corpo do e-mail", { tom: r.aprovou ? "ok" : "aviso" }); colar = false; carregar(); } catch (er) { TW.erro(er); } });
    root.addEventListener("click", async e => {
      const b = e.target.closest("[data-sit],[data-aba],[data-acao]"); if (!b || !root.contains(b) || b.closest("#ibar")) return;
      if (b.dataset.sit !== undefined) return aplicar({ sit: (F.get().sit || "") === b.dataset.sit ? "" : b.dataset.sit, aba: "" });
      if (b.dataset.aba) return aplicar({ aba: b.dataset.aba === "itens" ? "" : b.dataset.aba });
      const a = b.dataset.acao;
      if (a === "colar") { colar = true; return desenhar(); }
      if (a === "fechar") { colar = false; return desenhar(); }
      if (a === "enviar") {
        const w = window.open("", "_blank");          /* abre a aba já no clique: depois da espera o navegador bloquearia a janela */
        try { const r = await J("/api/ipi/envio", { method: "POST" });
          const dl = document.createElement("a"); dl.href = r.xlsx; dl.download = ""; document.body.appendChild(dl); dl.click(); dl.remove();
          if (w) w.location = r.gmail; else window.open(r.gmail, "_blank");
          TW.toast(`${nf(r.itens)} itens: planilha baixada e Gmail aberto`, { tom: "info", titulo: "Envio preparado" }); carregar(); }
        catch (er) { if (w) w.close(); TW.erro(er); }
        return;
      }
      if (a === "confirmar" || a === "cancelar") {
        try { await J(`/api/ipi/envio/${b.dataset.id}/${a}`, { method: "POST" }); TW.toast(a === "confirmar" ? "Envio confirmado: itens em «Enviado»" : "Envio cancelado", { tom: a === "confirmar" ? "ok" : "info" }); carregar(); }
        catch (er) { TW.erro(er); }
      }
    });
    carregar();
  }
  PSD.tela("monitoramento-ipi", tela);
})();
