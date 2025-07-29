"""
Technical Indicators for High-Profit Arbitrage Strategy
"""

import numpy as np
from typing import List, Optional
from loguru import logger


class RSICalculator:
    """
    Relative Strength Index (RSI) Calculator
    """
    
    def __init__(self, period: int = 14):
        self.period = period
    
    def calculate(self, prices: List[float]) -> float:
        """
        Calculate RSI for given price series
        
        Args:
            prices: List of closing prices
            
        Returns:
            RSI value (0-100)
        """
        if len(prices) < self.period + 1:
            return 50.0  # Neutral RSI if not enough data
        
        try:
            # Convert to numpy array
            prices_array = np.array(prices)
            
            # Calculate price changes
            deltas = np.diff(prices_array)
            
            # Separate gains and losses
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            # Calculate average gains and losses
            avg_gain = np.mean(gains[-self.period:])
            avg_loss = np.mean(losses[-self.period:])
            
            # Avoid division by zero
            if avg_loss == 0:
                return 100.0
            
            # Calculate RS and RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi)
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return 50.0
    
    def calculate_smoothed(self, prices: List[float]) -> float:
        """
        Calculate smoothed RSI using Wilder's smoothing method
        """
        if len(prices) < self.period + 1:
            return 50.0
        
        try:
            prices_array = np.array(prices)
            deltas = np.diff(prices_array)
            
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            # Initial averages
            avg_gain = np.mean(gains[:self.period])
            avg_loss = np.mean(losses[:self.period])
            
            # Wilder's smoothing
            for i in range(self.period, len(gains)):
                avg_gain = (avg_gain * (self.period - 1) + gains[i]) / self.period
                avg_loss = (avg_loss * (self.period - 1) + losses[i]) / self.period
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi)
            
        except Exception as e:
            logger.error(f"Error calculating smoothed RSI: {e}")
            return 50.0


class VolumeAnalyzer:
    """
    Volume Analysis for detecting surges and anomalies
    """
    
    def __init__(self):
        self.volume_history = {}
    
    def detect_volume_surge(self, symbol: str, current_volume: float, 
                          historical_volumes: List[float], 
                          surge_multiplier: float = 2.0) -> bool:
        """
        Detect if current volume represents a surge
        
        Args:
            symbol: Trading pair symbol
            current_volume: Current volume
            historical_volumes: List of historical volumes
            surge_multiplier: Multiplier to consider as surge (default 2.0x)
            
        Returns:
            True if volume surge detected
        """
        try:
            if not historical_volumes or len(historical_volumes) < 5:
                return False
            
            # Calculate average historical volume
            avg_historical = np.mean(historical_volumes)
            
            # Check if current volume is significantly higher
            if avg_historical > 0:
                surge_ratio = current_volume / avg_historical
                
                logger.debug(f"{symbol} Volume Analysis:")
                logger.debug(f"  Current: {current_volume:,.0f}")
                logger.debug(f"  Average: {avg_historical:,.0f}")
                logger.debug(f"  Ratio: {surge_ratio:.2f}x")
                
                return surge_ratio >= surge_multiplier
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting volume surge for {symbol}: {e}")
            return False
    
    def calculate_volume_trend(self, volumes: List[float], periods: int = 5) -> str:
        """
        Calculate volume trend over specified periods
        
        Returns:
            'increasing', 'decreasing', or 'stable'
        """
        try:
            if len(volumes) < periods:
                return 'stable'
            
            recent_volumes = volumes[-periods:]
            
            # Calculate trend using linear regression
            x = np.arange(len(recent_volumes))
            y = np.array(recent_volumes)
            
            # Calculate slope
            slope = np.polyfit(x, y, 1)[0]
            
            # Determine trend
            if slope > 0.1:
                return 'increasing'
            elif slope < -0.1:
                return 'decreasing'
            else:
                return 'stable'
                
        except Exception as e:
            logger.error(f"Error calculating volume trend: {e}")
            return 'stable'
    
    def get_volume_percentile(self, current_volume: float, 
                            historical_volumes: List[float]) -> float:
        """
        Get percentile rank of current volume compared to historical data
        
        Returns:
            Percentile (0-100)
        """
        try:
            if not historical_volumes:
                return 50.0
            
            volumes_array = np.array(historical_volumes + [current_volume])
            percentile = (np.searchsorted(np.sort(volumes_array), current_volume) / len(volumes_array)) * 100
            
            return float(percentile)
            
        except Exception as e:
            logger.error(f"Error calculating volume percentile: {e}")
            return 50.0


class MovingAverageCalculator:
    """
    Moving Average calculations for trend analysis
    """
    
    @staticmethod
    def sma(prices: List[float], period: int) -> Optional[float]:
        """Simple Moving Average"""
        try:
            if len(prices) < period:
                return None
            
            return float(np.mean(prices[-period:]))
            
        except Exception as e:
            logger.error(f"Error calculating SMA: {e}")
            return None
    
    @staticmethod
    def ema(prices: List[float], period: int) -> Optional[float]:
        """Exponential Moving Average"""
        try:
            if len(prices) < period:
                return None
            
            prices_array = np.array(prices)
            alpha = 2 / (period + 1)
            
            # Initialize with SMA
            ema_values = [np.mean(prices_array[:period])]
            
            # Calculate EMA
            for price in prices_array[period:]:
                ema_values.append(alpha * price + (1 - alpha) * ema_values[-1])
            
            return float(ema_values[-1])
            
        except Exception as e:
            logger.error(f"Error calculating EMA: {e}")
            return None


class BollingerBands:
    """
    Bollinger Bands for volatility analysis
    """
    
    @staticmethod
    def calculate(prices: List[float], period: int = 20, std_dev: float = 2.0) -> dict:
        """
        Calculate Bollinger Bands
        
        Returns:
            Dict with 'upper', 'middle', 'lower' bands
        """
        try:
            if len(prices) < period:
                return {'upper': None, 'middle': None, 'lower': None}
            
            prices_array = np.array(prices[-period:])
            
            # Middle band (SMA)
            middle = np.mean(prices_array)
            
            # Standard deviation
            std = np.std(prices_array)
            
            # Upper and lower bands
            upper = middle + (std_dev * std)
            lower = middle - (std_dev * std)
            
            return {
                'upper': float(upper),
                'middle': float(middle),
                'lower': float(lower)
            }
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return {'upper': None, 'middle': None, 'lower': None}


class MACD:
    """
    MACD (Moving Average Convergence Divergence) indicator
    """
    
    @staticmethod
    def calculate(prices: List[float], fast_period: int = 12, 
                 slow_period: int = 26, signal_period: int = 9) -> dict:
        """
        Calculate MACD
        
        Returns:
            Dict with 'macd', 'signal', 'histogram'
        """
        try:
            if len(prices) < slow_period:
                return {'macd': None, 'signal': None, 'histogram': None}
            
            # Calculate EMAs
            fast_ema = MovingAverageCalculator.ema(prices, fast_period)
            slow_ema = MovingAverageCalculator.ema(prices, slow_period)
            
            if fast_ema is None or slow_ema is None:
                return {'macd': None, 'signal': None, 'histogram': None}
            
            # MACD line
            macd_line = fast_ema - slow_ema
            
            # Signal line (EMA of MACD)
            # For simplicity, using the current MACD value as signal
            signal_line = macd_line  # In practice, you'd calculate EMA of MACD values
            
            # Histogram
            histogram = macd_line - signal_line
            
            return {
                'macd': float(macd_line),
                'signal': float(signal_line),
                'histogram': float(histogram)
            }
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return {'macd': None, 'signal': None, 'histogram': None}


class StochasticOscillator:
    """
    Stochastic Oscillator for momentum analysis
    """
    
    @staticmethod
    def calculate(highs: List[float], lows: List[float], closes: List[float], 
                 k_period: int = 14, d_period: int = 3) -> dict:
        """
        Calculate Stochastic Oscillator
        
        Returns:
            Dict with '%K' and '%D' values
        """
        try:
            if len(closes) < k_period:
                return {'%K': None, '%D': None}
            
            # Get recent data
            recent_highs = highs[-k_period:]
            recent_lows = lows[-k_period:]
            current_close = closes[-1]
            
            # Calculate %K
            highest_high = max(recent_highs)
            lowest_low = min(recent_lows)
            
            if highest_high == lowest_low:
                k_percent = 50.0
            else:
                k_percent = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
            
            # Calculate %D (SMA of %K)
            # For simplicity, using current %K as %D
            d_percent = k_percent
            
            return {
                '%K': float(k_percent),
                '%D': float(d_percent)
            }
            
        except Exception as e:
            logger.error(f"Error calculating Stochastic Oscillator: {e}")
            return {'%K': None, '%D': None}
