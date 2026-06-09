#!/usr/bin/env python3
"""generate_report.py — 从 run 目录生成交付报告"""

import argparse, json, os, re, glob

def load_json(path):
    try:
        with open(path) as f: return json.load(f)
    except: return None

def load_text(path):
    try:
        with open(path) as f: return f.read()
    except: return ""

def find_results(run_dir):
    results = []
    for f in glob.glob(os.path.join(run_dir, "attempts", "segment_*_result.json")):
        data = load_json(f)
        if data: results.append(data)
    results.sort(key=lambda x: x.get("segment_id", ""))
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()

    run_dir = args.run_dir
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "report_template.md")
    template = load_text(template_path)

    segments_data = load_json(os.path.join(run_dir, "segments.json"))
    canonical = load_text(os.path.join(run_dir, "canonical_match.md"))
    working = load_text(os.path.join(run_dir, "working.lean"))
    results = find_results(run_dir)

    total = len(results)
    success = sum(1 for r in results if r.get("success"))
    sorry = sum(r.get("sorry_count", 0) for r in results)

    theorem_name = segments_data.get("theorem_name", "unknown") if segments_data else "unknown"
    confidence = "HIGH" if sorry == 0 else "MEDIUM" if sorry <= 2 else "LOW"

    report = template.replace("{{theorem_name}}", theorem_name)
    report = report.replace("{{final_lean_code}}", working)
    report = report.replace("{{canonical_hits}}", canonical[:500] if canonical else "无")
    report = report.replace("{{total_segments}}", str(total))
    report = report.replace("{{success_count}}", str(success))
    report = report.replace("{{sorry_count}}", str(sorry))
    report = report.replace("{{confidence}}", confidence)

    advice = "审阅 Lean 代码是否忠实于原文" if sorry == 0 else \
             "重点审阅 sorry 段" if sorry <= 2 else "考虑补充更详细的原文"
    report = report.replace("{{review_advice}}", advice)

    # Build sorry list
    sorry_list = []
    for r in results:
        if r.get("sorry_count", 0) > 0:
            sorry_list.append(f"- 段 {r.get('segment_id','?')}: {r.get('sorry_count',0)} sorry(s)")
    report = report.replace("{{sorry_list}}", "\n".join(sorry_list) if sorry_list else "无")
    report = report.replace("{{gap_filler_list}}", "v1 暂未追踪")

    out = os.path.join(run_dir, "report.md")
    with open(out, "w") as f: f.write(report)
    print(f"Report: {out}")

if __name__ == "__main__": main()
