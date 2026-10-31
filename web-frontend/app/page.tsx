import DashboardView from "@/components/dashboard-view";

export default function Home() {
    return (
        <main className="min-h-screen bg-[#EFEBE3]">
            <div className="bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="text-xl font-bold text-blue-600">ARUN</span>
                        <span className="text-xl font-bold text-gray-800">TITAN</span>
                        <span className="text-xs font-bold bg-gray-200 px-2 py-1 rounded">HEADLESS v2.1</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="text-sm font-medium text-gray-600">Admin</div>
                    </div>
                </div>
            </div>
            <DashboardView />
        </main>
    );
}
