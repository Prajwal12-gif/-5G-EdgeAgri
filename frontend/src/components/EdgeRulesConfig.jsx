import React, { useState, useEffect } from 'react';
import { 
  Sliders, 
  Save, 
  Check, 
  RotateCcw, 
  ShieldAlert, 
  Droplet, 
  Thermometer, 
  Container,
  Cpu
} from 'lucide-react';
import { api } from '../services/api';

export default function EdgeRulesConfig({ selectedZone }) {
  const targetZone = selectedZone === 'all' ? 'zone_1' : selectedZone;
  const [configs, setConfigs] = useState(null);
  const [formState, setFormState] = useState({
    critical_moisture: 18.0,
    min_moisture: 25.0,
    max_temperature: 37.0,
    min_water_level: 20.0,
    irrigation_duration_seconds: 120,
    auto_actuation_enabled: true
  });
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    async function loadConfigs() {
      try {
        const res = await api.getEdgeConfigs();
        setConfigs(res);
        if (res && res[targetZone]) {
          setFormState({
            critical_moisture: res[targetZone].critical_moisture,
            min_moisture: res[targetZone].min_moisture,
            max_temperature: res[targetZone].max_temperature,
            min_water_level: res[targetZone].min_water_level,
            irrigation_duration_seconds: res[targetZone].irrigation_duration_seconds,
            auto_actuation_enabled: res[targetZone].auto_actuation_enabled
          });
        }
      } catch (e) {
        console.error("Error loading edge configs:", e);
      }
    }
    loadConfigs();
  }, [targetZone]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.updateEdgeConfig(targetZone, formState);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 2500);
    } catch (e) {
      console.error("Failed to update edge config:", e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="agri-card rounded-2xl p-5 border border-slate-800 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              Edge Decision Rules & Threshold Configurator
            </h2>
            <p className="text-xs text-slate-400">
              Configuring local MEC rule engine for {targetZone.replace('_', ' ').toUpperCase()}
            </p>
          </div>
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-emerald-700/20 transition-all active:scale-95"
        >
          {savedSuccess ? <Check className="w-3.5 h-3.5 text-white" /> : <Save className="w-3.5 h-3.5" />}
          {savedSuccess ? 'Rules Updated!' : saving ? 'Saving...' : 'Apply Rules'}
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        {/* Critical Moisture Threshold (Slide 9 default: 18%) */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-rose-300 flex items-center gap-1">
              <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
              Critical Drought Threshold (≤)
            </span>
            <span className="font-mono font-bold text-rose-400 text-sm">
              {formState.critical_moisture}%
            </span>
          </div>
          <input
            type="range"
            min="10"
            max="30"
            step="1"
            value={formState.critical_moisture}
            onChange={(e) => setFormState({ ...formState, critical_moisture: Number(e.target.value) })}
            className="w-full accent-rose-500 cursor-pointer"
          />
          <span className="text-[10px] text-slate-500 block">
            Slide 9 requirement: Triggers emergency "IRRIGATION REQUIRED" and opens valve immediately.
          </span>
        </div>

        {/* Warning Moisture Threshold */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-amber-300 flex items-center gap-1">
              <Droplet className="w-3.5 h-3.5 text-amber-400" />
              Warning Moisture Threshold (&lt;)
            </span>
            <span className="font-mono font-bold text-amber-400 text-sm">
              {formState.min_moisture}%
            </span>
          </div>
          <input
            type="range"
            min="15"
            max="45"
            step="1"
            value={formState.min_moisture}
            onChange={(e) => setFormState({ ...formState, min_moisture: Number(e.target.value) })}
            className="w-full accent-amber-500 cursor-pointer"
          />
          <span className="text-[10px] text-slate-500 block">
            Generates high-priority notification to schedule upcoming watering cycle.
          </span>
        </div>

        {/* Heat Stress Temperature Threshold */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-slate-200 flex items-center gap-1">
              <Thermometer className="w-3.5 h-3.5 text-orange-400" />
              Heat Stress Threshold (&gt;)
            </span>
            <span className="font-mono font-bold text-orange-400 text-sm">
              {formState.max_temperature}°C
            </span>
          </div>
          <input
            type="range"
            min="28"
            max="48"
            step="0.5"
            value={formState.max_temperature}
            onChange={(e) => setFormState({ ...formState, max_temperature: Number(e.target.value) })}
            className="w-full accent-orange-500 cursor-pointer"
          />
          <span className="text-[10px] text-slate-500 block">
            Deploys misting canopy recommendations to prevent crop heat damage.
          </span>
        </div>

        {/* Minimum Water Tank Level */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800/80 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-cyan-300 flex items-center gap-1">
              <Container className="w-3.5 h-3.5 text-cyan-400" />
              Minimum Reservoir Level (&lt;)
            </span>
            <span className="font-mono font-bold text-cyan-400 text-sm">
              {formState.min_water_level}%
            </span>
          </div>
          <input
            type="range"
            min="10"
            max="50"
            step="1"
            value={formState.min_water_level}
            onChange={(e) => setFormState({ ...formState, min_water_level: Number(e.target.value) })}
            className="w-full accent-cyan-500 cursor-pointer"
          />
          <span className="text-[10px] text-slate-500 block">
            Restricts automated high-volume irrigation when tank supply drops too low.
          </span>
        </div>
      </div>

      {/* Autonomous Actuation Toggle & Irrigation Duration */}
      <div className="pt-2 flex flex-wrap items-center justify-between gap-4 border-t border-slate-800 text-xs">
        <label className="flex items-center gap-2.5 cursor-pointer">
          <input
            type="checkbox"
            checked={formState.auto_actuation_enabled}
            onChange={(e) => setFormState({ ...formState, auto_actuation_enabled: e.target.checked })}
            className="w-4 h-4 rounded text-emerald-500 focus:ring-emerald-500 accent-emerald-500"
          />
          <span className="text-slate-200 font-medium">
            Enable Autonomous Edge Actuation (Opens Solenoid Valve automatically upon alert)
          </span>
        </label>

        <div className="flex items-center gap-2">
          <span className="text-slate-400">Default Run Duration:</span>
          <input
            type="number"
            min="30"
            max="600"
            step="10"
            value={formState.irrigation_duration_seconds}
            onChange={(e) => setFormState({ ...formState, irrigation_duration_seconds: Number(e.target.value) })}
            className="w-20 px-2 py-1 rounded bg-slate-900 border border-slate-700 text-white font-mono text-center focus:outline-none"
          />
          <span className="text-slate-400">sec</span>
        </div>
      </div>
    </div>
  );
}
