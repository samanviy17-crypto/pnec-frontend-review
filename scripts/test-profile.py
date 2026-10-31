"""Release regression: test-profile.py.

Run through scripts/run-release-tests.py with explicit frontend/backend roots.
Uses only the disposable build and isolated backend state selected by the runner.
"""
from pathlib import Path
import secrets
import os
import sqlite3
import sys
import tempfile
import threading
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server, WSGIRequestHandler

from release_test_support import FRONTEND_ROOT, BACKEND_ROOT, SITE_ROOT, PREVIEW_URL
from app.config import Config
from app import create_app, db
from app.models.event import Event
from app.models.user import User
from app.routes.auth import _rate_buckets
from app.services import risk_service


class QuietHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        pass


with tempfile.TemporaryDirectory(prefix='pnec-profile-test-') as directory:
    database = Path(directory) / 'profile.db'
    Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(database)
    Config.ADMIN_PASSWORD = ''
    Config.SECRET_KEY = secrets.token_hex(32)
    risk_service.get_risk_assessment = lambda *args, **kwargs: {
        'fire_level': 'LOW', 'flood_level': 'LOW', 'heat_level': 'LOW',
        'fire_score': 1, 'flood_score': 1, 'heat_score': 1, 'is_stale': False,
        'updated_at': datetime.now().isoformat()}

    def start():
        app = create_app()
        app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
        _rate_buckets.clear()
        server = make_server('127.0.0.1', 0, app, threaded=True, request_handler=QuietHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return app, server, thread

    app, server, thread = start()
    with app.app_context():
        db.session.add(Event(title='Profile browser test event', description='Isolated test event',
                             date=datetime.now() + timedelta(days=1), location='Test location'))
        db.session.commit()

    def verify_database():
        with sqlite3.connect(database) as connection:
            row = connection.execute('SELECT display_name,email,phone,password_hash FROM users WHERE email=?',
                                     (updated_email,)).fetchone()
            assert row and row[:3] == ('Updated Browser Resident', updated_email, '+18585550100')
            assert row[3] != password

    try:
        with sync_playwright() as play:
            browser = play.chromium.launch()
            context = browser.new_context()
            context.route('**/*', lambda route: route.continue_() if route.request.url.startswith(PREVIEW_URL + '/') else route.abort())
            context.route('http://127.0.0.1:8425/**', lambda route: route.continue_(
                url=route.request.url.replace(':8425', ':' + str(server.server_port), 1)))
            page = context.new_page()
            messages = []
            page.on('console', lambda message: messages.append(message.text))
            page.on('pageerror', lambda error: messages.append(str(error)))
            email = 'profile-' + secrets.token_hex(8) + '@example.test'
            updated_email = 'updated-' + secrets.token_hex(8) + '@example.test'
            password = secrets.token_urlsafe(24)
            base = PREVIEW_URL
            page.goto(base + '/', wait_until='domcontentloaded')
            page.goto(base + '/pages/register.html#register', wait_until='domcontentloaded')
            for field, value in [('name', 'Browser Resident'), ('email', email), ('password', password), ('confirm-password', password)]:
                page.locator('#register-' + field).fill(value)
            page.locator('#register-form button[type=submit]').click()
            page.wait_for_url('**/pages/profile.html')
            expect(page.locator('.profile-name')).to_contain_text('Browser Resident')
            with sqlite3.connect(database) as connection:
                assert connection.execute('SELECT email FROM users WHERE email=?', (email,)).fetchone()
            page.locator('#profile-signout-btn').click()
            page.wait_for_url(base + '/')

            def login(address):
                page.goto(base + '/pages/register.html#login', wait_until='domcontentloaded')
                page.locator('#login-email').fill(address)
                page.locator('#login-password').fill(password)
                page.locator('#login-form button[type=submit]').click()
                page.wait_for_url('**/pages/profile.html')
                expect(page.locator('#edit-email')).to_have_value(address)

            login(email)
            page.locator('#edit-display-name').fill('Discard me')
            page.locator('#profile-cancel-btn').click()
            expect(page.locator('#edit-display-name')).to_have_value('Browser Resident')
            page.locator('#edit-phone').fill('not a number')
            page.locator('#profile-save-btn').click()
            expect(page.locator('#profile-error')).to_contain_text('phone number')
            page.locator('#edit-display-name').fill('Updated Browser Resident')
            page.locator('#edit-email').fill(updated_email)
            page.locator('#edit-phone').fill('+1 (858) 555-0100')
            page.locator('#profile-save-btn').click()
            expect(page.locator('#profile-success')).to_be_visible()
            expect(page.locator('.profile-email')).to_have_text(updated_email)
            expect(page.locator('.profile-phone')).to_contain_text('+18585550100')
            verify_database()
            page.reload(wait_until='domcontentloaded')
            expect(page.locator('#edit-phone')).to_have_value('+18585550100')
            token = page.evaluate("sessionStorage.getItem('pnec_token')")
            assert token, 'Nonpersistent login must provide a session-storage bearer token.'
            page.locator('#profile-signout-btn').click()
            page.wait_for_url(base + '/')
            assert context.request.get(f'http://127.0.0.1:{server.server_port}/api/auth/me',
                                       headers={'Authorization': 'Bearer ' + token}).status == 401
            login(updated_email)

            # Stop and recreate the actual Flask app/server against the same file.
            server.shutdown(); thread.join(); server.server_close()
            with app.app_context():
                db.session.remove(); db.engine.dispose()
            app, server, thread = start()
            page.reload(wait_until='domcontentloaded')
            expect(page.locator('#edit-email')).to_have_value(updated_email)
            expect(page.locator('#edit-phone')).to_have_value('+18585550100')
            verify_database()

            navigation = page.get_by_role('navigation', name='PNEC profile navigation')
            links = navigation.locator('a').evaluate_all('(links) => links.map(link => ({label:link.textContent,url:link.href}))')
            assert len(links) == 8
            for link in links:
                response = page.goto(link['url'], wait_until='domcontentloaded')
                assert response.status == 200, link['label']
                page.wait_for_function("typeof fetchCurrentUser === 'function'")
                assert page.evaluate('fetchCurrentUser()')['email'] == updated_email
                if link['label'] == 'Calendar':
                    expect(page.locator('#pnec-calendar .calendar-grid')).to_be_visible()
                    page.locator('#view-list-btn').click()
                    expect(page.locator('#events-list-container')).to_contain_text('Profile browser test event')
                if link['label'] == 'Risk Watch':
                    expect(page.locator('#risk-widget')).to_be_visible()
                if link['label'] == 'Hazard Reporting':
                    expect(page.locator('#hazard-reporting')).to_be_visible()
            page.goto(base + '/pages/profile.html', wait_until='domcontentloaded')
            expect(page.locator('#edit-email')).to_have_value(updated_email)
            page.set_viewport_size({'width': 390, 'height': 844})
            expect(page.locator('#edit-email')).to_be_visible()
            assert page.locator('#edit-email').evaluate('(element) => element.getBoundingClientRect().width <= window.innerWidth')
            page.set_viewport_size({'width': 1280, 'height': 720})
            # Server validation remains authoritative even when bypassing the UI.
            with app.app_context():
                other = User(email='other@example.test', display_name='Other', password_hash='test-only-unused')
                db.session.add(other); db.session.commit(); other_id = other.id
            result = page.evaluate("""async id => {
                const response = await fetch(API_BASE+'/api/auth/profile', {method:'PATCH', credentials:'include',
                    headers:_getAuthHeaders(), body:JSON.stringify({id,display_name:'Unauthorized change'})});
                return response.status;
            }""", other_id)
            assert result == 400
            with app.app_context():
                assert db.session.get(User, other_id).display_name == 'Other'
            page.locator('#edit-email').fill('other@example.test')
            page.locator('#profile-save-btn').click()
            expect(page.locator('#profile-error')).to_contain_text('already exists')
            assert not any(password in message or (token and token in message) for message in messages)
            page.locator('#profile-signout-btn').click(); page.wait_for_url(base + '/')
            page.goto(base + '/pages/profile.html', wait_until='domcontentloaded')
            page.wait_for_url('**/pages/register.html?**')
            browser.close()
        print('PASS: registration, cookie/bearer login/logout, edit/cancel/validation, direct database checks, reload/new-email login, Flask restart persistence, calendar and all eight navigation links, ownership and protected profile.')
    finally:
        server.shutdown(); thread.join(); server.server_close()
        with app.app_context():
            db.session.remove(); db.engine.dispose()
