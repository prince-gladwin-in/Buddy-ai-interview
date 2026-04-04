"""
models.py — SQLAlchemy ORM models for the AI Interview System.
Tables: Candidate, MCQResult, VerbalResult, FaceAlert
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ── Candidate ──────────────────────────────────────────────────────────────────
class Candidate(db.Model):
    """Stores basic profile info collected at registration."""
    __tablename__ = 'candidates'

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    college       = db.Column(db.String(200))
    role          = db.Column(db.String(50))                  # Chosen interview role
    resume_path   = db.Column(db.String(300))                 # Saved PDF filename
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    mcq_results    = db.relationship('MCQResult',    backref='candidate', lazy=True, cascade='all, delete-orphan')
    verbal_results = db.relationship('VerbalResult', backref='candidate', lazy=True, cascade='all, delete-orphan')
    face_alerts    = db.relationship('FaceAlert',    backref='candidate', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Candidate {self.id} — {self.name}>'

    @property
    def mcq_passed(self):
        """Returns True if the candidate has a passing MCQ result."""
        result = MCQResult.query.filter_by(candidate_id=self.id).first()
        return result.passed if result else False

    @property
    def verbal_avg_score(self):
        """Average cosine similarity score across all verbal answers."""
        scores = [v.similarity_score for v in self.verbal_results if v.similarity_score is not None]
        return round(sum(scores) / len(scores), 3) if scores else None

    @property
    def face_alert_count(self):
        return len(self.face_alerts)


# ── MCQ Result ─────────────────────────────────────────────────────────────────
class MCQResult(db.Model):
    """Records per-session MCQ quiz outcomes."""
    __tablename__ = 'mcq_results'

    id           = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    role         = db.Column(db.String(50))
    score        = db.Column(db.Integer)
    total        = db.Column(db.Integer, default=10)
    passed       = db.Column(db.Boolean, default=False)
    answers_json = db.Column(db.Text)      # JSON: {"q_index": selected_option}
    taken_at     = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MCQResult candidate={self.candidate_id} score={self.score}/{self.total}>'


# ── Verbal Result ──────────────────────────────────────────────────────────────
class VerbalResult(db.Model):
    """Stores one row per verbal question answered by a candidate."""
    __tablename__ = 'verbal_results'

    id               = db.Column(db.Integer, primary_key=True)
    candidate_id     = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    question_index   = db.Column(db.Integer)
    question         = db.Column(db.Text)
    answer           = db.Column(db.Text)
    similarity_score = db.Column(db.Float)   # 0.0 – 1.0 cosine similarity
    taken_at         = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<VerbalResult candidate={self.candidate_id} q={self.question_index} score={self.similarity_score}>'


# ── Face Alert ─────────────────────────────────────────────────────────────────
class FaceAlert(db.Model):
    """Logs each face-validation alert raised during an interview session."""
    __tablename__ = 'face_alerts'

    id           = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    alert_type   = db.Column(db.String(50))   # 'no_face' | 'multiple_faces'
    timestamp    = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<FaceAlert candidate={self.candidate_id} type={self.alert_type}>'
