#!/usr/bin/env python3
"""
Convenience script to run the FastAPI backend server
"""
import os
import sys
import uvicorn

if __name__ == "__main__":
    # Configure UTF-8 encoding for Windows console
    if sys.platform == "win32":
        import codecs
        # Set environment variable for Python I/O encoding
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        # Reconfigure stdout and stderr
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'ignore')
    
    # No external dependencies needed - using SQLite and JWT
    
    print("[STARTUP] Starting AI Data Interoperability Platform Backend...")
    print("[API] API will be available at: http://localhost:8000")
    print("[DOCS] API Documentation at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop\n")
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=False,  # Disabled for clean startup
        log_level="info"
    )

