# Prism Studio

Prism Notes 的本地三栏写作工具：左侧内容库，中间文章工作台，右侧真实 Astro 成品预览。

- 合集按章节展示，直接拖动文章即可重排，章节号会自动连续更新。
- 分类与合集从现有数据中选择，也可当场创建；标签池支持多选和新增标签。
- 摘要使用多行编辑器；封面可以选择本地图片并调整比例、缩放与裁切位置。
- 编辑停止约 180ms 后原子保存，Astro HMR 随即更新预览；预览断线会自动恢复。
- 每分钟在工作区干净时自动快进同步 GitHub，也可以点击顶部“同步 GitHub”。
- 未发布文章显示红点、增删行数和文件列表；发布全部变更成功后状态自动刷新。
- 支持新建、编辑和移除文章。移除的文章进入 `.prism-studio/trash`，不会立即永久删除。

```bash
python3 -m pip install -r tools/prism-studio/requirements.txt
npm run studio
```

发布依赖外部的 Node.js、npm 与 git；GitHub 项目导入额外依赖 `gh` 登录。即使 `gh` 认证失效，只要仓库的 Git/SSH 推送正常，发布按钮仍然可用。修复 API 认证可执行 `gh auth login -h github.com`。构建 macOS 应用：双击 `build-macos.command`，或运行 `cd tools/prism-studio && pyinstaller --clean --noconfirm PrismStudio.spec`。

应用会从当前目录和 `.app` 所在路径自动向上寻找 Prism Notes 仓库，并自动搜索 Homebrew 与登录 shell 中的命令；如需打开另一份仓库，可在启动前设置 `PRISM_NOTES_ROOT=/完整/仓库路径`。
