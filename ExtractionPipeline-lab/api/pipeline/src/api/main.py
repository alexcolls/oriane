#!/usr/bin/env python3
"""
Main entry point for the Pipeline API
"""

# Import the app for convenience
from src.api.app import app

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
