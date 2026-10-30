import json
import time
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database import get_db
from backend.app.models import BenchmarkResult
from backend.app.schemas import BenchmarkRequest, BenchmarkOut
from backend.app.network_sim import network_simulator
from backend.app.edge_engine import edge_engine

router = APIRouter(prefix="/benchmark", tags=["Edge vs Cloud Evaluation"])

@router.post("/run", response_model=BenchmarkOut)
def run_edge_vs_cloud_benchmark(
    req: BenchmarkRequest,
    db: Session = Depends(get_db)
):
    """
    Executes a controlled comparative workload test between:
    1. Edge Path: Sensor -> 5G URLLC -> Edge Node -> Decision & Actuation
    2. Cloud Path: Sensor -> 5G/4G WAN -> Remote Cloud Datacenter -> Decision -> Actuation
    
    Measures latency, processing time, network overhead, and decision consistency.
    """
    workload_size = req.workload_size
    profile_key = req.network_profile

    edge_latencies: List[float] = []
    cloud_latencies: List[float] = []
    edge_proc_times: List[float] = []
    cloud_proc_times: List[float] = []
    
    edge_bytes_total = 0
    cloud_bytes_total = 0

    agreed_decisions = 0
    synthetic_payload_size = 256  # standard JSON telemetry packet size in bytes

    for i in range(workload_size):
        simulated_moisture = 15.0 + (i % 25)
        simulated_temp = 22.0 + (i % 18)
        sample_packet = {
            "zone_id": "zone_1",
            "zone_name": "Zone 1 - Wheat Fields",
            "soil_moisture": simulated_moisture,
            "temperature": simulated_temp,
            "humidity": 50.0,
            "water_level": 70.0
        }

        # 1. Edge Execution
        edge_trip = network_simulator.simulate_edge_roundtrip(synthetic_payload_size)
        edge_eval = edge_engine.evaluate_reading(sample_packet)
        edge_latencies.append(edge_trip["total_response_latency_ms"])
        edge_proc_times.append(edge_eval["processing_time_ms"])
        edge_bytes_total += edge_trip["network_overhead_bytes"]

        # 2. Cloud Execution
        cloud_trip = network_simulator.simulate_cloud_roundtrip(synthetic_payload_size)
        cloud_eval = edge_engine.evaluate_reading(sample_packet)
        cloud_latencies.append(cloud_trip["total_response_latency_ms"])
        cloud_proc_times.append(cloud_trip["compute_latency_ms"])
        cloud_bytes_total += cloud_trip["network_overhead_bytes"]

        # Verify decision consistency
        edge_alert_types = [a["alert_type"] for a in edge_eval["alerts"]]
        cloud_alert_types = [a["alert_type"] for a in cloud_eval["alerts"]]
        if edge_alert_types == cloud_alert_types:
            agreed_decisions += 1

    edge_avg_latency = round(sum(edge_latencies) / len(edge_latencies), 2)
    cloud_avg_latency = round(sum(cloud_latencies) / len(cloud_latencies), 2)
    edge_avg_proc = round(sum(edge_proc_times) / len(edge_proc_times), 3)
    cloud_avg_proc = round(sum(cloud_proc_times) / len(cloud_proc_times), 3)

    latency_reduction_pct = round(((cloud_avg_latency - edge_avg_latency) / cloud_avg_latency) * 100.0, 1)
    bandwidth_savings_pct = round(((cloud_bytes_total - edge_bytes_total) / cloud_bytes_total) * 100.0, 1)
    decision_consistency_pct = round((agreed_decisions / workload_size) * 100.0, 1)

    details = {
        "edge_latency_samples": edge_latencies[:20],
        "cloud_latency_samples": cloud_latencies[:20],
        "workload_profile": profile_key,
        "sample_size": workload_size
    }

    benchmark_record = BenchmarkResult(
        timestamp=datetime.utcnow(),
        scenario_name="Controlled 5G-Edge vs Remote Cloud Workload Evaluation",
        workload_size=workload_size,
        network_profile=profile_key,
        edge_avg_latency_ms=edge_avg_latency,
        cloud_avg_latency_ms=cloud_avg_latency,
        edge_processing_ms=edge_avg_proc,
        cloud_processing_ms=cloud_avg_proc,
        edge_network_overhead_bytes=edge_bytes_total,
        cloud_network_overhead_bytes=cloud_bytes_total,
        latency_reduction_pct=latency_reduction_pct,
        bandwidth_savings_pct=bandwidth_savings_pct,
        decision_consistency_pct=decision_consistency_pct,
        details_json=json.dumps(details)
    )
    db.add(benchmark_record)
    db.commit()
    db.refresh(benchmark_record)

    return BenchmarkOut(
        scenario_name=benchmark_record.scenario_name,
        workload_size=workload_size,
        network_profile=profile_key,
        edge_avg_latency_ms=edge_avg_latency,
        cloud_avg_latency_ms=cloud_avg_latency,
        edge_processing_ms=edge_avg_proc,
        cloud_processing_ms=cloud_avg_proc,
        edge_network_overhead_bytes=edge_bytes_total,
        cloud_network_overhead_bytes=cloud_bytes_total,
        latency_reduction_pct=latency_reduction_pct,
        bandwidth_savings_pct=bandwidth_savings_pct,
        decision_consistency_pct=decision_consistency_pct,
        timestamp=benchmark_record.timestamp,
        details=details
    )

@router.get("/history")
def get_benchmark_history(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Fetches past evaluation benchmark results."""
    records = db.query(BenchmarkResult).order_by(desc(BenchmarkResult.timestamp)).limit(limit).all()
    return records
