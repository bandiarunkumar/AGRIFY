// ============================================================
// Alerts Page — Live farm alerts by GPS
// ============================================================

import { getAlerts, getNews, getCurrentPosition, reverseGeocode } from '../api.js';
import { showToast } from '../voice.js';

export function renderAlerts() {
  return `
    <div class="page-section">
      <div class="page-header">
        <h1>🚨 Farm Alert Center</h1>
        <p>Live alerts from weather, soil, satellite NDVI, agriculture news, and crop calendars</p>
      </div>

      <div class="card" style="margin-bottom:var(--sp-xl);">
        <h3 class="section-title"><span class="icon">📍</span> Get Alerts for My Farm</h3>
        <div style="display:flex;gap:var(--sp-md);flex-wrap:wrap;align-items:flex-end;">
          <div class="form-group" style="min-width:160px;">
            <label>Current Crop</label>
            <select class="form-select" id="alert-crop">
              <option value="rice">Rice</option>
              <option value="wheat">Wheat</option>
              <option value="cotton">Cotton</option>
              <option value="maize">Maize</option>
              <option value="tomato">Tomato</option>
              <option value="potato">Potato</option>
            </select>
          </div>
          <div class="form-group" style="min-width:140px;">
            <label>Season</label>
            <select class="form-select" id="alert-season">
              <option value="Kharif">Kharif</option>
              <option value="Rabi">Rabi</option>
              <option value="Zaid">Zaid</option>
            </select>
          </div>
          <button class="gps-btn" id="load-alerts-btn">📡 Load Alerts for My GPS Location</button>
        </div>
      </div>

      <div id="alerts-results">
        <div style="text-align:center;padding:var(--sp-3xl);color:var(--c-text-muted);">
          <div style="font-size:3rem;margin-bottom:var(--sp-md);">🔔</div>
          <p>Click "Load Alerts" to fetch live alerts for your farm location</p>
        </div>
      </div>

      <!-- News Section -->
      <div style="margin-top:var(--sp-2xl);">
        <div class="card">
          <h3 class="section-title"><span class="icon">📰</span> Agriculture News</h3>
          <div id="news-results">
            <button class="btn btn-secondary" id="load-news-btn">📡 Load Latest Agriculture News</button>
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

  btn.textContent = '📡 Locating...';
  btn.classList.add('loading');

  document.getElementById('alerts-results').innerHTML = `
    <div class="loading-spinner"><div class="spinner"></div><div class="loading-text">Loading alerts...</div></div>
  `;

  try {
    const pos = await getCurrentPosition();
    const result = await getAlerts(pos.lat, pos.lon, crop, season);
    const alerts = result.alerts || [];

    const icons = { danger: '🔴', warning: '🟡', info: '🔵', tip: '✅' };
    const types = { weather: '🌤️', soil: '🧪', satellite: '🛰️', news: '📰', crop: '🌱' };

    if (alerts.length === 0) {
      document.getElementById('alerts-results').innerHTML = `
        <div class="card" style="text-align:center;border-color:rgba(34,197,94,0.3);">
          <div style="font-size:2.5rem;margin-bottom:var(--sp-md);">✅</div>
          <h3 style="color:var(--c-primary-light);">All Clear!</h3>
          <p style="color:var(--c-text-secondary);">No critical alerts for your farm at this time. Continue regular schedule.</p>
        </div>
      `;
    } else {
      document.getElementById('alerts-results').innerHTML = `
        <div style="margin-bottom:var(--sp-md);display:flex;align-items:center;gap:var(--sp-md);">
          <h3 class="section-title" style="margin:0;"><span class="icon">🚨</span> ${alerts.length} Active Alert${alerts.length > 1 ? 's' : ''}</h3>
          <span style="font-size:0.78rem;color:var(--c-text-muted);">GPS: ${pos.lat.toFixed(3)}, ${pos.lon.toFixed(3)}</span>
        </div>
        ${alerts.map(a => `
          <div class="alert-banner ${a.severity}" style="margin-bottom:var(--sp-sm);">
            <span class="alert-icon">${icons[a.severity] || '⚠️'}</span>
            <div class="alert-content">
              <div style="display:flex;align-items:center;gap:var(--sp-sm);margin-bottom:3px;">
                <div class="alert-title">${a.title}</div>
                <span style="font-size:0.7rem;opacity:0.7;">${types[a.type] || ''} ${a.type || ''}</span>
              </div>
              <div class="alert-message">${a.message}</div>
              ${a.source ? `<div style="margin-top:4px;font-size:0.7rem;opacity:0.6;">Source: ${a.source.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</div>` : ''}
            </div>
          </div>
        `).join('')}
      `;
    }

    showToast(`✅ ${alerts.length} alerts loaded`, 'success');
  } catch (err) {
    document.getElementById('alerts-results').innerHTML = `
      <div class="card" style="border-color:rgba(239,68,68,0.3);">
        <p style="color:#f87171;">⚠️ ${err.message}</p>
      </div>
    `;
    showToast(err.message, 'error');
  } finally {
    btn.textContent = '📡 Load Alerts for My GPS Location';
    btn.classList.remove('loading');
  }
}

async function loadNews() {
  const newsEl = document.getElementById('news-results');
  newsEl.innerHTML = `<div class="loading-spinner"><div class="spinner"></div></div>`;

  try {
    const result = await getNews();
    const articles = result.articles || [];

    if (articles.length === 0) {
      newsEl.innerHTML = `
        <div style="color:var(--c-text-muted);font-size:0.875rem;padding:var(--sp-md) 0;">
          ${result.note || 'No news available. Add NEWSAPI_KEY to backend/.env for live agriculture news.'}
        </div>
      `;
      return;
    }

    const sentimentColors = { positive: 'var(--c-success)', negative: '#f87171', neutral: 'var(--c-text-muted)' };
    const alertBadges = { danger: '🔴', warning: '🟡', none: '', info: '🔵' };

    newsEl.innerHTML = `
      <div style="display:flex;flex-direction:column;gap:var(--sp-md);">
        ${articles.map(art => `
          <div style="padding:var(--sp-md);background:var(--c-surface);border-radius:var(--r-lg);border:1px solid var(--c-border);transition:var(--t-fast);"
            onmouseover="this.style.borderColor='var(--c-primary)'" onmouseout="this.style.borderColor='var(--c-border)'">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:var(--sp-md);">
              <div style="flex:1;">
                <a href="${art.url}" target="_blank" rel="noopener" style="color:var(--c-text);font-weight:600;font-size:0.9rem;text-decoration:none;line-height:1.4;display:block;margin-bottom:6px;">
                  ${alertBadges[art.alert_level] || ''} ${art.title}
                </a>
                ${art.description ? `<p style="font-size:0.8rem;color:var(--c-text-secondary);line-height:1.5;margin-bottom:6px;">${art.description.slice(0,200)}...</p>` : ''}
                <div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;">
                  <span class="source-chip">📰 ${art.source_name || 'Unknown'}</span>
                  ${art.crop_tags ? art.crop_tags.split(',').slice(0,3).map(t => `<span class="crop-tag season">${t.trim()}</span>`).join('') : ''}
                  <span style="font-size:0.7rem;color:${sentimentColors[art.sentiment] || 'var(--c-text-muted)'};">
                    ${art.sentiment === 'positive' ? '📈' : art.sentiment === 'negative' ? '📉' : '📊'}
                  </span>
                  <span style="font-size:0.7rem;color:var(--c-text-muted);">
                    ${art.published_at ? new Date(art.published_at).toLocaleDateString('en-IN') : ''}
                  </span>
                </div>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  } catch (err) {
    newsEl.innerHTML = `<p style="color:#f87171;font-size:0.875rem;">⚠️ ${err.message}</p>`;
  }
}
