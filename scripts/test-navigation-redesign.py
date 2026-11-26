"""Read-only browser regression for the OCS redesign. No writes to the API.
Run: python scripts/test-navigation-redesign.py --base-url http://127.0.0.1:8765/pnec-frontend-review/ --output-dir /tmp/pnec-evidence
API responses are mocked for repeatable layout/interaction checks; --live allows
real requests for a second deployed-site pass. Authentication rendering uses a
synthetic cached resident; this does not claim backend authentication validation.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit, urljoin
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url', required=True)
parser.add_argument('--output-dir', type=Path, required=True)
parser.add_argument('--live', action='store_true')
args = parser.parse_args()
base = args.base_url.rstrip('/') + '/'
args.output_dir.mkdir(parents=True, exist_ok=True)
routes = ['', 'pages/about.html', 'pages/preparedness-resources.html',
          'pages/volunteer.html', 'pages/community-events-and-activities.html',
          'pages/find-your-neighborhood.html', 'pages/programs-and-services.html',
          'pages/contact.html', 'pages/register.html', 'pages/checklist.html',
          'pages/kit.html', 'pages/profile.html', 'pages/gallery.html',
          'pages/blog.html', 'pages/forgot-password.html']
report = []
def mock_api(route):
    path = urlsplit(route.request.url).path
    data = {}
    if path.endswith('/health'): data = {'status':'ok','review':True}
    elif path.endswith('/ready'): data = {'status':'ready'}
    elif '/events' in path: data = {'events':[]}
    elif '/neighborhood' in path: data = {'neighborhoods':[]}
    elif path.endswith('/preparedness/quiz'): data = {'questions':[]}
    elif path.endswith('/weekly-tip'): data = {'tip': None}
    elif path.endswith('/theme.css'):
        route.fulfill(status=200,content_type='text/css',body=''); return
    route.fulfill(status=200,content_type='application/json',body=json.dumps(data))

def close_home_welcome(page):
    # Existing helper auto-opens specifically at / on window.load. Dismiss it
    # explicitly for hero/navigation checks; helper interactions are tested below.
    page.wait_for_load_state('load')
    close = page.locator('#pnec-bot-close')
    if close.is_visible():
        close.click()

def open_mobile(page, width):
    if width <= 1050 and page.locator('.nav-trigger').get_attribute('aria-expanded') != 'true':
        page.locator('.nav-trigger').click()

with sync_playwright() as play:
    browser = play.chromium.launch()
    for width, columns in [(1440,4),(1280,4),(1024,2),(768,2),(390,1),(320,1)]:
        context = browser.new_context(viewport={'width':width,'height':900}, has_touch=width<=1050)
        if not args.live:
            context.route('**/*', lambda r: r.continue_() if r.request.url.startswith(base)
                          else mock_api(r) if '/api/' in r.request.url else r.abort())
        page=context.new_page(); errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        reference=None; link_reference=None
        for route in routes:
            print('Checking',width,route or 'home',flush=True)
            response=page.goto(base+route,wait_until='domcontentloaded');close_home_welcome(page)
            assert response.status==200,(width,route,response.status)
            page.wait_for_timeout(120)
            header=page.locator('#pnec-site-header')
            geometry=header.bounding_box()
            assert geometry['y']==0 and geometry['height']==80,(width,route,geometry)
            if reference is None:reference=geometry
            assert geometry==reference,(width,route,'top bar shifted')
            primary=page.locator('.pnec-primary > a')
            assert primary.all_text_contents()==['Home','Prepare','Resources','Community','Profile']
            category=header.get_attribute('data-category')
            assert page.locator('[data-context]:not([hidden])').count()==(0 if category=='home' else 1)
            assert page.locator('#navbar-login-item').is_visible()
            assert page.locator('#navbar-login-item').get_attribute('href').endswith('/pages/register.html#login')
            assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),(width,route,'overflow')
            if width>1050:
                positions=primary.evaluate_all('(els)=>els.map(e=>{const b=e.getBoundingClientRect();return [b.x,b.y,b.width,b.height]})')
                if link_reference is None:link_reference=positions
                assert positions==link_reference,(width,route,'primary links shifted')
                if category=='home':
                    assert page.locator('.pnec-context').count()==0
                    assert page.locator('body').evaluate('(e)=>getComputedStyle(e).paddingLeft')=='0px'
                else:
                    sidebar=page.locator('.pnec-context').bounding_box()
                    assert sidebar['y']==80 and sidebar['x']==0 and sidebar['width']==264
            if not route:
                cards=page.locator('.pnec-action');assert cards.count()==4
                boxes=[card.bounding_box() for card in cards.all()]
                assert len({round(b['y']) for b in boxes})==4//columns
                assert len({round(b['height']) for b in boxes})==1
                for card in cards.all():
                    card.scroll_into_view_if_needed()
                    def box():return card.evaluate('(e)=>{const b=e.getBoundingClientRect();return [b.x+scrollX,b.y+scrollY,b.width,b.height].map(v=>Math.round(v*100)/100)}')
                    before=box();card.hover();assert box()==before;card.focus();assert box()==before
                    assert page.request.get(urljoin(base,card.get_attribute('href').split('#')[0])).status==200
            assert not errors,(width,route,errors)
        # Every primary category follows its existing landing route and shows only its sidebar.
        for category in ['home','prepare','resources','community','profile']:
            open_mobile(page,width)
            page.locator(f'[data-category-link="{category}"]').click()
            page.wait_for_load_state('load');close_home_welcome(page)
            assert page.locator('#pnec-site-header').get_attribute('data-category')==category
            if category=='home':
                assert page.locator('.pnec-context').count()==0
            else:
                assert page.locator(f'[data-context="{category}"]').get_attribute('hidden') is None
            category=header.get_attribute('data-category')
            assert page.locator('[data-context]:not([hidden])').count()==(0 if category=='home' else 1)
            assert page.locator('#navbar-login-item').is_visible()
            assert page.locator('#navbar-login-item').get_attribute('href').endswith('/pages/register.html#login')
            open_mobile(page,width)
            assert page.locator(f'[data-category-link="{category}"]').get_attribute('aria-current')=='true'
            assert page.locator('.site-nav').evaluate('(e)=>e.scrollWidth<=e.clientWidth')
            if width<=1050:page.keyboard.press('Escape')
        # Profile sidebar is public; signed-out accounts receive an explicit login prompt.
        assert page.locator('.pnec-profile-welcome h1').inner_text()=='Your PNEC dashboard'
        open_mobile(page,width)
        assert page.locator('[data-context="profile"] nav a').all_text_contents()==['Dashboard','Preferences','Account Settings']
        home=page.locator('[data-category-link="home"]');home.focus();home.press('ArrowRight')
        assert page.locator('[data-category-link="prepare"]').evaluate('(e)=>e===document.activeElement')
        page.keyboard.press('End');assert page.locator('[data-category-link="profile"]').evaluate('(e)=>e===document.activeElement')
        if width<=1050:
            assert page.locator('main').evaluate('(e)=>e.inert')
            focusable=page.locator('#pnec-site-header').locator('a,button,summary').evaluate_all('(els)=>els.filter(e=>e.getClientRects().length && !e.disabled).map(e=>e.id)')
            page.keyboard.press('Escape')
            assert page.locator('.nav-trigger').evaluate('(e)=>e===document.activeElement')
            assert not page.locator('main').evaluate('(e)=>e.inert')
            open_mobile(page,width)
            backdrop=page.locator('.pnec-drawer-backdrop');backdrop.click(position={'x':backdrop.bounding_box()['width']-8,'y':650})
            assert page.locator('.nav-trigger').get_attribute('aria-expanded')=='false'
        # Existing helper interaction and mode checks remain independent of navigation.
        page.locator('#pnec-bot-fab').click();page.locator('#pnec-bot-panel').wait_for(state='visible')
        assert page.locator('#pnec-bot-panel').bounding_box()['y']>=80
        for mode in ['expand','modal']:
            control=page.locator('#pnec-bot-'+mode)
            if control.is_visible():control.click();page.wait_for_timeout(300);assert page.locator('#pnec-bot-panel').bounding_box()['y']>=80
        page.locator('#pnec-bot-close').click();assert page.locator('#pnec-bot-panel').is_hidden()
        # Check every contextual internal destination without production requests.
        for link in page.locator('[data-context-link]').all():
            assert page.request.get(urljoin(base,link.get_attribute('href').split('#')[0])).status==200
        assert not errors,errors
        report.append({'width':width,'routes':len(routes),'categories':5,'header':reference,'columns':columns,'errors':errors,'passed':True})
        context.close()
    # Existing role-aware IDs use the existing auth worker, not a new permission model.
    for role in ['resident','coordinator','staff','admin']:
        context=browser.new_context()
        user={'id':999,'display_name':'Synthetic navigation fixture','email':'fixture@example.test','role':role}
        def role_api(route):
            if route.request.url.startswith(base):route.continue_()
            elif urlsplit(route.request.url).path.endswith('/auth/me'):route.fulfill(status=200,content_type='application/json',body=json.dumps({'user':user}))
            else:mock_api(route)
        context.route('**/*',role_api)
        page=context.new_page();page.goto(base+'pages/profile.html',wait_until='networkidle')
        assert page.locator('.profile-name').inner_text().startswith(user['display_name'])
        assert page.locator('#account-settings').count()==1
        page.locator('#navbar-auth-logged-in > details > summary').click()
        assert page.locator('#nav-media-link').is_visible()==(role!='resident')
        assert page.locator('#nav-dashboard-link').is_visible()==(role in ['staff','admin'])
        assert page.locator('#nav-admin-link').is_visible()==(role=='admin')
        if role=='admin':
            page.locator('#nav-admin-link summary').click();assert page.get_by_role('link',name='Admin Dashboard',exact=True).is_visible()
            page.keyboard.press('Escape');assert not page.locator('#nav-admin-link details').evaluate('(e)=>e.open')
        context.close()
    browser.close()
(args.output_dir/'results.json').write_text(json.dumps(report,indent=2))
print(f'PASS: {len(routes)*len(report)} route/viewport checks, five categories/contextual links, keyboard/drawer, four roles and helper modes.')
