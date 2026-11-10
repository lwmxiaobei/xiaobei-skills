#!/bin/zsh
# 用官方 codex CLI 的 image_generation 生图（codex-image 技能写死的模型已失效）
# 用法：gen_img.sh <输出png路径> <提示词文件> [参考图...]
# codex 只负责生图（只读沙箱）；脚本按本次会话 thread_id 到 ~/.codex/generated_images/<id>/ 取图，避免拿错别的会话的图
# 本机全局 codex 0.143 太旧，用 npx 调最新官方版，不改全局安装
# stdin 必须接 /dev/null：在后台跑时 stdin 不关，codex exec 会一直等 "Reading additional input from stdin"
OUT="$1"; PROMPT_FILE="$2"; shift 2
REFS=(); for r in "$@"; do REFS+=(-i "$r"); done
mkdir -p "$(dirname "$OUT")"
TASK="Use your built-in image generation tool to create exactly ONE image from the image prompt below. Pass the image prompt through faithfully. If reference images are attached, use them only as described in the prompt. Do not run any shell commands and do not create files; just generate the image and then reply DONE.

IMAGE PROMPT:
$(cat "$PROMPT_FILE")"
LOG="$(mktemp -t genimg)"
npx -y @openai/codex@0.160.1 exec --json -c model_reasoning_effort="low" --skip-git-repo-check -s read-only "${REFS[@]}" -- "$TASK" < /dev/null > "$LOG" 2>"$LOG.err"
TID=$(grep -m1 '"thread.started"' "$LOG" | python3 -c 'import sys,json; print(json.loads(sys.stdin.read())["thread_id"])' 2>/dev/null)
DIR="$HOME/.codex/generated_images/$TID"
# 注意：不能写 ls -t "$DIR"/*.png(N)——没生成出图时 glob 为空，ls 会列当前目录，把别的文件当成图复制过去
IMGS=(); [[ -n "$TID" ]] && IMGS=("$DIR"/*.png(N.om)); IMG="${IMGS[1]}"
if [[ -z "$TID" || -z "$IMG" ]]; then echo "FAIL $OUT (thread=$TID) log=$LOG"; tail -5 "$LOG.err"; exit 1; fi
cp "$IMG" "$OUT" && echo "OK $OUT <- $IMG"
