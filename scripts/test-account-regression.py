"""Release regression: test-account-regression.py.

Run through scripts/run-release-tests.py with explicit frontend/backend roots.
Uses only the disposable build and isolated backend state selected by the runner.
"""
from pathlib import Path
import base64
import json
import os
import re
import secrets
import sys
import tempfile
import threading

from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server, WSGIRequestHandler
import requests

from release_test_support import FRONTEND_ROOT, BACKEND_ROOT, SITE_ROOT, PREVIEW_URL
from app.config import Config
from app import create_app, db
from app.models.user import User


class Quiet(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        pass


def no_provider(*args, **kwargs):
    raise requests.ConnectionError('External providers disabled in account regression')


requests.sessions.Session.request = no_provider
base = PREVIEW_URL
checks = []
with tempfile.TemporaryDirectory(prefix='pnec-account-regression-') as temp:
    Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(Path(temp) / 'accounts.db')
    Config.ADMIN_PASSWORD = ''
    Config.SECRET_KEY = secrets.token_hex(32)
    Config.UPLOAD_FOLDER = str(Path(temp) / 'uploads')
    app = create_app()
    app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False, FRONTEND_URL=base)
    server = make_server('127.0.0.1', 0, app, threaded=True, request_handler=Quiet)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as play:
            browser = play.chromium.launch()
            context = browser.new_context()
            context.route('**/*', lambda r: r.continue_() if r.request.url.startswith(PREVIEW_URL + '/') else r.abort())
            context.route('http://127.0.0.1:8425/**', lambda r: r.continue_(
                url=r.request.url.replace(':8425', ':' + str(server.server_port), 1)))
            page = context.new_page()
            # The form must handle submission while startup session requests wait.
            held = []
            context.route('**/api/auth/me', lambda r: held.append(r))
            page.goto(base + '/pages/register.html#login', wait_until='domcontentloaded')
            page.locator('#login-email').fill('missing@example.test')
            page.locator('#login-password').fill('wrong-password')
            page.locator('#login-submit-btn').click()
            expect(page.locator('#login-error')).to_contain_text('Incorrect email or password')
            context.unroute('**/api/auth/me')
            for route in held:
                route.fulfill(status=401, json={'message': 'Not signed in.'})
            checks.append('Login handles submission while initial session lookup is pending')

            email = 'account-' + secrets.token_hex(6) + '@example.test'
            password = secrets.token_urlsafe(24)
            page.goto(base + '/pages/register.html#register', wait_until='domcontentloaded')
            for field, value in [('name', 'Account Resident'), ('email', email), ('password', password), ('confirm-password', password)]:
                page.locator('#register-' + field).fill(value)
            page.locator('#register-form button[type=submit]').click()
            page.wait_for_url('**/pages/profile.html')
            expect(page.locator('#edit-neighborhood')).to_be_enabled()
            page.locator('#edit-neighborhood').select_option(index=1)
            selected = page.locator('#edit-neighborhood').input_value()
            page.locator('#profile-save-btn').click()
            expect(page.locator('#profile-success')).to_be_visible()

            # Backend outage differs from an expired session and supports retry.
            context.route('**/api/auth/me', lambda r: r.fulfill(status=502, body='<html>Unavailable</html>'))
            page.reload(wait_until='domcontentloaded')
            expect(page.locator('#profile-load-error')).to_contain_text('Unable to load')
            assert '/pages/profile.html' in page.url
            context.unroute('**/api/auth/me')
            page.locator('#profile-retry-btn').click()
            expect(page.locator('#edit-email')).to_have_value(email)
            checks.append('Profile unavailable state and retry preserve authenticated navigation')

            context.route('**/api/neighborhoods', lambda r: r.fulfill(status=503, json={'message': 'Unavailable'}))
            page.reload(wait_until='domcontentloaded')
            expect(page.locator('#edit-neighborhood')).to_be_disabled()
            page.locator('#edit-display-name').fill('Preserved Neighborhood')
            page.locator('#profile-save-btn').click()
            expect(page.locator('#profile-success')).to_be_visible()
            with app.app_context():
                assert str(User.query.filter_by(email=email).first().neighborhood_id) == selected
            context.unroute('**/api/neighborhoods')
            page.reload(wait_until='domcontentloaded')
            expect(page.locator('#edit-neighborhood')).to_have_value(selected)
            checks.append('Unavailable neighborhood list cannot clear the saved neighborhood')

            png = page.evaluate("""() => { const c=document.createElement('canvas');c.width=20;c.height=20;
                c.getContext('2d').fillRect(0,0,20,20);return c.toDataURL('image/png').split(',')[1]; }""")
            photo = {'name': 'fixture.png', 'mimeType': 'image/png', 'buffer': base64.b64decode(png)}
            page.locator('#avatar-change-btn').click()
            dialog = page.get_by_role('dialog', name='Change Profile Picture')
            expect(dialog).to_be_visible()
            expect(dialog).to_have_attribute('aria-modal', 'true')
            expect(page.locator('#avatar-drop-zone')).to_be_focused()
            page.keyboard.press('Shift+Tab')
            expect(page.locator('#avatar-modal-cancel')).to_be_focused()
            page.keyboard.press('Tab')
            expect(page.locator('#avatar-drop-zone')).to_be_focused()
            # Native modal inertness blocks attempts to move focus into the page.
            page.locator('#profile-save-btn').evaluate('(el) => el.focus()')
            assert page.evaluate("document.activeElement.closest('dialog') !== null")
            page.keyboard.press('Escape')
            expect(dialog).not_to_be_visible()
            expect(page.locator('#avatar-change-btn')).to_be_focused()
            page.locator('#avatar-change-btn').click()
            page.locator('#avatar-file-input').set_input_files(photo)
            expect(page.locator('#avatar-modal-save')).to_be_enabled()
            page.locator('#avatar-modal-save').focus()
            page.keyboard.press('Tab')
            expect(page.locator('#avatar-drop-zone')).to_be_focused()
            page.keyboard.press('Shift+Tab')
            expect(page.locator('#avatar-modal-save')).to_be_focused()
            page.locator('#avatar-file-input').set_input_files({'name':'broken.png','mimeType':'image/png','buffer':b'not an image'})
            expect(page.locator('#avatar-error')).to_contain_text('could not be read')
            expect(page.locator('#avatar-modal-save')).to_be_disabled()
            page.locator('#avatar-file-input').set_input_files({'name':'large.png','mimeType':'image/png','buffer':b'x' * (5*1024*1024+1)})
            expect(page.locator('#avatar-error')).to_contain_text('File too large')
            expect(page.locator('#avatar-modal-save')).to_be_disabled()
            # Bypass the browser's accept filter through an actual drop event.
            page.locator('#avatar-drop-zone').evaluate("""el => { const dt=new DataTransfer();
                dt.items.add(new File(['plain text'],'invalid.txt',{type:'text/plain'}));
                el.dispatchEvent(new DragEvent('drop',{bubbles:true,dataTransfer:dt})); }""")
            expect(page.locator('#avatar-error')).to_contain_text('Choose a JPG')
            page.locator('#avatar-file-input').set_input_files(photo)
            expect(page.locator('#avatar-modal-save')).to_be_enabled()
            page.locator('#avatar-modal-save').click()
            page.locator('#profile-cancel-btn').click()
            expect(page.locator('#profile-avatar-display img')).to_have_count(0)
            page.locator('#avatar-change-btn').click()
            page.locator('#avatar-file-input').set_input_files(photo)
            expect(page.locator('#avatar-modal-save')).to_be_enabled()
            page.locator('#avatar-modal-save').click()
            page.locator('#profile-save-btn').click()
            expect(page.locator('#profile-success')).to_be_visible()
            page.reload(wait_until='domcontentloaded')
            expect(page.locator('#profile-avatar-display img')).to_have_attribute('src', re.compile('^data:image/jpeg;base64,'))
            with app.app_context():
                assert User.query.filter_by(email=email).first().avatar_url.startswith('data:image/jpeg;base64,')
            checks.append('Avatar validation, decode failure, oversize rejection, cancel and persistence')
            # High-entropy 400px input previously exceeded MySQL TEXT after resize.
            noisy = page.evaluate("""() => {const c=document.createElement('canvas');c.width=c.height=400;
                const ctx=c.getContext('2d'), img=ctx.createImageData(400,400);
                let state=17;for(let i=0;i<img.data.length;i+=4){for(let j=0;j<3;j++){
                  state=(Math.imul(state,1664525)+1013904223)>>>0;img.data[i+j]=state>>>24;}
                  img.data[i+3]=255;}ctx.putImageData(img,0,0);return c.toDataURL('image/png').split(',')[1];}""")
            page.locator('#avatar-change-btn').click()
            page.locator('#avatar-file-input').set_input_files({'name':'noise.png','mimeType':'image/png','buffer':base64.b64decode(noisy)})
            expect(page.locator('#avatar-modal-save')).to_be_enabled()
            assert page.locator('#avatar-preview-img').get_attribute('src').__len__() <= 50000
            page.locator('#avatar-modal-save').click()
            expect(page.locator('#avatar-change-btn')).to_be_focused()
            page.locator('#profile-save-btn').click()
            expect(page.locator('#profile-success')).to_be_visible()
            with app.app_context():
                saved_photo = User.query.filter_by(email=email).first().avatar_url
                assert len(saved_photo.encode('ascii')) <= 60000
            checks.append('Modal semantics, focus containment, Escape/restoration; noisy photo fits MySQL TEXT')

            for width in [320, 390, 768, 1280]:
                page.set_viewport_size({'width':width,'height':900})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), ('profile', width)
                page.locator('#avatar-change-btn').click()
                expect(page.locator('#avatar-modal-save')).to_be_visible()
                assert page.locator('.avatar-modal').evaluate('(e)=>e.getBoundingClientRect().width <= innerWidth')
                page.locator('#avatar-modal-cancel').click()
            context.route('**/api/auth/logout', lambda r: r.abort())
            page.locator('#profile-signout-btn').click()
            expect(page.locator('#profile-signout-error')).to_contain_text('Unable to confirm sign out')
            assert page.evaluate("!!(localStorage.getItem('pnec_token') || sessionStorage.getItem('pnec_token'))")
            context.unroute('**/api/auth/logout')
            page.locator('#profile-signout-btn').click()
            page.wait_for_url(base + '/')
            checks.append('Failed logout retains credentials for retry; successful retry signs out')

            page.goto(base + '/pages/forgot-password.html', wait_until='domcontentloaded')
            page.locator('#forgot-email').fill(email)
            page.locator('#forgot-submit-btn').click()
            expect(page.locator('#forgot-success')).to_contain_text('If that email is registered')
            body = app.extensions['account_mail_outbox'][-1].body
            link = re.search(r'http://[^\s]+', body).group()
            replacement = secrets.token_urlsafe(24)
            page.goto(link, wait_until='domcontentloaded')
            page.locator('#reset-password').fill(replacement)
            page.locator('#reset-confirm').fill(replacement)
            page.locator('#reset-form button').click()
            expect(page.locator('#reset-success')).not_to_be_empty()
            page.goto(link, wait_until='domcontentloaded')
            page.locator('#reset-password').fill(replacement)
            page.locator('#reset-confirm').fill(replacement)
            page.locator('#reset-form button').click()
            expect(page.locator('#reset-error')).to_contain_text('invalid or expired')
            page.goto(base + '/pages/register.html#login', wait_until='domcontentloaded')
            for width in [320, 390, 768, 1280]:
                page.set_viewport_size({'width':width,'height':900})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), ('login', width)
            page.locator('#login-email').fill(email)
            page.locator('#login-password').fill(replacement)
            page.locator('#login-submit-btn').click()
            page.wait_for_url('**/pages/profile.html')
            expect(page.locator('#edit-email')).to_have_value(email)
            checks.append('Captured-mail password reset, one-time link rejection and new-password login')
            checks.append('Login/profile fit 320, 390, 768 and 1280px; avatar modal remains usable')
            browser.close()
        for check in checks:
            print('PASS:', check)
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
