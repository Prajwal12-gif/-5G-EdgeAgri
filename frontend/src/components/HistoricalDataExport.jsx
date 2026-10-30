import React, { useState, useEffect } from 'react';
import { 
  Download, 
  Database, 
  Search, 
  FileSpreadsheet, 
  Calendar,
  Filter,
  CheckCircle2
} from 'lucide-react';
import { api } from '../services/api';

export default function HistoricalDataExport({ selectedZone }) {
  const [readings, setReadings] = useState([]);
  const [limit, setLimit] = useState(50);
  const [loading, setLoading] = useState(false);

  const fetchReadings = async () => {
    setLoading(true);
    try {
      const data = await api.getHistoricalTelemetry(
        selectedZone === 'all' ? null : selectedZone,
        limit,
        48 // 48 hours
      );
      setReadings(data || []);
    } catch (e) {
      console.error("Error fetching historical table:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReadings();
  }, [selectedZone, limit]);

  const csvDownloadUrl = api.getExportCsvUrl(selectedZone);

  return (
    <div className="agri-card rounded-2xl p-6 border border-slate-800 space-y-4">
      {/* Header and Download Button */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-emerald-400" />
            Sensor Telemetry History & CSV Export Engine
          </h2>
          <p className="text-xs text-slate-400">
            Export persistent agricultural time-series records for external modeling in Pandas or R
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5">
            <span className="text-slate-400">Show:</span>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="bg-transparent text-white font-mono focus:outline-none cursor-pointer"
            >
              <option value="25" className="bg-slate-900">25 records</option>
              <option value="50" className="bg-slate-900">50 records</option>
              <option value="100" className="bg-slate-900">100 records</option>
              <option value="500" className="bg-slate-900">500 records</option>
            </select>
          </div>

          <a
            href={csvDownloadUrl}
            download
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-2 shadow-md shadow-emerald-700/25 transition-all active:scale-95"
          >
            <Download className="w-4 h-4" />
            Export Complete CSV Dataset
          </a>
        </div>
      </div>

      {/* Historical Data Table */}
      <div className="overflow-x-auto max-h-96 border border-slate-800/80 rounded-xl">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-slate-900 text-slate-400 border-b border-slate-800 sticky top-0">
            <tr>
              <th className="py-2.5 px-3">ID</th>
              <th className="py-2.5 px-3">Timestamp (UTC)</th>
              <th className="py-2.5 px-3">Zone</th>
              <th className="py-2.5 px-3">Soil Moisture</th>
              <th className="py-2.5 px-3">Temp</th>
              <th className="py-2.5 px-3">Humidity</th>
              <th className="py-2.5 px-3">Tank Level</th>
              <th className="py-2.5 px-3">5G Latency</th>
              <th className="py-2.5 px-3">Environment</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50 text-slate-300">
            {readings.length === 0 ? (
              <tr>
                <td colSpan="9" className="py-6 text-center text-slate-500 text-xs">
                  {loading ? 'Loading historical database records...' : 'No historical records found.'}
                </td>
              </tr>
            ) : (
              readings.map((r) => (
                <tr key={r.id} className="hover:bg-slate-800/30">
                  <td className="py-2 px-3 text-slate-500">#{r.id}</td>
                  <td className="py-2 px-3 text-slate-400">
                    {new Date(r.timestamp).toLocaleString()}
                  </td>
                  <td className="py-2 px-3 font-semibold text-white">
                    {r.zone_name ? r.zone_name.split(' - ')[0] : r.zone_id}
                  </td>
                  <td className="py-2 px-3">
                    <span className={r.soil_moisture <= 18 ? 'text-rose-400 font-bold' : 'text-emerald-400'}>
                      {r.soil_moisture}%
                    </span>
                  </td>
                  <td className="py-2 px-3">{r.temperature}°C</td>
                  <td className="py-2 px-3">{r.humidity}%</td>
                  <td className="py-2 px-3">{r.water_level}%</td>
                  <td className="py-2 px-3 text-cyan-400">{r.network_latency_ms} ms</td>
                  <td className="py-2 px-3">
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400">
                      SIMULATED
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
