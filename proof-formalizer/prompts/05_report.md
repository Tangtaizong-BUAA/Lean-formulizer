# Stage 5: Report

产出最终报告。

## 成功报告

当 formalize 成功（0 sorry + 编译通过）时，写入 `report.md`：

```markdown
# Formalization Report

## 定理
<定理名>

## 结果
✅ 编译通过，0 sorry

## 统计
| 指标 | 值 |
|------|------|
| 总段数 | N |
| gap 段数 | M |
| gap 补全成功 | K |
| Probe 调用次数 | P |
| Probe 自动替换次数 | R |
| API 用法错误修复次数 | F |
| 总 tactic 尝试次数 | T |

## Probe 替换记录
- [PROBE-REPLACE] OldName → NewName（段 N, 尝试 M）

## API 用法修复记录
- 修复：MisusedName → CorrectUsage（段 N）
```

## 失败报告

当 formalize 失败时，写入 `help_request.md`：

```markdown
# 需要人工介入

## 段 N
- 原文：<原文>
- 类型：gap / 非 gap
- 失败原因：<具体错误信息>
- 我需要你：<具体请求，例如"请把 X 这一步展开成具体计算"）

## 段 M
...
```

同时输出当前 `working.lean`（含 sorry 标注）。

## 注意

- report 必须如实反映所有 probe 替换和 API 修复
- help_request 的"我需要你"必须具体，不能写"请修正此段"
- 每个 sorry 都要在 help_request 中单独列一条
