import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import test from 'node:test';
import assert from 'node:assert/strict';

const source = readFileSync(new URL('./review-status.js', import.meta.url), 'utf8');
const api = 'https://pnec-backend-review.onrender.com';
async function render(base, fetch) {
  let start, banner;
  const document = {
    addEventListener: (_, callback) => { start = callback; },
    createElement: () => ({setAttribute() {}, style: {}}),
    body: {prepend: element => { banner = element; }},
  };
  vm.runInNewContext(source, {document, window: {PNEC_API_BASE: base}, fetch, AbortSignal});
  await start();
  return banner.textContent;
}
test('unconfigured and unapproved destinations keep the disconnected warning without requests', async () => {
  for (const base of [undefined, 'https://api.pnec-review.invalid', 'https://unapproved.example']) {
    assert.match(await render(base, () => assert.fail('Unexpected API request')), /not connected/);
  }
});
test('successful review health and readiness retain service and storage limitations', async () => {
  const paths = [];
  const message = await render(api, async (url, options) => {
    paths.push(url);
    assert.equal(options.mode, 'cors');
    return {ok: true, json: async () => url.endsWith('/health')
      ? {status: 'ok', review: true} : {status: 'ready'}};
  });
  assert.deepEqual(paths.sort(), [api + '/api/health', api + '/api/ready']);
  assert.match(message, /health and readiness verified/);
  assert.match(message, /resets on restart/);
  assert.match(message, /unavailable/);
});
test('network and CORS failures keep the unverified warning', async () => {
  assert.match(await render(api, async () => { throw new TypeError('Failed to fetch'); }), /could not be verified/);
});
test('HTTP errors and unreadable responses keep the unverified warning', async () => {
  for (const response of [{ok: false}, {ok: true, json: async () => { throw new SyntaxError(); }}]) {
    assert.match(await render(api, async () => response), /could not be verified/);
  }
});
test('wrong service identity or readiness cannot claim a verified connection', async () => {
  for (const payload of [{status: 'ok'}, {status: 'starting', review: true}]) {
    assert.match(await render(api, async () => ({ok: true, json: async () => payload})), /could not be verified/);
  }
});
