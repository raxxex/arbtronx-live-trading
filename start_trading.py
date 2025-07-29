#!/usr/bin/env python3
"""
ARBTRONX Live Trading Dashboard Startup Script
Simple script to start the live trading dashboard
"""

import subprocess
import sys
import os

def main():
    print("🚀 ARBTRONX Live Trading Dashboard")
    print("=" * 50)
    print("📱 Mobile-responsive interface")
    print("💰 Live trading with real funds")
    print("🔗 Binance API integration")
    print("🎯 4-Month roadmap: $200 → $100,000")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  No .env file found!")
        print("📝 Please create a .env file with your Binance API keys:")
        print("   BINANCE_API_KEY=your_api_key_here")
        print("   BINANCE_SECRET_KEY=your_secret_key_here")
        print("   USER_NAME=Your Name")
        print("   USER_EMAIL=your@email.com")
        print("   USER_ID=your_user_id")
        print("")
        print("🔑 You can also add API keys through the web interface")
        print("")
    
    print("🌐 Starting dashboard at: http://localhost:8006")
    print("📊 Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        # Start the live dashboard
        subprocess.run([sys.executable, "live_dashboard.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
