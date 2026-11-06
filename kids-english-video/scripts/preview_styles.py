#!/usr/bin/env python3
"""渲几张画风预览图（不用配音，假时间轴），挑画风、改画风参数后检查用。

用法：
  python3 preview_styles.py --out <目录> [--styles flat,crayon,paper,clay,watercolor] [--times 1.2,2.9,3.9,6.2] [--sheet]
  --sheet 另外把所有图拼成一张总览 <目录>/总览.jpg（每行一个画风）
  --video 2 另外渲一段 2 秒的视频测渲染速度
需要 uv（跑 playwright）。画面代码用 skill 模板里的 代码工程/（clips/preview.js + lib/kids.js），角色帧用 characters/<画风>/。
"""
import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SK = Path(__file__).resolve().parent.parent
ENG = SK / "template/代码工程"
FPS, BEAT = 30, 0.6


def spec_for(style, out):
    lines = [
        {"who": ["bobo"], "text": "Can you wave?", "zh": "你会挥手吗？", "t0": 0.6, "t1": 1.7, "scene": "demo"},
        {"who": ["rabbit"], "text": "Yes, I can!", "zh": "我会！", "t0": 2.4, "t1": 3.2, "scene": "demo"},
        {"who": ["teacher"], "text": "Wave!", "zh": "", "t0": 3.6, "t1": 4.1, "scene": "demo", "card": {"en": "wave", "zh": "挥手"}},
    ] + [{"who": ["rabbit", "bobo"], "text": "Wave!", "zh": "挥手！", "t0": 4.8 + k * 1.2, "t1": 5.3 + k * 1.2, "scene": "demo", "chant": k, "n": 3} for k in range(3)]
    n = int(8.4 * FPS) + 2
    mouth = {w: ["0"] * n for w in ("bobo", "rabbit", "fish", "bird", "teacher")}
    for l in lines:
        for w in l["who"]:
            for f in range(int(l["t0"] * FPS), int(l["t1"] * FPS)):
                mouth[w][f] = "12"[f % 2]
    ch = SK / "characters" / style
    spec = {"grammar": "preview", "duration": 8.4, "fps": FPS, "width": 1920, "height": 1080,
            "cues": [{"kind": "asset", "at": 0, "image": str(p)} for p in sorted(ch.glob("*.png"))],
            "data": {"bpm": 100, "beat": BEAT, "scenes": [{"id": "demo", "t0": 0, "t1": 8.4}], "lines": lines, "acts": [], "waits": [],
                     "mouth": {k: "".join(v) for k, v in mouth.items()}, "title": "Can You Wave?", "title_zh": "你会挥手吗？", "style": style}}
    p = out / f"spec_{style}.json"
    p.write_text(json.dumps(spec, ensure_ascii=False))
    return p


def render(style, out, times, video):
    sp = spec_for(style, out)
    cmd = ["uv", "run", "-q", "--with", "playwright==1.59.0", "python", "render.py", "--spec", str(sp)]
    r = subprocess.run(cmd + ["--out", str(out / style), "--stills", times], cwd=ENG, capture_output=True, text=True)
    if r.returncode:
        return f"{style}: 失败\n{r.stdout[-1500:]}{r.stderr[-1500:]}"
    msg = f"{style}: {out / style}"
    if video:
        t0 = time.time()
        r = subprocess.run(cmd + ["--out", str(out / f"{style}.mp4"), "--to", str(video)], cwd=ENG, capture_output=True, text=True)
        dt = time.time() - t0
        msg += f"  渲染 {video}s 视频用了 {dt:.1f}s（约 {dt / (video * FPS) * 1000:.0f} ms/帧，含启动）" if not r.returncode else f"  视频失败 {r.stderr[-800:]}"
    return msg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--styles", default="flat,crayon,paper,clay,watercolor")
    ap.add_argument("--times", default="1.2,2.9,3.9,6.2")
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--video", type=float, default=0)
    a = ap.parse_args()
    out = Path(a.out).expanduser().resolve(); out.mkdir(parents=True, exist_ok=True)
    styles = a.styles.split(",")
    with ThreadPoolExecutor(len(styles)) as ex:
        for msg in ex.map(lambda s: render(s, out, a.times, a.video), styles):
            print(msg, flush=True)
    if a.sheet:
        from PIL import Image
        ts = [f"t{float(t):06.2f}.png" for t in a.times.split(",")]
        tw, th = 640, 360
        sheet = Image.new("RGB", (tw * len(ts), th * len(styles)), "white")
        for i, s in enumerate(styles):
            for j, t in enumerate(ts):
                f = out / s / t
                if f.exists():
                    sheet.paste(Image.open(f).convert("RGB").resize((tw, th), Image.LANCZOS), (j * tw, i * th))
        sheet.save(out / "总览.jpg", quality=88)
        print("总览", out / "总览.jpg")


if __name__ == "__main__":
    sys.exit(main())
