"""Release boundaries: authentication gate and production deployment isolation."""
import pathlib, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class ReleaseTests(unittest.TestCase):
    def test_admin_fails_closed_until_real_site_is_configured(self):
        script = (ROOT/'site/admin/bootstrap.js').read_text(encoding='utf-8')
        self.assertIn('turbo_site_id', script)
        self.assertIn('CMS_MANUAL_INIT', script)
        self.assertIn('尚未啟用', (ROOT/'site/admin/index.html').read_text(encoding='utf-8'))
        self.assertNotIn("name: test", (ROOT/'site/admin/config.yml').read_text(encoding='utf-8'))

    def test_workflow_never_deploys_pull_requests(self):
        workflow = (ROOT/'.github/workflows/pages.yml').read_text(encoding='utf-8')
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn("github.event_name != 'pull_request'", workflow)
        self.assertIn('needs: build', workflow)
        self.assertIn('scripts/build.py', workflow)
        self.assertNotIn('scripts/migrate_legacy.py', workflow)

if __name__ == '__main__': unittest.main()
