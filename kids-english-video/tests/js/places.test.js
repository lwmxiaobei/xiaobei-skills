(async () => {
  const T = [], ok = (name, f, info) => { let v, e; try { v = f(); } catch (x) { e = x; } T.push({ name, ok: !e && !!v, info: e ? String(e) : String(info ?? '') }); };
  const NAMES = ['meadow', 'beach', 'snow', 'night', 'forest', 'kitchen', 'bedroom', 'playground', 'underwater'];
  const P = K.PLACES || {};
  ok('places_all', () => NAMES.every(n => {
    const p = P[n]; if (!p || !p.zh || !p.en || typeof p.bg !== 'function' || typeof p.front !== 'function') return false;
    const s = Object.values(p.spots || {});
    return s.length >= 4 && s.every(q => q.x >= 0 && q.x <= 1920 && q.y >= 300 && q.y <= 1080 && q.s > 0);
  }), NAMES.filter(n => !P[n]).join());
  let msg = '';
  try { K.place('beech'); } catch (e) { msg = String(e.message || e); }
  T.push({ name: 'place_unknown_throws', ok: /可选/.test(msg), info: msg });
  // 宽场景镜头摇到最右（看世界 960–2880）：五个点都画到了
  const blank = [];
  for (const n of NAMES) {
    if (!P[n]) { blank.push(n + ':缺'); continue; }
    const cv = new OffscreenCanvas(1920, 1080), g = cv.getContext('2d'), cam = { x: 1920, y: 540, z: 1, ww: 2880 };
    try { g.translate(-960, 0); P[n].bg(g, 1.0, 1.0, cam, 2880); P[n].front(g, 1.0, 1.0, cam, 2880); } catch (e) { blank.push(n + ':' + e); continue; }
    for (const [x, y] of [[5, 5], [1914, 5], [5, 1074], [1914, 1074], [960, 540]]) if (g.getImageData(x, y, 1, 1).data[3] < 255) blank.push(`${n}@${x},${y}`);
  }
  T.push({ name: 'place_fills_wide', ok: blank.length === 0, info: blank.join(' ') });
  // K.round：sc.bg 是字符串、不给 cfg.bg 时用场景
  const lum = d => 0.299 * d[0] + 0.587 * d[1] + 0.114 * d[2];
  const r1 = { ...K.SCN[0], bg: 'night' }, cast = () => ({ bobo: { x: 620, ...K.row(1) }, rabbit: { x: 1300, ...K.row(1) } });
  ok('round_uses_sc_bg', () => {
    const g = new OffscreenCanvas(1920, 1080).getContext('2d');
    K.round(g, 2.0, r1, { focus: 'rabbit', cast });
    const d = g.getImageData(10, 10, 1, 1).data; return lum(d) < 90 && d[2] > d[0];
  });
  ok('lively_calm', () => K.lively(7.0) === 0 && K.lively(2.0) === 1, `${K.lively && K.lively(7.0)} ${K.lively && K.lively(2.0)}`);
  // 深色场景的参与提示：字后面垫浅色底（FIX 的 r1 在 13.2–14.4 有 do 空拍，提示在 (960, 300)，字在 y 430）
  ok('prompt_on_dark', () => {
    const g = new OffscreenCanvas(1920, 1080).getContext('2d');
    K.round(g, 13.8, r1, { focus: 'rabbit', cast });
    const row = [...g.getImageData(800, 390, 100, 1).data, ...g.getImageData(1020, 390, 100, 1).data];
    let s = 0; for (let i = 0; i < row.length; i += 4) s += lum(row.slice(i, i + 3));
    return s / (row.length / 4) > 180;
  });
  // 前景只画在 frontTop 以下（K.round 按这个只处理画面底部一条，省时间）；没有前景的场景 frontTop 为 null、前景一笔不画
  const over = [];
  for (const n of NAMES) {
    const pl = P[n]; if (!pl) continue;
    for (const cam of [{ x: 960, y: 540, z: 1 }, { x: 1920, y: 540, z: 1, ww: 2880 }]) {
      const cv = new OffscreenCanvas(1920, 1080), g = cv.getContext('2d');
      g.translate(960 - cam.x, 0); pl.front(g, 1.0, 1.0, cam, cam.ww || 1920);
      if (!('frontTop' in pl) || (pl.frontTop !== null && !(pl.frontTop > 300 && pl.frontTop < 1080))) { over.push(n + ':没有 frontTop'); break; }
      const top = pl.frontTop ?? 1080;
      const d = top > 0 ? g.getImageData(0, 0, 1920, top).data : [];
      let row = -1; for (let i = 3; i < d.length; i += 4) if (d[i] > 0) { row = Math.floor((i >> 2) / 1920); break; }
      if (row >= 0) { over.push(`${n}@cam${cam.x}:第${row}行有前景`); break; }
    }
  }
  T.push({ name: 'front_within_top', ok: over.length === 0, info: over.join(' ') });
  return T;
})()
