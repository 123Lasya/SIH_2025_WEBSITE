import os
import pickle
import pandas as pd
import numpy as np
from django.conf import settings
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 1. MODEL + DATA PATHS
# ---------------------------------------------------------

MODEL_DIR = os.path.join(settings.BASE_DIR, "core", "ml_models")

MODEL_PATHS = {
    "Groundnut": os.path.join(MODEL_DIR, "groundnut_model.pkl"),
    "Soybean":   os.path.join(MODEL_DIR, "soyabean_model.pkl"),
    "Sunflower": os.path.join(MODEL_DIR, "mustard_model.pkl"), 
}

DATA_PATHS = {
    "Groundnut": os.path.join(MODEL_DIR, "processed_groundnut.csv"),
    "Soybean":   os.path.join(MODEL_DIR, "processed_soyabean.csv"),
    "Sunflower": os.path.join(MODEL_DIR, "processed_mustard.csv"),
}

loaded_models = {}
cached_data = {}

# ---------------------------------------------------------
# 2. LOAD MODEL ONLY ONCE
# ---------------------------------------------------------

def load_model(crop):
    """Load ML model for crop (cached)."""
    if crop not in loaded_models:
        with open(MODEL_PATHS[crop], "rb") as f:
            loaded_models[crop] = pickle.load(f)
    return loaded_models[crop]

# ---------------------------------------------------------
# 3. LOAD PROCESSED DATAFRAME
# ---------------------------------------------------------

def load_data(crop):
    """Load processed dataset (cached)."""
    if crop not in cached_data:
        df = pd.read_csv(DATA_PATHS[crop])
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        cached_data[crop] = df
    return cached_data[crop]

# ---------------------------------------------------------
# 4. FEATURES USED FOR ALL MODELS
# ---------------------------------------------------------

BASE_FEATURES = [
    "lag_1", "lag_7", "lag_14", "lag_30",
    "roll_7", "roll_30", "roll_90",
    "min_price", "max_price", "spread",
    "month", "day_of_year", "weekday", "year"
]

# Groundnut-specific features
GROUNDNUT_EXTRA = ["arrivals_lag_1", "arrivals_roll_7"]


def get_feature_order(crop, df):

    # Strict feature order for Groundnut model
    if crop == "Groundnut":
        return [
            "lag_1", "lag_7", "lag_14", "lag_30",
            "roll_7", "roll_30", "roll_90",
            "arrivals_lag_1", "arrivals_roll_7",
            "min_price", "max_price", "spread",
            "month", "day_of_year", "weekday", "year"
        ]

    # For Soybean & Sunflower (Mustard)
    return [
        "lag_1", "lag_7", "lag_14", "lag_30",
        "roll_7", "roll_30", "roll_90",
        "min_price", "max_price", "spread",
        "month", "day_of_year", "weekday", "year"
    ]

# 5. BUILD FEATURES FOR A FUTURE DATE

def build_features(df, future_date):
    future_date = pd.to_datetime(future_date)
    last_row = df.iloc[-1]

    features = {}

    # Date features
    features["year"] = future_date.year
    features["month"] = future_date.month
    features["day_of_year"] = future_date.dayofyear
    features["weekday"] = future_date.weekday()

    # Lag features
    features["lag_1"] = last_row["modal_price"]
    features["lag_7"] = df.iloc[-7]["modal_price"] if len(df) >= 7 else last_row["modal_price"]
    features["lag_14"] = df.iloc[-14]["modal_price"] if len(df) >= 14 else last_row["modal_price"]
    features["lag_30"] = df.iloc[-30]["modal_price"] if len(df) >= 30 else last_row["modal_price"]

    # Rolling averages
    features["roll_7"]  = df["modal_price"].tail(7).mean()
    features["roll_30"] = df["modal_price"].tail(30).mean()
    features["roll_90"] = df["modal_price"].tail(90).mean()

    # Market pattern
    features["min_price"] = last_row.get("min_price", last_row["modal_price"])
    features["max_price"] = last_row.get("max_price", last_row["modal_price"])
    features["spread"] = features["max_price"] - features["min_price"]

    # Extra groundnut features (ONLY IF PRESENT)
    if "arrivals_lag_1" in df.columns:
        features["arrivals_lag_1"] = last_row.get("arrivals_lag_1", 0.0)

    if "arrivals_roll_7" in df.columns:
        features["arrivals_roll_7"] = last_row.get("arrivals_roll_7", 0.0)

    return features

# 6. PREDICT PRICE FOR A SINGLE FUTURE DATE

def predict_price(crop, date):
    df = load_data(crop)
    model = load_model(crop)

    # Build features
    features = build_features(df, date)

    # Order features correctly
    feature_order = get_feature_order(crop, df)

    X = pd.DataFrame([[features[col] for col in feature_order]], columns=feature_order)

    pred = model.predict(X)[0]
    return round(float(pred), 2)

# 7. FORECAST NEXT 7 DAYS (USED IN DASHBOARD)

def forecast_next_7_days(crop):
    today = datetime.today().date()
    predictions = []

    for i in range(1, 8):
        d = today + timedelta(days=i)
        price = predict_price(crop, d)

        predictions.append({
            "date": d.strftime("%Y-%m-%d"),
            "price": price
        })

    return predictions
