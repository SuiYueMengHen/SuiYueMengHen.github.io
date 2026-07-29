from __future__ import annotations

import os
import re
import signal
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from PySide6.QtCore import QProcess, QRect, QTimer, QUrl, Qt, Signal
from PySide6.QtGui import QCloseEvent, QColor, QFont, QIcon, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QFileDialog, QFormLayout, QFrame, QHBoxLayout, QInputDialog, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy, QSlider, QSpinBox,
    QSplitter, QStackedWidget, QTabWidget, QTextEdit, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

from core import (
    article_assets, atomic_save, content_catalog, copy_images, create_collection,
    environment_status, find_port, git_article_changes, import_project,
    publish_commands, reorder_collection, resolve_command, serialize_frontmatter,
    split_frontmatter, trash_article,
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
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / relative


ROOT = discover_root()
ROLE_KIND, ROLE_PATH, ROLE_COLLECTION = Qt.UserRole, Qt.UserRole + 1, Qt.UserRole + 2


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
        self.list.blockSignals(True);self.list.clear();all_tags=sorted(set(pool)|set(selected))
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
        form=QFormLayout(self);form.setSpacing(12);self.title=QLineEdit();self.slug=QLineEdit();self.description=QTextEdit();self.description.setMinimumHeight(100);self.subtitle=QLineEdit();self.volume=QLineEdit();self.order=QSpinBox();self.order.setRange(0,9999);self.order.setSpecialValueText('自动');self.status=QComboBox();self.status.addItem('连载中','ongoing');self.status.addItem('已完结','complete');self.status.addItem('暂停','paused');self.featured=QCheckBox('在书架中突出显示')
        for label,widget in [('标题 *',self.title),('Slug（留空自动生成）',self.slug),('简介 *',self.description),('副标题',self.subtitle),('卷号',self.volume),('书架顺序',self.order),('状态',self.status),('',self.featured)]:form.addRow(label,widget)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);buttons.button(QDialogButtonBox.Ok).setText('创建合集');buttons.button(QDialogButtonBox.Cancel).setText('取消');buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);form.addRow(buttons)

    def values(self):
        return {'title':self.title.text(),'slug':self.slug.text(),'description':self.description.toPlainText(),'subtitle':self.subtitle.text(),'volume':self.volume.text(),'order':self.order.value() or None,'status':self.status.currentData(),'featured':self.featured.isChecked()}

    def accept(self):
        if not self.title.text().strip() or not self.description.toPlainText().strip():
            QMessageBox.warning(self,'信息不完整','合集标题和简介不能为空。');(self.title if not self.title.text().strip() else self.description).setFocus();return
        super().accept()


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
    reordered = Signal(str, list)

    def __init__(self):
        super().__init__();self.setHeaderHidden(True);self.setIndentation(16);self.setAnimated(True);self.setDragDropMode(QTreeWidget.InternalMove);self.setDefaultDropAction(Qt.MoveAction);self.setSelectionMode(QTreeWidget.SingleSelection)

    def dropEvent(self,event):
        dragged=self.currentItem();old_parent=dragged.parent() if dragged else None;target=self.itemAt(event.position().toPoint());target_parent=target.parent() if target and target.data(0,ROLE_KIND)=='article' else target
        valid=dragged and dragged.data(0,ROLE_KIND)=='article' and old_parent and old_parent.data(0,ROLE_KIND)=='collection' and target_parent is old_parent
        if not valid:event.ignore();return
        super().dropEvent(event);paths=[Path(old_parent.child(i).data(0,ROLE_PATH)) for i in range(old_parent.childCount())];self.reordered.emit(old_parent.data(0,ROLE_COLLECTION),paths)


class Studio(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('Prism Studio');self.setWindowIcon(QIcon(str(resource_path('assets/prism-studio-icon.png'))));self.resize(1580,960);self.setMinimumSize(1180,760)
        self.current_file:Path|None=None;self.original_metadata={};self.loaded_view_state=None;self.loading=False;self.document_dirty=False;self.catalog={};self.changes={};self.preview_path='/';self.preview_ready=False;self.preview_failures=0;self.server_pid=None;self.executor=ThreadPoolExecutor(max_workers=2,thread_name_prefix='prism-studio');self.environment_future=None;self.port=find_port();self.dev=QProcess(self);self.dev.setProcessChannelMode(QProcess.MergedChannels);self.dev.readyReadStandardOutput.connect(self.handle_dev_output);self.dev.finished.connect(lambda *_:QTimer.singleShot(700,self.ensure_preview))
        self.save_timer=QTimer(self);self.save_timer.setSingleShot(True);self.save_timer.setInterval(180);self.save_timer.timeout.connect(self.save_current)
        self.marker_timer=QTimer(self);self.marker_timer.setInterval(2200);self.marker_timer.timeout.connect(self.refresh_change_markers)
        self.preview_watchdog=QTimer(self);self.preview_watchdog.setInterval(1200);self.preview_watchdog.timeout.connect(self.ensure_preview)
        self.sync_process=QProcess(self);self.sync_process.setProcessChannelMode(QProcess.MergedChannels);self.sync_process.finished.connect(self.auto_sync_finished)
        self.build_ui();self.reload_content();self.start_preview();self.check_environment();self.marker_timer.start();self.preview_watchdog.start();QTimer.singleShot(2500,self.auto_sync)

    def panel(self,name):frame=QFrame();frame.setObjectName(name);return frame

    def build_ui(self):
        root=QWidget();outer=QVBoxLayout(root);outer.setContentsMargins(14,14,14,14);outer.setSpacing(10);self.setCentralWidget(root)
        top=QFrame();top.setObjectName('topbar');bar=QHBoxLayout(top);bar.setContentsMargins(16,8,12,8)
        brand=QLabel('PRISM  /  STUDIO');brand.setObjectName('wordmark');bar.addWidget(brand);self.workspace_status=QLabel('本地内容工作台');self.workspace_status.setObjectName('muted');bar.addWidget(self.workspace_status);bar.addStretch();sync=QPushButton('同步 GitHub');sync.clicked.connect(self.sync_repository);bar.addWidget(sync);env=QPushButton('检测环境');env.clicked.connect(self.check_environment);bar.addWidget(env);outer.addWidget(top)
        split=QSplitter(Qt.Horizontal);split.setChildrenCollapsible(False);outer.addWidget(split,1)

        left=self.panel('panel');lv=QVBoxLayout(left);lv.setContentsMargins(14,16,14,14);lv.setSpacing(10)
        head=QHBoxLayout();heading=QLabel('内容库');heading.setObjectName('panelTitle');self.pending_badge=QLabel('0 项未发布');self.pending_badge.setObjectName('badge');head.addWidget(heading);head.addStretch();head.addWidget(self.pending_badge);lv.addLayout(head)
        self.tree=ContentTree();self.tree.itemSelectionChanged.connect(self.select_item);self.tree.reordered.connect(self.apply_reorder);lv.addWidget(self.tree,1)
        create=QHBoxLayout();new_article=QPushButton('新建文章');new_article.setProperty('primary',True);new_article.clicked.connect(self.new_article);new_collection=QPushButton('新建合集');new_collection.clicked.connect(self.new_collection);create.addWidget(new_article);create.addWidget(new_collection);lv.addLayout(create)
        delete=QPushButton('移到废纸篓');delete.setProperty('danger',True);delete.clicked.connect(self.delete_article);lv.addWidget(delete)
        self.change_detail=QLabel('选择文章后，这里会显示尚未发布的变更。');self.change_detail.setObjectName('changeDetail');self.change_detail.setWordWrap(True);lv.addWidget(self.change_detail);split.addWidget(left)

        middle=self.panel('panel');mv=QVBoxLayout(middle);mv.setContentsMargins(18,16,18,14);mv.setSpacing(10)
        editor_head=QHBoxLayout();self.current_title=QLabel('请选择一篇文章');self.current_title.setObjectName('panelTitle');self.save_state=QLabel('等待编辑');self.save_state.setObjectName('muted');editor_head.addWidget(self.current_title);editor_head.addStretch();editor_head.addWidget(self.save_state);mv.addLayout(editor_head)
        self.tabs=QTabWidget();form_scroll=QScrollArea();form_scroll.setWidgetResizable(True);form_scroll.setFrameShape(QFrame.NoFrame);form=QWidget();layout=QFormLayout(form);layout.setContentsMargins(12,14,12,12);layout.setSpacing(11);layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.title_field=QLineEdit();layout.addRow('标题',self.title_field)
        self.description=QTextEdit();self.description.setMinimumHeight(92);self.description.setPlaceholderText('用两到三句话概括文章内容，这段文字会用于列表与搜索摘要。');layout.addRow('摘要',self.description)
        category_row=QHBoxLayout();self.category=QComboBox();self.category.setEditable(True);self.category.setInsertPolicy(QComboBox.NoInsert);add_category=QPushButton('新建');add_category.setProperty('compact',True);add_category.clicked.connect(self.add_category);category_row.addWidget(self.category,1);category_row.addWidget(add_category);layout.addRow('分类',category_row)
        collection_row=QHBoxLayout();self.collection=QComboBox();add_collection=QPushButton('新建');add_collection.setProperty('compact',True);add_collection.clicked.connect(self.new_collection);collection_row.addWidget(self.collection,1);collection_row.addWidget(add_collection);layout.addRow('合集',collection_row)
        self.order=QSpinBox();self.order.setRange(0,9999);self.order.setSpecialValueText('散篇 / 自动');layout.addRow('章节顺序',self.order)
        self.tags=TagPicker();layout.addRow('标签池',self.tags)
        cover_row=QHBoxLayout();self.cover=QLineEdit();self.cover.setReadOnly(True);cover_choose=QPushButton('选择并裁切');cover_choose.clicked.connect(self.choose_cover);cover_clear=QPushButton('清除');cover_clear.setProperty('compact',True);cover_clear.clicked.connect(lambda:self.cover.clear());cover_row.addWidget(self.cover,1);cover_row.addWidget(cover_choose);cover_row.addWidget(cover_clear);layout.addRow('封面',cover_row)
        self.cover_alt=QLineEdit();self.cover_alt.setPlaceholderText('描述封面画面，供无障碍阅读使用');layout.addRow('封面替代文本',self.cover_alt)
        self.date=QDateEdit();self.date.setCalendarPopup(True);self.date.setDate(date.today());layout.addRow('发布日期',self.date);self.canonical=QLineEdit();layout.addRow('Canonical URL',self.canonical)
        checks=QHBoxLayout();self.draft=QCheckBox('草稿');self.featured=QCheckBox('首页推荐');checks.addWidget(self.draft);checks.addWidget(self.featured);checks.addStretch();layout.addRow('状态',checks)
        form_scroll.setWidget(form);self.tabs.addTab(form_scroll,'文章信息');mv.addWidget(self.tabs,0)
        self.editor=QPlainTextEdit();self.editor.setObjectName('markdownEditor');font=QFont('SF Mono',13);font.setStyleHint(QFont.Monospace);self.editor.setFont(font);self.editor.setPlaceholderText('在这里开始写作…');mv.addWidget(self.editor,1)
        tools=QHBoxLayout();image=QPushButton('插入图片');image.clicked.connect(self.insert_images);self.project_button=QPushButton('插入 GitHub 项目');self.project_button.clicked.connect(self.add_project);tools.addWidget(image);tools.addWidget(self.project_button);tools.addStretch();mv.addLayout(tools);split.addWidget(middle)

        right=self.panel('panel');rv=QVBoxLayout(right);rv.setContentsMargins(14,16,14,14);rv.setSpacing(10)
        preview_head=QHBoxLayout();preview_title=QLabel('实时成品');preview_title.setObjectName('panelTitle');self.preview_status=QLabel('正在启动预览…');self.preview_status.setObjectName('liveStatus');self.preview_size=QComboBox();self.preview_size.addItems(['桌面','平板','手机']);self.preview_size.currentIndexChanged.connect(self.resize_preview);preview_head.addWidget(preview_title);preview_head.addWidget(self.preview_status);preview_head.addStretch();preview_head.addWidget(self.preview_size);rv.addLayout(preview_head)
        self.preview_frame=QFrame();self.preview_frame.setObjectName('previewFrame');pv=QVBoxLayout(self.preview_frame);pv.setContentsMargins(0,0,0,0);self.preview=QWebEngineView();self.preview.loadFinished.connect(self.preview_loaded);pv.addWidget(self.preview);rv.addWidget(self.preview_frame,1)
        self.console_tabs=QTabWidget();self.log=QPlainTextEdit();self.log.setReadOnly(True);self.log.setMaximumBlockCount(500);self.console_tabs.addTab(self.log,'运行日志');self.console_tabs.setMaximumHeight(150);rv.addWidget(self.console_tabs)
        publish=QHBoxLayout();self.publish_current=QPushButton('发布当前文章');self.publish_current.clicked.connect(lambda:self.publish(False));self.publish_all=QPushButton('发布全部变更');self.publish_all.setProperty('primary',True);self.publish_all.clicked.connect(lambda:self.publish(True));publish.addWidget(self.publish_current);publish.addWidget(self.publish_all);rv.addLayout(publish);split.addWidget(right);split.setSizes([300,620,650])

        for signal_object in [self.title_field.textChanged,self.description.textChanged,self.category.currentTextChanged,self.collection.currentIndexChanged,self.order.valueChanged,self.tags.changed,self.cover.textChanged,self.cover_alt.textChanged,self.date.dateChanged,self.canonical.textChanged,self.draft.toggled,self.featured.toggled,self.editor.textChanged]:signal_object.connect(self.schedule_save)
        self.setStyleSheet(self.stylesheet())

    def stylesheet(self):
        return '''
        QMainWindow{background:#dedbd3;color:#171713} QWidget{font-family:-apple-system,"Helvetica Neue";font-size:13px;color:#171713}
        #topbar,#panel{background:#f7f5ef;border:1px solid #cbc7bc;border-radius:12px} #wordmark{font-family:"Times New Roman";font-size:15px;font-weight:700;letter-spacing:3px} #panelTitle{font-family:"Times New Roman";font-size:19px;font-weight:700}
        #muted,#previewStatus{color:#77736a} #badge{padding:4px 9px;background:#e9e5dc;border-radius:9px;color:#5e5a52;font-size:11px} #liveStatus{color:#26735d;font-size:11px;padding:3px 8px;background:#e2efe8;border-radius:8px}
        QTreeWidget,QPlainTextEdit,QTextEdit,QLineEdit,QDateEdit,QSpinBox,QComboBox,QListWidget{background:#fffefa;border:1px solid #cbc7bc;border-radius:8px;padding:6px;selection-background-color:#e7ddd0;selection-color:#171713}
        QTreeWidget{padding:7px} QTreeWidget::item{min-height:29px;border-radius:6px;padding:2px 5px} QTreeWidget::item:hover{background:#eeeae1} QTreeWidget::item:selected{background:#dfd9cc;color:#171713}
        #markdownEditor{padding:16px;font-size:14px;line-height:1.5} #tagPool::item{min-height:25px} QTabWidget::pane{border:1px solid #cbc7bc;border-radius:8px;background:#fbfaf6} QTabBar::tab{padding:8px 14px;color:#6f6b63} QTabBar::tab:selected{color:#171713;border-bottom:2px solid #c84a38}
        QPushButton{min-height:36px;padding:4px 12px;border:1px solid #aaa59a;border-radius:8px;background:#fdfcf8} QPushButton:hover{background:#ece7dd;border-color:#777168} QPushButton:pressed{background:#ddd6c9} QPushButton[primary="true"]{background:#171713;color:#fffefa;border-color:#171713;font-weight:600} QPushButton[primary="true"]:hover{background:#38362f} QPushButton[danger="true"]{color:#a6382b;border-color:#d5a59d} QPushButton[compact="true"]{min-height:30px;padding:2px 9px} QPushButton:disabled{color:#aaa69e;background:#ebe8e1;border-color:#d6d2c9}
        #changeDetail{padding:10px;background:#eeeae2;border-radius:8px;color:#625e56;font-size:11px} #previewFrame{background:#27251f;border:1px solid #b6b1a6;border-radius:10px;padding:6px} QSplitter::handle{background:transparent;width:9px}
        QScrollBar:vertical{width:9px;background:transparent} QScrollBar::handle:vertical{background:#bcb7ac;border-radius:4px;min-height:30px} QToolTip{background:#171713;color:#fffefa;border:0;padding:6px}
        '''

    def schedule_save(self,*_):
        if not self.loading and self.current_file:self.document_dirty=True;self.save_state.setText('正在编辑 · 尚未保存');self.save_timer.start()

    def reload_content(self):
        selected=str(self.current_file) if self.current_file else None;self.catalog=content_catalog(ROOT);self.changes=git_article_changes(ROOT);self.loading=True
        current_collection=self.collection.currentData() if hasattr(self,'collection') else ''
        self.collection.clear();self.collection.addItem('不加入合集','')
        for item in self.catalog['collections']:self.collection.addItem(item['title'],item['id'])
        index=self.collection.findData(current_collection);self.collection.setCurrentIndex(max(0,index))
        current_category=self.category.currentText() if hasattr(self,'category') else '';self.category.clear();self.category.addItems(self.catalog['categories']);self.category.setEditText(current_category);self.loading=False;self.load_tree(selected)

    def article_item(self,article):
        changed=self.changes.get(article['slug']);text=('●  ' if changed else '')+article['title'];item=QTreeWidgetItem([text]);item.setData(0,ROLE_KIND,'article');item.setData(0,ROLE_PATH,str(article['path']));item.setData(0,ROLE_COLLECTION,article.get('collection') or '')
        flags=item.flags()|Qt.ItemIsSelectable|Qt.ItemIsEnabled
        if article.get('collection'):flags|=Qt.ItemIsDragEnabled
        item.setFlags(flags)
        if changed:
            item.setForeground(0,QColor('#b23b2c'));item.setToolTip(0,f"未发布：{changed['status']} · +{changed['added']} / -{changed['deleted']}\n"+'\n'.join(changed['files']))
        return item

    def load_tree(self,selected_path=None):
        self.tree.blockSignals(True);self.tree.clear();articles=self.catalog['articles'];by_collection={c['id']:[] for c in self.catalog['collections']}
        for article in articles:
            if article.get('collection') in by_collection:by_collection[article['collection']].append(article)
        collection_root=QTreeWidgetItem(['合集']);collection_root.setData(0,ROLE_KIND,'root');collection_root.setFlags(collection_root.flags()&~Qt.ItemIsDragEnabled);self.tree.addTopLevelItem(collection_root);collection_root.setExpanded(True)
        target_item=None
        for collection in self.catalog['collections']:
            parent=QTreeWidgetItem([f"{collection['title']}  ·  {len(by_collection[collection['id']])} 篇"]);parent.setData(0,ROLE_KIND,'collection');parent.setData(0,ROLE_COLLECTION,collection['id']);parent.setFlags((parent.flags()|Qt.ItemIsDropEnabled)&~Qt.ItemIsDragEnabled);collection_root.addChild(parent);parent.setExpanded(True)
            for article in sorted(by_collection[collection['id']],key=lambda x:(x.get('order') or 9999,x['title'])):
                item=self.article_item(article);parent.addChild(item)
                if selected_path==item.data(0,ROLE_PATH):target_item=item
        loose_root=QTreeWidgetItem(['散篇']);loose_root.setData(0,ROLE_KIND,'root');self.tree.addTopLevelItem(loose_root);loose_root.setExpanded(True)
        categories={}
        for article in [a for a in articles if not a.get('collection')]:categories.setdefault(article['category'] or '未分类',[]).append(article)
        for category,items in sorted(categories.items()):
            parent=QTreeWidgetItem([f'{category}  ·  {len(items)} 篇']);parent.setData(0,ROLE_KIND,'category');loose_root.addChild(parent);parent.setExpanded(True)
            for article in sorted(items,key=lambda x:x['title']):
                item=self.article_item(article);parent.addChild(item)
                if selected_path==item.data(0,ROLE_PATH):target_item=item
        projects=QTreeWidgetItem(['项目快照']);projects.setData(0,ROLE_KIND,'root');self.tree.addTopLevelItem(projects)
        for file in sorted((ROOT/'src/content/projects').glob('*.yaml')):item=QTreeWidgetItem([file.stem]);item.setData(0,ROLE_KIND,'project');item.setData(0,ROLE_PATH,str(file));projects.addChild(item)
        self.tree.blockSignals(False);self.pending_badge.setText(f'{len(self.changes)} 篇未发布');self.pending_badge.setStyleSheet('color:#a6382b' if self.changes else '')
        if target_item:self.tree.setCurrentItem(target_item)

    def refresh_change_markers(self):
        latest=git_article_changes(ROOT)
        if latest!=self.changes:self.changes=latest;self.load_tree(str(self.current_file) if self.current_file else None)

    def check_environment(self):
        if self.environment_future and not self.environment_future.done():return
        self.workspace_status.setText('正在后台检测环境…');self.environment_future=self.executor.submit(environment_status,ROOT);QTimer.singleShot(80,self.finish_environment_check)

    def finish_environment_check(self):
        if not self.environment_future.done():return QTimer.singleShot(80,self.finish_environment_check)
        try:status=self.environment_future.result()
        except Exception as error:self.workspace_status.setText('环境检测失败');self.log.appendPlainText(str(error));return
        publish_ready=status['node'] and status['npm'] and status['git'] and status['repository'];self.project_button.setEnabled(status['gh'] and status['gh_auth']);self.publish_current.setEnabled(publish_ready and bool(self.current_file));self.publish_all.setEnabled(publish_ready);missing=[key for key,value in status.items() if not value]
        self.workspace_status.setText('环境就绪' if not missing else '部分功能不可用');self.log.appendPlainText('环境检查：'+('全部就绪' if not missing else '不可用：'+', '.join(missing)))
        if not status['gh_auth']:self.log.appendPlainText('gh API 认证无效：仅项目导入被禁用；Git/SSH 发布不受影响。')

    def start_preview(self):
        npm=resolve_command('npm')
        if not npm:self.preview_status.setText('缺少 npm');return
        if self.dev.state()!=QProcess.NotRunning:return
        self.preview_ready=False;self.preview_status.setText('正在自动连接…');self.port=find_port();self.dev.setWorkingDirectory(str(ROOT));self.dev.start(npm,['run','dev','--','--host','127.0.0.1','--port',str(self.port)]);QTimer.singleShot(180,lambda:self.wait_for_preview(0))

    def handle_dev_output(self):
        output=bytes(self.dev.readAllStandardOutput()).decode(errors='replace').rstrip()
        if output:self.log.appendPlainText(output)
        match=re.search(r'https?://(?:127\.0\.0\.1|localhost):(\d+)',output)
        if match:self.port=int(match.group(1))
        pid=re.search(r'pid (\d+)',output)
        if pid and 'already running' not in output:self.server_pid=int(pid.group(1))

    def wait_for_preview(self,attempt=0):
        if self.port_open():self.preview_ready=True;self.preview_failures=0;self.preview_status.setText('● 实时连接');self.preview.setUrl(self.preview_url());return
        if attempt<100 and self.dev.state()!=QProcess.NotRunning:QTimer.singleShot(180,lambda:self.wait_for_preview(attempt+1))
        else:self.preview_status.setText('正在自动恢复…')

    def port_open(self):
        try:
            with socket.create_connection(('127.0.0.1',self.port),timeout=.08):return True
        except OSError:return False

    def ensure_preview(self):
        if self.port_open():
            self.preview_failures=0
            if not self.preview_ready:self.preview_ready=True;self.preview_status.setText('● 已自动重连');self.preview.setUrl(self.preview_url())
            return
        self.preview_ready=False;self.preview_failures+=1;self.preview_status.setText('正在自动恢复…')
        if self.preview_failures>=2:
            if self.dev.state()!=QProcess.NotRunning:self.dev.terminate();self.dev.waitForFinished(900)
            self.preview_failures=0;self.start_preview()

    def preview_url(self):return QUrl(f'http://127.0.0.1:{self.port}{self.preview_path}')
    def preview_loaded(self,success):
        if success:self.preview_ready=True;self.preview_status.setText('● 实时连接')
        elif self.port_open():QTimer.singleShot(250,lambda:self.preview.setUrl(self.preview_url()))

    def resize_preview(self,index):
        widths=[16777215,820,390];self.preview_frame.setMaximumWidth(widths[index]);self.preview_frame.setMinimumWidth(0 if index==0 else widths[index]);self.preview_frame.parentWidget().layout().setAlignment(self.preview_frame,Qt.AlignHCenter)

    def select_item(self):
        items=self.tree.selectedItems();item=items[0] if items else None
        if not item or item.data(0,ROLE_KIND)!='article':return
        path=Path(item.data(0,ROLE_PATH))
        if self.current_file and self.current_file!=path:self.save_timer.stop();self.save_current()
        data,body=split_frontmatter(path.read_text('utf-8'));self.current_file=path;self.original_metadata=dict(data);self.loading=True;self.title_field.setText(str(data.get('title','')));self.description.setPlainText(str(data.get('description','')));self.category.setEditText(str(data.get('category','')));index=self.collection.findData(data.get('collection') or '');self.collection.setCurrentIndex(max(0,index));self.order.setValue(int(data.get('collectionOrder',0) or 0));self.tags.set_pool(self.catalog['tags'],data.get('tags',[]));self.cover.setText(str(data.get('cover','') or ''));self.cover_alt.setText(str(data.get('coverAlt','') or ''));published=data.get('publishDate',date.today());self.date.setDate(published if isinstance(published,date) else date.fromisoformat(str(published)));self.canonical.setText(str(data.get('canonical','') or ''));self.draft.setChecked(bool(data.get('draft',False)));self.featured.setChecked(bool(data.get('featured',False)));self.editor.setPlainText(body);self.loading=False
        self.document_dirty=False;self.loaded_view_state=self.view_state();self.current_title.setText(data.get('title',path.parent.name));self.save_state.setText('已保存到本地');self.preview_path=f'/blog/{path.parent.name}/';self.publish_current.setEnabled(True);changed=self.changes.get(path.parent.name);self.change_detail.setText(f"● 尚未发布 · {changed['status']} · 新增 {changed['added']} 行 / 删除 {changed['deleted']} 行\n"+'\n'.join(changed['files']) if changed else '✓ 当前文章与 Git 仓库一致，没有未发布修改。')
        if self.preview_ready:self.preview.setUrl(self.preview_url())

    def metadata(self):
        collection=self.collection.currentData() or None
        data=dict(self.original_metadata);data.update({'title':self.title_field.text(),'description':self.description.toPlainText(),'publishDate':self.date.date().toString('yyyy-MM-dd'),'category':self.category.currentText().strip(),'tags':self.tags.selected_tags(),'collection':collection,'collectionOrder':self.order.value() or None if collection else None,'cover':self.cover.text() or None,'coverAlt':self.cover_alt.text() or None,'featured':self.featured.isChecked(),'draft':self.draft.isChecked(),'canonical':self.canonical.text() or None});return data

    def view_state(self):
        return (self.title_field.text(),self.description.toPlainText(),self.date.date().toString('yyyy-MM-dd'),self.category.currentText().strip(),tuple(self.tags.selected_tags()),self.collection.currentData() or '',self.order.value(),self.cover.text(),self.cover_alt.text(),self.canonical.text(),self.featured.isChecked(),self.draft.isChecked(),self.editor.toPlainText())

    def save_current(self):
        if not self.current_file or self.loading or not self.document_dirty:return
        current_state=self.view_state()
        if current_state==self.loaded_view_state:self.document_dirty=False;self.save_state.setText('已保存到本地');return
        data=self.metadata();atomic_save(self.current_file,serialize_frontmatter(data,self.editor.toPlainText()),ROOT);self.original_metadata=data;self.loaded_view_state=current_state;self.document_dirty=False;self.save_state.setText('● 已保存 · 等待发布');self.statusBar().showMessage('本地已保存，网站预览正在实时更新',1200);self.catalog=content_catalog(ROOT);self.refresh_change_markers()

    def add_category(self):
        value,ok=QInputDialog.getText(self,'新建分类','分类名称')
        if ok and value.strip():
            if self.category.findText(value.strip())<0:self.category.addItem(value.strip())
            self.category.setEditText(value.strip())

    def new_article(self):
        title,ok=QInputDialog.getText(self,'新建文章','文章标题')
        if not ok or not title.strip():return
        npm=resolve_command('npm')
        if not npm:return QMessageBox.warning(self,'无法创建文章','未找到 npm。')
        result=subprocess.run([npm,'run','post:new','--','--title',title.strip()],cwd=ROOT,capture_output=True,text=True);self.log.appendPlainText(result.stdout+result.stderr);self.reload_content()

    def new_collection(self):
        dialog=CollectionDialog(self)
        if dialog.exec()!=QDialog.Accepted:return
        try:
            path=create_collection(ROOT,**dialog.values());self.reload_content();index=self.collection.findData(path.stem)
            if index>=0:self.collection.setCurrentIndex(index)
            self.log.appendPlainText(f'合集已创建：{path.relative_to(ROOT)}')
        except (ValueError,FileExistsError) as error:QMessageBox.warning(self,'创建失败',str(error))

    def apply_reorder(self,collection_id,paths):
        try:reorder_collection(ROOT,collection_id,paths);self.catalog=content_catalog(ROOT);self.refresh_change_markers();self.statusBar().showMessage('合集章节顺序已更新，等待发布',2200)
        except ValueError as error:QMessageBox.warning(self,'无法调整顺序',str(error));self.reload_content()

    def delete_article(self):
        if not self.current_file:return QMessageBox.information(self,'移除文章','请先选择一篇文章。')
        self.save_timer.stop();self.save_current()
        title=self.title_field.text() or self.current_file.parent.name
        if QMessageBox.question(self,'移到废纸篓',f'确定移除《{title}》吗？\n\n文章会保存在 .prism-studio/trash，可手动恢复；Git 中会标记为待发布删除。')!=QMessageBox.Yes:return
        target=trash_article(self.current_file,ROOT);self.current_file=None;self.editor.clear();self.current_title.setText('请选择一篇文章');self.reload_content();self.log.appendPlainText(f'文章已移到可恢复废纸篓：{target.relative_to(ROOT)}')

    def choose_cover(self):
        if not self.current_file:return QMessageBox.information(self,'选择封面','请先选择一篇文章。')
        name,_=QFileDialog.getOpenFileName(self,'选择封面图片','','Images (*.webp *.avif *.png *.jpg *.jpeg)')
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
        names,_=QFileDialog.getOpenFileNames(self,'选择图片','','Images (*.webp *.avif *.png *.jpg *.jpeg)')
        try:
            for target in copy_images([Path(name) for name in names],self.current_file.parent):
                alt,ok=QInputDialog.getText(self,'图片替代文本',f'{target.name} 的替代文本')
                if ok and alt.strip():self.editor.insertPlainText(f'![{alt.strip()}](./{target.name})')
        except ValueError as error:QMessageBox.warning(self,'图片导入失败',str(error))

    def add_project(self):
        repo,ok=QInputDialog.getText(self,'导入 GitHub 项目','仓库 URL 或 owner/repo')
        if not ok:return
        try:path=import_project(repo,ROOT);self.reload_content();self.editor.insertPlainText(f'\n<GitHubProject repo="{repo.strip()}" />\n');self.log.appendPlainText(f'项目快照已保存：{path.relative_to(ROOT)}')
        except Exception as error:QMessageBox.warning(self,'导入失败',str(error))

    def sync_repository(self):
        git=resolve_command('git')
        if not git:return QMessageBox.warning(self,'无法同步','未找到 git。')
        dirty=subprocess.run([git,'status','--porcelain'],cwd=ROOT,capture_output=True,text=True).stdout.strip()
        if dirty and QMessageBox.question(self,'同步前确认','本地有尚未发布的修改。Git 会保留这些修改，但远端若改到同一位置可能无法快进。仍要继续同步吗？')!=QMessageBox.Yes:return
        QApplication.setOverrideCursor(Qt.WaitCursor);result=subprocess.run([git,'pull','--ff-only'],cwd=ROOT,capture_output=True,text=True);QApplication.restoreOverrideCursor();self.log.appendPlainText('$ git pull --ff-only\n'+result.stdout+result.stderr)
        if result.returncode:return QMessageBox.warning(self,'同步未完成','无法快进同步，请查看运行日志；本地内容没有被覆盖。')
        self.reload_content();QMessageBox.information(self,'同步完成','本地文章、合集和项目快照已与 GitHub 仓库同步。')

    def auto_sync(self):
        git=resolve_command('git')
        if not git or self.sync_process.state()!=QProcess.NotRunning:return QTimer.singleShot(60000,self.auto_sync)
        dirty=subprocess.run([git,'status','--porcelain'],cwd=ROOT,capture_output=True,text=True).stdout.strip()
        if dirty:return QTimer.singleShot(60000,self.auto_sync)
        self.workspace_status.setText('正在检查远端更新…');self.sync_process.setWorkingDirectory(str(ROOT));self.sync_process.start(git,['pull','--ff-only'])

    def auto_sync_finished(self,code,*_):
        output=bytes(self.sync_process.readAllStandardOutput()).decode(errors='replace').strip()
        if output:self.log.appendPlainText('[自动同步] '+output)
        if code==0:self.workspace_status.setText('已与 GitHub 自动同步');self.reload_content()
        else:self.workspace_status.setText('自动同步暂不可用，本地编辑不受影响')
        QTimer.singleShot(60000,self.auto_sync)

    def run_command(self,command):
        resolved=resolve_command(command[0]) if command[0] in {'npm','node','git','gh'} else command[0]
        if not resolved:self.log.appendPlainText(f'未找到命令：{command[0]}');return False
        self.log.appendPlainText('$ '+' '.join(command));QApplication.processEvents();result=subprocess.run([resolved,*command[1:]],cwd=ROOT,capture_output=True,text=True);self.log.appendPlainText((result.stdout+result.stderr).rstrip());return result.returncode==0

    def publish(self,all_changes):
        status=environment_status(ROOT)
        if not all(status.get(key,False) for key in ('node','npm','git','repository')):return QMessageBox.warning(self,'环境未就绪','发布需要 Node、npm、git 和当前 Git 仓库。')
        self.save_timer.stop();self.save_current();message,ok=QInputDialog.getText(self,'提交说明','这次修改做了什么？',text='publish: update notes')
        if not ok or not message.strip():return
        paths=None if all_changes else article_assets(self.current_file,ROOT) if self.current_file else []
        for command in publish_commands(paths,message.strip(),all_changes):
            if command[:3]==['git','commit','-m']:
                git=resolve_command('git');diff=subprocess.run([git,'diff','--cached'],cwd=ROOT,capture_output=True,text=True).stdout if git else ''
                if QMessageBox.question(self,'确认发布',f'将提交以下变更：\n\n{diff[:7000]}')!=QMessageBox.Yes:return
            if not self.run_command(command):return QMessageBox.warning(self,'发布中止','命令执行失败，请查看日志。已暂存内容不会丢失。')
        self.reload_content();self.change_detail.setText('✓ 所有已提交文章都已发布，未发布标记已刷新。');QMessageBox.information(self,'发布完成','提交已推送。红点已清除，GitHub Actions 正在部署网站。')

    def closeEvent(self,event:QCloseEvent):
        self.save_timer.stop();self.save_current();self.preview_watchdog.stop();self.sync_process.terminate();self.sync_process.waitForFinished(600);self.dev.terminate();self.dev.waitForFinished(1300);self.executor.shutdown(wait=False,cancel_futures=True)
        if self.server_pid:
            try:os.kill(self.server_pid,signal.SIGTERM)
            except ProcessLookupError:pass
        event.accept()


if __name__=='__main__':
    app=QApplication(sys.argv);app.setStyle('Fusion');app.setWindowIcon(QIcon(str(resource_path('assets/prism-studio-icon.png'))));window=Studio();window.show();sys.exit(app.exec())
