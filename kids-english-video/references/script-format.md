# script.json 台本格式

一个文件定义整集：标题、画风、配乐、节拍、音色、场景和事件。build.py 按它把配音卡到拍点上，画面和声音共用 build.py 算出的时间表。

## 顶层字段

```json
{
  "title": "Do You Like Carrots?",      // 片头大标题（英文）
  "title_zh": "你喜欢胡萝卜吗？",          // 片头中文副标题
  "grammar": "doyoulike",               // 本集画面文件 代码工程/clips/<grammar>.js
  "style": "flat",                      // flat / crayon / paper / clay / watercolor
  "music": "ukulele",                   // ukulele / musicbox / march / chiptune / none
  "bpm": 100,                           // 节拍。90–110 合适，太快孩子跟不上
  "owl": true,                          // 猫头鹰老师：老师说话时从右下角探出来（默认 true，false 整集不出现）
  "auto_sfx": true,                     // 自动加通用音效（默认 true）
  "pan": {"rabbit": -0.2},              // 可选：覆盖某个角色的声像（-1 左 … 1 右）
  "voices": { "bobo": {"id": "<Fish reference_id>", "name": "…", "speed": 1.0}, … },
  "scenes": [ {"id": "intro", "events": [ … ]}, … ]
}
```

示范集的台本写的是 `"owl": false`（画面和加猫头鹰之前逐像素一样）；new_episode.py 建别的集时删掉这一行，猫头鹰默认出现。

new_episode.py 只改开头的 style / music / grammar / title / title_zh 几行，保留每个事件一行的排版。手改时也保持这个排版，方便看。

## 音色

| 角色 | 音色 | speed |
|---|---|---|
| bobo（主角，橙色圆毛球） | Energetic Child `4fcb3a423c61415fb35604eba567d95f` | 1.0 |
| rabbit 粉兔子 | Cute child! `88aef4a31fd94aaa874c32252245b43f` | 1.0 |
| fish 蓝鱼 | Child (inquisitive boy) `0c0f9d7d87e44e2dabb53ebb092f5f53` | 1.05 |
| bird 黄色小鸟 | Child (cheerful girl) `4e407b98cb034f74b3863ec33c567c83` | 1.1 |
| teacher 老师（画面上是猫头鹰老师） | Teacher `73b5c16a6e504d6a97868581ada2b8d3` | 0.95 |
| panda 熊猫（慢悠悠的男孩） | boy `4fbed27c40e3465f98bc777fd0cc35ff` | 0.95 |
| elephant 大象（最低沉，憨厚） | boy (low) `d9ce1833c191476db346efb50aa20722` | 0.95 |
| frog 青蛙（最尖细） | Kid `b9011feb3c6f46ddaeb90043fab0eb4a` | 1.05 |
| penguin 企鹅（奶声奶气） | Baby `051eccd6d8894155a0c544b8e5c0fd72` | 1.05 |
| monkey 小猴（调皮，音高起伏大） | Child voice boy `829184c635314c9485e48690116ff8ad` | 1.1 |
| dino 小恐龙（女孩） | Girl `ee2fa25a56364be9a80d0028eecc6ea4` | 1.0 |

新角色的音色按音高和主角拉开：四个主角的基频中位数在 300–383 Hz，大象 140、熊猫 209、小恐龙 264 偏低，小猴、企鹅、青蛙在 387–408 偏高但语气不同（小猴起伏大、企鹅奶、青蛙尖）。同一场里尽量让高低搭配，别把三个高音放一起。

template/script.json 已经带上全部 11 个音色。台本里说话的角色在 voices 里没有，tts.py 和 build.py 直接报错，并写出该加的那一项（上表里的角色给推荐音色）。

再加别的角色：在 voices 里加一项（Fish 公共音色库挑一个，和已有的听得出区别），画面里要有对应的 `<名>_m0/m1/m2` 帧；声像不写就在正中（`pan` 可以覆盖）。

## 场景

`{"id": "carrots", "animal": "rabbit", "round": "guess", "bg": "beach", "trans": "map", "events": [...]}`。id 是画面文件里 `SC.<id>` 的名字；其余都可选，`events` 以外的字段原样进 spec，画面代码用 `sc.round`、`sc.bg`、`sc.trans` 读。场景开始和结束都对齐到拍点。

- `round`：这一轮的玩法，见 scene-cookbook.md「玩法」。
- `bg`：场景名 `meadow` 草地 / `beach` 海边 / `snow` 雪地 / `night` 夜晚 / `forest` 森林 / `kitchen` 厨房 / `bedroom` 卧室 / `playground` 游乐场 / `underwater` 海底（见 scene-cookbook.md「场景」）。玩法场景不给 `cfg.bg` 时自动用它，地图转场的站点也按它排。
- `trans`：进入这一场时的转场，`circle`（默认，彩色圆盖住、再开洞，颜色在画面文件的 `WIPE` 里配）/ `map` 地图 / `train` 小火车 / `slide` 滑梯 / `bubbles` 泡泡 / `door` 开门 / `page` 翻页（见 scene-cookbook.md「转场」）。`map` 和 `train` 要求这一场第一个事件是 `{"act": "travel", "beats": 4}`，否则画面报错。

## 事件

每个事件按顺序排在时间轴上。

| 事件 | 写法 | 含义 |
|---|---|---|
| 台词 | `{"who": "bobo", "say": "Do you like carrots?", "zh": "你喜欢胡萝卜吗？"}` | 上一句结束后至少隔 0.15 秒，顺延到下一个拍点开口。画面上单人台词出对话气泡，多人（who 是列表）出顶部横幅 |
| 齐声 | `"who": ["rabbit", "bobo"]` | 每个角色各合成一条，错开 25 毫秒叠在一起，像一群人在说 |
| 领念 | `"chant": 3, "every": 2` | 同一个词念 3 遍，每遍隔 2 拍（每遍单独一条 take，语气各不同）。画面上一个词一个词蹦出来排成一行 |
| 单词卡 | `"card": {"en": "carrots", "zh": "胡萝卜"}` | 一般给老师那句。卡片弹出（有物品图就带图），领念开始时缩到左上角 |
| 空拍 | `{"rest": 2}` | 停 2 拍（从下一个拍点算） |
| 等孩子答 | `{"rest": 3, "wait": true}` | 跟读题里的空白，每拍一声 tick，画面出"轮到你说！"和节拍点 |
| 等孩子做 | `{"rest": 4, "wait": "do"}` | wait 的种类：`say`（= true，轮到你说！）、`do`（站起来，一起做！）、`point`（用手指一指！）、`guess`（猜猜是什么？，配鼓点不配 tick）、`pick`（选一个！）、`freeze`（定住！不许动！，没有 tick）。写错种类 build.py 会报错 |
| 音乐停 | 任意台词、空拍、动作段加 `"music": "stop"` | 这段时间伴奏静音（前后 60 毫秒淡出淡入），相隔不到 1 拍的连成一段。木头人：喊 "Freeze!" 那句和后面的 freeze 空拍都加 |
| 跟读题 | `"quiz": "carrots"` / `"answer": "carrots"` | 老师问（quiz）→ wait → Bobo 答（answer）。答案显示绿色对勾、配 ding；以 No 开头的显示红叉、配 nope。故意答错但不是 No 开头的（问青蛙答 It's a panda!）在答案上写 `"good": false`，反过来也可以写 `"good": true` 强制算对 |
| 动作段 | `{"act": "try", "beats": 6}` | 没有台词、只有动作的几拍（尝一口、找东西、跳过去）。画面代码用 `K.actOf(sc.id, 'try')` 拿起止时间 |
| 旅程 | `{"act": "travel", "beats": 4, "sfx": [{"name": "boing", "beat": 0}, …]}` | 放在场景最前面，给地图、小火车转场的时间（地图：落下、Bobo 跳 3 下到下一站、收起；小火车：整段开过去）。滑梯、泡泡、开门、翻页写了它就盖着等到段尾再揭开 |
| 音效 | 台词：`"sfx": [{"name": "crunch", "at": "end", "offset": -0.05, "gain": -5}]`；动作：`"sfx": [{"name": "crunch", "beat": 2, "gain": -3}]` | 台词的 at 是 start / end（领念每遍都加）；动作的 beat 是从动作开始数第几拍（可以是小数）。gain 单位 dB |

自动音效（auto_sfx）：换场音效跟着转场走（泡泡 pop、滑梯 slide_down、翻页 pageflip、小火车 choo，其余 whoosh）、单词卡 sparkle、跟读题 pop、空拍 tick（guess 空拍换成一个 drumroll，freeze 空拍不加）、答案 ding / nope。

## 音效清单（sfx.py，全部代码合成）

boing 弹跳、splash 水花、flutter 翅膀扑腾、flap 拍翅、whoosh 转场、sparkle 闪光、twinkle 叮铃、ding 答对、nope 答错、pop 冒出、tick 节拍、step 脚步、thud 落地、giggle 咯咯笑、slide_up 上滑、slide_down 下滑、crunch 咬脆的、crisp 咬苹果、munch 软嚼、yuck 嫌弃、gulp 咽下、wow 惊喜、drumroll 鼓点滚奏（猜猜看，1.7 秒）、tada 揭晓、clap 拍手、freeze 玩具停摆（木头人定住）、magnify 放大镜找到、poof 变烟、choo 小火车汽笛、pageflip 翻页。

要新音效：在 sfx.py 里写一个函数、登记到表里，重跑 `sfx.py`。

## 内容设计经验

- **一集一个句型**，问答各一句，全集重复十几遍。单词 4 个左右，都是能画出来的具体东西或动作。
- **每轮的固定节奏**：问两遍 → 答两遍 → 老师念单词（单词卡）→ 动物领念 3 遍 → 动物和 Bobo 齐念 3 遍。孩子听到第二轮就知道接下来干什么。
- **反转**：让 Bobo 先说 No，再被说服说 Yes，练否定回答，也是全片的笑点。动作段 `act` 加音效（咬、嚼、咽、哇）。
- **跟读**：5 题左右，每题 3 拍空白。最后一题问个荒唐的（Do you like socks?），答案是 No。
- **领念的词尾**：吃东西的场景，咬的那一下放在"这句结束前 0.05 秒"（`"at": "end", "offset": -0.05`），画面里同一个公式算咬的时刻，咔嚓声不会盖住单词开头的辅音。
- **台词别用单独的感叹词开头**：Fish 会把 "Mmm!" 读成 "Hmm"，换成 "Yummy!" 这种真单词。
- **中文**：每句都给 zh，气泡里英文大字、中文小字。中文是给家长看的，口语、短。
- 片长不超过 3 分钟（片头约 9 秒，标准问答一轮约 20 秒，其他玩法一轮 10–25 秒，木头人约 24 秒，反转约 24 秒，跟读约 40 秒，片尾约 7 秒）。
