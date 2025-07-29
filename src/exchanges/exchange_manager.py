"""
Exchange Manager - Manages multiple exchange connections
"""
import asyncio
import os
from typing import Dict, List, Optional
from loguru import logger

from .base import BaseExchange, OrderBook, Balance, Trade
from .kucoin_exchange import KuCoinExchange
from .okx_exchange import OKXExchange
from .binance_exchange import BinanceExchange


class ExchangeManager:
    """Manages multiple exchange connections and operations"""
    
    def __init__(self):
        self.exchanges: Dict[str, BaseExchange] = {}
        self.connected = False
        
    async def initialize(self):
        """Initialize all exchanges"""
        try:
            # Read credentials directly from environment
            binance_credentials = {
                'apiKey': os.getenv('BINANCE_API_KEY'),
                'secret': os.getenv('BINANCE_SECRET_KEY'),
                'sandbox': os.getenv('BINANCE_SANDBOX', 'false').lower() == 'true'
            }

            kucoin_credentials = {
                'apiKey': os.getenv('KUCOIN_API_KEY'),
                'secret': os.getenv('KUCOIN_SECRET_KEY'),
                'passphrase': os.getenv('KUCOIN_PASSPHRASE'),
                'sandbox': os.getenv('KUCOIN_SANDBOX', 'false').lower() == 'true'
            }

            okx_credentials = {
                'apiKey': os.getenv('OKX_API_KEY'),
                'secret': os.getenv('OKX_SECRET_KEY'),
                'passphrase': os.getenv('OKX_PASSPHRASE'),
                'sandbox': os.getenv('OKX_SANDBOX', 'false').lower() == 'true'
            }

            # Debug: Print credentials
            logger.info(f"Binance credentials check: {binance_credentials}")

            # Initialize KuCoin (if credentials are provided)
            if kucoin_credentials.get('apiKey'):
                try:
                    kucoin = KuCoinExchange(kucoin_credentials)
                    if await kucoin.connect():
                        self.exchanges['kucoin'] = kucoin
                        logger.info("KuCoin exchange initialized")
                    else:
                        logger.warning("Failed to initialize KuCoin exchange")
                except Exception as e:
                    logger.warning(f"KuCoin initialization error: {e}")
            else:
                logger.info("KuCoin credentials not provided, skipping...")

            # Initialize OKX (if credentials are provided)
            if okx_credentials.get('apiKey'):
                try:
                    okx = OKXExchange(okx_credentials)
                    if await okx.connect():
                        self.exchanges['okx'] = okx
                        logger.info("OKX exchange initialized")
                    else:
                        logger.warning("Failed to initialize OKX exchange")
                except Exception as e:
                    logger.warning(f"OKX initialization error: {e}")
            else:
                logger.info("OKX credentials not provided, skipping...")

            # Initialize Binance (if credentials are provided)
            if binance_credentials.get('apiKey'):
                try:
                    binance = BinanceExchange(binance_credentials)
                    if await binance.connect():
                        self.exchanges['binance'] = binance
                        logger.info("Binance exchange initialized")
                    else:
                        logger.warning("Failed to initialize Binance exchange")
                except Exception as e:
                    logger.warning(f"Binance initialization error: {e}")
            else:
                logger.info("Binance credentials not provided, skipping...")

            if self.exchanges:
                self.connected = True
                logger.info(f"Exchange manager initialized with {len(self.exchanges)} exchanges")
                if len(self.exchanges) == 1:
                    logger.warning("Only one exchange available - arbitrage opportunities will be limited")
            else:
                logger.error("No exchanges could be initialized")

        except Exception as e:
            logger.error(f"Error initializing exchanges: {e}")
    
    async def shutdown(self):
        """Shutdown all exchanges"""
        try:
            for exchange in self.exchanges.values():
                await exchange.disconnect()
            
            self.exchanges.clear()
            self.connected = False
            logger.info("All exchanges disconnected")
            
        except Exception as e:
            logger.error(f"Error shutting down exchanges: {e}")
    
    async def start_websockets(self, symbols: List[str]):
        """Start WebSocket connections for all exchanges"""
        try:
            tasks = []
            for exchange in self.exchanges.values():
                task = asyncio.create_task(exchange.start_websocket(symbols))
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("WebSocket connections started for all exchanges")
            
        except Exception as e:
            logger.error(f"Error starting WebSocket connections: {e}")
    
    async def stop_websockets(self):
        """Stop WebSocket connections for all exchanges"""
        try:
            tasks = []
            for exchange in self.exchanges.values():
                task = asyncio.create_task(exchange.stop_websocket())
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("WebSocket connections stopped for all exchanges")
            
        except Exception as e:
            logger.error(f"Error stopping WebSocket connections: {e}")
    
    async def get_order_books(self, symbol: str) -> Dict[str, OrderBook]:
        """Get order books from all exchanges for a symbol"""
        order_books = {}
        
        tasks = []
        for name, exchange in self.exchanges.items():
            task = asyncio.create_task(self._get_exchange_order_book(name, exchange, symbol))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                name, order_book = result
                if order_book:
                    order_books[name] = order_book
        
        return order_books
    
    async def _get_exchange_order_book(self, name: str, exchange: BaseExchange, symbol: str) -> tuple:
        """Helper method to get order book from a specific exchange"""
        try:
            order_book = await exchange.get_order_book(symbol)
            return (name, order_book)
        except Exception as e:
            logger.error(f"Error getting order book from {name}: {e}")
            return (name, None)
    
    async def get_balances(self, currency: str = None) -> Dict[str, Dict[str, Balance]]:
        """Get balances from all exchanges"""
        balances = {}
        
        tasks = []
        for name, exchange in self.exchanges.items():
            task = asyncio.create_task(self._get_exchange_balance(name, exchange, currency))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                name, balance = result
                if balance:
                    balances[name] = balance
        
        return balances
    
    async def _get_exchange_balance(self, name: str, exchange: BaseExchange, currency: str) -> tuple:
        """Helper method to get balance from a specific exchange"""
        try:
            balance = await exchange.get_balance(currency)
            return (name, balance)
        except Exception as e:
            logger.error(f"Error getting balance from {name}: {e}")
            return (name, {})
    
    def get_exchange(self, name: str) -> Optional[BaseExchange]:
        """Get a specific exchange by name"""
        return self.exchanges.get(name.lower())
    
    def get_exchange_names(self) -> List[str]:
        """Get list of connected exchange names"""
        return list(self.exchanges.keys())
    
    def is_connected(self) -> bool:
        """Check if exchange manager is connected"""
        return self.connected and len(self.exchanges) > 0
    
    def get_cached_order_books(self, symbol: str) -> Dict[str, OrderBook]:
        """Get cached order books from all exchanges"""
        order_books = {}

        for name, exchange in self.exchanges.items():
            order_book = exchange.get_cached_order_book(symbol)
            if order_book:
                order_books[name] = order_book

        return order_books

    async def place_order(self, symbol: str, side: str, order_type: str, amount: float,
                         price: Optional[float] = None, exchange: str = 'binance') -> Dict:
        """
        Place a REAL order on the specified exchange

        Args:
            symbol: Trading pair (e.g., 'PEPE/USDT')
            side: 'buy' or 'sell'
            order_type: 'market' or 'limit'
            amount: Amount to trade
            price: Price for limit orders (required for limit orders)
            exchange: Exchange name (default: 'binance')

        Returns:
            Dict with success status and order details
        """
        try:
            if not self.connected:
                return {
                    'success': False,
                    'error': 'EXCHANGE_NOT_CONNECTED',
                    'message': 'Exchange manager not connected'
                }

            if exchange not in self.exchanges:
                return {
                    'success': False,
                    'error': 'EXCHANGE_NOT_AVAILABLE',
                    'message': f'Exchange {exchange} not available'
                }

            exchange_obj = self.exchanges[exchange]

            logger.info(f"🔴 PLACING REAL ORDER: {side.upper()} {amount:.6f} {symbol} @ {price or 'MARKET'} on {exchange.upper()}")

            # Place the order based on type
            if order_type.lower() == 'market':
                trade = await exchange_obj.place_market_order(symbol, side, amount)
            elif order_type.lower() == 'limit':
                if price is None:
                    return {
                        'success': False,
                        'error': 'PRICE_REQUIRED',
                        'message': 'Price is required for limit orders'
                    }
                trade = await exchange_obj.place_limit_order(symbol, side, amount, price)
            else:
                return {
                    'success': False,
                    'error': 'INVALID_ORDER_TYPE',
                    'message': f'Invalid order type: {order_type}'
                }

            if trade:
                logger.info(f"✅ REAL ORDER PLACED: {trade.id} - {side.upper()} {amount:.6f} {symbol}")
                return {
                    'success': True,
                    'order_id': trade.id,
                    'symbol': trade.symbol,
                    'side': trade.side,
                    'amount': trade.amount,
                    'price': trade.price,
                    'timestamp': trade.timestamp,
                    'exchange': exchange,
                    'is_live': True
                }
            else:
                return {
                    'success': False,
                    'error': 'ORDER_FAILED',
                    'message': 'Order placement failed - no trade returned'
                }

        except Exception as e:
            logger.error(f"❌ REAL ORDER ERROR: {e}")
            return {
                'success': False,
                'error': 'ORDER_EXCEPTION',
                'message': str(e)
            }

    async def cancel_order(self, order_id: str, symbol: str, exchange: str = 'binance') -> Dict:
        """
        Cancel a REAL order on the specified exchange

        Args:
            order_id: Order ID to cancel
            symbol: Trading pair
            exchange: Exchange name (default: 'binance')

        Returns:
            Dict with success status
        """
        try:
            if not self.connected:
                return {
                    'success': False,
                    'error': 'EXCHANGE_NOT_CONNECTED',
                    'message': 'Exchange manager not connected'
                }

            if exchange not in self.exchanges:
                return {
                    'success': False,
                    'error': 'EXCHANGE_NOT_AVAILABLE',
                    'message': f'Exchange {exchange} not available'
                }

            exchange_obj = self.exchanges[exchange]

            logger.info(f"🛑 CANCELING REAL ORDER: {order_id} on {exchange.upper()}")

            success = await exchange_obj.cancel_order(order_id, symbol)

            if success:
                logger.info(f"✅ REAL ORDER CANCELED: {order_id}")
                return {
                    'success': True,
                    'order_id': order_id,
                    'symbol': symbol,
                    'exchange': exchange,
                    'is_live': True
                }
            else:
                return {
                    'success': False,
                    'error': 'CANCEL_FAILED',
                    'message': f'Failed to cancel order {order_id}'
                }

        except Exception as e:
            logger.error(f"❌ CANCEL ORDER ERROR: {e}")
            return {
                'success': False,
                'error': 'CANCEL_EXCEPTION',
                'message': str(e)
            }
    
    def get_cached_balances(self, currency: str = None) -> Dict[str, Dict[str, Balance]]:
        """Get cached balances from all exchanges"""
        balances = {}
        
        for name, exchange in self.exchanges.items():
            balance = exchange.get_cached_balance(currency)
            if balance:
                balances[name] = balance
        
        return balances

    async def disconnect_all(self):
        """Disconnect from all exchanges"""
        try:
            for name, exchange in self.exchanges.items():
                try:
                    await exchange.disconnect()
                    logger.info(f"Disconnected from {name}")
                except Exception as e:
                    logger.error(f"Error disconnecting from {name}: {e}")

            self.exchanges.clear()
            self.connected = False
            logger.info("All exchanges disconnected")

        except Exception as e:
            logger.error(f"Error during disconnect_all: {e}")

    async def get_24h_ticker(self, exchange_name: str, symbol: str) -> Dict:
        """Get 24h ticker from specific exchange"""
        try:
            if exchange_name not in self.exchanges:
                raise Exception(f"Exchange {exchange_name} not found")

            exchange = self.exchanges[exchange_name]
            return await exchange.get_24h_ticker(symbol)

        except Exception as e:
            logger.error(f"Error getting 24h ticker from {exchange_name}: {e}")
            return {}

    async def get_ohlcv(self, exchange_name: str, symbol: str, timeframe: str = '1m', limit: int = 100) -> List:
        """Get OHLCV data from specific exchange"""
        try:
            if exchange_name not in self.exchanges:
                raise Exception(f"Exchange {exchange_name} not found")

            exchange = self.exchanges[exchange_name]
            return await exchange.get_ohlcv(symbol, timeframe, limit)

        except Exception as e:
            logger.error(f"Error getting OHLCV from {exchange_name}: {e}")
            return []

    async def get_balance(self, exchange_name: str, currency: str) -> Dict:
        """Get balance from specific exchange"""
        try:
            if exchange_name not in self.exchanges:
                raise Exception(f"Exchange {exchange_name} not found")

            exchange = self.exchanges[exchange_name]
            balance = await exchange.get_balance(currency)

            if balance:
                return {
                    'free': balance.free,
                    'used': balance.used,
                    'total': balance.total
                }
            else:
                return {'free': 0.0, 'used': 0.0, 'total': 0.0}

        except Exception as e:
            logger.error(f"Error getting balance from {exchange_name}: {e}")
            return {'free': 0.0, 'used': 0.0, 'total': 0.0}

    async def reconnect_exchange(self, exchange_name: str) -> bool:
        """Reconnect to a specific exchange"""
        try:
            if exchange_name not in self.exchanges:
                logger.error(f"Exchange {exchange_name} not found")
                return False

            exchange = self.exchanges[exchange_name]
            await exchange.disconnect()

            # Wait a bit before reconnecting
            await asyncio.sleep(2)

            success = await exchange.connect()
            if success:
                logger.info(f"Successfully reconnected to {exchange_name}")
            else:
                logger.error(f"Failed to reconnect to {exchange_name}")

            return success

        except Exception as e:
            logger.error(f"Error reconnecting to {exchange_name}: {e}")
            return False
