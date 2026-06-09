#!/usr/bin/env bash
# mathlib_lookup.sh — 三路检索 Mathlib 引理
#
# 用法: bash mathlib_lookup.sh <run_dir> <segment_id> [goal_type_string] [keywords_json]
#
# 输出: JSON 数组到 stdout，含 Top-5 候选
#   [{"name":"...","signature":"...","source":"...","score":0.8}, ...]
set -u

RUN_DIR="${1:?用法: mathlib_lookup.sh <run_dir> <segment_id> [goal] [keywords]}"
SEG_ID="${2:?segment_id required}"
GOAL_TYPE="${3:-}"
KEYWORDS_JSON="${4:-[]}"

WORKSPACE="$HOME/math-agent-workspace"
MATHLIB_SRC="${WORKSPACE}/.lake/packages/mathlib/Mathlib"
CANONICAL_DIR="$HOME/.claude/skills/proof-formalizer/canonical_proofs"
HELPERS_DIR="$HOME/.claude/skills/proof-formalizer/formalizer_helpers"
SEARCHD="$HELPERS_DIR/searchd.sh"
RESULTS=()

# Route 0: Dense vector search (bge-m3 + FAISS)
search_dense() {
    local query="$1"
    local k="${2:-10}"
    local py="$HOME/mathlib-rag/venv/bin/python3"
    local script="$HOME/mathlib-rag/scripts/search.py"

    if [[ ! -x "$py" ]] || [[ ! -f "$script" ]]; then
        echo "[]"
        return
    fi

    # 方案 A: curl daemon（模型常驻，零加载开销）
    if [[ -x "$SEARCHD" ]]; then
        local result
        result=$("$SEARCHD" search "$query" "$k" 2>/dev/null)
        if echo "$result" | python3 -c "import json; json.load(sys.stdin)" 2>/dev/null; then
            echo "$result"
            return
        fi
    fi

    # 方案 B: 直接 oneshot CLI（daemon 不可用时）
    "$py" "$script" "$query" -k "$k" --json 2>/dev/null || echo "[]"
}

# Route 1: exact? (如果提供了 goal_type)
if [ -n "$GOAL_TYPE" ]; then
  TMPFILE=$(mktemp -t exact_lookup_XXXXX.lean)
  cat > "$TMPFILE" << LEANEOF
import Mathlib
example : $GOAL_TYPE := by exact?
LEANEOF
  EXACT_OUTPUT=$(cd "$WORKSPACE" && lake env lean "$TMPFILE" 2>&1 || true)
  # 解析 "Try this: ..." 建议
  SUGGESTION=$(echo "$EXACT_OUTPUT" | sed -n 's/.*Try this: //p' | head -1 || true)
  if [ -n "$SUGGESTION" ]; then
    RESULTS+=("{\"name\":\"exact?\",\"signature\":\"$SUGGESTION\",\"source\":\"exact?_suggestion\",\"score\":1.2}")
  fi
  rm -f "$TMPFILE"
fi

# Route 2: grep Mathlib 源码
# 从 keywords_json 提取关键词（简单实现：去引号和方括号，按逗号分词）
KEYWORDS=$(echo "$KEYWORDS_JSON" | tr -d '[]"' | tr ',' ' ')
for KW in $KEYWORDS; do
  [ -z "$KW" ] && continue
  GREP_RESULTS=$(grep -rn "theorem\|lemma" "$MATHLIB_SRC" 2>/dev/null | grep -i "$KW" | head -5 || true)
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    THM_NAME=$(echo "$line" | sed -n 's/.*\(theorem\|lemma\)[[:space:]]*\([^[:space:]]*\).*/\2/p' | head -1 || true)
    [ -z "$THM_NAME" ] && continue
    SRC_PATH=$(echo "$line" | cut -d: -f1 | sed "s|$MATHLIB_SRC/||")
    RESULTS+=("{\"name\":\"$THM_NAME\",\"signature\":\"\",\"source\":\"$SRC_PATH\",\"score\":0.5}")  # grep score: 0.5
  done <<< "$GREP_RESULTS"
  # 最多取前 10 条结果
  [ ${#RESULTS[@]} -ge 10 ] && break
done

# Route 3: canonical_proofs 关键词搜索
for KW in $KEYWORDS; do
  [ -z "$KW" ] && continue
  CANON_GREP=$(grep -rni "$KW" "$CANONICAL_DIR" 2>/dev/null | head -3 || true)
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    CANON_FILE=$(echo "$line" | cut -d: -f1 | sed "s|$CANONICAL_DIR/||")
    CANON_ID=$(echo "$line" | sed -n 's/.*\([A-Z]*-[0-9]*\).*/\1/p' | head -1 || true)
    RESULTS+=("{\"name\":\"$CANON_ID\",\"signature\":\"\",\"source\":\"canonical_proofs/$CANON_FILE\",\"score\":1.5}")  # canonical score: 1.5
  done <<< "$CANON_GREP"
done

# Route 4: Dense vector search (bge-m3 + FAISS)
# Build step-context queries matching V2 training distribution (EN + ZH dual query)
QUERIES_JSON=$(python3 "$HELPERS_DIR/build_step_context_queries.py" "$GOAL_TYPE" "$KEYWORDS_JSON" 2>/dev/null || echo '{}')
EN_QUERY=$(echo "$QUERIES_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin).get('en',''))" 2>/dev/null)
ZH_QUERY=$(echo "$QUERIES_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin).get('zh',''))" 2>/dev/null)

# Search with both EN and ZH queries, merge results
for DENSE_QUERY in "$EN_QUERY" "$ZH_QUERY"; do
  [ -z "$DENSE_QUERY" ] && continue
  DENSE_RESULTS=$(search_dense "$DENSE_QUERY" 10)
  DENSE_COUNT=$(echo "$DENSE_RESULTS" | python3 -c "import json,sys; arr=json.load(sys.stdin); print(len(arr))" 2>/dev/null || echo 0)
  for i in $(seq 0 $((DENSE_COUNT - 1))); do
    ITEM=$(echo "$DENSE_RESULTS" | python3 -c "
import json, sys
arr = json.load(sys.stdin)
if $i < len(arr):
    d = arr[$i]
    d['score'] = d.get('score', 0) * 1.0
    d['source'] = 'dense_search'
    print(json.dumps(d, ensure_ascii=False))
" 2>/dev/null || true)
    if [ -n "$ITEM" ]; then
      RESULTS+=("$ITEM")
    fi
  done
done

# 合并去重，取 Top-5
# 按 score 排序去重（同名取最高分），取前 5
if [ ${#RESULTS[@]} -eq 0 ]; then
  echo "[]"
else
  # 用 Python 做合并去重排序
  echo "${RESULTS[@]}" | python3 -c "
import json, sys
items = []
for line in sys.stdin:
    for token in line.strip().split('{'):
        token = token.strip()
        if not token or token == '[':
            continue
        token = '{' + token
        # 修复可能的拼接问题
        while token.count('{') > token.count('}'):
            token += '}'
        try:
            d = json.loads(token.rstrip(',').rstrip(']'))
            items.append(d)
        except:
            pass

# 去重（按 name 取最高分）
by_name = {}
for d in items:
    name = d.get('name', '')
    score = d.get('score', 0)
    if name not in by_name or score > by_name[name].get('score', 0):
        by_name[name] = d

# 按 score 降序排列
sorted_items = sorted(by_name.values(), key=lambda x: x.get('score', 0), reverse=True)[:5]
print(json.dumps(sorted_items, ensure_ascii=False))
" 2>/dev/null || echo "[]"
fi
