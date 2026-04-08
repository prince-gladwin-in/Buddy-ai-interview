# Buddy AI — AI Interview Evaluation System

A complete AI-powered interview evaluation platform built with Flask, featuring semantic verbal scoring, real-time face proctoring, role-specific MCQs, and automated PDF performance reports.

---

## Features

| Module | Technology |
|---|---|
| **Candidate Registration** | Flask + SQLite, secure PDF resume upload |
| **Technical MCQ Round** | CSV-driven, role-specific, 6/10 progression gate |
| **Verbal AI Interview** | Web Speech API + SentenceTransformer (cosine similarity) |
| **Face Proctoring** | OpenCV Haar Cascade, webcam snapshot every 5s |
| **Admin Dashboard** | Secure portal, candidate search, FPDF2 PDF reports |
| **Buddy Persona** | Warm, empathetic AI guide between questions |

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/buddy-ai-interview.git
cd buddy-ai-interview

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
# Open http://localhost:5000
```

---

## Usage

### Candidate
1. `http://localhost:5000` → **Start Interview**
2. Fill registration form, upload PDF resume
3. Complete **10 MCQ questions** (20-min timer) — need **≥ 6/10** to proceed
4. Complete **5 verbal questions** via voice or typing — Buddy provides reflections
5. View results with MCQ score, verbal AI score, face alert log, and hire recommendation

### Admin
- `http://localhost:5000/admin/login`
- **Default credentials:** `admin` / `admin123`
- Search candidates, view full transcripts, download PDF reports

---

## Project Structure

```
├── app.py                  Flask application factory
├── config.py               Configuration (roles, paths, auth)
├── models.py               SQLAlchemy models (Candidate, MCQResult, VerbalResult, FaceAlert)
├── questions.csv           45 MCQs (15 × 3 roles)
├── verbal_questions.json   15 verbal questions + ideal answers
├── routes/
│   ├── candidate.py        Registration, MCQ, Verbal, Results
│   ├── admin.py            Dashboard, candidate detail, PDF downloads
│   └── api.py              /api/verbal/score, /api/face/check
├── services/
│   ├── scorer.py           SentenceTransformer semantic scoring
│   ├── face_check.py       OpenCV face detection
│   └── pdf_report.py       FPDF2 report generation
├── templates/              9 Jinja2 HTML templates
└── static/
    ├── css/style.css       Dark premium design system
    └── js/                 MCQ controller, Verbal + Buddy flow, Face monitor
```

---

## Tech Stack

- **Backend:** Python 3.10+, Flask 3.x, Flask-SQLAlchemy, SQLite
- **AI/ML:** `sentence-transformers` (paraphrase-MiniLM-L6-v2), `scikit-learn`
- **Vision:** `opencv-python` (Haar Cascade face detection)
- **PDF:** `fpdf2`
- **Frontend:** Vanilla HTML/CSS/JS, Web Speech API

---

## Notes

> The SentenceTransformer model (~80 MB) downloads automatically on the first verbal scoring call.
> Web Speech API works best in Chrome/Edge with a working microphone.
> Candidates can also type answers directly if voice is unavailable.

---

## License

MIT
