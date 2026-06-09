# Error → Action Mapping

| 错误特征 | 可能原因 | 首要行动 |
|---------|----------|---------|
| "Unknown identifier X" | 名字错 | 查 common_mathlib_names.md |
| "Unknown identifier" + 拼写相似 | 小拼写错 | 搜 Mathlib 源码 grep |
| "type mismatch, expected 2 ∣ a, got Even a" | Even ↔ Dvd 类型桥 | 用 .two_dvd / .two_dvd.mp |
| "omega could not prove" + 含平方 | omega 不懂乘法 | 换 Nat.Prime.dvd_of_dvd_pow 或 nlinarith |
| "rewrite failed: pattern not found" | rw/rfl 消掉变量 | 重读 goal state，用 subst 或改写法 |
| "unsolved goals" + goal 接近目标 | 差几步 | 换更强 tactic（simp→simp_all, omega→nlinarith） |
| "unsolved goals" + goal 完全不同 | 跳步或 align 错 | [B] gap_filler 或 [D] 回 align |
| "failed to synthesize instance" | 类型不明确 | 加显式标注 (2:ℤ) / (a : ℝ) |
| "maximum recursion depth" | simp 搜索爆炸 | 用 simp only [lemma1, lemma2] |
| "No goals to be solved" | sorry 过多闭合了 goal | 用 have 结构代替平铺 sorry |
| "expected '{' or indented" | calc/语法缩进错 | 检查 calc 语法，每行 `_ = _ := by ...` |
| "Nat/Int/Real cast mismatch" | 跨类型运算 | push_cast / exact_mod_cast / mod_cast |
| "obtain pattern mismatch" | 析构模式不匹配 | 检查类型（Dvd vs Exists vs And） |
| "linarith failed" + 含非线性项 | linarith 线性限制 | 换 nlinarith / positivity / ring |
| "simp made no progress" | simp 规则不匹配 | 换 simp only [具体引理] 或 unfold |
| "unknown constant" | import 缺失 | 检查 import Mathlib.* 是否覆盖 |
| "notation overloads" | 多种解释 | 加类型标注消除歧义 |
| "tactic 'omega' only handles Nat/Int" | 目标不是 Nat/Int | 换 linarith（Real） |
| "invalid occurrence of sorry" | sorry 位置错 | sorry 只能在 `by` 块内或 := by sorry |
| "unexpected end of input" | 缺少闭合括号 | 检查括号匹配 |
