# Story Card Video

把文章、网页、视频、截图或混合证据制作成高密度的 1080×1920 竖屏故事卡视频。

成片默认使用持续显示的标题与摘要、中部轮换的来源证据、背景音乐、信息完整的居中封面，以及固定品牌片尾。它适合 AI 新闻、产品动态、人物故事、研究进展和无旁白也能看懂的社交短视频。

## 功能

1. 生成 1080×1920、30 FPS 的竖屏视频
2. 使用两到四行标题建立钩子、冲突、方法与结果
3. 每 2.2 至 4 秒切换一张真实证据卡
4. 持续展示可读摘要和来源标识
5. 生成文字居中、信息相对完整的封面
6. 默认使用背景音乐，不生成旁白
7. 追加完整固定品牌片尾
8. 同时输出高清成片、720P 预览、封面和发布文案
9. 自动检查尺寸、时长、音视频流和关键画面

## 安装

使用 skills CLI 安装，并在交互列表中选择 `story-card-video`：

```bash
npx skills@latest add lwmxiaobei/xiaobei-skills
```

也可以手动克隆仓库并复制技能目录：

```bash
git clone https://github.com/lwmxiaobei/xiaobei-skills.git
cp -R xiaobei-skills/story-card-video ~/.codex/skills/story-card-video
```

重新启动 Codex，使技能目录重新加载。

## 依赖

需要以下运行环境：

```text
Python 3.10 或更高版本
Pillow
ffmpeg
ffprobe
```

安装 Pillow：

```bash
python3 -m pip install Pillow
```

macOS 可以使用 Homebrew 安装 FFmpeg：

```bash
brew install ffmpeg
```

## 使用方式

在 Codex 中提供文章链接、视频、截图或本地素材，并调用技能：

```text
使用 $story-card-video，把这个链接制作成竖屏故事卡视频：<URL>
```

也可以提供多个本地文件：

```text
使用 $story-card-video，把这些截图和视频制作成无旁白资讯卡短视频。
```

技能会核对素材、提炼有来源的事实、生成 `story.json`、渲染成片并检查输出。

## 命令行工作流

先确定技能目录和项目目录：

```bash
skill_dir="$HOME/.codex/skills/story-card-video"
project_dir="/path/to/story-project"
```

分析输入：

```bash
python3 "$skill_dir/scripts/analyze_inputs.py" \
  --project "$project_dir" \
  /path/to/input.png
```

编辑 `$project_dir/story.json` 后进行校验：

```bash
python3 "$skill_dir/scripts/validate_project.py" "$project_dir"
```

渲染视频与封面：

```bash
python3 "$skill_dir/scripts/render_video.py" "$project_dir"
```

生成输出检查报告：

```bash
python3 "$skill_dir/scripts/inspect_output.py" \
  "$project_dir/out/video.mp4" \
  --report-dir "$project_dir/out/qa"
```

对于网页链接，输入分析器只登记 URL。Codex Agent 仍需获取正文、保存来源信息并生成可核对的页面截图。

## 封面信息结构

推荐使用以下字段：

```json
{
  "cover_title": "短标题回退",
  "cover_kicker": "来源或事件背景",
  "cover_lines": [
    "事件主体或任务",
    "重要限制或事实边界",
    "具体结果",
    "关键数字或意义"
  ],
  "cover_evidence": [
    "支持事实一",
    "支持事实二"
  ],
  "source_label": "来源：原始账号或出版方"
}
```

封面规则：

1. 所有文字块水平居中
2. `cover_lines` 使用二到四行
3. 同时呈现事件主体、事实边界和具体结果
4. 来源提供关键数字时优先展示数字
5. `cover_evidence` 最多两行，并保持次要层级
6. 旧项目没有 `cover_lines` 时回退到 `cover_title`

完整字段说明见 [references/project-schema.md](references/project-schema.md)。文案与证据结构见 [references/story-formula.md](references/story-formula.md)。

## 输出文件

默认输出到项目的 `out` 目录：

```text
out/video.mp4
out/video_preview_720p.mp4
out/cover.png
out/publish.txt
out/qa/contact-sheet.jpg
out/qa/probe.json
```

如果 `settings.delivery_dir` 未设置为空，高清成片还会复制到：

```text
~/Documents/videos/<short_title>.mp4
```

## 项目结构

```text
story-card-video/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── assets/
│   ├── default-bgm.m4a
│   ├── example-story.json
│   └── logo-outro.mp4
├── references/
│   ├── project-schema.md
│   └── story-formula.md
└── scripts/
    ├── analyze_inputs.py
    ├── inspect_output.py
    ├── render_video.py
    ├── story_common.py
    └── validate_project.py
```

## 事实与发布边界

每条事实都应能追溯到用户提供的素材或保存的来源。不要从图片、文件名或缩略图推断收入、动机、身份、健康状况或因果关系。

默认背景音乐 `assets/default-bgm.m4a` 的版权状态未知。商业发布前必须确认音乐、截图、图片和视频片段的使用权。

默认片尾 `assets/logo-outro.mp4` 带有固定品牌身份。需要发布到其他账号时，请在制作前明确取消或替换片尾。

## 校验

校验技能目录：

```bash
python3 /path/to/skill-creator/scripts/quick_validate.py \
  /path/to/story-card-video
```

校验真实项目时，还应打开封面和输出联系表，检查文字居中、信息层级、安全边距、证据截图可读性、最后一张故事卡和完整片尾。
