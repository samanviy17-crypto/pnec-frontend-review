"""Verify the shared palette, theme choices and resident surfaces in Chromium."""
import argparse
from pathlib import Path
from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url', required=True)
parser.add_argument('--output-dir', type=Path, required=True)
args = parser.parse_args()
base = args.base_url.rstrip('/') + '/'
args.output_dir.mkdir(parents=True, exist_ok=True)
presets = ('site-default', 'midnight', 'light', 'green', 'sepia', 'cyberpunk', 'ocean', 'sunset')
white, pale, blue, green, ink = ('rgb(255, 255, 255)', 'rgb(244, 250, 246)', 'rgb(221, 242, 250)',
                                'rgb(97, 207, 112)', 'rgb(23, 62, 42)')
routes = {
    'pages/checklist.html': [('.checklist-hero', blue), ('.checklist-category', white)],
    'pages/preparedness-resources.html': [('.pnec-task-panel', blue), ('.pnec-preparedness .ocs-card', white)],
    'pages/community-events-and-activities.html': [],
    'pages/profile.html': [],
    'pages/settings.html': [('.pnec-preference-card', white), ('#preview-button', green)],
    'pages/register.html': [('.auth-form-stack', white), ('#login-submit-btn', green)],
    'pages/volunteer.html': [('#vol-submit-btn', green)],
    'role-quiz/': [('#quiz-shell', pale), ('.start-btn', green)],
}

with sync_playwright() as play:
    browser = play.chromium.launch()
    for width in (390, 820, 1440):
        context = browser.new_context(viewport={'width': width, 'height': 900}, color_scheme='dark', reduced_motion='reduce')
        context.route('**/*', lambda route: route.continue_() if route.request.url.startswith(base) else route.abort())
        page = context.new_page()
        page.goto(base, wait_until='networkidle')
        expect(page.locator('html')).to_have_attribute('data-appearance-resolved', 'light')
        expect(page.locator('html')).to_have_css('color-scheme', 'light')
        expect(page.locator('#pnec-site-header')).to_have_css('background-color', 'rgb(255, 255, 255)')
        expect(page.locator('.pnec-hero')).to_have_css('background-color', pale)
        expect(page.locator('.pnec-about-preview')).to_have_css('background-color', blue)
        expect(page.locator('.pnec-action').first).to_have_css('background-color', 'rgb(255, 255, 255)')
        expect(page.locator('.pnec-hero-copy h1')).to_have_css('color', 'rgb(23, 62, 42)')
        expect(page.locator('.pnec-hero-actions .primary')).to_have_css('background-color', 'rgb(97, 207, 112)')
        assert page.locator('.pnec-hero-backgrounds img').evaluate_all('(images) => images.every(image => image.naturalWidth > 0)')
        assert page.locator('.pnec-hero-pause').is_hidden()
        assert page.locator('.pnec-photo-credit summary').is_visible()
        if width >= 1000:
            assert page.locator('.pnec-actions').bounding_box()['y'] + page.locator('.pnec-actions').bounding_box()['height'] < 768
        close = page.locator('#pnec-bot-close')
        if close.is_visible():
            close.click()
        page.locator('#pnec-bot-fab').click()
        expect(page.locator('#pnec-bot-panel')).to_have_css('background-color', 'rgb(255, 255, 255)')
        close.click()
        page.screenshot(path=str(args.output_dir / f'light-home-{width}.png'))
        for route, surfaces in routes.items():
            assert page.goto(base + route, wait_until='domcontentloaded').status == 200
            expect(page.locator('#pnec-site-header')).to_have_css('background-color', 'rgb(255, 255, 255)')
            expect(page.locator('body')).to_have_css('background-color', pale)
            expect(page.locator('body')).to_have_css('color', ink)
            for selector, color in surfaces:
                expect(page.locator(selector).first).to_have_css('background-color', color)
            if route == 'pages/preparedness-resources.html':
                page.screenshot(path=str(args.output_dir / f'light-resources-{width}.png'))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, route)
        page.goto(base + 'pages/settings.html')
        for preset in presets:
            page.locator(f'[data-theme="{preset}"]').click()
            expect(page.locator('#appearance-contrast')).to_contain_text('Good contrast.')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, preset)
            sample = page.locator(f'[data-theme="{preset}"] .ocs__prefs-swatch-sample')
            surface, text = sample.evaluate("""element => {
                const style = getComputedStyle(element);
                return [style.backgroundColor, style.color];
            }""")
            page.goto(base, wait_until='domcontentloaded')
            expect(page.locator('.pnec-hero-copy h1')).to_have_css('color', text)
            # Cards and navigation share the configured surface, while the hero uses the swatch canvas.
            expect(page.locator('.pnec-hero')).to_have_css('background-color', surface)
            header_surface = page.locator('#pnec-site-header').evaluate('element => getComputedStyle(element).backgroundColor')
            expect(page.locator('.pnec-action').first).to_have_css('background-color', header_surface)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, preset, 'home')
            page.goto(base + 'pages/preparedness-resources.html', wait_until='domcontentloaded')
            expect(page.locator('.pnec-preparedness .ocs-card').first).to_have_css('background-color', header_surface)
            expect(page.locator('#preparedness-journey')).to_have_css('color', text)
            page.goto(base + 'pages/settings.html', wait_until='domcontentloaded')
        page.locator('#appearance-theme').select_option('dark')
        page.goto(base, wait_until='networkidle')
        expect(page.locator('html')).to_have_attribute('data-appearance-resolved', 'dark')
        assert page.locator('html').evaluate("element => element.classList.contains('pb-theme-dark')")
        expect(page.locator('#pnec-site-header')).to_have_css('background-color', 'rgb(23, 38, 56)')
        if close.is_visible():
            close.click()
        page.screenshot(path=str(args.output_dir / f'saved-dark-{width}.png'))
        page.goto(base + 'pages/settings.html')
        page.locator('[data-theme="site-default"]').click()
        expect(page.locator('html')).to_have_attribute('data-appearance-resolved', 'light')
        page.locator('#appearance-theme').select_option('system')
        expect(page.locator('[data-theme="site-default"]')).to_have_attribute('aria-pressed', 'false')
        page.goto(base, wait_until='networkidle')
        assert page.evaluate("JSON.parse(localStorage.getItem('pnec_appearance_v1')).theme") == 'system'
        expect(page.locator('html')).to_have_attribute('data-appearance-resolved', 'dark')
        expect(page.locator('.pnec-hero')).to_have_css('background-color', 'rgb(13, 25, 40)')
        expect(page.locator('.pnec-action').first).to_have_css('background-color', 'rgb(23, 38, 56)')
        page.goto(base + 'pages/settings.html')
        page.locator('[data-theme="site-default"]').click()
        expect(page.locator('[data-theme="site-default"]')).to_have_attribute('aria-pressed', 'true')
        page.goto(base, wait_until='networkidle')
        expect(page.locator('.pnec-hero')).to_have_css('background-color', pale)
        expect(page.locator('.pnec-action').first).to_have_css('background-color', white)
        page.goto(base + 'pages/settings.html')
        page.locator('#pnec-appearance-form button[type="reset"]').click()
        expect(page.locator('html')).to_have_attribute('data-appearance-resolved', 'light')
        context.unroute_all(behavior='wait')
        context.close()
        print(f'PASS at {width}px', flush=True)
