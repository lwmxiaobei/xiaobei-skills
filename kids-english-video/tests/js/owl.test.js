// 猫头鹰老师（kids_stage.js 的 K.owlAt / K.owl）和缺帧报错。FIX：老师 4.8–5.6 念单词卡，6.0 起领念
(async () => {
  const T = [], ok = (name, cond, info) => { let v; try { v = typeof cond === 'function' ? cond() : cond; } catch (e) { v = false; info = e.message; } T.push({ name, ok: !!v, info: String(info ?? '') }); };
  const at = t => { try { return K.owlAt(t); } catch (e) { return { err: e.message }; } };
  ok('owl_on_teacher_line', () => { const o = at(5.3); return o && o.p > 0.95 && /^owl_m[012]$/.test(o.pose); }, JSON.stringify(at(5.3)));
  ok('owl_hidden_otherwise', () => at(2.0) === null && at(9.0) === null && at(16) === null, JSON.stringify([at(2.0), at(9.0), at(16)]));
  ok('owl_rises_before_line', () => (o => o && o.p < 0.95)(at(4.6)), JSON.stringify(at(4.6)));
  const saved = K.MOUTH.teacher, f = Math.round(5.3 * K.FPS);
  K.MOUTH.teacher = saved.slice(0, f) + '2' + saved.slice(f + 1);
  ok('owl_mouth_follows_teacher', () => at(5.3).pose === 'owl_m2', JSON.stringify(at(5.3)));
  K.MOUTH.teacher = saved;
  // 不挡单词卡（中心 y 215、高 300）、领念行（y 235 上下）、等孩子的提示（到 y≈515）：猫头鹰整个在右下角
  ok('owl_with_card', () => { const b = at(5.3).box; return b.y0 >= 560 && b.x0 >= 1480 && b.x1 <= 1920 + 1 && b.y1 >= 1080; }, JSON.stringify(at(5.3)));
  const L0 = K.LINES;
  K.LINES = [...L0, { who: ['teacher', 'rabbit'], text: 'Hi!', zh: '', t0: 20.0, t1: 21.0, scene: 'fast' }];
  ok('owl_on_chorus', () => (o => o && o.p > 0.95)(at(20.5)), JSON.stringify(at(20.5)));
  K.LINES = L0;
  ok('owl_draws', () => { const c = document.createElement('canvas').getContext('2d'); c.canvas.width = 1920; c.canvas.height = 1080; K.owl(c, 5.3); return true; });
  // 缺帧：报错写清缺哪张、当前画风
  const msg = fn => { try { fn(); return ''; } catch (e) { return e.message; } };
  ok('missing_frame_message', () => (m => m.includes('zebra_m0') && m.includes('flat') && m.includes('characters/flat'))(msg(() => K.img('zebra_m0'))), msg(() => K.img('zebra_m0')));
  return T;
})()
