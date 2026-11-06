"""用 numpy 合成儿歌伴奏，和台词同一个节拍（script.json 的 bpm，从 0 秒起第一拍）。全部代码生成，没有版权问题。

风格（script.json 的 "music"）：
  ukulele   尤克里里：C-F-G-C，拨弦低音 + 反拍扫弦 + 木琴分解和弦 + 轻鼓（底鼓、拍手、沙锤）。欢快，默认
  musicbox  音乐盒：C-Am-F-G，高音八音盒分解和弦 + 低音盒音 + 很轻的长音垫底，没有鼓。轻柔，适合睡前、水彩画风
  march     玩具进行曲：C-F-G-C，大号"嘭"、铜管"恰"（嘭恰嘭恰）+ 钟琴 + 军鼓、大鼓，每四小节一个滚奏。神气
  chiptune  8-bit 游戏风：C-Am-F-G，方波低音八度跳 + 窄脉冲波快速琶音 + 噪声鼓。俏皮
  none      不要配乐（assemble.py 只出无伴奏版）
都没有旋律线，免得和念白抢。
用法：
  python bgm.py 时长秒数 输出.wav [风格] [bpm]
  python bgm.py --demo 目录 [bpm]      # 每种风格各出 16 秒试听
"""
import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 48000
STYLES = ["ukulele", "musicbox", "march", "chiptune", "none"]
C_F_G_C = [(48, [60, 64, 67]), (53, [60, 65, 69]), (55, [59, 62, 67]), (48, [60, 64, 67])]
C_AM_F_G = [(48, [60, 64, 67]), (45, [57, 60, 64]), (41, [57, 60, 65]), (43, [55, 59, 62])]
ARP = [0, 1, 2, 1, 0, 1, 2, 1]
rng = np.random.default_rng(5)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def filt(x, f, kind):
    return sosfilt(butter(2, f, btype=kind, fs=SR, output="sos"), x, axis=0)


def add(dst, src, at, pan=0.0):
    i = int(SR * at)
    if i >= len(dst):
        return
    n = min(len(src), len(dst) - i)
    ang = (pan + 1) * np.pi / 4
    dst[i:i + n, 0] += src[:n] * np.cos(ang) * np.sqrt(2)
    dst[i:i + n, 1] += src[:n] * np.sin(ang) * np.sqrt(2)


def tt(dur):
    return np.arange(int(SR * dur)) / SR


def fade_in(t, a):
    return np.minimum(1, t / a)


# ---------- 乐器 ----------
def pluck(f, dur, decay=0.996):
    """Karplus-Strong 拨弦。"""
    n = int(SR * dur)
    p = max(2, int(SR / f))
    buf = rng.uniform(-1, 1, p)
    out = np.empty(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = decay * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    return out


def marimba(f, dur=0.6):
    t = tt(dur)
    return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t / 0.02)) * np.exp(-t / 0.22)


def bass(f, dur):
    t = tt(dur)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
    return s * np.minimum(1, t / 0.005) * np.exp(-t / 0.35)


def kick():
    t = tt(0.25)
    f = 50 + 90 * np.exp(-t / 0.025)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.08)


def clap():
    t = tt(0.2)
    n = filt(rng.standard_normal(len(t)), [1000, 3500], "band")
    e = sum(np.exp(-np.maximum(t - d, 0) / 0.012) * (t >= d) for d in (0, 0.01, 0.02)) * np.exp(-t / 0.08)
    return n * e


def shaker():
    t = tt(0.07)
    return filt(rng.standard_normal(len(t)), 6000, "high") * np.sin(np.pi * t / t[-1]) ** 2


def tine(f, dur=1.8):
    """八音盒的钢片：一端固定的金属条，泛音在 6.27、17.55 倍，高泛音很快消失，"叮"一声之后是干净的长音。"""
    t = tt(dur)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.9) + 0.22 * np.sin(2 * np.pi * 6.27 * f * t) * np.exp(-t / 0.08) \
        + 0.06 * np.sin(2 * np.pi * 17.55 * f * t) * np.exp(-t / 0.02)
    return s * fade_in(t, 0.002)


def pad(notes, dur):
    """很轻的长音和弦：两个略微走音的正弦叠在一起，慢起慢收。"""
    t = tt(dur)
    s = sum(np.sin(2 * np.pi * hz(m) * t) + np.sin(2 * np.pi * hz(m) * 1.004 * t + 1.3) for m in notes)
    e = np.minimum(1, t / 0.4) * np.minimum(1, (dur - t) / 0.4)
    return s * e / len(notes)


def glock(f, dur=0.9):
    t = tt(dur)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.45) + 0.3 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t / 0.12) \
        + 0.1 * np.sin(2 * np.pi * 5.4 * f * t) * np.exp(-t / 0.04)
    return s * fade_in(t, 0.001)


def horn(f, dur, bright=6, rel=0.05):
    """铜管：带限锯齿波（加法合成，泛音逐级减弱），短起音，结尾收掉。"""
    t = tt(dur)
    k = np.arange(1, int(4000 / f) + 1)
    s = (np.sin(2 * np.pi * f * np.outer(t, k)) / k * np.exp(-k / bright)).sum(1)
    return s * fade_in(t, 0.02) * np.minimum(1, (dur - t) / rel) * (0.75 + 0.25 * np.exp(-t / 0.08))


def snare(roll=False):
    t = tt(0.06 if roll else 0.16)
    n = filt(rng.standard_normal(len(t)), [1200, 7000], "band") * np.exp(-t / (0.02 if roll else 0.05))
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.03)
    return n + 0.5 * tone


def bass_drum():
    t = tt(0.4)
    f = 45 + 60 * np.exp(-t / 0.04)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18)


def pulse(f, dur, duty=0.5, gate=0.85, decay=None):
    """8-bit 方波 / 脉冲波。duty 0.5 方波（低音），0.25 / 0.125 越来越尖（琶音）。"""
    t = tt(dur)
    ph = (f * t) % 1
    s = np.where(ph < duty, 1.0, -1.0) - (2 * duty - 1)
    e = (t < dur * gate).astype(float)
    if decay:
        e *= np.exp(-t / decay)
    return s * e * fade_in(t, 0.001)


def chip_kick():
    t = tt(0.14)
    f = 55 + 160 * np.exp(-t / 0.02)
    ph = np.cumsum(f) / SR
    return (2 * np.abs(2 * (ph % 1) - 1) - 1) * np.exp(-t / 0.06)          # 三角波扫频


def chip_noise(dur, hp, decay):
    t = tt(dur)
    n = np.repeat(rng.choice([-1.0, 1.0], len(t) // 4 + 1), 4)[:len(t)]     # 降采样的白噪声，NES 噪声通道那种粗颗粒
    return filt(n, hp, "high") * np.exp(-t / decay)


# ---------- 编曲 ----------
def ukulele(nb, beat, L):
    bar = beat * 4
    gtr, lo, mar, drm = (np.zeros((L, 2)) for _ in range(4))
    K, C, Sh = kick(), clap(), shaker()
    plucks = {}
    for b in range(nb):
        root, notes = C_F_G_C[b % 4]
        t0 = b * bar
        for bt in range(4):
            add(lo, bass(hz(root - 12 + (7 if bt == 2 else 0)), beat) * 0.55, t0 + bt * beat)
            for i, m in enumerate(notes):                          # 反拍扫弦，三根弦错开一点
                if m not in plucks:
                    plucks[m] = pluck(hz(m), beat * 0.9)
                add(gtr, plucks[m] * 0.16, t0 + bt * beat + beat / 2 + i * 0.008, pan=0.25)
            add(drm, K * (0.7 if bt in (0, 2) else 0.0), t0 + bt * beat)
            if bt in (1, 3):
                add(drm, C * 0.22, t0 + bt * beat)
            for e in range(2):
                add(drm, Sh * (0.05 if e else 0.03), t0 + bt * beat + e * beat / 2, pan=-0.3)
        tones = [hz(m + 12) for m in notes]
        for i, idx in enumerate(ARP):
            if b % 2 == 1 and i % 2:
                continue
            add(mar, marimba(tones[idx]) * rng.uniform(0.7, 1.0) * 0.12, t0 + i * beat / 2, pan=-0.25)
    return filt(gtr, 4500, "low") + lo + mar + drm


def musicbox(nb, beat, L):
    bar = beat * 4
    box, lo, pd, drm = (np.zeros((L, 2)) for _ in range(4))
    Sh = shaker()
    cache = {}
    T = lambda m, d=1.8: cache.setdefault((m, d), tine(hz(m), d))
    pat = [0, 1, 2, 3, 2, 1, 2, 1]
    for b in range(nb):
        root, notes = C_AM_F_G[b % 4]
        t0 = b * bar
        up = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[0] + 24]
        for i, idx in enumerate(pat):                              # 高音八分音符分解和弦，左右轻轻摆
            add(box, T(up[idx]) * rng.uniform(0.75, 1.0) * 0.16, t0 + i * beat / 2 + rng.uniform(0, 0.01), pan=0.3 * np.sin(i))
        add(lo, T(root + 12, 3.0) * 0.28, t0)                      # 低音盒音：每小节第一、三拍
        add(lo, T(root + 19, 2.2) * 0.18, t0 + 2 * beat)
        add(pd, pad([m + 12 for m in notes], bar + 0.4) * 0.05, t0)
        for bt in range(4):                                        # 极轻的沙锤点拍子，孩子跟念时有个依靠
            add(drm, Sh * 0.025, t0 + bt * beat, pan=-0.2)
    return filt(box, 9000, "low") + lo + pd + drm


def march(nb, beat, L):
    bar = beat * 4
    tuba, brs, gl, drm = (np.zeros((L, 2)) for _ in range(4))
    S, R, BD = snare(), snare(True), bass_drum()
    cache = {}
    for b in range(nb):
        root, notes = C_F_G_C[b % 4]
        t0 = b * bar
        for bt in range(4):
            t = t0 + bt * beat
            if bt in (0, 2):                                       # 嘭：大号，根音和五度
                m = root - 12 + (7 if bt == 2 else 0)
                add(tuba, cache.setdefault(("t", m), horn(hz(m), beat * 0.75, bright=3)) * 0.5, t)
                add(drm, BD * 0.6, t)
            else:                                                  # 恰：铜管短和弦 + 军鼓
                for m in notes:
                    add(brs, cache.setdefault(("b", m), horn(hz(m), beat * 0.32, bright=5, rel=0.03)) * 0.12, t, pan=0.2)
                add(drm, S * 0.3, t, pan=-0.1)
            g = notes[[0, 1, 2, 1][bt]] + 24                         # 钟琴：每拍一个和弦音
            add(gl, cache.setdefault(("g", g), glock(hz(g))) * 0.1, t, pan=-0.3)
        if b % 4 == 3:                                             # 第四小节最后一拍：小军鼓滚奏，进下一句
            for k in range(6):
                add(drm, R * (0.12 + 0.03 * k), t0 + 3 * beat + k * beat / 6, pan=-0.1)
    return filt(tuba, 900, "low") + filt(brs, 3500, "low") + gl + drm


def chiptune(nb, beat, L):
    bar = beat * 4
    lo, arp, drm = (np.zeros((L, 2)) for _ in range(3))
    KK, SN, HH = chip_kick(), chip_noise(0.12, 1500, 0.05), chip_noise(0.04, 7000, 0.012)
    cache = {}
    for b in range(nb):
        root, notes = C_AM_F_G[b % 4]
        t0 = b * bar
        for e in range(8):                                         # 低音八度跳：根音、高八度交替
            m = root - 12 + (12 if e % 2 else 0)
            add(lo, cache.setdefault(("l", m), pulse(hz(m), beat / 2, 0.5, 0.8)) * 0.16, t0 + e * beat / 2)
        tones = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[1] + 12]
        for s in range(16):                                        # 十六分音符琶音，每小节后半换成更尖的音色
            m = tones[s % 4] + (12 if s // 4 == 3 else 0)
            duty = 0.25 if s < 8 else 0.125
            add(arp, cache.setdefault(("a", m, duty), pulse(hz(m), beat / 4, duty, 0.9, decay=0.12)) * 0.07, t0 + s * beat / 4, pan=0.15)
        for bt in range(4):
            t = t0 + bt * beat
            add(drm, (KK * 0.55) if bt in (0, 2) else (SN * 0.18), t)
            add(drm, HH * 0.08, t + beat / 2, pan=-0.2)
    return filt(lo + arp, 7000, "low") + drm


ARRANGE = {"ukulele": ukulele, "musicbox": musicbox, "march": march, "chiptune": chiptune}


def generate(total, style="ukulele", bpm=100):
    """返回 (样本数, 2) 的 float32 伴奏，均方根约 -20 dBFS；style="none" 返回 None。"""
    global rng
    if style == "none":
        return None
    if style not in ARRANGE:
        raise ValueError(f"没有这种配乐：{style}（可选 {' / '.join(STYLES)}）")
    rng = np.random.default_rng(5)
    beat = 60 / bpm
    nb = int(np.ceil(total / (beat * 4))) + 1
    L = int(SR * (nb * beat * 4 + 2))
    m = ARRANGE[style](nb, beat, L)
    m = filt(filt(m, 40, "high"), 10000, "low")[: int(SR * total)]
    fi, fo = int(SR * 0.3), int(SR * min(2.5, total / 4))
    m[:fi] *= np.linspace(0, 1, fi)[:, None]
    m[-fo:] *= np.linspace(1, 0, fo)[:, None]
    m = m / np.sqrt(np.mean(m ** 2)) * 10 ** (-20 / 20)
    pk = np.abs(m).max()
    if pk > 0.9:
        m = m / pk * 0.9
    return m.astype(np.float32)


if __name__ == "__main__":
    if sys.argv[1] == "--demo":
        out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
        bpm = float(sys.argv[3]) if len(sys.argv) > 3 else 100
        for s in STYLES[:-1]:
            wavfile.write(out / f"{s}.wav", SR, generate(16, s, bpm))
            print(out / f"{s}.wav")
    else:
        total, out = float(sys.argv[1]), sys.argv[2]
        style = sys.argv[3] if len(sys.argv) > 3 else "ukulele"
        bpm = float(sys.argv[4]) if len(sys.argv) > 4 else 100
        wavfile.write(out, SR, generate(total, style, bpm))
        print(out)
