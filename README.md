# End-to-End IoT Air Quality Predictor

A fully automated, closed-loop Internet of Things (IoT) and Machine Learning architecture. This capstone project measures live environmental sensor data using an ESP32 edge device, infers the current Air Quality Index (AQI) classification through a localized Random Forest model, and synchronizes the full telemetry securely to ThingSpeak for observation and historical logging.

---

## 1. Project Overview & Features

This system is designed to provide real-time air quality monitoring with predictive capabilities while elegantly bypassing the rate-limiting constraints of free public cloud tiers like ThingSpeak.

### Core Features
*   **Decoupled Architecture**: Hardware data collection is independent of cloud ML prediction, ensuring seamless execution.
*   **Dual-State Hardware**: Two distinct ESP32 firmware modes:
    *   **Data Collection Mode**: Runs headless to generate massive, localized training datasets.
    *   **Live Prediction Mode**: Demonstrates real-time Machine Learning inference at the edge.
*   **Local Web API Bridge**: Python-based REST API serves instantaneous inferences to the ESP32 hardware without making the ESP32 wait for Cloud API limits.
*   **Interactive CLI Orchestrator**: A foolproof terminal interface abstracts complex execution commands, making demonstrations easy for all technical backgrounds.

### Hardware Stack
*   **Microcontroller**: ESP32
*   **Sensors**:
    *   MQ-135 (Air Quality / Simulating PM2.5)
    *   MQ-7 (Carbon Monoxide)
    *   DHT22 (Temperature & Humidity)

---

## 2. Infrastructure Setup & Prerequisites

### 2.1 ThingSpeak Configuration
Your free ThingSpeak channel must be configured with exactly 5 fields to match the payload bundles.
1.  Log into ThingSpeak and create a new Channel (or edit your existing one).
2.  Enable and name the following fields exactly:
    *   **Field 1**: PM2.5 (ug/m3)
    *   **Field 2**: CO (ppm)
    *   **Field 3**: Temperature (C)
    *   **Field 4**: Humidity (%)
    *   **Field 5**: ML_Predicted_AQI_Category
3.  Navigate to the "API Keys" tab and copy your **Write API Key**. You will need this for the ESP32 code.

### 2.2 Python Environment Setup
The centralized predictor runs on a local machine (Windows laptop, Linux server, Raspberry Pi).
1.  Ensure you have **Python 3.8+** installed.
2.  Open a terminal in the project directory.
3.  Install the required core data science and web routing libraries:
    ```bash
    pip install -r requirements.txt
    ```

### 2.3 ESP32 & Arduino IDE Setup
To compile and upload code to the ESP32, you must configure the Arduino IDE.
1.  **Install Arduino IDE**: Download and install the latest version of the Arduino IDE.
2.  **Add ESP32 Board Manager**:
    *   Go to `File` > `Preferences`.
    *   In the "Additional Boards Manager URLs" field, add: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
    *   Go to `Tools` > `Board` > `Boards Manager...`
    *   Search for "esp32" and install the official package by Espressif Systems.
3.  **Select Your Board**: Go to `Tools` > `Board` > `ESP32 Arduino` and select the appropriate board (e.g., "DOIT ESP32 DEVKIT V1").
4.  **Install Required Libraries**: Ensure you have installed the "DHT sensor library" by Adafruit via the Library Manager (`Tools` > `Manage Libraries...`).

---

## 3. Deployment Configuration

### 3.1 Network Configuration
The ESP32 and the Python Predictor must be connected to the exact same local network (e.g., your mobile hotspot).

1.  Open `ESP32_Predict/ESP32_Predict.ino` and `ESP32_Collect/ESP32_Collect.ino`.
2.  Update the network credentials:
    ```cpp
    const char* ssid = "YOUR_WIFI_MAC_SSID";
    const char* password = "YOUR_WIFI_PASSWORD";
    String writeAPIKey = "YOUR_THINGSPEAK_WRITE_API_KEY";
    ```
3.  In `ESP32_Predict.ino`, update the `python_server_ip` on **Line 26** to match the IPv4 address of the laptop/server holding the Python scripts (Find this using `ipconfig` on Windows or `ifconfig` on Linux/Mac).
    ```cpp
    String python_server_ip = "192.168.X.X";
    ```

---

## 4. End-to-End Execution Guide

All pipeline interactions are wrapped in a simplified Interactive Python Orchestrator menu, abstracting complex backend execution for ease of demonstration.

### Phase 1: Building the Dataset (Headless Logging)
1.  Open **`ESP32_Collect.ino`** in your Arduino IDE.
2.  Flash the code to your ESP32 board.
3.  Power on the board and let it run (e.g., near smoke, outdoors, indoors) to gather diverse sensor data.
4.  It will blindly push hundreds of raw sensor readings to ThingSpeak Fields 1-4. The more robust this phase, the smarter the subsequent AI model will be.

### Phase 2: Machine Learning Training
1.  Open a terminal in the project directory.
2.  Run the orchestrator menu:
    ```bash
    python main.py
    ```
3.  **Select Option 1 (Train ML Model)**.
    *   The script (`train_model.py`) will securely download all your newly collected historical data from ThingSpeak.
    *   It merges this data, engineers the continuous regression targets, and trains a `RandomForestRegressor`.
    *   The output model is exported and saved locally as `rf_model.pkl`.
    *   *Note: If you run this without sufficient training data on ThingSpeak, it will gracefully warn you to collect more edge data first.*

### Phase 3: Live AI Demonstration
1.  Ensure your `rf_model.pkl` has been successfully generated from Phase 2.
2.  In the `main.py` menu terminal, **Select Option 2 (Start Live Predictor)**.
    *   This launches the `live_predictor.py` Flask REST API listening on Port 5000.
3.  Open **`ESP32_Predict.ino`** in your Arduino IDE and flash it to the ESP32.
4.  Watch the Live Inferences:
    *   Every 20 seconds, the ESP32 instantly pings your local Python server with the raw environmental data.
    *   The Python server immediately replies with the AI Classification Label.
    *   The ESP32 bundles the sensory data + the intelligent prediction and pushes the complete status payload to ThingSpeak Fields 1-5 without delays or rate-limit violations.

You can halt the Predictor Server at any time by pressing `Ctrl+C` in the terminal, safely returning you to the main menu.
