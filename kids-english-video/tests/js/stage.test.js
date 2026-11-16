(async () => {
  const T = [], ok = (name, cond, info) => { let v; try { v = typeof cond === 'function' ? cond() : cond; } catch (e) { v = false; info = e.message; } T.push({ name, ok: !!v, info: String(info ?? '') }); };
  const near = (a, b, e = 1e-6) => Math.abs(a - b) <= e;
  const r1 = K.SCN[0], L = { bobo: { x: 600, y: 935 }, rabbit: { x: 1340, y: 935 } };
  let S = [];
  try { S = K.shots(r1, L, 'rabbit'); } catch (e) { ok('shots_call', false, e.message); }
  ok('shots_kinds', () => S.map(s => s.kind).join() === 'wide,medium,close,wide,medium,wide', S.map(s => s.kind));
  ok('shots_t0', () => [0, 1.2, 3.0, 4.8, 6.0, 9.6].every((v, i) => near(S[i].t0, v)), S.map(s => s.t0));
  ok('shots_min_len', () => S.length && S.every(s => s.t1 - s.t0 >= 2 * K.BEAT - 1e-6));
  ok('shots_on_beat', () => S.length && S.every(s => near(s.t0 / K.BEAT, Math.round(s.t0 / K.BEAT))));
  ok('shots_ease', () => S[1].ease === 'ease' && S[2].ease === 'ease' && S[3].ease === 'cut' && S[5].ease === 'cut', S.map(s => s.ease));
  ok('cam_zcap', () => S.length && S.every(s => s.z <= 1.5));
  // 近景、中景：说话气泡（带中文高 178，中心在头顶上方 118）不出画面上边
  const L3 = { bobo: { x: 600, y: 935 }, rabbit: { x: 1340, y: 980, s: 1.3 } }, topAbs = w => K.topOf(w, L3[w].y, (K.SCALE[w] ?? 0.9) * (L3[w].s ?? 1));
  // host 和 focus 隔得太远（中景框不下两个人 + 气泡）：用全景，不用中景
  const L4 = { bobo: { x: 260, y: 935 }, rabbit: { x: 1730, y: 935 } };
  ok('shots_wide_when_apart', () => !K.shots(r1, L4, 'rabbit').some(s => s.kind === 'medium' && s.on.length > 1), K.shots(r1, L4, 'rabbit').map(s => s.kind).join());
  ok('shots_bubble_fits', () => K.shots(r1, L3, 'rabbit').filter(s => s.kind !== 'wide').every(s => s.on.every(w => 540 + (topAbs(w) - 207 - s.y) * s.z >= 24 - 1e-6)),
    K.shots(r1, L3, 'rabbit').map(s => s.kind + ':' + Math.round(s.y)).join());
  ok('cam_held_in_chant', () => JSON.stringify(K.camAt(7.5, S)) === JSON.stringify(K.camAt(9.3, S)));
  ok('shots_empty_scene', () => (s => s.length === 1 && s[0].kind === 'wide' && near(s[0].t0, 14.4) && near(s[0].t1, 18.0))(K.shots(K.SCN[1], L, 'rabbit')));
  ok('shots_fast_dialog', () => K.shots(K.SCN[2], L, 'rabbit').every(s => s.t1 - s.t0 >= 2 * K.BEAT - 1e-6));
  const L2 = { bobo: { x: 120, y: 935 }, rabbit: { x: 1800, y: 935 } };
  ok('cam_clamped_at_edge', () => near(K.camAt(3.5, K.shots(r1, L2, 'rabbit')).x, 1920 - 960 / 1.5), (() => { try { return JSON.stringify(K.camAt(3.5, K.shots(r1, L2, 'rabbit'))); } catch (e) { return e.message; } })());
  ok('calm', () => K.calm(5.0) === 1 && K.calm(7.0) === 1 && K.calm(2.0) === 0 && K.calm(13.5) === 0);
  ok('ambT_slow', () => near((K.ambT(7.1) - K.ambT(7.0)) / 0.1, 0.3, 0.02) && near((K.ambT(2.1) - K.ambT(2.0)) / 0.1, 1, 0.02));
  ok('row', () => JSON.stringify([K.row(0), K.row(2)]) === JSON.stringify([{ y: 820, s: 0.8 }, { y: 980, s: 1.05 }]));
  ok('formation', () => (f => f.bobo.x === 620 && f.rabbit.x === 1300 && f.bobo.y === 980)(K.formation('faceoff', ['bobo', 'rabbit'])) &&
     (f => f.fish.y === 820 && f.fish.x === 960)(K.formation('triangle', ['fish', 'bobo', 'rabbit'])));
  const PAN = [{ kind: 'pan', t0: 0, t1: 4, x0: 960, x1: 2880, z: 1, y: 540, ease: 'cut' }];
  ok('pan_shot', () => near(K.camAt(2, PAN, 3840).x, 1920, 1) && near(K.camAt(4, PAN, 3840).x, 2880, 1));
  ok('lean', () => K.leanFor('bobo', 1.8, r1, L, 'rabbit') > 0 && K.leanFor('rabbit', 3.5, r1, L, 'rabbit') < 0 && K.leanFor('bobo', 0.3, r1, L, 'rabbit') === 0);
  const I = m => m.dx === 0 && m.dy === 0 && m.rot === 0 && m.sx === 1 && m.sy === 1;
  ok('squash', () => (a => a.sy < 1 && a.sx > 1)(K.mv.squash(4.93, 5)) && (a => near(a.dy, -160, 1) && a.sy > 1)(K.mv.squash(5.25, 5)) && K.mv.squash(5.56, 5).sy < 1 && I(K.mv.squash(6, 5)));
  ok('spin', () => Math.abs(K.mv.spin(5.15, 5).sx) < 0.05 && I(K.mv.spin(5.6, 5)));
  ok('tilt', () => near(K.mv.tilt(5.5, 5, 6).rot, 0.12, 0.01) && I(K.mv.tilt(6.5, 5, 6)));
  ok('shake_wiggle_tiptoe', () => I(K.mv.shake(6.2, 5, 6)) && Math.abs(K.mv.shake(5.3, 5, 6).dx) + Math.abs(K.mv.shake(5.31, 5, 6).dx) > 0 &&
     I(K.mv.wiggle(9, 5, 8)) && K.mv.wiggle(5.15, 5, 8).rot !== 0 && K.mv.tiptoe(5.5, 5, 6).dy < 0 && I(K.mv.tiptoe(6.5, 5, 6)));
  ok('lean_mv', () => K.mv.lean(5.5, 5, 6, -1).rot < 0 && I(K.mv.lean(6.5, 5, 6, -1)));
  ok('doubletake', () => K.mv.doubleTake(5.05, 5).rot !== 0 && I(K.mv.doubleTake(6, 5)));
  ok('mvadd', () => (m => m.dx === 3 && m.sx === 2)(K.mvAdd({ dx: 1, dy: 0, rot: 0, sx: 2, sy: 1 }, { dx: 2, dy: 0, rot: 0, sx: 1, sy: 1 })));
  const P = { x: 600, y: 935 };
  ok('enter_run', () => 600 + K.enter('run', 4, 5, 1, P, { from: 'left' }).dx < -100 && I(K.enter('run', 6.1, 5, 1, P)));
  ok('enter_drop_pop', () => 935 + K.enter('drop', 4, 5, 1, P).dy < -100 && K.enter('pop', 4, 5, 1, P).dy >= 250);
  ok('enter_done', () => ['slide', 'peek', 'pop', 'drop'].every(k => I(K.enter(k, 6.1, 5, 1, P))));
  ok('exit', () => I(K.exit('run', 4, 5, 1, P, { from: 'right' })) && 600 + K.exit('run', 6.1, 5, 1, P, { from: 'right' }).dx > 2020);
  ok('dust_fn', () => typeof K.dust === 'function' && typeof K.topOf === 'function');
  return T;
})()
