import logging
from datetime import datetime
from typing import Dict, Any, List
from backend.app.database import SessionLocal
from backend.app.models import SensorReading, Alert, ActuatorLog, EdgeConfig

logger = logging.getLogger("CloudSync")

class CloudSyncService:
    """
    Cloud Storage & Analytics Synchronization Layer.
    Persists edge-processed agricultural telemetry, alert histories,
    and actuation logs to SQLite database.
    """

    @staticmethod
    def save_reading(reading_data: Dict[str, Any]) -> SensorReading:
        with SessionLocal() as session:
            ts = reading_data.get("timestamp")
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts)
                except Exception:
                    ts = datetime.utcnow()
            elif not ts:
                ts = datetime.utcnow()

            record = SensorReading(
                timestamp=ts,
                zone_id=reading_data.get("zone_id"),
                zone_name=reading_data.get("zone_name"),
                crop_type=reading_data.get("crop_type"),
                soil_moisture=reading_data.get("soil_moisture"),
                temperature=reading_data.get("temperature"),
                humidity=reading_data.get("humidity"),
                water_level=reading_data.get("water_level"),
                solar_radiation=reading_data.get("solar_radiation", 500.0),
                soil_ph=reading_data.get("soil_ph", 6.5),
                battery_level=reading_data.get("battery_level", 98.0),
                network_profile=reading_data.get("network_profile", "5g_urllc"),
                network_latency_ms=reading_data.get("network_latency_ms", 2.5),
                packet_loss_flag=reading_data.get("packet_loss_flag", False),
                simulated_flag=True,
                edge_processed=reading_data.get("edge_processed", True)
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    @staticmethod
    def save_alert(alert_data: Dict[str, Any]) -> Alert:
        with SessionLocal() as session:
            alert = Alert(
                timestamp=datetime.utcnow(),
                zone_id=alert_data.get("zone_id"),
                zone_name=alert_data.get("zone_name"),
                alert_type=alert_data.get("alert_type"),
                severity=alert_data.get("severity", "MEDIUM"),
                message=alert_data.get("message"),
                suggested_action=alert_data.get("suggested_action"),
                acknowledged=False,
                source=alert_data.get("source", "EDGE"),
                response_latency_ms=alert_data.get("response_latency_ms", 2.8),
                simulated_flag=True
            )
            session.add(alert)
            session.commit()
            session.refresh(alert)
            return alert

    @staticmethod
    def log_actuation(actuation_data: Dict[str, Any]) -> ActuatorLog:
        with SessionLocal() as session:
            log = ActuatorLog(
                timestamp=datetime.utcnow(),
                zone_id=actuation_data.get("zone_id"),
                actuator_type=actuation_data.get("actuator_type", "IRRIGATION_VALVE"),
                action=actuation_data.get("action", "START"),
                duration_seconds=actuation_data.get("duration_seconds", 60),
                dosage_liters=actuation_data.get("dosage_liters", 150.0),
                triggered_by=actuation_data.get("triggered_by", "EDGE_AUTONOMOUS"),
                status=actuation_data.get("status", "SUCCESS"),
                details=actuation_data.get("reason", "Automated trigger")
            )
            session.add(log)
            session.commit()
            session.refresh(log)
            return log

    @staticmethod
    def seed_default_edge_configs():
        """Ensures default zone configs exist in SQLite."""
        with SessionLocal() as session:
            existing = session.query(EdgeConfig).all()
            if not existing:
                default_zones = [
                    EdgeConfig(
                        zone_id="zone_1",
                        zone_name="Zone 1 - Wheat Fields (North)",
                        min_moisture=25.0,
                        critical_moisture=18.0,
                        max_moisture=70.0,
                        min_temperature=10.0,
                        max_temperature=37.0,
                        min_humidity=30.0,
                        min_water_level=20.0,
                        irrigation_duration_seconds=120,
                        auto_actuation_enabled=True
                    ),
                    EdgeConfig(
                        zone_id="zone_2",
                        zone_name="Zone 2 - Tomato Greenhouse (East)",
                        min_moisture=30.0,
                        critical_moisture=20.0,
                        max_moisture=75.0,
                        min_temperature=15.0,
                        max_temperature=34.0,
                        min_humidity=45.0,
                        min_water_level=25.0,
                        irrigation_duration_seconds=90,
                        auto_actuation_enabled=True
                    ),
                    EdgeConfig(
                        zone_id="zone_3",
                        zone_name="Zone 3 - Maize & Fodder (South)",
                        min_moisture=22.0,
                        critical_moisture=16.0,
                        max_moisture=65.0,
                        min_temperature=12.0,
                        max_temperature=39.0,
                        min_humidity=25.0,
                        min_water_level=18.0,
                        irrigation_duration_seconds=150,
                        auto_actuation_enabled=True
                    )
                ]
                session.add_all(default_zones)
                session.commit()
                logger.info("Default Edge threshold configs seeded into SQLite.")

cloud_sync = CloudSyncService()
