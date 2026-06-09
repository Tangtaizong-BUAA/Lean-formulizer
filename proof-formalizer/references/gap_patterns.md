# Gap Patterns

## "易得" / "显然" / "trivially"
- 试 simp / decide / omega / linarith
- 如果是等式化简，试 ring
- 如果引用引理，试 exact?

## "由对称性"
- Lean 没有对称性 tactic，需显式构造
- 方法 A：复制前段证明替换变量
- 方法 B：用 symm / Commutative

## "类似地"
- 复制前段证明模式，替换变量名
- 注意类型可能不同需 cast

## "由 AM-GM / Cauchy-Schwarz"
- 查 canonical_proofs/inequalities.md
- AM-GM: Real 相关引理
- Cauchy-Schwarz: abs_inner_le_norm

## "这是经典结论"
- 先 canonical_proofs 匹配
- 再 exact? 搜索

## "经过计算" / "化简得"
- 等式：ring / omega / linarith
- 不等式：nlinarith / positivity
- 数值：decide / norm_num

## "由归纳"
- 确定归纳变量和假设形式
- 可能需要加强归纳假设

## "不失一般性" (WLOG)
- 需显式证明 WLOG 合理性
- 通常需要排序假设或对称性论证
