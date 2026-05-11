# Network Setup Guide for iFace950

## 🌐 Understanding the Network

You have **3 different IP addresses** to configure:

1. **Your Computer IP:** `192.168.0.185` (this is just for reference)
2. **iFace950 Device IP:** `192.168.0.XXX` (need to find this!)
3. **Android Device IP:** Assigned automatically by WiFi

---

## 📱 Step 1: Find iFace950 Device IP Address

### On the iFace950 Device:

1. **Press Menu** on the device
2. Navigate to: **Comm** → **TCP/IP**
3. You'll see:
   ```
   IP Address: 192.168.0.201  ← This is what you need!
   Subnet Mask: 255.255.255.0
   Gateway: 192.168.0.1
   ```
4. **Write down the IP Address**

**Common iFace950 IPs:**
- `192.168.0.201`
- `192.168.0.100`
- `192.168.1.201`

---

## ⚙️ Step 2: Configure iFace950 Device Settings

### TCP/IP Settings (on iFace950):

1. **Menu** → **Comm** → **TCP/IP**
2. Set these values:
   ```
   IP Address: 192.168.0.201  (or any available IP in your network)
   Subnet Mask: 255.255.255.0
   Gateway: 192.168.0.1
   ```
3. **Save** the settings

### TCP Comm Port (on iFace950):

1. **Menu** → **Comm** → **Comm Opt**
2. Find **TCP Port** setting
3. Set to: **4370** (this is the standard ZKTeco port)
4. **Save** the settings

### Cloud Server Settings (OPTIONAL - Not Needed for Our Setup):

**You DON'T need to configure cloud server settings!**

Our setup works like this:
```
iFace950 (Local Network)
    ↓
Android Device (Local Network)
    ↓
Internet
    ↓
PythonAnywhere (Cloud)
```

The Android device connects to iFace950 **locally** (no cloud server needed on the device).

**If you still want to configure it:**
1. **Menu** → **Comm** → **Cloud Server**
2. **Disable** cloud server (we're not using it)
3. Or leave it as is (won't interfere)

---

## 📝 Step 3: Update Configuration Files

### On Android Device (in Termux):

```bash
cd ~/downloads  # or ~/gym-sync
nano .env
```

Update this line:
```env
BIOMETRIC_DEVICE_IP=192.168.0.201  ← Use the IP you found on the device
BIOMETRIC_DEVICE_PORT=4370
```

Save: `Ctrl+X`, then `Y`, then `Enter`

---

## 🔍 Step 4: Test Connection

### From Android Device (in Termux):

```bash
# Test if you can reach the iFace950
ping 192.168.0.201

# You should see:
# 64 bytes from 192.168.0.201: icmp_seq=1 ttl=64 time=5.2 ms
# 64 bytes from 192.168.0.201: icmp_seq=2 ttl=64 time=4.8 ms
```

Press `Ctrl+C` to stop the ping.

**If ping works:** ✅ Network is good!  
**If ping fails:** ❌ Check WiFi and IP address

---

## 🚀 Step 5: Run the Sync

```bash
cd ~/downloads  # or ~/gym-sync
python android_device_sync.py
```

You should see:
```
✓ Authenticated with PythonAnywhere
Connecting to biometric device...
✓ Connected to biometric device at 192.168.0.201:4370
```

---

## 🔧 Troubleshooting

### "Connection refused" or "Timeout"

**Check 1: Same Network**
- Android device and iFace950 must be on the same WiFi
- Both should have IPs like `192.168.0.XXX`

**Check 2: Correct IP**
```bash
ping 192.168.0.201  # Use your actual device IP
```

**Check 3: Correct Port**
- Default ZKTeco port is `4370`
- Check on device: Menu → Comm → Comm Opt

**Check 4: Firewall**
- Some routers block device-to-device communication
- Check router settings for "AP Isolation" (should be disabled)

### "Can't find device"

**Option 1: Scan Network**
```bash
# Install nmap (optional)
pkg install nmap

# Scan your network for devices
nmap -p 4370 192.168.0.1-254
```

**Option 2: Check Router**
- Log into your router (usually `192.168.0.1`)
- Look at "Connected Devices" list
- Find the iFace950 device

---

## 📊 Network Configuration Summary

| Device | IP Address | Port | Purpose |
|--------|------------|------|---------|
| **Your Computer** | 192.168.0.185 | N/A | For reference only |
| **iFace950** | 192.168.0.201 | 4370 | Attendance device |
| **Android Device** | 192.168.0.XXX | N/A | Sync bridge |
| **Router/Gateway** | 192.168.0.1 | N/A | Network gateway |
| **PythonAnywhere** | Internet | 443 | Cloud backend |

---

## ✅ Quick Checklist

- [ ] Found iFace950 IP address (Menu → Comm → TCP/IP)
- [ ] iFace950 TCP port is 4370 (Menu → Comm → Comm Opt)
- [ ] Android device on same WiFi as iFace950
- [ ] Updated .env file with correct IP
- [ ] Can ping iFace950 from Android: `ping 192.168.0.201`
- [ ] Sync script running successfully

---

## 🎯 Common iFace950 Default Settings

**Default IP:** `192.168.1.201` or `192.168.0.201`  
**Default Port:** `4370`  
**Default Gateway:** `192.168.0.1` or `192.168.1.1`  
**Subnet Mask:** `255.255.255.0`

---

## 📞 Need Help?

1. Check the IP on the device (Menu → Comm → TCP/IP)
2. Make sure Android is on same WiFi
3. Test with ping command
4. Check TROUBLESHOOTING.md for more solutions

---

**Remember:** The iFace950 device has its own IP address. Your computer's IP (192.168.0.185) is different from the device's IP!
