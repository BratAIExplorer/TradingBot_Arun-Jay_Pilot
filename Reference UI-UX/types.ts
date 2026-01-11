
export type BotStatus = 'Running' | 'Paused' | 'Error' | 'Idle';

export interface Bot {
  id: string;
  name: string;
  strategy: string;
  status: BotStatus;
  profitPercent: number;
  allocatedBudget: number;
  tradesToday: number;
  lastActive: string;
}

export interface WatchlistItem {
  symbol: string;
  name: string;
  price: number;
  change: number;
  volume: string;
  marketCap: string;
}

export interface UserSettings {
  name: string;
  email: string;
  broker: string;
  apiKey: string;
  apiSecret: string;
  totalBudget: number;
  isTwoFactorEnabled: boolean;
}

export interface MarketTrend {
  time: string;
  value: number;
}
