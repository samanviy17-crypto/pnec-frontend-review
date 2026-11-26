"""Verify mobile Helper Bot settings and speech with local fixtures."""
import argparse

from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url', required=True)
args = parser.parse_args()
base = args.base_url.rstrip('/') + '/'


def route_request(route):
    request = route.request
    if request.url.endswith('/api/gemini') and request.method == 'POST':
        question = request.post_data_json['text']
        reply = {'Hola': 'Hola, Poway.', 'Hello': 'Hello, Poway.'}.get(question, '[]')
        route.fulfill(json={'text': reply}, headers={'Access-Control-Allow-Origin': '*'})
    elif request.url.startswith(base):
        route.continue_()
    else:
        route.abort()


with sync_playwright() as play:
    browser = play.chromium.launch()
    for mode in ('mouse', 'touch', 'keyboard'):
        page = browser.new_page(viewport={'width': 390, 'height': 844},
                                has_touch=mode == 'touch', is_mobile=mode == 'touch',
                                reduced_motion='reduce')
        page.route('**/*', route_request)
        page.add_init_script("""window.spoken = [];
          window.SpeechSynthesisUtterance = class { constructor(text) { this.text = text; } };
          Object.defineProperty(window, 'speechSynthesis', {value: {
            getVoices: () => window.englishOnly ? [{lang:'en-US'}]
              : [{lang:'en-US'}, {lang:'es-MX'}, {lang:'es_US'}],
            cancel() {},
            speak(reply) { spoken.push([reply.text, reply.lang, reply.voice.lang]); }
          }});""")
        page.goto(base)

        def activate(locator, key='Enter'):
            if mode == 'touch':
                locator.tap()
            elif mode == 'mouse':
                locator.click()
            else:
                locator.press(key)

        settings = page.locator('#pnec-bot-settings')
        close = page.locator('#pnec-bot-settings-close')
        language = page.locator('#pnec-bot-pref-lang')
        voice = page.locator('#pnec-bot-pref-voice')
        composer = page.locator('#pnec-bot-input')
        send = page.locator('#pnec-bot-send')

        def change_language(value):
            activate(settings)
            expect(close).to_be_focused()
            language.select_option(value)
            expect(page.locator('html')).to_have_attribute('lang', f'{value}-US')

        def close_settings():
            activate(close)
            expect(settings).to_be_focused()
            expect(close).to_be_hidden()

        def submit(question):
            composer.fill(question)
            activate(send)

        activate(page.locator('#pnec-bot-fab'))
        change_language('es')
        activate(voice, 'Space')
        expect(voice).to_be_checked()
        close_settings()
        submit('Hola')
        page.wait_for_function("spoken.length === 1")
        spanish_reply = ['Hola, Poway.', 'es-US', 'es_US']
        assert page.evaluate('spoken[0]') == spanish_reply

        change_language('en')
        close_settings()
        submit('Hello')
        page.wait_for_function("spoken.length === 2")
        assert page.evaluate('spoken[1]') == ['Hello, Poway.', 'en-US', 'en-US']

        replay = page.locator('[data-msg-action=speak]').first
        if mode == 'touch':
            expect(page.locator('.pnec-bot-msg-actions').first).to_have_css('opacity', '1')
        activate(replay)
        assert page.evaluate('spoken.slice(2)') == [spanish_reply]

        page.evaluate('window.englishOnly = true')
        change_language('es')
        close_settings()
        submit('Hola')
        expect(page.get_by_text('No se encontró una voz compatible', exact=False).first).to_be_visible()
        assert page.evaluate('spoken.length') == 3

        if mode == 'keyboard':
            activate(settings)
            page.keyboard.press('Escape')
            expect(settings).to_be_focused()
            expect(close).to_be_hidden()

        page.close()
        print(f'PASS 390px {mode}: settings, English and Spanish replies, replay, and missing voice')
    browser.close()
