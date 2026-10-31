"""Exercise real request-worker JavaScript in Chromium with controlled fetch responses.
No application server, credentials, or resident data are used. Mock transport tests
are separate from real-API browser workflows and must not be called deployment proof.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

from release_test_support import FRONTEND_ROOT as ROOT
with sync_playwright() as play:
    browser = play.chromium.launch()
    page = browser.new_page()
    page.add_script_tag(content='const API_BASE="http://127.0.0.1:8425";')
    # Include the shared errors without redefining API_BASE.
    errors = (ROOT / 'assets/js/utils/errors.js').read_text()
    page.add_script_tag(content=errors[errors.index('const ERROR_TYPES'):])
    for name in ['auth-api.js', 'preparedness-api.js']:
        page.add_script_tag(content=(ROOT / 'assets/js/api' / name).read_text())
    results = page.evaluate('''async () => {
      const cases = [];
      async function check(name, run) {
        try {await run(); cases.push({name, pass:true});}
        catch (e) {cases.push({name, pass:false, error:e.message});}
      }
      const assert = (ok, message) => {if (!ok) throw new Error(message);};
      const response = (body, status=200) => new Response(body, {status});
      const failure = async (name, fetcher, pattern, status, type) => check(name, async () => {
        window.fetch = fetcher;
        let caught;
        try {await pnecJsonRequest('/test', {}, 20);} catch (e) {caught = e;}
        assert(caught && pattern.test(caught.message), 'Expected useful error');
        if (status) assert(caught.status === status, 'Lost HTTP status');
        if (type) assert(caught.type === type, 'Lost error type');
      });
      await check('JSON success and request credentials/payload', async () => {
        window._getAuthHeaders = () => ({'Content-Type':'application/json'});
        window.fetch = async (url, options) => {
          assert(url.endsWith('/api/preparedness'), 'Wrong URL');
          assert(options.credentials === 'include' && options.method === 'PATCH', 'Lost credentials/method');
          assert(JSON.parse(options.body).items.water === true, 'Lost payload');
          assert(options.signal instanceof AbortSignal, 'Missing abort signal');
          return response('{"ok":true}');
        };
        assert((await pnecCommunityRequest('/preparedness', 'PATCH', {items:{water:true}})).ok, 'Missing result');
      });
      await failure('401 authentication', async () => response('<html>Unauthorized</html>',401), /sign in/,401,'AUTH_REQUIRED');
      await failure('403 authorization', async () => response('{}',403), /permission/,403,'FORBIDDEN');
      await failure('400 validation detail', async () => response('{"message":"Answer all questions"}',400), /Answer all questions/,400,'INVALID_DATA');
      await failure('400 specific detail before generic message', async () => response('{"message":"The submitted data was invalid.","detail":"This reset link is invalid or expired."}',400), /invalid or expired/,400,'INVALID_DATA');
      await failure('HTML 502 server error', async () => response('<html>private upstream trace</html>',502), /unexpected error/,502,'SERVER_ERROR');
      await failure('Malformed success response', async () => response('not json'), /unreadable response/);
      await failure('Offline/network failure', async () => {throw new TypeError('Failed to fetch');}, /internet connection/,undefined,'NETWORK_ERROR');
      await failure('Fetch timeout', (url, options) => new Promise((resolve,reject) =>
        options.signal.addEventListener('abort', () => reject(new DOMException('aborted','AbortError')))), /timed out/,undefined,'TIMEOUT');
      await failure('Body-read timeout', async (url, options) => ({ok:true,status:200,json:() => new Promise((resolve,reject) =>
        options.signal.addEventListener('abort', () => reject(new DOMException('aborted','AbortError'))))}), /timed out/,undefined,'TIMEOUT');
      await check('204 empty success', async () => {
        window.fetch = async () => response(null,204);
        assert(await pnecJsonRequest('/test') === null, 'Expected empty result');
      });
      await check('Successful request clears deadline', async () => {
        let signal;
        window.fetch = async (url, options) => {signal = options.signal; return response('{}');};
        await pnecJsonRequest('/test',{},10);
        await new Promise(resolve => setTimeout(resolve,30));
        assert(!signal.aborted, 'Deadline leaked after success');
      });
      return cases;
    }''')
    for r in results:
        print(('PASS' if r['pass'] else 'FAIL') + ': ' + r['name'] + (': ' + r.get('error','') if not r['pass'] else ''))
    browser.close()
    failures = sum(not r['pass'] for r in results)
    print(f'{len(results)-failures} passed, {failures} failed (controlled-transport Chromium cases)')
    if failures:
        raise SystemExit(1)
