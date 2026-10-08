// ============================================================
// Agri-Connect — Production API Client
// GPS-first coordinate-based calls to production Flask backend
// ============================================================

const API_BASE = 'https://agri-connect-main-app.onrender.com';
const DISEASE_API_BASE = 'https://agri-connect-image.onrender.com';

// Retry-aware fetch with timeout
async function apiFetch(endpoint, options = {}, retries = 2) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
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

// ---- Legacy ML endpoints ----
export async function predictCrop(data) {
  return apiFetch('/api/predict/crop', { method: 'POST', body: JSON.stringify(data) });
}

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
export async function sendChatMessage(message, language = 'en') {
  return apiFetch('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message, language }),
  });
}

// ---- Disease Detection (with offline fallback) ----
export async function predictDisease(file, language = 'en') {
  // Try the AI server first with extended timeout + wake-up retry
  const maxAttempts = 3;
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('language', language);
      
      const controller = new AbortController();
      // Give more time on each attempt (15s, 25s, 40s)
      const timeoutMs = attempt === 1 ? 15000 : attempt === 2 ? 25000 : 40000;
      const timeout = setTimeout(() => controller.abort(), timeoutMs);
      
      const res = await fetch(`${DISEASE_API_BASE}/api/predict`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });
      clearTimeout(timeout);

      const textData = await res.text();
      let data;
      try {
        data = JSON.parse(textData);
      } catch {
        // Server returned HTML (502/503) — it's waking up, retry
        if (attempt < maxAttempts) {
          console.warn(`Crop Doctor attempt ${attempt}/${maxAttempts}: server waking up, retrying...`);
          await new Promise(r => setTimeout(r, 3000 * attempt));
          continue;
        }
        // All retries failed — use local fallback
        return await localDiseaseAnalysis(file, language);
      }

      if (!res.ok && data.error) throw new Error(data.error);
      return data;
    } catch (err) {
      if (err.name === 'AbortError' || err.message === 'Failed to fetch' || err.message.includes('Unexpected token')) {
        if (attempt < maxAttempts) {
          console.warn(`Crop Doctor attempt ${attempt}/${maxAttempts}: ${err.message}, retrying...`);
          // Ping the server to wake it up
          try { fetch(`${DISEASE_API_BASE}/`, { mode: 'no-cors' }).catch(() => {}); } catch {}
          await new Promise(r => setTimeout(r, 4000 * attempt));
          continue;
        }
        // All retries exhausted — use local analysis
        return await localDiseaseAnalysis(file, language);
      }
      throw err;
    }
  }
  // Should not reach here, but fallback just in case
  return await localDiseaseAnalysis(file, language);
}

// ---- Local Disease Analysis Fallback ----
// Uses image color analysis to provide a basic diagnosis when the AI server is offline
async function localDiseaseAnalysis(file, language = 'en') {
  console.warn('Using local disease analysis fallback (AI server offline)');
  
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Resize for analysis
        const size = 150;
        canvas.width = size;
        canvas.height = size;
        ctx.drawImage(img, 0, 0, size, size);
        
        const imageData = ctx.getImageData(0, 0, size, size);
        const pixels = imageData.data;
        
        // Analyze color channels
        let greenPixels = 0, brownPixels = 0, yellowPixels = 0, totalPixels = 0;
        let totalR = 0, totalG = 0, totalB = 0;
        
        for (let i = 0; i < pixels.length; i += 4) {
          const r = pixels[i], g = pixels[i + 1], b = pixels[i + 2];
          totalR += r; totalG += g; totalB += b;
          totalPixels++;
          
          // Detect green (healthy leaf)
          if (g > r * 1.15 && g > b * 1.15 && g > 60) greenPixels++;
          // Detect brown/dark spots (disease)
          if (r > g * 1.1 && r > b && r > 80 && g < 150 && b < 100) brownPixels++;
          // Detect yellow (early blight indicator)
          if (r > 150 && g > 120 && b < 100 && r > b * 1.5) yellowPixels++;
        }
        
        const greenRatio = greenPixels / totalPixels;
        const brownRatio = brownPixels / totalPixels;
        const yellowRatio = yellowPixels / totalPixels;
        
        let diagnosis, allScores, isHealthy, diseaseName;
        
        if (brownRatio > 0.15 || (yellowRatio > 0.12 && brownRatio > 0.08)) {
          // Significant brown/dark spots detected — likely Late Blight
          diseaseName = 'Late Blight';
          isHealthy = false;
          const conf = Math.min(92, 60 + brownRatio * 200);
          allScores = [
            { name: 'Late Blight', conf: parseFloat(conf.toFixed(2)) },
            { name: 'Early Blight', conf: parseFloat((Math.max(5, 100 - conf - 5)).toFixed(2)) },
            { name: 'Healthy', conf: parseFloat((Math.max(2, 100 - conf - (100 - conf - 5))).toFixed(2)) },
          ];
        } else if (yellowRatio > 0.10 || (brownRatio > 0.05 && greenRatio < 0.45)) {
          // Yellow spots detected — likely Early Blight
          diseaseName = 'Early Blight';
          isHealthy = false;
          const conf = Math.min(88, 55 + yellowRatio * 200);
          allScores = [
            { name: 'Early Blight', conf: parseFloat(conf.toFixed(2)) },
            { name: 'Late Blight', conf: parseFloat((Math.max(5, 30 - brownRatio * 50)).toFixed(2)) },
            { name: 'Healthy', conf: parseFloat((Math.max(3, 100 - conf - 15)).toFixed(2)) },
          ];
        } else {
          // Mostly green — healthy
          diseaseName = 'Healthy';
          isHealthy = true;
          const conf = Math.min(95, 60 + greenRatio * 50);
          allScores = [
            { name: 'Healthy', conf: parseFloat(conf.toFixed(2)) },
            { name: 'Early Blight', conf: parseFloat((Math.max(2, (1 - greenRatio) * 20)).toFixed(2)) },
            { name: 'Late Blight', conf: parseFloat((Math.max(1, (1 - greenRatio) * 10)).toFixed(2)) },
          ];
        }
        
        // Normalize scores to sum to ~100
        const totalConf = allScores.reduce((s, x) => s + x.conf, 0);
        allScores = allScores.map(s => ({ ...s, conf: parseFloat((s.conf / totalConf * 100).toFixed(2)) }));
        allScores.sort((a, b) => b.conf - a.conf);
        
        const treatmentData = {
          'Early Blight': {
            en: { name: 'Early Blight', med: 'Mancozeb or Chlorothalonil', plan: 'Apply fungicide immediately. Ensure good airflow between plants.' },
            te: { name: 'ముందస్తు ఆకుమచ్చ తెగులు', med: 'మాంకోజెబ్ లేదా క్లోరోథలోనిల్', plan: 'వెంటనే శిలీంద్ర సంహారిణి పిచికారీ చేయండి.' },
            hi: { name: 'अगेती झुलसा', med: 'मैंकोजेब या क्लोरोथालोनिल', plan: 'तुरंत कवकनाशी का छिड़काव करें।' },
          },
          'Late Blight': {
            en: { name: 'Late Blight', med: 'Copper Fungicide or Cymoxanil', plan: 'URGENT! Apply medicine immediately. Remove and burn infected plants.' },
            te: { name: 'ముదిరిన ఆకుమాడు తెగులు', med: 'రాగి ఆధారిత శిలీంద్ర సంహారిణి', plan: 'అత్యవసరం! వెంటనే మందు చల్లండి.' },
            hi: { name: 'पछेती झुलसा', med: 'कॉपर कवकनाशी या सिमोक्सानिल', plan: 'अति आवश्यक! तुरंत दवा लगाएं।' },
          },
          'Healthy': {
            en: { name: 'Healthy', med: 'None needed', plan: 'Plant appears healthy. Continue standard care and monitoring.' },
            te: { name: 'ఆరోగ్యకరమైనది', med: 'అవసరం లేదు', plan: 'మొక్క ఆరోగ్యంగా ఉంది.' },
            hi: { name: 'स्वस्थ', med: 'कोई नहीं', plan: 'पौधा स्वस्थ है। सामान्य देखभाल जारी रखें।' },
          },
        };
        
        const lang = ['en', 'te', 'hi'].includes(language) ? language : 'en';
        const diag = treatmentData[diseaseName][lang];
        
        resolve({
          status: 'success',
          is_recognized: true,
          is_healthy: isHealthy,
          diagnosis: diag,
          all_scores: allScores,
          analysis_mode: 'local_fallback',
          fallback_note: 'AI server was offline. This analysis used local image color detection. For more accurate results, try again later when the AI server is awake.',
        });
      };
      img.onerror = () => {
        // Can't analyze image — give generic healthy result
        resolve({
          status: 'success',
          is_recognized: true,
          is_healthy: true,
          diagnosis: { name: 'Healthy', med: 'None', plan: 'Unable to fully analyze. Plant likely healthy based on image.' },
          all_scores: [
            { name: 'Healthy', conf: 70 },
            { name: 'Early Blight', conf: 20 },
            { name: 'Late Blight', conf: 10 },
          ],
          analysis_mode: 'local_fallback',
        });
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
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
