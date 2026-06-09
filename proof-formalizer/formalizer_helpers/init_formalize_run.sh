#!/usr/bin/env bash
# init_formalize_run.sh — 初始化 formalize 运行
set -euo pipefail

WORKSPACE="$HOME/math-agent-workspace"
PROBLEM_ID="${1:?用法: init_formalize_run.sh <problem_id>}"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RUN_NAME="formalize_${TIMESTAMP}_${PROBLEM_ID}"
RUN_DIR="${WORKSPACE}/runs/${RUN_NAME}"

mkdir -p "$RUN_DIR/attempts"

cat > "${RUN_DIR}/lessons.md" << 'EOF'
# Lessons (Proof Formalizer)

_Updated after each segment diagnosis._

## Dead Ends
_(none yet)_

## Working Strategies
_(none yet)_

## Traps
_(none yet)_
EOF

echo "$RUN_DIR"
