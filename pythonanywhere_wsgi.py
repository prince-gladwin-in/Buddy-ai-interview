# ============================================================================
# PythonAnywhere WSGI configuration file
# This file tells PythonAnywhere how to run your Flask application
# ============================================================================
import os
import sys

# Add your project directory to sys.path
project_home = '/home/your_username/buddy-ai-interview'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment to production
os.environ['FLASK_ENV'] = 'production'
os.environ['PYTHONUNBUFFERED'] = 'True'

# Import and run the Flask app
from app import app as application
