#!/usr/bin/env python3
"""
Strategy Manager
Coordinates multiple trading strategies and manages execution
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
from dataclasses import asdict

from .multi_strategy_engine import MultiStrategyEngine, TriangularOpportunity, FundingOpportunity, StatisticalOpportunity

class StrategyManager:
    """Manages and coordinates multiple trading strategies"""
    
    def __init__(self, exchange_manager):
        self.exchange_manager = exchange_manager
        self.multi_strategy_engine = MultiStrategyEngine(exchange_manager)
        
        # Strategy execution tracking
        self.execution_history = []
        self.strategy_performance = {
            'triangular': {'executions': 0, 'profit': 0.0, 'success_rate': 0.0},
            'funding': {'executions': 0, 'profit': 0.0, 'success_rate': 0.0},
            'statistical': {'executions': 0, 'profit': 0.0, 'success_rate': 0.0},
            'cross_exchange': {'executions': 0, 'profit': 0.0, 'success_rate': 0.0}
        }
        
        # Risk management
        self.max_concurrent_strategies = 3
        self.active_executions = {}
        self.daily_loss_limit = 1000.0
        self.daily_loss_current = 0.0
        
        logger.info("🎯 Strategy Manager initialized")
    
    async def scan_all_opportunities(self) -> Dict[str, List[Dict]]:
        """Scan for opportunities across all strategies"""
        try:
            # Get opportunities from multi-strategy engine
            opportunities = await self.multi_strategy_engine.scan_all_strategies()
            
            # Convert to serializable format
            serialized_opportunities = {}
            
            for strategy_name, strategy_opportunities in opportunities.items():
                serialized_opportunities[strategy_name] = []
                
                for opportunity in strategy_opportunities:
                    if hasattr(opportunity, '__dict__'):
                        # Convert dataclass to dict
                        opp_dict = asdict(opportunity)
                        opp_dict['strategy'] = strategy_name
                        opp_dict['timestamp'] = datetime.now().isoformat()
                        serialized_opportunities[strategy_name].append(opp_dict)
                    elif isinstance(opportunity, dict):
                        # Already a dict
                        opportunity['strategy'] = strategy_name
                        opportunity['timestamp'] = datetime.now().isoformat()
                        serialized_opportunities[strategy_name].append(opportunity)
            
            return serialized_opportunities
            
        except Exception as e:
            logger.error(f"Strategy scan error: {e}")
            return {}
    
    async def execute_best_opportunity(self) -> Dict[str, Any]:
        """Find and execute the best available opportunity"""
        try:
            # Check if we can execute more strategies
            if len(self.active_executions) >= self.max_concurrent_strategies:
                return {
                    'success': False,
                    'error': 'Maximum concurrent strategies reached',
                    'active_count': len(self.active_executions)
                }
            
            # Check daily loss limit
            if self.daily_loss_current >= self.daily_loss_limit:
                return {
                    'success': False,
                    'error': 'Daily loss limit reached',
                    'daily_loss': self.daily_loss_current
                }
            
            # Get all opportunities
            opportunities = await self.scan_all_opportunities()
            
            # Find best opportunity across all strategies
            best_opportunity = self._select_best_opportunity(opportunities)
            
            if not best_opportunity:
                return {
                    'success': False,
                    'error': 'No profitable opportunities found'
                }
            
            # Execute the opportunity
            result = await self._execute_opportunity(best_opportunity)
            
            return result
            
        except Exception as e:
            logger.error(f"Opportunity execution error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _select_best_opportunity(self, opportunities: Dict[str, List[Dict]]) -> Optional[Dict]:
        """Select the best opportunity across all strategies"""
        best_opportunity = None
        best_score = 0
        
        for strategy_name, strategy_opportunities in opportunities.items():
            for opportunity in strategy_opportunities:
                # Calculate opportunity score
                score = self._calculate_opportunity_score(opportunity, strategy_name)
                
                if score > best_score:
                    best_score = score
                    best_opportunity = opportunity
        
        return best_opportunity
    
    def _calculate_opportunity_score(self, opportunity: Dict, strategy_name: str) -> float:
        """Calculate a score for ranking opportunities"""
        try:
            # Base score from profit percentage
            profit_pct = opportunity.get('profit_percentage', 0)
            base_score = profit_pct * 10
            
            # Risk adjustment
            risk_score = opportunity.get('risk_score', 5.0)
            risk_adjustment = max(0, (10 - risk_score) / 10)
            
            # Strategy performance bonus
            strategy_perf = self.strategy_performance.get(strategy_name, {})
            success_rate = strategy_perf.get('success_rate', 0.5)
            performance_bonus = success_rate * 2
            
            # Execution time penalty (faster is better)
            execution_time = opportunity.get('execution_time', 3.0)
            time_penalty = max(0, execution_time - 1.0)
            
            # Final score
            final_score = (base_score * risk_adjustment + performance_bonus - time_penalty)
            
            return max(0, final_score)
            
        except Exception as e:
            logger.error(f"Score calculation error: {e}")
            return 0
    
    async def _execute_opportunity(self, opportunity: Dict) -> Dict[str, Any]:
        """Execute a trading opportunity"""
        strategy_name = opportunity.get('strategy', 'unknown')
        execution_id = f"{strategy_name}_{datetime.now().timestamp()}"
        
        try:
            # Add to active executions
            self.active_executions[execution_id] = {
                'strategy': strategy_name,
                'opportunity': opportunity,
                'start_time': datetime.now(),
                'status': 'executing'
            }
            
            # Execute based on strategy type
            if strategy_name == 'triangular':
                result = await self._execute_triangular_arbitrage(opportunity)
            elif strategy_name == 'funding':
                result = await self._execute_funding_arbitrage(opportunity)
            elif strategy_name == 'statistical':
                result = await self._execute_statistical_arbitrage(opportunity)
            elif strategy_name == 'cross_exchange':
                result = await self._execute_cross_exchange_arbitrage(opportunity)
            else:
                result = {
                    'success': False,
                    'error': f'Unknown strategy: {strategy_name}'
                }
            
            # Update execution tracking
            self._update_execution_tracking(execution_id, result)
            
            # Remove from active executions
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
            
            return result
            
        except Exception as e:
            logger.error(f"Execution error for {strategy_name}: {e}")
            
            # Clean up
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
            
            return {
                'success': False,
                'error': str(e),
                'strategy': strategy_name
            }
    
    async def _execute_triangular_arbitrage(self, opportunity: Dict) -> Dict[str, Any]:
        """Execute triangular arbitrage (simulation)"""
        try:
            # Simulate triangular arbitrage execution
            path = opportunity.get('path', [])
            expected_profit = opportunity.get('expected_profit', 0)
            
            # Simulate execution delay
            await asyncio.sleep(2.5)
            
            # Simulate success/failure (90% success rate for triangular)
            import random
            success = random.random() > 0.1
            
            if success:
                actual_profit = expected_profit * random.uniform(0.8, 1.2)
                return {
                    'success': True,
                    'strategy': 'triangular',
                    'path': path,
                    'expected_profit': expected_profit,
                    'actual_profit': actual_profit,
                    'execution_time': 2.5
                }
            else:
                loss = expected_profit * 0.1  # Small loss on failure
                return {
                    'success': False,
                    'strategy': 'triangular',
                    'error': 'Execution failed due to price movement',
                    'loss': loss
                }
                
        except Exception as e:
            return {
                'success': False,
                'strategy': 'triangular',
                'error': str(e)
            }
    
    async def _execute_funding_arbitrage(self, opportunity: Dict) -> Dict[str, Any]:
        """Execute funding rate arbitrage (simulation)"""
        try:
            symbol = opportunity.get('symbol', '')
            expected_profit = opportunity.get('expected_profit', 0)
            
            # Simulate execution delay
            await asyncio.sleep(1.5)
            
            # Simulate success/failure (85% success rate for funding)
            import random
            success = random.random() > 0.15
            
            if success:
                actual_profit = expected_profit * random.uniform(0.9, 1.1)
                return {
                    'success': True,
                    'strategy': 'funding',
                    'symbol': symbol,
                    'expected_profit': expected_profit,
                    'actual_profit': actual_profit,
                    'execution_time': 1.5
                }
            else:
                loss = expected_profit * 0.05
                return {
                    'success': False,
                    'strategy': 'funding',
                    'error': 'Funding rate changed during execution',
                    'loss': loss
                }
                
        except Exception as e:
            return {
                'success': False,
                'strategy': 'funding',
                'error': str(e)
            }
    
    async def _execute_statistical_arbitrage(self, opportunity: Dict) -> Dict[str, Any]:
        """Execute statistical arbitrage (simulation)"""
        try:
            pair_symbols = opportunity.get('pair_symbols', [])
            expected_profit = opportunity.get('expected_profit', 0)
            
            # Simulate execution delay
            await asyncio.sleep(3.0)
            
            # Simulate success/failure (75% success rate for statistical)
            import random
            success = random.random() > 0.25
            
            if success:
                actual_profit = expected_profit * random.uniform(0.7, 1.3)
                return {
                    'success': True,
                    'strategy': 'statistical',
                    'pair_symbols': pair_symbols,
                    'expected_profit': expected_profit,
                    'actual_profit': actual_profit,
                    'execution_time': 3.0
                }
            else:
                loss = expected_profit * 0.2
                return {
                    'success': False,
                    'strategy': 'statistical',
                    'error': 'Mean reversion did not occur',
                    'loss': loss
                }
                
        except Exception as e:
            return {
                'success': False,
                'strategy': 'statistical',
                'error': str(e)
            }
    
    async def _execute_cross_exchange_arbitrage(self, opportunity: Dict) -> Dict[str, Any]:
        """Execute cross-exchange arbitrage (simulation)"""
        try:
            symbol = opportunity.get('symbol', '')
            expected_profit = opportunity.get('net_profit', 0)
            
            # Simulate execution delay
            await asyncio.sleep(2.0)
            
            # Simulate success/failure (95% success rate for cross-exchange)
            import random
            success = random.random() > 0.05
            
            if success:
                actual_profit = expected_profit * random.uniform(0.9, 1.1)
                return {
                    'success': True,
                    'strategy': 'cross_exchange',
                    'symbol': symbol,
                    'expected_profit': expected_profit,
                    'actual_profit': actual_profit,
                    'execution_time': 2.0
                }
            else:
                loss = expected_profit * 0.1
                return {
                    'success': False,
                    'strategy': 'cross_exchange',
                    'error': 'Price moved during execution',
                    'loss': loss
                }
                
        except Exception as e:
            return {
                'success': False,
                'strategy': 'cross_exchange',
                'error': str(e)
            }
    
    def _update_execution_tracking(self, execution_id: str, result: Dict):
        """Update execution tracking and performance metrics"""
        try:
            execution_info = self.active_executions.get(execution_id, {})
            strategy_name = execution_info.get('strategy', 'unknown')
            
            # Add to execution history
            self.execution_history.append({
                'execution_id': execution_id,
                'strategy': strategy_name,
                'timestamp': datetime.now(),
                'result': result
            })
            
            # Update strategy performance
            if strategy_name in self.strategy_performance:
                perf = self.strategy_performance[strategy_name]
                perf['executions'] += 1
                
                if result.get('success', False):
                    profit = result.get('actual_profit', 0)
                    perf['profit'] += profit
                else:
                    loss = result.get('loss', 0)
                    perf['profit'] -= loss
                    self.daily_loss_current += loss
                
                # Update success rate
                successful_executions = sum(1 for exec_info in self.execution_history 
                                          if exec_info['strategy'] == strategy_name 
                                          and exec_info['result'].get('success', False))
                perf['success_rate'] = successful_executions / perf['executions']
            
            # Keep only recent execution history
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-1000:]
                
        except Exception as e:
            logger.error(f"Execution tracking update error: {e}")
    
    def get_strategy_performance(self) -> Dict:
        """Get performance statistics for all strategies"""
        return {
            'strategy_performance': self.strategy_performance,
            'active_executions': len(self.active_executions),
            'total_executions': len(self.execution_history),
            'daily_loss_current': self.daily_loss_current,
            'daily_loss_limit': self.daily_loss_limit,
            'recent_executions': self.execution_history[-10:] if self.execution_history else []
        }
    
    def reset_daily_metrics(self):
        """Reset daily tracking metrics"""
        self.daily_loss_current = 0.0
        logger.info("Daily metrics reset")
    
    def set_strategy_enabled(self, strategy_name: str, enabled: bool):
        """Enable or disable a specific strategy"""
        self.multi_strategy_engine.enable_strategy(strategy_name, enabled)
    
    def set_profit_threshold(self, strategy_name: str, threshold: float):
        """Set profit threshold for a strategy"""
        self.multi_strategy_engine.set_profit_threshold(strategy_name, threshold)
