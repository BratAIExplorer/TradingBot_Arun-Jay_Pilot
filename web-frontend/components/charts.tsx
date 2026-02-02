"use client";

import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Area,
    AreaChart
} from "recharts";

interface PnLDataPoint {
    time: string;
    pnl: number;
}

interface EquityChartProps {
    data: PnLDataPoint[];
    height?: number;
}

export function EquityChart({ data, height = 200 }: EquityChartProps) {
    // Determine if overall trend is positive
    const lastValue = data.length > 0 ? data[data.length - 1].pnl : 0;
    const isPositive = lastValue >= 0;
    const chartColor = isPositive ? "#22c55e" : "#ef4444";
    const gradientId = isPositive ? "greenGradient" : "redGradient";

    return (
        <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                <defs>
                    <linearGradient id="greenGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="redGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                <XAxis
                    dataKey="time"
                    stroke="#6b7280"
                    fontSize={10}
                    tickLine={false}
                />
                <YAxis
                    stroke="#6b7280"
                    fontSize={10}
                    tickLine={false}
                    tickFormatter={(value) => `₹${value}`}
                />
                <Tooltip
                    contentStyle={{
                        backgroundColor: "#1f2937",
                        border: "1px solid #374151",
                        borderRadius: "8px",
                        fontSize: "12px"
                    }}
                    labelStyle={{ color: "#9ca3af" }}
                    formatter={(value: number) => [`₹${value.toFixed(2)}`, "P&L"]}
                />
                <Area
                    type="monotone"
                    dataKey="pnl"
                    stroke={chartColor}
                    strokeWidth={2}
                    fill={`url(#${gradientId})`}
                />
            </AreaChart>
        </ResponsiveContainer>
    );
}

// Mini sparkline version for compact display
interface SparklineProps {
    data: number[];
    width?: number;
    height?: number;
}

export function PnLSparkline({ data, width = 80, height = 30 }: SparklineProps) {
    const chartData = data.map((value, index) => ({ index, value }));
    const lastValue = data.length > 0 ? data[data.length - 1] : 0;
    const color = lastValue >= 0 ? "#22c55e" : "#ef4444";

    return (
        <ResponsiveContainer width={width} height={height}>
            <LineChart data={chartData}>
                <Line
                    type="monotone"
                    dataKey="value"
                    stroke={color}
                    strokeWidth={1.5}
                    dot={false}
                />
            </LineChart>
        </ResponsiveContainer>
    );
}
