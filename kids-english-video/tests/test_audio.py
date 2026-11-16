"""伴奏按 stops 静音；6 个新音效。"""
import sys

import numpy as np
import pytest

from harness import TPL

sys.path.insert(0, str(TPL))
import bgm  # noqa: E402
import sfx  # noqa: E402

SR = 48000


def test_mute_inside_and_fades():
    y = bgm.mute_spans(np.ones((SR * 3, 2), np.float32), [[1.0, 2.0]], SR, 0.06)
    assert np.all(y[int(1.2 * SR):int(1.8 * SR)] == 0)
    assert y[int(0.5 * SR), 0] == 1 and y[int(2.5 * SR), 0] == 1
    assert abs(y[int(0.97 * SR), 0] - 0.5) < 0.05 and abs(y[int(2.03 * SR), 0] - 0.5) < 0.05


def test_mute_past_end():
    y = bgm.mute_spans(np.ones((SR * 3, 2), np.float32), [[2.5, 9.0]], SR)
    assert y[int(2.8 * SR), 0] == 0 and y[int(2.0 * SR), 0] == 1


def test_mute_does_not_touch_input():
    x = np.ones((SR, 2), np.float32)
    bgm.mute_spans(x, [[0.2, 0.4]], SR)
    assert np.all(x == 1)


DUR = {"drumroll": (1.4, 2.0), "tada": (0.6, 1.2), "clap": (0.05, 0.3), "freeze": (0.3, 0.8), "magnify": (0.4, 0.9), "poof": (0.2, 0.6), "choo": (0.8, 1.6), "pageflip": (0.2, 0.6)}


@pytest.mark.parametrize("name", DUR)
def test_new_sfx(name):
    y = sfx.SOUNDS[name]()
    lo, hi = DUR[name]
    assert np.all(np.isfinite(y)) and np.abs(y).max() > 0.01 and lo <= len(y) / sfx.SR <= hi
