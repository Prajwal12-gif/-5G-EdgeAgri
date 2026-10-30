import React from 'react';
import { 
  Droplet, 
  Thermometer, 
  CloudRain, 
  Container, 
  Sun, 
  BatteryCharging, 
  Wifi, 
  Power,
  AlertCircle,
  CheckCircle2,
  Zap
} from 'lucide-react';
import { api } from '../services/api';

export default function LiveSensors({ telemetryData, actuatorsState, selectedZone, onWaterTriggered }) {
  const zonesToDisplay = selectedZone === 'all' 
    ? ['zone_1', 'zone_2', 'zone_3'] 
    : [selectedZone];

  const handleQuickIrrigate = async (zoneId) => {
    try {
      await api.triggerActuator(zoneId, 'START', 150.0, 60);
      if (onWaterTriggered) onWaterTriggered(zoneId);
    } catch (e) {
      console.error("Actuator trigger error:", e);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
          <Zap className="w-5 h-5 text-emerald-400" />
          Real-Time 5G Agricultural Field Telemetry
        </h2>
        <span className="text-xs text-slate-400">
          Telemetry streaming interval: <span className="text-emerald-400 font-mono">2.0s</span>
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {zonesToDisplay.map((zoneId) => {
          const zone = telemetryData[zoneId] || {
            zone_id: zoneId,
            zone_name: `Zone ${zoneId.replace('zone_', '')}`,
            crop_type: 'Field Crops',
            soil_moisture: 35.0,
            temperature: 25.0,
            humidity: 55.0,
            water_level: 75.0,
            solar_radiation: 550.0,
            soil_ph: 6.5,
            battery_level: 95.0,
            network_latency_ms: 2.2,
            simulated_flag: true
          };

          const isActuatorRunning = actuatorsState[zoneId]?.status === 'RUNNING';
          const isCriticalDrought = zone.soil_moisture <= 18.0; // Slide 9 condition
          const isLowMoisture = zone.soil_moisture < 25.0 && !isCriticalDrought;
          const isLowWater = zone.water_level < 20.0;
          const isHeatStress = zone.temperature > 37.0;

          return (
            <div 
              key={zoneId} 
              className={`agri-card rounded-2xl p-5 border transition-all duration-300 relative overflow-hidden ${
                isCriticalDrought 
                  ? 'border-rose-500/70 shadow-lg shadow-rose-950/40 bg-gradient-to-b from-rose-950/30 to-slate-900' 
                  : isLowMoisture
                  ? 'border-amber-500/50 bg-gradient-to-b from-amber-950/20 to-slate-900'
                  : 'border-slate-800 hover:border-emerald-500/40'
              }`}
            >
              {/* Slide 9 Critical Condition Alert Banner */}
              {isCriticalDrought && (
                <div className="absolute top-0 left-0 right-0 bg-rose-600/90 text-white text-[11px] font-bold py-1 px-3 flex items-center justify-between tracking-wide uppercase">
                  <span className="flex items-center gap-1.5 animate-pulse">
                    <AlertCircle className="w-3.5 h-3.5" /> CRITICAL DROUGHT (≤18%)
                  </span>
                  <span>IRRIGATION REQUIRED</span>
                </div>
              )}

              {/* Card Header */}
              <div className={`flex items-start justify-between ${isCriticalDrought ? 'mt-4' : ''}`}>
                <div>
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    {zone.zone_name}
                  </h3>
                  <p className="text-xs text-slate-400">{zone.crop_type}</p>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                    SIMULATED SENSOR
                  </span>
                  <span className="text-[10px] font-mono text-cyan-400 flex items-center gap-1">
                    <Wifi className="w-2.5 h-2.5" /> {zone.network_latency_ms} ms
                  </span>
                </div>
              </div>

              {/* Primary Gauge: Soil Moisture */}
              <div className="mt-5 p-3.5 rounded-xl bg-slate-900/80 border border-slate-800/80">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
                    <Droplet className="w-4 h-4 text-cyan-400" />
                    Soil Moisture
                  </span>
                  <span className={`text-xl font-extrabold font-mono ${
                    isCriticalDrought ? 'text-rose-400 animate-pulse' : isLowMoisture ? 'text-amber-400' : 'text-emerald-400'
                  }`}>
                    {zone.soil_moisture}%
                  </span>
                </div>

                {/* Progress Bar with Threshold Reference Markers */}
                <div className="mt-2.5 relative">
                  <div className="h-2.5 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-700 rounded-full ${
                        isCriticalDrought 
                          ? 'bg-rose-500' 
                          : isLowMoisture 
                          ? 'bg-amber-400' 
                          : 'bg-emerald-500'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(0, zone.soil_moisture))}%` }}
                    />
                  </div>
                  {/* Slide 9 18% Threshold Marker */}
                  <div 
                    className="absolute top-0 bottom-0 w-0.5 bg-rose-400" 
                    style={{ left: '18%' }}
                    title="Slide 9: Critical Drought Threshold (18%)"
                  />
                </div>
                <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                  <span className="text-rose-400">0% (Critical ≤18%)</span>
                  <span>Target: 35-65%</span>
                  <span>100% Saturation</span>
                </div>
              </div>

              {/* Grid Metrics: Temp, Humidity, Reservoir, Solar */}
              <div className="grid grid-cols-2 gap-3 mt-3">
                {/* Temperature */}
                <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/60 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Thermometer className={`w-4 h-4 ${isHeatStress ? 'text-rose-400' : 'text-amber-400'}`} />
                    <span className="text-xs text-slate-400">Temp</span>
                  </div>
                  <span className={`text-sm font-bold font-mono ${isHeatStress ? 'text-rose-400' : 'text-slate-200'}`}>
                    {zone.temperature}°C
                  </span>
                </div>

                {/* Humidity */}
                <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/60 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CloudRain className="w-4 h-4 text-sky-400" />
                    <span className="text-xs text-slate-400">Humidity</span>
                  </div>
                  <span className="text-sm font-bold font-mono text-slate-200">
                    {zone.humidity}%
                  </span>
                </div>

                {/* Water Reservoir */}
                <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/60 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Container className={`w-4 h-4 ${isLowWater ? 'text-rose-400' : 'text-indigo-400'}`} />
                    <span className="text-xs text-slate-400">Tank Level</span>
                  </div>
                  <span className={`text-sm font-bold font-mono ${isLowWater ? 'text-rose-400' : 'text-slate-200'}`}>
                    {zone.water_level}%
                  </span>
                </div>

                {/* Solar Radiation */}
                <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/60 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sun className="w-4 h-4 text-amber-400" />
                    <span className="text-xs text-slate-400">Solar W/m²</span>
                  </div>
                  <span className="text-sm font-bold font-mono text-slate-200">
                    {zone.solar_radiation}
                  </span>
                </div>
              </div>

              {/* Local Actuation State & Manual Control */}
              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs">
                  <span className={`w-2.5 h-2.5 rounded-full ${isActuatorRunning ? 'bg-cyan-400 animate-ping' : 'bg-slate-600'}`} />
                  <span className="text-slate-300">
                    Valve: <strong className={isActuatorRunning ? 'text-cyan-400' : 'text-slate-400'}>
                      {isActuatorRunning ? 'IRRIGATING (AUTO/EDGE)' : 'STANDBY (CLOSED)'}
                    </strong>
                  </span>
                </div>

                <button
                  onClick={() => handleQuickIrrigate(zoneId)}
                  disabled={isActuatorRunning}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                    isActuatorRunning
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 cursor-not-allowed'
                      : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-700/20 active:scale-95'
                  }`}
                >
                  <Power className="w-3.5 h-3.5" />
                  {isActuatorRunning ? 'Irrigating...' : 'Water 150L'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
