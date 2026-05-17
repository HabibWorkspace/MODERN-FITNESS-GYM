# 📱 FOR GYM OWNER - Android Device Setup

## ⚠️ IMPORTANT: This is for the ANDROID DEVICE, not your computer!

---

## What You Need:

1. ✅ An Android phone or tablet (Android 7.0 or higher)
2. ✅ The device connected to the same WiFi as your iFace950 attendance machine
3. ✅ A charger to keep the device plugged in 24/7
4. ✅ 15 minutes for setup

---

## Step 1: Install Termux on Android Device

### On the Android Device:

1. **Download F-Droid app:**
   - Open browser on Android
   - Go to: **https://f-droid.org/**
   - Tap "Download F-Droid"
   - Install the APK file

2. **Install Termux from F-Droid:**
   - Open F-Droid app
   - Search for "Termux"
   - Tap "Install"
   - Wait for installation to complete

3. **Open Termux:**
   - You'll see a black screen with text (like a command prompt)
   - This is normal!

---

## Step 2: Install Required Software

### In Termux (on Android), type these commands ONE BY ONE:

**Command 1:** Update packages
```bash
pkg update -y
```
Wait for it to finish (may take 1-2 minutes)

**Command 2:** Upgrade packages
```bash
pkg upgrade -y
```
Wait for it to finish

**Command 3:** Install Python
```bash
pkg install -y python
```
Wait for it to finish

**Command 4:** Install other tools
```bash
pkg install -y git clang libffi openssl
```
Wait for it to finish

**Command 5:** Install Python libraries
```bash
pip install pyzk requests python-dotenv
```
Wait for it to finish (may take 2-3 minutes)

**Command 7:** Create project folder
```bash
mkdir -p ~/gym-sync
```

**Command 8:** Keep device awake
```bash
termux-wake-lock
```

✅ **Installation complete!**

---

## Step 3: Get the Files

### Option A: USB Cable (Easiest)

1. **Connect Android to your computer with USB cable**

2. **On Android:**
   - Swipe down from top
   - Tap "USB" notification
   - Select "File Transfer"

3. **On Computer:**
   - Open File Explorer
   - Find your Android device
   - Open "Internal Storage" → "Download" folder
   - Copy these files from computer to Android Downloads:
     - `android_device_sync.py`
     - `.env` (create from .env.example)

4. **In Termux on Android:**
   ```bash
   termux-setup-storage
   ```
   (Grant permission when asked)
   
   ```bash
   cd ~/gym-sync
   cp ~/storage/downloads/android_device_sync.py .
   cp ~/storage/downloads/.env .
   ```

### Option B: Create Files Directly in Termux

1. **Create configuration file:**
   ```bash
   cd ~/gym-sync
   nano .env
   ```

2. **Type this (or copy-paste):**
   ```
   PYTHONANYWHERE_URL=https://habibworkspace.pythonanywhere.com
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=admin22@@
   BIOMETRIC_DEVICE_IP=192.168.0.201
   BIOMETRIC_DEVICE_PORT=4370
   SYNC_INTERVAL=3
   PUSHER_APP_ID=2142303
   PUSHER_KEY=8f96a097d2f6d11c1a34
   PUSHER_SECRET=97a957c4a520fe63a10e
   PUSHER_CLUSTER=mt1
   ```

3. **Save the file:**
   - Press `Volume Down + X` (or `Ctrl + X`)
   - Press `Y`
   - Press `Enter`

4. **Create the sync script:**
   - I'll send you the `android_device_sync.py` file separately
   - Copy it to the Android device using USB method above

---

## Step 4: Start the Sync

```bash
cd ~/gym-sync
python android_device_sync.py
```

### You should see:

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

Starting sync loop...
✓ Synced attendance log for user 1
✓ Synced attendance log for user 2
```

**🎉 Success!** Your attendance is now syncing automatically!

---

## Step 5: Keep It Running 24/7

### Prevent Android from Stopping Termux:

1. **Go to Android Settings:**
   - Settings → Apps → Termux
   - Battery → Select "Unrestricted"
   - This prevents Android from killing Termux

2. **Keep device plugged in:**
   - Connect to charger
   - The device will run 24/7

3. **Screen can turn off:**
   - The sync continues even with screen off
   - You can lock the device

---

## Step 6: Auto-Start on Boot (Optional)

### Install Termux:Boot:

1. **In F-Droid app:**
   - Search "Termux:Boot"
   - Install it
   - Open it once (just to activate)

2. **In Termux:**
   ```bash
   mkdir -p ~/.termux/boot
   nano ~/.termux/boot/start-sync.sh
   ```

3. **Type this:**
   ```bash
   #!/data/data/com.termux/files/usr/bin/bash
   termux-wake-lock
   sleep 30
   cd ~/gym-sync
   python android_device_sync.py > ~/gym-sync/sync.log 2>&1 &
   ```

4. **Save:** Press `Volume Down + X`, then `Y`, then `Enter`

5. **Make it executable:**
   ```bash
   chmod +x ~/.termux/boot/start-sync.sh
   ```

**Now it starts automatically when device boots!**

---

## 📊 How to Check if It's Working

### View the logs:
```bash
tail -f ~/gym-sync/sync.log
```

### Check if running:
```bash
ps aux | grep python
```

### Stop the sync:
```bash
pkill -f android_device_sync.py
```

### Restart the sync:
```bash
cd ~/gym-sync
python android_device_sync.py &
```

---

## ⚠️ Troubleshooting

### "Can't connect to device"
- Make sure Android is on same WiFi as iFace950
- Check if IP address is correct: `192.168.100.35`
- Try: `ping 192.168.100.35`

### "Authentication failed"
- Check username and password in .env file
- Make sure admin account exists on website

### "Termux keeps closing"
- Go to Settings → Apps → Termux → Battery → Unrestricted
- Run: `termux-wake-lock`

### "Module not found"
```bash
pip install --upgrade pyzk requests python-dotenv
```

---

## 🔋 Battery & Power Tips

- ✅ Keep device plugged into charger 24/7
- ✅ Set screen timeout to 30 seconds (saves power)
- ✅ Disable battery optimization for Termux
- ✅ The sync runs even with screen off
- ✅ You can lock the device

---

## 📞 Need Help?

1. Check the logs: `tail -f ~/gym-sync/sync.log`
2. Make sure WiFi is connected
3. Make sure device is on same network as iFace950
4. Restart the sync service

---

## ✅ Final Checklist

- [ ] Termux installed from F-Droid
- [ ] All packages installed (python, pyzk, etc.)
- [ ] Files copied to ~/gym-sync folder
- [ ] .env file configured with correct settings
- [ ] Sync running and showing "✓ Connected"
- [ ] Battery optimization disabled for Termux
- [ ] Device plugged into charger
- [ ] Auto-start configured (optional)

---

**That's it!** Your Android device is now syncing attendance data from the iFace950 to your web app automatically. 🎉

The device can stay in a drawer or on a shelf - it just needs to be:
- ✅ On the same WiFi network
- ✅ Plugged into power
- ✅ Running Termux in background

---

**Questions?** Check the TROUBLESHOOTING.md file or contact your developer.
