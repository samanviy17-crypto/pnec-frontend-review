"""Real HTTP stakeholder journeys. Refuses anything except a marked disposable API.
Seeds synthetic coordinator/admin fixtures only in its private temporary SQLite DB.
Resident registration always uses the real UI; no auth/session/CSRF controls bypassed.
Never writes credentials into the report or screenshots.
"""
import argparse,json,secrets,sqlite3
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright,expect
from werkzeug.security import generate_password_hash

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url',default='http://localhost:8766/')
parser.add_argument('--api-url',default='http://localhost:8426')
parser.add_argument('--credentials-file',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
a=parser.parse_args();base=a.base_url.rstrip('/')+'/';api=a.api_url.rstrip('/')
assert urlsplit(base).hostname in ('localhost','127.0.0.1')
assert urlsplit(api).hostname==urlsplit(base).hostname
credentials=json.loads(a.credentials_file.read_text());state=Path(credentials['state_dir']).resolve()
assert state.name.startswith('pnec-local-review-') and state.stat().st_mode & 0o077==0
assert credentials['email'].endswith('@example.test')
a.output_dir.mkdir(parents=True,exist_ok=True)
report={'transport':'real loopback HTTP; no API mocks','synthetic_data_only':True,'checks':[]}
run=secrets.token_hex(4)
with sync_playwright() as p:
 browser=p.chromium.launch()
 probe=browser.new_context();marker=probe.request.get(api+'/api/local-review').json()
 assert marker.get('disposable') is True and marker.get('external_providers') is False and marker.get('synthetic_data_only') is True
 assert 'register-existing-announcements-blueprint' in marker.get('local_compatibility_fixes',[]), 'Enable the explicit disposable announcement compatibility fix'
 report['local_compatibility_fixes']=marker['local_compatibility_fixes']
 probe.close()
 # Role fixtures are explicit test setup, never public registration privileges.
 roles={}
 with sqlite3.connect(state/'review.db') as db:
  nid=db.execute("select id from neighborhoods where name like 'Synthetic Local Review%'").fetchone()[0]
  other=db.execute('insert into neighborhoods(name,number,zone) values(?,?,?)',('Synthetic Other Block '+run,998,'B')).lastrowid
  for role in ('coordinator','admin'):
   email=f'demo-{role}-{run}@example.test';password=secrets.token_urlsafe(24)
   uid=db.execute('insert into users(email,password_hash,display_name,neighborhood_id,role,is_active,created_at) values(?,?,?,?,?,?,?)',(email,generate_password_hash(password),'Synthetic '+role,nid,role,True,datetime.now(timezone.utc).replace(tzinfo=None).isoformat())).lastrowid
   roles[role]={'email':email,'password':password,'id':uid}
  db.commit()
 # Keep fixture credentials outside Git with owner-only permissions.
 private=state/('stakeholder-fixtures-'+run+'.json');private.write_text(json.dumps(roles));private.chmod(0o600)
 errors=[]
 def context():
  c=browser.new_context(viewport={'width':1280,'height':1000},reduced_motion='reduce')
  c.route('**/*',lambda r:r.continue_() if r.request.url.startswith((base,api+'/')) else r.abort())
  return c
 def page_for(c):
  page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)));return page
 def login(page,account):
  page.goto(base+'pages/register.html#login',wait_until='networkidle')
  page.fill('#login-email',account['email']);page.fill('#login-password',account['password']);page.locator('#login-password').press('Enter');page.wait_for_url('**/pages/profile.html');page.wait_for_load_state('networkidle')
  expect(page.locator('#profile-overview')).to_be_visible();expect(page.locator('#navbar-auth-logged-in')).to_be_visible()
 def token(c):return c.request.get(api+'/api/auth/csrf').json()['csrf_token']
 def write(c,method,path,data):
  return c.request.fetch(api+'/api'+path,method=method,data=data,headers={'Origin':base.rstrip('/'),'X-CSRF-Token':token(c)})
 resident=context();page=page_for(resident);login(page,credentials)
 primary=resident.request.get(api+'/api/auth/me').json()['user'];pid=primary['id']
 page.fill('#edit-bio','SYNTHETIC stakeholder review profile.');page.locator('#profile-save-btn').click();expect(page.locator('#profile-success')).to_be_visible()
 page.reload(wait_until='networkidle');expect(page.locator('#edit-bio')).to_have_value('SYNTHETIC stakeholder review profile.')
 page.locator('#pnec-account-dropdown > summary').click();expect(page.get_by_role('link',name='My Profile',exact=True)).to_be_visible();page.keyboard.press('Escape')
 report['checks'].append('Existing UI login, account menu, dashboard and profile edit/reload')
 # Register a distinct resident through the visible PNEC form.
 second=context();q=page_for(second);q.goto(base+'pages/register.html#register',wait_until='networkidle')
 email=f'demo-resident-{run}@example.test';password=secrets.token_urlsafe(24)
 q.fill('#register-name','Synthetic Second Resident');q.fill('#register-email',email);q.fill('#register-password',password);q.fill('#register-confirm-password',password)
 q.locator('#register-neighborhood-select').select_option(str(nid));q.locator('#register-form button[type="submit"]').click();q.wait_for_url('**/pages/profile.html');q.wait_for_load_state('networkidle')
 seconduser=second.request.get(api+'/api/auth/me').json()['user'];assert seconduser['role']=='resident' and seconduser['id']!=pid
 assert write(second,'PATCH','/auth/profile',{'role':'admin'}).status==400
 assert write(second,'PATCH','/auth/profile',{'id':pid,'bio':'Rejected other resident edit'}).status==400
 assert write(second,'PATCH','/preparedness',{'meeting_point':'Synthetic private B '+run}).status==200
 original=resident.request.get(api+'/api/preparedness').json()
 own=second.request.get(api+f'/api/preparedness?user_id={pid}').json();assert own['meeting_point']=='Synthetic private B '+run
 assert resident.request.get(api+'/api/preparedness').json()['meeting_point']==original['meeting_point']
 assert write(second,'PUT','/check-ins',{'status':'safe','note':'SYNTHETIC PRIVATE B '+run,'user_id':pid,'neighborhood_id':other}).status==200
 checkins=second.request.get(api+'/api/check-ins').json()['check_ins'];assert all(c['user_id']==seconduser['id'] and c['neighborhood_id']==nid for c in checkins)
 assert all(c['user_id']!=seconduser['id'] for c in resident.request.get(api+'/api/check-ins').json()['check_ins'])
 hazard=write(second,'POST','/hazards',{'neighborhood_id':nid,'category':'other','location':'Synthetic private B '+run,'description':'SYNTHETIC QA only, no real hazard.'});assert hazard.status==201
 hid=hazard.json()['id'];assert all(h['id']!=hid for h in resident.request.get(api+'/api/hazards').json()['hazards'])
 assert write(resident,'PATCH',f'/hazards/{hid}',{'status':'resolved'}).status==403
 assert write(resident,'POST','/volunteer/tasks',{}).status==403
 assert write(resident,'POST','/announcements',{'message':'Rejected resident notice'}).status==403
 report['blockers']=['Unmodified backend application factory omits announcement blueprint registration. This local launcher repairs it explicitly; the reviewed backend registration patch and additive migration must be integrated separately before a release.']
 report['checks'].append('Real registration creates resident; role/id escalation rejected; household/check-in/hazard data isolated between two residents, including forged identity/neighborhood parameters')
 coordinator=context();cp=page_for(coordinator);login(cp,roles['coordinator'])
 assert write(coordinator,'POST','/volunteer/tasks',{'title':'Rejected cross-block shift','neighborhood_id':other}).status==403
 cp.goto(base+'pages/volunteer.html',wait_until='networkidle')
 form=cp.locator('[data-community-tools] form');form.locator('[name="title"]').fill('SYNTHETIC demo shift '+run);form.locator('[name="description"]').fill('Synthetic local testing only; not a real event.');form.locator('[name="neighborhood_id"]').select_option(str(nid));form.locator('[name="starts_at"]').fill((datetime.now()+timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'));form.locator('[name="capacity"]').fill('1');form.get_by_role('button',name='Post a shift',exact=True).click()
 expect(cp.get_by_role('heading',name='SYNTHETIC demo shift '+run,exact=True)).to_be_visible()
 page.goto(base+'pages/volunteer.html',wait_until='networkidle');card=page.locator('[data-community-tools] article').filter(has=page.get_by_role('heading',name='SYNTHETIC demo shift '+run,exact=True));card.get_by_role('button',name='Claim a slot',exact=True).click();expect(card.get_by_role('button',name='Cancel my signup',exact=True)).to_be_visible()
 tasks=second.request.get(api+'/api/volunteer/tasks').json()['tasks'];task=next(t for t in tasks if t['title']=='SYNTHETIC demo shift '+run);assert 'volunteers' not in task
 assert write(second,'POST',f'/volunteer/tasks/{task["id"]}/signup',{}).status==409
 card.get_by_role('button',name='Cancel my signup',exact=True).click();expect(card.get_by_role('button',name='Claim a slot',exact=True)).to_be_visible()
 # Public volunteer-interest form is independent of account roles.
 page.locator('#vol-name').fill('Synthetic volunteer reviewer');page.locator('#vol-email').fill(f'demo-interest-{run}@example.test');page.locator('#vol-role').select_option('cert_volunteer');page.locator('#vol-message').fill('SYNTHETIC LOCAL QA only.');page.locator('#vol-submit-btn').click();expect(page.locator('#vol-alert-success')).to_be_visible()
 report['checks'].append('Coordinator UI posts shift; resident UI claims/cancels; full capacity 409; no resident roster leakage; cross-neighborhood coordinator write 403; volunteer interest UI submitted')
 admin=context();ap=page_for(admin);login(ap,roles['admin'])
 assert admin.request.get(api+'/api/admin/publish/health').status==200
 assert resident.request.get(api+'/api/admin/publish/health').status==401
 for old in admin.request.get(api+'/api/announcements').json()['announcements']:
  if old['message'].startswith('SYNTHETIC') and 'demo notification' in old['message']:
   assert write(admin,'PATCH',f'/announcements/{old["id"]}',{'is_active':False}).status==200
 notice=write(admin,'POST','/announcements',{'message':'SYNTHETIC demo notification '+run+' — not an emergency.','level':'info','expires_at':(datetime.now(timezone.utc)+timedelta(hours=2)).isoformat()});assert notice.status==201
 ann=notice.json()['announcement']['id'];page.goto(base,wait_until='networkidle')
 banner=page.locator('#pnec-alert-banner');expect(banner).to_contain_text('SYNTHETIC demo notification '+run)
 item=banner.locator('article').filter(has_text='SYNTHETIC demo notification '+run);item.get_by_role('button',name='Dismiss community announcement',exact=True).focus();page.keyboard.press('Enter');expect(item).to_have_count(0)
 page.reload(wait_until='networkidle');expect(banner).not_to_contain_text('SYNTHETIC demo notification '+run)
 assert write(admin,'PATCH',f'/announcements/{ann}',{'message':'SYNTHETIC revised demo notification '+run+' — not an emergency.'}).status==200
 page.reload(wait_until='networkidle');expect(banner).to_contain_text('SYNTHETIC revised demo notification '+run)
 report['checks'].append('Actual admin notification API on explicitly repaired disposable backend; community source label, keyboard dismissal/persistence and changed-version reappearance; resident creation 403. Backend release patch and additive migration remain required.')
 page.goto(base+'pages/settings.html',wait_until='networkidle');page.locator('[data-theme="ocean"]').click();page.goto(base+'pages/fire-safety.html',wait_until='networkidle');assert page.locator('html').get_attribute('data-appearance-preset')=='ocean'
 page.goto(base+'pages/settings.html',wait_until='networkidle');page.select_option('#site-language','es');page.locator('#pnec-language-form button[type="submit"]').click();page.reload(wait_until='networkidle');assert page.locator('#site-language').input_value()=='es'
 page.locator('#pnec-language-form button[type="reset"]').click();page.locator('[data-theme="site-default"]').click()
 report['checks'].append('Unmocked browser theme and reviewed language preferences persist across routes/reload')
 page.goto(base+'pages/profile.html',wait_until='networkidle');page.locator('#pnec-account-dropdown > summary').click();page.locator('#navbar-logout-btn').click();page.wait_for_url(base);assert resident.request.get(api+'/api/auth/me').status==401
 report['checks'].append('Actual logout revokes account session')
 assert not errors,errors;report['page_errors']=errors;report['passed']=True
 for c in [resident,second,coordinator,admin]:c.close()
 browser.close()
(a.output_dir/'stakeholder-live-results.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: real registration/login/profile/logout, multi-resident privacy, role/CSRF-protected volunteer journeys and real notification rendering/dismissal/versioning on the explicit local compatibility fix, persisted preferences; synthetic disposable data only.')
