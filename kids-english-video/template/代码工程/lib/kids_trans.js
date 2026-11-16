// kids_trans.js：旅程转场。台本里场景写 "trans": "map"（进入这个场景时用哪种转场），不写就是原来的彩色圆圈。
// map（地图，全集主线）和 train（小火车）要时间：场景开头放 {"act": "travel", "beats": 4}，转场画在这几拍里。
// 其他几种（slide 滑梯、bubbles 泡泡、door 开门、page 翻页）有 travel 段就拉长，没有就是 0.4 秒盖住 + 0.5 秒揭开。
// K.frame 每帧先问 K.journey：在转场窗口里就由这里画完整帧，否则走原来的代码。
(() => {
const { clamp, lerp } = U;
const W = 1920, H = 1080, TAU = Math.PI * 2;
const h = (i, k) => U.hash(i + 1000, k);
const eo = p => 1 - (1 - p) * (1 - p), ei = p => p * p, eio = p => (p < 0.5 ? 2 * p * p : 1 - 2 * (1 - p) * (1 - p));
K.TRANS = ['circle', 'map', 'train', 'slide', 'bubbles', 'door', 'page'];
const NEED = { map: true, train: true }, COVER = 0.4, REV = ty => (ty === 'map' ? 0.4 : 0.5);
const travelOf = s => K.ACTS.find(a => a.act === 'travel' && a.scene === s.id && Math.abs(a.t0 - s.t0) < 1e-3);
const isJourney = s => !!(s && s.trans && s.trans !== 'circle');
K.isJourney = isJourney;

// 进入第 j 个场景的转场时间窗：c0 开始盖住，h0 盖满（= 场景开头），r0 开始揭开，r1 揭完
const win = j => {
  const s = K.SCN[j], ty = s.trans;
  if (!isJourney(s)) return null;
  if (!K.TRANS.includes(ty)) throw new Error(`场景 ${s.id} 的转场 ${ty} 不认识（可选 ${K.TRANS.join(' / ')}）`);
  const tr = travelOf(s);
  if (NEED[ty] && !tr) throw new Error(`场景 ${s.id} 用 ${ty} 转场，开头要有一段 travel：{"act": "travel", "beats": 4}`);
  const span = tr ? tr.t1 - tr.t0 : 0;
  if (ty === 'train') return { ty, c0: s.t0, h0: s.t0, r0: s.t0 + span, r1: s.t0 + span };
  const rv = REV(ty);
  return { ty, c0: j > 0 ? s.t0 - COVER : s.t0, h0: s.t0, r0: s.t0 + Math.max(0, span - rv), r1: s.t0 + Math.max(span, rv) };
};
K.transAt = t => {
  for (let j = 0; j < K.SCN.length; j++) {
    const w = win(j);
    if (!w || t < w.c0 || t >= w.r1) continue;
    const f = (a, b) => clamp((t - a) / Math.max(1e-6, b - a));
    if (t < w.h0) return { type: w.ty, to: j, phase: 'cover', p: f(w.c0, w.h0), w };
    if (t < w.r0) return { type: w.ty, to: j, phase: 'hold', p: f(w.h0, w.r0), w };
    return { type: w.ty, to: j, phase: 'reveal', p: f(w.r0, w.r1), w };
  }
  return null;
};

// ---------- 地图 ----------
// 第一站是家，之后是写了 bg（场景名）或用地图转场的场景，按出场顺序。两站以上排成一行，超过 5 站排成蛇形两行
K.mapStations = () => {
  const st = [{ id: 'home', place: 'home' }];
  for (const s of K.SCN) if (typeof s.bg === 'string' || s.trans === 'map') st.push({ id: s.id, place: typeof s.bg === 'string' ? s.bg : 'meadow' });
  const n = st.length, two = n > 5, per = two ? Math.ceil(n / 2) : n;
  st.forEach((s, i) => {
    const row = two && i >= per ? 1 : 0, k = row ? i - per : i, m = row ? n - per : per;
    const x = lerp(300, 1620, m > 1 ? k / (m - 1) : 0.5);
    s.x = row ? 1920 - x : x; s.y = two ? (row ? 780 : 400) + (k % 2 ? 40 : -40) : 560 + (k % 2 ? 90 : -90);
  });
  return st;
};
const legOf = sTo => { const st = K.mapStations(), j = st.findIndex(s => s.id === K.SCN[sTo].id); return { st, a: st[Math.max(0, j - 1)], b: st[j], j }; };
// Bobo 在地图上的位置（站点坐标，画的时候站在站点圆牌上面）：hold 段每拍跳一下，最后一拍落到这一站
K.mapBobo = t => {
  const s = K.transAt(t); if (!s || s.type !== 'map') return null;
  const { a, b } = legOf(s.to), B = K.BEAT, n = Math.max(1, Math.floor((s.w.r0 - s.w.h0) / B + 1e-6));
  const pt = k => ({ x: lerp(a.x, b.x, k / n), y: lerp(a.y, b.y, k / n) });
  if (t < s.w.h0) return pt(0);
  const f = (t - s.w.h0) / B, k = Math.floor(f + 1e-9);
  if (k >= n) return pt(n);
  const u = f - k, p0 = pt(k), p1 = pt(k + 1);
  return { x: lerp(p0.x, p1.x, u), y: lerp(p0.y, p1.y, u) - 4 * u * (1 - u) * 90, air: u };
};
const homeIcon = (g, x, y, r) => {
  const P = K.P; g.fillStyle = P.home; g.fillRect(x - r * 0.5, y - r * 0.1, r, r * 0.65);
  g.fillStyle = P.roof; g.beginPath(); g.moveTo(x - r * 0.7, y - r * 0.05); g.lineTo(x, y - r * 0.65); g.lineTo(x + r * 0.7, y - r * 0.05); g.closePath(); g.fill();
  g.fillStyle = P.frame; g.fillRect(x - r * 0.15, y + r * 0.2, r * 0.3, r * 0.35);
};
const drawMap = (c, t, s, yoff) => K.layer(c, 'ui', g => {
  const P = K.P, { st, j } = legOf(s.to), m = K.mapBobo(t) || st[j], B = K.BEAT;
  g.save(); g.translate(0, yoff);
  g.fillStyle = P.map; g.fillRect(-20, -20, W + 40, H + 40);
  g.lineCap = 'round';
  for (let i = 0; i + 1 < st.length; i++) {                                          // 路：走过的实线，没走的虚线
    const a = st[i], b = st[i + 1], done = i + 1 < j, cur = i + 1 === j;
    g.setLineDash(done ? [] : [22, 20]); g.strokeStyle = done ? P.mapDone : P.mapLine; g.lineWidth = done ? 16 : 10;
    g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(b.x, b.y); g.stroke();
    if (cur) { g.setLineDash([]); g.strokeStyle = P.mapDone; g.lineWidth = 16; g.beginPath(); g.moveTo(a.x, a.y); g.lineTo(m.x, m.y + (m.air ? 4 * m.air * (1 - m.air) * 90 : 0)); g.stroke(); }
  }
  g.setLineDash([]);
  const beat = Math.max(0, (t - s.w.h0) / B), hit = s.phase === 'hold' ? Math.exp(-(beat % 1) * 6) : 0;
  st.forEach((p, i) => {
    const R = 70 * (i === j ? 1 + 0.08 * hit : 1);
    g.save(); g.globalAlpha *= i > j ? 0.5 : 1;
    g.fillStyle = i < j ? P.mapDone : i === j ? K.COL.bobo || P.title[0] : P.mapLine; g.beginPath(); g.arc(p.x, p.y, R + 10, 0, TAU); g.fill();
    g.fillStyle = P.frame; g.beginPath(); g.arc(p.x, p.y, R, 0, TAU); g.fill();
    if (p.place === 'home') homeIcon(g, p.x, p.y + 6, R * 0.8); else K.place(p.place).icon(g, p.x, p.y, R * 0.8);
    g.restore();
    const pl = p.place === 'home' ? { en: 'Home', zh: '家' } : K.place(p.place);
    K.txt(g, pl.en, p.x, p.y + R + 44, 38, K.EN, K.INK, { alpha: i > j ? 0.5 : 1 });
    K.txt(g, pl.zh, p.x, p.y + R + 84, 28, K.ZH2, K.SUB, { alpha: i > j ? 0.5 : 1 });
  });
  const land = s.w.r0 - (s.w.r0 - s.w.h0) % B;
  if (s.phase !== 'cover') K.sparks(g, t, Math.max(s.w.h0 + B, land), st[j].x, st[j].y, 90, 8);
  const pose = K.has('bobo_cheer') && m.air ? 'bobo_cheer' : 'bobo_m0';
  if (K.has(pose)) K.spr(g, pose, m.x, m.y - 64, 0.34, { cast: false });
  else { g.fillStyle = K.COL.bobo || P.title[0]; g.beginPath(); g.arc(m.x, m.y - 110, 50, 0, TAU); g.fill(); }
  g.restore();
});

// ---------- 小火车（拿上一场景的最后一帧当底，车头烟囱处是新旧画面的分界） ----------
let SNAP = null;
const snapOf = (from, run) => {
  if (SNAP && SNAP.id === from.id && SNAP.style === K.TH.id) return SNAP.cv;
  const cv = (SNAP && SNAP.cv) || document.createElement('canvas'); cv.width = W; cv.height = H;
  const g = cv.getContext('2d'), main = K.MAIN; g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = K.TH.paper; g.fillRect(0, 0, W, H);
  K.MAIN = g; try { run(from, g, from.t1 - 0.5 / K.FPS); } finally { K.MAIN = main; }
  SNAP = { id: from.id, style: K.TH.id, cv }; return cv;
};
const LT = 1500;
const train = (g, x0, t) => {                                                       // x0 = 车头最左边；车往左开
  const P = K.P, y = 990, cars = [[x0, 420, 0], [x0 + 450, 330, 1], [x0 + 810, 330, 2], [x0 + 1170, 330, 3]];
  g.fillStyle = P.wheel; g.fillRect(-20, y + 30, W + 40, 14);
  for (const [x, w, k] of cars) {
    g.fillStyle = P.wheel; g.fillRect(x + w - 10, y - 60, 50, 16);
    g.fillStyle = P.train[k]; g.beginPath(); g.roundRect(x, y - 220, w, 200, 26); g.fill();
    g.fillStyle = P.frame; for (let q = 0; q < (k ? 2 : 1); q++) { g.beginPath(); g.roundRect(x + (k ? 40 + q * 150 : 210), y - 190, k ? 110 : 160, 90, 16); g.fill(); }
    for (const wx of [x + 70, x + w - 70]) { g.fillStyle = P.wheel; g.beginPath(); g.arc(wx, y, 46, 0, TAU); g.fill();
      g.strokeStyle = P.frame; g.lineWidth = 8; g.beginPath(); const a = t * 9; g.moveTo(wx + Math.cos(a) * 30, y + Math.sin(a) * 30); g.lineTo(wx - Math.cos(a) * 30, y - Math.sin(a) * 30); g.stroke(); }
  }
  g.fillStyle = P.train[0]; g.beginPath(); g.roundRect(x0 + 190, y - 330, 230, 130, 20); g.fill();               // 驾驶室
  g.fillStyle = P.wheel; g.fillRect(x0 + 70, y - 330, 64, 120); g.fillRect(x0 + 50, y - 350, 104, 30);           // 烟囱
  g.fillStyle = P.knob; g.beginPath(); g.arc(x0 + 8, y - 120, 30, 0, TAU); g.fill();                              // 车灯
};
const drawTrain = (c, t, s, from, run) => {
  const x0 = lerp(W + 40, -LT - 200, s.p), seam = x0 + 102;
  if (from && seam > 0) { const im = snapOf(from, run); c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.beginPath(); c.rect(0, 0, Math.min(W, seam), H); c.clip(); c.drawImage(im, 0, 0); c.restore(); }
  K.layer(c, 'prop', g => {
    g.fillStyle = K.P.smoke;                                                        // 烟柱：从烟囱一直冒到画面顶上，盖住分界线
    for (let k = 0; k < 12; k++) { const y = 620 - k * 64, r = 64 + k * 5 + 8 * Math.sin(t * 5 + k); g.beginPath(); g.arc(seam + 14 * Math.sin(t * 4 + k * 1.3) + k * 6, y, r, 0, TAU); g.fill(); }
    train(g, x0, t);
  });
};

// ---------- 其他几种：盖住、揭开 ----------
const cover = (s) => (s.phase === 'cover' ? eo(s.p) : s.phase === 'hold' ? 1 : 1 - ei(s.p));   // 盖住的程度 0–1
const drawDoor = (c, s) => K.layer(c, 'ui', g => {
  const P = K.P;
  const panel = (x, w, side) => {
    if (w <= 1) return;
    g.fillStyle = P.door; g.fillRect(x, -20, w, H + 40);
    g.fillStyle = P.door2; const ix = x + w * 0.14, iw = w * 0.72;
    g.beginPath(); g.roundRect(ix, 120, iw, 360, 24); g.roundRect(ix, 560, iw, 400, 24); g.fill();
    g.fillStyle = P.knob; g.beginPath(); g.arc(side < 0 ? x + w - 50 : x + 50, 560, 22, 0, TAU); g.fill();
  };
  if (s.phase === 'reveal') { const k = 1 - ei(s.p); panel(0, W / 2 * k, -1); panel(W - W / 2 * k, W / 2 * k, 1); }   // 门往两边推开
  else { const k = s.phase === 'cover' ? eo(s.p) : 1; panel(-W / 2 + W / 2 * k, W / 2, -1); panel(W - W / 2 * k, W / 2, 1); }
});
const drawBubbles = (c, s) => K.layer(c, 'ui', g => {
  const P = K.P;
  for (let i = 0; i < 28; i++) {                                                      // 盖住：泡泡一个个冒起来变大；揭开：一个个破掉
    const cx = (i % 7 + 0.5) * W / 7 + 60 * (h(i, 1) - 0.5), cy = (Math.floor(i / 7) + 0.5) * H / 4 + 50 * (h(i, 2) - 0.5), d = 0.45 * h(i, 3);
    const r = 300 * (s.phase === 'cover' ? eo(clamp((s.p - d) / (1 - d))) : s.phase === 'hold' ? 1 : 1 - eo(clamp((s.p - d * 1.5) / 0.3)));
    if (r < 1) continue;
    const rise = s.phase === 'cover' ? (1 - s.p) * 160 : 0;
    g.fillStyle = i % 3 ? P.sea2 : P.water2; g.strokeStyle = P.bubbleRim; g.lineWidth = 10;
    g.beginPath(); g.arc(cx, cy + rise, r, 0, TAU); g.fill(); g.stroke();
    g.save(); g.plain = true; g.fillStyle = P.frame; g.globalAlpha *= 0.6; g.beginPath(); g.ellipse(cx - r * 0.35, cy + rise - r * 0.4, r * 0.18, r * 0.1, -0.6, 0, TAU); g.fill(); g.restore();
  }
});
const drawSlide = (c, s) => K.layer(c, 'ui', g => {
  const P = K.P, D = W + H, e = s.phase === 'cover' ? eio(s.p) * 1.04 : s.phase === 'hold' ? 1.04 : 0;
  const q = s.phase === 'reveal' ? eio(s.p) * 1.04 : 0;                                // 斜着的滑道：从左上角滑到右下角
  const band = (u0, u1) => { g.beginPath(); g.moveTo(u0 * D, 0); g.lineTo(u1 * D, 0); g.lineTo(u1 * D - H, H); g.lineTo(u0 * D - H, H); g.closePath(); };
  const u0 = s.phase === 'reveal' ? q : -0.1, u1 = s.phase === 'reveal' ? 1.1 : e;
  g.fillStyle = P.slide; band(u0, u1); g.fill();
  g.save(); g.plain = true; g.strokeStyle = P.sun; g.lineWidth = 26;
  for (const u of [u0, u1]) if (u > 0 && u < 1.04) { g.beginPath(); g.moveTo(u * D, 0); g.lineTo(u * D - H, H); g.stroke(); }
  g.restore();
  const u = s.phase === 'reveal' ? q : e;
  if (u > 0.05 && u < 1 && K.has('bobo_cheer')) K.spr(g, 'bobo_cheer', clamp(u * D - H / 2 - 40, 100, W - 100), H / 2 + 120, 0.4, { rot: -0.55, cast: false });   // Bobo 坐在滑道前沿
});
const drawPage = (c, s) => K.layer(c, 'ui', g => {
  const P = K.P;
  const x0 = s.phase === 'reveal' ? 0 : W * (1 - (s.phase === 'cover' ? eio(s.p) : 1)), x1 = s.phase === 'reveal' ? W * (1 - eio(s.p)) : W + 20;
  if (x1 - x0 < 1) return;
  g.fillStyle = P.map; g.fillRect(x0, -20, x1 - x0, H + 40);
  g.save(); g.plain = true; g.strokeStyle = P.mapLine; g.lineWidth = 3; g.globalAlpha *= 0.5;
  for (let y = 140; y < H; y += 72) { g.beginPath(); g.moveTo(Math.max(x0, 0) + 40, y); g.lineTo(Math.min(x1, W) - 40, y); g.stroke(); }
  g.restore();
  const edge = s.phase === 'reveal' ? x1 : x0;                                          // 翻起来的那条边：一道卷边
  if (edge > 0 && edge < W) { g.fillStyle = K.shade(P.map, 0.12); g.fillRect(edge - (s.phase === 'reveal' ? 44 : 0), -20, 44, H + 40); }
});

// K.frame 的钩子：这一帧在旅程转场里就画完返回 true
K.journey = (c, t, i, run) => {
  const s = K.transAt(t);
  if (!s) return false;
  const to = K.SCN[s.to], from = K.SCN[s.to - 1];
  run(s.phase === 'cover' ? from : to);
  if (s.type === 'map') drawMap(c, t, s, s.phase === 'cover' ? -H * (1 - eo(s.p)) : s.phase === 'reveal' ? -H * ei(s.p) : 0);
  else if (s.type === 'train') drawTrain(c, t, s, from, run);
  else if (s.type === 'door') drawDoor(c, s);
  else if (s.type === 'bubbles') drawBubbles(c, s);
  else if (s.type === 'slide') drawSlide(c, s);
  else if (s.type === 'page') drawPage(c, s);
  return true;
};
})();
