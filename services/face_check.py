"""
services/face_check.py — Real-time face validation using OpenCV Haar Cascade.
Accepts a base64-encoded JPEG image and returns a status dict.
"""
import base64
import io
import numpy as np
import cv2
from PIL import Image

# ── Load Haar Cascade (bundled with OpenCV — no extra download needed) ─────────
_face_cascade = None


def _get_cascade():
    """Load the face cascade classifier (lazy singleton)."""
    global _face_cascade
    if _face_cascade is None:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        _face_cascade = cv2.CascadeClassifier(cascade_path)
        if _face_cascade.empty():
            raise RuntimeError("Failed to load Haar Cascade. OpenCV may be corrupted.")
    return _face_cascade


def check_face(image_b64: str) -> dict:
    """
    Detect faces in a base64-encoded image.

    Args:
        image_b64: Base64 string of a JPEG/PNG webcam snapshot.
                   Leading 'data:image/...;base64,' prefix is stripped automatically.

    Returns:
        dict with keys:
          - status:  'ok' | 'no_face' | 'multiple_faces' | 'error'
          - faces:   int — number of faces detected
          - message: str — human-readable description
    """
    try:
        # ── Strip data-URL prefix if present ──────────────────────────────
        if ',' in image_b64:
            image_b64 = image_b64.split(',', 1)[1]

        # ── Decode base64 → PIL Image → NumPy array ───────────────────────
        image_bytes = base64.b64decode(image_b64)
        pil_image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        frame = np.array(pil_image)

        # ── Convert to grayscale for Haar Cascade ─────────────────────────
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

        # ── Detect faces ───────────────────────────────────────────────────
        cascade = _get_cascade()
        faces = cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60),   # Ignore very small detections
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        face_count = len(faces) if isinstance(faces, np.ndarray) else 0

        # ── Return result ──────────────────────────────────────────────────
        if face_count == 0:
            return {
                'status': 'no_face',
                'faces': 0,
                'message': 'No face detected. Please ensure your face is visible.'
            }
        elif face_count == 1:
            return {
                'status': 'ok',
                'faces': 1,
                'message': 'Face detected successfully.'
            }
        else:
            return {
                'status': 'multiple_faces',
                'faces': face_count,
                'message': f'{face_count} faces detected. Only one person should be present.'
            }

    except Exception as e:
        return {
            'status': 'error',
            'faces': -1,
            'message': f'Face check error: {str(e)}'
        }
