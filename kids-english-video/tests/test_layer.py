"""K.layer 的 top 选项（场景前景用）：只处理画面底部一条，画出来和整层一样。"""
from harness import FIX, make_clip_project, run_js

JS = r"""
(async () => {
  await window.prepare(1.0); window.renderFrame(1.0);
  const T = [], ok = (name, v, info) => T.push({ name, ok: !!v, info: String(info ?? '') });
  const mk = () => { const cv = document.createElement('canvas'); cv.width = 1920; cv.height = 1080; return cv.getContext('2d'); };
  const maxDiff = (a, b) => { const A = a.getImageData(0, 0, 1920, 1080).data, B = b.getImageData(0, 0, 1920, 1080).data; let m = 0; for (let i = 0; i < A.length; i++) { const d = Math.abs(A[i] - B[i]); if (d > m) m = d; } return m; };
  for (const n of ['forest', 'bedroom', 'night']) {
    const P = K.place(n);
    for (const cam of [{ x: 960, y: 540, z: 1 }, { x: 1100, y: 640, z: 1.4 }]) {
      const a = mk(), b = mk();
      K.withCam(a, cam, () => K.layer(a, 'prop', g => P.front(g, 1, 1, cam)));
      K.withCam(b, cam, () => K.layer(b, 'prop', g => P.front(g, 1, 1, cam), { top: P.frontTop }));
      const m = maxDiff(a, b); ok(`band_same_${n}_z${cam.z}`, m <= 2, m);
    }
  }
  // 真的只处理了底部：top 以上画的东西不出现
  const c = mk(), alpha = (x, y) => { const d = c.getImageData(x, y, 20, 20).data; let s = 0; for (let i = 3; i < d.length; i += 4) s += d[i]; return s / 400; };
  K.layer(c, 'prop', g => { g.fillStyle = K.P.wood; g.fillRect(900, 100, 100, 100); g.fillRect(900, 980, 100, 60); }, { top: 900 });
  ok('band_clips_above', alpha(940, 140) === 0 && alpha(940, 1000) > 100, `${alpha(940, 140)} ${alpha(940, 1000)}`);
  return T;
})()
"""


def test_layer_band_crayon(tmp_path):
    res = run_js(make_clip_project(tmp_path, FIX, style="crayon"), JS)
    bad = [f"{r['name']}: {r['info']}" for r in res if not r["ok"]]
    assert res and not bad, "\n".join(bad)


BLOB_JS = r"""
(async () => {
  await window.prepare(1.0); window.renderFrame(1.0);
  const cv = document.createElement('canvas'); cv.width = 1920; cv.height = 1080; const c = cv.getContext('2d');
  K.layer(c, 'bg', g => K.blob(g, [[900, 500, 120], [1020, 500, 120]], K.P.leaf));
  // 左圆右缘 x=1020 落在右圆里面：逐个圆填时被右圆盖住，和右圆内部一样亮；整条路径时这里露出一圈积色
  const lum = (x0) => { const d = c.getImageData(x0, 470, 8, 60).data; let s = 0; for (let i = 0; i < d.length; i += 4) s += 0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2]; return s / (d.length / 4); };
  const ring = lum(1010), inside = lum(1060);
  return [{ name: 'blob_no_inner_ring', ok: Math.abs(ring - inside) < 6, info: `${ring.toFixed(1)} ${inside.toFixed(1)}` }];
})()
"""


def test_blob_watercolor(tmp_path):
    res = run_js(make_clip_project(tmp_path, FIX, style="watercolor"), BLOB_JS)
    bad = [f"{r['name']}: {r['info']}" for r in res if not r["ok"]]
    assert res and not bad, "\n".join(bad)
