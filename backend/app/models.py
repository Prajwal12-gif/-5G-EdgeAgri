from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, Text
from backend.app.database import Base

class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    zone_id = Column(String(50), index=True)
    zone_name = Column(String(100))
    crop_type = Column(String(100))
    
    soil_moisture = Column(Float, nullable=False)   # Percentage (0-100)
    temperature = Column(Float, nullable=False)     # Celsius
    humidity = Column(Float, nullable=False)        # Percentage (0-100)
    water_level = Column(Float, nullable=False)     # Tank / reservoir level (%)
    solar_radiation = Column(Float, default=500.0)  # W/m2
    soil_ph = Column(Float, default=6.5)            # pH 0-14
    battery_level = Column(Float, default=98.0)     # Sensor battery %
    
    # 5G and System metadata
    network_profile = Column(String(50), default="5g_urllc")
    network_latency_ms = Column(Float, default=2.5)
    packet_loss_flag = Column(Boolean, default=False)
    simulated_flag = Column(Boolean, default=True)  # Clearly labels simulated vs real
    edge_processed = Column(Boolean, default=True)

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    zone_id = Column(String(50), index=True)
    zone_name = Column(String(100))
    alert_type = Column(String(100))  # LOW_MOISTURE, HIGH_TEMP, TANK_LOW, ANOMALY_DROP
    severity = Column(String(20), index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    message = Column(Text, nullable=False)
    suggested_action = Column(Text)
    acknowledged = Column(Boolean, default=False)
    source = Column(String(20), default="EDGE")  # EDGE or CLOUD
    response_latency_ms = Column(Float, default=3.2)
    simulated_flag = Column(Boolean, default=True)

class ActuatorLog(Base):
    __tablename__ = "actuator_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    zone_id = Column(String(50), index=True)
    actuator_type = Column(String(50))  # IRRIGATION_VALVE, DRIP_LINE, MIST_PUMP
    action = Column(String(20))          # START, STOP, PULSE
    duration_seconds = Column(Integer, default=60)
    dosage_liters = Column(Float, default=150.0)
    triggered_by = Column(String(50))    # EDGE_AUTONOMOUS, MANUAL_USER, SCHEDULE
    status = Column(String(20), default="SUCCESS")
    details = Column(Text, nullable=True)

class EdgeConfig(Base):
    __tablename__ = "edge_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    zone_id = Column(String(50), unique=True, index=True)
    zone_name = Column(String(100))
    min_moisture = Column(Float, default=25.0)       # Trigger irrigation below this
    critical_moisture = Column(Float, default=18.0)  # Critical threshold (from Slide 9: 18%)
    max_moisture = Column(Float, default=70.0)       # Halt irrigation above this
    min_temperature = Column(Float, default=12.0)
    max_temperature = Column(Float, default=38.0)    # Heat stress alert
    min_humidity = Column(Float, default=30.0)
    min_water_level = Column(Float, default=20.0)    # Tank refill alert
    irrigation_duration_seconds = Column(Integer, default=120)
    auto_actuation_enabled = Column(Boolean, default=True)

class BenchmarkResult(Base):
    __tablename__ = "benchmark_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    scenario_name = Column(String(100))
    workload_size = Column(Integer, default=50)
    network_profile = Column(String(50))
    
    edge_avg_latency_ms = Column(Float)
    cloud_avg_latency_ms = Column(Float)
    edge_processing_ms = Column(Float)
    cloud_processing_ms = Column(Float)
    edge_network_overhead_bytes = Column(Integer)
    cloud_network_overhead_bytes = Column(Integer)
    
    latency_reduction_pct = Column(Float)
    bandwidth_savings_pct = Column(Float)
    decision_consistency_pct = Column(Float)
    details_json = Column(Text, nullable=True)
