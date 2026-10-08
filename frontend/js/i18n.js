// ============================================================
// Agri-Connect i18n — English + Telugu Full Translation
// ============================================================

let lang = 'en';
const listeners = [];

const strings = {
  en: {
    // Navbar
    nav_home: 'Home',
    nav_analyzer: 'Analyzer',
    nav_weather: 'Weather',
    nav_market: 'Market',
    nav_cropDoctor: 'Crop Doctor',
    nav_chatbot: 'Chatbot',
    nav_alerts: 'Alerts',
    nav_experts: 'Experts',

    // Common
    loading: 'Loading...',
    error_gps: 'GPS not available',
    fetch_live: 'Fetch Live Prices',
    search: 'Search',
    back: '← Back',
    next: 'Next →',
    submit: 'Submit',
    cancel: 'Cancel',

    // Home page
    hero_badge: '🛰️ GPS · Satellite Soil · Live Weather Data',
    hero_title_1: "Smart Farming",
    hero_title_2: 'Made Simple',
    hero_title_3: 'For Every Farmer',
    hero_subtitle: 'Get accurate crop recommendations, market prices, and weather forecasts — powered by satellite soil data and your GPS location.',
    hero_cta_analyze: '🌱 Analyze My Farm',
    hero_cta_weather: '🌤️ Live Weather',
    hero_cta_doctor: '🔬 Crop Doctor',
    feature_crop_rec: 'Crop Recommendation',
    feature_crop_rec_desc: 'Top 3 crops ranked by suitability score using your soil NPK, pH, and live weather conditions.',
    feature_soil: 'Live Soil Data',
    feature_soil_desc: 'Satellite soil analysis by GPS coordinates — clay, sand, pH, organic carbon, N/P/K values for your field.',
    feature_weather: 'GPS Weather',
    feature_weather_desc: 'Live weather by your exact GPS location. 5-day forecast with farming advisories.',
    feature_fert: 'Fertilizer Guide',
    feature_fert_desc: 'Stage-wise application plan, nutrient deficiency summary, organic alternatives, and safety warnings.',
    feature_doctor: 'Crop Doctor',
    feature_doctor_desc: 'Upload a leaf photo for instant disease detection with treatment recommendations.',
    feature_market: 'Market Prices',
    feature_market_desc: 'Mandi price lookup by crop and location. Find the best-paying market near you.',
    feature_chatbot: 'Farm Assistant',
    feature_chatbot_desc: 'Ask farming questions in English or Telugu and get instant, practical advice.',
    feature_alerts: 'Alert Engine',
    feature_alerts_desc: 'Automated alerts from weather, satellite NDVI, news, and crop calendars.',
    data_sources: 'Data Sources',

    // Analyzer
    analyzer_title: '🌱 Farm Intelligence Analyzer',
    analyzer_desc: 'Accurate crop and fertilizer recommendations using live GPS, satellite soil data, and weather',
    step_location: 'Location',
    step_farm: 'Farm Details',
    step_soil: 'Soil',
    step_results: 'Results',
    farm_location: '📍 Farm Location',
    gps_note: 'Use GPS for the most accurate results. Weather and soil data are fetched by coordinates.',
    capture_gps: '📡 Capture My Farm Location (GPS)',
    or_manual: '— or enter manually —',
    latitude: 'Latitude',
    longitude: 'Longitude',
    land_area: 'Land Area',
    farmer_name: 'Farmer Name',
    next_farm_details: 'Next: Farm Details →',

    // Farm details
    previous_crop: 'Previous Crop',
    season_to_plant: 'Season to Plant',
    irrigation_type: 'Irrigation Type',
    region: 'Region',
    prev_fertilizer: 'Previous Fertilizer Used',
    prev_pesticide: 'Previous Pesticide Used',
    last_yield: 'Last Season Yield',
    annual_rainfall: 'Annual Rainfall',

    // Soil
    soil_data: '🧪 Soil Data',
    auto_fetch_soil: '🛰️ Auto-Fetch Satellite Soil Data',
    fetch_soil_btn: '📡 Fetch Soil Data',
    soil_type: 'Soil Type',
    ph_level: 'pH Level',
    nitrogen: 'Nitrogen (N)',
    phosphorus: 'Phosphorus (P)',
    potassium: 'Potassium (K)',
    moisture: 'Soil Moisture',
    organic_carbon: 'Organic Carbon',
    analyze_now: '🔍 Analyze Farm Now',

    // Results
    top_crops: '🌾 Top Crop Recommendations',
    sow: 'Sow',
    harvest: 'Harvest',
    profit_est: 'Profit est.',
    location_weather: '📍 Location & Live Weather',
    soil_profile: '🧪 Soil Profile',
    irrigation_guidance: '💧 Irrigation Guidance',
    fert_recommendation: '🧬 Fertilizer Recommendation',
    all_feasible: '🌿 All Feasible Crops',
    new_analysis: '🔄 Start New Analysis',

    // Weather
    weather_title: '🌤️ Live Weather & Forecast',
    weather_desc: 'Real-time weather data from OpenWeatherMap by GPS coordinates',
    load_weather: '📡 Load Weather for My Location',
    temperature: 'Temperature',
    humidity: 'Humidity',
    wind: 'Wind',
    five_day: '5-Day Forecast',

    // Market
    market_title: '📊 Live Mandi Market Prices',
    market_desc: 'Latest wholesale mandi prices across India',
    market_search: '🔍 Search Live Mandi Prices',
    commodity: 'Commodity / Crop',
    state: 'State',
    district: 'District',
    fetch_prices: '📡 Fetch Live Prices',
    avg_price: 'Avg Price',
    highest_price: 'Highest Price',
    lowest_price: 'Lowest Price',
    markets_reporting: 'Markets',
    best_market: '🏆 Best Market Today',

    // Chatbot
    chat_title: '💬 Farm Assistant',
    chat_desc: 'Ask farming questions in English or Telugu. Get instant, accurate advice.',
    chat_placeholder: 'Ask your farming question...',
    quick_questions: '💡 Quick Questions',
    chat_help: '🌐 I can help with',

    // Alerts
    alerts_title: '🚨 Farm Alert Center',
    alerts_desc: 'Live alerts from weather, soil, satellite NDVI, agriculture news, and crop calendars',
    current_crop: 'Current Crop',
    season: 'Season',
    load_alerts: '📡 Load Alerts for My GPS Location',
    agri_news: '📰 Agriculture News',
    load_news: '📡 Load Latest Agriculture News',

    // Crop Doctor
    doctor_title: '🔬 Crop Disease Detection',
    doctor_desc: 'Upload a leaf photo for instant disease identification and treatment advice',
    upload_image: 'Upload Leaf Image',
    detect: '🔬 Detect Disease',

    // Experts
    experts_title: '👨‍🌾 Contact Agriculture Experts',
    experts_desc: 'Connect directly with certified agronomists and plant pathologists for professional advice.',
    expert_call: 'Call Now',
    expert_whatsapp: 'WhatsApp',
    expert_specialty: 'Specialty: ',
  },
  te: {
    // Navbar
    nav_home: 'హోమ్',
    nav_analyzer: 'విశ్లేషకుడు',
    nav_weather: 'వాతావరణం',
    nav_market: 'మార్కెట్',
    nav_cropDoctor: 'పంట వైద్యుడు',
    nav_chatbot: 'చాట్‌బాట్',
    nav_alerts: 'హెచ్చరికలు',
    nav_experts: 'నిపుణులు',

    // Common
    loading: 'లోడ్ అవుతోంది...',
    error_gps: 'GPS అందుబాటులో లేదు',
    fetch_live: 'లైవ్ ధరలు పొందండి',
    search: 'శోధించండి',
    back: '← వెనుకకు',
    next: 'తదుపరి →',
    submit: 'సమర్పించండి',
    cancel: 'రద్దు',

    // Home page
    hero_badge: '🛰️ GPS · ఉపగ్రహ నేల · వాతావరణ డేటా',
    hero_title_1: 'తెలివైన వ్యవసాయం',
    hero_title_2: 'సులభంగా',
    hero_title_3: 'ప్రతి రైతు కోసం',
    hero_subtitle: 'మీ GPS స్థానం, ఉపగ్రహ నేల డేటా మరియు వాతావరణ అంచనాల ఆధారంగా ఖచ్చితమైన పంట సిఫారసులు.',
    hero_cta_analyze: '🌱 నా పొలాన్ని విశ్లేషించండి',
    hero_cta_weather: '🌤️ ప్రత్యక్ష వాతావరణం',
    hero_cta_doctor: '🔬 పంట వైద్యుడు',
    feature_crop_rec: 'పంట సిఫారసు',
    feature_crop_rec_desc: 'మీ పొలం పరిస్థితుల ఆధారంగా టాప్ 3 పంటలు, అనుకూలత స్కోర్లు, విత్తనం నెలలు మరియు లాభం అంచనాలు.',
    feature_soil: 'ప్రత్యక్ష నేల డేటా',
    feature_soil_desc: 'GPS కోఆర్డినేట్ల ద్వారా ఉపగ్రహ నేల విశ్లేషణ — క్లే, ఇసుక, pH, N/P/K.',
    feature_weather: 'GPS వాతావరణం',
    feature_weather_desc: 'మీ GPS స్థానం ద్వారా ప్రత్యక్ష వాతావరణం. 5-రోజుల అంచనా.',
    feature_fert: 'ఎరువుల గైడ్',
    feature_fert_desc: 'దశల వారీగా అమలు ప్రణాళిక, పోషక లోపం సారాంశం, సేంద్రీయ ప్రత్యామ్నాయాలు.',
    feature_doctor: 'పంట వైద్యుడు',
    feature_doctor_desc: 'వ్యాధి నిర్ధారణ కోసం ఆకు ఫోటో అప్‌లోడ్ చేయండి.',
    feature_market: 'మార్కెట్ ధరలు',
    feature_market_desc: 'పంట మరియు స్థానం ద్వారా మండి ధరల శోధన.',
    feature_chatbot: 'పొలం సహాయకుడు',
    feature_chatbot_desc: 'ఇంగ్లీష్ లేదా తెలుగులో వ్యవసాయ ప్రశ్నలు అడగండి. ఆచరణాత్మక సలహా పొందండి.',
    feature_alerts: 'హెచ్చరిక ఇంజిన్',
    feature_alerts_desc: 'వాతావరణం, ఉపగ్రహ, వార్తలు మరియు పంట క్యాలెండర్ల నుండి స్వయంచాలక హెచ్చరికలు.',
    data_sources: 'డేటా సోర్సులు',

    // Analyzer
    analyzer_title: '🌱 పొలం బుద్ధిమత్తా విశ్లేషకుడు',
    analyzer_desc: 'ప్రత్యక్ష GPS, నిజమైన నేల డేటా మరియు ప్రత్యక్ష వాతావరణాన్ని ఉపయోగించి పంట మరియు ఎరువుల సిఫారసులు',
    step_location: 'స్థానం',
    step_farm: 'పొలం వివరాలు',
    step_soil: 'నేల',
    step_results: 'ఫలితాలు',
    farm_location: '📍 పొలం స్థానం',
    gps_note: 'అత్యంత ఖచ్చితమైన ఫలితాల కోసం GPS ఉపయోగించండి.',
    capture_gps: '📡 నా పొలం స్థానాన్ని క్యాప్చర్ చేయండి (GPS)',
    or_manual: '— లేదా మానవీయంగా నమోదు చేయండి —',
    latitude: 'అక్షాంశం',
    longitude: 'రేఖాంశం',
    land_area: 'భూమి విస్తీర్ణం',
    farmer_name: 'రైతు పేరు',
    next_farm_details: 'తదుపరి: పొలం వివరాలు →',

    // Farm details
    previous_crop: 'మునుపటి పంట',
    season_to_plant: 'నాటేందుకు సీజన్',
    irrigation_type: 'నీటిపారుదల రకం',
    region: 'ప్రాంతం',
    prev_fertilizer: 'మునుపటి ఎరువు',
    prev_pesticide: 'మునుపటి పురుగుమందు',
    last_yield: 'గత సీజన్ దిగుబడి',
    annual_rainfall: 'వార్షిక వర్షపాతం',

    // Soil
    soil_data: '🧪 నేల డేటా',
    auto_fetch_soil: '🛰️ ఉపగ్రహ నేల డేటా ఆటో-ఫెచ్',
    fetch_soil_btn: '📡 నేల డేటా పొందండి',
    soil_type: 'నేల రకం',
    ph_level: 'pH స్థాయి',
    nitrogen: 'నత్రజని (N)',
    phosphorus: 'భాస్వరం (P)',
    potassium: 'పొటాషియం (K)',
    moisture: 'నేల తేమ',
    organic_carbon: 'కర్బన పదార్థం',
    analyze_now: '🔍 ఇప్పుడు పొలాన్ని విశ్లేషించండి',

    // Results
    top_crops: '🌾 టాప్ పంట సిఫారసులు',
    sow: 'విత్తడం',
    harvest: 'కోత',
    profit_est: 'లాభం అంచనా',
    location_weather: '📍 స్థానం & ప్రత్యక్ష వాతావరణం',
    soil_profile: '🧪 నేల ప్రొఫైల్',
    irrigation_guidance: '💧 నీటిపారుదల మార్గదర్శకత్వం',
    fert_recommendation: '🧬 ఎరువుల సిఫారసు',
    all_feasible: '🌿 అన్ని సాధ్యమైన పంటలు',
    new_analysis: '🔄 కొత్త విశ్లేషణ ప్రారంభించండి',

    // Weather
    weather_title: '🌤️ ప్రత్యక్ష వాతావరణం & అంచనా',
    weather_desc: 'GPS కోఆర్డినేట్ల ద్వారా OpenWeatherMap నుండి నిజ-సమయ వాతావరణ డేటా',
    load_weather: '📡 నా స్థానం కోసం వాతావరణం లోడ్ చేయండి',
    temperature: 'ఉష్ణోగ్రత',
    humidity: 'తేమ',
    wind: 'గాలి',
    five_day: '5-రోజుల అంచనా',

    // Market
    market_title: '📊 ప్రత్యక్ష మండి మార్కెట్ ధరలు',
    market_desc: 'భారతదేశం అంతటా తాజా మండి ధరలు',
    market_search: '🔍 ప్రత్యక్ష మండి ధరలు శోధించండి',
    commodity: 'వస్తువు / పంట',
    state: 'రాష్ట్రం',
    district: 'జిల్లా',
    fetch_prices: '📡 ప్రత్యక్ష ధరలు పొందండి',
    avg_price: 'సగటు ధర',
    highest_price: 'అత్యధిక ధర',
    lowest_price: 'అత్యల్ప ధర',
    markets_reporting: 'మార్కెట్లు',
    best_market: '🏆 నేటి అత్యుత్తమ మార్కెట్',

    // Chatbot
    chat_title: '💬 పొలం సహాయకుడు',
    chat_desc: 'ఇంగ్లీష్ లేదా తెలుగులో వ్యవసాయ ప్రశ్నలు అడగండి. తక్షణ, ఖచ్చితమైన సలహా పొందండి.',
    chat_placeholder: 'మీ వ్యవసాయ ప్రశ్న అడగండి...',
    quick_questions: '💡 త్వరిత ప్రశ్నలు',
    chat_help: '🌐 నేను సహాయం చేయగలను',

    // Alerts
    alerts_title: '🚨 పొలం హెచ్చరిక కేంద్రం',
    alerts_desc: 'వాతావరణం, నేల, ఉపగ్రహ NDVI, వ్యవసాయ వార్తలు మరియు పంట క్యాలెండర్ల నుండి ప్రత్యక్ష హెచ్చరికలు',
    current_crop: 'ప్రస్తుత పంట',
    season: 'సీజన్',
    load_alerts: '📡 నా GPS స్థానం కోసం హెచ్చరికలు లోడ్ చేయండి',
    agri_news: '📰 వ్యవసాయ వార్తలు',
    load_news: '📡 తాజా వ్యవసాయ వార్తలు లోడ్ చేయండి',

    // Crop Doctor
    doctor_title: '🔬 పంట వ్యాధి నిర్ధారణ',
    doctor_desc: 'వ్యాధి గుర్తింపు మరియు చికిత్స సలహా కోసం ఆకు ఫోటో అప్‌లోడ్ చేయండి',
    upload_image: 'ఆకు చిత్రాన్ని అప్‌లోడ్ చేయండి',
    detect: '🔬 వ్యాధిని కనుగొని',

    // Experts
    experts_title: '👨‍🌾 వ్యవసాయ నిపుణులను సంప్రదించండి',
    experts_desc: 'వృత్తిపరమైన సలహా కోసం సర్టిఫైడ్ వ్యవసాయ శాస్త్రవేత్తలు మరియు మొక్కల రోగ నిపుణులతో నేరుగా కనెక్ట్ అవ్వండి.',
    expert_call: 'ఇప్పుడే కాల్ చేయండి',
    expert_whatsapp: 'వాట్సాప్',
    expert_specialty: 'ప్రత్యేకత: ',
  }
};

export function t(key) {
  return strings[lang]?.[key] || strings.en[key] || key;
}

export function setLang(l) {
  lang = l;
  listeners.forEach(fn => fn(l));
}

export function getLang() { return lang; }

export function onLangChange(fn) {
  listeners.push(fn);
  window.addEventListener('langChange', (e) => {
    lang = e.detail;
    fn(lang);
  });
}
