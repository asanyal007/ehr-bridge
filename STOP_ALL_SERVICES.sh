#!/bin/bash
# Stop all services for AI Data Interoperability Platform

echo "🛑 Stopping all services..."

# Stop frontend
pkill -f "react-scripts" 2>/dev/null && echo "  ✅ Frontend stopped" || echo "  ⚪ Frontend not running"

# Stop backend
pkill -f "python3 run.py" 2>/dev/null && echo "  ✅ Backend stopped" || echo "  ⚪ Backend not running"

# Stop MongoDB
docker stop ehr-mongodb 2>/dev/null && docker rm ehr-mongodb 2>/dev/null && echo "  ✅ MongoDB stopped" || echo "  ⚪ MongoDB not running"

echo ""
echo "✅ All services stopped"

