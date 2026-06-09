#!/usr/bin/env python3
"""Cast planner for automatic diagnosis and repair of type cast errors.

Detects cross-type mismatches (ℕ ↔ ℤ ↔ ℚ ↔ ℝ) in Lean compilation errors
and generates candidate tactic sequences to resolve them.
"""

import json
import re
import sys
from pathlib import Path


# ── Cast diagnosis patterns (ordered by specificity) ──────────────────────

PATTERNS = [
    {
        "trigger": re.compile(
            r"expected\s+ℕ.*?got\s+ℤ", re.IGNORECASE | re.DOTALL
        ),
        "diagnosis": "需要 ℤ→ℕ 转换：用 Int.toNat 或 exact_mod_cast",
        "candidates": [
            "exact_mod_cast",
            "push_cast",
            "apply Int.ofNat_injective; exact_mod_cast",
        ],
        "inserts": [
            {"position": "before_tactic", "content": "have h_cast := ..."},
        ],
    },
    {
        "trigger": re.compile(
            r"expected\s+ℤ.*?got\s+ℕ", re.IGNORECASE | re.DOTALL
        ),
        "diagnosis": "需要 ℕ→ℤ 转换（通常自动，但 explicit cast 可能缺失）",
        "candidates": [
            "push_cast",
            "simp",
            "exact_mod_cast",
        ],
        "inserts": [],
    },
    {
        "trigger": re.compile(
            r"expected\s+ℚ.*?got\s+ℕ", re.IGNORECASE | re.DOTALL
        ),
        "diagnosis": "需要 ℕ→ℚ 转换：使用 Nat.cast 或 field_simp",
        "candidates": [
            "push_cast",
            "simp [Nat.cast_ofNat]",
            "field_simp",
        ],
        "inserts": [],
    },
    {
        "trigger": re.compile(
            r"expected\s+ℚ.*?got\s+ℤ", re.IGNORECASE | re.DOTALL
        ),
        "diagnosis": "需要 ℤ→ℚ 转换",
        "candidates": [
            "push_cast",
            "exact_mod_cast",
            "simp [Int.cast_ofNat]",
        ],
        "inserts": [],
    },
    {
        "trigger": re.compile(
            r"expected\s+ℝ.*?got\s+ℚ", re.IGNORECASE | re.DOTALL
        ),
        "diagnosis": "需要 ℚ→ℝ 转换",
        "candidates": [
            "push_cast",
            "exact_mod_cast",
        ],
        "inserts": [],
    },
    {
        "trigger": re.compile(
            r"⊢.*?↑.*?=.*?↑", re.IGNORECASE
        ),
        "diagnosis": "两边都有 cast 箭头 ↑，先 push_cast 统一再操作",
        "candidates": [
            "push_cast; ring",
            "norm_cast",
            "push_cast; simp",
        ],
        "inserts": [],
    },
    {
        "trigger": re.compile(
            r"failed to synthesize.*?CoeT\s+ℕ\s+ℤ", re.IGNORECASE | re.DOTALL
        ),
        "diagnosis": "Coercion ℕ→ℤ 实例缺失（可能缺少 open 或 import）",
        "candidates": [
            "exact_mod_cast",
            "norm_cast",
            "apply (Nat.cast_injective (R := ℤ))",
        ],
        "inserts": [],
    },
    {
        "trigger": re.compile(
            r"failed to synthesize.*?CoeT\s+ℤ\s+ℚ", re.IGNORECASE | re.DOTALL
        ),
        "diagnosis": "Coercion ℤ→ℚ 实例缺失",
        "candidates": [
            "push_cast",
            "exact_mod_cast",
        ],
        "inserts": [],
    },
    {
        "trigger": re.compile(
            r"Nat\.cast.*?fail|Int\.cast.*?fail", re.IGNORECASE
        ),
        "diagnosis": "Nat.cast / Int.cast 自动转换失败",
        "candidates": [
            "norm_cast",
            "push_cast",
            "exact_mod_cast",
        ],
        "inserts": [],
    },
    {
        "trigger": re.compile(
            r"mod_cast.*?fail|push_cast.*?(fail|error)", re.IGNORECASE
        ),
        "diagnosis": "mod_cast / push_cast 失败，可能需要手动分解类型转换",
        "candidates": [
            "apply_mod_cast",
            "field_simp; ring",
            "simpa [Nat.cast_add, Nat.cast_mul, Nat.cast_ofNat]",
        ],
        "inserts": [],
    },
]


def plan(error_text: str, tactic: str = "", goal: str = "") -> dict:
    """Diagnose cast errors and suggest repair strategies.

    Args:
        error_text: The stderr from lake env lean compilation.
        tactic: The tactic that was attempted (optional).
        goal: The goal before the tactic (optional).

    Returns:
        dict with applicable, diagnosis, suggested_inserts, candidate_tactics.
    """
    for pat in PATTERNS:
        if pat["trigger"].search(error_text):
            return {
                "applicable": True,
                "diagnosis": pat["diagnosis"],
                "suggested_inserts": pat.get("inserts", []),
                "candidate_tactics": pat["candidates"],
            }

    # Check if error contains cross-type keywords (generic fallback)
    # Must match at least two different types to avoid Nat...Nat false positives
    types_found = set(re.findall(r"(Nat|Int|Rat|Real)", error_text))
    if len(types_found) >= 2:
        # Two different types mentioned → likely cast issue
        return {
            "applicable": True,
            "diagnosis": "检测到跨类型错误，尝试 cast 修复",
            "suggested_inserts": [],
            "candidate_tactics": [
                "exact_mod_cast",
                "push_cast",
                "norm_cast",
                "simp [Nat.cast_ofNat, Int.cast_ofNat]",
            ],
        }

    return {
        "applicable": False,
        "diagnosis": "未检测到 cast 相关问题",
        "suggested_inserts": [],
        "candidate_tactics": [],
    }


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    import argparse

    ap = argparse.ArgumentParser(
        description="Cast planner for Lean type cast diagnostics"
    )
    ap.add_argument(
        "error_file",
        nargs="?",
        help="Path to stderr file (reads stdin if omitted or '-')",
    )
    ap.add_argument("--tactic", default="", help="The tactic attempted")
    ap.add_argument("--goal", default="", help="The goal before the tactic")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    ap.add_argument("--self-test", action="store_true", help="Run self tests")

    args = ap.parse_args()

    if args.self_test:
        run_self_tests()
        sys.exit(0)

    if args.error_file and args.error_file != "-":
        text = Path(args.error_file).read_text(encoding="utf-8", errors="replace")
    else:
        text = sys.stdin.read()

    result = plan(text, args.tactic, args.goal)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"applicable: {result['applicable']}")
        print(f"diagnosis: {result['diagnosis']}")
        print(f"candidates: {result['candidate_tactics']}")
        if result["suggested_inserts"]:
            print(f"inserts: {result['suggested_inserts']}")


# ── Self-tests ──────────────────────────────────────────────────────────────

def run_self_tests():
    passed = 0

    # Test 1: ℕ vs ℤ mismatch
    r = plan("type mismatch\n  expected ℕ\n  got ℤ")
    assert r["applicable"], "Should detect ℕ vs ℤ mismatch"
    assert len(r["candidate_tactics"]) >= 1
    passed += 1

    # Test 2: ℚ vs ℕ mismatch
    r = plan("type mismatch, expected ℚ and got ℕ")
    assert r["applicable"], "Should detect ℚ vs ℕ"
    assert "push_cast" in r["candidate_tactics"] or any("push_cast" in c for c in r["candidate_tactics"])
    passed += 1

    # Test 3: Goal with double cast arrows
    r = plan("unsolved goals: ⊢ (↑x : ℚ) = (↑y : ℚ)")
    assert r["applicable"], "Should detect double cast in goal"
    passed += 1

    # Test 4: mod_cast fail
    r = plan("mod_cast failed to apply at line 42")
    assert r["applicable"], "Should detect mod_cast fail"
    passed += 1

    # Test 5: No cast issue
    r = plan("simp made no progress at line 10")
    assert not r["applicable"], "simp_no_progress is not a cast issue"
    passed += 1

    # Test 6: ℤ vs ℕ (reverse direction)
    r = plan("type mismatch\n  expected\n    ℤ\n  got\n    ℕ")
    assert r["applicable"], "Should detect ℤ vs ℕ"
    passed += 1

    # Test 7: Generic cross-type detection
    r = plan("some error involving Nat and Int types")
    assert r["applicable"], "Should detect cross-type keywords"
    passed += 1

    # Test 8: Coercion instance missing
    r = plan("failed to synthesize instance CoeT ℕ ℤ for ...")
    assert r["applicable"], "Should detect CoeT missing"
    passed += 1

    print(f"Self-test: {passed} passed, 0 failed out of 8")


if __name__ == "__main__":
    main()
