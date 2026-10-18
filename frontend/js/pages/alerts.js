// ============================================================
// AGRIFY — Farm Risk & Advisory Alert Center
// Live alerts by GPS: weather, soil, satellite NDVI, news, crop

function escapeAlertText(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[char]);
}

function safeNewsUrl(value) {
  try {
    const url = new URL(String(value ?? ''));
    return ['https:', 'http:'].includes(url.protocol) ? escapeAlertText(url.href) : '#';
  } catch {
    return '#';
  }
}
// ============================================================

import { getAlerts, getNews, getCurrentPosition, reverseGeocode } from '../api.js';
import { showToast } from '../voice.js';

export function renderAlerts() {
  return `
    <div class="page-section alerts-page">

      <!-- Hero Header -->
      <div class="alerts-hero">
        <div class="alerts-hero-badge">
          <span class="badge-dot pulse-red"></span>
          <span>AGRIFY FARM RISK MONITOR</span>
        </div>
        <h1 class="alerts-hero-title">🚨 Farm Alert Center</h1>
        <p class="alerts-hero-sub">
          Rule-based advisories from available weather feeds, modeled soil estimates, and crop-season rules
        </p>
        <div class="alerts-source-strip">
          <span class="source-chip-pill">🌤️ Weather API</span>
          <span class="source-chip-pill">🧪 SoilGrids estimates</span>
          <span class="source-chip-pill">🌱 Crop Calendar</span>
        </div>
      </div>

      <!-- Controls Card -->
      <div class="card alerts-controls-card">
        <h3 class="section-title"><span class="icon">📍</span> Get Alerts for My Farm</h3>
        <div class="alerts-controls-row">
          <div class="form-group alerts-form-group">
            <label for="alert-crop">Current Crop</label>
            <select class="form-select" id="alert-crop">
              <option value="rice">Rice</option>
              <option value="wheat">Wheat</option>
              <option value="cotton">Cotton</option>
              <option value="maize">Maize</option>
              <option value="tomato">Tomato</option>
              <option value="potato">Potato</option>
            </select>
          </div>
          <div class="form-group alerts-form-group">
            <label for="alert-season">Season</label>
            <select class="form-select" id="alert-season">
              <option value="Kharif">Kharif</option>
              <option value="Rabi">Rabi</option>
              <option value="Zaid">Zaid</option>
            </select>
          </div>
          <button class="gps-btn alerts-gps-btn" id="load-alerts-btn">
            <span class="gps-btn-icon">📡</span> Load Alerts for My GPS Location
          </button>
        </div>
        <div class="alerts-controls-note">
          🔒 Your GPS coordinates are used only to fetch local alerts and are not stored.
        </div>
      </div>

      <!-- Alert Results -->
      <div id="alerts-results" aria-live="polite" aria-busy="false">
        <div class="alerts-empty-state">
          <div class="alerts-empty-icon">🔔</div>
          <div class="alerts-empty-title">No alerts loaded yet</div>
          <p class="alerts-empty-sub">Click "Load Alerts" to fetch live risk advisories for your farm location.</p>
        </div>
      </div>

      <!-- News Section -->
      <div class="alerts-news-section">
        <div class="card alerts-news-card">
          <div class="alerts-news-header">
            <h3 class="section-title" style="margin:0;"><span class="icon">📰</span> Agriculture News</h3>
            <span class="alerts-news-note">Curated agri news with crop tags &amp; sentiment</span>
          </div>
          <div id="news-results" aria-live="polite" aria-busy="false">
            <button class="btn btn-secondary alerts-load-news-btn" id="load-news-btn">
              📡 Load Latest Agriculture News
            </button>
          </div>
        </div>
      </div>

    </div>
  `;
}

export function initAlerts() {
  document.getElementById('load-alerts-btn')?.addEventListener('click', loadAlerts);
  document.getElementById('load-news-btn')?.addEventListener('click', loadNews);
}

async function loadAlerts() {
  const btn = document.getElementById('load-alerts-btn');
  const crop = document.getElementById('alert-crop')?.value || 'rice';
  const season = document.getElementById('alert-season')?.value || 'Kharif';

  document.getElementById('alerts-results')?.setAttribute('aria-busy', 'true');

  btn.textContent = '📡 Locating...';
  btn.classList.add('loading');

  document.getElementById('alerts-results').innerHTML = `
    <div class="alerts-loading-state">
      <div class="spinner alerts-spinner"></div>
      <div class="alerts-loading-text">Fetching live alerts for your location...</div>
      <div class="alerts-loading-sub">Checking available weather, soil estimates, and crop-season rules</div>
    </div>
  `;

  try {
    const pos = await getCurrentPosition();
    const result = await getAlerts(pos.lat, pos.lon, crop, season);
    const alerts = result.alerts || [];
    const degraded = ['partial', 'unavailable'].includes(result.data_quality);
    const dataNote = escapeAlertText(result.data_quality_note || 'Some alert sources may be unavailable.');

    const icons = { danger: '🔴', warning: '🟡', info: '🔵', tip: '✅' };
    const types = { weather: '🌤️', soil: '🧪', satellite: '🛰️', news: '📰', crop: '🌱' };

    if (alerts.length === 0) {
      document.getElementById('alerts-results').innerHTML = degraded ? `
        <div class="alerts-error-card" role="status">
          <div class="alerts-error-icon">📡</div>
          <div class="alerts-error-title">Alert coverage is incomplete</div>
          <p class="alerts-error-msg">${dataNote} An empty list does not mean the farm is risk-free.</p>
        </div>
      ` : `
        <div class="alerts-all-clear-card" role="status">
          <div class="all-clear-icon">✅</div>
          <div class="all-clear-title">No alerts from available sources</div>
          <p class="all-clear-sub">No alert rules were triggered by the data returned for this request. Keep monitoring your field.</p>
          <div class="all-clear-gps">📍 GPS: ${pos.lat.toFixed(3)}, ${pos.lon.toFixed(3)} · Crop: ${escapeAlertText(crop)} · Season: ${escapeAlertText(season)}</div>
          ${result.data_quality === 'estimated' ? `<p class="all-clear-sub">${dataNote}</p>` : ''}
        </div>
      `;
    } else {
      // Count by severity
      const dangerCount   = alerts.filter(a => a.severity === 'danger').length;
      const warningCount  = alerts.filter(a => a.severity === 'warning').length;
      const infoCount     = alerts.filter(a => a.severity === 'info' || a.severity === 'tip').length;

      document.getElementById('alerts-results').innerHTML = `
        ${degraded ? `<div class="alerts-error-card" role="status"><div class="alerts-error-icon">📡</div><div class="alerts-error-title">Some alert sources are unavailable</div><p class="alerts-error-msg">${dataNote}</p></div>` : ''}
        <div class="alerts-summary-bar">
          <div class="alerts-summary-left">
            <h3 class="section-title" style="margin:0;"><span class="icon">🚨</span> ${alerts.length} Active Alert${alerts.length > 1 ? 's' : ''}</h3>
            <span class="alerts-gps-pill">📍 ${pos.lat.toFixed(3)}, ${pos.lon.toFixed(3)}</span>
          </div>
          <div class="alerts-severity-tally">
            ${dangerCount  ? `<span class="severity-tally danger"><span class="tally-dot danger"></span>${dangerCount} Critical</span>` : ''}
            ${warningCount ? `<span class="severity-tally warning"><span class="tally-dot warning"></span>${warningCount} Warning</span>` : ''}
            ${infoCount    ? `<span class="severity-tally info"><span class="tally-dot info"></span>${infoCount} Advisory</span>` : ''}
          </div>
        </div>

        <div class="alerts-cards-list">
          ${alerts.map((a, i) => `
            <div class="alert-banner ${a.severity} alerts-card-enhanced" style="animation-delay:${i * 60}ms;">
              <div class="alert-card-left">
                <span class="alert-icon alert-icon-large">${icons[a.severity] || '⚠️'}</span>
                <span class="alert-type-chip">${types[a.type] || '📌'} ${a.type || 'general'}</span>
              </div>
              <div class="alert-content">
                <div class="alert-card-top-row">
                <div class="alert-title">${escapeAlertText(a.title)}</div>
                  <span class="alert-sev-label ${a.severity}">${a.severity === 'danger' ? 'CRITICAL' : a.severity === 'warning' ? 'WARNING' : a.severity === 'tip' ? 'TIP' : 'INFO'}</span>
                </div>
                <div class="alert-message">${escapeAlertText(a.message)}</div>
                ${a.source ? `
                  <div class="alert-source-row">
                    <span class="alert-source-label">Source: ${escapeAlertText(a.source.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()))}</span>
                  </div>` : ''}
              </div>
            </div>
          `).join('')}
        </div>

        <div class="alerts-footer-note">
          ⚠️ Advisories are rule-based and depend on the sources reported above. Verify critical recommendations with local agriculture officials.
        </div>
      `;
    }

    showToast(degraded ? 'Some alert feeds are unavailable; empty results are not an all-clear.' : `✅ ${alerts.length} alerts loaded`, degraded ? 'warning' : 'success');
  } catch (err) {
    document.getElementById('alerts-results').innerHTML = `
      <div class="alerts-error-card">
        <div class="alerts-error-icon">⚠️</div>
        <div class="alerts-error-title">Could Not Load Alerts</div>
        <p class="alerts-error-msg">${escapeAlertText(err.message)}</p>
        <div class="alerts-error-hint">Ensure GPS permission is granted and try again.</div>
      </div>
    `;
    showToast(err.message, 'error');
  } finally {
    document.getElementById('alerts-results')?.setAttribute('aria-busy', 'false');
    btn.textContent = '📡 Load Alerts for My GPS Location';
    btn.classList.remove('loading');
  }
}

async function loadNews() {
  const newsEl = document.getElementById('news-results');
  newsEl?.setAttribute('aria-busy', 'true');
  newsEl.innerHTML = `
    <div class="alerts-loading-state" style="padding:var(--sp-xl) 0;">
      <div class="spinner alerts-spinner"></div>
      <div class="alerts-loading-text">Fetching agriculture news...</div>
    </div>
  `;

  try {
    const result = await getNews();
    const articles = result.articles || [];

    if (articles.length === 0) {
      newsEl.innerHTML = `
        <div class="alerts-news-empty">
          <div class="alerts-empty-icon" style="font-size:2rem;">📰</div>
          <div style="font-size:0.88rem;color:var(--c-text-secondary);line-height:1.6;">
            ${escapeAlertText(result.note || 'No news available. Add NEWSAPI_KEY to backend/.env for live agriculture news.')}
          </div>
        </div>
      `;
      newsEl.setAttribute('aria-busy', 'false');
      return;
    }

    const sentimentColors = { positive: 'var(--c-success)', negative: '#f87171', neutral: 'var(--c-text-muted)' };
    const alertBadges = { danger: '🔴', warning: '🟡', none: '', info: '🔵' };

    newsEl.innerHTML = `
      <div class="alerts-news-list">
        ${articles.map((art, i) => `
          <div class="alerts-news-item" style="animation-delay:${i * 50}ms;">
            <div class="news-item-main">
              <a href="${safeNewsUrl(art.url)}" target="_blank" rel="noopener noreferrer" class="news-item-title">
                ${alertBadges[art.alert_level] || ''} ${escapeAlertText(art.title)}
              </a>
              ${art.description ? `<p class="news-item-desc">${escapeAlertText(art.description.slice(0,200))}...</p>` : ''}
              <div class="news-item-meta">
                <span class="source-chip">📰 ${escapeAlertText(art.source_name || 'Unknown')}</span>
                ${art.crop_tags ? String(art.crop_tags).split(',').slice(0,3).map(t => `<span class="crop-tag season">${escapeAlertText(t.trim())}</span>`).join('') : ''}
                <span class="news-sentiment-icon" style="color:${sentimentColors[art.sentiment] || 'var(--c-text-muted)'};">
                  ${art.sentiment === 'positive' ? '📈' : art.sentiment === 'negative' ? '📉' : '📊'}
                </span>
                <span class="news-date">
                  ${art.published_at ? new Date(art.published_at).toLocaleDateString('en-IN') : ''}
                </span>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  } catch (err) {
    newsEl.innerHTML = `
      <div class="alerts-error-card" style="margin:0;">
        <p class="alerts-error-msg">⚠️ ${escapeAlertText(err.message)}</p>
      </div>
    `;
  } finally {
    newsEl?.setAttribute('aria-busy', 'false');
  }
}
