# Multi-stage Docker build for AI Data Interoperability Platform
# Healthcare/EHR/HL7 Data Mapping with Sentence-BERT

# Stage 1: Build frontend
FROM node:18-alpine AS frontend-build

WORKDIR /frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install --production

# Copy frontend source
COPY frontend/src ./src
COPY frontend/public ./public

# Build frontend for production
ENV NODE_ENV=production
RUN npm run build

# Stage 2: Backend with Python and AI models
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including curl for health checks
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Sentence-BERT model for faster startup
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy backend code
COPY backend/ ./backend/

# Copy sample data
COPY sample_data_*.csv ./
COPY test_ehr_data.csv ./

# Copy frontend build from previous stage
COPY --from=frontend-build /frontend/build ./frontend/build

# Create necessary directories
RUN mkdir -p /app/data /app/backend/data

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/backend
ENV JWT_SECRET_KEY=change-this-in-production
ENV DATABASE_PATH=/app/data/interop.db
ENV GEMINI_API_KEY=your-gemini-api-key

# Health check (Windows-compatible)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application
WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

