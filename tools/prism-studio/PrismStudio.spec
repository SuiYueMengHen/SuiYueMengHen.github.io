from pathlib import Path
root = Path(SPECPATH).parents[1]
a = Analysis(['app.py'], pathex=[str(root)], datas=[('assets/prism-studio-icon.png','assets')], hiddenimports=['PySide6.QtWebEngineCore','PySide6.QtWebEngineWidgets','yaml'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz,a.scripts,[],exclude_binaries=True,name='Prism Studio',console=False)
coll = COLLECT(exe,a.binaries,a.datas,strip=False,name='Prism Studio')
app = BUNDLE(coll,name='Prism Studio.app',icon='assets/prism-studio-icon.png',bundle_identifier='io.github.suiyuemenghen.prismstudio')
