import subprocess,tempfile,unittest
from pathlib import Path
from core import article_preview_version,atomic_save,article_assets,content_catalog,copy_images,create_article,create_category,create_collection,delete_category,delete_project_snapshot,delete_trash_entries,ensure_mdx_article,execute_publish,git_content_changes,import_project,list_trash,load_collection_snapshot,load_project_snapshot,migrate_category,move_article,pages_site_url,preview_route,project_preview_version,publish_commands,reorder_collection,reorder_collections,reorder_projects,restore_trash_entry,save_project_snapshot,serialize_frontmatter,split_frontmatter,trash_article,wait_for_pages_deployment

class Result:
    def __init__(self,code=0,out='',err=''):self.returncode=code;self.stdout=out;self.stderr=err

class CoreTests(unittest.TestCase):
    def test_preview_fingerprints_match_web_runtime(self):
        article={'title':'棱镜','description':'清晰','category':'写作','tags':['A','中文'],'collection':None,'collectionOrder':None,'featured':True,'draft':False,'canonical':None};project={'repo':'o/r','title':'工具','description':'说明','topics':['cli','mac'],'homepage':None,'cover':None,'coverAlt':None,'featured':False,'order':2}
        self.assertEqual(article_preview_version(article,'正文\r\n'),'246cddcc998b9d18ebd1257199f576779ddd11f39a957af0c3578b7f57c4a72e');self.assertEqual(project_preview_version(project),'6d6f99f07afa98739f4307b830b10663d9c5d75eb99aa562913b08cc4d736482')
    def test_frontmatter_roundtrip(self):
        data={'title':'棱镜','tags':['写作','工具'],'draft':True};source=serialize_frontmatter(data,'正文\n');parsed,body=split_frontmatter(source);self.assertEqual(parsed['tags'],data['tags']);self.assertEqual(body,'正文\n')
    def test_atomic_save_creates_first_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'src/content/blog/x/index.md';path.parent.mkdir(parents=True);path.write_text('old','utf-8');atomic_save(path,'new',root);atomic_save(path,'newer',root);self.assertEqual((root/'.prism-studio/backups/src/content/blog/x/index.md').read_text('utf-8'),'old');self.assertEqual(path.read_text('utf-8'),'newer')
    def test_image_collision_and_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'cover.png';source.write_bytes(b'a');article=root/'post';article.mkdir();(article/'cover.png').write_bytes(b'b');copied=copy_images([source],article);self.assertEqual(copied[0].name,'cover-2.png');index=article/'index.md';index.write_text('![封面](./cover-2.png)','utf-8');self.assertEqual(article_assets(index),[index,copied[0]])
    def test_project_embed_converts_markdown_to_mdx(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);article=root/'src/content/blog/note/index.md';article.parent.mkdir(parents=True);article.write_text('正文','utf-8');converted=ensure_mdx_article(article,root);self.assertEqual(converted.name,'index.mdx');self.assertEqual(converted.read_text('utf-8'),'正文');self.assertFalse(article.exists());self.assertEqual(ensure_mdx_article(converted,root),converted)
    def test_trash_does_not_reserve_title_but_restore_detects_conflict(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);first=create_article(root,'同名文章');trashed=trash_article(first,root);second=create_article(root,'同名文章');self.assertTrue(second.exists());self.assertEqual(list_trash(root)[0]['title'],'同名文章')
            with self.assertRaises(FileExistsError):restore_trash_entry(trashed,root)
            self.assertEqual(delete_trash_entries([trashed],root),1);self.assertEqual(list_trash(root),[])
    def test_create_article_reuses_orphan_slug_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);orphan=root/'src/content/blog/demo2';orphan.mkdir(parents=True);(orphan/'unused.png').write_bytes(b'image');created=create_article(root,'demo2');self.assertEqual(created,orphan/'index.md');self.assertTrue((orphan/'unused.png').exists())
    def test_collection_can_empty_and_refill_without_losing_articles(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);create_collection(root,'示例合集','用于测试空合集重新加入文章',slug='book');first=create_article(root,'第一篇');second=create_article(root,'第二篇')
            move_article(root,first,'collection','book',[first]);move_article(root,first,'category','未分类',[])
            self.assertEqual([item for item in content_catalog(root)['articles'] if item.get('collection')=='book'],[])
            move_article(root,first,'collection','book',[first]);move_article(root,second,'collection','book',[first,second])
            members=sorted((item for item in content_catalog(root)['articles'] if item.get('collection')=='book'),key=lambda item:item['order'])
            self.assertEqual([item['title'] for item in members],['第一篇','第二篇']);self.assertEqual([item['order'] for item in members],[1,2])
    def test_failed_project_import_preserves_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);target=root/'src/content/projects/o--r.yaml';target.parent.mkdir(parents=True);target.write_text('old','utf-8')
            def runner(command,**kwargs):return Result(0) if command[1:3]==['auth','status'] else Result(1,err='offline')
            with self.assertRaises(RuntimeError):import_project('o/r',root,runner);self.assertEqual(target.read_text('utf-8'),'old')
    def test_project_url_normalization_accepts_browser_urls(self):
        from core import normalize_repo
        self.assertEqual(normalize_repo('https://github.com/OpenAI/codex.git/?tab=readme#top'),'OpenAI/codex')
    def test_project_snapshot_edit_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'src/content/projects/o--r.yaml';data={'repo':'o/r','title':'Tool','description':'note','topics':['cli','cli',' mac '],'stars':2,'syncedAt':'2026-01-01T00:00:00Z'}
            save_project_snapshot(path,data,root);loaded=load_project_snapshot(path);self.assertEqual(loaded['topics'],['cli','mac']);self.assertEqual(loaded['stars'],2)
    def test_delete_project_snapshot_is_scoped_to_project_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);project=root/'src/content/projects/o--r.yaml';project.parent.mkdir(parents=True);project.write_text('repo: o/r\n','utf-8');self.assertEqual(delete_project_snapshot(project,root),project.resolve());self.assertFalse(project.exists())
            outside=root/'src/content/collections/book.yaml';outside.parent.mkdir(parents=True);outside.write_text('title: Book\n','utf-8')
            with self.assertRaises(ValueError):delete_project_snapshot(outside,root)
    def test_pages_deployment_waits_for_matching_commit(self):
        class Response:
            def __init__(self,commit):self.commit=commit
            def __enter__(self):return self
            def __exit__(self,*_):return False
            def read(self):return ('{"commit":"'+self.commit+'"}').encode()
        commits=iter(['old','new']);result=wait_for_pages_deployment('https://example.com','new',attempts=2,interval=0,fetcher=lambda *_args,**_kwargs:Response(next(commits)),sleeper=lambda *_:None);self.assertTrue(result['deployed'])
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);config=root/'src/config/site.ts';config.parent.mkdir(parents=True);config.write_text("export const siteConfig={site:'https://notes.example'}",'utf-8');self.assertEqual(pages_site_url(root),'https://notes.example')
    def test_publish_command_scopes_current_content(self):
        commands=publish_commands([Path('post/index.md'),Path('post/a.png')],'note',False);self.assertEqual(commands[3],['git','add','--','post/index.md','post/a.png']);self.assertEqual(commands[-2],['git','commit','--only','-m','note','--','post/index.md','post/a.png']);self.assertEqual(commands[-1],['git','push'])
    def test_publish_verifies_remote_tracking_commit(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'post/index.md';path.parent.mkdir();path.write_text('note','utf-8');commands=[]
            def runner(command,**kwargs):
                commands.append(command)
                return Result(0,out='abc123\n' if 'rev-parse' in command else (' M post/index.md\n' if 'status' in command else ''))
            result=execute_publish(root,[path],'note',False,runner);self.assertTrue(result['success']);self.assertTrue(any('--only' in command for command in commands));self.assertEqual(result['commit'],'abc123')
    def test_publish_stops_before_build_when_scope_is_clean(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'post/index.md';path.parent.mkdir();path.write_text('note','utf-8');commands=[]
            def runner(command,**kwargs):commands.append(command);return Result(0,out='')
            result=execute_publish(root,[path],'note',False,runner);self.assertFalse(result['success']);self.assertEqual(result['stage'],'preflight');self.assertEqual(len(commands),1)
    def test_preview_routes_encode_unicode_slugs(self):
        self.assertEqual(preview_route('article','中文 demo'),'/blog/%E4%B8%AD%E6%96%87%20demo/');self.assertEqual(preview_route('project','anything'),'/projects/')
    def test_create_collection_uses_next_order(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);directory=root/'src/content/collections';directory.mkdir(parents=True);(directory/'first.yaml').write_text('title: 第一卷\ndescription: 简介\norder: 2\n','utf-8')
            target=create_collection(root,'第二卷','新的简介',slug='second')
            data=target.read_text('utf-8');self.assertEqual(target.name,'second.yaml');self.assertIn('order: 3',data);self.assertIn('title: 第二卷',data)
    def test_create_collection_rejects_duplicate_slug_and_order(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);directory=root/'src/content/collections';directory.mkdir(parents=True);(directory/'book.yaml').write_text('title: 书\ndescription: 简介\norder: 1\n','utf-8')
            with self.assertRaises(FileExistsError):create_collection(root,'书','简介',slug='book')
            with self.assertRaises(ValueError):create_collection(root,'另一本','简介',slug='other',order=1)
    def test_catalog_and_drag_reorder(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'src/content/collections').mkdir(parents=True);(root/'src/content/collections/book.yaml').write_text('title: 书\ndescription: 简介\norder: 1\n','utf-8')
            files=[]
            for slug,order in [('a',2),('b',1)]:
                path=root/f'src/content/blog/{slug}/index.md';path.parent.mkdir(parents=True);path.write_text(serialize_frontmatter({'title':slug,'description':'d','publishDate':'2026-01-01','category':'方法','tags':['写作'],'collection':'book','collectionOrder':order},'正文'),encoding='utf-8');files.append(path)
            project=root/'src/content/projects/o--r.yaml';project.parent.mkdir(parents=True);project.write_text('title: Prism\nrepo: o/r\n','utf-8')
            catalog=content_catalog(root);self.assertEqual(catalog['categories'],['未分类']);self.assertEqual(catalog['tags'],['写作']);self.assertEqual(catalog['collections'][0]['id'],'book');self.assertEqual(catalog['projects'][0]['repo'],'o/r')
            reorder_collection(root,'book',files);self.assertEqual(split_frontmatter(files[0].read_text('utf-8'))[0]['collectionOrder'],1);self.assertEqual(split_frontmatter(files[1].read_text('utf-8'))[0]['collectionOrder'],2)
    def test_move_article_between_category_and_collection(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);collections=root/'src/content/collections';collections.mkdir(parents=True);(collections/'book.yaml').write_text('title: 书\ndescription: 简介\norder: 1\n','utf-8')
            first=root/'src/content/blog/a/index.md';second=root/'src/content/blog/b/index.md'
            for path,title in ((first,'甲'),(second,'乙')):path.parent.mkdir(parents=True);path.write_text(serialize_frontmatter({'title':title,'category':'未分类'},'正文'),'utf-8')
            move_article(root,first,'collection','book',[first]);data,_=split_frontmatter(first.read_text('utf-8'));self.assertEqual(data['collection'],'book');self.assertEqual(data['category'],'未分类');self.assertEqual(data['collectionOrder'],1)
            move_article(root,second,'collection','book',[first,second]);self.assertEqual(split_frontmatter(second.read_text('utf-8'))[0]['collectionOrder'],2)
            move_article(root,first,'category','技术');data,_=split_frontmatter(first.read_text('utf-8'));self.assertNotIn('collection',data);self.assertEqual(data['category'],'技术');self.assertEqual(split_frontmatter(second.read_text('utf-8'))[0]['collectionOrder'],1)
    def test_reorder_collection_and_project_lists(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);collections=root/'src/content/collections';projects=root/'src/content/projects';collections.mkdir(parents=True);projects.mkdir(parents=True)
            c1=collections/'a.yaml';c2=collections/'b.yaml';c1.write_text('title: A\ndescription: A\norder: 1\n','utf-8');c2.write_text('title: B\ndescription: B\norder: 2\n','utf-8')
            p1=projects/'a.yaml';p2=projects/'b.yaml';p1.write_text('repo: o/a\ntitle: A\ndescription: A\norder: 1\n','utf-8');p2.write_text('repo: o/b\ntitle: B\ndescription: B\norder: 2\n','utf-8')
            reorder_collections(root,[c2,c1]);self.assertEqual(load_collection_snapshot(c2)['order'],1);self.assertEqual(load_collection_snapshot(c1)['order'],2)
            reorder_projects(root,[p2,p1]);self.assertEqual(load_project_snapshot(p2)['order'],1);self.assertEqual(load_project_snapshot(p1)['order'],2)
    def test_category_create_rename_delete_migrates_articles(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);loose=root/'src/content/blog/loose/index.md';book=root/'src/content/blog/book/index.md'
            for path,collection in ((loose,None),(book,'volume')):
                path.parent.mkdir(parents=True,exist_ok=True);path.write_text(serialize_frontmatter({'title':path.parent.name,'category':'旧分类','collection':collection},'正文'),'utf-8')
            create_category(root,'空分类');self.assertIn('空分类',content_catalog(root)['categories'])
            migrate_category(root,'旧分类','新分类');self.assertEqual(split_frontmatter(loose.read_text('utf-8'))[0]['category'],'新分类');self.assertEqual(split_frontmatter(book.read_text('utf-8'))[0]['category'],'新分类')
            delete_category(root,'新分类');self.assertEqual(split_frontmatter(loose.read_text('utf-8'))[0]['category'],'未分类');self.assertNotIn('新分类',content_catalog(root)['categories'])
    def test_git_change_mapping_marks_articles_and_collections(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);article=root/'src/content/blog/note/index.md';article.parent.mkdir(parents=True);article.write_text('note','utf-8');collection=root/'src/content/collections/book.yaml';collection.parent.mkdir(parents=True);collection.write_text('title: book\n','utf-8')
            def runner(command,**kwargs):
                if 'status' in command:return Result(0,out=' M src/content/blog/note/index.md\n?? src/content/collections/book.yaml\n?? src/content/projects/o--r.yaml\n')
                return Result(0,out='3\t1\tsrc/content/blog/note/index.md\n')
            changes=git_content_changes(root,runner);self.assertEqual(changes['articles']['note']['added'],3);self.assertEqual(changes['articles']['note']['deleted'],1);self.assertEqual(changes['collections']['book']['status'],'??');self.assertEqual(changes['projects']['o--r']['status'],'??')
            target=trash_article(article,root);self.assertTrue((target/'index.md').exists());self.assertFalse(article.parent.exists())

if __name__=='__main__':unittest.main()
