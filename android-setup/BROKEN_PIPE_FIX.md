# Broken Pipe Error - Fixed! ✅

## What Was the Problem?

**Error 32: Broken Pipe** happens when the iFace950 device closes the connection unexpectedly. This is common with ZKTeco devices because:

1. The device has a connection timeout
2. The device limits concurrent connections
3. Network instability

## What I Fixed:

✅ **Auto-reconnect on broken pipe**  
✅ **Connection lifetime management** (reconnects every 30 seconds)  
✅ **Better error handling**  
✅ **Increased timeout** (from 5s to 10s)  
✅ **Proper connection cleanup**  

## How to Update on Android:

### Step 1: Stop Current Sync (if running)

```bash
pkill -f android_device_sync.py
```

### Step 2: Download Updated Script

Transfer the new `android_device_sync.py` file to your Android device (same way you did before).

### Step 3: Replace Old Script

```bash
# If you're in ~/downloads
cd ~/downloads
# Copy the new file here (overwrite the old one)

# Or if you're in ~/gym-sync
cd ~/gym-sync
cp ~/storage/downloads/android_device_sync.py .
```

### Step 4: Run Updated Script

```bash
python android_device_sync.py
```

## What You'll See Now:

The script will:
- ✅ Connect to device
- ✅ Fetch attendance logs
- ✅ If "Broken Pipe" occurs → Automatically reconnect
- ✅ Continue syncing without stopping

**Example output:**
```
✓ Connected to biometric device
✓ Synced attendance log for user 1
✗ Connection error (Broken Pipe): [Errno 32] Broken pipe
Disconnecting and will reconnect on next cycle...
Connecting to biometric device...
✓ Connected to biometric device
✓ Synced attendance log for user 2
```

## Key Improvements:

### 1. Connection Lifetime
- Reconnects every 30 seconds automatically
- Prevents stale connections

### 2. Broken Pipe Handling
- Catches the error gracefully
- Disconnects cleanly
- Reconnects on next cycle

### 3. Better Timeout
- Increased from 5s to 10s
- More reliable for slow networks

### 4. Retry Logic
- If fetch fails → Reconnect and retry once
- If still fails → Wait for next cycle

## Testing:

After updating, test it:

```bash
# Run the sync
python android_device_sync.py

# Watch for these messages:
# ✓ Connected to biometric device
# ✓ Synced attendance log for user X
# (Should NOT see repeated Broken Pipe errors)
```

## If You Still Get Errors:

### Try These:

**1. Increase Sync Interval**

Edit `.env`:
```env
SYNC_INTERVAL=10  # Changed from 3 to 10 seconds
```

This gives the device more time between connections.

**2. Check Network Stability**

```bash
# Ping the device continuously
ping 192.168.0.201

# Should see consistent response times
# If you see timeouts or high latency, network is unstable
```

**3. Check Device Settings**

On iFace950:
- Menu → Comm → TCP/IP
- Check if "Max Connections" is set (increase if possible)

**4. Restart Device**

Sometimes the iFace950 needs a restart:
- Menu → System → Restart

## Alternative: Use UDP Instead of TCP

If TCP keeps having issues, we can try UDP mode.

Edit the script (line ~75):
```python
# Change this:
self.zk = ZK(ip, port=port, timeout=timeout, force_udp=False, ommit_ping=False)

# To this:
self.zk = ZK(ip, port=port, timeout=timeout, force_udp=True, ommit_ping=False)
```

UDP is less reliable but doesn't have "Broken Pipe" issues.

## Summary:

✅ **Updated script handles Broken Pipe automatically**  
✅ **Reconnects every 30 seconds**  
✅ **Better error recovery**  
✅ **Should work reliably now**  

Just transfer the new script to your Android device and run it!

---

**Need help?** Check the logs:
```bash
tail -f ~/downloads/sync.log
# or
tail -f ~/gym-sync/sync.log
```
