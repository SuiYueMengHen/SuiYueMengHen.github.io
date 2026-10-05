---
title: "Markdown 阅读示例"
description: "用于确认新博客排版的示例文章：文字、数学公式、代码与表格。"
publishDate: 2026-10-05
tags: [Markdown, 数学]
cover: ./cover.svg
coverAlt: "浅灰背景上的抽象曲线"
---

这是一篇**排版示例**，用于展示新博客的阅读效果。这里没有预置的分类或章节编号，正文直接按照 Markdown 的结构呈现。正式文章可以替换这篇示例。

## 文字与段落

留白让阅读更轻松。你可以使用 **粗体**、*斜体*、[链接](https://www.markdownguide.org/basic-syntax/)和 `行内代码`，也可以用简短的列表整理想法：

- 先说明问题。
- 再展开推导。
- 最后记录结论。

> 把复杂的想法写清楚，从一个简单的段落开始。

## 数学公式

行内公式可以自然融入文字。例如 $e^{i\pi}+1=0$，以及向量的内积 $\langle x,y\rangle=\sum_{k=1}^{n}x_k y_k$。

独立公式居中展示：

$$
\int_{-\infty}^{\infty} e^{-x^2}\,\mathrm{d}x=\sqrt{\pi}.
$$

多行推导可以使用 `aligned`：

$$
\begin{aligned}
f(x+h)&=f(x)+hf'(x)+\frac{h^2}{2}f''(x)+O(h^3),\\
\frac{f(x+h)-f(x)}{h}&=f'(x)+\frac{h}{2}f''(x)+O(h^2).
\end{aligned}
$$

矩阵也可以直接书写：

$$
A=\begin{pmatrix}1&2\\3&4\end{pmatrix},\qquad \det(A)=-2.
$$

下面是一条刻意保留的长公式，用来检查手机上的独立横向滚动：

$$
\prod_{k=1}^{n}(1+x_k)=1+\sum_{k=1}^{n}x_k+\sum_{1\le i<j\le n}x_i x_j+\sum_{1\le i<j<k\le n}x_i x_j x_k+\cdots+x_1 x_2\cdots x_n.
$$

## 代码

```python
def square(x: float) -> float:
    return x * x
```

## 表格

| 形式 | Markdown 写法 |
| --- | --- |
| 行内公式 | `$x^2$` |
| 独立公式 | 用一对 `$$` 包住公式 |
| 多行公式 | `aligned` 环境 |

---

文章只需要标题、日期和正文。标签与头图都是可选的；有头图时，它会出现在标题上方。
