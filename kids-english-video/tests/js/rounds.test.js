(async () => {
  const T = [], ok = (name, cond, info) => { let v; try { v = typeof cond === 'function' ? cond() : cond; } catch (e) { v = false; info = e.message; } T.push({ name, ok: !!v, info: String(info ?? '') }); };
  const g1 = K.SCN.find(s => s.id === 'g1');
  ok('reveal_p', () => K.revealP(26.0, g1) === 0 && K.revealP(26.8, g1) === 1);
  ok('rounds_api', () => ['qa', 'guess', 'doit', 'find', 'pick', 'count', 'missing', 'freeze'].every(k => typeof K.rounds[k] === 'function') && typeof K.round === 'function');
  // 插入手写镜头：前后被切开，碎片不足 2 拍的并进邻居，每个镜头仍 ≥ 2 拍
  const S = [{ t0: 0, t1: 6, kind: 'wide', on: [], z: 1, x: 960, y: 540, ease: 'cut' }];
  ok('insert_shot', () => { const R = K.insertShot(S, { t0: 2.4, t1: 3.6, kind: 'close', on: ['x'], z: 1.4, x: 900, y: 600, ease: 'ease' });
    return R.map(s => s.kind).join() === 'wide,close,wide' && R[1].t0 === 2.4 && R[2].t0 === 3.6 && R[2].t1 === 6; });
  ok('insert_shot_merge', () => { const R = K.insertShot(S, { t0: 0.6, t1: 4.8, kind: 'close', on: ['x'], z: 1.4, x: 900, y: 600, ease: 'ease' });
    return R.every(s => s.t1 - s.t0 >= 2 * K.BEAT - 1e-6) && R[R.length - 1].t1 === 6; });
  return T;
})()
