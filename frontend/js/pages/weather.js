// ============================================================
// Weather Page — GPS-first coordinate-based weather
// With data visualization charts
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
    <div class="page-section">
      <div class="page-header">
        <h1>🌤️ Live Weather</h1>
        <p>GPS-based live weather with 5-day farming forecast, charts, and advisories.</p>
      </div>

      <!-- Input Area -->
      <div class="card" style="margin-bottom:var(--sp-xl);">
        <div style="display:flex;gap:var(--sp-md);flex-wrap:wrap;align-items:flex-end;">
          <div style="flex:1;min-width:200px;">
            <label style="display:block;font-size:0.83rem;font-weight:600;color:var(--c-text-secondary);margin-bottom:var(--sp-sm);">City Name</label>
            <input type="text" class="form-input" id="wx-city" placeholder="Hyderabad, Warangal, Vijayawada..." />
          </div>
          <button class="btn btn-secondary" id="wx-search-btn">🔍 Search</button>
          <button class="gps-btn" id="wx-gps-btn">📡 Use My GPS Location</button>
        </div>
      </div>

      <!-- Results -->
      <div id="weather-results">
        <div style="text-align:center;padding:var(--sp-3xl);color:var(--c-text-muted);">
          <div style="font-size:3rem;margin-bottom:var(--sp-md);">🌤️</div>
          <p>Use GPS or search a city to see live weather and 5-day farming forecast</p>
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
    btn.textContent = '📡 Use My GPS Location';
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
    <div class="loading-spinner">
      <div class="spinner"></div>
      <div class="loading-text">Fetching live weather data...</div>
    </div>
  `;
}

function showError(msg) {
  document.getElementById('weather-results').innerHTML = `
    <div class="card" style="text-align:center;border-color:rgba(239,68,68,0.3);">
      <p style="color:#f87171;">⚠️ ${msg}</p>
    </div>
  `;
}

function renderWeatherResults(weather, forecast, locationName, source, gpsPos = null) {
  const emojiIcon = WX_ICONS[weather.icon] || '🌡️';
  const forecastDays = forecast?.forecast || [];
  const advisory = forecast?.advisory || [];

  let html = '';

  // Hero card
  html += `
    <div class="weather-hero" style="margin-bottom:var(--sp-xl);position:relative;">
      ${source === 'gps' ? '<div class="dq-badge dq-live" style="margin-bottom:var(--sp-sm);">📡 GPS — Coordinates-based</div>' : '<div class="dq-badge dq-reference" style="margin-bottom:var(--sp-sm);">🏙️ City Search</div>'}
      <div class="weather-icon-big">${emojiIcon}</div>
      <div class="weather-temp-big">${weather.temperature}°C</div>
      <div style="font-family:var(--font-display);font-size:1.5rem;font-weight:700;color:var(--c-primary-light);margin-bottom:4px;">${locationName}</div>
      <div style="color:var(--c-text-secondary);font-size:1.05rem;">${weather.description}</div>
      ${source === 'gps' && gpsPos ? `<div style="font-size:0.75rem;color:var(--c-text-muted);margin-top:6px;">📍 ${gpsPos.lat.toFixed(5)}, ${gpsPos.lon.toFixed(5)} (±${Math.round(gpsPos.accuracy)}m)</div>` : ''}
    </div>
  `;

  // Stats grid
  html += `
    <div class="grid-4" style="margin-bottom:var(--sp-xl);">
      <div class="stat-card">
        <div class="stat-icon amber">💧</div>
        <div class="stat-label">Humidity</div>
        <div class="stat-value">${weather.humidity}%</div>
        <div class="stat-sub">${weather.humidity > 80 ? '⚠️ High disease risk' : weather.humidity < 30 ? '⚠️ Very dry' : '✅ Normal'}</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon blue">💨</div>
        <div class="stat-label">Wind Speed</div>
        <div class="stat-value">${weather.wind_speed}<span style="font-size:1rem;"> m/s</span></div>
        <div class="stat-sub">${weather.wind_speed > 10 ? '⚠️ Avoid spraying' : '✅ Good for spray'}</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon green">🌧️</div>
        <div class="stat-label">Rainfall</div>
        <div class="stat-value">${weather.rainfall}<span style="font-size:1rem;"> mm</span></div>
        <div class="stat-sub">Last hour</div>
      </div>
      <div class="stat-card">
        <div class="stat-icon red">📊</div>
        <div class="stat-label">Pressure</div>
        <div class="stat-value">${weather.pressure}<span style="font-size:0.9rem;"> hPa</span></div>
        <div class="stat-sub">Temp: ${weather.temp_min}–${weather.temp_max}°C</div>
      </div>
    </div>
  `;

  // ===== DATA VISUALIZATION SECTION =====
  html += `
    <div class="viz-section-header" style="margin-bottom:var(--sp-lg);">
      <h2 style="font-family:var(--font-display);font-size:1.3rem;font-weight:800;color:var(--c-text);">📊 Weather Data Visualizations</h2>
      <p style="font-size:0.85rem;color:var(--c-text-muted);margin-top:4px;">All charts are generated from live weather data — no duplicate or static content</p>
    </div>
  `;

  // Chart 1: Weather Conditions Polar Area (from charts.js)
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
      <div class="card" style="margin-bottom:var(--sp-xl);">
        <h3 class="section-title"><span class="icon">📅</span> 5-Day Forecast Cards</h3>
        <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:var(--sp-sm);">
          ${forecastDays.map(day => `
            <div class="forecast-card">
              <div style="font-weight:700;font-size:0.85rem;color:var(--c-text);">${day.short_day}</div>
              <div style="font-size:0.72rem;color:var(--c-text-muted);margin-bottom:var(--sp-sm);">${day.date}</div>
              <div style="font-size:1.6rem;margin-bottom:4px;">${WX_ICONS[day.icon] || '🌤️'}</div>
              <div style="font-weight:700;">${day.temp_max}°</div>
              <div style="color:var(--c-text-muted);font-size:0.8rem;">${day.temp_min}°</div>
              ${day.rainfall_total > 0 ? `<div style="color:#60a5fa;font-size:0.75rem;margin-top:4px;">🌧️ ${day.rainfall_total}mm</div>` : ''}
              <div style="font-size:0.7rem;color:var(--c-text-muted);margin-top:4px;">${day.humidity_avg}%</div>
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

  // Farming advisory
  if (advisory.length) {
    const icons = { danger: '🔴', warning: '🟡', info: '🔵', tip: '✅' };
    html += `
      <div class="card">
        <h3 class="section-title"><span class="icon">🌾</span> Farming Advisory</h3>
        ${advisory.map(a => `
          <div class="alert-banner ${a.type}" style="margin-bottom:8px;">
            <span class="alert-icon">${icons[a.type] || '📢'}</span>
            <div class="alert-content">
              <div class="alert-title">${a.title}</div>
              <div class="alert-message">${a.message}</div>
            </div>
          </div>
        `).join('')}
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
