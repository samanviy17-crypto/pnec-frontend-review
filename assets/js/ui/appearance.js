// PNEC browser-local preferences. OCS preset/swatch and live-preview concepts;
// no OCS account endpoints, Google Translate cookies, or unrelated business logic.
(() => {
  const key = 'pnec_appearance_v1';
  // A missing scheme is light. Only a saved, explicit system setting follows the OS.
  const defaults = {theme:'light',preset:'site-default',background:'plain',font:'sans',size:'standard',button:'rounded',spacing:false,motion:false,bgColor:'',textColor:'',accentColor:'',language:'en',audio:{enabled:false,voice:'',rate:1,pitch:1,volume:1}};
  const presets = ['site-default','midnight','light','green','sepia','cyberpunk','ocean','sunset'];
  const choices = {theme:['system','light','dark'],preset:presets,background:['plain','soft','grid'],font:['sans','serif','mono'],size:['standard','large','extra'],button:['rounded','square','pill'],language:['en','es']};
  const root = document.documentElement;
  const system = matchMedia('(prefers-color-scheme: dark)');
  const colors = {bgColor:'--pnec-bg',textColor:'--pnec-text',accentColor:'--pnec-accent'};
  const numeric = (value, min, max, fallback) => typeof value === 'number' && Number.isFinite(value) ? Math.min(max, Math.max(min, value)) : fallback;
  function sanitize(value) {
    const clean = {...defaults, audio:{...defaults.audio}};
    if (!value || typeof value !== 'object') return clean;
    Object.keys(choices).forEach(name => { if (choices[name].includes(value[name])) clean[name] = value[name]; });
    ['spacing','motion'].forEach(name => {clean[name] = value[name] === true;});
    Object.keys(colors).forEach(name => { if (/^#[0-9a-f]{6}$/i.test(value[name] || '')) clean[name] = value[name]; });
    const a = value.audio;
    if (a && typeof a === 'object') clean.audio = {enabled:a.enabled === true,voice:typeof a.voice === 'string' ? a.voice.slice(0,200) : '',rate:numeric(a.rate,.5,2,1),pitch:numeric(a.pitch,.5,2,1),volume:numeric(a.volume,0,1,1)};
    return clean;
  }
  let current;
  try { current = sanitize(JSON.parse(localStorage.getItem(key))); } catch { current = sanitize(null); }
  // OCS live-preview readability math (WCAG relative luminance).
  function luminance(hex) {
    const rgb = hex.match(/[a-f\d]{2}/gi).map(part => {const c = parseInt(part,16)/255; return c <= .04045 ? c/12.92 : ((c+.055)/1.055)**2.4;});
    return .2126*rgb[0] + .7152*rgb[1] + .0722*rgb[2];
  }
  function contrast(a,b) {const x=luminance(a), y=luminance(b); return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
  const colorHex = value => {
    if (/^#[0-9a-f]{6}$/i.test(value)) return value;
    if (/^#[0-9a-f]{3}$/i.test(value)) return '#' + value.slice(1).split('').map(c => c+c).join('');
    const rgb = value.match(/\d+/g); return rgb?.length >= 3 ? '#' + rgb.slice(0,3).map(n => (+n).toString(16).padStart(2,'0')).join('') : '#10213a';
  };
  function palette() {const css = getComputedStyle(root); return Object.fromEntries(Object.entries(colors).map(([key,prop]) => [key,colorHex(css.getPropertyValue(prop).trim())]));}
  function apply() {
    ['theme','preset','background','font','size','button','spacing','motion'].forEach(name => {root.dataset['appearance' + name[0].toUpperCase() + name.slice(1)] = String(current[name]);});
    root.dataset.appearanceResolved = current.theme === 'system' ? (system.matches ? 'dark' : 'light') : current.theme;
    // User-picked colors are validated hex-only custom-property values; all layout
    // and preset styling stays in Sass. Color previews require runtime tokens.
    Object.entries(colors).forEach(([name,prop]) => {root.style.removeProperty(prop); if (current[name]) root.style.setProperty(prop,current[name]);});
    root.style.removeProperty('--pnec-tint'); root.style.removeProperty('--pnec-surface'); root.style.removeProperty('--pnec-muted');
    if (current.bgColor) { root.style.setProperty('--pnec-surface',current.bgColor); root.style.setProperty('--pnec-tint',current.bgColor); }
    if (current.textColor) root.style.setProperty('--pnec-muted',current.textColor);
    let p = palette();
    if(Object.keys(colors).some(name=>current[name]) && (contrast(p.bgColor,p.textColor)<4.5 || contrast(p.bgColor,p.accentColor)<4.5)) {
      // Invalid/corrupt persisted palettes fall back to the selected preset.
      Object.entries(colors).forEach(([name,prop])=>{current[name]='';root.style.removeProperty(prop);});
      root.style.removeProperty('--pnec-surface');root.style.removeProperty('--pnec-muted');root.style.removeProperty('--pnec-tint');p=palette();
    }
    const buttonText = contrast(p.accentColor,'#ffffff') >= 4.5 ? '#ffffff' : '#000000';
    const customAccent = current.accentColor || current.preset !== 'site-default';
    root.style.setProperty('--pnec-action-fill', customAccent ? p.accentColor : 'var(--pnec-brand)');
    root.style.setProperty('--pnec-action-ink', customAccent ? buttonText : 'var(--pnec-brand-ink)');
    window.PNECLocale.setLanguage(current.language);
    window.dispatchEvent(new CustomEvent('pnec:appearance-changed', {detail:structuredClone(current)}));
  }
  function save(statusId='appearance-status', message='Preferences saved in this browser.') {
    apply();
    try {localStorage.setItem(key,JSON.stringify(current));}
    catch {message = 'Preferences applied for this page. Browser storage is unavailable.';}
    const status=document.getElementById(statusId); if (status) window.PNECLocale.text(status,message);
  }
  let form, colorDraft = null;
  function sync() {
    if (!form) return;
    Object.keys(choices).concat(['spacing','motion']).forEach(name => {const control=form.elements.namedItem(name); if (control) {if (control.type==='checkbox') control.checked=current[name]; else control.value=current[name];}});
    const p=colorDraft || palette();
    Object.keys(colors).forEach(name => {form.elements.namedItem(name).value=colorDraft ? p[name] : current[name] || p[name];});
    const defaultActive = current.theme === defaults.theme && current.background === defaults.background
      && !Object.keys(colors).some(name => current[name]);
    document.querySelectorAll('[data-theme]').forEach(button => {
      const active = button.dataset.theme === current.preset &&
        (current.preset !== 'site-default' || defaultActive);
      button.setAttribute('aria-pressed', String(active));
    });
    const check=document.getElementById('appearance-contrast');
    const textRatio=contrast(p.bgColor,p.textColor), accentRatio=contrast(p.bgColor,p.accentColor);
    check.textContent=`Text: ${textRatio.toFixed(2)}:1. Accent: ${accentRatio.toFixed(2)}:1. ` + (textRatio>=4.5 && accentRatio>=4.5 ? 'Good contrast.' : 'Low contrast: choose more distinct colors before saving.');
    document.getElementById('site-language').value=current.language;
  }
  // Used by the separate language/audio controllers without exposing account data.
  window.PNECPreferences = {get:()=>structuredClone(current), update(patch,status){current=sanitize({...current,...patch});save(status);sync();},contrast};
  apply();
  system.addEventListener('change',()=>{apply();sync();});
  window.addEventListener('storage',event=>{if(event.key!==key && event.key!==null)return;try {current=sanitize(JSON.parse(event.newValue));}catch {current=sanitize(null);}apply();sync();});
  document.addEventListener('DOMContentLoaded',()=>{
    apply(); form=document.getElementById('pnec-appearance-form'); if (!form)return;
    sync();
    document.querySelectorAll('[data-theme]').forEach(button=>button.addEventListener('click',()=>{
      colorDraft=null;document.querySelector('.pnec-live-preview').removeAttribute('style');
      current.preset=button.dataset.theme;
      current.theme=['site-default','light','sepia','sunset'].includes(current.preset)?'light':'dark';
      if (current.preset === 'site-default') current.background = defaults.background;
      current.font=current.preset==='sepia'?'serif':current.preset==='cyberpunk'?'mono':'sans';
      Object.keys(colors).forEach(name=>{current[name]='';});save();sync();
    }));
    form.addEventListener('input',event=>{
      const name=event.target.name;
      if (Object.hasOwn(colors,name)) {
        colorDraft=Object.fromEntries(Object.keys(colors).map(key=>[key,form.elements.namedItem(key).value]));
        const preview=document.querySelector('.pnec-live-preview');
        Object.entries(colors).forEach(([key,prop])=>preview.style.setProperty(prop,colorDraft[key]));
        preview.style.setProperty('--pnec-action-fill',colorDraft.accentColor);
        preview.style.setProperty('--pnec-action-ink',contrast(colorDraft.accentColor,'#ffffff')>=4.5?'#ffffff':'#000000');
        sync();
      }
    });
    form.addEventListener('change',event=>{
      const name=event.target.name;
      if (Object.hasOwn(colors,name)) return;
      if (Object.hasOwn(choices,name)) current[name]=event.target.value;
      if (['motion','spacing'].includes(name)) current[name]=event.target.checked;
      if (name==='theme') {current.preset='site-default';Object.keys(colors).forEach(key=>{current[key]='';});}
      save();sync();
    });
    form.addEventListener('submit',event=>{
      event.preventDefault();
      if(colorDraft) {
        if(contrast(colorDraft.bgColor,colorDraft.textColor)<4.5 || contrast(colorDraft.bgColor,colorDraft.accentColor)<4.5) {
          document.getElementById('appearance-status').textContent='Colors need at least 4.5:1 text and accent contrast against the background. The page keeps its readable colors; adjust the live preview and save again.';
          return;
        }
        Object.assign(current,colorDraft);colorDraft=null;
        document.querySelector('.pnec-live-preview').removeAttribute('style');
      }
      save();sync();
    });
    form.addEventListener('reset',event=>{event.preventDefault();const {language,audio}=current;colorDraft=null;document.querySelector('.pnec-live-preview').removeAttribute('style');current={...sanitize(null),language,audio};save();sync();});
    document.getElementById('pnec-language-form').addEventListener('submit',event=>{event.preventDefault();current.language=document.getElementById('site-language').value;save('language-status');sync();});
    document.getElementById('pnec-language-form').addEventListener('reset',event=>{event.preventDefault();current.language='en';save('language-status','Language reset to English.');sync();});
  });
})();
