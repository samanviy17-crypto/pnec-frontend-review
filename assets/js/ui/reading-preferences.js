// Browser speech synthesis only. No microphone, autoplay, server audio or account data.
(() => {
  const preferences = window.PNECPreferences;
  if (!preferences) return;
  const supported = typeof window.speechSynthesis?.speak === 'function' && typeof window.SpeechSynthesisUtterance === 'function';
  const synth = supported ? window.speechSynthesis : null;
  const locale = window.PNECLocale;
  let selectedRange = null, chunks = [], active = false, generation = 0;
  function status(message) {const nodes=[...document.querySelectorAll('.pnec-speech-status')]; const target=document.querySelector('#pnec-audio-form .pnec-speech-status') || nodes[0]; nodes.forEach(node=>{locale.text(node,node===target?message:'');});}
  function settings() {return preferences.get().audio;}
  function pauseState(paused) {document.querySelectorAll('[data-speech="pause"]').forEach(button=>button.setAttribute('aria-pressed',String(paused)));}
  function stop(announce=true) {generation++;chunks=[];active=false;pauseState(false);if(synth)synth.cancel();if(announce)status('Speech stopped.');}
  function updateButtons() {
    const audio=settings();
    document.querySelectorAll('.pnec-reading-tools').forEach(node=>{node.hidden=!supported || !audio.enabled;});
    document.querySelectorAll('[data-speech]').forEach(button=>{button.disabled=!supported || !audio.enabled;});
    if (!audio.enabled && active) stop(false);
    pauseState(Boolean(synth?.paused));
  }
  function availableVoices() {
    const select=document.getElementById('speech-voice');if(!select || !supported)return;
    const value=select.value || settings().voice;
    select.replaceChildren(new Option(locale.t('Automatic compatible voice'),''));
    const matching = compatibleVoices(locale.language);
    matching.forEach(voice=>{select.add(new Option(`${voice.name} (${voice.lang})`,voice.voiceURI));});
    if ([...select.options].some(option=>option.value===value))select.value=value;
    if (!active) status(matching.length ? '' : 'No compatible voice is available.');
  }
  function formSettings() {
    const form=document.getElementById('pnec-audio-form');
    return form?{enabled:form.elements.enabled.checked,voice:form.elements.voice.value || (!compatibleVoices(locale.language).some(voice => voice.voiceURI === settings().voice) ? settings().voice : ''),rate:+form.elements.rate.value,pitch:+form.elements.pitch.value,volume:+form.elements.volume.value}:settings();
  }
  const languageOf = element => element?.closest('[lang]')?.lang || document.documentElement.lang || 'en';
  const baseLanguage = language => language.toLowerCase().split('-')[0];
  function compatibleVoices(lang) {
    return synth?.getVoices().filter(voice => baseLanguage(voice.lang) === baseLanguage(lang)) || [];
  }
  function noVoice(lang) {
    const message = 'No compatible voice was found ({language}). Add a voice in your device accessibility settings, then reopen the browser.';
    const target = document.querySelector('#pnec-audio-form .pnec-speech-status')
      || document.querySelector('.pnec-reading-tools:not([hidden]) .pnec-speech-status');
    if (target) locale.text(target,'speech.noVoice',message,{language:lang});
  }
  function speak(parts, audio=settings()) {
    if(!supported) {status('Text-to-speech is unavailable in this browser.');return;}
    if(!audio.enabled) {status('Enable text-to-speech in Preferences first.');return;}
    if (!parts.length) {status('Select text or open a page with readable content.');return;}
    stop(false);active=true;
    for (const {text, lang} of parts) {
      const segments = text.trim().match(/[\s\S]{1,200}(?:\s|$)|[\s\S]{1,200}/g) || [];
      chunks.push(...segments.map(text => ({text, lang})));
    }
    const missingLanguage = chunks.find(chunk => !compatibleVoices(chunk.lang).length)?.lang;
    if (missingLanguage) {
      stop(false);
      noVoice(missingLanguage);
      return;
    }
    const token=generation;
    function next() {
      if(token!==generation)return;
      const chunk=chunks.shift();if(!chunk){active=false;status('Reading finished.');return;}
      const utterance = new SpeechSynthesisUtterance(chunk.text);
      const voices = compatibleVoices(chunk.lang);
      if (!voices.length) { stop(false); noVoice(chunk.lang); return; }
      const voice = voices.find(voice => voice.voiceURI === audio.voice)
        || voices.find(voice => /^(es-(mx|us)|en-us)$/i.test(voice.lang))
        || voices.find(voice => voice.default) || voices[0];
      utterance.voice = voice;
      utterance.lang = voice.lang;
      utterance.rate=audio.rate;utterance.pitch=audio.pitch;utterance.volume=audio.volume;
      utterance.onend=next;
      utterance.onerror=event=>{if(token!==generation)return;active=false;chunks=[];status(event.error==='canceled' || event.error==='interrupted'?'Speech stopped.':'The selected voice could not play. Try another available voice.');};
      synth.speak(utterance);
    }
    status('Reading.');next();
  }
  function readableParts(root, range) {
    if (!root) return [];
    const parts = [];
    function collect(node) {
      const isText = node.nodeType === Node.TEXT_NODE;
      const element = isText ? node.parentElement : node;
      if (!element || element.closest('input,textarea,select,script,style,[hidden],[aria-hidden="true"]')) return;
      if (element.closest('.pnec-reading-tools') || !element.getClientRects().length
          || ['hidden', 'collapse'].includes(getComputedStyle(element).visibility)) return;
      if (range && !range.intersectsNode(node)) return;
      let text;
      if (isText) {
        const start = range?.startContainer === node ? range.startOffset : 0;
        const end = range?.endContainer === node ? range.endOffset : node.length;
        text = node.textContent.slice(start, end).trim();
      } else if (!range && element.matches('img[alt], [role="img"][aria-label]')) {
        text = (element.getAttribute('alt') || element.getAttribute('aria-label') || '').trim();
      }
      if (!text) return;
      const lang = languageOf(element);
      const previous = parts.at(-1);
      if (previous?.lang === lang) previous.text += ' ' + text;
      else parts.push({text, lang});
    }
    if (root.nodeType === Node.TEXT_NODE) collect(root);
    else {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
      while (walker.nextNode()) collect(walker.currentNode);
    }
    return parts;
  }
  const samples = {
    en: 'Neighbors helping neighbors through preparedness, response, and recovery.',
    es: 'Los vecinos se ayudan a prepararse, responder y recuperarse ante emergencias.'
  };
  function syncSample() {
    const sample = document.getElementById('speech-test-text');
    if (!sample) return;
    if (Object.values(samples).includes(sample.value)) sample.value = samples[preferences.get().language];
    sample.lang = preferences.get().language;
  }
  function syncForm() {
    const form=document.getElementById('pnec-audio-form');if(!form)return;
    const audio=settings();
    form.elements.enabled.checked=audio.enabled;
    ['voice','rate','pitch','volume'].forEach(name=>{form.elements[name].value=audio[name];});
    ['rate','pitch','volume'].forEach(name=>{const input=form.elements[name];document.getElementById(`speech-${name}-value`).textContent=name==='volume'?Math.round(input.value*100)+'%':input.value+(name==='rate'?'×':'');});
  }
  document.addEventListener('selectionchange',()=>{
    const selection=window.getSelection();
    if (selection?.rangeCount && selection.toString().trim() && !selection.anchorNode?.parentElement?.closest('[contenteditable="true"]')) {
      const range = selection.getRangeAt(0);
      selectedRange = range.cloneRange();
    }
    // Retain an explicit selection while the user opens the mobile reading controls.
  });
  document.addEventListener('DOMContentLoaded',()=>{
    updateButtons();syncForm();syncSample();availableVoices();
    if(!supported)status('Text-to-speech is unavailable in this browser. You can still use your screen reader.');
    else synth.addEventListener('voiceschanged',availableVoices);
    document.querySelectorAll('[data-speech]').forEach(button=>{
      button.addEventListener('mousedown',event=>{if(button.dataset.speech==='read')event.preventDefault();});
      button.addEventListener('click',()=>{
        if(button.dataset.speech==='stop')stop();
        else if(button.dataset.speech==='pause'){
          if(!active){status('No speech is playing.');return;}
          if(synth.paused){synth.resume();pauseState(false);status('Reading.');}else{synth.pause();pauseState(true);status('Speech paused. Activate Pause speech again to resume.');}
        } else if (button.dataset.speech === 'test') {
          const sample = document.getElementById('speech-test-text');
          speak([{text: sample.value.trim(), lang: sample.lang}].filter(part => part.text), formSettings());
        } else if (button.dataset.speech === 'page') speak(readableParts(document.querySelector('main')));
        else {
          if (selectedRange) speak(readableParts(selectedRange.commonAncestorContainer, selectedRange));
          else speak([]);
          selectedRange = null;
        }
      });
    });
    const form=document.getElementById('pnec-audio-form');if(!form)return;
    form.addEventListener('input',()=>{
      ['rate','pitch','volume'].forEach(name=>{const input=form.elements[name];document.getElementById(`speech-${name}-value`).textContent=name==='volume'?Math.round(input.value*100)+'%':input.value+(name==='rate'?'×':'');});
    });
    form.addEventListener('change',()=>{preferences.update({audio:formSettings()},'audio-status');});
    form.addEventListener('submit',event=>{event.preventDefault();preferences.update({audio:formSettings()},'audio-status');});
    form.addEventListener('reset',event=>{event.preventDefault();stop();preferences.update({audio:{enabled:false,voice:'',rate:1,pitch:1,volume:1}},'audio-status');syncForm();});
  });
  window.addEventListener('pnec:appearance-changed',()=>{updateButtons();syncSample();});
  window.addEventListener('pnec:language-changed',()=>{selectedRange=null;if(active)stop(false);availableVoices();});
  window.addEventListener('pagehide',()=>stop(false));
})();
