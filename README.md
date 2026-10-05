# SuiYueMengHen — Personal Website

> 记录思考，构建有用的工具。

基于 Astro、Markdown/MDX 和 Pagefind 构建的个人静态博客，部署于 GitHub Pages。文章、合集、项目快照、图片、设置和主题源码全部保存在本仓库。

站点采用统一的无衬线字体、深灰／白色双主题与简约卡片布局。首页是 About Me，博客提供置顶封面卡片、时间列表、标签筛选与搜索，项目页支持语言筛选。文章公式由 KaTeX 在构建时生成 HTML + MathML，不加载浏览器端公式引擎。

使用 Node.js 24 或更新版本。依赖固定版本并通过 lockfile 安装，更新由 Dependabot 提供。

## 快速开始

```bash
npm ci
npm run dev
```

浏览器打开 `http://localhost:4321`。完整检查使用：

```bash
npm run check
npm run test
npm run build
npx playwright install chromium
npm run test:e2e
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
title: '文章标题'
description: '30—80 字的文章摘要'
publishDate: 2026-07-28
updatedDate: 2026-08-01 # 可选
category: '设计'
tags: ['设计', '界面']
collection: digital-garden # 可选：src/content/collections 中的 slug
collectionOrder: 1 # 加入合集时必填，正整数且不可重复
featured: false # true：在 Blog 页置顶，同时保留在时间列表中
cover: ./cover.webp # 可选：与文章放在同一目录
coverAlt: '封面画面说明' # 有封面时填写
draft: true
autoNumbering: true # 自动显示“一、 / §1.1 / §1.1.1”
showContents: true # 显示文章开头的书籍式目录
showSideToc: true # 显示跟随阅读位置的侧边目录
canonical: 'https://example.com/original' # 可选
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

公式由 KaTeX 在构建时生成 HTML 与用于辅助阅读的 MathML；CSS 和数学字体随站点本地打包，无第三方 CDN。正式网页与 Prism Studio 实时预览共用预渲染的输出，即使禁用 JavaScript 也能阅读公式。无效或不支持的 TeX 会在构建时报告错误，避免发布损坏公式。

超长块级公式保持字号，在自己的容器内横向滚动，不撑宽手机页面。建议使用 `aligned`、`split` 或 `gathered` 手动组织多行公式。KaTeX 不提供旧 MathJax 的实时自动断行；若迁移含高级 MathJax 宏或 `\\require` 的文章，请先确认 KaTeX 支持情况。

### 插入响应式图片

单图缩放与图注：

```markdown
![系统结构图](./architecture.webp 'prism:width=72%;caption=图 1：系统结构')
```

多图并排使用图库围栏，每张图都能指定自己的宽度；空间不足时会自动换行：

```markdown
:::gallery

![输入状态](./before.webp 'prism:width=48%;caption=调整前')

![输出状态](./after.webp 'prism:width=48%;caption=调整后')

:::
```

Prism Studio 的“插入图片”会可视化设置替代文本、可选图注、10%—100% 显示宽度，并提供裁切开关、比例、缩放和位置调整；也可以直接将图片文件拖到 Markdown 光标位置。一次选择或拖入多张图片时可直接生成上述图库语法。

### 章节与目录

文章标题会自动编号，不需要在 Markdown 中手写序号：

- `#` 显示为“一、”（后续依次为“二、”“三、”）
- `##` 显示为“§1.1”
- `###` 显示为“§1.1.1”

文章页生成可展开的目录和桌面端随文目录。页内目录默认收起，让读者更快进入正文；无需 JavaScript 也能展开与跳转。随文目录会根据阅读位置自动高亮当前章节。

### 阅读设置

文章页的设置按钮允许读者调整字号、行距和版心宽度，选择保存在当前浏览器。页面滚动完全使用操作系统与浏览器的原生惯性，仅锚点跳转使用平滑滚动；减少动态效果模式下锚点即时跳转。全站默认值集中在 `src/config/site.ts` 的 `reading` 字段中。

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

站点名称、作者简介、头像、履历时间轴、导航、社交链接、评论和统计开关统一位于 [`src/config/site.ts`](src/config/site.ts)。视觉颜色与字体位于 `src/styles/tokens.css`。首页与 `/about/` 共用 `AboutProfile` 组件；`author.timeline` 中每条填写 `period`、`title` 与可选的 `description`。项目 YAML 的 `featured: true` 决定首页精选，`order` 控制完整项目列表顺序。

主题首次访问时跟随系统，切换后记住选择；在首屏绘制前初始化，减少闪烁。系统字体不需要额外字体请求。普通页面没有数学脚本，全文搜索引擎仅在搜索时加载，评论 iframe 在接近视口时加载。

修改后运行 `npm run check && npm run build`，确认无误再推送。

## 合集与项目

合集保存在 `src/content/collections/*.yaml`，入口为 `/collections/`，Blog 页也提供合集链接。`/blog/` 展示所有公开文章：`featured: true` 的文章在顶部置顶，所有文章按时间倒序展示，并支持标题／摘要／标签筛选；全文搜索位于 `/search/`。合集章节仍按 `collectionOrder` 排序，分类页继续只收录散篇；所有原有文章、合集、分类、归档和 RSS 地址保留。

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

## 代码格式与验证

新增或修改页面时使用 Prettier 的 Astro 插件格式化。端到端测试针对生产构建运行（`http://127.0.0.1:4322`），可覆盖 Pagefind 搜索；运行前先执行 `npm run build`。测试包含日夜模式持久化、无 JavaScript 公式与目录、项目筛选、阅读设置、旧链接及 375／768／1024／1440px 无横向溢出。

```bash
npm run format
npm run check
npm run test
npm run build
npm run test:e2e
```

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
