---
title: "量子力学笔记（一）：集合与关系、映射与函数"
description: "从集合、有序对和二元关系出发，整理映射与函数的基础定义。"
publishDate: 2026-10-09
tags: [量子力学, 数学基础]
---

**定义（无序对，Unordered Pair）:** 由两个元素 $a$ 和 $b$ 组成的集合称为无序对，记作 $\{a, b\}$。由于集合元素的无序性，满足 $\{a, b\} = \{b, a\}$。

**定义（有序对，Ordered Pair）:** 设 $a, b$ 为任意两个对象，有序对 $(a, b)$ 定义为集合 $\{\{a\}, \{a, b\}\}$，即

$$
(a,b):=\{\{a\},\{a,b\}\}.
$$

**定理（有序对的特征性质）**：对任意 $a,b,c,d$，  

$$
(a,b)=(c,d)
$$

当且仅当 $a=c,b=d$。

**定义（笛卡儿积，Cartesian Product）：** 设 $A, B$ 为集合，所有有序对 $(a, b)$（$a \in A, b \in B$）的集合称为 $A$ 与 $B$ 的笛卡儿积，记作 $A \times B$。即

$$
A \times B = \{ (a, b) \mid a \in A \land b \in B \}
$$

**定义（二元关系，Binary Relation）：** 设 $A, B$ 为集合，$A \times B$ 的任意子集 $R$ 称为从 $A$ 到 $B$ 的二元关系。即

$$
R \subseteq A \times B
$$

若 $(x,y)\in R$，则称 $x$ 与 $y$ 满足关系 $R$，记作  

$$
xRy
$$

**定义（映射/函数，Mapping/Function）：** 设 $X, Y$ 是集合（set），一个从 $X$ 到 $Y$ 的映射是**有序三元组（ordered triple）**

$$
f = (X, Y, F),
$$

其中 $F \subseteq X \times Y$，满足：

1. 存在性（Existence）：对每个 $x \in X$，存在 $y \in Y$，使得

$$
(x, y) \in F.
$$

2. 唯一性（Uniqueness）：若 $(x, y_1) \in F$ 且 $(x, y_2) \in F$，则

$$
y_1 = y_2.
$$

满足时，称 $f$ 是从 $X$ 到 $Y$ 的映射，记作

$$
f : X \to Y.
$$

对每个 $x \in X$，把对应的 $y \in Y$ 记作

$$
f(x) = y.
$$

并称 $y$ 是 $x$ 在 $f$ 下的像（image）。
集合 $F$ 称为 $f$ 的图像（graph）。

**定义（定义域，Domain；陪域，Codomain）：** 设 $f: X \to Y$。
$X$ 称为 $f$ 的定义域，记作

$$
\text{dom}(f) = X.
$$

$Y$ 称为 $f$ 的陪域，记作

$$
\text{codom}(f) = Y.
$$

**定义（值域/像，Range/Image）：** 设 $f : X \to Y$，$f$ 的像定义为

$$
\text{im}(f) := \{f(x) : x \in X\} = \{y \in Y : \exists x \in X, f(x) = y\}.
$$

显然，

$$
\text{im}(f) \subseteq Y.
$$

**定义（原像，Preimage）：** 设 $f : X \to Y$，$B \subseteq Y$，$B$ 在 $f$ 下的原像定义为

$$
f^{-1}(B) := \{x \in X : f(x) \in B\}.
$$

特别地，对单元素 $y \in Y$，

$$
f^{-1}(\{y\}) := \{x \in X : f(x) = y\}.
$$

**定义（函数相等，Function Equality）：** 设

$$
f : X \to Y, \quad g : X' \to Y'.
$$

若 $X = X'$，$Y = Y'$，且对任意 $x \in X$，

$$
f(x) = g(x),
$$

则称 $f$ 与 $g$ 相等，记作

$$
f = g.
$$

**定义（单射，Injective）：** 设 $f : X \to Y$，若对任意 $x_1, x_2 \in X$，

$$
f(x_1) = f(x_2) \Rightarrow x_1 = x_2,
$$

则称 $f$ 是单射。

**定义（满射，Surjective）：** 设 $f : X \to Y$，若

$$
\text{im}(f) = Y.
$$

即对每个 $y \in Y$，存在 $x \in X$，使得

$$
f(x) = y.
$$

则称 $f$ 是满射。

**定义（双射，Bijective）：** 若 $f : X \to Y$ 既是单射又是满射，则称 $f$ 是双射，一一对应（One-to-one correspondence）。

**定理：** 若 $f : X \to Y$ 是双射，则存在唯一的映射

$$
f^{-1} : Y \to X,
$$

使得对任意 $x \in X$，

$$
f^{-1}(f(x)) = x,
$$

且对任意 $y \in Y$，

$$
f(f^{-1}(y)) = y.
$$

这个 $f^{-1}$ 称为 $f$ 的逆映射（Inverse mapping）。

**定义（复合，Composition）：** 设

$$
f : X \to Y, \quad g : Y \to Z.
$$

定义复合映射

$$
g \circ f : X \to Z,
$$

$$
(g \circ f)(x) := g(f(x)), \quad x \in X.
$$

**定理（复合结合律，Associativity of Composition）：** 设

$$
f : X \to Y, \quad g : Y \to Z, \quad h : Z \to W,
$$

则

$$
h \circ (g \circ f) = (h \circ g) \circ f.
$$

**定义（限制，Restriction）：** 设

$$
f : X \to Y, \quad A \subseteq X,
$$

定义 $f$ 在 $A$ 上的限制为

$$
f|_A : A \to Y, \quad f|_A(x) := f(x) \quad (x \in A).
$$

**定义（延拓，Extension）：** 设

$$
f : X \to Y, \quad X \subseteq X',
$$

若存在映射

$$
g : X' \to Y,
$$

使得

$$
g|_X = f,
$$

则称 $g$ 是 $f$ 的延拓。
