"""Release regression: test-quiz.py.

Run through scripts/run-release-tests.py with explicit frontend/backend roots.
Uses only the disposable build and isolated backend state selected by the runner.
"""
import json
import os
from pathlib import Path
import secrets
import sqlite3
import sys
import tempfile
import threading
from urllib.request import urlopen

from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server, WSGIRequestHandler

from release_test_support import FRONTEND_ROOT, BACKEND_ROOT, SITE_ROOT, PREVIEW_URL
from app import create_app, db
from app.config import Config
from app.models.user import User
from app.services.preparedness_service import QUIZ


class QuietHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        pass


def main():
    base = PREVIEW_URL
    # Refuse to certify stale built quiz/transport JavaScript.
    for path in ['assets/js/pages/community-tools.js', 'assets/js/api/auth-api.js',
                 'assets/js/api/preparedness-api.js', 'assets/js/utils/errors.js']:
        with urlopen(base + '/' + path, timeout=10) as response:
            assert response.read() == (FRONTEND_ROOT / path).read_bytes(), path
    print('PASS: served quiz and request JavaScript match current source', flush=True)

    with tempfile.TemporaryDirectory(prefix='pnec-issue29-') as directory:
        database = Path(directory) / 'quiz.db'
        Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(database)
        Config.ADMIN_PASSWORD = ''
        Config.SECRET_KEY = secrets.token_hex(32)
        Config.UPLOAD_FOLDER = str(Path(directory) / 'uploads')
        app = create_app()
        app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
        with app.app_context():
            user = User(email='quiz-audit@example.test', display_name='Quiz audit',
                        password_hash='unused-synthetic-account', role='resident')
            token = user.generate_token()
            db.session.add(user)
            db.session.commit()
            user_id = user.id
        server = make_server('127.0.0.1', 0, app, threaded=True,
                             request_handler=QuietHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        invalidate_next = False

        def api_route(route):
            nonlocal invalidate_next
            options = {'url': route.request.url.replace(':8425', ':' + str(server.server_port), 1)}
            if (invalidate_next and route.request.method == 'POST'
                    and route.request.url.endswith('/api/preparedness/quiz')):
                # Exercise real Flask validation and its error message in the UI.
                options['post_data'] = json.dumps({'answers': {}})
                invalidate_next = False
            route.continue_(**options)

        def saved_answers():
            with sqlite3.connect(database) as connection:
                row = connection.execute(
                    'SELECT quiz_answers FROM household_preparedness WHERE user_id=?',
                    (user_id,)).fetchone()
                assert row is not None
                return json.loads(row[0])

        try:
            with sync_playwright() as play:
                browser = play.chromium.launch()
                context = browser.new_context()
                context.route('**/*', lambda route: route.continue_()
                              if route.request.url.startswith(base + '/') else route.abort())
                context.route('http://127.0.0.1:8425/**', api_route)
                context.add_init_script('localStorage.setItem("pnec_token", ' + json.dumps(token) + ');')
                page = context.new_page()
                page.goto(base + '/pages/checklist.html', wait_until='domcontentloaded')
                quiz = page.locator('.community-tools section').filter(
                    has=page.get_by_role('heading', name='Preparedness assessment', exact=True)).last
                expect(quiz.locator('select')).to_have_count(10)
                for ready_count in [0, 5, 10]:
                    answers = {key: index < ready_count for index, (key, _, _) in enumerate(QUIZ)}
                    tips = [tip for key, _, tip in QUIZ if not answers[key]][:3]
                    for key, value in answers.items():
                        quiz.locator('select[name="' + key + '"]').select_option('yes' if value else 'no')
                    with page.expect_response(lambda r: r.request.method == 'POST'
                                              and r.url.endswith('/api/preparedness/quiz')) as sent:
                        quiz.get_by_role('button', name='Save assessment', exact=True).click()
                    assert sent.value.status == 200
                    assert sent.value.json() == {'score': ready_count * 10, 'recommendations': tips}
                    expect(quiz.get_by_text('Saved.', exact=True)).to_be_visible()
                    assert saved_answers() == answers
                    page.reload(wait_until='domcontentloaded')
                    expect(quiz.locator('select')).to_have_count(10)
                    for key, value in answers.items():
                        expect(quiz.locator('select[name="' + key + '"]')).to_have_value('yes' if value else 'no')
                    expect(quiz.get_by_role('status').first).to_contain_text(f'{ready_count * 10}%')
                    for tip in tips:
                        expect(quiz.get_by_role('status').first).to_contain_text(tip)
                    if not tips:
                        expect(quiz.get_by_role('status').first).to_contain_text('practice your plan')
                    print(f'PASS: {ready_count}/10 score, ordered recommendations, Saved message, SQLite and reload', flush=True)
                before = saved_answers()
                invalidate_next = True
                with page.expect_response(lambda r: r.request.method == 'POST'
                                          and r.url.endswith('/api/preparedness/quiz')) as rejected:
                    quiz.get_by_role('button', name='Save assessment', exact=True).click()
                assert rejected.value.status == 400
                expect(quiz.get_by_text('Answer all ten questions with yes or no.', exact=True)).to_be_visible()
                assert saved_answers() == before
                page.reload(wait_until='domcontentloaded')
                expect(quiz.get_by_role('status').first).to_contain_text('100%')
                print('PASS: real API 400 is displayed; invalid submission preserves saved answers', flush=True)
                browser.close()
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
            with app.app_context():
                db.session.remove()
                db.engine.dispose()


if __name__ == '__main__':
    main()
