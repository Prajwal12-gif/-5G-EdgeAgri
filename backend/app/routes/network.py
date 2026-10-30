from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.network_sim import network_simulator

router = APIRouter(prefix="/network", tags=["5G Network Simulation"])

class SetProfileRequest(BaseModel):
    profile_key: str

@router.get("/profiles")
def get_network_profiles():
    """Returns available 5G and legacy cellular simulation profiles."""
    return {
        "active_profile": network_simulator.active_profile_key,
        "profiles": network_simulator.PROFILES
    }

@router.get("/status")
def get_network_status():
    """Returns real-time network traffic counters and packet delivery health."""
    active = network_simulator.get_profile()
    loss_rate = 0.0
    if network_simulator.total_packets_sent > 0:
        loss_rate = round((network_simulator.total_packets_dropped / network_simulator.total_packets_sent) * 100, 3)

    return {
        "active_profile_key": network_simulator.active_profile_key,
        "active_profile_name": active["name"],
        "base_latency_ms": active["base_latency_ms"],
        "jitter_ms": active["jitter_ms"],
        "bandwidth_mbps": active["bandwidth_mbps"],
        "total_packets_sent": network_simulator.total_packets_sent,
        "total_packets_dropped": network_simulator.total_packets_dropped,
        "measured_loss_rate_pct": loss_rate,
        "total_megabytes_transferred": round(network_simulator.total_bytes_transferred / (1024 * 1024), 2),
        "is_simulated": True
    }

@router.post("/set-profile")
def set_active_profile(req: SetProfileRequest):
    """Dynamically switches active simulated wireless profile (e.g. 5G URLLC vs 4G LTE)."""
    success = network_simulator.set_active_profile(req.profile_key)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid profile '{req.profile_key}'. Available: {list(network_simulator.PROFILES.keys())}"
        )
    return {
        "status": "success",
        "active_profile": network_simulator.active_profile_key,
        "details": network_simulator.get_profile()
    }
