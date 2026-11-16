"""示范集 doyoulike 在 flat、crayon 下的画面必须和改动前一致（基线在 WORK/回归基线/，见 harness.py）。

改画面库之前先生成基线：MAKE_BASELINE=1 pytest tests/test_regress.py。没有基线时这项跳过。
"""
import os
import shutil

import pytest
from PIL import Image, ImageChops

from harness import WORK, duration, make_episode, render_stills

TIMES = [2, 7.3, 10.5, 14.8, 17.5, 22, 31, 40, 52, 64, 70, 78.3, 80, 92.5, 100, 104]   # 片头、转场、问答、单词卡、领念、反转、跟读空拍和答案、片尾


@pytest.mark.parametrize("style", ["flat", "crayon"])
def test_doyoulike_unchanged(style, tmp_path):
    proj = make_episode(tmp_path / style, style) / "代码工程"
    times = [t for t in TIMES if t < duration(proj) - 0.1]
    shots = render_stills(proj, times, tmp_path / "now")
    base = WORK / "回归基线" / style
    if os.environ.get("MAKE_BASELINE"):
        base.mkdir(parents=True, exist_ok=True)
        for p in shots:
            shutil.copy(p, base / p.name)
        pytest.skip(f"基线已生成 {len(shots)} 张")
    if not base.is_dir():
        pytest.skip(f"没有基线 {base}：改画面库之前先跑 MAKE_BASELINE=1 pytest tests/test_regress.py")
    assert sorted(p.name for p in base.glob("*.png")) == sorted(p.name for p in shots)
    for p in shots:
        diff = ImageChops.difference(Image.open(p).convert("RGB"), Image.open(base / p.name).convert("RGB"))
        assert max(hi for lo, hi in diff.getextrema()) <= 2, p.name
