"""Build and test explicit release sources using disposable artifacts and state.

No dependency installation, original preview access, production writes or backend
source edits. Logs and build output remain in the printed temporary directory.
"""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frontend-root', type=Path, required=True)
    parser.add_argument('--backend-root', type=Path, required=True)
    args = parser.parse_args()
    frontend = args.frontend_root.resolve(strict=True)
    backend = args.backend_root.resolve(strict=True)
    assert frontend == Path(__file__).resolve().parents[1]
    assert (backend / 'app/routes/preparedness.py').is_file()
    assert not (frontend / '.env').exists(), 'Credentials must not be materialized'
    artifacts = Path(tempfile.mkdtemp(prefix='pnec-frontend-release-'))
    site = artifacts / 'site'
    print('Disposable artifacts:', artifacts, flush=True)
    environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
                   'JEKYLL_NO_BUNDLER_REQUIRE': 'true', 'EVENT_STORAGE_TIMEZONE': 'UTC',
                   'PNEC_FRONTEND_ROOT': str(frontend), 'PNEC_BACKEND_ROOT': str(backend),
                   'PNEC_SITE_ROOT': str(site), 'PNEC_TEST_BACKEND_PORT': '0'}
    # Build from a temporary working directory so inherited Sass cache defaults
    # cannot write into either release source, even if an option is ignored.
    ruby = '''gem "jekyll", ">= 3.9", "< 4"; require "jekyll";
Jekyll::Commands::Build.process({
  "source"=>ENV.fetch("PNEC_FRONTEND_ROOT"),
  "destination"=>ENV.fetch("PNEC_SITE_ROOT"),
  "config"=>File.join(ENV.fetch("PNEC_FRONTEND_ROOT"), "_config.yml"),
  "url"=>"https://pnec-review.invalid", "baseurl"=>"",
  "sass"=>{"cache"=>false, "cache_location"=>File.join(Dir.pwd,"sass-cache")}
})'''
    with (artifacts / 'build.log').open('w') as log:
        build = subprocess.run(['ruby', '-e', ruby], env=environment, cwd=artifacts,
                               stdout=log, stderr=subprocess.STDOUT, timeout=300)
    if build.returncode:
        print((artifacts / 'build.log').read_text()[-6000:])
        return build.returncode
    assert (site / 'index.html').is_file()
    (site / '_release_build.json').write_text(json.dumps({
        'frontend_root': str(frontend), 'backend_root': str(backend)}))
    print('PASS: isolated Jekyll build', flush=True)
    server = None
    for port in [4000, 8080]:
        try:
            server = ThreadingHTTPServer(('127.0.0.1', port),
                partial(QuietHandler, directory=str(site)))
            break
        except OSError:
            continue
    if server is None:
        raise RuntimeError('No unused preview port allowed by the unchanged backend CORS policy')
    environment['PNEC_PREVIEW_URL'] = f'http://127.0.0.1:{server.server_port}'
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    scripts = ['test-pnec-scss.py', 'test-request-worker.py', 'test-quiz.py', 'test-account-regression.py',
               'test-profile.py', 'test-community-tools.py', 'test-responsive.py',
               'test-production-contract.py', 'test-admin-security.py', 'test-media-release.py', 'audit-site.py']
    results = []
    try:
        for script in scripts:
            if not (frontend / 'scripts' / script).exists():
                continue
            with (artifacts / (script + '.log')).open('w') as log:
                run = subprocess.run([sys.executable, '-B', str(frontend / 'scripts' / script)],
                    cwd=artifacts, env=environment, stdout=log, stderr=subprocess.STDOUT,
                    timeout=420 if script == 'audit-site.py' else 180)
            results.append({'script': script, 'exit_code': run.returncode})
            print(('PASS' if run.returncode == 0 else 'FAIL') + ': ' + script, flush=True)
            if run.returncode:
                print((artifacts / (script + '.log')).read_text()[-6000:], flush=True)
        (artifacts / 'results.json').write_text(json.dumps(results, indent=2))
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
    print('Results:', json.dumps(results), flush=True)
    return int(any(result['exit_code'] for result in results))


if __name__ == '__main__':
    raise SystemExit(main())
