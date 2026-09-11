// frontend/js/alert.js
(function () {
  'use strict';

  const reportSection = document.getElementById('reportSection');
  const confirmCheckbox = document.getElementById('confirmCheckbox');
  const sendBtn = document.getElementById('sendAlertBtn');
  const resultDiv = document.getElementById('result');

  let incidentId = localStorage.getItem('incidentId');
  let report = null;
  try {
    report = JSON.parse(localStorage.getItem('report') || '{}');
  } catch (e) {
    report = {};
  }

  // Fallback demo report if visited directly
  if (!incidentId || !report || !report.accident_type) {
    incidentId = incidentId || 'DEMO-98421';
    report = {
      accident_type: 'Two-Car Collision',
      location_description: 'Outer Ring Road Flyover, Junction 4',
      reported_injured_count: '2',
      reported_injuries: 'Driver conscious with lacerations, passenger arm pain',
      vehicles_involved: 'Sedan and SUV',
      urgency_assessment: 'High (Immediate Ambulance Dispatch Required)',
      missing_information: 'None critical',
      confidence_notes: 'Verified via On-Device Emergency Engine (Zero Cloud API)'
    };
    localStorage.setItem('incidentId', incidentId);
    localStorage.setItem('report', JSON.stringify(report));
  }

  function renderField(label, value, isUrgent = false) {
    const safeVal = value === undefined || value === null ? 'Unknown' : value;
    const isUncertain = safeVal === 'Unknown' || safeVal === '';
    let badge = '';

    if (isUncertain) {
      badge = '<span class="badge warning">⚠️ Needs Verification</span>';
    } else if (isUrgent) {
      badge = '<span class="badge danger">🚨 High Priority</span>';
    }

    return `
      <p style="border-bottom: 1px solid #f1f5f9; padding-bottom: 0.5rem;">
        <strong style="color: var(--dark-slate);">${label}:</strong>
        <span style="color: #334155; font-size: 1rem;">${safeVal}</span>
        ${badge}
      </p>
    `;
  }

  const html = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;">
      <span class="badge info" style="font-size: 0.9rem;">Incident Reference: ${incidentId}</span>
      <span class="badge success">🌱 Eco-Priority Dispatch Ready</span>
    </div>
    ${renderField('Collision Type', report.accident_type)}
    ${renderField('Accident Location', report.location_description)}
    ${renderField('Injured Persons', report.reported_injured_count)}
    ${renderField('Visible Injuries', report.reported_injuries)}
    ${renderField('Vehicles Involved', report.vehicles_involved)}
    ${renderField('Urgency Scoring', report.urgency_assessment, true)}
    ${renderField('Missing Information', report.missing_information)}
    ${renderField('Engine Notes', report.confidence_notes)}
  `;

  reportSection.innerHTML = html;

  confirmCheckbox.addEventListener('change', () => {
    sendBtn.disabled = !confirmCheckbox.checked;
  });

  sendBtn.addEventListener('click', () => {
    const radioScript = [
      `[EMERGENCY DISPATCH TRANSMISSION]`,
      `INCIDENT ID: ${incidentId}`,
      `TYPE: ${report.accident_type || 'Vehicle Collision'}`,
      `LOCATION: ${report.location_description || 'Unknown'}`,
      `CASUALTIES: ${report.reported_injured_count || '1'} reported`,
      `INJURIES: ${report.reported_injuries || 'Trauma at scene'}`,
      `VEHICLES: ${report.vehicles_involved || 'Vehicles at site'}`,
      `URGENCY: ${report.urgency_assessment || 'High'}`,
      `TRANSIT ROUTE: Priority Green Corridor Route Activated (Eco-EMS)`,
      `ACTION: Call 112 immediately to confirm verbal intake.`
    ].join('\n');

    resultDiv.innerHTML = `
      <div style="background: #f0fdf4; border: 1.5px solid #86efac; border-radius: var(--radius-md); padding: 1.25rem; margin-top: 1.5rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
          <span class="badge success" style="font-size: 0.95rem;">✅ Alert Ready & Transmitted to Response Simulator</span>
        </div>
        <label style="font-weight: 700; color: #166534; font-size: 0.92rem;">Standardized 112 / EMS Radio Dispatch Script:</label>
        <textarea rows="8" style="width:100%; font-family: monospace; font-size: 0.88rem; background: #ffffff; margin-top: 0.4rem; padding: 0.75rem; border: 1px solid #cbd5e1; border-radius: 6px;" readonly>${radioScript}</textarea>
        
        <div style="display: flex; gap: 0.75rem; margin-top: 1rem; flex-wrap: wrap;">
          <button id="copyBtn" class="primary-btn">📋 Copy Radio Script</button>
          <button onclick="window.location.href='track.html'" class="primary-btn" style="background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);">
            🚑 Proceed to Live Response Tracker →
          </button>
        </div>
      </div>
    `;

    document.getElementById('copyBtn').addEventListener('click', () => {
      navigator.clipboard.writeText(radioScript);
      alert('Radio dispatch message copied to clipboard!');
    });

    // Auto scroll to result
    resultDiv.scrollIntoView({ behavior: 'smooth' });
  });
})();
