"""
RoadSafe AI - MVP Traffic Incident Dispatch Assistant
Built for PromptWars × Techverse Hackathon
Stack: Python, Streamlit, Google Gemini
"""

import os
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

from gemini_extractor import extract_accident_report, get_simulated_report, AccidentReport

# Page configuration
st.set_page_config(
    page_title="RoadSafe AI - Emergency Accident Intake",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for Emergency Theme
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.2rem;
    }
    .emergency-banner {
        background-color: #FEF2F2;
        border-left: 5px solid #DC2626;
        padding: 0.85rem 1.1rem;
        border-radius: 6px;
        color: #991B1B;
        font-weight: 600;
        margin-bottom: 1.5rem;
    }
    .badge-critical {
        background-color: #DC2626;
        color: white;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        display: inline-block;
    }
    .badge-high {
        background-color: #EA580C;
        color: white;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        display: inline-block;
    }
    .badge-moderate {
        background-color: #CA8A04;
        color: white;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        display: inline-block;
    }
    .badge-minor {
        background-color: #16A34A;
        color: white;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        display: inline-block;
    }
    .info-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Demo Scenarios for fast hackathon judging / testing
DEMO_SCENARIOS = {
    "Select a quick demo scenario...": "",
    "💥 Multi-Car Highway Crash (I-95)": (
        "Multi-car crash on Interstate 95 South near Exit 42. A blue Ford F-150 rear-ended "
        "a silver Honda Civic, spinning into a delivery truck. The front of the Civic is badly smashed; "
        "the driver is bleeding from their forehead and seems disoriented. The truck is leaking fuel "
        "across the two right lanes. Traffic is backing up fast and it's starting to rain."
    ),
    "🚦 Downtown Intersection T-Bone": (
        "Two cars collided at the corner of 5th Avenue and Elm Street. A black sedan ran a red light "
        "and T-boned a red hatchback. Both airbags deployed. The passenger in the red car is clutching "
        "their collarbone and crying in pain. Neither car is on fire, but the intersection is blocked."
    ),
    "🏍️ Motorcycle & Pedestrian Collision": (
        "A motorcycle struck an elderly pedestrian crossing Main Street near the Maple Ave crosswalk. "
        "The pedestrian is lying on the pavement, conscious but in severe leg pain. The motorcyclist "
        "slid into a parked white delivery van and is awake with abrasions. Oil is leaking from the bike."
    ),
}

# --- Sidebar: Configuration & Scenarios ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=64)
    st.title("RoadSafe AI 🛡️")
    st.caption("PromptWars × Techverse Hackathon MVP")
    st.markdown("---")

    st.subheader("🔑 Gemini API Setup")
    env_key = os.getenv("GEMINI_API_KEY", "")
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=env_key,
        type="password",
        help="Enter your Gemini API key from https://aistudio.google.com/app/apikey or set GEMINI_API_KEY in .env",
    )

    demo_mode = st.checkbox(
        "🧪 Offline Demo Mode (No API key needed)",
        value=True,
        help="Enable to test the full UI and dispatch generation without a Gemini API key.",
    )

    if api_key_input:
        st.success("API Key detected ✅")
    else:
        st.info("Offline Demo Mode Active 🧪 (Zero API key required)")

    st.markdown("---")
    st.subheader("⚡ Quick Demo Presets")
    selected_scenario = st.selectbox(
        "Load test scenario into prompt:",
        options=list(DEMO_SCENARIOS.keys()),
        index=0,
    )

    st.markdown("---")
    st.subheader("⚙️ Model Settings")
    model_choice = st.selectbox(
        "Gemini Model",
        options=["gemini-2.5-flash", "gemini-1.5-flash"],
        index=0,
        help="Gemini 2.5 Flash is recommended for fast multimodal extraction.",
    )

    st.caption("Made with Streamlit & Google Gemini")

# --- Main Page Header ---
st.markdown('<div class="main-title">RoadSafe AI 🚨</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">AI-assisted accident intake: extracts vital parameters, flags hazards & missing info, and prepares instant dispatch reports.</div>',
    unsafe_allow_html=True,
)

# Emergency Warning Banner
st.markdown(
    """
    <div class="emergency-banner">
        ⚠️ <strong>CRITICAL NOTICE:</strong> If this is an active life-threatening emergency, call <strong>911 / 112</strong> immediately. Do not delay emergency calls for AI processing.
    </div>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "accident_report" not in st.session_state:
    st.session_state.accident_report = None
if "report_confirmed" not in st.session_state:
    st.session_state.report_confirmed = False

# Populate text area with preset if chosen
default_text = ""
if selected_scenario and selected_scenario != "Select a quick demo scenario...":
    default_text = DEMO_SCENARIOS[selected_scenario]

# --- Section 1: Accident Input ---
st.subheader("1. Incident Intake")

col_text, col_photo = st.columns([1.6, 1.0], gap="medium")

with col_text:
    accident_description = st.text_area(
        "Describe the accident in your own words:",
        value=default_text,
        placeholder="e.g., Two cars collided at the corner of 4th and Pine. A silver sedan hit a black SUV. One driver is complaining of neck pain, and fluid is leaking from the sedan...",
        height=180,
    )
    st.caption("💡 Mention landmarks, cross streets, visible injuries, car types/colors, and any smoke or fuel.")

with col_photo:
    uploaded_photo = st.file_uploader(
        "Upload Crash Photo (Optional)",
        type=["jpg", "jpeg", "png"],
        help="Gemini will analyze the image for vehicle damage, license plates, hazards, and scene conditions.",
    )
    pil_image = None
    if uploaded_photo is not None:
        try:
            pil_image = Image.open(uploaded_photo)
            st.image(pil_image, caption="Uploaded Crash Photo", use_container_width=True)
        except Exception as img_err:
            st.error(f"Could not load image: {img_err}")

# Action Button
analyze_button = st.button("🚀 Analyze Accident & Generate Emergency Report", type="primary", use_container_width=True)

# Processing Logic
if analyze_button:
    if not api_key_input and not demo_mode:
        st.error("❌ Gemini API Key is required. Enter your key in the sidebar, or check 'Offline Demo Mode' to test right away.")
    elif not accident_description or len(accident_description.strip()) < 10:
        st.error("❌ Please provide a descriptive accident report (at least 10 characters).")
    else:
        with st.spinner("Analyzing incident description and photo..."):
            try:
                if api_key_input:
                    report = extract_accident_report(
                        description=accident_description,
                        api_key=api_key_input,
                        image=pil_image,
                        model_name=model_choice,
                    )
                    st.success("Accident analysis complete via Google Gemini! Review the structured report below.")
                else:
                    report = get_simulated_report(
                        description=accident_description,
                        has_image=(pil_image is not None),
                    )
                    st.info("Accident analysis generated in Offline Demo Mode. Add your Gemini API key for live AI extraction.")

                st.session_state.accident_report = report
                st.session_state.report_confirmed = False
            except Exception as e:
                st.error(f"Extraction failed: {str(e)}")

# --- Section 2 & 3: Structured Report Display ---
report: AccidentReport = st.session_state.accident_report

if report is not None:
    st.markdown("---")
    st.subheader("2. Structured Emergency Report")

    # Severity Banner & Key Metrics
    severity = report.severity_level.upper()
    badge_class = {
        "CRITICAL": "badge-critical",
        "HIGH": "badge-high",
        "MODERATE": "badge-moderate",
        "MINOR": "badge-minor",
    }.get(severity, "badge-moderate")

    col_sev, col_type = st.columns([1, 2])
    with col_sev:
        st.markdown(f"**Severity Level:** <span class='{badge_class}'>{severity}</span>", unsafe_allow_html=True)
    with col_type:
        st.markdown(f"**Incident Type:** `{report.incident_type}`")

    st.markdown("<br>", unsafe_allow_html=True)

    # Top Key Metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("📍 Location", report.location if len(report.location) < 30 else report.location[:27] + "...")
    with m2:
        st.metric("🚗 Vehicles", len(report.vehicles))
    with m3:
        st.metric("🩺 Injuries", report.injuries.count_estimate)
    with m4:
        st.metric("⚠️ Trapped Persons", "YES 🚨" if report.injuries.trapped_persons else "None reported")

    # Tabs for detailed breakdown
    tab_overview, tab_vehicles, tab_injuries, tab_hazards, tab_missing = st.tabs([
        "📋 Overview & Location",
        "🚗 Vehicles Involved",
        "🩺 Medical & Injuries",
        "⚠️ Hazards & Scene",
        "❓ Missing Critical Info",
    ])

    with tab_overview:
        st.markdown(f"**Exact / Detected Location:** `{report.location}`")
        if report.photo_observations:
            st.info(f"📸 **Photo Observations:** {report.photo_observations}")
        st.markdown(f"**Severity Rationale:** `{report.severity_level}` urgency based on reported damage, injuries, and road state.")

    with tab_vehicles:
        if report.vehicles:
            for idx, v in enumerate(report.vehicles, 1):
                with st.container():
                    st.markdown(f"**Vehicle #{idx}: {v.color} {v.vehicle_type}**")
                    if v.details:
                        st.caption(f"Details/Damage: {v.details}")
        else:
            st.write("No specific vehicles identified.")

    with tab_injuries:
        st.markdown(f"**Status Summary:** {report.injuries.status}")
        st.markdown(f"**Estimated Casualties:** {report.injuries.count_estimate}")
        st.markdown(f"**Severity Classification:** `{report.injuries.severity}`")
        if report.injuries.trapped_persons:
            st.error("🚨 **CRITICAL ALERT:** Occupants are reported trapped. Immediate extrication / rescue equipment needed!")
        else:
            st.info("No trapped occupants reported.")

    with tab_hazards:
        if report.hazards_present:
            for hazard in report.hazards_present:
                st.warning(f"⚠️ {hazard}")
        else:
            st.success("No active hazards (fire, fuel spill, downed power lines) detected.")

    with tab_missing:
        st.markdown("**Dispatchers need answers to these critical questions:**")
        if report.missing_critical_info:
            for item in report.missing_critical_info:
                st.markdown(f"- ❓ **{item}**")
        else:
            st.write("All standard emergency parameters were captured.")

    # --- Section 3: Confirm & Share Dispatch Script ---
    st.markdown("---")
    st.subheader("3. Emergency Dispatch Message")
    st.markdown(
        "Copy and transmit this standardized message to emergency dispatchers, police, or roadside assistance:"
    )

    # Standardized Dispatch Block
    st.code(report.dispatch_script, language="text")

    # Confirmation checkbox
    confirm_col, copy_col = st.columns([2, 1])
    with confirm_col:
        is_confirmed = st.checkbox(
            "✅ I confirm this summary accurately reflects the incident details.",
            value=st.session_state.report_confirmed,
        )
        st.session_state.report_confirmed = is_confirmed

    # Generate full report text for download
    full_report_text = f"""==================================================
ROADSAFE AI - EMERGENCY INCIDENT DISPATCH REPORT
==================================================
Severity:       {report.severity_level}
Incident Type:  {report.incident_type}
Location:       {report.location}
Vehicles Count: {len(report.vehicles)}
Injuries:       {report.injuries.status} (Count: {report.injuries.count_estimate}, Trapped: {report.injuries.trapped_persons})
Hazards:        {', '.join(report.hazards_present) if report.hazards_present else 'None'}

DISPATCH SCRIPT:
{report.dispatch_script}

MISSING CRITICAL DETAILS TO CONFIRM:
{chr(10).join(['- ' + m for m in report.missing_critical_info])}

PHOTO OBSERVATIONS:
{report.photo_observations or 'No photo provided'}
==================================================
"""
    st.download_button(
        label="📥 Download Full Incident Report (.txt)",
        data=full_report_text,
        file_name="RoadSafe_Emergency_Report.txt",
        mime="text/plain",
        disabled=not is_confirmed,
        help="Confirm the report above to enable download.",
    )

    if is_confirmed:
        st.success("Report confirmed! You can now copy the dispatch script above or download the file.")
