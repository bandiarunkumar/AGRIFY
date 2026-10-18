// ============================================================
// Agri-Connect — Production API Client
// GPS-first coordinate-based calls to production Flask backend
// ============================================================

const API_BASE = 'https://agri-connect-main-app.onrender.com';
const DISEASE_API_BASE = 'https://agri-connect-image.onrender.com';

export function getApiBase() {
  if (typeof window !== 'undefined' && window.__AGRIFY_API_BASE__) {
    return window.__AGRIFY_API_BASE__;
  }
  if (typeof import.meta !== 'undefined' && import.meta?.env?.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  const isLocal = typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
  // Use explicit 127.0.0.1 (not 'localhost') to bypass macOS AirPlay Receiver which binds to *:5000
  return isLocal ? 'http://127.0.0.1:5000' : API_BASE;
}

export function getDiseaseApiBase() {
  if (typeof window !== 'undefined' && window.__AGRIFY_DISEASE_API_BASE__) {
    return window.__AGRIFY_DISEASE_API_BASE__;
  }
  if (typeof import.meta !== 'undefined' && import.meta?.env?.VITE_IMAGE_API_BASE_URL) {
    return import.meta.env.VITE_IMAGE_API_BASE_URL;
  }
  const isLocal = typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
  return isLocal ? 'http://127.0.0.1:5001' : DISEASE_API_BASE;
}

// Retry-aware fetch with timeout
async function apiFetch(endpoint, options = {}, retries = 2) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);
  const base = getApiBase();

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(`${base}${endpoint}`, {
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        ...options,
      });
      clearTimeout(timeout);
      const data = await res.json();
      if (!res.ok && data.error) throw new Error(data.error);
      return data;
    } catch (err) {
      if (err.name === 'AbortError') {
        throw new Error('Request timed out. Check your internet connection.');
      }
      if (attempt === retries) {
        if (err.message === 'Failed to fetch') {
          throw new Error('Cannot connect to Agri-Connect server. The backend may be starting up — please try again in 30 seconds.');
        }
        throw err;
      }
      await new Promise(r => setTimeout(r, 1000 * (attempt + 1)));
    }
  }
}

// ---- GPS & Geocoding ----
export async function reverseGeocode(lat, lon) {
  return apiFetch(`/api/geocode/reverse?lat=${lat}&lon=${lon}`);
}

// ---- Weather (coordinate-first) ----
export async function getWeatherByCoords(lat, lon) {
  return apiFetch(`/api/weather/coords?lat=${lat}&lon=${lon}`);
}

export async function getForecastByCoords(lat, lon) {
  return apiFetch(`/api/forecast/coords?lat=${lat}&lon=${lon}`);
}

export async function getWeather(city) {
  return apiFetch(`/api/weather?city=${encodeURIComponent(city)}`);
}

export async function getForecast(city) {
  return apiFetch(`/api/forecast?city=${encodeURIComponent(city)}`);
}

// ---- Soil (real SoilGrids data) ----
export async function getSoilByCoords(lat, lon) {
  return apiFetch(`/api/soil/coords?lat=${lat}&lon=${lon}`);
}

// ---- Full Farm Analysis (primary endpoint) ----
export async function analyzeFarm(payload) {
  return apiFetch('/api/farm/analyze', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ---- Farm Action Plan (isolated extension) ----
export async function getFarmActionPlan(payload = {}) {
  const selectedLang = payload?.language || (typeof window !== 'undefined' ? window.localStorage?.getItem('lang') : 'en') || 'en';
  const lang = ['en', 'te', 'hi'].includes(selectedLang) ? selectedLang : 'en';

  const body = {
    ...payload,
    language: lang,
  };

  const isLocal = typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

  const primaryBase = getApiBase();

  try {
    const res = await fetch(`${primaryBase}/api/farm/action-plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok && data.error) throw new Error(data.error);
    return data;
  } catch (err) {
    if (isLocal) {
      // In local dev, if port 5000 is not reachable, attempt standard apiFetch
      return await apiFetch('/api/farm/action-plan', {
        method: 'POST',
        body: JSON.stringify(body),
      });
    }
    throw err;
  }
}

// ---- AGRIFY Voice Assistant Query (Phase 3D-3 / 3D-5) ----
export async function queryVoiceAssistant(payload) {
  const language = ['en', 'te', 'hi'].includes(payload?.language) ? payload.language : 'en';
  const body = {
    query: payload?.query || '',
    language,
    context: payload?.context || {},
  };

  const isLocal = typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

  try {
    const targetUrl = `${getApiBase()}/api/assistant/query`;

    const res = await fetch(targetUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const data = await res.json();
    if (!res.ok && data.error) throw new Error(data.error);
    return data;
  } catch (err) {
    if (isLocal) {
      return await apiFetch('/api/assistant/query', {
        method: 'POST',
        body: JSON.stringify(body),
      });
    }
    throw err;
  }
}

// ---- Legacy ML endpoints (Deprecated) ----
/**
 * @deprecated Legacy ML endpoint. Use analyzeFarm() for primary ICAR agronomic feasibility planning.
 */
export async function predictCrop(data) {
  return apiFetch('/api/predict/crop', { method: 'POST', body: JSON.stringify(data) });
}

/**
 * @deprecated Legacy ML endpoint. Inactive due to absent model artifacts and strict chemical safety rules.
 */
export async function predictFertilizer(data) {
  return apiFetch('/api/predict/fertilizer', { method: 'POST', body: JSON.stringify(data) });
}

export async function getSoilAnalysis(data) {
  return apiFetch('/api/soil-analysis', { method: 'POST', body: JSON.stringify(data) });
}

// ---- Market Prices ----
export async function getMarketPrices(data) {
  return apiFetch('/api/market-prices', { method: 'POST', body: JSON.stringify(data) });
}

// ---- News ----
export async function getNews() {
  return apiFetch('/api/news');
}

// ---- Alerts ----
export async function getAlerts(lat, lon, crop = 'rice', season = 'Kharif') {
  return apiFetch(`/api/alerts?lat=${lat}&lon=${lon}&crop=${crop}&season=${season}`);
}

// ---- Chatbot ----
export async function sendChatMessage(message, language = 'en', hasImage = false) {
  return apiFetch('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message, language, has_image: hasImage }),
  });
}

// ---- Disease Detection ----
export async function predictDisease(file, language = 'en') {
  if (!file) throw new Error('Choose a leaf image before analysis.');

  const formData = new FormData();
  formData.append('file', file);
  formData.append('language', language);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);

  const base = getDiseaseApiBase();
  try {
    let response;
    try {
      response = await fetch(`${base}/api/predict`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });
    } catch (error) {
      if (error.name === 'AbortError') throw new Error('Crop Doctor timed out. Please try again later.');
      throw new Error(`Crop Doctor is currently unavailable at ${base}. Please try again later.`);
    }

    let data;
    try {
      data = await response.json();
    } catch {
      throw new Error('Crop Doctor returned an unreadable response. Please try again later.');
    }
    if (!response.ok) throw new Error(data.error || 'Crop Doctor could not analyze this image.');
    if (data.status !== 'success' || (data.is_recognized !== false &&
        (data.is_recognized !== true || !data.diagnosis || !Array.isArray(data.all_scores)))) {
      throw new Error(data.error || 'Crop Doctor returned an incomplete diagnosis. Please try again later.');
    }
    return data;
  } finally {
    clearTimeout(timeout);
  }
}

// ---- GPS Helper ----
export function getCurrentPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation not supported by your browser'));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      pos => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude, accuracy: pos.coords.accuracy }),
      err => {
        const msgs = {
          1: 'Location permission denied. Please allow location access.',
          2: 'Location unavailable. Check GPS signal.',
          3: 'Location request timed out.',
        };
        reject(new Error(msgs[err.code] || 'Unknown location error'));
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 30000 }
    );
  });
}

// ---- Translation Helper ----
// Translation requests are routed through the API so credentials never reach the browser.
const translationCache = new Map();

export async function translateDynamicText(text, targetLang) {
  if (!text) return text;
  if (targetLang === 'en' || !targetLang) return text;
  
  const cacheKey = `${text}_${targetLang}`;
  if (translationCache.has(cacheKey)) {
    return translationCache.get(cacheKey);
  }

  try {
    const data = await apiFetch('/api/translate', {
      method: 'POST',
      body: JSON.stringify({ q: text, target: targetLang })
    });

    const translated = data.translatedText;
    if (!translated) return text;
    
    // Cache it to avoid repeated identical API calls
    translationCache.set(cacheKey, translated);
    return translated;
  } catch (err) {
    console.warn("Translation failed:", err);
    return text;
  }
}
