# End-to-End IoT Air Quality Predictor

A fully automated, closed-loop Internet of Things (IoT) and Machine Learning architecture. This project measures live environmental sensor data using an ESP32, infers the current Air Quality Index (AQI) classification through a localized Random Forest model, and synchronizes the full telemetry securely to ThingSpeak for observation.

## Hardware Stack
*   **Microcontroller**: ESP32
*   **Sensors**: MQ-135 (Air Quality), MQ-7 (Carbon Monoxide), DHT22 (Temperature & Humidity), PM2.5 Sensor (Simulated via MQ135 logic)

## Architecture
This pipeline avoids public cloud rate-limiting entirely by utilizing a Local Area Network (LAN) edge prediction server bridging the hardware to the cloud logging interface:

1.  **Collection Phase (`ESP32_Collect.ino`)**
    The ESP32 reads raw data from the sensors and pushes directly to Fields 1-4 on a ThingSpeak channel. This phase runs headless to generate a massive, localized training dataset.
2.  **Machine Learning Training (`train_model.py`)**
    Downloads the entire compiled dataset from ThingSpeak, engineers a unified PM2.5-based continuous target label, and trains a detailed `RandomForestRegressor`. The output is serialized as `rf_model.pkl`.
3.  **Live Prediction Loop (`ESP32_Predict.ino` & `live_predictor.py`)**
    *   The ESP32 pulls fresh data from the sensors.
    *   The ESP32 executes an immediate REST API request to the local Python script, handing off external inference to the laptop/server.
    *   The Python Flask Server interprets the payload and instantly responds with the categorical ML label (eg. "Moderate", "Hazardous").
    *   The ESP32 successfully bundles all sensors and the response label into a single payload, pushing the complete status to ThingSpeak Fields 1-5 without delays.

## Installation & Setup
The project structure is split between Arduino constraints (C++) and Model Orchestration (Python).

### 1. Python Environment
Install core data science and web routing libraries:
```bash
pip install -r requirements.txt
```

### 2. ThingSpeak Configuration
Your associated free ThingSpeak channel must be configured with exactly 5 fields:
*   **Field 1**: PM2.5
*   **Field 2**: CO
*   **Field 3**: Temperature
*   **Field 4**: Humidity
*   **Field 5**: ML_Predicted_AQI_Category

### 3. ESP32 Network configuration
Inside `ESP32_Predict.ino`, you must modify the code to point to the local instance hosting the Python server:
```cpp
const char* ssid = "YOUR_WIFI_MAC_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
String python_server_ip = "192.168.X.X"; // Match to local machine running Python
```

## Running the Application

All pipeline interactions are wrapped in a simplified Interactive Python Orchestrator menu, abstracting complex backend execution for ease of demonstration.

1.  Open a terminal inside the project directory.
2.  Run the menu interface: 
    ```bash
    python main.py
    ```
3.  **Select Option 1** to pull fresh ThingSpeak logs and retrain the Machine Learning core.
4.  **Select Option 2** to launch the localized TCP Server listener that will evaluate live ESP32 payloads over port `5000`.
