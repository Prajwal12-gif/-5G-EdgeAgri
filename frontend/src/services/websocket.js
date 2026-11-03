
const BACKEND_URL = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');

class TelemetryWebSocket {
  constructor() {
    this.ws = null;
    this.listeners = new Set();
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectDelay = 5000;
    this.reconnectTimer = null;
  }

  connect() {
    // Prevent duplicate connections
    if (
      this.ws &&
      (this.ws.readyState === WebSocket.CONNECTING ||
        this.ws.readyState === WebSocket.OPEN)
    ) {
      return;
    }

    // Connect to Render in production or use Vite proxy locally
    let wsUrl;

    if (BACKEND_URL) {
      const wsBase = BACKEND_URL.replace(/^https:/, 'wss:')
        .replace(/^http:/, 'ws:');

      wsUrl = `${wsBase}/ws/telemetry`;
    } else {
      const protocol =
        window.location.protocol === 'https:' ? 'wss:' : 'ws:';

      wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;
    }

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;

        this._notifyListeners({
          event: 'CONNECTION_STATUS',
          connected: true
        });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this._notifyListeners(data);
        } catch (e) {
          console.error('WS Parse error:', e);
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this.ws = null;

        this._notifyListeners({
          event: 'CONNECTION_STATUS',
          connected: false
        });

        this._scheduleReconnect();
      };

      this.ws.onerror = (err) => {
        console.warn('WebSocket error, will retry:', err);

        if (this.ws) {
          this.ws.close();
        }
      };

    } catch (e) {
      console.warn('WebSocket initialization error:', e);
      this._scheduleReconnect();
    }
  }

  _scheduleReconnect() {
    if (this.reconnectTimer) return;

    const delay = Math.min(
      1000 * Math.pow(1.5, this.reconnectAttempts),
      this.maxReconnectDelay
    );

    this.reconnectAttempts++;

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
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
        console.error('Listener error:', e);
      }
    });
  }
}

export const telemetryWs = new TelemetryWebSocket();
