import { register, login } from '../auth.js';

let mode = 'login'; // login or register

export function renderAuth(container) {
  container.innerHTML = `
    <section class="page auth-page">
      <div class="auth-card">
        <div class="auth-header">
          <div class="nav-logo-icon">🌾</div>
          <h1>AGRIFY</h1>
          <p class="auth-subtitle">Premium AgriTech Platform</p>
        </div>
        <div class="auth-tabs">
          <button class="auth-tab ${mode === 'login' ? 'active' : ''}" data-mode="login">Login</button>
          <button class="auth-tab ${mode === 'register' ? 'active' : ''}" data-mode="register">Register</button>
        </div>
        <form id="auth-form" class="auth-form" novalidate>
          <div id="auth-error" class="auth-error" style="display:none"></div>
          ${mode === 'register' ? `
            <div class="form-group">
              <label for="full_name">Full Name</label>
              <input id="full_name" name="full_name" type="text" required autocomplete="name" />
            </div>
          ` : ''}
          <div class="form-group">
            <label for="email">Email (optional)</label>
            <input id="email" name="email" type="email" autocomplete="email" />
          </div>
          <div class="form-group">
            <label for="phone">Phone (optional)</label>
            <input id="phone" name="phone" type="tel" autocomplete="tel" />
          </div>
          <div class="form-group">
            <label for="password">Password</label>
            <input id="password" name="password" type="password" required minlength="6" autocomplete="${mode === 'login' ? 'current-password' : 'new-password'}" />
          </div>
          <button class="auth-submit" type="submit">${mode === 'login' ? 'Login' : 'Create Account'}</button>
        </form>
      </div>
    </section>
  `;

  container.querySelectorAll('.auth-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      mode = btn.dataset.mode;
      renderAuth(container);
    });
  });

  const form = container.querySelector('#auth-form');
  const errorEl = container.querySelector('#auth-error');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorEl.style.display = 'none';
    const fd = new FormData(form);
    const full_name = fd.get('full_name') || '';
    const email = fd.get('email') || '';
    const phone = fd.get('phone') || '';
    const password = fd.get('password') || '';

    if (mode === 'register' && !email && !phone) {
      errorEl.textContent = 'Email or phone required';
      errorEl.style.display = 'block';
      return;
    }
    if (password.length < 6) {
      errorEl.textContent = 'Password must be at least 6 characters';
      errorEl.style.display = 'block';
      return;
    }

    try {
      if (mode === 'login') {
        await login(email || null, phone || null, password);
      } else {
        await register(full_name, email || null, phone || null, password);
      }
      window.dispatchEvent(new CustomEvent('authChange'));
      window.dispatchEvent(new CustomEvent('navigate', { detail: 'home' }));
    } catch (err) {
      errorEl.textContent = err.message || 'Authentication failed';
      errorEl.style.display = 'block';
    }
  });
}

export function initAuth() {}
