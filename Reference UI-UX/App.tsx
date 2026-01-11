
import React, { useState } from 'react';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import BotManagement from './pages/BotManagement';
import Watchlist from './pages/Watchlist';
import Settings from './pages/Settings';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'bots':
        return <BotManagement />;
      case 'watchlist':
        return <Watchlist />;
      case 'settings':
        return <Settings />;
      case 'investments':
        return (
          <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4">
            <div className="w-20 h-20 bg-indigo-50 rounded-full flex items-center justify-center text-indigo-600">
              <span className="text-3xl font-bold">V</span>
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">Virtual Portfolio</h2>
              <p className="text-slate-500">This feature is currently being simulated with live market data.</p>
            </div>
            <button 
              onClick={() => setActiveTab('dashboard')}
              className="px-6 py-2 bg-indigo-600 text-white rounded-xl font-semibold shadow-lg shadow-indigo-100"
            >
              Go to Dashboard
            </button>
          </div>
        );
      default:
        return <Dashboard />;
    }
  };

  return (
    <Layout activeTab={activeTab} setActiveTab={setActiveTab}>
      {renderContent()}
    </Layout>
  );
};

export default App;
