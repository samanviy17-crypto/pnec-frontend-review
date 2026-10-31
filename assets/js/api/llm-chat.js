/**
 * Shared text-generation helper for page-level chatbots.
 * Supports Gemini and Grok using a normalized request interface.
 */

function normalizeProvider(provider) {
  return String(provider || 'gemini').trim().toLowerCase();
}

function extractGeminiText(data) {
  return data?.candidates?.[0]?.content?.parts
    ?.map(part => part?.text || '')
    .join('')
    .trim();
}

function extractGeminiProxyText(data) {
  if (typeof data?.text === 'string') return data.text.trim();
  if (typeof data?.response === 'string') return data.response.trim();
  return '';
}

async function requestGeminiProxy({ endpoint, systemPrompt, userMessage, history = [], fetchOptions = {} }) {
  const response = await fetch(endpoint, {
    ...fetchOptions,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(fetchOptions.headers || {})
    },
    body: JSON.stringify({
      prompt: systemPrompt,
      text: userMessage,
      history
    })
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const details = data?.detail || data?.message || data?.error || `Gemini proxy request failed with ${response.status}`;
    throw new Error(details);
  }

  const text = extractGeminiProxyText(data);
  if (!text) throw new Error('Gemini proxy returned an empty response');
  return text;
}

export async function sendChatCompletion(options) {
  if (!options?.systemPrompt || !options?.userMessage) throw new Error('Missing chat message');
  if (!options?.endpoint) throw new Error('Configure the PNEC backend chat endpoint; browser service keys are prohibited.');
  return requestGeminiProxy(options);
}
