"""
Unit tests for the Magic Formula ranking logic in backend/Model_Generator.py.

Run with:
    pip install -r backend/requirements.txt pytest
    pytest tests/

NOTE: this replaces the earlier version of this test file, which tested the
pre-rewrite API (a single calculate_magic_formula_metrics(stock_data) method
and a screen_stocks() method that made live network calls internally). The
rewritten pipeline splits fundamentals (cached, quarterly) from market data
(fetched daily), so calculate_magic_formula_metrics now takes two dicts and
is a staticmethod — no network access needed to test it at all.
"""

import datetime
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from Model_Generator import MagicFormulaCalculator, is_stale  # noqa: E402


# ---------------------------------------------------------------------------
# calculate_magic_formula_metrics
# ---------------------------------------------------------------------------

def test_calculate_metrics_basic_case():
    fundamentals = {
        "symbol": "TEST",
        "name": "Test Inc.",
        "sector": "Technology",
        "ebit": 1_000_000,
        "total_assets": 8_000_000,
        "total_current_assets": 3_000_000,
        "total_current_liabilities": 1_000_000,
        "intangible_assets": 500_000,
        "goodwill": 500_000,
    }
    market_data = {"market_cap": 12_000_000, "enterprise_value": 10_000_000}
    # EY = 1,000,000 / 10,000,000 = 10%
    # net_working_capital = 3,000,000 - 1,000,000 = 2,000,000
    # net_fixed_assets = 8,000,000 - 3,000,000 - 500,000 - 500,000 = 4,000,000
    # capital_employed = 6,000,000 -> ROC = 1,000,000 / 6,000,000 = 16.67%

    result = MagicFormulaCalculator.calculate_magic_formula_metrics(fundamentals, market_data)

    assert result["earnings_yield"] == 10.0
    assert result["return_on_capital"] == pytest.approx(16.67, abs=0.01)
    assert result["symbol"] == "TEST"
    assert result["market_cap"] == 12_000_000


def test_calculate_metrics_zero_enterprise_value_does_not_divide_by_zero():
    fundamentals = {
        "symbol": "ZERO_EV", "name": "Zero EV Inc.", "sector": "Technology",
        "ebit": 1_000_000, "total_assets": 5_000_000, "total_current_assets": 2_000_000,
        "total_current_liabilities": 500_000, "intangible_assets": 0, "goodwill": 0,
    }
    market_data = {"market_cap": 1_000_000, "enterprise_value": 0}

    result = MagicFormulaCalculator.calculate_magic_formula_metrics(fundamentals, market_data)

    assert result["earnings_yield"] == 0
    assert result["return_on_capital"] > 0


def test_calculate_metrics_zero_capital_employed_does_not_divide_by_zero():
    fundamentals = {
        "symbol": "ZERO_CAP", "name": "Zero Cap Inc.", "sector": "Technology",
        "ebit": 1_000_000, "total_assets": 1_000_000, "total_current_assets": 1_000_000,
        "total_current_liabilities": 0, "intangible_assets": 500_000, "goodwill": 500_000,
    }
    market_data = {"market_cap": 5_000_000, "enterprise_value": 5_000_000}

    result = MagicFormulaCalculator.calculate_magic_formula_metrics(fundamentals, market_data)

    assert result["return_on_capital"] == 0


def test_calculate_metrics_negative_ebit_produces_negative_yield():
    fundamentals = {
        "symbol": "LOSS", "name": "Loss Inc.", "sector": "Technology",
        "ebit": -500_000, "total_assets": 5_000_000, "total_current_assets": 2_000_000,
        "total_current_liabilities": 500_000, "intangible_assets": 0, "goodwill": 0,
    }
    market_data = {"market_cap": 10_000_000, "enterprise_value": 10_000_000}

    result = MagicFormulaCalculator.calculate_magic_formula_metrics(fundamentals, market_data)

    assert result["earnings_yield"] < 0
    assert result["return_on_capital"] < 0


def test_calculate_metrics_missing_field_returns_none():
    incomplete_fundamentals = {"symbol": "BROKEN", "ebit": 1_000_000}
    market_data = {"market_cap": 1_000_000, "enterprise_value": 1_000_000}

    result = MagicFormulaCalculator.calculate_magic_formula_metrics(incomplete_fundamentals, market_data)

    assert result is None


# ---------------------------------------------------------------------------
# is_common_stock — junk ticker filter
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("symbol,name,expected", [
    ("AAPL", "Apple Inc.", True),
    ("MSFT", "Microsoft Corporation", True),
    ("PRH", "Prudential Financial, Inc. 5.95", False),   # preferred/debt-like name
    ("BRK.B", "Berkshire Hathaway Inc.", False),          # punctuation in symbol
    ("XYZ", "Some Trust Preferred Fund", False),          # 'preferred' in name
    ("ABCDEF", "Too Long Ticker Corp", False),            # >5 chars
])
def test_is_common_stock(symbol, name, expected):
    assert MagicFormulaCalculator.is_common_stock(symbol, name) is expected


# ---------------------------------------------------------------------------
# is_stale — fundamentals cache aging logic
# ---------------------------------------------------------------------------

def test_is_stale_missing_entry_is_stale():
    assert is_stale(None, datetime.datetime.utcnow()) is True


def test_is_stale_recent_entry_is_not_stale():
    now = datetime.datetime.utcnow()
    entry = {"fetched_at": (now - datetime.timedelta(days=1)).isoformat() + "Z"}
    assert is_stale(entry, now) is False


def test_is_stale_old_entry_is_stale():
    now = datetime.datetime.utcnow()
    entry = {"fetched_at": (now - datetime.timedelta(days=45)).isoformat() + "Z"}
    assert is_stale(entry, now) is True


def test_is_stale_boundary_at_max_age_is_stale():
    now = datetime.datetime.utcnow()
    entry = {"fetched_at": (now - datetime.timedelta(days=30)).isoformat() + "Z"}
    assert is_stale(entry, now) is True