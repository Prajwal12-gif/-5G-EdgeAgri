"""
Standalone Virtual Sensor Client for 5G-EdgeAgri
Can be executed in a separate terminal to act as an external field IoT device.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import json
import random
import paho.mqtt.client as mqtt

BROKER_HOST = os.getenv("MQTT_HOST", "127.0.0.1")
BROKER_PORT = int(os.getenv("MQTT_PORT", "1883"))

def run_standalone_sensors():
    print(f"[*] Starting Standalone Virtual Sensors...")
    print(f"[*] Target MQTT Broker: {BROKER_HOST}:{BROKER_PORT}")
    
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id="standalone-field-sensors")
    
    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        client.loop_start()
        print("[+] Connected to Mosquitto Broker!")
    except Exception as e:
        print(f"[-] Could not connect to Mosquitto on {BROKER_HOST}:{BROKER_PORT}: {e}")
        print("[!] Note: The backend has an internal event bus, but this standalone script targets external Mosquitto.")

    iteration = 0
    while True:
        iteration += 1
        payload = {
            "sensor_id": "field_node_01",
            "zone_id": "zone_1",
            "soil_moisture": round(random.uniform(22.0, 38.0), 1),
            "temperature": round(random.uniform(23.0, 31.0), 1),
            "humidity": round(random.uniform(45.0, 65.0), 1),
            "water_level": round(random.uniform(70.0, 85.0), 1),
            "simulated": True,
            "timestamp": time.time()
        }
        topic = "agri/farm/zone_1/sensors"
        try:
            client.publish(topic, json.dumps(payload))
            print(f"[{iteration}] Published telemetry to {topic}: Moisture={payload['soil_moisture']}% Temp={payload['temperature']}C")
        except Exception as e:
            print(f"Publish error: {e}")
            
        time.sleep(3)

if __name__ == "__main__":
    run_standalone_sensors()
