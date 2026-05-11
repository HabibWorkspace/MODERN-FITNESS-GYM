# Quick Start Guide - Android Device Sync

## 🚀 5-Minute Setup

### Step 1: Install Termux (2 minutes)
1. Download **F-Droid** app: https://f-droid.org/
2. Open F-Droid → Search "Termux" → Install
3. Open Termux

### Step 2: Run Auto-Install Script (2 minutes)
Copy and paste this ONE command into Termux:

```bash
pkg update -y && pkg install -y python git clang libffi openssl && pip install --upgrade pip && pip install pyzk requests python-dotenv && mkdir -p ~/gym-sync && cd ~/gym-sync && termux-wake-lock && echo "✓ Installation complete!"
```

Wait for it to finish (may take 2-3 minutes).

### Step 3: Create Configuration (1 minute)

```bash
cd ~/gym-sync
nano .env
```

Paste this (update IP if different):

```env
PYTHONANYWHERE_URL=https://habibworkspace.pythonanywhere.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin22@@
BIOMETRIC_DEVICE_IP=192.168.100.35
BIOMETRIC_DEVICE_PORT=4370
SYNC_INTERVAL=3
PUSHER_APP_ID=2142303
PUSHER_KEY=8f96a097d2f6d11c1a34
PUSHER_SECRET=97a957c4a520fe63a10e
PUSHER_CLUSTER=mt1
```

**Save:** Press `Ctrl+X`, then `Y`, then `Enter`

### Step 4: Transfer Sync Script

**Option A - USB Transfer:**
1. Connect Android to computer via USB
2. Copy `android_device_sync.py` to device Downloads folder
3. In Termux:
```bash
termux-setup-storage
# Grant permission when prompted
cp ~/storage/downloads/android_device_sync.py ~/gym-sync/
```

**Option B - Manual Creation:**
```bash
cd ~/gym-sync
nano android_device_sync.py
# Paste the content from android_device_sync.py file
# Save with Ctrl+X, Y, Enter
```

### Step 5: Start Sync

```bash
cd ~/gym-sync
python android_device_sync.py
```

You should see:
```
✓ Authenticated with PythonAnywhere
✓ Connected to biometric device
Starting sync loop...
```

**Done!** 🎉 The device is now syncing attendance data.

---

## 📱 Keep It Running 24/7

### Prevent Android from Killing Termux:

1. **Disable Battery Optimization:**
   - Settings → Apps → Termux → Battery → **Unrestricted**

2. **Keep Wake Lock Active:**
   ```bash
   termux-wake-lock
   ```

3. **Run in Background:**
   ```bash
   cd ~/gym-sync
   python android_device_sync.py > sync.log 2>&1 &
   ```
   Now you can close Termux and it keeps running!

---

## 🔄 Auto-Start on Device Boot

### Install Termux:Boot:
1. Open F-Droid → Search "Termux:Boot" → Install
2. Open Termux:Boot once to activate
3. In Termux:

```bash
mkdir -p ~/.termux/boot
nano ~/.termux/boot/start-sync.sh
```

Paste:
```bash
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
sleep 30
cd ~/gym-sync
python android_device_sync.py > ~/gym-sync/sync.log 2>&1 &
```

Make executable:
```bash
chmod +x ~/.termux/boot/start-sync.sh
```

**Now it starts automatically when device boots!**

---

## 🛠️ Common Commands

### Check if running:
```bash
ps aux | grep python
```

### View logs:
```bash
tail -f ~/gym-sync/sync.log
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

---

## ⚠️ Troubleshooting

### Can't connect to device?
- Ensure Android is on same WiFi as iFace950
- Check IP address: `ping 192.168.100.35`

### Authentication failed?
- Check username/password in .env file
- Verify admin user exists on PythonAnywhere

### Termux keeps closing?
- Run: `termux-wake-lock`
- Disable battery optimization (see above)

### "Module not found"?
```bash
pip install --upgrade pyzk requests python-dotenv
```

---

## 📊 Monitor Status

The sync logs show:
- ✓ Successful syncs
- ✗ Errors
- Total records synced
- Connection status

Check anytime with:
```bash
tail -20 ~/gym-sync/sync.log
```

---

## 🔋 Power Management

**Best Setup:**
- Keep device plugged into charger
- Screen timeout: 30 seconds
- Battery optimization: Disabled for Termux
- Wake lock: Active

The sync runs even with screen off!

---

## 📞 Need Help?

1. Check logs: `tail -f ~/gym-sync/sync.log`
2. Verify network: `ping 192.168.100.35`
3. Test API: `curl https://habibworkspace.pythonanywhere.com`
4. Restart everything: Reboot device

---

**That's it!** Your Android device is now a dedicated attendance sync bridge. 🎉
