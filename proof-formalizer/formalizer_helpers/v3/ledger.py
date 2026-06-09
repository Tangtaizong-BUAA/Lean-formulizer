#!/usr/bin/env python3
"""Attempt Ledger Manager for anti-loop architecture.

Manages the append-only ledger.jsonl for tracking tactic attempts,
segment state persistence, and generates human-readable summaries
for injection into LLM prompts.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


class LedgerManager:
    """Manages attempt ledger and segment state for one segment."""

    def __init__(self, run_dir: Path, segment_id: str):
        self.run_dir = Path(run_dir)
        self.segment_id = segment_id
        self.attempts_dir = self.run_dir / "attempts"
        self.ledger_path = self.attempts_dir / "ledger.jsonl"
        self.state_path = self.run_dir / f"segment_{segment_id}_state.json"

        # Ensure attempts directory exists
        self.attempts_dir.mkdir(parents=True, exist_ok=True)

    # ── Ledger operations ──────────────────────────────────────────────

    def _next_attempt_n(self) -> int:
        """Determine the next attempt number by counting existing ledger lines."""
        if not self.ledger_path.exists():
            return 1
        count = 0
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for _ in f:
                count += 1
        return count + 1

    def append_attempt(self, attempt: dict) -> int:
        """Write an attempt entry to ledger.jsonl.

        Args:
            attempt: Dict with at minimum: attempt_n, segment_id, level,
                     tactic_used, tactic_family, compile_result.

        Returns:
            The attempt_n that was assigned.
        """
        n = self._next_attempt_n()
        attempt["attempt_n"] = n
        attempt["segment_id"] = self.segment_id
        attempt["timestamp"] = datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        # Ensure all required fields exist
        attempt.setdefault("level", 0)
        attempt.setdefault("level_attempt_n", 0)
        attempt.setdefault("goal_before", "")
        attempt.setdefault("goal_before_hash", "")
        attempt.setdefault("tactic_used", "")
        attempt.setdefault("tactic_family", "unknown")
        attempt.setdefault("compile_result", "fail")
        attempt.setdefault("error_text_excerpt", "")
        attempt.setdefault("error_class", "unknown")
        attempt.setdefault("key_tokens", [])
        attempt.setdefault("fingerprint", "")
        attempt.setdefault("duration_ms", 0)
        attempt.setdefault("diagnosis_path", f"attempts/{n:02d}_diag.json")
        attempt.setdefault("tactic_path", f"attempts/{n:02d}_tactic.lean")
        attempt.setdefault("stderr_path", f"attempts/{n:02d}_stderr.txt")

        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(attempt, ensure_ascii=False) + "\n")

        return n

    def read_all(self) -> list[dict]:
        """Read all attempts for this segment from ledger.jsonl."""
        if not self.ledger_path.exists():
            return []
        results = []
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    if entry.get("segment_id") == self.segment_id:
                        results.append(entry)
        return results

    def summarize_for_prompt(self, max_chars: int = 2000) -> str:
        """Generate a human-readable summary for injection into LLM prompt.

        Args:
            max_chars: Maximum character length of summary.

        Returns:
            Markdown formatted summary string.
        """
        attempts = self.read_all()
        state = self.read_segment_state()

        n = len(attempts)
        cur_level = state.get("current_level", 0)
        total = state.get("total_attempts", 0)

        # Inline ladder data to avoid circular import
        _LADDER_LOCAL = [
            {"level": 0, "name": "tweak", "budget": 1},
            {"level": 1, "name": "switch_within", "budget": 2},
            {"level": 2, "name": "switch_family", "budget": 2},
            {"level": 3, "name": "lemma_rotate", "budget": 2},
            {"level": 4, "name": "replan", "budget": 1},
            {"level": 5, "name": "resegment", "budget": 1},
            {"level": 6, "name": "help_request", "budget": 0},
        ]
        level_name = _LADDER_LOCAL[cur_level]["name"] if cur_level < 7 else "help_request"
        level_budget = _LADDER_LOCAL[cur_level]["budget"] if cur_level < 7 else 0

        # Build summary
        lines = [
            f"## Attempt Ledger（Segment {self.segment_id}，已用 {total}/9 attempts）",
            f"",
            f"**当前 Level**：{cur_level} ({level_name}) — "
            f"已用 {state.get('level_attempts_used', {}).get(str(cur_level), 0)}/{level_budget}",
            f"",
        ]

        # Fingerprint history
        fp_hist = state.get("fingerprint_history", [])
        if fp_hist:
            lines.append("**Fingerprint 历史**：")
            for i, fp in enumerate(fp_hist[-10:]):
                att_idx = max(0, n - len(fp_hist) + i)
                is_repeat = i > 0 and fp == fp_hist[i - 1] if i < len(fp_hist) else False
                mark = " ← 重复" if is_repeat else ""
                lines.append(f"- Attempt {att_idx + 1}: {fp}{mark}")
            lines.append("")

        # Blacklist
        bl = state.get("blacklist", [])
        if bl:
            lines.append("**Tactic 黑名单**（禁止再用，包括语义变体）：")
            for entry in bl:
                banned_note = " (整 family 已 ban)" if entry.get("banned_entirely") else ""
                specifics = ", ".join(f"`{s}`" for s in entry.get("specific", []))
                lines.append(f"- {entry['family']} family{banned_note}: {specifics}")
            lines.append("")

        # Most recent failure
        if attempts:
            last = attempts[-1]
            if last.get("compile_result") == "fail":
                lines.append("**最近一次失败**：")
                lines.append(f"- Tactic: `{last.get('tactic_used', '?')}`")
                lines.append(f"- Error: {last.get('error_text_excerpt', '?')[:120]}")
                lines.append(f"- Goal: `{last.get('goal_before', '?')[:120]}`")
                lines.append("")

        # Last escalation reason
        # (derived from state transitions — approximate)
        last_reason = state.get("last_escalation_reason", "")
        if last_reason:
            lines.append(f"**升级原因**：{last_reason}")
            lines.append("")

        # What to do now
        allowed = state.get("allowed_families", [])
        if cur_level < 6 and allowed:
            lines.append("**本次必须**：")
            lines.append(f"1. 候选 family：{' / '.join(allowed[:5])}")
            lines.append("2. 不许再生成上面黑名单中的 tactic")

        summary = "\n".join(lines)
        if len(summary) > max_chars:
            summary = summary[: max_chars - 3] + "..."

        return summary

    # ── Segment state operations ───────────────────────────────────────

    def read_segment_state(self) -> dict:
        """Read segment_state.json, returning defaults if not found or corrupt."""
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, FileNotFoundError, ValueError):
                pass  # Corrupt or empty → return defaults

        return {
            "segment_id": self.segment_id,
            "current_level": 0,
            "level_attempts_used": {},
            "blacklist": [],
            "fingerprint_history": [],
            "total_attempts": 0,
            "status": "in_progress",
            "last_tactic": "",
            "last_goal": "",
        }

    def update_segment_state(self, **kwargs) -> dict:
        """Update segment_state.json fields and return new state.

        Kwargs can be any field from the state schema.
        Uses atomic write (temp file + rename) to prevent corruption.
        """
        state = self.read_segment_state()
        state.update(kwargs)
        state["segment_id"] = self.segment_id
        # Atomic write: temp file then rename
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        tmp.replace(self.state_path)
        return state

    # ── Per-attempt file helpers ───────────────────────────────────────

    def write_attempt_files(
        self,
        attempt_n: int,
        tactic_lean: str,
        stderr: str,
        diag: dict,
        prompt_summary: str = "",
    ):
        """Write the 4 required per-attempt files.

        Args:
            attempt_n: Attempt number (1-based).
            tactic_lean: The complete working.lean content for this attempt.
            stderr: The full stderr from compilation.
            diag: Error classifier output dict.
            prompt_summary: The prompt fed to the LLM for this attempt.
        """
        prefix = self.attempts_dir / f"{attempt_n:02d}"

        (prefix.parent / f"{attempt_n:02d}_tactic.lean").write_text(tactic_lean)
        (prefix.parent / f"{attempt_n:02d}_stderr.txt").write_text(stderr)
        (prefix.parent / f"{attempt_n:02d}_diag.json").write_text(
            json.dumps(diag, ensure_ascii=False, indent=2)
        )
        if prompt_summary:
            (prefix.parent / f"{attempt_n:02d}_prompt.md").write_text(prompt_summary)


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    import argparse

    ap = argparse.ArgumentParser(
        description="Attempt ledger manager"
    )
    ap.add_argument("--run-dir", required=True, help="Run directory path")
    ap.add_argument("--segment-id", default="01", help="Segment ID")
    ap.add_argument("--action", default="summarize",
                    choices=["summarize", "read-state", "read-all", "init"],
                    help="Action to perform")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    ap.add_argument("--self-test", action="store_true", help="Run self tests")

    # Check for --self-test early, before required arg validation
    if "--self-test" in sys.argv:
        run_self_tests()
        sys.exit(0)

    args = ap.parse_args()

    mgr = LedgerManager(Path(args.run_dir), args.segment_id)

    if args.action == "init":
        state = mgr.update_segment_state(
            current_level=0, total_attempts=0, status="in_progress"
        )
        print(json.dumps(state, ensure_ascii=False, indent=2))

    elif args.action == "summarize":
        summary = mgr.summarize_for_prompt()
        print(summary)

    elif args.action == "read-state":
        state = mgr.read_segment_state()
        print(json.dumps(state, ensure_ascii=False, indent=2))

    elif args.action == "read-all":
        attempts = mgr.read_all()
        print(json.dumps(attempts, ensure_ascii=False, indent=2))


# ── Self-tests ──────────────────────────────────────────────────────────────

def run_self_tests():
    import tempfile
    import shutil

    passed = 0
    failed = 0

    tmpdir = Path(tempfile.mkdtemp(prefix="ledger_test_"))
    try:
        run_dir = tmpdir / "test_run"
        mgr = LedgerManager(run_dir, "03")

        # Test 1: Init creates state
        state = mgr.update_segment_state(current_level=0, total_attempts=0,
                                         status="in_progress")
        assert state["segment_id"] == "03"
        assert state["current_level"] == 0
        assert mgr.state_path.exists()
        passed += 1

        # Test 2: Append attempt
        n = mgr.append_attempt({
            "level": 0,
            "tactic_used": "simp [Nat.mod_two]",
            "tactic_family": "simp",
            "compile_result": "fail",
            "error_class": "simp_no_progress",
            "key_tokens": ["Nat.mod_two"],
            "fingerprint": "fp_a1b2c3d4",
        })
        assert n == 1
        assert mgr.ledger_path.exists()
        passed += 1

        # Test 3: Read all
        attempts = mgr.read_all()
        assert len(attempts) == 1
        assert attempts[0]["tactic_used"] == "simp [Nat.mod_two]"
        passed += 1

        # Test 4: Append second attempt
        mgr.update_segment_state(
            total_attempts=1,
            level_attempts_used={"0": 1},
            fingerprint_history=["fp_a1b2c3d4"],
            current_level=1,
        )
        n = mgr.append_attempt({
            "level": 1,
            "tactic_used": "omega",
            "tactic_family": "omega",
            "compile_result": "fail",
            "error_class": "omega_fail",
            "key_tokens": [],
            "fingerprint": "fp_e5f6g7h8",
        })
        assert n == 2
        passed += 1

        # Test 5: Summarize for prompt
        mgr.update_segment_state(
            total_attempts=2,
            blacklist=[
                {"family": "simp", "specific": ["simp [Nat.mod_two]"],
                 "banned_entirely": True},
                {"family": "omega", "specific": ["omega"]},
            ],
            fingerprint_history=["fp_a1b2c3d4", "fp_e5f6g7h8"],
        )
        summary = mgr.summarize_for_prompt()
        assert "Segment 03" in summary
        assert "已用 2/9" in summary
        assert "simp" in summary
        assert "omega" in summary
        passed += 1

        # Test 6: Write attempt files
        mgr.write_attempt_files(
            1,
            "import Mathlib\nexample : 1 = 1 := rfl",
            "some error text",
            {"error_class": "simp_no_progress", "key_tokens": []},
            "# Prompt summary",
        )
        assert (mgr.attempts_dir / "01_tactic.lean").exists()
        assert (mgr.attempts_dir / "01_stderr.txt").exists()
        assert (mgr.attempts_dir / "01_diag.json").exists()
        assert (mgr.attempts_dir / "01_prompt.md").exists()
        passed += 1

        # Test 7: Second attempt_n is sequential
        mgr.append_attempt({
            "level": 0,
            "tactic_used": "rw [add_comm]",
            "tactic_family": "rw",
            "compile_result": "fail",
            "error_class": "rewrite_pattern_fail",
        })
        attempts = mgr.read_all()
        assert len(attempts) == 3
        assert attempts[2]["attempt_n"] == 3
        passed += 1

        # Test 8: Fresh LedgerManager has empty ledger
        mgr2 = LedgerManager(run_dir, "99")
        assert mgr2.read_all() == []
        state = mgr2.read_segment_state()
        assert state["segment_id"] == "99"
        assert state["current_level"] == 0
        passed += 1

    finally:
        shutil.rmtree(tmpdir)

    print(f"Self-test: {passed} passed, 0 failed out of 8")


if __name__ == "__main__":
    main()
