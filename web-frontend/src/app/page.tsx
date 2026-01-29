"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Wallet,
  TrendingUp,
  AlertTriangle,
  RefreshCw,
  Power
} from "lucide-react";
import StatCard from "@/components/StatCard";
import TradesTable, { Trade } from "@/components/TradesTable";
import { fetcher, endpoints, sendCommand } from "@/lib/api";

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalValue: 0,
    dailyPnL: 0,
    activePositions: 0,
    winRate: 0
  });
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null); // Null initially for hydration fix
  const [systemStatus, setSystemStatus] = useState("ONLINE");
  const [botControlStatus, setBotControlStatus] = useState("UNKNOWN"); // RUNNING | STOPPED
  const [mounted, setMounted] = useState(false);

  // Hydration Fix: Only render client-side date
  useEffect(() => {
    setMounted(true);
    setLastUpdated(new Date());
  }, []);

  const refreshData = async () => {
    try {
      // 1. Fetch Positions to calculate total value
      const positions = await fetcher(endpoints.positions);
      let totalVal = 0;
      let positionCount = 0;

      if (Array.isArray(positions)) {
        totalVal = positions.reduce((acc: number, pos: any) => acc + (pos.total_invested || 0), 0);
        positionCount = positions.length;
      }

      // 2. Fetch Recent Trades
      const recentTrades = await fetcher(endpoints.recentTrades);

      // 3. Fetch Bot Status
      const statusData = await fetcher(endpoints.controlStatus);
      if (statusData && statusData.status) {
        setBotControlStatus(statusData.status);
      }

      // Update State
      setStats(prev => ({
        ...prev,
        totalValue: totalVal,
        activePositions: positionCount,
        // Mocking PnL/Winrate for now until API provides it
        dailyPnL: 1250.50,
        winRate: 68
      }));

      if (Array.isArray(recentTrades)) {
        setTrades(recentTrades);
      }

      setLastUpdated(new Date());
      setLoading(false);
      setSystemStatus("ONLINE");
    } catch (error) {
      console.error("Failed to refresh data", error);
      setSystemStatus("OFFLINE");
    }
  };

  const handleBotControl = async (action: "START" | "STOP") => {
    const targetState = action === "START" ? "RUNNING" : "STOPPED";
    const success = await sendCommand(targetState);
    if (success) {
      setBotControlStatus(targetState);
      // Optimistic update
    }
  };

  useEffect(() => {
    if (mounted) {
      refreshData();
      const interval = setInterval(refreshData, 5000); // Poll every 5 seconds
      return () => clearInterval(interval);
    }
  }, [mounted]);

  // Don't render until client-side hydration is complete to avoid mismatches
  if (!mounted) return null;

  return (
    <div className="min-h-screen p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-black tracking-tighter text-white">ARUN <span className="text-accent">TITAN</span></h1>
          <p className="text-gray-500 font-medium text-sm">Autonomous Trading System</p>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/5">
            <div className={`w-2 h-2 rounded-full ${systemStatus === "ONLINE" ? "bg-success shadow-[0_0_10px_#10B981]" : "bg-danger"}`}></div>
            <span className="text-xs font-bold tracking-wider">{systemStatus}</span>
          </div>
          <button onClick={() => refreshData()} className="p-2 hover:bg-white/10 rounded-full transition-colors">
            <RefreshCw className="w-5 h-5 text-gray-400" />
          </button>
        </div>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Portfolio Value"
          value={`₹${stats.totalValue.toLocaleString()}`}
          icon={Wallet}
          trend={{ value: 2.4, isPositive: true }}
        />
        <StatCard
          title="Today's PnL"
          value={`₹${stats.dailyPnL.toLocaleString()}`}
          icon={TrendingUp}
          trend={{ value: 5.1, isPositive: true }}
          className="neon-border"
        />
        <StatCard
          title="Active Positions"
          value={stats.activePositions}
          icon={Activity}
          subValue="ACROSS 2 EXCHANGES"
        />
        <StatCard
          title="Win Rate"
          value={`${stats.winRate}%`}
          icon={AlertTriangle}
          trend={{ value: 1.2, isPositive: false }}
        />
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Trades (Takes up 2 columns) */}
        <div className="lg:col-span-2 space-y-4">
          <TradesTable trades={trades} />
        </div>

        {/* System Controls / Logs (Simplified Side Panel) */}
        <div className="glass-card rounded-2xl p-6 h-fit border border-white/5">
          <h3 className="font-semibold text-lg mb-4 text-white">System Control</h3>
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-white/5 border border-white/5 flex justify-between items-center">
              <span className="text-sm font-medium text-gray-300">Bot Service</span>
              {botControlStatus === "RUNNING" ? (
                <button
                  onClick={() => handleBotControl("STOP")}
                  className="px-4 py-1.5 rounded-lg bg-success text-black text-xs font-bold hover:bg-success/90 transition-colors animate-pulse">
                  RUNNING
                </button>
              ) : (
                <button
                  onClick={() => handleBotControl("START")}
                  className="px-4 py-1.5 rounded-lg bg-gray-600 text-white text-xs font-bold hover:bg-gray-500 transition-colors">
                  STOPPED
                </button>
              )}
            </div>

            <div className="p-4 rounded-xl bg-white/5 border border-white/5 flex justify-between items-center">
              <span className="text-sm font-medium text-gray-300">Emergency Stop</span>
              <button
                onClick={() => handleBotControl("STOP")}
                className="p-2 rounded-lg bg-danger/20 text-danger hover:bg-danger/30 transition-colors border border-danger/20 hover:border-danger">
                <Power className="w-5 h-5" />
              </button>
            </div>

            <div className="mt-8 pt-6 border-t border-white/5">
              <h4 className="text-xs font-bold uppercase text-gray-500 mb-3">Last Activity</h4>
              <div className="space-y-3">
                <div className="flex gap-3 text-xs">
                  <span className="text-gray-600 font-mono">
                    {lastUpdated?.toLocaleTimeString() || "--:--:--"}
                  </span>
                  <span className="text-gray-400">
                    {botControlStatus === "RUNNING" ? "Bot is active & scanning..." : "Bot is stopped."}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
