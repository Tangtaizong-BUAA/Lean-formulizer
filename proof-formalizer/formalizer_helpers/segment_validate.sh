#!/usr/bin/env bash
# segment_validate.sh — 验证单个 segment
#
# 用法: bash segment_validate.sh <run_dir> <segment_id> <attempt_id>
set -euo pipefail

RUN_DIR="${1:?用法: segment_validate.sh <run_dir> <seg_id> <attempt_id>}"
SEG_ID="${2:?segment_id required}"
ATTEMPT_ID="${3:-1}"

WORKSPACE="$HOME/math-agent-workspace"
BUILD_SCRIPT="$HOME/.claude/skills/math-thinking-flow/lean_helpers/build_and_parse.sh"
AUDIT_SCRIPT="$HOME/.claude/skills/proof-formalizer/formalizer_helpers/audit_with_sorry.sh"
ATTEMPT_FILE="${RUN_DIR}/attempts/segment_${SEG_ID}_attempt_${ATTEMPT_ID}.lean"
RESULT_FILE="${RUN_DIR}/attempts/segment_${SEG_ID}_attempt_${ATTEMPT_ID}_result.json"

[ -f "$ATTEMPT_FILE" ] || { echo "{\"success\":false,\"compile_errors\":[\"attempt file not found\"]}"; exit 1; }

cp "$ATTEMPT_FILE" "$WORKSPACE/MathAgent/Scratch.lean"

BUILD_OUTPUT=$(bash "$BUILD_SCRIPT" Scratch 2>&1 || true)

if echo "$BUILD_OUTPUT" | grep -q "SUCCESS: true"; then
  COMPILE_SUCCESS="true"
else
  COMPILE_SUCCESS="false"
fi

# sorry 计数与标注检查
SORRY_COUNT=0
SORRY_ANNOTATED="true"
if [ -f "$ATTEMPT_FILE" ]; then
  SORRY_COUNT=$(grep -cE '\bsorry\b' "$ATTEMPT_FILE" || true)
  if [ "$SORRY_COUNT" -gt 0 ]; then
    # 检查每个 sorry 前几行是否有 [SORRY
    while IFS= read -r line_num; do
      START=$((line_num - 3))
      [ "$START" -lt 1 ] && START=1
      CONTEXT=$(sed -n "${START},${line_num}p" "$ATTEMPT_FILE")
      if ! echo "$CONTEXT" | grep -q '\[SORRY'; then
        SORRY_ANNOTATED="false"
      fi
    done < <(grep -nE '\bsorry\b' "$ATTEMPT_FILE" | cut -d: -f1)
  fi
fi

# 公理审计
AUDIT_RESULT="SKIP"
if [ "$COMPILE_SUCCESS" = "true" ]; then
  AUDIT_OUTPUT=$(bash "$AUDIT_SCRIPT" "$ATTEMPT_FILE" 2>&1 || true)
  if echo "$AUDIT_OUTPUT" | grep -q "AUDIT_RESULT: FAIL"; then
    AUDIT_RESULT="FAIL"
  elif echo "$AUDIT_OUTPUT" | grep -q "AUDIT_RESULT: WARN"; then
    AUDIT_RESULT="WARN"
  else
    AUDIT_RESULT="PASS"
  fi
fi

# Goal state 提取
GOAL_AFTER=""
if [ "$COMPILE_SUCCESS" = "false" ]; then
  GOAL_AFTER=$(echo "$BUILD_OUTPUT" | grep -o '⊢.*' | head -3 | tr '\n' ';' | head -c 500 || true)
fi

# 写入 JSON
cat > "$RESULT_FILE" << EOF
{
  "segment_id": "${SEG_ID}",
  "attempt_id": "${ATTEMPT_ID}",
  "success": ${COMPILE_SUCCESS},
  "compile_errors": $(echo "$BUILD_OUTPUT" | grep "error:" | head -5 | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))'),
  "sorry_count": ${SORRY_COUNT},
  "sorry_annotated": ${SORRY_ANNOTATED},
  "audit_result": "${AUDIT_RESULT}",
  "goal_state_after": "${GOAL_AFTER}"
}
EOF

echo "Result: $RESULT_FILE"
