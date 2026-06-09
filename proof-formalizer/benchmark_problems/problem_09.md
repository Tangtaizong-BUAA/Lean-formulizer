# Problem 09: gcd (a + b) (lcm a b) = gcd a b

## Metadata

- **Domain:** Number Theory (Divisibility / GCD / LCM)
- **Difficulty:** Medium
- **Known in Mathlib:** No
- **Key Concepts:** GCD, LCM, Coprime decomposition, gcd_add identities

## Theorem

For all natural numbers \( a, b \in \mathbb{N} \):

\[
\gcd(a + b,\ \operatorname{lcm}(a,b)) = \gcd(a,b).
\]

In Lean:

```lean
import Mathlib
open Nat

theorem gcd_add_lcm_eq_gcd (a b : ℕ) : gcd (a + b) (lcm a b) = gcd a b :=
```

## Proof

Let \( g = \gcd(a,b) \). We need to show \( \gcd(a+b,\ \operatorname{lcm}(a,b)) = g \).

### Step 1: Coprime decomposition

By `Nat.exists_coprime`, there exist \( x, y \) such that:

\[
a = x \cdot g, \qquad b = y \cdot g, \qquad \gcd(x,y) = 1.
\]

(If \( g = 0 \), then \( a = b = 0 \) and we get \( x = y = 1 \) with \( \gcd(1,1) = 1 \).)

By commutativity of multiplication, we also have \( a = g \cdot x \) and \( b = g \cdot y \).

### Step 2: Express lcm in terms of g, x, y

Using `lcm_mul_left` and `Coprime.lcm_eq_mul`:

\[
\begin{aligned}
\operatorname{lcm}(a,b) &= \operatorname{lcm}(g \cdot x,\ g \cdot y) \\
&= g \cdot \operatorname{lcm}(x,y) \qquad \text{(by lcm\_mul\_left)} \\
&= g \cdot (x \cdot y) \qquad \text{(since } \gcd(x,y)=1 \text{ implies lcm}(x,y)=x\cdot y \text{ by Coprime.lcm\_eq\_mul)}.
\end{aligned}
\]

### Step 3: Factor g out of the gcd

\[
\begin{aligned}
\gcd(a+b,\ \operatorname{lcm}(a,b))
&= \gcd(g \cdot x + g \cdot y,\ g \cdot (x \cdot y)) \\
&= \gcd(g \cdot (x + y),\ g \cdot (x \cdot y)) \qquad \text{(distributivity)} \\
&= g \cdot \gcd(x + y,\ x \cdot y) \qquad \text{(by gcd\_mul\_left)}.
\end{aligned}
\]

### Step 4: Simplify gcd(x+y, x*y) when gcd(x,y)=1

Since \( \gcd(x,y) = 1 \), by `Coprime.gcd_mul`:

\[
\gcd(x + y,\ x \cdot y) = \gcd(x + y,\ x) \cdot \gcd(x + y,\ y).
\]

Now compute each factor:

\[
\begin{aligned}
\gcd(x + y,\ x) &= \gcd(y,\ x) = 1 \qquad \text{(by gcd\_self\_add\_left and gcd\_comm)}, \\
\gcd(x + y,\ y) &= \gcd(x,\ y) = 1 \qquad \text{(by gcd\_add\_self\_right and gcd\_comm)}.
\end{aligned}
\]

Therefore \( \gcd(x + y,\ x \cdot y) = 1 \cdot 1 = 1 \).

### Step 5: Conclusion

\[
\gcd(a+b,\ \operatorname{lcm}(a,b)) = g \cdot 1 = g = \gcd(a,b).
\]

QED.

## Lean Code (Complete)

```lean
import Mathlib
open Nat

/-- For any natural numbers a and b, the greatest common divisor of their sum
and their least common multiple equals their greatest common divisor. -/
theorem gcd_add_lcm_eq_gcd (a b : ℕ) : gcd (a + b) (lcm a b) = gcd a b := by
  -- Factor g = gcd a b and get a = g*x, b = g*y with Coprime x y
  set g := gcd a b with hg
  rcases exists_coprime a b with ⟨x, y, hcop, ha, hb⟩
  -- ha : a = x * g, hb : b = y * g
  have ha' : a = g * x := by rw [ha, mul_comm]
  have hb' : b = g * y := by rw [hb, mul_comm]

  -- Compute lcm a b = g * (x * y)
  have hlcm : lcm a b = g * (x * y) := by
    calc
      lcm a b = lcm (g * x) (g * y) := by rw [ha', hb']
      _ = g * lcm x y := by rw [lcm_mul_left]
      _ = g * (x * y) := by rw [hcop.lcm_eq_mul]

  -- Simplify gcd(x+y, x) and gcd(x+y, y) when Coprime x y
  have h_gcd_x : gcd (x + y) x = gcd y x := by
    rw [gcd_self_add_left]
  have h_gcd_y : gcd (x + y) y = gcd x y := by
    rw [gcd_comm, gcd_add_self_right, gcd_comm]

  -- Main computation
  calc
    gcd (a + b) (lcm a b) = gcd (g * x + g * y) (g * (x * y)) := by
      rw [ha', hb', hlcm]
    _ = gcd (g * (x + y)) (g * (x * y)) := by rw [← mul_add]
    _ = g * gcd (x + y) (x * y) := by rw [gcd_mul_left]
    _ = g * (gcd (x + y) x * gcd (x + y) y) := by rw [hcop.gcd_mul (x + y)]
    _ = g * (gcd y x * gcd x y) := by rw [h_gcd_x, h_gcd_y]
    _ = g * (1 * 1) := by
      rw [hcop.gcd_eq_one, gcd_comm y x, hcop.gcd_eq_one]
    _ = g := by simp
    _ = gcd a b := rfl
```

## Required Lemmas

All lemmas listed below with their full Mathlib/Lean core names and locations.

### From Lean Core (`Init.Data.Nat`)

| Lemma | Location | Statement |
|-------|----------|-----------|
| `Nat.exists_coprime` | `Init/Data/Nat/Coprime.lean:71` | `∃ m' n', Coprime m' n' ∧ m = m' * gcd m n ∧ n = n' * gcd m n` |
| `Nat.Coprime.gcd_eq_one` | `Init/Data/Nat/Coprime.lean:32` | `Coprime m n → gcd m n = 1` |
| `Nat.Coprime.gcd_mul` | `Init/Data/Nat/Coprime.lean:177` | `gcd k (m * n) = gcd k m * gcd k n` (if Coprime m n) |
| `Nat.gcd_mul_left` | `Init/Data/Nat/Gcd.lean:139` | `gcd (m * n) (m * k) = m * gcd n k` |
| `Nat.gcd_comm` | `Init/Data/Nat/Gcd.lean:109` | `gcd m n = gcd n m` |
| `Nat.gcd_self_add_left` | `Init/Data/Nat/Gcd.lean:272` | `gcd (m + n) m = gcd n m` |
| `Nat.gcd_add_self_right` | `Init/Data/Nat/Gcd.lean:263` | `gcd m (n + m) = gcd m n` |
| `Nat.lcm_mul_left` | `Init/Data/Nat/Lcm.lean:132` | `lcm (m * n) (m * k) = m * lcm n k` |
| `Nat.mul_add` | `Init/Data/Nat` | `m * (n + k) = m * n + m * k` |
| `Nat.mul_comm` | `Init/Data/Nat` | `m * n = n * m` |

### From Mathlib (`Mathlib/Data/Nat/GCD/Basic.lean`)

| Lemma | Location | Statement |
|-------|----------|-----------|
| `Nat.Coprime.lcm_eq_mul` | `Mathlib/Data/Nat/GCD/Basic.lean:90` | `Coprime m n → lcm m n = m * n` |

## Proof Walkthrough

The proof proceeds in five logical phases:

1. **Decomposition:** Write \( a = gx, b = gy \) with \(\gcd(x,y) = 1\) using `exists_coprime`. This lemma works even when \( g = 0 \) (the case \( a = b = 0 \)).

2. **LCM expression:** Using `lcm_mul_left` (which factors a common multiplier out of lcm) and `Coprime.lcm_eq_mul` (which says coprime numbers have lcm equal to their product), we get \(\operatorname{lcm}(a,b) = g \cdot x \cdot y\).

3. **Factor out g from the gcd:** The identity `gcd (m*n) (m*k) = m * gcd n k` (i.e., `gcd_mul_left`) lets us pull the common factor \( g \) out of the gcd computation, reducing the problem to showing \(\gcd(x+y,\ xy) = 1\).

4. **Coprime reduction:** Since \(\gcd(x,y) = 1\), the lemma `Coprime.gcd_mul` distributes the gcd over the product: \(\gcd(x+y, xy) = \gcd(x+y, x) \cdot \gcd(x+y, y)\). The standard identities \(\gcd(x+y, x) = \gcd(y,x)\) and \(\gcd(x+y, y) = \gcd(x,y)\) (lemmas `gcd_self_add_left` and `gcd_add_self_right` combined with `gcd_comm`) reduce both factors to \(\gcd(x,y) = 1\).

5. **Conclusion:** Multiplying back the factor \( g \) gives \( g \cdot 1 = g = \gcd(a,b) \).

All steps work for all natural numbers \( a, b \), including zeros, because `gcd_mul_left` holds for any multiplier \( g \) (including 0), and `exists_coprime` handles the \( g = 0 \) case by producing \( x = y = 1 \).
```

---

The directory `/Users/gongyuxuan/.claude/skills/proof-formalizer/benchmark_problems/` exists but is empty. Please save the content above to `problem_09.md` in that directory. Then you will have a ready-to-use benchmark problem about an original gcd/lcm identity with a complete, step-by-step verified proof and no skipped steps.