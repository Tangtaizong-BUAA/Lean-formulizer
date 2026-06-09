#!/usr/bin/env python3
"""API 用法检查器：编译失败后诊断具体的标识符用法问题。

输入：
  - 失败的 tactic 代码
  - Lean 编译错误
输出：
  - 识别出的具体 API 误用（JSON）
  - 修正建议
"""
import json
import re
import sys
import argparse
import subprocess
from pathlib import Path


IDENT_PATTERN = re.compile(r"[A-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_']*)+")


def extract_identifiers(code: str) -> list[str]:
    """从 Lean 代码中抽出所有看起来像 Mathlib 标识符的 token。"""
    ids = set()
    for m in IDENT_PATTERN.finditer(code):
        ids.add(m.group(0))
    return sorted(ids)


def diagnose_error(error_text: str) -> dict:
    """从 Lean 错误消息中提取信息。"""
    result = {"error_type": "unknown", "clues": []}

    if "Unknown identifier" in error_text or "Unknown constant" in error_text:
        m = re.search(r"Unknown (?:identifier|constant) [`']?([^`'\s]+)[`']?", error_text)
        if m:
            result["error_type"] = "unknown_identifier"
            result["bad_identifier"] = m.group(1)
    elif "type mismatch" in error_text or "Type mismatch" in error_text:
        result["error_type"] = "type_mismatch"
    elif "Invalid field" in error_text or "Invalid projection" in error_text:
        result["error_type"] = "invalid_field_access"
        m = re.search(r"Invalid (?:field|projection) [`']?([^`'\s]+)[`']?", error_text)
        if m:
            result["bad_field"] = m.group(1)
    elif "expected" in error_text.lower():
        result["error_type"] = "syntax"

    return result


def probe_identifier(ident: str) -> dict:
    """调用 probe_identifier.sh"""
    probe_path = Path.home() / ".claude/skills/proof-formalizer/formalizer_helpers/probe_identifier.sh"
    try:
        result = subprocess.run(
            [str(probe_path), ident],
            capture_output=True, text=True, timeout=60,
        )
        return json.loads(result.stdout)
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", required=True, help="失败的 Lean 代码文件路径")
    ap.add_argument("--error", required=True, help="Lean 错误输出文件路径")
    ap.add_argument("--output", required=True, help="诊断结果 JSON 输出路径")
    args = ap.parse_args()

    code = Path(args.code).read_text()
    error = Path(args.error).read_text()

    diagnosis = diagnose_error(error)

    # 对所有标识符做 probe（慢路径：每次编译失败才跑）
    idents = extract_identifiers(code)
    probe_results = {}
    for ident in idents[:20]:  # 限制数量
        probe_results[ident] = probe_identifier(ident)

    # 找出问题标识符
    not_found = {k: v for k, v in probe_results.items() if v.get("status") == "not_found"}

    output = {
        "diagnosis": diagnosis,
        "not_found_identifiers": not_found,
        "suggestions": [],
    }

    # 生成修正建议
    for bad_ident, probe_res in not_found.items():
        suggs = probe_res.get("suggestions", [])
        if suggs:
            output["suggestions"].append({
                "replace": bad_ident,
                "with": suggs[0],
                "alternatives": suggs[1:],
            })

    Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
