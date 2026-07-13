import json
import requests

KEY = "46khpWpgPvKmhMdWx64SjhRfJ9LCfipn"
BASE = "https://financialmodelingprep.com/stable"

endpoints = {
    "screener": f"{BASE}/company-screener?marketCapMoreThan=50000000&limit=3&apikey={KEY}",
    "income": f"{BASE}/income-statement?symbol=AAPL&limit=1&apikey={KEY}",
    "balance": f"{BASE}/balance-sheet-statement?symbol=AAPL&limit=1&apikey={KEY}",
    "enterprise_values": f"{BASE}/enterprise-values?symbol=AAPL&limit=1&apikey={KEY}",
    "profile": f"{BASE}/profile?symbol=AAPL&apikey={KEY}",
    "historical": f"{BASE}/historical-price-eod/full?symbol=AAPL&apikey={KEY}",
    "sp500": f"{BASE}/sp500-constituent?apikey={KEY}",
}

for name, url in endpoints.items():
    try:
        r = requests.get(url, timeout=15)
        print(f"\n=== {name} — HTTP {r.status_code} ===")
        try:
            print(json.dumps(r.json(), indent=2)[:800])
        except ValueError:
            print(f"(non-JSON response) {r.text[:300]}")
    except Exception as e:
        print(f"\n=== {name} — request failed: {e} ===")