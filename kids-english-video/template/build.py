"""script.json + 配音 take → 时间轴、人声音轨、口型、音效表、画面 spec。

所有台词都卡在节拍上开口（script.json 的 bpm，默认 100），背景音乐用同一个节拍，念出来像跟着音乐打拍子的童谣。
音效：通用的（转场 whoosh、单词卡 sparkle、跟读题 pop、空拍 tick、答案 ding/nope）自动加，"auto_sfx": false 关掉；
      其余写在 script.json 里：台词事件 "sfx": [{"name", "at": "start"|"end", "offset", "gain"}]（chant 每一遍都加），
      动作事件 "sfx": [{"name", "beat", "gain"}]（从动作开始数第几拍）。音效名是 sfx/ 下的文件名，见 sfx.py。
输出：
  build/voice.wav        人声（48kHz 立体声）
  build/timeline.json    场景、台词、动作、等待作答、音效的时间表（画面和声音共用）
  代码工程/spec.json      画面 spec（render.py 用）
用法：.venv/bin/python build.py
"""
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from scipy.io import wavfile

from tts import take_path

ROOT = Path(__file__).parent
SR, FPS = 48000, 30
S = json.loads((ROOT / "script.json").read_text())
BEAT = 60 / S.get("bpm", 100)
STYLES = ("flat", "crayon", "paper", "clay", "watercolor")
if S.get("style", "flat") not in STYLES:
    raise SystemExit(f"script.json 的 style 只能是 {STYLES}")
PAN = {"bobo": 0.0, "rabbit": -0.2, "fish": 0.2, "bird": 0.12, "teacher": 0.0} | S.get("pan", {})
GAP = 0.15          # 上一句结束到下一句开口，至少隔这么久，再顺延到下一个拍点
CHORUS_SPREAD = 0.025  # 齐声时每个声音错开的秒数，听起来像一群人在说


def next_beat(t):
    return math.ceil(t / BEAT - 1e-6) * BEAT


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def trim(x):
    """裁掉首尾静音：开口点就是 take 的 0 秒，方便卡拍。"""
    hop = SR // 100
    n = len(x) // hop
    db = 10 * np.log10(np.array([np.mean(x[i * hop:(i + 1) * hop] ** 2) for i in range(n)]) + 1e-10)
    on = np.flatnonzero(db > db.max() - 38)
    a = max(0, on[0] * hop - int(0.02 * SR))
    b = min(len(x), (on[-1] + 1) * hop + int(0.08 * SR))
    y = x[a:b].copy()
    f = int(0.006 * SR)
    y[:f] *= np.linspace(0, 1, f)
    y[-f * 4:] *= np.linspace(1, 0, f * 4)
    return y


def mouth(y):
    """每帧的张嘴程度 0/1/2（按 1/30 秒窗口的响度，相对这条 take 的最大响度）。"""
    hop = SR // FPS
    n = int(math.ceil(len(y) / hop))
    db = np.array([10 * np.log10(np.mean(y[i * hop:(i + 1) * hop] ** 2) + 1e-10) for i in range(n)])
    lv = np.clip((db - (db.max() - 30)) / 30, 0, 1)
    m = np.where(lv < 0.3, 0, np.where(lv < 0.62, 1, 2))
    m[-1:] = 0
    return m


takes_used = {}


def take(who, text):
    k = takes_used.get((who, text), 0)
    takes_used[(who, text)] = k + 1
    p = take_path(S["voices"][who], text, k)
    if not p.exists():
        raise SystemExit(f"缺配音 {p.name}（{who}: {text!r} 第 {k} 条），先跑 tts.py")
    return trim(load(p)), p


def main():
    (ROOT / "build").mkdir(exist_ok=True)
    clips, lines, acts, waits, scenes, sfx = [], [], [], [], [], []

    def fx(name, at, gain=0.0):
        if not (ROOT / "sfx" / f"{name}.wav").exists():
            raise SystemExit(f"没有音效 sfx/{name}.wav（先跑 sfx.py，或看 sfx.py 里有哪些）")
        sfx.append({"name": name, "at": round(at, 4), "gain": gain})
    t = 0.0
    for sc in S["scenes"]:
        t = next_beat(t)
        scene = {"id": sc["id"], "animal": sc.get("animal"), "t0": t}
        for ev in sc["events"]:
            if "rest" in ev:
                t0 = next_beat(t)
                t = t0 + ev["rest"] * BEAT
                if ev.get("wait"):
                    waits.append({"t0": t0, "t1": t})
                continue
            if "act" in ev:
                t0 = next_beat(t)
                t = t0 + ev["beats"] * BEAT
                acts.append({"act": ev["act"], "t0": t0, "t1": t, "scene": sc["id"]})
                for e in ev.get("sfx", []):
                    fx(e["name"], t0 + e["beat"] * BEAT, e.get("gain", 0))
                continue
            whos = ev["who"] if isinstance(ev["who"], list) else [ev["who"]]
            n = ev.get("chant", 1)
            start = next_beat(t + GAP)
            for k in range(n):
                at = start + k * ev.get("every", 1) * BEAT
                end = at
                for j, w in enumerate(whos):
                    y, p = take(w, ev["say"])
                    off = j * CHORUS_SPREAD
                    clips.append({"who": w, "at": at + off, "y": y, "gain": 1 / math.sqrt(len(whos)), "file": p.name})
                    end = max(end, at + off + len(y) / SR)
                line = {"who": whos, "text": ev["say"], "zh": ev.get("zh", ""), "t0": round(at, 4), "t1": round(end, 4),
                        "scene": sc["id"]}
                for key in ("card", "quiz", "answer"):
                    if key in ev:
                        line[key] = ev[key]
                if n > 1:
                    line["chant"] = k
                    line["n"] = n
                lines.append(line)
                for e in ev.get("sfx", []):
                    fx(e["name"], (end if e.get("at") == "end" else at) + e.get("offset", 0), e.get("gain", 0))
                t = end
        scene["t1"] = next_beat(t)
        t = scene["t1"]
        scenes.append(scene)
    total = scenes[-1]["t1"]

    # 人声音轨 + 每个角色的口型
    nS = int(SR * (total + 1))
    vo = np.zeros((nS, 2), np.float32)
    nF = int(math.ceil(total * FPS)) + 2
    mouths = {w: np.zeros(nF, np.int8) for w in S["voices"]}
    for c in clips:
        i = int(round(c["at"] * SR))
        y = c["y"] * c["gain"]
        ang = (PAN[c["who"]] + 1) * math.pi / 4
        m = min(len(y), nS - i)
        vo[i:i + m, 0] += y[:m] * math.cos(ang) * math.sqrt(2)
        vo[i:i + m, 1] += y[:m] * math.sin(ang) * math.sqrt(2)
        mo = mouth(c["y"])
        f0 = int(round(c["at"] * FPS))
        seg = mouths[c["who"]][f0:f0 + len(mo)]
        np.maximum(seg, mo[:len(seg)], out=seg)
    peak = np.abs(vo).max()
    vo *= 0.89 / peak
    wavfile.write(ROOT / "build/voice.wav", SR, vo)

    # 通用音效（画面里同样按这些时刻做动作）
    if S.get("auto_sfx", True):
        for sc in scenes[1:]:
            fx("whoosh", sc["t0"] - 0.28, -6)
        for ln in lines:
            if "card" in ln:
                fx("sparkle", ln["t0"] - 0.05, -4)
            if "answer" in ln:
                fx("ding" if ln["text"].lower().startswith("yes") else "nope", ln["t0"] - 0.1, -6)
            if "quiz" in ln:
                fx("pop", ln["t0"] - 0.08, -8)
        for w in waits:
            for b in range(int(round((w["t1"] - w["t0"]) / BEAT))):
                fx("tick", w["t0"] + b * BEAT, -10)
    sfx.sort(key=lambda e: e["at"])

    tl = {"bpm": S.get("bpm", 100), "beat": BEAT, "total": round(total, 4), "scenes": scenes, "lines": lines, "acts": acts,
          "waits": waits, "sfx": sfx}
    (ROOT / "build/timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1))

    assets = sorted(p.name for p in (ROOT / "代码工程/assets").glob("*.png"))
    spec = {"grammar": S["grammar"], "duration": round(total, 4), "fps": FPS, "width": 1920, "height": 1080,
            "cues": [{"kind": "asset", "at": 0, "image": f"assets/{a}"} for a in assets],
            "data": {k: tl[k] for k in ("bpm", "beat", "scenes", "lines", "acts", "waits")} |
                    {"mouth": {w: "".join(map(str, m.tolist())) for w, m in mouths.items()}, "title": S["title"], "title_zh": S.get("title_zh", ""),
                     "style": S.get("style", "flat")}}
    (ROOT / "代码工程/spec.json").write_text(json.dumps(spec, ensure_ascii=False))
    print(f"画风 {S.get('style', 'flat')}，配乐 {S.get('music', 'ukulele')}")
    print(f"总长 {total:.2f}s，{len(lines)} 句，{len(clips)} 条 take，音效 {len(sfx)} 个")
    for sc in scenes:
        print(f"  {sc['id']:6s} {sc['t0']:6.2f} – {sc['t1']:6.2f}  ({sc['t1'] - sc['t0']:.1f}s)")


if __name__ == "__main__":
    main()
