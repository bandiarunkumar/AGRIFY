// ============================================================
// Footer Component — Clean, minimal, user-friendly
// ============================================================

import { getLang } from '../i18n.js';

export function renderFooter() {
  const footerEl = document.getElementById('footer-root');
  if (!footerEl) return;

  const lang = getLang();

  footerEl.innerHTML = `
    <div class="footer-container">
      <div class="footer-grid">
        <!-- Quick Links -->
        <div class="footer-col">
          <div class="footer-heading">🔗 ${lang === 'te' ? 'త్వరిత లింకులు' : 'Quick Links'}</div>
          <ul class="footer-list">
            <li><a href="#" data-navigate="analysis" class="footer-link">🌱 ${lang === 'te' ? 'పొలం విశ్లేషణ' : 'Farm Analysis'}</a></li>
            <li><a href="#" data-navigate="weather" class="footer-link">🌤️ ${lang === 'te' ? 'వాతావరణం' : 'Weather Forecast'}</a></li>
            <li><a href="#" data-navigate="market" class="footer-link">📊 ${lang === 'te' ? 'మార్కెట్ ధరలు' : 'Market Prices'}</a></li>
            <li><a href="#" data-navigate="cropDoctor" class="footer-link">🔬 ${lang === 'te' ? 'పంట వైద్యుడు' : 'Crop Doctor'}</a></li>
          </ul>
        </div>

        <!-- More Features -->
        <div class="footer-col">
          <div class="footer-heading">🌾 ${lang === 'te' ? 'మరిన్ని' : 'More'}</div>
          <ul class="footer-list">
            <li><a href="#" data-navigate="chatbot" class="footer-link">💬 ${lang === 'te' ? 'స్మార్ట్ సహాయకుడు' : 'Smart Assistant'}</a></li>
            <li><a href="#" data-navigate="alerts" class="footer-link">🚨 ${lang === 'te' ? 'హెచ్చరికలు' : 'Farm Alerts'}</a></li>
            <li><span class="footer-text">📞 ${lang === 'te' ? 'కిసాన్ హెల్ప్‌లైన్' : 'Kisan Helpline'}: 1800-180-1551</span></li>
            <li><span class="footer-text">🌐 ${lang === 'te' ? 'ఇంగ్లీష్ & తెలుగు' : 'English & Telugu'}</span></li>
          </ul>
        </div>

        <!-- About -->
        <div class="footer-col">
          <div class="footer-heading">ℹ️ ${lang === 'te' ? 'గురించి' : 'About'}</div>
          <ul class="footer-list">
            <li><span class="footer-text">${lang === 'te' ? 'భారతీయ రైతుల కోసం తయారు చేయబడింది' : 'Made for Indian Farmers'}</span></li>
            <li><span class="footer-text">${lang === 'te' ? 'GPS-ఆధారిత విశ్లేషణ' : 'GPS-based Analysis'}</span></li>
            <li><span class="footer-text">${lang === 'te' ? 'పంట & ఎరువుల సిఫారసులు' : 'Crop & Fertilizer Recommendations'}</span></li>
            <li><span class="footer-text">${lang === 'te' ? '3000+ మండి మార్కెట్ ధరలు' : '3000+ Mandi Market Prices'}</span></li>
          </ul>
        </div>
      </div>

      <div class="footer-bottom">
        <div class="footer-brand">
          <span class="footer-logo">🌾</span>
          <span class="footer-brand-name">Agri<span class="green">Connect</span></span>
        </div>
        <div class="footer-copy">
          © ${new Date().getFullYear()} AgriConnect — ${lang === 'te' ? 'భారతీయ రైతుల కోసం నిర్మించబడింది' : 'Built for Indian Farmers'} 🇮🇳
        </div>
      </div>
    </div>
  `;

  // Attach navigation events
  footerEl.querySelectorAll('[data-navigate]').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      window.dispatchEvent(new CustomEvent('navigate', { detail: el.dataset.navigate }));
    });
  });
}
