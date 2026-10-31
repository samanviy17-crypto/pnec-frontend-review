"""Actual upload worker/gallery with isolated Flask and synthetic image content."""
import base64
import mimetypes
from pathlib import Path
import secrets
import tempfile
from urllib.parse import urlsplit, unquote
from playwright.sync_api import sync_playwright, expect
from werkzeug.security import generate_password_hash
from release_test_support import FRONTEND_ROOT, BACKEND_ROOT, SITE_ROOT
from app import create_app, db
from app.config import Config
from app.models.user import User

ORIGIN = 'https://pnec-review.invalid'
API = 'https://api.pnec-review.invalid'
PNG = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jG3sAAAAASUVORK5CYII='
with tempfile.TemporaryDirectory(prefix='pnec-media-release-') as directory:
    Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(Path(directory) / 'media.db')
    Config.SECRET_KEY = secrets.token_hex(32)
    Config.ADMIN_PASSWORD = ''
    Config.UPLOAD_FOLDER = str(Path(directory) / 'uploads')
    app = create_app()
    app.config.update(TESTING=True)
    with app.app_context():
        user = User(email='media-browser@example.test', display_name='Synthetic', role='admin', password_hash=generate_password_hash(secrets.token_urlsafe(32)))
        token = user.generate_token()
        db.session.add(user)
        db.session.commit()
    observed = []
    with sync_playwright() as play:
        browser = play.chromium.launch()
        context = browser.new_context()
        context.add_init_script('localStorage.setItem("pnec_token", '+repr(token)+');')
        def serve(route):
            request = route.request
            url = urlsplit(request.url)
            if url.path.startswith('/api/') or url.path.startswith('/static/uploads/'):
                assert request.url.startswith(API + '/'), 'Media/API fell back to frontend or localhost'
                assert request.method in ('GET', 'HEAD', 'OPTIONS') or (request.method == 'POST' and url.path == '/api/media')
                headers = {k: v for k, v in request.headers.items() if k.lower() in ('authorization', 'content-type')}
                headers['Origin'] = ORIGIN
                with app.app_context():
                    with app.test_client() as client:
                        response = client.open(url.path + ('?' + url.query if url.query else ''), method=request.method, headers=headers, data=request.post_data_buffer)
                observed.append((url.path, request.method, response.status_code))
                headers = {k: v for k, v in response.headers.items() if k.lower() not in ('content-length', 'set-cookie')}
                route.fulfill(status=response.status_code, headers=headers, body=response.data)
            elif url.netloc == urlsplit(ORIGIN).netloc:
                file = SITE_ROOT / unquote(url.path).lstrip('/')
                if file.is_dir(): file /= 'index.html'
                if file.is_file(): route.fulfill(path=str(file), content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
                else: route.fulfill(status=404, body='')
            else:
                route.abort()
        context.route('**/*', serve)
        page = context.new_page()
        page.goto(ORIGIN + '/pages/gallery.html', wait_until='domcontentloaded')
        page.wait_for_function('typeof uploadMediaPost === "function"')
        for title in ('First', 'Second'):
            result = page.evaluate('''async args => {
                const body = new FormData(); body.set('title', args.title);
                body.set('file', new Blob([Uint8Array.from(atob(args.png), c => c.charCodeAt(0))], {type:'image/png'}), 'same.png');
                return await uploadMediaPost(body);
            }''', {'title': title, 'png': PNG})
            assert result['post']['media_url'].startswith('/static/uploads/')
        page.reload(wait_until='domcontentloaded')
        expect(page.locator('#gallery-masonry img')).to_have_count(2)
        sources = page.locator('#gallery-masonry img').evaluate_all('(images) => images.map(image => image.src)')
        assert len(set(sources)) == 2 and all(source.startswith(API + '/static/uploads/') for source in sources)
        page.wait_for_function('Array.from(document.querySelectorAll("#gallery-masonry img")).every(image => image.complete && image.naturalWidth === 1)')
        browser.close()
    assert sum(method == 'POST' and status == 201 for _, method, status in observed) == 2
    assert sum(path.startswith('/static/uploads/') and status == 200 for path, _, status in observed) >= 2
    with app.app_context():
        db.session.remove()
        db.engine.dispose()
print('PASS: same-name multipart uploads, unique persisted URLs, real gallery rendering and HTTPS backend media retrieval')
