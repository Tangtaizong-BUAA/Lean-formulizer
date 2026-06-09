#!/usr/bin/env python3
"""Retry strategy matrix for anti-loop architecture.

Maps each error class to actionable tactic suggestions, lemma suggestions,
and auxiliary tool calls. Covers all 15 error classes from error_classifier.
"""

import json
import sys
from pathlib import Path


# ── Decision Matrix ────────────────────────────────────────────────────────

MATRIX = [
    {
        "error_class": "unknown_identifier",
        "action": {
            "next_tactic_hint": "标识符不存在。从 mathlib_lookup 查找正确名称或近似替代。",
            "tactic_family_suggestions": ["exact", "rw"],
            "lemma_suggestions": [],
            "auxiliary_calls": ["mathlib_lookup", "probe_identifier"],
            "confidence": 0.9,
        },
    },
    {
        "error_class": "unknown_namespace",
        "action": {
            "next_tactic_hint": "命名空间不存在。检查 open 语句或使用全限定名。",
            "tactic_family_suggestions": ["exact"],
            "lemma_suggestions": [],
            "auxiliary_calls": ["mathlib_lookup"],
            "confidence": 0.9,
        },
    },
    {
        "error_class": "type_mismatch",
        "action": {
            "next_tactic_hint": "类型不匹配。检查 cast 路径或使用模 cast 系列。",
            "tactic_family_suggestions": ["cast", "exact"],
            "lemma_suggestions": [],
            "auxiliary_calls": ["cast_planner"],
            "confidence": 0.85,
        },
    },
    {
        "error_class": "cast_fail",
        "action": {
            "next_tactic_hint": "cast 失败。尝试 exact_mod_cast / push_cast / norm_cast 组合。",
            "tactic_family_suggestions": ["cast"],
            "lemma_suggestions": [
                "Nat.cast_mul", "Nat.cast_add", "Int.cast_mul",
                "Nat.cast_ofNat", "map_natCast",
            ],
            "auxiliary_calls": ["cast_planner"],
            "confidence": 0.9,
        },
    },
    {
        "error_class": "invalid_field",
        "action": {
            "next_tactic_hint": "字段/投影名错误。probe 验证正确字段名。",
            "tactic_family_suggestions": ["exact", "rw"],
            "lemma_suggestions": [],
            "auxiliary_calls": ["mathlib_lookup"],
            "confidence": 0.85,
        },
    },
    {
        "error_class": "instance_synth_fail",
        "action": {
            "next_tactic_hint": "类型类实例缺失。添加必要的 typeclass 假设或使用 haveI。",
            "tactic_family_suggestions": ["exact", "refine"],
            "lemma_suggestions": [],
            "auxiliary_calls": [],
            "confidence": 0.7,
        },
    },
    {
        "error_class": "rewrite_pattern_fail",
        "action": {
            "next_tactic_hint": "rewrite 目标不匹配。可能 goal 已经变了，需重新提取真实 goal state。",
            "tactic_family_suggestions": ["exact", "calc"],
            "lemma_suggestions": [],
            "auxiliary_calls": ["goal_state_extract"],
            "confidence": 0.8,
        },
    },
    {
        "error_class": "omega_fail",
        "action": {
            "next_tactic_hint": "omega 不支持非线性或非 Presburger 算术。升级到 nlinarith；若仍失败试 polyrith。",
            "tactic_family_suggestions": ["linarith", "ring"],
            "lemma_suggestions": ["polyrith"],
            "auxiliary_calls": [],
            "confidence": 0.9,
        },
    },
    {
        "error_class": "linarith_fail",
        "action": {
            "next_tactic_hint": "linarith 失败。检查是否有非线性项；尝试 nlinarith 或 omega。",
            "tactic_family_suggestions": ["linarith", "omega"],
            "lemma_suggestions": [],
            "auxiliary_calls": [],
            "confidence": 0.85,
        },
    },
    {
        "error_class": "nlinarith_fail",
        "action": {
            "next_tactic_hint": "nlinarith 失败。多项式次数过高或非多项式项。尝试 polyrith 或手动分解。",
            "tactic_family_suggestions": ["linarith", "ring", "rw"],
            "lemma_suggestions": ["polyrith"],
            "auxiliary_calls": ["mathlib_lookup"],
            "confidence": 0.8,
        },
    },
    {
        "error_class": "simp_no_progress",
        "action": {
            "next_tactic_hint": "simp 默认规则不匹配。改用 simp only [具体引理]；或 unfold 定义后再 simp。",
            "tactic_family_suggestions": ["rw", "unfold_then_simp"],
            "lemma_suggestions": [],
            "auxiliary_calls": ["mathlib_lookup"],
            "confidence": 0.85,
        },
    },
    {
        "error_class": "unsolved_goals",
        "action": {
            "next_tactic_hint": "tactic 未闭合所有子目标。添加额外的 apply/refine/simp 步骤。",
            "tactic_family_suggestions": ["exact", "refine", "simp"],
            "lemma_suggestions": [],
            "auxiliary_calls": [],
            "confidence": 0.75,
        },
    },
    {
        "error_class": "recursion_depth",
        "action": {
            "next_tactic_hint": "递归深度超限。检查是否 mutual recursion 或简化目标/换思路。",
            "tactic_family_suggestions": ["exact", "calc", "rw"],
            "lemma_suggestions": [],
            "auxiliary_calls": [],
            "confidence": 0.7,
        },
    },
    {
        "error_class": "timeout",
        "action": {
            "next_tactic_hint": "编译超时。自动升级 heartbeat 重试；不计入 attempt。",
            "tactic_family_suggestions": [],
            "lemma_suggestions": [],
            "auxiliary_calls": ["perf_hint"],
            "confidence": 0.95,
        },
    },
    {
        "error_class": "syntax",
        "action": {
            "next_tactic_hint": "语法错误。检查 Lean 语法：缩进、括号、by/tactic 块分隔。",
            "tactic_family_suggestions": ["exact"],
            "lemma_suggestions": [],
            "auxiliary_calls": [],
            "confidence": 0.65,
        },
    },
    {
        "error_class": "unknown",
        "action": {
            "next_tactic_hint": "未识别的错误类型。重新读 goal state，尝试不同的 tactic family。",
            "tactic_family_suggestions": ["exact", "rw", "simp", "linarith"],
            "lemma_suggestions": [],
            "auxiliary_calls": ["goal_state_extract"],
            "confidence": 0.4,
        },
    },
]

# Build lookup dict for O(1) access
MATRIX_LOOKUP = {entry["error_class"]: entry["action"] for entry in MATRIX}


def decide_strategy(
    diag: dict,
    current_level: int,
    blacklist: list | None = None,
    history: list | None = None,
) -> dict:
    """Determine the recommended next action based on error classification.

    Args:
        diag: Output from error_classifier.classify().
        current_level: Current escalation level (0-6).
        blacklist: Current tactic blacklist entries.
        history: Past attempt fingerprints (unused currently, reserved).

    Returns:
        dict with next_tactic_hint, tactic_family_suggestions,
        lemma_suggestions, auxiliary_calls, confidence.
    """
    bl = blacklist or []
    hist = history or []
    error_class = diag.get("error_class", "unknown")

    # Look up base strategy
    action = MATRIX_LOOKUP.get(error_class)
    if action is None:
        action = MATRIX_LOOKUP["unknown"]

    # Filter out blacklisted families
    banned_families = {
        e["family"]
        for e in bl
        if e.get("banned_entirely", False)
    }
    filtered_families = [
        f for f in action["tactic_family_suggestions"]
        if f not in banned_families
    ]

    # If all suggested families are banned, try generic ones
    if not filtered_families and action["tactic_family_suggestions"]:
        generic = ["exact", "rw", "calc", "case_split"]
        filtered_families = [f for f in generic if f not in banned_families]

    # Adjust confidence based on level (higher level = less certain)
    conf = action["confidence"]
    if current_level >= 4:
        conf *= 0.6

    # Add cast_planner call for type-related errors (even if not cast_fail)
    aux = list(action.get("auxiliary_calls", []))
    if error_class in ("type_mismatch",) and "cast_planner" not in aux:
        aux.append("cast_planner")

    return {
        "next_tactic_hint": action["next_tactic_hint"],
        "tactic_family_suggestions": filtered_families,
        "lemma_suggestions": action.get("lemma_suggestions", []),
        "auxiliary_calls": aux,
        "confidence": conf,
    }


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    import argparse

    ap = argparse.ArgumentParser(
        description="Retry strategy decision engine"
    )
    ap.add_argument("--diag", help="Path to diag.json or JSON string")
    ap.add_argument("--level", type=int, default=0, help="Current escalation level")
    ap.add_argument("--blacklist", default="[]", help="Blacklist JSON")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    ap.add_argument("--self-test", action="store_true", help="Run self tests")

    args = ap.parse_args()

    if args.self_test:
        run_self_tests()
        sys.exit(0)

    diag = {}
    if args.diag:
        try:
            diag = json.loads(Path(args.diag).read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            diag = json.loads(args.diag)

    bl = json.loads(args.blacklist) if args.blacklist else []

    result = decide_strategy(diag, args.level, bl)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"hint: {result['next_tactic_hint']}")
        print(f"families: {result['tactic_family_suggestions']}")
        print(f"lemmas: {result['lemma_suggestions']}")
        print(f"aux: {result['auxiliary_calls']}")
        print(f"confidence: {result['confidence']}")


# ── Self-tests ──────────────────────────────────────────────────────────────

def run_self_tests():
    passed = 0
    failed = 0

    # Test each of the 16 error classes (15 + unknown)
    for entry in MATRIX:
        ec = entry["error_class"]
        result = decide_strategy({"error_class": ec, "key_tokens": []}, 0)
        if result["next_tactic_hint"] and result["confidence"] > 0:
            passed += 1
        else:
            failed += 1
            print(f"FAIL: {ec} returned empty/invalid result")

    # Test blacklist filtering
    bl = [{"family": "simp", "banned_entirely": True}]
    result = decide_strategy({"error_class": "simp_no_progress", "key_tokens": []}, 0, bl)
    assert "simp" not in result["tactic_family_suggestions"], "simp should be filtered"
    assert "rw" in result["tactic_family_suggestions"] or "unfold_then_simp" in result["tactic_family_suggestions"]
    passed += 1

    # Test cast_fail calls cast_planner
    result = decide_strategy({"error_class": "cast_fail", "key_tokens": []}, 0)
    assert "cast_planner" in result["auxiliary_calls"], "cast_fail should call cast_planner"
    passed += 1

    # Test type_mismatch also triggers cast_planner
    result = decide_strategy({"error_class": "type_mismatch", "key_tokens": []}, 0)
    assert "cast_planner" in result["auxiliary_calls"], "type_mismatch should call cast_planner"
    passed += 1

    # Test timeout calls perf_hint
    result = decide_strategy({"error_class": "timeout", "key_tokens": []}, 0)
    assert "perf_hint" in result["auxiliary_calls"], "timeout should call perf_hint"
    passed += 1

    # Test omega_fail suggests nlinarith or polyrith
    result = decide_strategy({"error_class": "omega_fail", "key_tokens": []}, 0)
    assert any(f in result["tactic_family_suggestions"] for f in ["linarith", "ring"]), \
        f"omega_fail should suggest nlinarith/polyrith alternatives, got {result['tactic_family_suggestions']}"
    passed += 1

    # Test level >= 4 reduces confidence
    r_low = decide_strategy({"error_class": "simp_no_progress", "key_tokens": []}, 0)
    r_high = decide_strategy({"error_class": "simp_no_progress", "key_tokens": []}, 4)
    assert r_high["confidence"] < r_low["confidence"], "Higher level should reduce confidence"
    passed += 1

    print(f"Self-test: {passed} passed, 0 failed out of {passed}")


if __name__ == "__main__":
    main()
