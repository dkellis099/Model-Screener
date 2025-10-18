import React, { useState, useEffect, useMemo } from 'react';
import { TrendingUp, Filter, Download, Info, X, BarChart3 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const MagicFormulaDashboard = () => {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSector, setSelectedSector] = useState('All');
  const [showInfo, setShowInfo] = useState(false);
  const [displayCount, setDisplayCount] = useState(30);
  const [selectedStock, setSelectedStock] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [loadingChart, setLoadingChart] = useState(false);
  
  const FMP_API_KEY = 'vPO3Q9TJPSQQuIGLSDfEJB1mtuJazaYP';
  
  useEffect(() => {
    fetch('/magic_formula_results.json')
      .then(response => response.json())
      .then(data => {
        setStocks(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error loading stock data:', error);
        setLoading(false);
      });
  }, []);
  
  const sectors = useMemo(() => {
    const uniqueSectors = [...new Set(stocks.map(s => s.sector))];
    return ['All', ...uniqueSectors.sort()];
  }, [stocks]);
  
  const filteredStocks = useMemo(() => {
    if (selectedSector === 'All') return stocks;
    return stocks.filter(s => s.sector === selectedSector);
  }, [stocks, selectedSector]);
  
  const displayedStocks = useMemo(() => {
    return filteredStocks.slice(0, displayCount);
  }, [filteredStocks, displayCount]);
  
  const formatMarketCap = (value) => {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value}`;
  };
  
  const fetchStockChart = async (symbol) => {
    setLoadingChart(true);
    setChartData([]);
    
    try {
      const response = await fetch(
        `https://financialmodelingprep.com/api/v3/historical-price-full/${symbol}?apikey=${FMP_API_KEY}`
      );
      const data = await response.json();
      
      if (data.historical) {
        const sixMonthsData = data.historical.slice(0, 126).reverse();
        const formattedData = sixMonthsData.map(item => ({
          date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          price: item.close
        }));
        setChartData(formattedData);
      }
    } catch (error) {
      console.error('Error fetching chart data:', error);
    } finally {
      setLoadingChart(false);
    }
  };
  
  const handleStockClick = (stock) => {
    setSelectedStock(stock);
    fetchStockChart(stock.symbol);
  };
  
  const closeModal = () => {
    setSelectedStock(null);
    setChartData([]);
  };
  
  const downloadCSV = () => {
    const headers = ['Rank', 'Symbol', 'Company', 'Sector', 'Market Cap', 'Earnings Yield %', 'ROC %'];
    const rows = displayedStocks.map((stock, idx) => [
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
  
  const loadMore = () => {
    setDisplayCount(prev => Math.min(prev + 30, filteredStocks.length));
  };
  
  return (
    <div className="min-h-screen bg-slate-100 p-6 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-slate-800">
              Magic Formula Stock Screener
            </h1>
          </div>
          <p className="text-slate-600 ml-13">
            Top-ranked stocks using Joel Greenblatt's proven investment strategy
          </p>
          <p className="text-slate-500 text-sm ml-13 mt-1">
            Last updated: {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
          </p>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-200 border-t-blue-600"></div>
          </div>
        )}

        {!loading && stocks.length === 0 && (
          <div className="bg-white rounded-xl p-8 text-center shadow-sm">
            <p className="text-slate-600">No stock data available. Please run the screener to generate results.</p>
          </div>
        )}

        {!loading && stocks.length > 0 && (
          <>
            {/* Info Modal */}
            {showInfo && (
              <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center p-4 z-50" onClick={() => setShowInfo(false)}>
                <div className="bg-white rounded-xl p-8 max-w-2xl shadow-2xl" onClick={e => e.stopPropagation()}>
                  <h3 className="text-2xl font-bold text-slate-800 mb-4">About the Magic Formula</h3>
                  <div className="space-y-4 text-slate-700">
                    <p>The Magic Formula is a quantitative investment strategy developed by Joel Greenblatt that ranks stocks based on two key metrics:</p>
                    <div className="space-y-3 pl-4">
                      <div className="flex gap-3">
                        <div className="w-1 bg-emerald-500 rounded"></div>
                        <div>
                          <div className="font-semibold text-slate-800">Earnings Yield</div>
                          <div className="text-sm">Measures how much a company earns relative to its value (EBIT / Enterprise Value)</div>
                        </div>
                      </div>
                      <div className="flex gap-3">
                        <div className="w-1 bg-blue-600 rounded"></div>
                        <div>
                          <div className="font-semibold text-slate-800">Return on Capital</div>
                          <div className="text-sm">Measures how efficiently a company uses its capital (EBIT / Capital Employed)</div>
                        </div>
                      </div>
                    </div>
                    <div className="bg-slate-50 rounded-lg p-4 text-sm text-slate-600 border border-slate-200">
                      <strong>Disclaimer:</strong> This tool is for educational and informational purposes only. It does not constitute investment advice. Always conduct your own research and consult with a financial advisor before making investment decisions.
                    </div>
                  </div>
                  <button 
                    onClick={() => setShowInfo(false)}
                    className="mt-6 w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg transition-colors font-medium"
                  >
                    Got it
                  </button>
                </div>
              </div>
            )}

            {/* Stock Chart Modal */}
            {selectedStock && (
              <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center p-4 z-50" onClick={closeModal}>
                <div className="bg-white rounded-xl p-8 max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl" onClick={e => e.stopPropagation()}>
                  <div className="flex items-start justify-between mb-6">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-2xl font-bold text-blue-600 font-mono">{selectedStock.symbol}</span>
                        <span className="text-slate-400">•</span>
                        <span className="text-xl font-semibold text-slate-800">{selectedStock.name}</span>
                      </div>
                      <p className="text-slate-500">6 Month Price Performance</p>
                    </div>
                    <button
                      onClick={closeModal}
                      className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                    >
                      <X className="w-6 h-6 text-slate-600" />
                    </button>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                      <div className="text-slate-500 text-sm mb-1">Market Cap</div>
                      <div className="text-xl font-bold text-slate-800">{formatMarketCap(selectedStock.market_cap)}</div>
                    </div>
                    <div className="bg-emerald-50 rounded-lg p-4 border border-emerald-200">
                      <div className="text-emerald-700 text-sm mb-1">Earnings Yield</div>
                      <div className="text-xl font-bold text-emerald-700">{selectedStock.earnings_yield.toFixed(2)}%</div>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                      <div className="text-blue-700 text-sm mb-1">Return on Capital</div>
                      <div className="text-xl font-bold text-blue-700">{selectedStock.return_on_capital.toFixed(2)}%</div>
                    </div>
                    <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                      <div className="text-purple-700 text-sm mb-1">Rank</div>
                      <div className="text-xl font-bold text-purple-700">#{Math.round(selectedStock.combined_rank)}</div>
                    </div>
                  </div>

                  <div className="bg-slate-50 rounded-lg p-6 border border-slate-200">
                    {loadingChart ? (
                      <div className="flex items-center justify-center h-64">
                        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-200 border-t-blue-600"></div>
                      </div>
                    ) : chartData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={chartData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                          <XAxis 
                            dataKey="date" 
                            stroke="#64748b"
                            tick={{ fontSize: 12 }}
                            interval="preserveStartEnd"
                          />
                          <YAxis 
                            stroke="#64748b"
                            tick={{ fontSize: 12 }}
                            domain={['auto', 'auto']}
                          />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: '#fff',
                              border: '1px solid #e2e8f0',
                              borderRadius: '8px',
                              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                            }}
                            formatter={(value) => [`$${value.toFixed(2)}`, 'Price']}
                          />
                          <Line 
                            type="monotone" 
                            dataKey="price" 
                            stroke="#2563eb" 
                            strokeWidth={3}
                            dot={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex items-center justify-center h-64 text-slate-500">
                        No chart data available
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Controls Card */}
            <div className="bg-white rounded-xl p-6 mb-6 shadow-sm border border-slate-200">
              <div className="flex flex-wrap gap-4 items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Filter className="w-5 h-5 text-slate-500" />
                    <select 
                      value={selectedSector}
                      onChange={(e) => {
                        setSelectedSector(e.target.value);
                        setDisplayCount(30);
                      }}
                      className="bg-white text-slate-700 px-4 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      {sectors.map(sector => (
                        <option key={sector} value={sector}>{sector}</option>
                      ))}
                    </select>
                  </div>
                  <span className="text-slate-600 text-sm">
                    Showing {displayedStocks.length} of {filteredStocks.length} stocks
                  </span>
                </div>
                
                <div className="flex gap-3">
                  <button
                    onClick={() => setShowInfo(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors"
                  >
                    <Info className="w-4 h-4" />
                    About
                  </button>
                  <button
                    onClick={downloadCSV}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                  >
                    <Download className="w-4 h-4" />
                    Export CSV
                  </button>
                </div>
              </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-slate-500 text-sm mb-2">Top Earnings Yield</div>
                    <div className="text-3xl font-bold text-slate-800 mb-1">{filteredStocks[0]?.earnings_yield.toFixed(2)}%</div>
                    <div className="text-emerald-600 text-sm font-medium">{filteredStocks[0]?.symbol}</div>
                  </div>
                  <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-emerald-600" />
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-slate-500 text-sm mb-2">Top Return on Capital</div>
                    <div className="text-3xl font-bold text-slate-800 mb-1">{filteredStocks[0]?.return_on_capital.toFixed(2)}%</div>
                    <div className="text-blue-600 text-sm font-medium">{filteredStocks[0]?.symbol}</div>
                  </div>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <BarChart3 className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-slate-500 text-sm mb-2">Total Stocks</div>
                    <div className="text-3xl font-bold text-slate-800 mb-1">{filteredStocks.length}</div>
                    <div className="text-purple-600 text-sm font-medium">Magic Formula ranked</div>
                  </div>
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <Filter className="w-6 h-6 text-purple-600" />
                  </div>
                </div>
              </div>
            </div>

            {/* Stock Table */}
            <div className="bg-white rounded-xl overflow-hidden shadow-sm border border-slate-200">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-50 border-b border-slate-200">
                    <tr>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Rank</th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Symbol</th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Company</th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Sector</th>
                      <th className="px-6 py-4 text-right text-xs font-semibold text-slate-600 uppercase tracking-wider">Market Cap</th>
                      <th className="px-6 py-4 text-right text-xs font-semibold text-slate-600 uppercase tracking-wider">Earnings Yield</th>
                      <th className="px-6 py-4 text-right text-xs font-semibold text-slate-600 uppercase tracking-wider">ROC</th>
                      <th className="px-6 py-4 text-center text-xs font-semibold text-slate-600 uppercase tracking-wider">Chart</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {displayedStocks.map((stock, index) => (
                      <tr 
                        key={stock.symbol} 
                        className="hover:bg-slate-50 transition-colors cursor-pointer"
                        onClick={() => handleStockClick(stock)}
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className={`inline-flex items-center justify-center w-8 h-8 rounded-lg font-bold text-sm ${
                            index < 3 ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600'
                          }`}>
                            {index + 1}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="font-mono font-bold text-blue-600">{stock.symbol}</div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm font-medium text-slate-800">{stock.name}</div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
                            {stock.sector}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-slate-700">
                          {formatMarketCap(stock.market_cap)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right">
                          <span className="font-semibold text-emerald-600">{stock.earnings_yield.toFixed(2)}%</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right">
                          <span className="font-semibold text-blue-600">{stock.return_on_capital.toFixed(2)}%</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-center">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleStockClick(stock);
                            }}
                            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                            title="View chart"
                          >
                            <BarChart3 className="w-4 h-4 text-slate-500" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {displayCount < filteredStocks.length && (
                <div className="p-6 text-center border-t border-slate-200 bg-slate-50">
                  <button
                    onClick={loadMore}
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
                  >
                    Load More ({Math.min(30, filteredStocks.length - displayCount)} more)
                  </button>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="mt-8 text-center text-slate-500 text-sm">
              <p>Based on Joel Greenblatt's <em>The Little Book That Beats the Market</em></p>
              <p className="mt-2">Data sourced from Financial Modeling Prep • Not investment advice</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default MagicFormulaDashboard;