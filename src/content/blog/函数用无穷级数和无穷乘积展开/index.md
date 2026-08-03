---
title: 函数用无穷级数和无穷乘积展开
description: 请用一到两句话概括文章内容，建议 30—80 字。
publishDate: '2026-08-03'
category: 未分类
tags:
- 待整理
featured: false
draft: false
autoNumbering: true
showContents: true
showSideToc: true
collection: 特殊函数概论
collectionOrder: 1
---

# 伯努利多项式与伯努利数

## 生成函数与定义

伯努利多项式 $\phi_n(x)$（$n = 0,1,2,\ldots$）由以下生成函数展开式给出：

> **定义（伯努利多项式）**  
> $$
> \frac{t e^{x t}}{e^{t} - 1} = \sum_{n = 0}^{\infty} \frac{t^n}{n!} \phi_n(x).
> $$  
> 该级数在 $|t| < 2\pi$ 时收敛，因为生成函数离 $t=0$ 最近的奇点为 $t = \pm 2\pi i$。

当 $x = 0$ 时，得到伯努利数：

> **定义（伯努利数）**  
> 令 $\phi_n = \phi_n(0)$，则  
> $$
> \frac{t}{e^{t} - 1} = \sum_{n = 0}^{\infty} \frac{t^n}{n!} \phi_n.
> $$  
> 称 $\phi_n$ 为伯努利数。

由生成函数的偶性可得伯努利数的奇偶性：

> **性质（奇偶性）**  
> $$
> \phi_0 = 1,\qquad \phi_1 = -\frac{1}{2},
> $$  
> $$
> \phi_{2k} = (-1)^{k-1} B_k,\qquad \phi_{2k+1} = 0 \quad (k = 1,2,\ldots),
> $$  
> 其中 $B_k$ 为通常定义的伯努利数。上式源于恒等式  
> $$
> \frac{t}{2}\frac{e^{t/2}+e^{-t/2}}{e^{t/2}-e^{-t/2}} = 1 + \sum_{n=1}^{\infty} (-1)^{n-1} \frac{t^{2n}}{(2n)!} B_n,
> $$  
> 该式左端为偶函数。

---

## 显明表达式与递推关系

利用生成函数展开，可以得到伯努利多项式的显明表达式：

> **定理（显明表达式）**  
> $$
> \phi_n(x) = \sum_{k=0}^{n} \binom{n}{k} \phi_k x^{n-k},\qquad n = 0,1,2,\ldots
> $$  
> 可用符号形式记为  
> $$
> \phi_n(x) = (\phi + x)^n,
> $$  
> 其中展开后需将 $\phi^k$ 替换为 $\phi_k$。

由恒等式 $\frac{e^t-1}{t} \cdot \frac{t}{e^t-1} = 1$ 可得伯努利数的递推关系：

> **定理（递推关系）**  
> $$
> \phi_0 = 1,
> $$  
> $$
> \sum_{k=0}^{n-1} \frac{1}{k!(n-k)!} \phi_k = 0 \quad (n \geq 2).
> $$  
> 其符号形式为  
> $$
> (\phi + 1)^n - \phi_n = 0 \quad (n = 2,3,\ldots).
> $$

---

## 基本性质

### 微商与积分

由显明表达式直接求导可得：

> **性质（微商）**  
> $$
> \frac{d}{dx}\phi_n(x) = n\,\phi_{n-1}(x),
> $$  
> 进而  
> $$
> \frac{d^p}{dx^p}\phi_n(x) = \frac{n!}{(n-p)!}\,\phi_{n-p}(x).
> $$

由此导出积分公式：

> **性质（积分）**  
> $$
> \int_a^x \phi_n(y)\,dy = \frac{1}{n+1}\big[\phi_{n+1}(x) - \phi_{n+1}(a)\big].
> $$

### 差分关系

由生成函数比较 $t^n$ 的系数可得：

> **性质（差分）**  
> $$
> \phi_0(x+1) = \phi_0(x),
> $$  
> $$
> \phi_1(x+1) = \phi_1(x) + 1,
> $$  
> $$
> \phi_n(x+1) = \phi_n(x) + n x^{n-1} \quad (n \geq 2).
> $$

### 互余宗量关系

利用生成函数在 $x \to 1-x$ 下的变换：

> **性质（互余宗量）**  
> $$
> \phi_n(1-x) = (-1)^n \phi_n(x).
> $$

### 加法公式

由生成函数的指数性质：

> **性质（加法公式）**  
> $$
> \phi_n(x+y) = \sum_{k=0}^{n} \binom{n}{k} \phi_k(y)\,x^{n-k}.
> $$

---

## 求和公式

由差分关系可导出幂和公式：

> **推论（求和公式）**  
> 对于 $n \geq 1$，  
> $$
> \sum_{s=1}^{m} s^n = \frac{1}{n+1}\big[\phi_{n+1}(m+1) - \phi_{n+1}\big],
> $$  
> 其中 $\phi_{n+1} = \phi_{n+1}(0)$。

---

## 与三角函数的联系

从生成函数还可得到余切、正切、余割的展开式：

> **性质（三角函数展开）**  
> $$
> \frac{t}{2}\cot\frac{t}{2} = 1 - \sum_{n=1}^{\infty} \frac{B_n}{(2n)!} t^{2n} \quad (|t| < 2\pi),
> $$  
> $$
> \frac{t}{2}\tan\frac{t}{2} = \sum_{n=1}^{\infty} \frac{(2^{2n} - 1)B_n}{(2n)!} t^{2n} \quad (|t| < \pi),
> $$  
> $$
> t\csc t = 1 + \sum_{n=1}^{\infty} \frac{2(2^{2n-1} - 1)B_n}{(2n)!} t^{2n} \quad (|t| < \pi).
> $$

# 欧勒多项式与欧勒数

## 生成函数与定义

欧勒多项式 $E_n(x)$（$n = 0,1,2,\ldots$）由以下生成函数展开式给出：

> **定义（欧勒多项式）**  
> $$
> \frac{2 e^{x t}}{e^{t} + 1} = \sum_{n = 0}^{\infty} \frac{t^n}{n!} E_n(x).
> $$  
> 该级数在 $|t| < \pi$ 时收敛，因为生成函数离 $t=0$ 最近的奇点为 $t = \pm \pi i$。

令 $x = \frac{1}{2}$ 时，生成函数成为偶函数，由此引出欧勒数：

> **定义（欧勒数）**  
> 令  
> $$
> \frac{2 e^{t/2}}{e^{t} + 1} = \operatorname{sech}\frac{t}{2} = \sum_{n = 0}^{\infty} \frac{(-1)^n E_n}{(2n)!} \left(\frac{t}{2}\right)^{2n},
> $$  
> 其中  
> $$
> E_n = (-1)^n 2^{2n} E_{2n}\left(\frac{1}{2}\right),
> $$  
> 称 $E_n$ 为欧勒数。

**【注】** 不同文献中欧勒数的定义可能略有差异。有些文献定义 $E_n = 2^n E_n(1/2)$，此时 $E_{2n+1} = 0$，而 $E_{2n}$ 等于本书定义的 $(-1)^n E_n$。

---

## 显明表达式与递推关系

利用生成函数展开，可得欧勒多项式的显明表达式：

> **定理（显明表达式）**  
> $$
> E_n(x) = \sum_{k = 0}^{[n/2]} (-1)^k \frac{E_k}{2^{2k}} \binom{n}{2k} \left(x - \frac{1}{2}\right)^{n - 2k},
> $$  
> 其中 $[n/2]$ 表示不超过 $n/2$ 的最大整数。

由恒等式  
> $$
> 1 = \frac{e^t + e^{-t}}{2} \cdot \frac{2}{e^t + e^{-t}}
> $$  
> 可得欧勒数的递推关系：

> **定理（递推关系）**  
> $$
> E_0 = 1,
> $$  
> $$
> \sum_{l = 0}^{k} (-1)^l \binom{2k}{2l} E_l = 0 \quad (k \geq 1).
> $$

---

## 基本性质

### 均值公式

由生成函数在 $x \to x+1$ 下的变换：

> **性质（均值公式）**  
> $$
> E_n(x + 1) + E_n(x) = 2x^n.
> $$

### 微商

由显明表达式直接求导：

> **性质（微商）**  
> $$
> \frac{d^p}{dx^p} E_n(x) = \frac{n!}{(n-p)!} E_{n-p}(x).
> $$

### 互余宗量关系

由生成函数在 $x \to 1-x$ 下的变换：

> **性质（互余宗量）**  
> $$
> E_n(1 - x) = (-1)^n E_n(x).
> $$

---

## 求和公式

由均值公式可导出交错幂和公式：

> **推论（求和公式）**  
> $$
> \sum_{s = 1}^{m} (-1)^s s^n = \frac{1}{2} \sum_{s = 1}^{m} (-1)^s \big[ E_n(s + 1) + E_n(s) \big].
> $$

---

## 与三角函数的联系

由生成函数可得正割函数的展开式：

> **性质（正割展开）**  
> $$
> \operatorname{sech} z = \sum_{n = 0}^{\infty} (-1)^n \frac{E_n}{(2n)!} z^{2n},
> $$  
> 即  
> $$
> \sec z = \sum_{n = 0}^{\infty} (-1)^n \frac{E_n}{(2n)!} z^{2n} \quad (|z| < \frac{\pi}{2}).
> $$

---

## 前几个欧勒数与欧勒多项式

由上述定义和递推关系可得：

> **性质（前十个欧勒数）**  
> $$
> E_0 = 1,\quad E_1 = 1,\quad E_2 = 5,\quad E_3 = 61,\quad E_4 = 1385,
> $$  
> $$
> E_5 = 50521,\quad E_6 = 2702765,\quad E_7 = 199360981,
> $$  
> $$
> E_8 = 19391512145,\quad E_9 = 2404879675441.
> $$

> **性质（前七个欧勒多项式）**  
> $$
> E_0(x) = 1,
> $$  
> $$
> E_1(x) = x - \frac{1}{2},
> $$  
> $$
> E_2(x) = x(x - 1),
> $$  
> $$
> E_3(x) = \left(x - \frac{1}{2}\right)\left(x^2 - x - \frac{1}{2}\right),
> $$  
> $$
> E_4(x) = x(x - 1)(x^2 - x - 1),
> $$  
> $$
> E_5(x) = \left(x - \frac{1}{2}\right)(x^4 - 2x^3 - x^2 + 2x + 1),
> $$  
> $$
> E_6(x) = x(x - 1)(x^4 - 2x^3 - 2x^2 + 3x + 3).
> $$

---

## 与伯努利多项式的关系

欧勒多项式可以用伯努利多项式表示：

> **性质（与伯努利多项式的关系）**  
> $$
> E_{n-1}(x) = \frac{2^n}{n} \left[ \phi_n\left(\frac{x+1}{2}\right) - \phi_n\left(\frac{x}{2}\right) \right] = \frac{2}{n} \left[ \phi_n(x) - 2^n \phi_n\left(\frac{x}{2}\right) \right],
> $$  
> 其中 $\phi_n(x)$ 为伯努利多项式。

# 欧勒-麦克洛临公式

## 达布公式

> **定理（达布公式）**  
> 设 $f(x)$ 在区间 $a \leqslant x \leqslant a + mh$ 上有 $n+1$ 阶连续微商，则
> $$
> \sum_{s=0}^{m-1} f(a + sh) = \frac{1}{h} \int_a^{a+mh} f(x) dx + \frac{1}{2} \big[ f(a) - f(a+mh) \big] + \sum_{k=1}^{n} \frac{(-1)^{k-1} B_k}{(2k)!} h^{2k-1} \big[ f^{(2k-1)}(a+mh) - f^{(2k-1)}(a) \big] + R_n,
> $$
> 其中 $B_k$ 是伯努利数，余项为
> $$
> R_n = h^{2n+1} \int_0^1 P_{2n}(t) \sum_{s=0}^{m-1} f^{(2n)}(a + h(t+s)) \, dt,
> $$
> 这里
> $$
> P_\lambda(t) = \frac{1}{\lambda!} \phi_\lambda(t) \quad (0 \leqslant t \leqslant 1),
> $$
> 且 $P_\lambda(t)$ 以 1 为周期延拓到整个实轴。

**【注】** 函数 $P_\lambda(t)$ 在 $0 \leqslant t \leqslant 1$ 上等于 $\phi_\lambda(t)/\lambda!$，并以 1 为周期延拓。由伯努利多项式的互余宗量关系可得
> $$
> P_\lambda(1-t) = (-1)^\lambda P_\lambda(t).
> $$

---

## 欧勒-麦克洛临求和公式（第一种形式）

由达布公式直接可得：

> **推论（求和公式）**  
> $$
> \sum_{s=0}^{m-1} f(a + sh) = \frac{1}{h} \int_a^{a+mh} f(x) dx + \frac{1}{2} \big[ f(a) - f(a+mh) \big] + \sum_{k=1}^{n} \frac{(-1)^{k-1} B_k}{(2k)!} h^{2k-1} \big[ f^{(2k-1)}(a+mh) - f^{(2k-1)}(a) \big] + R_n,
> $$
> 其中余项 $R_n$ 满足
> $$
> R_n = h^{2n+2} \int_0^m P_{2n+1}(t) f^{(2n+1)}(a + ht) \, dt.
> $$

---

## 周期函数 $P_\lambda(t)$ 的傅里叶展开

> **定理（傅里叶展开）**  
> 对于 $n \geq 1$，
> $$
> P_{2n}(t) = (-1)^{n+1} \sum_{k=1}^{\infty} \frac{2 \cos 2k\pi t}{(2k\pi)^{2n}},
> $$  
> 对于 $n \geq 0$，$0 < t < 1$，
> $$
> P_{2n+1}(t) = (-1)^{n+1} \sum_{k=1}^{\infty} \frac{2 \sin 2k\pi t}{(2k\pi)^{2n+1}}.
> $$

---

## 绝对值的估计

> **性质（估计）**  
> 对于 $\lambda \geq 1$，有
> $$
> |P_\lambda(t)| \leqslant \frac{4}{(2\pi)^\lambda}.
> $$
> 特别地，对于 $\lambda = 2n$，
> $$
> |P_{2n}(t)| \leqslant |P_{2n}(0)| = \frac{B_n}{(2n)!}.
> $$

**【证】** 由傅里叶展开和级数估计：
> $$
> |P_\lambda(t)| \leqslant \frac{2}{(2\pi)^\lambda} \sum_{k=1}^{\infty} \frac{1}{k^\lambda} \leqslant \frac{4}{(2\pi)^\lambda},
> $$
> 其中用到了
> $$
> \sum_{k=1}^{\infty} \frac{1}{k^\lambda} \leqslant 1 + \int_1^\infty \frac{dx}{x^\lambda} = 1 + \frac{1}{\lambda - 1} \leqslant 2 \quad (\lambda \geq 2).
> $$
> 当 $\lambda = 1$ 时，$|P_1(t)| = |t - 1/2| \leqslant 1/2 < 4/(2\pi)$，故不等式对 $\lambda \geq 1$ 均成立。

---

## 余项的进一步估计

> **定理（余项估计）**  
> 若 $f(x)$ 在 $x > 0$ 时具有固定的正负号，且当 $x \to \infty$ 时 $f(x)$ 及其各阶微商都单调地趋于 0，则欧勒-麦克洛临公式的余项可表示为
> $$
> R_n = \theta \cdot \frac{(-1)^{n+1} B_{n+1}}{(2n+2)!} h^{2n+2} \big[ f^{(2n+1)}(a + mh) - f^{(2n+1)}(a) \big], \quad 0 \leqslant \theta \leqslant 1.
> $$

---

## 欧勒-麦克洛临求和公式（第二种形式）

当 $m \to \infty$ 且 $f(x)$ 及其各阶微商在 $x \to \infty$ 时趋于 0 时，可得：

> **推论（无穷级数求和公式）**  
> $$
> \sum_{s=0}^{\infty} f(a + sh) = \frac{1}{h} \int_a^\infty f(x) dx + \frac{1}{2} f(a) - \sum_{k=1}^{n} \frac{(-1)^{k-1} B_k}{(2k)!} h^{2k-1} f^{(2k-1)}(a) + R_n,
> $$
> 其中
> $$
> R_n = h^{2n+1} \int_0^\infty P_{2n}(t) f^{(2n)}(a + ht) \, dt.
> $$

---

## 应用：欧勒常数的计算

由欧勒-麦克洛临公式可直接导出欧勒常数 $\gamma$ 的快速收敛表达式：

> **性质（欧勒常数）**  
> 欧勒常数定义为
> $$
> \gamma = \lim_{m \to \infty} \left\{ 1 + \frac{1}{2} + \cdots + \frac{1}{m} - \ln m \right\}.
> $$
> 应用欧勒-麦克洛临公式，可得
> $$
> \gamma = 1 + \frac{1}{2} + \cdots + \frac{1}{m} - \ln m - \frac{1}{2m} + \frac{1}{12m^2} - \frac{1}{120m^4} + \frac{1}{252m^6} - 7! \int_m^\infty P_7(t) \frac{dt}{t^8}.
> $$
> 其数值为
> $$
> \gamma = 0.57721566490153286060651\ldots
> $$

# 拉格朗日展开公式

## 零点和极点的围道积分定理

> **定理（零点和极点计数定理）**  
> 设 $\psi(z)$ 在围道 $C$ 内除有限个极点 $b_j$（$j = 1,2,\ldots$）外是解析的，$a_k$（$k = 1,2,\ldots$）是 $\psi(z)$ 在 $C$ 内的零点，在 $C$ 上 $\psi(z) \neq 0$。又设 $\phi(z)$ 是 $C$ 内及 $C$ 上的解析函数，则
> $$
> \frac{1}{2\pi i} \oint_C \phi(z) \frac{\psi'(z)}{\psi(z)} dz = \sum_k n_k \phi(a_k) - \sum_j p_j \phi(b_j),
> $$
> 其中 $n_k$ 和 $p_j$ 分别是零点 $a_k$ 和极点 $b_j$ 的阶数；积分沿 $C$ 的正向（逆时针）一周。

**【证】** 在零点 $a_k$ 附近，$\psi(z) = (z - a_k)^{n_k} \psi_k(z)$，$\psi_k(a_k) \neq 0$，故
> $$
> \frac{\psi'(z)}{\psi(z)} = \frac{n_k}{z - a_k} + \frac{\psi_k'(z)}{\psi_k(z)}.
> $$
> 由残数定理，$\frac{1}{2\pi i}\int_{(a_k)} \phi(z) \frac{\psi'(z)}{\psi(z)} dz = n_k \phi(a_k)$。类似地，在极点 $b_j$ 处贡献为 $-p_j \phi(b_j)$。求和即得。

---

## 零点个数公式

> **推论（零点个数）**  
> 令 $\phi(z) \equiv 1$，得
> $$
> \frac{1}{2\pi i} \oint_C \frac{\psi'(z)}{\psi(z)} dz = N - P,
> $$
> 其中 $N$ 是 $\psi(z)$ 在 $C$ 内的零点总数（按重数计），$P$ 是极点总数（按阶数计）。若 $\psi(z)$ 在 $C$ 内无奇点，则 $P = 0$，有
> $$
> \frac{1}{2\pi i} \oint_C \frac{\psi'(z)}{\psi(z)} dz = N.
> $$

---

## 拉格朗日定理

> **定理（拉格朗日展开公式）**  
> 设 $f(z)$ 和 $\phi(z)$ 在围道 $C$ 上及 $C$ 内是解析的，$a$ 为 $C$ 内一点。如果对于 $C$ 上的点 $\zeta$，参数 $t$ 满足
> $$
> |t \phi(\zeta)| < |\zeta - a|,
> $$
> 则
> - (i) 方程 $z = a + t \phi(z)$ 在 $C$ 内有一根且只有一根；当 $t = 0$ 时此根趋于 $a$；
> - (ii) 函数 $f(z)$ 可依 $t$ 的幂展开为
> $$
> f(z) = f(a) + \sum_{n = 1}^{\infty} \frac{t^n}{n!} \frac{d^{n-1}}{da^{n-1}} \left\{ f'(a) [\phi(a)]^n \right\}.
> $$

**【证】** (i) 令 $\psi(z) = z - a - t\phi(z)$。由零点个数公式，
> $$
> N = \frac{1}{2\pi i} \oint_C \frac{1 - t\phi'(\zeta)}{\zeta - a - t\phi(\zeta)} d\zeta.
> $$
> 将 $\frac{1}{\zeta - a - t\phi(\zeta)}$ 展开为 $\sum_{n=0}^{\infty} \frac{[t\phi(\zeta)]^n}{(\zeta - a)^{n+1}}$，利用科希积分公式，得到 $N = 1$。
>
> (ii) 设 $z$ 为唯一根，由零点和极点定理，
> $$
> f(z) = \frac{1}{2\pi i} \oint_C f(\zeta) \frac{\psi'(\zeta)}{\psi(\zeta)} d\zeta.
> $$
> 代入 $\psi$ 并展开，经整理得
> $$
> f(z) = f(a) + \sum_{n=1}^{\infty} \frac{t^n}{n!} \frac{d^{n-1}}{da^{n-1}} \left\{ f'(a) [\phi(a)]^n \right\}.
> $$

---

## 重要特例

> **推论（生成函数展开）**  
> 取 $\phi(z) = \frac{z^2 - 1}{2}$，方程 $z - x - t\phi(z) = 0$ 的一个根为
> $$
> z = \frac{1 - \sqrt{1 - 2xt + t^2}}{t},
> $$
> 当 $t \to 0$ 时 $z \to x$。令 $f(z) \equiv z$，由拉格朗日展开得
> $$
> \frac{1 - \sqrt{1 - 2xt + t^2}}{t} = x + \sum_{n=1}^{\infty} \frac{t^n}{n!} \frac{d^{n-1}}{dx^{n-1}} \left\{ \left( \frac{x^2 - 1}{2} \right)^n \right\}.
> $$
> 两边对 $x$ 求微商，得
> $$
> \frac{1}{\sqrt{1 - 2xt + t^2}} = \sum_{n=0}^{\infty} \frac{t^n}{n! 2^n} \frac{d^n}{dx^n} (x^2 - 1)^n.
> $$
> 此式给出了勒让德多项式的生成函数。

# 半纯函数的有理分式展开

## 半纯函数的基本概念

> **定义（半纯函数）**  
> 半纯函数是单值函数，它在有限区域内除极点之外没有别的奇点。

**【注】** 半纯函数的典型例子包括：
> - 有理函数 $P_n(z)/Q_m(z)$，其中 $P_n$ 和 $Q_m$ 分别为 $n$ 次和 $m$ 次多项式；
> - $\csc z$、$\cot z$ 等三角函数，它们的极点为 $z = n\pi$（$n = 0,\pm1,\pm2,\ldots$），均为一阶极点。

> **性质（极点的聚点）**  
> 在有限区域中，半纯函数的极点个数必为有限。若半纯函数有无穷多个极点 $a_n$（$n = 1,2,\ldots$），则必有 $\lim_{n\to\infty} a_n = \infty$。否则，若极限为有限值，则在有限区域内将有无穷多个极点，这与极点的孤立性矛盾。

---

## 米塔格-累夫勒定理

> **定理（米塔格-累夫勒有理分式展开）**  
> 设半纯函数 $f(z)$ 的极点为 $a_1,a_2,a_3,\ldots$，满足 $0 < |a_1| \leqslant |a_2| \leqslant |a_3| \leqslant \cdots$。如果存在具有下列性质的围道序列 $\{C_m\}$：
> - (i) 当 $m\to\infty$ 时，$C_m$ 到原点的最近距离 $R_m\to\infty$，但 $l_m/R_m$ 有界，其中 $l_m$ 是 $C_m$ 的周长；
> - (ii) 在 $C_m$ 上，
> $$
> |z^{-p} f(z)| < M,
> $$
> 其中 $p$ 为某最小的非负整数，$M$ 为与 $m$ 无关的正数，
> 
> 则 $f(z)$ 可展开为有理分式的级数
> $$
> f(z) = \sum_{k=0}^{p} f^{(k)}(0) \frac{z^k}{k!} + \sum_{n=1}^{\infty} \left\{ G_n\left(\frac{1}{z - a_n}\right) - \phi_{np}(z) \right\},
> $$
> 其中
> $$
> G_n\left(\frac{1}{z - a_n}\right) = \frac{A_{n,s_n}}{(z - a_n)^{s_n}} + \frac{A_{n,s_n-1}}{(z - a_n)^{s_n-1}} + \cdots + \frac{A_{n,1}}{z - a_n}
> $$
> 是 $f(z)$ 在 $a_n$ 点的主部（洛浪展开的负幂部分），而
> $$
> \phi_{np}(z) = \sum_{k=0}^{p} \left[ \frac{d^k}{d\xi^k} G_n\left(\frac{1}{\xi - a_n}\right) \right]_{\xi=0} \frac{z^k}{k!}
> $$
> 是 $G_n$ 在 $\xi = 0$ 处的泰勒展开的前 $p+1$ 项。

**【注】** 若 $z = 0$ 也是 $f(z)$ 的极点，则上述定理不能直接应用。此时可先考虑函数 $F(z) = f(z) - G_0(1/z)$，其中 $G_0(1/z)$ 是 $f(z)$ 在 $z = 0$ 点的主部，然后对 $F(z)$ 应用该定理。

---

## 一阶极点的特殊情形

> **推论（一阶极点的展开）**  
> 若 $a_1,a_2,\ldots$ 都是 $f(z)$ 的一阶极点（均非 $0$），且在围道序列 $C_m$ 上有 $|f(z)| < M$（即 $p = 0$），$M$ 与 $m$ 无关，则展开公式简化为
> $$
> f(z) = f(0) + \sum_{n=1}^{\infty} b_n \left( \frac{1}{z - a_n} + \frac{1}{a_n} \right),
> $$
> 其中 $b_n$ 是 $f(z)$ 在 $a_n$ 点的残数。

---

## 例：余切函数的有理分式展开

> **推论（$\cot z$ 的展开）**  
> $$
> \cot z = \frac{1}{z} + \sum_{n=-\infty}^{\infty} \left( \frac{1}{z - n\pi} + \frac{1}{n\pi} \right) = \frac{1}{z} + \sum_{n=1}^{\infty} \frac{2z}{z^2 - n^2 \pi^2}.
> $$

**【证】** 先考虑 $F(z) = \cot z - 1/z$，其极点为 $n\pi$（$n = \pm1,\pm2,\ldots$），均为一阶极点，残数为 $1$。取围道 $C_m$ 为以原点为中心、边长为 $(2m+1)\pi$ 的正方形，可证明在 $C_m$ 上 $|F(z)| < M$（$M$ 与 $m$ 无关）。由一阶极点的展开公式得
> $$
> \cot z - \frac{1}{z} = \left( \cot z - \frac{1}{z} \right)_{z\to 0} + \sum_{n=-\infty}^{\infty} \left( \frac{1}{z - n\pi} + \frac{1}{n\pi} \right).
> $$
> 由于当 $z\to 0$ 时 $\cot z - 1/z \to 0$，故得上述展开式。

---

## 由 $\cot z$ 展开导出的求和公式

> **推论（伯努利数与 $\zeta$ 函数的关系）**  
> 令 $z = t/2$，得
> $$
> \frac{t}{2} \cot \frac{t}{2} = 1 + \sum_{n=1}^{\infty} \frac{2t^2}{t^2 - (2n\pi)^2}.
> $$
> 将左端与伯努利数的展开式比较，并将右端各项按 $t$ 的幂级数展开，可得
> $$
> \sum_{n=1}^{\infty} \frac{1}{n^{2k}} = \frac{(2\pi)^{2k} B_k}{2(2k)!}, \quad k = 1,2,\ldots,
> $$
> 其中 $B_k$ 是伯努利数。

# 无穷乘积

## 收敛性定义

> **定义（无穷乘积的收敛性）**  
> 无穷乘积
> $$
> \prod_{n=1}^{\infty} u_n = u_1 \cdot u_2 \cdot u_3 \cdots
> $$
> 称为收敛的，如果存在正整数 $m$ 使得所有 $n > m$ 的 $u_n \neq 0$，且部分积
> $$
> p_n = u_{m+1} \cdot u_{m+2} \cdots u_n \quad (n > m)
> $$
> 在 $n \to \infty$ 时趋于不为零的极限 $U_m$。此时称
> $$
> U = \prod_{n=1}^{\infty} u_n = u_1 \cdot u_2 \cdots u_m \cdot U_m
> $$
> 为无穷乘积之值。该值与 $m$ 的选择无关。

---

## 收敛的必要条件

> **定理（必要条件）**  
> 若无穷乘积 $\prod_{n=1}^{\infty} u_n$ 收敛，则 $\lim_{n\to\infty} u_n = 1$。

**【证】** 当 $n \to \infty$ 时，$u_n = p_n / p_{n-1} \to 1$，因为 $p_n$ 与 $p_{n-1}$ 趋于同一非零极限。

**【注】** 由于上述原因，通常将无穷乘积写为
> $$
> \prod_{n=1}^{\infty} (1 + a_n),
> $$
> 其中 $\lim_{n\to\infty} a_n = 0$ 是收敛的必要条件。

---

## 收敛的充要条件

> **定理（收敛充要条件）**  
> 乘积 $\prod_{n=1}^{\infty} (1 + a_n)$ 收敛的充要条件是：存在 $m$ 使得级数
> $$
> \sum_{n=m+1}^{\infty} \ln(1 + a_n)
> $$
> 收敛，其中的对数取主值：$|\arg(1 + a_n)| < \pi$。若该级数的和为 $L$，则
> $$
> \prod_{n=1}^{\infty} (1 + a_n) = (1 + a_1)(1 + a_2)\cdots(1 + a_m) e^L.
> $$

**【证】**
> - **充分性**：若级数收敛，则部分积 $p_n = \exp\{\sum_{r=m+1}^n \ln(1 + a_r)\}$ 收敛于 $e^L$。
> - **必要性**：若乘积收敛，则 $\sum_{r=m+1}^{\infty} \ln(1 + a_r) = \lim_{n\to\infty} \ln p_n = \ln p$，其中 $\ln p$ 的值由主值分支的连续延拓确定。

---

## 绝对收敛

> **定义（绝对收敛）**  
> 无穷乘积 $\prod_{n=1}^{\infty} (1 + a_n)$ 称为绝对收敛的，如果 $\prod_{n=1}^{\infty} (1 + |a_n|)$ 收敛。

> **定理（绝对收敛蕴含收敛）**  
> 若 $\prod_{n=1}^{\infty} (1 + a_n)$ 绝对收敛，则它必是收敛的。

**【证】** 设 $q_n = \prod_{r=m+1}^n (1 + |a_r|) \to q \neq 0$。对于任意 $k > 0$，当 $n$ 足够大时，
> $$
> |(1 + a_{n+1})\cdots(1 + a_{n+k}) - 1| \leqslant (1 + |a_{n+1}|)\cdots(1 + |a_{n+k}|) - 1 = \frac{q_{n+k}}{q_n} - 1 < \epsilon.
> $$
> 由此可证部分积满足柯西判据，且极限不为零。

> **定理（绝对收敛的充要条件）**  
> 乘积 $\prod_{n=1}^{\infty} (1 + a_n)$ 绝对收敛的充要条件是级数 $\sum_{n=1}^{\infty} a_n$ 绝对收敛。

**【证】** 令 $P_n = \prod_{r=m+1}^n (1 + |a_r|)$，$S_n = \sum_{r=m+1}^n |a_r|$。由于
> $$
> 1 + |a_r| \leqslant e^{|a_r|},
> $$
> 可得 $S_n \leqslant \ln P_n \leqslant S_n$，故 $P_n$ 与 $S_n$ 的收敛性等价。

> **定理（对数级数的绝对收敛性）**  
> 乘积 $\prod_{n=1}^{\infty} (1 + a_n)$ 绝对收敛的充要条件是级数 $\sum_{n=1}^{\infty} \ln(1 + a_n)$ 绝对收敛。

**【证】** 当 $|a_n|$ 足够小（例如 $|a_n| < 1/2$）时，有
> $$
> \frac{1}{2} < \left| \frac{\ln(1 + a_n)}{a_n} \right| < \frac{3}{2},
> $$
> 故 $\sum |\ln(1 + a_n)|$ 与 $\sum |a_n|$ 的收敛性等价。

---

## 一致收敛

> **定义（一致收敛）**  
> 无穷乘积 $\prod_{n=1}^{\infty} \{1 + u_n(z)\}$ 称为在区域 $D$ 中一致收敛，如果给定 $\epsilon > 0$，存在与 $z$ 无关的 $m$，使得对于任意的 $p > 0$，
> $$
> \left| \prod_{n=1}^{m+p} \{1 + u_n(z)\} - \prod_{n=1}^{m} \{1 + u_n(z)\} \right| < \epsilon.
> $$

# 函数的无穷乘积展开

## 整函数的无穷乘积展开

> **定理（整函数无穷乘积展开）**  
> 设整函数 $f(z)$ 只有不为零的一阶零点 $a_1, a_2, \ldots$，满足 $\lim_{n\to\infty} a_n = \infty$，且存在围道序列 $\{C_m\}$，在其上
> $$
> \left| \frac{f'(z)}{f(z)} \right| < M,
> $$
> 其中 $M$ 为与 $m$ 无关的正数，则 $f(z)$ 可展开为无穷乘积
> $$
> f(z) = f(0) e^{\frac{f'(0)}{f(0)} z} \prod_{n=1}^{\infty} \left\{ \left( 1 - \frac{z}{a_n} \right) e^{z/a_n} \right\}.
> $$

> **定义（质因子）**  
> 上式中乘积的每一个因子 $\left( 1 - \frac{z}{a_n} \right) e^{z/a_n}$ 只在 $z = a_n$ 处为零，称为整函数 $f(z)$ 的**质因子**。

**【证】** 令 $F(z) = f'(z)/f(z)$。在零点 $a_n$ 处，$f(z) = (z - a_n) f'(a_n) + \cdots$，故 $F(z)$ 在 $a_n$ 处有一阶极点，残数为 $1$。由米塔格-累夫勒定理（§1.5），$F(z)$ 可展开为
> $$
> \frac{f'(z)}{f(z)} = \frac{f'(0)}{f(0)} + \sum_{n=1}^{\infty} \left( \frac{1}{z - a_n} + \frac{1}{a_n} \right).
> $$
> 从 $0$ 到 $z$ 逐项积分，即得所求展开式。

---

## 整函数的多个零点和重零点情形

> **推论（多阶零点）**  
> 若 $a_n$ 是 $f(z)$ 的 $m_n$ 阶零点，则展开式中的质因子应出现 $m_n$ 次：
> $$
> f(z) = f(0) e^{\frac{f'(0)}{f(0)} z} \prod_{n=1}^{\infty} \left\{ \left( 1 - \frac{z}{a_n} \right) e^{z/a_n} \right\}^{m_n}.
> $$

**【注】** 此时 $F(z) = f'(z)/f(z)$ 在 $a_n$ 处的残数为 $m_n$。

---

## 半纯函数的无穷乘积表示

> **定理（半纯函数的整函数商表示）**  
> 任意半纯函数 $f(z)$ 总可以用两个整函数的商表达：
> $$
> f(z) = \frac{G_1(z)}{G(z)},
> $$
> 其中 $G(z)$ 的零点就是 $f(z)$ 的极点。

**【证】** 取整函数 $G(z)$，使其零点恰为 $f(z)$ 的极点（按阶数计）。则 $f(z)G(z)$ 在有限区域内无奇点，因此是一整函数，记为 $G_1(z)$。

---

## 普遍的外氏质因子定理

> **定理（外氏质因子定理）**  
> 设 $f(z)$ 在有限区域内无本性奇点，其零点（或极点）为 $a_1, a_2, \ldots$，满足 $0 < |a_1| \leqslant |a_2| \leqslant \cdots$，则 $f(z)$ 可展开为无穷乘积
> $$
> f(z) = f(0) e^{G(z)} \prod_{n=1}^{\infty} \left\{ \left( 1 - \frac{z}{a_n} \right) e^{g_n(z)} \right\}^{m_n},
> $$
> 其中：
> - $G(z)$ 是一个整函数，满足 $G(0) = 0$；
> - $g_n(z)$ 是适当地选取的多项式，其作用是使乘积在任何有限区域内（除去极点处）绝对且一致收敛；
> - $m_n$ 代表零点（或极点）的阶数，可正可负：若 $a_n$ 是零点则 $m_n > 0$，若 $a_n$ 是极点则 $m_n < 0$。

**【证】** 选取
> $$
> g_n(z) = \sum_{s=1}^{k_n-1} \frac{1}{s} \left( \frac{z}{a_n} \right)^s,
> $$
> 其中 $k_n$ 为足够大的正整数。则在 $|z| < K$ 内，
> $$
> \left| \ln \left\{ \left( 1 - \frac{z}{a_n} \right) e^{g_n(z)} \right\} \right| \leqslant 2 |m_n| \left| \frac{K}{a_n} \right|^{k_n}.
> $$
> 选择 $k_n$ 使右端小于 $2^{-n}$ 的相应项，则乘积绝对且一致收敛。
>
> 令该收敛乘积为 $F(z)$，则 $f(z)/F(z)$ 是一个没有零点的整函数，故可写为 $C e^{G_2(z)}$。调整常数使 $G(0) = 0$，即得展开式。

---

## 条件加强时的特殊形式

> **推论（$F(z) = f'(z)/f(z)$ 满足有界条件时）**  
> 若 $F(z) = f'(z)/f(z)$ 满足 §1.5 中的条件 (1)，即存在围道序列使 $|z^{-p}F(z)| < M$，则
> $$
> G(z) = \sum_{k=0}^{p} F^{(k)}(0) \frac{z^{k+1}}{(k+1)!},
> $$
> 且
> $$
> g_n(z) = \sum_{k=0}^{p} \left[ \frac{d^k}{d\xi^k} G_n\left( \frac{1}{\xi - a_n} \right) \right]_{\xi=0} \frac{z^{k+1}}{(k+1)!},
> $$
> 其中 $G_n(1/(z - a_n))$ 是 $F(z)$ 在 $a_n$ 点的主部。

# 渐近展开

## 基本概念

> **定义（渐近展开）**  
> 设级数
> $$
> A_0 + A_1 z^{-1} + A_2 z^{-2} + \cdots
> $$
> 具有如下性质：对于任意固定的非负整数 $n$，当 $z$ 在一定的辐角范围 $|\arg z| < \Delta$ 内且 $|z| \to \infty$ 时，
> $$
> \lim_{z \to \infty} z^n \left\{ f(z) - \sum_{k=0}^{n} A_k z^{-k} \right\} = 0,
> $$
> 即
> $$
> f(z) = \sum_{k=0}^{n} A_k z^{-k} + o(z^{-n}),
> $$
> 则称该级数为 $f(z)$ 的**渐近展开**（或渐近级数），记作
> $$
> f(z) \sim \sum_{k=0}^{\infty} A_k z^{-k}, \quad |z| \to \infty, \quad |\arg z| < \Delta.
> $$

**【注1】** 渐近级数通常并不要求收敛。在实际应用中，是用级数的部分和 $S_n(z) = \sum_{k=0}^n A_k z^{-k}$ 作为 $f(z)$ 的近似，而不是要求 $n \to \infty$ 时级数收敛到 $f(z)$。事实上，渐近级数往往是发散的。

**【注2】** 渐近展开中的 $z$ 通常取复变数，且与辐角范围有关。在不同的辐角范围内，同一函数的渐近表示可能不同（参见第六章的 Stokes 现象）。

---

## 渐近级数的基本性质

### 唯一性

> **性质（唯一性）**  
> 在给定的辐角范围内，一个函数至多只有一个渐近展开。也就是说，若 $f(z)$ 的渐近展开存在，则它是唯一的。

**【证】** 若 $f(z)$ 有两个渐近展开 $\sum A_k z^{-k}$ 和 $\sum B_k z^{-k}$，则对于固定的 $n$，
> $$
> \lim_{|z| \to \infty} z^n \sum_{k=0}^{n} (A_k - B_k) z^{-k} = 0.
> $$
> 由此依次可得 $A_0 = B_0$，$A_1 = B_1$，……，$A_n = B_n$。由于 $n$ 任意，故两个展开相同。

**【注】** 唯一性并不意味着不同的函数不能有相同的渐近展开。事实上，同一发散的级数可以是两个不同函数的渐近展开，例如
> $$
> f(z) \sim \sum A_k z^{-k}, \qquad f(z) + e^{-z} \sim \sum A_k z^{-k}
> $$
> 在 $|\arg z| < \pi/2$ 时具有相同的渐近展开。

---

### 线性组合

> **性质（线性组合）**  
> 若
> $$
> f(z) \sim \sum_{k=0}^{\infty} A_k z^{-k}, \qquad g(z) \sim \sum_{k=0}^{\infty} B_k z^{-k},
> $$
> 则对于任意常数 $\alpha, \beta$，
> $$
> \alpha f(z) + \beta g(z) \sim \sum_{k=0}^{\infty} (\alpha A_k + \beta B_k) z^{-k}.
> $$

---

### 相乘

> **性质（乘积）**  
> 若 $f(z) \sim \sum A_k z^{-k}$，$g(z) \sim \sum B_k z^{-k}$，则
> $$
> f(z) g(z) \sim \sum_{m=0}^{\infty} C_m z^{-m},
> $$
> 其中
> $$
> C_m = \sum_{k=0}^{m} A_k B_{m-k}.
> $$

**【证】** 设
> $$
> f(z) = \sum_{k=0}^{n} A_k z^{-k} + \epsilon z^{-n}, \qquad g(z) = \sum_{k=0}^{n} B_k z^{-k} + \eta z^{-n},
> $$
> 其中 $\epsilon, \eta \to 0$（$|z| \to \infty$）。则
> $$
> z^n \left\{ f(z)g(z) - \sum_{m=0}^{n} C_m z^{-m} \right\} = A_0 \eta + B_0 \epsilon + O(z^{-1}) \to 0.
> $$

---

### 逐项积分

> **性质（逐项积分）**  
> 设 $z$ 为实变数或辐角固定的复变数。若
> $$
> f(z) \sim \sum_{k=2}^{\infty} A_k z^{-k},
> $$
> 则
> $$
> \int_z^{\infty} f(z) \, dz \sim \sum_{k=2}^{\infty} \frac{A_k}{k-1} z^{-k+1}.
> $$

**【注】** 该性质要求渐近展开中常数项和 $z^{-1}$ 项的系数均为 $0$，以保证积分在无穷远处收敛。

---

### 逐项微商的限制

> **性质（微商的限制）**  
> 一般说来，渐近展开不能逐项求微商。例如，函数 $e^{-x} \sin(e^x) \sim 0 + 0/x + 0/x^2 + \cdots$，但其微商在 $x \to \infty$ 时振荡，根本没有渐近展开。
>
> 但是，如果 $f(x)$ 有微商，且 $f(x)$ 和 $f'(x)$ 都有幂级数形式的渐近展开，则 $f(x)$ 的渐近展开可以逐项求微商。

---

## 渐近级数的误差特性

> **性质（误差估计）**  
> 按定义，用部分和 $S_n(z)$ 近似 $f(z)$ 时，误差为 $o(z^{-n})$。因此，对于固定的 $n$，$|z|$ 越大，近似程度越好。
>
> 然而，若渐近级数发散，则对于固定的 $z$，增加项数 $n$ 并不能无限制地改善近似；存在一个最优项数，超过该值后误差反而增大。这是渐近展开与收敛级数展开的重要区别。

---

## 例：函数的渐近展开

> **推论（一个典型例子）**  
> 对于 $x > 0$，函数
> $$
> f(x) = \int_x^{\infty} \frac{e^{x-t}}{t} \, dt
> $$
> 在 $x \to \infty$ 时的渐近展开为
> $$
> f(x) \sim \frac{1}{x} - \frac{1}{x^2} + \frac{2!}{x^3} - \frac{3!}{x^4} + \cdots + (-1)^{n-1} \frac{(n-1)!}{x^n} + \cdots.
> $$

**【误差特性】** 用前 $n$ 项作为近似时，误差绝对值小于 $n!/x^{n+1}$。对于固定的 $n$，误差随 $x \to \infty$ 趋于 $0$；但对于固定的 $x$，当 $n$ 超过约 $x$ 时，误差反而增大。这是发散的渐近级数的典型特征。


# 拉普拉斯积分的渐近展开

## 拉普拉斯积分

> **定义（拉普拉斯积分）**  
> 形如
> $$
> f(z) = \int_{0}^{\infty} e^{-zt} \phi(t) \, dt
> $$
> 的积分称为**拉普拉斯积分**。函数 $f(z)$ 称为 $\phi(t)$ 的拉普拉斯变换。

---

## 瓦特孙引理

> **定理（瓦特孙引理）**  
> 设 $\phi(t)$ 在扇形区域 $|\arg t| < \theta$ 中为单值解析函数。当 $t \to \infty$ 时，$\phi(t) = O(e^{bt})$，其中 $b$ 为实数；当 $t \to 0$ 时，
> $$
> t \phi(t) \sim \sum_{n=1}^{\infty} a_n t^{n/r} \quad (r > 0),
> $$
> 即
> $$
> \phi(t) \sim \sum_{n=1}^{\infty} a_n t^{n/r - 1} \quad (r > 0).
> $$
> 则拉普拉斯积分 $f(z)$ 在 $|z| \to \infty$，$|\arg z| \le \pi/2 - \delta$（$\delta > 0$）时具有渐近展开
> $$
> f(z) = \int_{0}^{\infty} e^{-zt} \phi(t) \, dt \sim \sum_{n=1}^{\infty} a_n \Gamma\left(\frac{n}{r}\right) z^{-n/r}.
> $$

**【证】** 由 $\phi(t)$ 的渐近展开，对于任意固定的正整数 $N$，存在 $K > 0$，使得
> $$
> \left| \phi(t) - \sum_{n=1}^{N-1} a_n t^{n/r - 1} \right| < K t^{N/r - 1} e^{bt}.
> $$
> 于是
> $$
> f(z) = \sum_{n=1}^{N-1} a_n \int_{0}^{\infty} e^{-zt} t^{n/r - 1} \, dt + R_N,
> $$
> 其中
> $$
> \int_{0}^{\infty} e^{-zt} t^{n/r - 1} \, dt = \Gamma\left(\frac{n}{r}\right) z^{-n/r}.
> $$
> 余项满足
> $$
> |R_N| < K \int_{0}^{\infty} e^{-(x - b)t} t^{N/r - 1} \, dt = K \Gamma\left(\frac{N}{r}\right) (x - b)^{-N/r},
> $$
> 其中 $x = \operatorname{Re}(z)$。只要 $x > b$，即 $|z| > b \csc \delta$，就有 $R_N = O(|z|^{-N/r})$。因此得到渐近展开。

---

## 瓦特孙引理的推广（围道积分情形）

> **定理（推广的瓦特孙引理）**  
> 考虑围道积分
> $$
> f(z) = \int_{\infty}^{(0+)} e^{-zt} \phi(t) \, dt, \quad 0 < \arg t < 2\pi,
> $$
> 其中积分围道如图2所示（从正实轴上方无穷远处出发，绕原点正向一周，回到正实轴下方无穷远处）。当 $t \to \infty$ 时，$\phi(t) = O(e^{bt})$，$b$ 为实数；当 $t \to 0$ 时，
> $$
> \left| t \phi(t) - \sum_{n=1}^{N} a_n t^{\lambda_n} \right| = o(|t|^{\lambda_N}),
> $$
> 其中 $0 < \lambda_1 < \lambda_2 < \cdots$。则在 $|z| \to \infty$，$|\arg z| \le \pi/2 - \delta$（$\delta > 0$）时，
> $$
> f(z) = \int_{\infty}^{(0+)} e^{-zt} \phi(t) \, dt \sim 2i \sum_{n=1}^{\infty} a_n \Gamma(\lambda_n) \sin(\lambda_n \pi) \, e^{i\lambda_n \pi} z^{-\lambda_n}.
> $$

**【证】** 该证明与瓦特孙引理类似，但需利用 $\Gamma$ 函数的围道积分表示（第三章，§3.7）：
> $$
> \Gamma(s) = -\frac{1}{2i \sin \pi s} \int_{\infty}^{(0+)} e^{-t} (-t)^{s-1} \, dt.
> $$
> 由该表示可算出围道积分的渐近展开系数。

---

## 例：厄密方程的积分解的渐近展开

> **推论（厄密方程积分解的渐近展开）**  
> 积分
> $$
> f(x) = \int_{\infty}^{(0+)} e^{-xt - \beta t^2} (-t)^{-\mu} \, dt \quad (|\arg(-t)| < \pi)
> $$
> 在 $|x| \to \infty$，$|\arg x| \le \pi/2 - \delta$（$\delta > 0$）时的渐近展开为
> $$
> f(x) \sim -2i x^{\mu-1} \sin(\mu\pi) \sum_{n=0}^{\infty} \frac{(-\beta)^n}{n!} \Gamma(2n - \mu + 1) x^{-2n}.
> $$

**【证】** 将 $\phi(t) = e^{-\beta t^2} (-t)^{-\mu}$ 在 $t = 0$ 附近展开为
> $$
> \phi(t) = \sum_{n=0}^{\infty} \frac{(-\beta)^n}{n!} t^{2n-\mu}.
> $$
> 代入推广的瓦特孙引理，$\lambda_n = 2n - \mu + 1$，$a_n = (-\beta)^n/n!$，可得上述渐近展开。

---

## 瓦特孙引理的条件与适用范围

> **性质（条件总结）**  
> 瓦特孙引理及其推广要求：
> - $\phi(t)$ 在 $t = 0$ 附近具有形如 $\sum a_n t^{\lambda_n - 1}$ 的渐近展开（幂指数不必是整数）；
> - $\phi(t)$ 在 $t \to \infty$ 时至多指数增长（$O(e^{bt})$）；
> - $z$ 的辐角限制在 $|\arg z| \le \pi/2 - \delta$（即右半平面内，且不靠近虚轴），以保证积分收敛且渐近展开有效；
> - 对于围道积分情形，$t$ 的辐角范围需与围道的分支规定一致。

> **性质（应用范围）**  
> 瓦特孙引理是求拉普拉斯型积分的渐近展开的基本工具。它在常微分方程的积分解法（§2.13）、特殊函数（如 $\Gamma$ 函数、贝塞耳函数）的渐近展开中具有广泛应用。

# 用正交函数组展开

## 正交归一函数组

> **定义（正交归一函数组）**  
> 设有一组连续函数 $\{\phi_n(x)\}$（$n = 1,2,\ldots$），定义在区间 $a \leqslant x \leqslant b$ 上。若它们满足
> $$
> (\phi_m, \phi_n) = \int_a^b \overline{\phi_m}(x) \phi_n(x) \rho(x) \, dx = \delta_{mn}
> $$
> （其中 $\delta_{mn} = 0$（$m \neq n$），$\delta_{mn} = 1$（$m = n$）），则称 $\{\phi_n(x)\}$ 为**正交归一函数组**，$\rho(x) > 0$ 称为**权函数**。

> **定义（内积）**  
> 表达式
> $$
> (\phi_m, \phi_n) = \int_a^b \overline{\phi_m}(x) \phi_n(x) \rho(x) \, dx
> $$
> 称为 $\phi_m$ 与 $\phi_n$ 的**内积**。若 $(\phi_m, \phi_n) = 0$，则称这两个函数**互相正交**。

**【例】** 函数组 $\{e^{inx}/\sqrt{2\pi}\}$（$n = 0,\pm1,\pm2,\ldots$）在区间 $[0,2\pi]$ 上构成正交归一函数组，权函数 $\rho(x) = 1$，因为
> $$
> \frac{1}{2\pi} \int_0^{2\pi} e^{-imx} e^{inx} \, dx = \delta_{mn}.
> $$

---

## 最佳逼近与广义傅里叶系数

> **定理（最佳逼近）**  
> 设 $f(x)$ 为区间 $[a,b]$ 上的连续函数。欲用正交归一函数组的线性组合
> $$
> f_k(x) = \sum_{n=1}^{k} c_n \phi_n(x)
> $$
> 作为 $f(x)$ 的近似，定义**平均平方误差**为
> $$
> (d_k, d_k) = \int_a^b |f(x) - f_k(x)|^2 \rho(x) \, dx,
> $$
> 其中 $d_k(x) = f(x) - f_k(x)$。则使平均平方误差最小的系数为
> $$
> c_n = (\phi_n, f).
> $$

**【证】** 计算平均平方误差：
> $$
> (d_k, d_k) = (f - f_k, f - f_k) = (f, f) + (f_k, f_k) - (f, f_k) - (f_k, f).
> $$
> 利用正交归一性，
> $$
> (f_k, f_k) = \sum_{n=1}^{k} |c_n|^2,
> $$
> $$
> (f, f_k) = \sum_{n=1}^{k} (f, \phi_n) c_n, \qquad (f_k, f) = \sum_{n=1}^{k} (\phi_n, f) \overline{c_n}.
> $$
> 因此
> $$
> (d_k, d_k) = (f, f) - \sum_{n=1}^{k} |(\phi_n, f)|^2 + \sum_{n=1}^{k} |c_n - (\phi_n, f)|^2.
> $$
> 右端最后一项恒为非负，且当且仅当 $c_n = (\phi_n, f)$ 时取最小值 $0$。

---

## 广义傅里叶系数与贝塞耳不等式

> **定义（广义傅里叶系数）**  
> 由最佳逼近定理确定的系数
> $$
> c_n = (\phi_n, f) = \int_a^b \overline{\phi_n}(x) f(x) \rho(x) \, dx
> $$
> 称为 $f(x)$ 关于函数组 $\{\phi_n(x)\}$ 的**广义傅里叶系数**。

> **定理（贝塞耳不等式）**  
> 对于任意连续函数 $f(x)$ 和正交归一函数组 $\{\phi_n(x)\}$，有
> $$
> \sum_{n=1}^{k} |c_n|^2 \leqslant (f, f) \quad (k \text{ 任意}),
> $$
> 其中 $c_n = (\phi_n, f)$。因此级数 $\sum_{n=1}^{\infty} |c_n|^2$ 收敛。

**【证】** 由最佳逼近的误差公式，
> $$
> 0 \leqslant (d_k, d_k) = (f, f) - \sum_{n=1}^{k} |c_n|^2,
> $$
> 故得不等式。

---

## 平均收敛与帕色伐等式

> **定义（平均收敛）**  
> 称级数 $\sum_{n=1}^{\infty} c_n \phi_n(x)$ **平均收敛**于 $f(x)$，如果
> $$
> \lim_{k \to \infty} \int_a^b \left| f(x) - \sum_{n=1}^{k} c_n \phi_n(x) \right|^2 \rho(x) \, dx = 0,
> $$
> 其中 $c_n = (\phi_n, f)$。

> **定理（帕色伐等式）**  
> 若 $\sum c_n \phi_n(x)$ 平均收敛于 $f(x)$，则
> $$
> \sum_{n=1}^{\infty} |c_n|^2 = (f, f),
> $$
> 其中 $c_n = (\phi_n, f)$。该等式称为**帕色伐等式**或**完备关系**。

**【注】** 若级数 $\sum c_n \phi_n(x)$ 在区间 $[a,b]$ 上一致收敛，则可逐项求积分，得到逐点收敛结果
> $$
> f(x) = \sum_{n=1}^{\infty} c_n \phi_n(x).
> $$

---

## 完备性与封闭性

> **定义（完备函数组）**  
> 若对于任意连续函数 $f(x)$，帕色伐等式
> $$
> \sum_{n=1}^{\infty} |(\phi_n, f)|^2 = (f, f)
> $$
> 都成立，则称 $\{\phi_n(x)\}$ 为连续函数空间中的**完备函数组**。

> **定义（封闭函数组）**  
> 函数组 $\{\phi_n(x)\}$ 称为**封闭的**，如果不存在与组中所有函数都正交的非零连续函数 $f(x)$。即：若 $(\phi_n, f) = 0$ 对所有 $n$ 成立，则 $f(x) \equiv 0$。

> **定理（完备性与封闭性的关系）**  
> 完备函数组必是封闭的。

**【证】** 若存在连续函数 $f(x)$ 与所有 $\phi_n$ 正交，则其所有广义傅里叶系数均为 $0$。由帕色伐等式得 $(f, f) = 0$，即 $f(x) \equiv 0$。故完备性蕴含封闭性。

---

## 正交归一化手续（Gram-Schmidt 过程）

> **定理（正交归一化）**  
> 设 $\psi_n(x)$（$n = 1,2,\ldots$）是区间 $[a,b]$ 上的一组线性无关的连续函数。可通过如下递推步骤构造一组正交归一函数组 $\{\phi_n(x)\}$：

> 第一步：计算 $\psi_1$ 的范数 $\|\psi_1\| = (\psi_1, \psi_1)^{1/2}$，令
> $$
> \phi_1(x) = \frac{\psi_1(x)}{\|\psi_1\|}.
> $$

> 第二步：取 $\phi_2(x) = c_1 \phi_1(x) + c_2 \psi_2(x)$，要求 $(\phi_1, \phi_2) = 0$ 且 $(\phi_2, \phi_2) = 1$。由此解得
> $$
> |c_2|^2 = \frac{1}{\|\psi_2\|^2 - |(\phi_1, \psi_2)|^2}, \qquad c_1 = -c_2 (\phi_1, \psi_2).
> $$

> 第三步：取 $\phi_3(x) = c_1 \phi_1(x) + c_2 \phi_2(x) + c_3 \psi_3(x)$，要求 $(\phi_1, \phi_3) = (\phi_2, \phi_3) = 0$ 且 $(\phi_3, \phi_3) = 1$。

> 如此继续，即得正交归一函数组 $\{\phi_n(x)\}$（$n = 1,2,\ldots$）。

---

## 多变数完备函数组的构造

> **定理（多变数完备函数组的构造）**  
> 设 $\{\phi_n(s)\}$（$n = 1,2,\ldots$）是区间 $a \leqslant s \leqslant b$ 上的完备正交归一函数组（权为 $1$）。又设对于每个 $n$，$\{\psi_{mn}(t)\}$（$m = 1,2,\ldots$）是区间 $c \leqslant t \leqslant d$ 上的完备正交归一函数组（权为 $1$）。则函数
> $$
> \omega_{mn}(s,t) = \phi_n(s) \psi_{mn}(t) \quad (m,n = 1,2,\ldots)
> $$
> 在矩形区域 $a \leqslant s \leqslant b$，$c \leqslant t \leqslant d$ 上构成完备正交归一函数组（权为 $1$）。

> 对于该区域内任意连续函数 $f(s,t)$，有完备性关系
> $$
> \iint |f(s,t)|^2 \, ds \, dt = \sum_{m,n=1}^{\infty} \left| \iint \overline{\omega_{mn}}(s,t) f(s,t) \, ds \, dt \right|^2.
> $$

**【证】** 由 $\{\phi_n\}$ 的完备性，
> $$
> \int_a^b |f(s,t)|^2 \, ds = \sum_{n=1}^{\infty} |g_n(t)|^2,
> $$
> 其中
> $$
> g_n(t) = \int_a^b \overline{\phi_n}(s) f(s,t) \, ds.
> $$
> 右端级数为非负连续函数级数，由第尼定理一致收敛，可逐项求积分：
> $$
> \iint |f|^2 \, ds \, dt = \sum_{n=1}^{\infty} \int_c^d |g_n(t)|^2 \, dt.
> $$
> 再由 $\{\psi_{mn}\}$ 的完备性，
> $$
> \int_c^d |g_n(t)|^2 \, dt = \sum_{m=1}^{\infty} \left| \int_c^d \overline{\psi_{mn}}(t) g_n(t) \, dt \right|^2.
> $$
> 代入即得所证关系。

