import requests
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import pickle
import os

# Your ThingSpeak Channel Details.
CHANNEL_ID = "3283502"
READ_API_KEY = "D4EV7MBCA1OOZD19"
CSV_FILENAME = 'historical_air_quality_data.csv'
MODEL_FILENAME = 'rf_model.pkl'

def download_thingspeak_data():
    """
    Downloads historical data from ThingSpeak.
    Pulls Fields 1-4.
    """
    print(f"\n📡 Connecting to ThingSpeak Channel {CHANNEL_ID}...")
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json"
    
    # We pull up to 8000 results (API Maximum).
    # If more is needed, you can use start/end times in query parameters.
    try:
        response = requests.get(url, params={'api_key': READ_API_KEY, 'results': 8000}, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching from ThingSpeak: {e}")
        return pd.DataFrame() # Return empty DF

    feeds = response.json().get('feeds', [])
    if not feeds:
        print("⚠️ No data found on ThingSpeak channel.")
        return pd.DataFrame()

    print(f"✅ Fetched {len(feeds)} records from ThingSpeak.")
    
    # Extract only the 4 raw sensor fields
    data = []
    for f in feeds:
        try:
            row = {
                'Timestamp': f.get('created_at'),
                'PM25': float(f['field1']) if f.get('field1') else np.nan,
                'CO': float(f['field2']) if f.get('field2') else np.nan,
                'Temp': float(f['field3']) if f.get('field3') else np.nan,
                'Humidity': float(f['field4']) if f.get('field4') else np.nan
            }
            data.append(row)
        except Exception:
            pass # Skip invalid rows

    df_new = pd.DataFrame(data).dropna()
    df_new['Timestamp'] = pd.to_datetime(df_new['Timestamp'])
    return df_new

def get_categorical_aqi(pm25):
    """
    Categorizes AQI purely based on PM2.5 thresholding.
    We generate this locally to provide the Continuous Target (or class) for the ML model.
    """
    if pd.isna(pm25): return np.nan
    
    # The Regressor script in script.ipynb predicted the continuous value.
    # To keep ML architecture consistent with user notebook, we will train 
    # the Regressor on PM2.5 directly (treating PM2.5 as the true "Continuous AQI Score" for training).
    return float(pm25)

def train_and_export():
    print("\n" + "="*40)
    print("📊 STARTING AQI MODEL TRAINING PIPELINE 📊")
    print("="*40)

    # 1. Fetch Cloud Data
    df_cloud = download_thingspeak_data()

    # 2. Merge with Local Historical Data (If it exists)
    if os.path.exists(CSV_FILENAME):
        print(f"📁 Found existing local dataset: {CSV_FILENAME}")
        df_local = pd.read_csv(CSV_FILENAME)
        df_local['Timestamp'] = pd.to_datetime(df_local['Timestamp'])
        
        # Merge and drop duplicates (keeps historical data safe and slowly expands)
        df_merged = pd.concat([df_local, df_cloud]).drop_duplicates(subset=['Timestamp'])
        print(f"🔗 Merged datasets. Total records: {len(df_merged)}")
    else:
        df_merged = df_cloud
        print(f"🆕 Creating new local dataset. Total records: {len(df_merged)}")

    if len(df_merged) < 20: # Arbitrary minimum required to do a test/train split
        print("❌ Not enough data to train a reliable model. Please collect more Edge data to ThingSpeak first!")
        return

    # 3. Apply Label Generation for Training
    # The regressor learns to map the 4 inputs back to the dominant AQI metric (PM2.5) 
    df_merged['AQI_Target'] = df_merged['PM25'].apply(get_categorical_aqi)
    
    # Save the expanded dataset back to disk
    df_merged.to_csv(CSV_FILENAME, index=False)
    print(f"💾 Updated local dataset saved to '{CSV_FILENAME}'.")

    # 4. Filter and Train
    X = df_merged[['PM25', 'CO', 'Temp', 'Humidity']]
    y = df_merged['AQI_Target']

    # Handle missing values
    valid_idx = ~(X.isna().any(axis=1) | y.isna())
    X = X[valid_idx]
    y = y[valid_idx]

    print(f"\n🧠 Traning RandomForestRegressor on {len(X)} valid records...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)

    # 5. Evaluate Model
    predictions = rf_model.predict(X_test)
    r2 = r2_score(y_test, predictions)
    print(f"🎯 Model R² Score: {r2:.4f}")

    if r2 < 0:
        print("⚠️ Warning: R² score is negative. The model is performing worse than a horizontal line.")
        print("This usually happens when the dataset is extremely small or lacks variance.")

    # 6. Export Model
    with open(MODEL_FILENAME, "wb") as f:
        pickle.dump(rf_model, f)
    
    print(f"\n✅ Model successfully exported to '{MODEL_FILENAME}'.")
    print("You can now run the Live Predictor!\n")

if __name__ == "__main__":
    train_and_export()
