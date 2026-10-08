// ============================================================
// Intro Video Walkthrough — Voice Narrated, Multi-Language
// ============================================================

const SLIDES = {
  en: [
    { icon: '🌾', title: 'Welcome to AgriConnect', text: 'Your smart farming assistant powered by GPS and satellite data. Let me show you how it works!', bg: 'linear-gradient(135deg,#0a2e1a,#0f3d1e)' },
    { icon: '🌱', title: 'Farm Analyzer', text: 'Capture your GPS location, and we fetch real satellite soil data — NPK, pH, moisture. Then we recommend the best 3 crops for your farm.', bg: 'linear-gradient(135deg,#1a2e0a,#1e3d0f)' },
    { icon: '🌤️', title: 'Live Weather', text: 'Get real-time weather for your exact GPS location. 5-day forecasts with farming advisories to protect your crops.', bg: 'linear-gradient(135deg,#0a1a2e,#0f2e3d)' },
    { icon: '📊', title: 'Market Prices', text: 'Search live Mandi prices across India. Find the best-paying market near you and maximize your profit.', bg: 'linear-gradient(135deg,#2e1a0a,#3d2e0f)' },
    { icon: '🔬', title: 'Crop Doctor', text: 'Upload a leaf photo and diseases are detected instantly. Get treatment recommendations and save your crops.', bg: 'linear-gradient(135deg,#1a0a2e,#2e0f3d)' },
    { icon: '💬', title: 'Smart Chatbot', text: 'Ask any farming question in English or Telugu. Get instant, expert-level advice powered by Google Gemini.', bg: 'linear-gradient(135deg,#0a2e2e,#0f3d3d)' },
    { icon: '🚨', title: 'Smart Alerts', text: 'Automated alerts from weather, satellite NDVI, agriculture news, and crop calendars. Never miss critical information.', bg: 'linear-gradient(135deg,#2e0a0a,#3d0f0f)' },
    { icon: '👨‍🌾', title: 'Expert Connect', text: 'Talk to certified agronomists and plant pathologists directly via call or WhatsApp for professional advice.', bg: 'linear-gradient(135deg,#0a2e1a,#0f3d1e)' },
    { icon: '🚀', title: 'Get Started Now!', text: 'Click "Analyze My Farm" to begin. AgriConnect is free, works on any device, and supports multiple languages. Happy farming!', bg: 'linear-gradient(135deg,#162e0a,#1e3d16)' },
  ],
  te: [
    { icon: '🌾', title: 'AgriConnect కు స్వాగతం', text: 'GPS మరియు ఉపగ్రహ డేటాతో నడిచే మీ స్మార్ట్ వ్యవసాయ సహాయకుడు. ఇది ఎలా పని చేస్తుందో చూపిస్తాను!', bg: 'linear-gradient(135deg,#0a2e1a,#0f3d1e)' },
    { icon: '🌱', title: 'పొలం విశ్లేషకుడు', text: 'మీ GPS స్థానాన్ని క్యాప్చర్ చేయండి, ఉపగ్రహ నేల డేటా — NPK, pH, తేమ పొందండి. మీ పొలానికి ఉత్తమ 3 పంటలను సిఫారసు చేస్తుంది.', bg: 'linear-gradient(135deg,#1a2e0a,#1e3d0f)' },
    { icon: '🌤️', title: 'ప్రత్యక్ష వాతావరణం', text: 'మీ GPS స్థానం కోసం నిజ-సమయ వాతావరణం. వ్యవసాయ సలహాలతో 5-రోజుల అంచనా.', bg: 'linear-gradient(135deg,#0a1a2e,#0f2e3d)' },
    { icon: '📊', title: 'మార్కెట్ ధరలు', text: 'భారతదేశం అంతటా మండి ధరలు శోధించండి. మీ సమీపంలోని అత్యుత్తమ మార్కెట్‌ను కనుగొనండి.', bg: 'linear-gradient(135deg,#2e1a0a,#3d2e0f)' },
    { icon: '🔬', title: 'పంట వైద్యుడు', text: 'ఆకు ఫోటో అప్‌లోడ్ చేయండి, వ్యాధులను గుర్తిస్తుంది. చికిత్స సిఫారసులు పొందండి.', bg: 'linear-gradient(135deg,#1a0a2e,#2e0f3d)' },
    { icon: '💬', title: 'స్మార్ట్ చాట్‌బాట్', text: 'ఇంగ్లీష్ లేదా తెలుగులో వ్యవసాయ ప్రశ్నలు అడగండి. Google Gemini ద్వారా తక్షణ సలహా పొందండి.', bg: 'linear-gradient(135deg,#0a2e2e,#0f3d3d)' },
    { icon: '🚨', title: 'స్మార్ట్ హెచ్చరికలు', text: 'వాతావరణం, ఉపగ్రహ, వార్తలు మరియు పంట క్యాలెండర్ల నుండి స్వయంచాలక హెచ్చరికలు.', bg: 'linear-gradient(135deg,#2e0a0a,#3d0f0f)' },
    { icon: '👨‍🌾', title: 'నిపుణుల సంప్రదింపు', text: 'కాల్ లేదా వాట్సాప్ ద్వారా సర్టిఫైడ్ వ్యవసాయ శాస్త్రవేత్తలతో నేరుగా మాట్లాడండి.', bg: 'linear-gradient(135deg,#0a2e1a,#0f3d1e)' },
    { icon: '🚀', title: 'ఇప్పుడే ప్రారంభించండి!', text: '"నా పొలాన్ని విశ్లేషించండి" క్లిక్ చేయండి. AgriConnect ఉచితం, ఏ పరికరంలోనైనా పని చేస్తుంది!', bg: 'linear-gradient(135deg,#162e0a,#1e3d16)' },
  ],
  hi: [
    { icon: '🌾', title: 'AgriConnect में स्वागत है', text: 'GPS और सैटेलाइट डेटा से संचालित आपका स्मार्ट खेती सहायक। मैं आपको दिखाता हूँ यह कैसे काम करता है!', bg: 'linear-gradient(135deg,#0a2e1a,#0f3d1e)' },
    { icon: '🌱', title: 'फार्म एनालाइज़र', text: 'अपना GPS लोकेशन कैप्चर करें, सैटेलाइट मिट्टी डेटा प्राप्त करें — NPK, pH, नमी। आपके खेत के लिए सर्वश्रेष्ठ 3 फसलों की सिफारिश करता है।', bg: 'linear-gradient(135deg,#1a2e0a,#1e3d0f)' },
    { icon: '🌤️', title: 'लाइव मौसम', text: 'आपके GPS लोकेशन के लिए रियल-टाइम मौसम। खेती सलाह के साथ 5-दिन का पूर्वानुमान।', bg: 'linear-gradient(135deg,#0a1a2e,#0f2e3d)' },
    { icon: '📊', title: 'बाज़ार भाव', text: 'पूरे भारत में मंडी भाव खोजें। अपने पास का सबसे अच्छा बाज़ार खोजें।', bg: 'linear-gradient(135deg,#2e1a0a,#3d2e0f)' },
    { icon: '🔬', title: 'फसल डॉक्टर', text: 'पत्ती की फोटो अपलोड करें, बीमारी पहचानता है। उपचार की सिफारिशें प्राप्त करें।', bg: 'linear-gradient(135deg,#1a0a2e,#2e0f3d)' },
    { icon: '💬', title: 'स्मार्ट चैटबॉट', text: 'हिंदी या अंग्रेज़ी में खेती के सवाल पूछें। Google Gemini से तुरंत सलाह पाएं।', bg: 'linear-gradient(135deg,#0a2e2e,#0f3d3d)' },
    { icon: '🚨', title: 'स्मार्ट अलर्ट', text: 'मौसम, सैटेलाइट, समाचार और फसल कैलेंडर से स्वचालित अलर्ट।', bg: 'linear-gradient(135deg,#2e0a0a,#3d0f0f)' },
    { icon: '👨‍🌾', title: 'विशेषज्ञ संपर्क', text: 'कॉल या WhatsApp के ज़रिए प्रमाणित कृषि वैज्ञानिकों से सीधे बात करें।', bg: 'linear-gradient(135deg,#0a2e1a,#0f3d1e)' },
    { icon: '🚀', title: 'अभी शुरू करें!', text: '"मेरा खेत विश्लेषण करें" पर क्लिक करें। AgriConnect मुफ़्त है और किसी भी डिवाइस पर काम करता है!', bg: 'linear-gradient(135deg,#162e0a,#1e3d16)' },
  ],
  ta: [
    { icon: '🌾', title: 'AgriConnect க்கு வரவேற்கிறோம்', text: 'GPS மற்றும் செயற்கைக்கோள் தரவுகளால் இயங்கும் உங்கள் ஸ்மார்ட் விவசாய உதவியாளர்!', bg: 'linear-gradient(135deg,#0a2e1a,#0f3d1e)' },
    { icon: '🌱', title: 'பண்ணை ஆய்வாளர்', text: 'GPS இருப்பிடத்தைப் பிடித்து, மண் தரவு பெறுங்கள். சிறந்த 3 பயிர்களை பரிந்துரைக்கிறது.', bg: 'linear-gradient(135deg,#1a2e0a,#1e3d0f)' },
    { icon: '🌤️', title: 'நேரடி வானிலை', text: 'உங்கள் GPS இருப்பிடத்திற்கான நிகழ்நேர வானிலை. 5 நாள் முன்னறிவிப்பு.', bg: 'linear-gradient(135deg,#0a1a2e,#0f2e3d)' },
    { icon: '📊', title: 'சந்தை விலைகள்', text: 'இந்தியா முழுவதும் மண்டி விலைகளைத் தேடுங்கள்.', bg: 'linear-gradient(135deg,#2e1a0a,#3d2e0f)' },
    { icon: '🔬', title: 'பயிர் மருத்துவர்', text: 'இலை புகைப்படத்தை பதிவேற்றுங்கள், நோய்களைக் கண்டறியும்.', bg: 'linear-gradient(135deg,#1a0a2e,#2e0f3d)' },
    { icon: '💬', title: 'ஸ்மார்ட் சாட்போட்', text: 'தமிழில் விவசாய கேள்விகளைக் கேளுங்கள். உடனடி ஆலோசனை பெறுங்கள்.', bg: 'linear-gradient(135deg,#0a2e2e,#0f3d3d)' },
    { icon: '🚨', title: 'ஸ்மார்ட் எச்சரிக்கைகள்', text: 'வானிலை, செயற்கைக்கோள் மற்றும் பயிர் காலண்டர்களில் இருந்து தானியங்கி எச்சரிக்கைகள்.', bg: 'linear-gradient(135deg,#2e0a0a,#3d0f0f)' },
    { icon: '👨‍🌾', title: 'நிபுணர் தொடர்பு', text: 'அழைப்பு அல்லது WhatsApp மூலம் விவசாய விஞ்ஞானிகளுடன் பேசுங்கள்.', bg: 'linear-gradient(135deg,#0a2e1a,#0f3d1e)' },
    { icon: '🚀', title: 'இப்போதே தொடங்குங்கள்!', text: 'AgriConnect இலவசம், எந்த சாதனத்திலும் வேலை செய்யும்!', bg: 'linear-gradient(135deg,#162e0a,#1e3d16)' },
  ],
  kn: [
    { icon: '🌾', title: 'AgriConnect ಗೆ ಸ್ವಾಗತ', text: 'GPS ಮತ್ತು ಉಪಗ್ರಹ ಡೇಟಾದಿಂದ ನಡೆಸಲ್ಪಡುವ ನಿಮ್ಮ ಸ್ಮಾರ್ಟ್ ಕೃಷಿ ಸಹಾಯಕ!', bg: 'linear-gradient(135deg,#0a2e1a,#0f3d1e)' },
    { icon: '🌱', title: 'ಫಾರ್ಮ್ ವಿಶ್ಲೇಷಕ', text: 'ನಿಮ್ಮ GPS ಸ್ಥಳವನ್ನು ಸೆರೆಹಿಡಿಯಿರಿ, ಮಣ್ಣಿನ ಡೇಟಾ ಪಡೆಯಿರಿ. ಉತ್ತಮ 3 ಬೆಳೆಗಳನ್ನು ಶಿಫಾರಸು ಮಾಡುತ್ತದೆ.', bg: 'linear-gradient(135deg,#1a2e0a,#1e3d0f)' },
    { icon: '🌤️', title: 'ನೇರ ಹವಾಮಾನ', text: 'ನಿಮ್ಮ GPS ಸ್ಥಳಕ್ಕಾಗಿ ನೈಜ-ಸಮಯದ ಹವಾಮಾನ. 5-ದಿನಗಳ ಮುನ್ಸೂಚನೆ.', bg: 'linear-gradient(135deg,#0a1a2e,#0f2e3d)' },
    { icon: '📊', title: 'ಮಾರುಕಟ್ಟೆ ಬೆಲೆಗಳು', text: 'ಭಾರತಾದ್ಯಂತ ಮಂಡಿ ಬೆಲೆಗಳನ್ನು ಹುಡುಕಿ.', bg: 'linear-gradient(135deg,#2e1a0a,#3d2e0f)' },
    { icon: '🔬', title: 'ಬೆಳೆ ವೈದ್ಯ', text: 'ಎಲೆ ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ, ರೋಗಗಳನ್ನು ಗುರುತಿಸುತ್ತದೆ.', bg: 'linear-gradient(135deg,#1a0a2e,#2e0f3d)' },
    { icon: '💬', title: 'ಸ್ಮಾರ್ಟ್ ಚಾಟ್‌ಬಾಟ್', text: 'ಕನ್ನಡದಲ್ಲಿ ಕೃಷಿ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳಿ. ತಕ್ಷಣ ಸಲಹೆ ಪಡೆಯಿರಿ.', bg: 'linear-gradient(135deg,#0a2e2e,#0f3d3d)' },
    { icon: '🚨', title: 'ಸ್ಮಾರ್ಟ್ ಎಚ್ಚರಿಕೆಗಳು', text: 'ಹವಾಮಾನ, ಉಪಗ್ರಹ ಮತ್ತು ಬೆಳೆ ಕ್ಯಾಲೆಂಡರ್‌ಗಳಿಂದ ಸ್ವಯಂಚಾಲಿತ ಎಚ್ಚರಿಕೆಗಳು.', bg: 'linear-gradient(135deg,#2e0a0a,#3d0f0f)' },
    { icon: '👨‍🌾', title: 'ತಜ್ಞರ ಸಂಪರ್ಕ', text: 'ಕರೆ ಅಥವಾ WhatsApp ಮೂಲಕ ಕೃಷಿ ವಿಜ್ಞಾನಿಗಳೊಂದಿಗೆ ಮಾಟಾಡಿ.', bg: 'linear-gradient(135deg,#0a2e1a,#0f3d1e)' },
    { icon: '🚀', title: 'ಈಗಲೇ ಪ್ರಾರಂಭಿಸಿ!', text: 'AgriConnect ಉಚಿತ, ಯಾವುದೇ ಸಾಧನದಲ್ಲಿ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ!', bg: 'linear-gradient(135deg,#162e0a,#1e3d16)' },
  ],
};

const LANG_LABELS = { en:'English', te:'తెలుగు', hi:'हिन्दी', ta:'தமிழ்', kn:'ಕನ್ನಡ' };

let currentSlide = 0, currentLang = 'en', isPlaying = false, autoTimer = null, speechSynth = window.speechSynthesis;
const VOICE_MAP = { en:'en-IN', te:'te-IN', hi:'hi-IN', ta:'ta-IN', kn:'kn-IN' };

function speak(text, lang) {
  speechSynth.cancel();
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = VOICE_MAP[lang] || 'en-IN';
  utter.rate = 0.9; utter.pitch = 1;
  const voices = speechSynth.getVoices();
  const match = voices.find(v => v.lang === utter.lang) || voices.find(v => v.lang.startsWith(lang));
  if (match) utter.voice = match;
  utter.onend = () => { if (isPlaying) nextSlide(); };
  speechSynth.speak(utter);
}

function stopSpeech() { speechSynth.cancel(); }

function nextSlide() {
  const slides = SLIDES[currentLang] || SLIDES.en;
  if (currentSlide < slides.length - 1) { currentSlide++; updatePlayer(); }
  else { isPlaying = false; clearInterval(autoTimer); updatePlayer(); }
}

function prevSlide() {
  if (currentSlide > 0) { currentSlide--; stopSpeech(); updatePlayer(); if(isPlaying) playCurrentSlide(); }
}

function playCurrentSlide() {
  const slides = SLIDES[currentLang] || SLIDES.en;
  const s = slides[currentSlide];
  speak(s.text, currentLang);
}

function togglePlay() {
  isPlaying = !isPlaying;
  if (isPlaying) playCurrentSlide();
  else stopSpeech();
  updatePlayer();
}

function setLang(lang) {
  currentLang = lang; currentSlide = 0; stopSpeech();
  if (isPlaying) playCurrentSlide();
  updatePlayer();
}

function goToSlide(i) {
  currentSlide = i; stopSpeech();
  if (isPlaying) playCurrentSlide();
  updatePlayer();
}

function updatePlayer() {
  const slides = SLIDES[currentLang] || SLIDES.en;
  const s = slides[currentSlide];
  const container = document.getElementById('intro-video-player');
  if (!container) return;

  // Update slide content
  const stage = container.querySelector('.iv-stage');
  if (stage) {
    stage.style.background = s.bg;
    stage.innerHTML = `
      <div class="iv-slide-icon">${s.icon}</div>
      <h3 class="iv-slide-title">${s.title}</h3>
      <p class="iv-slide-text">${s.text}</p>
      <div class="iv-ai-badge">🎙️ Voice Narrator</div>
    `;
    stage.classList.remove('iv-slide-enter');
    void stage.offsetWidth;
    stage.classList.add('iv-slide-enter');
  }

  // Progress bar
  const prog = container.querySelector('.iv-progress-fill');
  if (prog) prog.style.width = `${((currentSlide + 1) / slides.length) * 100}%`;

  // Counter
  const counter = container.querySelector('.iv-counter');
  if (counter) counter.textContent = `${currentSlide + 1} / ${slides.length}`;

  // Play button
  const playBtn = container.querySelector('.iv-play-btn');
  if (playBtn) playBtn.innerHTML = isPlaying ? '⏸️' : '▶️';

  // Dots
  const dots = container.querySelector('.iv-dots');
  if (dots) {
    dots.innerHTML = slides.map((_, i) =>
      `<button class="iv-dot ${i === currentSlide ? 'active' : ''}" data-slide="${i}"></button>`
    ).join('');
    dots.querySelectorAll('.iv-dot').forEach(d => {
      d.addEventListener('click', () => goToSlide(parseInt(d.dataset.slide)));
    });
  }

  // Lang buttons
  container.querySelectorAll('.iv-lang-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.lang === currentLang);
  });
}

export function renderIntroVideo() {
  const langBtns = Object.entries(LANG_LABELS).map(([k,v]) =>
    `<button class="iv-lang-btn ${k === currentLang ? 'active' : ''}" data-lang="${k}">${v}</button>`
  ).join('');

  return `
    <div class="iv-section" id="intro-video-section">
      <div class="iv-header">
        <div class="iv-header-badge">🎬 How AgriConnect Works</div>
        <h2 class="iv-header-title">Interactive App Tour</h2>
        <p class="iv-header-sub">Watch us explain every feature — in your language</p>
      </div>
      <div class="iv-lang-bar">${langBtns}</div>
      <div class="iv-player" id="intro-video-player">
        <div class="iv-stage iv-slide-enter" style="background:linear-gradient(135deg,#0a2e1a,#0f3d1e)">
          <div class="iv-slide-icon">🌾</div>
          <h3 class="iv-slide-title">Welcome to AgriConnect</h3>
          <p class="iv-slide-text">Press play to start the tour!</p>
          <div class="iv-ai-badge">🎙️ Voice Narrator</div>
        </div>
        <div class="iv-controls">
          <div class="iv-progress"><div class="iv-progress-fill"></div></div>
          <div class="iv-ctrl-row">
            <button class="iv-ctrl-btn iv-prev-btn">⏮️</button>
            <button class="iv-ctrl-btn iv-play-btn">▶️</button>
            <button class="iv-ctrl-btn iv-next-btn">⏭️</button>
            <span class="iv-counter">1 / 9</span>
            <div class="iv-dots"></div>
          </div>
        </div>
      </div>
    </div>
  `;
}

export function initIntroVideo() {
  // Load voices
  if (speechSynth.onvoiceschanged !== undefined) {
    speechSynth.onvoiceschanged = () => {};
  }
  speechSynth.getVoices();

  const container = document.getElementById('intro-video-player');
  if (!container) return;

  // Controls
  container.querySelector('.iv-play-btn')?.addEventListener('click', togglePlay);
  container.querySelector('.iv-prev-btn')?.addEventListener('click', prevSlide);
  container.querySelector('.iv-next-btn')?.addEventListener('click', nextSlide);

  // Lang buttons
  document.querySelectorAll('.iv-lang-btn').forEach(b => {
    b.addEventListener('click', () => setLang(b.dataset.lang));
  });

  // Initialize dots
  updatePlayer();
}
