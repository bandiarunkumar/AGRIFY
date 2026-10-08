// ============================================================
// Experts Page — Contact Real Agriculture Experts
// Beautiful professional directory with call/WhatsApp
// ============================================================

import { t } from '../i18n.js';

const expertsData = [
  {
    id: 1,
    name: 'Kisan Call Centre (KCC)',
    designation: 'Govt. of India — Ministry of Agriculture & Farmers Welfare',
    specialty: 'All Agriculture Queries, Govt. Schemes, MSP, Subsidies, Crop Insurance',
    phone: '18001801551',
    whatsapp: null,
    photo: 'https://images.unsplash.com/photo-1589923188900-85dae523342b?auto=format&fit=crop&w=300&h=300&q=80',
    location: 'Pan India — Toll Free',
    experience: 'Official Govt. Helpline — Available in 22 Indian Languages',
    accentColor: '#f59e0b',
    available: '24/7 — All Days Including Holidays',
    tags: ['Toll-Free', 'Govt. Schemes', 'MSP', '22 Languages'],
  },
  {
    id: 2,
    name: 'Dr. T. Mohapatra',
    designation: 'Former Director General — ICAR (Indian Council of Agricultural Research)',
    specialty: 'Crop Science, Rice Genomics, Seed Technology, Agricultural Policy',
    phone: '+911125842420',
    whatsapp: '911125842420',
    photo: 'https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?auto=format&fit=crop&w=300&h=300&q=80',
    location: 'Krishi Bhavan, New Delhi',
    experience: '35+ Years — Padma Shri Awardee, Plant Genetics & Molecular Biology',
    accentColor: '#16a34a',
    available: 'Mon–Fri, 10 AM – 4 PM (via ICAR Office)',
    tags: ['Crop Science', 'Rice', 'Genomics', 'Policy'],
  },
  {
    id: 3,
    name: 'IARI Plant Protection Helpline',
    designation: 'Indian Agricultural Research Institute — Division of Plant Pathology',
    specialty: 'Plant Disease Diagnosis, Fungal Infections, Blight, Wilt & Rust Control',
    phone: '+911125843375',
    whatsapp: '911125841490',
    photo: 'https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=300&h=300&q=80',
    location: 'IARI Campus, Pusa Road, New Delhi 110012',
    experience: 'India\'s Premier Agri-Research Institute — Est. 1905',
    accentColor: '#ef4444',
    available: 'Mon–Sat, 9:30 AM – 5 PM',
    tags: ['Plant Disease', 'Fungal', 'Blight', 'Wilt'],
  },
  {
    id: 4,
    name: 'Prof. PJNR Agricultural University',
    designation: 'PJTSAU Extension Services — Rajendranagar, Hyderabad',
    specialty: 'Telangana Crops, Soil Health, Cotton, Rice, Chilli & Turmeric Farming',
    phone: '+914024015011',
    whatsapp: '914024015011',
    photo: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=300&h=300&q=80',
    location: 'Rajendranagar, Hyderabad, Telangana',
    experience: 'State Agricultural University — Serving Telangana Farmers Since 1964',
    accentColor: '#3b82f6',
    available: 'Mon–Fri, 10 AM – 5 PM',
    tags: ['Telangana', 'Cotton', 'Rice', 'Chilli'],
  },
  {
    id: 5,
    name: 'Dr. Mangala Rai',
    designation: 'Former Secretary — DARE, Ministry of Agriculture',
    specialty: 'Agricultural Research, Biotechnology, Plant Breeding, Food Security',
    phone: '+911123382629',
    whatsapp: '911123382629',
    photo: 'https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=300&h=300&q=80',
    location: 'Department of Agricultural Research, New Delhi',
    experience: '40+ Years — Padma Bhushan Awardee, Crop Improvement Pioneer',
    accentColor: '#8b5cf6',
    available: 'Mon–Fri, 10 AM – 4 PM (via DARE Office)',
    tags: ['Biotech', 'Breeding', 'Food Security'],
  },
  {
    id: 6,
    name: 'TNAU Farmer Helpline',
    designation: 'Tamil Nadu Agricultural University — Extension Centre',
    specialty: 'IPM, Pest Control, Bio-Pesticides, Coconut, Banana & Paddy Diseases',
    phone: '+914222431405',
    whatsapp: '914222431405',
    photo: 'https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?auto=format&fit=crop&w=300&h=300&q=80',
    location: 'TNAU Campus, Coimbatore, Tamil Nadu 641003',
    experience: 'Leading State Agri University — Serving Tamil Nadu Farmers',
    accentColor: '#10b981',
    available: 'Mon–Sat, 9 AM – 5 PM',
    tags: ['Pest Control', 'IPM', 'Coconut', 'Paddy'],
  },
  {
    id: 7,
    name: 'NBSS & LUP Soil Helpline',
    designation: 'National Bureau of Soil Survey & Land Use Planning, Nagpur',
    specialty: 'Soil Health Cards, NPK Analysis, Soil Mapping, Organic Farming',
    phone: '+917122500386',
    whatsapp: '917122500386',
    photo: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=300&h=300&q=80',
    location: 'Seminary Hills, Nagpur, Maharashtra 440010',
    experience: 'ICAR Institute — India\'s Soil Mapping & Fertility Authority',
    accentColor: '#d97706',
    available: 'Mon–Fri, 10 AM – 5 PM',
    tags: ['Soil Health', 'NPK', 'Organic', 'Mapping'],
  },
  {
    id: 8,
    name: 'e-NAM Mandi Helpline',
    designation: 'National Agriculture Market — Ministry of Agriculture',
    specialty: 'Live Mandi Prices, Online Crop Trading, APMC Regulations, eNAM Registration',
    phone: '18002700224',
    whatsapp: null,
    photo: 'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=300&h=300&q=80',
    location: 'Pan India — Toll Free',
    experience: 'Official e-NAM Platform — 1000+ Mandis Connected Digitally',
    accentColor: '#06b6d4',
    available: 'Mon–Sat, 8 AM – 8 PM',
    tags: ['Mandi Prices', 'Trading', 'Toll-Free', 'eNAM'],
  },
];

function renderExpertCard(expert, index) {
  const delay = index * 0.08;
  const phoneClean = expert.phone.replace(/[^0-9+]/g, '');

  return `
    <div class="expert-card" style="animation-delay:${delay}s; --expert-accent: ${expert.accentColor};" id="expert-${expert.id}">
      <div class="expert-card-glow"></div>
      <div class="expert-card-inner">
        <div class="expert-header">
          <div class="expert-avatar-photo" style="border-color: ${expert.accentColor};">
            <img src="${expert.photo}" alt="${expert.name}" loading="lazy" />
          </div>
          <div class="expert-info">
            <h3 class="expert-name">${expert.name}</h3>
            <p class="expert-designation">${expert.designation}</p>
          </div>
        </div>

        <div class="expert-tags">
          ${expert.tags.map(tag => `<span class="expert-tag" style="border-color: ${expert.accentColor}44; color: ${expert.accentColor};">${tag}</span>`).join('')}
        </div>

        <div class="expert-details">
          <div class="expert-detail-row">
            <span class="expert-detail-icon">🎯</span>
            <span class="expert-detail-text">${expert.specialty}</span>
          </div>
          <div class="expert-detail-row">
            <span class="expert-detail-icon">📍</span>
            <span class="expert-detail-text">${expert.location}</span>
          </div>
          <div class="expert-detail-row">
            <span class="expert-detail-icon">⭐</span>
            <span class="expert-detail-text">${expert.experience}</span>
          </div>
          <div class="expert-detail-row">
            <span class="expert-detail-icon">🕐</span>
            <span class="expert-detail-text available-text">${expert.available}</span>
          </div>
        </div>

        <div class="expert-actions">
          <a href="tel:${phoneClean}" class="expert-btn expert-btn-call">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
            ${t('expert_call')}
          </a>
          ${expert.whatsapp ? `
            <a href="https://wa.me/${expert.whatsapp}?text=${encodeURIComponent('Hello, I am a farmer using AgriConnect app. I need help with: ')}" target="_blank" rel="noopener noreferrer" class="expert-btn expert-btn-whatsapp">
              <svg width="18" height="18" fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51a12.8 12.8 0 0 0-.57-.01c-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/></svg>
              ${t('expert_whatsapp')}
            </a>
          ` : `
            <span class="expert-btn expert-btn-callonly">
              📞 Call Only
            </span>
          `}
        </div>
      </div>
    </div>
  `;
}

export function renderExperts() {
  return `
    <div class="page-section experts-page">
      <div class="page-header">
        <h1>${t('experts_title')}</h1>
        <p>${t('experts_desc')}</p>
      </div>

      <!-- Emergency Hotline Banner -->
      <div class="expert-emergency-banner">
        <div class="expert-emergency-pulse"></div>
        <div class="expert-emergency-content">
          <div class="expert-emergency-left">
            <span class="expert-emergency-icon">🚨</span>
            <div>
              <div class="expert-emergency-title">Kisan Call Centre — Toll Free 24/7</div>
              <div class="expert-emergency-subtitle">Dial <strong>1800-180-1551</strong> for immediate agricultural assistance in 22 languages</div>
            </div>
          </div>
          <a href="tel:18001801551" class="expert-emergency-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
            Call Now
          </a>
        </div>
      </div>

      <!-- Expert Cards Grid -->
      <div class="experts-grid">
        ${expertsData.map((e, i) => renderExpertCard(e, i)).join('')}
      </div>

      <!-- Disclaimer -->
      <div class="expert-disclaimer">
        <div class="expert-disclaimer-icon">ℹ️</div>
        <div>
          <strong>Note:</strong> These are publicly available institutional helpline numbers and government office contacts. AgriConnect does not charge any consultation fees. Standard call/messaging rates may apply. Toll-free numbers (1800-xxx) are free from all networks. WhatsApp messages will open in a new tab.
        </div>
      </div>
    </div>
  `;
}

export function initExperts() {
  const cards = document.querySelectorAll('.expert-card');
  cards.forEach((card, i) => {
    card.style.animationDelay = `${i * 0.08}s`;
  });
}
