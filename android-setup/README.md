# Android Device Setup Guide for Attendance Sync

This guide will help you set up an Android device to sync attendance data from the iFace950 ZKT biometric device to your PythonAnywhere web app.

## Prerequisites

- Android device (phone or tablet) - Android 7.0 or higher
- The device should stay connected to the gym's WiFi network
- The device should be plugged into power (to run 24/7)

## Step 1: Install Termux

1. **Download Termux** from F-Droid (NOT from Google Play Store - it's outdated there)
   - Visit: https://f-droid.org/en/packages/com.termux/
   - Or download directly: https://f-droid.org/repo/com.termux_118.apk

2. **Install F-Droid** first if you don't have it:
   - Visit: https://f-droid.org/
   - Download and install F-Droid app
   - Then install Termux from F-Droid

3. **Open Termux** - you'll see a terminal interface

## Step 2: Install Required Packages

Copy and paste these commands one by one into Termux:

```bash
# Update package lists
pkg update -y

# Upgrade existing packages
pkg upgrade -y

# Install Python
pkg install python -y

# Install git
pkg install git -y

# Install required build tools
pkg install clang -y
pkg install libffi -y
pkg install openssl -y

# Install Python packages
pip install requests python-dotenv

# Install pyzk (ZKTeco device library)
pip install pyzk
```

**Note:** If you get any errors, try running each command separately and wait for it to complete.

## Step 3: Setup Wake Lock (Keep Device Awake)

To prevent Android from sleeping and stopping the sync:

```bash
# Install Termux:Boot (from F-Droid)
# This allows Termux to run on device startup

# Acquire wake lock in Termux
termux-wake-lock
```

Alternatively, install **Termux:Wake Lock** from F-Droid for better control.

## Step 4: Download Sync Script

```bash
# Create project directory
mkdir -p ~/gym-sync
cd ~/gym-sync

# Download the sync script (you'll need to transfer it)
# Option A: Use git if you have a repository
# git clone <your-repo-url> .

# Option B: We'll create the files manually (see next step)
```

## Step 5: Create Configuration Files

### Create .env file:

```bash
# Create .env file
nano .env
```

Paste this content (update with your actual values):

```env
# PythonAnywhere Configuration
PYTHONANYWHERE_URL=https://habibworkspace.pythonanywhere.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin22@@

# Biometric Device Configuration
BIOMETRIC_DEVICE_IP=192.168.100.35
BIOMETRIC_DEVICE_PORT=4370

# Sync Configuration
SYNC_INTERVAL=3

# Pusher Configuration (for real-time notifications)
PUSHER_APP_ID=2142303
PUSHER_KEY=8f96a097d2f6d11c1a34
PUSHER_SECRET=97a957c4a520fe63a10e
PUSHER_CLUSTER=mt1
```

**To save in nano:**
- Press `Ctrl + X`
- Press `Y` to confirm
- Press `Enter` to save

## Step 6: Transfer Sync Script

You have two options:

### Option A: Manual File Transfer

1. Connect your Android device to a computer via USB
2. Copy `android_device_sync.py` to the device
3. In Termux, move it to the right location:

```bash
cd ~/gym-sync
# If you copied to Downloads folder:
cp ~/storage/downloads/android_device_sync.py .
```

### Option B: Create File Directly in Termux

```bash
cd ~/gym-sync
nano android_device_sync.py
```

Then paste the content from the `android_device_sync.py` file (I'll create this next).

## Step 7: Setup Storage Access (for file transfer)

```bash
termux-setup-storage
```

This will prompt for storage permission - grant it. This allows Termux to access your device's storage.

## Step 8: Test the Sync

```bash
cd ~/gym-sync
python android_device_sync.py
```

You should see:
```
============================================================
Android Device Sync Service
============================================================
Device: 192.168.100.35:4370
Remote: https://habibworkspace.pythonanywhere.com
Sync Interval: 3s
============================================================

✓ Authenticated with PythonAnywhere
Connecting to biometric device...
✓ Connected to biometric device

Starting sync loop... (Press Ctrl+C to stop)
```

## Step 9: Run on Startup (Auto-start)

### Install Termux:Boot

1. Install **Termux:Boot** from F-Droid
2. Open Termux:Boot once to activate it
3. Create startup script:

```bash
mkdir -p ~/.termux/boot
nano ~/.termux/boot/start-sync.sh
```

Paste this content:

```bash
#!/data/data/com.termux/files/usr/bin/bash

# Acquire wake lock
termux-wake-lock

# Wait for network
sleep 30

# Start sync service
cd ~/gym-sync
python android_device_sync.py > ~/gym-sync/sync.log 2>&1 &
```

Make it executable:

```bash
chmod +x ~/.termux/boot/start-sync.sh
```

Now the sync will start automatically when the device boots!

## Step 10: Keep Screen Off (Save Battery)

The sync will run even with the screen off. To optimize:

1. Go to Android Settings → Display
2. Set screen timeout to 30 seconds
3. Keep device plugged into charger
4. The sync will continue running in background

## Monitoring and Maintenance

### Check if sync is running:

```bash
ps aux | grep python
```

### View sync logs:

```bash
cd ~/gym-sync
tail -f sync.log
```

### Stop sync:

```bash
pkill -f android_device_sync.py
```

### Restart sync:

```bash
cd ~/gym-sync
python android_device_sync.py &
```

## Troubleshooting

### Issue: "Connection refused" to biometric device

**Solution:**
- Ensure Android device is on the same WiFi network as the iFace950
- Check if device IP is correct: `192.168.100.35`
- Try pinging the device: `ping 192.168.100.35`

### Issue: "Authentication failed"

**Solution:**
- Check ADMIN_USERNAME and ADMIN_PASSWORD in .env file
- Ensure the admin user exists on PythonAnywhere

### Issue: Termux closes/stops

**Solution:**
- Run `termux-wake-lock` to prevent Android from killing the process
- Install Termux:Wake Lock from F-Droid
- Disable battery optimization for Termux in Android settings

### Issue: "Module not found" errors

**Solution:**
```bash
pip install --upgrade pyzk requests python-dotenv
```

### Issue: Sync stops after screen off

**Solution:**
- Disable battery optimization for Termux:
  - Settings → Apps → Termux → Battery → Unrestricted
- Use wake lock: `termux-wake-lock`

## Battery Optimization Settings

To ensure Termux runs continuously:

1. **Settings → Apps → Termux**
2. **Battery → Unrestricted** (or "Don't optimize")
3. **Mobile data** (if using mobile data as backup)
4. **Background data → Allow**

## Network Configuration

Ensure the Android device can reach both:
- ✅ Local device: `192.168.100.35:4370` (iFace950)
- ✅ Remote server: `https://habibworkspace.pythonanywhere.com`

Test connectivity:

```bash
# Test local device
ping 192.168.100.35

# Test remote server
curl https://habibworkspace.pythonanywhere.com/api/auth/login
```

## Security Notes

- The .env file contains sensitive credentials
- Keep the Android device in a secure location
- Consider changing default admin password
- The device should be on a trusted WiFi network

## Support

If you encounter issues:
1. Check the logs: `tail -f ~/gym-sync/sync.log`
2. Verify network connectivity
3. Ensure all packages are installed correctly
4. Restart Termux and try again

---

**Setup Complete!** 🎉

Your Android device is now acting as a bridge between the iFace950 biometric device and your PythonAnywhere web app, syncing attendance data every 3 seconds.
