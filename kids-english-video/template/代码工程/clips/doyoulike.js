// 示范集《Do You Like Carrots?》的画面（横屏 1920×1080，30fps）。通用部分都在 lib/kids.js（K.*），这里只放这一集特有的东西：
//   VOCAB      本集单词 → 图片、中文、颜色、碎屑色
//   吃东西     举着念单词、词尾咬一口（biteAt；script.json 里 chant 的音效 at: "end", offset: -0.05 是同一个时刻）、嚼到下一个词
//   各场景     SC.<场景 id>(c, t, sc)，场景 id 和 script.json 的 scenes[].id 一一对应
// 时间全部来自 spec.data（build.py 由配音时长和节拍算出），画风来自 spec.data.style。
// 写新一集：复制这个文件改名（文件名 = script.json 的 "grammar"），改 VOCAB 和 SC。
// 规矩：代码画的东西放进 K.layer(c, kind, g => …) 里并且只用 g 画；角色用 K.ch 画在主画布 c 上。
CLIPS.doyoulike = (() => {
const { clamp, lerp, ss } = U;
const VOCAB = {
  carrots: { img: 'food_carrot', zh: '胡萝卜', col: '#F26B1D', crumb: '#FF9A3C' },
  bananas: { img: 'food_banana', zh: '香蕉', col: '#D99A00', crumb: '#FFE58A' },
  apples: { img: 'food_apple', zh: '苹果', col: '#E8394B', crumb: '#FFF1C9' },
  broccoli: { img: 'food_broccoli', zh: '西兰花', col: '#2FA84F', crumb: '#6CCB5F' },
  socks: { img: 'food_sock', zh: '袜子', col: '#2F7BFF' },
};
const COL = { bobo: '#FF7A1A', rabbit: '#EE4F96', fish: '#2F7BFF', bird: '#E3A100', teacher: '#7A4CFF' };
const SCALE = { bobo: 0.95, rabbit: 0.95, fish: 0.9, bird: 0.78 };
const WIPE = { carrots: '#FF9F43', bananas: '#FFD43B', apples: '#FF6B6B', twist: '#7BD389', quiz: '#B48CFF', outro: '#6EC3F5' };
let GY;

// ---------- 吃东西 ----------
// 咬一口时从嘴边崩出来的碎屑
function crumbs(c, t, at, x, y, col, n = 8) {
  const p = (t - at) / 0.6; if (p < 0 || p > 1) return;
  c.save(); c.globalAlpha *= 1 - p * p; c.fillStyle = col;
  for (let i = 0; i < n; i++) {
    const a = Math.PI * (0.1 + 0.35 * U.hash(i, 31)), v = 150 + 150 * U.hash(i, 32), dir = i % 2 ? 1 : -1;
    c.beginPath(); c.arc(x + dir * Math.cos(a) * v * p, y - Math.sin(a) * v * p + 380 * p * p, 6 + 6 * U.hash(i, 33), 0, 7); c.fill();
  }
  c.restore();
}
// 跟读吃东西的节奏：0 举着念单词 → 1 词尾咬一口 → 2 嚼到下一个词开口前
const biteAt = l => l.t1 - 0.05;
function eatStep(t, words) {
  let k = 0;
  for (let i = 0; i < words.length; i++) {
    const b = biteAt(words[i]), nx = words[i + 1] ? words[i + 1].t0 - 0.06 : b + 1.1;
    if (t >= b && t < b + 0.16) k = 1;
    else if (t >= b + 0.16 && t < nx) k = 2;
  }
  return k;
}
const chewSq = t => ({ sx: 1 + 0.02 * Math.sin(t * 30), sy: 1 - 0.03 * Math.sin(t * 30) });

// ---------- 场景 ----------
const SC = {};

SC.intro = (c, t, sc) => {
  const [L0, L1] = K.linesOf('intro'), up = ss(L0.t0 - 0.7, L0.t0 - 0.2, t);
  K.layer(c, 'bg', g => {
    g.fillStyle = K.P.sky; g.fillRect(0, 0, K.W, K.H); K.confetti(g, t);
    g.fillStyle = K.P.grass; g.beginPath(); g.ellipse(960, GY + 300, 1250, 330, 0, 0, 7); g.fill();
    K.blanket(g, 960, 1150, { open: U.ease.out(clamp((t - L1.t0 + 0.25) / 0.5)), top: GY - 60, bot: GY + 110 });
  });
  K.title(c, t, up);
  if (t > L0.t0 - 0.5) {
    const p = K.popIn(t, L0.t0 - 0.5, 0.45, 2), b = K.bob(t), basket = t >= L1.t0 - 0.12;
    const hop = basket ? 60 * Math.sin(clamp((t - L1.t0 + 0.12) / 0.42) * Math.PI) : 0;
    K.shadow(c, 960, GY, 150, hop);
    const P = K.spr(c, basket ? 'bobo_basket' : 'bobo_wave', 960, GY + (1 - p) * 520 + b.dy - hop, basket ? SCALE.bobo * 1.08 : 1.05,
      { rot: basket ? 0.03 * Math.sin(t * 5) : Math.sin(t * 9) * 0.03, sx: b.sx, sy: b.sy * (1 + 0.015 * K.mouthAt('bobo', t)) });
    for (const L of [L0, L1]) {
      const q = K.popIn(t, L.t0 - 0.08, 0.26) * (1 - ss(L.t1 + 0.3, L.t1 + 0.48, t));
      K.bubble(c, L.text, L.zh, 1400, P.top + 60, 1130, P.top + 120, q, COL.bobo);
    }
  }
};

// 一轮问答：波波问两遍，动物答两遍（答的时候高兴地蹦一下）；老师念单词时食物飞进动物手里；
// 跟读时动物举着食物念、词尾咬一口、嚼；第二遍波波一起念，跟着拍子蹦。
// cfg: animal, boboX, home(t) → {x, y}, opts（画动物的额外参数）, src(t) → 食物原来的位置（底边中点）,
//      size/sizeTo 食物大小, hand 食物飞到哪（相对 home）, mouth 碎屑从哪崩出来（相对 home）, plate, always, bg(g, t), front(g, t), cardX
function foodRound(c, t, sc, cfg) {
  const who = cfg.animal, key = sc.id, V = VOCAB[key];
  const ls = K.linesOf(sc.id), qs = ls.filter(l => l.who[0] === 'bobo' && l.chant == null), yes = ls.filter(l => l.who[0] === who && l.chant == null);
  const card = ls.find(l => l.card), aw = K.chantsOf(sc.id).filter(l => l.who.includes(who)), bw = K.wordsOf(sc.id, 'bobo');
  const appear = cfg.always ? -1 : qs[0].t0 - 0.2, grab = card.t0 + 0.2, land = grab + 0.5;
  const home = cfg.home(t), src = cfg.src(t), hand = { x: home.x + cfg.hand.dx, y: home.y + cfg.hand.dy };
  const wig = qs.reduce((m, q) => Math.max(m, K.bump(t, q.t0, q.t1, 0.12)), 0);
  const k = t >= land ? eatStep(t, aw) : -1, yh = K.hopAt(t, yes.map(l => l.t0), 46, 0.36);
  K.qaScene(c, t, sc, who, cfg.bg, t => {
    const bh = bw.length ? K.hopAt(t, bw, 120) : null;
    const bobo = bh ? { x: cfg.boboX, y: GY, pose: 'bobo_m2', lift: bh.h, still: true, sx: bh.st === 'air' ? 0.94 : 1.1, sy: bh.st === 'air' ? 1.08 : 0.86 } : { x: cfg.boboX, y: GY };
    let an = { ...home, ...cfg.opts };
    if (k >= 0) an = { ...an, pose: `${who}_eat${k}`, ...(k === 2 ? chewSq(t) : {}), sy: (k === 1 ? 0.96 : k === 2 ? chewSq(t).sy : 1) };
    else if (yh) an = { ...an, lift: yh.h, still: true };
    return { order: ['bobo', who], bobo, [who]: an, front: g => {
      if (cfg.front) cfg.front(g, t);
      if (cfg.plate) K.plate(g, src.x, src.y + 6, 115);
      if (t >= appear && t < grab) {                                             // 盘子上（树上）的食物，波波问的时候一蹦一蹦
        const p = cfg.always ? 1 : K.popIn(t, appear, 0.35, 2.6);
        K.item(g, key, src.x, src.y - 26 * wig * Math.abs(Math.sin(t * 9)), cfg.size * p, { rot: 0.12 * wig * Math.sin(t * 14) });
        if (!cfg.always) K.sparks(g, t, appear, src.x, src.y - cfg.size * 0.45);
      } else if (t >= grab && t < land) {                                        // 飞进动物手里
        const p = MO.cubicInOut((t - grab) / (land - grab)), P = K.arcPos(p, src, hand, 240);
        K.item(g, key, P.x, P.y, lerp(cfg.size, cfg.sizeTo || cfg.size, p), { rot: p * Math.PI * 2 });
      }
      if (t >= land && t < land + 0.5) K.sparks(g, t, land, hand.x, hand.y - 60, 110);
      for (const l of aw) crumbs(g, t, biteAt(l), home.x + cfg.mouth.dx, home.y + cfg.mouth.dy, V.crumb);
    } };
  }, null, { cardX: cfg.cardX });
}

SC.carrots = (c, t, sc) => foodRound(c, t, sc, {
  animal: 'rabbit', boboX: 600, size: 190, sizeTo: 112, plate: true,
  home: () => ({ x: 1340, y: GY }), opts: { phase: 0.1 }, src: () => ({ x: 960, y: GY + 80 }),
  hand: { dx: 0, dy: -110 }, mouth: { dx: 0, dy: -205 },
  bg: (g, t) => { K.meadow(g, t); K.blanket(g, 960, 1560); },
});

const POND = { x0: 760, top: 650 };
SC.bananas = (c, t, sc) => foodRound(c, t, sc, {
  animal: 'fish', boboX: 360, size: 170, sizeTo: 150, plate: true,
  home: t => ({ x: 1330, y: K.surf(1330, t, POND.top) + 55 }), opts: { shadow: false, bob: 0.6, phase: 0.2, bx: -120 },
  src: () => ({ x: 560, y: GY + 80 }),
  hand: { dx: -175, dy: -75 }, mouth: { dx: -60, dy: -100 },
  bg: (g, t) => { K.meadow(g, t); K.blanket(g, 370, 620); K.pond(g, POND.x0, POND.top, t, false); },
  front: (g, t) => K.pond(g, POND.x0, POND.top, t, true),
});

// 苹果树：树冠上挂几个苹果，鸟要的那个单独画（会被摘走）
const TREE = { x: 1500, top: 360 }, APPLES = [[-150, 40], [-40, -70], [100, -10], [170, 110], [10, 120], [-120, 150]];
const PICK = { x: 1385, y: 520 };
SC.apples = (c, t, sc) => foodRound(c, t, sc, {
  animal: 'bird', boboX: 560, size: 66, sizeTo: 86, always: true, cardX: 790,      // 卡片往左挪，别挡住树上的鸟
  home: () => ({ x: 1252, y: 585 }), opts: { shadow: false, phase: 0.15 }, src: () => PICK,
  hand: { dx: 0, dy: -45 }, mouth: { dx: 0, dy: -134 },
  bg: (g, t) => {
    K.meadow(g, t, { sky: K.P.sky2 }); K.blanket(g, 560, 900); K.tree(g, TREE.x, TREE.top);
    for (const [dx, dy] of APPLES) K.item(g, 'apples', TREE.x + dx, TREE.top + dy + 30, 66, { rot: 0.05 * Math.sin(t * 2 + dx) });
  },
});

SC.twist = (c, t, sc) => {
  const ls = K.linesOf('twist'), ask = ls[0], no = ls.find(l => l.text.startsWith('No')), tryL = ls.find(l => l.text === 'Try it!');
  const yum = ls.find(l => l.text.startsWith('Yummy')), card = ls.find(l => l.card), act = K.actOf('twist', 'try'), words = K.chantsOf('twist');
  const B = K.BEAT, a0 = act.t0, BX = 520, PL = { x: 820, y: GY + 82 }, hand = { x: BX + 125, y: GY - 170 };
  const show = ask.t0 + 1.3, grab = tryL.t1 - 0.05, bite = a0 + 2 * B, wow = a0 + 5 * B;
  const BF = ['bobo_chew', 'bobo_bite', 'bobo_chew'];
  // 波波：嫌弃 → 拿着端详 → 咬一口 → 嚼 → 眼睛一亮 → 好吃！ → 跟着念、一口一口吃
  let bobo = { x: BX, y: GY };
  if (t >= no.t0 - 0.12 && t < no.t1 + 0.45) bobo = { x: BX, y: GY, pose: 'bobo_yuck', rot: 0.045 * Math.sin(t * 22) };
  else if (t >= a0 && t < bite) bobo = { x: BX, y: GY, pose: 'bobo_hold', still: true, rot: -0.05 * Math.sin((t - a0) * 3.2) };
  else if (t >= bite && t < bite + 0.3) bobo = { x: BX, y: GY, pose: 'bobo_bite', still: true, sx: 1.05, sy: 0.95 };
  else if (t >= bite + 0.3 && t < wow) bobo = { x: BX, y: GY, pose: 'bobo_chew', still: true, ...chewSq(t) };
  else if (t >= wow && t < yum.t0 - 0.1) { const e = Math.exp(-(t - wow) * 7); bobo = { x: BX, y: GY, pose: 'bobo_chew', still: true, sx: 1 + 0.12 * e, sy: 1 + 0.12 * e, lift: 40 * Math.sin(clamp((t - wow) / 0.35) * Math.PI) }; }
  else if (t >= yum.t0 - 0.1 && t < card.t0 - 0.1) bobo = { x: BX, y: GY, pose: 'bobo_yum', rot: 0.04 * Math.sin(t * 7) };
  else if (t >= card.t0 - 0.1) { const k = eatStep(t, words); bobo = { x: BX, y: GY, pose: BF[k], ...(k === 2 ? chewSq(t) : {}) }; }
  // 动物们：劝波波的时候往他那边探身子，波波说好吃以后一起欢呼，跟读时跟着拍子蹦
  const lean = K.bump(t, tryL.t0 - 0.2, tryL.t1 + 0.3, 0.2), cheer = t >= wow;
  const hop = K.hopAt(t, words.map(l => l.t0), 70, 0.4);
  const animal = (who, x, y, o = {}) => cheer
    ? { x, y, pose: `${who}_laugh`, lift: hop ? hop.h : 0, still: !!hop, rot: 0.04 * Math.sin(t * 9 + x), ...o }
    : { x, y, rot: -0.08 * lean, ...o };
  const zin = K.bump(t, a0 - 0.3, yum.t1 + 0.2, 0.45);
  const cam = { z: 1 + 0.1 * zin, x: lerp(960, BX + 220, zin), y: lerp(540, 600, zin) };
  K.qaScene(c, t, sc, 'rabbit', (g, t) => { K.meadow(g, t); K.blanket(g, 800, 1200); K.pond(g, 1440, 760, t, false); }, t => ({
    order: ['bobo', 'rabbit', 'bird', 'fish'],
    bobo, rabbit: animal('rabbit', 1050, GY, { phase: 0.1 }), bird: animal('bird', 1280, GY, { phase: 0.25 }),
    fish: animal('fish', 1690, K.surf(1690, t, 760) + 55, { shadow: false, bob: 0.6, phase: 0.2 }),
    front: g => {
      K.pond(g, 1440, 760, t, true);
      K.plate(g, PL.x, PL.y + 6, 110);
      if (t >= show && t < grab) {
        const no2 = K.bump(t, no.t0, no.t1, 0.1);
        K.item(g, 'broccoli', PL.x + 12 * no2 * Math.sin(t * 30), PL.y, 170 * K.popIn(t, show, 0.35, 2.6), { rot: 0.1 * Math.sin(t * 3) });
        K.sparks(g, t, show, PL.x, PL.y - 80);
      } else if (t >= grab && t < a0) {
        const p = MO.cubicInOut((t - grab) / (a0 - grab)), P = K.arcPos(p, PL, hand, 200);
        K.item(g, 'broccoli', P.x, P.y, lerp(170, 80, p), { rot: -p * Math.PI * 2 });
      }
      crumbs(g, t, bite, BX + 24, GY - 200, VOCAB.broccoli.crumb);
      for (const l of words) crumbs(g, t, biteAt(l), BX + 24, GY - 200, VOCAB.broccoli.crumb);
      K.starBurst(g, t, wow, BX, GY - 230);                                       // 眼睛一亮：头顶一圈星星
    },
  }), cam);
  if (t >= yum.t0 - 0.1 && t < yum.t1 + 1.4) K.withCam(c, cam, () => K.layer(c, 'ui', g => K.hearts(g, t, yum.t0 - 0.1, yum.t1, BX, GY - 330)));   // 爱心画在气泡上面
  K.chorusBanner(c, t, sc, 160);
};

// 跟读环节左边的大图卡：格子桌布上一个盘子，食物在盘子上一颠一颠
function picCard(c, t, key) {
  const V = VOCAB[key], x = 120, y = 150, w = 700, h = 760, cx = x + w / 2, col = V.col;
  K.layer(c, 'ui', g => {
    g.fillStyle = K.P.drop; g.beginPath(); g.roundRect(x + 12, y + 14, w, h, 60); g.fill();
    g.fillStyle = K.P.card; g.beginPath(); g.roundRect(x, y, w, h, 60); g.fill(); g.lineWidth = 14; g.strokeStyle = col; g.stroke();
    g.save(); g.beginPath(); g.roundRect(x + 7, y + 7, w - 14, h - 14, 54); g.clip();
    g.fillStyle = K.P.cardTint; g.fillRect(x, y, w, 540);
    K.blanket(g, cx, 900, { top: y + 340, bot: y + 540, nx: 9, ny: 3 });
    g.restore();
    const ph = (t % (K.BEAT * 2)) / (K.BEAT * 2), hop = Math.abs(Math.sin(Math.PI * ph * 2)) * 34;
    K.plate(g, cx, y + 440, 200);
    K.item(g, key, cx, y + 455 - hop, 300, { rot: 0.07 * Math.sin(t * 3.3), sy: 1 + 0.03 * Math.cos(Math.PI * ph * 4) });
    const s = K.fitSize(g, key, K.EN, 600, 120);
    K.txt(g, key, cx, y + h - 140, s, K.EN, col);
    K.txt(g, V.zh, cx, y + h - 54, 62, K.ZH, K.INK);
  });
}
// 波波在右下角陪着回答：喜欢就捧着脸，不喜欢就嫌弃地摇头
SC.quiz = (c, t, sc) => K.quiz(c, t, sc, {
  pic: picCard,
  react: a => { const no = a && !/^yes/i.test(a.text); return { pose: a ? (no ? 'bobo_yuck' : 'bobo_yum') : undefined, rot: no ? 0.06 * Math.sin(t * 20) : 0 }; },
});

SC.outro = (c, t, sc) => {
  K.layer(c, 'bg', g => {
    g.fillStyle = K.P.sky; g.fillRect(0, 0, K.W, K.H); K.confetti(g, t, 34);
    g.fillStyle = K.P.grass; g.beginPath(); g.ellipse(960, GY + 330, 1300, 360, 0, 0, 7); g.fill();
    K.blanket(g, 960, 1760, { top: GY - 80, bot: GY + 130 });
  });
  const ls = K.linesOf('outro'), enter = k => (1 - K.popIn(t, sc.t0 + k * 0.12, 0.45, 2)) * 600;
  K.ch(c, 'bobo', 420, GY + enter(0), t, { pose: 'bobo_wave', rot: Math.sin(t * 9) * 0.04, s: 1.0 });
  K.ch(c, 'rabbit', 800, GY + enter(1), t, { phase: 0.1 });
  K.ch(c, 'bird', 1160, GY + enter(2), t, { phase: 0.2 });
  K.ch(c, 'fish', 1520, GY - 70 + enter(3) + 14 * Math.sin(t * 3), t, { phase: 0.3, shw: 110 });
  K.layer(c, 'prop', g => ['carrots', 'bananas', 'apples', 'broccoli'].forEach((k, i) => {
    const x = [610, 980, 1340, 1730][i], p = K.popIn(t, sc.t0 + 0.5 + i * 0.1, 0.35, 2.6);
    if (p > 0.001) K.item(g, k, x, GY + 112 - Math.abs(Math.sin((t + i * 0.3) * Math.PI / K.BEAT)) * 10, 110 * p);
  }));
  const L = ls[0];
  K.banner(c, 'Bye-bye!', '再见！', 230, K.popIn(t, L.t0 - 0.1, 0.35), COL.bobo, 130);
};

return {
  fonts: K.fonts,
  init(ctx) { K.init(ctx, { vocab: VOCAB, colors: COL, scale: SCALE, wipe: WIPE }); GY = K.GY; },
  draw(c, t) { K.frame(c, t, SC); },
};
})();
