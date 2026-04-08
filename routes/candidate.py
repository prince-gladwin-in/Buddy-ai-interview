"""
routes/candidate.py — All candidate-facing routes.
Covers: registration, MCQ quiz, verbal interview, and results.
"""
import os
import json
import uuid
import random
import pandas as pd
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, flash, current_app, send_from_directory
)
from models import db, Candidate, MCQResult, VerbalResult, FaceAlert
from werkzeug.utils import secure_filename

candidate_bp = Blueprint('candidate', __name__)


# ────────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
    )


def load_questions(role: str, n: int = 10) -> list:
    """Load and randomly select n MCQ questions for the given role."""
    df = pd.read_csv(current_app.config['MCQ_QUESTIONS_FILE'])
    role_df = df[df['role'] == role]
    sampled = role_df.sample(min(n, len(role_df))).reset_index(drop=True)
    questions = []
    for _, row in sampled.iterrows():
        questions.append({
            'question': row['question'],
            'options': {
                'A': row['optionA'],
                'B': row['optionB'],
                'C': row['optionC'],
                'D': row['optionD'],
            },
            'answer': row['answer']
        })
    return questions


def load_verbal_questions(role: str) -> list:
    """Load verbal interview questions for the given role."""
    with open(current_app.config['VERBAL_QUESTIONS_FILE'], 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get(role, [])


# ────────────────────────────────────────────────────────────────────────────────
# Landing Page
# ────────────────────────────────────────────────────────────────────────────────

@candidate_bp.route('/')
def index():
    """Home / landing page."""
    return render_template('index.html', total_roles=len(current_app.config['ROLES']))


# ────────────────────────────────────────────────────────────────────────────────
# Registration
# ────────────────────────────────────────────────────────────────────────────────

@candidate_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Candidate registration with resume upload."""
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        email   = request.form.get('email', '').strip().lower()
        college = request.form.get('college', '').strip()
        role    = request.form.get('role', '').strip()
        file    = request.files.get('resume')

        # ── Validation ─────────────────────────────────────────────────────
        errors = []
        if not name:   errors.append("Name is required.")
        if not email:  errors.append("Email is required.")
        if not role:   errors.append("Please select a role.")
        if not file or file.filename == '':
            errors.append("Please upload your resume (PDF).")
        elif not allowed_file(file.filename):
            errors.append("Only PDF files are accepted.")

        # Check duplicate email
        if email and Candidate.query.filter_by(email=email).first():
            errors.append("This email is already registered. Please use a different one.")

        if errors:
            for err in errors:
                flash(err, 'error')
            return render_template('register.html',
                                   roles=current_app.config['ROLES'],
                                   form_data=request.form)

        # ── Save resume ────────────────────────────────────────────────────
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        resume_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(resume_path)

        # ── Create candidate record ────────────────────────────────────────
        candidate = Candidate(
            name=name,
            email=email,
            college=college,
            role=role,
            resume_path=filename
        )
        db.session.add(candidate)
        db.session.commit()

        # Store candidate ID in session
        session['candidate_id'] = candidate.id
        session['candidate_role'] = role
        flash(f"Welcome, {name}! Your registration is complete.", 'success')
        return redirect(url_for('candidate.mcq', candidate_id=candidate.id))

    return render_template('register.html',
                           roles=current_app.config['ROLES'],
                           form_data={})


# ────────────────────────────────────────────────────────────────────────────────
# MCQ Quiz
# ────────────────────────────────────────────────────────────────────────────────

@candidate_bp.route('/mcq/<int:candidate_id>', methods=['GET', 'POST'])
def mcq(candidate_id):
    """MCQ quiz engine — role-specific, 10 questions, gate at 6/10."""
    candidate = Candidate.query.get_or_404(candidate_id)

    # Prevent re-taking
    existing = MCQResult.query.filter_by(candidate_id=candidate_id).first()
    if existing:
        if existing.passed:
            return redirect(url_for('candidate.verbal', candidate_id=candidate_id))
        else:
            flash("You did not meet the MCQ threshold. Your session has ended.", 'error')
            return redirect(url_for('candidate.results', candidate_id=candidate_id))

    # ── Load or restore questions from session ─────────────────────────────
    session_key = f'mcq_questions_{candidate_id}'
    if session_key not in session:
        questions = load_questions(candidate.role, current_app.config['MCQ_QUESTIONS_PER_SESSION'])
        session[session_key] = questions
    else:
        questions = session[session_key]

    if request.method == 'POST':
        selected_answers = {}
        for i, q in enumerate(questions):
            selected_answers[str(i)] = request.form.get(f'q{i}', '')

        # ── Score ──────────────────────────────────────────────────────────
        score = sum(
            1 for i, q in enumerate(questions)
            if selected_answers.get(str(i)) == q['answer']
        )
        passed = score >= current_app.config['MCQ_PASS_THRESHOLD']

        # ── Save result ────────────────────────────────────────────────────
        mcq_result = MCQResult(
            candidate_id=candidate_id,
            role=candidate.role,
            score=score,
            total=len(questions),
            passed=passed,
            answers_json=json.dumps(selected_answers)
        )
        db.session.add(mcq_result)
        db.session.commit()

        # Clear session questions
        session.pop(session_key, None)

        if passed:
            flash(f"🎉 Great job! You scored {score}/{len(questions)}. Proceeding to the verbal interview.", 'success')
            return redirect(url_for('candidate.verbal', candidate_id=candidate_id))
        else:
            flash(f"You scored {score}/{len(questions)}. A minimum of {current_app.config['MCQ_PASS_THRESHOLD']} is required to proceed.", 'warning')
            return redirect(url_for('candidate.results', candidate_id=candidate_id))

    return render_template('mcq.html', candidate=candidate, questions=questions)


def generate_mcq_review(score, total_questions, role):
    """Generate AI-powered feedback based on MCQ performance."""
    percentage = (score / total_questions) * 100
    
    # Categorize performance
    if percentage >= 90:
        level = "Outstanding"
        feedback = f"Exceptional performance! You scored {score}/{total_questions} ({percentage:.0f}%). Your mastery of {role} concepts is exceptional. You're well-prepared for this role and demonstrated strong problem-solving abilities across all domains."
        suggestions = [
            "Continue maintaining your high standards and keep exploring advanced topics",
            "Consider mentoring others or contributing to technical discussions",
            "Focus on real-world problem-solving to deepen your expertise"
        ]
        growth = "minimal"
    elif percentage >= 80:
        level = "Excellent"
        feedback = f"Great work! You scored {score}/{total_questions} ({percentage:.0f}%). You have a strong grasp of {role} fundamentals and demonstrated solid understanding across most topics. You're ready to proceed to the next round with confidence."
        suggestions = [
            "Review the 1-2 questions you missed to solidify your knowledge",
            "Practice edge cases and advanced scenarios for these topics",
            f"Stay updated with latest best practices in {role}"
        ]
        growth = "moderate"
    elif percentage >= 70:
        level = "Good"
        feedback = f"Good effort! You scored {score}/{total_questions} ({percentage:.0f}%). You've shown solid understanding of key {role} concepts. There are some areas that need strengthening before proceeding to advanced topics."
        suggestions = [
            f"Review the {total_questions - score} questions you missed and understand the correct answers",
            "Study the fundamental concepts more thoroughly",
            "Practice similar questions to build confidence",
            "Focus on areas where you had doubts"
        ]
        growth = "moderate"
    elif percentage >= 60:
        level = "Average"
        feedback = f"Satisfactory performance! You scored {score}/{total_questions} ({percentage:.0f}%). You've met the minimum threshold to proceed, but there's significant room for growth in your {role} knowledge."
        suggestions = [
            f"Carefully review all {total_questions - score} incorrect answers",
            f"Go back to basics and strengthen your foundation in {role}",
            "Create a study plan targeting weak areas",
            "Practice regularly with varied questions",
            "Seek clarification on difficult concepts"
        ]
        growth = "significant"
    else:
        level = "Needs Improvement"
        feedback = f"You scored {score}/{total_questions} ({percentage:.0f}%). Unfortunately, you haven't met the passing threshold. This indicates you need more preparation in {role} concepts before proceeding to the next round."
        suggestions = [
            f"Take time to thoroughly study the {role} fundamentals",
            "Review all the questions and understand why each answer is correct",
            "Create a structured learning plan with clear milestones",
            "Consider finding mentorship or additional resources",
            "Practice consistently before attempting the test again"
        ]
        growth = "critical"
    
    return {
        "level": level,
        "feedback": feedback,
        "suggestions": suggestions,
        "growth": growth,
        "score": score,
        "total": total_questions,
        "percentage": percentage
    }


# ── MCQ Review
@candidate_bp.route('/review/<int:candidate_id>')
def review(candidate_id):
    """Display AI-generated MCQ review and feedback."""
    candidate = Candidate.query.get_or_404(candidate_id)
    mcq_result = MCQResult.query.filter_by(candidate_id=candidate_id).first()
    
    if not mcq_result:
        flash("No MCQ results found.", 'error')
        return redirect(url_for('candidate.index'))
    
    review_data = generate_mcq_review(mcq_result.score, mcq_result.total, candidate.role)
    
    return render_template('review.html', candidate=candidate, mcq_result=mcq_result, review_data=review_data)


# ────────────────────────────────────────────────────────────────────────────────
# Verbal Interview
# ────────────────────────────────────────────────────────────────────────────────

@candidate_bp.route('/verbal/<int:candidate_id>')
def verbal(candidate_id):
    """Verbal interview page — serves the questions; scoring happens via /api."""
    candidate = Candidate.query.get_or_404(candidate_id)

    # Gate check
    mcq_result = MCQResult.query.filter_by(candidate_id=candidate_id).first()
    if not mcq_result or not mcq_result.passed:
        flash("Access denied. You must pass the MCQ round first.", 'error')
        return redirect(url_for('candidate.index'))

    questions = load_verbal_questions(candidate.role)
    return render_template('verbal.html',
                           candidate=candidate,
                           questions=questions,
                           questions_json=json.dumps([q['question'] for q in questions]))


# ────────────────────────────────────────────────────────────────────────────────
# Results Page
# ────────────────────────────────────────────────────────────────────────────────

@candidate_bp.route('/results/<int:candidate_id>')
def results(candidate_id):
    """Show the candidate's complete interview results."""
    candidate = Candidate.query.get_or_404(candidate_id)
    mcq_result = MCQResult.query.filter_by(candidate_id=candidate_id).first()
    verbal_results = VerbalResult.query.filter_by(candidate_id=candidate_id).order_by(VerbalResult.question_index).all()
    face_alerts = FaceAlert.query.filter_by(candidate_id=candidate_id).all()

    verbal_avg = None
    if verbal_results:
        scores = [v.similarity_score for v in verbal_results if v.similarity_score is not None]
        verbal_avg = round(sum(scores) / len(scores), 3) if scores else 0.0

    return render_template(
        'results.html',
        candidate=candidate,
        mcq_result=mcq_result,
        verbal_results=verbal_results,
        face_alerts=face_alerts,
        verbal_avg=verbal_avg
    )
