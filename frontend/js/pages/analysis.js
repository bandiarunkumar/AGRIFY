// ============================================================
// AGRIFY Farm Intelligence Analyzer — Precision Planning Workflow
// ============================================================

import { analyzeFarm, getFarmActionPlan, getSoilByCoords, getWeatherByCoords, getSoilAnalysis, getCurrentPosition, reverseGeocode } from '../api.js';
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
          Crop and nutrient guidance using your farm coordinates, SoilGrids modeled layers where available, and weather feeds when available.
        </p>
        <div class="analysis-trust-strip">
          <span class="trust-pill"><span class="pill-icon">📍</span> GPS Micro-Targeting</span>
          <span class="trust-pill"><span class="pill-icon">🧪</span> Modeled Soil Estimates</span>
          <span class="trust-pill"><span class="pill-icon">🌤️</span> Weather When Available</span>
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
                Acquire GPS coordinates for your field. Available weather and SoilGrids data are linked to the coordinates rather than a municipal average.
              </p>
            </div>

            <!-- GPS Primary Button & Telemetry Panel -->
            <div class="gps-capture-panel">
              <div class="gps-hero-badge">📍 GPS Coordinates</div>
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
                <div class="radar-status-msg">📍 Waiting for farm coordinates...</div>
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
                <span class="gps-coord-preview">GPS Location</span>
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
                <label for="w-annual-rain">Annual Rainfall <span class="hint">(mm, leave 0 to use available inputs or regional estimates)</span></label>
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
                Soil chemistry affects crop growth. Fetch modeled SoilGrids layers where available, or enter laboratory measurements from your local Krishi Vigyan Kendra (KVK) card.
              </p>
            </div>

            <!-- Auto-fetch soil button -->
            <div class="satellite-fetch-banner">
              <div class="banner-badge">🧪 SOILGRIDS MODEL</div>
              <div class="banner-title">Fetch Modeled Soil Data</div>
              <p class="banner-desc">
                Fetches SoilGrids modeled soil layers where available. Phosphorus, potassium, moisture, and some nutrient fields are estimates, not laboratory measurements.
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

    // Publish session-level AGRIFY location context
    if (typeof window !== 'undefined' && Number.isFinite(lat) && Number.isFinite(lon)) {
      const locSnapshot = {
        latitude: lat,
        longitude: lon,
        ...(farmData.geo && typeof farmData.geo === 'object' ? farmData.geo : {}),
      };
      window._agrifyLocation = locSnapshot;
      try {
        sessionStorage.setItem('agrify_session_location', JSON.stringify(locSnapshot));
      } catch (_) {}
    }

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

    // Publish session-level AGRIFY location context immediately upon capture
    if (typeof window !== 'undefined' && Number.isFinite(pos.lat) && Number.isFinite(pos.lon)) {
      const locSnapshot = {
        latitude: pos.lat,
        longitude: pos.lon,
        ...(farmData.geo && typeof farmData.geo === 'object' ? farmData.geo : {}),
      };
      window._agrifyLocation = locSnapshot;
      try {
        sessionStorage.setItem('agrify_session_location', JSON.stringify(locSnapshot));
      } catch (_) {}
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

      btn.textContent = '⌛ Fetching modeled soil data...';
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

      const estimated = soil.data_quality === 'estimated' || soil.fallback;
      const qualityLabel = estimated ? '⚠️ Modeled estimate — confirm with a soil lab' : '✅ Soil data loaded';
      noteDiv.innerHTML = `
        <div class="soil-note-badge ${soil.fallback ? 'warning' : 'success'}">${qualityLabel}</div>
      `;

      status.textContent = estimated ? '⚠️ Modeled estimate loaded' : '✅ Loaded';
      showToast(
        estimated
          ? '⚠️ Soil data are modeled estimates; use a lab report for field-specific accuracy.'
          : `✅ Soil data loaded for (${farmData.lat.toFixed(3)}, ${farmData.lon.toFixed(3)})`,
        estimated ? 'warning' : 'success'
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
        Preparing available weather and modeled soil inputs for crop suitability ranking.
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
    // Voice Copilot reads this shared in-memory snapshot when it builds the
    // existing /api/assistant/query context.  Only publish coordinates after
    // Farm Analyzer has successfully completed with coordinates the farmer
    // explicitly captured or entered here; Voice Copilot never requests GPS.
    if (typeof window !== 'undefined' && Number.isFinite(payload.latitude) && Number.isFinite(payload.longitude)) {
      const analysisLocation = result.location && typeof result.location === 'object'
        ? result.location
        : {};

      window._agrifyAnalysisData = {
        ...result,
        request: {
          ...payload,
          active_crop: result.crop_recommendation?.top_3?.[0]?.crop || payload.previous_crop,
        },
        location: {
          ...analysisLocation,
          latitude: payload.latitude,
          longitude: payload.longitude,
        },
      };
      window._agrifyLocation = window._agrifyAnalysisData.location;
      try {
        sessionStorage.setItem('agrify_session_location', JSON.stringify(window._agrifyLocation));
      } catch (_) {}
    }
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
  const recommendationQuality = result.crop_recommendation?.data_quality || 'estimated';
  const recommendationNote = result.crop_recommendation?.data_quality_note || 'Some inputs are modeled or unavailable. Treat recommendations as preliminary.';
  const climateContext = weather.ok
    ? `Weather feed returned ${weather.temperature}°C and ${weather.humidity}% humidity.`
    : 'Weather data was unavailable; regional fallback values were used for ranking.';

  let html = '';

  if (recommendationQuality !== 'live') {
    html += `
      <div class="card" role="note" style="margin-bottom:var(--sp-lg);border-color:var(--c-accent);">
        <strong>Preliminary recommendation · ${recommendationQuality}</strong>
        <p style="margin:.4rem 0 0;color:var(--c-text-secondary);">${recommendationNote}</p>
      </div>
    `;
  }

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
        <span class="meta-strip-label">🤖 Recommendation Method</span>
        <span class="meta-strip-value"><span class="badge-dot"></span> Hybrid rule + model ranking</span>
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
            ${climateContext} Ranked using the available soil inputs and ${payload.season} season.
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
              <span class="metric-label">Illustrative Profit · Not a Forecast</span>
              <span class="metric-value profit">₹${(crop.net_profit_estimated || 0).toLocaleString()}</span>
            </div>
          </div>
          ${crop.reason ? `<div class="crop-reason-box">${reasonTr}</div>` : ''}
        </div>
      `;
    }
    html += `</div></div>`;
  }

  // ---- AVAILABLE DATA SUMMARY ----
  html += `
    <div class="grid-2 analysis-summary-grid" style="margin-bottom:var(--sp-xl);">
      <div class="card">
        <h3 class="section-title"><span class="icon">📍</span> Location & Weather</h3>
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
          <span class="metric-value">${weather.ok ? `${weather.temperature}°C (feels ${weather.feels_like}°C)` : 'Unavailable'}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">Humidity</span>
          <span class="metric-value">${weather.ok ? `${weather.humidity}%` : 'Unavailable'}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">Weather</span>
          <span class="metric-value">${weather.ok ? await translateDynamicText((weather.description || '—'), lang) : 'Unavailable'}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">Wind</span>
          <span class="metric-value">${weather.ok ? `${weather.wind_speed} m/s` : 'Unavailable'}</span>
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
                <th>Illustrative Profit Est.</th>
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
                  <td style="color:var(--c-success);" aria-label="Illustrative profit estimate">₹${(crop.net_profit_estimated || 0).toLocaleString()}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  // ============================================================
  // 📋 AI FARM ACTION PLAN (Async Non-Blocking Workspace)
  // ============================================================
  html += `
    <div id="farm-action-plan-section" style="margin-bottom:var(--sp-xl);">
      <div class="card action-plan-card action-plan-loading">
        <div class="action-plan-header">
          <div class="action-plan-heading-group">
            <span class="action-plan-badge">🌱 AGRIFY ADVISORY WORKSPACE</span>
            <h3 class="action-plan-title">📋 7-Day Farm Action Plan</h3>
          </div>
          <span class="action-plan-source-badge pulse">⏳ Synthesizing Plan...</span>
        </div>
        <p class="action-plan-loading-text">
          Synthesizing your field's live weather telemetry, soil nutrition, irrigation schedule, and active field alerts into prioritized daily actions.
        </p>
        <div class="action-plan-skeleton-bars">
          <div class="skeleton-line" style="height:14px;width:75%;margin-bottom:8px;"></div>
          <div class="skeleton-line" style="height:12px;width:90%;margin-bottom:8px;"></div>
          <div class="skeleton-line" style="height:12px;width:60%;"></div>
        </div>
      </div>
    </div>
  `;

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
          <span>${weather.ok ? `Weather feed: ${weather.temperature}°C · ${weather.humidity}% humidity · ${weather.wind_speed} m/s wind` : 'Weather feed unavailable; regional fallback values were used for crop ranking.'}</span>
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
        <h3 class="section-title"><span class="icon">💰</span> Illustrative Profit & Revenue Estimates</h3>
        <p class="viz-desc">Comparative estimates based on reference crop prices and yields, not current mandi prices or a farm-specific profit forecast.</p>
        <div class="chart-container" style="position:relative;height:340px;">
          <canvas id="chart-profit"></canvas>
        </div>
        <div class="viz-insight">
          <span class="viz-insight-icon">📈</span>
          <span>The green line shows the reference estimate. Actual yields, costs, and selling prices will vary.</span>
        </div>
      </div>
    `;
  }

  // -- CROP BUBBLE CHART (Duration vs Suitability vs Profit) --
  if (allFeasible.length > 1 || top3.length > 1) {
    html += `
      <div class="card viz-card" style="margin-bottom:var(--sp-xl);">
        <h3 class="section-title"><span class="icon">🫧</span> Crop Intelligence Bubble Map</h3>
        <p class="viz-desc">Each bubble = one crop. X-axis = growing duration, Y-axis = suitability score, and size = illustrative reference profit estimate.</p>
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

  // Asynchronously trigger Action Plan generation without blocking charts or page render
  loadFarmActionPlan(result, payload);
}

// ============================================================
// 📋 FARM ACTION PLAN HELPERS
// ============================================================
let currentAnalysisContext = null;

async function loadFarmActionPlan(result, payload) {
  currentAnalysisContext = { result, payload };
  const container = document.getElementById('farm-action-plan-section');
  if (!container) return;

  const rawLang = window.localStorage.getItem('lang') || 'en';
  const lang = ['en', 'te', 'hi'].includes(rawLang) ? rawLang : 'en';
  const targetCrop = result?.crop_recommendation?.top_3?.[0]?.crop || payload?.previous_crop || 'Crop';

  try {
    const plan = await getFarmActionPlan({
      analysis: result,
      crop: targetCrop,
      language: lang,
    });

    if (plan && plan.status === 'success') {
      renderActionPlanUI(plan, container, result, payload);
    } else {
      renderActionPlanFallbackUI(container, result, payload);
    }
  } catch (err) {
    console.warn('Action plan non-blocking fetch error:', err);
    renderActionPlanFallbackUI(container, result, payload);
  }
}

function renderActionPlanUI(plan, container, result, payload) {
  const isGemini = plan.source === 'gemini_ai';
  const sourceLabel = isGemini ? '✨ AGRIFY AI' : '⚙️ AGRIFY Rule Engine';
  const sourceClass = isGemini ? 'gemini' : 'rule';

  const immediateActions = plan.immediate_actions || [];
  const weekPlan = plan.this_week_plan || [];
  const keyRisks = plan.key_risks || [];
  const expertQuestions = plan.expert_questions || [];

  let immediateHtml = '';
  if (immediateActions.length > 0) {
    immediateHtml = `
      <div class="action-plan-subsection">
        <h4 class="action-plan-section-title">⚡ Immediate Priority Actions</h4>
        <div class="action-plan-immediate-grid">
          ${immediateActions.map(act => {
            const prio = (act.priority || 'medium').toLowerCase();
            const prioClass = prio === 'high' ? 'high' : (prio === 'low' ? 'low' : 'medium');
            return `
              <div class="action-item-card priority-${prioClass}">
                <div class="action-item-top">
                  <span class="action-category-tag">${act.category || 'Advisory'}</span>
                  <span class="priority-pill ${prioClass}">${prio.toUpperCase()} PRIORITY</span>
                </div>
                <div class="action-item-title">${act.title}</div>
                <div class="action-item-text">${act.action}</div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  }

  let scheduleHtml = '';
  if (weekPlan.length > 0) {
    scheduleHtml = `
      <div class="action-plan-subsection" style="margin-top:var(--sp-xl);">
        <h4 class="action-plan-section-title">📅 7-Day Advisory Schedule</h4>
        <div class="action-plan-timeline">
          ${weekPlan.map((step, idx) => `
            <div class="timeline-step-card">
              <div class="timeline-step-header">
                <span class="timeline-period-badge">${step.period || `Phase ${idx+1}`}</span>
                <span class="timeline-focus-title">${step.focus || ''}</span>
              </div>
              <ul class="timeline-task-list">
                ${(step.tasks || []).map(task => `
                  <li class="timeline-task-item">
                    <span class="timeline-check-icon">✓</span>
                    <span>${task}</span>
                  </li>
                `).join('')}
              </ul>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  let risksHtml = '';
  if (keyRisks.length > 0) {
    risksHtml = `
      <div class="action-plan-subsection" style="margin-top:var(--sp-xl);">
        <h4 class="action-plan-section-title">⚠️ Field Risk & Mitigation</h4>
        <div class="action-plan-risks-grid">
          ${keyRisks.map(r => `
            <div class="action-risk-card severity-${r.severity || 'warning'}">
              <div class="risk-card-title">⚠️ ${r.risk}</div>
              <div class="risk-card-mitigation"><span class="mitigation-label">Mitigation:</span> ${r.mitigation}</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  let expertsHtml = '';
  if (expertQuestions.length > 0) {
    expertsHtml = `
      <div class="action-plan-expert-card">
        <div class="expert-card-top">
          <div>
            <div class="expert-card-badge">👨‍🌾 KVK & EXTENSION ESCALATION</div>
            <h4 class="expert-card-title">Questions to Discuss With an Agriculture Expert</h4>
            <p class="expert-card-subtext">
              These targeted questions are formulated from your field telemetry and nutrient analysis for consultation with your local Krishi Vigyan Kendra (KVK) specialist or Agriculture Extension Officer.
            </p>
          </div>
          <button class="btn btn-sm btn-outline-primary btn-expert-cta" id="action-plan-experts-btn">
            👨‍🌾 Browse Expert Directory →
          </button>
        </div>
        <div class="expert-questions-list">
          ${expertQuestions.map(q => `
            <div class="expert-question-item">
              <span class="expert-q-icon">💬</span>
              <span class="expert-q-text">${q}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  const disclaimerHtml = `
    <div class="action-plan-disclaimer">
      <span class="disclaimer-icon">🛡️</span>
      <span>${plan.disclaimer || 'This Action Plan is an advisory guide based on available weather and modeled soil inputs. It does not guarantee specific yields or profits. Verify with your local agriculture extension officer.'}</span>
    </div>
  `;

  container.innerHTML = `
    <div class="card action-plan-card">
      <div class="action-plan-header">
        <div class="action-plan-heading-group">
          <span class="action-plan-badge">🌱 AGRIFY ADVISORY WORKSPACE</span>
          <h3 class="action-plan-title">📋 7-Day Farm Action Plan</h3>
        </div>
        <span class="action-plan-source-badge ${sourceClass}">${sourceLabel}</span>
      </div>

      <div class="action-plan-summary">
        <span class="summary-icon">💡</span>
        <div class="summary-text">${plan.summary}</div>
      </div>

      ${immediateHtml}
      ${scheduleHtml}
      ${risksHtml}
      ${expertsHtml}
      ${disclaimerHtml}
    </div>
  `;

  // Attach event listener to expert directory CTA button
  container.querySelector('#action-plan-experts-btn')?.addEventListener('click', () => {
    window.dispatchEvent(new CustomEvent('navigate', { detail: 'experts' }));
  });
}

function renderActionPlanFallbackUI(container, result, payload) {
  container.innerHTML = `
    <div class="card action-plan-card action-plan-fallback">
      <div class="action-plan-header">
        <div class="action-plan-heading-group">
          <span class="action-plan-badge">📋 AGRIFY ADVISORY</span>
          <h3 class="action-plan-title">📋 7-Day Farm Action Plan</h3>
        </div>
        <span class="action-plan-source-badge fallback">⚠️ Advisory Preview Offline</span>
      </div>
      <p class="action-plan-fallback-text" style="font-size:0.86rem;color:var(--c-text-muted);margin:var(--sp-sm) 0 var(--sp-md);">
        Unable to generate the automated 7-day action schedule right now. Your crop recommendations, fertilizer analysis, and irrigation guidance above are active and complete.
      </p>
      <button class="btn btn-sm btn-secondary" id="retry-action-plan-btn">
        🔄 Retry Action Plan
      </button>
    </div>
  `;

  container.querySelector('#retry-action-plan-btn')?.addEventListener('click', () => {
    container.innerHTML = `
      <div class="card action-plan-card action-plan-loading">
        <div class="action-plan-header">
          <div class="action-plan-heading-group">
            <span class="action-plan-badge">🌱 AGRIFY ADVISORY WORKSPACE</span>
            <h3 class="action-plan-title">📋 7-Day Farm Action Plan</h3>
          </div>
          <span class="action-plan-source-badge pulse">⏳ Synthesizing Plan...</span>
        </div>
        <p class="action-plan-loading-text">
          Retrying action plan synthesis for your farm coordinates...
        </p>
      </div>
    `;
    loadFarmActionPlan(result, payload);
  });
}

// Listen for language changes to keep Action Plan updated dynamically
if (typeof window !== 'undefined') {
  window.addEventListener('langChange', () => {
    if (currentAnalysisContext && document.getElementById('farm-action-plan-section')) {
      loadFarmActionPlan(currentAnalysisContext.result, currentAnalysisContext.payload);
    }
  });
}
