---
name: proof-formalizer
description: Formalize a human-written mathematical proof into compiling Lean 4 + Mathlib code. Triggers when the user provides a proof (LaTeX, Markdown, or natural language) and wants it translated to Lean, verified, or filled in where steps are skipped. This skill assumes the input proof is mathematically correct (possibly with 1-2 hand-waved gaps like "clearly" or "similarly"); its job is faithful translation + gap filling to achieve 0 sorry compilation. Triggers even when the user doesn't say "Lean" but gives a proof and asks for rigorous verification or formalization. Do NOT use for proving from scratch (use math-thinking-flow for that), or for proofs of unknown correctness.
---

# Proof Formalizer v3

把人类写的**正确**数学证明（可能含 1-2 个 gap）翻译成编译通过的 Lean 4 + Mathlib 代码。目标：0 sorry，100% 忠实于原文。

## 核心哲学（v2 反转）

1. **信任输入**：用户给的证明数学内容正确，我的工作是翻译 + 补 gap，不是质疑
2. **写之前先 probe**：任何 Mathlib 标识符写进 .lean 之前必须通过 probe 验证存在
3. **Goal-state 驱动**：每步基于真实 goal state 决定下一步，不许凭想象
4. **保守识别 gap**：宁可漏识别 gap 让它编译失败，也不误识别让模型瞎补
5. **失败求助而非 sorry**：补不出来时告诉用户"你这里跳步太大，展开一句我再补"，不是自欺欺人塞 sorry

## 激活条件

**激活**：
- 用户给了证明（LaTeX / Markdown / 自然语言）要求翻译或形式化
- 给了 `.lean` 文件要求修正并有原文可参考
- 要求"验证"或"检查跳步"一个已有证明

**不激活**：
- 只给定理陈述没给证明 → 建议用 math-thinking-flow
- 证明未知是否正确 → 不在本 skill 目标内
- 纯计算问题

## 工作流

```
Intake → Strategy → Segment + GapDetection → Align → Formalize → Report
  ↓                                                              ↓
  成功编译 + 0 sorry        →  输出 final.lean + report
  失败                     →  写 help_request.md 请用户补充说明
```

## 三大核心机制

### 机制一：Probe 先行（杀手机制）

铁律：任何 Mathlib 标识符在写入 .lean 前必须通过 `probe_identifier.sh` 验证存在。

什么叫标识符：任何形如 `X.Y.Z` 或 `X_y_z` 的 token（`Nat.Prime.dvd_of_dvd_pow`、`Finset.prod_bij`、`Or.resolve_left` 等）。

工作流程：
1. LLM 生成 tactic 候选
2. 用 grep 抽出所有标识符（正则 `[A-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_']*)+`）
3. 对每个标识符调 `probe_identifier.sh`
4. NOT_FOUND + 有 suggestion → 自动替换为 suggestions[0]，写 `[PROBE-REPLACE]` 注释
5. NOT_FOUND + 无 suggestion → 从 mathlib_lookup 再找，或标记该 tactic 失败
6. 全部 FOUND 才写入文件

### 机制二：保守 Gap 识别

三层识别，漏报远优于误报：

**层 1** — 关键词（高精度）：显然、易得、由此、类似地、由.*即得、留作练习、容易验证、不难看出、clearly、obviously、trivially、by symmetry

**层 2** — 结构启发式（中精度）：段长 < 30 词但声明了非平凡结论；明确写"由定理 X"但未给过程

**层 3** — 默认：都没触发 → 不是 gap，按原文直译。

gap 类型标签：`[ELIDED_COMPUTATION]`、`[ELIDED_LEMMA]`、`[IMPLICIT_SYMMETRY]`、`[SIMILAR_TO_PREVIOUS]`

### 机制三：失败求助（非 sorry）

- 非 gap 段失败 5 次 → 写 help_request 中断流程
- gap 段尝试 1 次失败 → 写 sorry（带 `[SORRY-N]` 标注）+ help_request 条目，继续下一段
- 任何 sorry 都要在 help_request 里单独列一条

help_request.md 格式：
```markdown
# 需要人工介入

## 段 N
- 原文：<原文>
- 类型：gap / 非 gap
- 失败原因：<具体错误>
- 我需要你：<具体请求，例如"请把 X 这一步展开成具体计算">
```

## V3 Anti-Loop 升级（核心变更）

v3 将 v2 的"5 次尝试硬编码"替换为反循环升级架构：

1. **Anti-Loop Escalation Ladder**：7 级阶梯，总预算硬上限 9 次
2. **Attempt Ledger**：append-only jsonl，强制持久化每次尝试
3. **Error Classifier**：15 类错误自动分类 + token 提取
4. **Tactic Fingerprint**：循环检测，连续重复即升级
5. **Tactic 黑名单**：失败 tactic 自动加入，升级时整 family 都可被 ban
6. **Auto Solver**：align 阶段自动跑 exact?/aesop/decide/omega 等
7. **Strategy Selection**：预先评估复杂度，axiom/decompose/abort 模式避免浪费
8. **Cast Planner**：类型不匹配自动诊断 + 注入修复
9. **Retry Strategy Matrix**：15 类错误 → 具体战术建议
10. **Performance Hints**：timeout 自动升级 heartbeat，不计入 attempt

详见 `prompts/04_formalize.md`（v3 重写版）和 `formalizer_helpers/v3/` 目录。

## 调度逻辑（v3）

```
输入证明 → Intake → Strategy → Segment + GapDetection → Align → Formalize

Formalize 主循环（v3 anti-loop）：
对每个 segment s：
    state = read_segment_state(s)
    若 alignment 有 auto_solved → 直接使用，跳过 LLM

    while state.status == "in_progress":
        level, reason = escalation.decide_next_level(state, last_diag)
        若 level == 6 → help_request
        若 escalated → update_blacklist(family_banned=True)

        读取 ledger summary + 黑名单
        按 level 路由生成 tactic
        probe 所有标识符
        编译 + error classification + fingerprint

        write_attempt_files (4 files)
        append ledger.jsonl
        update state

        若 success → 下一 segment
        若 timeout → 不计 attempt, upgrade heartbeat
```


## Probe 自动替换规则

1. 取 similar 建议的第一条
2. 直接替换，不询问
3. 替换后再 probe 一次验证
4. 写注释：`-- [PROBE-REPLACE] OldName → NewName`
5. 首选仍 NOT_FOUND → 试第二条；全不行 → tactic 失败

## API 用法错误（二次防线）

Probe 验证标识符存在，不验证用法。编译失败时：
1. 触发 `api_usage_checker.py`
2. 逐个标识符 `#check` 验证类型
3. 找到类型错 → 从 mathlib_lookup 找正确用法示例
4. 塞进下一次 tactic 生成的 prompt

## 工作区

Run 目录：`~/math-agent-workspace/runs/formalize_{timestamp}_{problem_id}/`

内含：intake.md, segments.json, alignment.md, working.lean, attempts/, probe_log.jsonl, help_request.md, final.lean, report.md

## 行为准则

1. 每阶段必读对应 prompt
2. 每个 Mathlib 标识符写入 .lean 前必须 probe
3. 不许凭记忆写标识符
4. Formalize 前必看真实 goal state
5. Gap 识别宁漏勿误
6. 编译必真实执行
7. 失败要求助，不要自欺欺人写无标注 sorry
8. 非 gap 段绝不写 sorry
9. Probe 自动替换时必须留注释
10. Report 必须如实反映：有无 sorry、有无 probe 替换、有无 API 用法错修复
