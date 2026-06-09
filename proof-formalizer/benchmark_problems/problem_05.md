# Problem 05: Sum of Fibonacci Squares

## Area
Fibonacci Numbers / Linear Recurrences

## Theorem Statement

**Theorem (Sum of Fibonacci Squares).** For all natural numbers `n`,

\[
\sum_{k=1}^{n} F_k^2 = F_n \cdot F_{n+1},
\]

where `F_k` denotes the `k`-th Fibonacci number, defined by `F_0 = 0`, `F_1 = 1`, and `F_{n+2} = F_{n+1} + F_n` for all `n`.

In Lean:
```lean4
theorem fib_sum_squares (n : ℕ) : (∑ k in Finset.range n, (Nat.fib (k + 1)) ^ 2) = Nat.fib n * Nat.fib (n + 1) :=
```

## Existing Mathlib Coverage

- `Nat.fib` — Fibonacci numbers defined
- `Nat.fib_zero`, `Nat.fib_one`, `Nat.fib_add_two` — basic properties
- `Nat.fib_add`, `Nat.fib_two_mul`, `Nat.fib_two_mul_add_one` — addition/doubling formulas
- `Nat.fib_gcd`, `Nat.fib_dvd` — divisibility properties
- `Int.fib_succ_mul_fib_pred_sub_fib_sq` — Cassini's identity (in ℤ)
- `Int.fib_add_sq_sub_fib_mul_fib_add_two_mul` — Catalan's identity (in ℤ)
- Sum of squares identity is **NOT in Mathlib**

## Detailed Proof

Let `F_n` denote `Nat.fib n`. We proceed by induction on `n`.

**Base case `n = 0`:**

We must show:
\[
\sum_{k=0}^{-1} F_{k+1}^2 = F_0 \cdot F_1.
\]

The left-hand side is the empty sum, which equals `0`. The right-hand side is `F_0 \cdot F_1 = 0 \cdot 1 = 0`. Thus `0 = 0` holds.

**Inductive hypothesis:**

Assume the theorem holds for some arbitrary `n`. That is:
\[
\sum_{k=0}^{n-1} F_{k+1}^2 = F_n \cdot F_{n+1}.
\tag{IH}
\]

**Inductive step (prove for `n+1`):**

We must show:
\[
\sum_{k=0}^{n} F_{k+1}^2 = F_{n+1} \cdot F_{n+2}.
\]

Starting from the left-hand side:

**Step 1 — Decompose the sum:**
The sum over `range (n+1)` equals the sum over `range n` plus the term indexed by `n`:
\[
\sum_{k \in \text{range}(n+1)} f(k) = \left(\sum_{k \in \text{range}(n)} f(k)\right) + f(n).
\]
Here `f(k) = F_{k+1}^2`, so `f(n) = F_{n+1}^2`. This is justified by `Finset.sum_range_succ`.

**Step 2 — Apply inductive hypothesis:**
The sum over `range n` of `F_{k+1}^2` equals `F_n * F_{n+1}` by the inductive hypothesis (IH):
\[
= (F_n \cdot F_{n+1}) + F_{n+1}^2
\]

**Step 3 — Factor:**
Distribute `F_{n+1}`:
\[
F_n \cdot F_{n+1} + F_{n+1}^2 = F_{n+1} \cdot (F_n + F_{n+1})
\]
This uses distributivity of multiplication over addition in `ℕ`:
`a * c + b * c = (a + b) * c` (via `Nat.add_mul` or `Nat.mul_add` with commutativity).

First, note that `F_{n+1}^2 = F_{n+1} * F_{n+1}` by definition of squaring.
Then `F_n * F_{n+1} + F_{n+1} * F_{n+1} = F_{n+1} * F_n + F_{n+1} * F_{n+1}` (by commutativity `Nat.mul_comm`).
Now `F_{n+1} * F_n + F_{n+1} * F_{n+1} = F_{n+1} * (F_n + F_{n+1})` (by `Nat.mul_add`: `a*(b+c) = a*b + a*c`).

**Step 4 — Apply Fibonacci recurrence:**
By the Fibonacci recurrence `Nat.fib_add_two`:
\[
F_{n+2} = F_n + F_{n+1}
\]
Therefore:
\[
F_{n+1} \cdot (F_n + F_{n+1}) = F_{n+1} \cdot F_{n+2}
\]

**Step 5 — Rewrite index:**
Note that `(n+1) + 1 = n+2`, so `F_{(n+1)+1} = F_{n+2}`:
\[
F_{n+1} \cdot F_{n+2} = F_{n+1} \cdot F_{(n+1)+1}
\]

Thus the equality holds for `n+1`. By the principle of mathematical induction, the theorem holds for all `n : Nat`.

### Verification of Small Values

| `n` | `F_n` | `F_{n+1}` | `F_n * F_{n+1}` | `\sum_{k=0}^{n-1} F_{k+1}^2` |
|-----|-------|-----------|-----------------|------------------------------|
| 0   | 0     | 1         | 0               | 0                            |
| 1   | 1     | 1         | 1               | 1                            |
| 2   | 1     | 2         | 2               | 1 + 1 = 2                    |
| 3   | 2     | 3         | 6               | 1 + 1 + 4 = 6                |
| 4   | 3     | 5         | 15              | 1 + 1 + 4 + 9 = 15           |
| 5   | 5     | 8         | 40              | 1 + 1 + 4 + 9 + 25 = 40      |

All values match.

## Required Mathlib Lemmas

1. `Nat.fib_zero` — `Nat.fib 0 = 0` (base case)
2. `Nat.fib_one` — `Nat.fib 1 = 1` (base case)
3. `Nat.fib_add_two` — `Nat.fib (n + 2) = Nat.fib n + Nat.fib (n + 1)` (recurrence)
4. `Finset.sum_range_succ` — `(∑ x in range (n+1), f x) = (∑ x in range n, f x) + f n`
5. `Finset.sum_range_zero` — `(∑ x in range 0, f x) = 0`
6. `Nat.mul_add` — `a * (b + c) = a * b + a * c`
7. `Nat.mul_comm` — `a * b = b * a`
8. `Nat.add_comm` — `a + b = b + a`
9. `Nat.succ_eq_add_one` — `Nat.succ n = n + 1`

## Estimated Difficulty

Medium — Straightforward induction with one algebraic manipulation, but requires familiarity with Finset sums and Fibonacci lemmas.

## Lean Formalization Sketch

```lean4
import Mathlib.Data.Nat.Fib.Basic
import Mathlib.Data.Finset.Basic
import Mathlib.Tactic

open Finset

theorem fib_sum_squares (n : ℕ) : (∑ k in range n, (Nat.fib (k + 1)) ^ 2) = Nat.fib n * Nat.fib (n + 1) := by
  induction n with
  | zero =>
    simp [Nat.fib_zero, Nat.fib_one]
  | succ n ih =>
    rw [sum_range_succ, ih]
    calc
      Nat.fib n * Nat.fib (n + 1) + (Nat.fib (n + 1)) ^ 2
          = Nat.fib (n + 1) * (Nat.fib n + Nat.fib (n + 1)) := by ring
      _ = Nat.fib (n + 1) * Nat.fib (n + 2) := by rw [Nat.fib_add_two]
      _ = Nat.fib (n + 1) * Nat.fib ((n + 1) + 1) := rfl
```
