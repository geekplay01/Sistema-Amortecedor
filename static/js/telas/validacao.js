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
    let v = null, passo = null, armado = null, timer = null, sel = null, base = null;
    const ro = () => v.status !== "andamento";
    const src = n => `/api/validacao/${vid}/img/${n}.png?u=${encodeURIComponent(v.updated_at || "")}`;
    const imgPerfect = () => v.imagens.perfect_limpo ? "perfect_limpo" : "perfect";
    const PASSOS = ["Desenhos", "Família", "Medidas", "Revisão e aprovação"];
    const sub = i => { const c = conta(v.dados.linhas);
      return [v.imagens.perfect && v.imagens.fornecedor ? (v.dados.mascara.length ? "máscara limpa" : "PERFECT e fornecedor") : "falta enviar", FAM(v.family) || "modelo F-008",
              c.linhas ? `${nf(c.conferidas)} de ${nf(c.linhas)} conferidas` : "leitura e conferência", ro() ? ST[v.status][0] : "F-008 em xlsx e pdf"][i]; };
    const feito = i => { const c = conta(v.dados.linhas); return [v.imagens.perfect && v.imagens.fornecedor, !!v.family, c.linhas > 0 && c.conferidas === c.linhas, ro()][i]; };
    const inicial = () => ro() ? 3 : !(v.imagens.perfect && v.imagens.fornecedor) ? 0 : !v.family ? 1 : 2;

    const topo = () => `<div class="psd-banc-top">
        ${o.voltar ? `<a class="psd-vvolta" href="${o.voltar}">${ico("chevron-right", "sm")}<span>Voltar à lista</span></a>` : ""}
        <span class="id">${esc(v.code)}</span><span class="desc">${esc([v.info.description, v.info.vehicle].filter(Boolean).join(", "))}</span>
        <dl class="psd-par"><div><dt>Fornecedor</dt><dd>${esc(v.supplier || "–")}</dd></div><div><dt>Cód. fornecedor</dt><dd>${esc(v.supplier_code || "–")}</dd></div>
          <div><dt>Família</dt><dd>${esc(FAM(v.family) || "–")}</dd></div><div><dt>Tipo</dt><dd>${esc(FAM(v.kind_label))}</dd></div></dl>
        <span class="dir">${badge(ST[v.status][0], ST[v.status][1])}<span id="vsalvo" class="text-xs text-mute">${ro() ? "concluída em " + dmy(v.concluida_em) : v.updated_at ? "rascunho salvo " + String(v.updated_at).slice(11, 16) : ""}</span></span></div>
      <div class="psd-passos" role="tablist">${PASSOS.map((t, i) => `<button type="button" role="tab" data-passo="${i}" aria-selected="${i === passo}" class="${feito(i) ? "feito" : ""}">${i + 1} · ${t}<small>${esc(sub(i))}</small></button>`).join("")}</div>`;
    const redesenharTopo = () => { const t = $("#vtopo", el); if (t) t.innerHTML = topo(); };
    const desenhar = () => { el.innerHTML = `<div class="psd-banc"><div id="vtopo">${topo()}</div><div id="vbc"></div></div>`; corpo(); };
    const corpo = () => { const c = $("#vbc", el); c.innerHTML = [passo1, passo2, passo3, passo4][passo](); [ligar1, ligar2, ligar3, ligar4][passo](c); };
    const ir = i => { passo = i; redesenharTopo(); corpo(); };
    const salvar = async (b, redesenha = false) => { try { v = await JS(`/${vid}`, "PATCH", b); redesenharTopo(); if (redesenha) corpo(); } catch (e) { TW.erro(e); } };
    const salvarLinhas = () => { clearTimeout(timer); timer = setTimeout(() => salvar({ linhas: v.dados.linhas }), 700); };
    const rodape = (prox, txt) => prox == null ? "" : `<div class="psd-vrodape"><button type="button" class="psd-btn" data-ir="${prox}">${esc(txt)}${ico("chevron-right", "sm")}</button></div>`;
    const drop = (lado, rot) => ro() ? empty("Sem desenho.") : `<label class="psd-drop" data-drop="${lado}">${ico("upload", "lg")}<b>Enviar ${esc(rot)}</b><span>PDF, PNG ou JPG; arraste o arquivo para cá ou clique</span><input type="file" accept=".pdf,.png,.jpg,.jpeg,.bmp,.webp" data-up="${lado}" hidden></label>`;
    const trocar = lado => ro() ? "" : `<label class="psd-btn sm">${ico("upload", "sm")}Trocar arquivo<input type="file" accept=".pdf,.png,.jpg,.jpeg,.bmp,.webp" data-up="${lado}" hidden></label>`;
    const enviar = async (lado, f) => { if (!f) return; const fd = new FormData(); fd.append("file", f);
      try { v = await TW.enviar(`/api/validacao/${vid}/desenho/${lado}`, fd, [f]); redesenharTopo(); corpo(); TW.toast(lado === "perfect" ? "Desenho PERFECT enviado." : "Desenho do fornecedor enviado."); } catch (e) { TW.erro(e); } };
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
        ${f ? `<div class="psd-vlista"><div class="psd-rot">Medidas do modelo, na ordem do F-008</div><ol>${f.medidas.map(m => `<li>${esc(m)}</li>`).join("")}</ol></div>` : empty("Escolha a família para ver as medidas do modelo.")}
      </div>${rodape(v.family ? 2 : null, "Próximo: medidas")}`; };
    const ligar2 = c => { ligarEnvio(c);
      c.querySelectorAll("[data-fam]").forEach(b => b.addEventListener("click", async () => { const nova = b.dataset.fam; if (nova === v.family) return;
        if (v.family && conta(v.dados.linhas).linhas && !(await TW.confirmar({ titulo: `Trocar para ${FAM(nova)}?`, texto: "As medidas com o mesmo nome guardam os valores; as que não existem no outro modelo saem da tabela.", botao: "Trocar a família" }))) return;
        salvar({ family: nova }, true); })); };

    /* ---------- passo 3: medidas ---------- */
    const marca = (l, i, lado) => l[lado] && usada(l) ? `<span class="psd-mk" data-i="${i}" style="left:${l[lado][0] * 100}%;top:${l[lado][1] * 100}%" title="${esc(l.n + " " + l.nome)}">${l.n}</span>` : "";
    const marcas = lado => v.dados.linhas.map((l, i) => marca(l, i, lado)).join("");
    const linha = (l, i) => { const dis = ro() ? "disabled" : "", a = ap(l);
      return `<tr data-i="${i}">
        <td><button type="button" class="psd-num${armado === i ? " armado" : ""}" data-arma="${i}" ${dis} title="Marcar onde esta medida fica nos desenhos">${l.n}</button></td>
        <td class="nome">${l.extra && !ro() ? `<input data-k="nome" value="${esc(l.nome)}" aria-label="Nome da medida em inglês">` : `<span>${esc(l.nome)}</span>`}${l.obs ? `<small title="${esc(l.obs)}">${esc(l.obs)}</small>` : ""}</td>
        ${["p", "f", "tm", "tn"].map(k => `<td><input data-k="${k}" value="${esc(l[k] || "")}" class="r" ${dis} aria-label="${{ p: "PERFECT", f: "Fornecedor", tm: "Tolerância +", tn: "Tolerância −" }[k]}"></td>`).join("")}
        <td class="c" data-ap>${apTag(a)}</td>
        <td><input data-k="melhoria" value="${esc(l.melhoria || "")}" ${dis} aria-label="Melhoria (Improve)"></td>
        <td class="c"><input type="checkbox" data-k="conferida" ${l.conferida ? "checked" : ""} ${dis} aria-label="Conferida"></td>
        <td>${l.extra && !ro() ? `<button type="button" class="psd-vx" data-tira="${i}" aria-label="Tirar a medida">${ico("x", "sm")}</button>` : ""}</td></tr>`; };
    const passo3 = () => { const c = conta(v.dados.linhas), lida = v.leitura_em, podeLer = v.ia.ok && !ro() && v.imagens.perfect && v.imagens.fornecedor && v.family;
      return `<div class="psd-vmedidas"><div class="min-w-0">
        <div class="psd-vleit"><span class="info">${lida ? `<b>${nf(c.linhas)} medidas</b> lidas pelo Claude em ${dmy(lida)} às ${String(lida).slice(11, 16)}, <b>${nf(c.conferidas)}</b> conferidas` : c.linhas ? `<b>${nf(c.linhas)} medidas</b>, <b>${nf(c.conferidas)}</b> conferidas` : "Nenhuma medida lida ainda"}</span>
          ${ro() ? "" : `<span class="dir"><button type="button" class="psd-btn sm ${lida ? "" : "prim"}" data-ler ${podeLer ? "" : "disabled"}>${ico("sparkles", "sm")}${lida ? "Ler de novo" : "Ler medidas com o Claude"}</button>
            <button type="button" class="psd-btn sm" data-mais ${v.dados.linhas.length >= 25 ? "disabled" : ""}>${ico("plus", "sm")}Adicionar medida</button>
            ${c.linhas && lida ? `<button type="button" class="psd-btn sm" data-confa>${ico("check", "sm")}Conferir as que deram A</button>` : ""}</span>`}</div>
        ${!v.ia.ok && !ro() ? notice(`${esc(v.ia.motivo)} Enquanto isso, as medidas podem ser digitadas na tabela.`, "amber") : ""}
        ${v.dados.linhas.length ? `<div class="psd-vtab-w"><table class="psd-vtab"><thead><tr><th>Nº</th><th>Medida</th><th class="r">PERFECT</th><th class="r">Fornecedor</th><th class="r">Tol. +</th><th class="r">Tol. −</th><th class="c">Ap</th><th>Melhoria</th><th class="c">Conferida</th><th></th></tr></thead>
          <tbody>${v.dados.linhas.map(linha).join("")}</tbody></table></div>` : empty("Escolha a família no passo 2 para montar a tabela.")}
        ${ro() ? "" : `<p class="psd-vdica">Clique no número de uma linha e depois na cota, num dos desenhos, para marcar onde ela fica. Arraste um número para corrigir. Tolerância «OK» aprova e «N» reprova a linha, como no modelo.</p>`}
      </div>
      <div class="psd-vpilha">
        <div><h4>Desenho PERFECT<span>${v.dados.mascara.length ? "máscara limpa" : ""}</span></h4><div class="psd-papel" data-lado="pp">${v.imagens.perfect ? `<img alt="" src="${src(imgPerfect())}">${marcas("pp")}` : empty("Sem desenho.")}</div></div>
        <div><h4>Desenho do fornecedor<span>${esc([v.supplier, v.supplier_code].filter(Boolean).join(" "))}</span></h4><div class="psd-papel" data-lado="pf">${v.imagens.fornecedor ? `<img alt="" src="${src("fornecedor")}">${marcas("pf")}` : empty("Sem desenho.")}</div></div>
      </div></div>${rodape(3, "Próximo: revisão e aprovação")}`; };
    const ligar3 = c => {
      ligarEnvio(c);
      const foco = i => c.querySelectorAll(".psd-mk, .psd-vtab tr").forEach(x => x.classList.toggle("foco", i != null && x.dataset.i === String(i)));
      const tab = c.querySelector(".psd-vtab");
      if (tab) {
        tab.addEventListener("mouseover", e => { const tr = e.target.closest("tr[data-i]"); foco(tr ? tr.dataset.i : null); });
        tab.addEventListener("mouseleave", () => foco(null));
        tab.addEventListener("input", e => { const i = e.target.closest("[data-k]"); if (!i) return; const tr = i.closest("tr"), l = v.dados.linhas[+tr.dataset.i], k = i.dataset.k;
          if (k === "conferida") l.conferida = i.checked; else l[k] = i.value;
          if (["p", "f", "tm", "tn"].includes(k)) { const a = ap(l); tr.querySelector("[data-ap]").innerHTML = apTag(a); const m = tr.querySelector('[data-k="melhoria"]');
            if (a === "R" && !l.melhoria && l.p) { l.melhoria = `CHANGE TO ${l.p}`.toUpperCase(); m.value = l.melhoria; } else if (a !== "R" && /^CHANGE TO /.test(l.melhoria || "")) { l.melhoria = ""; m.value = ""; } }
          salvarLinhas(); });
        tab.addEventListener("click", e => { const b = e.target.closest("[data-arma]"), x = e.target.closest("[data-tira]");
          if (b) { armado = armado === +b.dataset.arma ? null : +b.dataset.arma; c.querySelectorAll("[data-arma]").forEach(y => y.classList.toggle("armado", +y.dataset.arma === armado)); c.querySelectorAll(".psd-papel[data-lado]").forEach(p => p.classList.toggle("armado", armado != null)); }
          if (x) { v.dados.linhas.splice(+x.dataset.tira, 1); v.dados.linhas.forEach((l, k) => l.n = k + 1); salvar({ linhas: v.dados.linhas }, true); } });
      }
      c.querySelectorAll(".psd-papel[data-lado]").forEach(p => {
        const lado = p.dataset.lado, fr = e => { const r = p.getBoundingClientRect(); return [Math.min(Math.max((e.clientX - r.left) / r.width, 0), 1), Math.min(Math.max((e.clientY - r.top) / r.height, 0), 1)]; };
        p.addEventListener("mouseover", e => { const m = e.target.closest(".psd-mk"); foco(m ? m.dataset.i : null); });
        if (ro()) return;
        let arr = null;
        p.addEventListener("pointerdown", e => { const m = e.target.closest(".psd-mk"); if (!m) return; e.preventDefault(); arr = m; p.setPointerCapture(e.pointerId); });
        p.addEventListener("pointermove", e => { if (!arr) return; const [x, y] = fr(e); arr.style.left = x * 100 + "%"; arr.style.top = y * 100 + "%"; });
        p.addEventListener("pointerup", e => { if (arr) { v.dados.linhas[+arr.dataset.i][lado] = fr(e); arr = null; salvarLinhas(); return; }
          if (armado == null || e.target.closest(".psd-mk")) return; const l = v.dados.linhas[armado]; l[lado] = fr(e);
          if (!usada(l)) return TW.toast("Preencha o valor da linha para o número aparecer no desenho.", { tom: "aviso" });
          p.querySelectorAll(`.psd-mk[data-i="${armado}"]`).forEach(x => x.remove()); p.insertAdjacentHTML("beforeend", marca(l, armado, lado)); salvarLinhas(); });
      });
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

    /* ---------- passo 4: revisão e aprovação ---------- */
    const passo4 = () => { const c = conta(v.dados.linhas), dm = v.dados.damping, dis = ro() ? "disabled" : "", falta = c.linhas - c.conferidas;
      const lin = (g, lado, rot) => `<tr><td>${rot}</td>${[0, 1, 2, 3, 4].map(j => `<td><input class="r" data-dg="${g}" data-dl="${lado}" data-dj="${j}" value="${esc(dm[lado][g][j] || "")}" ${dis} aria-label="${rot} ${VEL[j]} m/s"></td>`).join("")}${lado === "p" ? `<td class="c" rowspan="2" data-dap="${g}">${apTag(apDamp(dm.p[g], dm.f[g], v.damping_regra))}</td>` : ""}</tr>`;
      return `<div class="psd-vrev"><section><h3>Damping force</h3>
          <div class="psd-vtab-w"><table class="psd-vtab"><thead><tr><th>F (N)</th>${VEL.map(x => `<th class="r">${x}</th>`).join("")}<th class="c">Ap</th></tr></thead>
          <tbody>${lin("pf", "p", "Pf PERFECT")}${lin("pf", "f", "Pf fornecedor")}${lin("py", "p", "Py PERFECT")}${lin("py", "f", "Py fornecedor")}</tbody></table></div>
          <p class="psd-vdica">Valores nominais em N, por velocidade (m/s).</p></section>
        <section><h3>Conclusão</h3>
          <div class="psd-est psd-vconta"><button type="button" tabindex="-1"><span class="t">Aprovadas (A)</span><span class="n">${nf(c.A)}</span></button><button type="button" tabindex="-1" class="${c.R ? "red" : ""}"><span class="t">Reprovadas (R)</span><span class="n">${nf(c.R)}</span></button>
            <button type="button" tabindex="-1" class="${falta ? "amb" : ""}"><span class="t">Conferidas</span><span class="n">${nf(c.conferidas)}</span><span class="l">de ${nf(c.linhas)}</span></button></div>
          ${ro() ? "" : falta ? notice(`Faltam ${nf(falta)} linha(s) para conferir no passo 3.`, "amber") : ""}
          ${ro() ? "" : `<div class="psd-vdecide"><button type="button" class="psd-btn prim" data-dec="aprovada" ${falta || !c.linhas ? "disabled" : ""}>${ico("circle-check", "sm")}Aprovar e gerar F-008</button><button type="button" class="psd-btn psd-vrepr" data-dec="reprovada" ${falta || !c.linhas ? "disabled" : ""}>Reprovar e gerar F-008</button></div>`}
          <div class="psd-varq">
            ${["xlsx", "pdf"].map(t => ro() && v[t] ? `<a href="/api/validacao/${vid}/arquivo/${t}" class="psd-varq-l"><span class="ext ${t}">${t.toUpperCase()}</span><span>${esc(v[t])}</span>${ico("download", "sm")}</a>`
              : `<div class="psd-varq-l mudo"><span class="ext ${t}">${t.toUpperCase()}</span><span>${esc(v.nome_f008)}.${t}</span></div>`).join("")}
            <div class="text-sm text-mute">${ro() ? (v.status === "aprovada" ? (v.drawing_file_id ? `Desenho do fornecedor enviado para <a class="font-semibold text-blue-600" href="/desenhos?open=${encodeURIComponent(v.code)}">Desenhos</a>.` : "") : "Reprovada: o desenho não foi para Desenhos.") : `Ao aprovar: o desenho do fornecedor vai para Desenhos como ${esc((v.kind === "rd" ? "RED" : "DES") + " - " + v.code + " - " + (v.supplier || "FORNECEDOR") + " - " + (v.supplier_code || "CÓDIGO") + " - REV.00")}.`}</div>
          </div>
          ${v.aviso ? notice(esc(v.aviso), "amber") : ""}
          ${ro() ? `<div class="psd-vdecide"><button type="button" class="psd-btn" data-nova>${ico("plus", "sm")}Nova validação deste item</button></div>` : ""}
        </section></div>`; };
    const ligar4 = c => {
      c.querySelectorAll("[data-dg]").forEach(i => i.addEventListener("input", () => { const dm = v.dados.damping; dm[i.dataset.dl][i.dataset.dg][+i.dataset.dj] = i.value;
        c.querySelector(`[data-dap="${i.dataset.dg}"]`).innerHTML = apTag(apDamp(dm.p[i.dataset.dg], dm.f[i.dataset.dg], v.damping_regra)); clearTimeout(timer); timer = setTimeout(() => salvar({ damping: dm }), 700); }));
      c.querySelectorAll("[data-dec]").forEach(b => b.addEventListener("click", async () => { const ok = b.dataset.dec === "aprovada";
        if (!(await TW.confirmar({ titulo: ok ? "Aprovar o desenho e gerar o F-008?" : "Reprovar o desenho e gerar o F-008?", texto: `${v.nome_f008}.xlsx e .pdf`, botao: ok ? "Aprovar e gerar" : "Reprovar e gerar", perigo: !ok, icone: ok ? "circle-check" : "",
          nota: ok ? "O desenho do fornecedor vai para Desenhos. A validação fica fechada para edição." : "A validação fica fechada para edição; para validar de novo, abra uma nova validação." }))) return;
        b.disabled = true; b.innerHTML = `${ico("loader-circle", "sm psd-gira")}Gerando o F-008…`;
        try { clearTimeout(timer); v = await JS(`/${vid}/concluir`, "POST", { decisao: b.dataset.dec }); redesenharTopo(); corpo(); TW.toast(v.aviso || (ok ? "F-008 gerado e desenho enviado para Desenhos." : "F-008 gerado com a reprovação."), { tom: v.aviso ? "aviso" : "ok", titulo: ok ? "Validação aprovada" : "Validação reprovada" }); }
        catch (e) { TW.erro(e); corpo(); } }));
      const nv = c.querySelector("[data-nova]");
      if (nv) nv.addEventListener("click", async () => { try { const r = await JS(`/${vid}/nova`, "POST"); location.href = (o.base || location.pathname) + "?" + new URLSearchParams({ ...(o.params || {}), v: r.id }); } catch (e) { TW.erro(e); } });
    };

    el.addEventListener("click", e => { const b = e.target.closest("[data-passo]"); if (b && el.contains(b)) ir(+b.dataset.passo); });
    document.addEventListener("keydown", e => { if (e.key === "Escape" && armado != null) { armado = null; el.querySelectorAll(".armado").forEach(x => x.classList.remove("armado")); } });
    el.innerHTML = TW.esqueleto(8);
    J(`/api/validacao/${vid}`).then(r => { v = r; passo = inicial(); desenhar(); }).catch(e => { el.innerHTML = notice(esc(e.message), "red"); });
  }
  const _J = J;          // leitura simples (GET)

  /* ======================= aba «Validar itens» do Redesenvolvimento ======================= */
  function abasRD(atual, n) {
    return `<div class="psd-seg" role="tablist" aria-label="Abas do Redesenvolvimento"><button type="button" data-aba="itens" aria-pressed="${atual === "itens"}">Itens</button><button type="button" data-aba="validar" aria-pressed="${atual === "validar"}">Validar itens${n != null ? ` <span class="psd-vn">${nf(n)}</span>` : ""}</button></div>`;
  }
  function ligarAbas(el) { el.addEventListener("click", e => { const b = e.target.closest("[data-aba]"); if (!b) return; location.href = "/redesenvolvimento" + (b.dataset.aba === "validar" ? "?aba=validar" : ""); }); }

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
        d.rows.map(r => [`<a class="font-semibold text-blue-600" href="/validacao?v=${r.id}">${esc(r.code)}</a>`, `<span class="block max-w-[18rem] truncate" title="${esc(r.description || "")}">${esc(r.description || "–")}</span>`,
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
