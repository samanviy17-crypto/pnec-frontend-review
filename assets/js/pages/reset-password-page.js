document.addEventListener('DOMContentLoaded', () => {
  const token = new URLSearchParams(location.search).get('token');
  history.replaceState(null, '', location.pathname);
  const form = document.getElementById('reset-form');
  const error = document.getElementById('reset-error');
  if (!token) { error.textContent = 'Request a new password reset link.'; form.hidden = true; return; }
  form.addEventListener('submit', async event => {
    event.preventDefault(); error.textContent = '';
    const password = document.getElementById('reset-password').value;
    if (password !== document.getElementById('reset-confirm').value) { error.textContent = 'Passwords do not match.'; return; }
    const button = form.querySelector('button'); button.disabled = true;
    try {
      const result = await resetPassword(token, password);
      localStorage.removeItem('pnec_token'); sessionStorage.removeItem('pnec_token'); localStorage.removeItem('pnec_user'); sessionStorage.removeItem('pnec_user');
      document.getElementById('reset-success').textContent = result.message; form.hidden = true;
    } catch (failure) { error.textContent = failure.message; }
    finally { button.disabled = false; }
  });
});
