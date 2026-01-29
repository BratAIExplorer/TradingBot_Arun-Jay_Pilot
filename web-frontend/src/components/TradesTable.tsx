import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export interface Trade {
    id: number;
    timestamp: string;
    symbol: string;
    action: "BUY" | "SELL";
    price: number;
    quantity: number;
    strategy: string;
    pnl_net?: number;
}

interface TradesTableProps {
    trades: Trade[];
    className?: string;
}

export default function TradesTable({ trades, className }: TradesTableProps) {
    if (!trades || trades.length === 0) {
        return (
            <div className={cn("glass-card rounded-2xl p-8 text-center", className)}>
                <h3 className="font-semibold text-lg mb-2">Recent Trades</h3>
                <p className="text-gray-500 italic">No trades recorded yet</p>
            </div>
        )
    }

    return (
        <div className={cn("glass-card rounded-2xl overflow-hidden border border-white/5", className)}>
            <div className="px-6 py-4 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
                <h3 className="font-semibold text-lg text-white">Recent Trades</h3>
                <button className="text-accent text-xs font-bold uppercase tracking-wider hover:opacity-80 transition-opacity">View All</button>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead>
                        <tr className="bg-black/20 text-gray-500 text-[10px] font-bold uppercase tracking-widest">
                            <th className="px-6 py-3">Time</th>
                            <th className="px-6 py-3">Symbol</th>
                            <th className="px-6 py-3">Action</th>
                            <th className="px-6 py-3 text-right">Price</th>
                            <th className="px-6 py-3 text-right">Qty</th>
                            <th className="px-6 py-3 text-right">PnL</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {trades.map((trade) => (
                            <tr key={trade.id} className="hover:bg-white/[0.02] transition-colors group">
                                <td className="px-6 py-4 text-xs text-gray-400 font-mono">
                                    {new Date(trade.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </td>
                                <td className="px-6 py-4 font-bold text-sm tracking-wide text-white">{trade.symbol}</td>
                                <td className="px-6 py-4">
                                    <span className={cn(
                                        "px-2 py-1 rounded text-[10px] font-bold border",
                                        trade.action === "BUY"
                                            ? "bg-success/10 text-success border-success/20"
                                            : "bg-danger/10 text-danger border-danger/20"
                                    )}>
                                        {trade.action}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-right font-mono text-sm text-gray-300">
                                    ₹{trade.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                </td>
                                <td className="px-6 py-4 text-right font-mono text-sm text-gray-300">
                                    {trade.quantity}
                                </td>
                                <td className={cn("px-6 py-4 text-right font-mono text-sm font-bold",
                                    (trade.pnl_net || 0) > 0 ? "text-success" : (trade.pnl_net || 0) < 0 ? "text-danger" : "text-gray-500"
                                )}>
                                    {trade.pnl_net ? `₹${trade.pnl_net.toFixed(2)}` : "-"}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
