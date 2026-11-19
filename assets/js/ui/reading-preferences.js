// Browser speech synthesis only. No microphone, autoplay, server audio or account data.
(() => {
  const preferences = window.PNECPreferences;
  if (!preferences) return;
  const supported = typeof window.speechSynthesis?.speak === 'function' && typeof window.SpeechSynthesisUtterance === 'function';
  const synth = supported ? window.speechSynthesis : null;
  let selectedText = '', chunks = [], active = false, generation = 0;
  function status(message) {const nodes=[...document.querySelectorAll('.pnec-speech-status')]; const target=document.querySelector('#pnec-audio-form .pnec-speech-status') || nodes[0]; nodes.forEach(node=>{node.textContent=node===target?message:'';});}
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
    select.replaceChildren(new Option('Browser default voice',''));
    synth.getVoices().forEach(voice=>{select.add(new Option(`${voice.name} (${voice.lang})`,voice.voiceURI));});
    if ([...select.options].some(option=>option.value===value))select.value=value;
    if(!synth.getVoices().length)status('No installed voices reported yet. The browser default may be available; try Test Voice.');
    else if(!active)status(`${synth.getVoices().length} browser voices available. Audio starts only when requested.`);
  }
  function formSettings() {
    const form=document.getElementById('pnec-audio-form');
    return form?{enabled:form.elements.enabled.checked,voice:form.elements.voice.value,rate:+form.elements.rate.value,pitch:+form.elements.pitch.value,volume:+form.elements.volume.value}:settings();
  }
  function speak(text, audio=settings()) {
    if(!supported) {status('Text-to-speech is unavailable in this browser.');return;}
    if(!audio.enabled) {status('Enable text-to-speech in Preferences first.');return;}
    text=text.trim().slice(0,20000);
    if(!text){status('Select text or open a page with readable content.');return;}
    stop(false);active=true;
    // Short chunks avoid long-utterance limits in some speech engines.
    chunks=text.match(/[\s\S]{1,200}(?:\s|$)|[\s\S]{1,200}/g) || [text];
    const token=generation;
    function next() {
      if(token!==generation)return;
      const chunk=chunks.shift();if(!chunk){active=false;status('Reading finished.');return;}
      const utterance=new SpeechSynthesisUtterance(chunk);
      const voice=synth.getVoices().find(v=>v.voiceURI===audio.voice);
      if(voice){utterance.voice=voice;utterance.lang=voice.lang;}else utterance.lang=document.documentElement.lang || 'en';
      utterance.rate=audio.rate;utterance.pitch=audio.pitch;utterance.volume=audio.volume;
      utterance.onend=next;
      utterance.onerror=event=>{if(token!==generation)return;active=false;chunks=[];status(event.error==='canceled' || event.error==='interrupted'?'Speech stopped.':'The selected voice could not play. Try another available voice.');};
      synth.speak(utterance);
    }
    status('Reading.');next();
  }
  function mainText() {
    const main=document.querySelector('main');if(!main)return '';
    const walker=document.createTreeWalker(main,NodeFilter.SHOW_TEXT,{acceptNode(node){
      const parent=node.parentElement;
      if(!parent || parent.closest('form,input,textarea,select,button,script,style,[hidden],[aria-hidden="true"],.pnec-speech-status'))return NodeFilter.FILTER_REJECT;
      return parent.getClientRects().length && node.textContent.trim()?NodeFilter.FILTER_ACCEPT:NodeFilter.FILTER_REJECT;
    }});
    const text=[];while(walker.nextNode())text.push(walker.currentNode.textContent.trim());return text.join(' ');
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
    if(selection?.toString().trim() && !selection.anchorNode?.parentElement?.closest('input,textarea,[contenteditable="true"]'))selectedText=selection.toString();
    // Retain an explicit selection while the user opens the mobile reading controls.
  });
  document.addEventListener('DOMContentLoaded',()=>{
    updateButtons();syncForm();availableVoices();
    if(!supported)status('Text-to-speech is unavailable in this browser. You can still use your screen reader.');
    else synth.addEventListener('voiceschanged',availableVoices);
    document.querySelectorAll('[data-speech]').forEach(button=>{
      button.addEventListener('mousedown',event=>{if(button.dataset.speech==='read')event.preventDefault();});
      button.addEventListener('click',()=>{
        if(button.dataset.speech==='stop')stop();
        else if(button.dataset.speech==='pause'){
          if(!active){status('No speech is playing.');return;}
          if(synth.paused){synth.resume();pauseState(false);status('Reading.');}else{synth.pause();pauseState(true);status('Speech paused. Activate Pause speech again to resume.');}
        }else if(button.dataset.speech==='test')speak(document.getElementById('speech-test-text').value,formSettings());
        else if(button.dataset.speech==='page')speak(mainText());
        else {speak(selectedText);selectedText='';}
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
  window.addEventListener('pnec:appearance-changed',()=>{updateButtons();});
  window.addEventListener('pagehide',()=>stop(false));
})();
