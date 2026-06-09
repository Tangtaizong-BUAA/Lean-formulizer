# Stage 1.5: Strategy Selection

在 intake 之后、segment 之前评估证明复杂度，选择形式化策略，避免大题反复浪费迭代。

## 输入
- `intake.md`（Stage 1 产出）

## 处理

1. **必须调用** `formalizer_helpers/v3/complexity_estimator.py --intake intake.md --output strategy.json`
2. 基于 `strategy.json` 写 `strategy.md`

## strategy.md 结构

```markdown
# Strategy

## 模式: <full | axiom | decompose | abort>

## 复杂度评估
- 估计段数: N
- 估计每段 attempts: M
- 估计总 LOC: L
- 深度: trivial | easy | medium | hard | infeasible
- 引用的重定理: [...]

## 接受为 axiom 的定理（若 mode=axiom）
| 定理 | 理由 | Mathlib 状态 |
|------|------|------------|
| PNT  | 多年项目 | 未形式化 |

## 中断条件（abort_if）
- 总 attempts > N × M × 2
- 单段 level >= 6 出现 K 次

## 用户确认（若 mode=axiom 或 abort）
**形式化前必须用户确认 axiom 列表**。如未在 strategy.md 中标注 `user_confirmed: true`，主循环必须停下询问。
```

## 输出
- `run_dir/strategy.json`
- `run_dir/strategy.md`

## 模式说明

| 模式 | 含义 | Formalize 阶段行为 |
|------|------|------------------|
| `full` | 完整形式化 | 原流程，逐段翻译 |
| `axiom` | 接受重定理为公理 | 先把 axiom 列表写入 working.lean 顶部 `axiom xxx : ...`，跳过这些定理的 formalize |
| `decompose` | 拆分子目标 | 调用 resegmenter 拆成多个子定理，每个独立形式化 |
| `abort` | 不可行 | 直接写 help_request，不进入 formalize |

## 注意

- complexity_estimator 是基于启发式的估算，非精确
- mode=axiom 或 abort 时，必须等待用户确认才能继续
- 标记 `user_confirmed: true` 是主循环的前置条件
