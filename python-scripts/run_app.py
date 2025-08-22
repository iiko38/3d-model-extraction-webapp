#!/usr/bin/env python3
"""
Launcher script for the 3D Model Library web app.
"""

import uvicorn

if __name__ == "__main__":
    print("Starting 3D Model Library web app...")
    print("Open your browser to: http://127.0.0.1:8000")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
