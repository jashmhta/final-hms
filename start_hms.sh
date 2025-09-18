#!/bin/bash
set -e
echo "🚀 Starting HMS Enterprise-Grade System..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3"
    exit 1
fi
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi
echo "📦 Activating virtual environment..."
source venv/bin/activate
echo "📦 Installing dependencies..."
pip install -r requirements.txt
echo "🗄️ Running database migrations..."
python backend/manage.py migrate
echo "👤 Creating superuser..."
python backend/manage.py createsuperuser --noinput || true
echo "🌐 Starting development server..."
python backend/manage.py runserver 0.0.0.0:8000 &
sleep 3
echo "🔍 Performing health check..."
if curl -s http://localhost:8000/health/ > /dev/null; then
    echo "✅ HMS System started successfully!"
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8000"
    echo "👤 Admin: http://localhost:8000/admin/"
    echo "💚 Health check: http://localhost:8000/health/"
else
    echo "❌ Health check failed. Check the logs for details."
fi
wait