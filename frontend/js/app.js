// ============================================================
// AGRIFY v3.0 — Main Application Router
// ============================================================

import '../css/style.css';
import '../css/premium.css';
import { initTheme } from './theme.js';
import { renderNavbar, renderMobileNav } from './components/navbar.js';
import { renderFooter } from './components/footer.js';
import { renderHome, initHome } from './pages/home.js';
import { renderWeather, initWeather } from './pages/weather.js';
import { renderMarket, initMarket } from './pages/market.js';
import { renderAnalysis, initAnalysis } from './pages/analysis.js';
import { renderCropDoctor, initCropDoctor } from './pages/cropDoctor.js';
import { renderChatbot, initChatbot } from './pages/chatbot.js';
import { renderAlerts, initAlerts } from './pages/alerts.js';
import { renderExperts, initExperts } from './pages/experts.js';
import { renderAuth, initAuth } from './pages/auth.js';
import { me, logout, getUser } from './auth.js';
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
  auth:     { render: renderAuth,     init: initAuth,     label: 'Account',  icon: '👤' },
};

let currentPage = 'home';
let homeCtaObserver = null;

// ============================================================
// NAVIGATE
// ============================================================
function navigateTo(page) {
  const route = routes[page];
  if (!route) return;

  homeCtaObserver?.disconnect();
  homeCtaObserver = null;

  currentPage = page;
  renderNavbar(page, routes);
  renderMobileNav(page, routes);

  const app = document.getElementById('app');
  app.innerHTML = route.render();

  // Keep route content visible immediately while adding a small, transform-only entrance.
  const pageRoot = app.firstElementChild;
  const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  if (pageRoot && !reduceMotion) pageRoot.classList.add('agrify-page-enter');

  // Stagger only the first few visual cards; never stage urgent alert content.
  if (!reduceMotion && page !== 'alerts') {
    const revealCards = app.querySelectorAll(
      '.card, .stat-card, .chart-container, .feature-card, .expert-card, .forecast-card, .crop-rec-card, .action-item-card, .timeline-step-card'
    );
    revealCards.forEach((card, index) => {
      if (index >= 5 || card.matches('.alerts-card-enhanced, .analysis-error-card, .wx-error-card, .cd-diagnosis-hero')) return;
      card.classList.add('agrify-card-reveal');
      card.style.setProperty('--agrify-reveal-delay', `${index * 38}ms`);
    });
  }

  if (route.init) route.init();

  // Attach navigation listeners in page content
  app.querySelectorAll('[data-navigate]').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      navigateTo(el.dataset.navigate);
    });

    if (!el.matches('a, button, input, select, textarea') && !el.hasAttribute('tabindex')) {
      el.tabIndex = 0;
      el.setAttribute('role', 'link');
      el.addEventListener('keydown', e => {
        if (e.key !== 'Enter') return;
        e.preventDefault();
        navigateTo(el.dataset.navigate);
      });
    }
  });

  // Global Voice Copilot FAB accessible across all pages (Home, Analysis, Weather, Market, Crop Doctor, Alerts, Experts)
  const fab = document.getElementById('voice-fab');
  if (fab) {
    fab.classList.remove('hidden');
    fab.classList.remove('home-cta-visible');
    if (page === 'home' && window.matchMedia('(max-width: 760px)').matches && window.IntersectionObserver) {
      const heroActions = app.querySelector('.hero-ctas');
      if (heroActions) {
        homeCtaObserver = new IntersectionObserver(([entry]) => {
          fab.classList.toggle('home-cta-visible', Boolean(entry?.isIntersecting));
        }, { threshold: 0.05 });
        homeCtaObserver.observe(heroActions);
      }
    }
  }

  // Re-render footer to update language
  renderFooter();

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================================
// INIT
// ============================================================
function init() {
  initTheme();
  syncVisibleViewportHeight();
  window.visualViewport?.addEventListener('resize', syncVisibleViewportHeight, { passive: true });
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

function syncVisibleViewportHeight() {
  const layoutHeight = window.innerHeight;
  const visibleHeight = window.visualViewport?.height || layoutHeight;
  const viewportGap = Math.max(0, layoutHeight - visibleHeight);
  document.documentElement.style.setProperty('--agrify-visible-viewport-gap', `${viewportGap}px`);
}

document.addEventListener('DOMContentLoaded', init);

