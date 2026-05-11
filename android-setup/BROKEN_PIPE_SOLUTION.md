# Broken Pipe Error - FINAL SOLUTION ✅

## The Problem

Android/Termux has issues with TCP connections to ZKTeco devices, causing "Broken Pipe" errors.

## The Solution

I've created **TWO versions** of the sync script. Try them in order:

---

## ✅ Solution 1: UDP Mode (Try This First)

The updated `android_device_sync.py` now uses **UDP instead of TCP**, which is more reliable on Android.

### On Android (in Termux):

```bash
# Stop old sync if running
pkill -f android_device_sync.py

# Transfer the NEW android_device_sync.py to your device
# (It now uses UDP mode)

# Run it
cd ~/downloads
python android_device_sync.py
```

**What changed:**
- ✅ Uses UDP protocol (more Android-friendly)
- ✅ Shorter connection lifetime (20 seconds)
- ✅ Better retry logic
- ✅ Improved error handling

---

## ✅ Solution 2: Simple Version (If UDP Still Fails)

If you still get Broken Pipe errors, use the **SIMPLE version** that connects/disconnects for each sync cycle.

### Transfer the Simple Version:

1. Copy `android_device_sync_simple.py` to your Android device
2. Run it instead:

```bash
cd ~/downloads
python android_device_sync_simple.py
```

**How it works:**
1. Connect to device
2. Fetch all attendance logs
3. **Disconnect immediately**
4. Sync to PythonAnywhere
5. Wait 5 seconds
6. Repeat

**Advantages:**
- ✅ No persistent connection = No Broken Pipe
- ✅ More reliable on Android
- ✅ Slightly slower but works

**Disadvantages:**
- ⚠️ Connects/disconnects every 5 seconds
- ⚠️ Slightly more load on device

---

## Comparison

| Version | Connection | Speed | Reliability |
|---------|-----------|-------|-------------|
| **Original** | TCP persistent | Fast | ❌ Broken Pipe |
| **UDP Mode** | UDP persistent | Fast | ✅ Better |
| **Simple** | Connect/Disconnect | Slower | ✅ Most Reliable |

---

## Recommended Approach

### Step 1: Try UDP Mode

```bash
cd ~/downloads
python android_device_sync.py
```

Watch for "Broken Pipe" errors. If you see them, go to Step 2.

### Step 2: Use Simple Version

```bash
cd ~/downloads
python android_device_sync_simple.py
```

This should work without any Broken Pipe errors.

---

## Configuration

Both versions use the same `.env` file:

```env
PYTHONANYWHERE_URL=https://habibworkspace.pythonanywhere.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin22@@
BIOMETRIC_DEVICE_IP=192.168.0.201
BIOMETRIC_DEVICE_PORT=4270
SYNC_INTERVAL=5
PUSHER_APP_ID=2142303
PUSHER_KEY=8f96a097d2f6d11c1a34
PUSHER_SECRET=97a957c4a520fe63a10e
PUSHER_CLUSTER=mt1
```

**Note:** Simple version uses 5-second interval by default (instead of 3).

---

## What You'll See

### UDP Mode (android_device_sync.py):
```
BiometricDeviceClient initialized for 192.168.0.201:4270 (UDP mode for Android)
✓ Authenticated with PythonAnywhere
✓ Connected to biometric device
✓ Synced attendance log for user 1
Connection is stale, reconnecting...
✓ Connected to biometric device
✓ Synced attendance log for user 2
```

### Simple Version (android_device_sync_simple.py):
```
Android Device Sync Service - SIMPLE VERSION
Mode: UDP (Android optimized)
This version connects/disconnects each time to avoid Broken Pipe

--- Cycle 1 ---
Connecting to 192.168.0.201:4270...
✓ Connected to device
Fetched 5 total records from device
✓ Disconnected from device
✓ Synced: User 1 at 2024-05-12 10:30:00
✓ Synced 1 new records (Total: 1)

--- Cycle 2 ---
Connecting to 192.168.0.201:4270...
✓ Connected to device
...
```

---

## Troubleshooting

### Still Getting Broken Pipe with Simple Version?

This shouldn't happen, but if it does:

**1. Check pyzk version:**
```bash
pip show pyzk
```

**2. Reinstall pyzk:**
```bash
pip uninstall pyzk
pip install pyzk
```

**3. Try different timeout:**

Edit the script, find this line:
```python
zk = ZK(DEVICE_IP, port=DEVICE_PORT, timeout=10, force_udp=True, ommit_ping=True)
```

Change timeout to 15:
```python
zk = ZK(DEVICE_IP, port=DEVICE_PORT, timeout=15, force_udp=True, ommit_ping=True)
```

### Connection Timeout?

Increase `SYNC_INTERVAL` in `.env`:
```env
SYNC_INTERVAL=10  # 10 seconds instead of 5
```

### Device Not Responding?

Check if device is reachable:
```bash
ping 192.168.0.201
```

---

## Which Version Should You Use?

**For Best Performance:**
- Try UDP mode first (`android_device_sync.py`)
- If it works without errors, use this

**For Maximum Reliability:**
- Use Simple version (`android_device_sync_simple.py`)
- Guaranteed to avoid Broken Pipe
- Slightly slower but rock solid

---

## Files Summary

| File | Purpose | When to Use |
|------|---------|-------------|
| `android_device_sync.py` | UDP mode, persistent connection | Try first |
| `android_device_sync_simple.py` | Connect/disconnect each cycle | If UDP fails |

---

## Final Notes

The Simple version is specifically designed for Android/Termux environments where TCP connections are problematic. It sacrifices a bit of speed for maximum reliability.

**Both versions:**
- ✅ Sync to PythonAnywhere
- ✅ Handle authentication
- ✅ Track synced records
- ✅ Log all activity
- ✅ Work with same .env file

Choose the one that works best for you!

---

**Need help?** Check the logs:
```bash
tail -f ~/downloads/sync.log
```
