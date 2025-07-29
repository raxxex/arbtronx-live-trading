#!/usr/bin/env python3
"""
Portfolio Risk Monitor - Integrated Risk Management System
Features: Real-time monitoring, ML-enhanced risk assessment, automated actions
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
from loguru import logger

try:
    from .advanced_risk_manager import AdvancedRiskManager, RiskLevel
except ImportError:
    # Fallback if advanced risk manager is not available
    AdvancedRiskManager = None
    class RiskLevel(Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"
from .dynamic_position_sizing import DynamicPositionSizing
from .stop_loss_manager import StopLossManager


class RiskAction(Enum):
    """Risk management actions"""
    NONE = "none"
    REDUCE_POSITION = "reduce_position"
    CLOSE_POSITION = "close_position"
    STOP_TRADING = "stop_trading"
    EMERGENCY_EXIT = "emergency_exit"
    INCREASE_MONITORING = "increase_monitoring"


@dataclass
class RiskAlert:
    """Risk alert structure"""
    alert_id: str
    level: RiskLevel
    category: str
    message: str
    recommended_action: RiskAction
    affected_positions: List[str]
    timestamp: datetime
    acknowledged: bool = False


@dataclass
class PortfolioSnapshot:
    """Portfolio risk snapshot"""
    timestamp: datetime
    total_capital: float
    total_exposure: float
    unrealized_pnl: float
    daily_pnl: float
    active_positions: int
    risk_score: float
    risk_level: RiskLevel
    var_95: float
    max_drawdown: float
    concentration_risk: float
    correlation_risk: float


class PortfolioRiskMonitor:
    """Integrated portfolio risk monitoring system"""
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # Initialize risk management components
        if AdvancedRiskManager:
            self.risk_manager = AdvancedRiskManager()
        else:
            self.risk_manager = None
        self.position_sizer = DynamicPositionSizing(initial_capital)
        self.stop_manager = StopLossManager()
        
        # Risk monitoring state
        self.active_alerts: Dict[str, RiskAlert] = {}
        self.alert_history: List[RiskAlert] = []
        self.portfolio_snapshots: List[PortfolioSnapshot] = []
        self.monitoring_active = False
        self.emergency_mode = False
        
        # Configuration
        self.monitoring_interval = 5  # seconds
        self.snapshot_interval = 60   # seconds
        self.max_alerts = 100
        
        # ML integration
        self.ml_integration = None
        
        logger.info(f"🛡️ Portfolio Risk Monitor initialized with ${initial_capital:,.2f}")
    
    def set_ml_integration(self, ml_integration):
        """Set ML integration for all risk components"""
        self.ml_integration = ml_integration
        if self.risk_manager and hasattr(self.risk_manager, 'set_ml_integration'):
            self.risk_manager.set_ml_integration(ml_integration)
        self.position_sizer.set_ml_integration(ml_integration)
        self.stop_manager.set_ml_integration(ml_integration)
        logger.info("🧠 ML integration enabled for portfolio risk monitoring")
    
    async def start_monitoring(self):
        """Start real-time risk monitoring"""
        if self.monitoring_active:
            logger.warning("Risk monitoring already active")
            return
        
        self.monitoring_active = True
        logger.info("🚀 Starting portfolio risk monitoring")
        
        # Start monitoring tasks
        asyncio.create_task(self._risk_monitoring_loop())
        asyncio.create_task(self._snapshot_loop())
        asyncio.create_task(self._alert_management_loop())
    
    async def stop_monitoring(self):
        """Stop risk monitoring"""
        self.monitoring_active = False
        logger.info("⏹️ Portfolio risk monitoring stopped")
    
    async def assess_new_opportunity(self, opportunity: Dict[str, Any]) -> Tuple[bool, float, float, str]:
        """
        Comprehensive assessment of new trading opportunity
        Returns: (approved, risk_score, position_size, reason)
        """
        try:
            symbol = opportunity.get('symbol', 'UNKNOWN')

            # 1. Risk assessment
            if self.risk_manager and hasattr(self.risk_manager, 'assess_opportunity_risk'):
                approved, risk_score, risk_reason = await self.risk_manager.assess_opportunity_risk(opportunity)
            else:
                # Fallback risk assessment
                approved, risk_score, risk_reason = True, 5.0, "Basic risk assessment - approved"

            if not approved:
                return False, risk_score, 0.0, risk_reason
            
            # 2. Position sizing
            position_size, sizing_details = await self.position_sizer.calculate_position_size(opportunity)
            
            # 3. Final portfolio checks
            portfolio_check = await self._final_portfolio_check(opportunity, position_size)
            
            if not portfolio_check['approved']:
                return False, risk_score, 0.0, portfolio_check['reason']
            
            logger.info(f"✅ Opportunity approved: {symbol} - Size: ${position_size:.2f}, Risk: {risk_score:.2f}")
            
            return True, risk_score, position_size, "Opportunity approved"
            
        except Exception as e:
            logger.error(f"Error assessing opportunity: {e}")
            return False, 10.0, 0.0, f"Assessment error: {str(e)}"
    
    async def create_position_protection(self, 
                                       position_id: str,
                                       symbol: str,
                                       entry_price: float,
                                       position_size: float,
                                       is_long: bool) -> str:
        """Create comprehensive position protection (stop-loss, take-profit)"""
        try:
            # Create stop-loss order
            stop_order_id = await self.stop_manager.create_stop_loss(
                position_id=position_id,
                symbol=symbol,
                entry_price=entry_price,
                position_size=position_size,
                is_long=is_long
            )
            
            logger.info(f"🛡️ Position protection created for {symbol}: {stop_order_id}")
            
            return stop_order_id
            
        except Exception as e:
            logger.error(f"Error creating position protection: {e}")
            raise
    
    async def update_market_data(self, price_updates: Dict[str, float]):
        """Update market data for all risk components"""
        try:
            # Update stop-loss manager
            triggered_orders = await self.stop_manager.update_stops(price_updates)
            
            # Process triggered orders
            for order in triggered_orders:
                await self._handle_triggered_order(order)
            
            # Update volatility estimates
            for symbol, price in price_updates.items():
                await self._update_volatility_estimate(symbol, price)
            
        except Exception as e:
            logger.error(f"Error updating market data: {e}")
    
    async def _risk_monitoring_loop(self):
        """Main risk monitoring loop"""
        while self.monitoring_active:
            try:
                # Update risk metrics
                risk_metrics = await self.risk_manager.update_risk_metrics()
                
                # Check for new alerts
                await self._check_risk_alerts(risk_metrics)
                
                # Check emergency conditions
                await self._check_emergency_conditions(risk_metrics)
                
                # Monitor positions
                position_actions = await self.risk_manager.monitor_positions()
                for action in position_actions:
                    await self._execute_risk_action(action)
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in risk monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _snapshot_loop(self):
        """Portfolio snapshot loop"""
        while self.monitoring_active:
            try:
                await self._take_portfolio_snapshot()
                await asyncio.sleep(self.snapshot_interval)
            except Exception as e:
                logger.error(f"Error in snapshot loop: {e}")
                await asyncio.sleep(self.snapshot_interval)
    
    async def _alert_management_loop(self):
        """Alert management loop"""
        while self.monitoring_active:
            try:
                # Clean up old alerts
                await self._cleanup_old_alerts()
                
                # Process active alerts
                await self._process_active_alerts()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in alert management loop: {e}")
                await asyncio.sleep(30)
    
    async def _final_portfolio_check(self, opportunity: Dict[str, Any], position_size: float) -> Dict[str, Any]:
        """Final portfolio-level checks before opening position"""
        try:
            # Check if we're in emergency mode
            if self.emergency_mode:
                return {'approved': False, 'reason': 'Emergency mode active - no new positions'}
            
            # Check maximum positions
            if len(self.risk_manager.positions) >= 10:
                return {'approved': False, 'reason': 'Maximum position limit reached (10)'}
            
            # Check capital utilization
            total_exposure = sum(abs(pos.size * pos.current_price) for pos in self.risk_manager.positions.values())
            new_exposure = total_exposure + position_size
            utilization = new_exposure / self.current_capital
            
            if utilization > 0.8:  # 80% max utilization
                return {'approved': False, 'reason': f'Capital utilization too high: {utilization:.1%}'}
            
            # Check correlation limits
            symbol = opportunity.get('symbol', '')
            correlation_risk = await self._check_correlation_risk(symbol)
            if correlation_risk > 0.7:
                return {'approved': False, 'reason': f'Correlation risk too high: {correlation_risk:.1%}'}
            
            return {'approved': True, 'reason': 'All checks passed'}
            
        except Exception as e:
            logger.error(f"Error in final portfolio check: {e}")
            return {'approved': False, 'reason': f'Check error: {str(e)}'}
    
    async def _check_risk_alerts(self, risk_metrics):
        """Check for new risk alerts"""
        try:
            alerts = []
            
            # High risk score alert
            if risk_metrics.overall_risk_score > 8.0:
                alerts.append(RiskAlert(
                    alert_id=f"high_risk_{int(time.time())}",
                    level=RiskLevel.HIGH,
                    category="Portfolio Risk",
                    message=f"High portfolio risk detected: {risk_metrics.overall_risk_score:.1f}/10",
                    recommended_action=RiskAction.REDUCE_POSITION,
                    affected_positions=list(self.risk_manager.positions.keys()),
                    timestamp=datetime.now()
                ))
            
            # High exposure alert
            exposure_pct = risk_metrics.portfolio_exposure
            if exposure_pct > 0.7:  # 70% exposure
                alerts.append(RiskAlert(
                    alert_id=f"high_exposure_{int(time.time())}",
                    level=RiskLevel.MEDIUM,
                    category="Portfolio Exposure",
                    message=f"High portfolio exposure: {exposure_pct:.1%}",
                    recommended_action=RiskAction.REDUCE_POSITION,
                    affected_positions=[],
                    timestamp=datetime.now()
                ))
            
            # Drawdown alert
            if risk_metrics.max_drawdown > 0.05:  # 5% drawdown
                alerts.append(RiskAlert(
                    alert_id=f"drawdown_{int(time.time())}",
                    level=RiskLevel.HIGH,
                    category="Drawdown",
                    message=f"Significant drawdown: {risk_metrics.max_drawdown:.1%}",
                    recommended_action=RiskAction.STOP_TRADING,
                    affected_positions=[],
                    timestamp=datetime.now()
                ))
            
            # Add new alerts
            for alert in alerts:
                self.active_alerts[alert.alert_id] = alert
                logger.warning(f"🚨 NEW ALERT [{alert.level.value}] {alert.category}: {alert.message}")
            
        except Exception as e:
            logger.error(f"Error checking risk alerts: {e}")
    
    async def _check_emergency_conditions(self, risk_metrics):
        """Check for emergency conditions"""
        try:
            emergency_triggers = []
            
            # Critical risk score
            if risk_metrics.overall_risk_score > 9.0:
                emergency_triggers.append("Critical risk score")
            
            # Extreme drawdown
            if risk_metrics.max_drawdown > 0.1:  # 10% drawdown
                emergency_triggers.append("Extreme drawdown")
            
            # Very high VaR
            if risk_metrics.var_95 > self.current_capital * 0.1:  # 10% of capital
                emergency_triggers.append("Extreme VaR")
            
            if emergency_triggers and not self.emergency_mode:
                self.emergency_mode = True
                logger.critical(f"🚨 EMERGENCY MODE ACTIVATED: {', '.join(emergency_triggers)}")
                
                # Create emergency alert
                emergency_alert = RiskAlert(
                    alert_id=f"emergency_{int(time.time())}",
                    level=RiskLevel.CRITICAL,
                    category="Emergency",
                    message=f"Emergency conditions detected: {', '.join(emergency_triggers)}",
                    recommended_action=RiskAction.EMERGENCY_EXIT,
                    affected_positions=list(self.risk_manager.positions.keys()),
                    timestamp=datetime.now()
                )
                
                self.active_alerts[emergency_alert.alert_id] = emergency_alert
            
        except Exception as e:
            logger.error(f"Error checking emergency conditions: {e}")
    
    async def _take_portfolio_snapshot(self):
        """Take portfolio risk snapshot"""
        try:
            risk_metrics = await self.risk_manager.update_risk_metrics()
            
            snapshot = PortfolioSnapshot(
                timestamp=datetime.now(),
                total_capital=self.current_capital,
                total_exposure=sum(abs(pos.size * pos.current_price) for pos in self.risk_manager.positions.values()),
                unrealized_pnl=sum(pos.unrealized_pnl for pos in self.risk_manager.positions.values()),
                daily_pnl=self.risk_manager.daily_pnl,
                active_positions=len(self.risk_manager.positions),
                risk_score=risk_metrics.overall_risk_score,
                risk_level=self._get_risk_level(risk_metrics.overall_risk_score),
                var_95=risk_metrics.var_95,
                max_drawdown=risk_metrics.max_drawdown,
                concentration_risk=risk_metrics.concentration_risk,
                correlation_risk=risk_metrics.correlation_risk
            )
            
            self.portfolio_snapshots.append(snapshot)
            
            # Keep only last 1440 snapshots (24 hours at 1-minute intervals)
            if len(self.portfolio_snapshots) > 1440:
                self.portfolio_snapshots = self.portfolio_snapshots[-1440:]
            
        except Exception as e:
            logger.error(f"Error taking portfolio snapshot: {e}")
    
    def _get_risk_level(self, risk_score: float) -> RiskLevel:
        """Convert risk score to risk level"""
        if risk_score >= 9.0:
            return RiskLevel.CRITICAL
        elif risk_score >= 7.0:
            return RiskLevel.HIGH
        elif risk_score >= 5.0:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def get_portfolio_status(self) -> Dict[str, Any]:
        """Get comprehensive portfolio status"""
        try:
            risk_metrics = await self.risk_manager.update_risk_metrics()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'monitoring_active': self.monitoring_active,
                'emergency_mode': self.emergency_mode,
                'capital': {
                    'initial': self.initial_capital,
                    'current': self.current_capital,
                    'daily_pnl': self.risk_manager.daily_pnl,
                    'unrealized_pnl': sum(pos.unrealized_pnl for pos in self.risk_manager.positions.values())
                },
                'risk': {
                    'overall_score': risk_metrics.overall_risk_score,
                    'level': self._get_risk_level(risk_metrics.overall_risk_score).value,
                    'var_95': risk_metrics.var_95,
                    'max_drawdown': risk_metrics.max_drawdown,
                    'portfolio_exposure': risk_metrics.portfolio_exposure
                },
                'positions': {
                    'active_count': len(self.risk_manager.positions),
                    'active_stops': len(self.stop_manager.active_stops),
                    'total_exposure': sum(abs(pos.size * pos.current_price) for pos in self.risk_manager.positions.values())
                },
                'alerts': {
                    'active_count': len(self.active_alerts),
                    'critical_count': len([a for a in self.active_alerts.values() if a.level == RiskLevel.CRITICAL]),
                    'high_count': len([a for a in self.active_alerts.values() if a.level == RiskLevel.HIGH])
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio status: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def _cleanup_old_alerts(self):
        """Clean up old alerts that are no longer relevant"""
        try:
            current_time = time.time()
            alert_lifetime = 3600  # 1 hour

            # Remove alerts older than alert_lifetime
            expired_alerts = []
            for alert_id, alert in self.active_alerts.items():
                if current_time - alert.timestamp > alert_lifetime:
                    expired_alerts.append(alert_id)

            for alert_id in expired_alerts:
                del self.active_alerts[alert_id]
                logger.debug(f"Cleaned up expired alert: {alert_id}")

            # Also clean up resolved alerts
            resolved_alerts = []
            for alert_id, alert in self.active_alerts.items():
                # Check if alert condition is still valid
                if alert.alert_type == "high_drawdown":
                    current_drawdown = abs(self.risk_manager.max_drawdown)
                    if current_drawdown < 0.05:  # 5% threshold
                        resolved_alerts.append(alert_id)
                elif alert.alert_type == "high_volatility":
                    current_vol = self.risk_manager.portfolio_volatility
                    if current_vol < 0.3:  # 30% threshold
                        resolved_alerts.append(alert_id)
                elif alert.alert_type == "position_limit":
                    total_exposure = sum(abs(pos.size * pos.current_price) for pos in self.risk_manager.positions.values())
                    if total_exposure < self.initial_capital * 0.8:  # 80% threshold
                        resolved_alerts.append(alert_id)

            for alert_id in resolved_alerts:
                del self.active_alerts[alert_id]
                logger.info(f"Resolved alert: {alert_id}")

        except Exception as e:
            logger.error(f"Error cleaning up alerts: {e}")
