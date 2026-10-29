import concurrent.futures, hashlib, json, pathlib, re, urllib.parse
import requests
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKUP = ROOT / 'backup'
PUBLIC = ROOT / 'site'
PUBLIC.mkdir(exist_ok=True)
(PUBLIC / 'assets').mkdir(exist_ok=True)
BASE = 'https://48565855-649322120594517142.preview.editmysite.com'
urls = set()
def absolute(u):
    u=urllib.parse.urljoin(BASE,u)
    parsed=urllib.parse.urlsplit(u)
    if parsed.hostname=='dsjhmath.weebly.com':u=BASE+parsed.path+('?' + parsed.query if parsed.query else '')
    return u
def add(u):
    if u and ('/uploads/' in u or '/themes/' in u or '/theme/' in u):
        urls.add(absolute(u))
for path in BACKUP.glob('*.html'):
    soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    for e in soup.select('[src],a[href],[style]'):
        add(e.get('src')); add(e.get('href'))
        for u in re.findall(r'url\([\'"]?(.*?)[\'"]?\)', e.get('style','')): add(u)
    for image in soup.select('.wslide-link-thumbnail img[src]'):
        u=image['src']
        parsed=urllib.parse.urlsplit(u)
        stem,ext=parsed.path.rsplit('.',1)
        add(stem+'_orig.'+ext)
custom_path=BACKUP/'custom-frames.json'
if custom_path.exists():
    for content in json.loads(custom_path.read_text(encoding='utf-8')).values():
        soup=BeautifulSoup(content,'html.parser')
        for e in soup.select('[src]'):
            u=e['src']
            if 'docs.google.com/gview' in u:u=urllib.parse.parse_qs(urllib.parse.urlsplit(u).query)['url'][0]
            if '/uploads/' in u:add(u)
            elif u.lower().endswith('.pdf'):urls.add(u)
styles = json.loads((BACKUP/'styles-final.json').read_text(encoding='utf-8'))
theme = next(BeautifulSoup(x,'html.parser').style.string for x in styles if 'title="wsite-theme-css"' in x)
(BACKUP/'theme.css').write_text(theme, encoding='utf-8')
for u in re.findall(r'url\([\'"]?(.*?)[\'"]?\)', theme):
    u=u.strip('\'"')
    if not u.startswith('data:'): urls.add(absolute(u))
cache_path=BACKUP/'asset-manifest.json'
cache=json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {}
def fetch(u):
    key=hashlib.sha256(u.encode()).hexdigest()[:20]
    ext=pathlib.PurePosixPath(urllib.parse.unquote(urllib.parse.urlsplit(u).path)).suffix.lower()
    if not re.fullmatch(r'\.[a-z0-9]{1,6}',ext): ext='.bin'
    target=PUBLIC/'assets'/(key+ext)
    if u in cache and cache[u].get('ok') and target.exists(): return u,cache[u]
    try:
        r=requests.get(u, timeout=(10,30))
        typ=r.headers.get('Content-Type','')
        ok=r.status_code==200 and len(r.content)>0 and 'text/html' not in typ.lower()
        result={'ok':ok,'status':r.status_code,'type':typ,'bytes':len(r.content)}
        if ok:
            target.write_bytes(r.content)
            result.update(path='assets/'+target.name,sha256=hashlib.sha256(r.content).hexdigest())
    except requests.RequestException as ex: result={'ok':False,'status':'network-error','reason':type(ex).__name__}
    return u,result
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
    for i,(u,result) in enumerate(pool.map(fetch, sorted(urls)),1):
        cache[u]=result
        if i%25==0: print(f'{i}/{len(urls)}',flush=True)
        cache_path.write_text(json.dumps(cache,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'total':len(cache),'saved':sum(x['ok'] for x in cache.values()),'failed':sum(not x['ok'] for x in cache.values())}))
