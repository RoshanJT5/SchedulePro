#!/bin/bash
# Quick start script for AI Timetable Generator with Gunicorn

set -e

echo "🚀 Starting AI Timetable Generator with Gunicorn..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "📝 Creating .env from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please edit it with your configuration."
    else
        echo "❌ Error: .env.example not found. Please create .env manually."
        exit 1
    fi
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Check MongoDB connection
echo "🔍 Checking MongoDB connection..."
python3 << EOF
from pymongo import MongoClient
import os
import sys

try:
    uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✅ MongoDB connection successful")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "❌ Cannot start application without database connection"
    exit 1
fi

# Start Gunicorn
echo "🌟 Starting Gunicorn server..."
echo "📍 Server will be available at: http://0.0.0.0:5000"
echo "📊 Workers: $(($(nproc) * 2 + 1))"
echo "🧵 Threads per worker: 4"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================"

exec gunicorn -c gunicorn_config.py app_with_navigation:app
