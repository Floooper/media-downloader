#!/bin/bash
# Media Downloader - Ubuntu 24.04 Installation Script
# This script sets up the complete development environment

set -e  # Exit on any error

echo "🚀 Media Downloader - Ubuntu 24.04 Installation"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Please run as a regular user."
   exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    curl \
    git \
    unzip \
    wget

# Install Node.js (latest LTS)
print_status "Installing Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
else
    print_success "Node.js already installed: $(node --version)"
fi

# Install Python libtorrent
print_status "Installing libtorrent..."
sudo apt install -y python3-libtorrent || {
    print_warning "System libtorrent not available, will try pip install later"
}

# Create application directory
APP_DIR="$HOME/media_downloader"
print_status "Setting up application directory: $APP_DIR"

if [ -d "$APP_DIR" ]; then
    print_warning "Directory already exists. Backing up to ${APP_DIR}.backup"
    mv "$APP_DIR" "${APP_DIR}.backup.$(date +%s)"
fi

# Copy application files (assumes script is run from the app directory)
cp -r . "$APP_DIR"
cd "$APP_DIR"

# Make scripts executable
chmod +x *.sh

# Setup Python virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt || {
    print_warning "Some packages failed to install, trying alternatives..."
    # Try without libtorrent if it fails
    pip install fastapi uvicorn sqlalchemy pydantic aiohttp python-multipart alembic python-dotenv psutil
}

# Setup frontend
print_status "Setting up frontend..."
cd frontend
npm install
cd ..

# Create necessary directories
print_status "Creating application directories..."
mkdir -p downloads
mkdir -p logs
mkdir -p data

# Create environment file
print_status "Creating environment configuration..."
cat > .env << EOF
# Media Downloader Configuration
API_HOST=localhost
API_PORT=8000
FRONTEND_PORT=5173
DEFAULT_DOWNLOAD_PATH=./downloads
DATABASE_URL=sqlite:///./data/media_downloader.db
LOG_LEVEL=INFO

# Media Manager API Keys (configure these later)
SONARR_URL=
SONARR_API_KEY=
RADARR_URL=
RADARR_API_KEY=
READARR_URL=
READARR_API_KEY=
LIDARR_URL=
LIDARR_API_KEY=
EOF

# Create systemd service file (optional)
print_status "Creating systemd service file..."
sudo tee /etc/systemd/system/media-downloader.service > /dev/null << EOF
[Unit]
Description=Media Downloader Application
After=network.target

[Service]
Type=forking
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/start.sh
ExecStop=$APP_DIR/stop.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Set up firewall rules (if ufw is enabled)
if command -v ufw &> /dev/null && sudo ufw status | grep -q "Status: active"; then
    print_status "Configuring firewall..."
    sudo ufw allow 8000
    sudo ufw allow 5173
fi

# Create desktop shortcut
print_status "Creating desktop shortcut..."
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/media-downloader.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Media Downloader
Comment=Unified Media Download Manager
Exec=xdg-open http://localhost:5173
Icon=applications-multimedia
Terminal=false
Categories=AudioVideo;Network;
EOF

# Test installation
print_status "Testing installation..."
if ./start.sh; then
    sleep 5
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "Backend is running!"
    else
        print_warning "Backend health check failed"
    fi
    
    if curl -s http://localhost:5173 > /dev/null; then
        print_success "Frontend is running!"
    else
        print_warning "Frontend health check failed"
    fi
    
    ./stop.sh
else
    print_error "Failed to start application"
fi

# Final instructions
echo ""
print_success "🎉 Installation completed!"
echo ""
echo "📋 Next steps:"
echo "   1. Start the application: ./start.sh"
echo "   2. Open in browser: http://localhost:5173"
echo "   3. Configure media managers in the settings"
echo ""
echo "🔧 Useful commands:"
echo "   • Start: ./start.sh"
echo "   • Stop: ./stop.sh"
echo "   • View logs: tail -f backend.log frontend.log"
echo "   • Enable auto-start: sudo systemctl enable media-downloader"
echo ""
echo "📁 Application directory: $APP_DIR"
echo "📁 Downloads directory: $APP_DIR/downloads"
echo ""
print_success "Ready for development! 🚀"

