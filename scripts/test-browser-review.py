"""Native engine smoke: real loopback pages, no API mocks or audio playback claim."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url',default='http://localhost:8766/')
parser.add_argument('--output-dir',type=Path,required=True)
a=parser.parse_args();base=a.base_url.rstrip('/')+'/';a.output_dir.mkdir(parents=True,exist_ok=True)
rows=[]
with sync_playwright() as p:
 for engine in ['chromium','firefox','webkit']:
  browser=getattr(p,engine).launch()
  for width in [390,768,1280]:
   c=browser.new_context(viewport={'width':width,'height':1000},reduced_motion='reduce')
   c.route('**/*',lambda r:r.continue_() if r.request.url.startswith((base,'http://localhost:8426/')) else r.abort())
   page=c.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for route in ['', 'pages/checklist.html','pages/fire-safety.html','pages/register.html','pages/settings.html','pages/profile.html','pages/volunteer.html','pages/preparedness-resources.html']:
    response=page.goto(base+route,wait_until='networkidle');assert response.status==200
    if page.locator('#pnec-bot-close').is_visible():page.locator('#pnec-bot-close').click()
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),(engine,width,route)
    expect(page.locator('#navbar-login-item')).to_be_visible()
    if route=='':assert page.locator('.pnec-context').count()==0
    if route=='pages/settings.html':
     page.locator('[data-theme="ocean"]').focus();page.keyboard.press('Enter');assert page.locator('html').get_attribute('data-appearance-preset')=='ocean'
     page.reload(wait_until='networkidle');expect(page.locator('[data-theme="ocean"]')).to_have_attribute('aria-pressed','true')
     page.select_option('#site-language','es');page.locator('#pnec-language-form button[type="submit"]').click();page.reload(wait_until='networkidle');assert page.locator('#site-language').input_value()=='es'
     page.locator('#pnec-language-form button[type="reset"]').click();page.locator('[data-theme="site-default"]').click()
     audio=page.evaluate('({supported:typeof speechSynthesis!=="undefined" && typeof SpeechSynthesisUtterance!=="undefined",voices:typeof speechSynthesis!=="undefined"?speechSynthesis.getVoices().length:0})')
     assert not page.locator('#audio [name="enabled"]').is_checked()
     expect(page.locator('[data-speech="test"]')).to_be_disabled()
     if audio['supported']:
      page.locator('#audio [name="enabled"]').check();expect(page.locator('[data-speech="test"]')).to_be_enabled();page.locator('#audio [data-speech="stop"]').click();page.locator('#audio [name="enabled"]').uncheck()
     rows.append({'engine':engine,'version':browser.version,'width':width,'native_audio_detection':audio,'audio_note':'opt-in/stop controls checked; no audible playback assertion'})
   assert not errors,(engine,width,errors);print('PASS',engine,width,'8 routes, keyboard preset, language persistence, native audio feature detection',flush=True);c.close()
  browser.close()
(a.output_dir/'browser-engine-results.json').write_text(json.dumps({'checks':rows,'route_viewport_checks':72,'page_errors':[],'passed':True},indent=2)+'\n')
