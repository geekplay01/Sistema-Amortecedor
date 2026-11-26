/* Componentes de tela em TailwindCSS (cards, KPIs, tabelas com rolagem interna, selos).
   As cores vêm das variáveis do tema (claro/escuro): bg-card, border-line, text-ink, text-mute — o mesmo HTML serve aos dois temas. */
window.PSDTW = (() => {
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const nf = (v, d = 0) => v == null || isNaN(v) ? "–" : Number(v).toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });
  const brl = v => v == null || isNaN(v) ? "–" : Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  const brl0 = v => v == null || isNaN(v) ? "–" : Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
  const dmy = s => s ? String(s).slice(0, 10).split("-").reverse().join("/") : "–";
  const TONE = { blue: "bg-blue-500/15 text-blue-600", green: "bg-emerald-500/15 text-emerald-600", amber: "bg-amber-500/20 text-amber-700", red: "bg-red-500/15 text-red-600", violet: "bg-violet-500/15 text-violet-600", slate: "bg-slate-500/15 text-slate-600" };
  const badge = (t, tone = "slate") => `<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${TONE[tone] || TONE.slate}">${esc(t)}</span>`;
  /* ícone do arquivo único (static/img/icones.svg; lista em tools/icones.py): ico("amortecedor"), ico("ship", "lg") */
  const ico = (n, cls = "") => `<svg class="psd-ico ${cls}" aria-hidden="true"><use href="${window.PSD_ICONES || "/static/img/icones.svg"}#i-${n}"/></svg>`;
  const stripes = () => '<span class="psd-stripes" aria-hidden="true"><i></i><i></i><i></i><i></i></span>';
  /* KPI: rótulo, número grande em Barlow e a linha de apoio. Etapa 23: os KPIs vizinhos formam uma faixa única (marca.css); só alerta muda a cor do
     número (red = ruptura/erro, amber = risco; blue, green, slate e sky ficam neutros); na linha de apoio, cada « · » vira uma linha (uma informação por linha) */
  const kpi = (label, value, sub = "", accent = "blue", icone = "") => `<div class="psd-kpi acc-${accent}"><div class="kpi-top"><span class="kpi-label">${label}</span>${icone ? `<span class="text-mute">${ico(icone)}</span>` : ""}</div>
    <div class="kpi-val">${value}</div>${sub ? `<div class="kpi-sub">${String(sub).replace(/ · (?![^<]*>)/g, "<br>")}</div>` : ""}</div>`;
  const card = (title, body, right = "", cls = "") => `<section class="rounded-2xl border border-line bg-card p-5 shadow-sm ${cls}"><div class="mb-4 flex flex-wrap items-center justify-between gap-3"><h3 class="m-0 text-base font-semibold text-ink">${title}</h3>${right}</div>${body}</section>`;
  const notice = (t, tone = "blue") => `<div class="rounded-xl border px-4 py-3 text-sm ${{ blue: "border-blue-500/30 bg-blue-500/10 text-ink", amber: "border-amber-500/40 bg-amber-500/10 text-ink", red: "border-red-500/40 bg-red-500/10 text-ink" }[tone]}">${t}</div>`;
  const empty = t => `<div class="rounded-2xl border border-dashed border-line bg-card px-6 py-12 text-center text-sm text-mute">${t}</div>`;
  /* tabela minimalista: fundo do card, bordas sutis, hover nas linhas e rolagem vertical INTERNA (cabeçalho fixo) */
  const table = (cols, rows, o = {}) => `<div class="${o.h || "max-h-[60vh]"} overflow-y-auto overflow-x-auto rounded-xl border border-line bg-card"><table class="psd-tbl w-full border-collapse text-sm">
    <thead class="sticky top-0 z-10 bg-thead"><tr class="border-b border-line">${cols.map(c => `<th class="psd-rot whitespace-nowrap px-4 py-2.5 ${c.r ? "text-right" : "text-left"}">${c.h}</th>`).join("")}</tr></thead>
    <tbody class="divide-y divide-line">${rows.length ? rows.map(r => `<tr>${r.map((v, i) => `<td class="px-4 py-2 text-ink ${cols[i].r ? "text-right tabular-nums" : ""} ${cols[i].nw === false ? "" : "whitespace-nowrap"}">${v}</td>`).join("")}</tr>`).join("") : `<tr><td class="px-4 py-10 text-center text-mute" colspan="${cols.length}">Nada encontrado com estes filtros.</td></tr>`}</tbody></table></div>`;
  const input = (id, ph, cls = "") => `<input id="${id}" type="search" placeholder="${ph}" class="w-full rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500 ${cls}">`;
  const select = (id, opts, cur = "", cls = "") => `<select id="${id}" class="rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500 ${cls}">${opts.map(([v, l]) => `<option value="${esc(v)}" ${String(v) === String(cur) ? "selected" : ""}>${esc(l)}</option>`).join("")}</select>`;
  const btn = (id, label, ghost = true) => `<button type="button" id="${id}" class="rounded-lg px-3.5 py-2 text-sm font-semibold ${ghost ? "border border-line bg-card text-ink hover:bg-slate-500/10" : "bg-blue-600 text-white hover:bg-blue-700"}">${label}</button>`;
  /* nome do arquivo baixado: «PerfectAmortecedores - <tela como no menu> - dd-mm.ext» (igual a exporter.friendly_name) */
  const nome = (tela, ext = "csv") => { const d = new Date(); return `PerfectAmortecedores - ${tela} - ${String(d.getDate()).padStart(2, "0")}-${String(d.getMonth() + 1).padStart(2, "0")}.${ext}`; };
  const csv = (name, head, rows) => { const q = v => '"' + String(v ?? "").replace(/"/g, '""') + '"'; const b = new Blob(["﻿" + [head, ...rows].map(r => r.map(q).join(";")).join("\r\n")], { type: "text/csv;charset=utf-8" }); const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(b), download: name }); document.body.appendChild(a); a.click(); a.remove(); };

  /* Estado dos filtros de uma tela (etapa 17 · Q8): a URL manda e é a única memória.
     · links e conectores abrem a tela já filtrada; o Voltar do navegador volta aos filtros da URL;
     · tela aberta pelo menu (URL sem filtros) vem LIMPA (nada é lembrado da visita anterior);
     · set() grava na URL (sem recarregar); chip ativo clicado de novo = toggle() limpa o filtro.
     Uso: const F = PSDTW.filtros("desenvolvimento", ["q", "status", ...]);  F.get() → {chave: valor}; F.set({status: "X"}); F.toggle("flag", "pend_compras"); F.clear() */
  const filtros = (tela, chaves) => {
    const pick = o => Object.fromEntries(chaves.filter(k => o[k] != null && o[k] !== "").map(k => [k, String(o[k])]));
    try { localStorage.removeItem("psd-filtros-" + tela); } catch (e) { }          // limpa o que a versão anterior guardou
    let st = pick(Object.fromEntries(new URLSearchParams(location.search)));
    const write = () => { const u = new URLSearchParams(st).toString(); history.replaceState(null, "", location.pathname + (u ? "?" + u : "") + location.hash); };
    write();
    return { get: () => ({ ...st }), set: patch => { st = pick({ ...st, ...patch }); write(); }, toggle: (k, v) => { st = pick({ ...st, [k]: st[k] === String(v) ? "" : v }); write(); }, clear: () => { st = {}; write(); } };
  };
  /* ---------- avisos no canto (etapa 17 · Q7): somem sozinhos em 4 s; erro só some ao fechar ----------
     toast("3 desenhos enviados", { tom: "ok", titulo: "Envio concluído" })  · tom: ok | erro | aviso | info */
  const TICO = { ok: "circle-check", erro: "circle-alert", aviso: "triangle-alert", info: "info" };
  const toast = (msg, o = {}) => {
    const tom = o.tom || "ok"; let box = document.querySelector(".psd-toasts");
    if (!box) { box = Object.assign(document.createElement("div"), { className: "psd-toasts" }); box.setAttribute("aria-live", "polite"); document.body.appendChild(box); }
    const t = Object.assign(document.createElement("div"), { className: "psd-toast " + tom }); t.setAttribute("role", tom === "erro" ? "alert" : "status");
    t.innerHTML = `<span class="t-ico">${ico(TICO[tom] || "info")}</span><div>${o.titulo ? `<b>${esc(o.titulo)}</b>` : ""}${o.html ? msg : esc(msg)}</div><button type="button" aria-label="Fechar aviso">${ico("x", "sm")}</button>`;
    const sai = () => { t.classList.add("saindo"); setTimeout(() => t.remove(), 170); };
    t.querySelector(":scope > button").onclick = sai; box.appendChild(t);       // o «fechar» (o aviso pode trazer outros botões, como «Desfazer»)
    if (tom !== "erro" && o.fixo !== true) setTimeout(sai, o.ms || 4000);
    return t;
  };
  /* ---------- confirmação no próprio app (nunca a caixa do navegador) ----------
     if (await confirmar({ titulo: "Excluir o ensaio?", texto: "AMD0100 · 12/11/2026", botao: "Excluir", perigo: true, nota: "Não dá para desfazer." })) … */
  /* com `campo: { tipo: "password", rotulo: "Nova senha", min: 8 }` a caixa pede um valor e devolve o texto digitado (ou false se cancelar) */
  const confirmar = (o = {}) => new Promise(res => {
    const d = Object.assign(document.createElement("dialog"), { className: "psd-confirm" + (o.perigo ? " perigo" : "") }), c = o.campo;
    d.innerHTML = `<form method="dialog"><div class="c-body"><span class="c-ico">${ico(o.icone || (o.perigo ? "trash-2" : c ? "pencil" : "info"), "lg")}</span><div class="min-w-0 flex-1"><h3>${esc(o.titulo || "Confirmar?")}</h3>${o.texto ? `<p>${o.html ? o.texto : esc(o.texto)}</p>` : ""}
      ${c ? `<label class="mt-3 flex flex-col gap-1"><span class="text-sm font-semibold text-ink">${esc(c.rotulo || "Valor")}</span><input name="v" type="${c.tipo || "text"}" ${c.min ? `minlength="${c.min}"` : ""} required autocomplete="new-password" class="rounded-lg border border-line bg-card px-3 py-2 text-ink"></label>` : ""}
      ${o.nota ? `<p class="c-note">${esc(o.nota)}</p>` : ""}</div></div>
      <div class="c-acts"><button type="button" class="psd-btn" data-r="0">${esc(o.cancelar || "Cancelar")}</button><button type="submit" class="psd-btn ${o.perigo ? "perigo" : "prim"}" data-r="1">${esc(o.botao || "Confirmar")}</button></div></form>`;
    const fim = v => { d.close(); d.remove(); res(v); };
    d.addEventListener("click", e => { const b = e.target.closest('[data-r="0"]'); if (b) fim(false); else if (e.target === d) fim(false); });
    d.querySelector("form").addEventListener("submit", e => { e.preventDefault(); fim(c ? d.querySelector("[name=v]").value : true); });
    d.addEventListener("cancel", e => { e.preventDefault(); fim(false); });
    document.body.appendChild(d); d.showModal(); (c ? d.querySelector("[name=v]") : d.querySelector(o.perigo ? '[data-r="0"]' : '[data-r="1"]')).focus();
  });
  /* ---------- envio de arquivos com progresso por arquivo (etapa 17 · Q7): aviso fixo no canto com uma barra por arquivo enquanto sobe; some ao terminar ----------
     const r = await enviar("/api/drawings/check", fd, arquivos)   (fd = FormData já montado; arquivos = File[] na mesma ordem) */
  const enviar = (url, fd, arquivos = []) => new Promise((res, rej) => {
    const kb = n => n > 1048576 ? nf(n / 1048576, 1) + " MB" : nf(Math.max(1, n / 1024)) + " KB", tot = arquivos.reduce((a, f) => a + (f.size || 0), 0) || 1, mostra = arquivos.slice(0, 8);
    const t = arquivos.length ? toast(`<div class="mt-2 flex flex-col gap-2">${mostra.map((f, i) => `<div><div class="flex justify-between gap-3 text-xs"><span class="truncate">${esc(f.name)}</span><span class="text-mute" data-pp="${i}">${kb(f.size || 0)}</span></div><div class="mt-1 h-1.5 rounded-full bg-thead"><div class="h-1.5 rounded-full bg-blue-500" data-pb="${i}" style="width:0%"></div></div></div>`).join("")}${arquivos.length > 8 ? `<div class="text-xs text-mute">+ ${arquivos.length - 8} arquivo(s)</div>` : ""}</div>`,
      { tom: "info", titulo: `Enviando ${arquivos.length} arquivo(s), ${kb(tot)}`, fixo: true, html: true }) : null;
    const xhr = new XMLHttpRequest(); xhr.open("POST", url);
    xhr.upload.onprogress = e => { if (!t || !e.lengthComputable) return; let acc = 0; const sent = e.loaded / e.total * tot;
      mostra.forEach((f, i) => { const p = Math.max(0, Math.min(1, (sent - acc) / (f.size || 1))); acc += f.size || 0; const b = t.querySelector(`[data-pb="${i}"]`); if (b) b.style.width = Math.round(100 * p) + "%"; if (p >= 1) { const s = t.querySelector(`[data-pp="${i}"]`); if (s) s.textContent = "✔ enviado"; } }); };
    const fim = () => { if (t) { t.classList.add("saindo"); setTimeout(() => t.remove(), 170); } };
    xhr.onload = () => { fim(); let j = null; try { j = JSON.parse(xhr.responseText); } catch (e) { }
      if (xhr.status >= 400 || !j) rej(new Error((j && j.error) || `Erro ${xhr.status} ao enviar.`)); else res(j); };
    xhr.onerror = () => { fim(); rej(new Error("Falha de conexão ao enviar os arquivos.")); };
    xhr.send(fd);
  });
  const erro = e => toast(e && e.message ? e.message : String(e), { tom: "erro", titulo: "Não deu certo" });          // erro no canto (substitui a caixa «alert» do navegador)
  /* ---------- código PERFECT editável na própria célula (Cobertura · «Nosso código», etapa 19 · Q7; Brands · «Código PERFECT», etapa 22) ----------
     editarCodigos(box, { lista, valor, ph, rotulo, salvar: async novo => … }) troca o conteúdo da célula por um campo com sugestões de códigos PERFECT.
     Enter chama salvar(texto em maiúsculas) — erro volta a célula e mostra o aviso; Esc ou sair do campo cancela; sem mudança não salva. */
  const editarCodigos = (box, o = {}) => {
    const antes = box.innerHTML, val = String(o.valor || "");
    let dl = document.getElementById("psd-codigos-dl");
    if (!dl) { dl = Object.assign(document.createElement("datalist"), { id: "psd-codigos-dl" }); document.body.appendChild(dl); }
    box.innerHTML = `<input class="psd-ed-in" list="psd-codigos-dl" value="${esc(val)}" placeholder="${esc(o.ph || "")}" aria-label="${esc(o.rotulo || "Código PERFECT")}">`;
    const inp = box.querySelector("input"); inp.focus(); inp.select(); let feito = false;
    const sugerir = async () => { const t = inp.value.split(/[,;\s]+/).pop(); if (t.length < 3) return;
      const d = await fetch("/api/samples/codes?q=" + encodeURIComponent(t)).then(r => r.json()).catch(() => ({ rows: [] }));
      dl.innerHTML = (d.rows || []).map(r => `<option value="${esc(o.lista ? inp.value.replace(/[^,;\s]*$/, "") + r.perfect_code : r.perfect_code)}">${esc(r.description || "")}</option>`).join(""); };
    const cancelar = () => { if (!feito) { feito = true; box.innerHTML = antes; } };
    const salvar = async () => {
      if (feito) return; feito = true; const novo = inp.value.trim().toUpperCase();
      if (novo === val.toUpperCase()) { box.innerHTML = antes; return; }
      try { await o.salvar(novo); } catch (er) { box.innerHTML = antes; erro(er); }
    };
    inp.addEventListener("input", sugerir);
    inp.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); salvar(); } if (e.key === "Escape") { e.preventDefault(); cancelar(); } });
    inp.addEventListener("blur", () => setTimeout(cancelar, 150));          // sair do campo sem Enter = cancelar
  };
  /* ---------- carregamento: faixas da marca + texto, ou esqueleto no lugar de KPIs/tabela ---------- */
  const carregando = (t = "Carregando…") => `<div class="psd-load rounded-2xl border border-line bg-card px-5 py-8">${stripes()}<span>${esc(t)}</span></div>`;
  const esqueleto = (linhas = 6, kpis = 0) => (kpis ? `<div class="grid grid-cols-2 gap-4 lg:grid-cols-4">${'<div class="skel h-24"></div>'.repeat(kpis)}</div>` : "")
    + `<div class="flex flex-col gap-2 ${kpis ? "mt-5" : ""}"><div class="skel h-10"></div>${'<div class="skel h-8"></div>'.repeat(linhas)}</div>`;
  /* ---------- gráfico (Chart.js 4, salvo em static/vendor): cores da marca, fonte e grade do tema; redesenha ao trocar o tema ----------
     grafico(el, { type: "bar", data: { labels, datasets: [{ label, data }] }, options }) → instância (el = <canvas> ou contêiner) */
  /* etapa 24 · Q9 (skill dataviz, regras em DESIGN.md §6.6): paleta validada em ordem fixa — azul, laranja, azul-claro, vermelho, violeta, verde; 7 = cinza de fundo.
     A tela pede cor por token ("--chart-2" ou "var(--chart-2)"); hex antigos ainda passados por alguma tela caem no slot equivalente (ANTIGAS). */
  const CORES = ["#3A57A3", "#D27800", "#2E9FD0", "#D62E3D", "#7B5CE0", "#0E9F6E", "#A3AEC2"];
  const ANTIGAS = { "#2F4A8C": 0, "#2F6BFF": 0, "#3B82F6": 0, "#F6A019": 1, "#F59E0B": 1, "#64C4E9": 2, "#5AA9FF": 2, "#06B6D4": 2, "#E72B3B": 3, "#EF4444": 3, "#F43F5E": 3,
    "#8B5CF6": 4, "#0E9F6E": 5, "#10B981": 5, "#94A3B8": 6, "#64748B": 6 };
  const cssv = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const tema = () => { const C = window.Chart; if (!C) return;
    C.defaults.font.family = '"Segoe UI Variable Text","Segoe UI",system-ui,sans-serif'; C.defaults.font.size = 12.5; C.defaults.color = cssv("--mut"); C.defaults.borderColor = cssv("--chart-grid");
    C.defaults.scale.grid.color = cssv("--chart-grid"); C.defaults.plugins.legend.labels.color = cssv("--chart-legend");
    Object.assign(C.defaults.plugins.tooltip, { backgroundColor: cssv("--card"), titleColor: cssv("--tx"), bodyColor: cssv("--tx"), borderColor: cssv("--line"), borderWidth: 1, padding: 10, cornerRadius: 10, boxPadding: 4,
      titleFont: { family: cssv("--fontd"), weight: "600", size: 13 }, usePointStyle: true });
    // bolinha da legenda do tamanho da caixa (8 px): sem boxHeight ela crescia até o tamanho da fonte e cobria o começo do texto
    Object.assign(C.defaults.plugins.legend.labels, { usePointStyle: true, boxWidth: 8, boxHeight: 8, padding: 14 }); C.defaults.plugins.legend.align = "start"; C.defaults.maintainAspectRatio = false;
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) C.defaults.animation = false; registra(); };
  const vivos = new Set();
  const paleta = () => CORES.map((c, i) => cssv(`--chart-${i + 1}`) || c);
  const corTema = c => { if (!c || typeof c !== "string") return c; const v = c.match(/^var\((--[\w-]+)\)$/); if (v) c = v[1];
    if (c.startsWith("--")) return cssv(c); const i = ANTIGAS[c.toUpperCase()] ?? CORES.indexOf(c.toUpperCase()); return i < 0 ? c : paleta()[i]; };
  const corDe = i => paleta()[i % 6];                                       // a 7ª (cinza) nunca é série automática
  const pinta = (type, datasets) => (datasets || []).forEach((ds, i) => {          // só pinta o que o chamador não definiu (marcado em _auto); série pode ter o próprio tipo (gráfico misto)
    ds._auto ??= { bg: ds.backgroundColor == null, bd: ds.borderColor == null }; if (!("_bg0" in ds)) { ds._bg0 = ds.backgroundColor; ds._bd0 = ds.borderColor; }
    const tp = ds.type || type, c = corTema(ds.cor) || corDe(i), roda = tp === "doughnut" || tp === "pie";
    if (ds._auto.bg) ds.backgroundColor = tp === "line" ? c + "1A" : roda ? paleta() : c;           // área da linha: lavada a 10%
    else ds.backgroundColor = Array.isArray(ds._bg0) ? ds._bg0.map(corTema) : corTema(ds._bg0);      // cor pedida pela tela também acompanha o tema
    if (ds._auto.bd) ds.borderColor = roda ? cssv("--card") : ds.stack != null && tp === "bar" ? cssv("--card") : c;   // pilha: borda na cor do cartão = vão de 2 px
    else ds.borderColor = Array.isArray(ds._bd0) ? ds._bd0.map(corTema) : corTema(ds._bd0);
    if (tp === "line") { ds.pointBackgroundColor = c; ds.pointBorderColor = cssv("--card"); } });
  /* números curtos no eixo e nos rótulos: 950 · 12,5 mil · 2,3 mi */
  const curto = v => { const a = Math.abs(v), f = x => Number(x).toLocaleString("pt-BR", { maximumFractionDigits: 1 });
    return a >= 1e6 ? f(v / 1e6) + " mi" : a >= 1e4 ? f(v / 1e3) + " mil" : f(v); };
  /* plugins: rótulo seletivo (fim da linha; maior e último mês na barra), linha do cursor nas linhas, divisória vertical (Pareto) */
  let registrado = false;
  const registra = () => { if (registrado || !window.Chart) return; registrado = true;
    const fixo = { _scriptable: false, _indexable: false };                // opções lidas como estão (fmt é função, não opção calculada)
    const rotulos = { id: "psdRotulos", defaults: { modo: null, fmt: null }, descriptors: fixo, afterDatasetsDraw(ch, _a, o) { if (!o || !o.modo) return;
      const { ctx } = ch, fmt = o.fmt || curto, its = [];
      ch.data.datasets.forEach((ds, di) => { const m = ch.getDatasetMeta(di); if (m.hidden || !m.visible) return; const v = ds.data;
        const ult = v.reduce((k, x, i) => x == null ? k : i, -1); if (ult < 0) return;
        if (o.modo === "fim" && m.type === "line") its.push({ el: m.data[ult], txt: fmt(v[ult]), lado: "dir" });
        if (o.modo === "destaque" && m.type === "bar") { const mx = v.reduce((k, x, i) => x != null && x > (v[k] ?? -Infinity) ? i : k, 0);
          [...new Set([mx, ult])].forEach(i => its.push({ el: m.data[i], txt: fmt(v[i]), lado: "cima" })); } });
      ctx.save(); ctx.font = `600 11.5px ${ch.options.font?.family || window.Chart.defaults.font.family}`; ctx.fillStyle = cssv("--tx");
      const usados = [];                                                     // rótulos que se tocariam: fica o primeiro, o resto vai para a dica e a legenda
      its.forEach(t => { if (!t.el) return; const w = ctx.measureText(t.txt).width, y = t.lado === "dir" ? t.el.y : t.el.y - 5;
        const x = t.lado === "dir" ? Math.min(t.el.x + 8, ch.width - w - 2) : Math.min(Math.max(t.el.x, w / 2 + 2), ch.width - w / 2 - 2);   // o texto nunca sai do quadro
        const cx = t.lado === "dir" ? x : x - w / 2, cy = t.lado === "dir" ? y - 7 : y - 14;
        if (usados.some(u => cx < u.x + u.w + 4 && cx + w + 4 > u.x && cy < u.y + 14 && cy + 14 > u.y)) return; usados.push({ x: cx, y: cy, w });
        ctx.textAlign = t.lado === "dir" ? "left" : "center"; ctx.textBaseline = t.lado === "dir" ? "middle" : "bottom"; ctx.fillText(t.txt, x, y); });
      ctx.restore(); } };
    const cursor = { id: "psdCursor", defaults: { ativo: false }, descriptors: fixo, afterDraw(ch, _a, op) { if (!op || !op.ativo) return; const a = ch.tooltip && ch.tooltip.getActiveElements(); if (!a || !a.length) return;
      const x = a[0].element.x, { top, bottom } = ch.chartArea, ctx = ch.ctx; ctx.save(); ctx.strokeStyle = cssv("--mut"); ctx.globalAlpha = .45; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x, top); ctx.lineTo(x, bottom); ctx.stroke(); ctx.restore(); } };
    const divisa = { id: "psdDivisa", defaults: { i: null, texto: "" }, descriptors: fixo, afterDatasetsDraw(ch, _a, o) { if (!o || o.i == null) return; const m = ch.getDatasetMeta(0).data, a = m[o.i], b = m[o.i + 1]; if (!a || !b) return;
      const x = (a.x + b.x) / 2, { top, bottom } = ch.chartArea, ctx = ch.ctx; ctx.save(); ctx.strokeStyle = cssv("--mut"); ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x, top + 16); ctx.lineTo(x, bottom); ctx.stroke(); ctx.font = `600 11.5px ${window.Chart.defaults.font.family}`; ctx.fillStyle = cssv("--tx");
      const w = ctx.measureText(o.texto).width, dir = x + 6 + w <= ch.chartArea.right; ctx.textAlign = dir ? "left" : "right"; ctx.textBaseline = "top";
      ctx.fillText(o.texto, dir ? x + 6 : x - 6, top); ctx.restore(); } };
    window.Chart.register(rotulos, cursor, divisa); };
  const _def = (o, k, v) => { if (o[k] === undefined) o[k] = v; return o[k]; };
  /* eixos padrão: grade fina e sólida só no eixo dos valores, sem linha de eixo, até 5 marcas com número curto; cada tela pode sobrescrever */
  const eixos = cfg => { if (cfg.type !== "bar" && cfg.type !== "line") return; const o = cfg.options, sc = _def(o, "scales", {}), val = o.indexAxis === "y" ? "x" : "y", cat = val === "x" ? "y" : "x";
    const c = _def(sc, cat, {}); _def(_def(c, "grid", {}), "display", false); _def(_def(c, "border", {}), "display", false);
    if (cat === "y") _def(_def(c, "ticks", {}), "autoSkip", false);        // barras deitadas (ranking): todo nome aparece
    const v = _def(sc, val, {}); _def(v, "beginAtZero", true); _def(_def(v, "border", {}), "display", false); const t = _def(v, "ticks", {}); _def(t, "maxTicksLimit", 5); _def(t, "callback", x => curto(x));
    // cores lidas do token a cada desenho (função): o Chart.js guarda as cores dos eixos e não as trocava com o tema
    Object.values(sc).forEach(s => { _def(_def(s, "grid", {}), "color", () => cssv("--chart-grid")); _def(_def(s, "ticks", {}), "color", () => cssv("--mut")); }); };
  const grafico = (el, cfg) => {
    if (!window.Chart) { (el.tagName === "CANVAS" ? el.parentElement : el).innerHTML = notice("Gráfico indisponível: static/vendor/chart.umd.js não foi carregado.", "amber"); return null; }
    tema(); let cv = el;
    if (el.tagName !== "CANVAS") { el.innerHTML = '<canvas role="img"></canvas>'; cv = el.firstChild; if (!el.style.height) el.style.height = (cfg.altura || 280) + "px"; el.style.position = "relative"; }
    if (cfg.titulo) cv.setAttribute("aria-label", cfg.titulo);
    const dss = cfg.data.datasets || [], o = cfg.options ||= {}, pl = _def(o, "plugins", {}), roda = cfg.type === "doughnut" || cfg.type === "pie";
    pinta(cfg.type, dss);
    dss.forEach(ds => { const tp = ds.type || cfg.type;
      if (tp === "bar") { ds.borderRadius ??= 4; ds.maxBarThickness ??= 24; ds.borderSkipped ??= "start";        // ponta arredondada de 4 px, base reta, no máximo 24 px
        ds.borderWidth ??= ds.stack != null ? { top: 2 } : 0; }
      if (tp === "line") { const ult = ds.data.reduce((k, x, i) => x == null ? k : i, -1);                       // 2 px, sem bolinha em todo ponto: só o último
        ds.tension ??= 0.25; ds.cubicInterpolationMode ??= "monotone"; /* monótona: a curva não passa do valor (não fura o zero) */ ds.borderWidth ??= 2; ds.fill ??= false; ds.pointRadius ??= ds.data.map((_, i) => i === ult ? 4 : 0); ds.pointBorderWidth ??= 2; ds.pointHoverRadius ??= 5; ds.pointHitRadius ??= 12; } });
    if (!roda) { eixos(cfg); const lg = _def(pl, "legend", {}); _def(lg, "display", dss.length > 1);                  // legenda só com 2 séries ou mais
      const linha = dss.some(ds => (ds.type || cfg.type) === "line");
      if (linha) { _def(o, "interaction", { mode: "index", intersect: false }); _def(pl, "psdCursor", { ativo: true }); }
      const unicaBarra = dss.length === 1 && cfg.type === "bar" && o.indexAxis !== "y" && dss[0].data.length > 2;
      const r = _def(pl, "psdRotulos", {}); if (r) _def(r, "modo", linha && dss.length <= 4 && !dss.some(ds => (ds.type || cfg.type) === "bar") ? "fim" : unicaBarra ? "destaque" : null);
      if (r && r.modo) { const p = _def(o, "layout", {}).padding; if (p === undefined) o.layout.padding = r.modo === "fim" ? { right: 40, top: 6 } : { top: 18 }; } }
    const old = window.Chart.getChart(cv); if (old) old.destroy();
    const g = new window.Chart(cv, { type: cfg.type, data: cfg.data, options: o }); vivos.add(g); return g;
  };
  /* ---------- barra segmentada alta (no lugar da rosca) e medidor (no lugar da meia-rosca): HTML, sem Chart.js ----------
     segmentos(el, [{ l, v, cor, txt }], { legenda: [{ l, cor }] (padrão: as partes), fmt }) — 28 px, vão de 2 px, a fatia de cada parte escrita dentro só se couber;
     a que não couber vai para a legenda ao lado do nome. Cor por token ("--chart-1"). */
  const _tinta = c => { const h = corTema(c) || "#000", m = h.match(/^#?([\da-f]{2})([\da-f]{2})([\da-f]{2})/i); if (!m) return "#fff";
    const L = m.slice(1).map(x => { const s = parseInt(x, 16) / 255; return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4; }), y = 0.2126 * L[0] + 0.7152 * L[1] + 0.0722 * L[2];
    return (1.05 / (y + 0.05)) >= ((y + 0.05) / 0.05) ? "#fff" : "#0B1220"; };                         // branco ou quase-preto, o que contrastar mais com o preenchimento
  const _vivosSeg = new Set();
  const _ajustaSeg = el => { el.querySelectorAll(".psd-segbar > div").forEach(b => { const s = b.firstElementChild; b.style.color = _tinta(b.dataset.cor); if (!s) return;
      s.hidden = false; const cabe = s.offsetWidth + 16 <= b.clientWidth; s.hidden = !cabe; const lg = el.querySelector(`[data-segl="${b.dataset.i}"]`); if (lg) lg.hidden = cabe; }); };
  const segmentos = (el, partes, op = {}) => { if (!el) return; const tot = partes.reduce((a, p) => a + (p.v || 0), 0) || 1, fmt = op.fmt || (p => Math.round(100 * p.v / tot) + "%");
    const vis = partes.map((p, i) => ({ ...p, i })).filter(p => p.v > 0), nome = p => `${p.l}: ${p.txt || nf(p.v)} (${nf(100 * p.v / tot, 1)}%)`;
    el.innerHTML = `<div class="psd-segbar" role="img" aria-label="${esc(vis.map(nome).join("; "))}">${vis.map(p => `<div data-i="${p.i}" data-cor="${esc(p.cor)}" tabindex="0" title="${esc(nome(p))}" style="flex:${p.v} 1 0;background:${String(p.cor).startsWith("--") ? `var(${p.cor})` : p.cor}"><span>${esc(fmt(p))}</span></div>`).join("")}</div>
      <div class="psd-legs">${partes.map((p, i) => `<span><i style="background:${String(p.cor).startsWith("--") ? `var(${p.cor})` : p.cor}"></i>${esc(p.l)}<b data-segl="${i}" hidden>${nf(100 * (p.v || 0) / tot, 1)}%</b></span>`).join("")}</div>`;
    _ajustaSeg(el); if (!el._ro && window.ResizeObserver) { el._ro = new ResizeObserver(() => _ajustaSeg(el)); el._ro.observe(el); } _vivosSeg.add(el); };
  /* medidor de meta: número grande, «de N (x%)» e o trilho em tom claro do azul; verde (--ok) só quando bate a meta */
  const medidor = o => { const v = o.value || 0, t = o.target || 0, ok = t && v >= t, p = t ? 100 * v / t : 0;
    return `<div class="psd-med">${o.title ? `<div class="psd-med-t">${esc(o.title)}</div>` : ""}<div class="lin"><b>${nf(v)}</b><span>${t ? `de ${nf(t)} (${nf(p, 1)}%)${ok ? ", atingida" : ""}` : "sem meta"}</span></div>
      <div class="trk" role="meter" aria-valuemin="0" aria-valuemax="${t || 0}" aria-valuenow="${v}" aria-label="${esc((o.title || "Meta") + ": " + nf(v) + (t ? " de " + nf(t) : ""))}"><div style="width:${Math.min(100, p).toFixed(1)}%;background:var(${ok ? "--ok" : "--chart-1"})"></div></div>
      ${o.subtitle ? `<div class="psd-med-s">${esc(o.subtitle)}</div>` : ""}</div>`; };
  /* ---------- update 5 (26/11/2026, maquete aprovada): rosca fina e anel de meta — SVG com cores por token (trocam com o tema sem redesenhar) ---------- */
  const _var = c => String(c).startsWith("--") ? `var(${c})` : c;
  const _ponto = (cx, cy, r, t) => [cx + r * Math.cos(2 * Math.PI * t - Math.PI / 2), cy + r * Math.sin(2 * Math.PI * t - Math.PI / 2)];
  const _arco = (cx, cy, r, a, b) => { const [x0, y0] = _ponto(cx, cy, r, a), [x1, y1] = _ponto(cx, cy, r, b); return `M${x0.toFixed(2)} ${y0.toFixed(2)} A${r} ${r} 0 ${b - a > 0.5 ? 1 : 0} 1 ${x1.toFixed(2)} ${y1.toFixed(2)}`; };
  /* rosca(partes [{l, v, cor}], {rotulo, acoes}) → anel de 12 px com 2 px de vão, o total no centro e, ao lado, nome, quantidade e % de cada parte (Dashboard › Sistema) */
  const rosca = (partes, o = {}) => { const tot = partes.reduce((a, p) => a + (p.v || 0), 0), vis = partes.filter(p => p.v > 0), R = 72, gap = vis.length > 1 ? 2 / (2 * Math.PI * R) : 0; let ac = 0;
    const pct = p => tot ? nf(100 * p.v / tot, 1) + "%" : "–";
    const arcos = vis.map(p => { const f = p.v / tot, d = f >= 0.9999 ? null : _arco(84, 84, R, ac + gap / 2, ac + f - gap / 2); ac += f;
      return d ? `<path d="${d}" fill="none" stroke="${_var(p.cor)}" stroke-width="12"><title>${esc(p.l)}: ${nf(p.v)} (${pct(p)})</title></path>` : `<circle cx="84" cy="84" r="${R}" fill="none" stroke="${_var(p.cor)}" stroke-width="12"/>`; }).join("");
    return `<div class="psd-rosca"><svg viewBox="0 0 168 168" role="img" aria-label="${esc(vis.map(p => `${p.l} ${nf(p.v)} (${pct(p)})`).join("; ") + `; total ${nf(tot)}`)}">
        <circle cx="84" cy="84" r="${R}" fill="none" stroke="var(--chart-trilho)" stroke-width="12" opacity="${tot ? 0 : 1}"/>${arcos}
        <text x="84" y="82" text-anchor="middle" class="n">${nf(tot)}</text><text x="84" y="102" text-anchor="middle" class="r">${esc(o.rotulo || "total")}</text></svg>
      <div class="tab">${partes.map(p => `<div class="lin"><i style="background:${_var(p.cor)}"></i><span>${esc(p.l)}</span><b>${nf(p.v)}</b><span class="p">${pct(p)}</span></div>`).join("")}${o.acoes ? `<div class="ac">${o.acoes}</div>` : ""}</div></div>`; };
  /* anel({value, target, title, subtitle, year}) → % no centro; o tracinho marca onde a meta deveria estar hoje (meta × parte do ano já passada);
     ao lado: «n de meta», o ritmo e a distância dele (laranja abaixo, verde acima); verde no anel só quando bate a meta (Dashboard e Metas) */
  const anel = o => { const v = o.value || 0, t = o.target || 0, ok = t > 0 && v >= t, p = t ? 100 * v / t : 0, hoje = new Date(), y = +o.year || hoje.getFullYear();
    const fr = y < hoje.getFullYear() ? 1 : y > hoje.getFullYear() ? 0 : (hoje - new Date(y, 0, 1)) / (new Date(y + 1, 0, 1) - new Date(y, 0, 1)), esp = Math.round(t * fr), dif = v - esp;
    const R = 44, C = 2 * Math.PI * R, [ix, iy] = _ponto(52, 52, R - 9, fr), [ox, oy] = _ponto(52, 52, R + 9, fr);
    const rit = !t ? "sem meta" : ok ? `meta atingida em ${y}` : fr >= 1 ? `ano encerrado` : `ritmo de hoje: ${nf(esp)}`;
    const chip = !t ? "" : ok ? `<span class="psd-anel-d cima">▲ ${v > t ? `${nf(v - t)} acima da meta` : "meta atingida"}</span>`
      : fr >= 1 ? `<span class="psd-anel-d baixo">▼ faltaram ${nf(t - v)}</span>` : dif >= 0 ? `<span class="psd-anel-d cima">▲ ${nf(dif)} acima do ritmo</span>` : `<span class="psd-anel-d baixo">▼ ${nf(-dif)} abaixo do ritmo</span>`;
    return `<div class="psd-anel"><svg viewBox="0 0 104 104" role="img" aria-label="${esc(`${o.title || "Meta"}: ${nf(v)}${t ? ` de ${nf(t)}, ${nf(p, 1)}%; ${rit}` : ""}`)}">
        <circle cx="52" cy="52" r="${R}" fill="none" stroke="var(--chart-trilho)" stroke-width="9"/>
        ${p > 0 ? `<circle cx="52" cy="52" r="${R}" fill="none" stroke="var(${ok ? "--ok" : "--chart-1"})" stroke-width="9" stroke-linecap="round" stroke-dasharray="${(C * Math.min(p, 100) / 100).toFixed(2)} ${C.toFixed(2)}" transform="rotate(-90 52 52)"/>` : ""}
        ${t && !ok && fr > 0 && fr < 1 ? `<line x1="${ix.toFixed(2)}" y1="${iy.toFixed(2)}" x2="${ox.toFixed(2)}" y2="${oy.toFixed(2)}" class="rit"><title>Ritmo de hoje: ${nf(esp)}</title></line>` : ""}
        <text x="52" y="58" text-anchor="middle">${t ? nf(p, p >= 100 ? 0 : 1) + "%" : "–"}</text></svg>
      <div class="inf">${o.title ? `<div class="tt">${esc(o.title)}</div>` : ""}<div class="num">${nf(v)}${t ? ` <small>de ${nf(t)}</small>` : ""}</div><div class="rit">${esc(rit)}</div>${chip}
        ${o.subtitle ? `<div class="ap">${esc(o.subtitle)}</div>` : ""}</div></div>`; };
  /* legenda em HTML (gráfico de uma série com cor por categoria, p. ex. curva A/B/C) */
  const legenda = itens => `<div class="psd-legs">${itens.map(x => `<span><i style="background:${String(x.cor).startsWith("--") ? `var(${x.cor})` : x.cor}"></i>${esc(x.l)}</span>`).join("")}</div>`;
  /* ---------- Barra de filtros (etapa 19 · Q4/Q6): um padrão para todas as telas ----------
     busca + até 3 filtros principais (tipo "seg" = botões lado a lado; "lista" = botão com o nome dentro que abre a lista com a contagem de cada opção)
     + «Mais filtros» (painel com os demais) + etiquetas dos filtros ativos com × e «Limpar tudo». Ações (Excel…) à direita.
     barra({ busca: {valor, ph}, principais: [{k, rotulo, tipo, atual, opcoes: [{v, l, n}]}], mais: [...mesmo formato], etiquetas: [{k, l}], acoes, aberto })
     ligarBarra(el, { set(k, v), busca(texto), limpar() }) — uma vez por elemento (o HTML de dentro pode ser redesenhado à vontade). */
  const _opcao = (o, f) => o.g ? `<div class="psd-opt-g">${esc(o.g)}</div>` : `<button type="button" role="menuitemradio" aria-checked="${String(o.v) === String(f.atual ?? "")}" data-fk="${esc(f.k)}" data-fv="${esc(o.v)}" class="psd-opt${String(o.v) === String(f.atual ?? "") ? " on" : ""}"><span class="truncate">${esc(o.l)}</span>${o.n != null ? `<span class="n">${nf(o.n)}</span>` : ""}</button>`;
  const _filtro = f => {
    if (f.tipo === "seg") return `<div class="psd-seg" role="group" aria-label="${esc(f.rotulo)}">${f.opcoes.map(o => `<button type="button" data-fk="${esc(f.k)}" data-fv="${esc(o.v)}" aria-pressed="${String(o.v) === String(f.atual ?? "")}"${o.n != null ? ` title="${nf(o.n)}"` : ""}>${esc(o.l)}</button>`).join("")}</div>`;
    const cur = f.opcoes.find(o => !o.g && String(o.v) === String(f.atual ?? "")) || { l: f.atual || "Todos" };
    return `<div class="psd-dd"><button type="button" data-dd aria-haspopup="menu" aria-expanded="false" class="psd-pill${f.atual ? " ativo" : ""}"><span class="r">${esc(f.rotulo)}</span><b>${esc(cur.l)}</b>${ico("chevron-down", "sm")}</button>
      <div class="psd-menu" role="menu" hidden>${f.opcoes.map(o => _opcao(o, f)).join("")}</div></div>`;
  };
  /* chip do «Mais filtros»: um valor (clicar de novo limpa) ou, com f.multi, vários juntos por «|» (data-fv já leva a lista resultante) */
  const _chipMais = (f, x) => {
    const lst = String(f.atual ?? "").split("|").filter(Boolean), on = f.multi ? lst.includes(String(x.v)) : String(x.v) === String(f.atual ?? "");
    const fv = f.multi ? (on ? lst.filter(v => v !== String(x.v)) : [...lst, String(x.v)]).join("|") : x.v;
    return `<button type="button" data-fk="${esc(f.k)}" data-fv="${esc(fv)}" ${f.multi ? "" : "data-ftg"} aria-pressed="${on}"${x.t ? ` title="${esc(x.t)}"` : ""} class="psd-chip">${esc(x.l)}${x.n != null ? `<span class="n">${nf(x.n)}</span>` : ""}</button>`;
  };
  const barra = o => {
    const mais = o.mais || [], nm = mais.filter(f => f.atual).length;    return `<div class="psd-fbar"><div class="flex flex-wrap items-center gap-2">
        ${o.busca ? `<label class="psd-search">${ico("search", "sm")}<input name="q" type="search" autocomplete="off" value="${esc(o.busca.valor || "")}" placeholder="${esc(o.busca.ph || "Buscar…")}"></label>` : ""}
        ${(o.principais || []).map(_filtro).join("")}
        ${mais.length ? `<button type="button" data-fmais aria-expanded="${!!o.aberto}" class="psd-pill${nm ? " ativo" : ""}">${ico("list-filter", "sm")}<b>Mais filtros</b>${nm ? `<span class="psd-badge">${nm}</span>` : ""}</button>` : ""}
        ${o.acoes ? `<div class="ml-auto flex items-center gap-2">${o.acoes}</div>` : ""}</div>
      ${mais.length ? `<div class="psd-mais"${o.aberto ? "" : " hidden"}>${mais.map(f => `<div class="psd-mais-g${f.opcoes.length > 8 ? " largo" : ""}"><div class="t">${esc(f.rotulo)}</div><div class="flex flex-wrap gap-1.5">${f.opcoes.map(x => _chipMais(f, x)).join("")}</div></div>`).join("")}</div>` : ""}
      ${(o.atalhos || []).length ? `<div class="psd-atalhos"><span class="t">Atalhos</span>${o.atalhos.map(a => `<button type="button" data-fk="${esc(a.k)}" data-fv="${esc(a.v)}" data-ftg aria-pressed="${!!a.on}" class="psd-chip${a.forte ? " forte" : ""}">${esc(a.l)}${a.n != null ? `<span class="n">${nf(a.n)}</span>` : ""}</button>`).join("")}</div>` : ""}
      ${(o.etiquetas || []).length ? `<div class="psd-tags">${o.etiquetas.map(t => `<span class="psd-tag">${esc(t.l)}<button type="button" data-fx="${esc(t.k)}" aria-label="Tirar o filtro ${esc(t.l)}">${ico("x", "sm")}</button></span>`).join("")}<button type="button" data-flimpar class="psd-link">Limpar tudo</button></div>` : ""}</div>`;
  };
  const pintarBarra = (el, o) => {        // redesenha mantendo o cursor na busca (a lista recarrega enquanto a pessoa digita)
    const f = document.activeElement, foco = f && f.name === "q" && el.contains(f);
    el.innerHTML = barra(o);
    if (foco) { const i = el.querySelector("input[name=q]"); if (i) { i.focus(); i.setSelectionRange(i.value.length, i.value.length); } }
  };
  const ligarBarra = (el, h) => {
    let timer;
    const fecha = (exceto) => el.querySelectorAll(".psd-dd [data-dd][aria-expanded=true]").forEach(b => { if (b !== exceto) { b.setAttribute("aria-expanded", "false"); b.nextElementSibling.hidden = true; } });
    el.addEventListener("click", e => {
      const dd = e.target.closest("[data-dd]"), fk = e.target.closest("[data-fk]"), fx = e.target.closest("[data-fx]"), fm = e.target.closest("[data-fmais]"), lp = e.target.closest("[data-flimpar]");
      if (dd) { const ab = dd.getAttribute("aria-expanded") !== "true"; fecha(dd); dd.setAttribute("aria-expanded", String(ab)); dd.nextElementSibling.hidden = !ab; return; }
      if (fk) { fecha(); const on = fk.getAttribute("aria-pressed") === "true" || fk.classList.contains("on"); h.set(fk.dataset.fk, fk.hasAttribute("data-ftg") && on ? "" : fk.dataset.fv); return; }
      if (fx) { h.set(fx.dataset.fx, ""); return; }
      if (fm) { const p = el.querySelector(".psd-mais"), ab = p.hidden; p.hidden = !ab; fm.setAttribute("aria-expanded", String(ab)); h.mais && h.mais(ab); return; }
      if (lp) { h.limpar(); }
    });
    el.addEventListener("input", e => { if (e.target.name === "q") { clearTimeout(timer); timer = setTimeout(() => h.busca(e.target.value.trim()), 300); } });
    el.addEventListener("keydown", e => { if (e.key === "Escape") fecha(); if (e.key === "Enter" && e.target.name === "q") e.preventDefault(); });
    document.addEventListener("click", e => { if (!el.contains(e.target)) fecha(); });
  };
  /* ajudantes da barra: opções a partir de [{v, n}] ou {valor: n}, e as etiquetas dos filtros ativos ({chave: rótulo}) */
  const ops = (lst, rot = v => v) => (Array.isArray(lst) ? lst : Object.entries(lst || {}).map(([v, n]) => ({ v, n }))).map(x => ({ v: x.v, l: rot(x.v), n: x.n }));
  const etiquetas = (s, nomes, val = (k, v) => v) => Object.keys(nomes).filter(k => s[k]).map(k => ({ k, l: `${nomes[k]}: ${val(k, s[k])}` }));
  /* botão principal (navy) e secundário (discreto) do padrão novo */
  const botao = (rotulo, o = {}) => `<${o.href ? `a href="${o.href}"` : `button type="button"`} ${o.attrs || ""} class="psd-btn ${o.secundario ? "" : "prim"}">${o.icone ? ico(o.icone, "sm") : ""}${esc(rotulo)}</${o.href ? "a" : "button"}>`;

  /* ---------- FOB em DES/R-D (etapa 22 · Q15–Q21) ----------
     fobRD(info, cheio) — info = rd.fob_info: verde = fornecedor do item (FOB_FINAL do servidor; sem ele, a planilha FOB), com «planilha: x» quando difere e
     «varia: a–b» entre aplicações; branco = vigente (fornecedor da última compra) ou outros fornecedores, da planilha. cheio = cartões do detalhe; senão célula da lista. */
  const usd = v => "US$ " + nf(v, 2);
  const fobRD = (f, cheio) => {
    if (!f) return cheio ? "" : '<span class="text-mute">–</span>';
    const it = f.item || {}, cmp = f.comparar || [], varia = it.varia ? `varia: ${nf(it.varia[0], 2)}–${nf(it.varia[1], 2)}` : "";
    const fonte = it.fonte === "servidor" ? "FOB_FINAL do servidor" : it.fonte === "planilha" ? "planilha FOB" : "";
    const semItem = `sem FOB ${it.fornecedor ? "de " + esc(it.fornecedor) : "do fornecedor"}`;
    const rot = c => c.rotulo === "vigente" ? "vigente" : "outro";
    if (!cheio) return `<div class="psd-fobl">${it.preco != null ? `<span class="psd-fob-min" title="${esc([`Fornecedor do item: ${it.fornecedor || "—"}`, fonte, varia].filter(Boolean).join(", "))}">${nf(it.preco, 2)}</span>` : `<span class="text-xs text-mute">${semItem}</span>`}
      <span class="text-xs text-mute">${esc(it.fornecedor || "")}${it.planilha != null ? `, planilha ${nf(it.planilha, 2)}` : ""}</span>
      ${cmp.map(c => `<span class="text-xs text-ink" title="${c.rotulo === "vigente" ? "Fornecedor da última compra (planilha FOB)" : "Outro fornecedor (planilha FOB)"}">${rot(c)} ${esc(c.fornecedor)} ${c.preco != null ? nf(c.preco, 2) : "sem FOB"}</span>`).join("")}</div>`;
    return `<div class="psd-fobrd">
      <div class="psd-fobrd-c on"><small>Fornecedor do item, ${esc(it.fornecedor || "—")}</small><b>${it.preco != null ? usd(it.preco) : semItem}</b><small>${[fonte, it.planilha != null ? `planilha: ${nf(it.planilha, 2)}` : "", varia].filter(Boolean).join(", ")}</small></div>
      ${cmp.map(c => `<div class="psd-fobrd-c"><small>${c.rotulo === "vigente" ? "Vigente (última compra)" : "Outro fornecedor"}, ${esc(c.fornecedor)}</small><b>${c.preco != null ? usd(c.preco) : "sem FOB"}</b><small>planilha FOB</small></div>`).join("")}
      ${cmp.length ? "" : '<div class="psd-fobrd-c vazio"><small>Comparação</small><b>–</b><small>nenhum outro fornecedor com FOB na planilha</small></div>'}</div>`;
  };

  /* ---------- sugestões do app no lugar da lista nativa (etapa 22) ----------
     O Chrome/Edge desenham a lista do <datalist> e o histórico dos campos de busca com a cor do WINDOWS, não com o tema do app: no modo claro com o
     Windows escuro as opções saíam escuras. Agora todo <input list="…"> mostra .psd-sug (cores do tema), lendo as <option> do próprio datalist — as
     telas continuam só preenchendo o datalist. ↑/↓ escolhem, Enter usa a opção marcada (sem marcar, o Enter segue para a tela), Esc fecha.
     Campos de busca ficam sem o histórico do navegador (autocomplete=off). */
  (() => {
    let s = null, escolhendo = false;
    const fechar = () => { if (!s) return; s.obs.disconnect(); s.box.remove(); s.inp.setAttribute("aria-expanded", "false"); s.inp.removeAttribute("aria-activedescendant"); s = null; };
    const opcoes = () => [...s.dl.querySelectorAll("option")].map(o => ({ v: o.value, l: o.textContent.trim() !== o.value ? o.textContent.trim() : "" })).filter(o => o.v);
    const posicionar = () => {
      const r = s.inp.getBoundingClientRect(), b = s.box; b.style.minWidth = Math.max(r.width, 224) + "px"; b.style.left = r.left + "px"; b.style.top = r.bottom + 4 + "px";
      const a = b.getBoundingClientRect(), dx = a.left - r.left, dy = a.top - (r.bottom + 4);          // dentro de um <dialog> com transform o «fixed» é relativo a ele: corrige
      let top = r.bottom + 4 - dy; if (a.height && r.bottom + 4 + a.height > innerHeight - 8 && r.top - a.height - 4 > 8) top = r.top - a.height - 4 - dy;
      b.style.left = Math.min(r.left, innerWidth - a.width - 8) - dx + "px"; b.style.top = top + "px";
    };
    const pintar = () => {
      if (!s) return; const t = s.inp.value.trim().toUpperCase();
      const ops = opcoes().filter(o => (o.v + " " + o.l).toUpperCase().includes(t)).slice(0, 60);
      s.ops = ops;
      if (!ops.length || (ops.length === 1 && ops[0].v.toUpperCase() === t)) { s.box.hidden = true; s.inp.setAttribute("aria-expanded", "false"); return; }
      if (s.idx >= ops.length) s.idx = -1;
      s.box.innerHTML = ops.map((o, i) => `<div role="option" id="psd-sug-${i}" aria-selected="${i === s.idx}" class="psd-sug-o${i === s.idx ? " on" : ""}" data-i="${i}"><b>${esc(o.v)}</b>${o.l ? `<span>${esc(o.l)}</span>` : ""}</div>`).join("");
      s.box.hidden = false; s.inp.setAttribute("aria-expanded", "true");
      if (s.idx >= 0) { s.inp.setAttribute("aria-activedescendant", "psd-sug-" + s.idx); s.box.children[s.idx].scrollIntoView({ block: "nearest" }); } else s.inp.removeAttribute("aria-activedescendant");
      posicionar();
    };
    const escolher = i => {
      const inp = s.inp, v = s.ops[i].v; fechar(); inp.value = v; escolhendo = true;
      try { inp.dispatchEvent(new Event("input", { bubbles: true })); inp.dispatchEvent(new Event("change", { bubbles: true })); } finally { escolhendo = false; }
      inp.focus();
    };
    const abrir = inp => {
      if (s && s.inp === inp) return; fechar();
      if (inp.hasAttribute("list")) { inp.dataset.psdList = inp.getAttribute("list"); inp.removeAttribute("list"); }          // sem «list», o navegador não abre a lista dele
      const dl = document.getElementById(inp.dataset.psdList); if (!dl) return;
      inp.setAttribute("autocomplete", "off"); inp.setAttribute("role", "combobox"); inp.setAttribute("aria-autocomplete", "list"); inp.setAttribute("aria-controls", "psd-sug");
      const box = Object.assign(document.createElement("div"), { id: "psd-sug", className: "psd-sug", hidden: true }); box.setAttribute("role", "listbox");
      (inp.closest("dialog") || document.body).appendChild(box);
      box.addEventListener("mousedown", e => { const o = e.target.closest("[data-i]"); e.preventDefault(); if (o) escolher(+o.dataset.i); });
      s = { inp, dl, box, idx: -1, ops: [], obs: new MutationObserver(() => pintar()) }; s.obs.observe(dl, { childList: true, subtree: true, characterData: true });
      pintar();
    };
    document.addEventListener("focusin", e => { const t = e.target; if (!(t instanceof HTMLInputElement)) return;
      if (t.hasAttribute("list") || t.dataset.psdList) abrir(t);
      else if (t.type === "search" || t.closest(".psd-search") || t.id === "navsearch") t.setAttribute("autocomplete", "off"); });
    document.addEventListener("focusout", e => { if (s && e.target === s.inp) setTimeout(() => { if (s && document.activeElement !== s.inp) fechar(); }, 120); });
    document.addEventListener("input", e => { const t = e.target; if (escolhendo || !(t instanceof HTMLInputElement) || !t.dataset.psdList) return;
      if (!s || s.inp !== t) abrir(t); else { s.idx = -1; pintar(); } });
    document.addEventListener("keydown", e => {          // captura: vem antes dos ouvintes do próprio campo (Enter da edição na célula, por exemplo)
      if (!s || e.target !== s.inp) return; const aberto = !s.box.hidden, n = s.ops.length;
      if ((e.key === "ArrowDown" || e.key === "ArrowUp") && n) { e.preventDefault(); if (!aberto) { pintar(); return; } s.idx = e.key === "ArrowDown" ? (s.idx + 1) % n : (s.idx <= 0 ? n - 1 : s.idx - 1); pintar(); }
      else if (e.key === "Enter" && aberto && s.idx >= 0) { e.preventDefault(); e.stopPropagation(); escolher(s.idx); }
      else if (e.key === "Escape" && aberto) { e.preventDefault(); e.stopPropagation(); s.box.hidden = true; s.inp.setAttribute("aria-expanded", "false"); }
    }, true);
    window.addEventListener("scroll", e => { if (!s || s.box.hidden || s.box.contains(e.target)) return;          // a lista acompanha a rolagem (a tabela rola ao focar o campo)
      const r = s.inp.getBoundingClientRect(); if (r.bottom < 0 || r.top > innerHeight) s.box.hidden = true; else posicionar(); }, true);
    window.addEventListener("resize", fechar);
  })();

  document.addEventListener("psd-theme", () => { tema(); vivos.forEach(g => { if (!g.canvas.isConnected) { vivos.delete(g); return; } pinta(g.config.type, g.data.datasets); g.config.clearCache?.(); g.update(); });
    _vivosSeg.forEach(el => el.isConnected ? _ajustaSeg(el) : _vivosSeg.delete(el)); });       // tinta do texto da barra segmentada muda com o tema
  /* ---------- etapa 24: chaves de escolha (.psd-seg, .psd-linha) — o destaque desliza até a opção escolhida (0,2 s) ----------
     Um único marcador (.psd-ind, com a faixa inclinada) fica atrás dos botões. A posição anterior de cada chave fica guardada pela identidade dela
     (id ou aria-label), então a animação aparece também quando a tela redesenha a chave (troca de aba, filtro). «Reduzir movimento» desliga (marca.css). */
  const ultimo = new Map(), CHAVES = ".psd-seg, .psd-linha";
  const posicionar = el => {
    const b = el.querySelector(':scope > button[aria-pressed="true"]'); let ind = el.querySelector(":scope > .psd-ind");
    if (!b) { if (ind) ind.style.opacity = "0"; return; }
    if (!ind) { ind = document.createElement("span"); ind.className = "psd-ind"; ind.setAttribute("aria-hidden", "true"); el.prepend(ind); el.classList.add("psd-anim"); }
    const r = { left: b.offsetLeft, top: b.offsetTop, width: b.offsetWidth, height: b.offsetHeight }, k = el.id || el.getAttribute("aria-label") || "";
    const px = o => Object.fromEntries(Object.entries(o).map(([a, x]) => [a, x + "px"]));
    if (!ind.dataset.pos) {           // marcador novo: começa onde a chave estava antes (mesma chave redesenhada) e desliza; sem histórico, aparece direto
      const antes = k && ultimo.get(k); ind.style.transition = "none"; Object.assign(ind.style, px(antes || r), { opacity: "1" }); void ind.offsetWidth; ind.style.transition = "";
    }
    Object.assign(ind.style, px(r), { opacity: "1" }); ind.dataset.pos = "1"; if (k) ultimo.set(k, r);
  };
  let fila = new Set(), agendado = false;
  const agenda = el => { fila.add(el); if (agendado) return; agendado = true; queueMicrotask(() => { agendado = false; const f = fila; fila = new Set(); f.forEach(x => x.isConnected && posicionar(x)); }); };
  const varrer = raiz => { if (raiz.nodeType !== 1) return; if (raiz.matches(CHAVES)) agenda(raiz); raiz.querySelectorAll(CHAVES).forEach(agenda); };
  if (typeof MutationObserver !== "undefined") {
    new MutationObserver(ms => ms.forEach(m => {
      if (m.type === "attributes") { const c = m.target.parentElement; if (c && c.matches(CHAVES)) agenda(c); }
      else { if (m.target.matches && m.target.matches(CHAVES)) agenda(m.target); m.addedNodes.forEach(varrer); }          // chave cujo conteúdo foi redesenhado (innerHTML)
    })).observe(document.documentElement, { subtree: true, childList: true, attributes: true, attributeFilter: ["aria-pressed"] });
    const inicio = () => varrer(document.body);
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", inicio); else inicio();
    addEventListener("resize", () => document.querySelectorAll(CHAVES).forEach(el => { const i = el.querySelector(":scope > .psd-ind"); if (i) { i.style.transition = "none"; posicionar(el); void i.offsetWidth; i.style.transition = ""; } }));
  }

  /* Zona de planilha (etapa 24 · update 4 · Q8): toda tela que recebe planilha usa a mesma caixa tracejada de Desenhos/Validação.
     Clique abre o seletor; arrastar e soltar; Ctrl+V cola um arquivo copiado no Explorer (enquanto a zona estiver na tela).
       zonaPlanilha({ id, titulo, dica, multiplo, aceita, compacta })  → html
       ligarPlanilha(el | "#id", { aceita, multiplo, receber(files) })   → files já filtrados pela extensão */
  const ACEITA = ".xlsx,.xls,.csv";
  const zonaPlanilha = ({ id, titulo = "Enviar planilha", dica, multiplo = false, aceita = ACEITA, compacta = true } = {}) =>
    `<label id="${id}" class="psd-drop${compacta ? " psd-drop-p" : ""}" tabindex="0">${ico("file-spreadsheet", "lg")}<b>${esc(titulo)}</b>
      <span>${esc(dica || `${aceita.replace(/\./g, "").toUpperCase().split(",").join(", ")}; arraste ${multiplo ? "os arquivos" : "o arquivo"} para cá, cole com Ctrl+V ou clique`)}</span>
      <input type="file" accept="${esc(aceita)}"${multiplo ? " multiple" : ""} hidden></label>`;
  const ligarPlanilha = (alvo, { aceita = ACEITA, multiplo = false, receber }) => {
    const z = typeof alvo === "string" ? document.querySelector(alvo) : alvo; if (!z) return;
    const exts = aceita.split(",").map(x => x.trim().toLowerCase()).filter(Boolean);
    const entrega = lista => { const fs = [...(lista || [])]; if (!fs.length) return;
      const ok = fs.filter(f => exts.some(x => f.name.toLowerCase().endsWith(x)));
      if (!ok.length) return toast(`Envie ${exts.join(", ")}: «${fs[0].name}» não é desse tipo.`, { tom: "aviso", titulo: "Arquivo não aceito" });
      if (ok.length < fs.length) toast(`${fs.length - ok.length} arquivo(s) de outro tipo ficaram de fora.`, { tom: "aviso" });
      receber(multiplo ? ok : ok.slice(0, 1)); };
    const inp = z.querySelector("input[type=file]");
    if (inp) inp.addEventListener("change", () => { entrega(inp.files); inp.value = ""; });
    z.addEventListener("keydown", e => { if ((e.key === "Enter" || e.key === " ") && inp && e.target === z) { e.preventDefault(); inp.click(); } });
    ["dragenter", "dragover"].forEach(n => z.addEventListener(n, e => { e.preventDefault(); z.classList.add("sobre"); }));
    z.addEventListener("dragleave", e => { if (!z.contains(e.relatedTarget)) z.classList.remove("sobre"); });
    z.addEventListener("drop", e => { e.preventDefault(); z.classList.remove("sobre"); entrega(e.dataTransfer && e.dataTransfer.files); });
    const colar = e => { if (!z.isConnected) return document.removeEventListener("paste", colar);          // a tela mudou: a zona saiu, o atalho também
      if (z.closest("[hidden]") || !z.offsetParent) return;
      const fs = e.clipboardData && e.clipboardData.files; if (!fs || !fs.length) return;          // texto colado num campo segue normal
      e.preventDefault(); entrega(fs); };
    document.addEventListener("paste", colar);
  };

  return { esc, nf, brl, brl0, dmy, badge, kpi, card, notice, empty, table, input, select, btn, csv, nome, filtros, ico, stripes, toast, confirmar, erro, editarCodigos, fobRD, enviar, carregando, esqueleto, grafico, CORES, curto, segmentos, medidor, rosca, anel, legenda, barra, pintarBarra, ligarBarra, botao, ops, etiquetas, zonaPlanilha, ligarPlanilha };
})();
