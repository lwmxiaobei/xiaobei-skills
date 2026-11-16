"""静态检查：场景和转场代码不写颜色字面量（颜色都从 K.P 取，换画风才会跟着变）。"""
import re
from pathlib import Path

LIB = Path(__file__).resolve().parent.parent / "template/代码工程/lib"


def test_no_color_literals():
    files = [LIB / "kids_scenes.js", LIB / "kids_trans.js"]
    assert files[0].exists(), "缺 lib/kids_scenes.js"
    bad = []
    for f in files:
        if not f.exists():
            continue
        for i, s in enumerate(f.read_text().splitlines(), 1):
            code = s.split("//")[0]
            if re.search(r"#[0-9A-Fa-f]{3,8}\b|rgba?\(", code):
                bad.append(f"{f.name}:{i}: {s.strip()[:80]}")
    assert not bad, "\n".join(bad)
