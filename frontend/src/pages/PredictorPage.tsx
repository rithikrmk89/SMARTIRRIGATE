import React, { useState } from 'react';
import {
  Droplets,
  Sparkles,
  AlertCircle,
  Clock,
  Compass,
  CheckCircle,
  HelpCircle,
  BarChart2,
  Cpu,
  Info,
} from 'lucide-react';
import { api } from '../api/client';
import { PredictionInput, PredictionResult } from '../types';

interface PredictorPageProps {
  onPredictionComplete: () => void;
  onShowToast: (type: 'success' | 'error' | 'warning', title: string, message?: string) => void;
}

const CROPS = [
  { name: 'Wheat', kc: 1.15, season: 'Rabi / Winter', color: 'bg-amber-500/10 text-amber-300 border-amber-500/30' },
  { name: 'Rice', kc: 1.25, season: 'Kharif / Monsoon', color: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' },
  { name: 'Maize', kc: 1.20, season: 'All-season cereal', color: 'bg-yellow-500/10 text-yellow-300 border-yellow-500/30' },
  { name: 'Cotton', kc: 1.15, season: 'Semi-arid commercial', color: 'bg-blue-500/10 text-blue-300 border-blue-500/30' },
  { name: 'Tomato', kc: 1.05, season: 'Horticulture vegetable', color: 'bg-red-500/10 text-red-300 border-red-500/30' },
  { name: 'Sugarcane', kc: 1.30, season: 'High water perennial', color: 'bg-green-500/10 text-green-300 border-green-500/30' },
  { name: 'Potato', kc: 1.10, season: 'Tuber cash crop', color: 'bg-orange-500/10 text-orange-300 border-orange-500/30' },
  { name: 'Barley', kc: 1.00, season: 'Drought-tolerant cereal', color: 'bg-purple-500/10 text-purple-300 border-purple-500/30' },
];

const SOILS = [
  { name: 'Sandy', desc: 'Fast drainage, low retention (split cycles needed)' },
  { name: 'Loamy', desc: 'Standard ideal agronomic balance' },
  { name: 'Clay', desc: 'High retention, slow infiltration (drip advised)' },
  { name: 'Silt', desc: 'Moderate-high retention, smooth texture' },
  { name: 'Peaty', desc: 'High organic matter, high sponge capacity' },
];

export const PredictorPage: React.FC<PredictorPageProps> = ({
  onPredictionComplete,
  onShowToast,
}) => {
  const [formData, setFormData] = useState<PredictionInput>({
    crop_type: 'Wheat',
    soil_type: 'Loamy',
    soil_moisture_pct: 35.0,
    temperature_c: 28.5,
    humidity_pct: 50.0,
    rainfall_mm: 0.0,
    sunlight_hours: 8.5,
    wind_speed_kmh: 12.0,
    area_hectares: 1.0,
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);

  const handleInputChange = (field: keyof PredictionInput, val: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: typeof val === 'string' && !isNaN(Number(val)) && field !== 'crop_type' && field !== 'soil_type'
        ? parseFloat(val)
        : val,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.predict(formData);
      setResult(res);
      onPredictionComplete();
      onShowToast(
        'success',
        'Prediction Complete',
        `Required depth: ${res.predicted_water_demand_mm_day} mm/day (${res.total_volume_m3} m³ volume).`
      );
    } catch (err: any) {
      onShowToast('error', 'Prediction Failed', err.message || 'Error executing ML model');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold font-heading text-white tracking-tight flex items-center gap-2">
          <Droplets className="w-7 h-7 text-emerald-400" />
          Smart Irrigation Water Demand Predictor
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Estimate precision crop evapotranspiration (ETc) requirements using trained Random Forest regression.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Input Form Column (7 Cols) */}
        <div className="lg:col-span-7 glass-panel rounded-2xl p-6 border border-slate-800">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Crop Selector */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
                Select Crop Species
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {CROPS.map((crop) => {
                  const isSelected = formData.crop_type === crop.name;
                  return (
                    <button
                      type="button"
                      key={crop.name}
                      onClick={() => handleInputChange('crop_type', crop.name)}
                      className={`p-3 rounded-xl border text-left transition-all ${
                        isSelected
                          ? 'border-emerald-500 bg-emerald-500/15 text-white ring-1 ring-emerald-500 shadow-md'
                          : 'border-slate-800 bg-slate-900/60 text-slate-300 hover:border-slate-700 hover:bg-slate-800/50'
                      }`}
                    >
                      <div className="font-bold text-sm">{crop.name}</div>
                      <div className="text-[10px] text-slate-400 mt-0.5">Kc: {crop.kc}</div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Soil Texture Selector */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
                Soil Texture Type
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {SOILS.map((soil) => {
                  const isSelected = formData.soil_type === soil.name;
                  return (
                    <button
                      type="button"
                      key={soil.name}
                      onClick={() => handleInputChange('soil_type', soil.name)}
                      className={`p-3 rounded-xl border text-left transition-all ${
                        isSelected
                          ? 'border-emerald-500 bg-emerald-500/15 text-white ring-1 ring-emerald-500'
                          : 'border-slate-800 bg-slate-900/60 text-slate-300 hover:border-slate-700'
                      }`}
                    >
                      <div className="font-bold text-sm">{soil.name}</div>
                      <div className="text-[10px] text-slate-400 truncate mt-0.5">{soil.desc}</div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Environmental Weather & Soil Sliders */}
            <div className="space-y-4 pt-2 border-t border-slate-800">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Environmental & Agro-Meteorological Parameters
              </h3>

              {/* Soil Moisture */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-slate-300">Soil Moisture Level</span>
                  <span className="font-mono text-emerald-400 font-bold">{formData.soil_moisture_pct}%</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="95"
                  step="0.5"
                  value={formData.soil_moisture_pct}
                  onChange={(e) => handleInputChange('soil_moisture_pct', parseFloat(e.target.value))}
                  className="w-full accent-emerald-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-500">
                  <span>Dry (&lt;20%)</span>
                  <span>Optimal (~50-60%)</span>
                  <span>Saturated (&gt;80%)</span>
                </div>
              </div>

              {/* Temperature & Humidity Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-slate-300">Ambient Temperature</span>
                    <span className="font-mono text-amber-400 font-bold">{formData.temperature_c} °C</span>
                  </div>
                  <input
                    type="range"
                    min="10"
                    max="48"
                    step="0.5"
                    value={formData.temperature_c}
                    onChange={(e) => handleInputChange('temperature_c', parseFloat(e.target.value))}
                    className="w-full accent-amber-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
                  />
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-slate-300">Relative Humidity</span>
                    <span className="font-mono text-blue-400 font-bold">{formData.humidity_pct} %</span>
                  </div>
                  <input
                    type="range"
                    min="15"
                    max="95"
                    step="1"
                    value={formData.humidity_pct}
                    onChange={(e) => handleInputChange('humidity_pct', parseFloat(e.target.value))}
                    className="w-full accent-blue-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
                  />
                </div>
              </div>

              {/* Rainfall & Sunshine */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-slate-300">Precipitation / Rainfall</span>
                    <span className="font-mono text-cyan-400 font-bold">{formData.rainfall_mm} mm</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="60"
                    step="0.5"
                    value={formData.rainfall_mm}
                    onChange={(e) => handleInputChange('rainfall_mm', parseFloat(e.target.value))}
                    className="w-full accent-cyan-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
                  />
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-slate-300">Daily Sunlight Duration</span>
                    <span className="font-mono text-yellow-400 font-bold">{formData.sunlight_hours} hrs</span>
                  </div>
                  <input
                    type="range"
                    min="4"
                    max="14"
                    step="0.5"
                    value={formData.sunlight_hours}
                    onChange={(e) => handleInputChange('sunlight_hours', parseFloat(e.target.value))}
                    className="w-full accent-yellow-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
                  />
                </div>
              </div>

              {/* Farm Area */}
              <div className="pt-2">
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
                  Farm Plot Area (Hectares)
                </label>
                <div className="flex items-center space-x-2">
                  {[0.5, 1.0, 2.0, 5.0, 10.0].map((area) => (
                    <button
                      type="button"
                      key={area}
                      onClick={() => handleInputChange('area_hectares', area)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                        formData.area_hectares === area
                          ? 'border-emerald-500 bg-emerald-500/20 text-white'
                          : 'border-slate-800 bg-slate-900 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {area} ha
                    </button>
                  ))}
                  <div className="flex-1 min-w-[100px]">
                    <input
                      type="number"
                      step="0.1"
                      min="0.1"
                      max="1000"
                      value={formData.area_hectares}
                      onChange={(e) => handleInputChange('area_hectares', parseFloat(e.target.value) || 1.0)}
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white text-right font-mono"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-xl bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-slate-950 font-extrabold text-sm shadow-lg shadow-emerald-500/20 flex items-center justify-center space-x-2 transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                  <span>Calculating Evapotranspiration...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 fill-slate-950" />
                  <span>Compute Precision Irrigation Requirement</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Prediction Results Column (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          {result ? (
            <div className="glass-panel rounded-2xl p-6 border border-emerald-500/30 space-y-5 animate-in fade-in-50 duration-300">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                  <h3 className="font-bold font-heading text-white text-base">Inference Output</h3>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  R²: {(result.model_r2 * 100).toFixed(1)}%
                </span>
              </div>

              {/* Main Demand Number */}
              <div className="text-center py-4 bg-slate-950/60 rounded-xl border border-slate-800/80">
                <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Predicted Water Demand</span>
                <div className="mt-1 flex items-baseline justify-center space-x-2">
                  <span className="text-4xl sm:text-5xl font-black font-heading text-emerald-400 tracking-tight">
                    {result.predicted_water_demand_mm_day}
                  </span>
                  <span className="text-sm font-semibold text-slate-300">mm / day</span>
                </div>
                <div className="text-xs text-slate-400 mt-2">
                  For {result.crop_type} on {result.soil_type} soil
                </div>
              </div>

              {/* Volumetric Breakdown */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/60">
                  <div className="text-[11px] text-slate-400 font-semibold uppercase">Total Field Volume</div>
                  <div className="text-lg font-bold font-mono text-white mt-0.5">{result.total_volume_m3} m³</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">{result.area_hectares} ha field plot</div>
                </div>
                <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-700/60">
                  <div className="text-[11px] text-slate-400 font-semibold uppercase">Liters Equivalent</div>
                  <div className="text-lg font-bold font-mono text-cyan-400 mt-0.5">
                    {result.total_volume_liters.toLocaleString()} L
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5">1 mm = 10,000 L / ha</div>
                </div>
              </div>

              {/* Agronomic Advisory Recommendation */}
              <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/30 space-y-2">
                <div className="flex items-center space-x-2 text-emerald-400 text-xs font-bold uppercase tracking-wider">
                  <Clock className="w-4 h-4" />
                  <span>Smart Agronomic Advisory & Schedule</span>
                </div>
                <p className="text-xs text-slate-200 leading-relaxed font-normal">
                  {result.recommendation}
                </p>
              </div>

              {/* Feature Importance / Explainability */}
              {result.feature_contributions && Object.keys(result.feature_contributions).length > 0 && (
                <div className="space-y-2 pt-2 border-t border-slate-800">
                  <div className="flex items-center justify-between text-xs font-bold text-slate-300">
                    <span className="flex items-center gap-1.5">
                      <BarChart2 className="w-3.5 h-3.5 text-emerald-400" />
                      Model Feature Explainability
                    </span>
                    <span className="text-[10px] text-slate-500 font-normal">Relative Weight</span>
                  </div>
                  <div className="space-y-1.5">
                    {Object.entries(result.feature_contributions).slice(0, 5).map(([feature, weight]) => (
                      <div key={feature} className="space-y-0.5">
                        <div className="flex justify-between text-[11px] text-slate-400">
                          <span className="capitalize">{feature.replace('_', ' ').replace('_pct', '%')}</span>
                          <span className="font-mono font-medium text-slate-300">{(weight * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                          <div
                            className="bg-emerald-400 h-full rounded-full transition-all duration-500"
                            style={{ width: `${Math.min(100, Math.max(5, weight * 100))}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Transparent Assumptions & Disclaimers Label */}
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-[11px] text-slate-400 flex items-start space-x-2">
                <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                <p className="leading-relaxed">
                  <strong>Assumptions & Transparency:</strong> {result.assumptions_note}
                </p>
              </div>
            </div>
          ) : (
            <div className="glass-panel rounded-2xl p-8 border border-slate-800 text-center flex flex-col items-center justify-center min-h-[420px] space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-slate-800/80 border border-slate-700/80 flex items-center justify-center text-emerald-400">
                <Cpu className="w-8 h-8 stroke-[1.5]" />
              </div>
              <div className="space-y-1 max-w-xs">
                <h3 className="font-bold font-heading text-white text-base">Awaiting Prediction</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Adjust field parameters on the left and click "Compute Precision Irrigation Requirement" to generate water volume schedules.
                </p>
              </div>
              <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/40 text-left text-xs text-slate-400 space-y-1 w-full max-w-xs">
                <div className="font-semibold text-slate-300 text-[11px] uppercase">Physics Grounding:</div>
                <div className="flex items-center gap-1.5">✓ FAO-56 Penman-Monteith ETc</div>
                <div className="flex items-center gap-1.5">✓ Soil moisture deficit integration</div>
                <div className="flex items-center gap-1.5">✓ USDA effective rainfall deduction</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
