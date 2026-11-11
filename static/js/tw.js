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
  const ACC = { blue: "bg-blue-500", green: "bg-emerald-500", slate: "bg-slate-400", amber: "bg-amber-500", red: "bg-red-500" };
  const kpi = (label, value, sub = "", accent = "blue") => `<div class="relative overflow-hidden rounded-2xl border border-line bg-card p-5 shadow-sm"><span class="absolute inset-x-0 top-0 h-1 ${ACC[accent] || ACC.blue}"></span>
    <div class="text-xs font-semibold uppercase tracking-wide text-mute">${label}</div><div class="mt-2 break-words text-2xl font-bold leading-none text-ink xl:text-3xl">${value}</div>${sub ? `<div class="mt-2 text-sm text-mute">${sub}</div>` : ""}</div>`;
  const card = (title, body, right = "", cls = "") => `<section class="rounded-2xl border border-line bg-card p-5 shadow-sm ${cls}"><div class="mb-4 flex flex-wrap items-center justify-between gap-3"><h3 class="m-0 text-base font-semibold text-ink">${title}</h3>${right}</div>${body}</section>`;
  const notice = (t, tone = "blue") => `<div class="rounded-xl border px-4 py-3 text-sm ${{ blue: "border-blue-500/30 bg-blue-500/10 text-ink", amber: "border-amber-500/40 bg-amber-500/10 text-ink", red: "border-red-500/40 bg-red-500/10 text-ink" }[tone]}">${t}</div>`;
  const empty = t => `<div class="rounded-2xl border border-dashed border-line bg-card px-6 py-12 text-center text-sm text-mute">${t}</div>`;
  /* tabela minimalista: fundo do card, bordas sutis, hover nas linhas e rolagem vertical INTERNA (cabeçalho fixo) */
  const table = (cols, rows, o = {}) => `<div class="${o.h || "max-h-[60vh]"} overflow-y-auto overflow-x-auto rounded-xl border border-line bg-card"><table class="w-full border-collapse text-sm">
    <thead class="sticky top-0 z-10 bg-card"><tr class="border-b border-line">${cols.map(c => `<th class="whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wide text-mute ${c.r ? "text-right" : "text-left"}">${c.h}</th>`).join("")}</tr></thead>
    <tbody class="divide-y divide-line">${rows.length ? rows.map(r => `<tr class="hover:bg-slate-500/10">${r.map((v, i) => `<td class="px-4 py-2.5 text-ink ${cols[i].r ? "text-right tabular-nums" : ""} ${cols[i].nw === false ? "" : "whitespace-nowrap"}">${v}</td>`).join("")}</tr>`).join("") : `<tr><td class="px-4 py-10 text-center text-mute" colspan="${cols.length}">Nada encontrado com estes filtros.</td></tr>`}</tbody></table></div>`;
  const input = (id, ph, cls = "") => `<input id="${id}" type="search" placeholder="${ph}" class="w-full rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500 ${cls}">`;
  const select = (id, opts, cur = "", cls = "") => `<select id="${id}" class="rounded-lg border border-line bg-card px-3 py-2 text-sm text-ink outline-none focus:border-blue-500 ${cls}">${opts.map(([v, l]) => `<option value="${esc(v)}" ${String(v) === String(cur) ? "selected" : ""}>${esc(l)}</option>`).join("")}</select>`;
  const btn = (id, label, ghost = true) => `<button type="button" id="${id}" class="rounded-lg px-3.5 py-2 text-sm font-semibold ${ghost ? "border border-line bg-card text-ink hover:bg-slate-500/10" : "bg-blue-600 text-white hover:bg-blue-700"}">${label}</button>`;
  const csv = (name, head, rows) => { const q = v => '"' + String(v ?? "").replace(/"/g, '""') + '"'; const b = new Blob(["﻿" + [head, ...rows].map(r => r.map(q).join(";")).join("\r\n")], { type: "text/csv;charset=utf-8" }); const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(b), download: name }); document.body.appendChild(a); a.click(); a.remove(); };

  /* Estado dos filtros de uma tela (padrão de todas as telas migradas, etapa 16):
     · a URL manda (links e conectores abrem a tela já filtrada); sem filtros na URL, volta o último uso (localStorage, por tela);
     · set() grava na URL (sem recarregar) e no navegador; chip ativo clicado de novo = toggle() limpa o filtro.
     Uso: const F = PSDTW.filtros("desenvolvimento", ["q", "status", ...]);  F.get() → {chave: valor}; F.set({status: "X"}); F.toggle("flag", "pend_compras"); F.clear(); F.restaurado */
  const filtros = (tela, chaves) => {
    const key = "psd-filtros-" + tela, pick = o => Object.fromEntries(chaves.filter(k => o[k] != null && o[k] !== "").map(k => [k, String(o[k])]));
    const daUrl = pick(Object.fromEntries(new URLSearchParams(location.search)));
    let salvo = {}; try { salvo = pick(JSON.parse(localStorage.getItem(key) || "{}")); } catch (e) { }
    const restaurado = !Object.keys(daUrl).length && Object.keys(salvo).length > 0;
    let st = Object.keys(daUrl).length ? daUrl : salvo;
    const write = () => { const u = new URLSearchParams(st).toString(); history.replaceState(null, "", location.pathname + (u ? "?" + u : "") + location.hash); try { localStorage.setItem(key, JSON.stringify(st)); } catch (e) { } };
    write();
    return { restaurado, get: () => ({ ...st }), set: patch => { st = pick({ ...st, ...patch }); write(); }, toggle: (k, v) => { st = pick({ ...st, [k]: st[k] === String(v) ? "" : v }); write(); }, clear: () => { st = {}; write(); } };
  };
  return { esc, nf, brl, brl0, dmy, badge, kpi, card, notice, empty, table, input, select, btn, csv, filtros };
})();
