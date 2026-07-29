# Prism Studio

Prism Notes 的本地三栏写作工具：左侧管理文章、创建合集并浏览项目，中间编辑元数据与 Markdown/MDX，右侧使用真实 Astro 页面实时预览。预览异常时可直接点击“重新连接预览”，无需重启应用。

```bash
python3 -m pip install -r tools/prism-studio/requirements.txt
npm run studio
```

发布依赖外部的 Node.js、npm 与 git；GitHub 项目导入额外依赖 `gh` 登录。即使 `gh` 认证失效，只要仓库的 Git/SSH 推送正常，发布按钮仍然可用。修复 API 认证可执行 `gh auth login -h github.com`。构建 macOS 应用：双击 `build-macos.command`，或运行 `cd tools/prism-studio && pyinstaller --clean --noconfirm PrismStudio.spec`。

应用会从当前目录和 `.app` 所在路径自动向上寻找 Prism Notes 仓库，并自动搜索 Homebrew 与登录 shell 中的命令；如需打开另一份仓库，可在启动前设置 `PRISM_NOTES_ROOT=/完整/仓库路径`。
