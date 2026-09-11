# 🛡️ RoadSafe AI - MVP

An AI-powered emergency intake, navigation, and live dispatch tracker for traffic accidents, built for the **PromptWars × Techverse** hackathon.

RoadSafe AI acts as a bridge between an eyewitness reporting an accident and appropriate emergency response teams. It converts unstructured, panicked eyewitness descriptions into a structured emergency report, identifies nearby medical services, and simulates real-time response dispatch tracking.

---

## 🌟 The 4 Core Web Workflows

1. **🚨 Report Accident (`/index.html`)**:
   - Eyewitness input form with text description, GPS / manual location capture, injured count, injuries, and vehicle details.
   - Intelligent Emergency Engine structures messy real-world inputs into verified dispatch data.
   - **Zero API Key required** (smart built-in offline engine, with optional Gemini support).

2. **🏥 Nearby Help (`/help.html`)**:
   - Interactive Leaflet map displaying the exact incident location marker.
   - Discovers nearby trauma centers and hospitals with distance calculations and instant Google Maps directions.

3. **📢 Emergency Alert (`/alert.html`)**:
   - Structured review of accident type, vehicles, urgency assessment, and confidence notes.
   - Emergency dispatch message generation with one-click copy and quick dial to emergency services (112).

4. **🚑 Track Response (`/track.html`)**:
   - Real-time simulation of the 6 response stages:
     1. Alert Submitted
     2. Emergency Service Notified
     3. Ambulance Assigned
     4. **Ambulance is on the way** (prominent active alert)
     5. Arrived at Incident
     6. Patient Transported
   - Interactive map featuring simulated moving ambulance markers and live stage advancement.

---

## 🚀 Quickstart Guide (Web Application)

### 1. Prerequisites
- [Node.js](https://nodejs.org/) (version 18 or higher)

### 2. Navigate to Backend & Install Dependencies
```powershell
cd backend
npm install
```

### 3. Start the Server
```powershell
npm start
```
The server will start at **`http://localhost:3000`**.

### 4. Open in Browser
- **Home / Report Accident**: [http://localhost:3000/index.html](http://localhost:3000/index.html)
- **Nearby Help**: [http://localhost:3000/help.html](http://localhost:3000/help.html)
- **Emergency Alert**: [http://localhost:3000/alert.html](http://localhost:3000/alert.html)
- **Track Response**: [http://localhost:3000/track.html](http://localhost:3000/track.html)

---

## 📁 Project Structure

```text
roadsafe-ai/
├── backend/
│   ├── app.js               # Express API server with smart offline analyzer & static server
│   └── package.json         # Node.js dependencies (express, multer, uuid)
├── frontend/
│   ├── index.html           # 1. Report Accident page
│   ├── help.html            # 2. Nearby Emergency Services & Hospital locator
│   ├── alert.html           # 3. Emergency Alert review & dispatch card
│   ├── track.html           # 4. Live Response Tracker & Timeline simulation
│   ├── css/
│   │   └── styles.css       # Unified emergency theme styling
│   └── js/
│       ├── report.js        # Geolocation, voice & form handling
│       ├── help.js          # Leaflet map & hospital queries
│       ├── alert.js         # Report review & copy dispatch script
│       └── track.js         # Response timeline & ambulance simulation
├── app.py                   # Streamlit interactive evaluation UI
├── gemini_extractor.py      # Multimodal Gemini extraction schema
├── requirements.txt         # Python dependencies
├── .gitignore               # Excludes node_modules, .env, and caches
└── README.md                # Project documentation
```

---

## 🧪 Zero API Key Offline Mode
RoadSafe AI is designed to run seamlessly offline or in air-gapped demo environments. If no Google Gemini API key is provided, the system automatically uses its built-in rule-based emergency classification engine to score urgency and extract incident metadata.

---

## ⚠️ Demo Disclaimer
RoadSafe AI is a prototype created for educational and hackathon demonstration purposes. No actual ambulances or emergency dispatchers are contacted. In a real medical emergency, always dial **112** (India) or **911** (US) immediately.
