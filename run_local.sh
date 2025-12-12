#!/bin/bash
# Quick start script for local development

set -e

echo "🚀 Starting Product Recommendation Agent"
echo "========================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating .env from env.example..."
    cp env.example .env
    echo "✅ .env created. Please edit it with your Databricks credentials before running."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -e .

# Run the application
echo "✅ Starting FastAPI server..."
echo "📍 API will be available at: http://localhost:8000"
echo "📚 API docs available at: http://localhost:8000/docs"
echo ""

python app/main.py

