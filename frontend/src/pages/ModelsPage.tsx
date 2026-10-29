import React, { useState, useEffect } from 'react';
import {
  Cpu,
  TrendingUp,
  BarChart2,
  CheckCircle,
  Trash2,
  Play,
  Layers,
  Sparkles,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { api } from '../api/client';
import { DatasetItem, MLModelItem } from '../types';

interface ModelsPageProps {
  onShowToast: (type: 'success' | 'error' | 'warning', title: string, message?: string) => void;
  onRefreshStats: () => void;
}

export const ModelsPage: React.FC<ModelsPageProps> = ({
  onShowToast,
  onRefreshStats,
}) => {
  const [models, setModels] = useState<MLModelItem[]>([]);
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [selectedModel, setSelectedModel] = useState<MLModelItem | null>(null);

  const [form, setForm] = useState({
    name: 'Random Forest Regressor v2',
    dataset_id: 0,
    model_type: 'random_forest',
    test_split_ratio: 0.2,
    n_estimators: 100,
    max_depth: 12,
  });

  const loadData = async () => {
    try {
      setLoading(true);
      const [mList, dList] = await Promise.all([api.getModels(), api.getDatasets()]);
      setModels(mList);
      setDatasets(dList);
      if (dList.length > 0 && form.dataset_id === 0) {
        setForm((prev) => ({ ...prev, dataset_id: dList[0].id }));
      }
      const active = mList.find((m) => m.is_active) || mList[0] || null;
      setSelectedModel(active);
    } catch (err: any) {
      onShowToast('error', 'Failed to Load Models', err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTrain = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.dataset_id === 0) {
      onShowToast('warning', 'No Dataset Selected', 'Please ingest or generate a dataset first.');
      return;
    }

    setTraining(true);
    try {
      const trained = await api.trainModel(form);
      onShowToast(
        'success',
        'Model Successfully Trained',
        `Evaluated on unseen test set: R² = ${(trained.metrics.r2 * 100).toFixed(1)}%, MAE = ${trained.metrics.mae} mm/day.`
      );
      loadData();
      onRefreshStats();
    } catch (err: any) {
      onShowToast('error', 'Training Failed', err.message);
    } finally {
      setTraining(false);
    }
  };

  const handleActivate = async (id: number) => {
    try {
      await api.activateModel(id);
      onShowToast('success', 'Active Model Updated', 'This model will now serve all incoming prediction requests.');
      loadData();
      onRefreshStats();
    } catch (err: any) {
      onShowToast('error', 'Activation Failed', err.message);
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Delete model "${name}"?`)) return;
    try {
      await api.deleteModel(id);
      onShowToast('success', 'Model Removed', `Deleted ${name} and its artefact.`);
      loadData();
      onRefreshStats();
    } catch (err: any) {
      onShowToast('error', 'Delete Failed', err.message);
    }
  };

  const featureChartData = selectedModel?.feature_importances
    ? Object.entries(selectedModel.feature_importances).map(([name, weight]) => ({
        name: name.replace('_', ' ').replace('_pct', '%'),
        importance: Number((weight * 100).toFixed(1)),
      }))
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold font-heading text-white tracking-tight flex items-center gap-2">
            <Cpu className="w-7 h-7 text-emerald-400" />
            Machine Learning Model Training & Evaluation
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Train regression algorithms on agricultural datasets. Strictly evaluates MAE, RMSE, and R² on held-out test splits.
          </p>
        </div>
        <button
          onClick={loadData}
          className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white transition-colors self-start"
          title="Refresh models"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Model Training Form (5 Cols) */}
        <div className="lg:col-span-5 glass-panel rounded-2xl p-6 border border-slate-800">
          <div className="pb-4 border-b border-slate-800">
            <h2 className="text-base font-bold font-heading text-white flex items-center gap-2">
              <Play className="w-5 h-5 text-emerald-400 fill-emerald-400" />
              Train New Regression Model
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Select dataset, choose architecture, and tune hyperparameters
            </p>
          </div>

          <form onSubmit={handleTrain} className="mt-4 space-y-4">
            {/* Model Name */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Model Name</label>
              <input
                type="text"
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white"
              />
            </div>

            {/* Dataset Picker */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Training Dataset</label>
              <select
                value={form.dataset_id}
                onChange={(e) => setForm({ ...form, dataset_id: parseInt(e.target.value) })}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white"
              >
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.row_count} rows)
                  </option>
                ))}
              </select>
            </div>

            {/* Model Architecture */}
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Algorithm</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: 'random_forest', label: 'Random Forest' },
                  { id: 'decision_tree', label: 'Decision Tree' },
                  { id: 'linear_regression', label: 'Linear Baseline' },
                ].map((type) => (
                  <button
                    type="button"
                    key={type.id}
                    onClick={() => setForm({ ...form, model_type: type.id })}
                    className={`py-2 px-2 rounded-xl border text-[11px] font-bold text-center transition-all ${
                      form.model_type === type.id
                        ? 'border-emerald-500 bg-emerald-500/20 text-white'
                        : 'border-slate-800 bg-slate-900/60 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {type.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Test Split Ratio */}
            <div>
              <div className="flex justify-between text-xs text-slate-300 font-semibold mb-1">
                <span>Test Split Ratio</span>
                <span className="font-mono text-emerald-400">{(form.test_split_ratio * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.4"
                step="0.05"
                value={form.test_split_ratio}
                onChange={(e) => setForm({ ...form, test_split_ratio: parseFloat(e.target.value) })}
                className="w-full accent-emerald-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
              />
            </div>

            {/* Random Forest Hyperparameters */}
            {form.model_type === 'random_forest' && (
              <div className="grid grid-cols-2 gap-3 pt-2">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 mb-1">N Estimators</label>
                  <input
                    type="number"
                    min="10"
                    max="300"
                    value={form.n_estimators}
                    onChange={(e) => setForm({ ...form, n_estimators: parseInt(e.target.value) || 100 })}
                    className="w-full px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 mb-1">Max Depth</label>
                  <input
                    type="number"
                    min="2"
                    max="25"
                    value={form.max_depth}
                    onChange={(e) => setForm({ ...form, max_depth: parseInt(e.target.value) || 12 })}
                    className="w-full px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white font-mono"
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={training || datasets.length === 0}
              className="w-full mt-2 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-slate-950 font-bold text-xs shadow-md shadow-emerald-500/20 flex items-center justify-center space-x-2 transition-all disabled:opacity-50"
            >
              {training ? (
                <>
                  <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                  <span>Fitting Model & Calculating Metrics...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 fill-slate-950" />
                  <span>Start Training Pipeline</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Feature Importance Visualizer (7 Cols) */}
        <div className="lg:col-span-7 glass-panel rounded-2xl p-6 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="pb-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold font-heading text-white flex items-center gap-2">
                  <BarChart2 className="w-5 h-5 text-emerald-400" />
                  Model Feature Importance
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Weights of inputs contributing to {selectedModel?.name || 'Active Model'}
                </p>
              </div>
              {selectedModel?.is_active && (
                <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Active Model
                </span>
              )}
            </div>

            <div className="h-64 mt-4 w-full">
              {featureChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={featureChartData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis type="number" stroke="#64748b" tick={{ fontSize: 11 }} unit="%" />
                    <YAxis dataKey="name" type="category" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                    <Tooltip
                      formatter={(val: any) => [`${val}%`, 'Importance Weight']}
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }}
                    />
                    <Bar dataKey="importance" fill="#10b981" radius={[0, 4, 4, 0]} barSize={14} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-500 text-xs">
                  No model selected or feature weights unavailable.
                </div>
              )}
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/50 text-slate-400 text-[11px] leading-relaxed mt-4">
            <strong>Explainability Notice:</strong> Feature importance ranks how heavily tree splits leverage each parameter. It demonstrates decision influence, not direct physical causality.
          </div>
        </div>
      </div>

      {/* Model Benchmark Comparison Table */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800">
        <div className="pb-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold font-heading text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              Trained Models Benchmark Registry
            </h2>
            <p className="text-xs text-slate-400">Strictly computed on 20% held-out test splits (Never fabricated)</p>
          </div>
          <span className="text-xs text-slate-400 font-mono">{models.length} model(s)</span>
        </div>

        <div className="overflow-x-auto mt-4">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-800/50 text-slate-400 uppercase font-semibold">
              <tr>
                <th className="py-3 px-4 rounded-l-lg">Model Name</th>
                <th className="py-3 px-3">Type</th>
                <th className="py-3 px-3">Train / Test Rows</th>
                <th className="py-3 px-3">Test MAE</th>
                <th className="py-3 px-3">Test RMSE</th>
                <th className="py-3 px-3">Test R² Score</th>
                <th className="py-3 px-3">Baseline Linear R²</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-4 rounded-r-lg text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400">
                    Loading model registry...
                  </td>
                </tr>
              ) : models.length > 0 ? (
                models.map((m) => (
                  <tr
                    key={m.id}
                    onClick={() => setSelectedModel(m)}
                    className={`cursor-pointer transition-colors ${
                      selectedModel?.id === m.id ? 'bg-emerald-500/10' : 'hover:bg-slate-800/30'
                    }`}
                  >
                    <td className="py-3 px-4 font-semibold text-white">
                      <div className="flex items-center gap-2">
                        <Cpu className="w-4 h-4 text-emerald-400 shrink-0" />
                        <span>{m.name}</span>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-slate-400 capitalize">{m.model_type.replace('_', ' ')}</td>
                    <td className="py-3 px-3 font-mono text-slate-400">
                      {m.train_rows} / {m.test_rows}
                    </td>
                    <td className="py-3 px-3 font-mono">{m.metrics.mae.toFixed(3)} mm</td>
                    <td className="py-3 px-3 font-mono text-slate-400">{m.metrics.rmse.toFixed(3)} mm</td>
                    <td className="py-3 px-3 font-mono font-bold text-emerald-400">
                      {(m.metrics.r2 * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-400">
                      {m.baseline_metrics ? `${(m.baseline_metrics.r2 * 100).toFixed(1)}%` : 'N/A'}
                    </td>
                    <td className="py-3 px-3">
                      {m.is_active ? (
                        <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[10px] font-bold">
                          ACTIVE
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 text-[10px]">
                          Standby
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right space-x-2" onClick={(e) => e.stopPropagation()}>
                      {!m.is_active && (
                        <button
                          onClick={() => handleActivate(m.id)}
                          className="px-2.5 py-1 rounded-lg bg-emerald-600/80 hover:bg-emerald-500 text-slate-950 font-bold text-[10px] transition-colors"
                        >
                          Set Active
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(m.id, m.name)}
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition-colors"
                        title="Delete model"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-500">
                    No models trained yet. Ingest a dataset and click "Start Training Pipeline" above.
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
