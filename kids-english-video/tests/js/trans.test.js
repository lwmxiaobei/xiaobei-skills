(async () => {
  const T = [], ok = (name, f, info) => { let v, e; try { v = f(); } catch (x) { e = x; } T.push({ name, ok: !e && !!v, info: e ? String(e) : String(info ?? (typeof v === 'object' ? JSON.stringify(v) : '')) }); };
  const throwsLike = (name, f, re) => { let m = ''; try { f(); } catch (e) { m = String(e.message || e); } T.push({ name, ok: re.test(m), info: m }); };
  ok('trans_none_is_circle', () => { for (let t = 0; t < 30; t += 0.1) if (K.transAt(t) !== null) return false; return true; });
  const S0 = K.SCN, A0 = K.ACTS;
  const SCN = [{ id: 'a', t0: 0, t1: 6 }, { id: 'b', t0: 6, t1: 14, trans: 'map', bg: 'beach' }, { id: 'c', t0: 14, t1: 20, trans: 'door', bg: 'snow' }];
  const ACTS = [{ act: 'travel', t0: 6, t1: 8.4, scene: 'b' }];
  const use = (scn, acts, f) => { K.SCN = scn; K.ACTS = acts; try { return f(); } finally { K.SCN = S0; K.ACTS = A0; } };
  const near = (a, b, e = 1e-6) => Math.abs(a - b) < e;
  throwsLike('trans_unknown_throws', () => use([SCN[0], { ...SCN[1], trans: 'rocket' }], ACTS, () => K.transAt(7)), /可选/);
  throwsLike('trans_needs_travel', () => use(SCN, [], () => K.transAt(7)), /travel/);
  ok('trans_phases', () => use(SCN, ACTS, () => {
    const q = t => K.transAt(t) || {};
    const a = q(5.8), b = q(7.0), c = q(8.2), d = K.transAt(9.0), e = q(13.8), f = q(14.2);
    return a.type === 'map' && a.to === 1 && a.phase === 'cover' && near(a.p, 0.5)
      && b.phase === 'hold' && near(b.p, 0.5) && c.phase === 'reveal' && near(c.p, 0.5) && d === null
      && e.type === 'door' && e.phase === 'cover' && f.phase === 'reveal' && near(f.p, 0.4);
  }));
  ok('trans_first_scene', () => use([{ ...SCN[0], trans: 'door' }, SCN[1]], ACTS, () => { const s = K.transAt(0.1); return s && s.phase === 'reveal' && s.to === 0 && K.transAt(-0.1) === null; }));
  ok('map_stations', () => use(SCN, ACTS, () => { const s = K.mapStations(); return s.length === 3 && s[0].id === 'home' && s[1].id === 'b' && s[1].place === 'beach' && s[2].place === 'snow' && s.every(p => p.x > 0 && p.x < 1920 && p.y > 0 && p.y < 1080); }));
  ok('map_bobo_beats', () => use(SCN, ACTS, () => {
    const s = K.mapStations(), d = (p, q) => Math.hypot(p.x - q.x, p.y - q.y), b = t => K.mapBobo(t);
    const ds = [6.6, 7.2, 7.8].map(t => d(b(t), s[1]));
    return d(b(6.0), s[0]) < 1 && d(b(7.8), s[1]) < 1 && d(b(8.2), s[1]) < 1 && ds[0] > ds[1] && ds[1] > ds[2] && d(b(6.9), s[0]) > 1;
  }));
  // hold 中间那帧：整屏是地图（四角和上边中间都是地图纸色）
  ok('map_covers', () => true);
  const P = K.P.map, hex = parseInt(P.slice(1), 16), want = [hex >> 16 & 255, hex >> 8 & 255, hex & 255];
  K.SCN = SCN; K.ACTS = ACTS;
  try {
    await window.prepare(7.0); window.renderFrame(7.0);
    const g = window.__canvas.getContext('2d'), bad = [];
    for (const [x, y] of [[5, 5], [1914, 5], [5, 1074], [1914, 1074], [960, 30]]) { const p = g.getImageData(x, y, 1, 1).data; if (want.some((v, i) => Math.abs(v - p[i]) > 2)) bad.push(`${x},${y}=${p.slice(0, 3)}`); }
    T[T.length - 1] = { name: 'map_covers', ok: bad.length === 0, info: bad.join(' ') };
  } catch (e) { T[T.length - 1] = { name: 'map_covers', ok: false, info: String(e) }; }
  finally { K.SCN = S0; K.ACTS = A0; }
  return T;
})()
