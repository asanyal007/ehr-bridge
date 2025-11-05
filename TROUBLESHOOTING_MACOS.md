# EHR AI Data Interoperability Platform - macOS Troubleshooting Guide

## Table of Contents
1. [Docker Desktop Issues](#docker-desktop-issues)
2. [Permission Issues](#permission-issues)
3. [Port Conflicts](#port-conflicts)
4. [Memory and Performance](#memory-and-performance)
5. [Network Connectivity](#network-connectivity)
6. [Database Issues](#database-issues)
7. [API and Configuration](#api-and-configuration)
8. [Model Download Failures](#model-download-failures)
9. [Container Issues](#container-issues)
10. [Apple Silicon Specific](#apple-silicon-specific)
11. [Common Error Messages](#common-error-messages)

## Docker Desktop Issues

### Issue: Docker Desktop won't start

**Symptoms:**
- Docker icon shows "Starting..." indefinitely
- Error: "Docker Desktop failed to start"

**Solutions:**

1. **Check system requirements:**
   ```bash
   sw_vers  # Should be macOS 11 or later
   ```

2. **Restart Docker:**
   ```bash
   killall Docker
   open -a Docker
   ```

3. **Reset Docker Desktop:**
   - Click Docker icon in menu bar
   - Select "Troubleshoot"
   - Click "Reset to factory defaults"
   - Confirm and restart

4. **Check for conflicting applications:**
   ```bash
   # Check if other virtualization software is running
   ps aux | grep -i virtual
   ps aux | grep -i vmware
   ```

5. **Reinstall Docker Desktop:**
   ```bash
   # Uninstall
   /Applications/Docker.app/Contents/MacOS/uninstall
   
   # Remove data
   rm -rf ~/Library/Group\ Containers/group.com.docker
   rm -rf ~/Library/Containers/com.docker.docker
   
   # Reinstall from https://www.docker.com/products/docker-desktop
   ```

### Issue: "Docker Desktop requires a newer version of macOS"

**Solution:**
- Update macOS to Big Sur (11.0) or later
- System Preferences > Software Update

### Issue: Docker commands not recognized

**Symptoms:**
- `docker: command not found`
- `docker-compose: command not found`

**Solutions:**

1. **Check if Docker is in PATH:**
   ```bash
   echo $PATH | grep docker
   ```

2. **Add Docker to PATH:**
   ```bash
   # Add to ~/.zshrc or ~/.bash_profile
   echo 'export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

3. **Verify Docker is running:**
   ```bash
   open -a Docker
   # Wait for Docker to start
   docker --version
   ```

### Issue: "Cannot connect to the Docker daemon"

**Solutions:**

1. **Start Docker Desktop:**
   ```bash
   open -a Docker
   ```

2. **Check Docker daemon:**
   ```bash
   docker info
   ```

3. **Reset Docker:**
   ```bash
   killall Docker
   rm ~/Library/Group\ Containers/group.com.docker/docker.sock
   open -a Docker
   ```

## Permission Issues

### Issue: "Permission denied" when running scripts

**Symptoms:**
- `./start.sh: Permission denied`
- Cannot execute shell scripts

**Solutions:**

1. **Make scripts executable:**
   ```bash
   chmod +x start.sh stop.sh logs.sh status.sh
   ```

2. **Verify permissions:**
   ```bash
   ls -la *.sh
   # Should show -rwxr-xr-x
   ```

3. **Run with bash explicitly:**
   ```bash
   bash start.sh
   ```

### Issue: "Operation not permitted" when accessing files

**Solutions:**

1. **Grant Full Disk Access to Terminal:**
   - System Preferences > Security & Privacy > Privacy
   - Select "Full Disk Access"
   - Click lock to make changes
   - Add Terminal (or iTerm2)

2. **Grant Full Disk Access to Docker:**
   - Same steps as above
   - Add Docker.app

3. **Check file ownership:**
   ```bash
   ls -la data/
   # If owned by root, fix it:
   sudo chown -R $USER:staff data/
   sudo chown -R $USER:staff backend/data/
   ```

### Issue: "Docker Desktop needs privileged access"

**Solution:**
- Enter your Mac password when prompted
- This is normal and required for Docker to function

## Port Conflicts

### Issue: Port 8000 already in use

**Symptoms:**
- Error: "Bind for 0.0.0.0:8000 failed: port is already allocated"
- Application won't start

**Solutions:**

1. **Find process using port 8000:**
   ```bash
   lsof -i :8000
   ```

2. **Kill the process:**
   ```bash
   # Replace PID with actual process ID from lsof output
   kill -9 <PID>
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
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Issue: Port 27017 (MongoDB) already in use

**Solutions:**

1. **Check if MongoDB is already running:**
   ```bash
   lsof -i :27017
   ps aux | grep mongod
   ```

2. **Stop existing MongoDB:**
   ```bash
   # If installed via Homebrew
   brew services stop mongodb-community
   
   # Or kill the process
   killall mongod
   ```

3. **Change MongoDB port:**
   Edit `docker-compose.yml`:
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
   - Docker Desktop > Preferences > Resources
   - Increase Memory to 8 GB or more
   - Click "Apply & Restart"

2. **Check available memory:**
   ```bash
   vm_stat
   # Or
   top -l 1 | grep PhysMem
   ```

3. **Close other applications:**
   ```bash
   # Check memory usage
   top -o mem
   
   # Close memory-hungry apps
   ```

4. **Restart Docker:**
   ```bash
   killall Docker
   open -a Docker
   ```

### Issue: Slow performance

**Solutions:**

1. **Allocate more CPUs:**
   - Docker Desktop > Preferences > Resources
   - Increase CPUs to 4 or more

2. **Enable gRPC FUSE:**
   - Docker Desktop > Preferences > General
   - ✅ Use gRPC FUSE for file sharing

3. **Check disk performance:**
   ```bash
   # Ensure Docker data is on SSD
   diskutil info / | grep "Solid State"
   ```

4. **Optimize Docker:**
   ```bash
   # Clean up unused resources
   docker system prune -a
   
   # Restart Docker
   killall Docker && open -a Docker
   ```

5. **For Apple Silicon:**
   - Ensure Rosetta is enabled in Docker settings
   - Check if native ARM images are being used

### Issue: High CPU usage

**Solutions:**

1. **Check container stats:**
   ```bash
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

3. **Check for infinite loops:**
   ```bash
   docker-compose logs -f app | grep -i error
   ```

4. **Restart containers:**
   ```bash
   docker-compose restart
   ```

## Network Connectivity

### Issue: Cannot access application at localhost:8000

**Solutions:**

1. **Check if containers are running:**
   ```bash
   docker-compose ps
   ```

2. **Check container health:**
   ```bash
   docker inspect --format='{{.State.Health.Status}}' ehr-app
   ```

3. **Test connectivity:**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

4. **Try alternative URLs:**
   - http://127.0.0.1:8000
   - http://localhost:3000

5. **Check if port is listening:**
   ```bash
   lsof -i :8000
   ```

6. **Restart containers:**
   ```bash
   docker-compose restart app
   ```

### Issue: Cannot connect to MongoDB

**Solutions:**

1. **Check MongoDB container:**
   ```bash
   docker-compose logs mongodb
   ```

2. **Verify MongoDB is healthy:**
   ```bash
   docker inspect --format='{{.State.Health.Status}}' ehr-mongodb
   ```

3. **Test connection:**
   ```bash
   docker exec -it ehr-mongodb mongosh
   ```

4. **Check network:**
   ```bash
   docker network ls
   docker network inspect ehr-network
   ```

5. **Restart MongoDB:**
   ```bash
   docker-compose restart mongodb
   ```

### Issue: Cannot access from other machines

**Solutions:**

1. **Find your IP:**
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   # Or
   ipconfig getifaddr en0  # WiFi
   ipconfig getifaddr en1  # Ethernet
   ```

2. **Check macOS Firewall:**
   - System Preferences > Security & Privacy > Firewall
   - Click "Firewall Options"
   - Ensure Docker is allowed

3. **Allow Docker through firewall:**
   ```bash
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /Applications/Docker.app
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /Applications/Docker.app
   ```

4. **Update docker-compose.yml:**
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
   ```bash
   docker-compose down
   ```

2. **Check for lock files:**
   ```bash
   find . -name "*.db-shm" -o -name "*.db-wal"
   ```

3. **Remove lock files (if safe):**
   ```bash
   rm data/*.db-shm data/*.db-wal
   rm backend/data/*.db-shm backend/data/*.db-wal
   ```

4. **Fix permissions:**
   ```bash
   chmod 644 data/*.db
   chmod 644 backend/data/*.db
   ```

5. **Restart:**
   ```bash
   docker-compose up -d
   ```

### Issue: MongoDB won't start

**Solutions:**

1. **Check logs:**
   ```bash
   docker-compose logs mongodb
   ```

2. **Remove corrupted data:**
   ```bash
   docker-compose down -v
   docker volume rm ehr-platform-macos_mongodb_data
   docker-compose up -d
   ```
   ⚠️ This deletes all MongoDB data!

3. **Check disk space:**
   ```bash
   df -h
   ```

4. **Verify MongoDB image:**
   ```bash
   docker pull mongo:7.0
   docker-compose up -d mongodb
   ```

### Issue: Data not persisting

**Solutions:**

1. **Check volume mounts:**
   ```bash
   docker inspect ehr-app | grep Mounts -A 10
   ```

2. **Verify data directories exist:**
   ```bash
   ls -la data/
   ls -la backend/data/
   ```

3. **Check permissions:**
   ```bash
   ls -la data/
   # Should be owned by your user, not root
   
   # Fix if needed:
   sudo chown -R $USER:staff data/
   sudo chown -R $USER:staff backend/data/
   ```

4. **Verify volumes:**
   ```bash
   docker volume ls
   docker volume inspect ehr-platform-macos_mongodb_data
   ```

## API and Configuration

### Issue: "Invalid API key" error

**Solutions:**

1. **Verify API key in .env:**
   ```bash
   cat .env | grep GEMINI_API_KEY
   ```

2. **Get new API key:**
   - Visit: https://makersuite.google.com/app/apikey
   - Create new key
   - Update `.env`:
     ```bash
     nano .env
     # Update GEMINI_API_KEY
     ```

3. **Restart application:**
   ```bash
   docker-compose restart app
   ```

4. **Check API key format:**
   - Should start with "AIza"
   - No quotes around the value in .env
   - No extra spaces

### Issue: Environment variables not loading

**Solutions:**

1. **Check .env file exists:**
   ```bash
   ls -la .env
   ```

2. **Verify .env format:**
   ```bash
   cat .env
   # Should have no spaces around =
   # Example: GEMINI_API_KEY=your-key-here
   ```

3. **Check for hidden characters:**
   ```bash
   cat -A .env
   # Should not show ^M or other special characters
   ```

4. **Rebuild containers:**
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

### Issue: JWT authentication failing

**Solutions:**

1. **Generate new JWT secret:**
   ```bash
   openssl rand -base64 32
   ```

2. **Update .env:**
   ```bash
   nano .env
   # Update JWT_SECRET_KEY with generated value
   ```

3. **Clear browser cookies:**
   - Chrome: Cmd+Shift+Delete
   - Safari: Cmd+,  > Privacy > Manage Website Data

4. **Restart:**
   ```bash
   docker-compose restart app
   ```

## Model Download Failures

### Issue: Sentence-BERT model download fails

**Symptoms:**
- Container startup takes very long
- Error: "Failed to download model"
- Timeout errors

**Solutions:**

1. **Check internet connection:**
   ```bash
   ping -c 3 huggingface.co
   ```

2. **Increase Docker timeout:**
   Edit `docker-compose.yml`:
   ```yaml
   services:
     app:
       healthcheck:
         start_period: 120s  # Increase from 60s
   ```

3. **Manual download:**
   ```bash
   # Download model to cache
   docker-compose run --rm app python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
   ```

4. **Check proxy settings (if behind firewall):**
   Edit `docker-compose.yml`:
   ```yaml
   services:
     app:
       environment:
         - HTTP_PROXY=http://proxy.example.com:8080
         - HTTPS_PROXY=http://proxy.example.com:8080
   ```

### Issue: Model cache not persisting

**Solutions:**

1. **Verify volume mount:**
   ```bash
   docker volume inspect ehr-platform-macos_model_cache
   ```

2. **Check volume in docker-compose.yml:**
   ```yaml
   volumes:
     - model_cache:/root/.cache/torch
   ```

3. **Manually create volume:**
   ```bash
   docker volume create model_cache
   docker-compose up -d
   ```

## Container Issues

### Issue: Container keeps restarting

**Solutions:**

1. **Check logs:**
   ```bash
   docker-compose logs -f app
   ```

2. **Check health:**
   ```bash
   docker inspect ehr-app | grep Health -A 10
   ```

3. **Disable health check temporarily:**
   Edit `docker-compose.yml`:
   ```yaml
   services:
     app:
       # Comment out healthcheck
       # healthcheck:
       #   test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
   ```

4. **Check resource limits:**
   ```bash
   docker stats
   ```

### Issue: "Container exited with code 137"

**Cause:** Out of memory

**Solutions:**
1. Increase Docker memory allocation
2. Check for memory leaks in logs
3. Restart Docker Desktop

### Issue: "Container exited with code 1"

**Cause:** Application error

**Solutions:**

1. **Check application logs:**
   ```bash
   docker-compose logs app | tail -100
   ```

2. **Check for missing dependencies:**
   ```bash
   docker-compose build --no-cache
   ```

3. **Verify environment variables:**
   ```bash
   docker-compose config
   ```

4. **Run container interactively:**
   ```bash
   docker-compose run --rm app bash
   # Then manually run the application
   ```

## Apple Silicon Specific

### Issue: "exec format error" on Apple Silicon

**Cause:** Trying to run x86 image without Rosetta

**Solutions:**

1. **Enable Rosetta in Docker:**
   - Docker Desktop > Settings > General
   - ✅ Use Rosetta for x86/amd64 emulation on Apple Silicon

2. **Rebuild for ARM64:**
   ```bash
   docker-compose build --build-arg BUILDPLATFORM=linux/arm64
   ```

3. **Use multi-platform build:**
   ```bash
   docker buildx create --use
   docker buildx build --platform linux/arm64 -t ehr-app .
   ```

### Issue: Slow performance on Apple Silicon

**Solutions:**

1. **Verify native ARM image:**
   ```bash
   docker inspect ehr-app | grep Architecture
   # Should show "arm64"
   ```

2. **Disable Rosetta if using ARM images:**
   - Only needed for x86 images

3. **Check if emulation is being used:**
   ```bash
   docker-compose logs app | grep -i rosetta
   ```

### Issue: Build fails on M1/M2/M3

**Solutions:**

1. **Update Docker Desktop:**
   - Should be version 4.0 or later

2. **Use buildx:**
   ```bash
   docker buildx build --platform linux/arm64 .
   ```

3. **Check Xcode Command Line Tools:**
   ```bash
   xcode-select --install
   ```

## Common Error Messages

### "ERROR: Couldn't connect to Docker daemon"

**Solution:**
```bash
open -a Docker
# Wait for Docker to start
```

### "ERROR: Version in './docker-compose.yml' is unsupported"

**Solution:**
Update Docker Desktop to latest version

### "ERROR: for app Cannot start service app: driver failed programming external connectivity"

**Solution:**
```bash
# Restart Docker
killall Docker
open -a Docker

# Or restart Mac
sudo reboot
```

### "ERRO[0000] error waiting for container: context canceled"

**Solution:**
```bash
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
Rebuild Docker image (curl should be included):
```bash
docker-compose build --no-cache
docker-compose up -d
```

## Getting Help

If none of these solutions work:

1. **Collect diagnostic information:**
   ```bash
   # System info
   system_profiler SPSoftwareDataType > system-info.txt
   
   # Docker info
   docker info > docker-info.txt
   docker-compose ps > containers.txt
   docker-compose logs > logs.txt
   
   # Network info
   ifconfig > network-info.txt
   ```

2. **Check logs:**
   ```bash
   ./logs.sh > full-logs.txt
   ```

3. **Check status:**
   ```bash
   ./status.sh
   ```

4. **Docker Desktop diagnostics:**
   - Click Docker icon > Troubleshoot > Get Support
   - This creates a diagnostic bundle

5. **Community support:**
   - Docker forums: https://forums.docker.com
   - Stack Overflow: Tag with `docker` and `macos`
   - GitHub Issues (if applicable)

## Prevention Tips

1. **Regular updates:**
   ```bash
   docker-compose pull
   docker-compose up -d --build
   ```

2. **Regular cleanup:**
   ```bash
   docker system prune -a --volumes
   ```
   ⚠️ This removes all unused data!

3. **Monitor resources:**
   ```bash
   docker stats
   ```

4. **Regular backups:**
   - Run backup script weekly
   - Test restore procedure

5. **Keep logs:**
   ```bash
   docker-compose logs > logs-$(date +%Y-%m-%d).txt
   ```

6. **Update macOS:**
   ```bash
   softwareupdate -l
   sudo softwareupdate -i -a
   ```

