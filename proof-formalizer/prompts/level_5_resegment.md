# Level 5: Resegment

## 你被叫到这里的原因
所有修复尝试都失败了，说明当前 segment 的粒度可能不合适。
你需要将这个 segment 拆分为更小的子步骤。

## 你能做什么（白名单）
- 将当前 segment 拆分为 2-3 个子 segment
- 为每个子 segment 设定 explicit goal_before/after
- 子 segment 的 goal 必须是当前 tactic state 中可见的
- 可以插入 `have` / `suffices` / `show` 结构

## 你不能做什么（红线）
- 不许继续在这个 segment 上尝试新 tactic
- 不许不拆分就直接跳到 help_request
- 拆分后的子 segment 不得有循环依赖

## 输入
- ledger summary: <LEDGER_SUMMARY>
- **重新提取的** 真实 goal: <FRESH_GOAL_STATE>
- 黑名单: <BLACKLIST>
- segment 原文: <ORIGINAL_TEXT>
- 上游 segment 输出: <UPSTREAM_GOALS>

## 输出格式（必须严格）
```markdown
## 重分段计划

### 子段 1
- goal_before: <...>
- goal_after: <...>
- tactic: <...>

### 子段 2
- goal_before: <...>
- goal_after: <...>
- tactic: <...>
```

理由（一句话）：<为什么拆分能解决当前困境>
