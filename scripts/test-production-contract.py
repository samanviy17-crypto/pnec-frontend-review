"""Check root-domain navigation and API targets without contacting production."""
from html.parser import HTMLParser
import json
from pathlib import Path
import secrets
from urllib.parse import unquote, urljoin, urlsplit

from playwright.sync_api import sync_playwright
from release_test_support import FRONTEND_ROOT, BACKEND_ROOT, SITE_ROOT
from app import create_app, db
from app.config import Config
from app.services import risk_service

ORIGIN = 'https://pnec-review.invalid'
API = 'https://api.pnec-review.invalid'
assert 'baseurl: ""' in (FRONTEND_ROOT / '_config.yml').read_text()
assert not (FRONTEND_ROOT / 'CNAME').exists(), 'No active domain config in review snapshot'
assert not (FRONTEND_ROOT / '_config.pages.yml').exists()
assert not (SITE_ROOT / '.env').exists()
for source in (FRONTEND_ROOT / 'assets').rglob('*.scss'):
    if source.read_text().startswith('---'):
        assert not source.with_suffix('.css').exists(), f'Duplicate CSS output: {source}'

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.links.extend(value for key, value in attrs
                          if key in ('src', 'href') and value)


pages = ['/', '/pages/register.html', '/pages/profile.html', '/pages/forgot-password.html',
         '/pages/reset-password.html', '/pages/checklist.html', '/pages/volunteer.html',
         '/pages/preparedness-resources.html', '/donation-form/', '/pages/dashboard.html',
         '/pages/community-events-and-activities.html']
checked = set()
for path in pages:
    file = SITE_ROOT / path.lstrip('/')
    if file.is_dir():
        file /= 'index.html'
    assert file.is_file(), path
    markup = file.read_text()
    assert '{{' not in markup and '{%' not in markup, path
    links = Links()
    links.feed(markup)
    for link in links.links:
        url = urlsplit(urljoin(ORIGIN + path, link))
        if url.netloc != urlsplit(ORIGIN).netloc:
            continue
        target = SITE_ROOT / unquote(url.path).lstrip('/')
        assert target.exists(), (path, link)
        checked.add(url.path)
print(f'PASS: {len(pages)} root-domain pages and {len(checked)} local asset/navigation paths; no duplicate CSS output')

# Browser sees the production origins, but every request is fulfilled locally.
Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
Config.SECRET_KEY = secrets.token_hex(32)
Config.ADMIN_PASSWORD = ''
app = create_app()
app.config.update(TESTING=True)
risk_service.get_risk_assessment = lambda *args, **kwargs: {
    'fire_level': 'LOW', 'heat_level': 'LOW', 'flood_level': 'LOW',
    'fire_score': 1, 'heat_score': 1, 'flood_score': 1,
    'updated_at': 'synthetic release verification', 'is_stale': False}
requests = []
wrong = []
missing = []
try:
    with sync_playwright() as play:
        browser = play.chromium.launch()
        context = browser.new_context()

        def serve(route):
            request = route.request
            url = urlsplit(request.url)
            if url.path.startswith('/api/'):
                requests.append(request.url)
                if url.scheme != 'https' or url.netloc != urlsplit(API).netloc:
                    wrong.append(request.url)
                    route.abort()
                    return
                assert request.method in ('GET', 'HEAD', 'OPTIONS'), 'Unexpected write in guest contract check'
                with app.test_client() as client:
                    response = client.open(url.path + ('?' + url.query if url.query else ''),
                        method=request.method, headers={'Origin': ORIGIN})
                headers = {key: value for key, value in response.headers.items()
                           if key.lower() not in ('content-length', 'set-cookie')}
                route.fulfill(status=response.status_code, body=response.data, headers=headers)
            elif url.netloc == urlsplit(ORIGIN).netloc:
                file = SITE_ROOT / unquote(url.path).lstrip('/')
                if file.is_dir():
                    file /= 'index.html'
                if file.is_file():
                    route.fulfill(path=str(file))
                else:
                    missing.append(url.path)
                    route.fulfill(status=404, body='Missing release asset')
            else:
                route.abort()  # External scripts/providers are not part of this check.

        context.route('**/*', serve)
        page = context.new_page()
        for path in pages + ['/pages/admin-nav.html', '/pages/admin-map-hotspots.html']:
            page.goto(ORIGIN + path, wait_until='domcontentloaded')
            page.wait_for_timeout(350)
        assert requests, 'No API requests observed'
        assert not wrong, wrong
        assert not missing, sorted(set(missing))
        print(f'PASS: {len(requests)} browser API requests all target {API}; no production network access')
        browser.close()
finally:
    with app.app_context():
        db.session.remove()
        db.engine.dispose()
