# codex-image Skill — 设计文档

| | |
|---|---|
| 日期 | 2026-05-20 |
| 作者 | 北哥 + Claude（brainstorming 阶段） |
| 状态 | 待实现 |
| 下一步 | 移交 superpowers:writing-plans 生成实现计划 |

---

## 1. 目标

提供一个**通用 skill**（任何支持标准 skill 协议的 agent 都能加载），让用户在**不持有 OPENAI_API_KEY** 的前提下，用 **ChatGPT 账号订阅额度**调用 OpenAI Responses API 的 `image_generation` hosted tool 生成或编辑图片。

skill 通过**完美伪装成 codex CLI 客户端**完成请求——所有 HTTP 指纹（OAuth 客户端 ID、`originator`、`User-Agent`、请求体结构、SSE 事件解析）与 codex 一致。

### 1.1 必须满足的硬约束（北哥指定）

1. **完美伪装 codex 客户端**：OpenAI 后端无法从 HTTP 指纹层面区分该 skill 与官方 codex CLI 的请求。
2. **鉴权稳定**：优先复用 `$CODEX_HOME/auth.json`；缺失则脚本自动拉起 PKCE OAuth 浏览器授权流程；token 过期自动 refresh；refresh 失败兜底再次 OAuth。

### 1.2 非目标

- 不支持 `OPENAI_API_KEY` 模式（codex 源码 `spec_plan.rs:295-309` 显式禁用 API Key 模式访问 `image_generation` hosted tool；我们的 skill 完全跟随这个限制）。
- 不支持批量生成（`batch` 能力初版砍掉；YAGNI）。
- 不支持纯本地透明背景抠图（这是 `imagegen` skill 的能力，不重复）。
- 不内置 prompt 增强 schema（与 `imagegen` skill 的 `references/prompting.md` 兼容即可）。

---

## 2. 关键决策（已锁定）

| 决策项 | 选择 | 替代方案 | 理由 |
|---|---|---|---|
| 宿主环境 | 标准通用 skill | Claude Code 专用 / Codex 专用 | 一份代码服务所有 agent 平台 |
| 鉴权 | 优先 `auth.json`，缺失则 PKCE OAuth | shell out `codex login` / 仅依赖 codex | 用户原话"如果没有则脚本拉起授权" |
| API 端点 | `POST /v1/responses` + `image_generation` hosted tool | `/v1/images/generations` Images API | hosted tool 才能走 ChatGPT 额度；Images API 必须 API Key |
| 顶层 model | `gpt-5.5` | `gpt-5.1-codex` / 让服务端默认 | 北哥指定 |
| 工具层 model | **不传**（靠后端默认 = `gpt-image-2`） | 显式 `model: "gpt-image-2"` | 与 codex 默认请求体一字不差，伪装最大化 |
| 能力 | `generate` / `edit` / `login` / `logout` / `status` | 加 `batch` | 范围克制 |
| logout 语义 | 只清 `tokens` 字段，文件保留 | 整文件删 | codex 也能正确识别"未登录" |
| 401 重试 | 强制 refresh + 重试一次 | 多次重试 / 不重试 | 平衡稳定性与简洁性 |
| `edit` 输入图 | data URI 内嵌（>5MB 自动缩至长边 2048px） | files API 上传 | 减少 round trip，简化代码 |
| 实现语言 | Python | Node / Rust | 与现有 `imagegen` skill 一致，依赖少 |

---

## 3. 架构

### 3.1 目录布局

```
codex-image-skill/                          # skill 根目录（即将作为新 skill 发布）
├── SKILL.md                                # skill 元数据 + 调用指南
├── agents/openai.yaml                      # 平台清单
├── assets/
│   ├── codex-image.png                     # 大图标
│   └── codex-image-small.svg               # 小图标
├── scripts/
│   ├── codex_image.py                      # CLI 主入口（argparse 分发）
│   ├── auth.py                             # 鉴权：读 auth.json / refresh / OAuth 兜底
│   ├── responses_client.py                 # /v1/responses SSE 流式客户端
│   ├── http_client.py                      # 共享 requests Session（统一 header 指纹）
│   └── output.py                           # base64 解码 + 文件命名 + 落盘
├── references/
│   ├── prompting.md                        # 共享提示词指南（与 imagegen skill 对齐）
│   ├── cli.md                              # 子命令、参数、示例
│   └── fingerprint.md                      # codex 伪装指纹规范（开发者文档）
├── tests/
│   ├── test_auth.py
│   ├── test_responses_client.py
│   └── test_output.py
├── docs/superpowers/specs/                 # 本目录（本设计文档所在）
├── pyproject.toml                          # uv 管理的依赖
├── LEGAL.md                                # 非官方 skill 免责声明（见 §10）
└── README.md
```

### 3.2 SKILL.md frontmatter

```yaml
---
name: "codex-image"
description: "Generate or edit images via OpenAI's Responses API using ChatGPT account auth reused from Codex CLI's auth.json, with built-in PKCE OAuth fallback. Use when the user wants OpenAI's hosted image_generation without an OPENAI_API_KEY, leveraging their ChatGPT subscription quota. Provides generate, edit, login, logout, status."
---
```

---

## 4. 组件契约

### 4.1 `auth.py` — 鉴权层

```python
# Public API
def get_access_token() -> str: ...
def interactive_login() -> Credentials: ...
def refresh_tokens(refresh_token: str, *, force: bool = False) -> Credentials: ...
def status() -> dict: ...           # { email, plan, expires_at, account_id, source }
def logout() -> None: ...           # 只清 tokens 字段

# Internal
def _load_auth_json() -> dict | None: ...
def _write_auth_json(data: dict) -> None: ...   # mode 0o600
def _decode_jwt_exp(jwt: str) -> int: ...       # 不验签，仅解 exp
def _start_callback_server(port: int) -> CallbackServer: ...
```

**`get_access_token()` 流程**：

1. 读 `$CODEX_HOME/auth.json`（`$CODEX_HOME` 缺省 `~/.codex`）
2. 文件不存在 / JSON 损坏 → 备份后转 `interactive_login()`
3. 解析 `tokens.access_token` 的 JWT `exp`
4. 若 `exp < now + 5min` 且有 `refresh_token` → `refresh_tokens()`
5. refresh 失败 → `interactive_login()`
6. 返回 `access_token` 字符串

**`interactive_login()` 流程**：

1. 生成 PKCE pair：`code_verifier` (43 字节随机)、`code_challenge` (S256)、`state` (32 字节随机 base64url)
2. 启动 `http.server.HTTPServer` on `127.0.0.1:1455`，端口占用则降级 `1457`
3. 构造 authorize URL（见 §6.1），`webbrowser.open(url)`
4. 阻塞等待回调（默认超时 90s）
5. 校验回调 `state` 字段
6. POST `https://auth.openai.com/oauth/token` 换 access_token / refresh_token / id_token
7. 写回 `$CODEX_HOME/auth.json`（结构与 codex 完全一致，见 §6.4）
8. 返回 `Credentials`

### 4.2 `responses_client.py` — API 层

```python
@dataclass
class GenerateResult:
    image_b64: str
    revised_prompt: str | None
    call_id: str
    model: str          # 顶层 model 回显
    raw_events: list[dict]   # debug 用，可选关闭

def generate(
    prompt: str,
    *,
    access_token: str,
    input_images: list[Path] | None = None,
    output_format: str = "png",
    image_model: str | None = None,    # 不传则不加进 tool spec（默认伪装）
) -> GenerateResult: ...

class UnauthorizedError(Exception): ...
class RateLimitedError(Exception): ...
class ApiError(Exception): ...
```

**`generate()` 行为**：

1. 构造请求体（见 §5.1）
2. POST `https://api.openai.com/v1/responses` with `stream=True`，header 见 §6.2
3. 行级解析 SSE：识别 `event:` 和 `data:` 字段
4. 累积事件直到 `response.completed` 或 `response.failed`
5. 在 `response.output_item.done` 事件里找 `item.type == "image_generation_call"`，取 `item.result` (base64)
6. 401 → raise `UnauthorizedError`（CLI 层负责 refresh + 重试一次）
7. 429 → 读 `Retry-After`，最多内部重试 3 次（指数退避 2s/4s/8s）
8. 5xx → 同上指数退避重试 3 次
9. 不消化 `response.image_generation_call.partial_image` 事件（如有）——初版只关心最终结果

### 4.3 `http_client.py` — 共享 Session

提供 `make_session(*, with_auth: bool = True) -> requests.Session`，统一注入 §6.2 列出的所有"伪装 header"，让 `auth.py` 和 `responses_client.py` 都用同一份指纹。

### 4.4 `output.py` — 落盘

```python
def save(image_b64: str, out_path: Path | None, *, force: bool = False) -> Path: ...
def default_path(slug: str, ext: str) -> Path: ...
    # $CODEX_HOME/generated_images/codex-image/<UTC>-<slug>.<ext>
```

- 默认目录自动 `mkdir -p`
- `out_path` 父目录不存在 → 报错退出（避免误写）
- 同名文件 + 未传 `--force` → 追加 `-v2` / `-v3` ... 自动避让
- base64 decode → 写文件 → 返回**绝对路径**

### 4.5 `codex_image.py` — CLI 表层

```
codex-image generate "PROMPT" [--output-format png|webp|jpeg] [--out PATH] [--force]
                              [--image-model MODEL]   # 高级隐藏
codex-image edit --input REF.png [--input REF2.png ...] "PROMPT" [--out PATH] [--force]
codex-image login
codex-image logout
codex-image status
```

退出码约定：

| Code | 含义 |
|---|---|
| 0 | 成功 |
| 2 | 用户输入错误（缺参数、参考图不存在、size 非法等）|
| 3 | 文件系统错误（权限、磁盘满）|
| 4 | 权限或计划错误（API 403）|
| 5 | 网络或限流错误（重试耗尽）|
| 6 | 部分成功（SSE 流断开但有 partial）|
| 7 | API 业务错误（response.failed）|
| 130 | 用户 Ctrl+C |

---

## 5. 数据流

### 5.1 `generate` 请求体（与 codex 默认 image_gen 调用一字不差）

```json
{
  "model": "gpt-5.5",
  "input": [
    {
      "role": "user",
      "content": [
        {"type": "input_text", "text": "<用户 prompt>"}
      ]
    }
  ],
  "tools": [
    {"type": "image_generation", "output_format": "png"}
  ],
  "stream": true
}
```

注意：
- 顶层 `model = gpt-5.5`（北哥指定）
- `tools[0]` 不传 `model` 字段，靠后端默认走 `gpt-image-2`（与 codex 一致）
- 不传 `tool_choice`、不传 `instructions`、不传 `previous_response_id`、不传 `store`（codex 默认调用也不传）

### 5.2 `edit` 请求体（与 generate 的差异）

```json
{
  "model": "gpt-5.5",
  "input": [
    {
      "role": "user",
      "content": [
        {"type": "input_text",  "text": "<prompt>"},
        {"type": "input_image", "image_url": "data:image/png;base64,<...>"},
        {"type": "input_image", "image_url": "data:image/png;base64,<...>"}
      ]
    }
  ],
  "tools": [{"type": "image_generation", "output_format": "png"}],
  "stream": true
}
```

预处理：参考图 >5MB 自动用 PIL 缩到长边 2048px；缩完仍 >10MB 直接报错退出 2。

### 5.3 端到端流程

```
$ codex-image generate "a red panda" --out panda.png

  argparse → dispatch("generate")
        ↓
  auth.get_access_token()
        ├── 读 ~/.codex/auth.json
        ├── 检查 JWT exp
        ├── 临近过期 → refresh
        └── 缺失/失败 → interactive_login()
        ↓
  responses_client.generate(prompt, access_token=...)
        ├── POST /v1/responses（SSE）
        ├── 解析事件流到 response.completed
        └── 返回 GenerateResult
        ↓
  catch UnauthorizedError → auth.refresh_tokens(force=True) → 重试一次
        ↓
  output.save(b64, Path("panda.png"))
        ↓
  print: "Saved: /abs/path/panda.png"
```

---

## 6. 完美伪装 codex 的指纹规范

> 所有数值来自 codex Rust 源码 `/Users/linweimin/codes/agent-learn/claude-code-mini/codex`，每项已附文件:行号。

### 6.1 OAuth 授权 URL 查询参数

| 参数 | 值 |
|---|---|
| `response_type` | `code` |
| `client_id` | `eci-prd-pub-codex-123` （`rmcp-client/src/perform_oauth_login.rs:720`）|
| `redirect_uri` | `http://localhost:1455/auth/callback` （备用 `1457`；`login/src/server.rs:55,57,156`）|
| `scope` | `openid profile email offline_access api.connectors.read api.connectors.invoke` （`login/src/server.rs:496-498`）|
| `code_challenge` | PKCE 计算值 |
| `code_challenge_method` | `S256` （`login/src/server.rs:504`）|
| `state` | 32 字节随机 base64url |
| `id_token_add_organizations` | `true` （codex 特有，`login/src/server.rs:505-512`）|
| `codex_cli_simplified_flow` | `true` （codex 特有，同上）|
| `originator` | `codex_cli_rs` （同上）|

完整示例 URL：
```
https://auth.openai.com/oauth/authorize
  ?response_type=code
  &client_id=eci-prd-pub-codex-123
  &redirect_uri=http%3A%2F%2Flocalhost%3A1455%2Fauth%2Fcallback
  &scope=openid+profile+email+offline_access+api.connectors.read+api.connectors.invoke
  &code_challenge=<PKCE>
  &code_challenge_method=S256
  &state=<32B>
  &id_token_add_organizations=true
  &codex_cli_simplified_flow=true
  &originator=codex_cli_rs
```

### 6.2 `/v1/responses` HTTP 请求头（**伪装核心**）

| Header | 值 | codex 出处 |
|---|---|---|
| `Authorization` | `Bearer <access_token>` | `responses-api-proxy/src/lib.rs:196-221` |
| `originator` | `codex_cli_rs` | `login/src/auth/default_client.rs:36,234` |
| `User-Agent` | `codex_cli_rs/<version> (<os_type> <os_ver>; <arch>) <terminal_info>` | `login/src/auth/default_client.rs:133-157` |
| `Accept` | `text/event-stream` | `codex-api/src/endpoint/responses.rs:139` |
| `Content-Type` | `application/json` | （reqwest 默认 + body）|
| `session-id` | UUIDv4 每次启动新生成 | `codex-api/src/requests/headers.rs:8` |
| `x-codex-installation-id` | UUIDv4 持久化到 `$XDG_CACHE_HOME/codex-image/installation_id` 或 `~/.codex-image/installation_id` | `core/src/client.rs:135` |

**不发**的 header（codex 内部多轮状态机用，单次调用发了反而暴露）：
- `x-codex-turn-state`
- `x-codex-turn-metadata`
- `x-openai-subagent`
- `x-openai-memgen-request`
- `x-responsesapi-include-timing-metrics`
- `thread-id`
- `x-client-request-id`
- `x-openai-internal-codex-residency`

### 6.3 `User-Agent` 字段拼装规则

```python
USER_AGENT_TEMPLATE = "codex_cli_rs/{version} ({os_type} {os_ver}; {arch}) {terminal}"

def build_user_agent() -> str:
    return USER_AGENT_TEMPLATE.format(
        version=CODEX_PRETEND_VERSION,             # 硬编码当前 codex release tag
        os_type=platform.system(),                  # "Darwin" / "Linux"
        os_ver=platform.release(),                  # "24.3.0"
        arch=platform.machine(),                    # "arm64"
        terminal=detect_terminal() or "unknown",    # $TERM_PROGRAM
    )

CODEX_PRETEND_VERSION = "0.45.0"   # TODO: 定期跟进 codex release，建议季度 review
```

### 6.4 `auth.json` 文件结构（与 codex 完全一致）

```json
{
  "auth_mode": "Chatgpt",
  "tokens": {
    "id_token": "<JWT>",
    "access_token": "<JWT>",
    "refresh_token": "<string>",
    "account_id": "<workspace_id>"
  },
  "last_refresh": "<ISO8601 UTC>"
}
```

文件权限：`0o600`。

`logout()` 把 `tokens` 字段整个删除（保留 `auth_mode` 和 `last_refresh`），codex 读到无 tokens 会自动当作未登录。

### 6.5 Token refresh 请求

POST `https://auth.openai.com/oauth/token`：

```json
{
  "client_id": "eci-prd-pub-codex-123",
  "grant_type": "refresh_token",
  "refresh_token": "<token>"
}
```

错误处理：
- `refresh_token_expired` / `refresh_token_reused` / `refresh_token_invalidated` → 删 tokens 字段 → 转 `interactive_login()`
- 其他 4xx → 同上
- 5xx → 重试 3 次（2s/4s/8s）

---

## 7. 错误处理

详细错误处理矩阵已在 §4 各组件中说明，此处汇总优先级：

1. **鉴权链路所有失败 → 兜底到 `interactive_login()`**，永不进死循环（OAuth 失败直接退出 2）
2. **API 401 → 强制 refresh + 重试一次**，仍 401 直接报错（不无限重试，避免风暴）
3. **API 429/5xx → 指数退避重试 3 次**
4. **SSE 流断开 → 不重试**（重试可能产生重复扣额度），直接报错并退出 6
5. **任何文件系统错 → 报错带 errno 退出 3**，不静默吞错
6. **用户 Ctrl+C → 优雅关闭** OAuth 回调服务器和 SSE 连接

---

## 8. 测试策略

### 8.1 单元测试（pytest）

| 模块 | 测试范围 |
|---|---|
| `auth.py` | mock auth.json 多种状态（不存在/损坏/正常/过期）；mock JWT exp 边界；mock refresh 流程的 200/400/refresh_token_expired 三种响应 |
| `responses_client.py` | mock httpx server 返回预录的 SSE 流（成功/失败/401/429/5xx/断流）；验证事件解析正确性；验证重试逻辑 |
| `output.py` | 临时目录 + 命名冲突 + force 行为 + 父目录不存在 |
| `http_client.py` | 验证所有伪装 header 实际出现在请求里（用 `httpretty` 或 `responses` 拦截）|

### 8.2 集成测试（手动一次性，不入 CI）

1. **新用户全流程**：删 `~/.codex/auth.json` → 跑 `codex-image login` → 浏览器授权 → 跑 `codex-image generate "test"` → 验证图片落盘
2. **复用 codex 登录**：用 `codex login` 登录后跑 `codex-image generate`，应无 OAuth 弹窗
3. **token 过期**：手动改 auth.json 把 `last_refresh` 改到 9 天前，跑 `codex-image generate`，应静默 refresh
4. **edit 流程**：传入两张参考图跑 `codex-image edit`
5. **logout**：跑 `codex-image logout`，验证 `tokens` 字段被清空但文件保留
6. **status**：跑 `codex-image status`，验证打印的 email/plan/expires_at 正确

### 8.3 指纹验证（关键）

用 `mitmproxy` 抓 codex 原生 `image_gen` 调用 + 抓本 skill 的请求，逐字段 diff 两份 HTTP request，确保：
- method、path、HTTP 协议版本相同
- 所有 header 名/值集合相同（除 `session-id`、`x-codex-installation-id` 等天然变化的 UUID）
- request body JSON 字段集合相同（除 `input.content[0].text`）

这一步必须在初版上线前手动跑过一次，写一份 diff 报告进 `references/fingerprint.md`。

---

## 9. 依赖

```toml
# pyproject.toml
[project]
dependencies = [
    "requests>=2.31",          # HTTP
    "pyjwt>=2.8",              # 解析 JWT exp（不验签）
    "pillow>=10",              # edit 模式参考图缩放
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-mock",
    "responses>=0.25",         # HTTP mocking
]
```

用 `uv` 管理（与现有 `imagegen` skill 一致）：
```bash
uv pip install -e .
```

---

## 10. 开放问题（不阻塞实现）

1. **codex 版本号维护**：`CODEX_PRETEND_VERSION` 硬编码会随 codex 升级过时；建议每季度 review 一次，或写一个 `scripts/check_codex_version.py` 拉取 GitHub release 自动提示。
2. **合规性灰区**：复用 codex 的 `client_id` (`eci-prd-pub-codex-123`) 是公开常量，但伪装请求本质上是"非官方客户端使用 ChatGPT 订阅额度"——OpenAI ToS 上属灰色地带。skill 自带一份 `LEGAL.md` 提示用户该 skill **非 OpenAI 官方**，由用户自担风险。
3. **图像模型固化策略**：当前不传 `tools[0].model` 靠后端默认；如未来后端默认换成非 gpt-image-2 的模型，可考虑在 CLI 暴露 `--image-model` 改为默认传值。
4. **多账号支持**：当前仅支持单一 `auth.json`；如有多账号需求，需引入 `--profile` 概念存到 `~/.codex-image/profiles/<name>.json`。初版砍掉。

---

## 11. 下一步

完成本设计文档审阅后，立即移交 **superpowers:writing-plans** skill 生成实现计划。计划应：

- 拆分 phase（建议：①骨架 ②auth.py ③http_client.py ④responses_client.py ⑤output.py ⑥codex_image.py CLI 集成 ⑦集成测试 ⑧指纹 diff 验证 ⑨SKILL.md + 文档）
- 每个 phase 内部使用 TDD（先写测试再写实现）
- 在 ④ 完成后引入 `mitmproxy` 指纹 diff 作为 review checkpoint

---

_文档结束_
