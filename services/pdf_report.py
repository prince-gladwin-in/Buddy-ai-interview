"""
services/pdf_report.py — Automated PDF report generation using FPDF2.
Generates two types of reports:
  1. Candidate Report   — personal performance summary
  2. Admin Report       — detailed analytics with recommendations
"""
from fpdf import FPDF
from datetime import datetime
import os


# ── Colour palette ─────────────────────────────────────────────────────────────
PRIMARY   = (79, 70, 229)    # Indigo
SECONDARY = (124, 58, 237)   # Violet
SUCCESS   = (16, 185, 129)   # Emerald
WARNING   = (245, 158, 11)   # Amber
DANGER    = (239, 68, 68)    # Red
DARK      = (17, 24, 39)     # Near-black
LIGHT     = (249, 250, 251)  # Off-white
GRAY      = (107, 114, 128)  # Gray


class BuddyPDF(FPDF):
    """Custom FPDF subclass with branded header/footer."""

    def __init__(self, title="Buddy AI Interview Report"):
        super().__init__()
        self.report_title = title

    def header(self):
        # Gradient-style header bar
        self.set_fill_color(*PRIMARY)
        self.rect(0, 0, 210, 22, 'F')
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.set_y(5)
        self.cell(0, 12, f'  🤖 {self.report_title}', align='L')
        self.set_font('Helvetica', '', 9)
        self.set_y(5)
        self.cell(0, 12, f'Generated: {datetime.now().strftime("%d %b %Y %H:%M")}  ', align='R')
        self.ln(20)
        self.set_text_color(*DARK)

    def footer(self):
        self.set_y(-15)
        self.set_fill_color(*PRIMARY)
        self.rect(0, 282, 210, 15, 'F')
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, f'Buddy AI Interview System  |  Page {self.page_no()}', align='C')

    # ── Helpers ────────────────────────────────────────────────────────────
    def section_title(self, text):
        self.set_fill_color(*PRIMARY)
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 9, f'  {text}', fill=True, ln=True)
        self.set_text_color(*DARK)
        self.ln(3)

    def key_value(self, key, value, key_w=60):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*GRAY)
        self.cell(key_w, 7, key)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(*DARK)
        self.cell(0, 7, str(value), ln=True)

    def score_badge(self, label, score, total=None, x=None, y=None):
        """Draw a coloured badge with a score."""
        if x: self.set_x(x)
        color = SUCCESS if (score >= 0.6 if isinstance(score, float) else score >= 6) else DANGER
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 10)
        txt = f'{score}/{total}' if total else f'{score:.1%}'
        self.cell(50, 9, f'{label}: {txt}', fill=True, align='C', ln=True)
        self.set_text_color(*DARK)

    def progress_bar(self, value, max_value=1.0, width=170, height=8):
        """Draw a horizontal progress bar."""
        pct = value / max_value if max_value else 0
        pct = max(0.0, min(1.0, pct))
        # Background
        self.set_fill_color(229, 231, 235)
        self.rect(self.get_x(), self.get_y(), width, height, 'F')
        # Fill
        color = SUCCESS if pct >= 0.6 else (WARNING if pct >= 0.4 else DANGER)
        self.set_fill_color(*color)
        self.rect(self.get_x(), self.get_y(), width * pct, height, 'F')
        self.ln(height + 2)


# ── Public functions ───────────────────────────────────────────────────────────

def generate_candidate_report(candidate, mcq_result, verbal_results, face_alerts, output_path: str):
    """
    Generate a PDF performance report for a candidate.

    Args:
        candidate:       Candidate ORM object
        mcq_result:      MCQResult ORM object (or None)
        verbal_results:  List of VerbalResult ORM objects
        face_alerts:     List of FaceAlert ORM objects
        output_path:     Full filesystem path for the output PDF
    """
    pdf = BuddyPDF(title="Candidate Performance Report")
    pdf.add_page()

    # ── 1. Candidate Information ───────────────────────────────────────────
    pdf.section_title("Candidate Profile")
    pdf.key_value("Name:", candidate.name)
    pdf.key_value("Email:", candidate.email)
    pdf.key_value("College:", candidate.college or "—")
    pdf.key_value("Applied Role:", candidate.role or "—")
    pdf.key_value("Interview Date:", candidate.registered_at.strftime("%d %b %Y") if candidate.registered_at else "—")
    pdf.ln(5)

    # ── 2. MCQ Performance ────────────────────────────────────────────────
    pdf.section_title("Technical MCQ Results")
    if mcq_result:
        pdf.key_value("Score:", f"{mcq_result.score}/{mcq_result.total}")
        pdf.key_value("Status:", "✓ PASSED — Proceeded to Verbal Round" if mcq_result.passed else "✗ DID NOT PASS — Below threshold of 6/10")
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(*GRAY)
        pdf.cell(60, 7, "Score progress:")
        pdf.ln(7)
        pdf.set_x(25)
        pdf.progress_bar(mcq_result.score, max_value=mcq_result.total)
    else:
        pdf.set_font('Helvetica', 'I', 10)
        pdf.cell(0, 7, "No MCQ data recorded.", ln=True)
    pdf.ln(3)

    # ── 3. Verbal Interview Performance ───────────────────────────────────
    pdf.section_title("Verbal Interview Results")
    if verbal_results:
        avg_score = sum(v.similarity_score for v in verbal_results if v.similarity_score) / len(verbal_results)
        pdf.key_value("Questions Answered:", str(len(verbal_results)))
        pdf.key_value("Average Similarity Score:", f"{avg_score:.1%}")

        row_color = False
        for i, vr in enumerate(verbal_results, 1):
            # Question header
            pdf.set_fill_color(243, 244, 246) if row_color else pdf.set_fill_color(255, 255, 255)
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(*PRIMARY)
            pdf.cell(0, 7, f"Q{i}. {vr.question[:90]}{'...' if len(vr.question) > 90 else ''}", fill=True, ln=True)

            # Answer
            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(*DARK)
            answer_text = vr.answer[:200] + '...' if len(vr.answer) > 200 else vr.answer
            pdf.multi_cell(0, 5, f"Answer: {answer_text}", fill=True)

            # Score bar
            sc = vr.similarity_score or 0.0
            score_color = SUCCESS if sc >= 0.6 else (WARNING if sc >= 0.4 else DANGER)
            pdf.set_fill_color(*score_color)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Helvetica', 'B', 8)
            label = "Excellent" if sc >= 0.8 else "Good" if sc >= 0.6 else "Fair" if sc >= 0.4 else "Needs Work"
            pdf.cell(0, 6, f"  Similarity Score: {sc:.1%}  [{label}]", fill=True, ln=True)
            pdf.set_text_color(*DARK)
            pdf.ln(2)
            row_color = not row_color
    else:
        pdf.set_font('Helvetica', 'I', 10)
        pdf.cell(0, 7, "No verbal interview data recorded.", ln=True)
    pdf.ln(3)

    # ── 4. Integrity Summary ──────────────────────────────────────────────
    pdf.section_title("Proctoring & Integrity Monitoring")
    alert_count = len(face_alerts)
    status_color = SUCCESS if alert_count == 0 else (WARNING if alert_count <= 3 else DANGER)
    pdf.set_fill_color(*status_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 9, f"  Total Face Alerts: {alert_count}  {'✓ No Issues' if alert_count == 0 else '⚠ Violations Detected'}", fill=True, ln=True)
    pdf.set_text_color(*DARK)
    pdf.ln(3)

    if face_alerts:
        pdf.set_font('Helvetica', '', 9)
        for fa in face_alerts[:10]:
            pdf.cell(0, 6, f"  • [{fa.timestamp.strftime('%H:%M:%S')}] {fa.alert_type.replace('_', ' ').title()}", ln=True)
        if len(face_alerts) > 10:
            pdf.cell(0, 6, f"  ... and {len(face_alerts) - 10} more alerts", ln=True)

    # ── 5. Overall Recommendation ──────────────────────────────────────────
    pdf.ln(5)
    pdf.section_title("Overall Recommendation")

    verbal_avg = sum(v.similarity_score for v in verbal_results if v.similarity_score) / len(verbal_results) if verbal_results else 0
    mcq_score = mcq_result.score if mcq_result else 0

    if mcq_score >= 8 and verbal_avg >= 0.70 and alert_count == 0:
        rec = "STRONG HIRE — Candidate demonstrated excellent technical knowledge and strong communication skills with no integrity concerns."
        rec_color = SUCCESS
    elif mcq_score >= 6 and verbal_avg >= 0.55 and alert_count <= 2:
        rec = "HIRE — Candidate met the required thresholds and showed satisfactory performance across all evaluation areas."
        rec_color = SUCCESS
    elif mcq_score >= 6 and verbal_avg >= 0.40:
        rec = "CONSIDER — Candidate passed technical screening but verbal responses suggest they need further development in communication."
        rec_color = WARNING
    else:
        rec = "PASS — Candidate did not meet the minimum performance benchmarks for this role at this time."
        rec_color = DANGER

    pdf.set_fill_color(*rec_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.multi_cell(0, 8, f"  {rec}", fill=True)
    pdf.set_text_color(*DARK)

    pdf.output(output_path)
    return output_path


def generate_admin_report(candidate, mcq_result, verbal_results, face_alerts, output_path: str):
    """Extended admin version with full Q&A details and analytics."""
    pdf = BuddyPDF(title="Admin Analytics Report")
    pdf.add_page()

    # Reuse candidate report content + extra analytics page
    pdf.section_title("Candidate Intelligence Summary")
    pdf.key_value("Candidate ID:", f"#{candidate.id}")
    pdf.key_value("Name:", candidate.name)
    pdf.key_value("Email:", candidate.email)
    pdf.key_value("College:", candidate.college or "—")
    pdf.key_value("Role Applied:", candidate.role or "—")
    pdf.ln(5)

    # MCQ analytics
    pdf.section_title("MCQ Analytics")
    if mcq_result:
        accuracy = (mcq_result.score / mcq_result.total) * 100
        pdf.key_value("Score:", f"{mcq_result.score}/{mcq_result.total} ({accuracy:.0f}%)")
        pdf.key_value("Gate Result:", "PASSED ✓" if mcq_result.passed else "FAILED ✗")
        pdf.key_value("Date Taken:", mcq_result.taken_at.strftime("%d %b %Y %H:%M") if mcq_result.taken_at else "—")
    pdf.ln(3)

    # Full verbal breakdown
    pdf.section_title("Verbal Interview Full Transcript")
    if verbal_results:
        scores = [v.similarity_score for v in verbal_results if v.similarity_score]
        avg = sum(scores) / len(scores) if scores else 0
        pdf.key_value("Average AI Score:", f"{avg:.1%}")
        pdf.key_value("Performance Level:", "Excellent" if avg >= 0.8 else "Good" if avg >= 0.6 else "Fair" if avg >= 0.4 else "Needs Improvement")
        pdf.ln(3)
        for i, vr in enumerate(verbal_results, 1):
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(*PRIMARY)
            pdf.multi_cell(0, 6, f"Q{i}: {vr.question}")
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(*DARK)
            pdf.set_x(10)
            pdf.multi_cell(0, 5, f"Answer: {vr.answer or '(No answer recorded)'}")
            sc = vr.similarity_score or 0.0
            pdf.set_text_color(SUCCESS[0], SUCCESS[1], SUCCESS[2]) if sc >= 0.6 else pdf.set_text_color(*DANGER)
            pdf.cell(0, 6, f"   → AI Score: {sc:.1%}", ln=True)
            pdf.set_text_color(*DARK)
            pdf.ln(2)

    # Integrity report
    pdf.section_title("Proctoring Log")
    pdf.key_value("Total Alerts:", str(len(face_alerts)))
    if face_alerts:
        no_face_count = sum(1 for fa in face_alerts if fa.alert_type == 'no_face')
        multi_face_count = sum(1 for fa in face_alerts if fa.alert_type == 'multiple_faces')
        pdf.key_value("  No Face Alerts:", str(no_face_count))
        pdf.key_value("  Multiple Face Alerts:", str(multi_face_count))
        pdf.set_font('Helvetica', '', 8)
        for fa in face_alerts:
            pdf.cell(0, 5, f"  [{fa.timestamp.strftime('%H:%M:%S')}] {fa.alert_type}", ln=True)

    pdf.output(output_path)
    return output_path
