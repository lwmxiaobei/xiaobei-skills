"""7 种玩法在 flat、crayon 下都能渲染（不报错、不是空白），抽帧存到 WORK/抽帧/（见 harness.py）供人工看。"""
from pathlib import Path

import pytest
from PIL import Image, ImageStat

from harness import SK, WORK, line, make_clip_project, render_stills


def _data():
    L, A, W = [], [], []
    S = [("qa", 0, 6), ("guess", 6, 12), ("doit", 12, 18), ("find", 18, 24), ("pick", 24, 30), ("count", 30, 36), ("missing", 36, 42), ("freeze", 42, 49.2)]
    L += [line("bobo", "Do you like apples?", 0.6, 1.8, "qa"), line("rabbit", "Yes, I do!", 2.4, 3.4, "qa"),
          line("teacher", "Apples!", 3.6, 4.2, "qa", card={"en": "apples", "zh": "苹果"}), line("rabbit", "Apples!", 4.8, 5.3, "qa", chant=0, n=1)]
    W += [{"t0": 6.6, "t1": 8.4, "kind": "guess", "scene": "guess"}]
    A += [{"act": "reveal", "t0": 8.4, "t1": 9.6, "scene": "guess"}]
    L += [line("rabbit", "Bananas!", 9.6, 10.6, "guess")]
    L += [line("teacher", "Jump!", 12.6, 13.2, "doit", card={"en": "jump", "zh": "跳"})]
    W += [{"t0": 13.8, "t1": 16.2, "kind": "do", "scene": "doit"}]
    L += [line("bobo", "Where is the carrot?", 18.6, 19.8, "find")]
    W += [{"t0": 20.4, "t1": 22.2, "kind": "point", "scene": "find"}]
    A += [{"act": "found", "t0": 22.2, "t1": 23.4, "scene": "find"}]
    L += [line("teacher", "Apple or banana?", 24.6, 25.8, "pick")]
    W += [{"t0": 26.4, "t1": 28.2, "kind": "pick", "scene": "pick"}]
    A += [{"act": "pick", "t0": 28.2, "t1": 29.4, "scene": "pick"}]
    L += [line(["teacher", "bobo"], w, t, t + 0.5, "count") for w, t in (("One!", 30.6), ("Two!", 31.8), ("Three!", 33.0))]
    L += [line("teacher", "Close your eyes!", 36.6, 37.6, "missing")]
    A += [{"act": "dark", "t0": 37.8, "t1": 39.0, "scene": "missing"}]
    W += [{"t0": 39.0, "t1": 40.8, "kind": "guess", "scene": "missing"}]
    A += [{"act": "reveal", "t0": 40.8, "t1": 42.0, "scene": "missing"}]
    A += [{"act": "dance", "t0": 42.0, "t1": 45.6, "scene": "freeze"}]
    L += [line("teacher", "Freeze!", 45.6, 46.1, "freeze")]
    W += [{"t0": 46.2, "t1": 48.6, "kind": "freeze", "scene": "freeze"}]
    return {"scenes": [{"id": i, "animal": None, "t0": a, "t1": b} for i, a, b in S], "lines": L, "acts": A, "waits": W}


ROUNDS_DATA = _data()
ROUND_TIMES = [1.2, 3.0, 5.0, 7.5, 8.8, 10.0, 12.9, 14.5, 15.6, 19.2, 21.0, 22.9, 25.2, 27.0, 28.9,
               31.0, 32.2, 33.5, 37.0, 38.5, 41.0, 44.0, 47.0, 48.4]


@pytest.mark.parametrize("style", ["flat", "crayon"])
def test_rounds_render(style, tmp_path):
    proj = make_clip_project(tmp_path, ROUNDS_DATA, style, clip_js=(SK / "tests/fixtures/rounds.js").read_text(), grammar="rounds")
    shots = render_stills(proj, ROUND_TIMES, WORK / "抽帧" / f"玩法_{style}")
    assert all(ImageStat.Stat(Image.open(p).convert("L")).stddev[0] > 10 for p in shots)
