// Public review pages must not imply that an unconfigured API is operational.
document.addEventListener('DOMContentLoaded', async () => {
  const banner = document.createElement('aside');
  banner.setAttribute('role', 'status');
  banner.style.cssText = 'padding:12px 20px;background:#fff3cd;color:#493c12;text-align:center;font:16px/1.5 system-ui';
  const base = window.PNEC_API_BASE || '';
  const configured = /^https:\/\/pnec-backend-review(?:-[a-z0-9]+)?\.onrender\.com$/.test(base);
  const unavailable = 'Login, registration, live risk, chat, and saved changes are unavailable until the API connection is verified.';
  banner.textContent = configured
    ? 'PNEC review preview — checking the review API connection. Free hosting may take a minute to wake up. Use synthetic data only.'
    : `PNEC static review preview — the review API is not connected. ${unavailable}`;
  document.body.prepend(banner);
  if (!configured) return;
  try {
    const responses = await Promise.all(['/api/health', '/api/ready'].map(path =>
      fetch(base + path, {mode: 'cors', cache: 'no-store', signal: AbortSignal.timeout(90000)})
    ));
    if (responses.some(response => !response.ok)) throw new Error('API unavailable');
    const [health, ready] = await Promise.all(responses.map(response => response.json()));
    if (health.status !== 'ok' || health.review !== true || ready.status !== 'ready') {
      throw new Error('Review API not ready');
    }
    banner.textContent = 'PNEC review preview — review API health and readiness verified. Use synthetic data only. Temporary storage resets on restart. Email delivery, AI provider chat, and the RPG are unavailable; individual features still require verification.';
  } catch {
    banner.textContent = `PNEC review preview — the review API connection could not be verified. The service may be waking up or unavailable; reload to retry. ${unavailable}`;
  }
});
