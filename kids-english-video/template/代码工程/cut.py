#!/usr/bin/env python3
"""把一张角色表切成单个角色帧（透明 PNG），按连通区域切，行优先编号。

底色自动取图片边缘的中位色：
- 绿幕（#00B140 一类）：按绿色溢出程度算透明度，并去绿边
- 浅灰/白等平涂底（--mode flat）：从图片边缘做“相似色连通”泛洪，只去掉和边缘连通的底色，
  被粗描边围住的浅色（白衬衫、奶油色肚子、眼睛高光）不会被抠掉；被围住的大块底色洞用更严的阈值再去一次
- 白板线稿（--mode keep）：不抠，只裁，合成时用 multiply

用法：
  python cut.py 表.png --out ../素材/sprites/前缀 [--mode auto|green|flat|keep] [--gap 28] [--min 4000] [--pick 0,3,5]
输出：前缀_<序号>.png，并在同目录写一张带序号的总览图 前缀__index.png 方便核对。
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("--out", required=True)
ap.add_argument("--mode", default="auto", choices=["auto", "green", "flat", "keep"])
ap.add_argument("--gap", type=int, default=28, help="间距小于这个像素的碎块并到同一个角色里（汗滴、动作线）")
ap.add_argument("--min", type=int, default=4000, help="面积小于这个像素数的块丢掉")
ap.add_argument("--tol", type=float, default=28, help="flat 模式：和底色的颜色距离小于它算底色")
ap.add_argument("--pick", help="只输出这些序号，逗号分隔")
ap.add_argument("--pad", type=int, default=6)
a = ap.parse_args()

im = np.asarray(Image.open(a.src).convert("RGB")).astype(np.float32)
H, W, _ = im.shape
border = np.concatenate([im[0], im[-1], im[:, 0], im[:, -1]])
bg = np.median(border, axis=0)
r, g, b = im[..., 0], im[..., 1], im[..., 2]

mode = a.mode
if mode == "auto":
    mode = "green" if bg[1] - max(bg[0], bg[2]) > 60 else "flat"

rgb = im.copy()
if mode == "green":
    spill = g - np.maximum(r, b)
    alpha = 1 - np.clip((spill - 30) / 70, 0, 1)
    rgb[..., 1] = np.where(spill > 0, np.minimum(g, np.maximum(r, b) + 0.25 * np.clip(spill, 0, 30)), g)
elif mode == "flat":
    dist = np.sqrt(((im - bg) ** 2).sum(-1))
    lo, hi = a.tol * 0.35, a.tol
    near = dist < hi
    lab, n = ndi.label(near)
    edge_ids = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    bgmask = np.isin(lab, edge_ids[edge_ids > 0])
    # 被描边围住的大块底色（手臂和身体之间的空隙）：颜色几乎等于底色、面积够大才去掉
    tight = (dist < a.tol * 0.3) & ~bgmask
    tl, tn = ndi.label(tight)
    if tn:
        sizes = ndi.sum(np.ones_like(dist), tl, index=np.arange(1, tn + 1))
        big = np.where(sizes > 1500)[0] + 1
        bgmask |= np.isin(tl, big)
    alpha = np.ones((H, W), np.float32)
    alpha[bgmask] = np.clip((dist[bgmask] - lo) / (hi - lo), 0, 1)
    # 抗锯齿边缘：底色区里的半透明像素，把底色从颜色里减掉一部分，避免叠到别的底上发灰
    al = alpha[..., None]
    rgb = np.where(al > 0.02, np.clip((im - bg * (1 - al)) / np.maximum(al, 0.02), 0, 255), im)
else:
    alpha = 1 - np.clip((np.min(im, -1) - 225) / 25, 0, 1)
    alpha = np.maximum(alpha, (im.max(-1) - im.min(-1) > 40).astype(np.float32))

mask = alpha > 0.1
grown = ndi.binary_dilation(mask, iterations=max(1, a.gap // 2))
lab, n = ndi.label(grown)
boxes = []
for i, sl in enumerate(ndi.find_objects(lab), 1):
    if sl is None:
        continue
    sub = mask[sl] & (lab[sl] == i)
    if sub.sum() < a.min:
        continue
    ys, xs = np.where(sub)
    y0, y1 = sl[0].start + ys.min(), sl[0].start + ys.max() + 1
    x0, x1 = sl[1].start + xs.min(), sl[1].start + xs.max() + 1
    boxes.append([int(x0), int(y0), int(x1), int(y1), i])

# 行优先：中心 y 相近（差小于平均高度一半）的算一行
boxes.sort(key=lambda bx: (bx[1] + bx[3]) / 2)
rows, cur = [], []
for bx in boxes:
    cy = (bx[1] + bx[3]) / 2
    if cur and abs(cy - np.mean([(c[1] + c[3]) / 2 for c in cur])) > np.mean([c[3] - c[1] for c in cur]) * 0.5:
        rows.append(cur)
        cur = []
    cur.append(bx)
if cur:
    rows.append(cur)

# 同一行里宽度明显超常（> 中位宽 1.6 倍）的块，多半是两个角色贴得太近：在中段找掩膜最稀的一列劈开
def split_wide(row):
    med = np.median([c[2] - c[0] for c in row])
    out = []
    for x0, y0, x1, y1, lid in row:
        w = x1 - x0
        if len(row) > 1 and w > med * 1.6:
            k = max(2, round(w / med))
            cols = (mask[y0:y1, x0:x1] & (lab[y0:y1, x0:x1] == lid)).sum(0).astype(float)
            cuts = []
            for j in range(1, k):
                c0 = int(w * (j - 0.35) / k)
                c1 = int(w * (j + 0.35) / k)
                cuts.append(x0 + c0 + int(np.argmin(cols[c0:c1])))
            edges = [x0] + cuts + [x1]
            for e0, e1 in zip(edges[:-1], edges[1:]):
                sub = mask[y0:y1, e0:e1] & (lab[y0:y1, e0:e1] == lid)
                ys = np.where(sub.any(1))[0]
                out.append([e0, y0 + int(ys.min()), e1, y0 + int(ys.max()) + 1, lid])
        else:
            out.append([x0, y0, x1, y1, lid])
    return out


rows = [split_wide(row) for row in rows]
ordered = [bx for row in rows for bx in sorted(row, key=lambda c: c[0])]

out = Path(a.out)
out.parent.mkdir(parents=True, exist_ok=True)
pick = {int(x) for x in a.pick.split(",")} if a.pick else None
rgba = np.dstack([rgb, alpha * 255]).clip(0, 255).astype(np.uint8)
prev = Image.open(a.src).convert("RGB")
d = ImageDraw.Draw(prev)
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
except OSError:
    font = ImageFont.load_default()
for k, (x0, y0, x1, y1, lid) in enumerate(ordered):
    d.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=4)
    d.text((x0 + 8, y0 + 4), str(k), fill=(255, 0, 0), font=font)
    if pick is not None and k not in pick:
        continue
    X0, Y0 = max(0, x0 - a.pad), max(0, y0 - a.pad)
    X1, Y1 = min(W, x1 + a.pad), min(H, y1 + a.pad)
    crop = rgba[Y0:Y1, X0:X1].copy()
    if mode != "keep":
        own = ndi.binary_dilation(lab[Y0:Y1, X0:X1] == lid, iterations=2)   # 别把相邻角色的边角带进来
        own[:, : x0 - X0] = False                                            # 劈开的块：只要自己那几列
        own[:, x1 - X0:] = False
        crop[..., 3] = (crop[..., 3] * own).astype(np.uint8)
        Image.fromarray(crop, "RGBA").save(f"{out}_{k}.png")
    else:
        Image.fromarray(crop[..., :3], "RGB").save(f"{out}_{k}.png")
    print(k, (x0, y0, x1 - x0, y1 - y0))
prev.thumbnail((1600, 1600))
prev.save(f"{out}__index.png")
print(f"mode={mode} bg={bg.round().tolist()} 共 {len(ordered)} 块 -> {out}_*.png")
