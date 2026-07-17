# Media Montage Video

`media-montage-video` 是一个用于制作混合媒体短视频的 Codex Skill。它可以把用户提供的视频、屏幕录制、产品演示和图片整理成完整的 Remotion 工程，并生成中文旁白、同步字幕、画面文案、预览视频和最终 MP4。

## 主要能力

1. 分析视频时长、分辨率、场景变化、音轨和关键画面。
2. 将输入素材统一转换为浏览器和 Remotion 可使用的格式。
3. 根据目标时长生成旁白、字幕、标题和分镜。
4. 使用 F5 TTS 1.1.21 生成中文旁白。
5. 自动同步旁白、字幕和场景时长。
6. 生成可编辑的 Remotion 工程。
7. 输出竖屏或横屏 H.264 视频及轻量预览版。
8. 自动检查黑帧、视频规格、字幕安全区和旁白覆盖率。

## 系统要求

### macOS

1. Python 3。
2. FFmpeg。
3. Node.js 和 npm。
4. `uv`，或者 Python 3.10、Python 3.11。
5. 首次安装和首次语音合成时可以访问 PyPI 与 Hugging Face。

推荐使用 Homebrew 安装基础依赖：

```bash
brew install ffmpeg node uv
```

### Windows

1. Python 3。
2. FFmpeg，并确保 `ffmpeg.exe` 位于 PATH。
3. Node.js 和 npm。
4. `uv.exe`，或者可由 `py` 启动器访问的 Python 3.10、Python 3.11。
5. 首次安装和首次语音合成时可以访问 PyPI 与 Hugging Face。

Windows 已完成路径、安装锁和 Python 启动器兼容处理，目前未做 Windows 实机测试。

本文后续示例统一使用 `python3`。Windows 用户可以将命令开头替换为 `py -3.11` 或可用的 `python`。渲染脚本会自动处理 `npm.cmd` 和 `remotion.cmd`。

## 安装 Skill

### macOS

```bash
git clone https://github.com/lwmxiaobei/xiaobei-skills.git
mkdir -p ~/.codex/skills
cp -R xiaobei-skills/media-montage-video ~/.codex/skills/
```

### Windows PowerShell

```powershell
git clone https://github.com/lwmxiaobei/xiaobei-skills.git
New-Item -ItemType Directory -Force "$HOME\.codex\skills"
Copy-Item -Recurse -Force ".\xiaobei-skills\media-montage-video" "$HOME\.codex\skills\"
```

安装完成后，重新启动 Codex 或开始一个新任务，使 Skill 清单重新加载。

## F5 TTS 固定运行时

Skill 不会在每个视频项目中重复创建 F5 TTS 环境，而是使用固定共享目录：

```text
~/.codex/runtimes/f5-tts/1.1.21/.venv
```

macOS 解释器路径：

```text
~/.codex/runtimes/f5-tts/1.1.21/.venv/bin/python
```

Windows 解释器路径：

```text
%USERPROFILE%\.codex\runtimes\f5-tts\1.1.21\.venv\Scripts\python.exe
```

检查运行时：

```bash
python3 scripts/synthesize_f5_speech.py --check-runtime
```

如果固定运行时不存在或依赖不完整，检查命令会自动执行 `scripts/install_f5_runtime.py`。安装器会优先使用 `uv`，然后尝试 Python 3.11 或 Python 3.10。

macOS 使用 `fcntl` 防止多个任务重复安装。Windows 使用 `msvcrt` 实现相同的安装锁。

可以通过以下环境变量覆盖默认解释器：

```text
MEDIA_MONTAGE_F5_PYTHON
VIDEOGEN_F5_PYTHON
F5_TTS_PYTHON
```

## 快速开始

以下命令均在 Skill 目录执行。

### 1. 创建项目

```bash
python3 scripts/create_project.py /path/to/my-video-project
```

### 2. 分析素材

```bash
python3 scripts/analyze_media.py /path/to/video.mp4 /path/to/images \
  --output-dir /path/to/my-video-project/analysis
```

必须查看生成的 `media-report.json` 和联系表，再决定视频截取区间与图片使用顺序。

### 3. 准备素材

```bash
python3 scripts/prepare_media.py \
  /path/to/my-video-project \
  /path/to/video.mp4 \
  /path/to/images
```

处理后的素材位于项目的 `public/assets/source` 目录，清单位于 `media-manifest.json`。

### 4. 编写分镜

根据 `references/media-schema.md` 编辑项目中的 `video.json`。每个场景可以包含视频、图片、文字、旁白、字幕和原始音频设置。

旁白、字幕和画面文案是三个独立层级：

1. `narrationText` 用于自然口语旁白。
2. `captions` 用于按时间分页的短字幕。
3. `elements` 和 `layout` 用于持续显示的标题、数字、标签与结论。

### 5. 生成旁白

单条旁白：

```bash
python3 scripts/synthesize_f5_speech.py \
  --text "这是一段测试旁白。" \
  --output /path/to/my-video-project/public/audio/test.wav
```

批量生成场景旁白：

```bash
python3 scripts/synthesize_f5_speech.py \
  --manifest /path/to/my-video-project/narration.json
```

推荐一次生成四到八个完整场景段落，不要把每一页字幕单独生成一段音频。

### 6. 同步字幕和时长

```bash
python3 scripts/sync_captions.py \
  /path/to/my-video-project \
  --target-duration 60
```

精确时长模式要求旁白至少覆盖叙述场景时间的 90%。如果覆盖率不足，应修改文案并重新生成旁白，不应使用大量静音填充。

### 7. 验证和渲染

```bash
python3 scripts/validate_project.py /path/to/my-video-project
python3 scripts/render_video.py /path/to/my-video-project
```

首次渲染会在项目目录中安装固定版本的 Remotion 依赖。

### 8. 质量检查

```bash
python3 scripts/inspect_video.py \
  /path/to/my-video-project/out/video.mp4 \
  --report-dir /path/to/my-video-project/out/qa
```

## 输出文件

默认输出：

```text
out/video.mp4
out/video_preview_720p.mp4
out/qa/report.json
```

`video.mp4` 是最终成片，`video_preview_720p.mp4` 是便于快速预览和传输的轻量版本。

## 默认声音和自定义声音

Skill 包含一段经过授权的中文参考音频，默认用于 F5 TTS 中文旁白。

如果使用自定义声音，必须同时提供经过授权的参考音频和准确文本：

```bash
python3 scripts/synthesize_f5_speech.py \
  --text "需要生成的旁白" \
  --output output.wav \
  --reference-audio authorized-reference.wav \
  --reference-text "参考音频中的准确内容"
```

不要在未经授权的情况下克隆他人的声音。

## 项目结构

```text
media-montage-video/
  SKILL.md
  README.md
  agents/
  assets/
    remotion-template/
    voice/
  references/
  scripts/
```

## 常见问题

### 找不到 FFmpeg

确认终端可以执行：

```bash
ffmpeg -version
ffprobe -version
```

Windows 需要把 FFmpeg 的 `bin` 目录加入 PATH。

### F5 TTS 自动安装失败

直接运行安装器查看完整错误：

```bash
python3 scripts/install_f5_runtime.py
```

确认存在 `uv`，或者 Python 3.10、Python 3.11，并检查 PyPI 网络连接。

### 首次合成无法下载模型

F5 TTS 首次生成语音时会从 Hugging Face 下载模型。检查网络、代理设置、磁盘空间和 Hugging Face 访问状态。

### 渲染时找不到 npm

安装 Node.js，并确认以下命令可用：

```bash
node --version
npm --version
```

## 许可与素材责任

使用者需要自行确认输入视频、图片、音乐、字体和自定义声音的使用授权。发布事实类内容前，应核实信息来源和素材许可。
