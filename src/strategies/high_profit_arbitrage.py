"""
High-Profit Arbitrage Strategy for Arbtronx
Targets 20% profit trades using advanced market signals
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from loguru import logger

from ..exchanges.exchange_manager import ExchangeManager
from ..utils.technical_indicators import RSICalculator, VolumeAnalyzer
from ..utils.whale_tracker import WhaleTracker


@dataclass
class MarketSignal:
    """Market signal data structure"""
    symbol: str
    spread_percentage: float
    rsi_buy_side: float
    rsi_sell_side: float
    volume_surge: bool
    whale_activity: bool
    volatility_24h: float
    confidence_score: float
    timestamp: datetime


@dataclass
class TradePosition:
    """Active trade position"""
    symbol: str
    buy_exchange: str
    sell_exchange: str
    entry_price_buy: float
    entry_price_sell: float
    quantity: float
    entry_time: datetime
    target_profit: float
    stop_loss: float
    status: str  # 'active', 'completed', 'stopped'


class HighProfitArbitrageStrategy:
    """
    Advanced arbitrage strategy targeting 20% profit trades
    """
    
    def __init__(self, exchange_manager: ExchangeManager):
        self.exchange_manager = exchange_manager
        self.rsi_calculator = RSICalculator(period=14)
        self.volume_analyzer = VolumeAnalyzer()
        self.whale_tracker = WhaleTracker()
        
        # Strategy parameters from config
        self.min_profit_threshold = 20.0  # 20% minimum profit
        self.min_spread_threshold = 6.0   # 6% minimum spread
        self.max_spread_threshold = 10.0  # 10% maximum spread
        self.min_volatility_24h = 8.0     # 8% minimum 24h volatility
        self.scan_interval = 5            # 5 seconds
        self.volume_surge_multiplier = 2.0 # 2x volume increase
        self.whale_order_threshold = 20000 # $20k whale threshold
        self.stop_loss_threshold = -5.0   # -5% stop loss
        self.cooldown_period = 60         # 1 minute cooldown
        
        # Trading pairs - high volatility tokens
        self.trading_pairs = [
            'PEPE/USDT', 'FLOKI/USDT', 'SHIB/USDT', 
            'DOGE/USDT', 'MATIC/USDT', 'SUI/USDT', 'BONK/USDT'
        ]
        
        # State tracking
        self.active_positions: Dict[str, TradePosition] = {}
        self.last_trade_time = None
        self.spread_history: Dict[str, List[Tuple[float, datetime]]] = {}
        self.price_cache: Dict[str, Dict[str, float]] = {}
        
        logger.info("🚀 High-Profit Arbitrage Strategy initialized")
        logger.info(f"Target pairs: {', '.join(self.trading_pairs)}")
        logger.info(f"Minimum profit target: {self.min_profit_threshold}%")
    
    async def start_scanning(self):
        """Start the main scanning loop"""
        logger.info("🔍 Starting high-profit arbitrage scanning...")
        
        while True:
            try:
                # Check cooldown period
                if self._is_in_cooldown():
                    await asyncio.sleep(self.scan_interval)
                    continue
                
                # Scan all trading pairs
                signals = await self._scan_all_pairs()
                
                # Process signals and look for trade opportunities
                for signal in signals:
                    if await self._should_enter_trade(signal):
                        await self._execute_arbitrage_trade(signal)
                
                # Monitor active positions
                await self._monitor_active_positions()
                
                # Wait for next scan
                await asyncio.sleep(self.scan_interval)
                
            except Exception as e:
                logger.error(f"Error in scanning loop: {e}")
                await asyncio.sleep(self.scan_interval)
    
    async def _scan_all_pairs(self) -> List[MarketSignal]:
        """Scan all trading pairs for arbitrage signals"""
        signals = []
        
        for symbol in self.trading_pairs:
            try:
                signal = await self._analyze_pair(symbol)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
        
        return signals
    
    async def _analyze_pair(self, symbol: str) -> Optional[MarketSignal]:
        """Analyze a single trading pair for arbitrage opportunity"""
        
        # Get order books from both exchanges
        order_books = await self.exchange_manager.get_order_books(symbol)
        
        if len(order_books) < 2:
            return None
        
        # Get current prices
        binance_data = order_books.get('binance')
        okx_data = order_books.get('okx')
        
        if not binance_data or not okx_data:
            return None
        
        # Calculate spreads in both directions
        binance_bid = binance_data.bids[0][0] if binance_data.bids else 0
        binance_ask = binance_data.asks[0][0] if binance_data.asks else 0
        okx_bid = okx_data.bids[0][0] if okx_data.bids else 0
        okx_ask = okx_data.asks[0][0] if okx_data.asks else 0
        
        if not all([binance_bid, binance_ask, okx_bid, okx_ask]):
            return None
        
        # Calculate spreads
        spread_binance_to_okx = ((okx_bid - binance_ask) / binance_ask) * 100
        spread_okx_to_binance = ((binance_bid - okx_ask) / okx_ask) * 100
        
        # Choose the best spread
        if spread_binance_to_okx > spread_okx_to_binance:
            spread_percentage = spread_binance_to_okx
            buy_exchange = 'binance'
            sell_exchange = 'okx'
            buy_price = binance_ask
            sell_price = okx_bid
        else:
            spread_percentage = spread_okx_to_binance
            buy_exchange = 'okx'
            sell_exchange = 'binance'
            buy_price = okx_ask
            sell_price = binance_bid
        
        # Check if spread meets minimum threshold
        if spread_percentage < self.min_spread_threshold:
            return None
        
        # Check if spread is within maximum threshold (avoid extreme volatility)
        if spread_percentage > self.max_spread_threshold:
            logger.warning(f"{symbol}: Spread {spread_percentage:.2f}% exceeds maximum threshold")
            return None
        
        # Get 24h volatility
        volatility_24h = await self._get_24h_volatility(symbol)
        if volatility_24h < self.min_volatility_24h:
            return None
        
        # Calculate RSI for both exchanges
        rsi_buy_side = await self._calculate_rsi(symbol, buy_exchange)
        rsi_sell_side = await self._calculate_rsi(symbol, sell_exchange)
        
        # Check RSI divergence condition
        rsi_condition = rsi_buy_side < 30 and rsi_sell_side > 50
        
        # Check volume surge
        volume_surge = await self._detect_volume_surge(symbol)
        
        # Check whale activity
        whale_activity = await self._detect_whale_activity(symbol, buy_exchange, sell_exchange)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            spread_percentage, rsi_condition, volume_surge, whale_activity, volatility_24h
        )
        
        # Store spread history
        self._update_spread_history(symbol, spread_percentage)
        
        return MarketSignal(
            symbol=symbol,
            spread_percentage=spread_percentage,
            rsi_buy_side=rsi_buy_side,
            rsi_sell_side=rsi_sell_side,
            volume_surge=volume_surge,
            whale_activity=whale_activity,
            volatility_24h=volatility_24h,
            confidence_score=confidence_score,
            timestamp=datetime.now()
        )
    
    async def _get_24h_volatility(self, symbol: str) -> float:
        """Get 24h volatility for a symbol"""
        try:
            # Get 24h ticker data from both exchanges
            binance_ticker = await self.exchange_manager.get_24h_ticker('binance', symbol)
            okx_ticker = await self.exchange_manager.get_24h_ticker('okx', symbol)
            
            if binance_ticker and okx_ticker:
                # Use average volatility from both exchanges
                binance_vol = abs(binance_ticker.get('percentage', 0))
                okx_vol = abs(okx_ticker.get('percentage', 0))
                return (binance_vol + okx_vol) / 2
            
            return 0.0
        except Exception as e:
            logger.error(f"Error getting 24h volatility for {symbol}: {e}")
            return 0.0
    
    async def _calculate_rsi(self, symbol: str, exchange: str) -> float:
        """Calculate RSI for a symbol on an exchange"""
        try:
            # Get recent price data (last 20 candles for RSI calculation)
            candles = await self.exchange_manager.get_ohlcv(exchange, symbol, '1m', limit=20)
            
            if len(candles) >= 14:
                closes = [float(candle[4]) for candle in candles]  # Close prices
                return self.rsi_calculator.calculate(closes)
            
            return 50.0  # Neutral RSI if not enough data
        except Exception as e:
            logger.error(f"Error calculating RSI for {symbol} on {exchange}: {e}")
            return 50.0
    
    async def _detect_volume_surge(self, symbol: str) -> bool:
        """Detect if there's a volume surge (2x+ increase in last 5 minutes)"""
        try:
            # Get recent volume data
            current_volume = await self._get_current_volume(symbol)
            historical_volume = await self._get_historical_volume(symbol, minutes=5)
            
            if current_volume and historical_volume:
                surge_ratio = current_volume / historical_volume
                return surge_ratio >= self.volume_surge_multiplier
            
            return False
        except Exception as e:
            logger.error(f"Error detecting volume surge for {symbol}: {e}")
            return False
    
    async def _detect_whale_activity(self, symbol: str, buy_exchange: str, sell_exchange: str) -> bool:
        """Detect whale activity (large orders >= $20k)"""
        try:
            # Check order books for large orders
            buy_whale = await self.whale_tracker.detect_large_orders(
                buy_exchange, symbol, self.whale_order_threshold, 'buy'
            )
            sell_whale = await self.whale_tracker.detect_large_orders(
                sell_exchange, symbol, self.whale_order_threshold, 'sell'
            )
            
            return buy_whale or sell_whale
        except Exception as e:
            logger.error(f"Error detecting whale activity for {symbol}: {e}")
            return False
    
    def _calculate_confidence_score(self, spread: float, rsi_condition: bool, 
                                  volume_surge: bool, whale_activity: bool, 
                                  volatility: float) -> float:
        """Calculate confidence score for the signal"""
        score = 0.0
        
        # Spread score (0-40 points)
        if spread >= 8.0:
            score += 40
        elif spread >= 7.0:
            score += 30
        elif spread >= 6.0:
            score += 20
        
        # RSI condition (0-25 points)
        if rsi_condition:
            score += 25
        
        # Volume surge (0-20 points)
        if volume_surge:
            score += 20
        
        # Whale activity (0-15 points)
        if whale_activity:
            score += 15
        
        return min(score, 100.0)  # Cap at 100
    
    def _update_spread_history(self, symbol: str, spread: float):
        """Update spread history for trend analysis"""
        if symbol not in self.spread_history:
            self.spread_history[symbol] = []
        
        self.spread_history[symbol].append((spread, datetime.now()))
        
        # Keep only last 100 entries
        if len(self.spread_history[symbol]) > 100:
            self.spread_history[symbol] = self.spread_history[symbol][-100:]
    
    def _is_in_cooldown(self) -> bool:
        """Check if bot is in cooldown period"""
        if not self.last_trade_time:
            return False

        time_since_last_trade = (datetime.now() - self.last_trade_time).total_seconds()
        return time_since_last_trade < self.cooldown_period

    async def _should_enter_trade(self, signal: MarketSignal) -> bool:
        """Determine if we should enter a trade based on the signal"""

        # Check if already have position in this symbol
        if signal.symbol in self.active_positions:
            return False

        # Check minimum confidence score (require at least 70%)
        if signal.confidence_score < 70.0:
            return False

        # Check all entry conditions
        conditions = {
            'spread_threshold': signal.spread_percentage >= self.min_spread_threshold,
            'rsi_divergence': signal.rsi_buy_side < 30 and signal.rsi_sell_side > 50,
            'volume_surge': signal.volume_surge,
            'whale_activity': signal.whale_activity,
            'volatility': signal.volatility_24h >= self.min_volatility_24h
        }

        # Log the signal analysis
        logger.info(f"🔍 Signal Analysis for {signal.symbol}:")
        logger.info(f"   Spread: {signal.spread_percentage:.2f}% ✅" if conditions['spread_threshold'] else f"   Spread: {signal.spread_percentage:.2f}% ❌")
        logger.info(f"   RSI: Buy={signal.rsi_buy_side:.1f}, Sell={signal.rsi_sell_side:.1f} ✅" if conditions['rsi_divergence'] else f"   RSI: Buy={signal.rsi_buy_side:.1f}, Sell={signal.rsi_sell_side:.1f} ❌")
        logger.info(f"   Volume Surge: ✅" if conditions['volume_surge'] else f"   Volume Surge: ❌")
        logger.info(f"   Whale Activity: ✅" if conditions['whale_activity'] else f"   Whale Activity: ❌")
        logger.info(f"   Volatility: {signal.volatility_24h:.1f}% ✅" if conditions['volatility'] else f"   Volatility: {signal.volatility_24h:.1f}% ❌")
        logger.info(f"   Confidence Score: {signal.confidence_score:.1f}%")

        # Require ALL conditions to be met for high-profit strategy
        all_conditions_met = all(conditions.values())

        if all_conditions_met:
            logger.success(f"🎯 ALL CONDITIONS MET for {signal.symbol}! Preparing to enter trade...")
        else:
            missing = [k for k, v in conditions.items() if not v]
            logger.info(f"⏳ Waiting for conditions: {', '.join(missing)}")

        return all_conditions_met

    async def _execute_arbitrage_trade(self, signal: MarketSignal):
        """Execute the arbitrage trade"""
        try:
            logger.info(f"🚀 EXECUTING HIGH-PROFIT ARBITRAGE TRADE for {signal.symbol}")
            logger.info(f"   Target Profit: {self.min_profit_threshold}%")
            logger.info(f"   Current Spread: {signal.spread_percentage:.2f}%")

            # Get current order books
            order_books = await self.exchange_manager.get_order_books(signal.symbol)
            binance_data = order_books.get('binance')
            okx_data = order_books.get('okx')

            if not binance_data or not okx_data:
                logger.error("Failed to get order book data")
                return

            # Determine buy/sell exchanges and prices
            binance_ask = binance_data.asks[0][0] if binance_data.asks else 0
            okx_bid = okx_data.bids[0][0] if okx_data.bids else 0
            okx_ask = okx_data.asks[0][0] if okx_data.asks else 0
            binance_bid = binance_data.bids[0][0] if binance_data.bids else 0

            # Choose direction with better spread
            if ((okx_bid - binance_ask) / binance_ask) > ((binance_bid - okx_ask) / okx_ask):
                buy_exchange = 'binance'
                sell_exchange = 'okx'
                buy_price = binance_ask
                sell_price = okx_bid
            else:
                buy_exchange = 'okx'
                sell_exchange = 'binance'
                buy_price = okx_ask
                sell_price = binance_bid

            # Calculate position size (use available balance)
            available_balance = await self._get_available_balance(buy_exchange, 'USDT')
            position_size_usd = min(available_balance * 0.95, 100000)  # Use 95% of balance, max $100k
            quantity = position_size_usd / buy_price

            logger.info(f"   Buy: {buy_exchange} @ ${buy_price:.6f}")
            logger.info(f"   Sell: {sell_exchange} @ ${sell_price:.6f}")
            logger.info(f"   Quantity: {quantity:.2f} {signal.symbol.split('/')[0]}")
            logger.info(f"   Position Size: ${position_size_usd:.2f}")

            # Calculate target profit price
            target_profit_price = buy_price * (1 + self.min_profit_threshold / 100)
            stop_loss_price = buy_price * (1 + self.stop_loss_threshold / 100)

            # Create trade position
            position = TradePosition(
                symbol=signal.symbol,
                buy_exchange=buy_exchange,
                sell_exchange=sell_exchange,
                entry_price_buy=buy_price,
                entry_price_sell=sell_price,
                quantity=quantity,
                entry_time=datetime.now(),
                target_profit=target_profit_price,
                stop_loss=stop_loss_price,
                status='active'
            )

            # Execute buy order (simulation mode for now)
            logger.info(f"📈 SIMULATED BUY: {quantity:.2f} {signal.symbol} on {buy_exchange} @ ${buy_price:.6f}")

            # Store active position
            self.active_positions[signal.symbol] = position
            self.last_trade_time = datetime.now()

            logger.success(f"✅ Trade position opened for {signal.symbol}")
            logger.info(f"   Target: ${target_profit_price:.6f} ({self.min_profit_threshold}% profit)")
            logger.info(f"   Stop Loss: ${stop_loss_price:.6f} ({self.stop_loss_threshold}% loss)")

        except Exception as e:
            logger.error(f"❌ Failed to execute trade for {signal.symbol}: {e}")

    async def _monitor_active_positions(self):
        """Monitor active positions for exit conditions"""
        positions_to_close = []

        for symbol, position in self.active_positions.items():
            try:
                # Get current price on sell exchange
                order_books = await self.exchange_manager.get_order_books(symbol)
                sell_exchange_data = order_books.get(position.sell_exchange)

                if not sell_exchange_data or not sell_exchange_data.bids:
                    continue

                current_sell_price = sell_exchange_data.bids[0][0]

                # Calculate current profit
                current_profit_pct = ((current_sell_price - position.entry_price_buy) / position.entry_price_buy) * 100
                current_profit_usd = (current_sell_price - position.entry_price_buy) * position.quantity

                # Check exit conditions
                should_exit = False
                exit_reason = ""

                # Target profit reached
                if current_profit_pct >= self.min_profit_threshold:
                    should_exit = True
                    exit_reason = f"TARGET PROFIT REACHED: {current_profit_pct:.2f}%"

                # Stop loss triggered
                elif current_profit_pct <= self.stop_loss_threshold:
                    should_exit = True
                    exit_reason = f"STOP LOSS TRIGGERED: {current_profit_pct:.2f}%"

                # Time-based exit (if position open for more than 10 minutes and losing)
                elif (datetime.now() - position.entry_time).total_seconds() > 600 and current_profit_pct < 0:
                    should_exit = True
                    exit_reason = f"TIME-BASED EXIT: {current_profit_pct:.2f}% after 10min"

                # RSI reversal signal
                elif await self._check_rsi_reversal(symbol, position):
                    should_exit = True
                    exit_reason = f"RSI REVERSAL SIGNAL: {current_profit_pct:.2f}%"

                if should_exit:
                    logger.info(f"🔄 CLOSING POSITION: {symbol}")
                    logger.info(f"   Reason: {exit_reason}")
                    logger.info(f"   Entry: ${position.entry_price_buy:.6f}")
                    logger.info(f"   Exit: ${current_sell_price:.6f}")
                    logger.info(f"   Profit: ${current_profit_usd:.2f} ({current_profit_pct:.2f}%)")

                    # Execute sell order (simulation)
                    logger.info(f"📉 SIMULATED SELL: {position.quantity:.2f} {symbol} on {position.sell_exchange} @ ${current_sell_price:.6f}")

                    positions_to_close.append(symbol)

                    if current_profit_pct >= self.min_profit_threshold:
                        logger.success(f"🎉 PROFITABLE TRADE COMPLETED: +{current_profit_pct:.2f}%")
                    else:
                        logger.warning(f"⚠️ Trade closed with loss: {current_profit_pct:.2f}%")

                else:
                    # Log position status
                    time_open = (datetime.now() - position.entry_time).total_seconds() / 60
                    logger.info(f"📊 {symbol}: {current_profit_pct:+.2f}% (${current_profit_usd:+.2f}) | Open: {time_open:.1f}min")

            except Exception as e:
                logger.error(f"Error monitoring position {symbol}: {e}")

        # Close completed positions
        for symbol in positions_to_close:
            del self.active_positions[symbol]

    async def _check_rsi_reversal(self, symbol: str, position: TradePosition) -> bool:
        """Check for RSI reversal signal"""
        try:
            rsi_buy = await self._calculate_rsi(symbol, position.buy_exchange)
            rsi_sell = await self._calculate_rsi(symbol, position.sell_exchange)

            # RSI reversal: buy side becomes overbought (>70) or sell side becomes oversold (<30)
            return rsi_buy > 70 or rsi_sell < 30
        except:
            return False

    async def _get_available_balance(self, exchange: str, currency: str) -> float:
        """Get available balance for trading"""
        try:
            balance = await self.exchange_manager.get_balance(exchange, currency)
            return balance.get('free', 0.0)
        except:
            return 10000.0  # Default simulation balance

    async def _get_current_volume(self, symbol: str) -> Optional[float]:
        """Get current trading volume"""
        try:
            # Get 1-minute volume data
            binance_ticker = await self.exchange_manager.get_24h_ticker('binance', symbol)
            okx_ticker = await self.exchange_manager.get_24h_ticker('okx', symbol)

            if binance_ticker and okx_ticker:
                return (binance_ticker.get('quoteVolume', 0) + okx_ticker.get('quoteVolume', 0)) / 2
            return None
        except:
            return None

    async def _get_historical_volume(self, symbol: str, minutes: int = 5) -> Optional[float]:
        """Get historical average volume"""
        try:
            # Get historical volume data (simplified)
            current_volume = await self._get_current_volume(symbol)
            if current_volume:
                return current_volume * 0.8  # Assume 20% lower historical average
            return None
        except:
            return None

    def get_strategy_status(self) -> Dict:
        """Get current strategy status"""
        return {
            'strategy_name': 'High-Profit Arbitrage',
            'target_profit': f"{self.min_profit_threshold}%",
            'active_positions': len(self.active_positions),
            'positions': [
                {
                    'symbol': pos.symbol,
                    'buy_exchange': pos.buy_exchange,
                    'sell_exchange': pos.sell_exchange,
                    'entry_time': pos.entry_time.isoformat(),
                    'status': pos.status
                }
                for pos in self.active_positions.values()
            ],
            'last_trade': self.last_trade_time.isoformat() if self.last_trade_time else None,
            'cooldown_remaining': max(0, self.cooldown_period - (datetime.now() - self.last_trade_time).total_seconds()) if self.last_trade_time else 0,
            'trading_pairs': self.trading_pairs,
            'scan_interval': self.scan_interval
        }
