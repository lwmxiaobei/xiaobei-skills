// kids_scenes.js：场景库。每个场景 = 背景 bg + 前景 front（盖在角色前面）+ 能站人的位置 spots + 地图小图标 icon。
// 台本里场景写 "bg": "beach"，K.round 没给 cfg.bg 时自动用；自己写场景时：
//   K.layer(c, 'bg', g => P.bg(g, t, K.ambT(t), cam, ww))，角色画完再 K.layer(c, 'prop', g => P.front(g, t, amb, cam, ww), { top: P.frontTop })。
// 画法约定：所有东西按屏幕坐标画在 0..1920 里，sx = 镜头 x - 960 是镜头往右摇了多少。
// 近景（地面、能站人的东西）按世界坐标画：x - sx；远景按视差系数 k 画：x - sx * k（k 越小越远、动得越慢），
// 所以任何世界宽度 ww、镜头摇到哪都铺满屏幕，视差也不用多开图层。颜色全从 K.P 取。
// amb 是背景动画时间（安静时段放慢）；海鸥、鱼群、蝴蝶、气球这种会穿过画面的，透明度乘 K.lively(t)，单词卡和领念时淡出。
(() => {
const W = 1920, H = 1080, TAU = Math.PI * 2;
const h = (i, k) => U.hash(i + 1000, k);
const sxOf = cam => (cam && cam.x != null ? cam.x - 960 : 0);
K.lively = t => 1 - K.calm(t);

// ---------- 小工具 ----------
const grad = (g, y0, y1, stops) => { const gr = g.createLinearGradient(0, y0, 0, y1); stops.forEach((c, i) => gr.addColorStop(i / (stops.length - 1), c)); return gr; };
const sky = (g, y1, ...cols) => { g.fillStyle = grad(g, 0, y1, cols); g.fillRect(-20, -20, W + 40, H + 40); };
// 波浪形的地面：从 y 起往下铺满
const ground = (g, sx, k, y, amp, f, col) => {
  g.fillStyle = col; g.beginPath(); g.moveTo(-40, H + 40);
  for (let x = -40; x <= W + 40; x += 40) g.lineTo(x, y + amp * Math.sin((x + sx * k) * f));
  g.lineTo(W + 40, H + 40); g.closePath(); g.fill();
};
// 横向重复的东西：间隔 span，视差 k；fn(本地 x, 编号) 的编号跟着世界位置走，摇镜头时不会变
const rep = (sx, k, span, fn, x0 = 0) => {
  const a = Math.floor((sx * k - x0 - span) / span), b = Math.ceil((sx * k - x0 + W + span) / span);
  for (let i = a; i <= b; i++) fn(x0 + i * span - sx * k, i);
};
// 一团圆：蜡笔/扁平/剪纸画成一条路径（蜡笔只描外缘）；水彩的边缘积色、黏土的浮雕会沿每个子路径描线，整团一条路径会露出里面的整圈，所以逐个圆填（像 K.tree）
const blob = (g, pts, col) => {
  const M = K.TH.mat, each = M && (M.pool || M.emboss);
  g.fillStyle = col; g.beginPath();
  for (const [x, y, r] of pts) { if (each) g.beginPath(); g.moveTo(x + r, y); g.arc(x, y, r, 0, TAU); if (each) g.fill(); }
  if (!each) g.fill();
};
const tri = (g, x, y, w, hh, col) => { g.fillStyle = col; g.beginPath(); g.moveTo(x - w / 2, y); g.lineTo(x, y - hh); g.lineTo(x + w / 2, y); g.closePath(); g.fill(); };
const plain = (g, fn) => { const p = g.plain; g.plain = true; g.save(); g.shadowColor = 'transparent'; fn(); g.restore(); g.plain = p; };
const gull = (g, x, y, s, flap) => {
  g.strokeStyle = K.P.gull; g.lineWidth = 6 * s; g.lineCap = 'round'; g.beginPath();
  g.moveTo(x - 24 * s, y); g.quadraticCurveTo(x - 12 * s, y - (14 + flap) * s, x, y); g.quadraticCurveTo(x + 12 * s, y - (14 + flap) * s, x + 24 * s, y); g.stroke();
};
const fish = (g, x, y, s, col, dir = 1) => {
  g.fillStyle = col; g.beginPath(); g.ellipse(x, y, 26 * s, 14 * s, 0, 0, TAU); g.fill();
  g.beginPath(); g.moveTo(x - 20 * s * dir, y); g.lineTo(x - 42 * s * dir, y - 14 * s); g.lineTo(x - 42 * s * dir, y + 14 * s); g.closePath(); g.fill();
};
const bubble = (g, x, y, r) => { g.fillStyle = K.P.bubble; g.strokeStyle = K.P.bubbleRim; g.lineWidth = Math.max(2, r * 0.18); g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill(); g.stroke(); };
const pine = (g, x, y, s, c1, c2, snowy) => {
  g.fillStyle = K.P.trunk2; g.fillRect(x - 12 * s, y - 40 * s, 24 * s, 40 * s);
  for (let j = 0; j < 3; j++) { tri(g, x, y - 30 * s - j * 70 * s, (190 - j * 45) * s, 130 * s, j % 2 ? c2 : c1); if (snowy) tri(g, x, y - 30 * s - j * 70 * s - 95 * s, (60 - j * 12) * s, 35 * s, K.P.snow); }
};
const window_ = (g, x, y, w, hh, glassCol) => {
  g.fillStyle = K.P.frame; g.beginPath(); g.roundRect(x - w / 2 - 16, y - 16, w + 32, hh + 32, 18); g.fill();
  g.fillStyle = glassCol; g.beginPath(); g.roundRect(x - w / 2, y, w, hh, 10); g.fill();
  g.fillStyle = K.P.frame; g.fillRect(x - 7, y, 14, hh); g.fillRect(x - w / 2, y + hh / 2 - 7, w, 14);
};

// ---------- 场景 ----------
const PLACES = {};

PLACES.meadow = {
  zh: '草地', en: 'Meadow',
  frontTop: null,                                                // 前景只画在这条世界 y 以下（null = 没有前景）
  spots: { left: { x: 560, y: 980, s: 1.05 }, right: { x: 1300, y: 980, s: 1.05 }, back: { x: 960, y: 830, s: 0.82 }, branch: { x: 1560, y: 572, s: 0.7 } },
  bg(g, t, amb, cam) { const sx = sxOf(cam); K.meadow(g, amb, { scroll: sx }); K.tree(g, 1720 - sx, 330); },
  front() {},
  icon(g, x, y, r) { blob(g, [[x - r * 0.3, y + r * 0.5, r * 0.8], [x + r * 0.5, y + r * 0.6, r * 0.6]], K.P.grass); K.flower(g, x, y + r * 0.3, r / 60, K.P.flowers[0]); },
};

PLACES.beach = {
  zh: '海边', en: 'Beach',
  frontTop: 1000,
  spots: { left: { x: 560, y: 980, s: 1.05 }, right: { x: 1300, y: 980, s: 1.05 }, back: { x: 900, y: 830, s: 0.82 }, rock: { x: 1520, y: 772, s: 0.78 } },
  bg(g, t, amb, cam) {
    const P = K.P, sx = sxOf(cam);
    sky(g, 560, P.sky2, P.sky);
    g.fillStyle = P.sunGlow; g.beginPath(); g.arc(1500 - sx * 0.1, 210, 150, 0, TAU); g.fill();
    g.fillStyle = P.sun; g.beginPath(); g.arc(1500 - sx * 0.1, 210, 92, 0, TAU); g.fill();
    K.clouds(g, amb, sx, 3, 80);
    g.fillStyle = P.sea; g.fillRect(-20, 560, W + 40, 300);
    g.strokeStyle = P.sea2; g.lineWidth = 7; g.lineCap = 'round';
    for (let j = 0; j < 5; j++) rep(sx, 0.4 + j * 0.12, 300, (x, i) => {
      const y = 600 + j * 42, d = 30 * Math.sin(amb * 0.9 + i + j);
      g.beginPath(); g.moveTo(x + d, y); g.lineTo(x + d + 70 + 30 * h(i, j), y); g.stroke();
    }, j * 80);
    ground(g, sx, 1, 790, 10, 0.006, P.sand);
    const shore = 784 + 9 * Math.sin(amb * 1.4);
    g.fillStyle = P.foam; g.beginPath(); g.moveTo(-40, shore + 20);
    for (let x = -40; x <= W + 40; x += 40) g.lineTo(x, shore + 8 * Math.sin((x + sx) * 0.02 + amb * 2));
    g.lineTo(W + 40, shore + 20); g.closePath(); g.fill();
    plain(g, () => rep(sx, 1, 170, (x, i) => { g.fillStyle = P.sand2; g.beginPath(); g.ellipse(x, 860 + 160 * h(i, 3), 16, 5, 0, 0, TAU); g.fill(); }));
    // 沙堡、大石头、椰子树（世界坐标）
    const cx = 260 - sx; g.fillStyle = P.sand2;
    g.fillRect(cx - 90, 790, 180, 80); g.fillRect(cx - 50, 740, 100, 60);
    for (const d of [-90, -50, 10, 50]) g.fillRect(cx + d, d < 0 && d > -60 ? 724 : 774, 40, 22);
    const rx = 1520 - sx; g.fillStyle = P.rock2; g.beginPath(); g.ellipse(rx + 10, 830, 170, 70, 0, Math.PI, 0); g.fill();
    g.fillStyle = P.rock; g.beginPath(); g.ellipse(rx, 826, 150, 62, 0, Math.PI, 0); g.fill();
    const px = 1820 - sx; g.strokeStyle = P.trunk; g.lineWidth = 34; g.lineCap = 'round';
    g.beginPath(); g.moveTo(px, 860); g.quadraticCurveTo(px - 40, 600, px - 10, 330); g.stroke();
    for (let k = 0; k < 5; k++) {
      const a = -Math.PI + k * Math.PI / 4 + 0.05 * Math.sin(amb * 1.3 + k), droop = 40 * (1 - Math.abs(Math.sin(a)));
      g.fillStyle = k % 2 ? P.palm2 : P.palm; g.beginPath(); g.ellipse(px - 10 + Math.cos(a) * 105, 330 + Math.sin(a) * 70 + droop, 125, 30, a, 0, TAU); g.fill();
    }
    blob(g, [[px - 30, 350, 20], [px + 8, 356, 20]], P.trunk2);
    const lv = K.lively(t);
    if (lv > 0.01) { g.save(); g.globalAlpha *= lv; for (let k = 0; k < 2; k++) gull(g, K.wrap(amb * 70 + k * 900, W + 400) - 200, 170 + 60 * k, 1 - 0.2 * k, 10 * Math.sin(amb * 8 + k)); g.restore(); }
  },
  front(g, t, amb, cam) {
    const P = K.P, sx = sxOf(cam) * 1.2;
    plain(g, () => {
      K.star(g, 150 - sx, 1040, 30, 0.3, P.shells[0]); K.star(g, 1790 - sx, 1050, 26, -0.2, P.shells[1]);
      g.fillStyle = P.shells[2]; g.beginPath(); g.ellipse(250 - sx, 1055, 22, 16, 0, 0, TAU); g.fill();
    });
  },
  icon(g, x, y, r) { const P = K.P; g.fillStyle = P.sun; g.beginPath(); g.arc(x + r * 0.35, y - r * 0.3, r * 0.35, 0, TAU); g.fill(); g.fillStyle = P.sea; g.fillRect(x - r * 0.8, y + r * 0.05, r * 1.6, r * 0.3); g.fillStyle = P.sand; g.fillRect(x - r * 0.8, y + r * 0.35, r * 1.6, r * 0.35); },
};

PLACES.snow = {
  zh: '雪地', en: 'Snow',
  frontTop: 970,
  spots: { left: { x: 600, y: 980, s: 1.05 }, right: { x: 1320, y: 980, s: 1.05 }, back: { x: 1000, y: 830, s: 0.82 }, hill: { x: 330, y: 772, s: 0.78 } },
  bg(g, t, amb, cam) {
    const P = K.P, sx = sxOf(cam);
    sky(g, 780, P.snowSky, P.snow2);
    rep(sx, 0.15, 700, (x, i) => { const hh = 300 + 120 * h(i, 1); tri(g, x, 780, 760, hh, P.mountain[i % 2]); tri(g, x, 780 - hh * 0.62, 760 * 0.38, hh * 0.38, P.snow); });
    rep(sx, 0.5, 260, (x, i) => pine(g, x, 800, 0.8 + 0.3 * h(i, 2), P.pine, P.pine2, true), 60);
    ground(g, sx, 1, 790, 12, 0.005, P.snow);
    plain(g, () => rep(sx, 1, 220, (x, i) => { g.fillStyle = P.snow2; g.beginPath(); g.ellipse(x, 880 + 150 * h(i, 4), 60, 10, 0, 0, TAU); g.fill(); }));
    const mx = 330 - sx; g.fillStyle = P.snow2; g.beginPath(); g.ellipse(mx + 12, 870, 260, 104, 0, Math.PI, 0); g.fill();
    g.fillStyle = P.snow; g.beginPath(); g.ellipse(mx, 866, 240, 94, 0, Math.PI, 0); g.fill();
    const nx = 1830 - sx;                                                          // 雪人（靠右，让开右边站位）
    for (const [dy, r] of [[860, 80], [740, 60], [640, 46]]) { g.fillStyle = P.snow2; g.beginPath(); g.arc(nx + 6, dy + 6, r, 0, TAU); g.fill(); g.fillStyle = P.snow; g.beginPath(); g.arc(nx, dy, r, 0, TAU); g.fill(); }
    blob(g, [[nx - 16, 630, 6], [nx + 16, 630, 6], [nx, 730, 7], [nx, 760, 7]], P.coal);
    g.fillStyle = P.nose; g.beginPath(); g.moveTo(nx, 640); g.lineTo(nx + 46, 648); g.lineTo(nx, 654); g.closePath(); g.fill();
    g.fillStyle = P.flowers[0]; g.beginPath(); g.roundRect(nx - 52, 676, 104, 22, 10); g.fill(); g.fillRect(nx + 20, 690, 22, 50);
    plain(g, () => { g.fillStyle = P.snow; for (let i = 0; i < 46; i++) {
      const x = h(i, 5) * W + 24 * Math.sin(amb * 0.8 + i), y = K.wrap(h(i, 6) * H + amb * (40 + 40 * h(i, 7)), H + 40) - 20;
      g.beginPath(); g.arc(x, y, 4 + 5 * h(i, 8), 0, TAU); g.fill();
    } });
  },
  front(g, t, amb, cam) {
    const P = K.P, sx = sxOf(cam) * 1.2;
    g.fillStyle = P.snow; g.beginPath(); g.ellipse(60 - sx, 1090, 280, 110, 0, 0, TAU); g.ellipse(1880 - sx, 1100, 300, 120, 0, 0, TAU); g.fill();
  },
  icon(g, x, y, r) { const P = K.P; tri(g, x, y + r * 0.6, r * 1.6, r * 1.1, P.mountain[1]); tri(g, x, y - r * 0.1, r * 0.6, r * 0.4, P.snow); blob(g, [[x + r * 0.45, y + r * 0.35, r * 0.25], [x + r * 0.45, y + r * 0.02, r * 0.17]], P.snow); },
};

PLACES.night = {
  zh: '夜晚', en: 'Night', dark: true,
  frontTop: 880,
  spots: { left: { x: 560, y: 980, s: 1.05 }, right: { x: 1300, y: 980, s: 1.05 }, back: { x: 900, y: 830, s: 0.82 }, hill: { x: 300, y: 774, s: 0.78 } },
  bg(g, t, amb, cam) {
    const P = K.P, sx = sxOf(cam);
    sky(g, 780, P.night, P.night2);
    plain(g, () => { for (let i = 0; i < 44; i++) {
      const x = K.wrap(h(i, 1) * (W + 200) - sx * 0.08, W + 200) - 100, y = 40 + h(i, 2) * 520, tw = 0.55 + 0.45 * Math.sin(amb * (1.5 + h(i, 3) * 2) + i * 2);
      g.save(); g.globalAlpha *= tw; K.star(g, x, y, 5 + 9 * h(i, 4), 0, P.starLite); g.restore();
    } });
    const mx = 1560 - sx * 0.08; g.fillStyle = P.moonGlow; g.beginPath(); g.arc(mx, 200, 150, 0, TAU); g.fill();
    g.fillStyle = P.moon; g.beginPath(); g.arc(mx, 200, 84, 0, TAU); g.fill();
    rep(sx, 0.3, 900, (x, i) => { g.fillStyle = P.hillN[i % 2]; for (const [dx, y, rx, ry] of [[0, 800, 620, 190], [480, 810, 520, 150]]) { g.beginPath(); g.ellipse(x + dx, y, rx, ry, 0, 0, TAU); g.fill(); } });
    const hx = 1450 - sx * 0.7;                                                    // 亮着窗的小房子
    g.fillStyle = P.houseN; g.fillRect(hx - 110, 600, 220, 190);
    g.fillStyle = P.roofN; g.beginPath(); g.moveTo(hx - 140, 610); g.lineTo(hx, 500); g.lineTo(hx + 140, 610); g.closePath(); g.fill();
    g.fillStyle = P.glowWin; for (const d of [-55, 55]) { g.beginPath(); g.roundRect(hx + d - 30, 640, 60, 60, 8); g.fill(); }
    ground(g, sx, 1, 792, 9, 0.006, P.grassN);
    plain(g, () => rep(sx, 1, 140, (x, i) => { g.fillStyle = P.grassN2; g.beginPath(); g.ellipse(x, 850 + 190 * h(i, 5), 24, 7, 0, 0, TAU); g.fill(); }));
    const kx = 300 - sx; g.fillStyle = P.grassN2; g.beginPath(); g.ellipse(kx, 866, 250, 96, 0, Math.PI, 0); g.fill();
    for (let i = 0; i < 12; i++) {                                                  // 萤火虫：原地绕圈、一闪一闪
      const x = h(i, 6) * W + 60 * Math.sin(amb * 0.7 + i * 2), y = 560 + h(i, 7) * 330 + 30 * Math.sin(amb * 0.9 + i), a = 0.4 + 0.6 * Math.max(0, Math.sin(amb * 2.2 + i * 1.7));
      g.save(); g.globalAlpha *= a; g.fillStyle = P.fireflyGlow; g.beginPath(); g.arc(x, y, 20, 0, TAU); g.fill(); g.fillStyle = P.firefly; g.beginPath(); g.arc(x, y, 6, 0, TAU); g.fill(); g.restore();
    }
  },
  front(g, t, amb, cam) {
    const P = K.P, sx = sxOf(cam) * 1.2;
    g.fillStyle = P.grassN2;
    for (const [x0, n] of [[-30, 7], [1720, 7]]) {
      g.beginPath(); for (let k = 0; k < n; k++) { const x = x0 + k * 38 - sx, hh = 120 + 70 * h(k + x0, 9), b = 10 * Math.sin(amb * 1.2 + k); g.moveTo(x - 16, H + 10); g.quadraticCurveTo(x + b, H - hh * 0.6, x + b * 2, H - hh); g.quadraticCurveTo(x + 6 + b, H - hh * 0.6, x + 18, H + 10); }
      g.fill();
    }
  },
  icon(g, x, y, r) { const P = K.P; g.fillStyle = P.night; g.beginPath(); g.arc(x, y, r * 0.85, 0, TAU); g.fill(); g.fillStyle = P.moon; g.beginPath(); g.arc(x - r * 0.15, y - r * 0.1, r * 0.4, 0, TAU); g.fill(); K.star(g, x + r * 0.45, y - r * 0.4, r * 0.15, 0, P.starLite); },
};

PLACES.forest = {
  zh: '森林', en: 'Forest',
  frontTop: 850,
  spots: { left: { x: 560, y: 980, s: 1.05 }, right: { x: 1300, y: 980, s: 1.05 }, back: { x: 960, y: 830, s: 0.82 }, log: { x: 1560, y: 784, s: 0.78 } },
  bg(g, t, amb, cam) {
    const P = K.P, sx = sxOf(cam);
    sky(g, 800, P.forestSky, P.sky);
    rep(sx, 0.25, 230, (x, i) => { g.fillStyle = P.trunkFar; g.fillRect(x - 22, 260, 44, 560); blob(g, [[x, 260, 130 + 30 * h(i, 1)], [x - 90, 330, 90], [x + 90, 320, 95]], P.leafFar); });
    rep(sx, 0.6, 420, (x, i) => { g.fillStyle = P.trunk; g.fillRect(x - 34, 220, 68, 600); blob(g, [[x, 200, 170], [x - 130, 280, 120], [x + 130, 270, 125], [x, 330, 120]], i % 2 ? P.leaf2 : P.leaf); }, 140);
    ground(g, sx, 1, 792, 10, 0.007, P.grass);
    rep(sx, 1, 380, (x, i) => blob(g, [[x, 800, 70], [x + 60, 790, 56], [x - 60, 806, 50]], P.bush), 90);
    plain(g, () => rep(sx, 1, 160, (x, i) => { g.fillStyle = P.grass2; g.beginPath(); g.ellipse(x, 860 + 170 * h(i, 2), 22, 7, 0, 0, TAU); g.fill(); }));
    for (const [wx, s] of [[300, 1], [420, 0.7], [1250, 0.8]]) {                // 蘑菇
      const x = wx - sx; g.fillStyle = P.stem; g.fillRect(x - 14 * s, 836 - 50 * s, 28 * s, 50 * s);
      g.fillStyle = P.mushroom; g.beginPath(); g.ellipse(x, 836 - 50 * s, 52 * s, 40 * s, 0, Math.PI, 0); g.fill();
      plain(g, () => blob(g, [[x - 20 * s, 836 - 70 * s, 8 * s], [x + 16 * s, 836 - 76 * s, 7 * s], [x, 836 - 60 * s, 6 * s]], P.stem));
    }
    const lx = 1560 - sx; g.fillStyle = P.trunk2; g.beginPath(); g.roundRect(lx - 190, 784, 380, 84, 42); g.fill();
    g.fillStyle = P.trunk; g.beginPath(); g.ellipse(lx + 190, 826, 30, 42, 0, 0, TAU); g.fill();
    plain(g, () => { for (let i = 0; i < 10; i++) {                               // 落叶
      const x = h(i, 3) * W + 50 * Math.sin(amb * 1.1 + i), y = K.wrap(h(i, 4) * H + amb * (34 + 20 * h(i, 5)), H + 60) - 30;
      g.save(); g.translate(x, y); g.rotate(amb * 2 + i); g.fillStyle = P.fall[i % 3]; g.beginPath(); g.ellipse(0, 0, 16, 8, 0, 0, TAU); g.fill(); g.restore();
    } });
    const lv = K.lively(t);
    if (lv > 0.01) for (let k = 0; k < 2; k++) {                                   // 蝴蝶
      const x = K.wrap(amb * 55 + k * 1000, W + 300) - 150, y = 420 + 120 * k + 40 * Math.sin(amb * 2 + k), f = Math.abs(Math.sin(amb * 12 + k));
      g.save(); g.globalAlpha *= lv; g.fillStyle = P.wings[k]; g.beginPath(); g.ellipse(x - 12, y, 14 * f + 3, 18, -0.3, 0, TAU); g.ellipse(x + 12, y, 14 * f + 3, 18, 0.3, 0, TAU); g.fill(); g.restore();
    }
  },
  front(g, t, amb, cam) {
    const P = K.P, sx = sxOf(cam) * 1.2;
    for (const [x0, dir] of [[40, 1], [1880, -1]]) for (let k = 0; k < 4; k++) {
      g.save(); g.translate(x0 - sx, H + 20); g.rotate(dir * (-0.9 + k * 0.35) + 0.03 * Math.sin(amb + k)); g.fillStyle = k % 2 ? P.fern : P.leaf2;
      g.beginPath(); g.ellipse(0, -110, 40, 130, 0, 0, TAU); g.fill(); g.restore();
    }
  },
  icon(g, x, y, r) { const P = K.P; g.fillStyle = P.trunk; g.fillRect(x - r * 0.1, y, r * 0.2, r * 0.7); blob(g, [[x, y - r * 0.1, r * 0.5], [x - r * 0.35, y + r * 0.1, r * 0.32], [x + r * 0.35, y + r * 0.1, r * 0.32]], P.leaf); },
};

PLACES.kitchen = {
  zh: '厨房', en: 'Kitchen',
  frontTop: 920,
  spots: { left: { x: 600, y: 980, s: 1.05 }, right: { x: 1280, y: 980, s: 1.05 }, back: { x: 960, y: 830, s: 0.82 }, counter: { x: 300, y: 604, s: 0.7 } },
  bg(g, t, amb, cam) {
    const P = K.P, sx = sxOf(cam);
    g.fillStyle = P.wallK; g.fillRect(-20, -20, W + 40, 820);
    plain(g, () => rep(sx, 1, 80, (x, i) => { for (let j = 0; j < 3; j++) { g.fillStyle = (i + j) % 2 ? P.tile : P.tile2; g.fillRect(x, 560 + j * 80, 80, 80); } }));
    g.fillStyle = P.floor; g.fillRect(-20, 790, W + 40, H);
    plain(g, () => rep(sx, 1, 240, x => { g.fillStyle = P.floor2; g.fillRect(x, 790, 6, 300); }));
    g.fillStyle = P.wood2; g.fillRect(-20, 784, W + 40, 14);
    window_(g, 1180 - sx, 150, 360, 270, P.glass);
    blob(g, [[1120 - sx + 20 * Math.sin(amb * 0.3), 250, 40], [1170 - sx + 20 * Math.sin(amb * 0.3), 240, 52], [1220 - sx + 20 * Math.sin(amb * 0.3), 258, 36]], P.cloud);
    const fx = 1720 - sx; g.fillStyle = P.fridge2; g.beginPath(); g.roundRect(fx - 120, 260, 250, 540, 30); g.fill();
    g.fillStyle = P.fridge; g.beginPath(); g.roundRect(fx - 130, 250, 250, 540, 30); g.fill();
    g.fillStyle = P.fridge2; g.fillRect(fx - 130, 450, 250, 10); g.fillRect(fx + 70, 300, 14, 110); g.fillRect(fx + 70, 500, 14, 160);
    const ox = 760 - sx; g.fillStyle = P.frame; g.beginPath(); g.arc(ox, 200, 70, 0, TAU); g.fill();       // 挂钟
    g.strokeStyle = K.INK; g.lineWidth = 8; g.lineCap = 'round'; g.beginPath(); g.arc(ox, 200, 70, 0, TAU); g.stroke();
    for (const [len, sp, w] of [[42, 0.05, 9], [56, 0.6, 6]]) { const a = amb * sp * TAU - Math.PI / 2; g.lineWidth = w; g.beginPath(); g.moveTo(ox, 200); g.lineTo(ox + Math.cos(a) * len, 200 + Math.sin(a) * len); g.stroke(); }
    const cx = 300 - sx; g.fillStyle = P.wood2; g.fillRect(cx - 250, 620, 500, 180); g.fillStyle = P.wood; g.beginPath(); g.roundRect(cx - 270, 596, 540, 30, 10); g.fill();
    g.fillStyle = P.wood2; for (const d of [-125, 125]) { g.fillRect(cx + d - 4, 650, 8, 120); }
    g.fillStyle = P.wood; g.fillRect(cx - 240, 230, 480, 22);                        // 架子和罐子
    P.jars.forEach((c, k) => { g.fillStyle = c; g.beginPath(); g.roundRect(cx - 180 + k * 140, 130, 90, 100, 16); g.fill(); });
    const px = 470 - sx; g.fillStyle = P.pot; g.beginPath(); g.roundRect(px - 70, 530, 140, 70, 18); g.fill(); g.fillRect(px - 90, 540, 180, 14);
    g.strokeStyle = P.steam; g.lineWidth = 12; g.lineCap = 'round';
    for (let k = 0; k < 3; k++) { const ph = K.wrap(amb * 0.5 + k / 3, 1); g.save(); g.globalAlpha *= Math.sin(ph * Math.PI); g.beginPath();
      g.moveTo(px - 36 + k * 36, 520 - ph * 160); g.bezierCurveTo(px - 60 + k * 36, 480 - ph * 160, px - 10 + k * 36, 440 - ph * 160, px - 36 + k * 36, 400 - ph * 160); g.stroke(); g.restore(); }
  },
  front(g, t, amb, cam) {
    const P = K.P, sx = sxOf(cam) * 1.2;
    g.fillStyle = P.wood2; g.beginPath(); g.roundRect(1560 - sx, 1012, 520, 120, 24); g.fill();
    g.fillStyle = P.wood; g.beginPath(); g.roundRect(1540 - sx, 996, 560, 40, 20); g.fill();
    g.fillStyle = P.frame; g.beginPath(); g.roundRect(1700 - sx, 930, 70, 70, 14); g.fill();
    g.strokeStyle = P.frame; g.lineWidth = 12; g.beginPath(); g.arc(1774 - sx, 962, 20, -1.2, 1.2); g.stroke();
  },
  icon(g, x, y, r) { const P = K.P; g.fillStyle = P.pot; g.beginPath(); g.roundRect(x - r * 0.55, y - r * 0.1, r * 1.1, r * 0.6, r * 0.15); g.fill(); g.fillRect(x - r * 0.7, y - r * 0.08, r * 1.4, r * 0.14);
    g.strokeStyle = P.steam; g.lineWidth = r * 0.12; g.lineCap = 'round'; for (const d of [-0.25, 0.1]) { g.beginPath(); g.moveTo(x + d * r, y - r * 0.25); g.quadraticCurveTo(x + (d - 0.15) * r, y - r * 0.5, x + d * r, y - r * 0.75); g.stroke(); } },
};

PLACES.bedroom = {
  zh: '卧室', en: 'Bedroom',
  frontTop: 860,
  spots: { left: { x: 560, y: 980, s: 1.05 }, right: { x: 1240, y: 980, s: 1.05 }, back: { x: 860, y: 840, s: 0.84 }, bed: { x: 1560, y: 704, s: 0.72 } },
  bg(g, t, amb, cam) {
    const P = K.P, sx = sxOf(cam);
    g.fillStyle = P.wallB; g.fillRect(-20, -20, W + 40, 820);
    plain(g, () => rep(sx, 1, 120, (x, i) => { for (let j = 0; j < 6; j++) { g.fillStyle = P.wallB2; g.beginPath(); g.arc(x + (j % 2) * 60, 60 + j * 120, 10, 0, TAU); g.fill(); } }));
    g.fillStyle = P.floor; g.fillRect(-20, 790, W + 40, H);
    plain(g, () => rep(sx, 1, 200, x => { g.fillStyle = P.floor2; g.fillRect(x, 790, 5, 300); }));
    g.fillStyle = P.wood2; g.fillRect(-20, 784, W + 40, 14);
    const wx = 960 - sx; window_(g, wx, 140, 330, 300, P.glass);                     // 窗户和窗帘
    for (const s of [-1, 1]) { const sw = 12 * Math.sin(amb * 0.9 + s); g.fillStyle = s < 0 ? P.curtain : P.curtain2;
      g.beginPath(); g.moveTo(wx + s * 200, 110); g.lineTo(wx + s * 120, 110); g.quadraticCurveTo(wx + s * (150 + sw), 300, wx + s * (130 + sw * 1.5), 480); g.lineTo(wx + s * 230, 480); g.closePath(); g.fill(); }
    g.fillStyle = P.rug; g.beginPath(); g.ellipse(900 - sx, 905, 520, 92, 0, 0, TAU); g.fill();
    plain(g, () => { g.fillStyle = P.rug2; g.beginPath(); g.ellipse(900 - sx, 905, 400, 64, 0, 0, TAU); g.fill(); g.fillStyle = P.rug; g.beginPath(); g.ellipse(900 - sx, 905, 300, 44, 0, 0, TAU); g.fill(); });
    const bx = 1560 - sx;                                                            // 床
    g.fillStyle = P.wood; g.beginPath(); g.roundRect(bx - 300, 560, 40, 260, 12); g.fill(); g.beginPath(); g.roundRect(bx + 260, 640, 40, 180, 12); g.fill();
    g.fillStyle = P.bed2; g.beginPath(); g.roundRect(bx - 270, 700, 540, 110, 26); g.fill();
    g.fillStyle = P.bed; g.beginPath(); g.roundRect(bx - 120, 690, 390, 100, 26); g.fill();
    g.fillStyle = P.pillow; g.beginPath(); g.roundRect(bx - 250, 650, 150, 64, 30); g.fill();
    const mx = 1560 - sx; g.strokeStyle = K.SUB; g.lineWidth = 3;                     // 床头风铃
    g.beginPath(); g.moveTo(mx - 120, 120); g.lineTo(mx + 120, 120); g.moveTo(mx, 40); g.lineTo(mx, 120); g.stroke();
    for (let k = 0; k < 3; k++) { const x = mx - 100 + k * 100 + 14 * Math.sin(amb * 1.2 + k), y = 220 + 30 * k % 60;
      g.beginPath(); g.moveTo(mx - 100 + k * 100, 120); g.lineTo(x, y - 20); g.stroke(); K.star(g, x, y, 24, amb + k, P.stars[k]); }
    const sh = 300 - sx; g.fillStyle = P.wood; g.fillRect(sh - 170, 360, 340, 20); g.fillRect(sh - 170, 560, 340, 20); g.fillRect(sh - 170, 360, 18, 430); g.fillRect(sh + 152, 360, 18, 430);
    blob(g, [[sh - 90, 320, 40], [sh + 60, 520, 40]], P.balloons[0]); blob(g, [[sh + 10, 330, 30]], P.balloons[1]);
    g.fillStyle = P.balloons[2]; g.fillRect(sh - 130, 480, 50, 80); g.fillStyle = P.balloons[3]; g.fillRect(sh - 70, 495, 40, 65);
  },
  front(g, t, amb, cam) {
    const P = K.P, sx = sxOf(cam) * 1.2;
    ['A', 'B', 'C'].forEach((ch, k) => { const x = 120 + k * 104 - sx - (k === 2 ? 52 : 0), y = k === 2 ? 920 : 1006;
      g.fillStyle = P.balloons[k]; g.beginPath(); g.roundRect(x - 48, y - 48, 96, 96, 14); g.fill(); K.txt(g, ch, x, y + 4, 64, K.EN, K.P.frame); });
  },
  icon(g, x, y, r) { const P = K.P; g.fillStyle = P.bed2; g.beginPath(); g.roundRect(x - r * 0.75, y, r * 1.5, r * 0.4, r * 0.1); g.fill(); g.fillStyle = P.pillow; g.beginPath(); g.roundRect(x - r * 0.7, y - r * 0.2, r * 0.45, r * 0.25, r * 0.1); g.fill(); g.fillStyle = P.wood; g.fillRect(x - r * 0.8, y - r * 0.35, r * 0.12, r * 0.9); },
};

PLACES.playground = {
  zh: '游乐场', en: 'Playground',
  frontTop: 920,
  spots: { left: { x: 640, y: 980, s: 1.05 }, right: { x: 1300, y: 980, s: 1.05 }, back: { x: 1000, y: 830, s: 0.82 }, slide: { x: 270, y: 524, s: 0.7 } },
  bg(g, t, amb, cam) {
    const P = K.P, sx = sxOf(cam);
    sky(g, 790, P.sky2, P.sky); K.clouds(g, amb, sx, 3, 90);
    rep(sx, 0.4, 330, (x, i) => blob(g, [[x, 720, 120 + 30 * h(i, 1)], [x + 110, 740, 100]], P.hill[i % 2]));
    ground(g, sx, 1, 792, 8, 0.006, P.grass);
    plain(g, () => rep(sx, 1, 150, (x, i) => { g.fillStyle = P.grass2; g.beginPath(); g.ellipse(x, 860 + 180 * h(i, 2), 22, 7, 0, 0, TAU); g.fill(); }));
    const bx = 1000 - sx; g.fillStyle = P.wood; g.beginPath(); g.roundRect(bx - 230, 800, 460, 70, 14); g.fill();    // 沙坑
    g.fillStyle = P.sand; g.beginPath(); g.roundRect(bx - 210, 806, 420, 50, 10); g.fill();
    const lx = 270 - sx; g.strokeStyle = P.metal; g.lineWidth = 14; g.lineCap = 'round';                        // 滑梯
    g.beginPath(); g.moveTo(lx - 80, 840); g.lineTo(lx - 80, 530); g.moveTo(lx + 70, 840); g.lineTo(lx + 70, 530); g.stroke();
    g.lineWidth = 8; for (let k = 0; k < 4; k++) { g.beginPath(); g.moveTo(lx - 80, 600 + k * 60); g.lineTo(lx + 70, 600 + k * 60); g.stroke(); }
    g.fillStyle = P.wood; g.fillRect(lx - 110, 520, 200, 24);
    g.fillStyle = P.slide; g.beginPath(); g.moveTo(lx + 80, 524); g.bezierCurveTo(lx + 260, 540, lx + 300, 820, lx + 480, 840); g.lineTo(lx + 480, 880);
    g.bezierCurveTo(lx + 270, 870, lx + 240, 600, lx + 80, 572); g.closePath(); g.fill();
    const wx = 1640 - sx; g.strokeStyle = P.metal; g.lineWidth = 16;                                              // 秋千
    g.beginPath(); g.moveTo(wx - 230, 860); g.lineTo(wx - 180, 420); g.lineTo(wx - 130, 860); g.moveTo(wx + 130, 860); g.lineTo(wx + 180, 420); g.lineTo(wx + 230, 860); g.moveTo(wx - 190, 420); g.lineTo(wx + 190, 420); g.stroke();
    for (let k = 0; k < 2; k++) { const ax = wx - 70 + k * 140, a = 0.35 * Math.sin(amb * 2.1 + k * 1.6), ex = ax + Math.sin(a) * 300, ey = 420 + Math.cos(a) * 300;
      g.strokeStyle = K.SUB; g.lineWidth = 5; g.beginPath(); g.moveTo(ax - 30, 420); g.lineTo(ex - 30, ey); g.moveTo(ax + 30, 420); g.lineTo(ex + 30, ey); g.stroke();
      g.fillStyle = P.seat; g.beginPath(); g.roundRect(ex - 46, ey - 6, 92, 20, 8); g.fill(); }
    const lv = K.lively(t);
    if (lv > 0.01) for (let k = 0; k < 3; k++) {                                                                // 气球往上飘
      const x = 500 + k * 420 + 40 * Math.sin(amb + k), y = K.wrap(1100 - amb * 40 - k * 400, 1400) - 200;
      g.save(); g.globalAlpha *= lv; g.strokeStyle = K.SUB; g.lineWidth = 3; g.beginPath(); g.moveTo(x, y + 50); g.quadraticCurveTo(x + 14, y + 100, x, y + 150); g.stroke();
      g.fillStyle = P.balloons[k]; g.beginPath(); g.ellipse(x, y, 40, 50, 0, 0, TAU); g.fill(); g.restore();
    }
  },
  front(g, t, amb, cam) {
    const P = K.P, sx = sxOf(cam) * 1.2;
    for (const x0 of [-40, 1600]) { g.fillStyle = P.fence2; g.fillRect(x0 - sx, 990, 380, 18); g.fillRect(x0 - sx, 1040, 380, 18);
      g.fillStyle = P.fence; for (let k = 0; k < 6; k++) { const x = x0 + 20 + k * 62 - sx; g.beginPath(); g.moveTo(x, 1090); g.lineTo(x, 950); g.lineTo(x + 20, 928); g.lineTo(x + 40, 950); g.lineTo(x + 40, 1090); g.closePath(); g.fill(); } }
  },
  icon(g, x, y, r) { const P = K.P; g.fillStyle = P.slide; g.beginPath(); g.moveTo(x - r * 0.4, y - r * 0.4); g.quadraticCurveTo(x + r * 0.1, y - r * 0.3, x + r * 0.7, y + r * 0.5); g.lineTo(x + r * 0.5, y + r * 0.6); g.quadraticCurveTo(x, y, x - r * 0.4, y - r * 0.15); g.closePath(); g.fill();
    g.strokeStyle = P.metal; g.lineWidth = r * 0.1; g.beginPath(); g.moveTo(x - r * 0.45, y - r * 0.4); g.lineTo(x - r * 0.45, y + r * 0.6); g.stroke(); },
};

PLACES.underwater = {
  zh: '海底', en: 'Under the sea', dark: true,
  frontTop: 890,
  spots: { left: { x: 560, y: 980, s: 1.05 }, right: { x: 1300, y: 980, s: 1.05 }, back: { x: 900, y: 830, s: 0.82 }, rock: { x: 1540, y: 772, s: 0.78 } },
  bg(g, t, amb, cam) {
    const P = K.P, sx = sxOf(cam);
    sky(g, 900, P.deep2, P.deep);
    g.fillStyle = P.ray;
    for (let k = 0; k < 5; k++) { const x = K.wrap(k * 420 - sx * 0.2, W + 400) - 200, s = 0.6 + 0.4 * Math.sin(amb * 0.5 + k);
      g.beginPath(); g.moveTo(x, -20); g.lineTo(x + 90 * s, -20); g.lineTo(x + 330, 900); g.lineTo(x + 180, 900); g.closePath(); g.fill(); }
    rep(sx, 0.35, 600, (x, i) => blob(g, [[x, 840, 240], [x + 220, 860, 180]], P.deepFar));
    ground(g, sx, 1, 796, 12, 0.006, P.bed3);
    plain(g, () => rep(sx, 1, 180, (x, i) => { g.fillStyle = P.bed4; g.beginPath(); g.ellipse(x, 860 + 170 * h(i, 1), 18, 6, 0, 0, TAU); g.fill(); }));
    rep(sx, 0.85, 310, (x, i) => {                                                    // 海草，摆来摆去
      g.fillStyle = i % 2 ? P.weed : P.weed2;
      for (let j = 0; j < 6; j++) { const b = 26 * Math.sin(amb * 1.3 + i + j * 0.5) * (j / 6); g.beginPath(); g.ellipse(x + b, 800 - j * 52, 22, 36, 0.3 * Math.sin(amb + j), 0, TAU); g.fill(); }
    }, 120);
    for (const [wx, k] of [[380, 0], [1180, 1], [1880, 2]]) blob(g, [[wx - sx, 790, 50], [wx - 50 - sx, 740, 34], [wx + 46 - sx, 735, 38], [wx - sx, 700, 28]], P.coral[k]);
    const rx = 1540 - sx; g.fillStyle = P.rock2; g.beginPath(); g.ellipse(rx + 12, 836, 180, 72, 0, Math.PI, 0); g.fill();
    g.fillStyle = P.rock; g.beginPath(); g.ellipse(rx, 832, 160, 64, 0, Math.PI, 0); g.fill();
    plain(g, () => { for (let i = 0; i < 18; i++) {                                  // 气泡往上冒
      const x = h(i, 2) * W + 16 * Math.sin(amb * 2 + i), y = K.wrap(h(i, 3) * H - amb * (50 + 40 * h(i, 4)), H + 60) - 30;
      bubble(g, x, y, 6 + 12 * h(i, 5));
    } });
    const lv = K.lively(t);
    if (lv > 0.01) { g.save(); g.globalAlpha *= lv; const x0 = K.wrap(amb * 90, W + 700) - 350;   // 小鱼群
      for (let k = 0; k < 7; k++) fish(g, x0 + (k % 3) * 70 - k * 18, 300 + Math.floor(k / 3) * 46 + 12 * Math.sin(amb * 3 + k), 0.9, P.school[k % 2]); g.restore(); }
  },
  front(g, t, amb, cam) {
    const P = K.P, sx = sxOf(cam) * 1.2;
    blob(g, [[60 - sx, 1080, 170], [220 - sx, 1090, 120]], P.rock2); blob(g, [[1840 - sx, 1080, 180], [1690 - sx, 1100, 110]], P.rock);
    K.star(g, 230 - sx, 1000, 34, 0.4, P.coral[1]);
  },
  icon(g, x, y, r) { const P = K.P; g.fillStyle = P.deep; g.beginPath(); g.arc(x, y, r * 0.85, 0, TAU); g.fill(); fish(g, x - r * 0.05, y, r / 40, P.school[0]); bubble(g, x + r * 0.45, y - r * 0.4, r * 0.12); bubble(g, x + r * 0.3, y - r * 0.6, r * 0.08); },
};

// 统一先按镜头平移 sx：场景函数里按屏幕坐标画，近景写 x - sx，远景写 x - sx * k
for (const p of Object.values(PLACES)) for (const key of ['bg', 'front']) {
  const f = p[key];
  p[key] = (g, t, amb, cam, ww = 1920) => { const sx = sxOf(cam); g.save(); g.translate(sx, 0); try { f(g, t, amb ?? K.ambT(t), cam, ww); } finally { g.restore(); } };
}
K.PLACES = PLACES;
K.blob = blob;
K.place = name => {
  const p = PLACES[name];
  if (!p) throw new Error(`没有这个场景：${name}（可选 ${Object.keys(PLACES).join(' / ')}）`);
  return p;
};
K.spot = (name, spot) => {
  const s = K.place(name).spots[spot];
  if (!s) throw new Error(`场景 ${name} 没有站位 ${spot}（可选 ${Object.keys(K.place(name).spots).join(' / ')}）`);
  return { ...s };
};
// K.round 用：cfg.place 优先，其次台本里场景的 bg（字符串）
K.placeOf = (cfg, sc) => { const n = cfg.place ?? (typeof sc.bg === 'string' ? sc.bg : null); return n ? K.place(n) : null; };
})();
