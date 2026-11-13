"""Read-only browser regression for the OCS redesign. No writes to the API.
Run: python scripts/test-navigation-redesign.py --base-url http://127.0.0.1:8765/pnec-frontend-review/ --output-dir /tmp/pnec-evidence
API responses are mocked for repeatable layout/interaction checks; --live allows
real requests for a second deployed-site pass. Authentication rendering uses a
synthetic cached resident; this does not claim backend authentication validation.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit
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

with sync_playwright() as play:
    browser = play.chromium.launch()
    for width, columns in [(1440,4),(1280,4),(1024,2),(768,2),(390,1),(320,1)]:
        context = browser.new_context(viewport={'width':width,'height':900}, has_touch=width<=1050)
        if not args.live:
            context.route('**/*', lambda r: r.continue_() if r.request.url.startswith(base)
                          else mock_api(r) if '/api/' in r.request.url
                          else r.abort())
        page = context.new_page()
        errors=[]
        page.on('pageerror', lambda error: errors.append(str(error)))
        reference=None
        for route in routes:
            print('Checking',width,route or 'home',flush=True)
            response=page.goto(base+route,wait_until='domcontentloaded')
            assert response.status == 200, (width,route,response.status)
            page.wait_for_timeout(250)
            geometry=page.locator('#pnec-site-header').evaluate('(e)=>({x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height})')
            assert geometry['y']==0 and geometry['height']==80,(width,route,geometry)
            if reference is None: reference=geometry
            assert geometry==reference,(width,route,'header shifted',reference,geometry)
            assert page.locator('nav[aria-label="Main navigation"]').count()==1
            overflow=page.evaluate('document.documentElement.scrollWidth > innerWidth')
            assert not overflow,(width,route,'horizontal overflow',page.evaluate('document.documentElement.scrollWidth'))
            if not route:
                cards=page.locator('.pnec-action')
                assert cards.count()==4
                boxes=[cards.nth(i).bounding_box() for i in range(4)]
                assert len({round(b['y']) for b in boxes}) == 4//columns,(width,boxes)
                assert len({round(b['height']) for b in boxes})==1,(width,'unequal heights',boxes)
                for i in range(4):
                    card=cards.nth(i); card.scroll_into_view_if_needed(); before=card.bounding_box()
                    card.hover(); assert card.bounding_box()==before
                    card.focus(); assert card.bounding_box()==before
                    assert page.request.get(card.get_attribute('href').split('#')[0] if card.get_attribute('href').startswith('http') else base.split('/pnec-frontend-review/')[0]+card.get_attribute('href').split('#')[0]).status==200
                page.evaluate('document.activeElement.blur(); window.scrollTo(0,0)')
                page.mouse.move(0,0)
                page.screenshot(path=str(args.output_dir/f'home-{width}.png'),full_page=True)
            # Compare navigation link positions after every actual page load.
            if width > 1050:
                positions=page.locator('#pnec-site-header .trigger > .page-link, #pnec-site-header .trigger > .pnec-disclosure > .page-link').evaluate_all('(els)=>els.map(e=>({x:e.getBoundingClientRect().x,y:e.getBoundingClientRect().y,width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height}))')
                if not route: link_reference=positions
                assert positions==link_reference,(width,route,'links shifted')
        # Exercise mouse/touch-style click, keyboard, Escape, and outside dismissal.
        page.goto(base,wait_until='domcontentloaded')
        if width<=1050:
            mobile=page.locator('.nav-trigger'); mobile.tap()
            assert mobile.get_attribute('aria-expanded')=='true'
        prepare=page.locator('#pnec-site-header button[aria-controls="pnec-menu-1"]')
        prepare.click()
        assert prepare.get_attribute('aria-expanded')=='true'
        assert page.locator('.site-nav').evaluate('(e)=>e.scrollWidth <= e.clientWidth'), (width, 'menu overflow')
        page.keyboard.press('Escape')
        assert prepare.get_attribute('aria-expanded')=='false'
        assert prepare.evaluate('(e)=>e===document.activeElement')
        prepare.press('ArrowDown')
        assert page.get_by_role('link',name='Preparedness Checklist',exact=True).evaluate('(e)=>e===document.activeElement')
        page.keyboard.press('Escape')
        prepare.press('Space')
        assert prepare.get_attribute('aria-expanded')=='true'
        page.mouse.click(width-5,850)
        assert prepare.get_attribute('aria-expanded')=='false'
        if width<=1050:
            assert mobile.get_attribute('aria-expanded')=='false'
            mobile.click(); page.keyboard.press('Escape')
            assert mobile.evaluate('(e)=>e===document.activeElement')
            mobile.click()
        # Actual link transition through menu, rather than only URL visits.
        page.get_by_role('button',name='About',exact=True).click()
        page.get_by_role('link',name='About PNEC',exact=True).click()
        page.wait_for_url('**/pages/about.html')
        assert page.locator('#pnec-site-header').bounding_box()['y']==0
        page.screenshot(path=str(args.output_dir/f'about-{width}.png'),full_page=True)
        # Signed-in display must fit the same reserved account slot.
        page.evaluate("localStorage.setItem('pnec_user',JSON.stringify({display_name:'Synthetic Resident',email:'synthetic@example.test',role:'resident'}))")
        page.reload(wait_until='domcontentloaded')
        page.wait_for_timeout(250)
        if width<=1050: page.locator('.nav-trigger').click()
        assert page.get_by_role('button',name='Account',exact=True).is_visible()
        assert not page.locator('#navbar-login-item').is_visible()
        page.get_by_role('button',name='Account',exact=True).click()
        assert page.get_by_role('link',name='My Profile',exact=True).is_visible()
        assert not page.locator('#nav-admin-link').is_visible()
        assert not errors,(width,errors)
        report.append({'width':width,'routes':len(routes),'header':reference,'columns':columns,'errors':errors,'passed':True})
        context.close()
    browser.close()
(args.output_dir/'results.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
