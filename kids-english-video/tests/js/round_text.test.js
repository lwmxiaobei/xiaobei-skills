(async () => {
  const T = [], ok = (name, cond, info) => { let v; try { v = typeof cond === 'function' ? cond() : cond; } catch (e) { v = false; info = e.message; } T.push({ name, ok: !!v, info: String(info ?? '') }); };
  const r1 = K.SCN.find(s => s.id === 'r1'), L0 = K.LINES;
  const cv = document.createElement('canvas'); cv.width = 1920; cv.height = 1080; const c = cv.getContext('2d');
  const bg = (g, t) => K.meadow(g, t), cast = () => K.formation('faceoff', ['bobo', 'rabbit']);
  const mk = (who, text, t0, t1, extra = {}) => ({ who, text, zh: '', t0, t1, scene: 'r1', ...extra });
  // 记下画出来（p > 0）的横幅文字
  const banners = fn => { const out = [], o = K.banner; K.banner = (cc, en, zh, cy, p, ...r) => { if (p > 0.001) out.push(en); return o(cc, en, zh, cy, p, ...r); }; try { fn(); } finally { K.banner = o; } return out; };

  // r1 的领念 6.0–12.5，之后加一句多人齐说（12.7–13.4）和一句老师口令（13.6–14.1）
  K.LINES = [...L0, mk(['bobo', 'rabbit'], "It's apples!", 12.7, 13.4), mk(['teacher'], 'Jump!', 13.6, 14.1), mk(['teacher', 'bobo'], 'One!', 13.6, 14.0)];
  ok('round_chorus_banner', () => banners(() => K.round(c, 13.0, r1, { bg, focus: 'rabbit', cast })).includes("It's apples!"));
  ok('round_chorus_no_teacher', () => !banners(() => K.round(c, 13.8, r1, { bg, focus: 'rabbit', cast })).includes('One!'));
  // 领念那一排：后面有别的台词时，在那句开口前收掉；没有就留到场景结束
  ok('chant_row_fades', () => K.chantAlpha(12.0, r1) > 0.99 && K.chantAlpha(12.7, r1) < 0.01);
  // 猫头鹰的对话气泡：玩法场景里老师单独说、不是单词卡/跟读题/领念的句子
  r1.round = 'qa';
  ok('owl_line_round', () => (K.owlLine(13.8) || {}).text === 'Jump!');
  ok('owl_line_card', () => K.owlLine(5.0) === null);
  // 气泡在猫头鹰左边、和它的头一样高，尾巴朝右指着它；不往上伸到右边角色的脸上
  ok('owl_bubble_beside', () => { const o = K.owlAt(13.8), got = [], ob = K.bubble;
    K.bubble = (cc, en, zh, cx, cy, tx, ty, ...r) => { got.push({ cx, cy, tx, ty }); return ob(cc, en, zh, cx, cy, tx, ty, ...r); };
    try { K.owl(c, 13.8); } finally { K.bubble = ob; }
    const b = got[0]; return b && b.cy >= o.box.y0 && b.tx > b.cx && b.ty >= o.box.y0; });
  delete r1.round;
  ok('owl_line_no_round', () => K.owlLine(13.8) === null);
  K.LINES = L0;
  // 尾巴点在气泡右边时，从右边沿伸出去（原来只会从底边伸）
  ok('bubble_side_tail', () => { const g = document.createElement('canvas'); g.width = 1920; g.height = 1080; const gc = g.getContext('2d');
    K.bubble(gc, 'Hi', '你好', 800, 500, 1100, 500, 1, '#f00'); return gc.getImageData(1000, 500, 1, 1).data[3] > 200; });
  // 跟读题答案不写 good：不是 No 开头就是绿色（It's apples! 这类句型不用每题写 good）
  const pill = text => { K.LINES = [...L0, mk(['teacher'], 'What is it?', 31, 32, { scene: 'qz', quiz: 'apples' }), mk(['bobo'], text, 33, 34, { scene: 'qz', answer: 'apples' })];
    const g = document.createElement('canvas'); g.width = 1920; g.height = 1080; const gc = g.getContext('2d');
    try { K.quiz(gc, 33.6, { id: 'qz', t0: 30, t1: 40 }); } finally { K.LINES = L0; }
    const d = gc.getImageData(1370, 688, 1, 1).data; return '#' + [0, 1, 2].map(i => d[i].toString(16).padStart(2, '0')).join('').toUpperCase(); };
  ok('quiz_answer_default_good', () => pill("It's apples!") === K.P.yes.toUpperCase() && pill("No, I don't!") === K.P.no.toUpperCase(), JSON.stringify([pill("It's apples!"), pill("No, I don't!"), K.P.yes, K.P.no]));
  ok('chant_row_stays', () => K.chantAlpha(12.7, r1) > 0.99 && K.chantAlpha(14.39, r1) < 0.01);
  return T;
})()
