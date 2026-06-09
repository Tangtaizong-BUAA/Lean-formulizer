#!/usr/bin/env python3
"""Escalation ladder for anti-loop architecture.

Implements a 7-level escalation ladder that forces the tactic generation
strategy to upgrade when loops are detected. The ladder ensures that at most
9 attempts total are made before forcing a help_request.

Levels:
  0: tweak          (budget 1) — tweak same tactic parameters
  1: switch_within  (budget 2) — switch within same tactic family
  2: switch_family  (budget 2) — switch to different tactic family
  3: lemma_rotate   (budget 2) — rotate mathlib lookup candidates
  4: replan         (budget 1) — re-read goal + new plan
  5: resegment      (budget 1) — split segment
  6: help_request   (budget 0) — stop and request human help
"""

import json
import sys
from pathlib import Path

LADDER = [
    {"level": 0, "name": "tweak", "budget": 1,
     "desc": "微调同 tactic 参数"},
    {"level": 1, "name": "switch_within", "budget": 2,
     "desc": "同 family 内切换"},
    {"level": 2, "name": "switch_family", "budget": 2,
     "desc": "切换 tactic family"},
    {"level": 3, "name": "lemma_rotate", "budget": 2,
     "desc": "换 mathlib_lookup 候选"},
    {"level": 4, "name": "replan", "budget": 1,
     "desc": "重读 goal + 新规划"},
    {"level": 5, "name": "resegment", "budget": 1,
     "desc": "拆分 segment"},
    {"level": 6, "name": "help_request", "budget": 0,
     "desc": "中断写 help_request"},
]

GLOBAL_BUDGET = sum(l["budget"] for l in LADDER[:6])  # = 9


def decide_next_level(state: dict, last_diag: dict | None = None) -> tuple[int, str]:
    """Determine the next escalation level.

    Args:
        state: The segment state dict from segment_state.json.
        last_diag: The most recent error classification dict (or None for first attempt).

    Returns:
        (next_level, reason) tuple.
    """
    cur = state.get("current_level", 0)
    fp_hist = state.get("fingerprint_history", [])

    # Rule A: global budget exhausted → Level 6
    if state.get("total_attempts", 0) >= GLOBAL_BUDGET:
        return (6, "global_budget_exhausted")

    # Rule B: current level budget exhausted → escalate
    cur_used_str = str(cur)
    cur_used = state.get("level_attempts_used", {}).get(cur_used_str, 0)
    if cur >= len(LADDER):
        return (6, "invalid_level")
    if cur_used >= LADDER[cur]["budget"]:
        return (cur + 1, "level_budget_exhausted")

    # Rule C: repeated fingerprint 2+ times → force escalate
    if len(fp_hist) >= 2 and fp_hist[-1] == fp_hist[-2]:
        return (cur + 1, "fingerprint_repeated_2x")

    # Rule D: error class implies jump
    if last_diag:
        err_class = last_diag.get("error_class", "unknown")
        if err_class == "timeout":
            return (cur, "timeout_not_counted")
        if err_class == "recursion_depth":
            return (cur, "recursion_depth_not_counted")
        if err_class == "rewrite_pattern_fail" and cur < 4:
            return (4, "rewrite_pattern_implies_stale_goal")

    return (cur, "stay_within_budget")


def update_blacklist(
    state: dict, last_tactic: str, last_family: str, escalated: bool
) -> dict:
    """Update the tactic blacklist.

    Always adds specific failed tactic.
    If escalated=True, bans the entire family.

    Args:
        state: The segment state dict (mutated in place).
        last_tactic: The specific tactic text that failed.
        last_family: The tactic family name.
        escalated: Whether escalation occurred on this attempt.

    Returns:
        The updated state dict.
    """
    bl = state.setdefault("blacklist", [])

    fam_entry = next((e for e in bl if e["family"] == last_family), None)
    if fam_entry is None:
        fam_entry = {"family": last_family, "specific": []}
        bl.append(fam_entry)

    if last_tactic not in fam_entry["specific"]:
        fam_entry["specific"].append(last_tactic)

    if escalated:
        fam_entry["banned_entirely"] = True

    return state


def get_allowed_families(state: dict) -> list[str]:
    """Get list of tactic families not blacklisted."""
    all_families = [
        "simp", "omega", "linarith", "ring", "rw", "exact",
        "cast", "decide", "aesop", "case_split", "calc",
    ]
    bl = state.get("blacklist", [])
    banned = {e["family"] for e in bl if e.get("banned_entirely")}
    return [f for f in all_families if f not in banned]


def get_banned_specifics(state: dict) -> list[str]:
    """Get list of banned specific tactic strings."""
    bl = state.get("blacklist", [])
    result = []
    for entry in bl:
        result.extend(entry.get("specific", []))
    return result


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    import argparse

    ap = argparse.ArgumentParser(
        description="Escalation ladder decision engine"
    )
    ap.add_argument(
        "--state",
        help="Path to segment_state.json",
    )
    ap.add_argument(
        "--diag",
        help="Path to last diag.json (optional)",
    )
    ap.add_argument(
        "--next-level-only",
        action="store_true",
        help="Output only the next level number",
    )
    ap.add_argument("--json", action="store_true", help="Output JSON")
    ap.add_argument("--self-test", action="store_true", help="Run self tests")

    args = ap.parse_args()

    if args.self_test:
        run_self_tests()
        sys.exit(0)

    state = {}
    if args.state:
        sp = Path(args.state)
        if sp.exists():
            state = json.loads(sp.read_text())

    diag = None
    if args.diag:
        dp = Path(args.diag)
        if dp.exists():
            diag = json.loads(dp.read_text())

    next_level, reason = decide_next_level(state, diag)

    if args.next_level_only:
        print(next_level)
    elif args.json:
        print(
            json.dumps(
                {
                    "next_level": next_level,
                    "reason": reason,
                    "budget_remaining": GLOBAL_BUDGET - state.get("total_attempts", 0),
                    "allowed_families": get_allowed_families(state),
                    "banned_specifics": get_banned_specifics(state),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"next_level: {next_level}")
        print(f"reason: {reason}")
        print(f"budget_remaining: {GLOBAL_BUDGET - state.get('total_attempts', 0)}")
        print(f"allowed_families: {get_allowed_families(state)}")
        print(f"banned_specifics: {get_banned_specifics(state)}")


# ── Self-tests ──────────────────────────────────────────────────────────────

def run_self_tests():
    passed = 0
    failed = 0

    # Test 1: Fresh state → Level 0
    state = {"current_level": 0, "total_attempts": 0, "level_attempts_used": {},
             "fingerprint_history": [], "blacklist": []}
    lvl, reason = decide_next_level(state, None)
    assert lvl == 0, f"Fresh state should be level 0, got {lvl}"
    assert reason == "stay_within_budget", f"Got {reason}"
    passed += 1

    # Test 2: Level 0 budget used → Level 1
    state = {"current_level": 0, "total_attempts": 1, "level_attempts_used": {"0": 1},
             "fingerprint_history": ["fp_a1b2c3d4"], "blacklist": []}
    lvl, reason = decide_next_level(state, {"error_class": "simp_no_progress"})
    assert lvl == 1, f"Budget used should escalate to 1, got {lvl}"
    assert reason == "level_budget_exhausted"
    passed += 1

    # Test 3: Repeated fingerprint → escalate
    state = {"current_level": 0, "total_attempts": 1, "level_attempts_used": {"0": 0},
             "fingerprint_history": ["fp_a1b2c3d4", "fp_a1b2c3d4"], "blacklist": []}
    lvl, reason = decide_next_level(state, {"error_class": "simp_no_progress"})
    assert lvl == 1, f"Repeated fp should escalate to 1, got {lvl}"
    assert reason == "fingerprint_repeated_2x"
    passed += 1

    # Test 4: Global budget exhausted → Level 6
    state = {"current_level": 0, "total_attempts": 9, "level_attempts_used": {"0": 0},
             "fingerprint_history": [], "blacklist": []}
    lvl, reason = decide_next_level(state, None)
    assert lvl == 6, f"Budget 9 should be help_request, got {lvl}"
    assert reason == "global_budget_exhausted"
    passed += 1

    # Test 5: Total attempts 8 with budget available → stay
    state = {"current_level": 2, "total_attempts": 8, "level_attempts_used": {"2": 0},
             "fingerprint_history": ["fp_a", "fp_b", "fp_c"], "blacklist": []}
    lvl, reason = decide_next_level(state, {"error_class": "simp_no_progress"})
    assert lvl == 2, f"Should stay at level 2, got {lvl}"
    passed += 1

    # Test 6: Timeout not counted as failure (stays at current level)
    state = {"current_level": 0, "total_attempts": 0, "level_attempts_used": {"0": 0},
             "fingerprint_history": [], "blacklist": []}
    lvl, reason = decide_next_level(state, {"error_class": "timeout"})
    assert lvl == 0, f"Timeout should stay at level 0, got {lvl}"
    assert reason == "timeout_not_counted"
    passed += 1

    # Test 7: rewrite_pattern_fail jump to level 4
    state = {"current_level": 0, "total_attempts": 0, "level_attempts_used": {"0": 0},
             "fingerprint_history": [], "blacklist": []}
    lvl, reason = decide_next_level(state, {"error_class": "rewrite_pattern_fail"})
    assert lvl == 4, f"Rewrite fail should jump to 4, got {lvl}"
    assert reason == "rewrite_pattern_implies_stale_goal"
    passed += 1

    # Test 8: Level 2 budget exhausted → Level 3
    state = {"current_level": 2, "total_attempts": 4, "level_attempts_used": {"0": 1, "1": 1, "2": 2},
             "fingerprint_history": ["fp_a", "fp_b", "fp_c", "fp_d"], "blacklist": []}
    lvl, reason = decide_next_level(state, {"error_class": "simp_no_progress"})
    assert lvl == 3, f"Level 2 exhausted should go to 3, got {lvl}"
    passed += 1

    # Test 9: blacklist update with escalation
    state = {"current_level": 0, "total_attempts": 0, "level_attempts_used": {"0": 0},
             "fingerprint_history": [], "blacklist": []}
    update_blacklist(state, "simp [Nat.mod_two]", "simp", escalated=True)
    assert state["blacklist"][0]["banned_entirely"] is True
    assert "simp [Nat.mod_two]" in state["blacklist"][0]["specific"]
    passed += 1

    # Test 10: blacklist update without escalation
    state = {"current_level": 0, "total_attempts": 0, "level_attempts_used": {"0": 0},
             "fingerprint_history": [], "blacklist": []}
    update_blacklist(state, "simp [Nat.mod_two]", "simp", escalated=False)
    assert state["blacklist"][0].get("banned_entirely", False) is False
    assert len(state["blacklist"][0]["specific"]) == 1
    passed += 1

    # Test 11: 12 attempts simulation → must hit level 6 by attempt 9
    attempt_count = 0
    state = {"current_level": 0, "total_attempts": 0,
             "level_attempts_used": {}, "fingerprint_history": [], "blacklist": []}
    fp_seq = ["fp_a", "fp_a", "fp_b", "fp_b", "fp_c", "fp_c",
              "fp_d", "fp_d", "fp_e", "fp_e", "fp_f", "fp_f"]
    max_level = 0
    for i in range(12):
        state["total_attempts"] = i
        state["fingerprint_history"].append(fp_seq[i])
        state["fingerprint_history"] = state["fingerprint_history"][-20:]
        lvl_str = str(state["current_level"])
        state["level_attempts_used"][lvl_str] = state["level_attempts_used"].get(lvl_str, 0) + 1
        lvl, reason = decide_next_level(state, {"error_class": "simp_no_progress"})
        max_level = max(max_level, lvl)
        state["current_level"] = lvl
        attempt_count += 1
        if lvl == 6:
            break

    assert attempt_count <= 9, f"Should reach help_request by attempt 9, got {attempt_count}"
    assert max_level >= 6, f"Max level should be 6, got {max_level}"
    passed += 1

    print(f"Self-test: {passed} passed, 0 failed out of {passed}")


if __name__ == "__main__":
    main()
