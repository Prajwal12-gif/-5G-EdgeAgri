import asyncio
import random
import math
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.app.network_sim import network_simulator
from backend.app.mqtt_service import mqtt_service
from backend.app.edge_engine import edge_engine

class VirtualSensorManager:
    """
    Simulates high-fidelity physical micro-climate and soil moisture dynamics
    across multiple agricultural zones without requiring physical Arduino/ESP32 hardware.
    """

    def __init__(self):
        self.zones = {
            "zone_1": {
                "zone_id": "zone_1",
                "zone_name": "Zone 1 - Wheat Fields (North)",
                "crop_type": "Winter Wheat (Triticum aestivum)",
                "soil_moisture": 38.5,
                "temperature": 24.2,
                "humidity": 58.0,
                "water_level": 82.0,
                "solar_radiation": 620.0,
                "soil_ph": 6.8,
                "battery_level": 96.0,
                "anomaly_mode": "NORMAL"
            },
            "zone_2": {
                "zone_id": "zone_2",
                "zone_name": "Zone 2 - Tomato Greenhouse (East)",
                "crop_type": "Hydroponic Cherry Tomatoes",
                "soil_moisture": 52.0,
                "temperature": 27.5,
                "humidity": 68.0,
                "water_level": 78.0,
                "solar_radiation": 480.0,
                "soil_ph": 6.2,
                "battery_level": 99.0,
                "anomaly_mode": "NORMAL"
            },
            "zone_3": {
                "zone_id": "zone_3",
                "zone_name": "Zone 3 - Maize & Fodder (South)",
                "crop_type": "Sweet Corn / Maize",
                "soil_moisture": 32.0,
                "temperature": 29.8,
                "humidity": 48.0,
                "water_level": 65.0,
                "solar_radiation": 740.0,
                "soil_ph": 6.5,
                "battery_level": 94.0,
                "anomaly_mode": "NORMAL"
            }
        }
        self.is_running = False
        self.interval = 2.0  # seconds between sensor reports
        self.update_count = 0
        self.latest_telemetry: Dict[str, Dict[str, Any]] = {}
        self.latest_evaluations: Dict[str, Dict[str, Any]] = {}

    def inject_anomaly(self, zone_id: str, anomaly_type: str) -> Dict[str, Any]:
        """
        Manually inject synthetic anomalies for real-time edge testing.
        Types: DROUGHT_SURGE, FROST_SPIKE, HEATWAVE, TANK_DRAIN, NORMAL
        """
        if zone_id not in self.zones:
            return {"status": "error", "message": f"Zone {zone_id} not found"}

        self.zones[zone_id]["anomaly_mode"] = anomaly_type
        
        # Immediate state transition for rapid responsiveness in demos
        if anomaly_type == "DROUGHT_SURGE":
            self.zones[zone_id]["soil_moisture"] = 16.5  # Below critical 18%
        elif anomaly_type == "FROST_SPIKE":
            self.zones[zone_id]["temperature"] = 3.2
        elif anomaly_type == "HEATWAVE":
            self.zones[zone_id]["temperature"] = 41.5
            self.zones[zone_id]["humidity"] = 22.0
        elif anomaly_type == "TANK_DRAIN":
            self.zones[zone_id]["water_level"] = 8.5
        elif anomaly_type == "NORMAL":
            self.zones[zone_id]["soil_moisture"] = 42.0
            self.zones[zone_id]["temperature"] = 25.0
            self.zones[zone_id]["water_level"] = 85.0

        return {
            "status": "success",
            "zone_id": zone_id,
            "anomaly_mode": anomaly_type,
            "current_state": self.zones[zone_id]
        }

    def trigger_water_replenishment(self, zone_id: str, liters: float = 200.0):
        """Simulates water absorbed by soil when actuator runs."""
        if zone_id in self.zones:
            z = self.zones[zone_id]
            # Moisture boost proportional to dosage
            moisture_gain = min(35.0, (liters / 10.0))
            z["soil_moisture"] = min(88.0, z["soil_moisture"] + moisture_gain)
            # Water level drops from tank
            tank_drop = (liters / 20.0)
            z["water_level"] = max(2.0, z["water_level"] - tank_drop)

    def generate_step(self) -> List[Dict[str, Any]]:
        """
        Simulates 1 tick of environmental sensor telemetry with realistic thermodynamics.
        """
        self.update_count += 1
        t = time.time()
        # Diurnal solar cycle simulation (sinusoidal temperature/solar curve)
        cycle_factor = math.sin(t / 60.0)
        generated_readings = []

        for zone_id, z in self.zones.items():
            mode = z.get("anomaly_mode", "NORMAL")

            if mode == "NORMAL":
                # Natural slight evaporation / moisture depletion
                moisture_decay = random.uniform(0.08, 0.25)
                z["soil_moisture"] = max(12.0, z["soil_moisture"] - moisture_decay)
                
                # Ambient temperature natural drift
                z["temperature"] = round(25.0 + (cycle_factor * 6.0) + random.uniform(-0.4, 0.4), 1)
                z["humidity"] = round(max(20.0, min(95.0, 60.0 - (cycle_factor * 12.0) + random.uniform(-1.0, 1.0))), 1)
                z["solar_radiation"] = round(max(50.0, 550.0 + (cycle_factor * 300.0) + random.uniform(-25.0, 25.0)), 1)
                # Slow battery discharge simulation
                z["battery_level"] = round(max(15.0, z["battery_level"] - 0.001), 1)
                # Minor water evaporation
                z["water_level"] = round(max(5.0, z["water_level"] - 0.02), 1)

            elif mode == "DROUGHT_SURGE":
                # Drops rapidly to trigger Slide 9 scenario (18% and below)
                z["soil_moisture"] = round(max(10.0, z["soil_moisture"] - random.uniform(0.5, 1.2)), 1)
                z["temperature"] = round(min(45.0, z["temperature"] + random.uniform(0.2, 0.6)), 1)

            elif mode == "FROST_SPIKE":
                z["temperature"] = round(max(-5.0, z["temperature"] - random.uniform(0.4, 1.0)), 1)
                z["humidity"] = round(min(98.0, z["humidity"] + 0.5), 1)

            elif mode == "HEATWAVE":
                z["temperature"] = round(min(48.0, z["temperature"] + random.uniform(0.3, 0.8)), 1)
                z["soil_moisture"] = round(max(8.0, z["soil_moisture"] - 0.6), 1)

            elif mode == "TANK_DRAIN":
                z["water_level"] = round(max(1.0, z["water_level"] - random.uniform(1.5, 3.5)), 1)

            # Route through 5G network simulator to compute transmission metrics
            payload_sample_bytes = 180  # JSON telemetry packet size
            net_stats = network_simulator.transmit(payload_sample_bytes)

            reading = {
                "zone_id": z["zone_id"],
                "zone_name": z["zone_name"],
                "crop_type": z["crop_type"],
                "soil_moisture": round(z["soil_moisture"], 1),
                "temperature": round(z["temperature"], 1),
                "humidity": round(z["humidity"], 1),
                "water_level": round(z["water_level"], 1),
                "solar_radiation": round(z["solar_radiation"], 1),
                "soil_ph": round(z["soil_ph"], 2),
                "battery_level": round(z["battery_level"], 1),
                "network_profile": net_stats["profile_key"],
                "network_latency_ms": net_stats["latency_ms"],
                "packet_loss_flag": net_stats["packet_lost"],
                "simulated_flag": True,  # Explicitly distinguished from physical
                "edge_processed": True,
                "timestamp": datetime.utcnow().isoformat()
            }

            self.latest_telemetry[zone_id] = reading
            generated_readings.append(reading)

            # Publish immediately over MQTT
            mqtt_topic = f"agri/farm/{zone_id}/sensors"
            mqtt_service.publish(mqtt_topic, reading)

        return generated_readings

virtual_sensors = VirtualSensorManager()
