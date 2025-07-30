#!/usr/bin/env python3
"""
Simple test to verify dashboard imports work correctly
"""
import sys
import os

def test_dashboard_imports():
    """Test that dashboard can be imported without errors"""
    print("🧪 Testing Dashboard Imports...")
    
    try:
        print("📊 Testing FastAPI import...")
        from fastapi import FastAPI
        
        print("🔧 Testing dashboard import...")
        import live_dashboard
        
        print("✅ Dashboard imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Error importing dashboard: {e}")
        return False

if __name__ == "__main__":
    success = test_dashboard_imports()
    if success:
        print("🎉 Dashboard test completed successfully!")
    else:
        print("💥 Dashboard test failed!")
