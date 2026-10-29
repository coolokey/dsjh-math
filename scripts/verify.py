import hashlib,json,pathlib,re,urllib.parse
from bs4 import BeautifulSoup
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1];B=ROOT/'backup';S=ROOT/'site'
original=json.loads((B/'pages.json').read_text(encoding='utf-8'))
generated=json.loads((S/'pages.json').read_text(encoding='utf-8'))
assert [(p['id'],p['title'],p['parent']) for p in original]==[(p['id'],p['title'],p['parent']) for p in generated]
assets=json.loads((B/'asset-manifest.json').read_text(encoding='utf-8'))
errors=[];galleries=0;photos=0;pdfs=0;documents=0
for p in generated:
    file=S/p['file'];raw=file.read_text(encoding='utf-8');s=BeautifulSoup(raw,'html.parser')
    if re.search(r'preview_token|\.preview\.editmysite|weebly-link|contenteditable=|javascript:',raw,re.I):errors.append((p['title'],'editor residue'))
    if s.select('input:not([disabled]):not([type="hidden"]),textarea:not([disabled]),select:not([disabled])'):errors.append((p['title'],'active legacy form'))
    if [(a.get_text(),a['href']) for a in s.select('.migration-nav a')]!=[(p['title'],p['file']) for p in generated]:errors.append((p['title'],'navigation order'))
    for e in s.select('[href],[src],[data-pdf-src]'):
        u=e.get('href') or e.get('src') or e.get('data-pdf-src')
        if not u or u.startswith(('#','http:','https:','mailto:','tel:','data:','//')):continue
        path=urllib.parse.unquote(urllib.parse.urlsplit(u).path)
        if path.startswith('/') or not (S/path).is_file():errors.append((p['title'],'missing local reference',u))
    for g in s.select('.migration-gallery'):
        galleries+=1;urls=[a['href'] for a in g.select('a[href]')];photos+=len(urls)
        if len(urls)!=len(set(urls)):errors.append((p['title'],'duplicate gallery photos'))
    f=B/(p['id']+'.html')
    if f.exists():
        source=BeautifulSoup(f.read_text(encoding='utf-8'),'html.parser')
        expected=[len(g.select('.wslide-link-thumbnail img')) or len(g.select('.wslide-slides img')) for g in source.select('.wslide')]
        actual=[len(g.select('a')) for g in s.select('.migration-gallery')]
        if expected!=actual:errors.append((p['title'],'gallery count',expected,actual))
for u,a in assets.items():
    if not a['ok']:continue
    f=S/a['path'];data=f.read_bytes()
    if hashlib.sha256(data).hexdigest()!=a['sha256']:errors.append((f.name,'hash mismatch'))
    if f.suffix=='.pdf':
        pdfs+=1
        if not data.startswith(b'%PDF-'):errors.append((f.name,'invalid PDF'))
    if f.suffix in ['.doc','.docx','.ppt','.pptx','.xls','.xlsx']:documents+=1
    if f.suffix in ['.jpg','.jpeg','.png','.gif']:
        try:
            with Image.open(f) as image:image.verify()
        except Exception as ex:errors.append((f.name,'invalid image',str(ex)))
report={'pages':len(generated),'galleries':galleries,'gallery_photos':photos,'saved_assets':sum(a['ok'] for a in assets.values()),'unavailable_assets':sum(not a['ok'] for a in assets.values()),'pdf_files':pdfs,'office_files':documents,'errors':errors}
(ROOT/'docs'/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2));assert not errors
