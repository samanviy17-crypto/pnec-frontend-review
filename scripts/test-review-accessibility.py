"""Record axe WCAG A/AA findings, responsive geometry and current review screenshots.
Axe is supplied by a local --axe-script path, never fetched into the product.
This audit reports findings; it is not a manual screen-reader or legal certification.
"""
import argparse,asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url',default='http://localhost:8766/')
parser.add_argument('--axe-script',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
a=parser.parse_args();base=a.base_url.rstrip('/')+'/';a.output_dir.mkdir(parents=True,exist_ok=True)
routes=['','pages/about.html','pages/checklist.html','pages/kit.html','pages/preparedness-resources.html','pages/fire-safety.html','pages/community-events-and-activities.html','pages/volunteer.html','pages/find-your-neighborhood.html','pages/programs-and-services.html','pages/contact.html','pages/register.html','pages/profile.html','pages/settings.html','pages/gallery.html','pages/blog.html','donation-form/','pages/security.html']
core=['','pages/checklist.html','pages/fire-safety.html','pages/register.html','pages/profile.html','pages/settings.html','pages/volunteer.html']
presets=['site-default','midnight','light','green','sepia','cyberpunk','ocean','sunset']
jobs=[(r,w,'site-default') for w in [390,768,1280] for r in routes]+[(r,1280,t) for t in presets[1:] for r in core]
async def main():
 results=[];queue=asyncio.Queue()
 for j in jobs:queue.put_nowait(j)
 async with async_playwright() as p:
  browser=await p.chromium.launch()
  async def worker():
   while not queue.empty():
    route,width,theme=queue.get_nowait()
    c=await browser.new_context(viewport={'width':width,'height':1000},reduced_motion='reduce')
    await c.add_init_script('localStorage.setItem("pnec_appearance_v1",'+json.dumps(json.dumps({'preset':theme,'theme':'dark' if theme in ['midnight','green','cyberpunk','ocean'] else 'light'}))+')')
    # Static and same-site API only. No external scripts or providers.
    async def local(request):
     if request.request.url.startswith((base,'http://localhost:8426/')):await request.continue_()
     else:await request.abort()
    await c.route('**/*',local);page=await c.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    response=await page.goto(base+route,wait_until='networkidle')
    if await page.locator('#pnec-bot-close').is_visible():await page.locator('#pnec-bot-close').click()
    await page.add_script_tag(path=str(a.axe_script))
    data=await page.evaluate('async()=>await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa"]}})')
    violations=[{'id':v['id'],'impact':v['impact'],'help':v['help'],'nodes':[{'target':n['target'],'summary':n['failureSummary']} for n in v['nodes']]} for v in data['violations']]
    result={'route':route or '/','width':width,'theme':theme,'http_status':response.status,'overflow':await page.evaluate('document.documentElement.scrollWidth>innerWidth'),'page_errors':errors,'violations':violations,'incomplete_rules':[v['id'] for v in data['incomplete']]}
    if theme=='site-default' and width in [390,1280] and route in core+['pages/preparedness-resources.html','pages/community-events-and-activities.html']:
     name=(route.removeprefix('pages/').replace('.html','').strip('/') or 'home')+f'-{width}.png'
     if route=='pages/register.html':
      # Capture empty form controls, excluding legacy testimonial/personal copy.
      await page.locator('.auth-form-panel').screenshot(path=str(a.output_dir/name))
     else:await page.screenshot(path=str(a.output_dir/name),full_page=True)
     result['screenshot']=name
    results.append(result);print(route or '/',width,theme,'violations',[(v['id'],len(v['nodes'])) for v in violations],'overflow',result['overflow'],flush=True)
    await c.close();queue.task_done()
  await asyncio.gather(worker(),worker(),worker());await browser.close()
 report={'axe_version':'4.11.0','policy':'real loopback API for anonymous pages; no external providers; no mocked identity','checks':sorted(results,key=lambda r:(r['theme'],r['width'],r['route'])),'manual_required':['VoiceOver/NVDA reading order and announcements','audible OS voice playback','image-background contrast and gradient text','touch and high zoom with assistive technology']}
 (a.output_dir/'accessibility-results.json').write_text(json.dumps(report,indent=2)+'\n')
 assert all(r['http_status']==200 and not r['overflow'] and not r['page_errors'] for r in results),'Page/geometry errors; inspect report'
 print(f'Completed {len(results)} checks; axe findings and incomplete rules remain explicitly recorded.')
asyncio.run(main())
