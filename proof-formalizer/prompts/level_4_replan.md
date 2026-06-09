# Level 4: Replan

## 你被叫到这里的原因
Tactic family 和引理层面的尝试全部失败。
你可能误判了 goal state、或者 segment 的翻译计划需要调整。
**必须先重新编译 working.lean 提取真实 goal state。**

## 你能做什么（白名单）
- 完全重新阅读当前 goal state（必须真实编译获取）
- 重新评估"这个 segment 到底需要什么"
- 考虑是否需要添加中间 `have` 语句分解 subgoal
- 考虑是否 goal 本身需要修正（如 cast 问题）
- 调用 cast_planner 诊断类型不匹配

## 你不能做什么（红线）
- 不许凭记忆猜 goal state
- 不许使用已 ban 的 tactic/family
- 不许继续沿用之前的翻译思路（forced fresh start）

## 输入
- ledger summary: <LEDGER_SUMMARY>
- **重新提取的** 真实 goal: <FRESH_GOAL_STATE>
- 黑名单: <BLACKLIST>
- segment 原文: <ORIGINAL_TEXT>
- alignment 计划: <ALIGNMENT_PLAN>

## 输出格式（必须严格）
```lean
<tactic 代码>
```

理由（一句话）：<新的翻译思路是什么，与之前的区别>
