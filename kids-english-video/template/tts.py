"""按 script.json 合成全部配音 take（Fish Audio 公共音色）。

每句话、每个领唱/跟唱单词各合成一条，存在 audio/takes/。文件名带音色、语速、文字和第几条的哈希，
改了哪句只重合成哪句；删掉某个文件再跑一遍就能单独重来。
用法：.venv/bin/python tts.py [--check]
"""
import hashlib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fishvoice import synth

ROOT = Path(__file__).parent
TAKES = ROOT / "audio/takes"


def take_path(voice, text, k):
    h = hashlib.sha1(f"{voice['id']}|{voice.get('speed', 1.0)}|{text}|{k}".encode()).hexdigest()[:10]
    slug = re.sub(r"[^a-z]+", "_", text.lower()).strip("_")[:24]
    return TAKES / f"{slug}_{k}_{h}.wav"


# 新角色的推荐音色（Fish 公共音色），voices 里缺了就提示加这一项
SUGGEST = {
    "panda": {"id": "4fbed27c40e3465f98bc777fd0cc35ff", "name": "boy", "speed": 0.95},
    "elephant": {"id": "d9ce1833c191476db346efb50aa20722", "name": "boy (low)", "speed": 0.95},
    "frog": {"id": "b9011feb3c6f46ddaeb90043fab0eb4a", "name": "Kid", "speed": 1.05},
    "penguin": {"id": "051eccd6d8894155a0c544b8e5c0fd72", "name": "Baby", "speed": 1.05},
    "monkey": {"id": "829184c635314c9485e48690116ff8ad", "name": "Child voice boy", "speed": 1.1},
    "dino": {"id": "ee2fa25a56364be9a80d0028eecc6ea4", "name": "Girl", "speed": 1.0},
}


def check_voices(script):
    """台本里说话的角色都要在 voices 里有音色；缺了直接说在 voices 里加哪一项。"""
    who = []
    for sc in script["scenes"]:
        for ev in sc["events"]:
            if "say" in ev:
                who += ev["who"] if isinstance(ev["who"], list) else [ev["who"]]
    miss = sorted({w for w in who if w not in script.get("voices", {})})
    if miss:
        eg = ", ".join(f'"{w}": ' + json.dumps(SUGGEST.get(w, {"id": "<Fish 音色 id>", "name": w, "speed": 1.0}), ensure_ascii=False) for w in miss)
        raise SystemExit(f"script.json 的 voices 里没有 {'、'.join(json.dumps(w) for w in miss)}：在 voices 里加 {eg}（各角色的推荐音色见 references/script-format.md）")


def jobs(script):
    """(说话人, 文字, 第几条, 路径) 列表；同一个人同一句话在全片里第 n 次出现就用第 n 条 take，听起来不会一模一样。"""
    check_voices(script)
    seen, out = {}, []
    for sc in script["scenes"]:
        for ev in sc["events"]:
            if "say" not in ev:
                continue
            whos = ev["who"] if isinstance(ev["who"], list) else [ev["who"]]
            for _ in range(ev.get("chant", 1)):
                for w in whos:
                    k = seen.get((w, ev["say"]), 0)
                    seen[(w, ev["say"])] = k + 1
                    out.append((w, ev["say"], k, take_path(script["voices"][w], ev["say"], k)))
    return out


def main():
    TAKES.mkdir(parents=True, exist_ok=True)
    script = json.loads((ROOT / "script.json").read_text())
    todo = jobs(script)
    need = [j for j in todo if not j[3].exists()]
    print(f"共 {len(todo)} 条 take，需要合成 {len(need)} 条")
    if "--check" in sys.argv or not need:
        return

    def go(j):
        w, text, k, p = j
        v = script["voices"][w]
        synth(text, v["id"], p, speed=v.get("speed", 1.0))
        return f"{w:8s} {text!r} #{k}"

    with ThreadPoolExecutor(3) as ex:
        for i, msg in enumerate(ex.map(go, need), 1):
            print(f"[{i}/{len(need)}] {msg}", flush=True)


if __name__ == "__main__":
    main()
