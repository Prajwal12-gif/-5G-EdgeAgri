import pytest
from backend.app.database import get_db, init_db
from backend.app.cloud_sync import cloud_sync
from backend.app.routes import telemetry, alerts, edge, actuators, network, benchmark
from backend.app.schemas import BenchmarkRequest, ActuatorTriggerRequest, AnomalyInjectionRequest

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()
    cloud_sync.seed_default_edge_configs()

def test_telemetry_live():
    res = telemetry.get_live_telemetry()
    assert res["status"] == "success"
    assert res["is_simulated"] is True
    assert "timestamp" in res

def test_network_profiles():
    res = network.get_network_profiles()
    assert "5g_urllc" in res["profiles"]
    assert "remote_cloud_wan" in res["profiles"]
    assert res["profiles"]["5g_urllc"]["base_latency_ms"] < 5.0

def test_edge_configs():
    configs = edge.get_edge_configs()
    assert "zone_1" in configs
    assert configs["zone_1"]["critical_moisture"] == 18.0

def test_actuator_status_and_trigger():
    db = next(get_db())
    try:
        # Trigger an actuation
        req = ActuatorTriggerRequest(
            zone_id="zone_1",
            actuator_type="IRRIGATION_VALVE",
            action="START",
            duration_seconds=60,
            dosage_liters=120.0,
            reason="UNIT_TEST_TRIGGER"
        )
        res = actuators.trigger_actuator(req, db=db)
        assert res["status"] == "success"
        
        # Verify status
        status = actuators.get_actuators_status()
        assert status["zones"]["zone_1"]["valve_open"] is True
    finally:
        db.close()

def test_controlled_benchmark_evaluation():
    db = next(get_db())
    try:
        req = BenchmarkRequest(workload_size=20, network_profile="5g_urllc")
        result = benchmark.run_edge_vs_cloud_benchmark(req, db=db)
        assert result.workload_size == 20
        assert result.edge_avg_latency_ms < result.cloud_avg_latency_ms
        assert result.latency_reduction_pct > 70.0  # Typically ~85-95% faster at edge
        assert result.decision_consistency_pct >= 90.0
        assert result.bandwidth_savings_pct > 0.0
    finally:
        db.close()

def test_anomaly_injection():
    req = AnomalyInjectionRequest(zone_id="zone_1", anomaly_type="DROUGHT_SURGE")
    res = telemetry.inject_anomaly(req)
    assert res["status"] == "success"
    assert res["current_state"]["soil_moisture"] <= 18.0
