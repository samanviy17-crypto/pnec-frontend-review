"""Authenticated contrast audit against the marked disposable local backend."""
import argparse
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright,expect
from pathlib import Path
import json
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--credentials-file',type=Path,required=True)
parser.add_argument('--axe-script',type=Path,required=True)
parser.add_argument('--base-url',default='http://localhost:8766/')
parser.add_argument('--api-url',default='http://localhost:8426')
parser.add_argument('--output-dir',type=Path,required=True)
a=parser.parse_args();base=a.base_url.rstrip('/')+'/';api=a.api_url.rstrip('/')
assert urlsplit(base).hostname in ['localhost','127.0.0.1'] and urlsplit(api).hostname==urlsplit(base).hostname
creds=json.loads(a.credentials_file.read_text());assert creds['email'].endswith('@example.test')
a.output_dir.mkdir(parents=True,exist_ok=True);rows=[]
with sync_playwright() as p:
 b=p.chromium.launch();c=b.new_context(viewport={'width':1280,'height':1000},reduced_motion='reduce');c.route('**/*',lambda r:r.continue_() if r.request.url.startswith((base,api+'/')) else r.abort());page=c.new_page();assert c.request.get(api+'/api/local-review').json().get('disposable') is True;page.goto(base+'pages/register.html#login',wait_until='networkidle');page.fill('#login-email',creds['email']);page.fill('#login-password',creds['password']);page.locator('#login-password').press('Enter');page.wait_for_url('**/pages/profile.html')
 for theme in ['site-default','midnight','light','green','sepia','cyberpunk','ocean','sunset']:
  page.evaluate('(t)=>localStorage.setItem("pnec_appearance_v1",JSON.stringify({preset:t,theme:["midnight","green","cyberpunk","ocean"].includes(t)?"dark":"light"}))',theme)
  for route in ['pages/profile.html','pages/checklist.html','pages/volunteer.html']:
   page.goto(base+route,wait_until='networkidle');expect(page.locator('#navbar-auth-logged-in')).to_be_visible();page.add_script_tag(path=str(a.axe_script));r=page.evaluate('async()=>await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa"]}})');rows.append({'route':route,'theme':theme,'violations':[{'id':v['id'],'nodes':[n['target'] for n in v['nodes']]} for v in r['violations']]});print(theme,route,[(v['id'],len(v['nodes'])) for v in rows[-1]['violations']],flush=True)
 b.close()
(a.output_dir/'authenticated-accessibility-results.json').write_text(json.dumps({'transport':'real PNEC UI login; no identity/API mocks','checks':rows},indent=2)+'\n')
assert not any(x['violations'] for x in rows)
