# 英语启蒙动画 · 第N集：<英文标题>

<!-- 做完一集后把这份说明改成本集的实际情况（示范集《Do You Like Carrots?》的内容作为例子保留在下面，改的时候替换掉） -->

- 成片：`out/成片.mp4`（带伴奏）、`out/成片_无背景音乐.mp4`
- 规格：横屏 1920×1080，30fps，约 139 秒，响度 -16 LUFS
- 画风：flat 扁平矢量；配乐：ukulele 尤克里里；节拍 100 BPM
- 观众：3–6 岁刚接触英语的孩子，家长放给孩子看、孩子跟着说

## 教学内容

- 句型：Do you like ___? / Yes, I do! / No, I don't!
- 单词：carrots（胡萝卜）、bananas（香蕉）、apples（苹果）、broccoli（西兰花），外加 yummy（好吃）、Try it!（尝一尝）
- 跟读最后一题故意问 "Do you like socks?"，孩子要答 No, I don't!

## 段落

| 段 | 时间 | 内容 |
|---|---|---|
| 片头 | 0–9s | 标题落下，Bobo 打招呼，抱着野餐篮说 "Let's have a picnic!"，野餐布铺开 |
| carrots | 9–29s | Bobo 问兔子两遍 → 单词卡，胡萝卜飞进兔子手里 → 兔子领念 ×3（举着念、词尾咬一口、嚼）→ 兔子和 Bobo 一起念 ×3 |
| bananas | 29–49s | 同上，鱼在池塘里吃香蕉 |
| apples | 49–68s | 同上，小鸟站在苹果树上 |
| 反转 | 68–92s | 动物们问 Bobo 喜不喜欢西兰花 → "No, I don't!" → "Try it!" → 尝一口、眼睛一亮 → "Yummy! Yes, I do!" → 一起念 Broccoli ×3 |
| 跟读 | 92–132s | 老师问五个问题，每题留 3 拍空给孩子回答，再由 Bobo 给出标准答案 |
| 片尾 | 132–139s | 全员挥手 Bye-bye |

## 本集新生成的图

`角色/动作/` 里，品红底，以 `角色/设定稿/全员.jpg` 为参考图：食物表、各角色吃东西三连、Bobo 抱篮子 / 嫌弃 / 端详 / 咬 / 嚼 / 好吃。

## 重新生成

所有命令在项目目录下执行。

```bash
.venv/bin/python tts.py
```

```bash
.venv/bin/python build.py
```

```bash
.venv/bin/python render_all.py --jobs 4
```

```bash
.venv/bin/python assemble.py
```

- 改台词：改 `script.json` → 四步全跑（tts.py 只重合成改过的句子）
- 某句读得不好：删掉 `audio/takes/` 里对应的文件再从 tts.py 跑
- 换配乐：改 `script.json` 的 `music` → 只跑 assemble.py
- 调音量：改 `assemble.py` 顶部 `BGM_DB`、`SFX_DB`、`STYLE_DB` → 只跑 assemble.py
- 改画面：改 `代码工程/clips/<grammar>.js` → 抽帧检查（`cd 代码工程 && uv run --with "playwright==1.59.0" python render.py --spec spec.json --out ../build/stills --stills 秒数,秒数`）→ 渲染 → 混音
- 只重渲一段看效果：`render_all.py --from 40 --to 60 --out build/片段.mp4`

## 文件

- `script.json`：台本（场景、台词、中文、单词卡、领念、空拍、动作、音效）、画风、配乐、音色
- `tts.py` / `fishvoice.py`：Fish Audio 合成，每条 take 按音色+文字+序号缓存在 `audio/takes/`
- `build.py`：把 take 卡到拍点上，出人声音轨、口型、音效表和画面 spec
- `render_all.py`：分段并行渲染画面 → `build/画面.mp4`
- `代码工程/clips/<grammar>.js`：本集画面；通用画面库在 `代码工程/lib/kids.js`
- `sfx.py` / `bgm.py`：代码合成的音效和伴奏
- `assemble.py`：混音出片
- `prep_assets.py`、`代码工程/cut.py`、`角色/gen_img.sh`：生图、切图、对齐

做法说明见 `~/.claude/skills/kids-english-video/SKILL.md`。
