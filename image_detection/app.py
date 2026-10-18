import os
import tensorflow as tf
import numpy as np
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import gc
from upload_validation import validate_image_upload, unique_upload_path

# Memory optimizations for Render Free Tier (512MB RAM)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reduce tf logging
tf.config.threading.set_inter_op_parallelism_threads(1)
tf.config.threading.set_intra_op_parallelism_threads(1)
try:
    tf.config.set_visible_devices([], 'GPU') # CPU only
except:
    pass

app = Flask(__name__)


def get_allowed_origins():
    """
    Resolve allowed CORS origins from environment variables.
    Supports ALLOWED_ORIGINS (comma-separated list) and FRONTEND_URL.
    In development, safely permits localhost and 127.0.0.1 development ports by default.
    In production, strictly restricts to configured domains.
    """
    default_dev_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:5001",
        "http://127.0.0.1:5001",
    ]
    env_allowed = os.getenv("ALLOWED_ORIGINS", "").strip()
    frontend_url = os.getenv("FRONTEND_URL", "").strip()
    is_prod = os.getenv("FLASK_ENV", "").lower() == "production"

    origins = []
    if env_allowed:
        origins.extend([o.strip() for o in env_allowed.split(",") if o.strip()])
    if frontend_url and frontend_url not in origins:
        origins.append(frontend_url)

    if not is_prod:
        for dev_origin in default_dev_origins:
            if dev_origin not in origins:
                origins.append(dev_origin)
    elif not origins:
        app.logger.warning(
            "FLASK_ENV=production but no ALLOWED_ORIGINS or FRONTEND_URL configured; "
            "CORS will reject all cross-origin requests until configured."
        )
        return []

    return origins


CORS(app, origins=get_allowed_origins())
MAX_IMAGE_BYTES = 5 * 1024 * 1024
app.config['MAX_CONTENT_LENGTH'] = MAX_IMAGE_BYTES
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"status": "error", "error": "Image exceeds the 5 MB upload limit."}), 413

print("Loading AI Model...")
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'potato_disease_model.keras')
model = tf.keras.models.load_model(MODEL_PATH)
CLASS_NAMES = ['Potato___Early_blight', 'Potato___Late_blight', 'Potato___healthy']

# Expert-Reviewed Agricultural Database (Responsible Agronomic Guidance)
TREATMENTS = {
    'Potato___Early_blight': {
        'en': {
            "name": "Early Blight",
            "crop": "Potato (Solanum tuberosum)",
            "symptoms": "Concentric dark brown to black rings ('target-board' spots) on older leaves. Foliage surrounding lesions may turn yellow.",
            "prevention": "Ensure adequate plant spacing for canopy ventilation, practice 2-3 year rotation with non-solanaceous crops, and avoid overhead sprinkler wetting.",
            "next_steps": "Scout lower canopy to measure spread. Remove heavily spotted bottom leaves. Have field symptoms verified by a local KVK officer or agronomist.",
            "med": "Protective fungicides (e.g. Mancozeb or Chlorothalonil) may be considered if recommended by local extension advisories. Follow product label instructions and local safety intervals strictly. Do not apply unverified chemical dosages.",
            "plan": "Improve field drainage and canopy airflow. Confirm symptoms with local agricultural extension officers before applying approved label treatments."
        },
        'te': {
            "name": "ముందస్తు ఆకుమచ్చ తెగులు",
            "crop": "బంగాళాదుంప (సోలనం ట్యూబరోసమ్)",
            "symptoms": "దిగువ ముదిరిన ఆకులపై వలయాకారపు గోధుమ లేదా నల్లటి మచ్చలు (టార్గెట్ బోర్డ్ ఆకారం). మచ్చ చుట్టూ ఆకు పసుపు రంగులోకి మారవచ్చు.",
            "prevention": "మొక్కల మధ్య సరైన గాలి ఆడేలా దూరం పాటించండి, 2-3 సంవత్సరాల పంట మార్పిడి చేయండి, ఆకులపై నీరు నిలవకుండా డ్రిప్ పద్ధతి వాడండి.",
            "next_steps": "పొలంలో తెగులు తీవ్రతను పరిశీలించండి. తీవ్రంగా దెబ్బతిన్న దిగువ ఆకులను తొలగించండి. స్థానిక కేవీకే అధికారి లేదా వ్యవసాయ విస్తరణ అధికారితో నిర్ధారించండి.",
            "med": "స్థానిక వ్యవసాయాధికారి సిఫార్సు చేస్తే మాంకోజెబ్ లేదా క్లోరోథలోనిల్ వంటి శిలీంద్ర సంహారిణులను లేబుల్ సూచనల ప్రకారం మాత్రమే ఉపయోగించండి. సొంతంగా రసాయన మోతాదులు నిర్ణయించవద్దు.",
            "plan": "పొలంలో గాలి బాగా ఆడేలా చూడండి. రసాయన చికిత్సలు చేసే ముందు స్థానిక వ్యవసాయ విస్తరణ అధికారి సలహా తీసుకోండి."
        },
        'hi': {
            "name": "अगेती झुलसा",
            "crop": "आलू (सोलेनम ट्यूबरोसम)",
            "symptoms": "निचली पुरानी पत्तियों पर संकेंद्रित छल्लों (टारगेट-बोर्ड) जैसे भूरे-काले धब्बे। धब्बों के चारों ओर पत्ती पीली पड़ सकती है।",
            "prevention": "पौधों के बीच हवा के प्रवाह के लिए उचित दूरी रखें, 2-3 वर्ष का फसल चक्र अपनाएं, पत्तियों पर सीधे पानी के छिड़काव से बचें।",
            "next_steps": "खेत में संक्रमण की गंभीरता का निरीक्षण करें। अत्यधिक प्रभावित निचली पत्तियों को हटा दें। स्थानीय केवीके (KVK) विशेषज्ञ से पुष्टि कराएं।",
            "med": "स्थानीय कृषि अधिकारी की सलाह पर मैंकोजेब या क्लोरोथालोनिल कवकनाशी का उपयोग किया जा सकता है। उत्पाद लेबल पर लिखे निर्देशों और सुरक्षा नियमों का पालन करें। मनमाने डोज का प्रयोग न करें।",
            "plan": "हवा का प्रवाह सुनिश्चित करें और जल निकासी सुधारें। रासायनिक उपचार से पहले स्थानीय केवीके या कृषि विस्तार अधिकारी से परामर्श लें।"
        },
        'mr': {
            "name": "करपा (Early Blight)",
            "crop": "बटाटा",
            "symptoms": "खालील जुन्या पानांवर गोलाकार वलयाकार काळे-तपकिरी ठिपके दिसतात.",
            "prevention": "झाडांमध्ये हवा खेळती राहील असे अंतर ठेवा, पीक फेरपालट करा, तुषार सिंचन टाळा.",
            "next_steps": "रोगाची तीव्रता तपासा. रोगट पाने काढून शेताबाहेर नष्ट करा. स्थानिक कृषी विज्ञान केंद्राचा सल्ला घ्या.",
            "med": "कृषी तज्ज्ञांच्या सल्ल्याने मॅन्कोझेब किंवा क्लोरोथालोनिल फवारणी लेबल निर्देशांनुसार करावी.",
            "plan": "हवा खेळती राहील याची काळजी घ्या आणि कृषी अधिकाऱ्यांशी संपर्क साधा."
        }
    },
    'Potato___Late_blight': {
        'en': {
            "name": "Late Blight",
            "crop": "Potato (Solanum tuberosum)",
            "symptoms": "Water-soaked, pale to dark green lesions turning purplish-black rapidly under cool, humid conditions. White downy mold visible on leaf undersides in high humidity.",
            "prevention": "Plant certified disease-free seed tubers, ensure good hilling/earthing-up to protect tubers, and avoid persistent canopy wetness.",
            "next_steps": "Monitor local weather forecasts for cool, rainy conditions. Contact local KVK extension officers as soon as possible for area-specific disease alerts and guidance.",
            "med": "Copper-based fungicides or registered systemic formulations (e.g. Cymoxanil combinations) may be recommended by local authorities during high-risk conditions. Apply strictly according to manufacturer label directions and harvest intervals. Do not apply unverified chemical dosages.",
            "plan": "Field confirmation required. Protect tubers with proper earthing-up, reduce canopy moisture, and consult extension guidance for approved label treatments."
        },
        'te': {
            "name": "ముదిరిన ఆకుమాడు తెగులు",
            "crop": "బంగాళాదుంప (సోలనం ట్యూబరోసమ్)",
            "symptoms": "చల్లని, తేమ వాతావరణంలో త్వరగా వ్యాపించే నీటి మచ్చలు, నలుపు-గోధుమ రంగులోకి మారడం. అధిక తేమ ఉన్నప్పుడు ఆకు కింద తెల్లటి బూజు లాంటి పెరుగుదల కనిపిస్తుంది.",
            "prevention": "ధృవీకరించిన విత్తన దుంపలను వాడండి, దుంపలను రక్షించడానికి మట్టిని గట్టుగా ఎత్తండి మరియు ఆకులపై ఎక్కువసేపు నీరు నిలవకుండా చూడండి.",
            "next_steps": "వాతావరణాన్ని గమనించండి. ప్రాంతీయ నిర్దిష్ట సలహా కోసం వీలైనంత త్వరగా స్థానిక కేవీకే లేదా వ్యవసాయ విస్తరణ అధికారులను సంప్రదించండి. సమగ్ర తెగులు యాజమాన్య పద్ధతులను పాటించండి.",
            "med": "అధిక ప్రమాదకర వాతావరణంలో రాగి ఆధారిత లేదా సైమోక్సానిల్ సంయోగ శిలీంద్ర సంహారిణులను స్థానిక అధికారుల సలహా మేరకు మాత్రమే లేబుల్ సూచనల ప్రకారం వాడండి. ధృవీకరించని రసాయన మోతాదులను ఉపయోగించవద్దు.",
            "plan": "స్థానిక వ్యవసాయాధికారితో లక్షణాలను నిర్ధారించండి. దుంపలను రక్షించడానికి మట్టిని గట్టుగా పోయండి మరియు లేబుల్ సూచనల ప్రకారం మాత్రమే మందులు వాడండి."
        },
        'hi': {
            "name": "पछेती झुलसा",
            "crop": "आलू (सोलेनम ट्यूबरोसम)",
            "symptoms": "ठंडे व नम मौसम में तेजी से फैलने वाले पानी जैसे धब्बे जो बैंगनी-काले हो जाते हैं। अधिक नमी में पत्ती की निचली सतह पर सफेद फफूंद दिखाई देती है।",
            "prevention": "प्रमाणित रोगमुक्त बीज कंदों का उपयोग करें, पत्तियों पर पानी जमा न होने दें, पंक्तियों में उचित दूरी रखें और कंदों को अच्छी तरह ढककर रखें।",
            "next_steps": "मौसम पर नजर रखें। क्षेत्र-विशेष सलाह के लिए जल्द से जल्द स्थानीय केवीके या कृषि विस्तार अधिकारी से संपर्क करें।",
            "med": "जोखिम की स्थिति में कॉपर युक्त कवकनाशी या सिमोक्सानिल संयोजन की सिफारिश स्थानीय विशेषज्ञों द्वारा की जा सकती है। केवल लेबल निर्देशों के अनुसार ही प्रयोग करें।",
            "plan": "खेत में लक्षणों की पुष्टि स्थानीय कृषि अधिकारी से कराएं। कंदों को ढकें, नमी नियंत्रित करें और लेबल-अनुमोदित उपचार ही लें।"
        },
        'mr': {
            "name": "उशिरा येणारा करपा",
            "crop": "बटाटा",
            "symptoms": "थंड आणि दमट हवेत काळे-जांभळे डाग पडतात व पानाच्या खाली पांढरी बुरशी दिसते.",
            "prevention": "प्रमाणित बियाणे वापरा, शेतात पाणी साचू देऊ नका, झाडांना भर द्या.",
            "next_steps": "हवामानावर लक्ष ठेवा आणि तातडीने स्थानिक कृषी विज्ञान केंद्राचा सल्ला घ्या.",
            "med": "स्थानिक तज्ञांच्या मार्गदर्शनाखाली कॉपरयुक्त किंवा सायमोक्सॅनिल बुरशीनाशकांचा लेबल निर्देशांनुसार वापर करा.",
            "plan": "कृषी अधिकाऱ्यांकडून रोगाची खात्री करून घ्या आणि प्रमाणित लेबल मार्गदर्शक तत्त्वांचे पालन करा."
        }
    },
    'Potato___healthy': {
        'en': {
            "name": "Healthy",
            "crop": "Potato (Solanum tuberosum)",
            "symptoms": "No characteristic foliar lesions, necrotic spots, or blight margins detected by the model on this leaf.",
            "prevention": "Maintain balanced crop nutrition, weed sanitation, regular field scouting, and proper irrigation scheduling.",
            "next_steps": "Continue routine scouting across different canopy layers. Model screening of a single leaf does not guarantee total crop health.",
            "med": "None required. Routine preventive chemical sprays should only be applied if recommended by local pest surveillance advisories.",
            "plan": "Plant leaf appears healthy. Continue standard agronomic care and regular monitoring."
        },
        'te': {
            "name": "ఆరోగ్యకరమైనది",
            "crop": "బంగాళాదుంప (సోలనం ట్యూబరోసమ్)",
            "symptoms": "ఈ ఆకుపై ఎలాంటి మచ్చలు లేదా తెగులు లక్షణాలు మోడల్‌కు కనిపించలేదు.",
            "prevention": "సిఫార్సు చేసిన సమతుల్య పోషకాలను అందించండి, కలుపు నివారించండి, క్రమం తప్పకుండా పొలాన్ని తనిఖీ చేయండి.",
            "next_steps": "పొలంలోని ఇతర భాగాలను కూడా పరిశీలిస్తూ ఉండండి. ఒకే ఆకు పరీక్ష మొత్తం పంట ఆరోగ్యాన్ని నిర్ధారించలేదు.",
            "med": "రసాయన మందులు అవసరం లేదు. స్థానిక నిఘా సూచనలు ఉంటే తప్ప నివారణ మందులు వాడవద్దు.",
            "plan": "మొక్క ఆరోగ్యంగా ఉంది. ఎప్పటిలాగే క్రమం తప్పకుండా నీరు, ఎరువులు వేస్తూ పర్యవేక్షించండి."
        },
        'hi': {
            "name": "स्वस्थ",
            "crop": "आलू (सोलेनम ट्यूबरोसम)",
            "symptoms": "पत्ती पर कोई विशिष्ट धब्बे या झुलसा के लक्षण मॉडल द्वारा नहीं पाए गए।",
            "prevention": "संतुलित पोषण, खरपतवार नियंत्रण, नियमित निगरानी और उचित सिंचाई व्यवस्था बनाए रखें।",
            "next_steps": "खेत में नियमित निगरानी जारी रखें। केवल एक पत्ती की जांच से पूरे खेत के रोगमुक्त होने की पुष्टि नहीं होती।",
            "med": "किसी रासायनिक दवा की आवश्यकता नहीं है। केवल स्थानीय सलाह होने पर ही निवारक उपाय करें।",
            "plan": "पौधा स्वस्थ दिखता है। सामान्य देखभाल और नियमित निरीक्षण जारी रखें।"
        },
        'mr': {
            "name": "निरोगी",
            "crop": "बटाटा",
            "symptoms": "पानावर कोणताही करपा किंवा रोगाची लक्षणे आढळली नाहीत.",
            "prevention": "संतुलित खते द्या, तण नियंत्रण करा आणि नियमित पाहणी करा.",
            "next_steps": "शेताचे नियमित निरीक्षण चालू ठेवा. एका पानावरून पूर्ण पीक निरोगी असल्याची खात्री होत नाही.",
            "med": "कोणत्याही औषधाची गरज नाही.",
            "plan": "रोप निरोगी आहे. नेहमीप्रमाणे काळजी घ्या."
        }
    }
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def predict_disease():
    file = request.files.get('file')
    lang = request.form.get('language', 'en')
    if lang not in {'en', 'te', 'hi', 'mr'}:
        lang = 'en'

    if not file:
        return jsonify({"status": "error", "error": "Image file is required."}), 400

    extension, validation_error = validate_image_upload(
        file.filename, request.content_length, MAX_IMAGE_BYTES
    )
    if validation_error:
        return jsonify({"status": "error", "error": validation_error}), 400

    filepath = unique_upload_path(app.config['UPLOAD_FOLDER'], extension)
    try:
        file.save(filepath)
        try:
            raw = tf.io.read_file(filepath)
            img = tf.io.decode_image(raw, channels=3, expand_animations=False)
            img = tf.image.resize(img, (224, 224))
            img_array = tf.expand_dims(img, 0)
        except Exception:
            return jsonify({"status": "error", "error": "The uploaded file is not a readable image."}), 400

        predictions = model(img_array, training=False).numpy()[0]
        max_conf = float(np.max(predictions))
        
        # If the model is not confident, it's likely not a potato leaf
        if max_conf < 0.65:
            return jsonify({
                "status": "success",
                "is_recognized": False,
                "error": "Image not recognized as a supported leaf or disease.",
            })

        idx = np.argmax(predictions)
        res_class = CLASS_NAMES[idx]
        
        # Get data for selected language
        diag = TREATMENTS[res_class][lang]
        
        scores = []
        for i, s in enumerate(predictions):
            scores.append({"name": TREATMENTS[CLASS_NAMES[i]][lang]["name"], "conf": round(float(s*100), 2)})

        # Release per-request tensors; keep the loaded model available to later requests.
        del img_array, img, predictions
        gc.collect()
        return jsonify({
            "status": "success",
            "is_recognized": True,
            "is_healthy": res_class == 'Potato___healthy',
            "diagnosis": diag,
            "all_scores": sorted(scores, key=lambda x: x['conf'], reverse=True)
        })
    finally:
        try:
            os.remove(filepath)
        except FileNotFoundError:
            pass


@app.errorhandler(500)
def handle_internal_error(e):
    return jsonify({"status": "error", "error": "Internal server error occurred while processing image."}), 500


if __name__ == '__main__':
    debug_enabled = (
        os.getenv('FLASK_DEBUG', 'false').strip().lower() == 'true'
        and os.getenv('FLASK_ENV', '').strip().lower() == 'development'
    )
    app.run(debug=debug_enabled, port=5001)
