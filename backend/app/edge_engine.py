import time
from typing import Dict, Any, List, Optional, Tuple
from backend.app.schemas import SensorReadingCreate, AlertCreate, ActuatorTriggerRequest

class EdgeProcessingEngine:
    """
    Sub-millisecond Edge Rule Engine for Smart Agriculture.
    Executes locally at the 5G Edge / MEC node to evaluate soil, water,
    and environmental parameters, detecting anomalies and issuing priority alerts.
    """

    def __init__(self):
        # In-memory cached configs for instantaneous edge rule matching
        self.zone_configs: Dict[str, Dict[str, Any]] = {
            "zone_1": {
                "zone_name": "Zone 1 - Wheat Fields (North)",
                "min_moisture": 25.0,
                "critical_moisture": 18.0,
                "max_moisture": 70.0,
                "min_temperature": 10.0,
                "max_temperature": 37.0,
                "min_humidity": 30.0,
                "min_water_level": 20.0,
                "irrigation_duration_seconds": 120,
                "auto_actuation_enabled": True
            },
            "zone_2": {
                "zone_name": "Zone 2 - Tomato Greenhouse (East)",
                "min_moisture": 30.0,
                "critical_moisture": 20.0,
                "max_moisture": 75.0,
                "min_temperature": 15.0,
                "max_temperature": 34.0,
                "min_humidity": 45.0,
                "min_water_level": 25.0,
                "irrigation_duration_seconds": 90,
                "auto_actuation_enabled": True
            },
            "zone_3": {
                "zone_name": "Zone 3 - Maize & Fodder (South)",
                "min_moisture": 22.0,
                "critical_moisture": 16.0,
                "max_moisture": 65.0,
                "min_temperature": 12.0,
                "max_temperature": 39.0,
                "min_humidity": 25.0,
                "min_water_level": 18.0,
                "irrigation_duration_seconds": 150,
                "auto_actuation_enabled": True
            }
        }
        # Last known readings for delta/anomaly detection
        self.previous_readings: Dict[str, Dict[str, Any]] = {}
        # Active actuation state per zone
        self.active_actuators: Dict[str, Dict[str, Any]] = {}

    def get_config(self, zone_id: str) -> Dict[str, Any]:
        return self.zone_configs.get(zone_id, {
            "zone_name": f"Zone {zone_id.replace('zone_', '')}",
            "min_moisture": 25.0,
            "critical_moisture": 18.0,
            "max_moisture": 70.0,
            "min_temperature": 12.0,
            "max_temperature": 38.0,
            "min_humidity": 30.0,
            "min_water_level": 20.0,
            "irrigation_duration_seconds": 120,
            "auto_actuation_enabled": True
        })

    def update_config(self, zone_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_config(zone_id)
        current.update({k: v for k, v in updates.items() if v is not None})
        self.zone_configs[zone_id] = current
        return current

    def evaluate_reading(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes edge rules, returns generated alerts, actuation triggers,
        and precise processing time.
        """
        start_time = time.perf_counter()
        
        zone_id = reading.get("zone_id", "zone_1")
        cfg = self.get_config(zone_id)
        
        alerts: List[Dict[str, Any]] = []
        actuation_trigger: Optional[Dict[str, Any]] = None
        
        moisture = reading.get("soil_moisture", 50.0)
        temp = reading.get("temperature", 25.0)
        humidity = reading.get("humidity", 60.0)
        water_level = reading.get("water_level", 75.0)
        zone_name = reading.get("zone_name", cfg.get("zone_name", zone_id))

        # Check rapid moisture drop anomaly if previous reading exists
        prev = self.previous_readings.get(zone_id)
        if prev:
            moisture_delta = prev.get("soil_moisture", moisture) - moisture
            if moisture_delta > 7.0:
                alerts.append({
                    "zone_id": zone_id,
                    "zone_name": zone_name,
                    "alert_type": "ANOMALY_MOISTURE_PLUNGE",
                    "severity": "HIGH",
                    "message": f"Rapid moisture drop detected (-{moisture_delta:.1f}%). Possible leak or soil dryout.",
                    "suggested_action": "Inspect irrigation drip lines and subsoil sensor seating.",
                    "source": "EDGE"
                })

        self.previous_readings[zone_id] = reading

        # Rule 1: Water Reservoir Level
        if water_level < 10.0:
            alerts.append({
                "zone_id": zone_id,
                "zone_name": zone_name,
                "alert_type": "WATER_TANK_CRITICAL",
                "severity": "CRITICAL",
                "message": f"Reservoir water level critically low at {water_level:.1f}%. Automatic irrigation restricted.",
                "suggested_action": "Refill water reservoir immediately or switch to secondary canal supply.",
                "source": "EDGE"
            })
        elif water_level < cfg["min_water_level"]:
            alerts.append({
                "zone_id": zone_id,
                "zone_name": zone_name,
                "alert_type": "WATER_TANK_LOW",
                "severity": "MEDIUM",
                "message": f"Reservoir water level is low ({water_level:.1f}% < {cfg['min_water_level']}%).",
                "suggested_action": "Schedule well pump cycle.",
                "source": "EDGE"
            })

        # Rule 2: Soil Moisture & Irrigation Actuation (Slide 9 scenario: Soil moisture <= 18% -> "IRRIGATION REQUIRED")
        if moisture <= cfg["critical_moisture"]:
            alerts.append({
                "zone_id": zone_id,
                "zone_name": zone_name,
                "alert_type": "CRITICAL_SOIL_DROUGHT",
                "severity": "CRITICAL",
                "message": f"Critical drought in {zone_name}! Soil moisture is {moisture:.1f}% (<= {cfg['critical_moisture']}%).",
                "suggested_action": "IRRIGATION REQUIRED: Solenoid valve activated immediately.",
                "source": "EDGE"
            })
            if cfg["auto_actuation_enabled"] and water_level > 10.0:
                actuation_trigger = {
                    "zone_id": zone_id,
                    "actuator_type": "IRRIGATION_VALVE",
                    "action": "START",
                    "duration_seconds": cfg["irrigation_duration_seconds"],
                    "dosage_liters": round(cfg["irrigation_duration_seconds"] * 2.5, 1),
                    "triggered_by": "EDGE_RULE_CRITICAL_DROUGHT",
                    "reason": f"Automatic emergency watering triggered: Soil moisture={moisture:.1f}%"
                }
        elif moisture < cfg["min_moisture"]:
            alerts.append({
                "zone_id": zone_id,
                "zone_name": zone_name,
                "alert_type": "LOW_SOIL_MOISTURE",
                "severity": "HIGH",
                "message": f"Low soil moisture detected ({moisture:.1f}% < {cfg['min_moisture']}%).",
                "suggested_action": "Trigger scheduled irrigation cycle.",
                "source": "EDGE"
            })
            if cfg["auto_actuation_enabled"] and water_level > 15.0 and not actuation_trigger:
                actuation_trigger = {
                    "zone_id": zone_id,
                    "actuator_type": "IRRIGATION_VALVE",
                    "action": "START",
                    "duration_seconds": int(cfg["irrigation_duration_seconds"] * 0.75),
                    "dosage_liters": round(cfg["irrigation_duration_seconds"] * 1.8, 1),
                    "triggered_by": "EDGE_RULE_LOW_MOISTURE",
                    "reason": f"Automated irrigation cycle: Soil moisture={moisture:.1f}%"
                }

        # Rule 3: Temperature Extremes
        if temp >= cfg["max_temperature"]:
            alerts.append({
                "zone_id": zone_id,
                "zone_name": zone_name,
                "alert_type": "HEAT_STRESS_ALERT",
                "severity": "HIGH",
                "message": f"High temperature stress: {temp:.1f}°C (Threshold: {cfg['max_temperature']}°C).",
                "suggested_action": "Deploy shade nets or trigger mist-sprinkler canopy cooling.",
                "source": "EDGE"
            })
        elif temp <= cfg["min_temperature"]:
            alerts.append({
                "zone_id": zone_id,
                "zone_name": zone_name,
                "alert_type": "FROST_WARNING",
                "severity": "MEDIUM",
                "message": f"Low temperature warning: {temp:.1f}°C (Frost danger below {cfg['min_temperature']}°C).",
                "suggested_action": "Verify greenhouse thermal curtains.",
                "source": "EDGE"
            })

        # Calculate processing time in milliseconds
        end_time = time.perf_counter()
        processing_time_ms = round((end_time - start_time) * 1000.0, 3)

        # Update actuator state if triggered
        if actuation_trigger:
            self.active_actuators[zone_id] = {
                **actuation_trigger,
                "start_time": time.time(),
                "status": "RUNNING"
            }

        return {
            "zone_id": zone_id,
            "processing_time_ms": processing_time_ms,
            "alerts": alerts,
            "actuation_trigger": actuation_trigger,
            "active_actuator_state": self.active_actuators.get(zone_id)
        }

edge_engine = EdgeProcessingEngine()
