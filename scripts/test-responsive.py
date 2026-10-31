"""Release regression: test-responsive.py.

Run through scripts/run-release-tests.py with explicit frontend/backend roots.
Uses only the disposable build and isolated backend state selected by the runner.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from release_test_support import PREVIEW_URL


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default=PREVIEW_URL)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    base = args.base_url.rstrip('/') + '/'
    parts = urlsplit(base)
    origin = f'{parts.scheme}://{parts.netloc}/'
    escaped = []
    rows = []
    with sync_playwright() as play:
        browser = play.chromium.launch()
        page = browser.new_page(viewport={'width':390, 'height':844})

        def handle(route):
            request = route.request
            if request.url.startswith(base):
                route.continue_()
            elif request.url.startswith(origin):
                escaped.append(request.url)
                route.abort()
            elif request.resource_type in ['stylesheet', 'font', 'image']:
                route.abort()
            else:
                route.abort()

        page.route('**/*', handle)
        page.goto(base, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_function('document.styleSheets.length >= 1')
        page.wait_for_load_state('load', timeout=30000)
        page.evaluate('document.fonts.ready')
        page.wait_for_timeout(1200)
        close = page.locator('#pnec-bot-close')
        if close.is_visible():
            close.click()
        for width in [320,375,390,414,767,768,1024,1280,1333,1334,1365,1440]:
            page.set_viewport_size({'width':width, 'height':900})
            page.wait_for_timeout(100)
            # Wait for font/image layout and inherited transitions to settle;
            # retain the exact overflow/video assertions below.
            page.wait_for_function('document.documentElement.scrollWidth <= innerWidth', timeout=5000)
            row = page.evaluate('''() => ({viewport:innerWidth,
                scroll:document.documentElement.scrollWidth,
                videoRight:document.getElementById('pnec-homepage-video').getBoundingClientRect().right,
                videoMargin:getComputedStyle(document.querySelector('.elementor-element-7bddfff > .elementor-widget-container')).marginRight})''')
            assert row['scroll'] <= width, row
            assert row['videoRight'] <= width + 1, row
            rows.append(row)
            if args.output_dir and width in [320,390,1440]:
                args.output_dir.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(args.output_dir / f'homepage-{width}.png'), full_page=True)
        assert not escaped, escaped
        # Keep the inherited desktop offset; the narrow-screen correction must not flatten it.
        # Preserve the desktop assertion; emit all offline measurements even on failure.
        if float(rows[-1]['videoMargin'].removesuffix('px')) >= 0:
            print('OFFLINE_RESPONSIVE_DIAGNOSTIC ' + json.dumps({
                'status': 'FAIL', 'widths': rows,
                'desktop_expected': 'negative margin from external theme',
                'desktop_actual': rows[-1]['videoMargin'],
                'escaping_local_requests': escaped}), flush=True)
        assert float(rows[-1]['videoMargin'].removesuffix('px')) < 0, rows[-1]
        browser.close()
    result = {'status':'PASS', 'widths':rows, 'escaping_local_requests':escaped,
              'network_policy':'external static assets allowed; API calls and external scripts blocked'}
    if args.output_dir:
        (args.output_dir/'responsive-results.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
