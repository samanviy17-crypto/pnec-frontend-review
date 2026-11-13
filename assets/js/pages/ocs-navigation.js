// OCS flat navigation extended with accessible, stationary disclosures.
// Native buttons supply Enter/Space activation. Links retain normal Tab order.
(() => {
  const header = document.getElementById('pnec-site-header');
  if (!header) return;
  const mobile = header.querySelector('.nav-trigger');
  const nav = header.querySelector('.site-nav');
  const toggles = [...header.querySelectorAll('[aria-controls]')].filter(button => button !== mobile);
  function close(button) {
    button.setAttribute('aria-expanded', 'false');
    document.getElementById(button.getAttribute('aria-controls')).hidden = true;
  }
  function closeAll() { toggles.forEach(close); }
  function closeMobile() {
    mobile.setAttribute('aria-expanded', 'false');
    mobile.setAttribute('aria-label', 'Open navigation');
    nav.classList.remove('is-open');
    closeAll();
  }
  mobile.addEventListener('click', () => {
    const opening = mobile.getAttribute('aria-expanded') !== 'true';
    closeMobile();
    if (opening) {
      mobile.setAttribute('aria-expanded', 'true');
      mobile.setAttribute('aria-label', 'Close navigation');
      nav.classList.add('is-open');
    }
  });
  toggles.forEach(button => {
    button.addEventListener('click', () => {
      const opening = button.getAttribute('aria-expanded') !== 'true';
      closeAll();
      if (opening) {
        button.setAttribute('aria-expanded', 'true');
        document.getElementById(button.getAttribute('aria-controls')).hidden = false;
      }
    });
    button.addEventListener('keydown', event => {
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        if (button.getAttribute('aria-expanded') !== 'true') button.click();
        document.getElementById(button.getAttribute('aria-controls')).querySelector('a,button').focus();
      }
    });
  });
  header.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    const open = toggles.find(button => button.getAttribute('aria-expanded') === 'true');
    if (open) { close(open); open.focus(); }
    else if (nav.classList.contains('is-open')) { closeMobile(); mobile.focus(); }
  });
  document.addEventListener('click', event => { if (!header.contains(event.target)) closeMobile(); });
  header.addEventListener('focusout', () => {
    requestAnimationFrame(() => { if (!header.contains(document.activeElement)) closeMobile(); });
  });
  matchMedia('(min-width: 1051px)').addEventListener('change', closeMobile);
})();
