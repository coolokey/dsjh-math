import json,pathlib,sys,tempfile,unittest,shutil
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
try:
    from content import load_content, ContentError, render_blocks
    from build import build
except ImportError:
    load_content=build=None
    class ContentError(ValueError):pass

class ContentTests(unittest.TestCase):
    def test_uploaded_pdf_blocks_have_deferred_preview_and_download(self):
        file='/dsjh-math/assets/uploads/calendar.PDF'
        soup=BeautifulSoup(render_blocks([dict(type='document',file=file,caption='下載新行事曆')]),'html.parser')
        self.assertEqual(soup.select_one('a.document-link')['href'],'assets/uploads/calendar.PDF')
        details=soup.select_one('details.pdf-preview')
        self.assertIsNotNone(details)
        self.assertFalse(details.has_attr('open'))
        self.assertEqual(details.summary.get_text(),'展開文件預覽')
        self.assertEqual(details.embed['data-pdf-src'],'assets/uploads/calendar.PDF')
        self.assertFalse(details.embed.has_attr('src'))
        for other in ('assets/lesson.docx','https://example.com/calendar.pdf'):
            self.assertNotIn('<embed',render_blocks([dict(type='document',file=other)]))

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT);self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name)
        shutil.copytree(ROOT/'content',self.root/'content') if (ROOT/'content').exists() else (self.root/'content').mkdir()
        (self.root/'site').mkdir()
        self.assets=ROOT/'site'
    def write_page(self,id='test-page',**kwargs):
        data=dict(id=id,title='測試頁',parent='',order=999,hidden=False,external=False,body='<p>測試內容</p>',blocks=[])
        data.update(kwargs);p=self.root/'content/pages'/f'{id}.json';p.parent.mkdir(exist_ok=True);p.write_text(json.dumps(data),encoding='utf-8');return p
    def test_new_blocks_can_be_placed_before_or_after_existing_content(self):
        for position in ('before','after'):
            self.write_page(body='<p>OLD_CONTENT</p>',blocks_position=position,blocks=[dict(type='text',text='NEW_CONTENT')])
            build(self.root/'content',self.root/'site',asset_root=self.assets)
            text=BeautifulSoup((self.root/'site/page-test-page.html').read_text(encoding='utf-8'),'html.parser').select_one('article').get_text()
            self.assertEqual(text.index('NEW_CONTENT')<text.index('OLD_CONTENT'),position=='before')
        self.write_page(blocks_position='invalid')
        with self.assertRaises(ContentError):load_content(self.root/'content',self.assets)
    def test_independent_build_and_edit_hide_delete_restore(self):
        self.assertIsNotNone(build,'formal content builder is missing')
        page=self.write_page(parent=None);out=self.root/'site';build(self.root/'content',out,asset_root=self.assets)
        route=out/'page-test-page.html';self.assertIn('測試內容',route.read_text(encoding='utf-8'))
        self.write_page(title='改名',hidden=True,body='<p>修改成功</p>');build(self.root/'content',out,asset_root=self.assets)
        self.assertIn('修改成功',route.read_text(encoding='utf-8'));self.assertNotIn('page-test-page.html',(out/'index.html').read_text(encoding='utf-8'))
        saved=page.read_text();page.unlink();(out/'unmanaged.html').write_text('keep');build(self.root/'content',out,asset_root=self.assets)
        self.assertFalse(route.exists());self.assertTrue((out/'unmanaged.html').exists())
        page.write_text(saved);build(self.root/'content',out,asset_root=self.assets);self.assertTrue(route.exists())
    def test_invalid_hierarchy_and_duplicate_identity(self):
        self.assertIsNotNone(load_content,'content loader is missing')
        for fields in [dict(parent='missing'),dict(parent='test-page')]:
            self.write_page(**fields)
            with self.assertRaises(ContentError):load_content(self.root/'content',self.assets)
        self.write_page(parent='second');self.write_page(id='second',parent='test-page')
        with self.assertRaises(ContentError):load_content(self.root/'content',self.assets)
        self.write_page(parent='',hidden=True);self.write_page(id='second',parent='test-page')
        with self.assertRaises(ContentError):load_content(self.root/'content',self.assets)
        self.write_page(parent='');self.write_page(id='second',parent='test-page');self.write_page(id='third',parent='second')
        with self.assertRaises(ContentError):load_content(self.root/'content',self.assets)
        (self.root/'content/pages/third.json').unlink()
        self.write_page(parent='');self.write_page(id='second',parent='')
        shutil.copy(self.root/'content/pages/test-page.json',self.root/'content/pages/duplicate.json')
        with self.assertRaises(ContentError):load_content(self.root/'content',self.assets)
    def test_unsafe_html_and_missing_files_fail(self):
        self.assertIsNotNone(load_content,'content loader is missing')
        for body in ['<script>alert(1)</script>','<embed src="https://example.com/evil.html" type="text/html">','<input>','<textarea></textarea>','<select></select>','<svg><animate attributeName="href" values="javascript:alert(1)"></animate></svg>','<math></math>','<img src="assets/missing.png">','<a href="javascript:alert(1)">x</a>','<p onclick="evil()">x</p>','<p style="background:url(javascript:evil())">x</p>','<iframe srcdoc="evil"></iframe>','<a href="page-missing.html">missing</a>']:
            self.write_page(body=body)
            with self.subTest(body=body),self.assertRaises(ContentError):load_content(self.root/'content',self.assets)
    def test_home_news_order_and_unsafe_links(self):
        self.assertIsNotNone(build)
        home=self.root/'content/home.json';data=json.loads(home.read_text(encoding='utf-8'))
        data['news']=[dict(date='2026-10-30',title='第一則新公告',text='**最新內容**',link='https://example.com'),dict(date='2026-10-29',title='第二則新公告',text='',link='')]
        home.write_text(json.dumps(data),encoding='utf-8');build(self.root/'content',self.root/'site',asset_root=self.assets)
        s=(self.root/'site/index.html').read_text(encoding='utf-8')
        self.assertIn('第一則新公告',s);self.assertLess(s.index('第一則新公告'),s.index('第二則新公告'))
        data['news'].reverse();home.write_text(json.dumps(data),encoding='utf-8');build(self.root/'content',self.root/'site',asset_root=self.assets)
        s=(self.root/'site/index.html').read_text(encoding='utf-8');self.assertLess(s.index('第二則新公告'),s.index('第一則新公告'))
        data['news'][0]['link']='javascript:alert(1)';home.write_text(json.dumps(data),encoding='utf-8')
        with self.assertRaises(ContentError):load_content(self.root/'content',self.assets)
    def test_blocks_render_and_home_id_is_fixed(self):
        self.assertIsNotNone(build,'formal content builder is missing')
        self.write_page(blocks=[dict(type='text',text='## 新標題\n\n**粗體**'),dict(type='image',file='assets/test.png',caption='相片說明'),dict(type='document',file='assets/test.pdf',caption='下載教材'),dict(type='gallery',images=[dict(file='assets/test.png',caption='第一張')]),dict(type='video',url='https://www.youtube.com/watch?v=abc12345678')])
        asset_root=self.root/'media';(asset_root/'assets').mkdir(parents=True)
        for n in ['test.png','test.pdf']:(asset_root/'assets'/n).write_bytes(b'test')
        # Existing pages reference real assets; use the actual media root for them.
        for n in ['test.png','test.pdf']:shutil.copy(asset_root/'assets'/n, self.root/n)
        # Add just these fixture files to a copied asset directory using hardlinks.
        shutil.copytree(self.assets/'assets',asset_root/'assets',dirs_exist_ok=True,copy_function=lambda a,b: __import__('os').link(a,b))
        build(self.root/'content',self.root/'site',asset_root=asset_root)
        s=BeautifulSoup((self.root/'site/page-test-page.html').read_text(encoding='utf-8'),'html.parser')
        self.assertIsNotNone(s.select_one('strong'));self.assertEqual(len(s.select('.migration-gallery img')),1)
        home=self.root/'content/home.json';data=json.loads(home.read_text(encoding='utf-8'));data['id']='changed';home.write_text(json.dumps(data),encoding='utf-8')
        with self.assertRaises(ContentError):load_content(self.root/'content',asset_root)
if __name__=='__main__':unittest.main()
