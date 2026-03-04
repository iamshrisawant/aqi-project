/*
 * ESP32_Predict.ino 
 * IoT Air Quality Monitoring System - Live Prediction Mode
 * Hardware: ESP32, MQ-135, MQ-7, DHT22
 * 
 * Purpose: Designed for the live demonstration. 
 * Reads Fields 1-4. Actively pings the Predictor API (Python) for the AI label
 * over the local network. 
 * Receives the prediction, and pushes a complete row (Fields 1-5) as a 
 * bundled HTTP GET request to ThingSpeak. 
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"

// ===== Pin Definitions =====
#define MQ135_PIN 34
#define MQ7_PIN   35
#define DHTPIN    4
#define DHTTYPE   DHT22 

// ===== Credentials & Config =====
const char* ssid = "Shri's a52";
const char* password = "OneTimePass";    
String writeAPIKey = "KRW44WZMKCYRZKB4";  

// ===== Network Configuration =====
const char* thingspeak_server = "http://api.thingspeak.com/update";

// REPLACE this IP Address with the IPv4 address of the laptop/server running main.py 
// Make sure both devices are on the "Shri's a52" network.
String python_server_ip = "192.168.x.x"; 
String predict_endpoint = "http://" + python_server_ip + ":5000/predict";

DHT dht(DHTPIN, DHTTYPE);
unsigned long lastUploadTime = 0;
const unsigned long uploadInterval = 20000; // 20s interval for ThingSpeak rate limits

void connectWiFi() {
    Serial.print("\nConnecting to WiFi");
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500); Serial.print(".");
    }
    Serial.println("\n✓ Connected!");
}

void setup() {
    Serial.begin(115200);
    dht.begin();
    pinMode(MQ135_PIN, INPUT);
    pinMode(MQ7_PIN, INPUT);
    
    Serial.println("\n⏳ Warming up sensors (30s)...");
    delay(30000); 
    connectWiFi();
    Serial.println("\n[LIVE PREDICTION MODE] System Ready. Starting Inference Loop...");
}

void loop() {
    if (WiFi.status() != WL_CONNECTED) connectWiFi();
    
    if (millis() - lastUploadTime >= uploadInterval) {
        lastUploadTime = millis();
        
        // 1. READ SENSORS
        int mq135_raw = analogRead(MQ135_PIN);
        int mq7_raw = analogRead(MQ7_PIN);
        float temperature = dht.readTemperature();
        float humidity = dht.readHumidity();
        
        if (isnan(temperature) || isnan(humidity)) {
            Serial.println("✗ DHT Read Failed");
            return;
        }
        
        float mq135_voltage = mq135_raw * (3.3 / 4095.0);
        float mq7_voltage = mq7_raw * (3.3 / 4095.0);
        float co_ppm = mq7_voltage * 100;
        float pm25 = (mq135_voltage * 100) / 2; 

        Serial.printf("\n[SENSORS] Temp: %.1fC | Hum: %.1f%% | CO: %.1fppm | PM2.5: %.1f\n", 
                      temperature, humidity, co_ppm, pm25);
                      
        // 2. PING PYTHON PREDICTOR INSTANTLY
        String ml_prediction = "";
        if (WiFi.status() == WL_CONNECTED) {
            HTTPClient httpPredictor;
            String url = predict_endpoint + "?pm25=" + String(pm25, 2) + 
                         "&co=" + String(co_ppm, 2) + 
                         "&temp=" + String(temperature, 1) + 
                         "&humidity=" + String(humidity, 1);
            
            Serial.println("⏳ Pinging Prediction API...");
            httpPredictor.begin(url);
            int httpCode = httpPredictor.GET();
            
            if (httpCode == 200) {
                ml_prediction = httpPredictor.getString();
                Serial.println("-----------------------------------");
                Serial.println("🤖 ML INFERENCE: " + ml_prediction);
                Serial.println("-----------------------------------");
            } else {
                Serial.println("⚠️ Predictor Offline. Fallback to Collection Mode.");
                ml_prediction = ""; // Leave null if server is down
            }
            httpPredictor.end();
        }

        // 3. PUSH BUNDLED DATA (FIELDS 1-5) TO THINGSPEAK
        if (WiFi.status() == WL_CONNECTED) {
            HTTPClient httpThingSpeak;
            String url = String(thingspeak_server) + "?api_key=" + writeAPIKey +
                         "&field1=" + String(pm25, 2) + "&field2=" + String(co_ppm, 2) +
                         "&field3=" + String(temperature, 1) + "&field4=" + String(humidity, 1) +
                         "&field5=" + ml_prediction;
            
            httpThingSpeak.begin(url);
            int httpCode = httpThingSpeak.GET();
            if (httpCode > 0) Serial.println("✓ Uploaded Full Bundle (Fields 1-5) to ThingSpeak");
            else Serial.println("✗ ThingSpeak Upload Failed");
            httpThingSpeak.end();
        }
    }
}
