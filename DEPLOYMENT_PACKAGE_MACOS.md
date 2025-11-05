# EHR AI Data Interoperability Platform - macOS Deployment Package

## Package Contents

```
ehr-platform-macos/
├── start.sh                     # One-click startup script
├── stop.sh                      # Stop all services
├── logs.sh                      # View application logs
├── status.sh                    # Check system status
├── docker-compose.yml           # Docker orchestration
├── Dockerfile                   # Application container definition
├── .dockerignore                # Docker build optimization
├── requirements.txt             # Python dependencies
├── env.template                 # Environment configuration template
├── MACOS_SETUP_GUIDE.md         # Detailed setup instructions
├── TROUBLESHOOTING_MACOS.md     # Common issues and solutions
├── backend/                     # Backend Python code
├── frontend/                    # Frontend React code
├── data/                        # SQLite databases (created on first run)
│   └── omop_vocab_seed/         # OMOP vocabulary seed data
├── sample_data_*.csv            # Sample EHR data files
└── README.md                    # Quick start guide
```

## System Requirements

### Minimum Requirements
- **OS**: macOS 11 (Big Sur) or later
- **RAM**: 8 GB
- **Disk**: 20 GB free space
- **CPU**: Intel or Apple Silicon (M1/M2/M3)

### Recommended Requirements
- **OS**: macOS 13 (Ventura) or later
- **RAM**: 16 GB
- **Disk**: 50 GB SSD
- **CPU**: Apple Silicon (M1/M2/M3) or Intel i7/i9
- **Internet**: Broadband connection (for AI model downloads)

### Software Prerequisites
- **Docker Desktop for Mac**: Version 4.0 or higher
  - Download: https://www.docker.com/products/docker-desktop
  - Supports both Intel and Apple Silicon
- **Google Gemini API Key**: For AI features
  - Get free key: https://makersuite.google.com/app/apikey

## Quick Start (3 Steps)

### Step 1: Install Docker Desktop for Mac
1. Download Docker Desktop from https://www.docker.com/products/docker-desktop
2. Choose the correct version:
   - **Apple Silicon**: Docker Desktop for Mac (Apple Chip)
   - **Intel**: Docker Desktop for Mac (Intel Chip)
3. Open the downloaded `.dmg` file
4. Drag Docker to Applications folder
5. Open Docker from Applications
6. Grant necessary permissions when prompted
7. Wait for "Docker Desktop is running" notification

### Step 2: Extract and Navigate
1. Extract the ZIP file (double-click or use `unzip`)
2. Open Terminal (Applications > Utilities > Terminal)
3. Navigate to extracted folder:
   ```bash
   cd ~/Downloads/ehr-platform-macos
   ```

### Step 3: Launch Application
1. Run the startup script:
   ```bash
   ./start.sh
   ```
2. When prompted, enter your Gemini API key
3. Wait 3-5 minutes for first-time setup (downloads Docker images and AI models)
4. Browser will open automatically to http://localhost:8000

That's it! The platform is now running.

## Management Commands

All commands should be run from the package directory in Terminal:

- **Start**: `./start.sh`
- **Stop**: `./stop.sh`
- **View Logs**: `./logs.sh`
- **Check Status**: `./status.sh`

## Accessing the Application

- **Main URL**: http://localhost:8000
- **Alternative**: http://localhost:3000
- **MongoDB**: mongodb://localhost:27017

## Default Credentials

- **Username**: `admin`
- **Password**: `admin123`

⚠️ Change these in production!

## Data Persistence

All data is persisted in:
- `./data/` - SQLite databases
- `./backend/data/` - Additional databases
- Docker volumes - MongoDB data

Your data will survive container restarts.

## Apple Silicon (M1/M2/M3) Notes

Docker Desktop automatically handles architecture differences. The platform works seamlessly on Apple Silicon with:
- Native ARM64 performance
- Rosetta 2 emulation when needed
- No additional configuration required

## Troubleshooting

### Docker Desktop not starting
- Check System Preferences > Security & Privacy for blocked apps
- Grant necessary permissions (Full Disk Access, Network)
- Restart your Mac

### Port already in use
- Change ports in `docker-compose.yml`:
  ```yaml
  ports:
    - "8001:8000"  # Change 8000 to 8001
  ```

### Permission denied when running scripts
- Make scripts executable:
  ```bash
  chmod +x start.sh stop.sh logs.sh status.sh
  ```

### Out of memory
- Increase Docker memory limit:
  - Docker Desktop > Preferences > Resources
  - Increase Memory slider

### Slow performance
- Allocate more CPUs in Docker Desktop Preferences > Resources
- Ensure Docker is using Apple Silicon native mode (not Rosetta)
- Use SSD for Docker data directory

For more help, see `TROUBLESHOOTING_MACOS.md`

## Updating the Application

1. Stop the platform:
   ```bash
   ./stop.sh
   ```
2. Replace files with new version
3. Start again:
   ```bash
   ./start.sh
   ```

Docker will rebuild with new code.

## Uninstalling

1. Stop the platform:
   ```bash
   ./stop.sh
   ```
2. Remove containers and volumes:
   ```bash
   docker-compose down -v
   ```
3. Delete the application folder:
   ```bash
   cd ..
   rm -rf ehr-platform-macos
   ```
4. (Optional) Uninstall Docker Desktop:
   - Drag Docker from Applications to Trash
   - Remove Docker data: `rm -rf ~/Library/Group\ Containers/group.com.docker`

## Keyboard Shortcuts

- **Stop logs**: `Ctrl+C` (when viewing logs)
- **Exit script**: `Ctrl+C` or Enter when prompted
- **Force quit**: `Ctrl+Z` (not recommended)

## Terminal Tips

### Navigate to package directory
```bash
cd ~/Downloads/ehr-platform-macos
```

### Check if Docker is running
```bash
docker ps
```

### View all containers
```bash
docker-compose ps
```

### Restart specific service
```bash
docker-compose restart app
docker-compose restart mongodb
```

### View logs for specific service
```bash
docker-compose logs -f app
docker-compose logs -f mongodb
```

### Clean up Docker resources
```bash
docker system prune -a
```

## Environment Variables

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

To edit `.env`:
```bash
nano .env
# or
vim .env
# or
open -e .env  # Opens in TextEdit
```

## Security Best Practices

1. **Change default credentials** immediately after first login
2. **Generate secure JWT secret**:
   ```bash
   openssl rand -base64 32
   ```
3. **Protect API keys**: Never commit `.env` to version control
4. **Use firewall**: Enable macOS firewall in System Preferences
5. **Regular updates**: Keep Docker Desktop and the application updated

## Performance Optimization

### For Apple Silicon (M1/M2/M3)
- Docker Desktop runs natively - no additional optimization needed
- Ensure "Use Rosetta for x86/amd64 emulation" is enabled in Docker settings

### For Intel Macs
- Allocate at least 4 CPUs and 8 GB RAM in Docker Desktop
- Close unnecessary applications to free resources

### General Tips
- Use SSD for Docker data
- Enable "Use gRPC FUSE for file sharing" in Docker Desktop
- Disable unnecessary Docker features in Preferences

## Backup Procedures

### Quick Backup
```bash
# Stop the platform
./stop.sh

# Backup data
tar -czf ehr-backup-$(date +%Y%m%d).tar.gz data backend/data

# Restart
./start.sh
```

### Full Backup (including MongoDB)
```bash
# Backup SQLite databases
tar -czf sqlite-backup-$(date +%Y%m%d).tar.gz data backend/data

# Backup MongoDB
docker exec ehr-mongodb mongodump --out=/data/backup
docker cp ehr-mongodb:/data/backup ./mongodb-backup-$(date +%Y%m%d)
tar -czf mongodb-backup-$(date +%Y%m%d).tar.gz mongodb-backup-$(date +%Y%m%d)
rm -rf mongodb-backup-$(date +%Y%m%d)
```

### Restore from Backup
```bash
# Stop platform
./stop.sh

# Restore SQLite
tar -xzf sqlite-backup-YYYYMMDD.tar.gz

# Restore MongoDB
docker-compose up -d mongodb
tar -xzf mongodb-backup-YYYYMMDD.tar.gz
docker cp mongodb-backup-YYYYMMDD ehr-mongodb:/data/backup
docker exec ehr-mongodb mongorestore /data/backup

# Start platform
./start.sh
```

## Monitoring

### Check container health
```bash
docker inspect --format='{{.State.Health.Status}}' ehr-app
docker inspect --format='{{.State.Health.Status}}' ehr-mongodb
```

### Monitor resource usage
```bash
docker stats
```

### View container logs
```bash
# Real-time logs
./logs.sh

# Last 100 lines
docker-compose logs --tail=100

# Logs since specific time
docker-compose logs --since=1h
```

## Advanced Configuration

### Custom Port Configuration
Edit `docker-compose.yml`:
```yaml
services:
  app:
    ports:
      - "8080:8000"  # Change external port to 8080
```

### Resource Limits
Edit `docker-compose.yml`:
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '4'      # Increase CPU limit
          memory: 8G     # Increase memory limit
```

### Network Configuration
```yaml
networks:
  ehr-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16
```

## Support

- **Documentation**: See `MACOS_SETUP_GUIDE.md`
- **Issues**: Check `TROUBLESHOOTING_MACOS.md`
- **Logs**: Run `./logs.sh` to see detailed logs
- **Community**: Docker forums, Stack Overflow

## Differences from Windows Package

- Uses shell scripts (`.sh`) instead of batch files (`.bat`)
- Native Terminal instead of Command Prompt/PowerShell
- Different Docker Desktop installation process
- Apple Silicon support with native ARM64 performance
- Unix-style file permissions and paths
- Different keyboard shortcuts (Ctrl vs Cmd)

## Next Steps

1. Change default admin password
2. Configure production API keys
3. Set up automated backups
4. Configure monitoring and alerts
5. Review security settings
6. Load production data
7. Set up SSL/TLS for production

