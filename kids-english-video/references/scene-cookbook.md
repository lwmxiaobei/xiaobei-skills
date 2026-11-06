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
| 气泡 | `K.bubble(c, en, zh, cx, cy, tailX, tailY, p, col)` | 自己进 ui 层，在主画布上调 |
| 横幅 | `K.banner(c, en, zh, cy, p, col, size)`、`K.chorusBanner(c, t, sc, cy)` | 齐声台词自动出横幅 |
| 单词卡 | `K.wordCard(c, t, sc, {x})` | 老师念 card 那句时弹出，领念开始缩到左上角；有 VOCAB.img 就带图 |
| 领念行 | `K.chantRow(c, t, sc, col)` | 一个词一个词蹦出来排成一行 |
| 片头标题 | `K.title(c, t, up, {y0, y1, start, zhAt})` | 字母一个个掉下来；up 0→1 把标题挪到上方变小 |
| 跟读环节 | `K.quiz(c, t, sc, {pic(c, t, key), react(answer) → K.ch 参数, host, good(answer) → bool})` | 左边大图卡（自己画）、右边问题、空拍、答案、右下角陪答角色。答案默认 Yes 开头绿勾、否则红叉；Where is…? 这类答案不是 Yes/No 的句型传 `good: () => true` |

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

## 示范集的结构（`clips/doyoulike.js`，230 行）

- `SC.intro`：彩纸屑背景，标题落下，Bobo 从下面弹上来挥手，说第二句时换成抱篮子、野餐布铺开。
- `SC.carrots / bananas / apples`：`foodRound`，每个场景只配动物位置、食物从哪来（盘子 / 树上）、背景（草地 / 池塘 / 苹果树）。
- `SC.twist`：Bobo 的表情随台词和动作段切换（嫌弃 → 端详 → 咬 → 嚼 → 眼睛一亮 → 好吃），动物们探身子劝、最后欢呼；动作段镜头推近 Bobo。
- `SC.quiz`：`K.quiz` + 左边一张"桌布上盘子里的食物"大图卡 + 右下角 Bobo 按答案捧脸或嫌弃。
- `SC.outro`：全员从下面弹上来，前面一排食物跟着拍子跳，Bye-bye 横幅。

第 1 集《Can You Hop?》（`../2026-11-03-can-you-hop/代码工程/clips/canyou.js`）是扁平风、还没抽出 K 之前写的，有跑步滚屏、跳、游、飞的动作写法，可以参考动作设计，代码要改成 K 的写法（放进 K.layer、用 K.P 颜色）才能用其他画风。

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
