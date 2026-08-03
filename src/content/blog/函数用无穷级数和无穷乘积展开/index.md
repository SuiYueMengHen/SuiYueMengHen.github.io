---
title: 函数用无穷级数和无穷乘积展开
description: 请用一到两句话概括文章内容，建议 30—80 字。
publishDate: '2026-08-03'
category: 未分类
tags:
- 待整理
featured: false
draft: false
autoNumbering: false
showContents: true
showSideToc: true
collection: 特殊函数概论
collectionOrder: 1
---

# 1.1 伯努利 (Bernoulli) 多项式与伯努利数

## 定义

> **定义 1.1（伯努利多项式的生成函数）**  
> 伯努利多项式 $\phi_n(x)$（$n=0,1,2,\dots$）由下列生成函数展开式给出：
> $$
> \frac{t e^{x t}}{e^{t} - 1} = \sum_{n=0}^{\infty} \frac{t^n}{n!} \phi_n(x), \qquad |t| < 2\pi.
> $$
> 级数在 $|t|<2\pi$ 内收敛，因为左端离 $t=0$ 最近的奇点为 $t=\pm 2\pi i$。

> **定义 1.2（伯努利数）**  
> 令 $\phi_n = \phi_n(0)$，则伯努利数 $B_k$ 定义为：
> $$
> \phi_0 = 1,\qquad \phi_1 = -\frac12,\qquad 
> \phi_{2k}=(-1)^{k-1}B_k,\qquad \phi_{2k+1}=0 \quad (k=1,2,\dots).
> $$
> 由此，伯努利数 $B_1,B_2,\dots$ 由下式给出：
> $$
> \frac{t}{e^t-1} = \sum_{n=0}^{\infty} \frac{t^n}{n!}\phi_n
> = 1 - \frac{t}{2} + \sum_{k=1}^{\infty} (-1)^{k-1} B_k \frac{t^{2k}}{(2k)!}.
> $$

---

## 基本性质与定理

### 1. 显明表达式与递推关系

> **定理 1.1（显明表达式）**  
> $$
> \phi_n(x) = \sum_{k=0}^{n} \binom{n}{k} \phi_k x^{n-k}, \qquad n=0,1,2,\dots
> $$
> 常用符号形式写为 $\phi_n(x)=(\phi+x)^n$，其中展开后 $\phi^k$ 替换为 $\phi_k$。

> **定理 1.2（伯努利数的递推关系）**  
> $$
> \phi_0 = 1,\qquad \sum_{k=0}^{n-1} \frac{\phi_k}{k!(n-k)!}=0 \quad (n\ge 2),
> $$
> 或符号形式：
> $$
> (\phi+1)^n - \phi_n = 0 \quad (n\ge 2).
> $$

**前十个伯努利数：**
$$
B_1=\frac16,\; B_2=\frac1{30},\; B_3=\frac1{42},\; B_4=\frac1{30},\; B_5=\frac5{66},\;
B_6=\frac{691}{2730},\; B_7=\frac76,\; B_8=\frac{3617}{510},\; B_9=\frac{43867}{798},\; B_{10}=\frac{174611}{330}.
$$

**前七个伯努利多项式：**
$$
\begin{aligned}
\phi_0(x)&=1,\\
\phi_1(x)&=x-\frac12,\\
\phi_2(x)&=x^2-x+\frac16,\\
\phi_3(x)&=x(x-1)(x-\tfrac12)=x^3-\frac32x^2+\frac12x,\\
\phi_4(x)&=x^4-2x^3+x^2-\frac1{30},\\
\phi_5(x)&=x^5-\frac52x^4+\frac53x^3-\frac16x,\\
\phi_6(x)&=x^6-3x^5+\frac52x^4-\frac12x^2+\frac1{42}.
\end{aligned}
$$

---

### 2. 微商与积分

> **定理 1.3（微商公式）**  
> $$
> \frac{d}{dx}\phi_n(x)=n\,\phi_{n-1}(x),\qquad 
> \frac{d^p}{dx^p}\phi_n(x)=\frac{n!}{(n-p)!}\phi_{n-p}(x).
> $$

> **推论（积分公式）**  
> $$
> \int_a^x \phi_n(y)\,dy = \frac{1}{n+1}\big[\phi_{n+1}(x)-\phi_{n+1}(a)\big].
> $$

---

### 3. 差分关系

> **定理 1.4（差分关系）**  
> $$
> \begin{aligned}
> \phi_0(x+1)&=\phi_0(x),\\
> \phi_1(x+1)&=\phi_1(x)+1,\\
> \phi_n(x+1)&=\phi_n(x)+n x^{n-1}\quad (n\ge 2).
> \end{aligned}
> $$

---

### 4. 互余宗量关系

> **定理 1.5（对称性）**  
> $$
> \phi_n(1-x)=(-1)^n \phi_n(x).
> $$

---

### 5. 加法公式

> **定理 1.6（加法公式）**  
> $$
> \phi_n(x+y)=\sum_{k=0}^{n} \binom{n}{k} \phi_k(y)\, x^{n-k}.
> $$

---

### 6. 求和公式

> **定理 1.7（幂和公式）**  
> 对任意正整数 $m$ 及 $n\ge 1$，
> $$
> \sum_{s=1}^{m} s^n = \frac{1}{n+1}\big[\phi_{n+1}(m+1)-\phi_{n+1}\big],\quad \phi_{n+1}=\phi_{n+1}(0).
> $$

---

### 7. 三角函数的展开式

由生成函数及伯努利数的定义，可导出下列展开式（均在相应的收敛半径内）：

> **定理 1.8（余切、正切、余割展开）**  
> $$
> \frac{t}{2}\cot\frac{t}{2} = 1 - \sum_{n=1}^{\infty} \frac{B_n}{(2n)!} t^{2n}, \qquad |t|<2\pi,
> $$
> $$
> \frac{t}{2}\tan\frac{t}{2} = \sum_{n=1}^{\infty} \frac{(2^{2n}-1)B_n}{(2n)!} t^{2n}, \qquad |t|<\pi,
> $$
> $$
> t\csc t = 1 + \sum_{n=1}^{\infty} \frac{2(2^{2n-1}-1)B_n}{(2n)!} t^{2n}, \qquad |t|<\pi.
> $$
