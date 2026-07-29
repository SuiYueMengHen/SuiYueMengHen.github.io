from __future__ import annotations
import re, signal, socket, subprocess, sys
from datetime import date
from pathlib import Path
import os
from PySide6.QtCore import QProcess, QTimer, QUrl, Qt
from PySide6.QtGui import QAction, QCloseEvent, QFont
from PySide6.QtWidgets import (QApplication,QCheckBox,QComboBox,QDateEdit,QFileDialog,QFormLayout,QHBoxLayout,QInputDialog,QLabel,QLineEdit,QMainWindow,QMessageBox,QPlainTextEdit,QPushButton,QSpinBox,QSplitter,QTabWidget,QTreeWidget,QTreeWidgetItem,QVBoxLayout,QWidget)
from PySide6.QtWebEngineWidgets import QWebEngineView
from core import atomic_save,article_assets,copy_images,environment_status,find_port,import_project,publish_commands,serialize_frontmatter,split_frontmatter

def discover_root()->Path:
    starts=[Path(os.environ['PRISM_NOTES_ROOT']).expanduser() for _ in [0] if os.environ.get('PRISM_NOTES_ROOT')]
    starts.extend([Path.cwd(),Path(sys.executable).resolve().parent,Path(__file__).resolve().parent])
    for start in starts:
        for candidate in (start,*start.parents):
            if (candidate/'package.json').exists() and (candidate/'src/content/blog').is_dir():return candidate
    return Path.cwd()

ROOT=discover_root()

class Studio(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('Prism Studio');self.resize(1500,900);self.current_file=None;self.loading=False;self.dev=QProcess(self);self.server_pid=None;self.port=find_port();self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(600);self.timer.timeout.connect(self.save_current)
        self.build_ui();self.load_tree();self.check_environment();self.start_preview()
    def build_ui(self):
        split=QSplitter(Qt.Horizontal);self.setCentralWidget(split)
        left=QWidget();lv=QVBoxLayout(left);title=QLabel('PRISM STUDIO');title.setObjectName('wordmark');lv.addWidget(title);self.tree=QTreeWidget();self.tree.setHeaderHidden(True);self.tree.itemSelectionChanged.connect(self.select_item);lv.addWidget(self.tree);self.new_button=QPushButton('新建文章');self.new_button.clicked.connect(self.new_article);lv.addWidget(self.new_button);split.addWidget(left)
        middle=QWidget();mv=QVBoxLayout(middle);self.tabs=QTabWidget();form=QWidget();layout=QFormLayout(form);self.fields={}
        for key,label in [('title','标题'),('description','摘要'),('category','分类'),('tags','标签（逗号分隔）'),('collection','合集 slug'),('cover','封面'),('canonical','Canonical URL')]:self.fields[key]=QLineEdit();layout.addRow(label,self.fields[key])
        self.date=QDateEdit();self.date.setCalendarPopup(True);self.date.setDate(date.today());layout.addRow('发布日期',self.date);self.order=QSpinBox();self.order.setRange(0,9999);layout.addRow('合集顺序（0=空）',self.order);self.draft=QCheckBox('草稿');self.featured=QCheckBox('置顶');checks=QHBoxLayout();checks.addWidget(self.draft);checks.addWidget(self.featured);layout.addRow('状态',checks);self.tabs.addTab(form,'文章参数');mv.addWidget(self.tabs)
        self.editor=QPlainTextEdit();self.editor.setFont(QFont('Computer Modern Typewriter Text',14));self.editor.textChanged.connect(lambda:self.timer.start() if not self.loading else None);mv.addWidget(self.editor,1);buttons=QHBoxLayout();image=QPushButton('插入图片');image.clicked.connect(self.insert_images);project=QPushButton('导入 GitHub 项目');project.clicked.connect(self.add_project);buttons.addWidget(image);buttons.addWidget(project);buttons.addStretch();mv.addLayout(buttons);split.addWidget(middle)
        right=QWidget();rv=QVBoxLayout(right);self.preview=QWebEngineView();rv.addWidget(self.preview,1);self.log=QPlainTextEdit();self.log.setReadOnly(True);self.log.setMaximumHeight(190);rv.addWidget(self.log);publish_current=QPushButton('发布当前内容');publish_current.clicked.connect(lambda:self.publish(False));self.publish_all=QPushButton('发布全部变更');self.publish_all.clicked.connect(lambda:self.publish(True));row=QHBoxLayout();row.addWidget(publish_current);row.addWidget(self.publish_all);rv.addLayout(row);self.publish_current=publish_current;self.project_button=project;split.addWidget(right);split.setSizes([240,590,670])
        for widget in [*self.fields.values(),self.date,self.order,self.draft,self.featured]:getattr(widget,'textChanged',getattr(widget,'dateChanged',getattr(widget,'valueChanged',getattr(widget,'toggled',None)))).connect(lambda *_:self.timer.start() if not self.loading else None)
        self.setStyleSheet('QMainWindow{background:#fbfaf6;color:#181816}QWidget{font-size:13px}#wordmark{font-weight:600;letter-spacing:3px;padding:12px}QTreeWidget,QPlainTextEdit,QLineEdit,QDateEdit,QSpinBox,QComboBox{border:1px solid #aaa79f;background:#fffefa;padding:5px}QPushButton{min-height:34px;border:1px solid #181816;background:#fbfaf6;padding:4px 10px}QPushButton:hover{background:#181816;color:#fbfaf6}QTabWidget::pane{border:1px solid #aaa79f}')
    def load_tree(self):
        self.tree.clear()
        for label,path,patterns in [('文章',ROOT/'src/content/blog',('index.md','index.mdx')),('合集',ROOT/'src/content/collections',('.yaml','.yml')),('项目',ROOT/'src/content/projects',('.yaml','.yml'))]:
            root=QTreeWidgetItem([label]);self.tree.addTopLevelItem(root);root.setExpanded(True)
            if path.exists():
                files=[p for p in path.rglob('*') if p.is_file() and (p.name in patterns or p.suffix in patterns)]
                for file in sorted(files):item=QTreeWidgetItem([file.parent.name if label=='文章' else file.stem]);item.setData(0,Qt.UserRole,str(file));root.addChild(item)
    def check_environment(self):
        status=environment_status(ROOT);missing=[key for key,value in status.items() if not value];self.log.appendPlainText('环境检查：'+('全部就绪' if not missing else '不可用：'+', '.join(missing)))
        github=status['gh'] and status['gh_auth'];self.project_button.setEnabled(github);self.publish_current.setEnabled(github and status['git'] and status['npm']);self.publish_all.setEnabled(github and status['git'] and status['npm'])
        if not status['gh_auth']:self.log.appendPlainText('GitHub 认证无效：请在终端执行 gh auth login -h github.com，然后重启 Studio。')
    def start_preview(self):
        self.dev.setWorkingDirectory(str(ROOT));self.dev.setProcessChannelMode(QProcess.MergedChannels);self.dev.readyReadStandardOutput.connect(self.handle_dev_output);self.dev.start('npm',['run','dev','--','--host','127.0.0.1','--port',str(self.port)]);QTimer.singleShot(250,self.wait_for_preview)
    def handle_dev_output(self):
        output=bytes(self.dev.readAllStandardOutput()).decode(errors='replace').rstrip();self.log.appendPlainText(output)
        url_match=re.search(r'http://127\.0\.0\.1:(\d+)',output)
        if url_match:self.port=int(url_match.group(1))
        pid_match=re.search(r'pid (\d+)',output)
        if pid_match and 'already running' not in output:self.server_pid=int(pid_match.group(1))
    def wait_for_preview(self,attempt=0):
        try:
            with socket.create_connection(('127.0.0.1',self.port),timeout=.1):pass
            self.preview.setUrl(QUrl(f'http://127.0.0.1:{self.port}/'))
        except OSError:
            if attempt<80:QTimer.singleShot(250,lambda:self.wait_for_preview(attempt+1))
            else:self.log.appendPlainText('预览服务启动超时，请检查上方日志。')
    def select_item(self):
        items=self.tree.selectedItems();path=Path(items[0].data(0,Qt.UserRole)) if items and items[0].data(0,Qt.UserRole) else None
        if not path or path.suffix not in ('.md','.mdx'):return
        self.current_file=path;data,body=split_frontmatter(path.read_text('utf-8'));self.loading=True
        for key in ('title','description','category','cover','canonical','collection'):self.fields[key].setText(str(data.get(key,'')))
        self.fields['tags'].setText(', '.join(data.get('tags',[])));published=data.get('publishDate',date.today());self.date.setDate(published if isinstance(published,date) else date.fromisoformat(str(published)));self.order.setValue(int(data.get('collectionOrder',0) or 0));self.draft.setChecked(bool(data.get('draft',False)));self.featured.setChecked(bool(data.get('featured',False)));self.editor.setPlainText(body);self.loading=False;slug=path.parent.name;self.preview.setUrl(QUrl(f'http://127.0.0.1:{self.port}/blog/{slug}/'))
    def metadata(self):
        data={'title':self.fields['title'].text(),'description':self.fields['description'].text(),'publishDate':self.date.date().toString('yyyy-MM-dd'),'category':self.fields['category'].text(),'tags':[tag.strip() for tag in self.fields['tags'].text().split(',') if tag.strip()],'collection':self.fields['collection'].text() or None,'collectionOrder':self.order.value() or None,'cover':self.fields['cover'].text() or None,'featured':self.featured.isChecked(),'draft':self.draft.isChecked(),'canonical':self.fields['canonical'].text() or None};return data
    def save_current(self):
        if not self.current_file or self.loading:return
        atomic_save(self.current_file,serialize_frontmatter(self.metadata(),self.editor.toPlainText()),ROOT);self.statusBar().showMessage('已自动保存',1600)
    def new_article(self):
        title,ok=QInputDialog.getText(self,'新建文章','标题');
        if not ok or not title.strip():return
        result=subprocess.run(['npm','run','post:new','--','--title',title.strip()],cwd=ROOT,capture_output=True,text=True);self.log.appendPlainText(result.stdout+result.stderr);self.load_tree()
    def insert_images(self):
        if not self.current_file:return QMessageBox.information(self,'插入图片','请先选择一篇文章。')
        names,_=QFileDialog.getOpenFileNames(self,'选择图片','','Images (*.webp *.avif *.png *.jpg *.jpeg)')
        try:
            for target in copy_images([Path(name) for name in names],self.current_file.parent):
                alt,ok=QInputDialog.getText(self,'图片替代文本',f'{target.name} 的替代文本');
                if ok and alt.strip():self.editor.insertPlainText(f'![{alt.strip()}](./{target.name})')
        except ValueError as error:QMessageBox.warning(self,'图片导入失败',str(error))
    def add_project(self):
        repo,ok=QInputDialog.getText(self,'导入 GitHub 项目','仓库 URL 或 owner/repo');
        if not ok:return
        try:
            path=import_project(repo,ROOT);self.load_tree();self.editor.insertPlainText(f'\n<GitHubProject repo="{repo.strip()}" />\n');self.log.appendPlainText(f'项目快照已保存：{path.relative_to(ROOT)}')
        except Exception as error:QMessageBox.warning(self,'导入失败',str(error))
    def run_command(self,command):
        self.log.appendPlainText('$ '+' '.join(command));QApplication.processEvents();result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True);self.log.appendPlainText((result.stdout+result.stderr).rstrip());return result.returncode==0
    def publish(self,all_changes):
        status=environment_status(ROOT)
        if not all(status.get(key,False) for key in ('node','npm','git','gh','gh_auth','repository')):return QMessageBox.warning(self,'环境未就绪','请检查 Node、npm、git、gh 与登录状态。认证命令：gh auth login -h github.com')
        self.save_current();message,ok=QInputDialog.getText(self,'提交说明','Git 提交说明',text='publish: update notes');
        if not ok or not message.strip():return
        paths=None if all_changes else article_assets(self.current_file,ROOT) if self.current_file else []
        for command in publish_commands(paths,message.strip(),all_changes):
            if command[:3]==['git','commit','-m']:
                diff=subprocess.run(['git','diff','--cached'],cwd=ROOT,capture_output=True,text=True).stdout
                if QMessageBox.question(self,'确认发布',f'将提交以下变更：\n\n{diff[:5000]}')!=QMessageBox.Yes:return
            if not self.run_command(command):return QMessageBox.warning(self,'发布中止','命令执行失败，请查看日志。')
        QMessageBox.information(self,'发布完成','提交已推送，GitHub Actions 将自动部署。')
    def closeEvent(self,event:QCloseEvent):
        self.save_current();self.dev.terminate();self.dev.waitForFinished(1500)
        if self.server_pid:
            try:os.kill(self.server_pid,signal.SIGTERM)
            except ProcessLookupError:pass
        event.accept()

if __name__=='__main__':app=QApplication(sys.argv);window=Studio();window.show();sys.exit(app.exec())
