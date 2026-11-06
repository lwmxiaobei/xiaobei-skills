"""Fish Audio 合成（公共音色，按 reference_id 调用）。

API key 沿用 manim-explainer-video 技能的查找顺序（环境变量 → 项目 .env → fish.env → ai-video-platform 的 .env.local），不打印 key。
"""
import sys
import http.client
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path("~/.claude/skills/manim-explainer-video/scripts").expanduser()))
from fish_tts import api_key  # noqa: E402

API = "https://api.fish.audio/v1/tts"
MODEL = "s2.1-pro-free"


def synth(text, voice, out, speed=1.0, model=MODEL):
    import msgpack
    key, _ = api_key(Path(__file__).parent)
    if not key:
        raise RuntimeError("找不到 Fish Audio API key")
    payload = {
        "text": text,
        "reference_id": voice,
        "prosody": {"speed": speed, "volume": 0, "normalize_loudness": True},
        "format": "wav",
        "sample_rate": 44100,
        "latency": "normal",
        "normalize": True,
    }
    body = msgpack.packb(payload, use_bin_type=True)
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/msgpack", "model": model}
    err = ""
    for attempt in range(6):
        req = urllib.request.Request(API, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            if data:
                Path(out).parent.mkdir(parents=True, exist_ok=True)
                Path(out).write_bytes(data)
                return
            err = "返回了空音频"
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise RuntimeError("Fish Audio 鉴权失败，检查 API key") from None
            if e.code == 402:
                raise RuntimeError("Fish Audio 余额不足") from None
            err = f"HTTP {e.code} {e.read()[:200].decode(errors='ignore')}"
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.IncompleteRead) as e:
            err = f"网络错误 {type(e).__name__}"
        time.sleep(3 + attempt * 4)
    raise RuntimeError(f"Fish Audio 合成失败：{err}")
