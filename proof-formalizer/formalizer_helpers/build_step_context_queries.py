#!/usr/bin/env python3
"""Build step-context style queries matching V2 training distribution.

V2 was trained on queries like:
  EN: "Given that x % y < y, I need to find a lemma to establish this. Keywords: ..."
  ZH: "现在我需要证明 x % y < y，用哪个引理能得到这个结论？关键词：..."

Usage:
  python3 build_step_context_queries.py "<goal_type>" '<keywords_json>'
  # Output: {"en": "...", "zh": "..."}
"""
import json
import re
import sys

_ABBREVIATIONS = {
    "add": "addition", "sub": "subtraction", "mul": "multiplication",
    "div": "division", "mod": "modulo", "neg": "negation",
    "abs": "absolute value", "succ": "successor", "pred": "predecessor",
    "nat": "natural number", "int": "integer", "rat": "rational",
    "pow": "power", "sqrt": "square root", "gcd": "greatest common divisor",
    "lcm": "least common multiple", "inv": "inverse", "rec": "recursion",
    "mon": "monoid", "grp": "group", "ab": "abelian",
    "ring": "ring", "fld": "field", "alg": "algebra",
    "hom": "homomorphism", "iso": "isomorphism", "emb": "embedding",
    "equiv": "equivalence", "comm": "commutative",
    "assoc": "associative", "ker": "kernel", "img": "image",
    "ideal": "ideal", "quot": "quotient", "comp": "composition",
    "prod": "product", "det": "determinant", "deg": "degree",
    "dim": "dimension", "lin": "linear", "le": "less than or equal",
    "lt": "less than", "ge": "greater than or equal", "gt": "greater than",
    "sup": "supremum", "inf": "infimum", "pos": "positive",
    "nonneg": "non-negative", "mono": "monotone monotonic",
    "bot": "bottom", "top": "top", "bdd": "bounded",
    "min": "minimum minimal", "max": "maximum maximal",
    "iff": "if and only if", "eq": "equal equality", "ne": "not equal",
    "cong": "congruent congruence", "refl": "reflexivity reflexive",
    "symm": "symmetry symmetric", "trans": "transitivity transitive",
    "dec": "decidable", "fn": "function", "fun": "function",
    "pred": "predicate", "rel": "relation", "finset": "finite set",
    "finsupp": "finitely supported", "lim": "limit",
    "conv": "convergence convergent", "cont": "continuous continuity",
    "diff": "differentiable differential", "deriv": "derivative",
    "meas": "measure measurable", "norm": "norm normal",
    "metric": "metric", "seq": "sequence", "cvx": "convex",
    "top": "topological topology", "cpt": "compact compactness",
    "conn": "connected connectivity", "nhds": "neighborhood",
    "homeo": "homeomorphism", "loc": "local locally",
    "sep": "separation separated", "union": "union",
    "inter": "intersection", "compl": "complement",
    "card": "cardinality cardinal", "count": "countable",
    "fintype": "finite type", "prime": "prime", "coprime": "coprime",
    "cyc": "cyclic cyclotomic", "gal": "Galois", "val": "valuation",
    "ell": "elliptic", "lattice": "lattice",
}


def expand_keyword(kw):
    lower = kw.lower().strip("_")
    if lower in _ABBREVIATIONS:
        return _ABBREVIATIONS[lower]
    return kw


def extract_goal_conclusion(goal_type):
    """Extract the core conclusion from a Lean goal type string."""
    s = goal_type.strip()
    # Strip turnstile
    if s.startswith("⊢ "):
        s = s[2:]
    # Strip outer ∀ binders (keep the conclusion)
    while s.startswith("∀") or s.startswith("∀ "):
        comma = s.find(",")
        if comma < 0:
            break
        s = s[comma + 1:].strip()
    # Truncate very long goals (model max_seq_length = 400, template overhead ~50 chars)
    if len(s) > 300:
        s = s[:300]
    return s


def build_queries(goal_type, keywords_json):
    """Build EN + ZH step-context queries from goal and keywords."""
    goal = extract_goal_conclusion(goal_type) if goal_type else ""
    try:
        keywords = json.loads(keywords_json) if keywords_json and keywords_json not in ("[]", "") else []
    except (json.JSONDecodeError, TypeError):
        keywords = []
    expanded = " ".join(expand_keyword(kw) for kw in keywords)

    if goal and expanded:
        en = f"Given that {goal}, I need to find a lemma to establish this. Keywords: {expanded}."
        zh = f"现在我需要证明 {goal}，用哪个引理能得到这个结论？关键词：{expanded}。"
    elif goal:
        en = f"Given that {goal}, I need to find a lemma to establish this."
        zh = f"现在我需要证明 {goal}，用哪个引理能得到这个结论？"
    elif expanded:
        en = f"I need a lemma about {expanded}."
        zh = f"现在我需要关于 {expanded} 的引理。"
    else:
        en = ""
        zh = ""

    return en, zh


if __name__ == "__main__":
    goal_type = sys.argv[1] if len(sys.argv) > 1 else ""
    keywords_json = sys.argv[2] if len(sys.argv) > 2 else "[]"
    en, zh = build_queries(goal_type, keywords_json)
    print(json.dumps({"en": en, "zh": zh}, ensure_ascii=False))
