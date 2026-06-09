# Common Mathlib Names (常错对照表)

| 错误（模型常猜） | 正确（Mathlib 实际） |
|---|---|
| add_comm_nat | Nat.add_comm |
| add_comm_int | Int.add_comm |
| dvd_iff_even | Nat.even_iff / Int.even_iff |
| sqrt_two_irrational | Nat.Prime.irrational_sqrt |
| prime_dvd_pow | Nat.Prime.dvd_of_dvd_pow |
| abs_add | abs_add 不直接在 ℝ 上；用 norm_add_le 或 by exact abs_add |
| coprime_iff_gcd_eq_one | Nat.Coprime.gcd_eq_one |
| even_iff_two_dvd | Nat.Even.two_dvd / Int.Even.two_dvd |
| odd_iff_not_even | Nat.odd_iff / Int.odd_iff |
| mul_comm | Mul.comm / Commutative.mul_comm |
| nat_div_mul_cancel | Nat.div_mul_cancel |
| int_div_mul_cancel | Int.div_mul_cancel |
| dvd_trans | Dvd.dvd_trans |
| dvd_gcd | Nat.dvd_gcd / Int.dvd_gcd |
| gcd_dvd_left | Nat.gcd_dvd_left |
| gcd_dvd_right | Nat.gcd_dvd_right |
| gcd_eq_one_iff | Nat.gcd_eq_one_iff_coprime |
| sq_eq_sq | Nat.sq_eq_sq / Int.sq_eq_sq |
| sum_range | Finset.sum_range_id / Finset.sum_range_succ |
| pos_of_ne_zero | Nat.pos_of_ne_zero |
| gcd_pos_of_pos_right | Nat.gcd_pos_of_pos_right |
| ne_of_gt | NE.ne_of_gt / ne_of_lt |
| not_dvd_one | 用 omega 或 contrapositive |
| prime_two | Nat.prime_two |
| irrational_sqrt | Nat.Prime.irrational_sqrt |
| le_of_dvd | Nat.le_of_dvd / Int.le_of_dvd |
| even_or_odd | Nat.even_or_odd / Int.even_or_odd |
| ring_nf | ring_nf tactic（不是引理） |
| push_cast | push_cast tactic |
| mod_cast | mod_cast tactic |
| exact_mod_cast | exact_mod_cast tactic |
