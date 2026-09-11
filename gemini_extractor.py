"""
RoadSafe AI - Gemini Accident Data Extractor
Extracts structured emergency incident data from accident descriptions and photos.
"""

from __future__ import annotations
import json
import os
from typing import List, Optional
from pydantic import BaseModel, Field
from PIL import Image

try:
    from google import genai
    from google.genai import types
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False

HAS_LEGACY_GENAI = False
if not HAS_GOOGLE_GENAI:
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FutureWarning)
            import google.generativeai as legacy_genai
        HAS_LEGACY_GENAI = True
    except ImportError:
        HAS_LEGACY_GENAI = False


class VehicleInfo(BaseModel):
    vehicle_type: str = Field(description="Type of vehicle (e.g., Sedan, SUV, Pickup Truck, Motorcycle, Bus, Bicycle, Pedestrian)")
    color: Optional[str] = Field(default="Unknown", description="Color or visual description of vehicle")
    details: Optional[str] = Field(default="", description="Observed damage, orientation, or role in collision")


class InjuryInfo(BaseModel):
    status: str = Field(description="Summary of injury status (e.g., '1 critical, 2 conscious', 'No injuries reported', 'Unknown')")
    count_estimate: str = Field(description="Estimated number of injured persons or 'Unknown'")
    severity: str = Field(description="Highest severity: Critical, Serious, Minor, None, or Unknown")
    trapped_persons: bool = Field(default=False, description="True if any occupants appear or are reported trapped")


class AccidentReport(BaseModel):
    severity_level: str = Field(description="Overall incident urgency: CRITICAL, HIGH, MODERATE, or MINOR")
    incident_type: str = Field(description="Classification: e.g., Head-on Collision, T-Bone, Rear-End, Rollover, Hit-and-Run, Multi-Car Pileup, Pedestrian Involved")
    location: str = Field(description="Specific location, cross streets, landmarks, highway mile marker, or 'Unknown - Not Specified'")
    vehicles: List[VehicleInfo] = Field(default_factory=list, description="List of vehicles/parties involved")
    injuries: InjuryInfo = Field(description="Injury assessment and casualty count")
    hazards_present: List[str] = Field(default_factory=list, description="Roadway and environmental hazards (e.g., Fuel leak, Fire risk, Blocked lanes, Downed lines)")
    missing_critical_info: List[str] = Field(
        default_factory=list,
        description="Crucial details dispatchers urgently need that were missing from the report (e.g., exact street number, consciousness of victims, fuel leak status)"
    )
    photo_observations: Optional[str] = Field(
        default=None,
        description="Observations extracted from the uploaded photo, such as visible vehicle deformation, airbag deployment, or road conditions"
    )
    dispatch_script: str = Field(
        description="Concise, standardized 911/EMS dispatch radio-ready message that can be read or transmitted directly to emergency operators"
    )


EXTRACTION_SYSTEM_PROMPT = """
You are RoadSafe AI, an expert emergency dispatch analyst assisting in rapid traffic incident intake.
Your mission is to parse accident descriptions (and optional accident scene photos) into a structured, highly accurate emergency report.

GUIDELINES:
1. Urgency & Severity:
   - CRITICAL: Life-threatening injuries, trapped victims, vehicle fire, rollovers on high-speed highways, or unconscious persons.
   - HIGH: Serious injuries, multiple vehicles blocking active highway lanes, suspected hazardous leaks.
   - MODERATE: Minor injuries, non-blocking collisions, minor intersection crashes.
   - MINOR: Property damage only, fender benders, clear roadways.
2. Missing Critical Info: Always identify what 911 dispatchers would urgently ask (e.g., exact direction of travel, number of trapped passengers, infant/child involvement, presence of smoke/flames).
3. Dispatch Script: Must be clear, crisp, and direct. Format:
   "EMERGENCY DISPATCH: [Severity] - [Incident Type] at [Location]. [Vehicles count] vehicles involved ([vehicle summary]). Injuries: [Injury summary]. Hazards: [Hazards summary]. Action needed: [EMS/Police/Fire dispatch request]."
4. Accuracy: Do NOT hallucinate specific addresses if not provided. State "Not provided - need cross streets" in missing info.
"""


def extract_accident_report(
    description: str,
    api_key: str,
    image: Optional[Image.Image] = None,
    model_name: str = "gemini-2.5-flash"
) -> AccidentReport:
    """
    Extract structured accident data from description and optional image.
    Supports google-genai modern SDK with fallback to google-generativeai.
    """
    if not description or not description.strip():
        raise ValueError("Accident description cannot be empty.")

    if not api_key or not api_key.strip():
        raise ValueError("Google Gemini API Key is required.")

    clean_api_key = api_key.strip()
    user_prompt = f"Accident Description:\n{description.strip()}"
    if image is not None:
        user_prompt += "\n\nAn accident scene photo is also provided. Analyze the photo alongside the description to confirm vehicles, damage, hazards, and scene details."

    # Try modern google-genai SDK first
    if HAS_GOOGLE_GENAI:
        try:
            client = genai.Client(api_key=clean_api_key)
            contents = [user_prompt]
            if image is not None:
                contents.append(image)

            # Using Gemini with structured response schema
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=EXTRACTION_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=AccidentReport,
                    temperature=0.1,
                )
            )

            if response.text:
                data = json.loads(response.text)
                return AccidentReport(**data)
        except Exception as e:
            # Fall back to legacy if modern fails or if model not recognized
            if not HAS_LEGACY_GENAI:
                raise RuntimeError(f"Gemini extraction error: {e}")

    # Fallback to legacy google-generativeai SDK
    if HAS_LEGACY_GENAI:
        try:
            legacy_genai.configure(api_key=clean_api_key)
            # Try gemini-1.5-flash or specified model
            legacy_model_name = "gemini-1.5-flash" if "2.5" in model_name else model_name
            model = legacy_genai.GenerativeModel(
                model_name=legacy_model_name,
                system_instruction=EXTRACTION_SYSTEM_PROMPT,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.1,
                }
            )

            prompt_parts = [
                f"{user_prompt}\n\nYou must return a JSON object matching this schema:\n"
                f"{json.dumps(AccidentReport.model_json_schema())}"
            ]
            if image is not None:
                prompt_parts.append(image)

            response = model.generate_content(prompt_parts)
            if not response.text:
                raise ValueError("Empty response received from Gemini.")

            data = json.loads(response.text)
            return AccidentReport(**data)
        except Exception as e:
            raise RuntimeError(f"Gemini API request failed: {e}")

    raise RuntimeError("Neither 'google-genai' nor 'google-generativeai' is installed.")


def get_simulated_report(description: str, has_image: bool = False) -> AccidentReport:
    """
    Returns a high-fidelity simulated AccidentReport for demonstration/offline evaluation.
    """
    desc_lower = description.lower()
    is_critical = any(w in desc_lower for w in ["fire", "bleed", "bleeding", "unconscious", "trapped", "fatal", "fuel leak", "roll", "severe"])
    severity = "CRITICAL" if is_critical else "HIGH" if any(w in desc_lower for w in ["injury", "pain", "hospital", "paramedic", "t-bone"]) else "MODERATE"

    # Infer vehicles
    vehicles = []
    if "truck" in desc_lower or "f-150" in desc_lower:
        vehicles.append(VehicleInfo(vehicle_type="Pickup / Truck", color="Blue/Dark", details="Frontal crash impact reported"))
    if "civic" in desc_lower or "sedan" in desc_lower:
        vehicles.append(VehicleInfo(vehicle_type="Sedan", color="Silver/Black", details="Rear and cabin collision damage"))
    if "motorcycle" in desc_lower or "bike" in desc_lower:
        vehicles.append(VehicleInfo(vehicle_type="Motorcycle", color="Dark", details="Down on pavement with fluid leakage"))
    if "pedestrian" in desc_lower:
        vehicles.append(VehicleInfo(vehicle_type="Pedestrian", color="N/A", details="Pedestrian struck at crosswalk"))
    if not vehicles:
        vehicles.append(VehicleInfo(vehicle_type="Passenger Vehicle", color="Unknown", details="Direct collision impact"))

    # Infer injuries
    has_trapped = "trapped" in desc_lower
    injuries = InjuryInfo(
        status="1-2 individuals reporting injuries or requiring medical triage" if is_critical else "Injuries reported at scene",
        count_estimate="1 to 2",
        severity="Critical" if is_critical else "Serious",
        trapped_persons=has_trapped
    )

    hazards = []
    if "fuel" in desc_lower or "leak" in desc_lower or "oil" in desc_lower:
        hazards.append("Flammable fluid / fuel spill on roadway")
    if "lane" in desc_lower or "traffic" in desc_lower or "block" in desc_lower:
        hazards.append("Traffic lanes blocked creating secondary collision hazard")
    if "rain" in desc_lower or "wet" in desc_lower:
        hazards.append("Wet road surface / reduced vehicle traction")
    if not hazards:
        hazards.append("Active vehicle debris in roadway")

    missing = [
        "Are all occupants conscious and breathing normally?",
        "Is there any active smoke, flame, or electrical spark?",
        "Exact highway milepost or nearest cross street reference",
    ]
    if not has_trapped:
        missing.append("Confirm whether doors can open or if rescue extrication tools are required.")

    location_guess = "Detected from incident report"
    for line in description.split("."):
        if any(term in line.lower() for term in ["at ", "near ", "interstate", "highway", "street", "avenue", "road", "exit"]):
            location_guess = line.strip()
            break

    dispatch_script = (
        f"EMERGENCY DISPATCH: {severity} - Traffic Collision at {location_guess}. "
        f"{len(vehicles)} vehicle(s)/parties involved. {injuries.status}. "
        f"Hazards: {', '.join(hazards[:2])}. Immediate Police and EMS response required."
    )

    photo_obs = None
    if has_image:
        photo_obs = "Simulated Visual Analysis: Vehicle structural deformation observed. Scene shows road obstruction and visible impact zones."

    return AccidentReport(
        severity_level=severity,
        incident_type="Traffic Collision / Multi-Party Crash",
        location=location_guess,
        vehicles=vehicles,
        injuries=injuries,
        hazards_present=hazards,
        missing_critical_info=missing,
        photo_observations=photo_obs,
        dispatch_script=dispatch_script
    )
