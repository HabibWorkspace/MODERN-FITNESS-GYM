# Local Device Sync Setup for PythonAnywhere

Since PythonAnywhere cannot connect directly to your local biometric device, you need to run a sync service on your local computer.

## How It Works

```
[Biometric Device] ←→ [Your Computer] ←→ [PythonAnywhere]
   192.168.0.201         Local Sync         Cloud Backend
```

1. Your local computer connects to the biometric device
2. Fetches attendance logs every 3 seconds
3. Pushes new records to PythonAnywhere via HTTPS API
4. PythonAnywhere serves the web interface

## Setup Instructions

### 1. On Your Local Computer

Create a `.env` file in the `backend` folder with:

```env
# Local device connection
BIOMETRIC_DEVICE_IP=192.168.0.201
BIOMETRIC_DEVICE_PORT=4370

# PythonAnywhere backend
PYTHONANYWHERE_URL=https://habibworkspace.pythonanywhere.com

# Admin credentials (for API authentication)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin22@@
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Run the Local Sync Service

```bash
python local_device_sync.py
```

You should see:

```
============================================================
Local Device Sync Service
============================================================
Device: 192.168.0.201:4370
Remote: https://habibworkspace.pythonanywhere.com
Sync Interval: 3s
============================================================
✓ Authenticated with PythonAnywhere
✓ Connected to biometric device

Starting sync loop... (Press Ctrl+C to stop)
✓ Synced 2 new attendance logs
✓ Synced 1 new attendance logs
...
```

### 4. Keep It Running

The sync service needs to run continuously on your local computer. You can:

- Run it in a terminal window
- Set it up as a Windows service
- Use a process manager like `pm2` or `supervisor`

## On PythonAnywhere

The PythonAnywhere backend will:
- NOT try to connect to the biometric device
- Only receive synced data from your local computer
- Serve the web interface normally

## Troubleshooting

### Device Not Connecting
- Check device IP: `ping 192.168.0.201`
- Verify device is powered on
- Check firewall settings

### Authentication Failed
- Verify admin credentials in `.env`
- Check PythonAnywhere URL is correct

### Sync Not Working
- Check internet connection
- Verify PythonAnywhere backend is running
- Check backend logs for errors

## Alternative: Run Everything Locally

If you prefer, you can run the entire backend locally:

```bash
cd backend
python app.py
```

Then access at `http://localhost:5000`

This way everything runs on your local network with direct device access.
