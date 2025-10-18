import React, { useState, useMemo } from 'react';
import { TrendingUp, Filter, Download, Info } from 'lucide-react';

// Sample data - replace this with your actual JSON data
const sampleStocks = [
  { symbol: "OMC", name: "Omnicom Group Inc.", sector: "Communication Services", market_cap: 15017400000, earnings_yield: 12.08, return_on_capital: 110.66, ey_rank: 13.0, roc_rank: 25.0, combined_rank: 38.0 },
  { symbol: "MO", name: "Altria Group, Inc.", sector: "Consumer Defensive", market_cap: 109276900000, earnings_yield: 10.07, return_on_capital: 173.53, ey_rank: 34.0, roc_rank: 11.0, combined_rank: 45.0 },
  { symbol: "CLX", name: "The Clorox Company", sector: "Consumer Defensive", market_cap: 14647060000, earnings_yield: 11.22, return_on_capital: 106.55, ey_rank: 19.0, roc_rank: 29.0, combined_rank: 48.0 },
  { symbol: "HPQ", name: "HP Inc.", sector: "Technology", market_cap: 25582790000, earnings_yield: 9.00, return_on_capital: 299.22, ey_rank: 56.0, roc_rank: 6.0, combined_rank: 62.0 },
  { symbol: "GIS", name: "General Mills, Inc.", sector: "Consumer Defensive", market_cap: 26600060000, earnings_yield: 7.41, return_on_capital: 131.46, ey_rank: 95.0, roc_rank: 19.0, combined_rank: 114.0 },
];

const MagicFormulaDashboard = () => {
  const [selectedSector, setSelectedSector] = useState('All');
  const [showInfo, setShowInfo] = useState(false);
  
  // In production, load this from your JSON file
  const stocks = sampleStocks;
  
  const sectors = useMemo(() => {
    const uniqueSectors = [...new Set(stocks.map(s => s.sector))];
    return ['All', ...uniqueSectors.sort()];
  }, [stocks]);
  
  const filteredStocks = useMemo(() => {
    if (selectedSector === 'All') return stocks;
    return stocks.filter(s => s.sector === selectedSector);
  }, [stocks, selectedSector]);
  
  const formatMarketCap = (value) => {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value}`;
  };
  
  const downloadCSV = () => {
    const headers = ['Rank', 'Symbol', 'Company', 'Sector', 'Market Cap', 'Earnings Yield %', 'ROC %'];
    const rows = filteredStocks.map((stock, idx) => [
      idx + 1,
      stock.symbol,
      stock.name,
      stock.sector,
      formatMarketCap(stock.market_cap),
      stock.earnings_yield,
      stock.return_on_capital
    ]);
    
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'magic_formula_stocks.csv';
    a.click();
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <TrendingUp className="w-10 h-10 text-emerald-400" />
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-emerald-400 to-blue-500 bg-clip-text text-transparent">
              Magic Formula Stock Screener
            </h1>
          </div>
          <p className="text-slate-400 text-lg mb-2">
            Top-ranked stocks using Joel Greenblatt's proven investment strategy
          </p>
          <p className="text-slate-500 text-sm">
            Last updated: {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
          </p>
        </div>

        {/* Info Modal */}
        {showInfo && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={() => setShowInfo(false)}>
            <div className="bg-slate-800 rounded-lg p-6 max-w-2xl" onClick={e => e.stopPropagation()}>
              <h3 className="text-2xl font-bold mb-4">About the Magic Formula</h3>
              <div className="space-y-3 text-slate-300">
                <p>The Magic Formula is a quantitative investment strategy developed by Joel Greenblatt that ranks stocks based on two key metrics:</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li><strong className="text-emerald-400">Earnings Yield:</strong> Measures how much a company earns relative to its value (EBIT / Enterprise Value)</li>
                  <li><strong className="text-blue-400">Return on Capital:</strong> Measures how efficiently a company uses its capital (EBIT / Capital Employed)</li>
                </ul>
                <p className="text-sm mt-4 text-slate-400">
                  <strong>Disclaimer:</strong> This tool is for educational and informational purposes only. It does not constitute investment advice. Always conduct your own research and consult with a financial advisor before making investment decisions.
                </p>
              </div>
              <button 
                onClick={() => setShowInfo(false)}
                className="mt-6 w-full bg-emerald-500 hover:bg-emerald-600 text-white py-2 rounded-lg transition-colors"
              >
                Got it
              </button>
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="bg-slate-800 rounded-lg p-4 mb-6 flex flex-wrap gap-4 items-center justify-between">
          <div className="flex items-center gap-3">
            <Filter className="w-5 h-5 text-slate-400" />
            <select 
              value={selectedSector}
              onChange={(e) => setSelectedSector(e.target.value)}
              className="bg-slate-700 text-white px-4 py-2 rounded-lg border border-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              {sectors.map(sector => (
                <option key={sector} value={sector}>{sector}</option>
              ))}
            </select>
            <span className="text-slate-400 text-sm">
              {filteredStocks.length} stocks
            </span>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={() => setShowInfo(true)}
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
            >
              <Info className="w-4 h-4" />
              About
            </button>
            <button
              onClick={downloadCSV}
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg transition-colors"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-gradient-to-br from-emerald-500/20 to-emerald-600/20 border border-emerald-500/30 rounded-lg p-4">
            <div className="text-emerald-400 text-sm font-medium mb-1">Top Earnings Yield</div>
            <div className="text-2xl font-bold">{filteredStocks[0]?.earnings_yield}%</div>
            <div className="text-slate-400 text-sm mt-1">{filteredStocks[0]?.symbol}</div>
          </div>
          
          <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/20 border border-blue-500/30 rounded-lg p-4">
            <div className="text-blue-400 text-sm font-medium mb-1">Top Return on Capital</div>
            <div className="text-2xl font-bold">{filteredStocks[0]?.return_on_capital}%</div>
            <div className="text-slate-400 text-sm mt-1">{filteredStocks[0]?.symbol}</div>
          </div>
          
          <div className="bg-gradient-to-br from-purple-500/20 to-purple-600/20 border border-purple-500/30 rounded-lg p-4">
            <div className="text-purple-400 text-sm font-medium mb-1">Average Market Cap</div>
            <div className="text-2xl font-bold">
              {formatMarketCap(filteredStocks.reduce((sum, s) => sum + s.market_cap, 0) / filteredStocks.length)}
            </div>
            <div className="text-slate-400 text-sm mt-1">Across {filteredStocks.length} stocks</div>
          </div>
        </div>

        {/* Stock Table */}
        <div className="bg-slate-800 rounded-lg overflow-hidden border border-slate-700">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-900">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Rank</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Symbol</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Company</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">Sector</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase tracking-wider">Market Cap</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-emerald-400 uppercase tracking-wider">Earnings Yield</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-blue-400 uppercase tracking-wider">ROC</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {filteredStocks.map((stock, index) => (
                  <tr key={stock.symbol} className="hover:bg-slate-700/50 transition-colors">
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${
                        index < 3 ? 'bg-gradient-to-br from-yellow-400 to-orange-500 text-slate-900' : 'bg-slate-700 text-slate-400'
                      } font-bold text-sm`}>
                        {index + 1}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <div className="font-mono font-bold text-emerald-400">{stock.symbol}</div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="text-sm font-medium">{stock.name}</div>
                    </td>
                    <td className="px-4 py-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-700 text-slate-300">
                        {stock.sector}
                      </span>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-right text-sm">
                      {formatMarketCap(stock.market_cap)}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-right">
                      <span className="font-semibold text-emerald-400">{stock.earnings_yield.toFixed(2)}%</span>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-right">
                      <span className="font-semibold text-blue-400">{stock.return_on_capital.toFixed(2)}%</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-slate-500 text-sm">
          <p>Based on Joel Greenblatt's <em>The Little Book That Beats the Market</em></p>
          <p className="mt-2">Data sourced from Financial Modeling Prep • Not investment advice</p>
        </div>
      </div>
    </div>
  );
};

export default MagicFormulaDashboard;