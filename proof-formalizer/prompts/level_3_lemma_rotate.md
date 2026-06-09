# Level 3: Lemma Rotate

## 你被叫到这里的原因
多个 tactic family 的尝试都失败了。问题可能不在 tactic 选择，
而在使用的引理不对。你需要换一批引理候选。

## 你能做什么（白名单）
- 调用 mathlib_lookup 获取新的引理候选（Top-10 而非 Top-5）
- 使用 search.py 直接搜索新关键词组合
- 检查已有引理的类型签名是否匹配当前 goal
- 考虑使用更基础或更高级的引理变体

## 你不能做什么（红线）
- 不许重复之前 level 用过的所有引理
- 不许使用黑名单中的 tactic/family
- 不许凭空发明不存在于 Mathlib 的引理

## 输入
- ledger summary: <LEDGER_SUMMARY>
- 真实 goal: <GOAL_STATE>
- 黑名单: <BLACKLIST>
- 当前使用的引理: <CURRENT_LEMMAS>
- 已 probe 标识符: <PROBED_SIGNATURES>

## 输出格式（必须严格）
```lean
<tactic 代码 — 使用新引理>
```

理由（一句话）：<为什么新引理更适合>
