import json
import logging
import asyncio
from typing import Callable, Dict, List, Any
import paho.mqtt.client as mqtt
from backend.app.config import settings

logger = logging.getLogger("MQTTService")

class MQTTService:
    def __init__(self):
        self.host = settings.MQTT_BROKER_HOST
        self.port = settings.MQTT_BROKER_PORT
        self.client_id = settings.MQTT_CLIENT_ID
        self.connected_to_broker = False
        self.client = None
        self.callbacks: Dict[str, List[Callable[[str, Dict[str, Any]], None]]] = {}
        self.internal_queue = asyncio.Queue()
        self.broker_mode = "INITIALIZING"

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.connected_to_broker = True
            self.broker_mode = "MOSQUITTO_BROKER_CONNECTED"
            logger.info(f"Successfully connected to Mosquitto broker at {self.host}:{self.port}")
            # Subscribe to farm telemetry and commands
            client.subscribe("agri/#")
        else:
            self.connected_to_broker = False
            self.broker_mode = f"BROKER_CONNECTION_FAILED_RC_{rc}"
            logger.warning(f"Mosquitto connection refused with result code {rc}")

    def _on_disconnect(self, client, userdata, disconnect_flags_or_rc, properties=None):
        self.connected_to_broker = False
        self.broker_mode = "INTERNAL_SIMULATED_BUS_ACTIVE"
        logger.warning("Disconnected from Mosquitto broker. Active fallback: Internal Event Bus.")

    def _on_message(self, client, userdata, msg):
        try:
            payload_str = msg.payload.decode("utf-8")
            data = json.loads(payload_str)
            self._dispatch(msg.topic, data)
        except Exception as e:
            logger.error(f"Error handling MQTT message on {msg.topic}: {e}")

    def _dispatch(self, topic: str, data: Dict[str, Any]):
        for pattern, callback_list in self.callbacks.items():
            # Basic wildcard matching ('agri/#' or exact match)
            if pattern == "agri/#" or pattern == topic or (pattern.endswith("+") and topic.startswith(pattern[:-1])):
                for cb in callback_list:
                    try:
                        if asyncio.iscoroutinefunction(cb):
                            asyncio.create_task(cb(topic, data))
                        else:
                            cb(topic, data)
                    except Exception as e:
                        logger.error(f"Callback dispatch error on topic {topic}: {e}")

    def register_callback(self, topic: str, callback: Callable[[str, Dict[str, Any]], None]):
        if topic not in self.callbacks:
            self.callbacks[topic] = []
        self.callbacks[topic].append(callback)

    def start(self):
        import socket
        try:
            # Check if Mosquitto broker is reachable first
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.3)
                result = s.connect_ex((self.host, self.port))
            
            if result == 0:
                self.client = mqtt.Client(
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                    client_id=self.client_id
                )
                self.client.on_connect = self._on_connect
                self.client.on_disconnect = self._on_disconnect
                self.client.on_message = self._on_message
                
                logger.info(f"Mosquitto broker detected at {self.host}:{self.port}. Connecting...")
                self.client.connect(self.host, self.port, keepalive=60)
                self.client.loop_start()
            else:
                self.connected_to_broker = False
                self.broker_mode = "INTERNAL_SIMULATED_BUS_ACTIVE (Mosquitto port 1883 not listening)"
                logger.info(f"Mosquitto broker not listening at {self.host}:{self.port}. Active fallback: Internal High-Speed Event Bus.")
        except Exception as e:
            self.connected_to_broker = False
            self.broker_mode = "INTERNAL_SIMULATED_BUS_ACTIVE"
            logger.info(f"Mosquitto broker check skipped: {e}. Active fallback: Internal High-Speed Event Bus.")

    def stop(self):
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass

    def publish(self, topic: str, payload: Dict[str, Any]):
        """
        Publishes message to Mosquitto (if connected) and always dispatches to internal listeners
        to ensure zero data loss during simulation experiments.
        """
        payload_json = json.dumps(payload)
        
        # Publish via Mosquitto if available
        if self.client and self.connected_to_broker:
            try:
                self.client.publish(topic, payload_json, qos=1)
            except Exception as e:
                logger.error(f"Failed to publish via Mosquitto: {e}")

        # Always dispatch to registered internal async consumers
        self._dispatch(topic, payload)

mqtt_service = MQTTService()
