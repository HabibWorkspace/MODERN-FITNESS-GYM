# FitCore Deployment Script for PythonAnywhere

Write-Host "STARTING DEPLOYMENT TO PYTHONANYWHERE..." -ForegroundColor Cyan

$projectRoot = "c:\Users\habib\OneDrive\Desktop\Projects\MODERN FITNESS GYM"
$backendDir = "$projectRoot\backend"
$frontendDir = "$projectRoot\frontend"
$androidDir = "$projectRoot\android-setup"

$sshHost = "HabibWorkSpace@ssh.pythonanywhere.com"
$remotePath = "/home/HabibWorkSpace/MODERN-FITNESS-GYM"

Write-Host "DEPLOYMENT CONFIGURATION:" -ForegroundColor Yellow
Write-Host "  Project Root: $projectRoot"
Write-Host "  SSH Host: $sshHost"
Write-Host "  Remote Path: $remotePath"
Write-Host ""

# Step 1: Upload Backend
Write-Host "Step 1: Uploading Backend Files..." -ForegroundColor Green
Write-Host "  Source: $backendDir"
Write-Host "  Destination: $remotePath/backend"

$backendCmd = "scp -r -o StrictHostKeyChecking=no `"$backendDir`" ${sshHost}:${remotePath}/"
Invoke-Expression $backendCmd
if ($LASTEXITCODE -eq 0) {
    Write-Host "  SUCCESS: Backend uploaded" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Backend upload failed" -ForegroundColor Red
}

Write-Host ""

# Step 2: Upload Frontend
Write-Host "Step 2: Uploading Frontend Files..." -ForegroundColor Green
Write-Host "  Source: $frontendDir\dist"
Write-Host "  Destination: $remotePath/frontend/dist"

$frontendCmd = "scp -r -o StrictHostKeyChecking=no `"$frontendDir\dist`" ${sshHost}:${remotePath}/frontend/"
Invoke-Expression $frontendCmd
if ($LASTEXITCODE -eq 0) {
    Write-Host "  SUCCESS: Frontend uploaded" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Frontend upload failed" -ForegroundColor Red
}

Write-Host ""

# Step 3: Apply Database Migrations
Write-Host "Step 3: Applying Database Migrations..." -ForegroundColor Green

$migrationCmd = "ssh -o StrictHostKeyChecking=no $sshHost `"cd $remotePath/backend && alembic upgrade head`""
Invoke-Expression $migrationCmd

Write-Host ""

# Step 4: Reload Web App
Write-Host "Step 4: Reloading PythonAnywhere Web App..." -ForegroundColor Green
Write-Host "  MANUAL STEP: Go to https://www.pythonanywhere.com/user/HabibWorkSpace/webapps/"
Write-Host "  Click: Reload habibworkspace.pythonanywhere.com"
Write-Host ""

# Step 5: Verify Deployment
Write-Host "Step 5: Verifying Deployment..." -ForegroundColor Green
Write-Host "  Testing backend health endpoint..."

Start-Sleep -Seconds 3

$healthCheck = Invoke-WebRequest -Uri "https://habibworkspace.pythonanywhere.com/api/health" -ErrorAction SilentlyContinue
if ($healthCheck.StatusCode -eq 200) {
    Write-Host "  SUCCESS: Backend is running!" -ForegroundColor Green
    Write-Host "  Response: $($healthCheck.Content)"
} else {
    Write-Host "  WARNING: Backend may still be loading..." -ForegroundColor Yellow
}

Write-Host ""

# Step 6: Android Sync Instructions
Write-Host "Step 6: Deploy Android Sync Script..." -ForegroundColor Green
Write-Host "  Copy these files to Android tablet:"
Write-Host "    1. $androidDir\sync.py"
Write-Host "    2. $androidDir\.env"
Write-Host ""
Write-Host "  On Android (Termux):"
Write-Host "    cd ~/gym-sync"
Write-Host "    python sync.py"
Write-Host ""

# Final Summary
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "  1. Reload web app in PythonAnywhere"
Write-Host "  2. Deploy Android sync script"
Write-Host "  3. Test device connection"
Write-Host "  4. Verify attendance sync"
Write-Host ""

Write-Host "IMPORTANT LINKS:" -ForegroundColor Cyan
Write-Host "  Frontend: https://habibworkspace.pythonanywhere.com"
Write-Host "  API Health: https://habibworkspace.pythonanywhere.com/api/health"
Write-Host "  PythonAnywhere: https://www.pythonanywhere.com/user/HabibWorkSpace/webapps/"
Write-Host ""

Write-Host "Deployment ready! Device should show Online once Android sync is running." -ForegroundColor Green
