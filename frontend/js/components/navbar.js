// ============================================================
// Navbar Component — Language toggle, GPS status
// ============================================================

import { t, getLang } from '../i18n.js';

let currentLang = 'en';

export function renderNavbar(activePage, routes) {
  const navEl = document.getElementById('navbar');
  if (!navEl) return;

  currentLang = getLang();

  // Use i18n for labels
  const labelMap = {
    home: t('nav_home'),
    analysis: t('nav_analyzer'),
    weather: t('nav_weather'),
    market: t('nav_market'),
    cropDoctor: t('nav_cropDoctor'),
    chatbot: t('nav_chatbot'),
    alerts: t('nav_alerts'),
    experts: t('nav_experts'),
  };

  const navLinks = Object.entries(routes)
    .filter(([key]) => ['home', 'analysis', 'weather', 'market', 'cropDoctor', 'chatbot', 'alerts', 'experts'].includes(key))
    .map(([key, r]) => `
      <button class="nav-link ${activePage === key ? 'active' : ''}" data-navigate="${key}" id="nav-${key}">
        ${r.icon} <span class="hide-mobile">${labelMap[key] || r.label}</span>
      </button>
    `).join('');

  navEl.innerHTML = `
    <div class="nav-inner">
      <div class="nav-logo" data-navigate="home">
        <div class="nav-logo-icon">🌾</div>
        <div class="nav-logo-text">Agri<span>Connect</span></div>
      </div>
      <div class="nav-links">
        ${navLinks}
        <button class="nav-lang-btn" id="nav-lang-btn">
          ${currentLang === 'en' ? '🇮🇳 తె' : '🇺🇸 EN'}
        </button>
      </div>
    </div>
  `;

  // Attach nav events
  navEl.querySelectorAll('[data-navigate]').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      window.dispatchEvent(new CustomEvent('navigate', { detail: el.dataset.navigate }));
    });
  });

  navEl.querySelector('#nav-lang-btn')?.addEventListener('click', () => {
    currentLang = currentLang === 'en' ? 'te' : 'en';
    window.dispatchEvent(new CustomEvent('langChange', { detail: currentLang }));
    renderNavbar(activePage, routes);
  });
}

// Mobile bottom nav
export function renderMobileNav(activePage, routes) {
  let mobileNavEl = document.getElementById('mobile-nav');
  if (!mobileNavEl) {
    mobileNavEl = document.createElement('nav');
    mobileNavEl.id = 'mobile-nav';
    mobileNavEl.className = 'mobile-nav';
    document.body.appendChild(mobileNavEl);
  }

  const visiblePages = ['home', 'analysis', 'weather', 'market', 'alerts'];
  mobileNavEl.innerHTML = visiblePages.map(key => {
    const r = routes[key];
    if (!r) return '';
    return `
      <button class="mobile-nav-item ${activePage === key ? 'active' : ''}" data-navigate="${key}">
        <span class="mn-icon">${r.icon}</span>
        ${r.label}
      </button>
    `;
  }).join('');

  mobileNavEl.querySelectorAll('[data-navigate]').forEach(el => {
    el.addEventListener('click', () => {
      window.dispatchEvent(new CustomEvent('navigate', { detail: el.dataset.navigate }));
    });
  });
}
