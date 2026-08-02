from __future__ import annotations

import os
import json
import re
import signal
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from PySide6.QtCore import QPoint, QProcess, QProcessEnvironment, QRect, QTimer, QUrl, Qt, Signal, QObject, Slot
from PySide6.QtGui import QCloseEvent, QColor, QFont, QIcon, QImage, QPainter, QPalette, QPen, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkProxy, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QFileDialog, QFormLayout, QFrame, QHBoxLayout, QInputDialog, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy, QSlider, QSpinBox,
    QSplitter, QStackedWidget, QTabWidget, QTextEdit, QTreeWidget, QTreeWidgetItemIterator,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PySide6.QtWebChannel import QWebChannel

from core import (
    article_assets, article_preview_version, atomic_save, command_environment, content_catalog, copy_images, create_article, create_collection,
    create_category, delete_category, delete_project_snapshot, delete_trash_entries, ensure_mdx_article, environment_status, execute_publish, find_port,
    git_content_changes, import_project, list_trash, load_collection_snapshot, load_project_snapshot, migrate_category, move_article, normalize_repo, pages_site_url, preview_route, restore_trash_entry,
    category_preview_version, collection_preview_version, project_preview_version, reorder_collection, reorder_collections, reorder_projects, resolve_command, save_collection_snapshot, save_project_snapshot, serialize_frontmatter, split_frontmatter, trash_article,
    wait_for_pages_deployment,
)


def valid_root(path: Path) -> bool:
    return (path / 'package.json').is_file() and (path / 'src/content/blog').is_dir()


def app_settings_path() -> Path:
    return Path.home() / 'Library/Application Support/Prism Studio/settings.json'


def read_app_settings() -> dict:
    try:return json.loads(app_settings_path().read_text('utf-8'))
    except (OSError,json.JSONDecodeError):return {}


def write_app_settings(data: dict) -> None:
    try:
        path=app_settings_path();path.parent.mkdir(parents=True,exist_ok=True);temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf-8');os.replace(temporary,path)
    except OSError:pass


def discover_root() -> Path:
    saved=read_app_settings().get('workspace');starts=[Path(os.environ['PRISM_NOTES_ROOT']).expanduser() for _ in [0] if os.environ.get('PRISM_NOTES_ROOT')]
    if saved:starts.append(Path(saved).expanduser())
    starts.extend([Path.cwd(),Path(sys.executable).resolve().parent,Path(__file__).resolve().parent,Path.home()/'Desktop/blog',Path.home()/'Documents/blog'])
    for start in starts:
        for candidate in (start, *start.parents):
            if valid_root(candidate):return candidate
    return Path.cwd()


def resource_path(relative: str) -> Path:
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / relative


def configure_process(process: QProcess) -> None:
    environment=QProcessEnvironment.systemEnvironment()
    for key,value in command_environment().items():environment.insert(key,value)
    environment.insert('ASTRO_DEV_BACKGROUND','0')
    process.setProcessEnvironment(environment)


def semantic_value(value):
    if isinstance(value,date):return value.isoformat()
    if isinstance(value,list):return [semantic_value(item) for item in value]
    if isinstance(value,dict):return {key:semantic_value(item) for key,item in value.items() if item not in (None,'',[])}
    return value


ROOT = discover_root()
ROLE_KIND, ROLE_PATH, ROLE_COLLECTION = Qt.UserRole, Qt.UserRole + 1, Qt.UserRole + 2


class StablePreviewInterceptor(QWebEngineUrlRequestInterceptor):
    """Keep the embedded page stable; Studio applies content updates itself."""
    def interceptRequest(self,info):
        url=info.requestUrl()
        if url.path()=='/@vite/client' or url.host()=='giscus.app':info.block(True)


class StableMarkdownEditor(QPlainTextEdit):
    """Keep IME composition and the user's insertion point under editor ownership."""
    compositionCommitted = Signal()

    def __init__(self,parent=None):
        super().__init__(parent);self.composing=False

    def inputMethodEvent(self,event):
        was_composing=self.composing;self.composing=bool(event.preeditString());super().inputMethodEvent(event)
        if not self.composing and (was_composing or event.commitString()):self.compositionCommitted.emit()


class PreviewScrollBridge(QObject):
    """Receive rendered source positions directly from the preview scroll event."""

    def __init__(self,studio):
        super().__init__(studio);self.studio=studio

    @Slot(float)
    def previewScrolled(self,line):
        self.studio.apply_preview_scroll(line)


class TagPicker(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self);layout.setContentsMargins(0, 0, 0, 0);layout.setSpacing(7)
        row = QHBoxLayout();self.input = QLineEdit();self.input.setPlaceholderText('输入新标签，回车创建')
        add = QPushButton('添加');add.setProperty('compact', True);add.clicked.connect(self.add_current);self.input.returnPressed.connect(self.add_current)
        row.addWidget(self.input, 1);row.addWidget(add);layout.addLayout(row)
        self.list = QListWidget();self.list.setObjectName('tagPool');self.list.setMinimumHeight(108);self.list.itemChanged.connect(lambda *_: self.changed.emit());layout.addWidget(self.list)

    def set_pool(self, pool: list[str], selected: list[str]):
        self.list.blockSignals(True);self.list.clear();all_tags=list(dict.fromkeys([*selected,*sorted(set(pool)-set(selected))]))
        for tag in all_tags:
            item=QListWidgetItem(tag);item.setFlags(item.flags()|Qt.ItemIsUserCheckable);item.setCheckState(Qt.Checked if tag in selected else Qt.Unchecked);self.list.addItem(item)
        self.list.blockSignals(False)

    def selected_tags(self) -> list[str]:
        return [self.list.item(i).text() for i in range(self.list.count()) if self.list.item(i).checkState()==Qt.Checked]

    def add_current(self):
        tag=self.input.text().strip()
        if not tag:return
        for i in range(self.list.count()):
            if self.list.item(i).text()==tag:self.list.item(i).setCheckState(Qt.Checked);break
        else:
            item=QListWidgetItem(tag);item.setFlags(item.flags()|Qt.ItemIsUserCheckable);item.setCheckState(Qt.Checked);self.list.addItem(item)
        self.input.clear();self.changed.emit()


class CollectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent);self.setWindowTitle('新建合集');self.setMinimumWidth(480);self.setObjectName('sheet')
        form=QFormLayout(self);form.setSpacing(12);self.title=QLineEdit();self.slug=QLineEdit();self.description=QTextEdit();self.description.setMinimumHeight(100);self.subtitle=QLineEdit();self.volume=QLineEdit();self.order_hint=QLabel('创建后位于书架末尾，可在左侧直接拖动排序。');self.order_hint.setObjectName('muted');self.order_hint.setWordWrap(True);self.status=QComboBox();self.status.addItem('连载中','ongoing');self.status.addItem('已完结','complete');self.status.addItem('暂停','paused');self.featured=QCheckBox('在书架中突出显示')
        for label,widget in [('标题 *',self.title),('Slug（留空自动生成）',self.slug),('简介 *',self.description),('副标题',self.subtitle),('卷号',self.volume),('书架顺序',self.order_hint),('状态',self.status),('',self.featured)]:form.addRow(label,widget)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.button(QDialogButtonBox.Ok).setText('创建合集');buttons.button(QDialogButtonBox.Cancel).setText('取消');buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);form.addRow(buttons)

    def values(self):
        return {'title':self.title.text(),'slug':self.slug.text(),'description':self.description.toPlainText(),'subtitle':self.subtitle.text(),'volume':self.volume.text(),'order':None,'status':self.status.currentData(),'featured':self.featured.isChecked()}

    def accept(self):
        if not self.title.text().strip() or not self.description.toPlainText().strip():
            QMessageBox.warning(self,'信息不完整','合集标题和简介不能为空。');(self.title if not self.title.text().strip() else self.description).setFocus();return
        super().accept()


class CategoryDialog(QDialog):
    def __init__(self,categories,parent=None):
        super().__init__(parent);self.setWindowTitle('管理分类');self.setMinimumSize(440,360);self.action=None
        layout=QVBoxLayout(self);hint=QLabel('合集文章不会出现在分类中。重命名或删除会批量迁移文章。');hint.setWordWrap(True);hint.setObjectName('muted');layout.addWidget(hint)
        self.list=QListWidget();self.list.addItems(categories);layout.addWidget(self.list,1)
        buttons=QHBoxLayout();rename=QPushButton('重命名');remove=QPushButton('删除并归入未分类');remove.setProperty('danger',True);close=QPushButton('完成')
        rename.clicked.connect(lambda:self.finish('rename'));remove.clicked.connect(lambda:self.finish('delete'));close.clicked.connect(self.reject)
        buttons.addWidget(rename);buttons.addWidget(remove);buttons.addStretch();buttons.addWidget(close);layout.addLayout(buttons)

    def finish(self,action):
        if not self.list.currentItem():return QMessageBox.information(self,'请选择分类','请先在列表中选择一个分类。')
        self.action=(action,self.list.currentItem().text());self.accept()


class TrashDialog(QDialog):
    def __init__(self,repo_root:Path,parent=None):
        super().__init__(parent);self.repo_root=repo_root;self.changed=False;self.setWindowTitle('文章废纸篓');self.setMinimumSize(620,430)
        layout=QVBoxLayout(self);hint=QLabel('废纸篓中的标题不占用内容库名称。恢复时若标题或 slug 与现有文章冲突，将停止恢复并提示。');hint.setObjectName('muted');hint.setWordWrap(True);layout.addWidget(hint)
        self.list=QListWidget();self.list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection);layout.addWidget(self.list,1)
        controls=QHBoxLayout();select_all=QPushButton('全选');restore=QPushButton('恢复所选');remove=QPushButton('永久删除所选');remove.setProperty('danger',True);empty=QPushButton('清空废纸篓');empty.setProperty('danger',True);close=QPushButton('完成');select_all.clicked.connect(self.list.selectAll);restore.clicked.connect(self.restore_selected);remove.clicked.connect(self.delete_selected);empty.clicked.connect(self.empty_trash);close.clicked.connect(self.accept)
        for button in (select_all,restore,remove,empty):controls.addWidget(button)
        controls.addStretch();controls.addWidget(close);layout.addLayout(controls);self.reload_items()

    def reload_items(self):
        self.list.clear()
        for entry in list_trash(self.repo_root):
            deleted=f" · {entry['deletedAt'][:10]}" if entry.get('deletedAt') else '';item=QListWidgetItem(f"《{entry['title']}》 · {entry['slug']}{deleted}");item.setData(Qt.UserRole,str(entry['path']));item.setToolTip(str(entry['path'].relative_to(self.repo_root)));self.list.addItem(item)
        if not self.list.count():self.list.addItem('废纸篓为空');self.list.item(0).setFlags(Qt.NoItemFlags)

    def selected_paths(self):return [Path(item.data(Qt.UserRole)) for item in self.list.selectedItems() if item.data(Qt.UserRole)]

    def restore_selected(self):
        paths=self.selected_paths()
        if not paths:return QMessageBox.information(self,'请选择文章','请先选择需要恢复的文章。')
        restored=[];errors=[]
        for path in paths:
            try:restored.append(restore_trash_entry(path,self.repo_root))
            except (OSError,ValueError,FileExistsError) as error:errors.append(str(error))
        if restored:self.changed=True;self.reload_items();QMessageBox.information(self,'恢复完成',f'已恢复 {len(restored)} 篇文章。')
        if errors:QMessageBox.warning(self,'部分文章无法恢复','\n\n'.join(errors))

    def delete_selected(self):
        paths=self.selected_paths()
        if not paths:return QMessageBox.information(self,'请选择文章','请先选择需要永久删除的文章。')
        if QMessageBox.question(self,'永久删除',f'确定永久删除所选 {len(paths)} 篇文章吗？\n\n此操作无法从 Prism Studio 撤销。')!=QMessageBox.Yes:return
        try:deleted=delete_trash_entries(paths,self.repo_root)
        except (OSError,ValueError) as error:return QMessageBox.warning(self,'删除失败',str(error))
        self.changed=True;self.reload_items();QMessageBox.information(self,'删除完成',f'已永久删除 {deleted} 篇文章。')

    def empty_trash(self):
        paths=[entry['path'] for entry in list_trash(self.repo_root)]
        if not paths:return QMessageBox.information(self,'废纸篓为空','没有可以删除的文章。')
        if QMessageBox.question(self,'清空废纸篓',f'确定永久删除废纸篓中的全部 {len(paths)} 篇文章吗？\n\n此操作无法从 Prism Studio 撤销。')!=QMessageBox.Yes:return
        try:delete_trash_entries(paths,self.repo_root)
        except (OSError,ValueError) as error:return QMessageBox.warning(self,'清空失败',str(error))
        self.changed=True;self.reload_items();QMessageBox.information(self,'废纸篓已清空','所有文章已永久删除。')


class CropCanvas(QLabel):
    def __init__(self, pixmap: QPixmap):
        super().__init__();self.source=pixmap;self.zoom=100;self.x_offset=0;self.y_offset=0;self.ratio=16/9;self.setMinimumSize(560,315);self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

    def crop_rect(self) -> QRect:
        width,height=self.source.width(),self.source.height();base_w=width*100/self.zoom;base_h=base_w/self.ratio
        if base_h>height*100/self.zoom:base_h=height*100/self.zoom;base_w=base_h*self.ratio
        crop_w=max(1,min(width,int(base_w)));crop_h=max(1,min(height,int(base_h)));max_x=width-crop_w;max_y=height-crop_h
        x=int(max_x*(self.x_offset+100)/200);y=int(max_y*(self.y_offset+100)/200);return QRect(x,y,crop_w,crop_h)

    def paintEvent(self,event):
        painter=QPainter(self);painter.fillRect(self.rect(),QColor('#171713'));crop=self.source.copy(self.crop_rect()).scaled(self.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation);x=(self.width()-crop.width())//2;y=(self.height()-crop.height())//2;painter.drawPixmap(x,y,crop);painter.setPen(QPen(QColor('#d24a34'),2));painter.drawRect(x,y,crop.width()-1,crop.height()-1)


class CoverCropDialog(QDialog):
    def __init__(self, source: Path, parent=None):
        super().__init__(parent);self.setWindowTitle('裁切文章封面');self.resize(720,560);pixmap=QPixmap(str(source))
        if pixmap.isNull():raise ValueError('无法读取这张图片。')
        self.canvas=CropCanvas(pixmap);layout=QVBoxLayout(self);layout.addWidget(self.canvas,1)
        ratio=QComboBox();ratio.addItem('16:9 横向封面',16/9);ratio.addItem('3:2 摄影比例',3/2);ratio.addItem('1:1 方形',1.0);ratio.currentIndexChanged.connect(lambda:self.set_ratio(ratio.currentData()))
        controls=QFormLayout();controls.addRow('裁切比例',ratio)
        for label,attr,minimum,maximum,value in [('缩放','zoom',100,250,100),('水平位置','x_offset',-100,100,0),('垂直位置','y_offset',-100,100,0)]:
            slider=QSlider(Qt.Horizontal);slider.setRange(minimum,maximum);slider.setValue(value);slider.valueChanged.connect(lambda v,a=attr:self.adjust(a,v));controls.addRow(label,slider)
        layout.addLayout(controls);buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel);buttons.button(QDialogButtonBox.Save).setText('使用此裁切');buttons.button(QDialogButtonBox.Cancel).setText('取消');buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)

    def set_ratio(self,value):self.canvas.ratio=float(value);self.canvas.update()
    def adjust(self,attr,value):setattr(self.canvas,attr,value);self.canvas.update()
    def cropped_image(self):return self.canvas.source.copy(self.canvas.crop_rect()).toImage()


class ContentTree(QTreeWidget):
    articleMoved = Signal(str, str, str, list)
    orderChanged = Signal(str, list)
    dropRejected = Signal(str)

    def __init__(self):
        super().__init__();self._drag_payload=None;self._last_article_target=None;self.setHeaderHidden(True);self.setIndentation(16);self.setAnimated(True);self.setDragDropMode(QTreeWidget.InternalMove);self.setDefaultDropAction(Qt.MoveAction);self.setSelectionMode(QTreeWidget.SingleSelection);self.setDropIndicatorShown(True);self.setAutoExpandDelay(280)

    def startDrag(self,supported_actions):
        item=self.currentItem();self._last_article_target=None
        self._drag_payload={'kind':item.data(0,ROLE_KIND),'path':str(item.data(0,ROLE_PATH) or '')} if item else None
        try:super().startDrag(supported_actions)
        finally:self._drag_payload=None;self._last_article_target=None

    def article_destination(self,target):
        if not target:return None
        kind=target.data(0,ROLE_KIND)
        destination=target.parent() if kind=='article' else target
        if destination and destination.data(0,ROLE_KIND) in {'collection','category'}:return destination,target if kind=='article' else None
        return None

    def dragMoveEvent(self,event):
        payload=self._drag_payload
        if payload and payload.get('kind')=='article':
            resolved=self.article_destination(self.itemAt(event.position().toPoint()))
            if resolved:
                destination,target_article=resolved;destination_kind=destination.data(0,ROLE_KIND);destination_id=str(destination.data(0,ROLE_COLLECTION) or '')
                self._last_article_target=(destination_kind,destination_id,str(target_article.data(0,ROLE_PATH) or '') if target_article else '')
                super().dragMoveEvent(event)
                if not event.isAccepted():event.acceptProposedAction()
                return
            if self._last_article_target:event.acceptProposedAction();return
            event.ignore();return
        super().dragMoveEvent(event)

    def dropEvent(self,event):
        payload=self._drag_payload or ({'kind':self.currentItem().data(0,ROLE_KIND),'path':str(self.currentItem().data(0,ROLE_PATH) or '')} if self.currentItem() else None);target=self.itemAt(event.position().toPoint())
        if not payload:event.ignore();return
        kind=payload.get('kind');dragged_path=payload.get('path','');target_kind=target.data(0,ROLE_KIND) if target else ''
        if kind=='article':
            resolved=self.article_destination(target);target_path=''
            if resolved:
                destination,target_article=resolved;destination_kind=destination.data(0,ROLE_KIND);destination_id=str(destination.data(0,ROLE_COLLECTION) or '');target_path=str(target_article.data(0,ROLE_PATH) or '') if target_article else ''
            elif self._last_article_target:
                destination_kind,destination_id,target_path=self._last_article_target;destination=self.find_destination(destination_kind,destination_id)
            else:destination=None;destination_kind='';destination_id=''
            if not destination or not destination_id:
                self.dropRejected.emit('请将文章放到具体的合集或分类名称上');event.ignore();return
            if target_path==dragged_path:event.ignore();return
            paths=[Path(destination.child(i).data(0,ROLE_PATH)) for i in range(destination.childCount()) if destination.child(i).data(0,ROLE_KIND)=='article' and str(destination.child(i).data(0,ROLE_PATH) or '')!=dragged_path]
            if target_path:
                target_file=Path(target_path);insert=paths.index(target_file) if target_file in paths else len(paths)
                if self.dropIndicatorPosition()==QAbstractItemView.DropIndicatorPosition.BelowItem:insert+=1
                paths.insert(min(insert,len(paths)),Path(dragged_path))
            else:paths.append(Path(dragged_path))
            ordered=[str(path) for path in paths]
            # QTreeWidget still owns persistent indexes until dropEvent returns. Rebuilding
            # synchronously here can make Qt apply the tail of the old drag to the new tree.
            self.setEnabled(False);QTimer.singleShot(0,lambda:self.finish_article_drop(dragged_path,destination_kind,destination_id,ordered));event.ignore();return
        dragged=self.find_path_item(dragged_path,kind);roots={'collection':'collections-root','project':'projects-root'}
        if not dragged or not target:event.ignore();return
        if kind not in roots:event.ignore();return
        root=dragged.parent();destination=target.parent() if target_kind==kind else target
        if not root or root.data(0,ROLE_KIND)!=roots[kind] or destination is not root:event.ignore();return
        dragged_path=str(dragged.data(0,ROLE_PATH));paths=[str(root.child(i).data(0,ROLE_PATH)) for i in range(root.childCount()) if root.child(i).data(0,ROLE_PATH)!=dragged_path]
        if target_kind==kind:
            target_path=str(target.data(0,ROLE_PATH));insert=paths.index(target_path) if target_path in paths else len(paths);paths.insert(insert,dragged_path)
        else:paths.append(dragged_path)
        self.setEnabled(False);QTimer.singleShot(0,lambda:self.finish_order_drop(kind,paths));event.ignore()

    def find_path_item(self,path,kind=''):
        iterator=QTreeWidgetItemIterator(self)
        while iterator.value():
            item=iterator.value()
            if str(item.data(0,ROLE_PATH) or '')==path and (not kind or item.data(0,ROLE_KIND)==kind):return item
            iterator+=1
        return None

    def find_destination(self,kind,identifier):
        iterator=QTreeWidgetItemIterator(self)
        while iterator.value():
            item=iterator.value()
            if item.data(0,ROLE_KIND)==kind and str(item.data(0,ROLE_COLLECTION) or '')==identifier:return item
            iterator+=1
        return None

    def finish_article_drop(self,article_path,destination_kind,destination_id,ordered_paths):
        try:self.articleMoved.emit(article_path,destination_kind,destination_id,ordered_paths)
        finally:self._last_article_target=None;self.setEnabled(True);self.setFocus()

    def finish_order_drop(self,kind,ordered_paths):
        try:self.orderChanged.emit(kind,ordered_paths)
        finally:self.setEnabled(True);self.setFocus()


class Studio(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('Prism Studio');self.setWindowIcon(QIcon(str(resource_path('assets/prism-studio-icon.png'))));self.resize(1580,960);self.setMinimumSize(1180,760);self.theme=read_app_settings().get('theme','light')
        self.current_file:Path|None=None;self.selected_kind='';self.selected_path:Path|None=None;self.selected_category='';self.original_metadata={};self.original_body='';self.loaded_view_state=None;self.loading=False;self.document_dirty=False;self.project_loading=False;self.project_original={};self.project_loaded_state=None;self.collection_loading=False;self.collection_original={};self.collection_loaded_state=None;self.category_loading=False;self.category_original_name='';self.catalog={};self.changes={};self.collection_changes={};self.project_changes={};self.content_change_files=[];self.change_refresh_queued=False;self.preview_path='/';self.preview_ready=False;self.preview_loading=False;self.preview_failures=0;self.preview_dom_attempts=0;self.preview_navigation=0;self.preview_patch_generation=0;self.preview_expected_version='';self.preview_starting_until=0.0;self.preview_refresh_pending=False;self.preview_scroll_suppressed_until=0.0;self.applying_preview_scroll=False;self.editor_sync_mode='scroll';self.legacy_preview_restarted=False;self.server_pid=None;self.gh_ready=False;self.executor=ThreadPoolExecutor(max_workers=4,thread_name_prefix='prism-studio');self.environment_future=None;self.change_future=None;self.publish_future=None;self.deployment_future=None;self.sync_future=None;self.project_future=None;self.preview_reply=None;self.preview_network=QNetworkAccessManager(self);self.preview_network.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy));self.port=find_port();self.dev=QProcess(self);configure_process(self.dev);self.dev.setProcessChannelMode(QProcess.MergedChannels);self.dev.readyReadStandardOutput.connect(self.handle_dev_output);self.dev.finished.connect(lambda *_:QTimer.singleShot(250,self.ensure_preview))
        settings=read_app_settings();last_article=Path(settings.get('last_article','')) if settings.get('workspace')==str(ROOT) and settings.get('last_article') else None
        if last_article and last_article.is_file():self.current_file=last_article
        self.save_timer=QTimer(self);self.save_timer.setSingleShot(True);self.save_timer.setInterval(360);self.save_timer.timeout.connect(self.save_current)
        self.project_save_timer=QTimer(self);self.project_save_timer.setSingleShot(True);self.project_save_timer.setInterval(180);self.project_save_timer.timeout.connect(self.save_project_current)
        self.collection_save_timer=QTimer(self);self.collection_save_timer.setSingleShot(True);self.collection_save_timer.setInterval(180);self.collection_save_timer.timeout.connect(self.save_collection_current)
        self.category_save_timer=QTimer(self);self.category_save_timer.setSingleShot(True);self.category_save_timer.setInterval(420);self.category_save_timer.timeout.connect(self.save_category_current)
        self.marker_timer=QTimer(self);self.marker_timer.setInterval(3500);self.marker_timer.timeout.connect(self.refresh_change_markers)
        self.preview_watchdog=QTimer(self);self.preview_watchdog.setInterval(1200);self.preview_watchdog.timeout.connect(self.ensure_preview)
        self.editor_sync_timer=QTimer(self);self.editor_sync_timer.setSingleShot(True);self.editor_sync_timer.setInterval(18);self.editor_sync_timer.timeout.connect(self.sync_preview_to_editor)
        self.preview_scroll_timer=QTimer(self);self.preview_scroll_timer.setInterval(90);self.preview_scroll_timer.timeout.connect(self.poll_preview_scroll)
        self.preview_refresh_timer=QTimer(self);self.preview_refresh_timer.setSingleShot(True);self.preview_refresh_timer.setInterval(50);self.preview_refresh_timer.timeout.connect(self.refresh_preview_fragment)
        self.sync_process=QProcess(self);configure_process(self.sync_process);self.sync_process.setProcessChannelMode(QProcess.MergedChannels);self.sync_process.finished.connect(self.auto_sync_finished)
        self.build_ui();self.reload_content();self.start_preview();self.check_environment();self.marker_timer.start();self.preview_watchdog.start();self.preview_scroll_timer.start();QTimer.singleShot(2500,self.auto_sync)
        if valid_root(ROOT):settings=read_app_settings();settings.update({'workspace':str(ROOT),'theme':self.theme});write_app_settings(settings)

    def panel(self,name):frame=QFrame();frame.setObjectName(name);return frame

    def build_ui(self):
        root=QWidget();outer=QVBoxLayout(root);outer.setContentsMargins(14,14,14,14);outer.setSpacing(10);self.setCentralWidget(root)
        top=QFrame();top.setObjectName('topbar');bar=QHBoxLayout(top);bar.setContentsMargins(16,8,12,8)
        brand=QLabel('PRISM  /  STUDIO');brand.setObjectName('wordmark');bar.addWidget(brand);self.workspace_status=QLabel('本地内容工作台');self.workspace_status.setObjectName('muted');bar.addWidget(self.workspace_status);bar.addStretch();workspace=QPushButton('选择工作区');workspace.clicked.connect(self.choose_workspace);bar.addWidget(workspace);reload_button=QPushButton('重新载入内容');reload_button.clicked.connect(self.reinitialize_content);bar.addWidget(reload_button);sync=QPushButton('同步 GitHub');sync.clicked.connect(self.sync_repository);bar.addWidget(sync);env=QPushButton('检测环境');env.clicked.connect(self.check_environment);bar.addWidget(env);self.theme_button=QPushButton();self.theme_button.clicked.connect(self.toggle_theme);bar.addWidget(self.theme_button);outer.addWidget(top)
        split=QSplitter(Qt.Horizontal);split.setChildrenCollapsible(False);outer.addWidget(split,1)

        left=self.panel('panel');lv=QVBoxLayout(left);lv.setContentsMargins(14,16,14,14);lv.setSpacing(10)
        head=QHBoxLayout();heading=QLabel('内容库');heading.setObjectName('panelTitle');self.pending_badge=QLabel('0 项未发布');self.pending_badge.setObjectName('badge');head.addWidget(heading);head.addStretch();head.addWidget(self.pending_badge);lv.addLayout(head)
        self.tree=ContentTree();self.tree.itemSelectionChanged.connect(self.select_item);self.tree.itemClicked.connect(self.expand_tree_item);self.tree.articleMoved.connect(self.apply_article_move);self.tree.orderChanged.connect(self.apply_tree_order);self.tree.dropRejected.connect(lambda message:self.statusBar().showMessage(message,3500));lv.addWidget(self.tree,1)
        create=QHBoxLayout();new_article=QPushButton('新建文章');new_article.setProperty('primary',True);new_article.clicked.connect(self.new_article);new_collection=QPushButton('新建合集');new_collection.clicked.connect(lambda:self.new_collection(True));create.addWidget(new_article);create.addWidget(new_collection);lv.addLayout(create)
        new_category=QPushButton('新建分类');new_category.clicked.connect(self.new_category_from_library);lv.addWidget(new_category)
        self.add_project_page_button=QPushButton('添加 GitHub 项目到项目页');self.add_project_page_button.setToolTip('粘贴 GitHub 仓库地址即可创建本地项目快照');self.add_project_page_button.clicked.connect(lambda:self.add_project(False));lv.addWidget(self.add_project_page_button)
        trash_actions=QHBoxLayout();delete=QPushButton('移到废纸篓');delete.setProperty('danger',True);delete.clicked.connect(self.delete_article);open_trash=QPushButton('打开废纸篓');open_trash.clicked.connect(self.open_trash);trash_actions.addWidget(delete);trash_actions.addWidget(open_trash);lv.addLayout(trash_actions)
        self.change_detail=QLabel('选择文章后，这里会显示尚未发布的变更。');self.change_detail.setObjectName('changeDetail');self.change_detail.setWordWrap(True);lv.addWidget(self.change_detail);split.addWidget(left)

        middle=self.panel('panel');mv=QVBoxLayout(middle);mv.setContentsMargins(18,16,18,14);mv.setSpacing(10)
        editor_head=QHBoxLayout();self.current_title=QLabel('请选择一篇文章');self.current_title.setObjectName('panelTitle');self.save_state=QLabel('等待编辑');self.save_state.setObjectName('muted');self.focus_button=QPushButton('专注写作');self.focus_button.clicked.connect(self.toggle_focus_mode);editor_head.addWidget(self.current_title);editor_head.addStretch();editor_head.addWidget(self.save_state);editor_head.addWidget(self.focus_button);mv.addLayout(editor_head)
        self.tabs=QTabWidget();self.tabs.setMinimumHeight(235);self.form_scroll=QScrollArea();self.form_scroll.setObjectName('formScroll');self.form_scroll.viewport().setObjectName('formViewport');self.form_scroll.setWidgetResizable(True);self.form_scroll.setFrameShape(QFrame.NoFrame);self.form_surface=QWidget();self.form_surface.setObjectName('formSurface');layout=QFormLayout(self.form_surface);layout.setContentsMargins(12,14,12,12);layout.setSpacing(11);layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.title_field=QLineEdit();layout.addRow('标题',self.title_field)
        self.description=QTextEdit();self.description.setMinimumHeight(92);self.description.setPlaceholderText('用两到三句话概括文章内容，这段文字会用于列表与搜索摘要。');layout.addRow('摘要',self.description)
        self.category_box=QWidget();category_box_layout=QVBoxLayout(self.category_box);category_box_layout.setContentsMargins(0,0,0,0);category_box_layout.setSpacing(5);category_row=QHBoxLayout();category_row.setContentsMargins(0,0,0,0);self.category=QComboBox();self.category.setEditable(False);add_category=QPushButton('新建');add_category.setProperty('compact',True);add_category.clicked.connect(self.add_category);manage_category=QPushButton('管理');manage_category.setProperty('compact',True);manage_category.clicked.connect(self.manage_categories);category_row.addWidget(self.category,1);category_row.addWidget(add_category);category_row.addWidget(manage_category);category_box_layout.addLayout(category_row);self.category_hint=QLabel('从已有分类中选择，或新建、重命名和删除分类。');self.category_hint.setObjectName('muted');self.category_hint.setWordWrap(True);category_box_layout.addWidget(self.category_hint);layout.addRow('分类',self.category_box)
        collection_row=QHBoxLayout();self.collection=QComboBox();add_collection=QPushButton('新建');add_collection.setProperty('compact',True);add_collection.clicked.connect(lambda:self.new_collection(False));collection_row.addWidget(self.collection,1);collection_row.addWidget(add_collection);layout.addRow('合集',collection_row)
        self.order=QSpinBox();self.order.setRange(0,9999);self.order.setSpecialValueText('散篇 / 自动');layout.addRow('章节顺序',self.order)
        self.tags=TagPicker();layout.addRow('标签池',self.tags)
        cover_row=QHBoxLayout();self.cover=QLineEdit();self.cover.setReadOnly(True);cover_choose=QPushButton('选择并裁切');cover_choose.clicked.connect(self.choose_cover);cover_clear=QPushButton('清除');cover_clear.setProperty('compact',True);cover_clear.clicked.connect(lambda:self.cover.clear());cover_row.addWidget(self.cover,1);cover_row.addWidget(cover_choose);cover_row.addWidget(cover_clear);layout.addRow('封面',cover_row)
        self.cover_alt=QLineEdit();self.cover_alt.setPlaceholderText('描述封面画面，供无障碍阅读使用');layout.addRow('封面替代文本',self.cover_alt)
        self.date=QDateEdit();self.date.setCalendarPopup(True);self.date.setDate(date.today());layout.addRow('发布日期',self.date);self.canonical=QLineEdit();layout.addRow('Canonical URL',self.canonical)
        checks=QHBoxLayout();self.draft=QCheckBox('草稿');self.featured=QCheckBox('首页推荐');checks.addWidget(self.draft);checks.addWidget(self.featured);checks.addStretch();layout.addRow('状态',checks)
        reading_options=QWidget();reading_options_layout=QVBoxLayout(reading_options);reading_options_layout.setContentsMargins(0,0,0,0);reading_options_layout.setSpacing(2)
        self.auto_numbering=QCheckBox('自动编号章节（第 1 章 / §1.1 / §1.1.1）');self.auto_numbering.setChecked(True)
        self.show_contents=QCheckBox('显示文章开头目录');self.show_contents.setChecked(True)
        self.show_side_toc=QCheckBox('显示随文侧边目录');self.show_side_toc.setChecked(True)
        reading_options_layout.addWidget(self.auto_numbering);reading_options_layout.addWidget(self.show_contents);reading_options_layout.addWidget(self.show_side_toc)
        reading_hint=QLabel('三项可独立设置；旧文章缺少字段时也会按全部开启显示。');reading_hint.setObjectName('muted');reading_hint.setWordWrap(True);reading_options_layout.addWidget(reading_hint);layout.addRow('阅读结构',reading_options)
        self.form_scroll.setWidget(self.form_surface);self.tabs.addTab(self.form_scroll,'文章信息')
        self.project_form_scroll=QScrollArea();self.project_form_scroll.setObjectName('formScroll');self.project_form_scroll.viewport().setObjectName('formViewport');self.project_form_scroll.setWidgetResizable(True);self.project_form_scroll.setFrameShape(QFrame.NoFrame);self.project_form_surface=QWidget();self.project_form_surface.setObjectName('formSurface');project_layout=QFormLayout(self.project_form_surface);project_layout.setContentsMargins(12,14,12,12);project_layout.setSpacing(11);project_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.project_repo=QLineEdit();self.project_repo.setReadOnly(True);project_layout.addRow('GitHub 仓库',self.project_repo)
        self.project_title_field=QLineEdit();project_layout.addRow('项目名称',self.project_title_field)
        self.project_description=QTextEdit();self.project_description.setMinimumHeight(110);self.project_description.setPlaceholderText('项目页卡片中显示的摘要。');project_layout.addRow('项目简介',self.project_description)
        self.project_topics=TagPicker();project_layout.addRow('项目标签',self.project_topics)
        self.project_homepage=QLineEdit();self.project_homepage.setPlaceholderText('https://…');project_layout.addRow('项目主页',self.project_homepage)
        self.project_cover=QLineEdit();self.project_cover.setPlaceholderText('可选：/images/project-cover.webp');project_layout.addRow('项目封面',self.project_cover)
        self.project_cover_alt=QLineEdit();self.project_cover_alt.setPlaceholderText('描述项目封面，供无障碍阅读使用');project_layout.addRow('封面替代文本',self.project_cover_alt)
        project_flags=QHBoxLayout();self.project_featured=QCheckBox('重点项目');self.project_order=QSpinBox();self.project_order.setRange(1,9999);self.project_order.setPrefix('列表序号 ');self.project_order.setReadOnly(True);self.project_order.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons);self.project_order.setToolTip('项目顺序由左侧项目列表拖动决定');project_flags.addWidget(self.project_featured);project_flags.addWidget(self.project_order);project_flags.addStretch();project_layout.addRow('展示设置',project_flags)
        self.project_readonly=QLabel('GitHub 的语言、Stars、Forks 和许可证会在重新导入项目时刷新；这里编辑的是网站展示内容。');self.project_readonly.setObjectName('muted');self.project_readonly.setWordWrap(True);project_layout.addRow('',self.project_readonly)
        project_actions=QHBoxLayout();self.delete_project_button=QPushButton('删除当前项目快照');self.delete_project_button.setProperty('danger',True);self.delete_project_button.clicked.connect(self.delete_project);project_actions.addWidget(self.delete_project_button);project_actions.addStretch();project_layout.addRow('危险操作',project_actions)
        self.project_form_scroll.setWidget(self.project_form_surface);self.tabs.addTab(self.project_form_scroll,'项目信息');self.tabs.setTabVisible(1,False)
        self.collection_form_scroll=QScrollArea();self.collection_form_scroll.setObjectName('formScroll');self.collection_form_scroll.viewport().setObjectName('formViewport');self.collection_form_scroll.setWidgetResizable(True);self.collection_form_scroll.setFrameShape(QFrame.NoFrame);self.collection_form_surface=QWidget();self.collection_form_surface.setObjectName('formSurface');collection_layout=QFormLayout(self.collection_form_surface);collection_layout.setContentsMargins(12,14,12,12);collection_layout.setSpacing(11);collection_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.collection_title_field=QLineEdit();collection_layout.addRow('合集名称',self.collection_title_field);self.collection_description=QTextEdit();self.collection_description.setMinimumHeight(100);collection_layout.addRow('合集简介',self.collection_description);self.collection_subtitle=QLineEdit();collection_layout.addRow('副标题',self.collection_subtitle);self.collection_volume=QLineEdit();collection_layout.addRow('卷号',self.collection_volume);self.collection_status=QComboBox();self.collection_status.addItem('连载中','ongoing');self.collection_status.addItem('已完成','complete');self.collection_status.addItem('暂停更新','paused');collection_layout.addRow('状态',self.collection_status);self.collection_featured=QCheckBox('重点合集');collection_layout.addRow('展示',self.collection_featured);self.collection_order_hint=QLabel('合集和章节的顺序由左侧内容库决定；直接拖动即可调整。');self.collection_order_hint.setObjectName('muted');self.collection_order_hint.setWordWrap(True);collection_layout.addRow('排序',self.collection_order_hint);self.collection_form_scroll.setWidget(self.collection_form_surface);self.tabs.addTab(self.collection_form_scroll,'合集信息');self.tabs.setTabVisible(2,False)
        self.category_form_scroll=QScrollArea();self.category_form_scroll.setObjectName('formScroll');self.category_form_scroll.viewport().setObjectName('formViewport');self.category_form_scroll.setWidgetResizable(True);self.category_form_scroll.setFrameShape(QFrame.NoFrame);self.category_form_surface=QWidget();self.category_form_surface.setObjectName('formSurface');category_info_layout=QFormLayout(self.category_form_surface);category_info_layout.setContentsMargins(12,14,12,12);category_info_layout.setSpacing(11);category_info_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow);self.category_name_field=QLineEdit();category_info_layout.addRow('分类名称',self.category_name_field);self.category_count=QLabel('0 篇文章');category_info_layout.addRow('当前内容',self.category_count);self.category_info_hint=QLabel('修改名称会自动迁移该分类中的全部散篇；“未分类”是系统保留位置。');self.category_info_hint.setObjectName('muted');self.category_info_hint.setWordWrap(True);category_info_layout.addRow('说明',self.category_info_hint);self.category_form_scroll.setWidget(self.category_form_surface);self.tabs.addTab(self.category_form_scroll,'分类信息');self.tabs.setTabVisible(3,False)
        self.editor=StableMarkdownEditor();self.editor.setObjectName('markdownEditor');self.editor.setMinimumHeight(350);font=QFont('SF Mono',13);font.setStyleHint(QFont.Monospace);self.editor.setFont(font);self.editor.setPlaceholderText('在这里开始写作…')
        self.editor.cursorPositionChanged.connect(self.schedule_cursor_sync);self.editor.verticalScrollBar().valueChanged.connect(self.schedule_editor_scroll_sync)
        self.editor.compositionCommitted.connect(self.schedule_save);self.editor.compositionCommitted.connect(self.schedule_cursor_sync)
        self.editor_split=QSplitter(Qt.Vertical);self.editor_split.setChildrenCollapsible(False);self.editor_split.addWidget(self.tabs);self.editor_split.addWidget(self.editor);self.editor_split.setSizes([285,590]);mv.addWidget(self.editor_split,1)
        tools=QHBoxLayout();self.image_button=QPushButton('插入图片');self.image_button.clicked.connect(self.insert_images);self.project_button=QPushButton('插入项目卡片到文章');self.project_button.clicked.connect(lambda:self.add_project(True));tools.addWidget(self.image_button);tools.addWidget(self.project_button);tools.addStretch();mv.addLayout(tools);split.addWidget(middle)

        right=self.panel('panel');rv=QVBoxLayout(right);rv.setContentsMargins(14,16,14,14);rv.setSpacing(10)
        preview_head=QHBoxLayout();preview_title=QLabel('实时成品');preview_title.setObjectName('panelTitle');self.preview_status=QLabel('正在启动预览…');self.preview_status.setObjectName('liveStatus');self.preview_size=QComboBox();self.preview_size.addItems(['桌面','平板','手机']);self.preview_size.currentIndexChanged.connect(self.resize_preview);preview_head.addWidget(preview_title);preview_head.addWidget(self.preview_status);preview_head.addStretch();preview_head.addWidget(self.preview_size);rv.addLayout(preview_head)
        preview_nav=QHBoxLayout();preview_nav.setSpacing(5)
        for label,path in [('首页','/'),('合集','/blog/'),('分类','/categories/'),('归档','/archive/'),('项目','/projects/')]:
            button=QPushButton(label);button.setProperty('compact',True);button.setToolTip(f'在右侧预览{label}页面');button.clicked.connect(lambda _checked=False,target=path:self.open_preview_page(target));preview_nav.addWidget(button)
        preview_nav.addStretch();rv.addLayout(preview_nav)
        self.preview_frame=QFrame();self.preview_frame.setObjectName('previewFrame');pv=QVBoxLayout(self.preview_frame);pv.setContentsMargins(0,0,0,0);self.preview=QWebEngineView();self.preview_interceptor=StablePreviewInterceptor(self);self.preview.page().profile().setUrlRequestInterceptor(self.preview_interceptor);self.preview_channel=QWebChannel(self.preview.page());self.preview_bridge=PreviewScrollBridge(self);self.preview_channel.registerObject('prismBridge',self.preview_bridge);self.preview.page().setWebChannel(self.preview_channel);self.preview.loadFinished.connect(self.preview_loaded);pv.addWidget(self.preview);rv.addWidget(self.preview_frame,1)
        self.console_tabs=QTabWidget();self.log=QPlainTextEdit();self.log.setReadOnly(True);self.log.setMaximumBlockCount(500);self.console_tabs.addTab(self.log,'运行日志');self.console_tabs.setMaximumHeight(150);rv.addWidget(self.console_tabs)
        publish=QHBoxLayout();self.publish_current=QPushButton('发布当前文章');self.publish_current.clicked.connect(lambda:self.publish(False));self.publish_all=QPushButton('发布全部变更');self.publish_all.setProperty('primary',True);self.publish_all.clicked.connect(lambda:self.publish(True));publish.addWidget(self.publish_current);publish.addWidget(self.publish_all);rv.addLayout(publish);split.addWidget(right);split.setSizes([300,620,650])

        for signal_object in [self.title_field.textChanged,self.description.textChanged,self.category.currentTextChanged,self.collection.currentIndexChanged,self.order.valueChanged,self.tags.changed,self.cover.textChanged,self.cover_alt.textChanged,self.date.dateChanged,self.canonical.textChanged,self.draft.toggled,self.featured.toggled,self.editor.textChanged]:signal_object.connect(self.schedule_save)
        for signal_object in [self.auto_numbering.toggled,self.show_contents.toggled,self.show_side_toc.toggled]:signal_object.connect(self.schedule_display_save)
        for signal_object in [self.project_title_field.textChanged,self.project_description.textChanged,self.project_topics.changed,self.project_homepage.textChanged,self.project_cover.textChanged,self.project_cover_alt.textChanged,self.project_featured.toggled,self.project_order.valueChanged]:signal_object.connect(self.schedule_project_save)
        for signal_object in [self.collection_title_field.textChanged,self.collection_description.textChanged,self.collection_subtitle.textChanged,self.collection_volume.textChanged,self.collection_status.currentIndexChanged,self.collection_featured.toggled]:signal_object.connect(self.schedule_collection_save)
        self.category_name_field.editingFinished.connect(self.schedule_category_save)
        self.collection.currentIndexChanged.connect(self.update_category_availability)
        self.apply_theme()

    def theme_colors(self):
        if self.theme=='dark':return {'bg':'#141412','surface':'#1f1f1b','surface2':'#292823','input':'#25241f','text':'#f0ede5','muted':'#aaa59b','border':'#47443d','hover':'#34322c','pressed':'#403d35','selected':'#403a32','button':'#292823','primary':'#f0ede5','on_primary':'#171713','danger':'#ef7765','danger_border':'#805047','badge':'#302d27','live_bg':'#18352c','live':'#8bd4b7','preview':'#090908','scroll':'#5b574e'}
        return {'bg':'#dedbd3','surface':'#f7f5ef','surface2':'#eeeae2','input':'#fffefa','text':'#171713','muted':'#6f6b63','border':'#cbc7bc','hover':'#ece7dd','pressed':'#ddd6c9','selected':'#dfd9cc','button':'#fdfcf8','primary':'#171713','on_primary':'#fffefa','danger':'#a6382b','danger_border':'#d5a59d','badge':'#e9e5dc','live_bg':'#e2efe8','live':'#26735d','preview':'#27251f','scroll':'#bcb7ac'}

    def stylesheet(self):
        c=self.theme_colors();arrow=str(resource_path(f"assets/chevron-{'dark' if self.theme=='dark' else 'light'}.svg"));check=str(resource_path(f"assets/check-{'dark' if self.theme=='dark' else 'light'}.svg"))
        css='''
        QMainWindow{background:$BG;color:$TEXT} QWidget{font-family:-apple-system,"Helvetica Neue";font-size:13px;color:$TEXT;background:transparent}
        #topbar,#panel{background:$SURFACE;border:1px solid $BORDER;border-radius:12px} #wordmark{font-family:"Times New Roman";font-size:15px;font-weight:700;letter-spacing:3px} #panelTitle{font-family:"Times New Roman";font-size:19px;font-weight:700}
        #muted,#previewStatus{color:$MUTED} #badge{padding:4px 9px;background:$BADGE;border-radius:9px;color:$MUTED;font-size:11px} #liveStatus{color:$LIVE;font-size:11px;padding:3px 8px;background:$LIVEBG;border-radius:8px}
        QDialog,QMessageBox,QInputDialog,QFileDialog,QCalendarWidget,QMenu{background-color:$SURFACE;color:$TEXT} QDialog QLabel,QMessageBox QLabel,QInputDialog QLabel,QFileDialog QLabel,QCalendarWidget QLabel{color:$TEXT;background:transparent} QMessageBox{min-width:420px} QMessageBox QLabel#qt_msgbox_label{min-width:300px;color:$TEXT} QMessageBox QLabel#qt_msgboxex_icon_label{background:transparent} QDialogButtonBox{background:transparent} QMenu{border:1px solid $BORDER;padding:5px} QMenu::item{min-height:28px;padding:4px 22px 4px 10px;border-radius:5px;color:$TEXT} QMenu::item:selected{background:$SELECTED;color:$TEXT} QCalendarWidget QWidget#qt_calendar_navigationbar{background:$SURFACE2} QCalendarWidget QToolButton{color:$TEXT;background:$BUTTON;border:1px solid $BORDER;border-radius:6px;min-height:30px} QCalendarWidget QAbstractItemView{background:$INPUT;color:$TEXT;selection-background-color:$SELECTED;selection-color:$TEXT}
        QScrollArea#formScroll,QWidget#formViewport,QWidget#formSurface{background-color:$SURFACE;color:$TEXT} QTabWidget::pane{border:1px solid $BORDER;border-radius:8px;background:$SURFACE}
        QTreeWidget,QPlainTextEdit,QTextEdit,QLineEdit,QDateEdit,QSpinBox,QComboBox,QListWidget{background:$INPUT;color:$TEXT;border:1px solid $BORDER;border-radius:8px;padding:7px;selection-background-color:$SELECTED;selection-color:$TEXT}
        QLabel,QCheckBox,QRadioButton,QGroupBox{color:$TEXT} QCheckBox{min-height:32px;spacing:9px} QCheckBox::indicator{width:17px;height:17px;border:1px solid $BORDER;border-radius:4px;background:$INPUT} QCheckBox::indicator:unchecked:hover{border:2px solid $TEXT;background:$HOVER} QCheckBox::indicator:checked{image:url("$CHECK");background:$PRIMARY;border:1px solid $PRIMARY} QCheckBox::indicator:checked:hover{border:2px solid $PRIMARY} QCheckBox::indicator:disabled{background:$SURFACE2;border-color:$BORDER} QLineEdit:read-only{background:$SURFACE2;color:$MUTED} QTreeWidget{padding:7px} QTreeWidget::item{min-height:29px;border-radius:6px;padding:2px 5px} QTreeWidget::item:hover{background:$HOVER} QTreeWidget::item:selected{background:$SELECTED;color:$TEXT}
        QComboBox{padding-right:34px;min-height:25px} QComboBox::drop-down{subcontrol-origin:padding;subcontrol-position:top right;width:30px;border-left:1px solid $BORDER;border-top-right-radius:7px;border-bottom-right-radius:7px;background:$SURFACE2} QComboBox::drop-down:hover{background:$HOVER} QComboBox::down-arrow{image:url("$ARROW");width:12px;height:8px} QComboBox QAbstractItemView{background:$INPUT;color:$TEXT;border:1px solid $BORDER;outline:0;padding:5px;selection-background-color:$SELECTED;selection-color:$TEXT}
        #markdownEditor{padding:18px;font-size:14px;line-height:1.5;background:$INPUT} #tagPool::item{min-height:25px} QTabBar::tab{padding:8px 14px;color:$MUTED;background:transparent} QTabBar::tab:selected{color:$TEXT;border-bottom:2px solid #c84a38}
        QPushButton{min-height:36px;padding:4px 12px;border:1px solid $BORDER;border-radius:8px;background:$BUTTON;color:$TEXT} QPushButton:hover{background:$HOVER} QPushButton:pressed{background:$PRESSED} QPushButton[primary="true"]{background:$PRIMARY;color:$ONPRIMARY;border-color:$PRIMARY;font-weight:600} QPushButton[danger="true"]{color:$DANGER;border-color:$DANGERBORDER} QPushButton[compact="true"]{min-height:30px;padding:2px 9px} QPushButton:disabled{color:$MUTED;background:$SURFACE2;border-color:$BORDER}
        #changeDetail{padding:10px;background:$SURFACE2;border-radius:8px;color:$MUTED;font-size:11px} #previewFrame{background:$PREVIEW;border:1px solid $BORDER;border-radius:10px;padding:6px} QSplitter::handle{background:transparent;width:9px;height:9px} QSplitter::handle:hover{background:$BORDER;border-radius:3px}
        QScrollBar:vertical{width:9px;background:transparent} QScrollBar::handle:vertical{background:$SCROLL;border-radius:4px;min-height:30px} QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0} QToolTip{background:$TEXT;color:$INPUT;border:0;padding:6px}
        '''
        replacements={'$BG':c['bg'],'$SURFACE2':c['surface2'],'$SURFACE':c['surface'],'$INPUT':c['input'],'$TEXT':c['text'],'$MUTED':c['muted'],'$BORDER':c['border'],'$HOVER':c['hover'],'$PRESSED':c['pressed'],'$SELECTED':c['selected'],'$BUTTON':c['button'],'$PRIMARY':c['primary'],'$ONPRIMARY':c['on_primary'],'$DANGERBORDER':c['danger_border'],'$DANGER':c['danger'],'$BADGE':c['badge'],'$LIVEBG':c['live_bg'],'$LIVE':c['live'],'$PREVIEW':c['preview'],'$SCROLL':c['scroll'],'$ARROW':arrow,'$CHECK':check}
        for token,value in replacements.items():css=css.replace(token,value)
        return css

    def apply_theme(self):
        c=self.theme_colors();palette=QPalette()
        for group in (QPalette.Active,QPalette.Inactive):
            for role,value in ((QPalette.Window,c['bg']),(QPalette.WindowText,c['text']),(QPalette.Base,c['input']),(QPalette.AlternateBase,c['surface2']),(QPalette.Text,c['text']),(QPalette.Button,c['button']),(QPalette.ButtonText,c['text']),(QPalette.Highlight,c['selected']),(QPalette.HighlightedText,c['text']),(QPalette.ToolTipBase,c['surface2']),(QPalette.ToolTipText,c['text']),(QPalette.PlaceholderText,c['muted']),(QPalette.Link,c['live']),(QPalette.BrightText,c['danger'])):palette.setColor(group,role,QColor(value))
        for role,value in ((QPalette.Window,c['bg']),(QPalette.WindowText,c['muted']),(QPalette.Base,c['surface2']),(QPalette.Text,c['muted']),(QPalette.Button,c['surface2']),(QPalette.ButtonText,c['muted']),(QPalette.PlaceholderText,c['muted'])):palette.setColor(QPalette.Disabled,role,QColor(value))
        application=QApplication.instance();application.setPalette(palette);application.setStyleSheet(self.stylesheet());surface_palette=self.form_surface.palette();surface_palette.setColor(QPalette.Window,QColor(c['surface']));surface_palette.setColor(QPalette.Base,QColor(c['surface']));self.form_surface.setPalette(surface_palette);self.form_surface.setAutoFillBackground(True);self.form_scroll.viewport().setPalette(surface_palette);self.form_scroll.viewport().setAutoFillBackground(True);self.project_form_surface.setPalette(surface_palette);self.project_form_surface.setAutoFillBackground(True);self.project_form_scroll.viewport().setPalette(surface_palette);self.project_form_scroll.viewport().setAutoFillBackground(True);self.collection_form_surface.setPalette(surface_palette);self.collection_form_surface.setAutoFillBackground(True);self.collection_form_scroll.viewport().setPalette(surface_palette);self.collection_form_scroll.viewport().setAutoFillBackground(True);self.category_form_surface.setPalette(surface_palette);self.category_form_surface.setAutoFillBackground(True);self.category_form_scroll.viewport().setPalette(surface_palette);self.category_form_scroll.viewport().setAutoFillBackground(True);self.theme_button.setText('浅色模式' if self.theme=='dark' else '深色模式');self.sync_preview_theme()

    def toggle_theme(self):
        self.theme='dark' if self.theme=='light' else 'light';settings=read_app_settings();settings.update({'theme':self.theme,'workspace':str(ROOT)});write_app_settings(settings);self.apply_theme()

    def sync_preview_theme(self):
        if not hasattr(self,'preview') or self.preview.url().host()!='127.0.0.1':return
        theme=json.dumps(self.theme);self.preview.page().runJavaScript(f"localStorage.setItem('prism-theme',{theme});document.documentElement.dataset.theme={theme};document.documentElement.style.colorScheme={theme};window.dispatchEvent(new CustomEvent('prism-theme-change',{{detail:{{theme:{theme}}}}}));")

    def toggle_focus_mode(self):
        visible=self.tabs.isVisible();self.tabs.setVisible(not visible);self.focus_button.setText('显示文章信息' if visible else '专注写作');self.editor.setFocus()

    def schedule_save(self,*_):
        if not self.loading and self.current_file:
            self.cancel_preview_request();self.preview_patch_generation+=1;self.document_dirty=True;self.preview_scroll_suppressed_until=time.monotonic()+.12;self.save_state.setText('正在编辑 · 即将实时同步');self.mark_selected_pending('文章内容已修改，正在保存并同步预览…')
            if self.editor.composing:self.save_timer.stop()
            else:self.save_timer.start()

    def schedule_display_save(self,*_):
        self.schedule_save()
        if not self.loading and self.current_file and not self.editor.composing:self.save_timer.start(45)

    def mark_selected_pending(self,message):
        item=self.tree.currentItem() if hasattr(self,'tree') else None
        if item and item.data(0,ROLE_KIND) in {'article','project','collection'}:
            label=item.text(0)
            if not label.startswith('●  '):item.setText(0,'●  '+label)
            item.setForeground(0,QColor(self.theme_colors()['danger']))
        known=len(self.changes)+len(self.collection_changes)+len(self.project_changes)
        self.pending_badge.setText(f'至少 {max(1,known)} 项未上传');self.pending_badge.setStyleSheet('color:#a6382b');self.change_detail.setText('● 尚未上传 · '+message)

    def reload_content(self):
        selected=str(self.selected_path or self.current_file) if (self.selected_path or self.current_file) else None;self.catalog=content_catalog(ROOT);self.loading=True
        current_collection=self.collection.currentData() if hasattr(self,'collection') else ''
        self.collection.clear();self.collection.addItem('不加入合集','')
        for item in self.catalog['collections']:self.collection.addItem(item['title'],item['id'])
        index=self.collection.findData(current_collection);self.collection.setCurrentIndex(max(0,index))
        current_category=self.category.currentText() if hasattr(self,'category') else '';self.category.clear();self.category.addItems(self.catalog['categories']);index=self.category.findText(current_category);self.category.setCurrentIndex(max(0,index));self.loading=False;self.update_category_availability();self.load_tree(selected);self.refresh_change_markers()

    def article_item(self,article):
        changed=self.changes.get(article['slug']);text=('●  ' if changed else '')+article['title'];item=QTreeWidgetItem([text]);item.setData(0,ROLE_KIND,'article');item.setData(0,ROLE_PATH,str(article['path']));item.setData(0,ROLE_COLLECTION,article.get('collection') or '')
        flags=item.flags()|Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsDragEnabled
        item.setFlags(flags)
        if changed:
            item.setForeground(0,QColor(self.theme_colors()['danger']));item.setToolTip(0,f"未发布：{changed['status']} · +{changed['added']} / -{changed['deleted']}\n"+'\n'.join(changed['files']))
        return item

    def load_tree(self,selected_path=None,activate_missing=True):
        self.tree.blockSignals(True);self.tree.clear();articles=self.catalog['articles'];by_collection={c['id']:[] for c in self.catalog['collections']}
        for article in articles:
            if article.get('collection') in by_collection:by_collection[article['collection']].append(article)
        collection_root=QTreeWidgetItem(['合集']);collection_root.setData(0,ROLE_KIND,'collections-root');collection_root.setFlags((collection_root.flags()|Qt.ItemIsDropEnabled)&~Qt.ItemIsDragEnabled);self.tree.addTopLevelItem(collection_root);collection_root.setExpanded(True)
        target_item=None
        for collection in self.catalog['collections']:
            collection_changed=self.collection_changes.get(collection['id']);parent=QTreeWidgetItem([('●  ' if collection_changed else '')+f"{collection['title']}  ·  {len(by_collection[collection['id']])} 篇"]);parent.setData(0,ROLE_KIND,'collection');parent.setData(0,ROLE_COLLECTION,collection['id']);parent.setData(0,ROLE_PATH,str(collection['path']));parent.setFlags(parent.flags()|Qt.ItemIsDropEnabled|Qt.ItemIsDragEnabled);collection_root.addChild(parent);parent.setExpanded(True)
            if selected_path==parent.data(0,ROLE_PATH):target_item=parent
            if collection_changed:parent.setForeground(0,QColor(self.theme_colors()['danger']));parent.setToolTip(0,f"未发布合集：{collection_changed['status']}\n{collection_changed['file']}")
            for article in sorted(by_collection[collection['id']],key=lambda x:(x.get('order') or 9999,x['title'])):
                item=self.article_item(article);parent.addChild(item)
                if selected_path==item.data(0,ROLE_PATH):target_item=item
            parent.setExpanded(parent.childCount()>0)
        loose_root=QTreeWidgetItem(['散篇']);loose_root.setData(0,ROLE_KIND,'loose-root');loose_root.setFlags(loose_root.flags()&~Qt.ItemIsDragEnabled);self.tree.addTopLevelItem(loose_root);loose_root.setExpanded(True)
        categories={name:[] for name in self.catalog.get('categories',[]) or ['未分类']}
        for article in [a for a in articles if not a.get('collection')]:categories.setdefault(article['category'] or '未分类',[]).append(article)
        for category,items in sorted(categories.items()):
            parent=QTreeWidgetItem([f'{category}  ·  {len(items)} 篇']);parent.setData(0,ROLE_KIND,'category');parent.setData(0,ROLE_COLLECTION,category);parent.setFlags((parent.flags()|Qt.ItemIsDropEnabled)&~Qt.ItemIsDragEnabled);loose_root.addChild(parent);parent.setExpanded(True)
            for article in sorted(items,key=lambda x:x['title']):
                item=self.article_item(article);parent.addChild(item)
                if selected_path==item.data(0,ROLE_PATH):target_item=item
            parent.setExpanded(parent.childCount()>0)
        projects=QTreeWidgetItem(['项目快照']);projects.setData(0,ROLE_KIND,'projects-root');projects.setFlags((projects.flags()|Qt.ItemIsDropEnabled)&~Qt.ItemIsDragEnabled);self.tree.addTopLevelItem(projects);projects.setExpanded(True)
        for project in self.catalog.get('projects',[]):
            changed=self.project_changes.get(project['id']);item=QTreeWidgetItem([('●  ' if changed else '')+project['title']]);item.setData(0,ROLE_KIND,'project');item.setData(0,ROLE_PATH,str(project['path']));item.setFlags(item.flags()|Qt.ItemIsDragEnabled);projects.addChild(item)
            if changed:item.setForeground(0,QColor(self.theme_colors()['danger']));item.setToolTip(0,f"未上传项目：{changed['status']}\n{changed['file']}")
            if selected_path==item.data(0,ROLE_PATH):target_item=item
        if target_item:self.tree.setCurrentItem(target_item)
        self.tree.blockSignals(False);pending=len(self.changes)+len(self.collection_changes)+len(self.project_changes);self.pending_badge.setText(f'{pending} 项未上传');self.pending_badge.setStyleSheet('color:#a6382b' if pending else '')
        if target_item and activate_missing and self.loaded_view_state is None:QTimer.singleShot(0,self.select_item)

    def refresh_change_markers(self):
        if self.change_future and not self.change_future.done():self.change_refresh_queued=True;return
        self.change_refresh_queued=False
        root=ROOT;self.change_future=self.executor.submit(git_content_changes,root);QTimer.singleShot(60,lambda:self.finish_change_markers(root))

    def finish_change_markers(self,root):
        if not self.change_future or not self.change_future.done():return QTimer.singleShot(60,lambda:self.finish_change_markers(root))
        if root!=ROOT:return
        try:latest=self.change_future.result()
        except Exception as error:self.change_future=None;self.log.appendPlainText(f'读取 Git 变更失败：{error}');return
        self.change_future=None
        articles=latest['articles'];collections=latest['collections'];projects=latest.get('projects',{});self.content_change_files=latest['files']
        if articles!=self.changes or collections!=self.collection_changes or projects!=self.project_changes:
            self.changes=articles;self.collection_changes=collections;self.project_changes=projects;self.load_tree(str(self.selected_path or self.current_file) if (self.selected_path or self.current_file) else None)
        if self.change_refresh_queued:self.change_refresh_queued=False;QTimer.singleShot(0,self.refresh_change_markers)

    def check_environment(self):
        if self.environment_future and not self.environment_future.done():return
        self.workspace_status.setText('正在后台检测环境…');self.environment_future=self.executor.submit(environment_status,ROOT);QTimer.singleShot(80,self.finish_environment_check)

    def finish_environment_check(self):
        if not self.environment_future.done():return QTimer.singleShot(80,self.finish_environment_check)
        try:status=self.environment_future.result()
        except Exception as error:self.workspace_status.setText('环境检测失败');self.log.appendPlainText(str(error));return
        publish_ready=status['node'] and status['npm'] and status['git'] and status['repository'];self.gh_ready=status['gh'] and status['gh_auth'];self.project_button.setEnabled(bool(self.current_file));self.add_project_page_button.setEnabled(True);self.publish_current.setEnabled(publish_ready and bool(self.selected_path or self.current_file));self.publish_all.setEnabled(publish_ready);missing=[key for key,value in status.items() if not value]
        self.workspace_status.setText('环境就绪' if not missing else '部分功能不可用');self.log.appendPlainText('环境检查：'+('全部就绪' if not missing else '不可用：'+', '.join(missing)))
        if not status['gh_auth']:self.log.appendPlainText('gh API 认证无效：仍可点击项目导入查看修复提示；Git/SSH 发布不受影响。')

    def start_preview(self):
        if not valid_root(ROOT):self.preview_status.setText('请选择正确的博客工作区');self.workspace_status.setText('工作区不可用');return
        npm=resolve_command('npm')
        if not npm:self.preview_status.setText('缺少 npm');return
        if self.dev.state()!=QProcess.NotRunning:return
        self.preview_ready=False;self.preview_status.setText('正在启动本地预览…');self.port=find_port();self.preview_starting_until=time.monotonic()+10;self.dev.setWorkingDirectory(str(ROOT));self.dev.start(npm,['run','dev','--','--ignore-lock','--host','127.0.0.1','--port',str(self.port)]);QTimer.singleShot(180,lambda:self.wait_for_preview(0))

    def restart_preview(self,path=None):
        """Rebuild Astro's content index after adding a new collection entry."""
        if path is not None:self.preview_path=path
        self.cancel_preview_request();self.preview_navigation+=1;self.preview_patch_generation+=1;self.preview_ready=False;self.preview_loading=False;self.preview_refresh_pending=False;self.preview_status.setText('正在载入新项目预览…')
        if self.dev.state()!=QProcess.NotRunning:
            self.dev.terminate()
            if not self.dev.waitForFinished(1800):self.dev.kill();self.dev.waitForFinished(1200)
        self.start_preview()

    def handle_dev_output(self):
        output=bytes(self.dev.readAllStandardOutput()).decode(errors='replace').rstrip()
        if output:self.log.appendPlainText(output)
        match=re.search(r'https?://(?:127\.0\.0\.1|localhost):(\d+)',output)
        if match:self.port=int(match.group(1))
        pid=re.search(r'pid (\d+)',output)
        if pid and 'already running' not in output:self.server_pid=int(pid.group(1))

    def wait_for_preview(self,attempt=0):
        if self.port_open():self.preview_failures=0;self.preview_starting_until=0;self.navigate_preview();return
        if attempt<100:QTimer.singleShot(180,lambda:self.wait_for_preview(attempt+1))
        else:self.preview_status.setText('正在自动恢复…')

    def port_open(self):
        try:
            with socket.create_connection(('127.0.0.1',self.port),timeout=.08):return True
        except OSError:return False

    def ensure_preview(self):
        if self.port_open():
            self.preview_failures=0
            if not self.preview_ready and not self.preview_loading:self.navigate_preview()
            return
        self.preview_ready=False;self.preview_loading=False;self.preview_failures+=1;self.preview_status.setText('正在自动恢复…')
        if self.preview_failures>=2 and time.monotonic()>self.preview_starting_until:self.preview_failures=0;self.start_preview()

    def preview_url(self):return QUrl(f'http://127.0.0.1:{self.port}{self.preview_path}')
    def navigate_preview(self,path=None):
        if path is not None:self.preview_path=path
        self.preview_navigation+=1;self.preview_patch_generation+=1;self.preview_dom_attempts=0;token=self.preview_navigation;self.preview_ready=False;self.preview_loading=True;self.preview_status.setText('正在打开预览…');self.try_preview_navigation(token,0)

    def try_preview_navigation(self,token,attempt):
        if token!=self.preview_navigation:return
        if not self.port_open():
            if time.monotonic()>self.preview_starting_until and self.dev.state()==QProcess.NotRunning:self.start_preview()
            if attempt<80:return QTimer.singleShot(180,lambda:self.try_preview_navigation(token,attempt+1))
            self.preview_loading=False;self.preview_status.setText('预览服务连接失败 · 正在重试');return
        target=self.preview_url()
        if self.preview.url()==target and self.preview_ready:self.refresh_preview_fragment();return
        self.preview_loading=True
        if self.preview.url()==target:self.preview.reload()
        else:self.preview.setUrl(target)
        QTimer.singleShot(1800,lambda:self.verify_preview_navigation(token,attempt))

    def verify_preview_navigation(self,token,attempt):
        if token!=self.preview_navigation or self.preview_ready:return
        self.preview_loading=False
        if attempt<4:self.preview_status.setText('页面载入较慢 · 自动重试');self.try_preview_navigation(token,attempt+1)
        else:self.preview_status.setText('页面载入失败 · 点击文章重试')

    def preview_loaded(self,success):
        loaded=self.preview.url();on_local_preview=loaded.host()=='127.0.0.1' and loaded.port()==self.port
        self.preview_loading=False
        if success and on_local_preview:
            article_route=preview_route('article',self.current_file.parent.name) if self.selected_kind=='article' and self.current_file else ''
            collection_route=preview_route('collection',self.selected_path.stem) if self.selected_kind=='collection' and self.selected_path else ''
            if article_route and self.preview_path==article_route:selector='.prose';expected_version=self.preview_expected_version;expected_id=''
            elif self.selected_kind=='project' and self.preview_path=='/projects/':selector='.projects';expected_version='';expected_id=''
            elif collection_route and self.preview_path==collection_route:selector='[data-preview-kind="collection"]';expected_version=self.preview_expected_version;expected_id=self.selected_path.stem
            elif self.selected_kind=='category' and self.preview_path=='/categories/':selector='[data-preview-kind="categories"]';expected_version=self.preview_expected_version;expected_id=''
            else:selector='#main-content';expected_version='';expected_id=''
            script=f"(()=>{{const node=document.querySelector({json.dumps(selector)});if(!node)return false;const expectedVersion={json.dumps(expected_version)},expectedId={json.dumps(expected_id)};if(expectedVersion&&node.dataset.contentVersion!==expectedVersion)return false;if(expectedId&&node.dataset.previewId!==expectedId)return false;return !document.querySelector('[data-preview-kind=\"not-found\"]')}})()"
            self.preview.page().runJavaScript(script,self.confirm_preview_dom)
        elif self.port_open():QTimer.singleShot(250,lambda:self.try_preview_navigation(self.preview_navigation,0))

    def confirm_preview_dom(self,ready):
        if not ready:
            self.preview_ready=False;self.preview_loading=False;self.preview_dom_attempts+=1
            if self.preview_dom_attempts<40:self.preview_status.setText('正在等待最新页面…');QTimer.singleShot(150,lambda:self.try_preview_navigation(self.preview_navigation,0))
            else:self.preview_status.setText('预览路由尚未就绪 · 正在重建');self.restart_preview(self.preview_path)
            return
        self.preview_dom_attempts=0;self.preview_ready=True;self.preview_failures=0;self.preview_status.setText('● 稳定实时预览');self.preview.page().runJavaScript("document.querySelector('.giscus')?.replaceChildren(Object.assign(document.createElement('p'),{className:'studio-comments-note',textContent:'正式网站会在此载入 GitHub Discussions；Studio 中保留版式预览，不加载外部 iframe。'}))");self.install_preview_scroll_bridge();self.sync_preview_theme();QTimer.singleShot(35,self.complete_preview_refresh)

    def complete_preview_refresh(self):
        self.preview_refresh_timer.stop();self.preview_refresh_pending=False;self.preview_scroll_suppressed_until=time.monotonic()+.18;self.install_preview_scroll_bridge();self.schedule_cursor_sync()

    def install_preview_scroll_bridge(self):
        if self.selected_kind!='article' or not self.preview_ready:return
        script="""
        (()=>{
          if(window.__prismScrollBridgeInstalled)return;
          const connect=()=>{
            if(!window.qt?.webChannelTransport||typeof QWebChannel==='undefined')return false;
            new QWebChannel(qt.webChannelTransport,channel=>{
              const bridge=channel.objects.prismBridge;if(!bridge)return;
              let userUntil=0,frame=0;
              const markUser=()=>{userUntil=performance.now()+320};
              const report=()=>{frame=0;if(performance.now()>userUntil)return;const prose=document.querySelector('.prose');if(!prose)return;
                const selector='p[data-source-start],h1[data-source-start],h2[data-source-start],h3[data-source-start],h4[data-source-start],h5[data-source-start],h6[data-source-start],li[data-source-start],pre[data-source-start],blockquote[data-source-start],table[data-source-start],figure[data-source-start],img[data-source-start],hr[data-source-start]';
                const nodes=[...prose.querySelectorAll(selector)],anchor=innerHeight*.28;let best=null,bestDistance=Infinity;
                for(const node of nodes){const rect=node.getBoundingClientRect(),distance=anchor<rect.top?rect.top-anchor:anchor>rect.bottom?anchor-rect.bottom:0;if(distance<bestDistance){best={node,rect};bestDistance=distance}}
                if(!best)return;const start=Number(best.node.dataset.sourceStart),end=Number(best.node.dataset.sourceEnd||start),fraction=Math.max(0,Math.min(1,(anchor-best.rect.top)/Math.max(1,best.rect.height)));bridge.previewScrolled(start+fraction*Math.max(0,end-start));};
              for(const event of ['wheel','touchmove','pointerdown','pointermove','keydown'])addEventListener(event,markUser,{passive:true,capture:true});
              addEventListener('scroll',()=>{if(frame||performance.now()>userUntil)return;frame=requestAnimationFrame(report)},{passive:true});
              window.__prismScrollBridgeInstalled=true;
            });return true;
          };
          if(connect())return;const existing=document.querySelector('script[data-prism-webchannel]');if(existing)return;
          const loader=document.createElement('script');loader.src='qrc:///qtwebchannel/qwebchannel.js';loader.dataset.prismWebchannel='true';loader.onload=connect;document.head.append(loader);
        })()
        """
        self.preview.page().runJavaScript(script)

    def refresh_preview_fragment(self,attempt=0,generation=None):
        if self.selected_kind not in {'article','project','collection','category'}:return self.complete_preview_refresh()
        if self.selected_kind=='article' and not self.current_file:return self.complete_preview_refresh()
        if self.selected_kind=='collection' and not self.selected_path:return self.complete_preview_refresh()
        if not self.preview_ready or not self.port_open():
            if attempt<40:return QTimer.singleShot(120,lambda:self.refresh_preview_fragment(attempt+1,generation))
            self.preview_status.setText('预览正在自动恢复 · 当前画面保持不变');self.preview_refresh_pending=False;return
        if generation is None:self.preview_patch_generation+=1;generation=self.preview_patch_generation
        url=self.preview_url().toString()+('?' if '?' not in self.preview_url().toString() else '&')+f'__prism_patch={time.time_ns()}'
        self.cancel_preview_request();request=QNetworkRequest(QUrl(url));request.setRawHeader(b'Cache-Control',b'no-cache, no-store');request.setRawHeader(b'Pragma',b'no-cache');request.setRawHeader(b'User-Agent',b'Prism-Studio-Preview');request.setAttribute(QNetworkRequest.Attribute.CacheLoadControlAttribute,QNetworkRequest.CacheLoadControl.AlwaysNetwork)
        self.preview_status.setText('正在同步内容…');reply=self.preview_network.get(request);self.preview_reply=reply;expected_version=self.preview_expected_version;reply.finished.connect(lambda:self.finish_preview_reply(reply,attempt,generation,expected_version));QTimer.singleShot(4500,lambda:self.expire_preview_reply(reply,generation))

    def cancel_preview_request(self):
        reply=self.preview_reply
        if reply is not None and reply.isRunning():reply.abort()
        self.preview_reply=None

    def expire_preview_reply(self,reply,generation):
        if generation==self.preview_patch_generation and reply is self.preview_reply and reply.isRunning():reply.abort()

    def finish_preview_reply(self,reply,attempt,generation,expected_version):
        if reply is self.preview_reply:self.preview_reply=None
        if generation!=self.preview_patch_generation:reply.deleteLater();return
        error=reply.error();source=bytes(reply.readAll()).decode('utf-8',errors='replace');reply.deleteLater()
        if error!=QNetworkReply.NetworkError.NoError:
            if attempt<40:return QTimer.singleShot(120,lambda:self.refresh_preview_fragment(attempt+1,generation))
            self.preview_status.setText('预览正在自动恢复 · 当前画面保持不变');self.preview_refresh_pending=False;return
        expected={'article':'.prose','project':'.projects','collection':'[data-preview-kind="collection"]','category':'[data-preview-kind="categories"]'}[self.selected_kind]
        valid_source=(expected=='.prose' and 'class="prose' in source) or (expected=='.projects' and 'class="projects' in source) or (self.selected_kind=='collection' and 'data-preview-kind="collection"' in source and f'data-preview-id="{self.selected_path.stem}"' in source) or (self.selected_kind=='category' and 'data-preview-kind="categories"' in source)
        if not valid_source:
            if attempt<40:return QTimer.singleShot(120,lambda:self.refresh_preview_fragment(attempt+1,generation))
            self.preview_status.setText('预览等待最新构建 · 当前画面保持不变');self.preview_refresh_pending=False;return
        marker=f'data-content-version="{expected_version}"'
        if expected_version and marker not in source:
            self.preview_status.setText('正在等待当前版本…')
            if attempt<40:return QTimer.singleShot(90,lambda:self.refresh_preview_fragment(attempt+1,generation))
            self.preview_refresh_pending=False;self.preview_status.setText('Astro 正在整理最新内容 · 画面不会回退');return QTimer.singleShot(600,self.refresh_preview_fragment)
        encoded=json.dumps(source)
        selectors={'article':['.article-head','.book-toc','.side-toc','.prose','.article-notes','.nav-section','.related'],'project':['.page-head','.projects'],'collection':['[data-preview-kind="collection"]'],'category':['[data-preview-kind="categories"]']}[self.selected_kind]
        selector_json=json.dumps(selectors);anchor=json.dumps(expected)
        script=f"""
        (()=>{{
          try{{
            const nextDoc=new DOMParser().parseFromString({encoded},'text/html');
            const anchorSelector={anchor},oldAnchor=document.querySelector(anchorSelector),nextAnchor=nextDoc.querySelector(anchorSelector);
            if(!oldAnchor||!nextAnchor)return false;
            const oldTop=oldAnchor.getBoundingClientRect().top+scrollY,relative=scrollY-oldTop;
            let changed=0;
            const replace=(selector)=>{{
              const current=document.querySelector(selector),next=nextDoc.querySelector(selector);
              if(current&&next){{let nodeChanged=false;if(current.className!==next.className){{current.className=next.className;nodeChanged=true;}}for(const attribute of [...current.attributes])if(!next.hasAttribute(attribute.name)){{current.removeAttribute(attribute.name);nodeChanged=true;}}for(const attribute of [...next.attributes])if(current.getAttribute(attribute.name)!==attribute.value){{current.setAttribute(attribute.name,attribute.value);nodeChanged=true;}}if(current.innerHTML!==next.innerHTML){{current.replaceChildren(...[...next.childNodes].map(node=>document.importNode(node,true)));nodeChanged=true;}}if(nodeChanged)changed++;}}
              else if(current&&!next){{current.remove();changed++;}}
              else if(!current&&next){{const clone=document.importNode(next,true);if(selector==='.book-toc'||selector==='.side-toc')oldAnchor.before(clone);else oldAnchor.after(clone);changed++;}}
            }};
            {selector_json}.forEach(replace);
            document.title=nextDoc.title||document.title;
            document.querySelectorAll('.prose pre').forEach(pre=>{{if(pre.querySelector('.copy-code'))return;const button=document.createElement('button');button.className='copy-code';button.type='button';button.textContent='复制';button.addEventListener('click',async()=>{{await navigator.clipboard.writeText(pre.innerText.replace(/^复制/,''));button.textContent='已复制';setTimeout(()=>button.textContent='复制',1200)}});pre.append(button)}});
            window.__prismInitCategories?.();
            const patchedAnchor=document.querySelector(anchorSelector);if(!patchedAnchor)return false;scrollTo({{top:patchedAnchor.getBoundingClientRect().top+scrollY+relative,behavior:'instant'}});
            document.documentElement.dataset.prismPatch={json.dumps(str(generation))};
            return true;
          }}catch(error){{console.warn('Prism patch deferred',error);return false}}
        }})()
        """
        self.preview.page().runJavaScript(script,lambda applied:self.preview_fragment_applied(bool(applied),attempt,generation))

    def preview_fragment_applied(self,applied,attempt,generation):
        if generation!=self.preview_patch_generation:return
        if applied:return self.finish_preview_fragment(generation)
        if attempt<8:return QTimer.singleShot(90,lambda:self.refresh_preview_fragment(attempt+1,generation))
        self.preview_refresh_pending=False;self.preview_status.setText('预览局部更新未就绪 · 当前画面保持不变')

    def finish_preview_fragment(self,generation):
        if generation!=self.preview_patch_generation:return
        self.preview_ready=True;self.preview_status.setText('● 当前版本已同步');self.complete_preview_refresh()

    def schedule_cursor_sync(self):
        if self.loading or self.editor.composing or self.selected_kind!='article' or not self.current_file:return
        self.editor_sync_mode='cursor';self.editor_sync_timer.start()

    def schedule_editor_scroll_sync(self,*_):
        if self.loading or self.applying_preview_scroll or self.selected_kind!='article' or not self.current_file:return
        self.editor_sync_mode='scroll'
        if not self.editor_sync_timer.isActive():self.editor_sync_timer.start()

    def editor_source_line(self):
        if self.editor_sync_mode=='cursor':
            cursor=self.editor.textCursor();block=cursor.block();column=cursor.position()-block.position()
            return block.blockNumber()+1+min(.85,column/max(1,block.length()-1))
        cursor=self.editor.cursorForPosition(QPoint(4,round(self.editor.viewport().height()*.28)))
        return cursor.blockNumber()+1

    def sync_preview_to_editor(self):
        if not self.preview_ready or self.selected_kind!='article' or not self.current_file:return
        line=self.editor_source_line();fallback=max(0.0,min(1.0,(line-1)/max(1,self.editor.document().blockCount()-1)))
        self.preview_scroll_suppressed_until=time.monotonic()+.14
        script=f"""
        (()=>{{const prose=document.querySelector('.prose');if(!prose)return false;
          const line={line},fallback={fallback},selector='p[data-source-start],h1[data-source-start],h2[data-source-start],h3[data-source-start],h4[data-source-start],h5[data-source-start],h6[data-source-start],li[data-source-start],pre[data-source-start],blockquote[data-source-start],table[data-source-start],figure[data-source-start],img[data-source-start],hr[data-source-start]';
          const nodes=[...prose.querySelectorAll(selector)];let best=null,bestScore=Infinity;
          for(const node of nodes){{const start=Number(node.dataset.sourceStart),end=Number(node.dataset.sourceEnd||start);const distance=line<start?start-line:line>end?line-end:0;const score=distance*1000+(end-start);if(score<bestScore){{best={{node,start,end}};bestScore=score}}}}
          const proseRect=prose.getBoundingClientRect(),proseTop=proseRect.top+scrollY,sticky=72;
          const startY=Math.max(0,proseTop-sticky),endY=Math.max(startY,proseTop+proseRect.height-innerHeight+sticky);
          let target=startY+fallback*(endY-startY);
          if(best){{const rect=best.node.getBoundingClientRect(),top=rect.top+scrollY;const fraction=best.end>best.start?Math.max(0,Math.min(1,(line-best.start)/(best.end-best.start))):.35;target=top+rect.height*fraction-innerHeight*.28}}
          target=Math.max(startY,Math.min(endY,target));
          window.scrollTo({{top:target,behavior:'instant'}});return true}})()
        """
        self.preview.page().runJavaScript(script)

    def poll_preview_scroll(self):
        if not self.isActiveWindow() or not self.preview.isVisible() or not self.preview_owns_focus() or self.editor.hasFocus() or not self.preview_ready or self.selected_kind!='article' or not self.current_file or self.document_dirty or self.preview_refresh_pending or time.monotonic()<self.preview_scroll_suppressed_until:return
        script="""
        (()=>{const prose=document.querySelector('.prose');if(!prose)return null;
          const selector='p[data-source-start],h1[data-source-start],h2[data-source-start],h3[data-source-start],h4[data-source-start],h5[data-source-start],h6[data-source-start],li[data-source-start],pre[data-source-start],blockquote[data-source-start],table[data-source-start],figure[data-source-start],img[data-source-start],hr[data-source-start]';
          const nodes=[...prose.querySelectorAll(selector)],anchor=innerHeight*.28;let best=null,bestDistance=Infinity;
          for(const node of nodes){const rect=node.getBoundingClientRect(),distance=anchor<rect.top?rect.top-anchor:anchor>rect.bottom?anchor-rect.bottom:0;if(distance<bestDistance){best={node,rect};bestDistance=distance}}
          if(!best)return null;const start=Number(best.node.dataset.sourceStart),end=Number(best.node.dataset.sourceEnd||start);const fraction=Math.max(0,Math.min(1,(anchor-best.rect.top)/Math.max(1,best.rect.height)));return start+fraction*Math.max(0,end-start);})()
        """
        self.preview.page().runJavaScript(script,lambda line:self.apply_preview_scroll(line,True))

    def apply_preview_scroll(self,ratio,require_preview_focus=False):
        if (require_preview_focus and (not self.preview_owns_focus() or self.editor.hasFocus())) or time.monotonic()<self.preview_scroll_suppressed_until or not isinstance(ratio,(int,float)):return
        line=max(1,min(self.editor.document().blockCount(),float(ratio)));target_block=round(line)-1
        anchor_cursor=self.editor.cursorForPosition(QPoint(4,round(self.editor.viewport().height()*.28)));delta=target_block-anchor_cursor.blockNumber();bar=self.editor.verticalScrollBar()
        if not delta:return
        self.applying_preview_scroll=True;bar.setValue(bar.value()+delta);self.applying_preview_scroll=False

    def preview_owns_focus(self):
        widget=QApplication.focusWidget()
        while widget is not None:
            if widget is self.preview:return True
            widget=widget.parentWidget()
        return self.preview.hasFocus()

    def resize_preview(self,index):
        widths=[16777215,820,390];self.preview_frame.setMaximumWidth(widths[index]);self.preview_frame.setMinimumWidth(0 if index==0 else widths[index]);self.preview_frame.parentWidget().layout().setAlignment(self.preview_frame,Qt.AlignHCenter)

    def open_preview_page(self,path):
        self.preview_path=path;self.navigate_preview(path)

    def set_content_mode(self,kind):
        article=kind=='article';project=kind=='project';collection=kind=='collection';category=kind=='category'
        self.tabs.setVisible(article or project or collection or category);self.tabs.setTabVisible(0,article);self.tabs.setTabVisible(1,project);self.tabs.setTabVisible(2,collection);self.tabs.setTabVisible(3,category)
        if article:self.tabs.setCurrentIndex(0)
        elif project:self.tabs.setCurrentIndex(1)
        elif collection:self.tabs.setCurrentIndex(2)
        elif category:self.tabs.setCurrentIndex(3)
        self.editor.setVisible(article);self.image_button.setVisible(article);self.project_button.setVisible(article);self.focus_button.setVisible(article)

    def project_topic_pool(self):
        return sorted({topic for project in self.catalog.get('projects',[]) for topic in project.get('topics',[])})

    def load_project_editor(self,path):
        try:data=load_project_snapshot(path)
        except (OSError,ValueError) as error:return QMessageBox.warning(self,'无法打开项目',str(error))
        self.project_loading=True;self.project_original=dict(data);self.project_repo.setText(str(data.get('repo','')));self.project_title_field.setText(str(data.get('title','')));self.project_description.setPlainText(str(data.get('description','')));self.project_topics.set_pool(self.project_topic_pool(),data.get('topics',[]));self.project_homepage.setText(str(data.get('homepage') or ''));self.project_cover.setText(str(data.get('cover') or ''));self.project_cover_alt.setText(str(data.get('coverAlt') or ''));self.project_featured.setChecked(bool(data.get('featured',False)));self.project_order.setValue(int(data.get('order',100) or 0));self.project_loading=False;self.project_loaded_state=self.project_view_state();self.preview_expected_version=project_preview_version(data);self.set_content_mode('project')

    def project_view_state(self):
        return (self.project_title_field.text(),self.project_description.toPlainText(),tuple(self.project_topics.selected_tags()),self.project_homepage.text(),self.project_cover.text(),self.project_cover_alt.text(),self.project_featured.isChecked(),self.project_order.value())

    def schedule_project_save(self,*_):
        if self.project_loading or self.selected_kind!='project' or not self.selected_path:return
        self.cancel_preview_request();self.preview_patch_generation+=1;self.save_state.setText('正在保存项目并同步预览…');self.mark_selected_pending('项目信息已修改，正在保存并同步预览…');self.project_save_timer.start()

    def save_project_current(self):
        if self.project_loading or self.selected_kind!='project' or not self.selected_path or not self.selected_path.exists():return
        state=self.project_view_state()
        if state==self.project_loaded_state:return
        old_title=self.project_original.get('title');data=dict(self.project_original);data.update({'title':self.project_title_field.text().strip(),'description':self.project_description.toPlainText().strip(),'topics':self.project_topics.selected_tags(),'homepage':self.project_homepage.text().strip() or None,'cover':self.project_cover.text().strip() or None,'coverAlt':self.project_cover_alt.text().strip() or None,'featured':self.project_featured.isChecked(),'order':self.project_order.value()})
        if not data['title']:self.save_state.setText('项目名称不能为空');return
        try:save_project_snapshot(self.selected_path,data,ROOT)
        except OSError as error:self.save_state.setText('项目保存失败');self.statusBar().showMessage(str(error),5000);return
        self.project_original=data;self.project_loaded_state=state;self.preview_expected_version=project_preview_version(data);self.preview_refresh_pending=True;self.preview_refresh_timer.start();self.save_state.setText('● 项目已保存 · 等待上传')
        if old_title!=data['title']:self.catalog=content_catalog(ROOT);self.load_tree(str(self.selected_path))
        self.refresh_change_markers()

    def load_collection_editor(self,path):
        try:data=load_collection_snapshot(path)
        except (OSError,ValueError) as error:return QMessageBox.warning(self,'无法打开合集',str(error))
        self.collection_loading=True;self.collection_original=dict(data);self.collection_title_field.setText(str(data.get('title','')));self.collection_description.setPlainText(str(data.get('description','')));self.collection_subtitle.setText(str(data.get('subtitle') or ''));self.collection_volume.setText(str(data.get('volume') or ''));index=self.collection_status.findData(data.get('status','ongoing'));self.collection_status.setCurrentIndex(max(0,index));self.collection_featured.setChecked(bool(data.get('featured',False)));self.collection_loading=False;self.collection_loaded_state=self.collection_view_state();self.preview_expected_version=collection_preview_version(data);self.set_content_mode('collection')

    def collection_view_state(self):
        return (self.collection_title_field.text(),self.collection_description.toPlainText(),self.collection_subtitle.text(),self.collection_volume.text(),self.collection_status.currentData(),self.collection_featured.isChecked())

    def schedule_collection_save(self,*_):
        if self.collection_loading or self.selected_kind!='collection' or not self.selected_path:return
        self.cancel_preview_request();self.preview_patch_generation+=1;self.mark_selected_pending('合集信息已修改，正在保存并同步预览…');self.save_state.setText('正在保存合集信息…');self.collection_save_timer.start()

    def save_collection_current(self):
        if self.collection_loading or self.selected_kind!='collection' or not self.selected_path or not self.selected_path.exists():return
        state=self.collection_view_state()
        if state==self.collection_loaded_state:return
        data=dict(self.collection_original);data.update({'title':self.collection_title_field.text().strip(),'description':self.collection_description.toPlainText().strip(),'subtitle':self.collection_subtitle.text().strip() or None,'volume':self.collection_volume.text().strip() or None,'status':self.collection_status.currentData(),'featured':self.collection_featured.isChecked()})
        try:save_collection_snapshot(self.selected_path,data,ROOT)
        except (OSError,ValueError) as error:self.save_state.setText('合集保存失败');self.statusBar().showMessage(str(error),5000);return
        self.collection_original=data;self.collection_loaded_state=state;self.preview_expected_version=collection_preview_version(data);self.catalog=content_catalog(ROOT);self.load_tree(str(self.selected_path));self.preview_refresh_pending=True;self.preview_refresh_timer.start();self.save_state.setText('● 合集已保存 · 等待上传');self.refresh_change_markers()

    def load_category_editor(self,name,item=None):
        self.category_loading=True;self.selected_category=name;self.category_original_name=name;self.category_name_field.setText(name);count=sum(1 for article in self.catalog.get('articles',[]) if not article.get('collection') and (article.get('category') or '未分类')==name);self.category_count.setText(f'{count} 篇散篇');self.category_name_field.setReadOnly(name=='未分类');self.category_info_hint.setText('“未分类”是系统保留位置，不能重命名；可把文章拖入或拖出。' if name=='未分类' else '修改名称会自动迁移该分类中的全部散篇；也可以直接把文章拖入其他分类或合集。');self.category_loading=False;self.preview_expected_version=category_preview_version(self.catalog.get('categories',[]));self.set_content_mode('category')
        if item:item.setExpanded(True)

    def schedule_category_save(self,*_):
        if self.category_loading or self.selected_kind!='category' or not self.category_original_name or self.category_original_name=='未分类':return
        if self.category_name_field.text().strip()==self.category_original_name:return
        self.save_state.setText('正在更新分类名称…');self.category_save_timer.start(30)

    def save_category_current(self):
        if self.category_loading or self.selected_kind!='category':return
        old=self.category_original_name;new=self.category_name_field.text().strip()
        if not new or new==old:return
        try:migrate_category(ROOT,old,new)
        except (OSError,ValueError) as error:self.save_state.setText('分类更新失败');self.statusBar().showMessage(str(error),5000);return
        self.category_original_name=new;self.selected_category=new;self.catalog=content_catalog(ROOT);self.load_tree();item=self.select_tree_category(new,False);self.load_category_editor(new,item);self.preview_refresh_pending=True;self.preview_refresh_timer.start();self.save_state.setText('● 分类已重命名 · 等待上传');self.refresh_change_markers()

    def select_tree_category(self,name,notify=True):
        iterator=QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item=iterator.value()
            if item.data(0,ROLE_KIND)=='category' and item.data(0,ROLE_COLLECTION)==name:
                if not notify:self.tree.blockSignals(True)
                self.tree.setCurrentItem(item);item.setExpanded(True)
                if not notify:self.tree.blockSignals(False)
                return item
            iterator+=1

    def select_item(self):
        items=self.tree.selectedItems();item=items[0] if items else None
        if not item:return
        kind=item.data(0,ROLE_KIND)
        if kind in {'collections-root','loose-root','projects-root'}:
            if self.current_file:self.save_timer.stop();self.save_current()
            if self.selected_kind=='project':self.project_save_timer.stop();self.save_project_current()
            if self.selected_kind=='collection':self.collection_save_timer.stop();self.save_collection_current()
            if self.selected_kind=='category':self.category_save_timer.stop();self.save_category_current()
            routes={'collections-root':('/blog/','合集书架'),'loose-root':('/categories/','散篇分类'),'projects-root':('/projects/','项目页')};route,title=routes[kind]
            self.current_file=None;self.selected_path=None;self.selected_kind='';self.set_content_mode('');self.current_title.setText(title);self.save_state.setText('正在预览网站页面');self.publish_current.setEnabled(False);self.change_detail.setText('选择内容可继续编辑；也可以直接新建文章、合集或项目。');self.navigate_preview(route);return
        if kind=='category':
            if self.current_file:self.save_timer.stop();self.save_current()
            if self.selected_kind=='project':self.project_save_timer.stop();self.save_project_current()
            if self.selected_kind=='collection':self.collection_save_timer.stop();self.save_collection_current()
            if self.selected_kind=='category':self.category_save_timer.stop();self.save_category_current()
            name=item.data(0,ROLE_COLLECTION) or item.text(0).split('  ·  ')[0];self.current_file=None;self.selected_path=None;self.selected_kind='category';self.current_title.setText(f'分类 · {name}');self.save_state.setText('拖动文章即可调整归属');self.publish_current.setText('发布全部分类变更');self.publish_current.setEnabled(False);self.change_detail.setText('分类名称和文章归属会实时保存到本地，使用“发布全部变更”统一上传。');self.load_category_editor(name,item);self.navigate_preview('/categories/');return
        if kind in {'collection','project'}:
            if self.current_file:self.save_timer.stop();self.save_current()
            if self.selected_kind=='project':self.project_save_timer.stop();self.save_project_current()
            if self.selected_kind=='collection':self.collection_save_timer.stop();self.save_collection_current()
            if self.selected_kind=='category':self.category_save_timer.stop();self.save_category_current()
            path=Path(item.data(0,ROLE_PATH));self.selected_kind=kind;self.selected_path=path;identifier=item.data(0,ROLE_COLLECTION) if kind=='collection' else path.stem
            if kind=='collection':item.setExpanded(True)
            self.publish_current.setText('上传当前合集' if kind=='collection' else '上传当前项目');self.publish_current.setEnabled(path.exists());self.current_title.setText(item.text(0).replace('●  ','').split('  ·  ')[0]);self.save_state.setText('本地快照 · 可单独上传')
            changed=(self.collection_changes if kind=='collection' else self.project_changes).get(identifier);self.change_detail.setText(f"● 尚未上传 · {changed['status']}\n{changed['file']}" if changed else '✓ 当前内容与 GitHub 仓库一致。')
            self.current_file=None
            if kind=='project':self.load_project_editor(path)
            else:self.load_collection_editor(path)
            self.navigate_preview(preview_route(kind,identifier));return
        if kind!='article':return
        path=Path(item.data(0,ROLE_PATH))
        if not path.is_file():self.reload_content();QMessageBox.warning(self,'文章文件不存在',f'找不到：{path}\n\n内容库已刷新。若博客目录被移动，请点击顶部“选择工作区”。');return
        route=preview_route('article',path.parent.name)
        if self.selected_kind=='article' and self.current_file==path and self.loaded_view_state is not None:
            if self.preview_path!=route or not self.preview_ready:self.navigate_preview(route)
            return
        if self.current_file and self.current_file!=path:self.save_timer.stop();self.save_current()
        try:data,body=split_frontmatter(path.read_text('utf-8'))
        except OSError as error:QMessageBox.warning(self,'无法打开文章',f'{error}\n\n请确认工作区与文件权限。');return
        if self.selected_kind=='project':self.project_save_timer.stop();self.save_project_current()
        if self.selected_kind=='collection':self.collection_save_timer.stop();self.save_collection_current()
        if self.selected_kind=='category':self.category_save_timer.stop();self.save_category_current()
        self.current_file=path;self.selected_kind='article';self.selected_path=path;self.original_metadata=dict(data);self.original_body=body;self.loading=True;self.title_field.setText(str(data.get('title','')));self.description.setPlainText(str(data.get('description','')));category=str(data.get('category','未分类'));category_index=self.category.findText(category)
        if category_index<0:self.category.addItem(category);category_index=self.category.findText(category)
        self.category.setCurrentIndex(max(0,category_index));index=self.collection.findData(data.get('collection') or '');self.collection.setCurrentIndex(max(0,index));self.order.setValue(int(data.get('collectionOrder',0) or 0));self.tags.set_pool(self.catalog['tags'],data.get('tags',[]));self.cover.setText(str(data.get('cover','') or ''));self.cover_alt.setText(str(data.get('coverAlt','') or ''));published=data.get('publishDate',date.today());self.date.setDate(published if isinstance(published,date) else date.fromisoformat(str(published)));self.canonical.setText(str(data.get('canonical','') or ''));self.draft.setChecked(bool(data.get('draft',False)));self.featured.setChecked(bool(data.get('featured',False)));self.auto_numbering.setChecked(bool(data.get('autoNumbering',True)));self.show_contents.setChecked(bool(data.get('showContents',True)));self.show_side_toc.setChecked(bool(data.get('showSideToc',True)));self.editor.setPlainText(body);self.loading=False;self.update_category_availability()
        self.preview_expected_version=article_preview_version(data,body);self.set_content_mode('article');self.document_dirty=False;self.loaded_view_state=self.view_state();self.current_title.setText(data.get('title',path.parent.name));self.save_state.setText('草稿 · 不会出现在正式网站' if self.draft.isChecked() else '已保存到本地');self.publish_current.setText('发布当前文章' if self.draft.isChecked() else '上传当前文章');self.publish_current.setEnabled(True);self.project_button.setEnabled(True);changed=self.changes.get(path.parent.name);self.change_detail.setText(f"● 尚未上传 · {changed['status']} · 新增 {changed['added']} 行 / 删除 {changed['deleted']} 行\n"+'\n'.join(changed['files']) if changed else '✓ 当前文章与 GitHub 仓库一致，没有待上传修改。')
        settings=read_app_settings();settings.update({'workspace':str(ROOT),'theme':self.theme,'last_article':str(path)});write_app_settings(settings);self.navigate_preview(route)

    def expand_tree_item(self,item,_column=0):
        if item.data(0,ROLE_KIND) in {'collection','category','collections-root','loose-root','projects-root'} and item.childCount():item.setExpanded(True)

    def choose_workspace(self):
        global ROOT
        selected=QFileDialog.getExistingDirectory(self,'选择 Prism Notes 博客目录',str(ROOT if ROOT.exists() else Path.home()),options=QFileDialog.Option.DontUseNativeDialog)
        if not selected:return
        candidate=Path(selected)
        if not valid_root(candidate):return QMessageBox.warning(self,'不是有效的博客目录','所选目录需要包含 package.json 与 src/content/blog。')
        self.save_timer.stop();self.save_current();self.project_save_timer.stop();self.save_project_current();self.collection_save_timer.stop();self.save_collection_current();self.category_save_timer.stop();self.save_category_current();ROOT=candidate.resolve();settings=read_app_settings();settings.update({'workspace':str(ROOT),'theme':self.theme});write_app_settings(settings);self.current_file=None
        if self.dev.state()!=QProcess.NotRunning:self.dev.terminate();self.dev.waitForFinished(1500)
        self.reload_content();self.start_preview();self.check_environment();self.workspace_status.setText(f'工作区 · {ROOT.name}')

    def reinitialize_content(self):
        self.save_timer.stop();self.save_current();self.project_save_timer.stop();self.save_project_current();self.collection_save_timer.stop();self.save_collection_current();self.category_save_timer.stop();self.save_category_current();selected=str(self.selected_path or self.current_file) if (self.selected_path or self.current_file) else None
        self.loaded_view_state=None;self.project_loaded_state=None;self.collection_loaded_state=None;self.catalog=content_catalog(ROOT);self.load_tree(selected);self.refresh_change_markers()
        if self.selected_kind in {'article','project','collection'}:self.navigate_preview(self.preview_path)
        self.workspace_status.setText('内容库与本地预览已重新载入');self.statusBar().showMessage('已从当前 Git 工作区重建文章、合集和项目索引',2500)

    def metadata(self):
        collection=self.collection.currentData() or None
        data=dict(self.original_metadata);data.update({'title':self.title_field.text(),'description':self.description.toPlainText(),'publishDate':self.date.date().toString('yyyy-MM-dd'),'category':self.category.currentText().strip(),'tags':self.tags.selected_tags(),'collection':collection,'collectionOrder':self.order.value() or None if collection else None,'cover':self.cover.text() or None,'coverAlt':self.cover_alt.text() or None,'featured':self.featured.isChecked(),'draft':self.draft.isChecked(),'autoNumbering':self.auto_numbering.isChecked(),'showContents':self.show_contents.isChecked(),'showSideToc':self.show_side_toc.isChecked(),'canonical':self.canonical.text() or None});return data

    def view_state(self):
        return (self.title_field.text(),self.description.toPlainText(),self.date.date().toString('yyyy-MM-dd'),self.category.currentText().strip(),tuple(self.tags.selected_tags()),self.collection.currentData() or '',self.order.value(),self.cover.text(),self.cover_alt.text(),self.canonical.text(),self.featured.isChecked(),self.draft.isChecked(),self.auto_numbering.isChecked(),self.show_contents.isChecked(),self.show_side_toc.isChecked(),self.editor.toPlainText())

    def save_current(self):
        if not self.current_file or self.loading or not self.document_dirty:return
        current_state=self.view_state()
        if current_state==self.loaded_view_state:self.document_dirty=False;self.save_state.setText('已保存到本地');return
        data=self.metadata();body=self.editor.toPlainText();old_tree_state=(self.original_metadata.get('title'),self.original_metadata.get('category'),self.original_metadata.get('collection'),self.original_metadata.get('collectionOrder'));new_tree_state=(data.get('title'),data.get('category'),data.get('collection'),data.get('collectionOrder'))
        if not str(data.get('title','')).strip():self.save_state.setText('文章标题不能为空 · 继续输入后会自动保存');return
        if not str(data.get('description','')).strip():self.save_state.setText('文章摘要不能为空 · 继续输入后会自动保存');return
        if not data.get('tags'):self.save_state.setText('至少选择一个标签 · 补充后会自动保存');return
        if len(str(data.get('description',''))) > 180:self.save_state.setText('文章摘要不能超过 180 个字符');return
        canonical=str(data.get('canonical') or '').strip()
        if canonical:
            canonical_url=QUrl(canonical)
            if not canonical_url.isValid() or canonical_url.scheme() not in {'http','https'} or not canonical_url.host():self.save_state.setText('Canonical 需要填写完整的 http(s) 地址');return
        if semantic_value(data)==semantic_value(self.original_metadata) and body==self.original_body:self.loaded_view_state=current_state;self.document_dirty=False;self.save_state.setText('已保存到本地');return
        try:atomic_save(self.current_file,serialize_frontmatter(data,body),ROOT)
        except OSError as error:self.save_state.setText('保存失败 · 修改仍在编辑器中');self.statusBar().showMessage(str(error),5000);return
        self.original_metadata=data;self.original_body=body;self.loaded_view_state=current_state;self.document_dirty=False;self.preview_expected_version=article_preview_version(data,body);self.preview_refresh_pending=True;self.preview_scroll_suppressed_until=time.monotonic()+.22;self.preview_refresh_timer.start();self.save_state.setText('● 已保存到本地 · 等待上传');self.statusBar().showMessage('已原子保存，本地备份和预览正在更新',1200)
        if old_tree_state!=new_tree_state:self.catalog=content_catalog(ROOT);self.load_tree(str(self.current_file))
        self.refresh_change_markers()

    def update_category_availability(self,*_):
        in_collection=bool(self.collection.currentData())
        if not self.loading and self.current_file:
            previous=self.original_metadata.get('collection')
            if in_collection and self.collection.currentData()!=previous:
                collection_id=self.collection.currentData();orders=[int(article.get('order') or 0) for article in self.catalog.get('articles',[]) if article.get('collection')==collection_id];self.order.setValue(max(orders,default=0)+1)
            elif not in_collection and previous:self.order.setValue(0)
            if in_collection:
                index=self.category.findText('未分类')
                if index>=0:self.category.setCurrentIndex(index)
        self.category_box.setEnabled(not in_collection);self.order.setEnabled(in_collection)
        self.category_hint.setText('合集文章只按章节归入合集，不参与任何分类。' if in_collection else '从已有分类中选择，或新建、重命名和删除分类。')

    def add_category(self):
        if self.collection.currentData():return QMessageBox.information(self,'合集文章无分类','先将文章设为“不加入合集”，再选择分类。')
        value,ok=QInputDialog.getText(self,'新建分类','分类名称')
        if ok and value.strip():
            try:create_category(ROOT,value)
            except ValueError as error:return QMessageBox.warning(self,'无法创建分类',str(error))
            self.catalog=content_catalog(ROOT);self.category.clear();self.category.addItems(self.catalog['categories']);self.category.setCurrentIndex(self.category.findText(value.strip()));self.schedule_save();self.refresh_change_markers()

    def new_category_from_library(self):
        value,ok=QInputDialog.getText(self,'新建分类','分类名称')
        if not ok or not value.strip():return
        try:create_category(ROOT,value.strip())
        except ValueError as error:return QMessageBox.warning(self,'无法创建分类',str(error))
        self.catalog=content_catalog(ROOT);self.load_tree();self.select_tree_category(value.strip());self.refresh_change_markers();self.workspace_status.setText(f'分类“{value.strip()}”已创建 · 等待上传')

    def manage_categories(self):
        dialog=CategoryDialog(self.catalog.get('categories',[]),self)
        if dialog.exec()!=QDialog.Accepted or not dialog.action:return
        action,name=dialog.action
        if action=='rename':
            target,ok=QInputDialog.getText(self,'重命名分类',f'将“{name}”重命名为：',text=name)
            if not ok or not target.strip() or target.strip()==name:return
            task=lambda:migrate_category(ROOT,name,target.strip());success=f'分类“{name}”已重命名为“{target.strip()}”，相关文章已迁移。'
        else:
            if name=='未分类':return QMessageBox.information(self,'不能删除','“未分类”是系统保留分类。')
            if QMessageBox.question(self,'删除分类',f'确定删除“{name}”吗？\n\n所有使用该分类的文章会自动移入“未分类”；合集文章仍只属于合集。')!=QMessageBox.Yes:return
            task=lambda:delete_category(ROOT,name);success=f'分类“{name}”已删除，相关文章已移入“未分类”。'
        self.workspace_status.setText('正在更新文章分类…');future=self.executor.submit(task);QTimer.singleShot(60,lambda:self.finish_category_task(future,success))

    def finish_category_task(self,future,success):
        if not future.done():return QTimer.singleShot(60,lambda:self.finish_category_task(future,success))
        try:changed=future.result()
        except Exception as error:self.workspace_status.setText('分类更新失败');return QMessageBox.warning(self,'分类更新失败',str(error))
        self.reload_content();self.workspace_status.setText('分类已更新 · 等待发布');self.log.appendPlainText(f'{success}\n共更新 {len(changed)} 篇文章。');QMessageBox.information(self,'分类已更新',success)

    def new_article(self):
        title,ok=QInputDialog.getText(self,'新建文章','文章标题')
        if not ok or not title.strip():return
        self.workspace_status.setText('正在创建文章…');future=self.executor.submit(create_article,ROOT,title.strip());QTimer.singleShot(60,lambda:self.finish_new_article(future))

    def finish_new_article(self,future):
        if not future.done():return QTimer.singleShot(60,lambda:self.finish_new_article(future))
        try:created=future.result()
        except (OSError,ValueError,FileExistsError) as error:self.workspace_status.setText('文章创建失败');return QMessageBox.warning(self,'创建失败',str(error))
        self.log.appendPlainText(f'已创建草稿：{created.relative_to(ROOT)}');self.workspace_status.setText('新文章已创建在“未分类” · 正在准备预览');self.catalog=content_catalog(ROOT);self.load_tree(str(created),activate_missing=False);route=preview_route('article',created.parent.name);self.restart_preview(route);QTimer.singleShot(0,lambda:self.select_tree_path(created))

    def new_collection(self,open_after=True):
        dialog=CollectionDialog(self)
        if dialog.exec()!=QDialog.Accepted:return
        try:
            path=create_collection(ROOT,**dialog.values());self.catalog=content_catalog(ROOT);self.log.appendPlainText(f'合集已创建：{path.relative_to(ROOT)}');self.workspace_status.setText('合集已创建 · 正在重建预览索引')
            if open_after or not self.current_file:
                self.load_tree(str(path),activate_missing=False);route=preview_route('collection',path.stem);self.restart_preview(route);QTimer.singleShot(0,lambda:self.select_tree_path(path))
            else:
                article_path=self.current_file;self.reload_content();index=self.collection.findData(path.stem)
                if index>=0:self.collection.setCurrentIndex(index)
                self.save_timer.stop();self.save_current();self.restart_preview(preview_route('article',article_path.parent.name))
            self.refresh_change_markers()
        except (OSError,ValueError,FileExistsError) as error:QMessageBox.warning(self,'创建失败',str(error))

    def apply_article_move(self,path,destination_kind,destination_id,paths):
        article=Path(path)
        if self.current_file==article:self.save_timer.stop();self.save_current()
        try:move_article(ROOT,article,destination_kind,destination_id,[Path(item) for item in paths]);self.catalog=content_catalog(ROOT);self.load_tree(str(article));self.refresh_change_markers()
        except (OSError,ValueError) as error:QMessageBox.warning(self,'无法移动文章',str(error));self.reload_content();return
        if self.current_file==article:
            data,body=split_frontmatter(article.read_text('utf-8'));self.original_metadata=dict(data);self.original_body=body;self.loading=True;category=str(data.get('category') or '未分类');self.category.setCurrentIndex(max(0,self.category.findText(category)));self.collection.setCurrentIndex(max(0,self.collection.findData(data.get('collection') or '')));self.order.setValue(int(data.get('collectionOrder',0) or 0));self.loading=False;self.loaded_view_state=self.view_state();self.preview_expected_version=article_preview_version(data,body);self.preview_refresh_pending=True;self.preview_refresh_timer.start();self.update_category_availability()
        destination='合集' if destination_kind=='collection' else '分类';self.save_state.setText(f'● 已移动到{destination} · 等待上传');self.statusBar().showMessage(f'文章已移动到“{destination_id}”',2200)

    def apply_tree_order(self,kind,paths):
        files=[Path(path) for path in paths]
        try:
            if kind=='collection':reorder_collections(ROOT,files);message='合集书架顺序已更新'
            elif kind=='project':reorder_projects(ROOT,files);message='项目展示顺序已更新'
            else:raise ValueError('不支持的排序类型。')
        except (OSError,ValueError) as error:QMessageBox.warning(self,'无法调整顺序',str(error));self.reload_content();return
        self.catalog=content_catalog(ROOT);selected=str(self.selected_path or self.current_file) if (self.selected_path or self.current_file) else None;self.load_tree(selected)
        if kind=='project' and self.selected_kind=='project' and self.selected_path:
            data=load_project_snapshot(self.selected_path);self.project_loading=True;self.project_order.setValue(int(data.get('order',1)));self.project_loading=False;self.project_original=data;self.project_loaded_state=self.project_view_state()
        if kind=='collection' and self.selected_kind=='collection' and self.selected_path:
            self.collection_original=load_collection_snapshot(self.selected_path);self.collection_loaded_state=self.collection_view_state()
        self.refresh_change_markers();self.save_state.setText('● 列表顺序已保存 · 等待上传');self.statusBar().showMessage(message+'，等待上传',2200)

    def delete_article(self):
        if not self.current_file:return QMessageBox.information(self,'移除文章','请先选择一篇文章。')
        self.save_timer.stop();self.save_current()
        title=self.title_field.text() or self.current_file.parent.name
        if QMessageBox.question(self,'移到废纸篓',f'确定移除《{title}》吗？\n\n文章会保存在 .prism-studio/trash，可手动恢复；Git 中会标记为待发布删除。')!=QMessageBox.Yes:return
        target=trash_article(self.current_file,ROOT);self.current_file=None;self.editor.clear();self.current_title.setText('请选择一篇文章');self.reload_content();self.log.appendPlainText(f'文章已移到可恢复废纸篓：{target.relative_to(ROOT)}')

    def open_trash(self):
        dialog=TrashDialog(ROOT,self);dialog.exec()
        if dialog.changed:self.current_file=None;self.selected_path=None;self.editor.clear();self.current_title.setText('请选择一篇文章');self.reload_content();self.workspace_status.setText('废纸篓已更新 · 等待发布')

    def choose_cover(self):
        if not self.current_file:return QMessageBox.information(self,'选择封面','请先选择一篇文章。')
        name,_=QFileDialog.getOpenFileName(self,'选择封面图片','','Images (*.webp *.avif *.png *.jpg *.jpeg)',options=QFileDialog.Option.DontUseNativeDialog)
        if not name:return
        try:dialog=CoverCropDialog(Path(name),self)
        except ValueError as error:return QMessageBox.warning(self,'封面读取失败',str(error))
        if dialog.exec()!=QDialog.Accepted:return
        extension='.jpg' if Path(name).suffix.lower() in {'.jpg','.jpeg'} else '.png';target=self.current_file.parent/f'cover{extension}';image=dialog.cropped_image()
        if not image.save(str(target),quality=92):return QMessageBox.warning(self,'封面保存失败','无法写入文章资源目录。')
        self.cover.setText(f'./{target.name}')
        if not self.cover_alt.text().strip():self.cover_alt.setText(f'{self.title_field.text()}封面')
        self.schedule_save()

    def insert_images(self):
        if not self.current_file:return QMessageBox.information(self,'插入图片','请先选择一篇文章。')
        names,_=QFileDialog.getOpenFileNames(self,'选择图片','','Images (*.webp *.avif *.png *.jpg *.jpeg)',options=QFileDialog.Option.DontUseNativeDialog)
        try:
            for target in copy_images([Path(name) for name in names],self.current_file.parent):
                alt,ok=QInputDialog.getText(self,'图片替代文本',f'{target.name} 的替代文本')
                if ok and alt.strip():self.editor.insertPlainText(f'![{alt.strip()}](./{target.name})')
        except ValueError as error:QMessageBox.warning(self,'图片导入失败',str(error))

    def add_project(self,embed=False):
        if embed and not self.current_file:return QMessageBox.information(self,'请先选择文章','插入项目卡片前，请先打开一篇 Markdown/MDX 文章。')
        if self.project_future and not self.project_future.done():return QMessageBox.information(self,'正在导入','当前 GitHub 项目仍在读取中。')
        repo,ok=QInputDialog.getText(self,'导入 GitHub 项目','仓库 URL 或 owner/repo')
        if not ok or not repo.strip():return
        try:normalized=normalize_repo(repo)
        except ValueError as error:return QMessageBox.warning(self,'仓库地址无效',str(error))
        self.project_button.setEnabled(False);self.add_project_page_button.setEnabled(False);self.workspace_status.setText('正在读取 GitHub 项目…');self.log.appendPlainText(f'正在导入项目：{normalized}');self.project_future=self.executor.submit(import_project,normalized,ROOT);QTimer.singleShot(80,lambda:self.finish_project_import(normalized,embed))

    def finish_project_import(self,repo,embed):
        if not self.project_future or not self.project_future.done():return QTimer.singleShot(80,lambda:self.finish_project_import(repo,embed))
        self.project_button.setEnabled(bool(self.current_file));self.add_project_page_button.setEnabled(True)
        try:path=self.project_future.result()
        except Exception as error:self.workspace_status.setText('项目导入失败');self.log.appendPlainText(f'项目导入失败：{error}');return QMessageBox.warning(self,'项目导入失败',f'{error}\n\n请确认仓库地址可访问，并在终端执行 gh auth status -h github.com。')
        if embed:
            self.save_timer.stop();self.save_current()
            try:self.current_file=ensure_mdx_article(self.current_file,ROOT);self.selected_path=self.current_file
            except (OSError,ValueError,FileExistsError) as error:return QMessageBox.warning(self,'无法启用项目预览',str(error))
            settings=read_app_settings();settings.update({'workspace':str(ROOT),'theme':self.theme,'last_article':str(self.current_file)});write_app_settings(settings);self.editor.insertPlainText(f'\n<GitHubProject repo="{repo}" />\n');self.document_dirty=True;self.save_timer.stop();self.save_current()
        self.catalog=content_catalog(ROOT);self.selected_kind='project' if not embed else 'article';self.selected_path=path if not embed else self.current_file;self.load_tree(str(self.selected_path));self.refresh_change_markers();self.workspace_status.setText('项目已保存到本地 · 等待上传');self.log.appendPlainText(f'项目快照已保存：{path.relative_to(ROOT)}')
        if not embed:
            data=load_project_snapshot(path);self.preview_expected_version=project_preview_version(data);self.restart_preview('/projects/');QTimer.singleShot(250,lambda:self.select_tree_path(path))
        QMessageBox.information(self,'项目已添加',f'{repo} 已加入项目页的本地快照。\n\n上传后网站项目页会自动显示该项目。')

    def delete_project(self):
        if self.selected_kind!='project' or not self.selected_path:return QMessageBox.information(self,'删除项目快照','请先在左侧选择一个项目。')
        self.project_save_timer.stop();self.save_project_current();path=self.selected_path;title=self.project_title_field.text().strip() or path.stem;repo=self.project_repo.text().strip()
        if QMessageBox.question(self,'删除项目快照',f'确定删除“{title}”吗？\n\n本地将删除 {path.name}，GitHub 仓库本身不会被删除。使用“发布全部变更”后，项目才会从线上项目页移除。')!=QMessageBox.Yes:return
        try:delete_project_snapshot(path,ROOT)
        except (OSError,ValueError) as error:return QMessageBox.warning(self,'删除失败',str(error))
        self.selected_kind='';self.selected_path=None;self.current_file=None;self.project_original={};self.project_loaded_state=None;self.set_content_mode('');self.current_title.setText('请选择一项内容');self.save_state.setText('项目快照已删除 · 等待上传');self.catalog=content_catalog(ROOT);self.load_tree();self.refresh_change_markers();self.navigate_preview('/projects/');self.workspace_status.setText('项目快照已删除 · 发布全部变更后线上生效');self.log.appendPlainText(f'已删除项目快照：{path.relative_to(ROOT)}'+(f'（{repo}）' if repo else ''))

    def select_tree_path(self,path):
        iterator=QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item=iterator.value()
            if item.data(0,ROLE_PATH)==str(path):
                self.tree.blockSignals(True);self.tree.setCurrentItem(item);self.tree.blockSignals(False);self.select_item();return
            iterator+=1

    def sync_repository(self):
        git=resolve_command('git')
        if not git:return QMessageBox.warning(self,'无法同步','未找到 git。')
        if self.sync_future and not self.sync_future.done():return
        if self.content_change_files and QMessageBox.question(self,'同步前确认','本地有尚未发布的修改。Git 会保留这些修改，但远端若改到同一位置可能无法快进。仍要继续同步吗？')!=QMessageBox.Yes:return
        self.workspace_status.setText('正在后台同步 GitHub…');self.sync_future=self.executor.submit(subprocess.run,[git,'pull','--ff-only'],cwd=ROOT,capture_output=True,text=True,env=command_environment(),timeout=120);QTimer.singleShot(80,self.finish_manual_sync)

    def finish_manual_sync(self):
        if not self.sync_future or not self.sync_future.done():return QTimer.singleShot(80,self.finish_manual_sync)
        try:result=self.sync_future.result()
        except Exception as error:self.workspace_status.setText('同步失败');return QMessageBox.warning(self,'同步未完成',str(error))
        self.log.appendPlainText('$ git pull --ff-only\n'+result.stdout+result.stderr)
        if result.returncode:self.workspace_status.setText('同步未完成');return QMessageBox.warning(self,'同步未完成','无法快进同步，请查看运行日志；本地内容没有被覆盖。')
        self.workspace_status.setText('已与 GitHub 同步');self.reload_content();QMessageBox.information(self,'同步完成','本地文章、合集和项目快照已与 GitHub 仓库同步。')

    def auto_sync(self):
        git=resolve_command('git')
        if not git or self.sync_process.state()!=QProcess.NotRunning:return QTimer.singleShot(60000,self.auto_sync)
        if self.content_change_files:return QTimer.singleShot(60000,self.auto_sync)
        self.workspace_status.setText('正在检查远端更新…');self.sync_process.setWorkingDirectory(str(ROOT));self.sync_process.start(git,['pull','--ff-only'])

    def auto_sync_finished(self,code,*_):
        output=bytes(self.sync_process.readAllStandardOutput()).decode(errors='replace').strip()
        if output:self.log.appendPlainText('[自动同步] '+output)
        if code==0:self.workspace_status.setText('已与 GitHub 自动同步');self.reload_content()
        else:self.workspace_status.setText('自动同步暂不可用，本地编辑不受影响')
        QTimer.singleShot(60000,self.auto_sync)

    def publish(self,all_changes):
        if self.publish_future and not self.publish_future.done():return QMessageBox.information(self,'正在发布','当前发布任务仍在运行，可在日志区域查看状态。')
        if not all(resolve_command(key) for key in ('node','npm','git')) or not (ROOT/'.git').exists():return QMessageBox.warning(self,'环境未就绪','发布需要 Node、npm、git 和当前 Git 仓库。')
        if self.selected_kind=='article' and self.current_file and self.draft.isChecked():
            if QMessageBox.question(self,'发布草稿',f'《{self.title_field.text()}》目前是草稿。\n\n草稿可以上传到 GitHub，但正式网站会主动隐藏它。是否现在取消草稿状态并公开发布？')!=QMessageBox.Yes:return
            self.draft.setChecked(False);self.document_dirty=True
        self.save_timer.stop();self.save_current();self.project_save_timer.stop();self.save_project_current();self.collection_save_timer.stop();self.save_collection_current();self.category_save_timer.stop();self.save_category_current();message,ok=QInputDialog.getText(self,'提交说明','这次修改做了什么？',text='publish: update notes')
        if not ok or not message.strip():return
        paths=None if all_changes else self.current_publish_paths()
        if not all_changes and not paths:return QMessageBox.information(self,'没有可上传内容','请先在左侧选择文章、合集或项目。')
        scope='整个工作区' if all_changes else '\n'.join(f'• {path.relative_to(ROOT)}' for path in paths)
        if QMessageBox.question(self,'确认上传',f'将检查、构建并真正推送到 GitHub：\n\n{scope}\n\n现有暂存区中的其他文件不会混入“发布当前文章”。继续吗？')!=QMessageBox.Yes:return
        self.publish_current.setEnabled(False);self.publish_all.setEnabled(False);self.workspace_status.setText('第 1/2 步 · 正在推送 GitHub…');self.change_detail.setText('完成推送后还会继续核验 GitHub Pages 线上版本。');self.log.appendPlainText(f'\n[发布开始] {message.strip()}')
        self.publish_future=self.executor.submit(execute_publish,ROOT,paths,message.strip(),all_changes);QTimer.singleShot(100,self.finish_publish)

    def current_publish_paths(self):
        if self.selected_kind=='article' and self.current_file:return article_assets(self.current_file,ROOT)
        if self.selected_kind=='project' and self.selected_path and self.selected_path.exists():return [self.selected_path]
        if self.selected_kind=='collection' and self.selected_path and self.selected_path.exists():
            collection_id=self.selected_path.stem;paths=[self.selected_path]
            for article in self.catalog.get('articles',[]):
                if article.get('collection')==collection_id:paths.extend(article_assets(article['path'],ROOT))
            return list(dict.fromkeys(paths))
        return []

    def finish_publish(self):
        if not self.publish_future or not self.publish_future.done():return QTimer.singleShot(100,self.finish_publish)
        try:result=self.publish_future.result()
        except Exception as error:result={'success':False,'log':'','error':str(error),'stage':'exception'}
        if result.get('log'):self.log.appendPlainText(result['log'])
        self.publish_all.setEnabled(True);self.publish_current.setEnabled(bool(self.selected_path or self.current_file));self.refresh_change_markers()
        if not result.get('success'):
            self.workspace_status.setText('上传失败 · 本地内容安全');self.change_detail.setText(f"上传未完成：{result.get('error','未知错误')}")
            return QMessageBox.warning(self,'上传未完成',f"失败阶段：{result.get('stage','未知')}\n{result.get('error','请查看日志。')}\n\n本地文件不会丢失，红点会继续保留。")
        commit=result.get('commit','');settings=read_app_settings();settings.update({'workspace':str(ROOT),'theme':self.theme,'last_article':str(self.current_file) if self.current_file else '', 'last_uploaded_commit':commit});write_app_settings(settings);self.workspace_status.setText(f'第 2/2 步 · 等待 Pages 部署 {commit[:8]}');self.change_detail.setText('GitHub 已收到提交；网站尚未确认更新，请保持 Studio 开启。');self.reload_content();self.start_deployment_check(commit)

    def start_deployment_check(self,commit):
        site=pages_site_url(ROOT)
        if not site:
            self.workspace_status.setText(f'已推送 GitHub · {commit[:8]}');self.change_detail.setText('未配置站点地址，无法核验 Pages。');return QMessageBox.information(self,'GitHub 推送完成','提交已推送，但没有找到 siteConfig.site，无法继续核验线上网站。')
        self.deployment_future=self.executor.submit(wait_for_pages_deployment,site,commit);QTimer.singleShot(250,lambda:self.finish_deployment_check(commit))

    def finish_deployment_check(self,commit):
        if not self.deployment_future or not self.deployment_future.done():return QTimer.singleShot(250,lambda:self.finish_deployment_check(commit))
        try:result=self.deployment_future.result()
        except Exception as error:result={'deployed':False,'url':pages_site_url(ROOT),'error':str(error)}
        self.refresh_change_markers();self.reload_content()
        if result.get('deployed'):
            self.workspace_status.setText(f'✓ 网站已更新 · {commit[:8]}');self.change_detail.setText('✓ GitHub 提交与 Pages 线上构建完全一致。');self.preview_status.setText('● 本地与线上内容已重新载入');self.log.appendPlainText(f"[部署完成] {result.get('url')} · {commit}");return QMessageBox.information(self,'网站已经更新',f"GitHub Pages 已确认运行提交 {commit[:8]}。\n\n网站：{result.get('url')}\n本地内容库和预览索引也已重新载入。")
        self.workspace_status.setText('GitHub 已推送 · Pages 尚未确认');self.change_detail.setText(f"线上核验超时：{result.get('error','状态未知')}。提交不会丢失，可稍后再次检查网站。");QMessageBox.warning(self,'网站仍在部署',f"提交 {commit[:8]} 已在 GitHub，但 Pages 在等待时间内没有返回同一构建版本。\n\n这不再显示为“网站上传完成”；请查看 Actions，或稍后重新打开网站。")

    def closeEvent(self,event:QCloseEvent):
        self.save_timer.stop();self.save_current();self.project_save_timer.stop();self.save_project_current();self.collection_save_timer.stop();self.save_collection_current();self.category_save_timer.stop();self.save_category_current();self.cancel_preview_request();self.preview_watchdog.stop();self.preview_scroll_timer.stop();self.preview_refresh_timer.stop();self.sync_process.terminate();self.sync_process.waitForFinished(600);self.dev.terminate();self.dev.waitForFinished(1300);self.executor.shutdown(wait=False,cancel_futures=True)
        if self.server_pid:
            try:os.kill(self.server_pid,signal.SIGTERM)
            except ProcessLookupError:pass
        event.accept()


if __name__=='__main__':
    app=QApplication(sys.argv);app.setStyle('Fusion');app.setWindowIcon(QIcon(str(resource_path('assets/prism-studio-icon.png'))));window=Studio();window.show();sys.exit(app.exec())
