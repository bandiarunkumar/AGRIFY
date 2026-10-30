const API_BASE = window.API_BASE || '';

function getUser() {
  try {
    return JSON.parse(localStorage.getItem('agrify_user') || 'null');
  } catch {
    return null;
  }
}

function setUser(user) {
  if (user) localStorage.setItem('agrify_user', JSON.stringify(user));
  else localStorage.removeItem('agrify_user');
}

export async function register(full_name, email, phone, password) {
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ full_name, email: email || null, phone: phone || null, password })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Registration failed');
  setUser(data.user);
  return data;
}

export async function login(email, phone, password) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: email || null, phone: phone || null, password })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Login failed');
  setUser(data.user);
  return data;
}

export async function logout() {
  try {
    await fetch(`${API_BASE}/api/auth/logout`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' }
    });
  } catch {}
  setUser(null);
}

export async function me() {
  try {
    const res = await fetch(`${API_BASE}/api/auth/me`, {
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!res.ok) { setUser(null); return null; }
    const data = await res.json();
    setUser(data.user);
    return data.user;
  } catch {
    setUser(null);
    return null;
  }
}

export { getUser, setUser };
