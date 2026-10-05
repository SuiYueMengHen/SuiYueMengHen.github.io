# SuiYueMengHen — Personal Website

Astro 静态个人网站，包含 About Me、Blog 与 Projects，部署于 GitHub Pages。使用 Node.js 24，执行 `npm ci` 安装固定版本依赖。

```bash
npm run dev
npm run check
npm run test
npm run build
npm run test:e2e
```

## 全新的 Blog

Blog 是单栏 Markdown 阅读页面。旧文章、合集和分类已经移除，分类功能暂不上线。新页面没有自动编号、侧栏目录、阅读设置、评论或项目嵌入。标签是普通链接，不需要浏览器脚本。列表按日期倒序，每篇文章只出现一次。

`src/content/blog/example/index.md` 是明确标注的排版示例，可以替换或删除。文章目录中的图片与 Markdown 一起维护。生产构建排除草稿，开发模式允许预览草稿。

创建文章：

```bash
npm run post:new -- --title "文章标题"
```

只需标题和日期，其他字段可选：

```yaml
---
title: '文章标题'
publishDate: 2026-10-05
description: '可选的列表摘要'
tags: ['数学', '笔记']
cover: ./cover.webp
coverAlt: '头图的画面说明'
draft: false
---
```

有头图时，头图位于文章标题上方。正文使用普通 Markdown：标题、段落、列表、引用、图片、代码块、表格。建议正文从 `##` 开始，页面标题使用 `title` 字段。

## 数学公式

行内公式使用 `$E=mc^2$`。独立公式使用：

```tex
$$
\int_{-\infty}^{\infty}e^{-x^2}\,\mathrm{d}x=\sqrt{\pi}
$$
```

多行推导使用 `aligned`、`split` 或 `gathered`。KaTeX 在构建时生成 HTML 和 MathML，公式 CSS 与字体本地打包，无需客户端公式引擎。关闭 JavaScript 后也能阅读。无效或不支持的 TeX 会使构建失败。长公式在自己的容器内横向滚动，避免撑宽手机页面；多行公式需要作者明确安排换行。

## 发布

```bash
npm run post:publish -- 文章-slug
```

执行检查和构建后，通过 Git 提交并推送。合并到 `main` 后 GitHub Actions 部署到 Pages。`/build-info.json` 可核验线上提交。旧博客的内容仅保留在 Git 历史中，不生成旧文章、分类或合集页面，也不进入搜索、RSS 或站点地图。

## 维护

- 作者简介、GitHub 头像与履历：`src/config/site.ts`。
- 首页及 About Me：`src/components/AboutProfile.astro`。
- 全站主题：`src/styles/tokens.css`；首次访问跟随系统，日夜切换后保存选择。
- 博客样式：`src/styles/blog.css`。
- 文章：`src/content/blog/`；项目快照：`src/content/projects/`。
- 项目页面继续独立维护；使用 `npm run project:import -- owner/repo` 导入 GitHub 快照。
- 全文搜索位于 `/search/`，Pagefind 只在搜索时加载。

本次博客不沿用 `tools/prism-studio/` 的旧分类与合集写作配置；请直接编辑 Markdown 或使用 `post:new` 命令。

```bash
npm run format
npm run format:check
npm run check
npm run test
npm run build
npx playwright install chromium
npm run test:e2e
```

网站代码采用 MIT License。文章与图片版权归作者所有。
