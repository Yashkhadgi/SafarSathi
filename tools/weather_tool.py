import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from config.settings import OPENWEATHER_API_KEY

BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"


def get_forecast(place_name: str, days: int = 3):
    try:
        if not OPENWEATHER_API_KEY:
            raise ValueError("OPENWEATHER_API_KEY not set in .env")

        resp = requests.get(BASE_URL, params={
            "q": place_name, "appid": OPENWEATHER_API_KEY, "units": "metric"
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        daily = {}
        for entry in data.get("list", []):
            date = entry["dt_txt"].split(" ")[0]
            temp = entry["main"]["temp"]
            condition = entry["weather"][0]["description"]
            if date not in daily:
                daily[date] = {"temps": [], "condition": condition}
            daily[date]["temps"].append(temp)

        forecast = []
        for date, info in list(daily.items())[:days]:
            forecast.append({
                "date": date,
                "temp_min": round(min(info["temps"]), 1),
                "temp_max": round(max(info["temps"]), 1),
                "condition": info["condition"],
            })
        return forecast
    except Exception as e:
        print(f"Weather lookup failed: {e}")
        return []


if __name__ == "__main__":
    print(get_forecast("Udaipur"))
