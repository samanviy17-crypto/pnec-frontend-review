// Test-only preload: no service or production network requests.
globalThis.fetch = () => Promise.reject(new Error('Network disabled in snapshot unit tests'));
