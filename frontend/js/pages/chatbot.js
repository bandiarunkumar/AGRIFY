// ============================================================
// AgriConnect AI — Premium ChatGPT-Style Chatbot
// Voice input, Camera, File upload, Markdown, Full power
// ============================================================

import { sendChatMessage, translateDynamicText } from '../api.js';
import { showToast } from '../voice.js';

let chatHistory = [];
let currentLang = 'en';
let isRecording = false;
let mediaRecorder = null;
let recognition = null;

const BOT_GREETINGS = {
  en: "🌾 **Namaste! I'm AgriConnect** — your intelligent farming companion.\n\nI can help you with:\n• 🌱 Crop recommendations & management\n• 💊 Disease diagnosis & treatment\n• 🧪 Fertilizer & soil advice\n• 💰 Market prices & government schemes\n• 🌤️ Weather-based farming tips\n• 📚 **Any question** — ask me anything!\n\nAsk me anything in **English** or **Telugu**. I'm here to help! 🚀",
  te: "🌾 **నమస్కారం! నేను AgriConnect** — మీ తెలివైన వ్యవసాయ సహాయకుడిని.\n\nనేను మీకు సహాయం చేయగలను:\n• 🌱 పంట సిఫారసులు & నిర్వహణ\n• 💊 వ్యాధి నిర్ధారణ & చికిత్స\n• 🧪 ఎరువులు & నేల సలహా\n• 💰 మార్కెట్ ధరలు & ప్రభుత్వ పథకాలు\n• 🌤️ వాతావరణ ఆధారిత వ్యవసాయ చిట్కాలు\n• 📚 **ఏదైనా ప్రశ్న** — ఏదైనా అడగండి!\n\n**ఇంగ్లీష్** లేదా **తెలుగు**లో ఏదైనా అడగండి. నేను సహాయం చేయడానికి ఇక్కడ ఉన్నాను! 🚀"
};

const QUICK_QUESTIONS = {
  en: [
    "🌾 What crop should I grow this Kharif?",
    "🐛 How to control fall armyworm in maize?",
    "💰 PM Kisan Yojana eligibility",
    "🧪 Best fertilizer for rice paddy",
    "🐄 Increase milk production in cows",
    "📊 Current MSP for wheat?",
    "💧 Drip irrigation benefits & cost",
    "🌿 Soil preparation for turmeric",
  ],
  te: [
    "🌾 ఖరీఫ్‌లో ఏ పంట వేయాలి?",
    "🐛 మొక్కజొన్నలో సేనా పురుగు నియంత్రణ",
    "💰 PM కిసాన్ యోజన అర్హత",
    "🧪 వరికి ఉత్తమ ఎరువు",
    "🐄 పాల ఉత్పత్తి పెంచడం",
    "📊 గోధుమ MSP ఎంత?",
    "💧 డ్రిప్ ఇరిగేషన్ ప్రయోజనాలు",
    "🌿 పసుపు సాగుకు నేల సిద్ధం",
  ]
};

/* ── Markdown → HTML ────────────────────────────────── */
function renderMarkdown(text) {
  if (!text) return '';
  let html = text
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="lang-$1">$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^### (.+)$/gm, '<h4 class="chat-h4">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 class="chat-h3">$1</h3>')
    .replace(/^# (.+)$/gm, '<h2 class="chat-h2">$1</h2>')
    .replace(/^---$/gm, '<hr class="chat-hr">')
    .replace(/^\d+\.\s(.+)$/gm, '<li class="chat-oli">$1</li>')
    .replace(/^[•\-\*]\s(.+)$/gm, '<li class="chat-li">$1</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
  html = html.replace(/((?:<li class="chat-li">.*?<\/li>\s*(?:<br>)?)+)/g, '<ul class="chat-ul">$1</ul>');
  html = html.replace(/((?:<li class="chat-oli">.*?<\/li>\s*(?:<br>)?)+)/g, '<ol class="chat-ol">$1</ol>');
  html = html.replace(/<ul class="chat-ul">(\s*<br>)?/g, '<ul class="chat-ul">');
  html = html.replace(/<ol class="chat-ol">(\s*<br>)?/g, '<ol class="chat-ol">');
  html = html.replace(/<br>\s*<\/ul>/g, '</ul>');
  html = html.replace(/<br>\s*<\/ol>/g, '</ol>');
  return `<p>${html}</p>`.replace(/<p><\/p>/g, '');
}

function escapeHtml(text) {
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

/* ── Render Page ────────────────────────────────────── */
export function renderChatbot() {
  const greet = BOT_GREETINGS[currentLang];
  chatHistory = [{ role: 'bot', text: greet }];
  return `
  <div class="page-section chatbot-page">
    <div class="chatbot-fullscreen">
      <!-- Header -->
      <div class="chatbot-header">
        <div class="chatbot-header-left">
          <div class="chatbot-avatar">
            <div class="chatbot-avatar-inner">🌾</div>
            <span class="chatbot-status-dot"></span>
          </div>
          <div>
            <div class="chatbot-header-name">AgriConnect</div>
            <div class="chatbot-header-status"><span class="status-pulse"></span> Powered by Gemini · Always Online</div>
          </div>
        </div>
        <div class="chatbot-header-right">
          <button class="chatbot-lang-btn ${currentLang==='en'?'active':''}" id="lang-en-btn">EN</button>
          <button class="chatbot-lang-btn ${currentLang==='te'?'active':''}" id="lang-te-btn">తె</button>
          <button class="chatbot-icon-btn" id="chat-clear-btn" title="New chat"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg></button>
        </div>
      </div>

      <!-- Messages -->
      <div class="chatbot-messages-area" id="chat-messages">
        <div class="chat-welcome-card">
          <div class="welcome-glow"></div>
          <div class="welcome-icon">🌾</div>
          <div class="welcome-title">AgriConnect</div>
          <div class="welcome-subtitle">Your intelligent farming companion — ask me anything!</div>
          <div class="welcome-chips" id="welcome-chips">
            ${(QUICK_QUESTIONS[currentLang]||QUICK_QUESTIONS.en).map(q=>`<button class="welcome-chip" data-question="${q.replace(/^[^\s]+\s/,'')}">${q}</button>`).join('')}
          </div>
        </div>
        <div class="chat-bubble bot">
          <div class="chat-bubble-avatar">🌾</div>
          <div class="chat-bubble-content">
            <div class="chat-bubble-text">${renderMarkdown(greet)}</div>
            <div class="chat-bubble-time">${new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</div>
          </div>
        </div>
      </div>

      <!-- Image Preview -->
      <div class="chat-preview-bar" id="chat-preview-bar" style="display:none;">
        <div class="preview-thumb" id="preview-thumb"></div>
        <span class="preview-name" id="preview-name"></span>
        <button class="preview-remove" id="preview-remove">✕</button>
      </div>

      <!-- Input Bar -->
      <div class="chatbot-input-bar">
        <div class="chatbot-input-wrapper">
          <input type="file" id="chat-file-input" accept="image/*" style="display:none" />
          <input type="file" id="chat-camera-input" accept="image/*" capture="environment" style="display:none" />
          <button class="chat-tool-btn" id="chat-attach-btn" title="Upload image">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
          </button>
          <button class="chat-tool-btn" id="chat-camera-btn" title="Take photo">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
          </button>
          <textarea id="chat-input" class="chatbot-textarea" placeholder="${currentLang==='te'?'మీ ప్రశ్న అడగండి...':'Ask me anything...'}" rows="1"></textarea>
          <button class="chat-tool-btn voice-btn" id="chat-voice-btn" title="Voice input">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
          </button>
          <button class="chatbot-send-btn" id="chat-send-btn" title="Send">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          </button>
        </div>
        <div class="chatbot-input-hint">AgriConnect can make mistakes. Verify important farming advice with local experts.</div>
      </div>
    </div>
  </div>`;
}

/* ── Init ──────────────────────────────────────────── */
export function initChatbot() {
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send-btn');

  sendBtn?.addEventListener('click', ()=> handleSend());
  input?.addEventListener('keydown', e => { if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();handleSend();} });
  input?.addEventListener('input', ()=>{ input.style.height='auto'; input.style.height=Math.min(input.scrollHeight,150)+'px'; });

  // Language
  document.getElementById('lang-en-btn')?.addEventListener('click',()=>{currentLang='en';window.dispatchEvent(new CustomEvent('navigate',{detail:'chatbot'}));});
  document.getElementById('lang-te-btn')?.addEventListener('click',()=>{currentLang='te';window.dispatchEvent(new CustomEvent('navigate',{detail:'chatbot'}));});

  // Clear
  document.getElementById('chat-clear-btn')?.addEventListener('click',()=>{chatHistory=[];pendingImage=null;window.dispatchEvent(new CustomEvent('navigate',{detail:'chatbot'}));});

  // Quick questions (both welcome chips and regular)
  document.querySelectorAll('[data-question]').forEach(btn=>{
    btn.addEventListener('click',()=>{
      if(input){input.value=btn.dataset.question;handleSend();}
    });
  });

  // File upload
  document.getElementById('chat-attach-btn')?.addEventListener('click',()=>document.getElementById('chat-file-input')?.click());
  document.getElementById('chat-file-input')?.addEventListener('change', handleFileSelect);

  // Camera
  document.getElementById('chat-camera-btn')?.addEventListener('click',()=>document.getElementById('chat-camera-input')?.click());
  document.getElementById('chat-camera-input')?.addEventListener('change', handleFileSelect);

  // Preview remove
  document.getElementById('preview-remove')?.addEventListener('click', clearPreview);

  // Voice
  document.getElementById('chat-voice-btn')?.addEventListener('click', toggleVoice);

  setTimeout(()=>input?.focus(), 300);
}

/* ── File / Image Handling ────────────────────────── */
let pendingImage = null;

function handleFileSelect(e) {
  const file = e.target.files?.[0];
  if (!file) return;
  if (!file.type.startsWith('image/')) { showToast('Please select an image file', 'warning'); return; }
  if (file.size > 10*1024*1024) { showToast('Image must be under 10MB', 'warning'); return; }

  const reader = new FileReader();
  reader.onload = (ev) => {
    pendingImage = { file, dataUrl: ev.target.result, name: file.name };
    showPreview(ev.target.result, file.name);
  };
  reader.readAsDataURL(file);
  e.target.value = '';
}

function showPreview(dataUrl, name) {
  const bar = document.getElementById('chat-preview-bar');
  const thumb = document.getElementById('preview-thumb');
  const nameEl = document.getElementById('preview-name');
  if (bar && thumb && nameEl) {
    thumb.innerHTML = `<img src="${dataUrl}" alt="preview" />`;
    nameEl.textContent = name;
    bar.style.display = 'flex';
  }
}

function clearPreview() {
  pendingImage = null;
  const bar = document.getElementById('chat-preview-bar');
  if (bar) bar.style.display = 'none';
}

/* ── Voice Input ──────────────────────────────────── */
function toggleVoice() {
  const btn = document.getElementById('chat-voice-btn');
  if (isRecording) { stopVoice(); return; }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) { showToast('Voice input not supported in this browser', 'warning'); return; }

  recognition = new SpeechRecognition();
  recognition.lang = currentLang === 'te' ? 'te-IN' : 'en-IN';
  recognition.interimResults = true;
  recognition.continuous = false;

  recognition.onstart = () => {
    isRecording = true;
    btn?.classList.add('recording');
    showToast('🎙️ Listening... Speak now', 'info');
  };

  recognition.onresult = (event) => {
    const input = document.getElementById('chat-input');
    let transcript = '';
    for (let i = 0; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }
    if (input) input.value = transcript;
  };

  recognition.onend = () => {
    isRecording = false;
    btn?.classList.remove('recording');
    const input = document.getElementById('chat-input');
    if (input?.value?.trim()) {
      handleSend();
    }
  };

  recognition.onerror = (e) => {
    isRecording = false;
    btn?.classList.remove('recording');
    if (e.error !== 'no-speech') showToast('Voice error: ' + e.error, 'error');
  };

  recognition.start();
}

function stopVoice() {
  const btn = document.getElementById('chat-voice-btn');
  isRecording = false;
  btn?.classList.remove('recording');
  recognition?.stop();
}

/* ── Send Message ─────────────────────────────────── */
async function handleSend() {
  const input = document.getElementById('chat-input');
  const msg = input?.value?.trim();
  const hasImage = !!pendingImage;

  if (!msg && !hasImage) return;

  input.value = '';
  input.style.height = 'auto';

  // Hide welcome chips
  const welcome = document.querySelector('.chat-welcome-card');
  if (welcome) welcome.style.display = 'none';

  // Show user message
  const displayMsg = hasImage ? (msg || '📷 [Image uploaded]') : msg;
  const imageHtml = hasImage ? `<div class="chat-image-preview"><img src="${pendingImage.dataUrl}" alt="uploaded" /></div>` : '';
  appendMessage('user', displayMsg, imageHtml);

  // Build the text to send (describe the image context)
  let textToSend = msg || '';
  if (hasImage) {
    textToSend = (msg ? msg + '\n\n' : '') + '[User has attached an image of a crop/plant leaf. Please analyze it and provide diagnosis, treatment recommendations, and farming advice based on the visual description.]';
  }

  clearPreview();
  const typingId = appendTyping();

  try {
    const result = await sendChatMessage(textToSend, currentLang);
    removeTyping(typingId);
    let responseText = result.reply || 'Sorry, I could not process that. Please try again.';
    if (currentLang !== 'en') {
      try { responseText = await translateDynamicText(responseText, currentLang); } catch(e) {}
    }
    appendMessage('bot', responseText);
  } catch (err) {
    removeTyping(typingId);
    appendMessage('bot', `⚠️ **Connection Error**\n\n${err.message}\n\nPlease check your connection or wait for the server to wake up (30-60 seconds on Render free tier).`);
  }
}

/* ── Append Message ───────────────────────────────── */
function appendMessage(role, text, extraHtml = '') {
  const container = document.getElementById('chat-messages');
  if (!container) return;
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${role}`;
  const time = new Date().toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' });

  if (role === 'bot') {
    bubble.innerHTML = `
      <div class="chat-bubble-avatar">🌾</div>
      <div class="chat-bubble-content">
        <div class="chat-bubble-text">${renderMarkdown(text)}</div>
        <div class="chat-bubble-meta">
          <span class="chat-bubble-time">${time}</span>
          <button class="chat-action-btn copy-btn" title="Copy">📋</button>
          <button class="chat-action-btn speak-btn" title="Read aloud">🔊</button>
        </div>
      </div>`;
    setTimeout(()=>{
      bubble.querySelector('.copy-btn')?.addEventListener('click', function() {
        navigator.clipboard.writeText(text).then(()=>{ this.textContent='✅'; setTimeout(()=>{this.textContent='📋';},1500); });
      });
      bubble.querySelector('.speak-btn')?.addEventListener('click', function() {
        const utter = new SpeechSynthesisUtterance(text.replace(/[*#_`]/g,''));
        utter.lang = currentLang === 'te' ? 'te-IN' : 'en-IN';
        utter.rate = 0.9;
        speechSynthesis.cancel();
        speechSynthesis.speak(utter);
        this.textContent = '⏹️';
        utter.onend = () => { this.textContent = '🔊'; };
      });
    }, 50);
  } else {
    bubble.innerHTML = `
      <div class="chat-bubble-content">
        ${extraHtml}
        <div class="chat-bubble-text">${escapeHtml(text)}</div>
        <div class="chat-bubble-time">${time}</div>
      </div>
      <div class="chat-bubble-avatar user-avatar">👤</div>`;
  }

  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
  chatHistory.push({ role, text });
}

/* ── Typing Indicator ─────────────────────────────── */
function appendTyping() {
  const id = 'typing-' + Date.now();
  const container = document.getElementById('chat-messages');
  if (!container) return id;
  const el = document.createElement('div');
  el.className = 'chat-bubble bot';
  el.id = id;
  el.innerHTML = `
    <div class="chat-bubble-avatar">🌾</div>
    <div class="chat-bubble-content">
      <div class="typing-indicator">
        <div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>
        <span class="typing-label">AgriConnect is thinking...</span>
      </div>
    </div>`;
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeTyping(id) { document.getElementById(id)?.remove(); }
