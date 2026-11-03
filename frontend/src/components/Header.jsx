import React, { useState } from 'react';
import {
  Radio, Wifi, Layers, Activity, Flame, RefreshCw, Cpu, ShieldCheck
} from 'lucide-react';
import { api } from '../services/api';

export default function Header({
  selectedZone,
  setSelectedZone,
  activeProfile,
  wsConnected,
  activeAlertsCount,
  onAnomalyInjected
}) {
  const [injecting, setInjecting] = useState(false);
  const [selectedAnomaly, setSelectedAnomaly] = useState('DROUGHT_SURGE');

  const handleInjectAnomaly = async () => {
    setInjecting(true);
    try {
      // "all" is deliberately sent to the backend when the overview is selected.
      // This makes Reset to Normal restore every zone, not just Zone 1.
      const targetZone = selectedZone === 'all' ? 'all' : selectedZone;
      const result = await api.injectAnomaly(targetZone, selectedAnomaly);
      if (result?.status !== 'success') {
        throw new Error(result?.message || 'The backend rejected the anomaly request.');
      }
      onAnomalyInjected?.(selectedAnomaly, result);
    } catch (error) {
      console.error('Failed to inject/reset anomaly:', error);
      window.alert(`Could not update simulator: ${error.message}`);
    } finally {
      setInjecting(false);
    }
  };

  return (
    <header className="border-b border-slate-800 bg-[#0f172a]/90 backdrop-blur-md sticky top-0 z-50">
      <div className="bg-slate-950/80 px-4 py-1.5 border-b border-slate-800/60 text-xs flex flex-wrap items-center justify-between text-slate-400">
        <div className="flex items-center space-x-3">
          <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
            <Radio className="w-3.5 h-3.5 animate-pulse text-emerald-400" />
            5G-EDGE AGRI • TEAM 14
          </span>
          <span className="hidden sm:inline text-slate-600">|</span>
          <span className="hidden sm:inline">1NT24CS202 — Prajwal Karadi</span>
          <span className="hidden sm:inline text-slate-600">•</span>
          <span className="hidden sm:inline">1NT24CS190 — Padavala Rishi</span>
          <span className="hidden md:inline text-slate-600">•</span>
          <span className="hidden md:inline">B.E Computer Science & Engineering</span>
        </div>
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-amber-500/10 text-amber-300 border border-amber-500/30">
          <ShieldCheck className="w-3 h-3 mr-1 text-amber-400" />
          SIMULATED BENCHMARK ENVIRONMENT (NO PHYSICAL SENSORS REQUIRED)
        </span>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Cpu className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                5G-EdgeAgri
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">v1.0 MEC</span>
              </h1>
            </div>
            <p className="text-xs text-slate-400">Sub-millisecond 5G URLLC Edge Processing & Autonomous Micro-Climate Actuation</p>
          </div>
        </div>

        <div className="flex items-center flex-wrap gap-2.5">
          <div className={`px-2.5 py-1 rounded-lg border text-xs font-mono flex items-center gap-1.5 ${
            wsConnected ? 'bg-emerald-950/40 text-emerald-300 border-emerald-700/50' : 'bg-rose-950/40 text-rose-300 border-rose-700/50'
          }`}>
            <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-400 animate-ping' : 'bg-rose-500'}`} />
            {wsConnected ? 'TELEMETRY LIVE (2s)' : 'DISCONNECTED'}
          </div>
          <div className="px-2.5 py-1 rounded-lg border bg-cyan-950/40 text-cyan-300 border-cyan-700/50 text-xs font-mono flex items-center gap-1.5">
            <Wifi className="w-3.5 h-3.5 text-cyan-400" /><span>5G URLLC (2.2 ms)</span>
          </div>
          <div className="px-2.5 py-1 rounded-lg border bg-slate-900 text-slate-300 border-slate-700 text-xs font-mono flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-indigo-400" /><span>MOSQUITTO / BUS</span>
          </div>

          <div className="flex items-center gap-1 bg-slate-900/90 border border-slate-700 rounded-lg p-1">
            <select
              value={selectedAnomaly}
              onChange={(e) => setSelectedAnomaly(e.target.value)}
              className="bg-transparent text-xs text-slate-200 border-none focus:outline-none px-2 py-0.5 cursor-pointer"
            >
              <option value="DROUGHT_SURGE" className="bg-slate-900">🚨 Slide 9: Drought (Moisture ≤18%)</option>
              <option value="HEATWAVE" className="bg-slate-900">🔥 Heat Stress (&gt;38°C)</option>
              <option value="TANK_DRAIN" className="bg-slate-900">🚰 Water Tank Depletion (&lt;10%)</option>
              <option value="FROST_SPIKE" className="bg-slate-900">❄️ Frost Alert (&lt;4°C)</option>
              <option value="NORMAL" className="bg-slate-900">✅ Reset to Normal (all zones if overview selected)</option>
            </select>
            <button
              onClick={handleInjectAnomaly}
              disabled={injecting}
              className="px-2.5 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-xs font-medium flex items-center gap-1 transition-all disabled:opacity-50"
            >
              {injecting ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Flame className="w-3 h-3 text-amber-400" />}
              {injecting ? 'Applying...' : 'Inject'}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center space-x-2 pt-1 pb-2 overflow-x-auto text-xs">
        <span className="text-slate-400 uppercase tracking-wider font-semibold mr-2 flex items-center gap-1">
          <Activity className="w-3.5 h-3.5" /> Zone:
        </span>
        {[
          { id: 'all', label: 'All Farm Zones (Overview)' },
          { id: 'zone_1', label: 'Zone 1: Winter Wheat (North)' },
          { id: 'zone_2', label: 'Zone 2: Tomato Greenhouse (East)' },
          { id: 'zone_3', label: 'Zone 3: Maize & Fodder (South)' },
        ].map((zone) => (
          <button
            key={zone.id}
            onClick={() => setSelectedZone(zone.id)}
            className={`px-3 py-1.5 rounded-md font-medium transition-all ${
              selectedZone === zone.id
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
            }`}
          >
            {zone.label}
          </button>
        ))}
      </div>
    </header>
  );
}
