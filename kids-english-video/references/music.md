# 配乐和音效

伴奏和音效全部用 numpy 合成（`bgm.py`、`sfx.py`），没有版权问题。伴奏和台词用同一个节拍（script.json 的 `bpm`，第一拍在 0 秒），念白听起来像跟着音乐打拍子的童谣。

## 五种配乐（script.json 的 `music`）

| 名字 | 和弦 | 编曲 | 适合 |
|---|---|---|---|
| `ukulele` | C-F-G-C | 拨弦低音（每拍，第三拍五度）+ 尤克里里反拍扫弦（Karplus-Strong）+ 木琴八分音符分解和弦 + 底鼓、拍手、沙锤 | 默认，欢快，什么画风都行 |
| `musicbox` | C-Am-F-G | 八音盒钢片音（泛音 6.27、17.55 倍）高音八分分解和弦 + 每小节一、三拍低音盒音 + 很轻的长音垫底 + 极轻沙锤点拍子，没有鼓 | 轻柔、睡前、配水彩 |
| `march` | C-F-G-C | 大号"嘭"（一、三拍，根音和五度）+ 铜管短和弦"恰"（二、四拍）+ 钟琴每拍一个和弦音 + 大鼓、军鼓，每四小节最后一拍小军鼓滚奏 | 神气，动作类句型 |
| `chiptune` | C-Am-F-G | 方波低音八度跳（八分）+ 25% / 12.5% 脉冲波十六分琶音 + 三角波底鼓、噪声军鼓和镲 | 俏皮，配扁平、黏土 |
| `none` | | 不要伴奏，assemble.py 只出一个无伴奏的成片 | |

都没有旋律线，免得和念白抢。

试听：`.venv/bin/python bgm.py --demo <目录>` 每种出 16 秒；`bgm.py 30 out.wav march 100` 出指定风格和节拍。

## 混音（assemble.py）

- 伴奏生成时统一到均方根 -20 dBFS，混音时再乘 `BGM_DB`（-13 dB）和 `STYLE_DB` 里该风格的修正（音乐盒 -3、8-bit -1）。
- 人声出现时伴奏侧链压低（threshold 0.03，ratio 4，release 350 ms），说话时伴奏让开，空拍时伴奏回来。
- 音效按 `build/timeline.json` 放，整体 `SFX_DB`（-1 dB），每个音效自己的 gain 写在 script.json。
- 最后整体 loudnorm 到 -16 LUFS、真峰值 -1.5 dB。
- 出两个版本：`out/成片.mp4`（带伴奏）、`out/成片_无背景音乐.mp4`（给需要自己配乐的平台）。

改这些数只重跑 `assemble.py`，几秒钟，不用重新渲染画面。

## 加一种新配乐

在 bgm.py 里：

1. 写乐器（返回单声道 numpy 数组的函数，参考 `tine`、`horn`、`pulse`）。
2. 写编曲函数 `def xxx(nb, beat, L)`：nb 小节数、beat 一拍秒数、L 总样本数；建几条 `np.zeros((L, 2))` 立体声轨，用 `add(轨, 样本, 秒, pan)` 把音符放到 `小节 * 4 * beat + 拍 * beat` 上，最后把各轨加起来返回。
3. 登记到 `ARRANGE` 和 `STYLES`，new_episode.py 的 `MUSIC` 也加上说明。
4. `bgm.py --demo` 试听，测一下响度（`ffmpeg -i x.wav -af ebur128 -f null -`），和别的风格差太多就在 assemble.py 的 `STYLE_DB` 里修正。

要点：不写旋律；低音在一、三拍；鼓轻；和弦循环 4 小节；随机数用模块里的 `rng`（generate 每次重置种子，同样的输入出同样的伴奏）。

## 音效

`sfx.py` 合成 22 个卡通音效到 `sfx/`（new_episode.py 建项目时已经跑过）。清单和挂法见 script-format.md。新音效：写一个函数（参考 `crunch`、`munch`、`slide`），登记到表里，重跑 `.venv/bin/python sfx.py`。
