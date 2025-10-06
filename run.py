#!/usr/bin/env python3
"""
Run script for the WebRTC Signaling Server
"""

import uvicorn
from src.utils.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    
    print(f"Starting WebRTC Signaling Server...")
    print(f"Host: {settings.host}")
    print(f"Port: {settings.port}")
    print(f"Debug: {settings.debug}")
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
