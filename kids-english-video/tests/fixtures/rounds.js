// 测试片段：每种玩法一个场景（tests/test_rounds.py 用），也是 K.rounds 的最小用例
CLIPS.rounds = (() => {
const VOCAB = { apples: { img: 'food_apple', zh: '苹果', col: '#E8453C' }, bananas: { img: 'food_banana', zh: '香蕉', col: '#E3A100' },
  carrot: { img: 'food_carrot', zh: '胡萝卜', col: '#F28C28' }, broccoli: { img: 'food_broccoli', zh: '西兰花', col: '#3FA34D' } };
const COL = { bobo: '#FF7A1A', rabbit: '#EE4F96', fish: '#2F7BFF', bird: '#E3A100', teacher: '#7A4CFF' };
const SCALE = { bobo: 0.95, rabbit: 0.95, fish: 0.9, bird: 0.78 };
const meadow = (g, t, amb) => K.meadow(g, amb);
const SC = {};
SC.qa = (c, t, sc) => K.rounds.qa(c, t, sc, { focus: 'rabbit', bg: meadow, cast: () => K.formation('faceoff', ['bobo', 'rabbit']) });
SC.guess = (c, t, sc) => K.rounds.guess(c, t, sc, { focus: 'rabbit', bg: meadow, hide: 'silhouette', item: { key: 'bananas', x: 960, y: 780, size: 280 },
  cast: () => ({ bobo: { x: 420, ...K.row(2) }, rabbit: { x: 1500, ...K.row(1) } }) });
SC.doit = (c, t, sc) => K.rounds.doit(c, t, sc, { focus: 'rabbit', bg: meadow, action: 'jump', cast: () => K.formation('triangle', ['bird', 'bobo', 'rabbit']) });
SC.find = (c, t, sc) => K.rounds.find(c, t, sc, { focus: 'bobo', bg: meadow, target: 2,
  items: [{ key: 'apples', x: 560, y: 720, size: 150 }, { key: 'bananas', x: 800, y: 650, size: 140 }, { key: 'carrot', x: 1120, y: 700, size: 160 },
          { key: 'broccoli', x: 1420, y: 660, size: 140 }, { key: 'apples', x: 1280, y: 840, size: 120 }],
  cast: () => ({ bobo: { x: 260, ...K.row(2) } }) });
SC.pick = (c, t, sc) => K.rounds.pick(c, t, sc, { focus: 'rabbit', bg: meadow, left: 'apples', right: 'bananas', correct: 'left',
  cast: () => ({ bobo: { x: 260, ...K.row(1) }, rabbit: { x: 1660, ...K.row(1) } }) });
SC.count = (c, t, sc) => K.rounds.count(c, t, sc, { focus: 'bobo', bg: meadow, items: [{ key: 'apples' }, { key: 'apples' }, { key: 'apples' }],
  cast: () => ({ bobo: { x: 300, ...K.row(1) } }) });
SC.missing = (c, t, sc) => K.rounds.missing(c, t, sc, { focus: 'rabbit', bg: meadow, gone: 3,
  items: [{ key: 'apples' }, { key: 'bananas' }, { key: 'carrot' }, { key: 'broccoli' }],
  cast: () => ({ bobo: { x: 300, ...K.row(1) }, rabbit: { x: 1620, ...K.row(1) } }) });
SC.freeze = (c, t, sc) => K.rounds.freeze(c, t, sc, { focus: 'rabbit', bg: meadow, wobbler: 'bird',
  poses: { bobo: 'bobo_cheer', rabbit: 'rabbit_laugh', bird: 'bird_wave' }, cast: () => K.formation('triangle', ['bird', 'bobo', 'rabbit']) });
return {
  fonts: K.fonts,
  init(ctx) { K.init(ctx, { vocab: VOCAB, colors: COL, scale: SCALE, wipe: {} }); },
  draw(c, t) { K.frame(c, t, SC); },
};
})();
