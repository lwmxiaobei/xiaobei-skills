"""画面 build/画面.mp4 + 人声 build/voice.wav + 音效 + 伴奏 → out/成片.mp4、out/成片_无背景音乐.mp4。

伴奏风格读 script.json 的 "music"（ukulele / musicbox / march / chiptune / none，见 bgm.py），节拍读 "bpm"。
none 只出一个无伴奏的 out/成片.mp4。

音效的时间来自 build/timeline.json（build.py 生成，和画面共用同一张时间表）。
伴奏在人声出现时侧链压低，整体响度标准化到 -16 LUFS。调音量改下面几个数再重跑本脚本即可，不用重新渲染画面。
用法：.venv/bin/python assemble.py
"""
import json
import re
import subprocess
from pathlib import Path

import numpy as np
from scipy.io import wavfile

import bgm

ROOT = Path(__file__).parent
SR = 48000
BGM_DB = -13.0   # 伴奏整体音量（儿歌念白，伴奏比讲解片响一些，有节奏感）
STYLE_DB = {"musicbox": -3.0, "chiptune": -1.0}   # 各风格在 BGM_DB 上再加减：音乐盒本来就该轻，方波听着比实测响
SFX_DB = -1.0    # 音效整体音量
TL = json.loads((ROOT / "build/timeline.json").read_text())
S = json.loads((ROOT / "script.json").read_text())
MUSIC, BPM = S.get("music", "ukulele"), S.get("bpm", 100)
VIDEO = ROOT / "build/画面.mp4"
MIX = ROOT / "build/mix"


def place(track, clip, at, gain_db=0.0):
    i = int(round(SR * at))
    m = min(len(clip), len(track) - i)
    if m > 0 and i >= 0:
        track[i:i + m] += clip[:m] * 10 ** (gain_db / 20)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def loudness(path):
    log = subprocess.run(["ffmpeg", "-v", "info", "-i", str(path), "-vn", "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", log)
    return float(m[-1]) if m else float("nan")


def final(out, with_bgm):
    inputs = ["-i", str(VIDEO), "-i", str(ROOT / "build/voice.wav"), "-i", str(MIX / "sfx.wav")]
    if with_bgm:
        inputs += ["-i", str(MIX / "bgm.wav")]
        fc = (f"[1:a]asplit=2[vo][sc];[3:a]volume={BGM_DB + STYLE_DB.get(MUSIC, 0)}dB[bg];"
              "[bg][sc]sidechaincompress=threshold=0.03:ratio=4:attack=15:release=350:makeup=1[bgd];"
              "[vo][2:a][bgd]amix=inputs=3:normalize=0[m];")
    else:
        fc = "[1:a][2:a]amix=inputs=2:normalize=0[m];"
    fc += "[m]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    print(f"{out.name}  {duration(out):.2f}s  响度 {loudness(out):.1f} LUFS")


def main():
    MIX.mkdir(parents=True, exist_ok=True)
    (ROOT / "out").mkdir(exist_ok=True)
    total = duration(VIDEO)
    sfx = np.zeros((int(SR * (total + 1)), 2), np.float32)
    cache = {}
    for e in TL["sfx"]:
        if e["name"] not in cache:
            _, x = wavfile.read(ROOT / "sfx" / f"{e['name']}.wav")
            cache[e["name"]] = x.astype(np.float32)
        place(sfx, cache[e["name"]], e["at"], e["gain"] + SFX_DB)
    wavfile.write(MIX / "sfx.wav", SR, sfx)
    print(f"音效 {len(TL['sfx'])} 个，音效峰值 {20 * np.log10(np.abs(sfx).max() + 1e-9):.1f} dBFS，配乐 {MUSIC}")
    music = bgm.generate(total, MUSIC, BPM)
    if music is None:
        final(ROOT / "out/成片.mp4", False)
        return
    wavfile.write(MIX / "bgm.wav", SR, music)
    final(ROOT / "out/成片.mp4", True)
    final(ROOT / "out/成片_无背景音乐.mp4", False)


if __name__ == "__main__":
    main()
