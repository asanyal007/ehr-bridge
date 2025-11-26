#!/usr/bin/env python3
"""
Convenience script to run the FastAPI backend server
"""
import os
import sys
import uvicorn

if __name__ == "__main__":
    # No external dependencies needed - using SQLite and JWT
    
    print("[START] Starting AI Data Interoperability Platform Backend...")
    print("[INFO] API will be available at: http://localhost:8000")
    print("[INFO] API Documentation at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop\n")
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

