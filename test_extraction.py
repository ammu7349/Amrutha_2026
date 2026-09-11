"""
Unit and syntax verification test for RoadSafe AI extraction schemas.
"""

import json
import os
from gemini_extractor import AccidentReport, VehicleInfo, InjuryInfo, extract_accident_report, get_simulated_report

def test_pydantic_schema():
    print("1. Testing AccidentReport Pydantic schema deserialization...")
    sample_data = {
        "severity_level": "CRITICAL",
        "incident_type": "Multi-Vehicle Collision",
        "location": "Interstate 95 South near Exit 42",
        "vehicles": [
            {
                "vehicle_type": "Pickup Truck",
                "color": "Blue",
                "details": "Ford F-150 with front-end damage"
            },
            {
                "vehicle_type": "Sedan",
                "color": "Silver",
                "details": "Honda Civic rear-ended, heavy deformation"
            }
        ],
        "injuries": {
            "status": "1 driver bleeding from forehead, disoriented",
            "count_estimate": "1-2",
            "severity": "Serious",
            "trapped_persons": False
        },
        "hazards_present": [
            "Fuel leak from delivery truck",
            "Two right lanes completely blocked",
            "Wet roadway due to rain"
        ],
        "missing_critical_info": [
            "Exact mile marker or closest emergency turnout",
            "Whether fuel leak has ignited or smells strongly",
            "Consciousness level of the Civic driver"
        ],
        "photo_observations": None,
        "dispatch_script": "EMERGENCY DISPATCH: CRITICAL - Multi-Vehicle Collision at I-95 South near Exit 42. 3 vehicles involved (Blue Ford F-150, Silver Honda Civic, Delivery Truck). 1 driver bleeding from head. Active fuel leak blocking 2 lanes. Requesting urgent EMS, Fire, and Highway Patrol."
    }

    report = AccidentReport(**sample_data)
    assert report.severity_level == "CRITICAL"
    assert len(report.vehicles) == 2
    assert report.injuries.severity == "Serious"
    assert len(report.hazards_present) == 3
    assert len(report.missing_critical_info) == 3
    print("   [OK] Schema deserialization passed successfully!")

def test_input_validation():
    print("2. Testing input validation for empty description and key...")
    try:
        extract_accident_report("", "")
        assert False, "Should have raised ValueError for empty description"
    except ValueError as e:
        assert "Accident description cannot be empty" in str(e)
        print("   [OK] Empty description check passed.")

    try:
        extract_accident_report("Two cars crashed on Broadway", "")
        assert False, "Should have raised ValueError for empty API key"
    except ValueError as e:
        assert "Google Gemini API Key is required" in str(e)
        print("   [OK] Missing API key check passed.")

def test_simulation():
    print("3. Testing offline simulation mode...")
    sim_report = get_simulated_report("Two cars crashed at 5th and Main. Blue sedan rear ended black truck. Fuel leak.", has_image=True)
    assert sim_report.severity_level in ["CRITICAL", "HIGH", "MODERATE", "MINOR"]
    assert len(sim_report.vehicles) > 0
    assert len(sim_report.hazards_present) > 0
    assert sim_report.photo_observations is not None
    assert "EMERGENCY DISPATCH" in sim_report.dispatch_script
    print("   [OK] Simulation mode passed successfully!")

if __name__ == "__main__":
    test_pydantic_schema()
    test_input_validation()
    test_simulation()
    print("\nAll local schema and validation tests passed successfully!")
