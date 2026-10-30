import React, { useState, useEffect } from 'react';
import { 
  AreaChart, 
  Area, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  CartesianGrid, 
  ReferenceLine 
} from 'recharts';
import { BarChart3, Clock, TrendingUp, RefreshCcw } from 'lucide-react';
import { api } from '../services/api';

export default function TelemetryCharts({ selectedZone }) {
  const [historyData, setHistoryData] = useState([]);
  const [activeMetric, setActiveMetric] = useState('moisture'); // moisture, temp_humidity, reservoir, latency
  const [timeWindowHours, setTimeWindowHours] = useState(24);
  const [loading, setLoading] = useState(false);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await api.getHistoricalTelemetry(
        selectedZone === 'all' ? null : selectedZone,
        150,
        timeWindowHours
      );
      // Format timestamps for chart
      const formatted = (data || []).map((item) => {
        const d = new Date(item.timestamp);
        return {
          ...item,
          timeLabel: d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          rawTime: d.getTime()
        };
      }).reverse();
      setHistoryData(formatted);
    } catch (e) {
      console.error("Failed to fetch historical telemetry:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, 15000); // refresh history every 15s
    return () => clearInterval(interval);
  }, [selectedZone, timeWindowHours]);

  return (
    <div className="agri-card rounded-2xl p-5 border border-slate-800">
      {/* Chart Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-5">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            Historical Environmental Analytics & Threshold Projections
          </h2>
          <p className="text-xs text-slate-400">
            Persistent SQLite time-series data synced from 5G Edge nodes
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2">
          {/* Metric Selector Buttons */}
          <div className="flex bg-slate-900 border border-slate-800 rounded-lg p-1 text-xs">
            <button
              onClick={() => setActiveMetric('moisture')}
              className={`px-3 py-1 rounded-md font-medium transition-all ${
                activeMetric === 'moisture'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Soil Moisture (%)
            </button>
            <button
              onClick={() => setActiveMetric('temp_humidity')}
              className={`px-3 py-1 rounded-md font-medium transition-all ${
                activeMetric === 'temp_humidity'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Temp & Humidity
            </button>
            <button
              onClick={() => setActiveMetric('reservoir')}
              className={`px-3 py-1 rounded-md font-medium transition-all ${
                activeMetric === 'reservoir'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Water Reservoir
            </button>
            <button
              onClick={() => setActiveMetric('latency')}
              className={`px-3 py-1 rounded-md font-medium transition-all ${
                activeMetric === 'latency'
                  ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              5G Latency (ms)
            </button>
          </div>

          {/* Time Window Switcher */}
          <div className="flex bg-slate-900 border border-slate-800 rounded-lg p-1 text-xs">
            {[
              { hours: 1, label: '1H' },
              { hours: 6, label: '6H' },
              { hours: 24, label: '24H' },
            ].map((t) => (
              <button
                key={t.hours}
                onClick={() => setTimeWindowHours(t.hours)}
                className={`px-2.5 py-1 rounded font-medium ${
                  timeWindowHours === t.hours
                    ? 'bg-slate-700 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          <button
            onClick={fetchHistory}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all"
            title="Refresh Historical Data"
          >
            <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-72 w-full">
        {historyData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-500 text-sm">
            Waiting for telemetry history...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            {activeMetric === 'moisture' ? (
              <AreaChart data={historyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="moistGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.6}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" vertical={false} />
                <XAxis dataKey="timeLabel" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[0, 100]} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} 
                  itemStyle={{ color: '#10b981' }}
                />
                {/* Critical Threshold 18% Reference Line from Slide 9 */}
                <ReferenceLine 
                  y={18} 
                  stroke="#f43f5e" 
                  strokeDasharray="4 4" 
                  label={{ value: 'CRITICAL IRRIGATION TRIGGER (18%)', fill: '#f43f5e', fontSize: 10, position: 'top' }} 
                />
                <Area 
                  type="monotone" 
                  dataKey="soil_moisture" 
                  name="Soil Moisture (%)" 
                  stroke="#10b981" 
                  strokeWidth={2.5} 
                  fillOpacity={1} 
                  fill="url(#moistGradient)" 
                />
              </AreaChart>
            ) : activeMetric === 'temp_humidity' ? (
              <LineChart data={historyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" vertical={false} />
                <XAxis dataKey="timeLabel" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} />
                <ReferenceLine y={38} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'Heat Stress (38°C)', fill: '#f59e0b', fontSize: 10 }} />
                <Line type="monotone" dataKey="temperature" name="Temperature (°C)" stroke="#f59e0b" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="humidity" name="Humidity (%)" stroke="#38bdf8" strokeWidth={2} dot={false} />
              </LineChart>
            ) : activeMetric === 'reservoir' ? (
              <AreaChart data={historyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="tankGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.6}/>
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" vertical={false} />
                <XAxis dataKey="timeLabel" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[0, 100]} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} />
                <ReferenceLine y={20} stroke="#f43f5e" strokeDasharray="3 3" label={{ value: 'Low Water Refill Trigger (20%)', fill: '#f43f5e', fontSize: 10 }} />
                <Area type="monotone" dataKey="water_level" name="Reservoir Level (%)" stroke="#06b6d4" strokeWidth={2.5} fill="url(#tankGradient)" />
              </AreaChart>
            ) : (
              <LineChart data={historyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" vertical={false} />
                <XAxis dataKey="timeLabel" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} />
                <Line type="monotone" dataKey="network_latency_ms" name="5G Latency (ms)" stroke="#818cf8" strokeWidth={2} dot={false} />
              </LineChart>
            )}
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
