#!/bin/bash
# start.sh - Script to start both LeafNode Backend and Frontend

# Function to clean up background processes on exit (Ctrl+C)
cleanup() {
    echo -e "\n🛑 Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        echo "Killing Backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "Killing Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo "Goodbye!"
    exit 0
}

# Catch the Ctrl+C signal and run the cleanup function
trap cleanup SIGINT SIGTERM

echo "🌱 Starting LeafNode Application..."

# ====================
# 1. SETUP & RUN BACKEND
# ====================
echo -e "\n[1/2] ⚙️ Setting up Backend..."
cd leafnode-backend

# Check if .venv exists, if not create it
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies and fail fast if installation fails
echo "Installing backend dependencies..."
if ! pip install -r requirements.txt; then
    echo "❌ Failed to install backend dependencies."
    exit 1
fi

# Make sure .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env found in backend. Creating one from .env.example..."
    cp .env.example .env
    echo "Lütfen daha sonra .env içindeki InfluxDB / Postgres ayarlarını güncelleyin!"
fi

# Run database migrations
echo "Running database migrations..."
if ! alembic upgrade head; then
    echo "❌ Migration encountered an issue. (Did you set PostgreSQL DATABASE_URL correctly?)"
    exit 1
fi

# Start backend in the background
echo "🚀 Starting FastAPI backend on http://localhost:8000 ..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 2 # Let the backend initialize

# Go back to root
cd ..

# ====================
# 2. SETUP & RUN FRONTEND
# ====================
echo -e "\n[2/2] 🖥️ Setting up Frontend..."
cd leafnode-frontend

# Install node modules
echo "Installing frontend dependencies..."
npm install > /dev/null 2>&1

# Start frontend in the background
echo "🚀 Starting Vite frontend..."
npm run dev &
FRONTEND_PID=$!

# ====================
# 3. IDLE AND WAIT
# ====================
echo -e "\n✅ Bütün sistem çalışır durumda! Uygulamayı kapatmak için Ctrl+C'ye basabilirsiniz."
wait
