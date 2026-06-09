#!/usr/bin/env bash
# searchd.sh — Mathlib dense search daemon 管理
#
# 用法:
#   searchd.sh start   → 启动 search.py --server（如已运行则跳过）
#   searchd.sh stop    → 关闭 daemon
#   searchd.sh status  → 检查 daemon 是否健康（返回 0=运行中，非 0=未运行）
#   searchd.sh ensure  → 确保 daemon 运行，必要时启动（适合脚本调用）
#   searchd.sh search "query" [k] → curl 快捷搜索，输出 JSON
#
# 端口: 8321

set -u

PORT=8321
HOST="localhost"
SEARCH_URL="http://${HOST}:${PORT}/search"
PYTHON="$HOME/mathlib-rag/venv/bin/python3"
SEARCH_PY="$HOME/mathlib-rag/scripts/search.py"
PID_FILE="$HOME/.claude/skills/proof-formalizer/formalizer_helpers/.searchd.pid"
LOG_FILE="$HOME/.claude/skills/proof-formalizer/formalizer_helpers/.searchd.log"

_health_check() {
    # 快速健康检查：curl 一个简单 query，超时 2s
    curl -s --max-time 2 "${SEARCH_URL}?q=health_check&k=1" > /dev/null 2>&1
}

_cleanup_stale_pid() {
    if [ -f "$PID_FILE" ]; then
        local old_pid
        old_pid=$(cat "$PID_FILE" 2>/dev/null || true)
        if [ -n "${old_pid:-}" ] && ! kill -0 "${old_pid}" 2>/dev/null; then
            rm -f "$PID_FILE"
        fi
    fi
}

cmd_start() {
    if _health_check; then
        echo "searchd already running on port $PORT"
        return 0
    fi

    _cleanup_stale_pid

    echo "Starting searchd on port $PORT..."
    nohup "$PYTHON" "$SEARCH_PY" --server --port "$PORT" > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_FILE"

    # Wait for server to be ready (up to 120 seconds)
    local waited=0
    while [ $waited -lt 120 ]; do
        if _health_check; then
            echo "searchd ready (pid=$pid, waited ${waited}s)"
            return 0
        fi
        sleep 2
        waited=$((waited + 2))
    done

    echo "ERROR: searchd failed to start within 120s"
    return 1
}

cmd_stop() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            echo "searchd stopped (pid=$pid)"
        fi
        rm -f "$PID_FILE"
    else
        # Try to find by port
        local pid
        pid=$(lsof -ti ":$PORT" 2>/dev/null || true)
        if [ -n "${pid:-}" ]; then
            kill "$pid" 2>/dev/null || true
            echo "searchd stopped (pid=$pid, found by port)"
        else
            echo "searchd not running"
        fi
    fi
}

cmd_status() {
    if _health_check; then
        echo "searchd: running on port $PORT"
        return 0
    else
        echo "searchd: not running"
        return 1
    fi
}

cmd_ensure() {
    # 确保 daemon 运行——适合被其他脚本调用
    if _health_check; then
        return 0
    fi
    cmd_start
}

cmd_search() {
    # curl 搜索，返回 JSON 到 stdout
    local query="${1:?need query}"
    local k="${2:-10}"
    cmd_ensure || { echo "[]"; return 1; }
    curl -s --max-time 30 "${SEARCH_URL}?q=$(echo "$query" | python3 -c 'import sys,urllib.parse; print(urllib.parse.quote(sys.stdin.read()))')&k=$k" || echo "[]"
}

case "${1:-}" in
    start)   cmd_start ;;
    stop)    cmd_stop ;;
    status)  cmd_status ;;
    ensure)  cmd_ensure ;;
    search)  cmd_search "${2:-}" "${3:-10}" ;;
    *)
        echo "Usage: searchd.sh {start|stop|status|ensure|search <query> [k]}"
        exit 1
        ;;
esac
