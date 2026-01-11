
import React from 'react';
import { Search, Filter, ArrowUp, ArrowDown, ChevronRight, Star } from 'lucide-react';
import { WATCHLIST } from '../constants';

const Watchlist: React.FC = () => {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Watchlists</h1>
          <p className="text-slate-500">Track your favorite stocks, ETFs, and mutual funds.</p>
        </div>
        <div className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input 
              type="text" 
              placeholder="Filter assets..." 
              className="pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all w-full md:w-64"
            />
          </div>
          <button className="p-2 bg-white border border-slate-200 rounded-xl text-slate-500 hover:bg-slate-50 transition-colors">
            <Filter size={18} />
          </button>
        </div>
      </div>

      <div className="bg-white rounded-3xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100">
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Asset</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">Price</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">Change</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">Market Cap</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">Volume</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {WATCHLIST.map((item) => (
                <tr key={item.symbol} className="hover:bg-slate-50 transition-colors cursor-pointer group">
                  <td className="px-6 py-5">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center font-bold text-indigo-600">
                        {item.symbol[0]}
                      </div>
                      <div>
                        <p className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">{item.symbol}</p>
                        <p className="text-xs text-slate-500">{item.name}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-5 text-right font-semibold text-slate-900">${item.price.toFixed(2)}</td>
                  <td className="px-6 py-5 text-right">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-bold ${
                      item.change >= 0 ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'
                    }`}>
                      {item.change >= 0 ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
                      {Math.abs(item.change)}%
                    </span>
                  </td>
                  <td className="px-6 py-5 text-right text-sm text-slate-600 font-medium">{item.marketCap}</td>
                  <td className="px-6 py-5 text-right text-sm text-slate-600 font-medium">{item.volume}</td>
                  <td className="px-6 py-5">
                    <div className="flex items-center justify-center gap-2">
                      <button className="p-2 text-slate-400 hover:text-amber-500 transition-colors">
                        <Star size={18} fill="currentColor" />
                      </button>
                      <button className="p-2 text-slate-400 hover:text-indigo-600 transition-colors">
                        <ChevronRight size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-indigo-600 rounded-3xl p-8 text-white relative overflow-hidden">
          <div className="relative z-10">
            <h3 className="text-2xl font-bold mb-2">Smart Alerts</h3>
            <p className="text-indigo-100 mb-6">Set price targets and receive AI-summarized triggers directly to your dashboard.</p>
            <button className="px-6 py-3 bg-white text-indigo-600 rounded-2xl font-bold hover:bg-indigo-50 transition-all shadow-lg">Configure Alerts</button>
          </div>
          <div className="absolute -right-12 -bottom-12 w-48 h-48 bg-white/10 rounded-full blur-3xl" />
        </div>
        <div className="bg-slate-900 rounded-3xl p-8 text-white relative overflow-hidden">
          <div className="relative z-10">
            <h3 className="text-2xl font-bold mb-2">Market Insights</h3>
            <p className="text-slate-400 mb-6">Our AI constantly scans sector rotations and volatility clusters to suggest additions.</p>
            <button className="px-6 py-3 bg-indigo-500 text-white rounded-2xl font-bold hover:bg-indigo-400 transition-all shadow-lg shadow-indigo-500/20">Explore Sectors</button>
          </div>
          <div className="absolute -right-12 -bottom-12 w-48 h-48 bg-indigo-500/20 rounded-full blur-3xl" />
        </div>
      </div>
    </div>
  );
};

export default Watchlist;
