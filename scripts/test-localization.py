"""Audit both locales in the built artifact, then exercise real UI language switching and speech."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url', required=True)
parser.add_argument('--site', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
base = args.base_url.rstrip('/') + '/'
paths = [path.relative_to(args.site).as_posix() for path in args.site.rglob('*.html')
         if path.relative_to(args.site).parts[0] not in {'docs', 'assets', 'images'}]
report = {}
with sync_playwright() as play:
    browser = play.chromium.launch()
    for language in ('en', 'es'):
        context = browser.new_context(reduced_motion='reduce')
        context.route('**/*', lambda route: route.continue_() if route.request.url.startswith(base) else route.abort())
        context.add_init_script(f'localStorage.setItem("pnec_appearance_v1", JSON.stringify({{language:"{language}"}}));')
        page = context.new_page()
        for path in sorted(paths):
            response = page.goto(base + path, wait_until='domcontentloaded')
            assert response.status == 200, (path, response.status)
            expect(page.locator('html')).to_have_attribute('lang', f'{language}-US')
            if language == 'es':
                original = page.locator('[data-source-language="en"]:visible').evaluate_all('''nodes => [...new Set(
                  nodes.map(node => node.textContent.trim()).filter(Boolean))]''')
                report[path] = original
        context.unroute_all(behavior='wait')
        context.close()

    for width in (390, 1280):
        context = browser.new_context(viewport={'width': width, 'height': 900}, reduced_motion='reduce')
        context.route('**/*', lambda route: route.continue_() if route.request.url.startswith(base) else route.abort())
        context.add_init_script('''window.spoken = [];
          window.voices = [{lang:"en-US",voiceURI:"en",name:"English"}, {lang:"es-ES",voiceURI:"es-ES",name:"Spanish (Spain)"}];
          window.SpeechSynthesisUtterance = class { constructor(text) { this.text = text; } };
          const speech = Object.assign(new EventTarget(), {
            getVoices: () => window.voices, cancel() {}, pause() {this.paused=true;}, resume() {this.paused=false;},
            speak(u) { window.spoken.push({text:u.text,lang:u.lang}); setTimeout(() => u.onend?.(), 0); }
          });
          Object.defineProperty(window,'speechSynthesis',{value:speech});''')
        page = context.new_page()
        page.goto(base + 'pages/settings.html')
        page.locator('#pnec-audio-form [name=enabled]').check()
        assert page.evaluate('spoken.length') == 0
        page.locator('#site-language').select_option('es')
        page.locator('#pnec-language-form button[type=submit]').click()
        expect(page.locator('h1')).to_have_text('Preferencias')
        page.evaluate('voices.unshift({lang:"es-MX",voiceURI:"es-MX",name:"Spanish (Mexico)"}); speechSynthesis.dispatchEvent(new Event("voiceschanged"))')
        page.locator('[data-speech=test]').click()
        assert page.evaluate('spoken.at(-1).lang') == 'es-MX'
        page.evaluate('voices = voices.filter(voice => voice.lang === "en-US"); speechSynthesis.dispatchEvent(new Event("voiceschanged"))')
        count = page.evaluate('spoken.length')
        page.locator('[data-speech=test]').click()
        expect(page.locator('#pnec-audio-form .pnec-speech-status')).to_contain_text('No se encontró una voz compatible')
        assert page.evaluate('spoken.length') == count
        page.goto(base + 'pages/preparedness-resources.html#preparedness-journey')
        expect(page.locator('#preparedness-journey')).to_have_text('Ruta de preparación')
        expect(page.locator('.ocs__nav-card-title').first).to_have_text('Evalúe su preparación')
        page.evaluate('''() => {
          const range = document.createRange();
          range.selectNodeContents(document.querySelector('#preparedness-journey'));
          const selection = getSelection();
          selection.removeAllRanges();
          selection.addRange(range);
        }''')
        page.wait_for_function('getSelection().toString() === "Ruta de preparación"')
        page.wait_for_timeout(70)
        page.locator('[data-speech=read]').first.evaluate('button => button.click()')
        page.wait_for_function('spoken.some(entry => entry.text === "Ruta de preparación" && entry.lang === "es-ES")')
        page.locator('[data-speech=page]').first.evaluate('button => button.click()')
        page.wait_for_function('spoken.some(entry => entry.lang.startsWith("es") && entry.text.includes("Evalúe su preparación"))')
        page.goto(base + 'role-quiz/')
        page.locator('#intro-screen .start-btn').click()
        expect(page.locator('#progress-text')).to_have_text('Pregunta 1 de 5')
        expect(page.locator('#choices-grid .choice-text').first).to_contain_text('Llamar a los vecinos')
        page.goto(base + 'pages/settings.html')
        page.locator('#pnec-language-form button[type=reset]').click()
        expect(page.locator('h1')).to_have_text('Preferences')
        page.locator('#speech-test-text').fill('This is a long English speech sample. ' * 20)
        page.locator('[data-speech=test]').click()
        page.wait_for_function('spoken.length > 2')
        assert page.evaluate('spoken.every(entry => entry.lang === "en-US" && entry.text.length <= 201)')
        page.reload()
        expect(page.locator('html')).to_have_attribute('lang', 'en-US')
        assert page.evaluate('spoken.length') == 0
        context.unroute_all(behavior='wait')
        context.close()
    browser.close()
args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(f'PASS {len(paths)} routes in both languages, 2 widths for locale switching and speech; coverage gaps recorded in {args.output}')
