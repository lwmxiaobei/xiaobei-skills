// 画面库 K 的扩展：安静时段、自动分镜、站位、程序动作、出场。在 kids.js 之后加载。
// 用法见 references/scene-cookbook.md「镜头和站位」「程序动作和出场」。
(() => {
const { clamp, lerp, ss } = U;
const ID = () => ({ dx: 0, dy: 0, rot: 0, sx: 1, sy: 1 });

// ---------- 安静时段：单词卡和领念期间，镜头不动、背景放慢 ----------
// 每个场景的窗口 = [第一句 card 或 chant 的 t0 − 0.3, 最后一句 chant 的 t1 + 0.3]（没有 chant 就取 card 那句）
let CW = null, CW_SRC = null;
function calmWins() {
  if (CW_SRC === K.LINES) return CW;
  CW_SRC = K.LINES; CW = [];
  for (const s of K.SCN) {
    const ls = K.linesOf(s.id), key = ls.filter(l => l.card || l.chant != null);
    if (!key.length) continue;
    const ch = ls.filter(l => l.chant != null);
    CW.push([key[0].t0 - 0.3, (ch.length ? ch[ch.length - 1] : key[key.length - 1]).t1 + 0.3]);
  }
  return CW;
}
K.calm = t => { let v = 0; for (const [a, b] of calmWins()) v = Math.max(v, K.bump(t, a, b, 0.3)); return v; };
// 背景动画用的时间：安静时段里走得慢（0.3 倍速）。云、浪、雪花、气泡这些用 K.ambT(t) 代替 t
let AT = null, AT_SRC = null;
const AH = 1 / 30;
K.ambT = t => {
  if (AT_SRC !== K.LINES) {
    AT_SRC = K.LINES;
    const end = K.SCN.length ? K.SCN[K.SCN.length - 1].t1 : 1, n = Math.ceil(end / AH) + 2;
    AT = new Float64Array(n);
    for (let i = 1; i < n; i++) AT[i] = AT[i - 1] + AH * (1 - 0.7 * K.calm((i - 0.5) * AH));
  }
  if (t <= 0) return t;
  const f = t / AH, i = Math.floor(f);
  if (i >= AT.length - 1) return AT[AT.length - 1] + (t - (AT.length - 1) * AH);
  return AT[i] + (AT[i + 1] - AT[i]) * (f - i);
};

// ---------- 自动分镜 ----------
// 头顶 y（按闭嘴帧的高度）
K.topOf = (who, y, s) => y - K.img(`${who}_m0`).height * (s ?? K.SCALE[who] ?? 0.9);
const ZM = 1.25, ZC = 1.5, RANK = { wide: 0, medium: 1, close: 2 };
const castOf = L => Object.keys(L).filter(k => L[k] && typeof L[k] === 'object' && 'x' in L[k]);
// 按台词排镜头：host 问 → 中景（host + focus），别人答 → 近景，老师念卡、齐声、等孩子、动作段 → 全景，领念 → 中景不动。
// 镜头至少 2 拍、起点在拍点上；更紧且对象都在上一个镜头里 → 缓推（ease），否则硬切（cut）；落在安静时段里一律硬切。
K.shots = (sc, L, focus, host = 'bobo') => {
  const B = K.BEAT, snap = x => Math.round(x / B) * B, cast = castOf(L);
  const X = w => (L[w] ? L[w].x : 960);
  // 推近时镜头中心不能太低：说话气泡（带中文高 178，中心在头顶上方 118）顶边要留在画面里 24 像素以上
  const top = w => (L[w] && K.has(`${w}_m0`) ? K.topOf(w, L[w].y, (K.SCALE[w] ?? 0.9) * (L[w].s ?? 1)) : 540);
  const fitY = (y, z, on) => Math.min(y, Math.min(...on.map(top)) - 207 + (540 - 24) / z);
  const wide = t0 => ({ t0, kind: 'wide', on: cast.slice(), z: 1, x: 960, y: 540 });
  const cand = [];
  for (const l of K.linesOf(sc.id)) {
    const w = l.who[0];
    if (l.who.length > 1 || l.card || w === 'teacher') cand.push(wide(snap(l.t0)));
    else if (l.chant != null) cand.push({ t0: snap(l.t0), kind: 'medium', on: [w], z: ZM, x: X(w), y: fitY(600, ZM, [w]) });
    else if (w === host) {
      const on = focus && focus !== host && L[focus] ? [host, focus] : [host], xs = on.map(X);
      if (Math.max(...xs) - Math.min(...xs) + 500 > 1920 / ZM) cand.push(wide(snap(l.t0)));    // 两个人隔太远，中景框不下：用全景
      else cand.push({ t0: snap(l.t0), kind: 'medium', on, z: ZM, x: xs.reduce((a, x) => a + x, 0) / on.length, y: fitY(600, ZM, on) });
    } else cand.push({ t0: snap(l.t0), kind: 'close', on: [w], z: ZC, x: X(w), y: fitY(680, ZC, [w]) });
  }
  for (const w of K.WAITS) if (w.scene === sc.id || (w.scene == null && w.t0 >= sc.t0 && w.t0 < sc.t1)) cand.push(wide(snap(w.t0)));
  for (const a of K.ACTS) if (a.scene === sc.id) cand.push(wide(snap(a.t0)));
  cand.sort((a, b) => a.t0 - b.t0);
  const out = [wide(sc.t0)];
  for (const c of cand) {
    const last = out[out.length - 1];
    if (c.kind === last.kind && c.on.join() === last.on.join()) continue;          // 和上一个一样：接着用
    if (c.t0 - last.t0 < 1e-6) { out[out.length - 1] = { ...c, t0: last.t0 }; continue; }   // 同一时刻：直接换掉
    if (c.t0 - last.t0 < 2 * B - 1e-6) continue;                                   // 上一个还不到 2 拍：这个不切了
    out.push(c);
  }
  if (out.length > 1 && sc.t1 - out[out.length - 1].t0 < 2 * B - 1e-6) out.pop();   // 最后一个太短：前一个延长
  for (let i = 0; i < out.length; i++) {
    const s = out[i], p = out[i - 1];
    s.t1 = i + 1 < out.length ? out[i + 1].t0 : sc.t1;
    s.ease = p && RANK[s.kind] > RANK[p.kind] && s.on.every(k => p.on.includes(k)) && K.calm(s.t0) === 0 ? 'ease' : 'cut';
  }
  return out;
};
// 镜头参数。手写镜头还可以用 {kind: 'pan', t0, t1, x0, x1, z, y}（横摇）和 {kind: 'follow', t0, t1, z, y, x: t => …}（跟拍）
const camOf = (s, t) => s.kind === 'pan' ? { z: s.z ?? 1, y: s.y ?? 540, x: lerp(s.x0, s.x1, MO.cubicInOut(clamp((t - s.t0) / (s.t1 - s.t0)))) }
  : s.kind === 'follow' ? { z: s.z ?? 1, y: s.y ?? 540, x: s.x(t) } : { z: s.z, x: s.x, y: s.y };
K.camAt = (t, shots, ww = 1920) => {
  let i = shots.findIndex(s => t < s.t1);
  if (i < 0) i = shots.length - 1;
  const s = shots[i];
  let cam = camOf(s, t);
  if (s.ease === 'ease' && i > 0 && t < s.t0 + 0.5) {
    const p = MO.cubicInOut(clamp((t - s.t0) / 0.5)), a = camOf(shots[i - 1], s.t0);
    cam = { z: lerp(a.z, cam.z, p), x: lerp(a.x, cam.x, p), y: lerp(a.y, cam.y, p) };
  }
  const z = clamp(cam.z, 1, 1.5), hw = 960 / z, hh = 540 / z;                       // 近景最多 1.5 倍：角色帧原图约 430 像素高，再大就糊
  return { z, x: clamp(cam.x, hw, ww - hw), y: clamp(cam.y, hh, 1080 - hh), ww };
};

// ---------- 站位 ----------
// 前后三排：后排小、高，前排大、低（可以被画面下边切掉一点）
const ROWS = [{ y: 820, s: 0.8 }, { y: 900, s: 0.92 }, { y: 980, s: 1.05 }];
K.row = i => ({ ...ROWS[clamp(i, 0, 2)] });
// 现成站位 → {who: {x, y, s}}，s 是相对缩放（画的时候乘到 K.SCALE[who] 上）
K.formation = (kind, whos) => {
  const L = {}, put = (w, x, r) => { const R = K.row(r); L[w] = { x, y: R.y, s: R.s }; };
  if (kind === 'faceoff') { put(whos[0], 620, 2); put(whos[1], 1300, 2); }
  else if (kind === 'triangle') { put(whos[0], 960, 0); put(whos[1], 560, 2); put(whos[2], 1360, 2); }
  else if (kind === 'high') { L[whos[0]] = { x: 1400, y: 560, s: 0.92 }; put(whos[1], 640, 2); }   // 第一个站在高处（树枝、滑梯顶），支撑物场景自己画
  else if (kind === 'path') whos.forEach((w, i) => put(w, 520 + 300 * i, 2 - i));
  else throw new Error('没有这种站位：' + kind);
  return L;
};
// 说话时身体往听的人那边倾（正值向右）：说话者 0.06，听者 0.03。host 说话时听者是 focus，别人说话时听者是 host
K.leanFor = (who, t, sc, L, focus, host = 'bobo') => {
  let r = 0;
  for (const l of K.linesOf(sc.id)) {
    if (l.who.length !== 1 || l.chant != null || l.who[0] === 'teacher') continue;
    const sp = l.who[0], li = sp === host ? focus : host;
    if (!L[sp] || !L[li] || sp === li || (who !== sp && who !== li)) continue;
    const k = K.bump(t, l.t0 - 0.25, l.t1, 0.25);
    if (!k) continue;
    const other = who === sp ? li : sp, dir = Math.sign(L[other].x - L[who].x);
    r += dir * (who === sp ? 0.06 : 0.03) * k;
  }
  return r;
};

// ---------- 程序动作：不用新图，返回 {dx, dy, rot, sx, sy}，传给 K.ch 的 move ----------
K.mvAdd = (...ms) => ms.reduce((a, m) => ({ dx: a.dx + (m.dx || 0), dy: a.dy + (m.dy || 0), rot: a.rot + (m.rot || 0), sx: a.sx * (m.sx ?? 1), sy: a.sy * (m.sy ?? 1) }), ID());
K.mv = {
  // 跳一下：蹲（压扁）→ 空中（拉长）→ 落地（压扁回弹）
  squash(t, t0, H = 160, air = 0.5) {
    const h = K.hopAt(t, [t0], H, air);
    if (!h) return ID();
    if (h.st === 'crouch') return { dx: 0, dy: 0, rot: 0, sx: 1 + 0.1 * h.k, sy: 1 - 0.15 * h.k };
    if (h.st === 'air') { const sy = 1.06 + 0.06 * Math.abs(2 * h.p - 1); return { dx: 0, dy: -h.h, rot: 0, sx: 1 - (sy - 1) * 0.7, sy }; }
    return { dx: 0, dy: 0, rot: 0, sx: 1 + 0.12 * (1 - h.k), sy: 1 - 0.18 * (1 - h.k) };
  },
  // 歪头（绕脚底转）
  tilt(t, t0, t1, a = 0.12) { const k = K.bump(t, t0, t1, 0.25); return k ? { ...ID(), rot: a * k } : ID(); },
  // 原地转一圈（水平缩放穿过 0），带一点跳
  spin(t, t0, d = 0.6) {
    if (t < t0 || t >= t0 + d) return ID();
    const p = (t - t0) / d;
    return { dx: 0, dy: -30 * Math.sin(Math.PI * p), rot: 0, sx: Math.cos(2 * Math.PI * p), sy: 1 };
  },
  // 发抖：左右快速抖，越来越小
  shake(t, t0, t1, amp = 10) {
    if (t < t0 || t > t1) return ID();
    return { ...ID(), dx: amp * Math.sin(t * 60) * (1 - 0.5 * (t - t0) / Math.max(1e-6, t1 - t0)) };
  },
  // 踮脚：抬高一点、小碎步
  tiptoe(t, t0, t1) {
    if (t < t0 || t > t1) return ID();
    return { dx: 0, dy: -(14 + 8 * Math.abs(Math.sin(Math.PI * (t - t0) / 0.15))), rot: 0, sx: 0.98, sy: 1.03 };
  },
  // 跟着拍子扭屁股：每拍换一边
  wiggle(t, t0, t1) {
    if (t < t0 || t > t1) return ID();
    const s = Math.sin(Math.PI * (t - t0) / K.BEAT);
    return { dx: 18 * s, dy: -6 * Math.abs(s), rot: 0.12 * s, sx: 1, sy: 1 };
  },
  // 身体往一边倾（dir = 1 向右，-1 向左）
  lean(t, t0, t1, dir, a = 0.06) { const k = K.bump(t, t0, t1, 0.25); return k ? { ...ID(), rot: dir * a * k } : ID(); },
  // 回头看两次：两下快速歪头，第二下带个小跳
  doubleTake(t, t0) {
    if (t < t0 || t > t0 + 0.7) return ID();
    const pulse = c => Math.exp(-(((t - c) / 0.06) ** 2));
    return { dx: 0, dy: -24 * pulse(t0 + 0.35), rot: 0.15 * pulse(t0) - 0.15 * pulse(t0 + 0.35), sx: 1, sy: 1 };
  },
};
// 落地扬尘（prop 层里画，0.5 秒）
K.dust = (g, t, t0, x, y) => {
  if (t < t0 || t > t0 + 0.5) return;
  const p = (t - t0) / 0.5;
  g.fillStyle = K.P.cloud;
  g.save(); g.globalAlpha *= 0.5 * (1 - p);
  for (let i = 0; i < 6; i++) {
    const s = i % 2 ? 1 : -1, k = 0.4 + 0.6 * ((i * 37) % 10) / 10;
    g.beginPath(); g.arc(x + s * (30 + 120 * p * k + i * 10), y - 10 - 30 * p * k, 18 + 26 * p * k, 0, 7); g.fill();
  }
  g.restore();
};

// ---------- 出场、退场：返回相对最终位置 to 的偏移 {dx, dy, rot, sx, sy, alpha} ----------
// run 从画外跑进来；pop 从地下弹上来（遮挡由场景前景负责）；drop 从天上掉下来；slide 斜着滑进来；peek 先在 o.behind 处探头两次再走出来
K.enter = (kind, t, t0, d, to, o = {}) => {
  if (t >= t0 + d) return { ...ID(), alpha: 1 };
  const p = clamp((t - t0) / d), W = K.W, e = U.ease.out(p);
  const from = o.from || (to.x < W / 2 ? 'left' : 'right'), sgn = from === 'left' ? -1 : 1;
  const dist = from === 'left' ? -(to.x + 300) : W - to.x + 300;
  if (kind === 'run') return { dx: dist * (1 - e), dy: -Math.abs(Math.sin(p * Math.PI * 6)) * 30 * (1 - p), rot: -sgn * 0.08 * (1 - p), sx: 1, sy: 1, alpha: 1 };
  if (kind === 'pop') return { dx: 0, dy: 250 * (1 - K.back(p, 2.2)), rot: 0, sx: 1 - 0.06 * Math.sin(Math.PI * p), sy: 1 + 0.1 * Math.sin(Math.PI * p), alpha: 1 };
  if (kind === 'drop') {
    const q = clamp(p / 0.85), k = clamp((p - 0.85) / 0.15);
    return { dx: 0, dy: -(to.y + 300) * (1 - q * q), rot: 0, sx: 1 + 0.12 * Math.sin(Math.PI * k), sy: 1 - 0.18 * Math.sin(Math.PI * k), alpha: 1 };
  }
  if (kind === 'slide') {
    const slope = o.slope ?? 0.4;
    return { dx: dist * (1 - e), dy: -Math.abs(dist) * slope * (1 - e), rot: -sgn * 0.25 * (1 - e), sx: 1, sy: 1, alpha: 1 };
  }
  if (kind === 'peek') {
    const bx = (o.behind && o.behind.dx) ?? 160;
    if (p < 0.6) { const q = p / 0.6; return { dx: bx, dy: 0, rot: -Math.sign(bx) * 0.25 * Math.abs(Math.sin(q * Math.PI * 2)), sx: 1, sy: 1, alpha: 1 }; }
    return { dx: bx * (1 - U.ease.inOut((p - 0.6) / 0.4)), dy: 0, rot: 0, sx: 1, sy: 1, alpha: 1 };
  }
  throw new Error('没有这种出场：' + kind);
};
// 退场 = 出场倒放：t ≤ t0 还在原位，t0 + d 之后到画外
K.exit = (kind, t, t0, d, from, o = {}) => (t <= t0 ? { ...ID(), alpha: 1 } : K.enter(kind, 2 * t0 + d - t, t0, d, from, o));
// ---------- 猫头鹰老师 ----------
// 老师的台词（who 里有 teacher，包括齐声）前 0.3 秒从右下角升上来，嘴跟着 mouth.teacher 换 owl_m0/m1/m2，说完 0.5 秒后沉下去；
// 两句隔不到 1.5 秒就一直待着。在镜头外画（不跟着推拉），整个在 y 560 以下、x 1480 以右，不挡单词卡、领念行和等孩子的提示。
// K.frame 自动调用；台本 "owl": false 关掉。
const OWL = { x: 1765, y: 1140, s: 0.72, rot: -0.08, pre: 0.3, post: 0.5, merge: 1.5, inD: 0.4, outD: 0.3 };
let OW = null, OW_SRC = null;
function owlWins() {
  if (OW_SRC === K.LINES) return OW;
  OW_SRC = K.LINES; OW = [];
  for (const l of K.LINES.filter(l => l.who.includes('teacher')).sort((a, b) => a.t0 - b.t0)) {
    const a = l.t0 - OWL.pre, b = l.t1 + OWL.post, last = OW[OW.length - 1];
    if (last && a - last[1] < OWL.merge) last[1] = Math.max(last[1], b); else OW.push([a, b]);
  }
  return OW;
}
// 这一刻猫头鹰的状态 {p 出来多少, pose, x, y 底边, s, rot, box 屏幕上的范围}，不在画面里返回 null
K.owlAt = t => {
  if (!K.OWL_ON) return null;
  const w = owlWins().find(([a, b]) => t >= a && t < b + OWL.outD);
  if (!w) return null;
  if (!K.has('owl_m0')) throw new Error(`缺素材 owl_m0：${K.TH.id} 画风的 characters/${K.TH.id}/ 里没有猫头鹰老师的帧（owl_m0 owl_m1 owl_m2），按 references/characters.md 生成，或者在 script.json 写 "owl": false 关掉`);
  const p = K.back(clamp((t - w[0]) / OWL.inD), 1.8) * (1 - ss(w[1], w[1] + OWL.outD, t));
  const pose = `owl_m${K.mouthAt('teacher', t)}`, im = K.img(pose), h = im.height * OWL.s, hw = im.width * OWL.s / 2;
  const y = OWL.y + (1 - p) * (h + 60) + K.bob(t, 0.3).dy * 0.6;
  return { p, pose, x: OWL.x, y, s: OWL.s, rot: OWL.rot, box: { x0: OWL.x - hw, x1: OWL.x + hw, y0: y - h, y1: y } };
};
// 猫头鹰说的话出对话气泡：玩法场景（台本写了 round）里老师单独说、不是单词卡 / 跟读题 / 领念的句子（口令、Let's dance!、What's this?）
K.owlLine = t => {
  const l = K.LINES.find(l => l.who.length === 1 && l.who[0] === 'teacher' && !l.card && !l.quiz && l.chant == null && t >= l.t0 - 0.08 && t < l.t1 + 0.48);
  const sc = l && K.SCN.find(s => s.id === l.scene);
  return sc && sc.round ? l : null;
};
K.owl = (c, t) => {
  const o = K.owlAt(t); if (!o) return;
  K.spr(c, o.pose, o.x, o.y, o.s, { rot: o.rot });
  const l = K.owlLine(t); if (!l) return;
  const p = K.popIn(t, l.t0 - 0.08, 0.26) * (1 - ss(l.t1 + 0.3, l.t1 + 0.48, t)) * clamp(o.p * 2);
  // 贴在它左边、和头一样高，尾巴朝右指着脸：右边站着的角色只会被挡到脚，不挡脸
  const bw = K.bubbleW(c, l.text, l.zh);
  K.bubble(c, l.text, l.zh, o.box.x0 - 20 - bw / 2, o.box.y0 + 60, o.box.x0 + 40, o.box.y0 + 75, p, K.COL.teacher);
};
})();
