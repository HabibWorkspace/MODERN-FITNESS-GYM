# How to Transfer Files to Android Device

## Method 1: USB Cable (Recommended)

### For Windows:

1. **Connect Android device to computer via USB cable**

2. **On Android device:**
   - Swipe down notification panel
   - Tap "USB for file transfer" or "Charging this device via USB"
   - Select "File Transfer" or "MTP" mode

3. **On Windows:**
   - Open File Explorer
   - You should see your device under "This PC" or "Devices"
   - Navigate to: `Internal Storage` → `Download` folder

4. **Copy files:**
   - Copy `android_device_sync.py` to the Download folder
   - Copy `.env.example` to the Download folder (rename to `.env` and edit)

5. **In Termux on Android:**
   ```bash
   # Grant storage access first
   termux-setup-storage
   
   # Copy files from Downloads to gym-sync folder
   cd ~/gym-sync
   cp ~/storage/downloads/android_device_sync.py .
   cp ~/storage/downloads/.env .
   
   # Verify files are there
   ls -la
   ```

---

## Method 2: Cloud Storage (Google Drive, Dropbox)

### Using Google Drive:

1. **On Computer:**
   - Upload `android_device_sync.py` to Google Drive
   - Upload `.env.example` (rename to `.env` after editing)

2. **On Android:**
   - Open Google Drive app
   - Download the files
   - They'll be in Downloads folder

3. **In Termux:**
   ```bash
   termux-setup-storage
   cd ~/gym-sync
   cp ~/storage/downloads/android_device_sync.py .
   cp ~/storage/downloads/.env .
   ```

---

## Method 3: Email

1. **Email yourself** the files as attachments
2. **On Android:** Open email, download attachments
3. **In Termux:** Copy from Downloads (see Method 1, step 5)

---

## Method 4: Direct Creation in Termux (No Transfer Needed)

### Create android_device_sync.py directly:

```bash
cd ~/gym-sync
nano android_device_sync.py
```

Then **copy and paste** the entire content from the `android_device_sync.py` file.

**To paste in Termux:**
- Long press on screen → Paste
- Or use Termux's paste button

**To save:**
- Press `Ctrl + X`
- Press `Y`
- Press `Enter`

### Create .env file directly:

```bash
cd ~/gym-sync
nano .env
```

Paste the configuration (see QUICK_START.md), then save.

---

## Method 5: QR Code / Link Sharing

### Using Termux API:

1. **Install Termux:API** from F-Droid

2. **In Termux:**
   ```bash
   pkg install termux-api
   ```

3. **Share file via Termux:**
   ```bash
   termux-share /path/to/file
   ```

---

## Method 6: Local Network Transfer (Advanced)

### Using Python HTTP Server:

1. **On Computer** (in the android-setup folder):
   ```bash
   python -m http.server 8000
   ```

2. **Find your computer's IP:**
   - Windows: `ipconfig` (look for IPv4 Address)
   - Example: `192.168.1.100`

3. **On Android in Termux:**
   ```bash
   cd ~/gym-sync
   curl -O http://192.168.1.100:8000/android_device_sync.py
   curl -O http://192.168.1.100:8000/.env.example
   mv .env.example .env
   ```

---

## Verify Files Are Transferred

```bash
cd ~/gym-sync
ls -la
```

You should see:
```
android_device_sync.py
.env
```

Check file contents:
```bash
head -20 android_device_sync.py
cat .env
```

---

## File Permissions

Make sure the Python script is readable:
```bash
chmod +x android_device_sync.py
```

---

## Troubleshooting

### "Permission denied" when copying from Downloads:
```bash
termux-setup-storage
# Grant permission when prompted, then try again
```

### Can't find Downloads folder:
```bash
ls ~/storage/downloads/
# If empty, files might be in:
ls ~/storage/shared/Download/
```

### Files not showing in Termux:
- Wait a few seconds after download
- Refresh file manager
- Try rebooting Android device

---

## Quick Copy-Paste Commands

After files are in Downloads folder:

```bash
# One-liner to copy everything
termux-setup-storage && cd ~/gym-sync && cp ~/storage/downloads/android_device_sync.py . && cp ~/storage/downloads/.env . && ls -la
```

---

Choose the method that works best for you! Method 1 (USB) is usually the fastest and most reliable.
