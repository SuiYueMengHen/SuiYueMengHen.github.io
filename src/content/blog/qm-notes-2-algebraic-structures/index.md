---
title: "量子力学笔记（二）：代数结构初步"
description: "整理二元运算、群、环与域等代数结构的基础定义。"
publishDate: 2026-10-09
tags: [量子力学, 数学基础]
---

**定义（二元运算，Binary Operation）：** 设 $S$ 是一个非空集合，一个从 $S \times S$ 到 $S$ 的映射

$$
* : S \times S \to S, \quad (a, b) \mapsto a * b
$$

称为 $S$ 上的一个二元运算。

**定义（群，Group）：** 设 $G$ 是非空集合，$*$ 是 $G$ 上的二元运算。若满足以下三条公理，则称 $(G, *)$ 为一个群。

1. 结合律（Associativity）：对任意 $a, b, c \in G$，

$$
(a * b) * c = a * (b * c).
$$

2. 单位元存在（Identity element）：存在 $e \in G$，使得对任意 $a \in G$，

$$
a * e = e * a = a.
$$

3. 逆元存在（Inverse element）：对任意 $a \in G$，存在 $a^{-1} \in G$，使得

$$
a * a^{-1} = a^{-1} * a = e.
$$

**定义（阿贝尔群/交换群，Abelian Group/Commutative Group）：** 设 $(G, *)$ 是群，若对任意 $a, b \in G$，

$$
a * b = b * a,
$$

则称 $(G, *)$ 为阿贝尔群，或交换群。

**定义（环，Ring）：** 设 $R$ 是非空集合，$+$ 和 $\cdot$ 是 $R$ 上的两个二元运算。若满足：

1. $(R, +)$ 是阿贝尔群，其单位元记作 0，称为零元（Zero element）。
2. 乘法结合律：对任意 $a, b, c \in R$，

$$
(a \cdot b) \cdot c = a \cdot (b \cdot c).
$$

3. 分配律（Distributivity）：对任意 $a, b, c \in R$，

$$
a \cdot (b + c) = a \cdot b + a \cdot c,
$$

$$
(a + b) \cdot c = a \cdot c + b \cdot c.
$$

则称 $(R, +, \cdot)$ 是一个环。

**定义（交换环，Commutative Ring）：** 若还满足：

乘法交换律（Commutative Law of Multiplication）：对任意 $a, b \in R$，

$$
a \cdot b = b \cdot a.
$$

则称 $R$ 为交换环。

**定义（含幺环，Unital）：** 对环而言，若存在 $1 \in R$, $1 \neq 0$，使得对任意 $a \in R$，

$$
1 \cdot a = a \cdot 1 = a,
$$

则称 $R$ 为含幺环，$1$ 称为该乘法单位元（Multiplicative Identity）。

**定义（除环，Division Ring）：** 设 $R$ 是含幺环，且 $1 \neq 0$。若对任意 $a \in R$，$a \neq 0$，都存在 $a^{-1} \in R$，使得

$$
a \cdot a^{-1} = a^{-1} \cdot a = 1,
$$

则称 $R$ 为一个除环。

**定义（域，Field）：** 设 $F$ 是非空集合，$+$ 和 $\cdot$ 是 $F$ 上的两个二元运算，若满足以下三个条件，则称 $(F, +, \cdot)$ 为一个域：

1. $(F, +)$ 是阿贝尔群（Abelian Group），其加法单位元记作$0$。
2. $F^* := F \setminus \{0\}$，$(F^*, \cdot)$ 是阿贝尔群。
3. 对任意 $a, b, c \in F$，

$$
a \cdot (b + c) = a \cdot b + a \cdot c,
$$

$$
(a + b) \cdot c = a \cdot c + b \cdot c.
$$

**定理（加法零元唯一）：** 域 $F$ 中的加法单位元唯一。

**定理（加法逆元唯一）：** 对每个 $a \in F$，加法逆元 $-a$ 唯一。

**定理（乘法单位元唯一）：** 域 $F$ 中的乘法单位元唯一。

**定理（乘法逆元唯一）：** 对每个 $a \in F^*$，乘法逆元 $a^{-1}$ 唯一。

**定理（零乘性质，Zero Product Property）：** 对任意 $a \in F$，

$$
0a = 0.
$$

**定理（符号性质，Sign Properties）：** 对任意 $a, b \in F$，

$$
(-a)b = -(ab), \quad a(-b) = -(ab), \quad (-a)(-b) = ab.
$$

**定理（无零因子，Zero Divisor）：** 若 $a, b \in F$ 且

$$
ab = 0,
$$

则

$$
a = 0 \quad \text{或} \quad b = 0.
$$

**定理（消去律，Cancellation Law）：** 若 $a \neq 0$ 且

$$
ab = ac,
$$

则

$$
b = c.
$$

**定义（特征，Characteristic）：** 设 $F$ 是域，考虑元素 $1_F$ 的整数倍。若有最小正整数 $n$，使得

$$
n \cdot 1_F = \underbrace{1_F+\cdots+1_F}_{n\text{ 个}}=0,
$$

则称 $F$ 的特征为 $n$，记作

$$
\text{char} F = n.
$$

若这样的正整数不存在，则称 $F$ 的特征为 0，记作

$$
\text{char} F = 0.
$$

**定理：** 若

$$
\text{char} F = n > 0,
$$

则 $n$ 必为素数。

**定义（子域，Subfield）：** 设 $F$ 是域，$K \subseteq F$。若 $K$ 在 $F$ 的加法和乘法下本身也是域，则称 $K$ 是 $F$ 的子域。

**定义（域同态，Field Homomorphism）：** 设 $F, K$ 是域，映射

$$
\varphi : F \to K.
$$

若满足对任意 $a, b \in F$，

$$
\varphi(a + b) = \varphi(a) + \varphi(b),
$$

$$
\varphi(ab) = \varphi(a)\varphi(b),
$$

$$
\varphi(1_F) = 1_K,
$$

则称 $\varphi$ 为域同态。