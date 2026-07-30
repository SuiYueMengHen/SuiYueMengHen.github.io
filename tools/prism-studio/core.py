from __future__ import annotations
import json, os, re, shutil, socket, ssl, subprocess, tempfile, time, unicodedata, urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable
import yaml
import certifi

IMAGE_EXTENSIONS={'.webp','.avif','.png','.jpg','.jpeg'}
KNOWN_TOOL_DIRS=(Path('/opt/homebrew/bin'),Path('/usr/local/bin'),Path('/usr/bin'),Path('/bin'))

def command_environment()->dict[str,str]:
    """Return an app-safe environment for CLI tools launched outside a shell."""
    env=os.environ.copy();existing=env.get('PATH','').split(os.pathsep)
    paths=[str(path) for path in KNOWN_TOOL_DIRS]
    env['PATH']=os.pathsep.join(dict.fromkeys([*paths,*filter(None,existing)]))
    return env

def resolve_command(name:str)->str|None:
    found=shutil.which(name,path=command_environment()['PATH'])
    if found:return found
    for directory in KNOWN_TOOL_DIRS:
        candidate=directory/name
        if candidate.exists() and os.access(candidate,os.X_OK):return str(candidate)
    try:
        result=subprocess.run(['/bin/zsh','-lc',f'command -v {name}'],capture_output=True,text=True,timeout=4)
        return result.stdout.strip() if result.returncode==0 and result.stdout.strip() else None
    except (OSError,subprocess.TimeoutExpired):return None

def split_frontmatter(source:str)->tuple[dict,str]:
    match=re.match(r'^---\r?\n(.*?)\r?\n---(?:\r?\n)*',source,re.S)
    if not match:return {},source
    return yaml.safe_load(match.group(1)) or {},source[match.end():]

def serialize_frontmatter(data:dict,body:str)->str:
    clean={key:value for key,value in data.items() if value not in (None,'',[])}
    header=yaml.safe_dump(clean,allow_unicode=True,sort_keys=False,default_flow_style=False).strip()
    return f'---\n{header}\n---\n\n{body.lstrip()}'

def atomic_save(path:Path,content:str,repo_root:Path,backup:bool=True)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if backup and path.exists():
        relative=path.resolve().relative_to(repo_root.resolve());target=repo_root/'.prism-studio'/'backups'/relative
        if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    fd,name=tempfile.mkstemp(prefix=f'.{path.name}.',dir=path.parent,text=True)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as handle:handle.write(content);handle.flush();os.fsync(handle.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

def copy_images(files:list[Path],article_dir:Path)->list[Path]:
    copied=[];article_dir.mkdir(parents=True,exist_ok=True)
    for source in files:
        if source.suffix.lower() not in IMAGE_EXTENSIONS:raise ValueError(f'不支持的图片格式：{source.suffix}')
        target=article_dir/source.name;counter=2
        while target.exists() and target.read_bytes()!=source.read_bytes():target=article_dir/f'{source.stem}-{counter}{source.suffix.lower()}';counter+=1
        if not target.exists():shutil.copy2(source,target)
        copied.append(target)
    return copied

def normalize_repo(value:str)->str:
    value=re.sub(r'^https?://github\.com/','',value.strip(),flags=re.I).removesuffix('.git').rstrip('/')
    if not re.match(r'^[\w.-]+/[\w.-]+$',value):raise ValueError('请输入 owner/repo 或完整 GitHub 仓库 URL')
    return value

def yaml_quote(value):return json.dumps(value,ensure_ascii=False)

def import_project(repo_value:str,repo_root:Path,runner:Callable=subprocess.run)->Path:
    repo=normalize_repo(repo_value)
    gh=resolve_command('gh')
    if not gh:raise RuntimeError('未找到 GitHub CLI。请先安装 gh，或从终端启动 Prism Studio。')
    try:auth=runner([gh,'auth','status','-h','github.com'],cwd=repo_root,capture_output=True,text=True,timeout=10)
    except subprocess.TimeoutExpired:raise RuntimeError('GitHub CLI 认证检查超时。请检查网络后重试。')
    if auth.returncode:raise RuntimeError('GitHub CLI 登录无效。请运行：gh auth login -h github.com')
    try:result=runner([gh,'api',f'repos/{repo}'],cwd=repo_root,capture_output=True,text=True,timeout=15)
    except subprocess.TimeoutExpired:raise RuntimeError('GitHub API 请求超时；原快照未更改。')
    if result.returncode:raise RuntimeError(result.stderr.strip() or 'GitHub 项目导入失败；原快照未更改。')
    data=json.loads(result.stdout);target=repo_root/'src/content/projects'/f"{repo.lower().replace('/','--')}.yaml"
    old=target.read_text('utf-8') if target.exists() else ''
    def prior(key,default):
        match=re.search(rf'^{key}:\s*(.+)$',old,re.M);return match.group(1) if match else default
    lines=[f"repo: {yaml_quote(data['full_name'])}",f"title: {yaml_quote(data['name'])}",f"description: {yaml_quote(data.get('description') or '')}",f"language: {yaml_quote(data['language']) if data.get('language') else 'null'}",f"stars: {data.get('stargazers_count',0)}",f"forks: {data.get('forks_count',0)}",f"license: {yaml_quote((data.get('license') or {}).get('spdx_id')) if data.get('license') else 'null'}",f"topics: {yaml_quote(data.get('topics',[]))}",f"homepage: {yaml_quote(data['homepage']) if data.get('homepage') else 'null'}",f"featured: {prior('featured','false')}",f"order: {prior('order','100')}",f"syncedAt: {yaml_quote(datetime.now(timezone.utc).isoformat())}"]
    atomic_save(target,'\n'.join(lines)+'\n',repo_root,backup=True);return target

def load_project_snapshot(path:Path)->dict:
    data=yaml.safe_load(path.read_text('utf-8')) or {}
    data['topics']=[str(topic).strip() for topic in data.get('topics',[]) if str(topic).strip()]
    return data

def save_project_snapshot(path:Path,data:dict,repo_root:Path)->None:
    clean=dict(data);clean['topics']=list(dict.fromkeys(str(topic).strip() for topic in clean.get('topics',[]) if str(topic).strip()))
    for key in ('cover','coverAlt'):
        if not clean.get(key):clean.pop(key,None)
    content=yaml.safe_dump(clean,allow_unicode=True,sort_keys=False,default_flow_style=False)
    atomic_save(path,content,repo_root,backup=True)

def pages_site_url(repo_root:Path)->str:
    config=repo_root/'src/config/site.ts'
    if config.exists():
        match=re.search(r"\bsite:\s*['\"](https?://[^'\"]+)",config.read_text('utf-8'))
        if match:return match.group(1).rstrip('/')
    return ''

def wait_for_pages_deployment(site_url:str,commit:str,attempts:int=60,interval:float=3,fetcher=urllib.request.urlopen,sleeper=time.sleep)->dict:
    endpoint=f"{site_url.rstrip('/')}/build-info.json"
    last_error='';context=ssl.create_default_context(cafile=certifi.where())
    for attempt in range(attempts):
        try:
            request=urllib.request.Request(f'{endpoint}?check={time.time_ns()}',headers={'Cache-Control':'no-cache','User-Agent':'Prism-Studio-Deploy-Check'})
            with fetcher(request,timeout=8,context=context) as response:data=json.loads(response.read().decode('utf-8'))
            if data.get('commit')==commit:return {'deployed':True,'url':site_url,'build':data}
            last_error=f"线上仍是 {str(data.get('commit','未知'))[:8]}"
        except Exception as error:last_error=str(error)
        if attempt+1<attempts:sleeper(interval)
    return {'deployed':False,'url':site_url,'error':last_error or '部署状态暂不可用'}

def find_port(start:int=4321)->int:
    for port in range(start,start+100):
        with socket.socket() as probe:
            try:probe.bind(('127.0.0.1',port));return port
            except OSError:pass
    raise RuntimeError('找不到可用的本地预览端口')

def command_available(name:str)->bool:return shutil.which(name) is not None

def environment_status(repo_root:Path,runner:Callable=subprocess.run)->dict[str,bool]:
    tools={name:resolve_command(name) for name in ('node','npm','git','gh')};status={name:bool(path) for name,path in tools.items()};status['repository']=(repo_root/'.git').exists()
    if status['gh']:
        try:
            auth=runner([tools['gh'],'auth','status','-h','github.com'],cwd=repo_root,capture_output=True,timeout=6)
            api=runner([tools['gh'],'api','user','--jq','.login'],cwd=repo_root,capture_output=True,timeout=8)
            status['gh_auth']=auth.returncode==0 and api.returncode==0
        except subprocess.TimeoutExpired:status['gh_auth']=False
    else:status['gh_auth']=False
    return status

def slugify_collection(value:str)->str:
    normalized=unicodedata.normalize('NFKC',value).strip().lower()
    return re.sub(r'[^\w\u3400-\u9fff.-]+','-',normalized).strip('-') or 'collection'

def preview_route(kind:str,identifier:str='')->str:
    from urllib.parse import quote
    if kind=='article':return f'/blog/{quote(identifier,safe="-._~")}/'
    if kind=='collection':return f'/collections/{quote(identifier,safe="-._~")}/'
    if kind=='project':return '/projects/'
    return '/'

def create_collection(repo_root:Path,title:str,description:str,slug:str='',subtitle:str='',volume:str='',status:str='ongoing',featured:bool=False,order:int|None=None)->Path:
    if not title.strip() or not description.strip():raise ValueError('合集标题和简介不能为空。')
    directory=repo_root/'src/content/collections';directory.mkdir(parents=True,exist_ok=True)
    existing=[]
    for file in directory.glob('*.yaml'):
        try:existing.append(yaml.safe_load(file.read_text('utf-8')) or {})
        except yaml.YAMLError:continue
    used={int(item['order']) for item in existing if isinstance(item.get('order'),int)}
    chosen=order or (max(used,default=0)+1)
    if chosen<=0:raise ValueError('合集顺序必须是正整数。')
    if chosen in used:raise ValueError(f'合集顺序 {chosen} 已被使用。')
    identifier=slugify_collection(slug or title);target=directory/f'{identifier}.yaml'
    if target.exists():raise FileExistsError(f'合集 slug 已存在：{identifier}')
    data={'title':title.strip(),'subtitle':subtitle.strip() or None,'description':description.strip(),'order':chosen,'volume':volume.strip() or None,'status':status,'featured':featured}
    content=yaml.safe_dump({key:value for key,value in data.items() if value not in (None,'')},allow_unicode=True,sort_keys=False)
    atomic_save(target,content,repo_root,backup=False);return target

def content_catalog(repo_root:Path)->dict:
    collections=[];projects=[];categories=set();tags=set();articles=[]
    directory=repo_root/'src/content/collections'
    for file in directory.glob('*.yaml') if directory.exists() else []:
        try:
            data=yaml.safe_load(file.read_text('utf-8')) or {};collections.append({'id':file.stem,'title':data.get('title',file.stem),'order':data.get('order',9999)})
        except yaml.YAMLError:continue
    blog=repo_root/'src/content/blog'
    if blog.exists():
        for file in sorted([*blog.glob('*/index.md'),*blog.glob('*/index.mdx')]):
            data,_=split_frontmatter(file.read_text('utf-8'));category=str(data.get('category','')).strip()
            if category and not data.get('collection'):categories.add(category)
            tags.update(str(tag).strip() for tag in data.get('tags',[]) if str(tag).strip())
            articles.append({'path':file,'slug':file.parent.name,'title':data.get('title',file.parent.name),'category':category,'tags':data.get('tags',[]),'collection':data.get('collection'),'order':data.get('collectionOrder')})
    project_dir=repo_root/'src/content/projects'
    for file in sorted(project_dir.glob('*.yaml')) if project_dir.exists() else []:
        try:
            data=yaml.safe_load(file.read_text('utf-8')) or {};projects.append({'id':file.stem,'path':file,'title':data.get('title',file.stem),'repo':data.get('repo',''),'topics':data.get('topics',[]),'data':data})
        except yaml.YAMLError:continue
    categories.update(load_category_registry(repo_root))
    collections.sort(key=lambda item:(item['order'],item['title']))
    return {'collections':collections,'projects':projects,'categories':sorted(categories),'tags':sorted(tags),'articles':articles}

def category_registry_path(repo_root:Path)->Path:return repo_root/'src/data/categories.json'

def load_category_registry(repo_root:Path)->list[str]:
    try:data=json.loads(category_registry_path(repo_root).read_text('utf-8'))
    except (OSError,json.JSONDecodeError):return []
    return sorted({str(item).strip() for item in data if str(item).strip()}) if isinstance(data,list) else []

def save_category_registry(repo_root:Path,categories:list[str])->Path:
    names=sorted({name.strip() for name in categories if name.strip()})
    target=category_registry_path(repo_root);atomic_save(target,json.dumps(names,ensure_ascii=False,indent=2)+'\n',repo_root)
    return target

def create_category(repo_root:Path,name:str)->Path:
    name=name.strip()
    if not name:raise ValueError('分类名称不能为空。')
    return save_category_registry(repo_root,[*content_catalog(repo_root)['categories'],name])

def migrate_category(repo_root:Path,old_name:str,new_name:str)->list[Path]:
    old_name=old_name.strip();new_name=new_name.strip()
    if not old_name or not new_name:raise ValueError('分类名称不能为空。')
    changed=[]
    for path in sorted([*(repo_root/'src/content/blog').glob('*/index.md'),*(repo_root/'src/content/blog').glob('*/index.mdx')]):
        data,body=split_frontmatter(path.read_text('utf-8'))
        if str(data.get('category','')).strip()==old_name:
            data['category']=new_name;atomic_save(path,serialize_frontmatter(data,body),repo_root);changed.append(path)
    names=[new_name if item==old_name else item for item in content_catalog(repo_root)['categories']]
    save_category_registry(repo_root,names);return changed

def delete_category(repo_root:Path,name:str)->list[Path]:
    changed=migrate_category(repo_root,name,'未分类')
    names=[item for item in content_catalog(repo_root)['categories'] if item!=name]
    save_category_registry(repo_root,[*names,'未分类']);return changed

def reorder_collection(repo_root:Path,collection_id:str,ordered_files:list[Path])->None:
    if not collection_id:raise ValueError('只能调整合集内文章的顺序。')
    for number,path in enumerate(ordered_files,1):
        data,body=split_frontmatter(path.read_text('utf-8'))
        if data.get('collection')!=collection_id:raise ValueError(f'{path.parent.name} 不属于合集 {collection_id}')
        data['collectionOrder']=number;atomic_save(path,serialize_frontmatter(data,body),repo_root)

def git_content_changes(repo_root:Path,runner:Callable=subprocess.run)->dict:
    git=resolve_command('git');articles={};collections={};projects={};files=[]
    if not git:return {'articles':articles,'collections':collections,'projects':projects,'files':files}
    result=runner([git,'-c','core.quotepath=false','status','--porcelain=v1','--untracked-files=all'],cwd=repo_root,capture_output=True,text=True)
    if result.returncode:return {'articles':articles,'collections':collections,'projects':projects,'files':files}
    for line in result.stdout.splitlines():
        if len(line)<4:continue
        status=line[:2].strip() or 'M';relative=line[3:].split(' -> ')[-1].strip('"');files.append(relative)
        match=re.match(r'src/content/blog/([^/]+)/',relative)
        if match:
            slug=match.group(1);item=articles.setdefault(slug,{'status':set(),'files':[],'added':0,'deleted':0});item['status'].add(status);item['files'].append(relative)
        collection_match=re.match(r'src/content/collections/([^/]+)\.ya?ml$',relative)
        if collection_match:collections[collection_match.group(1)]={'status':status,'file':relative}
        project_match=re.match(r'src/content/projects/([^/]+)\.ya?ml$',relative)
        if project_match:projects[project_match.group(1)]={'status':status,'file':relative}
    diff=runner([git,'diff','--numstat','HEAD','--','src/content/blog'],cwd=repo_root,capture_output=True,text=True)
    for line in diff.stdout.splitlines():
        parts=line.split('\t');match=re.match(r'src/content/blog/([^/]+)/',parts[-1]) if len(parts)>=3 else None
        if match and match.group(1) in articles:
            item=articles[match.group(1)];item['added']+=int(parts[0]) if parts[0].isdigit() else 0;item['deleted']+=int(parts[1]) if parts[1].isdigit() else 0
    for slug,item in articles.items():
        for relative in item['files']:
            path=repo_root/relative
            if '?' in item['status'] and path.is_file():item['added']+=sum(1 for _ in path.open('r',encoding='utf-8',errors='ignore'))
        item['status']=' / '.join(sorted(item['status']))
    return {'articles':articles,'collections':collections,'projects':projects,'files':files}

def git_article_changes(repo_root:Path,runner:Callable=subprocess.run)->dict[str,dict]:return git_content_changes(repo_root,runner)['articles']

def trash_article(article_file:Path,repo_root:Path)->Path:
    article_dir=article_file.parent
    if not article_dir.resolve().is_relative_to((repo_root/'src/content/blog').resolve()):raise ValueError('只能移除博客文章。')
    trash=repo_root/'.prism-studio'/'trash';trash.mkdir(parents=True,exist_ok=True)
    target=trash/f"{article_dir.name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}";counter=2
    while target.exists():target=trash/f'{target.name}-{counter}';counter+=1
    shutil.move(str(article_dir),target);return target

def article_assets(article_file:Path,repo_root:Path|None=None)->list[Path]:
    source=article_file.read_text('utf-8');paths=[article_file];data,_=split_frontmatter(source)
    for relative in re.findall(r'!\[[^\]]*\]\((\./[^)\s]+)',source):
        asset=article_file.parent/relative
        if asset.exists():paths.append(asset)
    if repo_root:
        collection=data.get('collection')
        if collection:
            candidate=repo_root/'src/content/collections'/f'{collection}.yaml'
            if candidate.exists():paths.append(candidate)
        for repo in re.findall(r'<GitHubProject\s+repo=["\']([^"\']+)["\']',source):
            candidate=repo_root/'src/content/projects'/f"{normalize_repo(repo).lower().replace('/','--')}.yaml"
            if candidate.exists():paths.append(candidate)
    return paths

def publish_commands(paths:list[Path]|None,message:str,all_changes:bool=False)->list[list[str]]:
    commands=[['npm','run','post:check'],['npm','test'],['npm','run','build']]
    commands.append(['git','add','-A'] if all_changes else ['git','add','--',*[str(path) for path in (paths or [])]])
    commit=['git','commit','-m',message] if all_changes else ['git','commit','--only','-m',message,'--',*[str(path) for path in (paths or [])]]
    diff=['git','diff','--cached','--stat'] if all_changes else ['git','diff','--cached','--stat','--',*[str(path) for path in (paths or [])]]
    commands.extend([diff,commit,['git','push']]);return commands

def execute_publish(repo_root:Path,paths:list[Path]|None,message:str,all_changes:bool=False,runner:Callable=subprocess.run)->dict:
    scoped=None if paths is None else [path.resolve().relative_to(repo_root.resolve()) if path.is_absolute() else path for path in paths]
    git=resolve_command('git') or 'git';status_command=[git,'status','--porcelain=v1'] if all_changes else [git,'status','--porcelain=v1','--',*[str(path) for path in (scoped or [])]]
    status=runner(status_command,cwd=repo_root,capture_output=True,text=True,env=command_environment())
    if status.returncode:return {'success':False,'stage':'preflight','log':'','error':status.stderr.strip() or '无法读取待上传状态。'}
    if not status.stdout.strip():return {'success':False,'stage':'preflight','log':'','error':'所选内容没有待上传变更。'}
    logs=[]
    for command in publish_commands(scoped,message,all_changes):
        resolved=resolve_command(command[0]) if command[0] in {'npm','node','git','gh'} else command[0]
        if not resolved:return {'success':False,'stage':'environment','log':'\n'.join(logs),'error':f'未找到命令：{command[0]}'}
        try:result=runner([resolved,*command[1:]],cwd=repo_root,capture_output=True,text=True,env=command_environment(),timeout=300)
        except subprocess.TimeoutExpired:return {'success':False,'stage':'timeout','log':'\n'.join(logs),'error':f'命令超时：{" ".join(command)}'}
        logs.append('$ '+' '.join(command)+'\n'+(result.stdout+result.stderr).rstrip())
        if result.returncode:return {'success':False,'stage':command[1] if len(command)>1 else command[0],'log':'\n'.join(logs),'error':(result.stderr or result.stdout).strip() or '命令执行失败'}
    local=runner([git,'rev-parse','HEAD'],cwd=repo_root,capture_output=True,text=True).stdout.strip()
    upstream=runner([git,'rev-parse','@{u}'],cwd=repo_root,capture_output=True,text=True).stdout.strip()
    if not local or local!=upstream:return {'success':False,'stage':'verify','log':'\n'.join(logs),'error':'推送后本地提交与远端跟踪分支不一致。'}
    return {'success':True,'stage':'done','log':'\n'.join(logs),'commit':local}
