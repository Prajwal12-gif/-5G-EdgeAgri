const API_BASE = '/api';

export const api = {
  // Telemetry
  async getLiveTelemetry() {
    const res = await fetch(`${API_BASE}/telemetry/live`);
    return res.json();
  },
  
  async getHistoricalTelemetry(zoneId = null, limit = 100, hours = 24) {
    let url = `${API_BASE}/telemetry/history?limit=${limit}&hours=${hours}`;
    if (zoneId && zoneId !== 'all') {
      url += `&zone_id=${zoneId}`;
    }
    const res = await fetch(url);
    return res.json();
  },

  async injectAnomaly(zoneId, anomalyType) {
    const res = await fetch(`${API_BASE}/telemetry/inject-anomaly`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ zone_id: zoneId, anomaly_type: anomalyType })
    });
    return res.json();
  },

  getExportCsvUrl(zoneId = null) {
    let url = `${API_BASE}/telemetry/export-csv?limit=2000`;
    if (zoneId && zoneId !== 'all') {
      url += `&zone_id=${zoneId}`;
    }
    return url;
  },

  // Alerts
  async getAlerts(zoneId = null, severity = null, unacknowledgedOnly = false) {
    let url = `${API_BASE}/alerts?unacknowledged_only=${unacknowledgedOnly}`;
    if (zoneId && zoneId !== 'all') url += `&zone_id=${zoneId}`;
    if (severity && severity !== 'ALL') url += `&severity=${severity}`;
    const res = await fetch(url);
    return res.json();
  },

  async acknowledgeAlert(alertId) {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/acknowledge`, {
      method: 'PUT'
    });
    return res.json();
  },

  async acknowledgeAllAlerts() {
    const res = await fetch(`${API_BASE}/alerts/acknowledge-all`, {
      method: 'POST'
    });
    return res.json();
  },

  // Edge Engine
  async getEdgeConfigs() {
    const res = await fetch(`${API_BASE}/edge/configs`);
    return res.json();
  },

  async updateEdgeConfig(zoneId, configUpdates) {
    const res = await fetch(`${API_BASE}/edge/configs/${zoneId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(configUpdates)
    });
    return res.json();
  },

  async getEdgeStatus() {
    const res = await fetch(`${API_BASE}/edge/status`);
    return res.json();
  },

  // Actuators
  async getActuatorsStatus() {
    const res = await fetch(`${API_BASE}/actuators/status`);
    return res.json();
  },

  async triggerActuator(zoneId, action = 'START', dosageLiters = 150.0, durationSeconds = 60) {
    const res = await fetch(`${API_BASE}/actuators/trigger`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        zone_id: zoneId,
        actuator_type: 'IRRIGATION_VALVE',
        action,
        duration_seconds: durationSeconds,
        dosage_liters: dosageLiters,
        reason: 'MANUAL_DASHBOARD_ACTUATION'
      })
    });
    return res.json();
  },

  // 5G Network Simulation
  async getNetworkProfiles() {
    const res = await fetch(`${API_BASE}/network/profiles`);
    return res.json();
  },

  async getNetworkStatus() {
    const res = await fetch(`${API_BASE}/network/status`);
    return res.json();
  },

  async setNetworkProfile(profileKey) {
    const res = await fetch(`${API_BASE}/network/set-profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile_key: profileKey })
    });
    return res.json();
  },

  // Controlled Benchmark (Edge vs Cloud)
  async runBenchmark(workloadSize = 50, networkProfile = '5g_urllc') {
    const res = await fetch(`${API_BASE}/benchmark/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workload_size: workloadSize,
        network_profile: networkProfile
      })
    });
    return res.json();
  },

  async getBenchmarkHistory() {
    const res = await fetch(`${API_BASE}/benchmark/history`);
    return res.json();
  }
};
