"""把整片画面分成几段并行渲染，再无损拼成 build/画面.mp4。

非扁平画风每帧要一两百毫秒，一集两分多钟单进程要十几到二十几分钟；分 4 段并行大约快 3 倍。
用法（项目目录下）：
  .venv/bin/python render_all.py              # 默认 4 段
  .venv/bin/python render_all.py --jobs 6
  .venv/bin/python render_all.py --from 40 --to 60 --out build/片段.mp4   # 只渲一段（改了某个场景时先看效果）
需要 uv（跑 playwright）。分段日志在 build/render_<k>.log。
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
ENG = ROOT / "代码工程"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--spec", default=str(ENG / "spec.json"))
    ap.add_argument("--out", default=str(ROOT / "build/画面.mp4"))
    ap.add_argument("--from", dest="t0", type=float, default=0)
    ap.add_argument("--to", dest="t1", type=float)
    a = ap.parse_args()
    spec = json.loads(Path(a.spec).read_text())
    fps = spec.get("fps", 30)
    f0 = round(a.t0 * fps)
    f1 = round((a.t1 if a.t1 is not None else spec["duration"]) * fps)
    n = max(1, min(a.jobs, (f1 - f0) // (fps * 2)))
    cuts = [f0 + (f1 - f0) * k // n // 2 * 2 for k in range(n)] + [f1]      # 分段点取偶数帧，一拍二的画风不会在段首多算一帧
    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    segs, procs = [], []
    st = time.time()
    for k in range(n):
        seg = build / f"seg_{k}.mp4"
        log = open(build / f"render_{k}.log", "w")
        cmd = ["uv", "run", "-q", "--with", "playwright==1.59.0", "python", "render.py", "--spec", str(Path(a.spec).resolve()),
               "--from", f"{cuts[k] / fps:.6f}", "--to", f"{cuts[k + 1] / fps:.6f}", "--out", str(seg)]
        procs.append((k, subprocess.Popen(cmd, cwd=ENG, stdout=log, stderr=subprocess.STDOUT), log))
        segs.append(seg)
    print(f"{n} 段并行：{', '.join(f'{cuts[k] / fps:.1f}–{cuts[k + 1] / fps:.1f}s' for k in range(n))}", flush=True)
    bad = []
    for k, p, log in procs:
        p.wait(); log.close()
        if p.returncode:
            bad.append(k)
        print(f"  第 {k} 段{'失败' if p.returncode else '完成'}  {time.time() - st:.0f}s", flush=True)
    if bad:
        for k in bad:
            print(f"--- build/render_{k}.log 末尾 ---\n" + (build / f"render_{k}.log").read_text()[-2000:])
        sys.exit(f"第 {bad} 段渲染失败")
    lst = build / "segs.txt"
    lst.write_text("".join(f"file '{s.resolve()}'\n" for s in segs))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
    for s in segs:
        s.unlink()
    lst.unlink()
    print(f"画面 -> {out}  共 {time.time() - st:.0f}s（{(f1 - f0) / max(1, time.time() - st):.1f} 帧/秒）")


if __name__ == "__main__":
    main()
