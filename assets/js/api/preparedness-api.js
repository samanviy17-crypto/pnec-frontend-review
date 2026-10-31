// Shared fetch worker: use the existing API host and account token.
window.pnecCommunityRequest = async function(path, method = 'GET', data) {
  return pnecJsonRequest(`${API_BASE}/api${path}`, {
    method, credentials: 'include', headers: _getAuthHeaders(),
    ...(data === undefined ? {} : {body: JSON.stringify(data)})
  });
};
