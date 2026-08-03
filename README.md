# 棱镜笔记 / Prism Notes

> 把复杂世界，折射成清晰的文字。

基于 Astro、Markdown/MDX 和 Pagefind 构建的个人静态博客，部署于 GitHub Pages。文章、合集、项目快照、图片、设置和主题源码全部保存在本仓库。

站点采用极简 LaTeX 论文风格，本地打包 Computer Modern 正文字体，并通过 MathJax SVG 支持行内公式与块级公式。

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

脚本会创建 `src/content/blog/文章-slug/index.md`。文章图片放在同一个目录。普通图片可继续写成 `![替代文本](./图片.webp)`；需要控制宽度或图注时使用 `![替代文本](./图片.webp "prism:width=64%;caption=可选图注")`，其中宽度限制为 10%—100%，`;caption=...` 可以省略。该语法同时兼容 Markdown 与 MDX。

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
collection: digital-garden # 可选：src/content/collections 中的 slug
collectionOrder: 1 # 加入合集时必填，正整数且不可重复
featured: false
draft: true
autoNumbering: true # 自动显示“一、 / §1.1 / §1.1.1”
showContents: true # 显示文章开头的书籍式目录
showSideToc: true # 显示跟随阅读位置的侧边目录
canonical: "https://example.com/original" # 可选
---
```

运行 `npm run dev` 可以预览草稿。生产构建会自动排除 `draft: true` 的文章。

上述三个阅读结构开关可以在 Prism Studio 的“文章信息 → 阅读结构”中独立调整。新文章和未填写这些字段的旧文章均默认全部开启；设置保存在文章 frontmatter 中，会随文章一起上传。

### 插入数学公式

Markdown 中使用标准 LaTeX 语法。行内公式写为 `$E = mc^2$`，块级公式写为：

```tex
$$
\int_{-\infty}^{\infty} e^{-x^2}\,dx = \sqrt{\pi}
$$
```

公式由 MathJax 在构建阶段渲染为 SVG，不需要浏览器运行额外脚本；正式网页与 Prism Studio 实时预览共用同一套输出。

超长块级公式会优先在顶层运算符处转换为 `aligned` 多行结构；分数、矩阵、cases 与手写多行环境不会被拆开。手机端保持可读字号，仍无法安全分段的公式只在公式自身区域横向滚动，不会撑宽整页。

### 插入响应式图片

单图缩放与图注：

```markdown
![系统结构图](./architecture.webp "prism:width=72%;caption=图 1：系统结构")
```

多图并排使用图库围栏，每张图都能指定自己的宽度；空间不足时会自动换行：

```markdown
:::gallery

![输入状态](./before.webp "prism:width=48%;caption=调整前")

![输出状态](./after.webp "prism:width=48%;caption=调整后")

:::
```

Prism Studio 的“插入图片”会可视化设置替代文本、可选图注、10%—100% 显示宽度，并提供裁切开关、比例、缩放和位置调整；也可以直接将图片文件拖到 Markdown 光标位置。一次选择或拖入多张图片时可直接生成上述图库语法。

### 章节与目录

文章标题会自动编号，不需要在 Markdown 中手写序号：

- `#` 显示为“一、”（后续依次为“二、”“三、”）
- `##` 显示为“§1.1”
- `###` 显示为“§1.1.1”

文章页会同时生成书籍式目录和桌面端随文目录。两者均可点击跳转；随文目录会根据阅读位置自动高亮当前章节。

### 阅读设置

页眉中的设置按钮允许读者调整字号、行距、版心宽度和段首缩进，选择保存在当前浏览器。页面滚动完全使用操作系统与浏览器的原生惯性，仅锚点跳转使用平滑滚动；减少动态效果模式下锚点即时跳转。全站默认值集中在 `src/config/site.ts` 的 `reading` 字段中。

评论区使用两份自定义 Giscus 主题：`public/giscus-latex-light.css` 与 `public/giscus-latex-dark.css`。它们通过 jsDelivr 加载，以满足 Giscus 自定义主题的跨域要求。

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

## 合集与项目

合集保存在 `src/content/collections/*.yaml`。`/blog/` 是合集书架，合集内文章只按 `collectionOrder` 排序，并完全独立于分类系统；未加入合集的文章才会进入按分类与中文标题排序的“散篇书架”。时间顺序仍可从页脚的归档入口查看。

导入或刷新 GitHub 项目快照：

```bash
gh auth login -h github.com # 仅认证失效时需要
npm run project:import -- owner/repo
```

项目数据保存于 `src/content/projects/*.yaml`，构建阶段不会请求 GitHub。在 `.mdx` 中可直接写 `<GitHubProject repo="owner/repo" />`，无需手动 import。

## Prism Studio 桌面写作工具

```bash
python3 -m pip install -r tools/prism-studio/requirements.txt
npm run studio
```

Prism Studio 提供文章/合集/项目浏览、文章与项目各自独立的可视化表单、Markdown/MDX 编辑、原子自动保存与首次修改备份、无闪烁 Astro 局部实时预览、图片管理、仅凭仓库地址导入 GitHub 项目，以及“上传当前内容 / 发布全部变更”两条可视化发布流程。发布会先推送 GitHub，再用 `/build-info.json` 核验 GitHub Pages 确实运行同一提交；草稿在上传前会明确提示是否转为公开文章。备份位于 `.prism-studio/backups/`，不会提交到 Git。

macOS `.app` 构建命令：

```bash
cd tools/prism-studio
pyinstaller --clean --noconfirm PrismStudio.spec
```

打包仅包含 Python、PySide6 与应用代码；Node、npm、git、gh 仍是外部依赖，用户凭据不会复制进应用。

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
src/content/collections/ 合集 YAML
src/content/projects/ GitHub 项目快照 YAML
src/config/site.ts  站点统一设置
src/pages/          页面和静态接口
src/components/     可复用组件
scripts/            新建、检查、发布文章的命令
tools/prism-studio/  PySide6 桌面写作工具
.github/workflows/  检查与 GitHub Pages 部署
```

## 初始内容状态

仓库以空内容库交付：文章、合集、项目快照与自定义分类均不预置数据。可通过 Prism Studio 或 `npm run post:new -- --title "文章标题"` 创建第一篇内容。

## License

网站代码采用 MIT License。文章与图片版权归作者所有，未经许可不得转载。
