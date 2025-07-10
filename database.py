import os
import logging
import streamlit as st
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import json


# ✅ Get DB URL from environment or Streamlit secrets
def get_database_url():
    # Use environment variable if it exists
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
    # Otherwise use Streamlit secrets (for production)
    try:
        import streamlit as st
        return st.secrets["DATABASE_URL"]
    except Exception as e:
        raise RuntimeError("No DATABASE_URL found in environment or Streamlit secrets") from e

# ✅ Resolve once after function is defined
DATABASE_URL = get_database_url()

# ✅ SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False  # Change to True if you want SQL debug logs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Portfolio(Base):
    __tablename__ = "portfolio"
    
    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Float, nullable=False, default=10.0)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # LONG or SHORT
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    pnl = Column(Float, nullable=False)
    strategy = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=True)
    executed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    trade_metadata = Column(JSON, nullable=True)

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # LONG or SHORT
    strategy = Column(String(50), nullable=False)
    timeframe = Column(String(10), nullable=False)
    entry_price = Column(Float, nullable=False)
    tp_price = Column(Float, nullable=False)
    sl_price = Column(Float, nullable=False)
    liquidation_price = Column(Float, nullable=True)
    confidence = Column(Float, nullable=False)
    score = Column(Float, nullable=False)
    rsi = Column(Float, nullable=True)
    macd_hist = Column(Float, nullable=True)
    bb_breakout = Column(String(10), nullable=True)
    trend = Column(String(20), nullable=True)
    regime = Column(String(20), nullable=True)
    vol_spike = Column(Boolean, default=False)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    signal_metadata = Column(JSON, nullable=True)

class AutomationStats(Base):
    __tablename__ = "automation_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    signals_generated = Column(Integer, default=0)
    trades_executed = Column(Integer, default=0)
    successful_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    start_time = Column(DateTime, nullable=True)
    last_update = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    session_data = Column(JSON, nullable=True)

class SystemSettings(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    data_type = Column(String(20), default='string')  # string, int, float, bool, json
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Database Operations Class
class DatabaseManager:
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        self.logger = logging.getLogger(__name__)
        
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("Database tables created successfully")
        except Exception as e:
            self.logger.error(f"Error creating database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()
    
    # Portfolio Operations
    def get_portfolio_balance(self) -> float:
        """Get current portfolio balance"""
        session = self.get_session()
        try:
            portfolio = session.query(Portfolio).order_by(Portfolio.updated_at.desc()).first()
            if portfolio:
                return portfolio.balance
            else:
                # Create initial portfolio
                initial_portfolio = Portfolio(balance=10.0)
                session.add(initial_portfolio)
                session.commit()
                return 10.0
        except Exception as e:
            self.logger.error(f"Error getting portfolio balance: {e}")
            session.rollback()
            return 10.0
        finally:
            session.close()
    
    def update_portfolio_balance(self, balance: float) -> bool:
        """Update portfolio balance"""
        session = self.get_session()
        try:
            portfolio = Portfolio(balance=balance)
            session.add(portfolio)
            session.commit()
            self.logger.info(f"Portfolio balance updated to ${balance}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating portfolio balance: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    # Trade Operations
    def add_trade(self, trade_data: dict) -> bool:
        """Add a new trade to the database"""
        session = self.get_session()
        try:
            trade = Trade(
                symbol=trade_data['symbol'],
                side=trade_data['side'],
                entry_price=trade_data['entry'],
                exit_price=trade_data['exit'],
                quantity=trade_data['qty'],
                pnl=trade_data['pnl'],
                strategy=trade_data['strategy'],
                confidence=trade_data.get('confidence'),
                trade_metadata=trade_data.get('metadata', {})
            )
            session.add(trade)
            session.commit()
            self.logger.info(f"Trade added: {trade_data['symbol']} - P&L: ${trade_data['pnl']}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding trade: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_trades(self, limit: int = 50, symbol: str = None) -> list:
        """Get trades from database"""
        session = self.get_session()
        try:
            query = session.query(Trade)
            
            if symbol:
                query = query.filter(Trade.symbol == symbol)
            
            trades = query.order_by(Trade.executed_at.desc()).limit(limit).all()
            
            return [{
                'id': trade.id,
                'symbol': trade.symbol,
                'side': trade.side,
                'entry': trade.entry_price,
                'exit': trade.exit_price,
                'qty': trade.quantity,
                'pnl': trade.pnl,
                'strategy': trade.strategy,
                'confidence': trade.confidence,
                'timestamp': trade.executed_at.strftime('%Y-%m-%d %H:%M:%S'),
                'metadata': trade.trade_metadata or {}
            } for trade in trades]
        except Exception as e:
            self.logger.error(f"Error getting trades: {e}")
            return []
        finally:
            session.close()
    
    def get_daily_pnl(self, date: datetime = None) -> float:
        """Get daily P&L for a specific date"""
        if date is None:
            date = datetime.now(timezone.utc)
        
        session = self.get_session()
        try:
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            trades = session.query(Trade).filter(
                Trade.executed_at >= start_date,
                Trade.executed_at <= end_date
            ).all()
            
            return sum(trade.pnl for trade in trades)
        except Exception as e:
            self.logger.error(f"Error getting daily P&L: {e}")
            return 0.0
        finally:
            session.close()
    
    # Signal Operations
    def add_signal(self, signal_data: dict) -> bool:
        """Add a new signal to the database"""
        session = self.get_session()
        try:
            signal = Signal(
                symbol=signal_data['symbol'],
                side=signal_data['side'],
                strategy=signal_data['strategy'],
                timeframe=signal_data['timeframe'],
                entry_price=signal_data['entry'],
                tp_price=signal_data['tp'],
                sl_price=signal_data['sl'],
                liquidation_price=signal_data.get('liquidation'),
                confidence=signal_data['confidence'],
                score=signal_data['score'],
                rsi=signal_data.get('rsi'),
                macd_hist=signal_data.get('macd_hist'),
                bb_breakout=signal_data.get('bb_breakout'),
                trend=signal_data.get('trend'),
                regime=signal_data.get('regime'),
                vol_spike=signal_data.get('vol_spike', False),
                signal_metadata=signal_data.get('metadata', {})
            )
            session.add(signal)
            session.commit()
            self.logger.info(f"Signal added: {signal_data['symbol']} - {signal_data['strategy']}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding signal: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_signals(self, limit: int = 10, active_only: bool = True) -> list:
        """Get signals from database"""
        session = self.get_session()
        try:
            query = session.query(Signal)
            
            if active_only:
                query = query.filter(Signal.is_active == True)
            
            signals = query.order_by(Signal.generated_at.desc()).limit(limit).all()
            
            return [{
                'id': signal.id,
                'symbol': signal.symbol,
                'side': signal.side,
                'strategy': signal.strategy,
                'timeframe': signal.timeframe,
                'entry': signal.entry_price,
                'tp': signal.tp_price,
                'sl': signal.sl_price,
                'liquidation': signal.liquidation_price,
                'confidence': signal.confidence,
                'score': signal.score,
                'rsi': signal.rsi,
                'macd_hist': signal.macd_hist,
                'bb_breakout': signal.bb_breakout,
                'trend': signal.trend,
                'regime': signal.regime,
                'vol_spike': signal.vol_spike,
                'timestamp': signal.generated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'metadata': signal.signal_metadata or {}
            } for signal in signals]
        except Exception as e:
            self.logger.error(f"Error getting signals: {e}")
            return []
        finally:
            session.close()
    
    def deactivate_signal(self, signal_id: int) -> bool:
        """Deactivate a signal"""
        session = self.get_session()
        try:
            signal = session.query(Signal).filter(Signal.id == signal_id).first()
            if signal:
                signal.is_active = False
                session.commit()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deactivating signal: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    # Automation Stats Operations
    def get_automation_stats(self) -> dict:
        """Get automation statistics"""
        session = self.get_session()
        try:
            stats = session.query(AutomationStats).order_by(AutomationStats.last_update.desc()).first()
            if stats:
                return {
                    'signals_generated': stats.signals_generated,
                    'trades_executed': stats.trades_executed,
                    'successful_trades': stats.successful_trades,
                    'total_pnl': stats.total_pnl,
                    'start_time': stats.start_time.isoformat() if stats.start_time else None,
                    'last_update': stats.last_update.isoformat() if stats.last_update else None,
                    'session_data': stats.session_data or {}
                }
            else:
                # Create initial stats
                initial_stats = AutomationStats()
                session.add(initial_stats)
                session.commit()
                return {
                    'signals_generated': 0,
                    'trades_executed': 0,
                    'successful_trades': 0,
                    'total_pnl': 0.0,
                    'start_time': None,
                    'last_update': None,
                    'session_data': {}
                }
        except Exception as e:
            self.logger.error(f"Error getting automation stats: {e}")
            return {}
        finally:
            session.close()
    
    def update_automation_stats(self, stats_data: dict) -> bool:
        """Update automation statistics"""
        session = self.get_session()
        try:
            stats = AutomationStats(
                signals_generated=stats_data.get('signals_generated', 0),
                trades_executed=stats_data.get('trades_executed', 0),
                successful_trades=stats_data.get('successful_trades', 0),
                total_pnl=stats_data.get('total_pnl', 0.0),
                start_time=datetime.fromisoformat(stats_data['start_time']) if stats_data.get('start_time') else None,
                session_data=stats_data.get('session_data', {})
            )
            session.add(stats)
            session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error updating automation stats: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    # Settings Operations
    def get_setting(self, key: str, default_value=None):
        """Get a system setting"""
        session = self.get_session()
        try:
            setting = session.query(SystemSettings).filter(SystemSettings.key == key).first()
            if setting:
                # Convert based on data type
                if setting.data_type == 'json':
                    return json.loads(setting.value)
                elif setting.data_type == 'int':
                    return int(setting.value)
                elif setting.data_type == 'float':
                    return float(setting.value)
                elif setting.data_type == 'bool':
                    return setting.value.lower() == 'true'
                else:
                    return setting.value
            return default_value
        except Exception as e:
            self.logger.error(f"Error getting setting {key}: {e}")
            return default_value
        finally:
            session.close()
    
    def set_setting(self, key: str, value, data_type: str = 'string') -> bool:
        """Set a system setting"""
        session = self.get_session()
        try:
            # Convert value to string for storage
            if data_type == 'json':
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            
            # Check if setting exists
            setting = session.query(SystemSettings).filter(SystemSettings.key == key).first()
            if setting:
                setting.value = value_str
                setting.data_type = data_type
                setting.updated_at = datetime.now()
            else:
                setting = SystemSettings(key=key, value=value_str, data_type=data_type)
                session.add(setting)
            
            session.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error setting {key}: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def migrate_json_data(self):
        """Migrate existing JSON data to database"""
        try:
            # Migrate portfolio data
            if os.path.exists('capital.json'):
                with open('capital.json', 'r') as f:
                    capital_data = json.load(f)
                    self.update_portfolio_balance(capital_data.get('balance', 10.0))
                self.logger.info("Portfolio data migrated successfully")
            
            # Migrate trade history
            if os.path.exists('trades_history.json'):
                with open('trades_history.json', 'r') as f:
                    trades_data = json.load(f)
                    for trade in trades_data:
                        self.add_trade(trade)
                self.logger.info(f"Migrated {len(trades_data)} trades to database")
            
            # Migrate signals
            if os.path.exists('signals'):
                signal_count = 0
                for filename in os.listdir('signals'):
                    if filename.endswith('.json'):
                        with open(os.path.join('signals', filename), 'r') as f:
                            signal_data = json.load(f)
                            self.add_signal(signal_data)
                            signal_count += 1
                self.logger.info(f"Migrated {signal_count} signals to database")
            
            # Migrate automation settings
            if os.path.exists('automation_settings.json'):
                with open('automation_settings.json', 'r') as f:
                    settings_data = json.load(f)
                    self.set_setting('automation_settings', settings_data, 'json')
                self.logger.info("Automation settings migrated successfully")
            
        except Exception as e:
            self.logger.error(f"Error migrating JSON data: {e}")

# Global database manager instance
db_manager = DatabaseManager()

# Initialize database on import
try:
    db_manager.create_tables()
    # Run migration if needed
    if os.path.exists('capital.json') or os.path.exists('trades_history.json'):
        db_manager.migrate_json_data()
except Exception as e:
    logging.error(f"Database initialization failed: {e}")