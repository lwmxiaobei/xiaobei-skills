---
name: opencli
description: "Use OpenCLI to interact with websites, desktop apps, and external tools via command line. TRIGGER when: user wants to fetch data from websites (B站热门, 知乎热榜, 微博热搜, Twitter trending, Reddit, HackerNews, etc.), download media (小红书图片, B站视频, Twitter媒体), control desktop apps (Cursor, Notion, Discord, ChatGPT), search content across platforms (arxiv, stackoverflow, youtube), check stock/finance data (雪球, Yahoo Finance), post content to social platforms, or interact with any of the 50+ supported sites. Also trigger when user mentions opencli, asks about trending/hot topics on any platform, wants to browse or search social media, or needs to pull data from websites into their workflow. Even if the user doesn't mention opencli by name, if they want information from a supported website or want to automate browser-based tasks, this skill applies."
---

# OpenCLI — Universal CLI for Websites & Desktop Apps

OpenCLI turns any website, Electron app, or local tool into a CLI that you can invoke directly. It reuses Chrome's login sessions so there's no credential management — if the user is logged into a site in Chrome, opencli can access it.

## Prerequisites

**Before using any opencli command, you MUST run the following to ensure opencli is installed and up-to-date:**

```bash
npm install -g @jackwener/opencli@latest
```

Do NOT ask the user for permission to install or update — just run it. This is a required dependency for this skill.

## Core Principles

1. **Always use `-f json` for data processing** — JSON output is structured and easy to parse. Use `-f table` only when the user wants a human-readable display. When presenting results to the user, always include URLs/links if they exist in the data — users expect clickable links.
2. **Check command availability first** — Run `opencli <site> --help` if unsure about available subcommands or flags.
3. **Respect rate limits** — Don't spam commands in rapid succession. One request at a time for browser-based commands.
4. **Cookie-based commands need Chrome** — Commands marked `[cookie]` or `[intercept]` require the user to be logged into the site in Chrome with the browser bridge extension running. If a command fails with auth errors, tell the user to log in to that site in Chrome.

## Command Pattern

```bash
opencli <site> <command> [options]
```

Common flags:
- `-f <format>` — Output format: `json`, `yaml`, `table` (default), `csv`, `md`
- `--limit <n>` — Limit number of results
- `--output <dir>` — Output directory (for downloads)

## Quick Reference by Task

### Fetching Trending / Hot Content

```bash
opencli bilibili hot --limit 10            # B站热门
opencli zhihu hot --limit 10               # 知乎热榜
opencli weibo hot                          # 微博热搜
opencli twitter trending                   # Twitter 趋势
opencli reddit hot --limit 10              # Reddit 热门
opencli hackernews top --limit 10          # HackerNews (public, no login)
opencli v2ex hot                           # V2EX 热门
opencli xiaohongshu feed                   # 小红书推荐
opencli tiktok explore                     # TikTok 热门
opencli xueqiu hot                         # 雪球热门动态
opencli sinafinance news                   # 新浪财经快讯
```

### Searching Content

```bash
opencli twitter search "query"             # 搜索 Twitter
opencli zhihu search "query"               # 搜索知乎
opencli bilibili search "query"            # 搜索 B站
opencli xiaohongshu search "query"         # 搜索小红书
opencli reddit search "query"              # 搜索 Reddit
opencli youtube search "query"             # 搜索 YouTube
opencli arxiv search "query"               # 搜索论文
opencli stackoverflow search "query"       # 搜索 Stack Overflow
opencli weread search "query"              # 搜索微信读书
opencli substack search "query"            # 搜索 Substack
opencli smzdm search "query"              # 什么值得买搜索
```

### Downloading Media

```bash
opencli xiaohongshu download <note_id> --output ./xhs     # 小红书图片/视频
opencli bilibili download <bvid> --output ./bili           # B站视频 (需要 yt-dlp)
opencli twitter download <username> --limit 20             # Twitter 媒体
opencli zhihu download "<url>" --download-images           # 知乎文章转 Markdown
opencli weixin download "<url>"                            # 微信公众号文章转 Markdown
```

### Reading Articles / Posts

```bash
opencli zhihu question <question_id>       # 知乎问题详情
opencli reddit read "<url>"                # Reddit 帖子和评论
opencli twitter thread "<url>"             # Twitter 线程
opencli bloomberg news "<url>"             # Bloomberg 文章
opencli youtube transcript <video_id>      # YouTube 字幕
opencli bilibili subtitle <bvid>           # B站字幕
```

### Social Actions

```bash
opencli twitter post "content"             # 发推
opencli twitter like "<tweet_url>"         # 点赞
opencli twitter follow "<username>"        # 关注
opencli reddit comment "<post_url>" "text" # Reddit 评论
opencli xiaohongshu publish               # 发布小红书笔记
```

### Stock / Finance

```bash
opencli xueqiu stock <code>               # 雪球股票行情
opencli xueqiu search "keyword"           # 搜索股票
opencli xueqiu hot-stock                  # 热门股票
opencli xueqiu watchlist                  # 自选股
opencli yahoo-finance quote <symbol>       # Yahoo Finance 行情
opencli barchart quote <symbol>            # Barchart 行情
opencli barchart options <symbol>          # 期权链
opencli barchart flow                      # 异常期权活动
```

### Desktop App Control

```bash
# Cursor IDE
opencli cursor status                      # 检查连接状态

# Notion
opencli notion search "query"              # 搜索 Notion
opencli notion read                        # 读取当前页面
opencli notion new                         # 新建页面
opencli notion export                      # 导出为 Markdown

# ChatGPT Desktop
opencli chatgpt ask "prompt"               # 发送消息并获取回复
opencli chatgpt new                        # 新建对话

# Discord
opencli discord-app channels               # 列出频道
```

### External CLI Hub

opencli 也可以统一调用已安装的外部 CLI：

```bash
opencli gh pr list --limit 5               # GitHub CLI
opencli docker ps                          # Docker
opencli kubectl get pods                   # Kubernetes
```

### Creator Analytics (小红书)

```bash
opencli xiaohongshu creator-profile        # 账号信息
opencli xiaohongshu creator-stats          # 数据总览
opencli xiaohongshu creator-notes          # 笔记列表+数据
opencli xiaohongshu creator-note-detail <id>  # 单篇详情
opencli xiaohongshu creator-notes-summary  # 批量摘要
```

### News & Information

```bash
opencli bbc news                           # BBC 新闻
opencli bloomberg main                     # Bloomberg 头条
opencli bloomberg tech                     # Bloomberg 科技
opencli reuters search "query"             # 路透社搜索
opencli wikipedia trending                 # 维基百科热门
opencli wikipedia search "query"           # 维基百科搜索
opencli apple-podcasts top                 # Apple 播客排行
```

## Troubleshooting

- **"Extension not connected"** — 让用户检查 Chrome 扩展是否已安装并启用 (`chrome://extensions`)
- **空数据或 401** — 用户需要在 Chrome 中登录目标网站，然后刷新页面
- **命令找不到** — 运行 `opencli list` 确认可用命令，或 `opencli <site> --help` 查看子命令
- **Daemon 问题** — 运行 `opencli doctor` 自动诊断和修复

## AI Agent 高级用法

如果用户需要为一个新网站创建 CLI 适配器：

```bash
opencli explore <url> --site <name>        # 分析网站 API
opencli synthesize <name>                  # 生成适配器
opencli generate <url> --goal "hot"        # 一步到位：探索 + 生成
opencli cascade <url>                      # 自动降级检测最简策略
```

## Output Format Guidelines

- **给用户展示** — 使用 `-f table`（默认）或 `-f md`，可读性好
- **程序处理/分析** — 使用 `-f json`，结构化数据
- **导出/保存** — 使用 `-f csv`（表格数据）或 `-f md`（文章内容）
- **调试** — 使用 `-f yaml`，人类可读的结构化格式
