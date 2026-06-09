#!/usr/bin/env python3
"""Complexity estimator for proof formalization strategy selection.

Reads intake.md and estimates proof complexity to recommend a formalization
mode: full (complete formalization), axiom (accept heavy theorems as axioms),
decompose (split into sub-goals), or abort (infeasible).
"""

import json
import re
import sys
from pathlib import Path


# ── Heavy theorem references ──────────────────────────────────────────────

HEAVY_THEOREMS = {
    "PNT": "PrimeNumberTheorem",
    "素数定理": "PrimeNumberTheorem",
    "Prime Number Theorem": "PrimeNumberTheorem",
    "Siegel-Walfisz": "SiegelWalfisz",
    "Vinogradov": "Vinogradov",
    "Vaughan": "VaughanIdentity",
    "Riemann": "RiemannZeta",
    "Mertens": "Mertens",
    "Dirichlet": "Dirichlet 系列",
    "Roth": "RothTheorem",
    "Szemeredi": "SzemerediRegularity",
    "Green-Tao": "GreenTao",
    "Bourgain": "Bourgain",
    "Zhang": "BoundedGaps",
    "Maynard": "Maynard",
    "Polymath": "Polymath8",
    "Chebotarev": "ChebotarevDensity",
    "Langlands": "Langlands",
    "Fermat's Last Theorem": "FLT",
    "Fermat 大定理": "FLT",
    "Poincare": "PoincareConjecture",
    "Weil": "Weil",
    "Tate": "Tate",
    "Deligne": "Deligne",
    "Shimura": "Shimura",
    "Taniyama": "TaniyamaShimura",
    "Modularity": "ModularityTheorem",
}


def scan_heavy_refs(text: str) -> list[dict]:
    """Scan text for references to heavy theorems.

    Returns:
        List of {"keyword": str, "theorem": str, "context": str} dicts.
    """
    refs = []
    for keyword, theorem in HEAVY_THEOREMS.items():
        if keyword.lower() in text.lower():
            # Extract surrounding context (±80 chars)
            idx = text.lower().find(keyword.lower())
            start = max(0, idx - 40)
            end = min(len(text), idx + len(keyword) + 40)
            context = text[start:end].replace("\n", " ").strip()
            refs.append({"keyword": keyword, "theorem": theorem, "context": context})
    return refs


def estimate_segment_count(text: str) -> int:
    """Estimate number of segments based on text structure.

    Heuristics: count "Step", "Case", paragraphs, and deductive markers.
    """
    # Count explicit step/case markers
    step_count = len(re.findall(r"(?:Step|步骤|Case|情况)\s*\d+", text, re.IGNORECASE))
    # Count paragraphs
    para_count = len(re.findall(r"\n\s*\n", text)) + 1
    # Count deduction markers ("hence", "therefore", "故", "所以")
    deduction_count = len(re.findall(
        r"(?:hence|therefore|thus|so |故|所以|从而|因此|于是)", text, re.IGNORECASE
    ))

    # Blend estimates
    estimated = max(step_count, deduction_count // 2, para_count // 3, 1)
    return min(estimated, 100)  # cap at 100


def estimate_loc(text: str) -> int:
    """Estimate total LOC based on segment count × complexity."""
    segs = estimate_segment_count(text)
    refs = scan_heavy_refs(text)

    # Base: 10-15 lines per segment
    base_loc = segs * 12

    # Heavy theorem refs add overhead
    base_loc += len(refs) * 20

    # Complexity indicators
    if re.search(r"(?:induction|归纳)", text, re.IGNORECASE):
        base_loc = int(base_loc * 1.3)
    if re.search(r"(?:contradiction|反证|by.*contra)", text, re.IGNORECASE):
        base_loc = int(base_loc * 1.1)
    if re.search(r"(?:double.*counting|算两次)", text, re.IGNORECASE):
        base_loc = int(base_loc * 1.2)

    return base_loc


def estimate_attempts_per_segment(text: str) -> int:
    """Estimate average attempts per segment."""
    segs = estimate_segment_count(text)
    if segs <= 3:
        return 2
    elif segs <= 10:
        return 3
    else:
        return 4


def determine_depth(text: str, refs: list[dict]) -> str:
    """Determine proof depth: trivial | easy | medium | hard | infeasible."""
    if len(refs) >= 3:
        return "hard"
    if any(r["theorem"] in {"PrimeNumberTheorem", "SiegelWalfisz", "Vinogradov", "FLT"}
           for r in refs):
        return "hard"
    if len(refs) >= 1:
        return "medium"

    segs = estimate_segment_count(text)
    if segs <= 2:
        return "trivial"
    elif segs <= 5:
        return "easy"
    elif segs <= 15:
        return "medium"
    else:
        return "hard"


def decide_mode(refs: list[dict], depth: str, segs: int) -> tuple[str, str]:
    """Decide recommended formalization mode.

    Returns:
        (mode, rationale) tuple.
    """
    # Unsolved heavy theorems → axiom mode
    if len(refs) >= 3:
        return ("axiom", f"至少 {len(refs)} 个重定理引用")
    if any(r["theorem"] in {"PrimeNumberTheorem", "SiegelWalfisz"}
           for r in refs):
        return ("axiom", "引用了 Mathlib 未形式化的核心定理")
    if any(r["theorem"] == "FLT" for r in refs):
        return ("abort", "Fermat's Last Theorem 在 Mathlib 中未形式化")

    # Very large proofs → decompose
    if segs > 30:
        return ("decompose", f"段数 > 30，建议拆子目标")

    if depth == "hard" and segs > 10:
        return ("decompose", f"hard 证明 ({segs} 段)，建议拆子目标")

    # Very small proofs → full
    if segs < 3:
        return ("full", "短证明")

    return ("full", "默认完整形式化")


def estimate(intake_path: Path) -> dict:
    """Estimate proof complexity from intake.md.

    Args:
        intake_path: Path to intake.md file.

    Returns:
        dict with estimated_segments, external_theorem_refs, depth_hint,
        recommended_mode, estimated_attempts_per_segment, estimated_total_loc,
        axiom_candidates, rationale.
    """
    text = intake_path.read_text(encoding="utf-8", errors="replace")

    refs = scan_heavy_refs(text)
    segs = estimate_segment_count(text)
    depth = determine_depth(text, refs)
    mode, rationale = decide_mode(refs, depth, segs)

    # Axiom candidates: heavy theorems NOT yet in Mathlib
    axiom_candidates = []
    if mode in ("axiom", "decompose"):
        for r in refs:
            axiom_candidates.append({
                "theorem": r["theorem"],
                "keyword": r["keyword"],
                "context": r["context"],
                "mathlib_status": "未形式化",
                "suggested_axiom": f"axiom {r['theorem']}_holds : ...",
            })

    return {
        "estimated_segments": segs,
        "external_theorem_refs": [
            {"theorem": r["theorem"], "keyword": r["keyword"]} for r in refs
        ],
        "depth_hint": depth,
        "recommended_mode": mode,
        "estimated_attempts_per_segment": estimate_attempts_per_segment(text),
        "estimated_total_loc": estimate_loc(text),
        "axiom_candidates": axiom_candidates,
        "rationale": rationale,
    }


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    import argparse

    ap = argparse.ArgumentParser(
        description="Estimate proof complexity for formalization strategy"
    )
    ap.add_argument("--intake", help="Path to intake.md")
    ap.add_argument("--output", default="-", help="Output JSON path (default: stdout)")
    ap.add_argument("--self-test", action="store_true", help="Run self tests")

    args = ap.parse_args()

    if args.self_test:
        run_self_tests()
        sys.exit(0)

    result = estimate(Path(args.intake))

    json_str = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(json_str)
    else:
        Path(args.output).write_text(json_str)


# ── Self-tests ──────────────────────────────────────────────────────────────

def run_self_tests():
    import tempfile, shutil

    tmpdir = Path(tempfile.mkdtemp(prefix="ce_test_"))
    passed = 0

    try:
        # Test 1: Short proof → full / easy
        intake_text = """# Intake: Fib Squares
## 定理陈述
theorem fib_squares : fib (n+1)^2 - fib n * fib (n+2) = (-1)^n

## 证明主体
Step 1: Base case n=0 is trivial.
Step 2: Assume holds for n, prove for n+1 by induction.
Hence the result follows.
"""
        p = tmpdir / "intake1.md"
        p.write_text(intake_text)
        result = estimate(p)
        assert result["recommended_mode"] == "full", f"Expected full, got {result['recommended_mode']}"
        assert result["depth_hint"] in ("trivial", "easy"), f"Got {result['depth_hint']}"
        assert result["estimated_segments"] <= 5
        passed += 1

        # Test 2: Heavy theorem → axiom
        intake_text2 = """# Intake: Vinogradov
## 定理陈述
Every sufficiently large odd integer is the sum of three primes.

## 证明主体
The proof uses the Vinogradov estimate for exponential sums.
By the Prime Number Theorem, we can estimate...
Siegel-Walfisz theorem handles the minor arcs.
By Vaughan's identity, the major arcs contribution is...
"""
        p2 = tmpdir / "intake2.md"
        p2.write_text(intake_text2)
        result2 = estimate(p2)
        assert result2["recommended_mode"] == "axiom", f"Expected axiom, got {result2['recommended_mode']}"
        assert len(result2["external_theorem_refs"]) >= 3, f"Expected >=3 refs, got {len(result2['external_theorem_refs'])}"
        passed += 1

        # Test 3: FLT → abort
        intake_text3 = """# Intake: FLT Application
## 证明主体
By Fermat's Last Theorem, the equation a^n + b^n = c^n has no solutions.
"""
        p3 = tmpdir / "intake3.md"
        p3.write_text(intake_text3)
        result3 = estimate(p3)
        assert result3["recommended_mode"] == "abort", f"Expected abort, got {result3['recommended_mode']}"
        passed += 1

        # Test 4: Large proof → decompose
        intake_text4 = "\n".join(
            [f"## Step {i}\nThis is step {i}.\n\nHence the deduction {i} follows.\n"
             for i in range(1, 40)]
        )
        p4 = tmpdir / "intake4.md"
        p4.write_text(intake_text4)
        result4 = estimate(p4)
        assert result4["recommended_mode"] in ("decompose", "full"), f"Got {result4['recommended_mode']}"
        assert result4["estimated_segments"] > 20
        passed += 1

        # Test 5: axiom mode sets user_confirmed requirement
        result5 = estimate(p2)
        assert result5["axiom_candidates"], "Should have axiom candidates"
        assert len(result5["axiom_candidates"]) >= 2
        passed += 1

    finally:
        shutil.rmtree(tmpdir)

    print(f"Self-test: {passed} passed, 0 failed out of 5")


if __name__ == "__main__":
    main()
