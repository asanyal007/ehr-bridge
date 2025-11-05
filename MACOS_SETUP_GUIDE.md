# EHR AI Data Interoperability Platform - macOS Setup Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Docker Desktop Installation](#docker-desktop-installation)
3. [Application Deployment](#application-deployment)
4. [Configuration](#configuration)
5. [Network Configuration](#network-configuration)
6. [Performance Tuning](#performance-tuning)
7. [Backup Procedures](#backup-procedures)
8. [Security Best Practices](#security-best-practices)
9. [Apple Silicon Specific](#apple-silicon-specific)

## Prerequisites

### System Requirements Check

Before starting, verify your system meets these requirements:

**macOS Version:**
```bash
sw_vers
```

**RAM:**
```bash
sysctl hw.memsize | awk '{print $2/1024/1024/1024 " GB"}'
```

**CPU:**
```bash
sysctl -n machdep.cpu.brand_string
sysctl -n hw.ncpu
```

**Disk Space:**
```bash
df -h /
```

**Architecture (Intel vs Apple Silicon):**
```bash
uname -m
# x86_64 = Intel
# arm64 = Apple Silicon (M1/M2/M3)
```

### Required Software
- macOS 11 (Big Sur) or later
- At least 8 GB RAM (16 GB recommended)
- 20 GB free disk space (50 GB recommended)
- Internet connection for downloads

## Docker Desktop Installation

### Step 1: Download Docker Desktop

1. **Visit Docker Desktop download page:**
   - https://www.docker.com/products/docker-desktop

2. **Choose the correct version:**
   - **Apple Silicon (M1/M2/M3)**: Click "Download for Mac - Apple Chip"
   - **Intel**: Click "Download for Mac - Intel Chip"

3. **Verify download:**
   ```bash
   ls -lh ~/Downloads/Docker.dmg
   ```

### Step 2: Install Docker Desktop

1. **Open the DMG file:**
   ```bash
   open ~/Downloads/Docker.dmg
   ```
   Or double-click `Docker.dmg` in Finder

2. **Drag Docker to Applications:**
   - In the opened window, drag the Docker icon to the Applications folder
   - Wait for the copy to complete

3. **Eject the DMG:**
   ```bash
   hdiutil detach /Volumes/Docker
   ```

### Step 3: Launch Docker Desktop

1. **Open Docker from Applications:**
   ```bash
   open -a Docker
   ```
   Or find Docker in Applications folder and double-click

2. **Grant necessary permissions:**
   - Click "OK" when prompted for privileged access
   - Enter your Mac password when requested
   - Allow Docker in System Preferences > Security & Privacy if prompted

3. **Accept license agreement:**
   - Read and accept the Docker Subscription Service Agreement

4. **Wait for Docker to start:**
   - Watch for "Docker Desktop is running" notification
   - Docker icon in menu bar should show green status

5. **Verify installation:**
   ```bash
   docker --version
   docker-compose --version
   ```

### Step 4: Configure Docker Desktop

1. **Open Docker Desktop Preferences:**
   - Click Docker icon in menu bar
   - Select "Preferences" or "Settings"

2. **Resources > Advanced:**
   - **CPUs**: Allocate at least 2 (recommended: 4)
   - **Memory**: Allocate at least 4 GB (recommended: 8 GB)
   - **Swap**: 1 GB
   - **Disk image size**: 60 GB

3. **General Settings:**
   - ✅ Start Docker Desktop when you log in
   - ✅ Use gRPC FUSE for file sharing (better performance)
   - ✅ Send usage statistics (optional)

4. **For Apple Silicon Macs:**
   - ✅ Use Rosetta for x86/amd64 emulation on Apple Silicon
   - This ensures compatibility with x86 images

5. **Click "Apply & Restart"**

## Application Deployment

### Step 1: Extract Package

1. **Extract the ZIP file:**
   ```bash
   cd ~/Downloads
   unzip ehr-platform-macos.zip
   cd ehr-platform-macos
   ```

2. **Verify contents:**
   ```bash
   ls -la
   ```

### Step 2: Get Gemini API Key

1. **Visit:** https://makersuite.google.com/app/apikey
2. **Sign in** with Google account
3. **Click "Create API Key"**
4. **Copy the API key** (keep it secure!)

### Step 3: Run Startup Script

1. **Make scripts executable (if needed):**
   ```bash
   chmod +x start.sh stop.sh logs.sh status.sh
   ```

2. **Run the startup script:**
   ```bash
   ./start.sh
   ```

3. **When text editor opens:**
   - Paste your Gemini API key
   - Save the file (Cmd+S in nano: Ctrl+O, Enter, Ctrl+X)
   - Close the editor

4. **Wait for deployment:**
   - First run: 3-5 minutes (downloads images and models)
   - Subsequent runs: 20-30 seconds

### Step 4: Verify Deployment

1. **Check container status:**
   ```bash
   docker-compose ps
   ```

2. **Expected output:**
   ```
   NAME          IMAGE                    STATUS         PORTS
   ehr-app       ehr-platform-macos_app   Up (healthy)   0.0.0.0:8000->8000/tcp
   ehr-mongodb   mongo:7.0                Up (healthy)   0.0.0.0:27017->27017/tcp
   ```

3. **Access the application:**
   - Open browser: http://localhost:8000
   - Login with default credentials:
     - Username: `admin`
     - Password: `admin123`

## Configuration

### Environment Variables

Edit `.env` file to customize:

```bash
# Using nano
nano .env

# Using vim
vim .env

# Using TextEdit
open -e .env

# Using VS Code (if installed)
code .env
```

Configuration options:
```bash
# JWT Secret Key (change for production!)
JWT_SECRET_KEY=your-secure-random-string-here

# Google Gemini API Key
GEMINI_API_KEY=your-actual-api-key

# MongoDB Configuration
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DB=ehr
```

### Generate Secure JWT Secret

```bash
# Method 1: Using openssl
openssl rand -base64 32

# Method 2: Using /dev/urandom
LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 32

# Method 3: Using Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Port Configuration

If ports 8000 or 27017 are already in use:

1. **Check what's using the port:**
   ```bash
   lsof -i :8000
   lsof -i :27017
   ```

2. **Edit `docker-compose.yml`:**
   ```bash
   nano docker-compose.yml
   ```

3. **Change ports:**
   ```yaml
   services:
     app:
       ports:
         - "8001:8000"  # Change external port
     mongodb:
       ports:
         - "27018:27017"  # Change external port
   ```

4. **Restart:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Network Configuration

### Firewall Configuration

1. **Enable macOS Firewall:**
   - System Preferences > Security & Privacy > Firewall
   - Click "Turn On Firewall"
   - Click "Firewall Options"
   - Allow Docker

2. **Allow incoming connections:**
   ```bash
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /Applications/Docker.app/Contents/MacOS/Docker
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /Applications/Docker.app/Contents/MacOS/Docker
   ```

### Access from Other Machines

To access from other computers on your network:

1. **Find your IP address:**
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

2. **Allow through firewall:**
   - System Preferences > Security & Privacy > Firewall > Firewall Options
   - Uncheck "Block all incoming connections"
   - Add Docker to allowed apps

3. **Access from other machines:**
   - http://YOUR-IP-ADDRESS:8000

### Network Troubleshooting

```bash
# Test Docker network
docker network ls
docker network inspect ehr-network

# Test connectivity
curl http://localhost:8000/api/v1/health

# Check DNS resolution
docker exec ehr-app ping -c 3 mongodb
```

## Performance Tuning

### Optimize Docker Resources

1. **Increase memory allocation:**
   - Docker Desktop > Preferences > Resources
   - Memory: 8-16 GB (depending on available RAM)

2. **Increase CPU allocation:**
   - CPUs: 4-8 cores (depending on available cores)

3. **Use SSD for Docker data:**
   - Docker stores data in `~/Library/Containers/com.docker.docker`
   - Ensure this is on SSD, not external drive

### File Sharing Performance

1. **Enable gRPC FUSE:**
   - Docker Desktop > Preferences > General
   - ✅ Use gRPC FUSE for file sharing

2. **Optimize volume mounts:**
   - Use named volumes instead of bind mounts when possible
   - Current setup already optimized

### Database Optimization

**SQLite:**
```bash
# Databases are stored in ./data and ./backend/data
# Ensure these directories are on SSD

# Check disk performance
diskutil info / | grep "Solid State"
```

**MongoDB:**
```bash
# Data persists in Docker volume
# Check volume location
docker volume inspect ehr-platform-macos_mongodb_data

# Optimize MongoDB settings (if needed)
docker exec ehr-mongodb mongosh --eval "db.adminCommand({setParameter: 1, internalQueryExecMaxBlockingSortBytes: 335544320})"
```

## Backup Procedures

### Automated Backup Script

Create `backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR=~/EHR-Backups/$(date +%Y%m%d_%H%M%S)

echo "Creating backup directory..."
mkdir -p "$BACKUP_DIR"

echo "Backing up SQLite databases..."
cp -R data "$BACKUP_DIR/"
cp -R backend/data "$BACKUP_DIR/backend-data"

echo "Exporting MongoDB data..."
docker exec ehr-mongodb mongodump --out=/data/backup
docker cp ehr-mongodb:/data/backup "$BACKUP_DIR/mongodb"

echo "Creating archive..."
cd ~/EHR-Backups
tar -czf "$(basename $BACKUP_DIR).tar.gz" "$(basename $BACKUP_DIR)"
rm -rf "$(basename $BACKUP_DIR)"

echo "Backup complete: $(basename $BACKUP_DIR).tar.gz"
```

Make it executable:
```bash
chmod +x backup.sh
```

### Manual Backup

```bash
# Stop the platform
./stop.sh

# Backup data directories
tar -czf ehr-backup-$(date +%Y%m%d).tar.gz data backend/data

# Backup MongoDB
docker-compose up -d mongodb
docker exec ehr-mongodb mongodump --out=/data/backup
docker cp ehr-mongodb:/data/backup ./mongodb-backup
tar -czf mongodb-backup-$(date +%Y%m%d).tar.gz mongodb-backup
rm -rf mongodb-backup

# Restart platform
./start.sh
```

### Restore from Backup

```bash
# Stop the platform
./stop.sh
docker-compose down -v

# Restore SQLite databases
tar -xzf ehr-backup-YYYYMMDD.tar.gz

# Start MongoDB
docker-compose up -d mongodb

# Restore MongoDB
tar -xzf mongodb-backup-YYYYMMDD.tar.gz
docker cp mongodb-backup ehr-mongodb:/data/backup
docker exec ehr-mongodb mongorestore /data/backup
rm -rf mongodb-backup

# Start full platform
./start.sh
```

### Automated Backup with Cron

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd ~/ehr-platform-macos && ./backup.sh

# Add weekly cleanup (keep last 4 weeks)
0 3 * * 0 find ~/EHR-Backups -name "*.tar.gz" -mtime +28 -delete
```

## Security Best Practices

### 1. Change Default Credentials

After first login:
- Navigate to Settings > Users
- Change admin password
- Create individual user accounts

### 2. Secure JWT Secret

```bash
# Generate strong secret
openssl rand -base64 32

# Update .env
nano .env
# Change JWT_SECRET_KEY to generated value
```

### 3. Secure API Keys

```bash
# Never commit .env to version control
echo ".env" >> .gitignore

# Protect .env file
chmod 600 .env

# Rotate API keys regularly
```

### 4. Network Security

For production:
```bash
# Use HTTPS (add reverse proxy like nginx)
# Restrict MongoDB access to localhost only
# Use VPN for remote access
```

### 5. macOS Security Features

```bash
# Enable FileVault (full disk encryption)
# System Preferences > Security & Privacy > FileVault

# Enable Firewall
# System Preferences > Security & Privacy > Firewall

# Keep macOS updated
softwareupdate -l
```

## Apple Silicon Specific

### Rosetta 2 Configuration

Docker Desktop automatically handles architecture differences, but you can verify:

```bash
# Check if Rosetta is enabled in Docker
docker info | grep -i rosetta

# Verify native ARM64 images are used when available
docker inspect ehr-app | grep Architecture
```

### Performance Optimization for M1/M2/M3

```bash
# Apple Silicon runs Docker natively - no emulation overhead
# Ensure native ARM images are used when available

# Check image architecture
docker image inspect ehr-platform-macos_app | grep Architecture

# Force ARM64 build (if needed)
docker-compose build --build-arg BUILDPLATFORM=linux/arm64
```

### Common Apple Silicon Issues

**Issue: x86 image running slow**
```bash
# Solution: Ensure Rosetta is enabled
# Docker Desktop > Settings > General
# ✅ Use Rosetta for x86/amd64 emulation
```

**Issue: Build fails on Apple Silicon**
```bash
# Solution: Use multi-platform build
docker buildx create --use
docker buildx build --platform linux/arm64,linux/amd64 -t ehr-app .
```

## Monitoring and Maintenance

### View Logs

```bash
# All logs
./logs.sh

# Specific service
docker-compose logs -f app
docker-compose logs -f mongodb

# Last 100 lines
docker-compose logs --tail=100 app

# Logs since 1 hour ago
docker-compose logs --since=1h app
```

### Check Health

```bash
# Container health
docker inspect --format='{{.State.Health.Status}}' ehr-app

# Resource usage
docker stats

# Disk usage
docker system df
```

### Cleanup

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes (careful!)
docker volume prune

# Remove everything unused
docker system prune -a --volumes
```

### Update Docker Desktop

```bash
# Check for updates
# Docker Desktop > Check for Updates

# Or download latest from:
# https://www.docker.com/products/docker-desktop
```

## Troubleshooting

See `TROUBLESHOOTING_MACOS.md` for detailed troubleshooting steps.

## Support

- **Documentation**: Check all `.md` files in package
- **Logs**: Run `./logs.sh` for detailed logs
- **Status**: Run `./status.sh` for system status
- **Community**: Docker forums, Stack Overflow
- **Docker Desktop**: https://docs.docker.com/desktop/mac/

## Useful Commands Reference

```bash
# Start platform
./start.sh

# Stop platform
./stop.sh

# View logs
./logs.sh

# Check status
./status.sh

# Restart services
docker-compose restart

# Rebuild and restart
docker-compose up -d --build

# View running containers
docker ps

# Execute command in container
docker exec -it ehr-app bash

# Connect to MongoDB
docker exec -it ehr-mongodb mongosh

# Check Docker disk usage
docker system df

# Clean up everything
docker system prune -a --volumes
```

