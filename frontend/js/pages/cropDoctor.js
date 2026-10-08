// ============================================
// AGRIFY Crop Doctor — Vision AI Pathology Lab
// Upload photo OR live camera scan
// ============================================

import { predictDisease } from '../api.js';
import { getLang } from '../i18n.js';
import { showToast } from '../voice.js';

// Detailed, real treatment database based on detected disease
// Each entry has specific dosage, timing, prevention steps (NOT generic)
const DISEASE_TREATMENT_DB = {
  'Early Blight': {
    severity: 'medium',
    severityLabel: 'Moderate',
    cause: 'Caused by Alternaria solani fungus. Spreads in warm (24–29°C), humid conditions with leaf wetness.',
    symptoms: [
      'Dark brown concentric ring spots on lower/older leaves',
      'Yellowing around lesions, leaves dry and fall',
      'Stems and tubers may also show sunken brown lesions',
    ],
    treatment: [
      { step: 'Immediate Spray', detail: 'Mancozeb 75% WP — 2.5 g/litre of water. Spray on all foliage, cover undersides of leaves.' },
      { step: 'Follow-up (7 days later)', detail: 'Chlorothalonil 75% WP — 2 g/litre. Repeat every 7–10 days if disease persists.' },
      { step: 'Alternative Organic', detail: 'Trichoderma viride (10 g/litre) OR copper oxychloride 50% WP (3 g/litre).' },
    ],
    prevention: [
      'Rotate crops every 2–3 years (avoid planting potato/tomato in same field)',
      'Remove and destroy infected plant debris after harvest',
      'Ensure adequate spacing (60×20 cm) for air circulation',
      'Avoid overhead irrigation — use drip or furrow method',
      'Treat seed tubers with Mancozeb dip (2.5 g/litre for 15 min) before planting',
    ],
    estimatedLoss: '20–40% yield loss if untreated. Early treatment can save 80% of the crop.',
  },
  'Late Blight': {
    severity: 'high',
    severityLabel: 'Severe — Act Immediately',
    cause: 'Caused by Phytophthora infestans (water mold). Spreads VERY fast in cool (10–20°C), wet weather. Can destroy entire field in 7–10 days.',
    symptoms: [
      'Water-soaked dark green/brown patches on leaves, spreading rapidly',
      'White fuzzy mold growth on leaf undersides (visible in morning dew)',
      'Stems turn dark and collapse; tubers rot with foul smell',
    ],
    treatment: [
      { step: 'URGENT First Spray', detail: 'Cymoxanil 8% + Mancozeb 64% WP (Curzate M8) — 3 g/litre. Spray immediately on all plants.' },
      { step: 'Second Spray (5 days)', detail: 'Metalaxyl 8% + Mancozeb 64% WP (Ridomil Gold) — 2.5 g/litre. Cover ALL foliage.' },
      { step: 'Copper Backup', detail: 'Bordeaux mixture (1%) OR copper hydroxide 77% WP (2 g/litre) as protective spray.' },
      { step: 'Remove Infected Plants', detail: 'Pull out and BURN severely infected plants immediately. Do not compost them.' },
    ],
    prevention: [
      'Plant certified disease-free seed tubers only',
      'Use resistant varieties: Kufri Jyoti, Kufri Badshah, Kufri Girdhari',
      'Avoid planting in low-lying, waterlogged areas',
      'Destroy all volunteer potato plants (self-sown from previous season)',
      'Prophylactic spray with Mancozeb if weather forecast shows continuous rain + cool temp',
    ],
    estimatedLoss: '80–100% crop loss if untreated! This is a crop emergency. Seek KVK help if widespread.',
  },
  'Healthy': {
    severity: 'low',
    severityLabel: 'No Disease Detected',
    cause: 'Your plant leaf shows no signs of disease. The crop appears to be in good condition.',
    symptoms: [],
    treatment: [
      { step: 'Continue Regular Care', detail: 'Maintain current watering schedule. Irrigate every 7–10 days depending on soil moisture.' },
      { step: 'Scheduled Nutrition', detail: 'Apply 50 kg Urea/ha at 30 days after planting (earthing-up stage). Follow with 25 kg MOP/ha.' },
      { step: 'Preventive Spray', detail: 'Prophylactic Mancozeb 2.5 g/litre spray every 15 days during monsoon to prevent fungal attack.' },
    ],
    prevention: [
      'Monitor field daily for any yellowing or spots on lower leaves',
      'Keep field weed-free — weeds harbor pests and compete for nutrients',
      'Ensure proper drainage to prevent waterlogging',
      'Install pheromone traps for potato tuber moth if in storage',
    ],
    estimatedLoss: 'No expected loss. Keep monitoring weekly for early signs of disease.',
  },
};

export function renderCropDoctor() {
  return `
    <div class="page-section crop-doctor-page">
      <!-- Crop Doctor Vision AI Hero Header -->
      <div class="cd-hero-header">
        <div class="cd-badge">
          <span class="badge-dot"></span>
          <span>AGRIFY VISION AI DIAGNOSTICS</span>
        </div>
        <h1 class="cd-title">🔬 Crop Doctor & Foliar Pathology</h1>
        <p class="cd-subtitle">
          Instant deep-learning leaf disease detection with chemical, biological, and preventive treatment protocols.
        </p>
        <div class="cd-trust-strip">
          <span class="trust-pill"><span class="pill-icon">🧠</span> Deep Learning Vision Model</span>
          <span class="trust-pill"><span class="pill-icon">📷</span> Field Macro & Live Camera Scan</span>
          <span class="trust-pill"><span class="pill-icon">💊</span> Actionable Treatment Protocols</span>
          <span class="trust-pill"><span class="pill-icon">👨‍🌾</span> Integrated Agronomist Escalation</span>
        </div>
      </div>

      <!-- Main Scanning Console Card -->
      <div class="card crop-doctor-card">
        <!-- Mode Selector -->
        <div class="cd-mode-selector">
          <button class="cd-mode-btn active" id="cd-mode-upload" data-mode="upload">
            📁 Upload Photo
          </button>
          <button class="cd-mode-btn" id="cd-mode-camera" data-mode="camera">
            📷 Live Camera Scan
          </button>
        </div>

        <!-- Upload Zone -->
        <div class="upload-zone" id="upload-zone">
          <div class="upload-icon-wrapper">
            <span class="upload-icon">📸</span>
          </div>
          <div class="upload-text">Click or drag a leaf photo here</div>
          <div class="upload-hint">JPG, PNG — auto-compressed for rapid AI analysis</div>
          <input type="file" id="leaf-input" accept="image/*" style="display:none;" />
        </div>

        <!-- Camera Zone -->
        <div id="camera-zone" style="display:none;">
          <div class="cd-camera-container" id="cd-camera-container">
            <video id="cd-video" autoplay playsinline class="cd-video"></video>
            <canvas id="cd-canvas" style="display:none;"></canvas>
            <div class="cd-camera-overlay">
              <div class="cd-camera-frame">
                <div class="cd-hud-corner tl"></div>
                <div class="cd-hud-corner tr"></div>
                <div class="cd-hud-corner bl"></div>
                <div class="cd-hud-corner br"></div>
              </div>
              <div class="cd-camera-hint">Position the infected leaf area inside the frame</div>
            </div>
          </div>
          <div style="display:flex;gap:var(--sp-md);justify-content:center;margin-top:var(--sp-lg);flex-wrap:wrap;">
            <button class="btn btn-accent btn-lg" id="cd-capture-btn">📸 Capture & Analyze</button>
            <button class="btn btn-secondary" id="cd-switch-cam-btn">🔄 Switch Camera</button>
          </div>
        </div>

        <!-- Preview -->
        <img id="leaf-preview" class="cd-leaf-preview" style="display:none;" alt="Leaf Preview" />

        <!-- Actions after upload -->
        <div class="cd-actions" id="cd-actions" style="display:none;">
          <button class="btn btn-accent btn-lg" id="cd-analyze-btn">🔬 Analyze Disease</button>
          <button class="btn btn-secondary" id="cd-change-btn">🔄 Change Photo</button>
        </div>

        <!-- Loading -->
        <div id="cd-loader" style="display:none;">
          <div class="card cd-loading-card">
            <div class="loading-spinner-wrap">
              <div class="spinner"></div>
            </div>
            <div class="loading-heading">Vision AI Analyzing Leaf</div>
            <div class="loading-subheading">🔬 Scanning foliar tissue for disease patterns...</div>
            <div class="loading-footnote">
              Evaluating lesion pigmentation, necroses, and texture against trained plant pathology models.
            </div>
            <div class="loading-pills-row">
              <span class="loading-pill active">🌿 Foliar Segmentation</span>
              <span class="loading-pill active">🔍 Lesion Detection</span>
              <span class="loading-pill">🧠 Pathology Matching</span>
            </div>
          </div>
        </div>

        <!-- Results -->
        <div id="cd-result" style="display:none;">
          <div id="cd-result-card"></div>
        </div>
      </div>

      <!-- Info Card -->
      <div class="card cd-info-card" style="margin-top:var(--sp-xl);">
        <h3 class="section-title"><span class="icon">📋</span> Supported Crops & Diagnostic Pipeline</h3>
        <div class="grid-3" style="gap:var(--sp-md);">
          <div class="stat-card cd-crop-stat">
            <div class="stat-icon green">🥔</div>
            <div class="stat-label">Potato</div>
            <div style="font-size:0.8rem;color:var(--c-text-secondary);margin-top:4px;">
              Early Blight, Late Blight, Healthy detection
            </div>
            <span class="cd-model-status live">● LIVE AI MODEL</span>
          </div>
          <div class="stat-card cd-crop-stat">
            <div class="stat-icon amber">🍅</div>
            <div class="stat-label">Tomato</div>
            <div style="font-size:0.8rem;color:var(--c-text-muted);margin-top:4px;">
              Leaf curl, Mosaic virus, Septoria
            </div>
            <span class="cd-model-status coming">○ PIPELINE IN TRAINING</span>
          </div>
          <div class="stat-card cd-crop-stat">
            <div class="stat-icon blue">🌶️</div>
            <div class="stat-label">Chilli</div>
            <div style="font-size:0.8rem;color:var(--c-text-muted);margin-top:4px;">
              Anthracnose, Powdery mildew, Leaf spot
            </div>
            <span class="cd-model-status coming">○ PIPELINE IN TRAINING</span>
          </div>
        </div>
        <div class="cd-tip-box" style="margin-top:var(--sp-md);">
          <span class="tip-icon">💡</span>
          <span class="tip-text">For the highest diagnostic confidence, frame a single leaf flat against natural diffuse daylight, avoiding extreme glare or heavy shadows.</span>
        </div>
      </div>
    </div>
  `;
}

let cameraStream = null;
let useFrontCamera = false;

export function initCropDoctor() {
  const uploadZone = document.getElementById('upload-zone');
  const cameraZone = document.getElementById('camera-zone');
  const fileInput = document.getElementById('leaf-input');
  const preview = document.getElementById('leaf-preview');
  const actions = document.getElementById('cd-actions');
  const analyzeBtn = document.getElementById('cd-analyze-btn');
  const changeBtn = document.getElementById('cd-change-btn');
  const loader = document.getElementById('cd-loader');
  const resultDiv = document.getElementById('cd-result');

  // ---- Mode Toggle: Upload vs Camera ----
  document.querySelectorAll('.cd-mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.cd-mode-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const mode = btn.dataset.mode;
      if (mode === 'upload') {
        uploadZone.style.display = 'flex';
        cameraZone.style.display = 'none';
        stopCamera();
      } else {
        uploadZone.style.display = 'none';
        cameraZone.style.display = 'block';
        startCamera();
      }
      // Reset state
      preview.style.display = 'none';
      actions.style.display = 'none';
      resultDiv.style.display = 'none';
    });
  });

  // ---- Upload Click ----
  uploadZone?.addEventListener('click', () => fileInput?.click());

  // ---- Drag & Drop ----
  uploadZone?.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('drag-over');
  });
  uploadZone?.addEventListener('dragleave', () => {
    uploadZone.classList.remove('drag-over');
  });
  uploadZone?.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    const files = e.dataTransfer?.files;
    if (files && files[0]) handleFileSelect(files[0]);
  });

  // ---- File input change ----
  fileInput?.addEventListener('change', () => {
    const file = fileInput.files?.[0];
    if (file) handleFileSelect(file);
  });

  function handleFileSelect(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      preview.src = e.target.result;
      preview.style.display = 'block';
      uploadZone.style.display = 'none';
      cameraZone.style.display = 'none';
      actions.style.display = 'flex';
      resultDiv.style.display = 'none';
    };
    reader.readAsDataURL(file);
  }

  // ---- Change Photo ----
  changeBtn?.addEventListener('click', () => {
    resetToUpload();
  });

  // ---- Analyze from uploaded file ----
  analyzeBtn?.addEventListener('click', async () => {
    const file = fileInput?.files?.[0];
    if (!file) {
      showToast('No image selected', 'error');
      return;
    }
    // Compress file before upload to make it much faster
    try {
      const compressedFile = await compressImage(file, 800);
      await analyzeImage(compressedFile);
    } catch (e) {
      await analyzeImage(file); // fallback to original
    }
  });

  // ---- Camera: Capture ----
  document.getElementById('cd-capture-btn')?.addEventListener('click', async () => {
    const video = document.getElementById('cd-video');
    const canvas = document.getElementById('cd-canvas');
    if (!video || !canvas) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    // Convert canvas to blob/file
    canvas.toBlob(async (blob) => {
      if (!blob) {
        showToast('Failed to capture image', 'error');
        return;
      }
      const file = new File([blob], 'leaf-capture.jpg', { type: 'image/jpeg' });

      // Show preview
      preview.src = canvas.toDataURL('image/jpeg');
      preview.style.display = 'block';
      cameraZone.style.display = 'none';
      stopCamera();

      await analyzeImage(file);
    }, 'image/jpeg', 0.9);
  });

  // ---- Switch Camera ----
  document.getElementById('cd-switch-cam-btn')?.addEventListener('click', () => {
    useFrontCamera = !useFrontCamera;
    startCamera();
  });

  // ---- Core Analyze Function ----
  async function analyzeImage(file) {
    actions.style.display = 'none';
    loader.style.display = 'block';
    resultDiv.style.display = 'none';

    try {
      const data = await predictDisease(file, getLang());
      loader.style.display = 'none';
      resultDiv.style.display = 'block';
      renderResult(data);
    } catch (err) {
      loader.style.display = 'none';
      actions.style.display = 'flex';
      showToast(`Error: ${err.message}`, 'error');
    }
  }

  // ---- Render Detailed Results ----
  function renderResult(data) {
    const card = document.getElementById('cd-result-card');
    if (!card || !data) return;

    if (data.is_recognized === false) {
      card.innerHTML = `
        <div class="card cd-unrecognized-card" style="text-align:center;padding:var(--sp-2xl);margin-bottom:var(--sp-xl);">
          <div style="font-size:3.5rem;margin-bottom:var(--sp-md);">🤷</div>
          <div style="font-family:var(--font-display);font-size:1.6rem;font-weight:800;color:var(--c-text);margin-bottom:8px;">No Supported Crop Match Found</div>
          <p style="color:var(--c-text-secondary);font-size:0.95rem;max-width:440px;margin:0 auto var(--sp-lg);line-height:1.6;">
            The uploaded image was not recognized as a supported crop leaf (potato, etc.). Please ensure the photo clearly captures a single crop leaf in natural lighting.
          </p>
          <button class="btn btn-secondary btn-lg" id="cd-scan-again">🔄 Try Again</button>
        </div>
      `;
      document.getElementById('cd-scan-again')?.addEventListener('click', resetToUpload);
      return;
    }

    const isHealthy = data.is_healthy;
    const diag = data.diagnosis || {};
    const scores = data.all_scores || [];
    const diseaseName = diag.name || 'Unknown';

    // Get detailed treatment info from our local DB
    const details = DISEASE_TREATMENT_DB[diseaseName] || DISEASE_TREATMENT_DB['Healthy'];
    const sevColors = { low: 'var(--c-success)', medium: 'var(--c-accent)', high: '#ef4444' };
    const sevBg = { low: 'rgba(34,197,94,0.08)', medium: 'rgba(245,158,11,0.08)', high: 'rgba(239,68,68,0.08)' };
    const sevBorder = { low: 'rgba(34,197,94,0.25)', medium: 'rgba(245,158,11,0.25)', high: 'rgba(239,68,68,0.3)' };

    let html = '';

    // ---- Fallback Mode Indicator ----
    if (data.analysis_mode === 'local_fallback') {
      html += `
        <div class="cd-offline-banner" style="margin-bottom:var(--sp-lg);">
          <span class="offline-icon">🔌</span>
          <div>
            <div class="offline-title">Local Fallback Analysis Mode</div>
            <div class="offline-desc">
              The neural vision server is initializing. This result uses local leaf pigmentation heuristic analysis as a preliminary estimate. Full AI deep-learning model will activate shortly.
            </div>
          </div>
        </div>
      `;
    }

    // ---- Diagnosis Header ----
    html += `
      <div class="cd-diagnosis-hero" style="background:${sevBg[details.severity]};border:1px solid ${sevBorder[details.severity]};margin-bottom:var(--sp-xl);">
        <div class="diagnosis-status-icon">${isHealthy ? '✅' : '⚠️'}</div>
        <div class="diagnosis-disease-name" style="color:${sevColors[details.severity]};">${diseaseName}</div>
        <div class="diagnosis-severity-wrap">
          <span>Pathology Severity:</span>
          <span class="severity-badge-pill" style="color:${sevColors[details.severity]};border-color:${sevColors[details.severity]};">${details.severityLabel}</span>
        </div>
      </div>
    `;

    // ---- Confidence Scores ----
    html += `
      <div class="card cd-confidence-card" style="margin-bottom:var(--sp-lg);padding:var(--sp-lg);">
        <h3 class="section-title"><span class="icon">📊</span> AI Detection Confidence</h3>
        <div style="display:flex;flex-direction:column;gap:var(--sp-sm);margin-top:var(--sp-sm);">
          ${scores.map((s, i) => `
            <div class="confidence-row">
              <span class="confidence-name ${i === 0 ? 'top' : ''}">${s.name}</span>
              <div class="confidence-track">
                <div class="confidence-fill" style="width:${s.conf}%;background:${i === 0 ? (isHealthy ? 'var(--c-success)' : sevColors[details.severity]) : 'var(--c-text-dim)'};"></div>
              </div>
              <span class="confidence-pct ${i === 0 ? 'top' : ''}" style="${i === 0 ? `color:${sevColors[details.severity]};` : ''}">${s.conf}%</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    // ---- Cause ----
    html += `
      <div class="card" style="margin-bottom:var(--sp-lg);padding:var(--sp-lg);">
        <h3 class="section-title"><span class="icon">🔍</span> About This Condition</h3>
        <p style="font-size:0.9rem;color:var(--c-text-secondary);line-height:1.7;">${details.cause}</p>
        ${details.symptoms.length ? `
          <div style="margin-top:var(--sp-md);">
            <div style="font-weight:700;font-size:0.85rem;margin-bottom:var(--sp-sm);color:var(--c-text);">Typical Field Symptoms:</div>
            <ul style="list-style:none;padding:0;display:flex;flex-direction:column;gap:6px;">
              ${details.symptoms.map(s => `
                <li style="display:flex;gap:8px;font-size:0.83rem;color:var(--c-text-secondary);line-height:1.5;">
                  <span style="flex-shrink:0;color:${sevColors[details.severity]};">•</span> ${s}
                </li>
              `).join('')}
            </ul>
          </div>
        ` : ''}
      </div>
    `;

    // ---- Treatment Steps ----
    html += `
      <div class="card" style="margin-bottom:var(--sp-lg);padding:var(--sp-lg);">
        <h3 class="section-title"><span class="icon">💊</span> Actionable Treatment Protocol</h3>
        <div style="display:flex;flex-direction:column;gap:var(--sp-md);margin-top:var(--sp-sm);">
          ${details.treatment.map((t, i) => `
            <div class="treatment-step-card" style="border-left:3px solid ${sevColors[details.severity]};">
              <span class="step-num" style="color:${sevColors[details.severity]};">${i + 1}</span>
              <div>
                <div class="step-title">${t.step}</div>
                <div class="step-detail">${t.detail}</div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    // ---- Prevention ----
    html += `
      <div class="card" style="margin-bottom:var(--sp-lg);padding:var(--sp-lg);">
        <h3 class="section-title"><span class="icon">🛡️</span> Cultural & Preventive Field Measures</h3>
        <ul class="solution-list" style="margin-top:var(--sp-sm);">
          ${details.prevention.map(p => `<li>${p}</li>`).join('')}
        </ul>
      </div>
    `;

    // ---- Yield Impact ----
    html += `
      <div class="yield-impact-banner" style="background:${sevBg[details.severity]};border:1px solid ${sevBorder[details.severity]};margin-bottom:var(--sp-xl);">
        📉 <strong>Projected Yield Impact:</strong> ${details.estimatedLoss}
      </div>
    `;

    // ---- Ask Expert & Scan Again ----
    html += `
      <div style="display:flex; gap:var(--sp-md); justify-content:center; flex-wrap:wrap; margin-top:var(--sp-xl);">
        ${!isHealthy ? '<button class="btn btn-accent btn-lg" id="cd-ask-expert">👨‍🌾 Ask an Expert</button>' : ''}
        <button class="btn btn-primary btn-lg" id="cd-scan-again">🔄 Scan Another Leaf</button>
      </div>
    `;

    card.innerHTML = html;

    document.getElementById('cd-scan-again')?.addEventListener('click', () => {
      resetToUpload();
    });
    document.getElementById('cd-ask-expert')?.addEventListener('click', () => {
      window.dispatchEvent(new CustomEvent('navigate', { detail: 'experts' }));
    });
  }

  function resetToUpload() {
    preview.style.display = 'none';
    preview.src = '';
    uploadZone.style.display = 'flex';
    cameraZone.style.display = 'none';
    actions.style.display = 'none';
    resultDiv.style.display = 'none';
    if (fileInput) fileInput.value = '';
    stopCamera();

    // Reset mode buttons
    document.querySelectorAll('.cd-mode-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('cd-mode-upload')?.classList.add('active');
  }
}

// ---- Camera Helpers ----
async function startCamera() {
  stopCamera();
  const video = document.getElementById('cd-video');
  if (!video) return;

  try {
    const constraints = {
      video: {
        facingMode: useFrontCamera ? 'user' : 'environment',
        width: { ideal: 1280 },
        height: { ideal: 720 },
      }
    };
    cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
    video.srcObject = cameraStream;
  } catch (err) {
    showToast('Camera not available: ' + err.message, 'error');
    // Fallback to upload mode
    document.getElementById('upload-zone').style.display = 'flex';
    document.getElementById('camera-zone').style.display = 'none';
    document.querySelectorAll('.cd-mode-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('cd-mode-upload')?.classList.add('active');
  }
}

function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(track => track.stop());
    cameraStream = null;
  }
  const video = document.getElementById('cd-video');
  if (video) video.srcObject = null;
}

// Helper: compress image before upload so API is fast
function compressImage(file, maxSize) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = event => {
      const img = new Image();
      img.src = event.target.result;
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let width = img.width;
        let height = img.height;

        if (width > height) {
          if (width > maxSize) { height *= maxSize / width; width = maxSize; }
        } else {
          if (height > maxSize) { width *= maxSize / height; height = maxSize; }
        }

        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob(blob => {
          if (blob) {
            resolve(new File([blob], file.name, { type: 'image/jpeg' }));
          } else {
            reject(new Error('Canvas to Blob failed'));
          }
        }, 'image/jpeg', 0.85);
      };
      img.onerror = error => reject(error);
    };
    reader.onerror = error => reject(error);
  });
}
