/* Animação da tela inicial (etapa 20 · Q8, refeita no passo 7): amortecedor semi-estrutural em 3D, desenhado num <canvas> por cima das faixas da marca (SVG).
   Peças, de cima para baixo: ponta roscada, haste cromada, vedação, guia ranhurada, corpo preto com a etiqueta FORCE GAS enrolada no tubo e o olhal com bucha.
   Projeção ortográfica, vista um pouco de cima (tampas em elipse). O tubo é um cilindro de verdade: cada coluna do corpo pega a fatia da etiqueta que está
   naquele ângulo, então ela curva nas bordas e corre em volta quando gira; um brilho holográfico passa pelas partes claras. O olhal muda com o giro:
   de lado é o bloco com o tubo da bucha (como no desenho técnico); de frente mostra o anel, a bucha e o furo.
   Roteiro do vídeo: tomba, gira duas voltas no próprio eixo e termina em pé, 13,1 s em ciclo. Com «reduzir movimento» fica parado, em pé.
   window.PSDSA.pose(segundos) congela num instante; pose(null) volta a animar (conferência). */
(function () {
  const cv = document.querySelector(".psd-sa canvas"); if (!cv) return;
  const ctx = cv.getContext("2d");
  const VB = [120, 30, 640, 580], PIV = [460, 360], ESC = .9, CICLO = 13.1, GIRO = .76, VOLTAS = 2, K = .2;   // ESC: escala da peça (a ponta fica abaixo do nome); K: achatamento das tampas
  const TOMBA = [[0, -58], [.13, -30], [.26, 42], [.38, 36], [.5, -12], [.63, -40], [.76, 0], [.92, 0], [1, -58]];
  const R = 30, CORPO = [-104, 160], ETQ = [-28, 92], OLHAL = 222;                                    // raio e trecho do corpo, trecho da etiqueta, centro do olhal
  const suave = p => .5 - .5 * Math.cos(Math.PI * p);
  function tomba(f) {
    for (let i = 0; i < TOMBA.length - 1; i++) { const [f0, a0] = TOMBA[i], [f1, a1] = TOMBA[i + 1]; if (f <= f1) return (a0 + (a1 - a0) * suave((f - f0) / (f1 - f0))) * Math.PI / 180; }
    return TOMBA[0][1] * Math.PI / 180;
  }
  function giro(f) { if (f >= GIRO) return 0; const u = f / GIRO; return 2 * Math.PI * VOLTAS * (u - Math.sin(2 * Math.PI * u) / (2 * Math.PI)); }

  // materiais: paradas de cor através do cilindro (da esquerda para a direita; a luz vem do alto à esquerda)
  const PRETO = [[0, "#040507"], [.16, "#191c22"], [.27, "#3e4450"], [.32, "#8e97a7"], [.36, "#3a404b"], [.6, "#15181d"], [.86, "#0c0e12"], [.95, "#22262e"], [1, "#050608"]];
  const CROMO = [[0, "#565e6c"], [.2, "#c9d0da"], [.33, "#ffffff"], [.45, "#b3bac6"], [.7, "#68707e"], [.88, "#a0a8b5"], [1, "#454c58"]];
  const ACO = [[0, "#3c424c"], [.3, "#9aa2ae"], [.4, "#c3c9d2"], [.7, "#5d6470"], [1, "#30353d"]];
  const ZINCO = [[0, "#6b7180"], [.3, "#d6dae2"], [.42, "#f3f5f8"], [.7, "#8c93a0"], [1, "#565c68"]];
  const BORRACHA = [[0, "#0b0c0e"], [.3, "#34373d"], [.6, "#1b1d21"], [1, "#08090a"]];
  const grad = (st, x0, y0, x1, y1) => { const g = ctx.createLinearGradient(x0, y0, x1, y1); st.forEach(([o, c]) => g.addColorStop(o, c)); return g; };
  let escuro = false;
  const contorno = () => { if (escuro) { ctx.strokeStyle = "rgba(150,172,225,.55)"; ctx.lineWidth = .9; ctx.stroke(); } };

  // tronco de cilindro com eixo no comprimento: lado + borda de baixo curva (a de cima fica sob a tampa)
  function lado(y0, y1, r0, r1) { ctx.beginPath(); ctx.moveTo(-r0, y0); ctx.lineTo(-r1, y1); ctx.ellipse(0, y1, r1, r1 * K, 0, Math.PI, 0, true); ctx.lineTo(r0, y0); ctx.ellipse(0, y0, r0, r0 * K, 0, 0, Math.PI, true); ctx.closePath(); }
  function peca(y0, y1, r0, r1, st) { const m = Math.max(r0, r1); lado(y0, y1, r0, r1); ctx.fillStyle = grad(st, -m, 0, m, 0); ctx.fill(); contorno(); }
  function tampa(y, r, st) { ctx.beginPath(); ctx.ellipse(0, y, r, r * K, 0, 0, 2 * Math.PI); ctx.fillStyle = grad(st, -r, 0, r, 0); ctx.fill(); contorno(); }
  function sulco(y, r, a) { ctx.beginPath(); ctx.ellipse(0, y, r, r * K, 0, 0, Math.PI); ctx.strokeStyle = `rgba(0,0,0,${a})`; ctx.lineWidth = 1.1; ctx.stroke();
    ctx.beginPath(); ctx.ellipse(0, y + 1.1, r, r * K, 0, 0, Math.PI); ctx.strokeStyle = "rgba(255,255,255,.13)"; ctx.lineWidth = .7; ctx.stroke(); }
  const TAMPA = [[0, "#16191e"], [.35, "#4b525e"], [.6, "#2a2e36"], [1, "#0e1014"]];

  // etiqueta: a imagem é girada 90° (o texto corre ao longo do tubo, de baixo para cima) e cada coluna do corpo recebe a fatia do ângulo que ela mostra
  let rot = null, holo = null; const img = new Image(), camada = document.createElement("canvas"), lc = camada.getContext("2d");
  img.onload = () => { const c = document.createElement("canvas"); c.width = img.height; c.height = img.width; const g = c.getContext("2d"); g.translate(0, img.width); g.rotate(-Math.PI / 2); g.drawImage(img, 0, 0);
    rot = c; holo = document.createElement("canvas"); holo.width = c.width; holo.height = c.height; pedir(); };
  img.src = cv.dataset.etiqueta;
  // holográfico: arco-íris suave que corre pela etiqueta com o giro e o tombo; em «overlay» o preto não muda, só as letras e os frisos brilham
  function holografico(phi, ang) {
    const h = holo.getContext("2d"), W = holo.width, H = holo.height, P = H / 2.4, off = ((phi * 120 + ang * 260) % P + P) % P, cores = ["#ff4d6d", "#ffd23f", "#3ee08f", "#3fa7ff", "#b06bff"];
    h.globalCompositeOperation = "source-over"; h.clearRect(0, 0, W, H); h.drawImage(rot, 0, 0);
    const g = h.createLinearGradient(0, -P + off, W, -P + off + 4 * P); for (let i = 0; i <= 20; i++) g.addColorStop(i / 20, cores[i % 5]);
    h.globalCompositeOperation = "overlay"; h.globalAlpha = .3; h.fillStyle = g; h.fillRect(0, 0, W, H); h.globalAlpha = 1;
    h.globalCompositeOperation = "destination-in"; h.drawImage(rot, 0, 0); h.globalCompositeOperation = "source-over";
  }
  function etiqueta(phi, ang) {
    if (!rot) return;
    holografico(phi, ang);
    if (camada.width !== cv.width || camada.height !== cv.height) { camada.width = cv.width; camada.height = cv.height; }
    lc.setTransform(1, 0, 0, 1, 0, 0); lc.clearRect(0, 0, camada.width, camada.height); lc.setTransform(ctx.getTransform());
    const L = ETQ[1] - ETQ[0], beta = L * holo.width / holo.height / R, s = .5;   // beta: arco coberto (rad), pela proporção da etiqueta
    for (let x = -R + s / 2; x < R; x += s) {
      const th = Math.asin(x / R); let psi = th - phi; psi = Math.atan2(Math.sin(psi), Math.cos(psi));
      if (Math.abs(psi) >= beta / 2) continue;
      const sw = Math.min(holo.width, Math.max(1, holo.width * s / (R * Math.cos(th)) / beta)), sx = Math.max(0, Math.min(holo.width - sw, (psi + beta / 2) / beta * holo.width - sw / 2));
      lc.drawImage(holo, sx, 0, sw, holo.height, x - s / 2, ETQ[0], s + .35, L);
    }
    // sombra do cilindro e reflexo do verniz, só sobre a etiqueta (source-atop)
    const g = lc.createLinearGradient(-R, 0, R, 0);
    [[0, "rgba(0,0,0,.82)"], [.17, "rgba(0,0,0,.3)"], [.3, "rgba(255,255,255,.08)"], [.33, "rgba(255,255,255,.32)"], [.37, "rgba(255,255,255,.05)"], [.55, "rgba(0,0,0,0)"], [.82, "rgba(0,0,0,.4)"], [1, "rgba(0,0,0,.85)"]].forEach(([o, c]) => g.addColorStop(o, c));
    lc.globalCompositeOperation = "source-atop"; lc.fillStyle = g; lc.fillRect(-R, ETQ[0], 2 * R, L); lc.globalCompositeOperation = "source-over";
    const m = ctx.getTransform(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.drawImage(camada, 0, 0); ctx.setTransform(m);
  }

  // olhal: anel com bucha cujo eixo fica atravessado ao amortecedor e gira junto (phi); de lado é um bloco, de frente mostra a face do anel
  function olhal(phi) {
    const c = Math.cos(phi), sn = Math.sin(phi), ax = Math.max(Math.abs(sn), .015), fr = sn >= 0 ? 1 : -1;
    const RA = 26, RB = 16.5, RT = 8.5, W = 34, LT = 52, y = OLHAL;         // raio do anel, da bucha e do tubo; largura do anel e comprimento do tubo
    const elipse = (x, r) => { ctx.beginPath(); ctx.ellipse(x, y, r * ax, r, 0, 0, 2 * Math.PI); };
    const casco = (a0, a1, r, st) => { const x0 = a0 * c, x1 = a1 * c; ctx.beginPath(); ctx.ellipse(x0, y, r * ax, r, 0, 0, 2 * Math.PI); ctx.ellipse(x1, y, r * ax, r, 0, 0, 2 * Math.PI);
      ctx.rect(Math.min(x0, x1), y - r, Math.abs(x1 - x0), 2 * r); ctx.fillStyle = grad(st, 0, y - r, 0, y + r); ctx.fill("nonzero"); };
    const aF = fr * W / 2, tF = fr * LT / 2;
    casco(-tF, -aF, RT, ZINCO);                                               // tubo da bucha, lado de trás
    casco(-aF, aF, RA, PRETO); if (escuro) { ctx.strokeStyle = "rgba(150,172,225,.5)"; ctx.lineWidth = .9; ctx.strokeRect(Math.min(-aF * c, aF * c), y - RA, Math.abs(2 * aF * c), 2 * RA); }
    const k = Math.round(20 + 52 * ax);                                       // face do anel: mais clara quanto mais virada para a frente
    elipse(aF * c, RA); ctx.fillStyle = `rgb(${k},${k + 4},${k + 10})`; ctx.fill(); contorno();
    elipse(aF * c, RA - 2.2); ctx.strokeStyle = "rgba(255,255,255,.14)"; ctx.lineWidth = .8; ctx.stroke();
    elipse(aF * c, RB); ctx.fillStyle = grad(BORRACHA, 0, y - RB, 0, y + RB); ctx.fill();
    casco(aF, tF, RT, ZINCO);                                                 // tubo da bucha, lado da frente
    elipse(tF * c, RT); ctx.fillStyle = "#e4e8ee"; ctx.fill(); elipse(tF * c, 3.4); ctx.fillStyle = "#15171b"; ctx.fill();
  }

  function quadro(f) {
    const ang = tomba(f), phi = giro(f); escuro = document.documentElement.dataset.theme === "dark";
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, cv.width, cv.height);
    const e = cv.width / VB[2]; ctx.setTransform(e, 0, 0, e, -VB[0] * e, -VB[1] * e); ctx.translate(PIV[0], PIV[1]); ctx.rotate(ang); ctx.scale(ESC, ESC);
    // de baixo para cima: cada peça cobre a tampa da de baixo
    peca(CORPO[1] + 8, OLHAL - 22, 14, 12, PRETO);                          // pescoço do olhal
    olhal(phi);
    peca(CORPO[1] - 4, CORPO[1] + 12, R, 17, PRETO);                         // fundo arredondado do tubo
    peca(CORPO[0], CORPO[1], R, R, PRETO);                                   // corpo
    etiqueta(phi, ang);
    if (escuro) { lado(CORPO[0], CORPO[1], R, R); contorno(); }
    peca(CORPO[0] - 26, CORPO[0] + 2, 33, 33, PRETO); sulco(CORPO[0] - 17, 33, .7); sulco(CORPO[0] - 8, 33, .7);   // guia ranhurada
    tampa(CORPO[0] - 26, 33, TAMPA); tampa(CORPO[0] - 26, 24, [[0, "#0c0e11"], [.4, "#2b3038"], [1, "#08090b"]]);
    peca(CORPO[0] - 33, CORPO[0] - 26, 12, 12, BORRACHA); tampa(CORPO[0] - 33, 12, BORRACHA);                        // vedação
    peca(CORPO[0] - 108, CORPO[0] - 33, 8, 8, CROMO);                                                              // haste cromada
    peca(CORPO[0] - 126, CORPO[0] - 108, 5.6, 5.6, ACO);                                                           // rosca
    for (let yy = CORPO[0] - 124; yy < CORPO[0] - 109; yy += 2.2) { ctx.beginPath(); ctx.ellipse(0, yy, 5.6, 5.6 * K, 0, 0, Math.PI); ctx.strokeStyle = "rgba(0,0,0,.45)"; ctx.lineWidth = .6; ctx.stroke(); }
    peca(CORPO[0] - 136, CORPO[0] - 126, 4.4, 4.4, ACO); tampa(CORPO[0] - 136, 4.4, ACO);                            // ponta
    ctx.fillStyle = "rgba(0,0,0,.6)"; ctx.fillRect(-.6, CORPO[0] - 136 - 4.4 * K, 1.2, 2 * 4.4 * K);              // fenda da ponta
  }

  const parado = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  let fixo = null, visivel = true, req = 0; const t0 = performance.now();
  function medir() { const b = cv.getBoundingClientRect(), d = window.devicePixelRatio || 1, w = Math.round(b.width * d), h = Math.round(b.height * d);
    if (w && h && (cv.width !== w || cv.height !== h)) { cv.width = w; cv.height = h; } }
  function passo(now) {
    req = 0; medir(); if (!cv.width) return;
    const seg = fixo != null ? fixo : parado ? CICLO * .8 : ((now - t0) / 1000) % CICLO;
    quadro(seg / CICLO);
    if (fixo == null && !parado && visivel) req = requestAnimationFrame(passo);
  }
  function pedir() { if (!req) req = requestAnimationFrame(passo); }
  if (window.ResizeObserver) new ResizeObserver(pedir).observe(cv);
  new MutationObserver(pedir).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  if (window.IntersectionObserver) new IntersectionObserver(es => { visivel = es[es.length - 1].isIntersecting; if (visivel) pedir(); }).observe(cv);
  window.PSDSA = { pose(seg) { fixo = seg == null ? null : +seg; if (fixo != null) { medir(); quadro(fixo / CICLO); } pedir(); } };
  pedir();
})();
