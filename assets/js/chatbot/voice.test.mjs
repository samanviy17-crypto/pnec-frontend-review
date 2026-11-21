import test from 'node:test';
import assert from 'node:assert/strict';

test('Helper Bot selects a compatible voice for each reply', async () => {
  const replies = [];
  globalThis.window = {
    speechSynthesis: {
      getVoices: () => [{lang: 'en-US'}, {lang: 'es-MX'}],
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
  assert.equal(speak('Handa nang magsimula.', 'fil-PH'), false);

  assert.deepEqual(replies.map(reply => [reply.lang, reply.voice?.lang]), [
    ['es-MX', 'es-MX'],
    ['en-US', 'en-US'],
  ]);
});
