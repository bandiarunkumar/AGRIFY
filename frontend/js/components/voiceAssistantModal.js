// ============================================================
// AGRIFY Voice Copilot Modal Component — Phase 3D-5
// Reusable, responsive, accessible global voice interface
// Orchestrates: voice.js (STT + TTS) + api.js (AI query)
// ============================================================

import {
  startListening,
  stopListening,
  speak,
  stopSpeaking,
  pauseSpeaking,
  resumeSpeaking,
  isSpeaking,
  isSpeechPaused,
  isSpeechSupported,
  isSpeechSynthesisSupported,
  onVoiceEvent,
  getVoiceState,
  showToast,
} from '../voice.js';
import { queryVoiceAssistant } from '../api.js';
import { getLang } from '../i18n.js';

let modalContainer = null;
let isOpenState = false;
let currentState = 'IDLE'; // IDLE | LISTENING | TRANSCRIBING | PROCESSING | SPEAKING | PAUSED | ERROR | UNSUPPORTED
let currentTranscript = '';
let conversationHistory = []; // session-only turns: [{ role: 'user'|'assistant', text, card, escalation, disclaimer }]
let unsubscribeVoiceEvents = null;

// ---- Localized UI Strings ----
const MODAL_STRINGS = {
  en: {
    title: 'AGRIFY Voice Copilot',
    subtitle: 'Ask about crops, fertilizers, irrigation, weather & mandi rates',
    tapToSpeak: 'Tap microphone to speak',
    listening: 'Listening... Speak your question',
    transcribing: 'Transcribing speech...',
    processing: 'AGRIFY is analyzing verified data...',
    speaking: 'Speaking response...',
    paused: 'Playback paused',
    unsupportedVoice: 'Voice input/playback is limited in this browser. You can type below.',
    micError: 'Could not capture voice. Please try again or type below.',
    typePlaceholder: 'Ask a farming question or tap mic...',
    askBtn: 'Ask',
    clearSession: 'Clear',
    close: 'Close',
    expertTitle: '👨‍🌾 Agriculture Expert Consultation Recommended',
    expertBtn: 'Browse Expert Directory',
    quickQuestions: [
      '🌾 What crops should I grow this season?',
      '💧 Should I irrigate my field today?',
      '🧪 What is my recommended fertilizer dosage?',
      '🌤️ Live weather and rain forecast',
      '📊 Mandi market prices for my crop',
    ],
  },
  te: {
    title: 'AGRIFY వాయిస్ సహాయకుడు',
    subtitle: 'పంటలు, ఎరువులు, నీటిపారుదల, వాతావరణం మరియు మార్కెట్ ధరలపై అడగండి',
    tapToSpeak: 'మాట్లాడటానికి మైక్ నొక్కండి',
    listening: 'వింటున్నాను... మీ ప్రశ్న అడగండి',
    transcribing: 'వాయిస్ గుర్తిస్తున్నాము...',
    processing: 'సమాచారాన్ని విశ్లేషిస్తున్నాము...',
    speaking: 'సమాధానం చదువుతున్నాము...',
    paused: 'ఆపివేయబడింది',
    unsupportedVoice: 'ఈ బ్రౌజర్‌లో వాయిస్ సదుపాయం పరిమితంగా ఉంది. కింద టైప్ చేయవచ్చు.',
    micError: 'వాయిస్ నమోదు కాలేదు. దయచేసి మళ్లీ ప్రయత్నించండి.',
    typePlaceholder: 'వ్యవసాయ ప్రశ్న అడగండి లేదా మైక్ నొక్కండి...',
    askBtn: 'అడగండి',
    clearSession: 'క్లియర్',
    close: 'మూసివేయి',
    expertTitle: '👨‍🌾 వ్యవసాయ నిపుణుల సలహా సిఫారసు చేయబడింది',
    expertBtn: 'నిపుణుల డైరెక్టరీ చూడండి',
    quickQuestions: [
      '🌾 ఈ సీజన్‌కు అనువైన పంటలు ఏవి?',
      '💧 ఈరోజు నా పొలానికి నీరు పెట్టాలా?',
      '🧪 సిఫారసు చేయబడిన ఎరువుల మోతాదు ఎంత?',
      '🌤️ తాజా వాతావరణం మరియు వర్ష సూచన',
      '📊 నా పంట మార్కెట్ ధరలు ఎంత?',
    ],
  },
  hi: {
    title: 'AGRIFY वॉइस सहायक',
    subtitle: 'फसल, खाद, सिंचाई, मौसम और मंडी भाव के बारे में पूछें',
    tapToSpeak: 'बोलने के लिए माइक दबाएं',
    listening: 'सुन रहे हैं... अपना प्रश्न पूछें',
    transcribing: 'आवाज पहचानी जा रही है...',
    processing: 'AGRIFY डेटा का विश्लेषण कर रहा है...',
    speaking: 'उत्तर सुनाया जा रहा है...',
    paused: 'रोका गया',
    unsupportedVoice: 'इस ब्राउज़र में वॉइस सुविधा सीमित है। आप नीचे टाइप कर सकते हैं।',
    micError: 'आवाज दर्ज नहीं हो सकी। कृपया पुनः प्रयास करें।',
    typePlaceholder: 'खेती का सवाल पूछें या माइक दबाएं...',
    askBtn: 'पूछें',
    clearSession: 'हटाएं',
    close: 'बंद करें',
    expertTitle: '👨‍🌾 कृषि विशेषज्ञ परामर्श अनुशंसित',
    expertBtn: 'विशेषज्ञ निर्देशिका देखें',
    quickQuestions: [
      '🌾 इस मौसम के लिए कौन सी फसलें उपयुक्त हैं?',
      '💧 क्या मुझे आज अपने खेत में सिंचाई करनी चाहिए?',
      '🧪 अनुशंसित उर्वरक खुराक क्या है?',
      '🌤️ ताजा मौसम और बारिश का पूर्वानुमान',
      '📊 मेरी फसल का मंडी भाव क्या है?',
    ],
  },
};

function getStrings() {
  const lang = getLang() || 'en';
  return MODAL_STRINGS[lang] || MODAL_STRINGS.en;
}

// ============================================================
// SAFE PAGE CONTEXT BUILDER
// ============================================================
export function buildSafePageContext() {
  const context = {};
  if (typeof window === 'undefined') return context;

  // 1. Check if cached analysis data exists
  if (window._agrifyAnalysisData && typeof window._agrifyAnalysisData === 'object') {
    const a = window._agrifyAnalysisData;
    if (a.request) context.request = a.request;
    if (a.location) context.location = a.location;
    if (a.soil) context.soil = a.soil;
    if (a.weather) context.weather = a.weather;
    if (a.crop_recommendation) context.crop_recommendation = a.crop_recommendation;
    if (a.fertilizer_recommendation) context.fertilizer_recommendation = a.fertilizer_recommendation;
    if (a.irrigation_guidance) context.irrigation_guidance = a.irrigation_guidance;
    if (a.alerts) context.alerts = a.alerts;
    if (a.action_plan) context.action_plan = a.action_plan;
  }

  // 2. Fallback: check session-level AGRIFY location context
  let sessionLocation = null;
  if (window._agrifyLocation && typeof window._agrifyLocation === 'object') {
    sessionLocation = window._agrifyLocation;
  } else {
    try {
      const stored = sessionStorage.getItem('agrify_session_location');
      if (stored) sessionLocation = JSON.parse(stored);
    } catch (_) {}
  }

  if (sessionLocation && typeof sessionLocation === 'object') {
    const sLat = sessionLocation.latitude ?? sessionLocation.lat;
    const sLon = sessionLocation.longitude ?? sessionLocation.lon;
    if (Number.isFinite(sLat) && Number.isFinite(sLon)) {
      if (!context.location) {
        context.location = { ...sessionLocation, latitude: sLat, longitude: sLon };
      }
      if (!context.request) {
        context.request = { latitude: sLat, longitude: sLon };
      } else {
        if (context.request.latitude == null) context.request.latitude = sLat;
        if (context.request.longitude == null) context.request.longitude = sLon;
      }
    }
  }

  // 3. Check form inputs if on analysis page
  const activeCropInput = document.getElementById('step-crop') || document.querySelector('select[name="crop"]');
  if (activeCropInput && activeCropInput.value) {
    if (!context.request) context.request = {};
    context.request.active_crop = activeCropInput.value;
  }

  // 3. Check weather page cached data
  if (window._agrifyWeatherData && typeof window._agrifyWeatherData === 'object') {
    context.weather = window._agrifyWeatherData;
  }

  // 4. Check market page cached data
  if (window._agrifyMarketData && typeof window._agrifyMarketData === 'object') {
    context.market = window._agrifyMarketData;
  }

  return context;
}

// ============================================================
// MODAL DOM INITIALIZATION
// ============================================================
export function initVoiceAssistantModal() {
  if (typeof document === 'undefined') return;

  if (document.getElementById('voice-copilot-overlay')) {
    modalContainer = document.getElementById('voice-copilot-overlay');
    return;
  }

  modalContainer = document.createElement('div');
  modalContainer.id = 'voice-copilot-overlay';
  modalContainer.className = 'voice-modal-overlay hidden';
  modalContainer.setAttribute('role', 'dialog');
  modalContainer.setAttribute('aria-modal', 'true');
  modalContainer.setAttribute('aria-label', 'AGRIFY Voice Copilot');

  modalContainer.innerHTML = `
    <div class="voice-modal-card" id="voice-modal-card">
      <!-- Header -->
      <div class="voice-modal-header">
        <div class="voice-modal-title-group">
          <div class="voice-modal-avatar">🌾</div>
          <div>
            <h3 class="voice-modal-title" id="vm-title">AGRIFY Voice Copilot</h3>
            <p class="voice-modal-sub" id="vm-sub">Farming Advisory AI</p>
          </div>
        </div>
        <div class="voice-modal-actions">
          <span class="voice-lang-chip" id="vm-lang-chip">EN</span>
          <button class="voice-modal-close-btn" id="vm-close-btn" aria-label="Close Voice Copilot">✕</button>
        </div>
      </div>

      <!-- Messages / Conversation Scroll -->
      <div class="voice-modal-body" id="vm-body">
        <!-- Quick Prompts / Welcome -->
        <div class="voice-welcome-view" id="vm-welcome">
          <div class="voice-welcome-badge">🎙️ Speak or Type in English, Telugu, or Hindi</div>
          <div class="voice-quick-chips" id="vm-quick-chips"></div>
        </div>

        <!-- Dynamic Turns Container -->
        <div class="voice-turns-container" id="vm-turns"></div>
      </div>

      <!-- Status Indicator & Live Transcript -->
      <div class="voice-status-bar" id="vm-status-bar">
        <div class="voice-status-icon" id="vm-status-icon">🎙️</div>
        <div class="voice-status-text-wrap">
          <div class="voice-status-text" id="vm-status-text">Tap microphone to speak</div>
          <div class="voice-live-transcript hidden" id="vm-live-transcript"></div>
        </div>
        <!-- TTS Playback Controls -->
        <div class="voice-tts-controls hidden" id="vm-tts-controls">
          <button class="voice-control-btn" id="vm-pause-resume-btn" title="Pause/Resume" aria-label="Pause or Resume Audio">⏸</button>
          <button class="voice-control-btn" id="vm-stop-btn" title="Stop Audio" aria-label="Stop Audio">⏹</button>
        </div>
      </div>

      <!-- Footer Action Area -->
      <div class="voice-modal-footer">
        <button class="voice-mic-main-btn" id="vm-mic-btn" aria-label="Toggle Microphone Recording">
          <span class="mic-icon">🎤</span>
          <span class="mic-wave"></span>
        </button>

        <form class="voice-text-form" id="vm-text-form">
          <input
            type="text"
            class="voice-text-input"
            id="vm-text-input"
            placeholder="Ask a farming question..."
            autocomplete="off"
            aria-label="Type your agriculture question"
          />
          <button type="submit" class="voice-send-btn" id="vm-send-btn" aria-label="Send Question">➔</button>
        </form>

        <button class="voice-clear-btn" id="vm-clear-btn" title="Clear Session" aria-label="Clear Conversation">🗑️</button>
      </div>
    </div>
  `;

  document.body.appendChild(modalContainer);

  // Attach Event Handlers
  attachModalEvents();

  // Subscribe to voice.js events
  subscribeToVoiceEvents();
}

// ============================================================
// EVENT HANDLERS
// ============================================================
function attachModalEvents() {
  const closeBtn = document.getElementById('vm-close-btn');
  const overlay = document.getElementById('voice-copilot-overlay');
  const micBtn = document.getElementById('vm-mic-btn');
  const textForm = document.getElementById('vm-text-form');
  const clearBtn = document.getElementById('vm-clear-btn');
  const pauseResumeBtn = document.getElementById('vm-pause-resume-btn');
  const stopBtn = document.getElementById('vm-stop-btn');

  // Close handlers
  if (closeBtn) closeBtn.onclick = closeVoiceAssistantModal;
  if (overlay) {
    overlay.onclick = (e) => {
      if (e.target === overlay) closeVoiceAssistantModal();
    };
  }

  // Keyboard accessibility: Escape key closes modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isOpenState) {
      closeVoiceAssistantModal();
    }
  });

  // Main Mic Button
  if (micBtn) {
    micBtn.onclick = handleMainMicClick;
  }

  // Fallback Text Form
  if (textForm) {
    textForm.onsubmit = (e) => {
      e.preventDefault();
      const input = document.getElementById('vm-text-input');
      if (input && input.value.trim()) {
        const query = input.value.trim();
        input.value = '';
        handleUserQuery(query);
      }
    };
  }

  // Clear Session
  if (clearBtn) {
    clearBtn.onclick = () => {
      conversationHistory = [];
      stopSpeaking();
      stopListening();
      renderTurns();
      setState('IDLE');
    };
  }

  // TTS Controls
  if (pauseResumeBtn) {
    pauseResumeBtn.onclick = () => {
      if (isSpeechPaused()) {
        resumeSpeaking();
        setState('SPEAKING');
      } else if (isSpeaking()) {
        pauseSpeaking();
        setState('PAUSED');
      }
    };
  }

  if (stopBtn) {
    stopBtn.onclick = () => {
      stopSpeaking();
      setState('IDLE');
    };
  }

  // Language Change sync
  window.addEventListener('langChange', () => {
    updateModalLanguage();
  });
}

function subscribeToVoiceEvents() {
  if (unsubscribeVoiceEvents) unsubscribeVoiceEvents();

  const unsub1 = onVoiceEvent('start', () => {
    setState('LISTENING');
  });

  const unsub2 = onVoiceEvent('transcript', ({ text, isFinal }) => {
    currentTranscript = text;
    const transEl = document.getElementById('vm-live-transcript');
    if (transEl) {
      transEl.textContent = `"${text}"`;
      transEl.classList.remove('hidden');
    }
    if (isFinal && text.trim()) {
      setState('PROCESSING');
      handleUserQuery(text.trim());
    }
  });

  const unsub3 = onVoiceEvent('end', ({ finalTranscript }) => {
    if (currentState === 'LISTENING' && !finalTranscript) {
      setState('IDLE');
    }
  });

  const unsub4 = onVoiceEvent('error', () => {
    setState('ERROR');
  });

  const unsub5 = onVoiceEvent('speakStart', () => {
    setState('SPEAKING');
  });

  const unsub6 = onVoiceEvent('speakEnd', () => {
    setState('IDLE');
  });

  unsubscribeVoiceEvents = () => {
    unsub1(); unsub2(); unsub3(); unsub4(); unsub5(); unsub6();
  };
}

// ============================================================
// MODAL OPEN / CLOSE LIFECYCLE
// ============================================================
export function openVoiceAssistantModal() {
  if (!modalContainer) initVoiceAssistantModal();
  if (!modalContainer) return;

  isOpenState = true;
  modalContainer.classList.remove('hidden');
  document.body.style.overflow = 'hidden';

  updateModalLanguage();
  renderQuickChips();
  renderTurns();
  setState('IDLE');

  const input = document.getElementById('vm-text-input');
  if (input) setTimeout(() => input.focus(), 150);
}

export function closeVoiceAssistantModal() {
  if (!modalContainer) return;

  isOpenState = false;
  modalContainer.classList.add('hidden');
  document.body.style.overflow = '';

  // Stop any active STT or TTS
  stopListening();
  stopSpeaking();
  setState('IDLE');
}

export function isVoiceAssistantModalOpen() {
  return isOpenState;
}

// ============================================================
// QUERY PROCESSING & UI STATE MANAGEMENT
// ============================================================
async function handleUserQuery(query) {
  if (!query || typeof query !== 'string' || !query.trim()) return;

  stopListening();
  setState('PROCESSING');

  // Add User turn immediately
  conversationHistory.push({
    role: 'user',
    text: query,
  });
  renderTurns();

  const currentLang = getLang() || 'en';
  const contextSnapshot = buildSafePageContext();

  try {
    const res = await queryVoiceAssistant({
      query,
      language: currentLang,
      context: contextSnapshot,
    });

    if (!res || res.status !== 'success') {
      throw new Error(res?.error || 'Failed to process voice query');
    }

    // Add Assistant Turn
    conversationHistory.push({
      role: 'assistant',
      text: res.spoken_response,
      card: res.display_card,
      escalation: res.expert_escalation,
      disclaimer: res.disclaimer,
      source: res.source,
    });
    renderTurns();

    // Trigger TTS
    if (res.spoken_response && isSpeechSynthesisSupported()) {
      speak(res.spoken_response, {
        lang: currentLang,
        onStart: () => setState('SPEAKING'),
        onEnd: () => setState('IDLE'),
        onError: () => setState('IDLE'),
      });
    } else {
      setState('IDLE');
    }
  } catch (err) {
    console.warn('Voice assistant query error:', err);
    conversationHistory.push({
      role: 'assistant',
      text: 'I could not connect to the AGRIFY advisory service at this moment. Please verify your connection or consult your local agricultural office.',
      card: {
        title: 'Connection Notice',
        category: 'System Notice',
        key_points: ['Backend query timeout or network issue', 'Deterministic offline guidance available on Farm Analyzer'],
        action_pill: { label: 'Open Analyzer', action: 'navigate_analysis' },
      },
      escalation: { recommended: false },
      disclaimer: 'Advisory guidance based on verified AGRIFY models.',
    });
    renderTurns();
    setState('ERROR');
  }
}

function handleMainMicClick() {
  const voiceState = getVoiceState();

  if (voiceState.isListening) {
    stopListening();
    setState('IDLE');
    return;
  }

  if (isSpeaking()) {
    stopSpeaking();
  }

  if (!isSpeechSupported()) {
    setState('UNSUPPORTED');
    showToast(getStrings().unsupportedVoice, 'warning');
    return;
  }

  const lang = getLang() || 'en';
  startListening({ lang });
  setState('LISTENING');
}

function setState(state) {
  currentState = state;
  const S = getStrings();

  const statusBar = document.getElementById('vm-status-bar');
  const statusIcon = document.getElementById('vm-status-icon');
  const statusText = document.getElementById('vm-status-text');
  const liveTrans = document.getElementById('vm-live-transcript');
  const ttsControls = document.getElementById('vm-tts-controls');
  const pauseResumeBtn = document.getElementById('vm-pause-resume-btn');
  const micBtn = document.getElementById('vm-mic-btn');

  if (!statusText || !micBtn) return;

  // Reset classes
  micBtn.classList.remove('listening', 'speaking', 'error');
  if (ttsControls) ttsControls.classList.add('hidden');
  if (liveTrans && state !== 'LISTENING' && state !== 'TRANSCRIBING') {
    liveTrans.classList.add('hidden');
  }

  switch (state) {
    case 'LISTENING':
      statusIcon.textContent = '🔴';
      statusText.textContent = S.listening;
      micBtn.classList.add('listening');
      break;

    case 'TRANSCRIBING':
      statusIcon.textContent = '📝';
      statusText.textContent = S.transcribing;
      break;

    case 'PROCESSING':
      statusIcon.textContent = '🤖';
      statusText.textContent = S.processing;
      break;

    case 'SPEAKING':
      statusIcon.textContent = '🔊';
      statusText.textContent = S.speaking;
      micBtn.classList.add('speaking');
      if (ttsControls) {
        ttsControls.classList.remove('hidden');
        if (pauseResumeBtn) pauseResumeBtn.textContent = '⏸';
      }
      break;

    case 'PAUSED':
      statusIcon.textContent = '⏸';
      statusText.textContent = S.paused;
      if (ttsControls) {
        ttsControls.classList.remove('hidden');
        if (pauseResumeBtn) pauseResumeBtn.textContent = '▶';
      }
      break;

    case 'ERROR':
      statusIcon.textContent = '⚠️';
      statusText.textContent = S.micError;
      micBtn.classList.add('error');
      break;

    case 'UNSUPPORTED':
      statusIcon.textContent = '⚠️';
      statusText.textContent = S.unsupportedVoice;
      break;

    case 'IDLE':
    default:
      statusIcon.textContent = '🎙️';
      statusText.textContent = S.tapToSpeak;
      break;
  }
}

// ============================================================
// RENDERING HELPERS
// ============================================================
function updateModalLanguage() {
  const S = getStrings();
  const lang = getLang() || 'en';

  const titleEl = document.getElementById('vm-title');
  const subEl = document.getElementById('vm-sub');
  const langChip = document.getElementById('vm-lang-chip');
  const inputEl = document.getElementById('vm-text-input');

  if (titleEl) titleEl.textContent = S.title;
  if (subEl) subEl.textContent = S.subtitle;
  if (langChip) langChip.textContent = lang.toUpperCase();
  if (inputEl) inputEl.placeholder = S.typePlaceholder;

  renderQuickChips();
}

function renderQuickChips() {
  const container = document.getElementById('vm-quick-chips');
  if (!container) return;

  const S = getStrings();
  container.innerHTML = S.quickQuestions
    .map(q => `<button class="voice-chip-btn" type="button">${q}</button>`)
    .join('');

  container.querySelectorAll('.voice-chip-btn').forEach(btn => {
    btn.onclick = () => {
      const text = btn.textContent.replace(/^[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}]\s*/u, '').trim();
      handleUserQuery(text);
    };
  });
}

function renderTurns() {
  const welcomeView = document.getElementById('vm-welcome');
  const turnsContainer = document.getElementById('vm-turns');
  if (!turnsContainer) return;

  if (conversationHistory.length === 0) {
    if (welcomeView) welcomeView.classList.remove('hidden');
    turnsContainer.innerHTML = '';
    return;
  }

  if (welcomeView) welcomeView.classList.add('hidden');

  const S = getStrings();

  turnsContainer.innerHTML = conversationHistory
    .map((turn, idx) => {
      if (turn.role === 'user') {
        return `
          <div class="voice-turn voice-turn-user">
            <div class="voice-bubble user-bubble">
              <span class="bubble-role">👨‍🌾 You</span>
              <p class="bubble-text">${escapeHtml(turn.text)}</p>
            </div>
          </div>
        `;
      }

      // Assistant Turn
      const card = turn.card;
      const escalation = turn.escalation;
      const disclaimer = turn.disclaimer;

      let cardHtml = '';
      if (card && card.title) {
        const pointsHtml = (card.key_points || [])
          .map(pt => `<li class="card-point">• ${escapeHtml(pt)}</li>`)
          .join('');

        let pillHtml = '';
        if (card.action_pill && card.action_pill.label && card.action_pill.action) {
          pillHtml = `
            <button class="voice-action-pill-btn" data-action="${escapeHtml(card.action_pill.action)}">
              ${escapeHtml(card.action_pill.label)} ➔
            </button>
          `;
        }

        cardHtml = `
          <div class="voice-display-card">
            <div class="voice-card-badge">${escapeHtml(card.category || 'Advisory')}</div>
            <h4 class="voice-card-title">${escapeHtml(card.title)}</h4>
            <ul class="voice-card-points">${pointsHtml}</ul>
            ${pillHtml}
          </div>
        `;
      }

      let escalationHtml = '';
      if (escalation && escalation.recommended) {
        escalationHtml = `
          <div class="voice-escalation-card">
            <div class="esc-header">
              <span class="esc-icon">👨‍🌾</span>
              <strong>${S.expertTitle}</strong>
            </div>
            ${escalation.suggested_question ? `<p class="esc-q"><em>"${escapeHtml(escalation.suggested_question)}"</em></p>` : ''}
            <button class="voice-expert-btn" data-action="navigate_experts">${S.expertBtn} ➔</button>
          </div>
        `;
      }

      let disclaimerHtml = '';
      if (disclaimer) {
        disclaimerHtml = `<div class="voice-disclaimer-text">ℹ️ ${escapeHtml(disclaimer)}</div>`;
      }

      return `
        <div class="voice-turn voice-turn-assistant">
          <div class="voice-bubble assistant-bubble">
            <div class="assistant-header">
              <span class="bubble-role">🌾 AGRIFY Copilot</span>
              <button class="voice-replay-btn" data-turn-idx="${idx}" title="Replay voice audio" aria-label="Replay audio">🔊 Listen</button>
            </div>
            <p class="bubble-text">${escapeHtml(turn.text)}</p>
            ${cardHtml}
            ${escalationHtml}
            ${disclaimerHtml}
          </div>
        </div>
      `;
    })
    .join('');

  // Attach dynamic action pill & replay click handlers
  turnsContainer.querySelectorAll('[data-action]').forEach(btn => {
    btn.onclick = (e) => {
      e.preventDefault();
      const action = btn.dataset.action;
      executeSafeNavigationAction(action);
    };
  });

  turnsContainer.querySelectorAll('.voice-replay-btn').forEach(btn => {
    btn.onclick = () => {
      const idx = parseInt(btn.dataset.turnIdx, 10);
      const item = conversationHistory[idx];
      if (item && item.text) {
        speak(item.text, {
          lang: getLang() || 'en',
          onStart: () => setState('SPEAKING'),
          onEnd: () => setState('IDLE'),
        });
      }
    };
  });

  // Auto scroll to latest response
  const body = document.getElementById('vm-body');
  if (body) body.scrollTop = body.scrollHeight;
}

// ============================================================
// SAFE NAVIGATION ACTION EXECUTOR
// ============================================================
function executeSafeNavigationAction(action) {
  const ALLOWED_ACTIONS = {
    navigate_analysis: 'analysis',
    navigate_weather: 'weather',
    navigate_market: 'market',
    navigate_alerts: 'alerts',
    navigate_cropDoctor: 'cropDoctor',
    navigate_experts: 'experts',
    navigate_home: 'home',
  };

  const page = ALLOWED_ACTIONS[action];
  if (page) {
    closeVoiceAssistantModal();
    window.dispatchEvent(new CustomEvent('navigate', { detail: page }));
  } else {
    console.warn('Unknown navigation action blocked:', action);
  }
}

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
