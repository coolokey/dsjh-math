"""Build the published site only from versioned CMS content; no backup dependency."""
import argparse,html,json,pathlib
from bs4 import BeautifulSoup
from content import load_content,render_blocks,render_news,route,safe_url
from layout import render_layout
ROOT=pathlib.Path(__file__).resolve().parents[1]

def build(content_root=None,out=None,asset_root=None):
    content_root=pathlib.Path(content_root or ROOT/'content');out=pathlib.Path(out or ROOT/'site');asset_root=pathlib.Path(asset_root or ROOT/'site')
    pages,aliases=load_content(content_root,asset_root)
    # Validate all source before changing any generated output.
    generated={}
    for p in pages:
        soup=BeautifulSoup(p['body']+'\n'+render_blocks(p['blocks']),'html.parser')
        if p['id']=='394608272104688055' and p.get('news'):
            target=soup.select_one('.home-news') or soup
            target.insert(0,BeautifulSoup(render_news(p['news']),'html.parser'))
        generated[route(p)]=render_layout(p,soup,pages,prepared=True,hero_image=p.get('hero_image','').removeprefix('/dsjh-math/'))
    byid={p['id']:p for p in pages}
    for name,id in aliases.items():
        p=byid[id];dest=route(p);title=html.escape(p['title'])
        generated[name]=f'<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={dest}"><title>{title}</title><a href="{dest}">{title}</a></html>'
    for body in generated.values():
        final=BeautifulSoup(body,'html.parser')
        for node in final.select('a[href],img[src],iframe[src],embed[data-pdf-src]'):
            safe_url(node.get('href',node.get('src',node.get('data-pdf-src',''))),asset_root,set(generated))
    out.mkdir(parents=True,exist_ok=True);manifest=out/'.generated-pages.json'
    previous=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else []
    for name in previous:
        if name not in generated and pathlib.Path(name).name==name and name.endswith('.html'):
            (out/name).unlink(missing_ok=True)
    for name,body in generated.items():(out/name).write_text(body,encoding='utf-8')
    stats=[{k:p[k] for k in ('title','id','parent','external')}|{'file':route(p),'hidden':p['hidden']} for p in pages]
    (out/'pages.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    manifest.write_text(json.dumps(sorted(generated),indent=2)+'\n',encoding='utf-8')
    (out/'.nojekyll').write_text('',encoding='utf-8')
    return stats

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--content',type=pathlib.Path,default=ROOT/'content');parser.add_argument('--out',type=pathlib.Path,default=ROOT/'site');args=parser.parse_args()
    result=build(args.content,args.out);print(json.dumps({'pages':len(result),'source':str(args.content)},ensure_ascii=False))
