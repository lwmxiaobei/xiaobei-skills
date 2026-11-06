#!/usr/bin/env python3
"""新建一集儿童英语动画项目：复制模板 + 选定画风的角色基础帧 + 设定稿，建 Python 环境。

用法：
  python3 new_episode.py <项目目录> --style crayon --music march [--grammar canyouswim] [--title "Can You Swim?"] [--title-zh "你会游泳吗？"]
  python3 new_episode.py <项目目录> --example          # 原样复制示范集《Do You Like Carrots?》（扁平风才有全部素材）
  python3 new_episode.py --list                         # 列出画风、配乐

画风：flat 扁平矢量 / crayon 蜡笔手绘 / paper 剪纸拼贴 / clay 3D 黏土 / watercolor 水彩绘本
配乐：ukulele 尤克里里 / musicbox 音乐盒 / march 玩具进行曲 / chiptune 8-bit / none 不要
项目里：
  代码工程/assets/      该画风的基础帧（4 个角色 × m0 m1 m2 wave laugh cheer），扁平风另有前两集的全部动作帧
  角色/设定稿/全员.jpg   该画风的设定稿，生新动作表时当参考图
  角色/画风提示词.txt    该画风的提示词段落（Art style + Background），新提示词直接拼进去
  clips/<grammar>.js    本集画面（从示范集复制改名，等着改）
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SK = Path(__file__).resolve().parent.parent
STYLES = {"flat": "扁平矢量", "crayon": "蜡笔手绘", "paper": "剪纸拼贴", "clay": "3D 黏土", "watercolor": "水彩绘本"}
MUSIC = {"ukulele": "尤克里里（欢快，默认）", "musicbox": "音乐盒（轻柔，适合睡前、水彩）", "march": "玩具进行曲（神气、有劲）",
         "chiptune": "8-bit 游戏风（俏皮、电子）", "none": "不要配乐"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", nargs="?")
    ap.add_argument("--style", default="flat", choices=STYLES)
    ap.add_argument("--music", default="ukulele", choices=MUSIC)
    ap.add_argument("--grammar", help="本集画面文件名（小写字母），默认用目录名里的字母")
    ap.add_argument("--title")
    ap.add_argument("--title-zh")
    ap.add_argument("--example", action="store_true", help="保留示范集的台本和画面，不改名")
    ap.add_argument("--no-venv", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list or not a.dir:
        print("画风："); [print(f"  {k:11s}{v}") for k, v in STYLES.items()]
        print("配乐："); [print(f"  {k:11s}{v}") for k, v in MUSIC.items()]
        return
    dst = Path(a.dir).expanduser().resolve()
    if dst.exists() and any(dst.iterdir()):
        sys.exit(f"{dst} 已存在且不是空目录")
    shutil.copytree(SK / "template", dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
    ch = SK / "characters" / a.style
    assets = dst / "代码工程/assets"
    assets.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in ch.glob("*.png"):
        shutil.copy(p, assets / p.name); n += 1
    (dst / "角色/设定稿").mkdir(parents=True, exist_ok=True)
    (dst / "角色/动作").mkdir(parents=True, exist_ok=True)
    (dst / "角色/切图").mkdir(parents=True, exist_ok=True)
    shutil.copy(ch / "lineup.jpg", dst / "角色/设定稿/全员.jpg")
    shutil.copy(ch / "style_prompt.txt", dst / "角色/画风提示词.txt")

    s = json.loads((dst / "script.json").read_text())
    s["style"], s["music"] = a.style, a.music
    if not a.example:
        g = a.grammar or re.sub(r"[^a-z]", "", dst.name.lower()) or "episode"
        if not re.fullmatch(r"[a-z][a-z0-9_]*", g):
            sys.exit("--grammar 只能是小写字母、数字、下划线")
        if g != "doyoulike":
            src = (dst / "代码工程/clips/doyoulike.js").read_text()
            (dst / f"代码工程/clips/{g}.js").write_text(src.replace("CLIPS.doyoulike", f"CLIPS.{g}"))
        s["grammar"] = g
        if a.title: s["title"] = a.title
        if a.title_zh: s["title_zh"] = a.title_zh
    text = (dst / "script.json").read_text()
    for k in ("style", "music", "grammar", "title", "title_zh"):                 # 只换开头这几个字段，保留每个事件一行的排版
        text = re.sub(rf'^  "{k}": .*?,$', f'  "{k}": {json.dumps(s[k], ensure_ascii=False)},', text, count=1, flags=re.M)
    (dst / "script.json").write_text(text)

    if not a.no_venv:
        subprocess.run(["uv", "venv", "-q", "--python", "3.12", str(dst / ".venv")], check=True)
        subprocess.run(["uv", "pip", "install", "-q", "--python", str(dst / ".venv/bin/python"), "numpy", "scipy", "pillow", "msgpack"], check=True)
        subprocess.run([str(dst / ".venv/bin/python"), "sfx.py"], cwd=dst, check=True, capture_output=True)   # 音效是代码合成的，先生成好
    print(f"项目 {dst}")
    print(f"  画风 {a.style}（{STYLES[a.style]}），配乐 {a.music}（{MUSIC[a.music]}），画面文件 代码工程/clips/{s['grammar']}.js")
    print(f"  基础角色帧 {n} 张 → 代码工程/assets/")
    if a.style != "flat" and a.example:
        print("  注意：示范集用到的食物、吃东西、野餐动作帧只有扁平风有，换别的画风要先按 references/characters.md 生成这些帧")


if __name__ == "__main__":
    main()
