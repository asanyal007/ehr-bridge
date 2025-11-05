#!/bin/bash
# Start all services for AI Data Interoperability Platform
# Including MongoDB, Backend, and Frontend

echo "════════════════════════════════════════════════════════════════"
echo "  🏥 Starting AI Data Interoperability Platform"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Change to project directory
cd "$(dirname "$0")"

# Stop existing services
echo "🛑 Stopping existing services..."
pkill -f "python3 run.py" 2>/dev/null
pkill -f "react-scripts" 2>/dev/null
docker stop ehr-mongodb 2>/dev/null
docker rm ehr-mongodb 2>/dev/null
sleep 2

# Start MongoDB
echo ""
echo "🗄️  Starting MongoDB..."
docker run -d \
  --name ehr-mongodb \
  -p 27017:27017 \
  -v "$(pwd)/mongo_data:/data/db" \
  mongo:7.0

# Wait for MongoDB
echo "   Waiting for MongoDB to be ready..."
sleep 5

# Check MongoDB
if docker ps | grep -q ehr-mongodb; then
    echo "   ✅ MongoDB running on port 27017"
else
    echo "   ❌ MongoDB failed to start"
    exit 1
fi

# Start Backend
echo ""
echo "📡 Starting Backend (FastAPI + Sentence-BERT)..."
cd backend
nohup python3 run.py > backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend
echo "   Waiting for backend to be ready..."
sleep 5

# Check backend
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "   ✅ Backend running on port 8000"
else
    echo "   ⏳ Backend still starting (check backend/backend.log)"
fi

# Start Frontend
echo ""
echo "🎨 Starting Frontend (React + Tailwind)..."
cd frontend
BROWSER=none nohup npm start > frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend
echo "   Waiting for frontend to be ready..."
sleep 10

# Check frontend
if curl -s http://localhost:3000/ > /dev/null 2>&1; then
    echo "   ✅ Frontend running on port 3000"
else
    echo "   ⏳ Frontend still starting (check frontend/frontend.log)"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ ALL SERVICES STARTED"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Frontend:  http://localhost:3000"
echo "📡 Backend:   http://localhost:8000"
echo "📚 API Docs:  http://localhost:8000/docs"
echo "🗄️  MongoDB:  localhost:27017"
echo ""
echo "🆕 New Feature: HL7 Viewer"
echo "   Click '📋 HL7 Viewer' button in the UI to:"
echo "   • Ingest HL7 v2 messages"
echo "   • View staged messages in MongoDB"
echo "   • Parse and visualize HL7 structures"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Check status:"
echo "   curl http://localhost:8000/api/v1/health | python3 -m json.tool"
echo ""
echo "🛑 Stop all services:"
echo "   ./STOP_ALL_SERVICES.sh"
echo ""
echo "🎉 Platform ready! Open http://localhost:3000"
echo ""

