#!/bin/bash

echo "🛑 Stopping Media Downloader services..."

# Kill development processes
pkill -u $(whoami) -f "uvicorn src.main:app" 2>/dev/null || true
pkill -u $(whoami) -f "vite" 2>/dev/null || true

# Clean up any remaining node processes
pkill -u $(whoami) -f "node.*vite" 2>/dev/null || true

echo "✅ Development servers stopped."
