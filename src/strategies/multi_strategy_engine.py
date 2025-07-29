#!/usr/bin/env python3
"""
Multi-Strategy Trading Engine
Implements multiple arbitrage strategies for enhanced profit opportunities
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger
import itertools

@dataclass
class TriangularOpportunity:
    """Triangular arbitrage opportunity"""
    path: List[str]  # e.g., ['BTC/USDT', 'ETH/BTC', 'ETH/USDT']
    exchanges: List[str]  # e.g., ['kucoin', 'okx', 'kucoin']
    prices: List[float]
    expected_profit: float
    profit_percentage: float
    execution_time: float
    risk_score: float
    volume_required: float

@dataclass
class FundingOpportunity:
    """Funding rate arbitrage opportunity"""
    symbol: str
    spot_exchange: str
    futures_exchange: str
    spot_price: float
    futures_price: float
    funding_rate: float
    funding_interval: int  # hours
    expected_profit: float
    profit_percentage: float
    risk_score: float
    position_size: float

@dataclass
class StatisticalOpportunity:
    """Statistical arbitrage opportunity"""
    pair_symbols: List[str]  # e.g., ['BTC/USDT', 'ETH/USDT']
    exchanges: List[str]
    correlation: float
    z_score: float
    mean_reversion_probability: float
    expected_profit: float
    profit_percentage: float
    risk_score: float
    position_sizes: List[float]

class MultiStrategyEngine:
    """Advanced multi-strategy trading engine"""
    
    def __init__(self, exchange_manager):
        self.exchange_manager = exchange_manager
        self.strategies_enabled = {
            'triangular': True,
            'funding': True,
            'statistical': True,
            'cross_exchange': True  # Original strategy
        }
        
        # Strategy parameters
        self.min_profit_thresholds = {
            'triangular': 0.1,      # 0.1% minimum profit
            'funding': 0.05,        # 0.05% minimum profit
            'statistical': 0.08,    # 0.08% minimum profit
            'cross_exchange': 0.15  # 0.15% minimum profit
        }
        
        # Risk limits
        self.max_risk_scores = {
            'triangular': 7.0,
            'funding': 6.0,
            'statistical': 8.0,
            'cross_exchange': 5.0
        }
        
        # Historical data for statistical arbitrage
        self.price_history = {}
        self.correlation_matrix = {}
        
        logger.info("🎯 Multi-Strategy Trading Engine initialized")
    
    async def scan_all_strategies(self) -> Dict[str, List]:
        """Scan for opportunities across all enabled strategies"""
        opportunities = {
            'triangular': [],
            'funding': [],
            'statistical': [],
            'cross_exchange': []
        }
        
        try:
            # Run all strategy scans concurrently
            tasks = []
            
            if self.strategies_enabled['triangular']:
                tasks.append(self._scan_triangular_arbitrage())
            
            if self.strategies_enabled['funding']:
                tasks.append(self._scan_funding_arbitrage())
            
            if self.strategies_enabled['statistical']:
                tasks.append(self._scan_statistical_arbitrage())
            
            if self.strategies_enabled['cross_exchange']:
                tasks.append(self._scan_cross_exchange_arbitrage())
            
            # Execute all scans
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            strategy_names = [name for name, enabled in self.strategies_enabled.items() if enabled]
            for i, result in enumerate(results):
                if not isinstance(result, Exception) and i < len(strategy_names):
                    strategy_name = strategy_names[i]
                    opportunities[strategy_name] = result
                elif isinstance(result, Exception):
                    logger.error(f"Strategy scan error: {result}")
            
        except Exception as e:
            logger.error(f"Multi-strategy scan error: {e}")
        
        return opportunities
    
    async def _scan_triangular_arbitrage(self) -> List[TriangularOpportunity]:
        """Scan for triangular arbitrage opportunities"""
        opportunities = []
        
        try:
            # Get available trading pairs
            all_pairs = await self._get_available_pairs()
            
            # Find triangular paths
            triangular_paths = self._find_triangular_paths(all_pairs)
            
            for path in triangular_paths:
                opportunity = await self._evaluate_triangular_path(path)
                if opportunity and opportunity.profit_percentage > self.min_profit_thresholds['triangular']:
                    opportunities.append(opportunity)
            
            # Sort by profit percentage
            opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
            
        except Exception as e:
            logger.error(f"Triangular arbitrage scan error: {e}")
        
        return opportunities[:10]  # Return top 10
    
    async def _scan_funding_arbitrage(self) -> List[FundingOpportunity]:
        """Scan for funding rate arbitrage opportunities"""
        opportunities = []
        
        try:
            # Get spot and futures prices
            spot_prices = await self._get_spot_prices()
            futures_data = await self._get_futures_data()
            
            for symbol in spot_prices:
                if symbol in futures_data:
                    opportunity = await self._evaluate_funding_opportunity(
                        symbol, spot_prices[symbol], futures_data[symbol]
                    )
                    
                    if opportunity and opportunity.profit_percentage > self.min_profit_thresholds['funding']:
                        opportunities.append(opportunity)
            
            # Sort by profit percentage
            opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
            
        except Exception as e:
            logger.error(f"Funding arbitrage scan error: {e}")
        
        return opportunities[:5]  # Return top 5
    
    async def _scan_statistical_arbitrage(self) -> List[StatisticalOpportunity]:
        """Scan for statistical arbitrage opportunities"""
        opportunities = []
        
        try:
            # Update price history
            await self._update_price_history()
            
            # Calculate correlations
            await self._update_correlations()
            
            # Find mean reversion opportunities
            correlated_pairs = self._find_correlated_pairs()
            
            for pair in correlated_pairs:
                opportunity = await self._evaluate_statistical_opportunity(pair)
                if opportunity and opportunity.profit_percentage > self.min_profit_thresholds['statistical']:
                    opportunities.append(opportunity)
            
            # Sort by mean reversion probability
            opportunities.sort(key=lambda x: x.mean_reversion_probability, reverse=True)
            
        except Exception as e:
            logger.error(f"Statistical arbitrage scan error: {e}")
        
        return opportunities[:8]  # Return top 8
    
    async def _scan_cross_exchange_arbitrage(self) -> List[Dict]:
        """Scan for traditional cross-exchange arbitrage"""
        opportunities = []
        
        try:
            # Get order books from all exchanges
            symbols = ['BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'LTC/USDT', 'SOL/USDT', 
                      'APE/USDT', 'DOGE/USDT', 'MATIC/USDT', 'TON/USDT']
            
            for symbol in symbols:
                order_books = await self.exchange_manager.get_order_books(symbol)
                
                if len(order_books) >= 2:
                    opportunity = await self._evaluate_cross_exchange_opportunity(symbol, order_books)
                    if opportunity and opportunity['spread_percentage'] > self.min_profit_thresholds['cross_exchange']:
                        opportunities.append(opportunity)
            
            # Sort by profit potential
            opportunities.sort(key=lambda x: x.get('net_profit', 0), reverse=True)
            
        except Exception as e:
            logger.error(f"Cross-exchange arbitrage scan error: {e}")
        
        return opportunities[:10]  # Return top 10
    
    def _find_triangular_paths(self, pairs: List[str]) -> List[List[str]]:
        """Find valid triangular arbitrage paths"""
        paths = []
        
        # Extract unique base and quote currencies
        currencies = set()
        for pair in pairs:
            base, quote = pair.split('/')
            currencies.add(base)
            currencies.add(quote)
        
        # Find triangular paths (A->B->C->A)
        for base_currency in ['USDT', 'BTC', 'ETH']:  # Start with major currencies
            for intermediate in currencies:
                if intermediate == base_currency:
                    continue
                
                for target in currencies:
                    if target == base_currency or target == intermediate:
                        continue
                    
                    # Check if path exists: base->intermediate->target->base
                    path1 = f"{intermediate}/{base_currency}"
                    path2 = f"{target}/{intermediate}"
                    path3 = f"{base_currency}/{target}"
                    
                    # Alternative path formats
                    alt_path1 = f"{base_currency}/{intermediate}"
                    alt_path2 = f"{intermediate}/{target}"
                    alt_path3 = f"{target}/{base_currency}"
                    
                    if (path1 in pairs or alt_path1 in pairs) and \
                       (path2 in pairs or alt_path2 in pairs) and \
                       (path3 in pairs or alt_path3 in pairs):
                        
                        # Determine correct path direction
                        actual_path = []
                        if path1 in pairs:
                            actual_path.append(path1)
                        else:
                            actual_path.append(alt_path1)
                        
                        if path2 in pairs:
                            actual_path.append(path2)
                        else:
                            actual_path.append(alt_path2)
                        
                        if path3 in pairs:
                            actual_path.append(path3)
                        else:
                            actual_path.append(alt_path3)
                        
                        paths.append(actual_path)
        
        return paths[:20]  # Limit to top 20 paths
    
    async def _evaluate_triangular_path(self, path: List[str]) -> Optional[TriangularOpportunity]:
        """Evaluate a triangular arbitrage path"""
        try:
            # Get prices for each step
            prices = []
            exchanges = []
            
            for pair in path:
                order_books = await self.exchange_manager.get_order_books(pair)
                if not order_books:
                    return None
                
                # Use best available exchange for each step
                best_exchange = min(order_books.keys(), 
                                  key=lambda x: order_books[x]['ask'])
                prices.append(order_books[best_exchange]['ask'])
                exchanges.append(best_exchange)
            
            # Calculate triangular arbitrage profit
            initial_amount = 1000  # Start with $1000 USDT
            current_amount = initial_amount
            
            # Execute triangular path
            for i, (pair, price) in enumerate(zip(path, prices)):
                base, quote = pair.split('/')
                
                if i == 0:  # First trade: USDT -> intermediate
                    current_amount = current_amount / price
                elif i == 1:  # Second trade: intermediate -> target
                    current_amount = current_amount * price
                else:  # Third trade: target -> USDT
                    current_amount = current_amount * price
            
            # Calculate profit
            profit = current_amount - initial_amount
            profit_percentage = (profit / initial_amount) * 100
            
            if profit_percentage > 0:
                return TriangularOpportunity(
                    path=path,
                    exchanges=exchanges,
                    prices=prices,
                    expected_profit=profit,
                    profit_percentage=profit_percentage,
                    execution_time=2.5,  # Estimated execution time
                    risk_score=self._calculate_triangular_risk(path, prices),
                    volume_required=initial_amount
                )
            
        except Exception as e:
            logger.error(f"Triangular path evaluation error: {e}")
        
        return None
    
    async def _evaluate_funding_opportunity(self, symbol: str, spot_data: Dict, futures_data: Dict) -> Optional[FundingOpportunity]:
        """Evaluate funding rate arbitrage opportunity"""
        try:
            spot_price = spot_data['price']
            futures_price = futures_data['price']
            funding_rate = futures_data.get('funding_rate', 0)
            
            # Calculate funding arbitrage profit
            price_diff = futures_price - spot_price
            price_diff_pct = (price_diff / spot_price) * 100
            
            # Annualized funding rate profit
            funding_profit_pct = funding_rate * (365 * 24 / 8)  # 8-hour funding
            
            total_profit_pct = abs(price_diff_pct) + funding_profit_pct
            
            if total_profit_pct > self.min_profit_thresholds['funding']:
                return FundingOpportunity(
                    symbol=symbol,
                    spot_exchange=spot_data['exchange'],
                    futures_exchange=futures_data['exchange'],
                    spot_price=spot_price,
                    futures_price=futures_price,
                    funding_rate=funding_rate,
                    funding_interval=8,
                    expected_profit=total_profit_pct * 1000,  # On $1000 position
                    profit_percentage=total_profit_pct,
                    risk_score=self._calculate_funding_risk(price_diff_pct, funding_rate),
                    position_size=1000
                )
            
        except Exception as e:
            logger.error(f"Funding opportunity evaluation error: {e}")
        
        return None
    
    def _calculate_triangular_risk(self, path: List[str], prices: List[float]) -> float:
        """Calculate risk score for triangular arbitrage"""
        # Base risk from number of trades
        base_risk = len(path) * 1.5
        
        # Price volatility risk
        price_volatility = np.std(prices) / np.mean(prices) * 100
        volatility_risk = min(price_volatility * 2, 5.0)
        
        # Execution risk (more trades = higher risk)
        execution_risk = len(path) * 0.8
        
        return min(base_risk + volatility_risk + execution_risk, 10.0)
    
    def _calculate_funding_risk(self, price_diff_pct: float, funding_rate: float) -> float:
        """Calculate risk score for funding arbitrage"""
        # Price difference risk
        price_risk = abs(price_diff_pct) * 0.5
        
        # Funding rate volatility risk
        funding_risk = abs(funding_rate) * 100
        
        # Base funding arbitrage risk
        base_risk = 3.0
        
        return min(base_risk + price_risk + funding_risk, 10.0)
    
    async def _get_available_pairs(self) -> List[str]:
        """Get all available trading pairs"""
        pairs = set()

        for exchange_name in self.exchange_manager.exchanges:
            try:
                exchange = self.exchange_manager.exchanges[exchange_name]
                if hasattr(exchange, 'ccxt_exchange') and exchange.ccxt_exchange:
                    markets = await exchange.ccxt_exchange.load_markets()
                    pairs.update(markets.keys())
                else:
                    # Fallback to common pairs if markets not available
                    common_pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'LTC/USDT', 'DOGE/USDT', 'MATIC/USDT', 'TON/USDT']
                    pairs.update(common_pairs)
            except Exception as e:
                logger.error(f"Error getting pairs from {exchange_name}: {e}")
                # Fallback to common pairs on error
                common_pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'LTC/USDT', 'DOGE/USDT', 'MATIC/USDT', 'TON/USDT']
                pairs.update(common_pairs)

        return list(pairs)
    
    async def _get_spot_prices(self) -> Dict[str, Dict]:
        """Get current spot prices"""
        prices = {}
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']

        for symbol in symbols:
            try:
                order_books = await self.exchange_manager.get_order_books(symbol)
                if order_books:
                    # Find exchange with best ask price (lowest sell price)
                    best_exchange = None
                    best_ask = float('inf')

                    for exchange_name, order_book in order_books.items():
                        if order_book and order_book.best_ask:
                            ask_price = order_book.best_ask[0]  # price is first element of tuple
                            if ask_price < best_ask:
                                best_ask = ask_price
                                best_exchange = exchange_name

                    if best_exchange:
                        prices[symbol] = {
                            'price': best_ask,
                            'exchange': best_exchange
                        }
            except Exception as e:
                logger.error(f"Error getting spot price for {symbol}: {e}")

        return prices
    
    async def _get_futures_data(self) -> Dict[str, Dict]:
        """Get futures prices and funding rates (mock data for now)"""
        # Mock futures data - in real implementation, connect to futures exchanges
        futures_data = {
            'BTC/USDT': {
                'price': 117900,  # Slightly higher than spot
                'funding_rate': 0.0001,  # 0.01% funding rate
                'exchange': 'binance_futures'
            },
            'ETH/USDT': {
                'price': 3648,
                'funding_rate': 0.00005,
                'exchange': 'binance_futures'
            },
            'SOL/USDT': {
                'price': 197.2,
                'funding_rate': 0.00015,
                'exchange': 'binance_futures'
            }
        }
        
        return futures_data

    async def _update_price_history(self):
        """Update price history for statistical arbitrage"""
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'LTC/USDT']

        for symbol in symbols:
            try:
                order_books = await self.exchange_manager.get_order_books(symbol)
                if order_books:
                    # Get average price across exchanges
                    prices = []
                    for order_book in order_books.values():
                        if order_book and order_book.best_ask:
                            prices.append(order_book.best_ask[0])  # price is first element of tuple

                    if prices:
                        avg_price = np.mean(prices)

                        if symbol not in self.price_history:
                            self.price_history[symbol] = []

                        self.price_history[symbol].append({
                            'timestamp': datetime.now(),
                            'price': avg_price
                        })

                        # Keep only last 100 data points
                        if len(self.price_history[symbol]) > 100:
                            self.price_history[symbol] = self.price_history[symbol][-100:]

            except Exception as e:
                logger.error(f"Error updating price history for {symbol}: {e}")

    async def _update_correlations(self):
        """Update correlation matrix for statistical arbitrage"""
        try:
            symbols = list(self.price_history.keys())

            if len(symbols) < 2:
                return

            # Calculate correlations between all pairs
            for i, symbol1 in enumerate(symbols):
                for j, symbol2 in enumerate(symbols[i+1:], i+1):
                    if len(self.price_history[symbol1]) >= 20 and len(self.price_history[symbol2]) >= 20:
                        # Get price series
                        prices1 = [p['price'] for p in self.price_history[symbol1][-20:]]
                        prices2 = [p['price'] for p in self.price_history[symbol2][-20:]]

                        # Calculate correlation
                        correlation = np.corrcoef(prices1, prices2)[0, 1]

                        pair_key = f"{symbol1}_{symbol2}"
                        self.correlation_matrix[pair_key] = {
                            'correlation': correlation,
                            'updated': datetime.now()
                        }

        except Exception as e:
            logger.error(f"Error updating correlations: {e}")

    def _find_correlated_pairs(self) -> List[Tuple[str, str]]:
        """Find highly correlated pairs for statistical arbitrage"""
        correlated_pairs = []

        for pair_key, data in self.correlation_matrix.items():
            correlation = data['correlation']

            # Look for high correlation (>0.7) or high negative correlation (<-0.7)
            if abs(correlation) > 0.7:
                symbol1, symbol2 = pair_key.split('_')
                correlated_pairs.append((symbol1, symbol2))

        return correlated_pairs

    async def _evaluate_statistical_opportunity(self, pair: Tuple[str, str]) -> Optional[StatisticalOpportunity]:
        """Evaluate statistical arbitrage opportunity"""
        try:
            symbol1, symbol2 = pair

            if symbol1 not in self.price_history or symbol2 not in self.price_history:
                return None

            # Get recent price data
            prices1 = [p['price'] for p in self.price_history[symbol1][-20:]]
            prices2 = [p['price'] for p in self.price_history[symbol2][-20:]]

            if len(prices1) < 20 or len(prices2) < 20:
                return None

            # Calculate price ratio
            ratios = [p1/p2 for p1, p2 in zip(prices1, prices2)]

            # Calculate z-score
            mean_ratio = np.mean(ratios)
            std_ratio = np.std(ratios)
            current_ratio = ratios[-1]
            z_score = (current_ratio - mean_ratio) / std_ratio if std_ratio > 0 else 0

            # Mean reversion probability (higher z-score = higher probability)
            mean_reversion_prob = min(abs(z_score) / 3.0, 1.0)

            # Calculate expected profit
            expected_return_to_mean = (mean_ratio - current_ratio) / current_ratio
            expected_profit_pct = abs(expected_return_to_mean) * 100 * mean_reversion_prob

            if expected_profit_pct > self.min_profit_thresholds['statistical'] and abs(z_score) > 1.5:
                return StatisticalOpportunity(
                    pair_symbols=[symbol1, symbol2],
                    exchanges=['kucoin', 'okx'],  # Default exchanges
                    correlation=self.correlation_matrix[f"{symbol1}_{symbol2}"]['correlation'],
                    z_score=z_score,
                    mean_reversion_probability=mean_reversion_prob,
                    expected_profit=expected_profit_pct * 10,  # On $1000 position
                    profit_percentage=expected_profit_pct,
                    risk_score=self._calculate_statistical_risk(z_score, std_ratio),
                    position_sizes=[500, 500]  # Equal position sizes
                )

        except Exception as e:
            logger.error(f"Statistical opportunity evaluation error: {e}")

        return None

    def _calculate_statistical_risk(self, z_score: float, volatility: float) -> float:
        """Calculate risk score for statistical arbitrage"""
        # Z-score risk (higher z-score = higher risk of continued divergence)
        z_risk = min(abs(z_score) * 0.8, 4.0)

        # Volatility risk
        vol_risk = min(volatility * 100, 3.0)

        # Base statistical arbitrage risk
        base_risk = 2.5

        return min(base_risk + z_risk + vol_risk, 10.0)

    async def _evaluate_cross_exchange_opportunity(self, symbol: str, order_books: Dict) -> Optional[Dict]:
        """Evaluate cross-exchange arbitrage opportunity"""
        try:
            if len(order_books) < 2:
                return None

            # Find best buy and sell prices
            exchanges = list(order_books.keys())
            buy_prices = {ex: order_books[ex]['ask'] for ex in exchanges}
            sell_prices = {ex: order_books[ex]['bid'] for ex in exchanges}

            # Find best arbitrage opportunity
            best_buy_exchange = min(buy_prices.keys(), key=lambda x: buy_prices[x])
            best_sell_exchange = max(sell_prices.keys(), key=lambda x: sell_prices[x])

            if best_buy_exchange == best_sell_exchange:
                return None

            buy_price = buy_prices[best_buy_exchange]
            sell_price = sell_prices[best_sell_exchange]

            # Calculate spread
            spread = sell_price - buy_price
            spread_percentage = (spread / buy_price) * 100

            if spread_percentage > 0:
                # Calculate trade amounts and profit
                trade_amount = 1000 / buy_price  # $1000 worth
                gross_profit = spread * trade_amount

                # Estimate fees (0.1% per trade)
                fees = (buy_price * trade_amount * 0.001) + (sell_price * trade_amount * 0.001)
                net_profit = gross_profit - fees

                return {
                    'symbol': symbol,
                    'buy_exchange': best_buy_exchange,
                    'sell_exchange': best_sell_exchange,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'spread_percentage': spread_percentage,
                    'trade_amount': trade_amount,
                    'net_profit': net_profit,
                    'risk_score': self._calculate_cross_exchange_risk(spread_percentage),
                    'strategy': 'cross_exchange'
                }

        except Exception as e:
            logger.error(f"Cross-exchange opportunity evaluation error: {e}")

        return None

    def _calculate_cross_exchange_risk(self, spread_percentage: float) -> float:
        """Calculate risk score for cross-exchange arbitrage"""
        # Spread risk (lower spread = higher risk)
        spread_risk = max(5.0 - spread_percentage * 2, 1.0)

        # Base cross-exchange risk
        base_risk = 2.0

        return min(base_risk + spread_risk, 10.0)

    def get_strategy_statistics(self) -> Dict:
        """Get statistics for all strategies"""
        return {
            'strategies_enabled': self.strategies_enabled,
            'min_profit_thresholds': self.min_profit_thresholds,
            'max_risk_scores': self.max_risk_scores,
            'price_history_length': {symbol: len(history) for symbol, history in self.price_history.items()},
            'correlations_tracked': len(self.correlation_matrix),
            'last_correlation_update': max([data['updated'] for data in self.correlation_matrix.values()]) if self.correlation_matrix else None
        }

    def enable_strategy(self, strategy_name: str, enabled: bool = True):
        """Enable or disable a specific strategy"""
        if strategy_name in self.strategies_enabled:
            self.strategies_enabled[strategy_name] = enabled
            logger.info(f"Strategy {strategy_name} {'enabled' if enabled else 'disabled'}")

    def set_profit_threshold(self, strategy_name: str, threshold: float):
        """Set minimum profit threshold for a strategy"""
        if strategy_name in self.min_profit_thresholds:
            self.min_profit_thresholds[strategy_name] = threshold
            logger.info(f"Profit threshold for {strategy_name} set to {threshold}%")
