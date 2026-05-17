# 🔧 Local Testing Setup - Android Device Sync

## Problem: Device Shows "Offline" When Testing Locally

When running the backend on your local machine (`http://127.0.0.1:5001`), the Android tablet can't reach it because:
- `127.0.0.1` only works on the same machine
- Android tablet needs your machine's **network IP address**

## Solution: Use Your Machine's Network IP

### Step 1: Find Your Machine's Network IP

**On Windows:**
```powershell
ipconfig | Select-String "IPv4 Address"
```

Look for output like:
```
IPv4 Address. . . . . . . . . . . : 172.20.176.1
```

**Your IP is: `172.20.176.1`** (yours will be different)

### Step 2: Update Android `.env` File

Create or edit `android-setup/.env`:

```env
# LOCAL TESTING - Points to your PC
PYTHONANYWHERE_URL=http://172.20.176.1:5001
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Biometric Device Configuration
BIOMETRIC_DEVICE_IP=192.168.0.201
BIOMETRIC_DEVICE_PORT=4370

# Sync Configuration
SYNC_INTERVAL=2
```

**Replace `172.20.176.1` with YOUR machine's IP address!**

### Step 3: Start Backend on All Network Interfaces

The backend must listen on `0.0.0.0` (all interfaces), not just `127.0.0.1`.

**Run:**
```bash
python run_simple.py
```

**You should see:**
```
🚀 Starting Flask server on http://0.0.0.0:5001
📱 Android tablet can reach at: http://172.20.176.1:5001
💻 Local browser can reach at: http://127.0.0.1:5001
```

### Step 4: Test Connection from Android Tablet

**In Termux on Android:**
```bash
curl http://172.20.176.1:5001/api/health
```

**Should return:**
```json
{"status":"healthy","message":"FitCore backend is running"}
```

### Step 5: Run Android Sync Script

**In Termux on Android:**
```bash
cd ~/gym-sync
python sync.py
```

**You should see:**
```
✓ Authenticated successfully
✓ PERMANENT CONNECTION ESTABLISHED (Serial: ABC123)
✓ SYNCED: User 1 at 14:30:45
```

### Step 6: Verify Device Status in Dashboard

1. Open FitCore dashboard
2. Go to **Attendance Dashboard**
3. Look for **"Device Online"** indicator
4. Should now show **GREEN** (Online)

---

## Network Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    WiFi Network                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Your PC (172.20.176.1:5001)                           │
│  ├─ Backend running on 0.0.0.0:5001                    │
│  └─ Accessible at: http://172.20.176.1:5001            │
│                                                         │
│  Android Tablet (192.168.x.x)                          │
│  ├─ Termux running sync.py                             │
│  ├─ Connects to: http://172.20.176.1:5001              │
│  └─ Sends heartbeat every 30 seconds                   │
│                                                         │
│  iFace950 Device (192.168.0.201:4370)                  │
│  ├─ Biometric device                                   │
│  └─ Synced by Android tablet                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### "Connection refused" or "Timeout"

**Check 1: Is backend running?**
```bash
curl http://127.0.0.1:5001/api/health
```

**Check 2: Is backend listening on all interfaces?**
```bash
netstat -ano | findstr :5001
```

**Check 3: Can Android reach your PC?**
```bash
# In Termux on Android
ping 172.20.176.1
```

### "Device still shows Offline"

**Check 1: Is sync script running?**
```bash
# In Termux on Android
ps aux | grep sync.py
```

**Check 2: Check sync logs:**
```bash
# In Termux on Android
tail -f sync.log
```

**Check 3: Verify heartbeat is being sent:**
```bash
# In Termux on Android
curl -X POST http://172.20.176.1:5001/api/attendance/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"device_ip":"192.168.0.201"}'
```

### "No mapping found for device user"

This means the device user ID doesn't exist in the system.

**Solution:**
1. Go to **Admin → Device Mappings**
2. Add the user from the biometric device
3. Map it to a member or trainer

---

## Switching Between Local and Production

### For Local Testing:
```env
PYTHONANYWHERE_URL=http://172.20.176.1:5001
```

### For Production:
```env
PYTHONANYWHERE_URL=https://habibworkspace.pythonanywhere.com
```

Just update the `.env` file and restart the sync script!

---

## Performance Notes

- **Sync Interval**: 2 seconds (real-time)
- **Heartbeat**: Every 30 seconds
- **Connection**: Permanent (no auto-disconnect)
- **Reconnect**: Only on actual errors

---

## Next Steps

1. ✅ Update `.env` with your machine's IP
2. ✅ Start backend with `python run_simple.py`
3. ✅ Run sync script on Android tablet
4. ✅ Check device status in dashboard
5. ✅ Test attendance sync

**Device should now show as "Online"!** 🎉
