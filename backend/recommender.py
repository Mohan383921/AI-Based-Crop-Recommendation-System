import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
from typing import Tuple, List, Dict, Any
from backend.models import CropRequest
from backend.providers import weather_api

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")

DATA = pd.DataFrame({
    'ph': [6.5, 7.0, 5.5, 6.8, 7.2],
    'moisture': [20, 35, 15, 40, 25],
    'n': [50, 60, 40, 55, 70],
    'p': [30, 25, 20, 35, 40],
    'k': [40, 50, 35, 45, 60],
    'rainfall': [100, 120, 80, 150, 90],
    'temperature': [25, 28, 22, 30, 27],
    'crop': ['rice', 'wheat', 'millet', 'maize', 'sugarcane']
})

def train_and_save_model():
    X = DATA.drop(columns=['crop'])
    y = DATA['crop']
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    try:
        joblib.dump(model, MODEL_PATH)
    except Exception:
        pass
    return model

def load_model():
    if os.path.exists(MODEL_PATH):
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            return train_and_save_model()
    else:
        return train_and_save_model()

MODEL = load_model()

def deterministic_yield(ph: float, moisture: float, n: float, p: float, k: float,
                        rainfall: float, temp: float) -> float:
    ph = float(np.clip(ph, 3.0, 10.0))
    moisture = float(np.clip(moisture, 0.0, 100.0))
    n = float(np.clip(n, 0.0, 500.0))
    p = float(np.clip(p, 0.0, 300.0))
    k = float(np.clip(k, 0.0, 400.0))
    rainfall = float(np.clip(rainfall, 0.0, 1000.0))
    temp = float(np.clip(temp, -10.0, 60.0))

    ph_score = max(0.0, 1.0 - abs(ph - 6.5) / 4.0)
    moisture_score = moisture / 100.0
    nutrient_score = (min(n,200)/200.0)*0.5 + (min(p,100)/100.0)*0.25 + (min(k,150)/150.0)*0.25
    rainfall_score = min(rainfall, 200.0) / 200.0
    temp_score = max(0.0, 1.0 - abs(temp - 27.0) / 30.0)

    aggregate = (ph_score * 0.30 +
                moisture_score * 0.20 +
                nutrient_score * 0.25 +
                rainfall_score * 0.15 +
                temp_score * 0.10)

    yield_t = 1.0 + aggregate * 7.0
    yield_t = float(np.clip(yield_t, 1.0, 8.0))
    return round(yield_t, 2)

def deterministic_profit(yield_t: float, crop_name: str) -> float:
    price_map = {
        "rice": 20000.0,
        "wheat": 18000.0,
        "millet": 15000.0,
        "maize": 16000.0,
        "sugarcane": 10000.0
    }
    price = price_map.get(str(crop_name).lower(), 15000.0)
    profit = yield_t * price
    return round(float(profit), 2)

def deterministic_sustainability(ph: float, last_crop: str) -> float:
    ph = float(np.clip(ph, 3.0, 10.0))
    base = max(0.0, 1.0 - abs(ph - 6.5) / 5.0)
    if last_crop and isinstance(last_crop, str):
        lc = last_crop.strip().lower()
        if lc in ["rice", "wheat", "millet", "maize", "sugarcane"]:
            base *= 0.92
    return round(float(np.clip(base, 0.0, 1.0)), 2)

def validate_inputs(ph: float, moisture: float, n: float, p: float, k: float,
                    rainfall: float, temp: float) -> List[str]:
    errors: List[str] = []
    if ph is None or ph != ph:
        errors.append("pH is missing or not a number.")
    else:
        if ph < 3.0 or ph > 10.0:
            errors.append(f"pH {ph} is out of realistic soil range (3–10).")
    if moisture is None or moisture != moisture:
        errors.append("Soil moisture is missing or not a number.")
    else:
        if moisture < 0.0 or moisture > 100.0:
            errors.append(f"Soil moisture {moisture}% is out of valid range (0–100%).")
    if n is None or n != n:
        errors.append("Nitrogen (N) is missing or not a number.")
    else:
        if n < 0.0 or n > 500.0:
            errors.append(f"Nitrogen value {n} is unrealistic (expected 0–500).")
    if p is None or p != p:
        errors.append("Phosphorus (P) is missing or not a number.")
    else:
        if p < 0.0 or p > 300.0:
            errors.append(f"Phosphorus value {p} is unrealistic (expected 0–300).")
    if k is None or k != k:
        errors.append("Potassium (K) is missing or not a number.")
    else:
        if k < 0.0 or k > 400.0:
            errors.append(f"Potassium value {k} is unrealistic (expected 0–400).")
    if rainfall is None or rainfall != rainfall:
        pass
    else:
        if rainfall < 0.0 or rainfall > 1000.0:
            errors.append(f"Rainfall {rainfall} mm seems invalid (expected 0–1000).")
    if temp is None or temp != temp:
        pass
    else:
        if temp < -10.0 or temp > 60.0:
            errors.append(f"Temperature {temp}°C is out of realistic range (-10 to 60°C).")
    return errors

def recommend_crops(request: CropRequest) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    weather = weather_api.get_weather_forecast(request.district)

    ph = request.soil_ph if request.soil_ph is not None else 6.5
    moisture = request.soil_moisture if request.soil_moisture is not None else 25.0
    n = request.nutrient_n if request.nutrient_n is not None else 50.0
    p = request.nutrient_p if request.nutrient_p is not None else 30.0
    k = request.nutrient_k if request.nutrient_k is not None else 40.0
    rainfall = request.rainfall if request.rainfall is not None else weather.get('rainfall', 100.0)
    temp = request.temperature if request.temperature is not None else weather.get('temperature', 27.0)
    last_crop = request.last_crop if request.last_crop is not None else ""

    errors = validate_inputs(ph, moisture, n, p, k, rainfall, temp)
    if errors:
        return [{"error": "Invalid inputs", "details": errors}], weather

    features = pd.DataFrame([{
        'ph': float(ph),
        'moisture': float(moisture),
        'n': float(n),
        'p': float(p),
        'k': float(k),
        'rainfall': float(rainfall),
        'temperature': float(temp)
    }])

    try:
        probs = MODEL.predict_proba(features)[0]
        crops = list(MODEL.classes_)
    except Exception:
        return [{"error": "Model error", "details": ["Recommendation model currently unavailable."]}], weather

    crop_scores = sorted(zip(crops, probs), key=lambda x: (-x[1], x[0]))

    recs: List[Dict[str, Any]] = []
    for crop, score in crop_scores[:request.top_k]:
        yld = deterministic_yield(ph, moisture, n, p, k, rainfall, temp)
        prof = deterministic_profit(yld, crop)
        sust = deterministic_sustainability(ph, last_crop)

        recs.append({
            'crop': str(crop),
            'score': float(round(float(score), 4)),
            'yield': yld,
            'profit': prof,
            'sustainability': sust,
            'rationale': f"Based on pH {ph}, NPK {n}/{p}/{k}, rainfall {rainfall}mm, temperature {round(temp,2)}°C",
            'rainfall': float(rainfall),
            'temperature': round(float(temp), 2)
        })

    return recs, weather
