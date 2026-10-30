from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class SensorReadingBase(BaseModel):
    zone_id: str
    zone_name: str
    crop_type: str
    soil_moisture: float = Field(..., ge=0.0, le=100.0, description="Soil moisture in %")
    temperature: float = Field(..., ge=-20.0, le=60.0, description="Temperature in °C")
    humidity: float = Field(..., ge=0.0, le=100.0, description="Relative humidity in %")
    water_level: float = Field(..., ge=0.0, le=100.0, description="Water tank level in %")
    solar_radiation: Optional[float] = 500.0
    soil_ph: Optional[float] = 6.5
    battery_level: Optional[float] = 98.0
    network_profile: Optional[str] = "5g_urllc"
    network_latency_ms: Optional[float] = 2.5
    packet_loss_flag: Optional[bool] = False
    simulated_flag: bool = True
    edge_processed: bool = True

class SensorReadingCreate(SensorReadingBase):
    pass

class SensorReadingOut(SensorReadingBase):
    id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class AlertBase(BaseModel):
    zone_id: str
    zone_name: str
    alert_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    suggested_action: Optional[str] = None
    acknowledged: bool = False
    source: str = "EDGE"
    response_latency_ms: float = 3.2
    simulated_flag: bool = True

class AlertCreate(AlertBase):
    pass

class AlertOut(AlertBase):
    id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class EdgeConfigBase(BaseModel):
    zone_id: str
    zone_name: str
    min_moisture: float = 25.0
    critical_moisture: float = 18.0
    max_moisture: float = 70.0
    min_temperature: float = 12.0
    max_temperature: float = 38.0
    min_humidity: float = 30.0
    min_water_level: float = 20.0
    irrigation_duration_seconds: int = 120
    auto_actuation_enabled: bool = True

class EdgeConfigUpdate(BaseModel):
    min_moisture: Optional[float] = None
    critical_moisture: Optional[float] = None
    max_moisture: Optional[float] = None
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    min_humidity: Optional[float] = None
    min_water_level: Optional[float] = None
    irrigation_duration_seconds: Optional[int] = None
    auto_actuation_enabled: Optional[bool] = None

class EdgeConfigOut(EdgeConfigBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ActuatorTriggerRequest(BaseModel):
    zone_id: str
    actuator_type: str = "IRRIGATION_VALVE"
    action: str = "START"  # START, STOP
    duration_seconds: int = 60
    dosage_liters: float = 150.0
    reason: str = "MANUAL_USER_OVERRIDE"

class ActuatorLogOut(BaseModel):
    id: int
    timestamp: datetime
    zone_id: str
    actuator_type: str
    action: str
    duration_seconds: int
    dosage_liters: float
    triggered_by: str
    status: str
    details: Optional[str]
    model_config = ConfigDict(from_attributes=True)

class NetworkProfileConfig(BaseModel):
    profile_name: str  # 5g_urllc, 5g_embb, 4g_lte, remote_cloud
    base_latency_ms: float
    jitter_ms: float
    packet_loss_rate: float
    bandwidth_mbps: float

class BenchmarkRequest(BaseModel):
    workload_size: int = Field(50, ge=10, le=500, description="Number of sensor events to evaluate")
    network_profile: str = "5g_urllc"

class BenchmarkOut(BaseModel):
    scenario_name: str
    workload_size: int
    network_profile: str
    edge_avg_latency_ms: float
    cloud_avg_latency_ms: float
    edge_processing_ms: float
    cloud_processing_ms: float
    edge_network_overhead_bytes: int
    cloud_network_overhead_bytes: int
    latency_reduction_pct: float
    bandwidth_savings_pct: float
    decision_consistency_pct: float
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

class AnomalyInjectionRequest(BaseModel):
    zone_id: str
    anomaly_type: str  # DROUGHT_SURGE, FROST_SPIKE, HEATWAVE, TANK_DRAIN, NORMAL
