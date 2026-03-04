from flask import Flask, request, jsonify
import pandas as pd
import pickle
import os
import logging

app = Flask(__name__)

# Suppress default flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

MODEL_PATH = "rf_model.pkl"

def load_model():
    if not os.path.exists(MODEL_PATH):
        print(f"\n[ERROR] Model file '{MODEL_PATH}' not found!")
        print("Please run the ‘Train ML Model’ option from the main menu first.\n")
        return None
    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
            return model
    except Exception as e:
        print(f"\n[ERROR] Failed to load model: {e}\n")
        return None

def get_categorical_aqi(pm25):
    """
    Categorizes AQI purely based on PM2.5 thresholding.
    This matches the logic defined in script.ipynb
    """
    if pd.isna(pm25): return "Unknown"
    if pm25 <= 50: return "Good"
    elif pm25 <= 100: return "Moderate"
    elif pm25 <= 150: return "Unhealthy for Sensitive"
    elif pm25 <= 200: return "Unhealthy"
    else: return "Hazardous"

@app.route('/predict', methods=['GET'])
def predict():
    """
    ESP32 Pings this endpoint via GET request.
    Example: http://<IP>:5000/predict?pm25=45.2&co=12.5&temp=28.3&humidity=65.8
    """
    # 1. Parse Query Parameters from ESP32
    try:
        pm25 = float(request.args.get('pm25', 0.0))
        co = float(request.args.get('co', 0.0))
        temp = float(request.args.get('temp', 0.0))
        humidity = float(request.args.get('humidity', 0.0))
    except ValueError:
        return "Error parsing sensor readouts", 400

    # 2. Load Model
    model = load_model()
    if model is None:
        return "Model Offline", 503

    try:
        # 3. Predict Raw AQI Value
        input_data = pd.DataFrame({'PM25': [pm25], 'CO': [co], 'Temp': [temp], 'Humidity': [humidity]})
        predicted_aqi_val = model.predict(input_data)[0]
        
        # 4. Convert Raw AQI to Category String (The ML Label)
        category = get_categorical_aqi(predicted_aqi_val)

        # Print to terminal for orchestrator visual
        print(f"📡 [PING RECEIVED] PM2.5:{pm25} CO:{co} Temp:{temp} Hum:{humidity}")
        print(f"🎯 [INFERRED AQI] {predicted_aqi_val:.1f} -> {category}\n")

        # 5. Return the string instantly to the ESP32
        return str(category), 200

    except Exception as e:
        print(f"[ERROR] Inference failed: {e}")
        return "Inference Error", 500

if __name__ == '__main__':
    print("\n" + "="*40)
    print("🚀 LIVE PREDICTOR API IS ONLINE 🚀")
    print("Listening for ESP32 pings on Port 5000...")
    print("Press Ctrl+C to stop the server and return to the main menu.")
    print("="*40 + "\n")
    
    # Run the Flask App strictly on the local network (0.0.0.0 allows external devices like ESP32 to connect)
    app.run(host='0.0.0.0', port=5000, debug=False)
