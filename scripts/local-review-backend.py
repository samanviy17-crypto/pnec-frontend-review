"""Run a disposable, loopback-only PNEC backend using copied source and synthetic data.

Usage: python scripts/local-review-backend.py --backend-root /path/pnec-backend-review
Dependencies: the backend requirements in an external virtual environment.
No production secrets, database, uploads, user records or outbound providers are used.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import sys
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--backend-root', type=Path, required=True)
parser.add_argument('--port', type=int, default=8425)
parser.add_argument('--resume-state', type=Path, help='Reuse only an existing private disposable state directory')
parser.add_argument('--enable-announcements', action='store_true', help='Register the existing announcement blueprint locally; backend release still needs the supplied patch')
args = parser.parse_args()
source = args.backend_root.resolve(strict=True)
assert (source / 'app/config.py').is_file(), 'Select the PNEC backend source'
with socket.socket() as probe:
    probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    probe.bind(('127.0.0.1', args.port))  # Fail before creating state if port is occupied.
state = args.resume_state.resolve(strict=True) if args.resume_state else Path(tempfile.mkdtemp(prefix='pnec-local-review-'))
if args.resume_state:
    assert state.name.startswith('pnec-local-review-') and state.stat().st_mode & 0o077 == 0
    assert (state / 'review.db').is_file() and (state / 'credentials.json').is_file()
    prior = json.loads((state / 'credentials.json').read_text())
    assert Path(prior['state_dir']).resolve() == state and prior['email'].endswith('@example.test')
state.chmod(0o700)
copy = state / 'backend'
# Copy application/migration source only. Never copy .env, instance, DB or uploads.
for name in ([] if args.resume_state else ['app', 'migrations']):
    shutil.copytree(source / name, copy / name,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.env', '*.db', '*.sqlite*'))
sys.path.insert(0, str(copy))
# Eliminate inherited provider, publication and production credentials before imports.
for name in ['DB_ENDPOINT','DB_USERNAME','DB_PASSWORD','DATABASE_URL','ADMIN_PASSWORD',
             'MAIL_USERNAME','MAIL_PASSWORD','MAIL_SERVER','GITHUB_TOKEN','GEMINI_API_KEY',
             'GROQ_API_KEY','VAPID_PRIVATE_KEY','VAPID_PUBLIC_KEY','REDIS_URL']:
    os.environ.pop(name, None)
os.environ.update(FLASK_ENV='development', SECRET_KEY=secrets.token_urlsafe(48),
                  PNEC_REVIEW_EPHEMERAL='true', FRONTEND_URL='http://localhost:8766', MAIL_DELIVERY='disabled')
import requests

def no_provider(*args, **kwargs):
    raise requests.ConnectionError('External providers are disabled in the disposable local preview.')
requests.sessions.Session.request = no_provider
from app.config import Config, DevelopmentConfig
Config.FLASK_PORT = args.port
Config.SQLALCHEMY_DATABASE_URI = f'sqlite:///{state / "review.db"}'
Config.UPLOAD_FOLDER = str(state / 'uploads')
Config.SECURITY_STATE_PATH = str(state / 'security-limits.json')
Config.SECRET_KEY = os.environ['SECRET_KEY']
Config.ADMIN_PASSWORD = None
Config.MAIL_SERVER = None
Config.MAIL_DELIVERY = 'disabled'
Config.FRONTEND_URL = 'http://localhost:8766'
# Exact loopback origins only. The existing CORS and CSRF middleware stays enabled.
import app.utils.csrf as csrf
csrf.APPROVED_ORIGINS[:] = [f'http://{host}:{port}' for host in ['localhost','127.0.0.1'] for port in [8766,4000,8080]]
from app import create_app, db
from flask import jsonify
from flask_migrate import upgrade
from app.models.neighborhood import Neighborhood
from app.models.user import User
from werkzeug.security import generate_password_hash
app = create_app(initialize_database=False)
compatibility_fixes = []
if args.enable_announcements:
    # Existing routes/decorators unchanged; only repair the omitted registration
    # in this disposable adapter, never the backend checkout or production app.
    from app.routes.announcement import announcements_bp
    app.register_blueprint(announcements_bp, url_prefix='/api')
    compatibility_fixes.append('register-existing-announcements-blueprint')
# Development cookies are HttpOnly, SameSite=Lax; HTTP loopback needs Secure=False.
# No production configuration class or security middleware is changed.
assert app.config['CSRF_PROTECTION_ENABLED'] is True
assert app.config['SESSION_COOKIE_HTTPONLY'] is True
assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'
with app.app_context():
    upgrade(directory=str(copy / 'migrations'))
    if args.enable_announcements:
        # The frozen backend migration also omits this existing model. This
        # additive table is created ONLY in the guarded disposable database.
        from app.models.announcement import Announcement
        Announcement.__table__.create(bind=db.engine, checkfirst=True)
        compatibility_fixes.append('create-missing-announcements-table')
    if args.resume_state:
        credentials = prior
    else:
        neighborhood = Neighborhood(name='Synthetic Local Review Neighborhood', number=999, zone='A')
        db.session.add(neighborhood); db.session.flush()
        credentials = {'email':'local-review@example.test','password':secrets.token_urlsafe(24),
                       'display_name':'Local Review Resident (synthetic)', 'frontend':'http://localhost:8766/',
                       'backend':f'http://localhost:{args.port}', 'state_dir':str(state),
                       'note':'Disposable local-only account; never use production credentials or resident data.'}
        resident = User(email=credentials['email'],password_hash=generate_password_hash(credentials['password']),
                        display_name=credentials['display_name'],role='resident',neighborhood_id=neighborhood.id)
        db.session.add(resident); db.session.commit()
credential_file = state / 'credentials.json'
credential_file.write_text(json.dumps(credentials, indent=2)+'\n'); credential_file.chmod(0o600)
@app.get('/api/local-review')
def local_review():
    return jsonify({'disposable':True,'external_providers':False,'synthetic_data_only':True,'local_compatibility_fixes':compatibility_fixes})
from werkzeug.serving import make_server
server = make_server('127.0.0.1', args.port, app, threaded=True)
print(f'Disposable backend: http://localhost:{args.port}', flush=True)
print(f'Private local credentials: {credential_file}', flush=True)
print(f'Disposable state (remove after stopping): {state}', flush=True)
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
