// assets/js/api/auth-api.js
// Responsibility: Auth fetch workers — backend auth plus local user cache in page layer.

// AI-assisted reliability change (OpenAI Codex), not proof of personal Create authorship.
// Bound both fetch and body reading; never retry a write automatically because
// a lost response does not establish whether the server committed the write.
async function pnecJsonRequest(url, options = {}, timeoutMs = 15000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {...options, signal: controller.signal});
    let data;
    try { data = response.status === 204 ? null : await response.json(); }
    catch (error) {
      if (controller.signal.aborted) throw error;
      if (response.ok) throw new Error('Server returned an unreadable response. Please retry.');
      data = {};
    }
    if (!response.ok) {
      const type = classifyHttpError(response.status);
      const detail = data && (data.detail || data.message || data.error);
      const error = new Error(response.status === 401 ? getErrorMessage(type) :
        (typeof detail === 'string' ? detail : getErrorMessage(type)));
      error.status = response.status; error.type = type;
      throw error;
    }
    return data;
  } catch (error) {
    if (controller.signal.aborted) {
      const timeout = new Error('Request timed out. Keep your changes and retry when connected.');
      timeout.type = 'TIMEOUT'; throw timeout;
    }
    if (error instanceof TypeError) {
      const network = new Error(getErrorMessage(ERROR_TYPES.NETWORK_ERROR));
      network.type = ERROR_TYPES.NETWORK_ERROR; throw network;
    }
    throw error;
  } finally { clearTimeout(timer); }
}

function _getAuthHeaders() {
  var token = localStorage.getItem('pnec_token') || sessionStorage.getItem('pnec_token');
  var headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = 'Bearer ' + token;
  return headers;
}

function _storeAuthResult(data, remember = true) {
  const storage = remember ? localStorage : sessionStorage;
  const other = remember ? sessionStorage : localStorage;
  other.removeItem('pnec_token'); other.removeItem('pnec_user');
  if (data && data.token) storage.setItem('pnec_token', data.token);
  if (data && data.user) storage.setItem('pnec_user', JSON.stringify(data.user));
}
async function validateAuthResponse(response) {
  if (response.ok) return response;
  const data = await response.json().catch(() => ({}));
  const error = new Error(data.detail || data.message || getErrorMessage(classifyHttpError(response.status)));
  error.type = classifyHttpError(response.status); error.status = response.status;
  throw error;
}

function loginUser(email, password, remember) {
  return pnecJsonRequest(`${API_BASE}/api/auth/login`, {
    method: 'POST', credentials: 'include',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({email, password, remember}),
  }).then(data => { _storeAuthResult(data, remember); return data; });
}

function registerUser(userData) {
  return pnecJsonRequest(`${API_BASE}/api/auth/register`, {
    method: 'POST', credentials: 'include',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({display_name: userData.display_name, email: userData.email,
      password: userData.password, neighborhood_id: userData.neighborhood_id}),
  }).then(data => { _storeAuthResult(data); return data; });
}

function logoutUser() {
  return pnecJsonRequest(`${API_BASE}/api/auth/logout`, {
    method: 'POST', credentials: 'include', headers: _getAuthHeaders(),
  }).then(data => {
    // Keep credentials available for retry if the server cannot confirm logout.
    for (const storage of [localStorage, sessionStorage]) {
      storage.removeItem('pnec_token'); storage.removeItem('pnec_user');
      storage.removeItem('pnec_new_user');
    }
    return data;
  });
}

function fetchCurrentUser({strict = false} = {}) {
  return pnecJsonRequest(`${API_BASE}/api/auth/me`, {
    method: 'GET',
    credentials: 'include',
    headers: _getAuthHeaders(),
  })
    .then(function(data) { return data.user || null; })
    .catch(function(error) {
      if (strict && error.status !== 401) throw error;
      return null;
    });
}

function fetchNeighborhoodsForSelect() {
  return pnecJsonRequest(`${API_BASE}/api/neighborhoods`, {
    method: 'GET',
    credentials: 'include',
  })
    .then(data => data.neighborhoods || []);
}


async function requestPasswordReset(email) {
  return accountRecoveryRequest('/forgot-password', {email});
}
async function resetPassword(token, password) {
  return accountRecoveryRequest('/reset-password', {token, password});
}
function accountRecoveryRequest(path, payload) {
  return pnecJsonRequest(`${API_BASE}/api/auth${path}`, {
    method: 'POST', credentials: 'include', headers: {'Content-Type':'application/json'},
    body: JSON.stringify(payload),
  });
}
function safeAccountRedirect() {
  const fallback = (window.PNEC_SITE_BASE || '') + '/pages/profile.html';
  const next = new URLSearchParams(location.search).get('next');
  if (!next) return fallback;
  try {
    const target = new URL(next, location.origin);
    return target.origin === location.origin ? target.pathname + target.search + target.hash : fallback;
  } catch (_) { return fallback; }
}


function updateProfile(payload) {
  return pnecJsonRequest(`${API_BASE}/api/auth/profile`, {
    method: 'PATCH', credentials: 'include', headers: _getAuthHeaders(),
    body: JSON.stringify(payload),
  }).then(data => {
    const remember = localStorage.getItem('pnec_token') !== null;
    _storeAuthResult(data, remember);
    return data.user;
  });
}
