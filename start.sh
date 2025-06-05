#!/bin/bash

echo "🚀 Starting Gotham Lights..."
echo ""

# Kill any existing processes on the ports
echo "🔧 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

# Wait a moment for cleanup
sleep 2

echo "🎯 Starting Backend API (FastAPI)..."
# Start backend in background
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "🎨 Starting Frontend (React)..."
# Start frontend in background
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Both servers starting..."
echo "🔗 Backend API: http://localhost:8000"
echo "🔗 Frontend UI: http://localhost:5173"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    # Kill any remaining processes on the ports
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
    echo "✅ Stopped!"
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup SIGINT

# Wait for user to press Ctrl+C
wait 