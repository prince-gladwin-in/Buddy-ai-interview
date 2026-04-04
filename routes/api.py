"""
routes/api.py — JSON API endpoints.
  POST /api/verbal/score  — Score a verbal answer via SentenceTransformer
  POST /api/face/check    — Check webcam snapshot via OpenCV
  POST /api/verbal/complete — Mark verbal interview complete and redirect
"""
import json
from flask import Blueprint, request, jsonify, session, current_app
from models import db, Candidate, VerbalResult, FaceAlert
from services.scorer import score_answer
from services.face_check import check_face

api_bp = Blueprint('api', __name__)


# ── Verbal Scoring ─────────────────────────────────────────────────────────────

@api_bp.route('/verbal/score', methods=['POST'])
def verbal_score():
    """
    Score one verbal question answer.
    Body JSON: { candidate_id, question_index, question, answer, ideal_answer }
    Returns: { score, label, success }
    """
    data = request.get_json(silent=True) or {}
    candidate_id   = data.get('candidate_id')
    question_index = data.get('question_index', 0)
    question       = data.get('question', '')
    answer         = data.get('answer', '')
    ideal_answer   = data.get('ideal_answer', '')

    if not candidate_id or not answer.strip():
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    # Compute semantic similarity
    score = score_answer(answer, ideal_answer)

    # Determine label
    if score >= 0.80:
        label = "Excellent"
        reflection = "That was a fantastic answer! I can really tell you've thought deeply about this. 🌟"
    elif score >= 0.60:
        label = "Good"
        reflection = "Nice work! You covered the key points really well. I appreciate your thoughtfulness. 😊"
    elif score >= 0.40:
        label = "Fair"
        reflection = "Thanks for sharing that! There's some great thinking in there — don't be too hard on yourself. 💪"
    else:
        label = "Needs Improvement"
        reflection = "I appreciate you giving it a go! Each question is a learning opportunity. You're doing great just by being here. 🙏"

    # Save to database
    verbal_result = VerbalResult(
        candidate_id=candidate_id,
        question_index=question_index,
        question=question,
        answer=answer,
        similarity_score=score
    )
    db.session.add(verbal_result)
    db.session.commit()

    return jsonify({
        'success': True,
        'score': score,
        'score_pct': f"{score:.0%}",
        'label': label,
        'reflection': reflection
    })


# ── Face Validation ────────────────────────────────────────────────────────────

@api_bp.route('/face/check', methods=['POST'])
def face_check():
    """
    Process a webcam snapshot and check for face presence.
    Body JSON: { candidate_id, image_b64 }
    Returns: { status, faces, message }
    """
    data = request.get_json(silent=True) or {}
    candidate_id = data.get('candidate_id')
    image_b64    = data.get('image_b64', '')

    if not image_b64:
        return jsonify({'status': 'error', 'message': 'No image provided'}), 400

    result = check_face(image_b64)

    # Log violations to the database
    if candidate_id and result['status'] in ('no_face', 'multiple_faces'):
        alert = FaceAlert(
            candidate_id=candidate_id,
            alert_type=result['status']
        )
        db.session.add(alert)
        db.session.commit()

    return jsonify(result)


# ── Verbal Interview Complete ──────────────────────────────────────────────────

@api_bp.route('/verbal/complete', methods=['POST'])
def verbal_complete():
    """
    Called when all verbal questions have been answered.
    Returns: { redirect_url }
    """
    data = request.get_json(silent=True) or {}
    candidate_id = data.get('candidate_id')
    if not candidate_id:
        return jsonify({'success': False, 'error': 'Missing candidate_id'}), 400

    return jsonify({
        'success': True,
        'redirect_url': f'/results/{candidate_id}'
    })
