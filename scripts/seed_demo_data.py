import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import random
from datetime import datetime, timedelta, timezone
from backend.app.database import init_db, SessionLocal
from backend.app.models import SensorReading, Alert, ActuatorLog, EdgeConfig, BenchmarkResult
from backend.app.cloud_sync import cloud_sync

def seed_database():
    print("Initializing Database schema...")
    init_db()
    cloud_sync.seed_default_edge_configs()
    
    session = SessionLocal()
    try:
        # Check if already seeded
        count = session.query(SensorReading).count()
        if count >= 50:
            print(f"Database already populated with {count} sensor readings.")
            return

        print("Seeding realistic historical agricultural telemetry for the past 24 hours...")
        now = datetime.now(timezone.utc)
        zones = [
            ("zone_1", "Zone 1 - Wheat Fields (North)", "Winter Wheat (Triticum aestivum)", 36.0, 24.0, 58.0, 85.0),
            ("zone_2", "Zone 2 - Tomato Greenhouse (East)", "Hydroponic Cherry Tomatoes", 54.0, 26.5, 66.0, 80.0),
            ("zone_3", "Zone 3 - Maize & Fodder (South)", "Sweet Corn / Maize", 33.0, 28.0, 50.0, 72.0)
        ]

        readings = []
        alerts = []
        actuations = []

        # Generate 144 points (every 10 minutes over last 24h)
        for step in range(144, 0, -1):
            ts = now - timedelta(minutes=step * 10)
            hour_of_day = ts.hour
            # Diurnal temperature fluctuation
            temp_offset = 6.0 * (1 - abs(hour_of_day - 14) / 10.0)

            for z_id, z_name, crop, base_moist, base_temp, base_hum, base_water in zones:
                # Add slight noise and gradual soil drying
                drying = ((144 - step) % 36) * 0.4
                moist = max(16.5, base_moist - drying + random.uniform(-1.0, 1.0))
                temp = round(base_temp + temp_offset + random.uniform(-0.5, 0.5), 1)
                hum = round(max(25.0, min(95.0, base_hum - (temp_offset * 1.5) + random.uniform(-2.0, 2.0))), 1)
                water = round(max(20.0, base_water - ((144 - step) * 0.1)), 1)
                latency = round(random.uniform(1.8, 3.4), 2)

                readings.append(SensorReading(
                    timestamp=ts,
                    zone_id=z_id,
                    zone_name=z_name,
                    crop_type=crop,
                    soil_moisture=round(moist, 1),
                    temperature=temp,
                    humidity=hum,
                    water_level=water,
                    solar_radiation=round(max(0.0, 650.0 * (1 - abs(hour_of_day - 13) / 7.0)), 1) if 6 <= hour_of_day <= 19 else 0.0,
                    soil_ph=round(6.4 + random.uniform(-0.2, 0.2), 2),
                    battery_level=round(99.0 - (0.02 * (144 - step)), 1),
                    network_profile="5g_urllc",
                    network_latency_ms=latency,
                    packet_loss_flag=False,
                    simulated_flag=True,
                    edge_processed=True
                ))

                # Inject past alert & actuation when moisture fell below 20%
                if moist <= 18.5 and step % 30 == 0:
                    alerts.append(Alert(
                        timestamp=ts,
                        zone_id=z_id,
                        zone_name=z_name,
                        alert_type="CRITICAL_SOIL_DROUGHT",
                        severity="CRITICAL",
                        message=f"Critical drought in {z_name}! Soil moisture dropped to {moist:.1f}%.",
                        suggested_action="IRRIGATION REQUIRED: Solenoid valve activated immediately.",
                        acknowledged=True,
                        source="EDGE",
                        response_latency_ms=round(random.uniform(2.1, 3.9), 2),
                        simulated_flag=True
                    ))
                    actuations.append(ActuatorLog(
                        timestamp=ts + timedelta(seconds=2),
                        zone_id=z_id,
                        actuator_type="IRRIGATION_VALVE",
                        action="START",
                        duration_seconds=120,
                        dosage_liters=250.0,
                        triggered_by="EDGE_RULE_CRITICAL_DROUGHT",
                        status="SUCCESS",
                        details="Automatic emergency watering triggered"
                    ))

        session.bulk_save_objects(readings)
        session.bulk_save_objects(alerts)
        session.bulk_save_objects(actuations)
        session.commit()
        print(f"Successfully seeded {len(readings)} sensor records, {len(alerts)} alerts, and {len(actuations)} actuation events.")
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
