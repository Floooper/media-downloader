#!/bin/bash

echo "🔍 Media Downloader Status Check"
echo "================================="

# Check if Docker container is running
if command -v docker &> /dev/null; then
    if sudo docker ps | grep -q "media-downloader"; then
        echo "📦 Docker: Container running ✅"
        echo "   Container ID: $(sudo docker ps --format 'table {{.ID}}\t{{.Status}}' | grep media-downloader | awk '{print $1}')"
        echo "   Status: $(sudo docker ps --format 'table {{.Status}}' | grep -A1 STATUS | tail -1)"
    else
        echo "📦 Docker: No container running ❌"
    fi
else
    echo "📦 Docker: Not available"
fi

echo ""

# Check backend health
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "🔧 Backend: Healthy ✅"
    echo "   URL: http://localhost:8000"
    
    # Get system info
    if command -v jq &> /dev/null; then
        MEMORY=$(curl -s http://localhost:8000/api/system/info | jq -r '.memory_usage.percent')
        VERSION=$(curl -s http://localhost:8000/api/system/info | jq -r '.version')
        echo "   Version: $VERSION"
        echo "   Memory: ${MEMORY}%"
    fi
else
    echo "🔧 Backend: Not responding ❌"
fi

echo ""

# Check frontend
if curl -s -I http://localhost:5173 > /dev/null 2>&1; then
    echo "📱 Frontend: Accessible ✅"
    echo "   URL: http://localhost:5173"
else
    echo "📱 Frontend: Not accessible ❌"
fi

echo ""

# Check processes
echo "🔄 Active Processes:"
if sudo docker ps | grep -q "media-downloader"; then
    echo "   Running in Docker container"
    sudo docker exec media-downloader ps aux | grep -E "(python|node)" | grep -v grep | while read line; do
        echo "   $line"
    done
else
    echo "   Local processes:"
    ps aux | grep -E "(uvicorn|vite)" | grep -v grep | while read line; do
        echo "   $line"
    done
fi

echo ""
echo "🎯 Quick Actions:"
echo "   ./start.sh  - Start services"
echo "   ./stop.sh   - Stop services"
echo "   sudo docker compose logs -f  - View logs"
