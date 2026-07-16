# Videogen

Videogen 是一个面向 Codex 的完整视频生成 skill。它可以从主题、文章、脚本、网页、文档或已有素材生成可编辑的 Remotion 工程，并输出高清 MP4 和轻量预览版。

它适合制作竖屏短视频、历史故事、知识讲解、产品介绍、纸艺拼贴动画和写实人物分层视频。

## 主要能力

1. 在生成旁白前锁定目标时长
2. 根据真实音频长度同步场景和字幕
3. 使用 F5 TTS 生成自然中文旁白
4. 内置已授权的默认参考音频
5. 支持用户提供自定义授权参考音频
6. 支持写实背景与透明人物分层
7. 支持人物入场、呼吸、重心摆动和轻微透视动作
8. 默认使用直接切镜，避免场景间闪黑或闪白
9. 自动检查工程、音轨、黑帧和关键画面
10. 同时输出高清成片与 720p 轻量预览

## 相关文档

1. [Codex 执行规范](SKILL.md)
2. [视频配置字段](references/video-schema.md)
3. [视觉风格预设](references/style-presets.md)
4. [交付质量检查](references/quality-gates.md)

## 安装

将整个 `videogen` 文件夹复制到 Codex skills 目录：

```bash
mkdir -p ~/.codex/skills
cp -R videogen ~/.codex/skills/videogen
```

重新打开 Codex 后，可以在提示词中直接使用：

```text
使用 $videogen 制作一条六十秒的赤壁之战竖屏视频，采用写实历史插画，人物需要分层并有轻微动作。
```

## 环境要求

基础视频流程需要：

1. Python 3
2. Node.js 和 npm
3. FFmpeg 和 FFprobe
4. 可用的图片生成能力或用户提供的素材

中文 F5 TTS 旁白还需要一个能够导入 `f5_tts` 的 Python 环境。模型权重由接收者机器上的 F5 TTS 和 Hugging Face 环境自行下载和缓存。

## 快速开始

### 1. 创建工程

在 skill 目录中运行：

```bash
python3 scripts/create_project.py /path/to/my-video
```

工程会从 `assets/remotion-template` 创建，不会修改 skill 自带模板。

### 2. 编辑视频配置

编辑新工程中的 `video.json`。配置包含画面尺寸、帧率、主题、场景、旁白、字幕、背景、人物和文字元素。

完整字段说明位于：

```text
references/video-schema.md
```

### 3. 准备素材

所有本地素材放在工程的 `public` 目录中：

```text
public/assets
public/audio
public/fonts
```

写实人物视频推荐使用两类独立素材：

1. 不包含主要人物的完整背景图
2. 带透明通道的人物前景图

人物和背景独立运动后，可以形成更自然的景深和视差效果。

### 4. 检查 F5 TTS 环境

```bash
python3 scripts/synthesize_f5_speech.py --check-runtime
```

脚本会按以下顺序寻找 F5 TTS：

1. `--python` 参数
2. `VIDEOGEN_F5_PYTHON` 环境变量
3. `F5_TTS_PYTHON` 环境变量
4. 当前 Python 环境
5. 当前 Virtualenv
6. 当前 Conda 环境
7. 项目附近的 `.venv`、`venv` 和 `env`
8. PATH 中的 `python3` 和 `python`

每个候选解释器都会实际执行 `import f5_tts`。脚本只会选择导入成功的环境，并保留虚拟环境入口路径，避免丢失对应的 `site-packages`。

无法自动发现时，可以显式配置：

```bash
export VIDEOGEN_F5_PYTHON=/path/to/f5-environment/bin/python
```

也可以在命令中指定：

```bash
python3 scripts/synthesize_f5_speech.py \
  --python /path/to/f5-environment/bin/python \
  --check-runtime
```

### 5. 使用默认声音生成旁白

内置参考音频已授权随 skill 分发，并可作为默认旁白参考使用。

单段生成：

```bash
python3 scripts/synthesize_f5_speech.py \
  --text "这里是旁白内容。" \
  --output /path/to/my-video/public/audio/scene-01.wav
```

多场景生成时，先创建 `narration.json`：

```json
[
  {
    "text": "第一幕旁白。",
    "output": "public/audio/scene-01.wav"
  },
  {
    "text": "第二幕旁白。",
    "output": "public/audio/scene-02.wav"
  }
]
```

然后在一个模型会话中合成全部场景：

```bash
python3 scripts/synthesize_f5_speech.py \
  --manifest /path/to/my-video/narration.json
```

为了减少每句话都使用相同语调的问题，每个音频文件应包含一整幕的自然段落，不要把每个短句分别生成。可以通过长短句变化、逗号、句号和少量感叹号控制停顿与强调。

### 6. 使用自定义声音

自定义声音需要用户提供或确认授权，并同时提供参考音频的准确文字：

```bash
python3 scripts/synthesize_f5_speech.py \
  --reference-audio /path/to/authorized-reference.wav \
  --reference-text "参考音频的准确文字" \
  --manifest /path/to/my-video/narration.json
```

自定义参考音频默认保留在用户自己的工程中。除非用户明确授权，不要把它加入共享 skill。

### 7. 同步字幕和精确时长

使用真实音频长度更新场景和字幕：

```bash
python3 scripts/sync_captions.py /path/to/my-video
```

需要六十秒成片时：

```bash
python3 scripts/sync_captions.py \
  /path/to/my-video \
  --target-duration 60
```

如果旁白总长度超过目标时长，脚本会停止并要求缩短文案。它不会强行拉伸或加速旁白。如果旁白较短，剩余时间会按场景比例分配为画面停留时间。

### 8. 配置人物动作

在人物图片元素中设置 `motionPreset`：

```json
{
  "id": "main-character",
  "type": "image",
  "src": "assets/characters/main-character.png",
  "x": 760,
  "y": 1260,
  "width": 650,
  "zIndex": 24,
  "role": "primary",
  "motionPreset": "character",
  "enter": {
    "type": "right",
    "atSeconds": 0.3,
    "durationSeconds": 0.8,
    "distance": 120
  },
  "drift": {
    "x": 6,
    "y": 8,
    "scale": 0.008,
    "periodSeconds": 4
  }
}
```

可用动作预设：

1. `character` 用于人物呼吸、重心变化和轻微透视
2. `drift` 用于普通图片和道具漂移
3. `static` 用于地图、标签和必须锁定的元素

所有动画均由 Remotion 帧驱动，不使用 CSS 动画。

### 9. 校验并渲染

```bash
python3 scripts/validate_project.py /path/to/my-video
python3 scripts/render_video.py /path/to/my-video
```

渲染完成后会生成：

```text
out/video.mp4
out/video_preview_720p.mp4
```

轻量预览应优先在 Codex 中打开，可以降低大文件打开超时的概率。

### 10. 检查成片

```bash
python3 scripts/inspect_video.py \
  /path/to/my-video/out/video.mp4 \
  --report-dir /path/to/my-video/out/qa
```

检查内容包括时长、尺寸、编码、音轨、黑帧和关键帧截图。交付前还需要人工检查字幕安全区、人物遮挡、场景切换、音量和旁白节奏。

## 视觉预设

内置预设包括：

1. 纸艺拼贴
2. 编辑卡片
3. 纪录片
4. 产品展示
5. 写实历史插画

详细规则和提示词骨架位于：

```text
references/style-presets.md
```

## 常见问题

### 找不到 F5 TTS

先执行运行时检查。如果自动发现失败，激活对应虚拟环境，设置 `VIDEOGEN_F5_PYTHON`，或者使用 `--python` 指定解释器。

### 首次生成旁白很慢

F5 TTS 首次运行可能需要下载模型。后续运行通常会使用接收者机器上的本地缓存。

### 旁白每句话语调相同

把完整场景写成一个自然段后一次生成。使用自然的长短句和标点控制节奏，并为不同场景使用不同 seed。不要逐句合成后机械拼接。

### 场景切换时闪一下

不要让整幕淡入透明或淡出到黑色。模板默认采用直接切镜，并在新场景开头使用轻微镜头推进来增强切换感。

### 成片在 Codex 中打开超时

优先打开 `out/video_preview_720p.mp4`。确认内容后再使用高清成片。

### 人物看起来仍然像静态图片

确认人物是独立透明图层，并设置 `motionPreset` 为 `character`。背景和人物应使用不同的移动幅度，以形成景深关系。

## 共享与授权

1. 内置默认参考音频已授权随 skill 分发和使用
2. 用户自定义声音必须由用户提供或确认授权
3. 字体、音乐、图片、模型和其他素材仍需分别确认许可
4. 历史重构画面应明确标注为艺术重构，不应冒充真实史料

## 目录说明

```text
videogen/
  SKILL.md
  README.md
  agents/openai.yaml
  references/video-schema.md
  references/style-presets.md
  references/quality-gates.md
  scripts/create_project.py
  scripts/synthesize_f5_speech.py
  scripts/synthesize_speech.py
  scripts/sync_captions.py
  scripts/validate_project.py
  scripts/render_video.py
  scripts/inspect_video.py
  assets/remotion-template/
  assets/voice/user-narrator-reference.wav
```

`SKILL.md` 是 Codex 执行任务时读取的操作规范，`README.md` 面向安装者和使用者。
