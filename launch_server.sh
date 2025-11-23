#!/bin/bash
# Script to launch the web server

# Ensure we are in the project root
cd "$(dirname "$0")"

# Activate venv if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the server
echo "Starting server on http://localhost:8000"
uvicorn src.server:app --reload --host 0.0.0.0 --port 8000