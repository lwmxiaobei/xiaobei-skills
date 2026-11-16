(async () => {
  const T = [], ok = (name, cond, info) => { let v; try { v = typeof cond === 'function' ? cond() : cond; } catch (e) { v = false; info = e.message; } T.push({ name, ok: !!v, info: String(info ?? '') }); };
  const g1 = K.SCN.find(s => s.id === 'g1'), r1 = K.SCN.find(s => s.id === 'r1');
  const cv = document.createElement('canvas'); cv.width = 1920; cv.height = 1080; const c = cv.getContext('2d');
  const bg = (g, t) => K.meadow(g, t);
  // 记下这一帧 K.spr 画了什么：[{n, x, y, s}]
  const spy = fn => { const out = [], o = K.spr; K.spr = (cc, n, x, y, s, op) => { out.push({ n, x, y, s }); return o(cc, n, x, y, s, op); }; try { fn(); } finally { K.spr = o; } return out; };

  // 猜猜看 become：揭晓（g1 的 reveal 26.4–27.6）弹完 0.5 秒后，物品换成能说话的角色，大小、位置和物品一样
  const im = K.img('penguin_m0'), it = { key: 'penguin_m0', x: 1100, y: 900, size: 400 }, sItem = it.size / Math.max(im.width, im.height);
  const guess = t => spy(() => K.rounds.guess(c, t, g1, { bg, focus: 'bobo', item: it, become: 'penguin', cast: () => ({ bobo: { x: 500, ...K.row(1) } }) }));
  // 物品画在 mid 里平移过的坐标系上（K.spr 收到 0, 0），角色按世界坐标画
  const isItem = r => r.n === 'penguin_m0' && r.x === 0 && r.y === 0, isChar = r => r.n.startsWith('penguin_m') && !isItem(r);
  ok('guess_become', () => { const d = guess(27.2), p = d.find(isChar);
    return p && Math.abs(p.x - it.x) < 1 && Math.abs(p.y - it.y) < 12 && Math.abs(p.s - sItem) < 1e-3 && !d.some(isItem); }, JSON.stringify(guess(27.2).filter(r => r.n.startsWith('penguin'))));
  ok('guess_become_hidden', () => [24.5, 26.0, 26.5].every(t => !guess(t).some(isChar)));
  ok('guess_become_item_before', () => guess(26.6).some(isItem));

  // 跟我做 airPose：离地时换帧，落地换回口型帧（r1 的 do 空拍 13.2–14.4，第一拍 13.2 起跳，0.34 秒落地）
  const doit = t => spy(() => K.rounds.doit(c, t, r1, { bg, focus: 'rabbit', action: 'jump', airPose: { rabbit: 'rabbit_jump' }, cast: () => K.formation('faceoff', ['bobo', 'rabbit']) }));
  ok('doit_air_pose', () => doit(13.37).some(r => r.n === 'rabbit_jump'), JSON.stringify(doit(13.37).map(r => r.n)));
  ok('doit_air_pose_land', () => { const d = doit(13.7); return !d.some(r => r.n === 'rabbit_jump') && d.some(r => r.n.startsWith('rabbit_m')); });
  ok('doit_air_pose_other', () => doit(13.37).some(r => r.n.startsWith('bobo_m')));
  // 老师念单词卡、后面跟着同一个词的领念（r1 的 Apples! 4.8–5.6）：是教单词，不是口令，不跳
  ok('doit_card_not_cmd', () => !doit(4.97).some(r => r.n === 'rabbit_jump'), JSON.stringify(doit(4.97).map(r => r.n)));
  return T;
})()
