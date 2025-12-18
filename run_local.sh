#!/bin/bash
# Local development runner for agent-will-smith
# Updated to use uvicorn CLI instead of embedded server

set -e

echo "🚀 Starting Agent Will Smith (Local Development)"
echo "================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Copy env.example to .env and configure your settings"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run with uvicorn
echo "Starting uvicorn server..."
echo "Logs: JSON structured format"
echo "Docs: http://localhost:8000/docs"
echo ""

uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info
