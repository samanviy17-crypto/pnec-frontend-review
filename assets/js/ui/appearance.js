// Personal browser preferences are deliberately separate from administrator CMS themes.
(() => {
  const key = 'pnec_appearance_v1';
  const defaults = {theme:'system',background:'plain',font:'sans',size:'standard',spacing:false,motion:false};
  const choices = {theme:['system','light','dark'],background:['plain','soft','grid'],font:['sans','serif','mono'],size:['standard','large','extra']};
  const root = document.documentElement;
  const system = matchMedia('(prefers-color-scheme: dark)');
  let current;
  function sanitize(value) {
    const clean = {...defaults};
    if (!value || typeof value !== 'object') return clean;
    Object.keys(choices).forEach(name => { if (choices[name].includes(value[name])) clean[name] = value[name]; });
    ['spacing','motion'].forEach(name => {clean[name] = value[name] === true;});
    return clean;
  }
  function apply() {
    Object.keys(current).forEach(name => root.dataset['appearance' + name[0].toUpperCase() + name.slice(1)] = String(current[name]));
    root.dataset.appearanceResolved = current.theme === 'system' ? (system.matches ? 'dark' : 'light') : current.theme;
    window.dispatchEvent(new CustomEvent('pnec:appearance-changed', {detail: {...current}}));
  }
  try { current = sanitize(JSON.parse(localStorage.getItem(key))); } catch { current = {...defaults}; }
  apply();
  system.addEventListener('change', apply);
  window.addEventListener('storage', event => {
    if (event.key !== key && event.key !== null) return;
    try {current = sanitize(JSON.parse(event.newValue));} catch {current = {...defaults};}
    apply(); sync();
  });
  let form;
  function sync() {
    if (!form) return;
    Object.keys(current).forEach(name => {
      const control = form.elements.namedItem(name);
      if (control.type === 'checkbox') control.checked = current[name]; else control.value = current[name];
    });
  }
  function save() {
    apply();
    let message = 'Appearance saved on this browser.';
    try { localStorage.setItem(key, JSON.stringify(current)); }
    catch { message = 'Appearance applied for this page. Browser storage is unavailable.'; }
    const status = document.getElementById('appearance-status');
    if (status) status.textContent = message;
  }
  document.addEventListener('DOMContentLoaded', () => {
    form = document.getElementById('pnec-appearance-form');
    if (!form) return;
    sync();
    form.addEventListener('change', () => {
      const data = Object.fromEntries(new FormData(form));
      ['spacing','motion'].forEach(name => {data[name] = form.elements.namedItem(name).checked;});
      current = sanitize(data); save();
    });
    form.addEventListener('reset', event => {event.preventDefault(); current = {...defaults}; sync(); save();});
  });
})();
