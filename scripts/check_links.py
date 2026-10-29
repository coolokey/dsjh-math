import concurrent.futures,json,pathlib,urllib.parse
import requests
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
B=ROOT/'backup'
urls=set()
pages=json.loads((B/'pages.json').read_text(encoding='utf-8'))
for p in pages:
    if p.get('url'): urls.add(p['url'])
for f in B.glob('*.html'):
    s=BeautifulSoup(f.read_text(encoding='utf-8'),'html.parser')
    for e in s.select('#main-wrap a[href],#main-wrap iframe[src]'):
        u=e.get('href') or e.get('src')
        if u.startswith('//'):u='https:'+u
        if u.startswith('http') and not any(t in u for t in ['weebly-link','dsjhmath.weebly.com','preview.editmysite','/uploads/']):urls.add(u)
def check(u):
    try:
        with requests.get(u,timeout=(6,12),stream=True,allow_redirects=True) as r:
            result={'status':r.status_code,'final_url':r.url,'state':'ok' if r.status_code<400 else 'invalid' if r.status_code in [404,410] else 'unverified'}
    except requests.RequestException as ex:result={'status':'network-error','state':'unverified','reason':type(ex).__name__}
    if result['state']!='ok' and u.startswith('http://'):
        try:
            with requests.get('https://'+u[7:],timeout=(6,12),stream=True,allow_redirects=True) as r:
                if r.status_code<400:result={'status':r.status_code,'final_url':r.url,'state':'ok','upgraded':True}
        except requests.RequestException:pass
    return u,result
out={}
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
    for i,(u,r) in enumerate(pool.map(check,sorted(urls)),1):
        out[u]=r
        (B/'link-report.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
        if i%20==0:print(f'{i}/{len(urls)}',flush=True)
print({s:sum(x['state']==s for x in out.values()) for s in ['ok','invalid','unverified']})
