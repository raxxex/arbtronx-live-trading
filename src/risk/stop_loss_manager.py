#!/usr/bin/env python3
"""
Advanced Stop-Loss and Take-Profit Management System
Features: Dynamic stops, trailing stops, ML-enhanced levels, time-based exits
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger


class StopType(Enum):
    """Stop-loss types"""
    FIXED = "fixed"
    TRAILING = "trailing"
    VOLATILITY_BASED = "volatility_based"
    ML_ENHANCED = "ml_enhanced"
    TIME_BASED = "time_based"


class OrderStatus(Enum):
    """Order status"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class StopLossOrder:
    """Stop-loss order definition"""
    order_id: str
    symbol: str
    position_id: str
    stop_type: StopType
    stop_price: float
    original_stop: float
    take_profit: Optional[float]
    entry_price: float
    position_size: float
    is_long: bool
    created_at: datetime
    expires_at: Optional[datetime]
    status: OrderStatus
    trail_amount: Optional[float] = None
    trail_percent: Optional[float] = None
    max_favorable_price: Optional[float] = None
    trigger_count: int = 0
    last_update: datetime = None


@dataclass
class StopLossConfig:
    """Stop-loss configuration"""
    default_stop_pct: float = 0.02  # 2% default stop
    default_tp_ratio: float = 2.0   # 2:1 risk/reward
    trailing_trigger_pct: float = 0.01  # Start trailing at 1% profit
    trailing_step_pct: float = 0.005    # Trail by 0.5%
    max_position_time: int = 3600       # 1 hour max position time
    volatility_multiplier: float = 1.5  # Volatility adjustment factor
    ml_confidence_threshold: float = 0.7 # ML confidence threshold


class StopLossManager:
    """Advanced stop-loss and take-profit management"""
    
    def __init__(self):
        self.config = StopLossConfig()
        self.active_stops: Dict[str, StopLossOrder] = {}
        self.stop_history: List[StopLossOrder] = []
        self.volatility_cache: Dict[str, float] = {}
        self.ml_integration = None
        self.price_feeds: Dict[str, float] = {}
        
        logger.info("🛡️ Advanced Stop-Loss Manager initialized")
    
    def set_ml_integration(self, ml_integration):
        """Set ML integration for enhanced stop management"""
        self.ml_integration = ml_integration
        logger.info("🧠 ML integration enabled for stop-loss management")
    
    async def create_stop_loss(self, 
                              position_id: str,
                              symbol: str,
                              entry_price: float,
                              position_size: float,
                              is_long: bool,
                              stop_type: StopType = StopType.ML_ENHANCED) -> str:
        """Create a new stop-loss order"""
        try:
            order_id = f"stop_{position_id}_{int(time.time())}"
            
            # Calculate stop-loss and take-profit levels
            stop_price, take_profit = await self._calculate_stop_levels(
                symbol, entry_price, is_long, stop_type
            )
            
            # Create stop-loss order
            stop_order = StopLossOrder(
                order_id=order_id,
                symbol=symbol,
                position_id=position_id,
                stop_type=stop_type,
                stop_price=stop_price,
                original_stop=stop_price,
                take_profit=take_profit,
                entry_price=entry_price,
                position_size=position_size,
                is_long=is_long,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=self.config.max_position_time),
                status=OrderStatus.ACTIVE,
                last_update=datetime.now()
            )
            
            # Set trailing parameters for trailing stops
            if stop_type == StopType.TRAILING:
                stop_order.trail_percent = self.config.trailing_step_pct
                stop_order.max_favorable_price = entry_price
            
            self.active_stops[order_id] = stop_order
            
            logger.info(f"🛡️ Stop-loss created for {symbol}: Stop={stop_price:.6f}, TP={take_profit:.6f}")
            
            return order_id
            
        except Exception as e:
            logger.error(f"Error creating stop-loss: {e}")
            raise
    
    async def update_stops(self, price_updates: Dict[str, float]) -> List[Dict[str, Any]]:
        """Update all stop-loss orders with new prices"""
        triggered_orders = []
        
        try:
            # Update price feeds
            self.price_feeds.update(price_updates)
            
            for order_id, stop_order in list(self.active_stops.items()):
                if stop_order.symbol not in price_updates:
                    continue
                
                current_price = price_updates[stop_order.symbol]
                
                # Check for stop-loss trigger
                if await self._check_stop_trigger(stop_order, current_price):
                    triggered_orders.append({
                        'action': 'stop_loss_triggered',
                        'order_id': order_id,
                        'position_id': stop_order.position_id,
                        'symbol': stop_order.symbol,
                        'trigger_price': current_price,
                        'stop_price': stop_order.stop_price,
                        'pnl': self._calculate_pnl(stop_order, current_price)
                    })
                    
                    stop_order.status = OrderStatus.TRIGGERED
                    self._move_to_history(order_id)
                    continue
                
                # Check for take-profit trigger
                if await self._check_take_profit_trigger(stop_order, current_price):
                    triggered_orders.append({
                        'action': 'take_profit_triggered',
                        'order_id': order_id,
                        'position_id': stop_order.position_id,
                        'symbol': stop_order.symbol,
                        'trigger_price': current_price,
                        'take_profit': stop_order.take_profit,
                        'pnl': self._calculate_pnl(stop_order, current_price)
                    })
                    
                    stop_order.status = OrderStatus.TRIGGERED
                    self._move_to_history(order_id)
                    continue
                
                # Update trailing stops
                if stop_order.stop_type == StopType.TRAILING:
                    await self._update_trailing_stop(stop_order, current_price)
                
                # Check for time-based exit
                if await self._check_time_exit(stop_order):
                    triggered_orders.append({
                        'action': 'time_exit_triggered',
                        'order_id': order_id,
                        'position_id': stop_order.position_id,
                        'symbol': stop_order.symbol,
                        'current_price': current_price,
                        'reason': 'max_time_exceeded'
                    })
                    
                    stop_order.status = OrderStatus.EXPIRED
                    self._move_to_history(order_id)
                    continue
                
                # Update ML-enhanced stops
                if stop_order.stop_type == StopType.ML_ENHANCED:
                    await self._update_ml_stop(stop_order, current_price)
                
                stop_order.last_update = datetime.now()
            
            if triggered_orders:
                logger.info(f"🚨 {len(triggered_orders)} stop orders triggered")
            
            return triggered_orders
            
        except Exception as e:
            logger.error(f"Error updating stops: {e}")
            return []
    
    async def _calculate_stop_levels(self, 
                                   symbol: str, 
                                   entry_price: float, 
                                   is_long: bool, 
                                   stop_type: StopType) -> Tuple[float, float]:
        """Calculate stop-loss and take-profit levels"""
        try:
            # Get volatility for the symbol
            volatility = self.volatility_cache.get(symbol, 0.02)
            
            # Base stop distance
            base_stop_pct = self.config.default_stop_pct
            
            # Adjust based on stop type
            if stop_type == StopType.VOLATILITY_BASED:
                stop_pct = base_stop_pct * (1 + volatility * self.config.volatility_multiplier)
            elif stop_type == StopType.ML_ENHANCED:
                stop_pct = await self._get_ml_stop_distance(symbol, base_stop_pct)
            else:
                stop_pct = base_stop_pct
            
            # Calculate stop-loss price
            if is_long:
                stop_price = entry_price * (1 - stop_pct)
                take_profit = entry_price * (1 + stop_pct * self.config.default_tp_ratio)
            else:
                stop_price = entry_price * (1 + stop_pct)
                take_profit = entry_price * (1 - stop_pct * self.config.default_tp_ratio)
            
            return stop_price, take_profit
            
        except Exception as e:
            logger.error(f"Error calculating stop levels: {e}")
            # Fallback values
            if is_long:
                return entry_price * 0.98, entry_price * 1.04
            else:
                return entry_price * 1.02, entry_price * 0.96
    
    async def _get_ml_stop_distance(self, symbol: str, base_stop_pct: float) -> float:
        """Get ML-enhanced stop distance"""
        try:
            if not self.ml_integration:
                return base_stop_pct
            
            prediction = await self.ml_integration.get_ml_prediction(symbol)
            if not prediction:
                return base_stop_pct
            
            # Adjust stop based on ML confidence and volatility forecast
            confidence = prediction.confidence_score / 100.0
            volatility_forecast = prediction.volatility_forecast
            
            # Higher confidence = tighter stops, higher volatility = wider stops
            confidence_adjustment = 0.8 + (confidence * 0.4)  # 0.8 to 1.2
            volatility_adjustment = 1.0 + (volatility_forecast * 2.0)  # 1.0 to 3.0
            
            adjusted_stop = base_stop_pct * confidence_adjustment * volatility_adjustment
            
            # Clamp to reasonable range
            return max(0.005, min(adjusted_stop, 0.05))  # 0.5% to 5%
            
        except Exception as e:
            logger.error(f"Error getting ML stop distance: {e}")
            return base_stop_pct
    
    async def _check_stop_trigger(self, stop_order: StopLossOrder, current_price: float) -> bool:
        """Check if stop-loss should be triggered"""
        try:
            if stop_order.is_long:
                return current_price <= stop_order.stop_price
            else:
                return current_price >= stop_order.stop_price
        except Exception:
            return False
    
    async def _check_take_profit_trigger(self, stop_order: StopLossOrder, current_price: float) -> bool:
        """Check if take-profit should be triggered"""
        try:
            if not stop_order.take_profit:
                return False
            
            if stop_order.is_long:
                return current_price >= stop_order.take_profit
            else:
                return current_price <= stop_order.take_profit
        except Exception:
            return False
    
    async def _update_trailing_stop(self, stop_order: StopLossOrder, current_price: float):
        """Update trailing stop-loss"""
        try:
            if not stop_order.trail_percent:
                return
            
            # Check if we should start trailing
            profit_pct = self._calculate_profit_pct(stop_order, current_price)
            if profit_pct < self.config.trailing_trigger_pct:
                return
            
            # Update max favorable price
            if stop_order.is_long:
                if current_price > stop_order.max_favorable_price:
                    stop_order.max_favorable_price = current_price
                    # Update trailing stop
                    new_stop = current_price * (1 - stop_order.trail_percent)
                    if new_stop > stop_order.stop_price:
                        stop_order.stop_price = new_stop
                        logger.debug(f"📈 Trailing stop updated for {stop_order.symbol}: {new_stop:.6f}")
            else:
                if current_price < stop_order.max_favorable_price:
                    stop_order.max_favorable_price = current_price
                    # Update trailing stop
                    new_stop = current_price * (1 + stop_order.trail_percent)
                    if new_stop < stop_order.stop_price:
                        stop_order.stop_price = new_stop
                        logger.debug(f"📉 Trailing stop updated for {stop_order.symbol}: {new_stop:.6f}")
                        
        except Exception as e:
            logger.error(f"Error updating trailing stop: {e}")
    
    async def _update_ml_stop(self, stop_order: StopLossOrder, current_price: float):
        """Update ML-enhanced stop-loss"""
        try:
            if not self.ml_integration:
                return
            
            # Get fresh ML prediction
            prediction = await self.ml_integration.get_ml_prediction(stop_order.symbol)
            if not prediction:
                return
            
            # Only adjust if confidence is high
            if prediction.confidence_score < self.config.ml_confidence_threshold * 100:
                return
            
            # Calculate new stop based on ML prediction
            new_stop_pct = await self._get_ml_stop_distance(stop_order.symbol, self.config.default_stop_pct)
            
            if stop_order.is_long:
                new_stop = current_price * (1 - new_stop_pct)
                # Only move stop up (tighter)
                if new_stop > stop_order.stop_price:
                    stop_order.stop_price = new_stop
                    logger.debug(f"🧠 ML stop updated for {stop_order.symbol}: {new_stop:.6f}")
            else:
                new_stop = current_price * (1 + new_stop_pct)
                # Only move stop down (tighter)
                if new_stop < stop_order.stop_price:
                    stop_order.stop_price = new_stop
                    logger.debug(f"🧠 ML stop updated for {stop_order.symbol}: {new_stop:.6f}")
                    
        except Exception as e:
            logger.error(f"Error updating ML stop: {e}")
    
    async def _check_time_exit(self, stop_order: StopLossOrder) -> bool:
        """Check if position should be closed due to time"""
        try:
            if not stop_order.expires_at:
                return False
            
            return datetime.now() >= stop_order.expires_at
        except Exception:
            return False
    
    def _calculate_pnl(self, stop_order: StopLossOrder, current_price: float) -> float:
        """Calculate P&L for position"""
        try:
            if stop_order.is_long:
                return (current_price - stop_order.entry_price) * stop_order.position_size
            else:
                return (stop_order.entry_price - current_price) * stop_order.position_size
        except Exception:
            return 0.0
    
    def _calculate_profit_pct(self, stop_order: StopLossOrder, current_price: float) -> float:
        """Calculate profit percentage"""
        try:
            if stop_order.is_long:
                return (current_price - stop_order.entry_price) / stop_order.entry_price
            else:
                return (stop_order.entry_price - current_price) / stop_order.entry_price
        except Exception:
            return 0.0
    
    def _move_to_history(self, order_id: str):
        """Move order to history"""
        if order_id in self.active_stops:
            self.stop_history.append(self.active_stops[order_id])
            del self.active_stops[order_id]
            
            # Keep only last 1000 entries
            if len(self.stop_history) > 1000:
                self.stop_history = self.stop_history[-1000:]
    
    def cancel_stop(self, order_id: str) -> bool:
        """Cancel a stop-loss order"""
        try:
            if order_id in self.active_stops:
                self.active_stops[order_id].status = OrderStatus.CANCELLED
                self._move_to_history(order_id)
                logger.info(f"🚫 Stop-loss cancelled: {order_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cancelling stop: {e}")
            return False
    
    def get_stop_summary(self) -> Dict[str, Any]:
        """Get stop-loss summary"""
        try:
            active_count = len(self.active_stops)
            triggered_today = len([
                s for s in self.stop_history 
                if s.status == OrderStatus.TRIGGERED and 
                s.last_update and s.last_update.date() == datetime.now().date()
            ])
            
            return {
                'active_stops': active_count,
                'triggered_today': triggered_today,
                'total_history': len(self.stop_history),
                'stop_types': {
                    stop_type.value: len([s for s in self.active_stops.values() if s.stop_type == stop_type])
                    for stop_type in StopType
                },
                'config': {
                    'default_stop_pct': self.config.default_stop_pct,
                    'default_tp_ratio': self.config.default_tp_ratio,
                    'max_position_time': self.config.max_position_time
                }
            }
        except Exception as e:
            logger.error(f"Error getting stop summary: {e}")
            return {'error': str(e)}
