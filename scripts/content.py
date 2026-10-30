"""Versioned CMS content, strict validation and structured block rendering."""
import datetime,html,json,pathlib,re,urllib.parse
from bs4 import BeautifulSoup
import markdown

HOME_ID='394608272104688055'
class ContentError(ValueError):pass

def route(page):return 'index.html' if page['id']==HOME_ID else 'page-'+page['id']+'.html'
def normalize_url(value):return value.removeprefix('/dsjh-math/')
def fail(message):raise ContentError(message)

def safe_url(value,asset_root,routes,media=False):
    if not isinstance(value,str):fail('URL must be text')
    value=normalize_url(value.strip());compact=re.sub(r'[\x00-\x20\x7f]+','',value)
    parsed=urllib.parse.urlsplit(compact)
    if parsed.scheme:
        if parsed.scheme.lower() not in ('http','https','mailto','tel'):fail('Unsafe URL: '+value)
        if media and parsed.scheme.lower()!='https':fail('Media requires HTTPS')
        return
    if value.startswith('//'):fail('Protocol-relative URL is not allowed')
    path=urllib.parse.unquote(parsed.path)
    if not path:return
    if path.startswith('/') or '\\' in path or '..' in pathlib.PurePosixPath(path).parts:fail('Unsafe local path: '+value)
    if path.startswith('assets/'):
        if not (asset_root/path).is_file():fail('Missing local attachment: '+path)
    elif path not in routes:fail('Missing local page: '+path)

def validate_html(body,asset_root,routes):
    if not isinstance(body,str):fail('body must be HTML text')
    soup=BeautifulSoup(body,'html.parser')
    for node in soup.find_all(True):
        if node.name in ('script','style','object','base','link','meta','form','svg','math','animate','set','foreignobject'):fail('Unsafe HTML element: '+node.name)
        if node.name in ('input','textarea','select','button') and not node.has_attr('disabled'):fail('Interactive form controls are not allowed')
        if node.name=='embed':
            pdf=node.get('data-pdf-src',node.get('src',''))
            if node.get('type')!='application/pdf' or not normalize_url(pdf).startswith('assets/') or not urllib.parse.urlsplit(pdf).path.lower().endswith('.pdf'):fail('Only local PDF embeds are allowed')
        for key,value in node.attrs.items():
            if key.lower().startswith('on') or key.lower() in ('srcdoc','formaction','action','srcset'):fail('Unsafe HTML attribute: '+key)
            if key in ('href','src','data-pdf-src','poster','xlink:href'):safe_url(value,asset_root,routes)
            if key=='style':
                # Existing inline layout styles are preserved; executable CSS is rejected.
                if re.search(r'expression|javascript|vbscript|@import|behavior\s*:|-moz-binding|[\\<>]',value,re.I):fail('Unsafe CSS')
                for match in re.finditer(r'url\(\s*[\'"]?(.*?)[\'"]?\s*\)',value,re.I):safe_url(match.group(1),asset_root,routes)
        if node.name=='iframe':
            u=urllib.parse.urlsplit(node.get('src',''))
            if u.scheme!='https' or u.hostname not in ('www.youtube.com','www.youtube-nocookie.com') or not u.path.startswith('/embed/'):fail('Only YouTube video embeds are supported')

def render_blocks(blocks):
    result=[]
    for b in blocks:
        kind=b.get('type');cap=html.escape(b.get('caption',''));file=html.escape(normalize_url(b.get('file','')),quote=True)
        if kind=='text':result.append(markdown.markdown(b.get('text',''),extensions=['tables','fenced_code']).replace('/dsjh-math/assets/','assets/'))
        elif kind=='image':result.append(f'<figure><img src="{file}" alt="{cap}" loading="lazy"><figcaption>{cap}</figcaption></figure>')
        elif kind=='document':
            document=f'<p><a class="document-link" href="{file}" target="_blank" rel="noopener">{cap or "開啟／下載文件"}</a></p>'
            path=normalize_url(b.get('file',''))
            if path.startswith('assets/') and urllib.parse.urlsplit(path).path.lower().endswith('.pdf'):
                document+=f'<details class="pdf-preview" aria-label="PDF 文件預覽"><summary>展開文件預覽</summary><embed type="application/pdf" data-pdf-src="{file}"></details>'
            result.append(document)
        elif kind=='gallery':
            images=[]
            for i,im in enumerate(b.get('images',[]),1):
                src=html.escape(normalize_url(im.get('file','')),quote=True);alt=html.escape(im.get('caption',''),quote=True)
                images.append(f'<a href="{src}" aria-label="開啟第 {i} 張活動照片原圖"><img src="{src}" alt="{alt}" loading="lazy"></a>')
            result.append('<div class="migration-gallery" aria-label="活動照片相簿">'+''.join(images)+'</div>')
        elif kind=='video':
            parsed=urllib.parse.urlsplit(b.get('url',''));vid=urllib.parse.parse_qs(parsed.query).get('v',[''])[0]
            if parsed.hostname=='youtu.be':vid=parsed.path.strip('/')
            if parsed.path.startswith('/embed/'):vid=parsed.path.split('/')[-1]
            if parsed.scheme!='https' or parsed.hostname not in ('www.youtube.com','youtube.com','youtu.be','www.youtube-nocookie.com') or not re.fullmatch('[A-Za-z0-9_-]{11}',vid):fail('Video URL must be a YouTube HTTPS URL')
            result.append(f'<iframe src="https://www.youtube-nocookie.com/embed/{vid}" title="影片" loading="lazy" allowfullscreen></iframe>')
        else:fail('Unknown block type: '+str(kind))
    return '\n'.join(result)

def load_content(content_root,asset_root):
    content_root=pathlib.Path(content_root);asset_root=pathlib.Path(asset_root)
    try:
        home=json.loads((content_root/'home.json').read_text(encoding='utf-8'))
        pages=[home]+[json.loads(p.read_text(encoding='utf-8')) for p in sorted((content_root/'pages').glob('*.json'))]
        aliases=json.loads((content_root/'aliases.json').read_text(encoding='utf-8'))
    except (OSError,ValueError) as e:fail('Cannot read content: '+str(e))
    if home.get('id')!=HOME_ID or home.get('parent') or home.get('hidden'):fail('Homepage identity and visibility are protected')
    byid={}
    required={'id','title','parent','order','hidden','external','body','blocks'}
    for p in pages:
        if not isinstance(p,dict) or not required.issubset(p):fail('Missing page fields')
        id=p['id']
        if p['parent'] is None:p['parent']=''
        if not isinstance(id,str) or not re.fullmatch('[A-Za-z0-9_-]+',id):fail('Invalid page ID')
        if id in byid:fail('Duplicate page ID: '+id)
        if not isinstance(p['title'],str) or not p['title'].strip():fail('Title is required')
        if not isinstance(p['body'],str):fail('body must be HTML text')
        if p.get('blocks_position','after') not in ('before','after'):fail('Invalid content block position')
        if not isinstance(p['parent'],str) or type(p['order']) is not int or type(p['hidden']) is not bool or type(p['external']) is not bool or not isinstance(p['blocks'],list):fail('Invalid page metadata')
        byid[id]=p
    for p in pages:
        trail=set();node=p
        while node['parent']:
            if node['id'] in trail:fail('Category cycle')
            trail.add(node['id'])
            if node['parent'] not in byid:fail('Missing parent: '+node['parent'])
            node=byid[node['parent']]
        if p['parent']:
            parent=byid[p['parent']]
            if parent['parent']:fail('Only two category levels are supported')
            if parent['hidden'] and not p['hidden']:fail('Hide child pages before hiding their category')
    if not isinstance(aliases,dict):fail('Invalid aliases')
    for name,id in aliases.items():
        if not re.fullmatch(r'[A-Za-z0-9_()\-]+\.html',name) or name in {route(p) for p in pages}:fail('Invalid alias route')
        if not isinstance(id,str):fail('Invalid alias target')
    aliases={name:id for name,id in aliases.items() if id in byid}
    routes={route(p) for p in pages}|set(aliases)
    for p in pages:
        p['body']=p['body'].replace('/dsjh-math/assets/','assets/')
        for b in p['blocks']:
            if not isinstance(b,dict):fail('Invalid block')
            kind=b.get('type')
            for field in ('file','caption','text','url'):
                if field in b and not isinstance(b[field],str):fail('Block fields must be text')
            if kind in ('image','document') and not b.get('file'):fail('Block file is required')
            if kind=='gallery' and (not isinstance(b.get('images'),list) or not all(isinstance(i,dict) and i.get('file') for i in b['images'])):fail('Gallery images are required')
        validate_html(p['body']+'\n'+render_blocks(p['blocks']),asset_root,routes)
    if not home.get('hero_image'):fail('Homepage hero image is required')
    safe_url(home['hero_image'],asset_root,routes,media=True)
    render_news(home.get('news',[]),asset_root,routes)
    return sorted(pages,key=lambda p:(p['order'],p['id'])),aliases


def render_news(news,asset_root=None,routes=None):
    if not isinstance(news,list):fail('Homepage news must be a list')
    result=[]
    for item in news:
        if not isinstance(item,dict) or not isinstance(item.get('title'),str) or not item['title'].strip():fail('News title is required')
        try:parsed_date=datetime.date.fromisoformat(item.get('date',''))
        except (TypeError,ValueError):fail('News date must use YYYY-MM-DD')
        text=item.get('text','');link=item.get('link','')
        if not isinstance(text,str) or not isinstance(link,str):fail('News fields must be text')
        body=markdown.markdown(text,extensions=['tables','fenced_code']);title=html.escape(item['title']);date=html.escape(item['date'])
        if asset_root is not None:
            validate_html(body,asset_root,routes)
            safe_url(link,asset_root,routes)
        if link:title=f'<a href="{html.escape(normalize_url(link),quote=True)}">{title}</a>'
        date_label=f'{parsed_date.year-1911:03d}{parsed_date.month:02d}{parsed_date.day:02d}' if parsed_date.year>=1912 else date
        result.append(f'<li class="news-entry cms-news-entry"><time class="news-date" datetime="{date}">{date_label}</time><h3>{title}</h3>{body}</li>')
    return '<section class="cms-news" aria-label="新公告"><ul>'+''.join(result)+'</ul></section>' if result else ''
