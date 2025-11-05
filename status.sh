#!/bin/bash

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    EHR Platform Status Dashboard                             ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Container Status:"
echo "─────────────────"
docker-compose ps
echo ""
echo "Health Checks:"
echo "──────────────"
docker inspect --format='{{.Name}}: {{.State.Health.Status}}' ehr-app ehr-mongodb 2>/dev/null || echo "Containers not running"
echo ""
echo "Resource Usage:"
echo "───────────────"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
echo ""
read -p "Press Enter to exit..."

