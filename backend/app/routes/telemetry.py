import io
import csv
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
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
    return {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat(),
        "zones": virtual_sensors.latest_telemetry,
        "is_simulated": True,
        "active_profile": virtual_sensors.zones.get("zone_1", {}).get("network_profile", "5g_urllc"),
    }


@router.get("/history", response_model=list[SensorReadingOut])
def get_historical_telemetry(
    zone_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=2000),
    hours: Optional[int] = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    query = db.query(SensorReading)
    if zone_id:
        query = query.filter(SensorReading.zone_id == zone_id)
    if hours:
        query = query.filter(SensorReading.timestamp >= datetime.utcnow() - timedelta(hours=hours))
    return query.order_by(desc(SensorReading.timestamp)).limit(limit).all()


@router.get("/export-csv")
def export_telemetry_csv(
    zone_id: Optional[str] = None,
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
):
    query = db.query(SensorReading)
    if zone_id:
        query = query.filter(SensorReading.zone_id == zone_id)
    readings = query.order_by(desc(SensorReading.timestamp)).limit(limit).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Timestamp (UTC)", "Zone ID", "Zone Name", "Crop Type",
        "Soil Moisture (%)", "Temperature (C)", "Humidity (%)", "Water Tank Level (%)",
        "Solar Radiation (W/m2)", "Soil pH", "Battery Level (%)", "5G Network Profile",
        "Latency (ms)", "Packet Loss Flag", "Simulated Flag",
    ])
    for r in readings:
        writer.writerow([
            r.id, r.timestamp.isoformat() if r.timestamp else "", r.zone_id, r.zone_name,
            r.crop_type, r.soil_moisture, r.temperature, r.humidity, r.water_level,
            r.solar_radiation, r.soil_ph, r.battery_level, r.network_profile,
            r.network_latency_ms, r.packet_loss_flag, r.simulated_flag,
        ])
    output.seek(0)
    filename = f"5g_edgeagri_telemetry_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/inject-anomaly")
def inject_anomaly(req: AnomalyInjectionRequest):
    result = virtual_sensors.inject_anomaly(req.zone_id, req.anomaly_type)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Invalid anomaly request"))
    return result
