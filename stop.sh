#!/bin/bash

echo "Stopping EHR Platform..."
docker-compose down
echo ""
echo "✅ Platform stopped"
read -p "Press Enter to exit..."

