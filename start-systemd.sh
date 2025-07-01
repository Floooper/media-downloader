#!/bin/bash

# Media Downloader Systemd Start Script
cd /mnt/md0/hosted/applications/media-downloader

echo "🚀 Starting Media Downloader (Production Mode)..."

# Check if virtual environment exists
if [ ! -d venv ]; then
    echo "❌ Error: Python virtual environment not found."
    exit 1
fi

# Initialize database if needed
echo "📊 Initializing database..."
source venv/bin/activate
python3 -c "
import os
os.makedirs('data', exist_ok=True)
try:
    from src.models import Base
    from sqlalchemy import create_engine
    engine = create_engine('sqlite:///./data/media_downloader.db')
    Base.metadata.create_all(engine)
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'❌ Database initialization failed: {e}')
    exit(1)
"

# Kill any existing processes
pkill -u ubuntu -f "uvicorn src.main:app" 2>/dev/null || true
pkill -u ubuntu -f "vite" 2>/dev/null || true

# Start the backend
echo "🔧 Starting backend server..."
nohup uvicorn src.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!

# Build frontend for production
echo "🌐 Building frontend..."
cd frontend
npm run build

# Start frontend with a simple HTTP server
echo "📱 Starting frontend server..."
cd ../dist
nohup python3 -m http.server 5173 > ../frontend-serve.log 2>&1 &
FRONTEND_PID=$!

cd ..

# Save PIDs for stop script
echo $BACKEND_PID > backend.pid
echo $FRONTEND_PID > frontend.pid

echo "✅ Services started"
echo "📱 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
