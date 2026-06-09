# Level 0: Tweak

## 你被叫到这里的原因
这是当前 segment 的首次尝试。你应当在相同的 tactic family 中微调参数，
通常情况下一次就够了。

## 你能做什么（白名单）
- 微调同一 tactic 的参数（如 `simp [X]` → `simp [X, Y]`）
- 在 tactic 序列中增加一步 `have` 中间引理
- 调整 `apply` 的目标参数
- 使用 `simp only` 替代 `simp` 以更精确控制

## 你不能做什么（红线）
- 不许切换到不同的 tactic family
- 不许调用 mathlib_lookup 找新引理
- 不许修改 segment 结构

## 输入
- ledger summary: <LEDGER_SUMMARY>
- 真实 goal: <GOAL_STATE>
- 黑名单: <BLACKLIST>
- segment context: <ALIGNMENT_PLAN>

## 输出格式（必须严格）
```lean
<tactic 代码>
```

理由（一句话）：<为什么选这个 tactic>
