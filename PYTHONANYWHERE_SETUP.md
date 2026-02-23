# PythonAnywhere + Supabase Deployment Guide

Simple deployment for FitCore using PythonAnywhere (free) + Supabase (free).

## Step 1: Create Supabase Database

1. Go to supabase.com and create account
2. Create new project, save the password
3. Go to SQL Editor, run the contents of `backend/supabase_schema.sql`
4. Get connection string from Project Settings → Database → Connection String (URI)
5. Save it - looks like: `postgresql://postgres.xxxxx:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres`

## Step 2: Sign Up for PythonAnywhere

1. Go to pythonanywhere.com
2. Create free "Beginner" account
3. Choose a username (e.g., `fitcore` - this will be your URL: `fitcore.pythonanywhere.com`)

## Step 3: Upload Code

In PythonAnywhere dashboard:

1. Go to "Files" tab
2. Click "Upload a file" and upload your project as ZIP, OR
3. Use "Bash console" and clone from GitHub:

```bash
git clone https://github.com/HabibWorkspace/MODERN-FITNESS-GYM.git
cd MODERN-FITNESS-GYM
```

## Step 4: Set Up Virtual Environment

In Bash console:

```bash
cd ~/MODERN-FITNESS-GYM
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 5: Configure Environment Variables

Create `.env` file in backend folder:

```bash
cd ~/MODERN-FITNESS-GYM/backend
nano .env
```

Paste this (replace with your values):

```env
DATABASE_URL=postgresql://postgres.xxxxx:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
JWT_ACCESS_TOKEN_EXPIRES=86400
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
FRONTEND_URL=https://YOUR_USERNAME.pythonanywhere.com
```

Press `Ctrl+X`, then `Y`, then `Enter` to save.

## Step 6: Set Up Web App

1. Go to "Web" tab
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select "Python 3.10"

### Configure WSGI File:

1. Click on WSGI configuration file link
2. Delete everything and paste:

```python
import sys
import os

# Add your project directory
project_home = '/home/YOUR_USERNAME/MODERN-FITNESS-GYM'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

backend_path = os.path.join(project_home, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Load environment variables
from dotenv import load_dotenv
env_path = os.path.join(backend_path, '.env')
load_dotenv(env_path)

# Import Flask app
from backend.app import app as application
```

3. Replace `YOUR_USERNAME` with your PythonAnywhere username
4. Save the file

### Configure Virtual Environment:

1. In "Web" tab, find "Virtualenv" section
2. Enter: `/home/YOUR_USERNAME/MODERN-FITNESS-GYM/venv`
3. Replace `YOUR_USERNAME` with your username

### Configure Static Files:

Add these mappings in "Static files" section:

| URL | Directory |
|-----|-----------|
| `/` | `/home/YOUR_USERNAME/MODERN-FITNESS-GYM/frontend/dist` |
| `/assets` | `/home/YOUR_USERNAME/MODERN-FITNESS-GYM/frontend/dist/assets` |

Replace `YOUR_USERNAME` with your username.

## Step 7: Build Frontend

In Bash console:

```bash
cd ~/MODERN-FITNESS-GYM/frontend
npm install
npm run build
```

## Step 8: Update Frontend API URL

Edit `frontend/.env`:

```bash
cd ~/MODERN-FITNESS-GYM/frontend
nano .env
```

Set:
```env
VITE_API_URL=https://YOUR_USERNAME.pythonanywhere.com/api
```

Rebuild:
```bash
npm run build
```

## Step 9: Reload Web App

1. Go to "Web" tab
2. Click green "Reload" button
3. Visit `https://YOUR_USERNAME.pythonanywhere.com`

## Step 10: Create Admin User

In Supabase SQL Editor:

```sql
INSERT INTO "user" (username, email, password_hash, plain_password, role, is_active)
VALUES ('admin', 'admin@fitcore.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYfZvJ8kYoS', 'admin123', 'admin', true);
```

Login with: `admin` / `admin123`

## Troubleshooting

### Check Error Logs:
- Go to "Web" tab
- Click "Error log" link
- Check for Python errors

### Check Server Log:
- Go to "Web" tab  
- Click "Server log" link

### Common Issues:

**Import errors**: Make sure virtualenv path is correct

**Database connection fails**: Check DATABASE_URL in .env

**Static files not loading**: Verify static file mappings

**CORS errors**: Check FRONTEND_URL in backend/.env

## Updating Your App

When you make changes:

```bash
cd ~/MODERN-FITNESS-GYM
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
cd frontend
npm run build
```

Then reload web app from "Web" tab.

## Free Tier Limits

- PythonAnywhere: 512MB storage, 100 seconds CPU/day
- Supabase: 500MB database, 2GB bandwidth

Perfect for small gym (100-200 members).

## Your URLs

- App: `https://YOUR_USERNAME.pythonanywhere.com`
- API: `https://YOUR_USERNAME.pythonanywhere.com/api`

Done! Much simpler than Vercel.
