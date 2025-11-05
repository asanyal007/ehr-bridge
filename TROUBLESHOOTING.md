# EHR AI Data Interoperability Platform - Troubleshooting Guide

## Table of Contents
1. [Docker Desktop Issues](#docker-desktop-issues)
2. [WSL 2 Issues](#wsl-2-issues)
3. [Port Conflicts](#port-conflicts)
4. [Memory and Performance](#memory-and-performance)
5. [Network Connectivity](#network-connectivity)
6. [Database Issues](#database-issues)
7. [API and Configuration](#api-and-configuration)
8. [Model Download Failures](#model-download-failures)
9. [Container Issues](#container-issues)
10. [Common Error Messages](#common-error-messages)

## Docker Desktop Issues

### Issue: Docker Desktop won't start

**Symptoms:**
- Docker Desktop icon shows "Starting..." indefinitely
- Error: "Docker Desktop failed to start"

**Solutions:**

1. **Check virtualization:**
   ```powershell
   # Run as Administrator
   Get-ComputerInfo | Select-Object HyperVisorPresent
   ```
   If False, enable virtualization in BIOS.

2. **Restart Docker service:**
   ```powershell
   # Run as Administrator
   Restart-Service docker
   ```

3. **Reset Docker Desktop:**
   - Right-click Docker Desktop icon
   - Select "Troubleshoot"
   - Click "Reset to factory defaults"

4. **Reinstall Docker Desktop:**
   - Uninstall Docker Desktop
   - Delete `C:\Program Files\Docker`
   - Delete `C:\ProgramData\Docker`
   - Reinstall from https://www.docker.com/products/docker-desktop

### Issue: "Docker Desktop requires Windows 10 Pro/Enterprise"

**Solution:**
- Upgrade to Windows 10 Pro, Enterprise, or Education
- Or use Windows 11 (any edition)
- Or enable WSL 2 backend (should work on Windows 10 Home)

### Issue: Docker commands not recognized

**Symptoms:**
- `docker: command not found`
- `docker-compose: command not found`

**Solutions:**

1. **Add Docker to PATH:**
   ```powershell
   # Check if Docker is in PATH
   $env:Path -split ';' | Select-String docker
   ```

2. **Manually add to PATH:**
   - Open System Properties > Environment Variables
   - Add to PATH: `C:\Program Files\Docker\Docker\resources\bin`
   - Restart PowerShell/CMD

3. **Restart Docker Desktop**

## WSL 2 Issues

### Issue: WSL 2 not installed

**Symptoms:**
- Error: "WSL 2 installation is incomplete"
- Docker Desktop fails to start

**Solutions:**

1. **Install WSL 2:**
   ```powershell
   # Run as Administrator
   wsl --install
   ```

2. **Update WSL kernel:**
   ```powershell
   wsl --update
   ```

3. **Set WSL 2 as default:**
   ```powershell
   wsl --set-default-version 2
   ```

4. **Restart computer**

### Issue: WSL 2 kernel update required

**Solution:**
1. Download WSL 2 kernel update: https://aka.ms/wsl2kernel
2. Run the installer
3. Restart Docker Desktop

### Issue: "The WSL 2 Linux kernel is now installed using a separate MSI update package"

**Solution:**
```powershell
# Update WSL
wsl --update

# Restart WSL
wsl --shutdown
```

## Port Conflicts

### Issue: Port 8000 already in use

**Symptoms:**
- Error: "Bind for 0.0.0.0:8000 failed: port is already allocated"
- Application won't start

**Solutions:**

1. **Find process using port 8000:**
   ```powershell
   netstat -ano | findstr :8000
   ```

2. **Kill the process:**
   ```powershell
   # Replace PID with actual process ID
   taskkill /PID <PID> /F
   ```

3. **Change application port:**
   Edit `docker-compose.yml`:
   ```yaml
   services:
     app:
       ports:
         - "8001:8000"  # Use port 8001 instead
   ```

4. **Restart:**
   ```powershell
   docker-compose down
   docker-compose up -d
   ```

### Issue: Port 27017 (MongoDB) already in use

**Solution:**
Same as above, but change MongoDB port:
```yaml
services:
  mongodb:
    ports:
      - "27018:27017"
```

Update `.env`:
```bash
MONGO_PORT=27018
```

## Memory and Performance

### Issue: "Not enough memory" error

**Symptoms:**
- Containers crash randomly
- Error: "Cannot allocate memory"
- Slow performance

**Solutions:**

1. **Increase Docker memory:**
   - Docker Desktop > Settings > Resources
   - Increase Memory to 8 GB or more
   - Click "Apply & Restart"

2. **Increase WSL 2 memory:**
   Create `C:\Users\YourUsername\.wslconfig`:
   ```ini
   [wsl2]
   memory=8GB
   processors=4
   swap=2GB
   ```

3. **Restart WSL:**
   ```powershell
   wsl --shutdown
   ```

4. **Close other applications** to free up RAM

### Issue: Slow performance

**Solutions:**

1. **Allocate more CPUs:**
   - Docker Desktop > Settings > Resources
   - Increase CPUs to 4 or more

2. **Use SSD for Docker data:**
   - Docker Desktop > Settings > Resources > Advanced
   - Change disk image location

3. **Optimize WSL 2:**
   ```powershell
   # Compact WSL disk
   wsl --shutdown
   diskpart
   # In diskpart:
   select vdisk file="C:\Users\YourUsername\AppData\Local\Docker\wsl\data\ext4.vhdx"
   compact vdisk
   exit
   ```

4. **Disable unnecessary services:**
   ```yaml
   # In docker-compose.yml, comment out services you don't need
   ```

### Issue: High CPU usage

**Solutions:**

1. **Check container stats:**
   ```powershell
   docker stats
   ```

2. **Limit container resources:**
   Edit `docker-compose.yml`:
   ```yaml
   services:
     app:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
   ```

3. **Check for infinite loops in logs:**
   ```powershell
   docker-compose logs -f app
   ```

## Network Connectivity

### Issue: Cannot access application at localhost:8000

**Solutions:**

1. **Check if containers are running:**
   ```powershell
   docker-compose ps
   ```

2. **Check container health:**
   ```powershell
   docker inspect --format='{{.State.Health.Status}}' ehr-app
   ```

3. **Check firewall:**
   ```powershell
   # Run as Administrator
   New-NetFirewallRule -DisplayName "EHR Platform" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
   ```

4. **Try alternative URL:**
   - http://127.0.0.1:8000
   - http://localhost:3000

5. **Check if port is listening:**
   ```powershell
   netstat -ano | findstr :8000
   ```

### Issue: Cannot connect to MongoDB

**Solutions:**

1. **Check MongoDB container:**
   ```powershell
   docker-compose logs mongodb
   ```

2. **Verify MongoDB is healthy:**
   ```powershell
   docker inspect --format='{{.State.Health.Status}}' ehr-mongodb
   ```

3. **Test connection:**
   ```powershell
   docker exec -it ehr-mongodb mongosh
   ```

4. **Check network:**
   ```powershell
   docker network ls
   docker network inspect ehr-network
   ```

### Issue: Cannot access from other machines

**Solutions:**

1. **Find your IP:**
   ```powershell
   ipconfig | findstr IPv4
   ```

2. **Allow through firewall:**
   ```powershell
   # Run as Administrator
   New-NetFirewallRule -DisplayName "EHR Platform External" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
   ```

3. **Update docker-compose.yml:**
   ```yaml
   services:
     app:
       ports:
         - "0.0.0.0:8000:8000"  # Explicitly bind to all interfaces
   ```

## Database Issues

### Issue: SQLite database locked

**Symptoms:**
- Error: "database is locked"
- Application hangs on database operations

**Solutions:**

1. **Stop all containers:**
   ```powershell
   docker-compose down
   ```

2. **Check for lock files:**
   ```powershell
   # Look for .db-shm and .db-wal files
   dir data\*.db*
   dir backend\data\*.db*
   ```

3. **Remove lock files (if safe):**
   ```powershell
   del data\*.db-shm
   del data\*.db-wal
   del backend\data\*.db-shm
   del backend\data\*.db-wal
   ```

4. **Restart:**
   ```powershell
   docker-compose up -d
   ```

### Issue: MongoDB won't start

**Solutions:**

1. **Check logs:**
   ```powershell
   docker-compose logs mongodb
   ```

2. **Remove corrupted data:**
   ```powershell
   docker-compose down -v
   docker volume rm ehr-platform-windows_mongodb_data
   docker-compose up -d
   ```
   ⚠️ This deletes all MongoDB data!

3. **Check disk space:**
   ```powershell
   Get-PSDrive C
   ```

### Issue: Data not persisting

**Solutions:**

1. **Check volume mounts:**
   ```powershell
   docker inspect ehr-app | findstr Mounts -A 10
   ```

2. **Verify data directories exist:**
   ```powershell
   dir data
   dir backend\data
   ```

3. **Check permissions:**
   - Right-click data folder > Properties > Security
   - Ensure your user has Full Control

## API and Configuration

### Issue: "Invalid API key" error

**Solutions:**

1. **Verify API key in .env:**
   ```powershell
   type .env | findstr GEMINI_API_KEY
   ```

2. **Get new API key:**
   - Visit: https://makersuite.google.com/app/apikey
   - Create new key
   - Update `.env`

3. **Restart application:**
   ```powershell
   docker-compose restart app
   ```

### Issue: Environment variables not loading

**Solutions:**

1. **Check .env file exists:**
   ```powershell
   dir .env
   ```

2. **Verify .env format:**
   - No spaces around `=`
   - No quotes around values
   - Example: `GEMINI_API_KEY=your-key-here`

3. **Rebuild containers:**
   ```powershell
   docker-compose down
   docker-compose up -d --build
   ```

### Issue: JWT authentication failing

**Solutions:**

1. **Generate new JWT secret:**
   ```powershell
   -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})
   ```

2. **Update .env:**
   ```bash
   JWT_SECRET_KEY=your-new-secret
   ```

3. **Clear browser cookies**

4. **Restart:**
   ```powershell
   docker-compose restart app
   ```

## Model Download Failures

### Issue: Sentence-BERT model download fails

**Symptoms:**
- Container startup takes very long
- Error: "Failed to download model"
- Timeout errors

**Solutions:**

1. **Check internet connection**

2. **Increase Docker timeout:**
   ```yaml
   # In docker-compose.yml
   services:
     app:
       healthcheck:
         start_period: 120s  # Increase from 60s
   ```

3. **Pre-download model:**
   ```powershell
   # After first successful run, model is cached in volume
   docker-compose down
   docker-compose up -d
   ```

4. **Use proxy (if behind firewall):**
   ```yaml
   services:
     app:
       environment:
         - HTTP_PROXY=http://proxy.example.com:8080
         - HTTPS_PROXY=http://proxy.example.com:8080
   ```

### Issue: Model cache not persisting

**Solution:**
Verify volume mount in `docker-compose.yml`:
```yaml
volumes:
  - model_cache:/root/.cache/torch
```

## Container Issues

### Issue: Container keeps restarting

**Solutions:**

1. **Check logs:**
   ```powershell
   docker-compose logs -f app
   ```

2. **Check health:**
   ```powershell
   docker inspect ehr-app
   ```

3. **Disable health check temporarily:**
   ```yaml
   # In docker-compose.yml
   services:
     app:
       # healthcheck:  # Comment out
       #   test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
   ```

4. **Check resource limits:**
   - Ensure enough memory/CPU allocated

### Issue: "Container exited with code 137"

**Cause:** Out of memory

**Solution:**
Increase Docker memory allocation (see Memory and Performance section)

### Issue: "Container exited with code 1"

**Cause:** Application error

**Solutions:**

1. **Check application logs:**
   ```powershell
   docker-compose logs app
   ```

2. **Check for missing dependencies:**
   ```powershell
   docker-compose build --no-cache
   ```

3. **Verify environment variables**

## Common Error Messages

### "ERROR: Couldn't connect to Docker daemon"

**Solution:**
Start Docker Desktop

### "ERROR: Version in '.\docker-compose.yml' is unsupported"

**Solution:**
Update Docker Desktop to latest version

### "ERROR: for app  Cannot start service app: driver failed programming external connectivity"

**Solution:**
Restart Docker Desktop or reboot computer

### "ERRO[0000] error waiting for container: context canceled"

**Solution:**
```powershell
docker-compose down
docker system prune -a
docker-compose up -d --build
```

### "Error response from daemon: Get https://registry-1.docker.io/v2/: net/http: request canceled"

**Solution:**
- Check internet connection
- Restart Docker Desktop
- Check proxy settings

### "exec: 'curl': executable file not found in $PATH"

**Solution:**
The Dockerfile should include curl installation. Rebuild:
```powershell
docker-compose build --no-cache
docker-compose up -d
```

## Getting Help

If none of these solutions work:

1. **Collect diagnostic information:**
   ```powershell
   # System info
   Get-ComputerInfo > system-info.txt
   
   # Docker info
   docker info > docker-info.txt
   docker-compose ps > containers.txt
   docker-compose logs > logs.txt
   
   # Network info
   ipconfig /all > network-info.txt
   ```

2. **Check logs:**
   - Run `logs.bat`
   - Look for ERROR or FATAL messages

3. **Check status:**
   - Run `status.bat`
   - Verify all containers are healthy

4. **Create GitHub issue** (if applicable) with:
   - Error message
   - Steps to reproduce
   - System information
   - Logs

5. **Community support:**
   - Docker forums: https://forums.docker.com
   - Stack Overflow: Tag with `docker` and `docker-compose`

## Prevention Tips

1. **Regular updates:**
   ```powershell
   docker-compose pull
   docker-compose up -d --build
   ```

2. **Regular cleanup:**
   ```powershell
   docker system prune -a --volumes
   ```
   ⚠️ This removes all unused data!

3. **Monitor resources:**
   ```powershell
   docker stats
   ```

4. **Regular backups:**
   - Run backup script weekly
   - Test restore procedure

5. **Keep logs:**
   ```powershell
   docker-compose logs > logs-$(Get-Date -Format 'yyyy-MM-dd').txt
   ```

