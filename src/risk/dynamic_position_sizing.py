#!/usr/bin/env python3
"""
Dynamic Position Sizing System for CEX Arbitrage Bot
Features: Kelly Criterion, ML-enhanced sizing, volatility adjustment
"""

import math
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger


@dataclass
class PositionSizeParams:
    """Parameters for position sizing calculation"""
    base_capital: float
    max_position_pct: float = 0.05  # 5% max position size
    kelly_fraction: float = 0.25    # Max Kelly fraction
    volatility_adjustment: bool = True
    ml_confidence_weight: float = 0.3
    risk_score_weight: float = 0.4
    success_rate_weight: float = 0.3


class DynamicPositionSizing:
    """Dynamic position sizing system with multiple algorithms"""
    
    def __init__(self, base_capital: float = 10000.0):
        self.base_capital = base_capital
        self.current_capital = base_capital
        self.params = PositionSizeParams(base_capital)
        self.volatility_cache: Dict[str, float] = {}
        self.success_rates: Dict[str, float] = {}
        self.ml_integration = None
        
        logger.info(f"💰 Dynamic Position Sizing initialized with ${base_capital:,.2f}")
    
    def set_ml_integration(self, ml_integration):
        """Set ML integration for enhanced sizing"""
        self.ml_integration = ml_integration
        logger.info("🧠 ML integration enabled for position sizing")
    
    def update_capital(self, new_capital: float):
        """Update current capital"""
        self.current_capital = new_capital
        logger.info(f"💰 Capital updated to ${new_capital:,.2f}")
    
    async def calculate_position_size(self, opportunity: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate optimal position size using multiple methods
        Returns: (position_size, sizing_details)
        """
        try:
            symbol = opportunity.get('symbol', 'UNKNOWN')
            strategy = opportunity.get('strategy', 'unknown')
            profit_pct = opportunity.get('profit_percentage', 0.0) / 100.0
            
            # Get base parameters
            sizing_details = {
                'method': 'dynamic_multi_factor',
                'symbol': symbol,
                'strategy': strategy,
                'profit_pct': profit_pct,
                'timestamp': datetime.now().isoformat()
            }
            
            # 1. Kelly Criterion sizing
            kelly_size = await self._calculate_kelly_size(opportunity, sizing_details)
            
            # 2. Volatility-adjusted sizing
            volatility_size = await self._calculate_volatility_adjusted_size(opportunity, sizing_details)
            
            # 3. ML-enhanced sizing
            ml_size = await self._calculate_ml_enhanced_size(opportunity, sizing_details)
            
            # 4. Risk-adjusted sizing
            risk_size = await self._calculate_risk_adjusted_size(opportunity, sizing_details)
            
            # Combine all methods with weights
            combined_size = (
                kelly_size * 0.3 +
                volatility_size * 0.25 +
                ml_size * 0.25 +
                risk_size * 0.2
            )
            
            # Apply final constraints
            final_size = await self._apply_constraints(combined_size, opportunity, sizing_details)
            
            sizing_details.update({
                'kelly_size': kelly_size,
                'volatility_size': volatility_size,
                'ml_size': ml_size,
                'risk_size': risk_size,
                'combined_size': combined_size,
                'final_size': final_size,
                'size_pct_of_capital': final_size / self.current_capital * 100
            })
            
            logger.info(f"💰 Position size for {symbol}: ${final_size:.2f} ({final_size/self.current_capital*100:.2f}% of capital)")
            
            return final_size, sizing_details
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            # Fallback to conservative size
            fallback_size = self.current_capital * 0.01  # 1% of capital
            return fallback_size, {'error': str(e), 'fallback_size': fallback_size}
    
    async def _calculate_kelly_size(self, opportunity: Dict[str, Any], details: Dict[str, Any]) -> float:
        """Calculate position size using Kelly Criterion"""
        try:
            symbol = opportunity.get('symbol', '')
            strategy = opportunity.get('strategy', '')
            profit_pct = opportunity.get('profit_percentage', 0.0) / 100.0
            
            # Get historical success rate for this strategy/symbol
            success_rate = self.success_rates.get(f"{strategy}_{symbol}", 0.6)  # Default 60%
            
            # Estimate loss percentage (typically stop-loss level)
            loss_pct = 0.02  # 2% default stop-loss
            
            # Kelly formula: f = (bp - q) / b
            # where b = profit ratio, p = win probability, q = loss probability
            if profit_pct > 0:
                kelly_fraction = (profit_pct * success_rate - (1 - success_rate)) / profit_pct
                kelly_fraction = max(0, min(kelly_fraction, self.params.kelly_fraction))
            else:
                kelly_fraction = 0
            
            kelly_size = kelly_fraction * self.current_capital
            
            details['kelly_fraction'] = kelly_fraction
            details['success_rate'] = success_rate
            details['loss_pct'] = loss_pct
            
            return kelly_size
            
        except Exception as e:
            logger.error(f"Error in Kelly sizing: {e}")
            return self.current_capital * 0.01
    
    async def _calculate_volatility_adjusted_size(self, opportunity: Dict[str, Any], details: Dict[str, Any]) -> float:
        """Calculate volatility-adjusted position size"""
        try:
            symbol = opportunity.get('symbol', '')
            
            # Get volatility for the symbol
            volatility = self.volatility_cache.get(symbol, 0.02)  # Default 2% daily volatility
            
            # Base size (2% of capital)
            base_size = self.current_capital * 0.02
            
            # Adjust for volatility (inverse relationship)
            # Higher volatility = smaller position
            volatility_adjustment = 1.0 / (1.0 + volatility * 10)
            
            volatility_size = base_size * volatility_adjustment
            
            details['volatility'] = volatility
            details['volatility_adjustment'] = volatility_adjustment
            
            return volatility_size
            
        except Exception as e:
            logger.error(f"Error in volatility sizing: {e}")
            return self.current_capital * 0.01
    
    async def _calculate_ml_enhanced_size(self, opportunity: Dict[str, Any], details: Dict[str, Any]) -> float:
        """Calculate ML-enhanced position size"""
        try:
            if not self.ml_integration:
                return self.current_capital * 0.02  # Default 2%
            
            symbol = opportunity.get('symbol', '')
            prediction = await self.ml_integration.get_ml_prediction(symbol)
            
            if not prediction:
                return self.current_capital * 0.02
            
            # Use ML confidence and risk score
            confidence = prediction.confidence_score / 100.0
            risk_score = prediction.risk_score / 10.0  # Normalize to 0-1
            
            # Higher confidence and lower risk = larger position
            ml_factor = confidence * (1.0 - risk_score)
            ml_factor = max(0.1, min(ml_factor, 1.0))  # Clamp between 10% and 100%
            
            # Base size adjusted by ML factor
            base_size = self.current_capital * 0.03
            ml_size = base_size * ml_factor
            
            details['ml_confidence'] = confidence
            details['ml_risk_score'] = risk_score
            details['ml_factor'] = ml_factor
            
            return ml_size
            
        except Exception as e:
            logger.error(f"Error in ML sizing: {e}")
            return self.current_capital * 0.02
    
    async def _calculate_risk_adjusted_size(self, opportunity: Dict[str, Any], details: Dict[str, Any]) -> float:
        """Calculate risk-adjusted position size"""
        try:
            strategy = opportunity.get('strategy', 'unknown')
            profit_pct = opportunity.get('profit_percentage', 0.0)
            execution_time = opportunity.get('execution_time_ms', 1000)
            
            # Strategy risk factors
            strategy_risk = {
                'cross_exchange': 0.8,    # Lower risk
                'triangular': 0.6,       # Medium risk
                'funding': 0.7,          # Medium-low risk
                'statistical': 0.5       # Higher risk
            }.get(strategy, 0.4)
            
            # Profit factor (higher profit = larger size)
            profit_factor = min(1.0, profit_pct / 0.5)  # Normalize to 0.5% profit
            
            # Execution time factor (faster = larger size)
            time_factor = max(0.5, 1.0 - (execution_time - 500) / 2000)
            
            # Combined risk factor
            risk_factor = strategy_risk * profit_factor * time_factor
            risk_factor = max(0.1, min(risk_factor, 1.0))
            
            # Base size adjusted by risk
            base_size = self.current_capital * 0.025
            risk_size = base_size * risk_factor
            
            details['strategy_risk'] = strategy_risk
            details['profit_factor'] = profit_factor
            details['time_factor'] = time_factor
            details['risk_factor'] = risk_factor
            
            return risk_size
            
        except Exception as e:
            logger.error(f"Error in risk sizing: {e}")
            return self.current_capital * 0.01
    
    async def _apply_constraints(self, size: float, opportunity: Dict[str, Any], details: Dict[str, Any]) -> float:
        """Apply final constraints to position size"""
        try:
            # Maximum position size constraint
            max_size = self.current_capital * self.params.max_position_pct
            size = min(size, max_size)
            
            # Minimum viable size
            min_size = 10.0  # $10 minimum
            size = max(size, min_size)
            
            # Round to reasonable precision
            size = round(size, 2)
            
            details['max_size_constraint'] = max_size
            details['min_size_constraint'] = min_size
            details['constraints_applied'] = True
            
            return size
            
        except Exception as e:
            logger.error(f"Error applying constraints: {e}")
            return 10.0  # Fallback minimum
    
    def update_success_rate(self, strategy: str, symbol: str, success: bool):
        """Update success rate for strategy/symbol combination"""
        key = f"{strategy}_{symbol}"
        
        if key not in self.success_rates:
            self.success_rates[key] = 0.6  # Default
        
        # Exponential moving average update
        alpha = 0.1  # Learning rate
        current_rate = self.success_rates[key]
        new_rate = current_rate * (1 - alpha) + (1.0 if success else 0.0) * alpha
        
        self.success_rates[key] = new_rate
        logger.info(f"📊 Success rate updated for {key}: {new_rate:.2%}")
    
    def update_volatility(self, symbol: str, volatility: float):
        """Update volatility estimate for symbol"""
        self.volatility_cache[symbol] = volatility
        logger.debug(f"📈 Volatility updated for {symbol}: {volatility:.4f}")
    
    def get_sizing_statistics(self) -> Dict[str, Any]:
        """Get position sizing statistics"""
        return {
            'current_capital': self.current_capital,
            'base_capital': self.base_capital,
            'max_position_pct': self.params.max_position_pct,
            'kelly_fraction_limit': self.params.kelly_fraction,
            'tracked_symbols': len(self.volatility_cache),
            'success_rates': dict(self.success_rates),
            'volatility_cache': dict(self.volatility_cache),
            'ml_enabled': self.ml_integration is not None
        }
