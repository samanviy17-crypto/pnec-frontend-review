"""Audit every built page offline: links, runtime assets, JS and responsive bounds."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote, urljoin
import json, mimetypes, re
from playwright.sync_api import sync_playwright
from release_test_support import SITE_ROOT, PREVIEW_URL

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.refs=[]; self.ids=set()
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if attrs.get('id'): self.ids.add(attrs['id'])
        for key in ('href','src','poster'):
            if attrs.get(key): self.refs.append((tag,key,attrs[key]))

pages=sorted(SITE_ROOT.rglob('*.html'))
missing=[];external_runtime=[];parsed={}; references=0
for p in pages:
    parser=Links();parser.feed(p.read_text());parsed[p]=parser
for p,parser in parsed.items():
    pageurl='https://pnec-review.invalid/'+p.relative_to(SITE_ROOT).as_posix()
    for tag,key,ref in parser.refs:
        u=urlsplit(urljoin(pageurl,ref))
        if u.scheme not in ('https','http'): continue
        if u.netloc!='pnec-review.invalid':
            if tag in ('script','link','img','source','video','iframe') and ('powaynec.com' in u.netloc or 'localhost' in u.netloc):external_runtime.append([str(p.relative_to(SITE_ROOT)),tag,ref])
            continue
        target=SITE_ROOT/unquote(u.path).lstrip('/')
        if target.is_dir():target/='index.html'
        if not target.exists():missing.append([str(p.relative_to(SITE_ROOT)),ref])
        references+=1
print('STATIC_AUDIT',json.dumps({'pages':len(pages),'local_references':references,'missing':missing,'external_live_assets':external_runtime}),flush=True)
issues=[];rows=[]
with sync_playwright() as play:
    browser=play.chromium.launch()
    context=browser.new_context()
    def route(request_route):
        u=urlsplit(request_route.request.url)
        if request_route.request.url.startswith(PREVIEW_URL+'/'):
            request_route.continue_()
        else:
            request_route.abort()
    context.route('**/*',route)
    for file in pages:
        path='/'+file.relative_to(SITE_ROOT).as_posix()
        for width in (390,768,1440):
            page=context.new_page()
            page.set_viewport_size({'width':width,'height':900})
            errors=[];page.on('pageerror', lambda err: errors.append(str(err)))
            page.goto(PREVIEW_URL+path,wait_until='domcontentloaded')
            page.evaluate('document.fonts.ready')
            page.wait_for_timeout(400)
            headers=page.locator('.pnec-resident-header').count()
            if headers:
                if headers!=1:issues.append({'page':path,'duplicate_headers':headers})
                layout=page.evaluate('''() => { const h=document.querySelector('.pnec-resident-header').getBoundingClientRect(); const title=Array.from(document.querySelectorAll('main h1,main h2,.jupiterx-main h1,.jupiterx-main h2')).find(e=>e.getBoundingClientRect().height>0); return {headerBottom:h.bottom,titleTop:title?title.getBoundingClientRect().top:null}; }''')
                if layout['titleTop'] is not None and layout['titleTop']<layout['headerBottom']-1:issues.append({'page':path,'width':width,'heading_overlaps_header':layout})
            bounds=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
            if bounds['scroll']>width:issues.append({'page':path,'width':width,'overflow':bounds['scroll']})
            if errors:issues.append({'page':path,'width':width,'javascript_errors':errors})
            rows.append({'page':path,**bounds,'javascript_errors':errors})
            if path in ('/index.html','/pages/contact.html','/pages/register.html'):
                page.evaluate('window.scrollTo({top:document.documentElement.scrollHeight,behavior:"instant"})')
                page.wait_for_timeout(100)
                page.evaluate('window.scrollTo({top:0,behavior:"instant"})')
                page.wait_for_timeout(3600)
                hidden=page.locator('.pnec-reveal').evaluate_all('(els)=>els.filter(e=>getComputedStyle(e).opacity==="0").length')
                if hidden:issues.append({'page':path,'width':width,'hidden_content_after_failsafe':hidden})
                output=Path('screenshots');output.mkdir(exist_ok=True)
                page.screenshot(path=str(output/(file.stem+'-'+str(width)+'.png')),full_page=True)
            page.close()
        print('AUDITED '+path,flush=True)
    browser.close()
report={'pages':len(pages),'local_references':references,'missing':missing,'external_live_assets':external_runtime,'browser_cases':len(rows),'issues':issues,'viewports':rows}
Path('full-site-audit.json').write_text(json.dumps(report,indent=2))
print('BROWSER_AUDIT',json.dumps({'pages':len(pages),'cases':len(rows),'issues':issues}),flush=True)
assert not missing and not external_runtime and not issues, 'See full-site-audit.json'
