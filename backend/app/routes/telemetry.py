import io
import csv
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.models import SensorReading
from backend.app.schemas import SensorReadingOut, AnomalyInjectionRequest
from backend.app.virtual_sensors import virtual_sensors

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

@router.get("/live")
def get_live_telemetry():
    """Returns the latest sensor readings and edge states for all agricultural zones."""
    return {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat(),
        "zones": virtual_sensors.latest_telemetry,
        "is_simulated": True,  # Explicit transparency
        "active_profile": virtual_sensors.zones.get("zone_1", {}).get("network_profile", "5g_urllc")
    }

@router.get("/history", response_model=List[SensorReadingOut])
def get_historical_telemetry(
    zone_id: Optional[str] = Query(None, description="Filter by zone ID"),
    limit: int = Query(100, ge=1, le=2000, description="Max records to return"),
    hours: Optional[int] = Query(24, ge=1, le=168, description="Time window in hours"),
    db: Session = Depends(get_db)
):
    """Fetches historical time-series sensor telemetry from persistent SQLite storage."""
    query = db.query(SensorReading)
    
    if zone_id:
        query = query.filter(SensorReading.zone_id == zone_id)
        
    if hours:
        since_time = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(SensorReading.timestamp >= since_time)
        
    readings = query.order_by(desc(SensorReading.timestamp)).limit(limit).all()
    return readings

@router.get("/export-csv")
def export_telemetry_csv(
    zone_id: Optional[str] = None,
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db)
):
    """Exports historical sensor telemetry to downloadable CSV format."""
    query = db.query(SensorReading)
    if zone_id:
        query = query.filter(SensorReading.zone_id == zone_id)
    readings = query.order_by(desc(SensorReading.timestamp)).limit(limit).all()

    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        "ID", "Timestamp (UTC)", "Zone ID", "Zone Name", "Crop Type",
        "Soil Moisture (%)", "Temperature (C)", "Humidity (%)",
        "Water Tank Level (%)", "Solar Radiation (W/m2)", "Soil pH",
        "Battery Level (%)", "5G Network Profile", "Latency (ms)",
        "Packet Loss Flag", "Simulated Flag"
    ])

    for r in readings:
        writer.writerow([
            r.id, r.timestamp.isoformat() if r.timestamp else "",
            r.zone_id, r.zone_name, r.crop_type,
            r.soil_moisture, r.temperature, r.humidity,
            r.water_level, r.solar_radiation, r.soil_ph,
            r.battery_level, r.network_profile, r.network_latency_ms,
            r.packet_loss_flag, r.simulated_flag
        ])

    output.seek(0)
    filename = f"5g_edgeagri_telemetry_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/inject-anomaly")
def inject_anomaly(req: AnomalyInjectionRequest):
    """
    Simulates dynamic agricultural anomalies for testing edge alerts & actuators.
    Types: DROUGHT_SURGE (drops moisture <= 18%), FROST_SPIKE, HEATWAVE, TANK_DRAIN, NORMAL
    """
    res = virtual_sensors.inject_anomaly(req.zone_id, req.anomaly_type)
    return res
