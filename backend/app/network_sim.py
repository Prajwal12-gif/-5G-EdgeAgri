import random
import time
from typing import Dict, Any, Tuple

class NetworkSimulator:
    """
    Simulates 5G (URLLC / eMBB), 4G LTE, and Remote Cloud WAN networking characteristics:
    latency, jitter, packet loss, bandwidth, and communication overhead.
    """
    PROFILES = {
        "5g_urllc": {
            "name": "5G URLLC (Ultra-Reliable Low-Latency)",
            "base_latency_ms": 2.2,
            "jitter_ms": 0.4,
            "packet_loss_rate": 0.0005,  # 99.95% reliability
            "bandwidth_mbps": 1000.0,
            "description": "Sub-millisecond 5G radio interface with edge server co-located at gNodeB"
        },
        "5g_embb": {
            "name": "5G eMBB (Enhanced Mobile Broadband)",
            "base_latency_ms": 9.5,
            "jitter_ms": 1.8,
            "packet_loss_rate": 0.005,
            "bandwidth_mbps": 2500.0,
            "description": "High-throughput 5G carrier band for multimedia/sensor streams"
        },
        "4g_lte": {
            "name": "4G LTE (Legacy Cellular)",
            "base_latency_ms": 48.0,
            "jitter_ms": 9.5,
            "packet_loss_rate": 0.025,
            "bandwidth_mbps": 45.0,
            "description": "Traditional 4G cellular uplink with higher round-trip radio latency"
        },
        "remote_cloud_wan": {
            "name": "Remote Cloud WAN (Multi-hop Internet)",
            "base_latency_ms": 142.0,
            "jitter_ms": 24.0,
            "packet_loss_rate": 0.038,
            "bandwidth_mbps": 100.0,
            "description": "Centralized Cloud datacenter via internet routing, gateways, and firewalls"
        }
    }

    def __init__(self):
        self.active_profile_key = "5g_urllc"
        self.total_packets_sent = 0
        self.total_packets_dropped = 0
        self.total_bytes_transferred = 0

    def get_profile(self, profile_key: str = None) -> Dict[str, Any]:
        key = profile_key or self.active_profile_key
        return self.PROFILES.get(key, self.PROFILES["5g_urllc"])

    def set_active_profile(self, profile_key: str) -> bool:
        if profile_key in self.PROFILES:
            self.active_profile_key = profile_key
            return True
        return False

    def transmit(self, payload_bytes: int, profile_key: str = None) -> Dict[str, Any]:
        """
        Calculates simulated network transmission latency, jitter, and packet loss.
        """
        profile = self.get_profile(profile_key)
        self.total_packets_sent += 1
        self.total_bytes_transferred += payload_bytes

        # Jitter follows normal distribution
        jitter = random.gauss(0, profile["jitter_ms"])
        # Ensure jitter doesn't reduce latency below physical hardware limits
        latency = max(0.8, profile["base_latency_ms"] + jitter)

        # Transmission serialization delay: (payload in bits) / (bandwidth in bps) * 1000 ms
        transmission_delay_ms = (payload_bytes * 8) / (profile["bandwidth_mbps"] * 1_000_000) * 1000.0
        total_latency_ms = round(latency + transmission_delay_ms, 2)

        # Check packet loss
        is_dropped = random.random() < profile["packet_loss_rate"]
        retransmitted = False
        if is_dropped:
            self.total_packets_dropped += 1
            # Retransmission penalty (ARQ / HARQ in 5G is ~2-4ms, TCP over WAN is 2x RTT)
            retransmission_penalty = 3.5 if "5g" in (profile_key or self.active_profile_key) else (profile["base_latency_ms"] * 1.8)
            total_latency_ms = round(total_latency_ms + retransmission_penalty, 2)
            retransmitted = True

        return {
            "profile_key": profile_key or self.active_profile_key,
            "profile_name": profile["name"],
            "latency_ms": total_latency_ms,
            "jitter_ms": round(abs(jitter), 2),
            "payload_bytes": payload_bytes,
            "packet_lost": is_dropped,
            "retransmitted": retransmitted,
            "simulated": True  # Explicitly flagged
        }

    def simulate_edge_roundtrip(self, payload_bytes: int = 256) -> Dict[str, Any]:
        """
        Edge Path: Sensor -> 5G URLLC -> Edge Node (local rule engine) -> Local Actuator
        Total latency = Uplink (5G) + Edge Compute (~0.8-2ms) + Local Downlink
        """
        edge_uplink = self.transmit(payload_bytes, "5g_urllc")
        edge_compute_time_ms = round(random.uniform(0.6, 2.1), 2)
        edge_downlink_latency = round(edge_uplink["latency_ms"] * 0.9, 2)
        total_response_ms = round(edge_uplink["latency_ms"] + edge_compute_time_ms + edge_downlink_latency, 2)

        return {
            "path": "EDGE",
            "network_profile": "5g_urllc",
            "network_latency_ms": edge_uplink["latency_ms"],
            "compute_latency_ms": edge_compute_time_ms,
            "total_response_latency_ms": total_response_ms,
            "network_overhead_bytes": payload_bytes * 2,  # uplink + ack
            "packet_loss": edge_uplink["packet_lost"]
        }

    def simulate_cloud_roundtrip(self, payload_bytes: int = 256) -> Dict[str, Any]:
        """
        Cloud Path: Sensor -> 5G / 4G -> ISP WAN -> Remote Cloud -> Rule Engine -> Return Trip
        Total latency = WAN Uplink (40-150ms) + Cloud Compute (~8-25ms) + WAN Downlink
        """
        wan_uplink = self.transmit(payload_bytes, "remote_cloud_wan")
        cloud_compute_time_ms = round(random.uniform(8.5, 26.0), 2)
        wan_downlink_latency = round(wan_uplink["latency_ms"] * 0.95, 2)
        total_response_ms = round(wan_uplink["latency_ms"] + cloud_compute_time_ms + wan_downlink_latency, 2)

        return {
            "path": "CLOUD",
            "network_profile": "remote_cloud_wan",
            "network_latency_ms": wan_uplink["latency_ms"],
            "compute_latency_ms": cloud_compute_time_ms,
            "total_response_latency_ms": total_response_ms,
            "network_overhead_bytes": payload_bytes * 4,  # TCP handshakes, TLS overhead, remote headers
            "packet_loss": wan_uplink["packet_lost"]
        }

network_simulator = NetworkSimulator()
