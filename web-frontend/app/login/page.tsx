"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { login, isAuthenticated, checkHealth } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginPage() {
    const router = useRouter();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [apiStatus, setApiStatus] = useState<"checking" | "online" | "offline">("checking");

    useEffect(() => {
        // Check if already authenticated
        if (isAuthenticated()) {
            router.push("/");
            return;
        }

        // Check API health
        checkHealth().then((health) => {
            setApiStatus(health ? "online" : "offline");
        });
    }, [router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        const result = await login(username, password);

        if (result.success) {
            router.push("/");
        } else {
            setError(result.error || "Login failed");
        }

        setLoading(false);
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800 p-4">
            <Card className="w-full max-w-md shadow-2xl border-slate-700 bg-slate-800/90 backdrop-blur">
                <CardHeader className="text-center space-y-2">
                    <div className="text-4xl mb-2">🤖</div>
                    <CardTitle className="text-2xl font-bold text-white">ARUN Trading Bot</CardTitle>
                    <p className="text-slate-400 text-sm">Titan V2 • Secure Access</p>

                    {/* API Status Indicator */}
                    <div className="flex items-center justify-center gap-2 mt-4">
                        <span className={`h-2 w-2 rounded-full ${apiStatus === "online" ? "bg-green-500" :
                                apiStatus === "offline" ? "bg-red-500" : "bg-yellow-500 animate-pulse"
                            }`}></span>
                        <span className="text-xs text-slate-400">
                            API: {apiStatus === "online" ? "Online" : apiStatus === "offline" ? "Offline" : "Checking..."}
                        </span>
                    </div>
                </CardHeader>

                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="username" className="text-slate-300">Username</Label>
                            <Input
                                id="username"
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="Enter username"
                                className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                                required
                                disabled={apiStatus === "offline"}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="password" className="text-slate-300">Password</Label>
                            <Input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Enter password"
                                className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-500"
                                required
                                disabled={apiStatus === "offline"}
                            />
                        </div>

                        {error && (
                            <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 text-red-400 text-sm">
                                ⚠️ {error}
                            </div>
                        )}

                        <Button
                            type="submit"
                            className="w-full bg-blue-600 hover:bg-blue-700"
                            disabled={loading || apiStatus === "offline"}
                        >
                            {loading ? "Authenticating..." : "Login"}
                        </Button>
                    </form>

                    <div className="mt-6 pt-4 border-t border-slate-700">
                        <p className="text-xs text-slate-500 text-center">
                            Default credentials (for development only):<br />
                            <code className="bg-slate-700 px-1 rounded">admin</code> / <code className="bg-slate-700 px-1 rounded">changeme123</code>
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
