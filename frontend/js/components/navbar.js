// ============================================================
// Navbar Component — Language toggle, GPS status
// ============================================================

import { t, getLang } from '../i18n.js';

let currentLang = 'en';

export function renderNavbar(activePage, routes) {
  const navEl = document.getElementById('navbar');
  if (!navEl) return;

  currentLang = getLang();
  navEl.setAttribute('aria-label', currentLang === 'te' ? 'ప్రధాన నావిగేషన్' : 'Main navigation');

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
      <button class="nav-link ${activePage === key ? 'active' : ''}" data-navigate="${key}" id="nav-${key}" type="button" aria-current="${activePage === key ? 'page' : 'false'}" aria-label="${labelMap[key] || r.label}" title="${labelMap[key] || r.label}">
        ${r.icon} <span class="hide-mobile">${labelMap[key] || r.label}</span>
      </button>
    `).join('');

  navEl.innerHTML = `
    <div class="nav-inner">
      <button class="nav-logo" data-navigate="home" type="button" title="AGRIFY Home" aria-label="AGRIFY Home">
        <div class="nav-logo-icon">🌾</div>
        <div class="nav-logo-text-group">
          <div class="nav-logo-text">AGRI<span>FY</span></div>
          <span class="nav-logo-tag">AI</span>
        </div>
      </button>
      <div class="nav-links" aria-label="${currentLang === 'te' ? 'ప్రధాన నావిగేషన్' : 'Main navigation'}">
        ${navLinks}
        <button class="nav-lang-btn" id="nav-lang-btn" type="button" title="${currentLang === 'te' ? 'భాష మార్చండి' : 'Switch language'}" aria-label="${currentLang === 'te' ? 'Switch language to English' : 'భాషను తెలుగుకు మార్చండి'}">
          ${currentLang === 'en' ? 'తె' : 'EN'}
        </button>
        <label class="theme-control" for="nav-theme-select">
          <span aria-hidden="true">◐</span>
          <span class="sr-only">${currentLang === 'te' ? 'రంగు థీమ్' : 'Color theme'}</span>
          <select id="nav-theme-select" aria-label="${currentLang === 'te' ? 'రంగు థీమ్ ఎంచుకోండి' : 'Choose color theme'}">
            <option value="system">${currentLang === 'te' ? 'సిస్టమ్' : 'System'}</option>
            <option value="light">${currentLang === 'te' ? 'లైట్' : 'Light'}</option>
            <option value="dark">${currentLang === 'te' ? 'డార్క్' : 'Dark'}</option>
          </select>
        </label>
        <button class="nav-auth-btn" id="nav-auth-btn" type="button">${(localStorage.getItem('agrify_user') ? JSON.parse(localStorage.getItem('agrify_user')).full_name.split(' ')[0] : (currentLang === 'te' ? 'లాగిన్' : 'Login'))}</button>
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

  navEl.querySelector('#nav-auth-btn')?.addEventListener('click', () => {
    const user = JSON.parse(localStorage.getItem('agrify_user') || 'null');
    if (user) {
      import('../auth.js').then(m => m.logout()).then(() => {
        window.dispatchEvent(new CustomEvent('authChange'));
        window.dispatchEvent(new CustomEvent('navigate', { detail: 'home' }));
        renderNavbar(activePage, routes);
      });
    } else {
      window.dispatchEvent(new CustomEvent('navigate', { detail: 'auth' }));
    }
  });

  window.addEventListener('authChange', () => {
    renderNavbar(activePage, routes);
  });

  const themeSelect = navEl.querySelector('#nav-theme-select');
  if (themeSelect) {
    themeSelect.value = document.documentElement.dataset.themePreference || 'system';
    themeSelect.addEventListener('change', () => {
      window.dispatchEvent(new CustomEvent('themeChange', { detail: themeSelect.value }));
    });
  }
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
  mobileNavEl.setAttribute('aria-label', getLang() === 'te' ? 'మొబైల్ పేజీ నావిగేషన్' : 'Mobile page navigation');

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

  const visiblePages = ['home', 'analysis', 'weather', 'market', 'cropDoctor', 'chatbot', 'alerts', 'experts'];
  mobileNavEl.innerHTML = visiblePages.map(key => {
    const r = routes[key];
    if (!r) return '';
    return `
      <button class="mobile-nav-item ${activePage === key ? 'active' : ''}" data-navigate="${key}" type="button" aria-current="${activePage === key ? 'page' : 'false'}" aria-label="${labelMap[key] || r.label}">
        <span class="mn-icon">${r.icon}</span>
        <span class="mn-label">${labelMap[key] || r.label}</span>
      </button>
    `;
  }).join('');

  mobileNavEl.querySelectorAll('[data-navigate]').forEach(el => {
    el.addEventListener('click', () => {
      window.dispatchEvent(new CustomEvent('navigate', { detail: el.dataset.navigate }));
    });
  });
}
