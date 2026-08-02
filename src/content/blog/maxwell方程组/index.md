---
title: Maxwell方程组
description: 请用一到两句话概括文章内容，建议 30—80 字。
publishDate: '2026-07-30'
category: 未分类
tags:
- 待整理
featured: false
draft: false
---

**真空中的麦克斯韦方程组**

微分形式：
$$
\begin{cases}
\nabla \cdot \mathbf{E} = \dfrac{\rho}{\varepsilon_0} \\[8pt]
\nabla \cdot \mathbf{B} = 0 \\[8pt]
\nabla \times \mathbf{E} = -\dfrac{\partial \mathbf{B}}{\partial t} \\[8pt]
\nabla \times \mathbf{B} = \mu_0 \mathbf{J} + \mu_0\varepsilon_0 \dfrac{\partial \mathbf{E}}{\partial t}
\end{cases}
$$

积分形式：
$$
\begin{cases}
\displaystyle \oint_S \mathbf{E} \cdot d\mathbf{A} = \dfrac{Q}{\varepsilon_0} \\[12pt]
\displaystyle \oint_S \mathbf{B} \cdot d\mathbf{A} = 0 \\[12pt]
\displaystyle \oint_C \mathbf{E} \cdot d\mathbf{l} = -\dfrac{d}{dt}\int_S \mathbf{B} \cdot d\mathbf{A} \\[12pt]
\displaystyle \oint_C \mathbf{B} \cdot d\mathbf{l} = \mu_0 I + \mu_0\varepsilon_0 \dfrac{d}{dt}\int_S \mathbf{E} \cdot d\mathbf{A}
\end{cases}
$$

$$
\int_\infty^\infty
$$