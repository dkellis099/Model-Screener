# Magic Formula Stock Screener

A full-stack tool that screens US large-cap stocks using Joel Greenblatt's "Magic Formula" — an automated data pipeline pulls fundamentals daily, ranks companies by profitability and valuation, and serves the results through a React dashboard.

**Live site:** [model-screener.vercel.app](https://model-screener.vercel.app)

> **This is a research tool, not investment advice.** It narrows a universe of stocks down to a shortlist worth researching further — it does not tell you what to buy. See [Limitations](#limitations--methodology-notes) below before using it to make investment decisions.

---

## What it does

Joel Greenblatt's Magic Formula (from *The Little Book That Beats the Market*) ranks companies on two metrics:

- **Earnings Yield** — `EBIT / Enterprise Value`. How much operating profit a company generates relative to what it would cost to buy the whole business (equity + debt, minus cash). Higher means cheaper relative to earnings.
- **Return on Capital** — `EBIT / (Net Working Capital + Net Fixed Assets)`. How efficiently a company turns its invested capital into profit. Higher means more efficient.

Each company is ranked on both metrics independently, and the two ranks are summed — lowest combined rank wins. The idea: buy good businesses (high ROC) at good prices (high earnings yield), avoiding the trap of cheap-but-bad or good-but-expensive.

## Architecture

```
backend/Model_Generator.py   → Python script that pulls fundamentals from the
                                Financial Modeling Prep API, computes Magic
                                Formula rankings, and writes results as JSON/CSV.

.github/workflows/main.yml   → GitHub Actions workflow that runs the script on
                                a schedule and commits the refreshed data.

public/                      → Static output consumed by the frontend
                                (magic_formula_results.json, last_updated.json).

src/                         → React (Vite) dashboard: sortable/filterable
                                table, sector filter, per-stock price chart.

api/chart.js                 → Vercel serverless function that proxies chart
                                requests to FMP, keeping the API key server-side.
```

**Stack:** React 18, Vite, Tailwind CSS, Recharts, Python (pandas/requests), GitHub Actions, Vercel.

## Data pipeline

Financial data is sourced from the [Financial Modeling Prep API](https://financialmodelingprep.com). Because the pipeline runs on a free-tier API key (250 requests/day), it does **not** use FMP's dynamic stock-screener or S&P 500 constituent endpoints (both are paid-tier only) — instead it screens a curated static list of large-cap tickers, refreshing fundamentals (which change quarterly) on a slower cadence than price/return data (which refreshes daily). This keeps the whole pipeline running for free while staying inside the request budget.

Every run writes a `generated_at` timestamp alongside the results, which the frontend displays as "Last updated" — if the automation ever silently breaks, the site will show a stale date rather than falsely claiming to be current.

## Running locally

```bash
git clone https://github.com/dkellis099/Model-Screener.git
cd Model-Screener
npm install
npm run dev
```

To regenerate the stock data yourself, you'll need a free [FMP API key](https://site.financialmodelingprep.com/):

```bash
pip install -r backend/requirements.txt   # requests, pandas
FMP_API_KEY=your_key_here python backend/Model_Generator.py
```

## Running tests

```bash
pip install pytest
pytest tests/
```

## Limitations & methodology notes

Worth knowing before treating this as anything more than a research starting point:

- **Not a live trading signal.** Greenblatt's original methodology is designed around holding a basket of ~20-30 stocks for roughly a year and rebalancing annually — not reacting to day-to-day rank changes.
- **Single data source.** All fundamentals come from one provider (FMP). No cross-validation against other sources; free/low-tier fundamental data occasionally includes stale or misclassified tickers (e.g. preferred shares, retired symbols).
- **Sector exclusions.** Greenblatt's original screen excludes financial and utility companies, since EBIT/capital-employed math doesn't translate cleanly to their balance sheets. Confirm sector filtering is applied before relying on results that include those sectors.
- **No portfolio construction logic.** This tool ranks and filters candidates; it does not handle position sizing, diversification limits, tax considerations, or rebalancing — all of which matter for actually deploying capital.
- **Point-in-time lag.** Fundamentals reflect the most recently *filed* financial statements, which can lag current company reality by up to a quarter.

## Disclaimer

Educational and informational purposes only. Not investment advice. Always do your own research and consult a licensed financial advisor before making investment decisions.