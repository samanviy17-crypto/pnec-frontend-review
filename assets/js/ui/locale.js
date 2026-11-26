---
---
(() => {
  const spanish = {{ site.data.pnec_es | jsonify }};
  const attributes = ['placeholder', 'aria-label', 'title', 'alt'];
  const excluded = 'script,style,pre,code,textarea,[contenteditable], [translate="no"], .pnec-bot-msg-bubble';
  const bindings = new Map();
  let language = 'en';
  let ready = false;
  const normalize = text => text.trim().replace(/\s+/g, ' ');
  const translate = (key, english = key, values = {}) => {
    const template = language === 'es' && Object.hasOwn(spanish, key) ? spanish[key] : english;
    return template.replace(/\{(\w+)\}/g, (token, name) => Object.hasOwn(values, name) ? values[name] : token);
  };

  function bind(node, key, english, attribute, values, leading = '', trailing = '') {
    const set = () => {
      const translated = translate(key, english, typeof values === 'function' ? values() : values);
      if (attribute) node.setAttribute(attribute, translated);
      else if (node.nodeType === Node.TEXT_NODE) node.nodeValue = language === 'es' ? leading + translated + trailing : translated;
      else node.textContent = translated;
    };
    if (!bindings.has(node)) bindings.set(node, new Map());
    bindings.get(node).set(attribute, set);
    set();
  }

  function scanStatic(container = document.body) {
    for (const element of container.querySelectorAll('*')) {
      if (element.closest(excluded) || element.tagName === 'TITLE') continue;
      const boundText = bindings.get(element)?.has(null);
      const explicit = element.dataset.i18n;
      if (element.tagName === 'OPTION' && !element.hasAttribute('value')) element.value = element.value;
      for (const attribute of attributes) {
        const value = element.getAttribute(attribute);
        if (!bindings.get(element)?.has(attribute) && value && Object.hasOwn(spanish, normalize(value))) bind(element, normalize(value), value, attribute);
      }
      if (boundText) continue;
      for (const node of element.childNodes) {
        if (bindings.has(node) || node.nodeType !== Node.TEXT_NODE || !node.nodeValue.trim()) continue;
        const source = node.nodeValue;
        const key = explicit || normalize(source);
        if (Object.hasOwn(spanish, key)) {
          const leading = source.match(/^\s*/)[0];
          const trailing = source.match(/\s*$/)[0];
          bind(node, key, source, null, undefined, leading, trailing);
        }
        else if (element.childElementCount === 0 && !element.hasAttribute('lang') && /[a-z]{2}/i.test(source)) {
          element.dataset.sourceLanguage = 'en';
          if (language === 'es') element.lang = 'en';
        }
      }
    }
  }

  function refresh() {
    for (const [node, setters] of bindings) {
      if (node.isConnected) setters.forEach(set => set());
      else bindings.delete(node);
    }
    for (const element of document.querySelectorAll('[data-source-language]')) {
      if (language === 'es') element.lang = element.dataset.sourceLanguage;
      else element.removeAttribute('lang');
    }
    const title = document.querySelector('title');
    if (title && language === 'es') {
      const source = title.dataset.english || title.textContent;
      title.dataset.english = source;
      const [name, ...suffix] = source.split(' — ');
      title.textContent = [translate(name), ...suffix].join(' — ');
    } else if (title?.dataset.english) title.textContent = title.dataset.english;
  }

  window.PNECLocale = {
    scanStatic,
    get language() { return language; },
    t: translate,
    text(node, key, english = key, values = {}) { bind(node, key, english, null, values); },
    attribute(node, attribute, key, english = key, values = {}) { bind(node, key, english, attribute, values); },
    setLanguage(next) {
      const changed = language !== next;
      language = next === 'es' ? 'es' : 'en';
      document.documentElement.lang = language === 'es' ? 'es-US' : 'en-US';
      document.documentElement.dataset.siteLanguage = language;
      if (ready && changed) refresh();
      if (changed) window.dispatchEvent(new CustomEvent('pnec:language-changed', {detail: language}));
    }
  };
  document.addEventListener('DOMContentLoaded', () => { scanStatic(); ready = true; refresh(); });
})();
