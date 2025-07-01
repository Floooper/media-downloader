#!/bin/bash
# Media Downloader - Ubuntu Package Creator
# This script creates a deployable package for Ubuntu systems

set -e

echo "📦 Creating Ubuntu deployment package..."

# Package information
PACKAGE_NAME="media-downloader"
PACKAGE_VERSION="0.1.0"
PACKAGE_FILE="${PACKAGE_NAME}-${PACKAGE_VERSION}-ubuntu.tar.gz"
TEMP_DIR="/tmp/${PACKAGE_NAME}-package"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Clean up any existing temp directory
if [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
fi

# Create temporary directory
mkdir -p "$TEMP_DIR"

print_status "Copying application files..."

# Copy main application files
cp -r src "$TEMP_DIR/"
cp -r frontend "$TEMP_DIR/"

# Copy configuration and setup files
cp requirements.txt "$TEMP_DIR/"
cp *.sh "$TEMP_DIR/"
cp README-Ubuntu.md "$TEMP_DIR/README.md"
cp install-ubuntu.sh "$TEMP_DIR/"

# Copy any existing configuration
if [ -f ".env" ]; then
    cp .env "$TEMP_DIR/.env.example"
fi

# Create necessary directories
mkdir -p "$TEMP_DIR/downloads"
mkdir -p "$TEMP_DIR/logs"
mkdir -p "$TEMP_DIR/data"

# Create version file
echo "$PACKAGE_VERSION" > "$TEMP_DIR/VERSION"

# Create package info file
cat > "$TEMP_DIR/PACKAGE_INFO" << EOF
Package: $PACKAGE_NAME
Version: $PACKAGE_VERSION
Platform: Ubuntu 24.04
Python: 3.12+
Node.js: 18+
Created: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Created-by: $(whoami)@$(hostname)
EOF

print_status "Cleaning up frontend node_modules (if present)..."
if [ -d "$TEMP_DIR/frontend/node_modules" ]; then
    rm -rf "$TEMP_DIR/frontend/node_modules"
fi

print_status "Cleaning up Python cache files..."
find "$TEMP_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$TEMP_DIR" -name "*.pyc" -delete 2>/dev/null || true
find "$TEMP_DIR" -name "*.pyo" -delete 2>/dev/null || true

# Remove macOS specific files
find "$TEMP_DIR" -name ".DS_Store" -delete 2>/dev/null || true

# Make scripts executable
chmod +x "$TEMP_DIR"/*.sh

print_status "Creating compressed archive..."
cd /tmp
tar -czf "$PACKAGE_FILE" "${PACKAGE_NAME}-package"

# Move package to original directory
ORIG_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$ORIG_DIR/$PACKAGE_FILE" ]; then
    rm "$ORIG_DIR/$PACKAGE_FILE"
fi
mv "$PACKAGE_FILE" "$ORIG_DIR/"

# Clean up temp directory
rm -rf "$TEMP_DIR"

# Get package size
PACKAGE_SIZE=$(du -h "$ORIG_DIR/$PACKAGE_FILE" | cut -f1)

print_success "Package created successfully!"
echo ""
echo "📦 Package Details:"
echo "   Name: $PACKAGE_FILE"
echo "   Size: $PACKAGE_SIZE"
echo "   Location: $(pwd)/$PACKAGE_FILE"
echo ""
echo "🚀 Ubuntu Deployment Instructions:"
echo "   1. Transfer package to Ubuntu system:"
echo "      scp $PACKAGE_FILE user@ubuntu-server:~/"
echo ""
echo "   2. On Ubuntu system, extract and install:"
echo "      tar -xzf $PACKAGE_FILE"
echo "      cd ${PACKAGE_NAME}-package"
echo "      chmod +x install-ubuntu.sh"
echo "      ./install-ubuntu.sh"
echo ""
echo "   3. Start the application:"
echo "      ./start.sh"
echo ""
echo "   4. Open in browser:"
echo "      http://localhost:5173"
echo ""
print_success "Ready for Ubuntu deployment! 🐧"

# Create checksum file
echo "📝 Creating checksum..."
cd "$ORIG_DIR"
sha256sum "$PACKAGE_FILE" > "$PACKAGE_FILE.sha256"
print_success "Checksum created: $PACKAGE_FILE.sha256"

