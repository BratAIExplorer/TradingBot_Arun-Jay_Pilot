"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
    fetchStatus,
    fetchPositions,
    fetchPnL,
    fetchCapital,
    controlBot,
    fetchLogs,
    isAuthenticated,
    logout
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

interface Position {
    symbol: string;
    qty?: number;
    net_quantity?: number;
    entry_price?: number;
    avg_entry_price?: number;
    ltp?: number;
    pnl?: number;
}

interface Status {
    status: string;
    running: boolean;
    uptime: string;
    counters?: {
        attempts: number;
        success: number;
        failed: number;
    };
}

interface Capital {
    total: number;
    deployed: number;
    available: number;
}

interface PnL {
    pnl: number;
    trades_count: number;
}

export default function DashboardView() {
    const router = useRouter();
    const [status, setStatus] = useState<Status | null>(null);
    const [positions, setPositions] = useState<Position[]>([]);
    const [logs, setLogs] = useState<string[]>([]);
    const [capital, setCapital] = useState<Capital>({ total: 50000, deployed: 0, available: 50000 });
    const [pnl, setPnl] = useState<PnL>({ pnl: 0, trades_count: 0 });
    const [loading, setLoading] = useState(false);
    const [authChecked, setAuthChecked] = useState(false);

    // Auth guard
    useEffect(() => {
        if (!isAuthenticated()) {
            router.push("/login");
        } else {
            setAuthChecked(true);
        }
    }, [router]);

    // Polling Loop
    useEffect(() => {
        if (!authChecked) return;

        const tick = async () => {
            const [s, p, l, c, pnlData] = await Promise.all([
                fetchStatus(),
                fetchPositions(),
                fetchLogs(),
                fetchCapital(),
                fetchPnL()
            ]);

            if (s) setStatus(s);
            if (p) setPositions(p.positions || []);
            if (l) setLogs(l.logs || []);
            if (c) setCapital(c);
            if (pnlData) setPnl(pnlData);
        };

        tick();
        const interval = setInterval(tick, 3000);
        return () => clearInterval(interval);
    }, [authChecked]);

    const handleControl = async (action: "start" | "stop") => {
        setLoading(true);
        await controlBot(action);
        const s = await fetchStatus();
        if (s) setStatus(s);
        setLoading(false);
    };

    const handleLogout = () => {
        logout();
    };

    const isRunning = status?.running || false;
    const deployedPct = capital.total > 0 ? (capital.deployed / capital.total) * 100 : 0;

    if (!authChecked) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-900">
                <div className="text-white">Loading...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-6">
            <div className="max-w-7xl mx-auto space-y-6">

                {/* Header */}
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                            🤖 ARUN Titan V2
                        </h1>
                        <p className="text-slate-400 text-sm">Trading Dashboard</p>
                    </div>
                    <Button
                        variant="outline"
                        onClick={handleLogout}
                        className="border-slate-600 text-slate-300 hover:bg-slate-700"
                    >
                        Logout
                    </Button>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

                    {/* Status Card */}
                    <Card className="border-l-4 border-l-blue-500 bg-slate-800/50 border-slate-700">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-slate-400">
                                ENGINE STATUS
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex justify-between items-center">
                                <div className="flex items-center gap-2">
                                    <span className={`h-3 w-3 rounded-full ${isRunning ? "bg-green-500 animate-pulse" : "bg-red-500"}`}></span>
                                    <span className="text-2xl font-bold text-white">{isRunning ? "RUNNING" : "STOPPED"}</span>
                                </div>
                                <Button
                                    variant={isRunning ? "destructive" : "default"}
                                    onClick={() => handleControl(isRunning ? "stop" : "start")}
                                    disabled={loading}
                                    className={isRunning ? "" : "bg-green-600 hover:bg-green-700"}
                                >
                                    {isRunning ? "STOP" : "START"}
                                </Button>
                            </div>
                            <div className="mt-2 text-xs text-slate-500">
                                Uptime: {status?.uptime || "0s"}
                            </div>
                            {status?.counters && (
                                <div className="mt-3 grid grid-cols-3 gap-2 border-t border-slate-700 pt-3">
                                    <div className="text-center">
                                        <div className="text-[10px] text-slate-500 uppercase">Attempts</div>
                                        <div className="font-bold text-white text-sm">{status.counters.attempts}</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-[10px] text-green-500 uppercase">Success</div>
                                        <div className="font-bold text-green-400 text-sm">{status.counters.success}</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-[10px] text-red-500 uppercase">Failed</div>
                                        <div className="font-bold text-red-400 text-sm">{status.counters.failed}</div>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Capital Card */}
                    <Card className="bg-slate-800/50 border-slate-700">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-slate-400">
                                CAPITAL DEPLOYED
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-white">
                                ₹{capital.deployed.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                            </div>
                            <Progress value={deployedPct} className="h-2 mt-2" />
                            <div className="text-xs text-slate-500 mt-1">
                                Available: ₹{capital.available.toLocaleString('en-IN', { minimumFractionDigits: 2 })} of ₹{capital.total.toLocaleString('en-IN')}
                            </div>
                        </CardContent>
                    </Card>

                    {/* PnL Card */}
                    <Card className="bg-slate-800/50 border-slate-700">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-slate-400">
                                TODAY'S P&L
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className={`text-2xl font-bold ${pnl.pnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                                {pnl.pnl >= 0 ? "+" : ""}₹{pnl.pnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                                {pnl.trades_count} Trade{pnl.trades_count !== 1 ? "s" : ""} Today
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                    {/* Active Positions Table */}
                    <div className="lg:col-span-2 space-y-4">
                        <h2 className="text-xl font-bold text-white">Active Positions</h2>
                        <Card className="bg-slate-800/50 border-slate-700">
                            <Table>
                                <TableHeader>
                                    <TableRow className="border-slate-700 hover:bg-slate-700/50">
                                        <TableHead className="text-slate-400">Symbol</TableHead>
                                        <TableHead className="text-slate-400">Qty</TableHead>
                                        <TableHead className="text-slate-400">Entry</TableHead>
                                        <TableHead className="text-slate-400">LTP</TableHead>
                                        <TableHead className="text-slate-400">P&L</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {positions.length === 0 ? (
                                        <TableRow className="border-slate-700">
                                            <TableCell colSpan={5} className="text-center h-24 text-slate-500">
                                                No active positions
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        positions.map((pos, i) => {
                                            const qty = pos.qty || pos.net_quantity || 0;
                                            const entry = pos.entry_price || pos.avg_entry_price || 0;
                                            const ltp = pos.ltp || entry;
                                            const positionPnl = (ltp - entry) * qty;

                                            return (
                                                <TableRow key={i} className="border-slate-700 hover:bg-slate-700/30">
                                                    <TableCell className="font-bold text-white">{pos.symbol}</TableCell>
                                                    <TableCell className="text-slate-300">{qty}</TableCell>
                                                    <TableCell className="text-slate-300">₹{entry.toFixed(2)}</TableCell>
                                                    <TableCell className="text-slate-300">₹{ltp.toFixed(2)}</TableCell>
                                                    <TableCell className={positionPnl >= 0 ? "text-green-500" : "text-red-500"}>
                                                        {positionPnl >= 0 ? "+" : ""}₹{positionPnl.toFixed(2)}
                                                    </TableCell>
                                                </TableRow>
                                            );
                                        })
                                    )}
                                </TableBody>
                            </Table>
                        </Card>
                    </div>

                    {/* Live Logs */}
                    <div className="space-y-4">
                        <h2 className="text-xl font-bold text-white">Live Logs</h2>
                        <Card className="bg-black border-slate-700 text-green-400 font-mono text-xs h-[400px] overflow-y-auto p-4">
                            {logs.length === 0 ? (
                                <div className="text-slate-500">Waiting for logs...</div>
                            ) : (
                                logs.map((log, i) => (
                                    <div key={i} className="mb-1 border-b border-slate-800 pb-1">
                                        {log}
                                    </div>
                                ))
                            )}
                        </Card>
                    </div>

                </div>
            </div>
        </div>
    );
}
