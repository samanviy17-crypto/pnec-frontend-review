// PNEC browser-local preferences. OCS preset/swatch and live-preview concepts;
// no OCS account endpoints, Google Translate cookies, or unrelated business logic.
(() => {
  const key = 'pnec_appearance_v1';
  const defaults = {theme:'system',preset:'site-default',background:'plain',font:'sans',size:'standard',button:'rounded',spacing:false,motion:false,bgColor:'',textColor:'',accentColor:'',language:'en',audio:{enabled:false,voice:'',rate:1,pitch:1,volume:1}};
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
    root.style.removeProperty('--pnec-surface'); root.style.removeProperty('--pnec-muted');
    if (current.bgColor) root.style.setProperty('--pnec-surface',current.bgColor);
    if (current.textColor) root.style.setProperty('--pnec-muted',current.textColor);
    let p = palette();
    if(Object.keys(colors).some(name=>current[name]) && (contrast(p.bgColor,p.textColor)<4.5 || contrast(p.bgColor,p.accentColor)<4.5)) {
      // Invalid/corrupt persisted palettes fall back to the selected preset.
      Object.entries(colors).forEach(([name,prop])=>{current[name]='';root.style.removeProperty(prop);});
      root.style.removeProperty('--pnec-surface');root.style.removeProperty('--pnec-muted');p=palette();
    }
    root.style.setProperty('--pnec-button-text',contrast(p.accentColor,'#ffffff') >= 4.5 ? '#ffffff' : '#111111');
    applyLanguage();
    window.dispatchEvent(new CustomEvent('pnec:appearance-changed', {detail:structuredClone(current)}));
  }
  const translations = {
    Home:'Inicio',Prepare:'Preparación',Resources:'Recursos',Community:'Comunidad',Profile:'Perfil',
    'Home Overview':'Resumen de inicio','About PNEC':'Acerca de PNEC','Weekly Preparedness Tip':'Consejo semanal','Our Story':'Nuestra historia','Contact PNEC':'Contacto',
    'Preparedness Dashboard':'Panel de preparación','Preparedness Checklist':'Lista de preparación','Emergency Kit':'Kit de emergencia','Preparedness Quiz':'Cuestionario de preparación','Household Planning':'Plan del hogar','Find Your PNEC Role':'Encuentre su función',
    'Resource Library':'Biblioteca de recursos','Fire Safety':'Seguridad contra incendios','Earthquake Safety':'Seguridad ante terremotos','Hazard Information':'Información sobre peligros','Programs and Services':'Programas y servicios','Past Events and Articles':'Eventos y artículos anteriores','Security and Privacy':'Seguridad y privacidad',
    'Community Events':'Eventos comunitarios','Volunteer Opportunities':'Oportunidades de voluntariado','Volunteer Shifts':'Turnos de voluntariado','Supply Drives':'Colectas de suministros','Neighborhood Resources':'Recursos vecinales','Report a Hazard':'Informar de un peligro','Community Gallery':'Galería comunitaria','News and Updates':'Noticias','Support PNEC':'Apoyar a PNEC',
    Dashboard:'Panel',Preferences:'Preferencias','Account Settings':'Ajustes de cuenta','Log In / Sign Up':'Iniciar sesión / Registrarse','Account tools':'Herramientas de cuenta',
    'Your PNEC':'Su PNEC',Appearance:'Apariencia',Language:'Idioma',Audio:'Audio','Pick a starting point':'Elija un punto de partida','Fine-tune':'Personalizar','Color scheme':'Modo de color','Font family':'Tipo de letra','Text size':'Tamaño del texto','Background pattern':'Patrón de fondo','Background color':'Color de fondo','Text color':'Color del texto','Accent color':'Color de acento','Button style':'Estilo de botón','More line spacing':'Más espacio entre líneas','Reduce motion':'Reducir movimiento','Live preview':'Vista previa','Save preferences':'Guardar preferencias','Reset to defaults':'Restablecer valores','Site language':'Idioma del sitio','Save language':'Guardar idioma','Reset to English':'Restablecer inglés',
    'Enable text-to-speech':'Activar lectura en voz alta',Voice:'Voz','Speech speed':'Velocidad',Pitch:'Tono',Volume:'Volumen','Test text':'Texto de prueba','Test Voice':'Probar voz','Save audio':'Guardar audio','Reset audio':'Restablecer audio',Listen:'Escuchar','Read page':'Leer página','Read selected text':'Leer texto seleccionado','Pause speech':'Pausar voz','Stop speech':'Detener voz',
    'preferences-intro':'Personalice PNEC. Estas preferencias se guardan en este navegador y están disponibles sin una cuenta.',
    'theme-intro':'Elija un tema y personalícelo. Las opciones se guardan automáticamente; los colores personalizados se muestran primero en la vista previa y se aplican con Guardar preferencias.',
    'language-coverage':'El idioma se aplica a las etiquetas revisadas de navegación y preferencias. Las guías, el contenido de usuarios, los formularios y los mensajes de la API conservan su idioma original. No se ofrece traducción automática de páginas.',
    'audio-intro':'Escuche el texto seleccionado o el contenido principal de una página cuando usted lo decida. El audio nunca comienza automáticamente. Las voces disponibles dependen del navegador y del sistema operativo.'
  };
  const english = new WeakMap();
  function applyLanguage() {
    root.dataset.siteLanguage = current.language;
    // Main content retains lang=en; mark only the reviewed translated labels.
    document.querySelectorAll('[data-i18n]').forEach(node => {
      if (!english.has(node)) english.set(node,node.textContent);
      node.textContent = current.language === 'es' ? translations[node.dataset.i18n] || english.get(node) : english.get(node);
      node.lang = current.language === 'es' && translations[node.dataset.i18n] ? 'es' : 'en';
    });
  }
  function save(statusId='appearance-status', message='Preferences saved in this browser.') {
    apply();
    try {localStorage.setItem(key,JSON.stringify(current));}
    catch {message = 'Preferences applied for this page. Browser storage is unavailable.';}
    const status=document.getElementById(statusId); if (status) status.textContent=message;
  }
  let form, colorDraft = null;
  function sync() {
    if (!form) return;
    Object.keys(choices).concat(['spacing','motion']).forEach(name => {const control=form.elements.namedItem(name); if (control) {if (control.type==='checkbox') control.checked=current[name]; else control.value=current[name];}});
    const p=colorDraft || palette();
    Object.keys(colors).forEach(name => {form.elements.namedItem(name).value=colorDraft ? p[name] : current[name] || p[name];});
    document.querySelectorAll('[data-theme]').forEach(button => button.setAttribute('aria-pressed',String(button.dataset.theme===current.preset)));
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
      current.theme=current.preset==='site-default'?'system':['light','sepia','sunset'].includes(current.preset)?'light':'dark';
      current.font=current.preset==='sepia'?'serif':current.preset==='cyberpunk'?'mono':'sans';
      Object.keys(colors).forEach(name=>{current[name]='';});save();sync();
    }));
    form.addEventListener('input',event=>{
      const name=event.target.name;
      if (Object.hasOwn(colors,name)) {
        colorDraft=Object.fromEntries(Object.keys(colors).map(key=>[key,form.elements.namedItem(key).value]));
        const preview=document.querySelector('.pnec-live-preview');
        Object.entries(colors).forEach(([key,prop])=>preview.style.setProperty(prop,colorDraft[key]));
        preview.style.setProperty('--pnec-button-text',contrast(colorDraft.accentColor,'#ffffff')>=4.5?'#ffffff':'#111111');
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
