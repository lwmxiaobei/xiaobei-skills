#!/usr/bin/env bash
# Real-time availability and price check. Run this immediately before register.sh.
# Usage: check.sh <domain> [<domain> ...]   (up to 20 domains per call)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/_lib.sh"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <domain> [<domain> ...]" >&2
  exit 2
fi

if [[ $# -gt 20 ]]; then
  echo "Error: at most 20 domains per request (got $#)." >&2
  exit 2
fi

# Build JSON array: ["a.com","b.dev"]
payload='{"domains":['
first=1
for d in "$@"; do
  if (( first )); then first=0; else payload+=','; fi
  # Basic sanity: reject quotes and backslashes in domain names to avoid JSON injection
  case "$d" in
    *[\"\\]*) echo "Error: invalid character in domain '$d'" >&2; exit 2 ;;
  esac
  payload+="\"${d}\""
done
payload+=']}'

cf_curl POST "/domain-check" \
  --header "Content-Type: application/json" \
  --data "$payload"
