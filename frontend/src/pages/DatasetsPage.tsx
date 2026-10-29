import React, { useState, useEffect } from 'react';
import {
  Upload,
  Database,
  FileText,
  Trash2,
  Eye,
  Sparkles,
  AlertTriangle,
  CheckCircle,
  FileCheck,
  RefreshCw,
  HardDrive,
} from 'lucide-react';
import { api } from '../api/client';
import { Modal } from '../components/Modal';
import { DatasetDetail, DatasetItem } from '../types';

interface DatasetsPageProps {
  onShowToast: (type: 'success' | 'error' | 'warning', title: string, message?: string) => void;
  onRefreshStats: () => void;
}

export const DatasetsPage: React.FC<DatasetsPageProps> = ({
  onShowToast,
  onRefreshStats,
}) => {
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [selectedDetail, setSelectedDetail] = useState<DatasetDetail | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const loadDatasets = async () => {
    try {
      setLoading(true);
      const data = await api.getDatasets();
      setDatasets(data);
    } catch (err: any) {
      onShowToast('error', 'Failed to Load Datasets', err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDatasets();
  }, []);

  const handleFileUpload = async (file: File) => {
    if (!file.name.endsWith('.csv')) {
      onShowToast('error', 'Invalid File Type', 'Please upload a CSV (.csv) file.');
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      onShowToast('error', 'File Too Large', 'Maximum allowed file size is 25MB.');
      return;
    }

    setUploading(true);
    try {
      const res = await api.uploadDataset(file);
      onShowToast(
        'success',
        'Dataset Ingested & Cleaned',
        `Successfully processed ${res.row_count} rows across ${res.column_count} columns.`
      );
      loadDatasets();
      onRefreshStats();
    } catch (err: any) {
      onShowToast('error', 'Ingestion Failed', err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleGenerateSample = async (samples: number) => {
    setGenerating(true);
    try {
      const res = await api.generateSampleDataset(samples, false);
      onShowToast(
        'success',
        'Demo Benchmark Generated',
        `Created synthetic FAO-56 benchmark dataset with ${res.row_count} records.`
      );
      loadDatasets();
      onRefreshStats();
    } catch (err: any) {
      onShowToast('error', 'Generation Failed', err.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleInspect = async (id: number) => {
    try {
      const detail = await api.getDatasetDetail(id);
      setSelectedDetail(detail);
      setModalOpen(true);
    } catch (err: any) {
      onShowToast('error', 'Could Not Inspect Dataset', err.message);
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Are you sure you want to delete dataset "${name}"?`)) return;
    try {
      await api.deleteDataset(id);
      onShowToast('success', 'Dataset Deleted', `Removed ${name} from storage.`);
      loadDatasets();
      onRefreshStats();
    } catch (err: any) {
      onShowToast('error', 'Delete Failed', err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold font-heading text-white tracking-tight flex items-center gap-2">
            <Database className="w-7 h-7 text-emerald-400" />
            Dataset Management & Ingestion Pipeline
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Upload agricultural weather records, clean schemas, impute missing values, or generate FAO-56 benchmark datasets.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleGenerateSample(1200)}
            disabled={generating}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-green-700 hover:from-emerald-500 hover:to-green-600 text-white font-bold text-xs shadow-md shadow-emerald-500/20 flex items-center space-x-2 transition-all disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-emerald-200" />
            <span>{generating ? 'Generating...' : 'Generate Demo Benchmark (1.2k)'}</span>
          </button>
          <button
            onClick={loadDatasets}
            className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white transition-colors"
            title="Refresh dataset list"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Upload Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileUpload(e.dataTransfer.files[0]);
          }
        }}
        className={`glass-panel rounded-2xl p-8 border-2 border-dashed text-center transition-all ${
          dragActive
            ? 'border-emerald-500 bg-emerald-500/10'
            : 'border-slate-800 hover:border-slate-700'
        }`}
      >
        <div className="max-w-md mx-auto space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-slate-800/80 border border-slate-700 mx-auto flex items-center justify-center text-emerald-400">
            <Upload className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold font-heading text-white text-base">
              Drag & Drop your agricultural CSV dataset here
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Supports CSV up to 25MB. Column names are automatically mapped to standardized agricultural features.
            </p>
          </div>
          <div>
            <label className="inline-flex items-center px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 cursor-pointer transition-colors">
              <span>{uploading ? 'Processing & Cleaning...' : 'Browse CSV Files'}</span>
              <input
                type="file"
                accept=".csv"
                disabled={uploading}
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileUpload(e.target.files[0]);
                  }
                }}
                className="hidden"
              />
            </label>
          </div>
        </div>
      </div>

      {/* Datasets Table */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800">
        <div className="pb-4 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-base font-bold font-heading text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-emerald-400" />
            Ingested Datasets Repository
          </h2>
          <span className="text-xs text-slate-400">{datasets.length} dataset(s) stored</span>
        </div>

        <div className="overflow-x-auto mt-4">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-800/50 text-slate-400 uppercase font-semibold">
              <tr>
                <th className="py-3 px-4 rounded-l-lg">Dataset Name</th>
                <th className="py-3 px-3">Rows</th>
                <th className="py-3 px-3">Columns</th>
                <th className="py-3 px-3">Imputed Nulls</th>
                <th className="py-3 px-3">Type</th>
                <th className="py-3 px-3">Size</th>
                <th className="py-3 px-4 rounded-r-lg text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    Loading datasets...
                  </td>
                </tr>
              ) : datasets.length > 0 ? (
                datasets.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-semibold text-white">
                      <div className="flex items-center gap-2">
                        <Database className="w-4 h-4 text-emerald-400 shrink-0" />
                        <div>
                          <div className="truncate max-w-xs">{d.name}</div>
                          <div className="text-[10px] text-slate-500 font-mono">{d.filename}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-3 font-mono font-medium">{d.row_count.toLocaleString()}</td>
                    <td className="py-3 px-3 font-mono text-slate-400">{d.column_count}</td>
                    <td className="py-3 px-3 font-mono">
                      {d.missing_values_count > 0 ? (
                        <span className="text-amber-400">{d.missing_values_count} cleaned</span>
                      ) : (
                        <span className="text-emerald-400">0 clean</span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      {d.is_synthetic ? (
                        <span className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30 text-[10px] font-semibold">
                          Synthetic Demo
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] font-semibold">
                          User Uploaded
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-slate-400 font-mono">
                      {(d.file_size_bytes / 1024).toFixed(1)} KB
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <button
                        onClick={() => handleInspect(d.id)}
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                        title="Inspect columns and preview records"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(d.id, d.name)}
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition-colors"
                        title="Delete dataset"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No datasets currently ingested. Click "Generate Demo Benchmark" or upload a CSV file above.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Dataset Inspection Modal */}
      {selectedDetail && (
        <Modal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title={selectedDetail.name}
          subtitle={`Schema summary & preview: ${selectedDetail.row_count} rows, ${selectedDetail.column_count} columns`}
          maxWidth="4xl"
        >
          <div className="space-y-6">
            {/* Quick Stats Pill */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Total Rows</div>
                <div className="text-base font-bold font-mono text-white mt-0.5">
                  {selectedDetail.row_count.toLocaleString()}
                </div>
              </div>
              <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Columns</div>
                <div className="text-base font-bold font-mono text-white mt-0.5">{selectedDetail.column_count}</div>
              </div>
              <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Missing Imputed</div>
                <div className="text-base font-bold font-mono text-emerald-400 mt-0.5">
                  {selectedDetail.missing_values_count}
                </div>
              </div>
              <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/60">
                <div className="text-[10px] text-slate-400 uppercase font-semibold">Data Nature</div>
                <div className="text-xs font-semibold text-slate-200 mt-1">
                  {selectedDetail.is_synthetic ? 'FAO-56 Synthetic Demo' : 'Public / User Sourced'}
                </div>
              </div>
            </div>

            {/* Column Schema Table */}
            <div>
              <h4 className="font-bold font-heading text-white text-sm mb-2">Column Data Types & Distribution</h4>
              <div className="overflow-x-auto border border-slate-800 rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-800/70 text-slate-300 font-semibold">
                    <tr>
                      <th className="py-2.5 px-3">Column Name</th>
                      <th className="py-2.5 px-3">Data Type</th>
                      <th className="py-2.5 px-3">Non-Null</th>
                      <th className="py-2.5 px-3">Uniques</th>
                      <th className="py-2.5 px-3">Mean</th>
                      <th className="py-2.5 px-3">Min / Max</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    {selectedDetail.columns.map((col) => (
                      <tr key={col.name} className="hover:bg-slate-800/40">
                        <td className="py-2 px-3 font-mono text-emerald-300 font-semibold">{col.name}</td>
                        <td className="py-2 px-3 text-slate-400 font-mono text-[11px]">{col.dtype}</td>
                        <td className="py-2 px-3 font-mono">{col.non_null_count}</td>
                        <td className="py-2 px-3 font-mono">{col.unique_count}</td>
                        <td className="py-2 px-3 font-mono">{col.mean !== null ? col.mean : '-'}</td>
                        <td className="py-2 px-3 font-mono text-slate-400">
                          {col.min !== null && col.max !== null ? `${col.min} - ${col.max}` : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Preview Rows Table */}
            {selectedDetail.preview_rows && selectedDetail.preview_rows.length > 0 && (
              <div>
                <h4 className="font-bold font-heading text-white text-sm mb-2">First 10 Sample Rows</h4>
                <div className="overflow-x-auto border border-slate-800 rounded-xl max-h-64">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-800/70 text-slate-300 font-semibold sticky top-0">
                      <tr>
                        {Object.keys(selectedDetail.preview_rows[0]).map((key) => (
                          <th key={key} className="py-2 px-3 whitespace-nowrap">
                            {key}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 text-slate-300">
                      {selectedDetail.preview_rows.map((row, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/40">
                          {Object.values(row).map((val: any, cIdx) => (
                            <td key={cIdx} className="py-2 px-3 whitespace-nowrap font-mono text-[11px] text-slate-300">
                              {String(val)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};
