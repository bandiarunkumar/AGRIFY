// ============================================================
// AGRIFY Weather Page — Field Weather Command Center
// GPS-first coordinate-based weather with agricultural analytics
// ============================================================

import { getWeatherByCoords, getForecastByCoords, getWeather, getForecast, getCurrentPosition, reverseGeocode } from '../api.js';
import { showToast } from '../voice.js';
import { t } from '../i18n.js';
import { createWeatherGaugeChart } from '../charts.js';

const WX_ICONS = {
  '01d': '☀️', '01n': '🌙', '02d': '⛅', '02n': '🌥️',
  '03d': '☁️', '03n': '☁️', '04d': '☁️', '04n': '☁️',
  '09d': '🌧️', '09n': '🌧️', '10d': '🌦️', '10n': '🌧️',
  '11d': '⛈️', '11n': '⛈️', '13d': '❄️', '13n': '❄️',
  '50d': '🌫️', '50n': '🌫️',
};

// Active chart instances for this page
const weatherCharts = {};
function destroyWeatherChart(id) {
  if (weatherCharts[id]) { weatherCharts[id].destroy(); delete weatherCharts[id]; }
}

export function renderWeather() {
  return `
    <div class="page-section weather-page">
      <!-- Observatory Hero Header -->
      <div class="weather-hero-header">
        <div class="weather-badge">
          <span class="badge-dot"></span>
          <span>AGRIFY MICROCLIMATE OBSERVATORY</span>
        </div>
        <h1 class="weather-title">🌤️ Real-Time Field Weather Intelligence</h1>
        <p class="weather-subtitle">
          GPS coordinate-precision meteorology, 5-day agricultural forecast modeling, and agronomic spraying & disease advisories.
        </p>
        <div class="weather-trust-strip">
          <span class="trust-pill"><span class="pill-icon">📍</span> GPS Micro-Coordinates</span>
          <span class="trust-pill"><span class="pill-icon">🌦️</span> OpenWeather Real-Time Feeds</span>
          <span class="trust-pill"><span class="pill-icon">🌾</span> Agricultural Spray Index</span>
          <span class="trust-pill"><span class="pill-icon">📈</span> 5-Day Trend Analytics</span>
        </div>
      </div>

      <!-- Location & Search Control Card -->
      <div class="card wx-search-card" style="margin-bottom:var(--sp-xl);">
        <div class="wx-search-form">
          <div class="wx-input-wrap">
            <label for="wx-city" class="wx-input-label">Search Indian City / District</label>
            <div class="wx-input-inner">
              <span class="wx-input-icon">🔍</span>
              <input type="text" class="form-input" id="wx-city" placeholder="Hyderabad, Warangal, Vijayawada, Guntur..." />
            </div>
          </div>
          <div class="wx-btn-group">
            <button class="btn btn-secondary" id="wx-search-btn">🔍 Search</button>
            <button class="gps-btn" id="wx-gps-btn">
              <span class="gps-icon-live">📡</span>
              <span>Use My GPS Location</span>
            </button>
          </div>
        </div>
        <div class="wx-search-hint">
          <span>💡 <strong>GPS Precision:</strong> Coordinates fetch hyper-local microclimate data for your exact field rather than broad municipal averages.</span>
        </div>
      </div>

      <!-- Results Container -->
      <div id="weather-results">
        <div class="card wx-empty-card">
          <div class="wx-empty-icon-wrap">
            <span class="wx-empty-satellite">🛰️</span>
            <span class="wx-empty-cloud">🌤️</span>
          </div>
          <h3 class="wx-empty-title">Awaiting Field Location</h3>
          <p class="wx-empty-desc">
            Acquire your device GPS or search an Indian district above to view live microclimate vitals, 5-day farming forecasts, and spray advisories.
          </p>
          <div class="wx-empty-features">
            <div class="wx-feat-item">
              <span class="wx-feat-icon">💨</span>
              <span class="wx-feat-text">Spray Timing Guidance</span>
            </div>
            <div class="wx-feat-item">
              <span class="wx-feat-icon">💧</span>
              <span class="wx-feat-text">Disease Risk from Humidity</span>
            </div>
            <div class="wx-feat-item">
              <span class="wx-feat-icon">🌧️</span>
              <span class="wx-feat-text">Precipitation Scheduling</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

export function initWeather() {
  document.getElementById('wx-gps-btn')?.addEventListener('click', fetchByGPS);
  document.getElementById('wx-search-btn')?.addEventListener('click', fetchByCity);
  document.getElementById('wx-city')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') fetchByCity();
  });
}

async function fetchByGPS() {
  const btn = document.getElementById('wx-gps-btn');
  btn.textContent = '📡 Locating...';
  btn.classList.add('loading');

  showLoading();
  try {
    const pos = await getCurrentPosition();
    const [weather, forecast, geo] = await Promise.all([
      getWeatherByCoords(pos.lat, pos.lon),
      getForecastByCoords(pos.lat, pos.lon),
      reverseGeocode(pos.lat, pos.lon),
    ]);

    if (weather.error) throw new Error(weather.error);
    if (forecast.error) throw new Error(forecast.error);

    const locationName = [geo.village, geo.district, geo.state].filter(Boolean).join(', ')
      || weather.city_name || `${pos.lat.toFixed(3)}, ${pos.lon.toFixed(3)}`;

    renderWeatherResults(weather, forecast, locationName, 'gps', pos);
    showToast(`✅ GPS weather loaded for ${locationName}`, 'success');
  } catch (err) {
    showError(err.message);
    showToast(err.message, 'error');
  } finally {
    btn.innerHTML = `<span class="gps-icon-live">📡</span> <span>Use My GPS Location</span>`;
    btn.classList.remove('loading');
  }
}

async function fetchByCity() {
  const city = document.getElementById('wx-city')?.value.trim();
  if (!city) { showToast('Enter a city name', 'error'); return; }

  const btn = document.getElementById('wx-search-btn');
  btn.textContent = 'Loading...';
  btn.disabled = true;
  showLoading();

  try {
    const [weather, forecast] = await Promise.all([
      getWeather(city),
      getForecast(city),
    ]);

    if (weather.error) throw new Error(weather.error);
    if (forecast.error) throw new Error(forecast.error);

    renderWeatherResults(weather, forecast, weather.city_name || city, 'city');
  } catch (err) {
    showError(err.message);
    showToast(err.message, 'error');
  } finally {
    btn.textContent = '🔍 Search';
    btn.disabled = false;
  }
}

function showLoading() {
  document.getElementById('weather-results').innerHTML = `
    <div class="card wx-loading-card">
      <div class="loading-spinner-wrap">
        <div class="spinner"></div>
      </div>
      <div class="loading-heading">Acquiring Meteorological Telemetry</div>
      <div class="loading-subheading">🌐 Fetching live weather & atmospheric data...</div>
      <div class="loading-footnote">
        Synchronizing ground station feeds and satellite microclimate models.
      </div>
      <div class="loading-pills-row">
        <span class="loading-pill active">📍 Location Pinpointed</span>
        <span class="loading-pill active">🌤️ Fetching Atmosphere</span>
        <span class="loading-pill">📊 Computing Agronomic Forecast</span>
      </div>
    </div>
  `;
}

function showError(msg) {
  document.getElementById('weather-results').innerHTML = `
    <div class="card wx-error-card">
      <div class="error-badge-icon">⚠️</div>
      <h3 class="error-title">Weather Retrieval Failed</h3>
      <p class="error-desc">${msg}</p>
      <div class="error-footnote">
        Please check your network connection, search query, or device GPS location permissions and try again.
      </div>
    </div>
  `;
}

function renderWeatherResults(weather, forecast, locationName, source, gpsPos = null) {
  const emojiIcon = WX_ICONS[weather.icon] || '🌡️';
  const forecastDays = forecast?.forecast || [];
  const advisory = forecast?.advisory || [];

  let html = '';

  // ---- HERO PRESENT-CONDITION CARD (Focal Point) ----
  html += `
    <div class="weather-hero" style="margin-bottom:var(--sp-xl);position:relative;">
      <div class="weather-hero-top-bar">
        ${source === 'gps' 
          ? '<div class="dq-badge dq-live"><span class="badge-dot"></span> 📡 GPS — Coordinates-Based Telemetry</div>' 
          : '<div class="dq-badge dq-reference">🏙️ City Search Reference</div>'}
        <span class="weather-updated-tag">🕒 Live Observation</span>
      </div>

      <div class="weather-hero-body">
        <div class="weather-icon-big">${emojiIcon}</div>
        <div class="weather-temp-big">${weather.temperature}°C</div>
        <div class="weather-location-name">📍 ${locationName}</div>
        <div class="weather-condition-desc">${weather.description}</div>
        ${source === 'gps' && gpsPos ? `<div class="weather-coords-pill">📍 Lat: ${gpsPos.lat.toFixed(5)}, Lon: ${gpsPos.lon.toFixed(5)} <span class="accuracy-tag">(±${Math.round(gpsPos.accuracy)}m accuracy)</span></div>` : ''}
      </div>
    </div>
  `;

  // ---- STATS / VITALS GRID ----
  html += `
    <div class="grid-4 weather-vitals-grid" style="margin-bottom:var(--sp-xl);">
      <div class="stat-card wx-stat-card">
        <div class="stat-icon amber">💧</div>
        <div class="stat-label">Humidity</div>
        <div class="stat-value">${weather.humidity}%</div>
        <div class="stat-sub ${weather.humidity > 80 ? 'sub-danger' : weather.humidity < 30 ? 'sub-warning' : 'sub-normal'}">
          ${weather.humidity > 80 ? '⚠️ High disease risk' : weather.humidity < 30 ? '⚠️ Very dry' : '✅ Normal range'}
        </div>
      </div>
      <div class="stat-card wx-stat-card">
        <div class="stat-icon blue">💨</div>
        <div class="stat-label">Wind Velocity</div>
        <div class="stat-value">${weather.wind_speed}<span class="stat-unit"> m/s</span></div>
        <div class="stat-sub ${weather.wind_speed > 10 ? 'sub-warning' : 'sub-normal'}">
          ${weather.wind_speed > 10 ? '⚠️ Avoid spraying' : '✅ Good for spray'}
        </div>
      </div>
      <div class="stat-card wx-stat-card">
        <div class="stat-icon green">🌧️</div>
        <div class="stat-label">Precipitation</div>
        <div class="stat-value">${weather.rainfall}<span class="stat-unit"> mm</span></div>
        <div class="stat-sub">Past hour accumulation</div>
      </div>
      <div class="stat-card wx-stat-card">
        <div class="stat-icon red">📊</div>
        <div class="stat-label">Atmospheric Pressure</div>
        <div class="stat-value">${weather.pressure}<span class="stat-unit"> hPa</span></div>
        <div class="stat-sub font-mono">Range: ${weather.temp_min}–${weather.temp_max}°C</div>
      </div>
    </div>
  `;

  // ---- FARMING ADVISORY (Prominently Framed) ----
  if (advisory.length) {
    const icons = { danger: '🔴', warning: '🟡', info: '🔵', tip: '✅' };
    html += `
      <div class="card wx-advisory-card" style="margin-bottom:var(--sp-xl);">
        <h3 class="section-title"><span class="icon">🌾</span> Agricultural Weather Advisory</h3>
        <div class="advisory-list">
          ${advisory.map(a => `
            <div class="alert-banner ${a.type}">
              <span class="alert-icon">${icons[a.type] || '📢'}</span>
              <div class="alert-content">
                <div class="alert-title">${a.title}</div>
                <div class="alert-message">${a.message}</div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  // ===== DATA VISUALIZATION SECTION =====
  html += `
    <div class="viz-section-header" style="margin-bottom:var(--sp-lg);">
      <h2 style="font-family:var(--font-display);font-size:1.3rem;font-weight:800;color:var(--c-text);">📊 Weather Data Visualizations</h2>
      <p style="font-size:0.85rem;color:var(--c-text-muted);margin-top:4px;">All charts are generated from live weather data — no duplicate or static content</p>
    </div>
  `;

  // Chart 1: Weather Conditions Polar Area & Chart 2: Temperature Breakdown
  html += `
    <div class="grid-2" style="margin-bottom:var(--sp-xl);">
      <div class="card viz-card">
        <h3 class="section-title"><span class="icon">🌡️</span> Current Conditions Radar</h3>
        <p class="viz-desc">Polar area chart showing the relative magnitude of temperature (${weather.temperature}°C), humidity (${weather.humidity}%), wind (${weather.wind_speed} m/s), and cloud cover (${weather.clouds || 0}%).</p>
        <div class="chart-container" style="height:280px;display:flex;align-items:center;justify-content:center;">
          <canvas id="wx-polar-chart"></canvas>
        </div>
        <div class="viz-insight">
          <span class="viz-insight-icon">💡</span>
          <span>Source: OpenWeatherMap live API — fetched at ${new Date().toLocaleTimeString()}</span>
        </div>
      </div>

      <!-- Chart 2: Temperature Feels Like Gauge -->
      <div class="card viz-card">
        <h3 class="section-title"><span class="icon">🌡️</span> Temperature Breakdown</h3>
        <p class="viz-desc">Comparing actual temperature, feels-like temperature, and day's min/max range.</p>
        <div class="chart-container" style="height:280px;">
          <canvas id="wx-temp-chart"></canvas>
        </div>
        <div class="viz-insight">
          <span class="viz-insight-icon">💡</span>
          <span>Feels like ${weather.feels_like || weather.temperature}°C. ${(weather.feels_like || weather.temperature) > weather.temperature ? 'Heat index elevated — drink more water.' : 'Comfortable for outdoor farming.'}</span>
        </div>
      </div>
    </div>
  `;

  // 5-day forecast
  if (forecastDays.length) {
    // Chart 3: Forecast Temperature Line Chart
    html += `
      <div class="card viz-card" style="margin-bottom:var(--sp-xl);">
        <h3 class="section-title"><span class="icon">📈</span> 5-Day Temperature & Rainfall Trend</h3>
        <p class="viz-desc">Line chart showing forecasted max/min temperatures and expected rainfall for the next 5 days.</p>
        <div class="chart-container" style="height:300px;">
          <canvas id="wx-forecast-chart"></canvas>
        </div>
        <div class="viz-insight">
          <span class="viz-insight-icon">🌾</span>
          <span>
            ${forecastDays.some(d => d.rainfall_total > 5) ? '🌧️ Rain expected — delay fertilizer application and harvesting.' : '☀️ Dry spell ahead — consider increasing irrigation frequency.'}
            Max temp: ${Math.max(...forecastDays.map(d => d.temp_max))}°C, Min temp: ${Math.min(...forecastDays.map(d => d.temp_min))}°C.
          </span>
        </div>
      </div>
    `;

    // Forecast cards
    html += `
      <div class="card wx-forecast-container" style="margin-bottom:var(--sp-xl);">
        <div class="forecast-header-wrap">
          <h3 class="section-title"><span class="icon">📅</span> 5-Day Forecast Cards</h3>
          <span class="forecast-subtitle">Daily agricultural outlook and precipitation expectations</span>
        </div>
        <div class="forecast-cards-grid">
          ${forecastDays.map(day => `
            <div class="forecast-card">
              <div class="forecast-day-name">${day.short_day}</div>
              <div class="forecast-date-str">${day.date}</div>
              <div class="forecast-icon-wrap">${WX_ICONS[day.icon] || '🌤️'}</div>
              <div class="forecast-temp-max">${day.temp_max}°</div>
              <div class="forecast-temp-min">${day.temp_min}°</div>
              ${day.rainfall_total > 0 ? `<div class="forecast-rain-pill">🌧️ ${day.rainfall_total}mm</div>` : '<div class="forecast-dry-pill">Dry</div>'}
              <div class="forecast-humidity-text">💧 ${day.humidity_avg}%</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    // Chart 4: Humidity Across Days
    html += `
      <div class="card viz-card" style="margin-bottom:var(--sp-xl);">
        <h3 class="section-title"><span class="icon">💧</span> Humidity & Wind Forecast</h3>
        <p class="viz-desc">Bar chart comparing humidity levels and wind conditions across the 5-day forecast.</p>
        <div class="chart-container" style="height:260px;">
          <canvas id="wx-humidity-chart"></canvas>
        </div>
        <div class="viz-insight">
          <span class="viz-insight-icon">🐛</span>
          <span>${forecastDays.some(d => d.humidity_avg > 80) ? '⚠️ High humidity days detected — increased fungal disease risk. Consider preventive spray.' : '✅ Humidity levels are moderate — low disease pressure expected.'}</span>
        </div>
      </div>
    `;
  }

  document.getElementById('weather-results').innerHTML = html;

  // ===== RENDER ALL CHARTS WITH REAL DATA =====
  // Chart 1: Polar Area — current conditions
  createWeatherGaugeChart('wx-polar-chart', weather);

  // Chart 2: Temperature breakdown bar chart
  renderTempChart(weather);

  // Chart 3: Forecast temperature line chart
  if (forecastDays.length) {
    renderForecastChart(forecastDays);
    renderHumidityChart(forecastDays);
  }
}

// ============================================================
// WEATHER-SPECIFIC CHARTS (unique to this page, not duplicates)
// ============================================================

function renderTempChart(weather) {
  const ctx = document.getElementById('wx-temp-chart')?.getContext('2d');
  if (!ctx) return;
  destroyWeatherChart('wx-temp-chart');

  const feelsLike = weather.feels_like || weather.temperature;

  weatherCharts['wx-temp-chart'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Min Temp', 'Actual', 'Feels Like', 'Max Temp'],
      datasets: [{
        label: 'Temperature (°C)',
        data: [weather.temp_min, weather.temperature, feelsLike, weather.temp_max],
        backgroundColor: [
          'rgba(59, 130, 246, 0.7)',
          'rgba(22, 163, 74, 0.7)',
          'rgba(245, 158, 11, 0.7)',
          'rgba(239, 68, 68, 0.7)',
        ],
        borderColor: ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444'],
        borderWidth: 2,
        borderRadius: 8,
        barPercentage: 0.65,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 20, 0.95)',
          titleColor: '#f0fdf4',
          bodyColor: '#f0fdf4',
          borderColor: 'rgba(34, 197, 94, 0.12)',
          borderWidth: 1,
          padding: 12,
          callbacks: { label: (ctx) => `${ctx.raw}°C` }
        },
        datalabels: {
          anchor: 'end',
          align: 'end',
          color: '#f0fdf4',
          font: { family: 'Inter', size: 13, weight: '700' },
          formatter: (v) => `${v}°C`,
        }
      },
      scales: {
        x: {
          ticks: { color: '#f0fdf4', font: { family: 'Inter', size: 12, weight: '600' } },
          grid: { display: false },
          border: { color: 'rgba(34, 197, 94, 0.12)' },
        },
        y: {
          beginAtZero: false,
          ticks: { color: '#6b7280', font: { size: 11 }, callback: v => v + '°C' },
          grid: { color: 'rgba(34, 197, 94, 0.06)' },
          border: { display: false },
        }
      },
      animation: { duration: 1000, easing: 'easeOutCubic' },
    },
    plugins: [ChartDataLabels],
  });
}

function renderForecastChart(days) {
  const ctx = document.getElementById('wx-forecast-chart')?.getContext('2d');
  if (!ctx) return;
  destroyWeatherChart('wx-forecast-chart');

  const labels = days.map(d => d.short_day);
  const maxTemps = days.map(d => d.temp_max);
  const minTemps = days.map(d => d.temp_min);
  const rainfall = days.map(d => d.rainfall_total || 0);

  weatherCharts['wx-forecast-chart'] = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Max Temp (°C)',
          data: maxTemps,
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          borderWidth: 3,
          pointBackgroundColor: '#ef4444',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 9,
          fill: false,
          tension: 0.35,
          yAxisID: 'y',
        },
        {
          label: 'Min Temp (°C)',
          data: minTemps,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderWidth: 3,
          pointBackgroundColor: '#3b82f6',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 9,
          fill: false,
          tension: 0.35,
          yAxisID: 'y',
        },
        {
          label: 'Rainfall (mm)',
          data: rainfall,
          type: 'bar',
          backgroundColor: 'rgba(96, 165, 250, 0.35)',
          borderColor: '#60a5fa',
          borderWidth: 1.5,
          borderRadius: 6,
          yAxisID: 'y1',
          barPercentage: 0.5,
          order: 2,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#f0fdf4', font: { family: 'Inter', size: 12, weight: '500' }, padding: 16, usePointStyle: true }
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 20, 0.95)',
          titleColor: '#f0fdf4',
          bodyColor: '#f0fdf4',
          borderColor: 'rgba(34, 197, 94, 0.12)',
          borderWidth: 1,
          padding: 14,
          callbacks: {
            label: (ctx) => {
              if (ctx.dataset.label.includes('Rainfall')) return `Rain: ${ctx.raw}mm`;
              return `${ctx.dataset.label}: ${ctx.raw}°C`;
            }
          }
        },
      },
      scales: {
        x: {
          ticks: { color: '#f0fdf4', font: { family: 'Inter', size: 12, weight: '600' } },
          grid: { display: false },
          border: { color: 'rgba(34, 197, 94, 0.12)' },
        },
        y: {
          type: 'linear',
          position: 'left',
          title: { display: true, text: 'Temperature (°C)', color: '#f0fdf4', font: { family: 'Inter', size: 12, weight: '600' } },
          ticks: { color: '#6b7280', font: { size: 11 }, callback: v => v + '°C' },
          grid: { color: 'rgba(34, 197, 94, 0.06)' },
          border: { display: false },
        },
        y1: {
          type: 'linear',
          position: 'right',
          title: { display: true, text: 'Rainfall (mm)', color: '#60a5fa', font: { family: 'Inter', size: 12, weight: '600' } },
          beginAtZero: true,
          ticks: { color: '#60a5fa', font: { size: 11 }, callback: v => v + 'mm' },
          grid: { display: false },
          border: { display: false },
        }
      },
      animation: { duration: 1400, easing: 'easeOutQuart' },
    }
  });
}

function renderHumidityChart(days) {
  const ctx = document.getElementById('wx-humidity-chart')?.getContext('2d');
  if (!ctx) return;
  destroyWeatherChart('wx-humidity-chart');

  const labels = days.map(d => d.short_day);
  const humidity = days.map(d => d.humidity_avg || 0);
  const wind = days.map(d => d.wind_avg || d.wind_speed || 0);

  const humidityColors = humidity.map(h => {
    if (h > 80) return 'rgba(239, 68, 68, 0.7)';
    if (h > 60) return 'rgba(245, 158, 11, 0.7)';
    return 'rgba(22, 163, 74, 0.7)';
  });

  weatherCharts['wx-humidity-chart'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Humidity (%)',
          data: humidity,
          backgroundColor: humidityColors,
          borderColor: humidityColors.map(c => c.replace(/[\d.]+\)$/, '1)')),
          borderWidth: 1.5,
          borderRadius: 6,
          barPercentage: 0.6,
          yAxisID: 'y',
        },
        {
          label: 'Wind Speed (m/s)',
          data: wind,
          type: 'line',
          borderColor: '#06b6d4',
          backgroundColor: 'rgba(6, 182, 212, 0.1)',
          borderWidth: 2.5,
          pointBackgroundColor: '#06b6d4',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 8,
          tension: 0.3,
          yAxisID: 'y1',
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#f0fdf4', font: { family: 'Inter', size: 12, weight: '500' }, padding: 16, usePointStyle: true }
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 20, 0.95)',
          titleColor: '#f0fdf4',
          bodyColor: '#f0fdf4',
          borderColor: 'rgba(34, 197, 94, 0.12)',
          borderWidth: 1,
          padding: 12,
        },
        datalabels: {
          display: (ctx) => ctx.datasetIndex === 0,
          anchor: 'end',
          align: 'end',
          color: '#f0fdf4',
          font: { family: 'Inter', size: 11, weight: '700' },
          formatter: (v) => `${v}%`,
        }
      },
      scales: {
        x: {
          ticks: { color: '#f0fdf4', font: { family: 'Inter', size: 12, weight: '600' } },
          grid: { display: false },
          border: { color: 'rgba(34, 197, 94, 0.12)' },
        },
        y: {
          type: 'linear',
          position: 'left',
          title: { display: true, text: 'Humidity (%)', color: '#f0fdf4', font: { family: 'Inter', size: 12, weight: '600' } },
          beginAtZero: true,
          max: 100,
          ticks: { color: '#6b7280', font: { size: 11 }, callback: v => v + '%' },
          grid: { color: 'rgba(34, 197, 94, 0.06)' },
          border: { display: false },
        },
        y1: {
          type: 'linear',
          position: 'right',
          title: { display: true, text: 'Wind (m/s)', color: '#06b6d4', font: { family: 'Inter', size: 12, weight: '600' } },
          beginAtZero: true,
          ticks: { color: '#06b6d4', font: { size: 11 } },
          grid: { display: false },
          border: { display: false },
        }
      },
      animation: { duration: 1100, easing: 'easeOutCubic' },
    },
    plugins: [ChartDataLabels],
  });
}
