#!/usr/bin/env bash
# try_exact.sh — 调 exact? 拿建议
#
# 用法: bash try_exact.sh <run_dir> <goal_lean_expression>
#
# 输出: exact? 建议的 tactic（纯文本），没有建议输出空
set -euo pipefail

RUN_DIR="${1:?用法: try_exact.sh <run_dir> <goal>}"
GOAL="${2:?goal expression required}"

WORKSPACE="$HOME/math-agent-workspace"
TMPFILE=$(mktemp -t try_exact_XXXXX.lean)
trap "rm -f $TMPFILE" EXIT

cat > "$TMPFILE" << EOF
import Mathlib
example : $GOAL := by exact?
EOF

OUTPUT=$(cd "$WORKSPACE" && lake env lean "$TMPFILE" 2>&1 || true)
SUGGESTION=$(echo "$OUTPUT" | grep -oP 'Try this: \K.*' | head -1 || true)

echo "$SUGGESTION"
