import test from 'node:test';
import assert from 'node:assert/strict';

test('Helper Bot selects a compatible voice for each reply', async () => {
  const replies = [];
  const voices = [{lang: 'en-US'}, {lang: 'es-MX'}];
  globalThis.window = {
    speechSynthesis: {
      getVoices: () => voices,
      cancel() {},
      speak: reply => replies.push(reply),
    },
  };
  globalThis.SpeechSynthesisUtterance = class {
    constructor(text) { this.text = text; }
  };

  const {speak} = await import('./voice.js');
  speak('Listo para empezar.', 'es-US');
  speak('Ready to start.');
  voices.push({lang: 'es_US'});
  speak('Bienvenidos.', 'es-US');
  speak('Welcome back.', 'en-US');
  voices.splice(1);
  assert.equal(speak('Hola.', 'es-US'), false);
  assert.equal(speak('Handa nang magsimula.', 'fil-PH'), false);

  assert.deepEqual(replies.map(reply => [reply.lang, reply.voice?.lang]), [
    ['es-MX', 'es-MX'],
    ['en-US', 'en-US'],
    ['es-US', 'es_US'],
    ['en-US', 'en-US'],
  ]);
});
