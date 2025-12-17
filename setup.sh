#!/bin/bash

# AI-Powered Research Paper Search - Setup Script
# This script sets up the complete development environment

set -e

echo "🔍 AI-Powered Research Paper Search - Setup Script"
echo "=================================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.9+ first."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

echo "✅ Prerequisites check passed!"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p backend/app/{api/v1,core,models,services,utils}
mkdir -p frontend/src/{components,services}

# Start PostgreSQL database
echo "🐘 Starting PostgreSQL database..."
docker-compose up -d postgres

echo "⏳ Waiting for PostgreSQL to initialize (30 seconds)..."
sleep 30

# Check if database is ready
echo "🔍 Checking database connection..."
max_attempts=10
attempt=1
while [ $attempt -le $max_attempts ]; do
    if docker-compose exec -T postgres pg_isready -U postgres -d research_db >/dev/null 2>&1; then
        echo "✅ Database is ready!"
        break
    fi
    echo "⏳ Waiting for database... (attempt $attempt/$max_attempts)"
    sleep 5
    ((attempt++))
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Database failed to start. Please check Docker logs."
    exit 1
fi

# Setup backend
echo "🐍 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate  # On Windows, this would be: venv\Scripts\activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Test database connection
echo "🧪 Testing database connection..."
python -c "
from dotenv import load_dotenv
load_dotenv()
from app.services.vector_service import VectorService
vs = VectorService()
print('✅ Vector service health:', vs.health_check())
"

echo "✅ Backend setup complete!"

# Setup frontend
echo "⚛️ Setting up frontend..."
cd ../frontend

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

echo "✅ Frontend setup complete!"

# Final instructions
echo ""
echo "🎉 Setup complete! Your AI-powered paper search is ready."
echo ""
echo "🚀 To start the application:"
echo ""
echo "Terminal 1 - Start Backend:"
echo "  cd backend"
echo "  source venv/bin/activate  # On Windows: venv\Scripts\activate"
echo "  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Terminal 2 - Start Frontend:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "🌐 Access your application:"
echo "  Frontend: http://localhost:5173"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "🧪 Test the AI search:"
echo "  curl \"http://localhost:8000/api/v1/papers/search/ai?query=detection%20unhealthy%20goat%20using%20deep%20learning\""
echo ""
echo "📚 Happy researching! 📚"
