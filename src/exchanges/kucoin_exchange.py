"""
KuCoin Exchange Implementation
"""
import asyncio
import json
import time
from typing import Dict, List, Optional
import ccxt.async_support as ccxt
import websockets
from loguru import logger

from .base import BaseExchange, OrderBook, Balance, Trade


class KuCoinExchange(BaseExchange):
    """KuCoin exchange implementation using CCXT and WebSocket"""
    
    def __init__(self, credentials: Dict[str, str]):
        super().__init__("KuCoin", credentials)
        self.ccxt_exchange = None
        self.websocket = None
        self.websocket_task = None
        self.websocket_url = "wss://ws-api-spot.kucoin.com/"
        
    async def connect(self) -> bool:
        """Connect to KuCoin exchange"""
        try:
            # Initialize CCXT exchange
            self.ccxt_exchange = ccxt.kucoin({
                'apiKey': self.credentials['apiKey'],
                'secret': self.credentials['secret'],
                'password': self.credentials['password'],
                'sandbox': self.credentials.get('sandbox', False),
                'enableRateLimit': True,
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
        """Disconnect from KuCoin exchange"""
        try:
            if self.websocket_task:
                self.websocket_task.cancel()
                
            if self.websocket:
                await self.websocket.close()
                
            if self.ccxt_exchange:
                await self.ccxt_exchange.close()
                
            self.connected = False
            logger.info(f"Disconnected from {self.name}")
            
        except Exception as e:
            logger.error(f"Error disconnecting from {self.name}: {e}")
    
    async def get_order_book(self, symbol: str) -> Optional[OrderBook]:
        """Get order book for a symbol"""
        try:
            if not self.ccxt_exchange:
                return None
                
            order_book_data = await self.ccxt_exchange.fetch_order_book(symbol)
            
            order_book = OrderBook(
                symbol=symbol,
                bids=order_book_data['bids'],
                asks=order_book_data['asks'],
                timestamp=int(time.time() * 1000)
            )
            
            self.update_order_book(order_book)
            return order_book
            
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol} from {self.name}: {e}")
            return None
    
    async def get_balance(self, currency: str = None) -> Dict[str, Balance]:
        """Get account balance(s)"""
        try:
            if not self.ccxt_exchange:
                return {}
                
            balance_data = await self.ccxt_exchange.fetch_balance()
            balances = {}
            
            for curr, data in balance_data.items():
                if curr in ['info', 'free', 'used', 'total']:
                    continue
                    
                if currency and curr != currency:
                    continue
                    
                balance = Balance(
                    currency=curr,
                    free=float(data.get('free', 0)),
                    used=float(data.get('used', 0)),
                    total=float(data.get('total', 0))
                )
                balances[curr] = balance
                self.update_balance(balance)
            
            return balances
            
        except Exception as e:
            logger.error(f"Error fetching balance from {self.name}: {e}")
            return {}
    
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
                amount=float(order['amount']),
                price=float(order.get('price', 0)),
                cost=float(order.get('cost', 0)),
                fee=float(order.get('fee', {}).get('cost', 0)),
                timestamp=order['timestamp'],
                status=order['status']
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
                amount=float(order['amount']),
                price=float(order['price']),
                cost=float(order.get('cost', 0)),
                fee=float(order.get('fee', {}).get('cost', 0)),
                timestamp=order['timestamp'],
                status=order['status']
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
                return {'maker': 0.001, 'taker': 0.001}  # Default KuCoin fees
                
            fees = await self.ccxt_exchange.fetch_trading_fees()
            symbol_fees = fees.get(symbol, {})
            
            return {
                'maker': float(symbol_fees.get('maker', 0.001)),
                'taker': float(symbol_fees.get('taker', 0.001))
            }
            
        except Exception as e:
            logger.error(f"Error fetching trading fees for {symbol} from {self.name}: {e}")
            return {'maker': 0.001, 'taker': 0.001}
    
    async def start_websocket(self, symbols: List[str]):
        """Start WebSocket connection for real-time data"""
        try:
            # Get WebSocket token from KuCoin
            token_response = await self.ccxt_exchange.public_post_bullet_public()
            token = token_response['data']['token']
            endpoint = token_response['data']['instanceServers'][0]['endpoint']
            
            ws_url = f"{endpoint}?token={token}&[connectId=arbitrage_bot]"
            
            self.websocket_task = asyncio.create_task(self._websocket_handler(ws_url, symbols))
            logger.info(f"Started WebSocket for {self.name}")
            
        except Exception as e:
            logger.error(f"Error starting WebSocket for {self.name}: {e}")
    
    async def stop_websocket(self):
        """Stop WebSocket connection"""
        if self.websocket_task:
            self.websocket_task.cancel()
            
        if self.websocket:
            await self.websocket.close()
    
    async def _websocket_handler(self, ws_url: str, symbols: List[str]):
        """Handle WebSocket connection and messages"""
        try:
            async with websockets.connect(ws_url) as websocket:
                self.websocket = websocket
                
                # Subscribe to order book updates
                for symbol in symbols:
                    kucoin_symbol = symbol.replace('/', '-')
                    subscribe_msg = {
                        "id": int(time.time() * 1000),
                        "type": "subscribe",
                        "topic": f"/market/level2:{kucoin_symbol}",
                        "privateChannel": False,
                        "response": True
                    }
                    await websocket.send(json.dumps(subscribe_msg))
                
                # Listen for messages
                async for message in websocket:
                    await self._handle_websocket_message(json.loads(message))
                    
        except Exception as e:
            logger.error(f"WebSocket error for {self.name}: {e}")
    
    async def _handle_websocket_message(self, message: dict):
        """Handle incoming WebSocket messages"""
        try:
            if message.get('type') == 'message' and message.get('topic', '').startswith('/market/level2:'):
                # Parse order book update
                data = message.get('data', {})
                symbol = message['topic'].split(':')[1].replace('-', '/')
                
                # Update order book with new data
                if 'asks' in data and 'bids' in data:
                    order_book = OrderBook(
                        symbol=symbol,
                        bids=[[float(bid[0]), float(bid[1])] for bid in data['bids']],
                        asks=[[float(ask[0]), float(ask[1])] for ask in data['asks']],
                        timestamp=int(time.time() * 1000)
                    )
                    self.update_order_book(order_book)
                    
        except Exception as e:
            logger.error(f"Error handling WebSocket message for {self.name}: {e}")
