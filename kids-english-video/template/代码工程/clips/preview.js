// 画风预览：只用基础帧（4 个角色 × m0 m1 m2 wave laugh cheer），一个场景把草地、池塘、树、气泡、单词卡、跟读行、横幅都过一遍。
// scripts/preview_styles.py 生成假时间轴的 spec 来渲；也是 K 最小用法的例子。
CLIPS.preview = (() => {
const COL = { bobo: '#FF7A1A', rabbit: '#EE4F96', fish: '#2F7BFF', bird: '#E3A100', teacher: '#7A4CFF' };
const SCALE = { bobo: 0.95, rabbit: 0.95, fish: 0.9, bird: 0.78 };
const VOCAB = { wave: { zh: '挥手', col: '#2F7BFF' } };
let GY;
const SC = {};
SC.demo = (c, t, sc) => {
  const words = K.chantsOf('demo'), cheer = words.length && t >= words[0].t0 - 0.1;
  const hop = K.hopAt(t, words.map(l => l.t0), 60, 0.4);
  const pose = (who, base) => cheer ? { pose: `${who}_${hop ? 'cheer' : 'laugh'}`, lift: hop ? hop.h : 0, still: !!hop } : base;
  K.qaScene(c, t, sc, 'rabbit', (g, t) => { K.meadow(g, t); K.tree(g, 1560, 330); K.pond(g, 1180, 780, t, false); K.blanket(g, 620, 760); }, t => ({
    order: ['bobo', 'rabbit', 'bird', 'fish'],
    bobo: { x: 380, y: GY, ...pose('bobo', K.linesOf('demo').some(l => l.who[0] === 'bobo' && t >= l.t0 && t < l.t1 + 0.4) ? {} : { pose: 'bobo_wave' }) },
    rabbit: { x: 820, y: GY, phase: 0.1, ...pose('rabbit', {}) },
    bird: { x: 1520, y: 560, phase: 0.2, shadow: false, ...pose('bird', {}) },
    fish: { x: 1380, y: K.surf(1380, t, 780) + 55, shadow: false, bob: 0.6, ...pose('fish', {}) },
    front: g => { K.pond(g, 1180, 780, t, true); K.plate(g, 620, GY + 90, 100); K.sparks(g, t, 0.2, 620, GY + 20); },
  }));
  K.chorusBanner(c, t, sc, 150);
};
return {
  fonts: K.fonts,
  init(ctx) { K.init(ctx, { vocab: VOCAB, colors: COL, scale: SCALE }); GY = K.GY; },
  draw(c, t) { K.frame(c, t, SC); },
};
})();
