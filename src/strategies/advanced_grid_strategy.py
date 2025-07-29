#!/usr/bin/env python3
"""
Advanced Grid Trading Strategy with Dynamic Adjustment
Implements intelligent grid management with market condition adaptation
"""

import asyncio
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from loguru import logger
from .grid_trading_engine import GridTradingEngine, GridConfiguration


class MarketCondition(Enum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


@dataclass
class MarketAnalysis:
    condition: MarketCondition
    volatility: float
    trend_strength: float
    volume_ratio: float
    price_change_24h: float
    recommended_action: str


@dataclass
class GridPerformanceMetrics:
    grid_id: str
    cycles_per_hour: float
    profit_rate: float
    efficiency_score: float
    market_capture_rate: float
    risk_score: float


class AdvancedGridStrategy:
    """Advanced Grid Trading Strategy with intelligent market adaptation"""
    
    def __init__(self, grid_engine: GridTradingEngine, exchange_manager):
        self.grid_engine = grid_engine
        self.exchange_manager = exchange_manager
        
        # Market analysis
        self.market_analyzer = MarketAnalyzer(exchange_manager)
        self.performance_tracker = GridPerformanceTracker()
        
        # Strategy parameters
        self.min_volatility_threshold = 0.02  # 2% minimum volatility
        self.max_volatility_threshold = 0.15  # 15% maximum volatility
        self.trend_threshold = 0.05  # 5% trend detection
        self.efficiency_threshold = 0.7  # 70% minimum efficiency
        
        # Dynamic adjustment settings
        self.adjustment_interval = 300  # 5 minutes
        self.last_adjustment = {}
        
        logger.info("🧠 Advanced Grid Strategy initialized")
    
    async def create_intelligent_grid(self, symbol: str, exchange: str, 
                                    capital_allocation: float = 100.0) -> Optional[str]:
        """Create a grid with intelligent configuration based on market analysis"""
        try:
            # Analyze market conditions
            analysis = await self.market_analyzer.analyze_market(symbol, exchange)
            
            # Generate optimal configuration
            config = await self._generate_optimal_config(symbol, analysis, capital_allocation)
            
            if not config:
                logger.warning(f"Market conditions not suitable for grid trading: {symbol}")
                return None
            
            # Create the grid
            grid_id = await self.grid_engine.create_grid(symbol, exchange, config)
            
            # Start monitoring this grid
            self.last_adjustment[grid_id] = time.time()
            
            logger.info(f"🧠 Intelligent grid created: {grid_id}")
            logger.info(f"   Market condition: {analysis.condition.value}")
            logger.info(f"   Volatility: {analysis.volatility:.2f}%")
            logger.info(f"   Grid spacing: {config['grid_spacing_pct']}%")
            logger.info(f"   Order size: ${config['order_size_usd']}")
            
            return grid_id
            
        except Exception as e:
            logger.error(f"Error creating intelligent grid: {e}")
            return None
    
    async def _generate_optimal_config(self, symbol: str, analysis: MarketAnalysis, 
                                     capital: float) -> Optional[Dict]:
        """Generate optimal grid configuration based on market analysis"""
        try:
            # Base configuration
            config = {
                'grid_spacing_pct': 0.5,
                'levels_above': 5,
                'levels_below': 5,
                'order_size_usd': 20.0,
                'profit_target_pct': 1.0,
                'stop_loss_pct': 5.0,
                'max_capital_usd': capital
            }
            
            # Adjust based on market conditions
            if analysis.condition == MarketCondition.HIGH_VOLATILITY:
                # Wider spacing for high volatility
                config['grid_spacing_pct'] = min(1.0, analysis.volatility * 10)
                config['profit_target_pct'] = 1.5
                config['levels_above'] = 4
                config['levels_below'] = 4
                
            elif analysis.condition == MarketCondition.LOW_VOLATILITY:
                # Tighter spacing for low volatility
                config['grid_spacing_pct'] = max(0.3, analysis.volatility * 5)
                config['profit_target_pct'] = 0.8
                config['levels_above'] = 6
                config['levels_below'] = 6
                
            elif analysis.condition == MarketCondition.TRENDING_UP:
                # More buy levels for uptrend
                config['levels_below'] = 7
                config['levels_above'] = 3
                config['profit_target_pct'] = 1.2
                
            elif analysis.condition == MarketCondition.TRENDING_DOWN:
                # More sell levels for downtrend
                config['levels_above'] = 7
                config['levels_below'] = 3
                config['profit_target_pct'] = 1.2
                
            # Adjust order size based on capital and levels
            total_levels = config['levels_above'] + config['levels_below']
            config['order_size_usd'] = min(20.0, capital / total_levels)
            
            # Validate configuration
            if config['grid_spacing_pct'] < 0.2 or config['grid_spacing_pct'] > 2.0:
                logger.warning(f"Grid spacing out of range: {config['grid_spacing_pct']}%")
                return None
            
            return config
            
        except Exception as e:
            logger.error(f"Error generating optimal config: {e}")
            return None
    
    async def monitor_and_adjust_grids(self):
        """Monitor all grids and adjust them based on performance and market conditions"""
        while True:
            try:
                active_grids = list(self.grid_engine.active_grids.keys())
                
                for grid_id in active_grids:
                    await self._monitor_grid_performance(grid_id)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in grid monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_grid_performance(self, grid_id: str):
        """Monitor and adjust a specific grid's performance"""
        try:
            # Check if adjustment is needed
            if not self._should_adjust_grid(grid_id):
                return
            
            grid = self.grid_engine.active_grids.get(grid_id)
            if not grid:
                return
            
            config = grid['config']
            
            # Analyze current market conditions
            analysis = await self.market_analyzer.analyze_market(config.symbol, config.exchange)
            
            # Calculate performance metrics
            metrics = await self.performance_tracker.calculate_metrics(grid_id, self.grid_engine)
            
            # Determine if adjustment is needed
            adjustment_needed = await self._evaluate_adjustment_need(analysis, metrics)
            
            if adjustment_needed:
                await self._adjust_grid(grid_id, analysis, metrics)
                self.last_adjustment[grid_id] = time.time()
            
        except Exception as e:
            logger.error(f"Error monitoring grid {grid_id}: {e}")
    
    def _should_adjust_grid(self, grid_id: str) -> bool:
        """Check if enough time has passed since last adjustment"""
        last_adj = self.last_adjustment.get(grid_id, 0)
        return time.time() - last_adj > self.adjustment_interval
    
    async def _evaluate_adjustment_need(self, analysis: MarketAnalysis, 
                                      metrics: GridPerformanceMetrics) -> bool:
        """Evaluate if grid adjustment is needed"""
        try:
            # Check efficiency
            if metrics.efficiency_score < self.efficiency_threshold:
                logger.info(f"Grid {metrics.grid_id} efficiency low: {metrics.efficiency_score:.2f}")
                return True
            
            # Check if market conditions changed significantly
            if analysis.volatility > self.max_volatility_threshold:
                logger.info(f"High volatility detected: {analysis.volatility:.2f}%")
                return True
            
            if analysis.volatility < self.min_volatility_threshold:
                logger.info(f"Low volatility detected: {analysis.volatility:.2f}%")
                return True
            
            # Check trend strength
            if abs(analysis.trend_strength) > self.trend_threshold:
                logger.info(f"Strong trend detected: {analysis.trend_strength:.2f}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating adjustment need: {e}")
            return False
    
    async def _adjust_grid(self, grid_id: str, analysis: MarketAnalysis, 
                          metrics: GridPerformanceMetrics):
        """Adjust grid configuration based on analysis and performance"""
        try:
            logger.info(f"🧠 Adjusting grid {grid_id} based on market conditions")
            
            # For now, we'll log the adjustment recommendation
            # In a full implementation, this would modify the grid
            
            if analysis.condition == MarketCondition.HIGH_VOLATILITY:
                logger.info(f"   Recommendation: Increase grid spacing to {analysis.volatility * 10:.1f}%")
            elif analysis.condition == MarketCondition.LOW_VOLATILITY:
                logger.info(f"   Recommendation: Decrease grid spacing to {analysis.volatility * 5:.1f}%")
            elif analysis.condition == MarketCondition.TRENDING_UP:
                logger.info(f"   Recommendation: Add more buy levels for uptrend")
            elif analysis.condition == MarketCondition.TRENDING_DOWN:
                logger.info(f"   Recommendation: Add more sell levels for downtrend")
            
            if metrics.efficiency_score < 0.5:
                logger.info(f"   Recommendation: Consider stopping grid due to low efficiency")
            
        except Exception as e:
            logger.error(f"Error adjusting grid: {e}")


class MarketAnalyzer:
    """Analyzes market conditions for optimal grid trading"""
    
    def __init__(self, exchange_manager):
        self.exchange_manager = exchange_manager
        self.price_history = {}
    
    async def analyze_market(self, symbol: str, exchange: str) -> MarketAnalysis:
        """Analyze current market conditions"""
        try:
            # Get current market data
            ticker = await self.exchange_manager.get_ticker(symbol, exchange)
            current_price = ticker['last']
            
            # Calculate volatility (simplified)
            volatility = await self._calculate_volatility(symbol, exchange)
            
            # Detect trend
            trend_strength = await self._detect_trend(symbol, exchange)
            
            # Analyze volume
            volume_ratio = await self._analyze_volume(symbol, exchange)
            
            # Determine market condition
            condition = self._determine_market_condition(volatility, trend_strength, volume_ratio)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(condition, volatility, trend_strength)
            
            return MarketAnalysis(
                condition=condition,
                volatility=volatility,
                trend_strength=trend_strength,
                volume_ratio=volume_ratio,
                price_change_24h=0.0,  # Simplified
                recommended_action=recommendation
            )
            
        except Exception as e:
            logger.error(f"Error analyzing market: {e}")
            # Return default analysis
            return MarketAnalysis(
                condition=MarketCondition.SIDEWAYS,
                volatility=0.03,
                trend_strength=0.0,
                volume_ratio=1.0,
                price_change_24h=0.0,
                recommended_action="create_standard_grid"
            )
    
    async def _calculate_volatility(self, symbol: str, exchange: str) -> float:
        """Calculate market volatility (simplified)"""
        # In a real implementation, this would use historical price data
        # For now, return a simulated volatility based on symbol
        volatility_map = {
            'BTC/USDT': 0.03,  # 3% daily volatility
            'ETH/USDT': 0.04,  # 4% daily volatility
            'SOL/USDT': 0.06,  # 6% daily volatility
        }
        return volatility_map.get(symbol, 0.05)
    
    async def _detect_trend(self, symbol: str, exchange: str) -> float:
        """Detect trend strength (-1 to 1, negative = downtrend)"""
        # Simplified trend detection
        return 0.0  # Assume sideways market
    
    async def _analyze_volume(self, symbol: str, exchange: str) -> float:
        """Analyze volume ratio compared to average"""
        # Simplified volume analysis
        return 1.0  # Assume normal volume
    
    def _determine_market_condition(self, volatility: float, trend_strength: float, 
                                  volume_ratio: float) -> MarketCondition:
        """Determine overall market condition"""
        if volatility > 0.08:
            return MarketCondition.HIGH_VOLATILITY
        elif volatility < 0.02:
            return MarketCondition.LOW_VOLATILITY
        elif trend_strength > 0.05:
            return MarketCondition.TRENDING_UP
        elif trend_strength < -0.05:
            return MarketCondition.TRENDING_DOWN
        else:
            return MarketCondition.SIDEWAYS
    
    def _generate_recommendation(self, condition: MarketCondition, volatility: float, 
                               trend_strength: float) -> str:
        """Generate trading recommendation"""
        if condition == MarketCondition.HIGH_VOLATILITY:
            return "use_wide_grid_spacing"
        elif condition == MarketCondition.LOW_VOLATILITY:
            return "use_tight_grid_spacing"
        elif condition == MarketCondition.TRENDING_UP:
            return "bias_towards_buy_orders"
        elif condition == MarketCondition.TRENDING_DOWN:
            return "bias_towards_sell_orders"
        else:
            return "create_balanced_grid"


class GridPerformanceTracker:
    """Tracks and analyzes grid performance metrics"""
    
    async def calculate_metrics(self, grid_id: str, grid_engine: GridTradingEngine) -> GridPerformanceMetrics:
        """Calculate comprehensive performance metrics for a grid"""
        try:
            grid_status = await grid_engine.get_grid_status(grid_id)
            
            if 'error' in grid_status:
                return self._default_metrics(grid_id)
            
            performance = grid_status['performance']
            
            # Calculate cycles per hour
            created_at = datetime.fromisoformat(grid_status['created_at'])
            hours_active = (datetime.now() - created_at).total_seconds() / 3600
            cycles_per_hour = performance['total_cycles'] / max(hours_active, 0.1)
            
            # Calculate profit rate
            profit_rate = performance['roi_pct'] / 100 if hours_active > 0 else 0
            
            # Calculate efficiency score (0-1)
            efficiency_score = min(1.0, cycles_per_hour / 2.0)  # 2 cycles/hour = 100% efficiency
            
            # Calculate market capture rate
            market_capture_rate = min(1.0, performance['total_cycles'] / max(hours_active * 1.5, 1))
            
            # Calculate risk score
            risk_score = abs(performance['unrealized_pnl']) / max(performance['total_invested'], 1)
            
            return GridPerformanceMetrics(
                grid_id=grid_id,
                cycles_per_hour=cycles_per_hour,
                profit_rate=profit_rate,
                efficiency_score=efficiency_score,
                market_capture_rate=market_capture_rate,
                risk_score=risk_score
            )
            
        except Exception as e:
            logger.error(f"Error calculating metrics for {grid_id}: {e}")
            return self._default_metrics(grid_id)
    
    def _default_metrics(self, grid_id: str) -> GridPerformanceMetrics:
        """Return default metrics when calculation fails"""
        return GridPerformanceMetrics(
            grid_id=grid_id,
            cycles_per_hour=0.0,
            profit_rate=0.0,
            efficiency_score=0.0,
            market_capture_rate=0.0,
            risk_score=0.0
        )
