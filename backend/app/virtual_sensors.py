import math
import random
import time
from datetime import datetime
from typing import Any, Dict, List

from backend.app.network_sim import network_simulator
from backend.app.mqtt_service import mqtt_service
from backend.app.edge_engine import edge_engine


class VirtualSensorManager:
    """Generates simulated telemetry for the three agricultural zones."""

    ZONE_DEFAULTS = {
        "zone_1": {
            "zone_id": "zone_1",
            "zone_name": "Zone 1 - Wheat Fields (North)",
            "crop_type": "Winter Wheat (Triticum aestivum)",
            "soil_moisture": 38.5, "temperature": 24.2, "humidity": 58.0,
            "water_level": 82.0, "solar_radiation": 620.0,
            "soil_ph": 6.8, "battery_level": 96.0,
        },
        "zone_2": {
            "zone_id": "zone_2",
            "zone_name": "Zone 2 - Tomato Greenhouse (East)",
            "crop_type": "Hydroponic Cherry Tomatoes",
            "soil_moisture": 52.0, "temperature": 27.5, "humidity": 68.0,
            "water_level": 78.0, "solar_radiation": 480.0,
            "soil_ph": 6.2, "battery_level": 99.0,
        },
        "zone_3": {
            "zone_id": "zone_3",
            "zone_name": "Zone 3 - Maize & Fodder (South)",
            "crop_type": "Sweet Corn / Maize",
            "soil_moisture": 32.0, "temperature": 29.8, "humidity": 48.0,
            "water_level": 65.0, "solar_radiation": 740.0,
            "soil_ph": 6.5, "battery_level": 94.0,
        },
    }
    VALID_MODES = {"DROUGHT_SURGE", "FROST_SPIKE", "HEATWAVE", "TANK_DRAIN", "NORMAL"}

    def __init__(self):
        self.zones: Dict[str, Dict[str, Any]] = {}
        self._restore_zone_defaults()
        self.is_running = False
        self.interval = 2.0
        self.update_count = 0
        self.latest_telemetry: Dict[str, Dict[str, Any]] = {}
        self.latest_evaluations: Dict[str, Dict[str, Any]] = {}

    def _restore_zone_defaults(self, zone_id: str = None):
        targets = [zone_id] if zone_id else list(self.ZONE_DEFAULTS)
        for zid in targets:
            defaults = self.ZONE_DEFAULTS[zid].copy()
            defaults["anomaly_mode"] = "NORMAL"
            self.zones[zid] = defaults

    def inject_anomaly(self, zone_id: str, anomaly_type: str) -> Dict[str, Any]:
        """Inject a supported synthetic condition, or restore one/all zones."""
        mode = (anomaly_type or "").strip().upper()
        if mode not in self.VALID_MODES:
            return {"status": "error", "message": f"Unsupported anomaly type: {mode}"}

        targets = list(self.zones) if zone_id == "all" else [zone_id]
        unknown = [zid for zid in targets if zid not in self.zones]
        if unknown:
            return {"status": "error", "message": f"Zone {unknown[0]} not found"}

        states = {}
        for zid in targets:
            if mode == "NORMAL":
                # Restore every environmental field, not just moisture/temp/tank.
                self._restore_zone_defaults(zid)
                edge_engine.reset_zone_state(zid)
            else:
                z = self.zones[zid]
                z["anomaly_mode"] = mode
                if mode == "DROUGHT_SURGE":
                    z["soil_moisture"] = 16.5
                elif mode == "FROST_SPIKE":
                    z["temperature"] = 3.2
                elif mode == "HEATWAVE":
                    z["temperature"] = 41.5
                    z["humidity"] = 22.0
                elif mode == "TANK_DRAIN":
                    z["water_level"] = 8.5
            states[zid] = self.zones[zid].copy()

        return {
            "status": "success",
            "zone_id": zone_id,
            "zones_affected": targets,
            "anomaly_mode": mode,
            "message": "All zones restored to baseline." if mode == "NORMAL" else f"{mode} injected.",
            "current_state": states if zone_id == "all" else states[zone_id],
        }

    def trigger_water_replenishment(self, zone_id: str, liters: float = 200.0):
        """Apply a bounded simulated irrigation event to one zone."""
        if zone_id not in self.zones:
            return
        liters = max(0.0, min(float(liters), 500.0))
        z = self.zones[zone_id]
        z["soil_moisture"] = min(88.0, z["soil_moisture"] + min(35.0, liters / 10.0))
        z["water_level"] = max(0.0, z["water_level"] - (liters / 20.0))

    def generate_step(self) -> List[Dict[str, Any]]:
        self.update_count += 1
        cycle_factor = math.sin(time.time() / 60.0)
        generated_readings = []

        for zone_id, z in self.zones.items():
            mode = z.get("anomaly_mode", "NORMAL")

            if mode == "NORMAL":
                z["soil_moisture"] = max(12.0, z["soil_moisture"] - random.uniform(0.02, 0.08))
                z["temperature"] = round(25.0 + cycle_factor * 4.0 + random.uniform(-0.4, 0.4), 1)
                z["humidity"] = round(max(35.0, min(85.0, 60.0 - cycle_factor * 8.0 + random.uniform(-1, 1))), 1)
                z["solar_radiation"] = round(max(50.0, 550.0 + cycle_factor * 250.0 + random.uniform(-25, 25)), 1)
                z["battery_level"] = round(max(15.0, z["battery_level"] - 0.001), 1)
                z["water_level"] = round(max(5.0, z["water_level"] - 0.005), 1)
            elif mode == "DROUGHT_SURGE":
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

            net_stats = network_simulator.transmit(180)
            reading = {
                "zone_id": z["zone_id"], "zone_name": z["zone_name"], "crop_type": z["crop_type"],
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
                "simulated_flag": True, "edge_processed": True,
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.latest_telemetry[zone_id] = reading
            generated_readings.append(reading)
            mqtt_service.publish(f"agri/farm/{zone_id}/sensors", reading)

        return generated_readings


virtual_sensors = VirtualSensorManager()
