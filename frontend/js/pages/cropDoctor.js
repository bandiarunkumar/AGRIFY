// ============================================
// AGRIFY Crop Doctor — Vision AI Pathology Lab
// Upload photo OR live camera scan
// ============================================

import { predictDisease } from '../api.js';
import { getLang } from '../i18n.js';
import { showToast } from '../voice.js';

// Crop Doctor predictions are limited to the potato classes listed below.

export function renderCropDoctor() {
  return `
    <div class="page-section crop-doctor-page">
      <!-- Crop Doctor Vision AI Hero Header -->
      <div class="cd-hero-header">
        <div class="cd-badge">
          <span class="badge-dot"></span>
          <span>POTATO LEAF IMAGE SCREENING</span>
        </div>
        <h1 class="cd-title">🔬 Crop Doctor & Foliar Pathology</h1>
        <p class="cd-subtitle">
          A model screening service for potato early blight, late blight, and healthy leaf classes. Results can be wrong; confirm field symptoms locally before treatment.
        </p>
        <div class="cd-trust-strip">
          <span class="trust-pill"><span class="pill-icon">🧠</span> Deep Learning Vision Model</span>
          <span class="trust-pill"><span class="pill-icon">📷</span> Field Macro & Live Camera Scan</span>
          <span class="trust-pill"><span class="pill-icon">💊</span> Confirm with a local expert</span>
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
        <div class="upload-zone" id="upload-zone" role="button" tabindex="0" aria-controls="leaf-input" aria-label="Choose a crop leaf photo">
          <div class="upload-icon-wrapper">
            <span class="upload-icon">📸</span>
          </div>
          <div class="upload-text">Click or drag a leaf photo here</div>
          <div class="upload-hint">JPG, PNG, WEBP — max 4.5 MB; auto-compressed before upload</div>
          <input type="file" id="leaf-input" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" style="display:none;" />
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
              Checking this image against the supported potato classes. No diagnosis is shown if the service is unavailable.
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
  uploadZone?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInput?.click(); }
  });

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
    const supportedTypes = new Set(['image/jpeg', 'image/png', 'image/webp']);
    if (!supportedTypes.has(file.type)) {
      showToast('Upload a JPG, PNG, or WEBP image.', 'warning');
      if (fileInput) fileInput.value = '';
      return;
    }
    if (file.size > 4.5 * 1024 * 1024) {
      showToast('Image must be 4.5 MB or smaller.', 'warning');
      if (fileInput) fileInput.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      preview.src = e.target.result;
      preview.style.display = 'block';
      uploadZone.style.display = 'none';
      cameraZone.style.display = 'none';
      actions.style.display = 'flex';
      resultDiv.style.display = 'none';
    };
    reader.onerror = () => showToast('The selected image could not be read.', 'error');
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
      resultDiv.style.display = 'block';
      const card = document.getElementById('cd-result-card');
      if (card) {
        card.innerHTML = `
          <div class="card cd-unrecognized-card" role="alert" style="text-align:center;padding:var(--sp-2xl);margin-bottom:var(--sp-xl);">
            <div style="font-size:2.5rem;margin-bottom:var(--sp-md);">📡</div>
            <h3 class="market-empty-title">Diagnosis unavailable</h3>
            <p class="market-empty-desc" id="cd-error-message"></p>
            <button class="btn btn-secondary btn-lg" id="cd-retry-analysis">Try this image again</button>
          </div>
        `;
        card.querySelector('#cd-error-message').textContent = err.message;
        card.querySelector('#cd-retry-analysis')?.addEventListener('click', () => analyzeImage(file));
      }
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

    const severity = isHealthy ? 'low' : 'medium';
    const sevColors = { low: 'var(--c-success)', medium: 'var(--c-accent)' };
    const sevBg = { low: 'rgba(34,197,94,0.08)', medium: 'rgba(245,158,11,0.08)' };
    const sevBorder = { low: 'rgba(34,197,94,0.25)', medium: 'rgba(245,158,11,0.25)' };

    let html = '';

    // ---- Diagnosis Header ----
    html += `
      <div class="cd-diagnosis-hero" style="background:${sevBg[severity]};border:1px solid ${sevBorder[severity]};margin-bottom:var(--sp-xl);">
        <div class="diagnosis-status-icon">${isHealthy ? '✅' : '⚠️'}</div>
        <div class="diagnosis-disease-name" style="color:${sevColors[severity]};">${isHealthy ? 'No supported disease pattern detected' : `Possible model match: ${diseaseName}`}</div>
        <div class="diagnosis-severity-wrap">Image screening only · confirm in the field</div>
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
                <div class="confidence-fill" style="width:${s.conf}%;background:${i === 0 ? (isHealthy ? 'var(--c-success)' : sevColors[severity]) : 'var(--c-text-dim)'};"></div>
              </div>
              <span class="confidence-pct ${i === 0 ? 'top' : ''}" style="${i === 0 ? `color:${sevColors[severity]};` : ''}">${s.conf}%</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    // ---- Clinical Agronomy Guidance Card ----
    html += `
      <div class="card cd-guidance-card" style="margin-bottom:var(--sp-lg);padding:var(--sp-lg);">
        <h3 class="section-title"><span class="icon">🌿</span> Agronomic Diagnosis & Management Guide</h3>

        <div class="cd-scope-badge-wrap" style="margin-bottom:var(--sp-md);">
          <span class="trust-pill" style="font-size:0.8rem;background:rgba(34,197,94,0.1);color:var(--c-primary);border:1px solid rgba(34,197,94,0.25);">
            🥔 Supported Scope: ${diag.crop || 'Potato (Solanum tuberosum)'}
          </span>
        </div>

        <div style="display:flex;flex-direction:column;gap:var(--sp-md);">
          ${diag.symptoms ? `
            <div class="guidance-block">
              <div style="font-weight:700;font-size:0.95rem;color:var(--c-text);margin-bottom:4px;">
                🔍 Observed Foliar Symptoms:
              </div>
              <p style="font-size:0.9rem;color:var(--c-text-secondary);line-height:1.6;margin:0;">
                ${diag.symptoms}
              </p>
            </div>
          ` : ''}

          ${diag.prevention ? `
            <div class="guidance-block">
              <div style="font-weight:700;font-size:0.95rem;color:var(--c-text);margin-bottom:4px;">
                🛡️ Field Hygiene & Preventive Practices:
              </div>
              <p style="font-size:0.9rem;color:var(--c-text-secondary);line-height:1.6;margin:0;">
                ${diag.prevention}
              </p>
            </div>
          ` : ''}

          ${(diag.next_steps || diag.plan) ? `
            <div class="guidance-block">
              <div style="font-weight:700;font-size:0.95rem;color:var(--c-text);margin-bottom:4px;">
                📋 Recommended Practical Next Steps:
              </div>
              <p style="font-size:0.9rem;color:var(--c-text-secondary);line-height:1.6;margin:0;">
                ${diag.next_steps || diag.plan}
              </p>
            </div>
          ` : ''}

          ${diag.med && diag.med !== 'None' ? `
            <div class="guidance-block" style="background:rgba(245,158,11,0.06);padding:var(--sp-md);border-radius:var(--r-md);border:1px solid rgba(245,158,11,0.2);">
              <div style="font-weight:700;font-size:0.95rem;color:var(--c-accent);margin-bottom:4px;">
                💊 Approved Chemical Management (Label Directed):
              </div>
              <p style="font-size:0.9rem;color:var(--c-text-secondary);line-height:1.6;margin:0 0 6px 0;">
                ${diag.med}
              </p>
              <div style="font-size:0.8rem;color:var(--c-text-muted);line-height:1.5;">
                ⚠️ <em>AGRIFY strictly adheres to ICAR safety guidelines: never apply unverified chemical dosages. Always consult a licensed local agronomist or Krishi Vigyan Kendra (KVK) officer and follow manufacturer product labels.</em>
              </div>
            </div>
          ` : ''}
        </div>
      </div>
    `;

    // Do not turn an image classification into treatment or yield-loss advice.
    html += `
      <div class="card" role="note" style="margin-bottom:var(--sp-xl);padding:var(--sp-lg);">
        <h3 class="section-title"><span class="icon">👨‍🌾</span> Confirm before taking action</h3>
        <p style="font-size:0.9rem;color:var(--c-text-secondary);line-height:1.7;">
          ${isHealthy
            ? 'This image did not match a supported disease pattern. That does not confirm the plant or field is disease-free; keep monitoring and seek local advice if symptoms continue.'
            : 'This image model screening is limited to potato leaves and can be wrong. Ask a local KVK or plant pathologist to confirm the field symptoms before choosing a treatment. Do not apply pesticides based on this result alone; follow local registration and product-label directions.'}
        </p>
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
