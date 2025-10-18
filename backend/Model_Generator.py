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
    
    def screen_stocks(self, symbols: List[str], min_market_cap: float = 50e6) -> pd.DataFrame:
        """Screen stocks and calculate Magic Formula rankings"""
        stock_metrics = []
        
        print(f"Screening {len(symbols)} stocks...")
        for i, symbol in enumerate(symbols):
            if i % 10 == 0:
                print(f"Progress: {i}/{len(symbols)}")
                time.sleep(1)  # Rate limiting
            
            stock_data = self.get_stock_data(symbol)
            if stock_data and stock_data['market_cap'] >= min_market_cap:
                metrics = self.calculate_magic_formula_metrics(stock_data)
                if metrics and metrics['earnings_yield'] > 0 and metrics['return_on_capital'] > 0:
                    stock_metrics.append(metrics)
        
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
            'ey_rank', 'roc_rank', 'combined_rank'
        ]
        
        return df[output_columns].reset_index(drop=True)
    
    def get_top_stocks(self, limit: int = 30) -> pd.DataFrame:
        """Get top ranked stocks using Magic Formula"""
        symbols = self.get_sp500_symbols()
        print(f"Found {len(symbols)} S&P 500 stocks")
        
        results = self.screen_stocks(symbols)
        return results.head(limit)

# Usage example
if __name__ == "__main__":
    # Replace with your API key
    API_KEY = "vPO3Q9TJPSQQuIGLSDfEJB1mtuJazaYP"
    
    calculator = MagicFormulaCalculator(API_KEY)
    
    # Get top 30 stocks
    top_stocks = calculator.get_top_stocks(limit=30)
    
    # Display results
    print("\n" + "="*80)
    print("MAGIC FORMULA TOP 30 STOCKS")
    print("="*80)
    print(top_stocks.to_string(index=False))
    
    # Save to CSV
    top_stocks.to_csv('magic_formula_results.csv', index=False)
    print("\nResults saved to magic_formula_results.csv")
    
    # Save to JSON for web display
    top_stocks.to_json('magic_formula_results.json', orient='records', indent=2)
    print("Results saved to magic_formula_results.json")