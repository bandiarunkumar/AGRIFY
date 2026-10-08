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

# Expert-Reviewed Agricultural Database
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
        file.save(filepath)
        img = tf.keras.utils.load_img(filepath, target_size=(224, 224))
        img_array = tf.expand_dims(tf.keras.utils.img_to_array(img), 0)

        predictions = model.predict(img_array, verbose=0)[0]
        max_conf = float(np.max(predictions))
        
        # If the model is not confident, it's likely not a potato leaf
        if max_conf < 0.65:
            os.remove(filepath)
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
            "all_scores": sorted(scores, key=lambda x: x['conf'], reverse=True)
        })

if __name__ == '__main__':
    app.run(debug=True, port=5001)