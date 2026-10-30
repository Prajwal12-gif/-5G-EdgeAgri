import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  AlertCircle, 
  Info, 
  CheckCheck, 
  Check, 
  Bell, 
  Clock, 
  Flame, 
  Droplet 
} from 'lucide-react';
import { api } from '../services/api';

export default function AlertsFeed({ selectedZone, newAlertNotification }) {
  const [alerts, setAlerts] = useState([]);
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [loading, setLoading] = useState(false);

  const fetchAlerts = async () => {
    try {
      const res = await api.getAlerts(
        selectedZone === 'all' ? null : selectedZone,
        filterSeverity
      );
      setAlerts(res || []);
    } catch (e) {
      console.error("Error fetching alerts:", e);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 5000);
    return () => clearInterval(interval);
  }, [selectedZone, filterSeverity, newAlertNotification]);

  const handleAcknowledge = async (id) => {
    try {
      await api.acknowledgeAlert(id);
      setAlerts(alerts.map(a => a.id === id ? { ...a, acknowledged: true } : a));
    } catch (e) {
      console.error("Error acknowledging alert:", e);
    }
  };

  const handleAcknowledgeAll = async () => {
    try {
      await api.acknowledgeAllAlerts();
      setAlerts(alerts.map(a => ({ ...a, acknowledged: true })));
    } catch (e) {
      console.error("Error acknowledging all alerts:", e);
    }
  };

  const getSeverityStyle = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return {
          border: 'border-rose-500/60',
          bg: 'bg-rose-950/30',
          badge: 'bg-rose-500 text-white animate-pulse',
          icon: <AlertCircle className="w-4 h-4 text-rose-400" />
        };
      case 'HIGH':
        return {
          border: 'border-amber-500/50',
          bg: 'bg-amber-950/20',
          badge: 'bg-amber-500/20 text-amber-300 border border-amber-500/40',
          icon: <Flame className="w-4 h-4 text-amber-400" />
        };
      case 'MEDIUM':
        return {
          border: 'border-cyan-500/40',
          bg: 'bg-cyan-950/20',
          badge: 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40',
          icon: <Droplet className="w-4 h-4 text-cyan-400" />
        };
      default:
        return {
          border: 'border-slate-800',
          bg: 'bg-slate-900/60',
          badge: 'bg-slate-800 text-slate-300',
          icon: <Info className="w-4 h-4 text-slate-400" />
        };
    }
  };

  const unacknowledgedCount = alerts.filter(a => !a.acknowledged).length;

  return (
    <div className="agri-card rounded-2xl p-5 border border-slate-800 flex flex-col h-full">
      {/* Alerts Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Bell className="w-5 h-5 text-amber-400" />
            {unacknowledgedCount > 0 && (
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-rose-500 rounded-full animate-ping" />
            )}
          </div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            Priority Agricultural Alerts
            {unacknowledgedCount > 0 && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 font-mono">
                {unacknowledgedCount} Pending
              </span>
            )}
          </h2>
        </div>

        {unacknowledgedCount > 0 && (
          <button
            onClick={handleAcknowledgeAll}
            className="text-xs text-slate-400 hover:text-emerald-400 flex items-center gap-1 transition-colors"
          >
            <CheckCheck className="w-3.5 h-3.5" /> Acknowledge All
          </button>
        )}
      </div>

      {/* Severity Filter Tabs */}
      <div className="flex gap-1.5 mb-3 text-xs overflow-x-auto pb-1">
        {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM'].map((sev) => (
          <button
            key={sev}
            onClick={() => setFilterSeverity(sev)}
            className={`px-2.5 py-1 rounded-md font-semibold transition-all ${
              filterSeverity === sev
                ? 'bg-slate-700 text-white'
                : 'text-slate-400 hover:text-slate-200 bg-slate-900'
            }`}
          >
            {sev}
          </button>
        ))}
      </div>

      {/* Alerts List */}
      <div className="space-y-3 overflow-y-auto max-h-[380px] pr-1">
        {alerts.length === 0 ? (
          <div className="py-12 text-center text-slate-500 text-xs">
            No active alerts detected. All zone metrics nominal.
          </div>
        ) : (
          alerts.map((alert) => {
            const style = getSeverityStyle(alert.severity);
            const ts = new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

            return (
              <div
                key={alert.id}
                className={`p-3.5 rounded-xl border transition-all ${style.border} ${style.bg} ${
                  alert.acknowledged ? 'opacity-50' : 'opacity-100'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-2">
                    {style.icon}
                    <span className="text-xs font-bold text-white">
                      {alert.zone_name}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${style.badge}`}>
                      {alert.severity}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      {ts}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-200 font-medium mb-1.5">
                  {alert.message}
                </p>

                {alert.suggested_action && (
                  <div className="mt-2 text-[11px] p-2 rounded-lg bg-slate-950/70 border border-slate-800 text-slate-300">
                    <strong className="text-emerald-400">Edge Action:</strong> {alert.suggested_action}
                  </div>
                )}

                <div className="mt-2 flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-800/60 font-mono">
                  <span>Source: {alert.source} • Latency: {alert.response_latency_ms} ms</span>
                  {!alert.acknowledged ? (
                    <button
                      onClick={() => handleAcknowledge(alert.id)}
                      className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white flex items-center gap-1"
                    >
                      <Check className="w-3 h-3 text-emerald-400" /> Acknowledge
                    </button>
                  ) : (
                    <span className="text-slate-600 flex items-center gap-1">
                      <CheckCheck className="w-3 h-3" /> Acknowledged
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
