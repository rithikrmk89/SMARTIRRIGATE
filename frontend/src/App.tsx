import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { ToastContainer, ToastMessage } from './components/Toast';
import { DashboardPage } from './pages/DashboardPage';
import { PredictorPage } from './pages/PredictorPage';
import { DatasetsPage } from './pages/DatasetsPage';
import { ModelsPage } from './pages/ModelsPage';
import { HistoryPage } from './pages/HistoryPage';
import { ArchitecturePage } from './pages/ArchitecturePage';
import { api } from './api/client';
import { DashboardStats, HealthStatus } from './types';
import { Sprout } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = (type: 'success' | 'error' | 'warning', title: string, message?: string) => {
    const id = `${Date.now()}-${Math.random()}`;
    setToasts((prev) => [...prev, { id, type, title, message }]);
  };

  const dismissToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const loadHealth = async () => {
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch {
      // Backend might be warming up
    }
  };

  const loadStats = async () => {
    try {
      const data = await api.getDashboardStats();
      setStats(data);
    } catch {
      // Backend might be warming up
    }
  };

  useEffect(() => {
    loadHealth();
    loadStats();
    const interval = setInterval(() => {
      loadStats();
    }, 25000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#0b1120] text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-slate-950">
      {/* Top Navigation */}
      <Navbar
        health={health}
        onRefreshHealth={loadHealth}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {activeTab === 'dashboard' && (
          <DashboardPage
            stats={stats}
            health={health}
            onNavigate={setActiveTab}
            onQuickPredict={() => setActiveTab('predict')}
          />
        )}

        {activeTab === 'predict' && (
          <PredictorPage
            onPredictionComplete={loadStats}
            onShowToast={showToast}
          />
        )}

        {activeTab === 'datasets' && (
          <DatasetsPage
            onShowToast={showToast}
            onRefreshStats={loadStats}
          />
        )}

        {activeTab === 'models' && (
          <ModelsPage
            onShowToast={showToast}
            onRefreshStats={loadStats}
          />
        )}

        {activeTab === 'history' && (
          <HistoryPage
            onShowToast={showToast}
            onRefreshStats={loadStats}
          />
        )}

        {activeTab === 'architecture' && (
          <ArchitecturePage health={health} />
        )}
      </main>

      {/* Global Toast Container */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/60 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <div className="flex items-center space-x-2">
            <Sprout className="w-4 h-4 text-emerald-400" />
            <span className="font-semibold text-slate-300">SmartIrrigate Cloud</span>
            <span>— Final-Year Cloud Computing & Precision Irrigation Capstone</span>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-slate-500">Storage: {health?.storage?.mode || 'Local Mode'}</span>
            <span className="text-slate-600">•</span>
            <button
              onClick={() => setActiveTab('architecture')}
              className="hover:text-emerald-400 transition-colors"
            >
              Architecture & Cloud Services
            </button>
            <span className="text-slate-600">•</span>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="hover:text-emerald-400 transition-colors flex items-center gap-1"
            >
              <span>API Swagger</span>
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
