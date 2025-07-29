"""
Performance Tracking for High-Profit Arbitrage Strategy
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from loguru import logger


@dataclass
class TradeRecord:
    """Individual trade record"""
    symbol: str
    entry_time: datetime
    exit_time: datetime
    buy_exchange: str
    sell_exchange: str
    entry_price_buy: float
    entry_price_sell: float
    exit_price_buy: float
    exit_price_sell: float
    quantity: float
    pnl_usd: float
    pnl_percentage: float
    fees_usd: float
    trade_duration_minutes: float
    strategy_signals: Dict  # RSI, volume surge, whale activity, etc.


@dataclass
class PerformanceMetrics:
    """Performance metrics summary"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl_usd: float
    total_pnl_percentage: float
    avg_trade_pnl: float
    best_trade_pnl: float
    worst_trade_pnl: float
    avg_trade_duration: float
    total_fees_paid: float
    sharpe_ratio: float
    max_drawdown: float
    profit_factor: float
    avg_winning_trade: float
    avg_losing_trade: float


class PerformanceTracker:
    """
    Tracks and analyzes trading performance
    """
    
    def __init__(self):
        self.trades: List[TradeRecord] = []
        self.daily_pnl: Dict[str, float] = {}
        self.hourly_pnl: Dict[str, float] = {}
        
        # Performance data file
        self.data_file = Path("data/performance_data.json")
        self.data_file.parent.mkdir(exist_ok=True)
        
        logger.info("📊 Performance Tracker initialized")
    
    def initialize(self):
        """Initialize performance tracker"""
        try:
            self._load_historical_data()
            logger.success("✅ Performance Tracker loaded historical data")
        except Exception as e:
            logger.warning(f"⚠️ Could not load historical data: {e}")
    
    def _load_historical_data(self):
        """Load historical performance data"""
        if not self.data_file.exists():
            return
        
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            # Load trades
            for trade_data in data.get('trades', []):
                trade = TradeRecord(
                    symbol=trade_data['symbol'],
                    entry_time=datetime.fromisoformat(trade_data['entry_time']),
                    exit_time=datetime.fromisoformat(trade_data['exit_time']),
                    buy_exchange=trade_data['buy_exchange'],
                    sell_exchange=trade_data['sell_exchange'],
                    entry_price_buy=trade_data['entry_price_buy'],
                    entry_price_sell=trade_data['entry_price_sell'],
                    exit_price_buy=trade_data['exit_price_buy'],
                    exit_price_sell=trade_data['exit_price_sell'],
                    quantity=trade_data['quantity'],
                    pnl_usd=trade_data['pnl_usd'],
                    pnl_percentage=trade_data['pnl_percentage'],
                    fees_usd=trade_data['fees_usd'],
                    trade_duration_minutes=trade_data['trade_duration_minutes'],
                    strategy_signals=trade_data.get('strategy_signals', {})
                )
                self.trades.append(trade)
            
            # Load daily P&L
            self.daily_pnl = data.get('daily_pnl', {})
            self.hourly_pnl = data.get('hourly_pnl', {})
            
            logger.info(f"📈 Loaded {len(self.trades)} historical trades")
            
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
    
    def _save_data(self):
        """Save performance data to file"""
        try:
            # Convert trades to serializable format
            trades_data = []
            for trade in self.trades:
                trade_dict = asdict(trade)
                trade_dict['entry_time'] = trade.entry_time.isoformat()
                trade_dict['exit_time'] = trade.exit_time.isoformat()
                trades_data.append(trade_dict)
            
            data = {
                'trades': trades_data,
                'daily_pnl': self.daily_pnl,
                'hourly_pnl': self.hourly_pnl,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("💾 Performance data saved")
            
        except Exception as e:
            logger.error(f"Error saving performance data: {e}")
    
    def record_trade(self, trade: TradeRecord):
        """Record a completed trade"""
        
        self.trades.append(trade)
        
        # Update daily P&L
        date_str = trade.exit_time.strftime('%Y-%m-%d')
        if date_str not in self.daily_pnl:
            self.daily_pnl[date_str] = 0.0
        self.daily_pnl[date_str] += trade.pnl_usd
        
        # Update hourly P&L
        hour_str = trade.exit_time.strftime('%Y-%m-%d %H:00')
        if hour_str not in self.hourly_pnl:
            self.hourly_pnl[hour_str] = 0.0
        self.hourly_pnl[hour_str] += trade.pnl_usd
        
        # Save data
        self._save_data()
        
        # Log trade
        result_emoji = "🟢" if trade.pnl_usd > 0 else "🔴"
        logger.info(f"{result_emoji} Trade recorded: {trade.symbol}")
        logger.info(f"   P&L: ${trade.pnl_usd:+,.2f} ({trade.pnl_percentage:+.2f}%)")
        logger.info(f"   Duration: {trade.trade_duration_minutes:.1f} minutes")
        logger.info(f"   Total trades: {len(self.trades)}")
    
    def get_performance_metrics(self, days: Optional[int] = None) -> PerformanceMetrics:
        """
        Calculate performance metrics
        
        Args:
            days: Number of days to look back (None for all time)
        """
        
        # Filter trades by date if specified
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered_trades = [t for t in self.trades if t.exit_time >= cutoff_date]
        else:
            filtered_trades = self.trades
        
        if not filtered_trades:
            return PerformanceMetrics(
                total_trades=0, winning_trades=0, losing_trades=0, win_rate=0.0,
                total_pnl_usd=0.0, total_pnl_percentage=0.0, avg_trade_pnl=0.0,
                best_trade_pnl=0.0, worst_trade_pnl=0.0, avg_trade_duration=0.0,
                total_fees_paid=0.0, sharpe_ratio=0.0, max_drawdown=0.0,
                profit_factor=0.0, avg_winning_trade=0.0, avg_losing_trade=0.0
            )
        
        # Basic metrics
        total_trades = len(filtered_trades)
        winning_trades = len([t for t in filtered_trades if t.pnl_usd > 0])
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0
        
        # P&L metrics
        total_pnl_usd = sum(t.pnl_usd for t in filtered_trades)
        total_pnl_percentage = sum(t.pnl_percentage for t in filtered_trades)
        avg_trade_pnl = total_pnl_usd / total_trades
        best_trade_pnl = max(t.pnl_usd for t in filtered_trades)
        worst_trade_pnl = min(t.pnl_usd for t in filtered_trades)
        
        # Duration and fees
        avg_trade_duration = sum(t.trade_duration_minutes for t in filtered_trades) / total_trades
        total_fees_paid = sum(t.fees_usd for t in filtered_trades)
        
        # Advanced metrics
        winning_pnl = [t.pnl_usd for t in filtered_trades if t.pnl_usd > 0]
        losing_pnl = [t.pnl_usd for t in filtered_trades if t.pnl_usd < 0]
        
        avg_winning_trade = sum(winning_pnl) / len(winning_pnl) if winning_pnl else 0.0
        avg_losing_trade = sum(losing_pnl) / len(losing_pnl) if losing_pnl else 0.0
        
        # Profit factor
        gross_profit = sum(winning_pnl) if winning_pnl else 0.0
        gross_loss = abs(sum(losing_pnl)) if losing_pnl else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Sharpe ratio (simplified)
        if len(filtered_trades) > 1:
            returns = [t.pnl_percentage for t in filtered_trades]
            avg_return = sum(returns) / len(returns)
            return_std = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
            sharpe_ratio = avg_return / return_std if return_std > 0 else 0.0
        else:
            sharpe_ratio = 0.0
        
        # Max drawdown
        max_drawdown = self._calculate_max_drawdown(filtered_trades)
        
        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl_usd=total_pnl_usd,
            total_pnl_percentage=total_pnl_percentage,
            avg_trade_pnl=avg_trade_pnl,
            best_trade_pnl=best_trade_pnl,
            worst_trade_pnl=worst_trade_pnl,
            avg_trade_duration=avg_trade_duration,
            total_fees_paid=total_fees_paid,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            profit_factor=profit_factor,
            avg_winning_trade=avg_winning_trade,
            avg_losing_trade=avg_losing_trade
        )
    
    def _calculate_max_drawdown(self, trades: List[TradeRecord]) -> float:
        """Calculate maximum drawdown percentage"""
        if not trades:
            return 0.0
        
        # Calculate cumulative P&L
        cumulative_pnl = []
        running_total = 0.0
        
        for trade in sorted(trades, key=lambda x: x.exit_time):
            running_total += trade.pnl_usd
            cumulative_pnl.append(running_total)
        
        # Find maximum drawdown
        max_drawdown = 0.0
        peak = cumulative_pnl[0]
        
        for pnl in cumulative_pnl:
            if pnl > peak:
                peak = pnl
            
            drawdown = (peak - pnl) / abs(peak) * 100 if peak != 0 else 0.0
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    def get_daily_pnl(self, days: int = 30) -> Dict[str, float]:
        """Get daily P&L for the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        return {
            date: pnl for date, pnl in self.daily_pnl.items()
            if date >= cutoff_str
        }
    
    def get_hourly_pnl(self, hours: int = 24) -> Dict[str, float]:
        """Get hourly P&L for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff_time.strftime('%Y-%m-%d %H:00')
        
        return {
            hour: pnl for hour, pnl in self.hourly_pnl.items()
            if hour >= cutoff_str
        }
    
    def get_symbol_performance(self) -> Dict[str, Dict]:
        """Get performance breakdown by trading symbol"""
        symbol_stats = {}
        
        for trade in self.trades:
            symbol = trade.symbol
            if symbol not in symbol_stats:
                symbol_stats[symbol] = {
                    'trades': 0,
                    'wins': 0,
                    'total_pnl': 0.0,
                    'best_trade': 0.0,
                    'worst_trade': 0.0
                }
            
            stats = symbol_stats[symbol]
            stats['trades'] += 1
            stats['total_pnl'] += trade.pnl_usd
            
            if trade.pnl_usd > 0:
                stats['wins'] += 1
            
            stats['best_trade'] = max(stats['best_trade'], trade.pnl_usd)
            stats['worst_trade'] = min(stats['worst_trade'], trade.pnl_usd)
        
        # Calculate win rates
        for symbol, stats in symbol_stats.items():
            stats['win_rate'] = (stats['wins'] / stats['trades']) * 100 if stats['trades'] > 0 else 0.0
            stats['avg_pnl'] = stats['total_pnl'] / stats['trades'] if stats['trades'] > 0 else 0.0
        
        return symbol_stats
    
    def get_strategy_signal_analysis(self) -> Dict:
        """Analyze performance based on strategy signals"""
        signal_analysis = {
            'rsi_divergence': {'trades': 0, 'wins': 0, 'total_pnl': 0.0},
            'volume_surge': {'trades': 0, 'wins': 0, 'total_pnl': 0.0},
            'whale_activity': {'trades': 0, 'wins': 0, 'total_pnl': 0.0},
            'all_signals': {'trades': 0, 'wins': 0, 'total_pnl': 0.0}
        }
        
        for trade in self.trades:
            signals = trade.strategy_signals
            
            # RSI divergence
            if signals.get('rsi_divergence', False):
                signal_analysis['rsi_divergence']['trades'] += 1
                signal_analysis['rsi_divergence']['total_pnl'] += trade.pnl_usd
                if trade.pnl_usd > 0:
                    signal_analysis['rsi_divergence']['wins'] += 1
            
            # Volume surge
            if signals.get('volume_surge', False):
                signal_analysis['volume_surge']['trades'] += 1
                signal_analysis['volume_surge']['total_pnl'] += trade.pnl_usd
                if trade.pnl_usd > 0:
                    signal_analysis['volume_surge']['wins'] += 1
            
            # Whale activity
            if signals.get('whale_activity', False):
                signal_analysis['whale_activity']['trades'] += 1
                signal_analysis['whale_activity']['total_pnl'] += trade.pnl_usd
                if trade.pnl_usd > 0:
                    signal_analysis['whale_activity']['wins'] += 1
            
            # All signals present
            if all([signals.get('rsi_divergence', False), 
                   signals.get('volume_surge', False), 
                   signals.get('whale_activity', False)]):
                signal_analysis['all_signals']['trades'] += 1
                signal_analysis['all_signals']['total_pnl'] += trade.pnl_usd
                if trade.pnl_usd > 0:
                    signal_analysis['all_signals']['wins'] += 1
        
        # Calculate win rates
        for signal_type, stats in signal_analysis.items():
            if stats['trades'] > 0:
                stats['win_rate'] = (stats['wins'] / stats['trades']) * 100
                stats['avg_pnl'] = stats['total_pnl'] / stats['trades']
            else:
                stats['win_rate'] = 0.0
                stats['avg_pnl'] = 0.0
        
        return signal_analysis
    
    def generate_performance_report(self) -> str:
        """Generate a comprehensive performance report"""
        
        metrics = self.get_performance_metrics()
        symbol_perf = self.get_symbol_performance()
        signal_analysis = self.get_strategy_signal_analysis()
        
        report = f"""
📊 HIGH-PROFIT ARBITRAGE PERFORMANCE REPORT
{'='*60}

📈 OVERALL PERFORMANCE
Total Trades: {metrics.total_trades}
Win Rate: {metrics.win_rate:.1f}% ({metrics.winning_trades}W / {metrics.losing_trades}L)
Total P&L: ${metrics.total_pnl_usd:+,.2f}
Average Trade: ${metrics.avg_trade_pnl:+,.2f}
Best Trade: ${metrics.best_trade_pnl:+,.2f}
Worst Trade: ${metrics.worst_trade_pnl:+,.2f}
Profit Factor: {metrics.profit_factor:.2f}
Max Drawdown: {metrics.max_drawdown:.2f}%
Avg Duration: {metrics.avg_trade_duration:.1f} minutes
Total Fees: ${metrics.total_fees_paid:,.2f}

🎯 SYMBOL PERFORMANCE
"""
        
        for symbol, stats in sorted(symbol_perf.items(), key=lambda x: x[1]['total_pnl'], reverse=True):
            report += f"{symbol}: {stats['trades']} trades, {stats['win_rate']:.1f}% WR, ${stats['total_pnl']:+,.2f}\n"
        
        report += f"""
🔍 STRATEGY SIGNAL ANALYSIS
RSI Divergence: {signal_analysis['rsi_divergence']['trades']} trades, {signal_analysis['rsi_divergence']['win_rate']:.1f}% WR
Volume Surge: {signal_analysis['volume_surge']['trades']} trades, {signal_analysis['volume_surge']['win_rate']:.1f}% WR
Whale Activity: {signal_analysis['whale_activity']['trades']} trades, {signal_analysis['whale_activity']['win_rate']:.1f}% WR
All Signals: {signal_analysis['all_signals']['trades']} trades, {signal_analysis['all_signals']['win_rate']:.1f}% WR

{'='*60}
Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return report
