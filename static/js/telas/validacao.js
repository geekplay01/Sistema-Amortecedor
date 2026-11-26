/* Tela · Validação (etapa 24) e a aba «Validar itens» do Redesenvolvimento.
   Bancada em 4 passos: 1 · Desenhos (PERFECT com a máscara limpa pela ferramenta de seleção; desenho do fornecedor) → 2 · Família (modelo F-008)
   → 3 · Medidas (o Claude lê e lista; cada linha espera a conferência do usuário; o número da linha liga a tabela às cotas nos dois desenhos)
   → 4 · Revisão e aprovação (damping force, conta e decisão; Aprovar ou Reprovar gera o F-008 em xlsx e pdf; só Aprovar sobe o desenho para Desenhos).
   A mesma bancada abre na tela do menu (/validacao?v=<id>) e na aba do R-D (/redesenvolvimento?aba=validar&v=<id>). Regras: Configurações › Regras das telas. */
(function () {
  const { $, esc, J, root, fail } = PSD;
  const TW = window.PSDTW, { nf, badge, notice, empty, ico, dmy } = TW;
  const ST = { andamento: ["Em andamento", "blue"], aprovada: ["Aprovada", "green"], reprovada: ["Reprovada", "red"] };
  const FAM = v => v ? v.charAt(0) + v.slice(1).toLowerCase().replace("interferencia", "interferência") : "";
  const JS = (u, metodo, corpo) => J("/api/validacao" + u, { method: metodo, headers: { "Content-Type": "application/json" }, body: JSON.stringify(corpo || {}) });
  const VEL = ["0,079", "0,157", "0,314", "0,520", "0,750"];

  /* regras do modelo F-008, iguais a validacao.ap / ap_damping (o servidor confere de novo ao gerar) */
  const numv = v => { const s = String(v ?? "").trim().replace(/[ØøΦ\s]/g, "").replace(",", "."); if (!s || !/^[-+]?(\d+\.?\d*|\.\d+)$/.test(s)) return null; return Number(s); };
  const ap = l => {
    const F = String(l.p || "").trim(), I = String(l.f || "").trim(), L = String(l.tm || "").trim(), M = String(l.tn || "").trim();
    if (L.toLowerCase() === "ok") return "A"; if (L.toUpperCase() === "N") return "R";
    if (!F || !I || numv(F) === 0) return "";
    const Fs = F.toUpperCase(), Is = I.toUpperCase();
    if (Fs.startsWith("M") && Is.startsWith("M")) return Fs === Is ? "A" : "R";
    for (const s of ["T", "°", "'"]) if (Fs.endsWith(s) && Is.endsWith(s)) return Fs === Is ? "A" : "R";
    const fn = numv(F), inn = numv(I); if (fn == null || inn == null) return Fs === Is ? "A" : "R";
    const lt = numv(L) || 0, mt = numv(M) || 0;
    if (fn === inn && fn > 0) return "A"; if (inn - lt <= fn && inn > fn) return "A"; if (fn + mt <= inn && inn < fn) return "A"; return "R";
  };
  /* damping: «faixa» (modelo Cartucho) ou «relativa» (os outros), como a fórmula Ap da aba DampingForce de cada modelo */
  const TOLD = [0.3, 0.25, 0.15, 0.15, 0.15], TOLR = [0.3, 0.25, 0.15, 0.2, 0.15];
  const apDamp = (p, f, regra) => { const pv = [0, 1, 2, 3, 4].map(i => numv((p || [])[i]) || 0), fv = [0, 1, 2, 3, 4].map(i => numv((f || [])[i]) || 0); if (!pv.some(Boolean)) return "";
    if (regra === "faixa") return pv.every((c, i) => { const t = TOLD[i], h = fv[i], lo = c < 1000 ? c * (1 - t) + 30 : c * (1 - t), hi = c < 1000 ? c * (1 + t) - 30 : c * (1 + t); return lo <= h && h <= hi; }) ? "A" : "R";
    if (!pv.slice(1).every(Boolean)) return "";
    return Math.abs(fv[0] - pv[0]) <= Math.abs(pv[0] * TOLR[0]) + 0.03 && [1, 2, 3, 4].every(i => Math.abs(fv[i] - pv[i]) / pv[i] <= TOLR[i]) ? "A" : "R"; };
  const usada = l => String(l.p || "").trim() || String(l.f || "").trim();
  const conta = ls => { const u = ls.filter(usada); return { linhas: u.length, conferidas: u.filter(l => l.conferida).length, A: u.filter(l => ap(l) === "A").length, R: u.filter(l => ap(l) === "R").length }; };
  const apTag = a => a ? `<span class="psd-ap ${a}">${a}</span>` : '<span class="text-mute">–</span>';

  /* ======================= bancada ======================= */
  function bancada(el, vid, o = {}) {
    let v = null, passo = null, armado = null, timer = null, sel = null, base = null, esc3 = null, tecla3 = null, modo = "marcar";
    const zoom = {}, desfazer = [];          // zoom e posição de cada desenho no passo 3 (ficam ao trocar de passo); números postos (Ctrl+Z)
    const ro = () => v.status !== "andamento";
    /* versão leve do desenho (JPEG 1600 px); o endereço só muda quando a imagem muda (img_ver), então o navegador reaproveita */
    const src = n => `/api/validacao/${vid}/img/${n}.png?tela=1&u=${v.img_ver[n] || 0}`;
    const imgPerfect = () => v.imagens.perfect_limpo ? "perfect_limpo" : "perfect";
    const PASSOS = ["Desenhos", "Família", "Medidas", "Revisão e aprovação"];
    const sub = i => { const c = conta(v.dados.linhas);
      return [v.imagens.perfect && v.imagens.fornecedor ? (v.dados.mascara.length ? "máscara limpa" : "PERFECT e fornecedor") : "falta enviar", FAM(v.family) || "modelo F-008",
              c.linhas ? `${nf(c.conferidas)} de ${nf(c.linhas)} conferidas` : "leitura e conferência", ro() ? ST[v.status][0] : "F-008 em xlsx e pdf"][i]; };
    const feito = i => { const c = conta(v.dados.linhas); return [v.imagens.perfect && v.imagens.fornecedor, !!v.family, c.linhas > 0 && c.conferidas === c.linhas, ro()][i]; };
    const inicial = () => ro() ? 3 : !(v.imagens.perfect && v.imagens.fornecedor) ? 0 : !v.family ? 1 : 2;

    const topo = () => `<div class="psd-banc-top">
        ${o.voltar ? `<a class="psd-vvolta" href="${o.voltar}">${ico("chevron-right", "sm")}<span>Voltar à lista</span></a>` : ""}
        <span class="id">${esc(v.code)}</span><span class="psd-vrevn" title="Revisão do teste (último REV do nome do F-008)">Rev.${String(v.revisao || 0).padStart(2, "0")}</span><span class="desc">${esc([v.info.description, v.info.vehicle].filter(Boolean).join(", "))}</span>
        <dl class="psd-par"><div><dt>Fornecedor</dt><dd>${esc(v.supplier || "–")}</dd></div><div><dt>Cód. fornecedor</dt><dd>${esc(v.supplier_code || "–")}</dd></div>
          <div><dt>Família</dt><dd>${esc(FAM(v.family) || "–")}</dd></div><div><dt>Tipo</dt><dd>${esc(FAM(v.kind_label))}</dd></div>
          ${v.par ? `<div><dt>Lado</dt><dd>${esc(v.par.meu)}, par ${v.par.validacao ? `<a class="psd-vpar" href="#" data-irpar="${v.par.validacao.id}">${esc(v.par.code)} (${esc(v.par.lado)})</a>` : esc(`${v.par.code} (${v.par.lado})`)}</dd></div>` : ""}</dl>
        <span class="dir">${badge(ST[v.status][0], ST[v.status][1])}<span id="vsalvo" class="text-xs text-mute">${ro() ? "concluída em " + dmy(v.concluida_em) : v.updated_at ? "rascunho salvo " + String(v.updated_at).slice(11, 16) : ""}</span>
          <button type="button" class="psd-vx" data-excluir title="Excluir esta revisão" aria-label="Excluir esta revisão">${ico("trash-2", "sm")}</button></span></div>
      <div class="psd-passos" role="tablist">${PASSOS.map((t, i) => `<button type="button" role="tab" data-passo="${i}" aria-selected="${i === passo}" class="${feito(i) ? "feito" : ""}">${i + 1} · ${t}<small>${esc(sub(i))}</small></button>`).join("")}</div>`;
    const redesenharTopo = () => { const t = $("#vtopo", el); if (t) t.innerHTML = topo(); };
    const desenhar = () => { el.innerHTML = `<div class="psd-banc"><div id="vtopo">${topo()}</div><div id="vbc"></div></div>`; corpo(); };
    const corpo = () => { document.querySelectorAll("body > .psd-vdes.cheio").forEach(x => x.remove()); document.body.classList.remove("psd-vcheio"); esc3 = null;
      const c = $("#vbc", el); c.innerHTML = [passo1, passo2, passo3, passo4][passo](); [ligar1, ligar2, ligar3, ligar4][passo](c); };
    const ir = i => { passo = i; redesenharTopo(); corpo(); };
    const salvar = async (b, redesenha = false) => { try { v = await JS(`/${vid}`, "PATCH", b); redesenharTopo(); if (redesenha) corpo(); } catch (e) { TW.erro(e); if (redesenha) corpo(); } };
    const salvarLinhas = () => { clearTimeout(timer); timer = setTimeout(() => salvar({ linhas: v.dados.linhas }), 700); };
    const rodape = (prox, txt) => prox == null ? "" : `<div class="psd-vrodape"><button type="button" class="psd-btn" data-ir="${prox}">${esc(txt)}${ico("chevron-right", "sm")}</button></div>`;
    const drop = (lado, rot) => ro() ? empty("Sem desenho.") : `<label class="psd-drop" data-drop="${lado}">${ico("upload", "lg")}<b>Enviar ${esc(rot)}</b><span>PDF, PNG ou JPG; arraste o arquivo para cá ou clique</span><input type="file" accept=".pdf,.png,.jpg,.jpeg,.bmp,.webp" data-up="${lado}" hidden></label>`;
    const trocar = lado => ro() ? "" : `<label class="psd-btn sm">${ico("upload", "sm")}Trocar arquivo<input type="file" accept=".pdf,.png,.jpg,.jpeg,.bmp,.webp" data-up="${lado}" hidden></label>`;
    const enviar = async (lado, f) => { if (!f) return; const fd = new FormData(); fd.append("file", f);
      try { v = await TW.enviar(`/api/validacao/${vid}/desenho/${lado}`, fd, [f]); redesenharTopo(); corpo(); const ln = v.lido_do_nome || {};
        TW.toast(lado === "perfect" ? "Desenho PERFECT enviado." : ln.supplier ? `Desenho do fornecedor enviado. Pelo nome do arquivo: ${ln.supplier}${ln.supplier_code ? ", código " + ln.supplier_code : ""}.` : "Desenho do fornecedor enviado. O nome do arquivo não traz o fornecedor: informe abaixo."); } catch (e) { TW.erro(e); } };
    const irPara = id => { location.href = (o.base || location.pathname) + "?" + new URLSearchParams({ ...(o.params || {}), v: id }); };
    const ligarEnvio = c => {
      c.querySelectorAll("[data-up]").forEach(i => i.addEventListener("change", () => enviar(i.dataset.up, i.files[0])));
      c.querySelectorAll("[data-drop]").forEach(z => { z.addEventListener("dragover", e => { e.preventDefault(); z.classList.add("sobre"); }); z.addEventListener("dragleave", () => z.classList.remove("sobre"));
        z.addEventListener("drop", e => { e.preventDefault(); z.classList.remove("sobre"); enviar(z.dataset.drop, e.dataTransfer.files[0]); }); });
      c.querySelectorAll("[data-ir]").forEach(b => b.addEventListener("click", () => ir(+b.dataset.ir)));
    };

    /* ---------- passo 1: desenhos ---------- */
    const passo1 = () => `<div class="psd-vdois">
      <section><h3>Desenho PERFECT</h3><p class="psd-vsub">Vai no F-008 em «Drawing image and/or picture of OEM/Reference»</p>
        ${v.imagens.perfect ? `${ro() ? "" : `<div class="psd-ferr"><span class="psd-ferr-dica">${ico("square-dashed", "sm")}Arraste para selecionar</span>
            <button type="button" class="psd-btn sm" data-m="apagar" title="Delete">${ico("eraser", "sm")}Apagar seleção</button><button type="button" class="psd-btn sm" data-m="manter">${ico("crop", "sm")}Manter só a seleção</button>
            <button type="button" class="psd-btn sm" data-m="desfazer" ${v.dados.mascara.length ? "" : "disabled"}>${ico("rotate-ccw", "sm")}Desfazer</button><span class="ml-auto">${trocar("perfect")}</span></div>`}
          <div class="psd-papel psd-masc" id="vpm" tabindex="0" aria-label="Desenho PERFECT: arraste para selecionar a área da máscara"><canvas></canvas><div class="psd-sel" hidden></div></div>` : drop("perfect", "o desenho PERFECT")}</section>
      <section><h3>Desenho do fornecedor</h3><p class="psd-vsub">Vai no F-008 em «Drawing image and/or Sample received»</p>
        ${v.imagens.fornecedor ? `${ro() ? "" : `<div class="psd-ferr"><span class="ml-auto">${trocar("fornecedor")}</span></div>`}<div class="psd-papel"><img alt="Desenho do fornecedor" src="${src("fornecedor")}"></div>` : drop("fornecedor", "o desenho do fornecedor")}
        <div class="psd-vcampos">
          <label><span>Fornecedor</span><input data-c="supplier" list="vforn" value="${esc(v.supplier || "")}" ${ro() ? "disabled" : ""}><datalist id="vforn">${(v.info.suppliers || []).map(s => `<option value="${esc(s)}">`).join("")}</datalist></label>
          <label><span>Código do fornecedor</span><input data-c="supplier_code" value="${esc(v.supplier_code || "")}" placeholder="Nº do desenho, ex.: DQ41746" ${ro() ? "disabled" : ""}></label>
          <label><span>Recebido em</span><input data-c="received_at" type="date" value="${esc(v.received_at || "")}" ${ro() ? "disabled" : ""}></label>
        </div></section></div>${rodape(1, "Próximo: família")}`;
    const ligar1 = c => {
      ligarEnvio(c);
      c.querySelectorAll("[data-c]").forEach(i => i.addEventListener("change", () => salvar({ [i.dataset.c]: i.value })));
      const box = $("#vpm", c); if (!box) return;
      const cv = box.querySelector("canvas"), sx = box.querySelector(".psd-sel"), ctx = cv.getContext("2d");
      base = new Image(); base.src = src("perfect");
      const pinta = () => { if (!base.naturalWidth) return; cv.width = base.naturalWidth; cv.height = base.naturalHeight; ctx.drawImage(base, 0, 0); const W = cv.width, H = cv.height;
        for (const op of v.dados.mascara) { const [x, y, w, h] = op.r, r = [x * W, y * H, w * W, h * H];
          if (op.t === "apagar") { ctx.fillStyle = "#fff"; ctx.fillRect(...r); }
          else { const d = ctx.getImageData(...r.map(Math.round)); ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, W, H); ctx.putImageData(d, Math.round(r[0]), Math.round(r[1])); } } };
      base.onload = pinta;
      if (ro()) return;
      const fr = e => { const b = cv.getBoundingClientRect(); return [Math.min(Math.max((e.clientX - b.left) / b.width, 0), 1), Math.min(Math.max((e.clientY - b.top) / b.height, 0), 1)]; };
      const mostra = () => { if (!sel) { sx.hidden = true; return; } const [x, y, w, h] = sel; Object.assign(sx.style, { left: x * 100 + "%", top: y * 100 + "%", width: w * 100 + "%", height: h * 100 + "%" }); sx.hidden = false; };
      let ini = null;
      box.addEventListener("pointerdown", e => { if (e.button !== 0) return; box.focus(); box.setPointerCapture(e.pointerId); ini = fr(e); sel = [...ini, 0, 0]; mostra(); });
      box.addEventListener("pointermove", e => { if (!ini) return; const p = fr(e); sel = [Math.min(ini[0], p[0]), Math.min(ini[1], p[1]), Math.abs(p[0] - ini[0]), Math.abs(p[1] - ini[1])]; mostra(); });
      box.addEventListener("pointerup", () => { ini = null; if (sel && (sel[2] < 0.004 || sel[3] < 0.004)) { sel = null; mostra(); } });
      const op = async t => {
        if (t === "desfazer") { v.dados.mascara.pop(); }
        else { if (!sel) return TW.toast("Arraste no desenho para selecionar a área primeiro.", { tom: "aviso" }); v.dados.mascara.push({ t, r: sel }); sel = null; mostra(); }
        pinta(); c.querySelector('[data-m="desfazer"]').disabled = !v.dados.mascara.length; await salvar({ mascara: v.dados.mascara });
      };
      c.querySelectorAll("[data-m]").forEach(b => b.addEventListener("click", () => op(b.dataset.m)));
      box.addEventListener("keydown", e => { if ((e.key === "Delete" || e.key === "Backspace") && sel) { e.preventDefault(); op("apagar"); } else if (e.key === "Escape") { sel = null; mostra(); }
        else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z" && v.dados.mascara.length) { e.preventDefault(); op("desfazer"); } });
    };

    /* ---------- passo 2: família ---------- */
    const passo2 = () => { const f = v.familias.find(x => x.v === v.family);
      return `<div class="psd-vfam"><div class="psd-rot">Família do amortecedor (modelo F-008)</div>
        <div class="psd-est psd-linha" role="group" aria-label="Família">${v.familias.map(x => `<button type="button" data-fam="${esc(x.v)}" aria-pressed="${x.v === v.family}" ${ro() ? "disabled" : ""}><span class="t">${esc(x.l)}</span><span class="n" title="medidas no modelo">${nf(x.n)}</span></button>`).join("")}</div>
        ${!v.family && v.info.family ? notice(`A família do item no catálogo é «${esc(FAM(v.info.family))}», que não tem modelo F-008. Escolha o modelo mais próximo.`, "amber") : ""}
        <label class="psd-switch"><input type="checkbox" data-mola ${v.dados.mola ? "checked" : ""} ${ro() ? "disabled" : ""}><span class="tr" aria-hidden="true"></span><span class="tx"><b>Item com mola</b><small>Acrescenta a medida LMAX2, logo abaixo do LMAX</small></span></label>
        ${f ? `<div class="psd-vlista"><div class="psd-rot">Medidas desta validação, na ordem do F-008</div><ol>${(v.dados.linhas.length ? v.dados.linhas.map(l => l.nome) : f.medidas).map(m => `<li${m === "LMAX2" ? ' class="mola"' : ""}>${esc(m)}</li>`).join("")}</ol></div>` : empty("Escolha a família para ver as medidas do modelo.")}
      </div>${rodape(v.family ? 2 : null, "Próximo: medidas")}`; };
    const ligar2 = c => { ligarEnvio(c);
      c.querySelectorAll("[data-fam]").forEach(b => b.addEventListener("click", async () => { const nova = b.dataset.fam; if (nova === v.family) return;
        if (v.family && conta(v.dados.linhas).linhas && !(await TW.confirmar({ titulo: `Trocar para ${FAM(nova)}?`, texto: "As medidas com o mesmo nome guardam os valores; as que não existem no outro modelo saem da tabela.", botao: "Trocar a família" }))) return;
        salvar({ family: nova }, true); }));
      const ml = c.querySelector("[data-mola]"); if (ml) ml.addEventListener("change", () => salvar({ mola: ml.checked }, true)); };

    /* ---------- passo 3: medidas ----------
       Digitação no desenho (padrão, sem API): «Digitar no desenho» marca a linha; o clique na cota abre o campo ali mesmo (PERFECT: valor e tolerâncias,
       «553±3» já separa; fornecedor: valor). Enter grava, põe o número no desenho e passa para a próxima linha. Roda do mouse aproxima, arrastar move,
       «Tela cheia» abre o desenho grande. Com a leitura pelo Claude ligada em Configurações, aparece também «Ler medidas com o Claude». */
    const marca = (l, i, lado) => l[lado] ? `<span class="psd-mk" data-i="${i}" style="left:${l[lado][0] * 100}%;top:${l[lado][1] * 100}%" title="${esc(l.n + " " + l.nome)}">${l.n}</span>` : "";
    const marcas = lado => v.dados.linhas.map((l, i) => marca(l, i, lado)).join("");
    const LADO = { pp: "PERFECT", pf: "fornecedor" };
    const linha = (l, i) => { const dis = ro() ? "disabled" : "", a = ap(l);
      return `<tr data-i="${i}" class="${armado === i ? "armada" : ""}">
        <td><button type="button" class="psd-num${armado === i ? " armado" : ""}" data-arma="${i}" ${dis} title="Digitar esta medida no desenho">${l.n}</button></td>
        <td class="nome">${!ro() ? `<input data-k="nome" class="nm" value="${esc(l.nome)}" title="Nome da cota no F-008 (só nesta validação)" aria-label="Nome da cota em inglês">` : `<span>${esc(l.nome)}</span>`}${l.obs ? `<small title="${esc(l.obs)}">${esc(l.obs)}</small>` : ""}</td>
        ${["p", "f", "tm", "tn"].map(k => `<td><input data-k="${k}" value="${esc(l[k] || "")}" class="r${k === "p" && l.fonte_p ? " pre" : ""}" ${k === "p" && l.fonte_p ? `title="Já preenchido: ${esc(l.fonte_p)}. Confira."` : ""} ${dis} aria-label="${{ p: "PERFECT", f: "Fornecedor", tm: "Tolerância +", tn: "Tolerância −" }[k]}"></td>`).join("")}
        <td class="c" data-ap>${apTag(a)}</td>
        <td><input data-k="melhoria" value="${esc(l.melhoria || "")}" ${dis} aria-label="Melhoria (Improve)"></td>
        <td class="c"><input type="checkbox" data-k="conferida" ${l.conferida ? "checked" : ""} ${dis} aria-label="Conferida"></td>
        <td>${l.extra && !ro() ? `<button type="button" class="psd-vx" data-tira="${i}" aria-label="Tirar a medida">${ico("x", "sm")}</button>` : ""}</td></tr>`; };
    const papel = (lado, titulo, extra, img) => `<div class="psd-vdes" data-des="${lado}"><h4><span class="tt">${titulo}${extra ? `<small>${extra}</small>` : ""}</span>
        <span class="psd-zctl">${img ? `<button type="button" data-z="mais" aria-label="Aproximar">${ico("plus", "sm")}</button><button type="button" data-z="menos" aria-label="Afastar"><b>−</b></button><button type="button" data-z="ajustar">Ajustar</button><button type="button" data-z="cheia">Tela cheia</button>` : ""}</span></h4>
      <div class="psd-papel" data-lado="${lado}">${img ? `<div class="psd-zoom"><img alt="" src="${img}">${marcas(lado)}</div>` : empty("Sem desenho.")}</div></div>`;
    const marcando = () => armado == null ? "" : `<div class="psd-vmarca">${ico("pencil", "sm")}<span>${modo === "marcar" ? "Marcando" : "Digitando"} <b>${esc(v.dados.linhas[armado].n + " " + v.dados.linhas[armado].nome)}</b>: clique na cota${modo === "marcar" ? ". Ctrl+Z desfaz; duplo clique no número abre o valor" : ""}</span>
        <span class="psd-seg sm" role="group" aria-label="Modo"><button type="button" data-modo="marcar" aria-pressed="${modo === "marcar"}">Só marcar</button><button type="button" data-modo="digitar" aria-pressed="${modo === "digitar"}">Marcar e digitar</button></span>
        <button type="button" class="psd-btn sm" data-pular>Pular linha</button><button type="button" class="psd-btn sm" data-parar>Parar</button></div>`;
    const passo3 = () => { const c = conta(v.dados.linhas), lida = v.leitura_em, podeLer = v.ia.ok && !ro() && v.imagens.perfect && v.imagens.fornecedor && v.family;
      return `<div class="psd-vmedidas"><div class="min-w-0">
        <div class="psd-vleit"><span class="info">${lida ? `<b>${nf(c.linhas)} ${c.linhas === 1 ? "medida" : "medidas"}</b>, lidas pelo Claude em ${dmy(lida)} às ${String(lida).slice(11, 16)}; <b>${nf(c.conferidas)}</b> ${c.conferidas === 1 ? "conferida" : "conferidas"}`
            : c.linhas ? `<b>${nf(c.linhas)} ${c.linhas === 1 ? "medida preenchida" : "medidas preenchidas"}</b>, <b>${nf(c.conferidas)}</b> ${c.conferidas === 1 ? "conferida" : "conferidas"}` : "Nenhuma medida preenchida ainda"}</span>
          ${ro() ? "" : `<span class="dir">
            ${v.dados.linhas.length ? `<button type="button" class="psd-btn sm ${c.linhas || v.ia.ligada ? "" : "prim"}" data-digitar>${ico("pencil", "sm")}Marcar no desenho</button>` : ""}
            ${v.imagens.perfect && v.imagens.fornecedor ? `<button type="button" class="psd-btn sm" data-sobrepor>${ico("layers", "sm")}Sobrepor</button>` : ""}
            ${v.ia.ligada ? `<button type="button" class="psd-btn sm ${lida || !v.ia.ok ? "" : "prim"}" data-ler ${podeLer ? "" : "disabled"}>${ico("sparkles", "sm")}${lida ? "Ler de novo" : "Ler medidas com o Claude"}</button>` : ""}
            <button type="button" class="psd-btn sm" data-mais ${v.dados.linhas.length >= 25 ? "disabled" : ""}>${ico("plus", "sm")}Adicionar medida</button>
            ${c.linhas ? `<button type="button" class="psd-btn sm" data-confa>${ico("check", "sm")}Conferir as que deram A</button>` : ""}</span>`}</div>
        ${v.ia.ligada && !v.ia.ok && !ro() ? notice(`${esc(v.ia.motivo)} Enquanto isso, digite as medidas no desenho.`, "amber") : ""}
        ${(() => { const op = v.dados.origem_par; if (!op || ro()) return "";
          return `<div class="psd-vaviso">${ico("arrow-left-right", "sm")}<span>Copiado de <b>${esc(op.code)} (${esc(op.lado)})</b>, ${op.decisao === "aprovada" ? "aprovado" : "reprovado"} em ${dmy(op.em)}: medidas, conferência e posições dos números. Confira as posições neste desenho; se ele for espelhado, use «Espelhar posições».</span>
            <button type="button" class="psd-btn sm" data-espelhar="ambos">${ico("arrow-left-right", "sm")}Espelhar posições</button></div>`; })()}
        ${(() => { if (ro()) return ""; const r = v.reaproveitar || {}, ks = ["pp", "pf"].filter(k => r[k]); if (!ks.length) return "";
          const de = ks.map(k => k === "pp" ? `PERFECT de ${r.pp.code} (${nf(r.pp.n)} linha${r.pp.n === 1 ? "" : "s"})` : `fornecedor ${r.pf.supplier} de ${r.pf.code} (${nf(r.pf.n)} linha${r.pf.n === 1 ? "" : "s"})`).join(" e ");
          return `<div class="psd-vaviso">${ico("history", "sm")}<span>Dá para reaproveitar as posições dos números: ${esc(de)}. Só entram nas linhas sem número; depois é só corrigir arrastando.</span><button type="button" class="psd-btn sm" data-reap="${ks.join(",")}">Reaproveitar posições</button></div>`; })()}
        <div id="vmarca">${marcando()}</div>
        ${v.dados.linhas.length ? `<div class="psd-vtab-w"><table class="psd-vtab"><thead><tr><th>Nº</th><th>Medida</th><th class="r">PERFECT</th><th class="r">Fornecedor</th><th class="r">Tol. +</th><th class="r">Tol. −</th><th class="c">Ap</th><th>Melhoria</th><th class="c">Conferida</th><th></th></tr></thead>
          <tbody>${v.dados.linhas.map(linha).join("")}</tbody></table></div>` : empty("Escolha a família no passo 2 para montar a tabela.")}
        ${ro() ? "" : `<p class="psd-vdica">No PERFECT, «553±3» ou «12.1 +0.15/0» já separa as tolerâncias. Tolerância «OK» aprova e «N» reprova a linha, como no modelo. Roda do mouse aproxima, arrastar move o desenho, arrastar um número muda o lugar dele.</p>`}
      </div>
      <div class="psd-vpilha">
        ${papel("pp", "Desenho PERFECT", v.dados.mascara.length ? "máscara limpa" : "", v.imagens.perfect ? src(imgPerfect()) : "")}
        ${papel("pf", "Desenho do fornecedor", esc([v.supplier, v.supplier_code].filter(Boolean).join(" ")), v.imagens.fornecedor ? src("fornecedor") : "")}
      </div></div>${rodape(3, "Próximo: revisão e aprovação")}`; };
    /* «553±3» → 553, 3, −3 · «12.1 +0.15/0» → 12.1, 0.15, 0 · «Ø51» → 51 */
    const separa = t => { const s = String(t || "").trim().replace(/^[ØøΦ]\s*/, "");
      let m = s.match(/^(.+?)\s*±\s*([\d.,]+)$/); if (m) return { v: m[1].trim(), tm: m[2], tn: "-" + m[2] };
      m = s.match(/^(.+?)\s*\+\s*([\d.,]+)\s*\/\s*-?\s*([\d.,]+)$/); if (m) return { v: m[1].trim(), tm: m[2], tn: Number(m[3].replace(",", ".")) ? "-" + m[3] : "0" };
      return { v: s }; };
    const ligar3 = c => {
      ligarEnvio(c);
      const foco = i => c.querySelectorAll(".psd-mk, .psd-vtab tr").forEach(x => x.classList.toggle("foco", i != null && x.dataset.i === String(i)));
      const tab = c.querySelector(".psd-vtab");
      const atualiza = i => { const tr = tab && tab.querySelector(`tr[data-i="${i}"]`), l = v.dados.linhas[i]; if (!tr) return;
        ["p", "f", "tm", "tn", "melhoria"].forEach(k => { const x = tr.querySelector(`[data-k="${k}"]`); if (x) x.value = l[k] || ""; }); tr.querySelector("[data-ap]").innerHTML = apTag(ap(l)); };
      const melhoria = l => { const a = ap(l); if (a === "R" && !l.melhoria && l.p) l.melhoria = `CHANGE TO ${l.p}`.toUpperCase(); else if (a !== "R" && /^CHANGE TO /.test(l.melhoria || "")) l.melhoria = ""; };
      const armar = i => { armado = i == null || i >= v.dados.linhas.length ? null : i; $("#vmarca", c).innerHTML = marcando();
        c.querySelectorAll("[data-arma]").forEach(y => y.classList.toggle("armado", +y.dataset.arma === armado)); c.querySelectorAll(".psd-vtab tr[data-i]").forEach(y => y.classList.toggle("armada", +y.dataset.i === armado));
        c.querySelectorAll(".psd-papel[data-lado]").forEach(p => p.classList.toggle("armado", armado != null));
        if (armado != null) { const tr = tab && tab.querySelector(`tr[data-i="${armado}"]`); if (tr) tr.scrollIntoView({ block: "nearest" }); } };
      if (tab) {
        tab.addEventListener("mouseover", e => { const tr = e.target.closest("tr[data-i]"); foco(tr ? tr.dataset.i : null); });
        tab.addEventListener("mouseleave", () => foco(null));
        /* tabela como planilha: Enter ou ↓ desce na mesma coluna, Shift+Enter ou ↑ sobe; colar várias linhas (uma coluna do Excel) preenche para baixo */
        const celula = (i, d) => { const tr = i.closest("tr"), k = i.dataset.k; let alvo = tr; do { alvo = d > 0 ? alvo.nextElementSibling : alvo.previousElementSibling; } while (alvo && !alvo.querySelector(`[data-k="${k}"]`));
          return alvo && alvo.querySelector(`[data-k="${k}"]`); };
        tab.addEventListener("keydown", e => { const i = e.target.closest("input[data-k]"); if (!i || i.type === "checkbox") return;
          const d = (e.key === "Enter" && !e.shiftKey) || e.key === "ArrowDown" ? 1 : (e.key === "Enter" && e.shiftKey) || e.key === "ArrowUp" ? -1 : 0; if (!d) return;
          const x = celula(i, d); e.preventDefault(); if (x) { x.focus(); x.select(); } });
        tab.addEventListener("paste", e => { const i = e.target.closest("input[data-k]"); if (!i || i.type === "checkbox") return;
          const vals = (e.clipboardData || window.clipboardData).getData("text").replace(/\r/g, "").split("\n").map(s => s.split("\t")[0].trim()); while (vals.length && !vals[vals.length - 1]) vals.pop();
          if (vals.length < 2) return; e.preventDefault(); let x = i;
          for (const val of vals) { if (!x) break; x.value = val; x.dispatchEvent(new Event("input", { bubbles: true })); x = celula(x, 1); } });
        tab.addEventListener("input", e => { const i = e.target.closest("[data-k]"); if (!i) return; const tr = i.closest("tr"), l = v.dados.linhas[+tr.dataset.i], k = i.dataset.k;
          if (k === "conferida") l.conferida = i.checked; else l[k] = i.value;
          if (k === "p" && l.fonte_p) { delete l.fonte_p; i.classList.remove("pre"); i.removeAttribute("title"); }
          if (["p", "f", "tm", "tn"].includes(k)) { melhoria(l); tr.querySelector("[data-ap]").innerHTML = apTag(ap(l)); tr.querySelector('[data-k="melhoria"]').value = l.melhoria || ""; }
          salvarLinhas(); });
        tab.addEventListener("click", e => { const b = e.target.closest("[data-arma]"), x = e.target.closest("[data-tira]");
          if (b) armar(armado === +b.dataset.arma ? null : +b.dataset.arma);
          if (x) { v.dados.linhas.splice(+x.dataset.tira, 1); v.dados.linhas.forEach((l, k) => l.n = k + 1); armado = null; salvar({ linhas: v.dados.linhas }, true); } });
      }
      /* o ouvinte fica no conteúdo do passo (novo a cada desenho), não em #vbc: em #vbc ele se acumulava a cada troca de passo e «Pular linha» pulava várias */
      c.querySelector(".psd-vmedidas").addEventListener("click", e => { if (e.target.closest("[data-digitar]")) { const i = v.dados.linhas.findIndex(l => !l.pp); armar(i < 0 ? 0 : i); }
        const md = e.target.closest("[data-modo]"); if (md) { modo = md.dataset.modo; armar(armado); }
        const ep = e.target.closest("[data-espelhar]"); if (ep) { clearTimeout(timer); salvar({ linhas: v.dados.linhas, espelhar: ep.dataset.espelhar }, true); }
        const rp = e.target.closest("[data-reap]"); if (rp) { clearTimeout(timer); salvar({ linhas: v.dados.linhas, reaproveitar: rp.dataset.reap.split(",") }, true).then(() => TW.toast("Posições reaproveitadas. Confira e arraste o que mudou.")); }
        if (e.target.closest("[data-sobrepor]")) sobrepor();
        if (e.target.closest("[data-pular]")) { fecharPop(); armar(armado + 1); } if (e.target.closest("[data-parar]")) { fecharPop(); armar(null); } });
      /* Ctrl+Z (ou Backspace fora de um campo): tira o último número posto e volta a linha */
      tecla3 = e => { if (!el.contains(c) || pop) return false; const campo = /^(INPUT|TEXTAREA|SELECT)$/.test((e.target && e.target.tagName) || "");
        const desf = ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z" && !campo) || (e.key === "Backspace" && !campo && armado != null);
        if (!desf || !desfazer.length) return false; e.preventDefault();
        const u = desfazer.pop(), l = v.dados.linhas[u.i]; l[u.lado] = u.antes;
        c.querySelectorAll(`.psd-papel[data-lado="${u.lado}"] .psd-mk[data-i="${u.i}"]`).forEach(m => m.remove());
        const z = c.querySelector(`.psd-papel[data-lado="${u.lado}"] .psd-zoom`); if (z && l[u.lado]) z.insertAdjacentHTML("beforeend", marca(l, u.i, u.lado));
        salvarLinhas(); armar(u.i); return true; };

      /* zoom e arrastar: a camada .psd-zoom (imagem + números) cresce; os números mantêm o tamanho (--z) */
      let pop = null;
      const fecharPop = () => { if (pop) { pop.remove(); pop = null; } };
      c.querySelectorAll(".psd-vdes").forEach(box => {
        const lado = box.dataset.des, p = box.querySelector(".psd-papel"), z = p.querySelector(".psd-zoom"); if (!z) return;
        const st = zoom[lado] || (zoom[lado] = { z: 1, x: 0, y: 0 });
        const limita = () => { const W = p.clientWidth, H = p.clientHeight; st.x = Math.min(0, Math.max(W - W * st.z, st.x)); st.y = Math.min(0, Math.max(H - H * st.z, st.y)); };
        const aplica = () => { limita(); z.style.transform = `translate(${st.x}px,${st.y}px) scale(${st.z})`; z.style.setProperty("--z", st.z); };
        const zoomEm = (f, cx, cy) => { const nz = Math.min(8, Math.max(1, st.z * f)); st.x = cx - (cx - st.x) * nz / st.z; st.y = cy - (cy - st.y) * nz / st.z; st.z = nz; fecharPop(); aplica(); };
        aplica();
        const fr = e => { const r = z.getBoundingClientRect(); return [Math.min(Math.max((e.clientX - r.left) / r.width, 0), 1), Math.min(Math.max((e.clientY - r.top) / r.height, 0), 1)]; };
        p.addEventListener("wheel", e => { e.preventDefault(); const r = p.getBoundingClientRect(); zoomEm(e.deltaY < 0 ? 1.25 : 0.8, e.clientX - r.left, e.clientY - r.top); }, { passive: false });
        box.querySelector(".psd-zctl").addEventListener("click", e => { const b = e.target.closest("[data-z]"); if (!b) return; const W = p.clientWidth / 2, H = p.clientHeight / 2;
          if (b.dataset.z === "mais") zoomEm(1.5, W, H); else if (b.dataset.z === "menos") zoomEm(1 / 1.5, W, H); else if (b.dataset.z === "ajustar") { Object.assign(st, { z: 1, x: 0, y: 0 }); fecharPop(); aplica(); }
          else { const on = !box.classList.contains("cheio"); fecharPop();
            /* tela cheia: o bloco vai para o <body> (sai do recorte e da camada da página) e volta para o mesmo lugar ao fechar */
            if (on) { box._lugar = document.createComment("desenho"); box.before(box._lugar); document.body.appendChild(box); } else if (box._lugar) { box._lugar.replaceWith(box); box._lugar = null; }
            box.classList.toggle("cheio", on); document.body.classList.toggle("psd-vcheio", on); b.textContent = on ? "Fechar tela cheia" : "Tela cheia";
            if (on) { const ir = z.querySelector("img"), ratio = ir.naturalWidth / ir.naturalHeight || 1.414; p.style.width = Math.min(innerWidth - 48, (innerHeight - 96) * ratio) + "px"; } else p.style.width = ""; Object.assign(st, { z: 1, x: 0, y: 0 }); aplica(); } });
        p.addEventListener("mouseover", e => { const m = e.target.closest(".psd-mk"); foco(m ? m.dataset.i : null); });
        let arr = null, pan = null;
        /* rodinha apertada e arrastar = mover o desenho, como no CAD (etapa 24); o clique esquerdo continua pondo o número */
        p.addEventListener("pointerdown", e => { if (e.target.closest(".psd-vpop")) return;
          if (e.button === 1) { e.preventDefault(); pan = { x0: e.clientX, y0: e.clientY, sx: st.x, sy: st.y, moveu: true, meio: true }; p.setPointerCapture(e.pointerId); p.classList.add("movendo"); return; }
          if (e.button !== 0) return; const m = e.target.closest(".psd-mk");
          if (m && !ro()) { e.preventDefault(); arr = m; p.setPointerCapture(e.pointerId); return; }
          pan = { x0: e.clientX, y0: e.clientY, sx: st.x, sy: st.y, moveu: false }; p.setPointerCapture(e.pointerId); });
        p.addEventListener("auxclick", e => { if (e.button === 1) e.preventDefault(); });          // sem a rolagem automática do navegador
        p.addEventListener("mousedown", e => { if (e.button === 1) e.preventDefault(); });
        p.addEventListener("pointermove", e => { if (arr) { const [x, y] = fr(e); arr.style.left = x * 100 + "%"; arr.style.top = y * 100 + "%"; return; }
          if (!pan) return; const dx = e.clientX - pan.x0, dy = e.clientY - pan.y0; if (Math.abs(dx) + Math.abs(dy) > 4) pan.moveu = true;
          if (pan.moveu && st.z > 1) { st.x = pan.sx + dx; st.y = pan.sy + dy; fecharPop(); aplica(); p.classList.add("movendo"); } });
        p.addEventListener("pointerup", e => { p.classList.remove("movendo");
          if (arr) { v.dados.linhas[+arr.dataset.i][lado] = fr(e); arr = null; salvarLinhas(); return; }
          const clique = pan && !pan.moveu; pan = null; if (!clique || ro() || armado == null) return;
          if (modo === "digitar") return abrirPop(lado, p, z, fr(e), e, true);
          /* só marcar: põe o número e passa para a próxima linha */
          const i = armado, l = v.dados.linhas[i]; desfazer.push({ i, lado, antes: l[lado] }); l[lado] = fr(e);
          z.querySelectorAll(`.psd-mk[data-i="${i}"]`).forEach(m => m.remove()); z.insertAdjacentHTML("beforeend", marca(l, i, lado)); salvarLinhas();
          armar(i + 1 < v.dados.linhas.length ? i + 1 : null);
          if (armado == null) TW.toast(`Última linha marcada no desenho ${LADO[lado]}. Para o outro desenho, clique em «Marcar no desenho» de novo.`, { tom: "info" }); });
        /* duplo clique num número: abre o valor daquela linha naquele desenho */
        p.addEventListener("dblclick", e => { const m = e.target.closest(".psd-mk"); if (!m || ro()) return; const i = +m.dataset.i; armar(i); abrirPop(lado, p, z, v.dados.linhas[i][lado], e, false); });
      });
      /* campo no ponto clicado: grava valor (e tolerâncias no PERFECT), põe o número no desenho e passa para a próxima linha */
      const abrirPop = (lado, p, z, pt, e, avanca = true) => { fecharPop(); const i = armado, l = v.dados.linhas[i], box = p.closest(".psd-vdes"), r = box.getBoundingClientRect(), k = lado === "pp" ? "p" : "f";
        pop = document.createElement("form"); pop.className = "psd-vpop"; pop.autocomplete = "off";          // fica no bloco do desenho (fora do recorte do papel)
        const x = Math.min(e.clientX - r.left + 14, r.width - 232), y = e.clientY - r.top + 14;
        Object.assign(pop.style, { left: Math.max(0, x) + "px", top: y + "px" });
        pop.innerHTML = `<div class="t"><span class="psd-num armado">${l.n}</span><b>${esc(l.nome)}</b><small>${LADO[lado]}</small></div>
          <label><span>Valor</span><input name="v" value="${esc(l[k] || "")}" placeholder="${lado === "pp" ? "553±3" : "552"}" required></label>
          ${lado === "pp" ? `<div class="dois"><label><span>Tol. +</span><input name="tm" value="${esc(l.tm || "")}"></label><label><span>Tol. −</span><input name="tn" value="${esc(l.tn || "")}"></label></div>` : ""}
          <div class="a"><button type="submit" class="psd-btn sm prim">Gravar</button><button type="button" class="psd-btn sm" data-fechar>Cancelar</button><small>Enter grava, Esc fecha</small></div>`;
        box.appendChild(pop); const iv = pop.querySelector("[name=v]"); iv.focus(); iv.select();
        const rp = pop.getBoundingClientRect(); if (rp.bottom > innerHeight - 8) pop.style.top = Math.max(0, y - rp.height - 28) + "px";          // sem espaço embaixo: abre acima do clique
        if (lado === "pp") iv.addEventListener("input", () => { const s = separa(iv.value); if (s.tm != null) { pop.querySelector("[name=tm]").value = s.tm; pop.querySelector("[name=tn]").value = s.tn; } });
        pop.addEventListener("keydown", ev => { if (ev.key === "Escape") { ev.preventDefault(); ev.stopPropagation(); fecharPop(); } });
        pop.querySelector("[data-fechar]").addEventListener("click", fecharPop);
        pop.addEventListener("submit", ev => { ev.preventDefault(); const s = separa(iv.value);
          l[k] = s.v; if (lado === "pp") { l.tm = (pop.querySelector("[name=tm]").value || "").trim(); l.tn = (pop.querySelector("[name=tn]").value || "").trim(); const t = numv(l.tn); if (t != null && t > 0) l.tn = "-" + l.tn; }
          if (String(l[lado]) !== String(pt)) desfazer.push({ i, lado, antes: l[lado] });
          l[lado] = pt; melhoria(l); atualiza(i);
          z.querySelectorAll(`.psd-mk[data-i="${i}"]`).forEach(m => m.remove()); z.insertAdjacentHTML("beforeend", marca(l, i, lado));
          fecharPop(); salvarLinhas();
          if (!avanca) return armar(null);
          armar(i + 1 < v.dados.linhas.length ? i + 1 : null);
          if (armado == null) TW.toast(`Última linha no desenho ${LADO[lado]}. Para continuar, clique em «Marcar no desenho».`, { tom: "info" }); });
      };
      esc3 = () => { if (!el.contains(c)) return false; if (pop) { fecharPop(); return true; }
        const ch = document.querySelector(".psd-vdes.cheio"); if (ch) { ch.querySelector('[data-z="cheia"]').click(); return true; } return false; };
      const ler = c.querySelector("[data-ler]");
      if (ler) ler.addEventListener("click", async () => {
        if (v.leitura_em && !(await TW.confirmar({ titulo: "Ler os desenhos de novo?", texto: "As linhas que você já conferiu ficam como estão; as outras são substituídas pela nova leitura.", botao: "Ler de novo" }))) return;
        ler.disabled = true; ler.innerHTML = `${ico("loader-circle", "sm psd-gira")}Lendo os desenhos…`;
        try { clearTimeout(timer); const r = await JS(`/${vid}/ler`, "POST"); v = r; redesenharTopo(); corpo(); TW.toast(`${nf(r.lidas || 0)} medida(s) lida(s). Confira cada linha antes de concluir.`, { titulo: "Leitura concluída" }); }
        catch (e) { TW.erro(e); ler.disabled = false; ler.innerHTML = `${ico("sparkles", "sm")}${v.leitura_em ? "Ler de novo" : "Ler medidas com o Claude"}`; } });
      const mais = c.querySelector("[data-mais]");
      if (mais) mais.addEventListener("click", () => { v.dados.linhas.push({ n: v.dados.linhas.length + 1, nome: "NOVA MEDIDA", p: "", f: "", tm: "", tn: "", melhoria: "", conferida: false, lida: false, pp: null, pf: null, obs: "", extra: true }); salvar({ linhas: v.dados.linhas }, true); });
      const ca = c.querySelector("[data-confa]");
      if (ca) ca.addEventListener("click", () => { let n = 0; v.dados.linhas.forEach(l => { if (usada(l) && ap(l) === "A" && !l.conferida) { l.conferida = true; n++; } }); salvar({ linhas: v.dados.linhas }, true); TW.toast(`${nf(n)} linha(s) marcada(s) como conferida(s).`); });
    };

    /* ---------- sobrepor os dois desenhos (etapa 24, sem API) ----------
       PERFECT em vermelho, fornecedor em azul; onde as linhas coincidem fica escuro. Alinha pelos números marcados nos dois desenhos (escala e posição por
       mínimos quadrados, 2 ou mais linhas); arrastar move o desenho do fornecedor, a roda muda o tamanho dele. Não lê números: mostra onde os desenhos diferem. */
    const sobrepor = async () => {
      const carrega = s => new Promise((ok, er) => { const im = new Image(); im.onload = () => ok(im); im.onerror = () => er(new Error("Não foi possível abrir os desenhos.")); im.src = s; });
      let a, b; try { [a, b] = await Promise.all([carrega(src(imgPerfect())), carrega(src("fornecedor"))]); } catch (e) { return TW.erro(e); }
      const tinge = (im, cor) => { const cv = document.createElement("canvas"); cv.width = im.naturalWidth; cv.height = im.naturalHeight; const x = cv.getContext("2d"); x.drawImage(im, 0, 0);
        const d = x.getImageData(0, 0, cv.width, cv.height), p = d.data;
        for (let k = 0; k < p.length; k += 4) { const tinta = 255 - (p[k] + p[k + 1] + p[k + 2]) / 3; p[k] = cor[0]; p[k + 1] = cor[1]; p[k + 2] = cor[2]; p[k + 3] = tinta < 40 ? 0 : Math.min(255, tinta * 1.6); }
        x.putImageData(d, 0, 0); return cv; };
      const A = tinge(a, [220, 38, 38]), B = tinge(b, [37, 99, 235]);
      const pares = v.dados.linhas.filter(l => l.pp && l.pf).map(l => [[l.pp[0] * A.width, l.pp[1] * A.height], [l.pf[0] * B.width, l.pf[1] * B.height]]);
      let t = { s: A.width / B.width, x: 0, y: 0 };
      const alinha = () => { const n = pares.length; if (n < 2) return false;
        const m = i => [pares.reduce((s, q) => s + q[i][0], 0) / n, pares.reduce((s, q) => s + q[i][1], 0) / n], mp = m(0), mf = m(1); let num = 0, den = 0;
        pares.forEach(([P, F]) => { const fx = F[0] - mf[0], fy = F[1] - mf[1]; num += (P[0] - mp[0]) * fx + (P[1] - mp[1]) * fy; den += fx * fx + fy * fy; });
        const s = den ? num / den : t.s; if (!(s > 0.2 && s < 5)) return false; t = { s, x: mp[0] - s * mf[0], y: mp[1] - s * mf[1] }; return true; };
      const auto = alinha();
      const box = document.createElement("div"); box.className = "psd-vsob"; box.setAttribute("role", "dialog"); box.setAttribute("aria-label", "Desenhos sobrepostos");
      box.innerHTML = `<div class="h"><b>Desenhos sobrepostos</b><span class="leg"><i class="r"></i>só no PERFECT</span><span class="leg"><i class="a"></i>só no fornecedor</span><span class="leg"><i class="e"></i>nos dois</span>
          <span class="ml-auto flex flex-wrap gap-1.5"><button type="button" class="psd-btn sm" data-al ${pares.length < 2 ? "disabled title=\"Marque 2 ou mais linhas nos dois desenhos\"" : ""}>Alinhar pelos números</button>
          <button type="button" class="psd-btn sm" data-sc="1.02">Fornecedor maior</button><button type="button" class="psd-btn sm" data-sc="0.98">Fornecedor menor</button><button type="button" class="psd-btn sm" data-fim>Fechar</button></span></div>
        <p class="d">${auto ? `Alinhado por ${nf(pares.length)} números marcados nos dois desenhos.` : pares.length >= 2 ? "Os números marcados não dão um alinhamento coerente (confira se marcam a mesma cota nos dois desenhos)." : "Marque 2 ou mais linhas nos dois desenhos para alinhar sozinho."} Arraste para mover o desenho do fornecedor; a roda do mouse muda o tamanho dele.</p>
        <div class="cv"><canvas></canvas></div>`;
      document.body.appendChild(box); document.body.classList.add("psd-vcheio");
      const cv = box.querySelector("canvas"), x = cv.getContext("2d"); cv.width = A.width; cv.height = A.height;
      const pinta = () => { x.globalCompositeOperation = "source-over"; x.fillStyle = "#fff"; x.fillRect(0, 0, cv.width, cv.height); x.drawImage(A, 0, 0);
        x.globalCompositeOperation = "multiply"; x.drawImage(B, t.x, t.y, B.width * t.s, B.height * t.s); x.globalCompositeOperation = "source-over"; };
      pinta();
      const k = () => cv.width / cv.getBoundingClientRect().width;
      const fim = () => { box.remove(); document.body.classList.remove("psd-vcheio"); document.removeEventListener("keydown", tecla, true); };
      const tecla = e => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); fim(); } };
      document.addEventListener("keydown", tecla, true);
      let arr = null;
      cv.addEventListener("pointerdown", e => { arr = { x0: e.clientX, y0: e.clientY, tx: t.x, ty: t.y }; cv.setPointerCapture(e.pointerId); });
      cv.addEventListener("pointermove", e => { if (!arr) return; t.x = arr.tx + (e.clientX - arr.x0) * k(); t.y = arr.ty + (e.clientY - arr.y0) * k(); pinta(); });
      cv.addEventListener("pointerup", () => { arr = null; });
      const escala = (f, cx, cy) => { t.x = cx - (cx - t.x) * f; t.y = cy - (cy - t.y) * f; t.s *= f; pinta(); };
      cv.addEventListener("wheel", e => { e.preventDefault(); const r = cv.getBoundingClientRect(); escala(e.deltaY < 0 ? 1.02 : 0.98, (e.clientX - r.left) * k(), (e.clientY - r.top) * k()); }, { passive: false });
      box.addEventListener("click", e => { if (e.target.closest("[data-fim]")) fim(); if (e.target.closest("[data-al]")) { alinha(); pinta(); }
        const sc = e.target.closest("[data-sc]"); if (sc) escala(+sc.dataset.sc, cv.width / 2, cv.height / 2); });
    };

    /* ---------- passo 4: revisão e aprovação ---------- */
    const passo4 = () => { const c = conta(v.dados.linhas), dm = v.dados.damping, dis = ro() ? "disabled" : "", falta = c.linhas - c.conferidas;
      const lin = (g, lado, rot) => `<tr><td>${rot}</td>${[0, 1, 2, 3, 4].map(j => `<td><input class="r" data-dg="${g}" data-dl="${lado}" data-dj="${j}" value="${esc(dm[lado][g][j] || "")}" ${dis} aria-label="${rot} ${VEL[j]} m/s"></td>`).join("")}${lado === "p" ? `<td class="c" rowspan="2" data-dap="${g}">${apTag(apDamp(dm.p[g], dm.f[g], v.damping_regra))}</td>` : ""}</tr>`;
      return `<div class="psd-vrev"><section><h3>Damping force</h3>
          <div class="psd-vtab-w"><table class="psd-vtab"><thead><tr><th>F (N)</th>${VEL.map(x => `<th class="r">${x}</th>`).join("")}<th class="c">Ap</th></tr></thead>
          <tbody>${lin("pf", "p", "Pf PERFECT")}${lin("pf", "f", "Pf fornecedor")}${lin("py", "p", "Py PERFECT")}${lin("py", "f", "Py fornecedor")}</tbody></table></div>
          <p class="psd-vdica">Valores nominais em N, por velocidade (m/s).</p>
          ${v.imagens.perfect || v.imagens.fornecedor ? `<div class="psd-vrecs"><div class="psd-rot">Imagens da aba de damping do F-008</div>
            <p class="psd-vdica">Arraste sobre a tabela de damping de cada desenho e use «Manter só a seleção»; sem recorte, vai o desenho inteiro.</p>
            <div class="psd-vrecs-g">${["pp", "pf"].filter(k => v.imagens[k === "pp" ? "perfect" : "fornecedor"]).map(k => { const r = (v.dados.recorte || {})[k];
              return `<div class="psd-vrec"><div class="tt"><b>${k === "pp" ? "PERFECT" : "Fornecedor"}</b><span>${r ? "só a tabela" : "desenho inteiro"}</span></div>
                <div class="psd-papel psd-masc" data-recp="${k}" tabindex="0"><img alt="" src="${src(k === "pp" ? imgPerfect() : "fornecedor")}">${r ? `<div class="psd-recorte" style="left:${r[0] * 100}%;top:${r[1] * 100}%;width:${r[2] * 100}%;height:${r[3] * 100}%"></div>` : ""}<div class="psd-sel" hidden></div></div>
                ${ro() ? "" : `<div class="a"><button type="button" class="psd-btn sm" data-recok="${k}">${ico("crop", "sm")}Manter só a seleção</button>${r ? `<button type="button" class="psd-btn sm" data-recx="${k}">Desenho inteiro</button>` : ""}</div>`}</div>`; }).join("")}</div></div>` : ""}</section>
        <section><h3>Conclusão</h3>
          <div class="psd-est psd-vconta"><button type="button" tabindex="-1"><span class="t">Aprovadas (A)</span><span class="n">${nf(c.A)}</span></button><button type="button" tabindex="-1" class="${c.R ? "red" : ""}"><span class="t">Reprovadas (R)</span><span class="n">${nf(c.R)}</span></button>
            <button type="button" tabindex="-1" class="${falta ? "amb" : ""}"><span class="t">Conferidas</span><span class="n">${nf(c.conferidas)}</span><span class="l">de ${nf(c.linhas)}</span></button></div>
          ${ro() ? "" : falta ? notice(`Faltam ${nf(falta)} linha(s) para conferir no passo 3.`, "amber") : ""}
          ${!ro() && v.dados.origem_par ? notice(`O outro lado, <b>${esc(v.dados.origem_par.code)} (${esc(v.dados.origem_par.lado)})</b>, foi ${v.dados.origem_par.decisao === "aprovada" ? "aprovado" : "reprovado"}. Conclua este lado com a mesma decisão, ou com outra se o desenho deste lado for diferente.`, "blue") : ""}
          ${ro() ? "" : `<div class="psd-vdecide"><button type="button" class="psd-btn ${(v.dados.origem_par || {}).decisao === "reprovada" ? "" : "prim"}" data-dec="aprovada" ${falta || !c.linhas ? "disabled" : ""}>${ico("circle-check", "sm")}Aprovar e gerar F-008</button><button type="button" class="psd-btn psd-vrepr${(v.dados.origem_par || {}).decisao === "reprovada" ? " forte" : ""}" data-dec="reprovada" ${falta || !c.linhas ? "disabled" : ""}>Reprovar e gerar F-008</button></div>`}
          ${ro() && v.par && v.par.validacao && v.par.validacao.status === "andamento" ? `<div class="psd-vaviso">${ico("arrow-left-right", "sm")}<span>O outro lado, <b>${esc(v.par.code)} (${esc(v.par.lado)})</b>, está pronto para concluir.</span><button type="button" class="psd-btn sm prim" data-irpar="${v.par.validacao.id}">Abrir ${esc(v.par.code)}</button></div>` : ""}
          <div class="psd-varq">
            ${["xlsx", "pdf"].map(t => ro() && v[t] ? `<a href="/api/validacao/${vid}/arquivo/${t}" class="psd-varq-l"><span class="ext ${t}">${t.toUpperCase()}</span><span>${esc(v[t])}</span>${ico("download", "sm")}</a>`
              : `<div class="psd-varq-l mudo"><span class="ext ${t}">${t.toUpperCase()}</span><span>${esc(v.nome_f008)}.${t}</span></div>`).join("")}
            <div class="text-sm text-mute">${ro() ? (v.status === "aprovada" ? (v.drawing_file_id ? `Desenho do fornecedor enviado para <a class="font-semibold text-blue-600" href="/desenhos?open=${encodeURIComponent(v.code)}">Desenhos</a>.` : "") : "Reprovada: o desenho não foi para Desenhos.") : `Ao aprovar: o desenho do fornecedor vai para Desenhos como ${esc((v.kind === "rd" ? "RED" : "DES") + " - " + v.code + " - " + (v.supplier || "FORNECEDOR") + " - " + (v.supplier_code || "CÓDIGO") + " - REV.00")}.`}</div>
          </div>
          ${v.aviso ? notice(esc(v.aviso), "amber") : ""}
          ${ro() ? `<div class="psd-vdecide"><button type="button" class="psd-btn" data-nova>${ico("plus", "sm")}Nova revisão (Rev.${String((Math.max(...v.revisoes.map(r => r.revisao)) || 0) + 1).padStart(2, "0")})</button></div>` : ""}
          ${v.revisoes.length > 1 ? `<div class="psd-vrevs"><div class="psd-rot">Revisões desta validação</div>${v.revisoes.map(r => `<div class="${r.id === v.id ? "atual" : ""}">
              ${r.id === v.id ? `<b>Rev.${String(r.revisao).padStart(2, "0")}</b>` : `<a href="#" data-irpar="${r.id}">Rev.${String(r.revisao).padStart(2, "0")}</a>`}${badge(ST[r.status][0], ST[r.status][1])}<span class="text-mute">${r.concluida_em ? dmy(r.concluida_em) : dmy(r.updated_at)}</span>
              <span class="ml-auto flex gap-1.5">${r.xlsx ? `<a class="psd-vfile" href="/api/validacao/${r.id}/arquivo/xlsx">xlsx</a>` : ""}${r.pdf ? `<a class="psd-vfile" href="/api/validacao/${r.id}/arquivo/pdf">pdf</a>` : ""}</span></div>`).join("")}</div>` : ""}
        </section></div>`; };
    const ligar4 = c => {
      /* recorte da tabela de damping (etapa 24): arrastar seleciona; «Manter só a seleção» guarda; «Desenho inteiro» desfaz */
      const selRec = {};
      if (!ro()) c.querySelectorAll("[data-recp]").forEach(box => { const k = box.dataset.recp, sx = box.querySelector(".psd-sel");
        const fr = e => { const b = box.getBoundingClientRect(); return [Math.min(Math.max((e.clientX - b.left) / b.width, 0), 1), Math.min(Math.max((e.clientY - b.top) / b.height, 0), 1)]; };
        const mostra = () => { const s = selRec[k]; if (!s) { sx.hidden = true; return; } Object.assign(sx.style, { left: s[0] * 100 + "%", top: s[1] * 100 + "%", width: s[2] * 100 + "%", height: s[3] * 100 + "%" }); sx.hidden = false; };
        let ini = null;
        box.addEventListener("pointerdown", e => { if (e.button !== 0) return; box.setPointerCapture(e.pointerId); ini = fr(e); selRec[k] = [...ini, 0, 0]; mostra(); });
        box.addEventListener("pointermove", e => { if (!ini) return; const p = fr(e); selRec[k] = [Math.min(ini[0], p[0]), Math.min(ini[1], p[1]), Math.abs(p[0] - ini[0]), Math.abs(p[1] - ini[1])]; mostra(); });
        box.addEventListener("pointerup", () => { ini = null; const s = selRec[k]; if (s && (s[2] < 0.01 || s[3] < 0.01)) { selRec[k] = null; mostra(); } }); });
      c.querySelectorAll("[data-recok]").forEach(b => b.addEventListener("click", () => { const k = b.dataset.recok;
        if (!selRec[k]) return TW.toast("Arraste sobre a tabela de damping do desenho primeiro.", { tom: "aviso" }); salvar({ recorte: { [k]: selRec[k] } }, true); }));
      c.querySelectorAll("[data-recx]").forEach(b => b.addEventListener("click", () => salvar({ recorte: { [b.dataset.recx]: null } }, true)));
      /* damping: Enter vai para o valor ao lado (no fim da linha, o 1º da linha de baixo), Shift+Enter volta; colar vários números preenche a linha; «1155±365» guarda 1155 */
      const cels = [...c.querySelectorAll("[data-dg]")];
      const grava = i => { const dm = v.dados.damping; dm[i.dataset.dl][i.dataset.dg][+i.dataset.dj] = i.value;
        c.querySelector(`[data-dap="${i.dataset.dg}"]`).innerHTML = apTag(apDamp(dm.p[i.dataset.dg], dm.f[i.dataset.dg], v.damping_regra)); clearTimeout(timer); timer = setTimeout(() => salvar({ damping: dm }), 700); };
      const nominal = i => { if (i.value.includes("±")) { i.value = i.value.split("±")[0].trim(); grava(i); } };
      cels.forEach((i, k) => {
        i.addEventListener("input", () => grava(i));
        i.addEventListener("keydown", e => { if (e.key !== "Enter") return; e.preventDefault(); nominal(i); const prox = cels[k + (e.shiftKey ? -1 : 1)]; if (prox) { prox.focus(); prox.select(); } else i.blur(); });
        i.addEventListener("blur", () => nominal(i));
        i.addEventListener("paste", e => { const t = (e.clipboardData || window.clipboardData).getData("text"); const vals = t.split(/[\s;\t]+/).map(x => x.split("±")[0].trim()).filter(Boolean);
          if (vals.length < 2) return; e.preventDefault(); vals.forEach((x, n) => { const alvo = cels[k + n]; if (alvo && alvo.dataset.dl === i.dataset.dl && alvo.dataset.dg === i.dataset.dg) { alvo.value = x; grava(alvo); } }); });
      });
      c.querySelectorAll("[data-dec]").forEach(b => b.addEventListener("click", async () => { const ok = b.dataset.dec === "aprovada";
        if (!(await TW.confirmar({ titulo: ok ? "Aprovar o desenho e gerar o F-008?" : "Reprovar o desenho e gerar o F-008?", texto: `${v.nome_f008}.xlsx e .pdf`, botao: ok ? "Aprovar e gerar" : "Reprovar e gerar", perigo: !ok, icone: ok ? "circle-check" : "",
          nota: ok ? "O desenho do fornecedor vai para Desenhos. A validação fica fechada para edição." : "A validação fica fechada para edição; para validar de novo, abra uma nova validação." }))) return;
        b.disabled = true; b.innerHTML = `${ico("loader-circle", "sm psd-gira")}Gerando o F-008…`;
        try { clearTimeout(timer); v = await JS(`/${vid}/concluir`, "POST", { decisao: b.dataset.dec }); redesenharTopo(); corpo(); TW.toast(v.aviso || (ok ? "F-008 gerado e desenho enviado para Desenhos." : "F-008 gerado com a reprovação."), { tom: v.aviso ? "aviso" : "ok", titulo: ok ? "Validação aprovada" : "Validação reprovada" });
          const pp = v.par_preparado;          // item com lados: oferece o outro lado, já preenchido
          if (pp && await TW.confirmar({ titulo: `Validar também ${pp.code} (${pp.lado})?`, icone: "arrow-left-right", botao: `Abrir ${pp.code}`, cancelar: "Agora não",
            texto: `A bancada do outro lado já está com a família, as medidas, a conferência e as posições dos números${pp.perfect ? " e com o desenho PERFECT vigente dele" : ""}. Falta enviar o desenho do fornecedor deste lado (o código sai do nome do arquivo) e concluir.` })) irPara(pp.id); }
        catch (e) { TW.erro(e); corpo(); } }));
      const nv = c.querySelector("[data-nova]");
      if (nv) nv.addEventListener("click", async () => { try { const r = await JS(`/${vid}/nova`, "POST"); location.href = (o.base || location.pathname) + "?" + new URLSearchParams({ ...(o.params || {}), v: r.id }); } catch (e) { TW.erro(e); } });
    };

    el.addEventListener("click", e => { const b = e.target.closest("[data-passo]"); if (b && el.contains(b)) ir(+b.dataset.passo);
      const pr = e.target.closest("[data-irpar]"); if (pr) { e.preventDefault(); irPara(pr.dataset.irpar); }
      if (e.target.closest("[data-excluir]")) excluir(); });
    /* excluir qualquer revisão (etapa 24): some o registro e os arquivos dela; o desenho já enviado para Desenhos fica */
    const excluir = async () => {
      const outras = v.revisoes.filter(r => r.id !== v.id);
      if (!(await TW.confirmar({ titulo: `Excluir ${v.code} Rev.${String(v.revisao).padStart(2, "0")}?`, botao: "Excluir", perigo: true,
        texto: `Somem as medidas, os desenhos desta validação${v.xlsx ? " e o F-008 (xlsx e pdf)" : ""}.${v.drawing_file_id ? " O desenho do fornecedor que ela enviou para Desenhos fica lá." : ""}${outras.length ? ` As outras ${outras.length} revisão(ões) continuam.` : ""}`,
        nota: "Não dá para desfazer." }))) return;
      try { await J(`/api/validacao/${vid}`, { method: "DELETE" }); TW.toast(`${v.code} Rev.${String(v.revisao).padStart(2, "0")} excluída.`);
        if (outras.length) irPara(outras[0].id); else location.href = o.voltar || "/validacao"; } catch (e) { TW.erro(e); } };
    document.addEventListener("keydown", e => { if (!el.isConnected) return;          // bancada que saiu da tela (troca de aba sem recarregar) não responde mais
      if (passo === 2 && tecla3 && tecla3(e)) return; if (e.key !== "Escape") return; if (esc3 && esc3()) return;          // Esc: fecha o campo, depois a tela cheia, depois para a digitação
      if (armado != null && passo === 2) { const b = el.querySelector("[data-parar]"); if (b) b.click(); } });
    el.innerHTML = TW.esqueleto(8);
    J(`/api/validacao/${vid}`).then(r => { v = r; passo = inicial(); desenhar(); }).catch(e => { el.innerHTML = notice(esc(e.message), "red"); });
  }
  const _J = J;          // leitura simples (GET)

  /* ======================= aba «Validar itens» do Redesenvolvimento ======================= */
  function abasRD(atual, n) {
    return `<div class="psd-seg" role="tablist" aria-label="Abas do Redesenvolvimento"><button type="button" data-aba="itens" aria-pressed="${atual === "itens"}">Itens</button><button type="button" data-aba="validar" aria-pressed="${atual === "validar"}">Validar itens${n != null ? ` <span class="psd-vn">${nf(n)}</span>` : ""}</button></div>`;
  }
  /* etapa 24: trocar de aba não recarrega a página — a tela é redesenhada e o destaque da chave desliza (tw.js); Voltar do navegador também troca */
  let voltarLigado = false;
  function ligarAbas(el) {
    el.addEventListener("click", e => { const b = e.target.closest("[data-aba]"); if (!b || b.getAttribute("aria-pressed") === "true") return;
      history.pushState(null, "", "/redesenvolvimento" + (b.dataset.aba === "validar" ? "?aba=validar" : "")); PSD.pages.redesenvolvimento(); scrollTo(0, 0); });
    if (!voltarLigado) { voltarLigado = true; addEventListener("popstate", () => { if (location.pathname === "/redesenvolvimento") PSD.pages.redesenvolvimento(); }); }
  }

  function abaRD() {
    const u = new URLSearchParams(location.search), vid = u.get("v");
    root.innerHTML = `<div class="flex flex-col gap-5"><div id="vabas">${abasRD("validar")}</div><div id="vconteudo"></div></div>`; ligarAbas($("#vabas"));
    const alvo = $("#vconteudo");
    if (vid) return bancada(alvo, +vid, { voltar: "/redesenvolvimento?aba=validar", base: "/redesenvolvimento", params: { aba: "validar" } });
    let q = u.get("q") || "", timer;
    alvo.innerHTML = `<div id="vbar"></div><div id="vmeta" class="mb-2 text-sm text-mute"></div><div id="vlista">${TW.esqueleto(6)}</div>`;
    const barra = () => TW.pintarBarra($("#vbar"), { busca: { valor: q, ph: "Buscar outro item de Redesenvolvimento: código, descrição, veículo…" } });
    const tom = st => /REPROVAD/.test(st) ? "no" : /FINALIZAD|CONCLU|APROVAD/.test(st) ? "ok" : "";
    const carregar = async () => {
      try {
        const d = await _J("/api/validacao/aba/rd?" + new URLSearchParams(q ? { q } : {}));
        $("#vabas").innerHTML = abasRD("validar", d.pendentes);
        $("#vmeta").innerHTML = q ? `<b class="text-ink">${nf(d.total)}</b> item(ns) em andamento com «${esc(q)}»` : `<b class="text-ink">${nf(d.total)}</b> item(ns) pendente(s) de validação no servidor`;
        $("#vlista").innerHTML = TW.table([{ h: "Código" }, { h: "Descrição" }, { h: "Veículo(s)" }, { h: "Fornecedor" }, { h: "Validação no app" }, { h: "" }, { h: "Sub status do servidor", nw: false }],
          d.rows.map(r => { const x = r.validacao, subs = [...new Map((r.subs || []).map(s => [s.v, s])).values()];
            return [`<a href="#" class="font-semibold text-blue-600" data-rd="rd" data-code="${esc(r.code)}">${esc(r.code)}</a>`, `<span class="block max-w-[16rem] truncate" title="${esc(r.description || "")}">${esc(r.description || "")}</span>`,
              `<span class="block max-w-[12rem] truncate" title="${esc(r.vehicles || "")}">${esc((r.vehicles || "–").replace(/ · /g, ", "))}</span>`, esc((r.suppliers || "–").replace(/ · /g, ", ")),
              x ? badge(x.status === "andamento" ? `Em andamento, ${nf(x.conferidas)} de ${nf(x.linhas)}` : x.status_label, ST[x.status][1]) : badge("Não iniciada", "slate"),
              x && x.status === "andamento" ? `<button type="button" class="psd-btn sm" data-abrir="${x.id}">Continuar</button>` : x ? `<button type="button" class="psd-btn sm" data-abrir="${x.id}">Abrir</button>` : `<button type="button" class="psd-btn sm prim" data-iniciar="${esc(r.code)}">Iniciar validação</button>`,
              subs.length ? `<div class="psd-sublist">${subs.map(s => `<span><i class="psd-sd ${tom(s.v)}"></i>${esc(s.v)}</span>`).join("")}</div>` : '<span class="text-mute">–</span>']; }),
          { h: "max-h-[65vh]" });
      } catch (e) { $("#vlista").innerHTML = notice(esc(e.message), "red"); }
    };
    TW.ligarBarra($("#vbar"), { set: () => { }, busca: t => { q = t; history.replaceState(null, "", "/redesenvolvimento?" + new URLSearchParams(q ? { aba: "validar", q } : { aba: "validar" })); carregar(); }, limpar: () => { q = ""; barra(); carregar(); } });
    $("#vlista").addEventListener("click", async e => { const a = e.target.closest("[data-abrir]"), i = e.target.closest("[data-iniciar]");
      if (a) location.href = "/redesenvolvimento?aba=validar&v=" + a.dataset.abrir;
      if (i) { i.disabled = true; try { const r = await JS("", "POST", { kind: "rd", code: i.dataset.iniciar }); location.href = "/redesenvolvimento?aba=validar&v=" + r.id; } catch (er) { TW.erro(er); i.disabled = false; } } });
    barra(); carregar();
  }

  /* ======================= tela «Validação» do menu ======================= */
  function tela() {
    const vid = new URLSearchParams(location.search).get("v");
    if (vid) { root.innerHTML = '<div id="vconteudo"></div>'; return bancada($("#vconteudo"), +vid, { voltar: "/validacao", base: "/validacao" }); }
    const F = TW.filtros("validacao", ["q", "status", "supplier", "family", "kind"]); let d = null, timer;
    root.innerHTML = `<div class="flex flex-col gap-5"><section aria-label="Situação"><div id="vest" class="psd-est"></div></section><div id="vbar"></div><div id="vmeta" class="text-sm text-mute"></div><div id="vlista">${TW.esqueleto(6)}</div></div>`;
    const NOMES = { status: "Situação", supplier: "Fornecedor", family: "Família", kind: "Tipo", q: "Busca" }, TIPO = { rd: "Redesenvolvimento", des: "Desenvolvimento" };
    const val = (k, x) => k === "status" ? ST[x][0] : k === "family" ? FAM(x) : k === "kind" ? TIPO[x] : x;
    const est = (v, t, n, l, cls) => `<button type="button" data-est="${v}" class="${cls || ""}" aria-pressed="${(F.get().status || "") === v}"><span class="t">${t}</span><span class="n">${nf(n)}</span><span class="l">${l}</span></button>`;
    const desenhar = () => { const s = F.get(), c = d.counts;
      $("#vest").innerHTML = `<button type="button" data-pend class="${c.pendentes ? "amb" : ""}"><span class="t">Pendentes no R-D</span><span class="n">${nf(c.pendentes)}</span><span class="l">sem validação iniciada</span></button>` +
        est("andamento", "Em andamento", c.andamento, "rascunho salvo") + est("aprovada", "Aprovadas", c.aprovada, "desenho enviado a Desenhos", "fim") + est("reprovada", "Reprovadas", c.reprovada, "aguardando nova revisão", c.reprovada ? "red" : "");
      TW.pintarBarra($("#vbar"), { busca: { valor: s.q, ph: "Código, fornecedor, código do fornecedor…" },
        principais: [{ k: "supplier", rotulo: "Fornecedor", tipo: "lista", atual: s.supplier || "", opcoes: [{ v: "", l: "Todos" }, ...d.suppliers.map(x => ({ v: x, l: x }))] },
                     { k: "family", rotulo: "Família", tipo: "lista", atual: s.family || "", opcoes: [{ v: "", l: "Todas" }, ...d.familias.map(x => ({ v: x.v, l: x.l }))] },
                     { k: "kind", rotulo: "Tipo", tipo: "lista", atual: s.kind || "", opcoes: [{ v: "", l: "Todos" }, { v: "rd", l: TIPO.rd }, { v: "des", l: TIPO.des }] }],
        etiquetas: TW.etiquetas(s, NOMES, val), acoes: TW.botao("Baixar Excel", { href: `/api/export/validacao.xlsx?${new URLSearchParams(s)}`, icone: "download" }) });
      const ativos = Object.keys(s).length;
      $("#vmeta").innerHTML = `<b class="text-ink">${nf(d.total)}</b> validação(ões)${ativos ? `, ${ativos} filtro(s) ativo(s)` : ""}`;
      $("#vlista").innerHTML = d.rows.length || ativos ? TW.table([{ h: "Código" }, { h: "Descrição" }, { h: "Fornecedor" }, { h: "Cód. fornecedor" }, { h: "Família" }, { h: "Medidas", r: true }, { h: "Situação" }, { h: "Atualizada" }, { h: "Arquivos" }],
        d.rows.map(r => [`<a class="font-semibold text-blue-600" href="/validacao?v=${r.id}">${esc(r.code)}</a>${r.revisao || r.n_revisoes > 1 ? ` <span class="psd-vrevn" title="${nf(r.n_revisoes)} revisão(ões)">Rev.${String(r.revisao).padStart(2, "0")}</span>` : ""}`, `<span class="block max-w-[18rem] truncate" title="${esc(r.description || "")}">${esc(r.description || "–")}</span>`,
          esc(r.supplier || "–"), esc(r.supplier_code || "–"), esc(FAM(r.family) || "–"), r.conta.linhas ? `${nf(r.conta.conferidas)} de ${nf(r.conta.linhas)}` : '<span class="text-mute">–</span>', badge(r.status_label, ST[r.status][1]), dmy(r.updated_at),
          r.xlsx || r.pdf ? `<span class="inline-flex gap-1.5">${r.xlsx ? `<a class="psd-vfile" href="/api/validacao/${r.id}/arquivo/xlsx">xlsx</a>` : ""}${r.pdf ? `<a class="psd-vfile" href="/api/validacao/${r.id}/arquivo/pdf">pdf</a>` : ""}</span>` : '<span class="text-mute">–</span>']), { h: "max-h-[65vh]" })
        : empty(`Nenhuma validação ainda. Comece pelos itens pendentes em <a class="font-semibold text-blue-600" href="/redesenvolvimento?aba=validar">Redesenvolvimento, aba «Validar itens»</a>.`);
    };
    const carregar = async () => { try { d = await _J("/api/validacao?" + new URLSearchParams(F.get())); desenhar(); } catch (e) { fail(e); } };
    const aplicar = (patch, logo) => { F.set(patch); clearTimeout(timer); timer = setTimeout(carregar, logo ? 0 : 250); };
    TW.ligarBarra($("#vbar"), { set: (k, x) => aplicar({ [k]: x }, true), busca: t => aplicar({ q: t }, true), limpar: () => { F.clear(); carregar(); } });
    $("#vest").addEventListener("click", e => { if (e.target.closest("[data-pend]")) { location.href = "/redesenvolvimento?aba=validar"; return; }
      const b = e.target.closest("[data-est]"); if (b) aplicar({ status: F.get().status === b.dataset.est ? "" : b.dataset.est }, true); });
    carregar();
  }

  PSD.validacao = { bancada, abaRD, abasRD, ligarAbas };
  PSD.tela("validacao", tela);
})();
