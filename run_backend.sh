#!/bin/bash

echo "========================================="
echo "Starting AI Auto Caller Backend"
echo "========================================="
echo ""

cd python_backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Using defaults..."
    echo "   For ElevenLabs TTS, create .env from .env.example"
fi

# Start the server
echo "🚀 Starting FastAPI server..."
python main.py
