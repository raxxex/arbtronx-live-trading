#!/usr/bin/env python3
"""
ARBTRONX Live Trading Dashboard - Alternative Entry Point
"""

# Import the main app from live_dashboard
from live_dashboard import app

# This file serves as an alternative entry point for deployment platforms
# that prefer app.py over live_dashboard.py

if __name__ == "__main__":
    import os
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    print("🚀 Starting ARBTRONX via app.py entry point...")
    uvicorn.run(app, host="0.0.0.0", port=port)
