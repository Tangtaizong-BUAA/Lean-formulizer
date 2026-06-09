#!/usr/bin/env bash
# auto_solver.sh — 对一个 goal 跑所有自动 tactic，尝试直接闭合
# 用法: auto_solver.sh <goal_type> <ctx_lemmas_json> <output_path>
# goal_type: Lean 目标类型字符串，如 "1 + 1 = 2"
# ctx_lemmas_json: JSON 数组字符串或文件路径（可为 ""）
# output_path: 输出 JSON 文件路径
#
# 输出 JSON:
#   {"solved": true, "tactic": "<找到的 tactic>", "by": "exact?"}
#   {"solved": false, "tactic": null, "tried": ["exact?", "aesop", ...]}
#
# 退出码: 0=solved, 1=unsolved, 2=error

set -u

# ── Self-test mode ────────────────────────────────────────────────────

if [[ "${1:-}" == "--self-test" ]]; then
    echo "=== auto_solver self-test ==="

    TMP_OUT=$(mktemp -t auto_test-XXXXXX)

    # Test 1: Simple equality should be solved
    if bash "$0" "1 + 1 = 2" "[]" "$TMP_OUT"; then
        echo "PASS: test 1 (simple arithmetic)"
    else
        echo "FAIL: test 1 (simple arithmetic should be solvable)"
    fi
    cat "$TMP_OUT"
    echo ""

    # Test 2: False statement should NOT be solved
    if bash "$0" "1 + 1 = 3" "[]" "$TMP_OUT"; then
        echo "FAIL: test 2 (false statement should not be solved)"
    else
        echo "PASS: test 2 (correctly unsolved)"
    fi
    echo ""

    # Test 3: Verify output JSON structure
    bash "$0" "1 + 1 = 2" "[]" "$TMP_OUT"
    python3 -c "
import json
d = json.load(open('$TMP_OUT'))
assert 'solved' in d
assert 'tactic' in d
assert d['solved'] == True
print('PASS: test 3 (JSON structure)')
"

    rm -f "$TMP_OUT"
    echo "=== self-test complete ==="
    exit 0
fi

GOAL="${1:?need goal type string}"
CTX="${2:-[]}"
OUT="${3:?need output path}"

WORKSPACE="$HOME/math-agent-workspace"

# Portability shim for timeout (macOS has no timeout by default)
# Use a function because variable-based shim breaks on nested quoting
_timeout() {
    local sec="$1"; shift
    if command -v gtimeout >/dev/null 2>&1; then
        gtimeout "$sec" "$@"
    elif command -v timeout >/dev/null 2>&1; then
        timeout "$sec" "$@"
    else
        perl -e 'alarm shift @ARGV; exec @ARGV' -- "$sec" "$@"
    fi
}

TIMEOUT_SEC=20

TMPDIR=$(mktemp -d -t auto_solve-XXXXXX)
trap "rm -rf $TMPDIR" EXIT

# Direct tactics that close goals on their own
DIRECT_TACTICS=(
    "aesop"
    "decide"
    "norm_num"
    "omega"
    "linarith"
    "nlinarith"
    "ring"
    "simp_all"
)

# Search tactics that require suggestion extraction and re-verification
# (exact? and apply? just suggest candidates; they don't close goals)
SEARCH_TACTICS=(
    "exact?"
    "apply?"
)

# ── Helper: compile a lean snippet and check if it succeeds ──────────

_compile_ok() {
    local lean_file="$1"
    local stderr_file="$TMPDIR/compile_stderr.txt"
    set +e
    _timeout "$TIMEOUT_SEC" bash -c "cd '$WORKSPACE' && lake env lean '$lean_file'" > "$stderr_file" 2>&1
    local ec=$?
    set -e
    if [ $ec -ne 0 ]; then
        return 1
    fi
    # Also reject output containing "warning" or "sorry"
    if grep -qiE "warning|sorry" "$stderr_file" 2>/dev/null; then
        return 1
    fi
    return 0
}

# ── Try direct tactics first ─────────────────────────────────────────

for T in "${DIRECT_TACTICS[@]}"; do
    TMP_LEAN="$TMPDIR/try_direct.lean"
    cat > "$TMP_LEAN" <<EOF
import Mathlib
example : $GOAL := by $T
EOF

    if _compile_ok "$TMP_LEAN"; then
        FINAL_TACTIC_JSON=$(printf '%s' "$T" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
        printf '{"solved":true,"tactic":%s,"by":"%s"}\n' "$FINAL_TACTIC_JSON" "$T" > "$OUT"
        exit 0
    fi
done

# ── Try search tactics (exact? / apply?) ─────────────────────────────

for T in "${SEARCH_TACTICS[@]}"; do
    TMP_LEAN="$TMPDIR/try_search.lean"
    cat > "$TMP_LEAN" <<EOF
import Mathlib
example : $GOAL := by $T
EOF

    # Run the search tactic (may output "Try this:" suggestions)
    SEARCH_OUT="$TMPDIR/search_output.txt"
    set +e
    _timeout $(($TIMEOUT_SEC * 2)) bash -c "cd '$WORKSPACE' && lake env lean '$TMP_LEAN'" > "$SEARCH_OUT" 2>&1
    _search_ec=$?
    set -e

    # If the search tactic itself succeeded and no errors/warnings/sorry
    if [ $_search_ec -eq 0 ] && ! grep -qiE "(error|warning|sorry)" "$SEARCH_OUT" 2>/dev/null; then
        # The tactic itself closed the goal (unlikely for exact?/apply?, but check)
        FINAL_TACTIC_JSON=$(printf '%s' "$T" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
        printf '{"solved":true,"tactic":%s,"by":"%s"}\n' "$FINAL_TACTIC_JSON" "$T" > "$OUT"
        exit 0
    fi

    # If the search tactic produced suggestions, extract and try each one
    # Use a temp file to avoid subshell issues with pipe
    if grep -q "Try this:" "$SEARCH_OUT" 2>/dev/null; then
        grep "Try this:" "$SEARCH_OUT" | head -5 > "$TMPDIR/suggestions.txt"
        while IFS= read -r line; do
            # Parse: "Try this: exact foo" or "Try this: refine foo" or "Try this: [apply] refine foo"
            SUGGESTION=$(echo "$line" | sed 's/.*Try this:\s*//' | sed 's/\[apply\]\s*//' | tr -d '\n')
            if [ -n "$SUGGESTION" ]; then
                # Re-compile with the suggestion as a tactic
                VERIFY_LEAN="$TMPDIR/verify.lean"
                cat > "$VERIFY_LEAN" <<EOF
import Mathlib
example : $GOAL := by
  $SUGGESTION
EOF
                if _compile_ok "$VERIFY_LEAN"; then
                    FINAL_TACTIC_JSON=$(printf '%s' "$SUGGESTION" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
                    printf '{"solved":true,"tactic":%s,"by":"%s"}\n' "$FINAL_TACTIC_JSON" "$T" > "$OUT"
                    exit 0
                fi
            fi
        done < "$TMPDIR/suggestions.txt"
    fi
done

# ── All failed ───────────────────────────────────────────────────────

ALL_TACTICS=("${DIRECT_TACTICS[@]}" "${SEARCH_TACTICS[@]}")
TRIED_JSON=$(printf '%s\n' "${ALL_TACTICS[@]}" | python3 -c 'import json,sys; print(json.dumps([l.strip() for l in sys.stdin]))')
printf '{"solved":false,"tactic":null,"tried":%s}\n' "$TRIED_JSON" > "$OUT"
exit 1
