"""Build a separate production artifact locally. Never publishes or changes Pages.

--verify-live-api is a read-only release gate, not used by offline preparation CI.
The API/domain are exact constants, never taken from review variables or secrets.
"""
import argparse,json,os,re,subprocess,tempfile
from pathlib import Path
from urllib.request import Request,urlopen

FRONTEND='https://powaynec.opencodingsociety.com'
API='https://powaynec-api.opencodingsociety.com'
SCHEMA='0002_announcements'
root=Path(__file__).resolve().parents[1]
def verify_live_api():
    # Standard TLS only; exact single CORS headers, no credentials or writes.
    for endpoint in ['health','ready']:
        with urlopen(Request(API+'/api/'+endpoint,headers={'Origin':FRONTEND}),timeout=20) as response:
            data=json.load(response)
            if (response.headers.get_all('Access-Control-Allow-Origin') != [FRONTEND]
                    or response.headers.get_all('Access-Control-Allow-Credentials') != ['true']):
                raise SystemExit('Production API exact single CORS/credential gate failed.')
            if endpoint=='health' and (data.get('status')!='ok' or data.get('review') is True):raise SystemExit('Production API health/review gate failed.')
            if endpoint=='ready' and (data.get('status')!='ready' or data.get('schema_revision')!=SCHEMA):raise SystemExit('Production schema is not ready.')
    request=Request(API+'/api/auth/profile',method='OPTIONS',headers={
        'Origin':FRONTEND,'Access-Control-Request-Method':'PATCH',
        'Access-Control-Request-Headers':'Authorization,Content-Type,X-CSRF-Token'})
    with urlopen(request,timeout=20) as response:
        if (response.headers.get_all('Access-Control-Allow-Origin') != [FRONTEND]
                or response.headers.get_all('Access-Control-Allow-Credentials') != ['true']):raise SystemExit('Production preflight CORS gate failed.')
        if 'PATCH' not in {m.strip() for m in response.headers.get('Access-Control-Allow-Methods','').split(',')}:raise SystemExit('Production PATCH preflight gate failed.')
        allowed={h.strip().lower() for h in response.headers.get('Access-Control-Allow-Headers','').split(',')}
        if not {'authorization','content-type','x-csrf-token'} <= allowed:raise SystemExit('Production CSRF/header preflight gate failed.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--destination',type=Path,required=True)
    p.add_argument('--verify-live-api',action='store_true')
    a=p.parse_args();destination=a.destination.resolve()
    if destination==root or root in destination.parents:raise SystemExit('Build outside source.')
    if a.verify_live_api:verify_live_api()
    with tempfile.TemporaryDirectory(prefix='pnec-production-build-') as work:
        subprocess.run(['bundle','exec','jekyll','build','--source',str(root),'--destination',str(destination),'--config',str(root/'_config.yml')+','+str(root/'_config.production.yml')],cwd=work,env={**os.environ,'BUNDLE_GEMFILE':str(root/'Gemfile')},check=True)
    pattern=r'window\.PNEC_REMOTE_API_BASE\s*=\s*("(?:[^"\\]|\\.)*")\s*;'
    checked=0
    for file in destination.rglob('*.html'):
        text=file.read_text()
        values=re.findall(pattern,text)
        for value in values:
            if json.loads(value)!=API:raise SystemExit('Incorrect production API in '+str(file.relative_to(destination)))
            checked+=1
        if values:
            canonical=re.findall(r'<link rel="canonical" href="([^"]+)"',text)
            if len(canonical)!=1 or not canonical[0].startswith(FRONTEND+'/'):raise SystemExit('Incorrect production canonical origin.')
            if not re.search(r'window\.PNEC_SITE_BASE\s*=\s*""\s*;',text):raise SystemExit('Incorrect production baseurl.')
            if not re.search(r'window\.PNEC_REVIEW_PREVIEW\s*=\s*false\s*;',text):raise SystemExit('Production must not be a review preview.')
            if '/pnec-frontend-review/' in text:raise SystemExit('Review project path leaked into production HTML.')
    if not checked or not re.search(pattern,(destination/'index.html').read_text()):raise SystemExit('Missing production runtime configuration.')
    for name in ['scripts','docs','deploy','.github','.env']:
        if (destination/name).exists():raise SystemExit('Non-product source included in artifact: '+name)
    subprocess.run(['python3',str(root/'scripts/check-pages-paths.py'),'--site',str(destination),'--base-path',''],check=True)
    print(f'PASS: production root/API/preview configuration verified in {checked} rendered pages; artifact only, no publication.')


if __name__=='__main__':main()
