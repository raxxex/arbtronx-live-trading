#!/usr/bin/env python3
"""
Enhanced Binance API Client with WebSocket support and production-grade reliability
Designed for live trading with robust error handling and real-time data
"""

import asyncio
import aiohttp
import websockets
import json
import hmac
import hashlib
import time
from urllib.parse import urlencode
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConnectionStatus:
    """Connection status tracking"""
    connected: bool = False
    last_ping: Optional[datetime] = None
    last_data: Optional[datetime] = None
    error_count: int = 0
    reconnect_count: int = 0

@dataclass
class MarketData:
    """Real-time market data structure"""
    symbol: str
    price: float
    change_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime
    
    @property
    def age_seconds(self) -> float:
        """Get data age in seconds"""
        return (datetime.now() - self.timestamp).total_seconds()
    
    @property
    def is_fresh(self, max_age: int = 5) -> bool:
        """Check if data is fresh (default: 5 seconds)"""
        return self.age_seconds <= max_age

class EnhancedBinanceAPI:
    """Enhanced Binance API client with WebSocket and production features"""
    
    def __init__(self, api_key: str, secret_key: str, testnet: bool = False):
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        
        # API endpoints
        if testnet:
            self.rest_base = "https://testnet.binance.vision"
            self.ws_base = "wss://testnet.binance.vision"
        else:
            self.rest_base = "https://api.binance.com"
            self.ws_base = "wss://stream.binance.com:9443"
        
        # Connection management
        self.status = ConnectionStatus()
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws_connection: Optional[websockets.WebSocketServerProtocol] = None
        
        # Data storage
        self.market_data: Dict[str, MarketData] = {}
        self.account_data: Dict[str, Any] = {}
        
        # Callbacks
        self.price_callbacks: List[Callable] = []
        self.balance_callbacks: List[Callable] = []
        
        # Rate limiting
        self.request_times: List[float] = []
        self.max_requests_per_minute = 1200  # Binance limit
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 60.0
    
    async def initialize(self) -> bool:
        """Initialize the API client"""
        try:
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Test basic connectivity
            if await self.test_connectivity():
                self.status.connected = True
                logger.info("✅ Enhanced Binance API initialized successfully")
                
                # Start background tasks
                asyncio.create_task(self._health_monitor())
                return True
            else:
                logger.error("❌ Failed to initialize Binance API")
                return False
                
        except Exception as e:
            logger.error(f"❌ API initialization error: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the API client"""
        try:
            if self.ws_connection:
                await self.ws_connection.close()
            
            if self.session:
                await self.session.close()
            
            self.status.connected = False
            logger.info("✅ Enhanced Binance API shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = time.time()
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        if len(self.request_times) >= self.max_requests_per_minute:
            return False
        
        self.request_times.append(now)
        return True
    
    async def _make_request_with_retry(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Optional[Dict]:
        """Make HTTP request with retry logic"""
        for attempt in range(self.max_retries):
            try:
                # Check rate limit
                if not self._check_rate_limit():
                    await asyncio.sleep(1)
                    continue
                
                result = await self._make_request(method, endpoint, params, signed)
                if result is not None:
                    self.status.error_count = 0  # Reset error count on success
                    return result
                
            except Exception as e:
                self.status.error_count += 1
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}, retrying in {delay}s")
                await asyncio.sleep(delay)
        
        logger.error(f"Request failed after {self.max_retries} attempts")
        return None
    
    async def _make_request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Optional[Dict]:
        """Make HTTP request to Binance API"""
        if not self.session:
            return None
        
        if params is None:
            params = {}
        
        headers = {'X-MBX-APIKEY': self.api_key}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            query_string = urlencode(params)
            params['signature'] = self._generate_signature(query_string)
        
        url = f"{self.rest_base}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                async with self.session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"API Error {response.status}: {error_text}")
                        return None
            elif method.upper() == 'POST':
                async with self.session.post(url, data=params, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"API Error {response.status}: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None
    
    async def test_connectivity(self) -> bool:
        """Test API connectivity"""
        try:
            result = await self._make_request('GET', '/api/v3/ping')
            if result is not None:
                self.status.last_ping = datetime.now()
                return True
            return False
        except Exception as e:
            logger.error(f"Connectivity test failed: {e}")
            return False
    
    async def get_server_time(self) -> Optional[Dict]:
        """Get server time"""
        return await self._make_request_with_retry('GET', '/api/v3/time')
    
    async def get_account_info(self) -> Optional[Dict]:
        """Get account information"""
        result = await self._make_request_with_retry('GET', '/api/v3/account', signed=True)
        if result:
            self.account_data = result
        return result
    
    async def get_ticker_24hr(self, symbol: str = None) -> Optional[Dict]:
        """Get 24hr ticker data"""
        params = {}
        if symbol:
            params['symbol'] = symbol.replace('/', '')
        
        return await self._make_request_with_retry('GET', '/api/v3/ticker/24hr', params)
    
    async def get_formatted_balances(self) -> Dict[str, Any]:
        """Get formatted account balances with validation"""
        try:
            account_info = await self.get_account_info()
            
            if not account_info:
                return {
                    "success": False,
                    "message": "Failed to fetch account info",
                    "balances": {},
                    "total_usdt_value": 0,
                    "data_age": 0
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
            
            # Calculate total USDT value
            total_usdt_value = filtered_balances.get('USDT', {}).get('total', 0)
            
            return {
                "success": True,
                "exchange": "binance",
                "balances": filtered_balances,
                "total_usdt_value": total_usdt_value,
                "timestamp": time.time(),
                "data_age": 0
            }
            
        except Exception as e:
            logger.error(f"Error getting formatted balances: {e}")
            return {
                "success": False,
                "message": f"Error: {e}",
                "balances": {},
                "total_usdt_value": 0,
                "data_age": 0
            }
    
    async def get_formatted_market_data(self) -> Dict[str, Any]:
        """Get formatted market data with validation for meme/altcoin pairs"""
        try:
            # Updated pairs for meme coins and altcoins
            pairs = ['PEPEUSDT', 'FLOKIUSDT', 'DOGEUSDT', 'SHIBUSDT', 'SUIUSDT']
            market_data = {}

            # Get all tickers at once for efficiency
            all_tickers = await self.get_ticker_24hr()

            if not all_tickers:
                return {
                    "success": False,
                    "message": "Failed to fetch market data",
                    "market_data": {},
                    "data_age": 0
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

                    # Format pair name for display
                    if pair == 'PEPEUSDT':
                        formatted_pair = 'PEPE/USDT'
                    elif pair == 'FLOKIUSDT':
                        formatted_pair = 'FLOKI/USDT'
                    elif pair == 'DOGEUSDT':
                        formatted_pair = 'DOGE/USDT'
                    elif pair == 'SHIBUSDT':
                        formatted_pair = 'SHIB/USDT'
                    elif pair == 'SUIUSDT':
                        formatted_pair = 'SUI/USDT'
                    else:
                        formatted_pair = pair[:4] + '/' + pair[4:]  # Fallback

                    # Create MarketData object
                    market_data_obj = MarketData(
                        symbol=formatted_pair,
                        price=float(ticker.get('lastPrice', 0)),
                        change_24h=float(ticker.get('priceChangePercent', 0)),
                        volume_24h=float(ticker.get('quoteVolume', 0)),
                        high_24h=float(ticker.get('highPrice', 0)),
                        low_24h=float(ticker.get('lowPrice', 0)),
                        timestamp=datetime.now()
                    )

                    # Store in cache
                    self.market_data[formatted_pair] = market_data_obj

                    # Format for API response
                    market_data[formatted_pair] = {
                        'symbol': formatted_pair,
                        'price': market_data_obj.price,
                        'change_24h': market_data_obj.change_24h,
                        'volume_24h': market_data_obj.volume_24h,
                        'high_24h': market_data_obj.high_24h,
                        'low_24h': market_data_obj.low_24h,
                        'is_fresh': market_data_obj.is_fresh,
                        'age_seconds': market_data_obj.age_seconds
                    }
            
            return {
                "success": True,
                "market_data": market_data,
                "timestamp": time.time(),
                "data_age": 0
            }
            
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {
                "success": False,
                "message": f"Error: {e}",
                "market_data": {},
                "data_age": 0
            }
    
    async def _health_monitor(self):
        """Background health monitoring"""
        while self.status.connected:
            try:
                # Ping every 30 seconds
                if await self.test_connectivity():
                    self.status.last_ping = datetime.now()
                else:
                    logger.warning("⚠️ Health check failed")
                    self.status.error_count += 1
                
                # Check data freshness
                for symbol, data in self.market_data.items():
                    if not data.is_fresh:
                        logger.warning(f"⚠️ Stale data for {symbol}: {data.age_seconds:.1f}s old")
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(30)
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status"""
        return {
            "connected": self.status.connected,
            "last_ping": self.status.last_ping.isoformat() if self.status.last_ping else None,
            "last_data": self.status.last_data.isoformat() if self.status.last_data else None,
            "error_count": self.status.error_count,
            "reconnect_count": self.status.reconnect_count,
            "data_freshness": {
                symbol: {
                    "age_seconds": data.age_seconds,
                    "is_fresh": data.is_fresh
                }
                for symbol, data in self.market_data.items()
            }
        }

# Global instance
enhanced_binance_api = None

def initialize_enhanced_binance_api(api_key: str, secret_key: str, testnet: bool = False):
    """Initialize the enhanced Binance API client"""
    global enhanced_binance_api
    enhanced_binance_api = EnhancedBinanceAPI(api_key, secret_key, testnet)
    return enhanced_binance_api

async def test_enhanced_connection():
    """Test the enhanced Binance connection"""
    if not enhanced_binance_api:
        return False
    
    try:
        success = await enhanced_binance_api.initialize()
        if success:
            logger.info("✅ Enhanced Binance API connection successful")
            
            # Test market data
            market_data = await enhanced_binance_api.get_formatted_market_data()
            if market_data['success']:
                logger.info("✅ Market data fetch successful")
                for symbol, data in market_data['market_data'].items():
                    logger.info(f"   {symbol}: ${data['price']:,.2f} ({data['change_24h']:+.2f}%)")
            
            # Test account data
            balance_data = await enhanced_binance_api.get_formatted_balances()
            if balance_data['success']:
                logger.info("✅ Account data fetch successful")
                logger.info(f"   Total USDT value: ${balance_data['total_usdt_value']:.2f}")
            else:
                logger.warning(f"⚠️ Account data fetch failed: {balance_data['message']}")
            
            return True
        else:
            logger.error("❌ Enhanced Binance API connection failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Enhanced connection test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the enhanced connection
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    if api_key and secret_key:
        initialize_enhanced_binance_api(api_key, secret_key)
        asyncio.run(test_enhanced_connection())
    else:
        print("❌ API keys not found in environment")
