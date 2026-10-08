// ============================================================
// Agri-Connect v3.0 — Main Application Router
// ============================================================

import '../css/style.css';
import { renderNavbar } from './components/navbar.js';
import { renderFooter } from './components/footer.js';
import { renderHome, initHome } from './pages/home.js';
import { renderWeather, initWeather } from './pages/weather.js';
import { renderMarket, initMarket } from './pages/market.js';
import { renderAnalysis, initAnalysis } from './pages/analysis.js';
import { renderCropDoctor, initCropDoctor } from './pages/cropDoctor.js';
import { renderChatbot, initChatbot } from './pages/chatbot.js';
import { renderAlerts, initAlerts } from './pages/alerts.js';
import { renderExperts, initExperts } from './pages/experts.js';
import { initVoice } from './voice.js';
import { onLangChange } from './i18n.js';

// ============================================================
// ROUTES
// ============================================================
const routes = {
  home:      { render: renderHome,      init: initHome,     label: 'Home',     icon: '🏠' },
  analysis:  { render: renderAnalysis,  init: initAnalysis, label: 'Analyzer', icon: '🌱' },
  weather:   { render: renderWeather,   init: initWeather,  label: 'Weather',  icon: '🌤️' },
  market:    { render: renderMarket,    init: initMarket,   label: 'Market',   icon: '📊' },
  cropDoctor:{ render: renderCropDoctor,init: initCropDoctor,label: 'Crop Doctor',icon: '🔬' },
  chatbot:   { render: renderChatbot,   init: initChatbot,  label: 'Chatbot',  icon: '💬' },
  alerts:    { render: renderAlerts,    init: initAlerts,   label: 'Alerts',   icon: '🚨' },
  experts:   { render: renderExperts,   init: initExperts,  label: 'Experts',  icon: '👨‍🌾' },
};

let currentPage = 'home';

// ============================================================
// NAVIGATE
// ============================================================
function navigateTo(page) {
  const route = routes[page];
  if (!route) return;

  currentPage = page;
  renderNavbar(page, routes);

  const app = document.getElementById('app');
  app.innerHTML = route.render();

  if (route.init) route.init();

  // Attach navigation listeners in page content
  app.querySelectorAll('[data-navigate]').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      navigateTo(el.dataset.navigate);
    });
  });

  // Voice FAB only on analysis pages
  const fab = document.getElementById('voice-fab');
  if (fab) {
    fab.classList.toggle('hidden', page === 'home');
  }

  // Re-render footer to update language
  renderFooter();

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================================
// INIT
// ============================================================
function init() {
  // Spawn global floating flower petals (persists across all pages)
  spawnGlobalFlowerPetals();

  renderFooter();
  initVoice();

  window.addEventListener('navigate', e => navigateTo(e.detail));

  onLangChange(() => navigateTo(currentPage));

  // Handle URL hash for deep-linking
  const hash = window.location.hash.replace('#', '');
  navigateTo(routes[hash] ? hash : 'home');

  window.addEventListener('hashchange', () => {
    const h = window.location.hash.replace('#', '');
    if (routes[h]) navigateTo(h);
  });
}

// ============================================================
// GLOBAL FLOATING FLOWER PETALS — Always visible on all pages
// ============================================================
function spawnGlobalFlowerPetals() {
  // Don't duplicate if already spawned
  if (document.getElementById('global-petals')) return;

  const container = document.createElement('div');
  container.id = 'global-petals';
  container.className = 'flower-petals-container';
  document.body.appendChild(container);

  const petals = ['🌸', '🌺', '🌻', '🌼', '🌷', '🍃', '🌿', '☘️', '🍂', '🌾'];
  const count = 30;

  for (let i = 0; i < count; i++) {
    const petal = document.createElement('div');
    petal.className = 'floating-petal';
    petal.textContent = petals[Math.floor(Math.random() * petals.length)];
    petal.style.left = `${Math.random() * 100}%`;
    petal.style.setProperty('--fall-duration', `${14 + Math.random() * 20}s`);
    petal.style.setProperty('--fall-delay', `${Math.random() * 18}s`);
    petal.style.setProperty('--drift-x', `${-60 + Math.random() * 120}px`);
    petal.style.setProperty('--petal-size', `${0.9 + Math.random() * 1.1}rem`);
    petal.style.setProperty('--petal-opacity', `${0.18 + Math.random() * 0.22}`);
    petal.style.setProperty('--spin', `${Math.random() > 0.5 ? '' : '-'}${400 + Math.random() * 400}deg`);
    petal.style.fontSize = `var(--petal-size)`;
    container.appendChild(petal);
  }
}

document.addEventListener('DOMContentLoaded', init);

