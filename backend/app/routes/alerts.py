from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.models import Alert
from backend.app.schemas import AlertOut

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertOut])
def get_alerts(
    zone_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    unacknowledged_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Fetches real-time edge and cloud alerts with priority filtering."""
    query = db.query(Alert)
    if zone_id:
        query = query.filter(Alert.zone_id == zone_id)
    if severity:
        query = query.filter(Alert.severity == severity.upper())
    if unacknowledged_only:
        query = query.filter(Alert.acknowledged == False)
        
    alerts = query.order_by(desc(Alert.timestamp)).limit(limit).all()
    return alerts

@router.put("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Marks an alert as acknowledged by the farmer."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        
    alert.acknowledged = True
    db.commit()
    db.refresh(alert)
    return {"status": "success", "message": f"Alert {alert_id} acknowledged", "alert": alert}

@router.post("/acknowledge-all")
def acknowledge_all_alerts(db: Session = Depends(get_db)):
    """Acknowledges all active pending alerts."""
    db.query(Alert).filter(Alert.acknowledged == False).update({Alert.acknowledged: True})
    db.commit()
    return {"status": "success", "message": "All pending alerts marked as acknowledged"}
