// assets/js/chatbot/voice.js
// PNEC Helper Bot v3 — Phase 3 voice in/out.
//
// Web Speech API: recognition (mic → text) and synthesis (text → audio).
// Both are best-effort: Safari iOS recognition is gated, some Linux
// browsers have no synthesis voices, etc. When unavailable we surface
// a friendly status message and the rest of the bot keeps working.
//
// Design choices:
//   • Push-to-toggle: tapping the mic starts listening; tapping again
//     stops. Auto-stops after 8s of silence.
//   • Live partial transcript flows into the composer textarea so the
//     user can see what was heard before sending.
//   • Long-press on the mic is reserved for Phase 4 (continuous mode).
//   • Speech synthesis is opt-in via Settings → "Voice replies".

const SR = window.SpeechRecognition || window.webkitSpeechRecognition || null;
const SS = window.speechSynthesis || null;

let recognizer = null;
let isListening = false;
let listenStopTimer = null;
let interimText = '';

export function isAvailable() {
  return !!SR;
}
export function isSpeakAvailable() {
  return !!SS;
}

function normalizeTag(tag) {
  return tag.replace(/_/g, '-').toLowerCase();
}

function pickVoice(lang) {
  const tag = normalizeTag(lang);
  const language = tag.split('-')[0];
  const voices = SS.getVoices().filter(voice => normalizeTag(voice.lang).split('-')[0] === language);
  const exact = voices.filter(voice => normalizeTag(voice.lang) === tag);
  return exact.find(voice => voice.default) || exact[0]
    || (language === 'es' && voices.find(voice => /^es-(mx|us)$/.test(normalizeTag(voice.lang))))
    || voices.find(voice => voice.default) || voices[0];
}

// ─── Public hooks called from index.js ────────────────────────────

export function attach(_bot) {
  // Nothing to wire on attach — the controller already wired the mic
  // button. We just make sure the API is reachable.
  if (!isAvailable()) return;
}

export function toggleListen(bot) {
  if (!isAvailable()) {
    bot._setStatus('idle', "Voice input isn't available in this browser");
    setTimeout(() => bot._setStatus('idle', 'PNEC · ready'), 2200);
    return;
  }
  if (isListening) { stopListen(bot); return; }
  startListen(bot);
}

function startListen(bot) {
  try {
    recognizer = new SR();
    recognizer.lang = (bot && bot.i18n && bot.i18n.langTag) ? bot.i18n.langTag() : 'en-US';
    recognizer.continuous = false;
    recognizer.interimResults = true;

    interimText = bot.dom.input.value || '';
    isListening = true;
    bot.dom.mic.classList.add('is-listening');
    bot.dom.mic.setAttribute('aria-pressed', 'true');
    bot._setStatus('streaming', 'Listening…');

    recognizer.onresult = (ev) => {
      let final = '';
      let interim = '';
      for (let i = ev.resultIndex; i < ev.results.length; i++) {
        const t = ev.results[i][0].transcript;
        if (ev.results[i].isFinal) final += t;
        else interim += t;
      }
      const composed = (interimText + (final ? ' ' + final.trim() : '') + (interim ? ' ' + interim : '')).trim();
      bot.dom.input.value = composed;
      bot._onInputChange();
      // Auto-stop after 1.6s with no interim/final updates
      clearTimeout(listenStopTimer);
      listenStopTimer = setTimeout(() => stopListen(bot, /*autoSubmit*/ true), 1600);
    };

    recognizer.onerror = () => stopListen(bot);
    recognizer.onend = () => {
      if (isListening) stopListen(bot);
    };
    recognizer.start();
  } catch (_e) {
    isListening = false;
    bot.dom.mic.classList.remove('is-listening');
    bot.dom.mic.setAttribute('aria-pressed', 'false');
    bot._setStatus('idle', 'PNEC · ready');
  }
}

function stopListen(bot, autoSubmit = false) {
  if (recognizer) {
    try { recognizer.stop(); } catch (_e) {}
    recognizer = null;
  }
  isListening = false;
  clearTimeout(listenStopTimer);
  bot.dom.mic.classList.remove('is-listening');
  bot.dom.mic.setAttribute('aria-pressed', 'false');
  bot._setStatus('idle', 'PNEC · ready');
  if (autoSubmit && (bot.dom.input.value || '').trim()) {
    bot._submitInput();
  }
}

// Speak an assistant response
let currentUtterance = null;
export function speak(text, lang = 'en-US') {
  if (!SS || !text) return false;
  // Stop any in-flight utterance
  try { SS.cancel(); } catch (_e) {}
  // Strip markdown that doesn't read aloud well
  const clean = String(text)
    .replace(/```[\s\S]*?```/g, '. code block. ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/\[FAQ#\d+\]/g, '')
    .replace(/\[News:[^\]]+\]/g, '')
    .replace(/[*_#>]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  if (!clean) return false;
  const u = new SpeechSynthesisUtterance(clean);
  const v = pickVoice(lang);
  if (!v) return false;
  u.voice = v;
  u.lang = v.lang.replace(/_/g, '-');
  u.rate = 1.02;
  u.pitch = 1.0;
  u.volume = 1.0;
  currentUtterance = u;
  try { SS.speak(u); return true; } catch (_e) { return false; }
}

export function stopSpeaking() {
  if (!SS) return;
  try { SS.cancel(); } catch (_e) {}
  currentUtterance = null;
}
