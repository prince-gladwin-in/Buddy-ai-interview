# 🚀 PythonAnywhere Deployment - Complete Step-by-Step Guide

## ✅ Prerequisites
- [ ] GitHub account (already have it ✓)
- [ ] PythonAnywhere account (free or paid)
- [ ] Your Buddy AI Interview repo on GitHub

---

## 📋 Step 1: Create PythonAnywhere Account

1. Go to https://www.pythonanywhere.com/
2. Click **Sign up**
3. Create account (free tier is fine to start)
4. Verify email
5. You're in! 🎉

**Your free domain**: `yourusername.pythonanywhere.com`

---

## 💻 Step 2: Open Bash Console & Clone Repo

1. Login to PythonAnywhere dashboard
2. Click **Consoles** (top menu)
3. Click **New console** → **Bash**
4. A console window opens - run these commands:

```bash
# Go to home directory
cd ~

# Clone your GitHub repo
git clone https://github.com/prince-gladwin-in/Buddy-ai-interview.git

# Navigate into project
cd buddy-ai-interview

# Check it worked
ls -la
```

**Expected output**: You should see files like `app.py`, `requirements.txt`, etc.

---

## 🔧 Step 3: Create Virtual Environment

Still in the Bash console, run:

```bash
# Create virtual environment with Python 3.10
mkvirtualenv --python=/usr/bin/python3.10 buddy_env

# If that doesn't work, try:
python3 -m venv buddy_env
source buddy_env/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

**This will take 2-3 minutes** ⏳ (installing sentence-transformers, opencv, etc.)

**When done**, you'll see: `Successfully installed ...`

---

## 🌐 Step 4: Create Web App in PythonAnywhere

1. Click **Web** (top menu)
2. Click **Add a new web app**
3. Choose **Manual configuration**
4. Select **Python 3.10**
5. Click **Create**

Your web app is created! ✓

---

## ⚙️ Step 5: Configure Web App Settings

### **Find your Web app settings:**
1. Go to **Web** tab
2. You should see your web app listed
3. Click on it to open settings

### **A. Set Virtualenv Path**

Look for **Virtualenv section**:
- Enter: `/home/yourusername/.virtualenvs/buddy_env`
- Replace `yourusername` with your actual PythonAnywhere username
- Press Enter to save

### **B. Set WSGI Configuration**

Look for **WSGI configuration file**:
- Click the link (shows path like `/var/www/yourusername_pythonanywhere_com_wsgi.py`)
- The file opens in editor
- **Delete all content** and paste this:

```python
import os
import sys

# Add your project directory
project_dir = '/home/yourusername/buddy-ai-interview'
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'buddy-ai-interview-secret-2024')

# Import Flask app
from app import app as application
```

**Remember**: Replace `yourusername` with your actual username
- Click **Save** (green button)

### **C. Configure Static Files**

Scroll down to **Static files** section:

**Add this mapping:**
- URL: `/static/`
- Directory: `/home/yourusername/buddy-ai-interview/static`
- Click **Add**

---

## 🗄️ Step 6: Initialize Database

1. Go back to **Consoles** → **Bash**
2. Activate the environment:
   ```bash
   cd ~/buddy-ai-interview
   workon buddy_env
   ```
3. Create database tables:
   ```bash
   python -c "from app import app; app.app_context().push(); from models import db; db.create_all(); print('✅ Database initialized!')"
   ```

**Should output**: `✅ Database initialized!`

---

## 🔄 Step 7: Reload Web App

1. Go to **Web** tab
2. Find your web app
3. Click the big green **Reload** button (top right)
4. Wait 1-2 seconds for reload to complete

**Status should change to**: 🟢 **Reloading** → 🟢 **Running**

---

## 🌍 Step 8: Test Your Live App

Visit your app at:
```
https://yourusername.pythonanywhere.com/
```

Replace `yourusername` with your actual PythonAnywhere username.

### **What should show:**
- ✅ Buddy AI Interview home page
- ✅ Candidate registration form
- ✅ Admin login at `/admin/login`

---

## ⚠️ If It Doesn't Work

### **Check Error Logs**

In **Web** tab, scroll down to **Log files**:
- Click **Error log** 
- Look for red error messages
- Common issues below 👇

### **Common Issues & Fixes**

#### **Issue: "ModuleNotFoundError: No module named 'app'"**
- **Fix**: Check WSGI file - wrong `project_dir` path?
- Verify path with: `wc -l ~/buddy-ai-interview/app.py`

#### **Issue: "Permission denied"**
- **Fix**: In bash console run:
  ```bash
  chmod 755 ~/buddy-ai-interview
  chmod 755 ~/buddy-ai-interview/instance
  ```

#### **Issue: Static files not loading (CSS/JS broken)**
- **Fix**: Check Static files configuration
- URL should be `/static/`
- Path should be `/home/yourusername/buddy-ai-interview/static`

#### **Issue: Database errors**
- **Fix**: Re-initialize database:
  ```bash
  cd ~/buddy-ai-interview && workon buddy_env
  python -c "from app import app; app.app_context().push(); from models import db; db.create_all()"
  ```

#### **Issue: "502 Bad Gateway"**
- **Fix**: Reload the web app again and wait 30 seconds

---

## 📱 Access Your App

### **Candidate Page**
```
https://yourusername.pythonanywhere.com/
```
- Register as candidate
- Take MCQ test
- Do verbal interview
- Get results

### **Admin Dashboard**
```
https://yourusername.pythonanywhere.com/admin/login
```
- Username: `admin`
- Password: `admin123` (default)
- ⚠️ **CHANGE THIS!** (see below)

---

## 🔐 Change Admin Password

1. Open Bash console
2. Run:
   ```bash
   cd ~/buddy-ai-interview && workon buddy_env
   python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your_new_password'))"
   ```
3. Copy the output (long hash)
4. Edit **WSGI file** and add this before `from app import app`:
   ```python
   os.environ['ADMIN_PASSWORD'] = 'your_new_password'
   ```
5. Save and reload web app

---

## 🔄 Update Code from GitHub

When you push new code to GitHub, update PythonAnywhere:

1. Open **Bash console**
2. Run:
   ```bash
   cd ~/buddy-ai-interview
   git pull
   workon buddy_env
   pip install -r requirements.txt --upgrade
   ```
3. Go to **Web** → Click **Reload** button

---

## 💾 Backup Your Database

Your SQLite database is here:
```
/home/yourusername/buddy-ai-interview/instance/interview.db
```

To download:
1. Go to **Files** (top menu)
2. Navigate to `instance/`
3. Right-click `interview.db` → **Download**

---

## 🎯 Summary Checklist

- [ ] Created PythonAnywhere account
- [ ] Cloned repo in bash console
- [ ] Created virtual environment
- [ ] Added web app (Python 3.10)
- [ ] Set virtualenv path
- [ ] Updated WSGI configuration file
- [ ] Configured static files
- [ ] Initialized database
- [ ] Clicked Reload button
- [ ] Tested app at `yourusername.pythonanywhere.com`
- [ ] Changed admin password
- [ ] ✅ **DEPLOYED!**

---

## 📞 Need Help?

If something breaks:
1. Check **Error log** in Web tab
2. Search error message in browser
3. Re-read the relevant section above

**Most common fix**: 🔄 Reload the web app!

---

**Your app is now LIVE on the internet! 🎉**
