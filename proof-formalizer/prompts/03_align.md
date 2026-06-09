# Stage 3: Align

为每个 segment 查找 Mathlib 候选引理，产出翻译计划。v3 增强：优先尝试自动求解。

## 处理步骤（v3 增强）

对每个 segment：

### Step 0: 自动求解（新增）

1. **必须调用** `formalizer_helpers/v3/auto_solver.sh "<expected_goal_before>" "[]" "<output.json>"`
2. 读取 output.json：
   - 如果 `solved: true` → 在 alignment.md 记录 `auto_solved: <tactic>`，formalize 阶段直接使用，不进 LLM
   - 如果 `solved: false` → 继续后续 mathlib_lookup 流程

### Step 1: Mathlib 查找（非 gap 段）

1. **必须调用** `formalizer_helpers/mathlib_lookup.sh "<segment 关键词>"`
2. 拿到 Top-5 候选引理
3. 基于原文语义选择最可能用到的 1-2 个
4. 写出翻译计划："本段预计用 X 引理按 Y 方式翻译"

### Step 2: Gap 段处理

1. 基于 expected_goal_before 和 gap_type 猜测"应该补什么"
2. ELIDED_COMPUTATION → 查找相关计算类引理（mod、div、mul 等）
3. ELIDED_LEMMA → 根据引理名查找具体引理
4. IMPLICIT_SYMMETRY → 查找 symm / congr 类引理
5. 也调 mathlib_lookup 拿候选

## 输出

写入 `alignment.md`：

```markdown
# Alignment

## 段 01: "假设 4k+3 的素数只有有限个..."
- 类型：非 gap
- auto_solved: by_contra fp  (如果 auto_solver 闭合)
- 翻译计划：反证法框架，用 `by_contra` 引入假设
- 候选引理：无（框架性步骤）

## 段 03: "显然 N ≡ 3 (mod 4)" [GAP: ELIDED_COMPUTATION]
- 类型：gap
- auto_solved: null (auto_solver 未闭合)
- 翻译计划：需补 N % 4 = 3 的计算证明
- 候选引理：Nat.add_mod, Nat.mul_mod, Nat.mod_mod
- 补全策略：展开 N = 4*M - 1，用 mod 算术化简
```

## 注意

- auto_solver 是必须调用的第一步，不许跳过
- mathlib_lookup 是必须调用的脚本，不许凭记忆推荐引理
- 候选引理的名字在下一阶段会通过 probe 验证
- gap 段的候选重点是"怎么补"，不是"原文怎么说"
- auto_solved 的 tactic 在 04_formalize 阶段优先使用，跳过 LLM 生成
