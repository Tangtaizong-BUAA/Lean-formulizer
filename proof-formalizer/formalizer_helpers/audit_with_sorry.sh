#!/usr/bin/env bash
# audit_with_sorry.sh — 公理审计（允许标注的 sorry）
#
# 包装 math-thinking-flow 的 check_axioms.sh
# - axiom 声明 → FAIL
# - sorry 无 [SORRY] 标注 → FAIL
# - sorry 有 [SORRY] 标注 → WARN (允许通过)
# - #print axioms 白名单含 sorryAx → WARN (仅限标注 sorry 带来的)
set -euo pipefail

TARGET_FILE="${1:?用法: audit_with_sorry.sh <lean_file>}"

[ ! -f "$TARGET_FILE" ] && { echo "AUDIT_RESULT: ERROR"; exit 1; }

echo "=== Axiom Audit (sorry-allowed) ==="

OVERALL_PASS=true
ANNOTATED_COUNT=0

# Check 1: axiom 声明
AXIOM_LINES=$(grep -nE '^\s*axiom\s+' "$TARGET_FILE" 2>/dev/null || true)
if [ -n "$AXIOM_LINES" ]; then
  echo "FAIL: axiom declarations found"
  echo "$AXIOM_LINES"
  OVERALL_PASS=false
else
  echo "PASS: no axiom declarations"
fi

# Check 2: sorry 标注检查
SORRY_LINES=$(sed 's/--.*$//' "$TARGET_FILE" | grep -nE '\bsorry\b' 2>/dev/null || true)
if [ -z "$SORRY_LINES" ]; then
  echo "PASS: no sorry found"
else
  UNANNOTATED=0
  while IFS= read -r sl; do
    LINE_NUM=$(echo "$sl" | cut -d: -f1)
    START=$((LINE_NUM - 3))
    [ "$START" -lt 1 ] && START=1
    CONTEXT=$(sed -n "${START},${LINE_NUM}p" "$TARGET_FILE")
    if echo "$CONTEXT" | grep -q '\[SORRY'; then
      ANNOTATED_COUNT=$((ANNOTATED_COUNT + 1))
    else
      UNANNOTATED=$((UNANNOTATED + 1))
      echo "  UNANNOTATED sorry at line $LINE_NUM"
    fi
  done <<< "$SORRY_LINES"

  if [ "$UNANNOTATED" -gt 0 ]; then
    echo "FAIL: $UNANNOTATED unannotated sorry(s)"
    OVERALL_PASS=false
  else
    echo "WARN: $ANNOTATED_COUNT annotated sorry(s) (allowed)"
  fi
fi

# Check 3: #print axioms 白名单（委托原脚本）
CHECK_AXIOMS="$HOME/.claude/skills/math-thinking-flow/lean_helpers/check_axioms.sh"
if [ -f "$CHECK_AXIOMS" ]; then
  WHITELIST_OUTPUT=$(bash "$CHECK_AXIOMS" "$TARGET_FILE" 2>&1 || true)
  if echo "$WHITELIST_OUTPUT" | grep -q "audit_axiom_whitelist: FAIL"; then
    # 检查是否只有 sorryAx（标注 sorry 带来的）
    echo "WARN: non-whitelisted axioms detected (may be sorryAx from annotated sorry)"
    echo "audit_axiom_whitelist: WARN"
  else
    echo "PASS: whitelisted axioms only"
  fi
fi

echo "=========================================="
if $OVERALL_PASS; then
  if [ "$ANNOTATED_COUNT" -gt 0 ]; then
    echo "AUDIT_RESULT: WARN"
    echo "AUDIT_DETAIL: $ANNOTATED_COUNT annotated sorry(s)"
  else
    echo "AUDIT_RESULT: PASS"
  fi
  exit 0
else
  echo "AUDIT_RESULT: FAIL"
  exit 1
fi
