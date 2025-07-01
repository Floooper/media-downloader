#!/bin/bash

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install backend dependencies
pip install fastapi uvicorn sqlalchemy aiohttp python-multipart python-dotenv

# Create frontend project
rm -rf frontend
npm create vite@latest frontend -- --template react-ts
cd frontend

# Install frontend dependencies
npm install
npm install --legacy-peer-deps @mantine/core @mantine/hooks @mantine/form @mantine/notifications @tabler/icons-react axios react-query

# Create necessary directories
mkdir -p src/{components,services,types}

echo "Setup complete! To start the application:"
echo "1. Terminal 1 (Backend): source venv/bin/activate && uvicorn src.main:app --reload"
echo "2. Terminal 2 (Frontend): cd frontend && npm run dev"

