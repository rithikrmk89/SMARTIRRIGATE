import React, { useState, useEffect } from 'react';
import {
  History,
  Download,
  Trash2,
  Search,
  RefreshCw,
  Droplets,
  Calendar,
  AlertTriangle,
} from 'lucide-react';
import { api } from '../api/client';
import { PredictionHistoryItem } from '../types';

interface HistoryPageProps {
  onShowToast: (type: 'success' | 'error' | 'warning', title: string, message?: string) => void;
  onRefreshStats: () => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({
  onShowToast,
  onRefreshStats,
}) => {
  const [history, setHistory] = useState<PredictionHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterCrop, setFilterCrop] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const loadHistory = async () => {
    try {
      setLoading(true);
      const data = await api.getPredictionHistory(filterCrop || undefined);
      setHistory(data);
    } catch (err: any) {
      onShowToast('error', 'Failed to Load History', err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [filterCrop]);

  const handleDelete = async (id: number) => {
    try {
      await api.deletePrediction(id);
      onShowToast('success', 'Record Deleted', 'Prediction log removed.');
      loadHistory();
      onRefreshStats();
    } catch (err: any) {
      onShowToast('error', 'Delete Failed', err.message);
    }
  };

  const handleClearAll = async () => {
    if (!confirm('Are you sure you want to clear all prediction history records?')) return;
    try {
      await api.clearHistory();
      onShowToast('success', 'History Cleared', 'All past inference logs cleared.');
      loadHistory();
      onRefreshStats();
    } catch (err: any) {
      onShowToast('error', 'Clear Failed', err.message);
    }
  };

  const filteredHistory = history.filter((item) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.crop_type.toLowerCase().includes(q) ||
      item.soil_type.toLowerCase().includes(q) ||
      item.recommendation.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold font-heading text-white tracking-tight flex items-center gap-2">
            <History className="w-7 h-7 text-emerald-400" />
            Prediction History & Audit Logs
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Browse past water demand recommendations, filter by crop type, and export audit data.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <a
            href={api.getExportCsvUrl()}
            download
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-semibold text-xs flex items-center space-x-2 transition-colors shadow-sm"
          >
            <Download className="w-4 h-4 text-emerald-400" />
            <span>Export CSV</span>
          </a>
          <button
            onClick={handleClearAll}
            disabled={history.length === 0}
            className="px-4 py-2.5 rounded-xl bg-red-950/40 hover:bg-red-900/60 border border-red-500/30 text-red-300 font-semibold text-xs flex items-center space-x-2 transition-colors disabled:opacity-50"
          >
            <Trash2 className="w-4 h-4" />
            <span>Clear History</span>
          </button>
          <button
            onClick={loadHistory}
            className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white transition-colors"
            title="Refresh history"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel rounded-2xl p-4 border border-slate-800 flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search by crop, soil texture, or recommendation..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white placeholder-slate-500"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <select
            value={filterCrop}
            onChange={(e) => setFilterCrop(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white w-full sm:w-auto"
          >
            <option value="">All Crop Species</option>
            {['Wheat', 'Rice', 'Maize', 'Cotton', 'Tomato', 'Sugarcane', 'Potato', 'Barley'].map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* History Table */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-800/50 text-slate-400 uppercase font-semibold">
              <tr>
                <th className="py-3 px-4 rounded-l-lg">Timestamp</th>
                <th className="py-3 px-3">Crop / Soil</th>
                <th className="py-3 px-3">Moisture</th>
                <th className="py-3 px-3">Temp / Humidity</th>
                <th className="py-3 px-3">Rainfall</th>
                <th className="py-3 px-3">Demand (mm/day)</th>
                <th className="py-3 px-3">Total Volume</th>
                <th className="py-3 px-4">Advisory Details</th>
                <th className="py-3 px-3 rounded-r-lg text-right">Delete</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400">
                    Loading records...
                  </td>
                </tr>
              ) : filteredHistory.length > 0 ? (
                filteredHistory.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 whitespace-nowrap text-slate-400 font-mono text-[11px]">
                      {new Date(item.created_at).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="py-3 px-3 font-semibold text-white">
                      <div>{item.crop_type}</div>
                      <div className="text-[10px] text-slate-400 font-normal">{item.soil_type}</div>
                    </td>
                    <td className="py-3 px-3 font-mono font-medium">
                      <span className={item.soil_moisture_pct < 25 ? 'text-amber-400' : 'text-slate-200'}>
                        {item.soil_moisture_pct}%
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-400">
                      {item.temperature_c}°C / {item.humidity_pct}%
                    </td>
                    <td className="py-3 px-3 font-mono">
                      {item.rainfall_mm > 0 ? (
                        <span className="text-cyan-400 font-semibold">{item.rainfall_mm} mm</span>
                      ) : (
                        <span className="text-slate-500">0 mm</span>
                      )}
                    </td>
                    <td className="py-3 px-3 font-mono">
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 font-bold">
                        {item.predicted_water_demand_mm_day} mm
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono">
                      <div className="font-semibold text-white">{item.total_volume_m3} m³</div>
                      <div className="text-[10px] text-slate-400">{item.area_hectares} ha</div>
                    </td>
                    <td className="py-3 px-4 max-w-sm text-slate-300 truncate" title={item.recommendation}>
                      {item.recommendation}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="p-1 rounded-lg text-slate-500 hover:text-red-400 hover:bg-slate-800 transition-colors"
                        title="Delete record"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-500">
                    No matching prediction records found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
