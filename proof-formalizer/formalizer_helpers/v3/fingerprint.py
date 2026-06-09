#!/usr/bin/env python3
"""Tactic fingerprint for loop detection.

Generates a stable fingerprint from error class + key tokens + goal shape +
tactic family. Fingerprints that repeat signal a loop, triggering escalation.
"""

import hashlib
import json
import re
import sys
from pathlib import Path


# ── Tactic family classifier ───────────────────────────────────────────────

FAMILY_RULES = [
    ("aesop", re.compile(r"\baesop\b|\btauto\b|\btidy\b")),
    ("omega", re.compile(r"\bomega\b")),
    ("linarith", re.compile(r"\blinarith\b|\bnlinarith\b|\bpolyrith\b")),
    ("ring", re.compile(r"\bring\b|\bring_nf\b|\blinear_combination\b")),
    ("calc", re.compile(r"\bcalc\b")),
    ("decide", re.compile(r"\bdecide\b|\bnative_decide\b|\bDecidable\.decide\b")),
    ("cast", re.compile(r"\bpush_cast\b|\bmod_cast\b|\bexact_mod_cast\b|\bnorm_cast\b")),
    ("rw", re.compile(r"\brw\b|\brewrite\b|\bconv\b")),
    ("simp", re.compile(r"\bsimp_all\b|\bsimp\b")),
    ("exact", re.compile(r"\bexact\b|\bapply\b|\brefine\b|\bexact\?\b|\bapply\?\b")),
    (
        "case_split",
        re.compile(
            r"\brcases\b|\bobtain\b|\bcases\b|\bmatch\b|\binduction\b|\bby_cases\b"
        ),
    ),
]


def classify_tactic_family(tactic: str) -> str:
    """Determine the tactic family from tactic text."""
    for family, pattern in FAMILY_RULES:
        if pattern.search(tactic):
            return family
    return "unknown"


# ── Goal abstraction ───────────────────────────────────────────────────────

# Top-level head symbols to preserve
HEAD_SYMBOLS = [
    "Finset.sum", "Finset.prod", "Nat.gcd", "Nat.lcm", "Nat.Prime",
    "Nat.ModEq", "Int.ModEq", "List.sum", "List.prod", "Set.range",
    "Set.mem", "Measurable", "Continuous", "Differentiable",
    "Polynomial", "Matrix", "ZMod", "Real.log", "Real.exp",
]


def abstract_goal(goal: str) -> str:
    """Abstract a goal string to a stable shape for comparison.

    Steps:
    1. Keep operators: ∣ = ≤ < → ∀ ∃ ∧ ∨ ≠ ≡
    2. Keep top-level head symbols
    3. Replace variable names with type prefixes
    4. Truncate nesting depth to 2
    """
    g = goal.strip()

    # Detect type context for replacement
    # Replace specific numeric/var tokens
    g = re.sub(r"\b\d+\b", "n", g)

    # Replace type-annotated variables: (x : Type) → t-
    g = re.sub(r"\([a-z]\d* : (\w+)\)", r"(t-\1)", g)

    # Replace standalone single-char variables
    g = re.sub(r"\b[a-z]\b", "x", g)
    g = re.sub(r"\b[a-z]'\b", "x'", g)

    # Replace multi-char lowercase identifiers (not head symbols)
    for head in HEAD_SYMBOLS:
        if head in g:
            g = g.replace(head, head.replace(".", "-"))

    # Collapse whitespace
    g = re.sub(r"\s+", " ", g).strip()

    # Truncate depth: keep only first 2 levels of parentheses nesting
    depth = 0
    result = []
    for ch in g:
        if ch == "(" or ch == "{":
            depth += 1
            if depth <= 2:
                result.append(ch)
        elif ch == ")" or ch == "}":
            if depth <= 2:
                result.append(ch)
            depth = max(0, depth - 1)
        else:
            if depth <= 2:
                result.append(ch)
    g = "".join(result)

    # Final cleanup
    g = re.sub(r"\s+", " ", g).strip()
    if len(g) > 100:
        g = g[:100]

    return g


# ── Fingerprint generation ─────────────────────────────────────────────────

def fingerprint(diag: dict, goal_before: str, tactic_used: str) -> str:
    """Generate a stable fingerprint for loop detection.

    fingerprint = sha1(error_class | sorted_key_tokens | goal_shape | tactic_family)

    Args:
        diag: Output from error_classifier.classify()
        goal_before: The goal string before tactic was applied
        tactic_used: The tactic text that was attempted

    Returns:
        A string like "fp_a1b2c3d4"
    """
    err = diag.get("error_class", "unknown")
    tokens = tuple(sorted(diag.get("key_tokens", [])[:5]))
    shape = abstract_goal(goal_before)
    family = classify_tactic_family(tactic_used)

    raw = f"{err}|{','.join(tokens)}|{shape}|{family}"
    h = hashlib.sha1(raw.encode()).hexdigest()[:8]
    return f"fp_{h}"


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    import argparse

    ap = argparse.ArgumentParser(
        description="Generate tactic attempt fingerprints"
    )
    ap.add_argument(
        "--diag",
        help="JSON file or JSON string from error_classifier",
    )
    ap.add_argument("--goal", help="Goal string before tactic")
    ap.add_argument("--tactic", help="Tactic text used")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    ap.add_argument("--self-test", action="store_true", help="Run self tests")

    args = ap.parse_args()

    if args.self_test:
        run_self_tests()
        sys.exit(0)

    if args.diag:
        try:
            diag = json.loads(Path(args.diag).read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            diag = json.loads(args.diag)
    else:
        diag = {"error_class": "unknown", "key_tokens": []}

    fp = fingerprint(diag, args.goal or "", args.tactic or "")

    if args.json:
        print(json.dumps({"fingerprint": fp}, ensure_ascii=False))
    else:
        print(fp)


# ── Self-tests ──────────────────────────────────────────────────────────────

def run_self_tests():
    tests = [
        # (diag, goal, tactic, expected_fp_behavior)
        # Same error + same goal + same family → same fp
        (
            {"error_class": "simp_no_progress", "key_tokens": ["Nat.mod_two"]},
            "2 ∣ Finset.sum S f",
            "simp [Nat.mod_two]",
            "consistent",
        ),
        # Different error → different fp
        (
            {"error_class": "type_mismatch", "key_tokens": ["ℕ", "ℤ"]},
            "2 ∣ Finset.sum S f",
            "simp [Nat.mod_two]",
            "different",
        ),
        # Different tactic family → different fp
        (
            {"error_class": "simp_no_progress", "key_tokens": ["Nat.mod_two"]},
            "2 ∣ Finset.sum S f",
            "omega",
            "different",
        ),
        # Different goal → different fp
        (
            {"error_class": "simp_no_progress", "key_tokens": ["Nat.mod_two"]},
            "a ≡ b [MOD n]",
            "simp [Nat.mod_two]",
            "different",
        ),
    ]

    fps = []
    for diag, goal, tactic, behavior in tests:
        fp = fingerprint(diag, goal, tactic)
        fps.append((fp, behavior))

    # Test 0 and 1 should differ (different error)
    assert fps[0][0] != fps[1][0], "Different errors should produce different fps"

    # Test 0 and 2 should differ (different family)
    assert fps[0][0] != fps[2][0], "Different families should produce different fps"

    # Test 0 and 3 should differ (different goal)
    assert fps[0][0] != fps[3][0], "Different goals should produce different fps"

    # Test consistency: run same input twice
    fp1 = fingerprint({"error_class": "simp_no_progress", "key_tokens": ["Nat.mod_two"]},
                      "2 ∣ Finset.sum S f", "simp [Nat.mod_two]")
    fp2 = fingerprint({"error_class": "simp_no_progress", "key_tokens": ["Nat.mod_two"]},
                      "2 ∣ Finset.sum S f", "simp [Nat.mod_two]")
    assert fp1 == fp2, "Same inputs should produce same fingerprint"

    print("Self-test: All fingerprint tests passed")
    print(f"  consistent: {fps[0][0]}")
    print(f"  different (err): {fps[1][0]}")
    print(f"  different (family): {fps[2][0]}")
    print(f"  different (goal): {fps[3][0]}")
    print(f"  deterministic: {fp1} = {fp2}")


if __name__ == "__main__":
    main()
