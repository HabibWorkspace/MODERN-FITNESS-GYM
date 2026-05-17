# MANUAL DEPLOYMENT - Copy & Paste Commands

## Prerequisites
- PythonAnywhere account (HabibWorkSpace)
- SSH access enabled
- Password ready

---

## STEP 1: Upload Backend Files

Open PowerShell and run:

```powershell
$projectRoot = "c:\Users\habib\OneDrive\Desktop\Projects\MODERN FITNESS GYM"
$backendDir = "$projectRoot\backend"
$sshHost = "HabibWorkSpace@ssh.pythonanywhere.com"
$remotePath = "/home/HabibWorkSpace/MODERN-FITNESS-GYM"

scp -r "$backendDir" "${sshHost}:${remotePath}/"
```

**When prompted:** Enter your PythonAnywhere password

---

## STEP 2: Upload Frontend Files

```powershell
$frontendDir = "$projectRoot\frontend\dist"

scp -r "$frontendDir" "${sshHost}:${remotePath}/frontend/"
```

**When prompted:** Enter your PythonAnywhere password

---

## STEP 3: Apply Database Migrations

```powershell
ssh $sshHost "cd $remotePath/backend && alembic upgrade head"
```

**When prompted:** Enter your PythonAnywhere password

---

## STEP 4: Update WSGI Configuration

1. Go to: https://www.pythonanywhere.com/user/HabibWorkSpace/webapps/
2. Click on: habibworkspace.pythonanywhere.com
3. Find: "WSGI configuration file"
4. Click the file path to edit it
5. Replace content with:

```python
import sys
import os

path = '/home/HabibWorkSpace/MODERN-FITNESS-GYM/backend'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['FLASK_ENV'] = 'production'

from app_pythonanywhere import app
application = app
```

6. Save the file

---

## STEP 5: Reload Web App

1. Go to: https://www.pythonanywhere.com/user/HabibWorkSpace/webapps/
2. Click on: habibworkspace.pythonanywhere.com
3. Click: "Reload" button
4. Wait 10 seconds

---

## STEP 6: Verify Backend

Open browser and go to:
```
https://habibworkspace.pythonanywhere.com/api/health
```

Should see:
```json
{"status":"healthy","message":"Backend running"}
```

---

## STEP 7: Deploy Android Sync

1. Copy these files to Android tablet:
   - `android-setup/sync.py`
   - `android-setup/.env`

2. On Android (Termux):
```bash
cd ~/gym-sync
python sync.py
```

---

## STEP 8: Verify Everything

1. Open: https://habibworkspace.pythonanywhere.com
2. Login with admin credentials
3. Go to: Attendance Dashboard
4. Check: Device should show "Online" (green)
5. Scan member on biometric device
6. Check: Record appears in dashboard within 2 seconds

---

## TROUBLESHOOTING

### Backend not responding
- Check PythonAnywhere error log
- Verify WSGI file is correct
- Click "Reload" again

### Device shows "Offline"
- Check Android sync is running
- Check sync logs: `tail -f ~/gym-sync/sync.log`
- Verify `.env` has correct URL

### SSH Password Issues
- Use your PythonAnywhere password
- If you forgot it, reset at: https://www.pythonanywhere.com/account/

---

## DONE!

Your FitCore system is now deployed to PythonAnywhere!

Device should show "Online" once Android sync is running.
