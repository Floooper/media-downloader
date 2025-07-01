#!/bin/bash

# Media Downloader Systemd Stop Script
cd /mnt/md0/hosted/applications/media-downloader

echo "🛑 Stopping Media Downloader..."

# Stop using saved PIDs
if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        echo "✅ Backend stopped"
    fi
    rm backend.pid
fi

if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo "✅ Frontend stopped"
    fi
    rm frontend.pid
fi

# Fallback: kill by process name
pkill -u ubuntu -f "uvicorn src.main:app" 2>/dev/null || true
pkill -u ubuntu -f "python3 -m http.server 5173" 2>/dev/null || true

echo "🛑 Services stopped"
