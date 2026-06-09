---

# Problem 03: Convolution Identities for Euler's Totient via Dirichlet Convolution

## Area
Euler's Totient / Multiplicative Functions / Dirichlet Convolution

## Theorem Statement

Let \(\varphi\) denote the Euler totient function, extended to an arithmetic function by setting \(\varphi(0) = 0\) and \(\varphi(n) = \text{Nat.totient}(n)\) for \(n \ge 1\). Let \(\zeta\) denote the constant arithmetic function defined by \(\zeta(0) = 0\) and \(\zeta(n) = 1\) for \(n \ge 1\) (the arithmetic function zeta). Let \(\mu\) denote the Möbius function, and let \(\text{id}\) denote the identity arithmetic function \(\text{id}(n) = n\). Multiplication in the ring of arithmetic functions is Dirichlet convolution:

\[(f * g)(n) = \sum_{d \cdot e = n} f(d) \cdot g(e) = \sum_{d \mid n} f(d) \cdot g(n/d).\]

Then the following identities hold:

1. **Convolution identity with zeta**:  
   \(\zeta * \varphi = \text{id}\) in the ring \(\text{ArithmeticFunction } \mathbb{N}\).  
   Equivalently, for every \(n \in \mathbb{N}\),  
   \[
   \sum_{d \mid n} \varphi(d) = n.
   \]

2. **Möbius inversion representation**:  
   \(\varphi = \mu * \text{id}\) in the ring \(\text{ArithmeticFunction } \mathbb{Z}\).  
   Equivalently, for every \(n \ge 1\),  
   \[
   \varphi(n) = \sum_{d \mid n} \mu(d) \cdot \frac{n}{d}.
   \]

In Lean notation, the main theorem statements would be:

```lean4
open ArithmeticFunction
open scoped ArithmeticFunction.Moebius

noncomputable def ArithmeticFunction.totient : ArithmeticFunction ℕ :=
  ⟨Nat.totient, by simp⟩

theorem ArithmeticFunction.zeta_mul_totient_eq_id :
    ζ * ArithmeticFunction.totient = id := ...

theorem ArithmeticFunction.totient_eq_moebius_mul_id :
    (ArithmeticFunction.totient : ArithmeticFunction ℤ) = μ * (id : ArithmeticFunction ℤ) := ...
```

## Existing Mathlib Coverage

The following relevant theorems already exist in Mathlib:

- **`Nat.totient`**: Definition of Euler's totient function.
- **`Nat.totient_one`**: `φ 1 = 1`.
- **`Nat.totient_zero`**: `φ 0 = 0`.
- **`Nat.totient_mul`**: `Nat.Coprime m n → φ (m * n) = φ m * φ n` (multiplicativity on coprime arguments).
- **`Nat.sum_totient`**: `n.divisors.sum φ = n` (sum over divisors equals n, the key ingredient).
- **`Nat.sum_totient'`**: `∑_{m ∈ range n.succ, m ∣ n} φ m = n` (variant).
- **`ArithmeticFunction.IsMultiplicative`**: The predicate defining multiplicative arithmetic functions, defined as `f 1 = 1 ∧ ∀ {m n}, m.Coprime n → f (m * n) = f m * f n`.
- **`ArithmeticFunction.isMultiplicative_zeta`**: ζ is multiplicative.
- **`ArithmeticFunction.isMultiplicative_id`**: id is multiplicative.
- **`ArithmeticFunction.isMultiplicative_moebius`**: μ is multiplicative.
- **`ArithmeticFunction.zeta_mul_apply`**: `(ζ * f) x = ∑ i ∈ divisors x, f i` (the Dirichlet convolution of ζ with f equals summation over divisors).
- **`ArithmeticFunction.mul_zeta_apply`**: `(f * ζ) x = ∑ i ∈ divisors x, f i`.
- **`ArithmeticFunction.coe_zeta_mul_coe_moebius`**: `↗ζ * ↗μ = 1` in `ArithmeticFunction R` for any `R` with `AddGroupWithOne`. This states that μ is the Dirichlet inverse of ζ.
- **`ArithmeticFunction.coe_moebius_mul_coe_zeta`**: `↗μ * ↗ζ = 1` (same by commutativity).
- **`ArithmeticFunction.id_apply`**: `id n = n`.
- **`ArithmeticFunction.instCommSemiring`**: `ArithmeticFunction ℕ` and `ArithmeticFunction ℤ` are commutative semirings (so Dirichlet convolution is commutative and associative, and the ring axioms hold).
- **`ArithmeticFunction.natCoe`**: The natural inclusion `ArithmeticFunction ℕ → ArithmeticFunction R` for any `AddMonoidWithOne R`.
- **`ArithmeticFunction.natCoe_mul`**: The inclusion is a ring homomorphism (preserves multiplication/Dirichlet convolution).

The following are **not** currently in Mathlib and would be formalized in this problem:
- `ArithmeticFunction.totient` (the definition as an arithmetic function).
- `ArithmeticFunction.zeta_mul_totient_eq_id` (the convolution identity).
- `ArithmeticFunction.totient_eq_moebius_mul_id` (Möbius inversion form).
- `ArithmeticFunction.isMultiplicative_totient` (totient is multiplicative, though this is a corollary of `Nat.totient_mul` and `Nat.totient_one`).

## Detailed Proof

We give a fully rigorous proof of both identities. For the remainder of this proof, we let \(\varphi\) denote the arithmetic function defined by \(\varphi(n) = \text{Nat.totient}(n)\) (with \(\varphi(0) = 0\) following from \(\text{Nat.totient}(0) = 0\)).

### Part 1: Proof of \(\zeta * \varphi = \text{id}\)

We need to show that for every \(n \in \mathbb{N}\),

\[(\zeta * \varphi)(n) = \text{id}(n) = n.\]

**Step 1.1: The case \(n = 0\).**  

By definition of Dirichlet convolution:
\[(\zeta * \varphi)(0) = \sum_{d \cdot e = 0} \zeta(d) \cdot \varphi(e).\]

Since \(d \cdot e = 0\) if and only if \(d = 0\) or \(e = 0\), each term in the sum involves either \(\zeta(0)\) or \(\varphi(0)\). By definition, \(\zeta(0) = 0\) and \(\varphi(0) = \text{Nat.totient}(0) = 0\). Hence every term in the sum is zero, so \((\zeta * \varphi)(0) = 0\). Also \(\text{id}(0) = 0\). Therefore the identity holds at \(n = 0\).

**Step 1.2: The case \(n > 0\).**  

For \(n > 0\), using the formula for Dirichlet convolution with \(\zeta\) (lemma `ArithmeticFunction.zeta_mul_apply`):
\[
(\zeta * \varphi)(n) = \sum_{i \in \text{divisors}(n)} \varphi(i).
\]

Here \(\text{divisors}(n)\) is the set of positive divisors of \(n\) (this is the meaning of `Finset.divisors` in Mathlib). 

By definition of \(\varphi\), for each divisor \(i \mid n\), \(\varphi(i) = \text{Nat.totient}(i)\). Hence:
\[
(\zeta * \varphi)(n) = \sum_{i \in \text{divisors}(n)} \text{Nat.totient}(i) = \sum_{i \mid n} \varphi(i).
\]

Now apply the theorem `Nat.sum_totient(n)`, which states:
\[
\sum_{i \in \text{divisors}(n)} \varphi(i) = n.
\]

This is exactly the theorem `Nat.sum_totient`. Therefore:
\[
(\zeta * \varphi)(n) = n = \text{id}(n).
\]

**Step 1.3: Conclusion.**  

Since the equality holds for every \(n \in \mathbb{N}\), by the extensionality principle for arithmetic functions (`ArithmeticFunction.ext`), we have \(\zeta * \varphi = \text{id}\) in \(\text{ArithmeticFunction } \mathbb{N}\).

This completes the proof of Part 1.

### Part 2: Proof of \(\varphi = \mu * \text{id}\)

We work in the ring \(\text{ArithmeticFunction } \mathbb{Z}\), which has a `CommSemiring` structure. The natural inclusion \(\iota: \text{ArithmeticFunction } \mathbb{N} \to \text{ArithmeticFunction } \mathbb{Z}\) is a ring homomorphism (preserving addition and Dirichlet convolution).

**Step 2.1: Lift the identity to \(\mathbb{Z}\).**  

From Part 1, we have \(\zeta * \varphi = \text{id}\) in \(\text{ArithmeticFunction } \mathbb{N}\). Applying the inclusion \(\iota\) to both sides, and using that \(\iota\) is a ring homomorphism (lemmas `ArithmeticFunction.natCoe_mul`, `ArithmeticFunction.natCoe_add`, etc.), we obtain:
\[
\iota(\zeta) * \iota(\varphi) = \iota(\text{id})
\]
in \(\text{ArithmeticFunction } \mathbb{Z}\). But \(\iota(\zeta)\) is precisely \(\zeta\) (the zeta function with values in \(\mathbb{Z}\)), \(\iota(\varphi)\) is \(\varphi\) with values in \(\mathbb{Z}\), and \(\iota(\text{id})\) is \(\text{id}\) in \(\mathbb{Z}\). So we have:
\[
\zeta * \varphi = \text{id}
\]
in \(\text{ArithmeticFunction } \mathbb{Z}\), where now all functions take values in \(\mathbb{Z}\).

**Step 2.2: Multiply by \(\mu\) on the left.**  

The Möbius function \(\mu\) is an arithmetic function with values in \(\mathbb{Z}\). By the lemma `ArithmeticFunction.coe_moebius_mul_coe_zeta`, we have:
\[
\mu * \zeta = 1
\]
in \(\text{ArithmeticFunction } \mathbb{Z}\), where \(1\) denotes the identity element for Dirichlet convolution: \(1(1) = 1\) and \(1(n) = 0\) for \(n \neq 1\).

Now multiply the equation \(\zeta * \varphi = \text{id}\) on the left by \(\mu\):

\[
\mu * (\zeta * \varphi) = \mu * \text{id}.
\]

**Step 2.3: Use associativity and the inverse property.**  

Dirichlet convolution is associative (`ArithmeticFunction.instCommSemiring` implies the ring axioms, hence associativity of multiplication). Therefore:

\[
(\mu * \zeta) * \varphi = \mu * \text{id}.
\]

By the lemma `ArithmeticFunction.coe_moebius_mul_coe_zeta`, we have \(\mu * \zeta = 1\). Substituting:

\[
1 * \varphi = \mu * \text{id}.
\]

Since \(1\) is the multiplicative identity for Dirichlet convolution, \(1 * \varphi = \varphi\). Therefore:

\[
\varphi = \mu * \text{id}
\]

in \(\text{ArithmeticFunction } \mathbb{Z}\).

**Step 2.4: Pointwise interpretation.**  

The equality \(\varphi = \mu * \text{id}\) in \(\text{ArithmeticFunction } \mathbb{Z}\) means that for every \(n \in \mathbb{N}\),

\[
\varphi(n) = (\mu * \text{id})(n) = \sum_{d \cdot e = n} \mu(d) \cdot \text{id}(e).
\]

For \(n = 0\), both sides are zero (by definition of arithmetic functions). For \(n \ge 1\), using the formula for Dirichlet convolution and the fact that \(\text{id}(e) = e\):

\[
\varphi(n) = \sum_{d \mid n} \mu(d) \cdot \frac{n}{d},
\]

where the sum runs over positive divisors \(d\) of \(n\), and \(n/d\) is the complementary divisor (which is \(\text{id}(n/d)\)). This is the classical formula expressing Euler's totient via Möbius inversion.

This completes the proof of Part 2. 

### Corollary: Multiplicativity of \(\varphi\) (Optional)

Although not required for the main theorem, we note that \(\varphi\) is a multiplicative arithmetic function. Indeed:

1. **Value at 1**: \(\varphi(1) = \text{Nat.totient}(1) = 1\) (lemma `Nat.totient_one`).
2. **Multiplicativity**: For coprime \(m, n\), \(\varphi(mn) = \varphi(m) \cdot \varphi(n)\) (lemma `Nat.totient_mul`).

Thus by the definition of `ArithmeticFunction.IsMultiplicative`, we have `ArithmeticFunction.IsMultiplicative (φ : ArithmeticFunction ℕ)`.

## Required Mathlib Lemmas

Here is a complete list of Mathlib lemmas needed for the formalization, organized by category:

### Definitions to Create
- `ArithmeticFunction.totient` -- the arithmetic function wrapping `Nat.totient`.

### From `Mathlib/Data/Nat/Totient.lean`
- `Nat.totient` (definition)
- `Nat.totient_zero` -- `φ 0 = 0`
- `Nat.totient_one` -- `φ 1 = 1` (used for IsMultiplicative proof)
- `Nat.totient_mul` -- `Nat.Coprime m n → φ (m * n) = φ m * φ n` (used for IsMultiplicative proof)
- `Nat.sum_totient` -- `n.divisors.sum φ = n` (the crucial identity for Part 1)

### From `Mathlib/NumberTheory/ArithmeticFunction/Defs.lean`
- `ArithmeticFunction` (definition)
- `ArithmeticFunction.ext` -- extensionality: `(∀ n, f n = g n) → f = g`
- `ArithmeticFunction.instCommSemiring` -- commutative semiring structure; provides the ring axioms (associativity, commutativity, distributivity) for Dirichlet convolution
- `ArithmeticFunction.mul_apply` -- `(f * g) n = ∑_{d*e = n} f d * g e`
- `ArithmeticFunction.IsMultiplicative` (definition, for the corollary)
- `ArithmeticFunction.IsMultiplicative.iff_ne_zero` -- characterization of multiplicative functions

### From `Mathlib/NumberTheory/ArithmeticFunction/Misc.lean`
- `ArithmeticFunction.id` -- the identity arithmetic function `id n = n`
- `ArithmeticFunction.id_apply` -- `id n = n`
- `ArithmeticFunction.isMultiplicative_id` (for the corollary)

### From `Mathlib/NumberTheory/ArithmeticFunction/Zeta.lean`
- `ArithmeticFunction.zeta` -- the zeta arithmetic function (defined earlier, used implicitly)
- `ArithmeticFunction.zeta_apply` -- `ζ 0 = 0` and `ζ n = 1` for `n ≠ 0`
- `ArithmeticFunction.zeta_mul_apply` -- `(ζ * f) x = ∑ i ∈ divisors x, f i` (for `f : ArithmeticFunction ℕ`)
- `ArithmeticFunction.coe_zeta_mul_apply` -- the general version over any semiring `R`

### From `Mathlib/NumberTheory/ArithmeticFunction/Moebius.lean`
- `ArithmeticFunction.moebius` -- definition of the Möbius function μ
- `ArithmeticFunction.moebius_apply_one` -- `μ 1 = 1`
- `ArithmeticFunction.coe_moebius_mul_coe_zeta` -- `↗μ * ↗ζ = 1` in `ArithmeticFunction R` for any `R` with `AddGroupWithOne`. This asserts that μ is the Dirichlet inverse of ζ.
- `ArithmeticFunction.coe_zeta_mul_coe_moebius` -- `↗ζ * ↗μ = 1` (commutative version)

### From `Mathlib/NumberTheory/ArithmeticFunction/Defs.lean` (coercion)
- `ArithmeticFunction.natCoe` -- the inclusion `ArithmeticFunction ℕ → ArithmeticFunction R` for any `AddMonoidWithOne R`
- `ArithmeticFunction.natCoe_mul` -- `↗(f * g) = ↗f * ↗g` (coercion preserves convolution)
- `ArithmeticFunction.natCoe_add` -- coercion preserves addition
- `ArithmeticFunction.natCoe_one` -- `↗(1 : ArithmeticFunction ℕ) = 1`

### Finset / Divisor utilities
- `Nat.divisors` -- the set of divisors of n
- `Finset.sum` -- basic summation properties (used implicitly in the proof)

## Estimated Difficulty
**Medium** for Lean formalization.

**Rationale**:
- The definition of `ArithmeticFunction.totient` is straightforward (one line).
- The proof of `zeta_mul_totient_eq_id` is essentially a single `simp` call using `ArithmeticFunction.zeta_mul_apply`, `ArithmeticFunction.id_apply`, and `Nat.sum_totient`, plus case analysis on `n = 0` vs `n > 0` (since `zeta_mul_apply` works for all `x` but `Nat.sum_totient` needs special handling at `n = 0`).
- The proof of `totient_eq_moebius_mul_id` requires algebraic manipulation in `ArithmeticFunction ℤ` using the ring structure, the inclusion from ℕ, and the `mu * zeta = 1` lemma.
- Care must be taken with the coercion from ℕ to ℤ and the ring operations: the equation `zeta_mul_totient_eq_id` is proved in ℕ but needs to be lifted to ℤ for the Möbius inversion step.
- The total proof is expected to be approximately 15-25 lines of Lean code (excluding the definition).