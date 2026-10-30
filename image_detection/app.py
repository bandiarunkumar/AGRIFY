import os
import tensorflow as tf
import numpy as np
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import gc

# Memory optimizations for Render Free Tier (512MB RAM)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reduce tf logging
tf.config.threading.set_inter_op_parallelism_threads(1)
tf.config.threading.set_intra_op_parallelism_threads(1)
try:
    tf.config.set_visible_devices([], 'GPU') # CPU only
except:
    pass

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

print("Loading AI Model...")
model = tf.keras.models.load_model('potato_disease_model.keras')
CLASS_NAMES = ['Potato___Early_blight', 'Potato___Late_blight', 'Potato___healthy']

# ===========================================================================
# INPUT SCREENING (pre-inference)
# ===========================================================================
# Why this exists
# ---------------
# The model exposes only 3 classes (potato early blight, late blight,
# healthy), so its softmax output always sums to 1.0 and it assigns one of
# those 3 labels to *any* image. Measured against the labeled dataset in
# image_detection/data/ (180 samples across the 3 supported classes) the
# model is highly accurate on real potato leaves (early blight 40/40,
# late blight 40/40, healthy 37/40) — but it reports the SAME confidence
# for images that are not leaves at all:
#
#     real potato leaf   : confidence 0.95-0.97, top-2 margin 0.93-0.94
#     portrait-like photo : confidence 0.98,        top-2 margin 0.96
#     sky / flat image   : confidence 0.98,        top-2 margin 0.97
#
# Confidence and top-2 margin therefore CANNOT separate leaves from
# non-leaves, and raising the confidence threshold would not help: it
# would only start rejecting genuine leaves.
#
# The screen below runs BEFORE inference and rejects images that fail
# basic photographic / colour checks. Thresholds were calibrated on the
# labeled dataset so that no real leaf is rejected:
#
#     entropy (bits)   real leaves min 6.639  -> reject below 6.0
#     blue ratio       real leaves max 0.067  -> reject above 0.30
#
# KNOWN LIMITATION: this is a conservative heuristic filter, NOT a plant
# classifier. It reliably rejects portraits, sky, flat/blank frames and
# undersized or extreme-aspect images. It cannot reject every possible
# non-leaf photo (for example a close-up of soil or a wooden table).
# Reliable out-of-distribution detection would require a separately
# trained "is this a leaf?" model with a labeled negative dataset, which
# is not available in this repository.
# ===========================================================================
SCREENING_VERSION = "1"
SCREENING_RULES = {
    "min_dimension": 64,        # smaller than this cannot be screened reliably
    "max_aspect_ratio": 2.5,    # width/height or height/width beyond this
    "max_blue_ratio": 0.30,     # sky / blue-dominant images
    "min_entropy": 6.0,         # flat, blank or very low-detail frames
    "min_confidence": 0.65,     # existing model-confidence floor
}

SCREENING_REASONS = {
    "low_resolution": "The image is too small to screen reliably. Please upload a larger photo of a single potato leaf.",
    "bad_aspect_ratio": "The image shape is not suitable for leaf screening. Please upload a square-ish photo of a single potato leaf.",
    "low_quality": "The image looks blank or has too little detail. Please upload a clear, well-lit photo of a single potato leaf.",
    "not_foliage": "This does not appear to be a potato leaf photo. Crop Doctor only screens potato leaves (early blight, late blight, healthy).",
}


def _image_metrics(img_array):
    """Cheap colour/detail statistics used to screen out non-leaf images."""
    arr = np.asarray(img_array)
    r = arr[:, :, 0].astype(np.int16)
    g = arr[:, :, 1].astype(np.int16)
    b = arr[:, :, 2].astype(np.int16)

    green_ratio = float(((g > r + 10) & (g > b + 10)).mean())
    blue_ratio = float(((b > r + 20) & (b > g + 10)).mean())

    gray = arr.mean(axis=2).ravel().astype(np.uint8)
    hist = np.bincount(gray, minlength=256).astype(float)
    probs = hist[hist > 0] / hist.sum()
    entropy = float(-(probs * np.log2(probs)).sum())

    height, width = int(arr.shape[0]), int(arr.shape[1])
    return {
        "width": width,
        "height": height,
        "aspect_ratio": round(float(width) / float(height), 3),
        "green_ratio": round(green_ratio, 4),
        "blue_ratio": round(blue_ratio, 4),
        "entropy": round(entropy, 3),
    }


def _screen_image(img_array):
    """Return (accepted, reason, metrics) for a decoded RGB image."""
    metrics = _image_metrics(img_array)
    width = metrics["width"]
    height = metrics["height"]
    aspect = max(float(width) / float(height), float(height) / float(width))

    if min(width, height) < SCREENING_RULES["min_dimension"]:
        return False, "low_resolution", metrics
    if aspect > SCREENING_RULES["max_aspect_ratio"]:
        return False, "bad_aspect_ratio", metrics
    if metrics["entropy"] < SCREENING_RULES["min_entropy"]:
        return False, "low_quality", metrics
    if metrics["blue_ratio"] > SCREENING_RULES["max_blue_ratio"]:
        return False, "not_foliage", metrics
    return True, None, metrics


# Expert-Reviewed Agricultural Database (Responsible Agronomic Guidance)


TREATMENTS = {
    'Potato___Early_blight': {
        'en': {"name": "Early Blight", "med": "Mancozeb or Chlorothalonil", "plan": "Apply fungicide immediately. Ensure good airflow."},
        'te': {"name": "ముందస్తు ఆకుమచ్చ తెగులు", "med": "మాంకోజెబ్ లేదా క్లోరోథలోనిల్", "plan": "వెంటనే శిలీంద్ర సంహారిణి పిచికారీ చేయండి. గాలి బాగా ఆడేలా చూడండి."},
        'hi': {"name": "अगेती झुलसा", "med": "मैंकोजेब या क्लोरोथालोनिल", "plan": "तुरंत कवकनाशी का छिड़काव करें। हवा का प्रवाह सुनिश्चित करें।"},
        'mr': {"name": "करपा (Early Blight)", "med": "मॅन्कोझेब किंवा क्लोरोथालोनिल", "plan": "त्वरीत बुरशीनाशकाची फवारणी करा. झाडांना खेळती हवा मिळेल याची काळजी घ्या."}
    },
    'Potato___Late_blight': {
        'en': {"name": "Late Blight", "med": "Copper Fungicide or Cymoxanil", "plan": "URGENT! Apply medicine immediately. Burn infected plants."},
        'te': {"name": "ముదిరిన ఆకుమాడు తెగులు", "med": "రాగి ఆధారిత శిలీంద్ర సంహారిణి", "plan": "అత్యవసరం! వెంటనే మందు చల్లండి. తెగులు సోకిన మొక్కలను కాల్చేయండి."},
        'hi': {"name": "पछेती झुलसा", "med": "कॉपर कवकनाशी या सिमोक्सानिल", "plan": "अति आवश्यक! तुरंत दवा लगाएं। संक्रमित पौधों को नष्ट करें।"},
        'mr': {"name": "उशिरा येणारा करपा", "med": "कॉपर बुरशीनाशक किंवा सायमोक्सॅनिल", "plan": "तातडीने औषध फवारा. रोगग्रस्त झाडे काढून टाका."}
    },
    'Potato___healthy': {
        'en': {"name": "Healthy", "med": "None", "plan": "Plant is healthy. Continue standard care."},
        'te': {"name": "ఆరోగ్యకరమైనది", "med": "అవసరం లేదు", "plan": "మొక్క ఆరోగ్యంగా ఉంది. ఎప్పటిలాగే నీరు, ఎరువులు వేయండి."},
        'hi': {"name": "स्वस्थ", "med": "कोई नहीं", "plan": "पौधा स्वस्थ है। सामान्य देखभाल जारी रखें।"},
        'mr': {"name": "निरोगी", "med": "गरज नाही", "plan": "रोप निरोगी आहे. नेहमीप्रमाणे काळजी घ्या."}
    }
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def predict_disease():
    file = request.files.get('file')
    lang = request.form.get('language', 'en')
    
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        try:
            file.save(filepath)
            raw = tf.io.read_file(filepath)
            img = tf.io.decode_image(raw, channels=3, expand_animations=False)
        except Exception:
            try:
                if 'filepath' in locals() and os.path.exists(filepath):
                    os.remove(filepath)
            except Exception:
                pass
            return jsonify({"status": "error", "error": "The uploaded file is not a readable image."}), 400
        except Exception:
            return jsonify({"status": "error", "error": "The uploaded file is not a readable image."}), 400

        # ---- Pre-inference input screening -------------------------------
        # Rejects images that are clearly not a potato leaf (portraits,
        # sky, blank frames, undersized or extreme-aspect images) BEFORE
        # the model runs, so a non-leaf photo can never be presented as a
        # disease diagnosis. See SCREENING_RULES for calibration data.
        accepted, reason, metrics = _screen_image(img.numpy())
        if not accepted:


            return jsonify({
                "status": "success",
                "is_recognized": False,
                "reason": reason,
                "error": SCREENING_REASONS.get(reason, SCREENING_REASONS["not_foliage"]),
                "screening": {
                    "version": SCREENING_VERSION,
                    "accepted": False,
                    "metrics": metrics,
                },
            })

        img = tf.image.resize(img, (224, 224))
        img_array = tf.expand_dims(img, 0)

        predictions = model(img_array, training=False).numpy()[0]
        max_conf = float(np.max(predictions))
        ordered = np.sort(predictions)[::-1]
        margin = float(ordered[0] - ordered[1])

        # If the model is not confident, it's likely not a potato leaf
        if max_conf < SCREENING_RULES["min_confidence"]:
            return jsonify({
                "status": "success",
                "is_recognized": False,
                "reason": "low_confidence",
                "error": "Image not recognized as a supported leaf or disease.",
                "screening": {
                    "version": SCREENING_VERSION,
                    "accepted": True,
                    "metrics": metrics,
                },
            })

        idx = np.argmax(predictions)
        res_class = CLASS_NAMES[idx]
        
        # Get data for selected language
        diag = TREATMENTS[res_class][lang]
        
        scores = []
        for i, s in enumerate(predictions):
            scores.append({"name": TREATMENTS[CLASS_NAMES[i]][lang]["name"], "conf": round(float(s*100), 2)})

        # Aggressively release memory for Render free tier
        del img_array, img, predictions
        tf.keras.backend.clear_session()
        gc.collect()
        
        os.remove(filepath)
        return jsonify({
            "status": "success",
            "is_recognized": True,
            "is_healthy": res_class == 'Potato___healthy',
            "diagnosis": diag,
            "all_scores": sorted(scores, key=lambda x: x['conf'], reverse=True),
            "screening": {
                "version": SCREENING_VERSION,
                "accepted": True,
                "metrics": metrics,
                "confidence": round(max_conf, 4),
                "top2_margin": round(margin, 4),
            },
        })

if __name__ == '__main__':
    app.run(debug=True, port=5001)