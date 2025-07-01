#!/bin/bash

# Print colorful messages
print_message() {
    emoji=$1
    message=$2
    echo -e "$emoji $message"
}

# Start production servers
print_message "🚀" "Starting Media Downloader (Production Mode)..."

# Set Python path
export PYTHONPATH=/mnt/md0/hosted/applications/media-downloader

# Set log level for production
export LOGLEVEL=INFO

# Start backend server
print_message "🔧" "Starting backend server..."
nohup uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID $BACKEND_PID"

# Start frontend in development mode temporarily
print_message "🌐" "Starting frontend server..."
cd frontend
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "Frontend started with PID $FRONTEND_PID"

# Give services a moment to start
sleep 2

# Check if services are running
echo -e "\n🔍 Checking services..."
if ps -p $BACKEND_PID > /dev/null; then
    print_message "✅" "Backend is running"
else
    print_message "❌" "Backend failed to start"
fi

if ps -p $FRONTEND_PID > /dev/null; then
    print_message "✅" "Frontend is running"
else
    print_message "❌" "Frontend failed to start"
fi

# Print startup message
echo -e "\n🎉 Production servers started!"
print_message "📱" "Frontend: http://localhost:5173"
print_message "🔧" "Backend API: http://localhost:8000"

# Print helpful commands
echo -e "\n📋 Commands:"
echo "  tail -f backend.log   # View backend logs"
echo "  tail -f frontend.log  # View frontend logs"
echo "  ./stop.sh            # Stop services"
