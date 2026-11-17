"""Offline browser acceptance for the November 16 redesign; never writes to APIs."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url', required=True)
parser.add_argument('--site', type=Path, required=True)
parser.add_argument('--output-dir', type=Path, required=True)
args = parser.parse_args()
base = args.base_url.rstrip('/') + '/'
args.output_dir.mkdir(parents=True, exist_ok=True)
routes = sorted(str(p.relative_to(args.site)) for p in args.site.rglob('*.html') if 'assets/' not in str(p.relative_to(args.site)))
report = []
notice_version = ['2026-11-16T12:00:00']

def api(route):
    path = urlsplit(route.request.url).path
    data = {}
    if path.endswith('/theme.css'):
        route.fulfill(status=200, content_type='text/css', body=''); return
    if path.endswith('/health'): data = {'status':'ok','review':True}
    if path.endswith('/ready'): data = {'status':'ready'}
    if path.endswith('/preparedness/weekly'):
        data = {'tips':[{'title':'Synthetic published tip','body':'Fixture content from the existing weekly API.'}], 'week_start':'2026-11-16'}
    if path.endswith('/announcements'):
        data = {'announcements':[
            {'id':1,'message':'Synthetic community notice <script>bad()</script>','level':'info','updated_at':notice_version[0]},
            {'id':2,'message':'Synthetic priority notice','level':'danger'},
            {'id':3,'message':'Expired fixture','level':'info','expires_at':'2000-01-01T00:00:00'}]}
    if '/events' in path: data = {'events':[]}
    if '/neighborhood' in path: data = {'neighborhoods':[]}
    if path.endswith('/preparedness/quiz'): data = {'questions':[]}
    route.fulfill(status=200, content_type='application/json', body=json.dumps(data))

def close_home_welcome(page):
    # Existing helper auto-opens specifically at / on window.load. Dismiss it
    # explicitly for hero/navigation checks; helper interactions are tested below.
    page.wait_for_load_state('load')
    close = page.locator('#pnec-bot-close')
    if close.is_visible():
        close.click()

with sync_playwright() as play:
    browser = play.chromium.launch()
    for width in [320,390,768,1280]:
        context = browser.new_context(viewport={'width':width,'height':900}, reduced_motion='reduce', has_touch=width<1051)
        context.route('**/*',lambda r: r.continue_() if r.request.url.startswith(base) else api(r) if '/api/' in r.request.url else r.abort())
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        for route in routes:
            response = page.goto(base + route, wait_until='domcontentloaded')
            close_home_welcome(page)
            assert response.status == 200, (width,route,response.status)
            page.wait_for_timeout(80)
            assert page.locator('#pnec-site-header').count()==1, (width,route,'missing shared sidebar')
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), (width,route,'overflow')
            assert not errors, (width,route,errors)
            report.append({'route':route,'width':width,'state':'anonymous/offline fixtures','passed':True})
        page.goto(base, wait_until='networkidle')
        close_home_welcome(page)
        assert page.locator('.pnec-alert').count()==2
        assert page.locator('.pnec-alert script').count()==0
        assert page.locator('.pnec-alert-danger button').count()==0
        page.get_by_role('button', name='Dismiss community announcement').click()
        page.reload(wait_until='networkidle')
        close_home_welcome(page)
        assert page.locator('.pnec-alert').count()==1
        notice_version[0] += '1'
        page.reload(wait_until='networkidle')
        close_home_welcome(page)
        assert page.locator('.pnec-alert').count()==2, 'Revised notice must reappear'
        assert page.locator('#weekly-tip-heading').inner_text()=="This week's preparedness tip"
        assert page.locator('#weekly-tip-content h3').inner_text()=='Synthetic published tip'
        assert 'Fixture content' in page.locator('#weekly-tip-content').inner_text()
        assert '2026-11-16' in page.locator('#weekly-tip-source').inner_text()
        assert page.locator('#weekly-tip-content').is_visible()
        assert page.locator('.pnec-carousel-controls, .pnec-slide, [data-slide]').count()==0
        assert page.locator('.pnec-hero-backgrounds img').count()==3
        assert page.locator('.pnec-hero-backgrounds img').evaluate_all('(els)=>els.every(e=>e.complete && e.naturalWidth>0)')
        assert len(set(page.locator('.pnec-hero-backgrounds img').evaluate_all('(els)=>els.map(e=>e.src)')))==3
        assert page.locator('[data-slide], [data-carousel], .pnec-slide').count()==0
        assert page.locator('.pnec-hero-pause').is_hidden()
        page.screenshot(path=str(args.output_dir/f'home-{width}.png'), full_page=True)
        if width<1051:
            page.locator('.nav-trigger').click()
            assert page.locator('#pnec-site-header').get_attribute('aria-modal')=='true'
            assert page.locator('main').evaluate('(e)=>e.inert')
            page.locator('#navbar-login-item').focus(); page.keyboard.press('Tab')
            assert page.locator('#pnec-site-header').evaluate('(e)=>e.contains(document.activeElement)')
            page.keyboard.press('Escape')
            assert page.locator('.nav-trigger').evaluate('(e)=>e===document.activeElement')
            assert not page.locator('main').evaluate('(e)=>e.inert')
        page.goto(base+'pages/settings.html', wait_until='networkidle')
        close_home_welcome(page)
        page.select_option('[name="theme"]','dark')
        page.select_option('[name="font"]','serif')
        page.select_option('[name="background"]','grid')
        page.select_option('[name="size"]','extra')
        page.check('[name="spacing"]')
        page.reload(wait_until='networkidle')
        close_home_welcome(page)
        assert page.locator('html').get_attribute('data-appearance-resolved')=='dark'
        assert page.locator('[name="font"]').input_value()=='serif'
        assert page.locator('#appearance-status').evaluate('(e)=>getComputedStyle(e).color') == 'rgb(237, 245, 251)'
        assert page.locator('main').evaluate('(e)=>getComputedStyle(e).backgroundImage') == 'none'
        assert page.locator('[name="size"]').input_value()=='extra'
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), (width,'enlarged settings overflow')
        page.evaluate('window.scrollTo(0,0)')
        page.screenshot(path=str(args.output_dir/f'settings-dark-{width}.png'), full_page=True)
        page.goto(base+'pages/kit.html', wait_until='networkidle')
        close_home_welcome(page)
        assert page.locator('html').get_attribute('data-appearance-font')=='serif'
        assert page.locator('.kit-item-name').first.evaluate('(e)=>getComputedStyle(e).color') == 'rgb(237, 245, 251)'
        search=page.locator('#pnec-kit-filter')
        search.fill('water')
        assert 'matching' in page.locator('#kit-filter-status').inner_text()
        assert page.locator('.kit-item:visible').count()>0
        search.fill('no matching synthetic item')
        assert page.locator('.kit-item:visible').count()==0
        search.fill('')
        item=page.locator('.kit-item').first
        item.press('Space')
        assert item.get_attribute('aria-checked')=='true'
        page.reload(wait_until='networkidle')
        close_home_welcome(page)
        assert page.locator('.kit-item').first.get_attribute('aria-checked')=='true'
        page.goto(base+'pages/preparedness-resources.html',wait_until='networkidle')
        close_home_welcome(page)
        page.locator('#pnec-resource-filter').fill('Wildfire')
        assert page.locator('.elementor-widget-image-box:visible').count()>0
        page.locator('#pnec-resource-filter').fill('no matching synthetic resource')
        assert page.locator('.elementor-widget-image-box:visible').count()==0
        page.locator('#pnec-resource-filter').fill('')
        page.locator('summary').first.press('Enter')
        assert page.locator('details').first.get_attribute('open') is not None
        page.goto(base+'pages/register.html',wait_until='networkidle')
        close_home_welcome(page)
        assert page.locator('.auth-form-stack').evaluate('(e)=>getComputedStyle(e).backgroundColor') == 'rgb(23, 38, 56)'
        page.goto(base+'pages/volunteer.html',wait_until='networkidle')
        close_home_welcome(page)
        assert page.locator('.vol-form-card').evaluate('(e)=>getComputedStyle(e).backgroundColor') == 'rgb(23, 38, 56)'
        page.goto(base+'pages/settings.html',wait_until='networkidle')
        close_home_welcome(page)
        page.get_by_role('button',name='Reset to defaults').click()
        assert page.locator('[name="theme"]').input_value()=='system'
        assert not errors, (width,errors)
        context.close()
    # Backgrounds cycle; the content DOM and its geometry remain fixed.
    context = browser.new_context(viewport={'width':1280,'height':900})
    context.route('**/*',lambda r: r.continue_() if r.request.url.startswith(base) else api(r) if '/api/' in r.request.url else r.abort())
    page = context.new_page()
    page.clock.install()
    page.goto(base,wait_until='networkidle')
    close_home_welcome(page)
    copy = page.locator('.pnec-hero-copy')
    before = copy.inner_html()
    box = copy.bounding_box()
    seen = []
    for _ in range(4):
        seen.append(page.locator('.pnec-hero-backgrounds .is-current').get_attribute('src'))
        page.clock.fast_forward(8100)
        assert copy.inner_html()==before
        assert copy.bounding_box()==box
    assert len(set(seen[:3]))==3 and seen[0]==seen[3]
    prepared = page.get_by_role('link',name='Get Prepared →',exact=True)
    assert prepared.get_attribute('href')==urlsplit(base).path+'pages/checklist.html'
    prepared.click()
    assert page.url==base+'pages/checklist.html'
    page.goto(base,wait_until='networkidle')
    close_home_welcome(page)
    page.get_by_role('button',name='Pause background photos').click()
    current = page.locator('.pnec-hero-backgrounds .is-current').get_attribute('src')
    page.clock.fast_forward(16000)
    assert page.locator('.pnec-hero-backgrounds .is-current').get_attribute('src')==current
    page.get_by_role('button',name='Resume background photos').click()
    page.emulate_media(reduced_motion='reduce')
    page.locator('.pnec-hero-pause').wait_for(state='hidden')
    current = page.locator('.pnec-hero-backgrounds .is-current').get_attribute('src')
    page.clock.fast_forward(16000)
    assert page.locator('.pnec-hero-backgrounds .is-current').get_attribute('src')==current
    assert page.locator('.pnec-hero-pause').is_hidden()
    page.emulate_media(reduced_motion='no-preference')
    page.evaluate("document.documentElement.dataset.appearanceMotion='true'; window.dispatchEvent(new Event('pnec:appearance-changed'))")
    current = page.locator('.pnec-hero-backgrounds .is-current').get_attribute('src')
    page.clock.fast_forward(16000)
    assert page.locator('.pnec-hero-backgrounds .is-current').get_attribute('src')==current
    context.close()
    # Empty successful responses, errors and malformed tip payloads share the notice.
    for payload in ({'tips':[]}, {'tips':[{'title':42,'body':None}]}, None):
        context = browser.new_context()
        def missing(route):
            if route.request.url.startswith(base): route.continue_()
            else: route.fulfill(status=503 if payload is None else 200, content_type='application/json', body=json.dumps(payload or {}))
        context.route('**/*',missing)
        page=context.new_page(); page.goto(base,wait_until='networkidle')
        close_home_welcome(page)
        assert page.locator('#weekly-tip-content').inner_text()=='The current weekly tip is unavailable. You can still use the emergency kit guide.'
        assert page.locator('#weekly-tip-source').inner_text()=='No live risk information is shown.'
        assert page.get_by_role('link',name='Review your emergency kit →').is_visible()
        assert page.locator('.pnec-alert').count()==0
        context.close()
    # Source-reviewed official notice config requires an allowlisted source and expiry.
    context = browser.new_context(viewport={'width':390,'height':900})
    def official_route(route):
        if route.request.url == base:
            html = (args.site/'index.html').read_text()
            import html as html_module
            import re
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            notices = [
                {'id':'fixture-official','message':'SYNTHETIC official-notice renderer test', 'verified':True,
                 'source_url':'https://www.weather.gov/', 'updated_at':(now-timedelta(hours=1)).isoformat(),
                 'expires_at':(now+timedelta(hours=1)).isoformat()},
                {'id':'untrusted','message':'Must not appear','verified':True,'source_url':'https://untrusted.example.test/',
                 'updated_at':now.isoformat(),'expires_at':(now+timedelta(hours=1)).isoformat()}]
            html = re.sub(r'data-configured-notices="[^"]*"', 'data-configured-notices="'+html_module.escape(json.dumps(notices),quote=True)+'"', html)
            route.fulfill(status=200,content_type='text/html',body=html)
        elif route.request.url.startswith(base): route.continue_()
        else: route.fulfill(status=503,content_type='application/json',body='{}')
    context.route('**/*',official_route)
    page = context.new_page()
    page.goto(base,wait_until='networkidle')
    close_home_welcome(page)
    assert page.locator('.pnec-alert').count()==1
    assert 'Verified official emergency notice' in page.locator('.pnec-alert').inner_text()
    assert page.locator('.pnec-alert button').count()==0
    assert page.locator('.pnec-alert a').get_attribute('href')=='https://www.weather.gov/'
    context.close()
    # Corrupt/blocked storage and unavailable/empty API responses are separate states.
    for storage in ['corrupt','blocked']:
        context = browser.new_context(viewport={'width':390,'height':900})
        context.route('**/*',lambda r: r.continue_() if r.request.url.startswith(base) else r.fulfill(status=503,content_type='application/json',body='{}'))
        if storage=='corrupt': context.add_init_script("localStorage.setItem('pnec_appearance_v1','{broken'); localStorage.setItem('pnec_dismissed_notice_versions','null')")
        else: context.add_init_script("Object.defineProperty(window, 'localStorage', {get(){throw new Error('Storage disabled')}})")
        page = context.new_page()
        page.goto(base,wait_until='networkidle')
        close_home_welcome(page)
        assert page.locator('#pnec-alert-banner').is_hidden()
        assert 'unavailable' in page.locator('#weekly-tip-content').inner_text()
        page.goto(base+'pages/settings.html',wait_until='networkidle')
        close_home_welcome(page)
        page.select_option('[name="theme"]','dark')
        assert page.locator('html').get_attribute('data-appearance-resolved')=='dark'
        if storage=='blocked': assert 'unavailable' in page.locator('#appearance-status').inner_text()
        context.close()
    browser.close()
(args.output_dir/'mortenson-results.json').write_text(json.dumps(report,indent=2))
print(f'PASS: {len(report)} route/viewport checks; fixed hero/background rotation, published and missing tip, notices, drawer, preferences, filters and kit persistence. APIs mocked; no live authentication claim.')
