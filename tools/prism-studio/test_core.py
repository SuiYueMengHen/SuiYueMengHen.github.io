import subprocess,tempfile,unittest
from pathlib import Path
from core import atomic_save,article_assets,copy_images,import_project,publish_commands,serialize_frontmatter,split_frontmatter

class Result:
    def __init__(self,code=0,out='',err=''):self.returncode=code;self.stdout=out;self.stderr=err

class CoreTests(unittest.TestCase):
    def test_frontmatter_roundtrip(self):
        data={'title':'棱镜','tags':['写作','工具'],'draft':True};source=serialize_frontmatter(data,'正文\n');parsed,body=split_frontmatter(source);self.assertEqual(parsed['tags'],data['tags']);self.assertEqual(body,'正文\n')
    def test_atomic_save_creates_first_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);path=root/'src/content/blog/x/index.md';path.parent.mkdir(parents=True);path.write_text('old','utf-8');atomic_save(path,'new',root);atomic_save(path,'newer',root);self.assertEqual((root/'.prism-studio/backups/src/content/blog/x/index.md').read_text('utf-8'),'old');self.assertEqual(path.read_text('utf-8'),'newer')
    def test_image_collision_and_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'cover.png';source.write_bytes(b'a');article=root/'post';article.mkdir();(article/'cover.png').write_bytes(b'b');copied=copy_images([source],article);self.assertEqual(copied[0].name,'cover-2.png');index=article/'index.md';index.write_text('![封面](./cover-2.png)','utf-8');self.assertEqual(article_assets(index),[index,copied[0]])
    def test_failed_project_import_preserves_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);target=root/'src/content/projects/o--r.yaml';target.parent.mkdir(parents=True);target.write_text('old','utf-8')
            def runner(command,**kwargs):return Result(0) if command[1:3]==['auth','status'] else Result(1,err='offline')
            with self.assertRaises(RuntimeError):import_project('o/r',root,runner);self.assertEqual(target.read_text('utf-8'),'old')
    def test_publish_command_scopes_current_content(self):
        commands=publish_commands([Path('post/index.md'),Path('post/a.png')],'note',False);self.assertEqual(commands[3],['git','add','--','post/index.md','post/a.png']);self.assertEqual(commands[-1],['git','push'])

if __name__=='__main__':unittest.main()
