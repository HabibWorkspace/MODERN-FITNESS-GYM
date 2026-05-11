# Test Pusher - Quick Diagnostic

## Test 1: Check if Pusher Service is Initialized

Open browser console on the dashboard and run:

```javascript
fetch('/api/attendance/health', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('token')
  }
})
.then(r => r.json())
.then(d => {
  console.log('Health check result:', d);
  console.log('Pusher configured:', d.pusher_configured);
  console.log('Pusher enabled:', d.pusher_enabled);
})
```

**Expected result:**
```
pusher_configured: true
pusher_enabled: true
```

If either is `false`, Pusher is not initialized properly.

---

## Test 2: Manually Trigger Pusher Event

In browser console, run:

```javascript
fetch('/api/attendance/test-pusher', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('token'),
    'Content-Type': 'application/json'
  }
})
.then(r => r.json())
.then(d => {
  console.log('Test Pusher result:', d);
  if (d.success) {
    console.log('✓ Pusher is working! You should see a toast notification.');
  } else {
    console.log('✗ Pusher failed:', d.error);
  }
})
```

**Expected result:**
- You should see a toast notification pop up with "Test User"
- Console should show: `success: true`

If you see the notification, Pusher IS working and the issue is in the sync-log endpoint.

---

## Test 3: Check PythonAnywhere Error Log

After running Test 2, check the PythonAnywhere error log for:

```
INFO - Attempting to trigger Pusher event: attendance-updates/check-in
INFO - ✓ Pusher event triggered successfully: attendance-updates/check-in
```

If you see these lines, Pusher backend is working.

---

## Test 4: Check Browser Console for Pusher Events

Keep browser console open and trigger a real check-in from Android sync.

Look for:
```
Check-in event received: {data}
```

If you see this, Pusher is receiving events but toast might not be showing.

---

## What to Report

Run all 4 tests and tell me:

1. **Test 1 result:** `pusher_configured` and `pusher_enabled` values
2. **Test 2 result:** Did you see a toast notification? What did console show?
3. **Test 3 result:** What lines appeared in PythonAnywhere error log?
4. **Test 4 result:** Did you see "Check-in event received" in console?

This will tell us exactly where the problem is.
