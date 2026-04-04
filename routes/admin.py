"""
routes/admin.py — Admin dashboard routes (protected by session auth).
  GET  /admin/login         — Show login page
  POST /admin/login         — Authenticate admin
  GET  /admin/logout        — Log out
  GET  /admin/dashboard     — Search / list candidates
  GET  /admin/candidate/<id> — Candidate detail view
  GET  /admin/report/<id>   — Generate and download PDF report
"""
import os
from functools import wraps
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    session, flash, send_file, current_app
)
from werkzeug.security import check_password_hash
from models import db, Candidate, MCQResult, VerbalResult, FaceAlert
from services.pdf_report import generate_candidate_report, generate_admin_report

admin_bp = Blueprint('admin', __name__)


# ── Auth decorator ─────────────────────────────────────────────────────────────

def admin_required(f):
    """Redirect to login if the admin session is not active."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash("Please log in to access the admin panel.", 'warning')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated


# ── Login / Logout ─────────────────────────────────────────────────────────────

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if (
            username == current_app.config['ADMIN_USERNAME'] and
            check_password_hash(current_app.config['ADMIN_PASSWORD_HASH'], password)
        ):
            session['admin_logged_in'] = True
            flash("Welcome back, Admin! 👋", 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash("Invalid credentials. Please try again.", 'error')

    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash("You have been logged out.", 'info')
    return redirect(url_for('admin.login'))


# ── Dashboard ──────────────────────────────────────────────────────────────────

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Search candidates and show summary statistics."""
    query  = request.args.get('q', '').strip()
    role   = request.args.get('role', '').strip()
    page   = request.args.get('page', 1, type=int)

    candidates_query = Candidate.query

    if query:
        # Search by ID, name, or email
        if query.isdigit():
            candidates_query = candidates_query.filter(Candidate.id == int(query))
        else:
            like = f'%{query}%'
            candidates_query = candidates_query.filter(
                db.or_(Candidate.name.ilike(like), Candidate.email.ilike(like))
            )

    if role:
        candidates_query = candidates_query.filter(Candidate.role == role)

    candidates = candidates_query.order_by(Candidate.registered_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    # Stats
    total_candidates = Candidate.query.count()
    total_passed_mcq = MCQResult.query.filter_by(passed=True).count()
    total_verbal     = VerbalResult.query.count()
    total_alerts     = FaceAlert.query.count()

    stats = {
        'total_candidates': total_candidates,
        'passed_mcq': total_passed_mcq,
        'verbal_answers': total_verbal,
        'face_alerts': total_alerts,
    }

    return render_template(
        'admin/dashboard.html',
        candidates=candidates,
        stats=stats,
        query=query,
        selected_role=role,
        roles=current_app.config['ROLES']
    )


# ── Candidate Detail ───────────────────────────────────────────────────────────

@admin_bp.route('/candidate/<int:candidate_id>')
@admin_required
def candidate_detail(candidate_id):
    """Full candidate profile with all interview data."""
    candidate      = Candidate.query.get_or_404(candidate_id)
    mcq_result     = MCQResult.query.filter_by(candidate_id=candidate_id).first()
    verbal_results = VerbalResult.query.filter_by(candidate_id=candidate_id).order_by(VerbalResult.question_index).all()
    face_alerts    = FaceAlert.query.filter_by(candidate_id=candidate_id).all()

    verbal_avg = None
    if verbal_results:
        scores = [v.similarity_score for v in verbal_results if v.similarity_score is not None]
        verbal_avg = round(sum(scores) / len(scores), 3) if scores else 0.0

    return render_template(
        'admin/candidate.html',
        candidate=candidate,
        mcq_result=mcq_result,
        verbal_results=verbal_results,
        face_alerts=face_alerts,
        verbal_avg=verbal_avg
    )


# ── PDF Report Download ────────────────────────────────────────────────────────

@admin_bp.route('/report/<int:candidate_id>')
@admin_required
def generate_report(candidate_id):
    """Generate and download a PDF admin report for a candidate."""
    candidate      = Candidate.query.get_or_404(candidate_id)
    mcq_result     = MCQResult.query.filter_by(candidate_id=candidate_id).first()
    verbal_results = VerbalResult.query.filter_by(candidate_id=candidate_id).order_by(VerbalResult.question_index).all()
    face_alerts    = FaceAlert.query.filter_by(candidate_id=candidate_id).all()

    filename    = f"admin_report_{candidate_id}_{candidate.name.replace(' ', '_')}.pdf"
    output_path = os.path.join(current_app.config['REPORTS_FOLDER'], filename)

    generate_admin_report(candidate, mcq_result, verbal_results, face_alerts, output_path)

    return send_file(output_path, as_attachment=True, download_name=filename)


@admin_bp.route('/candidate-report/<int:candidate_id>')
@admin_required
def candidate_report(candidate_id):
    """Generate and download a candidate-friendly PDF report."""
    candidate      = Candidate.query.get_or_404(candidate_id)
    mcq_result     = MCQResult.query.filter_by(candidate_id=candidate_id).first()
    verbal_results = VerbalResult.query.filter_by(candidate_id=candidate_id).order_by(VerbalResult.question_index).all()
    face_alerts    = FaceAlert.query.filter_by(candidate_id=candidate_id).all()

    filename    = f"candidate_report_{candidate_id}_{candidate.name.replace(' ', '_')}.pdf"
    output_path = os.path.join(current_app.config['REPORTS_FOLDER'], filename)

    generate_candidate_report(candidate, mcq_result, verbal_results, face_alerts, output_path)

    return send_file(output_path, as_attachment=True, download_name=filename)
