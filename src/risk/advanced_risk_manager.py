"""
Advanced Risk Management System for Enhanced Arbitrage Bot
"""
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque
import statistics
import numpy as np
from loguru import logger

from config import settings
from src.arbitrage.opportunity import ArbitrageOpportunity


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics"""
    overall_risk_score: float  # 0-100 scale
    risk_level: RiskLevel
    
    # Portfolio risk
    total_exposure_usd: float
    concentration_risk: float
    correlation_risk: float
    
    # Market risk
    volatility_risk: float
    liquidity_risk: float
    spread_risk: float
    
    # Operational risk
    execution_risk: float
    exchange_risk: float
    technical_risk: float
    
    # Performance risk
    drawdown_risk: float
    var_95: float  # Value at Risk (95% confidence)
    
    # Risk limits
    daily_loss_limit: float
    position_size_limit: float
    correlation_limit: float
    
    timestamp: int


@dataclass
class PositionRisk:
    """Risk assessment for individual positions"""
    symbol: str
    exchange_pair: Tuple[str, str]
    position_size_usd: float
    risk_score: float
    risk_factors: Dict[str, float]
    max_loss_estimate: float
    confidence_interval: Tuple[float, float]


@dataclass
class RiskAlert:
    """Risk alert notification"""
    level: RiskLevel
    category: str
    message: str
    recommended_action: str
    timestamp: int


class AdvancedRiskManager:
    """Advanced risk management system with sophisticated controls"""
    
    def __init__(self):
        # Risk limits and parameters
        self.max_daily_loss_usd = 1000.0
        self.max_position_size_usd = 2000.0
        self.max_total_exposure_usd = 10000.0
        self.max_correlation_exposure = 0.6
        self.max_single_exchange_exposure = 0.4
        
        # Risk monitoring
        self.risk_history: deque = deque(maxlen=100)
        self.position_history: deque = deque(maxlen=500)
        self.alert_history: deque = deque(maxlen=50)
        
        # Performance tracking
        self.daily_pnl: Dict[str, float] = {}  # Daily P&L by date
        self.daily_returns: List[float] = []  # Daily returns for metrics calculation
        self.execution_times: deque = deque(maxlen=100)
        self.slippage_history: deque = deque(maxlen=100)

        # Portfolio metrics
        self.portfolio_volatility: float = 0.0
        self.max_drawdown: float = 0.0
        self.sharpe_ratio: float = 0.0
        self.positions: Dict[str, any] = {}  # Current positions
        
        # Current state
        self.current_exposure_usd = 0.0
        self.active_positions: Dict[str, PositionRisk] = {}
        self.daily_loss_current = 0.0
        self.last_reset_date = time.strftime("%Y-%m-%d")
        
        # Risk factors weights
        self.risk_weights = {
            'volatility': 0.25,
            'liquidity': 0.20,
            'concentration': 0.15,
            'correlation': 0.15,
            'execution': 0.10,
            'exchange': 0.10,
            'drawdown': 0.05
        }
        
        # Market volatility data (simplified)
        self.volatility_data = {
            'BTC/USDT': 0.04,  # 4% daily volatility
            'ETH/USDT': 0.05,  # 5% daily volatility
            'SOL/USDT': 0.08,  # 8% daily volatility
            'XRP/USDT': 0.06,  # 6% daily volatility
            'TON/USDT': 0.10,  # 10% daily volatility
            'RNDR/USDT': 0.12, # 12% daily volatility
            'KAS/USDT': 0.15,  # 15% daily volatility
            'SNX/USDT': 0.10,  # 10% daily volatility
        }
    
    def assess_opportunity_risk(self, opportunity: ArbitrageOpportunity) -> Tuple[bool, float, Dict[str, float]]:
        """Comprehensive risk assessment for an arbitrage opportunity"""
        risk_factors = {}
        
        # 1. Volatility Risk
        volatility_risk = self._calculate_volatility_risk(opportunity.symbol)
        risk_factors['volatility'] = volatility_risk
        
        # 2. Liquidity Risk
        liquidity_risk = self._calculate_liquidity_risk(opportunity)
        risk_factors['liquidity'] = liquidity_risk
        
        # 3. Spread Risk
        spread_risk = self._calculate_spread_risk(opportunity)
        risk_factors['spread'] = spread_risk
        
        # 4. Execution Risk
        execution_risk = self._calculate_execution_risk(opportunity)
        risk_factors['execution'] = execution_risk
        
        # 5. Concentration Risk
        concentration_risk = self._calculate_concentration_risk(opportunity)
        risk_factors['concentration'] = concentration_risk
        
        # 6. Exchange Risk
        exchange_risk = self._calculate_exchange_risk(opportunity)
        risk_factors['exchange'] = exchange_risk
        
        # 7. Correlation Risk
        correlation_risk = self._calculate_correlation_risk(opportunity)
        risk_factors['correlation'] = correlation_risk
        
        # Calculate overall risk score
        overall_risk = sum(
            risk_factors[factor] * self.risk_weights.get(factor, 0.1)
            for factor in risk_factors
        )
        
        # Risk approval decision
        approved = self._make_risk_decision(overall_risk, risk_factors)
        
        return approved, overall_risk, risk_factors
    
    def _calculate_volatility_risk(self, symbol: str) -> float:
        """Calculate volatility-based risk (0-100 scale)"""
        base_volatility = self.volatility_data.get(symbol, 0.08)
        
        # Convert to risk score (higher volatility = higher risk)
        volatility_risk = min(base_volatility * 500, 100)  # Scale to 0-100
        
        return volatility_risk
    
    def _calculate_liquidity_risk(self, opportunity: ArbitrageOpportunity) -> float:
        """Calculate liquidity-based risk"""
        # Use volume as liquidity proxy
        if opportunity.volume < 1.0:
            return 80.0  # High risk for low liquidity
        elif opportunity.volume < 5.0:
            return 50.0  # Medium risk
        elif opportunity.volume < 20.0:
            return 20.0  # Low-medium risk
        else:
            return 10.0  # Low risk for high liquidity
    
    def _calculate_spread_risk(self, opportunity: ArbitrageOpportunity) -> float:
        """Calculate spread-based risk"""
        # Lower spreads are riskier (more likely to disappear)
        if opportunity.spread_percentage < 0.1:
            return 90.0  # Very high risk
        elif opportunity.spread_percentage < 0.3:
            return 60.0  # High risk
        elif opportunity.spread_percentage < 0.5:
            return 30.0  # Medium risk
        else:
            return 10.0  # Low risk
    
    def _calculate_execution_risk(self, opportunity: ArbitrageOpportunity) -> float:
        """Calculate execution-based risk"""
        risk_score = 0.0
        
        # Age of opportunity
        current_time = int(time.time() * 1000)
        age_seconds = (current_time - opportunity.timestamp) / 1000
        
        if age_seconds > 10:
            risk_score += 40.0
        elif age_seconds > 5:
            risk_score += 20.0
        
        # Expected slippage
        expected_slippage = getattr(opportunity, 'expected_slippage', 0.1)
        if expected_slippage > 0.5:
            risk_score += 30.0
        elif expected_slippage > 0.2:
            risk_score += 15.0
        
        # Historical execution performance
        if self.execution_times:
            avg_execution_time = statistics.mean(self.execution_times)
            if avg_execution_time > 10.0:
                risk_score += 20.0
            elif avg_execution_time > 5.0:
                risk_score += 10.0
        
        return min(risk_score, 100.0)
    
    def _calculate_concentration_risk(self, opportunity: ArbitrageOpportunity) -> float:
        """Calculate concentration risk"""
        # Check if adding this position would create concentration
        symbol_exposure = sum(
            pos.position_size_usd for pos in self.active_positions.values()
            if pos.symbol == opportunity.symbol
        )
        
        new_total_exposure = symbol_exposure + (opportunity.buy_amount * opportunity.buy_price)
        concentration_pct = new_total_exposure / max(self.max_total_exposure_usd, 1)
        
        if concentration_pct > 0.3:
            return 80.0  # High concentration risk
        elif concentration_pct > 0.2:
            return 50.0  # Medium concentration risk
        elif concentration_pct > 0.1:
            return 25.0  # Low-medium concentration risk
        else:
            return 10.0  # Low concentration risk
    
    def _calculate_exchange_risk(self, opportunity: ArbitrageOpportunity) -> float:
        """Calculate exchange-specific risk"""
        risk_score = 0.0
        
        # Exchange reliability scores (simplified)
        exchange_scores = {
            'kucoin': 15.0,
            'okx': 10.0,
            'binance': 5.0,
            'coinbase': 8.0
        }
        
        buy_exchange_risk = exchange_scores.get(opportunity.buy_exchange, 25.0)
        sell_exchange_risk = exchange_scores.get(opportunity.sell_exchange, 25.0)
        
        # Average exchange risk
        risk_score = (buy_exchange_risk + sell_exchange_risk) / 2
        
        # Same exchange risk (no true arbitrage)
        if opportunity.buy_exchange == opportunity.sell_exchange:
            risk_score += 50.0
        
        return min(risk_score, 100.0)
    
    def _calculate_correlation_risk(self, opportunity: ArbitrageOpportunity) -> float:
        """Calculate correlation risk with existing positions"""
        if not self.active_positions:
            return 10.0  # Low risk if no existing positions
        
        # Simple correlation based on asset class
        base_asset = opportunity.symbol.split('/')[0]
        
        # Count correlated positions
        correlated_exposure = 0.0
        for position in self.active_positions.values():
            position_base = position.symbol.split('/')[0]
            
            # High correlation assets
            if base_asset == position_base:
                correlated_exposure += position.position_size_usd
            elif self._are_correlated_assets(base_asset, position_base):
                correlated_exposure += position.position_size_usd * 0.7  # 70% correlation
        
        # Calculate correlation risk
        correlation_pct = correlated_exposure / max(self.current_exposure_usd, 1)
        
        if correlation_pct > 0.6:
            return 80.0  # High correlation risk
        elif correlation_pct > 0.4:
            return 50.0  # Medium correlation risk
        elif correlation_pct > 0.2:
            return 25.0  # Low-medium correlation risk
        else:
            return 10.0  # Low correlation risk
    
    def _are_correlated_assets(self, asset1: str, asset2: str) -> bool:
        """Check if two assets are correlated"""
        # Define correlation groups
        major_crypto = {'BTC', 'ETH'}
        defi_tokens = {'SNX', 'UNI', 'AAVE', 'COMP'}
        layer1_tokens = {'SOL', 'ADA', 'DOT', 'AVAX'}
        
        # Check if both assets are in the same group
        for group in [major_crypto, defi_tokens, layer1_tokens]:
            if asset1 in group and asset2 in group:
                return True
        
        return False
    
    def _make_risk_decision(self, overall_risk: float, risk_factors: Dict[str, float]) -> bool:
        """Make final risk approval decision"""
        # Check overall risk threshold
        if overall_risk > 70.0:
            return False
        
        # Check critical individual factors
        if risk_factors.get('liquidity', 0) > 80.0:
            return False
        
        if risk_factors.get('execution', 0) > 80.0:
            return False
        
        # Check daily loss limits
        if not self._check_daily_limits():
            return False
        
        # Check position size limits
        opportunity_size = risk_factors.get('position_size', 0)
        if opportunity_size > self.max_position_size_usd:
            return False
        
        return True
    
    def _check_daily_limits(self) -> bool:
        """Check if daily risk limits are exceeded"""
        current_date = time.strftime("%Y-%m-%d")
        
        # Reset daily counters if new day
        if current_date != self.last_reset_date:
            self.daily_loss_current = 0.0
            self.last_reset_date = current_date
        
        return self.daily_loss_current < self.max_daily_loss_usd
    
    def update_position_risk(self, symbol: str, exchange_pair: Tuple[str, str], 
                           position_size_usd: float, profit_loss: float):
        """Update risk metrics after position execution"""
        # Update daily P&L
        self.daily_loss_current += max(0, -profit_loss)  # Only count losses
        
        # Update exposure
        if profit_loss < 0:  # Position closed
            self.current_exposure_usd = max(0, self.current_exposure_usd - position_size_usd)
            # Remove from active positions
            position_key = f"{symbol}_{exchange_pair[0]}_{exchange_pair[1]}"
            if position_key in self.active_positions:
                del self.active_positions[position_key]
        else:  # Position opened
            self.current_exposure_usd += position_size_usd
            # Add to active positions
            position_key = f"{symbol}_{exchange_pair[0]}_{exchange_pair[1]}"
            self.active_positions[position_key] = PositionRisk(
                symbol=symbol,
                exchange_pair=exchange_pair,
                position_size_usd=position_size_usd,
                risk_score=0.0,  # Would be calculated
                risk_factors={},
                max_loss_estimate=position_size_usd * 0.05,  # 5% max loss estimate
                confidence_interval=(profit_loss * 0.8, profit_loss * 1.2)
            )
        
        # Store in history
        self.position_history.append({
            'symbol': symbol,
            'size_usd': position_size_usd,
            'pnl': profit_loss,
            'timestamp': int(time.time())
        })
    
    def calculate_portfolio_risk(self) -> RiskMetrics:
        """Calculate comprehensive portfolio risk metrics"""
        # Calculate individual risk components
        concentration_risk = self._calculate_portfolio_concentration_risk()
        correlation_risk = self._calculate_portfolio_correlation_risk()
        volatility_risk = self._calculate_portfolio_volatility_risk()
        liquidity_risk = self._calculate_portfolio_liquidity_risk()
        execution_risk = self._calculate_portfolio_execution_risk()
        exchange_risk = self._calculate_portfolio_exchange_risk()
        drawdown_risk = self._calculate_drawdown_risk()
        
        # Calculate overall risk score
        overall_risk = (
            concentration_risk * self.risk_weights['concentration'] +
            correlation_risk * self.risk_weights['correlation'] +
            volatility_risk * self.risk_weights['volatility'] +
            liquidity_risk * self.risk_weights['liquidity'] +
            execution_risk * self.risk_weights['execution'] +
            exchange_risk * self.risk_weights['exchange'] +
            drawdown_risk * self.risk_weights['drawdown']
        )
        
        # Determine risk level
        if overall_risk > 80:
            risk_level = RiskLevel.CRITICAL
        elif overall_risk > 60:
            risk_level = RiskLevel.HIGH
        elif overall_risk > 40:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # Calculate VaR (simplified)
        var_95 = self._calculate_var_95()
        
        risk_metrics = RiskMetrics(
            overall_risk_score=overall_risk,
            risk_level=risk_level,
            total_exposure_usd=self.current_exposure_usd,
            concentration_risk=concentration_risk,
            correlation_risk=correlation_risk,
            volatility_risk=volatility_risk,
            liquidity_risk=liquidity_risk,
            spread_risk=0.0,  # Would be calculated from current opportunities
            execution_risk=execution_risk,
            exchange_risk=exchange_risk,
            technical_risk=0.0,  # Would include system/network risks
            drawdown_risk=drawdown_risk,
            var_95=var_95,
            daily_loss_limit=self.max_daily_loss_usd,
            position_size_limit=self.max_position_size_usd,
            correlation_limit=self.max_correlation_exposure,
            timestamp=int(time.time())
        )
        
        # Store in history
        self.risk_history.append(risk_metrics)
        
        # Generate alerts if necessary
        self._check_risk_alerts(risk_metrics)
        
        return risk_metrics
    
    def _calculate_portfolio_concentration_risk(self) -> float:
        """Calculate portfolio concentration risk"""
        if not self.active_positions:
            return 0.0
        
        # Calculate concentration by symbol
        symbol_exposure = defaultdict(float)
        for position in self.active_positions.values():
            symbol_exposure[position.symbol] += position.position_size_usd
        
        # Find maximum concentration
        max_concentration = max(symbol_exposure.values()) if symbol_exposure else 0
        concentration_pct = max_concentration / max(self.current_exposure_usd, 1)
        
        # Convert to risk score
        if concentration_pct > 0.5:
            return 90.0
        elif concentration_pct > 0.3:
            return 60.0
        elif concentration_pct > 0.2:
            return 30.0
        else:
            return 10.0
    
    def _calculate_portfolio_correlation_risk(self) -> float:
        """Calculate portfolio correlation risk"""
        if len(self.active_positions) < 2:
            return 0.0
        
        # Simplified correlation calculation
        asset_groups = defaultdict(float)
        
        for position in self.active_positions.values():
            base_asset = position.symbol.split('/')[0]
            
            # Group by asset type
            if base_asset in ['BTC', 'ETH']:
                asset_groups['major'] += position.position_size_usd
            elif base_asset in ['SOL', 'ADA', 'DOT']:
                asset_groups['layer1'] += position.position_size_usd
            else:
                asset_groups['alt'] += position.position_size_usd
        
        # Calculate correlation risk
        max_group_exposure = max(asset_groups.values()) if asset_groups else 0
        correlation_pct = max_group_exposure / max(self.current_exposure_usd, 1)
        
        if correlation_pct > 0.7:
            return 80.0
        elif correlation_pct > 0.5:
            return 50.0
        elif correlation_pct > 0.3:
            return 25.0
        else:
            return 10.0
    
    def _calculate_portfolio_volatility_risk(self) -> float:
        """Calculate portfolio volatility risk"""
        if not self.active_positions:
            return 0.0
        
        # Weight-average volatility
        total_weighted_volatility = 0.0
        total_weight = 0.0
        
        for position in self.active_positions.values():
            volatility = self.volatility_data.get(position.symbol, 0.08)
            weight = position.position_size_usd
            
            total_weighted_volatility += volatility * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        avg_volatility = total_weighted_volatility / total_weight
        
        # Convert to risk score
        return min(avg_volatility * 500, 100)
    
    def _calculate_portfolio_liquidity_risk(self) -> float:
        """Calculate portfolio liquidity risk"""
        # This would analyze the liquidity of current positions
        # For now, return a simplified score
        return 20.0
    
    def _calculate_portfolio_execution_risk(self) -> float:
        """Calculate portfolio execution risk"""
        if not self.execution_times:
            return 30.0  # Default medium risk
        
        avg_execution_time = statistics.mean(self.execution_times)
        
        if avg_execution_time > 15.0:
            return 80.0
        elif avg_execution_time > 10.0:
            return 50.0
        elif avg_execution_time > 5.0:
            return 25.0
        else:
            return 10.0
    
    def _calculate_portfolio_exchange_risk(self) -> float:
        """Calculate portfolio exchange risk"""
        if not self.active_positions:
            return 0.0
        
        # Calculate exchange concentration
        exchange_exposure = defaultdict(float)
        
        for position in self.active_positions.values():
            for exchange in position.exchange_pair:
                exchange_exposure[exchange] += position.position_size_usd / 2  # Split between exchanges
        
        # Find maximum exchange exposure
        max_exposure = max(exchange_exposure.values()) if exchange_exposure else 0
        exposure_pct = max_exposure / max(self.current_exposure_usd, 1)
        
        if exposure_pct > 0.6:
            return 70.0
        elif exposure_pct > 0.4:
            return 40.0
        elif exposure_pct > 0.3:
            return 20.0
        else:
            return 10.0
    
    def _calculate_drawdown_risk(self) -> float:
        """Calculate drawdown risk"""
        if len(self.daily_pnl) < 5:
            return 20.0  # Default medium risk
        
        # Calculate maximum drawdown
        cumulative_pnl = []
        running_sum = 0
        
        for pnl in self.daily_pnl:
            running_sum += pnl
            cumulative_pnl.append(running_sum)
        
        if not cumulative_pnl:
            return 20.0
        
        peak = cumulative_pnl[0]
        max_drawdown = 0
        
        for value in cumulative_pnl:
            if value > peak:
                peak = value
            drawdown = (peak - value) / max(peak, 1)
            max_drawdown = max(max_drawdown, drawdown)
        
        # Convert to risk score
        if max_drawdown > 0.2:  # 20% drawdown
            return 90.0
        elif max_drawdown > 0.1:  # 10% drawdown
            return 60.0
        elif max_drawdown > 0.05:  # 5% drawdown
            return 30.0
        else:
            return 10.0
    
    def _calculate_var_95(self) -> float:
        """Calculate Value at Risk at 95% confidence level"""
        if len(self.daily_pnl) < 10:
            return self.current_exposure_usd * 0.05  # 5% of exposure
        
        # Sort daily P&L
        sorted_pnl = sorted(self.daily_pnl)
        
        # Get 5th percentile (95% VaR)
        var_index = int(len(sorted_pnl) * 0.05)
        var_95 = abs(sorted_pnl[var_index]) if var_index < len(sorted_pnl) else 0
        
        return var_95
    
    def _check_risk_alerts(self, risk_metrics: RiskMetrics):
        """Check for risk alerts and generate notifications"""
        alerts = []
        
        # Critical risk level
        if risk_metrics.risk_level == RiskLevel.CRITICAL:
            alerts.append(RiskAlert(
                level=RiskLevel.CRITICAL,
                category="Overall Risk",
                message=f"Critical risk level detected: {risk_metrics.overall_risk_score:.1f}",
                recommended_action="Stop all trading and review positions",
                timestamp=int(time.time())
            ))
        
        # High concentration
        if risk_metrics.concentration_risk > 70:
            alerts.append(RiskAlert(
                level=RiskLevel.HIGH,
                category="Concentration Risk",
                message=f"High concentration risk: {risk_metrics.concentration_risk:.1f}",
                recommended_action="Diversify positions across more symbols",
                timestamp=int(time.time())
            ))
        
        # High correlation
        if risk_metrics.correlation_risk > 70:
            alerts.append(RiskAlert(
                level=RiskLevel.HIGH,
                category="Correlation Risk",
                message=f"High correlation risk: {risk_metrics.correlation_risk:.1f}",
                recommended_action="Reduce correlated positions",
                timestamp=int(time.time())
            ))
        
        # Daily loss limit approaching
        if self.daily_loss_current > self.max_daily_loss_usd * 0.8:
            alerts.append(RiskAlert(
                level=RiskLevel.HIGH,
                category="Daily Loss Limit",
                message=f"Daily loss approaching limit: ${self.daily_loss_current:.2f}",
                recommended_action="Reduce position sizes or stop trading",
                timestamp=int(time.time())
            ))
        
        # Store alerts
        self.alert_history.extend(alerts)
        
        # Log critical alerts
        for alert in alerts:
            if alert.level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                logger.warning(f"RISK ALERT [{alert.level.value.upper()}] {alert.category}: {alert.message}")
    
    def get_risk_summary(self) -> Dict[str, any]:
        """Get comprehensive risk summary"""
        current_risk = self.calculate_portfolio_risk()
        
        return {
            'overall_risk_score': current_risk.overall_risk_score,
            'risk_level': current_risk.risk_level.value,
            'total_exposure_usd': current_risk.total_exposure_usd,
            'daily_loss_current': self.daily_loss_current,
            'daily_loss_limit': self.max_daily_loss_usd,
            'active_positions': len(self.active_positions),
            'recent_alerts': len([a for a in self.alert_history if int(time.time()) - a.timestamp < 3600]),
            'var_95': current_risk.var_95,
            'risk_factors': {
                'concentration': current_risk.concentration_risk,
                'correlation': current_risk.correlation_risk,
                'volatility': current_risk.volatility_risk,
                'execution': current_risk.execution_risk,
                'exchange': current_risk.exchange_risk,
                'drawdown': current_risk.drawdown_risk
            }
        }

    def update_risk_metrics(self):
        """Update risk metrics for monitoring"""
        try:
            # Calculate current portfolio metrics
            current_time = time.time()

            # Update daily P&L tracking
            if self.daily_pnl:
                daily_return = sum(self.daily_pnl.values())
                self.daily_returns.append(daily_return)

                # Keep only last 30 days
                if len(self.daily_returns) > 30:
                    self.daily_returns = self.daily_returns[-30:]

            # Update volatility metrics
            if len(self.daily_returns) >= 2:
                returns_array = np.array(self.daily_returns)
                self.portfolio_volatility = np.std(returns_array) * np.sqrt(252)  # Annualized

            # Update drawdown
            if self.daily_returns:
                cumulative_returns = np.cumsum(self.daily_returns)
                running_max = np.maximum.accumulate(cumulative_returns)
                drawdowns = (cumulative_returns - running_max) / np.maximum(running_max, 1)
                self.max_drawdown = abs(np.min(drawdowns)) if len(drawdowns) > 0 else 0.0

            # Update Sharpe ratio
            if len(self.daily_returns) >= 2:
                mean_return = np.mean(self.daily_returns)
                std_return = np.std(self.daily_returns)
                if std_return > 0:
                    self.sharpe_ratio = (mean_return / std_return) * np.sqrt(252)

            logger.debug(f"Risk metrics updated: volatility={self.portfolio_volatility:.4f}, "
                        f"drawdown={self.max_drawdown:.4f}, sharpe={self.sharpe_ratio:.4f}")

        except Exception as e:
            logger.error(f"Error updating risk metrics: {e}")
