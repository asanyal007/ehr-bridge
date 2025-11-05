@echo off
echo Building Windows Deployment Package...
echo.

REM Create package directory
set PACKAGE_NAME=ehr-platform-windows
set PACKAGE_DIR=%PACKAGE_NAME%

if exist %PACKAGE_DIR% rmdir /s /q %PACKAGE_DIR%
mkdir %PACKAGE_DIR%

REM Copy essential files
echo Copying application files...
xcopy /E /I /Y backend %PACKAGE_DIR%\backend
xcopy /E /I /Y frontend %PACKAGE_DIR%\frontend
xcopy /E /I /Y data\omop_vocab_seed %PACKAGE_DIR%\data\omop_vocab_seed

REM Copy configuration files
copy Dockerfile %PACKAGE_DIR%\
copy docker-compose.yml %PACKAGE_DIR%\
copy .dockerignore %PACKAGE_DIR%\
copy requirements.txt %PACKAGE_DIR%\

REM Copy sample data
copy sample_data_*.csv %PACKAGE_DIR%\
copy test_ehr_data.csv %PACKAGE_DIR%\

REM Copy scripts
copy start.bat %PACKAGE_DIR%\
copy start.ps1 %PACKAGE_DIR%\
copy stop.bat %PACKAGE_DIR%\
copy logs.bat %PACKAGE_DIR%\
copy status.bat %PACKAGE_DIR%\

REM Copy documentation
copy README.md %PACKAGE_DIR%\
copy DEPLOYMENT_PACKAGE.md %PACKAGE_DIR%\
copy WINDOWS_SETUP_GUIDE.md %PACKAGE_DIR%\
copy TROUBLESHOOTING.md %PACKAGE_DIR%\

REM Create .env template
(
    echo # EHR Platform Environment Configuration
    echo.
    echo # JWT Secret Key for authentication
    echo JWT_SECRET_KEY=change-this-to-a-secure-random-string
    echo.
    echo # Google Gemini API Key for AI features
    echo GEMINI_API_KEY=your-gemini-api-key-here
    echo.
    echo # MongoDB Configuration
    echo MONGO_HOST=mongodb
    echo MONGO_PORT=27017
    echo MONGO_DB=ehr
) > %PACKAGE_DIR%\.env.template

REM Create README
(
    echo # EHR AI Data Interoperability Platform
    echo.
    echo ## Quick Start
    echo.
    echo 1. Install Docker Desktop
    echo 2. Double-click start.bat
    echo 3. Configure your Gemini API key when prompted
    echo 4. Wait for the application to start
    echo 5. Access at http://localhost:8000
    echo.
    echo See DEPLOYMENT_PACKAGE.md for detailed instructions.
) > %PACKAGE_DIR%\README.txt

REM Create ZIP package
echo Creating ZIP archive...
powershell Compress-Archive -Path %PACKAGE_DIR% -DestinationPath %PACKAGE_NAME%.zip -Force

echo.
echo ✅ Package created: %PACKAGE_NAME%.zip
echo.
echo Package size:
dir %PACKAGE_NAME%.zip | find ".zip"
echo.
pause

