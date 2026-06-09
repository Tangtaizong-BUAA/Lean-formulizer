# Level 2: Switch Family

## 你被叫到这里的原因
当前 tactic family 内的所有尝试都已失败。
你必须切换到完全不同的 tactic family。

## 你能做什么（白名单）
- 切换到未被 ban 的 family（从 allowed_families 列表中选择）
- 重新评估 goal 结构，选择适合的 family：
  - 等式 → ring / rw / calc
  - 不等式 → linarith / nlinarith / omega
  - 整除 → exact / rcases / case_split  
  - 量化命题 → refine / intro / apply
- 可以组合使用不同 family 的 tactic

## 你不能做什么（红线）
- 不许使用黑名单中 `banned_entirely=true` 的任何 family
- 不许重复黑名单中的任何 specific tactic
- 不许使用前两个 level 用过的 family（若已被 ban）

## 输入
- ledger summary: <LEDGER_SUMMARY>
- 真实 goal: <GOAL_STATE>
- 黑名单: <BLACKLIST>
- 允许的 families: <ALLOWED_FAMILIES>
- segment context: <ALIGNMENT_PLAN>

## 输出格式（必须严格）
```lean
<tactic 代码>
```

理由（一句话）：<为什么选择这个新 family + tactic>
