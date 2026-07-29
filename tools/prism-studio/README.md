# Prism Studio

Prism Notes 的本地三栏写作工具：左侧管理文章/合集/项目，中间编辑元数据与 Markdown/MDX，右侧使用真实 Astro 页面实时预览。

```bash
python3 -m pip install -r tools/prism-studio/requirements.txt
npm run studio
```

GitHub 项目导入与发布依赖外部的 Node.js、npm、git、gh。认证失效时执行 `gh auth login -h github.com`。构建 macOS 应用：双击 `build-macos.command`，或运行 `cd tools/prism-studio && pyinstaller --clean --noconfirm PrismStudio.spec`。

应用会从当前目录和 `.app` 所在路径自动向上寻找 Prism Notes 仓库；如需打开另一份仓库，可在启动前设置 `PRISM_NOTES_ROOT=/完整/仓库路径`。
