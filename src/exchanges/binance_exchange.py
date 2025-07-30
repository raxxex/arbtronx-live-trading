"""
Binance Exchange Implementation
"""
import asyncio
import json
import time
from typing import Dict, List, Optional, Any
import ccxt.async_support as ccxt
import websockets
from loguru import logger

from .base import BaseExchange, OrderBook, Balance, Trade


class BinanceExchange(BaseExchange):
    """Binance exchange implementation using CCXT and WebSocket"""
    
    def __init__(self, credentials: Dict[str, str]):
        super().__init__("Binance", credentials)
        self.ccxt_exchange = None
        self.websocket = None
        self.websocket_task = None
        self.websocket_url = "wss://stream.binance.com:9443/ws"
        self.testnet_websocket_url = "wss://testnet.binance.vision/ws"
        
    async def connect(self) -> bool:
        """Connect to Binance exchange"""
        try:
            # Check if credentials are provided
            if not self.credentials.get('apiKey') or not self.credentials.get('secret'):
                logger.info(f"No credentials provided for {self.name}, skipping connection")
                return False

            # Initialize CCXT exchange
            self.ccxt_exchange = ccxt.binance({
                'apiKey': self.credentials['apiKey'],
                'secret': self.credentials['secret'],
                'sandbox': self.credentials.get('sandbox', False),
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',  # Use spot trading
                }
            })

            # Test connection
            await self.ccxt_exchange.load_markets()
            self.connected = True
            logger.info(f"Connected to {self.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to {self.name}: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Binance exchange"""
        try:
            if self.websocket_task:
                self.websocket_task.cancel()
                try:
                    await self.websocket_task
                except asyncio.CancelledError:
                    pass
            
            if self.websocket:
                await self.websocket.close()
            
            if self.ccxt_exchange:
                await self.ccxt_exchange.close()
            
            self.connected = False
            logger.info(f"Disconnected from {self.name}")
            
        except Exception as e:
            logger.error(f"Error disconnecting from {self.name}: {e}")

    async def fetch_ticker(self, symbol: str) -> Dict:
        """Fetch ticker data for a symbol"""
        try:
            if not self.ccxt_exchange:
                raise Exception("Exchange not connected")

            ticker = await self.ccxt_exchange.fetch_ticker(symbol)
            return ticker

        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol} from {self.name}: {e}")
            raise

    async def get_24h_ticker(self, symbol: str) -> Dict:
        """Get 24h ticker data"""
        try:
            ticker = await self.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'last': ticker.get('last', 0),
                'percentage': ticker.get('percentage', 0),
                'quoteVolume': ticker.get('quoteVolume', 0),
                'baseVolume': ticker.get('baseVolume', 0),
                'high': ticker.get('high', 0),
                'low': ticker.get('low', 0),
                'open': ticker.get('open', 0),
                'close': ticker.get('close', 0)
            }
        except Exception as e:
            logger.error(f"Error getting 24h ticker for {symbol}: {e}")
            return {}

    async def get_ohlcv(self, symbol: str, timeframe: str = '1m', limit: int = 100) -> List:
        """Get OHLCV data"""
        try:
            if not self.ccxt_exchange:
                raise Exception("Exchange not connected")

            ohlcv = await self.ccxt_exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return ohlcv

        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return []

    async def get_order_book(self, symbol: str) -> Optional[OrderBook]:
        """Get order book for a symbol"""
        try:
            if not self.ccxt_exchange:
                return None
            
            order_book_data = await self.ccxt_exchange.fetch_order_book(symbol, limit=20)
            
            order_book = OrderBook(
                symbol=symbol,
                bids=order_book_data['bids'],
                asks=order_book_data['asks'],
                timestamp=int(time.time() * 1000)
            )
            
            # Cache the order book
            self.update_order_book(order_book)
            return order_book
            
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol} from {self.name}: {e}")
            return None
    
    async def get_balance(self, currency: Optional[str] = None) -> Dict[str, Balance]:
        """Get account balance(s)"""
        try:
            if not self.ccxt_exchange:
                return {}
            
            balance_data = await self.ccxt_exchange.fetch_balance()
            balances = {}
            
            for curr, data in balance_data.items():
                if curr in ['info', 'free', 'used', 'total']:
                    continue
                
                if isinstance(data, dict) and 'total' in data:
                    balance = Balance(
                        currency=curr,
                        free=float(data.get('free', 0)),
                        used=float(data.get('used', 0)),
                        total=float(data.get('total', 0))
                    )
                    balances[curr] = balance
                    self.update_balance(balance)
            
            if currency:
                balance_obj = balances.get(currency)
                return {currency: balance_obj} if balance_obj else {}
            
            return balances
            
        except Exception as e:
            logger.error(f"Error fetching balance from {self.name}: {e}")
            return {}

    async def get_formatted_balances(self) -> Dict[str, Any]:
        """Get formatted account balances with USDT values - compatibility method"""
        try:
            balances = await self.get_balance()
            formatted_balances = {}
            total_usdt_value = 0.0
            
            for currency, balance in balances.items():
                if isinstance(balance, Balance) and balance.total > 0:
                    usdt_value = balance.total
                    if currency != 'USDT':
                        try:
                            ticker = await self.get_24h_ticker(f"{currency}/USDT")
                            price = ticker.get('last', 0) or ticker.get('close', 0)
                            usdt_value = balance.total * price
                        except:
                            usdt_value = 0
                    
                    formatted_balances[currency] = {
                        'free': balance.free,
                        'used': balance.used,
                        'total': balance.total,
                        'usdt_value': usdt_value
                    }
                    total_usdt_value += usdt_value
            
            return {
                "success": True,
                "balances": formatted_balances,
                "total_usdt_value": total_usdt_value
            }
            
        except Exception as e:
            logger.error(f"Error getting formatted balances: {e}")
            return {"success": False, "error": str(e)}

    async def get_formatted_market_data(self) -> Dict[str, Any]:
        """Get formatted market data for multiple symbols - compatibility method"""
        try:
            symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'DOT/USDT']
            market_data = {}
            
            for symbol in symbols:
                try:
                    ticker = await self.get_24h_ticker(symbol)
                    if ticker:
                        market_data[symbol.replace('/', '')] = {
                            'symbol': symbol.replace('/', ''),
                            'price': ticker.get('last', 0) or ticker.get('close', 0),
                            'change': ticker.get('change', 0),
                            'change_percent': ticker.get('percentage', 0),
                            'volume': ticker.get('baseVolume', 0),
                            'high': ticker.get('high', 0),
                            'low': ticker.get('low', 0)
                        }
                except Exception as e:
                    logger.warning(f"Failed to get data for {symbol}: {e}")
                    continue
            
            return {
                "success": True,
                "market_data": market_data,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting formatted market data: {e}")
            return {"success": False, "error": str(e)}
    
    async def place_market_order(self, symbol: str, side: str, amount: float) -> Trade:
        """Place a market order"""
        try:
            if not self.ccxt_exchange:
                raise Exception("Exchange not connected")
            
            order = await self.ccxt_exchange.create_market_order(symbol, side, amount)
            
            return Trade(
                id=order['id'],
                symbol=symbol,
                side=side,
                amount=amount,
                price=order.get('price', 0),
                fee=order.get('fee', {}).get('cost', 0),
                timestamp=order.get('timestamp', int(time.time() * 1000)),
                status=order.get('status', 'unknown'),
                cost=amount * order.get('price', 0)
            )
            
        except Exception as e:
            logger.error(f"Error placing market order on {self.name}: {e}")
            raise
    
    async def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Trade:
        """Place a limit order"""
        try:
            if not self.ccxt_exchange:
                raise Exception("Exchange not connected")
            
            order = await self.ccxt_exchange.create_limit_order(symbol, side, amount, price)
            
            return Trade(
                id=order['id'],
                symbol=symbol,
                side=side,
                amount=amount,
                price=price,
                fee=order.get('fee', {}).get('cost', 0),
                timestamp=order.get('timestamp', int(time.time() * 1000)),
                status=order.get('status', 'unknown'),
                cost=amount * price
            )
            
        except Exception as e:
            logger.error(f"Error placing limit order on {self.name}: {e}")
            raise
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        try:
            if not self.ccxt_exchange:
                return False
            
            await self.ccxt_exchange.cancel_order(order_id, symbol)
            return True
            
        except Exception as e:
            logger.error(f"Error canceling order {order_id} on {self.name}: {e}")
            return False
    
    async def get_trading_fees(self, symbol: str) -> Dict[str, float]:
        """Get trading fees for a symbol"""
        try:
            if not self.ccxt_exchange:
                return {}
            
            # Binance typically has 0.1% maker/taker fees for spot trading
            # This can be fetched dynamically if needed
            return {
                'maker': 0.001,  # 0.1%
                'taker': 0.001   # 0.1%
            }
            
        except Exception as e:
            logger.error(f"Error fetching trading fees for {symbol} from {self.name}: {e}")
            return {}
    
    async def start_websocket(self, symbols: List[str]):
        """Start WebSocket connection for real-time data"""
        try:
            if self.websocket_task:
                return
            
            self.websocket_task = asyncio.create_task(self._websocket_handler(symbols))
            logger.info(f"Started WebSocket for {self.name}")
            
        except Exception as e:
            logger.error(f"Error starting WebSocket for {self.name}: {e}")
    
    async def stop_websocket(self):
        """Stop WebSocket connection"""
        try:
            if self.websocket_task:
                self.websocket_task.cancel()
                try:
                    await self.websocket_task
                except asyncio.CancelledError:
                    pass
                self.websocket_task = None
            
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
            
            logger.info(f"Stopped WebSocket for {self.name}")
            
        except Exception as e:
            logger.error(f"Error stopping WebSocket for {self.name}: {e}")
    
    async def _websocket_handler(self, symbols: List[str]):
        """Handle WebSocket connection and messages"""
        try:
            # Convert symbols to Binance format (lowercase with no slash)
            binance_symbols = [symbol.replace('/', '').lower() for symbol in symbols]
            
            # Create stream names for order book updates
            streams = [f"{symbol}@depth20@100ms" for symbol in binance_symbols]
            stream_url = f"{self.websocket_url}/{'/'.join(streams)}"
            
            # Use testnet URL if in sandbox mode
            if self.credentials.get('sandbox', False):
                stream_url = f"{self.testnet_websocket_url}/{'/'.join(streams)}"
            
            async with websockets.connect(stream_url) as websocket:
                self.websocket = websocket
                logger.info(f"WebSocket connected to {self.name}")
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self._process_websocket_message(data)
                    except Exception as e:
                        logger.error(f"Error processing WebSocket message from {self.name}: {e}")
                        
        except Exception as e:
            logger.error(f"WebSocket error for {self.name}: {e}")
            # Attempt to reconnect after a delay
            await asyncio.sleep(5)
            if self.connected:
                await self.start_websocket(symbols)
    
    async def _process_websocket_message(self, data: dict):
        """Process incoming WebSocket messages"""
        try:
            if 'stream' in data and 'data' in data:
                stream = data['stream']
                message_data = data['data']
                
                # Handle depth updates
                if '@depth' in stream:
                    symbol_part = stream.split('@')[0].upper()
                    # Convert back to standard format (e.g., BTCUSDT -> BTC/USDT)
                    if symbol_part.endswith('USDT'):
                        symbol = f"{symbol_part[:-4]}/USDT"
                    else:
                        # Handle other quote currencies if needed
                        symbol = symbol_part
                    
                    order_book = OrderBook(
                        symbol=symbol,
                        bids=[(float(bid[0]), float(bid[1])) for bid in message_data.get('bids', [])],
                        asks=[(float(ask[0]), float(ask[1])) for ask in message_data.get('asks', [])],
                        timestamp=message_data.get('lastUpdateId', int(time.time() * 1000))
                    )
                    
                    self.update_order_book(order_book)
                    
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")

    async def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100):
        """
        Fetch OHLCV (Open, High, Low, Close, Volume) data for volatility analysis

        Args:
            symbol: Trading pair symbol (e.g., 'PEPE/USDT')
            timeframe: Timeframe for candles ('1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of candles to fetch (max 1000)

        Returns:
            List of OHLCV data: [[timestamp, open, high, low, close, volume], ...]
        """
        try:
            if not self.ccxt_exchange:
                logger.error("CCXT exchange not initialized")
                return []

            # Fetch OHLCV data using CCXT
            ohlcv = await self.ccxt_exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

            logger.debug(f"Fetched {len(ohlcv)} OHLCV candles for {symbol} ({timeframe})")
            return ohlcv

        except Exception as e:
            logger.error(f"Error fetching OHLCV data for {symbol}: {e}")
            return []

    async def calculate_volatility(self, symbol: str, timeframe: str = '1h', periods: int = 24):
        """
        Calculate price volatility for a symbol

        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe for analysis
            periods: Number of periods to analyze

        Returns:
            float: Volatility percentage (0.0 to 100.0)
        """
        try:
            ohlcv = await self.fetch_ohlcv(symbol, timeframe, periods + 1)

            if len(ohlcv) < 2:
                logger.warning(f"Insufficient data for volatility calculation: {symbol}")
                return 1.5  # Default medium volatility

            # Calculate price changes
            price_changes = []
            for i in range(1, len(ohlcv)):
                prev_close = ohlcv[i-1][4]  # Previous close price
                curr_close = ohlcv[i][4]    # Current close price

                if prev_close > 0:
                    change_pct = abs((curr_close - prev_close) / prev_close) * 100
                    price_changes.append(change_pct)

            if not price_changes:
                return 1.5  # Default medium volatility

            # Calculate average volatility
            avg_volatility = sum(price_changes) / len(price_changes)

            logger.debug(f"Calculated volatility for {symbol}: {avg_volatility:.2f}%")
            return avg_volatility

        except Exception as e:
            logger.error(f"Error calculating volatility for {symbol}: {e}")
            return 1.5  # Default medium volatility
