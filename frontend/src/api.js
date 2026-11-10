function cookie(name) {
  const item = document.cookie.split('; ').find(c => c.startsWith(name + '='));
  return item ? decodeURIComponent(item.slice(name.length + 1)) : '';
}

export async function api(path, { method = 'GET', body, ...options } = {}) {
  const headers = { ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}), ...options.headers };
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method.toUpperCase())) {
    headers['X-CSRFToken'] = cookie('csrftoken');
  }
  const response = await fetch('/api' + path, {
    method, credentials: 'same-origin', headers,
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    ...options
  });
  let data;
  try { data = await response.json(); }
  catch { throw new Error('Unexpected server response. Please retry.'); }
  if (!response.ok) {
    const error = new Error(data.error || 'Request failed.');
    error.status = response.status;
    throw error;
  }
  return data;
}
