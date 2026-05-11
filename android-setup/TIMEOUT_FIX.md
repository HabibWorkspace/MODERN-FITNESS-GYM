# Timeout Error - Troubleshooting Guide

## What "Timeout" Means

The Android device **cannot reach** the iFace950 device at `192.168.0.201:4270`.

This is a **network connectivity issue**, not a code problem.

---

## 🔍 Step 1: Check Network Connection

### On Android (in Termux):

```bash
# Test if you can reach the device
ping 192.168.0.201
```

**Expected Result:**
```
64 bytes from 192.168.0.201: icmp_seq=1 ttl=64 time=5.2 ms
64 bytes from 192.168.0.201: icmp_seq=2 ttl=64 time=4.8 ms
```

**If you see "timeout" or "unreachable":**
- ❌ Android device CANNOT reach iFace950
- Network issue needs to be fixed first

**Press Ctrl+C to stop ping**

---

## 🔧 Common Causes & Solutions

### Cause 1: Different WiFi Networks ⚠️

**Problem:** Android and iFace950 are on different networks.

**Check:**
- Android WiFi: Settings → WiFi → Check network name
- iFace950 IP: Should be `192.168.0.201`

**Solution:**
- Connect Android to the SAME WiFi as iFace950
- Both must be on `192.168.0.x` network

---

### Cause 2: Wrong IP Address ⚠️

**Problem:** iFace950 IP changed or is incorrect.

**Check on iFace950 Device:**
1. Menu → Comm → TCP/IP
2. Look at IP Address
3. Is it `192.168.0.201`?

**If Different:**
Update `.env` file on Android:
```bash
cd ~/downloads
nano .env
# Change BIOMETRIC_DEVICE_IP to the correct IP
```

---

### Cause 3: AP Isolation Enabled ⚠️

**Problem:** Router blocks device-to-device communication.

**Check Router Settings:**
1. Log into router (usually `192.168.0.1`)
2. Look for "AP Isolation" or "Client Isolation"
3. If enabled, **disable it**

**Common Router IPs:**
- `192.168.0.1`
- `192.168.1.1`
- `192.168.100.1`

---

### Cause 4: Firewall on iFace950 ⚠️

**Problem:** Device firewall blocking connections.

**Check on iFace950:**
1. Menu → Comm → Comm Opt
2. Check if "Firewall" is enabled
3. If yes, disable or add Android IP to whitelist

---

### Cause 5: Wrong Port ⚠️

**Problem:** Port number is incorrect.

**Check on iFace950:**
1. Menu → Comm → Comm Opt
2. Look at TCP Port
3. Should be `4270` (as you configured)

**If Different:**
Update `.env` on Android:
```bash
nano .env
# Change BIOMETRIC_DEVICE_PORT to correct port
```

---

### Cause 6: Device Not Responding ⚠️

**Problem:** iFace950 is offline or frozen.

**Solution:**
1. Check if device screen is on
2. Try accessing device menu
3. Restart device if needed (Menu → System → Restart)

---

## 📊 Diagnostic Commands

### On Android (in Termux):

```bash
# 1. Check your Android IP
ifconfig wlan0 | grep inet

# Should show something like:
# inet addr:192.168.0.XXX

# 2. Check if you can reach router
ping 192.168.0.1

# 3. Check if you can reach iFace950
ping 192.168.0.201

# 4. Check if port is open (requires nmap)
pkg install nmap
nmap -p 4270 192.168.0.201
```

---

## ✅ Quick Checklist

Run through this checklist:

- [ ] Android connected to WiFi
- [ ] Android IP is `192.168.0.XXX` (same subnet)
- [ ] Can ping router: `ping 192.168.0.1`
- [ ] Can ping iFace950: `ping 192.168.0.201`
- [ ] iFace950 IP is correct (check on device)
- [ ] iFace950 port is `4270` (check on device)
- [ ] AP Isolation is disabled on router
- [ ] iFace950 device is powered on and responsive

---

## 🎯 Most Likely Issues

### Issue 1: Different WiFi Networks (90% of cases)

**Symptoms:**
- Ping fails
- Timeout error
- Works on PC but not Android

**Solution:**
Connect Android to the SAME WiFi network as iFace950.

**How to Check:**
```bash
# On Android
ifconfig wlan0 | grep inet
# Should show: 192.168.0.XXX

# If it shows 192.168.1.XXX or different, wrong network!
```

---

### Issue 2: AP Isolation (5% of cases)

**Symptoms:**
- Can ping router
- Cannot ping iFace950
- Both on same network

**Solution:**
Disable AP Isolation in router settings.

---

### Issue 3: Wrong IP/Port (5% of cases)

**Symptoms:**
- Ping works
- Sync times out

**Solution:**
Verify IP and port on iFace950 device.

---

## 🔧 Step-by-Step Fix

### Step 1: Verify Network

```bash
# On Android
ping 192.168.0.201
```

**If ping works:** Go to Step 2  
**If ping fails:** Fix network first (see causes above)

### Step 2: Verify Port

```bash
# Install nmap
pkg install nmap

# Check if port is open
nmap -p 4270 192.168.0.201
```

**Expected:**
```
4270/tcp open
```

**If closed:** Check port number on iFace950

### Step 3: Test Connection

```bash
# Try connecting with longer timeout
cd ~/downloads
nano .env

# Change timeout in script or increase SYNC_INTERVAL
SYNC_INTERVAL=10
```

### Step 4: Run Sync

```bash
python android_device_sync_simple.py
```

---

## 📱 Compare with PC

Since it works on your PC:

### On Your PC:

```bash
# Check your PC's IP
ipconfig

# Note the IP (e.g., 192.168.0.185)
```

### On Android:

```bash
# Check Android's IP
ifconfig wlan0 | grep inet

# Compare with PC's IP
# Should be in same range (192.168.0.XXX)
```

**If different ranges:**
- PC: `192.168.0.185` ✅
- Android: `192.168.1.100` ❌

**Solution:** Connect Android to same WiFi as PC.

---

## 🆘 Emergency Solution

If you can't fix the network issue, use your PC as a proxy:

### Option 1: Use PC as Bridge

Run this on your PC:
```bash
cd "C:\Users\habib\OneDrive\Desktop\Projects\MODERN FITNESS GYM\backend"
python local_device_sync.py
```

This works because your PC can reach the device.

### Option 2: Hotspot from PC

1. Create WiFi hotspot from your PC
2. Connect Android to PC's hotspot
3. Connect iFace950 to PC's hotspot
4. Now all on same network

---

## 📞 What to Tell Gym Owner

**Simple Instructions:**

1. **Check WiFi:**
   - "Make sure your Android phone is connected to the same WiFi as the attendance machine"

2. **Test Connection:**
   ```bash
   ping 192.168.0.201
   ```
   - "You should see numbers appearing every second"
   - "If you see 'timeout', the phone can't reach the machine"

3. **Fix Network:**
   - "Connect to the correct WiFi network"
   - "Ask your IT person to disable 'AP Isolation' on the router"

---

## 🎓 Understanding the Error

```
Timeout Error = Cannot reach device
Broken Pipe Error = Connection drops unexpectedly
```

**Timeout is easier to fix** - it's just a network configuration issue!

---

## ✅ Success Criteria

When network is fixed, you'll see:

```bash
ping 192.168.0.201
# 64 bytes from 192.168.0.201: time=5ms ✅
```

Then sync will work:
```bash
python android_device_sync_simple.py
# ✓ Connected to device ✅
# ✓ Synced attendance log ✅
```

---

**Bottom Line:** Fix the network connection first, then the sync will work!
