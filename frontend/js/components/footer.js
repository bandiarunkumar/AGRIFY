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
        <!-- Brand Info -->
        <div class="footer-col footer-col-brand">
          <div class="footer-brand">
            <span class="footer-logo">🌾</span>
            <span class="footer-brand-name">AGRI<span class="green">FY</span></span>
          </div>
          <p class="footer-tagline">
            ${lang === 'te' 
              ? 'ఉపగ్రహ నేల డేటా, ప్రత్యక్ష వాతావరణం మరియు కృత్రిమ మేధస్సుతో భారతీయ రైతులకు అధునాతన వ్యవసాయ సహాయకుడు.' 
              : 'Next-generation agricultural intelligence for Indian farmers — combining satellite soil data, live weather, and adaptive AI.'}
          </p>
          <div class="footer-status-badge">
            <span class="status-pulse"></span>
            <span>${lang === 'te' ? 'సిస్టమ్ సిద్ధంగా ఉంది · GPS ఆన్‌లైన్' : 'Satellite & AI Engines Online'}</span>
          </div>
        </div>

        <!-- Quick Links -->
        <div class="footer-col">
          <div class="footer-heading">🔗 ${lang === 'te' ? 'ముఖ్యమైన సాధనాలు' : 'Core Tools'}</div>
          <ul class="footer-list">
            <li><a href="#" data-navigate="analysis" class="footer-link">🌱 ${lang === 'te' ? 'పొలం విశ్లేషణ' : 'Farm Analysis'}</a></li>
            <li><a href="#" data-navigate="weather" class="footer-link">🌤️ ${lang === 'te' ? 'వాతావరణ అంచనా' : 'Weather Forecast'}</a></li>
            <li><a href="#" data-navigate="market" class="footer-link">📊 ${lang === 'te' ? 'మార్కెట్ ధరలు' : 'Market Prices'}</a></li>
            <li><a href="#" data-navigate="cropDoctor" class="footer-link">🔬 ${lang === 'te' ? 'పంట వైద్యుడు' : 'Crop Doctor'}</a></li>
          </ul>
        </div>

        <!-- More Features -->
        <div class="footer-col">
          <div class="footer-heading">🌾 ${lang === 'te' ? 'సేవలు & సహాయం' : 'Services & Support'}</div>
          <ul class="footer-list">
            <li><a href="#" data-navigate="chatbot" class="footer-link">💬 ${lang === 'te' ? 'స్మార్ట్ సహాయకుడు' : 'AI Farm Assistant'}</a></li>
            <li><a href="#" data-navigate="alerts" class="footer-link">🚨 ${lang === 'te' ? 'పొలం హెచ్చరికలు' : 'Farm Alerts'}</a></li>
            <li><a href="#" data-navigate="experts" class="footer-link">👨‍🌾 ${lang === 'te' ? 'నిపుణుల సంప్రదింపు' : 'Expert Connect'}</a></li>
            <li><span class="footer-text">📞 ${lang === 'te' ? 'కిసాన్ టోల్-ఫ్రీ' : 'Kisan Helpline'}: 1800-180-1551</span></li>
          </ul>
        </div>

        <!-- Trust & Origin -->
        <div class="footer-col">
          <div class="footer-heading">ℹ️ ${lang === 'te' ? 'గురించి' : 'About'}</div>
          <ul class="footer-list">
            <li><span class="footer-text">🇮🇳 ${lang === 'te' ? 'భారతీయ రైతుల కోసం రూపొందించబడింది' : 'Built for Indian Farmers'}</span></li>
            <li><span class="footer-text">🛰️ ${lang === 'te' ? 'ISRIC & ఉపగ్రహ నేల డేటా' : 'ISRIC & Satellite Soil Data'}</span></li>
            <li><span class="footer-text">🌾 ${lang === 'te' ? '3000+ అగ్‌మార్క్‌నెట్ మండీలు' : '3000+ Agmarknet Mandis'}</span></li>
            <li><span class="footer-text">🌐 ${lang === 'te' ? 'ఇంగ్లీష్ & తెలుగు భాషా మద్దతు' : 'English & Telugu Multi-Language'}</span></li>
          </ul>
        </div>
      </div>

      <div class="footer-bottom">
        <div class="footer-copy">
          © ${new Date().getFullYear()} AGRIFY — ${lang === 'te' ? 'భారతీయ వ్యవసాయ సాధికారత' : 'Empowering Indian Agriculture with Data & AI'} 🇮🇳
        </div>
        <div class="footer-bottom-meta">
          <span>🌿 Eco-Conscious AI</span> · <span>🔒 Privacy First</span> · <span>🆓 100% Free for Farmers</span>
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
