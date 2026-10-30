import pytest
from backend.app.edge_engine import EdgeProcessingEngine

def test_critical_soil_moisture_triggers_irrigation():
    """
    Validates Slide 9 scenario:
    'Soil moisture = 18% -> Edge detects critical condition -> IRRIGATION REQUIRED'
    """
    engine = EdgeProcessingEngine()
    reading = {
        "zone_id": "zone_1",
        "zone_name": "Zone 1 - Wheat Fields",
        "soil_moisture": 18.0,  # Slide 9 critical condition
        "temperature": 26.0,
        "humidity": 45.0,
        "water_level": 80.0
    }
    result = engine.evaluate_reading(reading)
    
    # Assert alert was created with CRITICAL severity
    critical_alerts = [a for a in result["alerts"] if a["severity"] == "CRITICAL" and a["alert_type"] == "CRITICAL_SOIL_DROUGHT"]
    assert len(critical_alerts) >= 1
    assert "IRRIGATION REQUIRED" in critical_alerts[0]["suggested_action"]
    
    # Assert actuation trigger occurred
    actuation = result["actuation_trigger"]
    assert actuation is not None
    assert actuation["actuator_type"] == "IRRIGATION_VALVE"
    assert actuation["action"] == "START"
    assert result["processing_time_ms"] < 20.0  # Ultra-fast edge computation

def test_water_tank_critical_depletion():
    engine = EdgeProcessingEngine()
    reading = {
        "zone_id": "zone_2",
        "zone_name": "Zone 2 - Greenhouse",
        "soil_moisture": 15.0,  # dry
        "temperature": 25.0,
        "humidity": 50.0,
        "water_level": 8.0     # critically depleted reservoir
    }
    result = engine.evaluate_reading(reading)
    tank_alerts = [a for a in result["alerts"] if a["alert_type"] == "WATER_TANK_CRITICAL"]
    assert len(tank_alerts) == 1
    # Automated irrigation should be restricted when water is empty
    assert result["actuation_trigger"] is None

def test_heat_stress_anomaly():
    engine = EdgeProcessingEngine()
    reading = {
        "zone_id": "zone_3",
        "zone_name": "Zone 3 - Maize",
        "soil_moisture": 40.0,
        "temperature": 41.2,  # exceeds 39 threshold
        "humidity": 30.0,
        "water_level": 70.0
    }
    result = engine.evaluate_reading(reading)
    heat_alerts = [a for a in result["alerts"] if a["alert_type"] == "HEAT_STRESS_ALERT"]
    assert len(heat_alerts) == 1
