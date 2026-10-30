import React, { useState, useEffect } from 'react';
import { 
  Wifi, 
  Activity, 
  Radio, 
  AlertTriangle, 
  ArrowUpRight, 
  CheckCircle,
  Network
} from 'lucide-react';
import { api } from '../services/api';

export default function NetworkSimulator({ activeProfileKey, onProfileChanged }) {
  const [networkStatus, setNetworkStatus] = useState(null);
  const [profiles, setProfiles] = useState({});
  const [loading, setLoading] = useState(false);

  const fetchStatus = async () => {
    try {
      const [statusRes, profilesRes] = await Promise.all([
        api.getNetworkStatus(),
        api.getNetworkProfiles()
      ]);
      setNetworkStatus(statusRes);
      setProfiles(profilesRes.profiles || {});
    } catch (e) {
      console.error("Failed to fetch network simulation status:", e);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleSwitchProfile = async (key) => {
    setLoading(true);
    try {
      await api.setNetworkProfile(key);
      await fetchStatus();
      if (onProfileChanged) onProfileChanged(key);
    } catch (e) {
      console.error("Error setting network profile:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="agri-card rounded-2xl p-6 border border-slate-800 space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <span className="p-2 rounded-lg bg-cyan-500/20 text-cyan-400">
            <Radio className="w-5 h-5" />
          </span>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              5G Network Simulation & Wireless Layer Control
            </h2>
            <p className="text-xs text-slate-400">
              Configurable 3GPP channel emulation: URLLC sub-millisecond, eMBB broadband, and 4G legacy
            </p>
          </div>
        </div>

        <span className="px-2.5 py-1 rounded-full text-xs font-mono bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
          Profile: {networkStatus?.active_profile_name || '5G URLLC'}
        </span>
      </div>

      {/* Network Live Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-slate-400 block text-[11px]">Base Radio Latency</span>
          <span className="text-lg font-bold font-mono text-cyan-400">
            {networkStatus?.base_latency_ms || 2.2} ms
          </span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-slate-400 block text-[11px]">Radio Jitter (σ)</span>
          <span className="text-lg font-bold font-mono text-indigo-400">
            ±{networkStatus?.jitter_ms || 0.4} ms
          </span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-slate-400 block text-[11px]">Air-Interface Bandwidth</span>
          <span className="text-lg font-bold font-mono text-emerald-400">
            {networkStatus?.bandwidth_mbps || 1000} Mbps
          </span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-slate-400 block text-[11px]">Simulated Packet Loss</span>
          <span className="text-lg font-bold font-mono text-amber-400">
            {networkStatus?.measured_loss_rate_pct || 0.0}%
          </span>
        </div>
      </div>

      {/* Profile Selector Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 pt-1">
        {Object.entries(profiles).map(([key, prof]) => {
          const isActive = (networkStatus?.active_profile_key || '5g_urllc') === key;
          return (
            <button
              key={key}
              onClick={() => handleSwitchProfile(key)}
              disabled={loading}
              className={`p-3.5 rounded-xl text-left border transition-all ${
                isActive
                  ? 'bg-gradient-to-b from-cyan-950/40 to-slate-900 border-cyan-500 shadow-md shadow-cyan-950/50'
                  : 'bg-slate-900/50 border-slate-800 hover:border-slate-700 hover:bg-slate-800/40'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className={`text-xs font-bold ${isActive ? 'text-cyan-300' : 'text-slate-200'}`}>
                  {prof.name.split(' ')[0]} {prof.name.split(' ')[1]}
                </span>
                {isActive && <CheckCircle className="w-3.5 h-3.5 text-cyan-400" />}
              </div>
              <p className="text-[11px] text-slate-400 line-clamp-2 mb-2 leading-relaxed">
                {prof.description}
              </p>
              <div className="text-[10px] font-mono text-slate-500 flex justify-between pt-1 border-t border-slate-800/60">
                <span>{prof.base_latency_ms} ms</span>
                <span>{prof.bandwidth_mbps} Mbps</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
