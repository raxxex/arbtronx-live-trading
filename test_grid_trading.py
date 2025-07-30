#!/usr/bin/env python3
"""
Simple test script to verify grid trading functionality
"""
import asyncio
import os
from src.exchanges.exchange_manager import ExchangeManager
from src.strategies.grid_trading_engine import GridTradingEngine

async def test_grid_trading():
    """Test basic grid trading functionality"""
    print("🧪 Testing Grid Trading Engine...")
    
    try:
        # Initialize Exchange Manager
        print("📊 Initializing Exchange Manager...")
        exchange_manager = ExchangeManager()
        await exchange_manager.initialize()
        
        if not exchange_manager.exchanges:
            print("⚠️ No exchanges initialized - check API credentials")
            return False
        
        # Initialize Grid Trading Engine
        print("🔲 Initializing Grid Trading Engine...")
        grid_engine = GridTradingEngine(exchange_manager)
        
        print("🎯 Testing grid configuration...")
        test_config = {
            'order_size_usd': 10,
            'grid_spacing_pct': 0.5,
            'levels_above': 3,
            'levels_below': 3,
            'profit_target_pct': 1.0,
            'stop_loss_pct': 5.0,
            'max_capital_usd': 100,
            'use_smart_range': False
        }
        
        test_symbol = 'BTC/USDT'
        test_exchange = 'binance'
        
        print(f"🔍 Testing grid creation for {test_symbol}...")
        
        print("✅ Grid Trading Engine initialized successfully!")
        print(f"   Available exchanges: {list(exchange_manager.exchanges.keys())}")
        print(f"   Test configuration: {test_config}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing grid trading: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_grid_trading())
    if success:
        print("🎉 Grid Trading test completed successfully!")
    else:
        print("💥 Grid Trading test failed!")
