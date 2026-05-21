# codex-image

一个 Claude / Codex **Skill**，让 AI 助手能够直接使用你的 **ChatGPT 订阅账号额度** 来生成或编辑图片，**无需 `OPENAI_API_KEY`**。

> 这是一个 **skill（技能）**，不是给你手工敲命令的 CLI 工具。你只需要在和 AI 助手对话时用自然语言提出需求，助手会自动判断、调用并完成任务。

> English version: [`README.md`](./README.md)

## 这是什么

`codex-image` 是给具备 Skill 能力的 AI 助手（如 Claude Code、Codex 等）安装的一个扩展。安装后，当你在对话中表达"生成图片 / 编辑图片"的意图，助手会：

1. 识别意图并自动激活本 skill
2. 复用本机已有的 `codex` 登录态（`~/.codex/auth.json`），没有时自动拉起一次浏览器 OAuth 登录
3. 通过 OpenAI Responses API 的 `image_generation` 托管工具生成 / 编辑图片
4. 把图片保存到本地并把路径返回给你

整个过程消耗的是你 **ChatGPT 订阅（Plus / Pro / Business）** 的使用额度，不走 API key 计费。

> ⚠️ 这是非官方 skill，使用前请阅读 [`LEGAL.md`](./LEGAL.md)。

## 安装

### 方式一：通过 `npx skills add`（推荐）

一行命令从 GitHub 仓库安装到本地 skill 目录：

```bash
npx skills add https://github.com/lwmxiaobei/xiaobei-skills
```

执行后会拉取仓库中的 skill 集合（含本 `codex-image`），并放到 AI 助手能识别的位置。重启 / 新开会话即可触发。

### 方式二：手动安装

把本目录放到 AI 助手识别 skill 的位置（以 Claude Code 为例，通常是 `~/.claude/skills/` 或项目级 `.claude/skills/`），助手启动时会自动加载 `SKILL.md`。

### 底层依赖

无论哪种方式安装，底层都依赖 Python 环境，建议先准备好：

```bash
uv pip install -e .
```

或者把 `scripts/` 目录加进 `PATH`。AI 助手在真正调用 skill 时会自动跑底层脚本，你平时不需要直接执行。

## 如何使用（用自然语言驱动）

不要去背命令，**直接和 AI 助手说话就行**。下面是一些典型触发用法。

### 1. 生成新图片

> 「帮我生成一张小熊猫吃竹子的图，保存到 `panda.png`」
>
> 「Generate an image of a cyberpunk cat sitting on a neon-lit rooftop」
>
> 「用 gpt-image 给我画一张极简风格的山水画」

助手识别到生成意图后，会激活本 skill 并把图片产出到你指定的路径（或默认输出目录）。

### 2. 编辑 / 改图（基于参考图）

> 「把这张照片改成夜景效果」（附带 `photo.jpg`）
>
> 「以 `ref1.png` 和 `ref2.png` 为参考，融合成一张新海报」
>
> 「Edit this image to make the background snowy」

只要你给出参考图路径并描述修改意图，助手会调用 skill 的 edit 流程。

### 3. 账号管理

> 「检查一下我的 codex 登录状态」
>
> 「我要重新登录 ChatGPT 账号」
>
> 「退出当前账号」

助手会通过 skill 的 login / logout / status 子命令完成相应操作。

## 触发条件（Skill 何时会被激活）

`SKILL.md` 已声明触发规则，AI 助手会基于此判断是否调用：

会触发：

- 你提到生成 / 编辑图片、画图、改图、出图
- 你点名 `codex-image` / "用我的 ChatGPT 额度"
- 你本机已有 `codex` 登录态，且需求是图片生成

不会触发：

- 你明确希望走 `OPENAI_API_KEY`（请用通用 Images API skill）
- 你想用 Google / Gemini / Adobe 等其他厂商的图像模型
- 你只需要本地抠图 / 去背景（用 `imagegen` skill）

## 输出位置

默认产出路径：

```
$CODEX_HOME/generated_images/codex-image/<UTC时间>-<slug>.<扩展名>
```

也可以在对话里指定文件名，例如「保存到 `~/Desktop/out.png`」，助手会把它作为 `--out` 传下去。

## 工作原理（简介）

Skill 底层会向 `https://api.openai.com/v1/responses` 发起请求，使用 `image_generation` 这个 hosted tool；HTTP 指纹与官方 `codex` CLI 完全对齐，从而能复用 ChatGPT 订阅鉴权。详细字节级规格见 [`references/fingerprint.md`](./references/fingerprint.md)。

## 进一步阅读

- [`SKILL.md`](./SKILL.md) — skill 元信息与触发说明（AI 助手实际读取的入口）
- [`references/cli.md`](./references/cli.md) — 底层脚本的完整参数（助手会自动用，无需手敲）
- [`references/prompting.md`](./references/prompting.md) — 写好图片提示词的方法
- [`references/fingerprint.md`](./references/fingerprint.md) — HTTP 指纹与官方 CLI 对齐细节
- [`LEGAL.md`](./LEGAL.md) — 法律声明与免责条款

## 目录结构

```
codex-image/
├── SKILL.md       # skill 元数据 + 触发指南（AI 助手读取入口）
├── scripts/       # Python 实现（助手自动调用）
├── references/    # 提示词 / CLI / 指纹文档
├── agents/        # 子代理定义
├── tests/         # pytest 单元测试
├── pyproject.toml
├── LEGAL.md
└── README.md
```
