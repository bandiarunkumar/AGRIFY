// ============================================================
// Home Page — CINEMATIC HEROIC Entry with Letter Scramble
// ============================================================

import { t, getLang } from '../i18n.js';
import { renderIntroVideo, initIntroVideo } from '../components/introVideo.js';

let hasPlayedIntro = false;

export function renderHome() {
  const lang = getLang();

  return `
    <!-- CINEMATIC INTRO OVERLAY (plays once per session) -->
    ${!hasPlayedIntro ? `
    <div class="cinema-intro-overlay" id="cinema-intro">
      <!-- Particle explosion layer -->
      <canvas id="cinema-particles-canvas"></canvas>

      <!-- Shockwave rings -->
      <div class="cinema-shockwave-container">
        <div class="cinema-shockwave ring1"></div>
        <div class="cinema-shockwave ring2"></div>
        <div class="cinema-shockwave ring3"></div>
      </div>

      <!-- Lightning bolt flashes -->
      <div class="cinema-lightning" id="cinema-lightning"></div>

      <!-- Core content -->
      <div class="cinema-intro-content">
        <!-- Central emblem -->
        <div class="cinema-emblem" id="cinema-emblem">
          <div class="cinema-emblem-ring"></div>
          <div class="cinema-emblem-ring cinema-emblem-ring-2"></div>
          <div class="cinema-emblem-icon">🌾</div>
        </div>

        <!-- Scramble Title -->
        <div class="cinema-title-stage" id="cinema-title-stage">
          <div class="cinema-scramble-line" data-final="AGRI" id="scramble-word-1"></div>
          <div class="cinema-scramble-line cinema-green-word" data-final="FY" id="scramble-word-2"></div>
        </div>

        <!-- Tagline -->
        <div class="cinema-tagline" id="cinema-tagline">
          <span class="cinema-tagline-word" style="--tw:0">Smart</span>
          <span class="cinema-tagline-word" style="--tw:1">Farming</span>
          <span class="cinema-tagline-word" style="--tw:2">for</span>
          <span class="cinema-tagline-word" style="--tw:3">Every</span>
          <span class="cinema-tagline-word" style="--tw:4">Farmer</span>
          <span class="cinema-tagline-word cinema-tagline-emoji" style="--tw:5">🌱</span>
        </div>

        <!-- Click to enter -->
        <div class="cinema-enter-hint" id="cinema-enter-hint">
          <span class="cinema-enter-pulse"></span>
          CLICK ANYWHERE TO ENTER
        </div>
      </div>
    </div>
    ` : ''}

    <div class="hero-section">
      <div class="hero-badge hero-anim" style="--anim-order:0">
        <span class="hero-badge-dot"></span>
        ${t('hero_badge')}
      </div>

      <h1 class="hero-title">
        <span class="hero-word-line">
          <span class="hero-word hero-jumble-word" data-final="${t('hero_title_1').split(' ')[0] || 'Smart'}" style="--word-i:0">${t('hero_title_1').split(' ')[0] || 'Smart'}</span>
          <span class="hero-word hero-jumble-word" data-final="${t('hero_title_1').split(' ')[1] || 'Farming'}" style="--word-i:1">${t('hero_title_1').split(' ')[1] || 'Farming'}</span>
        </span>
        <span class="hero-word-line">
          <span class="hero-word hero-jumble-word green" data-final="${t('hero_title_2').split(' ')[0] || 'Made'}" style="--word-i:2">${t('hero_title_2').split(' ')[0] || 'Made'}</span>
          <span class="hero-word hero-jumble-word green" data-final="${t('hero_title_2').split(' ')[1] || 'Simple'}" style="--word-i:3">${t('hero_title_2').split(' ')[1] || 'Simple'}</span>
        </span>
        <span class="hero-word-line">
          <span class="hero-word hero-jumble-word" data-final="${t('hero_title_3').split(' ')[0] || 'For'}" style="--word-i:4">${t('hero_title_3').split(' ')[0] || 'For'}</span>
          <span class="hero-word hero-jumble-word" data-final="${t('hero_title_3').split(' ')[1] || 'Every'}" style="--word-i:5">${t('hero_title_3').split(' ')[1] || 'Every'}</span>
          <span class="hero-word hero-jumble-word" data-final="${t('hero_title_3').split(' ')[2] || 'Farmer'}" style="--word-i:6">${t('hero_title_3').split(' ')[2] || 'Farmer'}</span>
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
            <span class="hero-mascot-live">${lang === 'te' ? 'ఆన్‌లైన్ · సిద్ధంగా ఉంది' : 'Active · Multilingual'}</span>
          </div>
          <p class="hero-mascot-quote">
            ${lang === 'te' 
              ? 'నమస్కారం! మీ నేల డేటా, పంట సిఫారసులు మరియు 3000+ మార్కెట్ ధరల గురించి ఏ ప్రశ్నైనా అడగండి.' 
              : '“Namaste! I analyze your soil data, diagnose crop leaf diseases, and track mandi price trends in real-time.”'}
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
          <span class="trust-label">${lang === 'te' ? 'ISRIC ఉపగ్రహ నేల డేటా' : 'ISRIC Satellite Soil Grids'}</span>
        </div>
        <div class="trust-sep">·</div>
        <div class="trust-item">
          <span class="trust-icon">📊</span>
          <span class="trust-label">${lang === 'te' ? '3000+ లైవ్ మండీలు' : '3,000+ Mandi Prices'}</span>
        </div>
        <div class="trust-sep">·</div>
        <div class="trust-item">
          <span class="trust-icon">🔬</span>
          <span class="trust-label">${lang === 'te' ? 'AI వ్యాధి నిర్ధారణ' : 'Vision Disease AI'}</span>
        </div>
        <div class="trust-sep">·</div>
        <div class="trust-item">
          <span class="trust-icon">🗣️</span>
          <span class="trust-label">${lang === 'te' ? 'వాయిస్ & తెలుగు మద్దతు' : 'Voice & Telugu Support'}</span>
        </div>
      </div>

      <!-- Feature Grid -->
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
            <span class="feature-badge badge-blue">GPS Live</span>
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
            <span class="feature-badge badge-amber">CNN Vision</span>
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
            <span class="feature-badge badge-amber">Real-Time</span>
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
  const isFirstVisit = !hasPlayedIntro;
  const introDelay = isFirstVisit ? 5000 : 0;

  // ============================================
  // CINEMATIC INTRO (plays once per session)
  // ============================================
  if (!hasPlayedIntro) {
    hasPlayedIntro = true;
    const overlay = document.getElementById('cinema-intro');
    if (overlay) {
      initParticleCanvas();
      triggerLightningFlashes();
      startLetterScramble('scramble-word-1', 600);
      startLetterScramble('scramble-word-2', 1200);
      animateTaglineWords();

      // Show enter hint after animations settle
      setTimeout(() => {
        const hint = document.getElementById('cinema-enter-hint');
        if (hint) hint.classList.add('cinema-enter-visible');
      }, 3800);

      // Auto-dismiss after 5 seconds
      const autoDismiss = setTimeout(() => {
        dismissCinemaIntro(overlay);
      }, 5800);

      // Click to skip
      overlay.addEventListener('click', () => {
        clearTimeout(autoDismiss);
        dismissCinemaIntro(overlay);
      });
    }
  }

  // Trigger hero word jumble after intro
  triggerHeroJumble(introDelay);

  // Initialize intro video player
  setTimeout(() => initIntroVideo(), introDelay + 500);
}

// ============================================
// LETTER SCRAMBLE ENGINE
// ============================================
const SCRAMBLE_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@#$%&*!?';

function startLetterScramble(elementId, startDelay) {
  const container = document.getElementById(elementId);
  if (!container) return;

  const finalWord = container.getAttribute('data-final');
  if (!finalWord) return;

  // Create letter cells
  const letters = finalWord.split('');
  container.innerHTML = '';

  letters.forEach((char, i) => {
    const cell = document.createElement('span');
    cell.className = 'cinema-scramble-char';
    cell.style.setProperty('--ci', i);
    cell.textContent = SCRAMBLE_CHARS[Math.floor(Math.random() * SCRAMBLE_CHARS.length)];
    cell.setAttribute('data-final', char);
    container.appendChild(cell);
  });

  // Phase 1: Wild scramble (all letters randomizing)
  setTimeout(() => {
    const cells = container.querySelectorAll('.cinema-scramble-char');
    cells.forEach(cell => cell.classList.add('cinema-char-active'));

    let scrambleInterval = setInterval(() => {
      cells.forEach(cell => {
        if (!cell.classList.contains('cinema-char-locked')) {
          cell.textContent = SCRAMBLE_CHARS[Math.floor(Math.random() * SCRAMBLE_CHARS.length)];
        }
      });
    }, 50);

    // Phase 2: Lock letters one by one
    letters.forEach((char, i) => {
      setTimeout(() => {
        const cell = cells[i];
        if (cell) {
          cell.textContent = char;
          cell.classList.add('cinema-char-locked');
          cell.classList.add('cinema-char-slam');
        }
        // Clear interval when last letter locks
        if (i === letters.length - 1) {
          clearInterval(scrambleInterval);
        }
      }, 800 + i * 150);
    });
  }, startDelay);
}

// ============================================
// PARTICLE CANVAS
// ============================================
function initParticleCanvas() {
  const canvas = document.getElementById('cinema-particles-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const particles = [];
  const particleCount = 120;

  for (let i = 0; i < particleCount; i++) {
    particles.push({
      x: canvas.width / 2 + (Math.random() - 0.5) * 100,
      y: canvas.height / 2 + (Math.random() - 0.5) * 100,
      vx: (Math.random() - 0.5) * 8,
      vy: (Math.random() - 0.5) * 8,
      radius: Math.random() * 3 + 1,
      alpha: Math.random() * 0.8 + 0.2,
      color: Math.random() > 0.5 ? '#22c55e' : '#86efac',
      life: 1,
      decay: 0.003 + Math.random() * 0.008,
    });
  }

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    let alive = false;
    particles.forEach(p => {
      if (p.life <= 0) return;
      alive = true;

      p.x += p.vx;
      p.y += p.vy;
      p.vx *= 0.99;
      p.vy *= 0.99;
      p.life -= p.decay;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = p.alpha * p.life;
      ctx.fill();
      ctx.globalAlpha = 1;

      // Trailing line
      if (p.life > 0.3) {
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(p.x - p.vx * 3, p.y - p.vy * 3);
        ctx.strokeStyle = p.color;
        ctx.globalAlpha = p.alpha * p.life * 0.3;
        ctx.lineWidth = p.radius * 0.5;
        ctx.stroke();
        ctx.globalAlpha = 1;
      }
    });

    if (alive) requestAnimationFrame(animate);
  }

  // Start particles after a brief delay for dramatic effect
  setTimeout(() => animate(), 200);
}

// ============================================
// LIGHTNING FLASHES
// ============================================
function triggerLightningFlashes() {
  const container = document.getElementById('cinema-lightning');
  if (!container) return;

  const flashTimes = [300, 800, 1600, 2400];
  flashTimes.forEach(delay => {
    setTimeout(() => {
      container.classList.add('cinema-flash-active');
      setTimeout(() => container.classList.remove('cinema-flash-active'), 100);
    }, delay);
  });
}

// ============================================
// TAGLINE WORD ANIMATION
// ============================================
function animateTaglineWords() {
  const words = document.querySelectorAll('.cinema-tagline-word');
  words.forEach((word, i) => {
    setTimeout(() => {
      word.classList.add('cinema-tagline-visible');
    }, 2800 + i * 180);
  });
}

// ============================================
// DISMISS CINEMA INTRO
// ============================================
function dismissCinemaIntro(overlay) {
  if (overlay.classList.contains('cinema-intro-exit')) return;
  overlay.classList.add('cinema-intro-exit');

  // Screen shake effect on the body
  document.body.classList.add('cinema-screen-shake');
  setTimeout(() => document.body.classList.remove('cinema-screen-shake'), 500);

  setTimeout(() => {
    overlay.remove();
    // Trigger hero entry immediately after
    triggerHeroJumble(200);
  }, 900);
}

// ============================================
// HERO JUMBLE ANIMATION — Words scramble in
// ============================================
function triggerHeroJumble(baseDelay) {
  const words = document.querySelectorAll('.hero-jumble-word');

  words.forEach((word, i) => {
    const finalText = word.getAttribute('data-final') || word.textContent;
    const letters = finalText.split('');

    // Replace text content with letter spans
    word.textContent = '';
    word.style.opacity = '1';

    letters.forEach((char, ci) => {
      const span = document.createElement('span');
      span.className = 'hero-letter-cell';
      span.style.setProperty('--li', ci);
      span.setAttribute('data-final', char);
      span.textContent = SCRAMBLE_CHARS[Math.floor(Math.random() * SCRAMBLE_CHARS.length)];
      word.appendChild(span);
    });

    // Start scramble for this word
    const wordDelay = baseDelay + i * 300;

    setTimeout(() => {
      word.classList.add('hero-word-smash-in');

      const cells = word.querySelectorAll('.hero-letter-cell');

      // Scramble phase
      let scrambleInt = setInterval(() => {
        cells.forEach(cell => {
          if (!cell.classList.contains('hero-letter-locked')) {
            cell.textContent = SCRAMBLE_CHARS[Math.floor(Math.random() * SCRAMBLE_CHARS.length)];
          }
        });
      }, 40);

      // Lock letters one by one
      cells.forEach((cell, ci) => {
        setTimeout(() => {
          const finalChar = cell.getAttribute('data-final');
          cell.textContent = finalChar;
          cell.classList.add('hero-letter-locked');
          cell.classList.add('hero-letter-slam');

          if (ci === cells.length - 1) {
            clearInterval(scrambleInt);
          }
        }, 400 + ci * 80);
      });
    }, wordDelay);
  });

  // Animate other hero elements
  const heroAnims = document.querySelectorAll('.hero-anim');
  heroAnims.forEach((el) => {
    const order = parseInt(el.style.getPropertyValue('--anim-order') || '0');
    el.style.animationDelay = `${baseDelay + 2200 + order * 120}ms`;
    el.classList.add('hero-anim-active');
  });
}
