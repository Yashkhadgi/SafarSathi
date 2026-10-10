import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from config.settings import EXCHANGE_RATE_API_KEY

BASE_URL = "https://v6.exchangerate-api.com/v6"


def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """
    Returns {"converted_amount": float, "rate": float} on success,
    or {"error": "<short message>"} on failure. NEVER raises.
    """
    try:
        if not EXCHANGE_RATE_API_KEY:
            return {"error": "EXCHANGE_RATE_API_KEY not set in .env"}
        url = f"{BASE_URL}/{EXCHANGE_RATE_API_KEY}/pair/{from_currency.upper()}/{to_currency.upper()}/{amount}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("result") != "success":
            return {"error": data.get("error-type", "conversion failed")}
        return {
            "converted_amount": round(data["conversion_result"], 2),
            "rate": data["conversion_rate"],
        }
    except Exception as e:
        print(f"Currency conversion failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    print(convert_currency(100, "USD", "INR"))
