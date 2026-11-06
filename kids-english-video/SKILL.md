---
name: kids-english-video
description: 做给 3–6 岁孩子看的英语启蒙动画短片（横屏 1920×1080，两三分钟一集）：一个句型反复问答、单词卡、领念跟念、留空拍让孩子开口答、片尾再见。角色图用 Codex 生图，配音用 Fish Audio，画面用 Canvas 代码逐帧渲染，音效和儿歌伴奏由代码合成。画风五选一（扁平矢量、蜡笔手绘、剪纸拼贴、3D 黏土、水彩绘本），配乐五选一（尤克里里、音乐盒、玩具进行曲、8-bit、不要）。用户说做英语儿歌视频、幼儿英语、少儿英语启蒙、亲子英语动画、英语单词/句型动画、Can you…? / Do you like…? 这类问答动画，或者要"做下一集""换个画风/配乐重做一集"时都用这个 skill，即使没提画风、Fish Audio 或 Codex。也用于修改用这套流程做出的已有集（改台词、重配某句、换画风、调音量、重渲染）。
---

# 儿童英语启蒙动画

一集的样子（示范集《Do You Like Carrots?》，约 139 秒）：

| 段 | 内容 |
|---|---|
| 片头 | 标题字母一个个掉下来，主角 Bobo 打招呼，引出场景 |
| 3–4 轮问答 | Bobo 问一个动物两遍 → 动物回答 → 老师（不出镜）念单词，单词卡弹出 → 动物领念 ×3 → 动物和 Bobo 齐念 ×3。每轮换一个单词、一个动物 |
| 反转 | 动物们反过来问 Bobo，先说 No，再被说服变成 Yes（制造一个笑点，顺便练否定回答） |
| 跟读 | 老师提问，留 3 拍空白（画面出"轮到你说！"和节拍点），然后 Bobo 给标准答案。最后一题故意问个荒唐的，答 No |
| 片尾 | 全员挥手 Bye-bye |

所有台词都卡在同一个节拍上（默认 100 BPM），伴奏也用这个节拍，念起来像童谣。口型按配音响度逐帧切换。

## 目录

```
kids-english-video/
├── template/                 一集的项目骨架（new_episode.py 复制它）
│   ├── script.json           台本：句型、台词、中文、单词卡、领念、空拍、动作、音效、画风、配乐、音色
│   ├── tts.py fishvoice.py   Fish Audio 配音（每条按文字缓存）
│   ├── build.py              卡拍点 → 人声、口型、音效表、画面 spec
│   ├── render_all.py         分段并行渲染画面
│   ├── assemble.py bgm.py sfx.py   混音、伴奏、音效
│   ├── prep_assets.py        切好的图 → 素材（去底色边、统一身高、对齐）
│   ├── 角色/gen_img.sh       Codex 生图
│   └── 代码工程/             渲染器：clip.html + lib/kids.js（画面库 K）+ clips/<本集>.js（本集画面）
├── characters/<画风>/        五种画风的基础角色帧、设定稿 lineup.jpg、画风提示词 style_prompt.txt
├── assets/画风总览.jpg        五种画风同一画面的对比（每行一种：扁平、蜡笔、剪纸、黏土、水彩）
├── scripts/new_episode.py    新建一集
├── scripts/preview_styles.py 渲画风预览（调画风参数后检查用）
└── references/               按需读
```

## 流程

### 0. 定内容、画风、配乐

- **内容**：一个句型（Can you hop? / Do you like carrots? / Where is the cat? / What color is it?…）+ 4 个具体、能画出来的单词 + 一个反转 + 一道荒唐题。句子短，3–6 岁能跟。用户只给了主题时自己定，写进台本前用一两句话说给用户听。
- **画风、配乐**：用户没说就问一次（AskUserQuestion），把 `assets/画风总览.jpg` 发给用户看。

| 画风 `style` | 样子 | 英文字体 | 速度 |
|---|---|---|---|
| `flat` 扁平矢量 | 干净色块，最快，素材最全（前两集的吃东西、跳、跑等动作帧都有） | Lilita One | 每帧约 4 ms |
| `crayon` 蜡笔手绘 | 蜡笔笔触、纸纹、描边抖动，一拍二 | Gochi Hand | 约 200 ms |
| `paper` 剪纸拼贴 | 纸片投影、毛边、纸纤维，一拍二 | Lilita One | 约 180 ms |
| `clay` 3D 黏土 | 鼓起来的高光暗部、软投影、暗角，一拍二 | Lilita One | 约 150 ms |
| `watercolor` 水彩绘本 | 边缘积色、颜料颗粒、晕染、纸纹 | Kalam | 约 220 ms |

| 配乐 `music` | 适合 |
|---|---|
| `ukulele` 尤克里里 | 默认，欢快 |
| `musicbox` 音乐盒 | 轻柔、睡前，配水彩 |
| `march` 玩具进行曲 | 神气，动作类句型（Can you jump?） |
| `chiptune` 8-bit | 俏皮，配扁平或黏土 |
| `none` | 不要伴奏 |

### 1. 新建项目

```bash
python3 ~/.claude/skills/kids-english-video/scripts/new_episode.py <项目目录> --style crayon --music musicbox --grammar whereis --title "Where Is the Cat?" --title-zh "小猫在哪里？"
```

复制模板、该画风的基础角色帧（4 个角色 × 闭嘴/半张/大张嘴、挥手、大笑、欢呼）、设定稿和画风提示词，建 `.venv`（uv，Python 3.12），生成音效。`--example` 原样复制示范集（扁平风素材齐全，可以直接跑通全流程当参照）。项目目录放在用户的视频目录下，按 `日期-片名` 命名。

### 2. 写台本 `script.json`

格式和写法见 `references/script-format.md`。要点：每个事件一行；`rest` 是空几拍；`chant` + `every` 是领念；`card` 弹单词卡；`quiz` / `answer` / `{"rest": 3, "wait": true}` 组成跟读题；`act` 是不说话的动作段（几拍）；音效挂在事件上。

### 3. 生成本集需要的新图

基础帧只有站着说话、挥手、大笑、欢呼。本集的物品（食物、动物、颜色物件）和特殊动作（吃、找、躲、指）要按选定画风生成。流程、提示词写法、切图和对齐见 `references/characters.md`。要点：

- 参考图用项目里的 `角色/设定稿/全员.jpg`，提示词末尾直接拼 `角色/画风提示词.txt`（画风段 + 品红底段）。
- 品红底 #FF00FF（绿色物品不能用绿幕）。`gen_img.sh` 可以后台并行跑几张。
- 切图 `代码工程/cut.py 表.png --out 角色/切图/<前缀> --mode flat --tol 60`，再 `prep_assets.py` 去边、按已有帧身高缩放、按下半身对齐。
- 生完一定打开看：Codex 偶尔漏画、多画、画成别的姿势，切图偶尔把两个角色并成一块。

### 4. 配音

```bash
.venv/bin/python tts.py
```

Fish Audio `s2.1-pro-free`，音色 ID 在 script.json `voices` 里（沿用前两集：Bobo、兔子、鱼、小鸟、老师）。API key 沿用 manim-explainer-video 技能的查找顺序，不要打印 key。每条按音色+文字+序号缓存，改哪句只重合成哪句；某条读得不好就删掉 `audio/takes/` 里那个文件再跑。合成完挑几条听（或用 mlx-whisper 转写核对），尤其是感叹词。

### 5. 编排

```bash
.venv/bin/python build.py
```

把每条 take 卡到拍点上，输出人声 `build/voice.wav`、`build/timeline.json`、`代码工程/spec.json`，打印每个场景的起止时间。

### 6. 写本集画面 `代码工程/clips/<grammar>.js`

从示范集 `doyoulike.js` 改（new_episode.py 已经复制好、改了名）。画面库 K 提供了草地、池塘、树、野餐布、气泡、单词卡、领念行、跟读环节、镜头、转场、片头标题，场景代码主要是摆角色、写每个场景特有的小动作。API 和规则见 `references/scene-cookbook.md`。最重要的一条：**代码画的东西放进 `K.layer(c, kind, g => …)` 里用 g 画**，画风材质（蜡笔、剪纸、黏土、水彩）才会加上；扁平风下它直接画，不影响。

改完先抽帧看：

```bash
cd 代码工程 && uv run --with "playwright==1.59.0" python render.py --spec spec.json --out ../build/stills --stills 2,10.5,15,22
```

每个场景至少看一张，看完再整片渲染。

### 7. 渲染、混音

```bash
.venv/bin/python render_all.py --jobs 4
```

```bash
.venv/bin/python assemble.py
```

扁平风整集 4 段并行约 70 秒；其他画风约 8–10 分钟（蜡笔实测 139 秒的片子约 8.5 分钟，一拍二的自动跳过重复帧），放后台跑。出 `out/成片.mp4`（带伴奏）和 `out/成片_无背景音乐.mp4`，响度 -16 LUFS。调音量改 `assemble.py` 顶部的 `BGM_DB` / `SFX_DB` / `STYLE_DB`，只重跑 assemble。

### 8. 检查、交付

- 抽 6–8 帧拼一张图看（片头、每轮单词卡、跟读、片尾）。
- 听：开头、一轮问答、跟读空拍。确认音效没盖住单词开头。
- 把项目 `README.md` 改成本集说明（模板里有格式）。
- 用 SendUserFile 发成片。

## 改已有的一集

| 要改 | 做什么 |
|---|---|
| 台词、加减一轮 | 改 script.json → tts → build → 渲染 → assemble |
| 某句读得不好 | 删 `audio/takes/` 里那条 → tts → build → 渲染 → assemble（时间轴可能变） |
| 换画风 | script.json 的 `style` 改掉，`代码工程/assets/` 换成 `characters/<新画风>/` 的帧，本集新生成的图按新画风重生 → build → 渲染 → assemble |
| 换配乐 | 改 `music` → 只跑 assemble |
| 音量 | 改 assemble.py 顶部 → 只跑 assemble |
| 画面细节 | 改 clips/<grammar>.js → 抽帧 → 渲染 → assemble。只改一段可以 `render_all.py --from 40 --to 60 --out build/片段.mp4` 先看 |

## 参考文档

- `references/script-format.md`：script.json 全部字段、事件类型、音效清单、内容设计经验
- `references/characters.md`：角色设定、五种画风的提示词、生新动作表/物品图、切图、对齐、扩一个新画风
- `references/scene-cookbook.md`：画面库 K 的 API、材质层规则、示范集的场景结构、常见写法
- `references/music.md`：五种配乐的编曲、音量、怎么加新风格
- `references/pitfalls.md`：踩过的坑（Codex 生图、切图、Fish 读音、渲染速度、浏览器滤镜）
