import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import LiveSensors from './components/LiveSensors';
import TelemetryCharts from './components/TelemetryCharts';
import EdgeVsCloudComparison from './components/EdgeVsCloudComparison';
import NetworkSimulator from './components/NetworkSimulator';
import AlertsFeed from './components/AlertsFeed';
import EdgeRulesConfig from './components/EdgeRulesConfig';
import ActuatorControls from './components/ActuatorControls';
import HistoricalDataExport from './components/HistoricalDataExport';

import { telemetryWs } from './services/websocket';
import { api } from './services/api';

import { 
  LayoutDashboard, 
  Scale, 
  SlidersHorizontal, 
  Sliders, 
  Database, 
  Radio, 
  Wifi, 
  Zap, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';

export default function App() {
  const [selectedZone, setSelectedZone] = useState('all');
  const [activeTab, setActiveTab] = useState('overview'); // overview, benchmark, actuators, config, history
  const [wsConnected, setWsConnected] = useState(false);
  const [telemetryData, setTelemetryData] = useState({});
  const [actuatorsState, setActuatorsState] = useState({});
  const [activeProfile, setActiveProfile] = useState('5g_urllc');
  const [toastMessage, setToastMessage] = useState(null);
  const [newAlertTrigger, setNewAlertTrigger] = useState(0);

  // Initial fetch
  useEffect(() => {
    async function initData() {
      try {
        const live = await api.getLiveTelemetry();
        if (live && live.zones) {
          setTelemetryData(live.zones);
        }
        const acts = await api.getActuatorsStatus();
        if (acts && acts.zones) {
          setActuatorsState(acts.zones);
        }
      } catch (e) {
        console.warn("Initial API load:", e);
      }
    }
    initData();
  }, []);

  // Subscribe to real-time WebSocket stream
  useEffect(() => {
    telemetryWs.connect();

    const unsubscribe = telemetryWs.subscribe((msg) => {
      if (msg.event === 'CONNECTION_STATUS') {
        setWsConnected(msg.connected);
      } else if (msg.event === 'TELEMETRY_UPDATE') {
        // Map list of readings to zone dictionary
        if (msg.readings) {
          const mapped = {};
          msg.readings.forEach(r => { mapped[r.zone_id] = r; });
          setTelemetryData(prev => ({ ...prev, ...mapped }));
        }
        if (msg.actuators) {
          setActuatorsState(msg.actuators);
        }
      } else if (msg.event === 'NEW_ALERT') {
        setNewAlertTrigger(prev => prev + 1);
        setToastMessage({
          title: `[${msg.data.severity}] ${msg.data.alert_type}`,
          message: msg.data.message,
          action: msg.data.suggested_action,
          severity: msg.data.severity
        });
        setTimeout(() => setToastMessage(null), 6000);
      } else if (msg.event === 'INITIAL_STATE') {
        if (msg.readings) {
          const mapped = {};
          msg.readings.forEach(r => { mapped[r.zone_id] = r; });
          setTelemetryData(mapped);
        }
        if (msg.actuators) {
          setActuatorsState(msg.actuators);
        }
      }
    });

    return () => unsubscribe();
  }, []);

  return (
    <div className="min-h-screen bg-[#0b1120] text-slate-100 flex flex-col">
      {/* Top Header */}
      <Header
        selectedZone={selectedZone}
        setSelectedZone={setSelectedZone}
        activeProfile={activeProfile}
        wsConnected={wsConnected}
        onAnomalyInjected={(anomaly) => {
          setToastMessage({
            title: `Synthetic Anomaly Injected`,
            message: `Mode activated: ${anomaly}. Evaluating sub-millisecond edge rules...`,
            severity: 'HIGH'
          });
          setTimeout(() => setToastMessage(null), 4000);
        }}
      />

      {/* Floating Alert Notification Toast */}
      {toastMessage && (
        <div className="fixed bottom-5 right-5 z-50 max-w-md animate-bounce">
          <div className={`p-4 rounded-xl border shadow-2xl backdrop-blur-md ${
            toastMessage.severity === 'CRITICAL'
              ? 'bg-rose-950/90 border-rose-500 text-rose-100 shadow-rose-950/60'
              : 'bg-amber-950/90 border-amber-500 text-amber-100 shadow-amber-950/60'
          }`}>
            <div className="flex items-start gap-3">
              <AlertCircle className={`w-5 h-5 flex-shrink-0 ${
                toastMessage.severity === 'CRITICAL' ? 'text-rose-400' : 'text-amber-400'
              }`} />
              <div className="text-xs">
                <div className="font-bold text-sm mb-1">{toastMessage.title}</div>
                <div>{toastMessage.message}</div>
                {toastMessage.action && (
                  <div className="mt-2 pt-2 border-t border-white/20 font-mono text-[11px] text-white">
                    <strong>Action:</strong> {toastMessage.action}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Navigation Tabs Bar */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 flex-wrap gap-2">
          <div className="flex items-center space-x-1 sm:space-x-2 text-xs font-semibold overflow-x-auto">
            {[
              { id: 'overview', label: 'Dashboard Overview', icon: LayoutDashboard },
              { id: 'benchmark', label: 'Edge vs Cloud Benchmark (Slide 8)', icon: Scale },
              { id: 'actuators', label: 'Irrigation Actuators', icon: SlidersHorizontal },
              { id: 'config', label: 'Edge Rule Thresholds', icon: Sliders },
              { id: 'network', label: '5G Radio Simulator', icon: Radio },
              { id: 'history', label: 'Historical Data & CSV', icon: Database },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-3 py-2 rounded-xl flex items-center gap-1.5 transition-all ${
                    isActive
                      ? 'bg-emerald-600 text-white shadow-md shadow-emerald-700/25'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          <div className="text-xs font-mono text-slate-500 hidden lg:block">
            MEC Architecture • Sub-millisecond Execution
          </div>
        </div>

        {/* Tab 1: Dashboard Overview (Telemetry + Charts + Alerts) */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <LiveSensors
              telemetryData={telemetryData}
              actuatorsState={actuatorsState}
              selectedZone={selectedZone}
              onWaterTriggered={(zId) => {
                setToastMessage({
                  title: "Emergency Irrigation Valve Activated",
                  message: `150 Liters dispatched to ${zId.toUpperCase()}`,
                  severity: "MEDIUM"
                });
                setTimeout(() => setToastMessage(null), 3500);
              }}
            />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <TelemetryCharts selectedZone={selectedZone} />
              </div>
              <div className="lg:col-span-1">
                <AlertsFeed 
                  selectedZone={selectedZone} 
                  newAlertNotification={newAlertTrigger} 
                />
              </div>
            </div>

            {/* Quick Embedded Benchmark Preview */}
            <div className="pt-2">
              <EdgeVsCloudComparison />
            </div>
          </div>
        )}

        {/* Tab 2: Edge vs Cloud Controlled Benchmark Laboratory */}
        {activeTab === 'benchmark' && (
          <div className="space-y-6">
            <EdgeVsCloudComparison />
            <NetworkSimulator 
              activeProfileKey={activeProfile}
              onProfileChanged={(k) => setActiveProfile(k)}
            />
          </div>
        )}

        {/* Tab 3: Actuator Controls & History Logs */}
        {activeTab === 'actuators' && (
          <ActuatorControls selectedZone={selectedZone} />
        )}

        {/* Tab 4: Edge Rule Configurator */}
        {activeTab === 'config' && (
          <EdgeRulesConfig selectedZone={selectedZone} />
        )}

        {/* Tab 5: 5G Network Simulation Settings */}
        {activeTab === 'network' && (
          <div className="space-y-6">
            <NetworkSimulator 
              activeProfileKey={activeProfile}
              onProfileChanged={(k) => setActiveProfile(k)}
            />
          </div>
        )}

        {/* Tab 6: Historical Data & CSV Export */}
        {activeTab === 'history' && (
          <HistoricalDataExport selectedZone={selectedZone} />
        )}
      </main>

      {/* Footer with Research References from Slide 10 */}
      <footer className="mt-auto border-t border-slate-800 bg-slate-950/80 px-4 py-5 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div>
            <span className="font-semibold text-slate-300">5G-EdgeAgri:</span> A Software-Based 5G-Enabled Edge Computing Framework for Real-Time Smart Agriculture.
            <div className="text-[11px] text-slate-600 mt-0.5">
              Team 14 • 1NT24CS202 (Prajwal Karadi) & 1NT24CS190 (Padavala Rishi) • B.E Computer Science and Engineering
            </div>
          </div>

          <div className="flex flex-wrap gap-3 text-[11px] text-slate-400">
            <span>Sensors (2025)</span>
            <span>•</span>
            <span>IEEE ICECET (2023)</span>
            <span>•</span>
            <span>Comp. & Elec. in Ag (2022)</span>
            <span>•</span>
            <span className="text-emerald-400 font-mono">SQLite + FastAPI + Mosquitto</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
