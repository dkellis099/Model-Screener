import requests
import pandas as pd
import time
from typing import List, Dict
import json

class MagicFormulaCalculator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://financialmodelingprep.com/api/v3"
        
    def get_sp500_symbols(self) -> List[str]:
        """Fetch S&P 500 stock symbols"""
        url = f"{self.base_url}/sp500_constituent?apikey={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return [item['symbol'] for item in data]
        return []
    
    def get_stock_screener(self, market_cap_min: int = 50000000, limit: int = 3000) -> List[str]:
        """Fetch stocks using stock screener - gets largest stocks by market cap"""
        url = f"{self.base_url}/stock-screener?marketCapMoreThan={market_cap_min}&limit={limit}&apikey={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Sort by market cap and return symbols
            sorted_stocks = sorted(data, key=lambda x: x.get('marketCap', 0), reverse=True)
            return [item['symbol'] for item in sorted_stocks[:limit]]
        return []
    
    def get_all_tradable_stocks(self) -> List[str]:
        """Get all tradable stocks, filter to largest ~3000 by attempting to get market caps"""
        try:
            # Get all available stock symbols
            url = f"{self.base_url}/stock/list?apikey={self.api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                # Filter for US exchanges and common stock types
                us_stocks = [
                    item['symbol'] for item in data 
                    if item.get('exchangeShortName') in ['NASDAQ', 'NYSE', 'AMEX']
                    and item.get('type') == 'stock'
                    and len(item['symbol']) <= 5  # Filter out weird tickers
                ]
                print(f"Found {len(us_stocks)} US stocks")
                return us_stocks[:3000]  # Limit to first 3000
        except Exception as e:
            print(f"Error fetching stock list: {str(e)}")
        return []
    
    def get_stock_data(self, symbol: str) -> Dict:
        """Fetch financial data for a single stock"""
        try:
            # Get income statement for EBIT
            income_url = f"{self.base_url}/income-statement/{symbol}?limit=1&apikey={self.api_key}"
            income_response = requests.get(income_url)
            
            # Get balance sheet for working capital and fixed assets
            balance_url = f"{self.base_url}/balance-sheet-statement/{symbol}?limit=1&apikey={self.api_key}"
            balance_response = requests.get(balance_url)
            
            # Get key metrics for enterprise value
            metrics_url = f"{self.base_url}/key-metrics/{symbol}?limit=1&apikey={self.api_key}"
            metrics_response = requests.get(metrics_url)
            
            # Get company profile for market cap
            profile_url = f"{self.base_url}/profile/{symbol}?apikey={self.api_key}"
            profile_response = requests.get(profile_url)
            
            if all(r.status_code == 200 for r in [income_response, balance_response, metrics_response, profile_response]):
                income = income_response.json()[0] if income_response.json() else {}
                balance = balance_response.json()[0] if balance_response.json() else {}
                metrics = metrics_response.json()[0] if metrics_response.json() else {}
                profile = profile_response.json()[0] if profile_response.json() else {}
                
                return {
                    'symbol': symbol,
                    'name': profile.get('companyName', ''),
                    'sector': profile.get('sector', ''),
                    'market_cap': profile.get('mktCap', 0),
                    'ebit': income.get('operatingIncome', 0),  # EBIT approximation
                    'enterprise_value': metrics.get('enterpriseValue', 0),
                    'total_assets': balance.get('totalAssets', 0),
                    'total_current_assets': balance.get('totalCurrentAssets', 0),
                    'total_current_liabilities': balance.get('totalCurrentLiabilities', 0),
                    'intangible_assets': balance.get('intangibleAssets', 0),
                    'goodwill': balance.get('goodwill', 0),
                }
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
        
        return None
    
    def calculate_magic_formula_metrics(self, stock_data: Dict) -> Dict:
        """Calculate Earnings Yield and Return on Capital"""
        try:
            ebit = stock_data['ebit']
            enterprise_value = stock_data['enterprise_value']
            
            # Calculate Net Working Capital
            net_working_capital = (stock_data['total_current_assets'] - 
                                 stock_data['total_current_liabilities'])
            
            # Calculate Net Fixed Assets (Tangible Assets)
            net_fixed_assets = (stock_data['total_assets'] - 
                              stock_data['total_current_assets'] - 
                              stock_data['intangible_assets'] - 
                              stock_data['goodwill'])
            
            # Calculate Earnings Yield (higher is better)
            earnings_yield = (ebit / enterprise_value * 100) if enterprise_value > 0 else 0
            
            # Calculate Return on Capital (higher is better)
            capital_employed = net_working_capital + net_fixed_assets
            return_on_capital = (ebit / capital_employed * 100) if capital_employed > 0 else 0
            
            return {
                **stock_data,
                'earnings_yield': round(earnings_yield, 2),
                'return_on_capital': round(return_on_capital, 2),
                'net_working_capital': net_working_capital,
                'net_fixed_assets': net_fixed_assets
            }
            
        except Exception as e:
            print(f"Error calculating metrics for {stock_data.get('symbol', 'unknown')}: {str(e)}")
            return None
    
    def screen_stocks(self, symbols: List[str], min_market_cap: float = 50e6, max_stocks: int = None) -> pd.DataFrame:
        """Screen stocks and calculate Magic Formula rankings"""
        stock_metrics = []
        total = len(symbols)
        
        print(f"Screening {total} stocks...")
        print(f"This may take a while. Estimated time: {total * 0.5 / 60:.1f} minutes")
        
        for i, symbol in enumerate(symbols):
            # Progress update every 10 stocks
            if i % 10 == 0:
                print(f"Progress: {i}/{total} ({i/total*100:.1f}%) - {len(stock_metrics)} stocks passed screening")
                time.sleep(0.5)  # Rate limiting
            
            stock_data = self.get_stock_data(symbol)
            if stock_data and stock_data['market_cap'] >= min_market_cap:
                metrics = self.calculate_magic_formula_metrics(stock_data)
                if metrics and metrics['earnings_yield'] > 0 and metrics['return_on_capital'] > 0:
                    # Calculate returns
                    returns = self.calculate_returns(symbol)
                    metrics.update(returns)
                    stock_metrics.append(metrics)
                    
                    # Early exit if we have enough stocks and max_stocks is set
                    if max_stocks and len(stock_metrics) >= max_stocks * 3:
                        print(f"Collected {len(stock_metrics)} stocks, stopping early")
                        break
        
        print(f"\nScreening complete! Found {len(stock_metrics)} qualifying stocks")
        
        # Create DataFrame
        df = pd.DataFrame(stock_metrics)
        
        if df.empty:
            return df
        
        # Rank stocks (1 = best)
        df['ey_rank'] = df['earnings_yield'].rank(ascending=False)
        df['roc_rank'] = df['return_on_capital'].rank(ascending=False)
        
        # Combined rank (lower is better)
        df['combined_rank'] = df['ey_rank'] + df['roc_rank']
        
        # Sort by combined rank
        df = df.sort_values('combined_rank')
        
        # Select relevant columns
        output_columns = [
            'symbol', 'name', 'sector', 'market_cap',
            'earnings_yield', 'return_on_capital', 
            'return_1d', 'return_1m', 'return_1y',
            'ey_rank', 'roc_rank', 'combined_rank'
        ]
        
        return df[output_columns].reset_index(drop=True)
    
    def get_stock_price_history(self, symbol: str, days: int = 365) -> List[Dict]:
        """Fetch historical price data for stock chart and returns"""
        try:
            url = f"{self.base_url}/historical-price-full/{symbol}?apikey={self.api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if 'historical' in data:
                    historical = data['historical'][:days]
                    return [{'date': item['date'], 'close': item['close']} for item in reversed(historical)]
        except Exception as e:
            print(f"Error fetching price history for {symbol}: {str(e)}")
        return []
    
    def calculate_returns(self, symbol: str) -> Dict:
        """Calculate 1-day, 1-month, and 1-year returns"""
        try:
            url = f"{self.base_url}/historical-price-full/{symbol}?apikey={self.api_key}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if 'historical' in data and len(data['historical']) > 0:
                    historical = data['historical']
                    current_price = historical[0]['close']
                    
                    # 1-day return
                    day_1_return = None
                    if len(historical) > 1:
                        day_1_price = historical[1]['close']
                        day_1_return = ((current_price - day_1_price) / day_1_price) * 100
                    
                    # 1-month return (approximately 21 trading days)
                    month_1_return = None
                    if len(historical) > 21:
                        month_1_price = historical[21]['close']
                        month_1_return = ((current_price - month_1_price) / month_1_price) * 100
                    
                    # 1-year return (approximately 252 trading days)
                    year_1_return = None
                    if len(historical) > 252:
                        year_1_price = historical[252]['close']
                        year_1_return = ((current_price - year_1_price) / year_1_price) * 100
                    
                    return {
                        'return_1d': round(day_1_return, 2) if day_1_return is not None else None,
                        'return_1m': round(month_1_return, 2) if month_1_return is not None else None,
                        'return_1y': round(year_1_return, 2) if year_1_return is not None else None
                    }
        except Exception as e:
            print(f"Error calculating returns for {symbol}: {str(e)}")
        
        return {'return_1d': None, 'return_1m': None, 'return_1y': None}
    
    def get_top_stocks(self, universe: str = 'sp500', limit: int = 100) -> pd.DataFrame:
        """Get top ranked stocks using Magic Formula
        
        Args:
            universe: 'sp500', 'large_cap' (3000 biggest), or 'all'
            limit: Number of top stocks to return
        """
        if universe == 'sp500':
            print("Using S&P 500 universe (~500 stocks)")
            symbols = self.get_sp500_symbols()
        elif universe == 'large_cap':
            print("Using Large Cap universe (~3000 biggest stocks)")
            symbols = self.get_stock_screener(market_cap_min=50000000, limit=3000)
        elif universe == 'all':
            print("Using All tradable US stocks")
            symbols = self.get_all_tradable_stocks()
        else:
            print("Unknown universe, defaulting to S&P 500")
            symbols = self.get_sp500_symbols()
        
        print(f"Found {len(symbols)} symbols in universe")
        
        results = self.screen_stocks(symbols, max_stocks=limit)
        return results.head(limit)

# Usage example
if __name__ == "__main__":
    # Get API key from environment variable (for GitHub Actions) or use hardcoded value
    import os
    import sys
    
    API_KEY = os.getenv('FMP_API_KEY', 'vPO3Q9TJPSQQuIGLSDfEJB1mtuJazaYP')
    
    # Parse command line arguments
    universe = 'large_cap'  # Default to S&P 500
    limit = 200  # Default to top 100
    
    if len(sys.argv) > 1:
        universe = sys.argv[1]  # sp500, large_cap, or all
    if len(sys.argv) > 2:
        limit = int(sys.argv[2])
    
    print(f"\n{'='*80}")
    print(f"MAGIC FORMULA STOCK SCREENER")
    print(f"Universe: {universe.upper()}")
    print(f"Target stocks: {limit}")
    print(f"{'='*80}\n")
    
    calculator = MagicFormulaCalculator(API_KEY)
    
    # Get top stocks from selected universe
    top_stocks = calculator.get_top_stocks(universe=universe, limit=limit)
    
    # Display results
    print("\n" + "="*80)
    print(f"MAGIC FORMULA TOP {len(top_stocks)} STOCKS")
    print("="*80)
    print(top_stocks.head(30).to_string(index=False))  # Print first 30
    
    # Save to CSV
    top_stocks.to_csv('magic_formula_results.csv', index=False)
    print(f"\nResults saved to magic_formula_results.csv ({len(top_stocks)} stocks)")
    
    # Save to JSON for web display
    top_stocks.to_json('magic_formula_results.json', orient='records', indent=2)
    print(f"Results saved to magic_formula_results.json ({len(top_stocks)} stocks)")
    
    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print(f"Total stocks screened: {len(top_stocks)}")
    print(f"Average Earnings Yield: {top_stocks['earnings_yield'].mean():.2f}%")
    print(f"Average Return on Capital: {top_stocks['return_on_capital'].mean():.2f}%")
    if 'return_1y' in top_stocks.columns:
        valid_returns = top_stocks['return_1y'].dropna()
        if len(valid_returns) > 0:
            print(f"Average 1-Year Return: {valid_returns.mean():.2f}%")
    print("="*80)
