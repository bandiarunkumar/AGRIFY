// ============================================================
// Voice & Toast Module
// ============================================================

let recognition = null;
let isListening = false;

// ---- Toast ----
export function showToast(message, type = 'info', duration = 4000) {
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
    toast.style.animation = 'fadeInUp 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ---- Voice ----
export function initVoice() {
  // Create voice FAB (floating action button)
  let fab = document.getElementById('voice-fab');
  if (!fab) {
    fab = document.createElement('button');
    fab.id = 'voice-fab';
    fab.className = 'voice-fab hidden';
    fab.title = 'Voice Input (Telugu/English)';
    fab.innerHTML = '🎤';
    fab.setAttribute('aria-label', 'Voice input');
    document.body.appendChild(fab);
  }

  fab.addEventListener('click', toggleVoice);

  // Setup speech recognition
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;

  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'te-IN'; // Telugu first, falls back to English

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    const activeInput = document.querySelector('.form-input:focus, #chat-input');
    if (activeInput) {
      activeInput.value = transcript;
      activeInput.dispatchEvent(new Event('input', { bubbles: true }));
    }
    showToast(`🎤 "${transcript}"`, 'info', 3000);
    stopVoice();
  };

  recognition.onerror = (e) => {
    console.warn('Voice error:', e.error);
    stopVoice();
  };

  recognition.onend = () => stopVoice();
}

function toggleVoice() {
  if (isListening) { stopVoice(); return; }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    showToast('Voice not supported in this browser', 'warning');
    return;
  }
  startVoice();
}

function startVoice() {
  isListening = true;
  const fab = document.getElementById('voice-fab');
  fab?.classList.add('listening');
  fab && (fab.innerHTML = '🔴');
  try { recognition?.start(); } catch (e) { stopVoice(); }
  showToast('🎤 Listening... (Telugu/English)', 'info', 5000);
}

function stopVoice() {
  isListening = false;
  const fab = document.getElementById('voice-fab');
  fab?.classList.remove('listening');
  fab && (fab.innerHTML = '🎤');
  try { recognition?.stop(); } catch (e) { /* ignore */ }
}

// Setup individual mic buttons
export function setupMicButtons() {
  document.querySelectorAll('.mic-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = btn.closest('.input-with-mic')?.querySelector('.form-input');
      if (!input) return;

      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        showToast('Voice input not supported in this browser. Try Chrome.', 'warning');
        return;
      }

      const rec = new SpeechRecognition();
      rec.lang = 'te-IN';
      rec.onresult = (e) => {
        input.value = e.results[0][0].transcript;
        btn.classList.remove('listening');
        showToast(`🎤 "${input.value}"`, 'info', 2000);
      };
      rec.onerror = () => btn.classList.remove('listening');
      rec.onend = () => btn.classList.remove('listening');

      btn.classList.add('listening');
      rec.start();
    });
  });
}
