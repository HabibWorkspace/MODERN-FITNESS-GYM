"""
Network Connection Test Script
Run this on Android to diagnose connection issues.
"""
import os
import socket
import subprocess
from dotenv import load_dotenv

# Load environment
load_dotenv()

DEVICE_IP = os.getenv('BIOMETRIC_DEVICE_IP', '192.168.0.201')
DEVICE_PORT = int(os.getenv('BIOMETRIC_DEVICE_PORT', 4270))

print("=" * 60)
print("Network Connection Diagnostic Tool")
print("=" * 60)
print()

# Test 1: Check environment variables
print("Test 1: Configuration")
print(f"  Device IP: {DEVICE_IP}")
print(f"  Device Port: {DEVICE_PORT}")
print()

# Test 2: Check local IP
print("Test 2: Your Android IP Address")
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
    print(f"  Your IP: {local_ip}")
    
    # Check if same subnet
    device_subnet = '.'.join(DEVICE_IP.split('.')[:3])
    local_subnet = '.'.join(local_ip.split('.')[:3])
    
    if device_subnet == local_subnet:
        print(f"  ✓ Same subnet as device ({device_subnet}.x)")
    else:
        print(f"  ✗ DIFFERENT subnet!")
        print(f"    Device: {device_subnet}.x")
        print(f"    You: {local_subnet}.x")
        print(f"  → You need to connect to the same WiFi network!")
except Exception as e:
    print(f"  ✗ Error: {e}")
print()

# Test 3: Ping device
print("Test 3: Ping Device")
print(f"  Pinging {DEVICE_IP}...")
try:
    result = subprocess.run(
        ['ping', '-c', '3', DEVICE_IP],
        capture_output=True,
        text=True,
        timeout=10
    )
    if result.returncode == 0:
        print(f"  ✓ Device is reachable!")
        # Extract average time
        for line in result.stdout.split('\n'):
            if 'avg' in line or 'time' in line:
                print(f"  {line.strip()}")
    else:
        print(f"  ✗ Device is NOT reachable!")
        print(f"  → Check if device is on same WiFi network")
        print(f"  → Check if device IP is correct")
except subprocess.TimeoutExpired:
    print(f"  ✗ Ping timeout!")
    print(f"  → Device is not responding")
except Exception as e:
    print(f"  ✗ Error: {e}")
print()

# Test 4: Check port
print("Test 4: Check Port Connection")
print(f"  Testing {DEVICE_IP}:{DEVICE_PORT}...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((DEVICE_IP, DEVICE_PORT))
    sock.close()
    
    if result == 0:
        print(f"  ✓ Port {DEVICE_PORT} is OPEN!")
        print(f"  → Device is ready for connection")
    else:
        print(f"  ✗ Port {DEVICE_PORT} is CLOSED or FILTERED!")
        print(f"  → Check if port number is correct on device")
        print(f"  → Check device firewall settings")
except socket.timeout:
    print(f"  ✗ Connection timeout!")
    print(f"  → Device is not responding on this port")
except Exception as e:
    print(f"  ✗ Error: {e}")
print()

# Test 5: Try ZK connection
print("Test 5: Try ZKTeco Connection")
try:
    from zk import ZK
    print(f"  Attempting to connect...")
    
    zk = ZK(DEVICE_IP, port=DEVICE_PORT, timeout=10, force_udp=True)
    conn = zk.connect()
    
    if conn:
        print(f"  ✓ Successfully connected to device!")
        
        # Get device info
        try:
            serial = conn.get_serialnumber()
            print(f"  Device Serial: {serial}")
        except:
            print(f"  (Could not get serial number)")
        
        try:
            users = conn.get_users()
            print(f"  Registered Users: {len(users)}")
        except:
            print(f"  (Could not get user count)")
        
        try:
            attendances = conn.get_attendance()
            print(f"  Attendance Records: {len(attendances)}")
        except:
            print(f"  (Could not get attendance count)")
        
        conn.disconnect()
        print(f"  ✓ Connection test successful!")
    else:
        print(f"  ✗ Failed to connect!")
        
except ImportError:
    print(f"  ✗ pyzk library not installed!")
    print(f"  → Run: pip install pyzk")
except Exception as e:
    print(f"  ✗ Connection failed: {e}")
    print(f"  → This is the actual error you're getting in the sync")
print()

# Summary
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print()
print("If all tests passed (✓):")
print("  → Your network is configured correctly")
print("  → The sync should work")
print()
print("If any test failed (✗):")
print("  → Fix the issue mentioned in that test")
print("  → Run this script again to verify")
print()
print("Common fixes:")
print("  1. Connect Android to same WiFi as device")
print("  2. Check device IP on iFace950 (Menu → Comm → TCP/IP)")
print("  3. Check device port (Menu → Comm → Comm Opt)")
print("  4. Disable AP Isolation on router")
print("  5. Restart iFace950 device")
print()
print("=" * 60)
