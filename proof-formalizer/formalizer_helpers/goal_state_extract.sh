#!/usr/bin/env bash
# goal_state_extract.sh — 提取当前 goal state
#
# 用法: bash goal_state_extract.sh <run_dir> <lean_file> [after_line_number]
#
# 策略：编译含 sorry 的文件，Lean 会在 "unsolved goals" 错误中打印 goal
# 输出: goal state（纯文本）
set -euo pipefail

RUN_DIR="${1:?用法: goal_state_extract.sh <run_dir> <lean_file> [after_line]}"
LEAN_FILE="${2:?lean file path required}"
AFTER_LINE="${3:-0}"

WORKSPACE="$HOME/math-agent-workspace"
BUILD_SCRIPT="$HOME/.claude/skills/math-thinking-flow/lean_helpers/build_and_parse.sh"

# 复制到工作区
cp "$LEAN_FILE" "$WORKSPACE/MathAgent/Scratch.lean"

# 编译
BUILD_OUTPUT=$(bash "$BUILD_SCRIPT" Scratch 2>&1 || true)

# 从编译输出提取 goal state
# 格式通常是：
#   case ...
#   a b : ℤ
#   h : ...
#   ⊢ <goal>
GOAL_STATE=""
if echo "$BUILD_OUTPUT" | grep -q "unsolved goals\|unsolved goal"; then
  # 提取 ⊢ 开头的行及上面的上下文
  GOAL_STATE=$(echo "$BUILD_OUTPUT" | grep -A 5 "unsolved goal" | grep -E '⊢|: ' | head -10 || true)
fi

# 如果有多个 sorry，可能需要更精确的行号过滤
if [ "$AFTER_LINE" -gt 0 ]; then
  GOAL_STATE=$(echo "$BUILD_OUTPUT" | awk "/Scratch.lean:${AFTER_LINE}:/,/⊢/" | head -10 || true)
fi

echo "$GOAL_STATE"
