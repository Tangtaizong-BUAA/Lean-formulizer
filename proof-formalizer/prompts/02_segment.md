# Stage 2: Segment + GapDetection

把证明切成原子推理步骤，并识别 gap 段。

## 切分规则

- 粒度：一个推理步骤 = 一段（≈一个 `have` 或一个 tactic 能闭合）
- 太细（一句话一段）→ 合并到上下文
- 太粗（一段话一段）→ 拆开

## 处理步骤

1. 把 intake.md 的证明主体切成 segments
2. 每段字段：id, original_text, expected_goal_before, expected_goal_after, dependencies
3. **必须调用** `formalizer_helpers/gap_detector.py --input segments.json --output segments_with_gaps.json`
4. gap_detector 会自动为每段添加 is_gap, gap_type, gap_layer 字段

## 输出

写入 `segments_with_gaps.json`：

```json
[
  {
    "id": "01",
    "original_text": "假设 4k+3 的素数只有有限个...",
    "expected_goal_before": "⊢ ...",
    "expected_goal_after": "⊢ ...",
    "dependencies": [],
    "is_gap": false,
    "gap_type": null,
    "gap_layer": 0
  },
  {
    "id": "03",
    "original_text": "显然 N ≡ 3 (mod 4)",
    "expected_goal_before": "⊢ N % 4 = 3",
    "expected_goal_after": "⊢ ...",
    "dependencies": [],
    "is_gap": true,
    "gap_type": "ELIDED_COMPUTATION",
    "gap_layer": 1
  }
]
```

## gap_type 说明

| gap_type | 含义 | 来源 |
|----------|------|------|
| ELIDED_COMPUTATION | 省略计算（"经过计算"、"易得"） | 层 1/2 |
| ELIDED_LEMMA | 省略引理（"由 X 定理"） | 层 1 |
| IMPLICIT_SYMMETRY | 对称性跳步（"类似地"） | 层 1 |

## 保守原则

**宁漏勿误**：gap_detector 三层都不触发的段，不算 gap，按原文直译。
