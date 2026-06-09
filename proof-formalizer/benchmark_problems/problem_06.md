---

# Problem 06: General Chinese Remainder Theorem for Natural Numbers

## Theorem Statement

The general Chinese Remainder Theorem for natural numbers. The system of two congruences `x ≡ a [MOD n]` and `x ≡ b [MOD m]` has a solution if and only if the residues `a` and `b` are congruent modulo `gcd n m`.

**Lean declaration:**

```lean4
import Mathlib.Data.Nat.ModEq

open Nat

/-- If `x` satisfies both `x ≡ a [MOD n]` and `x ≡ b [MOD m]`, then `a` and `b` are congruent
  modulo `gcd n m`. This is the necessary condition for the Chinese Remainder Theorem. -/
theorem chineseRemainder_necessity {a b m n x : ℕ} (h1 : x ≡ a [MOD n]) (h2 : x ≡ b [MOD m]) :
    a ≡ b [MOD gcd n m] := by
  have hgcd_left : gcd n m ∣ n := gcd_dvd_left n m
  have hgcd_right : gcd n m ∣ m := gcd_dvd_right n m
  have ha : x ≡ a [MOD gcd n m] := h1.of_dvd hgcd_left
  have hb : x ≡ b [MOD gcd n m] := h2.of_dvd hgcd_right
  exact (ha.symm).trans hb

/-- **General Chinese Remainder Theorem**: the system of two congruences
  `x ≡ a [MOD n]` and `x ≡ b [MOD m]` has a natural solution `x` if and only if
  `a ≡ b [MOD gcd n m]`. -/
theorem chineseRemainder_iff {a b m n : ℕ} :
    (∃ x, x ≡ a [MOD n] ∧ x ≡ b [MOD m]) ↔ a ≡ b [MOD gcd n m] := by
  constructor
  · rintro ⟨x, hx1, hx2⟩
    exact chineseRemainder_necessity hx1 hx2
  · intro h
    have ⟨k, hk⟩ := Nat.chineseRemainder' h
    exact ⟨k, hk.1, hk.2⟩
```

## Informal Proof

### Theorem 1: Necessity

**Statement:** If `x ≡ a [MOD n]` and `x ≡ b [MOD m]`, then `a ≡ b [MOD gcd n m]`.

**Proof:**

1. Since `gcd n m` divides `n` (by `Nat.gcd_dvd_left n m`), we can apply `Nat.ModEq.of_dvd` to `h1` to deduce `x ≡ a [MOD gcd n m]`.
2. Similarly, since `gcd n m` divides `m` (by `Nat.gcd_dvd_right n m`), we apply `Nat.ModEq.of_dvd` to `h2` to deduce `x ≡ b [MOD gcd n m]`.
3. By symmetry from step 1, `a ≡ x [MOD gcd n m]`.
4. By transitivity with step 2, `a ≡ b [MOD gcd n m]`.

This is the necessary condition: if a simultaneous solution exists, the two residues must be compatible modulo the gcd of the moduli.

### Theorem 2: Equivalence

**Statement:** `(∃ x, x ≡ a [MOD n] ∧ x ≡ b [MOD m]) ↔ a ≡ b [MOD gcd n m]`.

**Proof:**

**Forward direction (necessity):** This is exactly Theorem 1 above.

**Reverse direction (sufficiency):** Assume `h : a ≡ b [MOD gcd n m]`. The function `Nat.chineseRemainder' h` (defined in `Mathlib/Data/Nat/ModEq.lean`) produces a natural number `k` such that `k ≡ a [MOD n]` and `k ≡ b [MOD m]`. This function handles all edge cases (including zero moduli) explicitly. Therefore `⟨k, hk.1, hk.2⟩` provides the witness.

## Mathematical Background

The classical Chinese Remainder Theorem requires the moduli to be coprime. The general form drops this requirement: a solution exists exactly when the residues are compatible modulo the greatest common divisor of the moduli. For coprime moduli, `gcd n m = 1` and the condition `a ≡ b [MOD 1]` is always true (by `Nat.modEq_one`), recovering the classical statement.

## Required Mathlib Lemmas

| Full Name | Module | Purpose |
|---|---|---|
| `Nat.gcd_dvd_left n m` | `Mathlib.Data.Nat.GCD.Basic` | `gcd n m ∣ n` |
| `Nat.gcd_dvd_right n m` | `Mathlib.Data.Nat.GCD.Basic` | `gcd n m ∣ m` |
| `Nat.ModEq.of_dvd {a b m n : ℕ} (d : m ∣ n) (h : a ≡ b [MOD n]) : a ≡ b [MOD m]` | `Mathlib.Data.Nat.ModEq` | Reduces modulus by divisibility |
| `Nat.ModEq.symm` | `Mathlib.Data.Nat.ModEq` | Symmetry of `ModEq` |
| `Nat.ModEq.trans` | `Mathlib.Data.Nat.ModEq` | Transitivity of `ModEq` |
| `Nat.chineseRemainder' (h : a ≡ b [MOD gcd n m]) : { k // k ≡ a [MOD n] ∧ k ≡ b [MOD m] }` | `Mathlib.Data.Nat.ModEq` | Existence of solution for general CRT |

## Edge Cases Handled

- **`n = 0` or `m = 0`**: `gcd n 0 = n` and `gcd 0 m = m`. The lemma `chineseRemainder_necessity` still holds. `Nat.chineseRemainder'` has explicit branches for zero moduli (it returns `a` when `n = 0` and `b` when `m = 0`), so the reverse direction also holds.
- **`gcd n m = 0`**: This occurs only when `n = m = 0`. In this case `a ≡ b [MOD 0]` means `a = b`. Necessity: if `x ≡ a [MOD 0]` then `x = a` and `x ≡ b [MOD 0]` gives `x = b`, so `a = b`. Sufficiency: `Nat.chineseRemainder'` returns `a` (which equals `b`).

## Originality Check

This theorem is **not** present as a top-level lemma in Mathlib. The existing lemmas are:
- `Nat.chineseRemainder` (coprime case only, returns a solution without the iff)
- `Nat.chineseRemainder'` (general case, provides existence given the gcd condition, but not the equivalence)
- `Nat.modEq_and_modEq_iff_modEq_mul` (equivalence for same `a,b` with coprime moduli)

No existing lemma states the full equivalence `(∃ x, x ≡ a [MOD n] ∧ x ≡ b [MOD m]) ↔ a ≡ b [MOD gcd n m]`. The `chineseRemainder_necessity` direction is also not stated separately. This problem therefore fills a genuine gap, bundling necessity and sufficiency into a single clean equivalence.

---

This is the complete content for `problem_06.md`. All the Mathlib identifiers used have been verified to exist in the current version of Mathlib (via the source at `/Users/gongyuxuan/math-agent-workspace/.lake/packages/mathlib/`).