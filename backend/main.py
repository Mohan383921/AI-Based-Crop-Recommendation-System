from typing import Any, Dict
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from backend import models, recommender

app = FastAPI(title="Crop Recommendation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/recommendations")
def get_recommendations(request: models.CropRequest) -> Dict[str, Any]:
    recs, weather = recommender.recommend_crops(request)
    return {"recommendations": recs, "weather": weather}


@app.post("/ivr")
def ivr_simulation(payload: Dict[str, Any] = Body(...)) -> Dict[str, str]:
    option = payload.get("option")
    try:
        option = int(option)
    except Exception:
        return {"message": "Invalid option. Send option as integer (1 or 2)."}

    if option == 1:
        return {"message": "🌦 Weather update: Rainfall 120 mm, Temperature 27 °C"}
    elif option == 2:
        dummy_req = models.CropRequest(district="Ranchi", top_k=1)
        recs, weather = recommender.recommend_crops(dummy_req)
        best = recs[0] if recs else {"crop": "N/A", "yield": 0}
        return {"message": f"🌾 Suggested crop: {best.get('crop', 'N/A')}. Expected yield: {best.get('yield', 0)} t/acre."}
    else:
        return {"message": "Invalid option. Please press 1 for weather or 2 for recommendation."}


@app.post("/sms")
def sms_simulation(payload: Dict[str, Any] = Body(...)) -> Dict[str, str]:
    raw = payload.get("message", "")
    if not raw:
        return {"message": "No message provided. Please send soil data like: PH=6.5 N=50 P=30 K=40"}

    msg = raw.upper().replace(",", " ").replace(";", " ")
    ph = n = p = k = None
    tokens = msg.split()
    for t in tokens:
        if "=" in t:
            key, val = t.split("=", 1)
            key = key.strip()
            val = val.strip()
            try:
                if key == "PH":
                    ph = float(val)
                elif key == "N":
                    n = float(val)
                elif key == "P":
                    p = float(val)
                elif key == "K":
                    k = float(val)
            except Exception:
                continue

    ph = ph if ph is not None else 6.5
    n = n if n is not None else 50.0
    p = p if p is not None else 30.0
    k = k if k is not None else 40.0

    req = models.CropRequest(
        district="Ranchi",
        soil_ph=ph,
        soil_moisture=25.0,
        nutrient_n=n,
        nutrient_p=p,
        nutrient_k=k,
        top_k=1
    )

    recs, weather = recommender.recommend_crops(req)
    best = recs[0] if recs else None
    if best and not (isinstance(best, dict) and best.get("error")):
        return {"message": f"🌾 Suggested crop: {best.get('crop')} | Yield: {best.get('yield')} t/acre | Profit est: {best.get('profit')}"}
    else:
        if best and isinstance(best, dict) and best.get("error"):
            details = best.get("details", [])
            return {"message": "Input validation failed: " + "; ".join(details)}
        return {"message": "Could not determine recommendation. Please try again."}
        