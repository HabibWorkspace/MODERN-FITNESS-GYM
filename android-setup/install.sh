#!/data/data/com.termux/files/usr/bin/bash

# Android Device Sync - Installation Script for Termux
# Run this script in Termux to set up everything automatically

echo "============================================================"
echo "Android Device Sync - Automated Installation"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Step 1: Update packages
echo "Step 1: Updating Termux packages..."
pkg update -y && pkg upgrade -y
if [ $? -eq 0 ]; then
    print_success "Packages updated"
else
    print_error "Failed to update packages"
    exit 1
fi
echo ""

# Step 2: Install required packages
echo "Step 2: Installing required packages..."
pkg install -y python git clang libffi openssl
if [ $? -eq 0 ]; then
    print_success "System packages installed"
else
    print_error "Failed to install system packages"
    exit 1
fi
echo ""

# Step 3: Install Python packages
echo "Step 3: Installing Python packages..."
pip install pyzk requests python-dotenv
if [ $? -eq 0 ]; then
    print_success "Python packages installed"
else
    print_error "Failed to install Python packages"
    exit 1
fi
echo ""

# Step 4: Create project directory
echo "Step 4: Creating project directory..."
mkdir -p ~/gym-sync
cd ~/gym-sync
print_success "Project directory created at ~/gym-sync"
echo ""

# Step 5: Setup storage access
echo "Step 5: Setting up storage access..."
print_info "You will be prompted to grant storage permission"
print_info "Please allow the permission when prompted"
termux-setup-storage
print_success "Storage access configured"
echo ""

# Step 6: Acquire wake lock
echo "Step 6: Acquiring wake lock..."
termux-wake-lock
print_success "Wake lock acquired (prevents Android from killing the process)"
echo ""

# Step 7: Create .env template
echo "Step 7: Creating configuration template..."
cat > ~/gym-sync/.env << 'EOF'
# PythonAnywhere Configuration
PYTHONANYWHERE_URL=https://habibworkspace.pythonanywhere.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin22@@

# Biometric Device Configuration
BIOMETRIC_DEVICE_IP=192.168.100.35
BIOMETRIC_DEVICE_PORT=4370

# Sync Configuration
SYNC_INTERVAL=3

# Pusher Configuration
PUSHER_APP_ID=2142303
PUSHER_KEY=8f96a097d2f6d11c1a34
PUSHER_SECRET=97a957c4a520fe63a10e
PUSHER_CLUSTER=mt1
EOF
print_success "Configuration file created at ~/gym-sync/.env"
echo ""

# Step 8: Setup auto-start
echo "Step 8: Setting up auto-start on boot..."
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start-sync.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash

# Acquire wake lock
termux-wake-lock

# Wait for network
sleep 30

# Start sync service
cd ~/gym-sync
python android_device_sync.py > ~/gym-sync/sync.log 2>&1 &
EOF
chmod +x ~/.termux/boot/start-sync.sh
print_success "Auto-start configured"
print_info "Install 'Termux:Boot' from F-Droid to enable auto-start on device boot"
echo ""

# Final instructions
echo "============================================================"
echo "Installation Complete!"
echo "============================================================"
echo ""
print_success "All packages installed successfully"
echo ""
echo "Next steps:"
echo "1. Copy android_device_sync.py to ~/gym-sync/"
echo "2. Edit ~/gym-sync/.env if needed (nano ~/gym-sync/.env)"
echo "3. Run: cd ~/gym-sync && python android_device_sync.py"
echo ""
echo "Optional:"
echo "- Install Termux:Boot from F-Droid for auto-start on device boot"
echo "- Install Termux:Wake Lock from F-Droid for better wake lock control"
echo ""
echo "Troubleshooting:"
echo "- View logs: tail -f ~/gym-sync/sync.log"
echo "- Check if running: ps aux | grep python"
echo "- Stop sync: pkill -f android_device_sync.py"
echo ""
echo "============================================================"
