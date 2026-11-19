"""Apply the proposed backend patch only to copied source; migrate fresh synthetic state and test HTTP role/CSRF decisions."""
import argparse,sys
from pathlib import Path
import shutil,subprocess,tempfile,time,json,socket,sqlite3,secrets
from datetime import datetime
from urllib.request import urlopen
from playwright.sync_api import sync_playwright
from werkzeug.security import generate_password_hash
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--backend-root',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
a=parser.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
root=Path(__file__).resolve().parents[1];source=a.backend_root.resolve(strict=True);work=Path(tempfile.mkdtemp(prefix='pnec-announcement-patch-'));copy=work/'backend'
for name in ['app','migrations']:shutil.copytree(source/name,copy/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.env','*.db'))
subprocess.run(['git','apply',str(root/'docs/backend-patches/register-announcements.patch')],cwd=copy,check=True)
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
log=work/'server.log';handle=log.open('w');process=subprocess.Popen([sys.executable,'-B',str(root/'scripts/local-review-backend.py'),'--backend-root',str(copy),'--port',str(port)],stdout=handle,stderr=subprocess.STDOUT)
try:
 for _ in range(100):
  if process.poll() is not None:raise AssertionError(log.read_text()[-3000:])
  try:
   with urlopen(f'http://localhost:{port}/api/ready',timeout=1) as r:ready=json.load(r)
   break
  except OSError:time.sleep(.1)
 else:raise AssertionError('Patch backend did not become ready')
 assert ready['schema_revision']=='0002_announcements',ready
 credential_path=next(x.split(': ',1)[1] for x in log.read_text().splitlines() if x.startswith('Private local credentials: '));creds=json.loads(Path(credential_path).read_text());state=Path(creds['state_dir']);password=secrets.token_urlsafe(24)
 with sqlite3.connect(state/'review.db') as db:db.execute('insert into users(email,password_hash,display_name,role,is_active,created_at) values(?,?,?,?,?,?)',('patch-admin@example.test',generate_password_hash(password),'Synthetic patch admin','admin',True,datetime.now().isoformat()));db.commit()
 with sync_playwright() as p:
  request=p.request.new_context(base_url=f'http://localhost:{port}',extra_http_headers={'Origin':'http://localhost:8766'})
  assert request.get('/api/announcements').status==200
  assert request.post('/api/announcements',data={'message':'Rejected anonymous'}).status==401
  assert request.post('/api/auth/login',data={'email':creds['email'],'password':creds['password']}).status==200
  assert request.post('/api/announcements',data={'message':'Rejected resident'}).status==403
  assert request.post('/api/auth/login',data={'email':'patch-admin@example.test','password':password}).status==200
  assert request.post('/api/announcements',data={'message':'SYNTHETIC patch verification','level':'info'}).status==201
  assert request.post('/api/announcements',data={'message':'Rejected origin'},headers={'Origin':'https://unapproved.example.test'}).status==403
  assert len(request.get('/api/announcements').json()['announcements'])==1
  request.dispose()
 (a.output_dir/'backend-patch-results.json').write_text(json.dumps({'patch':'docs/backend-patches/register-announcements.patch','fresh_migration':ready,'actual_HTTP':'anonymous read 200/write 401; resident write 403; admin write 201; unapproved Origin 403; persisted public list','production_applied':False,'backend_checkout_changed':False,'passed':True},indent=2)+'\n')
 print('PASS: proposed backend patch applies and migrates fresh isolated SQLite; actual HTTP auth/CSRF/admin/resident decisions passed; no backend checkout changes.')
finally:process.terminate();process.wait(timeout=10);handle.close()
