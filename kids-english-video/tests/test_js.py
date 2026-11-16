"""tests/js/*.test.js：每个文件在 FIX 时间表的扁平风项目里跑一遍，列出不通过的断言。"""
from pathlib import Path

import pytest

from harness import FIX, make_clip_project, run_js

JS = sorted((Path(__file__).parent / "js").glob("*.test.js"))


@pytest.mark.parametrize("path", JS, ids=[p.stem for p in JS])
def test_js(path, tmp_path):
    res = run_js(make_clip_project(tmp_path, FIX), path.read_text())
    bad = [f"{r['name']}: {r['info']}" for r in res if not r["ok"]]
    assert res and not bad, "\n".join(bad)


def test_owl_off(tmp_path):
    """台本 "owl": false：猫头鹰整集不出现。"""
    res = run_js(make_clip_project(tmp_path, FIX | {"owl": False}), "(async () => [{ name: 'owl_off', ok: K.owlAt(5.3) === null, info: '' }])()")
    assert res[0]["ok"]


def test_owl_frames_missing(tmp_path):
    """画风里没有猫头鹰帧：报错说清缺 owl_m0，以及可以用 "owl": false 关掉。"""
    js = "(async () => { try { K.owlAt(5.3); return [{ name: 'owl_missing', ok: false, info: 'no error' }]; } catch (e) { return [{ name: 'owl_missing', ok: e.message.includes('owl_m0') && e.message.includes('\"owl\": false'), info: e.message }]; } })()"
    res = run_js(make_clip_project(tmp_path, FIX, drop=("owl_",)), js)
    assert res[0]["ok"], res[0]["info"]
