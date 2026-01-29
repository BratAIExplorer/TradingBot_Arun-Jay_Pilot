// Smart URL detection for VPS vs Localhost
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ||
    (typeof window !== "undefined" ? window.location.protocol + "//" + window.location.hostname + ":8000" : "http://localhost:8000");

export async function fetcher(endpoint: string) {
    try {
        const res = await fetch(`${API_BASE_URL}${endpoint}`, {
            cache: "no-store",
        });
        if (!res.ok) {
            console.error(`API Error ${res.status}: ${res.statusText}`);
            return null;
        }
        return res.json();
    } catch (error) {
        console.error("Fetch error:", error);
        return null;
    }
}

export const endpoints = {
    health: "/health",
    positions: "/api/positions",
    recentTrades: "/api/trades/recent",
    controlStatus: "/api/control/status",
    controlSet: "/api/control/set",
};

export async function sendCommand(status: "RUNNING" | "STOPPED") {
    try {
        const res = await fetch(`${API_BASE_URL}${endpoints.controlSet}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status }),
        });
        return res.ok;
    } catch (error) {
        console.error("Command error:", error);
        return false;
    }
}
