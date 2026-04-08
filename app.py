"""
app.py — Flask application factory and entry point for the AI Interview System.
Run with: python app.py
"""
import os
from flask import Flask
from config import Config
from models import db


def create_app(config_class=Config):
    """Application factory: create and configure the Flask app."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── Ensure required directories exist ──────────────────────────────────
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['BASE_DIR'], 'instance'), exist_ok=True)

    # ── Initialize database ────────────────────────────────────────────────
    db.init_app(app)

    # ── Register Blueprints ────────────────────────────────────────────────
    from routes.candidate import candidate_bp
    from routes.admin import admin_bp
    from routes.api import api_bp

    app.register_blueprint(candidate_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    # ── Create database tables ─────────────────────────────────────────────
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("  Buddy AI Interview System — Starting up...")
    print("  📍 http://localhost:5000")
    print("  🔑 Admin: http://localhost:5000/admin/login")
    print("=" * 60)
    
    # Get port from environment (Heroku sets this)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
