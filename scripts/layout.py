"""Presentation layer; source text, page identities and media stay unchanged."""
import hashlib,html,re
from pathlib import Path
from string import Template
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
def esc(text):return html.escape(str(text),quote=True)
def route(page):return 'index.html' if page['id']=='394608272104688055' else 'page-'+page['id']+'.html'

def navigation(pages,current):
    pages=[p for p in pages if not p.get('hidden')]
    def branch(parent=''):
        out=''
        for p in pages:
            if (p['parent'] or '')!=parent:continue
            children=[c for c in pages if c['parent']==p['id']]
            active=' aria-current="page"' if p['id']==current['id'] else ''
            selected=' class="current-group"' if current['parent']==p['id'] else ''
            out+=f'<li{selected}><div class="nav-label"><a href="{route(p)}"{active}>{esc(p["title"])}</a>'
            if children:out+=f'<button class="submenu-toggle" aria-label="展開{esc(p["title"])}" aria-controls="nav-{p["id"]}" aria-expanded="false"><span aria-hidden="true">＋</span></button>'
            out+='</div>'
            if children:out+=f'<ul id="nav-{p["id"]}">'+branch(p['id'])+'</ul>'
            out+='</li>'
        return out
    return '<nav class="migration-nav" id="site-navigation" aria-label="網站分類"><ul>'+branch()+'</ul></nav>'

def directory(pages,current,headings):
    pages=[p for p in pages if not p.get('hidden')]
    parent=next((p for p in pages if p['id']==current['parent']),current)
    siblings=[p for p in pages if p['parent']==parent['id']]
    if not siblings:siblings=[p for p in pages if not p['parent']]
    out=f'<aside class="page-sidebar"><details class="section-directory" open><summary>瀏覽{esc(parent["title"].replace("▽",""))}<span aria-hidden="true">＋</span></summary><div><ul>'
    for s in siblings:
        active=' class="selected"' if s['id']==current['id'] else ''
        out+=f'<li><a href="{route(s)}"{active}>{esc(s["title"])}</a></li>'
    out+='</ul></div></details>'
    if headings:
        out+='<details class="page-toc" open><summary>本頁內容<span aria-hidden="true">＋</span></summary><div><ol>'
        out+=''.join(f'<li><a href="#{esc(i)}">{esc(t)}</a></li>' for i,t in headings)
        out+='</ol></div></details>'
    return out+'</aside>'

def prepare_content(soup):
    original=soup.select_one('#main-wrap > .container')
    content=BeautifulSoup(str(original) if original else str(soup.select_one('#main-wrap')),'html.parser')
    for node in content.select('*'):
        if node.name=='font':
            for key in ['color','size','face']:node.attrs.pop(key,None)
        if node.get('style'):
            rules=[]
            for rule in node['style'].split(';'):
                key=rule.partition(':')[0].strip().lower()
                if key not in ['color','background-color','font-size','font-family','line-height','height','min-height','position','top','left','right','bottom','text-shadow','letter-spacing']:rules.append(rule)
            node['style']=';'.join(rules)
        for key in ['bgcolor','bordercolor']:node.attrs.pop(key,None)
    for node in content.select('.wsite-spacer-label,.ui-resizable-handle'):node.decompose()
    for node in content.select('.wsite-spacer'):node['class']=['layout-spacer']
    for node in reversed(content.select('.paragraph li')):
        if not re.sub(r'[\s\ufeff\u200b]+','',node.get_text()) and not node.select('img,embed,iframe,a[href],input,hr'):
            node.decompose()
    for embed in list(content.select('embed[type="application/pdf"]')):
        details=content.new_tag('details',attrs={'class':'pdf-preview','aria-label':'PDF 文件預覽'})
        summary=content.new_tag('summary');summary.string='展開文件預覽';details.append(summary)
        embed['data-pdf-src']=embed['src'];del embed['src']
        embed.replace_with(details);details.append(embed)
    for a in content.select('a[href]'):
        if re.search(r'assets/.*\.(pdf|docx?)$',a['href']):
            a['class']=list(a.get('class',[]))+['document-link'];a['target']='_blank';a['rel']='noopener'
    for gallery in content.select('.migration-gallery'):
        gallery['aria-label']='活動照片相簿'
        for index,a in enumerate(gallery.select('a'),1):a['aria-label']=f'開啟第 {index} 張活動照片原圖'
    return content

def home_content(content):
    news=content.select_one('[id="158018943686919168-col0-ul"]')
    side=content.select_one('[id="158018943686919168-col1-ul"]')
    if not news or not side:return str(content)
    section_title=content.select_one('[id="641288472171706089"]')
    if section_title:section_title.name='h2';section_title['class']=list(section_title.get('class',[]))+['news-section-title']
    update=content.select_one('[id="542845552173515768"]')
    if update:update.name='p';update['class']=['source-update']
    history=content.new_tag('details',attrs={'class':'news-archive'})
    summary=content.new_tag('summary');summary.string='歷史公告與活動紀錄';history.append(summary)
    archive=content.new_tag('div');history.append(archive)
    items=news.find_all('li',recursive=False)
    for index,item in enumerate(items):
        item['class']=list(item.get('class',[]))+['news-entry']
        if index>8:archive.append(item.extract())
    for paragraph in news.select('.paragraph'):
        lines=paragraph.select('li') or [paragraph]
        for line in lines:
            text=next((t for t in line.find_all(string=True) if re.sub(r'[\s\ufeff\u200b]+','',str(t))),None)
            if text is None:continue
            match=re.match(r'^[\s\ufeff\u200b]*(\d{6,7})(?=\D|$)',str(text))
            if not match:continue
            badge=content.new_tag('span',attrs={'class':'news-date'});badge.string=match.group(1)
            rest=str(text)[match.end():];text.replace_with(badge)
            if rest:badge.insert_after(rest)
    news.append(history)
    container=content.new_tag('div',attrs={'class':'home-layout'})
    left=content.new_tag('section',attrs={'class':'home-news','aria-label':'最新消息'})
    right=content.new_tag('aside',attrs={'class':'home-reading','aria-label':'好文分享'})
    left.append(news.extract());right.append(side.extract());container.append(left);container.append(right)
    original_table=content.select_one('.wsite-multicol')
    if original_table:original_table.replace_with(container)
    return str(content)

def render_layout(page,soup,pages,prepared=False,hero_image=''):
    content=BeautifulSoup(str(soup),'html.parser') if prepared else prepare_content(soup)
    home=page['id']=='394608272104688055'
    headings=[]
    for index,h in enumerate(content.select('h2,h3'),1):
        text=h.get_text(' ',strip=True).replace('\ufeff','')
        if not text:continue
        identity=h.get('id') or 'section-'+str(index);h['id']=identity
        headings.append((identity,text))
    current_h1=content.find('h1')
    if current_h1 and current_h1.get_text(strip=True)==page['title']:current_h1.decompose()
    parent=next((p for p in pages if p['id']==page['parent']),None)
    crumbs='<a href="index.html">領域首頁</a>'
    if parent:crumbs+=f'<span aria-hidden="true">／</span><a href="{route(parent)}">{esc(parent["title"].replace("▽",""))}</a>'
    crumbs+=f'<span aria-hidden="true">／</span><span>{esc(page["title"].replace("▽",""))}</span>'
    quick_ids=['950890031291555289','371456961889235384','911440036309704097','101879850848966350']
    quick=''
    for index,i in enumerate(quick_ids,1):
        p=next((p for p in pages if p['id']==i and not p.get('hidden')),None)
        if p is None:continue
        quick+=f'<a href="{route(p)}"><span class="quick-number">0{index}</span><span>{esc(p["title"].replace("▽",""))}</span><span aria-hidden="true">↗</span></a>'
    if home:
        hero_style=(soup.select_one('.wsite-header') or {}).get('style','')
        match=re.search(r'url\([\'"]?([^\)\'"]+)',hero_style)
        photo=hero_image or (match.group(1) if match else '')
        cube_link='<a class="text-link" href="page-911440036309704097.html">走進魔方花絮 <span aria-hidden="true">↗</span></a>' if any(p['id']=='911440036309704097' and not p.get('hidden') for p in pages) else ''
        lead=f'<section class="home-hero"><div class="hero-copy"><p class="eyebrow">溪中魔『數』・教與學的日常</p><h1>從課堂到生活，<br>發現數學的<span>更多可能。</span></h1><p class="hero-description">教學資源、共學足跡與活動紀錄，<br>一起探索屬於溪中的數學風景。</p>{cube_link}</div><figure class="hero-photo"><img src="{esc(photo)}" alt="大溪國中校園中的彩色魔術方塊" fetchpriority="high"><figcaption>一顆魔方，開啟對數學的好奇。</figcaption><span class="photo-corner" aria-hidden="true">＋</span></figure></section><div class="quick-resources" aria-label="常用資料">{quick}</div>'
        body='<div class="content-column home-content">'+(str(content) if prepared else home_content(content))+'</div>'
    else:
        lead=''
        body=f'<header class="page-lead"><div class="breadcrumbs" aria-label="目前位置">{crumbs}</div><p class="eyebrow">{esc(parent["title"].replace("▽","")) if parent else "溪中數學・教學與生活"}</p><h1>{esc(page["title"].replace("▽",""))}</h1></header><div class="page-grid">{directory(pages,page,headings)}<article class="content-column" data-page-title="{esc(page["title"])}">{content}</article></div>'
    shell=Template((ROOT/'templates/base.html').read_text(encoding='utf-8'))
    versions={name:hashlib.sha256((ROOT/'site'/name).read_bytes()).hexdigest()[:12] for name in ['design.css','design.js']}
    return shell.substitute(title=esc(page['title'])+'｜溪中魔「數」領域網站',body_class='home-page' if home else 'inner-page',navigation=navigation(pages,page),lead=lead,body=body,css_url='design.css?v='+versions['design.css'],js_url='design.js?v='+versions['design.js'])
