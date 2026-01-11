
import React, { useState } from 'react';
import { Play, Pause, Plus, MoreHorizontal, Settings, Info, Sparkles, Send } from 'lucide-react';
import { INITIAL_BOTS } from '../constants';
import { Bot } from '../types';
import { getStrategyAdvice } from '../services/geminiService';

const BotManagement: React.FC = () => {
  const [bots, setBots] = useState<Bot[]>(INITIAL_BOTS);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState<string | null>(null);

  const toggleBot = (id: string) => {
    setBots(prev => prev.map(bot => 
      bot.id === id 
        ? { ...bot, status: bot.status === 'Running' ? 'Paused' : 'Running' } 
        : bot
    ));
  };

  const askAi = async () => {
    setIsAiLoading(true);
    const advice = await getStrategyAdvice("Currently tracking tech stocks with high volatility but strong earnings reports.");
    setAiResponse(advice);
    setIsAiLoading(false);
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Trading Bot Strategies</h1>
          <p className="text-slate-500">Deploy, manage, and monitor your AI agents.</p>
        </div>
        <button className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-2xl font-bold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100">
          <Plus size={20} />
          Create New Bot
        </button>
      </div>

      {/* AI Assistant Banner */}
      <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-600 p-px rounded-3xl overflow-hidden shadow-xl shadow-indigo-100">
        <div className="bg-white/95 backdrop-blur-sm p-6 flex flex-col md:flex-row items-center gap-6">
          <div className="bg-indigo-600 p-4 rounded-2xl text-white shadow-lg shadow-indigo-200">
            <Sparkles size={32} />
          </div>
          <div className="flex-1 text-center md:text-left">
            <h3 className="text-xl font-bold text-slate-900">QuantIQ Strategy Advisor</h3>
            <p className="text-slate-500 mt-1">Get AI-powered insights for your next trading strategy based on real-time market sentiment.</p>
            {aiResponse && (
              <div className="mt-4 p-4 bg-slate-50 rounded-xl text-sm text-slate-700 border border-slate-100">
                {aiResponse}
              </div>
            )}
          </div>
          <button 
            onClick={askAi}
            disabled={isAiLoading}
            className="px-6 py-3 bg-slate-900 text-white rounded-2xl font-bold hover:bg-slate-800 transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {isAiLoading ? <span className="animate-spin">🌀</span> : <Send size={18} />}
            {isAiLoading ? 'Analyzing...' : 'Get Strategy Insight'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {bots.map((bot) => (
          <div key={bot.id} className="bg-white rounded-3xl border border-slate-100 shadow-sm p-6 hover:border-indigo-200 transition-all group">
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-bold text-xl ${
                  bot.status === 'Running' ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-50 text-slate-400'
                }`}>
                  {bot.name[0]}
                </div>
                <div>
                  <h4 className="font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">{bot.name}</h4>
                  <p className="text-xs text-slate-400">ID: {bot.id}</p>
                </div>
              </div>
              <button className="text-slate-300 hover:text-slate-600">
                <MoreHorizontal size={20} />
              </button>
            </div>

            <div className="mb-6">
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Active Strategy</p>
              <p className="text-sm font-semibold text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-100">
                {bot.strategy}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="p-3 rounded-2xl bg-slate-50">
                <p className="text-[10px] text-slate-400 uppercase font-bold">P/L %</p>
                <p className={`text-lg font-bold ${bot.profitPercent >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                  {bot.profitPercent > 0 ? '+' : ''}{bot.profitPercent}%
                </p>
              </div>
              <div className="p-3 rounded-2xl bg-slate-50">
                {/* Fixed the className property which had a typo causing parsing errors */}
                <p className="text-[10px] text-slate-400 uppercase font-bold">Allocated</p>
                <p className="text-lg font-bold text-slate-900">${bot.allocatedBudget}</p>
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-slate-50">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${bot.status === 'Running' ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                <span className="text-xs font-semibold text-slate-500">{bot.status}</span>
              </div>
              <div className="flex gap-2">
                <button className="p-2 text-slate-400 hover:text-indigo-600 transition-colors">
                  <Settings size={18} />
                </button>
                <button 
                  onClick={() => toggleBot(bot.id)}
                  className={`p-2 rounded-xl transition-all ${
                    bot.status === 'Running' 
                      ? 'bg-rose-50 text-rose-600 hover:bg-rose-100' 
                      : 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100'
                  }`}
                >
                  {bot.status === 'Running' ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" />}
                </button>
              </div>
            </div>
          </div>
        ))}

        {/* Add Bot Empty State Card */}
        <button className="bg-slate-50 rounded-3xl border-2 border-dashed border-slate-200 p-8 flex flex-col items-center justify-center group hover:bg-slate-100 hover:border-indigo-300 transition-all">
          <div className="w-14 h-14 bg-white rounded-full flex items-center justify-center text-slate-300 group-hover:text-indigo-500 shadow-sm transition-colors mb-4">
            <Plus size={28} />
          </div>
          <p className="font-bold text-slate-500 group-hover:text-indigo-600">New Automation</p>
          <p className="text-xs text-slate-400 mt-1">Connect another broker API</p>
        </button>
      </div>
    </div>
  );
};

export default BotManagement;
