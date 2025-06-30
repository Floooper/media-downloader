# Media Downloader - Ubuntu 24.04 Deployment Guide

🚀 **Complete unified media download manager with Readarr/Sonarr/Radarr integration**

## 📦 Quick Installation

1. **Extract the package:**
   ```bash
   tar -xzf media-downloader.tar.gz
   cd media_downloader
   ```

2. **Run the installation script:**
   ```bash
   chmod +x install-ubuntu.sh
   ./install-ubuntu.sh
   ```

3. **Start the application:**
   ```bash
   ./start.sh
   ```

4. **Open in browser:**
   ```
   http://localhost:5173
   ```

## ✨ Features

- **🔄 Queue Management** - Real-time download queue with drag-and-drop reordering
- **🏷️ Smart Tagging** - Auto-assign tags based on patterns with destination folders
- **📚 Media Manager Integration** - Direct integration with Readarr, Sonarr, Radarr, Lidarr
- **🌐 Transmission API** - Acts as a Transmission-compatible download client
- **📊 System Monitoring** - Real-time system info, resource usage, API status
- **🔧 Advanced Settings** - Comprehensive configuration and troubleshooting tools
- **📝 In-App Logging** - Built-in log viewer with filtering and export
- **🎯 Multiple Formats** - Support for Torrents, Magnet Links, and NZB files

## 🔧 Manual Installation (if script fails)

### System Dependencies
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm git
```

### Python Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
cd ..
```

### Start Services
```bash
./start.sh
```

## 📋 Configuration

### Environment Variables (.env)
```bash
API_HOST=localhost
API_PORT=8000
FRONTEND_PORT=5173
DEFAULT_DOWNLOAD_PATH=./downloads
DATABASE_URL=sqlite:///./data/media_downloader.db

# Media Manager URLs and API Keys
READARR_URL=http://localhost:8787
READARR_API_KEY=your_readarr_api_key
SONARR_URL=http://localhost:8989
SONARR_API_KEY=your_sonarr_api_key
RADARR_URL=http://localhost:7878
RADARR_API_KEY=your_radarr_api_key
```

### Media Manager Setup

1. **Go to System tab** in the web interface
2. **Navigate to Download Client tab**
3. **Copy configuration values** for your media manager
4. **Add as Transmission client** in Readarr/Sonarr/Radarr:
   - **Host:** localhost
   - **Port:** 8000
   - **URL Base:** /api/transmission/rpc
   - **Category:** readarr/sonarr/radarr

## 🚀 Development

### Start Development Mode
```bash
# Backend (with auto-reload)
source venv/bin/activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (with hot reload)
cd frontend
npm run dev
```

### Project Structure
```
media_downloader/
├── src/                    # Backend source code
│   ├── api/               # FastAPI routes
│   ├── models/            # Database models
│   ├── services/          # Business logic
│   └── main.py           # Application entry point
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API clients
│   │   └── types/         # TypeScript types
│   └── package.json
├── downloads/             # Default download directory
├── data/                  # Database and app data
├── logs/                  # Application logs
└── requirements.txt       # Python dependencies
```

## 🔨 Commands

| Command | Description |
|---------|-------------|
| `./start.sh` | Start both backend and frontend |
| `./stop.sh` | Stop all services |
| `tail -f backend.log` | View backend logs |
| `tail -f frontend.log` | View frontend logs |

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port
sudo lsof -i :8000
# Kill process
sudo kill -9 <PID>
```

### Permission Issues
```bash
# Fix script permissions
chmod +x *.sh
# Fix directory permissions
chmod -R 755 .
```

### Python Dependencies Failed
```bash
# Install system packages for compilation
sudo apt install python3-dev build-essential
# Try installing without libtorrent
pip install fastapi uvicorn sqlalchemy pydantic aiohttp
```

### Node.js Issues
```bash
# Clear npm cache
npm cache clean --force
# Delete node_modules and reinstall
rm -rf frontend/node_modules
cd frontend && npm install
```

## 🔧 System Service (Auto-start)

### Enable Auto-start
```bash
sudo systemctl enable media-downloader
sudo systemctl start media-downloader
```

### Service Commands
```bash
# Status
sudo systemctl status media-downloader
# Start
sudo systemctl start media-downloader
# Stop
sudo systemctl stop media-downloader
# Restart
sudo systemctl restart media-downloader
# View logs
journalctl -u media-downloader -f
```

## 📊 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `http://localhost:8000/docs` | FastAPI documentation |
| `http://localhost:8000/api/downloads` | Downloads API |
| `http://localhost:8000/api/queue` | Queue management |
| `http://localhost:8000/api/tags` | Tag management |
| `http://localhost:8000/api/transmission/rpc` | Transmission compatibility |
| `http://localhost:8000/api/system/info` | System information |

## 🌐 Remote Access

### Allow External Connections
```bash
# Edit .env file
API_HOST=0.0.0.0
# Configure firewall
sudo ufw allow 8000
sudo ufw allow 5173
```

### Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📈 Performance Tuning

### For Heavy Usage
```bash
# Increase file descriptor limits
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize for more concurrent downloads
export MAX_CONCURRENT_DOWNLOADS=10
```

## 🔐 Security

### Basic Security Setup
```bash
# Create dedicated user
sudo useradd -m -s /bin/bash mediadownloader
sudo usermod -aG sudo mediadownloader

# Move application
sudo mv media_downloader /opt/
sudo chown -R mediadownloader:mediadownloader /opt/media_downloader

# Run as service user
sudo -u mediadownloader /opt/media_downloader/start.sh
```

## 📞 Support

- **Application Logs:** Check `backend.log` and `frontend.log`
- **System Logs:** `journalctl -u media-downloader`
- **Debug Mode:** Set `LOG_LEVEL=DEBUG` in `.env`
- **In-App Debugging:** Enable DebugPanel in development mode

---

🎉 **Happy downloading!** Your Ubuntu system is now ready for unified media management!

