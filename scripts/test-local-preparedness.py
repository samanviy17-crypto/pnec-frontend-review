"""Unmocked loopback browser/API acceptance against an explicitly disposable backend.
Never targets production. Credentials are read from a private, untracked state file.
"""
import argparse
import json
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright, expect

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url',default='http://localhost:8766/')
parser.add_argument('--api-url',default='http://localhost:8426')
parser.add_argument('--credentials-file',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args();base=args.base_url.rstrip('/')+'/';api=args.api_url.rstrip('/')
assert urlsplit(base).hostname in ['localhost','127.0.0.1']
assert urlsplit(api).hostname==urlsplit(base).hostname,'Cookie test requires same-site loopback hostnames'
creds=json.loads(args.credentials_file.read_text())
assert creds['email'].endswith('@example.test')
args.output_dir.mkdir(parents=True,exist_ok=True)
report={'frontend':base,'backend':api,'synthetic_data_only':True,'transport':'actual loopback HTTP; no API/identity mocks'}
with sync_playwright() as p:
 browser=p.chromium.launch();context=browser.new_context(viewport={'width':1280,'height':1000})
 marker=context.request.get(api+'/api/local-review').json();assert marker.get('disposable') is True and marker.get('external_providers') is False
 for endpoint in ['/health','/ready']:
  response=context.request.get(api+'/api'+endpoint,headers={'Origin':base.rstrip('/')});assert response.status==200
  assert response.headers.get('access-control-allow-origin')==base.rstrip('/')
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 context.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) or r.request.url.startswith(api+'/') else r.abort())
 page.goto(base,wait_until='networkidle')
 if page.locator('#pnec-bot-close').is_visible():page.locator('#pnec-bot-close').click()
 assert page.locator('#navbar-login-item').is_visible()
 assert page.locator('.pnec-context').count()==0
 assert page.locator('body').evaluate('(e)=>getComputedStyle(e).paddingLeft')=='0px'
 assert page.evaluate('API_BASE')==api
 page.locator('#navbar-login-item').click();page.wait_for_url('**/pages/register.html#login')
 page.goto(base+'pages/checklist.html',wait_until='networkidle')
 titles=['Your household plan','Preparedness assessment','Resident well-being check-in','Report a neighborhood hazard']
 def panel(title):return page.locator('[data-community-tools] > section').filter(has=page.get_by_role('heading',name=title,exact=True))
 for title in titles:
  expect(panel(title).get_by_role('link',name='Log in to PNEC',exact=True)).to_be_visible()
  assert panel(title).locator('form').count()==0
 for endpoint in ['/preparedness','/check-ins','/hazards']:
  assert context.request.get(api+'/api'+endpoint).status==401
 assert len(context.request.get(api+'/api/preparedness/quiz').json()['questions'])==10
 report['unauthenticated']='four explicit login prompts; protected data 401; quiz questions public'
 page.goto(base+'pages/register.html?next='+ '/pages/checklist.html' +'#login',wait_until='networkidle')
 page.fill('#login-email',creds['email']);page.fill('#login-password',creds['password']);page.locator('#login-form button[type="submit"]').click()
 page.wait_for_url('**/pages/checklist.html');page.wait_for_load_state('networkidle')
 expect(page.locator('#navbar-auth-logged-in')).to_be_visible();assert page.locator('#navbar-login-item').is_hidden()
 page.locator('#pnec-account-dropdown > summary').click();expect(page.get_by_role('link',name='My Profile',exact=True)).to_be_visible();page.keyboard.press('Escape')
 cookies=context.cookies(api);session=next(c for c in cookies if c['name']=='pnec_session')
 assert session['httpOnly'] and session['sameSite']=='Lax' and not session['secure']
 report['login']='actual PNEC UI POST; account menu replaces Login; HttpOnly SameSite=Lax development cookie'
 plan=panel(titles[0]);plan.locator('[name="household_size"]').fill('3');plan.locator('[name="meeting_point"]').fill('Synthetic review meeting point (not a real household)');plan.locator('[name="evacuation_plan"]').fill('Synthetic local QA plan only.');plan.get_by_role('button',name='Save household plan',exact=True).click();expect(plan.get_by_role('status')).to_contain_text('Saved.')
 quiz=panel(titles[1]);expect(quiz.locator('select')).to_have_count(10)
 for select in quiz.locator('select').all():select.select_option('yes')
 quiz.get_by_role('button',name='Save assessment',exact=True).click();expect(quiz).to_contain_text('Preparedness score: 100%')
 checkin=panel(titles[2]);checkin.locator('[name="status"]').select_option('safe');checkin.locator('[name="note"]').fill('SYNTHETIC LOCAL TEST — not a real resident status.');checkin.get_by_role('button',name='Update my status',exact=True).click();expect(checkin).to_contain_text('SYNTHETIC LOCAL TEST')
 hazard=panel(titles[3]);hazard.locator('[name="neighborhood_id"]').select_option(index=1);hazard.locator('[name="category"]').select_option('other');hazard.locator('[name="location"]').fill('Synthetic QA location (not an incident)');hazard.locator('[name="description"]').fill('SYNTHETIC LOCAL TEST — no real hazard reported.');hazard.get_by_role('button',name='Submit hazard report',exact=True).click();expect(hazard).to_contain_text('SYNTHETIC LOCAL TEST — no real hazard reported.')
 page.reload(wait_until='networkidle');expect(panel(titles[0]).locator('[name="meeting_point"]')).to_have_value('Synthetic review meeting point (not a real household)');expect(panel(titles[1])).to_contain_text('Preparedness score: 100%');expect(panel(titles[2])).to_contain_text('SYNTHETIC LOCAL TEST');expect(panel(titles[3])).to_contain_text('SYNTHETIC LOCAL TEST — no real hazard reported.')
 with sqlite3.connect(Path(creds['state_dir'])/'review.db') as db:
  assert db.execute('select count(*) from household_preparedness where household_size=3').fetchone()[0]>=1
  assert db.execute('select count(*) from resident_check_ins').fetchone()[0]>=1
  assert db.execute('select count(*) from hazard_reports').fetchone()[0]>=1
 report['four_features']='household PATCH, quiz POST, check-in PUT and hazard POST persisted; reload and SQLite verified'
 # Cookie-only requests prove security checks without relying on the returned bearer.
 assert context.request.get(api+'/api/preparedness').status==200
 assert context.request.patch(api+'/api/preparedness',data={'meeting_point':'Rejected CSRF attempt'},headers={'Origin':'https://unapproved.example.test'}).status==403
 assert context.request.patch(api+'/api/preparedness',data={'meeting_point':'Rejected missing CSRF'}).status==403
 token=context.request.get(api+'/api/auth/csrf').json()['csrf_token']
 assert context.request.patch(api+'/api/preparedness',data={'meeting_point':'Synthetic review meeting point (not a real household)'},headers={'X-CSRF-Token':token}).status==200
 assert context.request.get(api+'/api/preparedness',headers={'Authorization':'Bearer invalid-synthetic-token'}).status==401
 reports=context.request.get(api+'/api/hazards').json()['hazards'];report_id=reports[0]['id']
 assert context.request.patch(api+f'/api/hazards/{report_id}',data={'status':'resolved'},headers={'Origin':base.rstrip('/')}).status==403
 report['security']='cookie auth works; unapproved Origin 403; missing session CSRF token 403; correct CSRF 200; invalid bearer 401 despite cookie; resident moderation 403'
 assert not errors,errors
 page.locator('#pnec-account-dropdown > summary').click();page.locator('#navbar-logout-btn').click();page.wait_for_url(base);page.wait_for_load_state('networkidle')
 if page.locator('#pnec-bot-close').is_visible():page.locator('#pnec-bot-close').click()
 expect(page.locator('#navbar-login-item')).to_be_visible();assert context.request.get(api+'/api/preparedness').status==401
 # Mobile top Login and section navigation are usable before authentication.
 page.set_viewport_size({'width':390,'height':900});expect(page.locator('#navbar-login-item')).to_be_visible()
 page.locator('.nav-trigger').click();page.locator('[data-category-link="prepare"]').click();page.wait_for_load_state('networkidle')
 page.locator('.nav-trigger').click();assert page.locator('[data-context="prepare"]').is_visible();page.keyboard.press('Escape')
 assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
 report['logout_and_mobile']='actual logout invalidates session; mobile Login visible and Prepare drawer works'
 report['page_errors']=errors;report['passed']=True
 context.close();browser.close()
(args.output_dir/'local-integration-results.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: unmocked local login/logout, four database-backed features, reload persistence, cookies/CORS/CSRF/authorization and mobile navigation; disposable synthetic data only.')
