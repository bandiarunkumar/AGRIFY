// ============================================================
// Home Page — Farmer workspace and AGRIFY field intelligence
// ============================================================

import { t, getLang } from '../i18n.js';
import { renderIntroVideo, initIntroVideo } from '../components/introVideo.js';

export function renderHome() {
  const lang = getLang();

  return `
    <div class="hero-section">
      <div class="hero-badge hero-anim" style="--anim-order:0">
        <span class="hero-badge-dot"></span>
        ${t('hero_badge')}
      </div>

      <div class="hero-main">
        <div class="hero-copy">
      <h1 class="hero-title">
        <span class="hero-word-line">
          <span class="hero-word">${t('hero_title_1').split(' ')[0] || 'Smart'}</span>
          <span class="hero-word">${t('hero_title_1').split(' ')[1] || 'Farming'}</span>
        </span>
        <span class="hero-word-line">
          ${lang === 'te'
            ? `<span class="hero-word green">${t('hero_title_2')}</span>`
            : `<span class="hero-word green">${t('hero_title_2').split(' ')[0] || 'Made'}</span>
               <span class="hero-word green">${t('hero_title_2').split(' ')[1] || 'Simple'}</span>`}
        </span>
        <span class="hero-word-line">
          <span class="hero-word">${t('hero_title_3').split(' ')[0] || 'For'}</span>
          <span class="hero-word">${t('hero_title_3').split(' ')[1] || 'Every'}</span>
          <span class="hero-word">${t('hero_title_3').split(' ')[2] || 'Farmer'}</span>
        </span>
      </h1>

      <p class="hero-subtitle hero-anim" style="--anim-order:7">
        ${t('hero_subtitle')}
      </p>

      <!-- AGRIFY AI Companion Floating Banner -->
      <div class="hero-mascot-card hero-anim" style="--anim-order:8" data-navigate="chatbot">
        <div class="hero-mascot-avatar-wrap">
          <img src="/ai-mascot.png" alt="AGRIFY AI Mascot" class="hero-mascot-img" />
          <span class="hero-mascot-pulse"></span>
        </div>
        <div class="hero-mascot-speech">
          <div class="hero-mascot-header">
            <span class="hero-mascot-tag">✨ AGRIFY AI</span>
            <span class="hero-mascot-live">${lang === 'te' ? 'వ్యవసాయ సహాయకుడు' : 'Farming assistant'}</span>
          </div>
          <p class="hero-mascot-quote">
            ${lang === 'te' 
              ? 'నమస్కారం! వ్యవసాయ విషయాలపై అడగండి. అందుబాటులో ఉన్న నేల, వాతావరణం మరియు మార్కెట్ డేటాతో సమాధానం ఇస్తాను.'
              : '“Ask me about farming. I can explain available soil, weather, and market information and clearly flag when data is unavailable.”'}
          </p>
          <div class="hero-mascot-action">
            <span>${lang === 'te' ? 'చాట్ ప్రారంభించండి' : 'Ask AI Companion'}</span>
            <span class="action-arrow">→</span>
          </div>
        </div>
      </div>

      <div class="hero-ctas hero-anim" style="--anim-order:9">
        <button class="btn btn-accent btn-lg" data-navigate="analysis" id="hero-start-btn">
          ${t('hero_cta_analyze')}
        </button>
        <button class="btn btn-secondary btn-lg" data-navigate="weather">
          ${t('hero_cta_weather')}
        </button>
        <button class="btn btn-secondary btn-lg" data-navigate="cropDoctor">
          ${t('hero_cta_doctor')}
        </button>
      </div>

      <!-- Trust & Capability Badges -->
      <div class="hero-trust-bar hero-anim" style="--anim-order:10">
        <div class="trust-item">
          <span class="trust-icon">🛰️</span>
          <span class="trust-label">${lang === 'te' ? 'ISRIC నేల అంచనాలు' : 'ISRIC soil estimates'}</span>
        </div>
        <div class="trust-sep">·</div>
        <div class="trust-item">
          <span class="trust-icon">📊</span>
          <span class="trust-label">${lang === 'te' ? 'Agmarknet ధరల శోధన' : 'Agmarknet price lookup'}</span>
        </div>
        <div class="trust-sep">·</div>
        <div class="trust-item">
          <span class="trust-icon">🔬</span>
          <span class="trust-label">${lang === 'te' ? 'బంగాళాదుంప ఆకు స్క్రీనింగ్' : 'Potato leaf screening'}</span>
        </div>
        <div class="trust-sep">·</div>
        <div class="trust-item">
          <span class="trust-icon">🗣️</span>
          <span class="trust-label">${lang === 'te' ? 'వాయిస్ & తెలుగు మద్దతు' : 'Voice & Telugu Support'}</span>
        </div>
      </div>
        </div>

        <div class="hero-landscape" role="img" aria-label="${lang === 'te' ? 'వ్యవసాయ భూమి, ఉదయ సూర్యుడు మరియు పంట వరుసల అసలు దృశ్యచిత్రం' : 'Illustration of Indian farmland at sunrise with cultivated crop rows'}">
          <svg class="landscape-art" viewBox="0 0 720 500" aria-hidden="true" focusable="false">
            <defs>
              <linearGradient id="field-sky" x1="0" y1="0" x2="0.9" y2="1">
                <stop offset="0" stop-color="#f5d9a1" />
                <stop offset="0.58" stop-color="#e8c88c" />
                <stop offset="1" stop-color="#bdd2a4" />
              </linearGradient>
              <linearGradient id="field-earth" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stop-color="#8aab65" />
                <stop offset="1" stop-color="#315c3c" />
              </linearGradient>
              <linearGradient id="field-row" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stop-color="#d9c18b" stop-opacity=".85" />
                <stop offset="1" stop-color="#c7a766" stop-opacity=".08" />
              </linearGradient>
              <radialGradient id="field-sun-glow">
                <stop offset="0" stop-color="#fff6d9" stop-opacity=".95" />
                <stop offset="1" stop-color="#fff6d9" stop-opacity="0" />
              </radialGradient>
            </defs>
            <rect width="720" height="500" rx="32" fill="url(#field-sky)" />
            <circle cx="514" cy="122" r="112" fill="url(#field-sun-glow)" />
            <circle cx="514" cy="122" r="38" fill="#fff1c9" />
            <path d="M0 245 C105 195 205 211 296 244 C397 280 485 205 579 221 C633 230 681 250 720 264 L720 500 L0 500Z" fill="#829c6b" opacity=".63" />
            <path d="M0 294 C99 250 207 270 303 302 C415 338 501 259 594 273 C646 280 688 299 720 312 L720 500 L0 500Z" fill="#53764e" />
            <path d="M0 343 C120 302 231 326 336 357 C452 392 560 313 720 357 L720 500 L0 500Z" fill="url(#field-earth)" />
            <path d="M0 381 C137 340 235 355 347 390 C478 430 582 351 720 389 L720 500 L0 500Z" fill="#315a3d" />
            <g fill="none" stroke="url(#field-row)" stroke-width="3" opacity=".8">
              <path d="M-40 500 C123 387 241 370 375 386 C510 402 610 450 760 500" />
              <path d="M76 500 C208 403 295 393 390 404 C494 416 582 460 665 500" />
              <path d="M203 500 C286 435 340 420 406 427 C472 433 523 465 568 500" />
              <path d="M324 500 C366 461 393 447 423 449 C455 451 480 474 501 500" />
            </g>
            <g fill="#6f8d52" opacity=".88">
              <path d="M96 328c-8-25-4-44 10-59 12 20 12 39 1 58 18-13 34-15 49-7-16 17-34 22-54 13l-2 28h-5l1-33Z" />
              <path d="M628 318c-7-21-4-38 8-51 11 17 11 33 1 50 16-11 29-12 42-5-14 15-29 18-46 10l-2 25h-5l2-29Z" />
            </g>
            <g fill="#e9d49f" opacity=".55">
              <circle cx="135" cy="152" r="2" /><circle cx="181" cy="116" r="2" /><circle cx="231" cy="166" r="1.5" />
              <circle cx="401" cy="101" r="2" /><circle cx="609" cy="179" r="2" /><circle cx="355" cy="185" r="1.5" />
            </g>
          </svg>
          <div class="landscape-caption">
            <span class="landscape-caption-mark" aria-hidden="true">✳</span>
            <span>${lang === 'te' ? 'మీ పొలం కోసం రూపొందించబడింది' : 'Intelligence rooted in your field'}</span>
          </div>
          <svg class="landscape-leaf" viewBox="0 0 42 42" aria-hidden="true" focusable="false"><path d="M35 6C20 7 8 12 7 24c-.7 7 5 12 12 11C31 33 36 21 35 6Z" fill="currentColor"/><path d="M8 35c6-9 12-14 22-22" fill="none" stroke="var(--c-bg-card)" stroke-width="1.7" stroke-linecap="round" opacity=".85"/></svg>
        </div>
      </div>

      <!-- Feature Grid -->
      <div class="home-workspace-heading">
        <span class="home-kicker">${lang === 'te' ? 'వ్యవసాయ పనిముట్లు' : 'YOUR FARM WORKSPACE'}</span>
        <h2>${lang === 'te' ? 'మీ తదుపరి పనిని ఎంచుకోండి' : 'Choose what you need today'}</h2>
        <p>${lang === 'te' ? 'ప్రస్తుత వ్యవసాయ సమాచారం కోసం మీ స్థలం మరియు పంట వివరాలను ఉపయోగించండి.' : 'Use your farm location and crop details to get relevant field guidance.'}</p>
      </div>
      <div class="feature-grid hero-anim" style="max-width:1160px;margin-top:var(--sp-2xl);--anim-order:11">
        <div class="feature-card" data-navigate="analysis">
          <div class="feature-card-header">
            <span class="feature-card-icon">🌱</span>
            <span class="feature-badge badge-green">ML AI</span>
          </div>
          <div class="feature-card-title">${t('feature_crop_rec')}</div>
          <div class="feature-card-desc">${t('feature_crop_rec_desc')}</div>
          <div class="feature-card-footer">
            <span class="feature-action-text">${lang === 'te' ? 'విశ్లేషించండి' : 'Analyze Now'}</span>
            <span class="feature-arrow">→</span>
          </div>
        </div>

        <div class="feature-card" data-navigate="analysis">
          <div class="feature-card-header">
            <span class="feature-card-icon">🌐</span>
            <span class="feature-badge badge-sand">ISRIC v2.0</span>
          </div>
          <div class="feature-card-title">${t('feature_soil')}</div>
          <div class="feature-card-desc">${t('feature_soil_desc')}</div>
          <div class="feature-card-footer">
            <span class="feature-action-text">${lang === 'te' ? 'నేల డేటా' : 'View Soil Health'}</span>
            <span class="feature-arrow">→</span>
          </div>
        </div>

        <div class="feature-card" data-navigate="weather">
          <div class="feature-card-header">
            <span class="feature-card-icon">🌩️</span>
            <span class="feature-badge badge-blue">GPS Weather</span>
          </div>
          <div class="feature-card-title">${t('feature_weather')}</div>
          <div class="feature-card-desc">${t('feature_weather_desc')}</div>
          <div class="feature-card-footer">
            <span class="feature-action-text">${lang === 'te' ? 'వాతావరణం' : 'Check Forecast'}</span>
            <span class="feature-arrow">→</span>
          </div>
        </div>

        <div class="feature-card" data-navigate="analysis">
          <div class="feature-card-header">
            <span class="feature-card-icon">🧬</span>
            <span class="feature-badge badge-green">Agronomy</span>
          </div>
          <div class="feature-card-title">${t('feature_fert')}</div>
          <div class="feature-card-desc">${t('feature_fert_desc')}</div>
          <div class="feature-card-footer">
            <span class="feature-action-text">${lang === 'te' ? 'ఎరువుల గైడ్' : 'Dosage Guide'}</span>
            <span class="feature-arrow">→</span>
          </div>
        </div>

        <div class="feature-card" data-navigate="cropDoctor">
          <div class="feature-card-header">
            <span class="feature-card-icon">🔬</span>
            <span class="feature-badge badge-amber">Potato model</span>
          </div>
          <div class="feature-card-title">${t('feature_doctor')}</div>
          <div class="feature-card-desc">${t('feature_doctor_desc')}</div>
          <div class="feature-card-footer">
            <span class="feature-action-text">${lang === 'te' ? 'ఫోటో స్కాన్' : 'Scan Leaf Photo'}</span>
            <span class="feature-arrow">→</span>
          </div>
        </div>

        <div class="feature-card" data-navigate="market">
          <div class="feature-card-header">
            <span class="feature-card-icon">📊</span>
            <span class="feature-badge badge-sand">Agmarknet</span>
          </div>
          <div class="feature-card-title">${t('feature_market')}</div>
          <div class="feature-card-desc">${t('feature_market_desc')}</div>
          <div class="feature-card-footer">
            <span class="feature-action-text">${lang === 'te' ? 'మండి ధరలు' : 'Explore Markets'}</span>
            <span class="feature-arrow">→</span>
          </div>
        </div>

        <div class="feature-card" data-navigate="chatbot">
          <div class="feature-card-header">
            <span class="feature-card-icon">💬</span>
            <span class="feature-badge badge-green">Gemini AI</span>
          </div>
          <div class="feature-card-title">${t('feature_chatbot')}</div>
          <div class="feature-card-desc">${t('feature_chatbot_desc')}</div>
          <div class="feature-card-footer">
            <span class="feature-action-text">${lang === 'te' ? 'సందేహాలు అడగండి' : 'Chat in EN / తె'}</span>
            <span class="feature-arrow">→</span>
          </div>
        </div>

        <div class="feature-card" data-navigate="alerts">
          <div class="feature-card-header">
            <span class="feature-card-icon">🚨</span>
            <span class="feature-badge badge-amber">Farm advisories</span>
          </div>
          <div class="feature-card-title">${t('feature_alerts')}</div>
          <div class="feature-card-desc">${t('feature_alerts_desc')}</div>
          <div class="feature-card-footer">
            <span class="feature-action-text">${lang === 'te' ? 'హెచ్చరికలు చూడండి' : 'View Advisories'}</span>
            <span class="feature-arrow">→</span>
          </div>
        </div>

        <div class="feature-card" data-navigate="experts">
          <div class="feature-card-header">
            <span class="feature-card-icon">👨‍🌾</span>
            <span class="feature-badge badge-blue">Helplines</span>
          </div>
          <div class="feature-card-title">Expert Connect</div>
          <div class="feature-card-desc">Talk to certified agronomists and plant pathologists directly via call or WhatsApp.</div>
          <div class="feature-card-footer">
            <span class="feature-action-text">${lang === 'te' ? 'నిపుణులను కలవండి' : 'Contact Specialists'}</span>
            <span class="feature-arrow">→</span>
          </div>
        </div>
      </div>

      ${renderIntroVideo()}
    </div>
  `;
}

export function initHome() {
  initIntroVideo();
}
