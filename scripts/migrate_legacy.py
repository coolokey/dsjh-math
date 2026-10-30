import hashlib,html,json,pathlib,re,urllib.parse
from bs4 import BeautifulSoup
from layout import render_layout

ROOT=pathlib.Path(__file__).resolve().parents[1]
B=ROOT/'backup'; OUT=ROOT/'site'
BASE='https://48565855-649322120594517142.preview.editmysite.com'
pages=json.loads((B/'pages.json').read_text(encoding='utf-8'))
assets=json.loads((B/'asset-manifest.json').read_text(encoding='utf-8'))
links=json.loads((B/'link-report.json').read_text(encoding='utf-8'))
custom=json.loads((B/'custom-frames.json').read_text(encoding='utf-8'))
byid={p['id']:p for p in pages}
def filename(p):return 'index.html' if p==pages[0] else 'page-'+p['id']+'.html'
def esc(x):return html.escape(x,quote=True)
aliases={}
def alias(label,p):aliases['/'+''.join(str(ord(c)) if ord(c)>127 else c for c in label)+'.html']=p
for p in pages:
    alias(p['title'].replace('▽',''),p)
for label,title in {'領域會議照片':'領域會議照片','教學觀摩':'教學觀摩','領域社團':'領域社團▽','照片區':'照片區','暢所欲「圓」專題':'暢所欲「圓」專題','暢所欲『圓』專題':'暢所欲「圓」專題','領域社團▽':'領域社團▽','領域社團研習':'103學年桌遊社團','領域行事曆':'領域行事曆','領域社團集錦':'領域社團▽'}.items():
    alias(label,next(p for p in pages if p['title']==title))
aliases.update({'/389362249531038222969661.html':byid['280347767837955330'],'/2627425152274421230022291123012356038988.html':byid['836935670277758784'],'/389362249526371356962903129255.html':byid['437398475864824744'],'/2670036938.html':byid['180400788921841327'],'/26700369383074032722.html':byid['180400788921841327']})
issues=[]
def asset_url(u):
    u=urllib.parse.urljoin(BASE,u)
    parsed=urllib.parse.urlsplit(u)
    if parsed.hostname=='dsjhmath.weebly.com':u=BASE+parsed.path+('?' + parsed.query if parsed.query else '')
    return u
def local(u):
    a=assets.get(asset_url(u))
    return a.get('path') if a and a['ok'] else None
def css_urls(css):
    def sub(m):
        u=m.group(1).strip('\'"'); p=local(u)
        return 'url("'+(p or ('https:'+u if u.startswith('//') else u if u.startswith('http') else ''))+'")'
    return re.sub(r'url\((.*?)\)',sub,css)
def nav():
    result='<nav class="migration-nav" aria-label="網站分類"><ul>'
    for p in pages:
        if p['parent']:continue
        result+='<li><a href="'+filename(p)+'">'+esc(p['title'])+'</a>'
        children=[c for c in pages if c['parent']==p['id']]
        if children:
            result+='<button class="submenu-toggle" aria-label="展開'+esc(p['title'])+'" aria-expanded="false">▾</button><ul>'
            result+=''.join('<li><a href="'+filename(c)+'">'+esc(c['title'])+'</a></li>' for c in children)
            result+='</ul>'
        result+='</li>'
    return result+'</ul></nav>'
def rewrite_link(u,label,p):
    if not u or u=='#':return None
    if u.startswith('http://weebly-link/'):
        q=byid.get(u.rsplit('/',1)[-1]);return filename(q) if q else None
    parsed=urllib.parse.urlsplit(u)
    if parsed.hostname=='dsjhmath.weebly.com':
        if parsed.path in ('','/'):return 'index.html'
        target=aliases.get(urllib.parse.unquote(parsed.path))
        if target:return filename(target)+('#'+parsed.fragment if parsed.fragment else '')
        if '/uploads/' not in parsed.path:
            candidates=[q for q in pages if q['title'].replace('▽','') in label.replace('﻿','')]
            if candidates:return filename(max(candidates,key=lambda x:len(x['title'])))
            issues.append({'page':p['title'],'url':u,'reason':'unmapped-original-page'})
            return None
    if '/uploads/' in u:
        saved=local(u)
        if not saved:issues.append({'page':p['title'],'url':u,'reason':'asset-unavailable'})
        return saved
    if u.startswith('//'):u='https:'+u
    report=links.get(u)
    if report and report['state']=='invalid':
        issues.append({'page':p['title'],'url':u,'reason':'HTTP '+str(report['status'])});return None
    return report['final_url'] if report and report.get('upgraded') else u

template=BeautifulSoup((B/(pages[0]['id']+'.html')).read_text(encoding='utf-8'),'html.parser')
stats=[]
for p in pages:
    path=B/(p['id']+'.html')
    soup=BeautifulSoup(path.read_text(encoding='utf-8') if path.exists() else str(template),'html.parser')
    main=soup.select_one('#main-wrap')
    for frame in list(soup.select('iframe[id^="custom-frame-"]')):
        raw=custom.get(frame.get('id'))
        if raw:
            inner=BeautifulSoup(raw,'html.parser').select_one('#customhtml-content')
            wrapper=soup.new_tag('div',attrs={'class':'custom-embed'})
            for child in list(inner.contents):wrapper.append(child.extract())
            frame.replace_with(wrapper)
    for frame in list(soup.select('iframe[src]')):
        if 'docs.google.com/gview' in frame['src']:
            u=urllib.parse.parse_qs(urllib.parse.urlsplit(frame['src']).query).get('url',[''])[0]
            frame.replace_with(soup.new_tag('embed',src=u,type='application/pdf'))
    if p['external']:
        report=links.get(p['url'],{})
        active=report.get('state')!='invalid'
        content='<h1>'+esc(p['title'])+'</h1>'
        content+=('<p>此項目原為外部網站連結。</p><p><a href="'+esc(p['url'])+'" target="_blank" rel="noopener noreferrer">開啟原網站</a></p>') if active else '<p>原外部連結已失效，依搬移設定略過備份。</p>'
        main.clear();main.append(BeautifulSoup('<div class="container external-page">'+content+'</div>','html.parser'))
    # Turn slideshows into local galleries, preserving all original images.
    for slide in list(soup.select('.wslide')):
        gallery=soup.new_tag('div',attrs={'class':'migration-gallery'})
        seen=set()
        originals=slide.select('.wslide-link-thumbnail img[src]') or slide.select('.wslide-slides img[src]')
        for image in originals:
            u=image['src']
            if slide.select('.wslide-link-thumbnail img[src]'):
                stem,ext=u.rsplit('.',1)
                original=stem+'_orig.'+ext
                if local(original):u=original
            if u in seen:continue
            seen.add(u)
            a=soup.new_tag('a',href=u); im=soup.new_tag('img',src=image['src'],alt=p['title']+'活動照片',loading='lazy');a.append(im);gallery.append(a)
        slide.replace_with(gallery)
    for e in list(soup.select('script,form,.w-element-controls,#wsite-menus,.JCLRgrips,.wsite-social,.phone-number,.wsite-youtube-coverbox,.customhtml-blocker,.wsite-spotlight-cover')):e.decompose()
    header=soup.select_one('#header-wrap')
    if header:header.clear()
    for form in soup.select('.wsite-form-container'):
        notice=soup.new_tag('p',attrs={'class':'form-archive-note'});notice.string='原 Weebly 留言表單已停用，以下保留歷史欄位供參考，無法填寫或送出。';form.insert_before(notice)
        for control in form.select('input,textarea,select'):control['disabled']=''
        for submit in form.parent.select('[role="button"]'):
            submit.decompose()
    for e in list(soup.select('[id$="-pdf-upload"],[id$="-pdf-fallback"]')):e.decompose()
    for e in list(soup.select('iframe')):
        src=e.get('src','')
        if 'youtube.com/embed/' in src:
            e['src']='https:'+src if src.startswith('//') else src
            e['title']=p['title']+'影片';e['loading']='lazy';e['allowfullscreen']=''
        elif 'generateMap.php' in src:
            a=soup.new_tag('a',href='https://www.google.com/maps?q=24.8799484,121.2958623');a.string='在 Google 地圖查看大溪國中';e.replace_with(a)
        elif src and not any(x in src for x in ['editmysite','preview_token','about:blank']):
            u=rewrite_link(src,p['title'],p)
            a=soup.new_tag('a',href=u) if u else soup.new_tag('span')
            a.string='開啟原嵌入內容' if u else '原嵌入連結已失效';e.replace_with(a)
        else:e.decompose()
    # Navigation is reconstructed directly from the recorded original hierarchy.
    original_nav=soup.select_one('#nav-wrap')
    if original_nav:original_nav.replace_with(BeautifulSoup(nav(),'html.parser'))
    for e in soup.select('*'):
        for attr in list(e.attrs):
            if attr.startswith('on') or attr in ['contenteditable','data-original-title','data-pwprotected','data-membership_required']:del e[attr]
        if e.get('style'):e['style']=css_urls(e['style']).replace('pointer-events: none;','')
        if e.name in ['img','embed','source','video','audio'] and e.get('src'):
            u=e['src'];saved=local(u)
            if '/uploads/' in u or asset_url(u) in assets:
                if saved:e['src']=saved
                else:
                    issues.append({'page':p['title'],'url':u,'reason':'asset-unavailable'})
                    if e.name=='img':
                        e.replace_with(soup.new_string(''))
                    else:e.replace_with(soup.new_string('原檔案無法取得，已略過。'))
                    continue
            elif u.startswith('//'):e['src']='https:'+u
            if e.name=='img':e['loading']='lazy';e['alt']=e.get('alt') or p['title']+'圖片'
        if e.name=='a' and e.get('href'):
            u=e['href']
            if re.fullmatch(r'(index|page-\d+)\.html',u):continue
            dest=rewrite_link(u,e.get_text(' ',strip=True),p)
            if dest:e['href']=dest
            else:
                del e['href']
                if u!='#':e['title']='原連結已失效或無法取得，未備份'
            if dest and dest.startswith('http'):e['rel']='noopener noreferrer'
    # Restore native PDF interaction and provide a direct download on phones.
    for embed in soup.select('embed[src]'):
        if embed.get('type')=='application/pdf':
            a=soup.new_tag('a',href=embed['src']);a.string='開啟／下載 PDF';embed.parent.insert_before(a)
    content=str(soup)
    assert 'preview_token' not in content
    doc=render_layout(p,soup,pages)
    (OUT/filename(p)).write_text(doc,encoding='utf-8')
    stats.append({'title':p['title'],'id':p['id'],'parent':p['parent'],'file':filename(p),'external':p['external']})
for old,p in aliases.items():
    dest=filename(p)
    (OUT/old.lstrip('/')).write_text('<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url='+dest+'"><title>'+esc(p['title'])+'</title><a href="'+dest+'">'+esc(p['title'])+'</a></html>',encoding='utf-8')
design=next(BeautifulSoup(x,'html.parser').style.string for x in json.loads((B/'styles-final.json').read_text(encoding='utf-8')) if 'id="designOptionsStyle"' in x)
(OUT/'theme.css').write_text(css_urls((B/'theme.css').read_text(encoding='utf-8'))+'\n'+design,encoding='utf-8')
(OUT/'.nojekyll').write_text('')
(OUT/'pages.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'docs'/'skipped-links.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pages':len(stats),'local_pages':sum(not p['external'] for p in pages),'external_items':sum(p['external'] for p in pages),'skipped_references':len(issues)},ensure_ascii=False))
