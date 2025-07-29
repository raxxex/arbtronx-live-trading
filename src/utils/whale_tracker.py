"""
Whale Tracker for detecting large orders and whale activity
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class WhaleOrder:
    """Whale order data structure"""
    symbol: str
    exchange: str
    side: str  # 'buy' or 'sell'
    price: float
    quantity: float
    value_usd: float
    timestamp: datetime
    order_type: str  # 'market', 'limit'


@dataclass
class WhaleActivity:
    """Whale activity summary"""
    symbol: str
    total_buy_volume: float
    total_sell_volume: float
    net_volume: float  # buy - sell
    large_orders_count: int
    avg_order_size: float
    timestamp: datetime


class WhaleTracker:
    """
    Tracks whale activity and large orders across exchanges
    """
    
    def __init__(self, whale_threshold: float = 20000.0):
        self.whale_threshold = whale_threshold  # $20k default
        self.whale_orders: Dict[str, List[WhaleOrder]] = {}
        self.activity_cache: Dict[str, WhaleActivity] = {}
        self.last_scan_time: Dict[str, datetime] = {}
        
        logger.info(f"🐋 Whale Tracker initialized with ${whale_threshold:,.0f} threshold")
    
    async def detect_large_orders(self, exchange: str, symbol: str, 
                                threshold: float, side: Optional[str] = None) -> bool:
        """
        Detect large orders in the order book
        
        Args:
            exchange: Exchange name ('binance', 'okx')
            symbol: Trading pair symbol
            threshold: USD threshold for whale orders
            side: 'buy', 'sell', or None for both sides
            
        Returns:
            True if whale orders detected
        """
        try:
            # This would integrate with exchange order book data
            # For now, implementing a simulation
            
            # Get order book depth
            order_book = await self._get_order_book_depth(exchange, symbol)
            
            if not order_book:
                return False
            
            whale_orders_found = []
            
            # Check buy orders
            if side in [None, 'buy'] and order_book.get('bids'):
                for price, quantity in order_book['bids'][:20]:  # Check top 20 levels
                    value_usd = price * quantity
                    if value_usd >= threshold:
                        whale_order = WhaleOrder(
                            symbol=symbol,
                            exchange=exchange,
                            side='buy',
                            price=price,
                            quantity=quantity,
                            value_usd=value_usd,
                            timestamp=datetime.now(),
                            order_type='limit'
                        )
                        whale_orders_found.append(whale_order)
            
            # Check sell orders
            if side in [None, 'sell'] and order_book.get('asks'):
                for price, quantity in order_book['asks'][:20]:  # Check top 20 levels
                    value_usd = price * quantity
                    if value_usd >= threshold:
                        whale_order = WhaleOrder(
                            symbol=symbol,
                            exchange=exchange,
                            side='sell',
                            price=price,
                            quantity=quantity,
                            value_usd=value_usd,
                            timestamp=datetime.now(),
                            order_type='limit'
                        )
                        whale_orders_found.append(whale_order)
            
            # Store whale orders
            if whale_orders_found:
                if symbol not in self.whale_orders:
                    self.whale_orders[symbol] = []
                
                self.whale_orders[symbol].extend(whale_orders_found)
                
                # Keep only recent orders (last 1 hour)
                cutoff_time = datetime.now() - timedelta(hours=1)
                self.whale_orders[symbol] = [
                    order for order in self.whale_orders[symbol] 
                    if order.timestamp > cutoff_time
                ]
                
                # Log whale activity
                for order in whale_orders_found:
                    logger.info(f"🐋 WHALE ORDER DETECTED: {symbol}")
                    logger.info(f"   Exchange: {exchange}")
                    logger.info(f"   Side: {order.side.upper()}")
                    logger.info(f"   Size: ${order.value_usd:,.0f} ({order.quantity:.2f} @ ${order.price:.6f})")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting whale orders for {symbol} on {exchange}: {e}")
            return False
    
    async def _get_order_book_depth(self, exchange: str, symbol: str) -> Optional[Dict]:
        """
        Get order book depth from exchange
        This is a placeholder - would integrate with actual exchange APIs
        """
        try:
            # Simulate order book data
            # In real implementation, this would call exchange APIs
            
            import random
            
            # Generate simulated order book
            base_price = 1.0  # Base price for simulation
            
            bids = []
            asks = []
            
            # Generate bids (buy orders)
            for i in range(50):
                price = base_price * (1 - (i * 0.001))  # Decreasing prices
                quantity = random.uniform(1000, 50000)  # Random quantity
                bids.append([price, quantity])
            
            # Generate asks (sell orders)
            for i in range(50):
                price = base_price * (1 + (i * 0.001))  # Increasing prices
                quantity = random.uniform(1000, 50000)  # Random quantity
                asks.append([price, quantity])
            
            # Occasionally add whale orders
            if random.random() < 0.1:  # 10% chance of whale order
                whale_quantity = random.uniform(50000, 200000)
                if random.random() < 0.5:
                    # Add whale bid
                    bids[0][1] = whale_quantity
                else:
                    # Add whale ask
                    asks[0][1] = whale_quantity
            
            return {
                'bids': bids,
                'asks': asks,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting order book for {symbol} on {exchange}: {e}")
            return None
    
    def get_whale_activity_summary(self, symbol: str, 
                                 time_window: int = 300) -> Optional[WhaleActivity]:
        """
        Get whale activity summary for a symbol
        
        Args:
            symbol: Trading pair symbol
            time_window: Time window in seconds (default 5 minutes)
            
        Returns:
            WhaleActivity summary or None
        """
        try:
            if symbol not in self.whale_orders:
                return None
            
            # Filter orders within time window
            cutoff_time = datetime.now() - timedelta(seconds=time_window)
            recent_orders = [
                order for order in self.whale_orders[symbol]
                if order.timestamp > cutoff_time
            ]
            
            if not recent_orders:
                return None
            
            # Calculate activity metrics
            buy_orders = [order for order in recent_orders if order.side == 'buy']
            sell_orders = [order for order in recent_orders if order.side == 'sell']
            
            total_buy_volume = sum(order.value_usd for order in buy_orders)
            total_sell_volume = sum(order.value_usd for order in sell_orders)
            net_volume = total_buy_volume - total_sell_volume
            
            avg_order_size = sum(order.value_usd for order in recent_orders) / len(recent_orders)
            
            activity = WhaleActivity(
                symbol=symbol,
                total_buy_volume=total_buy_volume,
                total_sell_volume=total_sell_volume,
                net_volume=net_volume,
                large_orders_count=len(recent_orders),
                avg_order_size=avg_order_size,
                timestamp=datetime.now()
            )
            
            # Cache the activity
            self.activity_cache[symbol] = activity
            
            return activity
            
        except Exception as e:
            logger.error(f"Error getting whale activity for {symbol}: {e}")
            return None
    
    def is_whale_buying(self, symbol: str, time_window: int = 300) -> bool:
        """
        Check if whales are predominantly buying
        
        Args:
            symbol: Trading pair symbol
            time_window: Time window in seconds
            
        Returns:
            True if net whale buying detected
        """
        activity = self.get_whale_activity_summary(symbol, time_window)
        
        if not activity:
            return False
        
        # Consider whale buying if net volume > $50k and buy volume > sell volume
        return activity.net_volume > 50000 and activity.total_buy_volume > activity.total_sell_volume
    
    def is_whale_selling(self, symbol: str, time_window: int = 300) -> bool:
        """
        Check if whales are predominantly selling
        """
        activity = self.get_whale_activity_summary(symbol, time_window)
        
        if not activity:
            return False
        
        # Consider whale selling if net volume < -$50k and sell volume > buy volume
        return activity.net_volume < -50000 and activity.total_sell_volume > activity.total_buy_volume
    
    def get_whale_sentiment(self, symbol: str, time_window: int = 300) -> str:
        """
        Get overall whale sentiment for a symbol
        
        Returns:
            'bullish', 'bearish', or 'neutral'
        """
        activity = self.get_whale_activity_summary(symbol, time_window)
        
        if not activity:
            return 'neutral'
        
        # Calculate sentiment based on net volume
        if activity.net_volume > 50000:
            return 'bullish'
        elif activity.net_volume < -50000:
            return 'bearish'
        else:
            return 'neutral'
    
    def get_recent_whale_orders(self, symbol: str, limit: int = 10) -> List[WhaleOrder]:
        """
        Get recent whale orders for a symbol
        
        Args:
            symbol: Trading pair symbol
            limit: Maximum number of orders to return
            
        Returns:
            List of recent whale orders
        """
        if symbol not in self.whale_orders:
            return []
        
        # Sort by timestamp (most recent first)
        sorted_orders = sorted(
            self.whale_orders[symbol],
            key=lambda x: x.timestamp,
            reverse=True
        )
        
        return sorted_orders[:limit]
    
    def clear_old_data(self, max_age_hours: int = 24):
        """
        Clear old whale order data
        
        Args:
            max_age_hours: Maximum age of data to keep in hours
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        for symbol in list(self.whale_orders.keys()):
            self.whale_orders[symbol] = [
                order for order in self.whale_orders[symbol]
                if order.timestamp > cutoff_time
            ]
            
            # Remove empty entries
            if not self.whale_orders[symbol]:
                del self.whale_orders[symbol]
        
        # Clear old activity cache
        for symbol in list(self.activity_cache.keys()):
            if self.activity_cache[symbol].timestamp < cutoff_time:
                del self.activity_cache[symbol]
        
        logger.debug(f"Cleared whale data older than {max_age_hours} hours")
    
    def get_tracker_stats(self) -> Dict:
        """
        Get whale tracker statistics
        
        Returns:
            Dictionary with tracker statistics
        """
        total_orders = sum(len(orders) for orders in self.whale_orders.values())
        active_symbols = len(self.whale_orders)
        
        recent_activity = {}
        for symbol, orders in self.whale_orders.items():
            recent_orders = [
                order for order in orders
                if order.timestamp > datetime.now() - timedelta(minutes=15)
            ]
            if recent_orders:
                recent_activity[symbol] = len(recent_orders)
        
        return {
            'whale_threshold': self.whale_threshold,
            'total_tracked_orders': total_orders,
            'active_symbols': active_symbols,
            'recent_activity_15min': recent_activity,
            'symbols_with_data': list(self.whale_orders.keys())
        }
