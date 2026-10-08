// ============================================================
// AGRIFY Market Intelligence — Live Agmarknet & Mandi Analytics
// Enhanced: Telangana districts, AP districts, all Indian mandis
// ============================================================

import { getMarketPrices } from '../api.js';
import { showToast } from '../voice.js';
import {
  createMarketPriceChart,
  createPriceDistributionChart,
  createMarketSharePieChart,
  createMSPComparisonChart
} from '../charts.js';

// Indian states for dropdown
const INDIAN_STATES = [
  '', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar',
  'Chhattisgarh', 'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh',
  'Jharkhand', 'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra',
  'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha',
  'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana',
  'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
  'Delhi', 'Chandigarh', 'Jammu and Kashmir',
];

// Telangana districts for dropdown
const TELANGANA_DISTRICTS = [
  '', 'Adilabad', 'Bhadradri Kothagudem', 'Hanamkonda', 'Hyderabad',
  'Jagtial', 'Jangaon', 'Jogulamba Gadwal', 'Kamareddy', 'Karimnagar',
  'Khammam', 'Kumuram Bheem', 'Mahabubabad', 'Mahabubnagar',
  'Mancherial', 'Medak', 'Medchal-Malkajgiri', 'Mulugu',
  'Nagarkurnool', 'Nalgonda', 'Narayanpet', 'Nirmal', 'Nizamabad',
  'Peddapalli', 'Rajanna Sircilla', 'Rangareddy', 'Sangareddy',
  'Siddipet', 'Suryapet', 'Vikarabad', 'Wanaparthy',
  'Warangal', 'Warangal Rural', 'Yadadri Bhuvanagiri',
];

// AP districts
const AP_DISTRICTS = [
  '', 'Anantapur', 'Chittoor', 'East Godavari', 'Guntur',
  'Krishna', 'Kurnool', 'Prakasam', 'Srikakulam',
  'Visakhapatnam', 'West Godavari',
];

function getDistrictsForState(state) {
  if (state === 'Telangana') return TELANGANA_DISTRICTS;
  if (state === 'Andhra Pradesh') return AP_DISTRICTS;
  return null;
}

export function renderMarket() {
  return `
    <div class="page-section market-page">
      <!-- Market Hero Header -->
      <div class="market-hero-header">
        <div class="market-badge">
          <span class="badge-dot"></span>
          <span>AGRIFY MANDI INTELLIGENCE ENGINE</span>
        </div>
        <h1 class="market-title">📊 Real-Time Mandi Market Intelligence</h1>
        <p class="market-subtitle">
          Live wholesale market (mandi) commodity arrivals and modal prices across Telangana, Andhra Pradesh, and national agricultural markets.
        </p>
        <div class="market-trust-strip">
          <span class="trust-pill"><span class="pill-icon">🏛️</span> Agmarknet & data.gov.in Verified</span>
          <span class="trust-pill"><span class="pill-icon">⚖️</span> Modal, Min & Max Pricing</span>
          <span class="trust-pill"><span class="pill-icon">📈</span> District Volatility Analytics</span>
          <span class="trust-pill"><span class="pill-icon">📋</span> MSP Benchmark Protection</span>
        </div>
      </div>

      <!-- Search & Filter Card -->
      <div class="card market-query-card" style="margin-bottom:var(--sp-xl);">
        <h3 class="section-title"><span class="icon">🔍</span> Search Live Mandi Prices</h3>
        <div class="form-grid">
          <div class="form-group">
            <label for="market-crop">Commodity / Crop</label>
            <select class="form-select" id="market-crop">
              <optgroup label="Cereals & Grains">
                <option value="rice">Rice / Paddy</option>
                <option value="wheat">Wheat</option>
                <option value="maize">Maize (Corn)</option>
                <option value="jowar">Jowar (Sorghum)</option>
                <option value="bajra">Bajra (Pearl Millet)</option>
              </optgroup>
              <optgroup label="Pulses">
                <option value="chickpea">Bengal Gram (Chana)</option>
                <option value="lentil">Lentil (Masur)</option>
                <option value="mungbean">Green Gram (Moong)</option>
                <option value="blackgram">Black Gram (Urad)</option>
                <option value="pigeonpeas">Pigeon Pea (Arhar/Tur)</option>
              </optgroup>
              <optgroup label="Vegetables">
                <option value="tomato" selected>Tomato</option>
                <option value="potato">Potato</option>
                <option value="onion">Onion</option>
                <option value="green_chilli">Green Chilli</option>
                <option value="brinjal">Brinjal</option>
                <option value="cabbage">Cabbage</option>
                <option value="cauliflower">Cauliflower</option>
                <option value="capsicum">Capsicum</option>
                <option value="ladies_finger">Ladies Finger (Bhindi)</option>
                <option value="beans">Beans</option>
                <option value="bitter_gourd">Bitter Gourd</option>
                <option value="bottle_gourd">Bottle Gourd</option>
                <option value="ridge_gourd">Ridge Gourd</option>
                <option value="cucumber">Cucumber</option>
                <option value="drumstick">Drumstick</option>
                <option value="spinach">Spinach</option>
                <option value="coriander">Coriander (Leaves)</option>
                <option value="carrot">Carrot</option>
              </optgroup>
              <optgroup label="Oilseeds & Cash Crops">
                <option value="soybean">Soybean</option>
                <option value="groundnut">Groundnut</option>
                <option value="cotton">Cotton / Kapas</option>
                <option value="coconut">Coconut</option>
                <option value="sunflower">Sunflower</option>
                <option value="sesame">Sesame (Til)</option>
                <option value="castor">Castor Seed</option>
                <option value="sugarcane">Sugarcane</option>
              </optgroup>
              <optgroup label="Spices">
                <option value="chilli">Red Chilli (Dry)</option>
                <option value="turmeric">Turmeric</option>
                <option value="coriander">Coriander</option>
              </optgroup>
              <optgroup label="Fruits">
                <option value="banana">Banana</option>
                <option value="mango">Mango</option>
                <option value="apple">Apple</option>
                <option value="grapes">Grapes</option>
                <option value="orange">Orange</option>
                <option value="pomegranate">Pomegranate</option>
                <option value="watermelon">Watermelon</option>
                <option value="papaya">Papaya</option>
              </optgroup>
            </select>
          </div>
          <div class="form-group">
            <label for="market-state">State</label>
            <select class="form-select" id="market-state">
              ${INDIAN_STATES.map(s => `<option value="${s}" ${s === 'Telangana' ? 'selected' : ''}>${s || '— All India —'}</option>`).join('')}
            </select>
          </div>
          <div class="form-group">
            <label for="market-district-select">District <span class="hint">(optional — leave empty for all districts)</span></label>
            <select class="form-select" id="market-district-select">
              ${TELANGANA_DISTRICTS.map(d => `<option value="${d}">${d || '— All Districts —'}</option>`).join('')}
            </select>
            <input type="text" class="form-input" id="market-district-input" placeholder="e.g. Hyderabad, Guntur" style="display:none;" />
          </div>
          <div class="form-group market-search-action">
            <button class="btn btn-primary btn-full" id="market-search-btn">📡 Fetch Live Prices</button>
          </div>
        </div>
      </div>

      <!-- Results Container -->
      <div id="market-results">
        <div class="card market-empty-card">
          <div class="market-empty-icon-wrap">
            <span class="market-empty-satellite">📡</span>
            <span class="market-empty-mandi">🏛️</span>
          </div>
          <h3 class="market-empty-title">Select Commodity & Mandi Territory</h3>
          <p class="market-empty-desc">
            Select a crop and market territory above, then click <strong>"Fetch Live Prices"</strong> to view today's real wholesale mandi rates, peak selling points, and price distribution.
          </p>
          <div class="market-empty-features">
            <div class="market-feat-item">
              <span class="market-feat-icon">🏆</span>
              <span class="market-feat-text">Peak Market Identification</span>
            </div>
            <div class="market-feat-item">
              <span class="market-feat-icon">⚖️</span>
              <span class="market-feat-text">Modal vs Minimum Spread</span>
            </div>
            <div class="market-feat-item">
              <span class="market-feat-icon">📋</span>
              <span class="market-feat-text">Government MSP Benchmarks</span>
            </div>
          </div>
        </div>
      </div>

      <!-- MSP Reference -->
      <div class="card market-msp-card" style="margin-top:var(--sp-xl);">
        <h3 class="section-title"><span class="icon">📋</span> MSP Reference Benchmark (2024-25)</h3>
        <p style="font-size:0.85rem;color:var(--c-text-muted);margin-bottom:var(--sp-md);">
          Official Minimum Support Prices recommended by the Commission for Agricultural Costs and Prices (CACP).
        </p>
        <div style="overflow-x:auto;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Crop</th>
                <th>MSP (₹/quintal)</th>
                <th>MSP (₹/kg)</th>
                <th>Season</th>
              </tr>
            </thead>
            <tbody>
              ${[
                ['Rice (Common)', '2300', '23', 'Kharif'],
                ['Wheat', '2275', '22.75', 'Rabi'],
                ['Maize', '2090', '20.90', 'Kharif'],
                ['Cotton (Medium)', '7020', '70.20', 'Kharif'],
                ['Soybean', '4600', '46', 'Kharif'],
                ['Groundnut', '6783', '67.83', 'Kharif'],
                ['Chickpea', '5440', '54.40', 'Rabi'],
                ['Lentil (Masur)', '6425', '64.25', 'Rabi'],
                ['Pigeon Pea', '7550', '75.50', 'Kharif'],
                ['Sugarcane (FRP)', '340', '3.40', 'Year-round'],
                ['Red Chilli (Dry)', '~16000', '~160', 'Kharif/Rabi'],
                ['Turmeric', '~12000', '~120', 'Kharif'],
              ].map(([crop, quintal, kg, season]) => `
                <tr>
                  <td style="font-weight:600;">${crop}</td>
                  <td style="color:var(--c-primary-light);font-weight:700;">₹${quintal}</td>
                  <td style="font-weight:600;">₹${kg}/kg</td>
                  <td><span class="crop-tag season">${season}</span></td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
        <div style="font-size:0.75rem;color:var(--c-text-muted);margin-top:var(--sp-md);line-height:1.5;">
          📋 Source: Cabinet Committee on Economic Affairs (CCEA), Govt. of India 2024-25.<br>
          Actual mandi prices may fluctuate with daily market arrivals. Verify at <a href="https://agmarknet.gov.in" target="_blank" rel="noopener" style="color:var(--c-primary-light);">agmarknet.gov.in</a>
        </div>
      </div>
    </div>
  `;
}

export function initMarket() {
  document.getElementById('market-search-btn')?.addEventListener('click', searchMarket);

  // State change → update district dropdown
  const stateSelect = document.getElementById('market-state');
  stateSelect?.addEventListener('change', () => {
    updateDistrictSelector(stateSelect.value);
  });

  // Enter key on text input
  document.getElementById('market-district-input')?.addEventListener('keydown', e => {
    if (e.key === 'Enter') searchMarket();
  });
}

function updateDistrictSelector(state) {
  const distSelect = document.getElementById('market-district-select');
  const distInput = document.getElementById('market-district-input');

  const districts = getDistrictsForState(state);

  if (districts) {
    // Show dropdown
    distSelect.style.display = '';
    distInput.style.display = 'none';
    distSelect.innerHTML = districts.map(d => `<option value="${d}">${d || '— All Districts —'}</option>`).join('');
  } else {
    // Show free text input
    distSelect.style.display = 'none';
    distInput.style.display = '';
    distInput.value = '';
  }
}

async function searchMarket() {
  const crop = document.getElementById('market-crop')?.value;
  const state = document.getElementById('market-state')?.value.trim();

  // Get district from either dropdown or text input
  const distSelect = document.getElementById('market-district-select');
  const distInput = document.getElementById('market-district-input');
  let district = '';
  if (distSelect && distSelect.style.display !== 'none') {
    district = distSelect.value;
  } else if (distInput) {
    district = distInput.value.trim();
  }

  if (!crop) { showToast('Please select a commodity', 'error'); return; }

  const btn = document.getElementById('market-search-btn');
  btn.textContent = '⏳ Fetching from Agmarknet...';
  btn.disabled = true;

  document.getElementById('market-results').innerHTML = `
    <div class="card market-loading-card">
      <div class="loading-spinner-wrap">
        <div class="spinner"></div>
      </div>
      <div class="loading-heading">Fetching Live Mandi Prices</div>
      <div class="loading-subheading">📡 Querying Agmarknet & national regulated markets database...</div>
      <div class="loading-footnote">
        Fetching wholesale arrivals, minimum, maximum, and modal price spreads.
      </div>
      <div class="loading-pills-row">
        <span class="loading-pill active">🌾 Commodity Identified</span>
        <span class="loading-pill active">🏛️ Connecting to Agmarknet</span>
        <span class="loading-pill">📊 Computing Price Spreads</span>
      </div>
    </div>
  `;

  try {
    const result = await getMarketPrices({ crop, state, district, location: state });

    if (result.error) throw new Error(result.error);

    const markets = result.markets || [];

    let html = '';

    // Data quality indicator
    html += `
      <div class="market-meta-strip" style="margin-bottom:var(--sp-lg);">
        <span class="dq-badge dq-live">
          <span class="badge-dot"></span> 📡 LIVE MANDI FEED
        </span>
        <span class="source-chip">
          🏛️ Source: Agmarknet / data.gov.in
        </span>
        ${result.fetch_timestamp ? `<span class="market-timestamp">🕒 Updated: ${new Date(result.fetch_timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>` : ''}
      </div>
    `;

    // Summary stats
    html += `
      <div class="market-kpi-grid" style="margin-bottom:var(--sp-xl);">
        <div class="stat-card market-stat-card">
          <div class="stat-label">Avg Modal Price</div>
          <div class="stat-value">₹${result.avg_price_per_kg}</div>
          <div class="stat-sub">per kg</div>
        </div>
        <div class="stat-card market-stat-card">
          <div class="stat-label">Highest Modal Price</div>
          <div class="stat-value" style="color:var(--c-success);">₹${result.max_price_per_kg}</div>
          <div class="stat-sub">per kg</div>
        </div>
        <div class="stat-card market-stat-card">
          <div class="stat-label">Lowest Modal Price</div>
          <div class="stat-value">₹${result.min_price_per_kg}</div>
          <div class="stat-sub">per kg</div>
        </div>
        <div class="stat-card market-stat-card">
          <div class="stat-label">Avg / Quintal</div>
          <div class="stat-value font-mono">₹${result.avg_price_per_quintal || (result.avg_price_per_kg * 100).toFixed(0)}</div>
          <div class="stat-sub">per 100 kg</div>
        </div>
        <div class="stat-card market-stat-card">
          <div class="stat-label">Reporting Mandis</div>
          <div class="stat-value">${result.total_markets_reporting || markets.length}</div>
          <div class="stat-sub">markets reporting today</div>
        </div>
      </div>
    `;

    if (result.best_market) {
      html += `
        <div class="market-best-banner" style="margin-bottom:var(--sp-xl);">
          <div class="best-badge">🏆 TOP SELLING OPPORTUNITY</div>
          <div class="best-title">${result.best_market}</div>
          <div class="best-subtitle">Peak modal price: <strong>₹${result.max_price_per_kg}/kg</strong> (₹${(parseFloat(result.max_price_per_kg) * 100).toFixed(0)}/quintal)</div>
        </div>
      `;
    }

    // Group markets by district for better readability
    if (markets.length) {
      // Get unique districts
      const districtGroups = {};
      markets.forEach(m => {
        const d = m.district || 'Other';
        if (!districtGroups[d]) districtGroups[d] = [];
        districtGroups[d].push(m);
      });
      const districtCount = Object.keys(districtGroups).length;

      html += `
        <div class="card market-table-card" style="margin-bottom:var(--sp-xl);">
          <div class="market-table-header">
            <div>
              <h3 class="section-title" style="margin:0;"><span class="icon">🏪</span> ${result.crop} — ${result.location || 'All India'}</h3>
              <p style="font-size:0.83rem;color:var(--c-text-muted);margin-top:4px;">Wholesale mandi arrivals with modal and range figures</p>
            </div>
            <span class="mandi-count-pill">${districtCount} Districts · ${markets.length} Mandis</span>
          </div>
          <div style="overflow-x:auto;">
            <table class="data-table">
              <thead>
                <tr>
                  <th>#</th><th>Market (Mandi)</th><th>District</th>
                  <th>Variety</th><th>₹/kg (Modal)</th><th>₹/Quintal (Min)</th>
                  <th>₹/Quintal (Max)</th><th>₹/Quintal (Modal)</th><th>Date</th>
                </tr>
              </thead>
              <tbody>
                ${markets.map((m, i) => `
                  <tr>
                    <td>${i + 1}</td>
                    <td style="font-weight:600;">${m.name}</td>
                    <td>${m.district || '—'}</td>
                    <td style="font-size:0.8rem;">${m.variety || '—'}</td>
                    <td style="font-weight:700;color:var(--c-text);">₹${m.price_per_kg}</td>
                    <td>₹${m.min_price_per_quintal || '—'}</td>
                    <td>₹${m.max_price_per_quintal || '—'}</td>
                    <td style="color:var(--c-primary-light);font-weight:700;">₹${m.price_per_quintal}</td>
                    <td style="font-size:0.78rem;">${m.arrival_date || m.last_updated || '—'}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
          <div class="market-table-footer">
            ${result.data_quality_note || 'Prices are reported by regulated markets under Agmarknet. Verify with your local mandi commission agent.'}
          </div>
        </div>
      `;
    } else {
      html += `
        <div class="card market-empty-card" style="margin-bottom:var(--sp-xl);">
          <div style="font-size:2.4rem;margin-bottom:var(--sp-md);">🤷</div>
          <h3 class="market-empty-title">No Markets Reporting Today</h3>
          <p class="market-empty-desc">There are no regulated mandis currently reporting price arrivals for this crop and territory today.</p>
          <p style="font-size:0.82rem;color:var(--c-text-muted);">Try selecting a different district or state (e.g., Telangana or All India).</p>
        </div>
      `;
    }

    // ============================================================
    // 📊 MARKET DATA VISUALIZATION SECTION
    // ============================================================
    if (markets.length >= 2) {
      html += `
        <div style="margin-top:var(--sp-2xl);margin-bottom:var(--sp-xl);">
          <div class="viz-section-header">
            <h2 class="section-title" style="font-size:1.3rem;border:none;padding:0;margin:0;">
              <span class="icon">📊</span> Market Price Analytics
            </h2>
            <p style="font-size:0.85rem;color:var(--c-text-muted);margin-top:4px;">Visual comparative analysis of ${result.crop || crop} prices across mandis</p>
          </div>
        </div>
      `;

      // -- MANDI PRICE COMPARISON CHART --
      html += `
        <div class="card viz-card" style="margin-bottom:var(--sp-xl);">
          <h3 class="section-title"><span class="icon">📊</span> Top Mandi Price Comparison</h3>
          <p class="viz-desc">Horizontal bar chart showing price per kg at top mandis. Yellow dashed line = average price. Green = above average, Red = below.</p>
          <div class="chart-container" style="position:relative;height:${Math.max(320, Math.min(markets.length, 15) * 34)}px;">
            <canvas id="chart-market-prices"></canvas>
          </div>
          <div class="viz-insight">
            <span class="viz-insight-icon">🎯</span>
            <span>Sell at green-bar mandis for optimal returns. Market average: ₹${result.avg_price_per_kg}/kg</span>
          </div>
        </div>
      `;

      // -- DISTRICT PRICE DISTRIBUTION --
      html += `
        <div class="card viz-card" style="margin-bottom:var(--sp-xl);">
          <h3 class="section-title"><span class="icon">🏘️</span> District-wise Price Distribution</h3>
          <p class="viz-desc">Grouped bars showing Min, Modal (average), and Max price per quintal across districts</p>
          <div class="chart-container" style="position:relative;height:360px;">
            <canvas id="chart-price-distribution"></canvas>
          </div>
          <div class="viz-insight">
            <span class="viz-insight-icon">💡</span>
            <span>Wider gaps between Min and Max indicate more price volatility. Target districts with high modal prices.</span>
          </div>
        </div>
      `;

      // -- MARKET SHARE PIE + MSP COMPARISON --
      html += `<div class="grid-2" style="margin-bottom:var(--sp-xl);">`;

      // Market share donut
      html += `
        <div class="card viz-card">
          <h3 class="section-title"><span class="icon">🥧</span> Mandi Distribution by District</h3>
          <p class="viz-desc">How many mandis are reporting prices in each district</p>
          <div class="chart-container" style="position:relative;max-width:400px;margin:0 auto;">
            <canvas id="chart-market-share"></canvas>
          </div>
          <div class="viz-insight">
            <span class="viz-insight-icon">📍</span>
            <span>${Object.keys(markets.reduce((acc, m) => { acc[m.district || 'Other'] = 1; return acc; }, {})).length} districts reporting across ${markets.length} mandis</span>
          </div>
        </div>
      `;

      // MSP Comparison
      const mspData = {
        'Rice': 2300, 'Wheat': 2275, 'Maize': 2090, 'Cotton': 7020,
        'Soybean': 4600, 'Groundnut': 6783, 'Chickpea': 5440,
        'Lentil': 6425, 'Pigeon Pea': 7550, 'Sugarcane': 340,
        'Tomato': 0, 'Potato': 0, 'Onion': 0,
      };
      const cropNameUpper = (result.crop || crop || '').charAt(0).toUpperCase() + (result.crop || crop || '').slice(1);
      const lowerCropName = cropNameUpper.toLowerCase();
      const mspKey = Object.keys(mspData).find(k => lowerCropName.includes(k.toLowerCase()));
      const mspVal = mspKey ? mspData[mspKey] : 0;
      const avgQtl = parseFloat(result.avg_price_per_quintal || (result.avg_price_per_kg * 100));

      if (mspVal > 0 && avgQtl > 0) {
        html += `
          <div class="card viz-card">
            <h3 class="section-title"><span class="icon">📋</span> MSP vs Market Price</h3>
            <p class="viz-desc">Government MSP compared to today's market average for ${cropNameUpper}</p>
            <div class="chart-container" style="position:relative;height:280px;">
              <canvas id="chart-msp-comparison"></canvas>
            </div>
            <div class="viz-insight">
              <span class="viz-insight-icon">${avgQtl >= mspVal ? '✅' : '⚠️'}</span>
              <span>${avgQtl >= mspVal
                ? `Market price is ₹${(avgQtl - mspVal).toFixed(0)} above MSP — positive return for farmers!`
                : `Market price is ₹${(mspVal - avgQtl).toFixed(0)} below MSP — consider govt procurement centers.`}</span>
            </div>
          </div>
        `;
      } else {
        html += `
          <div class="card viz-card">
            <h3 class="section-title"><span class="icon">📈</span> Price Summary</h3>
            <p class="viz-desc">Quick overview of today's price range for ${cropNameUpper}</p>
            <div style="display:flex;flex-direction:column;gap:var(--sp-md);padding:var(--sp-lg) 0;">
              <div class="metric-row">
                <span class="metric-label">Lowest Price</span>
                <span class="metric-value cost">₹${result.min_price_per_kg}/kg</span>
              </div>
              <div class="metric-row">
                <span class="metric-label">Average Price</span>
                <span class="metric-value highlight">₹${result.avg_price_per_kg}/kg</span>
              </div>
              <div class="metric-row">
                <span class="metric-label">Highest Price</span>
                <span class="metric-value profit">₹${result.max_price_per_kg}/kg</span>
              </div>
              <div class="metric-row">
                <span class="metric-label">Price Spread</span>
                <span class="metric-value font-mono">₹${(parseFloat(result.max_price_per_kg) - parseFloat(result.min_price_per_kg)).toFixed(2)}/kg</span>
              </div>
              <div class="metric-row">
                <span class="metric-label">Best Market</span>
                <span class="metric-value highlight">${result.best_market || '—'}</span>
              </div>
            </div>
          </div>
        `;
      }
      html += `</div>`;

      // Store chart init vars for use after DOM write
      var _mspVal = mspVal, _avgQtl = avgQtl, _cropNameUpper = cropNameUpper;
    }

    document.getElementById('market-results').innerHTML = html;

    // ---- Initialize Market Charts ----
    if (markets.length >= 2) {
      requestAnimationFrame(() => {
        setTimeout(() => {
          try {
            createMarketPriceChart('chart-market-prices', markets, result.crop || crop);
            createPriceDistributionChart('chart-price-distribution', markets, result.crop || crop);
            createMarketSharePieChart('chart-market-share', markets);
            if (_mspVal > 0 && _avgQtl > 0) {
              createMSPComparisonChart('chart-msp-comparison', _avgQtl, _mspVal, _cropNameUpper);
            }
          } catch (chartErr) {
            console.warn('Market chart initialization error:', chartErr);
          }
        }, 200);
      });
    }

    showToast(`📡 ${markets.length} mandi prices fetched from Agmarknet`, 'success');

  } catch (err) {
    document.getElementById('market-results').innerHTML = `
      <div class="card market-error-card">
        <div class="error-badge-icon">⚠️</div>
        <h3 class="error-title">Mandi Price Retrieval Failed</h3>
        <p class="error-desc">${err.message}</p>
        <div class="error-footnote">
          Make sure the backend server is running. Agmarknet API may also be temporarily unavailable from data.gov.in.
        </div>
      </div>
    `;
    showToast(err.message, 'error');
  } finally {
    btn.textContent = '📡 Fetch Live Prices';
    btn.disabled = false;
  }
}
