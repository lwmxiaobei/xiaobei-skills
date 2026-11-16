"""Fish Audio 的 key 只从这几处找：环境变量 → 项目目录的 .env / .env.local → ~/.config/kids-english-video/fish.env。

断言里不直接比较 key，免得测试失败时把真 key 打出来。
"""
import sys

from harness import TPL

sys.path.insert(0, str(TPL))
import fishvoice  # noqa: E402


def _isolate(monkeypatch, tmp_path):
    for name in ("FISH_AUDIO_API_KEY", "FISH_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    proj = tmp_path / "proj"
    proj.mkdir()
    return proj


def test_key_nowhere(monkeypatch, tmp_path):
    proj = _isolate(monkeypatch, tmp_path)
    key, src = fishvoice.api_key(proj)
    found = key is not None
    assert not found, f"不该找到 key，却从 {src} 找到了"


def test_key_order(monkeypatch, tmp_path):
    proj = _isolate(monkeypatch, tmp_path)
    cfg = tmp_path / "home/.config/kids-english-video"
    cfg.mkdir(parents=True)
    got = lambda: fishvoice.api_key(proj)[0]
    (cfg / "fish.env").write_text("FISH_API_KEY=from-config\n")
    ok = got() == "from-config"
    assert ok, "~/.config/kids-english-video/fish.env 没读到"
    (proj / ".env").write_text('export FISH_AUDIO_API_KEY="from-project"  # 注释\n')
    ok = got() == "from-project"
    assert ok, "项目 .env 应该比 ~/.config 优先"
    monkeypatch.setenv("FISH_API_KEY", "from-env")
    ok = got() == "from-env"
    assert ok, "环境变量应该最优先"
