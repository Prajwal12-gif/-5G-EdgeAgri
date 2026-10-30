import pytest
from backend.app.network_sim import NetworkSimulator

def test_network_profiles_latency_comparison():
    sim = NetworkSimulator()
    
    # Transmit over 5G URLLC
    edge_tx = sim.transmit(payload_bytes=256, profile_key="5g_urllc")
    assert edge_tx["profile_key"] == "5g_urllc"
    assert edge_tx["latency_ms"] < 15.0  # sub-15ms including serialization
    
    # Transmit over 4G LTE
    lte_tx = sim.transmit(payload_bytes=256, profile_key="4g_lte")
    assert lte_tx["latency_ms"] > 18.0
    
    # Transmit over Remote Cloud WAN
    cloud_tx = sim.transmit(payload_bytes=256, profile_key="remote_cloud_wan")
    assert cloud_tx["latency_ms"] > 80.0
    
    # 5G must be significantly faster than Cloud WAN
    assert edge_tx["latency_ms"] < cloud_tx["latency_ms"]

def test_edge_vs_cloud_roundtrip():
    sim = NetworkSimulator()
    edge_res = sim.simulate_edge_roundtrip(256)
    cloud_res = sim.simulate_cloud_roundtrip(256)
    
    assert edge_res["path"] == "EDGE"
    assert cloud_res["path"] == "CLOUD"
    assert edge_res["total_response_latency_ms"] < cloud_res["total_response_latency_ms"]
    assert edge_res["network_overhead_bytes"] < cloud_res["network_overhead_bytes"]
