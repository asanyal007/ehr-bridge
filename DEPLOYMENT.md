# Deployment Guide - AI Data Interoperability Platform

Complete guide for deploying the Healthcare EHR/HL7 AI Data Interoperability Platform in production environments.

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [Docker Deployment](#docker-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Security Hardening](#security-hardening)
5. [Performance Optimization](#performance-optimization)
6. [Monitoring & Logging](#monitoring--logging)
7. [Backup & Recovery](#backup--recovery)

---

## Deployment Options

### Option 1: Single Docker Container (Small Teams)
- **Best for**: 1-50 concurrent users
- **Resources**: 2 CPU, 4GB RAM, 20GB storage
- **Setup time**: 10 minutes
- **Complexity**: Low

### Option 2: Docker Compose (Medium Teams)
- **Best for**: 50-200 concurrent users  
- **Resources**: 4 CPU, 8GB RAM, 50GB storage
- **Setup time**: 30 minutes
- **Complexity**: Medium

### Option 3: Kubernetes (Enterprise)
- **Best for**: 200+ concurrent users, multi-tenant
- **Resources**: Scalable (min 8 CPU, 16GB RAM)
- **Setup time**: 2-4 hours
- **Complexity**: High

---

## Docker Deployment

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ehr-interop-prod
    ports:
      - "80:8000"
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - DATABASE_PATH=/app/data/interop.db
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=WARNING
    volumes:
      - ./data:/app/data:rw
      - ./logs:/app/logs:rw
      - ./models_cache:/root/.cache/torch:ro
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: ehr-interop-nginx
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: always
```

### Environment Setup

Create `.env.production`:

```bash
# Security
JWT_SECRET_KEY=<GENERATE_SECURE_32_CHAR_KEY>

# Database
DATABASE_PATH=/app/data/interop.db

# Logging
LOG_LEVEL=WARNING
LOG_FILE=/app/logs/app.log

# API
API_HOST=0.0.0.0
API_PORT=8000
WORKERS=4

# CORS (update with your domain)
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### Generate Secure JWT Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Deploy

```bash
# Set environment
export $(cat .env.production | xargs)

# Build and start
docker-compose -f docker-compose.prod.yml up -d --build

# Verify
docker-compose -f docker-compose.prod.yml logs -f

# Check health
curl http://localhost/api/v1/health
```

---

## Kubernetes Deployment

### 1. Create Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ehr-interop
```

### 2. Create Secrets

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ehr-interop-secrets
  namespace: ehr-interop
type: Opaque
stringData:
  JWT_SECRET_KEY: "<YOUR_SECURE_KEY>"
```

### 3. Persistent Volume

```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ehr-interop-data
  namespace: ehr-interop
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
  storageClassName: standard
```

### 4. Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ehr-interop
  namespace: ehr-interop
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ehr-interop
  template:
    metadata:
      labels:
        app: ehr-interop
    spec:
      containers:
      - name: app
        image: your-registry/ehr-interop:latest
        ports:
        - containerPort: 8000
        env:
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: ehr-interop-secrets
              key: JWT_SECRET_KEY
        - name: DATABASE_PATH
          value: "/app/data/interop.db"
        volumeMounts:
        - name: data
          mountPath: /app/data
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: ehr-interop-data
```

### 5. Service & Ingress

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ehr-interop-service
  namespace: ehr-interop
spec:
  selector:
    app: ehr-interop
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP

---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ehr-interop-ingress
  namespace: ehr-interop
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - ehr-interop.yourdomain.com
    secretName: ehr-interop-tls
  rules:
  - host: ehr-interop.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ehr-interop-service
            port:
              number: 80
```

### Deploy to Kubernetes

```bash
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml
kubectl apply -f pvc.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Verify
kubectl get pods -n ehr-interop
kubectl logs -f deployment/ehr-interop -n ehr-interop
```

---

## Security Hardening

### 1. Update CORS Configuration

In `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### 2. Enable HTTPS

Use Let's Encrypt with Nginx:

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name ehr-interop.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Database Security

```bash
# Set proper file permissions
chmod 600 data/interop.db
chown app:app data/interop.db

# Enable SQLite encryption (optional)
# Install sqlcipher and update database.py
```

### 4. Rate Limiting

Add to `backend/main.py`:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/jobs")
@limiter.limit("10/minute")
async def create_job(request: Request, ...):
    ...
```

---

## Performance Optimization

### 1. Pre-download AI Model

In Dockerfile:

```dockerfile
# Pre-download model during build
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### 2. Use Production WSGI Server

Update `Dockerfile` CMD:

```dockerfile
CMD ["gunicorn", "backend.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

Add to `requirements.txt`:
```
gunicorn==21.2.0
```

### 3. Enable Caching

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

@app.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend())
```

### 4. Database Optimization

```python
# In database.py, add connection pooling
import sqlite3
from contextlib import contextmanager

class ConnectionPool:
    def __init__(self, db_path, max_connections=5):
        self.db_path = db_path
        self.pool = Queue(maxsize=max_connections)
        for _ in range(max_connections):
            self.pool.put(sqlite3.connect(db_path))
```

---

## Monitoring & Logging

### 1. Prometheus Metrics

```python
# backend/main.py
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### 2. Structured Logging

```python
import logging
import json
from pythonjsonlogger import jsonlogger

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)
```

### 3. Health Checks

Enhanced health endpoint:

```python
@app.get("/api/v1/health")
async def health_check():
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "unknown",
        "ai_model": "unknown",
        "disk_usage": "unknown"
    }
    
    try:
        # Check database
        jobs_count = len(db.get_all_jobs())
        health["database"] = f"connected ({jobs_count} jobs)"
    except Exception as e:
        health["database"] = f"error: {str(e)}"
        health["status"] = "unhealthy"
    
    try:
        # Check AI model
        if ai_engine:
            health["ai_model"] = "loaded"
        else:
            health["ai_model"] = "not loaded"
    except Exception as e:
        health["ai_model"] = f"error: {str(e)}"
    
    try:
        # Check disk usage
        import shutil
        total, used, free = shutil.disk_usage("/app/data")
        health["disk_usage"] = f"{used//2**30}GB / {total//2**30}GB"
    except Exception as e:
        health["disk_usage"] = f"error: {str(e)}"
    
    return health
```

---

## Backup & Recovery

### 1. Database Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_PATH="/app/data/interop.db"

# Create backup
sqlite3 $DB_PATH ".backup '$BACKUP_DIR/interop_$DATE.db'"

# Compress
gzip "$BACKUP_DIR/interop_$DATE.db"

# Keep only last 7 days
find $BACKUP_DIR -name "interop_*.db.gz" -mtime +7 -delete

echo "Backup completed: interop_$DATE.db.gz"
```

### 2. Automated Backups with Cron

```bash
# Add to crontab
0 2 * * * /app/backup.sh >> /var/log/backup.log 2>&1
```

### 3. Restore Database

```bash
# Decompress
gunzip interop_20241011_020000.db.gz

# Stop application
docker-compose down

# Replace database
cp interop_20241011_020000.db data/interop.db

# Restart
docker-compose up -d
```

---

## Production Checklist

- [ ] Generate secure JWT secret key
- [ ] Configure CORS with specific domains
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Set up database backups (automated)
- [ ] Configure monitoring and alerts
- [ ] Set proper file permissions
- [ ] Enable rate limiting
- [ ] Pre-download AI model in Docker image
- [ ] Use production WSGI server (Gunicorn)
- [ ] Set up log aggregation
- [ ] Configure health checks
- [ ] Test disaster recovery procedure
- [ ] Document rollback procedure
- [ ] Set up CI/CD pipeline
- [ ] Perform security audit
- [ ] Load testing (100+ concurrent users)

---

## Rollback Procedure

```bash
# 1. Stop current deployment
docker-compose down

# 2. Pull previous image version
docker pull your-registry/ehr-interop:v1.9.0

# 3. Update docker-compose.yml
image: your-registry/ehr-interop:v1.9.0

# 4. Restore database backup
cp backups/interop_previous.db data/interop.db

# 5. Start application
docker-compose up -d

# 6. Verify health
curl http://localhost/api/v1/health
```

---

## Support & Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild image
docker-compose build

# Rolling update (zero downtime)
docker-compose up -d --no-deps --build app
```

### View Logs

```bash
# Real-time logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs app
```

### Database Maintenance

```bash
# Vacuum database (compact)
sqlite3 data/interop.db "VACUUM;"

# Check integrity
sqlite3 data/interop.db "PRAGMA integrity_check;"
```

---

**For questions or issues, refer to the main README.md or open an issue on GitHub.**

