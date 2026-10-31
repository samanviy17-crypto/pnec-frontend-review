"""Require explicit release roots; never infer a sibling/original repository."""
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit
from urllib.request import urlopen


def required_path(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f'{name} must explicitly identify the release test input.')
    return Path(value).resolve(strict=True)


FRONTEND_ROOT = required_path('PNEC_FRONTEND_ROOT')
BACKEND_ROOT = required_path('PNEC_BACKEND_ROOT')
SITE_ROOT = required_path('PNEC_SITE_ROOT')
PREVIEW_URL = os.environ.get('PNEC_PREVIEW_URL', '').rstrip('/')
assert FRONTEND_ROOT == Path(__file__).resolve().parents[1], 'Wrong frontend source'
assert (BACKEND_ROOT / 'app/routes/preparedness.py').is_file(), 'Missing release API'
assert SITE_ROOT != FRONTEND_ROOT / '_site', 'Use a disposable build artifact'
assert urlsplit(PREVIEW_URL).hostname == '127.0.0.1', 'Use an isolated local preview'
with urlopen(PREVIEW_URL + '/_release_build.json', timeout=10) as response:
    provenance = json.load(response)
assert provenance['frontend_root'] == str(FRONTEND_ROOT), 'Wrong preview artifact'
assert provenance['backend_root'] == str(BACKEND_ROOT), 'Wrong backend selection'

# All integration scripts import this before importing any backend module.
sys.path.insert(0, str(BACKEND_ROOT))
import requests


def no_external_provider(*args, **kwargs):
    raise requests.ConnectionError('External providers disabled in release verification')


# Browser interception alone cannot block server-side weather/news/AI calls.
requests.sessions.Session.request = no_external_provider
import app
assert Path(app.__file__).resolve() == BACKEND_ROOT / 'app/__init__.py', 'Wrong Flask source'
print(f'Release inputs: frontend={FRONTEND_ROOT}; backend={BACKEND_ROOT}; site={SITE_ROOT}', flush=True)
