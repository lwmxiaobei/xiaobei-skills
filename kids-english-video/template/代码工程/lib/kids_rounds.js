// 画面库 K 的扩展：玩法（猜猜看、跟我做、找一找、二选一、数一数、少了什么、木头人）。在 kids_stage.js 之后加载。
// 用法见 references/scene-cookbook.md「玩法」。
(() => {
const { clamp, lerp, ss } = U;
const TAU = Math.PI * 2;
const isCh = v => v && typeof v === 'object' && 'x' in v;
const pose = (who, name) => (K.has(`${who}_${name}`) ? `${who}_${name}` : undefined);
const waitsOf = (sc, kind) => K.WAITS.filter(w => (w.scene === sc.id || (w.scene == null && w.t0 >= sc.t0 && w.t0 < sc.t1)) && (!kind || w.kind === kind));
const actsOf = (sc, act) => K.ACTS.filter(a => a.scene === sc.id && a.act === act);
const inAny = (t, spans, lead = 0) => spans.find(s => t >= s.t0 - lead && t < s.t1) || null;
const beatsIn = (a, b, every = 1) => { const out = []; for (let x = a; x < b - 1e-6; x += K.BEAT * every) out.push(x); return out; };
const lastBeat = (beats, t, lead = 0) => { let r = null; for (const b of beats) if (b <= t + lead) r = b; return r; };
const snap = x => Math.round(x / K.BEAT) * K.BEAT;
const sizeOf = (key, size) => { const im = K.img(K.VOC[key] ? K.VOC[key].img : key), s = size / Math.max(im.width, im.height); return { w: im.width * s, h: im.height * s }; };
const addMv = (p, m) => { p.move = K.mvAdd(p.move || {}, m); };
// cfg.cast(t) 拷一份再改：fn(who, p, i, L)，i 是按前后排的序号
const tweak = (cfg, fn) => t => {
  const L0 = cfg.cast(t), L = {};
  for (const k of Object.keys(L0)) L[k] = isCh(L0[k]) ? { ...L0[k] } : L0[k];
  (L.order || K.byDepth(L)).forEach((k, i) => { if (isCh(L[k])) fn(k, L[k], i, L); });
  return L;
};
// 近景对准一个角色：头顶落在画面 y≈500，给上方的提示字留位置
const closeOn = (L, who, t0, t1) => {
  const p = L[who], s = (K.SCALE[who] ?? 0.9) * (p.s ?? 1);
  return { t0, t1, kind: 'close', on: [who], z: 1.4, x: p.x, y: K.topOf(who, p.y, s) + 30, ease: 'ease' };
};
// 动作段期间（到结束后 0.3 秒）换欢呼帧（有就换），开头跳一下
const cheer = (who, p, t, a, i) => {
  if (!a || t < a.t0 || t > a.t1 + 0.3) return;
  if (!p.pose) p.pose = pose(who, 'cheer');
  addMv(p, K.mv.squash(t, a.t0 + 0.14 + i * 0.08, 70, 0.4));
};
// 等孩子想的时候：轮流歪头
const think = (p, t, w, i) => { if (w) addMv(p, K.mv.tilt(t, w.t0, w.t1, (i % 2 ? 1 : -1) * 0.08)); };

// ---------- 小道具（在 K.layer 的 g 上画）----------
// 一团烟：几个圆先胀开再缩没，0.5 秒
K.poof = (g, t, t0, x, y, r = 80) => {
  const p = (t - t0) / 0.5; if (p < 0 || p > 1) return;
  const col = '#EEEAF4';
  g.save(); g.fillStyle = col; g.strokeStyle = K.shade(col, 0.28); g.lineWidth = 4;
  for (let i = 0; i < 7; i++) {
    const a = i / 7 * TAU + 0.3, d = r * (0.2 + 0.8 * Math.sqrt(p)), rr = r * 0.5 * Math.sin(Math.PI * Math.sqrt(p)) * (0.8 + 0.4 * U.hash(i, 51));
    g.beginPath(); g.arc(x + Math.cos(a) * d, y + Math.sin(a) * d * 0.7, Math.max(0.1, rr), 0, TAU); g.fill(); g.stroke();
  }
  g.restore();
};
// 圆环（光环）
const ring = (g, x, y, r, w, col) => { g.fillStyle = col; g.beginPath(); g.arc(x, y, r + w / 2, 0, TAU); g.arc(x, y, r - w / 2, 0, TAU, true); g.fill('evenodd'); };
// 绿色对勾徽章
const check = (g, x, y, r, p) => {
  if (p <= 0.001) return;
  g.save(); g.translate(x, y); g.scale(p, p);
  g.fillStyle = K.P.yes; g.beginPath(); g.arc(0, 0, r, 0, TAU); g.fill();
  g.strokeStyle = '#fff'; g.lineWidth = r * 0.26; g.lineCap = 'round'; g.lineJoin = 'round';
  g.beginPath(); g.moveTo(-r * 0.45, 0); g.lineTo(-r * 0.1, r * 0.35); g.lineTo(r * 0.5, -r * 0.35); g.stroke();
  g.restore();
};
// 音符
const note = (g, x, y, s, col, rot) => {
  g.save(); g.translate(x, y); g.rotate(rot); g.scale(s, s); g.fillStyle = col;
  g.beginPath(); g.ellipse(0, 0, 22, 16, -0.4, 0, TAU); g.fill();
  g.beginPath(); g.rect(13, -78, 9, 78); g.fill();
  g.beginPath(); g.moveTo(22, -78); g.quadraticCurveTo(54, -60, 44, -28); g.quadraticCurveTo(40, -50, 22, -54); g.closePath(); g.fill();
  g.restore();
};
// 剪影：物品图按 alpha 填成一种颜色（缓存）
const SIL = new Map();
const silhouette = (key, size, col) => {
  const n = K.VOC[key] ? K.VOC[key].img : key, id = `${n}|${size}|${col}`;
  if (SIL.has(id)) return SIL.get(id);
  const im = K.img(n), s = size / Math.max(im.width, im.height), w = Math.max(1, Math.round(im.width * s)), h = Math.max(1, Math.round(im.height * s));
  const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
  const x = cv.getContext('2d'); x.drawImage(im, 0, 0, w, h); x.globalCompositeOperation = 'source-in'; x.fillStyle = col; x.fillRect(0, 0, w, h);
  SIL.set(id, cv); return cv;
};
// 草丛：底边中点 (cx, base)，宽 bw、高 bh；open 0→1 从中间往两边分开、变小
const BUSH = [[-0.32, -0.42, 0.24], [0.02, -0.62, 0.3], [0.34, -0.42, 0.24], [-0.16, -0.22, 0.24], [0.2, -0.22, 0.24]];
const bush = (g, cx, base, bw, bh, open, shake) => {
  for (const [col, k] of [[K.P.leaf2, 1], [K.P.leaf, 0.62]]) {
    g.fillStyle = col;
    for (const [u, v, r] of BUSH) {
      const side = u < 0 ? -1 : 1, sc = 1 - 0.4 * open;
      const x = cx + u * bw + side * open * bw * 0.6 + shake, y = base + v * bh - (k < 1 ? r * bh * 0.25 : 0);
      g.beginPath(); g.ellipse(x, y, r * bw * 0.9 * k * sc, r * bh * 1.3 * k * sc, 0, 0, TAU); g.fill();
    }
  }
};
// 台子（二选一）
const pedestal = (g, x, top, col) => {
  const GY = K.GY;
  g.fillStyle = K.P.ground; g.beginPath(); g.ellipse(x + 8, GY + 26, 130, 22, 0, 0, TAU); g.fill();
  g.fillStyle = K.shade(col, -0.62); g.beginPath(); g.roundRect(x - 90, top + 14, 180, GY + 20 - top - 14, 16); g.fill();
  g.fillStyle = K.P.card; g.beginPath(); g.roundRect(x - 90, top + 72, 180, 24, 8); g.fill();
  g.fillStyle = col; g.beginPath(); g.roundRect(x - 122, top - 10, 244, 38, 19); g.fill();
};
// 放大镜：镜片里放大显示 inside(g)（以镜片中心为原点放大 1.6 倍）
const magnifier = (g, x, y, R, k, inside) => {
  if (k <= 0.001) return;
  g.save(); g.translate(x, y); g.scale(k, k);
  g.save(); g.rotate(0.75); g.fillStyle = K.P.trunk; g.beginPath(); g.roundRect(R * 1.05, -R * 0.15, R * 0.95, R * 0.3, R * 0.15); g.fill(); g.restore();
  g.save(); g.beginPath(); g.arc(0, 0, R, 0, TAU); g.clip();
  g.fillStyle = K.P.sky2; g.fillRect(-R, -R, 2 * R, 2 * R);
  g.scale(1.6, 1.6); g.translate(-x, -y); inside(g);
  g.restore();
  ring(g, 0, 0, R + R * 0.08, R * 0.16, K.INK);
  g.fillStyle = 'rgba(255,255,255,0.75)'; g.beginPath(); g.ellipse(-R * 0.4, -R * 0.4, R * 0.24, R * 0.1, -0.8, 0, TAU); g.fill();
  g.restore();
};

// ---------- 镜头 ----------
// 在分镜里插一个手写镜头：被盖住的部分切掉，切剩不足 2 拍的碎片并进插入的镜头；插入的镜头不足 2 拍时往前补齐。插入镜头之后的那个一律硬切
K.insertShot = (S, s) => {
  const B2 = 2 * K.BEAT, eps = 1e-6;
  if (!S.length) return [{ ...s }];
  const start = S[0].t0, end = S[S.length - 1].t1;
  let a = Math.max(start, s.t0), b = Math.min(Math.max(s.t1, a + B2), end);
  if (b - a < B2 - eps) a = Math.max(start, b - B2);
  const before = [], after = [];
  for (const x of S) {
    if (x.t0 < a - eps) before.push({ ...x, t1: Math.min(x.t1, a) });
    if (x.t1 > b + eps) after.push({ ...x, t0: Math.max(x.t0, b) });
  }
  const lb = before[before.length - 1];
  if (lb && lb.t1 - lb.t0 < B2 - eps) { before.pop(); a = lb.t0; }
  const fa = after[0];
  if (fa && fa.t1 - fa.t0 < B2 - eps) { after.shift(); b = fa.t1; }
  if (after.length) after[0] = { ...after[0], ease: 'cut' };
  return [...before, { ...s, t0: a, t1: b }, ...after];
};
// 揭晓进度：动作段（默认 reveal）开始前 0，开始后 0.3 秒内到 1；场景里没有这个动作段就是 1
K.revealP = (t, sc, act = 'reveal') => { const a = K.actOf(sc.id, act); return a ? clamp((t - a.t0) / 0.3) : 1; };

// ---------- 玩法骨架 ----------
// cfg = { focus, bg(g, t, amb, cam)（不给就用 cfg.place 或台本的 "bg" 场景）, place?, cast(t) → L, host?, shots?, extraShots?(L) → [镜头], ww?, cardX?,
//         mid?(g, t)（和背景同一层，角色后面）, overlay?(c, t, pos, L), front?(g, t, pos, L)（prop 层，角色前面）, hud?(c, t)（镜头外）,
//         jolt?(t) → {dx, dy}（画面抖，整场放大 0.8% 防露边）, promptAt?: [x, y], prompt?: false }
// L[who] = {x, y, s（相对 K.SCALE 的缩放）, pose?, move?, still?, hidden?, draw?(c, t) → {top}, …K.ch 的参数}
K.round = (c, t, sc, cfg) => {
  const host = cfg.host || 'bobo', focus = cfg.focus, L = cfg.cast(t);
  let shots = cfg.shots || K.shots(sc, L, focus, host);
  if (cfg.extraShots) for (const s of cfg.extraShots(L)) shots = K.insertShot(shots, s);
  const cam = K.camAt(t, shots, cfg.ww), pos = {}, amb = K.ambT(t), ww = cfg.ww || 1920;
  const PL = cfg.bg ? null : K.placeOf(cfg, sc);                                  // 没给 cfg.bg：用台本里的 "bg" 场景（kids_scenes.js）
  if (!cfg.bg && !PL) throw new Error(`场景 ${sc.id} 没有背景：台本里写 "bg"（场景名），或者给 cfg.bg`);
  const bg = cfg.bg || ((g, tt, a, cm) => PL.bg(g, tt, a, cm, ww));
  c.save();
  if (cfg.jolt) { const j = cfg.jolt(t) || {}; c.translate(960 + (j.dx || 0), 540 + (j.dy || 0)); c.scale(1.008, 1.008); c.translate(-960, -540); }
  K.withCam(c, cam, () => {
    K.layer(c, 'bg', g => { bg(g, t, amb, cam); if (cfg.mid) cfg.mid(g, t); });
    for (const who of (L.order || K.byDepth(L))) {
      const p = L[who]; if (!isCh(p) || p.hidden) continue;
      const move = K.mvAdd(p.move || {}, { rot: p.still ? 0 : K.leanFor(who, t, sc, L, focus, host) });
      const r = p.draw ? p.draw(c, t) : K.ch(c, who, p.x, p.y, t, { ...p, s: (K.SCALE[who] ?? 0.9) * (p.s ?? 1), move });
      pos[who] = { x: p.x + move.dx, top: p.top ?? r.top, bx: p.bx };
    }
    if (cfg.overlay) cfg.overlay(c, t, pos, L);
    const pf = PL && PL.frontTop != null;                                         // 场景前景只在画面底部：图层只处理那一条（cfg.front 可能画在任何地方，就整层）
    if (pf || cfg.front) K.layer(c, 'prop', g => { if (pf) PL.front(g, t, amb, cam, ww); if (cfg.front) cfg.front(g, t, pos, L); }, { top: cfg.front ? null : PL.frontTop });
    K.bubbles(c, t, sc, pos);
  });
  c.restore();
  if (cfg.hud) cfg.hud(c, t);
  K.wordCard(c, t, sc, { x: cfg.cardX });
  K.chantRow(c, t, sc);
  for (const l of K.linesOf(sc.id)) {                                              // 多人齐说（不含老师的）：顶部横幅
    if (l.who.length < 2 || l.chant != null || l.who.includes('teacher')) continue;
    K.banner(c, l.text, l.zh, 150, K.popIn(t, l.t0 - 0.1, 0.32) * (1 - ss(l.t1 + 0.5, l.t1 + 0.7, t)), K.COL.teacher);
  }
  const w = inAny(t, waitsOf(sc), 0.1);
  if (w && cfg.prompt !== false) { const [px, py] = cfg.promptAt || [960, 300]; K.layer(c, 'ui', g => K.waitPrompt(g, t, w, px, py, { pill: !!(PL && PL.dark) })); }
  return { L, pos, cam };
};
K.rounds = {};
// 标准问答：就是 K.round
K.rounds.qa = (c, t, sc, cfg) => K.round(c, t, sc, cfg);

// 猜猜看：cfg.item = {key, x, y, size}，cfg.hide = 'silhouette' | 'bush' | 'corner'。动作段 reveal 揭晓，揭晓时近景推到物品
K.rounds.guess = (c, t, sc, cfg) => {
  const it = cfg.item, hide = cfg.hide || 'silhouette', a = K.actOf(sc.id, 'reveal'), rp = K.revealP(t, sc);
  const { w, h } = sizeOf(it.key, it.size), wNow = inAny(t, waitsOf(sc), 0.1);
  const e = a ? K.back(clamp((t - a.t0) / 0.5), 1.6) : 1;
  const pulse = a && t >= a.t0 ? 1 + 0.25 * Math.sin(Math.PI * clamp((t - a.t0) / 0.5)) : 1;
  const peek = wNow && rp === 0 ? Math.abs(Math.sin(t * 5)) : 0;
  const bw = Math.max(w, h) * 1.25, bh = h * 0.78;
  const place = () => {
    if (hide === 'bush') return { x: lerp(it.x + w * 0.15, it.x, e), y: it.y - 10 * peek * (1 - e), rot: lerp(0.18, 0, e) };
    if (hide === 'corner') { const x0 = 1920 + w * 0.2 - w * 0.12 * peek; return { x: lerp(x0, it.x, e), y: it.y, rot: lerp(-0.3, 0, e) }; }
    if (hide !== 'silhouette') throw new Error('没有这种藏法：' + hide);
    return { x: it.x, y: it.y, rot: (1 - rp) * 0.06 * Math.sin(t * 3) };
  };
  const qx = hide === 'corner' ? 1920 - 130 : it.x, qy = it.y - (hide === 'bush' ? bh : h) - 70;
  // cfg.become = 角色 id：揭晓弹完（reveal 开始后 0.5 秒）物品换成这个角色，同一位置、同样大小，之后能说话、领念。物品图用它的 _m0 帧
  const b = cfg.become, swap = b && a ? a.t0 + 0.5 : Infinity;
  const cast = !b ? cfg.cast : tt => {
    const L = cfg.cast(tt), im = K.img(K.VOC[it.key] ? K.VOC[it.key].img : it.key);
    return { ...L, [b]: { ...(L[b] || {}), x: it.x, y: it.y, s: it.size / Math.max(im.width, im.height) / (K.SCALE[b] ?? 0.9), hidden: tt < swap } };
  };
  return K.round(c, t, sc, {
    promptAt: [960, 230], ...cfg,
    cast: tweak({ cast }, (who, p, i) => { think(p, t, wNow && t < (a ? a.t0 : Infinity) ? wNow : null, i); if (who !== b) cheer(who, p, t, a, i); }),
    extraShots: () => (a ? [{ t0: a.t0, t1: a.t1, kind: 'close', on: [], z: 1.4, x: it.x, y: it.y - h / 2, ease: 'ease' }] : []),
    mid: (g, tt) => {
      if (cfg.mid) cfg.mid(g, tt);
      const P = place();
      g.save(); g.translate(P.x, P.y); g.rotate(P.rot); g.scale(pulse, pulse);
      if ((hide !== 'silhouette' || rp > 0) && t < swap) K.item(g, it.key, 0, 0, it.size);
      if (hide === 'silhouette' && rp < 1) { g.globalAlpha *= 1 - rp; g.drawImage(silhouette(it.key, it.size, K.INK), -w / 2, -h); }
      g.restore();
      if (hide === 'bush') bush(g, it.x, it.y + 12, bw, bh, e, wNow && rp === 0 ? 3 * Math.sin(t * 45) : 0);
    },
    front: (g, tt, pos, L) => {
      if (a) K.starBurst(g, t, a.t0, it.x, it.y - h / 2, 1.2, 8, Math.max(w, h) * 0.7);
      if (!wNow && t < (a ? a.t0 : Infinity)) K.txt(g, '?', qx, qy + 8 * Math.sin(t * 4), 130, K.EN, K.COL.teacher, { stroke: K.P.textStroke, sw: 22 });
      if (cfg.front) cfg.front(g, tt, pos, L);
    },
  });
};

// 跟我做：cfg.action = 'jump' | 'spin' | 'stomp' | 'tiptoe' | 'wiggle'。do 空拍和老师那句期间，全员每拍做一次（spin 每 2 拍一圈）
// cfg.airPose = {who: 帧名}：跳起来离地时换这一帧（青蛙 frog_jump、兔子 rabbit_jump），落地换回口型帧
const ACTIONS = ['jump', 'spin', 'stomp', 'tiptoe', 'wiggle'];
K.rounds.doit = (c, t, sc, cfg) => {
  const act = cfg.action || 'jump', B = K.BEAT;
  if (!ACTIONS.includes(act)) throw new Error(`没有这种动作：${act}（可选 ${ACTIONS.join(' / ')}）`);
  const ls = K.linesOf(sc.id), chanted = new Set(ls.filter(l => l.chant != null).map(l => l.text));   // 后面有同一个词领念的单词卡是教单词，不是口令
  const wins = [...waitsOf(sc, 'do').map(w => [w.t0, w.t1]),
    ...ls.filter(l => l.who.includes('teacher') && l.chant == null && !chanted.has(l.text)).map(l => [l.t0, Math.max(l.t1, l.t0 + 0.01)])];
  const air = act === 'stomp' ? 0.22 : B - 0.26;
  const lands = act === 'jump' || act === 'stomp' ? wins.flatMap(([a, b]) => beatsIn(a, b).map(x => x + air)) : [];
  const moveAt = () => {
    for (const [a, b] of wins) {
      if (t < a - 0.2 || t > b + B + 0.2) continue;
      if (act === 'wiggle') { if (t >= a && t <= b) return K.mv.wiggle(t, a, b); continue; }
      if (act === 'tiptoe') { if (t >= a && t <= b) return K.mvAdd(K.mv.tiptoe(t, a, b), { dx: 12 * Math.sin(Math.PI * (t - a) / B) }); continue; }
      if (act === 'spin') { const tb = lastBeat(beatsIn(a, b, 2), t); if (tb != null && t < tb + 1.6 * B) return K.mv.spin(t, tb, 1.6 * B); continue; }
      const tb = lastBeat(beatsIn(a, b), t, 0.14);
      if (tb != null && t < tb + B - 0.14) return act === 'stomp' ? K.mv.squash(t, tb, 40, air) : K.mv.squash(t, tb, 120, air);
    }
    return null;
  };
  const m = moveAt();
  return K.round(c, t, sc, {
    promptAt: [960, 240], ...cfg,
    cast: tweak(cfg, (who, p) => { if (!m) return; addMv(p, { ...m, dy: m.dy * (p.s ?? 1) }); if (cfg.airPose && cfg.airPose[who] && m.dy < -20) p.pose = cfg.airPose[who]; }),
    jolt: act === 'stomp' ? () => { const tl = lastBeat(lands, t); if (tl == null || t - tl > 0.3) return null; const j = 4 * Math.exp(-(t - tl) * 12) * Math.cos((t - tl) * 60); return { dx: 0.5 * j, dy: j }; } : cfg.jolt,
    front: (g, tt, pos, L) => {
      for (const tl of lands) if (t >= tl && t < tl + 0.5) for (const k of K.byDepth(L)) K.dust(g, t, tl, L[k].x, L[k].y);
      if (cfg.front) cfg.front(g, tt, pos, L);
    },
  });
};

// 找一找：cfg.items = [{key, x, y, size}] 满屏物品，cfg.target 目标下标。动作段 found：前 60% 放大镜从画面中间扫到目标，之后目标外光环跳动、其他物品变淡、近景推到目标
K.rounds.find = (c, t, sc, cfg) => {
  const items = cfg.items, ti = cfg.target ?? 0, T = items[ti], a = K.actOf(sc.id, 'found');
  const tz = sizeOf(T.key, T.size), tc = { x: T.x, y: T.y - tz.h / 2 }, R = Math.max(tz.w, tz.h) * 0.62;
  const d = a ? a.t1 - a.t0 : 1, tf = a ? a.t0 + 0.6 * d : Infinity;
  const hl = ss(tf, tf + 0.25, t), hb = t >= tf ? Math.exp(-(((t - tf) / K.BEAT) % 1) * 6) : 0;
  const wNow = inAny(t, waitsOf(sc), 0.1);
  const drawItems = (g, alphaOthers) => {
    items.forEach((it, i) => { if (i !== ti) K.item(g, it.key, it.x, it.y - 5 * Math.sin(K.ambT(t) * 2 + i * 1.7), it.size, { alpha: alphaOthers, rot: 0.04 * Math.sin(t * 1.5 + i) }); });
    const k = 1 + 0.08 * hb * hl;
    K.item(g, T.key, T.x, T.y - 5 * Math.sin(K.ambT(t) * 2 + ti * 1.7), T.size, { rot: 0.04 * Math.sin(t * 1.5 + ti) * (1 - hl), sx: k, sy: k });
  };
  return K.round(c, t, sc, {
    ...cfg,
    cast: tweak(cfg, (who, p, i) => {
      think(p, t, wNow, i);
      if (a && t >= tf && t < a.t1 + 0.6) { if (!p.pose) p.pose = pose(who, 'point') || pose(who, 'cheer'); addMv(p, K.mv.lean(t, tf, a.t1 + 0.6, Math.sign(T.x - p.x) || 1)); }
    }),
    extraShots: () => (a ? [{ t0: snap(tf), t1: Math.max(a.t1, snap(tf) + 2 * K.BEAT), kind: 'close', on: [], z: 1.4, x: tc.x, y: tc.y, ease: 'ease' }] : []),
    mid: (g, tt) => { if (cfg.mid) cfg.mid(g, tt); drawItems(g, 1 - 0.5 * hl); },
    front: (g, tt, pos, L) => {
      if (a && t >= a.t0 && t < tf + 0.3) {                                          // 放大镜：扫过去，找到后往右上飞走缩没
        const q = U.ease.inOut(clamp((t - a.t0) / (0.6 * d))), out = clamp((t - tf) / 0.3);
        const x = lerp(960, tc.x, q) + 140 * Math.sin(q * TAU) * (1 - q) + out * R * 1.4, y = lerp(480, tc.y, q) - 120 * Math.sin(Math.PI * q) - out * R * 1.4;
        magnifier(g, x, y, R, 1 - U.ease.in(out), gg => drawItems(gg, 1));
      }
      if (hl > 0) { ring(g, tc.x, tc.y, R * 1.1 * (1 + 0.08 * hb), 14, K.P.stars[0]); K.sparks(g, t, tf, tc.x, tc.y, R * 1.2); }
      if (cfg.front) cfg.front(g, tt, pos, L);
    },
  });
};

// 二选一：cfg.left、cfg.right（VOCAB 词），cfg.correct = 'left' | 'right'。两样东西在 x 640、1280 的台子上；动作段 pick：对的跳一下冒星星，错的抖一抖缩没冒烟
K.rounds.pick = (c, t, sc, cfg) => {
  const a = K.actOf(sc.id, 'pick'), good = cfg.correct || 'left', top = cfg.top ?? 700, size = cfg.size ?? 230;
  const S = [['left', 640, cfg.left], ['right', 1280, cfg.right]];
  const w = inAny(t, waitsOf(sc, 'pick'));
  const beat = w ? (t - w.t0) / K.BEAT : 0, lit = w ? (Math.floor(beat) % 2 ? 'right' : 'left') : null, hit = w ? Math.exp(-(beat % 1) * 6) : 0;
  const st = side => {                                                               // 这一边的物品状态 {dx, dy, k}
    let dx = 0, dy = 0, k = side === lit ? 1 + 0.12 * hit : 1;
    if (!a || t < a.t0) return { dx, dy, k };
    if (side === good) { const hp = K.hopAt(t, [a.t0 + 0.14], 110, 0.45); if (hp) { dy = -hp.h; if (hp.st !== 'air') k *= 1 - 0.08 * (hp.st === 'crouch' ? hp.k : 1 - hp.k); } }
    else { if (t < a.t0 + 0.45) dx = 14 * Math.sin(t * 55); k *= 1 - U.ease.in(clamp((t - a.t0 - 0.45) / 0.25)); }
    return { dx, dy, k };
  };
  return K.round(c, t, sc, {
    ...cfg,
    cast: tweak(cfg, (who, p, i) => cheer(who, p, t, a && { t0: a.t0 + 0.3, t1: a.t1 }, i)),
    mid: (g, tt) => {
      if (cfg.mid) cfg.mid(g, tt);
      for (const [side, x, key] of S) {
        pedestal(g, x, top, (K.VOC[key] || {}).col || K.COL.teacher);
        const s = st(side); if (s.k <= 0.001) continue;
        K.item(g, key, x + s.dx, top - 4 + s.dy, size, { sx: s.k, sy: s.k });
      }
    },
    front: (g, tt, pos, L) => {
      if (a) for (const [side, x, key] of S) {
        const h = sizeOf(key, size).h;
        if (side === good) { K.starBurst(g, t, a.t0 + 0.3, x, top - h / 2, 1.2, 8, 170); check(g, x + 110, top - h - 10, 46, K.popIn(t, a.t0 + 0.3, 0.35)); }
        else K.poof(g, t, a.t0 + 0.5, x, top - h / 2, 110);
      }
      if (cfg.front) cfg.front(g, tt, pos, L);
    },
  });
};

// 数一数：cfg.items = [{key}]。场景里文字以 one…ten 开头的台词按顺序，每句开口时弹出一个物品，带数字角标；cfg.x / y / size / gap 可改排布
const NUM = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'];
K.countLines = sc => K.linesOf(sc.id).filter(l => NUM.includes((String(l.text).toLowerCase().match(/[a-z]+/) || [''])[0]));
K.rounds.count = (c, t, sc, cfg) => {
  const items = cfg.items, n = items.length, CL = K.countLines(sc);
  const gap = cfg.gap ?? Math.min(300, 1100 / Math.max(1, n - 1)), x0 = cfg.x ?? 1060, y = cfg.y ?? 800, size = cfg.size ?? 210;
  const X = i => x0 + (i - (n - 1) / 2) * gap;
  const cur = CL.findIndex(l => t >= l.t0 - 0.1 && t < l.t1 + 0.4);
  return K.round(c, t, sc, {
    ...cfg,
    cast: tweak(cfg, (who, p) => { for (const l of CL) addMv(p, K.mv.squash(t, l.t0, 60, 0.35)); }),
    front: (g, tt, pos, L) => {
      items.forEach((it, i) => {
        const l = CL[i]; if (!l || t < l.t0 - 0.05) return;
        const p = K.popIn(t, l.t0 - 0.05, 0.35), on = K.bump(t, l.t0 - 0.05, l.t1, 0.1), k = p * (1 + 0.12 * on);
        const { w, h } = sizeOf(it.key, size), col = (K.VOC[it.key] || {}).col || K.COL.teacher;
        K.item(g, it.key, X(i), y, size, { sx: k, sy: k });
        g.save(); g.translate(X(i) + w * 0.42, y - h * k - 6); g.scale(p, p);
        g.fillStyle = col; g.beginPath(); g.arc(0, 0, 42, 0, TAU); g.fill();
        K.txt(g, String(i + 1), 0, 3, 58, K.EN, '#fff');
        g.restore();
      });
      if (cfg.front) cfg.front(g, tt, pos, L);
    },
    hud: (cc, tt) => {
      if (cur >= 0) {                                                                // 正在数的那个词大字弹出来
        const l = CL[cur], it = items[Math.min(cur, n - 1)], col = (K.VOC[it.key] || {}).col || K.COL.teacher;
        const p = K.popIn(t, l.t0 - 0.1, 0.3, 2.8) * (1 - ss(l.t1 + 0.2, l.t1 + 0.4, t));
        if (p > 0.001) K.layer(cc, 'ui', g => { g.save(); g.translate(960, 190); g.scale(p, p); K.txt(g, l.text, 0, 0, 140, K.EN, col, { stroke: K.P.textStroke, sw: 26 }); g.restore(); });
      }
      if (cfg.hud) cfg.hud(cc, tt);
    },
  });
};

// 少了什么：cfg.items = [{key}] 排一排，cfg.gone 拿走的下标。动作段 dark：画面 0.3 秒暗到 0.85（角色有 <who>_cover1 帧就捂眼），最暗时拿走；动作段 reveal：弹回来
K.rounds.missing = (c, t, sc, cfg) => {
  const items = cfg.items, n = items.length, gi = cfg.gone ?? 0, d = K.actOf(sc.id, 'dark'), r = K.actOf(sc.id, 'reveal');
  const gap = cfg.gap ?? Math.min(280, 1100 / n), x0 = cfg.x ?? 960, y = cfg.y ?? 790, size = cfg.size ?? 190;
  const X = i => x0 + (i - (n - 1) / 2) * gap;
  const tHide = d ? (d.t0 + d.t1) / 2 : Infinity, tBack = r ? r.t0 : Infinity;
  const dk = d ? 0.85 * K.bump(t, d.t0, d.t1 - 0.3, 0.3) : 0;
  const gh = sizeOf(items[gi].key, size).h, wNow = inAny(t, waitsOf(sc), 0.1);
  return K.round(c, t, sc, {
    ...cfg,
    cast: tweak(cfg, (who, p, i) => {
      if (d && t >= d.t0 && t < d.t1) { const cv = pose(who, 'cover1'); if (cv) p.pose = cv; else addMv(p, K.mv.shake(t, d.t0, d.t1, 4)); }
      think(p, t, wNow, i); cheer(who, p, t, r, i);
    }),
    mid: (g, tt) => {
      if (cfg.mid) cfg.mid(g, tt);
      K.blanket(g, x0, n * gap + 80, { top: y - 50, bot: y + 70, nx: 2 * n, ny: 3 });
      items.forEach((it, i) => {
        let k = 1;
        if (i === gi) { if (t >= tHide && t < tBack) return; if (t >= tBack) k = K.popIn(t, tBack, 0.4); }
        K.item(g, it.key, X(i), y + 10, size, { sx: k, sy: k, rot: 0.03 * Math.sin(K.ambT(t) * 2 + i) });
      });
    },
    front: (g, tt, pos, L) => {
      if (d && t >= d.t1 - 0.3 && t < tBack) {                                         // 空位：虚线圈 + 问号
        const al = clamp((t - d.t1 + 0.3) / 0.3), k = 1 + 0.06 * Math.sin(t * 6);
        g.save(); g.globalAlpha *= al; g.setLineDash([18, 14]); g.strokeStyle = K.COL.teacher; g.lineWidth = 8;
        g.beginPath(); g.ellipse(X(gi), y + 10 - gh / 2, size * 0.55 * k, gh * 0.6 * k, 0, 0, TAU); g.stroke(); g.setLineDash([]);
        K.txt(g, '?', X(gi), y + 10 - gh / 2, 120 * k, K.EN, K.COL.teacher, { stroke: K.P.textStroke, sw: 20 });
        g.restore();
      }
      if (r) K.sparks(g, t, tBack, X(gi), y + 10 - gh / 2, size * 0.6, 8);
      if (cfg.front) cfg.front(g, tt, pos, L);
    },
    hud: (cc, tt) => {
      if (dk > 0.001) {
        cc.save(); cc.setTransform(1, 0, 0, 1, 0, 0); cc.globalAlpha = dk; cc.fillStyle = '#140F24'; cc.fillRect(0, 0, 1920, 1080); cc.restore();
        K.layer(cc, 'ui', g => {                                                       // 暗场里：两只闭着的眼睛 + "闭上眼睛！"
          const col = '#FFE9A8';
          g.save(); g.globalAlpha *= dk / 0.85; g.strokeStyle = col; g.lineWidth = 16; g.lineCap = 'round';
          for (const s of [-1, 1]) {
            const ex = 960 + s * 120, ey = 430 + 6 * Math.sin(t * 3);
            g.beginPath(); g.arc(ex, ey, 70, 0.15 * Math.PI, 0.85 * Math.PI); g.stroke();
            for (const a of [0.3, 0.5, 0.7]) { const ca = Math.cos(a * Math.PI), sa = Math.sin(a * Math.PI); g.beginPath(); g.moveTo(ex + ca * 70, ey + sa * 70); g.lineTo(ex + ca * 98, ey + sa * 98); g.stroke(); }
          }
          K.txt(g, '闭上眼睛！', 960, 640, 70, K.ZH, col);
          g.restore();
        });
      }
      if (cfg.hud) cfg.hud(cc, tt);
    },
  });
};

// 木头人：动作段 dance 全员扭 + 跟拍跳（一直扭到 Freeze! 开口）；freeze 空拍（从它前面那句 Freeze! 开口起）全员定住，有 cfg.poses = {who: 帧名} 就换帧；
// cfg.wobbler 在 freeze 空拍的最后 40% 越晃越大，最后倒下（第 1 次倒向 cfg.fallDir，默认 1 = 向右，之后左右轮换），镜头在最后 2 拍推近它；
// 倒下的样子保持到下一段 dance。cfg.wobbleOn（下标或下标数组）只在这几个空拍里倒，默认每个都倒
K.rounds.freeze = (c, t, sc, cfg) => {
  const B = K.BEAT, ls = K.linesOf(sc.id);
  const spans = waitsOf(sc, 'freeze').map(w => {
    const l = ls.filter(l => /freez/i.test(l.text) && l.t0 <= w.t0 + 1e-6 && l.t0 >= w.t0 - 4 * B).pop();
    return { t0: l ? l.t0 : w.t0, t1: w.t1, w };
  });
  const dances = actsOf(sc, 'dance').map(a => { const s = spans.find(s => s.t0 >= a.t1 - 1e-6 && s.t0 - a.t1 < 2 * B); return { t0: a.t0, t1: s ? s.t0 : a.t1 }; });
  const fz = inAny(t, spans), wb = cfg.wobbler;
  const WSS = wb ? (cfg.wobbleOn == null ? spans : [].concat(cfg.wobbleOn).map(i => spans[i]).filter(Boolean)) : [];
  const wobbleRot = () => {
    const k = WSS.map(s => s.w.t0 <= t).lastIndexOf(true); if (k < 0) return 0;
    const WS = WSS[k], dir = (cfg.fallDir || 1) * (k % 2 ? -1 : 1), nd = dances.find(a => a.t0 >= WS.t1 - 1e-6);
    const ws0 = WS.w.t0 + 0.6 * (WS.w.t1 - WS.w.t0), f0 = WS.t1 - 0.3, until = nd ? nd.t0 : Infinity;
    const wob = (x, q) => (0.03 + 0.17 * q * q) * Math.sin((x - ws0) * (9 + 6 * q));
    if (t < ws0 || t >= until) return 0;
    if (t < f0) return wob(t, clamp((t - ws0) / Math.max(0.1, f0 - ws0)));
    const p = clamp((t - f0) / 0.4), settle = p >= 1 ? 0.03 * dir * Math.exp(-(t - f0 - 0.4) * 8) * Math.sin((t - f0) * 30) : 0;
    return lerp(wob(f0, 1), dir * 0.5, p * p) + settle;
  };
  const dance = dances.find(a => t >= a.t0 && t < a.t1);
  return K.round(c, t, sc, {
    ...cfg,
    cast: tweak(cfg, (who, p, i) => {
      const flip = i % 2 ? -1 : 1;
      if (dance) { const m = K.mv.wiggle(t, dance.t0, dance.t1); addMv(p, { dx: flip * m.dx, dy: m.dy - 18 * Math.abs(Math.sin(Math.PI * (t - dance.t0) / B)), rot: flip * m.rot }); }
      if (fz) {
        p.still = true; const ps = cfg.poses && cfg.poses[who]; if (ps && K.has(ps)) p.pose = ps;
        addMv(p, { rot: flip * 0.08 });
      }
      if (who === wb) addMv(p, { rot: wobbleRot() });
    }),
    extraShots: L => (L[wb] ? WSS.map(WS => closeOn(L, wb, WS.t1 - 2 * B, WS.t1 + B)) : []),
    front: (g, tt, pos, L) => {
      if (dance) for (let k = 0; k < 6; k++) {                                         // 跳舞时飘音符
        const ph = K.wrap((t - dance.t0) / 2 + k / 6, 1), x = 260 + k * 280 + 30 * Math.sin(t * 2 + k), y = 760 - 460 * ph;
        note(g, x, y, Math.max(0.01, Math.sin(Math.PI * ph) * 0.9), K.P.stars[k % K.P.stars.length], 0.2 * Math.sin(t * 3 + k));
      }
      for (const s of spans) for (const k of Object.keys(pos)) K.sparks(g, t, s.t0, pos[k].x, pos[k].top + 40, 70, 5);
      if (cfg.front) cfg.front(g, tt, pos, L);
    },
    hud: (cc, tt) => {
      if (fz) { const al = 0.12 * ss(fz.t0, fz.t0 + 0.15, t); cc.save(); cc.setTransform(1, 0, 0, 1, 0, 0); cc.globalAlpha = al; cc.fillStyle = '#7FB8FF'; cc.fillRect(0, 0, 1920, 1080); cc.restore(); }
      if (cfg.hud) cfg.hud(cc, tt);
    },
  });
};
})();
