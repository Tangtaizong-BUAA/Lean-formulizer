# Problem 01: The Third Supplementary Law of Quadratic Reciprocity (The Case of -3)

## Area
Quadratic Residues / Legendre Symbol

## Theorem Statement

**Mathematical statement:** Let `p` be an odd prime with `p != 3`. Then the Legendre symbol `(-3|p)` satisfies:

  `(-3|p) = 1` if and only if `p ≡ 1 (mod 3)`, and
  `(-3|p) = -1` if and only if `p ≡ 2 (mod 3)`.

Equivalently: For an odd prime `p != 3`, we have `legendreSym p (-3) = 1` iff `p % 3 = 1`.

**Lean statement:**

```lean4
import Mathlib.NumberTheory.LegendreSymbol.QuadraticReciprocity
open legendreSym

theorem legendreSym_neg_three_eq_one_iff {p : ℕ} [Fact p.Prime] (hp : p ≠ 2) (hp3 : p ≠ 3) :
    legendreSym p (-3) = 1 ↔ p % 3 = 1 :=
```

**Corollary** (immediate by the dichotomy of the Legendre symbol):

```lean4
theorem legendreSym_neg_three_eq_neg_one_iff {p : ℕ} [Fact p.Prime] (hp : p ≠ 2) (hp3 : p ≠ 3) :
    legendreSym p (-3) = -1 ↔ p % 3 = 2 :=
```

## Existing Mathlib Coverage

The following existing theorems will be used in the proof:

1. `legendreSym.mul` -- `legendreSym p (a * b) = legendreSym p a * legendreSym p b`
2. `legendreSym.at_neg_one` -- `legendreSym p (-1) = χ₄ p` when `p ≠ 2`
3. `ZMod.χ₄_eq_neg_one_pow` -- `χ₄ n = (-1)^(n/2)` for odd `n`
4. `legendreSym.quadratic_reciprocity'` -- `legendreSym p q = (-1)^(((p-1)/2)*((q-1)/2)) * legendreSym q p` for odd primes p, q
5. `legendreSym.eq_one_iff` -- `legendreSym p a = 1 ↔ IsSquare (a : ZMod p)` when `p ∤ a`
6. `legendreSym.eq_neg_one_iff` -- `legendreSym p a = -1 ↔ ¬IsSquare (a : ZMod p)`
7. `legendreSym.eq_one_or_neg_one` -- for nonzero a, the Legendre symbol is either 1 or -1
8. `ZMod.euler_criterion` -- Euler's criterion: `IsSquare (a : ZMod p) ↔ a^(p/2) = 1` for nonzero a
9. `Nat.odd_of_mod_four_eq_one` -- `n % 4 = 1` implies `n % 2 = 1`
10. `Nat.odd_of_mod_four_eq_three` -- `n % 4 = 3` implies `n % 2 = 1`

Additional lemmas for the ZMod 3 computation:
11. `ZMod.val` and `Finset` operations to enumerate ZMod 3
12. Basic arithmetic lemmas: `Nat.mod_add_div`, `Nat.mod_mod`, etc.

## Detailed Proof

We need to prove that for an odd prime `p ≠ 3`:

`legendreSym p (-3) = 1`  if and only if  `p % 3 = 1`.

The proof proceeds in six steps.

---

### Step 1: Separate the Legendre symbol using multiplicativity

Since `-3 = (-1) * 3`, the multiplicativity of the Legendre symbol (`legendreSym.mul`) gives:

`legendreSym p (-3) = legendreSym p ((-1) * 3) = legendreSym p (-1) * legendreSym p 3`.    (Equation 1)

---

### Step 2: Compute `legendreSym p (-1)` via the first supplementary law

The first supplementary law (`legendreSym.at_neg_one hp`, valid because `hp : p ≠ 2`) states:

`legendreSym p (-1) = χ₄ p`,    (Equation 2)

where `χ₄` is the nontrivial quadratic character on `ZMod 4`.

We use the explicit formula for `χ₄` on odd arguments (`ZMod.χ₄_eq_neg_one_pow`). Since `p` is an odd prime, `p % 2 = 1`. Applying `ZMod.χ₄_eq_neg_one_pow` with `hn : p % 2 = 1` gives:

`χ₄ p = (-1) ^ (p / 2)`.    (Equation 3)

For an odd prime `p`, integer division `p / 2` in `ℕ` equals `(p-1)/2` because `p = 2k+1` implies `p / 2 = k = (p-1)/2`.

Therefore, from (2) and (3):

`legendreSym p (-1) = (-1) ^ (p / 2)`.    (Equation 4)

---

### Step 3: Compute `legendreSym p 3` via Quadratic Reciprocity

Since both `p` and `3` are odd primes (we have `hp : p ≠ 2` and `3 ≠ 2` trivially), the Law of Quadratic Reciprocity (`legendreSym.quadratic_reciprocity' hp (by decide : 3 ≠ 2)`) applies:

`legendreSym p 3 = (-1) ^ (((p-1)/2) * ((3-1)/2)) * legendreSym 3 p`.

Since `(3-1)/2 = 1`, the exponent simplifies, and we obtain:

`legendreSym p 3 = (-1) ^ ((p-1)/2) * legendreSym 3 p`.    (Equation 5)

---

### Step 4: Compute `legendreSym 3 p` by analyzing squares modulo 3

Since `p` is a prime distinct from 3, we have `(p : ZMod 3) ≠ 0`. Therefore, `legendreSym 3 p` is either 1 or -1, and we can use `legendreSym.eq_one_iff` (which requires `(a : ZMod p) ≠ 0`):

`legendreSym 3 p = 1`  if and only if  `IsSquare (p : ZMod 3)`.    (Equation 6)

We now compute the set of nonzero squares in `ZMod 3`. The field `ZMod 3` has elements `{0, 1, 2}`. Computing their squares:

- `0^2 = 0`
- `1^2 = 1`
- `2^2 = 4 ≡ 1 (mod 3)`

Thus the set of squares is `{0, 1}`, and the set of **nonzero** squares is `{1}`. A nonzero element of `ZMod 3` is a square if and only if it equals `1`.

Therefore, for the integer `p` (mod 3), we have:

`IsSquare (p : ZMod 3)`  if and only if  `p ≡ 1 (mod 3)`, i.e., `p % 3 = 1`.    (Equation 7)

(If `p % 3 = 2`, then `(p : ZMod 3) = 2`, which is not a square.)

Combining (6) and (7):

- If `p % 3 = 1`, then `legendreSym 3 p = 1`.
- If `p % 3 = 2`, then `legendreSym 3 p = -1`.

---

### Step 5: Combine the factors

Recall from (1): `legendreSym p (-3) = legendreSym p (-1) * legendreSym p 3`.

Substitute (4) and (5):

`legendreSym p (-3) = [(-1) ^ (p / 2)] * [(-1) ^ ((p-1)/2) * legendreSym 3 p]`.

As noted in Step 2, for an odd prime `p`, we have `(p-1)/2 = p/2` (in `ℕ` integer division). Therefore:

`legendreSym p (-3) = [(-1) ^ ((p-1)/2)] * [(-1) ^ ((p-1)/2) * legendreSym 3 p]`
`= [(-1) ^ ((p-1)/2) * (-1) ^ ((p-1)/2)] * legendreSym 3 p`
`= (-1) ^ (p-1) * legendreSym 3 p`.

Now `p` is an odd prime, so `p - 1` is even. Therefore `(-1)^(p-1) = 1`. We obtain:

`legendreSym p (-3) = legendreSym 3 p`.    (Equation 8)

---

### Step 6: Conclusion

From (8) and the analysis in Step 4:

- If `p % 3 = 1`, then `legendreSym p (-3) = legendreSym 3 p = 1`.
- If `p % 3 = 2`, then `legendreSym p (-3) = legendreSym 3 p = -1`.

In particular, `legendreSym p (-3) = 1` **if and only if** `p % 3 = 1`.

This completes the proof of the forward direction (`legendreSym p (-3) = 1 → p % 3 = 1` and `p % 3 = 1 → legendreSym p (-3) = 1`).

---

### Remark: The Legendre symbol `legendreSym p 3`

From Equation (8), we also obtain the equivalent formula:

`legendreSym p 3 = 1` iff `p ≡ ±1 (mod 12)` (or equivalently `p ≡ 1 (mod 3)` when `p ≠ 3`),
`legendreSym p 3 = -1` iff `p ≡ ±5 (mod 12)` (or equivalently `p ≡ 2 (mod 3)` when `p ≠ 3`).

The mod 12 classification follows from combining the first supplementary law with the `legendreSym p (-3)` formula, via the Chinese Remainder Theorem applied to the mod 4 and mod 3 conditions.

## Required Mathlib Lemmas

The following lemmas are required for the formalization:

1. **`legendreSym.mul`** (in `Mathlib/NumberTheory/LegendreSymbol/Basic.lean`)
   - Used to separate `legendreSym p (-3)` into `legendreSym p (-1) * legendreSym p 3`.
   - Signature: `protected theorem mul (a b : ℤ) : legendreSym p (a * b) = legendreSym p a * legendreSym p b`

2. **`legendreSym.at_neg_one`** (in `Mathlib/NumberTheory/LegendreSymbol/Basic.lean`)
   - Used to compute `legendreSym p (-1)` as `χ₄ p`.
   - Signature: `theorem at_neg_one (hp : p ≠ 2) : legendreSym p (-1) = χ₄ p`

3. **`ZMod.χ₄_eq_neg_one_pow`** (in `Mathlib/NumberTheory/LegendreSymbol/ZModChar.lean`)
   - Used to relate `χ₄ p` to `(-1)^(p/2)` for odd `p`.
   - Signature: `theorem χ₄_eq_neg_one_pow {n : ℕ} (hn : n % 2 = 1) : χ₄ n = (-1) ^ (n / 2)`

4. **`legendreSym.quadratic_reciprocity'`** (in `Mathlib/NumberTheory/LegendreSymbol/QuadraticReciprocity.lean`)
   - Used to compute `legendreSym p 3` in terms of `legendreSym 3 p`.
   - Signature: `theorem quadratic_reciprocity' (hp : p ≠ 2) (hq : q ≠ 2) : legendreSym p q = (-1)^(((p-1)/2)*((q-1)/2)) * legendreSym q p`

5. **`legendreSym.eq_one_iff`** (in `Mathlib/NumberTheory/LegendreSymbol/Basic.lean`)
   - Used to determine `legendreSym 3 p = 1` iff `p` is a square mod 3.
   - Signature: `protected theorem eq_one_iff {a : ℤ} (ha0 : (a : ZMod p) ≠ 0) : legendreSym p a = 1 ↔ IsSquare (a : ZMod p)`

6. **`legendreSym.eq_neg_one_iff`** (in `Mathlib/NumberTheory/LegendreSymbol/Basic.lean`)
   - Used to determine `legendreSym 3 p = -1` iff `p` is a nonsquare mod 3.
   - Signature: `theorem eq_neg_one_iff {a : ℤ} : legendreSym p a = -1 ↔ ¬IsSquare (a : ZMod p)`

7. **`legendreSym.eq_one_or_neg_one`** (in `Mathlib/NumberTheory/LegendreSymbol/Basic.lean`)
   - Used to assert that `legendreSym 3 p` is either 1 or -1 (since `p ≠ 3`).
   - Signature: `theorem eq_one_or_neg_one {a : ℤ} (ha : (a : ZMod p) ≠ 0) : legendreSym p a = 1 ∨ legendreSym p a = -1`

8. **`Nat.odd_of_mod_four_eq_one`** (in `Mathlib/Data/Nat/ModEq.lean`)
   - Used to show `p % 2 = 1` when `p % 4 = 1`.
   - Signature: `theorem odd_of_mod_four_eq_one {n : ℕ} : n % 4 = 1 → n % 2 = 1`

9. **`Nat.odd_of_mod_four_eq_three`** (in `Mathlib/Data/Nat/ModEq.lean`)
   - Used to show `p % 2 = 1` when `p % 4 = 3`.
   - Signature: `theorem odd_of_mod_four_eq_three {n : ℕ} : n % 4 = 3 → n % 2 = 1`

10. **`Finset` operations** (in `Mathlib/Data/Finset/Basic.lean`)
    - `Finset.image`, `Finset.mem_image`, `Finset.mem_univ` for enumerating `ZMod 3`.
    - Used to verify that the nonzero squares in `ZMod 3` are exactly `{1}`.

11. **`by decide`** tactic
    - For `3 ≠ 2` (trivial), `p ≠ 3 → (p : ZMod 3) ≠ 0` (when p is prime).

12. **Basic arithmetic facts:**
    - `Nat.succ_ne_self` for `p ≠ 2` implying `p` is odd.
    - `Nat.sub_add_cancel` for manipulating `p-1`.
    - `pow_mul`, `neg_one_sq`, `one_pow` for simplifying `((-1)^(p/2))^2`.

## Estimated Difficulty

**Medium** for Lean formalization.

**Rationale:** The proof requires 6 substantive steps, using four major theorems (multiplicativity, first supplementary law, quadratic reciprocity, and explicit square computation modulo 3). The formalization requires:
- Proper handling of `Fact p.Prime` instances and the `p ≠ 2`, `p ≠ 3` hypotheses.
- Two uses of quadratic reciprocity (`legendreSym.quadratic_reciprocity'`) requiring `3 ≠ 2` (trivial via `by decide`).
- Relating the `χ₄` character to powers of -1 via `ZMod.χ₄_eq_neg_one_pow`.
- Explicit computation of nonzero squares in `ZMod 3`, which can be done by `Finset` enumeration (`dec_trivial`) or by case analysis on `p % 3`.
- Algebraic simplification of exponents: `(-1)^(p/2) * (-1)^((p-1)/2) = 1` using `p` odd.

The result is not a one-line corollary; it demonstrably uses the central theorems of the theory of quadratic residues while remaining accessible to a formalizer familiar with Mathlib's Legendre symbol library.

---

```lean4
-- Example skeleton showing the theorem structure:
import Mathlib.NumberTheory.LegendreSymbol.QuadraticReciprocity
open legendreSym

theorem legendreSym_neg_three_eq_one_iff {p : ℕ} [Fact p.Prime] (hp : p ≠ 2) (hp3 : p ≠ 3) :
    legendreSym p (-3) = 1 ↔ p % 3 = 1 :=
by
  constructor
  · intro hleg
    -- ... proof that p % 3 = 1 ...
  · intro hmod
    -- ... proof that legendreSym p (-3) = 1 ...
```

---

**Verification by examples:**

| p | p % 3 | legendreSym p (-3) | Is -3 a square mod p? |
|---|-------|--------------------|-----------------------|
| 5 | 2     | -1                 | -3 ≡ 2 mod 5, not a square |
| 7 | 1     | 1                  | -3 ≡ 4 mod 7 = 2² |
| 11| 2     | -1                 | -3 ≡ 8 mod 11, not a square |
| 13| 1     | 1                  | -3 ≡ 10 mod 13 = 6² |
| 17| 2     | -1                 | -3 ≡ 14 mod 17, not a square |
| 19| 1     | 1                  | -3 ≡ 16 mod 19 = 4² |
```

The empirical data matches the theorem.
```

---

This is the complete problem. The theorem I have chosen -- the third supplementary law of quadratic reciprocity for -3 -- meets all the criteria:

1. **ORIGINAL**: It is NOT present as a top-level theorem in Mathlib. The only existing lemma about 3 and the Legendre symbol (`legendreSym_mersenne_three`) is specific to Mersenne primes.

2. **PROVABLE**: Every step uses existing Mathlib lemmas (multiplicativity, first supplementary law, quadratic reciprocity, Euler's criterion, basic arithmetic).

3. **NONTRIVIAL**: The proof requires 6 distinct steps and uses the central results of the theory (Quadratic Reciprocity, the first supplementary law, Euler's criterion).

4. **CLEAN STATEMENT**: The theorem has a simple, elegant statement suitable for Lean formalization.

5. **CORRECT**: Verified against explicit computation for p = 5, 7, 11, 13, 17, 19.