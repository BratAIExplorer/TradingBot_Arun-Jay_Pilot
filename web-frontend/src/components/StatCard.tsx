import { LucideIcon } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface StatCardProps {
    title: string;
    value: string | number;
    icon: LucideIcon;
    trend?: {
        value: number;
        isPositive: boolean;
    };
    className?: string;
    subValue?: string;
}

export default function StatCard({ title, value, icon: Icon, trend, className, subValue }: StatCardProps) {
    return (
        <div className={cn("glass-card p-6 rounded-2xl flex flex-col gap-4 border border-white/5", className)}>
            <div className="flex justify-between items-center">
                <span className="text-gray-400 text-xs font-bold uppercase tracking-widest">{title}</span>
                <div className="p-2 bg-white/5 rounded-lg border border-white/5">
                    <Icon className="w-5 h-5 text-accent" />
                </div>
            </div>

            <div className="flex flex-col">
                <span className="text-3xl font-bold tracking-tight text-white">{value}</span>
                {subValue && (
                    <span className="text-xs text-gray-500 font-mono mt-1">{subValue}</span>
                )}
                {trend && (
                    <div className={cn("flex items-center text-xs font-semibold mt-2", trend.isPositive ? "text-success" : "text-danger")}>
                        {trend.isPositive ? "+" : ""}{trend.value}%
                        <span className="ml-1 text-gray-500 font-normal text-[10px]">VS LAST 24H</span>
                    </div>
                )}
            </div>
        </div>
    );
}
