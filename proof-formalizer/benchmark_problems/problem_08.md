定理：** 设 S 是一个有限非空的素数集合，且 2 ∈ S。则有理数 Σ_{p∈S} 1/p 不是整数。等价地，对任意 n≥1，前 n 个素数的倒数和 ∑_{k=1}^n 1/p_k 不是整数。

**详细证明：**

**1. 设定。** 设 S = {p_1, p_2, ..., p_n}，其中 p_1 = 2，p_2, ..., p_n 是奇素数。定义 P = ∏_{p∈S} p，即 S 中所有元素的乘积。定义有理数 R = Σ_{p∈S} 1/p = Σ_{k=1}^n 1/p_k。

**2. 通分。** 将 R 写为公分母 P 的形式：
   R = (Σ_{k=1}^n P/p_k) / P。
   因此，N := R * P = Σ_{k=1}^n P/p_k。

**3. N 的奇偶性。** 我们需要证明 N 是奇数。
   - **情况 k=1（对应素数 2）。** P/p_1 = P/2 = ∏_{k=2}^n p_k，即奇素数 p_2, p_3, ..., p_n 的乘积。奇数的乘积是奇数，因此 P/2 是奇数。当 S = {2} 且 n=1 时，P/2 是空乘积，定义为 1，也是奇数。
   - **情况 k≥2（对应奇素数）。** 对每个 k≥2，P/p_k 的因式分解包含因子 p_1 = 2，因为 p_k 是唯一被移除的因子。因此 P/p_k 是偶数。
   - 所以 N = (奇数) + (偶数) + (偶数) + ... + (偶数) = 奇数。

**4. R 的整性条件。** 如果 R 是整数，则 N = R * P 必然是偶数，因为：
   - P 是偶数（因为它包含因子 p_1 = 2）。
   - 偶数乘以任何整数都是偶数。
   因此，如果 R 是整数，则 N 是偶数。

**5. 矛盾。** 第 3 步证明 N 是奇数；第 4 步证明如果 R 是整数则 N 是偶数。奇数和偶数不能相同。矛盾。因此 R 不是整数。

**所需 Mathlib 引理：**

1. **`Nat.Prime.eq_two_or_odd`** (`Data/Nat/Prime/Defs.lean`) -- 每个素数要么是 2，要么是奇数。用于证明 S 中除 2 以外的每个素数都是奇数。

2. **`Nat.odd_mul`** (`Algebra/Ring/Parity.lean`) -- 自然数 a 和 b 的积是奇数当且仅当 a 和 b 都是奇数。用于证明（奇）素数的乘积是奇数。

3. **`Nat.even_mul`** (`Algebra/Group/Nat/Even.lean`) -- 偶数和任何整数的积是偶数。更一般地，`Even.mul_left`（在 `Algebra/Ring/Parity.lean` 中）说：如果 a 是偶数，那么对任意 b，a*b 是偶数。用于证明如果 R 是整数，则 N = R*P 是偶数。

4. **`Nat.even_iff_two_dvd`** (`Algebra/Ring/Parity.lean`) -- 一个数是偶数当且仅当它能被 2 整除。用于连接偶数和可除性。

5. **`Nat.odd_iff_not_even`** (或 `Nat.not_even_iff`) -- 一个数是奇数当且仅当它不是偶数。用于得出 N 不是偶数因此不能被 2 整除的结论。

6. **`Nat.Prime.one_lt`** (`Data/Nat/Prime/Defs.lean`) -- 如果 p 是素数，则 1 < p。用于确保素数非零。

7. **`Nat.Prime.ne_zero`** (`Data/Nat/Prime/Defs.lean`) -- 如果 p 是素数，则 p ≠ 0。需要用于 Finset 乘积。

8. **`Finset.prod_insert`** 和 **`Finset.prod_empty`** (`Data/Finset/Basic.lean`) -- 用于操作 Finset 乘积。

9. **`Finset.sum_add_distrib`** -- 和的基本代数性质。

10. **`Nat.dvd_of_mod_eq_zero`** (`Data/Nat/Dvd.lean`) -- 可除性和模算术之间的联系。

11. **`Nat.Prime.dvd_primorial`** (`NumberTheory/Primorial.lean`) -- 素数 p 整除 p#。或者，我们直接使用乘积中 2 整除 P 的事实。

12. **`Nat.Prime.two_le`** (`Data/Nat/Prime/Defs.lean`) -- 每个素数至少为 2。

13. **`Odd.mul`** (`Algebra/Ring/Parity.lean`) -- 如果 a 是奇数且 b 是奇数，则 a*b 是奇数。（`Nat.odd_mul` 的类似结果，以函数形式给出。）

14. **`Nat.Odd.of_mul_right`** (`Algebra/Ring/Parity.lean`) -- 乘积为奇数的推理。

15. **`Nat.two_mul`** / **`Nat.mul_two`** -- 乘以 2 的基本算术。

**关于形式化的说明：** 该定理可以用几种等效方式表述。一种直接的方式是采用 `Finset ℕ` 并表述为 `¬ (∑ p in S, (1 : ℚ) / (p : ℚ)) ∈ (algebraMap ℤ ℚ).range`。或者，人们可以纯粹在 ℕ 中工作，表述为 `¬ (∏ p in S, p) ∣ (∑ p in S, (∏ q in S, q) / p)`，这意味着分母不能整除分子。

由于 READ-ONLY 限制，我无法将文件写入磁盘，但可以将上述内容作为有效的 Markdown 内容保存到 `/Users/gongyuxuan/.claude/skills/proof-formalizer/benchmark_problems/problem_08.md`。