#!/usr/bin/env python3
"""Error classifier for Lean 4 compilation errors.

Classifies stderr output into exactly 15 error classes using regex patterns
matched in priority order (first match wins). Also extracts key_tokens for
fingerprinting and diagnosis.
"""

import json
import re
import sys
from pathlib import Path

# ── Classification rules in priority order (first match wins) ──────────────

RULES = [
    {
        "error_class": "unknown_identifier",
        "pattern": re.compile(
            r"unknown (identifier|constant) ['`]?(\S+?)['`]?", re.IGNORECASE
        ),
        "key_tokens": lambda m: [m.group(2)] if m.lastindex >= 2 else [],
    },
    {
        "error_class": "unknown_namespace",
        "pattern": re.compile(r"unknown namespace '(\S+)'", re.IGNORECASE),
        "key_tokens": lambda m: [m.group(1)],
    },
    {
        "error_class": "type_mismatch",
        "pattern": re.compile(
            r"type mismatch.*?(?:expected\s+(.+?)\s+got\s+(.+?)(?:\s|$)|has type.*?but.*?expected)",
            re.IGNORECASE | re.DOTALL,
        ),
        "key_tokens": lambda m: (
            [m.group(1).strip(), m.group(2).strip()]
            if m.lastindex and m.lastindex >= 2
            else []
        ),
    },
    {
        "error_class": "cast_fail",
        "pattern": re.compile(
            r"(push_cast|exact_mod_cast|mod_cast|norm_cast).*?(fail|error|did not)",
            re.IGNORECASE,
        ),
        "key_tokens": lambda m: [m.group(1)],
    },
    {
        "error_class": "cast_fail",
        "pattern": re.compile(
            r"failed to synthesize.*?CoeT|failed to synthesize.*?Coe",
            re.IGNORECASE | re.DOTALL,
        ),
        "key_tokens": lambda m: [],
    },
    {
        "error_class": "invalid_field",
        "pattern": re.compile(
            r"invalid (field|projection) ['`]?(\S+?)['`]?", re.IGNORECASE
        ),
        "key_tokens": lambda m: [m.group(2)] if m.lastindex >= 2 else [],
    },
    {
        "error_class": "instance_synth_fail",
        "pattern": re.compile(
            r"failed to synthesize.*?instance|typeclass instance problem",
            re.IGNORECASE | re.DOTALL,
        ),
        "key_tokens": lambda m: [],
    },
    {
        "error_class": "rewrite_pattern_fail",
        "pattern": re.compile(
            r"motive is not type correct|rewrite.*?pattern.*?not found", re.IGNORECASE
        ),
        "key_tokens": lambda m: [],
    },
    {
        "error_class": "omega_fail",
        "pattern": re.compile(r"omega (could not prove|failed)", re.IGNORECASE),
        "key_tokens": lambda m: [],
    },
    {
        "error_class": "linarith_fail",
        "pattern": re.compile(r"(?<!n)linarith failed", re.IGNORECASE),
        "key_tokens": lambda m: [],
    },
    {
        "error_class": "nlinarith_fail",
        "pattern": re.compile(r"nlinarith failed", re.IGNORECASE),
        "key_tokens": lambda m: [],
    },
    {
        "error_class": "simp_no_progress",
        "pattern": re.compile(r"simp made no progress", re.IGNORECASE),
        "key_tokens": lambda m: [],
    },
    {
        "error_class": "unsolved_goals",
        "pattern": re.compile(r"unsolved goals", re.IGNORECASE),
        "key_tokens": lambda m: [],
    },
    {
        "error_class": "recursion_depth",
        "pattern": re.compile(
            r"maximum recursion depth|deep recursion", re.IGNORECASE
        ),
        "key_tokens": lambda m: [],
    },
    {
        "error_class": "timeout",
        "pattern": re.compile(
            r"\(deterministic\) timeout|maxHeartbeats|heartbeat", re.IGNORECASE
        ),
        "key_tokens": lambda m: [],
    },
    {
        "error_class": "syntax",
        "pattern": re.compile(r"expected", re.IGNORECASE),
        "key_tokens": lambda m: [],
    },
]


def classify(error_text: str) -> dict:
    """Classify a Lean compilation error.

    Args:
        error_text: The full stderr output from `lake env lean`.

    Returns:
        dict with keys: error_class, key_tokens, raw_excerpt, matched_pattern
    """
    for rule in RULES:
        m = rule["pattern"].search(error_text)
        if m:
            return {
                "error_class": rule["error_class"],
                "key_tokens": rule["key_tokens"](m),
                "raw_excerpt": error_text[:500],
                "matched_pattern": rule["pattern"].pattern,
            }

    return {
        "error_class": "unknown",
        "key_tokens": [],
        "raw_excerpt": error_text[:500],
        "matched_pattern": "fallback",
    }


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    import argparse

    ap = argparse.ArgumentParser(
        description="Classify Lean 4 compilation errors"
    )
    ap.add_argument(
        "error_file",
        nargs="?",
        help="Path to stderr file (reads stdin if omitted or '-')",
    )
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

    result = classify(text)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"error_class: {result['error_class']}")
        print(f"key_tokens:  {result['key_tokens']}")
        print(f"pattern:     {result['matched_pattern']}")
        print(f"excerpt:     {result['raw_excerpt'][:200]}")


# ── Self-tests ──────────────────────────────────────────────────────────────

def run_self_tests():
    """Hard-coded test cases that exercise each error class."""
    tests = [
        # (error_text_snippet, expected_class, expected_min_tokens)
        (
            "unknown identifier 'Nat.gcd_dvd_left'",
            "unknown_identifier",
            1,
        ),
        (
            "Unknown constant `Finset.prod_bij` at ...",
            "unknown_identifier",
            1,
        ),
        (
            "unknown namespace 'Set.mem'",
            "unknown_namespace",
            1,
        ),
        (
            "type mismatch\n  expected\n    ℕ\n  got\n    ℤ",
            "type_mismatch",
            2,
        ),
        (
            "type mismatch, expected ℚ and got ℕ",
            "type_mismatch",
            2,
        ),
        (
            "exact_mod_cast failed to apply",
            "cast_fail",
            1,
        ),
        (
            "mod_cast.fail: mod_cast can't close the goal",
            "cast_fail",
            1,
        ),
        (
            "failed to synthesize instance OfNat (Nat → Nat) 0",
            "instance_synth_fail",
            0,
        ),
        (
            "typeclass instance problem is stuck",
            "instance_synth_fail",
            0,
        ),
        (
            "invalid field 'val'",
            "invalid_field",
            1,
        ),
        (
            "Invalid projection Finset.sum.prop",
            "invalid_field",
            1,
        ),
        (
            "omega could not prove the goal",
            "omega_fail",
            0,
        ),
        (
            "omega failed to find a contradiction",
            "omega_fail",
            0,
        ),
        (
            "linarith failed",
            "linarith_fail",
            0,
        ),
        (
            "nlinarith failed",
            "nlinarith_fail",
            0,
        ),
        (
            "simp made no progress",
            "simp_no_progress",
            0,
        ),
        (
            "unsolved goals: ⊢ 2 ∣ Finset.sum S f",
            "unsolved_goals",
            0,
        ),
        (
            "maximum recursion depth has been reached",
            "recursion_depth",
            0,
        ),
        (
            "(deterministic) timeout at ...",
            "timeout",
            0,
        ),
        (
            "maxHeartbeats limit exceeded",
            "timeout",
            0,
        ),
        (
            "motive is not type correct\n  ...",
            "rewrite_pattern_fail",
            0,
        ),
        (
            "rewrite pattern not found in target",
            "rewrite_pattern_fail",
            0,
        ),
        (
            "expected ':=', '=>', or '|'",
            "syntax",
            0,
        ),
        (
            "syntax error: expected token",
            "syntax",
            0,
        ),
        (
            "some unrecognized error message here",
            "unknown",
            0,
        ),
    ]

    passed = 0
    failed = 0

    for i, (text, expected_class, min_tokens) in enumerate(tests):
        result = classify(text)

        class_ok = result["error_class"] == expected_class
        tokens_ok = len(result["key_tokens"]) >= min_tokens

        status = "PASS" if (class_ok and tokens_ok) else "FAIL"
        if class_ok and tokens_ok:
            passed += 1
        else:
            failed += 1
            print(
                f"FAIL test {i}: got class={result['error_class']} "
                f"(expected {expected_class}), "
                f"tokens={result['key_tokens']} (min {min_tokens})"
            )

    print(f"\nSelf-test: {passed} passed, {failed} failed out of {len(tests)}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
