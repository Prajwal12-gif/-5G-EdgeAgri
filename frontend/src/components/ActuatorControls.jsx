import React, { useState, useEffect } from 'react';
import { 
  Power, 
  Droplet, 
  CheckCircle, 
  XCircle, 
  Clock, 
  History, 
  RotateCcw,
  SlidersHorizontal
} from 'lucide-react';
import { api } from '../services/api';

export default function ActuatorControls({ selectedZone, onActionExecuted }) {
  const [actuatorsStatus, setActuatorsStatus] = useState({});
  const [actuatorHistory, setActuatorHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchStatusAndHistory = async () => {
    try {
      const [statusRes, historyRes] = await Promise.all([
        api.getActuatorsStatus(),
        api.getActuatorHistory(selectedZone === 'all' ? null : selectedZone, 15)
      ]);
      setActuatorsStatus(statusRes.zones || {});
      setActuatorHistory(historyRes || []);
    } catch (e) {
      console.error("Error fetching actuator data:", e);
    }
  };

  useEffect(() => {
    fetchStatusAndHistory();
    const interval = setInterval(fetchStatusAndHistory, 4000);
    return () => clearInterval(interval);
  }, [selectedZone]);

  const handleToggleValve = async (zoneId, currentOpen) => {
    setLoading(true);
    try {
      const action = currentOpen ? 'STOP' : 'START';
      await api.triggerActuator(zoneId, action, 200.0, 90);
      await fetchStatusAndHistory();
      if (onActionExecuted) onActionExecuted(zoneId, action);
    } catch (e) {
      console.error("Failed to toggle valve:", e);
    } finally {
      setLoading(false);
    }
  };

  const zonesList = selectedZone === 'all' 
    ? [
        { id: 'zone_1', name: 'Zone 1: Wheat Fields' },
        { id: 'zone_2', name: 'Zone 2: Greenhouse' },
        { id: 'zone_3', name: 'Zone 3: Maize Sector' }
      ]
    : [{ id: selectedZone, name: selectedZone.replace('_', ' ').toUpperCase() }];

  return (
    <div className="agri-card rounded-2xl p-5 border border-slate-800 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-cyan-500/20 text-cyan-400">
            <SlidersHorizontal className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              Field Actuators & Irrigation Control (MEC Local Loop)
            </h2>
            <p className="text-xs text-slate-400">
              Direct sub-millisecond edge solenoid valve triggering with feedback verification
            </p>
          </div>
        </div>
      </div>

      {/* Actuator Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {zonesList.map((z) => {
          const zoneState = actuatorsStatus[z.id];
          const isOpen = zoneState?.valve_open;

          return (
            <div 
              key={z.id}
              className={`p-4 rounded-xl border transition-all ${
                isOpen 
                  ? 'bg-gradient-to-b from-cyan-950/40 to-slate-900 border-cyan-500 shadow-md shadow-cyan-950/40' 
                  : 'bg-slate-900/60 border-slate-800'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-white">{z.name}</span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold flex items-center gap-1 ${
                  isOpen 
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' 
                    : 'bg-slate-800 text-slate-400'
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${isOpen ? 'bg-cyan-400 animate-ping' : 'bg-slate-500'}`} />
                  {isOpen ? 'OPEN / PUMPING' : 'CLOSED'}
                </span>
              </div>

              <div className="text-xs text-slate-400 space-y-1 font-mono mb-4">
                <div>Type: Solenoid Relay 24V</div>
                <div>Status: {isOpen ? 'Discharging 2.5 L/s' : 'Idle'}</div>
              </div>

              <button
                onClick={() => handleToggleValve(z.id, isOpen)}
                disabled={loading}
                className={`w-full py-2 rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                  isOpen
                    ? 'bg-rose-600/80 hover:bg-rose-600 text-white shadow-md shadow-rose-900/30'
                    : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-900/30'
                }`}
              >
                <Power className="w-3.5 h-3.5" />
                {isOpen ? 'Halt Irrigation (Close Valve)' : 'Start Irrigation Cycle'}
              </button>
            </div>
          );
        })}
      </div>

      {/* Actuation History Log Table */}
      <div className="pt-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
          <History className="w-3.5 h-3.5 text-slate-400" />
          Recent Actuation Events (Persistent SQLite Log)
        </h3>

        <div className="overflow-x-auto max-h-48 border border-slate-800/80 rounded-xl">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900 text-slate-400 border-b border-slate-800 sticky top-0">
              <tr>
                <th className="py-2 px-3">Time</th>
                <th className="py-2 px-3">Zone</th>
                <th className="py-2 px-3">Action</th>
                <th className="py-2 px-3">Dosage</th>
                <th className="py-2 px-3">Triggered By</th>
                <th className="py-2 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 text-slate-300">
              {actuatorHistory.length === 0 ? (
                <tr>
                  <td colSpan="6" className="py-4 text-center text-slate-500 text-xs">
                    No recent actuation logs recorded yet.
                  </td>
                </tr>
              ) : (
                actuatorHistory.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/30">
                    <td className="py-2 px-3 text-slate-400">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-2 px-3 text-white font-semibold">{log.zone_id}</td>
                    <td className="py-2 px-3">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                        log.action === 'START' ? 'bg-cyan-500/20 text-cyan-300' : 'bg-slate-800 text-slate-400'
                      }`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="py-2 px-3">{log.dosage_liters} L ({log.duration_seconds}s)</td>
                    <td className="py-2 px-3 text-slate-400">{log.triggered_by}</td>
                    <td className="py-2 px-3 text-emerald-400 font-semibold">{log.status}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
