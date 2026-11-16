(async () => {
  const T = [], ok = (name, cond, info) => T.push({ name, ok: !!cond, info: String(info ?? '') });
  ok('wait_text', JSON.stringify(K.WAIT_TEXT) === JSON.stringify({ say: '轮到你说！', do: '站起来，一起做！', point: '用手指一指！', guess: '猜猜是什么？', pick: '选一个！', freeze: '定住！不许动！' }), JSON.stringify(K.WAIT_TEXT));
  ok('wait_at_inside', K.waitAt && K.waitAt(13.5)?.kind === 'do');
  ok('wait_at_outside', K.waitAt && K.waitAt(2.0) === null);
  const c = new OffscreenCanvas(10, 10).getContext('2d'); let e;
  K.withCam(c, { z: 1.5, x: 3000, y: 540, ww: 3840 }, () => { e = c.getTransform().e; });
  ok('withcam_ww', Math.abs(e - (960 - 1.5 * 3000)) < 1e-6, e);
  K.withCam(c, { z: 1.5, x: 3000, y: 540 }, () => { e = c.getTransform().e; });
  ok('withcam_default_clamp', Math.abs(e - (960 - 1.5 * 1280)) < 1e-6, e);
  // K.ch 的 move：位移、旋转、缩放叠加（画到离屏画布上，看 K.spr 收到的变换）
  const cv = new OffscreenCanvas(1920, 1080), g = cv.getContext('2d');
  const a = K.ch(g, 'bobo', 600, 935, 0.3, { still: true, shadow: false });
  const b = K.ch(g, 'bobo', 600, 935, 0.3, { still: true, shadow: false, move: { dx: 50, dy: -100, rot: 0, sx: 1, sy: 2 } });
  ok('ch_move_dy_sy', Math.abs((b.top) - (a.top - 100 - (935 - a.top))) < 1e-6, `${a.top} ${b.top}`);
  ok('ch_no_move_same', K.ch(g, 'bobo', 600, 935, 0.3, { still: true, shadow: false }).top === a.top);
  ok('wait_prompt_fn', typeof K.waitPrompt === 'function');
  // 单词卡后面没有领念（跟我做的口令卡）：卡片照常在 (960, 215) 弹出，不能出现 NaN 变换
  const saved = K.LINES, sc = K.SCN.find(s => s.id === 'empty'), tr = [];
  K.LINES = [...saved, { who: ['teacher'], text: 'Jump!', t0: 15.0, t1: 15.6, scene: 'empty', card: { en: 'jump', zh: '跳' } }];
  const g2 = new OffscreenCanvas(1920, 1080).getContext('2d'), t0 = g2.translate.bind(g2);
  g2.translate = (x, y) => { tr.push(x, y); t0(x, y); };
  const tr2 = [];
  try { K.wordCard(g2, 15.8, sc); g2.translate = (x, y) => { tr2.push(x, y); t0(x, y); }; K.wordCard(g2, 16.6, sc); } finally { K.LINES = saved; }
  ok('wordcard_without_chant', tr.length >= 2 && tr.every(Number.isFinite) && tr[0] === 960 && tr[1] === 215, tr.slice(0, 4).join());
  ok('wordcard_without_chant_corner', tr2.length >= 2 && tr2[0] < 400 && tr2[1] === 100, tr2.slice(0, 2).join());   // 念完 0.3 秒后缩到左上角
  return T;
})()
