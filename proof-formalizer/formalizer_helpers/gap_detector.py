#!/usr/bin/env python3
"""Gap detector: 保守识别人类证明中的跳步。

输入: segments.json (由上游产出的切分结果)
输出: 为每个 segment 添加 is_gap 和 gap_type 字段
"""
import json
import re
import sys
import argparse
from pathlib import Path


# 层 1：高精度关键词
GAP_KEYWORDS_ZH = [
    "显然", "易得", "由此", "类似地", "由.*即得", "留作练习",
    "容易验证", "不难看出", "显而易见", "显然地", "容易得到",
    "容易看出", "简单计算", "经过计算", "自然地", "不失一般性",
]
GAP_KEYWORDS_EN = [
    "clearly", "obviously", "trivially", "it's easy to see",
    "by a similar argument", "by symmetry", "we can easily",
    "an easy computation", "it follows that", "by the same argument",
]
GAP_PATTERNS = [re.compile(k, re.IGNORECASE) for k in GAP_KEYWORDS_ZH + GAP_KEYWORDS_EN]


def detect_gap_type(text: str) -> str | None:
    """返回 gap 类型，或 None。层 1 识别。"""
    t = text.strip()

    # 对称性
    if re.search(r"(类似地|对称地|by symmetry|similarly)", t, re.IGNORECASE):
        return "IMPLICIT_SYMMETRY"

    # 省略计算
    if re.search(r"(经过计算|简单计算|易得|an easy computation|by calculation)", t, re.IGNORECASE):
        return "ELIDED_COMPUTATION"

    # 省略引理（"由 X 定理"或"由 X 不等式"）
    if re.search(r"(由.{1,20}(定理|引理|不等式|公式)|by.{1,30}(theorem|lemma|inequality))", t, re.IGNORECASE):
        return "ELIDED_LEMMA"

    # 通用 hand-wave
    for p in GAP_PATTERNS:
        if p.search(t):
            return "ELIDED_COMPUTATION"  # 默认归此类

    return None


def layer2_heuristic(text: str, prev_text: str = "") -> bool:
    """层 2：结构启发式。极短段 + 结论词 + 无推导符号 → 疑似 gap。

    宁漏勿误：含推导符号（|, ∈, =, ⇒, →, ≤, ≥, <, >, ∏, ∑, ∉）的段不算 gap，
    因为推导符号表明作者确实给出了推理过程。
    """
    words = re.findall(r"\w+", text)
    if len(words) >= 15:
        return False
    # 总结段（含 ∎/QED/证毕）→ 不是 gap
    if re.search(r"(∎|QED|证毕|证明完毕|\$\\square\$)", text, re.IGNORECASE):
        return False
    # 含推导符号 → 不是 gap
    derivation_symbols = r"[|∈=⇒→≤≥<>∏∑∉]"
    if re.search(derivation_symbols, text):
        return False
    concl_markers = ["故", "从而", "所以", "因此", "therefore", "hence", "thus"]
    if any(m in text.lower() for m in concl_markers):
        if len(text.strip()) > 10:
            return True
    return False


def process(segments_path: Path, output_path: Path):
    segs = json.loads(segments_path.read_text())

    for i, seg in enumerate(segs):
        text = seg.get("original_text", "")

        # 层 1
        gap_type = detect_gap_type(text)
        if gap_type:
            seg["is_gap"] = True
            seg["gap_type"] = gap_type
            seg["gap_layer"] = 1
            continue

        # 层 2
        prev_text = segs[i-1].get("original_text", "") if i > 0 else ""
        if layer2_heuristic(text, prev_text):
            seg["is_gap"] = True
            seg["gap_type"] = "ELIDED_COMPUTATION"  # 层 2 统一归此
            seg["gap_layer"] = 2
            continue

        # 层 3：不是 gap
        seg["is_gap"] = False
        seg["gap_type"] = None
        seg["gap_layer"] = 0

    output_path.write_text(json.dumps(segs, ensure_ascii=False, indent=2))

    # 统计
    n_gap = sum(1 for s in segs if s["is_gap"])
    print(f"Total segments: {len(segs)}", file=sys.stderr)
    print(f"Gap segments: {n_gap}", file=sys.stderr)
    for s in segs:
        if s["is_gap"]:
            print(f"  [GAP-{s.get('gap_type','?')}] id={s.get('id','?')} text={s['original_text'][:50]}...", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    process(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()
