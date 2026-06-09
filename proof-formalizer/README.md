# Proof Formalizer v3

将人类编写的数学证明自动形式化为 **Lean 4 + Mathlib4** 编译通过的代码。目标：**0 sorry，100% 忠实于原始证明**。

> 🏠 项目主页：[GaussAI Math](http://argonai.cn/math/index.html)
>
> 🤗 检索模型：[YuxuanGong/lean-RAG](https://huggingface.co/YuxuanGong/lean-RAG) — 基于 BGE-M3 微调的 Mathlib4 API 检索模型，Recall@5 61.5%，MRR 42.1%

---

## 概述

Proof Formalizer 是一个 AI 驱动的数学证明形式化框架。输入人类写的正确数学证明（LaTeX / Markdown / 自然语言），输出编译通过的 Lean 4 代码。框架会：

- 自动识别证明中的跳步（gap）并尝试补全
- 通过 `probe` 验证每个 Mathlib 标识符确实存在
- 基于真实 Lean goal state 驱动证明生成
- 失败时写 `help_request` 请用户介入，而非偷偷塞 `sorry`

## 与 math-thinking-flow 的分工

| | Proof Formalizer | Math Thinking Flow |
|---|---|---|
| **输入** | 已有的人类证明 | 只有定理陈述 |
| **任务** | 翻译 + 补 gap + 验证 | 从零推导 + 策略搜索 |
| **哲学** | 信任输入，忠实翻译 | 探索未知，迭代反思 |

```
有现成的人类证明吗？
├── 是 → Proof Formalizer（翻译 + 验证 + 补全跳步）
└── 否 → Math Thinking Flow（从零推导 + 策略搜索 + 迭代反思）
```

## 核心工作流

```
Intake → Strategy → Segment + GapDetection → Align → Formalize → Report
  ↓                                                              ↓
  成功编译 + 0 sorry        →  输出 final.lean + report
  失败                     →  写 help_request.md 请用户补充说明
```

### 六大阶段

| 阶段 | 文件 | 职责 |
|------|------|------|
| 1. Intake | `prompts/01_intake.md` | 提取定理陈述、构建符号表、识别前置概念 |
| 1b. Strategy | `prompts/01b_strategy.md` | 评估复杂度，选择 full/axiom/decompose/abort 策略 |
| 2. Segment | `prompts/02_segment.md` | 将证明拆分为可独立处理的段，保守识别 gap |
| 3. Align | `prompts/03_align.md` | 匹配 gap 到 Mathlib 引理，自动求解 exact?/aesop/decide |
| 4. Formalize | `prompts/04_formalize.md` | 逐段翻译，anti-loop 主循环，probe + 编译验证 |
| 5. Report | `prompts/05_report.md` | 生成最终报告，包含 sorry 统计和 probe 替换记录 |

## 三大核心机制

### 1. Probe 先行

铁律：**任何 Mathlib 标识符在写入 `.lean` 前必须通过 `probe_identifier.sh` 验证存在**。

```
LLM 生成 tactic → 提取标识符 → probe_identifier.sh 逐个验证
  ├── FOUND → 写入 .lean
  ├── NOT_FOUND + 有 suggestion → 自动替换，写 [PROBE-REPLACE] 注释
  └── NOT_FOUND + 无 suggestion → mathlib_lookup 查找 / 标记失败
```

### 2. 保守 Gap 识别

三层识别，漏报远优于误报：

| 层 | 方法 | 示例 |
|---|------|------|
| 1 | 关键词匹配 | 显然、易得、clearly、by symmetry |
| 2 | 结构启发式 | 段长 < 30 词但断言非平凡结论 |
| 3 | 默认 | 都不是 → 不是 gap，按原文直译 |

### 3. 失败求助（非 sorry）

- 非 gap 段连续失败 → 写 `help_request.md` 中断
- gap 段 1 次失败 → 写 `sorry`（带 `[SORRY-N]` 标注）+ help_request 条目
- 任何 sorry 在 help_request 中单独列出，请求用户展开

## v3 Anti-Loop 架构

v3 引入反循环升级系统，防止 LLM 在同一个错误上死循环：

| 组件 | 文件 | 职责 |
|------|------|------|
| Escalation Ladder | `v3/escalation.py` | 7 级阶梯，硬上限 9 次尝试 |
| Attempt Ledger | `v3/ledger.py` | Append-only JSONL，持久化每次尝试 |
| Error Classifier | `v3/error_classifier.py` | 15 类错误自动分类 + token 提取 |
| Tactic Fingerprint | `v3/fingerprint.py` | 循环检测，连续重复即升级 |
| Blacklist | — | 失败 tactic 自动加入，可整 family 封禁 |
| Auto Solver | `v3/auto_solver.sh` | align 阶段自动跑 exact?/aesop/decide/omega |
| Cast Planner | `v3/cast_planner.py` | 类型不匹配自动诊断 + 注入修复 |
| Retry Strategy | `v3/retry_strategy.py` | 15 类错误 → 具体战术建议 |
| Perf Hints | `v3/perf_hint.py` | Timeout 自动升级 heartbeat |

### 升级阶梯

| Level | 名称 | 触发条件 |
|-------|------|---------|
| 0 | Tweak | 类型/命名微调 |
| 1 | Switch Within | 同 family 换 tactic |
| 2 | Switch Family | 换 tactic family |
| 3 | Lemma Rotate | 换引理/重排参数 |
| 4 | Replan | 重新提取 goal state，重规划 |
| 5 | Resegment | 合并相邻段或拆分更小 |
| 6 | Help Request | 放弃，请用户介入 |

## 前置依赖

1. **Lean 4 工作区**：`~/math-agent-workspace/`（Mathlib 已编译）
2. **Mathlib RAG**：`~/mathlib-rag/`（BGE-M3 微调模型 + FAISS 索引）
   - 模型下载：`huggingface-cli download YuxuanGong/lean-RAG`
3. **Python 3.10+**：gap_detector.py、api_usage_checker.py、v3 模块

## 使用示例

### 形式化请求

```
把这个证明转成 Lean：

假设 √2 = a/b 其中 a,b 互素，则 a²=2b²，故 2|a。
令 a=2c，代入得 4c²=2b²，即 b²=2c²，故 2|b。
与 a,b 互素矛盾，因此 √2 是无理数。
```

### 验证请求

```
验证这个证明有没有跳步：
<粘贴证明>
```

## 目录结构

```
proof-formalizer/
├── SKILL.md                    # Skill 定义与行为准则
├── prompts/                    # 各阶段 prompt 指令
│   ├── 01_intake.md            # 输入解析
│   ├── 01b_strategy.md         # 策略评估
│   ├── 02_segment.md           # 分段与 gap 识别
│   ├── 03_align.md             # 引理对齐
│   ├── 04_formalize.md         # 形式化主循环（v3 anti-loop）
│   ├── 05_report.md            # 报告生成
│   └── level_0-5_*.md          # Anti-loop 升级路由
├── formalizer_helpers/         # 工具脚本
│   ├── probe_identifier.sh     # 标识符探针（核心）
│   ├── mathlib_lookup.sh       # Mathlib RAG 检索
│   ├── gap_detector.py         # Gap 检测
│   ├── api_usage_checker.py    # API 用法验证
│   ├── goal_state_extract.sh   # Goal state 提取
│   ├── init_formalize_run.sh   # Run 目录初始化
│   ├── segment_validate.sh     # 段编译验证
│   ├── generate_report.py      # 报告生成
│   └── v3/                     # v3 Anti-loop 模块
│       ├── escalation.py       # 升级决策
│       ├── ledger.py           # 尝试账本
│       ├── error_classifier.py # 错误分类
│       ├── fingerprint.py      # Tactic 指纹
│       ├── cast_planner.py     # 类型转换规划
│       ├── retry_strategy.py   # 重试策略矩阵
│       ├── complexity_estimator.py # 复杂度评估
│       ├── perf_hint.py        # 性能提示
│       └── auto_solver.sh      # 自动求解器
├── references/                 # 参考知识库
│   ├── common_mathlib_names.md # 常用 Mathlib 名称
│   ├── error_to_action.md      # 错误→行动映射
│   ├── gap_patterns.md         # Gap 模式库
│   └── tactic_by_goal_shape.md # Goal shape → tactic 建议
├── assets/
│   └── report_template.md      # 报告模板
└── benchmark_problems/         # Benchmark 问题集
    ├── problem_01.md           # 无理数证明（易→中）
    ├── problem_03.md           # 不等式证明（中）
    ├── problem_05.md           # 数论（中→难）
    ├── problem_06.md           # 代数（中）
    ├── problem_08.md           # 分析（难）
    └── problem_09.md           # 拓扑（难）
```

## 工作区约定

Run 目录：`~/math-agent-workspace/runs/formalize_{timestamp}_{problem_id}/`

```
runs/formalize_{ts}_{id}/
├── intake.md              # 阶段 1 输出
├── strategy.md            # 阶段 1b 输出
├── segments.json          # 阶段 2 输出
├── alignment.md           # 阶段 3 输出
├── working.lean           # 当前编译的 .lean 文件
├── attempts/              # 每次尝试的完整记录
│   ├── 01_tactic.lean
│   ├── 01_stderr.txt
│   ├── 01_diag.json
│   ├── 01_prompt.md
│   └── ...
├── probe_log.jsonl        # Probe 日志
├── ledger.jsonl           # v3 attempt 账本
├── help_request.md        # 需人工介入时写入
├── final.lean             # 最终产物
└── report.md              # 阶段 5 输出
```

## 已知局限

- 只支持单定理形式化（不支持整个章节）
- Gap 补全成功率 ~70%+，失败时请用户介入
- Probe 自动替换取 suggestions[0]，偶尔不是最优选择
- 依赖特定 Mathlib4 版本，API 名可能随版本变化

## 许可

MIT License
