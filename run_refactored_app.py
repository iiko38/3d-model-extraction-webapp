#!/usr/bin/env python3
"""
Launcher for the refactored 3D Warehouse application
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def main():
    """Launch the refactored application."""
    try:
        from app.main_refactored import app
        import uvicorn
        
        print("🚀 Starting Refactored 3D Warehouse...")
        print("📍 URL: http://127.0.0.1:8000")
        print("📊 API Docs: http://127.0.0.1:8000/docs")
        print("🔍 Health Check: http://127.0.0.1:8000/health")
        print("\n✨ Features:")
        print("   • Filterable grid with FTS5 search")
        print("   • Inline editing for file metadata")
        print("   • Bulk actions and pattern renaming")
        print("   • URL health monitoring")
        print("   • Product bundle downloads")
        print("   • Enhanced statistics dashboard")
        print("\nPress Ctrl+C to stop the server")
        
        uvicorn.run(
            "app.main_refactored:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you have installed the required dependencies:")
        print("   pip install fastapi uvicorn jinja2 requests")
        return 1
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
