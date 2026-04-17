# cloudflare-registrar

一个 Claude Code skill，封装了 Cloudflare Registrar API（Beta），用于域名搜索、可用性与价格查询，以及域名注册。

> English version: [README.md](./README.md)

## 功能简介

为 Claude 提供一套安全、一致的工作流，覆盖三类任务：

- **搜索（Search）**：根据关键词生成候选域名（带缓存、速度快，用于发现灵感）。
- **查询（Check）**：实时查询指定域名的可用性和价格（权威数据，下单前必须调用）。
- **注册（Register）**：正式购买域名（**会产生费用，且不可退款**）。

注册环节带有安全护栏：Claude 在调用 `/registrations` 之前，始终会先做一次实时价格查询，并用自然语言向你二次确认域名和价格。

## 前置条件

- 一个 Cloudflare 账号。
- 一个具备 **Registrar 写入权限** 的 API Token。
- 账号中已配置默认付款方式的账单资料。
- Cloudflare Dashboard 中已设置好默认注册联系人信息，并接受《域名注册协议》。
- 本地 shell 中可用的 `curl`。

## 安装

将 skill 目录放入用户级 Claude skills 目录：

```
~/.claude/skills/cloudflare-registrar/
```

重启 Claude Code（或执行 `/reload-plugins`）后生效。

设置两个环境变量以便脚本完成鉴权。推荐写入 `~/.zshenv`，确保所有 shell 上下文（包括 Claude Code、cron、IDE 终端）都能读取到：

```bash
export ACCOUNT_ID="<你的 Cloudflare Account ID>"
export CLOUDFLARE_API_TOKEN="<具备 Registrar 权限的 API Token>"
```

> 不要把 Token 直接粘贴到与 Claude 的对话中。如果 skill 脚本提示 "env var is required"，请在自己的 shell 中 export 好变量，**不要** 通过聊天消息发送。

## 通过 Claude 使用

直接用自然语言提问即可。skill 的描述经过设计，即便不提 "Cloudflare" 也能正确触发：

- "帮我找 5 个可以注册的 `.dev` 域名，用于一个 AI 记账项目。"
- "`acme-robotics.ai` 现在能注册吗？多少钱？"
- "在我的 Cloudflare 账号上注册 `mybrand.dev`。"

Claude 会依次：

1. 在需要时运行 `search.sh` 生成候选域名。
2. 在任何计费操作之前调用 `check.sh` 获取实时价格。
3. 以"域名 + 价格 + 不可退款"的摘要向你请求明确确认。
4. 在你明确同意后才运行 `register.sh`。
5. 若注册进入异步流程，则轮询 `status.sh` 获取结果。

## 直接使用脚本

所有脚本位于 `scripts/` 目录。脚本将 API 响应 JSON 打印到 stdout，HTTP 错误会以非零退出码结束。

| 命令 | 用途 |
| --- | --- |
| `scripts/search.sh "<关键词>" [limit]` | 生成候选域名（带缓存，适合探索）。 |
| `scripts/check.sh <domain> [<domain> ...]` | 实时查询可用性与价格，单次最多 20 个。 |
| `scripts/register.sh <domain> [--async]` | **计费操作**。使用账号默认配置完成注册。 |
| `scripts/status.sh <domain>` | 查询进行中或已完成注册的工作流状态。 |

示例：

```bash
scripts/check.sh acme.dev acme.ai acme.com
```

## 注册默认设置

`register.sh` 有意采用账号默认值：

- `auto_renew`：**false**（默认不自动续费更安全）
- `privacy_mode`：注册局默认值（TLD 支持时通常为 `redaction`）
- 注册联系人：账号中配置的默认联系人
- 付款方式：账号中配置的默认付款方式

如需覆盖以上任一项，请直接用 `curl` 调用 Registrar API；脚本不支持通过参数覆盖这些字段。

## 常见错误情形

`check.sh` 返回的几种不可注册原因：

- `domain_unavailable` —— 已被他人持有。
- `extension_not_supported_via_api` —— 该 TLD 仅支持在 Dashboard 操作，API 不开放，需去面板处理。
- `extension_not_supported` / `extension_disallows_registration` —— Cloudflare 根本不售卖该 TLD。

`register.sh` 返回的工作流状态：

- `succeeded` —— 已成功。
- `in_progress` —— 用 `status.sh` 轮询。
- `failed` —— 查看 `error.code` / `error.message`，**不要** 静默重试。
- `action_required` / `blocked` —— 停止流程，将信息反馈给用户。

## 暂不支持

Registrar API Beta 目前不覆盖：

- 续费（Renewals）
- 转入（Transfers）
- 联系人信息修改
- 溢价域名费用确认（Premium fee）

上述操作请前往 Cloudflare Dashboard 完成。

## 目录结构

```
cloudflare-registrar/
├── README.md           英文说明
├── README.zh.md        中文说明（本文件）
├── SKILL.md            Skill 触发后 Claude 读取的操作指引
├── scripts/
│   ├── _lib.sh         共享的鉴权与 base URL 逻辑
│   ├── search.sh       GET  /registrar/domain-search
│   ├── check.sh        POST /registrar/domain-check
│   ├── register.sh     POST /registrar/registrations        （计费）
│   └── status.sh       GET  /registrar/registrations/<d>/registration-status
└── evals/
    └── evals.json      用于评估 skill 行为的测试 prompt
```

## 参考链接

- Cloudflare Registrar API 文档： https://developers.cloudflare.com/registrar/registrar-api/
- 创建 API Token： `https://dash.cloudflare.com/<ACCOUNT_ID>/api-tokens`
- 账单与付款方式： `https://dash.cloudflare.com/<ACCOUNT_ID>/billing/payment-info`
