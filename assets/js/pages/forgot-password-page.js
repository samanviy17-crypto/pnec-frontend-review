document.addEventListener('DOMContentLoaded', initForgotPage);

const SITE_BASE = window.PNEC_SITE_BASE || '';

function initForgotPage() {
  const form = document.getElementById('forgot-form');
  if (form) form.addEventListener('submit', handleForgotSubmit);
}

async function handleForgotSubmit(e) {
  e.preventDefault();
  const email = document.getElementById('forgot-email').value.trim();
  const errorBox = document.getElementById('forgot-error');
  const successBox = document.getElementById('forgot-success');
  const btn = document.getElementById('forgot-submit-btn');

  errorBox.textContent = '';
  successBox.style.display = 'none';

  if (!email) {
    errorBox.textContent = 'Please enter your email address.';
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Sending…';

  try {
    const data = await requestPasswordReset(email);
    successBox.textContent = data.message;
    successBox.style.display = 'block';
    document.getElementById('forgot-form').style.display = 'none';
  } catch (error) {
    errorBox.textContent = error.message || 'Unable to connect. Please check your connection and try again.';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Send Reset Link';
  }
}
