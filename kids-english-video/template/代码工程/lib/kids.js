// kids.js：儿童英语动画的通用画面库 K。每集的场景文件 clips/<集>.js 在 init 里调 K.init(ctx, cfg)，然后用 K.* 画。
//
// 画风（spec.data.style）：flat 扁平矢量 / crayon 蜡笔手绘 / paper 剪纸拼贴 / clay 3D 黏土 / watercolor 水彩绘本。
// 画风分两层：
//   1. 角色、食物这些 Codex 图，生图时就是对应画风（assets/ 里放对应画风的帧）。
//   2. 代码画的背景、道具、气泡、单词卡，统一走 K.layer(c, kind, g => …)：先画进离屏画布 g，
//      画的过程中每次 g.fill() 都按画风加料（蜡笔描边、水彩边缘积色、黏土高光暗部、剪纸投影），
//      画完整层再加纸纹/蜡笔颗粒/水彩颗粒，最后带抖动滤镜贴回主画布。flat 画风直接画，不经过离屏画布。
// 所以场景代码里：代码画的东西放进 K.layer，角色用 K.ch 直接画在主画布上（中间夹着），文字照常 fillText。
// kind：'bg' 背景，'prop' 角色前面的道具，'ui' 气泡/卡片/字（颗粒和抖动减弱，保证字看得清）。
window.K = (() => {
const K = {};
const { clamp, lerp, ss } = U;
let A, W, H, FPS, D, TH, T_NOW = 0;

// ---------- 画风 ----------
const BASE_PAL = {
  sky: '#FFFBF2', sky2: '#EEF8FF', grass: '#9ED67A', grass2: '#86C863', hill: ['#D6F2BF', '#C3EAA6'],
  water: '#6EC3F5', water2: '#A9DEFB', waterFront: 'rgba(110,195,245,0.62)', foam: '#FFFFFF',
  trunk: '#B9804F', leaf: '#6DCB7A', leaf2: '#5CBB6B', cloud: '#FFFFFF', card: '#FFFFFF', cardTint: '#FFF4E2',
  drop: 'rgba(43,35,64,0.12)', ground: 'rgba(70,50,90,0.10)',
  flowers: ['#FF8FB1', '#FFFFFF', '#B48CFF', '#FF9F43'], flowerMid: '#FFE066',
  confetti: ['#FFB3C7', '#A8D8FF', '#FFE08A', '#C9B6FF', '#B8F0C0', '#FFC59E'], stars: ['#FFD43B', '#FF8FB1', '#7CC8FF', '#7BD389'],
  blanket: ['#FFFFFF', '#FF6F6F'], plate: ['#FFFFFF', '#ECE7F5'], quizBg: '#FFF6DA', quizDot: 'rgba(255,214,120,0.35)',
  yes: '#26B34A', no: '#FF5A5F', hearts: ['#FF6F91', '#FF9EB5'], textStroke: '#FFFFFF',
  title: ['#FF7A1A', '#EE4F96', '#2F7BFF', '#E3A100', '#7A4CFF'],
};
const THEMES = {
  flat: {
    label: '扁平矢量', en: 'LilitaOne-400', zh: 'PuHui-Black', zh2: 'PuHui-Bold', enK: 1, ink: '#2B2340', sub: '#6E6680', paper: '#FFFBF2',
    pal: {}, mat: null, step: 1,
  },
  crayon: {
    label: '蜡笔手绘', en: 'GochiHand-400', zh: 'LXGWWenKai-500', zh2: 'LXGWWenKai-500', enK: 1.12, ink: '#3B2A22', sub: '#7A6658', paper: '#FBF6EA',
    pal: { sky: '#FBF6EA', sky2: '#EAF4FA', grass: '#8FCB5C', grass2: '#6CB343', hill: ['#D3EAA8', '#BCDF8C'], water: '#5DB4EA', water2: '#A6DAF7',
      waterFront: 'rgba(93,180,234,0.55)', trunk: '#A8693A', leaf: '#5DBE57', leaf2: '#45A843', card: '#FFFDF7', cardTint: '#FFF3DD',
      drop: 'rgba(59,42,34,0.10)', ground: 'rgba(59,42,34,0.10)', blanket: ['#FFFDF7', '#F45B5B'], quizBg: '#FFF3D6' },
    mat: { outline: { w: 3.4, dark: 0.34 }, tooth: { a: 0.6, ui: 0.22, rot: -0.5 }, grain: 0.16, wobble: { amp: 3.2, freq: 0.03, boil: 8, ui: 0.5 } },
    step: 2, post: { paper: 0.45 },
  },
  paper: {
    label: '剪纸拼贴', en: 'LilitaOne-400', zh: 'PuHui-Black', zh2: 'PuHui-Bold', enK: 1, ink: '#3A2C24', sub: '#6F5E50', paper: '#EADCC2',
    pal: { sky: '#C4E4F1', sky2: '#D2EBF6', grass: '#7EC05A', grass2: '#5FA743', hill: ['#B8DA8E', '#9DCB72'], water: '#4FA9DE', water2: '#8CCBEE',
      waterFront: 'rgba(79,169,222,0.6)', trunk: '#9C6A3F', leaf: '#58B35C', leaf2: '#3F9B47', card: '#FFFDF5', cardTint: '#F6E7CC',
      drop: 'rgba(60,40,20,0.0)', ground: 'rgba(60,40,20,0.12)', quizBg: '#F3E3C3', quizDot: 'rgba(214,160,80,0.35)' },
    mat: { shadow: { col: 'rgba(60,40,20,0.34)', blur: 7, dx: 3, dy: 5 }, jag: { amp: 2.2, freq: 0.16, ui: 0.6 }, fiber: 0.5 },
    sprShadow: { col: 'rgba(60,40,20,0.35)', blur: 10, dx: 5, dy: 8 }, step: 2, post: { paper: 0.55, vignette: 0.18 },
  },
  clay: {
    label: '3D 黏土', en: 'LilitaOne-400', zh: 'PuHui-Black', zh2: 'PuHui-Bold', enK: 1, ink: '#3A2A40', sub: '#6E5F75', paper: '#F4ECE4',
    pal: { sky: '#C3E6F7', sky2: '#D5EEFA', grass: '#7FCF6A', grass2: '#62BA52', hill: ['#BDE7A0', '#A4DB85'], water: '#55B8F0', water2: '#9AD8F8',
      waterFront: 'rgba(85,184,240,0.6)', trunk: '#B07A4A', leaf: '#63C66A', leaf2: '#4DB257', cardTint: '#FFF1DE',
      drop: 'rgba(50,30,20,0.0)', ground: 'rgba(50,30,20,0.16)', quizBg: '#FBEBD0' },
    mat: { shadow: { col: 'rgba(50,30,20,0.26)', blur: 16, dx: 4, dy: 9 }, emboss: { hi: 'rgba(255,255,255,0.6)', lo: 'rgba(60,30,20,0.30)', blur: 16, off: 8, w: 12 }, grain: 0.07 },
    sprShadow: { col: 'rgba(50,30,20,0.30)', blur: 18, dx: 6, dy: 12 }, step: 2, post: { vignette: 0.28 },
  },
  watercolor: {
    label: '水彩绘本', en: 'Kalam-700', zh: 'LXGWWenKai-500', zh2: 'LXGWWenKai-500', enK: 0.96, ink: '#3D3A4A', sub: '#77707F', paper: '#F8F4EA',
    pal: { sky: '#F8F4EA', sky2: '#EDF3F6', grass: '#A9D48B', grass2: '#8CC26E', hill: ['#DDEBC8', '#CBE2B1'], water: '#86C5E6', water2: '#B9DDF0',
      waterFront: 'rgba(134,197,230,0.5)', trunk: '#B88A62', leaf: '#86C77E', leaf2: '#6FB56A', card: '#FFFEFA', cardTint: '#FBF0DF',
      drop: 'rgba(61,58,74,0.08)', ground: 'rgba(61,58,74,0.08)', blanket: ['#FFFEFA', '#F58A84'], quizBg: '#FBF1DD' },
    mat: { pool: { w: 16, blur: 5, dark: 0.24, a: 0.75 }, gran: 0.24, bloom: 0.3, wobble: { amp: 4, freq: 0.012, boil: 0, ui: 0.4 } },
    step: 1, post: { paper: 0.55 },
  },
};
K.THEMES = THEMES;

// ---------- 颜色 ----------
function parse(s) {
  if (s[0] === '#') { let h = s.slice(1); if (h.length === 3) h = [...h].map(x => x + x).join(''); const n = parseInt(h.slice(0, 6), 16); return [n >> 16 & 255, n >> 8 & 255, n & 255, h.length === 8 ? parseInt(h.slice(6), 16) / 255 : 1]; }
  const m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null;
  const v = m[1].split(',').map(Number); return [v[0], v[1], v[2], v.length > 3 ? v[3] : 1];
}
const rgb = (r, g, b, a = 1) => `rgba(${r | 0},${g | 0},${b | 0},${a})`;
K.shade = (s, k) => { const c = parse(s); if (!c) return s; return k >= 0 ? rgb(c[0] * (1 - k), c[1] * (1 - k), c[2] * (1 - k * 0.7), c[3]) : rgb(lerp(c[0], 255, -k), lerp(c[1], 255, -k), lerp(c[2], 255, -k), c[3]); };
const alphaOf = s => { const c = typeof s === 'string' && parse(s); return c ? c[3] : 0; };

// ---------- 纹理（可平铺的周期噪声瓦片，生成一次） ----------
const mul = s => () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
function noise(N, seed, oct) {          // oct: [[x 方向格子数, y 方向格子数, 权重]]，格子数要整除 N 才能无缝平铺
  const r = mul(seed), v = new Float32Array(N * N); let tw = 0;
  for (const [cx, cy, w] of oct) {
    const g = Array.from({ length: cx * cy }, r); tw += w;
    for (let y = 0; y < N; y++) {
      const fy = y / N * cy, y0 = Math.floor(fy), ty = fy - y0, sy = ty * ty * (3 - 2 * ty), y1 = (y0 + 1) % cy;
      for (let x = 0; x < N; x++) {
        const fx = x / N * cx, x0 = Math.floor(fx), tx = fx - x0, sx = tx * tx * (3 - 2 * tx), x1 = (x0 + 1) % cx;
        const a = g[y0 * cx + x0], b = g[y0 * cx + x1], c = g[y1 * cx + x0], d = g[y1 * cx + x1];
        v[y * N + x] += w * ((a + (b - a) * sx) * (1 - sy) + (c + (d - c) * sx) * sy);
      }
    }
  }
  for (let i = 0; i < v.length; i++) v[i] /= tw;
  return v;
}
function tile(N, fn) {
  const cv = document.createElement('canvas'); cv.width = cv.height = N;
  const g = cv.getContext('2d'), im = g.createImageData(N, N), d = im.data;
  for (let i = 0; i < N * N; i++) { const p = fn(i); d[i * 4] = p[0]; d[i * 4 + 1] = p[1]; d[i * 4 + 2] = p[2]; d[i * 4 + 3] = p[3]; }
  g.putImageData(im, 0, 0); return cv;
}
const TEX = {};
function textures() {
  if (TEX.ok) return; TEX.ok = true;
  const N = 512;
  const fine = noise(N, 11, [[N, N, 1]]);
  const streak = noise(N, 12, [[16, 256, 0.6], [32, 512, 0.4]]);            // 横向拉长的条纹（蜡笔笔触/纸纤维），用时再旋转
  const mid = noise(N, 13, [[8, 8, 0.5], [16, 16, 0.3], [32, 32, 0.2]]);
  const blot = noise(N, 14, [[4, 4, 0.6], [8, 8, 0.4]]);
  // 蜡笔：颜色没涂到的纸纹小白点（destination-out 用）
  TEX.tooth = tile(N, i => { const v = streak[i] * 0.65 + fine[i] * 0.35; const a = clamp((v - 0.56) / 0.1); return [255, 255, 255, a * 255]; });
  // 通用细颗粒（暗）
  TEX.grain = tile(N, i => [40, 30, 25, clamp((fine[i] - 0.45) * 2.2) * 255]);
  // 剪纸纸纤维：明暗细纹
  TEX.fiber = tile(N, i => { const v = streak[i] * 0.7 + fine[i] * 0.3; return v > 0.5 ? [255, 255, 255, clamp((v - 0.5) * 3) * 150] : [70, 50, 30, clamp((0.5 - v) * 3) * 130]; });
  // 水彩颗粒：细密的深色颗粒 + 大块浓淡
  TEX.gran = tile(N, i => [50, 40, 60, (clamp((fine[i] - 0.62) * 4) * 0.7 + clamp((mid[i] - 0.5) * 2) * 0.5) * 255]);
  TEX.bloom = tile(N, i => [255, 255, 255, clamp((blot[i] - 0.52) * 3) * 255]);
  // 整画面的纸（multiply 叠上去）
  TEX.paper = tile(N, i => { const v = 255 - (fine[i] - 0.5) * 22 - (mid[i] - 0.5) * 26 - clamp(streak[i] - 0.6) * 30; return [v, v - 2, v - 6, 255]; });
}
function pat(g, key, m) {
  const p = g.createPattern(TEX[key], 'repeat');
  if (m) p.setTransform(m);
  return p;
}

// ---------- 抖动（SVG 位移滤镜） ----------
// 每个画风建几张同参数不同种子的滤镜；boil > 0 时按 boil 次/秒换种子（手绘线条"沸腾"），0 = 静止
const FIL = {};
function filters() {
  const M = TH.mat; if (!M || FIL.ok) return; FIL.ok = true;
  const w = M.wobble || M.jag; if (!w) return;
  const ns = 'http://www.w3.org/2000/svg', svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('width', 0); svg.setAttribute('height', 0); svg.style.position = 'absolute';
  const reg = `filterUnits="userSpaceOnUse" x="0" y="0" width="${W}" height="${H}" color-interpolation-filters="sRGB"`;
  // 噪声只算一次：先用 feTurbulence 画成整张图，位移滤镜再用 feImage 读这张图。
  // 结果和每帧现算 feTurbulence 逐像素一致，每帧省三分之一时间。图异步加载，K.ready 之后才能渲（clip.js 会等）
  let h = '';
  for (let k = 0; k < 4; k++) h += `<filter id="ktn${k}" ${reg}><feTurbulence type="fractalNoise" baseFrequency="${w.freq}" numOctaves="2" seed="${k + 1}"/></filter>`;
  svg.innerHTML = h; document.body.appendChild(svg);
  const urls = [];
  for (let k = 0; k < 4; k++) {
    const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
    const g = cv.getContext('2d'); g.filter = `url(#ktn${k})`; g.fillRect(0, 0, W, H);
    urls.push(cv.toDataURL('image/png'));
  }
  const mk = (id, url, scale) => `<filter id="${id}" ${reg}><feImage href="${url}" x="0" y="0" width="${W}" height="${H}" preserveAspectRatio="none" result="n"/>`
    + `<feDisplacementMap in="SourceGraphic" in2="n" scale="${scale}" xChannelSelector="R" yChannelSelector="G"/></filter>`;
  svg.innerHTML = urls.map((u, k) => mk(`kw${k}`, u, w.amp * 2) + mk(`kwu${k}`, u, w.amp * 2 * (w.ui ?? 0.5))).join('');
  K.ready = Promise.all(urls.map(u => { const im = new Image(); im.src = u; return im.decode(); })).then(() => new Promise(r => setTimeout(r, 300)));
}
const boilK = t => { const w = TH.mat.wobble || TH.mat.jag; return w && w.boil ? Math.floor(t * w.boil) % 4 : 0; };

// ---------- 材质层 ----------
const BUF = [];
function buf(i) { if (!BUF[i]) { const cv = document.createElement('canvas'); cv.width = W; cv.height = H; BUF[i] = cv; } return BUF[i]; }
let depth = 0;
function patch(g, M) {
  const of = g.fill, os = g.stroke;
  g.fill = function (...a) {
    const fs = this.fillStyle;
    if (this.plain || typeof fs !== 'string' || alphaOf(fs) < 0.55 || this.globalAlpha < 0.5) return of.apply(this, a);
    if (M.outline) {                       // 蜡笔：先描一圈深色粗线，再填色盖掉里面那半，只剩外缘（重叠的圆不会露出里面的线）
      this.save(); this.shadowColor = 'transparent'; this.lineJoin = 'round'; this.lineCap = 'round';
      this.lineWidth = M.outline.w * 2; this.strokeStyle = K.shade(fs, M.outline.dark); this.globalAlpha *= 0.85; os.call(this); this.restore();
    }
    of.apply(this, a);
    if (M.pool) {                          // 水彩：边缘颜料堆积，形状内侧一圈模糊的深色
      this.save(); this.shadowColor = 'transparent'; this.clip(...a); this.filter = `blur(${M.pool.blur}px)`;
      this.lineWidth = M.pool.w; this.strokeStyle = K.shade(fs, M.pool.dark); this.globalAlpha *= M.pool.a; os.call(this); this.restore();
    }
    if (M.emboss) {                        // 黏土：沿轮廓描一圈同色线，只要它偏移的投影——左上内侧亮、右下内侧暗，形状鼓起来
      const E = M.emboss;
      this.save(); this.clip(...a); this.lineWidth = E.w; this.strokeStyle = fs;
      for (const [col, k] of [[E.hi, 1], [E.lo, -1]]) { this.shadowColor = col; this.shadowBlur = E.blur; this.shadowOffsetX = E.off * k; this.shadowOffsetY = E.off * 1.3 * k; os.call(this); }
      this.restore();
    }
  };
  return () => { g.fill = of; };
}
// 代码画的一组东西走画风材质。fn(g) 里只用 g 画（别用外面的 c）。
// 某些填充不想加料（印花、细碎小块）：g.plain = true 画完再改回 false。
K.layer = (c, kind, fn) => {
  const M = TH.mat;
  if (!M) return fn(c);
  const L = buf(depth), g = L.getContext('2d');
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.filter = 'none'; g.plain = false;
  g.shadowColor = 'transparent'; g.shadowBlur = 0; g.shadowOffsetX = 0; g.shadowOffsetY = 0;
  g.clearRect(0, 0, W, H);
  const T = c.getTransform();
  g.setTransform(T);
  if (M.shadow) { g.shadowColor = M.shadow.col; g.shadowBlur = M.shadow.blur; g.shadowOffsetX = M.shadow.dx; g.shadowOffsetY = M.shadow.dy; }
  const unpatch = patch(g, M);
  depth++;
  try { g.save(); fn(g); g.restore(); } finally { depth--; unpatch(); }
  g.setTransform(1, 0, 0, 1, 0, 0); g.shadowColor = 'transparent'; g.shadowBlur = 0; g.shadowOffsetX = 0; g.shadowOffsetY = 0;
  const ui = kind === 'ui', bk = boilK(T_NOW);
  const mT = new DOMMatrix([T.a, T.b, T.c, T.d, T.e, T.f]);                       // 纹理跟着镜头走，不会"浴室玻璃"
  const over = (key, a, op, rot = 0, shift = 0) => {
    if (a <= 0) return;
    g.globalCompositeOperation = op; g.globalAlpha = a;
    g.fillStyle = pat(g, key, mT.translate(shift * 97, shift * 61).rotate(rot * 180 / Math.PI)); g.fillRect(0, 0, W, H);
  };
  if (M.tooth) over('tooth', ui ? M.tooth.ui : M.tooth.a, 'destination-out', M.tooth.rot, bk);
  if (M.grain) over('grain', M.grain * (ui ? 0.5 : 1), 'source-atop', 0.3, bk);
  if (M.fiber) over('fiber', M.fiber * (ui ? 0.6 : 1), 'source-atop', 0.15);
  if (M.gran) over('gran', M.gran * (ui ? 0.4 : 1), 'source-atop');
  if (M.bloom) over('bloom', M.bloom * (ui ? 0.3 : 1), 'source-atop', 0, 3);
  g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1;
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0);
  if (M.wobble || M.jag) c.filter = `url(#${ui ? 'kwu' : 'kw'}${bk})`;
  c.drawImage(L, 0, 0); c.restore();
};
// 整画面收尾：纸纹、暗角
K.finish = c => {
  const F = TH.post; if (!F) return;
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0);
  if (F.paper) { c.globalCompositeOperation = 'multiply'; c.globalAlpha = F.paper; c.fillStyle = pat(c, 'paper'); c.fillRect(0, 0, W, H); }
  if (F.vignette) {
    c.globalCompositeOperation = 'multiply'; c.globalAlpha = 1;
    const gr = c.createRadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, H * 1.05);
    gr.addColorStop(0, 'rgba(255,255,255,0)'); gr.addColorStop(1, `rgba(120,90,70,${F.vignette})`); c.fillStyle = gr; c.fillRect(0, 0, W, H);
  }
  c.restore();
};

// ---------- 数据 ----------
// cfg: { vocab: {词: {img, zh, col, …}}, colors: {角色: 主色}, scale: {角色: 缩放}, wipe: {场景: 颜色}, shadowW: {角色: 脚下影子半宽} }
K.init = (ctx, cfg = {}) => {
  A = {};
  for (const q of ctx.of('asset')) A[decodeURIComponent(q.image).split('/').pop().replace(/\.png$/, '')] = ctx.IMG[q.image];
  W = ctx.W; H = ctx.H; FPS = ctx.FPS; D = ctx.data;
  const st = D.style || 'flat';
  if (!THEMES[st]) throw new Error(`没有这个画风：${st}（可选 ${Object.keys(THEMES).join(' / ')}）`);
  TH = { ...THEMES[st], id: st }; TH.pal = { ...BASE_PAL, ...TH.pal };
  K.TH = TH; K.P = TH.pal; K.EN = TH.en; K.ZH = TH.zh; K.ZH2 = TH.zh2; K.INK = TH.ink; K.SUB = TH.sub;
  K.W = W; K.H = H; K.FPS = FPS; K.BEAT = D.beat; K.LINES = D.lines || []; K.ACTS = D.acts || []; K.WAITS = D.waits || []; K.SCN = D.scenes || [];
  K.MOUTH = D.mouth || {}; K.TITLE = D.title || ''; K.TITLE_ZH = D.title_zh || '';
  K.VOC = cfg.vocab || {}; K.COL = { teacher: '#7A4CFF', ...(cfg.colors || {}) }; K.SCALE = cfg.scale || {}; K.WIPE = cfg.wipe || {};
  K.GY = cfg.ground ?? 935;
  K.ready = Promise.resolve();
  window.frameKey = (TH.step || 1) > 1 ? (t => Math.floor(t * FPS / TH.step + 1e-6)) : null;
  if (TH.mat) { textures(); filters(); }
};
K.fonts = ['PuHui-Black', 'PuHui-Bold', 'LXGWWenKai-500'];

// ---------- 小工具 ----------
K.img = n => { const im = A[n]; if (!im) throw new Error('缺素材 ' + n + '（assets/' + n + '.png）'); return im; };
K.has = n => !!A[n];
K.back = (p, s = 2.2) => MO.backOut(clamp(p), s);
K.popIn = (t, t0, d = 0.3, s = 2.4) => t < t0 ? 0 : K.back((t - t0) / d, s);
K.bump = (t, a, b, r = 0.35) => ss(a, a + r, t) * (1 - ss(b, b + r, t));
K.mouthAt = (who, t) => { const s = K.MOUTH[who]; const i = Math.round(t * FPS); return s && i >= 0 && i < s.length ? +s[i] : 0; };
K.linesOf = id => K.LINES.filter(l => l.scene === id);
K.chantsOf = id => K.LINES.filter(l => l.scene === id && l.chant != null);
K.actOf = (id, act) => K.ACTS.find(a => a.scene === id && a.act === act);
K.wordsOf = (id, who) => K.chantsOf(id).filter(l => l.who.includes(who)).map(l => l.t0);
K.arcPos = (p, a, b, h) => ({ x: lerp(a.x, b.x, p), y: lerp(a.y, b.y, p) - 4 * p * (1 - p) * h });
K.wrap = (x, span) => ((x % span) + span) % span;

// 精灵：按比例画，锚点默认底边中点。画风有角色投影（剪纸、黏土）时自动带上，o.cast === false 关掉
K.spr = (c, n, x, y, s, o = {}) => {
  const im = K.img(n), w = im.width * s, h = im.height * s, ax = o.ax ?? 0.5, ay = o.ay ?? 1;
  c.save(); c.translate(x, y); if (o.rot) c.rotate(o.rot); c.scale((o.flip ? -1 : 1) * (o.sx ?? 1), o.sy ?? 1);
  if (o.alpha != null) c.globalAlpha *= o.alpha;
  const S = TH.sprShadow;
  if (S && o.cast !== false && c === K.MAIN) { c.shadowColor = S.col; c.shadowBlur = S.blur; c.shadowOffsetX = S.dx; c.shadowOffsetY = S.dy; }
  c.imageSmoothingQuality = 'high'; c.drawImage(im, -ax * w, -ay * h, w, h); c.restore();
  return { w, h, top: y - ay * h * (o.sy ?? 1) };
};
// 跟着节拍一颠一颠：拍点上落地压扁，拍子中间最高
K.bob = (t, k = 0) => {
  const ph = (((t + k) / K.BEAT) % 1 + 1) % 1, hit = Math.exp(-ph * 9);
  return { dy: -9 * Math.sin(Math.PI * ph), sx: 1 + 0.035 * hit, sy: 1 - 0.035 * hit };
};
K.shadow = (c, x, y, w, lift = 0) => {
  const k = 1 - Math.min(lift / 500, 0.55);
  c.fillStyle = TH.pal.ground; c.beginPath(); c.ellipse(x, y + 6, w * k, w * k * 0.15, 0, 0, 7); c.fill();
};
// 角色：默认按配音口型换帧（<who>_m0/m1/m2）、跟拍子颠。o.pose 指定别的帧
K.ch = (c, who, x, y, t, o = {}) => {
  const m = o.mouth ?? K.mouthAt(who, t);
  const name = o.pose || `${who}_m${m}`;
  const b = o.still ? { dy: 0, sx: 1, sy: 1 } : K.bob(t, o.phase || 0);
  const s = o.s ?? K.SCALE[who] ?? 0.9, lift = o.lift || 0;
  const talk = 1 + 0.012 * (o.pose ? m : 0);
  if (o.shadow !== false) K.shadow(c, x, y, s * (o.shw || 150), lift);
  return K.spr(c, name, x, y + b.dy * (o.bob ?? 1) - lift, s,
    { flip: o.flip, sx: b.sx * (o.sx || 1), sy: b.sy * talk * (o.sy || 1), rot: o.rot, alpha: o.alpha, cast: o.cast });
};
// 文字。英文字体按画风换，enK 补偿不同字体的视觉大小
const famK = fam => fam === TH.en ? TH.enK : 1;
K.txt = (c, s, x, y, size, fam, col, o = {}) => {
  size *= famK(fam);
  c.save(); c.font = `${size}px "${fam}"`; c.textAlign = o.align || 'center'; c.textBaseline = 'middle';
  if (o.alpha != null) c.globalAlpha *= o.alpha;
  if (o.stroke) { c.lineJoin = 'round'; c.strokeStyle = o.stroke; c.lineWidth = o.sw || size * 0.18; c.strokeText(s, x, y); c.shadowColor = 'transparent'; }
  c.fillStyle = col; c.fillText(s, x, y); c.restore();
};
K.tw = (c, s, size, fam) => { c.save(); c.font = `${size * famK(fam)}px "${fam}"`; const w = c.measureText(s).width; c.restore(); return w; };
K.fitSize = (c, s, fam, maxW, max) => Math.min(max, max * maxW / Math.max(1, K.tw(c, s, max, fam)));
K.star = (c, x, y, r, rot, col) => {
  c.save(); c.translate(x, y); c.rotate(rot); c.fillStyle = col; c.beginPath();
  for (let i = 0; i < 10; i++) { const a = i / 10 * Math.PI * 2 - Math.PI / 2, rr = i % 2 ? r * 0.45 : r; c.lineTo(Math.cos(a) * rr, Math.sin(a) * rr); }
  c.closePath(); c.fill(); c.restore();
};
K.heart = (c, x, y, r, col) => {
  c.fillStyle = col; c.beginPath(); c.moveTo(x, y + r * 0.9);
  c.bezierCurveTo(x - r * 1.5, y - r * 0.1, x - r * 0.6, y - r * 1.2, x, y - r * 0.35);
  c.bezierCurveTo(x + r * 0.6, y - r * 1.2, x + r * 1.5, y - r * 0.1, x, y + r * 0.9); c.fill();
};
// 物品图（vocab 里的 img）：size 是长边像素，锚点默认底边中点
K.item = (c, key, x, y, size, o = {}) => {
  const n = K.VOC[key] ? K.VOC[key].img : key, im = K.img(n);
  return K.spr(c, n, x, y, size / Math.max(im.width, im.height), o);
};

// ---------- 气泡、横幅 ----------
// 对话气泡：英文大字 + 中文小字，尾巴从底边指向说话的人。在主画布上调，自己会进 ui 材质层
K.bubble = (c, en, zh, cx, cy, tx, ty, p, col) => {
  if (p <= 0.001) return;
  K.layer(c, 'ui', g => bubbleRaw(g, en, zh, cx, cy, tx, ty, p, col));
};
function bubbleRaw(c, en, zh, cx, cy, tx, ty, p, col) {
  const { EN, ZH2 } = K;
  const bw = Math.max(K.tw(c, en, 70, EN), zh ? K.tw(c, zh, 38, ZH2) : 0) + 90, bh = zh ? 178 : 124, r = 46;
  cx = clamp(cx, bw / 2 + 24, W - bw / 2 - 24);
  const x = cx - bw / 2, y = cy - bh / 2, bx = clamp(tx, x + r + 34, x + bw - r - 34);
  c.save(); c.translate(tx, ty); c.scale(p, p); c.translate(-tx, -ty);
  const path = (dx, dy) => {
    c.beginPath(); c.moveTo(x + r + dx, y + dy); c.lineTo(x + bw - r + dx, y + dy); c.quadraticCurveTo(x + bw + dx, y + dy, x + bw + dx, y + r + dy);
    c.lineTo(x + bw + dx, y + bh - r + dy); c.quadraticCurveTo(x + bw + dx, y + bh + dy, x + bw - r + dx, y + bh + dy);
    c.lineTo(bx + 30 + dx, y + bh + dy); c.lineTo(tx + dx, ty + dy); c.lineTo(bx - 30 + dx, y + bh + dy);
    c.lineTo(x + r + dx, y + bh + dy); c.quadraticCurveTo(x + dx, y + bh + dy, x + dx, y + bh - r + dy);
    c.lineTo(x + dx, y + r + dy); c.quadraticCurveTo(x + dx, y + dy, x + r + dx, y + dy); c.closePath();
  };
  path(8, 10); c.fillStyle = TH.pal.drop; c.fill();
  path(0, 0); c.fillStyle = TH.pal.card; c.fill(); c.lineJoin = 'round'; c.lineWidth = 7; c.strokeStyle = col; c.stroke();
  K.txt(c, en, cx, y + (zh ? 66 : bh / 2 + 2), 70, K.EN, K.INK);
  if (zh) K.txt(c, zh, cx, y + 134, 38, K.ZH2, K.SUB);
  c.restore();
}
// 顶部横幅：齐声的台词、老师的话
K.banner = (c, en, zh, cy, p, col = K.INK, size = 104) => {
  if (p <= 0.001) return;
  K.layer(c, 'ui', g => {
    const bw = Math.max(K.tw(g, en, size, K.EN), zh ? K.tw(g, zh, 46, K.ZH2) : 0) + 120, bh = zh ? size + 112 : size + 60;
    g.save(); g.translate(960, cy); g.scale(p, p);
    g.fillStyle = TH.pal.drop; g.beginPath(); g.roundRect(-bw / 2 + 8, -bh / 2 + 10, bw, bh, 50); g.fill();
    g.fillStyle = TH.pal.card; g.beginPath(); g.roundRect(-bw / 2, -bh / 2, bw, bh, 50); g.fill();
    g.lineWidth = 8; g.strokeStyle = col; g.stroke();
    K.txt(g, en, 0, zh ? -bh / 2 + 30 + size / 2 : 4, size, K.EN, col);
    if (zh) K.txt(g, zh, 0, bh / 2 - 46, 46, K.ZH2, K.SUB);
    g.restore();
  });
};
// 单人台词气泡：pos[who] = {x, top, bx?}；齐声、老师、跟读、单词卡不在这里画
K.bubbles = (c, t, sc, pos) => {
  const ls = K.linesOf(sc.id).filter(l => l.chant == null && !l.card && l.who.length === 1 && l.who[0] !== 'teacher' && pos[l.who[0]]);
  const on = ls.map(l => [l, K.popIn(t, l.t0 - 0.08, 0.26) * (1 - ss(l.t1 + 0.3, l.t1 + 0.48, t))]).filter(([, p]) => p > 0.001);
  if (!on.length) return;
  K.layer(c, 'ui', g => { for (const [l, p] of on) { const P = pos[l.who[0]]; bubbleRaw(g, l.text, l.zh, P.x + (P.bx || 0), P.top - 118, P.x, P.top - 16, p, K.COL[l.who[0]] || K.INK); } });
};
K.chorusBanner = (c, t, sc, cy = 150) => {
  for (const l of K.linesOf(sc.id)) {
    if (l.who.length < 2 || l.chant != null) continue;
    K.banner(c, l.text, l.zh, cy, K.popIn(t, l.t0 - 0.1, 0.32) * (1 - ss(l.t1 + 0.5, l.t1 + 0.7, t)), K.COL.teacher);
  }
};

// ---------- 背景 ----------
K.clouds = (c, t, scroll = 0, n = 4, y0 = 120) => {
  for (let i = 0; i < n; i++) {
    const sp = 12 + U.hash(i, 3) * 14, span = W + 500;
    const x = ((U.hash(i, 1) * span + t * sp - scroll * 0.15) % span + span) % span - 250, y = y0 + U.hash(i, 2) * 220, k = 0.7 + U.hash(i, 4) * 0.6;
    c.fillStyle = TH.pal.cloud; c.beginPath();
    c.ellipse(x, y, 90 * k, 46 * k, 0, 0, 7); c.ellipse(x + 70 * k, y + 10 * k, 60 * k, 36 * k, 0, 0, 7); c.ellipse(x - 66 * k, y + 14 * k, 54 * k, 30 * k, 0, 0, 7); c.fill();
  }
};
K.flower = (c, x, y, k, col) => {
  c.strokeStyle = TH.pal.grass2; c.lineWidth = 6 * k; c.beginPath(); c.moveTo(x, y); c.lineTo(x, y - 34 * k); c.stroke();
  c.fillStyle = col; for (let i = 0; i < 5; i++) { const a = i / 5 * Math.PI * 2; c.beginPath(); c.arc(x + Math.cos(a) * 11 * k, y - 40 * k + Math.sin(a) * 11 * k, 9 * k, 0, 7); c.fill(); }
  c.fillStyle = TH.pal.flowerMid; c.beginPath(); c.arc(x, y - 40 * k, 8 * k, 0, 7); c.fill();
};
// 草地：远山 + 草坪 + 小花；o.scroll 让场景往左滚（跑步段），o.sky 天空色。在 K.layer 里调
K.meadow = (c, t, o = {}) => {
  const P = TH.pal, sx = o.scroll || 0, GY = K.GY;
  c.fillStyle = o.sky || P.sky; c.fillRect(0, 0, W, H);
  K.clouds(c, t, sx);
  for (let layer = 0; layer < 2; layer++) {
    const span = 1500, par = layer ? 0.45 : 0.25;
    c.fillStyle = P.hill[layer];
    for (let i = -1; i < 3; i++) {
      const x = K.wrap(i * span + (layer ? 600 : 0) - sx * par, span * 2) - 400;
      c.beginPath(); c.ellipse(x, GY + 40, 700 - layer * 120, 260 - layer * 70, 0, Math.PI, 0); c.fill();
      c.beginPath(); c.ellipse(x + 750, GY + 40, 560, 200 - layer * 50, 0, Math.PI, 0); c.fill();
    }
  }
  c.fillStyle = P.grass; c.beginPath(); c.moveTo(0, H);
  for (let x = 0; x <= W; x += 40) c.lineTo(x, GY - 14 + 8 * Math.sin((x + sx) * 0.012));
  c.lineTo(W, H); c.closePath(); c.fill();
  c.fillStyle = P.grass2;
  for (let i = 0; i < 14; i++) { const x = K.wrap(i * 157 - sx, W + 200) - 100, y = GY + 50 + U.hash(i, 7) * 90; c.beginPath(); c.ellipse(x, y, 22, 7, 0, 0, 7); c.fill(); }
  for (let i = 0; i < 9; i++) { const x = K.wrap(i * 233 + 60 - sx, W + 200) - 100; K.flower(c, x, GY + 70 + U.hash(i, 9) * 80, 0.9 + U.hash(i, 8) * 0.4, P.flowers[i % P.flowers.length]); }
};
// 池塘：front=false 画水体，front=true 画盖在角色前面的半透明水面（鱼看起来半截在水里）
K.surf = (x, t, top) => top + 7 * Math.sin(x * 0.018 + t * 3.2) + 4 * Math.sin(x * 0.041 - t * 2.1);
K.pond = (c, x0, top, t, front) => {
  const P = TH.pal;
  c.save(); c.beginPath(); c.moveTo(x0 - 90, H + 10); c.quadraticCurveTo(x0 - 30, top + 30, x0 + 90, K.surf(x0 + 90, t, top));
  for (let x = x0 + 90; x <= W + 20; x += 20) c.lineTo(x, K.surf(x, t, top));
  c.lineTo(W + 20, H + 10); c.closePath();
  if (!front) {
    c.fillStyle = P.water; c.fill(); c.clip();
    c.strokeStyle = P.water2; c.lineWidth = 8; c.lineCap = 'round';
    for (let i = 0; i < 6; i++) { const y = top + 70 + i * 55, x = x0 + 120 + K.wrap(i * 260 + t * 30, W - x0) * 0.8; c.beginPath(); c.moveTo(x, y); c.lineTo(x + 70, y); c.stroke(); }
  } else { c.fillStyle = P.waterFront; c.fill(); c.strokeStyle = P.foam; c.lineWidth = 6; c.stroke(); }
  c.restore();
};
K.tree = (c, x, top) => {
  const P = TH.pal, GY = K.GY;
  c.fillStyle = P.trunk; c.beginPath(); c.roundRect(x - 38, top + 120, 76, GY - top - 100, 20); c.fill();
  c.strokeStyle = P.trunk; c.lineWidth = 26; c.lineCap = 'round'; c.beginPath(); c.moveTo(x - 10, top + 245); c.quadraticCurveTo(x - 120, top + 250, x - 260, top + 236); c.stroke();
  c.fillStyle = P.leaf;
  for (const [dx, dy, r] of [[0, 40, 190], [-150, 100, 120], [150, 90, 130], [-60, -60, 130], [90, -40, 120]]) { c.beginPath(); c.arc(x + dx, top + dy, r, 0, 7); c.fill(); }
  c.fillStyle = P.leaf2;
  for (const [dx, dy, r] of [[60, 110, 60], [-90, 60, 46], [20, -20, 40]]) { c.beginPath(); c.arc(x + dx, top + dy, r, 0, 7); c.fill(); }
};
K.confetti = (c, t, n = 26) => {
  const cols = TH.pal.confetti;
  for (let i = 0; i < n; i++) {
    const x = U.hash(i, 11) * W, y = K.wrap(U.hash(i, 12) * H + t * (14 + U.hash(i, 13) * 20), H + 80) - 40, r = 10 + U.hash(i, 14) * 16;
    c.save(); c.globalAlpha *= 0.7; c.fillStyle = cols[i % cols.length]; c.beginPath(); c.arc(x + 20 * Math.sin(t * 0.8 + i), y, r, 0, 7); c.fill(); c.restore();
  }
};
// 野餐布：近大远小的梯形格子布，open 控制从中间往两边铺开
K.blanket = (c, cx, w, o = {}) => {
  const GY = K.GY, top = o.top ?? GY - 70, bot = o.bot ?? GY + 120, open = o.open ?? 1, nx = o.nx || 10, ny = o.ny || 4, [c0, c1] = o.cols || TH.pal.blanket;
  if (open <= 0.001) return;
  const P = (u, v) => [cx + (u * 2 - 1) * lerp(w * 0.78, w, v) / 2 * open, lerp(top, bot, v)];
  const quad = (a, b, d, e, dx = 0, dy = 0) => { c.beginPath(); c.moveTo(a[0] + dx, a[1] + dy); c.lineTo(b[0] + dx, b[1] + dy); c.lineTo(d[0] + dx, d[1] + dy); c.lineTo(e[0] + dx, e[1] + dy); c.closePath(); c.fill(); };
  c.fillStyle = TH.pal.ground; quad(P(0, 0), P(1, 0), P(1, 1), P(0, 1), 8, 12);
  c.fillStyle = c0; quad(P(0, 0), P(1, 0), P(1, 1), P(0, 1));
  c.save(); c.shadowColor = 'transparent'; c.fillStyle = c1; c.plain = true;      // 格子是印在布上的：不要各自的投影、描边、鼓包
  for (let i = 0; i < nx; i++) for (let j = 0; j < ny; j++) if ((i + j) % 2 === 0)
    quad(P(i / nx, j / ny), P((i + 1) / nx, j / ny), P((i + 1) / nx, (j + 1) / ny), P(i / nx, (j + 1) / ny));
  c.plain = false; c.restore();
};
K.plate = (c, x, y, r = 120) => {
  const [p0, p1] = TH.pal.plate;
  c.fillStyle = TH.pal.ground; c.beginPath(); c.ellipse(x + 6, y + 10, r, r * 0.3, 0, 0, 7); c.fill();
  c.fillStyle = p0; c.beginPath(); c.ellipse(x, y, r, r * 0.3, 0, 0, 7); c.fill();
  c.fillStyle = p1; c.beginPath(); c.ellipse(x, y + 2, r * 0.68, r * 0.19, 0, 0, 7); c.fill();
};
// 跟读环节的底：浅色底 + 圆点
K.dots = c => {
  c.fillStyle = TH.pal.quizBg; c.fillRect(0, 0, W, H);
  c.fillStyle = TH.pal.quizDot;
  for (let i = 0; i < 12; i++) for (let j = 0; j < 7; j++) { c.beginPath(); c.arc(i * 170 + (j % 2) * 85 + 40, j * 170 + 40, 16, 0, 7); c.fill(); }
};

// ---------- 特效 ----------
K.sparks = (c, t, t0, x, y, r0 = 100, n = 6) => {
  const p = (t - t0) / 0.6; if (p < 0 || p > 1) return;
  const S = TH.pal.stars;
  for (let i = 0; i < n; i++) {
    const a = i / n * Math.PI * 2 + 0.4, d = r0 + 80 * p;
    c.save(); c.globalAlpha *= 1 - p; K.star(c, x + Math.cos(a) * d, y + Math.sin(a) * d * 0.75, 12 + 8 * (1 - p), t * 4 + i, S[i % 3]); c.restore();
  }
};
// 头顶往上飘的小爱心
K.hearts = (c, t, t0, t1, x, y) => {
  for (let i = 0; i < 7; i++) {
    const s = t0 + i * 0.3; if (s > t1) break;
    const p = (t - s) / 1.3; if (p < 0 || p > 1) continue;
    const hx = x + (i % 2 ? 1 : -1) * (150 + 60 * U.hash(i, 41)) + 14 * Math.sin(t * 5 + i), hy = y - 220 * p;
    c.save(); c.globalAlpha *= Math.min(1, (1 - p) * 2.5); K.heart(c, hx, hy, 20 + 10 * U.hash(i, 42), TH.pal.hearts[i % 2]); c.restore();
  }
};
// 一圈转着散开的星星（眼睛一亮、答对了）
K.starBurst = (c, t, t0, x, y, dur = 1.2, n = 8, r = 190) => {
  if (t < t0 || t >= t0 + dur) return;
  const p = (t - t0) / dur, S = TH.pal.stars;
  for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2 + t, d = r + 60 * p; c.save(); c.globalAlpha *= 1 - p; K.star(c, x + Math.cos(a) * d, y + Math.sin(a) * d * 0.8, 24, t * 4 + i, S[i % S.length]); c.restore(); }
};

// ---------- 单词卡、跟读单词行 ----------
// 老师念单词（带 card 的那句）时，卡片（物品图 + 英文 + 中文）从上面弹出来；跟读一开始缩到左上角当角标。
// o.x：卡片弹出时的中心 x（别挡住角色），默认 960
K.wordCard = (c, t, sc, o = {}) => {
  const L = K.LINES.find(l => l.scene === sc.id && l.card); if (!L || t < L.t0 - 0.12) return;
  const key = L.card.en, V = K.VOC[key] || { col: K.INK };
  const first = K.chantsOf(sc.id).find(l => l.t0 > L.t0);
  const tb = first ? first.t0 - 0.32 : Infinity;
  const p = K.popIn(t, L.t0 - 0.12, 0.42), q = ss(tb, tb + 0.35, t);
  const out = 1 - ss(sc.t1 - 0.5, sc.t1 - 0.2, t);
  const KS = 0.42, k = lerp(1, KS, q) * p * out * (1 + 0.04 * K.mouthAt('teacher', t));
  if (k <= 0.001) return;
  const X0 = o.x || 960;
  K.layer(c, 'ui', g => {
    const pic = V.img && K.has(V.img), ew = Math.max(K.tw(g, L.card.en, 150, K.EN), K.tw(g, L.card.zh, 64, K.ZH));
    const cw = pic ? ew + 340 : ew + 160, chh = 300, fx = -cw / 2 + 155, tx = pic ? fx + 135 + ew / 2 : 0;
    g.save(); g.translate(lerp(X0, 40 + cw * KS / 2, q), lerp(215, 100, q)); g.scale(k, k); g.rotate(lerp(-0.03, -0.06, q));
    g.fillStyle = TH.pal.drop; g.beginPath(); g.roundRect(-cw / 2 + 10, -chh / 2 + 12, cw, chh, 48); g.fill();
    g.fillStyle = TH.pal.card; g.beginPath(); g.roundRect(-cw / 2, -chh / 2, cw, chh, 48); g.fill();
    g.lineWidth = 12; g.strokeStyle = V.col; g.stroke();
    if (pic) K.item(g, key, fx, 0, 220, { ay: 0.5, rot: 0.08 * Math.sin(t * 3) });
    K.txt(g, L.card.en, tx, -32, 150, K.EN, V.col);
    K.txt(g, L.card.zh, tx, 92, 64, K.ZH, K.INK);
    g.restore();
    if (q < 1 && p > 0.5) for (let i = 0; i < 6; i++) {                       // 弹出时周围冒几颗星
      const a = i / 6 * Math.PI * 2 + 0.3, d = cw / 2 + 40 + 80 * ss(L.t0, L.t0 + 0.6, t), al = 1 - ss(L.t0 + 0.2, L.t0 + 0.7, t);
      g.save(); g.globalAlpha = al * (1 - q); K.star(g, X0 + Math.cos(a) * d, 215 + Math.sin(a) * d * 0.4, 18, t * 3 + i, TH.pal.stars[i % 3]); g.restore();
    }
  });
};
// 领念/跟念：Carrots! Carrots! Carrots! 一个词一个词蹦出来排成一行（每组 chant 一行，下一组接着替换）。col 默认用卡片单词的颜色
K.chantRow = (c, t, sc, col) => {
  const all = K.chantsOf(sc.id); if (!all.length) return;
  const starts = all.filter(l => l.chant === 0).map(l => l.t0);
  let gi = -1; for (let i = 0; i < starts.length; i++) if (t >= starts[i] - 0.05) gi = i;
  if (gi < 0) return;
  const words = all.filter(l => l.t0 >= starts[gi] - 1e-6 && (gi + 1 >= starts.length || l.t0 < starts[gi + 1] - 1e-6));
  const fade = gi + 1 >= starts.length ? 1 - ss(sc.t1 - 0.6, sc.t1 - 0.25, t) : 1;
  const card = K.LINES.find(l => l.scene === sc.id && l.card);
  col = col || (card && K.VOC[card.card.en] ? K.VOC[card.card.en].col : K.COL.teacher);
  const n = words.length, gap = Math.min(560, 1700 / n);
  if (!words.some(l => t >= l.t0 - 0.03)) return;
  K.layer(c, 'ui', g => words.forEach((l, k) => {
    if (t < l.t0 - 0.03) return;
    const p = K.popIn(t, l.t0 - 0.03, 0.28, 2.8), on = K.bump(t, l.t0 - 0.05, l.t1, 0.12), size = K.fitSize(g, l.text, K.EN, gap - 60, 130);
    const m = k - (n - 1) / 2;
    g.save(); g.translate(960 + m * gap, 235); g.rotate(m * 0.06); g.scale(p * (0.9 + 0.16 * on) * fade, p * (0.9 + 0.16 * on) * fade);
    K.txt(g, l.text, 0, 0, size, K.EN, col, { stroke: TH.pal.textStroke, sw: size * 0.19 });
    if (l.zh) K.txt(g, l.zh, 0, size * 0.5 + 42, 46, K.ZH, K.INK, { stroke: TH.pal.textStroke, sw: 12, alpha: 0.85 });
    g.restore();
  }));
};

// ---------- 镜头、问答场景骨架 ----------
// 动物（非 bobo、非老师）单独说话时镜头稍微推近、往它那边偏
K.camFor = (t, sc, x, host = 'bobo') => {
  let w = 0;
  for (const l of K.linesOf(sc.id)) if (l.who.length === 1 && l.who[0] !== host && l.who[0] !== 'teacher' && l.chant == null) w = Math.max(w, K.bump(t, l.t0 - 0.25, l.t1 + 0.15));
  return { z: 1 + 0.06 * w, x: lerp(960, x, 0.22 * w), y: lerp(540, 600, w) };
};
K.withCam = (c, cam, fn) => {
  const hw = 960 / cam.z, hh = 540 / cam.z, x = clamp(cam.x, hw, W - hw), y = clamp(cam.y, hh, H - hh);   // 推近时不露出画布外
  c.save(); c.translate(960, 540); c.scale(cam.z, cam.z); c.translate(-x, -y); fn(); c.restore();
};
// 原地跳一下：crouch → air → land
K.hopAt = (t, times, Hh = 170, air = 0.5) => {
  for (const w of times) {
    if (t >= w - 0.14 && t < w) return { st: 'crouch', h: 0, k: (t - w + 0.14) / 0.14 };
    if (t >= w && t < w + air) { const p = (t - w) / air; return { st: 'air', h: 4 * p * (1 - p) * Hh, p }; }
    if (t >= w + air && t < w + air + 0.12) return { st: 'land', h: 0, k: (t - w - air) / 0.12 };
  }
  return null;
};
// 一个问答场景：背景（bg 材质层）→ 角色（主画布）→ 前景（prop 材质层）→ 气泡，都在镜头里；单词卡和跟读行在镜头外。
// layout(t) → { order: [角色…], <角色>: {x, y, pose?, …K.ch 的参数} 或 {draw: () => {top}}, front?(g) }
K.qaScene = (c, t, sc, focus, drawBg, layout, cam, o = {}) => {
  const pos = {}, L = layout(t);
  K.withCam(c, cam || K.camFor(t, sc, L[focus] ? L[focus].x : 960), () => {
    K.layer(c, 'bg', g => drawBg(g, t));
    for (const who of L.order) { const p = L[who]; const r = p.draw ? p.draw() : K.ch(c, who, p.x, p.y, t, p); pos[who] = { x: p.x, top: p.top ?? r.top, bx: p.bx }; }
    if (L.front) K.layer(c, 'prop', g => L.front(g));
    K.bubbles(c, t, sc, pos);
  });
  K.wordCard(c, t, sc, { x: o.cardX });
  K.chantRow(c, t, sc);
};

// ---------- 片头标题 ----------
// 标题一个字母一个字母从上面掉下来，up 0→1 把标题从中间挪到上面变小
K.title = (c, t, up, o = {}) => {
  const T = K.TITLE, cols = TH.pal.title;
  K.layer(c, 'ui', g => {
    const fit = 1700 / K.tw(g, T, 100, K.EN) * 100;
    const size = lerp(Math.min(170, fit), Math.min(118, fit * 0.7), up), ty = lerp(o.y0 ?? 390, o.y1 ?? 170, up);
    g.save(); g.font = `${size * TH.enK}px "${K.EN}"`; const full = g.measureText(T).width; g.restore();
    let x = 960 - full / 2, ci = 0;
    for (let i = 0; i < T.length; i++) {
      const chr = T[i], w = K.tw(g, chr, size, K.EN), t0 = (o.start ?? 0.25) + i * 0.09;
      if (chr !== ' ' && t >= t0) {
        const p = K.back((t - t0) / 0.4, 3), b = K.bob(t, i * 0.06);
        g.save(); g.translate(x + w / 2, ty - (1 - p) * 300 + b.dy * 0.8); g.rotate(Math.sin(t * 2 + i) * 0.05); g.scale(b.sx, b.sy);
        K.txt(g, chr, 0, 0, size, K.EN, cols[ci % cols.length], { stroke: TH.pal.textStroke, sw: size * 0.16 }); g.restore();
        ci++;
      }
      x += w;
    }
    if (K.TITLE_ZH) K.txt(g, K.TITLE_ZH, 960, ty + size * 0.74, lerp(64, 46, up), K.ZH, K.INK, { alpha: ss(o.zhAt ?? 2.3, (o.zhAt ?? 2.3) + 0.5, t) });
  });
};

// ---------- 跟读环节 ----------
// 老师问（quiz: 词）→ 留空拍给孩子答（rest + wait）→ Bobo 给标准答案（answer: 词，Yes 开头绿色对勾，否则红叉；
// 答案不是 Yes/No 的句型（Where is…? → It's in the box!）传 o.good(answerLine) → true 显示对勾）。
// o.pic(c, t, key)：左边的大图卡；o.react(answerLine|undefined) → 右下角陪答角色的 K.ch 参数（或 null 不画）
K.quiz = (c, t, sc, o = {}) => {
  const ls = K.linesOf(sc.id), intro = ls.find(l => !l.quiz && !l.answer);
  const qs = ls.filter(l => l.quiz), as = ls.filter(l => l.answer);
  K.layer(c, 'bg', g => K.dots(g));
  const firstQ = qs.length ? qs[0].t0 - 0.35 : sc.t1;
  if (intro && t < firstQ + 0.2) {                                                  // 轮到你啦
    const out = 1 - ss(firstQ - 0.2, firstQ + 0.1, t);
    K.banner(c, intro.text, intro.zh, 330, K.popIn(t, intro.t0 - 0.1, 0.35) * out, K.COL.teacher, 120);
    if (o.host !== false) K.ch(c, o.host || 'bobo', 960, K.GY + 60 + (1 - K.popIn(t, sc.t0 + 0.2, 0.45)) * 500 + (1 - out) * 500, t,
      { pose: K.has('bobo_wave') ? 'bobo_wave' : undefined, s: 1.0, rot: Math.sin(t * 9) * 0.03 });
  }
  qs.forEach((q, i) => {
    const a = as[i], t0 = q.t0 - 0.35, t1 = i + 1 < qs.length ? qs[i + 1].t0 - 0.35 : sc.t1 - 0.2;
    if (t < t0 - 0.1 || t > t1 + 0.4) return;
    const pin = U.ease.out(clamp((t - t0) / 0.4)), pout = U.ease.in(clamp((t - t1 + 0.35) / 0.4));
    const key = q.quiz, V = K.VOC[key] || { col: K.COL.teacher };
    if (o.pic) { c.save(); c.translate(-(1 - pin) * 1000 - pout * 1100, 0); o.pic(c, t, key); c.restore(); }
    c.save(); c.translate((1 - pin) * 1200 + pout * 1300, 0);
    K.layer(c, 'ui', g => {
      const sp = q.text.lastIndexOf(' ');                                             // 问句拆两行，单词单独一行、用单词的颜色
      const parts = o.split ? o.split(q) : [q.text.slice(0, sp), q.text.slice(sp + 1)];   // o.split(q) → [第一行, 第二行]：最后一个词单独一行不合适的问句（What color is it?）自己拆
      K.txt(g, parts[0], 1370, 200, 104, K.EN, K.INK);
      const w2 = parts[1], s2 = K.fitSize(g, w2, K.EN, 860, 132);
      K.txt(g, w2, 1370, 318, s2, K.EN, V.col, { stroke: TH.pal.textStroke, sw: s2 * 0.12 });
      K.txt(g, q.zh, 1370, 425, 50, K.ZH2, K.SUB);
      const w = a && K.WAITS.find(w => w.t0 >= q.t1 - 0.01 && w.t1 <= a.t0 + 0.01);
      if (w && t >= w.t0 - 0.1 && t < a.t0) {                                       // 留给孩子回答的空拍
        const p = K.popIn(t, w.t0 - 0.1, 0.3);
        K.txt(g, '?', 1370, 590 + 10 * Math.sin(t * 8), 160 * p, K.EN, K.COL.teacher, { stroke: TH.pal.textStroke, sw: 24 });
        K.txt(g, '轮到你说！', 1370, 720, 54, K.ZH, K.COL.teacher, { alpha: p });
        const nb = Math.round((w.t1 - w.t0) / K.BEAT);
        for (let k = 0; k < nb; k++) { const on = t >= w.t0 + k * K.BEAT; g.fillStyle = on ? K.COL.teacher : 'rgba(122,76,255,0.2)'; g.beginPath(); g.arc(1370 + (k - (nb - 1) / 2) * 56, 805, on ? 18 : 14, 0, 7); g.fill(); }
      }
      if (a && t >= a.t0 - 0.12) {
        const p = K.popIn(t, a.t0 - 0.12, 0.35, 2.6), yes = o.good ? o.good(a) : /^yes/i.test(a.text);
        const acol = yes ? TH.pal.yes : TH.pal.no, as = K.fitSize(g, a.text, K.EN, 700, 112);   // 长答案缩字号，不超出右半屏
        g.save(); g.translate(1370, 600); g.scale(p, p); g.rotate(yes ? -0.02 : 0.02);
        const bw = K.tw(g, a.text, as, K.EN) + 240;
        g.fillStyle = acol; g.beginPath(); g.roundRect(-bw / 2, -100, bw, 200, 100); g.fill();
        g.fillStyle = '#fff'; g.beginPath(); g.arc(-bw / 2 + 100, 0, 62, 0, 7); g.fill();
        g.strokeStyle = acol; g.lineWidth = 20; g.lineCap = 'round'; g.lineJoin = 'round'; g.beginPath();
        if (yes) { g.moveTo(-bw / 2 + 72, 2); g.lineTo(-bw / 2 + 94, 26); g.lineTo(-bw / 2 + 132, -24); }
        else { g.moveTo(-bw / 2 + 76, -24); g.lineTo(-bw / 2 + 124, 24); g.moveTo(-bw / 2 + 124, -24); g.lineTo(-bw / 2 + 76, 24); }
        g.stroke();
        K.txt(g, a.text, 60, 4, as, K.EN, '#fff');
        g.restore();
        K.txt(g, a.zh, 1370, 760, 56, K.ZH, acol, { alpha: p });
      }
    });
    c.restore();
  });
  if (o.react && t >= firstQ) {                                                    // 右下角陪着回答的角色
    const a = as.find(a => t >= a.t0 - 0.1 && t < a.t1 + 0.5);
    const r = o.react(a);
    if (r) K.ch(c, r.who || 'bobo', 1730, H - 20 + (1 - K.popIn(t, firstQ, 0.4)) * 400, t, { s: 0.62, shadow: false, ...r });
  }
};

// ---------- 整片：找场景、转场、收尾 ----------
// SC: {场景 id: (c, t, sc) => …}。转场：彩色圆盖住旧画面，再从中间开一个洞露出新画面（颜色 cfg.wipe[下一场景]）
K.frame = (c, t, SC) => {
  K.MAIN = c;
  const step = TH.step || 1;                                                       // 剪纸、黏土、蜡笔"一拍二"：每两帧换一次画面，像定格动画
  if (step > 1) t = Math.floor(t * FPS / step + 1e-6) * step / FPS;
  T_NOW = t;
  const SCN = K.SCN;
  let i = SCN.findIndex(s => t < s.t1); if (i < 0) i = SCN.length - 1;
  const sc = SCN[i], next = SCN[i + 1], R = Math.hypot(960, 540) + 40;
  c.fillStyle = TH.paper; c.fillRect(0, 0, W, H);
  const run = s => { if (!SC[s.id]) throw new Error(`场景 ${s.id} 没有画法（SC.${s.id}）`); SC[s.id](c, t, s); };
  if (next && t > next.t0 - 0.32) {
    run(sc);
    const p = U.ease.in(clamp((t - (next.t0 - 0.32)) / 0.32));
    K.layer(c, 'ui', g => { g.fillStyle = K.WIPE[next.id] || K.INK; g.beginPath(); g.arc(960, 540, R * p, 0, 7); g.fill(); });
  } else {
    run(sc);
    if (i > 0 && t < sc.t0 + 0.4) {
      const p = U.ease.out(clamp((t - sc.t0) / 0.4));
      K.layer(c, 'ui', g => { g.fillStyle = K.WIPE[sc.id] || K.INK; g.beginPath(); g.rect(-40, -40, W + 80, H + 80); g.moveTo(960 + R * p, 540); g.arc(960, 540, R * p, 0, 7, true); g.fill('evenodd'); });
    }
  }
  K.finish(c);
};

return K;
})();
