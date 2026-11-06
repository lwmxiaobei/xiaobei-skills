"""切好的单帧（角色/切图/<前缀>_<序号>.png）→ 代码工程/assets/<名字>.png。

一张表里的帧当成一组处理：
  0. 去底色边（clean）：cut.py 只把和底色很近的像素算透明，抗锯齿的过渡像素会留下一圈粉紫（品红底）或绿（绿幕）边，
     被包住的小块底色（卷毛的洞、手臂和身体之间）也会留下。这里把"像底色"的像素都当背景，边缘几像素按底色反解透明度。
  1. 缩放：整组按同一个比例缩放，让参考帧（--ref）的高度 = 已有素材 --height-of 的高度（或 --height 像素）。
     口型帧、动作帧和以前的帧放在一起大小一致。都不给就不缩放。
  2. 对齐：同组帧按下半身（--frac：从底往上算多大比例是"下半身"）的透明通道做互相关，对齐到同一张画布，换帧时身体不跳。
  3. 居中：画布左右补边，让参考帧下半身的重心落在画布正中（画的时候锚点是底边中点）。
  --single：每帧单独处理（食物、道具这种互不相干的东西），只做 0 和 1（每帧都按自己的长边 --long 缩放，可选）。

例子：
  # 口型 + 动作表（6 帧，第 0 帧是 m0，按旧的 bobo_m0 身高缩放）
  .venv/bin/python prep_assets.py bobo_act --names bobo_m0,bobo_m1,bobo_m2,bobo_wave,bobo_laugh,bobo_cheer --frac 0.35
  # 新动作和已有帧大小一致：参考帧是第 2 帧（站着的那个），高度对齐已有的 rabbit_m0
  .venv/bin/python prep_assets.py rabbit_eat --names rabbit_eat0,rabbit_eat1,rabbit_eat2 --ref 0 --height-of rabbit_m0 --frac 0.3
  # 食物：每个单独，长边 360 像素
  .venv/bin/python prep_assets.py food --names food_carrot,food_banana,food_apple --single --long 360
名字写 - 表示这一帧不要。
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.signal import fftconvolve

ROOT = Path(__file__).parent


def clean(im, bg, band=3, tol=70):
    a = np.asarray(im.convert("RGBA")).astype(np.float64)
    P, al = a[..., :3], a[..., 3] / 255
    isbg = (al < 0.5) | (np.sqrt(((P - bg) ** 2).sum(-1)) < tol)
    core = ndi.distance_transform_edt(~isbg) > band
    if not core.any():
        return im
    _, (iy, ix) = ndi.distance_transform_edt(~core, return_indices=True)
    F = P[iy, ix]
    d = F - bg
    k = np.clip(((P - bg) * d).sum(-1) / np.maximum((d * d).sum(-1), 1), 0, 1)
    edge = ~core & ~isbg
    out = a.copy()
    out[..., :3] = np.where(edge[..., None], F, P)
    out[..., 3] = np.where(core, 255, np.where(edge, k * 255, 0))
    out = Image.fromarray(out.round().astype(np.uint8), "RGBA")
    return out.crop(out.getbbox()) if out.getbbox() else out


def lower(a, frac):
    m = (a > 128).astype(np.float32)
    m[: int(len(m) * (1 - frac))] = 0
    return m


def offset(ref, im, frac, r=60):
    """im 相对 ref 的平移，让两者下半身重合最多（只在 ±r 像素里找）。"""
    A, B = lower(np.asarray(ref)[..., 3], frac), lower(np.asarray(im)[..., 3], frac)
    cc = fftconvolve(A, B[::-1, ::-1], mode="full")
    oy, ox = B.shape[0] - 1, B.shape[1] - 1
    win = cc[max(0, oy - r):oy + r + 1, max(0, ox - r):ox + r + 1]
    dy, dx = np.unravel_index(np.argmax(win), win.shape)
    return int(dx - min(r, ox)), int(dy - min(r, oy))


def prep(frames, names, out, ref=0, height=None, frac=0.35, single=False, long=None, bg=(250, 6, 249)):
    bg = np.array(bg, float)
    ims = [clean(im, bg) for im in frames]
    pairs = [(n, im) for n, im in zip(names, ims) if n and n != "-"]
    out.mkdir(parents=True, exist_ok=True)
    if single:
        for n, im in pairs:
            if long:
                k = long / max(im.size)
                im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
            im.save(out / f"{n}.png")
        return [n for n, _ in pairs]
    k = height / ims[ref].height if height else 1.0
    ims = [im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS) for im in ims]
    offs = [offset(ims[ref], im, frac) for im in ims]
    x0 = min(dx for dx, _ in offs); y0 = min(dy for _, dy in offs)
    y1 = max(dy + im.height for (_, dy), im in zip(offs, ims))
    m = lower(np.asarray(ims[ref])[..., 3], frac)
    cx = (m.sum(0) * np.arange(m.shape[1])).sum() / max(m.sum(), 1) + offs[ref][0]
    x1 = max(dx + im.width for (dx, _), im in zip(offs, ims))
    half = max(cx - x0, x1 - cx)
    L = int(round(cx - half))
    Wc, Hc = int(round(2 * half)), int(y1 - y0)
    for n, (dx, dy), im in zip(names, offs, ims):
        if not n or n == "-":
            continue
        c = Image.new("RGBA", (Wc, Hc))
        c.alpha_composite(im, (dx - L, dy - y0))
        c.save(out / f"{n}.png")
    print(f"缩放 {k:.3f}  偏移 {offs}  画布 {(Wc, Hc)}")
    return [n for n in names if n and n != "-"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prefix", help="角色/切图/ 下的前缀（cut.py --out 用的那个）")
    ap.add_argument("--names", required=True, help="逗号分隔，按切图序号对应；- 跳过")
    ap.add_argument("--src", default=str(ROOT / "角色/切图"))
    ap.add_argument("--out", default=str(ROOT / "代码工程/assets"))
    ap.add_argument("--ref", type=int, default=0, help="参考帧序号（缩放、对齐、居中都以它为准）")
    ap.add_argument("--height-of", help="参考帧缩放到和这个已有素材一样高（代码工程/assets/<名>.png）")
    ap.add_argument("--height", type=int, help="参考帧缩放到这个高度（像素）")
    ap.add_argument("--frac", type=float, default=0.35, help="下半身占比：两脚站立的 0.25–0.35，鱼这种没有脚的用 1.0")
    ap.add_argument("--single", action="store_true", help="每帧单独处理，不对齐（食物、道具）")
    ap.add_argument("--long", type=int, help="--single 时把每帧长边缩放到这个像素")
    ap.add_argument("--bg", default="FA06F9", help="表的底色（cut.py 打印的 bg），默认品红；绿幕用 00B140")
    a = ap.parse_args()
    names = a.names.split(",")
    src = Path(a.src)
    frames = [Image.open(src / f"{a.prefix}_{i}.png") for i in range(len(names))]
    height = a.height
    if a.height_of:
        height = Image.open(Path(a.out) / f"{a.height_of}.png").height
    bg = tuple(int(a.bg[i:i + 2], 16) for i in (0, 2, 4))
    done = prep(frames, names, Path(a.out), a.ref, height, a.frac, a.single, a.long, bg)
    print("写入", ", ".join(done))


if __name__ == "__main__":
    main()
