#!/usr/bin/env python3
"""
Main entry point for the Oriane Pipeline API Docker container.
This file serves as the entry point that imports and runs the actual application.
"""

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
