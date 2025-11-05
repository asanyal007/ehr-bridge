#!/bin/bash

# ============================================================================
# EHR Platform - macOS Package Builder
# ============================================================================

set -e

echo "Building macOS Deployment Package..."
echo ""

# Create package directory
PACKAGE_NAME="ehr-platform-macos"
PACKAGE_DIR="$PACKAGE_NAME"

if [ -d "$PACKAGE_DIR" ]; then
    rm -rf "$PACKAGE_DIR"
fi
mkdir -p "$PACKAGE_DIR"

# Copy essential files
echo "Copying application files..."
cp -R backend "$PACKAGE_DIR/"
cp -R frontend "$PACKAGE_DIR/"
mkdir -p "$PACKAGE_DIR/data/omop_vocab_seed"
cp -R data/omop_vocab_seed/* "$PACKAGE_DIR/data/omop_vocab_seed/" 2>/dev/null || true

# Copy configuration files
cp Dockerfile "$PACKAGE_DIR/"
cp docker-compose.yml "$PACKAGE_DIR/"
cp .dockerignore "$PACKAGE_DIR/"
cp requirements.txt "$PACKAGE_DIR/"

# Copy sample data
cp sample_data_*.csv "$PACKAGE_DIR/" 2>/dev/null || true
cp test_ehr_data.csv "$PACKAGE_DIR/" 2>/dev/null || true

# Copy scripts
cp start.sh "$PACKAGE_DIR/"
cp stop.sh "$PACKAGE_DIR/"
cp logs.sh "$PACKAGE_DIR/"
cp status.sh "$PACKAGE_DIR/"

# Make scripts executable
chmod +x "$PACKAGE_DIR/start.sh"
chmod +x "$PACKAGE_DIR/stop.sh"
chmod +x "$PACKAGE_DIR/logs.sh"
chmod +x "$PACKAGE_DIR/status.sh"

# Copy documentation
cp README.md "$PACKAGE_DIR/" 2>/dev/null || true
cp DEPLOYMENT_PACKAGE_MACOS.md "$PACKAGE_DIR/" 2>/dev/null || true
cp MACOS_SETUP_GUIDE.md "$PACKAGE_DIR/" 2>/dev/null || true
cp TROUBLESHOOTING_MACOS.md "$PACKAGE_DIR/" 2>/dev/null || true

# Create .env template
cat > "$PACKAGE_DIR/env.template" << 'EOF'
# EHR Platform Environment Configuration

# JWT Secret Key for authentication
JWT_SECRET_KEY=change-this-to-a-secure-random-string

# Google Gemini API Key for AI features
GEMINI_API_KEY=your-gemini-api-key-here

# MongoDB Configuration
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DB=ehr
EOF

# Create README
cat > "$PACKAGE_DIR/README.txt" << 'EOF'
# EHR AI Data Interoperability Platform

## Quick Start

1. Install Docker Desktop for Mac
2. Open Terminal and navigate to this folder
3. Run: ./start.sh
4. Configure your Gemini API key when prompted
5. Wait for the application to start
6. Access at http://localhost:8000

See DEPLOYMENT_PACKAGE_MACOS.md for detailed instructions.
EOF

# Create ZIP package
echo "Creating ZIP archive..."
zip -r "${PACKAGE_NAME}.zip" "$PACKAGE_DIR" -q

echo ""
echo "✅ Package created: ${PACKAGE_NAME}.zip"
echo ""
echo "Package size:"
ls -lh "${PACKAGE_NAME}.zip" | awk '{print $5 "\t" $9}'
echo ""
read -p "Press Enter to exit..."

