"""用 numpy 合成全部卡通音效，输出到 sfx/*.wav（48kHz 立体声，峰值 -6 dBFS）。没有外部素材，没有版权问题。
用法：.venv/bin/python sfx.py
"""
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 48000
OUT = Path(__file__).parent / "sfx"
rng = np.random.default_rng(3)


def t_(d):
    return np.arange(int(SR * d)) / SR


def noise(d):
    return rng.standard_normal(int(SR * d))


def band(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)


def low(x, f):
    return sosfilt(butter(2, f, btype="low", fs=SR, output="sos"), x)


def tone(freq, d, wave="sine"):
    """freq 可以是数组（随时间变化的频率）。"""
    t = t_(d)
    f = np.broadcast_to(freq, t.shape)
    ph = 2 * np.pi * np.cumsum(f) / SR
    if wave == "tri":
        return 2 / np.pi * np.arcsin(np.sin(ph))
    return np.sin(ph)


def env(d, a=0.005, r=None):
    t = t_(d)
    e = np.minimum(1, t / a)
    return e * (np.exp(-t / r) if r else np.minimum(1, (d - t) / 0.02).clip(0))


def mix(*parts):
    n = max(len(p[1]) + int(SR * p[0]) for p in parts)
    y = np.zeros(n)
    for at, x in parts:
        i = int(SR * at)
        y[i:i + len(x)] += x
    return y


def boing():
    d = 0.5
    t = t_(d)
    f = 180 + 420 * (1 - np.exp(-t / 0.06)) + 40 * np.sin(2 * np.pi * 18 * t) * np.exp(-t / 0.2)
    return tone(f, d) * env(d, 0.004, 0.16)


def splash():
    d = 0.6
    x = band(noise(d), 600, 5000) * env(d, 0.01, 0.12)
    drops = [tone(np.linspace(900, 1700, int(SR * 0.06)) + 0, 0.06) * env(0.06, 0.002, 0.02) * 0.5 for _ in range(4)]
    return mix((0, x), *[(0.08 + i * 0.07 + rng.uniform(0, 0.03), dr) for i, dr in enumerate(drops)])


def flutter():
    d = 0.45
    x = band(noise(d), 300, 2500)
    am = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 22 * t_(d)))
    return x * am * env(d, 0.01, 0.15) * 0.8


def flap():
    d = 0.12
    return band(noise(d), 200, 1500) * env(d, 0.004, 0.03)


def whoosh():
    d = 0.55
    t = t_(d)
    x = noise(d)
    out = np.zeros_like(x)
    for i, f in enumerate(np.linspace(400, 3000, 12)):
        w = np.exp(-((t / d - i / 11) ** 2) / 0.02)
        out += band(x, f * 0.7, f * 1.3) * w
    return out * np.sin(np.pi * t / d) ** 1.5


def sparkle():
    notes = [1568, 2093, 2637, 3136]
    parts = [(i * 0.055, (tone(f, 0.5) + 0.3 * tone(f * 2.01, 0.5)) * env(0.5, 0.002, 0.18) * 0.5) for i, f in enumerate(notes)]
    return mix(*parts)


def twinkle():
    notes = [2637, 2093, 2637, 3136, 2637]
    return mix(*[(i * 0.09, tone(f, 0.3) * env(0.3, 0.002, 0.08) * 0.4) for i, f in enumerate(notes)])


def ding():
    a = (tone(1047, 0.8) + 0.4 * tone(2094, 0.8)) * env(0.8, 0.002, 0.3)
    b = (tone(1568, 0.9) + 0.4 * tone(3136, 0.9)) * env(0.9, 0.002, 0.35)
    return mix((0, a * 0.6), (0.12, b * 0.6))


def nope():
    d = 0.22
    a = tone(392, d, "tri") * env(d, 0.004, 0.08)
    b = tone(330, 0.32, "tri") * env(0.32, 0.004, 0.12)
    return mix((0, a), (0.18, b)) * 0.8


def pop():
    d = 0.12
    t = t_(d)
    return tone(500 + 900 * np.exp(-t / 0.015), d) * env(d, 0.001, 0.025)


def tick():
    d = 0.06
    return tone(1800, d) * env(d, 0.001, 0.012) * 0.6


def step():
    d = 0.12
    t = t_(d)
    return (tone(120 + 80 * np.exp(-t / 0.02), d) + 0.3 * low(noise(d), 800)) * env(d, 0.002, 0.03)


def slide(f0, f1, d):
    t = t_(d)
    f = f0 * (f1 / f0) ** (t / d) * (1 + 0.012 * np.sin(2 * np.pi * 6 * t))
    return (tone(f, d) + 0.15 * tone(f * 2, d)) * env(d, 0.03, None) * 0.7


def thud():
    d = 0.4
    t = t_(d)
    body = tone(70 + 90 * np.exp(-t / 0.03), d) * env(d, 0.002, 0.12)
    return body + 0.4 * low(noise(d), 600) * env(d, 0.001, 0.04)


def giggle():
    parts = []
    for i in range(6):
        f0 = 700 - i * 25
        d = 0.09
        t = t_(d)
        parts.append((i * 0.12, tone(f0 * (1 + 0.15 * np.sin(np.pi * t / d)), d, "tri") * env(d, 0.005, 0.04) * 0.6))
    return mix(*parts)


def crunch(lo=900, hi=6000, n=4, gap=0.045):
    """咬脆东西：几粒很短的带通噪声，一粒比一粒弱。"""
    parts = []
    for i in range(n):
        d = 0.05 + rng.uniform(0, 0.02)
        g = band(noise(d), lo * rng.uniform(0.85, 1.15), hi) * env(d, 0.001, 0.012) * (0.85 ** i)
        parts.append((i * gap + rng.uniform(0, 0.012), g))
    body = tone(260 + 300 * np.exp(-t_(0.08) / 0.01), 0.08) * env(0.08, 0.001, 0.02) * 0.35
    return mix((0, body), *parts)


def munch():
    """软软地嚼：两下低沉的闷噪声。"""
    parts = []
    for i in range(2):
        d = 0.14
        x = band(noise(d), 180, 1400) * np.sin(np.pi * t_(d) / d) ** 2
        parts.append((i * 0.17, x))
    return mix(*parts)


def yuck():
    """嫌弃：往下滑的颤音。"""
    d = 0.6
    t = t_(d)
    f = 520 * (190 / 520) ** (t / d) * (1 + 0.06 * np.sin(2 * np.pi * 11 * t))
    return (tone(f, d, "tri") + 0.2 * tone(f * 2, d)) * env(d, 0.01, None) * 0.75


def gulp():
    d = 0.16
    t = t_(d)
    return tone(160 + 380 * (t / d) ** 2, d) * env(d, 0.004, 0.05)


SOUNDS = {
    "boing": boing, "splash": splash, "flutter": flutter, "flap": flap, "whoosh": whoosh, "sparkle": sparkle,
    "twinkle": twinkle, "ding": ding, "nope": nope, "pop": pop, "tick": tick, "step": step, "thud": thud,
    "giggle": giggle, "slide_up": lambda: slide(300, 1100, 2.6), "slide_down": lambda: slide(1200, 220, 0.45),
    "crunch": crunch, "crisp": lambda: crunch(1800, 9000, 3, 0.035), "munch": munch, "yuck": yuck, "gulp": gulp,
    "wow": lambda: slide(420, 1250, 0.5),
}


def main():
    OUT.mkdir(exist_ok=True)
    for name, fn in SOUNDS.items():
        y = fn()
        y = y / (np.abs(y).max() + 1e-9) * 0.5
        wavfile.write(OUT / f"{name}.wav", SR, np.stack([y, y], 1).astype(np.float32))
    print("音效", len(SOUNDS), "个 ->", OUT)


if __name__ == "__main__":
    main()
