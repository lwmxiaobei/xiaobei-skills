"""测试工具：建临时渲染项目、在页面里跑 JS 测试、抽帧、造假配音、建示范集。

跑法（skill 根目录）：
  uv run --with pytest --with numpy --with scipy --with pillow --with msgpack --with "playwright==1.59.0" pytest tests -q

回归基线和给人看的抽帧放在 WORK：环境变量 KIDS_VIDEO_TEST_DIR，默认 ~/.cache/kids-english-video/tests（不进仓库）。
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SK = Path(__file__).resolve().parent.parent
TPL = SK / "template"
WORK = Path(os.environ.get("KIDS_VIDEO_TEST_DIR", "~/.cache/kids-english-video/tests")).expanduser()
FPS = 30
WHO = ("bobo", "rabbit", "fish", "bird", "teacher")

DEFAULT_CLIP = """CLIPS.%s = (() => {
  const SC = new Proxy({}, { get: () => (c, t) => K.layer(c, 'bg', g => K.meadow(g, t)) });
  return { fonts: K.fonts, init(ctx) { K.init(ctx, {}); }, draw(c, t) { K.frame(c, t, SC); } };
})();
"""


def line(who, text, t0, t1, scene, **kw):
    return {"who": who if isinstance(who, list) else [who], "text": text, "zh": "", "t0": t0, "t1": t1, "scene": scene, **kw}


def _fix():
    L = [line("bobo", "Do you like apples?", 1.2, 2.6, "r1"),
         line("rabbit", "Yes, I do!", 3.0, 4.1, "r1"),
         line("teacher", "Apples!", 4.8, 5.6, "r1", card={"en": "apples", "zh": "苹果"})]
    L += [line("rabbit", "Apples!", t, t + 0.5, "r1", chant=k, n=3) for k, t in enumerate((6.0, 7.2, 8.4))]
    L += [line(["rabbit", "bobo"], "Apples!", t, t + 0.5, "r1", chant=k, n=3) for k, t in enumerate((9.6, 10.8, 12.0))]
    L += [line("bobo" if i % 2 == 0 else "rabbit", "Hi!", round(18.0 + 0.6 * i, 4), round(18.5 + 0.6 * i, 4), "fast") for i in range(6)]
    return {"scenes": [{"id": "r1", "animal": "rabbit", "t0": 0.0, "t1": 14.4},
                       {"id": "empty", "animal": None, "t0": 14.4, "t1": 18.0},
                       {"id": "fast", "animal": None, "t0": 18.0, "t1": 24.0},
                       {"id": "g1", "animal": None, "t0": 24.0, "t1": 30.0}],
            "lines": L,
            "acts": [{"act": "dance", "t0": 14.4, "t1": 18.0, "scene": "empty"},
                     {"act": "reveal", "t0": 26.4, "t1": 27.6, "scene": "g1"}],
            "waits": [{"t0": 13.2, "t1": 14.4, "kind": "do", "scene": "r1"}]}


FIX = _fix()


def make_clip_project(tmp, data, style="flat", clip_js=None, grammar="fixture", drop=()):
    """复制 template/代码工程 到 tmp/代码工程，放进该画风的角色帧和扁平风的食物图，写 spec.json 和片段文件。drop：不放这些前缀的帧。"""
    dst = Path(tmp) / "代码工程"
    shutil.copytree(TPL / "代码工程", dst, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
    assets = dst / "assets"
    assets.mkdir(exist_ok=True)
    for p in list((SK / "characters" / style).glob("*.png")) + list((SK / "characters/flat").glob("food_*.png")):
        if not (assets / p.name).exists() and not p.name.startswith(tuple(drop)):
            shutil.copy(p, assets / p.name)
    (dst / "clips" / f"{grammar}.js").write_text(clip_js if clip_js is not None else DEFAULT_CLIP % grammar)
    d = {"bpm": 100, "beat": 0.6, "scenes": [], "lines": [], "acts": [], "waits": [], "stops": [],
         "title": "Test", "title_zh": "测试", "style": style} | json.loads(json.dumps(data))
    dur = d["scenes"][-1]["t1"]
    d["mouth"] = {w: "0" * (int(dur * FPS) + 2) for w in WHO}
    spec = {"grammar": grammar, "duration": dur, "fps": FPS, "width": 1920, "height": 1080,
            "cues": [{"kind": "asset", "at": 0, "image": f"assets/{p.name}"} for p in sorted(assets.glob("*.png"))],
            "data": d}
    (dst / "spec.json").write_text(json.dumps(spec, ensure_ascii=False))
    return dst


def _render(proj, *args):
    r = subprocess.run([sys.executable, "render.py", "--spec", "spec.json", *args], cwd=proj, capture_output=True, text=True)
    out = r.stdout + r.stderr
    if r.returncode != 0 or "[pageerror]" in out:
        raise AssertionError(f"render.py 失败（{r.returncode}）：\n{out[-3000:]}")
    return out


def run_js(proj, js):
    """在页面里执行一段 JS 测试（返回 [{name, ok, info}] 的异步表达式）。"""
    (Path(proj) / "_test.js").write_text(js)
    out = _render(proj, "--out", "/dev/null", "--eval", "_test.js")
    m = re.search(r"^EVAL_RESULT (.*)$", out, re.M)
    if not m:
        raise AssertionError("没有 EVAL_RESULT：\n" + out[-3000:])
    return json.loads(m.group(1))


def render_stills(proj, times, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    _render(proj, "--out", str(out), "--stills", ",".join(f"{t:g}" for t in times))
    return [out / f"t{float(t):06.2f}.png" for t in times]


def dummy_takes(project):
    """按项目 script.json 给每条台词写一段 0.5 秒的 440 Hz 假配音（路径和 tts.py 一样），不调 Fish。"""
    code = ("import json, numpy as np; from scipy.io import wavfile; import tts\n"
            "s = json.load(open('script.json'))\n"
            "t = np.arange(int(0.5 * 48000)) / 48000; y = (0.4 * np.sin(2 * np.pi * 440 * t) * np.minimum(1, (0.5 - t) * 20)).astype(np.float32)\n"
            "for w, text, k, p in tts.jobs(s):\n"
            "    p.parent.mkdir(parents=True, exist_ok=True)\n"
            "    p.exists() or wavfile.write(p, 48000, y)\n")
    subprocess.run([sys.executable, "-c", code], cwd=project, check=True)


def run_py(project, script, check=True):
    return subprocess.run([sys.executable, script], cwd=project, capture_output=True, text=True, check=check)


def make_episode(dst, style, example=True):
    """new_episode.py --example 建示范集 → 换画风 → 假配音 → 音效 → build.py。"""
    dst = Path(dst)
    args = [sys.executable, str(SK / "scripts/new_episode.py"), str(dst), "--no-venv"] + (["--example"] if example else [])
    subprocess.run(args, check=True, capture_output=True)
    sp = dst / "script.json"
    sp.write_text(re.sub(r'"style":\s*"\w+"', f'"style": "{style}"', sp.read_text(), count=1))
    dummy_takes(dst)
    run_py(dst, "sfx.py")
    r = run_py(dst, "build.py", check=False)
    if r.returncode != 0:
        raise AssertionError(r.stdout + r.stderr)
    return dst


def duration(proj):
    return json.loads((Path(proj) / "spec.json").read_text())["duration"]
