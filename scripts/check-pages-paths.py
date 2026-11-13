"""Validate generated local links/assets remain inside the GitHub project path."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import posixpath
from urllib.parse import unquote, urlsplit

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--site', type=Path, required=True)
args = parser.parse_args()
root = args.site.resolve(strict=True)
base = '/pnec-frontend-review'
errors = set()


class Links(HTMLParser):
    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        urls = [attributes.get(key, '') for key in ('href', 'src', 'poster')]
        if attributes.get('srcset') and not attributes['srcset'].startswith('data:'):
            urls += [part.strip().split()[0] for part in attributes['srcset'].split(',') if part.strip()]
        for url in urls:
            parts = urlsplit(url)
            if not url or url.startswith('#') or parts.scheme or parts.netloc or '${' in url:
                continue
            path = unquote(parts.path)
            resolved = posixpath.normpath(path if path.startswith('/') else
                                         posixpath.join(posixpath.dirname(self.url), path))
            if resolved != base and not resolved.startswith(base + '/'):
                errors.add((self.file, url, 'escapes project baseurl'))
                continue
            target = root / resolved[len(base):].lstrip('/')
            if not target.is_file() and not (target / 'index.html').is_file():
                errors.add((self.file, url, 'missing local target'))


pages = list(root.rglob('*.html'))
assert pages and (root / 'index.html').is_file() and (root / '404.html').is_file()
for file in pages:
    links = Links()
    links.file = file.relative_to(root).as_posix()
    links.url = base + '/' + links.file
    links.feed(file.read_text())
if errors:
    for error in sorted(errors):
        print(' | '.join(error))
    raise SystemExit('Project-site path checks failed.')
print(f'PASS: local links, images, srcsets and scripts across {len(pages)} HTML files')
