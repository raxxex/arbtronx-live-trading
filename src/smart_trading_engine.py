#!/usr/bin/env python3
"""
Smart Trading Engine for ARBTRONX
Implements advanced features: Smart Entry, Auto Switch, Loss Cut, Cycle Discipline
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class TradingSignal(Enum):
    WAIT = "wait"
    ENTER = "enter"
    EXIT = "exit"
    PAUSE = "pause"

@dataclass
class MarketMetrics:
    """Market analysis metrics"""
    symbol: str
    price: float
    volume_24h: float
    volume_spike: float  # Current volume vs 24h average
    rsi: float
    rsi_divergence: bool
    volatility_score: float
    breakout_risk: float
    timestamp: datetime

@dataclass
class GridStatus:
    """Grid trading status"""
    symbol: str
    active: bool
    entry_price: float
    grid_range: Tuple[float, float]  # (lower, upper)
    completed_cycles: int
    current_profit: float
    total_invested: float
    last_cycle_time: datetime
    risk_level: str  # "low", "medium", "high"

class SmartTradingEngine:
    """Advanced trading engine with smart features"""
    
    def __init__(self, enhanced_api):
        self.api = enhanced_api
        self.active_grids: Dict[str, GridStatus] = {}
        self.market_metrics: Dict[str, MarketMetrics] = {}
        
        # Configuration
        self.meme_pairs = [
            'PEPE/USDT', 'FLOKI/USDT', 'DOGE/USDT', 
            'SHIB/USDT', 'SUI/USDT', 'WIF/USDT',
            'BONK/USDT', 'MEME/USDT', 'BOME/USDT', 'POPCAT/USDT'
        ]
        
        # Smart Entry Settings
        self.volume_spike_threshold = 2.0  # 2x normal volume
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        
        # Auto Switch Settings
        self.volatility_check_interval = 300  # 5 minutes
        self.min_volatility_score = 5.0
        
        # Loss Cut Settings
        self.breakout_threshold = 0.15  # 15% beyond grid range
        self.max_loss_per_grid = 0.08  # 8% maximum loss
        
        # Cycle Discipline Settings
        self.min_cycle_duration = 1800  # 30 minutes minimum
        self.reinvest_percentage = 1.0  # 100% reinvestment
        
        # Historical data for analysis
        self.price_history: Dict[str, List[float]] = {}
        self.volume_history: Dict[str, List[float]] = {}
        
    async def initialize(self):
        """Initialize the smart trading engine"""
        try:
            logger.info("🧠 Initializing Smart Trading Engine...")
            
            # Start background tasks
            asyncio.create_task(self._market_analysis_loop())
            asyncio.create_task(self._auto_switch_loop())
            asyncio.create_task(self._risk_monitoring_loop())
            
            logger.info("✅ Smart Trading Engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Smart Trading Engine: {e}")
            return False
    
    async def _market_analysis_loop(self):
        """Continuous market analysis for smart entry signals"""
        while True:
            try:
                await self._analyze_all_pairs()
                await asyncio.sleep(60)  # Analyze every minute
            except Exception as e:
                logger.error(f"Market analysis error: {e}")
                await asyncio.sleep(60)
    
    async def _analyze_all_pairs(self):
        """Analyze all meme pairs for trading opportunities"""
        try:
            # Get current market data
            market_data = await self.api.get_formatted_market_data()
            if not market_data['success']:
                return
            
            for symbol in self.meme_pairs:
                if symbol in market_data['market_data']:
                    data = market_data['market_data'][symbol]
                    await self._analyze_pair(symbol, data)
                    
        except Exception as e:
            logger.error(f"Error analyzing pairs: {e}")
    
    async def _analyze_pair(self, symbol: str, data: Dict):
        """Analyze individual pair for smart entry signals"""
        try:
            # Update price history
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            self.price_history[symbol].append(data['price'])
            
            # Keep only last 100 data points
            if len(self.price_history[symbol]) > 100:
                self.price_history[symbol] = self.price_history[symbol][-100:]
            
            # Update volume history
            if symbol not in self.volume_history:
                self.volume_history[symbol] = []
            self.volume_history[symbol].append(data['volume_24h'])
            
            if len(self.volume_history[symbol]) > 100:
                self.volume_history[symbol] = self.volume_history[symbol][-100:]
            
            # Calculate metrics
            metrics = await self._calculate_metrics(symbol, data)
            self.market_metrics[symbol] = metrics
            
            # Check for smart entry signal
            signal = await self._get_trading_signal(symbol, metrics)
            
            if signal == TradingSignal.ENTER:
                await self._smart_entry(symbol, metrics)
            elif signal == TradingSignal.PAUSE:
                await self._pause_grid(symbol, "Risk management")
                
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
    
    async def _calculate_metrics(self, symbol: str, data: Dict) -> MarketMetrics:
        """Calculate advanced market metrics"""
        try:
            price = data['price']
            volume = data['volume_24h']
            
            # Calculate RSI
            rsi = await self._calculate_rsi(symbol)
            
            # Calculate volume spike
            volume_spike = await self._calculate_volume_spike(symbol)
            
            # Check RSI divergence
            rsi_divergence = await self._check_rsi_divergence(symbol)
            
            # Calculate volatility score
            volatility_score = await self._calculate_volatility_score(symbol)
            
            # Calculate breakout risk
            breakout_risk = await self._calculate_breakout_risk(symbol)
            
            return MarketMetrics(
                symbol=symbol,
                price=price,
                volume_24h=volume,
                volume_spike=volume_spike,
                rsi=rsi,
                rsi_divergence=rsi_divergence,
                volatility_score=volatility_score,
                breakout_risk=breakout_risk,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error calculating metrics for {symbol}: {e}")
            return MarketMetrics(
                symbol=symbol, price=data['price'], volume_24h=data['volume_24h'],
                volume_spike=1.0, rsi=50.0, rsi_divergence=False,
                volatility_score=5.0, breakout_risk=0.0, timestamp=datetime.now()
            )
    
    async def _calculate_rsi(self, symbol: str, period: int = 14) -> float:
        """Calculate RSI indicator"""
        try:
            if symbol not in self.price_history or len(self.price_history[symbol]) < period + 1:
                return 50.0  # Neutral RSI
            
            prices = np.array(self.price_history[symbol][-period-1:])
            deltas = np.diff(prices)
            
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi)
            
        except Exception as e:
            logger.error(f"Error calculating RSI for {symbol}: {e}")
            return 50.0
    
    async def _calculate_volume_spike(self, symbol: str) -> float:
        """Calculate volume spike ratio"""
        try:
            if symbol not in self.volume_history or len(self.volume_history[symbol]) < 10:
                return 1.0
            
            current_volume = self.volume_history[symbol][-1]
            avg_volume = np.mean(self.volume_history[symbol][-10:-1])
            
            if avg_volume == 0:
                return 1.0
            
            return current_volume / avg_volume
            
        except Exception as e:
            logger.error(f"Error calculating volume spike for {symbol}: {e}")
            return 1.0
    
    async def _check_rsi_divergence(self, symbol: str) -> bool:
        """Check for RSI divergence pattern"""
        try:
            if symbol not in self.price_history or len(self.price_history[symbol]) < 20:
                return False
            
            # Simple divergence check: price making lower lows while RSI making higher lows
            prices = self.price_history[symbol][-20:]
            
            # Calculate RSI for recent periods
            rsi_values = []
            for i in range(len(prices) - 14):
                subset = prices[i:i+15]
                deltas = np.diff(subset)
                gains = np.where(deltas > 0, deltas, 0)
                losses = np.where(deltas < 0, -deltas, 0)
                
                avg_gain = np.mean(gains)
                avg_loss = np.mean(losses)
                
                if avg_loss == 0:
                    rsi_values.append(100.0)
                else:
                    rs = avg_gain / avg_loss
                    rsi_values.append(100 - (100 / (1 + rs)))
            
            if len(rsi_values) < 3:
                return False
            
            # Check for bullish divergence (price down, RSI up)
            price_trend = prices[-1] < prices[-3]
            rsi_trend = rsi_values[-1] > rsi_values[-3]
            
            return price_trend and rsi_trend
            
        except Exception as e:
            logger.error(f"Error checking RSI divergence for {symbol}: {e}")
            return False
    
    async def _calculate_volatility_score(self, symbol: str) -> float:
        """Calculate volatility score for pair ranking"""
        try:
            if symbol not in self.price_history or len(self.price_history[symbol]) < 20:
                return 5.0
            
            prices = np.array(self.price_history[symbol][-20:])
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns) * 100  # Convert to percentage
            
            # Scale to 0-10 score
            score = min(volatility * 100, 10.0)
            return float(score)
            
        except Exception as e:
            logger.error(f"Error calculating volatility score for {symbol}: {e}")
            return 5.0
    
    async def _calculate_breakout_risk(self, symbol: str) -> float:
        """Calculate risk of price breaking out of grid range"""
        try:
            if symbol not in self.active_grids:
                return 0.0
            
            grid = self.active_grids[symbol]
            current_price = self.price_history[symbol][-1] if symbol in self.price_history else grid.entry_price
            
            lower_bound, upper_bound = grid.grid_range
            
            # Calculate distance from grid boundaries
            if current_price < lower_bound:
                risk = (lower_bound - current_price) / lower_bound
            elif current_price > upper_bound:
                risk = (current_price - upper_bound) / upper_bound
            else:
                risk = 0.0
            
            return float(risk)
            
        except Exception as e:
            logger.error(f"Error calculating breakout risk for {symbol}: {e}")
            return 0.0
    
    async def _get_trading_signal(self, symbol: str, metrics: MarketMetrics) -> TradingSignal:
        """Generate trading signal based on analysis"""
        try:
            # Check if grid is already active
            if symbol in self.active_grids and self.active_grids[symbol].active:
                # Check for exit/pause conditions
                if metrics.breakout_risk > self.breakout_threshold:
                    return TradingSignal.PAUSE
                return TradingSignal.WAIT
            
            # Smart entry conditions
            volume_condition = metrics.volume_spike >= self.volume_spike_threshold
            rsi_condition = (metrics.rsi <= self.rsi_oversold and metrics.rsi_divergence) or \
                           (metrics.rsi >= self.rsi_overbought and metrics.rsi_divergence)
            volatility_condition = metrics.volatility_score >= self.min_volatility_score
            
            if volume_condition and rsi_condition and volatility_condition:
                return TradingSignal.ENTER
            
            return TradingSignal.WAIT
            
        except Exception as e:
            logger.error(f"Error generating trading signal for {symbol}: {e}")
            return TradingSignal.WAIT
    
    async def _smart_entry(self, symbol: str, metrics: MarketMetrics):
        """Execute smart entry for grid trading"""
        try:
            logger.info(f"🎯 Smart entry signal for {symbol}")
            logger.info(f"   Volume spike: {metrics.volume_spike:.2f}x")
            logger.info(f"   RSI: {metrics.rsi:.1f} (Divergence: {metrics.rsi_divergence})")
            logger.info(f"   Volatility score: {metrics.volatility_score:.1f}")
            
            # Calculate optimal grid parameters
            grid_spacing = await self._calculate_optimal_spacing(symbol, metrics)
            order_size = await self._calculate_optimal_order_size(symbol)
            
            # Create grid
            await self._create_smart_grid(symbol, metrics.price, grid_spacing, order_size)
            
        except Exception as e:
            logger.error(f"Error executing smart entry for {symbol}: {e}")
    
    async def _calculate_optimal_spacing(self, symbol: str, metrics: MarketMetrics) -> float:
        """Calculate optimal grid spacing based on volatility"""
        try:
            base_spacing = {
                'PEPE/USDT': 0.4, 'FLOKI/USDT': 0.5, 'DOGE/USDT': 0.6,
                'SHIB/USDT': 0.4, 'SUI/USDT': 0.8, 'WIF/USDT': 0.5,
                'BONK/USDT': 0.4, 'MEME/USDT': 0.5, 'BOME/USDT': 0.6, 'POPCAT/USDT': 0.5
            }
            
            base = base_spacing.get(symbol, 0.5)
            
            # Adjust based on volatility
            if metrics.volatility_score > 8.0:
                return base * 1.5  # Wider spacing for high volatility
            elif metrics.volatility_score < 3.0:
                return base * 0.7  # Tighter spacing for low volatility
            
            return base
            
        except Exception as e:
            logger.error(f"Error calculating optimal spacing for {symbol}: {e}")
            return 0.5
    
    async def _calculate_optimal_order_size(self, symbol: str) -> float:
        """Calculate optimal order size based on available capital"""
        try:
            # Get current balance
            balance_data = await self.api.get_formatted_balances()
            if not balance_data['success']:
                return 20.0  # Default order size
            
            total_usdt = balance_data.get('total_usdt_value', 200.0)
            
            # Use 20% of total capital per grid, divided by 5 levels
            order_size = (total_usdt * 0.20) / 5
            
            return max(order_size, 10.0)  # Minimum $10 per order
            
        except Exception as e:
            logger.error(f"Error calculating optimal order size: {e}")
            return 20.0
    
    async def _create_smart_grid(self, symbol: str, entry_price: float, spacing: float, order_size: float):
        """Create a smart grid with calculated parameters"""
        try:
            # Calculate grid range
            range_multiplier = 0.10  # 10% range around entry price
            lower_bound = entry_price * (1 - range_multiplier)
            upper_bound = entry_price * (1 + range_multiplier)
            
            # Create grid status
            grid_status = GridStatus(
                symbol=symbol,
                active=True,
                entry_price=entry_price,
                grid_range=(lower_bound, upper_bound),
                completed_cycles=0,
                current_profit=0.0,
                total_invested=order_size * 5,  # 5 levels
                last_cycle_time=datetime.now(),
                risk_level="medium"
            )
            
            self.active_grids[symbol] = grid_status
            
            logger.info(f"✅ Smart grid created for {symbol}")
            logger.info(f"   Entry: ${entry_price:.6f}")
            logger.info(f"   Range: ${lower_bound:.6f} - ${upper_bound:.6f}")
            logger.info(f"   Spacing: {spacing}%")
            logger.info(f"   Order size: ${order_size:.2f}")
            
        except Exception as e:
            logger.error(f"Error creating smart grid for {symbol}: {e}")
    
    async def _auto_switch_loop(self):
        """Auto switch to most volatile pairs"""
        while True:
            try:
                await self._evaluate_pair_switching()
                await asyncio.sleep(self.volatility_check_interval)
            except Exception as e:
                logger.error(f"Auto switch error: {e}")
                await asyncio.sleep(self.volatility_check_interval)
    
    async def _evaluate_pair_switching(self):
        """Evaluate if we should switch to more volatile pairs"""
        try:
            # Rank pairs by volatility
            volatility_ranking = []
            for symbol, metrics in self.market_metrics.items():
                volatility_ranking.append((symbol, metrics.volatility_score))
            
            # Sort by volatility (highest first)
            volatility_ranking.sort(key=lambda x: x[1], reverse=True)
            
            logger.info("📊 Volatility ranking:")
            for i, (symbol, score) in enumerate(volatility_ranking[:5]):
                logger.info(f"   {i+1}. {symbol}: {score:.1f}")
            
            # Check if we should switch any active grids
            await self._consider_switching(volatility_ranking)
            
        except Exception as e:
            logger.error(f"Error evaluating pair switching: {e}")
    
    async def _consider_switching(self, volatility_ranking: List[Tuple[str, float]]):
        """Consider switching low-performing grids to high-volatility pairs"""
        try:
            top_volatile = [pair for pair, score in volatility_ranking[:3] if score >= self.min_volatility_score]
            
            for symbol, grid in self.active_grids.items():
                if not grid.active:
                    continue
                
                current_volatility = self.market_metrics.get(symbol, {}).volatility_score if symbol in self.market_metrics else 0
                
                # Check if there's a much better pair available
                for top_symbol in top_volatile:
                    if top_symbol == symbol:
                        continue
                    
                    top_volatility = self.market_metrics.get(top_symbol, {}).volatility_score if top_symbol in self.market_metrics else 0
                    
                    # Switch if new pair has 50% higher volatility and current grid is underperforming
                    if (top_volatility > current_volatility * 1.5 and 
                        grid.completed_cycles == 0 and 
                        (datetime.now() - grid.last_cycle_time).seconds > 3600):  # 1 hour
                        
                        await self._switch_grid(symbol, top_symbol)
                        break
                        
        except Exception as e:
            logger.error(f"Error considering switching: {e}")
    
    async def _switch_grid(self, from_symbol: str, to_symbol: str):
        """Switch grid from one pair to another"""
        try:
            logger.info(f"🔄 Switching grid: {from_symbol} → {to_symbol}")
            
            # Close current grid
            if from_symbol in self.active_grids:
                self.active_grids[from_symbol].active = False
            
            # Create new grid for better pair
            if to_symbol in self.market_metrics:
                metrics = self.market_metrics[to_symbol]
                await self._smart_entry(to_symbol, metrics)
            
        except Exception as e:
            logger.error(f"Error switching grid from {from_symbol} to {to_symbol}: {e}")
    
    async def _risk_monitoring_loop(self):
        """Monitor risk and implement loss cut protection"""
        while True:
            try:
                await self._monitor_risk()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Risk monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _monitor_risk(self):
        """Monitor risk for all active grids"""
        try:
            for symbol, grid in self.active_grids.items():
                if not grid.active:
                    continue
                
                # Check breakout risk
                if symbol in self.market_metrics:
                    metrics = self.market_metrics[symbol]
                    
                    if metrics.breakout_risk > self.breakout_threshold:
                        await self._pause_grid(symbol, f"Breakout risk: {metrics.breakout_risk:.1%}")
                    
                    # Check maximum loss
                    loss_percentage = abs(grid.current_profit) / grid.total_invested
                    if loss_percentage > self.max_loss_per_grid:
                        await self._pause_grid(symbol, f"Max loss reached: {loss_percentage:.1%}")
                        
        except Exception as e:
            logger.error(f"Error monitoring risk: {e}")
    
    async def _pause_grid(self, symbol: str, reason: str):
        """Pause grid trading for risk management"""
        try:
            if symbol in self.active_grids:
                self.active_grids[symbol].active = False
                self.active_grids[symbol].risk_level = "high"
                
                logger.warning(f"⏸️  Grid paused for {symbol}: {reason}")
                
        except Exception as e:
            logger.error(f"Error pausing grid for {symbol}: {e}")
    
    async def check_cycle_completion(self, symbol: str) -> bool:
        """Check if grid cycle should be completed (discipline enforcement)"""
        try:
            if symbol not in self.active_grids:
                return False
            
            grid = self.active_grids[symbol]
            
            # Enforce minimum cycle duration
            time_since_start = (datetime.now() - grid.last_cycle_time).seconds
            if time_since_start < self.min_cycle_duration:
                logger.info(f"⏳ Cycle discipline: {symbol} needs {self.min_cycle_duration - time_since_start}s more")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking cycle completion for {symbol}: {e}")
            return False
    
    async def complete_cycle_and_reinvest(self, symbol: str, profit: float):
        """Complete cycle and reinvest profits"""
        try:
            if symbol not in self.active_grids:
                return
            
            grid = self.active_grids[symbol]
            grid.completed_cycles += 1
            grid.current_profit += profit
            grid.last_cycle_time = datetime.now()
            
            # Calculate reinvestment amount
            reinvest_amount = profit * self.reinvest_percentage
            grid.total_invested += reinvest_amount
            
            logger.info(f"🔄 Cycle completed for {symbol}")
            logger.info(f"   Cycle #{grid.completed_cycles}")
            logger.info(f"   Profit: ${profit:.2f}")
            logger.info(f"   Reinvesting: ${reinvest_amount:.2f} ({self.reinvest_percentage:.0%})")
            logger.info(f"   New capital: ${grid.total_invested:.2f}")
            
            # Reset for next cycle
            await self._prepare_next_cycle(symbol)
            
        except Exception as e:
            logger.error(f"Error completing cycle for {symbol}: {e}")
    
    async def _prepare_next_cycle(self, symbol: str):
        """Prepare for next trading cycle with increased capital"""
        try:
            if symbol not in self.active_grids:
                return
            
            grid = self.active_grids[symbol]
            
            # Calculate new order sizes based on increased capital
            new_order_size = grid.total_invested / 5  # 5 levels
            
            # Update grid with new parameters
            if symbol in self.market_metrics:
                metrics = self.market_metrics[symbol]
                spacing = await self._calculate_optimal_spacing(symbol, metrics)
                
                logger.info(f"🚀 Next cycle prepared for {symbol}")
                logger.info(f"   New order size: ${new_order_size:.2f}")
                logger.info(f"   Grid spacing: {spacing}%")
                
        except Exception as e:
            logger.error(f"Error preparing next cycle for {symbol}: {e}")
    
    def get_smart_trading_status(self) -> Dict:
        """Get comprehensive smart trading status"""
        try:
            active_grids_info = {}
            for symbol, grid in self.active_grids.items():
                metrics = self.market_metrics.get(symbol, {})
                
                active_grids_info[symbol] = {
                    "active": grid.active,
                    "entry_price": grid.entry_price,
                    "completed_cycles": grid.completed_cycles,
                    "current_profit": grid.current_profit,
                    "total_invested": grid.total_invested,
                    "risk_level": grid.risk_level,
                    "volatility_score": getattr(metrics, 'volatility_score', 0),
                    "volume_spike": getattr(metrics, 'volume_spike', 1.0),
                    "rsi": getattr(metrics, 'rsi', 50.0),
                    "breakout_risk": getattr(metrics, 'breakout_risk', 0.0)
                }
            
            # Volatility ranking
            volatility_ranking = []
            for symbol, metrics in self.market_metrics.items():
                volatility_ranking.append({
                    "symbol": symbol,
                    "volatility_score": metrics.volatility_score,
                    "volume_spike": metrics.volume_spike,
                    "rsi": metrics.rsi
                })
            
            volatility_ranking.sort(key=lambda x: x['volatility_score'], reverse=True)
            
            return {
                "smart_features_active": True,
                "active_grids": active_grids_info,
                "volatility_ranking": volatility_ranking[:10],
                "total_active_grids": len([g for g in self.active_grids.values() if g.active]),
                "total_completed_cycles": sum(g.completed_cycles for g in self.active_grids.values()),
                "total_profit": sum(g.current_profit for g in self.active_grids.values()),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting smart trading status: {e}")
            return {"smart_features_active": False, "error": str(e)}

# Global instance
smart_trading_engine = None

def initialize_smart_trading_engine(enhanced_api):
    """Initialize the smart trading engine"""
    global smart_trading_engine
    smart_trading_engine = SmartTradingEngine(enhanced_api)
    return smart_trading_engine
