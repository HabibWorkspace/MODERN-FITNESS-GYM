# Troubleshooting Guide - Android Device Sync

## Common Issues and Solutions

---

## 🔴 Connection Issues

### Issue: "Failed to connect to biometric device"

**Symptoms:**
```
✗ Failed to connect to biometric device at 192.168.100.35:4370
```

**Solutions:**

1. **Check WiFi Connection:**
   ```bash
   # Test if device is reachable
   ping 192.168.100.35
   ```
   - Ensure Android is on the same WiFi network as iFace950
   - Check if WiFi is stable (not sleeping)

2. **Verify Device IP:**
   - Check iFace950 device settings for correct IP
   - Update `.env` file if IP changed:
   ```bash
   nano ~/gym-sync/.env
   # Update BIOMETRIC_DEVICE_IP
   ```

3. **Check Device Port:**
   - Default ZKTeco port is 4370
   - Verify in device settings

4. **Firewall/Network Issues:**
   - Some routers block device-to-device communication
   - Try connecting Android to device's network directly
   - Check if router has "AP Isolation" enabled (disable it)

---

## 🔴 Authentication Issues

### Issue: "Authentication failed"

**Symptoms:**
```
✗ Authentication failed: 401
```

**Solutions:**

1. **Check Credentials:**
   ```bash
   nano ~/gym-sync/.env
   # Verify ADMIN_USERNAME and ADMIN_PASSWORD
   ```

2. **Test Login Manually:**
   ```bash
   curl -X POST https://habibworkspace.pythonanywhere.com/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin22@@"}'
   ```

3. **Check PythonAnywhere Status:**
   - Visit: https://habibworkspace.pythonanywhere.com
   - Ensure site is running

4. **Password Special Characters:**
   - If password has special characters, ensure they're properly escaped in .env

---

## 🔴 Module/Import Errors

### Issue: "ModuleNotFoundError: No module named 'zk'"

**Symptoms:**
```
✗ Failed to import pyzk library
```

**Solutions:**

1. **Reinstall pyzk:**
   ```bash
   pip install --upgrade pyzk
   ```

2. **Install with dependencies:**
   ```bash
   pip install pyzk requests python-dotenv
   ```

3. **Check Python version:**
   ```bash
   python --version
   # Should be 3.7 or higher
   ```

4. **Clear pip cache and reinstall:**
   ```bash
   pip install --no-cache-dir pyzk
   ```

---

## 🔴 Termux Keeps Closing

### Issue: Sync stops when screen turns off

**Solutions:**

1. **Acquire Wake Lock:**
   ```bash
   termux-wake-lock
   ```

2. **Disable Battery Optimization:**
   - Settings → Apps → Termux
   - Battery → Unrestricted (or "Don't optimize")

3. **Install Termux:Wake Lock:**
   - Download from F-Droid
   - Provides better wake lock control

4. **Run as Background Service:**
   ```bash
   cd ~/gym-sync
   python android_device_sync.py > sync.log 2>&1 &
   ```

5. **Disable Doze Mode for Termux:**
   - Settings → Battery → Battery optimization
   - Find Termux → Don't optimize

---

## 🔴 Network Timeout Issues

### Issue: "Connection timeout" or "Request timeout"

**Solutions:**

1. **Increase Timeout:**
   Edit `android_device_sync.py`:
   ```python
   # Change timeout from 10 to 30 seconds
   timeout=30
   ```

2. **Check Internet Connection:**
   ```bash
   ping google.com
   curl https://habibworkspace.pythonanywhere.com
   ```

3. **WiFi Sleep Settings:**
   - Settings → WiFi → Advanced
   - Keep WiFi on during sleep: Always

4. **Mobile Data Backup:**
   - Enable mobile data as backup
   - Settings → Apps → Termux → Mobile data: Allow

---

## 🔴 Sync Not Working

### Issue: No attendance records syncing

**Symptoms:**
```
Synced 0 new attendance logs
```

**Solutions:**

1. **Check Device Mappings:**
   - Ensure device users are mapped in the system
   - Visit: https://habibworkspace.pythonanywhere.com/attendance/mappings

2. **Verify Device Has Logs:**
   - Check iFace950 device directly
   - Ensure attendance logs exist

3. **Check Sync Status:**
   ```bash
   tail -f ~/gym-sync/sync.log
   ```

4. **Manual Sync Test:**
   - Try syncing from web interface
   - Check if backend is receiving data

---

## 🔴 Storage/Permission Issues

### Issue: "Permission denied" errors

**Solutions:**

1. **Grant Storage Permission:**
   ```bash
   termux-setup-storage
   # Grant permission when prompted
   ```

2. **Check File Permissions:**
   ```bash
   cd ~/gym-sync
   chmod 644 .env
   chmod 755 android_device_sync.py
   ```

3. **Reinstall Termux:**
   - Backup your files first
   - Uninstall and reinstall from F-Droid

---

## 🔴 High Battery Drain

### Issue: Android device battery draining fast

**Solutions:**

1. **Keep Device Plugged In:**
   - This is a 24/7 service, should stay on charger

2. **Reduce Sync Frequency:**
   ```bash
   nano ~/gym-sync/.env
   # Change SYNC_INTERVAL from 3 to 10 seconds
   SYNC_INTERVAL=10
   ```

3. **Lower Screen Brightness:**
   - Settings → Display → Brightness: Minimum

4. **Disable Unnecessary Apps:**
   - Close other apps running in background

---

## 🔴 Auto-Start Not Working

### Issue: Sync doesn't start on device boot

**Solutions:**

1. **Install Termux:Boot:**
   - Must be from F-Droid (not Play Store)
   - Open Termux:Boot once to activate

2. **Check Boot Script:**
   ```bash
   cat ~/.termux/boot/start-sync.sh
   # Should contain the startup commands
   ```

3. **Make Script Executable:**
   ```bash
   chmod +x ~/.termux/boot/start-sync.sh
   ```

4. **Test Boot Script Manually:**
   ```bash
   ~/.termux/boot/start-sync.sh
   ```

5. **Check Android Auto-Start Settings:**
   - Settings → Apps → Termux:Boot
   - Ensure "Auto-start" is enabled

---

## 🔴 Logs Not Showing

### Issue: Can't see sync logs

**Solutions:**

1. **Check Log File Location:**
   ```bash
   ls -la ~/gym-sync/sync.log
   ```

2. **View Logs:**
   ```bash
   tail -f ~/gym-sync/sync.log
   ```

3. **If No Log File:**
   ```bash
   cd ~/gym-sync
   python android_device_sync.py 2>&1 | tee sync.log
   ```

---

## 🔴 Duplicate Records

### Issue: Same attendance logged multiple times

**Solutions:**

1. **Check Backend Logic:**
   - Backend should prevent duplicates
   - Check `/api/attendance/sync-log` endpoint

2. **Clear Device Logs:**
   - After successful sync, clear device logs
   - Prevents re-syncing old records

3. **Restart Sync Service:**
   ```bash
   pkill -f android_device_sync.py
   cd ~/gym-sync
   python android_device_sync.py
   ```

---

## 🔴 Slow Performance

### Issue: Sync is very slow

**Solutions:**

1. **Check Network Speed:**
   ```bash
   # Install speedtest
   pip install speedtest-cli
   speedtest-cli
   ```

2. **Reduce Sync Interval:**
   - If network is slow, increase interval
   ```bash
   nano ~/gym-sync/.env
   SYNC_INTERVAL=10
   ```

3. **Close Other Apps:**
   - Free up device resources

4. **Restart Device:**
   - Sometimes helps with performance

---

## 📊 Diagnostic Commands

### Check Everything:

```bash
# Check if sync is running
ps aux | grep python

# Check network connectivity
ping 192.168.100.35
ping google.com

# Check logs
tail -20 ~/gym-sync/sync.log

# Check environment variables
cat ~/gym-sync/.env

# Check Python packages
pip list | grep -E "pyzk|requests|dotenv"

# Check Termux wake lock
termux-wake-status

# Check disk space
df -h

# Check memory
free -h
```

---

## 🆘 Emergency Reset

If nothing works, start fresh:

```bash
# Stop sync
pkill -f android_device_sync.py

# Backup .env
cp ~/gym-sync/.env ~/gym-sync/.env.backup

# Remove everything
rm -rf ~/gym-sync

# Reinstall
mkdir -p ~/gym-sync
cd ~/gym-sync

# Restore .env
cp ~/gym-sync/.env.backup .env

# Reinstall packages
pip install --upgrade pyzk requests python-dotenv

# Copy sync script again
# (transfer android_device_sync.py)

# Start fresh
python android_device_sync.py
```

---

## 📞 Getting Help

### Information to Provide:

1. **Error message:**
   ```bash
   tail -50 ~/gym-sync/sync.log
   ```

2. **Environment:**
   ```bash
   python --version
   pip list
   cat ~/gym-sync/.env  # Remove passwords before sharing!
   ```

3. **Network status:**
   ```bash
   ping 192.168.100.35
   curl https://habibworkspace.pythonanywhere.com
   ```

4. **Device info:**
   - Android version
   - Device model
   - Termux version

---

## ✅ Health Check Script

Create a health check script:

```bash
nano ~/gym-sync/health_check.sh
```

Paste:

```bash
#!/data/data/com.termux/files/usr/bin/bash

echo "=== Gym Sync Health Check ==="
echo ""

echo "1. Sync Process:"
ps aux | grep python | grep -v grep && echo "✓ Running" || echo "✗ Not running"
echo ""

echo "2. Network - Device:"
ping -c 1 192.168.100.35 > /dev/null 2>&1 && echo "✓ Device reachable" || echo "✗ Device unreachable"
echo ""

echo "3. Network - Internet:"
ping -c 1 google.com > /dev/null 2>&1 && echo "✓ Internet connected" || echo "✗ No internet"
echo ""

echo "4. Backend:"
curl -s https://habibworkspace.pythonanywhere.com > /dev/null && echo "✓ Backend reachable" || echo "✗ Backend unreachable"
echo ""

echo "5. Recent Logs:"
tail -5 ~/gym-sync/sync.log
echo ""

echo "=== End Health Check ==="
```

Make executable:
```bash
chmod +x ~/gym-sync/health_check.sh
```

Run anytime:
```bash
~/gym-sync/health_check.sh
```

---

**Still having issues?** Check the logs carefully - they usually tell you exactly what's wrong!
