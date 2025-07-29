"""
Configuration settings for ARBTRONX Live Trading Dashboard
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Settings:
    """Application settings"""

    # API Configuration
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_SECRET_KEY: Optional[str] = None
    BINANCE_SANDBOX: bool = False

    # Exchange credentials structure
    binance_credentials: dict = None
    kucoin_credentials: dict = None
    okx_credentials: dict = None

    # Trading Configuration
    MIN_PROFIT_THRESHOLD: float = 0.5
    MAX_POSITION_SIZE: float = 1000.0
    ENABLE_AUTO_TRADING: bool = False
    
    # Grid Trading Settings
    DEFAULT_GRID_LEVELS: int = 10
    DEFAULT_GRID_SPACING: float = 0.5
    MAX_GRID_LEVELS: int = 50
    MIN_GRID_SPACING: float = 0.1
    MAX_GRID_SPACING: float = 5.0
    
    # Risk Management
    MAX_DRAWDOWN: float = 0.1  # 10%
    STOP_LOSS_PERCENTAGE: float = 0.05  # 5%
    
    # Database
    DATABASE_URL: str = "sqlite:///arbitrage_bot.db"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    def __post_init__(self):
        """Load environment variables"""
        self.BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
        self.BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
        self.BINANCE_SANDBOX = os.getenv('BINANCE_SANDBOX', 'false').lower() == 'true'

        # Initialize credentials dictionaries
        self.binance_credentials = {
            'apiKey': self.BINANCE_API_KEY,
            'secret': self.BINANCE_SECRET_KEY,
            'sandbox': self.BINANCE_SANDBOX
        }

        self.kucoin_credentials = {
            'apiKey': os.getenv('KUCOIN_API_KEY'),
            'secret': os.getenv('KUCOIN_SECRET_KEY'),
            'passphrase': os.getenv('KUCOIN_PASSPHRASE'),
            'sandbox': os.getenv('KUCOIN_SANDBOX', 'false').lower() == 'true'
        }

        self.okx_credentials = {
            'apiKey': os.getenv('OKX_API_KEY'),
            'secret': os.getenv('OKX_SECRET_KEY'),
            'passphrase': os.getenv('OKX_PASSPHRASE'),
            'sandbox': os.getenv('OKX_SANDBOX', 'false').lower() == 'true'
        }
        
        # Trading settings from env
        self.MIN_PROFIT_THRESHOLD = float(os.getenv('MIN_PROFIT_THRESHOLD', self.MIN_PROFIT_THRESHOLD))
        self.MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', self.MAX_POSITION_SIZE))
        self.ENABLE_AUTO_TRADING = os.getenv('ENABLE_AUTO_TRADING', 'false').lower() == 'true'
        
        # Risk management from env
        self.MAX_DRAWDOWN = float(os.getenv('MAX_DRAWDOWN', self.MAX_DRAWDOWN))
        self.STOP_LOSS_PERCENTAGE = float(os.getenv('STOP_LOSS_PERCENTAGE', self.STOP_LOSS_PERCENTAGE))
        
        # Database from env
        self.DATABASE_URL = os.getenv('DATABASE_URL', self.DATABASE_URL)
        
        # Logging from env
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', self.LOG_LEVEL)

# Global settings instance (will be created after environment loading)
settings = None

def get_settings():
    """Get or create settings instance"""
    global settings
    if settings is None:
        settings = Settings()
    return settings

# Initialize settings
settings = Settings()
