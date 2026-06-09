# Level 1: Switch Within Family

## 你被叫到这里的原因
Level 0 的微调已经失败（预算用完或 fingerprint 重复）。
你需要保持在同一个 tactic family 内，但更换具体策略。

## 你能做什么（白名单）
- 同一 family 内切换到不同 tactic（如 `simp_all` → `simp only`）
- 使用 family 内更强大的变体（如 `rw` → `rw [...]; rfl`）
- 增加 `unfold` 或 `dsimp` 预处理步骤
- 改变 rewrite 的方向（`rw` → `rw [← ...]`）

## 你不能做什么（红线）
- 不许切换到不同的 tactic family
- 不许重复黑名单中已失败的 specific tactic
- 不许调用 mathlib_lookup 找新引理

## 输入
- ledger summary: <LEDGER_SUMMARY>
- 真实 goal: <GOAL_STATE>
- 黑名单: <BLACKLIST>
- segment context: <ALIGNMENT_PLAN>

## 输出格式（必须严格）
```lean
<tactic 代码>
```

理由（一句话）：<为什么选这个变体>
