"""Browser contract for a built production artifact; all network responses local.

Uses fixed anonymous API fixtures for routing/layout checks, not authentication proof.
Real authenticated/persistence acceptance is run separately against disposable Flask.
"""
import argparse,json,mimetypes
from pathlib import Path
from urllib.parse import urlsplit,unquote
from playwright.sync_api import sync_playwright,expect
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--site',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
a=p.parse_args();site=a.site.resolve(strict=True);a.output_dir.mkdir(parents=True,exist_ok=True)
ORIGIN='https://powaynec.opencodingsociety.com';API='https://powaynec-api.opencodingsociety.com'
LOOPBACK='http://127.0.0.1'
observed=[];missing=[];rows=[]
with sync_playwright() as play:
    browser=play.chromium.launch()
    for width in [390,768,1280]:
        context=browser.new_context(viewport={'width':width,'height':1000},reduced_motion='reduce')
        def serve(route):
            url=urlsplit(route.request.url)
            if url.path.startswith('/api/'):
                assert url.scheme+'://'+url.netloc==API, 'Wrong production API origin: '+route.request.url
                assert route.request.method in ('GET','HEAD','OPTIONS'), 'Anonymous artifact check cannot write'
                observed.append(url.path)
                data={};status=200
                if url.path=='/api/auth/me':status=401
                elif url.path=='/api/announcements':data={'announcements':[]}
                elif url.path=='/api/preparedness/quiz':data={'questions':[]}
                elif url.path=='/api/volunteer/tasks':data={'tasks':[]}
                elif url.path=='/api/neighborhoods':data=[]
                elif url.path=='/api/preparedness/weekly':data={'tips':[]}
                if url.path.endswith('/theme.css'):
                    route.fulfill(status=200,body='',content_type='text/css',headers={'Access-Control-Allow-Origin':ORIGIN,'Access-Control-Allow-Credentials':'true'});return
                route.fulfill(status=status,body=json.dumps(data),content_type='application/json',headers={'Access-Control-Allow-Origin':ORIGIN,'Access-Control-Allow-Credentials':'true'});return
            if url.scheme+'://'+url.netloc in (ORIGIN, LOOPBACK):
                file=site/unquote(url.path).lstrip('/')
                if file.is_dir():file/='index.html'
                if file.is_file():route.fulfill(path=str(file),content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
                else:missing.append(url.path);route.fulfill(status=404,body='Missing production asset')
            else:route.abort()
        context.route('**/*',serve);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        for path in ['/', '/pages/register.html','/pages/checklist.html','/pages/fire-safety.html','/pages/profile.html','/pages/settings.html','/pages/volunteer.html','/pages/preparedness-resources.html','/rpg/latest/']:
            response=page.goto(ORIGIN+path,wait_until='networkidle');assert response.status==200
            if page.locator('#pnec-bot-close').is_visible():page.locator('#pnec-bot-close').click()
            assert page.evaluate('window.PNEC_API_BASE')==API
            assert page.evaluate('window.PNEC_SITE_BASE')=='' and page.evaluate('window.PNEC_REVIEW_PREVIEW') is False
            assert page.locator('link[rel="canonical"]').get_attribute('href').startswith(ORIGIN+'/')
            assert page.locator('script[src*="review-status.js"]').count()==0
            expect(page.locator('#navbar-login-item')).to_be_visible()
            assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
            if path=='/rpg/latest/':
                expect(page.get_by_role('heading',name='Preparedness RPG unavailable',exact=True)).to_be_visible()
                assert page.locator('#gameContainer').count()==0
                assert 'assets/js/rpg/latest/GameControl.js' not in page.content()
            if path=='/':assert page.locator('.pnec-context').count()==0 and page.locator('.pnec-hero-backgrounds img').count()==3
            else:assert page.locator('.pnec-context').count()==1
            rows.append({'path':path,'width':width,'passed':True})
        page.goto(ORIGIN+'/',wait_until='networkidle');page.locator('#navbar-login-item').click();page.wait_for_url(ORIGIN+'/pages/register.html#login');expect(page.locator('#login-form')).to_be_visible()
        if width == 390:
            for path in ('/', '/pages/blog.html'):
                response = page.goto(LOOPBACK + path, wait_until='networkidle')
                assert response.status == 200
                assert page.evaluate('window.PNEC_API_BASE') == API
        assert not errors,errors;context.close()
    browser.close()
assert observed and not missing,missing
(a.output_dir/'production-artifact-results.json').write_text(json.dumps({'checks':rows,'api_paths':sorted(set(observed)),'missing_assets':missing,'policy':'anonymous API fixtures; all network local; no authentication/persistence claim','passed':True},indent=2)+'\n')
print('PASS: 27 production-origin route/viewport checks, loopback API selection, runtime/canonical/API/base paths, Login destination and local assets; fixture API only.')
