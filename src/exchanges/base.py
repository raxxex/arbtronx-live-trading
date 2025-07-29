"""
Base exchange interface for standardized exchange operations
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
import asyncio


@dataclass
class OrderBook:
    """Order book data structure"""
    symbol: str
    bids: List[Tuple[float, float]]  # [(price, amount), ...]
    asks: List[Tuple[float, float]]  # [(price, amount), ...]
    timestamp: int
    
    @property
    def best_bid(self) -> Optional[Tuple[float, float]]:
        """Get the best bid (highest buy price)"""
        return self.bids[0] if self.bids else None
    
    @property
    def best_ask(self) -> Optional[Tuple[float, float]]:
        """Get the best ask (lowest sell price)"""
        return self.asks[0] if self.asks else None


@dataclass
class Balance:
    """Account balance data structure"""
    currency: str
    free: float
    used: float
    total: float


@dataclass
class Trade:
    """Trade execution result"""
    id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    amount: float
    price: float
    cost: float
    fee: float
    timestamp: int
    status: str  # 'open', 'closed', 'canceled'


class BaseExchange(ABC):
    """Abstract base class for exchange implementations"""
    
    def __init__(self, name: str, credentials: Dict[str, str]):
        self.name = name
        self.credentials = credentials
        self.connected = False
        self._order_books: Dict[str, OrderBook] = {}
        self._balances: Dict[str, Balance] = {}
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the exchange"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from the exchange"""
        pass
    
    @abstractmethod
    async def get_order_book(self, symbol: str) -> Optional[OrderBook]:
        """Get order book for a symbol"""
        pass
    
    @abstractmethod
    async def get_balance(self, currency: str = None) -> Dict[str, Balance]:
        """Get account balance(s)"""
        pass
    
    @abstractmethod
    async def place_market_order(self, symbol: str, side: str, amount: float) -> Trade:
        """Place a market order"""
        pass
    
    @abstractmethod
    async def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Trade:
        """Place a limit order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def get_trading_fees(self, symbol: str) -> Dict[str, float]:
        """Get trading fees for a symbol"""
        pass
    
    @abstractmethod
    async def start_websocket(self, symbols: List[str]):
        """Start WebSocket connection for real-time data"""
        pass
    
    @abstractmethod
    async def stop_websocket(self):
        """Stop WebSocket connection"""
        pass
    
    def get_cached_order_book(self, symbol: str) -> Optional[OrderBook]:
        """Get cached order book data"""
        return self._order_books.get(symbol)
    
    def get_cached_balance(self, currency: str = None) -> Dict[str, Balance]:
        """Get cached balance data"""
        if currency:
            return {currency: self._balances.get(currency)} if currency in self._balances else {}
        return self._balances.copy()
    
    def update_order_book(self, order_book: OrderBook):
        """Update cached order book"""
        self._order_books[order_book.symbol] = order_book
    
    def update_balance(self, balance: Balance):
        """Update cached balance"""
        self._balances[balance.currency] = balance
    
    @property
    def is_connected(self) -> bool:
        """Check if exchange is connected"""
        return self.connected
