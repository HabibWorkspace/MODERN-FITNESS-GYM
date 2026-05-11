# Setup Checklist

## For Developer (You)

### Before Sending to Gym Owner:

- [ ] Create `.env` file from `.env.example`
- [ ] Verify all values in `.env` are correct:
  - [ ] PYTHONANYWHERE_URL
  - [ ] ADMIN_USERNAME  
  - [ ] ADMIN_PASSWORD
  - [ ] BIOMETRIC_DEVICE_IP (192.168.100.35)
  - [ ] BIOMETRIC_DEVICE_PORT (4370)
- [ ] Test script on your PC (optional, if on same network)
- [ ] Package files into ZIP or folder
- [ ] Send to gym owner with clear instructions
- [ ] Be available for initial setup support

### Files to Send:

**Essential:**
- [ ] android_device_sync.py
- [ ] .env (configured)
- [ ] FOR_GYM_OWNER.md
- [ ] QUICK_START.md
- [ ] TROUBLESHOOTING.md
- [ ] SEND_TO_GYM_OWNER.txt

**Optional:**
- [ ] TRANSFER_INSTRUCTIONS.md
- [ ] README.md
- [ ] requirements.txt

---

## For Gym Owner (On Android Device)

### Initial Setup:

- [ ] Download F-Droid app
- [ ] Install Termux from F-Droid (NOT Play Store!)
- [ ] Open Termux
- [ ] Run: `pkg update -y`
- [ ] Run: `pkg upgrade -y`
- [ ] Run: `pkg install -y python git clang libffi openssl`
- [ ] Run: `pip install pyzk requests python-dotenv`
- [ ] Run: `mkdir -p ~/gym-sync`
- [ ] Run: `termux-wake-lock`

### File Transfer:

- [ ] Connect Android to computer via USB
- [ ] Enable "File Transfer" mode on Android
- [ ] Copy files to Android Downloads folder
- [ ] In Termux: `termux-setup-storage` (grant permission)
- [ ] In Termux: `cd ~/gym-sync`
- [ ] In Termux: `cp ~/storage/downloads/android_device_sync.py .`
- [ ] In Termux: `cp ~/storage/downloads/.env .`
- [ ] Verify files: `ls -la`

### Configuration:

- [ ] Android device on same WiFi as iFace950
- [ ] Device IP is correct (192.168.100.35)
- [ ] Admin credentials are correct
- [ ] Test connection: `ping 192.168.100.35`

### Start Sync:

- [ ] Run: `cd ~/gym-sync`
- [ ] Run: `python android_device_sync.py`
- [ ] See "✓ Authenticated with PythonAnywhere"
- [ ] See "✓ Connected to biometric device"
- [ ] See "Starting sync loop..."
- [ ] Test: Scan fingerprint on iFace950
- [ ] Verify attendance appears in web app

### Keep Running 24/7:

- [ ] Settings → Apps → Termux → Battery → Unrestricted
- [ ] Device plugged into charger
- [ ] Wake lock active: `termux-wake-lock`
- [ ] Run in background: `python android_device_sync.py &`
- [ ] Can close Termux app (keeps running)
- [ ] Can lock screen (keeps running)

### Auto-Start (Optional):

- [ ] Install Termux:Boot from F-Droid
- [ ] Open Termux:Boot once
- [ ] Run: `mkdir -p ~/.termux/boot`
- [ ] Create startup script (see guide)
- [ ] Make executable: `chmod +x ~/.termux/boot/start-sync.sh`
- [ ] Test: Reboot device, check if sync starts

---

## Verification

### Check if Working:

- [ ] Sync process running: `ps aux | grep python`
- [ ] Logs showing activity: `tail -f ~/gym-sync/sync.log`
- [ ] Device connected: See "✓ Connected" in logs
- [ ] Records syncing: See "✓ Synced" messages
- [ ] Web app showing attendance
- [ ] Real-time updates working

### Network Tests:

- [ ] Can reach device: `ping 192.168.100.35`
- [ ] Can reach backend: `curl https://habibworkspace.pythonanywhere.com`
- [ ] Internet working: `ping google.com`

### Battery & Power:

- [ ] Device plugged into charger
- [ ] Battery optimization disabled
- [ ] Wake lock active
- [ ] Screen can turn off (sync continues)

---

## Troubleshooting

### If Not Working:

- [ ] Check logs: `tail -f ~/gym-sync/sync.log`
- [ ] Verify WiFi connection
- [ ] Verify device IP: `ping 192.168.100.35`
- [ ] Check credentials in .env file
- [ ] Restart sync: `pkill -f android_device_sync.py && cd ~/gym-sync && python android_device_sync.py`
- [ ] Check TROUBLESHOOTING.md

### Common Issues:

- [ ] "Connection refused" → Check WiFi, verify IP
- [ ] "Authentication failed" → Check username/password
- [ ] "Module not found" → Run: `pip install pyzk requests python-dotenv`
- [ ] Termux closes → Disable battery optimization
- [ ] No logs syncing → Check device user mappings

---

## Maintenance

### Weekly:

- [ ] Check logs for errors
- [ ] Verify sync is running
- [ ] Check web app for recent attendance

### Monthly:

- [ ] Update packages: `pkg upgrade`
- [ ] Update Python libs: `pip install --upgrade pyzk requests python-dotenv`
- [ ] Check device storage space
- [ ] Verify auto-start still working

### As Needed:

- [ ] Restart if errors occur
- [ ] Update .env if settings change
- [ ] Update script if new version available

---

## Success Criteria

✅ Sync running 24/7
✅ Attendance appearing in web app within 3 seconds
✅ No errors in logs
✅ Device stays connected
✅ Auto-starts on reboot
✅ Works with screen off
✅ Gym owner doesn't need to touch it

---

## Support Contacts

**Developer:** [Your contact info]
**Documentation:** See FOR_GYM_OWNER.md
**Troubleshooting:** See TROUBLESHOOTING.md

---

**Last Updated:** 2024
**Version:** 1.0
