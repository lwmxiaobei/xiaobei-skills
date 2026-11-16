"""build.py：场景字段透传、wait 种类、音乐暂停时段、按种类加的自动音效。"""
import json
import shutil

import numpy as np
import pytest
from scipy.io import wavfile

from harness import TPL, dummy_takes, run_py

VOICES = json.loads((TPL / "script.json").read_text())["voices"]


def script(wait2="guess"):
    return {"title": "T", "grammar": "fixture", "style": "flat", "bpm": 100, "voices": VOICES,
            "scenes": [{"id": "a", "animal": "rabbit", "round": "guess", "bg": "beach", "events": [
                {"who": "bobo", "say": "Hello!"}, {"rest": 2, "wait": True}, {"rest": 3, "wait": wait2},
                {"who": "teacher", "say": "Freeze!", "music": "stop"}, {"rest": 4, "wait": "freeze", "music": "stop"},
                {"act": "dance", "beats": 2, "music": "stop"}]}]}


def run_build(dst, wait2="guess", data=None):
    shutil.copytree(TPL, dst, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
    (dst / "代码工程/assets").mkdir(exist_ok=True)
    (dst / "script.json").write_text(json.dumps(data or script(wait2)))
    run_py(dst, "sfx.py")
    if not (dst / "sfx/drumroll.wav").exists():                       # Task 2 之前的占位
        wavfile.write(dst / "sfx/drumroll.wav", 48000, np.zeros((4800, 2), np.float32))
    dummy_takes(dst)
    return run_py(dst, "build.py", check=False)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    dst = tmp_path_factory.mktemp("b") / "p"
    r = run_build(dst)
    assert r.returncode == 0, r.stdout + r.stderr
    return json.loads((dst / "build/timeline.json").read_text()), json.loads((dst / "代码工程/spec.json").read_text())


def test_scene_fields(built):
    s = built[0]["scenes"][0]
    assert (s["round"], s["bg"], s["animal"]) == ("guess", "beach", "rabbit") and "events" not in s


def test_wait_kinds(built):
    tl = built[0]
    assert [w["kind"] for w in tl["waits"]] == ["say", "guess", "freeze"] and {w["scene"] for w in tl["waits"]} == {"a"}


def test_stops_merged(built):
    tl = built[0]
    fz = next(l for l in tl["lines"] if l["text"] == "Freeze!")
    assert len(tl["stops"]) == 1 and tl["stops"][0] == pytest.approx([fz["t0"], tl["acts"][0]["t1"]], abs=1e-3)


def test_auto_sfx(built):
    tl = built[0]
    say, guess, frz = tl["waits"]
    names = lambda a, b: [e["name"] for e in tl["sfx"] if a - 1e-6 <= e["at"] < b - 1e-6]
    assert names(say["t0"], say["t1"]).count("tick") == 2
    assert names(guess["t0"], guess["t1"]) == ["drumroll"]
    assert names(frz["t0"], frz["t1"]) == []


def test_spec_has_stops(built):
    tl, spec = built
    assert spec["data"]["stops"] == tl["stops"]


def test_bad_wait_kind(tmp_path):
    r = run_build(tmp_path / "p", wait2="jump")
    assert r.returncode != 0 and "wait 只能是" in r.stdout + r.stderr


def test_trans_sfx(tmp_path):
    """换场的自动音效跟着转场走：翻页 pageflip、泡泡 pop、滑梯 slide_down、小火车 choo（车开出来那一拍），其余 whoosh。"""
    sc = lambda i, trans=None, travel=False: {"id": i, "bg": "beach", **({"trans": trans} if trans else {}), "events":
        ([{"act": "travel", "beats": 4}] if travel else []) + [{"who": "bobo", "say": "Hello!"}]}
    data = {**script(), "scenes": [sc("a"), sc("b", "page"), sc("c", "train", True), sc("d", "bubbles"), sc("e", "slide"), sc("f", "map", True), sc("g")]}
    r = run_build(tmp_path / "p", data=data)
    assert r.returncode == 0, r.stdout + r.stderr
    tl = json.loads((tmp_path / "p/build/timeline.json").read_text())
    near = lambda t: sorted(e["name"] for e in tl["sfx"] if abs(e["at"] - t) < 0.35)
    got = [near(s["t0"]) for s in tl["scenes"][1:]]
    assert got == [["pageflip"], ["choo"], ["pop"], ["slide_down"], ["whoosh"], ["whoosh"]], got


def test_voice_missing(tmp_path):
    """台本里有新角色说话、voices 里没配它：build.py 报错说清在 voices 里加哪一项（不碰 Fish）。"""
    dst = tmp_path / "p"
    shutil.copytree(TPL, dst, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
    s = script(); s["scenes"][0]["events"].insert(0, {"who": "panda", "say": "Hi!"})
    s["voices"] = {k: v for k, v in VOICES.items() if k != "panda"}
    (dst / "script.json").write_text(json.dumps(s))
    r = run_py(dst, "build.py", check=False)
    out = r.stdout + r.stderr
    assert r.returncode != 0 and "voices" in out and '"panda"' in out and "Traceback" not in out, out[-800:]


def test_owl_flag_passed(tmp_path):
    """script.json 的 "owl" 原样进 spec.data（不写就是 true）。"""
    s = script(); s["owl"] = False
    r = run_build(tmp_path / "p", data=s)
    assert r.returncode == 0, r.stdout + r.stderr
    assert json.loads((tmp_path / "p/代码工程/spec.json").read_text())["data"]["owl"] is False


def test_guest_lineup_copied(tmp_path):
    """new_episode.py 把新角色设定稿复制成 角色/设定稿/客串.jpg，新集默认打开猫头鹰。"""
    import subprocess, sys
    from harness import SK
    dst = tmp_path / "ep"
    subprocess.run([sys.executable, str(SK / "scripts/new_episode.py"), str(dst), "--no-venv", "--style", "clay"], check=True, capture_output=True)
    assert (dst / "角色/设定稿/客串.jpg").read_bytes() == (SK / "characters/clay/lineup_guests.jpg").read_bytes()
    assert "owl" not in json.loads((dst / "script.json").read_text())


def test_answer_good(tmp_path):
    """跟读题答案："good" 写明对错（It's a panda! 对 → ding，绿勾；故意答错 → nope），不写时 No 开头算错、其余算对，原样进 spec。"""
    s = script()
    s["scenes"][0]["events"] = [
        {"who": "teacher", "say": "What's this?", "quiz": "panda"}, {"rest": 3, "wait": True},
        {"who": "bobo", "say": "It's a panda!", "answer": "panda", "good": True},
        {"who": "teacher", "say": "What's this?", "quiz": "frog"}, {"rest": 3, "wait": True},
        {"who": "bobo", "say": "It's a panda!", "answer": "frog", "good": False},
        {"who": "teacher", "say": "Do you like socks?", "quiz": "socks"}, {"rest": 3, "wait": True},
        {"who": "bobo", "say": "No, I don't!", "answer": "socks"},
        {"who": "teacher", "say": "What color is it?", "quiz": "red"}, {"rest": 3, "wait": True},
        {"who": "bobo", "say": "It's red!", "answer": "red"}]
    r = run_build(tmp_path / "p", data=s)
    assert r.returncode == 0, r.stdout + r.stderr
    tl = json.loads((tmp_path / "p/build/timeline.json").read_text())
    ans = [l for l in tl["lines"] if "answer" in l]
    near = lambda l: [e["name"] for e in tl["sfx"] if abs(e["at"] - (l["t0"] - 0.1)) < 1e-3]
    # 不写 good：No 开头算错，其余算对（It's red! 不能因为不是 Yes 开头就配 nope）
    assert [near(l) for l in ans] == [["ding"], ["nope"], ["nope"], ["ding"]]
    assert [l.get("good") for l in ans] == [True, False, None, None]
