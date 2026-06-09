# Tactic by Goal Shape

## Goal 形如 `a = b`（等式）
- 首选：`rfl` / `ring` / `ring_nf`
- 后备：`simp` / `linear_combination` / `omega`（Nat/Int）
- 计算：`norm_num` / `decide`

## Goal 形如 `a ≤ b`（线性不等式）
- Nat/Int：`omega`
- Real：`linarith`
- 含乘法：`nlinarith` / `positivity`
- 含范数：`gcongr` / `bound`

## Goal 形如 `a ∣ b`（整除）
- 构造证人：`use k; ring` / `use k; linarith`
- 推理：`Nat.Prime.dvd_of_dvd_pow` / `Int.dvd_gcd`
- 常数：`omega`（仅 Nat/Int 常数）

## Goal 形如 `∃ x, P x`（存在）
- 首选：`use x` / `refine ⟨?_, ?_⟩`
- 非构造性：`Classical.choice`

## Goal 形如 `∀ x, P x`（全称）
- 首选：`intro x`

## Goal 形如 `P ∧ Q`
- 首选：`constructor` / `⟨?_, ?_⟩`

## Goal 形如 `P ∨ Q`
- 首选：`left` / `right` / `by_cases`

## Goal 形如 `¬ P`
- 首选：`intro h` / `push_neg`

## Goal 含 `Irrational`
- 查 canonical_proofs/irrationality.md
- 一行版：`hp.irrational_sqrt`

## Goal 含 `Prime`
- `Nat.Prime.*` 家族
- `dvd_of_dvd_pow` / `dvd_iff_not_coprime`

## Goal 含 `Even` / `Odd`
- `Nat.even_iff` / `Int.even_iff`
- `.two_dvd` / `.two_dvd.mp`

## Goal 含 `Coprime`
- `Nat.Coprime.gcd_eq_one`
- `Nat.Coprime.mul_dvd_of_dvd_of_dvd`

## Goal 含 `gcd`
- `Nat.dvd_gcd` / `Nat.gcd_dvd_left` / `Nat.gcd_dvd_right`
- `Nat.gcd_eq_one_iff_coprime`

## Goal 含 cast（Nat→Int→Real）
- `push_cast` / `exact_mod_cast` / `mod_cast`
- `Int.cast_ne_zero` / `Nat.cast_le`

## Goal 含 `∑`（求和）
- `Finset.sum_range_id` / `Finset.sum_range_succ`
- `simp [Finset.sum_add_distrib]`
