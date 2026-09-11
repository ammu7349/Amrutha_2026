// backend/app.js (updated to use native fetch with intelligent offline fallback, Node 18+)
const express = require('express');
const path = require('path');
const multer = require('multer');
const { v4: uuidv4 } = require('uuid');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Serve static frontend files
app.use(express.static(path.join(__dirname, '..', 'frontend')));

// In-memory store for incidents (demo only)
const incidents = {};

// Multer for file uploads (photos/audio)
const upload = multer({ storage: multer.memoryStorage() });

// Offline analyzer function - Zero API key required
function analyzeReportOffline(body) {
  const description = body.description || '';
  const injuredCount = parseInt(body.injuredCount, 10) || 0;
  const injuryDetails = body.injuryDetails || '';
  const vehicles = body.vehicles || '';
  const manualLocation = body.manualLocation || '';

  // Heuristic urgency assessment
  let urgency = 'Moderate (Assistance Required)';
  const textCombo = (description + ' ' + injuryDetails).toLowerCase();
  if (injuredCount >= 2 || /severe|unconscious|head|bleeding|blood|critical|heavy|crush|trauma/i.test(textCombo)) {
    urgency = 'Critical (Immediate Ambulance Dispatch Required)';
  } else if (injuredCount > 0 || /fracture|broken|pain|hit|cut|injury/i.test(textCombo)) {
    urgency = 'High (Ambulance Response Required)';
  }

  // Accident type classifier
  let accidentType = 'Vehicle Collision';
  if (/pedestrian|hit person|crossing|walking/i.test(textCombo)) {
    accidentType = 'Pedestrian Collision';
  } else if (/motorcycle|bike|scooter|two-wheeler|two wheeler/i.test(textCombo + ' ' + vehicles.toLowerCase())) {
    accidentType = 'Two-Wheeler Accident';
  } else if (/truck|bus|lorry|heavy/i.test(textCombo + ' ' + vehicles.toLowerCase())) {
    accidentType = 'Heavy Transport Collision';
  } else if (/rollover|overturned|skidded|tree|pole|divider/i.test(textCombo)) {
    accidentType = 'Single-Vehicle Crash / Rollover';
  }

  return {
    accident_type: accidentType,
    location_description: manualLocation || (description.length > 60 ? description.substring(0, 60) + '...' : (description || 'Incident Site')),
    reported_injured_count: injuredCount > 0 ? String(injuredCount) : 'None reported',
    reported_injuries: injuryDetails || (injuredCount > 0 ? 'Injuries reported by bystander' : 'No visible severe injuries reported'),
    vehicles_involved: vehicles || 'Reported vehicle(s) on scene',
    missing_information: (!injuryDetails && injuredCount > 0) ? 'Specific injury symptoms' : 'None critical',
    urgency_assessment: urgency,
    confidence_notes: 'Analyzed via Offline Smart Emergency Engine (Zero API Key required)'
  };
}

// Helper to call Gemini API if key is available
async function callGemini(payload) {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) return null;
  const response = await fetch('https://generativeai.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = await response.text();
    console.warn(`Gemini error: ${response.status} ${err}. Using offline parser.`);
    return null;
  }
  return await response.json();
}

// Endpoint: Receive accident report, analyze (online Gemini or offline engine), return structured JSON
app.post('/api/report', upload.single('photo'), async (req, res) => {
  try {
    const { description, latitude, longitude, injuredCount, injuryDetails, vehicles } = req.body;
    let structured = null;

    // Try Gemini if API key is configured
    if (process.env.GEMINI_API_KEY) {
      try {
        const parts = [];
        if (description) parts.push({ text: description });
        if (req.file) {
          const base64 = req.file.buffer.toString('base64');
          const mime = req.file.mimetype;
          parts.push({ inlineData: { mimeType: mime, data: base64 } });
        }
        const systemInstruction = `You are a helpful assistant extracting emergency-report data. Return a JSON object with the following keys exactly: accident_type, location_description, reported_injured_count, reported_injuries, vehicles_involved, missing_information, urgency_assessment, confidence_notes. Use "Unknown" for any unknown field. Do NOT invent data. Provide concise values.`;
        const payload = {
          contents: [{ role: 'user', parts }],
          generationConfig: { temperature: 0.2 },
          systemInstruction: { role: 'system', parts: [{ text: systemInstruction }] },
        };
        const geminiResult = await callGemini(payload);
        const candidate = geminiResult?.candidates?.[0];
        let jsonText = candidate?.content?.parts?.[0]?.text?.trim() || '';
        jsonText = jsonText.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '').trim();
        if (jsonText) {
          structured = JSON.parse(jsonText);
        }
      } catch (geminiErr) {
        console.warn('Gemini API call failed, falling back to local extractor:', geminiErr.message);
      }
    }

    // Offline fallback: zero API key needed
    if (!structured || structured.error) {
      structured = analyzeReportOffline(req.body);
    }

    structured.location_coordinates = {
      latitude: parseFloat(latitude) || 12.9716,
      longitude: parseFloat(longitude) || 77.5946
    };

    const incidentId = uuidv4();
    incidents[incidentId] = {
      ...structured,
      status: 'Alert Submitted',
      createdAt: new Date().toISOString()
    };

    res.json({ incidentId, report: structured });
  } catch (err) {
    console.error('Error handling /api/report:', err);
    res.status(500).json({ error: err.message });
  }
});

// Get current incident status
app.get('/api/status/:id', (req, res) => {
  const incident = incidents[req.params.id];
  if (!incident) return res.status(404).json({ error: 'Incident not found' });
  res.json(incident);
});

// Advance simulated status (demo control)
const statusFlow = [
  'Alert Submitted',
  'Emergency Service Notified',
  'Ambulance Assigned',
  'Ambulance is on the way',
  'Arrived at Incident',
  'Patient Transported',
];

app.post('/api/simulate/advance/:id', (req, res) => {
  const incident = incidents[req.params.id];
  if (!incident) return res.status(404).json({ error: 'Incident not found' });
  const idx = statusFlow.findIndex(s => s.toLowerCase() === (incident.status || '').toLowerCase());
  if (idx !== -1 && idx < statusFlow.length - 1) {
    incident.status = statusFlow[idx + 1];
    incident.updatedAt = new Date().toISOString();
  }
  res.json({ status: incident.status });
});

app.listen(PORT, () => {
  console.log(`Backend listening on http://localhost:${PORT}`);
});
