import concurrent.futures,hashlib,json,pathlib,subprocess
import requests
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE='https://coolokey.github.io/dsjh-math/'
pages=json.loads((ROOT/'site/pages.json').read_text(encoding='utf-8'))
commit=subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()
targets={p['file'] for p in pages}|{'design.css','design.js','pages.json'}
targets.update(p.relative_to(ROOT/'site').as_posix() for p in (ROOT/'site/assets').rglob('*') if p.suffix in ['.pdf','.doc','.docx'])
targets.update('admin/'+p.name for p in (ROOT/'site/admin').iterdir() if p.is_file())
photo_page=BeautifulSoup((ROOT/'site/page-259717796982727694.html').read_text(encoding='utf-8'),'html.parser')
targets.add(photo_page.select_one('.migration-gallery a')['href'])
def check(path):
    try:
        r=requests.get(BASE+path+'?v='+commit[:12],timeout=(10,35))
        local=(ROOT/'site'/path).read_bytes()
        remote=r.content
        if pathlib.Path(path).suffix in ['.html','.css','.js','.json','.yml']:
            local=local.replace(b'\r\n',b'\n');remote=remote.replace(b'\r\n',b'\n')
        return {'path':path,'status':r.status_code,'matches_local':r.status_code==200 and hashlib.sha256(remote).digest()==hashlib.sha256(local).digest()}
    except requests.RequestException as ex:return {'path':path,'error':type(ex).__name__,'matches_local':False}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(check,sorted(targets)))
report={'url':BASE,'branch':'main','deployment':'GitHub Actions','deployment_commit':commit,'checks':len(results),'all_passed':all(x['matches_local'] for x in results),'results':results}
(ROOT/'docs/deployment-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'url':BASE,'checks':len(results),'all_passed':report['all_passed'],'failed':[x for x in results if not x['matches_local']]},ensure_ascii=False,indent=2))
assert report['all_passed']
