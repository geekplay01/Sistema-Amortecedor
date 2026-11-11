/* Gráficos do PERFECT Shock Data — motor próprio em SVG (sem dependências, sem CDN, funciona offline atrás do firewall).
   Gradientes reais nas barras/linhas/arcos, tooltips interativos, legendas claras e paleta executiva (azul cobalto, verde esmeralda, cinza chumbo).
   (Plotly não desenha barras com gradiente; por isso o motor é próprio — e o mesmo código serve aos temas claro e escuro.)
   API:  PSDCharts.gauge | funnel | bars | hbars | donut | line (elemento, opções) → Promise */
window.PSDCharts = (() => {
  const nf = n => (n == null || isNaN(n)) ? "–" : Number(n).toLocaleString("pt-BR", { maximumFractionDigits: 1 });
  const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  const esc = s => String(s ?? "").replace(/[&<>"]/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[m]));
  const short = (s, n) => { s = String(s ?? ""); return s.length > n ? s.slice(0, n - 1) + "…" : s; };
  const mlabel = (m, short) => { const p = String(m).split("-"); return p.length > 1 && /^\d{4}$/.test(p[0]) ? ["", "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"][+p[1]] + (short ? "" : "/" + p[0].slice(2)) : String(m); };
  // paleta executiva: cobalto, esmeralda, chumbo, âmbar, violeta, ciano, coral, ardósia
  const BASE = ["#2f6bff", "#10b981", "#64748b", "#f59e0b", "#8b5cf6", "#06b6d4", "#f43f5e", "#94a3b8"];
  const theme = () => ({ tx: css("--tx") || "#0f172a", mut: css("--mut") || "#64748b", line: css("--line") || "#e2e8f0", card: css("--card") || "#fff", dark: document.documentElement.getAttribute("data-theme") === "dark" });
  const mix = (hex, amt) => { const n = parseInt(hex.slice(1), 16), f = c => Math.max(0, Math.min(255, Math.round(c + (amt > 0 ? (255 - c) : c) * amt))); return "#" + [n >> 16, (n >> 8) & 255, n & 255].map(f).map(v => v.toString(16).padStart(2, "0")).join(""); };
  let uid = 0;
  const grad = (id, clr, vertical = true, a0 = 1, a1 = .62) => `<linearGradient id="${id}" x1="0" y1="0" x2="${vertical ? 0 : 1}" y2="${vertical ? 1 : 0}"><stop offset="0" stop-color="${mix(clr, .18)}" stop-opacity="${a0}"/><stop offset="1" stop-color="${clr}" stop-opacity="${a1}"/></linearGradient>`;

  // ---------- tooltip único, acompanhando o mouse ----------
  let tip = null;
  const tipEl = () => tip || (tip = Object.assign(document.body.appendChild(document.createElement("div")), { className: "ch-tip", hidden: true }));
  document.addEventListener("mousemove", e => {
    const t = e.target.closest && e.target.closest("[data-tip]"), el = tipEl();
    if (!t || !t.closest(".ch")) { el.hidden = true; return; }
    el.innerHTML = t.getAttribute("data-tip"); el.hidden = false;
    const w = el.offsetWidth, h = el.offsetHeight; el.style.left = Math.min(e.clientX + 14, innerWidth - w - 8) + "px"; el.style.top = Math.max(8, e.clientY - h - 12) + "px";
  });
  const tt = (title, rows) => esc(title) && `<b>${esc(title)}</b>` + rows.map(r => `<div><i style="background:${r[2] || "#64748b"}"></i><span>${esc(r[0])}</span><strong>${r[1]}</strong></div>`).join("");
  const tipAttr = (title, rows) => `data-tip="${tt(title, rows).replace(/"/g, "&quot;")}"`;

  // ---------- registro: redesenha ao trocar o tema ou redimensionar ----------
  const reg = new Map();
  const render = async (el, kind, o) => {
    if (!el) return; reg.set(el, [kind, o]); el.classList.add("ch");
    const so = Object.assign({}, o, { _w: Math.max(300, Math.min(el.clientWidth || 620, 1200)) });
    try { el.innerHTML = SVG[kind](so); } catch (e) { console.error("gráfico", kind, e); el.innerHTML = '<div class="ch-empty">Não foi possível desenhar o gráfico.</div>'; }
  };
  let rt = null; window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(() => reg.forEach(([k, o], el) => { if (document.body.contains(el)) render(el, k, o); else reg.delete(el); }), 200); });
  document.addEventListener("psd-theme", () => reg.forEach(([k, o], el) => { if (document.body.contains(el)) render(el, k, o); else reg.delete(el); }));

  const nice = v => { if (v <= 0) return 1; const e = Math.pow(10, Math.floor(Math.log10(v))), f = v / e; return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * e; };
  const legend = (c, items, x0, y) => { let lx = x0; return items.map(([n, clr]) => { const x = lx; lx += 36 + String(n).length * 7.4; return `<rect x="${x}" y="${y - 9}" width="10" height="10" rx="3" fill="${clr}"/><text x="${x + 15}" y="${y}" font-size="11.5" fill="${c.tx}">${esc(n)}</text>`; }).join(""); };
  const rtop = (x, y, w, h, r) => { r = Math.min(r, w / 2, h); return h <= 0 ? "" : `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`; };

  const SVG = {
    gauge(o) {
      const c = theme(), id = "g" + (++uid), W = 300, cx = 150, cy = 156, r = 104, sw = 20, tgt = o.target || 0, v = o.value || 0, frac = tgt ? Math.min(v / tgt, 1) : 0, ok = tgt && v >= tgt, clr = ok ? "#10b981" : "#2f6bff";
      const pt = (f, rr = r) => { const a = Math.PI * (1 - f); return [cx + rr * Math.cos(a), cy - rr * Math.sin(a)]; }, arc = f => { const [x, y] = pt(f); return `M${cx - r},${cy} A${r},${r} 0 0 1 ${x.toFixed(1)},${y.toFixed(1)}`; };
      const [tx0, ty0] = pt(1, r - sw / 2 - 4), [tx1, ty1] = pt(1, r + sw / 2 + 4), [ex, ey] = pt(frac);
      return `<svg viewBox="0 0 ${W} 196" role="img" aria-label="${esc(o.title)}: ${nf(v)} de ${nf(tgt)}"><defs>${grad(id, clr, false, .75, 1)}<filter id="${id}s" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="${clr}" flood-opacity=".35"/></filter></defs>
        ${o.title ? `<text x="${cx}" y="16" text-anchor="middle" font-weight="700" font-size="13" fill="${c.tx}">${esc(o.title)}</text>` : ""}${o.subtitle ? `<text x="${cx}" y="32" text-anchor="middle" font-size="10.5" fill="${c.mut}">${esc(short(o.subtitle, 56))}</text>` : ""}
        <path d="${arc(1)}" fill="none" stroke="${c.line}" stroke-width="${sw}" stroke-linecap="round"/>
        ${frac > 0 ? `<path d="${arc(frac)}" fill="none" stroke="url(#${id})" stroke-width="${sw}" stroke-linecap="round" filter="url(#${id}s)" ${tipAttr(o.title || "Meta", [["Realizado", nf(v), clr], ["Meta", nf(tgt), "#64748b"], ["Atingido", nf(tgt ? Math.round(1000 * v / tgt) / 10 : 0) + "%", clr]])}/><circle cx="${ex.toFixed(1)}" cy="${ey.toFixed(1)}" r="4.5" fill="#fff" stroke="${clr}" stroke-width="2"/>` : ""}
        ${tgt ? `<line x1="${tx0}" y1="${ty0}" x2="${tx1}" y2="${ty1}" stroke="${c.mut}" stroke-width="2"/>` : ""}
        <text x="${cx}" y="${cy - 14}" text-anchor="middle" font-size="40" font-weight="800" fill="${c.tx}">${nf(v)}</text>
        <text x="${cx}" y="${cy + 6}" text-anchor="middle" font-size="12" fill="${c.mut}">${tgt ? "de " + nf(tgt) + " · " + nf(Math.round(1000 * v / tgt) / 10) + "%" : ""}</text>
        <text x="${cx - r}" y="${cy + 24}" text-anchor="middle" font-size="10" fill="${c.mut}">0</text><text x="${cx + r}" y="${cy + 24}" text-anchor="middle" font-size="10" fill="${c.mut}">${nf(tgt)}</text></svg>`;
    },
    funnel(o) {
      const c = theme(), id = "f" + (++uid), W = o._w || 560, Lw = Math.min(250, W * .42), barW = W - Lw - 36, rowH = 40, max = Math.max(...o.values, 1), H = o.labels.length * rowH + 8, pal = o.colors || BASE;
      const defs = o.labels.map((_, i) => grad(id + i, pal[i % pal.length], false, .95, .7)).join("");
      return `<svg viewBox="0 0 ${W} ${H}" role="img"><defs>${defs}</defs>${o.labels.map((l, i) => { const v = o.values[i], w = Math.max(v / max * barW, 46), x = Lw + 10, y = i * rowH + 4, prev = i ? o.values[i - 1] : null;
        return `<g ${tipAttr(l, [["Itens", nf(v), pal[i % pal.length]], ...(prev ? [["vs. etapa anterior", nf(Math.round(1000 * v / prev) / 10) + "%", "#64748b"]] : [])])}><text x="${Lw}" y="${y + 23}" text-anchor="end" font-size="12" fill="${c.tx}">${esc(short(l, Math.floor((Lw - 6) / 7.2)))}</text>
          <rect class="hov" x="${x.toFixed(1)}" y="${y}" width="${w.toFixed(1)}" height="${rowH - 8}" rx="8" fill="url(#${id + i})"/><text x="${(x + w / 2).toFixed(1)}" y="${y + 23}" text-anchor="middle" font-size="12.5" font-weight="700" fill="#fff" style="paint-order:stroke;stroke:rgba(15,23,42,.35);stroke-width:2px">${nf(v)}</text></g>`; }).join("")}</svg>`;
    },
    bars(o) {
      const c = theme(), id = "b" + (++uid), pal = o.colors || BASE, W = o._w || 620, H = o.height || 280, L = 44, R = 10, T = o.series.length > 1 ? 34 : 14, B = 30, pw = W - L - R, ph = H - T - B, n = o.x.length;
      const clrs = o.series.map((s, j) => s.color || pal[j % pal.length]);
      const tot = o.x.map((_, i) => o.stacked ? o.series.reduce((a, s) => a + (s.y[i] || 0), 0) : Math.max(...o.series.map(s => s.y[i] || 0)));
      const ymax = nice(Math.max(...tot, 1)), gw = pw / n, bw = o.stacked ? gw * .6 : Math.min(gw * .74 / o.series.length, 38);
      let g = ""; for (let k = 0; k <= 4; k++) { const y = T + ph - ph * k / 4; g += `<line x1="${L}" x2="${W - R}" y1="${y}" y2="${y}" stroke="${c.line}" ${k ? 'stroke-dasharray="3 5"' : ""}/><text x="${L - 8}" y="${y + 4}" text-anchor="end" font-size="10.5" fill="${c.mut}">${nf(ymax * k / 4)}</text>`; }
      const bars = o.x.map((x, i) => { let acc = 0; const hit = `<rect x="${L + i * gw}" y="${T}" width="${gw}" height="${ph}" fill="transparent" ${tipAttr(mlabel(x), o.series.map((s, j) => [s.name, nf(s.y[i] || 0), clrs[j]]))}/>`;
        return hit + o.series.map((s, j) => { const v = s.y[i] || 0, h = ph * v / ymax, bx = o.stacked ? L + i * gw + (gw - bw) / 2 : L + i * gw + (gw - bw * o.series.length) / 2 + j * bw, by = o.stacked ? T + ph - ph * (acc + v) / ymax : T + ph - h; acc += v;
          return v ? `<path class="hov" d="${rtop(+bx.toFixed(1), +by.toFixed(1), +(bw - (o.stacked ? 0 : 3)).toFixed(1), +h.toFixed(1), 6)}" fill="url(#${id + j})" pointer-events="none"/>` + (o.labels && !o.stacked && n <= 14 ? `<text x="${(bx + (bw - 3) / 2).toFixed(1)}" y="${(by - 5).toFixed(1)}" text-anchor="middle" font-size="10" font-weight="600" fill="${c.mut}" pointer-events="none">${nf(v)}</text>` : "") : ""; }).join("") + `<text x="${L + i * gw + gw / 2}" y="${H - 10}" text-anchor="middle" font-size="10.5" fill="${c.mut}">${esc(mlabel(x, n > 8 && W < 760))}</text>`; }).join("");
      return `<svg viewBox="0 0 ${W} ${H}" role="img"><defs>${clrs.map((k, j) => grad(id + j, k)).join("")}</defs>${g}${bars}${o.series.length > 1 ? legend(c, o.series.map((s, j) => [s.name, clrs[j]]), L, 14) : ""}</svg>`;
    },
    hbars(o) {
      const c = theme(), id = "h" + (++uid), W = o._w || 620, rowH = 32, max = Math.max(...o.values, 1), H = o.labels.length * rowH + 10, L = Math.min(280, W * .42), clr = o.color || "#2f6bff", tot = o.values.reduce((a, b) => a + b, 0) || 1;
      return `<svg viewBox="0 0 ${W} ${H}" role="img"><defs>${grad(id, clr, false, .7, 1)}</defs>${o.labels.map((l, i) => { const w = Math.max((W - L - 70) * o.values[i] / max, 3), y = i * rowH + 4;
        return `<g ${tipAttr(l, [["Quantidade", nf(o.values[i]), clr], ["Participação", nf(Math.round(1000 * o.values[i] / tot) / 10) + "%", "#64748b"]])}><rect x="0" y="${y - 2}" width="${W}" height="${rowH - 4}" fill="transparent"/><text x="${L - 10}" y="${y + 17}" text-anchor="end" font-size="12" fill="${c.tx}">${esc(short(l, Math.floor((L - 14) / 7.2)))}</text>
          <rect x="${L}" y="${y + 3}" width="${(W - L - 70).toFixed(1)}" height="${rowH - 12}" rx="${(rowH - 12) / 2}" fill="${c.line}" opacity=".45"/><rect class="hov" x="${L}" y="${y + 3}" width="${w.toFixed(1)}" height="${rowH - 12}" rx="${(rowH - 12) / 2}" fill="url(#${id})"/><text x="${L + (W - L - 70) + 10}" y="${y + 17}" font-size="12" font-weight="700" fill="${c.tx}">${nf(o.values[i])}</text></g>`; }).join("")}</svg>`;
    },
    donut(o) {
      const c = theme(), id = "d" + (++uid), pal = o.colors || BASE, tot = o.values.reduce((a, b) => a + b, 0) || 1, cx = 100, cy = 100, R = 82, r = 54; let a0 = -Math.PI / 2;
      const P = (a, rr) => [cx + rr * Math.cos(a), cy + rr * Math.sin(a)];
      const seg = o.values.map((v, i) => { const ang = Math.min(2 * Math.PI * v / tot, 2 * Math.PI - .001), a1 = a0 + ang, [x0, y0] = P(a0, R), [x1, y1] = P(a1, R), [x2, y2] = P(a1, r), [x3, y3] = P(a0, r), lg = ang > Math.PI ? 1 : 0;
        const d = v ? `<path class="hov" d="M${x0.toFixed(1)},${y0.toFixed(1)}A${R},${R} 0 ${lg} 1 ${x1.toFixed(1)},${y1.toFixed(1)}L${x2.toFixed(1)},${y2.toFixed(1)}A${r},${r} 0 ${lg} 0 ${x3.toFixed(1)},${y3.toFixed(1)}Z" fill="url(#${id + i})" stroke="${c.card}" stroke-width="2" ${tipAttr(o.labels[i], [["Itens", nf(v), pal[i % pal.length]], ["Participação", nf(Math.round(1000 * v / tot) / 10) + "%", "#64748b"]])}/>` : ""; a0 = a1; return d; }).join("");
      const lg = o.labels.map((l, i) => `<g transform="translate(212 ${50 + i * 26})"><rect width="12" height="12" rx="4" fill="${pal[i % pal.length]}"/><text x="19" y="10.5" font-size="12.5" fill="${c.tx}">${esc(l)}</text><text x="19" y="10.5" dx="${String(l).length * 7.4 + 10}" font-size="12" fill="${c.mut}">${nf(o.values[i])} · ${Math.round(100 * o.values[i] / tot)}%</text></g>`).join("");
      return `<svg viewBox="0 0 470 200" role="img"><defs>${o.values.map((_, i) => grad(id + i, pal[i % pal.length], false, 1, .75)).join("")}</defs>${seg}<text x="${cx}" y="${cy + 2}" text-anchor="middle" font-size="24" font-weight="800" fill="${c.tx}">${nf(tot)}</text><text x="${cx}" y="${cy + 20}" text-anchor="middle" font-size="10.5" fill="${c.mut}">total</text>${lg}</svg>`;
    },
    line(o) {
      const c = theme(), id = "l" + (++uid), pal = o.colors || BASE, W = o._w || 620, H = o.height || 260, L = 44, R = 14, T = o.series.length > 1 ? 34 : 16, B = 30, pw = W - L - R, ph = H - T - B, n = o.x.length, ymax = nice(Math.max(...o.series.flatMap(s => s.y), 1));
      const px = i => L + (n > 1 ? pw * i / (n - 1) : pw / 2), py = v => T + ph - ph * v / ymax, clrs = o.series.map((s, j) => s.color || pal[j % pal.length]); let g = "";
      for (let k = 0; k <= 4; k++) { const y = T + ph - ph * k / 4; g += `<line x1="${L}" x2="${W - R}" y1="${y}" y2="${y}" stroke="${c.line}" ${k ? 'stroke-dasharray="3 5"' : ""}/><text x="${L - 8}" y="${y + 4}" text-anchor="end" font-size="10.5" fill="${c.mut}">${nf(ymax * k / 4)}</text>`; }
      const curve = ys => { const p = ys.map((v, i) => [px(i), py(v)]); if (p.length < 3) return "M" + p.map(q => q.join(",")).join("L"); let d = `M${p[0][0].toFixed(1)},${p[0][1].toFixed(1)}`; for (let i = 0; i < p.length - 1; i++) { const a = p[i - 1] || p[i], b = p[i], cc = p[i + 1], e = p[i + 2] || cc; d += `C${(b[0] + (cc[0] - a[0]) / 6).toFixed(1)},${(b[1] + (cc[1] - a[1]) / 6).toFixed(1)} ${(cc[0] - (e[0] - b[0]) / 6).toFixed(1)},${(cc[1] - (e[1] - b[1]) / 6).toFixed(1)} ${cc[0].toFixed(1)},${cc[1].toFixed(1)}`; } return d; };
      const lines = o.series.map((s, j) => { const d = curve(s.y); return `${o.fill !== false ? `<path d="${d}L${px(n - 1).toFixed(1)},${T + ph}L${px(0).toFixed(1)},${T + ph}Z" fill="url(#${id + j})"/>` : ""}<path d="${d}" fill="none" stroke="${clrs[j]}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`; }).join("");
      const hits = o.x.map((x, i) => `<g ${tipAttr(mlabel(x), o.series.map((s, j) => [s.name, nf(s.y[i]), clrs[j]]))}><rect x="${(px(i) - pw / n / 2).toFixed(1)}" y="${T}" width="${(pw / Math.max(n, 1)).toFixed(1)}" height="${ph}" fill="transparent"/>${o.series.map((s, j) => `<circle class="hov" cx="${px(i).toFixed(1)}" cy="${py(s.y[i]).toFixed(1)}" r="4" fill="${c.card}" stroke="${clrs[j]}" stroke-width="2.4"/>`).join("")}</g>`).join("");
      return `<svg viewBox="0 0 ${W} ${H}" role="img"><defs>${clrs.map((k, j) => `<linearGradient id="${id + j}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${k}" stop-opacity=".38"/><stop offset="1" stop-color="${k}" stop-opacity="0"/></linearGradient>`).join("")}</defs>${g}${lines}${hits}${o.x.map((x, i) => (n <= 12 || i % Math.ceil(n / 12) === 0) ? `<text x="${px(i)}" y="${H - 10}" text-anchor="middle" font-size="10.5" fill="${c.mut}">${esc(mlabel(x))}</text>` : "").join("")}${o.series.length > 1 ? legend(c, o.series.map((s, j) => [s.name, clrs[j]]), L, 14) : ""}</svg>`;
    },
  };

  return { ready: () => Promise.resolve(null), nf, palette: BASE, gauge: (e, o) => render(e, "gauge", o), funnel: (e, o) => render(e, "funnel", o), bars: (e, o) => render(e, "bars", o), hbars: (e, o) => render(e, "hbars", o), donut: (e, o) => render(e, "donut", o), line: (e, o) => render(e, "line", o) };
})();
