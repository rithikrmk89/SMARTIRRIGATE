import {
  DashboardStats,
  DatasetDetail,
  DatasetItem,
  HealthStatus,
  MLModelItem,
  PredictionHistoryItem,
  PredictionInput,
  PredictionResult,
} from '../types';

function normalizeApiBase(base: string): string {
  let cleaned = (base || '/api').trim().replace(/\/+$/, '');
  if (cleaned.startsWith('http') && !cleaned.endsWith('/api')) {
    cleaned = `${cleaned}/api`;
  }
  return cleaned;
}

const API_BASE = normalizeApiBase((import.meta.env.VITE_API_BASE_URL as string) || '/api');

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errMsg = `Request failed with status ${res.status}`;
    try {
      const errData = await res.json();
      if (errData && errData.detail) {
        errMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errMsg);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // Health
  getHealth: async (): Promise<HealthStatus> => {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse<HealthStatus>(res);
  },

  // Dashboard Stats
  getDashboardStats: async (): Promise<DashboardStats> => {
    const res = await fetch(`${API_BASE}/predictions/stats`);
    return handleResponse<DashboardStats>(res);
  },

  // Datasets
  getDatasets: async (): Promise<DatasetItem[]> => {
    const res = await fetch(`${API_BASE}/datasets`);
    return handleResponse<DatasetItem[]>(res);
  },

  getDatasetDetail: async (id: number): Promise<DatasetDetail> => {
    const res = await fetch(`${API_BASE}/datasets/${id}`);
    return handleResponse<DatasetDetail>(res);
  },

  uploadDataset: async (file: File): Promise<DatasetDetail> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/datasets/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<DatasetDetail>(res);
  },

  generateSampleDataset: async (numSamples = 1000, includeOutliers = false): Promise<DatasetDetail> => {
    const res = await fetch(`${API_BASE}/datasets/generate-sample`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ num_samples: numSamples, include_outliers: includeOutliers }),
    });
    return handleResponse<DatasetDetail>(res);
  },

  deleteDataset: async (id: number): Promise<{ message: string; id: number }> => {
    const res = await fetch(`${API_BASE}/datasets/${id}`, { method: 'DELETE' });
    return handleResponse<{ message: string; id: number }>(res);
  },

  // Models
  getModels: async (): Promise<MLModelItem[]> => {
    const res = await fetch(`${API_BASE}/models`);
    return handleResponse<MLModelItem[]>(res);
  },

  trainModel: async (params: {
    name: string;
    dataset_id: number;
    model_type: string;
    test_split_ratio: number;
    n_estimators: number;
    max_depth?: number;
  }): Promise<MLModelItem> => {
    const res = await fetch(`${API_BASE}/models/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return handleResponse<MLModelItem>(res);
  },

  activateModel: async (id: number): Promise<MLModelItem> => {
    const res = await fetch(`${API_BASE}/models/${id}/activate`, { method: 'POST' });
    return handleResponse<MLModelItem>(res);
  },

  deleteModel: async (id: number): Promise<{ message: string; id: number }> => {
    const res = await fetch(`${API_BASE}/models/${id}`, { method: 'DELETE' });
    return handleResponse<{ message: string; id: number }>(res);
  },

  // Predictions
  predict: async (input: PredictionInput): Promise<PredictionResult> => {
    const res = await fetch(`${API_BASE}/predictions/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    });
    return handleResponse<PredictionResult>(res);
  },

  getPredictionHistory: async (crop?: string): Promise<PredictionHistoryItem[]> => {
    const url = crop ? `${API_BASE}/predictions/history?crop=${encodeURIComponent(crop)}` : `${API_BASE}/predictions/history`;
    const res = await fetch(url);
    return handleResponse<PredictionHistoryItem[]>(res);
  },

  deletePrediction: async (id: number): Promise<{ message: string; id: number }> => {
    const res = await fetch(`${API_BASE}/predictions/${id}`, { method: 'DELETE' });
    return handleResponse<{ message: string; id: number }>(res);
  },

  clearHistory: async (): Promise<{ message: string }> => {
    const res = await fetch(`${API_BASE}/predictions`, { method: 'DELETE' });
    return handleResponse<{ message: string }>(res);
  },

  getExportCsvUrl: (): string => `${API_BASE}/predictions/export`,
};
