#!/usr/bin/env python3
"""
Simple test application for KinD validation
"""

from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "pipeline-api"}

@app.get("/")
async def root():
    return {"message": "Pipeline API is running"}

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False
    )
