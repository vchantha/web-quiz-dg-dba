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
  const type = (response.headers.get('content-type') || '').toLowerCase();
  if (!type.includes('application/json')) {
    const reason = response.status === 400
      ? 'Check DJANGO_ALLOWED_HOSTS or QUIZ_ALLOW_IP_HOSTS for your server address.'
      : response.status === 403
      ? 'Check CSRF configuration, reverse-proxy Host forwarding, and the browser URL.'
      : response.status === 502 || response.status === 503
      ? 'The backend service is unavailable; check Docker logs.'
      : 'Verify that Nginx routes /api/ to Django.';
    throw new Error('API returned HTTP ' + response.status + ' instead of JSON. ' + reason);
  }
  let data;
  try { data = await response.json(); }
  catch { throw new Error('API returned invalid JSON (HTTP ' + response.status + '). Check backend logs.'); }
  if (!response.ok) {
    const error = new Error(data.error || 'Request failed.');
    error.status = response.status;
    throw error;
  }
  return data;
}
