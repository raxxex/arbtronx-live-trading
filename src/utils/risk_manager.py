"""
Risk Management for High-Profit Arbitrage Strategy
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class RiskMetrics:
    """Risk metrics data structure"""
    total_exposure_usd: float
    max_position_size: float
    active_positions_count: int
    daily_loss_usd: float
    max_daily_loss_limit: float
    win_rate: float
    avg_trade_duration_minutes: float
    max_drawdown_percentage: float
    risk_score: float  # 0-100, higher is riskier


class RiskManager:
    """
    Risk management system for the high-profit arbitrage bot
    """
    
    def __init__(self):
        # Risk limits
        self.max_total_exposure_usd = 500000.0  # $500k max total exposure
        self.max_position_size_usd = 100000.0   # $100k max per position
        self.max_active_positions = 5           # Max 5 concurrent positions
        self.max_daily_loss_usd = 50000.0       # $50k max daily loss
        self.max_drawdown_percentage = 20.0     # 20% max drawdown
        self.min_win_rate = 60.0                # 60% minimum win rate
        
        # Risk tracking
        self.daily_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.max_historical_balance = 0.0
        self.current_balance = 0.0
        
        # Position tracking
        self.active_positions: Dict = {}
        self.trade_history: List = []
        
        logger.info("🛡️ Risk Manager initialized")
        logger.info(f"   Max Total Exposure: ${self.max_total_exposure_usd:,.0f}")
        logger.info(f"   Max Position Size: ${self.max_position_size_usd:,.0f}")
        logger.info(f"   Max Active Positions: {self.max_active_positions}")
        logger.info(f"   Max Daily Loss: ${self.max_daily_loss_usd:,.0f}")
    
    async def initialize(self):
        """Initialize risk manager"""
        try:
            # Load historical data if available
            await self._load_risk_data()
            logger.success("✅ Risk Manager initialized successfully")
        except Exception as e:
            logger.error(f"❌ Risk Manager initialization failed: {e}")
            raise
    
    async def _load_risk_data(self):
        """Load historical risk data"""
        # This would load from database or file
        # For now, initialize with default values
        self.current_balance = 100000.0  # $100k starting balance
        self.max_historical_balance = self.current_balance
        logger.info(f"💰 Starting balance: ${self.current_balance:,.2f}")
    
    def can_open_position(self, symbol: str, position_size_usd: float) -> tuple[bool, str]:
        """
        Check if a new position can be opened
        
        Returns:
            (can_open, reason)
        """
        
        # Check position size limit
        if position_size_usd > self.max_position_size_usd:
            return False, f"Position size ${position_size_usd:,.0f} exceeds limit ${self.max_position_size_usd:,.0f}"
        
        # Check if already have position in this symbol
        if symbol in self.active_positions:
            return False, f"Already have active position in {symbol}"
        
        # Check max active positions
        if len(self.active_positions) >= self.max_active_positions:
            return False, f"Max active positions ({self.max_active_positions}) reached"
        
        # Check total exposure
        current_exposure = self._calculate_total_exposure()
        new_total_exposure = current_exposure + position_size_usd
        
        if new_total_exposure > self.max_total_exposure_usd:
            return False, f"Total exposure ${new_total_exposure:,.0f} would exceed limit ${self.max_total_exposure_usd:,.0f}"
        
        # Check daily loss limit
        if self.daily_pnl < -self.max_daily_loss_usd:
            return False, f"Daily loss limit ${self.max_daily_loss_usd:,.0f} exceeded"
        
        # Check drawdown
        current_drawdown = self._calculate_drawdown()
        if current_drawdown > self.max_drawdown_percentage:
            return False, f"Drawdown {current_drawdown:.1f}% exceeds limit {self.max_drawdown_percentage}%"
        
        # Check win rate (if we have enough trades)
        if self.total_trades >= 10:
            win_rate = (self.winning_trades / self.total_trades) * 100
            if win_rate < self.min_win_rate:
                return False, f"Win rate {win_rate:.1f}% below minimum {self.min_win_rate}%"
        
        return True, "Position approved"
    
    def should_close_position(self, symbol: str, current_pnl_percentage: float) -> tuple[bool, str]:
        """
        Check if a position should be closed due to risk management
        
        Returns:
            (should_close, reason)
        """
        
        if symbol not in self.active_positions:
            return False, "Position not found"
        
        position = self.active_positions[symbol]
        
        # Check stop loss
        if current_pnl_percentage <= -5.0:  # 5% stop loss
            return True, f"Stop loss triggered: {current_pnl_percentage:.2f}%"
        
        # Check time-based exit (if position open too long)
        position_age = (datetime.now() - position['entry_time']).total_seconds() / 3600  # hours
        
        if position_age > 24:  # 24 hours max
            return True, f"Position held too long: {position_age:.1f} hours"
        
        # Check if daily loss limit approaching
        if self.daily_pnl < -self.max_daily_loss_usd * 0.8:  # 80% of limit
            return True, "Approaching daily loss limit"
        
        return False, "Position within risk limits"
    
    def record_position_opened(self, symbol: str, position_size_usd: float, entry_time: datetime):
        """Record that a position was opened"""
        
        self.active_positions[symbol] = {
            'size_usd': position_size_usd,
            'entry_time': entry_time,
            'unrealized_pnl': 0.0
        }
        
        logger.info(f"📈 Position opened: {symbol} (${position_size_usd:,.0f})")
        logger.info(f"   Active positions: {len(self.active_positions)}")
        logger.info(f"   Total exposure: ${self._calculate_total_exposure():,.0f}")
    
    def record_position_closed(self, symbol: str, pnl_usd: float, pnl_percentage: float):
        """Record that a position was closed"""
        
        if symbol not in self.active_positions:
            logger.warning(f"Tried to close non-existent position: {symbol}")
            return
        
        position = self.active_positions[symbol]
        
        # Update statistics
        self.total_trades += 1
        self.daily_pnl += pnl_usd
        self.current_balance += pnl_usd
        
        if pnl_usd > 0:
            self.winning_trades += 1
        
        # Update max historical balance
        if self.current_balance > self.max_historical_balance:
            self.max_historical_balance = self.current_balance
        
        # Record trade
        trade_record = {
            'symbol': symbol,
            'entry_time': position['entry_time'],
            'exit_time': datetime.now(),
            'pnl_usd': pnl_usd,
            'pnl_percentage': pnl_percentage,
            'position_size': position['size_usd']
        }
        
        self.trade_history.append(trade_record)
        
        # Remove from active positions
        del self.active_positions[symbol]
        
        # Log trade result
        result_emoji = "🟢" if pnl_usd > 0 else "🔴"
        logger.info(f"{result_emoji} Position closed: {symbol}")
        logger.info(f"   P&L: ${pnl_usd:+,.2f} ({pnl_percentage:+.2f}%)")
        logger.info(f"   Daily P&L: ${self.daily_pnl:+,.2f}")
        logger.info(f"   Win Rate: {self.get_win_rate():.1f}%")
        logger.info(f"   Balance: ${self.current_balance:,.2f}")
    
    def _calculate_total_exposure(self) -> float:
        """Calculate total USD exposure across all positions"""
        return sum(pos['size_usd'] for pos in self.active_positions.values())
    
    def _calculate_drawdown(self) -> float:
        """Calculate current drawdown percentage"""
        if self.max_historical_balance == 0:
            return 0.0
        
        drawdown = ((self.max_historical_balance - self.current_balance) / self.max_historical_balance) * 100
        return max(0.0, drawdown)
    
    def get_win_rate(self) -> float:
        """Get current win rate percentage"""
        if self.total_trades == 0:
            return 0.0
        
        return (self.winning_trades / self.total_trades) * 100
    
    def get_risk_metrics(self) -> RiskMetrics:
        """Get current risk metrics"""
        
        total_exposure = self._calculate_total_exposure()
        max_position = max([pos['size_usd'] for pos in self.active_positions.values()], default=0.0)
        drawdown = self._calculate_drawdown()
        win_rate = self.get_win_rate()
        
        # Calculate average trade duration
        if self.trade_history:
            durations = [
                (trade['exit_time'] - trade['entry_time']).total_seconds() / 60
                for trade in self.trade_history
            ]
            avg_duration = sum(durations) / len(durations)
        else:
            avg_duration = 0.0
        
        # Calculate risk score (0-100, higher is riskier)
        risk_score = 0.0
        
        # Exposure risk (0-30 points)
        exposure_ratio = total_exposure / self.max_total_exposure_usd
        risk_score += exposure_ratio * 30
        
        # Drawdown risk (0-25 points)
        drawdown_ratio = drawdown / self.max_drawdown_percentage
        risk_score += drawdown_ratio * 25
        
        # Win rate risk (0-20 points)
        if self.total_trades >= 10:
            win_rate_risk = max(0, (self.min_win_rate - win_rate) / self.min_win_rate)
            risk_score += win_rate_risk * 20
        
        # Daily loss risk (0-25 points)
        daily_loss_ratio = abs(min(0, self.daily_pnl)) / self.max_daily_loss_usd
        risk_score += daily_loss_ratio * 25
        
        return RiskMetrics(
            total_exposure_usd=total_exposure,
            max_position_size=max_position,
            active_positions_count=len(self.active_positions),
            daily_loss_usd=min(0, self.daily_pnl),
            max_daily_loss_limit=self.max_daily_loss_usd,
            win_rate=win_rate,
            avg_trade_duration_minutes=avg_duration,
            max_drawdown_percentage=drawdown,
            risk_score=min(100.0, risk_score)
        )
    
    def reset_daily_metrics(self):
        """Reset daily metrics (call at start of each day)"""
        self.daily_pnl = 0.0
        logger.info("📅 Daily risk metrics reset")
    
    def get_risk_status(self) -> Dict:
        """Get comprehensive risk status"""
        metrics = self.get_risk_metrics()
        
        # Determine risk level
        if metrics.risk_score < 30:
            risk_level = "LOW"
            risk_color = "green"
        elif metrics.risk_score < 60:
            risk_level = "MEDIUM"
            risk_color = "yellow"
        else:
            risk_level = "HIGH"
            risk_color = "red"
        
        return {
            'risk_level': risk_level,
            'risk_color': risk_color,
            'risk_score': metrics.risk_score,
            'metrics': {
                'total_exposure_usd': metrics.total_exposure_usd,
                'max_position_size': metrics.max_position_size,
                'active_positions': metrics.active_positions_count,
                'daily_pnl': self.daily_pnl,
                'win_rate': metrics.win_rate,
                'drawdown': metrics.max_drawdown_percentage,
                'balance': self.current_balance
            },
            'limits': {
                'max_exposure': self.max_total_exposure_usd,
                'max_position': self.max_position_size_usd,
                'max_positions': self.max_active_positions,
                'max_daily_loss': self.max_daily_loss_usd,
                'max_drawdown': self.max_drawdown_percentage
            }
        }
