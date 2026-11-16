# 画面：clips/<grammar>.js 和画面库 K

渲染器是 `代码工程/clip.html`：浏览器里一个 1920×1080 的 Canvas，render.py 用 Playwright 逐帧调 `renderFrame(t)` 截图。每集一个画面文件 `clips/<grammar>.js`，通用部分在 `lib/kids.js`（全局对象 `K`）。时间全部来自 build.py 算好的 spec（`K.LINES` 等），画面代码不写死秒数。

## 文件骨架

```js
CLIPS.whereis = (() => {
const { clamp, lerp, ss } = U;                    // ss(a, b, t) 是 smoothstep
const VOCAB = { cat: { img: 'pet_cat', zh: '小猫', col: '#F28C28' }, … };   // 单词 → 物品图、中文、颜色
const COL = { bobo: '#FF7A1A', rabbit: '#EE4F96', fish: '#2F7BFF', bird: '#E3A100', teacher: '#7A4CFF' };   // 气泡边框色
const SCALE = { bobo: 0.95, rabbit: 0.95, fish: 0.9, bird: 0.78 };          // 角色画多大
const WIPE = { round1: '#FF9F43', quiz: '#B48CFF', outro: '#6EC3F5' };       // 进入某场景的转场颜色
let GY;                                           // 地面线 y（935）
const SC = {};
SC.intro = (c, t, sc) => { … };                   // 每个 script.json 场景 id 一个函数
…
return {
  fonts: K.fonts,
  init(ctx) { K.init(ctx, { vocab: VOCAB, colors: COL, scale: SCALE, wipe: WIPE }); GY = K.GY; },
  draw(c, t) { K.frame(c, t, SC); },
};
})();
```

`K.frame` 负责：一拍二的时间取整、按 t 找当前场景、场景交界的转场、整画面收尾（纸纹、暗角）。场景函数 `SC.<id>(c, t, sc)` 里 `sc = {id, t0, t1}`。

## 最重要的规则：材质层

代码画的东西要放进 `K.layer(c, kind, g => { … })`，并且**只用 g 画**：

- kind：`'bg'` 背景，`'prop'` 角色前面的道具和水面，`'ui'` 气泡、卡片、文字（颗粒和抖动减弱，字看得清）。
- 非扁平画风下，g 是离屏画布：每次 `g.fill()` 自动加料（蜡笔描边、水彩积色、黏土鼓包、剪纸投影），画完整层加纹理，再带抖动滤镜贴回主画布。扁平画风下 g 就是 c，直接画。
- 角色用 `K.ch(c, …)` / `K.spr(c, …)` 画在**主画布 c** 上，夹在 bg 层和 prop 层之间。剪纸、黏土的角色投影只在主画布上加。
- 不想加料的填充（布上的印花、细碎小块）：`g.plain = true; …; g.plain = false;`。半透明（alpha < 0.55）的填充本来就不加料。
- 每个 K.layer 都有固定开销（非扁平画风每层约 20–40 ms），同类东西合进一层：所有气泡一层（`K.bubbles` 已经这样做），一堆道具一层。
- 颜色用调色板 `K.P.*`（sky grass grass2 hill water trunk leaf card cardTint drop ground blanket plate quizBg yes no stars confetti…），不要写死，换画风时颜色跟着变。物品、角色自己的颜色（VOCAB.col、COL）可以写死。
- 字体用 `K.EN`（英文）、`K.ZH`（中文粗）、`K.ZH2`（中文次级）、`K.INK`（正文色）、`K.SUB`（次要文字色），每种画风不同。写字用 `K.txt(g, s, x, y, size, K.EN, col, {stroke, sw, alpha, align})`，它会按画风补偿字号。

## 时间和节奏

| 函数 | 用途 |
|---|---|
| `K.linesOf(id)` | 该场景的所有台词 `{who: [..], text, zh, t0, t1, card?, quiz?, answer?, chant?, n?}` |
| `K.chantsOf(id)` | 领念的那些（每遍一条） |
| `K.wordsOf(id, who)` | 某个角色参与的领念开口时刻列表 |
| `K.actOf(id, 'try')` | 动作段 `{t0, t1}` |
| `K.BEAT` | 一拍的秒数（0.6） |
| `K.mouthAt(who, t)` | 当前口型 0/1/2 |
| `K.popIn(t, t0, d, s)` | 从 0 弹到 1（回弹缓动） |
| `K.bump(t, a, b, r)` | a 到 b 之间是 1，两头 r 秒平滑过渡 |
| `K.hopAt(t, times, H, air)` | 在这些时刻原地跳：`{st: 'crouch'|'air'|'land', h}` 或 null |
| `K.bob(t, k)` | 跟拍子颠：`{dy, sx, sy}`（K.ch 默认已经带） |
| `K.arcPos(p, a, b, h)` | 抛物线飞过去（物品飞进手里） |
| `MO.cubicInOut` `U.ease.out` 等 | 缓动 |

## 角色

```js
K.ch(c, 'rabbit', x, GY, t, { pose: 'rabbit_wave', phase: 0.1, lift: 0, still: false, flip: false, rot: 0, s: 0.95, shadow: true, bob: 1, sx: 1, sy: 1 });
```

- 不给 pose 就按配音口型换 `<who>_m0/m1/m2`，跟拍子颠。给 pose 时说话会轻微缩放（看得出在说）。
- `phase` 错开每个角色的颠的节奏；`lift` 离地高度（跳）；`still: true` 不颠（跳起来、吃东西时）；`shadow: false` 不画脚下的影子（鱼、站在树上的鸟）。
- 返回 `{w, h, top}`，top 是头顶 y，气泡挂在它上面。

新角色（`panda elephant frog penguin monkey dino`）用法一样，帧已经按和 Bobo 的比例缩放好，`s` 不用另调；`K.COL` 有它们的默认颜色，脚下影子宽度按体型配好（大象宽、青蛙窄）。当前画风缺某张帧时 `K.img` 报错，说清缺哪张、在哪个画风。

## 猫头鹰老师

`K.frame` 每帧自动调用 `K.owl(c, t)`，本集画面不用写。老师说话（`who` 里有 `teacher`，齐声也算）前 0.3 秒，猫头鹰从右下角弹上来（中心 x 1765，脚在画面下边外，缩放 0.72），嘴按老师的配音口型换 `owl_m0/m1/m2`，说完 0.5 秒后沉下去；两段老师台词隔不到 1.5 秒就不下去。它画在场景之上、换场圆之下，不跟镜头推拉；地图、小火车这类旅程转场期间不画。

- 它占右下角大约 x 1620–1910、y 850–1080，单词卡（缩到左上角）和领念行（下方中间）都碰不到。本集画面别把要看的东西放在这块。
- 玩法场景（台本写了 `round`）里老师单独说、不是单词卡 / 跟读题 / 领念的句子（Jump like a frog!、Let's dance!、What's this?），猫头鹰出对话气泡（`K.owlLine(t)` 给出是哪一句）。气泡贴在它左边、和头一样高（右边沿在猫头鹰左边 20 像素，大约 y 830–1010），尾巴朝右指着它，所以站在右边的角色最多被挡到脚。别的场景里老师的话由本集画面自己显示（跟读的开场横幅、片尾）。
- `K.owlAt(t)` → `{p, pose, x, y, s, rot, box}` 或 `null`，`box` 是它当前占的矩形 `{x0, x1, y0, y1}`，摆东西时可以用来避让。
- 台本 `"owl": false` 整集不出现。当前画风没有 `owl_m0` 时报错，说清缺哪张，或者让你写 `"owl": false`。

## 现成的部件

| 部件 | 写法 | 说明 |
|---|---|---|
| 草地 | `K.meadow(g, t, {scroll, sky})` | 天空、云、两层远山、草坪、小花。scroll 让场景往左滚（跑步） |
| 池塘 | `K.pond(g, x0, top, t, false)` + 前景层 `K.pond(g, x0, top, t, true)` | 后者是半透明水面，盖在鱼前面 |
| 水面高度 | `K.surf(x, t, top)` | 让鱼跟着水波上下 |
| 树 | `K.tree(g, x, top)` | 树冠 + 横枝（鸟可以站） |
| 野餐布 | `K.blanket(g, cx, w, {open, top, bot, nx, ny})` | 近大远小的格子布，open 0→1 铺开 |
| 盘子 | `K.plate(g, x, y, r)` | |
| 彩纸屑 | `K.confetti(g, t, n)` | 片头片尾的背景 |
| 圆点底 | `K.dots(g)` | 跟读环节的底 |
| 物品 | `K.item(g, key, x, y, size, {rot, ay, flip})` | key 是 VOCAB 里的词（用它的 img）或素材名；size 是长边 |
| 星星、爱心 | `K.sparks(g, t, t0, x, y)`、`K.starBurst(g, t, t0, x, y)`、`K.hearts(g, t, t0, t1, x, y)` | 出现、答对、眼睛一亮、好吃 |
| 气泡 | `K.bubble(c, en, zh, cx, cy, tailX, tailY, p, col)` | 自己进 ui 层，在主画布上调。尾巴点在气泡右边时从右边沿伸出去，否则从底边；`K.bubbleW(c, en, zh)` 是它的宽度 |
| 横幅 | `K.banner(c, en, zh, cy, p, col, size)`、`K.chorusBanner(c, t, sc, cy)` | 齐声台词自动出横幅 |
| 单词卡 | `K.wordCard(c, t, sc, {x})` | 老师念 card 那句时弹出，领念开始缩到左上角；有 VOCAB.img 就带图 |
| 领念行 | `K.chantRow(c, t, sc, col)` | 一个词一个词蹦出来排成一行 |
| 片头标题 | `K.title(c, t, up, {y0, y1, start, zhAt})` | 字母一个个掉下来；up 0→1 把标题挪到上方变小 |
| 跟读环节 | `K.quiz(c, t, sc, {pic(c, t, key), react(answer) → K.ch 参数, host, good(answer) → bool, split(q) → [第一行, 第二行]})` | 左边大图卡（自己画）、右边问题、空拍、答案、右下角陪答角色。答案默认 Yes 开头绿勾、否则红叉；Where is…? 这类答案不是 Yes/No 的句型传 `good: () => true`；问句默认把最后一个词单独放第二行，不合适时（What color is it?）传 `split` 自己拆 |

## 问答场景骨架 `K.qaScene`

一轮问答的标准画法：背景（bg 层）→ 角色（主画布）→ 前景（prop 层）→ 单人台词气泡，都在镜头里；单词卡、领念行在镜头外。动物单独说话时镜头自动稍微推近、偏向它。

```js
SC.round1 = (c, t, sc) => K.qaScene(c, t, sc, 'rabbit',
  (g, t) => { K.meadow(g, t); K.blanket(g, 960, 1560); },           // 背景
  t => ({
    order: ['bobo', 'rabbit'],                                        // 画的先后
    bobo: { x: 600, y: GY },
    rabbit: { x: 1340, y: GY, phase: 0.1, pose: … },                 // K.ch 的参数；或 {draw: () => ({top}), x}
    front: g => { K.plate(g, 960, GY + 86, 115); … },                // 前景道具
  }),
  null,                                                               // 镜头：null 用默认，或 {z, x, y}
  { cardX: 790 });                                                    // 单词卡弹出的位置，别挡住角色
```

示范集的 `foodRound(c, t, sc, cfg)` 在这个骨架上加了：Bobo 问的时候盘子里的食物一蹦一蹦、老师念单词时食物飞进动物手里、领念时举着念—咬—嚼、碎屑、动物答 Yes 时蹦一下。新句型照这个思路写一个 `xxxRound`，三四个场景只是参数不同。

## 镜头和站位（`lib/kids_stage.js`）

**安静时段。** `K.calm(t)`：单词卡和领念期间为 1（每个场景从第一句 card / chant 前 0.3 秒到最后一句 chant 后 0.3 秒），其余为 0。这段时间镜头不动、背景放慢、不进新东西。背景里的云、浪、雪花、气泡用 `K.ambT(t)` 代替 `t`，安静时段里自动降到 0.3 倍速。

**自动分镜。** `K.shots(sc, L, focus, host = 'bobo')` 按台词排镜头，`K.camAt(t, shots, ww)` 取当前镜头，交给 `K.withCam`：

| 台词 | 镜头 |
|---|---|
| host 单说 | 中景 1.25 倍，host 和 focus 一起（两人隔得太远、中景框不下时用全景） |
| 别的角色单说 | 近景 1.5 倍（上限，角色帧原图约 430 像素高，再大就糊） |
| 老师念 card、齐声、等孩子、动作段 | 全景 |
| 领念 | 中景，镜头不动 |

镜头至少 2 拍、起点在拍点上；更紧且对象都在上一个镜头里就缓推 0.5 秒，否则硬切；落在安静时段里一律硬切。推近时镜头中心会往上收，保证说话气泡顶边留在画面里（角色站得高、个子大时自动生效）。`K.qaScene(…, 'auto', …)` 和 `K.round` 默认用它。

手写镜头：`{t0, t1, kind: 'wide'|'medium'|'close', z, x, y, ease}`，另有横摇 `{kind: 'pan', t0, t1, x0, x1, z, y}`（宽场景，`K.camAt` 的 `ww` 给世界宽度）和跟拍 `{kind: 'follow', t0, t1, z, y, x: t => …}`。`K.withCam(c, {z, x, y, ww})` 的 `ww` 让镜头能移到 1920 以外。

**站位。** 不要站成一排：

- `K.row(0|1|2)` → `{y, s}`：后排 `{820, 0.8}`、中排 `{900, 0.92}`、前排 `{980, 1.05}`。s 乘到 `K.SCALE[who]` 上。
- `K.formation(kind, whos)` → `{who: {x, y, s}}`：`'faceoff'` 面对面（620 / 1300 前排）、`'triangle'`（后排中间一个、前排左右两个）、`'high'`（第一个站在 1400, 560 的高处，支撑物自己画）、`'path'`（沿小路往远处排）。
- `L` 不写 `order` 时按 y 从小到大画（`K.byDepth(L)`），后排先画。
- `K.leanFor(who, t, sc, L, focus)`：说话时朝对方倾 0.06，听的人朝说话的人倾 0.03。现有帧都是正面，转向靠倾斜，不水平翻转。`K.round` 自动加。

## 程序动作和出场（`lib/kids_stage.js`）

不用新图的动作，都返回 `{dx, dy, rot, sx, sy}`，传给 `K.ch(…, {move})`，多个用 `K.mvAdd(a, b, …)` 叠加（位移、旋转相加，缩放相乘）。窗口外返回单位值，可以一直调。

| 函数 | 动作 |
|---|---|
| `K.mv.squash(t, t0, H = 160, air = 0.5)` | 在 t0 起跳：蹲下压扁 → 空中拉长 → 落地压扁回弹 |
| `K.mv.tilt(t, t0, t1, a = 0.12)` | 歪头（绕脚底转） |
| `K.mv.spin(t, t0, d = 0.6)` | 原地转一圈 |
| `K.mv.shake(t, t0, t1, amp = 10)` | 发抖 |
| `K.mv.tiptoe(t, t0, t1)` | 踮脚小碎步 |
| `K.mv.wiggle(t, t0, t1)` | 跟拍子扭，每拍换一边 |
| `K.mv.lean(t, t0, t1, dir, a = 0.06)` | 往一边倾 |
| `K.mv.doubleTake(t, t0)` | 回头看两次 |
| `K.dust(g, t, t0, x, y)` | 落地扬尘（在 prop 层画） |

出场 `K.enter(kind, t, t0, d, to, o)` 返回相对最终位置 `to` 的偏移（多一个 alpha），`t ≥ t0 + d` 后是单位值：

- `'run'`：从 `o.from`（'left' / 'right'，默认近的一边）画外跑进来，边跑边颠。
- `'pop'`：从地面下 250 像素弹上来。下半身要被前景（草丛、洞口、水面）挡住，前景放 prop 层。
- `'drop'`：从画面上方掉下来，落地压扁。挂气球、降落伞自己在头顶画。
- `'slide'`：沿斜线滑进来（`o.slope` 默认 0.4），滑梯、雪橇。
- `'peek'`：先在 `o.behind.dx`（默认 160）处探头两次，再走出来。遮挡物自己画。

退场 `K.exit(kind, t, t0, d, from, o)` 是出场倒放。

## 玩法（`lib/kids_rounds.js`）

每轮不再只是"问答 + 领念"，换着用下面 8 种。都是 `K.rounds.<种类>(c, t, sc, cfg)`，场景函数里直接返回它。最小用例见 `tests/fixtures/rounds.js`（每种一个场景），台本里对应的 act / wait 见 `tests/test_rounds.py`。

**骨架 `K.round(c, t, sc, cfg)`。** 字幕：单人台词出对话气泡；多人齐说（不含老师）出顶部横幅；领念那一排念完后，场景里还有别的台词就在那句开口前收掉（`K.chantAlpha(t, sc)`），不会和后面的提示叠在一起；老师的口令由猫头鹰的对话气泡说（见「猫头鹰老师」）。镜头内：背景层（`cfg.bg(g, t, amb)`，`amb = K.ambT(t)`；不给 `cfg.bg` 就用台本里这一场的 `"bg"` 场景，见下面「场景」，两个都没有会报错；再画 `cfg.mid(g, t)`）→ 角色（`L.order` 或按 y；自动加 `K.leanFor`）→ `cfg.overlay(c, t, pos, L)` → prop 层（场景前景 + `cfg.front(g, t, pos, L)`）→ 气泡。镜头外：`cfg.hud(c, t)` → 单词卡 → 领念行 → 当前空拍的提示 `K.waitPrompt`（默认 (960, 300)，`cfg.promptAt: [x, y]` 改，`cfg.prompt: false` 不画）。

- `cfg.cast(t)` → `L = {who: {x, y, s, pose?, move?, still?, hidden?, draw?}}`，`s` 是相对 `K.SCALE[who]` 的缩放（`K.row`、`K.formation` 给的就是这个）。
- 镜头默认 `K.shots(sc, L, focus, host)`；`cfg.shots` 整套手写，`cfg.extraShots(L) → [镜头]` 在自动分镜里插几个（`K.insertShot`）。
- `cfg.jolt(t) → {dx, dy}`：画面抖（整场放大 0.8% 防露边）。

```js
SC.r2 = (c, t, sc) => K.rounds.qa(c, t, sc, { focus: 'rabbit',          // 背景用台本里的 "bg": "beach"
  cast: () => K.formation('faceoff', ['bobo', 'rabbit']) });
```

| 种类 | cfg | 台本里要有 | 画面 |
|---|---|---|---|
| `qa` | — | 普通问答 | 就是 `K.round` |
| `guess` | `item: {key, x, y, size}`，`hide: 'silhouette' \| 'bush' \| 'corner'`，可选 `become`（角色 id：揭晓后变成这个角色） | wait `guess` → act `reveal` → 答案 | 剪影（轻晃，头上一个问号）/ 藏在草丛后露一角 / 从画面右边探出一角；`reveal` 时物品弹一下、星星、近景推过去，剪影淡掉、草丛分开、探头的滑进来 |
| `doit` | `action: 'jump' \| 'spin' \| 'stomp' \| 'tiptoe' \| 'wiggle'`，可选 `airPose: {who: 帧名}` | 老师口令（可带 card）→ wait `do` | 口令那句和空拍里全员每拍做一次（spin 每 2 拍一圈）；jump、stomp 落地扬尘，stomp 画面抖 4 像素。提示默认 (960, 240) |
| `find` | `items: [{key, x, y, size}]`，`target` 下标 | 问 Where is…? → wait `point` → act `found` | `found` 前 60% 放大镜从中间扫到目标（镜片里放大），之后目标外光环跟拍跳、其他变淡、近景推过去；说话的角色换 `_point` 帧（没有就 `_cheer`）指过去 |
| `pick` | `left`、`right`（VOCAB 词），`correct: 'left' \| 'right'` | 问 A or B? → wait `pick` → act `pick` | 两个台子在 x 640、1280；空拍里两边跟着提示箭头轮流跳；`pick` 时对的跳一下、星星、绿色对勾，错的抖一抖缩没冒烟 |
| `count` | `items: [{key}]`，可选 `x / y / size / gap` | 台词以 one…ten 开头（`K.countLines(sc)` 认） | 每数一句弹出一个物品带数字角标，上方大字是这一句，全员跟着跳 |
| `missing` | `items: [{key}]`，`gone` 下标，可选 `x / y / size / gap` | Close your eyes! → act `dark` → wait `guess` → act `reveal` | 野餐布上一排；`dark` 画面暗到 0.85、出现闭眼图标和"闭上眼睛！"，角色有 `<who>_cover1` 帧就捂眼（没有就抖）；最暗时拿走，空位出虚线圈和问号；`reveal` 弹回来冒星星 |
| `freeze` | `poses: {who: 帧名}`，`wobbler`，可选 `wobbleOn`（第几个 freeze 空拍，默认最后一个）、`fallDir`（1 右 / -1 左） | act `dance` → 老师 Freeze! → wait `freeze`（可以来两遍） | 跳舞时全员扭 + 跟拍跳、飘音符；从 Freeze! 开口起定住（换 `poses` 帧、各自歪一个角度、画面微微发蓝）；`wobbler` 在空拍最后 40% 越晃越大、最后倒向一边，镜头最后 2 拍推近它；倒下的状态保持到下一段 `dance` |

辅助：`K.revealP(t, sc, act = 'reveal')` → 0..1（动作段开始前 0，开始后 0.3 秒到 1，没有这个动作段就是 1）；`K.insertShot(S, s)` 插手写镜头（切剩不足 2 拍的碎片并进插入的镜头）；`K.poof(g, t, t0, x, y, r)` 一团烟。

注意：

- 猜猜看猜动物：`item.key` 用那个动物的 `_m0` 帧（或 VOCAB 里 img 是它的词），给 `become: 'penguin'`。揭晓弹完（reveal 开始后 0.5 秒）物品换成角色本身，同一位置同样大小，之后能说话、领念；揭晓前它在 cast 里是 hidden。cast 里可以给它别的参数（pose、phase），x、y、s 由 item 决定。
- 跟我做的口令：老师说的、后面没有同一句领念的话（单词卡 + 领念是教单词，那几拍不跳）。所以一个跟我做场景里可以先问答、念单词卡、领念，再喊口令。
- 跟我做的 `airPose`：跳起来离地时换成这一帧（`frog_jump`、`rabbit_jump`、`fish_leap`），落地换回口型帧。
- 每种玩法会改 `cast` 返回的角色（加动作、换帧），`cfg.cast` 只管站位，返回新对象即可（会被拷一份）。
- `cfg.mid`、`cfg.front`、`cfg.hud` 照样可以传，玩法自己的东西画完再调你的。
- 单词卡后面没有领念（跟我做的口令卡）时，卡片在老师念完 0.3 秒后缩到左上角，不会挡提示。

## 场景（`lib/kids_scenes.js`）

9 个代码画的场景，每集挑着用，台本里每场写 `"bg": "<场景名>"`。`K.round` 没给 `cfg.bg` 时自动画这个场景的背景和前景（前景盖在角色前面），深色场景的参与提示字后面自动垫一块浅色底。所有颜色从 `K.P` 取，五种画风都能用。对比图：`python3 scripts/preview_styles.py --out <目录> --places --sheet`（行是场景、列是画风）。

| 场景名 | 中文 / 英文 | 前景（角色前面） | 特别位置（第 4 个 spot） |
|---|---|---|---|
| `meadow` | 草地 / Meadow | 无 | `branch` 树枝（1560, 572），小鸟站 |
| `beach` | 海边 / Beach | 贝壳、海星 | `rock` 礁石（1520, 772） |
| `snow` | 雪地 / Snow | 两堆雪 | `hill` 雪坡（330, 772）；雪人在 1830 |
| `night` | 夜晚 / Night（深色） | 两丛草 | `hill` 山坡（300, 774）；萤火虫 |
| `forest` | 森林 / Forest | 两丛蕨叶 | `log` 倒下的木头（1560, 784） |
| `kitchen` | 厨房 / Kitchen | 右下角桌子和杯子 | `counter` 灶台（300, 604）；冰箱在 1700 附近，别让角色站进去 |
| `bedroom` | 卧室 / Bedroom | 左下角 ABC 积木 | `bed` 床上（1560, 704） |
| `playground` | 游乐场 / Playground | 两段白栅栏 | `slide` 滑梯平台（270, 524） |
| `underwater` | 海底 / Under the sea（深色） | 两块礁石、海星 | `rock` 礁石（1540, 772）；鱼群、光柱、气泡 |

每个场景都有 `left`、`right`（前排，y 980）、`back`（后排，y 830 左右）三个站位，加上表里的特别位置。

- `K.place(名)` → `{zh, en, dark, frontTop, spots, bg, front, icon}`，名字写错报错并列出可选的；`K.PLACES` 是全部。
- `K.spot(名, 位置)` → `{x, y, s}`，直接放进 `cast`：`bird: K.spot('forest', 'log')`。
- `P.bg(g, t, amb, cam, ww)`、`P.front(g, t, amb, cam, ww)` 在 `K.withCam` 里调；`cam` 就是当前镜头（`K.round` 里自动传）。宽场景 `ww` 可以大于 1920（比如 2880 横摇），场景自己铺满。
- 视差：远景（天、远山、远处的树）比近景动得慢，镜头一摇就看得出远近，不多开图层。
- `P.icon(g, x, y, r)`：地图转场站点上的小图标。
- 海鸥、鱼群、蝴蝶、气球这种会从画面穿过的小东西，单词卡、领念时段自动淡出（`K.lively(t)`），不抢孩子的注意。

自己写场景（不走 `K.round`）的骨架（海边、世界宽 2880、地图揭开后镜头从右摇到左）：

```js
const P = K.place('beach'), amb = K.ambT(t), cam = { x: 1920, y: 540, z: 1, ww: 2880 };
K.withCam(c, cam, () => {
  K.layer(c, 'bg', g => P.bg(g, t, amb, cam, 2880));
  K.ch(c, 'bobo', 420, K.GY, t, {});                                        // 角色直接画在主画布上
  K.layer(c, 'prop', g => P.front(g, t, amb, cam, 2880), { top: P.frontTop });   // 只画前景时带 top，省时间
});
```

`K.layer(c, kind, fn, { top })`：`fn` 只画在世界坐标 y ≥ top 的地方时，蜡笔、剪纸这类画风只处理画面底部一条（每层省 30–50 毫秒）；画到 top 以上的会被裁掉。场景前景都标了 `frontTop`，前景和别的东西画在同一层时不要带 top。

加新场景：照现有的写一个 `PLACES.<名>`。约定：

1. 按屏幕坐标画：近景（地面、能站人的东西）写 `x - sx`，远景写 `x - sx * k`（k 越小越远），重复的东西用 `rep(sx, k, 间距, fn)` 铺，任何镜头位置都铺满。
2. 颜色只用 `K.P`（新颜色加进 `kids.js` 的 `BASE_PAL`，五个画风有需要再各自覆盖）；`tests/test_static.py` 会查颜色字面量。
3. 前景只画在 `frontTop` 以下；没有前景就 `frontTop: null`。`places.test.js` 会查。
4. 一团圆（树冠、云、灌木）用 `blob(g, [[x, y, r], …], 颜色)`：蜡笔下只描外缘，水彩、黏土下逐个圆填（一条路径会描出每个圆的整圈）。
5. 写完跑 `preview_styles.py --places --sheet` 看五个画风，`--profile` 看每帧耗时（要 ≤ 300 毫秒）。

## 转场（`lib/kids_trans.js`）

台本里场景写 `"trans": "<种类>"`：进入这一场时用哪种转场。不写就是原来的彩色圆圈。一集用一种当主线（推荐地图），中间穿插一两种别的。

| 种类 | 画面 | 要 travel 段 | 换场音效（自动） |
|---|---|---|---|
| `circle` | 彩色圆盖住、再开洞（颜色在 `WIPE` 里配） | 不要 | whoosh |
| `map` | 地图从上面落下来盖住：一排站点（家 + 每个场景的小图标），走过的路是实线；Bobo 每拍跳一下跳到下一站，落地冒星星，地图再收上去 | 要 | whoosh；跳的声音写在 travel 段（见下） |
| `train` | 小火车从右往左开过去，车头烟囱处是分界：车后面已经换成新场景，前面还是上一场的最后一帧，烟柱盖住分界线 | 要 | choo（汽笛 + 嚓嚓，车开出来那一拍） |
| `slide` | 一条斜的大滑梯带从左上滑下来盖住，Bobo 坐着滑下去 | 不要 | slide_down |
| `bubbles` | 一屏大泡泡涌上来盖住，再一个个破掉 | 不要 | pop |
| `door` | 两扇门关上、再打开 | 不要 | whoosh |
| `page` | 一张横线纸翻过来盖住、再翻走 | 不要 | pageflip |

- `map`、`train` 要时间：这一场的第一个事件写 `{"act": "travel", "beats": 4}`，没有会报错（错误信息里给出写法）。地图在这 4 拍里：前 0.4 秒落下、Bobo 跳 3 下、最后 0.4 秒收起；小火车整 4 拍开过去。地图段的跳跃声写在 travel 段上：`"sfx": [{"name": "boing", "beat": 0}, {"name": "boing", "beat": 1}, {"name": "boing", "beat": 2}, {"name": "ding", "beat": 3}]`。
- 其他几种不写 travel 就是 0.4 秒盖住 + 0.5 秒揭开；写了 travel 就盖着等到 travel 段快结束再揭开。
- 地图站点 = 家 + 写了 `bg` 或用 `map` 转场的场景，按出场顺序；超过 5 站排成蛇形两行。
- 和旅程转场相邻的场景交界不再画圆圈（不会先闪一个圈）。
- 片头场景写 trans 没有"盖住"阶段（前面没有东西可盖）。
- 查询：`K.transAt(t)` → `{type, to, phase: 'cover' | 'hold' | 'reveal', p}` 或 null；`K.mapStations()`；`K.mapBobo(t)`。

## 示范集的结构（`clips/doyoulike.js`，230 行）

- `SC.intro`：彩纸屑背景，标题落下，Bobo 从下面弹上来挥手，说第二句时换成抱篮子、野餐布铺开。
- `SC.carrots / bananas / apples`：`foodRound`，每个场景只配动物位置、食物从哪来（盘子 / 树上）、背景（草地 / 池塘 / 苹果树）。
- `SC.twist`：Bobo 的表情随台词和动作段切换（嫌弃 → 端详 → 咬 → 嚼 → 眼睛一亮 → 好吃），动物们探身子劝、最后欢呼；动作段镜头推近 Bobo。
- `SC.quiz`：`K.quiz` + 左边一张"桌布上盘子里的食物"大图卡 + 右下角 Bobo 按答案捧脸或嫌弃。
- `SC.outro`：全员从下面弹上来，前面一排食物跟着拍子跳，Bye-bye 横幅。

## 画风参数（`lib/kids.js` 的 `THEMES`）

```js
crayon: {
  label, en: 'GochiHand-400', zh: 'LXGWWenKai-500', zh2, enK: 1.12,   // 字体和英文字号补偿
  ink, sub, paper,                                                      // 文字色、底色
  pal: { … },                                                           // 覆盖 BASE_PAL 的颜色
  mat: { outline: {w, dark}, tooth: {a, ui, rot}, grain, wobble: {amp, freq, boil, ui} },
  step: 2,                                                              // 一拍二
  post: { paper: 0.45, vignette: 0 },                                   // 整画面纸纹、暗角
}
```

| mat 项 | 作用 | 用在 |
|---|---|---|
| `outline {w, dark}` | 每块填充外缘一圈深色粗线 | 蜡笔 |
| `tooth {a, ui, rot}` | 纸纹白点（颜色没涂到的地方） | 蜡笔 |
| `grain` | 细颗粒 | 蜡笔、黏土 |
| `wobble {amp, freq, boil, ui}` | 位移滤镜抖动；boil 每秒换几次噪声（线条"沸腾"），0 静止 | 蜡笔、水彩 |
| `jag {amp, freq, ui}` | 高频小抖动：剪刀毛边 | 剪纸 |
| `shadow {col, blur, dx, dy}` | 每块投影 | 剪纸、黏土 |
| `fiber` | 纸纤维明暗细纹 | 剪纸 |
| `emboss {hi, lo, blur, off, w}` | 内侧左上亮、右下暗，鼓起来 | 黏土 |
| `pool {w, blur, dark, a}` | 边缘内侧积色 | 水彩 |
| `gran`、`bloom` | 颜料颗粒、大块浓淡 | 水彩 |
| `sprShadow`（和 mat 同级） | 角色投影 | 剪纸、黏土 |

调参数后用 `scripts/preview_styles.py --out <目录> --styles crayon --sheet` 渲几张对比。

## 抽帧和调试

- 抽帧：`render.py --spec spec.json --out <目录> --stills 2,10.5,15`。
- 浏览器里拖时间条：在 `代码工程/` 下起静态服务器打开 `clip.html?spec=spec.json`（spec 里的图片路径是相对 代码工程/ 的）。
- 报"缺素材 xxx"：`代码工程/assets/xxx.png` 不存在，或 build.py 之后才加的图（spec 只登记 build.py 时已有的图，加图后重跑 build.py）。
- 报"场景 xxx 没有画法"：script.json 有这个场景 id，画面文件里没写 `SC.xxx`。
