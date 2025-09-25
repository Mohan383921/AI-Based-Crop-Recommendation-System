import requests

API_KEY = "8c0f9e85282d055723edee7e04a9610d"  # Replace with your real key
BASE_URL = "https://api.agromonitoring.com/agro/1.0"

POLYGONS = {
    "Ranchi": "68b82eabfdb6858e6b1bbf6",
    "Ranchi2": "68b82f051fd7b90e611654bc"
}

def get_weather_forecast(district: str):
    try:
        polygon_id = POLYGONS.get(district)
        if not polygon_id:
            raise ValueError(f"No polygon found for district: {district}")

        url = f"{BASE_URL}/weather?polyid={polygon_id}&appid={API_KEY}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return {
                "rainfall": data.get("rain", {}).get("1h", 0) or 50,
                "temperature": data.get("main", {}).get("temp", 298) - 273.15
            }
    except Exception as e:
        print("Weather API error:", e)
    return {"rainfall": 100, "temperature": 27}
