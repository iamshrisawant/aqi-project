/*
 * ESP32_Collect.ino 
 * IoT Air Quality Monitoring System - Data Collection Mode
 * Hardware: ESP32, MQ-135, MQ-7, DHT11
 * 
 * Purpose: Strictly collects raw data (Fields 1-4) and pushes directly to ThingSpeak.
 * This script is used ONLY to build the training dataset. It does not ping the 
 * Python predictor API.
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"

// ===== Pin Definitions =====
#define MQ135_PIN 34
#define MQ7_PIN   35
#define DHTPIN    4
#define DHTTYPE   DHT11 
#define GP2Y10_LED_PIN 5
#define GP2Y10_AOUT_PIN 32

// ===== Credentials & Config =====
const char* ssid = "Shri's a52";
const char* password = "OneTimePass";    
String writeAPIKey = "KRW44WZMKCYRZKB4";  
String channelID = "3283502";

const char* server = "http://api.thingspeak.com/update";

DHT dht(DHTPIN, DHTTYPE);
unsigned long lastUploadTime = 0;
const unsigned long uploadInterval = 20000; // 20s interval for logging

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
    pinMode(GP2Y10_AOUT_PIN, INPUT);
    pinMode(GP2Y10_LED_PIN, OUTPUT);
    digitalWrite(GP2Y10_LED_PIN, HIGH); // Default OFF
    
    Serial.println("\n⏳ Warming up sensors (30s)...");
    delay(30000); 
    connectWiFi();
    Serial.println("\n[DATA COLLECTION MODE] System Ready. Starting raw data logging...");
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
        
        // GP2Y10 Read Cycle
        digitalWrite(GP2Y10_LED_PIN, LOW); // LED ON
        delayMicroseconds(280);
        int gp2y10_raw = analogRead(GP2Y10_AOUT_PIN);
        delayMicroseconds(40);
        digitalWrite(GP2Y10_LED_PIN, HIGH); // LED OFF
        delayMicroseconds(9680);
        
        if (isnan(temperature) || isnan(humidity)) {
            Serial.println("✗ DHT Read Failed");
            return;
        }
        
        float mq135_voltage = mq135_raw * (3.3 / 4095.0); // MQ-135 Raw AQ voltage
        float mq7_voltage = mq7_raw * (3.3 / 4095.0);
        float co_ppm = mq7_voltage * 100;
        
        // GP2Y10 PM2.5 calculation
        float gp2y10_voltage = gp2y10_raw * (3.3 / 4095.0);
        float pm25 = 0.17 * gp2y10_voltage - 0.1; // mg/m3
        if (pm25 < 0) pm25 = 0.0;
        pm25 *= 1000; // ug/m3

        Serial.printf("\n[COLLECTING] Temp: %.1fC | Hum: %.1f%% | CO: %.1fppm | MQ135(V): %.2fV | GP2Y10 PM2.5: %.1f\n", 
                      temperature, humidity, co_ppm, mq135_voltage, pm25);
                      
        // 2. PUSH STRICTLY FIELDS 1-5 TO THINGSPEAK (No Field 6 Prediction)
        if (WiFi.status() == WL_CONNECTED) {
            HTTPClient http;
            String url = String(server) + "?api_key=" + writeAPIKey +
                         "&field1=" + String(pm25, 2) + "&field2=" + String(mq135_voltage, 2) +
                         "&field3=" + String(co_ppm, 2) + "&field4=" + String(temperature, 1) +
                         "&field5=" + String(humidity, 1);
            
            http.begin(url);
            int httpCode = http.GET();
            if (httpCode > 0) Serial.println("✓ Uploaded Raw Sensors to ThingSpeak (Field 6 left null)");
            else Serial.println("✗ ThingSpeak Upload Failed");
            http.end();
        }
    }
}
