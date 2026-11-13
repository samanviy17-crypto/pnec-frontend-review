"""Build the GitHub project site; use an API only after public review checks pass."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--destination', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
destination = args.destination.resolve()
if destination == root or root in destination.parents:
    raise SystemExit('Build outside source.')
api = os.environ.get('PNEC_REVIEW_API_URL', '').rstrip('/')
if api:
    parts = urlsplit(api)
    if (parts.scheme != 'https' or not re.fullmatch(r'pnec-backend-review(?:-[a-z0-9]+)?\.onrender\.com', parts.netloc)
            or parts.path or parts.query or parts.fragment):
        raise SystemExit('Use only the approved separate Render review API root URL.')
    with urlopen(Request(api + '/api/health', headers={'Origin': 'https://samanviy17-crypto.github.io'}), timeout=90) as response:
        health = json.load(response)
        if (health.get('status') != 'ok' or health.get('review') is not True
                or response.headers.get('Access-Control-Allow-Origin') != 'https://samanviy17-crypto.github.io'):
            raise SystemExit('Review API health/CORS validation failed.')
    with urlopen(api + '/api/ready', timeout=30) as response:
        if json.load(response).get('status') != 'ready':
            raise SystemExit('Review API schema is not ready.')
with tempfile.TemporaryDirectory(prefix='pnec-pages-') as temporary:
    # Jekyll 3 selects its config parser by extension and ignores .json files.
    # JSON content is valid YAML, so use a supported extension for this override.
    override = Path(temporary) / 'api.yml'
    override.write_text(json.dumps({'api_base_url': api or 'https://api.pnec-review.invalid'}))
    config = ','.join(str(p) for p in (root / '_config.yml', root / '_config.pages.yml', override))
    subprocess.run(['bundle', 'exec', 'jekyll', 'build', '--source', str(root),
                    '--destination', str(destination), '--config', config], cwd=temporary,
                   env={**os.environ, 'BUNDLE_GEMFILE': str(root / 'Gemfile')}, check=True)
expected_api = api or 'https://api.pnec-review.invalid'
runtime_pattern = r'window\.PNEC_API_BASE\s*=\s*("(?:[^"\\]|\\.)*")\s*;'
checked = 0
for page in destination.rglob('*.html'):
    for value in re.findall(runtime_pattern, page.read_text(encoding='utf-8')):
        if json.loads(value) != expected_api:
            raise SystemExit(f'Incorrect API URL embedded in {page.relative_to(destination)}.')
        checked += 1
if not checked or not re.search(runtime_pattern, (destination / 'index.html').read_text(encoding='utf-8')):
    raise SystemExit('Missing frontend runtime API configuration.')
print(f'PASS: expected API URL embedded in {checked} rendered pages')
print('PASS: GitHub Pages project-site build')
