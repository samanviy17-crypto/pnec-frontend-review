// Shared OCS sidebar: native disclosures plus a modal mobile drawer.
(() => {
  const header = document.getElementById('pnec-site-header');
  if (!header) return;
  const mobile = header.querySelector('.nav-trigger');
  const nav = header.querySelector('.site-nav');
  const backdrop = document.querySelector('.pnec-drawer-backdrop');
  const narrow = matchMedia('(max-width: 1050px)');
  const toggles = [...header.querySelectorAll('[aria-controls]')].filter(button => button !== mobile);
  let isolated = [];
  function close(button) {
    button.setAttribute('aria-expanded', 'false');
    document.getElementById(button.getAttribute('aria-controls')).hidden = true;
  }
  function closeAll() { toggles.forEach(close); }
  function closeMobile(restore = false) {
    const wasOpen = nav.classList.contains('is-open');
    mobile.setAttribute('aria-expanded', 'false');
    mobile.setAttribute('aria-label', 'Open navigation');
    nav.classList.remove('is-open');
    header.removeAttribute('role'); header.removeAttribute('aria-modal'); header.removeAttribute('aria-label');
    backdrop.hidden = true;
    document.body.classList.remove('pnec-drawer-open');
    isolated.forEach(([node, wasInert]) => {node.inert = wasInert;}); isolated = [];
    closeAll();
    if (restore && wasOpen) mobile.focus();
  }
  mobile.addEventListener('click', () => {
    const opening = mobile.getAttribute('aria-expanded') !== 'true';
    closeMobile();
    if (opening) {
      mobile.setAttribute('aria-expanded', 'true'); mobile.setAttribute('aria-label', 'Close navigation');
      nav.classList.add('is-open'); backdrop.hidden = false;
      header.setAttribute('role', 'dialog'); header.setAttribute('aria-modal', 'true'); header.setAttribute('aria-label', 'Site navigation');
      document.body.classList.add('pnec-drawer-open');
      [...document.body.children].filter(node => node !== header && node !== backdrop && !['SCRIPT','STYLE','LINK'].includes(node.tagName)).forEach(node => {
        isolated.push([node, node.inert]); node.inert = true;
      });
      nav.querySelector('a').focus();
    }
  });
  header.querySelector('.pnec-skip').addEventListener('click', () => closeMobile());
  nav.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (!link) return;
    const url = new URL(link.href, location.href);
    if (url.origin === location.origin) closeMobile();
  });
  backdrop.addEventListener('click', () => closeMobile(true));
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
    if (event.key === 'Tab' && narrow.matches && nav.classList.contains('is-open')) {
      const focusable = [...header.querySelectorAll('a,button,select,input')].filter(node => node.getClientRects().length && !node.disabled && node.tabIndex >= 0);
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {event.preventDefault(); last.focus();}
      else if (!event.shiftKey && document.activeElement === last) {event.preventDefault(); first.focus();}
    }
    if (event.key !== 'Escape') return;
    const open = toggles.find(button => button.getAttribute('aria-expanded') === 'true');
    if (open) { close(open); open.focus(); }
    else closeMobile(true);
  });
  document.addEventListener('click', event => { if (!header.contains(event.target) && event.target !== backdrop) closeMobile(); });
  header.addEventListener('focusout', () => {
    requestAnimationFrame(() => { if (!header.contains(document.activeElement) && !nav.classList.contains('is-open')) closeAll(); });
  });
  narrow.addEventListener('change', () => closeMobile(true));
})();
