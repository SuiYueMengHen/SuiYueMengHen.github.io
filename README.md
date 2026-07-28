# 棱镜笔记 / Prism Notes

> 把复杂世界，折射成清晰的文字。

基于 Astro、Markdown 和 Pagefind 构建的个人静态博客，部署于 GitHub Pages。文章、图片、设置和主题源码全部保存在本仓库。

站点采用极简 LaTeX 论文风格，本地打包 Computer Modern 字体，并通过 KaTeX 支持行内公式与块级公式。

## 快速开始

```bash
npm install
npm run dev
```

浏览器打开 `http://localhost:4321`。完整检查使用：

```bash
npm run check
npm run test
npm run build
```

## 写一篇文章

### 1. 创建草稿

```bash
npm run post:new -- --title "文章标题"
```

脚本会创建 `src/content/blog/文章-slug/index.md`。文章图片放在同一个目录，通过 `![替代文本](./图片.webp)` 引用。建议使用 WebP 或 AVIF，并填写准确的替代文本。

### 2. 编辑与预览

frontmatter 示例：

```yaml
---
title: "文章标题"
description: "30—80 字的文章摘要"
publishDate: 2026-07-28
updatedDate: 2026-08-01 # 可选
category: "设计"
tags: ["设计", "界面"]
featured: false
draft: true
series: "系列名称" # 可选
canonical: "https://example.com/original" # 可选
---
```

运行 `npm run dev` 可以预览草稿。生产构建会自动排除 `draft: true` 的文章。

### 插入数学公式

Markdown 中使用标准 LaTeX 语法。行内公式写为 `$E = mc^2$`，块级公式写为：

```tex
$$
\int_{-\infty}^{\infty} e^{-x^2}\,dx = \sqrt{\pi}
$$
```

公式由 KaTeX 在构建阶段渲染，同时输出可访问的 MathML，不需要浏览器运行额外脚本。

### 3. 发布

```bash
npm run post:publish -- 文章-slug
npm run publish -- "发布：文章标题"
```

第二条命令会依次执行内容检查、测试、生产构建、Git 提交和推送。推送到 `main` 后，GitHub Actions 自动部署。

也可以在 GitHub 网页打开 Markdown 文件，点击铅笔图标编辑并提交；提交后同样会触发部署。

### 撤回文章

将文章 frontmatter 中的 `draft` 改为 `true`，提交并推送。文件和历史仍保留在 GitHub，但不会出现在网站、搜索、RSS 或站点地图中。

## 修改博客设置

站点名称、作者、首页文案、导航、社交链接、评论和统计开关统一位于 [`src/config/site.ts`](src/config/site.ts)。视觉颜色与字体位于 `src/styles/tokens.css`。

修改后运行 `npm run check && npm run build`，确认无误再推送。

## 评论配置

评论使用 [Giscus](https://giscus.app/zh-CN)，数据保存在本仓库的 GitHub Discussions。仓库创建后需要：

1. 在仓库 Settings → General → Features 开启 Discussions。
2. 安装 Giscus GitHub App，并允许访问本仓库。
3. 在 Giscus 配置页选择 `General` 分类。
4. 将生成的 `repoId` 与 `categoryId` 填入 `src/config/site.ts`。

仓库开启 Discussions 后，也可以运行 `npm run comments:configure` 自动读取并写入这些 ID。

缺少 ID 时网站会显示前往 Discussions 的降级入口，不会出现损坏的评论框。

## 自定义域名

1. 将 `astro.config.mjs` 和 `src/config/site.ts` 中的 `site` 改为自定义域名。
2. 创建 `public/CNAME`，内容仅为域名，例如 `blog.example.com`。
3. 在域名服务商配置 GitHub Pages 所需 DNS 记录。
4. 在仓库 Settings → Pages 中填写域名并启用 Enforce HTTPS。

项目使用用户站点仓库，不设置 Astro `base`；切换域名不需要修改内部链接。

## 目录说明

```text
src/content/blog/   Markdown/MDX 文章和配图
src/config/site.ts  站点统一设置
src/pages/          页面和静态接口
src/components/     可复用组件
scripts/            新建、检查、发布文章的命令
.github/workflows/  检查与 GitHub Pages 部署
```

## 演示文章

仓库初始包含三篇标注为“演示文章”的内容，用于展示排版和首页状态。写好正式文章后，可以直接删除对应的三个目录。

## License

网站代码采用 MIT License。文章与图片版权归作者所有，未经许可不得转载。
