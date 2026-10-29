import React from 'react';
import { Sprout, Cloud, Database, HardDrive, ExternalLink, RefreshCw } from 'lucide-react';
import { HealthStatus } from '../types';

interface NavbarProps {
  health: HealthStatus | null;
  onRefreshHealth: () => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  health,
  onRefreshHealth,
  activeTab,
  setActiveTab,
}) => {
  const isHealthy = health?.status === 'healthy';
  const isAzure = health?.storage?.mode?.includes('Azure') ?? false;
  const isCloud = isAzure || (health?.storage?.mode?.includes('AWS') ?? false);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'predict', label: 'Demand Predictor' },
    { id: 'datasets', label: 'Datasets' },
    { id: 'models', label: 'ML Models' },
    { id: 'history', label: 'History' },
    { id: 'architecture', label: 'Cloud Architecture' },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-slate-800 bg-slate-900/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-green-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <Sprout className="w-6 h-6 text-slate-950 stroke-[2.5]" />
            </div>
            <div>
              <span className="text-lg font-bold font-heading text-white tracking-tight flex items-center gap-1.5">
                SmartIrrigate <span className="text-emerald-400 font-extrabold text-sm px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-500/30">Cloud</span>
              </span>
              <p className="text-[11px] text-slate-400 font-medium">Smart Irrigation & Water Demand Prediction</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const active = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                    active
                      ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Right Status Indicators */}
          <div className="flex items-center space-x-3">
            {/* Storage Mode Pill */}
            <div
              className={`hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${
                isCloud
                  ? 'bg-blue-500/10 text-blue-300 border-blue-500/30'
                  : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
              }`}
            >
              {isCloud ? <Cloud className="w-3.5 h-3.5" /> : <HardDrive className="w-3.5 h-3.5" />}
              <span>{isAzure ? 'Azure Blob Storage' : isCloud ? 'Cloud Storage' : 'Local SQLite'}</span>
            </div>

            {/* Health Status Indicator */}
            <button
              onClick={onRefreshHealth}
              title="Click to refresh system health status"
              className="flex items-center space-x-2 px-3 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700 text-xs font-medium text-slate-300 transition-colors"
            >
              <span className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`} />
              <span className="hidden xs:inline">{isHealthy ? 'System Online' : 'Degraded'}</span>
              <RefreshCw className="w-3 h-3 text-slate-400 ml-1" />
            </button>

            {/* FastAPI Swagger Link */}
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              title="Open FastAPI Swagger Interactive Docs"
              className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </div>
      </div>

      {/* Mobile nav bar */}
      <div className="md:hidden flex overflow-x-auto px-4 py-2 space-x-2 border-t border-slate-800/80 bg-slate-900/60">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`whitespace-nowrap px-3 py-1 rounded-md text-xs font-medium ${
              activeTab === item.id
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>
    </header>
  );
};
