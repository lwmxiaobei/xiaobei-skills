#!/usr/bin/env bash
# Search for candidate domain names (cached, discovery use).
# Usage: search.sh "<keyword or phrase>" [limit]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/_lib.sh"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 \"<keyword>\" [limit]" >&2
  exit 2
fi

QUERY="$1"
LIMIT="${2:-10}"

cf_curl GET "/domain-search" \
  --get \
  --data-urlencode "q=${QUERY}" \
  --data-urlencode "limit=${LIMIT}"
