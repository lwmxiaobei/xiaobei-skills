# 角色、画风、生图、切图

## 角色

原创角色，四个出镜 + 一个不出镜的老师：

- **Bobo**（主角，`bobo`）：橘色的圆毛球，头和身子是一个球，奶油色椭圆肚皮，头顶两只小圆耳朵和一撮深橘色卷毛，短短的管状胳膊和小短腿，大白眼睛黑眼珠，咧嘴笑露一颗小白牙，粉脸蛋。
- **兔子**（`rabbit`）：浅粉色，站着，比 Bobo 高一点，长耳朵内侧玫粉色，白色圆嘴套两颗门牙，白肚皮，大脚。
- **鱼**（`fish`）：天蓝色圆鱼，三分之四侧面朝向观众，身上深蓝圆点，宝蓝色扇形大尾巴和小鳍，浮在离地一点的地方。
- **小鸟**（`bird`）：最小，阳光黄的圆小鸡，头顶三根小羽毛，橙色三角嘴，金黄色小翅膀，细橙腿，粉脸蛋。
- **老师**（`teacher`）：只有声音，画面上用紫色（`#7A4CFF`）代表。

设定稿（四个角色一排）在 `characters/<画风>/lineup.jpg`，new_episode.py 复制到项目的 `角色/设定稿/全员.jpg`。生任何新图都把它当参考图。

## 已有的帧

| 画风 | 帧 |
|---|---|
| 五种都有 | `<角色>_m0` 闭嘴、`_m1` 半张、`_m2` 大张（口型），`_wave` 挥手，`_laugh` 大笑，`_cheer` 欢呼跳起 |
| 只有 flat | 前两集的动作：`bobo_ask bobo_basket bobo_bite bobo_chew bobo_fall bobo_flap bobo_hold bobo_run1/2 bobo_yuck bobo_yum`，`rabbit_crouch rabbit_jump rabbit_eat0/1/2`，`fish_swim1/2 fish_eat0/1/2`，`bird_fly1/2 bird_eat0/1/2`，食物 `food_apple food_banana food_broccoli food_carrot food_sock` |
| 只有 crayon | 第3集《Where Is the Cat?》：小猫 `cat_m0/m1/m2 cat_lie cat_crouch cat_jump`（新角色，灰色虎斑小猫），`bobo_search bobo_shrug bobo_lookup bobo_point bobo_headtouch bobo_walk bobo_cover0/1/2 bobo_peek bobo_hug bobo_startle`，`rabbit_point rabbit_pointup fish_point fish_pointup bird_point bird_pointup`（往左指 / 往左上指着笑），道具 `prop_box prop_table prop_tree prop_yarn` |

示范集要用到"只有 flat"那一行里的吃东西、野餐、食物帧。用别的画风做示范集，或者新一集要类似动作，就按下面的方法用该画风生成。新生成的帧顺手复制一份到 `characters/<画风>/`，下一集就能直接用。

## 五种画风

画风提示词在 `characters/<画风>/style_prompt.txt`（两段：Art style + Background），生新图时直接拼在提示词末尾。代码画的背景、气泡、单词卡的材质参数在 `lib/kids.js` 的 `THEMES` 里（见 scene-cookbook.md）。

| 画风 | 角色图的样子 | 代码画面的材质 |
|---|---|---|
| flat 扁平矢量 | 粗描边、平涂色块、简单高光 | 无，直接画 |
| crayon 蜡笔手绘 | 蜡笔笔触和纸纹、略抖的深色描边 | 深色描边、纸纹白点、颗粒、线条"沸腾"抖动，一拍二 |
| paper 剪纸拼贴 | 每块都是剪下来的彩纸，层层叠着，下层有薄影 | 每块投影、剪刀毛边、纸纤维、暗角，一拍二 |
| clay 3D 黏土 | 定格动画的橡皮泥，左上打光，有指纹 | 鼓起来的高光暗部、软投影、暗角，一拍二 |
| watercolor 水彩绘本 | 透明水彩晕染、边缘积色、铅笔细线 | 边缘积色、颜料颗粒、晕染、纸纹、轻微抖动 |

## 生图

```bash
角色/gen_img.sh <输出.png> <提示词文件> [参考图...]
```

用官方 codex CLI（npx `@openai/codex@0.160.1`）的图像生成，按本次会话 ID 到 `~/.codex/generated_images/<id>/` 取图。stdin 已接 `/dev/null`，可以 `&` 后台并行跑 4–5 张。偶尔网络失败（`image generation failed: connection failed`），脚本会打印 FAIL，重跑那一张就行。

### 动作表（一个角色多个姿势）

一张 3:2 横图，3×2 六个姿势。提示词结构（以 Bobo 为例）：

```
Sprite sheet of BOBO (the round orange creature, first character in the attached reference): SIX full-body poses of the same character arranged in a 3 by 2 grid (two rows of three), landscape 3:2 image, evenly spaced.
1) front view, holding a big orange carrot with both hands up to show it, big happy open smile;
2) front view, biting the carrot, eyes closed happily, cheeks puffed;
3) front view, chewing with closed mouth, cheeks round, eyes happy arcs;
4) ...
（拼上 角色/画风提示词.txt 的两段）
```

- 第几个角色写清楚（参考图里从左往右 first / second / third / fourth）。
- 每个姿势一句，写朝向、手在干什么、表情。同一组需要换帧不跳的（口型、吃东西三连），写"IDENTICAL … except the mouth"。
- 物品（胡萝卜）写在姿势里时说清颜色和大小，避免画成别的东西。
- 品红底：所有画风都用 `#FF00FF`。绿色的东西多（西兰花、树叶、青蛙）不能用绿幕，品红最安全。提示词里已经要求角色不含品红、紫色；要画紫色的东西（葡萄）时去掉这句，改用浅灰底（`#E6E6E6`），切图时 `--bg` 跟着改。

### 物品图（食物、玩具、动物）

一张图放 4–6 个物品，一行或两行，彼此留宽。提示词："Six separate objects for a preschool cartoon, side by side with wide gaps, each one alone: 1) a carrot … 2) …" + 画风两段。

### 新角色

先按设定稿的写法生一张新角色的设定稿（参考图仍给全员设定稿，提示词说 "a NEW character in exactly the same art style as the attached lineup"），再生它的口型 + 动作表。

## 切图、对齐

```bash
.venv/bin/python 代码工程/cut.py 角色/动作/bobo_吃.png --out 角色/切图/bobo_eat --mode flat --tol 60
```

按连通区域切，行优先编号，输出 `<前缀>_<序号>.png` 和带序号的总览 `<前缀>__index.png`，**打开总览核对**：

- 两个姿势挨得近被并成一块：加 `--gap 6`（默认 28，是为了把汗滴、动作线并回角色）。
- 碎块（星星、汗滴）被单独切出来：`--min` 调大，或者在下一步用 `-` 跳过。
- 顺序和提示词不一致（Codex 有时排成两列）：下一步 `--names` 按实际顺序写。

```bash
# 一组动作：第 0 帧当参考，缩放到和已有的 bobo_m0 一样高，按下半身对齐
.venv/bin/python prep_assets.py bobo_eat --names bobo_hold,bobo_bite,bobo_chew --ref 0 --height-of bobo_m0 --frac 0.35
# 物品：每个单独处理，长边 360 像素
.venv/bin/python prep_assets.py food --names food_carrot,food_banana,food_apple,- --single --long 360
```

- `--frac` 是"下半身"占比，用来对齐：两脚站立 0.25–0.35，鱼这种没脚的 1.0。
- 跳起来、飞起来的姿势不要当参考帧；参考帧选站着的那张。
- `--height-of` 按已有素材的画布高度算，而旧帧画布上下常带透明边（rabbit_m0 下面 20 像素、fish_m0 下面 63 像素），新帧会偏大。先量旧帧不透明区域的高度用 `--height`，再把新帧脚底的透明边补成和旧帧一样（第3集踩过）。
- 物品图提示词要写明 NO faces：参考图是带脸的角色，Codex 会顺手给盒子、桌子、树都画上脸。
- 结果写进 `代码工程/assets/`，画面里用名字引用（`K.img('bobo_bite')`，或 `K.ch(c, 'bobo', x, y, t, {pose: 'bobo_bite'})`）。
- 处理完拼一张图看：大小和已有帧一致、换帧时脚不跳、没有品红边。

## 加第六种画风

1. 写画风段落（参考 `characters/*/style_prompt.txt` 的写法：像什么、材质、描边、光、颜色，加 "Keep the character identity…"），拼上品红底段。
2. 生设定稿：提示词 = `characters/lineup_prompt.txt`（四个角色的描述）+ 新画风段（设定稿用的画风段去掉 "exactly match the attached reference lineup" 这半句），参考图用 `characters/flat/lineup.jpg`。
3. 用新设定稿当参考，每个角色生一张 6 姿势表（m0 m1 m2 wave laugh cheer），切图，`prep_assets.prep(...)` 缩放到 flat 对应 `<角色>_m0` 的高度，存到 `characters/<新画风>/`，连同 `lineup.jpg` 和 `style_prompt.txt`。
4. `lib/kids.js` 的 `THEMES` 加一项（字体、调色板 pal、材质 mat、step、post），`build.py` 的 `STYLES`、`new_episode.py` 的 `STYLES` 加上名字。
5. `scripts/preview_styles.py --styles <新画风> --out <目录> --sheet` 看效果，调 mat 参数。
