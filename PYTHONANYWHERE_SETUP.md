# PythonAnywhere Deployment Guide

## Prerequisites
- PythonAnywhere account (free or paid tier)
- GitHub repository with your code

## Step-by-Step Deployment

### 1. Create PythonAnywhere Account
- Sign up at https://www.pythonanywhere.com/
- Free tier includes: `your_username.pythonanywhere.com`

### 2. Open Bash Console
- Click **Consoles** → **New console** → **Bash**
- Run these commands:

```bash
# Clone your repository
cd ~
git clone https://github.com/prince-gladwin-in/Buddy-ai-interview.git

# Navigate to project
cd buddy-ai-interview

# Create virtual environment
mkvirtualenv --python=/usr/bin/python3.10 buddy_env

# Activate virtual environment
workon buddy_env

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Web App
- Go to **Web** tab in PythonAnywhere dashboard
- Click **Add a new web app**
- Choose: **Manual configuration** → **Python 3.10**
- Click **Create**

### 4. Update WSGI Configuration
- In Web tab, find **WSGI configuration file**
- Click to edit it
- Replace the content with this (adjust path if needed):

```python
import os
import sys

project_home = '/home/your_username/buddy-ai-interview'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ['FLASK_ENV'] = 'production'
os.environ['PYTHONUNBUFFERED'] = 'True'

from app import app as application
```

### 5. Set Virtual Environment
- In **Web** tab, scroll to **Virtualenv**
- Enter: `/home/your_username/.virtualenvs/buddy_env`
- Click the 🔄 reload button to apply

### 6. Configure Static Files
- In **Web** tab, under **Static files**:
  - URL: `/static/`
  - Directory: `/home/your_username/buddy-ai-interview/static`
- Save it

### 7. Set Environment Variables
- Click **Web** → **Edit WSGI configuration**
- Add these before `from app import app`:

```python
os.environ['SECRET_KEY'] = 'your-secret-key'
os.environ['ADMIN_PASSWORD'] = 'your-password'
# Add others as needed
```

### 8. Configure Database
- Use SQLite (no extra setup needed) for Free tier
- Or use MySQL (available in paid tiers)
- Database files stored in project directory work fine

### 9. Reload Web App
- Click the green **Reload** button at the top of Web tab
- Wait 1-2 minutes for changes to apply

### 10. Access Your App
- Visit: `https://your_username.pythonanywhere.com/`
- Admin login: `https://your_username.pythonanywhere.com/admin/login`

## Useful Commands in PythonAnywhere Bash

```bash
# Activate environment
workon buddy_env

# Update code from GitHub
cd ~/buddy-ai-interview
git pull

# Update dependencies
pip install -r requirements.txt --upgrade

# Check logs
tail -f /var/log/your_username.pythonanywhere.com.log

# Access Python shell
python manage.py shell
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **"ModuleNotFoundError"** | Check virtualenv path, install dependencies |
| **"Permission denied"** | Use `chmod +x` on necessary files |
| **Static files not loading** | Verify Static files path in Web tab |
| **Database locked** | SQLite issue - restart web app |
| **Slow uploads** | Use PythonAnywhere's file upload or SFTP |

## Key Advantages of PythonAnywhere
✅ Easy setup - no terminal knowledge needed  
✅ Free tier available  
✅ HTTPS by default  
✅ No credit card for free tier  
✅ Python-specific hosting  
✅ MySQL included (in paid tiers)  

## Key Limitations
❌ Free tier limited to 100MB storage  
❌ Flask uploads limited to file size constraints  
❌ Limited to 100 CPU seconds/day (free)  
❌ No background tasks on free tier  

---

**Recommended**: Use **Paid Tier** ($5/month) for unlimited storage and better performance.
