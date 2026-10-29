import json,pathlib,re,unittest
from bs4 import BeautifulSoup

ROOT=pathlib.Path(__file__).resolve().parents[1]
S=ROOT/'site'
PAGES=json.loads((S/'pages.json').read_text(encoding='utf-8'))
BASE=json.loads((ROOT/'tests/baseline.json').read_text(encoding='utf-8'))
def normalize(s):return re.sub(r'[\s\u200b\ufeff]+','',s)

class RedesignTests(unittest.TestCase):
    def test_semantic_shell_and_current_page_for_every_route(self):
        for p in PAGES:
            with self.subTest(page=p['title']):
                s=BeautifulSoup((S/p['file']).read_text(encoding='utf-8'),'html.parser')
                self.assertIsNotNone(s.select_one('header.site-header'))
                self.assertIsNotNone(s.select_one('main#main-wrap'))
                self.assertEqual(s.select_one('.migration-nav [aria-current="page"]')['href'],p['file'])
                self.assertIsNotNone(s.select_one('a.skip-link[href="#main-wrap"]'))

    def test_existing_text_and_assets_remain_available(self):
        for p in PAGES:
            with self.subTest(page=p['title']):
                s=BeautifulSoup((S/p['file']).read_text(encoding='utf-8'),'html.parser')
                main=s.select_one('#main-wrap');text=normalize(main.get_text(' '))
                for original in BASE[p['file']]['texts']:
                    self.assertIn(normalize(original),text,original)
                links={e.get('href') for e in main.select('a[href]')}
                self.assertTrue(set(BASE[p['file']]['files']).issubset(links))
                self.assertEqual(BASE[p['file']]['photos'],[e['href'] for e in main.select('.migration-gallery a')])

    def test_pdfs_are_closed_and_not_loaded_before_request(self):
        count=0
        for p in PAGES:
            s=BeautifulSoup((S/p['file']).read_text(encoding='utf-8'),'html.parser')
            for embed in s.select('embed[type="application/pdf"]'):
                count+=1
                details=embed.find_parent('details')
                self.assertIsNotNone(details)
                self.assertNotIn('open',details.attrs)
                self.assertFalse(embed.get('src'))
                self.assertTrue((S/embed['data-pdf-src']).is_file())
        self.assertGreater(count,0)

    def test_home_has_accessible_history(self):
        s=BeautifulSoup((S/'index.html').read_text(encoding='utf-8'),'html.parser')
        self.assertIsNotNone(s.select_one('details.news-archive > summary'))
        self.assertEqual(4,len(s.select('.quick-resources a')))

if __name__=='__main__':unittest.main()

