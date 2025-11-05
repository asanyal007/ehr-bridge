# EHR AI Data Interoperability Platform - Deployment Package

## Package Contents

```
ehr-platform-windows/
├── start.bat                    # One-click startup (Windows CMD)
├── start.ps1                    # One-click startup (PowerShell)
├── stop.bat                     # Stop all services
├── logs.bat                     # View application logs
├── status.bat                   # Check system status
├── docker-compose.yml           # Docker orchestration
├── Dockerfile                   # Application container definition
├── .dockerignore                # Docker build optimization
├── requirements.txt             # Python dependencies
├── .env.template                # Environment configuration template
├── WINDOWS_SETUP_GUIDE.md       # Detailed setup instructions
├── TROUBLESHOOTING.md           # Common issues and solutions
├── backend/                     # Backend Python code
├── frontend/                    # Frontend React code
├── data/                        # SQLite databases (created on first run)
│   └── omop_vocab_seed/         # OMOP vocabulary seed data
├── sample_data_*.csv            # Sample EHR data files
└── README.md                    # Quick start guide
```

## System Requirements

### Minimum Requirements
- **OS**: Windows 10 (64-bit) or Windows 11
- **RAM**: 8 GB
- **Disk**: 20 GB free space
- **CPU**: 4 cores

### Recommended Requirements
- **OS**: Windows 11
- **RAM**: 16 GB
- **Disk**: 50 GB SSD
- **CPU**: 8 cores
- **Internet**: Broadband connection (for AI model downloads)

### Software Prerequisites
- **Docker Desktop**: Version 4.0 or higher
  - Download: https://www.docker.com/products/docker-desktop
  - Requires WSL 2 backend on Windows
- **Google Gemini API Key**: For AI features
  - Get free key: https://makersuite.google.com/app/apikey

## Quick Start (3 Steps)

### Step 1: Install Docker Desktop
1. Download Docker Desktop from https://www.docker.com/products/docker-desktop
2. Run the installer
3. Restart your computer
4. Start Docker Desktop
5. Wait for "Docker Desktop is running" notification

### Step 2: Configure API Key
1. Double-click `start.bat`
2. When Notepad opens with `.env` file, replace `your-gemini-api-key-here` with your actual Gemini API key
3. Save and close Notepad

### Step 3: Launch Application
1. The startup script will automatically continue
2. Wait 3-5 minutes for first-time setup (downloads Docker images and AI models)
3. Browser will open automatically to http://localhost:8000

That's it! The platform is now running.

## Management Commands

- **Start**: Double-click `start.bat`
- **Stop**: Double-click `stop.bat`
- **View Logs**: Double-click `logs.bat`
- **Check Status**: Double-click `status.bat`

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

## Troubleshooting

### Docker Desktop not starting
- Enable WSL 2: `wsl --install` in PowerShell (Admin)
- Enable virtualization in BIOS

### Port already in use
- Change ports in `docker-compose.yml`:
  ```yaml
  ports:
    - "8001:8000"  # Change 8000 to 8001
  ```

### Out of memory
- Increase Docker memory limit in Docker Desktop Settings > Resources

### Slow performance
- Allocate more CPUs in Docker Desktop Settings > Resources
- Use SSD for Docker data directory

For more help, see `TROUBLESHOOTING.md`

## Updating the Application

1. Stop the platform: `stop.bat`
2. Replace files with new version
3. Start again: `start.bat`

Docker will rebuild with new code.

## Uninstalling

1. Stop the platform: `stop.bat`
2. Remove containers and volumes:
   ```
   docker-compose down -v
   ```
3. Delete the application folder
4. (Optional) Uninstall Docker Desktop

## Support

- Documentation: See `WINDOWS_SETUP_GUIDE.md`
- Issues: Check `TROUBLESHOOTING.md`
- Logs: Run `logs.bat` to see detailed logs

