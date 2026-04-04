/**
 * face_monitor.js — Real-time face validation using the webcam.
 * Captures a snapshot every 5 seconds and POSTs it to /api/face/check.
 * Logs alerts and shows toast notifications on violations.
 */

let faceMonitorInterval = null;
let candidateId         = null;
let alertCount          = 0;

/**
 * Entry point — called from verbal.html after page load.
 * @param {number} candidate_id
 */
function initFaceMonitor(candidate_id) {
  candidateId = candidate_id;
  startWebcam();
}

/* ── Webcam Initialisation ───────────────────────────────────────────────── */

async function startWebcam() {
  const video   = document.getElementById('webcam-video');
  const overlay = document.getElementById('webcam-overlay');

  if (!video) return;

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 320, height: 240, facingMode: 'user' },
      audio: false
    });
    video.srcObject = stream;
    video.addEventListener('loadedmetadata', () => {
      if (overlay) overlay.style.display = 'none';
      updateFaceStatus('ok', 'Camera active — monitoring started.');
      // Begin periodic face checks after a short warm-up delay
      setTimeout(() => {
        faceMonitorInterval = setInterval(captureAndCheck, 5000);
      }, 2000);
    });
  } catch (err) {
    console.warn('[FaceMonitor] Camera access denied:', err);
    updateFaceStatus('error', 'Camera access denied — proctoring disabled.');
    if (overlay) {
      overlay.innerHTML = '<span style="font-size:2rem">📷❌</span><p>Camera access denied</p>';
    }
  }
}

/* ── Capture & Check ─────────────────────────────────────────────────────── */

function captureAndCheck() {
  const video  = document.getElementById('webcam-video');
  const canvas = document.getElementById('webcam-canvas');
  if (!video || !canvas || video.readyState < 2) return;

  // Draw current video frame to canvas
  canvas.width  = 320;
  canvas.height = 240;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, 320, 240);

  // Convert to base64 JPEG (lower quality = smaller payload)
  const imageB64 = canvas.toDataURL('image/jpeg', 0.6);

  fetch('/api/face/check', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ candidate_id: candidateId, image_b64: imageB64 })
  })
  .then(r => r.json())
  .then(data => handleFaceResult(data))
  .catch(err => console.warn('[FaceMonitor] Check error:', err));
}

/* ── Handle Result ───────────────────────────────────────────────────────── */

function handleFaceResult(data) {
  const { status, message } = data;

  switch (status) {
    case 'ok':
      updateFaceStatus('ok', '✅ Face detected');
      break;

    case 'no_face':
      alertCount++;
      updateFaceStatus('warning', '⚠️ No face detected!');
      showFaceAlert('warning', '⚠️ No face detected — please ensure your face is clearly visible.');
      logAlert('no_face');
      break;

    case 'multiple_faces':
      alertCount++;
      updateFaceStatus('danger', '🚫 Multiple faces detected!');
      showFaceAlert('danger', '🚫 Multiple faces detected — only you should be in frame!');
      logAlert('multiple_faces');
      break;

    case 'error':
      console.warn('[FaceMonitor] Server error:', message);
      break;

    default:
      break;
  }
}

/* ── UI Helpers ──────────────────────────────────────────────────────────── */

function updateFaceStatus(type, message) {
  const icon = document.getElementById('face-icon');
  const text = document.getElementById('face-status-text');
  if (!icon || !text) return;

  const iconMap = { ok: '✅', warning: '⚠️', danger: '🚫', error: '❌' };
  icon.textContent = iconMap[type] || '⏳';
  text.textContent = message;
}

function showFaceAlert(type, message) {
  // Create a floating toast notification
  const toast = document.createElement('div');
  toast.style.cssText = `
    position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
    background: ${type === 'danger' ? 'rgba(239,68,68,0.95)' : 'rgba(245,158,11,0.95)'};
    color: #fff; padding: 14px 24px; border-radius: 12px;
    font-family: Inter, sans-serif; font-size: 0.9rem; font-weight: 600;
    z-index: 9999; box-shadow: 0 8px 30px rgba(0,0,0,0.4);
    animation: fadeInUp 0.3s ease; max-width: 460px; text-align: center;
  `;
  toast.textContent = message;
  document.body.appendChild(toast);

  // Auto-remove after 4 seconds
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function logAlert(type) {
  const entries = document.getElementById('alert-entries');
  if (!entries) return;

  const now   = new Date().toLocaleTimeString();
  const entry = document.createElement('div');
  entry.className = `alert-entry alert-entry--${type === 'no_face' ? 'warning' : 'danger'}`;
  entry.innerHTML = `
    <span>${type === 'no_face' ? '👤' : '🚫'}</span>
    <span>${type.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}</span>
    <span style="margin-left:auto;opacity:0.7;font-size:0.7rem">${now}</span>
  `;
  entries.prepend(entry);

  // Keep only the last 5 entries visible
  const allEntries = entries.querySelectorAll('.alert-entry');
  if (allEntries.length > 5) allEntries[allEntries.length - 1].remove();
}

/* ── Cleanup ─────────────────────────────────────────────────────────────── */

function stopFaceMonitor() {
  if (faceMonitorInterval) {
    clearInterval(faceMonitorInterval);
    faceMonitorInterval = null;
  }
  const video = document.getElementById('webcam-video');
  if (video && video.srcObject) {
    video.srcObject.getTracks().forEach(t => t.stop());
  }
}
