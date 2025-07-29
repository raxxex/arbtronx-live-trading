#!/usr/bin/env python3
"""
Advanced Grid Trading Engine for ARBTRONX
Implements automated grid trading with dynamic adjustment and profit cycling
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
import statistics

from loguru import logger
from config import settings


class GridDirection(Enum):
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


class GridOrderStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    FILLED = "filled"
    CANCELLED = "cancelled"


@dataclass
class GridOrder:
    order_id: str
    grid_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    price: float
    amount: float
    level: int
    status: GridOrderStatus
    exchange: str
    created_at: datetime
    filled_at: Optional[datetime] = None
    filled_price: Optional[float] = None
    profit: float = 0.0


@dataclass
class GridLevel:
    level: int
    price: float
    buy_order: Optional[GridOrder] = None
    sell_order: Optional[GridOrder] = None
    is_active: bool = True


@dataclass
class GridConfiguration:
    symbol: str
    exchange: str
    center_price: float
    grid_spacing_pct: float
    levels_above: int
    levels_below: int
    order_size_usd: float
    profit_target_pct: float
    stop_loss_pct: float
    max_capital_usd: float
    use_smart_range: bool = True
    atr_period: int = 24  # Hours for ATR calculation
    volatility_multiplier: float = 1.5  # Multiplier for grid spacing

@dataclass
class MarketVolatility:
    """Market volatility analysis for smart grid spacing"""
    symbol: str
    atr_24h: float
    atr_72h: float
    std_dev_24h: float
    std_dev_72h: float
    price_range_24h: float
    volatility_score: float
    recommended_spacing_pct: float
    confidence_level: str
    last_updated: float

@dataclass
class SmartGridRange:
    """Smart grid range calculation result"""
    symbol: str
    base_spacing_pct: float
    smart_spacing_pct: float
    atr_based_spacing: float
    std_dev_based_spacing: float
    final_spacing_pct: float
    volatility_regime: str  # LOW, MEDIUM, HIGH, EXTREME
    grid_width_usd: float
    recommended_levels: int
    confidence_score: float

@dataclass
class GridLevel:
    """Individual grid level for visualization"""
    price: float
    order_type: str  # 'buy' or 'sell'
    order_id: Optional[str]
    quantity: float
    filled_quantity: float
    fill_percentage: float
    profit_potential: float
    created_at: float
    status: str  # 'pending', 'partial', 'filled', 'cancelled'
    distance_from_market: float

@dataclass
class GridVisualization:
    """Complete grid visualization data"""
    symbol: str
    current_price: float
    grid_levels: List[GridLevel]
    total_levels: int
    buy_levels: int
    sell_levels: int
    total_capital: float
    filled_capital: float
    pending_capital: float
    profit_levels: int
    loss_levels: int
    grid_range_pct: float
    last_updated: float

@dataclass
class CycleMetrics:
    """Performance metrics for a completed cycle"""
    cycle_id: str
    symbol: str
    start_time: float
    end_time: Optional[float]
    duration_hours: Optional[float]
    roi_percentage: float
    max_drawdown: float
    total_trades: int
    profit_usd: float
    starting_capital: float
    peak_capital: float
    final_capital: float
    volatility_regime: str
    grid_spacing_used: float
    is_complete: bool

@dataclass
class PerformanceAnalytics:
    """Comprehensive performance analytics"""
    symbol: str
    total_cycles: int
    completed_cycles: int
    avg_cycle_duration: float
    avg_roi_per_cycle: float
    total_profit: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    win_rate: float
    profit_factor: float
    volatility: float
    best_cycle_roi: float
    worst_cycle_roi: float
    consistency_score: float
    risk_adjusted_return: float

@dataclass
class GridStats:
    grid_id: str
    symbol: str
    total_cycles: int
    profitable_cycles: int
    total_profit: float
    total_fees: float
    net_profit: float
    win_rate: float
    avg_cycle_time: float
    active_orders: int
    created_at: datetime
    last_cycle_at: Optional[datetime] = None

@dataclass
class CompletedCycle:
    """Track completed trading cycles for auto-compounding"""
    cycle_id: str
    symbol: str
    start_time: float
    end_time: float
    initial_capital: float
    final_capital: float
    profit: float
    roi_pct: float
    phase: int
    cycle_number: int

@dataclass
class PhaseInfo:
    """Phase information for the 4-phase roadmap"""
    phase_number: int
    start_capital: float
    target_capital: float
    target_cycles: int
    target_roi_per_cycle: float
    completed_cycles: int
    current_capital: float
    is_complete: bool
    start_time: Optional[float] = None
    end_time: Optional[float] = None

class PhaseTracker:
    """Track progress through the 4-phase roadmap to $100K"""

    def __init__(self, starting_capital: float = 200.0):
        self.starting_capital = starting_capital
        self.current_phase = 1
        self.total_cycles_completed = 0
        self.total_profit = 0.0
        self.start_time = time.time()

        # Define the 4-phase roadmap
        self.phases = {
            1: PhaseInfo(1, 200, 1000, 8, 25.0, 0, starting_capital, False),
            2: PhaseInfo(2, 1000, 5000, 8, 25.0, 0, 0, False),
            3: PhaseInfo(3, 5000, 20000, 6, 25.0, 0, 0, False),
            4: PhaseInfo(4, 20000, 100000, 6, 20.0, 0, 0, False)
        }

        # Set start time for phase 1
        self.phases[1].start_time = self.start_time

    def update_capital(self, new_capital: float):
        """Update current capital and check for phase progression"""
        current_phase_info = self.phases[self.current_phase]
        current_phase_info.current_capital = new_capital

        # Check if phase is complete
        if new_capital >= current_phase_info.target_capital and not current_phase_info.is_complete:
            self._complete_phase()

    def complete_cycle(self, profit: float, roi_pct: float):
        """Record a completed cycle"""
        current_phase_info = self.phases[self.current_phase]
        current_phase_info.completed_cycles += 1
        self.total_cycles_completed += 1
        self.total_profit += profit

    def _complete_phase(self):
        """Mark current phase as complete and advance to next"""
        current_phase_info = self.phases[self.current_phase]
        current_phase_info.is_complete = True
        current_phase_info.end_time = time.time()

        if self.current_phase < 4:
            self.current_phase += 1
            next_phase_info = self.phases[self.current_phase]
            next_phase_info.start_time = time.time()
            next_phase_info.current_capital = current_phase_info.current_capital

    def get_current_phase_status(self) -> Dict:
        """Get detailed status of current phase"""
        phase_info = self.phases[self.current_phase]

        progress_pct = (phase_info.completed_cycles / phase_info.target_cycles) * 100
        capital_progress_pct = ((phase_info.current_capital - phase_info.start_capital) /
                               (phase_info.target_capital - phase_info.start_capital)) * 100

        return {
            'phase_number': self.current_phase,
            'phase_name': f"Phase {self.current_phase}",
            'start_capital': phase_info.start_capital,
            'current_capital': phase_info.current_capital,
            'target_capital': phase_info.target_capital,
            'completed_cycles': phase_info.completed_cycles,
            'target_cycles': phase_info.target_cycles,
            'progress_pct': min(progress_pct, 100),
            'capital_progress_pct': min(capital_progress_pct, 100),
            'cycles_remaining': max(0, phase_info.target_cycles - phase_info.completed_cycles),
            'capital_remaining': max(0, phase_info.target_capital - phase_info.current_capital),
            'is_complete': phase_info.is_complete,
            'target_roi_per_cycle': phase_info.target_roi_per_cycle
        }

    def get_roadmap_overview(self) -> Dict:
        """Get overview of all phases"""
        phases_status = {}
        for phase_num, phase_info in self.phases.items():
            status = "🏆 COMPLETE" if phase_info.is_complete else ("🔥 ACTIVE" if phase_num == self.current_phase else "⏳ PENDING")
            phases_status[f"phase_{phase_num}"] = {
                'phase_number': phase_num,
                'status': status,
                'start_capital': phase_info.start_capital,
                'target_capital': phase_info.target_capital,
                'current_capital': phase_info.current_capital,
                'completed_cycles': phase_info.completed_cycles,
                'target_cycles': phase_info.target_cycles,
                'is_complete': phase_info.is_complete,
                'is_active': phase_num == self.current_phase
            }

        return {
            'current_phase': self.current_phase,
            'total_cycles_completed': self.total_cycles_completed,
            'total_profit': self.total_profit,
            'starting_capital': self.starting_capital,
            'phases': phases_status
        }

    def estimate_completion_time(self) -> Dict:
        """Estimate time to reach $100K based on current performance"""
        if self.total_cycles_completed == 0:
            return {
                'estimated_days': None,
                'estimated_date': None,
                'avg_roi_per_cycle': 0,
                'cycles_remaining': 28
            }

        # Calculate average cycle performance
        elapsed_time = time.time() - self.start_time
        avg_cycle_time_days = (elapsed_time / 86400) / self.total_cycles_completed
        avg_roi = (self.total_profit / self.starting_capital) * 100 / self.total_cycles_completed

        # Calculate remaining cycles needed
        current_capital = self.phases[self.current_phase].current_capital
        cycles_remaining = 0

        for phase_num in range(self.current_phase, 5):
            if phase_num in self.phases:
                phase_info = self.phases[phase_num]
                cycles_remaining += max(0, phase_info.target_cycles - phase_info.completed_cycles)

        estimated_days = cycles_remaining * avg_cycle_time_days
        estimated_date = time.time() + (estimated_days * 86400)

        return {
            'estimated_days': round(estimated_days, 1),
            'estimated_date': estimated_date,
            'avg_roi_per_cycle': round(avg_roi, 2),
            'cycles_remaining': cycles_remaining,
            'avg_cycle_time_days': round(avg_cycle_time_days, 2)
        }


class GridTradingEngine:
    """Advanced Grid Trading Engine with dynamic adjustment"""
    
    def __init__(self, exchange_manager, risk_manager=None):
        self.exchange_manager = exchange_manager
        self.risk_manager = risk_manager
        
        # Grid management
        self.active_grids: Dict[str, Dict] = {}
        self.grid_orders: Dict[str, GridOrder] = {}
        self.grid_stats: Dict[str, GridStats] = {}
        
        # Configuration
        self.default_config = {
            'grid_spacing_pct': 0.5,
            'levels_above': 5,
            'levels_below': 5,
            'order_size_usd': 20.0,
            'profit_target_pct': 1.0,
            'stop_loss_pct': 5.0,
            'max_capital_usd': 100.0
        }
        
        # Market data
        self.price_history: Dict[str, List] = {}
        self.volatility_cache: Dict[str, float] = {}

        # Smart Grid Range System
        self.market_volatility_cache: Dict[str, MarketVolatility] = {}
        self.smart_range_cache: Dict[str, SmartGridRange] = {}
        self.volatility_update_interval = 3600  # Update every hour
        self.price_data_cache: Dict[str, List] = {}  # Store OHLCV data

        # Grid Visualization & Performance Analytics
        self.grid_visualizations: Dict[str, GridVisualization] = {}
        self.cycle_metrics: Dict[str, List[CycleMetrics]] = {}
        self.performance_analytics: Dict[str, PerformanceAnalytics] = {}
        self.active_cycles: Dict[str, CycleMetrics] = {}  # Currently running cycles
        
        # Performance tracking
        self.total_grids_created = 0
        self.total_profit = 0.0
        self.total_cycles = 0

        # Auto Compounder + Phase Tracker
        self.auto_compound_enabled = True
        self.phase_tracker = PhaseTracker()
        self.completed_cycles = []
        self.daily_pnl = {}
        self.last_rebalance_time = time.time()
        self.rebalance_threshold_pct = 10.0  # Rebalance when portfolio changes by 10%

        logger.info("🔲 Grid Trading Engine initialized with Auto-Compounder & Phase Tracker")

    async def calculate_market_volatility(self, symbol: str, exchange: str = 'binance') -> MarketVolatility:
        """Calculate comprehensive market volatility metrics for smart grid spacing"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{exchange}"
            if cache_key in self.market_volatility_cache:
                cached = self.market_volatility_cache[cache_key]
                if time.time() - cached.last_updated < self.volatility_update_interval:
                    return cached

            logger.info(f"📊 Calculating market volatility for {symbol}...")

            # Get historical price data (24h and 72h)
            price_data_24h = await self._get_historical_prices(symbol, exchange, '1h', 24)
            price_data_72h = await self._get_historical_prices(symbol, exchange, '1h', 72)

            if not price_data_24h or not price_data_72h:
                # Fallback to default volatility
                return self._create_default_volatility(symbol)

            # Calculate ATR (Average True Range)
            atr_24h = self._calculate_atr(price_data_24h)
            atr_72h = self._calculate_atr(price_data_72h)

            # Calculate standard deviation of returns
            returns_24h = self._calculate_returns(price_data_24h)
            returns_72h = self._calculate_returns(price_data_72h)

            std_dev_24h = statistics.stdev(returns_24h) if len(returns_24h) > 1 else 0.01
            std_dev_72h = statistics.stdev(returns_72h) if len(returns_72h) > 1 else 0.01

            # Calculate price range
            prices_24h = [candle['close'] for candle in price_data_24h]
            price_range_24h = (max(prices_24h) - min(prices_24h)) / min(prices_24h)

            # Calculate volatility score (0-100)
            volatility_score = min(100, (std_dev_24h * 100 + price_range_24h * 50) * 2)

            # Determine recommended spacing based on volatility
            if volatility_score < 20:
                recommended_spacing = 0.3  # Low volatility - tight grids
                confidence = "HIGH"
            elif volatility_score < 40:
                recommended_spacing = 0.5  # Medium volatility - normal grids
                confidence = "HIGH"
            elif volatility_score < 70:
                recommended_spacing = 0.8  # High volatility - wider grids
                confidence = "MEDIUM"
            else:
                recommended_spacing = 1.2  # Extreme volatility - very wide grids
                confidence = "MEDIUM"

            volatility = MarketVolatility(
                symbol=symbol,
                atr_24h=atr_24h,
                atr_72h=atr_72h,
                std_dev_24h=std_dev_24h,
                std_dev_72h=std_dev_72h,
                price_range_24h=price_range_24h,
                volatility_score=volatility_score,
                recommended_spacing_pct=recommended_spacing,
                confidence_level=confidence,
                last_updated=time.time()
            )

            # Cache the result
            self.market_volatility_cache[cache_key] = volatility

            logger.info(f"✅ Volatility calculated for {symbol}: {volatility_score:.1f} score, {recommended_spacing:.1f}% spacing")

            return volatility

        except Exception as e:
            logger.error(f"Error calculating market volatility for {symbol}: {e}")
            return self._create_default_volatility(symbol)

    async def calculate_smart_grid_range(self, symbol: str, exchange: str, base_spacing_pct: float,
                                       current_price: float) -> SmartGridRange:
        """Calculate optimal grid spacing using ATR and volatility analysis"""
        try:
            # Get market volatility
            volatility = await self.calculate_market_volatility(symbol, exchange)

            # ATR-based spacing calculation
            atr_pct = (volatility.atr_24h / current_price) * 100
            atr_based_spacing = max(0.2, min(2.0, atr_pct * 0.8))  # 80% of ATR, clamped

            # Standard deviation-based spacing
            std_dev_based_spacing = max(0.3, min(1.5, volatility.std_dev_24h * 100 * 1.2))

            # Combine methods with weights
            smart_spacing = (
                atr_based_spacing * 0.4 +  # 40% ATR
                std_dev_based_spacing * 0.3 +  # 30% Std Dev
                volatility.recommended_spacing_pct * 0.3  # 30% Volatility Score
            )

            # Apply volatility regime adjustments
            if volatility.volatility_score < 20:
                regime = "LOW"
                final_spacing = smart_spacing * 0.8  # Tighter grids for low volatility
                recommended_levels = 8  # More levels for frequent trading
            elif volatility.volatility_score < 40:
                regime = "MEDIUM"
                final_spacing = smart_spacing  # Normal spacing
                recommended_levels = 6
            elif volatility.volatility_score < 70:
                regime = "HIGH"
                final_spacing = smart_spacing * 1.2  # Wider grids for high volatility
                recommended_levels = 5
            else:
                regime = "EXTREME"
                final_spacing = smart_spacing * 1.5  # Very wide grids
                recommended_levels = 4  # Fewer levels to manage risk

            # Ensure minimum and maximum bounds
            final_spacing = max(0.2, min(2.5, final_spacing))

            # Calculate grid width in USD
            grid_width_usd = (final_spacing / 100) * current_price * recommended_levels * 2

            # Calculate confidence score
            confidence_score = 0.9 if volatility.confidence_level == "HIGH" else 0.7

            smart_range = SmartGridRange(
                symbol=symbol,
                base_spacing_pct=base_spacing_pct,
                smart_spacing_pct=smart_spacing,
                atr_based_spacing=atr_based_spacing,
                std_dev_based_spacing=std_dev_based_spacing,
                final_spacing_pct=final_spacing,
                volatility_regime=regime,
                grid_width_usd=grid_width_usd,
                recommended_levels=recommended_levels,
                confidence_score=confidence_score
            )

            # Cache the result
            cache_key = f"{symbol}_{exchange}"
            self.smart_range_cache[cache_key] = smart_range

            logger.info(f"🎯 Smart grid range for {symbol}: {final_spacing:.2f}% spacing ({regime} volatility)")

            return smart_range

        except Exception as e:
            logger.error(f"Error calculating smart grid range for {symbol}: {e}")
            # Fallback to base spacing
            return SmartGridRange(
                symbol=symbol,
                base_spacing_pct=base_spacing_pct,
                smart_spacing_pct=base_spacing_pct,
                atr_based_spacing=base_spacing_pct,
                std_dev_based_spacing=base_spacing_pct,
                final_spacing_pct=base_spacing_pct,
                volatility_regime="UNKNOWN",
                grid_width_usd=0,
                recommended_levels=5,
                confidence_score=0.5
            )

    async def _get_historical_prices(self, symbol: str, exchange: str, timeframe: str, limit: int) -> List[Dict]:
        """Get historical OHLCV data for volatility calculations"""
        try:
            if exchange in self.exchange_manager.exchanges:
                exchange_obj = self.exchange_manager.exchanges[exchange]

                # Get OHLCV data
                ohlcv = await exchange_obj.fetch_ohlcv(symbol, timeframe, limit=limit)

                if ohlcv:
                    # Convert to list of dicts for easier processing
                    candles = []
                    for candle in ohlcv:
                        candles.append({
                            'timestamp': candle[0],
                            'open': candle[1],
                            'high': candle[2],
                            'low': candle[3],
                            'close': candle[4],
                            'volume': candle[5]
                        })
                    return candles

            return []

        except Exception as e:
            logger.error(f"Error fetching historical prices for {symbol}: {e}")
            return []

    def _calculate_atr(self, price_data: List[Dict], period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            if len(price_data) < period:
                return 0.01  # Default ATR

            true_ranges = []
            for i in range(1, len(price_data)):
                current = price_data[i]
                previous = price_data[i-1]

                tr1 = current['high'] - current['low']
                tr2 = abs(current['high'] - previous['close'])
                tr3 = abs(current['low'] - previous['close'])

                true_range = max(tr1, tr2, tr3)
                true_ranges.append(true_range)

            # Calculate ATR as average of true ranges
            if true_ranges:
                atr = sum(true_ranges[-period:]) / min(period, len(true_ranges))
                return atr

            return 0.01

        except Exception as e:
            logger.error(f"Error calculating ATR: {e}")
            return 0.01

    def _calculate_returns(self, price_data: List[Dict]) -> List[float]:
        """Calculate price returns for standard deviation"""
        try:
            returns = []
            for i in range(1, len(price_data)):
                current_price = price_data[i]['close']
                previous_price = price_data[i-1]['close']

                if previous_price > 0:
                    return_pct = (current_price - previous_price) / previous_price
                    returns.append(return_pct)

            return returns

        except Exception as e:
            logger.error(f"Error calculating returns: {e}")
            return [0.01]

    def _create_default_volatility(self, symbol: str) -> MarketVolatility:
        """Create default volatility when calculation fails"""
        return MarketVolatility(
            symbol=symbol,
            atr_24h=0.01,
            atr_72h=0.01,
            std_dev_24h=0.01,
            std_dev_72h=0.01,
            price_range_24h=0.02,
            volatility_score=30.0,  # Medium volatility default
            recommended_spacing_pct=0.5,
            confidence_level="LOW",
            last_updated=time.time()
        )

    async def generate_grid_visualization(self, symbol: str, exchange: str = 'binance') -> GridVisualization:
        """Generate comprehensive grid visualization data"""
        try:
            # Get current price
            ticker = await self.exchange_manager.get_24h_ticker(exchange, symbol)
            current_price = ticker.get('last', 0) or ticker.get('close', 0)

            # Get active grid for this symbol
            grid_key = f"{symbol}_{exchange}"
            grid_levels = []

            if grid_key in self.active_grids:
                grid = self.active_grids[grid_key]

                # Generate grid levels from active grid
                for level_price, order_info in grid.buy_orders.items():
                    level = GridLevel(
                        price=level_price,
                        order_type='buy',
                        order_id=order_info.get('order_id'),
                        quantity=order_info.get('quantity', 0),
                        filled_quantity=order_info.get('filled_quantity', 0),
                        fill_percentage=order_info.get('filled_quantity', 0) / order_info.get('quantity', 1) * 100,
                        profit_potential=(current_price - level_price) / level_price * 100,
                        created_at=order_info.get('created_at', time.time()),
                        status=order_info.get('status', 'pending'),
                        distance_from_market=abs(current_price - level_price) / current_price * 100
                    )
                    grid_levels.append(level)

                for level_price, order_info in grid.sell_orders.items():
                    level = GridLevel(
                        price=level_price,
                        order_type='sell',
                        order_id=order_info.get('order_id'),
                        quantity=order_info.get('quantity', 0),
                        filled_quantity=order_info.get('filled_quantity', 0),
                        fill_percentage=order_info.get('filled_quantity', 0) / order_info.get('quantity', 1) * 100,
                        profit_potential=(level_price - current_price) / current_price * 100,
                        created_at=order_info.get('created_at', time.time()),
                        status=order_info.get('status', 'pending'),
                        distance_from_market=abs(level_price - current_price) / current_price * 100
                    )
                    grid_levels.append(level)

            # Sort levels by price (highest to lowest)
            grid_levels.sort(key=lambda x: x.price, reverse=True)

            # Calculate statistics
            buy_levels = len([l for l in grid_levels if l.order_type == 'buy'])
            sell_levels = len([l for l in grid_levels if l.order_type == 'sell'])
            total_capital = sum(l.quantity * l.price for l in grid_levels)
            filled_capital = sum(l.filled_quantity * l.price for l in grid_levels)
            pending_capital = total_capital - filled_capital
            profit_levels = len([l for l in grid_levels if l.profit_potential > 0])
            loss_levels = len([l for l in grid_levels if l.profit_potential < 0])

            # Calculate grid range
            if grid_levels:
                max_price = max(l.price for l in grid_levels)
                min_price = min(l.price for l in grid_levels)
                grid_range_pct = (max_price - min_price) / current_price * 100
            else:
                grid_range_pct = 0

            visualization = GridVisualization(
                symbol=symbol,
                current_price=current_price,
                grid_levels=grid_levels,
                total_levels=len(grid_levels),
                buy_levels=buy_levels,
                sell_levels=sell_levels,
                total_capital=total_capital,
                filled_capital=filled_capital,
                pending_capital=pending_capital,
                profit_levels=profit_levels,
                loss_levels=loss_levels,
                grid_range_pct=grid_range_pct,
                last_updated=time.time()
            )

            # Cache the visualization
            self.grid_visualizations[symbol] = visualization

            return visualization

        except Exception as e:
            logger.error(f"Error generating grid visualization for {symbol}: {e}")
            # Return empty visualization
            return GridVisualization(
                symbol=symbol,
                current_price=0,
                grid_levels=[],
                total_levels=0,
                buy_levels=0,
                sell_levels=0,
                total_capital=0,
                filled_capital=0,
                pending_capital=0,
                profit_levels=0,
                loss_levels=0,
                grid_range_pct=0,
                last_updated=time.time()
            )

    def start_cycle_tracking(self, symbol: str, starting_capital: float, grid_spacing: float, volatility_regime: str) -> str:
        """Start tracking a new trading cycle"""
        cycle_id = f"{symbol}_{int(time.time())}"

        cycle = CycleMetrics(
            cycle_id=cycle_id,
            symbol=symbol,
            start_time=time.time(),
            end_time=None,
            duration_hours=None,
            roi_percentage=0,
            max_drawdown=0,
            total_trades=0,
            profit_usd=0,
            starting_capital=starting_capital,
            peak_capital=starting_capital,
            final_capital=starting_capital,
            volatility_regime=volatility_regime,
            grid_spacing_used=grid_spacing,
            is_complete=False
        )

        self.active_cycles[cycle_id] = cycle

        logger.info(f"📊 Started cycle tracking for {symbol}: {cycle_id}")
        return cycle_id

    def update_cycle_metrics(self, cycle_id: str, current_capital: float, trades_count: int = 0):
        """Update metrics for an active cycle"""
        if cycle_id not in self.active_cycles:
            return

        cycle = self.active_cycles[cycle_id]

        # Update capital tracking
        cycle.final_capital = current_capital
        if current_capital > cycle.peak_capital:
            cycle.peak_capital = current_capital

        # Calculate current ROI
        cycle.roi_percentage = (current_capital - cycle.starting_capital) / cycle.starting_capital * 100

        # Calculate max drawdown
        if cycle.peak_capital > cycle.starting_capital:
            current_drawdown = (cycle.peak_capital - current_capital) / cycle.peak_capital * 100
            cycle.max_drawdown = max(cycle.max_drawdown, current_drawdown)

        # Update trade count
        cycle.total_trades = trades_count

        # Calculate profit
        cycle.profit_usd = current_capital - cycle.starting_capital

    def complete_cycle(self, cycle_id: str) -> Optional[CycleMetrics]:
        """Mark a cycle as complete and calculate final metrics"""
        if cycle_id not in self.active_cycles:
            return None

        cycle = self.active_cycles[cycle_id]
        cycle.end_time = time.time()
        cycle.duration_hours = (cycle.end_time - cycle.start_time) / 3600
        cycle.is_complete = True

        # Move to completed cycles
        symbol = cycle.symbol
        if symbol not in self.cycle_metrics:
            self.cycle_metrics[symbol] = []

        self.cycle_metrics[symbol].append(cycle)
        del self.active_cycles[cycle_id]

        # Update performance analytics
        self.update_performance_analytics(symbol)

        logger.info(f"✅ Completed cycle {cycle_id}: {cycle.roi_percentage:.2f}% ROI in {cycle.duration_hours:.1f}h")
        return cycle

    def update_performance_analytics(self, symbol: str):
        """Calculate comprehensive performance analytics for a symbol"""
        if symbol not in self.cycle_metrics or not self.cycle_metrics[symbol]:
            return

        cycles = self.cycle_metrics[symbol]
        completed_cycles = [c for c in cycles if c.is_complete]

        if not completed_cycles:
            return

        # Basic metrics
        total_cycles = len(cycles)
        completed_count = len(completed_cycles)

        # Duration metrics
        durations = [c.duration_hours for c in completed_cycles if c.duration_hours]
        avg_duration = statistics.mean(durations) if durations else 0

        # ROI metrics
        rois = [c.roi_percentage for c in completed_cycles]
        avg_roi = statistics.mean(rois) if rois else 0
        best_roi = max(rois) if rois else 0
        worst_roi = min(rois) if rois else 0

        # Profit metrics
        profits = [c.profit_usd for c in completed_cycles]
        total_profit = sum(profits)

        # Risk metrics
        drawdowns = [c.max_drawdown for c in completed_cycles]
        max_drawdown = max(drawdowns) if drawdowns else 0

        # Calculate Sharpe ratio (simplified)
        if rois and len(rois) > 1:
            roi_std = statistics.stdev(rois)
            sharpe_ratio = avg_roi / roi_std if roi_std > 0 else 0
        else:
            sharpe_ratio = 0

        # Calculate Sortino ratio (downside deviation)
        negative_rois = [r for r in rois if r < 0]
        if negative_rois and len(negative_rois) > 1:
            downside_std = statistics.stdev(negative_rois)
            sortino_ratio = avg_roi / abs(downside_std) if downside_std != 0 else 0
        else:
            sortino_ratio = sharpe_ratio

        # Win rate
        winning_cycles = len([r for r in rois if r > 0])
        win_rate = winning_cycles / len(rois) * 100 if rois else 0

        # Profit factor
        gross_profit = sum([p for p in profits if p > 0])
        gross_loss = abs(sum([p for p in profits if p < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Volatility
        volatility = statistics.stdev(rois) if len(rois) > 1 else 0

        # Consistency score (inverse of coefficient of variation)
        consistency_score = abs(avg_roi) / volatility if volatility > 0 else 100

        # Risk-adjusted return
        risk_adjusted_return = avg_roi / max(max_drawdown, 1)

        analytics = PerformanceAnalytics(
            symbol=symbol,
            total_cycles=total_cycles,
            completed_cycles=completed_count,
            avg_cycle_duration=avg_duration,
            avg_roi_per_cycle=avg_roi,
            total_profit=total_profit,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            volatility=volatility,
            best_cycle_roi=best_roi,
            worst_cycle_roi=worst_roi,
            consistency_score=consistency_score,
            risk_adjusted_return=risk_adjusted_return
        )

        self.performance_analytics[symbol] = analytics

        logger.info(f"📊 Updated performance analytics for {symbol}: {avg_roi:.2f}% avg ROI, {win_rate:.1f}% win rate")

    async def create_grid(self, symbol: str, exchange: str, config: Optional[Dict] = None) -> Dict:
        """Create a new grid trading setup"""
        try:
            # Generate grid ID
            grid_id = f"grid_{symbol.replace('/', '_')}_{int(time.time())}"
            
            # Get current market price
            ticker = await self.exchange_manager.get_ticker(symbol, exchange)
            current_price = ticker['last']
            
            # Merge configuration
            grid_config = self.default_config.copy()
            if config:
                grid_config.update(config)

            # Calculate smart grid range if enabled
            base_spacing = grid_config['grid_spacing_pct']
            final_spacing = base_spacing
            levels_above = grid_config['levels_above']
            levels_below = grid_config['levels_below']

            use_smart_range = grid_config.get('use_smart_range', True)
            if use_smart_range:
                logger.info(f"🧠 Calculating smart grid range for {symbol}...")
                smart_range = await self.calculate_smart_grid_range(
                    symbol, exchange, base_spacing, current_price
                )

                final_spacing = smart_range.final_spacing_pct

                # Adjust levels based on volatility regime
                if smart_range.volatility_regime == "LOW":
                    levels_above = min(8, levels_above + 2)  # More levels for low volatility
                    levels_below = min(8, levels_below + 2)
                elif smart_range.volatility_regime == "HIGH":
                    levels_above = max(3, levels_above - 1)  # Fewer levels for high volatility
                    levels_below = max(3, levels_below - 1)
                elif smart_range.volatility_regime == "EXTREME":
                    levels_above = max(2, levels_above - 2)  # Very few levels for extreme volatility
                    levels_below = max(2, levels_below - 2)

                logger.info(f"🎯 Smart grid: {base_spacing:.2f}% → {final_spacing:.2f}% spacing ({smart_range.volatility_regime} volatility)")
                logger.info(f"📊 Grid levels adjusted: {levels_above} above, {levels_below} below")

            # Create grid configuration
            config_obj = GridConfiguration(
                symbol=symbol,
                exchange=exchange,
                center_price=current_price,
                grid_spacing_pct=final_spacing,
                levels_above=levels_above,
                levels_below=levels_below,
                order_size_usd=grid_config['order_size_usd'],
                profit_target_pct=grid_config['profit_target_pct'],
                stop_loss_pct=grid_config['stop_loss_pct'],
                max_capital_usd=grid_config['max_capital_usd'],
                use_smart_range=use_smart_range
            )
            
            # Calculate grid levels
            grid_levels = await self._calculate_grid_levels(config_obj)
            
            # Create grid structure
            grid_data = {
                'grid_id': grid_id,
                'config': config_obj,
                'levels': grid_levels,
                'status': 'active',
                'created_at': datetime.now(),
                'last_update': datetime.now(),
                'total_invested': 0.0,
                'unrealized_pnl': 0.0,
                'realized_pnl': 0.0
            }
            
            # Initialize grid stats
            self.grid_stats[grid_id] = GridStats(
                grid_id=grid_id,
                symbol=symbol,
                total_cycles=0,
                profitable_cycles=0,
                total_profit=0.0,
                total_fees=0.0,
                net_profit=0.0,
                win_rate=0.0,
                avg_cycle_time=0.0,
                active_orders=0,
                created_at=datetime.now()
            )
            
            # Store grid
            self.active_grids[grid_id] = grid_data
            
            # Place initial orders
            orders_result = await self._place_initial_grid_orders(grid_id)

            if not orders_result.get('success'):
                # Remove failed grid
                del self.active_grids[grid_id]
                return {
                    'success': False,
                    'error': 'FAILED_TO_PLACE_ORDERS',
                    'message': orders_result.get('message', 'Failed to place grid orders')
                }

            self.total_grids_created += 1

            logger.info(f"🔲 REAL Grid created: {grid_id} for {symbol} on {exchange}")
            logger.info(f"   Center price: ${current_price:.4f}")
            logger.info(f"   Grid spacing: {config_obj.grid_spacing_pct}%")
            logger.info(f"   Levels: {config_obj.levels_below} below, {config_obj.levels_above} above")
            logger.info(f"   Order size: ${config_obj.order_size_usd}")
            logger.info(f"   Orders placed: {orders_result.get('orders_placed', 0)}")

            return {
                'success': True,
                'grid_id': grid_id,
                'orders_placed': orders_result.get('orders_placed', 0),
                'grid_levels': len(grid_levels),
                'capital_used': orders_result.get('capital_used', 0),
                'message': f'REAL grid created for {symbol}'
            }
            
        except Exception as e:
            logger.error(f"Error creating grid for {symbol}: {e}")
            return {
                'success': False,
                'error': 'GRID_CREATION_ERROR',
                'message': str(e)
            }
    
    async def _calculate_grid_levels(self, config: GridConfiguration) -> List[GridLevel]:
        """Calculate grid price levels"""
        levels = []
        
        # Calculate price increment
        price_increment = config.center_price * (config.grid_spacing_pct / 100)
        
        # Create levels below center price (buy orders)
        for i in range(1, config.levels_below + 1):
            level_price = config.center_price - (price_increment * i)
            levels.append(GridLevel(
                level=-i,
                price=level_price
            ))
        
        # Create levels above center price (sell orders)
        for i in range(1, config.levels_above + 1):
            level_price = config.center_price + (price_increment * i)
            levels.append(GridLevel(
                level=i,
                price=level_price
            ))
        
        # Sort by level
        levels.sort(key=lambda x: x.level)
        
        return levels
    
    async def _place_initial_grid_orders(self, grid_id: str) -> Dict:
        """Place initial grid orders"""
        try:
            grid = self.active_grids[grid_id]
            config = grid['config']
            
            orders_placed = 0
            total_capital_needed = 0
            
            for level in grid['levels']:
                if level.level < 0:  # Buy orders (below center price)
                    # Calculate order amount in base currency
                    order_amount = config.order_size_usd / level.price
                    
                    # Create buy order
                    order = await self._create_grid_order(
                        grid_id=grid_id,
                        symbol=config.symbol,
                        side='buy',
                        price=level.price,
                        amount=order_amount,
                        level=level.level,
                        exchange=config.exchange
                    )
                    
                    if order:
                        level.buy_order = order
                        orders_placed += 1
                        total_capital_needed += config.order_size_usd
                
                elif level.level > 0:  # Sell orders (above center price)
                    # For sell orders, we need to have base currency
                    # For now, we'll create them as pending and activate when we have inventory
                    order_amount = config.order_size_usd / level.price
                    
                    # Create sell order (will be activated when we have inventory)
                    order = GridOrder(
                        order_id=f"grid_sell_{grid_id}_{level.level}_{int(time.time())}",
                        grid_id=grid_id,
                        symbol=config.symbol,
                        side='sell',
                        price=level.price,
                        amount=order_amount,
                        level=level.level,
                        status=GridOrderStatus.PENDING,
                        exchange=config.exchange,
                        created_at=datetime.now()
                    )
                    
                    level.sell_order = order
                    self.grid_orders[order.order_id] = order
            
            # Update grid stats
            self.grid_stats[grid_id].active_orders = orders_placed
            grid['total_invested'] = total_capital_needed

            logger.info(f"🔲 Placed {orders_placed} initial grid orders for {grid_id}")
            logger.info(f"   Total capital allocated: ${total_capital_needed:.2f}")

            return {
                'success': True,
                'orders_placed': orders_placed,
                'capital_used': total_capital_needed
            }

        except Exception as e:
            logger.error(f"Error placing initial grid orders for {grid_id}: {e}")
            return {
                'success': False,
                'message': str(e),
                'orders_placed': 0,
                'capital_used': 0
            }
    
    async def _create_grid_order(self, grid_id: str, symbol: str, side: str, 
                                price: float, amount: float, level: int, exchange: str) -> Optional[GridOrder]:
        """Create and submit a grid order"""
        try:
            order_id = f"grid_{side}_{grid_id}_{level}_{int(time.time())}"
            
            # Create order object
            order = GridOrder(
                order_id=order_id,
                grid_id=grid_id,
                symbol=symbol,
                side=side,
                price=price,
                amount=amount,
                level=level,
                status=GridOrderStatus.PENDING,
                exchange=exchange,
                created_at=datetime.now()
            )
            
            # Submit REAL order to Binance exchange
            try:
                # Place actual order on Binance
                exchange_result = await self.exchange_manager.place_order(
                    symbol=symbol,
                    side=side,
                    order_type='limit',
                    amount=amount,
                    price=price,
                    exchange=exchange
                )

                if exchange_result and exchange_result.get('success'):
                    order.status = GridOrderStatus.ACTIVE
                    order.exchange_order_id = exchange_result.get('order_id')
                    logger.info(f"✅ REAL order placed: {order_id} - {side} {amount:.6f} {symbol} @ ${price:.4f}")
                else:
                    order.status = GridOrderStatus.FAILED
                    logger.error(f"❌ Failed to place REAL order: {order_id} - {exchange_result.get('error', 'Unknown error')}")
                    return None

            except Exception as e:
                order.status = GridOrderStatus.FAILED
                logger.error(f"❌ Exception placing REAL order {order_id}: {e}")
                return None
            
            # Store order
            self.grid_orders[order_id] = order
            
            logger.debug(f"🔲 Created grid order: {order_id} - {side} {amount:.6f} {symbol} @ ${price:.4f}")
            
            return order
            
        except Exception as e:
            logger.error(f"Error creating grid order: {e}")
            return None
    
    async def stop_all_grids(self) -> Dict:
        """Stop all active grids and cancel all orders"""
        try:
            if not self.active_grids:
                return {
                    'success': True,
                    'message': 'No active grids to stop',
                    'grids_stopped': 0,
                    'orders_canceled': 0,
                    'capital_released': 0
                }

            grids_stopped = 0
            orders_canceled = 0
            capital_released = 0

            # Stop each grid
            for grid_id in list(self.active_grids.keys()):
                grid = self.active_grids[grid_id]
                config = grid['config']

                # Cancel all active orders for this grid
                for order_id, order in list(self.grid_orders.items()):
                    if order.grid_id == grid_id and order.status == GridOrderStatus.ACTIVE:
                        try:
                            # Cancel real order on exchange
                            if hasattr(order, 'exchange_order_id') and order.exchange_order_id:
                                cancel_result = await self.exchange_manager.cancel_order(
                                    order_id=order.exchange_order_id,
                                    symbol=order.symbol,
                                    exchange=order.exchange
                                )

                                if cancel_result and cancel_result.get('success'):
                                    order.status = GridOrderStatus.CANCELLED
                                    orders_canceled += 1
                                    logger.info(f"✅ Canceled order: {order_id}")
                                else:
                                    logger.error(f"❌ Failed to cancel order: {order_id}")
                            else:
                                # Mark as cancelled if no exchange order ID
                                order.status = GridOrderStatus.CANCELLED
                                orders_canceled += 1

                        except Exception as e:
                            logger.error(f"Error canceling order {order_id}: {e}")

                # Calculate capital released
                capital_released += grid.get('total_invested', 0)

                # Remove grid
                del self.active_grids[grid_id]
                grids_stopped += 1

                logger.info(f"🛑 Stopped grid: {grid_id}")

            # Clear grid orders
            self.grid_orders.clear()

            logger.info(f"🛑 Stopped {grids_stopped} grids, canceled {orders_canceled} orders")

            return {
                'success': True,
                'grids_stopped': grids_stopped,
                'orders_canceled': orders_canceled,
                'capital_released': capital_released,
                'message': f'Successfully stopped {grids_stopped} grids'
            }

        except Exception as e:
            logger.error(f"Error stopping all grids: {e}")
            return {
                'success': False,
                'error': str(e),
                'grids_stopped': 0,
                'orders_canceled': 0,
                'capital_released': 0
            }

    async def auto_compound_and_rebalance(self, new_balance: float) -> Dict:
        """Auto-compound profits and rebalance all grids"""
        try:
            if not self.auto_compound_enabled:
                return {'success': False, 'message': 'Auto-compounding disabled'}

            logger.info(f"🔄 AUTO-COMPOUNDING: New balance ${new_balance:.2f}")

            # Update phase tracker with new capital
            self.phase_tracker.update_capital(new_balance)

            # Check if we should rebalance (significant capital change)
            time_since_rebalance = time.time() - self.last_rebalance_time
            should_rebalance = time_since_rebalance > 3600  # Rebalance every hour minimum

            if should_rebalance and len(self.active_grids) > 0:
                logger.info("🔄 REBALANCING all grids with new capital...")

                # Stop all current grids
                stop_result = await self.stop_all_grids()
                if not stop_result.get('success'):
                    return {'success': False, 'message': 'Failed to stop grids for rebalancing'}

                # Calculate new allocation per grid
                available_capital = new_balance * 0.95  # Use 95% of balance, keep 5% buffer
                num_symbols = 5  # PEPE, FLOKI, DOGE, SHIB, SUI
                capital_per_grid = available_capital / num_symbols

                # Create new grids with larger capital
                symbols = ['PEPE/USDT', 'FLOKI/USDT', 'DOGE/USDT', 'SHIB/USDT', 'SUI/USDT']
                grids_created = 0

                for symbol in symbols:
                    if capital_per_grid >= 20:  # Minimum grid size
                        config = {
                            'max_capital_usd': capital_per_grid,
                            'order_size_usd': min(capital_per_grid / 10, 50),  # 10 orders max
                            'grid_spacing_pct': 0.5,
                            'levels_above': 5,
                            'levels_below': 5
                        }

                        grid_result = await self.create_grid(symbol, 'binance', config)
                        if grid_result.get('success'):
                            grids_created += 1
                            logger.info(f"✅ Rebalanced grid for {symbol} with ${capital_per_grid:.2f}")

                self.last_rebalance_time = time.time()

                return {
                    'success': True,
                    'message': f'Auto-compounded and rebalanced {grids_created} grids',
                    'new_balance': new_balance,
                    'capital_per_grid': capital_per_grid,
                    'grids_created': grids_created,
                    'is_rebalanced': True
                }
            else:
                return {
                    'success': True,
                    'message': 'Capital updated, no rebalancing needed',
                    'new_balance': new_balance,
                    'is_rebalanced': False
                }

        except Exception as e:
            logger.error(f"Error in auto-compound and rebalance: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Auto-compound failed'
            }

    def record_completed_cycle(self, symbol: str, profit: float, initial_capital: float) -> Dict:
        """Record a completed trading cycle"""
        try:
            cycle_id = f"cycle_{symbol.replace('/', '_')}_{int(time.time())}"
            final_capital = initial_capital + profit
            roi_pct = (profit / initial_capital) * 100

            # Create completed cycle record
            completed_cycle = CompletedCycle(
                cycle_id=cycle_id,
                symbol=symbol,
                start_time=time.time() - 3600,  # Assume 1 hour cycle
                end_time=time.time(),
                initial_capital=initial_capital,
                final_capital=final_capital,
                profit=profit,
                roi_pct=roi_pct,
                phase=self.phase_tracker.current_phase,
                cycle_number=self.phase_tracker.total_cycles_completed + 1
            )

            self.completed_cycles.append(completed_cycle)

            # Update phase tracker
            self.phase_tracker.complete_cycle(profit, roi_pct)

            # Update daily P&L
            today = datetime.now().strftime('%Y-%m-%d')
            if today not in self.daily_pnl:
                self.daily_pnl[today] = 0
            self.daily_pnl[today] += profit

            logger.info(f"📊 CYCLE COMPLETED: {symbol} - ${profit:.2f} profit ({roi_pct:.1f}% ROI)")

            return {
                'success': True,
                'cycle_id': cycle_id,
                'profit': profit,
                'roi_pct': roi_pct,
                'phase': self.phase_tracker.current_phase,
                'total_cycles': self.phase_tracker.total_cycles_completed
            }

        except Exception as e:
            logger.error(f"Error recording completed cycle: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_active_grids_status(self) -> Dict:
        """Get status of all active grids"""
        try:
            active_grids_info = {}
            total_capital_used = 0
            total_active_orders = 0

            for grid_id, grid in self.active_grids.items():
                config = grid['config']

                # Count active orders for this grid
                active_orders = sum(1 for order in self.grid_orders.values()
                                  if order.grid_id == grid_id and order.status == GridOrderStatus.ACTIVE)

                capital_used = grid.get('total_invested', 0)
                total_capital_used += capital_used
                total_active_orders += active_orders

                # Get symbol from grid stats
                grid_stats = self.grid_stats.get(grid_id)
                symbol = grid_stats.symbol if grid_stats else 'Unknown'

                active_grids_info[grid_id] = {
                    'symbol': symbol,
                    'active_orders': active_orders,
                    'capital_used': capital_used,
                    'grid_spacing': config.grid_spacing_pct,
                    'levels': config.levels_below + config.levels_above,
                    'created_at': grid.get('created_at', 'Unknown'),
                    'status': grid.get('status', 'ACTIVE').upper(),
                    'unrealized_pnl': grid.get('unrealized_pnl', 0),
                    'realized_pnl': grid.get('realized_pnl', 0)
                }

            return {
                'success': True,
                'total_active_grids': len(self.active_grids),
                'total_capital_used': total_capital_used,
                'total_active_orders': total_active_orders,
                'grids': active_grids_info
            }

        except Exception as e:
            logger.error(f"Error getting active grids status: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_active_grids': 0,
                'total_capital_used': 0,
                'total_active_orders': 0,
                'grids': {}
            }

    def get_live_pnl_status(self) -> Dict:
        """Get live P&L and performance metrics"""
        try:
            # Calculate today's P&L
            today = datetime.now().strftime('%Y-%m-%d')
            today_pnl = self.daily_pnl.get(today, 0)

            # Calculate this week's P&L
            week_pnl = 0
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                week_pnl += self.daily_pnl.get(date, 0)

            # Calculate average ROI per cycle
            avg_roi = 0
            if self.completed_cycles:
                avg_roi = sum(cycle.roi_pct for cycle in self.completed_cycles) / len(self.completed_cycles)

            # Get current phase status
            phase_status = self.phase_tracker.get_current_phase_status()

            # Get completion estimate
            completion_estimate = self.phase_tracker.estimate_completion_time()

            return {
                'success': True,
                'live_pnl': {
                    'today_pnl': today_pnl,
                    'week_pnl': week_pnl,
                    'total_profit': self.phase_tracker.total_profit,
                    'total_cycles': self.phase_tracker.total_cycles_completed,
                    'avg_roi_per_cycle': round(avg_roi, 2),
                    'current_capital': phase_status['current_capital'],
                    'starting_capital': self.phase_tracker.starting_capital
                },
                'phase_progress': phase_status,
                'completion_estimate': completion_estimate,
                'recent_cycles': [
                    {
                        'symbol': cycle.symbol,
                        'profit': cycle.profit,
                        'roi_pct': cycle.roi_pct,
                        'end_time': cycle.end_time
                    } for cycle in self.completed_cycles[-5:]  # Last 5 cycles
                ]
            }

        except Exception as e:
            logger.error(f"Error getting live P&L status: {e}")
            return {
                'success': False,
                'error': str(e),
                'live_pnl': {},
                'phase_progress': {},
                'completion_estimate': {},
                'recent_cycles': []
            }

    def get_phase_roadmap_status(self) -> Dict:
        """Get complete phase roadmap status"""
        try:
            roadmap = self.phase_tracker.get_roadmap_overview()
            current_phase = self.phase_tracker.get_current_phase_status()
            completion_estimate = self.phase_tracker.estimate_completion_time()

            return {
                'success': True,
                'roadmap_overview': roadmap,
                'current_phase_detail': current_phase,
                'completion_estimate': completion_estimate,
                'auto_compound_enabled': self.auto_compound_enabled,
                'last_rebalance_time': self.last_rebalance_time,
                'total_completed_cycles': len(self.completed_cycles)
            }

        except Exception as e:
            logger.error(f"Error getting phase roadmap status: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def monitor_grids(self):
        """Monitor all active grids for order fills and profit opportunities"""
        while True:
            try:
                for grid_id in list(self.active_grids.keys()):
                    await self._monitor_grid(grid_id)

                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"Error in grid monitoring: {e}")
                await asyncio.sleep(10)
    
    async def _monitor_grid(self, grid_id: str):
        """Monitor a specific grid for order fills and adjustments"""
        try:
            grid = self.active_grids[grid_id]
            config = grid['config']
            
            # Get current market price
            ticker = await self.exchange_manager.get_ticker(config.symbol, config.exchange)
            current_price = ticker['last']
            
            # Check for filled orders and create profit cycles
            await self._check_filled_orders(grid_id, current_price)
            
            # Update unrealized PnL
            await self._update_unrealized_pnl(grid_id, current_price)
            
            # Check if grid needs adjustment
            await self._check_grid_adjustment(grid_id, current_price)
            
            # Update last update time
            grid['last_update'] = datetime.now()
            
        except Exception as e:
            logger.error(f"Error monitoring grid {grid_id}: {e}")
    
    async def _check_filled_orders(self, grid_id: str, current_price: float):
        """Check for filled orders and create profit cycles"""
        try:
            grid = self.active_grids[grid_id]
            
            for level in grid['levels']:
                # Check buy orders
                if level.buy_order and level.buy_order.status == GridOrderStatus.ACTIVE:
                    if current_price <= level.buy_order.price:
                        # Simulate order fill
                        await self._fill_order(level.buy_order, current_price)
                        
                        # Create corresponding sell order
                        await self._create_profit_sell_order(grid_id, level.buy_order)
                
                # Check sell orders
                if level.sell_order and level.sell_order.status == GridOrderStatus.ACTIVE:
                    if current_price >= level.sell_order.price:
                        # Simulate order fill
                        await self._fill_order(level.sell_order, current_price)
                        
                        # Complete profit cycle
                        await self._complete_profit_cycle(grid_id, level.sell_order)
            
        except Exception as e:
            logger.error(f"Error checking filled orders for {grid_id}: {e}")
    
    async def _fill_order(self, order: GridOrder, fill_price: float):
        """Mark an order as filled"""
        order.status = GridOrderStatus.FILLED
        order.filled_at = datetime.now()
        order.filled_price = fill_price
        
        logger.info(f"🔲 Grid order filled: {order.order_id} - {order.side} @ ${fill_price:.4f}")
    
    async def _create_profit_sell_order(self, grid_id: str, buy_order: GridOrder):
        """Create a sell order to complete the profit cycle"""
        try:
            grid = self.active_grids[grid_id]
            config = grid['config']
            
            # Calculate sell price with profit target
            profit_multiplier = 1 + (config.profit_target_pct / 100)
            sell_price = buy_order.filled_price * profit_multiplier
            
            # Create sell order
            sell_order = await self._create_grid_order(
                grid_id=grid_id,
                symbol=config.symbol,
                side='sell',
                price=sell_price,
                amount=buy_order.amount,
                level=buy_order.level + 1000,  # Mark as profit order
                exchange=config.exchange
            )
            
            if sell_order:
                # Link orders for profit tracking
                sell_order.profit = (sell_price - buy_order.filled_price) * buy_order.amount
                
                logger.info(f"🔲 Created profit sell order: {sell_order.order_id}")
                logger.info(f"   Buy: ${buy_order.filled_price:.4f} → Sell: ${sell_price:.4f}")
                logger.info(f"   Expected profit: ${sell_order.profit:.4f}")
            
        except Exception as e:
            logger.error(f"Error creating profit sell order: {e}")
    
    async def _complete_profit_cycle(self, grid_id: str, sell_order: GridOrder):
        """Complete a profit cycle and update statistics"""
        try:
            # Update grid stats
            stats = self.grid_stats[grid_id]
            stats.total_cycles += 1
            stats.total_profit += sell_order.profit
            stats.last_cycle_at = datetime.now()
            
            if sell_order.profit > 0:
                stats.profitable_cycles += 1
            
            # Calculate win rate
            stats.win_rate = (stats.profitable_cycles / stats.total_cycles) * 100
            
            # Update grid realized PnL
            grid = self.active_grids[grid_id]
            grid['realized_pnl'] += sell_order.profit
            
            # Update global stats
            self.total_profit += sell_order.profit
            self.total_cycles += 1
            
            logger.success(f"🔲 Profit cycle completed for {grid_id}")
            logger.success(f"   Cycle profit: ${sell_order.profit:.4f}")
            logger.success(f"   Total cycles: {stats.total_cycles}")
            logger.success(f"   Win rate: {stats.win_rate:.1f}%")
            
            # Create new buy order to replace the filled one
            await self._replace_filled_buy_order(grid_id, sell_order)
            
        except Exception as e:
            logger.error(f"Error completing profit cycle: {e}")
    
    async def _replace_filled_buy_order(self, grid_id: str, sell_order: GridOrder):
        """Replace a filled buy order to continue the grid"""
        try:
            grid = self.active_grids[grid_id]
            config = grid['config']
            
            # Find the original grid level for this sell order
            original_level = sell_order.level - 1000  # Remove profit order marker
            
            # Create new buy order at the same level
            for level in grid['levels']:
                if level.level == original_level:
                    new_buy_order = await self._create_grid_order(
                        grid_id=grid_id,
                        symbol=config.symbol,
                        side='buy',
                        price=level.price,
                        amount=config.order_size_usd / level.price,
                        level=level.level,
                        exchange=config.exchange
                    )
                    
                    if new_buy_order:
                        level.buy_order = new_buy_order
                        logger.info(f"🔲 Replaced buy order at level {level.level}")
                    break
            
        except Exception as e:
            logger.error(f"Error replacing filled buy order: {e}")
    
    async def get_grid_status(self, grid_id: str) -> Dict:
        """Get comprehensive status of a grid"""
        try:
            if grid_id not in self.active_grids:
                return {'error': 'Grid not found'}
            
            grid = self.active_grids[grid_id]
            stats = self.grid_stats[grid_id]
            config = grid['config']
            
            # Count active orders
            active_orders = sum(1 for order in self.grid_orders.values() 
                              if order.grid_id == grid_id and order.status == GridOrderStatus.ACTIVE)
            
            # Calculate current performance
            total_invested = grid['total_invested']
            realized_pnl = grid['realized_pnl']
            unrealized_pnl = grid['unrealized_pnl']
            total_pnl = realized_pnl + unrealized_pnl
            
            roi_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0
            
            return {
                'grid_id': grid_id,
                'symbol': config.symbol,
                'exchange': config.exchange,
                'status': grid['status'],
                'created_at': grid['created_at'].isoformat(),
                'last_update': grid['last_update'].isoformat(),
                'config': {
                    'center_price': config.center_price,
                    'grid_spacing_pct': config.grid_spacing_pct,
                    'levels_above': config.levels_above,
                    'levels_below': config.levels_below,
                    'order_size_usd': config.order_size_usd,
                    'profit_target_pct': config.profit_target_pct
                },
                'performance': {
                    'total_cycles': stats.total_cycles,
                    'profitable_cycles': stats.profitable_cycles,
                    'win_rate': stats.win_rate,
                    'total_invested': total_invested,
                    'realized_pnl': realized_pnl,
                    'unrealized_pnl': unrealized_pnl,
                    'total_pnl': total_pnl,
                    'roi_pct': roi_pct,
                    'active_orders': active_orders
                },
                'last_cycle_at': stats.last_cycle_at.isoformat() if stats.last_cycle_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting grid status: {e}")
            return {'error': str(e)}
    
    async def get_all_grids_summary(self) -> Dict:
        """Get summary of all active grids"""
        try:
            total_grids = len(self.active_grids)
            total_active_orders = sum(1 for order in self.grid_orders.values() 
                                    if order.status == GridOrderStatus.ACTIVE)
            
            total_invested = sum(grid['total_invested'] for grid in self.active_grids.values())
            total_realized_pnl = sum(grid['realized_pnl'] for grid in self.active_grids.values())
            total_unrealized_pnl = sum(grid['unrealized_pnl'] for grid in self.active_grids.values())
            
            overall_roi = ((total_realized_pnl + total_unrealized_pnl) / total_invested * 100) if total_invested > 0 else 0
            
            return {
                'total_grids': total_grids,
                'total_active_orders': total_active_orders,
                'total_cycles': self.total_cycles,
                'total_profit': self.total_profit,
                'total_invested': total_invested,
                'total_realized_pnl': total_realized_pnl,
                'total_unrealized_pnl': total_unrealized_pnl,
                'overall_roi_pct': overall_roi,
                'grids': [await self.get_grid_status(grid_id) for grid_id in self.active_grids.keys()]
            }
            
        except Exception as e:
            logger.error(f"Error getting grids summary: {e}")
            return {'error': str(e)}
    
    async def stop_grid(self, grid_id: str) -> bool:
        """Stop a specific grid and cancel all orders"""
        try:
            if grid_id not in self.active_grids:
                return False
            
            # Cancel all active orders for this grid
            cancelled_orders = 0
            for order in self.grid_orders.values():
                if order.grid_id == grid_id and order.status == GridOrderStatus.ACTIVE:
                    order.status = GridOrderStatus.CANCELLED
                    cancelled_orders += 1
            
            # Mark grid as stopped
            self.active_grids[grid_id]['status'] = 'stopped'
            
            logger.info(f"🔲 Grid stopped: {grid_id}")
            logger.info(f"   Cancelled {cancelled_orders} active orders")
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping grid {grid_id}: {e}")
            return False
    
    async def _update_unrealized_pnl(self, grid_id: str, current_price: float):
        """Update unrealized PnL for a grid"""
        try:
            # This would calculate unrealized PnL based on current positions
            # For now, we'll set it to 0 as we're focusing on realized profits
            self.active_grids[grid_id]['unrealized_pnl'] = 0.0
            
        except Exception as e:
            logger.error(f"Error updating unrealized PnL: {e}")
    
    async def _check_grid_adjustment(self, grid_id: str, current_price: float):
        """Check if grid needs adjustment based on market movement"""
        try:
            grid = self.active_grids[grid_id]
            config = grid['config']
            
            # Calculate price deviation from center
            price_deviation_pct = abs(current_price - config.center_price) / config.center_price * 100
            
            # If price moved more than 5%, consider grid adjustment
            if price_deviation_pct > 5.0:
                logger.info(f"🔲 Grid {grid_id} may need adjustment - price deviation: {price_deviation_pct:.2f}%")
                # Grid adjustment logic would go here
            
        except Exception as e:
            logger.error(f"Error checking grid adjustment: {e}")
