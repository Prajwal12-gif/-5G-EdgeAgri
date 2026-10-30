class TelemetryWebSocket {
  constructor() {
    this.ws = null;
    this.listeners = new Set();
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectDelay = 5000;
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use host with port 8000 if not proxying, or window.location.host
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/telemetry`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this._notifyListeners({ event: 'CONNECTION_STATUS', connected: true });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this._notifyListeners(data);
        } catch (e) {
          console.error("WS Parse error:", e);
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this._notifyListeners({ event: 'CONNECTION_STATUS', connected: false });
        this._scheduleReconnect();
      };

      this.ws.onerror = (err) => {
        console.warn("WS error, will retry:", err);
        if (this.ws) this.ws.close();
      };
    } catch (e) {
      console.warn("WebSocket initialization error:", e);
      this._scheduleReconnect();
    }
  }

  _scheduleReconnect() {
    const delay = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), this.maxReconnectDelay);
    this.reconnectAttempts++;
    setTimeout(() => this.connect(), delay);
  }

  subscribe(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  _notifyListeners(data) {
    this.listeners.forEach((callback) => {
      try {
        callback(data);
      } catch (e) {
        console.error("Listener error:", e);
      }
    });
  }
}

export const telemetryWs = new TelemetryWebSocket();
