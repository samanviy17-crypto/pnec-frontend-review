"""Verify PNEC source/output ownership against the explicit disposable release build."""
import json
from pathlib import Path
import re
from release_test_support import FRONTEND_ROOT, SITE_ROOT

manifest = json.loads((FRONTEND_ROOT / 'scripts/pnec-scss-manifest.json').read_text())
for row in manifest['standalone']:
    assert not (FRONTEND_ROOT / row['old']).exists(), row['old']
    assert (FRONTEND_ROOT / row['entry']).read_text().startswith('---\n---\n'), row['entry']
    assert (FRONTEND_ROOT / row['partial']).is_file(), row['partial']
    assert (SITE_ROOT / row['old']).is_file(), row['old']
for row in manifest['static_html']:
    assert (FRONTEND_ROOT / row['entry']).is_file(), row['entry']
    assert (FRONTEND_ROOT / row['partial']).is_file(), row['partial']
    assert (SITE_ROOT / row['url']).is_file(), row['url']
for source in (FRONTEND_ROOT / '_sass/beasts').rglob('*'):
    if source.suffix not in ('.scss', '.sass'):
        continue
    for name in re.findall(r"@import\s+[\"'](beasts/[^\"';]+)[\"']", source.read_text()):
        target = FRONTEND_ROOT / '_sass' / name
        assert any(target.with_name('_' + target.name).with_suffix(ext).is_file()
                   for ext in ('.scss', '.sass')), name
# Verify the wider set of migrated PNEC pages, beyond the functional suite's routes.
for source in (FRONTEND_ROOT / 'pages').glob('*.html'):
    for name in re.findall(r"(?:href|src)=[\"']([^\"']+\.css)[\"']", source.read_text()):
        if name.startswith('../assets/css/beasts/'):
            assert (SITE_ROOT / 'pages' / name).resolve().is_file(), (source.name, name)
print('PASS: PNEC standalone/static SCSS outputs, partial dependencies and migrated static CSS links')
