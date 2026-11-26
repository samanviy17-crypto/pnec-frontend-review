"""Verify Helper Bot settings layouts and mobile speech with local fixtures."""
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


def verify_settings_layout(browser, width, mode):
    mobile = mode == 'mobile'
    single_pane = mode in ('compact', 'mobile')
    page = browser.new_page(viewport={'width': width, 'height': 640},
                            has_touch=mobile, is_mobile=mobile, reduced_motion='reduce')
    page.route('**/*', route_request)
    page.goto(base)
    page.locator('#pnec-bot-fab').click()
    if mode == 'expanded':
        page.locator('#pnec-bot-expand').click()
    elif mode == 'maximized':
        page.locator('#pnec-bot-modal').click()

    panel = page.locator('#pnec-bot-panel')
    settings = page.locator('#pnec-bot-settings')
    close = page.locator('#pnec-bot-settings-close')
    drawer = page.locator('#pnec-bot-settings-drawer')
    body = drawer.locator('.pnec-bot-settings-body')
    conversation = page.locator('.pnec-bot-main')
    rail = page.locator('.pnec-bot-rail')
    settings.click()
    expect(close).to_be_focused()

    panel_box = panel.bounding_box()
    drawer_box = drawer.bounding_box()
    inner_width = panel.evaluate('panel => panel.clientWidth')
    fixed_widths = {'compact': 380, 'expanded': 720}
    if mode in fixed_widths:
        assert abs(panel_box['width'] - fixed_widths[mode]) <= 1, (mode, width, panel_box)
    else:
        # A fixed reference box uses the same containing block as the panel.
        # A stable scrollbar gutter can reduce it without changing viewport metrics.
        inset = '8px' if mobile else '4vw'
        bounds = panel.evaluate("""(panel, inset) => {
            const probe = document.createElement('div');
            Object.assign(probe.style, {
                position: 'fixed', top: '0', left: inset, right: inset,
                height: '0', visibility: 'hidden',
            });
            panel.after(probe);
            const {left, right} = probe.getBoundingClientRect();
            probe.remove();
            return {left, right};
        }""", inset)
        assert abs(panel_box['x'] - bounds['left']) <= 1, (mode, width, panel_box, bounds)
        assert abs(panel_box['x'] + panel_box['width'] - bounds['right']) <= 1, (mode, width, panel_box, bounds)
    if single_pane:
        expect(conversation).to_be_hidden()
        expect(rail).to_be_hidden()
        assert abs(drawer_box['width'] - inner_width) <= 1, (mode, width, drawer_box, inner_width)
    else:
        expect(conversation).to_be_visible()
        expect(rail).to_be_visible()
        rail_box = rail.bounding_box()
        chat_box = conversation.bounding_box()
        assert rail_box['x'] + rail_box['width'] <= chat_box['x'] + 1
        assert chat_box['x'] + chat_box['width'] <= drawer_box['x'] + 1
        assert abs(drawer_box['width'] - (280 if mode == 'expanded' else 320)) <= 1
    assert abs(drawer_box['x'] + drawer_box['width'] - (panel_box['x'] + panel_box['width'])) <= 1

    page.locator('#pnec-bot-pref-lang').select_option('es')
    expect(page.locator('html')).to_have_attribute('lang', 'es-US')
    voice = page.locator('#pnec-bot-pref-voice')
    voice.tap() if mobile else voice.click()
    expect(voice).to_be_checked()
    assert body.evaluate('body => body.scrollHeight > body.clientHeight')
    assert body.evaluate('body => body.scrollWidth <= body.clientWidth + 1'), (mode, width)
    drawer.get_by_role('link').last.focus()
    expect(drawer.get_by_role('link').last).to_be_in_viewport()
    expect(close).to_be_in_viewport()
    close.tap() if mobile else close.click()
    expect(drawer).to_be_hidden()
    expect(settings).to_be_focused()
    expect(conversation).to_be_visible()
    settings.press('Enter')
    expect(close).to_be_focused()
    page.keyboard.press('Escape')
    expect(settings).to_be_focused()
    expect(drawer).to_be_hidden()
    page.close()
    print(f'PASS {mode}: {width}px viewport, {panel_box["width"]:.0f}px chatbot, '
          f'{drawer_box["width"]:.0f}px settings drawer')


with sync_playwright() as play:
    browser = play.chromium.launch()
    for width in (768, 1024, 1440):
        for mode in ('compact', 'expanded', 'maximized'):
            verify_settings_layout(browser, width, mode)
    for width in (320, 390, 720):
        verify_settings_layout(browser, width, 'mobile')

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
