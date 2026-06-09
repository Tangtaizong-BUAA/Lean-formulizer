#!/usr/bin/env bash
# 验证 Mathlib 标识符存在性
# 用法：probe_identifier.sh <identifier>
# 输出：JSON
#   FOUND:     {"status": "found", "name": "...", "signature": "..."}
#   NOT_FOUND: {"status": "not_found", "name": "...", "suggestions": ["...", ...]}
#   ERROR:     {"status": "error", "message": "..."}

set -u

IDENT="${1:?need identifier}"
WORKSPACE="$HOME/math-agent-workspace"
TMPDIR=$(mktemp -d -t probe-XXXXXX)
trap "rm -rf $TMPDIR" EXIT

# 写临时 .lean 做 #check
TMP_LEAN="$TMPDIR/probe.lean"
cat > "$TMP_LEAN" <<EOF
import Mathlib
#check @${IDENT}
EOF

# 编译
cd "$WORKSPACE"
OUTPUT=$(lake env lean "$TMP_LEAN" 2>&1 || true)

# 解析输出
if echo "$OUTPUT" | grep -q "error"; then
    # 未找到，尝试从报错中提取建议
    # 方法 1: Lean 的 "did you mean" 报错
    SUGGESTIONS=$(echo "$OUTPUT" | grep -oE "did you mean '[^']+'" | sed "s/did you mean '//; s/'//" | head -5 | tr '\n' '|' | sed 's/|$//' || true)

    # 方法 1b: Lean 4 的 "unknown identifier, possible interpretations" 格式
    if [[ -z "$SUGGESTIONS" ]]; then
        SUGGESTIONS=$(echo "$OUTPUT" | grep -oE "  [a-zA-Z][a-zA-Z0-9_']*(\.[a-zA-Z][a-zA-Z0-9_']*)*" | head -5 | tr '\n' '|' | sed 's/|$//' || true)
    fi

    # 方法 2: 向量检索拿相似名
    if [[ -z "$SUGGESTIONS" ]]; then
        QUERY=$(echo "$IDENT" | sed 's/\./ /g; s/_/ /g')
        SEARCHD="$HOME/.claude/skills/proof-formalizer/formalizer_helpers/searchd.sh"

        _extract_names() {
            python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    names = [d['name'] for d in data if d.get('name')][:5]
    print('|'.join(names))
except:
    pass" 2>/dev/null || echo ""
        }

        # 方案 A: curl daemon（模型常驻，零加载开销）
        if [[ -x "$SEARCHD" ]]; then
            SUGGESTIONS=$("$SEARCHD" search "$QUERY" 5 2>/dev/null | _extract_names)
        fi

        # 方案 B: 直接 oneshot CLI
        if [[ -z "$SUGGESTIONS" ]]; then
            PY="$HOME/mathlib-rag/venv/bin/python3"
            SEARCH="$HOME/mathlib-rag/scripts/search.py"
            if [[ -x "$PY" && -f "$SEARCH" ]]; then
                SUGGESTIONS=$("$PY" "$SEARCH" "$QUERY" -k 5 --json 2>/dev/null | _extract_names)
            fi
        fi
    fi

    # 输出 JSON
    SUGG_JSON=$(echo -n "$SUGGESTIONS" | python3 -c "
import json, sys
s = sys.stdin.read()
arr = [x for x in s.split('|') if x]
print(json.dumps(arr))
")

    printf '{"status":"not_found","name":"%s","suggestions":%s}\n' "$IDENT" "$SUGG_JSON"
else
    # 找到了，提取完整签名（多行）
    SIG=$(echo "$OUTPUT" | sed -n '/^@/,/^$/p' | head -20)
    if [[ -z "$SIG" ]]; then
        SIG=$(echo "$OUTPUT" | head -5 | tr '\n' ' ')
    fi

    # 同时提取 docstring（如果有）
    DOC=$(echo "$OUTPUT" | grep -A 5 "^/--" | head -10 || echo "")
    if [[ -z "$DOC" ]]; then
        DOC=""
    fi

    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # 写入 probe_signatures.json（若环境变量已设置）
    if [[ -n "${PROBE_SIG_FILE:-}" ]]; then
        SIG_JSON=$(printf '%s' "$SIG" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read()))")
        DOC_JSON=$(printf '%s' "$DOC" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read()))")
        TIMESTAMP_JSON=$(printf '%s' "$TIMESTAMP" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read()))")
        IDENT_JSON=$(printf '%s' "$IDENT" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read()))")

        python3 - <<PYEOF
import json
from pathlib import Path
f = Path("${PROBE_SIG_FILE}")
data = {}
if f.exists():
    try:
        data = json.loads(f.read_text() or "{}")
    except (json.JSONDecodeError, ValueError):
        data = {}
data[${IDENT_JSON}] = {
    "signature": ${SIG_JSON},
    "docstring": ${DOC_JSON},
    "timestamp": ${TIMESTAMP_JSON}
}
f.write_text(json.dumps(data, ensure_ascii=False, indent=2))
PYEOF
    fi

    # 仍然输出 v2 兼容的 JSON 到 stdout
    SIG_JSON_OUT=$(printf '%s' "$SIG" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read()))")
    printf '{"status":"found","name":"%s","signature":%s}\n' "$IDENT" "$SIG_JSON_OUT"
fi
