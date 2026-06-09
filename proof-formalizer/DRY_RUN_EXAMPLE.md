# Dry Run Example: √2 Irrationality

## Input
```
√2 是无理数。反证法。假设 √2 = a/b，其中 a、b 互素。
则 a² = 2b²，故 2 | a²，从而 2 | a。
设 a = 2k，代入得 4k² = 2b²，即 b² = 2k²，故 2 | b²，从而 2 | b。
但 2 | a 且 2 | b 与 gcd(a,b) = 1 矛盾。
```

## Intake 产出
- 定理陈述：`¬ ∃ (a b : ℕ), b ≠ 0 ∧ Nat.Coprime a b ∧ a^2 = 2 * b^2`
- 符号：√2 → Real.sqrt 2, 互素 → Nat.Coprime, | → Dvd
- 前置：Nat.Coprime, Nat.Prime.dvd_of_dvd_pow, Nat.dvd_gcd

## Segment 切分（5 段）

| id | original_text | type | math_keywords | gap_size |
|----|--------------|------|---------------|----------|
| 01 | 假设 √2 = a/b, a,b 互素 | explicit | ["√2","有理数","互素","反证法"] | small |
| 02 | 则 a² = 2b², 故 2\|a² | elided_calc | ["平方","整除"] | small |
| 03 | 从而 2\|a | elided_lemma | ["素数","整除","prime"] | medium |
| 04 | 设 a=2k, 代入得 b²=2k², 故 2\|b², 从而 2\|b | elided_calc | ["代入","整除"] | medium |
| 05 | 2\|a 且 2\|b 与 gcd=1 矛盾 | explicit | ["gcd","矛盾","coprime"] | small |

## MatchCanonical

- 整个定理陈述匹配 **IR-01** (√p 无理性)
- 关键词交集：√2, irrational, prime, 无理 → ≥2 匹配
- **Action**: 直接套用 IR-01 one-line proof

```lean
theorem sqrt_two_irrational : Irrational (Real.sqrt 2) :=
  Nat.prime_two.irrational_sqrt
```

**如果用户要求手动证明**（而非一行版），则 IR-01 的 manual 证明模板被贴入，各段对应：
- 段01 → `rintro ⟨a, b, hb, hcop, hsq⟩`
- 段02+03 → `have hpa : p ∣ a := hp.dvd_of_dvd_pow ⟨b ^ 2, hsq⟩` (canonical NT-02 匹配)
- 段04 → `obtain ⟨k, hk⟩ := hpa` + `have hpb : p ∣ b := ...`
- 段05 → `have : p ∣ a.gcd b := Nat.dvd_gcd hpa hpb` + `rw [hcop.gcd_eq_one] at this` + `omega` (canonical NT-03 匹配)

## AlignAndSearch (对手动版的段02)

如果段02 没命中 canonical：
- `mathlib_lookup.sh` 返回：
  1. `Nat.Prime.dvd_of_dvd_pow` — score 0.9
  2. `Nat.dvd_gcd` — score 0.5
- 预测 tactic: `exact hp.dvd_of_dvd_pow ⟨b^2, hsq⟩`
- 预测结构: `have hpa : 2 ∣ a := by ...`

## Scaffold

```lean
import Mathlib

theorem sqrt_two_irrational_manual :
    ¬ ∃ (a b : ℕ), b ≠ 0 ∧ Nat.Coprime a b ∧ a ^ 2 = 2 * b ^ 2 := by
  -- 段 01：假设 √2 = a/b, a,b 互素
  sorry
  -- 段 02+03：a² = 2b², 故 2|a
  sorry
  -- 段 04：设 a=2k, 代入得 b²=2k², 故 2|b
  sorry
  -- 段 05：2|a 且 2|b 与 gcd=1 矛盾
  sorry
```

## Formalize 演示

### 段01：canonical 无匹配 → mathlib_lookup → goal_state_extract
- goal: `⊢ ¬ ∃ (a b : ℕ), b ≠ 0 ∧ Nat.Coprime a b ∧ a ^ 2 = 2 * b ^ 2`
- 写：`rintro ⟨a, b, hb, hcop, hsq⟩`
- validate → 成功

### 段02+03：canonical NT-02 匹配
- 直接贴：`have h2a : (2 : ℕ) ∣ a := Nat.prime_two.dvd_of_dvd_pow ⟨b ^ 2, hsq⟩`
- validate → 成功

### 段04：
- goal_state_extract 显示：`a b : ℕ, hb, hcop, hsq, h2a : 2 ∣ a ⊢ False`
- 写：`obtain ⟨k, hk⟩ := h2a`
- 然后：`have h2b : (2 : ℕ) ∣ b := Nat.prime_two.dvd_of_dvd_pow ⟨k ^ 2, by linarith [show (2*k)^2 = 2*b^2 from by rw [← hsq, hk]; ring]⟩`
- validate → 如果 linarith 通过则成功

### 如果段04失败（linarith 不闭合）：
- Diagnose: [A] 本段写错
- 升级重试：改用 nlinarith 或 ring 协助
- 仍失败 → sorry 推进

### 段05：canonical NT-03 匹配
- 贴：`have : (2 : ℕ) ∣ a.gcd b := Nat.dvd_gcd h2a h2b`
- `rw [hcop.gcd_eq_one] at this`
- `omega`

## 关键观察

1. **Canonical 命中 3/5 段**（NT-02, NT-02 again, NT-03），省了 3 次 LLM 调用
2. **IR-01 直接匹配整个定理**——如果用户接受一行版，直接完成
3. **Goal state 驱动避免了之前的"盲猜 tactic"问题**
4. **3 次预算足够**：canonical 1 次 + 手动 1 次 + 升级 1 次
