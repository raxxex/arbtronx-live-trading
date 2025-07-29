"""
Database models for the arbitrage bot
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

from config import settings

Base = declarative_base()


class ArbitrageOpportunityLog(Base):
    """Log of arbitrage opportunities found"""
    __tablename__ = 'arbitrage_opportunities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    buy_exchange = Column(String(20), nullable=False)
    sell_exchange = Column(String(20), nullable=False)
    buy_price = Column(Float, nullable=False)
    sell_price = Column(Float, nullable=False)
    spread_percentage = Column(Float, nullable=False)
    profit_usd = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Additional details
    buy_amount = Column(Float)
    sell_amount = Column(Float)
    buy_fee = Column(Float)
    sell_fee = Column(Float)
    net_profit = Column(Float)
    
    def __repr__(self):
        return f"<ArbitrageOpportunity({self.symbol}, {self.spread_percentage:.2f}%, ${self.profit_usd:.2f})>"


class TradeExecution(Base):
    """Log of executed trades"""
    __tablename__ = 'trade_executions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    buy_exchange = Column(String(20), nullable=False)
    sell_exchange = Column(String(20), nullable=False)
    
    # Trade details
    buy_trade_id = Column(String(100))
    sell_trade_id = Column(String(100))
    buy_amount = Column(Float, nullable=False)
    sell_amount = Column(Float, nullable=False)
    buy_price = Column(Float, nullable=False)
    sell_price = Column(Float, nullable=False)
    
    # Profit calculation
    expected_profit = Column(Float, nullable=False)
    actual_profit = Column(Float, nullable=False)
    profit_difference = Column(Float)
    
    # Execution details
    execution_time = Column(Float)  # seconds
    success = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text)
    simulation = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    executed_at = Column(DateTime)
    
    def __repr__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"<TradeExecution({self.symbol}, {status}, ${self.actual_profit:.2f})>"


class ExchangeBalance(Base):
    """Log of exchange balances"""
    __tablename__ = 'exchange_balances'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    exchange = Column(String(20), nullable=False, index=True)
    currency = Column(String(10), nullable=False, index=True)
    free = Column(Float, nullable=False)
    used = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<ExchangeBalance({self.exchange}, {self.currency}, {self.total:.6f})>"


class BotStatus(Base):
    """Log of bot status and statistics"""
    __tablename__ = 'bot_status'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    running = Column(Boolean, nullable=False)
    uptime = Column(Float)  # seconds
    scan_count = Column(Integer, default=0)
    opportunities_found = Column(Integer, default=0)
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    total_profit = Column(Float, default=0.0)
    exchanges_connected = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<BotStatus(running={self.running}, profit=${self.total_profit:.2f})>"


class SystemLog(Base):
    """System logs and events"""
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(10), nullable=False, index=True)  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    module = Column(String(50))
    function = Column(String(50))
    line_number = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<SystemLog({self.level}, {self.message[:50]}...)>"


# Database engine and session
engine = None
SessionLocal = None


async def init_database():
    """Initialize the database"""
    global engine, SessionLocal
    
    try:
        # Create engine
        engine = create_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True
        )
        
        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        print(f"Database initialized: {settings.database_url}")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise


def get_db():
    """Get database session"""
    if SessionLocal is None:
        raise Exception("Database not initialized")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseManager:
    """Database operations manager"""

    def __init__(self):
        self.session = None

    async def initialize(self):
        """Initialize the database"""
        try:
            await init_database()
            from loguru import logger
            logger.info("Database initialized successfully")
        except Exception as e:
            from loguru import logger
            logger.warning(f"Database initialization failed: {e}")

    def get_session(self):
        """Get a database session"""
        if SessionLocal is None:
            raise Exception("Database not initialized")
        return SessionLocal()
    
    def log_opportunity(self, opportunity) -> int:
        """Log an arbitrage opportunity"""
        with self.get_session() as session:
            log_entry = ArbitrageOpportunityLog(
                symbol=opportunity.symbol,
                buy_exchange=opportunity.buy_exchange,
                sell_exchange=opportunity.sell_exchange,
                buy_price=opportunity.buy_price,
                sell_price=opportunity.sell_price,
                spread_percentage=opportunity.spread_percentage,
                profit_usd=opportunity.profit_usd,
                volume=opportunity.volume,
                buy_amount=opportunity.buy_amount,
                sell_amount=opportunity.sell_amount,
                buy_fee=opportunity.buy_fee,
                sell_fee=opportunity.sell_fee,
                net_profit=opportunity.net_profit
            )
            session.add(log_entry)
            session.commit()
            return log_entry.id
    
    def log_execution(self, execution_result) -> int:
        """Log a trade execution"""
        with self.get_session() as session:
            log_entry = TradeExecution(
                symbol=execution_result.opportunity.symbol,
                buy_exchange=execution_result.opportunity.buy_exchange,
                sell_exchange=execution_result.opportunity.sell_exchange,
                buy_trade_id=execution_result.buy_trade.id if execution_result.buy_trade else None,
                sell_trade_id=execution_result.sell_trade.id if execution_result.sell_trade else None,
                buy_amount=execution_result.opportunity.buy_amount,
                sell_amount=execution_result.opportunity.sell_amount,
                buy_price=execution_result.opportunity.buy_price,
                sell_price=execution_result.opportunity.sell_price,
                expected_profit=execution_result.opportunity.net_profit,
                actual_profit=execution_result.actual_profit,
                profit_difference=execution_result.profit_difference,
                execution_time=execution_result.execution_time,
                success=execution_result.success,
                error_message=execution_result.error_message,
                simulation=settings.simulation_mode,
                executed_at=datetime.utcnow()
            )
            session.add(log_entry)
            session.commit()
            return log_entry.id
    
    def log_balances(self, balances: dict):
        """Log exchange balances"""
        with self.get_session() as session:
            for exchange, currencies in balances.items():
                for currency, balance in currencies.items():
                    log_entry = ExchangeBalance(
                        exchange=exchange,
                        currency=currency,
                        free=balance.free,
                        used=balance.used,
                        total=balance.total
                    )
                    session.add(log_entry)
            session.commit()
    
    def log_bot_status(self, status: dict):
        """Log bot status"""
        with self.get_session() as session:
            log_entry = BotStatus(
                running=status.get('running', False),
                uptime=status.get('uptime', 0),
                scan_count=status.get('scan_count', 0),
                opportunities_found=status.get('opportunities_found', 0),
                total_executions=status.get('total_executions', 0),
                successful_executions=status.get('successful_executions', 0),
                total_profit=status.get('total_profit', 0.0),
                exchanges_connected=status.get('exchanges_connected', 0)
            )
            session.add(log_entry)
            session.commit()
    
    def get_recent_executions(self, limit: int = 50) -> list:
        """Get recent trade executions"""
        with self.get_session() as session:
            executions = session.query(TradeExecution)\
                .order_by(TradeExecution.created_at.desc())\
                .limit(limit)\
                .all()
            return executions
    
    def get_profit_summary(self, days: int = 30) -> dict:
        """Get profit summary for the last N days"""
        with self.get_session() as session:
            from datetime import timedelta
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Total profit
            total_profit = session.query(func.sum(TradeExecution.actual_profit))\
                .filter(TradeExecution.success == True)\
                .filter(TradeExecution.created_at >= start_date)\
                .scalar() or 0.0
            
            # Number of successful trades
            successful_trades = session.query(func.count(TradeExecution.id))\
                .filter(TradeExecution.success == True)\
                .filter(TradeExecution.created_at >= start_date)\
                .scalar() or 0
            
            # Total trades
            total_trades = session.query(func.count(TradeExecution.id))\
                .filter(TradeExecution.created_at >= start_date)\
                .scalar() or 0
            
            return {
                'total_profit': total_profit,
                'successful_trades': successful_trades,
                'total_trades': total_trades,
                'success_rate': (successful_trades / total_trades * 100) if total_trades > 0 else 0,
                'days': days
            }

    async def log_execution(self, execution_result):
        """Log an execution result"""
        try:
            if hasattr(execution_result, 'opportunity'):
                self.log_trade_execution(execution_result)
        except Exception as e:
            from loguru import logger
            logger.warning(f"Failed to log execution: {e}")
