// ============================================================
// AGRIFY Voice & Speech Module — Phase 3D-4
// Browser-native Speech-to-Text (STT) + Text-to-Speech (TTS)
// Supported Indian Regional Locales: en-IN, te-IN, hi-IN
// ============================================================

const SPEECH_LANG_MAP = {
  en: 'en-IN',
  te: 'te-IN',
  hi: 'hi-IN',
};

// ---- STT Internal State ----
let recognition = null;
let isListeningState = false;
let currentAppLang = 'en';
const voiceListeners = new Map(); // event -> Set of callbacks

// ---- TTS Internal State (Phase 3D-4 Foundation) ----
let isSpeakingState = false;
let isPausedState = false;
let currentUtterance = null;
let cachedVoices = [];

// ---- Toast Notifications ----
export function showToast(message, type = 'info', duration = 4000) {
  if (typeof document === 'undefined') return;
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span> ${message}`;
  toast.onclick = () => toast.remove();

  container.appendChild(toast);
  setTimeout(() => {
    if (toast && toast.style) {
      toast.style.animation = 'fadeInUp 0.3s ease reverse';
    }
    setTimeout(() => {
      if (toast && typeof toast.remove === 'function') {
        toast.remove();
      }
    }, 300);
  }, duration);
}

// ============================================================
// SPEECH CAPABILITY & LANGUAGE RESOLUTION
// ============================================================
export function isSpeechSupported() {
  if (typeof window === 'undefined') return false;
  return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
}

export function isSpeechSynthesisSupported() {
  if (typeof window === 'undefined') return false;
  return !!(window.speechSynthesis && typeof window.SpeechSynthesisUtterance !== 'undefined');
}

export function getSpeechLangCode(appLang) {
  const lang = appLang || (typeof window !== 'undefined' ? window.localStorage?.getItem('lang') : 'en') || 'en';
  return SPEECH_LANG_MAP[lang] || 'en-IN';
}

export function getVoiceState() {
  return {
    isListening: isListeningState,
    isSpeaking: isSpeakingState,
    isPaused: isPausedState,
    appLanguage: currentAppLang,
    speechLangCode: getSpeechLangCode(currentAppLang),
    isSttSupported: isSpeechSupported(),
    isTtsSupported: isSpeechSynthesisSupported(),
    isSupported: isSpeechSupported(), // backward-compatible alias
  };
}

export function getTtsState() {
  return {
    isSpeaking: isSpeakingState,
    isPaused: isPausedState,
    isSupported: isSpeechSynthesisSupported(),
    appLanguage: currentAppLang,
    speechLangCode: getSpeechLangCode(currentAppLang),
    availableVoicesCount: getAvailableVoices().length,
  };
}

export function setVoiceLang(appLang) {
  const prevLang = currentAppLang;
  if (appLang && ['en', 'te', 'hi'].includes(appLang)) {
    currentAppLang = appLang;
  } else {
    currentAppLang = 'en';
  }

  const speechCode = getSpeechLangCode(currentAppLang);
  if (recognition) {
    recognition.lang = speechCode;
  }

  // Phase 3D-4 Rule: If language changes while speaking, immediately stop current speech
  if (isSpeakingState && prevLang !== currentAppLang) {
    stopSpeaking();
  }

  emitVoiceEvent('langChange', { appLang: currentAppLang, speechCode });
  updateFabTitle();
}

export function setTtsLang(appLang) {
  setVoiceLang(appLang);
}

// ============================================================
// EVENT SUBSCRIPTION
// ============================================================
export function onVoiceEvent(event, callback) {
  if (!voiceListeners.has(event)) {
    voiceListeners.set(event, new Set());
  }
  voiceListeners.get(event).add(callback);
  return () => voiceListeners.get(event)?.delete(callback);
}

function emitVoiceEvent(event, data) {
  const cbs = voiceListeners.get(event);
  if (cbs) {
    cbs.forEach(cb => {
      try { cb(data); } catch (e) { console.warn(`Voice event [${event}] error:`, e); }
    });
  }
}

// ============================================================
// TEXT-TO-SPEECH (TTS) CLEANING & VOICE SELECTION — Phase 3D-4
// ============================================================

/**
 * Strips markdown and formatting artifacts while preserving numbers, units,
 * Telugu/Hindi scripts, and natural conversational punctuation.
 */
export function cleanSpeechText(text) {
  if (!text || typeof text !== 'string') return '';

  let cleaned = text;

  // 1. Remove markdown links [text](url) -> text
  cleaned = cleaned.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');

  // 2. Remove markdown bold/italic asterisks & underscores
  cleaned = cleaned.replace(/[*_#`~]+/g, ' ');

  // 3. Remove markdown list markers at beginning of lines
  cleaned = cleaned.replace(/^[\s*>-]+/gm, '');

  // 4. Remove emojis or icons that interfere with TTS pronunciation
  cleaned = cleaned.replace(/[\u{1F300}-\u{1F6FF}\u{1F900}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '');

  // 5. Normalize whitespace while preserving natural punctuation
  cleaned = cleaned.replace(/\s+/g, ' ').trim();

  return cleaned;
}

/**
 * Returns available speechSynthesis voices, updating internal cache.
 */
export function getAvailableVoices() {
  if (!isSpeechSynthesisSupported()) return [];
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    const voices = window.speechSynthesis.getVoices();
    if (voices && voices.length > 0) {
      cachedVoices = voices;
    }
  }
  return cachedVoices;
}

/**
 * Selects the optimal browser voice matching language & region:
 * 1. Exact match (e.g. 'te-IN', 'hi-IN', 'en-IN')
 * 2. Same-language voice with regional preference
 * 3. Browser default voice fallback
 */
export function selectBestVoice(targetLangCode) {
  const voices = getAvailableVoices();
  if (!voices || voices.length === 0) return null;

  const code = (targetLangCode || 'en-IN').toLowerCase().replace('_', '-');
  const langPrefix = code.split('-')[0];

  // 1. Exact regional match (e.g. te-IN)
  const exactMatch = voices.find(v => {
    const vLang = (v.lang || '').toLowerCase().replace('_', '-');
    return vLang === code;
  });
  if (exactMatch) return exactMatch;

  // 2. Prefix match with Indian regional preference if possible
  const indianRegional = voices.find(v => {
    const vLang = (v.lang || '').toLowerCase().replace('_', '-');
    const vName = (v.name || '').toLowerCase();
    return vLang.startsWith(langPrefix) && (vLang.includes('in') || vName.includes('india') || vName.includes('hindi') || vName.includes('telugu'));
  });
  if (indianRegional) return indianRegional;

  // 3. Any voice sharing the language prefix
  const langMatch = voices.find(v => {
    const vLang = (v.lang || '').toLowerCase().replace('_', '-');
    return vLang.startsWith(langPrefix);
  });
  if (langMatch) return langMatch;

  // 4. Default voice
  const defaultVoice = voices.find(v => v.default);
  if (defaultVoice) return defaultVoice;

  // 5. First available voice
  return voices[0] || null;
}

// ============================================================
// CORE TEXT-TO-SPEECH (TTS) INTERFACE — Phase 3D-4
// ============================================================

/**
 * Speaks the given text using browser SpeechSynthesis.
 * Automatically stops active STT to prevent feedback loop.
 */
export function speak(text, options = {}) {
  if (!isSpeechSynthesisSupported()) {
    const notice = 'Voice playback is not supported in this browser.';
    showToast(notice, 'warning');
    if (options.onError) options.onError(notice, 'not-supported');
    emitVoiceEvent('ttsError', { message: notice, code: 'not-supported' });
    return false;
  }

  // Pre-condition: Stop microphone listening to avoid recording assistant's own speech
  if (isListeningState) {
    stopListening();
  }

  // Clean text strictly for TTS
  const speechText = cleanSpeechText(text);
  if (!speechText) {
    if (options.onEnd) options.onEnd();
    return false;
  }

  // Stop any active utterance before starting new one
  try {
    window.speechSynthesis.cancel();
  } catch (e) {
    /* ignore */
  }

  const targetLang = options.lang ? getSpeechLangCode(options.lang) : getSpeechLangCode(currentAppLang);
  const utterance = new window.SpeechSynthesisUtterance(speechText);
  utterance.lang = targetLang;

  // Rate & Pitch tuned for natural agricultural voice advisory
  utterance.rate = typeof options.rate === 'number' ? options.rate : 0.95;
  utterance.pitch = typeof options.pitch === 'number' ? options.pitch : 1.0;
  utterance.volume = typeof options.volume === 'number' ? options.volume : 1.0;

  const voice = selectBestVoice(targetLang);
  if (voice) {
    utterance.voice = voice;
  }

  utterance.onstart = () => {
    isSpeakingState = true;
    isPausedState = false;
    currentUtterance = utterance;
    emitVoiceEvent('speakStart', { text: speechText, lang: targetLang, voice: voice?.name });
    if (options.onStart) options.onStart();
  };

  utterance.onend = () => {
    isSpeakingState = false;
    isPausedState = false;
    currentUtterance = null;
    emitVoiceEvent('speakEnd', { text: speechText });
    if (options.onEnd) options.onEnd();
  };

  utterance.onerror = (event) => {
    // Ignore harmless 'canceled' / 'interrupted' events triggered when stopSpeaking is called intentionally
    if (event.error === 'canceled' || event.error === 'interrupted') {
      isSpeakingState = false;
      isPausedState = false;
      currentUtterance = null;
      return;
    }

    isSpeakingState = false;
    isPausedState = false;
    currentUtterance = null;
    const errorMsg = `Speech synthesis issue (${event.error || 'unknown'}).`;
    console.warn('TTS playback error:', event);
    emitVoiceEvent('ttsError', { message: errorMsg, error: event.error });
    if (options.onError) options.onError(errorMsg, event.error);
  };

  utterance.onpause = () => {
    isPausedState = true;
    emitVoiceEvent('speakPause', {});
    if (options.onPause) options.onPause();
  };

  utterance.onresume = () => {
    isPausedState = false;
    emitVoiceEvent('speakResume', {});
    if (options.onResume) options.onResume();
  };

  try {
    currentUtterance = utterance;
    window.speechSynthesis.speak(utterance);
    return true;
  } catch (err) {
    isSpeakingState = false;
    isPausedState = false;
    currentUtterance = null;
    console.warn('Speech synthesis start failed:', err);
    return false;
  }
}

export function stopSpeaking() {
  if (!isSpeechSynthesisSupported()) return;
  try {
    window.speechSynthesis.cancel();
  } catch (e) {
    /* ignore */
  }
  isSpeakingState = false;
  isPausedState = false;
  currentUtterance = null;
  emitVoiceEvent('speakStop', {});
}

export function pauseSpeaking() {
  if (!isSpeechSynthesisSupported() || !isSpeakingState) return;
  try {
    window.speechSynthesis.pause();
    isPausedState = true;
  } catch (e) {
    /* ignore */
  }
}

export function resumeSpeaking() {
  if (!isSpeechSynthesisSupported() || !isPausedState) return;
  try {
    window.speechSynthesis.resume();
    isPausedState = false;
  } catch (e) {
    /* ignore */
  }
}

export function isSpeaking() {
  return isSpeakingState && !isPausedState;
}

export function isSpeechPaused() {
  return isPausedState;
}

// ============================================================
// CORE SPEECH RECOGNITION (STT) INTERFACE — Phase 3D-2 Foundation
// ============================================================
export function startListening(options = {}) {
  if (!isSpeechSupported()) {
    const errorMsg = 'Voice recognition is not supported in this browser. Please use Chrome, Edge, or a Web Speech-enabled browser.';
    showToast(errorMsg, 'warning');
    if (options.onError) options.onError(errorMsg, 'not-supported');
    emitVoiceEvent('error', { message: errorMsg, code: 'not-supported' });
    return null;
  }

  // Pre-condition: Stop active TTS to prevent self-transcription
  if (isSpeakingState) {
    stopSpeaking();
  }

  if (isListeningState) {
    stopListening();
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const rec = new SpeechRecognition();

  const targetLang = options.lang ? getSpeechLangCode(options.lang) : getSpeechLangCode(currentAppLang);
  rec.lang = targetLang;
  rec.continuous = options.continuous || false;
  rec.interimResults = options.interimResults !== undefined ? options.interimResults : true;

  let finalTranscript = '';

  rec.onstart = () => {
    isListeningState = true;
    updateFabState('listening');
    if (options.onStart) options.onStart();
    emitVoiceEvent('start', { lang: targetLang });
  };

  rec.onresult = (event) => {
    let interimTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      const trans = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalTranscript += trans;
      } else {
        interimTranscript += trans;
      }
    }

    const currentText = finalTranscript || interimTranscript;

    if (options.onTranscript) {
      options.onTranscript(currentText, !!finalTranscript);
    }
    emitVoiceEvent('transcript', { text: currentText, isFinal: !!finalTranscript, interim: interimTranscript });

    // Auto-fill active inputs if present
    const activeInput = document.querySelector('.form-input:focus, #chat-input');
    if (activeInput && currentText) {
      activeInput.value = currentText;
      activeInput.dispatchEvent(new Event('input', { bubbles: true }));
    }
  };

  rec.onerror = (e) => {
    let friendlyMessage = 'Voice recognition encountered an issue. Please try again.';
    if (e.error === 'not-allowed' || e.error === 'permission-denied') {
      friendlyMessage = 'Microphone permission denied. Please allow microphone access in your browser settings.';
    } else if (e.error === 'no-speech') {
      friendlyMessage = 'No speech detected. Please speak clearly into your microphone.';
    } else if (e.error === 'network') {
      friendlyMessage = 'Network error during voice recognition. Please check your internet connection.';
    } else if (e.error === 'audio-capture') {
      friendlyMessage = 'No microphone was found. Please ensure a microphone is connected.';
    }

    updateFabState('error');
    if (e.error !== 'no-speech') {
      showToast(friendlyMessage, 'warning');
    }

    if (options.onError) options.onError(friendlyMessage, e.error);
    emitVoiceEvent('error', { message: friendlyMessage, code: e.error });
    stopListening();
  };

  rec.onend = () => {
    isListeningState = false;
    updateFabState('idle');
    if (finalTranscript) {
      showToast(`🎤 "${finalTranscript}"`, 'info', 2500);
    }
    if (options.onEnd) options.onEnd(finalTranscript);
    emitVoiceEvent('end', { finalTranscript });
  };

  try {
    rec.start();
    recognition = rec;
    return rec;
  } catch (err) {
    isListeningState = false;
    updateFabState('idle');
    console.warn('Voice start exception:', err);
    return null;
  }
}

export function stopListening() {
  isListeningState = false;
  if (recognition) {
    try { recognition.stop(); } catch (e) { /* ignore */ }
    recognition = null;
  }
  updateFabState('idle');
}

// ============================================================
// FAB VISUAL STATE MANAGEMENT
// ============================================================
function updateFabState(state) {
  if (typeof document === 'undefined') return;
  const fab = document.getElementById('voice-fab');
  if (!fab) return;

  if (state === 'listening') {
    fab.classList.add('listening');
    fab.innerHTML = '🔴';
  } else if (state === 'error') {
    fab.classList.remove('listening');
    fab.innerHTML = '⚠️';
    setTimeout(() => updateFabState('idle'), 2500);
  } else {
    fab.classList.remove('listening');
    fab.innerHTML = '🎤';
  }
}

function updateFabTitle() {
  if (typeof document === 'undefined') return;
  const fab = document.getElementById('voice-fab');
  if (!fab) return;
  const langLabels = { en: 'English (en-IN)', te: 'Telugu (te-IN)', hi: 'Hindi (hi-IN)' };
  const label = langLabels[currentAppLang] || 'English';
  fab.title = `Voice Input (${label})`;
  fab.setAttribute('aria-label', `Voice input (${label})`);
}

// ============================================================
// INITIALIZER & BROWSER EVENT HANDLERS
// ============================================================
export function initVoice() {
  if (typeof window === 'undefined') return;

  currentAppLang = window.localStorage?.getItem('lang') || 'en';
  if (!['en', 'te', 'hi'].includes(currentAppLang)) currentAppLang = 'en';

  // Cache voices asynchronously when browser signals voiceschanged
  if (window.speechSynthesis) {
    getAvailableVoices();
    window.speechSynthesis.onvoiceschanged = () => {
      getAvailableVoices();
    };
  }

  let fab = document.getElementById('voice-fab');
  if (!fab && typeof document !== 'undefined') {
    fab = document.createElement('button');
    fab.id = 'voice-fab';
    fab.className = 'voice-fab hidden';
    fab.innerHTML = '🎤';
    document.body.appendChild(fab);
  }

  updateFabTitle();
  if (fab) {
    fab.removeEventListener('click', handleFabClick);
    fab.addEventListener('click', handleFabClick);
  }

  // Sync with global language changes
  window.addEventListener('langChange', (e) => {
    setVoiceLang(e.detail);
  });
}

async function handleFabClick() {
  if (isListeningState) {
    stopListening();
  }
  if (isSpeakingState) {
    stopSpeaking();
  }

  try {
    const { openVoiceAssistantModal } = await import('./components/voiceAssistantModal.js');
    openVoiceAssistantModal();
  } catch (err) {
    console.warn('Could not open voice assistant modal:', err);
    // Graceful fallback
    if (!isSpeechSupported()) {
      showToast('Voice input is not supported in this browser.', 'warning');
      return;
    }
    startListening();
  }
}

// ============================================================
// INDIVIDUAL MIC BUTTONS SETUP
// ============================================================
export function setupMicButtons() {
  if (typeof document === 'undefined') return;
  document.querySelectorAll('.mic-btn').forEach(btn => {
    btn.onclick = () => {
      const input = btn.closest('.input-with-mic')?.querySelector('.form-input');
      if (!input) return;

      if (!isSpeechSupported()) {
        showToast('Voice input is not supported in this browser. Please use Chrome.', 'warning');
        return;
      }

      if (btn.classList.contains('listening')) {
        stopListening();
        btn.classList.remove('listening');
        return;
      }

      if (isSpeakingState) {
        stopSpeaking();
      }

      btn.classList.add('listening');
      btn.innerHTML = '🔴';

      startListening({
        lang: currentAppLang,
        interimResults: true,
        onTranscript: (text) => {
          input.value = text;
          input.dispatchEvent(new Event('input', { bubbles: true }));
        },
        onError: () => {
          btn.classList.remove('listening');
          btn.innerHTML = '🎤';
        },
        onEnd: () => {
          btn.classList.remove('listening');
          btn.innerHTML = '🎤';
        },
      });
    };
  });
}
