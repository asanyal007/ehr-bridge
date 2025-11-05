# EHR AI Data Interoperability Platform - Windows Setup Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Docker Desktop Installation](#docker-desktop-installation)
3. [WSL 2 Setup](#wsl-2-setup)
4. [Application Deployment](#application-deployment)
5. [Configuration](#configuration)
6. [Network Configuration](#network-configuration)
7. [Performance Tuning](#performance-tuning)
8. [Backup Procedures](#backup-procedures)
9. [Security Best Practices](#security-best-practices)

## Prerequisites

### System Requirements Check

Before starting, verify your system meets these requirements:

**Windows Version:**
```powershell
# Run in PowerShell
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsHardwareAbstractionLayer
```

**RAM:**
```powershell
Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property capacity -Sum | ForEach-Object {"{0:N2} GB" -f ($_.sum / 1GB)}
```

**CPU Cores:**
```powershell
Get-WmiObject -Class Win32_Processor | Select-Object NumberOfCores, NumberOfLogicalProcessors
```

**Disk Space:**
```powershell
Get-PSDrive C | Select-Object Used,Free
```

### Required Software
- Windows 10 64-bit: Pro, Enterprise, or Education (Build 19041 or higher)
- Windows 11 64-bit: Any edition
- Virtualization enabled in BIOS

## Docker Desktop Installation

### Step 1: Enable Virtualization

1. **Check if virtualization is enabled:**
   ```powershell
   # Run as Administrator
   Get-ComputerInfo | Select-Object HyperVisorPresent, HyperVRequirementVirtualizationFirmwareEnabled
   ```

2. **If disabled, enable in BIOS:**
   - Restart computer
   - Enter BIOS (usually F2, F10, Del, or Esc during boot)
   - Find "Virtualization Technology" or "Intel VT-x" or "AMD-V"
   - Enable it
   - Save and exit

### Step 2: Install WSL 2

1. **Open PowerShell as Administrator**

2. **Install WSL 2:**
   ```powershell
   wsl --install
   ```

3. **Restart your computer**

4. **Verify WSL 2 installation:**
   ```powershell
   wsl --list --verbose
   ```

### Step 3: Download and Install Docker Desktop

1. **Download Docker Desktop:**
   - Visit: https://www.docker.com/products/docker-desktop
   - Click "Download for Windows"

2. **Run the installer:**
   - Double-click `Docker Desktop Installer.exe`
   - Ensure "Use WSL 2 instead of Hyper-V" is checked
   - Follow the installation wizard

3. **Restart your computer** when prompted

4. **Start Docker Desktop:**
   - Find Docker Desktop in Start Menu
   - Wait for "Docker Desktop is running" notification

5. **Verify installation:**
   ```powershell
   docker --version
   docker-compose --version
   ```

### Step 4: Configure Docker Desktop

1. **Open Docker Desktop Settings** (gear icon)

2. **Resources > Advanced:**
   - **CPUs**: Allocate at least 2 (recommended: 4)
   - **Memory**: Allocate at least 4 GB (recommended: 8 GB)
   - **Swap**: 1 GB
   - **Disk image size**: 60 GB

3. **General:**
   - ✅ Use WSL 2 based engine
   - ✅ Start Docker Desktop when you log in

4. **Click "Apply & Restart"**

## WSL 2 Setup

### Verify WSL 2 Configuration

```powershell
# Check WSL version
wsl --list --verbose

# Should show:
#   NAME                   STATE           VERSION
# * Ubuntu                 Running         2
```

### Set WSL 2 as Default

```powershell
wsl --set-default-version 2
```

### Update WSL Kernel

```powershell
wsl --update
```

## Application Deployment

### Step 1: Extract Package

1. **Extract the ZIP file:**
   - Right-click `ehr-platform-windows.zip`
   - Select "Extract All..."
   - Choose destination folder (e.g., `C:\EHR-Platform`)

2. **Navigate to extracted folder:**
   ```powershell
   cd C:\EHR-Platform\ehr-platform-windows
   ```

### Step 2: Get Gemini API Key

1. **Visit:** https://makersuite.google.com/app/apikey
2. **Sign in** with Google account
3. **Click "Create API Key"**
4. **Copy the API key** (keep it secure!)

### Step 3: Run Startup Script

**Option A: Using Command Prompt (Recommended)**
1. Double-click `start.bat`
2. When Notepad opens, paste your Gemini API key
3. Save and close Notepad
4. Wait for deployment to complete

**Option B: Using PowerShell**
1. Right-click `start.ps1`
2. Select "Run with PowerShell"
3. If you get an execution policy error:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
4. Run `start.ps1` again

### Step 4: Verify Deployment

1. **Check container status:**
   ```powershell
   docker-compose ps
   ```

2. **Expected output:**
   ```
   NAME          IMAGE                    STATUS         PORTS
   ehr-app       ehr-platform-windows_app Up (healthy)   0.0.0.0:8000->8000/tcp
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
# JWT Secret Key (change for production!)
JWT_SECRET_KEY=your-secure-random-string-here

# Google Gemini API Key
GEMINI_API_KEY=your-actual-api-key

# MongoDB Configuration
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DB=ehr
```

### Port Configuration

If ports 8000 or 27017 are already in use:

1. **Edit `docker-compose.yml`:**
   ```yaml
   services:
     app:
       ports:
         - "8001:8000"  # Change external port
     mongodb:
       ports:
         - "27018:27017"  # Change external port
   ```

2. **Restart:**
   ```powershell
   docker-compose down
   docker-compose up -d
   ```

## Network Configuration

### Firewall Rules

Docker Desktop automatically configures Windows Firewall. If you have issues:

1. **Open Windows Defender Firewall**
2. **Allow Docker Desktop:**
   - Advanced settings > Inbound Rules
   - New Rule > Program
   - Browse to: `C:\Program Files\Docker\Docker\Docker Desktop.exe`
   - Allow the connection

### Access from Other Machines

To access from other computers on your network:

1. **Find your IP address:**
   ```powershell
   ipconfig | findstr IPv4
   ```

2. **Add firewall rule:**
   ```powershell
   # Run as Administrator
   New-NetFirewallRule -DisplayName "EHR Platform" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
   ```

3. **Access from other machines:**
   - http://YOUR-IP-ADDRESS:8000

## Performance Tuning

### Optimize Docker Resources

1. **Increase memory allocation:**
   - Docker Desktop > Settings > Resources
   - Memory: 8-16 GB (depending on available RAM)

2. **Increase CPU allocation:**
   - CPUs: 4-8 cores (depending on available cores)

3. **Use SSD for Docker data:**
   - Docker Desktop > Settings > Resources > Advanced
   - Change disk image location to SSD

### Optimize WSL 2 Performance

Create `.wslconfig` in your home directory (`C:\Users\YourUsername\.wslconfig`):

```ini
[wsl2]
memory=8GB
processors=4
swap=2GB
localhostForwarding=true
```

Restart WSL:
```powershell
wsl --shutdown
```

### Database Optimization

**SQLite:**
- Databases are stored in `./data` and `./backend/data`
- Ensure these directories are on SSD

**MongoDB:**
- Data persists in Docker volume
- To move to different drive:
  ```yaml
  volumes:
    mongodb_data:
      driver: local
      driver_opts:
        type: none
        o: bind
        device: D:\docker-data\mongodb
  ```

## Backup Procedures

### Automated Backup Script

Create `backup.bat`:

```batch
@echo off
set BACKUP_DIR=C:\EHR-Backups\%date:~-4,4%%date:~-10,2%%date:~-7,2%

echo Creating backup directory...
mkdir "%BACKUP_DIR%"

echo Backing up SQLite databases...
xcopy /E /I /Y data "%BACKUP_DIR%\data"
xcopy /E /I /Y backend\data "%BACKUP_DIR%\backend-data"

echo Exporting MongoDB data...
docker exec ehr-mongodb mongodump --out=/data/backup
docker cp ehr-mongodb:/data/backup "%BACKUP_DIR%\mongodb"

echo Backup complete: %BACKUP_DIR%
pause
```

### Manual Backup

1. **Stop the platform:**
   ```powershell
   docker-compose down
   ```

2. **Copy data directories:**
   ```powershell
   xcopy /E /I data C:\Backups\ehr-data
   xcopy /E /I backend\data C:\Backups\ehr-backend-data
   ```

3. **Export MongoDB:**
   ```powershell
   docker-compose up -d mongodb
   docker exec ehr-mongodb mongodump --out=/data/backup
   docker cp ehr-mongodb:/data/backup C:\Backups\mongodb
   ```

4. **Restart platform:**
   ```powershell
   docker-compose up -d
   ```

### Restore from Backup

1. **Stop the platform:**
   ```powershell
   docker-compose down -v
   ```

2. **Restore data directories:**
   ```powershell
   xcopy /E /I C:\Backups\ehr-data data
   xcopy /E /I C:\Backups\ehr-backend-data backend\data
   ```

3. **Start MongoDB:**
   ```powershell
   docker-compose up -d mongodb
   ```

4. **Restore MongoDB:**
   ```powershell
   docker cp C:\Backups\mongodb ehr-mongodb:/data/backup
   docker exec ehr-mongodb mongorestore /data/backup
   ```

5. **Start full platform:**
   ```powershell
   docker-compose up -d
   ```

## Security Best Practices

### 1. Change Default Credentials

After first login:
- Navigate to Settings > Users
- Change admin password
- Create individual user accounts

### 2. Secure JWT Secret

Generate a strong JWT secret:
```powershell
# Generate random string
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})
```

Update in `.env`:
```bash
JWT_SECRET_KEY=your-generated-secure-string
```

### 3. Secure API Keys

- Never commit `.env` to version control
- Rotate API keys regularly
- Use environment-specific keys

### 4. Network Security

For production:
- Use HTTPS (add reverse proxy like nginx)
- Restrict MongoDB access to localhost only
- Use VPN for remote access

### 5. Update Regularly

```powershell
# Pull latest Docker images
docker-compose pull

# Rebuild and restart
docker-compose up -d --build
```

## Monitoring and Maintenance

### View Logs

```powershell
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f mongodb
```

### Check Health

```powershell
# Container health
docker inspect --format='{{.State.Health.Status}}' ehr-app

# Resource usage
docker stats
```

### Cleanup

```powershell
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes (careful!)
docker volume prune
```

## Troubleshooting

See `TROUBLESHOOTING.md` for detailed troubleshooting steps.

## Support

- **Documentation**: Check all `.md` files in package
- **Logs**: Run `logs.bat` for detailed logs
- **Status**: Run `status.bat` for system status
- **Community**: GitHub Issues (if applicable)

