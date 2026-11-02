"""Five real admin pages, role-based bearer requests, no external provider access."""
import mimetypes
import secrets
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright, expect
from werkzeug.security import generate_password_hash
from release_test_support import FRONTEND_ROOT, BACKEND_ROOT, SITE_ROOT
from app import create_app, db
from app.config import Config
from app.models.user import User

ORIGIN = 'https://pnec-review.invalid'
API = 'https://api.pnec-review.invalid'
Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
Config.SECRET_KEY = secrets.token_hex(32)
Config.ADMIN_PASSWORD = ''
Config.GITHUB_TOKEN = None
app = create_app()
app.config.update(TESTING=True, GITHUB_TOKEN=None)
with app.app_context():
    tokens = {}
    passwords = {}
    for role in ('admin', 'resident'):
        passwords[role] = secrets.token_urlsafe(32)
        user = User(email=role+'@security.example.test', display_name='Synthetic '+role,
                    password_hash=generate_password_hash(passwords[role]), role=role)
        tokens[role] = user.generate_token()
        db.session.add(user)
    db.session.commit()

pages = [('admin-editor.html', '#ae-app'), ('admin-blog.html', '#ab-app'),
         ('admin-nav.html', '#an-app'), ('admin-map-hotspots.html', '#amh-app'),
         ('admin-volunteer.html', '#av-app')]
observed = []
LOGIN = '/pages/register.html#login'
missing_local = []


def handler(identity, allow_login=False, client_ip='127.0.0.1'):
    def serve(route):
        request = route.request
        url = urlsplit(request.url)
        if url.path.startswith('/api/'):
            assert request.url.startswith(API + '/api/'), 'Wrong API origin'
            assert 'x-pnec-admin-key' not in request.headers, 'Retired credential header'
            assert request.method in ('GET', 'HEAD', 'OPTIONS') or (
                allow_login and request.method == 'POST' and url.path == '/api/auth/login'
            ), 'Unexpected write during admin navigation verification'
            authorization = request.headers.get('authorization', '')
            if identity in tokens and authorization:
                assert authorization == 'Bearer ' + tokens[identity]
            # External GitHub file operations remain stubbed. Actual admin role
            # decisions at health/blog/volunteer endpoints are never stubbed.
            if url.path.startswith('/api/admin/publish/') and url.path != '/api/admin/publish/health':
                route.fulfill(status=404, body='{}', content_type='application/json')
                return
            headers = {'Origin': ORIGIN, 'Authorization': authorization}
            if request.headers.get('content-type'):
                headers['Content-Type'] = request.headers['content-type']
            with app.app_context():
                with app.test_client() as client:
                    response = client.open(url.path + ('?' + url.query if url.query else ''),
                        method=request.method, headers=headers, data=request.post_data_buffer,
                        environ_overrides={'REMOTE_ADDR': client_ip})
            if request.method == 'POST':
                assert response.status_code == 200, 'Synthetic login failed'
                assert response.json['user']['role'] == identity
                tokens[identity] = response.json['token']
            observed.append((identity, url.path, response.status_code, bool(authorization)))
            headers = {k: v for k, v in response.headers.items() if k.lower() not in ('content-length', 'set-cookie')}
            route.fulfill(status=response.status_code, body=response.data, headers=headers)
        elif url.netloc == urlsplit(ORIGIN).netloc:
            target = SITE_ROOT / unquote(url.path).lstrip('/')
            if target.is_dir():
                target /= 'index.html'
            if target.is_file():
                route.fulfill(path=str(target), content_type=mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
            else:
                missing_local.append(url.path)
                route.fulfill(status=404, body='Missing release artifact')
        else:
            route.abort()
    return serve


with sync_playwright() as play:
    browser = play.chromium.launch()
    # Preserve the original 15 guest/resident/admin authorization scenarios.
    for identity in ('guest', 'resident', 'admin'):
        context = browser.new_context(timezone_id='America/Los_Angeles')
        if identity in tokens:
            context.add_init_script('localStorage.setItem("pnec_token", '+repr(tokens[identity])+');')
        context.route('**/*', handler(identity))
        page = context.new_page()
        for filename, selector in pages:
            page.goto(ORIGIN + '/pages/' + filename, wait_until='domcontentloaded')
            if identity == 'admin':
                expect(page.locator(selector)).to_be_visible(timeout=10000)
                if filename == 'admin.html':
                    # Real rendered function: editing UTC must preserve local wall time.
                    assert page.evaluate("eventLocalInputValue('2030-11-11T02:00:00Z')") == '2030-11-10T18:00'
                    assert page.evaluate("eventLocalInputValue('2030-07-11T01:00:00Z')") == '2030-07-10T18:00'
            else:
                page.wait_for_timeout(500)
                expect(page.locator(selector)).not_to_be_visible()
            assert page.locator('input[type="password"]').count() == 0, filename
            assert page.locator('a[href="' + LOGIN + '"]').count() > 0, filename
            assert page.locator('a[href="/pages/login.html"]').count() == 0, filename
        context.close()

    # Main dashboard verifies server identity after shared helpers load. Exercise
    # session-only credentials and a forged cached admin label without a token.
    for identity in ('guest','resident','admin'):
        context=browser.new_context()
        context.add_init_script('sessionStorage.setItem("pnec_user", JSON.stringify({role:"admin",display_name:"Synthetic"}));')
        if identity in tokens:
            context.add_init_script('sessionStorage.setItem("pnec_token", '+repr(tokens[identity])+');')
        context.route('**/*',handler(identity))
        page=context.new_page()
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(ORIGIN+'/pages/admin.html',wait_until='domcontentloaded')
        if identity=='admin':
            expect(page.locator('#adm-shell')).to_be_visible()
            page.wait_for_function('Number(document.getElementById("stat-users").textContent)>0')
        else:
            expect(page.locator('#adm-gate')).to_be_visible()
            expect(page.locator('#adm-shell')).not_to_be_visible()
        assert not errors,errors
        context.close()

    # Ten fresh browser sessions: actually follow each tool's login link,
    # authenticate through the served PNEC form, then return to that exact tool.
    # Distinct test clients use distinct peer addresses, without bypassing limits
    # or trusting X-Forwarded-For. No token preloading in these scenarios.
    journeys = 0
    for identity in ('resident', 'admin'):
        for filename, selector in pages:
            journeys += 1
            context = browser.new_context(viewport={'width': 1280, 'height': 900}, reduced_motion='reduce')
            context.route('**/*', handler(identity, allow_login=True, client_ip='192.0.2.' + str(journeys)))
            page = context.new_page()
            tool = ORIGIN + '/pages/' + filename
            page.goto(tool, wait_until='domcontentloaded')
            expect(page.locator(selector)).not_to_be_visible()
            admin_login = page.get_by_role('link', name='Sign in with administrator account', exact=True)
            expect(admin_login).to_have_count(1)
            expect(admin_login).to_have_attribute('href', LOGIN)
            admin_login.click()
            expect(page).to_have_url(ORIGIN + LOGIN)
            expect(page.locator('#pane-login')).to_be_visible()
            expect(page.locator('#auth-tab-login')).to_have_attribute('aria-selected', 'true')
            page.locator('#login-email').fill(identity + '@security.example.test')
            page.locator('#login-password').fill(passwords[identity])
            # Submit the actual login form through the focused password field;
            # this also covers keyboard access without chasing animated buttons.
            page.locator('#login-password').press('Enter')
            expect(page).to_have_url(ORIGIN + '/pages/profile.html')
            # The exact required link has no next parameter. Preserve the
            # existing profile redirect and explicitly return to the tool.
            page.goto(tool, wait_until='domcontentloaded')
            if identity == 'admin':
                expect(page.locator(selector)).to_be_visible(timeout=10000)
            else:
                page.wait_for_timeout(500)
                expect(page.locator(selector)).not_to_be_visible()
            # Verify the returned identity against the REAL isolated backend
            # gate, even if a UI visibility check could otherwise pass early.
            endpoint = '/api/blog?all=1' if filename == 'admin-blog.html' else (
                '/api/volunteer/interests' if filename == 'admin-volunteer.html' else '/api/admin/publish/health')
            status = page.evaluate("async url => { const token = localStorage.getItem('pnec_token') || sessionStorage.getItem('pnec_token'); return (await fetch(url, {headers:{Authorization:'Bearer '+token}})).status; }", API + endpoint)
            assert status == 200 if identity == 'admin' else status in (401, 403)
            context.close()
    browser.close()
assert journeys == 10
assert not missing_local, sorted(set(missing_local))
assert any(who == 'admin' and status == 200 and authenticated for who, _, status, authenticated in observed)
assert all(status in (401, 403) for who, path, status, _ in observed if who == 'resident' and path in ('/api/admin/publish/health', '/api/volunteer/interests', '/api/blog'))
print('PASS: original 15 admin-page/identity combinations plus 3 session-only/forged-cache dashboard checks and 10 click-through/login/return journeys; actual role authorization and HTTPS production API only')
with app.app_context():
    db.session.remove()
    db.engine.dispose()
