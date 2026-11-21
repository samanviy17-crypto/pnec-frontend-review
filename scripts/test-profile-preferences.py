"""Offline navigation/personalization acceptance. All account data and voices are fixtures."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url',required=True)
parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args();base=args.base_url.rstrip('/')+'/'
args.output_dir.mkdir(parents=True,exist_ok=True)
report=[]

def offline(route):
    if route.request.url.startswith(base):route.continue_();return
    path=urlsplit(route.request.url).path
    if path.endswith('/theme.css'):route.fulfill(status=200,content_type='text/css',body='');return
    if path.endswith('/auth/me'):route.fulfill(status=401,content_type='application/json',body='{"error":"Sign in required"}');return
    route.fulfill(status=200,content_type='application/json',body='{}')

def open_page(page,path='pages/settings.html'):
    assert page.goto(base+path,wait_until='networkidle').status==200
    if page.locator('#pnec-bot-close').is_visible():page.locator('#pnec-bot-close').click()

def set_color(page,name,value):
    page.locator(f'[name="{name}"]').evaluate('(el,value)=>{el.value=value;el.dispatchEvent(new Event("input",{bubbles:true}));el.dispatchEvent(new Event("change",{bubbles:true}));}',value)

speech_fixture="""
window.__speech={calls:[],canceled:0,paused:false};
window.SpeechSynthesisUtterance=class {constructor(text){this.text=text}};
Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{
 getVoices:()=>[{name:'Synthetic English voice',voiceURI:'fixture-en',lang:'en-US'},{name:'Synthetic Spanish voice',voiceURI:'fixture-es',lang:'es-MX'}],
 addEventListener(){},
 speak(utterance){window.__speech.calls.push({text:utterance.text,rate:utterance.rate,pitch:utterance.pitch,volume:utterance.volume,voice:utterance.voice?.voiceURI,lang:utterance.lang});},
 cancel(){window.__speech.canceled++},
 pause(){window.__speech.paused=true},resume(){window.__speech.paused=false},
 get paused(){return window.__speech.paused}
}});
"""
with sync_playwright() as play:
    browser=play.chromium.launch()
    for width in (320,390,768,1280):
        print('Checking themes, language and speech at',width,flush=True)
        context=browser.new_context(viewport={'width':width,'height':1000},reduced_motion='reduce')
        context.route('**/*',offline);context.add_init_script(speech_fixture)
        page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        open_page(page)
        assert page.locator('[data-theme]').count()==8
        names=page.locator('.ocs__prefs-swatch-name').all_text_contents()
        assert names==['Site Default','Midnight','Light','Green','Sepia','Cyberpunk','Ocean','Sunset']
        for name in ['site-default','midnight','light','green','sepia','cyberpunk','ocean','sunset']:
            card=page.locator(f'[data-theme="{name}"]');card.focus();card.press('Enter')
            assert card.get_attribute('aria-pressed')=='true'
            assert page.locator('[data-theme][aria-pressed="true"]').count()==1
            assert 'Good contrast' in page.locator('#appearance-contrast').inner_text()
            assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),(width,name)
            page.reload(wait_until='networkidle');assert page.locator(f'[data-theme="{name}"]').get_attribute('aria-pressed')=='true'
            assert page.locator('html').get_attribute('data-appearance-preset')==name
        # Cross-page preset and font/button/readability persistence.
        page.locator('[data-theme="ocean"]').click()
        page.select_option('[name="font"]','serif');page.select_option('[name="size"]','extra')
        page.select_option('[name="button"]','pill');page.check('[name="spacing"]');page.check('[name="motion"]')
        for font in ['sans','serif','mono']:
            page.select_option('[name="font"]',font)
            assert page.locator('.ocs__prefs-swatch-name').evaluate_all('(els)=>els.every(e=>e.scrollWidth<=e.clientWidth)'),(width,font,'large theme label overflow')
        page.select_option('[name="font"]','serif')
        open_page(page,'pages/kit.html')
        assert page.locator('html').get_attribute('data-appearance-preset')=='ocean'
        assert page.locator('html').get_attribute('data-appearance-font')=='serif'
        open_page(page)
        assert page.locator('[name="button"]').input_value()=='pill'
        assert page.locator('[name="size"]').input_value()=='extra'
        # Custom colors preview independently, then save when readable.
        page.locator('[data-theme="light"]').click()
        before=page.locator('body').evaluate('(e)=>getComputedStyle(e).backgroundColor')
        set_color(page,'bgColor','#f4ecd8');set_color(page,'textColor','#212121');set_color(page,'accentColor','#7b1942')
        assert page.locator('.pnec-live-preview').evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(244, 236, 216)'
        assert page.locator('body').evaluate('(e)=>getComputedStyle(e).backgroundColor')==before
        page.locator('#pnec-appearance-form button[type="submit"]').click()
        page.reload(wait_until='networkidle')
        assert page.locator('[name="bgColor"]').input_value()=='#f4ecd8'
        assert page.locator('body').evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(244, 236, 216)'
        set_color(page,'textColor','#f4ecd8');page.locator('#pnec-appearance-form button[type="submit"]').click()
        assert 'at least 4.5:1' in page.locator('#appearance-status').inner_text()
        assert page.locator('body').evaluate('(e)=>getComputedStyle(e).color')=='rgb(33, 33, 33)'
        page.reload(wait_until='networkidle');assert page.locator('[name="textColor"]').input_value()=='#212121'
        # Reviewed shell labels translate; main editorial/user content stays original.
        page.select_option('#site-language','es');page.locator('#pnec-language-form button[type="submit"]').click()
        assert page.locator('h1').inner_text()=='Preferencias'
        assert page.locator('html').get_attribute('lang')=='es-US'
        open_page(page,'pages/kit.html')
        assert page.locator('[data-category-link="prepare"]').inner_text()=='Preparación'
        assert page.locator('html').get_attribute('lang')=='es-US'
        open_page(page);assert page.locator('#site-language').input_value()=='es'
        page.locator('#pnec-language-form button[type="reset"]').click()
        assert page.locator('h1').inner_text()=='Preferences'
        # Speech is opt-in and never starts on load. Test only the browser contract.
        assert page.evaluate('__speech.calls.length')==0
        assert page.locator('[data-speech="test"]').is_disabled()
        page.locator('#pnec-audio-form [name="enabled"]').check()
        page.select_option('#speech-voice','fixture-en')
        for name,value in [('rate',1.5),('pitch',1.2),('volume',0.4)]:
            page.locator(f'#speech-{name}').evaluate('(el,v)=>{el.value=v;el.dispatchEvent(new Event("input",{bubbles:true}));el.dispatchEvent(new Event("change",{bubbles:true}));}',value)
        page.locator('[data-speech="test"]').click()
        calls=page.evaluate('__speech.calls');assert len(calls)>0 and calls[0]['rate']==1.5 and calls[0]['pitch']==1.2 and calls[0]['volume']==0.4 and calls[0]['voice']=='fixture-en'
        page.locator('#audio [data-speech="pause"]').click();assert page.evaluate('__speech.paused')
        page.locator('#audio [data-speech="pause"]').click();assert not page.evaluate('__speech.paused')
        page.locator('#audio [data-speech="stop"]').click();assert 'stopped' in page.locator('#audio .pnec-speech-status').inner_text()
        page.select_option('#site-language','es')
        page.locator('#pnec-language-form button[type="submit"]').click()
        page.locator('[data-speech="test"]').click()
        spanish = page.evaluate('__speech.calls.at(-1)')
        assert spanish['text'].startswith('Los vecinos') and spanish['lang']=='es-MX' and spanish['voice']=='fixture-es'
        page.locator('#pnec-language-form button[type="reset"]').click()
        page.reload(wait_until='networkidle');assert page.evaluate('__speech.calls.length')==0
        assert page.locator('#pnec-audio-form [name="enabled"]').is_checked()
        assert page.locator('#speech-rate').input_value()=='1.5'
        # Read explicit selected text, not form inputs or hidden content.
        open_page(page,'pages/kit.html')
        page.evaluate('''()=>{const title=document.querySelector('main h1');const range=document.createRange();range.selectNodeContents(title);const s=getSelection();s.removeAllRanges();s.addRange(range);}''')
        page.wait_for_timeout(80)
        if width<=1050:page.locator('.nav-trigger').click()
        page.locator('[data-speech="read"]').click()
        assert page.evaluate('__speech.calls.length')>0
        assert page.evaluate('__speech.calls[0].text')==page.locator('main h1').inner_text()
        page.locator('[data-speech="stop"]').click()
        page.locator('[data-speech="page"]').click();assert len(page.evaluate('__speech.calls'))>=2
        if width<=1050:page.keyboard.press('Escape')
        open_page(page)
        page.locator('#pnec-audio-form button[type="reset"]').click();assert not page.locator('#pnec-audio-form [name="enabled"]').is_checked()
        page.locator('#pnec-appearance-form button[type="reset"]').click()
        assert page.locator('[data-theme="site-default"]').get_attribute('aria-pressed')=='true'
        assert page.locator('[name="font"]').input_value()=='sans'
        assert not errors,(width,errors)
        report.append({'width':width,'themes':8,'persistence':True,'custom_contrast_guard':True,'language':'reviewed en/es labels','speech':'mock browser contract; no real audio assertion','page_errors':errors,'passed':True})
        context.close()
    # Real feature detection and safe absence; no speech is requested here.
    context=browser.new_context();context.route('**/*',offline)
    context.add_init_script("Object.defineProperty(window,'speechSynthesis',{configurable:true,value:undefined})")
    page=context.new_page();open_page(page)
    assert page.locator('[data-speech="test"]').is_disabled()
    assert 'unavailable' in page.locator('#audio .pnec-speech-status').inner_text()
    context.close()
    # Untrusted persisted fields cannot inject CSS, arbitrary fonts or language codes.
    context=browser.new_context();context.route('**/*',offline)
    context.add_init_script("localStorage.setItem('pnec_appearance_v1',JSON.stringify({font:'url(https://invalid)',preset:'invalid',language:'invalid',bgColor:'red;display:none',audio:{enabled:true,rate:999,pitch:-1,volume:2}}))")
    page=context.new_page();open_page(page)
    assert page.locator('[data-theme="site-default"]').get_attribute('aria-pressed')=='true'
    assert page.locator('[name="font"]').input_value()=='sans'
    assert page.locator('#site-language').input_value()=='en'
    assert page.locator('#speech-rate').input_value()=='2'
    assert page.locator('#speech-pitch').input_value()=='0.5'
    context.close();browser.close()
(args.output_dir/'profile-preferences-results.json').write_text(json.dumps(report,indent=2))
print('PASS: 8 themes × 4 widths, custom colors/contrast/fonts/buttons, persistence, reviewed language, opt-in speech protocol and unsupported browser fallback.')
