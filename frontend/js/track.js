// frontend/js/track.js
(function () {
  'use strict';

  // 1. Defined stages exactly matching the requirement
  const STAGES = [
    'Alert Submitted',
    'Emergency Service Notified',
    'Ambulance Assigned',
    'Ambulance is on the way',
    'Arrived at Incident',
    'Patient Transported'
  ];

  // 2. Retrieve persisted information from localStorage
  let incidentId = localStorage.getItem('incidentId');
  let report = null;
  try {
    report = JSON.parse(localStorage.getItem('report') || '{}');
  } catch (e) {
    report = {};
  }

  // Fallback demo incident if none exists in localStorage
  if (!incidentId) {
    incidentId = 'DEMO-' + Math.floor(100000 + Math.random() * 900000);
    localStorage.setItem('incidentId', incidentId);
  }

  // Determine Location
  let locationText = '';
  if (report && report.location_description && report.location_description !== 'Unknown') {
    locationText = report.location_description;
  }
  let lat = report && report.location_coordinates ? report.location_coordinates.latitude : null;
  let lng = report && report.location_coordinates ? report.location_coordinates.longitude : null;

  if (lat && lng && !isNaN(lat) && !isNaN(lng)) {
    locationText = locationText ? `${locationText} (${lat.toFixed(4)}, ${lng.toFixed(4)})` : `Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}`;
  } else {
    // Default fallback coordinates (e.g. Bangalore / Central hub)
    lat = 12.9716;
    lng = 77.5946;
    if (!locationText) {
      locationText = `MG Road Intersection (Lat: ${lat}, Lng: ${lng})`;
    }
  }

  // Determine Selected Emergency Service
  const storedService = localStorage.getItem('selectedService') || (report && report.selectedService);
  const emergencyServiceText = storedService || 'National Emergency Medical Service (112) / Trauma Care Ambulance';

  // Current status index
  let savedStatus = localStorage.getItem('demoStatus') || 'Alert Submitted';
  let currentStageIndex = STAGES.findIndex(s => s.toLowerCase() === savedStatus.toLowerCase());
  if (currentStageIndex === -1) currentStageIndex = 0;

  // DOM Elements
  const incidentIdEl = document.getElementById('incidentId');
  const accidentLocationEl = document.getElementById('accidentLocation');
  const emergencyServiceEl = document.getElementById('emergencyService');
  const currentStatusEl = document.getElementById('currentStatus');
  const ambulanceBanner = document.getElementById('ambulanceBanner');
  const timelineList = document.getElementById('timelineList');
  const advanceBtn = document.getElementById('advanceBtn');
  const resetBtn = document.getElementById('resetBtn');

  // Populate static fields
  incidentIdEl.textContent = incidentId;
  accidentLocationEl.textContent = locationText;
  emergencyServiceEl.textContent = emergencyServiceText;

  // Initialize Leaflet Map
  let map, incidentMarker, ambulanceMarker;
  try {
    const mapDiv = document.getElementById('map');
    if (mapDiv && typeof L !== 'undefined') {
      map = L.map('map').setView([lat, lng], 14);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
      }).addTo(map);

      incidentMarker = L.marker([lat, lng])
        .addTo(map)
        .bindPopup(`<strong>Accident Location</strong><br>${locationText}`)
        .openPopup();
    }
  } catch (err) {
    console.warn('Map initialization note:', err);
  }

  // Update Ambulance Marker on map based on status
  function updateAmbulanceOnMap(stageIndex) {
    if (!map || typeof L === 'undefined') return;

    // Show ambulance marker for stages: Assigned, On the way, Arrived, Transported
    if (stageIndex >= 2) {
      // Calculate simulated ambulance position relative to incident
      let offsetLat = 0;
      let offsetLng = 0;

      if (stageIndex === 2) { // Assigned (at base hospital ~2km away)
        offsetLat = 0.012;
        offsetLng = 0.010;
      } else if (stageIndex === 3) { // Ambulance is on the way (~500m away)
        offsetLat = 0.0035;
        offsetLng = 0.0030;
      } else if (stageIndex === 4) { // Arrived at Incident
        offsetLat = 0.0002;
        offsetLng = 0.0002;
      } else if (stageIndex === 5) { // Patient Transported (moving toward hospital)
        offsetLat = -0.008;
        offsetLng = -0.008;
      }

      const ambCoords = [lat + offsetLat, lng + offsetLng];
      const ambIcon = L.divIcon({
        className: 'custom-amb-icon',
        html: '<div style="font-size: 26px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.4));">🚑</div>',
        iconSize: [30, 30],
        iconAnchor: [15, 15]
      });

      if (!ambulanceMarker) {
        ambulanceMarker = L.marker(ambCoords, { icon: ambIcon })
          .addTo(map)
          .bindPopup('<strong>Simulated Ambulance</strong><br>In response to Incident ' + incidentId);
      } else {
        ambulanceMarker.setLatLng(ambCoords);
      }

      if (stageIndex === 3) {
        ambulanceMarker.openPopup();
      }
    } else {
      if (ambulanceMarker) {
        map.removeLayer(ambulanceMarker);
        ambulanceMarker = null;
      }
    }
  }

  // Render Timeline and Status UI
  function renderUI() {
    const currentStage = STAGES[currentStageIndex];
    localStorage.setItem('demoStatus', currentStage);

    // Update status badge
    currentStatusEl.textContent = currentStage;
    if (currentStage === 'Ambulance is on the way') {
      currentStatusEl.className = 'badge warning';
    } else if (currentStageIndex === STAGES.length - 1) {
      currentStatusEl.className = 'badge success';
    } else {
      currentStatusEl.className = 'badge info';
    }

    // Toggle prominent "Ambulance is on the way" banner
    if (currentStage === 'Ambulance is on the way') {
      ambulanceBanner.style.display = 'flex';
    } else {
      ambulanceBanner.style.display = 'none';
    }

    // Update timeline items
    timelineList.innerHTML = '';
    STAGES.forEach((stage, idx) => {
      const li = document.createElement('li');
      li.className = 'timeline-item';

      const isCompleted = idx < currentStageIndex;
      const isActive = idx === currentStageIndex;
      const isAmbulanceStage = stage === 'Ambulance is on the way';

      if (isCompleted) {
        li.classList.add('completed');
      } else if (isActive) {
        li.classList.add('active');
      }

      if (isAmbulanceStage && (isActive || isCompleted)) {
        li.classList.add('highlight-stage');
      }

      const icon = document.createElement('span');
      icon.className = 'timeline-icon';
      icon.textContent = isCompleted ? '✓' : (idx + 1);

      const text = document.createElement('span');
      text.className = 'timeline-text';
      text.textContent = stage;

      if (isAmbulanceStage && isActive) {
        text.innerHTML = `<strong>${stage}</strong> <span class="badge warning" style="margin-left: 8px;">Active Stage</span>`;
      }

      li.appendChild(icon);
      li.appendChild(text);
      timelineList.appendChild(li);
    });

    // Update Map
    updateAmbulanceOnMap(currentStageIndex);

    // Button states
    if (currentStageIndex >= STAGES.length - 1) {
      advanceBtn.textContent = 'All Stages Completed (Demo)';
      advanceBtn.disabled = true;
    } else {
      advanceBtn.disabled = false;
      const nextStage = STAGES[currentStageIndex + 1];
      advanceBtn.textContent = `Advance Demo Status → ${nextStage}`;
    }
  }

  // Advance Demo Status Button Handler
  advanceBtn.addEventListener('click', async () => {
    if (currentStageIndex < STAGES.length - 1) {
      currentStageIndex++;
      renderUI();

      // Attempt to sync with backend if running
      try {
        await fetch(`/api/simulate/advance/${incidentId}`, { method: 'POST' });
      } catch (e) {
        // Backend failure is non-blocking for demo presentation
      }
    }
  });

  // Reset Demo Status Button Handler
  resetBtn.addEventListener('click', () => {
    currentStageIndex = 0;
    renderUI();
  });

  // Initial Render
  renderUI();

})();
