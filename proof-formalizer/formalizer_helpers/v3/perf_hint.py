#!/usr/bin/env python3
"""Performance hint manager for Lean 4 heartbeat/timeout handling.

Automatically escalates `maxHeartbeats` option when compilation times out,
without counting the timeout as a failed attempt.
"""

import json
import re
import sys
from pathlib import Path

HEARTBEAT_LADDER = [200_000, 400_000, 800_000, 1_000_000]
MAX_HEARTBEAT = HEARTBEAT_LADDER[-1]

TIMEOUT_PATTERNS = [
    r"\(deterministic\) timeout",
    r"maxHeartbeats",
    r"heartbeat.*(exceeded|limit|maximum)",
    r"deep recursion",
]


def is_timeout_error(stderr: str) -> bool:
    """Check if a compilation error is a timeout/heartbeat issue.

    Args:
        stderr: The compilation stderr output.

    Returns:
        True if this is a performance-related error that should not count
        as a semantic failure.
    """
    return any(re.search(p, stderr, re.IGNORECASE) for p in TIMEOUT_PATTERNS)


def get_current_heartbeat(lean_text: str) -> int:
    """Extract current heartbeat setting from lean file text.

    Returns 0 if no set_option maxHeartbeats is found.
    """
    m = re.search(r"set_option\s+maxHeartbeats\s+(\d+)", lean_text)
    if m:
        return int(m.group(1))
    return 0


def get_next_heartbeat(current: int) -> int | None:
    """Get the next heartbeat value in the ladder.

    Returns None if already at maximum.
    """
    if current == 0:
        return HEARTBEAT_LADDER[0]
    if current >= MAX_HEARTBEAT:
        return None
    for hb in HEARTBEAT_LADDER:
        if hb > current:
            return hb
    return None


def inject_heartbeat(lean_file: Path, hb: int):
    """Insert or replace maxHeartbeats option in a Lean file.

    Inserts after the last 'import' line, or replaces existing setting.

    Args:
        lean_file: Path to the .lean file.
        hb: The heartbeat value to set.
    """
    text = lean_file.read_text(encoding="utf-8", errors="replace")

    if "maxHeartbeats" in text:
        # Replace existing setting
        text = re.sub(
            r"set_option\s+maxHeartbeats\s+\d+",
            f"set_option maxHeartbeats {hb}",
            text,
        )
    else:
        # Insert after last import line
        lines = text.split("\n")
        last_import = max(
            (i for i, l in enumerate(lines) if l.strip().startswith("import")),
            default=-1,
        )
        if last_import >= 0:
            lines.insert(last_import + 1, "")
            lines.insert(last_import + 1, f"set_option maxHeartbeats {hb}")
        else:
            # No import line found — insert at beginning
            lines.insert(0, f"set_option maxHeartbeats {hb}")
        text = "\n".join(lines)

    lean_file.write_text(text, encoding="utf-8")


def handle_timeout(lean_file: Path, stderr: str) -> dict:
    """Handle a timeout by escalating heartbeat if possible.

    Args:
        lean_file: Path to the working.lean file.
        stderr: The compilation stderr.

    Returns:
        dict with keys: escalated, new_heartbeat, exhausted.
    """
    if not is_timeout_error(stderr):
        return {"escalated": False, "new_heartbeat": 0, "exhausted": False}

    text = lean_file.read_text(encoding="utf-8", errors="replace")
    current = get_current_heartbeat(text)
    next_hb = get_next_heartbeat(current)

    if next_hb is None:
        return {"escalated": False, "new_heartbeat": current, "exhausted": True}

    inject_heartbeat(lean_file, next_hb)
    return {"escalated": True, "new_heartbeat": next_hb, "exhausted": False}


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    import argparse

    ap = argparse.ArgumentParser(
        description="Performance hint manager for Lean 4"
    )
    ap.add_argument("--lean-file", help="Path to working.lean")
    ap.add_argument(
        "--stderr", help="Path to stderr file (or '-' for stdin)"
    )
    ap.add_argument("--check-only", action="store_true", help="Only check if timeout")
    ap.add_argument("--get-current-hb", action="store_true", help="Print current heartbeat")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    ap.add_argument("--self-test", action="store_true", help="Run self tests")

    args = ap.parse_args()

    if args.self_test:
        run_self_tests()
        sys.exit(0)

    if args.get_current_hb and args.lean_file:
        text = Path(args.lean_file).read_text()
        print(get_current_heartbeat(text))
        return

    if args.check_only and args.stderr:
        if args.stderr == "-":
            text = sys.stdin.read()
        else:
            text = Path(args.stderr).read_text()
        result = {"is_timeout": is_timeout_error(text)}
        if args.json:
            print(json.dumps(result))
        else:
            print(f"is_timeout: {result['is_timeout']}")
        return

    if args.lean_file and args.stderr:
        if args.stderr == "-":
            stderr = sys.stdin.read()
        else:
            stderr = Path(args.stderr).read_text()

        result = handle_timeout(Path(args.lean_file), stderr)

        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(f"escalated: {result['escalated']}")
            print(f"new_heartbeat: {result['new_heartbeat']}")
            print(f"exhausted: {result['exhausted']}")


# ── Self-tests ──────────────────────────────────────────────────────────────

def run_self_tests():
    import tempfile, shutil

    tmpdir = Path(tempfile.mkdtemp(prefix="ph_test_"))
    passed = 0

    try:
        # Test 1: is_timeout_error
        assert is_timeout_error("(deterministic) timeout at line 42")
        assert is_timeout_error("maxHeartbeats limit exceeded")
        assert is_timeout_error("heartbeat limit exceeded at line 42")
        assert not is_timeout_error("simp made no progress")
        passed += 1

        # Test 2: get_current_heartbeat
        assert get_current_heartbeat("set_option maxHeartbeats 400000") == 400000
        assert get_current_heartbeat("import Mathlib\nset_option maxHeartbeats 200000") == 200000
        assert get_current_heartbeat("import Mathlib\nexample : 1=1 := rfl") == 0
        passed += 1

        # Test 3: get_next_heartbeat
        assert get_next_heartbeat(0) == 200000
        assert get_next_heartbeat(200000) == 400000
        assert get_next_heartbeat(400000) == 800000
        assert get_next_heartbeat(800000) == 1_000_000
        assert get_next_heartbeat(1_000_000) is None
        assert get_next_heartbeat(2_000_000) is None
        passed += 1

        # Test 4: inject_heartbeat (new file, no existing)
        f = tmpdir / "test.lean"
        f.write_text("import Mathlib\n\nexample : 1=1 := rfl\n")
        inject_heartbeat(f, 200000)
        text = f.read_text()
        assert "maxHeartbeats 200000" in text
        passed += 1

        # Test 5: inject_heartbeat (replace existing)
        f.write_text("import Mathlib\nset_option maxHeartbeats 100000\n\nexample : 1=1 := rfl\n")
        inject_heartbeat(f, 400000)
        text = f.read_text()
        assert "maxHeartbeats 400000" in text
        assert "maxHeartbeats 100000" not in text
        passed += 1

        # Test 6: handle_timeout on real file
        f.write_text("import Mathlib\n\nexample : 1=1 := rfl\n")
        result = handle_timeout(f, "(deterministic) timeout")
        assert result["escalated"] is True
        assert result["new_heartbeat"] == 200000
        assert result["exhausted"] is False
        text = f.read_text()
        assert "maxHeartbeats 200000" in text
        passed += 1

        # Test 7: handle_timeout at max
        f.write_text("import Mathlib\nset_option maxHeartbeats 1000000\n\nexample : 1=1 := rfl\n")
        result = handle_timeout(f, "(deterministic) timeout")
        assert result["exhausted"] is True
        passed += 1

        # Test 8: handle_timeout non-timeout error
        f.write_text("import Mathlib\n\nexample : 1=1 := rfl\n")
        result = handle_timeout(f, "simp made no progress")
        assert result["escalated"] is False
        passed += 1

    finally:
        shutil.rmtree(tmpdir)

    print(f"Self-test: {passed} passed, 0 failed out of 8")


if __name__ == "__main__":
    main()
