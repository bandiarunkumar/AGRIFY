// ============================================================
// AGRIFY Farm Intelligence Analyzer — Precision Planning Workflow
// ============================================================

import { analyzeFarm, getSoilByCoords, getWeatherByCoords, predictCrop, predictFertilizer, getSoilAnalysis, getCurrentPosition, reverseGeocode } from '../api.js';
import { showToast, setupMicButtons } from '../voice.js';
import { t } from '../i18n.js';
import {
  createSoilRadarChart,
  createCropSuitabilityChart,
  createProfitChart,
  createNPKDonutChart,
  createCropBubbleChart,
  createWeatherGaugeChart,
  createFertilizerStageChart
} from '../charts.js';

let wizardStep = 1;
let farmData = {};   // collected across wizard steps

export function renderAnalysis() {
  wizardStep = 1;
  farmData = {};

  return `
    <div class="page-section analysis-page">
      <!-- AGRIFY Farm Intelligence Hero Header -->
      <div class="analysis-hero-header">
        <div class="analysis-badge">
          <span class="badge-dot"></span>
          <span>AGRIFY AI ADVISORY ENGINE</span>
        </div>
        <h1 class="analysis-title">🌱 Farm Intelligence Analyzer</h1>
        <p class="analysis-subtitle">
          Precision crop, soil, and nutrient advisory powered by real-time GPS coordinates, satellite soil telemetry, and microclimate forecasting.
        </p>
        <div class="analysis-trust-strip">
          <span class="trust-pill"><span class="pill-icon">📍</span> GPS Micro-Targeting</span>
          <span class="trust-pill"><span class="pill-icon">🛰️</span> Satellite Soil Telemetry</span>
          <span class="trust-pill"><span class="pill-icon">🌤️</span> Live Microclimate Forecast</span>
          <span class="trust-pill"><span class="pill-icon">🧠</span> Agronomic AI Suitability</span>
        </div>
      </div>

      <div class="wizard">
        <!-- Guided Progress Stepper -->
        <div class="wizard-progress">
          <div class="wizard-step-indicator">
            <div class="wizard-step-dot active" id="dot-1">1</div>
            <div class="wizard-step-line" id="line-1"></div>
            <div class="wizard-step-dot" id="dot-2">2</div>
            <div class="wizard-step-line" id="line-2"></div>
            <div class="wizard-step-dot" id="dot-3">3</div>
            <div class="wizard-step-line" id="line-3"></div>
            <div class="wizard-step-dot" id="dot-4">4</div>
          </div>
          <div class="wizard-step-labels">
            <span class="wizard-step-label active">1. Location</span>
            <span class="wizard-step-label">2. Farm Details</span>
            <span class="wizard-step-label">3. Soil Telemetry</span>
            <span class="wizard-step-label">4. AI Report</span>
          </div>
        </div>

        <!-- STEP 1: GPS Location -->
        <div class="wizard-panel active" id="step-1">
          <div class="card analysis-step-card">
            <div class="step-card-header">
              <div class="step-badge">STEP 1 OF 3</div>
              <h3 class="section-title"><span class="icon">📍</span> Farm Location & Boundaries</h3>
              <p class="step-card-subtitle">
                Acquire precision GPS coordinates for your field. Real-time satellite soil and microclimate models are indexed to exact geographical coordinates rather than generic municipal boundaries.
              </p>
            </div>

            <!-- GPS Primary Button & Telemetry Panel -->
            <div class="gps-capture-panel">
              <div class="gps-hero-badge">🛰️ Precision Satellite Targeting</div>
              <h4 class="gps-hero-title">Automated Field Geolocation</h4>
              <p class="gps-hero-desc">
                Use your device's GPS to acquire coordinates. Weather and soil profiles will be synthesized for your exact farm parcel.
              </p>

              <button class="gps-btn" id="gps-btn">
                <span class="gps-icon-live">📡</span>
                <span>Capture My Farm Location (GPS)</span>
              </button>
              <div id="gps-status"></div>

              <!-- Map Tracking Animation -->
              <div id="map-radar-container" style="display:none;">
                <div class="radar-scan-grid"></div>
                <div class="radar-sweep-beam"></div>
                <div class="radar-center-blip"></div>
                <div class="radar-status-msg">🛰️ Aligning with Earth Observation Satellites...</div>
              </div>

              <!-- Live Map iframe Container -->
              <div id="map-iframe-container" style="display:none;">
                <iframe id="location-map-iframe" width="100%" height="100%" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" src=""></iframe>
              </div>
            </div>

            <!-- GPS Result Display -->
            <div id="gps-result" style="display:none;" class="card card-sm gps-result-card">
              <div class="gps-result-header">
                <span class="status-pill success">✅ Geolocation Coordinates Locked</span>
                <span class="gps-coord-preview">Live GPS Telemetry</span>
              </div>
              <div class="grid-2">
                <div class="metric-row">
                  <span class="metric-label">Latitude</span>
                  <span class="metric-value font-mono" id="display-lat">—</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">Longitude</span>
                  <span class="metric-value font-mono" id="display-lon">—</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">Village / Town</span>
                  <span class="metric-value" id="display-village">—</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">District</span>
                  <span class="metric-value" id="display-district">—</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">State</span>
                  <span class="metric-value" id="display-state">—</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">Accuracy</span>
                  <span class="metric-value accuracy-badge" id="display-accuracy">—</span>
                </div>
              </div>
            </div>

            <!-- Manual Fallback -->
            <div class="manual-fallback-section">
              <div class="divider-text-wrap">
                <span class="divider-text">— or enter coordinates & farm details manually —</span>
              </div>
              <div class="form-grid">
                <div class="form-group">
                  <label for="manual-lat">Latitude <span class="hint">(e.g. 17.3850 for Hyderabad)</span></label>
                  <input type="number" class="form-input" id="manual-lat" step="0.0001" placeholder="17.3850" />
                </div>
                <div class="form-group">
                  <label for="manual-lon">Longitude <span class="hint">(e.g. 78.4867 for Hyderabad)</span></label>
                  <input type="number" class="form-input" id="manual-lon" step="0.0001" placeholder="78.4867" />
                </div>
                <div class="form-group">
                  <label for="w-acres">Land Area <span class="hint">(acres)</span></label>
                  <input type="number" class="form-input" id="w-acres" value="5" min="0.5" step="0.5" />
                </div>
                <div class="form-group">
                  <label for="w-farmer-name">Farmer Name <span class="hint">(optional)</span></label>
                  <div class="input-with-mic">
                    <input type="text" class="form-input" id="w-farmer-name" placeholder="Your name" />
                    <button class="mic-btn" title="Voice input" type="button">🎤</button>
                  </div>
                </div>
              </div>
            </div>

            <div class="wizard-actions">
              <div></div>
              <button class="btn btn-primary btn-lg" id="step1-next">
                Next: Farm Details →
              </button>
            </div>
          </div>
        </div>

        <!-- STEP 2: Farm Details -->
        <div class="wizard-panel" id="step-2">
          <div class="card analysis-step-card">
            <div class="step-card-header">
              <div class="step-badge">STEP 2 OF 3</div>
              <h3 class="section-title"><span class="icon">🌾</span> Farm & Crop Details</h3>
              <p class="step-card-subtitle">
                Specify your crop rotation history, preferred planting season, and field management history to calibrate machine learning suitability.
              </p>
            </div>

            <div class="form-subheading">🌱 Season & Environmental Context</div>
            <div class="form-grid">
              <div class="form-group">
                <label for="w-prev-crop">Previous Crop</label>
                <select class="form-select" id="w-prev-crop">
                  <option value="Rice">Rice</option>
                  <option value="Wheat">Wheat</option>
                  <option value="Cotton">Cotton</option>
                  <option value="Maize">Maize</option>
                  <option value="Sugarcane">Sugarcane</option>
                  <option value="Groundnut">Groundnut</option>
                  <option value="Soybean">Soybean</option>
                  <option value="Potato">Potato</option>
                  <option value="Tomato">Tomato</option>
                  <option value="Onion">Onion</option>
                  <option value="Chickpea">Chickpea</option>
                  <option value="Unknown">Unknown / First Time</option>
                </select>
              </div>
              <div class="form-group">
                <label for="w-season">Season to Plant</label>
                <select class="form-select" id="w-season">
                  <option value="Kharif">Kharif (Jun–Oct)</option>
                  <option value="Rabi">Rabi (Oct–Mar)</option>
                  <option value="Zaid">Zaid (Mar–Jun)</option>
                </select>
              </div>
              <div class="form-group">
                <label for="w-irrigation">Irrigation Type</label>
                <select class="form-select" id="w-irrigation">
                  <option value="Drip">Drip</option>
                  <option value="Sprinkler">Sprinkler</option>
                  <option value="Flood">Flood</option>
                  <option value="Rainfed">Rainfed</option>
                </select>
              </div>
              <div class="form-group">
                <label for="w-region">Region</label>
                <select class="form-select" id="w-region">
                  <option value="South">South India</option>
                  <option value="North">North India</option>
                  <option value="East">East India</option>
                  <option value="West">West India</option>
                </select>
              </div>
            </div>

            <div class="form-subheading" style="margin-top:var(--sp-xl);">🧪 Field Inputs & Historical Yield</div>
            <div class="form-grid">
              <div class="form-group">
                <label for="w-prev-fert">Previous Fertilizer Used</label>
                <select class="form-select" id="w-prev-fert">
                  <option value="Urea">Urea</option>
                  <option value="DAP">DAP</option>
                  <option value="NPK">NPK</option>
                  <option value="MOP">MOP</option>
                  <option value="Compost">Compost</option>
                  <option value="Zinc Sulphate">Zinc Sulphate</option>
                </select>
              </div>
              <div class="form-group">
                <label for="w-prev-pest">Previous Pesticide Used</label>
                <select class="form-select" id="w-prev-pest">
                  <option value="Neem oil">Neem oil (Organic)</option>
                  <option value="Imidacloprid">Imidacloprid</option>
                  <option value="Chlorpyrifos">Chlorpyrifos</option>
                  <option value="Glyphosate">Glyphosate</option>
                  <option value="Spinosad">Spinosad</option>
                  <option value="Emamectin benzoate">Emamectin benzoate</option>
                </select>
              </div>
              <div class="form-group">
                <label for="w-yield-last">Last Season Yield <span class="hint">(kg total)</span></label>
                <input type="number" class="form-input" id="w-yield-last" value="4000" min="0" />
              </div>
              <div class="form-group">
                <label for="w-annual-rain">Annual Rainfall <span class="hint">(mm, leave 0 to use live data)</span></label>
                <input type="number" class="form-input" id="w-annual-rain" value="0" min="0" placeholder="0 = auto from weather" />
              </div>
            </div>

            <div class="wizard-actions">
              <button class="btn btn-secondary" id="step2-back">← Back</button>
              <button class="btn btn-primary" id="step2-next">Next: Soil Data →</button>
            </div>
          </div>
        </div>

        <!-- STEP 3: Soil Data -->
        <div class="wizard-panel" id="step-3">
          <div class="card analysis-step-card">
            <div class="step-card-header">
              <div class="step-badge">STEP 3 OF 3</div>
              <h3 class="section-title"><span class="icon">🧪</span> Soil Telemetry & Laboratory Data</h3>
              <p class="step-card-subtitle">
                Soil chemistry determines crop vitality and nutrient uptake. Fetch satellite soil telemetry with one click, or enter lab measurements from your local Krishi Vigyan Kendra (KVK) card.
              </p>
            </div>

            <!-- Auto-fetch soil button -->
            <div class="satellite-fetch-banner">
              <div class="banner-badge">🛰️ EARTH OBSERVATION SATELLITE</div>
              <div class="banner-title">Auto-Fetch Satellite Soil Data</div>
              <p class="banner-desc">
                Pulls real-time satellite spectral reflectance estimates for soil NPK, pH, moisture, and carbon at your farm coordinates.
              </p>
              <div class="banner-actions">
                <button class="btn btn-secondary" id="fetch-soil-btn">📡 Fetch Soil Data</button>
                <span id="soil-fetch-status"></span>
              </div>
            </div>

            <!-- Soil Form -->
            <div class="form-subheading">🧪 Soil Chemistry & Macronutrients</div>
            <div class="form-grid">
              <div class="form-group">
                <label for="w-soil-type">Soil Type</label>
                <select class="form-select" id="w-soil-type">
                  <option value="Loamy">Loamy</option>
                  <option value="Clay">Clay</option>
                  <option value="Sandy">Sandy</option>
                  <option value="Silt">Silt</option>
                  <option value="Clay Loam">Clay Loam</option>
                  <option value="Sandy Loam">Sandy Loam</option>
                </select>
              </div>
              <div class="form-group">
                <label for="w-ph">pH Level <span class="required-star">*</span> <span class="hint">4.0–9.0</span></label>
                <input type="number" class="form-input" id="w-ph" min="4.0" max="9.0" step="0.1" placeholder="6.5" />
              </div>
              <div class="form-group">
                <label for="w-n">Nitrogen (N) <span class="required-star">*</span> <span class="hint">0–140 kg/ha scale</span></label>
                <input type="number" class="form-input" id="w-n" min="0" max="140" placeholder="50" />
              </div>
              <div class="form-group">
                <label for="w-p">Phosphorus (P) <span class="required-star">*</span> <span class="hint">0–145 kg/ha scale</span></label>
                <input type="number" class="form-input" id="w-p" min="0" max="145" placeholder="40" />
              </div>
              <div class="form-group">
                <label for="w-k">Potassium (K) <span class="required-star">*</span> <span class="hint">0–205 kg/ha scale</span></label>
                <input type="number" class="form-input" id="w-k" min="0" max="205" placeholder="30" />
              </div>
              <div class="form-group">
                <label for="w-moisture">Soil Moisture <span class="required-star">*</span> <span class="hint">20–80%</span></label>
                <input type="number" class="form-input" id="w-moisture" min="0" max="100" placeholder="40" />
              </div>
              <div class="form-group">
                <label for="w-oc">Organic Carbon <span class="hint">(dg/kg — HMR auto-converts)</span></label>
                <input type="number" class="form-input" id="w-oc" min="0" max="500" placeholder="80" />
              </div>
              <div class="form-group">
                <label for="w-rainfall">Annual Rainfall <span class="hint">(mm)</span></label>
                <input type="number" class="form-input" id="w-rainfall" min="0" max="2000" placeholder="600" />
              </div>
            </div>

            <div id="soil-data-note"></div>

            <div class="form-tip-box">
              <div class="tip-text">
                💡 Fields marked with <span class="required-star">*</span> are mandatory. Use <strong>"Fetch Soil Data"</strong> above OR enter values manually from your local KVK soil health report.
              </div>
            </div>

            <div class="wizard-actions">
              <button class="btn btn-secondary" id="step3-back">← Back</button>
              <button class="btn btn-accent btn-lg" id="step3-submit">🔍 Analyze Farm Now</button>
            </div>
          </div>
        </div>

        <!-- STEP 4: Results -->
        <div class="wizard-panel" id="step-4">
          <div id="analysis-results"></div>
        </div>
      </div>
    </div>
  `;
}

export function initAnalysis() {
  // ---- GPS Button ----
  document.getElementById('gps-btn')?.addEventListener('click', () => captureGPS());

  // ---- Step 1 Next ----
  document.getElementById('step1-next')?.addEventListener('click', () => {
    const lat = farmData.lat || parseFloat(document.getElementById('manual-lat')?.value);
    const lon = farmData.lon || parseFloat(document.getElementById('manual-lon')?.value);

    if (!lat || !lon || isNaN(lat) || isNaN(lon)) {
      showToast('Please capture GPS location or enter lat/lon manually', 'error');
      return;
    }

    farmData.lat = lat;
    farmData.lon = lon;
    farmData.area_acres = parseFloat(document.getElementById('w-acres')?.value) || 5;
    farmData.farmer_name = document.getElementById('w-farmer-name')?.value || '';

    goToStep(2);
  });

  // ---- Step 2 ----
  document.getElementById('step2-back')?.addEventListener('click', () => goToStep(1));
  document.getElementById('step2-next')?.addEventListener('click', () => {
    farmData.previous_crop = document.getElementById('w-prev-crop')?.value;
    farmData.season = document.getElementById('w-season')?.value;
    farmData.irrigation = document.getElementById('w-irrigation')?.value;
    farmData.region = document.getElementById('w-region')?.value;
    farmData.previous_fertilizer = document.getElementById('w-prev-fert')?.value;
    farmData.previous_pesticide = document.getElementById('w-prev-pest')?.value;
    farmData.yield_last = parseFloat(document.getElementById('w-yield-last')?.value) || 4000;
    farmData.annual_rainfall_mm = parseFloat(document.getElementById('w-annual-rain')?.value) || 0;
    goToStep(3);
  });

  // ---- Step 3 Soil Fetch ----
  document.getElementById('fetch-soil-btn')?.addEventListener('click', () => fetchSoilData());

  document.getElementById('step3-back')?.addEventListener('click', () => goToStep(2));
  document.getElementById('step3-submit')?.addEventListener('click', () => submitAnalysis());

  setupMicButtons();
}

async function captureGPS() {
  const btn = document.getElementById('gps-btn');
  const status = document.getElementById('gps-status');
  const resultDiv = document.getElementById('gps-result');
  const radarDiv = document.getElementById('map-radar-container');
  const mapIframeDiv = document.getElementById('map-iframe-container');
  const mapIframe = document.getElementById('location-map-iframe');

  btn.textContent = '📡 Locating...';
  btn.classList.add('loading');
  status.textContent = 'Requesting GPS signal...';

  if (resultDiv) resultDiv.style.display = 'none';
  if (mapIframeDiv) mapIframeDiv.style.display = 'none';
  if (radarDiv) radarDiv.style.display = 'block';

  try {
    const pos = await getCurrentPosition();
    farmData.lat = pos.lat;
    farmData.lon = pos.lon;

    status.textContent = `✅ GPS captured (accuracy: ±${Math.round(pos.accuracy)}m). Reverse geocoding...`;

    // Show live map iframe
    if (radarDiv) radarDiv.style.display = 'none';
    if (mapIframeDiv && mapIframe) {
      const iframeSrc = `https://www.openstreetmap.org/export/embed.html?bbox=${pos.lon-0.005},${pos.lat-0.005},${pos.lon+0.005},${pos.lat+0.005}&layer=mapnik&marker=${pos.lat},${pos.lon}`;
      mapIframe.src = iframeSrc;
      mapIframeDiv.style.display = 'block';
    }

    // Reverse geocode
    try {
      const geo = await reverseGeocode(pos.lat, pos.lon);
      farmData.geo = geo;

      document.getElementById('display-lat').textContent = pos.lat.toFixed(6);
      document.getElementById('display-lon').textContent = pos.lon.toFixed(6);
      document.getElementById('display-village').textContent = geo.village || '—';
      document.getElementById('display-district').textContent = geo.district || '—';
      document.getElementById('display-state').textContent = geo.state || '—';
      document.getElementById('display-accuracy').textContent = `±${Math.round(pos.accuracy)}m`;

      resultDiv.style.display = 'block';
      showToast(`📍 ${geo.village || geo.district || 'Location'} captured! (${pos.lat.toFixed(4)}, ${pos.lon.toFixed(4)})`, 'success');
      status.textContent = `✅ ${geo.display_name || `${pos.lat.toFixed(4)}, ${pos.lon.toFixed(4)}`}`;
    } catch (geoErr) {
      document.getElementById('display-lat').textContent = pos.lat.toFixed(6);
      document.getElementById('display-lon').textContent = pos.lon.toFixed(6);
      document.getElementById('display-village').textContent = '—';
      document.getElementById('display-district').textContent = '—';
      document.getElementById('display-state').textContent = '—';
      document.getElementById('display-accuracy').textContent = `±${Math.round(pos.accuracy)}m`;
      resultDiv.style.display = 'block';
      status.textContent = `GPS: ${pos.lat.toFixed(4)}, ${pos.lon.toFixed(4)}`;
    }

  } catch (err) {
    showToast(err.message, 'error');
    status.textContent = '❌ ' + err.message;
    if (document.getElementById('map-radar-container')) {
      document.getElementById('map-radar-container').style.display = 'none';
    }
  } finally {
    btn.innerHTML = `<span class="gps-icon-live">📡</span> <span>Capture My Farm Location (GPS)</span>`;
    btn.classList.remove('loading');
  }
}

async function fetchSoilData() {
  const btn = document.getElementById('fetch-soil-btn');
  const status = document.getElementById('soil-fetch-status');
  const noteDiv = document.getElementById('soil-data-note');

  if (!farmData.lat || !farmData.lon) {
    showToast('Please capture GPS location first (Step 1)', 'error');
    return;
  }

  btn.textContent = '⌛ Fetching satellite soil data...';
  btn.disabled = true;
  status.textContent = `Fetching soil data for ${farmData.lat.toFixed(4)}, ${farmData.lon.toFixed(4)}...`;

  try {
    const { getSoilByCoords } = await import('../api.js');
    const soil = await getSoilByCoords(farmData.lat, farmData.lon);

    if (soil.ok) {
      // Populate form fields
      const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el && val !== undefined && val !== null) el.value = val;
      };

      setVal('w-soil-type', soil.soil_type);
      setVal('w-ph', soil.ph);
      setVal('w-n', soil.N);
      setVal('w-p', soil.P);
      setVal('w-k', soil.K);
      setVal('w-moisture', soil.moisture_pct);
      setVal('w-oc', soil.organic_carbon);

      farmData.soil_from_api = soil;

      const qualityLabel = soil.fallback ? '⚠️ Regional estimate (satellite unavailable)' : '✅ Satellite soil data loaded';
      noteDiv.innerHTML = `
        <div class="soil-note-badge ${soil.fallback ? 'warning' : 'success'}">${qualityLabel}</div>
      `;

      status.textContent = soil.fallback ? '⚠️ Regional estimate used' : '✅ Loaded';
      showToast(
        soil.fallback
          ? '⚠️ Satellite data unavailable — using regional estimates'
          : `✅ Soil data loaded for (${farmData.lat.toFixed(3)}, ${farmData.lon.toFixed(3)})`,
        soil.fallback ? 'warning' : 'success'
      );
    } else {
      status.textContent = '❌ Failed';
      showToast('Could not fetch soil data', 'error');
    }
  } catch (err) {
    status.textContent = '❌ Error: ' + err.message;
    showToast('Soil fetch failed: ' + err.message, 'error');
  } finally {
    btn.textContent = '📡 Fetch Soil Data';
    btn.disabled = false;
  }
}

function goToStep(step) {
  wizardStep = step;
  document.querySelectorAll('.wizard-panel').forEach(p => p.classList.remove('active'));
  document.getElementById(`step-${step}`)?.classList.add('active');

  for (let i = 1; i <= 4; i++) {
    const dot = document.getElementById(`dot-${i}`);
    const line = document.getElementById(`line-${i}`);
    if (dot) {
      dot.classList.remove('active', 'completed');
      if (i < step) dot.classList.add('completed');
      if (i === step) dot.classList.add('active');
    }
    if (line) {
      line.classList.toggle('completed', i < step);
    }
  }

  const stepLabels = document.querySelectorAll('.wizard-step-label');
  stepLabels.forEach((label, idx) => {
    label.classList.toggle('active', idx + 1 === step);
    label.classList.toggle('completed', idx + 1 < step);
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function submitAnalysis() {
  // Collect soil data from form
  const soilType = document.getElementById('w-soil-type')?.value;
  const phVal = document.getElementById('w-ph')?.value;
  const nVal = document.getElementById('w-n')?.value;
  const pVal = document.getElementById('w-p')?.value;
  const kVal = document.getElementById('w-k')?.value;
  const moistureVal = document.getElementById('w-moisture')?.value;
  const ocVal = document.getElementById('w-oc')?.value;
  const rainfallVal = document.getElementById('w-rainfall')?.value;

  // Validate mandatory soil fields
  const missingFields = [];
  if (!phVal || phVal.trim() === '') missingFields.push('pH Level');
  if (!nVal || nVal.trim() === '') missingFields.push('Nitrogen (N)');
  if (!pVal || pVal.trim() === '') missingFields.push('Phosphorus (P)');
  if (!kVal || kVal.trim() === '') missingFields.push('Potassium (K)');
  if (!moistureVal || moistureVal.trim() === '') missingFields.push('Soil Moisture');

  if (missingFields.length > 0) {
    showToast(`⚠️ Please fill these required fields: ${missingFields.join(', ')}`, 'error');
    // Highlight empty fields
    const fieldMap = { 'pH Level': 'w-ph', 'Nitrogen (N)': 'w-n', 'Phosphorus (P)': 'w-p', 'Potassium (K)': 'w-k', 'Soil Moisture': 'w-moisture' };
    missingFields.forEach(f => {
      const el = document.getElementById(fieldMap[f]);
      if (el) {
        el.style.borderColor = '#ef4444';
        el.style.boxShadow = '0 0 0 3px rgba(239,68,68,0.2)';
        el.addEventListener('input', () => { el.style.borderColor = ''; el.style.boxShadow = ''; }, { once: true });
      }
    });
    return;
  }

  const ph = parseFloat(phVal);
  const N = parseFloat(nVal);
  const P = parseFloat(pVal);
  const K = parseFloat(kVal);
  const moisture = parseFloat(moistureVal);
  const oc = parseFloat(ocVal) || 50;
  const rainfall = parseFloat(rainfallVal) || 600;

  // Build payload — always include soil data
  const payload = {
    latitude: farmData.lat,
    longitude: farmData.lon,
    area_acres: farmData.area_acres || 5,
    season: farmData.season || 'Kharif',
    region: farmData.region || 'South',
    previous_crop: farmData.previous_crop || 'Rice',
    previous_fertilizer: farmData.previous_fertilizer || 'Urea',
    previous_pesticide: farmData.previous_pesticide || 'Neem oil',
    irrigation: farmData.irrigation || 'Drip',
    yield_last: farmData.yield_last || 4000,
    farmer_name: farmData.farmer_name || '',
    annual_rainfall_mm: farmData.annual_rainfall_mm || rainfall || 0,
    // Always send soil values
    N: N,
    P: P,
    K: K,
    ph: ph,
    soil_type: soilType || 'Loamy',
    soil_moisture: moisture,
    organic_carbon: oc,
  };

  goToStep(4);

  const resultsEl = document.getElementById('analysis-results');
  resultsEl.innerHTML = `
    <div class="card analysis-loading-card">
      <div class="loading-spinner-wrap">
        <div class="spinner"></div>
      </div>
      <div class="loading-heading">Generating AI Farm Intelligence</div>
      <div class="loading-subheading">🌐 Fetching live weather & microclimate for your coordinates...</div>
      <div class="loading-footnote">
        Synthesizing meteorological streams, satellite soil telemetry, and predictive crop suitability models.
      </div>
      <div class="loading-pills-row">
        <span class="loading-pill active">📍 Location Synchronized</span>
        <span class="loading-pill active">🌤️ Microclimate Feed</span>
        <span class="loading-pill active">🧪 Calibrating NPK</span>
        <span class="loading-pill">🧠 Evaluating Suitability</span>
      </div>
    </div>
  `;

  try {
    const result = await analyzeFarm(payload);
    renderResults(result, payload);
  } catch (err) {
    resultsEl.innerHTML = `
      <div class="card analysis-error-card">
        <div class="error-badge-icon">⚠️</div>
        <h3 class="error-title">Analysis Request Failed</h3>
        <p class="error-desc">${err.message}</p>
        <div class="error-footnote">
          The server may be waking up (free tier sleeps after inactivity).<br>
          Please wait a few moments and try again.
        </div>
        <button class="btn btn-secondary" style="margin-top:var(--sp-xl);" onclick="window.dispatchEvent(new CustomEvent('navigate',{detail:'analysis'}))">
          ← Try Again
        </button>
      </div>
    `;
  }
}

async function renderResults(result, payload) {
  const { translateDynamicText } = await import('../api.js');
  const lang = window.localStorage.getItem('lang') || 'en';
  const resultsEl = document.getElementById('analysis-results');
  const top3 = result.crop_recommendation?.top_3 || [];
  const allFeasible = result.crop_recommendation?.all_feasible || [];
  const weather = result.weather || {};
  const soil = result.soil || {};
  const geo = result.location || {};
  const fert = result.fertilizer_recommendation || {};
  const irr = result.irrigation_guidance || {};
  const alerts = result.alerts || [];
  const acres = payload.area_acres || 5;

  let html = '';

  // ---- TOP SUMMARY STRIP ----
  html += `
    <div class="analysis-results-meta-strip">
      <div class="meta-strip-item">
        <span class="meta-strip-label">📍 Field Location</span>
        <span class="meta-strip-value">${payload.latitude?.toFixed(4)}, ${payload.longitude?.toFixed(4)}</span>
      </div>
      <div class="meta-strip-item">
        <span class="meta-strip-label">🌾 Target Season</span>
        <span class="meta-strip-value">${payload.season || 'Kharif'}</span>
      </div>
      <div class="meta-strip-item">
        <span class="meta-strip-label">📐 Land Area</span>
        <span class="meta-strip-value">${acres} Acres</span>
      </div>
      <div class="meta-strip-item">
        <span class="meta-strip-label">🤖 Intelligence Mode</span>
        <span class="meta-strip-value"><span class="badge-dot"></span> AGRIFY AI Engine</span>
      </div>
    </div>
  `;

  // ---- ALERTS (if any danger/warning) ----
  const importantAlerts = alerts.filter(a => a.severity === 'danger' || a.severity === 'warning');
  if (importantAlerts.length) {
    html += `<div style="margin-bottom:var(--sp-xl);">`;
    html += `<h3 class="section-title"><span class="icon">🚨</span> Farm Alerts</h3>`;
    for (let a of importantAlerts.slice(0, 3)) {
      const icons = { danger: '🔴', warning: '🟡', info: '🔵', tip: '✅' };
      const titleTrans = await translateDynamicText(a.title, lang);
      const msgTrans = await translateDynamicText(a.message, lang);
      html += `
        <div class="alert-banner ${a.severity}" style="margin-bottom:var(--sp-sm);">
          <span class="alert-icon">${icons[a.severity] || '⚠️'}</span>
          <div class="alert-content">
            <div class="alert-title">${titleTrans}</div>
            <div class="alert-message">${msgTrans}</div>
            ${a.source ? `<div style="margin-top:4px;font-size:0.7rem;opacity:0.7;">Source: ${a.source}</div>` : ''}
          </div>
        </div>
      `;
    }
    html += `</div>`;
  }

  // ---- TOP 3 CROP RECOMMENDATIONS ----
  if (top3.length) {
    html += `
      <div class="analysis-section-block" style="margin-bottom:var(--sp-xl);">
        <div class="section-header-wrap">
          <h3 class="section-title"><span class="icon">🌾</span> Top Crop Recommendations</h3>
          <div class="section-context-desc">
            Calibrated for live microclimate (${weather.temperature}°C, ${weather.humidity}% humidity), satellite soil telemetry, and ${payload.season} season.
          </div>
        </div>
        <div class="grid-3">
    `;
    for (let i = 0; i < top3.length; i++) {
      const crop = top3[i];
      const rankEmojis = ['🥇', '🥈', '🥉'];
      const rankBadges = ['AI Primary Choice', 'Secondary Option', 'Tertiary Option'];
      
      const cropName = await translateDynamicText(crop.crop, lang);
      const sowName = await translateDynamicText(crop.sowing_months, lang);
      const harvName = await translateDynamicText(crop.harvest_months, lang);
      const reasonTr = await translateDynamicText(crop.reason, lang);
      const seasonTr = await translateDynamicText(crop.season, lang);

      html += `
        <div class="crop-rec-card ${i === 0 ? 'top-pick' : ''}">
          <div class="crop-rank-badge">
            <span class="rank-medal">${rankEmojis[i] || `#${i+1}`}</span>
            <span class="rank-title">${rankBadges[i] || `Rank #${i+1}`}</span>
          </div>
          <div class="crop-rank">${i + 1}</div>
          <div class="crop-name-big" style="text-transform: capitalize;">${cropName}</div>
          <div class="suitability-bar">
            <div class="suitability-fill" style="width:${crop.suitability_score}%"></div>
          </div>
          <div class="score-label">Agronomic Fit: ${crop.suitability_score}%</div>
          <div class="crop-tags-row">
            <span class="crop-tag season">📅 ${seasonTr}</span>
            <span class="crop-tag water">💧 ${crop.water_need}</span>
            <span class="crop-tag duration">⏱️ ${crop.duration_days}d</span>
          </div>
          <div class="crop-metrics-list">
            <div class="metric-row">
              <span class="metric-label">Sow</span>
              <span class="metric-value font-sm">${sowName}</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">Harvest</span>
              <span class="metric-value font-sm">${harvName}</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">Estimated Profit</span>
              <span class="metric-value profit">₹${(crop.net_profit_estimated || 0).toLocaleString()}</span>
            </div>
          </div>
          ${crop.reason ? `<div class="crop-reason-box">${reasonTr}</div>` : ''}
        </div>
      `;
    }
    html += `</div></div>`;
  }

  // ---- LIVE DATA SUMMARY GRID ----
  html += `
    <div class="grid-2 analysis-summary-grid" style="margin-bottom:var(--sp-xl);">
      <div class="card">
        <h3 class="section-title"><span class="icon">📍</span> Location & Live Microclimate</h3>
        ${geo.village || geo.district ? `
        <div class="metric-row">
          <span class="metric-label">Location</span>
          <span class="metric-value">${[geo.village, geo.district, geo.state].filter(Boolean).join(', ')}</span>
        </div>
        ` : ''}
        <div class="metric-row">
          <span class="metric-label">Coordinates</span>
          <span class="metric-value font-mono">${payload.latitude?.toFixed(4)}, ${payload.longitude?.toFixed(4)}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">Temperature</span>
          <span class="metric-value">${weather.temperature}°C (feels ${weather.feels_like}°C)</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">Humidity</span>
          <span class="metric-value">${weather.humidity}%</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">Weather</span>
          <span class="metric-value">${await translateDynamicText((weather.description || '—'), lang)}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">Wind</span>
          <span class="metric-value">${weather.wind_speed} m/s</span>
        </div>
      </div>

      <div class="card">
        <h3 class="section-title"><span class="icon">🧪</span> Soil Telemetry Profile</h3>
        <div class="metric-row">
          <span class="metric-label">Soil Type</span>
          <span class="metric-value">${soil.soil_type || '—'}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">N · P · K</span>
          <span class="metric-value font-mono">${soil.N || '—'} · ${soil.P || '—'} · ${soil.K || '—'}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">pH</span>
          <span class="metric-value">${soil.ph || '—'}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">Clay / Sand</span>
          <span class="metric-value">${soil.clay_pct ? soil.clay_pct + '%' : '—'} / ${soil.sand_pct ? soil.sand_pct + '%' : '—'}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">Moisture</span>
          <span class="metric-value">${soil.moisture_pct || '—'}%</span>
        </div>
      </div>
    </div>
  `;

  // ---- IRRIGATION GUIDANCE ----
  if (irr.recommendation) {
    html += `
      <div class="card irrigation-card" style="margin-bottom:var(--sp-xl);">
        <h3 class="section-title"><span class="icon">💧</span> Irrigation Guidance</h3>
        <div class="grid-2">
          <div>
            <div class="metric-row">
              <span class="metric-label">Crop Water Need</span>
              <span class="metric-value">${irr.crop_water_need_mm_day} mm/day</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">Rain Contribution</span>
              <span class="metric-value">${irr.rain_forecast_contribution_mm} mm</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">Net Irrigation Needed</span>
              <span class="metric-value ${irr.net_irrigation_needed_mm_day > 5 ? 'cost' : 'profit'}">${irr.net_irrigation_needed_mm_day} mm/day</span>
            </div>
          </div>
          <div style="display:flex;align-items:center;">
            <div class="irrigation-advice-box">
              💧 ${await translateDynamicText(irr.recommendation, lang)}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // ---- FERTILIZER RECOMMENDATION ----
  if (fert && (fert.recommended_fertilizer || (fert.stage_wise_application && fert.stage_wise_application.length > 0))) {
    const bf = fert.recommended_fertilizer || {};
    let nutrientDefHtml = '<div style="color:var(--c-success);font-size:0.85rem;">✅ No major nutrient deficiencies detected</div>';
    
    if (fert.nutrient_deficiency_summary && fert.nutrient_deficiency_summary.length > 0) {
      nutrientDefHtml = '<div style="font-weight:700;font-size:0.85rem;margin-bottom:var(--sp-sm);">Nutrient Status:</div>';
      for (let d of fert.nutrient_deficiency_summary) {
        let levelClass = d.level === 'low' ? 'high' : d.level === 'excess' ? 'medium' : 'low';
        let nutTrans = await translateDynamicText(d.nutrient, lang);
        let remTrans = await translateDynamicText(d.remedy, lang);
        let lvlTrans = await translateDynamicText(d.level, lang);
        nutrientDefHtml += `
          <div class="metric-row">
            <span class="metric-label">${nutTrans}</span>
            <div>
              <span class="severity-badge ${levelClass}">${lvlTrans}</span>
              <div style="font-size:0.72rem;color:var(--c-text-muted);margin-top:2px;">${remTrans}</div>
            </div>
          </div>
        `;
      }
    }

    let stagesHtml = '';
    if (fert.stage_wise_application && fert.stage_wise_application.length > 0) {
      stagesHtml = `
        <div style="margin-bottom:var(--sp-lg);">
          <div style="font-weight:700;margin-bottom:var(--sp-sm);font-size:0.9rem;">📅 Stage-wise Application Guide:</div>
          <div style="display:flex;flex-direction:column;gap:var(--sp-sm);">
      `;
      for (let i = 0; i < fert.stage_wise_application.length; i++) {
        let s = fert.stage_wise_application[i];
        let stgName = await translateDynamicText(s.stage, lang);
        stagesHtml += `
          <div style="display:flex;align-items:center;gap:var(--sp-md);padding:10px 14px;background:var(--c-surface);border-radius:var(--r-md);border-left:3px solid var(--c-primary);">
            <span style="font-weight:700;color:var(--c-primary-light);min-width:20px;">${i+1}</span>
            <div>
              <div style="font-weight:600;font-size:0.85rem;color:var(--c-text)">${stgName}</div>
              <div style="font-size:0.78rem;color:var(--c-text-muted);">N: ${s.n_pct}% · P: ${s.p_pct}% · K: ${s.k_pct}%</div>
            </div>
          </div>
        `;
      }
      stagesHtml += `</div></div>`;
    }
    
    let organicHtml = '';
    if (fert.organic_alternatives && fert.organic_alternatives.length > 0) {
      organicHtml = `
        <div style="margin-bottom:var(--sp-md);">
          <div style="font-weight:700;margin-bottom:var(--sp-sm);font-size:0.9rem;">🌿 Organic Alternatives:</div>
          <ul class="solution-list">
      `;
      for (let oa of fert.organic_alternatives) {
        let oaTr = await translateDynamicText(oa, lang);
        organicHtml += `<li>${oaTr}</li>`;
      }
      organicHtml += `</ul></div>`;
    }

    let warningHtml = '';
    if (fert.warning) {
      warningHtml = `
        <div style="padding:var(--sp-md);background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.2);border-radius:var(--r-md);font-size:0.83rem;color:var(--c-accent);">
          ⚠️ ${await translateDynamicText(fert.warning, lang)}
        </div>
      `;
    }

    const fertName = await translateDynamicText((bf.fertilizer || '—'), lang);

    html += `
      <div class="card" style="margin-bottom:var(--sp-xl);">
        <h3 class="section-title"><span class="icon">🧬</span> Fertilizer Recommendation</h3>
        <div class="grid-2" style="margin-bottom:var(--sp-lg);">
          <div>
            <div class="metric-row">
              <span class="metric-label">Best Fertilizer</span>
              <span class="metric-value highlight" style="font-size:1.1rem;">${fertName}</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">Confidence</span>
              <span class="metric-value">${bf.confidence || '—'}%</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">NPK Ratio</span>
              <span class="metric-value font-mono">${bf.details?.npk || '—'}</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">Qty / hectare</span>
              <span class="metric-value">${bf.details?.qty_per_ha || '—'} kg</span>
            </div>
            <div class="metric-row">
              <span class="metric-label">Cost / kg</span>
              <span class="metric-value">₹${bf.details?.cost_per_kg || '—'}</span>
            </div>
          </div>
          <div>
            ${nutrientDefHtml}
          </div>
        </div>
        ${stagesHtml}
        ${organicHtml}
        ${warningHtml}
      </div>
    `;
  }

  // ---- ALL FEASIBLE CROPS TABLE ----
  if (allFeasible.length > 3) {
    html += `
      <div class="card" style="margin-bottom:var(--sp-xl);">
        <h3 class="section-title"><span class="icon">🌿</span> All Feasible Crops (${allFeasible.length} found)</h3>
        <p style="font-size:0.83rem;color:var(--c-text-muted);margin-bottom:var(--sp-md);">
          All crops passing agronomic suitability filters for your location, soil, and season.
          Sorted by suitability score.
        </p>
        <div style="overflow-x:auto;">
          <table class="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Crop</th>
                <th>Score</th>
                <th>Season</th>
                <th>Water Need</th>
                <th>Duration</th>
                <th>Price/kg</th>
                <th>Profit Est.</th>
              </tr>
            </thead>
            <tbody>
              ${allFeasible.map((crop, i) => `
                <tr>
                  <td>${i + 1}</td>
                  <td style="font-weight:600;text-transform:capitalize;" class="t-crop" data-crop="${crop.crop}">${crop.crop}</td>
                  <td>
                    <div style="display:flex;align-items:center;gap:8px;">
                      <div class="progress-bar" style="width:60px;">
                        <div class="progress-fill" style="width:${crop.suitability_score}%;background:var(--c-primary);"></div>
                      </div>
                      <span style="font-size:0.8rem;color:var(--c-primary-light);">${crop.suitability_score}%</span>
                    </div>
                  </td>
                  <td class="t-season" data-season="${crop.season}">${crop.season}</td>
                  <td>${crop.water_need}</td>
                  <td>${crop.duration_days}d</td>
                  <td>₹${crop.price_per_kg}/kg</td>
                  <td style="color:var(--c-success);">₹${(crop.net_profit_estimated || 0).toLocaleString()}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  // ============================================================
  // 📊 DATA VISUALIZATION DASHBOARD
  // ============================================================
  const soilForChart = {
    N: soil.N || payload.N || 0,
    P: soil.P || payload.P || 0,
    K: soil.K || payload.K || 0,
    ph: soil.ph || payload.ph || 0,
    moisture_pct: soil.moisture_pct || payload.soil_moisture || 0,
    organic_carbon: soil.organic_carbon || payload.organic_carbon || 0,
  };

  html += `
    <div style="margin-top:var(--sp-2xl);margin-bottom:var(--sp-xl);">
      <div class="viz-section-header">
        <h2 class="section-title" style="font-size:1.3rem;border:none;padding:0;margin:0;">
          <span class="icon">📊</span> Data Visualization Dashboard
        </h2>
        <p style="font-size:0.85rem;color:var(--c-text-muted);margin-top:4px;">Interactive charts based on your farm analysis results</p>
      </div>
    </div>
  `;

  // -- SOIL NUTRIENT RADAR + WEATHER GAUGE --
  html += `
    <div class="grid-2" style="margin-bottom:var(--sp-xl);">
      <div class="card viz-card">
        <h3 class="section-title"><span class="icon">🧪</span> Soil Nutrient Analysis</h3>
        <p class="viz-desc">Radar chart comparing your soil's NPK, pH, moisture, and organic carbon against ideal ranges</p>
        <div class="chart-container" style="position:relative;max-width:420px;margin:0 auto;">
          <canvas id="chart-soil-radar"></canvas>
        </div>
        <div class="viz-insight">
          <span class="viz-insight-icon">💡</span>
          <span>Green area = Your soil. Amber dashed = Ideal range. Larger green overlap with amber means healthier soil.</span>
        </div>
      </div>

      <div class="card viz-card">
        <h3 class="section-title"><span class="icon">🌤️</span> Current Weather Conditions</h3>
        <p class="viz-desc">Polar area chart of live weather factors affecting crop growth</p>
        <div class="chart-container" style="position:relative;max-width:420px;margin:0 auto;">
          <canvas id="chart-weather-gauge"></canvas>
        </div>
        <div class="viz-insight">
          <span class="viz-insight-icon">💡</span>
          <span>Temperature: ${weather.temperature}°C · Humidity: ${weather.humidity}% · Wind: ${weather.wind_speed} m/s</span>
        </div>
      </div>
    </div>
  `;

  // -- CROP SUITABILITY CHART --
  if (allFeasible.length > 0 || top3.length > 0) {
    const charted = allFeasible.length > 0 ? allFeasible.slice(0, 10) : top3;
    html += `
      <div class="card viz-card" style="margin-bottom:var(--sp-xl);">
        <h3 class="section-title"><span class="icon">🏆</span> Crop Suitability Comparison</h3>
        <p class="viz-desc">Horizontal bar chart ranking all feasible crops by suitability score based on your soil, weather, and season</p>
        <div class="chart-container" style="position:relative;height:${Math.max(280, charted.length * 38)}px;">
          <canvas id="chart-crop-suitability"></canvas>
        </div>
        <div class="viz-insight">
          <span class="viz-insight-icon">🎯</span>
          <span>Green bars ≥75% = Excellent fit · Blue bars = Good fit · Red bars = Below average for your conditions</span>
        </div>
      </div>
    `;
  }

  // -- PROFIT ANALYSIS CHART --
  if (top3.length > 0) {
    html += `
      <div class="card viz-card" style="margin-bottom:var(--sp-xl);">
        <h3 class="section-title"><span class="icon">💰</span> Profit & Revenue Analysis</h3>
        <p class="viz-desc">Comparative financial analysis — Revenue (blue), Cost (red), and Net Profit trend (green line) for recommended crops</p>
        <div class="chart-container" style="position:relative;height:340px;">
          <canvas id="chart-profit"></canvas>
        </div>
        <div class="viz-insight">
          <span class="viz-insight-icon">📈</span>
          <span>The green line shows net profit trend. Higher green line = more profitable crop for your farm.</span>
        </div>
      </div>
    `;
  }

  // -- CROP BUBBLE CHART (Duration vs Suitability vs Profit) --
  if (allFeasible.length > 1 || top3.length > 1) {
    html += `
      <div class="card viz-card" style="margin-bottom:var(--sp-xl);">
        <h3 class="section-title"><span class="icon">🫧</span> Crop Intelligence Bubble Map</h3>
        <p class="viz-desc">Each bubble = one crop. X-axis = growing duration, Y-axis = suitability score, Bubble size = profit potential</p>
        <div class="chart-container" style="position:relative;height:360px;">
          <canvas id="chart-crop-bubble"></canvas>
        </div>
        <div class="viz-insight">
          <span class="viz-insight-icon">🔍</span>
          <span>Top-right = High suitability, longer growing. Top-left = High suitability, quick harvest. Larger bubble = higher profit.</span>
        </div>
      </div>
    `;
  }

  // -- FERTILIZER NPK DONUT + STAGES CHART --
  if (fert && (fert.recommended_fertilizer || (fert.stage_wise_application && fert.stage_wise_application.length > 0))) {
    html += `<div class="grid-2" style="margin-bottom:var(--sp-xl);">`;

    // NPK Donut
    const bf2 = fert.recommended_fertilizer || {};
    html += `
      <div class="card viz-card">
        <h3 class="section-title"><span class="icon">🧬</span> NPK Composition</h3>
        <p class="viz-desc">Nutrient ratio breakdown of the recommended fertilizer</p>
        <div class="chart-container" style="position:relative;max-width:320px;margin:0 auto;">
          <canvas id="chart-npk-donut"></canvas>
        </div>
        <div class="viz-insight">
          <span class="viz-insight-icon">🧪</span>
          <span>Recommended: ${bf2.fertilizer || '—'} · NPK Ratio: ${bf2.details?.npk || '—'} · Qty: ${bf2.details?.qty_per_ha || '—'} kg/ha</span>
        </div>
      </div>
    `;

    // Stages chart
    if (fert.stage_wise_application && fert.stage_wise_application.length > 0) {
      html += `
        <div class="card viz-card">
          <h3 class="section-title"><span class="icon">📅</span> Stage-wise Fertilizer Application</h3>
          <p class="viz-desc">NPK distribution across different crop growth stages</p>
          <div class="chart-container" style="position:relative;height:280px;">
            <canvas id="chart-fert-stages"></canvas>
          </div>
          <div class="viz-insight">
            <span class="viz-insight-icon">⏱️</span>
            <span>Apply the right nutrients at the right stage for maximum crop yield and resource efficiency</span>
          </div>
        </div>
      `;
    }
    html += `</div>`;
  }

  // ---- BACK BUTTON ----
  html += `
    <div style="text-align:center;margin-top:var(--sp-2xl);">
      <button class="btn btn-secondary btn-lg" id="new-analysis-btn">
        🔄 Start New Analysis
      </button>
    </div>
  `;

  // ---- Store data for chart initialization ----
  const chartPayload = {
    soilForChart,
    weather,
    top3,
    allFeasible,
    fert,
  };

  resultsEl.innerHTML = html;

  // ---- Initialize all charts after DOM render ----
  requestAnimationFrame(() => {
    setTimeout(() => {
      try {
        // Soil Radar
        createSoilRadarChart('chart-soil-radar', chartPayload.soilForChart);

        // Weather Gauge
        createWeatherGaugeChart('chart-weather-gauge', chartPayload.weather);

        // Crop Suitability
        const suitCrops = chartPayload.allFeasible.length > 0
          ? chartPayload.allFeasible.slice(0, 10)
          : chartPayload.top3;
        if (suitCrops.length > 0) {
          createCropSuitabilityChart('chart-crop-suitability', suitCrops);
        }

        // Profit Chart
        if (chartPayload.top3.length > 0) {
          const profitCrops = chartPayload.allFeasible.length > 2
            ? chartPayload.allFeasible.slice(0, 6)
            : chartPayload.top3;
          createProfitChart('chart-profit', profitCrops);
        }

        // Bubble Chart
        const bubbleCrops = chartPayload.allFeasible.length > 1
          ? chartPayload.allFeasible.slice(0, 8)
          : chartPayload.top3;
        if (bubbleCrops.length > 1) {
          createCropBubbleChart('chart-crop-bubble', bubbleCrops);
        }

        // Fertilizer NPK Donut
        if (chartPayload.fert && chartPayload.fert.recommended_fertilizer) {
          createNPKDonutChart('chart-npk-donut', chartPayload.fert.recommended_fertilizer);
        }

        // Fertilizer Stages
        if (chartPayload.fert?.stage_wise_application?.length > 0) {
          createFertilizerStageChart('chart-fert-stages', chartPayload.fert.stage_wise_application);
        }
      } catch (chartErr) {
        console.warn('Chart initialization error:', chartErr);
      }
    }, 150);
  });

  // Post-process table translations to avoid making 30x sequential requests blocking UI render
  if (lang !== 'en') {
    setTimeout(async () => {
      const cropEls = resultsEl.querySelectorAll('.t-crop');
      for (const el of cropEls) el.textContent = await translateDynamicText(el.dataset.crop, lang);
      const seasEls = resultsEl.querySelectorAll('.t-season');
      for (const el of seasEls) el.textContent = await translateDynamicText(el.dataset.season, lang);
    }, 100);
  }

  document.getElementById('new-analysis-btn')?.addEventListener('click', () => {
    farmData = {};
    goToStep(1);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}
