// Public review pages must not imply that an unconfigured API is operational.
document.addEventListener('DOMContentLoaded', () => {
  const banner = document.createElement('aside');
  banner.setAttribute('role', 'status');
  banner.style.cssText = 'padding:12px 20px;background:#fff3cd;color:#493c12;text-align:center;font:16px/1.5 system-ui';
  const configured = !window.PNEC_API_BASE.includes('.invalid');
  banner.textContent = configured
    ? 'PNEC review preview — separate test API with temporary storage. Use synthetic data only. Email, AI providers, and the RPG are not configured.'
    : 'PNEC static review preview — the review API is not connected. Login, registration, live risk, chat, and saved changes are unavailable.';
  document.body.prepend(banner);
});
