"""Offline UI acceptance for conditional navigation, wildfire geometry and service states."""
import argparse,json
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright,expect
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url',required=True);parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args();base=args.base_url.rstrip('/')+'/';args.output_dir.mkdir(parents=True,exist_ok=True);report=[]
with sync_playwright() as p:
 browser=p.chromium.launch()
 for width in (320,390,768,1280):
  context=browser.new_context(viewport={'width':width,'height':1000},reduced_motion='reduce')
  def offline(route):
   if route.request.url.startswith(base):route.continue_()
   elif urlsplit(route.request.url).path.endswith('/auth/me'):route.fulfill(status=401,content_type='application/json',body='{}')
   elif urlsplit(route.request.url).path.endswith('/theme.css'):route.fulfill(status=200,content_type='text/css',body='')
   else:route.fulfill(status=503,content_type='application/json',body='{}')
  context.route('**/*',offline)
  context.add_init_script("localStorage.setItem('pnec_user',JSON.stringify({role:'admin',display_name:'Stale synthetic cache'}))")
  page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(base,wait_until='networkidle')
  if page.locator('#pnec-bot-close').is_visible():page.locator('#pnec-bot-close').click()
  assert page.locator('.pnec-context').count()==0
  assert page.locator('body').evaluate('(e)=>getComputedStyle(e).paddingLeft')=='0px'
  assert page.locator('.pnec-hero-backgrounds img').count()==3
  assert page.locator('.pnec-primary a').count()==5
  expect(page.locator('#navbar-login-item')).to_be_visible();assert page.locator('#navbar-auth-logged-in').is_hidden()
  if width>1050:
   login=page.locator('#navbar-login-item').bounding_box();last=page.locator('.pnec-primary a').last.bounding_box()
   assert login['x']>=last['x']+last['width']
  page.locator('#navbar-login-item').click();page.wait_for_url('**/pages/register.html#login');expect(page.locator('#login-form')).to_be_visible()
  page.goto(base+'pages/fire-safety.html',wait_until='networkidle')
  assert page.locator('#pnec-site-header').get_attribute('data-category')=='resources'
  assert page.locator('[data-context="resources"]').get_attribute('hidden') is None
  assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
  assert page.locator('main time').get_attribute('datetime')=='2026-11-17'
  for target in ['https://ecode360.com/50659259','https://www.fire.ca.gov/dspace','https://bof.fire.ca.gov/projects-and-programs/defensible-space-zones-0-1-and-2','https://oal.ca.gov/emergency_regulations/emergency_regulations_under_review/']:
   assert page.locator(f'main a[href="{target}"]').count()>0
  assert '2026-1116-02E' in page.locator('main').inner_text()
  assert 'not a universal' in page.locator('main').inner_text()
  assert 'at least 10 feet' in page.locator('.pnec-tree-rules').inner_text()
  assert 'at least 20 feet' in page.locator('.pnec-tree-rules').inner_text()
  assert '5 feet above the roof' in page.locator('.pnec-tree-rules').inner_text()
  house=page.locator('#tree-house-gap');gap=page.locator('#tree-canopy-gap')
  assert 'meet the two' in page.locator('#tree-distance-status').inner_text()
  house.focus();house.press('Home');gap.focus();gap.press('Home')
  assert 'Below' in page.locator('#tree-distance-status').inner_text()
  house.press('End');gap.press('End')
  assert page.locator('#tree-house-value').inner_text()=='30 feet'
  assert 'meet the two' in page.locator('#tree-distance-status').inner_text()
  line=page.locator('#tree-house-line');assert float(line.get_attribute('x2'))-float(line.get_attribute('x1'))==270
  line=page.locator('#tree-gap-line');assert float(line.get_attribute('x2'))-float(line.get_attribute('x1'))==270
  assert not errors,(width,errors)
  report.append({'width':width,'home_sidebar':False,'top_login':True,'stale_cache_rejected':True,'fire_scope_sources_and_geometry':True,'page_errors':errors,'passed':True});context.close()
 # An unavailable local service is not described as an internet failure.
 context=browser.new_context();context.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort())
 page=context.new_page();page.goto(base+'pages/checklist.html',wait_until='networkidle')
 expect(page.locator('[data-community-tools]')).to_contain_text('Cannot reach the local PNEC backend')
 assert 'Check your internet connection' not in page.locator('[data-community-tools]').inner_text()
 assert page.locator('[data-community-tools] form').count()==0
 assert page.locator('[data-community-tools] a').count()==4
 context.close()
 # Empty public question data receives an explicit availability message after auth.
 context=browser.new_context()
 def empty_data(route):
  if route.request.url.startswith(base):route.continue_();return
  path=urlsplit(route.request.url).path;data={}
  if path.endswith('/auth/me'):data={'user':{'id':999,'role':'resident','display_name':'Synthetic QA','email':'qa@example.test','neighborhood_id':1}}
  elif path.endswith('/neighborhoods'):data={'neighborhoods':[{'id':1,'name':'Synthetic neighborhood'}]}
  elif path.endswith('/preparedness/quiz'):data={'questions':[]}
  elif path.endswith('/preparedness'):data={'household_size':1,'quiz_answers':{},'assessment':None}
  elif path.endswith('/check-ins'):data={'check_ins':[]}
  elif path.endswith('/hazards'):data={'hazards':[]}
  elif path.endswith('/theme.css'):route.fulfill(status=200,content_type='text/css',body='');return
  route.fulfill(status=200,content_type='application/json',body=json.dumps(data))
 context.route('**/*',empty_data);page=context.new_page();page.goto(base+'pages/checklist.html',wait_until='networkidle')
 expect(page.locator('#preparedness-quiz')).to_contain_text('No assessment questions are available yet.')
 expect(page.locator('#navbar-auth-logged-in')).to_be_visible()
 context.close();browser.close()
(args.output_dir/'fire-login-ui-results.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: top Login, stale identity rejection, conditional Home/Resources, fire sources/status and interactive distances at four widths; offline and no-data states.')
