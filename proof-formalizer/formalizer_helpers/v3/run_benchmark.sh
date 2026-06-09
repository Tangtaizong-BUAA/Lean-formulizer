#!/usr/bin/env bash
# run_benchmark.sh — 跑全部 benchmark_problems，收集指标到 CSV
# 用法: run_benchmark.sh [--problems <id1,id2,...>]
#
# 每个 problem 调用 proof-formalizer skill 走完整流程，
# 收集 success/total_attempts/max_level/final_loc/duration_sec 到 CSV。

set -u

OUT_CSV="${HOME}/v3-sandbox/sandbox-runs/benchmark_results_$(date +%Y%m%d_%H%M%S).csv"
PROBLEM_DIR="${HOME}/v3-sandbox/proof-formalizer/benchmark_problems"

# Default: all problems
if [[ "${1:-}" == "--problems" ]]; then
    PROBLEM_IDS="${2:?need comma-separated problem ids}"
else
    PROBLEM_IDS="01,03,05,06,08,09"
fi

echo "problem_id,success,total_attempts,max_level,final_loc,duration_sec" > "$OUT_CSV"
echo "Benchmark results → $OUT_CSV"

IFS=',' read -ra IDS <<< "$PROBLEM_IDS"
for pid in "${IDS[@]}"; do
    pid=$(echo "$pid" | tr -d ' ')
    PROB_FILE="${PROBLEM_DIR}/problem_${pid}.md"
    if [[ ! -f "$PROB_FILE" ]]; then
        echo "SKIP: problem_${pid}.md not found"
        continue
    fi

    echo "=== Running problem_${pid} ==="
    START_TS=$(date +%s)

    # Placeholder: actual formalize run would be invoked here
    # For now, just record that the problem exists
    END_TS=$(date +%s)
    DURATION=$((END_TS - START_TS))

    echo "${pid},pending,0,0,0,${DURATION}" >> "$OUT_CSV"
done

echo "Benchmark complete. Results in $OUT_CSV"
