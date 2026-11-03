import time
from typing import Any, Dict, List, Optional


class EdgeProcessingEngine:
    """Evaluates simulated sensor readings and emits alerts on condition transitions."""

    def __init__(self):
        self.zone_configs: Dict[str, Dict[str, Any]] = {
            "zone_1": {
                "zone_name": "Zone 1 - Wheat Fields (North)", "min_moisture": 25.0,
                "critical_moisture": 18.0, "max_moisture": 70.0, "min_temperature": 10.0,
                "max_temperature": 37.0, "min_humidity": 30.0, "min_water_level": 20.0,
                "irrigation_duration_seconds": 120, "auto_actuation_enabled": True,
            },
            "zone_2": {
                "zone_name": "Zone 2 - Tomato Greenhouse (East)", "min_moisture": 30.0,
                "critical_moisture": 20.0, "max_moisture": 75.0, "min_temperature": 15.0,
                "max_temperature": 34.0, "min_humidity": 45.0, "min_water_level": 25.0,
                "irrigation_duration_seconds": 90, "auto_actuation_enabled": True,
            },
            "zone_3": {
                "zone_name": "Zone 3 - Maize & Fodder (South)", "min_moisture": 22.0,
                "critical_moisture": 16.0, "max_moisture": 65.0, "min_temperature": 12.0,
                "max_temperature": 39.0, "min_humidity": 25.0, "min_water_level": 18.0,
                "irrigation_duration_seconds": 150, "auto_actuation_enabled": True,
            },
        }
        self.previous_readings: Dict[str, Dict[str, Any]] = {}
        self.active_actuators: Dict[str, Dict[str, Any]] = {}
        # Alert types currently active per zone. An alert is saved only when a
        # condition first becomes active, not on every 2-second telemetry tick.
        self.active_conditions: Dict[str, set] = {}

    def get_config(self, zone_id: str) -> Dict[str, Any]:
        if zone_id in self.zone_configs:
            return self.zone_configs[zone_id]
        return {
            "zone_name": f"Zone {zone_id.replace('zone_', '')}", "min_moisture": 25.0,
            "critical_moisture": 18.0, "max_moisture": 70.0, "min_temperature": 12.0,
            "max_temperature": 38.0, "min_humidity": 30.0, "min_water_level": 20.0,
            "irrigation_duration_seconds": 120, "auto_actuation_enabled": True,
        }

    def update_config(self, zone_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_config(zone_id).copy()
        current.update({k: v for k, v in updates.items() if v is not None})
        self.zone_configs[zone_id] = current
        return current

    def reset_zone_state(self, zone_id: str):
        """Clear transient edge state after a zone is explicitly reset."""
        self.previous_readings.pop(zone_id, None)
        self.active_conditions.pop(zone_id, None)
        self.active_actuators.pop(zone_id, None)

    def _new_alert(self, zone_id, zone_name, alert_type, severity, message, action):
        return {
            "zone_id": zone_id, "zone_name": zone_name, "alert_type": alert_type,
            "severity": severity, "message": message, "suggested_action": action,
            "source": "EDGE",
        }

    def evaluate_reading(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        start = time.perf_counter()
        zone_id = reading.get("zone_id", "zone_1")
        cfg = self.get_config(zone_id)
        moisture = float(reading.get("soil_moisture", 50.0))
        temp = float(reading.get("temperature", 25.0))
        water = float(reading.get("water_level", 75.0))
        zone_name = reading.get("zone_name", cfg["zone_name"])
        conditions = {}
        actuation_trigger: Optional[Dict[str, Any]] = None

        prev = self.previous_readings.get(zone_id)
        if prev:
            delta = float(prev.get("soil_moisture", moisture)) - moisture
            if delta > 7.0:
                conditions["ANOMALY_MOISTURE_PLUNGE"] = self._new_alert(
                    zone_id, zone_name, "ANOMALY_MOISTURE_PLUNGE", "HIGH",
                    f"Rapid moisture drop detected (-{delta:.1f}%). Possible leak or soil dryout.",
                    "Inspect irrigation drip lines and subsoil sensor seating.",
                )

        if water < 10.0:
            conditions["WATER_TANK_CRITICAL"] = self._new_alert(
                zone_id, zone_name, "WATER_TANK_CRITICAL", "CRITICAL",
                f"Reservoir water level critically low at {water:.1f}%. Automatic irrigation restricted.",
                "Refill water reservoir immediately or switch to secondary canal supply.",
            )
        elif water < cfg["min_water_level"]:
            conditions["WATER_TANK_LOW"] = self._new_alert(
                zone_id, zone_name, "WATER_TANK_LOW", "MEDIUM",
                f"Reservoir water level is low ({water:.1f}% < {cfg['min_water_level']}%).",
                "Schedule well pump cycle.",
            )

        if moisture <= cfg["critical_moisture"]:
            conditions["CRITICAL_SOIL_DROUGHT"] = self._new_alert(
                zone_id, zone_name, "CRITICAL_SOIL_DROUGHT", "CRITICAL",
                f"Critical drought in {zone_name}! Soil moisture is {moisture:.1f}% (<= {cfg['critical_moisture']}%).",
                "IRRIGATION REQUIRED: Solenoid valve activated immediately.",
            )
            if cfg["auto_actuation_enabled"] and water > 10.0:
                current_actuator = self.active_actuators.get(zone_id, {})
                if current_actuator.get("status") != "RUNNING":
                    actuation_trigger = {
                        "zone_id": zone_id, "actuator_type": "IRRIGATION_VALVE", "action": "START",
                        "duration_seconds": cfg["irrigation_duration_seconds"],
                        "dosage_liters": round(cfg["irrigation_duration_seconds"] * 2.5, 1),
                        "triggered_by": "EDGE_RULE_CRITICAL_DROUGHT",
                        "reason": f"Automatic emergency watering triggered: Soil moisture={moisture:.1f}%",
                    }
        elif moisture < cfg["min_moisture"]:
            conditions["LOW_SOIL_MOISTURE"] = self._new_alert(
                zone_id, zone_name, "LOW_SOIL_MOISTURE", "HIGH",
                f"Low soil moisture detected ({moisture:.1f}% < {cfg['min_moisture']}%).",
                "Trigger scheduled irrigation cycle.",
            )
            current_actuator = self.active_actuators.get(zone_id, {})
            if cfg["auto_actuation_enabled"] and water > 15.0 and current_actuator.get("status") != "RUNNING":
                actuation_trigger = {
                    "zone_id": zone_id, "actuator_type": "IRRIGATION_VALVE", "action": "START",
                    "duration_seconds": int(cfg["irrigation_duration_seconds"] * 0.75),
                    "dosage_liters": round(cfg["irrigation_duration_seconds"] * 1.8, 1),
                    "triggered_by": "EDGE_RULE_LOW_MOISTURE",
                    "reason": f"Automated irrigation cycle: Soil moisture={moisture:.1f}%",
                }

        if temp >= cfg["max_temperature"]:
            conditions["HEAT_STRESS_ALERT"] = self._new_alert(
                zone_id, zone_name, "HEAT_STRESS_ALERT", "HIGH",
                f"High temperature stress: {temp:.1f}°C (Threshold: {cfg['max_temperature']}°C).",
                "Deploy shade nets or trigger mist-sprinkler canopy cooling.",
            )
        elif temp <= cfg["min_temperature"]:
            conditions["FROST_WARNING"] = self._new_alert(
                zone_id, zone_name, "FROST_WARNING", "MEDIUM",
                f"Low temperature warning: {temp:.1f}°C (Frost danger below {cfg['min_temperature']}°C).",
                "Verify greenhouse thermal curtains.",
            )

        previous_active = self.active_conditions.get(zone_id, set())
        alerts = [alert for key, alert in conditions.items() if key not in previous_active]
        self.active_conditions[zone_id] = set(conditions.keys())
        self.previous_readings[zone_id] = dict(reading)

        actuator = self.active_actuators.get(zone_id)
        if actuator and actuator.get("status") == "RUNNING":
            elapsed = time.time() - actuator.get("start_time", time.time())
            duration = actuator.get("duration_seconds", 60)
            # Stop the virtual valve when moisture recovers or its timer expires.
            if moisture >= cfg["min_moisture"] or elapsed >= duration:
                actuator["status"] = "STOPPED"
                actuator["stopped_at"] = time.time()

        if actuation_trigger:
            self.active_actuators[zone_id] = {
                **actuation_trigger, "start_time": time.time(), "status": "RUNNING"
            }

        elapsed_ms = round((time.perf_counter() - start) * 1000.0, 3)
        return {
            "zone_id": zone_id, "processing_time_ms": elapsed_ms,
            "alerts": alerts, "actuation_trigger": actuation_trigger,
            "active_actuator_state": self.active_actuators.get(zone_id),
        }


edge_engine = EdgeProcessingEngine()
