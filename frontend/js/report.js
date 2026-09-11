// frontend/js/report.js
(function () {
  const form = document.getElementById('reportForm');
  const photoInput = document.getElementById('photo');
  const photoPreview = document.getElementById('photoPreview');
  const geoBtn = document.getElementById('geoBtn');
  const latitudeInput = document.getElementById('latitude');
  const longitudeInput = document.getElementById('longitude');
  const voiceBtn = document.getElementById('voiceBtn');
  const voiceStatus = document.getElementById('voiceStatus');
  const loading = document.getElementById('loading');

  // Photo preview
  photoInput.addEventListener('change', () => {
    const file = photoInput.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      photoPreview.src = url;
      photoPreview.style.display = 'block';
    } else {
      photoPreview.style.display = 'none';
    }
  });

  // Geolocation
  geoBtn.addEventListener('click', () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser');
      return;
    }
    geoBtn.disabled = true;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        latitudeInput.value = latitude;
        longitudeInput.value = longitude;
        geoBtn.textContent = 'Location captured';
      },
      (err) => {
        alert('Unable to retrieve location: ' + err.message);
        geoBtn.disabled = false;
      }
    );
  });

  // Voice capture (simple MediaRecorder, stores as audio/webm)
  let mediaRecorder;
  let audioChunks = [];
  voiceBtn.addEventListener('click', async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert('Audio capture not supported');
      return;
    }
    if (voiceBtn.dataset.recording === 'true') {
      // stop recording
      mediaRecorder.stop();
      voiceBtn.textContent = 'Capture Voice (optional)';
      voiceBtn.dataset.recording = 'false';
      return;
    }
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];
    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
    mediaRecorder.onstop = () => {
      const blob = new Blob(audioChunks, { type: 'audio/webm' });
      // Attach to form via a hidden File input created on the fly
      const audioFile = new File([blob], 'voice.webm', { type: 'audio/webm' });
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(audioFile);
      const hiddenInput = document.createElement('input');
      hiddenInput.type = 'file';
      hiddenInput.name = 'audio';
      hiddenInput.files = dataTransfer.files;
      hiddenInput.style.display = 'none';
      form.appendChild(hiddenInput);
      voiceStatus.textContent = 'Voice captured';
    };
    mediaRecorder.start();
    voiceBtn.textContent = 'Stop Recording';
    voiceBtn.dataset.recording = 'true';
  });

  // Form submit
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    loading.style.display = 'block';
    const formData = new FormData(form);
    // Attach extra fields if missing
    if (!formData.get('latitude') || !formData.get('longitude')) {
      alert('Please capture or enter location');
      loading.style.display = 'none';
      return;
    }
    try {
      const resp = await fetch('/api/report', {
        method: 'POST',
        body: formData,
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || 'Server error');
      // Store for later pages
      localStorage.setItem('incidentId', data.incidentId);
      localStorage.setItem('report', JSON.stringify(data.report));
      // Redirect to nearby help page
      window.location.href = 'help.html';
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      loading.style.display = 'none';
    }
  });
})();
