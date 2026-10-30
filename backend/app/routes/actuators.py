from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.models import ActuatorLog
from backend.app.schemas import ActuatorTriggerRequest, ActuatorLogOut
from backend.app.edge_engine import edge_engine
from backend.app.virtual_sensors import virtual_sensors
from backend.app.cloud_sync import cloud_sync

router = APIRouter(prefix="/actuators", tags=["Actuators"])

@router.get("/status")
def get_actuators_status():
    """Returns the live state of solenoid valves and pumps for all zones."""
    return {
        "status": "success",
        "actuators": edge_engine.active_actuators,
        "zones": {
            z_id: {
                "valve_open": z_id in edge_engine.active_actuators and edge_engine.active_actuators[z_id].get("status") == "RUNNING",
                "details": edge_engine.active_actuators.get(z_id)
            }
            for z_id in ["zone_1", "zone_2", "zone_3"]
        }
    }

@router.post("/trigger")
def trigger_actuator(
    req: ActuatorTriggerRequest,
    db: Session = Depends(get_db)
):
    """
    Manual farmer override to remotely start or stop irrigation valves.
    Transmitted with low-latency over 5G to the edge node.
    """
    if req.action.upper() == "START":
        # Boost virtual soil moisture
        virtual_sensors.trigger_water_replenishment(req.zone_id, req.dosage_liters)
        
        edge_engine.active_actuators[req.zone_id] = {
            "zone_id": req.zone_id,
            "actuator_type": req.actuator_type,
            "action": "START",
            "duration_seconds": req.duration_seconds,
            "dosage_liters": req.dosage_liters,
            "triggered_by": req.reason,
            "status": "RUNNING"
        }
    else:
        if req.zone_id in edge_engine.active_actuators:
            edge_engine.active_actuators[req.zone_id]["status"] = "STOPPED"

    # Persist log
    log = cloud_sync.log_actuation({
        "zone_id": req.zone_id,
        "actuator_type": req.actuator_type,
        "action": req.action.upper(),
        "duration_seconds": req.duration_seconds,
        "dosage_liters": req.dosage_liters,
        "triggered_by": req.reason,
        "status": "SUCCESS",
        "reason": f"Manual override: {req.action}"
    })

    return {
        "status": "success",
        "message": f"Actuator {req.actuator_type} {req.action} command executed for {req.zone_id}",
        "log_id": log.id
    }

@router.get("/history", response_model=List[ActuatorLogOut])
def get_actuator_history(
    zone_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Fetches historical actuation logs."""
    query = db.query(ActuatorLog)
    if zone_id:
        query = query.filter(ActuatorLog.zone_id == zone_id)
    logs = query.order_by(desc(ActuatorLog.timestamp)).limit(limit).all()
    return logs
