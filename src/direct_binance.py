#!/usr/bin/env python3
"""
Direct Binance API connection for real data
Bypasses complex exchange manager for simple data fetching
"""

import asyncio
import aiohttp
import hmac
import hashlib
import time
from urllib.parse import urlencode
from typing import Dict, Any, Optional
import json

class DirectBinanceAPI:
    """Direct Binance API client for real data fetching"""
    
    def __init__(self, api_key: str, secret_key: str, testnet: bool = False):
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        
        if testnet:
            self.base_url = "https://testnet.binance.vision"
        else:
            self.base_url = "https://api.binance.com"
    
    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    async def _make_request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Optional[Dict]:
        """Make HTTP request to Binance API"""
        if params is None:
            params = {}
        
        headers = {
            'X-MBX-APIKEY': self.api_key
        }
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            query_string = urlencode(params)
            params['signature'] = self._generate_signature(query_string)
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                if method.upper() == 'GET':
                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            print(f"Binance API Error {response.status}: {error_text}")
                            return None
                elif method.upper() == 'POST':
                    async with session.post(url, data=params, headers=headers) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            print(f"Binance API Error {response.status}: {error_text}")
                            return None
        except Exception as e:
            print(f"Request error: {e}")
            return None
    
    async def get_account_info(self) -> Optional[Dict]:
        """Get account information including balances"""
        return await self._make_request('GET', '/api/v3/account', signed=True)
    
    async def get_ticker_24hr(self, symbol: str = None) -> Optional[Dict]:
        """Get 24hr ticker price change statistics"""
        params = {}
        if symbol:
            params['symbol'] = symbol.replace('/', '')
        
        return await self._make_request('GET', '/api/v3/ticker/24hr', params)
    
    async def get_ticker_price(self, symbol: str = None) -> Optional[Dict]:
        """Get latest price for symbol(s)"""
        params = {}
        if symbol:
            params['symbol'] = symbol.replace('/', '')
        
        return await self._make_request('GET', '/api/v3/ticker/price', params)
    
    async def get_exchange_info(self) -> Optional[Dict]:
        """Get exchange trading rules and symbol information"""
        return await self._make_request('GET', '/api/v3/exchangeInfo')
    
    async def test_connectivity(self) -> bool:
        """Test API connectivity"""
        result = await self._make_request('GET', '/api/v3/ping')
        return result is not None
    
    async def get_server_time(self) -> Optional[Dict]:
        """Get server time"""
        return await self._make_request('GET', '/api/v3/time')
    
    async def get_formatted_balances(self) -> Dict[str, Any]:
        """Get formatted account balances"""
        account_info = await self.get_account_info()
        
        if not account_info:
            return {
                "success": False,
                "message": "Failed to fetch account info",
                "balances": {},
                "total_usdt_value": 0
            }
        
        # Filter and format balances
        filtered_balances = {}
        major_currencies = ['USDT', 'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'LTC', 'ADA', 'DOT', 'MATIC']
        
        for balance in account_info.get('balances', []):
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            if asset in major_currencies and total > 0:
                filtered_balances[asset] = {
                    'free': free,
                    'used': locked,
                    'total': total
                }
        
        # Calculate total USDT value (simplified - just USDT for now)
        total_usdt_value = filtered_balances.get('USDT', {}).get('total', 0)
        
        return {
            "success": True,
            "exchange": "binance",
            "balances": filtered_balances,
            "total_usdt_value": total_usdt_value,
            "timestamp": time.time()
        }
    
    async def get_formatted_market_data(self) -> Dict[str, Any]:
        """Get formatted market data for grid trading pairs"""
        pairs = ['PEPEUSDT', 'FLOKIUSDT', 'DOGEUSDT', 'SHIBUSDT', 'SUIUSDT', 'BTCUSDT', 'ETHUSDT']
        market_data = {}
        
        try:
            # Get 24hr ticker data for all symbols
            all_tickers = await self.get_ticker_24hr()
            
            if not all_tickers:
                return {
                    "success": False,
                    "message": "Failed to fetch market data",
                    "market_data": {}
                }
            
            # Convert to dict for easy lookup
            ticker_dict = {}
            if isinstance(all_tickers, list):
                for ticker in all_tickers:
                    ticker_dict[ticker['symbol']] = ticker
            
            # Format data for our pairs
            for pair in pairs:
                if pair in ticker_dict:
                    ticker = ticker_dict[pair]
                    # Handle different token lengths
                    if pair.endswith('USDT'):
                        base_token = pair[:-4]  # Remove 'USDT'
                        formatted_pair = base_token + '/USDT'
                    else:
                        formatted_pair = pair[:3] + '/' + pair[3:]  # Fallback

                    market_data[formatted_pair] = {
                        'symbol': formatted_pair,
                        'price': float(ticker.get('lastPrice', 0)),
                        'change_24h': float(ticker.get('priceChangePercent', 0)),
                        'volume_24h': float(ticker.get('quoteVolume', 0)),
                        'high_24h': float(ticker.get('highPrice', 0)),
                        'low_24h': float(ticker.get('lowPrice', 0)),
                        'is_fresh': True,
                        'timestamp': time.time()
                    }
                else:
                    # Fallback data
                    if pair.endswith('USDT'):
                        base_token = pair[:-4]
                        formatted_pair = base_token + '/USDT'
                    else:
                        formatted_pair = pair[:3] + '/' + pair[3:]
                    market_data[formatted_pair] = {
                        'symbol': formatted_pair,
                        'price': 0,
                        'change_24h': 0,
                        'volume_24h': 0,
                        'high_24h': 0,
                        'low_24h': 0,
                        'is_fresh': False,
                        'timestamp': time.time()
                    }
            
            return {
                "success": True,
                "market_data": market_data,
                "timestamp": time.time(),
                "data_age": 0
            }
            
        except Exception as e:
            print(f"Error getting market data: {e}")
            return {
                "success": False,
                "message": f"Error fetching market data: {e}",
                "market_data": {},
                "timestamp": time.time(),
                "data_age": 999
            }

    async def get_public_market_data(self) -> Dict[str, Any]:
        """Get market data using public API only (no authentication required)"""
        pairs = ['PEPEUSDT', 'FLOKIUSDT', 'DOGEUSDT', 'SHIBUSDT', 'SUIUSDT', 'BTCUSDT', 'ETHUSDT']
        market_data = {}

        try:
            # Use public endpoint without authentication
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/v3/ticker/24hr"
                async with session.get(url) as response:
                    if response.status == 200:
                        all_tickers = await response.json()

                        # Convert to dict for easy lookup
                        ticker_dict = {}
                        if isinstance(all_tickers, list):
                            for ticker in all_tickers:
                                ticker_dict[ticker['symbol']] = ticker

                        # Format data for our pairs
                        for pair in pairs:
                            if pair in ticker_dict:
                                ticker = ticker_dict[pair]
                                # Handle different token lengths
                                if pair.endswith('USDT'):
                                    base_token = pair[:-4]  # Remove 'USDT'
                                    formatted_pair = base_token + '/USDT'
                                else:
                                    formatted_pair = pair[:3] + '/' + pair[3:]  # Fallback

                                market_data[formatted_pair] = {
                                    'symbol': formatted_pair,
                                    'price': float(ticker.get('lastPrice', 0)),
                                    'change_24h': float(ticker.get('priceChangePercent', 0)),
                                    'volume_24h': float(ticker.get('quoteVolume', 0)),
                                    'high_24h': float(ticker.get('highPrice', 0)),
                                    'low_24h': float(ticker.get('lowPrice', 0)),
                                    'is_fresh': True,
                                    'timestamp': time.time()
                                }

                        return {
                            "success": True,
                            "market_data": market_data,
                            "timestamp": time.time(),
                            "data_age": 0
                        }
                    else:
                        error_text = await response.text()
                        print(f"Public API Error {response.status}: {error_text}")
                        return {
                            "success": False,
                            "message": f"Public API error: {response.status}",
                            "market_data": {},
                            "timestamp": time.time(),
                            "data_age": 999
                        }

        except Exception as e:
            print(f"Error getting public market data: {e}")
            return {
                "success": False,
                "message": f"Error fetching public market data: {e}",
                "market_data": {},
                "timestamp": time.time(),
                "data_age": 999
            }

# Global instance
direct_binance = None

def initialize_direct_binance(api_key: str, secret_key: str, testnet: bool = False):
    """Initialize the direct Binance API client"""
    global direct_binance
    direct_binance = DirectBinanceAPI(api_key, secret_key, testnet)
    return direct_binance

async def test_connection():
    """Test the direct Binance connection"""
    if not direct_binance:
        return False
    
    try:
        # Test basic connectivity
        ping_result = await direct_binance.test_connectivity()
        if not ping_result:
            print("❌ Binance ping failed")
            return False
        
        print("✅ Binance ping successful")
        
        # Test server time
        server_time = await direct_binance.get_server_time()
        if server_time:
            print(f"✅ Server time: {server_time}")
        
        # Test market data (public endpoint)
        market_data = await direct_binance.get_formatted_market_data()
        if market_data['success']:
            print("✅ Market data fetch successful")
            for pair, data in market_data['market_data'].items():
                print(f"   {pair}: ${data['price']:,.2f} ({data['change_24h']:+.2f}%)")
        
        # Test account info (private endpoint)
        account_data = await direct_binance.get_formatted_balances()
        if account_data['success']:
            print("✅ Account data fetch successful")
            print(f"   Total USDT value: ${account_data['total_usdt_value']:.2f}")
            for asset, balance in account_data['balances'].items():
                print(f"   {asset}: {balance['total']:.8f}")
        else:
            print(f"❌ Account data fetch failed: {account_data['message']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the direct connection
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    if api_key and secret_key:
        initialize_direct_binance(api_key, secret_key)
        asyncio.run(test_connection())
    else:
        print("❌ API keys not found in environment")
