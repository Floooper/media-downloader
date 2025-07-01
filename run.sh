#!/bin/bash
cd "$(dirname "$0")"
nohup uvicorn src.main:app --reload --port 8001 > app.log 2>&1 &
