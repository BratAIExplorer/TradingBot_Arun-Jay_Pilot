
import { Bot, WatchlistItem, MarketTrend } from './types';

export const INITIAL_BOTS: Bot[] = [
  {
    id: '1',
    name: 'Alpha Sentinel',
    strategy: 'Moving Average Crossover (SMA 50/200)',
    status: 'Running',
    profitPercent: 12.4,
    allocatedBudget: 5000,
    tradesToday: 8,
    lastActive: 'Just now'
  },
  {
    id: '2',
    name: 'Neural Arbitrage',
    strategy: 'Sentiment Analysis / News-Driven',
    status: 'Running',
    profitPercent: -2.1,
    allocatedBudget: 3500,
    tradesToday: 24,
    lastActive: '2 mins ago'
  },
  {
    id: '3',
    name: 'Momentum Scalper',
    strategy: 'RSI & Bollinger Band Mean Reversion',
    status: 'Paused',
    profitPercent: 5.8,
    allocatedBudget: 2000,
    tradesToday: 0,
    lastActive: '1 hour ago'
  }
];

export const WATCHLIST: WatchlistItem[] = [
  { symbol: 'NVDA', name: 'Nvidia Corporation', price: 726.13, change: 5.63, volume: '45M', marketCap: '1.7T' },
  { symbol: 'META', name: 'Meta Platforms Inc', price: 484.03, change: -4.44, volume: '22M', marketCap: '1.2T' },
  { symbol: 'TSLA', name: 'Tesla Inc', price: 188.13, change: 17.17, volume: '110M', marketCap: '600B' },
  { symbol: 'AMZN', name: 'Amazon.com Inc', price: 174.45, change: 3.02, volume: '38M', marketCap: '1.8T' },
  { symbol: 'MSFT', name: 'Microsoft Corp', price: 410.34, change: 0.16, volume: '20M', marketCap: '3.0T' }
];

export const MOCK_TRENDS: MarketTrend[] = Array.from({ length: 24 }, (_, i) => ({
  time: `${i}:00`,
  value: Math.floor(Math.random() * 1000) + 4000
}));
