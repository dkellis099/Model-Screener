"""
Magic Formula Stock Screener — data pipeline.

Redesigned to work entirely within Financial Modeling Prep's free tier
(250 requests/day). See Readme.md for the full architecture explanation.

Key design choices:
- Ticker universe is a static, curated list (backend/universe.json), NOT
  pulled from FMP's company-screener or sp500-constituent endpoints — both
  are paid-tier only on the stable API. Refresh universe.json periodically
  by hand from a free source, e.g.:
  https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv
- Fundamentals (income statement, balance sheet, profile — 3 calls/symbol)
  are cached in backend/fundamentals_cache.json and refreshed on a rotating
  basis (a limited number of symbols per run), since they only change
  quarterly. This is the expensive part of the budget, so it's spread out.
- Enterprise value / market cap / price (1 call/symbol via the
  enterprise-values endpoint, which bundles all of it) is refreshed for
  every cached symbol on every run, since that's cheap and changes daily.
- Historical returns (1d/1m/1y) are only fetched for the final top-N ranked
  stocks, not the whole scan universe, since they're a display feature and
  the most expensive call per symbol.
"""

import requests
import pandas as pd
import time
import re
import json
import datetime
import os
from typing import Dict, List, Optional

# --- Config ---------------------------------------------------------------

UNIVERSE_FILE = "backend/universe.json"
FUNDAMENTALS_CACHE_FILE = "backend/fundamentals_cache.json"
RESULTS_JSON = "public/magic_formula_results.json"
RESULTS_CSV = "public/magic_formula_results.csv"
LAST_UPDATED_FILE = "public/last_updated.json"

FUNDAMENTALS_MAX_AGE_DAYS = 30      # re-pull income/balance/profile at most this often
FUNDAMENTALS_REFRESH_BUDGET = 15    # symbols refreshed per run (3 calls each = 45 calls)
TOP_N_FOR_RETURNS = 30              # only fetch historical returns for the final top N

MIN_MARKET_CAP = 2_000_000_000      # $2B floor for "large cap"
SECTOR_EXCLUDE = {"Financial Services", "Utilities", "Real Estate"}

REQUEST_DELAY_SECONDS = 0.25        # be polite to the API between calls


# --- Helpers ----------------------------------------------------------------

def load_json(path: str, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def save_json(path: str, data):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# --- Core calculator ----------------------------------------------------------

class MagicFormulaCalculator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://financialmodelingprep.com/stable"

    def _get(self, path: str, **params):
        params["apikey"] = self.api_key
        url = f"{self.base_url}/{path}"
        try:
            response = requests.get(url, params=params, timeout=20)
        except requests.RequestException as e:
            print(f"Request error for {path} ({params.get('symbol', '')}): {e}")
            return None

        if response.status_code != 200:
            print(f"{path} failed for {params.get('symbol', '')}: "
                  f"HTTP {response.status_code} — {response.text[:200]}")
            return None

        try:
            return response.json()
        except ValueError:
            print(f"{path} returned non-JSON for {params.get('symbol', '')}")
            return None

    def fetch_fundamentals(self, symbol: str) -> Optional[Dict]:
        """3 API calls: income statement, balance sheet, profile."""
        income = self._get("income-statement", symbol=symbol, limit=1)
        time.sleep(REQUEST_DELAY_SECONDS)
        balance = self._get("balance-sheet-statement", symbol=symbol, limit=1)
        time.sleep(REQUEST_DELAY_SECONDS)
        profile = self._get("profile", symbol=symbol)
        time.sleep(REQUEST_DELAY_SECONDS)

        if not income or not balance or not profile:
            return None

        income = income[0]
        balance = balance[0]
        profile = profile[0]

        return {
            "symbol": symbol,
            "name": profile.get("companyName", ""),
            "sector": profile.get("sector", ""),
            # stable API's income-statement includes a real 'ebit' field;
            # fall back to operatingIncome as an approximation if it's missing.
            "ebit": income.get("ebit", income.get("operatingIncome", 0)),
            "total_assets": balance.get("totalAssets", 0),
            "total_current_assets": balance.get("totalCurrentAssets", 0),
            "total_current_liabilities": balance.get("totalCurrentLiabilities", 0),
            "intangible_assets": balance.get("intangibleAssets", 0),
            "goodwill": balance.get("goodwill", 0),
            "fetched_at": datetime.datetime.utcnow().isoformat() + "Z",
        }

    def fetch_market_data(self, symbol: str) -> Optional[Dict]:
        """1 API call: enterprise-values bundles price, market cap, debt, cash, EV."""
        ev = self._get("enterprise-values", symbol=symbol, limit=1)
        time.sleep(REQUEST_DELAY_SECONDS)
        if not ev:
            return None
        ev = ev[0]
        return {
            "market_cap": ev.get("marketCapitalization", 0),
            "enterprise_value": ev.get("enterpriseValue", 0),
        }

    def fetch_returns(self, symbol: str) -> Dict:
        """1 API call: historical daily prices, used to compute 1d/1m/1y % change."""
        hist = self._get("historical-price-eod/full", symbol=symbol)
        time.sleep(REQUEST_DELAY_SECONDS)
        if not hist:
            return {"return_1d": None, "return_1m": None, "return_1y": None}

        # Stable API returns a flat array, most-recent-first.
        closes = [row["close"] for row in hist if "close" in row]

        def pct_change(past_index):
            if len(closes) > past_index and closes[past_index]:
                return round((closes[0] - closes[past_index]) / closes[past_index] * 100, 2)
            return None

        return {
            "return_1d": pct_change(1),
            "return_1m": pct_change(21),
            "return_1y": pct_change(252),
        }

    @staticmethod
    def is_common_stock(symbol: str, name: str) -> bool:
        """Best-effort filter for junk tickers (preferred shares, notes, etc.).

        Preferred/debt issues are often named with keywords like "Preferred" or
        "Depositary", but just as often just have a bare coupon rate tacked on
        (e.g. "Prudential Financial, Inc. 5.95") with no keyword at all — so a
        numeric-rate pattern is checked too.
        """
        if not re.fullmatch(r"[A-Z]{1,5}", symbol):
            return False
        name_lower = (name or "").lower()
        junk_terms = ["preferred", "depositary", "trust pfd", "notes", "debenture", "%"]
        if any(term in name_lower for term in junk_terms):
            return False
        if re.search(r"\d+\.\d+", name or ""):  # e.g. "... 5.95" coupon rate
            return False
        return True

    @staticmethod
    def calculate_magic_formula_metrics(fundamentals: Dict, market_data: Dict) -> Optional[Dict]:
        try:
            ebit = fundamentals["ebit"]
            enterprise_value = market_data["enterprise_value"]

            net_working_capital = (
                fundamentals["total_current_assets"] - fundamentals["total_current_liabilities"]
            )
            net_fixed_assets = (
                fundamentals["total_assets"]
                - fundamentals["total_current_assets"]
                - fundamentals["intangible_assets"]
                - fundamentals["goodwill"]
            )

            earnings_yield = (ebit / enterprise_value * 100) if enterprise_value > 0 else 0
            capital_employed = net_working_capital + net_fixed_assets
            return_on_capital = (ebit / capital_employed * 100) if capital_employed > 0 else 0

            return {
                "symbol": fundamentals["symbol"],
                "name": fundamentals["name"],
                "sector": fundamentals["sector"],
                "market_cap": market_data["market_cap"],
                "earnings_yield": round(earnings_yield, 2),
                "return_on_capital": round(return_on_capital, 2),
            }
        except (KeyError, TypeError, ZeroDivisionError) as e:
            print(f"Error calculating metrics for {fundamentals.get('symbol', 'unknown')}: {e}")
            return None


# --- Orchestration ------------------------------------------------------------

def is_stale(entry: Optional[Dict], now: datetime.datetime) -> bool:
    if not entry:
        return True
    fetched_at = datetime.datetime.fromisoformat(entry["fetched_at"].replace("Z", ""))
    return (now - fetched_at).days >= FUNDAMENTALS_MAX_AGE_DAYS


def main():
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        raise SystemExit("FMP_API_KEY not set")

    calc = MagicFormulaCalculator(api_key)
    now = datetime.datetime.utcnow()

    universe: List[str] = load_json(UNIVERSE_FILE, [])
    if not universe:
        raise SystemExit(f"No tickers found in {UNIVERSE_FILE} — nothing to screen.")
    print(f"Universe: {len(universe)} symbols")

    # --- Step 1: rotate fundamentals refresh for stale/missing symbols ---
    cache: Dict[str, Dict] = load_json(FUNDAMENTALS_CACHE_FILE, {})
    stale_symbols = [s for s in universe if is_stale(cache.get(s), now)][:FUNDAMENTALS_REFRESH_BUDGET]
    print(f"Refreshing fundamentals for {len(stale_symbols)} symbol(s) this run "
          f"({len(universe) - len([s for s in universe if is_stale(cache.get(s), now)])} already fresh)")

    for symbol in stale_symbols:
        data = calc.fetch_fundamentals(symbol)
        if data:
            cache[symbol] = data
        else:
            print(f"  Skipping {symbol} — fundamentals fetch failed")

    save_json(FUNDAMENTALS_CACHE_FILE, cache)

    # --- Step 2: daily EV/price pull + ranking for every symbol with cached fundamentals ---
    rows = []
    cached_symbols = [s for s in universe if s in cache]
    print(f"Scoring {len(cached_symbols)} symbol(s) with cached fundamentals "
          f"({len(universe) - len(cached_symbols)} not yet cached — will appear in a future run)")

    for symbol in cached_symbols:
        fundamentals = cache[symbol]

        if not calc.is_common_stock(symbol, fundamentals.get("name", "")):
            continue
        if fundamentals.get("sector") in SECTOR_EXCLUDE:
            continue

        market_data = calc.fetch_market_data(symbol)
        if not market_data or market_data["market_cap"] < MIN_MARKET_CAP:
            continue

        metrics = calc.calculate_magic_formula_metrics(fundamentals, market_data)
        if metrics and metrics["earnings_yield"] > 0 and metrics["return_on_capital"] > 0:
            rows.append(metrics)

    print(f"{len(rows)} stock(s) passed screening")

    df = pd.DataFrame(rows)
    if df.empty:
        print("No stocks passed screening — refusing to overwrite existing data.")
        return

    df["ey_rank"] = df["earnings_yield"].rank(ascending=False)
    df["roc_rank"] = df["return_on_capital"].rank(ascending=False)
    df["combined_rank"] = df["ey_rank"] + df["roc_rank"]
    df = df.sort_values("combined_rank").reset_index(drop=True)

    # --- Step 3: historical returns only for the final top-N (budget-limited) ---
    top_symbols = df.head(TOP_N_FOR_RETURNS)["symbol"].tolist()
    print(f"Fetching historical returns for top {len(top_symbols)} ranked stock(s)")
    returns_map = {symbol: calc.fetch_returns(symbol) for symbol in top_symbols}

    for col in ["return_1d", "return_1m", "return_1y"]:
        df[col] = df["symbol"].map(lambda s: returns_map.get(s, {}).get(col))

    output_columns = [
        "symbol", "name", "sector", "market_cap",
        "earnings_yield", "return_on_capital",
        "return_1d", "return_1m", "return_1y",
        "ey_rank", "roc_rank", "combined_rank",
    ]
    df = df[output_columns]

    df.to_csv(RESULTS_CSV, index=False)
    df.to_json(RESULTS_JSON, orient="records", indent=2)
    save_json(LAST_UPDATED_FILE, {"generated_at": now.isoformat() + "Z"})

    print("=" * 80)
    print(f"Saved {len(df)} ranked stock(s) to {RESULTS_JSON} / {RESULTS_CSV}")
    print(f"Average Earnings Yield: {df['earnings_yield'].mean():.2f}%")
    print(f"Average Return on Capital: {df['return_on_capital'].mean():.2f}%")
    print("=" * 80)


if __name__ == "__main__":
    main()