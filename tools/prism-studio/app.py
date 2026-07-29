from __future__ import annotations

import os
import re
import signal
import socket
import subprocess
import sys
from datetime import date
from pathlib import Path

from PySide6.QtCore import QProcess, QTimer, QUrl, Qt
from PySide6.QtGui import QCloseEvent, QFont, QIcon
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDateEdit, QDialog,
    QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout,
    QInputDialog, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPlainTextEdit, QPushButton, QSpinBox, QSplitter, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from core import (
    article_assets, atomic_save, copy_images, create_collection,
    environment_status, find_port, import_project, publish_commands,
    resolve_command, serialize_frontmatter, split_frontmatter,
)


def discover_root() -> Path:
    starts = [Path(os.environ['PRISM_NOTES_ROOT']).expanduser() for _ in [0] if os.environ.get('PRISM_NOTES_ROOT')]
    starts.extend([Path.cwd(), Path(sys.executable).resolve().parent, Path(__file__).resolve().parent])
    for start in starts:
        for candidate in (start, *start.parents):
            if (candidate / 'package.json').exists() and (candidate / 'src/content/blog').is_dir():
                return candidate
    return Path.cwd()


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
    return base / relative


ROOT = discover_root()


class CollectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('新建合集')
        self.setMinimumWidth(440)
        form = QFormLayout(self)
        self.title = QLineEdit()
        self.slug = QLineEdit()
        self.description = QPlainTextEdit()
        self.description.setMaximumHeight(90)
        self.subtitle = QLineEdit()
        self.volume = QLineEdit()
        self.order = QSpinBox()
        self.order.setRange(0, 9999)
        self.order.setSpecialValueText('自动')
        self.status = QComboBox()
        self.status.addItem('连载中', 'ongoing')
        self.status.addItem('已完结', 'complete')
        self.status.addItem('暂停', 'paused')
        self.featured = QCheckBox('在书架中突出显示')
        form.addRow('标题 *', self.title)
        form.addRow('Slug（留空自动生成）', self.slug)
        form.addRow('简介 *', self.description)
        form.addRow('副标题', self.subtitle)
        form.addRow('卷号', self.volume)
        form.addRow('书架顺序', self.order)
        form.addRow('状态', self.status)
        form.addRow('', self.featured)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText('创建合集')
        buttons.button(QDialogButtonBox.Cancel).setText('取消')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self) -> dict:
        return {
            'title': self.title.text(),
            'slug': self.slug.text(),
            'description': self.description.toPlainText(),
            'subtitle': self.subtitle.text(),
            'volume': self.volume.text(),
            'order': self.order.value() or None,
            'status': self.status.currentData(),
            'featured': self.featured.isChecked(),
        }

    def accept(self):
        if not self.title.text().strip() or not self.description.toPlainText().strip():
            QMessageBox.warning(self, '信息不完整', '合集标题和简介不能为空。')
            (self.title if not self.title.text().strip() else self.description).setFocus()
            return
        super().accept()


class Studio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Prism Studio')
        self.setWindowIcon(QIcon(str(resource_path('assets/prism-studio-icon.png'))))
        self.resize(1500, 900)
        self.current_file: Path | None = None
        self.loading = False
        self.dev = QProcess(self)
        self.dev.setProcessChannelMode(QProcess.MergedChannels)
        self.dev.readyReadStandardOutput.connect(self.handle_dev_output)
        self.server_pid: int | None = None
        self.port = find_port()
        self.preview_path = '/'
        self.preview_ready = False
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(600)
        self.timer.timeout.connect(self.save_current)
        self.build_ui()
        self.load_tree()
        self.check_environment()
        self.start_preview()

    def build_ui(self):
        split = QSplitter(Qt.Horizontal)
        self.setCentralWidget(split)

        left = QWidget()
        lv = QVBoxLayout(left)
        title = QLabel('PRISM STUDIO')
        title.setObjectName('wordmark')
        lv.addWidget(title)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemSelectionChanged.connect(self.select_item)
        lv.addWidget(self.tree)
        create_row = QHBoxLayout()
        self.new_button = QPushButton('新建文章')
        self.new_button.clicked.connect(self.new_article)
        self.new_collection_button = QPushButton('新建合集')
        self.new_collection_button.clicked.connect(self.new_collection)
        create_row.addWidget(self.new_button)
        create_row.addWidget(self.new_collection_button)
        lv.addLayout(create_row)
        split.addWidget(left)

        middle = QWidget()
        mv = QVBoxLayout(middle)
        self.tabs = QTabWidget()
        form = QWidget()
        layout = QFormLayout(form)
        self.fields = {}
        for key, label in [('title', '标题'), ('description', '摘要'), ('category', '分类'), ('tags', '标签（逗号分隔）'), ('collection', '合集 slug'), ('cover', '封面'), ('canonical', 'Canonical URL')]:
            self.fields[key] = QLineEdit()
            layout.addRow(label, self.fields[key])
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(date.today())
        layout.addRow('发布日期', self.date)
        self.order = QSpinBox()
        self.order.setRange(0, 9999)
        layout.addRow('合集顺序（0=空）', self.order)
        self.draft = QCheckBox('草稿')
        self.featured = QCheckBox('置顶')
        checks = QHBoxLayout()
        checks.addWidget(self.draft)
        checks.addWidget(self.featured)
        layout.addRow('状态', checks)
        self.tabs.addTab(form, '文章参数')
        mv.addWidget(self.tabs)
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont('Computer Modern Typewriter Text', 14))
        self.editor.textChanged.connect(lambda: self.timer.start() if not self.loading else None)
        mv.addWidget(self.editor, 1)
        buttons = QHBoxLayout()
        image = QPushButton('插入图片')
        image.clicked.connect(self.insert_images)
        project = QPushButton('导入 GitHub 项目')
        project.clicked.connect(self.add_project)
        buttons.addWidget(image)
        buttons.addWidget(project)
        buttons.addStretch()
        mv.addLayout(buttons)
        split.addWidget(middle)

        right = QWidget()
        rv = QVBoxLayout(right)
        preview_bar = QHBoxLayout()
        self.preview_status = QLabel('预览连接中…')
        self.preview_status.setObjectName('previewStatus')
        reconnect = QPushButton('重新连接预览')
        reconnect.clicked.connect(self.reconnect_preview)
        env_button = QPushButton('重新检测环境')
        env_button.clicked.connect(self.check_environment)
        preview_bar.addWidget(self.preview_status)
        preview_bar.addStretch()
        preview_bar.addWidget(reconnect)
        preview_bar.addWidget(env_button)
        rv.addLayout(preview_bar)
        self.preview = QWebEngineView()
        self.preview.loadFinished.connect(self.preview_loaded)
        rv.addWidget(self.preview, 1)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(190)
        rv.addWidget(self.log)
        self.publish_current = QPushButton('发布当前内容')
        self.publish_current.clicked.connect(lambda: self.publish(False))
        self.publish_all = QPushButton('发布全部变更')
        self.publish_all.clicked.connect(lambda: self.publish(True))
        row = QHBoxLayout()
        row.addWidget(self.publish_current)
        row.addWidget(self.publish_all)
        rv.addLayout(row)
        self.project_button = project
        split.addWidget(right)
        split.setSizes([260, 580, 660])

        for widget in [*self.fields.values(), self.date, self.order, self.draft, self.featured]:
            signal_object = getattr(widget, 'textChanged', getattr(widget, 'dateChanged', getattr(widget, 'valueChanged', getattr(widget, 'toggled', None))))
            signal_object.connect(lambda *_: self.timer.start() if not self.loading else None)
        self.setStyleSheet(
            'QMainWindow{background:#fbfaf6;color:#181816}QWidget{font-size:13px}'
            '#wordmark{font-weight:600;letter-spacing:3px;padding:12px}'
            '#previewStatus{color:#68665f;padding:4px}'
            'QTreeWidget,QPlainTextEdit,QLineEdit,QDateEdit,QSpinBox,QComboBox{border:1px solid #aaa79f;background:#fffefa;padding:5px}'
            'QPushButton{min-height:34px;border:1px solid #181816;background:#fbfaf6;padding:4px 10px}'
            'QPushButton:hover{background:#181816;color:#fbfaf6}QPushButton:disabled{color:#999;border-color:#bbb}'
            'QTabWidget::pane{border:1px solid #aaa79f}'
        )

    def load_tree(self):
        self.tree.clear()
        for label, path, patterns in [('文章', ROOT / 'src/content/blog', ('index.md', 'index.mdx')), ('合集', ROOT / 'src/content/collections', ('.yaml', '.yml')), ('项目', ROOT / 'src/content/projects', ('.yaml', '.yml'))]:
            root = QTreeWidgetItem([label])
            self.tree.addTopLevelItem(root)
            root.setExpanded(True)
            if path.exists():
                files = [p for p in path.rglob('*') if p.is_file() and (p.name in patterns or p.suffix in patterns)]
                for file in sorted(files):
                    item = QTreeWidgetItem([file.parent.name if label == '文章' else file.stem])
                    item.setData(0, Qt.UserRole, str(file))
                    root.addChild(item)

    def check_environment(self):
        status = environment_status(ROOT)
        missing = [key for key, value in status.items() if not value]
        self.log.appendPlainText('环境检查：' + ('全部就绪' if not missing else '不可用：' + ', '.join(missing)))
        github = status['gh'] and status['gh_auth']
        publish_ready = status['git'] and status['npm'] and status['node'] and status['repository']
        self.project_button.setEnabled(github)
        self.publish_current.setEnabled(publish_ready)
        self.publish_all.setEnabled(publish_ready)
        if not status['gh_auth']:
            self.log.appendPlainText('GitHub API 认证无效：仅“导入 GitHub 项目”被禁用。发布仍可使用 Git/SSH；修复命令：gh auth login -h github.com')
        if not publish_ready:
            self.log.appendPlainText('发布需要 Node、npm、git 与当前 Git 仓库。Finder 启动时 Studio 会自动查找 Homebrew 和登录 shell 中的命令。')

    def start_preview(self):
        npm = resolve_command('npm')
        if not npm:
            self.preview_status.setText('未找到 npm，无法启动预览')
            self.log.appendPlainText('预览未启动：未找到 npm。请安装 Node.js 后点击“重新连接预览”。')
            return
        if self.dev.state() != QProcess.NotRunning:
            return
        self.preview_ready = False
        self.preview_status.setText('预览服务启动中…')
        self.port = find_port()
        self.dev.setWorkingDirectory(str(ROOT))
        self.dev.start(npm, ['run', 'dev', '--', '--host', '127.0.0.1', '--port', str(self.port)])
        if not self.dev.waitForStarted(4000):
            self.preview_status.setText('预览进程启动失败')
            self.log.appendPlainText(f'无法启动预览：{self.dev.errorString()}')
            return
        QTimer.singleShot(250, lambda: self.wait_for_preview(0))

    def handle_dev_output(self):
        output = bytes(self.dev.readAllStandardOutput()).decode(errors='replace').rstrip()
        if output:
            self.log.appendPlainText(output)
        url_match = re.search(r'https?://(?:127\.0\.0\.1|localhost):(\d+)', output)
        if url_match:
            self.port = int(url_match.group(1))
        pid_match = re.search(r'pid (\d+)', output)
        if pid_match and 'already running' not in output:
            self.server_pid = int(pid_match.group(1))

    def preview_url(self) -> QUrl:
        return QUrl(f'http://127.0.0.1:{self.port}{self.preview_path}')

    def wait_for_preview(self, attempt=0):
        try:
            with socket.create_connection(('127.0.0.1', self.port), timeout=.15):
                pass
            self.preview_ready = True
            self.preview_status.setText(f'预览已连接 · 127.0.0.1:{self.port}')
            self.preview.setUrl(self.preview_url())
        except OSError:
            if self.dev.state() == QProcess.NotRunning:
                self.preview_status.setText('预览服务已停止')
                self.log.appendPlainText('预览进程已停止。请点击“重新连接预览”重试。')
            elif attempt < 100:
                QTimer.singleShot(250, lambda: self.wait_for_preview(attempt + 1))
            else:
                self.preview_status.setText('预览连接超时')
                self.log.appendPlainText('预览服务连接超时。请点击“重新连接预览”；若仍失败，请检查 npm 日志。')

    def preview_loaded(self, success: bool):
        if success:
            self.preview_status.setText(f'预览已连接 · 127.0.0.1:{self.port}')
        elif self.preview_ready:
            self.preview_status.setText('页面加载失败，可重新连接预览')

    def reconnect_preview(self):
        try:
            with socket.create_connection(('127.0.0.1', self.port), timeout=.2):
                pass
            self.preview_ready = True
            self.preview.setUrl(self.preview_url())
            self.preview_status.setText(f'预览已重连 · 127.0.0.1:{self.port}')
        except OSError:
            if self.dev.state() != QProcess.NotRunning:
                self.dev.terminate()
                self.dev.waitForFinished(2500)
            self.start_preview()

    def select_item(self):
        items = self.tree.selectedItems()
        path = Path(items[0].data(0, Qt.UserRole)) if items and items[0].data(0, Qt.UserRole) else None
        if not path or path.suffix not in ('.md', '.mdx'):
            return
        self.current_file = path
        data, body = split_frontmatter(path.read_text('utf-8'))
        self.loading = True
        for key in ('title', 'description', 'category', 'cover', 'canonical', 'collection'):
            self.fields[key].setText(str(data.get(key, '') or ''))
        self.fields['tags'].setText(', '.join(data.get('tags', [])))
        published = data.get('publishDate', date.today())
        self.date.setDate(published if isinstance(published, date) else date.fromisoformat(str(published)))
        self.order.setValue(int(data.get('collectionOrder', 0) or 0))
        self.draft.setChecked(bool(data.get('draft', False)))
        self.featured.setChecked(bool(data.get('featured', False)))
        self.editor.setPlainText(body)
        self.loading = False
        self.preview_path = f'/blog/{path.parent.name}/'
        if self.preview_ready:
            self.preview.setUrl(self.preview_url())

    def metadata(self):
        return {'title': self.fields['title'].text(), 'description': self.fields['description'].text(), 'publishDate': self.date.date().toString('yyyy-MM-dd'), 'category': self.fields['category'].text(), 'tags': [tag.strip() for tag in self.fields['tags'].text().split(',') if tag.strip()], 'collection': self.fields['collection'].text() or None, 'collectionOrder': self.order.value() or None, 'cover': self.fields['cover'].text() or None, 'featured': self.featured.isChecked(), 'draft': self.draft.isChecked(), 'canonical': self.fields['canonical'].text() or None}

    def save_current(self):
        if not self.current_file or self.loading:
            return
        atomic_save(self.current_file, serialize_frontmatter(self.metadata(), self.editor.toPlainText()), ROOT)
        self.statusBar().showMessage('已自动保存', 1600)

    def new_article(self):
        title, ok = QInputDialog.getText(self, '新建文章', '标题')
        if not ok or not title.strip():
            return
        npm = resolve_command('npm')
        if not npm:
            return QMessageBox.warning(self, '无法创建文章', '未找到 npm。请安装 Node.js 后重新检测环境。')
        result = subprocess.run([npm, 'run', 'post:new', '--', '--title', title.strip()], cwd=ROOT, capture_output=True, text=True)
        self.log.appendPlainText(result.stdout + result.stderr)
        self.load_tree()

    def new_collection(self):
        dialog = CollectionDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            path = create_collection(ROOT, **dialog.values())
            self.load_tree()
            self.log.appendPlainText(f'合集已创建：{path.relative_to(ROOT)}')
            QMessageBox.information(self, '合集已创建', f'已创建 {path.stem}，现在可在文章参数中填写该 slug。')
        except (ValueError, FileExistsError) as error:
            QMessageBox.warning(self, '创建失败', str(error))

    def insert_images(self):
        if not self.current_file:
            return QMessageBox.information(self, '插入图片', '请先选择一篇文章。')
        names, _ = QFileDialog.getOpenFileNames(self, '选择图片', '', 'Images (*.webp *.avif *.png *.jpg *.jpeg)')
        try:
            for target in copy_images([Path(name) for name in names], self.current_file.parent):
                alt, ok = QInputDialog.getText(self, '图片替代文本', f'{target.name} 的替代文本')
                if ok and alt.strip():
                    self.editor.insertPlainText(f'![{alt.strip()}](./{target.name})')
        except ValueError as error:
            QMessageBox.warning(self, '图片导入失败', str(error))

    def add_project(self):
        repo, ok = QInputDialog.getText(self, '导入 GitHub 项目', '仓库 URL 或 owner/repo')
        if not ok:
            return
        try:
            path = import_project(repo, ROOT)
            self.load_tree()
            self.editor.insertPlainText(f'\n<GitHubProject repo="{repo.strip()}" />\n')
            self.log.appendPlainText(f'项目快照已保存：{path.relative_to(ROOT)}')
        except Exception as error:
            QMessageBox.warning(self, '导入失败', str(error))

    def run_command(self, command):
        resolved = resolve_command(command[0]) if command[0] in {'npm', 'node', 'git', 'gh'} else command[0]
        if not resolved:
            self.log.appendPlainText(f'未找到命令：{command[0]}')
            return False
        actual = [resolved, *command[1:]]
        self.log.appendPlainText('$ ' + ' '.join(command))
        QApplication.processEvents()
        result = subprocess.run(actual, cwd=ROOT, capture_output=True, text=True)
        self.log.appendPlainText((result.stdout + result.stderr).rstrip())
        return result.returncode == 0

    def publish(self, all_changes):
        status = environment_status(ROOT)
        if not all(status.get(key, False) for key in ('node', 'npm', 'git', 'repository')):
            return QMessageBox.warning(self, '环境未就绪', '发布需要 Node、npm、git 和当前 Git 仓库；GitHub CLI 登录不影响 SSH 推送。')
        self.save_current()
        message, ok = QInputDialog.getText(self, '提交说明', 'Git 提交说明', text='publish: update notes')
        if not ok or not message.strip():
            return
        paths = None if all_changes else article_assets(self.current_file, ROOT) if self.current_file else []
        for command in publish_commands(paths, message.strip(), all_changes):
            if command[:3] == ['git', 'commit', '-m']:
                git = resolve_command('git')
                diff = subprocess.run([git, 'diff', '--cached'], cwd=ROOT, capture_output=True, text=True).stdout if git else ''
                if QMessageBox.question(self, '确认发布', f'将提交以下变更：\n\n{diff[:5000]}') != QMessageBox.Yes:
                    return
            if not self.run_command(command):
                return QMessageBox.warning(self, '发布中止', '命令执行失败，请查看日志。已暂存内容不会被删除，可修复后重试。')
        QMessageBox.information(self, '发布完成', '提交已推送，GitHub Actions 将自动部署。')

    def closeEvent(self, event: QCloseEvent):
        self.save_current()
        self.dev.terminate()
        self.dev.waitForFinished(1500)
        if self.server_pid:
            try:
                os.kill(self.server_pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    icon = QIcon(str(resource_path('assets/prism-studio-icon.png')))
    app.setWindowIcon(icon)
    window = Studio()
    window.show()
    sys.exit(app.exec())
