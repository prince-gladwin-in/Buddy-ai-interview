"""
services/scorer.py — Semantic similarity scoring using SentenceTransformer.
Compares candidate verbal answers to ideal answers via cosine similarity.
Model: paraphrase-MiniLM-L6-v2 (downloaded on first run, ~80 MB)
"""
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# ── Model singleton: loaded once at import time ────────────────────────────────
_model = None


def _get_model():
    """Load the SentenceTransformer model (lazy singleton)."""
    global _model
    if _model is None:
        print("[Scorer] Loading SentenceTransformer model (first run may take a moment)...")
        _model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        print("[Scorer] Model loaded ✓")
    return _model


def score_answer(candidate_answer: str, ideal_answer: str) -> float:
    """
    Compute the cosine similarity between a candidate's answer and the ideal answer.

    Args:
        candidate_answer: The transcribed or typed answer from the candidate.
        ideal_answer:     The reference answer stored in verbal_questions.json.

    Returns:
        A float in [0.0, 1.0] representing semantic similarity.
        Scores are clamped to [0.0, 1.0] and rounded to 3 decimal places.
    """
    if not candidate_answer or not candidate_answer.strip():
        return 0.0

    model = _get_model()

    # Encode both texts as sentence embeddings
    embeddings = model.encode(
        [candidate_answer.strip(), ideal_answer.strip()],
        convert_to_numpy=True
    )

    # Compute cosine similarity (returns a 2D array)
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

    # Clamp and round
    score = float(np.clip(similarity, 0.0, 1.0))
    return round(score, 3)


def score_to_label(score: float) -> str:
    """
    Convert a numeric similarity score to a human-readable performance label.
    Used in reports and the admin dashboard.
    """
    if score >= 0.80:
        return "Excellent"
    elif score >= 0.60:
        return "Good"
    elif score >= 0.40:
        return "Fair"
    else:
        return "Needs Improvement"
